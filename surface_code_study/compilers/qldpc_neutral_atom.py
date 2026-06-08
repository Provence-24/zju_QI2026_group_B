"""
Neutral atom platform compiler for qLDPC (BB) codes.

Extends the dual-zone architecture from the surface code compiler to
handle the non-local connectivity of qLDPC codes. Each check in the
Tanner graph requires moving its ancilla and connected data qubits
from the storage zone into the entangling zone for Rydberg-mediated
CZ gates, then back to storage.

Key differences from the surface code compiler:
  - No 2D grid layout; connectivity is defined by the Tanner graph.
  - Checks are batched using greedy graph coloring to parallelise
    non-conflicting movements within each round.
  - Movement-induced decoherence is proportional to the number of
    batches (each batch = one round-trip shuttling cycle).

The physical model is consistent with the existing NeutralAtomCompiler:
  - Storage zone: T1 ~ 1 s, T2 ~ 1 ms (ground-state hyperfine qubit)
  - Entangling zone: T1 ~ 100 us, T2 ~ 100 us (Rydberg state)
  - Movement time per batch: ~200 us (optical tweezer transport)
  - Gate time: ~0.1 us (Rydberg CZ pulse)
"""

from __future__ import annotations

import stim
import numpy as np

from surface_code_study.compilers.base import PlatformCompiler
from surface_code_study.qldpc.bb_code import BBCode
from surface_code_study.qldpc.circuit_builder import _find_logical_observable


class NeutralAtomQLDPCCompiler(PlatformCompiler):
    """Platform-aware compiler for qLDPC codes on neutral atom hardware."""

    def __init__(self, code: BBCode, noise_params: dict):
        """
        Parameters
        ----------
        code : BBCode
            The BB code to compile.
        noise_params : dict
            Platform noise parameters (same format as NeutralAtomCompiler).
            Must contain: p_1q, p_2q, p_meas, p_reset, T1_us, T2_us.
            Optional: t_move_ns, t_gate_ns, T1_storage_us, T2_storage_us,
                      T1_rydberg_us, T2_rydberg_us.
        """
        self._bb_code = code
        # Call base with distance=0 (not meaningful for qLDPC)
        super().__init__(distance=0, noise_params=noise_params)

    # ------------------------------------------------------------------
    # Layout (Tanner graph → qubit index assignment)
    # ------------------------------------------------------------------

    def _init_layout(self) -> dict:
        H_X = self._bb_code.H_X
        H_Z = self._bb_code.H_Z
        n_data = self._bb_code.n
        m_X = H_X.shape[0]
        m_Z = H_Z.shape[0]

        x_anc_start = n_data
        z_anc_start = n_data + m_X

        # Build neighbour lists
        x_checks = []
        for i in range(m_X):
            nbrs = [j for j in range(n_data) if H_X[i, j]]
            x_checks.append((i, x_anc_start + i, nbrs))

        z_checks = []
        for i in range(m_Z):
            nbrs = [j for j in range(n_data) if H_Z[i, j]]
            z_checks.append((i, z_anc_start + i, nbrs))

        # 1D coordinates for stim
        data_coords = {i: (float(i), 0.0) for i in range(n_data)}
        ancilla_coords = {}
        for i in range(m_X):
            ancilla_coords[x_anc_start + i] = (float(n_data + i), 0.0)
        for i in range(m_Z):
            ancilla_coords[z_anc_start + i] = (float(n_data + m_X + i), 0.0)

        return {
            'data': list(range(n_data)),
            'ancilla_x': list(range(x_anc_start, x_anc_start + m_X)),
            'ancilla_z': list(range(z_anc_start, z_anc_start + m_Z)),
            'ancillas': list(range(x_anc_start, z_anc_start + m_Z)),
            'x_checks': x_checks,   # [(check_idx, anc_idx, [dq_idx, ...]), ...]
            'z_checks': z_checks,
            'data_coords': data_coords,
            'ancilla_coords': ancilla_coords,
        }

    # ------------------------------------------------------------------
    # Batch scheduling (greedy graph coloring)
    # ------------------------------------------------------------------

    def _batch_checks(
        self, checks: list[tuple[int, int, list[int]]]
    ) -> list[list[tuple[int, int, list[int]]]]:
        """
        Partition checks into non-conflicting batches using greedy coloring.

        Two checks conflict if they share any data qubit, since both would
        need to be in the entangling zone simultaneously for a global gate.

        Returns a list of batches, each batch is a list of
        (check_idx, anc_idx, [dq_indices]) tuples.
        """
        if not checks:
            return []

        # Build conflict graph: each check conflicts with checks sharing a data qubit
        # Map data qubit → list of check indices that touch it
        dq_to_checks: dict[int, list[int]] = {}
        for c_idx, (check_i, anc, nbrs) in enumerate(checks):
            for dq in nbrs:
                dq_to_checks.setdefault(dq, []).append(c_idx)

        n = len(checks)
        conflict_adj = [set() for _ in range(n)]
        for dq, c_list in dq_to_checks.items():
            for a in c_list:
                for b in c_list:
                    if a != b:
                        conflict_adj[a].add(b)
                        conflict_adj[b].add(a)

        # Greedy coloring: sort by degree (largest first, Welsh-Powell heuristic)
        order = sorted(range(n), key=lambda i: -len(conflict_adj[i]))
        color = [-1] * n

        for c_idx in order:
            used_colors = {color[neighbor] for neighbor in conflict_adj[c_idx]
                          if color[neighbor] >= 0}
            col = 0
            while col in used_colors:
                col += 1
            color[c_idx] = col

        num_batches = max(color) + 1 if color else 0
        batches = [[] for _ in range(num_batches)]
        for c_idx, col in enumerate(color):
            batches[col].append(checks[c_idx])

        return batches

    # ------------------------------------------------------------------
    # Syndrome extraction round
    # ------------------------------------------------------------------

    def build_round(self, is_first_round: bool = False) -> stim.Circuit:
        c = stim.Circuit()
        anc_x = self._layout['ancilla_x']
        anc_z = self._layout['ancilla_z']
        all_anc = anc_x + anc_z
        data = self._layout['data']
        x_checks = self._layout['x_checks']
        z_checks = self._layout['z_checks']

        p_1q   = self.params['p_1q']
        p_2q   = self.params['p_2q']
        p_meas = self.params['p_meas']
        p_reset = self.params['p_reset']
        t_move_ns = self.params.get('t_move_ns', 200_000)
        t_gate_ns = self.params.get('t_gate_ns', 100)
        t_meas_ns = self.params.get('t_cycle_ns', 200_000) * 0.9

        T1_s = self.params.get('T1_storage_us', self.params['T1_us'])
        T2_s = self.params.get('T2_storage_us', self.params['T2_us'])
        T1_r = self.params.get('T1_rydberg_us', 100.0)
        T2_r = self.params.get('T2_rydberg_us', 100.0)

        # ── Batch X-checks ────────────────────────────────────────────────
        x_batches = self._batch_checks(x_checks)
        z_batches = self._batch_checks(z_checks)

        # ── TICK 1: ancilla initialization ──────────────────────────────────
        c.append("R", all_anc)
        c.append("X_ERROR", all_anc, p_reset)
        for q in all_anc:
            c.append("DEPOLARIZE1", q, p_1q)
        c.append("TICK")

        # ── X-check extraction (shuttling model) ────────────────────────────
        for batch in x_batches:
            moved_qubits = set()
            for _, anc, nbrs in batch:
                moved_qubits.add(anc)
                for dq in nbrs:
                    moved_qubits.add(dq)

            # Hadamard on X ancillas
            for _, anc, _ in batch:
                c.append("H", anc)
                c.append("DEPOLARIZE1", anc, p_1q)

            # Move into entangling zone → all qubits idle in storage
            c += self.idle_noise(self.all_qubits, t_move_ns, T1_s, T2_s)

            # Rydberg gate: entangling zone qubits in Rydberg state
            moved_list = list(moved_qubits)
            c += self.idle_noise(moved_list, t_gate_ns, T1_r, T2_r)
            c += self.idle_noise_except(moved_list, t_gate_ns, T1_s, T2_s)

            # CNOT gates
            for _, anc, nbrs in batch:
                for dq in nbrs:
                    c.append("CX", [anc, dq])
                    c.append("DEPOLARIZE2", [anc, dq], p_2q)

            # Move back to storage zone
            c += self.idle_noise(self.all_qubits, t_move_ns, T1_s, T2_s)

            # Undo Hadamard
            for _, anc, _ in batch:
                c.append("H", anc)
                c.append("DEPOLARIZE1", anc, p_1q)

            c.append("TICK")

        # ── Measurement: X-ancillas ────────────────────────────────────────
        c += self.idle_noise(data, t_meas_ns, T1_s, T2_s)
        c.append("M", anc_x)
        c.append("X_ERROR", anc_x, p_meas)

        # ── Z-check extraction (shuttling model) ────────────────────────────
        for batch in z_batches:
            moved_qubits = set()
            for _, anc, nbrs in batch:
                moved_qubits.add(anc)
                for dq in nbrs:
                    moved_qubits.add(dq)

            # Move into entangling zone
            c += self.idle_noise(self.all_qubits, t_move_ns, T1_s, T2_s)

            # Rydberg gate
            moved_list = list(moved_qubits)
            c += self.idle_noise(moved_list, t_gate_ns, T1_r, T2_r)
            c += self.idle_noise_except(moved_list, t_gate_ns, T1_s, T2_s)

            # CNOT gates (data → ancilla for Z-checks)
            for _, anc, nbrs in batch:
                for dq in nbrs:
                    c.append("CX", [dq, anc])
                    c.append("DEPOLARIZE2", [dq, anc], p_2q)

            # Move back to storage zone
            c += self.idle_noise(self.all_qubits, t_move_ns, T1_s, T2_s)

            c.append("TICK")

        # ── Measurement: Z-ancillas ────────────────────────────────────────
        c += self.idle_noise(data, t_meas_ns, T1_s, T2_s)
        c.append("M", anc_z)
        c.append("X_ERROR", anc_z, p_meas)

        # ── DETECTOR markers ────────────────────────────────────────────────
        n_x = len(anc_x)
        n_z = len(anc_z)
        n_all = n_x + n_z

        if is_first_round:
            # Only Z-checks are deterministic in round 0
            for j in range(n_z):
                c.append("DETECTOR", [stim.target_rec(-n_z + j)])
        else:
            for i in range(n_x):
                cur = -n_all + i
                prev = -2 * n_all + i
                c.append("DETECTOR", [stim.target_rec(cur), stim.target_rec(prev)])
            for j in range(n_z):
                cur = -n_z + j
                prev = -n_all - n_z + j
                c.append("DETECTOR", [stim.target_rec(cur), stim.target_rec(prev)])

        return c

    # ------------------------------------------------------------------
    # Full memory circuit (overrides base for qLDPC logical observable)
    # ------------------------------------------------------------------

    def build_memory_circuit(self, num_rounds: int) -> stim.Circuit:
        circuit = stim.Circuit()

        # Qubit coordinates
        all_coords = dict(self._layout['data_coords'])
        if 'ancilla_coords' in self._layout:
            all_coords.update(self._layout['ancilla_coords'])
        for qidx in sorted(all_coords.keys()):
            r, c = all_coords[qidx]
            circuit.append("QUBIT_COORDS", [qidx], [float(r), float(c)])

        # Initialize data qubits
        data = self._layout['data']
        circuit.append("R", data)
        circuit.append("X_ERROR", data, self.params['p_reset'])

        # Syndrome extraction rounds
        for i in range(num_rounds):
            circuit += self.build_round(is_first_round=(i == 0))

        # Final data qubit measurement
        circuit.append("M", data)

        # Logical observable (qLDPC-specific)
        circuit += self._add_qldpc_observable()

        return circuit

    def _add_qldpc_observable(self) -> stim.Circuit:
        """
        Define the logical Z observable for the qLDPC code.

        Uses the first Z-type logical operator (ker(H_X) \ im(H_Z^T)).
        References the final data qubit measurements via rec targets.
        """
        obs_circuit = stim.Circuit()
        logical_z = _find_logical_observable(
            self._bb_code.H_X, self._bb_code.H_Z
        )
        n_data = self._bb_code.n
        if np.any(logical_z):
            targets = [
                stim.target_rec(-n_data + i)
                for i in range(n_data) if logical_z[i]
            ]
            obs_circuit.append("OBSERVABLE_INCLUDE", targets, 0)
        return obs_circuit

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def all_qubits(self) -> list[int]:
        return self._layout['data'] + self._layout['ancillas']
