Invoke the bill-drafter agent to produce a complete, debate-ready Bill from a problem description and evidence.

Usage: /draft-bill <problem description>

Arguments:
  A natural-language description of the change needed and why.
  The more specific the description, the better the Bill.

Examples:
  /draft-bill step detection fails on stairs — acc_filt peak delayed by 80ms under sigmoid loading
  /draft-bill replace soft TPU enclosure — heel-strike transient attenuated below detection threshold
  /draft-bill HP filter cutoff too low — gravity component reaching algorithm input

What bill-drafter does:
  1. Reads amendments, case law, device_context.md, and relevant source files
  2. Checks evidence gates (physical evidence must exist in the record)
  3. Identifies the correct amendment grounding
  4. Verifies the proposed change is specific and measurable
  5. Outputs a complete Bill or an INCOMPLETE report explaining what evidence is missing

Bill quality gates (all must pass before a Bill is output):
  Evidence gate    — physical evidence must exist in device_context.md or this session
  Amendment gate   — an Article or Amendment must authorise the change
  Outcome gate     — expected improvement must name a domain primitive and unit
  Scope gate       — proposed change must name specific files, functions, or values

After bill-drafter outputs the Bill:
  1. Review the Bill with the Justice
  2. Run /hear "[Bill name]" to open debate
  3. After ruling, implement on the branch named in the Bill

Constitutional grounding:
  Article I  — Bill must trace to a domain primitive
  Article II — Bills are proposed; the Justice enacts
  Amendment 4 — three consecutive failures should trigger a Bill, not a fourth attempt

Now invoke the bill-drafter agent with problem description: "$ARGUMENTS"
If no description given, print this usage and stop.
