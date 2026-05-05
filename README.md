# Crucible-Lite — Hardware CI/CD Framework for Embedded Design

**Crucible-Lite** is an agent-assisted framework for bringing CI/CD discipline to hardware product development. It is designed for **system integrators** — engineers who design circuits, choose sensors, write firmware, and need a structured, repeatable path from algorithm idea to deployed device.

It is not a build tool. It is not a hardware description language. It is a **governance model** that turns human decisions into traceable, physical-evidence-backed records — the same way good software CI/CD turns code changes into auditable commit histories.

---

## The Core Problem It Solves

Hardware development fails at predictable points:

1. **Algorithm validated in Python, broken on device.** Nobody connected the simulation to the hardware in a structured way. The algorithm worked in NumPy but the firmware used integer math.

2. **Toolchain switched mid-project.** Someone found a better library at Stage 3. Two weeks of validated work was silently invalidated.

3. **"It worked yesterday."** No traceable record of what changed, when, and why. The last known-good state is a mystery.

4. **Decisions made from intuition.** A threshold gets changed because it "looked about right." No physical evidence, no record.

5. **Hardware used as a debugging tool.** The board is flashed 40 times before the algorithm is correct. Each flash is a context switch, a potential brick, and a lost afternoon.

Crucible addresses all five with a single mechanism: **every change that touches algorithm, firmware, hardware, or toolchain must be backed by physical evidence and approved by a human before it goes in.**

---

## The Two Articles

Everything in Crucible derives from two unconditional rules:

### Article I — Physics First

No parameter, threshold, gate, or algorithm decision may be defined unless it traces to a first-order physically measurable quantity dictates the system charateristics of your device trying to measure or use in the host functions, e.g., a flow rate meter can infer the porosity of a filter.

*For a gait wearable:* all parameters trace to cadence, step length, or vertical oscillation.  
*For a thermostat:* all parameters trace to thermal mass, heat transfer coefficient, or occupancy signal.  
*For a glucose monitor:* all parameters trace to optical absorption coefficient and sample path length.

IMU readings, ADC counts, and filter outputs are *measurements* of physical quantities — not the quantities themselves. An engineer who sets a threshold by fitting it to data without naming the physical quantity it represents has guessed, not derived.

**This Article is unconditional.** A parameter that cannot be traced to a measurable physical quantity is not a parameter — it is a guess. Guesses are not permitted in Crucible.

### Article II — Human in the Loop

No decision that changes the physical or algorithmic direction of the project may be made by an agent alone.

**An agent executes. A human decides.**

The boundary: any action whose consequence cannot be fully reversed by a single `git revert` requires human approval before execution. Flashing firmware to hardware is the limiting case — it is irreversible within a session.

Evidence — signal plots, UART output, test results, field measurements — is the only valid input to a human decision. Argument from intuition, prior success, or expediency is not valid.

**This Article is unconditional.**

---

## The Pipeline

```
 ┌─────────────────────────────────────────────────────────────────┐
 │                    CRUCIBLE PIPELINE                            │
 │                                                                 │
 │  Stage 0 ── HIL Toolchain Lock  ◄─── START HERE (always)       │
 │                │                                                │
 │                ▼                                                │
 │  Stage 1 ── Simulation          ◄─── also fed by field data ┐  │
 │                │                                             │  │
 │                ▼                                             │  │
 │  Stage 2 ── Firmware Integration on Dev Kit                  │  │
 │                │                                             │  │
 │                ▼                                             │  │
 │  Stage 3 ── Field Test          ──── data captured ──────────┘  │
 │                │                                                │
 │                ▼                                                │
 │  Stage 4 ── Host Integration    (smart home, gateway, cloud)    │
 └─────────────────────────────────────────────────────────────────┘
```

**Stage 0 is the first gate, not the last.** Toolchain failures (wrong board variant, USB cable, BLE scan name, UF2 offset) discovered at Stage 3 cost days. Discovered at Stage 0, they cost 20 minutes.

**The simulation loop is bidirectional.** Stage 1 starts from a physics model of your device domain. After Stage 3 field tests, real measurement data replays back through simulation — this keeps the physics-first principle intact as the device encounters real-world variance. Simulation is never frozen; it evolves with evidence.

---

## What Crucible Is Not

- **Not a build system.** It doesn't replace Make, CMake, PlatformIO, or Arduino CLI. It governs *which* of those tools is active and *why*.
- **Not a CI server.** GitHub Actions, Buildkite, and Jenkins run pipelines. Crucible defines what those pipelines must enforce.
- **Not an algorithm library.** It provides no signal processing code. It provides the governance structure that validates whatever signal processing your device needs.
- **Not a hardware design tool.** It reads your existing BOM and schematic and provides grounded suggestions from test results. It does not design circuits.

---

## Who It Is For

**System integrators** building connected hardware: wearables, smart home sensors, industrial monitors, medical-adjacent devices. Teams of 1–10 engineers who cannot afford a dedicated QA process but cannot afford to ship wrong data either.

You bring: the circuit, the BOM, the algorithm idea, the dev kit.  
Crucible brings: the governance structure, the agent workflow, the feedback loop, and the paper trail.

---

## Getting Started

1. Read [ONBOARDING.md](ONBOARDING.md) — 15 minutes, establishes reading order
2. Read [CONSTITUTION.md](CONSTITUTION.md) — the full governance model (Articles + Amendment process)
3. Fork this repo and run `/toolchain init` to register your hardware
4. Run `/session 0` — HIL toolchain lock for your dev kit
5. File your first Bill when you want to change anything

**Reference implementation:** [crucible-comfort](https://github.com/rturcottetardif/crucible-comfort) is a complete implementation of Crucible on a real device — thermal comfort wearable on nRF52840 + BLE. All stages are documented with real results. See [examples/crucible_comfort/](examples/crucible_comfort/README.md) for a guided tour of what to look at first.

---

## The Name

A crucible is the vessel in which materials are subjected to extreme conditions to test and refine their properties. The same physics-first, evidence-only principle that governs metallurgy governs this framework. You do not declare a material pure because it looks right. You measure it.
