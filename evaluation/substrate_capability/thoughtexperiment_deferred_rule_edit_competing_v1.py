#!/usr/bin/env python3
"""Source-locked multi-writer and ambiguity gate for deferred SetRuleClause."""
import hashlib,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
RUNNER=Path(__file__).resolve();ANALYZER=ROOT/'evaluation/substrate_capability/analyze_thoughtexperiment_deferred_rule_edit_competing_v1.py'
PROTOCOL=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_DEFERRED_RULE_EDIT_COMPETING_V1_PREREG_20261005.md'
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_deferred_rule_edit_competing_v1_lock_20261005.json';OUT=ROOT/'evaluation/reports/thoughtexperiment_deferred_rule_edit_competing_v1_20261005.json'
SOURCES=('runners/dsl/Cargo.toml','runners/dsl/Cargo.lock','runners/dsl/src/graph.rs','runners/dsl/src/rewrite.rs','runners/dsl/src/substrate.rs','runners/dsl/src/py.rs','runners/dsl/python/substrate_rs/ext.py','runners/dsl/python/substrate_rs/_native.build.json')
SCENARIOS=('competing','duplicate','ambiguous_target')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dig(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def frozen():
 from substrate_rs import _native
 fs=(RUNNER,ANALYZER,PROTOCOL,*(ROOT/x for x in SOURCES));b=Path(_native.__file__).resolve()
 return {'files':{str(p.relative_to(ROOT)):sha(p) for p in fs},'native_binary':{'path':str(b),'sha256':sha(b)}}
def fixture(scenario):
 from substrate_rs import Substrate
 s=Substrate();t=s._inner.add_rule({'name':'target_rule','match':[['x','probe_link','y']],'where':{'type':'Lit','value':True},'effects':[['set_attr_if_different','x','fired',True]]});target=s._inner.rule_metadata(t)
 if scenario=='ambiguous_target':s._inner.add_rule({'name':'target_rule','match':[['x','never','y']],'effects':[]})
 a=s.add_node('Trigger',{});b=s.add_node('Trigger',{});s.add_edge_unchecked(a,'trigger_a',b);s.add_edge_unchecked(a,'trigger_b',b)
 values=(True,False) if scenario=='competing' else (False,False)
 producers=[]
 for name,edge,value in zip(('writer_a','writer_b'),('trigger_a','trigger_b'),values):
  rule={'name':name,'match':[['x',edge,'y']],'effects':[['set_rule_clause','target_rule','where',{'type':'Lit','value':value}],['del_edge','x',edge,'y']]}
  s._inner.add_rule(rule);producers.append(rule)
 pre=s._inner.graph_to_dict();snap=s._snapshot_with_backend('shared_graph_pages')
 return s,snap,pre,target,producers
def marker(branch):
 p=branch.add_node('Probe',{});q=branch.add_node('ProbeTarget',{});branch.add_edge_unchecked(p,'probe_link',q);branch._inner.run_rules_report(20,False)
 n=next(n for n in branch._inner.graph_to_dict()['nodes'] if n['id']==p.value);return bool(n.get('attrs',{}).get('fired'))
def omission(snap,producer):
 b=snap.fork();variant={**producer,'effects':[producer['effects'][1]]}
 if not b._inner.replace_active_rule_by_name(producer['name'],variant):raise RuntimeError('producer replacement failed')
 c=b._inner.run_rules_report(20,False);m=marker(b);return {'omitted_writer':producer['name'],'marker':m,'closure_status':c['status']}
def execute(scenario,rep):
 s,snap,pre,target,producers=fixture(scenario);base=dig(pre);rev=tuple(s._inner.experiment_graph_rule_revision());w=snap.fork();t0=time.perf_counter_ns()
 report=w._inner.run_rules_effect_target_delta_report(20,False);events=[e for e in report['rule_write_events'] if e.get('deferred') and e['rule_name'] in ('writer_a','writer_b')]
 origins=[{'writer':e['rule_name'],'effect_index':o['effect_index']} for e in events for o in e.get('deferred_effect_origins',[])]
 changes=[{'writer':e['rule_name'],**c} for e in events for c in e.get('deferred_rule_changes',[])]
 branches=[omission(snap,p) for p in producers];elapsed=time.perf_counter_ns()-t0
 after=s._inner.graph_to_dict();after_rev=tuple(s._inner.experiment_graph_rule_revision())
 target_meta=s._inner.rule_metadata(target['rule_idx'])
 return {'scenario':scenario,'replicate':rep,'events':[{'writer':e['rule_name'],'progressed':e['progressed'],'origins':e.get('deferred_effect_origins',[]),'changes':e.get('deferred_rule_changes',[])} for e in events],'origins':origins,'changes':changes,'branches':branches,'initial_target_revision':target['revision'],'target_revision_after':target_meta['revision'],'target_uid':target['rule_uid'],'wall_ns':elapsed,'status':report['status'],'progress_steps':report['progress_steps'],'primary_unchanged':dig(after)==base and rev==after_rev}
def worker(i):
 lock=json.loads(LOCK.read_text())['sources'];before=frozen()
 if before!=lock:raise RuntimeError('source lock mismatch')
 rows=[execute(sc,100+i) for sc in SCENARIOS];after=frozen()
 if after!=lock:raise RuntimeError('source drift')
 return {'worker':i,'pid':os.getpid(),'sources_before':before,'sources_after':after,'rows':rows}
def isolated(sc,rep):
 lock=json.loads(LOCK.read_text())['sources'];before=frozen()
 if before!=lock:raise RuntimeError('source lock mismatch')
 r=execute(sc,rep);after=frozen()
 if after!=lock:raise RuntimeError('source drift')
 return {'pid':os.getpid(),'sources_before':before,'sources_after':after,**r}
def main():
 if sys.argv[1:]==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing overwrite')
  LOCK.write_text(json.dumps({'schema':'DeferredRuleEditCompetingV1Lock','sources':frozen(),'workers':3,'isolated_replicates_per_scenario':3,'scenarios':SCENARIOS},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if len(sys.argv)==3 and sys.argv[1]=='--worker':print(json.dumps(worker(int(sys.argv[2])),sort_keys=True,separators=(',',':')));return 0
 if len(sys.argv)==4 and sys.argv[1]=='--isolated':print(json.dumps(isolated(sys.argv[2],int(sys.argv[3])),sort_keys=True,separators=(',',':')));return 0
 if sys.argv[1:]!=['--run']:raise SystemExit('usage --lock|--run|--worker N|--isolated scenario replicate')
 if frozen()!=json.loads(LOCK.read_text())['sources']:raise SystemExit('source lock mismatch')
 env=dict(os.environ);env['PYTHONPATH']=os.pathsep.join((str(ROOT/'runners/dsl/python'),str(ROOT)));iso=[];workers=[]
 for sc in SCENARIOS:
  for rep in range(3):
   p=subprocess.run([sys.executable,str(RUNNER),'--isolated',sc,str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=120)
   if p.returncode:raise RuntimeError(f'{sc}/{rep}: {p.stderr[-2000:]}')
   iso.append(json.loads(p.stdout.strip().splitlines()[-1]))
 for i in range(3):
  p=subprocess.run([sys.executable,str(RUNNER),'--worker',str(i)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=180)
  if p.returncode:raise RuntimeError(f'worker/{i}: {p.stderr[-2000:]}')
  workers.append(json.loads(p.stdout.strip().splitlines()[-1]))
 if frozen()!=json.loads(LOCK.read_text())['sources']:raise SystemExit('source drift during capture')
 OUT.write_text(json.dumps({'schema':'DeferredRuleEditCompetingV1','lock_sha256':sha(LOCK),'host':platform.platform(),'workers':workers,'isolated':iso},indent=2,sort_keys=True)+'\n');print(OUT.relative_to(ROOT));return 0
if __name__=='__main__':raise SystemExit(main())
