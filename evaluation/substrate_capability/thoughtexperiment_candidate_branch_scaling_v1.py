#!/usr/bin/env python3
"""Source-locked sparse-graph scaling for thoughtexperiment candidate branches."""
import hashlib,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
RUNNER=Path(__file__).resolve(); ANALYZER=ROOT/'evaluation/substrate_capability/analyze_thoughtexperiment_candidate_branch_scaling_v1.py'
PROTOCOL=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_CANDIDATE_BRANCH_SCALING_V1_PREREG_20261005.md'
FIXTURE=ROOT/'evaluation/substrate_capability/thoughtexperiment_candidate_branch_scaling_v1_fixture_20261005.json'
SEED=ROOT/'seeds/self_change_reasoning.json'
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_candidate_branch_scaling_v1_lock_20261005.json'
OUT=ROOT/'evaluation/reports/thoughtexperiment_candidate_branch_scaling_v1_20261005.json'
SOURCES=('runners/dsl/Cargo.toml','runners/dsl/Cargo.lock','runners/dsl/src/graph.rs','runners/dsl/src/graph_rules.rs','runners/dsl/src/rewrite.rs','runners/dsl/src/substrate.rs','runners/dsl/src/py.rs','runners/dsl/python/substrate_rs/ext.py','runners/dsl/python/substrate_rs/_native.build.json')
PHASES=('fork','rule_install','task_input','closure','targeted_read')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def frozen():
 from substrate_rs import _native
 files=(RUNNER,ANALYZER,PROTOCOL,FIXTURE,SEED,*(ROOT/x for x in SOURCES));binary=Path(_native.__file__).resolve()
 return {'files':{str(p.relative_to(ROOT)):sha(p) for p in files},'native_binary':{'path':str(binary),'sha256':sha(binary)}}
def rss_kib():
 try:
  for line in Path('/proc/self/status').read_text().splitlines():
   if line.startswith('VmRSS:'):return int(line.split()[1])
 except OSError:pass
 return None
def rule(case,name,where):
 return {'name':name,'match':[['x','has_task','y'],['y','has_context','z']],
  'where':where,'effects':[['set_attr_if_different','y','task_pass',{'__term__':{'type':'Lit','value':True}}]]}
def branch_once(base,target_idx,candidate_where,signal):
 times={};t=time.perf_counter_ns();b=base.fork_shared_graph_pages_experiment();times['fork']=time.perf_counter_ns()-t
 inner=b._inner
 t=time.perf_counter_ns()
 if candidate_where is not None:
  if not inner.remove_rule(target_idx):raise RuntimeError('cannot remove active rule in branch')
  inner.add_rule(rule({},'scale_candidate',candidate_where))
 times['rule_install']=time.perf_counter_ns()-t
 t=time.perf_counter_ns();x=b.add_node('TaskInput',{'signal':signal});y=b.add_node('TaskOutput',{});z=b.add_node('TaskContext',{})
 inner.add_edge_unchecked(x,'has_task',y);inner.add_edge_unchecked(y,'has_context',z);times['task_input']=time.perf_counter_ns()-t
 t=time.perf_counter_ns();inner.run_rules_delta_report(30,False);times['closure']=time.perf_counter_ns()-t
 t=time.perf_counter_ns();value=bool(b.node(y)['attrs'].get('task_pass',False));times['targeted_read']=time.perf_counter_ns()-t
 return {'times_ns':times,'output':value}
def graph_digest(sub):
 g=sub.graph_to_dict();blob=json.dumps(g,sort_keys=True,separators=(',',':')).encode();return hashlib.sha256(blob).hexdigest(),len(g.get('nodes',[])),len(g.get('edges',[]))
def worker(worker_idx,n):
 from substrate.world_adapter import WorldAdapter
 lock=json.loads(LOCK.read_text());before=frozen()
 if before!=lock['sources']:raise RuntimeError('source mismatch before worker')
 fx=json.loads(FIXTURE.read_text());case=fx['case'];adapter=WorldAdapter(seeds=());adapter.inner.load_seed_manifest(json.loads(SEED.read_text()),adapter.agent)
 live=rule(case,'branch_scaling_target',case['live_where']);target=adapter.inner.add_rule(live)
 setup_start=time.perf_counter_ns();previous=None
 for i in range(n):
  node=adapter.s.add_node('ScaleDecoy',{'ordinal':i})
  if previous is not None:adapter.inner.add_edge_unchecked(previous,'decoy_next',node)
  previous=node
 graph_setup_ns=time.perf_counter_ns()-setup_start
 before_digest,nodes_before,edges_before=graph_digest(adapter.s);rule_before=adapter.inner.rule_metadata(target);rss_before=rss_kib();measure=[]
 for rep in range(fx['replications_per_arm']):
  order=('noop','candidate') if (rep+worker_idx)%2==0 else ('candidate','noop');rows={}
  for arm in order:
   rows[arm]=branch_once(adapter.s,target,None if arm=='noop' else case['candidate_where'],case['input']['signal'])
  measure.append({'rep':rep,'order':list(order),'noop':rows['noop'],'candidate':rows['candidate']})
 after_digest,nodes_after,edges_after=graph_digest(adapter.s);rule_after=adapter.inner.rule_metadata(target);rss_after=rss_kib();after=frozen()
 if after!=lock['sources']:raise RuntimeError('source drift during worker')
 return {'worker':worker_idx,'pid':os.getpid(),'decoy_nodes':n,'graph_setup_ns':graph_setup_ns,'nodes':nodes_before,'edges':edges_before,
  'rss_before_kib':rss_before,'rss_after_kib':rss_after,'primary_digest_before':before_digest,'primary_digest_after':after_digest,'primary_rule_before':rule_before,'primary_rule_after':rule_after,
  'nodes_after':nodes_after,'edges_after':edges_after,'measurements':measure,'sources_before':before,'sources_after':after}
def main():
 fx=json.loads(FIXTURE.read_text())
 if sys.argv[1:]==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite lock/capture')
  LOCK.write_text(json.dumps({'schema':'ThoughtexperimentCandidateBranchScalingV1Lock','sources':frozen(),'workers_per_size':3,'sizes':fx['node_counts'],'replications_per_arm':fx['replications_per_arm']},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if len(sys.argv)==4 and sys.argv[1]=='--worker':
  i,n=int(sys.argv[2]),int(sys.argv[3]);print(json.dumps(worker(i,n),sort_keys=True,separators=(',',':')));return 0
 if sys.argv[1:]!=['--run']:raise SystemExit('usage --lock|--run|--worker WORKER SIZE')
 lock=json.loads(LOCK.read_text())
 if frozen()!=lock['sources']:raise SystemExit('source lock mismatch')
 env=dict(os.environ);env['PYTHONPATH']=os.pathsep.join((str(ROOT/'runners/dsl/python'),str(ROOT)));rows=[]
 for size in lock['sizes']:
  for i in range(lock['workers_per_size']):
   p=subprocess.run([sys.executable,str(RUNNER),'--worker',str(i),str(size)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=600)
   if p.returncode:raise RuntimeError(f'worker={i} size={size}: {p.stderr[-3000:]}')
   rows.append(json.loads(p.stdout.strip().splitlines()[-1]))
 if frozen()!=lock['sources']:raise SystemExit('source drift during capture')
 OUT.write_text(json.dumps({'schema':'ThoughtexperimentCandidateBranchScalingV1','lock_sha256':sha(LOCK),'host':platform.platform(),'workers':rows},indent=2,sort_keys=True)+'\n');print(OUT.relative_to(ROOT));return 0
if __name__=='__main__':raise SystemExit(main())
