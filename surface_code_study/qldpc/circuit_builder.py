"""
Circuit builder for qLDPC (BB) code memory experiments using Stim.

Generates a syndrome-extraction circuit from the Tanner graph of a CSS
qLDPC code. For each BB code with check matrices H_X and H_Z:

  - X-check ancillas interact via CNOT(ancilla → data) for each 1 in H_X.
  - Z-check ancillas interact via CNOT(data → ancilla) for each 1 in H_Z.

Noise is injected via stim's standard Pauli error channels following the
same conventions as the existing surface code circuit_builder.py:
  - DEPOLARIZE2 after each CNOT (p_gate_2q)
  - DEPOLARIZE1 after each Hadamard (p_gate_1q)
  - X_ERROR on measurement and reset (p_meas, p_reset)
  - DEPOLARIZE1 on all data qubits per round (p_idle)

References
----------
stim docs: https://github.com/quantumlib/stim
Kovalev & Pryadko, arXiv:1207.0803 — BB code construction
"""

from __future__ import annotations

from typing import List

import numpy as np
import stim

from surface_code_study.qldpc.bb_code import BBCode


def _find_logical_observable(H_X: np.ndarray, H_Z: np.ndarray) -> np.ndarray:
    """
    Find a Z-type logical operator for the CSS code.

    Returns a binary vector v ∈ F_2^n such that:
      - v ∈ ker(H_X)  (commutes with X-checks)
      - v ∉ im(H_Z^T) (not a trivial stabilizer)

    Uses GF(2) Gaussian elimination to compute a basis of
    ker(H_X) / im(H_Z^T).

    Returns
    -------
    np.ndarray of shape (n,) — the data qubit indices where the logical
    Z operator acts (first basis vector of the logical space).
    """
    from surface_code_study.qldpc.bb_code import _rank_gf2

    n = H_X.shape[1]
    m_X = H_X.shape[0]
    m_Z = H_Z.shape[0]

    # Compute nullspace of H_X: vectors v such that H_X @ v = 0
    # Stack [H_X; H_Z] to find vectors in ker(H_X) \ im(H_Z^T)
    # Step 1: find ker(H_X) basis
    aug = H_X.copy() % 2
    # Row-echelon form on augmented matrix to find nullspace
    nrows, ncols = aug.shape
    pivot_col = np.full(nrows, -1, dtype=int)
    row = 0
    for col in range(ncols):
        if row >= nrows:
            break
        pivot = None
        for r in range(row, nrows):
            if aug[r, col]:
                pivot = r
                break
        if pivot is None:
            continue
        aug[[row, pivot]] = aug[[pivot, row]]
        for r in range(nrows):
            if r != row and aug[r, col]:
                aug[r] ^= aug[row]
        pivot_col[row] = col
        row += 1
    r_X = row  # rank of H_X

    # Free columns = columns without pivots
    free_cols = [c for c in range(n) if c not in pivot_col[:r_X]]

    # Build nullspace basis vectors (one per free column)
    nullspace_basis = []
    for free_c in free_cols:
        v = np.zeros(n, dtype=np.int8)
        v[free_c] = 1
        # For each pivot row, set the free column's contribution
        for r in range(r_X):
            pc = pivot_col[r]
            if aug[r, free_c]:
                v[pc] = 1
        nullspace_basis.append(v)

    if not nullspace_basis:
        # No logical qubits — code has k=0
        return np.zeros(n, dtype=np.int8)

    # Filter: remove vectors that are in im(H_Z^T)
    logical_basis = []
    for v in nullspace_basis:
        # Check if v is in the column space of H_Z^T, i.e., row space of H_Z
        # Stack H_Z with v to check if v is a linear combination of H_Z rows
        stacked = np.vstack([H_Z % 2, v.reshape(1, -1)])
        r_before = _rank_gf2(H_Z % 2)
        r_after = _rank_gf2(stacked)
        if r_after > r_before:
            logical_basis.append(v)

    if logical_basis:
        return logical_basis[0]
    # Fallback: return first nullspace vector
    return nullspace_basis[0]


def build_qldpc_circuit(
    code: BBCode,
    rounds: int,
    p_gate_1q: float = 0.0,
    p_gate_2q: float = 0.0,
    p_meas: float = 0.0,
    p_reset: float = 0.0,
    p_idle: float = 0.0,
) -> stim.Circuit:
    """
    Build a qLDPC memory circuit with explicit noise channels.

    Circuit structure (per round):
      1. idle noise on data qubits
      2. X-check extraction: reset → H → CNOTs → H → measure
      3. Z-check extraction: reset → CNOTs → measure
      4. DETECTOR annotations comparing consecutive syndrome measurements

    After the final round, all data qubits are measured in the Z basis.
    A logical observable is defined from the first Z-type logical operator.

    Parameters
    ----------
    code : BBCode
        The BB code with H_X and H_Z check matrices.
    rounds : int
        Number of syndrome-extraction rounds (typically = distance).
    p_gate_1q : float
        Single-qubit gate depolarization probability.
    p_gate_2q : float
        Two-qubit gate depolarization probability.
    p_meas : float
        Measurement bit-flip probability.
    p_reset : float
        Reset bit-flip probability.
    p_idle : float
        Idle depolarization probability per round on each data qubit.

    Returns
    -------
    stim.Circuit
        Noisy circuit with detectors and one logical observable.
    """
    H_X = code.H_X
    H_Z = code.H_Z
    n_data = code.n
    m_X = H_X.shape[0]  # number of X-checks
    m_Z = H_Z.shape[0]  # number of Z-checks
    m_total = m_X + m_Z

    # Qubit index ranges
    x_anc_start = n_data
    z_anc_start = n_data + m_X

    # Precompute neighbour lists for efficient CNOT insertion
    x_neighbors: List[List[int]] = [[] for _ in range(m_X)]
    z_neighbors: List[List[int]] = [[] for _ in range(m_Z)]
    for i in range(m_X):
        for j in range(n_data):
            if H_X[i, j]:
                x_neighbors[i].append(j)
    for i in range(m_Z):
        for j in range(n_data):
            if H_Z[i, j]:
                z_neighbors[i].append(j)

    # Logical observable
    logical_z = _find_logical_observable(H_X, H_Z)

    circuit = stim.Circuit()

    # ── Initialize data qubits in |0⟩ ───────────────────────────────────────
    circuit.append("R", list(range(n_data)))
    if p_reset > 0:
        circuit.append("X_ERROR", list(range(n_data)), p_reset)

    # ── Syndrome extraction rounds ──────────────────────────────────────────
    for r in range(rounds):
        # Idle noise on data qubits (before_round depolarization equivalent)
        if p_idle > 0:
            circuit.append("DEPOLARIZE1", list(range(n_data)), p_idle)

        # ── X-check extraction ──────────────────────────────────────────────
        # Reset X-ancillas
        circuit.append("R", list(range(x_anc_start, x_anc_start + m_X)))
        if p_reset > 0:
            circuit.append("X_ERROR", list(range(x_anc_start, x_anc_start + m_X)), p_reset)

        # Hadamard on X-ancillas
        for i in range(m_X):
            anc = x_anc_start + i
            circuit.append("H", anc)
            if p_gate_1q > 0:
                circuit.append("DEPOLARIZE1", anc, p_gate_1q)

        # CNOT gates: ancilla → data for each 1 in H_X
        for i in range(m_X):
            anc = x_anc_start + i
            for dq in x_neighbors[i]:
                circuit.append("CX", [anc, dq])
                if p_gate_2q > 0:
                    circuit.append("DEPOLARIZE2", [anc, dq], p_gate_2q)

        # Undo Hadamard
        for i in range(m_X):
            anc = x_anc_start + i
            circuit.append("H", anc)
            if p_gate_1q > 0:
                circuit.append("DEPOLARIZE1", anc, p_gate_1q)

        # Measure X-ancillas
        circuit.append("M", list(range(x_anc_start, x_anc_start + m_X)))
        if p_meas > 0:
            circuit.append("X_ERROR", list(range(x_anc_start, x_anc_start + m_X)), p_meas)

        # ── Z-check extraction ──────────────────────────────────────────────
        # Reset Z-ancillas
        circuit.append("R", list(range(z_anc_start, z_anc_start + m_Z)))
        if p_reset > 0:
            circuit.append("X_ERROR", list(range(z_anc_start, z_anc_start + m_Z)), p_reset)

        # CNOT gates: data → ancilla for each 1 in H_Z
        for i in range(m_Z):
            anc = z_anc_start + i
            for dq in z_neighbors[i]:
                circuit.append("CX", [dq, anc])
                if p_gate_2q > 0:
                    circuit.append("DEPOLARIZE2", [dq, anc], p_gate_2q)

        # Measure Z-ancillas
        circuit.append("M", list(range(z_anc_start, z_anc_start + m_Z)))
        if p_meas > 0:
            circuit.append("X_ERROR", list(range(z_anc_start, z_anc_start + m_Z)), p_meas)

        # ── DETECTOR annotations ────────────────────────────────────────────
        # Measurement order within each round: X-checks first, then Z-checks.
        #   rec[-1] .. rec[-m_Z]:          Z-check measurements (last to first)
        #   rec[-(m_Z+1)] .. rec[-m_total]: X-check measurements (last to first)
        #
        # First round: only Z-checks have deterministic outcomes (data qubits
        #   are initialised in |0⟩, a +1 eigenstate of Z). X-check outcomes
        #   are random because |0⟩ is not an X eigenstate.
        # Later rounds: both X and Z detectors compare consecutive measurements.

        if r == 0:
            # Z-check detectors only (X-checks are random in round 0)
            for j in range(m_Z):
                idx = -m_Z + j  # rec index of Z-check j
                circuit.append("DETECTOR", [stim.target_rec(idx)])
        else:
            # X-check detectors: compare round r to round r-1
            for i in range(m_X):
                cur = -m_total + i
                prev = -2 * m_total + i
                circuit.append("DETECTOR", [stim.target_rec(cur), stim.target_rec(prev)])
            # Z-check detectors: compare round r to round r-1
            for j in range(m_Z):
                cur = -m_Z + j
                prev = -m_total - m_Z + j
                circuit.append("DETECTOR", [stim.target_rec(cur), stim.target_rec(prev)])

    # ── Final data qubit measurement ────────────────────────────────────────
    circuit.append("M", list(range(n_data)))

    # ── Logical observable ────────────────────────────────────────────────
    # The logical Z observable is the product of Z measurements on data
    # qubits where logical_z has a 1.
    obs_targets = []
    for i in range(n_data):
        if logical_z[i]:
            # Data qubit i measurement is at rec index: -(n_data - i)
            # rec[-1] is the last data qubit, rec[-n_data] is the first
            obs_targets.append(stim.target_rec(-n_data + i))
    if obs_targets:
        circuit.append("OBSERVABLE_INCLUDE", obs_targets, 0)

    return circuit


# ──────────────────────────────────────────────────────────────────────────────
# Convenience: build circuit from platform parameters
# ──────────────────────────────────────────────────────────────────────────────

def build_qldpc_circuit_from_params(
    code: BBCode,
    rounds: int,
    platform_params: dict,
    noise_scale: float = 1.0,
    p: float | None = None,
) -> stim.Circuit:
    """
    Build a qLDPC circuit with platform noise, mirroring the interface of
    ``build_surface_code_circuit``.

    Parameters
    ----------
    code : BBCode
    rounds : int
    platform_params : dict
        With keys: p_gate_1q, p_gate_2q, p_meas, p_reset, p_idle, relative_scales.
    noise_scale : float
        Scale factor on natural rates (ignored if p is given).
    p : float | None
        Base physical 2Q gate error rate. When provided, all other channels
        scale by the platform's relative_scales.

    Returns
    -------
    stim.Circuit
    """
    if p is not None:
        p_2q = float(p)
        scales = platform_params.get("relative_scales", {})
        p_1q = p_2q * scales.get("gate_1q", 0.3)
        p_meas = p_2q * scales.get("meas", 5.0)
        p_reset = p_2q * scales.get("reset", 0.1)
        p_idle = p_2q * scales.get("idle", 10.0)
    else:
        p_2q = noise_scale * float(platform_params.get("p_gate_2q", 0))
        p_1q = noise_scale * float(platform_params.get("p_gate_1q", 0))
        p_meas = noise_scale * float(platform_params.get("p_meas", 0))
        p_reset = noise_scale * float(platform_params.get("p_reset", 0))
        p_idle = noise_scale * float(platform_params.get("p_idle", 0))

    return build_qldpc_circuit(
        code=code,
        rounds=rounds,
        p_gate_1q=p_1q,
        p_gate_2q=p_2q,
        p_meas=p_meas,
        p_reset=p_reset,
        p_idle=p_idle,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Phenomenological noise variant (lighter-weight, for threshold validation)
# ──────────────────────────────────────────────────────────────────────────────

def build_qldpc_phenomenological_circuit(
    code: BBCode,
    rounds: int,
    p_data: float = 0.0,
    p_meas: float = 0.0,
) -> stim.Circuit:
    """
    Build a qLDPC memory circuit with phenomenological (data + measurement) noise.

    This is a simplified model where:
      - Each data qubit suffers DEPOLARIZE1(p_data) once per round.
      - Each syndrome measurement is flipped with probability p_meas.
      - No explicit gate noise (CNOTs are perfect).

    The resulting DEM is much smaller than the full circuit-level model,
    making BP+OSD decoding tractable for threshold validation.

    Parameters
    ----------
    code : BBCode
    rounds : int
    p_data : float
        Per-round depolarization probability on each data qubit.
    p_meas : float
        Measurement bit-flip probability.
    """
    H_X = code.H_X
    H_Z = code.H_Z
    n_data = code.n
    m_X = H_X.shape[0]
    m_Z = H_Z.shape[0]
    m_total = m_X + m_Z
    x_anc_start = n_data
    z_anc_start = n_data + m_X

    x_neighbors = [[j for j in range(n_data) if H_X[i, j]] for i in range(m_X)]
    z_neighbors = [[j for j in range(n_data) if H_Z[i, j]] for i in range(m_Z)]

    logical_z = _find_logical_observable(H_X, H_Z)

    circuit = stim.Circuit()

    # Initialize data qubits in |0⟩
    circuit.append("R", list(range(n_data)))

    for r in range(rounds):
        # Phenomenological data depolarization
        if p_data > 0:
            circuit.append("DEPOLARIZE1", list(range(n_data)), p_data)

        # ── X-check extraction (noiseless gates) ──
        circuit.append("R", list(range(x_anc_start, x_anc_start + m_X)))
        for i in range(m_X):
            anc = x_anc_start + i
            circuit.append("H", anc)
            for dq in x_neighbors[i]:
                circuit.append("CX", [anc, dq])
            circuit.append("H", anc)
        circuit.append("M", list(range(x_anc_start, x_anc_start + m_X)))
        if p_meas > 0:
            circuit.append("X_ERROR", list(range(x_anc_start, x_anc_start + m_X)), p_meas)

        # ── Z-check extraction (noiseless gates) ──
        circuit.append("R", list(range(z_anc_start, z_anc_start + m_Z)))
        for i in range(m_Z):
            anc = z_anc_start + i
            for dq in z_neighbors[i]:
                circuit.append("CX", [dq, anc])
        circuit.append("M", list(range(z_anc_start, z_anc_start + m_Z)))
        if p_meas > 0:
            circuit.append("X_ERROR", list(range(z_anc_start, z_anc_start + m_Z)), p_meas)

        # DETECTOR annotations
        if r == 0:
            for j in range(m_Z):
                circuit.append("DETECTOR", [stim.target_rec(-m_Z + j)])
        else:
            for i in range(m_X):
                cur = -m_total + i
                prev = -2 * m_total + i
                circuit.append("DETECTOR", [stim.target_rec(cur), stim.target_rec(prev)])
            for j in range(m_Z):
                cur = -m_Z + j
                prev = -m_total - m_Z + j
                circuit.append("DETECTOR", [stim.target_rec(cur), stim.target_rec(prev)])

    # Final data qubit measurement
    circuit.append("M", list(range(n_data)))

    # Logical observable
    obs_targets = [stim.target_rec(-n_data + i) for i in range(n_data) if logical_z[i]]
    if obs_targets:
        circuit.append("OBSERVABLE_INCLUDE", obs_targets, 0)

    return circuit


# ──────────────────────────────────────────────────────────────────────────────
# Quick sanity check
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from surface_code_study.qldpc.bb_code import build_bb_code_72_12_6

    code = build_bb_code_72_12_6()
    print(f"Code: n={code.n}, k={code.k}")
    print(f"H_X: {code.H_X.shape}, density={np.mean(code.H_X):.4f}")
    print(f"H_Z: {code.H_Z.shape}, density={np.mean(code.H_Z):.4f}")

    circ = build_qldpc_circuit(
        code, rounds=6,
        p_gate_1q=0.001, p_gate_2q=0.01,
        p_meas=0.01, p_reset=0.001, p_idle=0.001,
    )
    print(f"\nCircuit stats:")
    print(f"  num_qubits     = {circ.num_qubits}")
    print(f"  num_operations = {len(circ)}")
    print(f"  num_detectors  = {circ.num_detectors}")
    print(f"  num_observables= {circ.num_observables}")

    dem_raw = circ.detector_error_model(decompose_errors=False)
    print(f"  DEM instructions (raw) = {len(dem_raw)}")
    print(f"\nFirst 5 DEM instructions:")
    for inst in list(dem_raw)[:5]:
        print(f"  {inst}")
