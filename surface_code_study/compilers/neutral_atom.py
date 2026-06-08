"""
Neutral atom platform compiler.

Models the Harvard/QuEra dual-zone architecture (Bluvstein 2024):
  - Storage zone: atoms in ground-state hyperfine qubit, T1 ~ 1 s, T2 ~ 1 ms.
  - Entangling zone: Rydberg-mediated global CZ pulses. During gate operation
    atoms are in a Rydberg state with lifetime ~100 us and correspondingly
    worse coherence.

Syndrome extraction is broken into movement batches. Each batch:
  1. Move selected (ancilla, data) pairs into the entangling zone
     → all qubits idle in storage with storage-zone T1/T2 (moved atoms
       remain in ground state during optical-tweezer transport).
  2. Gate: atoms in entangling zone are excited to Rydberg state
     → Rydberg T1/T2 idle on gated atoms + storage T1/T2 on idle atoms
     → apply global CZ pulse + DEPOLARIZE2 on all pairs in the zone
  3. Move them back to storage zone
     → all qubits idle with storage-zone T1/T2

Because t_move_ns (100-500 us) >> t_gate_ns (~0.1 us), movement-induced
decoherence is the dominant noise mechanism. However, Rydberg-state
decoherence during the gate pulse is non-negligible (~0.1% per gate)
and is now modeled separately from the gate depolarizing error.
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
        t_gate_ns = self.params.get('t_gate_ns', 100)
        t_meas_ns = self.params.get('t_cycle_ns', 200_000) * 0.9

        # Zone-specific coherence times
        # Storage zone: ground-state atoms, excellent coherence
        T1_s = self.params.get('T1_storage_us', self.params['T1_us'])
        T2_s = self.params.get('T2_storage_us', self.params['T2_us'])
        # Rydberg state: finite radiative lifetime, worse coherence
        T1_r = self.params.get('T1_rydberg_us', 100.0)
        T2_r = self.params.get('T2_rydberg_us', 100.0)

        # ── TICK 1: ancilla initialization ────────────────────────────────
        c.append("R", all_anc)
        c.append("X_ERROR", all_anc, p_reset)
        for q in all_anc:
            c.append("DEPOLARIZE1", q, p_1q)
        c.append("TICK")

        # ── Movement batches: move → CZ → move back ───────────────────────
        batches = self._schedule_movement_batches()

        for batch_idx, pairs in enumerate(batches):
            moved_qubits = set()
            for anc, dq in pairs:
                moved_qubits.add(anc)
                moved_qubits.add(dq)

            # Hadamard on X ancillas before CX
            for anc, _ in pairs:
                if anc in anc_x:
                    c.append("H", anc)
                    c.append("DEPOLARIZE1", anc, p_1q)

            # Step 1: Move into entangling zone
            # All qubits idle in storage (moved atoms are in ground state
            # during optical-tweezer transport; unmoved atoms wait in storage).
            c += self.idle_noise(self.all_qubits, t_move_ns, T1_s, T2_s)

            # Step 2: Global entangling pulse + Rydberg decoherence
            # Participating atoms are excited to Rydberg state with shorter
            # lifetime. Non-participating atoms remain in storage.
            c += self.idle_noise(list(moved_qubits), t_gate_ns, T1_r, T2_r)
            c += self.idle_noise_except(list(moved_qubits), t_gate_ns, T1_s, T2_s)

            for anc, dq in pairs:
                if anc in anc_x:
                    c.append("CX", [anc, dq])
                else:
                    c.append("CX", [dq, anc])
                c.append("DEPOLARIZE2", [anc, dq], p_2q)

            # Step 3: Move back to storage zone
            # All qubits idle with storage coherence (ground-state transport).
            c += self.idle_noise(self.all_qubits, t_move_ns, T1_s, T2_s)

            # Undo Hadamard on X ancillas after CX
            for anc, _ in pairs:
                if anc in anc_x:
                    c.append("H", anc)
                    c.append("DEPOLARIZE1", anc, p_1q)

            c.append("TICK")

        # ── Measurement (data qubits idle in storage) ─────────────────────
        c += self.idle_noise(data, t_meas_ns, T1_s, T2_s)

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
