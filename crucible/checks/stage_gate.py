"""
Amendment 2 — Stage Gate Order enforcement.

Detects stages marked CLOSED in toolchain_config.md without a corresponding
stage-compactor entry in case_law.md.
"""

import re
from typing import Optional
from pathlib import Path


def _closed_stages(repo_root: Path) -> set[str]:
    path = repo_root / 'docs' / 'toolchain_config.md'
    if not path.exists():
        return set()
    text = path.read_text()
    # Match patterns like: Stage 0: CLOSED, Stage 1 — CLOSED, stage_lock: CLOSED
    return set(re.findall(
        r'Stage\s+(\d+)[^\n]*?CLOSED', text, re.IGNORECASE
    ))


def _compacted_stages(repo_root: Path) -> set[str]:
    path = repo_root / 'docs' / 'governance' / 'case_law.md'
    if not path.exists():
        return set()
    text = path.read_text()
    # stage-compactor entries reference "Stage N" and "compacted" or "closed"
    return set(re.findall(
        r'Stage\s+(\d+)[^\n]*?(?:compacted|stage.compactor|gate closed)',
        text, re.IGNORECASE
    ))


def run(repo_root: Path, base_ref: Optional[str] = None) -> list[dict]:
    findings = []
    closed = _closed_stages(repo_root)
    compacted = _compacted_stages(repo_root)
    missing = closed - compacted

    for stage in sorted(missing):
        findings.append({
            'severity': 'VIOLATION',
            'file': 'docs/toolchain_config.md',
            'message': f'Stage {stage} marked CLOSED in toolchain_config.md but no '
                       f'stage-compactor entry found in case_law.md. '
                       f'Stage gate was closed without the compactor — Amendment 2 violation.',
        })

    return findings
