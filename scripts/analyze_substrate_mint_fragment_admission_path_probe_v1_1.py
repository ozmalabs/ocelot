#!/usr/bin/env python3
"""Independent route, checker, lock, and worker analysis for admission probe v1."""
from __future__ import annotations
import hashlib,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/substrate_mint_fragment_admission_path_probe_v1_1_20260928.json'
LOCK=ROOT/'evaluation/substrate_capability/mint_fragment_admission_path_probe_v1_1_lock_20260928.json'
OUT=ROOT/'evaluation/reports/substrate_mint_fragment_admission_path_probe_v1_1_analysis_20260928.json'
ROUTES=('direct_add_rule','checkpoint_import','rule_patch_revision','graph_rule_self_mint')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());runs=raw.get('runs',[])
 route_rows=[(r,route) for r in runs for route in r.get('routes',[])]
 checks={
  'runner_gates_pass':bool(raw.get('all_checks_pass')) and all(raw.get('checks',{}).values()),
  'three_unique_worker_pids':len(runs)==3 and len({r.get('pid') for r in runs})==3,
  'all_route_cells_present_once_per_worker':all(tuple(sorted(x.get('route') for x in r.get('routes',[])))==tuple(sorted(ROUTES)) for r in runs),
  'checker_rejects_negative_fixture_each_worker':all(not r.get('checker',{}).get('accepted') and bool(r.get('checker',{}).get('reasons')) for r in runs),
  'all_four_routes_accept_out_of_fragment_rule':len(route_rows)==12 and all(row.get('accepted') for _,row in route_rows),
  'direct_and_import_make_one_live_rule':all(row.get('rule_count')==1 for _,row in route_rows if row.get('route') in ('direct_add_rule','checkpoint_import')),
  'patch_commits_new_effect_revision':all(row.get('after',{}).get('revision')==row.get('before',{}).get('revision',-1)+1 and row.get('receipt',{}).get('revision')==1 for _,row in route_rows if row.get('route')=='rule_patch_revision'),
  'self_mint_installs_but_does_not_fire_new_rule':all(row.get('minted_rule_count')==1 and row.get('rule_count_after')==row.get('rule_count_before',-1)+1 and row.get('trigger_edge_absent') and row.get('cycle_report',{}).get('steps',0)>0 for _,row in route_rows if row.get('route')=='graph_rule_self_mint'),
  'source_locks_match_workers_and_checkout':raw.get('locked_inputs')==lock.get('locked_inputs')==raw.get('post_run_inputs') and all(r.get('before')==lock.get('locked_inputs')==r.get('after') for r in runs),
  'raw_and_lock_hashes_recorded':bool(sha(RAW)) and bool(sha(LOCK)),
 }
 analysis={'schema_version':1,'analysis_id':'substrate-mint-fragment-admission-path-probe-v1-1-independent-analysis','raw_sha256':sha(RAW),'lock_sha256':sha(LOCK),'checks':checks,'all_checks_pass':all(checks.values()),'route_acceptance_counts':{name:sum(row.get('accepted') is True for _,row in route_rows if row.get('route')==name) for name in ROUTES},'claim_boundary':'Exact route behavior only: current runtime routes accept this checker-rejected fresh-mint syntax. The probe never executes closure on the out-of-fragment rule and does not establish general termination or exhaustive route coverage.'}
 OUT.write_text(json.dumps(analysis,indent=2,sort_keys=True)+'\n');print(json.dumps({'analysis':str(OUT.relative_to(ROOT)),'checks':checks,'all_checks_pass':analysis['all_checks_pass'],'route_acceptance_counts':analysis['route_acceptance_counts']},indent=2))
 if not analysis['all_checks_pass']:raise SystemExit('independent admission-path analysis failed')
if __name__=='__main__':main()
