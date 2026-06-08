"""
Experiment 4: qLDPC vs Surface Code — neutral atom platform comparison.

Compares logical error rates (PL per logical qubit per round) between
rotated surface codes (d=3, 5) and the BB [[72,12,6]] qLDPC code under
the same neutral atom shuttling noise model.

Both code families use the dual-zone atom shuttling compiler:
  - Surface code: NeutralAtomCompiler (4 batches/round, MWPM decoder)
  - qLDPC:        NeutralAtomQLDPCCompiler (8 batches/round, BP+OSD decoder)

The key metric is PL vs p (physical 2Q gate error rate), with k (logical
qubit count) annotated for each code.

Outputs
-------
results/exp4_qldpc_vs_surface.json
results/exp4_qldpc_vs_surface.png
results/exp4_qldpc_vs_surface.pdf
"""

import argparse
import json
import sys
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from surface_code_study.platforms import NEUTRAL_ATOM, get_platform
from surface_code_study.compilers import get_compiler, get_qldpc_compiler
from surface_code_study.simulator import (
    get_decoder,
    run_adaptive_experiment,
    run_single_experiment,
    compute_pl_per_cycle,
)
from surface_code_study.qldpc import build_bb_code_72_12_6, BBCode

# ── Configuration ────────────────────────────────────────────────────────────

P_VALUES = [0.0005, 0.001, 0.002, 0.004, 0.006, 0.008, 0.01]
SURFACE_D_VALUES = [3, 5]
QLDPC_ROUNDS = 3
SURFACE_SHOTS = 2000
QLDPC_SHOTS = 50

RESULTS_DIR = Path(__file__).parent.parent.parent / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


# ── Build platform noise params ──────────────────────────────────────────────

def build_noise_params(p_2q: float, base_platform) -> dict:
    """Scale neutral atom platform noise to target p_2q."""
    pdict = base_platform._asdict()
    scales = pdict.get("relative_scales", {})
    return {
        "p_gate_2q": p_2q,
        "p_gate_1q": p_2q * scales.get("gate_1q", 0.17),
        "p_meas": p_2q * scales.get("meas", 0.83),
        "p_reset": p_2q * scales.get("reset", 0.83),
        "p_idle": p_2q * scales.get("idle", 0.17),
        "T1_us": pdict["T1_us"],
        "T2_us": pdict["T2_us"],
        "cycle_time_us": pdict["cycle_time_us"],
        "relative_scales": scales,
    }


# ── Surface code simulation ──────────────────────────────────────────────────

def run_surface_code_point(platform_name: str, d: int, rounds: int,
                           noise_params: dict, n_shots: int,
                           decoder_name: str = "mwpm") -> dict:
    """Run one surface code data point with neutral atom compiler."""
    compiler = get_compiler(platform_name, distance=d, noise_params=noise_params)
    circuit = compiler.build_memory_circuit(num_rounds=rounds)
    decoder = get_decoder(decoder_name, circuit)
    result = run_single_experiment(
        circuit=circuit, num_shots=n_shots, num_rounds=rounds, d=d,
        decoder=decoder, platform_name=platform_name,
        p_scale=noise_params["p_gate_2q"],
    )
    return result.to_dict()


# ── qLDPC simulation ─────────────────────────────────────────────────────────

def run_qldpc_point(code: BBCode, rounds: int, noise_params: dict,
                    n_shots: int) -> dict:
    """Run one qLDPC data point with neutral atom shuttling compiler."""
    compiler = get_qldpc_compiler("neutral_atom", code=code, noise_params=noise_params)
    circuit = compiler.build_memory_circuit(num_rounds=rounds)
    decoder = get_decoder("bposd", circuit, code_type="qldpc")
    result = run_single_experiment(
        circuit=circuit, num_shots=n_shots, num_rounds=rounds, d=0,
        decoder=decoder, platform_name="neutral_atom",
        p_scale=noise_params["p_gate_2q"],
    )
    return result.to_dict()


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Experiment 4: qLDPC vs Surface Code comparison"
    )
    parser.add_argument("--skip-surface", action="store_true",
                        help="Skip surface code simulations")
    parser.add_argument("--skip-qldpc", action="store_true",
                        help="Skip qLDPC simulations")
    args = parser.parse_args()

    platform = get_platform(NEUTRAL_ATOM)
    print("=" * 65)
    print("Experiment 4: qLDPC vs Surface Code (Neutral Atom Platform)")
    print("=" * 65)

    all_results: dict = {"surface": {}, "qldpc": {}}

    # ── Surface code ───────────────────────────────────────────────────────
    if not args.skip_surface:
        print("\n--- Surface Code (NeutralAtomCompiler + MWPM) ---")
        for d in SURFACE_D_VALUES:
            label = f"surface_d{d}"
            all_results["surface"][label] = []
            for p in P_VALUES:
                noise = build_noise_params(p, platform)
                print(f"  d={d}, p={p:.4f} ... ", end="", flush=True)
                t0 = time.perf_counter()
                res = run_surface_code_point(
                    NEUTRAL_ATOM, d=d, rounds=d, noise_params=noise,
                    n_shots=SURFACE_SHOTS,
                )
                elapsed = time.perf_counter() - t0
                res["k"] = 1  # surface code encodes 1 logical qubit
                all_results["surface"][label].append(res)
                print(f"PL={res['PL']:.6f} ({elapsed:.1f}s)")

    # ── qLDPC ──────────────────────────────────────────────────────────────
    if not args.skip_qldpc:
        print("\n--- qLDPC [[72,12,6]] (NeutralAtomQLDPCCompiler + BP+OSD) ---")
        code = build_bb_code_72_12_6()
        label = "qldpc_72_12_6"
        all_results["qldpc"][label] = []

        for p in P_VALUES:
            noise = build_noise_params(p, platform)
            print(f"  p={p:.4f} ... ", end="", flush=True)
            t0 = time.perf_counter()
            try:
                res = run_qldpc_point(
                    code, rounds=QLDPC_ROUNDS, noise_params=noise,
                    n_shots=QLDPC_SHOTS,
                )
                res["k"] = code.k
                all_results["qldpc"][label].append(res)
                elapsed = time.perf_counter() - t0
                print(f"PL={res['PL']:.6f} ({elapsed:.1f}s)")
            except Exception as e:
                print(f"FAILED: {e}")
                all_results["qldpc"][label].append({
                    "p_scale": p, "PL": float("nan"), "k": code.k,
                    "error": str(e),
                })

    # ── Save JSON ──────────────────────────────────────────────────────────
    json_path = RESULTS_DIR / "exp4_qldpc_vs_surface.json"
    with open(json_path, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\nSaved {json_path}")

    # ── Plot ────────────────────────────────────────────────────────────────
    plot_comparison(all_results, RESULTS_DIR)
    print("\n=== Experiment 4 complete ===")


# ── Plotting ─────────────────────────────────────────────────────────────────

def plot_comparison(all_results: dict, results_dir: Path):
    fig, ax = plt.subplots(figsize=(10, 7))

    colors = {
        "surface_d3": "#e63946",
        "surface_d5": "#e63946",
        "qldpc_72_12_6": "#2a9d8f",
    }
    markers = {
        "surface_d3": "s",
        "surface_d5": "D",
        "qldpc_72_12_6": "o",
    }

    for family, codes in all_results.items():
        for label, points in codes.items():
            if not points:
                continue

            p_vals = np.array([pt["p_scale"] for pt in points
                              if not np.isnan(pt.get("PL", float("nan")))],
                              dtype=float)
            pl_vals = np.array([pt["PL"] for pt in points
                               if not np.isnan(pt.get("PL", float("nan")))],
                              dtype=float)
            k_val = points[0].get("k", 1) if points else 1

            if len(p_vals) == 0:
                continue

            color = colors.get(label, "gray")
            marker = markers.get(label, "o")

            if "surface" in label:
                d = label.split("d")[-1]
                name = f"Surface code d={d} (k=1)"
            else:
                name = f"BB [[72,12,6]] (k={k_val})"

            ax.loglog(p_vals, pl_vals, marker=marker, color=color,
                     markersize=9, linewidth=2, label=name, markerfacecolor="white")

    # Reference lines
    p_ref = np.array(P_VALUES)
    ax.loglog(p_ref, p_ref, "k--", linewidth=1, alpha=0.4, label="PL = p (no correction)")

    ax.set_xlabel("Physical 2Q gate error rate  p", fontsize=12)
    ax.set_ylabel("Logical error rate per logical qubit per round  $P_L$", fontsize=12)
    ax.set_title(
        "qLDPC vs Surface Code — Neutral Atom Platform (shuttling noise)",
        fontsize=13,
    )
    ax.legend(fontsize=10, loc="upper left")
    ax.grid(which="both", alpha=0.3, linewidth=0.4)
    ax.tick_params(labelsize=10)
    ax.set_xlim(min(P_VALUES) * 0.7, max(P_VALUES) * 1.3)

    fig.tight_layout()

    png_path = results_dir / "exp4_qldpc_vs_surface.png"
    pdf_path = results_dir / "exp4_qldpc_vs_surface.pdf"
    fig.savefig(png_path, dpi=150)
    fig.savefig(pdf_path)
    print(f"Saved {png_path}  and  {pdf_path}")
    plt.close(fig)


if __name__ == "__main__":
    main()
