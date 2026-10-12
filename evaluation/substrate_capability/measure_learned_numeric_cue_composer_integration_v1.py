#!/usr/bin/env python3
"""Run frozen synthesized relation Terms through native residual cue composition."""
from __future__ import annotations
import copy,hashlib,importlib.util,itertools,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT),str(ROOT/'evaluation/substrate_capability')]
RUNNER=Path(__file__).resolve()
PREREG=ROOT/'docs/research/engine_substrate/LEARNED_NUMERIC_CUE_COMPOSER_INTEGRATION_V1_PREREG_20261003.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_learned_numeric_cue_composer_integration_v1.py'
LOCK=ROOT/'evaluation/substrate_capability/learned_numeric_cue_composer_integration_v1_lock_20261003.json'
OUT=ROOT/'evaluation/reports/learned_numeric_cue_composer_integration_v1_20261003.json'
BASE=ROOT/'evaluation/substrate_capability/measure_residual_to_composer_numeric_cue_v1.py'
LEARN_LOCK=ROOT/'evaluation/substrate_capability/numeric_opposition_relation_learning_v1_1_lock_20261003.json'
LEARN_CAPTURE=ROOT/'evaluation/reports/numeric_opposition_relation_learning_v1_1_20261003.json'
LEARN_ANALYSIS=ROOT/'evaluation/reports/numeric_opposition_relation_learning_v1_1_coverage_analysis_20261003.json'
TERM_MAP={'ax':'actual_dx','ay':'actual_dy','ex':'expected_dx','ey':'expected_dy'}

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load_module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod);return mod
def frozen():
 import thoughtexperiment_a8_proposal_bridge_v1_4 as bridge
 from substrate_rs import _native
 paths=(RUNNER,PREREG,ANALYZER,BASE,LEARN_LOCK,LEARN_CAPTURE,LEARN_ANALYSIS,
  ROOT/'domains/generator.py',ROOT/'domains/reflective_faculty.py',ROOT/'domains/edit_ops.py',
  ROOT/'domains/engine_provenance.py',ROOT/'domains/self_correction.py',
  ROOT/'runners/dsl/src/term.rs',ROOT/'runners/dsl/src/graph_rules.rs',ROOT/'runners/dsl/src/substrate.rs',
  ROOT/'runners/dsl/src/py.rs',ROOT/'runners/dsl/src/graph.rs',ROOT/'runners/dsl/src/grammar.rs',
  ROOT/'runners/dsl/src/sym.rs',ROOT/'runners/dsl/src/lib.rs',ROOT/'runners/dsl/src/persist.rs',
  ROOT/'runners/dsl/Cargo.toml',ROOT/'runners/dsl/Cargo.lock',ROOT/'runners/dsl/python/substrate_rs/__init__.py',
  ROOT/'evaluation/substrate_capability/thoughtexperiment_a8_generalization_adapters_v1.py',
  ROOT/'evaluation/substrate_capability/thoughtexperiment_a8_proposal_bridge_v1_4.py',
  ROOT/'evaluation/substrate_capability/measure_residual_to_composer_grounding_boundary_v1.py',
  ROOT/'evaluation/substrate_capability/thoughtexperiment_navigation_polarity_repair_v1_1.py',
  ROOT/'seeds/composer_experiment_graph.json',ROOT/'seeds/composer_dispatch.json',ROOT/'seeds/relation_vocabulary.json',
  ROOT/'seeds/autonomy.json',ROOT/'seeds/grid_navigation.json')
 return {'files':{str(p.relative_to(ROOT)):sha(p) for p in paths},
  'native_binary':{'path':str(Path(_native.__file__).resolve()),'sha256':sha(Path(_native.__file__).resolve())},
  'bridge_runtime':bridge.frozen()}
def term_digest(term):return hashlib.sha256(json.dumps(term,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def numeric_cue_rule(term,term_index):
 def bind(x):
  if isinstance(x,dict):
   if x.get('type')=='Var':
    key=TERM_MAP.get(x.get('name'))
    if key is None:raise ValueError(f"unexpected learned variable {x.get('name')}")
    return {'type':'Attr','node':{'type':'Var','name':'residual'},'key':key}
   return {k:bind(v) for k,v in x.items()}
  if isinstance(x,(list,tuple)):return [bind(v) for v in x]
  return x
 CUE=['test','send','judge','structure','gradient','flip','comparison','gate']
 key=f'learned_numeric_opposition_{term_index}_v1'
 where={'type':'And','items':[
  {'type':'Eq','a':{'type':'Attr','node':{'type':'Var','name':'residual'},'key':'schema'},'b':{'type':'Lit','value':'outcome_residual.v1'}},
  bind(term),
  {'type':'Eq','a':{'type':'Attr','node':{'type':'Var','name':'residual'},'key':'cue_derived'},'b':{'type':'Lit','value':0}}]}
 rule={'name':f'experiment_learned_numeric_cue_{term_index}','order':-100,
  'area':'experiment_residual_cue_derivation','comment':'Apply a frozen synthesized numeric relation Term to a raw outcome residual; cue vocabulary mapping is evaluator-authored.',
  'match':[['residual','is_outcome_residual','residual']],'where':where,
  'effects':[['set_attr','residual','cue_derived',1],
   ['add_node','axis','CapabilityAxis',{'induced':1.0,'capability_keys':[key],
    'residual_predicates':CUE,'from_observation':1.0,'source':'learned_numeric_residual_rule'}],
   ['add_edge','axis','derived_from_residual','residual']]}
 return rule,key
def primary_input(term_i,task_i,learn_terms=None):
 import thoughtexperiment_a8_generalization_adapters_v1 as adapters
 import thoughtexperiment_a8_proposal_bridge_v1_4 as bridge
 import domains.reflective_faculty as rf
 from measure_residual_to_composer_numeric_cue_v1 import TASKS,TARGETS,ACTION_VECTOR,BranchAgent,add_raw_residual,state,digest
 from measure_residual_to_composer_grounding_boundary_v1 import action_outcome
 from domains.engine_provenance import build_is_stale
 if build_is_stale(str(ROOT)):raise RuntimeError('native engine is stale')
 task=copy.deepcopy(TASKS[task_i]);worker_id=term_i*len(TASKS)+task_i
 ctx=adapters.prepare('navigation',worker_id,'train');sub,native,target=ctx['sub'],ctx['native'],ctx['target']
 if task['kind']=='opposite':
  observed=action_outcome(ctx,{'case':task['id'],'target':TARGETS[task['expected']],'expected':task['expected']})
  actual,expected=observed['actual'],observed['expected']
  if actual!=task['actual'] or expected!=task['expected']:raise RuntimeError(f'faulted outcome mismatch: {observed}')
 else:
  observed={'case':task['id'],'actual':task['actual'],'expected':task['expected'],'source':'synthetic_residual_control'}
  actual,expected=task['actual'],task['expected']
 if task['kind']=='absent_target':
  rules=native.export_rules();idx=next((j for j,r in enumerate(rules) if r.get('name')==target and r.get('active',True)),None)
  if idx is None or not native.remove_rule(idx):raise RuntimeError('could not remove target rule')
 residual_id=add_raw_residual(sub,task,actual,expected);primary_before=state(sub,native);snapshot=sub.snapshot()
 t=time.perf_counter_ns();baseline=snapshot.fork();base_fork_ns=time.perf_counter_ns()-t
 t=time.perf_counter_ns();candidate=snapshot.fork();candidate_fork_ns=time.perf_counter_ns()-t
 ba=BranchAgent(baseline,ctx['agent'].agent);ca=BranchAgent(candidate,ctx['agent'].agent)
 bn,cn=baseline._inner,candidate._inner;before_b=state(baseline,bn);before_c=state(candidate,cn)
 learned_term=learn_terms[term_i]['term'];rule,cue_key=numeric_cue_rule(learned_term,term_i)
 t=time.perf_counter_ns();cn.add_rule(rule);rule_install_ns=time.perf_counter_ns()-t
 av=ACTION_VECTOR.get(actual);ev=ACTION_VECTOR.get(expected);observation=[]
 if av is not None:observation.extend([['actual_dx',str(av[0])],['actual_dy',str(av[1])]])
 if ev is not None:observation.extend([['expected_dx',str(ev[0])],['expected_dy',str(ev[1])]])
 t=time.perf_counter_ns();base_induced=rf.induce_concern(ba,observation);base_induction_ns=time.perf_counter_ns()-t
 t=time.perf_counter_ns();base_ground=rf.ground_concern(ba,[base_induced.get('capability_key')]);base_ground_ns=time.perf_counter_ns()-t
 t=time.perf_counter_ns();induced=rf.induce_concern(ca,observation);induction_ns=time.perf_counter_ns()-t
 axis_nodes=[n for n in candidate.nodes('CapabilityAxis') if candidate.node(n)['attrs'].get('source')=='learned_numeric_residual_rule']
 attrs=candidate.node(residual_id)['attrs'];derived=bool(axis_nodes) and attrs.get('cue_derived')==1
 proposal_key=cue_key if derived else induced.get('capability_key')
 t=time.perf_counter_ns();ground=rf.ground_concern(ca,[proposal_key]);ground_ns=time.perf_counter_ns()-t
 structural=ground.get('structural_variant') or {};candidate_after=state(candidate,cn);base_after=state(baseline,bn)
 target_before=bridge._target_rule(native,target);heldout=None;score_ns=0
 if structural.get('built') and task['kind']=='opposite':
  t=time.perf_counter_ns();score_ctx=adapters.prepare('navigation',worker_id,'heldout')
  heldout=adapters.score(score_ctx,{'label':'learned_numeric_cue_candidate','rules':{target:structural['rule']}})
  score_ns=time.perf_counter_ns()-t
 primary_after=state(sub,native)
 receipt=sub.add_node('ExperimentResidual',{'experiment_id':f'learned_numeric_cue_v1_{term_i}_{task["id"]}',
  'source':'learned_numeric_cue_composer_integration_v1','task_case':task['id'],'learned_term_sha256':term_digest(learned_term),
  'derived_cue':derived,'cue_predicates':['test','send','judge','structure','gradient','flip','comparison','gate'] if derived else [],
  'proposal_built':bool(structural.get('built')),'operator':structural.get('kind'),'target_rule':structural.get('removed_rule'),
  'candidate_rule':structural.get('rule') if structural.get('built') else {},
  'heldout_pass':bool(heldout and heldout.get('oracle_pass'))})
 final=state(sub,native);receipt_id=int(receipt.value)
 before_nodes={r['id']:r['record'] for r in primary_before['nodes']};final_nodes={r['id']:r['record'] for r in final['nodes']}
 new_ids=sorted(set(final_nodes)-set(before_nodes));primary_unchanged=digest(primary_before)==digest(primary_after)
 only_returned=(new_ids==[receipt_id] and all(final_nodes.get(i)==v for i,v in before_nodes.items())
  and final['edges']==primary_before['edges'] and final['rules']==primary_before['rules'])
 return {'term_index':term_i,'task_index':task_i,'task':task,'source_stable':True,
  'learned_term':learned_term,'learned_term_sha256':term_digest(learned_term),'bound_rule_where':rule['where'],
  'task_outcome':observed,'observation':observation,'fork_ns':base_fork_ns+candidate_fork_ns,
  'rule_install_ns':rule_install_ns,'baseline':{'proposal_built':bool((base_ground.get('structural_variant') or {}).get('built')),
   'branch_changed':digest(before_b)!=digest(base_after),'induction_ns':base_induction_ns,'ground_ns':base_ground_ns},
  'candidate':{'derived_cue':derived,'native_rule_fired':derived,'cue_key':cue_key if derived else None,
   'induced_key':induced.get('capability_key'),'axis_count':len(axis_nodes),'induction_ns':induction_ns,
   'ground_ns':ground_ns,'branch_changed':digest(before_c)!=digest(candidate_after),
   'proposal_built':bool(structural.get('built')),'operator':structural.get('kind'),'target':structural.get('removed_rule'),
   'site':structural.get('site'),'heldout_score':heldout,'score_ns':score_ns,
   'target_rule_preserved_in_primary':bridge._target_rule(native,target)==target_before,
   'primary_rule_store_unchanged_during_compose':native.export_rules()==primary_before['rules']},
  'primary':{'unchanged_during_branch':primary_unchanged,'only_residual_returned':only_returned,
   'rules_unchanged_during_branch':primary_before['rules']==primary_after['rules'],
   'revision_unchanged_during_branch':primary_before['revision']==primary_after['revision'],
   'new_node_ids':new_ids,'returned_node_id':receipt_id}}

def one_worker(i,learn_terms):
 from measure_residual_to_composer_numeric_cue_v1 import TASKS
 term_i,task_i=divmod(i,len(TASKS));before=frozen();row=primary_input(term_i,task_i,learn_terms);after=frozen()
 row['source_before']=before;row['source_after']=after;row['source_stable']=before==after
 return row
def main():
 args=sys.argv[1:]
 if args[:1]==['--worker']:
  lock=json.loads(LOCK.read_text());idx=int(args[1]);print(json.dumps(one_worker(idx,lock['learned_terms']),sort_keys=True,separators=(',',':')));return 0
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite')
  if sha(LEARN_LOCK)!=json.load(open(LEARN_CAPTURE))['lock_sha256']:raise SystemExit('learner capture/lock mismatch')
  learner_lock=json.loads(LEARN_LOCK.read_text());learn=json.loads(LEARN_CAPTURE.read_text());analysis=json.loads(LEARN_ANALYSIS.read_text())
  if (learn.get('sources')!=learner_lock.get('sources') or not analysis.get('measurement_integrity_pass')
      or not analysis.get('generalization_gate_pass') or analysis.get('input_hashes',{}).get('lock_sha256')!=sha(LEARN_LOCK)
      or analysis.get('input_hashes',{}).get('capture_sha256')!=sha(LEARN_CAPTURE)):
   raise SystemExit('coverage-directed learner evidence did not validate')
  terms=[]
  for r in learn['workers']:
   terms.append({'worker':r['worker'],'term':r['term'],'sha256':term_digest(r['term']),
    'training_size':len(r['training']),'size':r['size'],'search_wall_ns':r['wall_ns'],'halt_reason':r['halt_reason']})
  from domains.engine_provenance import build_is_stale
  if build_is_stale(str(ROOT)):raise SystemExit('native engine is stale')
  tasks=load_module('learned_cue_task_source',BASE).TASKS
  LOCK.write_text(json.dumps({'schema':'LearnedNumericCueComposerIntegrationV1Lock','sources':frozen(),
   'learned_terms':terms,'tasks':tasks,
   'term_variable_to_residual_attribute':TERM_MAP,'cue_mapping':'authored fixed existing flip cue',
   'workers':len(terms)*len(tasks),
   'learned_term_count':len(terms),'candidate_backend':'Substrate.snapshot().fork()'},indent=2,sort_keys=True)+'\n')
  print(LOCK.relative_to(ROOT));return 0
 if args!=['--run']:raise SystemExit('usage: --lock, --run, or --worker ID')
 lock=json.loads(LOCK.read_text())
 if frozen()!=lock['sources']:raise SystemExit('source drift from lock')
 env={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}:{ROOT}/evaluation/substrate_capability'};rows=[]
 for i in range(lock['workers']):
  p=subprocess.run([sys.executable,str(RUNNER),'--worker',str(i)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=240)
  if p.returncode:raise RuntimeError(f'worker {i}: {p.stderr[-2500:]}')
  rows.append(json.loads(p.stdout.strip().splitlines()[-1]))
 if frozen()!=lock['sources']:raise SystemExit('source drift during integration run')
 OUT.write_text(json.dumps({'schema':'LearnedNumericCueComposerIntegrationV1Results','lock_sha256':sha(LOCK),
  'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),
  'sources':frozen(),'workers':rows},indent=2,sort_keys=True)+'\n')
 print(OUT.relative_to(ROOT));return 0
if __name__=='__main__':raise SystemExit(main())
