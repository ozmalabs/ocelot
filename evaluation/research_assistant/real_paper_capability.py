"""Reproduce a bounded real-paper reader/formula/Lean capability probe.

Uses local sources only. The selection is the first 12 operator-bearing math
fragments in recognized formal statements per file, not a random sample.
"""
from __future__ import annotations
import hashlib
import json
import re
import tempfile
from pathlib import Path
from scripts.ocelot_research_service import ResearchService
from scripts.ocelot_research_lean import LeanExportError

ROOT = Path(__file__).resolve().parents[2]
GE = ROOT.parent / 'graphic-equalisation'
OUT = ROOT / 'evaluation/research_assistant/real_papers_20261115'
PAPERS = [
    ('ge_theory', GE, 'papers/formal/01_law_of_graphic_equalisation_theory_referenced.tex'),
    ('ge_born', GE, 'papers/formal/01d_graphic_equalisation_born_recovery.tex'),
    ('arxiv_2606_13224', ROOT, 'data/arxiv/2606.13224/main.tex'),
]
# Detect delimited math, not LaTeX macros, prose equations, figure text or
# external \input files. Match longest delimiters before inline dollar math.
MATH = re.compile(r'\\\[(.*?)\\\]|\\\((.*?)\\\)|(?<!\\)\$(?!\$)(.*?)(?<!\\)\$', re.S)
OPERATOR = re.compile(r'[=+\-*/^<>≤≥≠∈∀∃∑×]|\\(?:frac|sum|prod|forall|exists|land|lor|implies|leq|geq|neq|cdot|times|to|in|subset|cup|cap|partial)\b')
MAX_FRAGMENTS = 12


def run() -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'lean').mkdir(exist_ok=True)
    reports = []
    with tempfile.TemporaryDirectory(prefix='ocelot-paper-probe-') as workspace:
        svc = ResearchService(workspace)
        for paper_id, repo, rel in PAPERS:
            file = repo / rel
            if not file.is_file():
                reports.append({'paper_id': paper_id, 'path': rel, 'status': 'source_missing'})
                continue
            sha = hashlib.sha256(file.read_bytes()).hexdigest()
            state = svc.call('init', {'question': f'Probe extraction from {paper_id}',
                                      'roots': [{'root_id': paper_id, 'path': str(repo), 'files': [rel]}]})
            sid = state['investigation_id']
            ingest = svc.call('paper_ingest', {'session_id': sid, 'root_id': paper_id, 'path': rel, 'max_formula_candidates': 0})
            claims = ingest['claims']
            sampled = []
            eligible = 0
            for claim in claims:
                excerpt = claim.get('raw_excerpt') or ''
                for match in MATH.finditer(excerpt):
                    formula = next(x for x in match.groups() if x is not None).strip()
                    if not OPERATOR.search(formula):
                        continue
                    eligible += 1
                    if len(sampled) >= MAX_FRAGMENTS:
                        continue
                    # Keep formula content exactly as written for source matching.
                    sampled.append({'claim_id': claim['id'], 'claim_label': claim.get('paper_label'),
                                    'source_line_start': claim['source_locator']['start_line'] + excerpt[:match.start()].count('\n'),
                                    'formula': formula})
            for i, item in enumerate(sampled, start=1):
                arguments = {'session_id': sid, 'claim_id': item['claim_id'], 'formula': item['formula'],
                             'reviewer': 'automated capability probe (not a human review)',
                             'review_note': 'Mechanical formula translation probe; semantics and source fidelity are not verified.'}
                try:
                    model = svc.call('formula_model', arguments)
                    translation = model.get('translation', model)
                    item['translation_status'] = translation.get('status', 'unsupported')
                    item['translation_reason'] = translation.get('reason')
                    item['translation_residuals'] = translation.get('residuals', [])
                    if item['translation_status'] != 'translated':
                        item['lean_status'] = 'not_attempted_translation_unsupported'
                        continue
                    item['term'] = translation['term']
                    item['source_match'] = model['found_verbatim_in_claim']
                    node_id = model['candidate']['id']
                    try:
                        exported = svc.call('export_lean', {'session_id': sid, 'node_id': node_id})
                        name = f'{paper_id}_{i:02d}.lean'
                        (OUT / 'lean' / name).write_text(exported['lean'], encoding='utf-8')
                        check = svc.call('check_lean', {'session_id': sid, 'node_id': node_id})
                        item['lean_status'] = check['status']
                        item['lean_file'] = f'lean/{name}'
                        item['lean_source_sha256'] = check['source_sha256']
                        item['lean_version'] = check['lean_version']
                        if check['status'] != 'accepted':
                            item['lean_error'] = (check['stdout'] + check['stderr'])[:3000]
                    except LeanExportError as exc:
                        item['lean_status'] = 'unsupported'
                        item['lean_error'] = str(exc)
                except Exception as exc:
                    item['translation_status'] = 'error'
                    item['lean_status'] = 'not_attempted_error'
                    item['translation_reason'] = f'{type(exc).__name__}: {exc}'
            native = svc.call('native_graph', {'session_id': sid, 'query': {'type': 'NodesOfType', 'node_type': 'Claim'}})
            reports.append({'paper_id': paper_id, 'source': str(file), 'source_sha256': sha,
                            'source_revision': ingest['preview'].get('revision'),
                            'status': 'ingested' if ingest['ingested'] else 'no_claims_or_partial',
                            'claims_extracted': len(claims),
                            'native_claims_after_models': len(native['query_result']),
                            'unresolved_references': len(ingest['preview']['unresolved_references']),
                            'eligible_operator_fragments': eligible, 'sampled_count': len(sampled),
                            'fragments': sampled})
    return {'study': 'exploratory real-paper capability probe',
            'selection': 'first 12 delimited operator-bearing math fragments in recognized formal statement environments in each selected file, in source order; repeated occurrences retained',
            'limits': ['source text only; no OCR, external input files, or whole-paper formula census',
                       'operator-fragment detection is heuristic; a fragment is not necessarily a complete claim',
                       'successful syntax translation and Lean acceptance do not establish faithful formalization or prove the paper',
                       'nonrandom small sample; no estimate of general accuracy'], 'papers': reports}


def main():
    result = run()
    path = OUT / 'results.json'
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'result_path': str(path), 'papers': [
        {'paper_id': p['paper_id'], 'status': p['status'],
         'claims_extracted': p.get('claims_extracted'), 'sampled_count': p.get('sampled_count'),
         'translated': sum(x['translation_status'] == 'translated' for x in p.get('fragments', [])),
         'lean_accepted': sum(x['lean_status'] == 'accepted' for x in p.get('fragments', []))}
        for p in result['papers']]}, indent=2))

if __name__ == '__main__':
    main()
