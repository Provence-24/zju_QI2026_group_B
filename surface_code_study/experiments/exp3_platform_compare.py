"""
Experiment 3: Platform comparison — comprehensive summary.

Combines exp1 (PL vs p) and exp2 (PL vs d) into a single figure with
two sub-panels, plus computes the minimum d required to reach PL=10^-6
at each platform's natural operating point (noise_scale=1.0).

Outputs
-------
results/exp3_platform_compare.json
results/exp3_platform_compare.png
results/exp3_platform_compare.pdf
"""

import argparse
import json
import sys
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from surface_code_study.circuit_builder import build_surface_code_circuit
from surface_code_study.platforms import PLATFORMS
from surface_code_study.simulator import (
    DEFAULT_DECODER,
    get_decoder,
    run_adaptive_experiment,
)


def build_circuit(platform_name, platform_params, d, rounds, noise_scale, p, use_compiler):
    """Build circuit — either via stim built-in or PlatformCompiler."""
    if use_compiler:
        from surface_code_study.compilers import get_compiler

        # Scale parameters
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

D_VALUES: list[int] = [3, 5, 7, 9]
P_NATURAL: float = 1.0     # noise_scale = 1.0 → platform natural operating point
PL_TARGET: float = 1e-6     # target logical error rate
P_FOR_D_TABLE: float = 0.001  # p=0.1% 2Q gate error — used for d_needed table
MIN_ERRORS: int = 100

RESULTS_DIR = Path(__file__).parent.parent.parent / "results"

# ── Scan helpers ──────────────────────────────────────────────────────────────

def scan_pl_vs_d(
    platform_name: str,
    platform_params: dict,
    d_values: list[int],
    p_scale: float,
    use_compiler: bool = False,
) -> list[dict]:
    results = []
    for d in d_values:
        rounds = d
        print(f"  d={d} ... ", end="", flush=True)
        t0 = time.perf_counter()
        circuit = build_circuit(
            platform_name, platform_params, d=d, rounds=rounds,
            noise_scale=p_scale, p=None, use_compiler=use_compiler,
        )
        decoder = get_decoder(DEFAULT_DECODER, circuit)
        res = run_adaptive_experiment(
            circuit=circuit, num_rounds=rounds, d=d,
            decoder=decoder,
            platform_name=platform_name, p_scale=p_scale,
            min_logical_errors=MIN_ERRORS,
        )
        elapsed = time.perf_counter() - t0
        flag = " [upper bound]" if res.hit_max_shots else ""
        print(
            f"PL={res.pl:.3e} ± {res.pl_std:.3e}{flag}  "
            f"({res.num_shots:,} shots, {res.num_logical_errors} errors, {elapsed:.1f}s)"
        )
        results.append(res.to_dict())
    return results


def estimate_d_for_pl_target(
    platform_name: str,
    platform_params: dict,
    p: float,
    pl_target: float,
    d_range: range = range(3, 21, 2),
    use_compiler: bool = False,
) -> tuple[int | None, float]:
    """
    Estimate the minimum d needed to reach PL ≤ pl_target at given p.

    Parameters
    ----------
    p : float
        Physical 2Q gate error rate (p = p_gate_2q).
    pl_target : float

    Returns (d_min, PL_at_d) where d_min is the smallest d achieving PL ≤ pl_target.
    If even d=29 doesn't achieve it, returns (None, PL_at_d=29).
    """
    print(f"  Finding d for PL ≤ {pl_target:.1e} at {platform_name} (p={p:.3g}) ...")

    # First, do a coarse scan
    coarse_ds = list(range(3, 21, 2))  # d = 3, 5, 7, 9, 11, 13, 15, 17, 19
    coarse_results = {}
    for d in coarse_ds:
        circuit = build_circuit(
            platform_name, platform_params, d=d, rounds=d,
            noise_scale=1.0, p=p, use_compiler=use_compiler,
        )
        decoder = get_decoder(DEFAULT_DECODER, circuit)
        res = run_adaptive_experiment(
            circuit=circuit, num_rounds=d, d=d,
            decoder=decoder,
            platform_name=platform_name, p_scale=p,
            min_logical_errors=50, max_shots=1_000_000,
        )
        coarse_results[d] = res.pl
        print(f"    d={d:2d}: PL={res.pl:.3e}")

    # Find the d where PL first drops below target
    for d in coarse_ds:
        if coarse_results[d] <= pl_target:
            return d, coarse_results[d]

    return None, coarse_results[coarse_ds[-1]]


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


def plot_combined(
    pl_vs_d: dict[str, list[dict]],
    d_needed: dict[str, tuple],
    out_png: Path,
    out_pdf: Path,
):
    """Two-panel figure: PL vs d (left), PL vs p (right)."""
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))

    # ── Left: PL vs d ──────────────────────────────────────────────────────
    ax = axes[0]
    p_natural = 1.0  # fixed from constant

    for platform_name, results in pl_vs_d.items():
        ds   = np.array([r["d"]        for r in results], dtype=float)
        pl   = np.array([r["PL"]       for r in results], dtype=float)
        pls  = np.array([r["PL_std"]   for r in results], dtype=float)
        ul   = np.array([r["hit_max_shots"] for r in results], dtype=bool)

        color = COLORS.get(platform_name, "gray")
        label = LABELS.get(platform_name, platform_name)

        nm = ~ul
        if np.any(nm):
            ax.errorbar(ds[nm], pl[nm], yerr=pls[nm],
                        marker="o", markersize=6, linewidth=1.8,
                        capsize=3, color=color, label=label)
        if np.any(ul):
            ax.errorbar(ds[ul], pl[ul], yerr=pls[ul],
                        marker=None, linewidth=0, uplims=True, color=color, alpha=0.4)
            ax.scatter(ds[ul], pl[ul], marker="v", s=20, color=color, alpha=0.4)

    # Reference: Λ=1 suppression line
    d_ref = np.array([3, 5, 7, 9, 11], dtype=float)
    p_base = 1e-3  # approximate p at natural operating point for reference
    pl_ref = p_base ** ((d_ref + 1) / 2.0)
    ax.plot(d_ref, pl_ref, "k--", linewidth=1, alpha=0.5, label="Λ=1 reference (p=0.1%)")

    ax.set_yscale("log")
    ax.set_xlabel("Code distance  $d$", fontsize=12)
    ax.set_ylabel("Logical error rate per cycle  $P_L$", fontsize=12)
    ax.set_title(f"PL vs d  (p = natural operating point)", fontsize=12)
    ax.legend(fontsize=9)
    ax.grid(which="both", alpha=0.3, linewidth=0.4)
    ax.tick_params(labelsize=10)

    # ── Right: Summary table as text ──────────────────────────────────────
    ax = axes[1]
    ax.axis("off")

    table_data = []
    for platform_name in PLATFORMS:
        d_needed_val, pl_at_d = d_needed[platform_name]
        label = LABELS.get(platform_name, platform_name)
        if d_needed_val is not None:
            d_str = f"d={d_needed_val}"
            pl_str = f"PL≈{pl_at_d:.1e}"
        else:
            d_str = f">29 (not achieved)"
            pl_str = f"PL({pl_at_d:.1e})"
        table_data.append([label, d_str, pl_str])

    table = ax.table(
        cellText=table_data,
        colLabels=["Platform", "Min d for PL=10^-6", "Actual PL at that d"],
        cellLoc="center",
        loc="upper center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1.2, 2.0)

    # Style header
    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_facecolor("#ddeeff")
            cell.set_text_props(weight="bold")

    ax.set_title(
        f"Summary: d needed for $P_L$ ≤ {PL_TARGET:.0e}\n"
        f"(at platform natural operating point, noise_scale=1.0)",
        fontsize=12, pad=20,
    )

    fig.tight_layout()
    fig.savefig(out_png, dpi=150)
    fig.savefig(out_pdf)
    print(f"Saved {out_png}  and  {out_pdf}")
    plt.close(fig)


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Experiment 3: Platform comparison")
    parser.add_argument("--use_compiler", action="store_true",
                        help="Use PlatformCompiler instead of stim built-in circuit")
    parser.add_argument("--d", type=int, nargs="+", default=[3, 5, 7, 9],
                        help="Code distances to scan")
    parser.add_argument("--rounds", type=int, default=None,
                        help="Number of rounds (default: d)")
    args = parser.parse_args()

    d_values = args.d
    print(f"=== Experiment 3: Platform comparison (compiler={args.use_compiler}) ===\n")

    results_dir = RESULTS_DIR / ("compiler" if args.use_compiler else "builtin")
    results_dir.mkdir(parents=True, exist_ok=True)

    d_needed = {}
    pl_vs_d = {}

    for platform_name, params in PLATFORMS.items():
        pdict = params._asdict()
        print(f"\n[{platform_name}]")
        print("--- PL vs d scan ---")
        results = scan_pl_vs_d(
            platform_name, pdict, d_values, P_NATURAL,
            use_compiler=args.use_compiler,
        )
        pl_vs_d[platform_name] = results

        print("--- d for PL=10^-6 (at p=0.1% 2Q gate error) ---")
        d_min, pl_at_d = estimate_d_for_pl_target(
            platform_name, pdict, P_FOR_D_TABLE, PL_TARGET,
            use_compiler=args.use_compiler,
        )
        d_needed[platform_name] = (d_min, pl_at_d)

    # ── Save JSON ────────────────────────────────────────────────────────────
    json_path = results_dir / "exp3_platform_compare.json"
    serialised = {
        "pl_vs_d": pl_vs_d,
        "d_needed_for_pl_target": {
            name: {"d_min": d_[0], "pl_at_d": d_[1]}
            for name, d_ in d_needed.items()
        },
    }
    with open(json_path, "w") as f:
        json.dump(serialised, f, indent=2)
    print(f"\nSaved {json_path}")

    # ── Plot ─────────────────────────────────────────────────────────────────
    plot_combined(
        pl_vs_d, d_needed,
        out_png=results_dir / "exp3_platform_compare.png",
        out_pdf=results_dir / "exp3_platform_compare.pdf",
    )

    print("\n=== Experiment 3 complete ===")


if __name__ == "__main__":
    main()
