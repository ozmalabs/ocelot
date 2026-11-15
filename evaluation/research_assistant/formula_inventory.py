"""Inspect bounded source-located formula-candidate coverage on the probe papers."""
from __future__ import annotations
import json
import tempfile
from pathlib import Path
from scripts.ocelot_research_service import ResearchService
from evaluation.research_assistant.real_paper_capability import PAPERS

OUT = Path(__file__).resolve().parent / 'real_papers_20261115_after' / 'formula_inventory.json'


def main():
    rows = []
    with tempfile.TemporaryDirectory(prefix='ocelot-inventory-') as root:
        svc = ResearchService(root)
        for pid, repo, path in PAPERS:
            sid = svc.call('init', {'question': 'Formula inventory', 'roots': [
                {'root_id': pid, 'path': str(repo), 'files': [path]}]})['investigation_id']
            result = svc.call('paper_preview', {'session_id': sid, 'root_id': pid,
                                                'path': path, 'max_formula_candidates': 256})
            rows.append({'paper_id': pid, 'source_sha256': result['sha256'],
                         'claim_records': len(result['records']),
                         'candidate_count': len(result['formula_candidates']),
                         'formula_extraction': result['formula_extraction']})
    OUT.parent.mkdir(exist_ok=True, parents=True)
    OUT.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps(rows, indent=2, ensure_ascii=False))

if __name__ == '__main__': main()
