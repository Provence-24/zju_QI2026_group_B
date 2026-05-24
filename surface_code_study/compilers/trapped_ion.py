"""
Trapped ion platform compiler.

Models the Quantinuum H2 / QCCD architecture where ancillas and data qubits
reside in separate trap zones. Every ancilla-data interaction requires ion
transport between zones, incurring idle decoherence proportional to the
transport time (t_transport_ns), which is much larger than gate times.

Simplified model:
  - All ancillas in zone A, all data qubits in zone B
  - Each (ancilla, data) interaction: transport → gate → transport back
  - MS gate approximated by CZ + single-qubit rotations (Clifford equivalent)
  - Transport noise applied via idle_noise() on both participating qubits

t_transport_ns is typically 1-10 ms, making transport-induced decoherence
the dominant noise source despite excellent intrinsic gate fidelities.
"""

import stim
from surface_code_study.compilers.base import PlatformCompiler


class TrappedIonCompiler(PlatformCompiler):
    """Rotated surface code compiler for trapped ion (QCCD) platforms."""

    STEP_DIRS = ['N', 'W', 'S', 'E']

    def _init_layout(self) -> dict:
        layout = self._build_rotated_layout()
        layout['_dir_groups'] = self._classify_directions(layout)
        return layout

    def _classify_directions(self, layout: dict) -> dict:
        """Classify ancilla-data pairs by direction (same as 4-step CZ schedule)."""
        dir_groups = {d: [] for d in self.STEP_DIRS}
        ancilla_coords = layout['ancilla_coords']
        data_coords = layout['data_coords']

        for anc, data_list in layout['connectivity'].items():
            ar, ac = ancilla_coords[anc]
            for dq in data_list:
                dr, dc = data_coords[dq]
                if dr < ar:
                    dir_groups['N'].append((anc, dq))
                elif dr > ar:
                    dir_groups['S'].append((anc, dq))
                elif dc < ac:
                    dir_groups['W'].append((anc, dq))
                elif dc > ac:
                    dir_groups['E'].append((anc, dq))

        return dir_groups

    def build_round(self, is_first_round: bool = False) -> stim.Circuit:
        c = stim.Circuit()
        anc_x = self._layout['ancilla_x']
        anc_z = self._layout['ancilla_z']
        all_anc = anc_x + anc_z
        data = self._layout['data']
        all_qubits = data + all_anc

        p_1q = self.params['p_1q']
        p_2q = self.params['p_2q']
        p_meas = self.params['p_meas']
        p_reset = self.params['p_reset']
        t_transport_ns = self.params.get('t_transport_ns', 2_000_000)
        t_meas_ns = self.params.get('t_cycle_ns', 2_000_000) * 0.9
        p_heating = self.params.get('p_heating', 0.0)

        # ── TICK 1: Initialize ancillas ───────────────────────────────────
        c.append("R", all_anc)
        c.append("X_ERROR", all_anc, p_reset)
        for q in all_anc:
            c.append("DEPOLARIZE1", q, p_1q)
        c.append("TICK")

        # ── 4-step interaction schedule (N, W, S, E) ─────────────────────
        dir_groups = self._layout['_dir_groups']

        for direction in self.STEP_DIRS:
            pairs = dir_groups[direction]

            for anc, dq in pairs:
                # Hadamard on X ancillas (before the CZ sandwich)
                if anc in anc_x:
                    c.append("H", anc)
                    c.append("DEPOLARIZE1", anc, p_1q)

                # Transport ancilla to data zone → idle decoherence
                c += self.idle_noise([anc, dq], t_transport_ns)
                if p_heating > 0:
                    c.append("DEPOLARIZE1", [anc, dq], p_heating)

                # MS gate (approximated as CX + noise)
                if anc in anc_x:
                    c.append("CX", [anc, dq])
                else:
                    c.append("CX", [dq, anc])
                c.append("DEPOLARIZE2", [anc, dq], p_2q)

                # Transport ancilla back to zone A → idle decoherence
                c += self.idle_noise([anc, dq], t_transport_ns)
                if p_heating > 0:
                    c.append("DEPOLARIZE1", [anc, dq], p_heating)

                # Undo Hadamard on X ancillas
                if anc in anc_x:
                    c.append("H", anc)
                    c.append("DEPOLARIZE1", anc, p_1q)

            c.append("TICK")

        # ── Measurement ───────────────────────────────────────────────────
        # Data qubits idle during ancilla readout
        c += self.idle_noise(data, t_meas_ns)

        c.append("M", all_anc)
        c.append("X_ERROR", all_anc, p_meas)

        # ── DETECTOR markers ──────────────────────────────────────────────
        n_all = len(all_anc)
        n_z = len(anc_z)

        if is_first_round:
            for i in range(n_z):
                c.append("DETECTOR", [stim.target_rec(-n_z + i)])
        else:
            for i in range(n_all):
                c.append(
                    "DETECTOR",
                    [
                        stim.target_rec(-n_all + i),
                        stim.target_rec(-2 * n_all + i),
                    ],
                )

        return c
