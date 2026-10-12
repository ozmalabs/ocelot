#!/usr/bin/env python3
"""Source-locked generic structural proposal transfer to recurrence."""
from __future__ import annotations
import hashlib,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'evaluation/substrate_capability')]
RUNNER=Path(__file__).resolve()
PREREG=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_RECURRENCE_GENERAL_STRUCTURAL_PROPOSAL_V1_PREREG_20261002.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_thoughtexperiment_recurrence_general_structural_proposal_v1.py'
AMENDMENT=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_RECURRENCE_GENERAL_STRUCTURAL_PROPOSAL_V1_1_AMENDMENT_20261002.md'
ADAPTER=ROOT/'evaluation/substrate_capability/thoughtexperiment_blinded_panel_adapters_v1.py'
TASK_RUNNER=ROOT/'evaluation/substrate_capability/thoughtexperiment_recurrence_candidate_admission_v1.py'
TASK_PREREG=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_RECURRENCE_CANDIDATE_ADMISSION_V1_PREREG_20261002.md'
TASK_RESULTS=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_RECURRENCE_CANDIDATE_ADMISSION_V1_RESULTS_20261002.md'
SOURCES=('domains/reflective_faculty.py','domains/edit_ops.py','domains/self_correction.py',
 'domains/self_correct_dispatch.py','substrate/boot_core.py','substrate/seed_loader.py',
 'runners/dsl/src/py.rs','runners/dsl/src/substrate.rs','runners/dsl/src/graph.rs',
 'runners/dsl/src/graph_rules.rs','runners/dsl/src/term.rs','runners/dsl/src/persist.rs',
 'runners/dsl/src/grammar.rs','runners/dsl/src/sym.rs','runners/dsl/src/lib.rs',
 'runners/dsl/Cargo.toml','runners/dsl/Cargo.lock','runners/dsl/python/substrate_rs/__init__.py',
 'seeds/minting_recurrence_ledger.json','seeds/relation_vocabulary.json',
 'seeds/composer_dispatch.json','seeds/autonomy.json')
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_recurrence_general_structural_proposal_v1_1_lock_20261002.json'
ORDERS=ROOT/'evaluation/reports/thoughtexperiment_recurrence_general_structural_proposal_v1_1_orders_20261002.json'
SCORES=ROOT/'evaluation/reports/thoughtexperiment_recurrence_general_structural_proposal_v1_1_scores_20261002.json'
WORKERS=4
CUE=['mrl','offer','due','once','guard','constrain','restrict','narrow','extra','condition','equality']

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def frozen()->dict:
 from substrate_rs import _native
 paths=[ROOT/p for p in SOURCES]+[RUNNER,PREREG,AMENDMENT,ANALYZER,ADAPTER,TASK_RUNNER,TASK_PREREG,TASK_RESULTS]
 out={str(p.relative_to(ROOT)):sha(p) for p in paths};out['loaded_native_binary']=sha(Path(_native.__file__).resolve())
 return out
def semantic_digest(candidate:dict)->str:
 rows={}
 for name,row in sorted((candidate.get('rules') or {}).items()):
  value=json.loads(json.dumps(row,sort_keys=True));value.pop('name',None);rows[name]=value
 raw=json.dumps(rows,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
 return 'sha256:'+hashlib.sha256(raw).hexdigest()
def order_worker(worker:int)->dict:
 import thoughtexperiment_blinded_panel_adapters_v1 as adapters
 import domains.reflective_faculty as rf
 before=frozen();ctx=adapters.prepare('recurrence',worker,'train');sub=ctx['sub'];key=f'recurrence_structural_proposal_{worker}'
 sub.add_node('CapabilityAxis',{'is_axis':1.0,'capability_keys':[key],'induced':1.0,
  'residual_predicates':CUE,'structural_rule_scope':'all_mutable_rules','from_observation':1.0,
  'source':'recurrence_general_structural_proposal_v1'})
 primary_before=ctx['native'].export_rules();started=time.perf_counter_ns()
 result=rf.compose_general_structural_variant(sub,[key],f'recurrence_{worker}')
 compose_ns=time.perf_counter_ns()-started
 candidate=({'label':f"generic_{result.get('kind')}",'rules':{result['removed_rule']:result['rule']}}
  if result.get('built') else None)
 target_rows=[r for r in primary_before if r.get('name')=='mrl_offer_due_once' and r.get('active',True)]
 target_unchanged=all(next((r for r in ctx['native'].export_rules() if r.get('name')==old.get('name') and r.get('active',True)),None)==old for old in target_rows)
 after=frozen()
 if before!=after:raise RuntimeError('source drift during order worker')
 return {'worker':worker,'cue':CUE,'proposal':candidate,'built':bool(result.get('built')),
  'target':result.get('removed_rule'),'operator':result.get('kind'),'site':result.get('site'),
  'wall':result.get('wall'),'compose_ns':compose_ns,'primary_target_unchanged':target_unchanged,
  'proposal_digest':semantic_digest(candidate) if candidate else None,'source_before':before,'source_after':after}
def score_worker(order:dict)->dict:
 import thoughtexperiment_blinded_panel_adapters_v1 as adapters
 before=frozen();worker=int(order['worker']);ctx=adapters.prepare('recurrence',worker,'heldout')
 proposal=adapters.score(ctx,order['proposal']) if order.get('proposal') else None
 positive=next((c for c in ctx['candidates'] if c.get('label')=='dedup_identity_fix'),None)
 if positive is None:raise RuntimeError('dedup_identity_fix reference missing')
 reference=adapters.score(ctx,positive);after=frozen()
 if before!=after:raise RuntimeError('source drift during score worker')
 return {'worker':worker,'proposal_score':proposal,'positive_reference_score':reference,
  'source_before':before,'source_after':after}
def main()->int:
 mode=sys.argv[1:]
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit('stale native engine: '+'; '.join(stale))
 env={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}:{ROOT}/evaluation/substrate_capability'}
 if mode[:1]==['--order-worker']:
  print(json.dumps(order_worker(int(sys.argv[2])),sort_keys=True,separators=(',',':')));return 0
 if mode[:1]==['--score-worker']:
  print(json.dumps(score_worker(json.load(sys.stdin)),sort_keys=True,separators=(',',':')));return 0
 if mode==['--lock']:
  if any(p.exists() for p in (LOCK,ORDERS,SCORES)):raise SystemExit('refusing to overwrite lock/capture')
  LOCK.write_text(json.dumps({'schema':'ThoughtexperimentRecurrenceGeneralStructuralProposalV1_1Lock',
   'sources':frozen(),'semantic_engine':rust_source_fingerprint(str(ROOT)),
   'workers':WORKERS,'cue':CUE,'target':'mrl_offer_due_once','expected_operator':'add_match_guard',
   'positive_reference':'dedup_identity_fix','split':'train_then_heldout'},indent=2,sort_keys=True)+'\n')
  print(LOCK.relative_to(ROOT));return 0
  
 if mode==['--orders']:
  if not LOCK.exists() or ORDERS.exists() or SCORES.exists():raise SystemExit('missing lock or capture exists')
  lock=json.loads(LOCK.read_text());before=frozen()
  if before!=lock['sources']:raise SystemExit('source drift from lock')
  workers=[]
  for i in range(WORKERS):
   p=subprocess.run([sys.executable,str(RUNNER),'--order-worker',str(i)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=45)
   if p.returncode:raise RuntimeError(f'order worker {i}: {p.stderr[-3000:]}')
   workers.append(json.loads(p.stdout.strip().splitlines()[-1]))
  if frozen()!=before:raise SystemExit('source drift during order capture')
  ORDERS.write_text(json.dumps({'schema':'ThoughtexperimentRecurrenceGeneralStructuralProposalV1_1Orders',
   'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),
   'lock_sha256':sha(LOCK),'workers':workers},indent=2,sort_keys=True)+'\n')
  print(ORDERS.relative_to(ROOT));return 0
 if mode==['--scores']:
  if not ORDERS.exists() or SCORES.exists():raise SystemExit('missing orders or score capture exists')
  lock=json.loads(LOCK.read_text());before=frozen()
  if before!=lock['sources']:raise SystemExit('source drift from lock')
  orders=json.loads(ORDERS.read_text())['workers'];scores=[]
  for order in orders:
   p=subprocess.run([sys.executable,str(RUNNER),'--score-worker'],input=json.dumps(order),cwd=ROOT,env=env,text=True,capture_output=True,timeout=45)
   if p.returncode:raise RuntimeError(f"score worker {order['worker']}: {p.stderr[-3000:]}")
   scores.append(json.loads(p.stdout.strip().splitlines()[-1]))
  if frozen()!=before:raise SystemExit('source drift during score capture')
  SCORES.write_text(json.dumps({'schema':'ThoughtexperimentRecurrenceGeneralStructuralProposalV1_1Scores',
   'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),
   'lock_sha256':sha(LOCK),'orders_sha256':sha(ORDERS),'workers':scores},indent=2,sort_keys=True)+'\n')
  print(SCORES.relative_to(ROOT));return 0
 raise SystemExit('use --lock, --orders, or --scores')
if __name__=='__main__':raise SystemExit(main())
