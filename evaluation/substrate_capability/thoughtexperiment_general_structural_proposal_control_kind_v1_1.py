#!/usr/bin/env python3
"""Locked two-stage proposal-generation probe on a non-action classifier."""
from __future__ import annotations
import copy,hashlib,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'evaluation/substrate_capability')]
RUNNER=Path(__file__).resolve()
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_thoughtexperiment_general_structural_proposal_control_kind_v1_1.py'
ADAPTER=ROOT/'evaluation/substrate_capability/thoughtexperiment_blinded_panel_adapters_v1.py'
TASK=ROOT/'evaluation/substrate_capability/thoughtexperiment_control_kind_classification_repair_v1.py'
PREREG=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_GENERAL_STRUCTURAL_PROPOSAL_CONTROL_KIND_V1_PREREG_20261002.md'
AMENDMENT=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_GENERAL_STRUCTURAL_PROPOSAL_CONTROL_KIND_V1_1_AMENDMENT_20261002.md'
EVIDENCE=(ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_CONTROL_KIND_CLASSIFICATION_REPAIR_V1_PREREG_20261002.md',
 ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_CONTROL_KIND_CLASSIFICATION_REPAIR_V1_RESULTS_20261002.md',
 ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_BLINDED_PROPOSAL_UTILITY_V1_2_RESULTS_20261002.md',
 ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_PROPOSAL_GENERATION_BOUNDARY_AUDIT_20261002.md',
 ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_GENERAL_STRUCTURAL_PROPOSAL_CONTROL_KIND_V1_RESULTS_20261002.md')
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_general_structural_proposal_control_kind_v1_1_lock_20261002.json'
ORDERS=ROOT/'evaluation/reports/thoughtexperiment_general_structural_proposal_control_kind_v1_1_orders_20261002.json'
SCORES=ROOT/'evaluation/reports/thoughtexperiment_general_structural_proposal_control_kind_v1_1_scores_20261002.json'
WORKERS=4;TARGET='classify_kind_family'
PROMPT=['classify','kind','family','flip','comparison']
SOURCES=('domains/reflective_faculty.py','domains/edit_ops.py','domains/self_correction.py',
 'domains/engine_provenance.py','substrate/boot_core.py','substrate/seed_loader.py',
 'runners/dsl/src/py.rs','runners/dsl/src/substrate.rs','runners/dsl/src/graph.rs',
 'runners/dsl/src/graph_rules.rs','runners/dsl/src/term.rs','runners/dsl/src/persist.rs',
 'runners/dsl/src/grammar.rs','runners/dsl/src/sym.rs','runners/dsl/src/lib.rs',
 'runners/dsl/Cargo.toml','runners/dsl/Cargo.lock','runners/dsl/python/substrate_rs/__init__.py',
 'seeds/control_kinds.json','seeds/relation_vocabulary.json')

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def frozen():
 from substrate_rs import _native
 files=(*[ROOT/x for x in SOURCES],ADAPTER,TASK,RUNNER,ANALYZER,PREREG,AMENDMENT,*EVIDENCE)
 out={str(p.relative_to(ROOT)):sha(p) for p in files};out['loaded_native_binary']=sha(Path(_native.__file__).resolve());return out

def semantic_digest(candidate):
 rules={}
 for name,row in sorted((candidate.get('rules') or {}).items()):
  value=copy.deepcopy(row)
  if isinstance(value,dict):
   for key in ('name','content_hash','revision','rule_uid'):value.pop(key,None)
  rules[name]=value
 return 'sha256:'+hashlib.sha256(json.dumps(rules,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()

class Agent:
 def __init__(self,ctx):self.s=ctx['sub'];self.inner=ctx['native'];self.agent=ctx['root']

def _compose(worker,cue):
 import domains.reflective_faculty as rf
 from substrate.seed_loader import manifest_for
 import thoughtexperiment_blinded_panel_adapters_v1 as adapters
 ctx=adapters.prepare('control_kind',worker,'train');sub=ctx['sub'];native=ctx['native'];target=ctx['target']
 native.load_seed_manifest(manifest_for('relation_vocabulary'),ctx['root'])
 key=f'general_structural_control_kind_{worker}_'+('prompted' if cue else 'unprompted')
 residual=(['test','send','judge','structure','gradient']+PROMPT if cue else [])
 sub.add_node('CapabilityAxis',{'is_axis':1.0,'capability_keys':[key],'induced':1.0,
  'residual_predicates':residual,'structural_rule_scope':'all_mutable_rules',
  'from_observation':1.0,'source':'general_structural_proposal_control_kind_v1_1'})
 before=next(copy.deepcopy(r) for r in native.export_rules() if r.get('name')==target and r.get('active',True))
 start=time.perf_counter_ns();result=rf.ground_concern(Agent(ctx),[key])
 decision_ns=time.perf_counter_ns()-start
 structural=result.get('structural_variant') or {}
 after=next(copy.deepcopy(r) for r in native.export_rules() if r.get('name')==target and r.get('active',True))
 candidate={'label':'graph_'+str(structural.get('kind')),'rules':{target:copy.deepcopy(structural['rule'])}} if structural.get('built') else None
 reference=[copy.deepcopy(c) for c in ctx['candidates']]
 desc=[{'label':c['label'],'digest':adapters.digest(c),'targets':sorted((c.get('rules') or {}).keys())} for c in reference]
 host_match=next((d for d in desc if candidate and d['digest']==adapters.digest(candidate)),None)
 return {'worker':worker,'source_target':before,'host_reference_candidates':reference,
  'host_reference_descriptors':desc,'host_enumeration_ns':ctx['enumeration_ns'],
  'task_context_setup_ns':ctx['training_context_ns'],'cue':residual,'grounded':bool(structural.get('built')),
  'dispatch_path':result.get('path'),'dispatch_served_by':result.get('served_by'),
  'target':structural.get('removed_rule'),'operator':structural.get('kind'),'site':structural.get('site'),
  'wall':structural.get('wall'),'candidate':candidate,'candidate_semantic_digest':semantic_digest(candidate) if candidate else None,
  'candidate_host_reference_match':host_match,'target_preserved':before==after,
  'graph_decision_ns':decision_ns,'graph_revision':list(native.experiment_graph_rule_revision()),
  'applicability_extraction_ns':None,'materialization_in_composer':True}

def _order_worker(worker):
 before=frozen();prompted=_compose(worker,True);no_cue=_compose(worker,False);after=frozen()
 if before!=after:raise RuntimeError('source drift during proposal capture')
 return {'worker':worker,'source_before':before,'source_after':after,'source_stable':before==after,
  'prompted':prompted,'unprompted':no_cue}

def _score_worker(order):
 import thoughtexperiment_blinded_panel_adapters_v1 as adapters
 import thoughtexperiment_control_kind_classification_repair_v1 as task
 before=frozen();worker=int(order['worker']);ctx=adapters.prepare('control_kind',worker,'heldout')
 outcomes=[adapters.score(ctx,c) for c in order['prompted']['host_reference_candidates']]
 candidate=order['prompted']['candidate'];proposal=adapters.score(ctx,candidate) if candidate else None
 s,root,n,source,fault,_=task.rule_setup(None)
 controls={}
 for name,rule in (('source',source),('fault',fault)):
  controls[name]=adapters.score(ctx,{'label':name+'_control','rules':{TARGET:copy.deepcopy(rule)}})
 after=frozen()
 if before!=after:raise RuntimeError('source drift during held-out scoring')
 return {'worker':worker,'source_before':before,'source_after':after,'source_stable':before==after,
  'host_candidate_outcomes':outcomes,'proposal_outcome':proposal,'source_control':controls['source'],'fault_control':controls['fault']}

def main():
 if sys.argv[1:2]==['--order-worker']:
  print(json.dumps(_order_worker(int(sys.argv[2])),sort_keys=True,separators=(',',':')));return 0
 if sys.argv[1:2]==['--score-worker']:
  print(json.dumps(_score_worker(json.load(sys.stdin)),sort_keys=True,separators=(',',':')));return 0
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit('stale native engine: '+'; '.join(stale))
 env={**os.environ,'PYTHONPATH':f'{ROOT / "runners/dsl/python"}:{ROOT}:{ROOT / "evaluation/substrate_capability"}'}
 if sys.argv[1:]==['--lock']:
  if any(p.exists() for p in (LOCK,ORDERS,SCORES)):raise SystemExit('refusing to overwrite capture')
  LOCK.write_text(json.dumps({'schema':'GeneralStructuralProposalControlKindV1_1Lock','sources':frozen(),
   'semantic_engine':rust_source_fingerprint(str(ROOT)),'workers':WORKERS,'target':TARGET,'prompt':PROMPT,
   'unprompted_residual':[],'heldout':'control-kind fixture held-out names'},indent=2,sort_keys=True)+'\n')
  print(LOCK.relative_to(ROOT));return 0
 if not LOCK.exists():raise SystemExit('missing source lock')
 lock=json.loads(LOCK.read_text());before=frozen()
 if before!=lock['sources']:raise SystemExit('source drift from lock')
 if sys.argv[1:]==['--orders']:
  if ORDERS.exists() or SCORES.exists():raise SystemExit('capture already exists')
  workers=[]
  for i in range(WORKERS):
   p=subprocess.run([sys.executable,str(RUNNER),'--order-worker',str(i)],cwd=ROOT,env=env,text=True,capture_output=True)
   if p.returncode:raise RuntimeError(f'order worker {i}: {p.stderr[-3000:]}')
   workers.append(json.loads(p.stdout.strip().splitlines()[-1]))
  if before!=frozen():raise SystemExit('source drift during order stage')
  ORDERS.write_text(json.dumps({'schema':'GeneralStructuralProposalControlKindV1_1Orders','lock_sha256':sha(LOCK),
   'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':{'platform':platform.platform(),
   'machine':platform.machine(),'python':sys.version.split()[0]},'workers':workers},indent=2,sort_keys=True)+'\n')
  print(json.dumps({'stage':'orders_frozen','workers':len(workers),'path':ORDERS.relative_to(ROOT).as_posix()}));return 0
 if sys.argv[1:]==['--score']:
  if not ORDERS.exists() or SCORES.exists():raise SystemExit('missing orders or score already exists')
  doc=json.loads(ORDERS.read_text());workers=[]
  for row in doc['workers']:
   p=subprocess.run([sys.executable,str(RUNNER),'--score-worker'],input=json.dumps(row),cwd=ROOT,env=env,text=True,capture_output=True)
   if p.returncode:raise RuntimeError(f"score worker {row['worker']}: {p.stderr[-3000:]}")
   workers.append(json.loads(p.stdout.strip().splitlines()[-1]))
  if before!=frozen():raise SystemExit('source drift during score stage')
  SCORES.write_text(json.dumps({'schema':'GeneralStructuralProposalControlKindV1_1Scores','orders_sha256':sha(ORDERS),
   'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'workers':workers},indent=2,sort_keys=True)+'\n')
  print(json.dumps({'stage':'scored_after_order_freeze','workers':len(workers),'path':SCORES.relative_to(ROOT).as_posix()}));return 0
 raise SystemExit('choose --lock, --orders, or --score')
if __name__=='__main__':raise SystemExit(main())
