"""
Superconducting platform compiler.

Models Google Willow-style transmon qubits on a 2D grid with nearest-neighbour
CZ gates. Uses a 4-step CZ schedule (N, W, S, E) with idle decoherence applied
to all non-participating qubits after each step. The measurement step contributes
the largest idle noise because data qubits sit idle during dispersive readout.
"""

import stim
from surface_code_study.compilers.base import PlatformCompiler


class SuperconductingCompiler(PlatformCompiler):
    """Rotated surface code compiler for superconducting transmon platforms."""

    STEP_DIRS = ['N', 'W', 'S', 'E']

    def _init_layout(self) -> dict:
        layout = self._build_rotated_layout()
        # Pre-compute directional gate groups for efficient build_round()
        layout['_dir_groups'] = self._classify_directions(layout)
        return layout

    def _classify_directions(self, layout: dict) -> dict:
        """
        For each ancilla, classify its data neighbours by direction (N/W/S/E).

        Returns {direction: [(ancilla, data_qubit), ...]}
        """
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
        t_cycle_ns = self.params['t_cycle_ns']

        # Fraction of cycle time per gate tick vs measurement tick.
        # Gate ticks are fast (~10-20 ns), measurement dominates (t_cycle ~ 200 ns).
        # Approximate: 4 gate ticks × 0.05 + measurement tick × 0.8 = t_cycle
        gate_tick_ns = t_cycle_ns * 0.05
        meas_tick_ns = t_cycle_ns * 0.80

        # ── TICK 1: Initialize ancillas + Hadamard on X ancillas ──────────
        c.append("R", all_anc)
        c.append("X_ERROR", all_anc, p_reset)
        for q in anc_x:
            c.append("H", q)
            c.append("DEPOLARIZE1", q, p_1q)
        c.append("TICK")

        # ── TICK 2-5: 4-step CX schedule ──────────────────────────────────
        # X ancillas: CX(anc → data) with ancilla control
        # Z ancillas: CX(data → anc) with data control
        dir_groups = self._layout['_dir_groups']
        for direction in self.STEP_DIRS:
            pairs = dir_groups[direction]
            active = set()
            for anc, dq in pairs:
                if anc in anc_x:
                    c.append("CX", [anc, dq])
                else:
                    c.append("CX", [dq, anc])
                c.append("DEPOLARIZE2", [anc, dq], p_2q)
                active.add(anc)
                active.add(dq)

            # Idle noise on all qubits not participating in this step
            idle_qubits = [q for q in all_qubits if q not in active]
            c += self.idle_noise(idle_qubits, gate_tick_ns)
            c.append("TICK")

        # ── TICK 6: Hadamard + Measurement (longest step) ─────────────────
        # Undo Hadamard on X ancillas
        for q in anc_x:
            c.append("H", q)
            c.append("DEPOLARIZE1", q, p_1q)

        # Idle noise on data qubits during measurement (dominant noise source)
        c += self.idle_noise(data, meas_tick_ns)

        # Measure all ancillas
        c.append("M", all_anc)
        c.append("X_ERROR", all_anc, p_meas)

        # ── DETECTOR markers ──────────────────────────────────────────────
        # First round: only Z ancillas (deterministic measurement from |0⟩ init).
        # Later rounds: all ancillas, comparing consecutive measurements.
        n_all = len(all_anc)
        n_z = len(anc_z)

        if is_first_round:
            # Z ancillas are at the END of the measurement order (anc_x first, then anc_z)
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
