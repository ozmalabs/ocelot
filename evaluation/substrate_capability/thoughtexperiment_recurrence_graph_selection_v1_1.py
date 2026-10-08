#!/usr/bin/env python3
"""Prospective recurrence candidate selection with graph-resident evidence."""
from __future__ import annotations
import hashlib,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'evaluation/substrate_capability')]
RUNNER=Path(__file__).resolve();ANALYZER=ROOT/'evaluation/substrate_capability/analyze_thoughtexperiment_recurrence_graph_selection_v1_1.py'
PROTOCOL=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_RECURRENCE_GRAPH_SELECTION_V1_1_PREREG_20261002.md'
BASE=ROOT/'evaluation/substrate_capability/thoughtexperiment_recurrence_candidate_admission_v1.py'
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_recurrence_graph_selection_v1_1_lock_20261002.json'
ORDERS=ROOT/'evaluation/reports/thoughtexperiment_recurrence_graph_selection_v1_1_orders_20261002.json'
SCORES=ROOT/'evaluation/reports/thoughtexperiment_recurrence_graph_selection_v1_1_scores_20261002.json'
WORKERS=4;REPEATS=4;TARGET='mrl_offer_due_once'
ACTIVE=('domains/contract_query.py','domains/self_correction.py','domains/edit_ops.py','domains/engine_provenance.py',
 'substrate/boot_core.py','substrate/seed_loader.py','runners/dsl/src/py.rs','runners/dsl/src/substrate.rs',
 'runners/dsl/src/graph.rs','runners/dsl/src/graph_rules.rs','runners/dsl/src/term.rs','runners/dsl/src/persist.rs',
 'runners/dsl/src/grammar.rs','runners/dsl/src/sym.rs','runners/dsl/src/lib.rs','runners/dsl/Cargo.toml','runners/dsl/Cargo.lock',
 'runners/dsl/python/substrate_rs/__init__.py','seeds/minting_recurrence_ledger.json','seeds/relation_vocabulary.json',
 'seeds/composer_dispatch.json','seeds/autonomy.json')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def frozen():
 from substrate_rs import _native
 paths=[ROOT/p for p in ACTIVE]+[RUNNER,ANALYZER,PROTOCOL,BASE]
 out={str(p.relative_to(ROOT)):sha(p) for p in paths};out['loaded_native_binary']=sha(Path(_native.__file__).resolve());return out
def episode_correct(row):return row.get('offer_counts')==[1,1] and row.get('fixedpoint_progress')==0 and len(row.get('recurrence_keys',[]))==2
def descriptor(c):
 from thoughtexperiment_recurrence_candidate_admission_v1 import canonical_digest
 return {'proposal_id':canonical_digest(c),'proposal_label':c.get('label',''),'outcome_class':c.get('outcome_class',''),
  'targets':sorted((c.get('rules') or {}).keys())}
def enumerate_candidates(worker,split):
 from thoughtexperiment_recurrence_candidate_admission_v1 import build_base
 start=time.perf_counter_ns();sub,native,episode,keys,candidates=build_base(worker,split);elapsed=time.perf_counter_ns()-start
 descriptors=[descriptor(c) for c in candidates]
 if len(descriptors)!=8 or len({d['proposal_id'] for d in descriptors})!=8:raise RuntimeError('candidate surface is not eight unique descriptors')
 return sub,native,episode,candidates,descriptors,elapsed
def score_one(worker_id,split,candidate):
 from thoughtexperiment_recurrence_candidate_admission_v1 import score_candidate
 row=score_candidate(worker_id,split,candidate)
 return {**row,'oracle_correct':episode_correct(row)}
def orders_worker(worker):
 from domains.contract_query import select_candidate_from_graph_evidence
 before=frozen();sub,native,_ep,candidates,descriptors,enum_ns=enumerate_candidates(worker,'selection')
 training={d['proposal_id']:[] for d in descriptors};evidence=[];train_keys=[];task_ns=0
 for ci,(candidate,d) in enumerate(zip(candidates,descriptors)):
  for sample in range(REPEATS):
   task_id=worker*10000+sample
   start=time.perf_counter_ns();out=score_one(task_id,f'train_{worker}_{sample}',candidate);task_ns+=time.perf_counter_ns()-start
   probe=f'w{worker}_train_{sample}';training[d['proposal_id']].append({'probe_id':probe,'outcome':out})
   train_keys.extend(out['recurrence_keys'])
   evidence.append({'proposal_id':d['proposal_id'],'probe_id':probe,
    'predicted':'correct' if out['oracle_correct'] else 'incorrect','expected':'correct'})
 snapshot=sub.snapshot();branch=snapshot.fork();decision_start=time.perf_counter_ns()
 decision=select_candidate_from_graph_evidence(branch,f'recurrence_fresh_v1_1_w{worker}',
  [{'proposal_id':d['proposal_id'],'proposal_label':d['proposal_label']} for d in descriptors],evidence)
 decision_ns=time.perf_counter_ns()-decision_start;decision.pop('proposal_node',None)
 primary_rules=native.export_rules();residual=None
 if decision.get('ok'):
  residual=sub.add_node('ExperimentResidual',{'experiment_id':f'recurrence_fresh_v1_1_w{worker}',
   'selected_candidate_id':decision['proposal_id'],'matching_evidence_count':decision['matching_evidence_count'],
   'training_probe_count':decision['probe_count'],'source':'recurrence_graph_selection_v1_1'})
 return {'worker':worker,'candidate_descriptors':descriptors,'training':training,'training_recurrence_keys':sorted(train_keys),
  'decision':decision,'decision_ns':decision_ns,'enumeration_ns':enum_ns,'training_episode_runtime_ns':task_ns,
  'primary_rules_unchanged':native.export_rules()==primary_rules,
  'primary_candidate_evidence_absent':not sub.nodes('CandidateProposal') and not sub.nodes('CandidateEvidence'),
  'residual_returned':residual is not None and sub.node(residual)['attrs'].get('selected_candidate_id')==decision.get('proposal_id'),
  'source_before':before,'source_after':frozen(),'source_stable':before==frozen()}
def score_worker(order):
 before=frozen();sub,native,_ep,candidates,descriptors,enum_ns=enumerate_candidates(order['worker'],'heldout_inventory')
 if descriptors!=order['candidate_descriptors']:raise RuntimeError('candidate descriptors changed after orders freeze')
 heldout={d['proposal_id']:[] for d in descriptors};keys=[];runtime_ns=0
 for candidate,d in zip(candidates,descriptors):
  for sample in range(REPEATS):
   task_id=order['worker']*10000+1000+sample
   start=time.perf_counter_ns();out=score_one(task_id,f'heldout_{order["worker"]}_{sample}',candidate);runtime_ns+=time.perf_counter_ns()-start
   heldout[d['proposal_id']].append({'sample':sample,'outcome':out});keys.extend(out['recurrence_keys'])
 after=frozen()
 return {'worker':order['worker'],'heldout':heldout,'heldout_recurrence_keys':sorted(keys),
  'enumeration_ns':enum_ns,'heldout_episode_runtime_ns':runtime_ns,'source_before':before,'source_after':after,'source_stable':before==after}
def main():
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit('stale native engine: '+'; '.join(stale))
 env={**os.environ,'PYTHONPATH':f'{ROOT / "runners/dsl/python"}:{ROOT / "evaluation/substrate_capability"}:{ROOT}'}
 if sys.argv[1:]==['--lock']:
  if any(p.exists() for p in (LOCK,ORDERS,SCORES)):raise SystemExit('refusing to overwrite')
  LOCK.write_text(json.dumps({'schema':'RecurrenceGraphSelectionV1_1Lock','sources':frozen(),
   'semantic_engine':rust_source_fingerprint(str(ROOT)),'workers':WORKERS,'train_episodes_per_candidate_worker':REPEATS,
   'heldout_episodes_per_candidate_worker':REPEATS,'sample_unit':'one fresh recurrence episode containing two due keys'},indent=2,sort_keys=True)+'\n');print(LOCK);return
 if not LOCK.exists() or frozen()!=json.loads(LOCK.read_text())['sources']:raise SystemExit('missing lock or source drift')
 if sys.argv[1:]==['--orders']:
  if ORDERS.exists() or SCORES.exists():raise SystemExit('capture exists')
  ws=[]
  for i in range(WORKERS):
   p=subprocess.run([sys.executable,str(RUNNER),'--orders-worker',str(i)],cwd=ROOT,env=env,text=True,capture_output=True)
   if p.returncode:raise RuntimeError(p.stderr[-3000:])
   ws.append(json.loads(p.stdout.strip().splitlines()[-1]))
  if frozen()!=json.loads(LOCK.read_text())['sources']:raise SystemExit('source drift before orders freeze')
  ORDERS.write_text(json.dumps({'schema':'RecurrenceGraphSelectionV1_1Orders','lock_sha256':sha(LOCK),'workers':ws,
   'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':{'platform':platform.platform(),'python':sys.version.split()[0]}},indent=2,sort_keys=True)+'\n');print(ORDERS);return
 if sys.argv[1:]==['--score']:
  if not ORDERS.exists() or SCORES.exists():raise SystemExit('orders missing or score exists')
  od=json.loads(ORDERS.read_text())
  if od['lock_sha256']!=sha(LOCK):raise SystemExit('order/lock digest mismatch')
  ws=[]
  for order in od['workers']:
   p=subprocess.run([sys.executable,str(RUNNER),'--score-worker'],input=json.dumps(order),cwd=ROOT,env=env,text=True,capture_output=True)
   if p.returncode:raise RuntimeError(p.stderr[-3000:])
   ws.append(json.loads(p.stdout.strip().splitlines()[-1]))
  if frozen()!=json.loads(LOCK.read_text())['sources']:raise SystemExit('source drift while scoring')
  SCORES.write_text(json.dumps({'schema':'RecurrenceGraphSelectionV1_1Scores','orders_sha256':sha(ORDERS),'workers':ws},indent=2,sort_keys=True)+'\n');print(SCORES);return
 if sys.argv[1:2]==['--orders-worker']:print(json.dumps(orders_worker(int(sys.argv[2])),sort_keys=True,separators=(',',':')));return
 if sys.argv[1:2]==['--score-worker']:print(json.dumps(score_worker(json.load(sys.stdin)),sort_keys=True,separators=(',',':')));return
 raise SystemExit('use --lock, --orders, or --score')
if __name__=='__main__':main()
