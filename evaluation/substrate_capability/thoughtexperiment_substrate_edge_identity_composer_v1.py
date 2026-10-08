#!/usr/bin/env python3
"""Source-locked residual-to-edge-guard composer evaluation."""
from __future__ import annotations
import copy,hashlib,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'evaluation/substrate_capability')]
RUNNER=Path(__file__).resolve()
PREREG=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_SUBSTRATE_EDGE_IDENTITY_COMPOSER_V1_PREREG_20261002.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_thoughtexperiment_substrate_edge_identity_composer_v1.py'
CORE=(ROOT/'domains/edit_ops.py',ROOT/'domains/reflective_faculty.py')
HELPER=ROOT/'evaluation/substrate_capability/thoughtexperiment_bidirectional_edge_identity_guards_v1_1.py'
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_substrate_edge_identity_composer_v1_lock_20261002.json'
ORDERS=ROOT/'evaluation/reports/thoughtexperiment_substrate_edge_identity_composer_v1_orders_20261002.json'
SCORES=ROOT/'evaluation/reports/thoughtexperiment_substrate_edge_identity_composer_v1_scores_20261002.json'
FAMILIES=('recurrence','conversation');WORKERS=4;REPEATS=2;SEED=20261029
CUES={'recurrence':['mrl','offer','due','once','edge','output','candidate'],
 'conversation':['reply','adjacency','message','response','responds_to','once','edge','output']}
AMBIGUOUS=['reply','adjacency','message','once','edge','output']
NO_OVERLAP=['unrelated']

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def frozen():
 import thoughtexperiment_bidirectional_edge_identity_guards_v1_1 as helper
 from substrate_rs import _native
 files=(*CORE,HELPER,helper.PREREG,helper.ANALYZER,RUNNER,PREREG,ANALYZER)
 out={str(p.relative_to(ROOT)):sha(p) for p in files}
 out.update({f'episode_helper::{k}':v for k,v in helper.frozen().items()})
 out['loaded_native_binary']=sha(Path(_native.__file__).resolve())
 return out
def digest(rule):
 row=copy.deepcopy(rule);row.pop('name',None);row.pop('active',None)
 return 'sha256:'+hashlib.sha256(json.dumps(row,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def context(family,worker,split,sample=0):
 import thoughtexperiment_bidirectional_edge_identity_guards_v1_1 as helper
 return helper.recurrence_context(worker,split,sample) if family=='recurrence' else helper.conversation_context()
def add_axis(sub,key,cues):
 sub.add_node('CapabilityAxis',{'is_axis':1.0,'capability_keys':[key],'induced':1.0,
  'residual_predicates':list(cues),'structural_rule_scope':'all_mutable_rules',
  'from_observation':1.0,'source':'substrate_edge_identity_composer_v1'})
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
 import thoughtexperiment_bidirectional_edge_identity_guards_v1_1 as helper
 before=frozen();rows={};worker_started=time.perf_counter_ns()
 for family in FAMILIES:
  ctx,result,candidate,compose_ns,primary_unchanged,source_digest=compose(family,worker,'proposal_order',CUES[family],f'order{worker}')
  train_started=time.perf_counter_ns()
  training=[helper.score_episode(family,worker,f'train_{worker}',i,candidate) for i in range(REPEATS)] if candidate else []
  train_ns=time.perf_counter_ns()-train_started
  source_started=time.perf_counter_ns()
  source=[helper.source_episode(family,worker,f'train_source_{worker}',i) for i in range(REPEATS)]
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
 import thoughtexperiment_bidirectional_edge_identity_guards_v1_1 as helper
 before=frozen();rows={};worker_started=time.perf_counter_ns()
 for family in FAMILIES:
  candidate=order['families'][family]['proposal']['candidate']
  started=time.perf_counter_ns()
  trials=[helper.score_episode(family,int(order['worker']),f'heldout_{order["worker"]}',i,candidate)
   for i in range(REPEATS)] if candidate else []
  score_ns=time.perf_counter_ns()-started
  source_started=time.perf_counter_ns()
  source=[helper.source_episode(family,int(order['worker']),f'heldout_source_{order["worker"]}',i)
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
  LOCK.write_text(json.dumps({'schema':'SubstrateEdgeIdentityComposerV1Lock','sources':frozen(),
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
  ORDERS.write_text(json.dumps({'schema':'SubstrateEdgeIdentityComposerV1Orders','lock_sha256':sha(LOCK),
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
  SCORES.write_text(json.dumps({'schema':'SubstrateEdgeIdentityComposerV1Scores','lock_sha256':sha(LOCK),
   'orders_sha256':sha(ORDERS),'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'workers':ws},
   indent=2,sort_keys=True)+'\n')
  print(SCORES.relative_to(ROOT));return 0
 raise SystemExit('use --lock, --orders, or --scores')
if __name__=='__main__':raise SystemExit(main())
