#!/usr/bin/env python3
"""Source-locked four-arm diagnosis on a production-derived discourse rule."""
from __future__ import annotations
import hashlib,json,os,platform,random,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
RUNNER=Path(__file__).resolve();ANALYZER=ROOT/'evaluation/substrate_capability/analyze_thoughtexperiment_production_rule_diagnosis_v1.py'
PROTOCOL=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_PRODUCTION_RULE_DIAGNOSIS_V1_PREREG_20261005.md'
SEED=ROOT/'seeds/conversation_discourse_state.json'
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_production_rule_diagnosis_v1_lock_20261005.json'
OUT=ROOT/'evaluation/reports/thoughtexperiment_production_rule_diagnosis_v1_20261005.json'
SOURCES=('runners/dsl/Cargo.toml','runners/dsl/Cargo.lock','runners/dsl/src/graph.rs','runners/dsl/src/rewrite.rs','runners/dsl/src/substrate.rs','runners/dsl/src/py.rs','runners/dsl/python/substrate_rs/ext.py','runners/dsl/python/substrate_rs/_native.build.json')
ARMS=('endpoint_blind','endpoint_rematch','target_trace','value_trace')
FAULT='fault_marker'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def frozen():
 from substrate_rs import _native
 files=(RUNNER,ANALYZER,PROTOCOL,SEED,*(ROOT/x for x in SOURCES));binary=Path(_native.__file__).resolve()
 return {'files':{str(p.relative_to(ROOT)):sha(p) for p in files},'native_binary':{'path':str(binary),'sha256':sha(binary)}}
def fixture(case_id):
 from substrate_rs import Substrate
 seed=json.loads(SEED.read_text());rule=next(r for r in seed['rules'] if r['name']=='discourse_goal_resolve')
 rule=json.loads(json.dumps(rule));rule['effects'][2][3]=FAULT
 s=Substrate();state=s.add_node('DiscourseState',{});origin=s.add_node('Event',{'event_index':1});goal=s.add_node('Goal',{'lifecycle_status':'executing'});event=s.add_node('Event',{'kind':'action_result','event_index':2})
 for src,typ,tgt in ((state,'has_active_goal',goal),(goal,'originated_in',origin),(state,'has_event',event),(event,'for_goal',goal)):s.add_edge_unchecked(src,typ,tgt)
 s._inner.add_rule(rule);snapshot=s._snapshot_with_backend('shared_graph_pages')
 return s,snapshot,rule,{'state':state.value,'origin':origin.value,'goal':goal.value,'event':event.value,'fault':FAULT}
def candidate_match(graph,rule,target_node):
 es=[(int(e['src']),str(e['type']),int(e['tgt'])) for e in graph['edges']]
 bindings=[{}]
 for src_var,edge_type,tgt_var in rule['match']:
  next_bindings=[]
  for old in bindings:
   for src,typ,tgt in es:
    if typ!=edge_type:continue
    b=dict(old);ok=True
    for var,nid in ((src_var,src),(tgt_var,tgt)):
     if var in b and b[var]!=nid:ok=False;break
     b[var]=nid
    if ok:next_bindings.append(b)
  bindings=next_bindings
  if not bindings:break
 nd={int(n['id']):n for n in graph['nodes']};valid=[]
 for b in bindings:
  if b.get('goal')!=target_node:continue
  ga=nd.get(b.get('goal'),{}).get('attrs',{});ea=nd.get(b.get('event'),{}).get('attrs',{});oa=nd.get(b.get('origin'),{}).get('attrs',{})
  if ga.get('lifecycle_status')!='executing' or ea.get('kind')!='action_result' or ea.get('event_index',0)<=oa.get('event_index',0):continue
  if sum(1 for a,t,z in es if a==b['event'] and t=='for_goal')!=1:continue
  valid.append(b)
 candidates=[]
 if len(valid)==1:
  b=valid[0]
  for i,effect in enumerate(rule['effects']):
   if any(isinstance(x,str) and x in b and b[x]==target_node for x in effect[1:]):candidates.append(i)
 return candidates,len(valid)
def omission(snapshot,rule,index,goal,fault,oracle_event_id):
 branch=snapshot.fork();variant={**rule,'effects':[e for i,e in enumerate(rule['effects']) if i!=index]}
 if not branch._inner.replace_active_rule_by_name('discourse_goal_resolve',variant):raise RuntimeError('rule replacement refused')
 report=branch._inner.run_rules_report(10,False);graph=branch._inner.graph_to_dict();node=next(n for n in graph['nodes'] if int(n['id'])==goal)
 attrs=node.get('attrs',{});edge_set={(int(e['src']),str(e['type']),int(e['tgt'])) for e in graph['edges']}
 healthy=(attrs.get('outcome')!=fault and attrs.get('lifecycle_status')=='resolved' and attrs.get('status')=='resolved' and attrs.get('last_transition_event',{}).get('__nid__')==oracle_event_id)
 return attrs.get('outcome')!=fault,healthy,report,graph
def execute(arm,rep):
 s,snap,rule,oracle=fixture(rep);primary_before=s._inner.graph_to_dict();primary_digest=hashlib.sha256(json.dumps(primary_before,sort_keys=True,separators=(',',':')).encode()).hexdigest();rev_before=tuple(s._inner.experiment_graph_rule_revision())
 work=snap.fork();t0=time.perf_counter_ns();c0=time.process_time_ns()
 if arm=='endpoint_blind':report=work._inner.run_rules_delta_report(10,False);candidates=list(range(len(rule['effects'])));rematch_count=None
 elif arm=='endpoint_rematch':
  report=work._inner.run_rules_delta_report(10,False);candidates,rematch_count=candidate_match(primary_before,rule,oracle['goal'])
 elif arm=='target_trace':
  report=work._inner.run_rules_effect_target_delta_report(10,False);candidates=[];rematch_count=None
  for ev in report['rule_write_events']:
   if ev['rule_name']!='discourse_goal_resolve' or not ev['progressed']:continue
   for e in ev['effect_snapshots']:
    hit=oracle['goal'] in e['node_ids'] or any(oracle['goal'] in edge for edge in e['edges'])
    if hit:candidates.append(int(e['effect_index']))
 elif arm=='value_trace':
  report=work._inner.run_rules_effect_delta_report(10,False);candidates=[];rematch_count=None
  for ev in report['rule_write_events']:
   if ev['rule_name']!='discourse_goal_resolve' or not ev['progressed']:continue
   for e in ev['effect_snapshots']:
    if any(v['node_id']==oracle['goal'] and v['after'] is not None and v['after']['attrs'].get('outcome')==FAULT and (v['before'] is None or v['before']['attrs'].get('outcome')!=FAULT) for v in e['node_values']):candidates.append(int(e['effect_index']))
 found=None;attempts=0;outcomes=[];cured_digest=None
 for i in candidates:
  attempts+=1;cured,healthy,branch_report,branch_graph=omission(snap,rule,i,oracle['goal'],FAULT,oracle['event']);digest=hashlib.sha256(json.dumps(branch_graph,sort_keys=True,separators=(',',':')).encode()).hexdigest()
  outcomes.append({'effect_index':i,'cured':cured,'healthy_survivors':healthy,'status':branch_report['status']})
  if cured:found=i;cured_digest=digest;break
 elapsed=time.perf_counter_ns()-t0;cpu=time.process_time_ns()-c0
 primary_after=s._inner.graph_to_dict();rev_after=tuple(s._inner.experiment_graph_rule_revision())
 return {'arm':arm,'replicate':rep,'candidates':candidates,'rematch_matches':rematch_count,'attempts':attempts,'found':found,'outcomes':outcomes,'cured_graph_digest':cured_digest,'wall_ns':elapsed,'cpu_ns':cpu,'report_event_count':len(report['rule_write_events']),'report_json_bytes':len(json.dumps(report['rule_write_events'],sort_keys=True,separators=(',',':')).encode()),'effect_snapshot_objects':report.get('rule_write_effect_snapshot_objects',0),'effect_value_bytes':report.get('rule_write_effect_snapshot_bytes',0),'effect_truncated':report.get('rule_write_effect_snapshots_truncated',0),'status':report['status'],'progress_steps':report['progress_steps'],'fault_effect_index':2,'primary_unchanged':hashlib.sha256(json.dumps(primary_after,sort_keys=True,separators=(',',':')).encode()).hexdigest()==primary_digest and rev_before==rev_after,'primary_digest':primary_digest,'revision_before':rev_before,'revision_after':rev_after}
def worker(index):
 locked=json.loads(LOCK.read_text())['sources'];before=frozen()
 if before!=locked:raise RuntimeError('source lock mismatch before worker')
 arms=list(ARMS);random.Random(1000+index).shuffle(arms);rows=[execute(a,100+index) for a in arms];after=frozen()
 if after!=locked:raise RuntimeError('source lock mismatch after worker')
 return {'worker':index,'pid':os.getpid(),'sources_before':before,'sources_after':after,'rows':rows}
def isolated(arm,rep):
 locked=json.loads(LOCK.read_text())['sources'];before=frozen()
 if before!=locked:raise RuntimeError('source lock mismatch before isolated run')
 row=execute(arm,rep);after=frozen()
 if after!=locked:raise RuntimeError('source lock mismatch after isolated run')
 return {'pid':os.getpid(),'sources_before':before,'sources_after':after,**row}
def main():
 if sys.argv[1:]==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite lock/capture')
  LOCK.write_text(json.dumps({'schema':'ThoughtexperimentProductionRuleDiagnosisV1Lock','sources':frozen(),'workers':3,'isolated_replicates_per_arm':3,'arms':ARMS,'snapshot_backend':'shared_graph_pages'},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if len(sys.argv)==3 and sys.argv[1]=='--worker':print(json.dumps(worker(int(sys.argv[2])),sort_keys=True,separators=(',',':')));return 0
 if len(sys.argv)==4 and sys.argv[1]=='--isolated':print(json.dumps(isolated(sys.argv[2],int(sys.argv[3])),sort_keys=True,separators=(',',':')));return 0
 if sys.argv[1:]!=['--run']:raise SystemExit('usage: --lock | --run | --worker N')
 if frozen()!=json.loads(LOCK.read_text())['sources']:raise SystemExit('source lock mismatch before capture')
 env=dict(os.environ);env['PYTHONPATH']=os.pathsep.join((str(ROOT/'runners/dsl/python'),str(ROOT)));isolated_rows=[];workers=[]
 for arm in ARMS:
  for rep in range(3):
   p=subprocess.run([sys.executable,str(RUNNER),'--isolated',arm,str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=120)
   if p.returncode:raise RuntimeError(f'{arm}/{rep}: {p.stderr[-2500:]}')
   isolated_rows.append(json.loads(p.stdout.strip().splitlines()[-1]))
 for i in range(3):
  p=subprocess.run([sys.executable,str(RUNNER),'--worker',str(i)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=120)
  if p.returncode:raise RuntimeError(f'worker/{i}: {p.stderr[-2500:]}')
  workers.append(json.loads(p.stdout.strip().splitlines()[-1]))
 if frozen()!=json.loads(LOCK.read_text())['sources']:raise SystemExit('source lock drift during capture')
 OUT.write_text(json.dumps({'schema':'ThoughtexperimentProductionRuleDiagnosisV1','lock_sha256':sha(LOCK),'host':platform.platform(),'workers':workers,'isolated':isolated_rows},indent=2,sort_keys=True)+'\n');print(OUT.relative_to(ROOT));return 0
if __name__=='__main__':raise SystemExit(main())
