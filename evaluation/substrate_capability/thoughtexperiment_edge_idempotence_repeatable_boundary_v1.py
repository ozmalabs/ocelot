#!/usr/bin/env python3
"""Measure coarse edge-once guard suppression on a real repeatable rule."""
from __future__ import annotations
import copy,hashlib,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
RUNNER=Path(__file__).resolve()
PREREG=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_EDGE_IDEMPOTENCE_REPEATABLE_BOUNDARY_V1_PREREG_20261002.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_thoughtexperiment_edge_idempotence_repeatable_boundary_v1.py'
SOURCES=('substrate/world_adapter.py','substrate/boot_core.py','substrate/seed_loader.py','domains/reflective_faculty.py',
 'domains/contract_query.py','domains/engine_provenance.py','runners/dsl/src/py.rs','runners/dsl/src/substrate.rs',
 'runners/dsl/src/graph.rs','runners/dsl/src/graph_rules.rs','runners/dsl/src/term.rs','runners/dsl/src/persist.rs',
 'runners/dsl/src/grammar.rs','runners/dsl/src/sym.rs','runners/dsl/src/lib.rs','runners/dsl/Cargo.toml','runners/dsl/Cargo.lock',
 'runners/dsl/python/substrate_rs/__init__.py','domains/language_world.py','domains/reference_resolution.py',
 'seeds/intent.json','seeds/conversation_reply.json','seeds/conversation.json','seeds/faculty_lessons.json',
 'seeds/psychology.json','seeds/relations.json')
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_edge_idempotence_repeatable_boundary_v1_lock_20261002.json'
ORDERS=ROOT/'evaluation/reports/thoughtexperiment_edge_idempotence_repeatable_boundary_v1_orders_20261002.json'
SCORES=ROOT/'evaluation/reports/thoughtexperiment_edge_idempotence_repeatable_boundary_v1_scores_20261002.json'
WORKERS=4;TARGET='reply_to_adjacency_pair'
TRAIN=(("hello there","greeting"),("what is it?","question"))
HELDOUT=(("the sky is blue","statement"),("hello again","greeting"),("what now?","question"))
CUE=['reply','adjacency','message','response','guard','condition','once']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def frozen():
 from substrate_rs import _native
 files=[ROOT/p for p in SOURCES]+[RUNNER,PREREG,ANALYZER]
 out={str(p.relative_to(ROOT)):sha(p) for p in files};out['loaded_native_binary']=sha(Path(_native.__file__).resolve());return out
def digest(rule):
 row=copy.deepcopy(rule);row.pop('name',None)
 return 'sha256:'+hashlib.sha256(json.dumps({TARGET:row},sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def open_world():
 from substrate.world_adapter import WorldAdapter
 wa=WorldAdapter(seeds=(),shadow_read=False,deep_ingest=False);wa.enable_replies()
 return wa
def target_rule(wa):
 rows=wa.inner.export_rules();hits=[(i,r) for i,r in enumerate(rows) if r.get('name')==TARGET and r.get('active',True)]
 if len(hits)!=1:raise RuntimeError(f'expected one active target rule, got {len(hits)}')
 return hits[0]
def fault_rule(rule):
 out=copy.deepcopy(rule);where=out.get('where')
 if not isinstance(where,dict) or where.get('type')!='And':raise RuntimeError('unexpected target where shape')
 before=len(where.get('items') or []);where['items']=[x for x in where.get('items') or [] if x.get('type')!='Not']
 if len(where['items'])!=before-1:raise RuntimeError('expected exactly one negative guard')
 return out
def edge_once_candidate(rule):
 bound=set()
 for edge in rule.get('match') or []:
  if isinstance(edge,list) and len(edge)>=3:
   if isinstance(edge[0],str):bound.add(edge[0])
   if isinstance(edge[2],str):bound.add(edge[2])
 sites=[]
 for effect in rule.get('effects') or []:
  if isinstance(effect,list) and len(effect)>=4 and effect[0]=='add_edge' and effect[1] in bound:
   site=(effect[1],effect[2],effect[3] if effect[3] in bound else None)
   if site not in sites:sites.append(site)
 if len(sites)!=1:raise RuntimeError(f'expected single bound-source site, got {sites!r}')
 var,edge_type,target_var=sites[0]
 predicate=({'type':'Eq','a':{'type':'Var','name':'existing_edge_target'},
   'b':{'type':'Var','name':target_var}} if target_var else {'type':'Lit','value':True})
 guard={'type':'Not','arg':{'type':'Exists','source':{'type':'Neighbours',
  'node':{'type':'Var','name':var},'edge_type':edge_type},'var_name':f'existing_{var}',
  'predicate':predicate}}
 out=copy.deepcopy(rule);out['name']=f'{TARGET}_edge_once_0';out.pop('active',None)
 if out['where'].get('type')=='And':out['where']['items'].append(guard)
 else:out['where']={'type':'And','items':[out['where'],guard]}
 scope=target_var or 'any_target'
 return {'label':f'edge_once:{var}:{edge_type}:{scope}','rules':{TARGET:out}},sites
def composer_candidate(wa,key):
 import domains.reflective_faculty as rf
 wa.s.add_node('CapabilityAxis',{'is_axis':1.0,'capability_keys':[key],'induced':1.0,
  'residual_predicates':CUE,'structural_rule_scope':'all_mutable_rules','from_observation':1.0,
  'source':'repeatable_edge_boundary_v1'})
 result=rf.compose_general_structural_variant(wa.s,[key],key)
 if not result.get('built') or result.get('removed_rule')!=TARGET:raise RuntimeError(f'composer failed to target rule: {result}')
 return {'label':f"composer:{result['kind']}",'rules':{TARGET:result['rule']}},result
def install(wa,candidate):
 idx,source=target_rule(wa)
 if not wa.inner.remove_rule(idx):raise RuntimeError('target removal failed')
 wa.inner.add_rule(candidate['rules'][TARGET])
 return source
def run_sequence(candidate,sequence):
 wa=open_world();idx,source=target_rule(wa)
 if candidate is not None:
  fault=fault_rule(source);wa.inner.remove_rule(idx);wa.inner.add_rule(fault);install(wa,candidate)
 rules_before=wa.inner.export_rules();counts=[];ids=[];runtime=0
 for i,(text,act) in enumerate(sequence):
  start=time.perf_counter_ns();mid=wa.receive_utterance(text,speech_act=act,speaker='user',tick=i);wa.comprehend();runtime+=time.perf_counter_ns()-start
  ids.append(str(mid));counts.append(sum(1 for reply in wa.agent_outbound_messages() if mid in wa.responds_to(reply)))
 after_rules=wa.inner.export_rules()
 return {'reply_counts_by_input':counts,'expected_counts':[1]*len(sequence),'correct':counts==[1]*len(sequence),
  'agent_outbound_count':len(wa.agent_outbound_messages()),'input_count':len(sequence),
  'input_ids':ids,'rules_unchanged_during_sequence':rules_before==after_rules,'sequence_runtime_ns':runtime,
  'rule_store_stable_during_sequence':rules_before==after_rules}
def worker_order(worker):
 from domains.contract_query import select_candidate_from_graph_evidence
 before=frozen();wa=open_world();idx,source=target_rule(wa);fault=fault_rule(source)
 wa.inner.remove_rule(idx);wa.inner.add_rule(fault)
 generic,sites=edge_once_candidate(fault);compose,compose_result=composer_candidate(wa,f'repeatable_reply_{worker}')
 candidates=[generic,compose];descriptors=[{'proposal_id':digest(c['rules'][TARGET]),'label':c['label']} for c in candidates]
 if len({d['proposal_id'] for d in descriptors})!=2:raise RuntimeError('candidate digest collision')
 primary_rules=wa.inner.export_rules();outcomes=[];evidence=[];scoring_ns=0
 for c,d in zip(candidates,descriptors):
  row=run_sequence(c,TRAIN);scoring_ns+=row['sequence_runtime_ns']
  outcomes.append({'proposal_id':d['proposal_id'],'label':d['label'],'outcome':row})
  evidence.append({'proposal_id':d['proposal_id'],'probe_id':f'train_reply_{worker}',
   'predicted':'correct' if row['correct'] else 'incorrect','expected':'correct'})
 # Source positive control is measured on the same two-message training task.
 baseline_train=run_sequence(None,TRAIN)
 branch=wa.s.snapshot().fork();start=time.perf_counter_ns()
 decision=select_candidate_from_graph_evidence(branch,f'repeatable_boundary_{worker}',
  [{'proposal_id':d['proposal_id'],'proposal_label':'hypothesis'} for d in descriptors],evidence)
 selector_ns=time.perf_counter_ns()-start;decision.pop('proposal_node',None)
 after=frozen()
 return {'worker':worker,'descriptors':descriptors,'selector_proposals':[{'proposal_id':d['proposal_id'],'proposal_label':'hypothesis'} for d in descriptors],
  'training_evidence':evidence,'candidate_outcomes':outcomes,'baseline_train':baseline_train,
  'decision':decision,'selected_label':next((d['label'] for d in descriptors if d['proposal_id']==decision.get('proposal_id')),None),
  'generic_site':sites,'composer':{k:compose_result.get(k) for k in ('removed_rule','kind','site')},
  'training_scoring_ns':scoring_ns,'selector_ns':selector_ns,
  'primary_rule_preserved':wa.inner.export_rules()==primary_rules,
  'branch_evidence_isolated':not wa.s.nodes('CandidateProposal') and not wa.s.nodes('CandidateEvidence'),
  'source_before':before,'source_after':after,'source_stable':before==after}
def worker_score(order):
 before=frozen();worker=int(order['worker']);wa=open_world();idx,source=target_rule(wa);fault=fault_rule(source)
 if not wa.inner.remove_rule(idx):raise RuntimeError('target fault replacement failed')
 wa.inner.add_rule(fault)
 generic,sites=edge_once_candidate(fault);compose,_=composer_candidate(wa,f'heldout_composer_{worker}')
 options=[generic,compose];ds=[{'proposal_id':digest(c['rules'][TARGET]),'label':c['label']} for c in options]
 if ds!=order['descriptors']:raise RuntimeError('heldout candidate descriptor mismatch')
 # The selector should abstain. This diagnostic scores the rejected coarse guard only;
 # it is never adopted or passed to the selector.
 diag=run_sequence(generic,HELDOUT);baseline=run_sequence(None,HELDOUT);after=frozen()
 return {'worker':worker,'descriptors':ds,'generic_heldout_diagnostic':diag,'baseline_heldout':baseline,
  'source_before':before,'source_after':after,'source_stable':before==after}
def main():
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit('stale native engine: '+'; '.join(stale))
 env={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}'};args=sys.argv[1:]
 if args[:1]==['--order-worker']:
  print(json.dumps(worker_order(int(args[1])),sort_keys=True,separators=(',',':')));return 0
 if args[:1]==['--score-worker']:
  print(json.dumps(worker_score(json.load(sys.stdin)),sort_keys=True,separators=(',',':')));return 0
 if args==['--lock']:
  if any(p.exists() for p in (LOCK,ORDERS,SCORES)):raise SystemExit('refusing to overwrite')
  LOCK.write_text(json.dumps({'schema':'ThoughtexperimentRepeatableEdgeBoundaryV1Lock','sources':frozen(),
   'semantic_engine':rust_source_fingerprint(str(ROOT)),'workers':WORKERS,'target':TARGET,
   'train_input_count':len(TRAIN),'heldout_input_count':len(HELDOUT),
   'candidate_count':2,'expected_train_decision':'abstain','expected_generic_site':'agent.sent'},indent=2,sort_keys=True)+'\n')
  print(LOCK.relative_to(ROOT));return 0
 if args==['--orders']:
  if not LOCK.exists() or ORDERS.exists() or SCORES.exists():raise SystemExit('missing lock or captures exist')
  lock=json.loads(LOCK.read_text());before=frozen()
  if before!=lock['sources']:raise SystemExit('source drift from lock')
  ws=[]
  for i in range(WORKERS):
   p=subprocess.run([sys.executable,str(RUNNER),'--order-worker',str(i)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=120)
   if p.returncode:raise RuntimeError(f'order worker {i}: {p.stderr[-3000:]}')
   ws.append(json.loads(p.stdout.strip().splitlines()[-1]))
  if frozen()!=before:raise SystemExit('source drift during orders')
  ORDERS.write_text(json.dumps({'schema':'ThoughtexperimentRepeatableEdgeBoundaryV1Orders','lock_sha256':sha(LOCK),
   'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),'workers':ws},indent=2,sort_keys=True)+'\n')
  print(ORDERS.relative_to(ROOT));return 0
 if args==['--scores']:
  if not ORDERS.exists() or SCORES.exists():raise SystemExit('orders missing or scores exist')
  lock=json.loads(LOCK.read_text());before=frozen()
  if before!=lock['sources']:raise SystemExit('source drift from lock')
  ws=[]
  for order in json.loads(ORDERS.read_text())['workers']:
   p=subprocess.run([sys.executable,str(RUNNER),'--score-worker'],input=json.dumps(order),cwd=ROOT,env=env,text=True,capture_output=True,timeout=120)
   if p.returncode:raise RuntimeError(f"score worker {order['worker']}: {p.stderr[-3000:]}")
   ws.append(json.loads(p.stdout.strip().splitlines()[-1]))
  if frozen()!=before:raise SystemExit('source drift during heldout')
  SCORES.write_text(json.dumps({'schema':'ThoughtexperimentRepeatableEdgeBoundaryV1Scores','lock_sha256':sha(LOCK),
   'orders_sha256':sha(ORDERS),'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'workers':ws},indent=2,sort_keys=True)+'\n')
  print(SCORES.relative_to(ROOT));return 0
 raise SystemExit('use --lock, --orders, or --scores')
if __name__=='__main__':raise SystemExit(main())
