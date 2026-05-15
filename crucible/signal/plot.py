"""
Generic signal diagnostic plot utilities — infrastructure layer.

All functions are parameterized by metric name, unit, and axis labels.
No domain knowledge is baked in (no gait, no temperature, no pressure).

Projects generate domain-specific wrappers in src/plot.py via
`/toolchain scaffold`, which uses domain primitive names and units
from Amendment 1 (docs/device_context.md Signal Inventory) as labels.

All functions:
  - Write to a file and return the resolved output Path.
  - Never display to screen (Agg backend — headless CI safe).
  - Create output directory if it does not exist.
"""
from __future__ import annotations

from pathlib import Path
from typing import Sequence

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


# ─────────────────────────────────────────────────────────────────────────────
# Raw sensor time-series trace
# ─────────────────────────────────────────────────────────────────────────────

def plot_sensor_trace(
    samples: "np.ndarray",
    odr_hz: float = 100.0,
    title: str = "Sensor Trace",
    output: str | Path = "sensor_trace.png",
    channels: Sequence[str] | None = None,
    channel_groups: Sequence[tuple[str, str]] | None = None,
    dpi: int = 150,
) -> Path:
    """Plot raw sensor samples as time-series traces.

    Parameters
    ----------
    samples : np.ndarray (N,) or (N, C)
        Sensor data. Single-channel or multi-channel.
    odr_hz : float
        Sample rate used to build the time axis.
    title : str
    output : str | Path
    channels : sequence[str] | None
        Column labels. Defaults to ``ch0``, ``ch1``, ...
    channel_groups : sequence[(label, unit)] | None
        One entry per subplot. Columns are split evenly across groups.
        If None, all channels appear in a single subplot.
    dpi : int
    """
    if samples.ndim == 1:
        samples = samples[:, np.newaxis]
    n, c = samples.shape
    t = np.arange(n) / odr_hz
    ch_labels = list(channels) if channels else [f"ch{i}" for i in range(c)]

    if channel_groups:
        n_groups = len(channel_groups)
        cols_per = c // n_groups
        fig, axes = plt.subplots(n_groups, 1, figsize=(14, 4 * n_groups), sharex=True)
        if n_groups == 1:
            axes = [axes]
        fig.suptitle(title, fontsize=11)
        for g, (ax, (grp_label, grp_unit)) in enumerate(zip(axes, channel_groups)):
            start = g * cols_per
            end = (start + cols_per) if g < n_groups - 1 else c
            for i in range(start, end):
                ax.plot(t, samples[:, i], linewidth=0.8, label=ch_labels[i])
            ax.set_ylabel(f"{grp_label} ({grp_unit})")
            ax.legend(fontsize=8, loc="upper right")
            ax.grid(True, alpha=0.3)
        axes[-1].set_xlabel("Time (s)")
    else:
        fig, ax = plt.subplots(figsize=(14, 4))
        fig.suptitle(title, fontsize=11)
        for i in range(c):
            ax.plot(t, samples[:, i], linewidth=0.8, label=ch_labels[i])
        ax.set_xlabel("Time (s)")
        ax.legend(fontsize=8, loc="upper right")
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    out = Path(output).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(str(out), dpi=dpi)
    plt.close(fig)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Per-profile metric bar chart
# ─────────────────────────────────────────────────────────────────────────────

def plot_metric_bar(
    results: dict[str, dict],
    metric_key: str,
    metric_label: str,
    metric_unit: str,
    threshold: float | None = None,
    threshold_label: str | None = None,
    labels: Sequence[str] | None = None,
    compare_key: str | None = None,
    compare_label: str = "Comparison",
    output: str | Path = "metric_bar.png",
    title: str | None = None,
    dpi: int = 150,
) -> Path:
    """Bar chart comparing a metric across simulation/field profiles.

    Parameters
    ----------
    results : dict[profile_name, dict]
        Each value must contain ``metric_key``. May also contain ``compare_key``.
    metric_key : str
        Primary metric field (e.g. ``"mean_error"``).
    metric_label : str
        Y-axis label (e.g. ``"Symmetry Index"``).
    metric_unit : str
        Unit string (e.g. ``"%"``, ``"°C"``).
    threshold : float | None
        Reference line (e.g. pass/fail boundary).
    threshold_label : str | None
        Legend label for the reference line.
    labels : sequence[str] | None
        Profile display names (defaults to ``results`` keys).
    compare_key : str | None
        If given, draw a second bar series using this key.
    compare_label : str
        Legend label for the second series.
    output : str | Path
    title : str | None
    dpi : int
    """
    profile_keys = list(results.keys())
    display_labels = list(labels) if labels else profile_keys
    primary_vals = [float(results[k].get(metric_key) or 0.0) for k in profile_keys]

    COLOR_A = "#90CAF9"
    COLOR_B = "#1565C0"
    x = np.arange(len(profile_keys))

    fig, ax = plt.subplots(figsize=(10, 5))
    if title:
        fig.suptitle(title, fontsize=12)
    elif threshold is not None:
        fig.suptitle(
            f"{metric_label} (target < {threshold} {metric_unit})", fontsize=12
        )

    if compare_key:
        compare_vals = [float(results[k].get(compare_key) or 0.0) for k in profile_keys]
        w = 0.35
        b1 = ax.bar(x - w / 2, primary_vals, w, color=COLOR_A,
                    label=metric_label, edgecolor="white")
        b2 = ax.bar(x + w / 2, compare_vals, w, color=COLOR_B,
                    label=compare_label, edgecolor="white")
        for bar, val in zip(list(b1) + list(b2), primary_vals + compare_vals):
            ax.text(bar.get_x() + bar.get_width() / 2, val * 1.02,
                    f"{val:.2f}", ha="center", va="bottom", fontsize=9, fontweight="bold")
    else:
        b1 = ax.bar(x, primary_vals, 0.6, color=COLOR_B, edgecolor="white")
        for bar, val in zip(b1, primary_vals):
            ax.text(bar.get_x() + bar.get_width() / 2, val * 1.02,
                    f"{val:.2f}", ha="center", va="bottom", fontsize=9, fontweight="bold")

    if threshold is not None:
        lbl = threshold_label or f"threshold ({threshold} {metric_unit})"
        ax.axhline(threshold, color="red", linewidth=1.2, linestyle="--", label=lbl)

    ax.set_xticks(x)
    ax.set_xticklabels(display_labels, fontsize=10)
    ax.set_ylabel(f"{metric_label} ({metric_unit})")
    ax.legend(fontsize=9)
    ax.grid(True, axis="y", alpha=0.3)

    plt.tight_layout()
    out = Path(output).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(str(out), dpi=dpi)
    plt.close(fig)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Event sequence metric timeline
# ─────────────────────────────────────────────────────────────────────────────

def plot_metric_timeline(
    events: list,
    index_field: str,
    primary_field: str,
    primary_label: str,
    primary_unit: str,
    secondary_field: str | None = None,
    secondary_label: str | None = None,
    secondary_unit: str | None = None,
    threshold: float | None = None,
    output: str | Path = "metric_timeline.png",
    title: str = "Metric Timeline",
    dpi: int = 150,
) -> Path:
    """Plot one or two metrics from a sequence of parsed UART events.

    Works with both ``UartEvent`` objects (accessing ``.fields``) and plain
    dataclass instances (accessing attributes directly).

    Parameters
    ----------
    events : list
        Sequence of event objects. Each must expose ``index_field`` and
        ``primary_field`` as either a ``.fields`` dict key or an attribute.
    index_field : str
        X-axis field (e.g. ``"anchor_step"``, ``"sample_index"``).
    primary_field : str
        First metric field.
    primary_label : str
        Y-axis label for the primary subplot.
    primary_unit : str
    secondary_field : str | None
        If given, a second subplot is drawn.
    secondary_label : str | None
    secondary_unit : str | None
    threshold : float | None
        Reference line on the primary axis.
    output : str | Path
    title : str
    dpi : int
    """

    def _get(ev: object, key: str) -> float:
        if isinstance(ev, dict):
            return float(ev.get(key, 0))
        if hasattr(ev, "fields"):
            return float(getattr(ev, "fields", {}).get(key, 0))
        return float(getattr(ev, key, 0))

    indices = [_get(ev, index_field) for ev in events]
    primary_vals = [_get(ev, primary_field) for ev in events]

    n_axes = 2 if secondary_field else 1
    fig, axes = plt.subplots(n_axes, 1, figsize=(12, 4 * n_axes), sharex=True)
    if n_axes == 1:
        axes = [axes]
    fig.suptitle(title, fontsize=11)

    axes[0].plot(indices, primary_vals, marker="o", linewidth=1.2, color="#1565C0")
    if threshold is not None:
        axes[0].axhline(
            threshold, color="red", linestyle="--", linewidth=1.0,
            label=f"threshold ({threshold} {primary_unit})",
        )
        axes[0].legend(fontsize=8)
    axes[0].set_ylabel(f"{primary_label} ({primary_unit})")
    axes[0].grid(True, alpha=0.3)

    if secondary_field and secondary_label and secondary_unit:
        secondary_vals = [_get(ev, secondary_field) for ev in events]
        axes[1].plot(indices, secondary_vals, marker="s", linewidth=1.2, color="#43A047")
        axes[1].set_ylabel(f"{secondary_label} ({secondary_unit})")
        axes[1].set_xlabel(index_field)
        axes[1].grid(True, alpha=0.3)
    else:
        axes[0].set_xlabel(index_field)

    plt.tight_layout()
    out = Path(output).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(str(out), dpi=dpi)
    plt.close(fig)
    return out
