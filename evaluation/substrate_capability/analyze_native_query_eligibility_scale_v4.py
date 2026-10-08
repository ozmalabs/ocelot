#!/usr/bin/env python3
"""Independent lock, oracle, and cost-curve analysis for query eligibility v1."""
from __future__ import annotations
import hashlib, json, math, statistics, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'evaluation/substrate_capability'))
import native_query_eligibility_scale_v4 as runner

CAPTURE = ROOT / 'evaluation/reports/native_query_eligibility_scale_v4_20261005.json'
LOCK = ROOT / 'evaluation/substrate_capability/native_query_eligibility_scale_v4_lock_20261005.json'
OUT = ROOT / 'evaluation/reports/native_query_eligibility_scale_v4_analysis_20261005.json'

def percentile90(values):
    ordered = sorted(values)
    return ordered[math.ceil(.9 * len(ordered)) - 1]

def oracle(size, seed):
    import random
    predictions = [bool(i % 2) for i in range(size)]
    random.Random(seed).shuffle(predictions)
    ranks = list(range(size)); random.Random(seed ^ 0x5A17).shuffle(ranks)
    eligible = [i for i, positive in enumerate(predictions) if positive]
    selected = min(eligible, key=lambda i: ranks[i])
    digest = hashlib.sha256(json.dumps(eligible, separators=(',', ':')).encode()).hexdigest()
    return len(eligible), digest, selected, ranks[selected]

def main():
    capture = json.loads(CAPTURE.read_text()); lock = json.loads(LOCK.read_text())
    expected_panels = {(p['size'], p['replicate'], p['seed']) for p in lock['panels']}
    observed_panels = {(w['size'], w['replicate'], w['seed']) for w in capture['workers']}
    oracle_checks = []
    for worker in capture['workers']:
        count, digest, selected, selected_rank = oracle(worker['size'], worker['seed'])
        oracle_checks.append(worker['prediction_positive_count'] == count
            and worker['eligible_count'] == count
            and worker['eligible_ordinals_sha256'] == digest
            and worker['expected_eligible_ordinals_sha256'] == digest
            and worker['selected_ordinal'] == selected
            and worker['expected_selected_ordinal'] == selected
            and worker['selected_rank'] == selected_rank
            and worker['eligible_identity_parity'] and worker['selected_identity_parity'])
    current_inputs = runner.manifest()
    grouped = {}
    for size in lock['sizes']:
        group = [w for w in capture['workers'] if w['size'] == size]
        grouped[str(size)] = {'replicates': len(group)}
        for field in ('graph_build_ns', 'eligibility_closure_ns', 'selection_closure_ns',
                      'worker_cpu_ns', 'worker_wall_ns', 'peak_rss_kib'):
            values = [w[field] for w in group]
            grouped[str(size)][field] = {'median': statistics.median(values), 'p90': percentile90(values)}
        grouped[str(size)]['eligible_fraction'] = statistics.mean(w['eligible_count'] / size for w in group)
    checks = {
        'capture_passed': capture['passed'],
        'capture_lock_hash': capture['lock_sha256'] == runner.sha(LOCK),
        'source_lock_current': current_inputs == lock['inputs'] == capture['locked_inputs'] == capture['post_run_inputs'],
        'expected_panel_set': observed_panels == expected_panels,
        'twenty_five_workers': len(capture['workers']) == 25,
        'independent_oracle_replay': all(oracle_checks),
        'all_timings_positive': all(w[k] > 0 for w in capture['workers'] for k in
            ('graph_build_ns', 'eligibility_closure_ns', 'selection_closure_ns', 'worker_cpu_ns', 'worker_wall_ns')),
        'five_replicates_each_size': all(grouped[str(size)]['replicates'] == 5 for size in lock['sizes']),
    }
    result = {'schema': 'NativeQueryEligibilityScaleV4Analysis', 'passed': all(checks.values()),
        'checks': checks, 'capture_sha256': runner.sha(CAPTURE), 'lock_sha256': runner.sha(LOCK),
        'analyzer_sha256': runner.sha(Path(__file__).resolve()), 'by_size': grouped,
        'interpretation_limit': 'Graph-level cost curve for the v1.3 authored native rule shape; five population sizes on one host do not prove asymptotic complexity or task-natural applicability.'}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'passed': result['passed'], 'checks': checks, 'output': OUT.relative_to(ROOT).as_posix()}))
    return 0 if result['passed'] else 2

if __name__ == '__main__': raise SystemExit(main())
