"""
Circuit builder for rotated surface code memory experiments using Stim.

Uses stim.Circuit.generated() with the "surface_code:rotated_memory_z" task,
which produces an ideal fault-tolerant memory experiment with detectors and
an observable. We map platform noise parameters onto stim's built-in error
channels while preserving each platform's internal error ratios.

Physical error rate p — interface design
-----------------------------------------
The user wants to sweep physical error rate p ∈ [0.001%, 1%] as the x-axis.
We provide two ways to set the noise level:

  1. noise_scale (default 1.0): scales all of a platform's natural rates.
     noise_scale=1.0 → platform's natural operating point.
     noise_scale=0.5 → half of natural rates.

  2. p (overrides noise_scale when provided): interpret p as the "base
     physical error rate" applied to the platform's p_gate_2q channel, with
     all other channels scaled by the platform's internal ratios.

     For example, superconducting with p=0.001 sets p_gate_2q=0.001 (matching
     Google's reported 2Q fidelity) and scales other channels by their
     natural ratios: p_idle = 0.001 * 10 = 0.01, p_meas = 0.001 * 5 = 0.005.

     Ion trap with p=0.001 sets p_gate_2q=0.001 but p_meas = 0.001 * 6 = 0.006
     and p_idle ≈ 0 (since ion trap idle error is negligible).

This means the same p value represents the same 2Q gate error probability
across all platforms, which is the most hardware-relevant single number.

References
----------
stim docs: https://github.com/quantumlib/stim
  Circuit.generated(task, distance, rounds, ...)
"""

from __future__ import annotations

import stim


def build_surface_code_circuit(
    d: int,
    platform_params: dict,
    rounds: int | None = None,
    noise_scale: float = 1.0,
    p: float | None = None,
) -> stim.Circuit:
    """
    Build a rotated surface code memory circuit with platform noise.

    Parameters
    ----------
    d : int
        Code distance. Rounds defaults to d (standard for memory experiments).
    platform_params : dict
        Dictionary with keys: p_gate_1q, p_gate_2q, p_meas, p_reset, p_idle,
        relative_scales.
    rounds : int | None
        Number of syndrome-extraction rounds. Defaults to d.
    noise_scale : float
        Global scale factor s ∈ (0, ∞). Scales all platform error channels.
        noise_scale=1.0 → natural operating point.  noise_scale=0 → perfect.
        Ignored if ``p`` is provided.
    p : float | None
        Physical error rate (base). When provided, overrides noise_scale.
        Interpreted as the target p_gate_2q value; all other channels are
        set proportionally to their relative_scales.
        For example, p=0.001 with superconducting (scales["gate_2q"]=1.0,
        scales["idle"]=10.0) gives p_gate_2q=0.001, p_idle=0.01.

    Returns
    -------
    stim.Circuit
        Stim circuit with detectors and one logical observable.
    """
    if rounds is None:
        rounds = d

    if p is not None:
        # p is the base physical error rate → use it as p_gate_2q and scale
        # other channels by the platform's relative ratios.
        p_2q   = float(p)
        scales = platform_params.get("relative_scales", {})
        p_1q   = p_2q * scales.get("gate_1q", 0.3)
        p_meas = p_2q * scales.get("meas", 5.0)
        p_reset = p_2q * scales.get("reset", 0.1)
        p_idle = p_2q * scales.get("idle", 10.0)
    else:
        # Scale platform's natural rates by noise_scale
        p_2q   = noise_scale * float(platform_params["p_gate_2q"])
        p_1q   = noise_scale * float(platform_params["p_gate_1q"])
        p_meas = noise_scale * float(platform_params["p_meas"])
        p_reset = noise_scale * float(platform_params["p_reset"])
        p_idle = noise_scale * float(platform_params["p_idle"])

    # after_clifford_depolarization is the per-Clifford-gate depolarization.
    # We attribute all 2Q gate errors here; 1Q gate errors are folded in as
    # a small fraction of p_2q (consistent with p_1q << p_2q in real platforms).
    after_clifford_depol = p_2q
    # before_round_data_depolarization is applied to each data qubit each round.
    before_round_data_depol = p_idle
    # Measurement and reset bit-flip probabilities
    before_measure_flip = p_meas
    after_reset_flip = p_reset

    circuit = stim.Circuit.generated(
        "surface_code:rotated_memory_z",
        distance=d,
        rounds=rounds,
        after_clifford_depolarization=after_clifford_depol,
        before_round_data_depolarization=before_round_data_depol,
        after_reset_flip_probability=after_reset_flip,
        before_measure_flip_probability=before_measure_flip,
    )

    return circuit


def build_perfect_circuit(d: int, rounds: int | None = None) -> stim.Circuit:
    """
    Build a perfect (no-noise) rotated surface code memory circuit.

    Useful for verifying that PL = 0 when noise is absent.
    """
    if rounds is None:
        rounds = d
    return stim.Circuit.generated(
        "surface_code:rotated_memory_z",
        distance=d,
        rounds=rounds,
        after_clifford_depolarization=0.0,
        before_round_data_depolarization=0.0,
        after_reset_flip_probability=0.0,
        before_measure_flip_probability=0.0,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Quick sanity check
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json

    from surface_code_study.platforms import SUPERCONDUCTING, get_platform

    platform = get_platform(SUPERCONDUCTING)
    params = platform._asdict()

    print(f"Building d=3 circuit for {SUPERCONDUCTING} at natural operating point ...")
    circ = build_surface_code_circuit(d=3, platform_params=params, noise_scale=1.0)

    # Also demonstrate the p-based interface (p = physical 2Q gate error rate)
    print(f"\nBuilding d=3 circuit for {SUPERCONDUCTING} with p=0.001 (0.1% 2Q gate error) ...")
    circ_p = build_surface_code_circuit(d=3, platform_params=params, p=0.001)
    print(f"  num_qubits={circ_p.num_qubits}, num_detectors={circ_p.num_detectors}")

    print(f"\nCircuit stats (natural rates):")
    print(f"  num_qubits     = {circ.num_qubits}")
    print(f"  num_operations = {len(circ)}")
    print(f"  num_detectors  = {circ.num_detectors}")
    print(f"  num_observables= {circ.num_observables}")

    # Show detector error model
    dem = circ.detector_error_model(decompose_errors=True)
    print(f"\nDetector error model ({len(dem)} entries):")
    print(dem)

    # Perfect circuit test
    print("\nBuilding perfect d=3 circuit (noise_scale=0) ...")
    perfect = build_perfect_circuit(d=3)
    perfect_dem = perfect.detector_error_model(decompose_errors=True)
    print(f"Perfect circuit num_detectors = {perfect.num_detectors}")
    print(f"Perfect DEM has {len(perfect_dem)} entries (should be small/empty)")
