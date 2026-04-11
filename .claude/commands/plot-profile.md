Invoke the plotter agent to generate a signal diagnostic plot for a single signal profile.

Usage: /plot-profile <profile> [mode]

Arguments:
- profile: a profile name defined in the project's signal model (read from docs/device_context.md Signal Inventory or docs/toolchain_config.md)
- mode: optional variant (e.g. nominal, worst-case, pathological — project-specific)

What this does:
1. Dispatches the plotter agent for the named profile only
2. Plotter reads the project's signal model, generates the signal sequence, applies firmware-matched filters
3. Saves plot to docs/plots/<profile>_signal_check.png
4. Prints data table to stdout (peak values, key timestamps, threshold crossings)
5. If CRUCIBLE_DEMO=1 is set, opens the plot in Preview automatically

Constitutional grounding:
- Signal Plot Amendment (check docs/governance/amendments.md for current number): mandatory after any signal model or algorithm parameter change
- Bureaucracy Signal Plotting Standing Order: no Bill or hearing required

The plotter agent does NOT:
- Modify source code or algorithm parameters
- Interpret whether the signal is correct (that is the Justice's role)
- Run simulations or build firmware
- Propose fixes based on what it observes

Example invocations:
  /plot-profile nominal
  /plot-profile worst-case
  /plot-profile worst-case pathological

Now invoke the plotter agent with the profile "$ARGUMENTS".
Parse the first word as the profile name and the second word (if present) as the mode.
If no profile is given, print the usage above and stop — do not guess a profile.

The plotter agent must:
1. Read docs/toolchain_config.md to locate the firmware repo and signal model path
2. Read docs/device_context.md Signal Inventory to confirm the profile name is valid
3. Call the project's signal model to generate the signal sequence for the named profile
4. Apply the filter chain defined in the project's algorithm source
5. Plot using crucible.signal.plot — do NOT write inline plot code
