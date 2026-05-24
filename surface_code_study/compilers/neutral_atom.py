"""
Neutral atom platform compiler.

Models the Harvard/QuEra dual-zone architecture (Bluvstein 2024):
  - Storage zone: atoms in ground state, excellent T1/T2.
  - Entangling zone: Rydberg-mediated global CZ pulses.

Syndrome extraction is broken into movement batches. Each batch:
  1. Move selected (ancilla, data) pairs into the entangling zone
     → idle noise on moved atoms for t_move_ns
  2. Apply global CZ pulse + DEPOLARIZE2 on all pairs in the zone
  3. Move them back to storage zone
     → idle noise on moved atoms for t_move_ns

Because t_move_ns (100-500 us) >> t_gate_ns (~0.1 us), movement-induced
decoherence is the dominant noise mechanism even with modest T1/T2.
"""

import stim
from surface_code_study.compilers.base import PlatformCompiler


class NeutralAtomCompiler(PlatformCompiler):
    """Rotated surface code compiler for neutral atom platforms."""

    STEP_DIRS = ['N', 'W', 'S', 'E']

    def _init_layout(self) -> dict:
        layout = self._build_rotated_layout()
        layout['_dir_groups'] = self._classify_directions(layout)
        return layout

    def _classify_directions(self, layout: dict) -> dict:
        """Classify ancilla-data pairs by direction for batch scheduling."""
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

    def _schedule_movement_batches(self) -> list[list[tuple[int, int]]]:
        """
        Return movement batches for one syndrome round.

        Uses 4-directional batching (N, W, S, E). Within each batch,
        no data qubit is shared between ancillas, making it safe for
        a global CZ pulse.

        This is a conservative estimate: in real hardware, more
        aggressive batching could reduce the number of batches.
        """
        dir_groups = self._layout['_dir_groups']
        batches = []
        for direction in self.STEP_DIRS:
            pairs = dir_groups[direction]
            if pairs:
                batches.append(list(pairs))
        return batches

    def build_round(self, is_first_round: bool = False) -> stim.Circuit:
        c = stim.Circuit()
        anc_x = self._layout['ancilla_x']
        anc_z = self._layout['ancilla_z']
        all_anc = anc_x + anc_z
        data = self._layout['data']

        p_1q = self.params['p_1q']
        p_2q = self.params['p_2q']
        p_meas = self.params['p_meas']
        p_reset = self.params['p_reset']
        t_move_ns = self.params.get('t_move_ns', 200_000)
        t_meas_ns = self.params.get('t_cycle_ns', 200_000) * 0.9

        # ── TICK 1: ancilla initialization ────────────────────────────────
        c.append("R", all_anc)
        c.append("X_ERROR", all_anc, p_reset)
        # Single-qubit gate noise on ancilla reset
        for q in all_anc:
            c.append("DEPOLARIZE1", q, p_1q)
        c.append("TICK")

        # ── Movement batches: move → CZ → move back ───────────────────────
        batches = self._schedule_movement_batches()

        for batch_idx, pairs in enumerate(batches):
            # Collect all qubits involved in this batch's movement
            moved_qubits = set()
            for anc, dq in pairs:
                moved_qubits.add(anc)
                moved_qubits.add(dq)

            # Hadamard on X ancillas before CX
            for anc, _ in pairs:
                if anc in anc_x:
                    c.append("H", anc)
                    c.append("DEPOLARIZE1", anc, p_1q)

            # Step 1: Move into entangling zone → idle decoherence
            c += self.idle_noise(list(moved_qubits), t_move_ns)

            # Step 2: Global entangling pulse (CX) + 2Q depolarizing noise
            for anc, dq in pairs:
                if anc in anc_x:
                    c.append("CX", [anc, dq])
                else:
                    c.append("CX", [dq, anc])
                c.append("DEPOLARIZE2", [anc, dq], p_2q)

            # Step 3: Move back to storage zone → idle decoherence
            c += self.idle_noise(list(moved_qubits), t_move_ns)

            # Undo Hadamard on X ancillas after CX
            for anc, _ in pairs:
                if anc in anc_x:
                    c.append("H", anc)
                    c.append("DEPOLARIZE1", anc, p_1q)

            c.append("TICK")

        # ── Measurement (long step, data qubits idle) ─────────────────────
        # Data qubits experience idle decoherence while ancillas are read out
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
