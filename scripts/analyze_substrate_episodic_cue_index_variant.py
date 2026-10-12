#!/usr/bin/env python3
"""Independent checks and paired comparison for cue-index variant v3."""
import hashlib, json, math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
run=json.loads((ROOT/'evaluation/reports/substrate_episodic_cue_index_variant_v3_20260925.json').read_text())
lock=json.loads((ROOT/'docs/research/engine_substrate/SUBSTRATE_EPISODIC_CUE_INDEX_VARIANT_LOCK_V3_20260925.json').read_text())
checks={}
checks['run_id_locked']=run['run_id']==lock['run_id']
checks['locked_sources_match_run']=run['source_sha256']==lock['source_sha256']
checks['current_harness_and_prereg_match_lock']=all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in lock['source_sha256'].items())
checks['all_harness_checks_pass']=all(run['checks'].values())
checks['all_32_cells_present']=len(run['runs'])==32
checks['all_response_pairs_exact'] = all(x['readers']['control']['state_summary']==x['readers']['control']['expected_summary'] and x['readers']['control']['state_summary']==x['readers']['audit']['state_summary'] for x in run['runs'])
checks['confidence_values_within_1e_12']=all(math.isclose(x['readers']['control']['confidence'],.5 if x['workload']=='collision' else .85,abs_tol=1e-12) for x in run['runs'])
comparisons={}
for workload in ('unique','collision'):
 for n in (6,24,78,192):
  base=run['summary'][f'baseline/{workload}/{n}']; opt=run['summary'][f'request_count/{workload}/{n}']
  comparisons[f'{workload}/{n}']={
   'baseline_control_tick_ms_median':base['control_tick_ms_median'],
   'request_count_control_tick_ms_median':opt['control_tick_ms_median'],
   'wall_time_ratio_request_over_baseline':opt['control_tick_ms_median']/base['control_tick_ms_median'],
   'candidate_tests_baseline':base['all_candidate_tests_per_query'],
   'candidate_tests_request_count':opt['all_candidate_tests_per_query'],
   'candidate_tests_reduction_fraction':1-opt['all_candidate_tests_per_query']/base['all_candidate_tests_per_query'],
   'term_evals_baseline':base['term_evals_total_per_query'],
   'term_evals_request_count':opt['term_evals_total_per_query'],
   'term_evals_reduction_fraction':1-opt['term_evals_total_per_query']/base['term_evals_total_per_query'],
   'baseline_pair_rule_candidate_tests':base['pair_rule_candidate_tests_per_query'],
   'request_count_retrieve_rule_term_evals':opt['retrieve_rule_term_evals_per_query'],
  }
checks={k:bool(v) for k,v in checks.items()}
out={'schema_version':1,'run_id':run['run_id'],'checks':checks,'comparisons':comparisons,'claim_boundary':'Two synthetic workloads; N<=192; two replicates/cell. Response-level parity only. Count/Filter and retrieval still scan episode records. Does not establish natural-task tractability, scaling beyond measured range, persistent collision-state parity, concurrent semantics, or rung 3/4 learning.'}
path=ROOT/'evaluation/reports/substrate_episodic_cue_index_variant_v3_analysis_20260925.json'
path.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,indent=2))
if not all(checks.values()): raise SystemExit('analysis checks failed')
