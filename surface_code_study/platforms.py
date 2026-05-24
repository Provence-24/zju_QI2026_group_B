"""
Platform-specific noise parameters for surface code simulations.

All parameters are drawn from recent literature (2024-2025).
Each platform's internal ratio (e.g. p_meas / p_gate_2q) is preserved as
a signature, while an overall scale factor ``p`` is used to sweep the
logical error rate in experiments.

References
----------
Superconducting (Google Willow):
    "Quantum error correction below the surface code threshold"
    Google Quantum AI, arXiv:2408.13687 (2024)
    See also: Nature 640, 61-67 (2025) — "Willow" chip results

Neutral Atoms (Harvard/QuEra):
    "Logical qubits with neutral atoms" (Bluvstein et al.)
    arXiv:2312.13231, Nature 627, 263-269 (2024)

Ion Traps (Quantinuum H2):
    Quantinuum H2 Technical Brief (2024)
    "Quantinuum H2 Quantum Computer" — specifications
    p_meas from: "Demonstration of quantum accuracy at the 100-qubit scale"
    (Quantinuum, 2025)
"""

from dataclasses import dataclass
from typing import NamedTuple


class PlatformParams(NamedTuple):
    """Noise parameters for a quantum platform.

    Units are physical error probabilities (dimensionless).
    All values are per-operation rates unless noted.

    Attributes
    ----------
    p_gate_1q : float
        Single-qubit Clifford gate error rate.
    p_gate_2q : float
        Two-qubit Clifford gate error rate (dominant term).
    p_meas : float
        Measurement error rate (bit-flip probability per measurement).
    p_reset : float
        Reset/initialization error rate.
    p_idle : float
        Idle depolarization rate per cycle (data qubit, per unit time).
        In stim's model this is converted via cycle_time.
    cycle_time_us : float
        Physical duration of one syndrome-extraction cycle (microseconds).
        Used for context only; does not affect the logical error rate in
        our simplified model.
    T1_us : float
        T1 relaxation time (microseconds). Used by PlatformCompiler to
        compute physically accurate idle decoherence via Pauli channel.
    T2_us : float
        T2 dephasing time (microseconds). Clamped to T2 ≤ 2*T1.
    relative_scales : dict[str, float]
        Platform-internal scaling factors relative to a base error rate.
        Keys: "gate_1q", "gate_2q", "meas", "reset", "idle".
        These ratios are what make each platform distinctive.
    """

    p_gate_1q: float
    p_gate_2q: float
    p_meas: float
    p_reset: float
    p_idle: float
    cycle_time_us: float
    T1_us: float
    T2_us: float
    relative_scales: dict[str, float]


# ──────────────────────────────────────────────────────────────────────────────
# Platform definitions
# ──────────────────────────────────────────────────────────────────────────────

def _build_superconducting() -> PlatformParams:
    """
    Google Willow (Nature 2024/2025).

    Source: Google Quantum AI, arXiv:2408.13687 (2024).
    Two-qubit gate fidelity: ~99.9 % → p_2q ≈ 0.1 % (adjacent gates).
    Single-qubit gate fidelity: ~99.97 % → p_1q ≈ 3×10⁻⁴.
    Measurement fidelity: ~99.5 % → p_meas ≈ 0.5 %.
    Reset fidelity: ~99.99 % → p_reset ≈ 10⁻⁴.
    Idle T2 ≈ 100 μs, cycle ≈ 1 μs → p_idle ≈ 1 % per cycle.

    Note: p_idle here is the *probability* per cycle that a data qubit
    depolarizes, consistent with stim's before_round_data_depolarization.

    T1 ≈ 100 μs, T2 ≈ 100 μs (Willow transmon qubits, Nature 2025).
    T2 is typically limited by T1 in transmons.
    """
    return PlatformParams(
        p_gate_1q=3e-4,          # 0.03 % — Google's best 1q gate fidelity
        p_gate_2q=1e-3,         # 0.10 % — adjacent 2q gates on Willow
        p_meas=5e-3,            # 0.50 % — measurement error
        p_reset=1e-4,           # 0.01 % — reset fidelity 99.99 %
        p_idle=1e-2,            # 1.0 %  — T2≈100μs, cycle≈1μs → ~1% per cycle
        cycle_time_us=1.0,      # 1 μs per syndrome round
        T1_us=100.0,            # 100 μs — transmon T1 (Willow, Nature 2025)
        T2_us=100.0,            # 100 μs — transmon T2 ≈ T1
        relative_scales={
            "gate_1q": 0.3,     # p_gate_1q / p_gate_2q = 0.3
            "gate_2q": 1.0,      # baseline
            "meas":    5.0,      # p_meas / p_gate_2q = 5
            "reset":   0.1,     # p_reset / p_gate_2q = 0.1
            "idle":   10.0,     # p_idle / p_gate_2q = 10
        },
    )


def _build_neutral_atom() -> PlatformParams:
    """
    Harvard / QuEra neutral atoms (Nature 2024, Bluvstein et al.).

    Source: Bluvstein et al., arXiv:2312.13231 (2023);
            published in Nature 627, 263-269 (2024).

    Rydberg-mediated two-qubit gates: fidelity ~99.4 % → p_2q ≈ 0.6 %.
    Single-qubit gates: fidelity ~99.9 % → p_1q ≈ 1×10⁻³.
    Measurement: ~99.5 % → p_meas ≈ 0.5 %.
    Reset: ~99.5 % → p_reset ≈ 0.5 % (laser cooling, less mature).
    Idle: T2(r) ~ ms range, cycle ~ 1 μs → p_idle ~ 0.1 % per cycle
          (estimate; neutral atoms have excellent coherence).

    Storage zone: T1 ~ 1 s (ground state), T2 ~ 1 ms (magnetic noise limit).
    Note: "estimate,待校准" values are based on typical published ranges
    and the specific experimental conditions in Bluvstein 2024.
    """
    return PlatformParams(
        p_gate_1q=1e-3,          # 0.10 % — single-qubit gate fidelity ~99.9 %
        p_gate_2q=6e-3,          # 0.60 % — Rydberg 2q gates, Nature 2024
        p_meas=5e-3,            # 0.50 % — measurement fidelity ~99.5 %
        p_reset=5e-3,           # 0.50 % — estimate,待校准; laser cooling overhead
        p_idle=1e-3,            # 0.10 % — estimate,待校准; T2~1ms, cycle~1μs
        cycle_time_us=1.0,      # 1 μs per syndrome round (typical)
        T1_us=1e6,              # 1 s — ground-state storage T1
        T2_us=1e3,              # 1 ms — magnetic noise / light shift limit
        relative_scales={
            "gate_1q": 0.17,     # p_gate_1q / p_gate_2q ≈ 1/6
            "gate_2q": 1.0,      # baseline
            "meas":    0.83,     # p_meas / p_gate_2q ≈ 5/6
            "reset":   0.83,     # p_reset / p_gate_2q ≈ 5/6
            "idle":    0.17,     # p_idle / p_gate_2q ≈ 1/6
        },
    )


def _build_ion_trap() -> PlatformParams:
    """
    Quantinuum H2 (2024-2025).

    Sources:
      - Quantinuum H2 Technical Brief (2024)
      - "Demonstration of quantum accuracy at the 100-qubit scale"
        (Quantinuum, 2025) — measurement error ~0.6 % (corrected).
      - Mølmer-Sørensen gates: two-qubit fidelity ~99.9 % → p_2q ≈ 1×10⁻³.
      - Single-qubit gates: fidelity ~99.99 % → p_1q ≈ 1×10⁻⁴.
      - Long coherence: T2 > 1 s → negligible idle error per cycle.

    Note: Quantinuum's strength is gate fidelity; measurement error is
    higher than superconducting due to readout cross-talk in traps.
    All values are based on published specs and may be updated with
    newer校准数据.
    """
    return PlatformParams(
        p_gate_1q=1e-4,          # 0.01 % — Mølmer-Sørensen 1q fidelity ~99.99 %
        p_gate_2q=1e-3,         # 0.10 % — 2q gate fidelity ~99.9 %
        p_meas=6e-3,            # 0.60 % — Quantinuum 2025 corrected measurement
        p_reset=1e-3,           # 0.10 % — estimate,待校准; ion replenishment
        p_idle=1e-6,            # negligible — T2 > 1 s, cycle ~10 μs
        cycle_time_us=10.0,     # 10 μs per gate operation (Mølmer-Sørensen)
        T1_us=1e7,              # >10 s — trapped ion ground state T1
        T2_us=1e7,              # >10 s — ultra-long coherence in trap
        relative_scales={
            "gate_1q": 0.1,      # p_gate_1q / p_gate_2q = 0.1
            "gate_2q": 1.0,     # baseline
            "meas":    6.0,     # p_meas / p_gate_2q = 6
            "reset":   1.0,     # p_reset / p_gate_2q = 1
            "idle":    1e-3,    # p_idle / p_gate_2q ≈ 0 (negligible)
        },
    )


# ──────────────────────────────────────────────────────────────────────────────
# Registry
# ──────────────────────────────────────────────────────────────────────────────

SUPERCONDUCTING = "superconducting"
NEUTRAL_ATOM    = "neutral_atom"
ION_TRAP        = "ion_trap"

PLATFORMS: dict[str, PlatformParams] = {
    SUPERCONDUCTING: _build_superconducting(),
    NEUTRAL_ATOM:    _build_neutral_atom(),
    ION_TRAP:        _build_ion_trap(),
}


def get_platform(name: str) -> PlatformParams:
    """Return the PlatformParams for a named platform."""
    if name not in PLATFORMS:
        raise KeyError(f"Unknown platform {name!r}. Available: {list(PLATFORMS)}")
    return PLATFORMS[name]


def all_platforms() -> list[tuple[str, PlatformParams]]:
    """Return [(name, params), ...] for all registered platforms."""
    return list(PLATFORMS.items())
