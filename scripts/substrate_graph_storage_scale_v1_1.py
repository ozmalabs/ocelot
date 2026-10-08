#!/usr/bin/env python3
"""Source-locked sparse native typed-graph storage construction panel."""
from __future__ import annotations
import hashlib,json,os,platform,random,resource,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
from substrate_rs import Substrate,_native
from domains.engine_provenance import assert_measuring_engine,build_is_stale
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_GRAPH_STORAGE_SCALE_V1_PREREG_20260928.md'
AMENDMENT=ROOT/'docs/research/engine_substrate/SUBSTRATE_GRAPH_STORAGE_SCALE_V1_1_AMENDMENT_20260928.md'
LOCK=ROOT/'evaluation/substrate_capability/graph_storage_scale_v1_1_lock_20260928.json'
RAW=ROOT/'evaluation/reports/substrate_graph_storage_scale_v1_1_20260928.json'
SUMMARY=ROOT/'evaluation/reports/substrate_graph_storage_scale_v1_1_summary_20260928.json'
SOURCES=('runners/dsl/src/graph.rs','runners/dsl/src/substrate.rs','runners/dsl/src/py.rs','runners/dsl/python/substrate_rs/_native.build.json','runners/dsl/python/substrate_rs/__init__.py','domains/engine_provenance.py','scripts/substrate_graph_storage_scale_v1_1.py','scripts/analyze_substrate_graph_storage_scale_v1_1.py','docs/research/engine_substrate/SUBSTRATE_GRAPH_STORAGE_SCALE_V1_PREREG_20260928.md','docs/research/engine_substrate/SUBSTRATE_GRAPH_STORAGE_SCALE_V1_1_AMENDMENT_20260928.md','docs/research/engine_substrate/SUBSTRATE_GRAPH_STORAGE_SCALE_V1_1_CAPTURE_CORRECTION_20260928.md')
SIZES=(10_000,100_000,1_000_000,10_000_000);REPS=(0,1)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def fingerprint():
 native=Path(_native.__file__).resolve()
 return {'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'files':{p:sha(ROOT/p) for p in SOURCES},'native_path':str(native),'native_sha256':sha(native),'native_build_stale':build_is_stale(str(ROOT))}
def current_rss_bytes():
 try:
  for line in Path('/proc/self/status').read_text().splitlines():
   if line.startswith('VmRSS:'):return int(line.split()[1])*1024
 except OSError:pass
 return None
def peak_rss_bytes():
 v=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
 return int(v*(1024 if sys.platform.startswith('linux') else 1))
def node_id(n):return int(n.value if hasattr(n,'value') else n)
def worker(n,rep):
 before=fingerprint();rss0=current_rss_bytes();s=Substrate();inner=s._inner
 t0=time.perf_counter_ns();c0=time.process_time_ns();first=prev=mid=last=None
 for i in range(n):
  cur=inner.add_node('StorageProbe',{})
  if first is None:first=cur
  if i==n//2:mid=cur
  if i==n-1:last=cur
  prev=cur
 node_wall=time.perf_counter_ns()-t0;node_cpu=time.process_time_ns()-c0;rss_nodes=current_rss_bytes()
 t0=time.perf_counter_ns();c0=time.process_time_ns();prior=None;sample_edges=[]
 for i in range(n):
  # Node IDs are consecutive in this fresh graph; keep only sampled IDs.
  cur=_native.NodeID(i)
  if prior is not None:
   inner.add_edge_unchecked(prior,'next',cur,{})
   if i in (1,n//2,n-1):sample_edges.append((i-1,i))
  prior=cur
 edge_wall=time.perf_counter_ns()-t0;edge_cpu=time.process_time_ns()-c0;rss_edges=current_rss_bytes()
 count_nodes=inner.node_count();count_edges=inner.edge_count();read_checks=[]
 for label,nid in (('first',first),('middle',mid),('last',last)):
  got=inner.node(nid);read_checks.append({'label':label,'id':node_id(nid),'exists':got is not None,'type':got.get('type') if isinstance(got,dict) else None})
 edge_checks=[]
 for left,right in sample_edges:
  got=[node_id(x) for x in inner.neighbours(_native.NodeID(left),'next')]
  edge_checks.append({'src':left,'expected_tgt':right,'actual_tgts':got,'pass':got==[right]})
 after=fingerprint()
 return {'n':n,'replicate':rep,'pid':os.getpid(),'before':before,'after':after,'rss_before_bytes':rss0,'rss_after_nodes_bytes':rss_nodes,'rss_after_edges_bytes':rss_edges,'peak_rss_bytes':peak_rss_bytes(),'node_build_wall_ns':node_wall,'node_build_cpu_ns':node_cpu,'edge_build_wall_ns':edge_wall,'edge_build_cpu_ns':edge_cpu,'total_build_wall_ns':node_wall+edge_wall,'total_build_cpu_ns':node_cpu+edge_cpu,'node_count':count_nodes,'edge_count':count_edges,'sampled_node_reads':read_checks,'sampled_edge_reads':edge_checks,'sampled_checks_pass':len(read_checks)==3 and all(r['exists'] and r['type']=='StorageProbe' for r in read_checks) and len(edge_checks)==3 and all(r['pass'] for r in edge_checks),'environment':{'python':sys.version,'platform':platform.platform()}}
def cells():return [(n,r) for n in SIZES for r in REPS]
def main():
 assert_measuring_engine()
 if sys.argv[1:]==['--lock']:
  fp=fingerprint()
  if fp['native_build_stale']:raise SystemExit('native build is stale')
  LOCK.parent.mkdir(parents=True,exist_ok=True);LOCK.write_text(json.dumps(fp,indent=2,sort_keys=True)+'\n');print(LOCK);return
 if len(sys.argv)==4 and sys.argv[1]=='--worker':
  print(json.dumps(worker(int(sys.argv[2]),int(sys.argv[3])),sort_keys=True));return
 locked=fingerprint()
 if locked['native_build_stale'] or not LOCK.exists() or json.loads(LOCK.read_text())!=locked:raise SystemExit('missing/stale source lock or native build')
 jobs=cells();random.Random(20260928).shuffle(jobs);runs=[];started=datetime.now(timezone.utc).isoformat();env=dict(os.environ);env['PYTHONPATH']=os.pathsep.join((str(ROOT),str(ROOT/'runners/dsl/python'),env.get('PYTHONPATH','')))
 for n,rep in jobs:
  cp=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker',str(n),str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,check=True)
  row=json.loads(cp.stdout);row['worker_returncode']=cp.returncode;row['worker_stderr']=cp.stderr;runs.append(row)
 after=fingerprint();checks={'eight_workers':len(runs)==8,'two_workers_per_size':all(sum(x['n']==n for x in runs)==2 for n in SIZES),'unique_pids':len({x['pid'] for x in runs})==8,'stable_parent_and_workers':after==locked and all(x['before']==locked==x['after'] for x in runs),'correct_graph_counts':all(x['node_count']==x['n'] and x['edge_count']==x['n']-1 for x in runs),'sampled_graph_checks':all(x['sampled_checks_pass'] for x in runs),'positive_timings':all(min(x[k] for k in ('node_build_wall_ns','node_build_cpu_ns','edge_build_wall_ns','edge_build_cpu_ns'))>0 for x in runs),'rss_nondecreasing':all(x['rss_before_bytes']<=x['rss_after_nodes_bytes']<=x['rss_after_edges_bytes'] for x in runs)}
 RAW.write_text(json.dumps({'schema_version':1,'run_id':'substrate-graph-storage-scale-v1.1-20260928','started_utc':started,'locked_inputs':locked,'post_run_inputs':after,'schedule':jobs,'checks':checks,'all_checks_pass':all(checks.values()),'runs':runs},indent=2,sort_keys=True)+'\n')
 summary={'schema_version':1,'raw_path':str(RAW.relative_to(ROOT)),'locked_inputs':locked,'post_run_inputs':after,'checks':checks,'all_checks_pass':all(checks.values())};SUMMARY.write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n');print(json.dumps(summary,indent=2,sort_keys=True))
 if not all(checks.values()):raise SystemExit('graph storage scale gates failed')
if __name__=='__main__':main()
