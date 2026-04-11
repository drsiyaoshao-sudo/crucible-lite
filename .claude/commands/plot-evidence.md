Invoke the plotter agent to collect and present evidence during a Judicial Hearing or simulation validation run.

Usage: /plot-evidence <type> [args]

Evidence types:
  signal   <profile> [mode]     — signal diagnostic plot for one profile
  uart     <log_path>           — UART session output from a Renode log file
  sim      <profile> [mode]     — full simulation evidence: UART + signal plot combined

Arguments:
  profile:  a profile name defined in the project's signal model
            (read from docs/device_context.md Signal Inventory or docs/toolchain_config.md)
  mode:     optional variant (e.g. nominal, worst-case, pathological — project-specific)
  log_path: path to UART log file (e.g. simulator/logs/renode_<profile>.log)

Examples:
  /plot-evidence signal nominal
  /plot-evidence signal worst-case pathological
  /plot-evidence uart simulator/logs/renode_nominal.log
  /plot-evidence sim nominal
  /plot-evidence sim worst-case pathological

Constitutional grounding:
  Signal Plot Amendment (check docs/governance/amendments.md for current number):
    signal plots mandatory after any signal model or algorithm parameter change
  Bureaucracy Signal Plotting Standing Order: no Bill or hearing required

Now invoke the plotter agent with evidence type and arguments: "$ARGUMENTS"
Parse the first word as the evidence type. Pass remaining words as the target (profile or log_path).
If no type is given, print the usage above and stop.

Before invoking the plotter, read docs/device_context.md Signal Inventory to confirm
the requested profile name exists. If it does not, stop and print:
  "Profile '<name>' not found in Signal Inventory. Valid profiles are: [list from device_context.md]
   Add it via /spec signals if this is a new operating condition."
