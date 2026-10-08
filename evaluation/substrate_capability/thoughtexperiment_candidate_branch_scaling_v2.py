#!/usr/bin/env python3
"""Factorial aperture/separator/background scaling for CoW rule rehearsal."""
import hashlib,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
RUNNER=Path(__file__).resolve();ANALYZER=ROOT/'evaluation/substrate_capability/analyze_thoughtexperiment_candidate_branch_scaling_v2.py';PROTOCOL=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_CANDIDATE_BRANCH_SCALING_V2_PREREG_20261005.md';FIXTURE=ROOT/'evaluation/substrate_capability/thoughtexperiment_candidate_branch_scaling_v2_fixture_20261005.json';SEED=ROOT/'seeds/self_change_reasoning.json';LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_candidate_branch_scaling_v2_lock_20261005.json';OUT=ROOT/'evaluation/reports/thoughtexperiment_candidate_branch_scaling_v2_20261005.json';SOURCES=('runners/dsl/Cargo.toml','runners/dsl/Cargo.lock','runners/dsl/src/graph.rs','runners/dsl/src/graph_rules.rs','runners/dsl/src/rewrite.rs','runners/dsl/src/substrate.rs','runners/dsl/src/py.rs','runners/dsl/python/substrate_rs/ext.py','runners/dsl/python/substrate_rs/_native.build.json');PHASES=('fork','rule_install','task_frame','separator_edges','closure','targeted_read')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def frozen():
 from substrate_rs import _native
 paths=(RUNNER,ANALYZER,PROTOCOL,FIXTURE,SEED,*(ROOT/x for x in SOURCES));binary=Path(_native.__file__).resolve();return {'files':{str(p.relative_to(ROOT)):sha(p) for p in paths},'native_binary':{'path':str(binary),'sha256':sha(binary)}}
def rss_kib():
 try:
  for line in Path('/proc/self/status').read_text().splitlines():
   if line.startswith('VmRSS:'):return int(line.split()[1])
 except OSError:pass
 return None
def term_attr(node,key):return {'type':'Attr','node':{'type':'Var','name':node},'key':key}
def rule(name,k,threshold):
 match=[['x','has_task','y'],['y','has_context','q0']]
 match.extend([[f'q{i}','task_link',f'q{i+1}'] for i in range(k-1)])
 where={'type':'And','items':[{'type':'Gte','a':term_attr('x','signal'),'b':{'type':'Lit','value':threshold}},
  {'type':'Exists','source':{'type':'Neighbours','node':{'type':'Var','name':'q0'},'edge_type':'boundary_link'},'var_name':'w',
   'predicate':{'type':'Eq','a':term_attr('w','role'),'b':{'type':'Lit','value':'goal'}}}]}
 return {'name':name,'match':match,'where':where,'effects':[['set_attr_if_different','y','task_pass',{'__term__':{'type':'Lit','value':True}}]]}
def graph_digest(sub):
 g=sub.graph_to_dict();raw=json.dumps(g,sort_keys=True,separators=(',',':')).encode();return hashlib.sha256(raw).hexdigest(),len(g.get('nodes',[])),len(g.get('edges',[]))
def make_background(adapter,n,topology):
 ids=[];t=time.perf_counter_ns()
 for i in range(n):ids.append(adapter.s.add_node('ScaleDecoy',{'ordinal':i,'role':'decoy'}))
 if topology=='path':
  edges=[(ids[i-1],ids[i]) for i in range(1,n)]
 elif topology=='binary_tree':
  edges=[(ids[(i-1)//2],ids[i]) for i in range(1,n)]
 else:raise ValueError(topology)
 for a,b in edges:adapter.inner.add_edge_unchecked(a,'decoy_link',b)
 return ids,time.perf_counter_ns()-t
def branch_timed(base,target_idx,cell,arm,audit=False):
 t=time.perf_counter_ns();b=base.fork_shared_graph_pages_experiment();fork_ns=time.perf_counter_ns()-t
 # Run branch body against this already-created child to keep fork separate.
 result=execute_child(b,target_idx,cell,arm,audit=audit);result['times_ns']['fork']=fork_ns;return result
def execute_child(b,target_idx,cell,arm,audit=False):
 case=cell['case'];k=cell['task_aperture_nodes'];times={};t=time.perf_counter_ns()
 rule_idx=target_idx
 if arm=='candidate':
  if not b._inner.remove_rule(target_idx):raise RuntimeError('branch could not remove target rule')
  rule_idx=b._inner.add_rule(rule('scaling_candidate',k,1))
 times['rule_install']=time.perf_counter_ns()-t
 t=time.perf_counter_ns();x=b.add_node('TaskInput',{'signal':case['signal']});y=b.add_node('TaskOutput',{});frame=[]
 for i in range(k):frame.append(b.add_node('TaskFrameNode',{'ordinal':i}))
 b._inner.add_edge_unchecked(x,'has_task',y);b._inner.add_edge_unchecked(y,'has_context',frame[0])
 for i in range(k-1):b._inner.add_edge_unchecked(frame[i],'task_link',frame[i+1])
 times['task_frame']=time.perf_counter_ns()-t
 t=time.perf_counter_ns()
 for node in cell['_boundary_decoys']:b._inner.add_edge_unchecked(frame[0],'boundary_link',node)
 goal=b.add_node('ScaleDecoy',{'role':'goal','ordinal':-1});b._inner.add_edge_unchecked(frame[0],'boundary_link',goal);times['separator_edges']=time.perf_counter_ns()-t
 Native=None
 if audit:
  from substrate_rs import _native
  Native=_native.Substrate;Native.scale_audit_set_per_rule_enabled(False);Native.scale_audit_set_enabled(False);Native.scale_audit_reset();Native.scale_audit_per_rule_reset();Native.scale_audit_set_per_rule_enabled(True);Native.scale_audit_set_enabled(True)
 t=time.perf_counter_ns()
 try:b._inner.run_rules_delta_report(30,False)
 finally:
  times['closure']=time.perf_counter_ns()-t
  if audit:Native.scale_audit_set_per_rule_enabled(False);Native.scale_audit_set_enabled(False)
 audit_metrics={};audit_rows=[];audit_global={};audit_rule_meta=[]
 if audit:
  audit_rows=[list(row) for row in Native.scale_audit_per_rule_snapshot()]
  audit_global={str(name):int(value) for name,value in Native.scale_audit_snapshot()}
  audit_rule_meta=[list(row) for row in Native.scale_audit_rule_metadata_snapshot()]
  for idx,metric,value in Native.scale_audit_per_rule_snapshot():
   if int(idx)==int(rule_idx):audit_metrics[str(metric)]=int(value)
 t=time.perf_counter_ns();out=bool(b.node(y)['attrs'].get('task_pass',False));times['targeted_read']=time.perf_counter_ns()-t
 return {'output':out,'times_ns':times,'audit_metrics':audit_metrics if audit else None,'audit_rows':audit_rows if audit else None,'audit_global':audit_global if audit else None,'audit_rule_meta':audit_rule_meta if audit else None,'boundary_neighbor_count':len(b.neighbours(frame[0],'boundary_link'))}
def worker(wid,topology,n,k,boundary):
 from substrate.world_adapter import WorldAdapter
 lock=json.loads(LOCK.read_text());before=frozen()
 if before!=lock['sources']:raise RuntimeError('source lock mismatch')
 fx=json.loads(FIXTURE.read_text());adapter=WorldAdapter(seeds=());adapter.inner.load_seed_manifest(json.loads(SEED.read_text()),adapter.agent);target=adapter.inner.add_rule(rule('scaling_target',k,0))
 ids,setup_ns=make_background(adapter,n,topology);cell={'topology':topology,'background_nodes':n,'task_aperture_nodes':k,'separator_edges':boundary,'case':fx['case'],'_boundary_decoys':ids[:boundary-1]}
 before_graph,nodes,edges=graph_digest(adapter.s);rule_before=adapter.inner.rule_metadata(target);rss_before=rss_kib();measured=[]
 for rep in range(fx['replications_per_arm']):
  order=('noop','candidate') if (wid+rep)%2==0 else ('candidate','noop');arms={}
  for arm in order:arms[arm]=branch_timed(adapter.s,target,cell,arm)
  measured.append({'rep':rep,'order':list(order),'noop':arms['noop'],'candidate':arms['candidate']})
 audit_probe=branch_timed(adapter.s,target,cell,'noop',audit=True)
 after_graph,nodes_after,edges_after=graph_digest(adapter.s);rule_after=adapter.inner.rule_metadata(target);rss_after=rss_kib();after=frozen()
 if after!=lock['sources']:raise RuntimeError('source changed')
 return {'worker':wid,'pid':os.getpid(),'topology':topology,'background_nodes':n,'task_aperture_nodes':k,'separator_edges':boundary,'graph_setup_ns':setup_ns,'nodes':nodes,'edges':edges,'nodes_after':nodes_after,'edges_after':edges_after,'rss_before_kib':rss_before,'rss_after_kib':rss_after,'primary_graph_before':before_graph,'primary_graph_after':after_graph,'primary_rule_before':rule_before,'primary_rule_after':rule_after,'measurements':measured,'audit_probe':audit_probe,'sources_before':before,'sources_after':after}
def cells(fx):
 return [(t,n,k,b) for t in fx['topologies'] for n in fx['background_nodes'] for k in fx['task_aperture_nodes'] for b in fx['separator_edges']]
def main():
 fx=json.loads(FIXTURE.read_text())
 if sys.argv[1:]==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing overwrite')
  LOCK.write_text(json.dumps({'schema':'ThoughtexperimentCandidateBranchScalingV2Lock','sources':frozen(),'workers_per_cell':fx['workers_per_cell'],'replications_per_arm':fx['replications_per_arm'],'cells':[{'topology':t,'background_nodes':n,'task_aperture_nodes':k,'separator_edges':b} for t,n,k,b in cells(fx)]},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if len(sys.argv)==7 and sys.argv[1]=='--worker':
  print(json.dumps(worker(*[int(sys.argv[2]),sys.argv[3],int(sys.argv[4]),int(sys.argv[5]),int(sys.argv[6])]),sort_keys=True,separators=(',',':')));return 0
 if sys.argv[1:]!=['--run']:raise SystemExit('usage --lock|--run|--worker ID TOPOLOGY N K B')
 lock=json.loads(LOCK.read_text())
 if frozen()!=lock['sources']:raise SystemExit('source lock mismatch')
 env=dict(os.environ);env['PYTHONPATH']=os.pathsep.join((str(ROOT/'runners/dsl/python'),str(ROOT)));rows=[]
 for cell in lock['cells']:
  for wid in range(lock['workers_per_cell']):
   args=[sys.executable,str(RUNNER),'--worker',str(wid),cell['topology'],str(cell['background_nodes']),str(cell['task_aperture_nodes']),str(cell['separator_edges'])]
   p=subprocess.run(args,cwd=ROOT,env=env,text=True,capture_output=True,timeout=300)
   if p.returncode:raise RuntimeError(f"cell={cell} worker={wid}: {p.stderr[-3000:]}")
   rows.append(json.loads(p.stdout.strip().splitlines()[-1]))
 if frozen()!=lock['sources']:raise SystemExit('source drift')
 OUT.write_text(json.dumps({'schema':'ThoughtexperimentCandidateBranchScalingV2','lock_sha256':sha(LOCK),'host':platform.platform(),'workers':rows},indent=2,sort_keys=True)+'\n');print(OUT.relative_to(ROOT));return 0
if __name__=='__main__':raise SystemExit(main())
