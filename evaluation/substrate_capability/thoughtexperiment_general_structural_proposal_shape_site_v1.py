#!/usr/bin/env python3
"""Locked diagnostic of cue-conditioned ordered EditSite selection."""
from __future__ import annotations
import copy,hashlib,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'evaluation/substrate_capability')]
RUNNER=Path(__file__).resolve()
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_thoughtexperiment_general_structural_proposal_shape_site_v1.py'
ADAPTER=ROOT/'evaluation/substrate_capability/thoughtexperiment_blinded_panel_adapters_v1.py'
TASK=ROOT/'evaluation/substrate_capability/thoughtexperiment_shape_axis_full_candidate_admission_v1.py'
PREREG=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_GENERAL_STRUCTURAL_PROPOSAL_SHAPE_SITE_V1_PREREG_20261002.md'
AMENDMENT=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_GENERAL_STRUCTURAL_PROPOSAL_SHAPE_SITE_V1_AMENDMENT_20261002.md'
EVIDENCE=(ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_SHAPE_AXIS_FULL_CANDIDATE_ADMISSION_V1_PREREG_20261002.md',
 ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_SHAPE_AXIS_FULL_CANDIDATE_ADMISSION_V1_RESULTS_20261002.md',
 ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_GENERAL_STRUCTURAL_PROPOSAL_CONTROL_KIND_V1_2_RESULTS_20261002.md',
 ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_PROPOSAL_GENERATION_BOUNDARY_AUDIT_20261002.md')
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_general_structural_proposal_shape_site_v1_lock_20261002.json'
ORDERS=ROOT/'evaluation/reports/thoughtexperiment_general_structural_proposal_shape_site_v1_orders_20261002.json'
SCORES=ROOT/'evaluation/reports/thoughtexperiment_general_structural_proposal_shape_site_v1_scores_20261002.json'
WORKERS=4;TARGET='sd_mint_quantum'
CONDITIONS={'key_to_signature':['shape','axis','quantum','mint','swap','leaf','attribute','key to signature'],
 'signature_to_key':['shape','axis','quantum','mint','swap','leaf','attribute','signature to key'],
 'ambiguous':['shape','axis','quantum','mint','swap','leaf','attribute','key','signature']}
SOURCES=('domains/reflective_faculty.py','domains/edit_ops.py','domains/self_correction.py',
 'domains/engine_provenance.py','substrate/boot_core.py','substrate/seed_loader.py',
 'runners/dsl/src/py.rs','runners/dsl/src/substrate.rs','runners/dsl/src/graph.rs',
 'runners/dsl/src/graph_rules.rs','runners/dsl/src/term.rs','runners/dsl/src/persist.rs',
 'runners/dsl/src/grammar.rs','runners/dsl/src/sym.rs','runners/dsl/src/lib.rs',
 'runners/dsl/Cargo.toml','runners/dsl/Cargo.lock','runners/dsl/python/substrate_rs/__init__.py',
 'seeds/relation_vocabulary.json','seeds/composer_dispatch.json','seeds/autonomy.json','seeds/shape_decode_loop.json')

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def frozen():
 from substrate_rs import _native
 files=(*[ROOT/p for p in SOURCES],ADAPTER,TASK,RUNNER,ANALYZER,PREREG,AMENDMENT,*EVIDENCE)
 out={str(p.relative_to(ROOT)):sha(p) for p in files};out['loaded_native_binary']=sha(Path(_native.__file__).resolve());return out
def sem_digest(candidate):
 rules={}
 for target,rule in sorted((candidate.get('rules') or {}).items()):
  row=copy.deepcopy(rule)
  if isinstance(row,dict):
   for k in ('name','content_hash','revision','rule_uid'):row.pop(k,None)
  rules[target]=row
 return 'sha256:'+hashlib.sha256(json.dumps(rules,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def target_rule(native):
 return next((copy.deepcopy(r) for r in native.export_rules() if r.get('name')==TARGET and r.get('active',True)),None)

def order_worker(worker):
 import domains.reflective_faculty as rf
 import thoughtexperiment_blinded_panel_adapters_v1 as adapters
 before=frozen();ctx=adapters.prepare('shape_axis',worker,'train');sub=ctx['sub'];native=ctx['native'];candidates=copy.deepcopy(ctx['candidates'])
 desc=[{'label':c['label'],'digest':adapters.digest(c),'semantic_digest':sem_digest(c)} for c in candidates]
 agent=ctx['agent'];target_before=target_rule(native);proposals={}
 for condition,predicates in CONDITIONS.items():
  key=f'shape_site_{worker}_{condition}'
  sub.add_node('CapabilityAxis',{'is_axis':1.0,'capability_keys':[key],'induced':1.0,
   'residual_predicates':list(predicates),'structural_rule_scope':'all_mutable_rules',
   'from_observation':1.0,'source':'thoughtexperiment_general_structural_proposal_shape_site_v1'})
  started=time.perf_counter_ns();result=rf.compose_general_structural_variant(agent,[key],f'w{worker}_{condition}')
  elapsed=time.perf_counter_ns()-started
  rule=result.get('rule') if result.get('built') else None
  proposal={'label':'graph_'+condition,'rules':{TARGET:copy.deepcopy(rule)}} if rule else None
  ref=next((d for d,c in zip(desc,candidates) if proposal and adapters.digest(c)==adapters.digest(proposal)),None)
  proposals[condition]={'built':bool(rule),'target':result.get('removed_rule'),'operator':result.get('kind'),
   'site':result.get('site'),'wall':result.get('wall'),'candidate':proposal,
   'digest':adapters.digest(proposal) if proposal else None,
   'semantic_digest':sem_digest(proposal) if proposal else None,'host_reference_match':ref,
   'composer_ns':elapsed}
 after=frozen()
 if before!=after:raise RuntimeError('source drift during site-order capture')
 if target_rule(native)!=target_before:raise RuntimeError('composition changed primary target rule')
 return {'worker':worker,'source_before':before,'source_after':after,'source_stable':before==after,
  'target_before':target_before,'target_after':target_rule(native),'host_candidates':candidates,
  'host_descriptors':desc,'host_enumeration_ns':ctx['enumeration_ns'],
  'task_context_setup_ns':ctx['training_context_ns'],'proposals':proposals}

def score_worker(order):
 import thoughtexperiment_blinded_panel_adapters_v1 as adapters
 before=frozen();worker=int(order['worker']);ctx=adapters.prepare('shape_axis',worker,'heldout')
 actual=[{'label':c['label'],'digest':adapters.digest(c),'semantic_digest':sem_digest(c)} for c in ctx['candidates']]
 if actual!=order['host_descriptors']:raise RuntimeError('held-out host candidate descriptors differ')
 host=[adapters.score(ctx,c) for c in order['host_candidates']]
 proposal_outcomes={name:(adapters.score(ctx,p['candidate']) if p['candidate'] else None)
  for name,p in order['proposals'].items()}
 after=frozen()
 if before!=after:raise RuntimeError('source drift during site scoring')
 return {'worker':worker,'source_before':before,'source_after':after,'source_stable':before==after,
  'host_candidate_outcomes':host,'proposal_outcomes':proposal_outcomes}

def main():
 if sys.argv[1:2]==['--order-worker']:
  print(json.dumps(order_worker(int(sys.argv[2])),sort_keys=True,separators=(',',':')));return 0
 if sys.argv[1:2]==['--score-worker']:
  print(json.dumps(score_worker(json.load(sys.stdin)),sort_keys=True,separators=(',',':')));return 0
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit('stale native engine: '+'; '.join(stale))
 env={**os.environ,'PYTHONPATH':f'{ROOT / "runners/dsl/python"}:{ROOT}:{ROOT / "evaluation/substrate_capability"}'}
 if sys.argv[1:]==['--lock']:
  if any(p.exists() for p in (LOCK,ORDERS,SCORES)):raise SystemExit('refusing to overwrite capture')
  LOCK.write_text(json.dumps({'schema':'GeneralStructuralProposalShapeSiteV1Lock','sources':frozen(),
   'semantic_engine':rust_source_fingerprint(str(ROOT)),'workers':WORKERS,'target':TARGET,
   'conditions':CONDITIONS,'candidate_policy':'all host candidates scored after order freeze'},indent=2,sort_keys=True)+'\n')
  print(LOCK.relative_to(ROOT));return 0
 if not LOCK.exists():raise SystemExit('missing source lock')
 lock=json.loads(LOCK.read_text());before=frozen()
 if before!=lock['sources']:raise SystemExit('source drift from shape-site lock')
 if sys.argv[1:]==['--orders']:
  if ORDERS.exists() or SCORES.exists():raise SystemExit('capture already exists')
  rows=[]
  for i in range(WORKERS):
   p=subprocess.run([sys.executable,str(RUNNER),'--order-worker',str(i)],cwd=ROOT,env=env,text=True,capture_output=True)
   if p.returncode:raise RuntimeError(f'order worker {i}: {p.stderr[-3000:]}')
   rows.append(json.loads(p.stdout.strip().splitlines()[-1]))
  if before!=frozen():raise SystemExit('source drift during order stage')
  ORDERS.write_text(json.dumps({'schema':'GeneralStructuralProposalShapeSiteV1Orders','lock_sha256':sha(LOCK),
   'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':{'platform':platform.platform(),
   'machine':platform.machine(),'python':sys.version.split()[0]},'workers':rows},indent=2,sort_keys=True)+'\n')
  print(json.dumps({'stage':'orders_frozen','workers':len(rows),'path':ORDERS.relative_to(ROOT).as_posix()}));return 0
 if sys.argv[1:]==['--score']:
  if not ORDERS.exists() or SCORES.exists():raise SystemExit('missing orders or score capture exists')
  doc=json.loads(ORDERS.read_text());rows=[]
  for order in doc['workers']:
   p=subprocess.run([sys.executable,str(RUNNER),'--score-worker'],input=json.dumps(order),cwd=ROOT,env=env,text=True,capture_output=True)
   if p.returncode:raise RuntimeError(f"score worker {order['worker']}: {p.stderr[-3000:]}")
   rows.append(json.loads(p.stdout.strip().splitlines()[-1]))
  if before!=frozen():raise SystemExit('source drift during score stage')
  SCORES.write_text(json.dumps({'schema':'GeneralStructuralProposalShapeSiteV1Scores','orders_sha256':sha(ORDERS),
   'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'workers':rows},indent=2,sort_keys=True)+'\n')
  print(json.dumps({'stage':'scored_after_order_freeze','workers':len(rows),'path':SCORES.relative_to(ROOT).as_posix()}));return 0
 raise SystemExit('choose --lock, --orders, or --score')
if __name__=='__main__':raise SystemExit(main())
