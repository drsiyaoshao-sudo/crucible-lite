# Example: GaitSense Ankle Wearable

**Device:** Seeed XIAO nRF52840 Sense — nRF52840 + LSM6DS3TR-C IMU + BLE 5.0  
**Domain:** Gait biomechanics — walking symmetry detection  
**Crucible stages completed:** 0–3 (Stage 4 host integration in progress)  
**Status:** Active development — all five stages documented with real results

---

## What this example demonstrates

GaitSense is the canonical reference implementation of Crucible. It is the project from which the framework was extracted. Everything in CONSTITUTION.md was derived from decisions made — and mistakes caught — during GaitSense development.

Key things this example demonstrates that the framework documentation cannot:

**1. What a toolchain block looks like in practice.**  
Zephyr was the planned firmware toolchain. After three failed attempts to read the IMU (WHO_AM_I returning EIO, root cause P0.27 pin conflict between I2C SCL and session button), it was formally blocked under the three-strike rule. The switch to Arduino was clean, documented, and traceable. The blocked toolchain record is in `toolchain_config.md` with the failure evidence cited.

**2. What a critical safety bug looks like when governance catches it.**  
BUG-013: the SI computation was silently zeroed by an ARM FPU emulator bug (`VABS.F32` broken in Renode 1.16.1). Every healthy walker test passed. The only test that caught it was the pathological walker test — a test explicitly designed to check the device under conditions where the correct answer is non-zero. Without the governance requirement to test non-zero correctness, this bug would have shipped to hardware reporting "perfect symmetry" for every patient.

**3. What 17 device-specific Amendments look like.**  
From the minimal four (primitives, stage gates, toolchain, three-strike) to device-specific rules about signal plot mandates, simulation pipeline integrity, and terrain-aware algorithm design. Each Amendment has a failure mode it was written to prevent.

**4. What the simulation feedback loop looks like.**  
Stage 1 simulation used a physics-based walker model. After field test (Stage 3) with hand-swinging the board (no ankle strap), data was replayed through the simulation to verify the SI computation behaved correctly under realistic (if imperfect) motion.

---

## Domain primitives

```
1. Cadence (steps/min)         — fundamental temporal frequency of gait
2. Step Length (m)             — spatial extent of each step
3. Vertical Oscillation (cm)  — amplitude of centre-of-mass vertical movement per step

All IMU axis values are projections of these three quantities onto the sensor frame.
The Symmetry Index (SI) traces to cadence and step length differences between left/right leg.
```

---

## Where to find the reference implementation

The full codebase is at: `github.com/[org]/gait_device`

Key files for framework adopters:
- `CLAUDE.md` — the device-specific Constitution (17 Amendments, full case law)
- `docs/gaitsense_code/amendments.md` — all 17 ratified Amendments with derivation traces
- `docs/gaitsense_code/case_law.md` — binding precedents (Stair Walker Case, VABS.F32 Case, etc.)
- `docs/toolchain_config.md` — full toolchain record including blocked Zephyr entry
- `docs/executive_branch_document/handoff.md` — Stage 4 hardware bring-up guide
- `docs/executive_branch_document/bug_receipt.md` — all 13 bugs with symptom/root cause/fix
- `.claude/commands/` — session, hear, toolchain, plot-evidence, plot-profile commands

---

## Outcome summary

| Stage | Result |
|-------|--------|
| 0 — HIL Toolchain Lock | CLOSED — USB counter ✓, IMU ✓, algo USB ✓, BLE NUS ✓ |
| 1 — Simulation | CLOSED — 4 profiles × 100/100 steps; pathological SI > 10% on all 4 |
| 2 — Firmware (USB) | CLOSED — STEP# lines on USB serial, SI responds to heel lift |
| 3 — Field Test (BLE) | CLOSED — STEP# lines received on laptop over BLE, 200-step stress test passing |
| 4 — Host Integration | Open |

---

## Lessons for framework adopters

**Lesson 1 — The toolchain is the first thing that breaks.**  
We spent more time on toolchain problems (Zephyr block, SoftDevice UF2 offset, BLE name truncation) than on algorithm problems. HIL first is not a philosophy — it is the result of learning this the hard way.

**Lesson 2 — Simulation and hardware are not the same thing.**  
Amendment 5 (Simulation is the Hardware Proxy) was written because early in the project we treated simulation results as definitive. They are not — they are predictions. The gap between prediction and hardware result is information. When hardware deviates from simulation, that is data about the hardware, not evidence that the simulation is wrong.

**Lesson 3 — "No crash" is not a passing criterion.**  
BUG-013 passed every test that checked "does the firmware run" and "does it produce output." The only thing it failed was "is the output correct under inputs where the correct answer is non-zero." This is Amendment 4 (Stage Gate Confirmation) in practice: confirming the exit criteria are met is not the same as confirming the firmware runs.

**Lesson 4 — Physical derivation is more important than precision.**  
The 30 dps push-off threshold is not a finely-tuned hyperparameter. It is derived from three physical quantities (minimum push-off speed, rebound artifact amplitude, safety margin) and is valid across terrain types. A threshold derived from physical quantities is robust to device-to-device variance. A threshold tuned to a dataset is not.
