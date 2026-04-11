"""
Signal diagnostic plot utilities.

All functions write to a file and return the output path. No top-level
script code — import and call. Matplotlib backend is set to Agg so these
run headless in CI without a display.

Typical usage:
    from crucible.signal.plot import plot_si_bar, plot_step_count_bar, plot_signal_trace

    plot_si_bar(results, output="docs/plots/si_comparison.png")
    plot_signal_trace(samples, title="Flat walk 100 steps", output="docs/plots/trace.png")
"""
from __future__ import annotations

from pathlib import Path
from typing import Sequence

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


# ─────────────────────────────────────────────────────────────────────────────
# SI / step-count bar chart
# ─────────────────────────────────────────────────────────────────────────────

def plot_si_bar(
    results: dict[str, dict],
    labels: Sequence[str] | None = None,
    output: str | Path = "si_comparison.png",
    si_tolerance_pct: float = 3.0,
    title: str = "Symmetry Index Comparison",
    dpi: int = 150,
) -> Path:
    """Bar chart comparing SI% across profiles for two detectors.

    Parameters
    ----------
    results : dict
        Keyed by profile name. Each value must contain:
            "std_si"    float | None  — standard-detector SI%
            "new_si"    float | None  — new-detector SI%
        Optional keys:
            "std_count" int  — step count for standard detector
            "new_count" int  — step count for new detector
    labels : list[str] | None
        Human-readable labels for each profile (same order as results keys).
        Defaults to the keys of `results`.
    output : str | Path
        Destination file path.
    si_tolerance_pct : float
        Red dashed threshold line.
    title : str
        Figure suptitle.
    dpi : int

    Returns
    -------
    Path
        Resolved output path.
    """
    profile_keys = list(results.keys())
    if labels is None:
        labels = profile_keys

    COLORS_STD = "#90CAF9"
    COLORS_NEW = "#1565C0"

    std_si_vals = [
        results[k]["std_si"] if results[k].get("std_si") is not None else 0.0
        for k in profile_keys
    ]
    new_si_vals = [
        results[k]["new_si"] if results[k].get("new_si") is not None else 0.0
        for k in profile_keys
    ]

    x = np.arange(len(profile_keys))
    w = 0.35

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.suptitle(title, fontsize=12)

    b1 = ax.bar(x - w / 2, std_si_vals, w, color=COLORS_STD,
                label="Standard", edgecolor="white")
    b2 = ax.bar(x + w / 2, new_si_vals, w, color=COLORS_NEW,
                label="New", edgecolor="white")

    ax.axhline(si_tolerance_pct, color="red", linewidth=1.2, linestyle="--",
               label=f"±{si_tolerance_pct}% tolerance")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylabel("SI (%)")
    ax.set_title(f"Symmetry Index (target <{si_tolerance_pct}%)")
    y_max = max(max(std_si_vals), max(new_si_vals), si_tolerance_pct + 0.5) * 1.2
    ax.set_ylim(0, y_max)
    ax.legend(fontsize=9)
    ax.grid(True, axis="y", alpha=0.3)

    for bar, val in zip(list(b1) + list(b2), std_si_vals + new_si_vals):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 0.05,
                f"{val:.2f}%", ha="center", va="bottom", fontsize=9, fontweight="bold")

    plt.tight_layout()
    out = Path(output).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(str(out), dpi=dpi)
    plt.close(fig)
    return out


def plot_step_count_bar(
    results: dict[str, dict],
    labels: Sequence[str] | None = None,
    target: int = 100,
    tolerance: int = 5,
    output: str | Path = "step_count.png",
    title: str = "Step Count Comparison",
    dpi: int = 150,
) -> Path:
    """Bar chart comparing detected step counts across profiles.

    Parameters
    ----------
    results : dict
        Keyed by profile name. Each value must contain:
            "std_count" int  — standard-detector step count
            "new_count" int  — new-detector step count
    labels : list[str] | None
    target : int
        Expected step count for the dashed reference line.
    tolerance : int
        Pass/fail band around the target (±tolerance).
    output : str | Path
    title : str
    dpi : int
    """
    profile_keys = list(results.keys())
    if labels is None:
        labels = profile_keys

    COLORS_STD = "#90CAF9"
    COLORS_NEW = "#1565C0"

    std_counts = [results[k].get("std_count", 0) for k in profile_keys]
    new_counts = [results[k].get("new_count", 0) for k in profile_keys]

    x = np.arange(len(profile_keys))
    w = 0.35

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.suptitle(title, fontsize=12)

    b1 = ax.bar(x - w / 2, std_counts, w, color=COLORS_STD,
                label="Standard", edgecolor="white")
    b2 = ax.bar(x + w / 2, new_counts, w, color=COLORS_NEW,
                label="New", edgecolor="white")

    ax.axhline(target, color="green", linewidth=1.2, linestyle="--",
               label=f"Target ({target} ±{tolerance})")
    ax.axhline(target - tolerance, color="green", linewidth=0.6, linestyle=":", alpha=0.5)
    ax.axhline(target + tolerance, color="green", linewidth=0.6, linestyle=":", alpha=0.5)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylabel("Steps detected")
    ax.set_title(f"Step Count (target {target} ±{tolerance})")
    ax.set_ylim(0, max(max(std_counts), max(new_counts), target + tolerance) * 1.15)
    ax.legend(fontsize=9)
    ax.grid(True, axis="y", alpha=0.3)

    for bar, val in zip(list(b1) + list(b2), std_counts + new_counts):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 0.5,
                str(val), ha="center", va="bottom", fontsize=9, fontweight="bold")

    plt.tight_layout()
    out = Path(output).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(str(out), dpi=dpi)
    plt.close(fig)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# IMU signal trace
# ─────────────────────────────────────────────────────────────────────────────

def plot_signal_trace(
    samples: "np.ndarray",
    odr_hz: float = 208.0,
    title: str = "IMU Signal Trace",
    output: str | Path = "signal_trace.png",
    channels: Sequence[str] = ("ax", "ay", "az", "gx", "gy", "gz"),
    dpi: int = 150,
) -> Path:
    """Plot raw IMU samples as time-series traces.

    Parameters
    ----------
    samples : np.ndarray (N, 6)
        Columns: [ax ay az gx gy gz] in physical units (m/s² and dps).
    odr_hz : float
        Sample rate used to build the time axis.
    title : str
    output : str | Path
    channels : sequence of 6 str
        Column labels.
    dpi : int
    """
    import numpy as np
    n = len(samples)
    t = np.arange(n) / odr_hz

    fig, axes = plt.subplots(2, 1, figsize=(14, 6), sharex=True)
    fig.suptitle(title, fontsize=11)

    # Accelerometer
    ax0 = axes[0]
    for i, label in enumerate(channels[:3]):
        ax0.plot(t, samples[:, i], linewidth=0.8, label=label)
    ax0.set_ylabel("Acceleration (m/s²)")
    ax0.legend(fontsize=8, loc="upper right")
    ax0.grid(True, alpha=0.3)

    # Gyroscope
    ax1 = axes[1]
    for i, label in enumerate(channels[3:6]):
        ax1.plot(t, samples[:, i + 3], linewidth=0.8, label=label)
    ax1.set_ylabel("Angular rate (dps)")
    ax1.set_xlabel("Time (s)")
    ax1.legend(fontsize=8, loc="upper right")
    ax1.grid(True, alpha=0.3)

    plt.tight_layout()
    out = Path(output).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(str(out), dpi=dpi)
    plt.close(fig)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Snapshot SI timeline
# ─────────────────────────────────────────────────────────────────────────────

def plot_snapshot_timeline(
    snapshots: list,
    si_tolerance_pct: float = 3.0,
    output: str | Path = "snapshot_timeline.png",
    title: str = "Snapshot Timeline",
    dpi: int = 150,
) -> Path:
    """Plot SI% and cadence over session snapshots.

    Parameters
    ----------
    snapshots : list[SnapshotEvent]
    si_tolerance_pct : float
        Reference line for SI pass/fail.
    output : str | Path
    title : str
    dpi : int
    """
    if not snapshots:
        raise ValueError("No snapshots to plot.")

    indices  = [s.anchor_step for s in snapshots]
    si_vals  = [s.si_stance_pct for s in snapshots]
    cad_vals = [s.mean_cadence_spm for s in snapshots]

    fig, axes = plt.subplots(2, 1, figsize=(12, 6), sharex=True)
    fig.suptitle(title, fontsize=11)

    axes[0].plot(indices, si_vals, marker="o", linewidth=1.2, color="#1565C0")
    axes[0].axhline(si_tolerance_pct, color="red", linestyle="--",
                    linewidth=1.0, label=f"±{si_tolerance_pct}% tolerance")
    axes[0].set_ylabel("SI stance (%)")
    axes[0].legend(fontsize=8)
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(indices, cad_vals, marker="s", linewidth=1.2, color="#43A047")
    axes[1].set_ylabel("Cadence (spm)")
    axes[1].set_xlabel("Anchor step index")
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    out = Path(output).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(str(out), dpi=dpi)
    plt.close(fig)
    return out
