"""
Amendment 12 — Corpus Supremacy enforcement.

Layer 2 swap (signals.py / algorithm.py) without Hearing → VIOLATION
Direct edit to Layer 4 ephemeral files without corpus change   → VIOLATION
"""

import re
import subprocess
from typing import Optional
from pathlib import Path

LAYER_2 = {'src/signals.py', 'src/algorithm.py'}
LAYER_4 = {'src/events.py', 'src/analysis.py', 'src/plot.py'}
LAYER_4_PREFIX = 'test'   # any file under test/ is Layer 4


def _changed_files(base_ref: Optional[str]) -> set[str]:
    if base_ref:
        result = subprocess.run(
            ['git', 'diff', '--name-only', f'{base_ref}...HEAD'],
            capture_output=True, text=True
        )
    else:
        result = subprocess.run(
            ['git', 'diff', '--cached', '--name-only'],
            capture_output=True, text=True
        )
    return set(result.stdout.strip().splitlines())


def _case_law_text(repo_root: Path) -> str:
    path = repo_root / 'docs' / 'governance' / 'case_law.md'
    return path.read_text() if path.exists() else ''


def _hearing_present(case_law: str, filename: str) -> bool:
    """True if case_law contains a Hearing entry mentioning the file or Layer 2."""
    if re.search(r'Judicial Hearing', case_law, re.IGNORECASE) and \
       re.search(r'signals\.py|algorithm\.py|Layer 2', case_law, re.IGNORECASE):
        return True
    return False


def _corpus_changed(changed: set[str]) -> bool:
    """True if a Layer 1 corpus file changed in the same diff."""
    corpus = {
        'docs/device_context.md',
        'docs/governance/amendments.md',
        'docs/toolchain_config.md',
        'CONSTITUTION.md',
    }
    return bool(changed & corpus)


def run(repo_root: Path, base_ref: Optional[str] = None) -> list[dict]:
    findings = []
    changed = _changed_files(base_ref)
    case_law = _case_law_text(repo_root)

    # Layer 2 swap check
    layer2_touched = changed & LAYER_2
    if layer2_touched:
        if not _hearing_present(case_law, str(layer2_touched)):
            findings.append({
                'severity': 'VIOLATION',
                'file': ', '.join(sorted(layer2_touched)),
                'message': f'Layer 2 corpus file(s) changed without a recorded Judicial Hearing. '
                           f'Run /judicial hear before swapping signals.py or algorithm.py. '
                           f'Amendment 12 — Corpus Supremacy.',
            })

    # Layer 4 direct edit check
    layer4_touched = {
        f for f in changed
        if f in LAYER_4 or Path(f).parts[0] == LAYER_4_PREFIX
    }
    if layer4_touched and not _corpus_changed(changed):
        findings.append({
            'severity': 'VIOLATION',
            'file': ', '.join(sorted(layer4_touched)),
            'message': f'Layer 4 ephemeral file(s) edited directly without a corresponding '
                       f'corpus change (Layer 1/2). Correct path: change the corpus, then '
                       f'regenerate. Amendment 12 — Corpus Supremacy.',
        })

    return findings
