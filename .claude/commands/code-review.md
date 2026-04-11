Invoke the code-reviewer agent to audit firmware and algorithm source for constitutional compliance.

Usage: /code-review [focus]

Focus (optional):
  article1   — Article I traceability only (every threshold traces to a domain primitive)
  filters    — filter chain coherence only (cutoffs, Nyquist, DC paths)
  fsm        — FSM structural integrity only (dead states, unreachable states, ambiguous transitions)
  units      — unit consistency only (caller/callee mismatches, undocumented conversions)
  amend7     — Amendment 7 calibration documentation only
  (none)     — full review across all categories

Constitutional grounding:
  Article I  — all thresholds must trace to domain primitives
  Amendment 1 — domain primitives are the evidence base for every finding
  Amendment 7 — calibration constants require derivation documentation

Reads before reviewing:
  docs/governance/amendments.md     — domain primitives and calibration amendments
  docs/device_context.md            — Signal Inventory (expected units and ranges)
  docs/toolchain_config.md          — active firmware repo and source file paths
  firmware source files             — from registered repo

Blocks stage gate if:
  Any ARTICLE-I-VIOLATION or FSM-DEAD-STATE is found.
  Each finding requires a Bill before /session can advance.

Now invoke the code-reviewer agent with focus "$ARGUMENTS".
If no focus given, run the full review.
If Amendment 1 has not been ratified, print:
  "Amendment 1 not ratified — domain primitives undefined.
   Run /spec collect before code review."
