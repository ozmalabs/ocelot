#!/usr/bin/env python3
"""Source-locked residual-to-edge-guard composer evaluation."""
from __future__ import annotations
import copy,hashlib,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'evaluation/substrate_capability')]
RUNNER=Path(__file__).resolve()
PREREG=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_SUBSTRATE_EDGE_ATTRIBUTE_IDENTITY_V1_PREREG_20261002.md'
AMENDMENT=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_SUBSTRATE_EDGE_ATTRIBUTE_IDENTITY_CURRENT_SOURCE_AMENDMENT_20261003.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_thoughtexperiment_substrate_edge_attribute_identity_v1.py'
CORE=(ROOT/'domains/edit_ops.py',ROOT/'domains/reflective_faculty.py',ROOT/'domains/seed_registry.py',ROOT/'seeds/actor_goals.json')
HELPER=ROOT/'evaluation/substrate_capability/thoughtexperiment_bidirectional_edge_identity_guards_v1_1.py'
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_substrate_edge_attribute_identity_current_source_v1_lock_20261003.json'
ORDERS=ROOT/'evaluation/reports/thoughtexperiment_substrate_edge_attribute_identity_current_source_v1_orders_20261003.json'
SCORES=ROOT/'evaluation/reports/thoughtexperiment_substrate_edge_attribute_identity_current_source_v1_scores_20261003.json'
FAMILIES=('recurrence','conversation','actor_recipient_edge','actor_recipient_identity');WORKERS=4;REPEATS=2;SEED=20261031
CUES={'recurrence':['mrl','offer','due','once','edge','output','candidate'],
 'conversation':['reply','adjacency','message','response','responds_to','once','edge','output'],
 'actor_recipient_edge':['mint','recipient','actor','goal','once','edge','output','any','endpoint'],
 'actor_recipient_identity':['mint','recipient','actor','verb','pair','identity']}
AMBIGUOUS=['reply','adjacency','message','once','edge','output']
NO_OVERLAP=['unrelated']

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def frozen():
 import thoughtexperiment_bidirectional_edge_identity_guards_v1_1 as helper
 from substrate_rs import _native
 files=(*CORE,HELPER,helper.PREREG,helper.ANALYZER,RUNNER,PREREG,AMENDMENT,ANALYZER)
 out={str(p.relative_to(ROOT)):sha(p) for p in files}
 out.update({f'episode_helper::{k}':v for k,v in helper.frozen().items()})
 out['loaded_native_binary']=sha(Path(_native.__file__).resolve())
 return out
def digest(rule):
 row=copy.deepcopy(rule);row.pop('name',None);row.pop('active',None)
 return 'sha256:'+hashlib.sha256(json.dumps(row,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def install_variant(native,target,candidate):
 rows=native.export_rules();active=[(i,r) for i,r in enumerate(rows) if r.get('name')==target and r.get('active',True)]
 if len(active)!=1 or not native.remove_rule(active[0][0]):raise RuntimeError(f'failed to replace {target}')
 native.add_rule(candidate['rules'][target])
def context(family,worker,split,sample=0):
 import thoughtexperiment_bidirectional_edge_identity_guards_v1_1 as helper
 if family=='recurrence':return helper.recurrence_context(worker,split,sample)
 if family=='conversation':return helper.conversation_context()
 return actor_context(fault=True)
def actor_context(*,fault=True):
 import domains.seed_registry
 from substrate.boot_core import boot_core
 sub,agent=boot_core(seeds=('actor_goals',));native=sub._inner;target='mint_actor_goal_recipient'
 rows=native.export_rules();active=[(i,r) for i,r in enumerate(rows) if r.get('name')==target and r.get('active',True)]
 if len(active)!=1:raise RuntimeError('actor-recipient target missing or duplicated')
 source=copy.deepcopy(active[0][1]);rule=copy.deepcopy(source)
 if fault:
  rule['where']['items']=[x for x in rule.get('where',{}).get('items',[]) if x.get('type')!='Not']
  if not native.remove_rule(active[0][0]):raise RuntimeError('actor-recipient fault replacement failed')
  native.add_rule(rule)
 return {'family':'actor_recipient','sub':sub,'native':native,'agent':agent,'target':target,'source_rule':source,'rule':rule}
def actor_episode(worker,split,sample,candidate):
 ctx=actor_context(fault=candidate is not None);sub,native,agent=ctx['sub'],ctx['native'],ctx['agent']
 if candidate is not None:install_variant(native,ctx['target'],candidate)
 rules_before=native.export_rules();verbs=['sing'] if split.startswith('train') else ['sing','dance']
 counts=[];sweeps=[];actor_id=f'actor-{worker}'
 for verb in verbs:
  action=sub.add_node('ActorAction',{'actor':actor_id,'actor_role':'agent','verb':verb,'object_domain':verb})
  recipient=sub.add_node('RecipientVerb',{'verb':verb})
  sub.add_edge(agent,'has_actor_action',action);sub.add_edge(agent,'has_recipient_verb',recipient)
  sweeps.append(int(native.run_rules(100)))
  counts.append(sum(1 for n in sub.nodes('ActorGoal') if sub.node(n)['attrs'].get('actor')==actor_id and sub.node(n)['attrs'].get('verb')==verb))
 fixed=int(native.run_rules(100))
 return {'correct':counts==[1]*len(verbs) and fixed==0,'output_counts':counts,'expected_counts':[1]*len(verbs),
  'verbs':verbs,'rule_store_stable':native.export_rules()==rules_before,'input_sweeps':sweeps,'fixedpoint_progress':fixed}
def score_episode(family,worker,split,sample,candidate):
 if family.startswith('actor_recipient'):return actor_episode(worker,split,sample,candidate)
 import thoughtexperiment_bidirectional_edge_identity_guards_v1_1 as helper
 return helper.score_episode(family,worker,split,sample,candidate)
def source_episode(family,worker,split,sample):
 if family.startswith('actor_recipient'):return actor_episode(worker,split,sample,None)
 import thoughtexperiment_bidirectional_edge_identity_guards_v1_1 as helper
 return helper.source_episode(family,worker,split,sample)
def add_axis(sub,key,cues):
 sub.add_node('CapabilityAxis',{'is_axis':1.0,'capability_keys':[key],'induced':1.0,
  'residual_predicates':list(cues),'structural_rule_scope':'all_mutable_rules',
  'from_observation':1.0,'source':'substrate_edge_attribute_identity_v1'})
def compose(family,worker,split,cues,tag):
 import domains.reflective_faculty as rf
 ctx=context(family,worker,split)
 primary_before=ctx['native'].export_rules()
 source_rule=next(r for r in primary_before if r.get('name')==ctx['target'] and r.get('active',True))
 add_axis(ctx['sub'],f'{tag}_{family}_{worker}',cues)
 started=time.perf_counter_ns()
 result=rf.compose_general_structural_variant(ctx['sub'],[f'{tag}_{family}_{worker}'],tag)
 elapsed=time.perf_counter_ns()-started
 rule=result.get('rule') if result.get('built') else None
 candidate={'label':'substrate_composer','rules':{ctx['target']:copy.deepcopy(rule)}} if rule else None
 return ctx,result,candidate,elapsed,ctx['native'].export_rules()==primary_before,digest(source_rule)
def order_worker(worker):
 before=frozen();rows={};worker_started=time.perf_counter_ns()
 for family in FAMILIES:
  ctx,result,candidate,compose_ns,primary_unchanged,source_digest=compose(family,worker,'proposal_order',CUES[family],f'order{worker}')
  train_started=time.perf_counter_ns()
  training=[score_episode(family,worker,f'train_{worker}',i,candidate) for i in range(REPEATS)] if candidate else []
  train_ns=time.perf_counter_ns()-train_started
  source_started=time.perf_counter_ns()
  source=[source_episode(family,worker,f'train_source_{worker}',i) for i in range(REPEATS)]
  source_ns=time.perf_counter_ns()-source_started
  rows[family]={'proposal':{'built':bool(candidate),'target':result.get('removed_rule'),
   'operator':result.get('kind'),'site':result.get('site'),'wall':result.get('wall'),
   'candidate':candidate,'digest':digest(candidate['rules'][ctx['target']]) if candidate else None,
   'source_rule_digest':source_digest,
   'compose_ns':compose_ns},'training':training,'source_training':source,
   'training_scoring_ns':train_ns,'source_control_ns':source_ns,
   'primary_rule_unchanged':primary_unchanged}
 # Scope and abstention controls use fresh contexts and are not scored as proposals.
 ctx,result,_,no_overlap_ns,_,_=compose('recurrence',worker,'no_overlap',NO_OVERLAP,f'nooverlap{worker}')
 no_overlap={'built':bool(result.get('built')),'wall':result.get('wall'),'kind':result.get('kind')}
 ctx,result,_,ambiguous_ns,_,_=compose('conversation',worker,'ambiguous',AMBIGUOUS,f'ambiguous{worker}')
 ambiguous={'built':bool(result.get('built')),'wall':result.get('wall'),'kind':result.get('kind')}
 after=frozen()
 return {'worker':worker,'families':rows,'controls':{'no_overlap':no_overlap,'no_overlap_ns':no_overlap_ns,
  'ambiguous_site':ambiguous,'ambiguous_site_ns':ambiguous_ns},'source_before':before,'source_after':after,
  'source_stable':before==after,'worker_stage_wall_ns':time.perf_counter_ns()-worker_started}
def score_worker(order):
 before=frozen();rows={};worker_started=time.perf_counter_ns()
 for family in FAMILIES:
  candidate=order['families'][family]['proposal']['candidate']
  started=time.perf_counter_ns()
  trials=[score_episode(family,int(order['worker']),f'heldout_{order["worker"]}',i,candidate)
   for i in range(REPEATS)] if candidate else []
  score_ns=time.perf_counter_ns()-started
  source_started=time.perf_counter_ns()
  source=[source_episode(family,int(order['worker']),f'heldout_source_{order["worker"]}',i)
   for i in range(REPEATS)]
  source_ns=time.perf_counter_ns()-source_started
  rows[family]={'heldout':trials,'heldout_scoring_ns':score_ns,'source_heldout':source,'source_control_ns':source_ns}
 after=frozen()
 return {'worker':order['worker'],'families':rows,'source_before':before,'source_after':after,
  'source_stable':before==after,'worker_stage_wall_ns':time.perf_counter_ns()-worker_started}
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
  LOCK.write_text(json.dumps({'schema':'SubstrateEdgeAttributeIdentityCurrentSourceV1Lock','sources':frozen(),
   'semantic_engine':rust_source_fingerprint(str(ROOT)),'families':FAMILIES,'workers':WORKERS,
   'repeats':REPEATS,'seed':SEED,'cues':CUES,'ambiguous_cue':AMBIGUOUS,'no_overlap_cue':NO_OVERLAP,
   'proposal_path':'compose_general_structural_variant; graph-resident EditOp and EditSite selection'},
   indent=2,sort_keys=True)+'\n')
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
  ORDERS.write_text(json.dumps({'schema':'SubstrateEdgeAttributeIdentityV1Orders','lock_sha256':sha(LOCK),
   'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),'workers':ws},
   indent=2,sort_keys=True)+'\n')
  print(ORDERS.relative_to(ROOT));return 0
 if args==['--scores']:
  if not ORDERS.exists() or SCORES.exists():raise SystemExit('orders missing or scores exist')
  before=frozen();ws=[]
  for order in json.loads(ORDERS.read_text())['workers']:
   p=subprocess.run([sys.executable,str(RUNNER),'--score-worker'],input=json.dumps(order),cwd=ROOT,env=env,text=True,capture_output=True,timeout=180)
   if p.returncode:raise RuntimeError(f"score worker {order['worker']}: {p.stderr[-3000:]}")
   ws.append(json.loads(p.stdout.strip().splitlines()[-1]))
  if frozen()!=before:raise SystemExit('source drift during held-out capture')
  SCORES.write_text(json.dumps({'schema':'SubstrateEdgeAttributeIdentityV1Scores','lock_sha256':sha(LOCK),
   'orders_sha256':sha(ORDERS),'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'workers':ws},
   indent=2,sort_keys=True)+'\n')
  print(SCORES.relative_to(ROOT));return 0
 raise SystemExit('use --lock, --orders, or --scores')
if __name__=='__main__':raise SystemExit(main())
