# Contributing to Crucible

Crucible is a framework, not a library. Contributions are governance improvements, not code additions. Understanding this distinction before contributing will save everyone time.

---

## What kinds of contributions are in scope

### 1. New device-domain examples

The reference implementation (GaitSense) covers one domain: gait biomechanics. Every domain has different physical primitives, different failure modes, and different validation requirements. A contribution that documents how Crucible was applied to a thermostat, a glucose monitor, a vibration sensor, or a smart irrigation controller is valuable precisely because it stresses the governance model in new ways and surfaces rules that need to be made more general.

**Format:** A new directory in `examples/<your_device>/` containing at minimum:
- `README.md` — device description, domain primitives, brief outcome summary
- `amendments.md` — the Amendments you ratified for this device
- `lessons.md` — what you had to adapt from the generic framework and why

### 2. Governance model improvements

If a governance rule in CONSTITUTION.md produced a *worse* hardware outcome than the alternative would have, that is a bug. File it. The same standard applies here as to all firmware bugs: cite the symptom, the root cause, and what physical evidence supports the proposed change.

This is a Bill. Use the Bill template in [docs/governance/bill_template.md](docs/governance/bill_template.md). A governance change without a Bill will not be merged.

### 3. Agent workflow improvements

If a slash command produced incorrect output, an agent took an action it was not supposed to, or a workflow step is ambiguous in a way that caused real problems — file an issue with the specific command, the actual output, and what the correct output should have been.

### 4. Documentation gaps

If a section of the documentation is missing for a use case that clearly falls within scope, file an issue. Be specific: what were you trying to do, what did you look for, what was missing?

---

## What is not in scope

- **New firmware libraries or algorithm implementations.** Crucible governs the process; it does not ship algorithms. Your algorithm lives in your project repo.
- **Build system integrations.** Crucible works with any build system. We do not maintain Arduino, PlatformIO, or Zephyr-specific tooling here.
- **Hardware designs.** We document pin maps and BOM patterns for reference. We do not accept schematic submissions or PCB layouts.
- **"Just add a flag" requests.** If the governance rule feels like overhead, that is worth discussing — but the discussion belongs in a Judicial Hearing, not a PR that quietly removes the gate.

---

## How to file a governance Bill (proposed change to CONSTITUTION.md or framework docs)

Every change to the governance model requires a Bill. The Bill format is in [docs/governance/bill_template.md](docs/governance/bill_template.md).

1. Open a GitHub Issue with the title `[BILL] <descriptive name>`
2. Paste the completed Bill template into the issue body
3. A maintainer assigns the issue to the Judicial Hearing process
4. Two positions are argued (for and against the proposed change)
5. The maintainer (Justice) rules based on physical/empirical evidence
6. If enacted: a PR is opened on a branch named `bill/<descriptive-name>`
7. The ruling is recorded in `docs/governance/case_law.md` before the PR merges

---

## How to submit a device example

1. Fork the repo
2. Create `examples/<your_device>/`
3. Write `README.md`, `amendments.md`, `lessons.md` (minimum)
4. Open a PR with title `[EXAMPLE] <device name>`
5. In the PR description, state your domain primitives and the outcome you validated against

**PR requirements:**
- Domain primitives must be named explicitly (Article I compliance)
- At least one test result must be documented with the physical evidence that validates it
- The toolchain must be registered (even a simple one — just show it was explicit)

---

## Commit message conventions

This framework uses git history as its audit trail. Commit messages matter.

```
<type>: <one-line description>

[body — optional, for non-obvious changes]

[Bill/Amendment/Case reference if applicable]
```

Types: `governance`, `docs`, `example`, `agent`, `fix`, `toolchain`

Examples:
```
governance: add Article I domain-primitive naming requirement to Bill template

docs: add smart home sensor example with thermal primitives

agent: update /hw-advisor to require physical evidence for all suggestions

fix: correct stage gate numbering in adoption guide (was 0-4, should be 0-4 with 0 first)

governance: ratify Amendment 3 (simulation field-data feedback loop)
[Bill: BILL-003, enacted 2026-04-10]
```

---

## Code of conduct

This project operates on the same principle as its governance model: evidence over opinion. Criticism is welcome when it is grounded in a specific hardware outcome that the current rules produce incorrectly. Criticism that cannot cite a physical consequence will not be acted on, but it will be acknowledged.

---

## Maintainer response time

This is an early public release. Issues will be responded to within 2 weeks. Bills require more time — the hearing process is not instant. If you have filed a Bill and not heard back in 3 weeks, ping the maintainer in the issue.
