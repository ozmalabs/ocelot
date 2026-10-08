#!/usr/bin/env python3
"""Independent oracle analysis for the multi-shape matcher differential."""
from __future__ import annotations
import hashlib, json, random, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'evaluation/substrate_capability'))
import bound_edge_matcher_differential_v2 as runner
CAPTURE = ROOT / 'evaluation/reports/bound_edge_matcher_differential_v2_20261005.json'
LOCK = ROOT / 'evaluation/substrate_capability/bound_edge_matcher_differential_v2_lock_20261005.json'
OUT = ROOT / 'evaluation/reports/bound_edge_matcher_differential_v2_analysis_20261005.json'

def digest(pairs):
    return hashlib.sha256(json.dumps(sorted([list(x) for x in pairs]), separators=(',', ':')).encode()).hexdigest()

def generated(panel):
    density, seed = panel['density'], panel['seed']; rng = random.Random(seed); n = runner.NODE_COUNT
    left, right = list(range(0, 8)), list(range(4, 12)); universe = [(i, j) for i in range(n) for j in range(n)]
    if density == 1.0: relation = list(universe)
    elif density == 0.0: relation = []
    else: relation = [pair for pair in universe if rng.random() < density]
    decoys = [pair for pair in universe if rng.random() < 0.25]
    rng.shuffle(relation); split = len(relation) // 2
    return left, right, relation, decoys, relation[:split], relation[split:]

def expected_sets(left, right, relation):
    relation = set(relation)
    return {
        'witness_lr': {(i, j) for i in left for j in right if i != j and (i, j) in relation},
        'witness_rl': {(i, j) for i in left for j in right if i != j and (j, i) in relation},
        'witness_loop': {(i, i) for i in left if (i, i) in relation},
        'witness_where': {(i, j) for i in left for j in right if i != j and (i, j) in relation and i % 3 == j % 3},
    }

def main():
    capture = json.loads(CAPTURE.read_text()); lock = json.loads(LOCK.read_text())
    expected_panels = {(p['density'], p['replicate'], p['seed']) for p in lock['panels']}
    observed_panels = {(w['density'], w['replicate'], w['seed']) for w in capture['workers']}
    oracle_pass = []
    for panel, worker in zip(lock['panels'], capture['workers']):
        left, right, relation, decoys, first, second = generated(panel)
        expected_first = expected_sets(left, right, first)
        expected_final = expected_sets(left, right, relation)
        expected_ok = all(worker['first_results'][name]['expected_sha256'] == digest(pairs)
            and worker['final_results'][name]['expected_sha256'] == digest(expected_final[name])
            and worker['first_results'][name]['actual_sha256'] == digest(pairs)
            and worker['final_results'][name]['actual_sha256'] == digest(expected_final[name])
            and worker['first_results'][name]['actual_count'] == len(pairs)
            and worker['final_results'][name]['actual_count'] == len(expected_final[name])
            for name, pairs in expected_first.items())
        oracle_pass.append(expected_ok and worker['candidate_edge_count'] == len(relation)
            and worker['decoy_edge_count'] == len(decoys)
            and worker['first_edge_count'] == len(first) and worker['second_edge_count'] == len(second)
            and worker['first_relation_sha256'] == digest(first)
            and worker['final_relation_sha256'] == digest(relation)
            and worker['decoy_relation_sha256'] == digest(decoys))
    current = runner.manifest()
    checks = {'capture_passed': capture['passed'],
        'capture_lock_hash': capture['lock_sha256'] == runner.sha(LOCK),
        'source_lock_current': current == lock['inputs'] == capture['locked_inputs'] == capture['post_run_inputs'],
        'expected_panel_set': expected_panels == observed_panels,
        'thirty_two_workers': len(capture['workers']) == 32,
        'independent_four_rule_oracle': all(oracle_pass),
        'all_first_phase_parity': all(r['parity'] for w in capture['workers'] for r in w['first_results'].values()),
        'all_final_phase_parity': all(r['parity'] for w in capture['workers'] for r in w['final_results'].values()),
        'empty_and_complete_controls': all((w['density'] != 0.0 or w['candidate_edge_count'] == 0)
            and (w['density'] != 1.0 or w['candidate_edge_count'] == runner.NODE_COUNT ** 2) for w in capture['workers'])}
    result = {'schema': 'BoundEdgeMatcherDifferentialV2Analysis', 'passed': all(checks.values()),
        'checks': checks, 'capture_sha256': runner.sha(CAPTURE), 'lock_sha256': runner.sha(LOCK),
        'analyzer_sha256': runner.sha(Path(__file__).resolve()),
        'workers_by_density': {str(d): sum(w['density'] == d for w in capture['workers']) for d in lock['densities']},
        'rule_shapes': lock['rules'],
        'interpretation_limit': 'Targeted four-shape generated-graph semantic differential; not a proof of all matcher or deletion/retraction semantics.'}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'passed': result['passed'], 'checks': checks, 'output': OUT.relative_to(ROOT).as_posix()}))
    return 0 if result['passed'] else 2

if __name__ == '__main__': raise SystemExit(main())
