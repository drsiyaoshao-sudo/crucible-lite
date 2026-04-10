# Bill Template

Copy this template when proposing any change to simulation, firmware, software, or hardware. A Bill without physical evidence will be returned to the drafter — it cannot be debated.

---

```markdown
### BILL: [Descriptive name — what changes and why in one phrase]
Proposed by: [engineer name or agent]
Date drafted: [YYYY-MM-DD]
Change type: simulation / firmware / software / hardware / governance

---

**Problem statement:**
[What failure mode, gap, or measurement deficit does this address?
Cite the specific test result, signal measurement, field observation, or
simulation output that revealed the problem.
One paragraph maximum. If you cannot write this paragraph, the Bill is not ready.]

---

**Proposed change:**
[Exactly what changes — file names, function names, parameter values, component
substitutions, or governance rules. Be specific enough that someone who has never
seen this codebase could implement the change from this description alone.]

---

**Article / Amendment grounding:**
[Which Article or Amendment authorizes this change?
Which Amendment would be violated if this change is NOT made?
If neither Article applies directly, this is not a valid change — file an Amendment proposal instead.]

---

**Physical evidence:**
[Signal plots, UART output tables, unit test results, field measurement logs,
datasheet extracts, or simulation outputs that support the problem statement.
Attach files or reference their paths in the repo.

REQUIRED FORMAT — at least one of:
- A plot showing the failure mode (path: docs/.../plot.png)
- A UART log excerpt showing the incorrect output
- A unit test result showing failure under specific input conditions
- A field measurement table showing the deviation from expected

A Bill with no physical evidence is returned to the drafter.]

---

**Expected outcome:**
[What measurable improvement does this produce?
State in terms of your domain primitives — not in terms of code metrics.

Good: "Step detection on stair terrain increases from 0/100 to ≥98/100"
Good: "SI false-negative rate for 25% asymmetry decreases from 100% to 0%"
Bad:  "The algorithm will be more robust"
Bad:  "Performance improves"]

---

**Rollback plan:**
[If this change produces unexpected results on hardware, what is the rollback?
For firmware: git revert + reflash. For hardware BOM changes: keep the old part in stock.
If there is no rollback plan, state why and what the recovery procedure is.]

---

**Branch:**
[The git branch on which this change will be implemented if enacted.
Convention: bill/<short-descriptive-name>
Example: bill/pushoff-primary-step-detector]
```

---

## Guidance notes

### When a Bill is required vs. not

**Requires a Bill:**
- Any new algorithm parameter, threshold, or filter coefficient
- Any change to the firmware FSM (new state, modified transition condition)
- Any change to the simulation (new walker profile, modified signal generation)
- Any hardware change (component substitution, BOM revision, enclosure spec change)
- Any governance change (Amendment modification, new Standing Order)

**Does not require a Bill (Bureaucracy Standing Orders):**
- Running existing simulation scripts against existing profiles
- Generating signal diagnostic plots
- Installing or pinning library versions
- Committing validated work to git
- Running unit tests

### The "physical evidence" requirement in practice

The most common reason a Bill is returned: the evidence section says "it makes sense" or "I tested it and it worked" without attaching the test output.

Acceptable evidence examples:
- Screenshot of oscilloscope capture showing the failure mode
- UART log showing `step_count=0` on the stair profile
- Unit test output showing `SI=0.0% (expected >10%)` under pathological input
- Field measurement CSV showing cadence deviation of >15 spm from simulation prediction
- Datasheet note showing that the selected component has a lower operating range than the signal requires

Unacceptable evidence examples:
- "I believe this will fix the problem" (no evidence)
- "Similar projects use this approach" (no project-specific evidence)
- "The simulation passed" (simulation passing is the gate, not the evidence for the change)

### What happens after a Bill is filed

1. A maintainer (or the opposing attorney agent if using `/hear`) reviews the Bill for completeness
2. If incomplete (missing evidence, missing grounding): returned to drafter with specific gaps noted
3. If complete: debate opens — opposing attorney argues against the Bill
4. Justice (human) rules based on physical/empirical evidence
5. If enacted: Bill is implemented on the named branch, validated against the expected outcome
6. If validated: branch merges, Bill is archived in case law
7. If validation fails: Bill goes back to debate with the new failure as evidence
