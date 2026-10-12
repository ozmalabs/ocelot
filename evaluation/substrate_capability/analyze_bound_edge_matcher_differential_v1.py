#!/usr/bin/env python3
"""Independent generated-graph oracle for the bound-edge matcher gate."""
from __future__ import annotations
import hashlib, json, random, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'evaluation/substrate_capability'))
import bound_edge_matcher_differential_v1 as runner

CAPTURE = ROOT / 'evaluation/reports/bound_edge_matcher_differential_v1_20261005.json'
LOCK = ROOT / 'evaluation/substrate_capability/bound_edge_matcher_differential_v1_lock_20261005.json'
OUT = ROOT / 'evaluation/reports/bound_edge_matcher_differential_v1_analysis_20261005.json'

def digest(pairs):
    return hashlib.sha256(json.dumps(sorted([list(x) for x in pairs]), separators=(',', ':')).encode()).hexdigest()

def generated(panel):
    density, seed = panel['density'], panel['seed']; rng = random.Random(seed)
    left, right = list(range(0, 8)), list(range(4, 12))
    candidates = [(i, j) for i in left for j in right if i != j]
    if density == 1.0: selected = list(candidates)
    elif density == 0.0: selected = []
    else: selected = [pair for pair in candidates if rng.random() < density]
    decoys = [pair for pair in candidates if rng.random() < 0.35]
    rng.shuffle(selected); split = len(selected) // 2
    first, second = selected[:split], selected[split:]
    return left, right, candidates, selected, decoys, first, second

def main():
    capture = json.loads(CAPTURE.read_text()); lock = json.loads(LOCK.read_text())
    expected = {(p['density'], p['replicate'], p['seed']) for p in lock['panels']}
    observed = {(w['density'], w['replicate'], w['seed']) for w in capture['workers']}
    oracle_ok = []
    for panel, worker in zip(lock['panels'], capture['workers']):
        left, right, candidates, selected, decoys, first, second = generated(panel)
        oracle_ok.append(worker['density'] == panel['density'] and worker['seed'] == panel['seed']
            and worker['candidate_pair_count'] == len(candidates)
            and worker['selected_relation_count'] == len(selected)
            and worker['first_relation_count'] == len(first)
            and worker['second_relation_count'] == len(second)
            and worker['decoy_relation_count'] == len(decoys)
            and worker['first_relation_sha256'] == digest(first)
            and worker['final_relation_sha256'] == digest(selected)
            and worker['decoy_relation_sha256'] == digest(decoys)
            and worker['expected_first_witness_sha256'] == digest(first)
            and worker['expected_final_witness_sha256'] == digest(selected)
            and worker['first_phase_parity'] and worker['final_phase_parity'])
    current = runner.manifest()
    checks = {'capture_passed': capture['passed'],
        'capture_lock_hash': capture['lock_sha256'] == runner.sha(LOCK),
        'source_lock_current': current == lock['inputs'] == capture['locked_inputs'] == capture['post_run_inputs'],
        'expected_panel_set': expected == observed,
        'thirty_two_workers': len(capture['workers']) == 32,
        'independent_graph_oracle': all(oracle_ok),
        'phase_one_and_two_parity': all(w['first_phase_parity'] and w['final_phase_parity'] for w in capture['workers']),
        'incremental_edge_addition_accounting': all(w['final_witness_count'] - w['first_witness_count'] == w['second_relation_count'] for w in capture['workers']),
        'empty_and_complete_density_controls': all((w['density'] != 0.0 or w['selected_relation_count'] == 0)
            and (w['density'] != 1.0 or w['selected_relation_count'] == w['candidate_pair_count']) for w in capture['workers'])}
    result = {'schema': 'BoundEdgeMatcherDifferentialV1Analysis', 'passed': all(checks.values()),
        'checks': checks, 'capture_sha256': runner.sha(CAPTURE), 'lock_sha256': runner.sha(LOCK),
        'analyzer_sha256': runner.sha(Path(__file__).resolve()),
        'workers_by_density': {str(d): sum(w['density'] == d for w in capture['workers']) for d in lock['densities']},
        'interpretation_limit': 'Targeted generated-graph semantic differential of fully bound directed edge matching and add-only mutation; not a general proof of matcher correctness.'}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'passed': result['passed'], 'checks': checks, 'output': OUT.relative_to(ROOT).as_posix()}))
    return 0 if result['passed'] else 2

if __name__ == '__main__': raise SystemExit(main())
