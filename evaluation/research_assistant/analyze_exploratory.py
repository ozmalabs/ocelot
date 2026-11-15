"""Analyze the fixed four-case feasibility comparison; descriptive only."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from statistics import mean
from evaluation.research_assistant.harness import SCORES


def analyze(root: Path) -> dict:
    assignments = json.loads((root / 'assignments.json').read_text())['assignments']
    answers = json.loads((root / 'blind_answers.json').read_text())
    expected = {r['blind_label']: r for r in assignments}
    if len(expected) != len(assignments) or len(answers) != len(assignments):
        raise ValueError('duplicate assignment or missing answer')
    for a in answers:
        label = a['blind_label']
        if label not in expected or a['task_id'] != expected[label]['task_id'] or hashlib.sha256(a['answer'].encode()).hexdigest() != a['answer_sha256']:
            raise ValueError(f'answer identity/hash mismatch: {label}')
    graders = []
    for name in ('grader1.json', 'grader2.json'):
        records = json.loads((root/name).read_text())['records']
        by_label = {r['blind_label']: r for r in records}
        if len(by_label) != len(records) or set(by_label) != set(expected):
            raise ValueError(f'grader labels mismatch: {name}')
        for label, r in by_label.items():
            if r['task_id'] != expected[label]['task_id']:
                raise ValueError('grader task mismatch')
            if any(type(r['scores'].get(s)) is not int or r['scores'][s] not in (0,1,2) for s in SCORES):
                raise ValueError('invalid score')
        graders.append(by_label)
    agreement = {s: sum(graders[0][x]['scores'][s] == graders[1][x]['scores'][s] for x in expected) for s in SCORES}
    rows=[]
    for label, item in expected.items():
        dimensions={s: mean(g[label]['scores'][s] for g in graders) for s in SCORES}
        rows.append({'label': label, 'task_id': item['task_id'], 'arm': item['arm'], 'dimensions': dimensions, 'primary': mean(dimensions.values())})
    arms={}
    for arm in sorted({r['arm'] for r in rows}):
        subset=[r for r in rows if r['arm']==arm]
        arms[arm]={'n':len(subset), 'primary_mean':mean(r['primary'] for r in subset),
                   'dimensions':{s:mean(r['dimensions'][s] for r in subset) for s in SCORES}}
    tasks=sorted({r['task_id'] for r in rows})
    pairs=[]
    for task in tasks:
        scores={r['arm']: r['primary'] for r in rows if r['task_id']==task}
        pairs.append({'task_id':task, 'research_helper_minus_source_only': scores['research_helper']-scores['source_only'],
                      'research_helper_minus_generic_ledger': scores['research_helper']-scores['generic_ledger']})
    return {'study':'four-case exploratory, not confirmatory', 'rows':rows, 'arms':arms, 'paired_differences':pairs,
            'agreement_count_of_12':agreement, 'operational_costs':{'tokens':None,'latency_ms':None,'tool_cost':None},
            'limitations':['four cases, closely related to prior pilot','shared filesystem and unenforced key isolation','one run per arm/task, same model family','no fixed model version or token budget','grading may be unblinded by answer content','no independent key validation'],
            'inference':'Descriptive only; no causal effectiveness claim or confidence interval.'}


def main():
    root=Path(__file__).parent/'exploratory_20261114b'
    print(json.dumps(analyze(root),indent=2))

if __name__=='__main__': main()
