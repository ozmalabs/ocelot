#!/usr/bin/env python3
"""Independent semantic and provenance audit for read-only boundary replay."""
import hashlib,json,random
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/substrate_conversation_readonly_boundary_v1_20260926.json'
LOCK=ROOT/'evaluation/substrate_capability/conversation_readonly_boundary_lock_20260926.json'
SIZES=(1,2,4,8);REPS=3;ARMS=('full','scoped');SEED=20260925
PATHS={'protocol_sha256':ROOT/'docs/research/engine_substrate/SUBSTRATE_CONVERSATION_READONLY_BOUNDARY_PREREG_20260926.md','runner_sha256':ROOT/'scripts/substrate_conversation_readonly_boundary_v1.py','analyzer_sha256':ROOT/'scripts/analyze_substrate_conversation_readonly_boundary_v1.py','seed_sha256':ROOT/'seeds/conversation_deliberation_phase4a.json','materializer_sha256':ROOT/'domains/conversation_deliberation.py','rewrite_sha256':ROOT/'runners/dsl/src/rewrite.rs','substrate_sha256':ROOT/'runners/dsl/src/substrate.rs','py_binding_sha256':ROOT/'runners/dsl/src/py.rs'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 d=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());runs=d['runs'];expected=[(n,r,a) for n in SIZES for r in range(REPS) for a in ARMS];random.Random(SEED).shuffle(expected)
 actual={(x['size'],x['replicate'],x['arm']):x for x in runs};checks={
 'raw_lock_equal':d['locked_inputs']==lock,
 'lock_hash_equal':d['lock_sha256']==sha(LOCK),
 'source_hashes_current':lock=={k:sha(v) for k,v in PATHS.items()},
 'worker_count_24':len(runs)==24,
 'unique_worker_processes':len({x['pid'] for x in runs})==24,
 'complete_balanced_matrix':len(actual)==24 and set(actual)==set(expected),
 'locked_randomized_schedule':d['schedule']==[list(x) for x in expected],
 'all_workers_fixed_point':all(x['outcome']['status']=='fixed_point' for x in runs),
 'all_expected_decisions':all(x['all_expected_task_outcomes'] and all(x['expected_task_outcomes']) for x in runs),
 'read_only_boundary_topology':all(x['boundary_count']==x['size']-1 and x['boundary_owner_sizes']==[2]*(x['size']-1) and x['boundary_candidate_edges']==2*(x['size']-1) for x in runs),
 'mutable_candidates_frame_local':all(x['mutable_candidate_ids_unique'] and set(x['candidate_owner_sizes'])=={1} for x in runs),
 'scoring_rule_reads_shared_boundary':all(x['scoring_rule_boundary_read'] for x in runs),
 'native_hash_consistent':len({x['native_extension_sha256'] for x in runs})==1 and all(x['native_extension_sha256']==d['native_extension_sha256'] for x in runs)}
 parity=[]
 for n in SIZES:
  for r in range(REPS):
   f,s=actual[n,r,'full'],actual[n,r,'scoped'];parity.append({'size':n,'replicate':r,'projection_equal':f['projection']==s['projection'],'fixed_point_both':f['outcome']['status']==s['outcome']['status']=='fixed_point','expected_winners_equal':f['expected_winners']==s['expected_winners']})
 checks['exact_full_scoped_projection_parity']=all(x['projection_equal'] and x['fixed_point_both'] and x['expected_winners_equal'] for x in parity)
 recomputed=[]
 for n in SIZES:
  for r in range(REPS):
   f,s=actual[n,r,'full'],actual[n,r,'scoped']
   recomputed.append({'size':n,'replicate':r,'projection_equal':f['projection']==s['projection'],'fixed_point_both':f['outcome']['status']==s['outcome']['status']=='fixed_point','full_candidates':f['scale_audit'].get('cand_enum',0),'scoped_candidates':s['scale_audit'].get('cand_enum',0),'full_term_evaluations':f['scale_audit'].get('term_evals_total',0),'scoped_term_evaluations':s['scale_audit'].get('term_evals_total',0),'full_wall_ns':f['wall_ns'],'scoped_wall_ns':s['wall_ns'],'scoped_frame_turns':s['frame_turns']})
 checks['parent_pair_table_matches_independent_recompute']=d['paired']==recomputed
 report={'audit':'independent semantic/provenance audit','checks':checks,'all_checks_pass':all(checks.values()),'projection_parity_pairs_by_size':{str(n):sum(p['projection_equal'] for p in parity if p['size']==n) for n in SIZES},'paired':parity,'raw_sha256':sha(RAW),'lock_sha256':sha(LOCK),'claim_boundary':d['claim_boundary']}
 out=ROOT/'evaluation/reports/substrate_conversation_readonly_boundary_v1_analysis_20260926.json';out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps({'analysis':str(out),'checks':checks,'all_checks_pass':report['all_checks_pass'],'parity':report['projection_parity_pairs_by_size']},indent=2))
if __name__=='__main__':main()
