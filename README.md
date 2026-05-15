# crucible-core

The Crucible Constitutional Governance Framework — Python infrastructure, project
templates, and the `crucible` CLI.

`crucible-core` provides a reusable framework that each project workspace instantiates
into its own directory. The infrastructure code (`crucible/`) and the agent / command /
governance templates (`templates/`) are shared; per-project state (ratified Amendment 1,
populated device_context, customised agents) lives in the project workspace, not here.

## Layout

```
crucible-core/
├── crucible/                 ← Python infrastructure package (pip-installable)
│   ├── cli.py                ← `crucible init` CLI
│   ├── signal/               ← UART event parsing, plotting utilities
│   ├── transport/            ← BLE / serial transport helpers
│   ├── sim/                  ← Renode simulation bridge
│   └── checks/               ← CI integrity checks
├── templates/                ← copied into project workspaces by `crucible init`
│   ├── CLAUDE.md
│   ├── CONSTITUTION.md
│   ├── .claude/
│   │   ├── agents/           ← 17 agent definitions
│   │   ├── commands/         ← 10 slash commands
│   │   └── hooks/            ← Article I PreToolUse hook
│   ├── .githooks/            ← Article I git pre-commit hook
│   └── docs/
│       ├── governance/amendments.md
│       ├── governance/case_law.md
│       ├── device_context.md
│       └── toolchain_config.md
└── pyproject.toml
```

## Install

```bash
git clone <crucible-core-remote> ~/crucible/core
pipx install -e ~/crucible/core
```

`pipx install -e` creates an isolated venv for the `crucible` CLI and links it on
PATH. Editable install means `git pull` in `~/crucible/core/` is picked up
automatically — no re-install needed.

Verify: `crucible --help`.

## Start (or adopt) a project

```bash
cd /path/to/your/project       # any directory you want Crucible governance applied to
crucible init                   # copies templates here; launches Claude Code
```

`crucible init` does, in order:

1. **Copy `templates/` into the current directory** (CLAUDE.md, CONSTITUTION.md,
   `.claude/`, `.githooks/`, `docs/governance/`, `docs/device_context.md`,
   `docs/toolchain_config.md`).
2. **Merge an existing `CLAUDE.md`** if one is present in the directory. The
   Crucible template content is placed first, then the existing content,
   separated by marker comments. In your first Claude Code session, ask the
   `doc-reviewer` agent to audit the merged file and propose a consolidated
   version.
3. **Set up the Claude Code memory symlink** so per-project auto-memory lives
   in `<project>/docs/memory/`.
4. **Create `~/crucible/<basename>` → `<project-dir>`** as a discovery symlink.
   `ls ~/crucible/` then shows every Crucible-adopted project.
5. **Initialise git** if `.git/` is absent, and activate the Article I pre-commit
   hook (`git config core.hooksPath .githooks`). Commit the new files.
6. **Exec into Claude Code** if `claude` is on PATH.

Flags:
- `--no-git` — skip git init / staging / commit / hook activation
- `--no-claude` — do not launch Claude Code; print the next-step hint instead
- `--force` — overwrite existing files that conflict with the templates
  (CLAUDE.md is merged automatically regardless of this flag)

Once Claude Code is open, the typical first-session sequence is:
1. `/spec collect` — ratify project-specific Amendment 1 (domain primitives)
2. Run `agent-updater` to propagate Amendment 1 into the agent set
3. `/toolchain init` — register hardware, pins, libraries, blocked toolchains
4. `/session 0` — HIL toolchain lock

## How to think about Crucible

| You want to… | Do this |
|---|---|
| Adopt Crucible in an existing project | `cd <project-dir> && crucible init` |
| Work on an existing Crucible project | `cd ~/crucible/<name>` (registry shortcut) or `cd <project-dir>` and open Claude Code |
| Improve the framework | Edit files in `~/crucible/core/` directly (this repo) |
| Pull framework updates into an existing project | Manual — each project is its own constitutional fork; cherry-pick or diff against `~/crucible/core/templates/` |

Each project workspace is **independent of `crucible-core` after `crucible init`**.
Constitutional records (`docs/governance/amendments.md`, ratifications, case law)
diverge per project — that is the intended design, because Article I primitives
differ between hardware targets and an Amendment ratified for one device should
not bind another.

## CLAUDE.md merge feature

When `crucible init` is run in a directory that already has its own `CLAUDE.md`
(typical when adopting Crucible into an existing project), the original CLAUDE.md
is preserved verbatim beneath the Crucible template. The resulting merged file
looks like:

```markdown
<!-- ======== CRUCIBLE FRAMEWORK ENTRY-POINT (merged by `crucible init` on <date>) ======== -->

<!-- ====== BEGIN CRUCIBLE FRAMEWORK SECTION ====== -->
... template content ...
<!-- ====== END CRUCIBLE FRAMEWORK SECTION ====== -->
<!-- ====== BEGIN ORIGINAL PROJECT CLAUDE.md ====== -->
... original project content ...
<!-- ====== END ORIGINAL PROJECT CLAUDE.md ====== -->
```

The merged file is committed as-is by `crucible init`. In your first Claude
Code session, invoke the `doc-reviewer` agent — it recognises the marker
block and produces a consolidated CLAUDE.md proposal (deduplicates headings,
flags conflicting instructions, identifies project-specific guidance worth
keeping). Review the proposal and commit the consolidated version yourself.
