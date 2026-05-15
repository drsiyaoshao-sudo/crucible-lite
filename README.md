# crucible-core

The Crucible Constitutional Governance Framework — Python infrastructure and project templates.

`crucible-core` provides the framework that individual project directories instantiate.
Each project (e.g. `crucible-cloth-grasp/`, `crucible-gait-v2/`) is a separate workspace
that ratifies its own Amendment 1 (domain primitives) and customizes the agent set for
its hardware target. The infrastructure code (`crucible/`) and the agent / command /
governance templates (`templates/`) are shared.

## Layout

```
crucible-core/
├── crucible/          ← Python infrastructure package (pip-installable)
│   ├── signal/        ← UART event parsing, plotting utilities
│   ├── transport/     ← BLE / serial transport helpers
│   ├── sim/           ← Renode simulation bridge
│   └── checks/        ← CI integrity checks
├── templates/         ← copy these into a new project directory
│   ├── CLAUDE.md
│   ├── CONSTITUTION.md
│   ├── .claude/
│   │   ├── agents/    ← 17 agent definitions
│   │   └── commands/  ← 10 slash commands
│   └── docs/
│       ├── governance/amendments.md
│       ├── governance/case_law.md
│       ├── device_context.md
│       └── toolchain_config.md
└── pyproject.toml
```

## Use

Install the Python infrastructure once:

```bash
cd ~/code/crucible-core
pip install -e .
```

Start a new project by copying the templates into a fresh directory:

```bash
mkdir ~/code/crucible-<project-name>
cp -r ~/code/crucible-core/templates/. ~/code/crucible-<project-name>/
cd ~/code/crucible-<project-name>
git init
```

Then run `/spec collect` to ratify the project-specific Amendment 1.

A `crucible new <project>` CLI is planned but not yet implemented.
