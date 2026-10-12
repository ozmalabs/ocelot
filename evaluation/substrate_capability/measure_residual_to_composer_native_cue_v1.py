#!/usr/bin/env python3
"""Measure native graph-rule derivation of a composer cue from raw residuals."""
from __future__ import annotations
import copy, hashlib, importlib.util, json, os, platform, subprocess, sys, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'evaluation/substrate_capability')]
RUNNER=Path(__file__).resolve()
PREREG=ROOT/'docs/research/engine_substrate/RESIDUAL_TO_COMPOSER_NATIVE_CUE_V1_PREREG_20261003.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_residual_to_composer_native_cue_v1.py'
LOCK=ROOT/'evaluation/substrate_capability/residual_to_composer_native_cue_v1_lock_20261003.json'
OUT=ROOT/'evaluation/reports/residual_to_composer_native_cue_v1_20261003.json'
BASELINE=ROOT/'evaluation/substrate_capability/measure_residual_to_composer_grounding_boundary_v1.py'
BRANCH_BASE=ROOT/'evaluation/substrate_capability/measure_residual_to_composer_branch_isolation_v1.py'
ADAPTER=ROOT/'evaluation/substrate_capability/thoughtexperiment_a8_generalization_adapters_v1.py'
BRIDGE=ROOT/'evaluation/substrate_capability/thoughtexperiment_a8_proposal_bridge_v1_4.py'
TASK_RUNNER=ROOT/'evaluation/substrate_capability/thoughtexperiment_navigation_polarity_repair_v1_1.py'
TASKS=[
 {'id':'opposite_up','actual':'Down','expected':'Up','kind':'opposite'},
 {'id':'opposite_down','actual':'Up','expected':'Down','kind':'opposite'},
 {'id':'opposite_left','actual':'Right','expected':'Left','kind':'opposite'},
 {'id':'opposite_right','actual':'Left','expected':'Right','kind':'opposite'},
 {'id':'orthogonal','actual':'Right','expected':'Up','kind':'other'},
 {'id':'orthogonal_2','actual':'Up','expected':'Left','kind':'other'},
 {'id':'same_direction','actual':'Up','expected':'Up','kind':'other'},
 {'id':'same_direction_2','actual':'Left','expected':'Left','kind':'other'},
 {'id':'unknown_action','actual':'Teleport','expected':'Up','kind':'unknown'},
 {'id':'unknown_expected','actual':'Down','expected':'Portal','kind':'unknown'},
 {'id':'missing_expected','actual':'Down','expected':None,'kind':'missing'},
 {'id':'zero_displacement','actual':'Stay','expected':'Up','kind':'zero'},
 {'id':'target_absent','actual':'Down','expected':'Up','kind':'absent_target'},
]
ACTION_PAIRS=(('Up','Down'),('Down','Up'),('Left','Right'),('Right','Left'))
TARGETS={'Up':[4.0,5.0],'Down':[6.0,5.0],'Left':[5.0,4.0],'Right':[5.0,6.0]}
CUE=['test','send','judge','structure','gradient','flip','comparison','gate']
SOURCES=('domains/reflective_faculty.py','domains/edit_ops.py','domains/self_correction.py',
 'domains/engine_provenance.py','substrate/boot_core.py','substrate/seed_loader.py',
 'runners/dsl/src/py.rs','runners/dsl/src/substrate.rs','runners/dsl/src/graph.rs',
 'runners/dsl/src/graph_rules.rs','runners/dsl/src/term.rs','runners/dsl/src/persist.rs',
 'runners/dsl/src/grammar.rs','runners/dsl/src/sym.rs','runners/dsl/src/lib.rs',
 'runners/dsl/Cargo.toml','runners/dsl/Cargo.lock',
 'runners/dsl/python/substrate_rs/__init__.py',
 'seeds/composer_experiment_graph.json','seeds/composer_dispatch.json',
 'seeds/relation_vocabulary.json','seeds/autonomy.json','seeds/grid_navigation.json')
WORKERS=len(TASKS)

def sha(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()
def load_module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod);return mod
def frozen():
 from substrate_rs import _native
 bridge=load_module('native_cue_bridge_hash',BRIDGE)
 files={str(p.relative_to(ROOT)):sha(p) for p in
        (RUNNER,PREREG,ANALYZER,BASELINE,BRANCH_BASE,ADAPTER,BRIDGE,TASK_RUNNER,*[ROOT/s for s in SOURCES])}
 return {'files':files,'native_binary':{'path':str(Path(_native.__file__).resolve()),
         'sha256':sha(Path(_native.__file__).resolve())},'bridge_runtime':bridge.frozen()}

def canon(value):
 if hasattr(value,'value') and type(value).__name__=='NodeID':return int(value.value)
 if isinstance(value,dict):return {str(k):canon(v) for k,v in sorted(value.items(),key=lambda kv:str(kv[0]))}
 if isinstance(value,(list,tuple)):return [canon(v) for v in value]
 return value
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()
def state(sub,native):
 nodes=[];edges=set()
 for nid in sorted(sub.nodes(),key=lambda n:int(n.value)):
  nodes.append({'id':int(nid.value),'record':canon(sub.node(nid))})
  for edge in sub.incident_edges(nid):edges.add(json.dumps(canon(edge),sort_keys=True,separators=(',',':'),default=str))
 return {'nodes':nodes,'edges':sorted(edges),'rules':native.export_rules(),
         'revision':list(native.experiment_graph_rule_revision()),
         'node_count':sub.node_count(),'edge_count':sub.edge_count()}

def V(name):return {'type':'Var','name':name}
def L(value):return {'type':'Lit','value':value}
def A(name,key):return {'type':'Attr','node':V(name),'key':key}
def Eq(left,right):return {'type':'Eq','a':left,'b':right}
def And(*items):return {'type':'And','items':list(items)}
def native_cue_rule():
 return {'name':'experiment_derive_flip_cue_from_opposite_action_relation','order':-100,
  'area':'experiment_residual_cue_derivation',
  'comment':'Map raw action residuals to the held flip cue when task ontology marks their actions as exact opposites.',
  'match':[['residual','is_outcome_residual','residual'],['pair','is_opposite_action_pair','pair']],
  'where':And(Eq(A('residual','schema'),L('outcome_residual.v1')),
   Eq(A('pair','schema'),L('opposite_action_pair.v1')),
   Eq(A('residual','actual_action'),A('pair','source_action')),
   Eq(A('residual','expected_action'),A('pair','target_action')),
   Eq(A('residual','cue_derived'),L(0))),
  'effects':[
   ['set_attr','residual','cue_derived',1],
   ['add_node','axis','CapabilityAxis',{'induced':1.0,'capability_keys':['native_residual_opposite_v1'],
    'residual_predicates':CUE,'from_observation':1.0,'source':'native_residual_opposition_rule'}],
   ['add_edge','axis','derived_from_residual','residual']]}

class BranchAgent:
 def __init__(self,sub,root):self.s=sub;self.inner=sub._inner;self.agent=root

def add_action_ontology(sub):
 for index,(source,target) in enumerate(ACTION_PAIRS):
  pair=sub.add_node('OppositeActionPair',{'schema':'opposite_action_pair.v1','source_action':source,
   'target_action':target,'domain':'cardinal_grid','pair_ordinal':index})
  sub.add_edge_unchecked(pair,'is_opposite_action_pair',pair,{})

def add_raw_residual(sub,task,actual,expected):
 node=sub.add_node('OutcomeResidual',{'schema':'outcome_residual.v1','actual_action':actual,
  'expected_action':expected,'cue_derived':0,'observation_status':'not_observed' if task['kind']!='opposite' else 'observed'})
 sub.add_edge_unchecked(node,'is_outcome_residual',node,{})
 return node

def worker(i):
 import thoughtexperiment_a8_generalization_adapters_v1 as adapters
 import thoughtexperiment_a8_proposal_bridge_v1_4 as bridge
 from measure_residual_to_composer_grounding_boundary_v1 import action_outcome
 import domains.reflective_faculty as rf
 from domains.engine_provenance import build_is_stale
 if build_is_stale(str(ROOT)):raise RuntimeError('native engine is stale')
 task=TASKS[i];before=frozen();ctx=adapters.prepare('navigation',i,'train')
 sub,native=ctx['sub'],ctx['native'];target=ctx['target']
 if task['kind']=='opposite':
  observed=action_outcome(ctx,{'case':task['id'],'target':TARGETS[task['expected']],
                              'expected':task['expected']})
  actual,expected=observed['actual'],observed['expected']
  if actual!=task['actual'] or expected!=task['expected']:
   raise RuntimeError(f"faulted task residual disagrees with fixture: {task} vs {observed}")
 else:
  observed={'case':task['id'],'actual':task['actual'],'expected':task['expected'],
            'source':'synthetic_residual_control'}
  actual,expected=task['actual'],task['expected']
 if task['kind']=='absent_target':
  rows=native.export_rules();idx=next((j for j,r in enumerate(rows)
   if r.get('name')==target and r.get('active',True)),None)
  if idx is None or not native.remove_rule(idx):raise RuntimeError('could not remove target rule')
 add_action_ontology(sub);residual_id=add_raw_residual(sub,task,actual,expected)
 primary_before=state(sub,native);snapshot=sub.snapshot()
 fork_started=time.perf_counter_ns();baseline=snapshot.fork();baseline_fork_ns=time.perf_counter_ns()-fork_started
 fork_started=time.perf_counter_ns();candidate=snapshot.fork();candidate_fork_ns=time.perf_counter_ns()-fork_started
 ba=BranchAgent(baseline,ctx['agent'].agent);ca=BranchAgent(candidate,ctx['agent'].agent)
 baseline_native=baseline._inner;candidate_native=candidate._inner
 base_before=state(baseline,baseline_native);candidate_before=state(candidate,candidate_native)
 candidate_native.add_rule(native_cue_rule())
 raw_observation=[['actual',str(actual)]]
 if expected is not None:raw_observation.append(['expected',str(expected)])
 t=time.perf_counter_ns();base_induced=rf.induce_concern(ba,raw_observation);base_induce_ns=time.perf_counter_ns()-t
 base_key=base_induced.get('capability_key')
 t=time.perf_counter_ns();base_ground=rf.ground_concern(ba,[base_key]);base_ground_ns=time.perf_counter_ns()-t
 t=time.perf_counter_ns();induced=rf.induce_concern(ca,raw_observation);induce_ns=time.perf_counter_ns()-t
 axis_nodes=[n for n in candidate.nodes('CapabilityAxis')
  if candidate.node(n)['attrs'].get('source')=='native_residual_opposition_rule']
 native_cue_attrs=[dict(candidate.node(n)['attrs']) for n in axis_nodes]
 residual_after=candidate.node(residual_id)['attrs']
 derived=bool(axis_nodes) and residual_after.get('cue_derived')==1
 proposal_key='native_residual_opposite_v1' if derived else induced.get('capability_key')
 t=time.perf_counter_ns();ground=rf.ground_concern(ca,[proposal_key]);ground_ns=time.perf_counter_ns()-t
 structural=ground.get('structural_variant') or {}
 base_after=state(baseline,baseline_native);candidate_after=state(candidate,candidate_native)
 target_before=bridge._target_rule(native,target)
 # Candidate scoring happens in a fresh held-out context and never mutates primary.
 heldout=None
 if structural.get('built') and task['kind']=='opposite':
  score_ctx=adapters.prepare('navigation',i,'heldout')
  heldout=adapters.score(score_ctx,{'label':'native_residual_candidate',
                                     'rules':{target:structural['rule']}})
 primary_after=state(sub,native)
 # Return a compact result receipt. Branch-only seed/rule growth is not copied.
 receipt=sub.add_node('ExperimentResidual',{'experiment_id':f'native_cue_v1_worker_{i}_{task["id"]}',
  'source':'residual_to_composer_native_cue_v1','task_case':task['id'],
  'raw_actual_action':actual,'raw_expected_action':expected,'derived_cue':bool(derived),
  'cue_predicates':CUE if derived else [],'proposal_built':bool(structural.get('built')),
  'target_rule':structural.get('removed_rule'),'operator':structural.get('kind'),
  'candidate_rule':structural.get('rule') if structural.get('built') else {},
  'heldout_pass':bool(heldout and heldout.get('oracle_pass'))})
 primary_after_return=state(sub,native)
 receipt_id=int(receipt.value)
 before_nodes={row['id']:row['record'] for row in primary_before['nodes']}
 final_nodes={row['id']:row['record'] for row in primary_after_return['nodes']}
 new_ids=sorted(set(final_nodes)-set(before_nodes))
 primary_isolated=(digest(primary_before)==digest(primary_after))
 original_preserved=all(final_nodes.get(nid)==record for nid,record in before_nodes.items())
 after=frozen()
 return {'worker':i,'task':task,'source_before':before,'source_after':after,'source_stable':before==after,
  'raw_residual':observed,'observation_passed_to_induction':raw_observation,
  'fork_ms':(baseline_fork_ns+candidate_fork_ns)/1e6,
  'baseline':{'fork_ns':baseline_fork_ns,'induced_key':base_key,'grounded':bool(base_ground.get('grounded')),
   'proposal_built':bool((base_ground.get('structural_variant') or {}).get('built')),
   'grounding_ns':base_ground_ns,'branch_changed':digest(base_before)!=digest(base_after)},
  'candidate':{'native_cue_rule_observed_fired':derived,
   'derived_cue':derived,'axis_attrs':native_cue_attrs,'fork_ns':candidate_fork_ns,
   'induced_key':induced.get('capability_key'),'induction_ns':induce_ns,'grounding_ns':ground_ns,
   'proposal_built':bool(structural.get('built')),'operator':structural.get('kind'),
   'target':structural.get('removed_rule'),'site':structural.get('site'),
   'target_rule_preserved_in_primary':bridge._target_rule(native,target)==target_before,
   'heldout_score':heldout,'branch_changed':digest(candidate_before)!=digest(candidate_after),
   'branch_rule_count_delta':len(candidate_after['rules'])-len(candidate_before['rules']),
   'branch_node_delta':candidate_after['node_count']-candidate_before['node_count'],
   'native_cue_mapping_source':'branch_only_native_rule'},
  'primary':{'unchanged_during_branch':primary_isolated,'rules_unchanged_during_branch':
   primary_before['rules']==primary_after['rules'],'revision_unchanged_during_branch':
   primary_before['revision']==primary_after['revision'],'only_residual_returned':
   new_ids==[receipt_id] and original_preserved and primary_after_return['edges']==primary_before['edges']
   and primary_after_return['rules']==primary_before['rules'],'new_node_ids':new_ids,
   'returned_residual_id':receipt_id,'returned_candidate_present':bool(
    sub.node(receipt)['attrs'].get('candidate_rule'))}}

def main():
 args=sys.argv[1:]
 if args[:1]==['--worker']:
  print(json.dumps(worker(int(args[1])),sort_keys=True,separators=(',',':')));return 0
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite existing lock/capture')
  from domains.engine_provenance import build_is_stale,rust_source_fingerprint
  stale=build_is_stale(str(ROOT))
  if stale:raise SystemExit('stale native engine: '+'; '.join(stale))
  LOCK.write_text(json.dumps({'schema':'ResidualToComposerNativeCueV1Lock','sources':frozen(),
   'tasks':TASKS,'directed_action_relations':ACTION_PAIRS,'workers':WORKERS,
   'native_rule':native_cue_rule(),'candidate_backend':'Substrate.snapshot().fork()'},indent=2,sort_keys=True)+'\n')
  print(LOCK.relative_to(ROOT));return 0
 if args!=['--run']:raise SystemExit('usage: --lock, --run, or --worker ID')
 lock=json.loads(LOCK.read_text())
 if frozen()!=lock['sources']:raise SystemExit('source drift from lock')
 env={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}:{ROOT}/evaluation/substrate_capability'}
 rows=[]
 for i in range(lock['workers']):
  proc=subprocess.run([sys.executable,str(RUNNER),'--worker',str(i)],cwd=ROOT,env=env,
   text=True,capture_output=True,timeout=240)
  if proc.returncode:raise RuntimeError(f'worker {i}: {proc.stderr[-3000:]}')
  rows.append(json.loads(proc.stdout.strip().splitlines()[-1]))
 if frozen()!=lock['sources']:raise SystemExit('source drift during run')
 OUT.write_text(json.dumps({'schema':'ResidualToComposerNativeCueV1Results','lock_sha256':sha(LOCK),
  'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),
  'sources':frozen(),'workers':rows},indent=2,sort_keys=True)+'\n')
 print(OUT.relative_to(ROOT));return 0
if __name__=='__main__':raise SystemExit(main())
