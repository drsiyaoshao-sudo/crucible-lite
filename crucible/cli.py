"""Crucible CLI — bootstrap a project workspace from the framework templates."""
from __future__ import annotations

import argparse
import datetime as dt
import os
import shutil
import subprocess
import sys
from pathlib import Path


TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

CLAUDE_MD = "CLAUDE.md"
MERGE_HEADER_BANNER = (
    "<!-- ========================================================================\n"
    "     CRUCIBLE FRAMEWORK ENTRY-POINT (merged by `crucible init` on {date})\n"
    "\n"
    "     This file was created by merging the Crucible CLAUDE.md template with the\n"
    "     existing project CLAUDE.md found in this directory. Both sections are\n"
    "     preserved verbatim, separated by the markers below.\n"
    "\n"
    "     ACTION REQUIRED: in your first Claude Code session here, ask the\n"
    "     doc-reviewer agent to audit this file. It will produce a consolidated\n"
    "     CLAUDE.md proposal that deduplicates, reorders, and reconciles the two\n"
    "     halves. Commit the result yourself after review.\n"
    "     ======================================================================== -->\n\n"
)
CRUCIBLE_BEGIN_MARKER = "<!-- ====== BEGIN CRUCIBLE FRAMEWORK SECTION ====== -->\n"
CRUCIBLE_END_MARKER = "\n<!-- ====== END CRUCIBLE FRAMEWORK SECTION ====== -->\n\n"
PROJECT_BEGIN_MARKER = "<!-- ====== BEGIN ORIGINAL PROJECT CLAUDE.md ====== -->\n\n"
PROJECT_END_MARKER = "\n<!-- ====== END ORIGINAL PROJECT CLAUDE.md ====== -->\n"


def harness_memory_path(project_path: Path) -> Path:
    encoded = str(project_path.resolve()).replace("/", "-")
    return Path.home() / ".claude" / "projects" / encoded


def _template_relpaths(templates_dir: Path) -> list[Path]:
    return [p.relative_to(templates_dir) for p in templates_dir.rglob("*") if p.is_file()]


def _merge_claude_md(project_dir: Path, template_path: Path) -> bool:
    """Merge an existing CLAUDE.md with the template version. Returns True if merged."""
    existing = project_dir / CLAUDE_MD
    if not existing.exists():
        return False
    template_content = template_path.read_text(encoding="utf-8")
    existing_content = existing.read_text(encoding="utf-8")
    today = dt.date.today().isoformat()
    merged = (
        MERGE_HEADER_BANNER.format(date=today)
        + CRUCIBLE_BEGIN_MARKER
        + template_content
        + CRUCIBLE_END_MARKER
        + PROJECT_BEGIN_MARKER
        + existing_content
        + PROJECT_END_MARKER
    )
    existing.write_text(merged, encoding="utf-8")
    return True


def cmd_init(args: argparse.Namespace) -> int:
    project_dir = Path.cwd().resolve()
    project_name = project_dir.name

    if not TEMPLATES_DIR.exists():
        print(f"error: templates directory not found at {TEMPLATES_DIR}", file=sys.stderr)
        return 2

    template_files = _template_relpaths(TEMPLATES_DIR)

    # CLAUDE.md is handled specially: merge instead of conflict.
    claude_template = TEMPLATES_DIR / CLAUDE_MD
    claude_merged = False

    conflicts = []
    for rel in template_files:
        if rel.name == CLAUDE_MD and rel.parent == Path("."):
            continue  # handled as merge below
        if (project_dir / rel).exists():
            conflicts.append(rel)

    if conflicts and not args.force:
        print(f"error: the following files already exist in {project_dir}:", file=sys.stderr)
        for c in conflicts:
            print(f"  {c}", file=sys.stderr)
        print(file=sys.stderr)
        print("Re-run with --force to overwrite, or delete/move the conflicting files first.", file=sys.stderr)
        print("(Note: CLAUDE.md is handled separately and will be merged automatically.)", file=sys.stderr)
        return 1

    # Copy all template files except top-level CLAUDE.md
    for rel in template_files:
        if rel.name == CLAUDE_MD and rel.parent == Path("."):
            continue
        dest = project_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(TEMPLATES_DIR / rel, dest)

    # Handle CLAUDE.md
    if claude_template.exists():
        if (project_dir / CLAUDE_MD).exists():
            claude_merged = _merge_claude_md(project_dir, claude_template)
        else:
            shutil.copy2(claude_template, project_dir / CLAUDE_MD)

    memory_dir = project_dir / "docs" / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)
    memory_index = memory_dir / "MEMORY.md"
    if not memory_index.exists():
        memory_index.write_text("", encoding="utf-8")

    harness_dir = harness_memory_path(project_dir)
    harness_dir.mkdir(parents=True, exist_ok=True)
    harness_symlink = harness_dir / "memory"
    if harness_symlink.exists() or harness_symlink.is_symlink():
        harness_symlink.unlink()
    harness_symlink.symlink_to(memory_dir)

    crucible_registry = Path.home() / "crucible" / project_name
    crucible_registry.parent.mkdir(parents=True, exist_ok=True)
    if crucible_registry.is_symlink():
        if crucible_registry.resolve() != project_dir:
            crucible_registry.unlink()
            crucible_registry.symlink_to(project_dir)
    elif crucible_registry.exists():
        print(
            f"warning: {crucible_registry} already exists and is not a symlink; leaving it alone.",
            file=sys.stderr,
        )
    else:
        crucible_registry.symlink_to(project_dir)

    if not args.no_git:
        is_repo = (project_dir / ".git").exists()
        if not is_repo:
            subprocess.run(["git", "init", "-q"], cwd=project_dir, check=True)
        if (project_dir / ".githooks" / "pre-commit").exists():
            subprocess.run(
                ["git", "config", "core.hooksPath", ".githooks"],
                cwd=project_dir,
                check=True,
            )
        subprocess.run(["git", "add", "-A"], cwd=project_dir, check=True)
        commit_msg = (
            f"Initialize {project_name} from crucible-core templates"
            if not is_repo
            else f"Add Crucible governance scaffold to {project_name}"
        )
        if claude_merged:
            commit_msg += " (CLAUDE.md merged — review needed)"
        subprocess.run(
            ["git", "commit", "-q", "-m", commit_msg],
            cwd=project_dir,
            check=False,
        )

    print(f"crucible initialized in {project_dir}")
    print(f"  templates copied from {TEMPLATES_DIR}")
    print(f"  memory: {memory_dir} (symlinked from {harness_symlink})")
    print(f"  registry: {crucible_registry} -> {project_dir}")
    if not args.no_git:
        print(f"  git hooks: core.hooksPath = .githooks")
    if claude_merged:
        print()
        print("  *** CLAUDE.md MERGED — REVIEW NEEDED ***")
        print("  Your existing CLAUDE.md was preserved verbatim beneath the Crucible template.")
        print("  In your first Claude Code session here, run:")
        print("    \"invoke doc-reviewer to audit the merged CLAUDE.md\"")
        print("  doc-reviewer will produce a consolidated proposal you can review.")
    print()

    if args.no_claude:
        print("Next: launch Claude Code here when ready.")
        print(f"  cd {project_dir} && claude")
        return 0

    claude_bin = shutil.which("claude")
    if not claude_bin:
        print("claude command not found on PATH.")
        print(f"Install Claude Code, then run: cd {project_dir} && claude")
        return 0

    print("Launching Claude Code...")
    os.execv(claude_bin, ["claude"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="crucible",
        description="Crucible Constitutional Governance Framework CLI.",
    )
    sub = parser.add_subparsers(dest="command")

    p_init = sub.add_parser(
        "init",
        help="Initialize Crucible in the current directory and launch Claude Code.",
    )
    p_init.add_argument(
        "--no-git",
        action="store_true",
        help="Skip git init / staging / commit and hook activation",
    )
    p_init.add_argument(
        "--no-claude",
        action="store_true",
        help="Do not launch Claude Code at the end; just print the next-step hint",
    )
    p_init.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files that conflict with the templates "
             "(CLAUDE.md is merged automatically regardless of this flag).",
    )
    p_init.set_defaults(func=cmd_init)

    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
