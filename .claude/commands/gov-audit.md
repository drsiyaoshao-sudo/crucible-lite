Invoke the constitution-auditor agent to check the governance record for internal consistency.

Usage: /gov-audit [focus]

Focus (optional):
  amendments  — amendment health only (orphaned, superseded, stale, malformed)
  case-law    — case law health only (orphaned, frozen conflicts, missing fields, unimplemented)
  toolchain   — toolchain config vs Amendment 3 alignment only
  index       — amendment index accuracy only
  citations   — source code amendment citation checks only
  (none)      — full audit across all categories

Constitutional grounding:
  All Articles and Amendments — this agent audits the entire governance record
  Amendment 3 — toolchain alignment is a hard check
  Amendment 4 — three-strike violations may appear as unrecorded case law entries

Highest-severity finding:
  CONFLICT — a frozen precedent contradicts a live amendment.
  All CONFLICT findings require a /hear before the next stage gate.

Run before:
  /compact all (ensures compaction operates on a consistent record)
  Any stage gate where governance questions exist
  After ratifying new amendments (to catch index gaps)

Now invoke the constitution-auditor agent with focus "$ARGUMENTS".
If no focus given, run the full audit.
