Invoke the doc-reviewer agent to audit docs/ for completeness, staleness, and cross-document consistency.

Usage: /doc-review [focus]

Focus (optional):
  device     — docs/device_context.md only
  toolchain  — docs/toolchain_config.md only
  governance — amendments.md and case_law.md only
  cross      — cross-document consistency checks only
  (none)     — full review across all docs

Constitutional grounding:
  Amendment 2 — each closed stage must have test data recorded
  Amendment 3 — toolchain_config.md must be consistent with active toolchain record
  Amendment 6 — closed Stage 1 requires signal plots recorded in Test Results

Severity levels:
  BLOCKER  — blocks /session stage advance
  WARNING  — should fix before gate, does not hard-block
  INFO     — completeness gap, low urgency

Run before:
  Any stage gate (/session status)
  /compact (ensures compaction has complete source material)
  /hear (attorneys need a complete evidence base)

Now invoke the doc-reviewer agent with focus "$ARGUMENTS".
If no focus given, run the full review.
