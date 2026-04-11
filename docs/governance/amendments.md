# Crucible Amendments

All amendments derive from Article I (Signal First) and/or Article II (Human in the Loop)
in CONSTITUTION.md. The governing Articles are unconditional and cannot be amended.

Amendment 1 is always the Domain Primitives amendment — written by `/spec collect` for
each specific project. Amendments 2–4 are mandatory framework amendments ratified here.
Amendments 5 onwards are domain-agnostic operational amendments included as defaults;
ratify them by removing the PROPOSED prefix. Project-specific amendments (signal plot
mandate, statistical derivation rules, etc.) are added after Amendment 1 is ratified.

---

## Mandatory Framework Amendments

These three must be ratified before /session 0 on any Crucible project.
They are pre-written here — read, confirm they are correct for your project,
then remove the PROPOSED prefix to ratify.

---

### Amendment 2 — Stage Gate Order
*Traces to: Article I + II*
*Status: PROPOSED — ratify by removing this line*

Development proceeds through exactly these stages in order, and no stage begins
until the previous stage's exit criteria are explicitly confirmed by the human:

  Spec Gate → Stage 0 (HIL Toolchain Lock) → Stage 1 (Simulation) →
  Stage 2 (Firmware Integration) → Stage 3 (Field Test) → Stage 4 (Host Integration)

An agent must not begin Stage N+1 work while Stage N has any open failure, even one
that appears unrelated to the next stage's work. Each stage's errors become
exponentially more expensive to fix in later stages. Hardware is a validation tool,
not a debugging tool.

**Exit criteria for each stage are defined in `/session`.**
**Stage closeout is executed by `stage-compactor`.**

---

### Amendment 3 — Toolchain Alignment
*Traces to: Article II*
*Status: PROPOSED — ratify by removing this line*

Every agent working on this project must operate within the toolchain that is currently
active and recorded in `docs/toolchain_config.md`. No agent may introduce a new
toolchain, framework, or build system without a Bill enacted through the Legislative
Process. Switching toolchains mid-stage is not permitted — it requires a new stage gate.

The active toolchain record in `docs/toolchain_config.md` is the single source of truth
for all build, flash, and test operations. An agent that silently switches from the active
toolchain to a different one violates Article II regardless of whether the output compiles.

A blocked toolchain may only be re-activated by explicit human decision at a stage gate,
recorded in toolchain_config.md with a date and reason.

---

### Amendment 4 — Three-Strike Escalation Rule
*Traces to: Article II*
*Status: PROPOSED — ratify by removing this line*

If a simulation, unit test, hardware smoke test, or iterative fix process fails to meet
exit criteria within three attempts, the agent must stop, report the full status to the
human, and wait for a human determination before any further action.

The three-strike report must include:
  1. What was attempted on each of the three tries
  2. What was observed on each attempt (exact output, not a summary)
  3. What the agent does not know — the open question that a human must answer

The agent must not propose a fourth approach without explicit human direction.

**Rationale:** Continuing past three failures compounds work debt and masks the root
cause. Three-strike reports also function as input to Judicial Hearings when the
failure pattern suggests a design conflict rather than a bug.

---

## Domain-Agnostic Operational Amendments

Ratify these as they become relevant to your project. Remove the PROPOSED prefix
after explicit human ratification.

---

### Amendment 5 — Simulation is the Hardware Proxy
*Traces to: Article I + II*
*Status: PROPOSED — ratify when Stage 1 begins*

If something cannot be tested in simulation, a simulation test must be written first.
Hardware results that deviate from simulation predictions are evidence of a hardware or
mounting problem — not a firmware problem — unless the corresponding simulation test
was never written.

The handoff document (`docs/governance/handoff.md`) is the binding prediction set
against which hardware results are compared at each stage gate.

---

### Amendment 6 — Signal Plot Mandate
*Traces to: Article I + II*
*Status: PROPOSED — ratify when Stage 1 begins*

After any change to the project's signal model or any filter coefficient in firmware
source, an agent must generate a signal plot, save it to `docs/plots/`, and wait for
human visual confirmation before proceeding.

Signal plots are the primary mechanism for catching silent model errors that pass
numerical tests. Human visual review of physical plausibility cannot be substituted
by a numerical test. A metric value that looks correct can be produced by a physically
implausible signal.

**Invoked by:** `/plot-profile` and `/plot-evidence signal`

---

### Amendment 7 — Calibration Discipline
*Traces to: Article I*
*Status: PROPOSED — ratify before any threshold is introduced in firmware*

One new calibration constant may be introduced per algorithmic iteration. Every
calibration constant must be documented with its physical derivation before the
session ends.

A constant derived from a physical measurement predicts its own correct value when
the operating conditions change. A tuned constant (fitted to observed data without
physical derivation) requires re-tuning at every hardware or population change.

Documentation format (inline in firmware source):
```
/* CONSTANT_NAME — derived from [domain primitive].
 * Physical derivation: [formula or measurement].
 * Value: [N] [unit].
 * Traces to: Amendment 1 primitive [N]. */
```

---

### Amendment 8 — Algorithm Search Honesty
*Traces to: Article I + II*
*Status: PROPOSED — ratify when algorithm work begins*

When an algorithm fix domain has been exhausted without resolution, the agent must
explicitly state:
  - Which domain was searched
  - Why it yielded no result
  - No more than three alternative domains

The human selects exactly one alternative. The hardware iteration option (sensor
repositioning, BOM change, enclosure change) must always remain on the list —
it is never automatically eliminated.

**Rationale:** An agent that continues searching within an exhausted domain without
disclosure violates Article II. Switching domains unilaterally violates the same
Article. The cost of an algorithm fix may exceed the cost of a hardware change —
the human must be in the decision.

---

### Amendment 9 — Hardware Optimization Transparency
*Traces to: Article II*
*Status: PROPOSED — ratify when algorithm work begins*

When an agent identifies that an algorithm change enables lower-cost hardware
(fewer sensors, lower-spec component, simpler enclosure), it must explicitly state
this and the physical reasoning before proceeding. The human decides whether to
optimize.

BOM changes have supply chain, procurement, and schedule consequences an agent
does not possess. All BOM or hardware specification changes require explicit human
authorization and must be recorded in `docs/device_context.md` BOM section.

---

### Amendment 10 — Interim Results and Decision Logging
*Traces to: Article II*
*Status: PROPOSED — ratify before any multi-step iterative session*

During any iterative build-debug process, intermediate results must be printed to
the terminal for human review. The agent waits for a human determination before
proposing the next action.

The specific human decision must be recorded in `docs/governance/case_law.md` or
the relevant stage record before the session ends.

**Rationale:** Prevents the most common failure mode in agentic development — an
agent runs five sub-steps autonomously, encounters an anomaly in step 2, compensates
in step 3, and delivers a result in step 5 that looks correct but carries a hidden
assumption no human ever approved.

---

## Project-Specific Amendments

Amendment 1 (Domain Primitives) is written here by `/spec collect` after human
ratification. Subsequent project-specific amendments are added below Amendment 1
as the project evolves.

> [Amendment 1 will appear here after /spec collect is run and ratified.]

---

## Amendment Index

| # | Title | Status | Traces to |
|---|-------|--------|-----------|
| 1 | Domain Primitives | NOT YET RATIFIED — run /spec collect | Article I |
| 2 | Stage Gate Order | PROPOSED | Article I + II |
| 3 | Toolchain Alignment | PROPOSED | Article II |
| 4 | Three-Strike Escalation Rule | PROPOSED | Article II |
| 5 | Simulation is the Hardware Proxy | PROPOSED | Article I + II |
| 6 | Signal Plot Mandate | PROPOSED | Article I + II |
| 7 | Calibration Discipline | PROPOSED | Article I |
| 8 | Algorithm Search Honesty | PROPOSED | Article I + II |
| 9 | Hardware Optimization Transparency | PROPOSED | Article II |
| 10 | Interim Results and Decision Logging | PROPOSED | Article II |
