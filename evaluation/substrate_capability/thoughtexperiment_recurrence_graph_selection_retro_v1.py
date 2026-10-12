#!/usr/bin/env python3
"""Retrospective cross-family replay of recurrence training evidence."""
from __future__ import annotations
import hashlib,json,os,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
RUNNER=Path(__file__).resolve();ANALYZER=ROOT/'evaluation/substrate_capability/analyze_thoughtexperiment_recurrence_graph_selection_retro_v1.py'
PROTOCOL=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_RECURRENCE_GRAPH_SELECTION_RETRO_V1_PREREG_20261002.md'
INPUT=ROOT/'evaluation/reports/thoughtexperiment_recurrence_candidate_admission_v1_raw_20261002.json'
INPUT_LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_recurrence_candidate_admission_v1_lock_20261002.json'
BASE_RUNNER=ROOT/'evaluation/substrate_capability/thoughtexperiment_recurrence_candidate_admission_v1.py'
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_recurrence_graph_selection_retro_v1_lock_20261002.json'
OUT=ROOT/'evaluation/reports/thoughtexperiment_recurrence_graph_selection_retro_v1_20261002.json'
ACTIVE=('domains/contract_query.py','domains/engine_provenance.py','substrate/boot_core.py','substrate/seed_loader.py',
 'runners/dsl/src/py.rs','runners/dsl/src/substrate.rs','runners/dsl/src/graph.rs','runners/dsl/src/term.rs',
 'runners/dsl/src/grammar.rs','runners/dsl/src/sym.rs','runners/dsl/src/lib.rs','runners/dsl/Cargo.toml','runners/dsl/Cargo.lock')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def frozen():
 from substrate_rs import _native
 paths=[ROOT/p for p in ACTIVE]+[RUNNER,ANALYZER,PROTOCOL,INPUT,INPUT_LOCK,BASE_RUNNER]
 out={str(p.relative_to(ROOT)):sha(p) for p in paths};out['loaded_native_binary']=sha(Path(_native.__file__).resolve());return out
def correct(row):return len(row['offer_counts'])==len(row['recurrence_keys']) and all(x==1 for x in row['offer_counts']) and row['fixedpoint_progress']==0
def replay():
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 from domains.contract_query import select_candidate_from_graph_evidence
 from substrate.boot_core import boot_core
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit('stale native engine: '+'; '.join(stale))
 lock=json.loads(LOCK.read_text())
 if frozen()!=lock['sources']:raise SystemExit('source drift from lock')
 raw=json.loads(INPUT.read_text());results=[]
 for worker in raw['workers']:
  descriptors=worker['candidate_descriptors'];outcomes=worker['candidate_outcomes']
  if len(descriptors)!=8 or len(outcomes)!=8:raise RuntimeError('candidate matrix is incomplete')
  by_digest={x['digest']:x for x in outcomes}
  if set(by_digest)!={x['digest'] for x in descriptors}:raise RuntimeError('descriptor/outcome digest mismatch')
  proposals=[{'proposal_id':d['digest'],'proposal_label':d['label']} for d in descriptors]
  evidence=[];training_by_digest={};heldout_by_digest={}
  for d in descriptors:
   outcome=by_digest[d['digest']];tr=outcome['training'];ho=outcome['heldout']
   if set(tr['recurrence_keys']) & set(ho['recurrence_keys']):raise RuntimeError('training/heldout keys overlap')
   training_by_digest[d['digest']]=sum(1 for i,key in enumerate(tr['recurrence_keys'])
    if tr['offer_counts'][i]==1 and tr['fixedpoint_progress']==0)
   heldout_by_digest[d['digest']]=sum(1 for i,key in enumerate(ho['recurrence_keys'])
    if ho['offer_counts'][i]==1 and ho['fixedpoint_progress']==0)
   for i,key in enumerate(tr['recurrence_keys']):
    evidence.append({'proposal_id':d['digest'],'probe_id':key,
     'predicted':'correct' if tr['offer_counts'][i]==1 and tr['fixedpoint_progress']==0 else 'incorrect',
     'expected':'correct'})
  sub,root=boot_core(seeds=());primary_rules=sub._inner.export_rules();snap=sub.snapshot();branch=snap.fork()
  start=time.perf_counter_ns();decision=select_candidate_from_graph_evidence(branch,f'recurrence_retro_worker_{worker["worker"]}',proposals,evidence);decision_ns=time.perf_counter_ns()-start
  decision.pop('proposal_node',None)
  residual=None
  if decision.get('ok'):
   residual=sub.add_node('ExperimentResidual',{'experiment_id':f'recurrence_retro_worker_{worker["worker"]}',
    'selected_candidate_id':decision['proposal_id'],'matching_evidence_count':decision['matching_evidence_count'],
    'training_probe_count':decision['probe_count'],'source':'recurrence_graph_selection_retrospective_v1'})
  results.append({'worker':worker['worker'],'candidate_count':len(proposals),'training_probe_count':len({x['probe_id'] for x in evidence}),
   'decision':decision,'decision_ns':decision_ns,'training_matches_by_digest':training_by_digest,
   'heldout_matches_by_digest':heldout_by_digest,'selected_label':by_digest[decision.get('proposal_id','')]['label'] if decision.get('ok') else None,
   'primary_rule_set_unchanged':sub._inner.export_rules()==primary_rules,
   'primary_candidate_nodes_absent':not sub.nodes('CandidateProposal') and not sub.nodes('CandidateEvidence'),
   'residual_returned':residual is not None and sub.node(residual)['attrs'].get('selected_candidate_id')==decision.get('proposal_id'),
   'recurrence_keys_train':sorted({x['probe_id'] for x in evidence}),
   'recurrence_keys_heldout':sorted({k for d in descriptors for k in by_digest[d['digest']]['heldout']['recurrence_keys']})})
 if frozen()!=lock['sources']:raise SystemExit('source drift during replay')
 return {'schema':'RecurrenceGraphSelectionRetrospectiveV1','lock_sha256':sha(LOCK),
  'input_raw_sha256':sha(INPUT),'semantic_engine':rust_source_fingerprint(str(ROOT)),
  'retrospective_known_data':True,'workers':results}
def main():
 from domains.engine_provenance import rust_source_fingerprint
 if sys.argv[1:]==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite')
  LOCK.write_text(json.dumps({'schema':'RecurrenceGraphSelectionRetrospectiveV1Lock','sources':frozen(),
   'semantic_engine':rust_source_fingerprint(str(ROOT))},indent=2,sort_keys=True)+'\n');print(LOCK);return
 if sys.argv[1:]==['--replay']:
  if not LOCK.exists() or OUT.exists():raise SystemExit('missing lock or output exists')
  result=replay();OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(OUT);return
 raise SystemExit('use --lock or --replay')
if __name__=='__main__':main()
