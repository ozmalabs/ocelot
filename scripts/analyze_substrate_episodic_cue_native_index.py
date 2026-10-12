#!/usr/bin/env python3
import hashlib,json,math
from pathlib import Path
R=Path(__file__).resolve().parents[1]
run=json.loads((R/'evaluation/reports/substrate_episodic_cue_native_index_20260925.json').read_text())
lock=json.loads((R/'docs/research/engine_substrate/SUBSTRATE_EPISODIC_CUE_NATIVE_INDEX_LOCK_V2_20260925.json').read_text())
checks={'run_id_locked':run['run_id']==lock['run_id'],'raw_hashes_match_lock':run['source_sha256']==lock['source_sha256'],'current_locked_inputs_match':all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in lock['source_sha256'].items()),'harness_checks_pass':all(run['checks'].values()),'48_cells_present':len(run['runs'])==48}
comparisons={}
for w in ('unique','collision'):
 for n in (6,24,78,192):
  row={}
  for v in ('baseline','request_count','request_indexed'):
   x=run['summary'][f'{v}/{w}/{n}']
   row[v]={k:x[k] for k in ('control_tick_ms_median','all_candidate_tests_per_query','all_where_evaluations_per_query','term_evals_total_per_query','retrieve_rule_candidate_tests_per_query','retrieve_rule_term_evals_per_query','filter_term_evals_per_query')}
  row['indexed_vs_request_count']={'wall_ratio':row['request_indexed']['control_tick_ms_median']/row['request_count']['control_tick_ms_median'],'candidate_tests_delta':row['request_indexed']['all_candidate_tests_per_query']-row['request_count']['all_candidate_tests_per_query'],'term_eval_reduction_fraction':1-row['request_indexed']['term_evals_total_per_query']/row['request_count']['term_evals_total_per_query'],'retrieve_term_reduction_fraction':1-row['request_indexed']['retrieve_rule_term_evals_per_query']/row['request_count']['retrieve_rule_term_evals_per_query']}
  comparisons[f'{w}/{n}']=row
out={'schema_version':1,'run_id':run['run_id'],'checks':checks,'comparisons':comparisons,'interpretation':'At N=192 the native attr index leaves rule candidate tests and where evaluations unchanged, showing retrieval match enumeration still visits the episode population. It removes Filter term evaluations and cuts retrieval-rule term evaluations substantially; end-to-end wall change is smaller. Exact response semantics passed in the synthetic workload; the persistent collision-mark side effect remains intentionally absent in both prototypes.'}
(R/'evaluation/reports/substrate_episodic_cue_native_index_analysis_20260925.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,indent=2))
if not all(checks.values()): raise SystemExit('native index analysis failed')
