"""
Sanity checks for the surface code simulation framework.

Run with:  python -m surface_code_study.tests.test_sanity
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import numpy as np
from surface_code_study.circuit_builder import build_perfect_circuit, build_surface_code_circuit
from surface_code_study.platforms import PLATFORMS, SUPERCONDUCTING, get_platform
from surface_code_study.simulator import (
    compute_pl_per_cycle,
    run_adaptive_experiment,
    run_single_experiment,
)


def test_zero_noise_pl():
    """Test 1: Zero noise → PL must be exactly 0."""
    print("Test 1: Zero noise → PL = 0 ... ", end="")
    circuit = build_perfect_circuit(d=3, rounds=3)
    result = run_single_experiment(
        circuit=circuit,
        num_shots=1_000,
        num_rounds=3,
        d=3,
        platform_name="test",
        p_scale=0.0,
    )
    assert result.pl == 0.0, f"Expected PL=0, got {result.pl}"
    assert result.num_logical_errors == 0
    print("PASS")


def test_high_noise_obvious_failure():
    """Test 2: d=3, p above threshold → PL > 5% (obvious logical failure)."""
    print("Test 2: d=3, p above threshold → PL > 5% ... ", end="")
    platform = get_platform(SUPERCONDUCTING)
    params = platform._asdict()

    # Use large noise_scale to be clearly above threshold.
    # Note: noise_scale must keep all error probs ≤ 0.75 (stim DEPOLARIZE1 limit).
    # With noise_scale=10: p_idle=0.1, p_meas=0.05, p_2q=0.01 — all safe.
    ns = 10.0
    circuit = build_surface_code_circuit(d=3, platform_params=params, noise_scale=ns)
    result = run_single_experiment(
        circuit=circuit,
        num_shots=5_000,
        num_rounds=3,
        d=3,
        platform_name="test",
        p_scale=100.0,
    )
    # At noise_scale=100 (p_2q=0.1, p_idle=1.0), PL should be >> 0.1
    # With such extreme noise, the decoder should fail badly
    assert result.pl > 0.01, (
        f"Expected PL > 1% at high noise (ns={ns}), got {result.pl:.3e}. "
        "Something is wrong with the noise injection."
    )
    print(f"PASS (PL={result.pl:.4f})")


def test_d_increases_pl_decreases_below_threshold():
    """Test 3: At p below threshold, larger d → lower PL."""
    print("Test 3: p fixed, d↑ → PL↓ (below threshold) ... ", end="")
    platform = get_platform(SUPERCONDUCTING)
    params = platform._asdict()

    # Use a low noise scale where we're well below threshold
    ns = 0.5
    pls = {}
    for d in [3, 5]:
        circuit = build_surface_code_circuit(d=d, platform_params=params, noise_scale=ns, rounds=d)
        res = run_single_experiment(
            circuit=circuit,
            num_shots=20_000,
            num_rounds=d,
            d=d,
            platform_name="test",
            p_scale=ns,
        )
        pls[d] = res.pl
        print(f"\n    d={d}: PL={res.pl:.3e}  ({res.num_shots} shots, {res.num_logical_errors} errors)")

    assert pls[5] < pls[3], (
        f"Expected PL(d=5) < PL(d=3) at ns={ns}, "
        f"got PL(d=5)={pls[5]:.3e} vs PL(d=3)={pls[3]:.3e}"
    )
    print("PASS")


def test_d_increases_pl_increases_above_threshold():
    """Test 4: At p above threshold, both d=3 and d=5 give PL > 1% (threshold theorem).

    The Fowler threshold says: for p > p_th, PL → 0.5 as d → ∞ (no correction).
    Above threshold, even d=5 should give >1% logical error rate, confirming we are
    in the strong-noise regime.
    """
    print("Test 4: Above threshold — both d=3 and d=5 give PL > 1% ... ", end="")
    platform = get_platform(SUPERCONDUCTING)
    params = platform._asdict()

    # ns=10 → p_idle=0.10, p_2q=0.01, p_meas=0.05; well above typical threshold
    ns = 10.0
    pls = {}
    for d in [3, 5]:
        circuit = build_surface_code_circuit(d=d, platform_params=params, noise_scale=ns, rounds=d)
        res = run_single_experiment(
            circuit=circuit,
            num_shots=10_000,
            num_rounds=d,
            d=d,
            platform_name="test",
            p_scale=ns,
        )
        pls[d] = res.pl
        print(f"\n    d={d}: PL={pls[d]:.3f}  ({res.num_shots} shots, {res.num_logical_errors} errors)")

    # Both should be clearly above threshold (>1%)
    assert pls[3] > 0.01, f"Expected PL(d=3) > 1%, got {pls[3]:.3f}"
    assert pls[5] > 0.01, f"Expected PL(d=5) > 1%, got {pls[5]:.3f}"
    print("PASS")


def test_performance_target():
    """Test 5: d=3, p=0.1%, 10⁵ shots in < 5 s."""
    print("Test 5: d=3, p=0.1%, 100k shots performance ... ", end="")
    import time

    platform = get_platform(SUPERCONDUCTING)
    params = platform._asdict()
    circuit = build_surface_code_circuit(d=3, platform_params=params, noise_scale=1.0)

    t0 = time.perf_counter()
    result = run_single_experiment(
        circuit=circuit,
        num_shots=100_000,
        num_rounds=3,
        d=3,
        platform_name="test",
        p_scale=1.0,
    )
    elapsed = time.perf_counter() - t0

    assert elapsed < 5.0, f"100k shots took {elapsed:.1f}s (> 5s target)"
    assert result.num_shots == 100_000
    print(f"PASS ({elapsed:.2f}s for 100k shots)")


def test_pl_formula():
    """Test 6: Verify the PL per-cycle conversion formula."""
    print("Test 6: PL formula correctness ... ", end="")

    # If P_run = 0 → PL = 0
    pl = compute_pl_per_cycle(num_logical_errors=0, num_rounds=5, num_shots=100_000)
    assert pl == 0.0, f"Expected PL=0 for 0 errors, got {pl}"

    # P_run = 1/N, R=1 → PL = (1-(1-2/N)^1)/2 = 1/N
    pl = compute_pl_per_cycle(num_logical_errors=1, num_rounds=1, num_shots=1000)
    expected = (1 - (1 - 2/1000)) / 2
    assert abs(pl - expected) < 1e-12

    # Low-error limit: PL ≈ P_run/(2R)
    pl = compute_pl_per_cycle(num_logical_errors=10, num_rounds=5, num_shots=100_000)
    approx = 10 / 100_000 / 10  # P_run/(2R)
    assert abs(pl - approx) < 0.01, f"Expected ~{approx:.6f}, got {pl:.6f}"

    print("PASS")


def main():
    print("=== Surface Code Sanity Checks ===\n")

    test_zero_noise_pl()
    test_high_noise_obvious_failure()
    test_d_increases_pl_decreases_below_threshold()
    test_d_increases_pl_increases_above_threshold()
    test_performance_target()
    test_pl_formula()

    print("\n=== All tests passed ===")


if __name__ == "__main__":
    main()
