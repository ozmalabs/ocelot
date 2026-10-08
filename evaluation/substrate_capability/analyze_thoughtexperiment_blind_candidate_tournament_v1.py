#!/usr/bin/env python3
"""Independent lifecycle, selection, isolation, and repeatability gates."""
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
import sys
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
RUNNER=ROOT/'evaluation/substrate_capability/thoughtexperiment_blind_candidate_tournament_v1.py'
ANALYZER=Path(__file__).resolve()
PROTOCOL=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_BLIND_CANDIDATE_TOURNAMENT_V1_PREREG_20261005.md'
SEED=ROOT/'seeds/self_change_reasoning.json';EDIT_OPS=ROOT/'domains/edit_ops.py'
BASELINE=ROOT/'evaluation/reports/blind_structural_repair_relation_evidence_v1_analysis_20261005.json'
SOURCES=('runners/dsl/Cargo.toml','runners/dsl/Cargo.lock','runners/dsl/src/graph.rs','runners/dsl/src/graph_rules.rs','runners/dsl/src/rewrite.rs','runners/dsl/src/substrate.rs','runners/dsl/src/py.rs','runners/dsl/python/substrate_rs/ext.py','runners/dsl/python/substrate_rs/_native.build.json')
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_blind_candidate_tournament_v1_lock_20261005.json'
CAPTURE=ROOT/'evaluation/reports/thoughtexperiment_blind_candidate_tournament_v1_20261005.json'
OUT=ROOT/'evaluation/reports/thoughtexperiment_blind_candidate_tournament_v1_analysis_20261005.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def frozen():
 from substrate_rs import _native
 paths=(RUNNER,ANALYZER,PROTOCOL,SEED,EDIT_OPS,BASELINE,*(ROOT/x for x in SOURCES));binary=Path(_native.__file__).resolve()
 return {'files':{str(p.relative_to(ROOT)):sha(p) for p in paths},'native_binary':{'path':str(binary),'sha256':sha(binary)}}
def main():
 lock=json.loads(LOCK.read_text());capture=json.loads(CAPTURE.read_text());errors=[]
 if frozen()!=lock['sources']:errors.append('source hashes differ from lock')
 if capture.get('lock_sha256')!=sha(LOCK):errors.append('capture lock hash mismatch')
 workers=capture.get('workers',[])
 if len(workers)!=lock['workers']:errors.append('worker count mismatch')
 case_sets=[]
 for worker in workers:
  if worker.get('sources_before')!=lock['sources'] or worker.get('sources_after')!=lock['sources']:errors.append(f"worker {worker.get('worker')} source mismatch")
  rows=worker.get('cases',[])
  if len(rows)!=lock['case_count']:errors.append('case count mismatch')
  case_sets.append({r.get('case_id'):r for r in rows})
  for row in rows:
   ids=[c['candidate_id'] for c in row.get('candidates',[])]
   if len(ids)!=len(set(ids)):errors.append(f"duplicate candidates {row.get('case_id')}")
   if row.get('candidate_count')!=len(ids):errors.append(f"candidate accounting mismatch {row.get('case_id')}")
   if row.get('revision_after_rehearsal')!=row.get('target_revision_initial'):errors.append(f"primary changed during rehearsal {row.get('case_id')}")
 if case_sets:
  first=case_sets[0]
  for other in case_sets[1:]:
   if set(other)!=set(first):errors.append('worker case IDs differ');continue
   for cid,a in first.items():
    b=other[cid]
    for key in ('candidate_count','candidates','noop_outputs','placebo_outputs','noop_gain','placebo_gain','selected_candidate_id','selected_count','revision_after_rehearsal','canary_outputs','commit_count','abort_count','abort_reason','final_outputs','revision_after_terminal','target_revision_initial','patch_status','patch_reason','graph_status'):
     if a.get(key)!=b.get(key):errors.append(f'worker semantic mismatch {cid}.{key}');break
 rows=list(case_sets[0].values()) if case_sets else []
 by={r['case_id']:r for r in rows}
 repair=by.get('opaque_repair_needed',{});no_repair=by.get('opaque_no_repair',{})
 # The graph selector sees only opaque IDs and evidence. Reconstruct the
 # uniquely eligible pool from trial measurements, not operator labels.
 eligible=[c['candidate_id'] for c in repair.get('candidates',[]) if c['gain']>repair.get('noop_gain',0)+5 and c['gain']>repair.get('placebo_gain',0)+5]
 if len(eligible)!=1 or repair.get('selected_candidate_id') not in eligible:errors.append('repair-needed graph selection did not choose the sole control-beating candidate')
 if repair.get('selected_count')!=1 or repair.get('canary_outputs')!=[True,True,True]:errors.append('repair-needed canary gate failed')
 if repair.get('commit_count')!=1 or repair.get('revision_after_terminal')!=repair.get('target_revision_initial',-1)+1:errors.append('repair-needed commit/revision gate failed')
 if repair.get('final_outputs')!=[True,True]:errors.append('repair-needed final holdout failed')
 if no_repair.get('selected_count')!=0 or no_repair.get('commit_count')!=0 or no_repair.get('abort_count')!=1:errors.append('no-repair case did not abstain and abort')
 if no_repair.get('revision_after_terminal')!=no_repair.get('target_revision_initial'):errors.append('no-repair target revision changed')
 time_fields=('noop_rehearsal_3x','placebo_rehearsal_3x','candidate_rehearsal','graph_selection')
 times={key:statistics.median(r['timing_ns'][key] for r in rows if key in r.get('timing_ns',{})) for key in time_fields} if rows else {}
 result={'schema':'ThoughtexperimentBlindCandidateTournamentV1Analysis','passed':not errors,'errors':errors,
  'summary':{'workers':len(workers),'case_count':len(rows),'repair_candidate_count':repair.get('candidate_count'),
   'repair_selected_count':repair.get('selected_count'),'repair_eligible_count':len(eligible),
   'repair_commits':repair.get('commit_count'),'no_repair_selected_count':no_repair.get('selected_count'),
   'no_repair_aborts':no_repair.get('abort_count'),'no_repair_revision_unchanged':no_repair.get('revision_after_terminal')==no_repair.get('target_revision_initial'),
   'median_phase_ns':times},
  'interpretation':'One fixed rule family and two task conditions; graph-native selection consumes measured outcomes, while task generation and the oracle remain harness supplied.'}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,sort_keys=True));return 0 if not errors else 1
if __name__=='__main__':raise SystemExit(main())
