#!/usr/bin/env python3
"""Compare event+full-rematch, effect trace, and counterfactual branch diagnosis."""
from __future__ import annotations
import hashlib,json,os,platform,random,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
RUNNER=Path(__file__).resolve();ANALYZER=ROOT/'evaluation/substrate_capability/analyze_thoughtexperiment_effect_trace_counterfactual_v1.py'
PROTOCOL=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_EFFECT_TRACE_COUNTERFACTUAL_V1_PREREG_20261005.md'
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_effect_trace_counterfactual_v1_lock_20261005.json'
OUT=ROOT/'evaluation/reports/thoughtexperiment_effect_trace_counterfactual_v1_20261005.json'
SOURCES=('runners/dsl/Cargo.toml','runners/dsl/Cargo.lock','runners/dsl/src/graph.rs','runners/dsl/src/rewrite.rs','runners/dsl/src/substrate.rs','runners/dsl/src/py.rs','runners/dsl/python/substrate_rs/ext.py','runners/dsl/python/substrate_rs/__init__.py','runners/dsl/python/substrate_rs/_native.build.json')
SIZES=(4,8,16,32);CASES_PER_SIZE=20
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def frozen():
 from substrate_rs import _native
 files=(RUNNER,ANALYZER,PROTOCOL,*(ROOT/x for x in SOURCES));binary=Path(_native.__file__).resolve()
 return {'files':{str(p.relative_to(ROOT)):sha(p) for p in files},'native_binary':{'path':str(binary),'sha256':sha(binary)}}
def make_base(size,case_id):
 from substrate_rs import Substrate
 rng=random.Random(0xC0A71+case_id*65537+size*524287);base=Substrate();anchor=base.add_node('Anchor',{})
 order=list(range(size));rng.shuffle(order);nodes={i:base.add_node('Target',{'health':0,'slot':i}) for i in order}
 vars_=[f'v{i}' for i in range(size)];slot_order=list(range(size));rng.shuffle(slot_order)
 for i in range(size):base.add_edge_unchecked(anchor,f'slot_{i}',nodes[i])
 clause_order=list(range(size));rng.shuffle(clause_order)
 match=[['anchor',f'slot_{i}',vars_[i]] for i in clause_order]
 effect_order=list(range(size));rng.shuffle(effect_order);bad_var=rng.randrange(size);bad_effect_index=effect_order.index(bad_var)
 effects=[['set_attr',vars_[i],'health',999 if i==bad_var else 1] for i in effect_order]
 rule={'name':'calibration_sweep','match':match,'effects':effects}
 base._inner.add_rule(rule)
 snapshot=base._snapshot_with_backend('shared_graph_pages')
 oracle={'case_id':case_id,'size':size,'bad_variable':vars_[bad_var],'bad_node_id':nodes[bad_var].value,'bad_effect_index':bad_effect_index,'effect_variables':[vars_[i] for i in effect_order],'variable_node_ids':{vars_[i]:nodes[i].value for i in range(size)}}
 return base,snapshot,rule,oracle
def unify(pattern_term,node_id,binding):
 if pattern_term in binding:return binding[pattern_term]==node_id
 if node_id in binding.values():return False
 binding[pattern_term]=node_id;return True
def full_rematch(graph,rule,target_node):
 edge_rows=[(int(e['src']),str(e['type']),int(e['tgt'])) for e in graph['edges']]
 bindings=[{}]
 for src,edge_type,tgt in rule['match']:
  next_bindings=[]
  for old in bindings:
   for edge_src,edge_name,edge_tgt in edge_rows:
    if edge_name!=edge_type:continue
    current=dict(old)
    if unify(src,edge_src,current) and unify(tgt,edge_tgt,current):next_bindings.append(current)
  bindings=next_bindings
  if not bindings:break
 if len(bindings)!=1:return []
 binding=bindings[0];result=[]
 for index,effect in enumerate(rule['effects']):
  if effect[0]=='set_attr' and effect[2]=='health' and binding.get(effect[1])==target_node:
   result.append(index)
 return result
def branch_omission(snapshot,rule,effect_index,target_node):
 branch=snapshot.fork();variant={**rule,'effects':[e for i,e in enumerate(rule['effects']) if i!=effect_index]}
 if not branch._inner.replace_active_rule_by_name('calibration_sweep',variant):raise RuntimeError('counterfactual replacement refused')
 receipt=branch._inner.run_rules_report(1,False);graph=branch._inner.graph_to_dict()
 target=next((n for n in graph['nodes'] if int(n['id'])==target_node),None)
 cured=target is not None and target.get('attrs',{}).get('health',0)!=999
 return cured,receipt
def execute_case(size,case_id):
 base,snapshot,rule,oracle=make_base(size,case_id);primary_before=base._inner.graph_to_dict();primary_digest=hashlib.sha256(json.dumps(primary_before,sort_keys=True,separators=(',',':')).encode()).hexdigest();revision_before=tuple(base._inner.experiment_graph_rule_revision())
 # Endpoint-only closure and full graph/rule rematching.
 endpoint_branch=snapshot.fork();t0=time.perf_counter_ns();c0=time.process_time_ns();endpoint_report=endpoint_branch._inner.run_rules_delta_report(1,False);endpoint_graph=endpoint_branch._inner.graph_to_dict();endpoint_observer_wall=time.perf_counter_ns()-t0;endpoint_observer_cpu=time.process_time_ns()-c0
 t0=time.perf_counter_ns();c0=time.process_time_ns();rematch_candidates=full_rematch(endpoint_graph,rule,oracle['bad_node_id']);rematch_wall=time.perf_counter_ns()-t0;rematch_cpu=time.process_time_ns()-c0
 t0=time.perf_counter_ns();c0=time.process_time_ns();rematch_attempts=0;rematch_found=None
 for candidate in rematch_candidates:
  rematch_attempts+=1;cured,_=branch_omission(snapshot,rule,candidate,oracle['bad_node_id'])
  if cured:rematch_found=candidate;break
 rematch_branch_wall=time.perf_counter_ns()-t0;rematch_branch_cpu=time.process_time_ns()-c0
 # Endpoint-only policy searches effect indices in order by counterfactual omission.
 t0=time.perf_counter_ns();c0=time.process_time_ns();endpoint_attempts=0;endpoint_found=None
 for candidate in range(size):
  endpoint_attempts+=1;cured,_=branch_omission(snapshot,rule,candidate,oracle['bad_node_id'])
  if cured:endpoint_found=candidate;break
 endpoint_search_wall=time.perf_counter_ns()-t0;endpoint_search_cpu=time.process_time_ns()-c0
 # Per-effect trace localizes the failing target before one omission branch.
 trace_branch=snapshot.fork();t0=time.perf_counter_ns();c0=time.process_time_ns();trace_report=trace_branch._inner.run_rules_effect_delta_report(1,False);trace_observer_wall=time.perf_counter_ns()-t0;trace_observer_cpu=time.process_time_ns()-c0
 trace_events=[e for e in trace_report['rule_write_events'] if e['rule_name']=='calibration_sweep' and e['progressed']]
 trace_candidates=[]
 for event in trace_events:
  for effect in event.get('effect_snapshots',[]):
   if any(int(v['node_id'])==oracle['bad_node_id'] and v['after'] is not None and v['after']['attrs'].get('health')==999 for v in effect.get('node_values',[])):
    trace_candidates.append(int(effect['effect_index']))
 t0=time.perf_counter_ns();c0=time.process_time_ns();trace_attempts=0;trace_found=None
 for candidate in trace_candidates:
  trace_attempts+=1;cured,_=branch_omission(snapshot,rule,candidate,oracle['bad_node_id'])
  if cured:trace_found=candidate;break
 trace_branch_wall=time.perf_counter_ns()-t0;trace_branch_cpu=time.process_time_ns()-c0
 primary_after=base._inner.graph_to_dict();primary_after_digest=hashlib.sha256(json.dumps(primary_after,sort_keys=True,separators=(',',':')).encode()).hexdigest()
 endpoint_events=[e for e in endpoint_report['rule_write_events'] if e['rule_name']=='calibration_sweep' and e['progressed']]
 revision_after=tuple(base._inner.experiment_graph_rule_revision())
 return {'case_id':case_id,'size':size,'oracle':oracle,'endpoint':{'candidate_count':size,'candidate_attempts':endpoint_attempts,'found':endpoint_found,'status':endpoint_report['status'],'progress_steps':endpoint_report['progress_steps'],'observer_wall_ns':endpoint_observer_wall,'observer_cpu_ns':endpoint_observer_cpu,'search_wall_ns':endpoint_search_wall,'search_cpu_ns':endpoint_search_cpu,'event_count':len(endpoint_events),'event_effect_snapshots':sum(len(e.get('effect_snapshots',[])) for e in endpoint_events)},'full_rematch':{'candidates':rematch_candidates,'attempts':rematch_attempts,'found':rematch_found,'rematch_wall_ns':rematch_wall,'rematch_cpu_ns':rematch_cpu,'branch_wall_ns':rematch_branch_wall,'branch_cpu_ns':rematch_branch_cpu,'total_wall_ns':endpoint_observer_wall+rematch_wall+rematch_branch_wall,'total_cpu_ns':endpoint_observer_cpu+rematch_cpu+rematch_branch_cpu},'effect_trace':{'candidates':trace_candidates,'attempts':trace_attempts,'found':trace_found,'status':trace_report['status'],'progress_steps':trace_report['progress_steps'],'observer_wall_ns':trace_observer_wall,'observer_cpu_ns':trace_observer_cpu,'branch_wall_ns':trace_branch_wall,'branch_cpu_ns':trace_branch_cpu,'total_wall_ns':trace_observer_wall+trace_branch_wall,'total_cpu_ns':trace_observer_cpu+trace_branch_cpu,'event_count':len(trace_events),'snapshots_truncated':trace_report['rule_write_effect_snapshots_truncated']},'endpoint_total_wall_ns':endpoint_observer_wall+endpoint_search_wall,'endpoint_total_cpu_ns':endpoint_observer_cpu+endpoint_search_cpu,'primary_unchanged':primary_digest==primary_after_digest and revision_before==revision_after,'primary_digest':primary_digest,'primary_after_digest':primary_after_digest,'primary_revision_before':revision_before,'primary_revision_after':revision_after}
def worker(index):
 locked=json.loads(LOCK.read_text())['sources'];before=frozen()
 if before!=locked:raise RuntimeError('source lock mismatch before worker')
 rows=[execute_case(n,i) for n in SIZES for i in range(CASES_PER_SIZE)];after=frozen()
 if after!=locked:raise RuntimeError('source lock mismatch after worker')
 return {'worker':index,'pid':os.getpid(),'sources_before':before,'sources_after':after,'rows':rows}
def main():
 if sys.argv[1:]==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite lock or capture')
  LOCK.write_text(json.dumps({'schema':'ThoughtexperimentEffectTraceCounterfactualV1Lock','sources':frozen(),'workers':3,'sizes':SIZES,'cases_per_size':CASES_PER_SIZE,'snapshot_backend':'shared_graph_pages','progress_budget':1},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if len(sys.argv)==3 and sys.argv[1]=='--worker':print(json.dumps(worker(int(sys.argv[2])),separators=(',',':'),sort_keys=True));return 0
 if sys.argv[1:]!=['--run']:raise SystemExit('usage: --lock | --run | --worker N')
 if frozen()!=json.loads(LOCK.read_text())['sources']:raise SystemExit('source lock mismatch before capture')
 env=dict(os.environ);env['PYTHONPATH']=os.pathsep.join((str(ROOT/'runners/dsl/python'),str(ROOT)));workers=[]
 for i in range(3):
  p=subprocess.run([sys.executable,str(RUNNER),'--worker',str(i)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=600)
  if p.returncode:raise RuntimeError(f'worker {i}: {p.stderr[-2000:]}')
  workers.append(json.loads(p.stdout.strip().splitlines()[-1]))
 if frozen()!=json.loads(LOCK.read_text())['sources']:raise SystemExit('source lock drift during capture')
 OUT.write_text(json.dumps({'schema':'ThoughtexperimentEffectTraceCounterfactualV1','lock_sha256':sha(LOCK),'host':platform.platform(),'workers':workers},indent=2,sort_keys=True)+'\n');print(OUT.relative_to(ROOT));return 0
if __name__=='__main__':raise SystemExit(main())
