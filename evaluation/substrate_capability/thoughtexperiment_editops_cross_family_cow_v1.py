#!/usr/bin/env python3
"""Cross-family generated edge-guard selection on CoW branches."""
from __future__ import annotations
import copy,hashlib,importlib.util,json,os,platform,random,subprocess,sys,threading,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'evaluation/substrate_capability')]
RUNNER=Path(__file__).resolve()
PREREG=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_EDITOPS_CROSS_FAMILY_COW_V1_PREREG_20261003.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_thoughtexperiment_editops_cross_family_cow_v1.py'
BASE=ROOT/'evaluation/substrate_capability/thoughtexperiment_bidirectional_edge_identity_guards_v1_1.py'
EDITOPS_WRAPPER=ROOT/'evaluation/substrate_capability/thoughtexperiment_editops_edge_hypotheses_v1.py'
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_editops_cross_family_cow_v1_lock_20261003.json'
ORDERS=ROOT/'evaluation/reports/thoughtexperiment_editops_cross_family_cow_v1_orders_20261003.json'
SCORES=ROOT/'evaluation/reports/thoughtexperiment_editops_cross_family_cow_v1_scores_20261003.json'
FAMILIES=('recurrence','conversation');BACKENDS=('full_copy','shared_graph_pages')
WORKERS=4;SEED=20261036;CAP=100

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;assert spec.loader;spec.loader.exec_module(m);return m
def modules():
 b=load('cross_family_base',BASE);w=load('cross_family_editops',EDITOPS_WRAPPER);w.install(b);return b,w
def frozen():
 from substrate_rs import _native
 from domains.engine_provenance import rust_source_fingerprint
 b,w=modules()
 files=[RUNNER,PREREG,ANALYZER,BASE,EDITOPS_WRAPPER,
  ROOT/'evaluation/substrate_capability/thoughtexperiment_bidirectional_edge_identity_guards_v1_1_lock_20261002.json',
  ROOT/'evaluation/reports/thoughtexperiment_bidirectional_edge_identity_guards_v1_1_orders_20261002.json',
  ROOT/'evaluation/reports/thoughtexperiment_bidirectional_edge_identity_guards_v1_1_scores_20261002.json',
  ROOT/'evaluation/substrate_capability/analyze_thoughtexperiment_bidirectional_edge_identity_guards_v1_1.py',
  ROOT/'evaluation/substrate_capability/analyze_thoughtexperiment_editops_edge_hypotheses_v1.py',
  ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_EDITOPS_EDGE_HYPOTHESES_V1_PREREG_20261002.md',
  ROOT/'domains/edit_ops.py',ROOT/'domains/contract_query.py',ROOT/'domains/reflective_faculty.py',
  ROOT/'domains/seed_registry.py',ROOT/'domains/discourse_state.py',ROOT/'substrate/world_adapter.py',
  ROOT/'substrate/boot_core.py',ROOT/'substrate/seed_loader.py',ROOT/'runners/dsl/python/substrate_rs/__init__.py',
  ROOT/'runners/dsl/src/substrate.rs',ROOT/'runners/dsl/src/graph.rs',ROOT/'runners/dsl/src/rewrite.rs',
  ROOT/'runners/dsl/src/cow_paged_vec.rs',ROOT/'runners/dsl/src/cow_sharded_map.rs',ROOT/'runners/dsl/Cargo.lock']
 for p in b.SOURCES: files.append(ROOT/p)
 files=list(dict.fromkeys(files))
 return {'files':{str(p.relative_to(ROOT)):sha(p) for p in files},
  'base_frozen':b.frozen(),'editops_wrapper_frozen':w.frozen(),
  'native_binary':{'path':str(Path(_native.__file__).resolve()),'sha256':sha(Path(_native.__file__).resolve())},
  'semantic_engine':rust_source_fingerprint(str(ROOT))}
def make_pool(family,worker):
 b,_=modules();ctx,cands,desc,sites,compose_ns,composer,pt=b.build_pool(family,worker)
 return ctx,cands,desc,sites,compose_ns,composer,pt
def make_ctx(b,family,worker,split,fault):
 return b.recurrence_context(worker,split,0,fault=fault) if family=='recurrence' else b.conversation_context(fault=fault)
def execute_recurrence(ctx,branch):
 native=branch._inner;worker=ctx['keys'][0].split('-')[1];keys=ctx['keys']
 sweep0=[int(native.run_rules(CAP)) for _ in range(5)]
 j=1;key=keys[j];attrs={'predicate':'bind','recurrence_key':key,
  'structural_signature':[['relation','bind','ITEM',f'SLOT{j}',int(worker)]],
  'capability_key':[key,'X']}
 cand=branch.add_node('PredicateRecurrenceCandidate',attrs)
 ev=branch.add_node('ResidualSegmentEvidence',{**attrs,'segment_ordinal':j,'integer_native':1})
 branch.add_edge(ctx['episode'],'has_predicate_recurrence_candidate',cand)
 branch.add_edge(cand,'supported_by_segment',ev)
 sweep1=[int(native.run_rules(CAP)) for _ in range(5)]
 counts=[]
 for k in keys:
  n=next(n for n in branch.nodes('PredicateRecurrenceCandidate') if branch.node(n)['attrs'].get('recurrence_key')==k)
  counts.append(len(list(branch.neighbours(n,'has_mint_offer'))))
 fixed=int(native.run_rules(CAP))
 return {'correct':counts==[1,1] and fixed==0,'output_counts':counts,'expected_counts':[1,1],
  'fixedpoint_progress':fixed,'stage0_sweeps':sweep0,'stage1_sweeps':sweep1}
def execute_conversation(ctx,branch,split):
 wa=copy.copy(ctx['adapter']);wa.s=branch;wa.inner=branch._inner;wa._conversation_lock=threading.RLock()
 seq=modules()[0].TRAIN_CONVERSATION if split.startswith('train') else modules()[0].HELDOUT_CONVERSATION
 counts=[];ids=[];start=time.perf_counter_ns()
 for i,(text,act) in enumerate(seq):
  mid=wa.receive_utterance(text,speech_act=act,speaker='user',tick=i);wa.comprehend()
  ids.append(str(mid));counts.append(sum(1 for reply in wa.agent_outbound_messages() if mid in wa.responds_to(reply)))
 return {'correct':counts==[1]*len(seq),'output_counts':counts,'expected_counts':[1]*len(seq),
  'input_ids':ids,'sequence_runtime_ns':time.perf_counter_ns()-start}
def run_branch(family,worker,split,candidate,backend,return_receipt=False):
 from domains.engine_provenance import build_is_stale
 if build_is_stale(str(ROOT)):raise RuntimeError('stale native engine')
 b,_=modules();ctx=make_ctx(b,family,worker,split,candidate is not None)
 parent,native,agent,target=ctx['sub'],ctx['native'],ctx['agent'],ctx['target']
 rules0=digest(native.export_rules());rev=tuple(parent.experiment_graph_rule_revision())
 receipt=parent.add_node('ThoughtExperimentProposal',{'proposal_status':'unselected','target_rule':target,'family':family})
 graph0=digest(parent.graph_to_dict());rev=tuple(parent.experiment_graph_rule_revision())
 t=time.perf_counter_ns();snap=parent._snapshot_with_backend(backend);branch=snap.fork();snapshot_ns=time.perf_counter_ns()-t
 patch_ns=0
 if candidate is not None:
  t=time.perf_counter_ns();ok=branch.replace_active_rule_by_name(target,candidate['rules'][target]);patch_ns=time.perf_counter_ns()-t
  if not ok:raise RuntimeError(f'{family}: branch rule patch failed')
 t=time.perf_counter_ns()
 result=execute_recurrence(ctx,branch) if family=='recurrence' else execute_conversation(ctx,branch,split)
 closure_ns=time.perf_counter_ns()-t
 primary_unchanged=digest(parent.graph_to_dict())==graph0 and digest(native.export_rules())==rules0 and tuple(parent.experiment_graph_rule_revision())==rev
 if not primary_unchanged:raise RuntimeError(f'{family}: branch changed primary')
 returned=None
 if return_receipt:
  if candidate is None or not result['correct']:raise RuntimeError('cannot return an invalid proposal')
  branch.begin_experiment_delta_journal();branch.checkpoint_experiment_delta_journal()
  branch.set_attr(receipt,'proposal_status','selected_from_training')
  branch.set_attr(receipt,'candidate_id',candidate['proposal_id'])
  branch.set_attr(receipt,'candidate_label',candidate['label'])
  branch.set_attr(receipt,'candidate_rule_json',json.dumps(candidate['rules'][target],sort_keys=True))
  branch.set_attr(receipt,'training_exact',1.0)
  t=time.perf_counter_ns();delta=branch.finish_experiment_delta_journal().get('derived_only',{});extract_ns=time.perf_counter_ns()-t
  t=time.perf_counter_ns();parent.apply_experiment_graph_delta(rev,delta);adopt_ns=time.perf_counter_ns()-t
  parent_receipt=parent.node(receipt)['attrs'];branch_receipt=branch.node(receipt)['attrs'];after=digest(parent.graph_to_dict())
  try:parent.apply_experiment_graph_delta(rev,delta);stale=True
  except RuntimeError:stale=False
  returned={'delta':delta,'receipt_parity':parent_receipt==branch_receipt,'stale_retry_rejected':not stale,
   'stale_retry_unchanged':digest(parent.graph_to_dict())==after,'primary_rules_preserved':digest(native.export_rules())==rules0,
   'parent_receipt':parent_receipt,'branch_receipt':branch_receipt,
   'extract_ns':extract_ns,'adopt_ns':adopt_ns}
 return {'family':family,'worker':worker,'split':split,'backend':backend,
  'candidate_id':None if candidate is None else candidate['proposal_id'],
  'candidate_label':'source_rule' if candidate is None else candidate['label'],
  'result':result,'snapshot_ns':snapshot_ns,'rule_patch_ns':patch_ns,'branch_execution_ns':closure_ns,
  'primary_unchanged_before_return':primary_unchanged,'receipt_return':returned}
def decide(sub,family,worker,desc,evidence,control=None):
 return modules()[0].selector_decision(sub,f'cross_cow_{family}',worker,desc,evidence,control)
def order_worker(worker):
 before=frozen();families={}
 for fi,family in enumerate(FAMILIES):
  ctx,cands,desc,sites,compose_ns,composer,pt=make_pool(family,worker)
  perm=list(range(len(cands)));random.Random(SEED+worker*100+fi).shuffle(perm)
  cands=[cands[i] for i in perm];desc=[desc[i] for i in perm]
  for candidate,descriptor in zip(cands,desc):candidate['proposal_id']=descriptor['proposal_id']
  training={b:[run_branch(family,worker,f'train_{worker}',c,b) for c in cands] for b in BACKENDS}
  evidence=[{'proposal_id':r['candidate_id'],'probe_id':f'{family}_train_{worker}',
   'predicted':'correct' if r['result']['correct'] else 'incorrect','expected':'correct'}
   for r in training['shared_graph_pages']]
  t=time.perf_counter_ns();decision=decide(ctx['sub'],family,worker,desc,evidence);selector_ns=time.perf_counter_ns()-t;decision.pop('proposal_node',None)
  controls={}
  for name in ('all_wrong','tie'):
   control=decide(ctx['sub'],family,worker,desc,evidence,name);control.pop('proposal_node',None);controls[name]=control
  selected=next((c for c in cands if c['proposal_id']==decision.get('proposal_id')),None)
  source={b:run_branch(family,worker,f'train_source_{worker}',None,b) for b in BACKENDS}
  families[family]={'candidate_order':perm,'descriptors':desc,'candidate_rules':[c['rules'] for c in cands],
   'sites':sites,'composer':composer,'training':training,'evidence':evidence,'decision':decision,
   'selected_label':None if selected is None else selected['label'],'controls':controls,'source_controls':source,
   'compose_ns':compose_ns,'site_generation_ns':pt['generic_generation_ns'],'selector_ns':selector_ns}
 after=frozen()
 if before!=after:raise RuntimeError('source drift in order stage')
 return {'worker':worker,'pid':os.getpid(),'families':families,'source_before':before,'source_after':after,'source_stable':before==after}
def score_worker(order):
 before=frozen();worker=int(order['worker']);scores={};adoptions={}
 for family in FAMILIES:
  row=order['families'][family];target=modules()[0].TARGETS[family]
  cands=[{'proposal_id':d['proposal_id'],'label':d['label'],'rules':rules}
    for d,rules in zip(row['descriptors'],row['candidate_rules'])]
  selected=next((c for c in cands if c['proposal_id']==row['decision'].get('proposal_id')),None)
  if selected is None:raise RuntimeError(f'{family}: selector abstained')
  adoptions[family]=run_branch(family,worker,f'train_adopt_{worker}',selected,'shared_graph_pages',return_receipt=True)
  scores[family]={b:[run_branch(family,worker,f'heldout_{worker}',c,b) for c in cands] for b in BACKENDS}
  scores[family]['source_controls']={b:run_branch(family,worker,f'heldout_source_{worker}',None,b) for b in BACKENDS}
 after=frozen()
 if before!=after:raise RuntimeError('source drift in held-out stage')
 return {'worker':worker,'pid':os.getpid(),'adoptions':adoptions,'heldout':scores,
  'source_before':before,'source_after':after,'source_stable':before==after}
def main():
 args=sys.argv[1:]
 if args==['--lock']:
  if any(p.exists() for p in (LOCK,ORDERS,SCORES)):raise SystemExit('refusing to overwrite artifacts')
  from domains.engine_provenance import build_is_stale
  stale=build_is_stale(str(ROOT))
  if stale:raise SystemExit('stale native engine: '+'; '.join(stale))
  LOCK.write_text(json.dumps({'schema':'ThoughtexperimentEditOpsCrossFamilyCowV1Lock','sources':frozen(),
   'workers':WORKERS,'seed':SEED,'families':FAMILIES,'backends':BACKENDS,
   'candidate_count_per_family':4},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if len(args)==2 and args[0]=='--worker-order':print(json.dumps(order_worker(int(args[1])),sort_keys=True,separators=(',',':')));return 0
 if args==['--worker-score']:print(json.dumps(score_worker(json.load(sys.stdin)),sort_keys=True,separators=(',',':')));return 0
 if args==['--orders']:
  lock=json.loads(LOCK.read_text())
  if frozen()!=lock['sources'] or ORDERS.exists() or SCORES.exists():raise SystemExit('source drift or capture exists')
  env={**os.environ,'OZMA_NO_LLM':'1','OZMA_SEED_PERSIST_DISABLED':'1','PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}:{ROOT}/evaluation/substrate_capability'};rows=[]
  for i in range(WORKERS):
   p=subprocess.run([sys.executable,str(RUNNER),'--worker-order',str(i)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=300)
   if p.returncode:raise RuntimeError(f'order worker {i}: {p.stderr[-3000:]}')
   rows.append(json.loads(p.stdout.strip().splitlines()[-1]))
  if frozen()!=lock['sources']:raise SystemExit('source drift after order stage')
  ORDERS.write_text(json.dumps({'schema':'ThoughtexperimentEditOpsCrossFamilyCowV1Orders','lock_sha256':sha(LOCK),
   'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),'workers':rows},indent=2,sort_keys=True)+'\n');print(ORDERS.relative_to(ROOT));return 0
 if args==['--scores']:
  lock=json.loads(LOCK.read_text())
  if not ORDERS.exists() or SCORES.exists() or frozen()!=lock['sources']:raise SystemExit('orders missing, scores exist, or source drift')
  env={**os.environ,'OZMA_NO_LLM':'1','OZMA_SEED_PERSIST_DISABLED':'1','PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}:{ROOT}/evaluation/substrate_capability'};rows=[]
  for order in json.loads(ORDERS.read_text())['workers']:
   p=subprocess.run([sys.executable,str(RUNNER),'--worker-score'],input=json.dumps(order),cwd=ROOT,env=env,text=True,capture_output=True,timeout=300)
   if p.returncode:raise RuntimeError(f"score worker {order['worker']}: {p.stderr[-3000:]}")
   rows.append(json.loads(p.stdout.strip().splitlines()[-1]))
  if frozen()!=lock['sources']:raise SystemExit('source drift after scores')
  SCORES.write_text(json.dumps({'schema':'ThoughtexperimentEditOpsCrossFamilyCowV1Scores','lock_sha256':sha(LOCK),
   'orders_sha256':sha(ORDERS),'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'workers':rows},indent=2,sort_keys=True)+'\n');print(SCORES.relative_to(ROOT));return 0
 raise SystemExit('use --lock, --orders, --scores, --worker-order N, or --worker-score')
if __name__=='__main__':raise SystemExit(main())
