#!/usr/bin/env python3
"""Paired recurrence candidate evaluation with bounded early rejection."""
from __future__ import annotations
import hashlib,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'evaluation/substrate_capability')]
RUNNER=Path(__file__).resolve();ANALYZER=ROOT/'evaluation/substrate_capability/analyze_thoughtexperiment_recurrence_early_rejection_v1.py'
PROTOCOL=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_RECURRENCE_EARLY_REJECTION_V1_PREREG_20261002.md'
BASE=ROOT/'evaluation/substrate_capability/thoughtexperiment_recurrence_candidate_admission_v1.py'
GRAPH_RUNNER=ROOT/'evaluation/substrate_capability/thoughtexperiment_recurrence_graph_selection_v1_1.py'
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_recurrence_early_rejection_v1_lock_20261002.json'
ORDERS=ROOT/'evaluation/reports/thoughtexperiment_recurrence_early_rejection_v1_orders_20261002.json'
SCORES=ROOT/'evaluation/reports/thoughtexperiment_recurrence_early_rejection_v1_scores_20261002.json'
WORKERS=4;REPEATS=4;BATCH=100;STAGE_BUDGET=200
ACTIVE=('domains/contract_query.py','domains/self_correction.py','domains/edit_ops.py','domains/engine_provenance.py',
 'substrate/boot_core.py','substrate/seed_loader.py','runners/dsl/src/py.rs','runners/dsl/src/substrate.rs',
 'runners/dsl/src/graph.rs','runners/dsl/src/graph_rules.rs','runners/dsl/src/term.rs','runners/dsl/src/persist.rs',
 'runners/dsl/src/grammar.rs','runners/dsl/src/sym.rs','runners/dsl/src/lib.rs','runners/dsl/Cargo.toml','runners/dsl/Cargo.lock',
 'runners/dsl/python/substrate_rs/__init__.py','seeds/minting_recurrence_ledger.json','seeds/relation_vocabulary.json',
 'seeds/composer_dispatch.json','seeds/autonomy.json')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def frozen():
 from substrate_rs import _native
 paths=[ROOT/p for p in ACTIVE]+[RUNNER,ANALYZER,PROTOCOL,BASE,GRAPH_RUNNER]
 out={str(p.relative_to(ROOT)):sha(p) for p in paths};out['loaded_native_binary']=sha(Path(_native.__file__).resolve());return out
def digest(c):
 from thoughtexperiment_recurrence_candidate_admission_v1 import canonical_digest
 return canonical_digest(c)
def candidates(worker,split):
 from thoughtexperiment_recurrence_candidate_admission_v1 import build_base
 t=time.perf_counter_ns();sub,native,episode,keys,cs=build_base(worker,split);ns=time.perf_counter_ns()-t
 ds=[{'proposal_id':digest(c),'proposal_label':c['label'],'outcome_class':c.get('outcome_class','')} for c in cs]
 if len(ds)!=8 or len({d['proposal_id'] for d in ds})!=8:raise RuntimeError('expected eight unique candidates')
 return sub,native,episode,keys,cs,ds,ns
def install(native,candidate):
 from thoughtexperiment_recurrence_candidate_admission_v1 import TARGET
 active=[(i,r) for i,r in enumerate(native.export_rules()) if r.get('name')==TARGET and r.get('active',True)]
 if not active or not all(native.remove_rule(i) for i,_ in reversed(active)):raise RuntimeError('could not remove active faulty rule')
 native.add_rule(candidate['rules'][TARGET])
def close_bounded(native):
 sweeps=[];remaining=STAGE_BUDGET
 while remaining>0:
  limit=min(BATCH,remaining);n=int(native.run_rules(limit));sweeps.append(n);remaining-=limit
  if n<limit:return {'fixedpoint':True,'sweeps':sweeps,'work':sum(sweeps),'budget_exhausted':False}
 return {'fixedpoint':False,'sweeps':sweeps,'work':sum(sweeps),'budget_exhausted':True}
def offers(sub,keys):
 counts=[]
 for key in keys:
  nodes=[n for n in sub.nodes('PredicateRecurrenceCandidate') if sub.node(n)['attrs'].get('recurrence_key')==key]
  counts.append(len(list(sub.neighbours(nodes[0],'has_mint_offer'))) if nodes else 0)
 return counts
def bounded_score(worker_id,split,candidate):
 from thoughtexperiment_recurrence_candidate_admission_v1 import build_base
 total_start=time.perf_counter_ns();t=time.perf_counter_ns();sub,native,episode,keys,_=build_base(worker_id,split);setup_ns=time.perf_counter_ns()-t
 t=time.perf_counter_ns();install(native,candidate);install_ns=time.perf_counter_ns()-t
 t=time.perf_counter_ns();stage1=close_bounded(native);stage1_ns=time.perf_counter_ns()-t
 stage2=None
 if stage1['fixedpoint']:
  t=time.perf_counter_ns()
  for j,key in enumerate(keys[1:],start=1):
   attrs={'predicate':'bind','recurrence_key':key,'structural_signature':[['relation','bind','ITEM',f'SLOT{j}',worker_id]],'capability_key':[key,'X']}
   cand=sub.add_node('PredicateRecurrenceCandidate',attrs);ev=sub.add_node('ResidualSegmentEvidence',{**attrs,'segment_ordinal':j,'integer_native':1})
   sub.add_edge(episode,'has_predicate_recurrence_candidate',cand);sub.add_edge(cand,'supported_by_segment',ev)
  second_candidate_mutation_ns=time.perf_counter_ns()-t
  t=time.perf_counter_ns();stage2=close_bounded(native);stage2_ns=time.perf_counter_ns()-t
 else:stage2_ns=0;second_candidate_mutation_ns=0
 counts=offers(sub,keys);complete=bool(stage1['fixedpoint'] and stage2 and stage2['fixedpoint'])
 return {'pass':counts==[1,1] and complete,'oracle_correct':counts==[1,1] and complete,
  'offer_counts':counts,'fixedpoint_progress':0 if complete else 100,'bounded_status':'fixedpoint' if complete else 'work_budget_exhausted',
  'capped_stage':None if complete else ('first_candidate' if not stage1['fixedpoint'] else 'second_candidate'),
  'first_candidate_sweeps':stage1['sweeps'],'second_candidate_sweeps':stage2['sweeps'] if stage2 else [],
  'bounded_work_by_stage':{'first_candidate':stage1['work'],'second_candidate':stage2['work'] if stage2 else 0},
  'budget_exhausted_by_stage':{'first_candidate':stage1['budget_exhausted'],'second_candidate':stage2['budget_exhausted'] if stage2 else False},
  'recurrence_keys':keys,'setup_ns':setup_ns,'install_ns':install_ns,'stage1_ns':stage1_ns,
  'second_candidate_mutation_ns':second_candidate_mutation_ns,'stage2_ns':stage2_ns,
  'runtime_ns':time.perf_counter_ns()-total_start}
def ref_score(worker_id,split,candidate):
 from thoughtexperiment_recurrence_candidate_admission_v1 import score_candidate
 t=time.perf_counter_ns();r=score_candidate(worker_id,split,candidate);r['runtime_ns']=time.perf_counter_ns()-t
 r['oracle_correct']=r['offer_counts']==[1,1] and r['fixedpoint_progress']==0 and len(r['recurrence_keys'])==2
 return r
def order_worker(worker):
 from domains.contract_query import select_candidate_from_graph_evidence
 before=frozen();sub,native,episode,keys,cs,ds,enum_ns=candidates(worker,'selection')
 base_rows={d['proposal_id']:[] for d in ds};bounded_rows={d['proposal_id']:[] for d in ds};base_ev=[];bounded_ev=[];train_keys=[]
 base_runtime=bounded_runtime=0
 for candidate,d in zip(cs,ds):
  for sample in range(REPEATS):
   wid=worker*10000+sample;split=f'train_{worker}_{sample}'
   br=ref_score(wid,split,candidate);rr=bounded_score(wid,split,candidate)
   base_runtime+=br['runtime_ns'];bounded_runtime+=rr['runtime_ns']
   pid=f'w{worker}_train_{sample}';base_rows[d['proposal_id']].append({'probe_id':pid,'outcome':br});bounded_rows[d['proposal_id']].append({'probe_id':pid,'outcome':rr})
   train_keys.extend(br['recurrence_keys'])
   base_ev.append({'proposal_id':d['proposal_id'],'probe_id':pid,'predicted':'correct' if br['oracle_correct'] else 'incorrect','expected':'correct'})
   bounded_ev.append({'proposal_id':d['proposal_id'],'probe_id':pid,'predicted':'correct' if rr['oracle_correct'] else 'incorrect','expected':'correct'})
 snapshot=sub.snapshot();decision={};decision_ns={}
 for arm,evidence in (('baseline',base_ev),('bounded',bounded_ev)):
  branch=snapshot.fork();t=time.perf_counter_ns();dec=select_candidate_from_graph_evidence(branch,f'early_reject_{arm}_w{worker}',
   [{'proposal_id':d['proposal_id'],'proposal_label':d['proposal_label']} for d in ds],evidence);decision_ns[arm]=time.perf_counter_ns()-t;dec.pop('proposal_node',None);decision[arm]=dec
 primary_rules=native.export_rules()
 residual=None
 if decision['bounded'].get('ok') and decision['baseline'].get('ok'):
  residual=sub.add_node('ExperimentResidual',{'experiment_id':f'early_reject_w{worker}',
   'selected_candidate_id':decision['bounded']['proposal_id'],'baseline_candidate_id':decision['baseline']['proposal_id'],
   'source':'recurrence_early_rejection_v1'})
 return {'worker':worker,'descriptors':ds,'baseline_training':base_rows,'bounded_training':bounded_rows,
  'training_recurrence_keys':sorted(train_keys),'decisions':decision,'decision_ns':decision_ns,
  'candidate_enumeration_ns':enum_ns,'baseline_training_runtime_ns':base_runtime,'bounded_training_runtime_ns':bounded_runtime,
  'primary_rules_unchanged':native.export_rules()==primary_rules,
  'primary_candidate_evidence_absent':not sub.nodes('CandidateProposal') and not sub.nodes('CandidateEvidence'),
  'residual_returned':residual is not None and sub.node(residual)['attrs']['selected_candidate_id']==decision['bounded'].get('proposal_id'),
  'source_before':before,'source_after':frozen(),'source_stable':before==frozen()}
def score_worker(order):
 before=frozen();sub,native,episode,keys,cs,ds,enum_ns=candidates(order['worker'],'heldout_inventory')
 if ds!=order['descriptors']:raise RuntimeError('candidate descriptors changed after orders freeze')
 out={d['proposal_id']:[] for d in ds};base_runtime=bounded_runtime=0;heldout_keys=[]
 for candidate,d in zip(cs,ds):
  for sample in range(REPEATS):
   wid=order['worker']*10000+1000+sample;split=f'heldout_{order["worker"]}_{sample}'
   br=ref_score(wid,split,candidate);rr=bounded_score(wid,split,candidate);base_runtime+=br['runtime_ns'];bounded_runtime+=rr['runtime_ns']
   heldout_keys.extend(br['recurrence_keys']);out[d['proposal_id']].append({'sample':sample,'baseline':br,'bounded':rr})
 after=frozen()
 return {'worker':order['worker'],'heldout':out,'heldout_recurrence_keys':sorted(heldout_keys),
  'candidate_enumeration_ns':enum_ns,'baseline_heldout_runtime_ns':base_runtime,'bounded_heldout_runtime_ns':bounded_runtime,
  'source_before':before,'source_after':after,'source_stable':before==after}
def main():
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit('stale native engine: '+'; '.join(stale))
 env={**os.environ,'PYTHONPATH':f'{ROOT / "runners/dsl/python"}:{ROOT / "evaluation/substrate_capability"}:{ROOT}'}
 if sys.argv[1:]==['--lock']:
  if any(p.exists() for p in (LOCK,ORDERS,SCORES)):raise SystemExit('refusing to overwrite')
  LOCK.write_text(json.dumps({'schema':'RecurrenceEarlyRejectionV1Lock','sources':frozen(),'semantic_engine':rust_source_fingerprint(str(ROOT)),
   'workers':WORKERS,'repeats':REPEATS,'rule_batch':BATCH,'per_stage_budget':STAGE_BUDGET},indent=2,sort_keys=True)+'\n');print(LOCK);return
 if not LOCK.exists() or frozen()!=json.loads(LOCK.read_text())['sources']:raise SystemExit('missing lock or source drift')
 if sys.argv[1:]==['--orders']:
  if ORDERS.exists() or SCORES.exists():raise SystemExit('capture exists')
  ws=[]
  for i in range(WORKERS):
   p=subprocess.run([sys.executable,str(RUNNER),'--orders-worker',str(i)],cwd=ROOT,env=env,text=True,capture_output=True)
   if p.returncode:raise RuntimeError(p.stderr[-3000:])
   ws.append(json.loads(p.stdout.strip().splitlines()[-1]))
  if frozen()!=json.loads(LOCK.read_text())['sources']:raise SystemExit('source drift before order freeze')
  ORDERS.write_text(json.dumps({'schema':'RecurrenceEarlyRejectionV1Orders','lock_sha256':sha(LOCK),'workers':ws,
   'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':{'platform':platform.platform(),'python':sys.version.split()[0]}},indent=2,sort_keys=True)+'\n');print(ORDERS);return
 if sys.argv[1:]==['--score']:
  if not ORDERS.exists() or SCORES.exists():raise SystemExit('orders missing or scores exist')
  od=json.loads(ORDERS.read_text())
  if od['lock_sha256']!=sha(LOCK):raise SystemExit('order lock mismatch')
  ws=[]
  for order in od['workers']:
   p=subprocess.run([sys.executable,str(RUNNER),'--score-worker'],input=json.dumps(order),cwd=ROOT,env=env,text=True,capture_output=True)
   if p.returncode:raise RuntimeError(p.stderr[-3000:])
   ws.append(json.loads(p.stdout.strip().splitlines()[-1]))
  if frozen()!=json.loads(LOCK.read_text())['sources']:raise SystemExit('source drift while scoring')
  SCORES.write_text(json.dumps({'schema':'RecurrenceEarlyRejectionV1Scores','orders_sha256':sha(ORDERS),'workers':ws},indent=2,sort_keys=True)+'\n');print(SCORES);return
 if sys.argv[1:2]==['--orders-worker']:print(json.dumps(order_worker(int(sys.argv[2])),sort_keys=True,separators=(',',':')));return
 if sys.argv[1:2]==['--score-worker']:print(json.dumps(score_worker(json.load(sys.stdin)),sort_keys=True,separators=(',',':')));return
 raise SystemExit('use --lock, --orders, or --score')
if __name__=='__main__':main()
