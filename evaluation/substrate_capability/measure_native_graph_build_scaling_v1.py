#!/usr/bin/env python3
"""Measure native graph node/edge insertion throughput and resident memory."""
from __future__ import annotations
import hashlib,json,os,platform,random,resource,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'runners/dsl/python'))
RUNNER=Path(__file__).resolve()
PREREG=ROOT/'docs/research/engine_substrate/NATIVE_GRAPH_BUILD_SCALING_V1_PREREG_20261002.md'
LOCK=ROOT/'evaluation/substrate_capability/native_graph_build_scaling_v1_lock_20261002.json'
OUT=ROOT/'evaluation/reports/native_graph_build_scaling_v1_20261002.json'
NODE_COUNTS=(100000,1000000);EDGE_MULTIPLIERS=(0,1,2);REPLICATES=3;ORDER_SEED=61006
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def native_hash():
 from substrate_rs import _native
 return sha(Path(_native.__file__).resolve())
def frozen():return {'runner':sha(RUNNER),'preregistration':sha(PREREG),
 'native_binary':native_hash(),'python':sys.version,'platform':platform.platform()}
def rss():
 try:return int(Path('/proc/self/statm').read_text().split()[1])*os.sysconf('SC_PAGE_SIZE')
 except (OSError,ValueError,IndexError):return None
def peak_rss_bytes():
 v=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
 return int(v*1024) if sys.platform.startswith('linux') else int(v)
def worker(n,density,rep):
 from substrate_rs import Substrate
 graph=Substrate();rss_start=rss();peak_start=peak_rss_bytes()
 t=time.perf_counter_ns();nodes=[graph.add_node('ScaleNode',{'ordinal':i}) for i in range(n)]
 node_ns=time.perf_counter_ns()-t;rss_nodes=rss();peak_nodes=peak_rss_bytes()
 edge_count=n*density;t=time.perf_counter_ns()
 for i,src in enumerate(nodes):
  for k in range(density):graph.add_edge_unchecked(src,f'scale_edge_{k}',nodes[(i+k+1)%n])
 edge_ns=time.perf_counter_ns()-t;rss_edges=rss();peak_edges=peak_rss_bytes()
 return {'nodes':n,'edges':edge_count,'edge_multiplier':density,'replicate':rep,
  'node_insert_ns':node_ns,'edge_insert_ns':edge_ns,'total_insert_ns':node_ns+edge_ns,
  'node_throughput_per_s':n/(node_ns/1e9),'edge_throughput_per_s':edge_count/(edge_ns/1e9) if edge_count else None,
  'rss_start_bytes':rss_start,'rss_after_nodes_bytes':rss_nodes,'rss_after_edges_bytes':rss_edges,
  'rss_node_delta_bytes':rss_nodes-rss_start if rss_nodes is not None and rss_start is not None else None,
  'rss_edge_delta_bytes':rss_edges-rss_nodes if rss_edges is not None and rss_nodes is not None else None,
  'peak_start_bytes':peak_start,'peak_after_nodes_bytes':peak_nodes,'peak_after_edges_bytes':peak_edges,
  'peak_total_delta_bytes':peak_edges-peak_start}
def main():
 args=sys.argv[1:]
 if args[:1]==['--worker']:
  print(json.dumps(worker(int(args[1]),int(args[2]),int(args[3])),sort_keys=True,separators=(',',':')));return 0
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite existing capture')
  cells=[(n,d,r) for n in NODE_COUNTS for d in EDGE_MULTIPLIERS for r in range(REPLICATES)]
  random.Random(ORDER_SEED).shuffle(cells)
  LOCK.write_text(json.dumps({'schema':'NativeGraphBuildScalingV1Lock','sources':frozen(),
   'node_counts':NODE_COUNTS,'edge_multipliers':EDGE_MULTIPLIERS,'replicates':REPLICATES,
   'order_seed':ORDER_SEED,'capture_order':[list(x) for x in cells],
   'api':'substrate_rs.Substrate.add_node and add_edge_unchecked; one node type; edge sources use cyclic offsets'},
   indent=2,sort_keys=True)+'\n')
  print(LOCK.relative_to(ROOT));return 0
 if args!=['--run']:raise SystemExit('usage: --lock, --run, or --worker N EDGE_MULTIPLIER REP')
 lock=json.loads(LOCK.read_text())
 if frozen()!=lock['sources']:raise SystemExit('source drift from lock')
 env={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python'};rows=[]
 for n,d,rep in lock['capture_order']:
  p=subprocess.run([sys.executable,str(RUNNER),'--worker',str(n),str(d),str(rep)],cwd=ROOT,env=env,
   text=True,capture_output=True,timeout=300)
  if p.returncode:raise RuntimeError(f'worker {n}/{d}/{rep}: {p.stderr[-2000:]}')
  rows.append(json.loads(p.stdout.strip().splitlines()[-1]))
 if frozen()!=lock['sources']:raise SystemExit('source drift during capture')
 OUT.write_text(json.dumps({'schema':'NativeGraphBuildScalingV1Results','lock_sha256':sha(LOCK),
  'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),
  'sources':frozen(),'rows':rows},indent=2,sort_keys=True)+'\n')
 print(OUT.relative_to(ROOT));return 0
if __name__=='__main__':raise SystemExit(main())
