#!/usr/bin/env python3
"""Measure sequential usefulness and controlled regression rollback."""
import hashlib,importlib.util,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'evaluation/substrate_capability')]
RUNNER=Path(__file__).resolve()
PRE=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_PERSISTENT_ADOPTION_V1_PREREG_20261003.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_thoughtexperiment_persistent_adoption_v1.py'
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_persistent_adoption_v1_lock_20261003.json'
OUT=ROOT/'evaluation/reports/thoughtexperiment_persistent_adoption_v1_20261003.json'
SOURCES=('runners/dsl/src/py.rs','runners/dsl/src/substrate.rs','runners/dsl/src/rewrite.rs',
 'runners/dsl/python/substrate_rs/__init__.py','domains/edit_ops.py','domains/contract_query.py',
 'domains/engine_provenance.py','evaluation/substrate_capability/thoughtexperiment_editops_cross_family_cow_v1.py',
 'evaluation/substrate_capability/analyze_thoughtexperiment_editops_cross_family_cow_v1.py',
 'evaluation/substrate_capability/thoughtexperiment_bidirectional_edge_identity_guards_v1_1.py',
 'evaluation/substrate_capability/thoughtexperiment_editops_edge_hypotheses_v1.py',
 'evaluation/substrate_capability/thoughtexperiment_editops_cross_family_cow_v1_lock_20261003.json',
 'evaluation/reports/thoughtexperiment_editops_cross_family_cow_v1_orders_20261003.json',
 'evaluation/reports/thoughtexperiment_editops_cross_family_cow_v1_scores_20261003.json',
 'evaluation/substrate_capability/thoughtexperiment_rule_activation_v1.py',
 'evaluation/substrate_capability/thoughtexperiment_rule_activation_v1_lock_20261003.json',
 'evaluation/reports/thoughtexperiment_rule_activation_v1_20261003.json')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def frozen():
 from substrate_rs import _native
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 if build_is_stale(str(ROOT)):raise RuntimeError('native engine stale')
 paths=[ROOT/p for p in SOURCES]+[RUNNER,PRE,ANALYZER]
 return {'files':{str(p.relative_to(ROOT)):sha(p) for p in paths},
  'native':{'path':str(Path(_native.__file__).resolve()),'sha256':sha(Path(_native.__file__).resolve())},
  'rust_fingerprint':rust_source_fingerprint(str(ROOT))}
def run():
 from thoughtexperiment_editops_cross_family_cow_v1 import modules,make_pool,make_ctx,execute_recurrence,execute_conversation,digest
 b,_=modules();rows=[]
 for family in ('recurrence','conversation'):
  for worker in range(4):
   _,candidates,descriptors,*_=make_pool(family,worker)
   for c,d in zip(candidates,descriptors):c['proposal_id']=d['proposal_id']
   token='candidate:has_mint_offer' if family=='recurrence' else 'in:m:responds_to'
   selected=next(c for c in candidates if token in c['label'])
   ctx=make_ctx(b,family,worker,f'persistent_{worker}',True);sub,native,target=ctx['sub'],ctx['native'],ctx['target']
   rev=tuple(sub.experiment_graph_rule_revision());t=time.perf_counter_ns()
   sub.replace_active_rule_by_name_if_revision(rev,target,selected['rules'][target]);activation_ns=time.perf_counter_ns()-t
   if family=='recurrence':
    first=execute_recurrence(ctx,sub)
    episode=sub.add_node('MintingRecurrenceEpisode',{'mint_after_quanta':1,'integer_native':1,'generator':'persistent_adoption_v1'})
    sub.add_edge(ctx['agent'],'has_minting_recurrence_episode',episode)
    key=f'persistent-{worker}';attrs={'predicate':'bind','recurrence_key':key,
     'structural_signature':[['relation','bind','ITEM','PERSISTENT',worker]],
     'capability_key':[key,'X'],'persistence':1,'latest_segment_ordinal':1}
    cand=sub.add_node('PredicateRecurrenceCandidate',attrs)
    ev=sub.add_node('ResidualSegmentEvidence',{**attrs,'segment_ordinal':1,'integer_native':1})
    sub.add_edge(episode,'has_predicate_recurrence_candidate',cand);sub.add_edge(cand,'supported_by_segment',ev)
    native.run_rules(100);second={'correct':len(list(sub.neighbours(cand,'has_mint_offer')))==1,
      'output_count':len(list(sub.neighbours(cand,'has_mint_offer')))}
   else:
    first=execute_conversation(ctx,sub,'train')
    second=execute_conversation(ctx,sub,'heldout')
   rows.append({'family':family,'worker':worker,'selected_label':selected['label'],'activation_ns':activation_ns,
    'first':first,'second':second,'same_substrate':True})
 for worker in range(4):
  _,cs,ds,*_=make_pool('recurrence',worker)
  for c,d in zip(cs,ds):c['proposal_id']=d['proposal_id']
  wrong=next(c for c in cs if 'out:agent:observed' in c['label'])
  ctx=make_ctx(b,'recurrence',worker,f'rollback_{worker}',True);sub,native,target=ctx['sub'],ctx['native'],ctx['target']
  original=ctx['source_rule'];rev=tuple(sub.experiment_graph_rule_revision())
  sub.replace_active_rule_by_name_if_revision(rev,target,wrong['rules'][target])
  failed=execute_recurrence(ctx,sub)
  bad_name=wrong['rules'][target]['name'];rollback_rev=tuple(sub.experiment_graph_rule_revision())
  t=time.perf_counter_ns();rolled=sub.replace_active_rule_by_name_if_revision(rollback_rev,bad_name,original);rollback_ns=time.perf_counter_ns()-t
  recovered=execute_recurrence(ctx,sub)
  rows.append({'family':'rollback','worker':worker,'bad_candidate':wrong['label'],'failure_detected':not failed['correct'],
   'failed_output_counts':failed['output_counts'],'rollback_succeeded':rolled,'rollback_ns':rollback_ns,
   'recovered':recovered,'source_rule_active':any(r.get('name')==target and r.get('active',True) for r in native.export_rules())})
 return rows
def main():
 if sys.argv[1:]==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite')
  LOCK.write_text(json.dumps({'schema':'ThoughtexperimentPersistentAdoptionV1Lock','sources':frozen(),
   'workers_per_family':4,'families':['recurrence','conversation'],'rollback_workers':4},indent=2,sort_keys=True)+'\n')
  print(LOCK.relative_to(ROOT));return 0
 if sys.argv[1:]==['--run']:
  lock=json.loads(LOCK.read_text())
  if frozen()!=lock['sources']:raise SystemExit('source drift')
  rows=run()
  if frozen()!=lock['sources']:raise SystemExit('source drift during capture')
  OUT.write_text(json.dumps({'schema':'ThoughtexperimentPersistentAdoptionV1Results',
   'lock_sha256':sha(LOCK),'sources':frozen(),'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
   'rows':rows},indent=2,sort_keys=True)+'\n')
  print(OUT.relative_to(ROOT));return 0
 raise SystemExit('usage: --lock | --run')
if __name__=='__main__':raise SystemExit(main())
