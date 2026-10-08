#!/usr/bin/env python3
"""Independent integrity, task, selection, and full-phase timing analysis."""
import hashlib,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
RUNNER=ROOT/'evaluation/substrate_capability/thoughtexperiment_blind_candidate_tournament_v2.py'
ANALYZER=Path(__file__).resolve();PROTOCOL=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_BLIND_CANDIDATE_TOURNAMENT_V2_PREREG_20261005.md'
FIXTURE=ROOT/'evaluation/substrate_capability/thoughtexperiment_blind_candidate_tournament_v2_fixture_20261005.json'
SEED=ROOT/'seeds/self_change_reasoning.json';EDIT_OPS=ROOT/'domains/edit_ops.py'
BASELINE=ROOT/'evaluation/reports/thoughtexperiment_blind_candidate_tournament_v1_analysis_20261005.json'
SOURCES=('runners/dsl/Cargo.toml','runners/dsl/Cargo.lock','runners/dsl/src/graph.rs','runners/dsl/src/graph_rules.rs','runners/dsl/src/rewrite.rs','runners/dsl/src/substrate.rs','runners/dsl/src/py.rs','runners/dsl/python/substrate_rs/ext.py','runners/dsl/python/substrate_rs/_native.build.json')
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_blind_candidate_tournament_v2_lock_20261005.json'
CAPTURE=ROOT/'evaluation/reports/thoughtexperiment_blind_candidate_tournament_v2_20261005.json'
OUT=ROOT/'evaluation/reports/thoughtexperiment_blind_candidate_tournament_v2_analysis_20261005.json'
PHASES=('candidate_generation','noop_rehearsal_3x','placebo_rehearsal_3x','candidate_rehearsal_pool','graph_selection','canary_rehearsal_3x','canary_commit_tick','final_verification','abort_close_tick')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def frozen():
 from substrate_rs import _native
 paths=(RUNNER,ANALYZER,PROTOCOL,FIXTURE,SEED,EDIT_OPS,BASELINE,*(ROOT/x for x in SOURCES));binary=Path(_native.__file__).resolve()
 return {'files':{str(p.relative_to(ROOT)):sha(p) for p in paths},'native_binary':{'path':str(binary),'sha256':sha(binary)}}
def main():
 lock=json.loads(LOCK.read_text());capture=json.loads(CAPTURE.read_text());errors=[]
 fixture_by_id={case['case_id']:case for case in json.loads(FIXTURE.read_text())['cases']}
 if frozen()!=lock['sources']:errors.append('source hashes differ from lock')
 if capture.get('lock_sha256')!=sha(LOCK):errors.append('capture lock hash mismatch')
 workers=capture.get('workers',[])
 if len(workers)!=lock['workers']:errors.append('worker count mismatch')
 sets=[]
 semantic_keys=('candidate_count','candidates','noop_outputs','placebo_outputs','noop_gain','placebo_gain','selected_candidate_id','selected_count','revision_after_rehearsal','canary_outputs','commit_count','abort_count','abort_reason','final_outputs','target_revision_initial','revision_after_terminal','patch_status','patch_reason','graph_status')
 for worker in workers:
  if worker.get('sources_before')!=lock['sources'] or worker.get('sources_after')!=lock['sources']:errors.append(f"worker {worker.get('worker')} source mismatch")
  rows=worker.get('cases',[])
  if len(rows)!=lock['case_count']:errors.append('case count mismatch')
  sets.append({r.get('case_id'):r for r in rows})
  for row in rows:
   ids=[c.get('candidate_id') for c in row.get('candidates',[])]
   if len(ids)!=len(set(ids)):errors.append(f"duplicate candidates in {row.get('case_id')}")
   if row.get('candidate_count')!=len(ids):errors.append(f"candidate count mismatch in {row.get('case_id')}")
   if row.get('revision_after_rehearsal')!=row.get('target_revision_initial'):errors.append(f"primary changed during rehearsal in {row.get('case_id')}")
   if set(row.get('timing_ns',{}))!=set(PHASES):errors.append(f"timing phases missing in {row.get('case_id')}")
 if sets:
  base=sets[0]
  for other in sets[1:]:
   if set(other)!=set(base):errors.append('worker case IDs differ');continue
   for cid,a in base.items():
    b=other[cid]
    for key in semantic_keys:
     if a.get(key)!=b.get(key):errors.append(f"worker mismatch {cid}.{key}");break
 rows=list(sets[0].values()) if sets else [];by={r['case_id']:r for r in rows}
 repair_ids=('opaque_01','opaque_03');abstain_ids=('opaque_02','opaque_04','opaque_05','opaque_06')
 for cid in repair_ids:
  row=by.get(cid,{})
  eligible=[c['candidate_id'] for c in row.get('candidates',[]) if c['gain']>row.get('noop_gain',0)+5 and c['gain']>row.get('placebo_gain',0)+5]
  if len(eligible)!=1 or row.get('selected_candidate_id') not in eligible:errors.append(f'{cid} did not select its sole control-beating candidate')
  if row.get('selected_count')!=1 or row.get('commit_count')!=1:errors.append(f'{cid} selection/commit failed')
  if row.get('patch_status')!='committed' or row.get('patch_reason')!='ok':errors.append(f'{cid} RulePatch receipt failed')
  if row.get('revision_after_terminal')!=row.get('target_revision_initial',-1)+1:errors.append(f'{cid} revision did not advance once')
  case=fixture_by_id[cid]
  if any(p!=s['expected'] for p,s in zip(row.get('canary_outputs',[]),case['canary'])):errors.append(f'{cid} canary mismatch')
  if len(row.get('canary_outputs',[]))!=len(case['canary']):errors.append(f'{cid} canary length mismatch')
  if any(p!=s['expected'] for p,s in zip(row.get('final_outputs',[]),case['final'])):errors.append(f'{cid} final holdout mismatch')
  if len(row.get('final_outputs',[]))!=len(case['final']):errors.append(f'{cid} final length mismatch')
 for cid in abstain_ids:
  row=by.get(cid,{})
  if row.get('selected_count')!=0 or row.get('commit_count')!=0 or row.get('abort_count')!=1:errors.append(f'{cid} did not abstain/abort')
  if row.get('revision_after_terminal')!=row.get('target_revision_initial'):errors.append(f'{cid} changed target revision')
 ambiguous=by.get('opaque_05',{})
 if ambiguous.get('noop_gain')!=10 or not any(c.get('operator_hidden')=='shift_numeric_literal' and c.get('gain')==10 for c in ambiguous.get('candidates',[])):
  errors.append('ambiguous threshold training control was not represented as expected')
 relation=by.get('opaque_06',{})
 relation_rows=[c for c in relation.get('candidates',[]) if c.get('operator_hidden')=='add_match_edge']
 if not relation_rows:errors.append('irrelevant relation proposal was not generated')
 if any(c['gain']>relation.get('noop_gain',0)+5 for c in relation_rows):errors.append('irrelevant relation unexpectedly cleared control margin')
 per_phase={}
 for phase in PHASES:
  samples=[r['timing_ns'][phase] for r in rows if r.get('timing_ns',{}).get(phase,0)>0]
  per_phase[phase]={'observations':len(samples),'median_ns':statistics.median(samples) if samples else None}
 full_success=[]
 for cid in repair_ids:
  t=by.get(cid,{}).get('timing_ns',{})
  full_success.append(sum(t.get(k,0) for k in ('candidate_generation','noop_rehearsal_3x','placebo_rehearsal_3x','candidate_rehearsal_pool','graph_selection','canary_rehearsal_3x','canary_commit_tick','final_verification')))
 result={'schema':'ThoughtexperimentBlindCandidateTournamentV2Analysis','passed':not errors,'errors':errors,
  'summary':{'workers':len(workers),'case_count':len(rows),'repair_cases_committed':sum(by.get(cid,{}).get('commit_count',0)==1 for cid in repair_ids),
   'abstention_cases':len(abstain_ids),'relation_candidate_count':len(relation_rows),
   'ambiguous_training_abstained':ambiguous.get('selected_count')==0,
   'full_measured_lifecycle_ns_median':statistics.median(full_success) if full_success else None,
   'phase_timings':per_phase},
  'interpretation':'Two edit families and four abstention/distractor controls on six authored cases; task construction and labels remain harness supplied.'}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,sort_keys=True));return 0 if not errors else 1
if __name__=='__main__':raise SystemExit(main())
