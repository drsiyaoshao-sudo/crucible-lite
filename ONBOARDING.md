# Onboarding — Start Here

**Estimated time:** 30 minutes to first running session.

---

## What you are looking at

Crucible is a governance framework for hardware development. It is not a library or a build tool. It is a set of rules, agent workflows, and document templates that enforce the same discipline in hardware development that good CI/CD enforces in software development.

The most important thing to understand before touching anything:

> **An agent executes. A human decides.**  
> Every agent in this framework does work — builds, simulates, plots, tests — but every decision about direction, threshold, or design is made by you.

---

## Reading order

Read these in order. Each takes 5–10 minutes.

### 1. This file (you are here)
Establishes what to read and why.

### 2. [README.md](README.md)
The elevator pitch: what Crucible solves, the five failure modes, the two Articles, the pipeline map. Understand the problem before the solution.

### 3. [CONSTITUTION.md](CONSTITUTION.md)
The governance model in full. Pay particular attention to:
- Article I (Signal First) — you will need to name your domain primitives before writing any code
- The distinction between a **Bill** (a change proposal), a **Hearing** (a conflict resolution), and an **Amendment** (a new governance rule)
- The hw-advisor role — this is what gives you design feedback grounded in test results

### 4. [docs/governance/adoption_guide.md](docs/governance/adoption_guide.md)
How to fork and adapt this framework for your specific device. Covers which parts are universal, which parts are device-specific, and what you must write before your first session.

### 5. [docs/testing/hil_testing_guide.md](docs/testing/hil_testing_guide.md)
The HIL-first principle in detail. Read this before you do anything with hardware. Understanding *why* Stage 0 runs first will save you significant debugging time.

---

## First session checklist

Before running `/session 0`, you need three things:

### A. Your domain primitives (Article I compliance)

Write down — on paper is fine — the two or three physical quantities your device ultimately measures or responds to. These are not sensor readings. These are the things the person or system using your device actually cares about.

Examples:
- *Gait wearable:* Symmetry Index (%) derived from stance duration → traces to cadence and step length
- *Smart thermostat:* Room temperature error (°C) → traces to thermal mass and heat transfer
- *Air quality monitor:* PM2.5 concentration (μg/m³) → traces to particulate mass and sensor path length

If you cannot name these, stop. Read Article I again. Do not proceed past this step until you can name your primitives. Every threshold you set without naming a primitive is a guess.

### B. Your dev kit and toolchain

Know the answers to:
- What board are you using? (exact model, part number)
- What sensor(s) are on it or wired to it?
- How do you flash firmware? (UF2, J-Link, DFU, JTAG)
- How do you observe output? (USB serial, BLE, RTT, UART)

Run `/toolchain init` to record these formally. The toolchain janitor will walk you through each field interactively.

### C. A git repository

This framework uses git as the record of decisions. Every Bill enacted, every Amendment ratified, every case law ruling recorded — all of it is a commit. Without git history, you have no audit trail.

---

## The five stages at a glance

| Stage | What happens | Entry condition |
|-------|-------------|-----------------|
| **0 — HIL Toolchain Lock** | Flash counter → IMU → algo USB → algo BLE. Prove the flash-run-observe loop works. | None — always first |
| **1 — Simulation** | Validate algorithm on physics model. Also accepts field measurement data as input. | Stage 0 closed |
| **2 — Firmware Integration** | Port validated algorithm to dev kit. USB serial validation. | Stage 1 closed |
| **3 — Field Test** | Real device, real conditions. Data captured and fed back to Stage 1 simulation. | Stage 2 closed |
| **4 — Host Integration** | Connect device to smart home hub, gateway, cloud, or other consumer system. | Stage 3 closed |

**Stage 0 failure is not a setback — it is the framework working.** A toolchain failure caught at Stage 0 takes 20 minutes to fix. The same failure caught at Stage 3 takes a week.

---

## How the agents work

Agents are Claude subagents launched by slash commands. They do not make decisions — they execute procedures and present evidence. The key commands:

| Command | When to use |
|---------|-------------|
| `/session [stage]` | Orchestrate a full stage or check session status |
| `/toolchain <subcommand>` | Register hardware, libraries, repos; run validation |
| `/hear "<name>" A vs B` | Declare a judicial hearing when two rules conflict |
| `/hw-advisor` | Get design suggestions grounded in your test results |
| `/plot-profile <profile>` | Generate a signal diagnostic plot |
| `/plot-evidence <type>` | Collect evidence during a hearing or validation run |

Agents read `docs/toolchain_config.md` before taking any toolchain-dependent action. A blocked toolchain produces a hard stop with the reason — the agent does not work around it.

---

## The feedback loop

The most important thing Crucible does that conventional CI/CD does not:

```
  Field test data ──► Simulation ──► Algorithm refinement ──► Firmware
                                                                  │
                                                                  ▼
                                              Field test ◄── HIL validation
```

When your field test produces a result that deviates from your simulation prediction, you do not immediately fix the firmware. You replay the field data through the simulation first. If the simulation also deviates, the physics model is wrong — update it. If the simulation matches the field data but the firmware does not, the porting is wrong — fix the port. This distinction is not possible without the simulation layer, which is why Crucible keeps it alive through all five stages.

---

## Common mistakes (learn from the reference implementation)

**1. Using hardware as a debugging tool.**  
The GaitSense project flashed the board 40+ times before establishing Crucible discipline. After establishing it, the algorithm was correct before the first flash. Stage 0 is cheap. Stage 3 with a broken algorithm is not.

**2. Switching toolchains under pressure.**  
Zephyr was blocked after three failed attempts to read the IMU. The temptation was to "just try one more thing." The three-strike rule prevented this. The switch to Arduino was clean, documented, and traceable. Two weeks later, nobody had to ask "why are we using Arduino?"

**3. Setting thresholds by feel.**  
The 30 dps push-off threshold in GaitSense is not a round number chosen because it looked right. It is derived: minimum push-off angular velocity at 0.1 m/s walking speed ≈ 100 dps; early-stance rebound artifact ≈ 9–14 dps; 30 dps gives 3× margin above noise with 3× margin below minimum signal. That derivation is in the amendment record. A threshold without a derivation is a guess.

**4. Skipping the pathological test.**  
BUG-013 in GaitSense: the SI computation was silently zeroed by an FPU emulator bug. Every healthy walker test passed. Only the pathological walker test (where the correct answer is non-zero) caught it. For any clinical or safety-adjacent device: always test under conditions where the correct answer is non-zero.

---

## Getting help and contributing

This framework is in early public release. Criticism is invited. File a GitHub Issue if:
- A governance rule causes a worse hardware outcome than violating it would
- The agent workflow fails in a way the documentation does not address
- You have adopted this for a device type not covered by the examples and want to contribute a case study

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full process.
