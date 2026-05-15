"""Crucible CLI — bootstrap new project workspaces from the framework templates."""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"


def harness_memory_path(project_path: Path) -> Path:
    """Compute the Claude Code harness memory path for a project directory.

    Claude Code encodes the absolute path by replacing every '/' with '-' and
    storing the project under ~/.claude/projects/<encoded>/.
    """
    encoded = str(project_path.resolve()).replace("/", "-")
    return Path.home() / ".claude" / "projects" / encoded


def cmd_new(args: argparse.Namespace) -> int:
    project_name = args.name
    base_dir = Path(args.dir).expanduser().resolve()
    project_dir = base_dir / project_name

    if not TEMPLATES_DIR.exists():
        print(f"error: templates directory not found at {TEMPLATES_DIR}", file=sys.stderr)
        return 2

    if project_dir.exists():
        print(f"error: {project_dir} already exists", file=sys.stderr)
        return 1

    base_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(TEMPLATES_DIR, project_dir)

    memory_dir = project_dir / "docs" / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)
    (memory_dir / "MEMORY.md").write_text("", encoding="utf-8")

    harness_dir = harness_memory_path(project_dir)
    harness_dir.mkdir(parents=True, exist_ok=True)
    symlink_path = harness_dir / "memory"
    if symlink_path.exists() or symlink_path.is_symlink():
        symlink_path.unlink()
    symlink_path.symlink_to(memory_dir)

    if not args.no_git:
        subprocess.run(["git", "init", "-q"], cwd=project_dir, check=True)
        if (project_dir / ".githooks" / "pre-commit").exists():
            subprocess.run(
                ["git", "config", "core.hooksPath", ".githooks"],
                cwd=project_dir,
                check=True,
            )
        subprocess.run(["git", "add", "-A"], cwd=project_dir, check=True)
        subprocess.run(
            ["git", "commit", "-q", "-m", f"Initialize {project_name} from crucible-core templates"],
            cwd=project_dir,
            check=False,
        )

    print(f"{project_name} created at {project_dir}")
    print(f"  templates copied from {TEMPLATES_DIR}")
    print(f"  memory: {memory_dir} (symlinked from {symlink_path})")
    if not args.no_git:
        print(f"  git repo initialised with initial commit")
    print()
    print("Next steps:")
    print(f"  cd {project_dir}")
    print(f"  # open Claude Code here, then run /spec collect")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="crucible",
        description="Crucible Constitutional Governance Framework CLI.",
    )
    sub = parser.add_subparsers(dest="command")

    p_new = sub.add_parser("new", help="Create a new Crucible project workspace.")
    p_new.add_argument("name", help="Project name (used as the directory name verbatim).")
    p_new.add_argument(
        "--dir",
        default="~/crucible",
        help="Parent directory in which to create the project (default: ~/crucible)",
    )
    p_new.add_argument(
        "--no-git",
        action="store_true",
        help="Skip git init + initial commit",
    )
    p_new.set_defaults(func=cmd_new)

    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
