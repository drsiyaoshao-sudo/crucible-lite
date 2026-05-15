# crucible-core

Constitutional governance framework for hardware development — Python infrastructure and project templates.

> **Heads-up:** this repository was renamed from `crucible-lite` and **restructured** on 2026-05-15.
> The previous mono-repo layout (governance + framework + one project's customizations all at
> the root) has been split into a reusable framework (this branch) and per-project workspaces.
> See [Structural rebase](#structural-rebase) below for details.

## What is Crucible?

Crucible is a constitutional governance framework for hardware development. It enforces:

- **Article I — Signal First** — every threshold, parameter, filter cutoff, and FSM transition
  must trace to a named domain primitive (a first-order physically measurable quantity).
- **Article II — Human in the Loop** — irreversible actions require explicit human approval.

The framework provides 17 agents (attorneys, advisors, reviewers, simulator orchestrators,
police) and 10 slash commands that operationalise these rules through a judicial process
(Bills, Hearings, Amendments, Case Law) on top of Claude Code.

## Layout

```
crucible-core/
├── crucible/                 ← Python infrastructure package (pip-installable)
│   ├── cli.py                ← `crucible new <project>` CLI
│   ├── signal/               ← UART event parsing, plot utilities
│   ├── transport/            ← BLE / serial transport helpers
│   ├── sim/                  ← Renode simulation bridge
│   └── checks/               ← CI integrity checks
├── templates/                ← copied into new project workspaces by `crucible new`
│   ├── CLAUDE.md
│   ├── CONSTITUTION.md
│   ├── .claude/
│   │   ├── agents/           ← 17 agent definitions
│   │   └── commands/         ← 10 slash commands
│   └── docs/
│       ├── governance/amendments.md   ← Amendments 1–11 (1–4 PROPOSED until ratified)
│       ├── governance/case_law.md
│       ├── device_context.md          ← placeholder
│       └── toolchain_config.md        ← placeholder
└── pyproject.toml
```

## Install

```bash
git clone https://github.com/SNI22/crucible_lite.git ~/code/crucible-core
pipx install -e ~/code/crucible-core
```

`pipx install -e` creates an isolated venv for the `crucible` CLI and links it on PATH.
Editable install means `git pull` in `~/code/crucible-core/` is picked up automatically —
no re-install needed.

Verify:

```bash
crucible --help
```

## Start a new project

```bash
crucible new <project-name>
```

This:
1. Creates `~/code/crucible-<project-name>/`.
2. Copies `templates/` into it.
3. Creates `<project>/docs/memory/` and symlinks the Claude Code harness memory path to it,
   so per-project auto-memory lives inside the project directory.
4. Runs `git init` and makes an initial commit.

Then in the new directory:
1. Open Claude Code.
2. Run `/spec collect` to interview about device purpose, signal inventory, and ratify
   project-specific Amendment 1 (domain primitives).
3. Run the `agent-updater` agent to propagate Amendment 1 into the agent set.
4. Run `/toolchain init` to register hardware, pins, libraries, blocked toolchains.
5. Continue through `/session 0` (HIL toolchain lock) and subsequent stage gates.

## How Crucible is meant to be used

| You want to… | Do this |
|---|---|
| Work on an existing project | `cd ~/code/crucible-<project>` and open Claude Code |
| Start a new project | `crucible new <project>` and follow the spec / toolchain flow above |
| Improve the framework | Edit files in `~/code/crucible-core/` directly (this repo) |
| Pull framework updates into an existing project | Manual — each project is its own constitutional fork; cherry-pick or diff against `crucible-core/templates/` |

Each `crucible-<project>` workspace is **independent of `crucible-core` after creation**.
Constitutional records (`docs/governance/amendments.md`, ratifications, case law) diverge
per project — that is the intended design, because Article I primitives differ between
hardware targets and an Amendment ratified for one device should not bind another.

## Structural rebase

This branch (`framework-restructure`) is the result of splitting the old mono-repo into:

- **Framework** (this branch, intended to become `main`) — `crucible/` infrastructure +
  `templates/` project skeleton + `crucible` CLI. Reusable across many projects.
- **Per-project workspaces** — each project gets its own directory (e.g.
  `~/code/crucible-cloth-grasp/`) with its own ratified Amendment 1, customised agents,
  populated `device_context.md` and `toolchain_config.md`, and its own git history.

### Why the change

The old layout assumed one project per repo and burned project-specific customizations
(domain primitives, agent edits, toolchain records) into the framework files directly. That
worked for a single project but did not scale — starting a second project meant either
hand-de-customising or forking-then-stripping a heavily-modified copy.

The new layout makes the framework reusable: `pipx install -e` once, then `crucible new`
per project. Per-project state (governance record, propagated agent edits, populated
toolchain config) lives in the project workspace, not the framework.

### What moved where

| Was in old `main` | Is now |
|---|---|
| `crucible/` (Python infra) | `crucible/` (here), pip-installable via `pyproject.toml` |
| `.claude/agents/`, `.claude/commands/` | `templates/.claude/agents/`, `templates/.claude/commands/` — copied into new projects |
| `CLAUDE.md`, `CONSTITUTION.md` | `templates/CLAUDE.md`, `templates/CONSTITUTION.md` — copied into new projects |
| `docs/governance/`, `docs/device_context.md`, `docs/toolchain_config.md` | `templates/docs/...` — copied into new projects |
| `examples/`, `CHANGELOG.md`, `ONBOARDING.md`, etc. | Removed — these were reference-implementation artefacts that didn't fit the framework/instance split |

The agent and command files in `templates/.claude/` still carry the crucible-comfort
gait-domain reference (stance/swing/heel-strike, m/s², dps) from when the repo carried
that example implementation. Each new project's `agent-updater` propagation pass after
`/spec collect` overwrites those references with the project's own primitives — so the
reference content is not stale framework, it is a starter template.

### Existing branches

- `main` — old structure (pre-restructure). Unchanged on this branch.
- `cloth_grasp` — the first project that used the old structure, now extracted to a
  standalone workspace at `~/code/crucible-cloth-grasp/` locally. The branch is preserved
  on this repo for history. New cloth-grasp work continues on that branch but in a
  different working directory.

### Migration checklist for existing forks

If you have an existing fork of this repo at the old structure and want to migrate to
the framework/instance split:

1. Rename your local directory to reflect the project it currently represents
   (e.g. `crucible-lite/` → `crucible-<your-project>/`).
2. Clone this branch into a new `crucible-core/` directory and `pipx install -e` it.
3. The existing project workspace stays as-is — it is now your first project workspace.
   Future projects use `crucible new`.

Open a pull request to merge this branch into `main` once you have reviewed the structural
diff.
