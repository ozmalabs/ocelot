#!/usr/bin/env python3
"""Independent numerical audit for the K=16 scope replication."""
from __future__ import annotations
import hashlib, json, math, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'evaluation/reports/substrate_vision_k16_scope_multiseed_v1_1_20260927.json'
OUT = ROOT / 'evaluation/reports/substrate_vision_k16_scope_multiseed_v1_1_analysis_20260927.json'
SEEDS = (20260931, 20260932, 20260933)
TOL = 1e-10

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def osi(row):
    row = np.asarray(row, dtype=float)
    j = int(np.argmax(row)); jo = (j + len(row) // 2) % len(row)
    den = row[j] + row[jo]
    return float((row[j] - row[jo]) / den) if den > 1e-9 else 0.0

def main():
    data = json.loads(RAW.read_text())
    runs = data.get('runs', [])
    by_seed = {int(r['seed']): r for r in runs}
    checks = {
        'three_expected_seeds': set(by_seed) == set(SEEDS) and len(runs) == 3,
        'three_distinct_workers': len({r.get('pid') for r in runs}) == 3,
        'all_arms_are_full_rescan': all(a.get('variant', {}).get('executor') == 'full_rescan' for r in runs for a in r.get('arms', [])),
        'each_seed_has_global_and_scoped': all(len(by_seed[s].get('arms', [])) == 2 and {a['variant']['scope'] for a in by_seed[s]['arms']} == {'global', 'root_scoped'} for s in SEEDS) if set(by_seed) == set(SEEDS) else False,
        'complete_4x4_root_membership': all(a.get('n_units') == 16 and a.get('root_membership_count') == 16 for r in runs for a in r.get('arms', [])),
        'tuning_and_osi_are_finite': all(np.isfinite(np.asarray(a.get('tuning', []), dtype=float)).all() and np.isfinite(np.asarray(a.get('osi_per_unit', []), dtype=float)).all() for r in runs for a in r.get('arms', [])),
        'outputs_nonzero': all(float(np.max(np.asarray(a['tuning'], dtype=float))) > 0.0 for r in runs for a in r.get('arms', [])),
        'source_lock_stable': data.get('post_run_inputs') == data.get('locked_inputs') and all(r.get('started_inputs') == data.get('locked_inputs') == r.get('finished_inputs') for r in runs),
        'driver_gates_pass': data.get('pass') is True,
    }
    comparisons = []
    if set(by_seed) == set(SEEDS):
        for seed in SEEDS:
            arms = {a['variant']['scope']: a for a in by_seed[seed]['arms']}
            global_arm, scoped_arm = arms['global'], arms['root_scoped']
            gt = np.asarray(global_arm['tuning'], dtype=float); st = np.asarray(scoped_arm['tuning'], dtype=float)
            go = np.asarray(global_arm['osi_per_unit'], dtype=float); so = np.asarray(scoped_arm['osi_per_unit'], dtype=float)
            independent_g = np.asarray([osi(row) for row in gt]); independent_s = np.asarray([osi(row) for row in st])
            comparisons.append({'seed': seed, 'max_abs_tuning_delta': float(np.max(np.abs(gt-st))),
                                'max_abs_osi_delta': float(np.max(np.abs(go-so))),
                                'global_mean_osi': float(np.mean(independent_g)), 'root_scoped_mean_osi': float(np.mean(independent_s)),
                                'global_osi_recomputed': bool(np.allclose(go, independent_g, atol=TOL, rtol=0)),
                                'root_scoped_osi_recomputed': bool(np.allclose(so, independent_s, atol=TOL, rtol=0)),
                                'tuning_parity': bool(gt.shape == st.shape and gt.shape == (16, 12) and np.allclose(gt, st, atol=TOL, rtol=0))})
    checks['independent_osi_recomputation'] = all(c['global_osi_recomputed'] and c['root_scoped_osi_recomputed'] for c in comparisons)
    checks['per_seed_tuning_parity'] = len(comparisons) == 3 and all(c['tuning_parity'] for c in comparisons)
    checks['recognized_status_and_positive_progress'] = all(
        set(a.get(k, {})) <= {'fixed_point', 'repeated_graph_state'} and sum(a.get(k, {}).values()) > 0
        for r in runs for a in r.get('arms', []) for k in ('adaptation_status_counts', 'probe_status_counts'))
    payload = {'schema_version': 1, 'raw_sha256': sha(RAW), 'checks': checks, 'comparisons': comparisons,
               'pass': all(checks.values()),
               'interpretation': 'A parity pass supports exact K=16 tuning preservation for these three calibrated 4x4 single-sheet preparations under full-rescan closure. It does not estimate natural-task prevalence, demonstrate learned cortical selectivity, or establish a cost reduction.'}
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'output': str(OUT.relative_to(ROOT)), 'checks': checks, 'comparisons': comparisons}, indent=2))
    if not payload['pass']: raise SystemExit('independent multi-seed analysis failed')

if __name__ == '__main__': main()
