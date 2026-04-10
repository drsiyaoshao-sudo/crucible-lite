Run a full Crucible development session from HIL toolchain lock through host integration.

Usage: /session [stage]

Stages:
  status   — read constitutional record, print current stage and open gates
  0        — Stage 0: HIL Toolchain Lock  ← ALWAYS FIRST on any new session or new hardware
  1        — Stage 1: Simulation (physics model or field data replay)
  2        — Stage 2: Firmware Integration on Dev Kit
  3        — Stage 3: Field Test
  4        — Stage 4: Host Integration

If no stage given, run status first, then ask Justice which stage to begin.

---

## Design Principle — HIL First

**Hardware-in-the-loop must be the first gate, not the last.**

Every session begins with Stage 0 before any simulation or algorithm work begins.
Toolchain failures (wrong board, cable, FQBN, BLE name truncation, flash offset) discovered
at Stage 0 take 20 minutes. Discovered at Stage 3, they take days.

Stage 0 is cheap. Stage 0 failure at Stage 3 is expensive.
Article II irreversibility does not apply to Stage 0 — counter flashing is trivially reversible.

---

## Session Initialisation (always runs first)

**Step 0a — Toolchain config check:**
Read `docs/toolchain_config.md`. If missing or lock status is not LOCKED: stop and print:
  "Toolchain config missing or unlocked. Run /toolchain init (new project) or
   /toolchain lock (Stage 0 complete) before starting a session."

Print active toolchain summary: board, FQBN, flash method, wireless transport.
If any blocked toolchain appears in the active slot: stop and report the conflict.

**Step 0b — Domain primitives check:**
Read the project's Amendment 1 (Domain Primitives). Print them. If not yet ratified:
  "Domain primitives not ratified. Name your physical primitives and ratify Amendment 1
   before running any stage. See docs/governance/adoption_guide.md."

**Step 0c — Package check:**
Invoke `package-manager` to verify required Python packages.
Do not proceed until package-manager reports clean.

Print session header:
```
══════════════════════════════════════════════════════════════════
  CRUCIBLE SESSION — $(date)
══════════════════════════════════════════════════════════════════
  Project: [read from docs/device_purpose.md first line]
  Domain primitives: [from Amendment 1]

  Constitutional record:
    Amendments: [N] ratified  — most recent: [title]
    Case law:   [N] precedents recorded

  Stage status:
    Stage 0 — HIL Toolchain Lock:         [CLOSED / OPEN / NOT STARTED]
    Stage 1 — Simulation:                 [CLOSED / OPEN / NOT STARTED]
    Stage 2 — Firmware Integration:       [CLOSED / OPEN / NOT STARTED]
    Stage 3 — Field Test:                 [CLOSED / OPEN / NOT STARTED]
    Stage 4 — Host Integration:           [CLOSED / OPEN / NOT STARTED]

  Active toolchain (from docs/toolchain_config.md):
    Board:    [hardware.board]
    Build:    [active_toolchain.build]
    Flash:    [active_toolchain.flash]
    Observe:  [active_toolchain.serial_monitor]
    Wireless: [active_toolchain.wireless_receiver]

  Skills:
    /session [stage]         — this orchestrator
    /toolchain <subcommand>  — toolchain janitor
    /hear "<name>" A vs B    — judicial hearing
    /hw-advisor              — design suggestions from test results
    /plot-evidence <type>    — evidence collection
    /plot-profile <profile>  — signal diagnostic plot
══════════════════════════════════════════════════════════════════
```

---

## Stage 0 — HIL Toolchain Lock

**Purpose:** Prove the complete build → flash → run → observe loop works.
**Agents:** package-manager (already ran), uart-reader
**Reference:** docs/testing/hil_testing_guide.md

Implements your project's Smoke Test Order Amendment (equivalent of Amendment 16 in GaitSense).
All four tests must pass in sequence. A failure at any step blocks further stages.

### Smoke Test 1 — Counter

Flash a counter program (increments once per second, prints to USB serial).
Expected: `counter=1`, `counter=2`, `counter=3` — no resets.

Failure modes:
- Blank: charge-only USB cable or wrong board variant
- Garbage: baud rate mismatch
- Resets: watchdog or SoftDevice issue

[GATE 0.1] Pass → continue.

### Smoke Test 2 — Sensor Readout

Flash a sensor readout program (reads sensor, prints raw values to USB serial).
Expected: physically plausible values (gravity on Z for IMU; room temp for temperature sensor; etc.)

Failure modes:
- "Sensor init FAILED": I2C address wrong, power-enable pin not asserted
- All zeros: I2C not responding, check pin assignment
- Wrong units: sensor returns g, firmware multiplies by 9.81f (or vice versa)

[GATE 0.2] Pass → continue.

### Smoke Test 3 — Algorithm over USB

Flash full algorithm stack (sensor → algorithm → USB serial output).
Expected: algorithm-specific output within seconds of applying stimulus.

Failure modes:
- No output: input not reaching algorithm
- Always same value: sensor sampling not updating
- Correct output but "zero-when-should-be-nonzero": test explicitly under non-zero input conditions

[GATE 0.3] Pass → continue.

### Smoke Test 4 — Algorithm over Wireless

Flash wireless firmware, run host receiver script.
Expected: same algorithm output received on host.

Failure modes:
- Device not found: name truncation in advertising packet
- Connected but no data: write gated on `connected()` check; write unconditionally
- Truncated lines: MTU fragmentation; shorten format strings or add line-buffer in receiver

[GATE 0.4] **Stage 0 CLOSED.**

**[JUSTICE GATE S0]** All four tests pass → invoke `stage-compactor` to close Stage 0.
Then run `/toolchain lock` to stamp toolchain config as Stage 0 validated.

---

## Stage 1 — Simulation

**Purpose:** Validate algorithm on a physics model of your device domain.
Simulation can also accept field measurement data as input (field data replay).
**Entry condition:** Stage 0 closed.

### Pipeline

```
Physics-model path:
    Define walker/thermal/motion/optical model
    → Run simulation against model
    → Signal plots (your signal plot mandate Amendment)
    → Verify algorithm output matches physical expectation

Field data replay path:
    Capture raw sensor data from Stage 3 field test (or bench capture)
    → Replay through simulation in place of physics model
    → Verify simulation matches observed hardware behaviour
    → If it doesn't: physics model is wrong — update model before fixing firmware
```

**Both paths use the same simulation pipeline.** The difference is the input source.

Run `/plot-profile` for signal diagnostic plots after any algorithm parameter change.

### Exit criteria
- [ ] Algorithm produces correct output on physics model (your domain-specific pass criteria)
- [ ] Algorithm tested under conditions where the correct answer is non-zero (mandatory — BUG-013 class)
- [ ] Signal plots reviewed by Justice
- [ ] No unexplained deviation between simulation and any available field data

**[JUSTICE GATE S1]** → invoke `stage-compactor` to close Stage 1.

---

## Stage 2 — Firmware Integration

**Purpose:** Run the validated algorithm on real hardware via USB serial.
Cross-validate that the dev kit port matches simulation predictions.
**Entry condition:** Stage 1 closed.

### Pipeline

```
1. Build and flash production firmware (algorithm + wireless output)
2. USB serial monitoring path:
   Walk / stimulate sensor / apply test input
   → capture STEP#/event/reading lines
   → compare against Stage 1 simulation prediction
3. Sensitivity test:
   Apply known asymmetry / offset / anomaly
   → output must change measurably
   (e.g. heel lift for gait; known temperature offset for thermostat)
```

Tolerance: hardware vs simulation per your domain-specific Amendment
(GaitSense uses ±5 spm cadence, ±6.3% SI)

### Exit criteria
- [ ] Output within tolerance of Stage 1 simulation on standard stimulus
- [ ] Output changes measurably under known perturbation (sensitivity confirmed)
- [ ] No firmware resets in ≥ 10 min continuous session

**[JUSTICE GATE S2]** → invoke `stage-compactor` to close Stage 2.

---

## Stage 3 — Field Test

**Purpose:** Real device, real conditions. Data captured and fed back to Stage 1.
**Entry condition:** Stage 2 closed.

### Pre-flight (Article II)

Before any field test data collection:
- Justice reviews Stage 2 evidence
- Justice confirms hardware is ready for field deployment
- **JUSTICE APPROVES FIELD TEST** — hard gate, no agent self-selects

### Protocol

Define your field test protocol per your device domain.
At minimum:
1. Baseline run — nominal conditions, measure primary output
2. Perturbation run — known deviation from nominal, measure output change
3. Edge case run — extreme but realistic conditions
4. Data capture — all sessions logged for simulation replay

### Feedback loop to simulation

After field test:
```
Field data → replay in Stage 1 simulation
If simulation matches field: physics model is valid ✓
If simulation does not match: update physics model, re-run Stage 1
                              (do not fix firmware until simulation matches)
```

### Exit criteria
- [ ] Baseline run: output within target range
- [ ] Perturbation run: output changes measurably in expected direction
- [ ] Field data replayed in simulation: model validated or updated
- [ ] All deviations explained and recorded in case law

**[JUSTICE GATE S3]** → invoke `stage-compactor` to close Stage 3.

---

## Stage 4 — Host Integration

**Purpose:** Connect device to smart home hub, gateway, cloud, or other consumer system.
**Entry condition:** Stages 0–3 all closed.

### Pipeline

```
1. Host system connection (MQTT, Matter, BLE GATT, REST API)
2. Data ingestion verification:
   → Host receives correct values
   → Host handles device disconnect/reconnect gracefully
3. Automation trigger test:
   → Define one automation (light on = occupancy detected, alert = threshold exceeded)
   → Verify trigger fires correctly and within latency budget
4. Long-run stability (≥ 30 min session)
   → No dropped connections, no corrupt data, no false triggers
```

### Exit criteria
- [ ] Host receives correct values matching Stage 3 field test output
- [ ] Automation trigger fires correctly with latency < [your target]
- [ ] 30-min stability: no resets, no dropped data, no false triggers

**[JUSTICE GATE S4 — FINAL]** → invoke `stage-compactor` to close Stage 4.

---

## Constitutional References

- Article I: all thresholds trace to domain primitives — not to data fitting
- Article II: no field test or host deployment without Justice approval
- Amendment 1: domain primitives (your device-specific version)
- Amendment 2: stage gate order
- Amendment 3: toolchain alignment
- Amendment 4: three-strike escalation — three failures → /hear before new approach
