"""
Experiment 1: Logical error rate vs physical error rate.

Fixed d=5, scans p ∈ [10⁻⁵, 10⁻²] (logarithmic, 10 points per platform).
Adaptive sampling: collect ≥ 100 logical errors per data point.

Outputs
-------
results/exp1_pl_vs_p.json   — raw results
results/exp1_pl_vs_p.png   — log-log plot
results/exp1_pl_vs_p.pdf   — vector version
"""

import json
import sys
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

# ── project root so this can be run as: python -m surface_code_study.experiments.exp1_pl_vs_p ──
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from surface_code_study.circuit_builder import build_surface_code_circuit
from surface_code_study.platforms import PLATFORMS
from surface_code_study.simulator import (
    SimulationResult,
    run_adaptive_experiment,
)

# ── Constants ──────────────────────────────────────────────────────────────────

D: int = 5
ROUNDS: int = D  # standard: rounds = distance
MIN_ERRORS: int = 100

# Log-spaced noise-scale scan.
# noise_scale=1.0 = platform natural operating point.
# Empirical check: at d=5, ns=0.3 gives PL≈2×10⁻⁵ (needs ~800k shots for 100 errors).
# ns=0.01 gives PL≈0 in 50k shots → skip as upper-bound only.
# Range: ns ∈ [0.3 … 3.0] to capture sub-threshold to near-threshold behaviour.
P_SCALES: list[float] = [
    0.3, 0.4, 0.55, 0.7, 0.9, 1.1, 1.4, 1.8, 2.3, 3.0
]
PLATFORM_NAMES: list[str] = list(PLATFORMS.keys())

RESULTS_DIR = Path(__file__).parent.parent.parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)


# ── Core scan ─────────────────────────────────────────────────────────────────

def scan_platform(
    platform_name: str,
    platform_params: dict,
    p_scales: list[float],
) -> list[SimulationResult]:
    """Run the PL vs p scan for one platform."""
    results = []
    for p in p_scales:
        print(f"  {platform_name:16s}  p_scale={p:.3e} ... ", end="", flush=True)
        t0 = time.perf_counter()

        circuit = build_surface_code_circuit(
            d=D,
            platform_params=platform_params,
            rounds=ROUNDS,
            noise_scale=p,
        )

        result = run_adaptive_experiment(
            circuit=circuit,
            num_rounds=ROUNDS,
            d=D,
            platform_name=platform_name,
            p_scale=p,
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


# ── Plotting ─────────────────────────────────────────────────────────────────

COLORS = {
    "superconducting": "#e63946",
    "neutral_atom":    "#2a9d8f",
    "ion_trap":        "#457b9d",
}

LABELS = {
    "superconducting": "Superconducting (Google Willow)",
    "neutral_atom":    "Neutral Atoms (Harvard/QuEra)",
    "ion_trap":        "Ion Traps (Quantinuum H2)",
}


def plot_results(all_results: dict[str, list[SimulationResult]], out_png: Path, out_pdf: Path):
    """Draw a log-log plot: p_scale vs PL for each platform."""
    fig, ax = plt.subplots(figsize=(8, 5.5))

    for platform_name, results in all_results.items():
        p_scales = np.array([r.p_scale for r in results])
        pl       = np.array([r.pl       for r in results])
        pl_std   = np.array([r.pl_std   for r in results])
        hit_max  = np.array([r.hit_max_shots for r in results])

        color = COLORS.get(platform_name, "gray")
        label = LABELS.get(platform_name, platform_name)

        # Separate results that hit max_shots (upper limits) from normal points
        normal_mask = ~hit_max
        ul_mask     =  hit_max

        if np.any(normal_mask):
            ax.errorbar(
                p_scales[normal_mask], pl[normal_mask],
                yerr=pl_std[normal_mask],
                marker="o", markersize=5, linewidth=1.5,
                capsize=3, color=color, label=label,
            )

        if np.any(ul_mask):
            # Upper limits: show as downward arrows with PL_std as the bound
            ax.errorbar(
                p_scales[ul_mask], pl[ul_mask],
                yerr=pl_std[ul_mask],
                marker=None, linewidth=0,
                uplims=True, lolims=False,
                color=color, alpha=0.4,
            )
            # Mark with a small dot at the upper-bound value
            ax.scatter(
                p_scales[ul_mask], pl[ul_mask],
                marker="v", s=20, color=color, alpha=0.4,
            )

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Physical error rate scale  $p$", fontsize=12)
    ax.set_ylabel("Logical error rate per cycle  $P_L$", fontsize=12)
    ax.set_title(f"Surface code (d={D}, R={ROUNDS}) — MWPM decoding", fontsize=13)
    ax.legend(fontsize=10)
    ax.grid(which="both", alpha=0.3, linewidth=0.4)
    ax.tick_params(labelsize=10)

    fig.tight_layout()
    fig.savefig(out_png, dpi=150)
    fig.savefig(out_pdf)
    print(f"Saved {out_png}  and  {out_pdf}")
    plt.close(fig)


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print(f"=== Experiment 1: PL vs p  (d={D}, R={ROUNDS}) ===\n")

    all_results: dict[str, list[SimulationResult]] = {}

    for platform_name, params in PLATFORMS.items():
        print(f"\nPlatform: {platform_name}")
        pdict = params._asdict()
        results = scan_platform(platform_name, pdict, P_SCALES)
        all_results[platform_name] = results

    # ── Save JSON ────────────────────────────────────────────────────────────
    json_path = RESULTS_DIR / "exp1_pl_vs_p.json"
    serialised = {
        platform_name: [r.to_dict() for r in results]
        for platform_name, results in all_results.items()
    }
    with open(json_path, "w") as f:
        json.dump(serialised, f, indent=2)
    print(f"\nSaved {json_path}")

    # ── Plot ─────────────────────────────────────────────────────────────────
    plot_results(
        all_results,
        out_png=RESULTS_DIR / "exp1_pl_vs_p.png",
        out_pdf=RESULTS_DIR / "exp1_pl_vs_p.pdf",
    )

    print("\n=== Experiment 1 complete ===")


if __name__ == "__main__":
    main()
