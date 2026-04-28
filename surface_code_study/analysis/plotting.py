"""
Reusable plotting utilities for surface code study results.
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import matplotlib.pyplot as plt
import numpy as np


# ── Style constants ───────────────────────────────────────────────────────────

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


# ── Shared style setup ────────────────────────────────────────────────────────

def setup_style():
    """Apply a clean style to all subsequent matplotlib plots."""
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 11,
        "axes.labelsize": 12,
        "axes.titlesize": 13,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
        "figure.dpi": 150,
        "savefig.dpi": 150,
        "savefig.bbox": "tight",
    })


# ── Shared plot helpers ───────────────────────────────────────────────────────

def plot_with_upper_limits(
    ax: plt.Axes,
    x: np.ndarray,
    y: np.ndarray,
    yerr: np.ndarray,
    hit_max: np.ndarray,
    color: str,
    label: str,
    marker: str = "o",
) -> None:
    """
    Plot data on ax with error bars, handling upper-limit points.

    Parameters
    ----------
    ax : plt.Axes
    x, y, yerr : arrays of same length
    hit_max : bool array
        True where max_shots was hit (plot as upper limit with arrow).
    color, label, marker : passed to errorbar.
    """
    normal_mask = ~hit_max
    ul_mask     =  hit_max

    if np.any(normal_mask):
        ax.errorbar(
            x[normal_mask], y[normal_mask],
            yerr=yerr[normal_mask],
            marker=marker, markersize=6, linewidth=1.8,
            capsize=3, color=color, label=label,
        )

    if np.any(ul_mask):
        ax.errorbar(
            x[ul_mask], y[ul_mask],
            yerr=yerr[ul_mask],
            marker=None, linewidth=0,
            uplims=True, color=color, alpha=0.4,
        )
        ax.scatter(
            x[ul_mask], y[ul_mask],
            marker="v", s=20, color=color, alpha=0.4,
        )


def save_fig(fig: plt.Figure, path_png: Path | str, path_pdf: Path | str | None = None):
    """Save figure in PNG and optionally PDF."""
    path_png = Path(path_png)
    fig.savefig(path_png)
    print(f"Saved {path_png}")
    if path_pdf:
        path_pdf = Path(path_pdf)
        fig.savefig(path_pdf)
        print(f"Saved {path_pdf}")
    plt.close(fig)


# ── Quick preview from JSON ────────────────────────────────────────────────────

def plot_json_results(
    json_path: str | Path,
    title: str,
    xlabel: str,
    ylabel: str,
    xkey: str,
    ykey: str = "PL",
    yerrkey: str = "PL_std",
    out_png: str | Path | None = None,
) -> plt.Figure:
    """
    Quick plot from a saved exp JSON file.

    Parameters
    ----------
    json_path : path to expN_pl_vs_*.json
    title, xlabel, ylabel : axis labels
    xkey : key in each result dict to use as x (e.g. "p_scale", "d")
    ykey, yerrkey : keys for y and yerr
    out_png : if given, save to this path

    Returns
    -------
    fig : plt.Figure
    """
    import json

    setup_style()

    with open(json_path) as f:
        data = json.load(f)

    fig, ax = plt.subplots(figsize=(7, 5))

    # Detect format: flat list or {platform: [results]}
    if isinstance(data, list):
        platforms = {"_": data}
    else:
        platforms = data

    for pname, results in platforms.items():
        x_vals = np.array([r[xkey] for r in results])
        y_vals = np.array([r[ykey] for r in results])
        y_err = np.array([r.get(yerrkey, 0) for r in results])
        hit_max = np.array([r.get("hit_max_shots", False) for r in results])

        color = COLORS.get(pname, "gray")
        label = LABELS.get(pname, pname)
        plot_with_upper_limits(ax, x_vals, y_vals, y_err, hit_max, color, label)

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend()
    ax.grid(which="both", alpha=0.3, linewidth=0.4)

    if out_png:
        save_fig(fig, out_png)

    return fig
