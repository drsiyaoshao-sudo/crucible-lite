# Adoption Guide — Adapting Crucible for Your Device

This guide walks you through forking Crucible and making it operational for your specific hardware project. Estimated time for a single engineer on a well-understood device: 2–4 hours.

---

## What you keep verbatim

The following never change regardless of your device domain:

| Element | Why it is universal |
|---------|-------------------|
| Article I (Signal First) | The requirement to trace parameters to physical quantities applies to every measurement domain |
| Article II (Human in the Loop) | The irreversibility of hardware actions is a physical fact, not a convention |
| Bill format | Structured evidence requirement works for every type of change |
| Judicial hearing procedure | Conflict resolution by evidence works for any technical dispute |
| Three-strike escalation rule | Diminishing returns after three failed attempts is domain-independent |
| Stage 0 (HIL Toolchain Lock) | Toolchain failures discovered late are expensive in every domain |

---

## What you replace

### 1. Domain primitives (Article I implementation)

The most important step. Before writing a single Amendment, name your primitives.

**Template:**
```
### Domain Primitives — [Device Name]

The [Device Name] ultimately measures / controls:
  1. [Primitive 1] ([unit])  — [one-line physical description]
  2. [Primitive 2] ([unit])  — [one-line physical description]
  3. [Primitive 3] ([unit])  — [optional; most domains have 2–3 primitives]

Every threshold, filter cutoff, FSM transition, and algorithm parameter
in this project must trace to one of these three quantities.
A parameter that cannot be so traced is a guess and is not permitted.

Derivation chain example:
  [Sensor reading] → [physical quantity 1] → [primitive 1]
  e.g. acc_z (m/s²) → vertical acceleration → Vertical Oscillation (cm)
```

**Examples by device type:**

*Environmental monitor (indoor air quality):*
```
1. PM2.5 concentration (μg/m³)   — particulate matter in respirable size range
2. CO2 concentration (ppm)        — proxy for ventilation adequacy
3. Relative Humidity (%)          — comfort and mould risk
All sensor counts, Mie scattering coefficients, and NDIR absorption values
are measurements of these three quantities.
```

*Smart irrigation controller:*
```
1. Volumetric Water Content (m³/m³) — actual soil moisture
2. Evapotranspiration rate (mm/day) — water loss to atmosphere
3. Field Capacity (%)               — upper bound of plant-available water
Soil resistance readings, dielectric constant measurements, and rain sensor
counts are measurements of these three quantities.
```

*Vibration-based predictive maintenance:*
```
1. RMS acceleration (m/s²)         — overall vibration energy
2. Dominant frequency (Hz)         — identifies fault signature
3. Kurtosis                        — impulsiveness (bearing fault indicator)
Raw FFT bins, filter outputs, and ADC counts are measurements of these.
```

---

### 2. Stage gate sequence (your Amendment 1)

The reference implementation has 5 stages: HIL lock, simulation, firmware, field test, integration. Your device may need a different sequence.

**Questions to ask:**
- Can you simulate before you have hardware? If yes, simulation precedes HIL.
- Is there a regulatory submission gate that must happen before field testing?
- Does integration (cloud, smart home) block field testing, or can it run in parallel?

The sequence must be written as an explicit Amendment before your first session. The stage gate Amendment is the contract between you and your future self about what "done" means at each step.

**Minimum viable stage gate Amendment:**
```
### Amendment [N] — Stage Gate Order

Development proceeds in exactly this order:
  0: HIL Toolchain Lock
  1: [your simulation / algorithm validation stage]
  2: [your firmware integration stage]
  3: [your field test stage]
  4: [your integration / deployment stage]

No stage begins until the previous stage's exit criteria are explicitly
confirmed by the human and recorded.
```

---

### 3. Toolchain alignment (your toolchain Amendment + toolchain_config.md)

Run `/toolchain init` to create your `docs/toolchain_config.md`. This creates the Record of Truth for all build, flash, and test operations.

Mandatory sections:
- Hardware: board model, MCU, sensors, I2C/SPI addresses
- Pin map: every signal with its GPIO assignment and any conflict warnings
- Active firmware toolchain: FQBN or build command, flash method, serial monitor
- Blocked toolchains: any tool that was tried and failed (even partial attempts count)
- Library manifest: pinned versions of every library used
- Repository registry: this repo and any cross-referenced repos

---

### 4. Your Amendments

Start with the four mandatory Amendments, then add device-specific rules as you discover them.

**Mandatory starting set:**

| # | Title | What it governs |
|---|-------|-----------------|
| 1 | Domain Primitives | Which physical quantities all parameters must trace to |
| 2 | Stage Gate Order | The sequence and exit criteria for each stage |
| 3 | Toolchain Alignment | Active toolchain record, blocked toolchain record |
| 4 | Three-Strike Escalation | When to stop and ask the human |

**Common device-specific Amendments (from GaitSense example):**

| GaitSense Amendment | Generic form | When you need it |
|--------------------|-------------|-----------------|
| Signal Plot Mandate (Am. 11) | "Signal diagnostic plots are mandatory after any algorithm parameter change" | Any device where you need to visually verify signal integrity |
| Simulation is Hardware Proxy (Am. 5) | "Hardware deviations from simulation predictions are hardware problems, not firmware problems, until proven otherwise" | Any device with a validated simulation layer |
| Three Measurement Primitives (Am. 2) | [replace with your domain primitives Amendment] | Every device |
| Smoke Test Order (Am. 16) | Counter → sensor → algorithm USB → algorithm BLE | Any BLE device; adapt transport as needed |

---

### 5. Your hw-advisor input documents

The hw-advisor reads three things:
1. `docs/toolchain_config.md` — hardware, pin map, BOM fragments
2. Your field test results (UART logs, CSV exports, signal plots)
3. A device purpose statement: one paragraph describing what this device does and who depends on it

Write the device purpose statement now and keep it in `docs/device_purpose.md`. Every hw-advisor suggestion will be grounded in this statement — a suggestion that does not serve the stated purpose will not be made.

---

## The adaptation checklist

Before running `/session 0`:

- [ ] Domain primitives named and written down (not in any file yet — just on paper)
- [ ] Amendment 1 (Domain Primitives) drafted
- [ ] Amendment 2 (Stage Gate Order) drafted
- [ ] `/toolchain init` run — `docs/toolchain_config.md` created
- [ ] Amendment 3 (Toolchain Alignment) drafted referencing the config file
- [ ] Amendment 4 (Three-Strike Escalation) drafted
- [ ] `docs/device_purpose.md` written (one paragraph)
- [ ] All four Amendments ratified (you are the sole voting body at this stage — explicit ratification required)
- [ ] `docs/gaitsense_code/amendments.md` (or your equivalent) committed to git

Then run `/session 0`.

---

## Common adaptation mistakes

**Copying GaitSense Amendments verbatim.**  
GaitSense Amendments reference specific signal names (`gyr_y`, `acc_filt`), specific thresholds (30 dps), and specific terrain profiles. These are wrong for your device. Keep the *structure* of each Amendment; replace the *specifics* with your domain.

**Skipping domain primitive naming.**  
The most common failure. Engineers want to get to the firmware. The primitives feel abstract. Skipping them means your first threshold will be a guess, your second will be a different guess, and at Stage 3 you will have no way to explain why the device behaves the way it does.

**Treating the toolchain config as optional.**  
`toolchain_config.md` is not documentation — it is a gatekeeper. Every agent reads it before acting. If it is incomplete, agents will stop and ask you to fill it in. Fill it in before Stage 0.

**Ratifying too many Amendments at once.**  
The GaitSense project accumulated 17 Amendments 21 days of development. You do not need 17 Amendments before you start. You need four. The rest emerge from real problems encountered during development. An Amendment written speculatively without a failure mode it addresses is likely wrong.

---

## Example adaptation: smart home PIR occupancy sensor

**Domain primitives:**
```
1. Occupancy state (binary: occupied / unoccupied)
2. Occupancy transition latency (ms) — time from motion to state change
3. False-positive rate (%) — unoccupied room incorrectly classified as occupied
```

**Stage gate sequence:**
```
Stage 0: HIL Toolchain Lock (PIR + microcontroller + BLE/Zigbee)
Stage 1: Simulation — motion event model + PIR output model
Stage 2: Firmware Integration — occupancy FSM on dev kit, USB serial validation
Stage 3: Field Test — real room, varied occupancy patterns, log and replay
Stage 4: Integration — Home Assistant / Matter gateway / MQTT broker
```

**Amendment 1 — Domain Primitives:** (as above)  
**Amendment 2 — Stage Gate Order:** (as above sequence)  
**Amendment 3 — Toolchain Alignment:** Run `/toolchain init` with your PIR dev kit  
**Amendment 4 — Three-Strike Escalation:** Standard

**Device purpose statement:**
> The PIR occupancy sensor detects human presence in a room and reports it to a home automation hub. A false negative (occupied room reported as empty) causes unnecessary HVAC/lighting shutoff, wasting comfort. A false positive (empty room reported as occupied) wastes energy. Both errors have measurable costs; neither is acceptable beyond the validated threshold. The device must be correct more than 98% of the time under all lighting conditions the room will encounter.

This statement is what every hw-advisor suggestion will be grounded in.
