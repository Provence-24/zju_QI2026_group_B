"""
Experiment 2: Logical error rate vs code distance.

Fixed p=0.1% (physical 2Q gate error rate; p = p_gate_2q for all platforms),
scans d ∈ {3, 5, 7, 9} to verify exponential suppression:

    P_L ≈ Λ · p^((d+1)/2)

Taking log₁₀:
    log10(P_L) = log10(Λ) + ((d+1)/2) · log10(p)

The slope is fixed by the formula; we fit the intercept log10(Λ).
The suppression factor Λ captures platform-specific advantages.

Outputs
-------
results/exp2_pl_vs_d.json
results/exp2_pl_vs_d.png
results/exp2_pl_vs_d.pdf
"""

import argparse
import json
import sys
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from surface_code_study.circuit_builder import build_surface_code_circuit
from surface_code_study.platforms import PLATFORMS
from surface_code_study.simulator import (
    DEFAULT_DECODER,
    SimulationResult,
    get_decoder,
    run_adaptive_experiment,
)


def build_circuit(platform_name, platform_params, d, rounds, noise_scale, p, use_compiler):
    """Build circuit — either via stim built-in or PlatformCompiler."""
    if use_compiler:
        from surface_code_study.compilers import get_compiler

        params = dict(platform_params)
        if p is not None:
            p_val = float(p)
            scales = params.get('relative_scales', {})
            params['p_gate_2q'] = p_val
            params['p_gate_1q'] = p_val * scales.get('gate_1q', 0.3)
            params['p_meas'] = p_val * scales.get('meas', 5.0)
            params['p_reset'] = p_val * scales.get('reset', 0.1)
        else:
            scale = float(noise_scale)
            params['p_gate_2q'] = scale * float(params['p_gate_2q'])
            params['p_gate_1q'] = scale * float(params['p_gate_1q'])
            params['p_meas'] = scale * float(params['p_meas'])
            params['p_reset'] = scale * float(params['p_reset'])

        compiler = get_compiler(platform_name, distance=d, noise_params=params)
        return compiler.build_memory_circuit(num_rounds=rounds)
    else:
        return build_surface_code_circuit(
            d=d,
            platform_params=platform_params,
            rounds=rounds,
            noise_scale=noise_scale,
            p=p,
        )

# ── Constants ──────────────────────────────────────────────────────────────────

P_FIXED: float = 0.001       # 0.1% physical 2Q gate error rate (p = p_gate_2q)
D_VALUES: list[int] = [3, 5, 7, 9]
MIN_ERRORS: int = 100

RESULTS_DIR = Path(__file__).parent.parent.parent / "results"

# ── Core scan ─────────────────────────────────────────────────────────────────

def scan_platform(
    platform_name: str,
    platform_params: dict,
    d_values: list[int],
    p_fixed: float,
    use_compiler: bool = False,
) -> list[SimulationResult]:
    """Scan d for one platform at fixed p."""
    results = []
    for d in d_values:
        rounds = d  # standard: rounds = distance
        print(f"  {platform_name:16s}  d={d} ... ", end="", flush=True)
        t0 = time.perf_counter()

        circuit = build_circuit(
            platform_name, platform_params, d=d, rounds=rounds,
            noise_scale=1.0, p=p_fixed, use_compiler=use_compiler,
        )

        decoder = get_decoder(DEFAULT_DECODER, circuit)
        result = run_adaptive_experiment(
            circuit=circuit,
            num_rounds=rounds,
            d=d,
            decoder=decoder,
            platform_name=platform_name,
            p_scale=p_fixed,
            min_logical_errors=MIN_ERRORS,
        )
        results.append(result)

        elapsed = time.perf_counter() - t0
        flag = " [upper bound]" if result.hit_max_shots else ""
        print(
            f"PL={result.pl:.3e} ± {result.pl_std:.3e}{flag}  "
            f"({result.num_shots:,} shots, {result.num_logical_errors} errors, {elapsed:.1f}s)"
        )
    return results


# ── Fitting ───────────────────────────────────────────────────────────────────

def fit_suppression_factor(
    results: list[SimulationResult],
    p_fixed: float,
) -> tuple[float, float]:
    """
    Fit the suppression factor Λ from PL ≈ Λ · p_fixed^((d+1)/2).

    Returns
    -------
    lambda_val : float
        Suppression factor Λ (dimensionless).
    lambda_std : float
        Standard error on Λ from the fit.
    """
    log_p = np.log10(p_fixed)

    # x = (d+1)/2, y = log10(PL)
    x = np.array([(r.d + 1) / 2.0 for r in results], dtype=float)
    y = np.log10(np.array([r.pl for r in results], dtype=float))

    # Weighted least squares: weight ∝ 1/pl_std
    weights = 1.0 / np.array([r.pl_std for r in results], dtype=float)

    # Simple linear regression: y = intercept + slope * x
    # slope is fixed = log10(p_fixed); intercept = log10(Λ)
    # We only fit the intercept given the known slope.
    slope_fixed = log_p

    # Weighted mean of (y - slope*x) across all d
    residuals = y - slope_fixed * x
    weighted_mean = np.sum(weights * residuals) / np.sum(weights)
    weighted_var = 1.0 / np.sum(weights)

    log_lambda = weighted_mean
    log_lambda_std = np.sqrt(weighted_var)

    lambda_val = 10**log_lambda
    lambda_std = lambda_val * log_lambda_std * np.log(10)

    return lambda_val, lambda_std


# ── Plotting ─────────────────────────────────────────────────────────────────

COLORS = {
    "superconducting": "#e63946",
    "neutral_atom":    "#2a9d8f",
    "ion_trap":        "#457b9d",
}

LABELS = {
    "superconducting": "Superconducting",
    "neutral_atom":    "Neutral Atoms",
    "ion_trap":        "Ion Traps",
}


def plot_results(
    all_results: dict[str, list[SimulationResult]],
    out_png: Path,
    out_pdf: Path,
):
    """Semilogy plot: d vs PL, with theoretical reference lines."""
    fig, ax = plt.subplots(figsize=(7, 5))

    # Theoretical reference: PL = p_fixed^((d+1)/2)  (Λ=1)
    d_ref = np.array([3, 5, 7, 9], dtype=float)
    x_ref = (d_ref + 1) / 2.0

    # Find global p_fixed from first result
    p_fixed = all_results["superconducting"][0].p_scale

    for platform_name, results in all_results.items():
        d_vals = np.array([r.d for r in results], dtype=float)
        pl_vals = np.array([r.pl for r in results])
        pl_std  = np.array([r.pl_std for r in results])
        hit_max = np.array([r.hit_max_shots for r in results])

        color = COLORS.get(platform_name, "gray")
        label = LABELS.get(platform_name, platform_name)

        normal_mask = ~hit_max
        ul_mask     = hit_max

        if np.any(normal_mask):
            ax.errorbar(
                d_vals[normal_mask], pl_vals[normal_mask],
                yerr=pl_std[normal_mask],
                marker="o", markersize=6, linewidth=1.8,
                capsize=3, color=color, label=f"{label}",
            )

        if np.any(ul_mask):
            ax.errorbar(
                d_vals[ul_mask], pl_vals[ul_mask],
                yerr=pl_std[ul_mask],
                marker=None, linewidth=0,
                uplims=True, color=color, alpha=0.4,
            )
            ax.scatter(
                d_vals[ul_mask], pl_vals[ul_mask],
                marker="v", s=20, color=color, alpha=0.4,
            )

    ax.set_yscale("log")
    ax.set_xlabel("Code distance  $d$", fontsize=12)
    ax.set_ylabel("Logical error rate per cycle  $P_L$", fontsize=12)
    ax.set_title(
        f"Error suppression: d vs PL  (p = {p_fixed:.1%}, R = d)",
        fontsize=13,
    )
    ax.legend(fontsize=11)
    ax.grid(which="both", alpha=0.3, linewidth=0.4)
    ax.tick_params(labelsize=10)

    fig.tight_layout()
    fig.savefig(out_png, dpi=150)
    fig.savefig(out_pdf)
    print(f"Saved {out_png}  and  {out_pdf}")
    plt.close(fig)


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Experiment 2: PL vs d")
    parser.add_argument("--use_compiler", action="store_true",
                        help="Use PlatformCompiler instead of stim built-in circuit")
    args = parser.parse_args()

    print(f"=== Experiment 2: PL vs d  (p_fixed={P_FIXED:.1%}, compiler={args.use_compiler}) ===\n")

    results_dir = RESULTS_DIR / ("compiler" if args.use_compiler else "builtin")
    results_dir.mkdir(parents=True, exist_ok=True)

    all_results: dict[str, list[SimulationResult]] = {}

    for platform_name, params in PLATFORMS.items():
        print(f"\nPlatform: {platform_name}")
        pdict = params._asdict()
        results = scan_platform(platform_name, pdict, D_VALUES, P_FIXED,
                                use_compiler=args.use_compiler)
        all_results[platform_name] = results

    # ── Fit Λ for each platform ──────────────────────────────────────────────
    print("\n=== Fitting suppression factor Λ ===")
    lambda_table = {}
    for platform_name, results in all_results.items():
        lam_val, lam_std = fit_suppression_factor(results, P_FIXED)
        lambda_table[platform_name] = {"lambda": lam_val, "lambda_std": lam_std}
        print(
            f"  {platform_name:16s}  Λ = {lam_val:.3f} ± {lam_std:.3f}"
        )

    # ── Save JSON ────────────────────────────────────────────────────────────
    json_path = results_dir / "exp2_pl_vs_d.json"
    serialised = {
        platform_name: {
            "results": [r.to_dict() for r in results],
            "lambda": lambda_table[platform_name],
        }
        for platform_name, results in all_results.items()
    }
    with open(json_path, "w") as f:
        json.dump(serialised, f, indent=2)
    print(f"\nSaved {json_path}")

    # ── Plot ─────────────────────────────────────────────────────────────────
    plot_results(
        all_results,
        out_png=results_dir / "exp2_pl_vs_d.png",
        out_pdf=results_dir / "exp2_pl_vs_d.pdf",
    )

    print("\n=== Experiment 2 complete ===")


if __name__ == "__main__":
    main()
