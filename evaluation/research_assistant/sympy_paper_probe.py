"""Replay the fixed paper fragments as unverified SymPy/Lark proposals."""
from __future__ import annotations

from collections import Counter
from importlib.metadata import version, PackageNotFoundError
import json
from pathlib import Path

from scripts.ocelot_formula_sympy import sympy_lark_candidate

ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / 'evaluation/research_assistant/real_papers_20261115_after/results.json'
OUTPUT = ROOT / 'evaluation/research_assistant/prior_art_20261115/sympy_paper_probe.json'


def main():
    sample = json.loads(BASELINE.read_text())
    versions = {}
    for package in ('sympy', 'lark'):
        try:
            versions[package] = version(package)
        except PackageNotFoundError:
            versions[package] = None
    papers = []
    for paper in sample['papers']:
        fragments = []
        for fragment in paper.get('fragments', []):
            parsed = sympy_lark_candidate(fragment['formula'])
            fragments.append({'formula': fragment['formula'], 'source_line_start': fragment['source_line_start'],
                              'native_translation_status': fragment['translation_status'], 'candidate': parsed})
        papers.append({'paper_id': paper['paper_id'], 'source_sha256': paper.get('source_sha256'),
                       'counts': dict(Counter(f['candidate']['status'] for f in fragments)), 'fragments': fragments})
    report = {'selection': sample['selection'], 'versions': versions, 'papers': papers,
              'interpretation': 'Parser candidates only; neither correctness nor native executability is established.'}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({'output': str(OUTPUT), 'versions': versions,
                      'counts': {p['paper_id']: p['counts'] for p in papers}}, indent=2))


if __name__ == '__main__':
    main()
