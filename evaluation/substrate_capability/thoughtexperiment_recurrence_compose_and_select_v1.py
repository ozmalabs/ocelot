#!/usr/bin/env python3
"""Compose a generic proposal, then select among explicit recurrence hypotheses."""
from __future__ import annotations
import hashlib,json,os,platform,random,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'evaluation/substrate_capability')]
RUNNER=Path(__file__).resolve()
PREREG=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_RECURRENCE_COMPOSE_AND_SELECT_V1_PREREG_20261002.md'
AMENDMENT=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_RECURRENCE_COMPOSE_AND_SELECT_V1_1_AMENDMENT_20261002.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_thoughtexperiment_recurrence_compose_and_select_v1.py'
ADAPTER=ROOT/'evaluation/substrate_capability/thoughtexperiment_blinded_panel_adapters_v1.py'
COMPOSER=ROOT/'evaluation/substrate_capability/thoughtexperiment_recurrence_general_structural_proposal_v1.py'
COMPOSER_RESULTS=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_RECURRENCE_GENERAL_STRUCTURAL_PROPOSAL_V1_1_RESULTS_20261002.md'
BASE=ROOT/'evaluation/substrate_capability/thoughtexperiment_recurrence_candidate_admission_v1.py'
BASE_PROTOCOL=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_RECURRENCE_CANDIDATE_ADMISSION_V1_PREREG_20261002.md'
BASE_RESULTS=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_RECURRENCE_CANDIDATE_ADMISSION_V1_RESULTS_20261002.md'
SELECTOR=ROOT/'domains/contract_query.py'
SOURCES=('domains/contract_query.py','domains/reflective_faculty.py','domains/edit_ops.py',
 'domains/self_correction.py','domains/self_correct_dispatch.py','domains/engine_provenance.py',
 'substrate/boot_core.py','substrate/seed_loader.py','runners/dsl/src/py.rs',
 'runners/dsl/src/substrate.rs','runners/dsl/src/graph.rs','runners/dsl/src/graph_rules.rs',
 'runners/dsl/src/term.rs','runners/dsl/src/persist.rs','runners/dsl/src/grammar.rs',
 'runners/dsl/src/sym.rs','runners/dsl/src/lib.rs','runners/dsl/Cargo.toml','runners/dsl/Cargo.lock',
 'runners/dsl/python/substrate_rs/__init__.py','seeds/minting_recurrence_ledger.json',
 'seeds/relation_vocabulary.json','seeds/composer_dispatch.json','seeds/autonomy.json')
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_recurrence_compose_and_select_v1_1_lock_20261002.json'
ORDERS=ROOT/'evaluation/reports/thoughtexperiment_recurrence_compose_and_select_v1_1_orders_20261002.json'
SCORES=ROOT/'evaluation/reports/thoughtexperiment_recurrence_compose_and_select_v1_1_scores_20261002.json'
WORKERS=4;REPEATS=2;SEED=20261021;TARGET='mrl_offer_due_once'
CUE=['mrl','offer','due','once','guard','constrain','restrict','narrow','extra','condition','equality']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def frozen():
 from substrate_rs import _native
 paths=[ROOT/p for p in SOURCES]+[RUNNER,PREREG,AMENDMENT,ANALYZER,ADAPTER,COMPOSER,COMPOSER_RESULTS,BASE,BASE_PROTOCOL,BASE_RESULTS,SELECTOR]
 out={str(p.relative_to(ROOT)):sha(p) for p in paths};out['loaded_native_binary']=sha(Path(_native.__file__).resolve());return out
def digest(c):
 from thoughtexperiment_recurrence_candidate_admission_v1 import canonical_digest
 return canonical_digest(c)
def build_pool(worker):
 import thoughtexperiment_blinded_panel_adapters_v1 as adapters
 import domains.reflective_faculty as rf
 ctx=adapters.prepare('recurrence',worker,'train');sub=ctx['sub'];key=f'compose_select_{worker}'
 sub.add_node('CapabilityAxis',{'is_axis':1.0,'capability_keys':[key],'induced':1.0,
  'residual_predicates':CUE,'structural_rule_scope':'all_mutable_rules','from_observation':1.0,
  'source':'recurrence_compose_and_select_v1'})
 start=time.perf_counter_ns();result=rf.compose_general_structural_variant(sub,[key],f'compose_select_{worker}')
 compose_ns=time.perf_counter_ns()-start
 if not result.get('built'):raise RuntimeError(f"composer abstained: {result.get('wall')}")
 generic={'label':'composer_'+str(result['kind']),'rules':{result['removed_rule']:result['rule']}}
 candidates=list(ctx['candidates'])+[generic]
 descriptors=[{'proposal_id':digest(c),'label':str(c.get('label','')),'target':TARGET} for c in candidates]
 if len(descriptors)!=9 or len({x['proposal_id'] for x in descriptors})!=9:raise RuntimeError('candidate set is not nine unique hypotheses')
 return ctx,candidates,descriptors,{'compose_ns':compose_ns,'operator':result['kind'],'site':result.get('site'),'target':result.get('removed_rule')}
def score_candidate(task_id,split,candidate):
 from thoughtexperiment_recurrence_candidate_admission_v1 import score_candidate as score
 row=score(task_id,split,candidate)
 correct=row.get('offer_counts')==[1,1] and row.get('fixedpoint_progress')==0
 return {'correct':correct,'offer_counts':row.get('offer_counts'),'fixedpoint_progress':row.get('fixedpoint_progress'),
  'recurrence_keys':row.get('recurrence_keys'),
  'first_candidate_sweeps':row.get('first_candidate_sweeps'),'second_candidate_sweeps':row.get('second_candidate_sweeps')}
def order_worker(worker):
 from domains.contract_query import select_candidate_from_graph_evidence
 before=frozen();ctx,candidates,descriptors,cmeta=build_pool(worker);rng=random.Random(SEED+worker)
 permutation=list(range(len(candidates)));rng.shuffle(permutation)
 candidates=[candidates[i] for i in permutation];descriptors=[descriptors[i] for i in permutation]
 outcomes=[];evidence=[];training_keys=[];task_ns=0
 for ci,candidate in enumerate(candidates):
  pid=descriptors[ci]['proposal_id'];rows=[]
  for sample in range(REPEATS):
   task_id=worker*100000+sample
   t=time.perf_counter_ns();row=score_candidate(task_id,f'train_{worker}_{sample}',candidate);task_ns+=time.perf_counter_ns()-t
   probe=f'train_{worker}_{sample}';rows.append({'probe_id':probe,**row})
   evidence.append({'proposal_id':pid,'probe_id':probe,'predicted':'correct' if row['correct'] else 'incorrect','expected':'correct'})
   training_keys.extend(row.get('recurrence_keys') or [])
  outcomes.append({'proposal_id':pid,'label':descriptors[ci]['label'],'rows':rows})
 primary_rules=ctx['native'].export_rules();branch=ctx['sub'].snapshot().fork()
 start=time.perf_counter_ns();decision=select_candidate_from_graph_evidence(branch,f'compose_select_{worker}',
  [{'proposal_id':x['proposal_id'],'proposal_label':'hypothesis'} for x in descriptors],evidence)
 decision_ns=time.perf_counter_ns()-start
 winner=decision.get('proposal_id');selected_label=next((x['label'] for x in descriptors if x['proposal_id']==winner),None)
 decision.pop('proposal_node',None)
 controls={}
 for control,value in (('all_wrong','incorrect'),('tie','correct')):
  b=ctx['sub'].snapshot().fork();ev=[{'proposal_id':d['proposal_id'],'probe_id':f'{control}_{j}',
    'predicted':value,'expected':'correct'} for d in descriptors for j in range(2)]
  x=select_candidate_from_graph_evidence(b,f'compose_select_{control}_{worker}',
   [{'proposal_id':d['proposal_id'],'proposal_label':'hypothesis'} for d in descriptors],ev);x.pop('proposal_node',None);controls[control]=x
 after=frozen()
 return {'worker':worker,'candidate_descriptors':descriptors,'candidate_outcomes':outcomes,
  'selector_proposals':[{'proposal_id':d['proposal_id'],'proposal_label':'hypothesis'} for d in descriptors],
  'selector_training_evidence':evidence,
  'training_keys':training_keys,'decision':decision,'selected_label':selected_label,'controls':controls,
  'composer':cmeta,'composer_selected_candidate_id':next((x['proposal_id'] for x in descriptors if x['label'].startswith('composer_')),None),
  'candidate_order':permutation,'enumeration_and_composition_ns':cmeta['compose_ns'],
  'training_scoring_ns':task_ns,'selector_ns':decision_ns,
  'primary_rules_unchanged':ctx['native'].export_rules()==primary_rules,
  'branch_evidence_isolated':not ctx['sub'].nodes('CandidateProposal') and not ctx['sub'].nodes('CandidateEvidence'),
  'source_before':before,'source_after':after,'source_stable':before==after}
def score_worker(order):
 before=frozen();worker=int(order['worker']);ctx,candidates,descriptors,cmeta=build_pool(worker)
 permutation=order['candidate_order'];candidates=[candidates[i] for i in permutation];descriptors=[descriptors[i] for i in permutation]
 if descriptors!=order['candidate_descriptors']:raise RuntimeError('candidate descriptors/order mismatch')
 pid=order['decision'].get('proposal_id');candidate=next((c for c in candidates if digest(c)==pid),None)
 if candidate is None:raise RuntimeError('frozen winner missing from regenerated candidate set')
 rows=[];times=[]
 for sample in range(REPEATS):
  task_id=worker*100000+1000+sample;t=time.perf_counter_ns()
  row=score_candidate(task_id,f'heldout_{worker}_{sample}',candidate);times.append(time.perf_counter_ns()-t);rows.append(row)
 after=frozen()
 return {'worker':worker,'selected_digest':pid,'selected_label':next(x['label'] for x in descriptors if x['proposal_id']==pid),
  'heldout_rows':rows,'heldout_runtime_ns':times,'composer_regenerated':cmeta,
  'source_before':before,'source_after':after,'source_stable':before==after}
def main():
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit('stale native engine: '+'; '.join(stale))
 env={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}:{ROOT}/evaluation/substrate_capability'}
 args=sys.argv[1:]
 if args[:1]==['--order-worker']:
  print(json.dumps(order_worker(int(args[1])),sort_keys=True,separators=(',',':')));return 0
 if args[:1]==['--score-worker']:
  print(json.dumps(score_worker(json.load(sys.stdin)),sort_keys=True,separators=(',',':')));return 0
 if args==['--lock']:
  if any(p.exists() for p in (LOCK,ORDERS,SCORES)):raise SystemExit('refusing to overwrite')
  LOCK.write_text(json.dumps({'schema':'ThoughtexperimentRecurrenceComposeAndSelectV1_1Lock','sources':frozen(),
   'semantic_engine':rust_source_fingerprint(str(ROOT)),'workers':WORKERS,'repeats':REPEATS,
   'seed':SEED,'target':TARGET,'candidate_count':9,'composer_operator':'add_match_guard',
   'selector':'select_candidate_from_graph_evidence','positive_reference':'dedup_identity_fix',
   'cue':CUE,'train_then_heldout':True},indent=2,sort_keys=True)+'\n')
  print(LOCK.relative_to(ROOT));return 0
 if args==['--orders']:
  if not LOCK.exists() or ORDERS.exists() or SCORES.exists():raise SystemExit('missing lock or captures already exist')
  lock=json.loads(LOCK.read_text());before=frozen()
  if before!=lock['sources']:raise SystemExit('source drift from lock')
  workers=[]
  for i in range(WORKERS):
   p=subprocess.run([sys.executable,str(RUNNER),'--order-worker',str(i)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=90)
   if p.returncode:raise RuntimeError(f'order worker {i}: {p.stderr[-3000:]}')
   workers.append(json.loads(p.stdout.strip().splitlines()[-1]))
  if frozen()!=before:raise SystemExit('source drift during order capture')
  ORDERS.write_text(json.dumps({'schema':'ThoughtexperimentRecurrenceComposeAndSelectV1_1Orders','lock_sha256':sha(LOCK),
   'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),'workers':workers},indent=2,sort_keys=True)+'\n')
  print(ORDERS.relative_to(ROOT));return 0
 if args==['--scores']:
  if not ORDERS.exists() or SCORES.exists():raise SystemExit('missing orders or scores already exist')
  lock=json.loads(LOCK.read_text());before=frozen()
  if before!=lock['sources']:raise SystemExit('source drift from lock')
  workers=[]
  for order in json.loads(ORDERS.read_text())['workers']:
   p=subprocess.run([sys.executable,str(RUNNER),'--score-worker'],input=json.dumps(order),cwd=ROOT,env=env,text=True,capture_output=True,timeout=90)
   if p.returncode:raise RuntimeError(f"score worker {order['worker']}: {p.stderr[-3000:]}")
   workers.append(json.loads(p.stdout.strip().splitlines()[-1]))
  if frozen()!=before:raise SystemExit('source drift during heldout scoring')
  SCORES.write_text(json.dumps({'schema':'ThoughtexperimentRecurrenceComposeAndSelectV1_1Scores','lock_sha256':sha(LOCK),
   'orders_sha256':sha(ORDERS),'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'workers':workers},indent=2,sort_keys=True)+'\n')
  print(SCORES.relative_to(ROOT));return 0
 raise SystemExit('use --lock, --orders, --scores')
if __name__=='__main__':raise SystemExit(main())
