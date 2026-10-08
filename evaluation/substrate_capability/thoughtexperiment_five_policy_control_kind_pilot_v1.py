#!/usr/bin/env python3
"""Locked two-stage five-policy order/scoring pilot on control-kind repair."""
from __future__ import annotations
import hashlib,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'evaluation/substrate_capability')]
RUNNER=Path(__file__).resolve()
POLICY=ROOT/'evaluation/substrate_capability/thoughtexperiment_blinded_panel_rank_policy_v1.py'
PROTOCOL=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_FIVE_POLICY_CONTROL_KIND_PILOT_V1_PREREG_20261002.md'
CONTROL_RUNNER=ROOT/'evaluation/substrate_capability/thoughtexperiment_control_kind_classification_repair_v1.py'
REC_RAW=ROOT/'evaluation/reports/thoughtexperiment_recurrence_candidate_admission_v1_raw_20261002.json'
NAV_RAW=ROOT/'evaluation/reports/thoughtexperiment_navigation_outcome_rank_integration_v1_raw_20261002.json'
SHAPE_RAW=ROOT/'evaluation/reports/thoughtexperiment_shape_axis_full_candidate_admission_v1_raw_20261002.json'
SHAPE_RUNNER=ROOT/'evaluation/substrate_capability/thoughtexperiment_shape_axis_full_candidate_admission_v1.py'
SHAPE_PROTOCOL=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_SHAPE_AXIS_FULL_CANDIDATE_ADMISSION_V1_PREREG_20261002.md'
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_five_policy_control_kind_pilot_v1_lock_20261002.json'
ORDERS=ROOT/'evaluation/reports/thoughtexperiment_five_policy_control_kind_pilot_v1_orders_20261002.json'
SCORES=ROOT/'evaluation/reports/thoughtexperiment_five_policy_control_kind_pilot_v1_scores_20261002.json'
SOURCES=('domains/reflective_faculty.py','domains/self_correct_dispatch.py','domains/self_correction.py',
 'domains/edit_ops.py','domains/engine_provenance.py','substrate/boot_core.py','substrate/seed_loader.py',
 'seeds/control_kinds.json','seeds/relation_vocabulary.json','seeds/composer_dispatch.json','seeds/autonomy.json',
 'runners/dsl/src/py.rs','runners/dsl/src/substrate.rs','runners/dsl/src/graph.rs','runners/dsl/src/graph_rules.rs',
 'runners/dsl/src/term.rs','runners/dsl/src/persist.rs','runners/dsl/src/grammar.rs','runners/dsl/src/sym.rs',
 'runners/dsl/src/lib.rs','runners/dsl/Cargo.toml','runners/dsl/Cargo.lock','runners/dsl/python/substrate_rs/__init__.py')
WORKERS=4

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def frozen()->dict:
 from substrate_rs import _native
 rows={p:sha(ROOT/p) for p in SOURCES}
 rows.update({str(p.relative_to(ROOT)):sha(p) for p in (RUNNER,POLICY,PROTOCOL,CONTROL_RUNNER,REC_RAW,NAV_RAW,SHAPE_RAW,SHAPE_RUNNER,SHAPE_PROTOCOL)})
 rows['loaded_native_binary']=sha(Path(_native.__file__).resolve())
 return rows

def training_records(index:int,candidates:list[dict])->tuple[dict,list[dict],int]:
 import thoughtexperiment_control_kind_classification_repair_v1 as control
 from thoughtexperiment_blinded_panel_rank_policy_v1 import bundle_digest
 started=time.perf_counter_ns();rows=[]
 for candidate in candidates:
  variant=candidate['rules'][control.TARGET]
  cases=[control.score_case(variant,case) for case in control.TRAIN]
  rows.append({'target_rule':control.TARGET,'candidate_label':candidate['label'],
   'candidate_digest':bundle_digest(candidate),'outcome_class':str(candidate.get('outcome_class') or ''),
   'task_utility':float(bool(cases) and all(x['pass'] for x in cases)),
   'training_cases':cases})
 return rows,time.perf_counter_ns()-started

def load_transfer_training(index:int)->dict[str,list[dict]]:
 import thoughtexperiment_shape_axis_full_candidate_admission_v1 as shape_runner
 from thoughtexperiment_blinded_panel_rank_policy_v1 import bundle_digest
 rec=json.loads(REC_RAW.read_text())['workers'][index%3]['candidate_outcomes']
 nav=json.loads(NAV_RAW.read_text())['workers'][index%3]['training_scores']
 shape=json.loads(SHAPE_RAW.read_text())['workers'][index]['training_outcomes']
 _sub,_agent,_native,_model,shape_candidates,_cost=shape_runner.build_context(index,'train')
 shape_class={c['label']:str(c.get('outcome_class') or '') for c in shape_candidates}
 shape_digests={c['label']:bundle_digest(c) for c in shape_candidates}
 if any(shape_digests.get(x['label'])!=x['digest'] for x in shape):
  raise RuntimeError('shape training outcome descriptors disagree with the current candidate generator')
 result={
  'recurrence':[{'target_rule':'mrl_offer_due_once','candidate_label':x['label'],'candidate_digest':x['digest'],
   'outcome_class':str(x.get('outcome_class') or ''),'task_utility':float(x['training']['pass'])} for x in rec],
  'navigation':[{'target_rule':'hop_descend_gradient','candidate_label':label,
   'task_utility':float(row['utility'])} for label,row in nav.items()],
  'shape_axis':[{'target_rule':'sd_mint_quantum','candidate_label':x['label'],'candidate_digest':x['digest'],
   'outcome_class':shape_class[x['label']],'task_utility':float(x['utility'])} for x in shape],
 }
 return result

def order_worker(index:int)->dict:
 import thoughtexperiment_control_kind_classification_repair_v1 as control
 from thoughtexperiment_blinded_panel_rank_policy_v1 import policy_orders,bundle_digest
 before=frozen();started=time.perf_counter_ns()
 sub,root,native,source,fault,candidates=control.rule_setup(None)
 candidates=[c for c in candidates if c.get('rules',{}).get(control.TARGET) is not None]
 enum_ns=time.perf_counter_ns()-started
 if len(candidates)!=6:raise RuntimeError('control-kind candidate set changed')
 local_records,train_ns=training_records(index,candidates)
 other=load_transfer_training(index)
 training={**other,'control_kind':[
  {'target_rule':control.TARGET,'candidate_label':row['candidate_label'],
   'candidate_digest':row['candidate_digest'],'outcome_class':row['outcome_class'],
   'task_utility':row['task_utility']} for row in local_records]}
 order=policy_orders(worker=index,evaluation_family='control_kind',candidates=candidates,
  training_by_family=training,random_seed=420001+index,rule_overrides={control.TARGET:fault})
 after=frozen()
 if before!=after:raise RuntimeError('source drift in order worker')
 # Keep training case labels internal to this order-stage artifact; no held-out values/code output.
 order['source_before']=before;order['source_after']=after;order['source_stable']=before==after
 order['candidate_enumeration_ns']=enum_ns;order['training_label_generation_ns']=train_ns
 order['training_outcomes']=[{k:v for k,v in row.items() if k!='training_cases'} for row in local_records]
 return order

def score_worker(payload:dict)->dict:
 import thoughtexperiment_control_kind_classification_repair_v1 as control
 before=frozen();candidate_by_label={c['label']:c for c in payload['candidate_bundles']};arms={}
 for arm,order in payload['orders'].items():
  trials=[]
  for label in order:
   candidate=candidate_by_label[label];started=time.perf_counter_ns()
   outcomes=[control.score_case(candidate['rules'][control.TARGET],case) for case in control.HELDOUT]
   elapsed=time.perf_counter_ns()-started;utility=float(bool(outcomes) and all(x['pass'] for x in outcomes))
   trials.append({'label':label,'heldout_utility':utility,'outcomes':outcomes,'trial_elapsed_ns':elapsed})
   if utility>=1.0:break
  arms[arm]={'order':order,'trials':trials,'first_candidate_utility':trials[0]['heldout_utility'],
   'attempts_until_success':len(trials),'success':bool(trials[-1]['heldout_utility']>=1.0)}
 after=frozen()
 return {'worker':payload['worker'],'source_before':before,'source_after':after,'source_stable':before==after,'arms':arms}

def main()->int:
 if sys.argv[1:2]==['--order-worker']:
  print(json.dumps(order_worker(int(sys.argv[2])),sort_keys=True,separators=(',',':')));return 0
 if sys.argv[1:2]==['--score-worker']:
  print(json.dumps(score_worker(json.load(sys.stdin)),sort_keys=True,separators=(',',':')));return 0
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit('stale native engine: '+'; '.join(stale))
 if sys.argv[1:]==['--lock']:
  if any(p.exists() for p in (LOCK,ORDERS,SCORES)):raise SystemExit('refusing to overwrite lock/captures')
  LOCK.write_text(json.dumps({'schema':'FivePolicyControlKindPilotV1Lock','sources':frozen(),
   'semantic_engine':rust_source_fingerprint(str(ROOT)),'workers':WORKERS,
   'random_seeds':[420001+i for i in range(WORKERS)],
   'transfer_families':['recurrence','navigation','shape_axis']},indent=2,sort_keys=True)+'\n')
  print(LOCK.relative_to(ROOT));return 0
 if not LOCK.exists():raise SystemExit('missing source lock')
 lock=json.loads(LOCK.read_text());before=frozen()
 if before!=lock['sources']:raise SystemExit('source drift from lock')
 env={**os.environ,'PYTHONPATH':f'{ROOT / "runners/dsl/python"}:{ROOT}:{ROOT / "evaluation/substrate_capability"}'}
 if sys.argv[1:]==['--orders']:
  if ORDERS.exists() or SCORES.exists():raise SystemExit('order/score capture already exists')
  workers=[]
  for i in range(WORKERS):
   p=subprocess.run([sys.executable,str(RUNNER),'--order-worker',str(i)],cwd=ROOT,env=env,text=True,capture_output=True)
   if p.returncode:raise RuntimeError(f'order worker {i}: {p.stderr[-3000:]}')
   workers.append(json.loads(p.stdout.strip().splitlines()[-1]))
  after=frozen()
  if before!=after:raise SystemExit('source drift during order capture')
  ORDERS.write_text(json.dumps({'schema':'FivePolicyControlKindPilotV1OrderCapture',
   'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':{'platform':platform.platform(),
   'machine':platform.machine(),'python':sys.version.split()[0]},'lock':lock,'source_before':before,
   'source_after':after,'semantic_engine':rust_source_fingerprint(str(ROOT)),'workers':workers},indent=2,sort_keys=True)+'\n')
  print(json.dumps({'stage':'orders_frozen','workers':len(workers),'orders':str(ORDERS.relative_to(ROOT))},sort_keys=True));return 0
 if sys.argv[1:]==['--score']:
  if not ORDERS.exists() or SCORES.exists():raise SystemExit('missing orders or score capture exists')
  order_doc=json.loads(ORDERS.read_text());scores=[]
  for row in order_doc['workers']:
   payload={'worker':row['worker'],'candidate_bundles':row['candidate_bundles'],'orders':row['orders']}
   p=subprocess.run([sys.executable,str(RUNNER),'--score-worker'],input=json.dumps(payload),cwd=ROOT,env=env,text=True,capture_output=True)
   if p.returncode:raise RuntimeError(f"score worker {row['worker']}: {p.stderr[-3000:]}")
   scores.append(json.loads(p.stdout.strip().splitlines()[-1]))
  after=frozen()
  if before!=after:raise SystemExit('source drift during held-out scoring')
  SCORES.write_text(json.dumps({'schema':'FivePolicyControlKindPilotV1ScoreCapture',
   'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'orders_sha256':sha(ORDERS),
   'source_before':before,'source_after':after,'workers':scores},indent=2,sort_keys=True)+'\n')
  print(json.dumps({'stage':'heldout_scored_after_orders','workers':len(scores),'scores':str(SCORES.relative_to(ROOT))},sort_keys=True));return 0
 raise SystemExit('choose --lock, --orders, or --score')
if __name__=='__main__':raise SystemExit(main())
