#!/usr/bin/env python3
"""Cross-family test of generic edge-identity guard generation and selection."""
from __future__ import annotations
import copy,hashlib,json,os,platform,random,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
RUNNER=Path(__file__).resolve()
PREREG=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_BIDIRECTIONAL_EDGE_IDENTITY_GUARDS_V1_PREREG_20261002.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_thoughtexperiment_bidirectional_edge_identity_guards_v1.py'
SOURCES=('domains/contract_query.py','domains/reflective_faculty.py','domains/engine_provenance.py',
 'substrate/world_adapter.py','substrate/boot_core.py','substrate/seed_loader.py',
 'domains/language_world.py','domains/reference_resolution.py',
 'runners/dsl/src/py.rs','runners/dsl/src/substrate.rs','runners/dsl/src/graph.rs',
 'runners/dsl/src/graph_rules.rs','runners/dsl/src/term.rs','runners/dsl/src/persist.rs',
 'runners/dsl/src/grammar.rs','runners/dsl/src/sym.rs','runners/dsl/src/lib.rs',
 'runners/dsl/Cargo.toml','runners/dsl/Cargo.lock','runners/dsl/python/substrate_rs/__init__.py',
 'seeds/minting_recurrence_ledger.json','seeds/relation_vocabulary.json','seeds/composer_dispatch.json',
 'seeds/autonomy.json','seeds/intent.json','seeds/conversation_reply.json','seeds/conversation.json',
 'seeds/faculty_lessons.json','seeds/psychology.json','seeds/relations.json')
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_bidirectional_edge_identity_guards_v1_lock_20261002.json'
ORDERS=ROOT/'evaluation/reports/thoughtexperiment_bidirectional_edge_identity_guards_v1_orders_20261002.json'
SCORES=ROOT/'evaluation/reports/thoughtexperiment_bidirectional_edge_identity_guards_v1_scores_20261002.json'
FAMILIES=('recurrence','conversation');WORKERS=4;REPEATS=2;SEED=20261023
TARGETS={'recurrence':'mrl_offer_due_once','conversation':'reply_to_adjacency_pair'}
CUES={'recurrence':['mrl','offer','due','once','guard','constrain','restrict','narrow','extra','condition','equality'],
 'conversation':['reply','adjacency','message','response','guard','condition','once']}
TRAIN_CONVERSATION=(('hello there','greeting'),('good morning','greeting'))
HELDOUT_CONVERSATION=(('what is it?','question'),('hello again','greeting'),('hi there','greeting'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def frozen():
 from substrate_rs import _native
 paths=[ROOT/p for p in SOURCES]+[RUNNER,PREREG,ANALYZER]
 out={str(p.relative_to(ROOT)):sha(p) for p in paths};out['loaded_native_binary']=sha(Path(_native.__file__).resolve());return out
def rule_digest(family,rule):
 row=copy.deepcopy(rule);row.pop('name',None)
 return 'sha256:'+hashlib.sha256(json.dumps({TARGETS[family]:row},sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def generic_edge_guard_hypotheses(rule):
 """For each emitted edge, add one guard at each match-bound endpoint."""
 bound=set()
 for edge in rule.get('match') or []:
  if isinstance(edge,list) and len(edge)>=3:
   if isinstance(edge[0],str):bound.add(edge[0])
   if isinstance(edge[2],str):bound.add(edge[2])
 sites=[]
 for effect in rule.get('effects') or []:
  if not (isinstance(effect,list) and len(effect)>=4 and effect[0]=='add_edge'):continue
  src,edge_type,tgt=effect[1],effect[2],effect[3]
  options=[]
  if src in bound:options.append(('out',src,tgt if tgt in bound else None))
  if tgt in bound:options.append(('in',tgt,src if src in bound else None))
  for direction,var,other in options:
   site=(direction,var,edge_type,other)
   if site not in sites:sites.append(site)
 out=[]
 for i,(direction,var,edge_type,other) in enumerate(sites):
  existing=f'existing_{direction}_{i}'
  if direction=='out':
   source={'type':'Neighbours','node':{'type':'Var','name':var},'edge_type':edge_type}
  else:
   source={'type':'InNeighbours','node':{'type':'Var','name':var},'edge_type':edge_type}
  predicate=({'type':'Eq','a':{'type':'Var','name':existing},'b':{'type':'Var','name':other}}
    if other is not None else {'type':'Lit','value':True})
  guard={'type':'Not','arg':{'type':'Exists','source':source,'var_name':existing,'predicate':predicate}}
  variant=copy.deepcopy(rule);variant['name']=f"{rule.get('name','rule')}_identity_guard_{i}";variant.pop('active',None)
  where=variant.get('where')
  if isinstance(where,dict) and where.get('type')=='And':where.setdefault('items',[]).append(guard)
  elif where:variant['where']={'type':'And','items':[where,guard]}
  else:variant['where']=guard
  scope=other or 'any_target'
  out.append({'label':f'edge_once:{direction}:{var}:{edge_type}:{scope}','rules':{rule['name']:variant}})
 if len(out)!=3:raise RuntimeError(f"expected three generic edge sites for {rule.get('name')}, got {sites!r}")
 return out,sites
def recurrence_context(worker,split,sample,*,fault=True):
 from substrate.boot_core import boot_core
 from substrate.seed_loader import manifest_for
 sub,agent=boot_core(seeds=());native=sub._inner
 for seed in ('relation_vocabulary','composer_dispatch','autonomy','minting_recurrence_ledger'):
  native.load_seed_manifest(manifest_for(seed),agent)
 target=TARGETS['recurrence'];rows=native.export_rules();active=[(i,r) for i,r in enumerate(rows) if r.get('name')==target and r.get('active',True)]
 if len(active)!=1:raise RuntimeError('recurrence target rule missing or duplicated')
 source=copy.deepcopy(active[0][1]);rule=copy.deepcopy(source)
 if fault:rule['where']['items']=[x for x in rule['where']['items'] if x.get('type')!='Not']
 if fault:
  if not native.remove_rule(active[0][0]):raise RuntimeError('recurrence fault replacement failed')
  native.add_rule(rule)
 episode=sub.add_node('MintingRecurrenceEpisode',{'mint_after_quanta':1,'integer_native':1,'generator':'bidirectional_edge_v1'})
 sub.add_edge(agent,'has_minting_recurrence_episode',episode)
 keys=[f'bidir-{worker}-{split}-{sample}-{j}' for j in range(2)]
 def add_due(j):
  key=keys[j];attrs={'predicate':'bind','recurrence_key':key,
   'structural_signature':[['relation','bind','ITEM',f'SLOT{j}',worker]],'capability_key':[key,'X']}
  cand=sub.add_node('PredicateRecurrenceCandidate',attrs)
  ev=sub.add_node('ResidualSegmentEvidence',{**attrs,'segment_ordinal':j,'integer_native':1})
  sub.add_edge(episode,'has_predicate_recurrence_candidate',cand);sub.add_edge(cand,'supported_by_segment',ev)
 add_due(0)
 return {'family':'recurrence','sub':sub,'native':native,'agent':agent,'target':target,'source_rule':source,
  'rule':rule,'episode':episode,'keys':keys,'add_due':add_due}
def conversation_context(*,fault=True):
 from substrate.world_adapter import WorldAdapter
 wa=WorldAdapter(seeds=(),shadow_read=False,deep_ingest=False);wa.enable_replies()
 target=TARGETS['conversation'];rows=wa.inner.export_rules();active=[(i,r) for i,r in enumerate(rows) if r.get('name')==target and r.get('active',True)]
 if len(active)!=1:raise RuntimeError('conversation target rule missing or duplicated')
 source=copy.deepcopy(active[0][1]);rule=copy.deepcopy(source)
 if fault:
  rule['where']['items']=[x for x in rule['where']['items'] if x.get('type')!='Not']
  if not wa.inner.remove_rule(active[0][0]):raise RuntimeError('conversation fault replacement failed')
  wa.inner.add_rule(rule)
 return {'family':'conversation','sub':wa.s,'native':wa.inner,'agent':wa.agent,'adapter':wa,
  'target':target,'source_rule':source,'rule':rule}
def build_pool(family,worker,split='train',sample=0):
 import domains.reflective_faculty as rf
 ctx=recurrence_context(worker,split,sample) if family=='recurrence' else conversation_context()
 generated,sites=generic_edge_guard_hypotheses(ctx['rule'])
 key=f'bidir_edge_{family}_{worker}_{split}_{sample}'
 ctx['sub'].add_node('CapabilityAxis',{'is_axis':1.0,'capability_keys':[key],'induced':1.0,
  'residual_predicates':CUES[family],'structural_rule_scope':'all_mutable_rules','from_observation':1.0,
  'source':'bidirectional_edge_identity_guards_v1'})
 started=time.perf_counter_ns();result=rf.compose_general_structural_variant(ctx['sub'],[key],key)
 compose_ns=time.perf_counter_ns()-started
 if not result.get('built') or result.get('removed_rule')!=ctx['target']:
  raise RuntimeError(f"composer failed to target {family}: {result}")
 composer={'label':f"composer:{result['kind']}",'rules':{ctx['target']:result['rule']}}
 candidates=generated+[composer]
 descriptors=[{'proposal_id':rule_digest(family,c['rules'][ctx['target']]),'label':c['label']} for c in candidates]
 if len(descriptors)!=4 or len({d['proposal_id'] for d in descriptors})!=4:raise RuntimeError(f'{family} candidate collision or count mismatch')
 return ctx,candidates,descriptors,sites,compose_ns,{'target':result.get('removed_rule'),'operator':result.get('kind'),'site':result.get('site')}
def install_variant(native,target,candidate):
 rows=native.export_rules();active=[(i,r) for i,r in enumerate(rows) if r.get('name')==target and r.get('active',True)]
 if len(active)!=1 or not native.remove_rule(active[0][0]):raise RuntimeError(f'failed to replace {target}')
 native.add_rule(candidate['rules'][target])
def score_episode(family,worker,split,sample,candidate):
 target=TARGETS[family]
 if family=='recurrence':
  ctx=recurrence_context(worker,split,sample,fault=candidate is not None);sub,native=ctx['sub'],ctx['native']
  if candidate is not None:install_variant(native,target,candidate)
  rules_before=native.export_rules()
  sweeps0=[int(native.run_rules(100)) for _ in range(5)]
  ctx['add_due'](1);sweeps1=[int(native.run_rules(100)) for _ in range(5)]
  counts=[]
  for key in ctx['keys']:
   node=next(n for n in sub.nodes('PredicateRecurrenceCandidate') if sub.node(n)['attrs'].get('recurrence_key')==key)
   counts.append(len(list(sub.neighbours(node,'has_mint_offer'))))
  fixed=int(native.run_rules(100));return {'correct':counts==[1,1] and fixed==0,'output_counts':counts,
   'fixedpoint_progress':fixed,'stage0_sweeps':sweeps0,'stage1_sweeps':sweeps1,'keys':ctx['keys'],
   'rule_store_stable':native.export_rules()==rules_before}
 ctx=conversation_context(fault=candidate is not None);wa=ctx['adapter'];native=ctx['native']
 if candidate is not None:install_variant(native,target,candidate)
 rules_before=native.export_rules();seq=TRAIN_CONVERSATION if split.startswith('train') else HELDOUT_CONVERSATION
 counts=[];ids=[];elapsed=0
 for i,(text,act) in enumerate(seq):
  t=time.perf_counter_ns();mid=wa.receive_utterance(text,speech_act=act,speaker='user',tick=i);wa.comprehend();elapsed+=time.perf_counter_ns()-t
  ids.append(str(mid));counts.append(sum(1 for reply in wa.agent_outbound_messages() if mid in wa.responds_to(reply)))
 return {'correct':counts==[1]*len(seq),'output_counts':counts,'expected_counts':[1]*len(seq),
  'input_ids':ids,'rule_store_stable':native.export_rules()==rules_before,'sequence_runtime_ns':elapsed}
def source_episode(family,worker,split,sample):return score_episode(family,worker,split,sample,None)
def selector_decision(sub,family,worker,descriptors,evidence,control=None):
 from domains.contract_query import select_candidate_from_graph_evidence
 branch=sub.snapshot().fork()
 proposals=[{'proposal_id':d['proposal_id'],'proposal_label':'hypothesis'} for d in descriptors]
 if control is None:return select_candidate_from_graph_evidence(branch,f'bidir_select_{family}_{worker}',proposals,evidence)
 val='incorrect' if control=='all_wrong' else 'correct'
 rows=[{'proposal_id':d['proposal_id'],'probe_id':f'{control}_{i}','predicted':val,'expected':'correct'}
  for d in descriptors for i in range(REPEATS)]
 return select_candidate_from_graph_evidence(branch,f'bidir_{control}_{family}_{worker}',proposals,rows)
def order_worker(worker):
 before=frozen();family_rows={}
 for family in FAMILIES:
  ctx,cands,desc,sites,compose_ns,composer=build_pool(family,worker)
  rng=random.Random(SEED+worker*100+FAMILIES.index(family));perm=list(range(4));rng.shuffle(perm)
  cands=[cands[i] for i in perm];desc=[desc[i] for i in perm]
  outcomes=[];evidence=[];keys=[];training_ns=0
  for c,d in zip(cands,desc):
   rows=[]
   for sample in range(REPEATS):
    start=time.perf_counter_ns();row=score_episode(family,worker,f'train_{worker}',sample,c);training_ns+=time.perf_counter_ns()-start
    rows.append({'sample':sample,**row});keys.extend(row.get('keys',[]))
    evidence.append({'proposal_id':d['proposal_id'],'probe_id':f'train_{worker}_{sample}',
     'predicted':'correct' if row['correct'] else 'incorrect','expected':'correct'})
   outcomes.append({'proposal_id':d['proposal_id'],'label':d['label'],'rows':rows})
  primary_rules=ctx['native'].export_rules();start=time.perf_counter_ns()
  decision=selector_decision(ctx['sub'],family,worker,desc,evidence);selector_ns=time.perf_counter_ns()-start
  decision.pop('proposal_node',None)
  controls={}
  for control in ('all_wrong','tie'):
   x=selector_decision(ctx['sub'],family,worker,desc,evidence,control);x.pop('proposal_node',None);controls[control]=x
  source_rows=[source_episode(family,worker,f'train_source_{worker}',sample) for sample in range(REPEATS)]
  family_rows[family]={'descriptors':desc,'selector_proposals':[{'proposal_id':d['proposal_id'],'proposal_label':'hypothesis'} for d in desc],
   'training_evidence':evidence,'training_outcomes':outcomes,'decision':decision,
   'selected_label':next((d['label'] for d in desc if d['proposal_id']==decision.get('proposal_id')),None),
   'controls':controls,'source_train':source_rows,'sites':sites,'composer':composer,
   'compose_ns':compose_ns,'training_scoring_ns':training_ns,'selector_ns':selector_ns,
   'training_keys':keys,'primary_rule_unchanged':ctx['native'].export_rules()==primary_rules,
   'branch_evidence_isolated':not ctx['sub'].nodes('CandidateProposal') and not ctx['sub'].nodes('CandidateEvidence'),
   'candidate_order':perm}
 after=frozen()
 return {'worker':worker,'families':family_rows,'source_before':before,'source_after':after,'source_stable':before==after}
def score_worker(order):
 before=frozen();rows={}
 for family in FAMILIES:
  ctx,cands,desc,sites,compose_ns,composer=build_pool(family,int(order['worker']),'heldout')
  perm=order['families'][family]['candidate_order'];cands=[cands[i] for i in perm];desc=[desc[i] for i in perm]
  if desc!=order['families'][family]['descriptors']:raise RuntimeError(f'{family}: candidate descriptor drift')
  outcomes=[]
  for c,d in zip(cands,desc):
   trials=[score_episode(family,int(order['worker']),f'heldout_{order["worker"]}',sample,c) for sample in range(REPEATS)]
   outcomes.append({'proposal_id':d['proposal_id'],'label':d['label'],'trials':trials})
  source=[source_episode(family,int(order['worker']),f'heldout_source_{order["worker"]}',sample) for sample in range(REPEATS)]
  rows[family]={'descriptors':desc,'candidate_outcomes':outcomes,'source_heldout':source}
 after=frozen()
 return {'worker':order['worker'],'families':rows,'source_before':before,'source_after':after,'source_stable':before==after}
def main():
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit('stale native engine: '+'; '.join(stale))
 env={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}'};args=sys.argv[1:]
 if args[:1]==['--order-worker']:
  print(json.dumps(order_worker(int(args[1])),sort_keys=True,separators=(',',':')));return 0
 if args[:1]==['--score-worker']:
  print(json.dumps(score_worker(json.load(sys.stdin)),sort_keys=True,separators=(',',':')));return 0
 if args==['--lock']:
  if any(p.exists() for p in (LOCK,ORDERS,SCORES)):raise SystemExit('refusing to overwrite')
  LOCK.write_text(json.dumps({'schema':'ThoughtexperimentBidirectionalEdgeIdentityGuardsV1Lock','sources':frozen(),
   'semantic_engine':rust_source_fingerprint(str(ROOT)),'families':FAMILIES,'workers':WORKERS,
   'repeats':REPEATS,'seed':SEED,'targets':TARGETS,'train_conversation':TRAIN_CONVERSATION,
   'heldout_conversation':HELDOUT_CONVERSATION,'candidate_count_per_family':4,
   'selection':'native graph Term from graph-resident training outcome evidence'},indent=2,sort_keys=True)+'\n')
  print(LOCK.relative_to(ROOT));return 0
 if args==['--orders']:
  if not LOCK.exists() or ORDERS.exists() or SCORES.exists():raise SystemExit('missing lock or captures exist')
  lock=json.loads(LOCK.read_text());before=frozen()
  if before!=lock['sources']:raise SystemExit('source drift from lock')
  ws=[]
  for i in range(WORKERS):
   p=subprocess.run([sys.executable,str(RUNNER),'--order-worker',str(i)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=180)
   if p.returncode:raise RuntimeError(f'order worker {i}: {p.stderr[-3000:]}')
   ws.append(json.loads(p.stdout.strip().splitlines()[-1]))
  if frozen()!=before:raise SystemExit('source drift during order capture')
  ORDERS.write_text(json.dumps({'schema':'ThoughtexperimentBidirectionalEdgeIdentityGuardsV1Orders','lock_sha256':sha(LOCK),
   'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),'workers':ws},indent=2,sort_keys=True)+'\n')
  print(ORDERS.relative_to(ROOT));return 0
 if args==['--scores']:
  if not ORDERS.exists() or SCORES.exists():raise SystemExit('orders missing or scores exist')
  lock=json.loads(LOCK.read_text());before=frozen()
  if before!=lock['sources']:raise SystemExit('source drift from lock')
  ws=[]
  for order in json.loads(ORDERS.read_text())['workers']:
   p=subprocess.run([sys.executable,str(RUNNER),'--score-worker'],input=json.dumps(order),cwd=ROOT,env=env,text=True,capture_output=True,timeout=180)
   if p.returncode:raise RuntimeError(f"score worker {order['worker']}: {p.stderr[-3000:]}")
   ws.append(json.loads(p.stdout.strip().splitlines()[-1]))
  if frozen()!=before:raise SystemExit('source drift during heldout capture')
  SCORES.write_text(json.dumps({'schema':'ThoughtexperimentBidirectionalEdgeIdentityGuardsV1Scores','lock_sha256':sha(LOCK),
   'orders_sha256':sha(ORDERS),'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'workers':ws},indent=2,sort_keys=True)+'\n')
  print(SCORES.relative_to(ROOT));return 0
 raise SystemExit('use --lock, --orders, or --scores')
if __name__=='__main__':raise SystemExit(main())
