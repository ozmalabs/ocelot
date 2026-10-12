#!/usr/bin/env python3
import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
run=json.loads((R/'evaluation/reports/substrate_episodic_cue_native_index_join_v2_20260925.json').read_text())
lock=json.loads((R/'docs/research/engine_substrate/SUBSTRATE_EPISODIC_CUE_INDEXED_JOIN_LOCK_V2_20260925.json').read_text())
checks={'run_id_locked':run['run_id']==lock['run_id'],'raw_hashes_match_lock':run['source_sha256']==lock['source_sha256'],'current_locked_inputs_match':all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in lock['source_sha256'].items()),'all_preregistered_checks_pass':all(run['checks'].values()),'48_cells_present':len(run['runs'])==48}
comparisons={}
for w in ('unique','collision'):
 for n in (6,24,78,192):
  vals={}
  for v in ('baseline','request_count','request_indexed'):
   x=run['summary'][f'{v}/{w}/{n}']
   vals[v]={k:x[k] for k in ('control_tick_ms_median','all_candidate_tests_per_query','all_where_evaluations_per_query','term_evals_total_per_query','candidate_pairs_hinted_per_query','retrieve_rule_candidate_tests_per_query','retrieve_rule_term_evals_per_query')}
  a=vals['request_count'];b=vals['request_indexed']
  vals['indexed_vs_count']={'retrieval_candidate_reduction_fraction':1-b['retrieve_rule_candidate_tests_per_query']/a['retrieve_rule_candidate_tests_per_query'],'all_candidate_reduction_fraction':1-b['all_candidate_tests_per_query']/a['all_candidate_tests_per_query'],'term_eval_reduction_fraction':1-b['term_evals_total_per_query']/a['term_evals_total_per_query'],'wall_ratio':b['control_tick_ms_median']/a['control_tick_ms_median']}
  comparisons[f'{w}/{n}']=vals
out={'schema_version':1,'run_id':run['run_id'],'engine_build_id':lock['engine_build_id'],'checks':checks,'comparisons':comparisons,'interpretation':'The cue index hint prunes the retrieval rule match-edge candidates to a constant small set over N=6..192 in these unique and one-collision synthetic workloads. Other rules still account for many global candidate tests and where evaluations. Exact responses match; prototypes still do not persist baseline collision marks. Two replicates are descriptive only.'}
(R/'evaluation/reports/substrate_episodic_cue_native_index_join_analysis_20260925.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,indent=2))
if not all(checks.values()): raise SystemExit('indexed join analysis failed')
