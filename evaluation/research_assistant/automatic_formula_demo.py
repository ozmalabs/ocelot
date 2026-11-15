"""Source-to-native-to-Lean examples from two previously sampled local papers.

Two source spans are selected explicitly after inspection, not randomly; their
purpose is to verify the integration path, not to estimate coverage.
"""
from __future__ import annotations
import json
import tempfile
from pathlib import Path
from scripts.ocelot_research_service import ResearchService

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'evaluation/research_assistant/real_papers_20261115_after'
CASES = [
    {'id': 'narrativium_N', 'root': ROOT.parent / 'graphic-equalisation',
     'path': 'papers/formal/04_narrativium_theory_referenced.tex',
     'formula': 'N=2', 'inputs': [{'N': 2}, {'N': 1}]},
    {'id': 'narrativium_mass_energy', 'root': ROOT.parent / 'graphic-equalisation',
     'path': 'papers/formal/04_narrativium_theory_referenced.tex',
     'formula': 'E_0=mc^2', 'domain_assumptions': {'implicit_products': {'mc': ['m', 'c']}},
     'inputs': [{'E_0': 18, 'm': 2, 'c': 3}, {'E_0': 36, 'm': 2, 'c': 3}]},
    {'id': 'arxiv_natural_domain', 'root': ROOT,
     'path': 'data/arxiv/2606.13224/main.tex',
     'formula': r'm,n\in\NN', 'domain_assumptions': {'natural_minimum': 0},
     'inputs': [{'m': 0, 'n': 2}, {'m': -1, 'n': 2}]},
    {'id': 'arxiv_membership', 'root': ROOT,
     'path': 'data/arxiv/2606.13224/main.tex',
     'formula': r'\epsilon,\mu\in\{0,1\}',
     'inputs': [{'epsilon': 0, 'mu': 1}, {'epsilon': 2, 'mu': 1}]},
]


def main():
    OUT.mkdir(exist_ok=True, parents=True)
    (OUT / 'lean').mkdir(exist_ok=True)
    rows = []
    with tempfile.TemporaryDirectory(prefix='ocelot-paper-automatic-') as directory:
        svc = ResearchService(directory)
        for case in CASES:
            sid = svc.call('init', {'question': 'Read and model the selected paper formula',
                'roots': [{'root_id': 'paper', 'path': str(case['root']), 'files': [case['path']]}]})['investigation_id']
            base = {'session_id': sid, 'root_id': 'paper', 'path': case['path']}
            preview = svc.call('paper_preview', {**base, 'max_formula_candidates': 256})
            found = [(i, item) for i, item in enumerate(preview['formula_candidates'])
                     if item['formula'] == case['formula']]
            if not found:
                rows.append({'id': case['id'], 'status': 'not_extracted'})
                continue
            index, item = found[0]
            svc.call('paper_ingest', {**base, 'max_formula_candidates': 0})
            result = svc.call('paper_ingest', {**base, 'formula_offset': index, 'max_formula_candidates': 1})
            evidence = result['formula_evidence'][0]
            model = svc.call('formula_model', {'session_id': sid, 'claim_id': evidence['id'],
                'formula': item['formula'], 'domain_assumptions': case.get('domain_assumptions', {}),
                'reviewer': 'automated source-to-model capability probe',
                'review_note': 'Explicit candidate; semantic faithfulness and paper claims require independent review.'})
            if model.get('status') == 'unsupported':
                rows.append({'id': case['id'], 'status': 'translation_refused', 'detail': model})
                continue
            node = model['candidate']['id']
            lean = svc.call('export_lean', {'session_id': sid, 'node_id': node})
            lean_path = OUT / 'lean' / (case['id'] + '.lean')
            lean_path.write_text(lean['lean'], encoding='utf-8')
            check = svc.call('check_lean', {'session_id': sid, 'node_id': node})
            values = []
            for env in case['inputs']:
                run = svc.call('execute', {'session_id': sid, 'node_id': node, 'env': env})
                values.append({'env': env, 'status': run['status'], 'value': run['value']})
            native = svc.call('native_graph', {'session_id': sid,
                        'query': {'type': 'NodesOfType', 'node_type': 'Evidence'}})
            rows.append({'id': case['id'], 'status': 'translated', 'paper': str(case['root'] / case['path']),
                'source_sha256': preview['sha256'], 'source_line': item['locator']['start_line'],
                'formula': item['formula'], 'formula_offset': index,
                'source_match': model['found_verbatim_in_claim'],
                'translation_residuals': model['translation']['residuals'],
                'native_values': values, 'native_evidence_count': len(native['query_result']),
                'lean': {'status': check['status'], 'source_sha256': check['source_sha256'],
                         'version': check['lean_version'], 'file': str(lean_path.relative_to(OUT))}})
    (OUT / 'automatic_examples.json').write_text(json.dumps({'selection': 'hand-selected after the original probe, not a coverage sample', 'cases': rows}, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps(rows, indent=2, ensure_ascii=False))

if __name__ == '__main__': main()
