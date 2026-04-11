"""
Structured event types emitted by firmware over UART during a session.

These are domain-agnostic containers. A project's signal_analysis module
parses raw UART text into these types; the simulation pipeline and host
tools consume them without knowing the underlying domain.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class StepEvent:
    """One detected step from the firmware."""
    step_index:   int
    ts_ms:        float   # timestamp in milliseconds
    peak_acc_mag: float   # peak acceleration magnitude, m/s²
    peak_gyr_y:   float   # peak gyro Y, dps
    cadence_spm:  float   # instantaneous cadence, steps/min


@dataclass
class SnapshotEvent:
    """Rolling symmetry/cadence summary emitted every N steps."""
    anchor_step:        int
    anchor_ts_ms:       float
    si_stance_pct:      float   # stance-phase symmetry index, %
    si_swing_pct:       float   # swing-phase symmetry index, %
    si_peak_angvel_pct: float   # peak angular velocity SI, %
    mean_cadence_spm:   float   # mean cadence over the window, steps/min
    step_count:         int     # steps in this window
    is_running:         bool


@dataclass
class SessionEndEvent:
    """Emitted once at the end of a recording session."""
    total_steps: int
