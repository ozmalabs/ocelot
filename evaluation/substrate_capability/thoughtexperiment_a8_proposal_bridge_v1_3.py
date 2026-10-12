#!/usr/bin/env python3
"""Two-stage source-locked A8 proposal bridge into the Thoughtexperiment scorer."""
from __future__ import annotations
import copy,hashlib,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'evaluation/substrate_capability')]
RUNNER=Path(__file__).resolve()
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_thoughtexperiment_a8_proposal_bridge_v1_3.py'
ADAPTER=ROOT/'evaluation/substrate_capability/thoughtexperiment_blinded_panel_adapters_v1.py'
NAV_TASK=ROOT/'evaluation/substrate_capability/thoughtexperiment_navigation_polarity_repair_v1_1.py'
PROTOCOL=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_A8_PROPOSAL_BRIDGE_V1_PREREG_20261002.md'
AMENDMENT=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_A8_PROPOSAL_BRIDGE_V1_3_AMENDMENT_20261003.md'
EVIDENCE=(ROOT/'docs/research/engine_substrate/MAC_FAC_A8_RESULTS.md',
 ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_NAVIGATION_POLARITY_REPAIR_V1_1_RESULTS_20261002.md',
 ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_BLINDED_PROPOSAL_UTILITY_V1_2_RESULTS_20261002.md',
 ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_A8_PROPOSAL_BRIDGE_V1_RESULTS_20261002.md',
 ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_A8_PROPOSAL_BRIDGE_V1_1_RESULTS_20261002.md',
 ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_A8_PROPOSAL_BRIDGE_V1_2_RESULTS_20261002.md')
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_a8_proposal_bridge_v1_3_lock_20261003.json'
ORDERS=ROOT/'evaluation/reports/thoughtexperiment_a8_proposal_bridge_v1_3_orders_20261003.json'
SCORES=ROOT/'evaluation/reports/thoughtexperiment_a8_proposal_bridge_v1_3_scores_20261003.json'
WORKERS=4
COMMON_CUE=['test','send','judge','structure','gradient']
PROMPT_CUE=COMMON_CUE+['flip','comparison','gate']
SOURCES=(
 'domains/reflective_faculty.py','domains/edit_ops.py','domains/self_correction.py',
 'domains/self_correct_dispatch.py','domains/engine_provenance.py','substrate/boot_core.py',
 'substrate/seed_loader.py','runners/dsl/src/py.rs','runners/dsl/src/substrate.rs',
 'runners/dsl/src/graph.rs','runners/dsl/src/graph_rules.rs','runners/dsl/src/term.rs',
 'runners/dsl/src/persist.rs','runners/dsl/src/grammar.rs','runners/dsl/src/sym.rs',
 'runners/dsl/src/lib.rs','runners/dsl/Cargo.toml','runners/dsl/Cargo.lock',
 'runners/dsl/python/substrate_rs/__init__.py','seeds/composer_experiment_graph.json',
 'seeds/composer_dispatch.json','seeds/relation_vocabulary.json','seeds/autonomy.json',
 'seeds/grid_navigation.json')

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def frozen()->dict:
 from substrate_rs import _native
 paths=(*[ROOT/p for p in SOURCES],ADAPTER,NAV_TASK,RUNNER,ANALYZER,PROTOCOL,AMENDMENT,*EVIDENCE)
 rows={str(p.relative_to(ROOT)):sha(p) for p in paths}
 rows['loaded_native_binary']=sha(Path(_native.__file__).resolve())
 return rows

def _target_rule(native,name):
 return next((copy.deepcopy(row) for row in native.export_rules()
  if row.get('name')==name and row.get('active',True)),None)

def _mutate_first_literal(value):
 if isinstance(value,dict):
  if value.get('type')=='Lit' and 'value' in value:
   value['value']=str(value['value'])+'__parity_mismatch__';return True
  for child in value.values():
   if _mutate_first_literal(child):return True
 elif isinstance(value,list):
  for child in value:
   if _mutate_first_literal(child):return True
 return False

def _parity_controls()->dict:
 """Exercise canonical positive parity after firing and four negative controls."""
 import domains.reflective_faculty as rf
 from substrate.seed_loader import manifest_for
 import thoughtexperiment_blinded_panel_adapters_v1 as adapters
 ctx=adapters.prepare('navigation',0,'train');key='a8_clause_parity_control'
 ctx['sub'].add_node('CapabilityAxis',{'is_axis':1.0,'capability_keys':[key],
  'induced':1.0,'residual_predicates':PROMPT_CUE,'from_observation':1.0,
  'source':'thoughtexperiment_a8_proposal_bridge_v1_3_parity_control'})
 result=rf.ground_concern(ctx['agent'],[key])
 manifest=manifest_for('composer_experiment_graph')
 manifest_rules=[row.get('attrs',{}) for row in manifest.get('nodes',[])
  if row.get('type')=='Rule' and row.get('attrs',{}).get('id')]
 active={row.get('name'):row for row in ctx['native'].export_rules()
  if isinstance(row,dict) and row.get('active',True)}
 expected_by_name={str(row['id']):{'name':str(row['id']),
  'match':row.get('match',[]),'where':row.get('where'),
  'effects':row.get('effect',row.get('effects'))} for row in manifest_rules}
 positives={name:rf._composer_rule_matches_manifest(active[name],expected)
  for name,expected in expected_by_name.items() if name in active}
 if len(positives)!=len(expected_by_name) or not all(positives.values()):
  raise RuntimeError(f'canonical positive parity controls failed: {positives}')
 sample_name='compose_experiment_judge_graph';sample=copy.deepcopy(active[sample_name]);expected=expected_by_name[sample_name]
 negatives={}
 changed=copy.deepcopy(sample);changed['effects'][0][0]=str(changed['effects'][0][0])+'__mismatch__'
 negatives['effect_operator_rejected']=not rf._composer_rule_matches_manifest(changed,expected)
 changed=copy.deepcopy(sample);changed['where']=copy.deepcopy(changed.get('where'))
 if not _mutate_first_literal(changed['where']):raise RuntimeError('could not form guard-literal mismatch control')
 negatives['guard_literal_rejected']=not rf._composer_rule_matches_manifest(changed,expected)
 changed=copy.deepcopy(sample);changed['effects']=copy.deepcopy(changed['effects'])
 if not _mutate_first_literal(changed['effects']):raise RuntimeError('could not form effect-literal mismatch control')
 negatives['effect_literal_rejected']=not rf._composer_rule_matches_manifest(changed,expected)
 changed=copy.deepcopy(sample);changed['effects']=list(reversed(changed['effects']))
 negatives['effect_order_rejected']=not rf._composer_rule_matches_manifest(changed,expected)
 if not all(negatives.values()):raise RuntimeError(f'canonical negative parity controls failed: {negatives}')
 if result.get('served_by')!='graph' or not (result.get('structural_variant') or {}).get('built'):
  raise RuntimeError('parity positive control did not complete graph-authored structural composition')
 return {'graph_composition_served_by':result.get('served_by'),
  'active_composer_rules':sorted(positives),'positive_canonical_matches':positives,
  'negative_mismatch_rejections':negatives}

def _digest(adapters,candidate):return adapters.digest(candidate)

def _describe(adapters,candidate):
 return {'label':str(candidate['label']),'digest':_digest(adapters,candidate),
  'targets':sorted((candidate.get('rules') or {}).keys()),
  'outcome_class':str(candidate.get('outcome_class') or '')}

def _compose(ctx,worker,cue):
 import domains.reflective_faculty as rf
 sub=ctx['sub'];native=ctx['native'];target=ctx['target'];task=ctx['task_module']
 axis_key=f'a8_proposal_{worker}_'+('prompted' if cue else 'unprompted')
 residual=list(PROMPT_CUE if cue else COMMON_CUE)
 target_before=_target_rule(native,target)
 sub.add_node('CapabilityAxis',{'is_axis':1.0,'capability_keys':[axis_key],
  'induced':1.0,'residual_predicates':residual,'from_observation':1.0,
  'source':'thoughtexperiment_a8_proposal_bridge_v1'})
 applicability=[];original=rf._ensure_editop_applicability
 def measured(sub0):
  started=time.perf_counter_ns()
  try:return original(sub0)
  finally:applicability.append(time.perf_counter_ns()-started)
 rf._ensure_editop_applicability=measured
 started=time.perf_counter_ns()
 try:result=rf.ground_concern(ctx['agent'],[axis_key])
 finally:rf._ensure_editop_applicability=original
 composer_ns=time.perf_counter_ns()-started
 structural=result.get('structural_variant') or {}
 target_after=_target_rule(native,target)
 rule=structural.get('rule') if structural.get('built') else None
 candidate=None
 if rule is not None:
  candidate={'label':f"a8_graph_{structural.get('kind')}",
   'rules':{target:copy.deepcopy(rule)}}
 return {'cue':residual,'grounded':bool(result.get('grounded')),
  'served_by':result.get('served_by'),'composer_path':result.get('path'),
  'built':bool(structural.get('built')),'kind':structural.get('kind'),
  'target':structural.get('removed_rule'),'site':structural.get('site'),
  'wall':structural.get('wall'),'candidate':candidate,
  'candidate_digest':_digest(__import__('thoughtexperiment_blinded_panel_adapters_v1'),candidate) if candidate else None,
  'target_rule_preserved_during_composition':target_before==target_after,
  'applicability_precompute_ns':sum(applicability),
  'composer_total_ns':composer_ns,'graph_mutation_revision':list(native.experiment_graph_rule_revision()),
  'candidate_descriptor':_describe(__import__('thoughtexperiment_blinded_panel_adapters_v1'),candidate) if candidate else None}

def _order_worker(worker:int)->dict:
 import thoughtexperiment_blinded_panel_adapters_v1 as adapters
 before=frozen();host_ctx=adapters.prepare('navigation',worker,'train')
 target=host_ctx['target'];candidates=[copy.deepcopy(x) for x in host_ctx['candidates']]
 if len(candidates)<3:raise RuntimeError('host reference candidate set has fewer than three candidates')
 labels=[x['label'] for x in candidates]
 if len(labels)!=len(set(labels)):raise RuntimeError('host reference candidate labels are not unique')
 host_desc=[_describe(adapters,c) for c in candidates]
 target_source=_target_rule(host_ctx['native'],target)
 prompted=_compose(host_ctx,worker,True)
 no_cue_ctx=adapters.prepare('navigation',worker,'train')
 no_cue=_compose(no_cue_ctx,worker,False)
 after=frozen()
 if before!=after:raise RuntimeError('source drift during order/proposal worker')
 return {'worker':worker,'pid':os.getpid(),'source_before':before,'source_after':after,
  'source_stable':before==after,'target_rule':target,'faulted_source_rule':target_source,
  'host_reference_candidates':candidates,'host_reference_descriptors':host_desc,
  'host_candidate_enumeration_ns':host_ctx['enumeration_ns'],
  'common_task_context_setup_ns':host_ctx['training_context_ns'],
  'prompted_graph_proposal':prompted,'unprompted_graph_proposal':no_cue}

def _score_worker(payload:dict)->dict:
 import thoughtexperiment_blinded_panel_adapters_v1 as adapters
 before=frozen();worker=int(payload['worker']);ctx=adapters.prepare('navigation',worker,'heldout')
 target=ctx['target']
 expected=payload['host_reference_descriptors'];actual=[_describe(adapters,c) for c in ctx['candidates']]
 if expected!=actual:raise RuntimeError('host reference descriptors changed between proposal and held-out scoring')
 if target!=payload['target_rule']:raise RuntimeError('target rule changed between stages')
 candidate_map={c['label']:c for c in payload['host_reference_candidates']}
 host_outcomes=[adapters.score(ctx,candidate_map[d['label']]) for d in expected]
 by_digest={row['digest']:row for row in host_outcomes}
 def score_proposal(row):
  candidate=row.get('candidate')
  if candidate is None:return None
  dg=_digest(adapters,candidate)
  if dg in by_digest:return {'outcome':by_digest[dg],'reused_host_candidate_label':by_digest[dg]['label'],
    'digest_match':True}
  return {'outcome':adapters.score(ctx,candidate),'reused_host_candidate_label':None,'digest_match':False}
 prompted=score_proposal(payload['prompted_graph_proposal'])
 unprompted=score_proposal(payload['unprompted_graph_proposal'])
 fault_control={'label':'fault_rule_control','rules':{target:copy.deepcopy(payload['faulted_source_rule'])}}
 fault_outcome=adapters.score(ctx,fault_control)
 # A separate source-correct control is reconstructed from the task fixture.
 task=ctx['task_module'];sub0,agent0,_module=task.build_agent();_,source_rule=task.active_rule(agent0.inner)
 source_control={'label':'source_rule_control','rules':{target:copy.deepcopy(source_rule)}}
 source_outcome=adapters.score(ctx,source_control)
 after=frozen()
 if before!=after:raise RuntimeError('source drift during held-out scoring worker')
 return {'worker':worker,'pid':os.getpid(),'source_before':before,'source_after':after,
  'source_stable':before==after,'heldout_context_setup_ns':ctx['training_context_ns'],
  'heldout_reference_enumeration_ns':ctx['enumeration_ns'],
  'host_candidate_outcomes':host_outcomes,'prompted_graph_proposal_outcome':prompted,
  'unprompted_graph_proposal_outcome':unprompted,'fault_rule_control':fault_outcome,
  'source_rule_control':source_outcome}

def main()->int:
 if sys.argv[1:2]==['--order-worker']:
  print(json.dumps(_order_worker(int(sys.argv[2])),sort_keys=True,separators=(',',':')));return 0
 if sys.argv[1:2]==['--score-worker']:
  print(json.dumps(_score_worker(json.load(sys.stdin)),sort_keys=True,separators=(',',':')));return 0
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit('stale native engine: '+'; '.join(stale))
 if sys.argv[1:]==['--lock']:
  if any(p.exists() for p in (LOCK,ORDERS,SCORES)):raise SystemExit('refusing to overwrite existing lock/capture')
  parity_controls=_parity_controls()
  LOCK.write_text(json.dumps({'schema':'ThoughtexperimentA8ProposalBridgeV1_3Lock',
   'sources':frozen(),'semantic_engine':rust_source_fingerprint(str(ROOT)),
   'canonical_clause_parity_controls':parity_controls,
   'workers':WORKERS,'cue_predicates':{'prompted':PROMPT_CUE,'unprompted':COMMON_CUE},
   'heldout_cases':['down','right'],'candidate_policy':'exhaustive reference scoring; default-order prefix; one graph proposal'},indent=2,sort_keys=True)+'\n')
  print(LOCK.relative_to(ROOT));return 0
 if not LOCK.exists():raise SystemExit('missing source lock')
 lock=json.loads(LOCK.read_text());before=frozen()
 if before!=lock['sources']:raise SystemExit('source drift from panel lock')
 env={**os.environ,'PYTHONPATH':f'{ROOT / "runners/dsl/python"}:{ROOT}:{ROOT / "evaluation/substrate_capability"}'}
 if sys.argv[1:]==['--orders']:
  if ORDERS.exists() or SCORES.exists():raise SystemExit('order or score capture already exists')
  rows=[]
  for worker in range(WORKERS):
   proc=subprocess.run([sys.executable,str(RUNNER),'--order-worker',str(worker)],cwd=ROOT,env=env,text=True,capture_output=True)
   if proc.returncode:raise RuntimeError(f'order worker {worker}: {proc.stderr[-4000:]}')
   rows.append(json.loads(proc.stdout.strip().splitlines()[-1]))
  after=frozen()
  if before!=after:raise SystemExit('source drift during order capture')
  ORDERS.write_text(json.dumps({'schema':'ThoughtexperimentA8ProposalBridgeV1_3Orders',
   'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':{'platform':platform.platform(),
   'machine':platform.machine(),'python':sys.version.split()[0]},'lock':lock,'source_before':before,
   'source_after':after,'semantic_engine':rust_source_fingerprint(str(ROOT)),'workers':rows},indent=2,sort_keys=True)+'\n')
  print(json.dumps({'stage':'orders_frozen','workers':len(rows),'orders':ORDERS.relative_to(ROOT).as_posix()},sort_keys=True));return 0
 if sys.argv[1:]==['--score']:
  if not ORDERS.exists() or SCORES.exists():raise SystemExit('missing orders or scores already exist')
  doc=json.loads(ORDERS.read_text())
  for row in doc['workers']:
   prompted=row['prompted_graph_proposal'];unprompted=row['unprompted_graph_proposal']
   if prompted.get('served_by')!='graph' or not prompted.get('built') or not prompted.get('target_rule_preserved_during_composition'):
    raise SystemExit(f"refusing held-out scoring: worker {row['worker']} prompted graph attribution/preservation gate failed")
   if prompted.get('kind')!='flip_comparison' or prompted.get('target')!='hop_descend_gradient':
    raise SystemExit(f"refusing held-out scoring: worker {row['worker']} prompted proposal operator/target gate failed")
   if unprompted.get('served_by')!='graph' or unprompted.get('built') or unprompted.get('candidate') is not None:
    raise SystemExit(f"refusing held-out scoring: worker {row['worker']} graph no-cue abstention gate failed")
  rows=[]
  for payload in doc['workers']:
   proc=subprocess.run([sys.executable,str(RUNNER),'--score-worker'],input=json.dumps(payload),cwd=ROOT,env=env,text=True,capture_output=True)
   if proc.returncode:raise RuntimeError(f"score worker {payload['worker']}: {proc.stderr[-4000:]}")
   rows.append(json.loads(proc.stdout.strip().splitlines()[-1]))
  after=frozen()
  if before!=after:raise SystemExit('source drift during score capture')
  SCORES.write_text(json.dumps({'schema':'ThoughtexperimentA8ProposalBridgeV1_3Scores',
   'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
   'orders_sha256':sha(ORDERS),'source_before':before,'source_after':after,'workers':rows},indent=2,sort_keys=True)+'\n')
  print(json.dumps({'stage':'heldout_scored','workers':len(rows),'scores':SCORES.relative_to(ROOT).as_posix()},sort_keys=True));return 0
 raise SystemExit('choose --lock, --orders, or --score')
if __name__=='__main__':raise SystemExit(main())
