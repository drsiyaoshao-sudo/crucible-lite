# Onboarding — Start Here

> **If you are Claude Code:** read [`CLAUDE.md`](CLAUDE.md) first. It tells you what governs your behaviour, where every file lives, and what you must not do without human approval.

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

Before running `/session 0`, you need four things:

### A. Python environment

```bash
pip install -r requirements.txt
```

This installs numpy, matplotlib, and bleak. Verify external tools are on your PATH:

```bash
which renode      # Renode simulation engine — https://renode.io
which pio         # PlatformIO — pip install platformio
which ninja       # Zephyr link step — brew install ninja
```

Missing tools produce warnings at session start, not errors — they are only needed for the paths that use them (Renode for Stage 1 firmware path, `pio`/`ninja` for Stage 0 firmware build).

### B. Your domain primitives (Article I compliance)

Write down — on paper is fine — the two or three physical quantities your device ultimately measures or responds to. These are not sensor readings. These are the things the person or system using your device actually cares about.

Examples:
- *Gait wearable:* Symmetry Index (%) derived from stance duration → traces to cadence and step length
- *Smart thermostat:* Room temperature error (°C) → traces to thermal mass and heat transfer
- *Air quality monitor:* PM2.5 concentration (μg/m³) → traces to particulate mass and sensor path length

If you cannot name these, stop. Read Article I again. Do not proceed past this step until you can name your primitives. Every threshold you set without naming a primitive is a guess.

### C. Your dev kit and toolchain

Know the answers to:
- What board are you using? (exact model, part number)
- What sensor(s) are on it or wired to it?
- How do you flash firmware? (UF2, J-Link, DFU, JTAG)
- How do you observe output? (USB serial, BLE, RTT, UART)

Run `/toolchain init` to record these formally. The toolchain janitor will walk you through each field interactively.

### D. A git repository

This framework uses git as the record of decisions. Every Bill enacted, every Amendment ratified, every case law ruling recorded — all of it is a commit. Without git history, you have no audit trail.

---

## Complete workflow map

### New project (one-time setup)

```
START NEW PROJECT
│
├─► pip install -r requirements.txt
│     Installs: numpy, matplotlib, bleak, pytest
│     Check: which renode  /  which pio  /  which ninja
│
├─► /spec collect ──────────────────────────────────────────────────────────────────────┐
│     │  Interview: device purpose, project target, pass/fail threshold,                │
│     │  signal inventory, domain primitives, operating envelope                        │
│     │  Writes: docs/device_context.md                                                 │
│     │  Drafts: Amendment 1 (Domain Primitives)                                        │
│     ▼                                                                                 │
│   Human ratifies Amendment 1?                                                         │
│     No ──► revise and re-ask                                                          │
│     Yes──► Amendment 1 written to docs/governance/amendments.md                      │
│            agent-updater ──► propagates primitives to code-reviewer,                 │
│                               sw-advisor, hw-advisor, bill-drafter                   │
│                                                                                       │
├─► /toolchain init ─────────────────────────────────────────────────────────────────┐  │
│     Register: board, FQBN, pins, libraries, repos                                  │  │
│     Fill in: ## Firmware UART Format (event markers, field names, session_end)     │  │
│     Writes: docs/toolchain_config.md (status: UNLOCKED)                            │  │
│                                                                                     │  │
├─► Ratify Amendments 2–4 + Amendment 11 ────────────────────────────────────────────┘  │
│     Amendment 2: Stage Gate Order                                                      │
│     Amendment 3: Toolchain Alignment                                                   │
│     Amendment 4: Three-Strike Rule                                                     │
│     Amendment 11: Scaffold Immutability                                                │
│     (remove PROPOSED prefix in amendments.md for each)                                 │
│                                                                                        │
└─► Ready for /session 0 ◄───────────────────────────────────────────────────────────┘
```

---

### Every session start (session initialisation)

```
/session [stage]
│
Step 0a — Spec check
│  Read docs/device_context.md
│  Placeholder text? ──► STOP: "Run /spec collect"
│  Populated? ──► print project target + threshold
│
Step 0b — Toolchain check
│  Read docs/toolchain_config.md
│  Missing? ──► STOP: "Run /toolchain init"
│  Stage 0 not yet closed AND status UNLOCKED? ──► allow (Stage 0 will lock it)
│  Stage 0 closed AND status UNLOCKED? ──► STOP: "Run /toolchain lock"
│  Blocked toolchain in active slot? ──► STOP: report conflict
│
Step 0c — Domain primitives check
│  Amendment 1 ratified? ──► print primitives
│  Not ratified? ──► STOP: "Run /spec collect"
│
Step 0d — Police check
│  New project (no commits, no case_law entries)? ──► skip, note "new project"
│  Has history? ──► audit last 10 commits vs case_law.md
│     VIOLATION found? ──► STOP: print violation report
│     WARNINGs? ──► print inline, session continues with acknowledgement required
│     CLEAN? ──► note "Police check: clean"
│
Step 0e — Package check
│  package-manager verifies Python dependencies
│  Any missing? ──► install, then continue
│
Print session header ──► show stage status, toolchain summary, commands
│
└─► Proceed to requested stage
```

---

### Per-stage flow (generic — applies to all stages)

```
ENTER STAGE N
│
├─ Prerequisite: Stage N-1 CLOSED (enforced by Amendment 2)
│
├─ Work loop ─────────────────────────────────────────────────────────┐
│   │                                                                  │
│   │  Agent executes procedure (simulation / firmware / field test)   │
│   │                                                                  │
│   │  Failure? ──► attempt 2 ──► attempt 3 ──► STOP (Amendment 4)   │
│   │              Three-strike: full report to human                  │
│   │              Human selects domain ──► /judicial bill if needed   │
│   │                                                                  │
│   │  Output deviates unexpectedly?                                   │
│   │    ──► /advisor sw (algorithm) or /advisor hw (hardware)         │
│   │    ──► findings → /judicial bill → /judicial hear → implement    │
│   │                                                                  │
│   │  Two agents produce conflicting results?                         │
│   │    ──► /judicial hear ──► ruling ──► case_law.md ──► agent-updater│
│   │                                                                  │
│   └─────────────────────────────────────────── back to work loop ───┘
│
├─ Exit criteria check (human confirms each criterion explicitly)
│
├─ JUSTICE GATE ──────────────────────────────────────────────────────┐
│   │                                                                  │
│   ├─ /review code ──► any ARTICLE-I-VIOLATION? ──► Bill required     │
│   ├─ /review doc  ──► any BLOCKER? ──► fix before gate               │
│   ├─ police       ──► any VIOLATION? ──► STOP, rule before gate      │
│   │                                                                  │
│   │  All clean? ──► human confirms gate criteria met                 │
│   │                                                                  │
│   ├─ stage-compactor ──► freeze case law, write handoff record        │
│   └─ Stage N marked CLOSED in toolchain_config.md                    │
│
└─► ENTER STAGE N+1
```

---

### Bill and Hearing flow (any time a change is needed)

```
Change needed (algorithm, firmware, hardware, simulation)
│
├─► /judicial bill "problem description"
│     bill-drafter reads: amendments.md, case_law.md,
│                          device_context.md, source files
│     Evidence gate: physical evidence must exist in record
│     Amendment gate: must name governing Article/Amendment
│     Outcome gate: expected improvement in domain primitive units
│     Scope gate: specific files/functions/values named
│        │
│        ├─ Gates pass ──► complete Bill output
│        └─ Gates fail ──► INCOMPLETE report: "run /regression or /plot evidence first"
│
├─► Human reviews Bill
│
├─► /judicial hear "Bill name" Position-A vs Position-B
│     judicial-clerk ──► COURTROOM READY
│     attorney-A + attorney-B argue in parallel
│     (optional) /plot evidence ──► generate requested evidence
│     (optional) Justice asks clarifying questions
│     Justice rules ──► prevailing position + physical basis
│     Prevailing attorney writes to case_law.md
│     agent-updater ──► if ruling changes agent scope: propose edits
│
└─► Implement on branch named in Bill ──► validate ──► merge
```

---

### Housekeeping (on demand, no stage gate required)

```
On demand ──► any of:

  /review code    ──► code-reviewer  ──► ARTICLE-I, FSM, filters, units
  /review doc     ──► doc-reviewer   ──► docs completeness, staleness, cross-refs
  /review gov     ──► constitution-auditor ──► amendment conflicts, orphaned entries
  /regression     ──► regression-runner ──► simulator-operator ──► plotter + uart-reader
  /advisor sw     ──► sw-advisor     ──► profile matrix analysis, algorithm suggestions
  /advisor hw     ──► hw-advisor     ──► BOM, pins, signal integrity, enclosure
  /compact        ──► stage-compactor or doc triage
  /plot profile   ──► plotter        ──► single profile diagnostic
  /plot evidence  ──► plotter        ──► hearing or validation evidence
```

---

### Agent orchestration map

```
Commands (human-invoked)          Agents (AI-executed)
─────────────────────────         ────────────────────────────────────────────

/session ─────────────────────►  police
                                  package-manager
                                  stage-compactor
                                  agent-updater (after Amendment ratification)

/judicial hear ───────────────►  judicial-clerk
                                  ├─► attorney-A
                                  ├─► attorney-B
                                  └─► (optional) plotter, simulator-operator
                                  agent-updater (after ruling)

/judicial bill ───────────────►  bill-drafter

/regression ──────────────────►  regression-runner
                                  └─► simulator-operator (per profile)
                                        ├─► [Path A] src/signals.py + src/algorithm.py
                                        ├─► [Path B] RenoneBridge → uart-reader
                                        ├─► compare_paths() if both available
                                        └─► plotter

/plot evidence ───────────────►  plotter
/plot profile ────────────────►  plotter

/review code ─────────────────►  code-reviewer
/review doc ──────────────────►  doc-reviewer
/review gov ──────────────────►  constitution-auditor
/advisor sw ──────────────────►  sw-advisor
/advisor hw ──────────────────►  hw-advisor
/compact ─────────────────────►  stage-compactor
/toolchain ───────────────────►  (direct file writes — no agent)
/spec ────────────────────────►  (direct file writes — no agent)

/gen-new-agent ───────────────►  (human executes — no agent by design)
```

---

## The five stages at a glance

| Stage | What happens | Entry condition |
|-------|-------------|-----------------|
| **0 — HIL Toolchain Lock** | Flash counter → IMU → algo USB → algo BLE. Prove the flash-run-observe loop works. Run `/toolchain scaffold` at end of Stage 0. | None — always first |
| **1 — Simulation** | Two paths: **A** (signal-only — pure Python, fast) and **B** (Renode — firmware in emulator). Both must pass before gate. | Stage 0 closed + scaffold done |
| **2 — Firmware Integration** | Port validated algorithm to dev kit. USB serial validation against Stage 1 Python model predictions. | Stage 1 closed |
| **3 — Field Test** | Real device, real conditions. Field data replayed through `src/analysis.py` — same parser as simulation. | Stage 2 closed |
| **4 — Host Integration** | Connect device to smart home hub, gateway, cloud, or other consumer system. | Stage 3 closed |

**Stage 0 failure is not a setback — it is the framework working.** A toolchain failure caught at Stage 0 takes 20 minutes to fix. The same failure caught at Stage 3 takes a week.

### Stage 1 in detail — two simulation paths

```
Path A — Signal-only (no firmware, seconds to run):
  src/signals.py::generate(profile, n_steps)   ← you write the physics model
         │
         ▼
  src/algorithm.py::run(samples)               ← you write the Python algorithm
         │
         ▼
  metrics dict  →  compare against pass/fail threshold

Path B — Renode (firmware in emulator, minutes to run):
  src/signals.py::generate(profile, n_steps)   ← same physics model
         │
         ▼
  RenoneBridge(elf_path).run(samples)          ← firmware runs in Renode
         │
         ▼
  src/analysis.py::PARSER.parse_log(text)      ← generated parser reads UART
         │
         ▼
  metrics dict  →  compare against pass/fail threshold

Path A+B — parity check:
  run both → compare_paths() → if they diverge, Python model OR firmware is wrong
  Justice decides which. Do not fix firmware until divergence is explained.
```

**What you must write before Stage 1:**
- `src/signals.py::generate()` — physics model that synthesizes sensor data per profile
- `src/algorithm.py::run()` — Python implementation of your algorithm (mirrors firmware logic)

These are stubbed by `/toolchain scaffold`. The rest of `src/` is generated automatically.

---

## How the agents work

Agents are Claude subagents launched by slash commands. They do not make decisions — they execute procedures and present evidence. The key commands:

| Command | When to use |
|---------|-------------|
| `/session [stage]` | Orchestrate a full stage or check session status |
| `/toolchain init` | Register hardware, FQBN, pins, libraries, UART format |
| `/toolchain scaffold` | Generate `src/` modules after filling in UART format |
| `/toolchain lock` | Stamp toolchain config as Stage 0 validated |
| `/judicial hear "<name>" A vs B` | Declare a judicial hearing when two rules conflict |
| `/regression [--signal-only\|--renode]` | Run full profile matrix; both paths if neither flag given |
| `/advisor hw` | Get design suggestions grounded in your test results |
| `/advisor sw` | Get algorithm suggestions grounded in simulation profiles |
| `/plot profile <profile>` | Generate a signal diagnostic plot |
| `/plot evidence <type>` | Collect evidence during a hearing or validation run |

Agents read `docs/toolchain_config.md` before taking any toolchain-dependent action. A blocked toolchain produces a hard stop with the reason — the agent does not work around it.

---

## The feedback loop

The most important thing Crucible does that conventional CI/CD does not:

```
  Field test data ──► src/analysis.py ──► Simulation ──► Algorithm refinement ──► Firmware
                       (same parser as                                                  │
                        Renode path)                                                    ▼
                                                             Field test ◄── HIL validation
```

When your field test produces a result that deviates from your simulation prediction, you do not immediately fix the firmware. You replay the field data through `src/analysis.py` — the same parser the simulation uses — and feed it into `src/algorithm.py`. If the Python model also deviates, the physics model is wrong — update it. If the Python model matches the field data but the firmware does not, the porting is wrong — fix the port. If neither matches, the signal model is wrong — update `src/signals.py`.

This three-way diagnostic (field data vs Python model vs firmware) is only possible because the simulation, field data, and firmware all share the same `src/analysis.py` parser. That is why `/toolchain scaffold` generates it once and Amendment 11 freezes it — changing the parser mid-project destroys the traceability chain.

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

**5. Letting the Python model and firmware diverge silently.**  
The signal-only path (Path A) and the Renode path (Path B) must agree within tolerance before Stage 1 closes. If you skip the parity check, you will hit Stage 2 or Stage 3 with firmware that disagrees with your simulation — and you will not know which is correct. The compare_paths() report at Stage 1 gate is the only moment where you can resolve this before the hardware is in your hands.

**6. Implementing `src/signals.py` as noise + a plausible mean.**  
The signal generator is your physics model. A synthetic signal that looks right but has the wrong frequency content, wrong noise floor, or wrong transient shape will pass simulation but fail in the field. Derive every parameter in `generate()` from a domain primitive with a source citation — the same discipline Article I requires in firmware.

---

## Getting help and contributing

This framework is in early public release. Criticism is invited. File a GitHub Issue if:
- A governance rule causes a worse hardware outcome than violating it would
- The agent workflow fails in a way the documentation does not address
- You have adopted this for a device type not covered by the examples and want to contribute a case study

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full process.
