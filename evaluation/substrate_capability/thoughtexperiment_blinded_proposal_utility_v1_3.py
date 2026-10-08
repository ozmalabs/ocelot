#!/usr/bin/env python3
"""Source-locked, two-stage five-policy panel across four correction families."""
from __future__ import annotations
import hashlib,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'evaluation/substrate_capability')]
RUNNER=Path(__file__).resolve()
ADAPTER=ROOT/'evaluation/substrate_capability/thoughtexperiment_blinded_panel_adapters_v1.py'
POLICY=ROOT/'evaluation/substrate_capability/thoughtexperiment_blinded_panel_rank_policy_v1_1.py'
PROTOCOLS=(ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_BLINDED_PROPOSAL_UTILITY_V1_PREREG_20261002.md',
 ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_BLINDED_PROPOSAL_UTILITY_V1_1_AMENDMENT_20261002.md',
 ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_BLINDED_PROPOSAL_UTILITY_V1_2_AMENDMENT_20261002.md',
 ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_BLINDED_PROPOSAL_UTILITY_V1_3_AMENDMENT_20261002.md',
 ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_BLINDED_PROPOSAL_UTILITY_V1_4_AMENDMENT_20261002.md',
 ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_BLINDED_PROPOSAL_UTILITY_V1_3_SOURCE_REFRESH_20261003.md')
FAMILIES=('shape_axis','recurrence','navigation','control_kind');WORKERS=4
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_blinded_proposal_utility_v1_3_lock_20261003.json'
ORDERS=ROOT/'evaluation/reports/thoughtexperiment_blinded_proposal_utility_v1_3_orders_20261003.json'
SCORES=ROOT/'evaluation/reports/thoughtexperiment_blinded_proposal_utility_v1_3_scores_20261003.json'
ANALYZER=ROOT/'scripts/analyze_thoughtexperiment_blinded_proposal_utility_v1_3.py'
SOURCES=(
 'domains/reflective_faculty.py','domains/collapse_watch.py','domains/collapse_model.py',
 'domains/self_correction.py','domains/self_correct_dispatch.py','domains/imagination.py','domains/edit_ops.py',
 'domains/engine_provenance.py','substrate/boot_core.py','substrate/seed_loader.py',
 'seeds/shape_decode_loop.json','seeds/minting_recurrence_ledger.json','seeds/relation_vocabulary.json',
 'seeds/composer_dispatch.json','seeds/autonomy.json','seeds/grid_navigation.json','seeds/control_kinds.json',
 'runners/dsl/src/py.rs','runners/dsl/src/substrate.rs','runners/dsl/src/graph.rs','runners/dsl/src/graph_rules.rs',
 'runners/dsl/src/term.rs','runners/dsl/src/persist.rs','runners/dsl/src/grammar.rs','runners/dsl/src/sym.rs',
 'runners/dsl/src/lib.rs','runners/dsl/Cargo.toml','runners/dsl/Cargo.lock','runners/dsl/python/substrate_rs/__init__.py')
TASK_FILES=(
 'evaluation/substrate_capability/thoughtexperiment_shape_axis_full_candidate_admission_v1.py',
 'evaluation/substrate_capability/thoughtexperiment_recurrence_candidate_admission_v1.py',
 'evaluation/substrate_capability/thoughtexperiment_control_kind_classification_repair_v1.py',
 'evaluation/substrate_capability/thoughtexperiment_navigation_polarity_repair_v1_1.py',
 'docs/research/engine_substrate/THOUGHTEXPERIMENT_SHAPE_AXIS_FULL_CANDIDATE_ADMISSION_V1_PREREG_20261002.md',
 'docs/research/engine_substrate/THOUGHTEXPERIMENT_RECURRENCE_CANDIDATE_ADMISSION_V1_PREREG_20261002.md',
 'docs/research/engine_substrate/THOUGHTEXPERIMENT_CONTROL_KIND_CLASSIFICATION_REPAIR_V1_PREREG_20261002.md',
 'docs/research/engine_substrate/THOUGHTEXPERIMENT_NAVIGATION_POLARITY_REPAIR_V1_PREREG_20261002.md',
 'docs/research/engine_substrate/THOUGHTEXPERIMENT_NAVIGATION_POLARITY_REPAIR_V1_1_AMENDMENT_20261002.md')
SEEDS={(f,j):420001+100*i+j for i,f in enumerate(FAMILIES) for j in range(WORKERS)}
ARMS=('experience_rank','frozen_rank','default_order','random_order','target_memoization')

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def frozen()->dict:
 from substrate_rs import _native
 paths=(*[ROOT/p for p in SOURCES],*[(ROOT/p) for p in TASK_FILES],ADAPTER,POLICY,RUNNER,ANALYZER,*PROTOCOLS)
 rows={str(p.relative_to(ROOT)):sha(p) for p in paths}
 rows['loaded_native_binary']=sha(Path(_native.__file__).resolve())
 return rows

def _train_worker(index:int)->dict:
 import thoughtexperiment_blinded_panel_adapters_v1 as adapters
 from thoughtexperiment_blinded_panel_rank_policy_v1_1 import policy_orders,descriptors
 before=frozen();training_data={};contexts={}
 for family in FAMILIES:
  ctx=adapters.prepare(family,index,'train');contexts[family]=ctx
  if len(ctx['candidates'])<3:raise RuntimeError(f'{family}: fewer than three candidates')
  labels=[c['label'] for c in ctx['candidates']]
  if len(labels)!=len(set(labels)):raise RuntimeError(f'{family}: duplicate candidate labels')
  started=time.perf_counter_ns();rows=[]
  for candidate in ctx['candidates']:
   outcome=adapters.score(ctx,candidate)
   rows.append({'target_rule':ctx['target'],'candidate_label':candidate['label'],'candidate_digest':outcome['digest'],
    'outcome_class':str(candidate.get('outcome_class') or ''),'task_utility':outcome['utility'],
    'task_cases':outcome['task_cases'],'primary_preserved':outcome['primary_preserved'],
    'receipt_verified':outcome['receipt_verified'],'cost_ns':outcome['cost_ns']})
  training_score_ns=time.perf_counter_ns()-started
  training_data[family]={'candidate_descriptors':descriptors(ctx['candidates']),'outcomes':rows,
   'training_context_setup_ns':ctx['training_context_ns'],'candidate_enumeration_ns':ctx['enumeration_ns'],
   'training_label_generation_ns':training_score_ns}
 families={}
 for family in FAMILIES:
  ctx=contexts[family]
  order=policy_orders(worker=index,evaluation_family=family,candidates=ctx['candidates'],
   training_by_family={f:[{k:r[k] for k in ('target_rule','candidate_label','candidate_digest','outcome_class','task_utility')}
                         for r in training_data[f]['outcomes']] for f in FAMILIES},
   random_seed=SEEDS[family,index],rule_overrides=ctx['rule_overrides'])
  order['task_context_setup_ns']=ctx['training_context_ns']
  order['candidate_enumeration_ns']=ctx['enumeration_ns']
  order['training_label_generation_ns']=training_data[family]['training_label_generation_ns']
  order['baseline_rule_digest']=hashlib.sha256(json.dumps(ctx['rule_overrides'],sort_keys=True,separators=(',',':')).encode()).hexdigest()
  families[family]=order
 after=frozen()
 if before!=after:raise RuntimeError('source drift during train/order worker')
 return {'worker':index,'pid':os.getpid(),'source_before':before,'source_after':after,'source_stable':before==after,
  'training_data_by_family':training_data,'families':families}

def _score_worker(payload:dict)->dict:
 import thoughtexperiment_blinded_panel_adapters_v1 as adapters
 from thoughtexperiment_blinded_panel_rank_policy_v1_1 import descriptors
 before=frozen();families={}
 for family in FAMILIES:
  order_row=payload['families'][family];ctx=adapters.prepare(family,payload['worker'],'heldout')
  expected=order_row['candidate_descriptors'];actual=descriptors(ctx['candidates'])
  if actual!=expected:raise RuntimeError(f'{family}: held-out candidate descriptors differ from frozen order stage')
  bundles={c['label']:c for c in order_row['candidate_bundles']}
  if set(bundles)!=set(order_row['orders']['default_order']):raise RuntimeError(f'{family}: candidate bundle/order mismatch')
  candidate_outcomes={label:adapters.score(ctx,bundles[label]) for label in order_row['orders']['default_order']}
  if set(candidate_outcomes)!=set(bundles):raise RuntimeError(f'{family}: exhaustive candidate outcome matrix is incomplete')
  if not all(item['primary_preserved'] and item['receipt_verified'] for item in candidate_outcomes.values()):
   raise RuntimeError(f'{family}: candidate audit found primary mutation or invalid receipt')
  arms={}
  for arm in ARMS:
   trials=[]
   for label in order_row['orders'][arm]:
    outcome=candidate_outcomes[label];trials.append(outcome)
    if outcome['utility']>=1.0:break
   if not trials or trials[-1]['utility']<1.0:raise RuntimeError(f'{family}/{arm}: no candidate solves held-out task')
   arms[arm]={'order':order_row['orders'][arm],'trials':trials,
    'first_candidate_utility':trials[0]['utility'],'attempts_until_success':len(trials),
    'success':bool(trials[-1]['utility']>=1.0),
    'trial_cost_sum_ns':{key:sum(row['cost_ns'][key] for row in trials) for key in
      ('branch_creation_ns','candidate_patch_ns','task_scoring_ns','adoption_verification_ns','candidate_trial_ns')}}
  families[family]={'candidate_descriptors':actual,'heldout_context_setup_ns':ctx['training_context_ns'],
   'candidate_enumeration_ns':ctx['enumeration_ns'],'candidate_outcomes':list(candidate_outcomes.values()),
   'exhaustive_audit_candidate_trial_cost_ns':sum(x['cost_ns']['candidate_trial_ns'] for x in candidate_outcomes.values()),
   'arms':arms}
 after=frozen()
 return {'worker':payload['worker'],'pid':os.getpid(),'source_before':before,'source_after':after,
  'source_stable':before==after,'families':families}

def _policy_training_cost(worker_row:dict,family:str,arm:str)->int:
 training=worker_row['training_data_by_family']
 if arm=='experience_rank':required=[f for f in FAMILIES if f!=family]
 elif arm=='target_memoization':required=[family]
 else:required=[]
 return sum(int(training[f]['training_context_setup_ns'])+int(training[f]['candidate_enumeration_ns'])+
  int(training[f]['training_label_generation_ns']) for f in required)

def main()->int:
 if sys.argv[1:2]==['--order-worker']:
  print(json.dumps(_train_worker(int(sys.argv[2])),sort_keys=True,separators=(',',':')));return 0
 if sys.argv[1:2]==['--score-worker']:
  print(json.dumps(_score_worker(json.load(sys.stdin)),sort_keys=True,separators=(',',':')));return 0
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit('stale native engine: '+'; '.join(stale))
 if sys.argv[1:]==['--lock']:
  if any(p.exists() for p in (LOCK,ORDERS,SCORES)):raise SystemExit('refusing to overwrite lock or captures')
  LOCK.write_text(json.dumps({'schema':'BlindedProposalUtilityV1_3Lock','sources':frozen(),
   'semantic_engine':rust_source_fingerprint(str(ROOT)),'workers':WORKERS,'families':list(FAMILIES),
   'arms':list(ARMS),'random_seeds':{f'{f}:{w}':SEEDS[f,w] for f in FAMILIES for w in range(WORKERS)},
   'cost_fields':['context_setup_ns','candidate_enumeration_ns','policy_order_ns','training_acquisition_ns',
    'branch_creation_ns','candidate_patch_ns','task_scoring_ns','adoption_verification_ns']},indent=2,sort_keys=True)+'\n')
  print(LOCK.relative_to(ROOT));return 0
 if not LOCK.exists():raise SystemExit('missing source lock')
 lock=json.loads(LOCK.read_text());before=frozen()
 if before!=lock['sources']:raise SystemExit('source drift from panel lock')
 env={**os.environ,'PYTHONPATH':f'{ROOT / "runners/dsl/python"}:{ROOT}:{ROOT / "evaluation/substrate_capability"}'}
 if sys.argv[1:]==['--orders']:
  if ORDERS.exists() or SCORES.exists():raise SystemExit('order or score capture already exists')
  workers=[]
  for i in range(WORKERS):
   p=subprocess.run([sys.executable,str(RUNNER),'--order-worker',str(i)],cwd=ROOT,env=env,text=True,capture_output=True)
   if p.returncode:raise RuntimeError(f'order worker {i}: {p.stderr[-4000:]}')
   workers.append(json.loads(p.stdout.strip().splitlines()[-1]))
  after=frozen()
  if before!=after:raise SystemExit('source drift during order capture')
  ORDERS.write_text(json.dumps({'schema':'BlindedProposalUtilityV1_3OrderCapture',
   'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':{'platform':platform.platform(),
   'machine':platform.machine(),'python':sys.version.split()[0]},'lock':lock,'semantic_engine':rust_source_fingerprint(str(ROOT)),
   'source_before':before,'source_after':after,'workers':workers},indent=2,sort_keys=True)+'\n')
  print(json.dumps({'stage':'orders_frozen','workers':len(workers),'families':list(FAMILIES),'orders':ORDERS.relative_to(ROOT).as_posix()},sort_keys=True));return 0
 if sys.argv[1:]==['--score']:
  if not ORDERS.exists() or SCORES.exists():raise SystemExit('missing frozen orders or score capture exists')
  order_doc=json.loads(ORDERS.read_text());score_rows=[]
  for row in order_doc['workers']:
   p=subprocess.run([sys.executable,str(RUNNER),'--score-worker'],input=json.dumps(row),cwd=ROOT,env=env,text=True,capture_output=True)
   if p.returncode:raise RuntimeError(f"score worker {row['worker']}: {p.stderr[-4000:]}")
   score_rows.append(json.loads(p.stdout.strip().splitlines()[-1]))
  after=frozen()
  if before!=after:raise SystemExit('source drift during score capture')
  order_by_worker={row['worker']:row for row in order_doc['workers']}
  ledger=[]
  for score in score_rows:
   order_row=order_by_worker[score['worker']]
   for family in FAMILIES:
    for arm in ARMS:
     order_ns=int(order_row['families'][family]['policy_order_timing_ns'][arm])
     train_ns=_policy_training_cost(order_row,family,arm)
     eval=score['families'][family]
     eval_setup=int(eval['heldout_context_setup_ns'])+int(eval['candidate_enumeration_ns'])
     trial_ns=int(eval['arms'][arm]['trial_cost_sum_ns']['candidate_trial_ns'])
     ledger.append({'worker':score['worker'],'family':family,'arm':arm,
      'context_and_enumeration_ns':eval_setup,'policy_order_ns':order_ns,
      'required_training_acquisition_ns':train_ns,'attempted_candidate_trial_ns':trial_ns,
      'shared_exhaustive_audit_candidate_trial_ns':int(eval['exhaustive_audit_candidate_trial_cost_ns']),
      'end_to_end_selection_ns':eval_setup+order_ns+train_ns+trial_ns})
  SCORES.write_text(json.dumps({'schema':'BlindedProposalUtilityV1_3ScoreCapture',
   'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'orders_sha256':sha(ORDERS),
   'source_before':before,'source_after':after,'workers':score_rows,'cost_ledger':ledger},indent=2,sort_keys=True)+'\n')
  print(json.dumps({'stage':'heldout_scored_after_order_freeze','workers':len(score_rows),'family_cells':len(ledger),'scores':SCORES.relative_to(ROOT).as_posix()},sort_keys=True));return 0
 raise SystemExit('choose --lock, --orders, or --score')
if __name__=='__main__':raise SystemExit(main())
