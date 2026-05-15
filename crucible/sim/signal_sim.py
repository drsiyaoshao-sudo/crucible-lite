"""
Signal-only simulation path — pure Python, no Renode, no firmware.

Validates algorithm logic and signal model consistency without running firmware.

When to use this path vs the Renode path
-----------------------------------------
Signal-only (this module):
  - Algorithm under development — firmware not yet written
  - Fast iteration on signal model / physics parameters
  - Cross-checking a Python algorithm model against expected output
  - CI environments without Renode
  - Any run where you want results in seconds, not minutes

Renode path (crucible.sim.renode):
  - Firmware correctness validation — the C implementation must produce the
    same output as the Python model for the same input
  - Stage 1 gate requires at least one Renode run to validate firmware parity
  - Pre-Stage 2 confirmation that the firmware port matches the Python model

The signal-only path is NOT a substitute for the Renode path at Stage 1 gate.
It is a faster inner loop for the algorithm development work that precedes it.

Public API
----------
    SignalSimulator(signal_generator, algorithm)
    result  = simulator.run(profile, n_steps)
    results = simulator.run_matrix(profiles, n_steps)

    compare_paths(signal_result, renode_result, metric_keys, tolerance)
"""
from __future__ import annotations

from typing import Any, Callable

import numpy as np


class SignalSimulator:
    """Run the project's algorithm in pure Python against generated signal data.

    Parameters
    ----------
    signal_generator : callable
        ``generate(profile: str, n_steps: int) -> np.ndarray``
        The project's physics model / signal generator.
        Lives in ``src/signals.py``, generated as a stub by ``/toolchain scaffold``
        and implemented by the project engineer.
    algorithm : callable
        ``run(samples: np.ndarray) -> dict[str, Any]``
        Python model of the firmware algorithm. Must produce the same output
        as the firmware for the same input — that equivalence is what Stage 1
        validates against the Renode path.
        Lives in ``src/algorithm.py``, generated as a stub by ``/toolchain scaffold``.
    """

    def __init__(
        self,
        signal_generator: Callable[[str, int], np.ndarray],
        algorithm: Callable[[np.ndarray], dict[str, Any]],
    ) -> None:
        self._generate = signal_generator
        self._run_algorithm = algorithm

    def run(
        self,
        profile: str,
        n_steps: int = 100,
    ) -> dict[str, Any]:
        """Run one simulation profile.

        Parameters
        ----------
        profile : str
            Profile name (must be declared in docs/device_context.md
            Signal Inventory / Operating Envelope).
        n_steps : int
            Number of simulation steps. Domain-specific: steps for gait,
            samples for a sensor stream, cycles for a control loop, etc.

        Returns
        -------
        dict
            Metric dict from ``algorithm.run()``. Keys are domain primitive
            names from Amendment 1. Augmented with three private keys:

            ``_profile``  str        profile name
            ``_n_steps``  int        n_steps used
            ``_samples``  np.ndarray raw generated samples (for plotting)

        Raises
        ------
        NotImplementedError
            If the project's ``src/signals.py`` or ``src/algorithm.py`` stubs
            have not been implemented.
        ValueError
            If the signal generator returns an empty or malformed array.
        """
        samples = self._generate(profile, n_steps)
        if samples is None or (hasattr(samples, "__len__") and len(samples) == 0):
            raise ValueError(
                f"Signal generator returned empty samples for profile '{profile}'. "
                "Check src/signals.py generate() implementation."
            )

        result = self._run_algorithm(samples)

        if not isinstance(result, dict):
            raise TypeError(
                f"Algorithm run() must return a dict of metrics. "
                f"Got: {type(result).__name__}. Check src/algorithm.py."
            )

        result["_profile"] = profile
        result["_n_steps"] = n_steps
        result["_samples"] = samples
        return result

    def run_matrix(
        self,
        profiles: list[str],
        n_steps: int = 100,
    ) -> dict[str, dict[str, Any]]:
        """Run a full profile matrix.

        Parameters
        ----------
        profiles : list[str]
            Profile names from docs/device_context.md Signal Inventory.
        n_steps : int
            Applied to every profile in the matrix.

        Returns
        -------
        dict[profile_name, result_dict]
            Each value is the result of ``run(profile, n_steps)``.
            Failed profiles have an ``"_error"`` key with the exception message.
        """
        results: dict[str, dict[str, Any]] = {}
        for profile in profiles:
            try:
                results[profile] = self.run(profile, n_steps)
            except Exception as exc:
                results[profile] = {
                    "_profile": profile,
                    "_n_steps": n_steps,
                    "_samples": None,
                    "_error": str(exc),
                }
        return results


# ─────────────────────────────────────────────────────────────────────────────
# Path comparison utility
# ─────────────────────────────────────────────────────────────────────────────

def compare_paths(
    signal_result: dict[str, Any],
    renode_result: dict[str, Any],
    metric_keys: list[str],
    tolerance: dict[str, float],
) -> dict[str, dict]:
    """Compare signal-only and Renode path outputs for the same profile.

    Used at Stage 1 to verify that the Python algorithm model and the
    firmware implementation agree within tolerance.

    Parameters
    ----------
    signal_result : dict
        Output of ``SignalSimulator.run()``.
    renode_result : dict
        Metrics parsed from the Renode UART log (project's ``src/analysis.py``).
    metric_keys : list[str]
        Metric names to compare (domain primitive keys from Amendment 1).
    tolerance : dict[str, float]
        Allowed absolute difference per metric key.
        e.g. ``{"symmetry_index_pct": 1.0, "cadence_spm": 2.0}``

    Returns
    -------
    dict[metric_key, {"signal": v, "renode": v, "diff": d, "pass": bool}]
        One entry per metric key.
    """
    comparison: dict[str, dict] = {}
    for key in metric_keys:
        sv = signal_result.get(key)
        rv = renode_result.get(key)
        tol = tolerance.get(key, 0.0)

        if sv is None or rv is None:
            comparison[key] = {
                "signal": sv,
                "renode": rv,
                "diff": None,
                "pass": False,
                "note": "missing in one path",
            }
            continue

        diff = abs(float(sv) - float(rv))
        comparison[key] = {
            "signal": float(sv),
            "renode": float(rv),
            "diff": diff,
            "pass": diff <= tol,
        }
    return comparison


def format_comparison_report(
    profile: str,
    comparison: dict[str, dict],
) -> str:
    """Format a compare_paths result as a human-readable report."""
    lines = [
        f"PATH COMPARISON — profile: {profile}",
        f"{'Metric':<28} {'Signal-only':>12} {'Renode':>12} {'Diff':>10} {'Pass?':>6}",
        "─" * 72,
    ]
    all_pass = True
    for key, row in comparison.items():
        sv = f"{row['signal']:.3f}" if row["signal"] is not None else "—"
        rv = f"{row['renode']:.3f}" if row["renode"] is not None else "—"
        df = f"{row['diff']:.3f}" if row["diff"] is not None else "—"
        ok = "PASS" if row["pass"] else "FAIL"
        if not row["pass"]:
            all_pass = False
        note = f"  ← {row['note']}" if row.get("note") else ""
        lines.append(f"{key:<28} {sv:>12} {rv:>12} {df:>10} {ok:>6}{note}")
    lines.append("─" * 72)
    lines.append("PATHS AGREE" if all_pass else "PATHS DIVERGE — Python model and firmware differ")
    return "\n".join(lines)
