#!/usr/bin/env python3
"""Independent integrity review for the full shape-axis candidate capture."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_shape_axis_full_candidate_admission_v1_lock_20261002.json'
RAW=ROOT/'evaluation/reports/thoughtexperiment_shape_axis_full_candidate_admission_v1_raw_20261002.json'
OUT=ROOT/'evaluation/reports/thoughtexperiment_shape_axis_full_candidate_admission_v1_review_20261002.json'
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def main()->int:
 lock=json.loads(LOCK.read_text());raw=json.loads(RAW.read_text());ws=raw['workers']
 expected={x['label']:x['digest'] for x in ws[0]['candidate_descriptors']}
 checks={
  'schema_and_lock_link':raw.get('schema')=='ShapeAxisFullCandidateAdmissionV1Capture' and raw.get('lock')==lock,
  'capture_source_lock_parity':lock['sources']==raw.get('source_before')==raw.get('source_after'),
  'semantic_engine_parity':lock.get('semantic_engine')==raw.get('semantic_engine'),
  'four_fresh_workers':len(ws)==4 and len({w['pid'] for w in ws})==4,
  'worker_source_stability':all(w.get('source_stable') and w['source_before']==w['source_after']==lock['sources'] for w in ws),
  'same_six_unique_candidates':all(w['candidate_count']==6 and len(w['candidate_descriptors'])==6 and
    len({x['label'] for x in w['candidate_descriptors']})==6 and
    {x['label']:x['digest'] for x in w['candidate_descriptors']}==expected for w in ws),
  'complete_train_and_heldout_matrices':all(len(w['training_outcomes'])==6 and len(w['heldout_outcomes'])==6 and
    {x['label'] for x in w['training_outcomes']}==set(expected) and
    {x['label'] for x in w['heldout_outcomes']}==set(expected) for w in ws),
  'disjoint_train_and_heldout_cases':all(w['disjoint_cases'] and
    not set(w['training_case_ids'])&set(w['heldout_case_ids']) for w in ws),
  'primary_state_preserved':all(x['primary_preserved'] for w in ws for x in w['training_outcomes']+w['heldout_outcomes']),
  'oracle_recomputed_for_every_candidate':all(all(set(x['oracle'])=={'all_observations_settled','one_axis_per_signature','native_fixed_point','candidate_applied'}
    and x['utility']==float(all(x['oracle'].values())) for x in w['training_outcomes']+w['heldout_outcomes']) for w in ws),
  'candidate_costs_present':all(all(set(x['cost_ns'])=={'context_setup_ns','enumeration_ns','branch_creation_ns','candidate_patch_ns','task_closure_ns','candidate_total_ns'}
    and all(isinstance(v,int) and v>=0 for v in x['cost_ns'].values()) for x in w['training_outcomes']+w['heldout_outcomes']) for w in ws),
  'heldout_utility_has_success_and_failure':all(any(x['utility']==1 for x in w['heldout_outcomes']) and any(x['utility']==0 for x in w['heldout_outcomes']) for w in ws),
 }
 per_worker=[]
 for w in ws:
  per_worker.append({'worker':w['worker'],'pid':w['pid'],
   'heldout_utility':{x['label']:x['utility'] for x in w['heldout_outcomes']},
   'heldout_candidate_total_ns':{x['label']:x['cost_ns']['candidate_total_ns'] for x in w['heldout_outcomes']}})
 report={'schema':'ShapeAxisFullCandidateAdmissionV1Review','raw_sha256':sha(RAW),'lock_sha256':sha(LOCK),
  'checks':checks,'passed':sum(checks.values()),'total':len(checks),'valid':all(checks.values()),'per_worker':per_worker,
  'scope_limit':'four process replications of one authored shape-axis oracle; not a ranker utility or generalization result'}
 serialized=json.dumps(report,indent=2,sort_keys=True)+'\n'
 if OUT.exists():
  if OUT.read_text()!=serialized:raise SystemExit('review evidence changed; preserve existing output and write a new version')
 else:OUT.write_text(serialized)
 print(json.dumps({'passed':report['passed'],'total':report['total'],'valid':report['valid'],'capture_matches_current_inputs':OUT.read_text()==serialized,'review':OUT.relative_to(ROOT).as_posix()},sort_keys=True))
 return 0 if report['valid'] else 1
if __name__=='__main__':raise SystemExit(main())
