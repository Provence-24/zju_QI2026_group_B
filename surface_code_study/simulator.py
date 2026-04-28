"""
Simulator for surface code memory experiments.

Performs the full pipeline:
  1. Sample syndrome bits (detectors) and logical observable from a stim circuit
  2. Decode using pymatching (MWPM)
  3. Compare decoded outcome to ground truth
  4. Accumulate statistics and compute PL (per-logical error rate per cycle)

The per-cycle logical error rate is computed from the per-run logical error
probability P_run via:

    PL = (1 - (1 - 2·P_run)^(1/R)) / 2

where R is the number of syndrome-extraction rounds. This formula accounts for
the fact that a logical error may occur in any of the R rounds (single
approximation, valid when PL·R ≪ 1).

References
----------
Fowler et al., "Surface codes: Towards practical large-scale quantum computation"
    PRA 86, 032324 (2012) — Eq. (1) and surrounding discussion.
"""

from __future__ import annotations

import time
from typing import Callable

import numpy as np
import stim
import pymatching

from surface_code_study.circuit_builder import build_perfect_circuit


# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────

MIN_LOGICAL_ERRORS: int = 100
"""Minimum number of logical errors to accumulate for 10% relative error."""

MAX_SHOTS: int = 10_000_000
"""Hard upper bound on number of shots per experiment."""

PL_RELATIVE_ERROR: float = 0.10
"""Target relative error on PL estimate (1 sigma)."""


# ──────────────────────────────────────────────────────────────────────────────
# Core simulation functions
# ──────────────────────────────────────────────────────────────────────────────

def compute_pl_per_cycle(
    num_logical_errors: int,
    num_rounds: int,
    num_shots: int,
) -> float:
    """
    Convert a raw logical error count into a per-logical-per-cycle PL estimate.

    Parameters
    ----------
    num_logical_errors : int
        Number of shots in which the decoded logical observable was wrong.
    num_rounds : int
        Number of syndrome-extraction rounds (R).
    num_shots : int
        Total number of circuit evaluations.

    Returns
    -------
    float
        Estimated logical error rate per logical qubit per cycle, PL.

    Notes
    -----
    The conversion uses the relation::

        P_run = num_logical_errors / num_shots
        PL   = (1 - (1 - 2·P_run)^(1/R)) / 2

    derived from the approximation that logical errors are rare and that
    P_run ≈ 2R·PL for PL·R ≪ 1 (single-error approximation).
    The inverse transformation gives PL ≈ P_run / (2R) in the low-error limit,
    but we use the exact formula above to remain accurate at higher error rates.
    """
    if num_shots == 0:
        return 0.0

    p_run = num_logical_errors / num_shots

    if p_run >= 0.5:
        # The formula breaks down above 0.5; clamp to a sensible maximum.
        return 0.25 / num_rounds  # ~maximum PL for completely random decoding

    # Exact inversion (handles the case P_run = 0 safely)
    if p_run == 0.0:
        return 0.0

    pl = (1.0 - (1.0 - 2.0 * p_run) ** (1.0 / num_rounds)) / 2.0
    return max(0.0, pl)


def estimate_pl_std(
    num_logical_errors: int,
    num_shots: int,
    pl_estimate: float,
    num_rounds: int,
) -> float:
    """
    Estimate the standard deviation of the PL estimate.

    Uses binomial standard error: σ(P_run) = sqrt(P_run·(1-P_run) / N).
    Propagated to PL via dPL/dP_run, valid for small errors.

    When no errors are observed (num_logical_errors == 0), returns the
    90 % confidence upper bound on P_run converted to PL units:
    P_run_upper ≈ 2.3 / N  (90 % Poisson upper bound for 0 observed).
    """
    if num_shots == 0:
        return float("inf")

    if num_logical_errors == 0:
        # 90 % Poisson upper bound for 0 events: ln(1/0.1) / N ≈ 2.303 / N
        p_run_upper = 2.303 / num_shots
        pl_upper = (1.0 - (1.0 - 2.0 * p_run_upper) ** (1.0 / num_rounds)) / 2.0
        return pl_upper  # treat this as a 1-sigma equivalent for the bound

    p_run = num_logical_errors / num_shots
    sigma_p_run = np.sqrt(p_run * (1.0 - p_run) / num_shots)

    # dPL/dP_run from the PL formula
    if p_run < 0.5 and num_rounds > 0:
        factor = (1.0 - 2.0 * p_run) ** (1.0 / num_rounds - 1.0)
        sigma_pl = sigma_p_run * factor / num_rounds
    else:
        sigma_pl = float("inf")

    return sigma_pl


class SimulationResult:
    """Container for a single simulation outcome."""

    __slots__ = (
        "platform_name",
        "d",
        "rounds",
        "p_scale",
        "pl",
        "pl_std",
        "p_run",
        "num_shots",
        "num_logical_errors",
        "time_seconds",
        "hit_max_shots",
    )

    def __init__(
        self,
        *,
        platform_name: str,
        d: int,
        rounds: int,
        p_scale: float,
        pl: float,
        pl_std: float,
        p_run: float,
        num_shots: int,
        num_logical_errors: int,
        time_seconds: float,
        hit_max_shots: bool = False,
    ):
        self.platform_name = platform_name
        self.d = d
        self.rounds = rounds
        self.p_scale = p_scale
        self.pl = pl
        self.pl_std = pl_std
        self.p_run = p_run
        self.num_shots = num_shots
        self.num_logical_errors = num_logical_errors
        self.time_seconds = time_seconds
        self.hit_max_shots = hit_max_shots

    def __repr__(self) -> str:
        return (
            f"SimulationResult(platform={self.platform_name!r}, d={self.d}, "
            f"p_scale={self.p_scale}, PL={self.pl:.3e}±{self.pl_std:.3e}, "
            f"shots={self.num_shots}, errors={self.num_logical_errors}, "
            f"hit_max={self.hit_max_shots}, time={self.time_seconds:.1f}s)"
        )

    def to_dict(self) -> dict:
        return {
            "platform": self.platform_name,
            "d": self.d,
            "rounds": self.rounds,
            "p_scale": self.p_scale,
            "PL": self.pl,
            "PL_std": self.pl_std,
            "P_run": self.p_run,
            "shots": self.num_shots,
            "logical_errors": self.num_logical_errors,
            "hit_max_shots": self.hit_max_shots,
            "time_seconds": self.time_seconds,
        }


def run_single_experiment(
    circuit: stim.Circuit,
    num_shots: int,
    num_rounds: int,
    d: int,
    platform_name: str = "unknown",
    p_scale: float = 1.0,
    progress_callback: Callable[[int, int], None] | None = None,
) -> SimulationResult:
    """
    Run one complete simulation experiment and return the PL estimate.

    Parameters
    ----------
    circuit : stim.Circuit
        The surface code circuit (with detectors and observables).
    num_shots : int
        Number of circuit evaluations (shots).
    num_rounds : int
        Number of syndrome-extraction rounds R.
    d : int
        Code distance (used in the returned result).
    platform_name : str
        Label for the platform (for reporting).
    p_scale : float
        Noise scale factor (for reporting).
    progress_callback : callable | None
        Optional callback(num_shots_done, total) for progress reporting.

    Returns
    -------
    SimulationResult
        Contains PL, statistical error, and timing information.
    """
    t0 = time.perf_counter()

    # ── Build the pymatching decoder from the circuit's detector error model ──
    dem = circuit.detector_error_model(decompose_errors=True)
    matcher = pymatching.Matching.from_detector_error_model(dem)

    # ── Compile a fast sampler ────────────────────────────────────────────────
    sampler = circuit.compile_detector_sampler()

    # ── Main sampling loop ───────────────────────────────────────────────────
    logical_errors = 0
    shots_done = 0

    # Process in batches for memory efficiency and progress reporting
    batch_size = 10_000

    while shots_done < num_shots:
        current_batch = min(batch_size, num_shots - shots_done)

        # Sample detectors (syndrome) and observables (logical readout)
        # When append_observables=True, stim returns a single array of shape
        # (shots, num_detectors + num_observables). We split it.
        combined = sampler.sample(current_batch, append_observables=True)
        n_det = circuit.num_detectors
        syndrome = combined[:, :n_det]
        observable = combined[:, n_det:]

        # Decode each shot using MWPM
        for syndrome_bits, obs_bits in zip(syndrome, observable):
            # stim returns bool arrays; convert to list of ints for pymatching
            syndrome_list = list(syndrome_bits.astype(np.uint8))
            predicted_logical = matcher.decode(syndrome_list)

            # Ground truth: we prepared logical |0⟩ → observable should be 0
            # obs_bits[0] is the actual measured logical observable
            actual_logical = int(obs_bits[0])

            if predicted_logical != actual_logical:
                logical_errors += 1

        shots_done += current_batch

        if progress_callback is not None:
            progress_callback(shots_done, num_shots)

    # ── Compute PL per cycle ─────────────────────────────────────────────────
    pl = compute_pl_per_cycle(logical_errors, num_rounds, shots_done)
    pl_std = estimate_pl_std(logical_errors, shots_done, pl, num_rounds)
    p_run = logical_errors / shots_done if shots_done > 0 else 0.0

    elapsed = time.perf_counter() - t0

    return SimulationResult(
        platform_name=platform_name,
        d=d,
        rounds=num_rounds,
        p_scale=p_scale,
        pl=pl,
        pl_std=pl_std,
        p_run=p_run,
        num_shots=shots_done,
        num_logical_errors=logical_errors,
        time_seconds=elapsed,
        hit_max_shots=False,
    )


def run_adaptive_experiment(
    circuit: stim.Circuit,
    num_rounds: int,
    d: int,
    platform_name: str = "unknown",
    p_scale: float = 1.0,
    min_logical_errors: int = MIN_LOGICAL_ERRORS,
    max_shots: int = MAX_SHOTS,
    progress_callback: Callable[[int, int, int], None] | None = None,
) -> SimulationResult:
    """
    Run a simulation with adaptive shot count until a target number of
    logical errors is observed.

    Stops when either ``min_logical_errors`` logical errors have been observed
    or ``max_shots`` is reached.

    Parameters
    ----------
    circuit : stim.Circuit
    num_rounds : int
    d : int
        Code distance (passed to the result).
    platform_name : str
    p_scale : float
    min_logical_errors : int
        Target number of logical errors (default: 100 → ~10% relative error).
    max_shots : int
        Hard upper limit on shots (default: 10⁷).
    progress_callback : callable | None
        Called as callback(errors_sofar, shots_sofar, target_errors).

    Returns
    -------
    SimulationResult
    """
    t0 = time.perf_counter()

    dem = circuit.detector_error_model(decompose_errors=True)
    matcher = pymatching.Matching.from_detector_error_model(dem)
    sampler = circuit.compile_detector_sampler()

    logical_errors = 0
    shots_done = 0
    batch_size = 10_000

    while shots_done < max_shots:
        current_batch = min(batch_size, max_shots - shots_done)

        combined = sampler.sample(current_batch, append_observables=True)
        n_det = circuit.num_detectors
        syndrome = combined[:, :n_det]
        observable = combined[:, n_det:]

        for syndrome_bits, obs_bits in zip(syndrome, observable):
            syndrome_list = list(syndrome_bits.astype(np.uint8))
            predicted_logical = matcher.decode(syndrome_list)
            actual_logical = int(obs_bits[0])

            if predicted_logical != actual_logical:
                logical_errors += 1

        shots_done += current_batch

        if progress_callback is not None:
            progress_callback(logical_errors, shots_done, min_logical_errors)

        if logical_errors >= min_logical_errors:
            break

    hit_max = shots_done >= max_shots

    pl = compute_pl_per_cycle(logical_errors, num_rounds, shots_done)
    pl_std = estimate_pl_std(logical_errors, shots_done, pl, num_rounds)
    p_run = logical_errors / shots_done if shots_done > 0 else 0.0
    elapsed = time.perf_counter() - t0

    return SimulationResult(
        platform_name=platform_name,
        d=d,
        rounds=num_rounds,
        p_scale=p_scale,
        pl=pl,
        pl_std=pl_std,
        p_run=p_run,
        num_shots=shots_done,
        num_logical_errors=logical_errors,
        time_seconds=elapsed,
        hit_max_shots=hit_max,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Sanity-check helpers
# ──────────────────────────────────────────────────────────────────────────────

def verify_zero_noise_pl(d: int = 3, rounds: int | None = None) -> float:
    """
    Verify that a perfect circuit gives PL = 0.

    Runs ``num_shots`` shots of a noise-free d=3 surface code and returns
    the observed logical error count (should be 0).
    """
    circuit = build_perfect_circuit(d=d, rounds=rounds)
    if rounds is None:
        rounds = d

    result = run_single_experiment(
        circuit=circuit,
        num_shots=1_000,
        num_rounds=rounds,
        d=d,
        platform_name="perfect",
        p_scale=0.0,
    )
    return result.pl


# ──────────────────────────────────────────────────────────────────────────────
# Quick sanity check
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from surface_code_study.circuit_builder import build_surface_code_circuit
    from surface_code_study.platforms import SUPERCONDUCTING, get_platform

    platform = get_platform(SUPERCONDUCTING)
    params = platform._asdict()

    print("=== Simulator self-test ===")
    print("Test 1: Zero noise → PL should be 0")
    pl_zero = verify_zero_noise_pl(d=3)
    print(f"  PL(zero noise) = {pl_zero:.3e}  ({'PASS' if pl_zero == 0 else 'FAIL'})\n")

    print("Test 2: d=3, p=0.1% (noise_scale=1.0, 1000 shots)")
    circ = build_surface_code_circuit(d=3, platform_params=params, noise_scale=1.0)
    result = run_single_experiment(
        circuit=circ,
        num_shots=1_000,
        num_rounds=3,
        d=3,
        platform_name=SUPERCONDUCTING,
        p_scale=1.0,
    )
    print(f"  {result}")
    print(f"  PL = {result.pl:.6f} ± {result.pl_std:.6f}")
    print(f"  P_run = {result.p_run:.6f}")
    print(f"  Time = {result.time_seconds:.2f}s for {result.num_shots} shots")
    print(f"  Throughput = {result.num_shots / result.time_seconds:.0f} shots/s\n")

    print("Test 3: Adaptive sampling (target 100 errors)")
    circ2 = build_surface_code_circuit(d=3, platform_params=params, noise_scale=1.0)
    result2 = run_adaptive_experiment(
        circuit=circ2,
        num_rounds=3,
        d=3,
        platform_name=SUPERCONDUCTING,
        p_scale=1.0,
        min_logical_errors=100,
    )
    print(f"  {result2}")
    print(f"  PL = {result2.pl:.6f} ± {result2.pl_std:.6f}")
    print(f"  Time = {result2.time_seconds:.2f}s")
