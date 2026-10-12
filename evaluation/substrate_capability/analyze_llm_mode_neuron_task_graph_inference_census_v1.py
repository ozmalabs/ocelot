#!/usr/bin/env python3
"""Independent integrity and semantic checks for the LLM graph inference census."""
from __future__ import annotations
import hashlib, json, math, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOCK = ROOT / 'evaluation/substrate_capability/llm_mode_neuron_task_graph_inference_census_v1_lock_20261002.json'
CAPTURE = ROOT / 'evaluation/reports/llm_mode_neuron_task_graph_inference_census_v1_20261002.json'
ANALYSIS = ROOT / 'evaluation/reports/llm_mode_neuron_task_graph_inference_census_v1_analysis_20261002.json'
TOL = 1e-8

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def close(a, b):
    return math.isfinite(float(a)) and math.isfinite(float(b)) and abs(float(a)-float(b)) < TOL

def main():
    lock = json.loads(LOCK.read_text())
    data = json.loads(CAPTURE.read_text())
    errors = []
    runs = data.get('runs', [])
    config = data.get('configuration', {})
    def require(condition, message):
        if not condition: errors.append(message)

    require(data.get('lock_sha256') == sha(LOCK), 'lock hash mismatch')
    require(data.get('sources') == lock.get('sources'), 'capture source lock differs')
    require(data.get('post_run_sources') == lock.get('sources'), 'post-run source drift')
    require(len(runs) == 3, 'expected three fresh workers')
    require(len({r.get('worker_pid') for r in runs}) == len(runs), 'worker PIDs are not distinct')
    require(config.get('heldout_rows_per_worker') == 10, 'configuration does not declare ten held-out rows')
    require(not data.get('failures'), 'worker failure recorded')
    flat = []
    for run_i, run in enumerate(runs):
        require(run.get('input_count') == 10 and len(run.get('rows', [])) == 10, f'worker {run_i}: held-out count mismatch')
        require(run.get('all_topologies_identical'), f'worker {run_i}: topology changed across inputs')
        require(run.get('source_lock_start') == lock.get('sources') == run.get('source_lock_end'), f'worker {run_i}: source drift')
        for row in run.get('rows', []):
            flat.append(row)
            idx = row.get('heldout_index')
            require(isinstance(idx, int) and 0 <= idx < 10, f'worker {run_i}: invalid input index')
            require(row.get('nodes') == 12, f'worker {run_i} input {idx}: expected 12 graph variables')
            require(row.get('connected') and row.get('component_count') == 1, f'worker {run_i} input {idx}: graph is disconnected')
            require(row.get('exact_extraction') is True, f'worker {run_i} input {idx}: factor extraction mismatch')
            require(row.get('minfill_width_certificate') == row.get('triangulation_width'), f'worker {run_i} input {idx}: width certificate mismatch')
            require(close(row.get('jt_energy'), row.get('oracle_energy')), f'worker {run_i} input {idx}: JT differs from independent VE')
            require(close(row.get('direct_rescore'), row.get('oracle_energy')), f'worker {run_i} input {idx}: returned state rescore mismatch')
            require(row.get('no_mutation') is True, f'worker {run_i} input {idx}: input graph mutated')
            target, pred = row.get('mode_target', []), row.get('mode_prediction', [])
            require(len(target) == len(pred) == 4, f'worker {run_i} input {idx}: mode result size mismatch')
            if len(target) == len(pred) and target:
                agreement = sum(float(a) == float(b) for a, b in zip(target, pred))/len(target)
                require(close(row.get('mode_sign_agreement'), agreement), f'worker {run_i} input {idx}: agreement summary mismatch')
            timing = row.get('timing_ns', {})
            require(all(isinstance(timing.get(k), int) and timing[k] >= 0 for k in ('graph_construction','runtime_extraction','minfill_order','oracle','junction_tree')),
                    f'worker {run_i} input {idx}: invalid timing record')
    require(len(flat) == 30, 'expected thirty total input rows')
    summary = {
        'workers': len(runs), 'input_rows': len(flat),
        'all_connected': all(r.get('connected') for r in flat),
        'all_exact_extractions': all(r.get('exact_extraction') for r in flat),
        'max_width_certificate': max((r.get('minfill_width_certificate', -1) for r in flat), default=-1),
        'mean_mode_sign_agreement': (sum(r.get('mode_sign_agreement', 0.0) for r in flat)/len(flat)) if flat else None,
        'energy_oracle_max_abs_delta': max((abs(float(r['jt_energy'])-float(r['oracle_energy'])) for r in flat), default=None),
        'median_junction_tree_ms': sorted(r['timing_ns']['junction_tree']/1e6 for r in flat)[len(flat)//2] if flat else None,
        'median_graph_construction_ms': sorted(r['timing_ns']['graph_construction']/1e6 for r in flat)[len(flat)//2] if flat else None,
    }
    result = {'schema':'LlmModeNeuronTaskGraphInferenceCensusV1Analysis','gates_pass':not errors,'errors':errors,'summary':summary}
    ANALYSIS.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if errors else 0

if __name__ == '__main__':
    sys.exit(main())
