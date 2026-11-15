"""Source-located positive and ambiguity controls; selected after initial probe.

These are intentionally hand-selected and do not measure coverage. The paper
reader does not automatically extract these prose/remark passages.
"""
from __future__ import annotations
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path
from scripts.ocelot_research_service import ResearchService
from scripts.ocelot_research_lean import LeanExportError

ROOT = Path(__file__).resolve().parents[2]
GE = ROOT.parent / 'graphic-equalisation'
OUT = ROOT / 'evaluation/research_assistant/real_papers_20261115'
CONTROLS = [
    ('simple_integer', 'papers/formal/04_narrativium_theory_referenced.tex', 'N=2'),
    ('floating_point', 'papers/formal/01f_graphic_equalisation_qualia_and_consciousness_grounding.tex', 'g=0.13'),
    ('implicit_multiplication', 'papers/formal/04_narrativium_theory_referenced.tex', 'E_0=mc^2'),
]


def main():
    rows = []
    with tempfile.TemporaryDirectory(prefix='ocelot-manual-controls-') as work:
        svc = ResearchService(work)
        for label, rel, formula in CONTROLS:
            file = GE / rel
            raw = file.read_bytes()
            sha = hashlib.sha256(raw).hexdigest()
            lines = raw.decode('utf-8').splitlines()
            found = [(i, line) for i, line in enumerate(lines, 1) if '$' + formula + '$' in line]
            if not found:
                rows.append({'id': label, 'status': 'source_not_found'})
                continue
            lineno, line = found[0]
            sid = svc.call('init', {'question': 'Manually locate a source formula for a capability control',
                                    'roots': [{'root_id': 'ge', 'path': str(GE), 'files': [rel]}]})['investigation_id']
            source = svc.call('record', {'session_id': sid, 'kind': 'Source', 'fields': {
                'name': file.name, 'locator': {'root_id': 'ge', 'repository': 'graphic-equalisation',
                                              'path': rel, 'sha256': sha,
                                              'start_line': lineno, 'end_line': lineno}}})
            claim = svc.call('record', {'session_id': sid, 'kind': 'Claim', 'fields': {
                'wording': line.strip(), 'raw_excerpt': line.strip(), 'claim_type': 'inference',
                'status': 'unresolved', 'extraction': 'manual_source_location', 'semantics_verified': False}})
            svc.call('link', {'session_id': sid, 'src': claim['id'], 'relation': 'cites', 'tgt': source['id']})
            model = svc.call('formula_model', {'session_id': sid, 'claim_id': claim['id'],
                'formula': formula, 'reviewer': 'automated source-located control, not a scientific review',
                'review_note': 'Manually located source formula; intended meanings and paper claims not verified.'})
            trans = model.get('translation', model)
            row = {'id': label, 'source': str(file), 'source_sha256': sha, 'source_line': lineno,
                   'formula': formula, 'translation_status': trans.get('status'),
                   'term': trans.get('term'), 'variables': trans.get('variables'),
                   'residuals': trans.get('residuals', []), 'source_match': model.get('found_verbatim_in_claim'),
                   'selection': 'hand-selected after seeing initial result; not an extraction coverage sample'}
            if trans.get('status') == 'translated':
                node_id = model['candidate']['id']
                try:
                    lean = svc.call('export_lean', {'session_id': sid, 'node_id': node_id})['lean']
                    path = OUT / 'lean' / f'control_{label}.lean'
                    path.write_text(lean, encoding='utf-8')
                    checked = svc.call('check_lean', {'session_id': sid, 'node_id': node_id})
                    row.update({'lean_status': checked['status'], 'lean_file': str(path.relative_to(OUT)),
                                'lean_version': checked['lean_version'], 'lean_sha256': checked['source_sha256']})
                    if label == 'simple_integer' and checked['status'] == 'accepted':
                        row['native_when_N_2'] = svc.call('execute', {'session_id': sid, 'node_id': node_id, 'env': {'N': 2}})['value']
                        row['native_when_N_1'] = svc.call('execute', {'session_id': sid, 'node_id': node_id, 'env': {'N': 1}})['value']
                        # A kernel-checked concrete evaluation, not a proof of the paper.
                        term_name = re.search(r'^def (researchTerm_\d+_claim_\d+) \(input_N : Int\)', lean, re.M)
                        if term_name:
                            assertion = f'\nexample : {term_name.group(1)} 2 (by decide) = true := by decide\n'
                            proof_path = OUT / 'lean' / 'control_simple_integer_example.lean'
                            proof_path.write_text(lean + assertion, encoding='utf-8')
                            run = subprocess.run([checked['lean_executable'], '-j', '1', str(proof_path)], capture_output=True, text=True, timeout=60)
                            row['lean_example_status'] = 'accepted' if run.returncode == 0 else 'rejected'
                            row['lean_example_output'] = (run.stdout + run.stderr)[:2000]
                except LeanExportError as exc:
                    row['lean_status'] = 'unsupported'
                    row['lean_error'] = str(exc)
            else:
                row['lean_status'] = 'not_attempted'
            rows.append(row)
    result = {'study': 'hand-selected real-source controls, not a coverage sample', 'controls': rows}
    (OUT / 'manual_controls.json').write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps([{'id': r['id'], 'translation': r.get('translation_status'), 'lean': r.get('lean_status'),
                       'lean_example': r.get('lean_example_status')} for r in rows], indent=2))

if __name__ == '__main__':
    main()
