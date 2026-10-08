#!/usr/bin/env python3
"""Graph-only minimum vertex separator search on captured task graph families."""
from __future__ import annotations
import hashlib,itertools,json,os,platform,subprocess,sys,time,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
PROTOCOL=ROOT/'docs/research/engine_substrate/TASK_GRAPH_SEPARATOR_DISCOVERY_AUDIT_V1_PREREG_20261002.md'
RUNNER=Path(__file__).resolve();ANALYZER=ROOT/'evaluation/substrate_capability/analyze_task_graph_separator_discovery_audit_v1.py'
MODE_CAPTURE=ROOT/'evaluation/reports/llm_mode_neuron_task_graph_inference_census_v1_20261002.json'
MODE_LOCK=ROOT/'evaluation/substrate_capability/llm_mode_neuron_task_graph_inference_census_v1_lock_20261002.json'
TRANSPORT_CAPTURE=ROOT/'evaluation/reports/llm_transport_task_graph_exact_census_v1_1_20261002.json'
TRANSPORT_LOCK=ROOT/'evaluation/substrate_capability/llm_transport_task_graph_exact_census_v1_1_lock_20261002.json'
ROLE_CAPTURE=ROOT/'evaluation/reports/llm_transport_role_separator_v1_2_20261002.json'
ROLE_ANALYSIS=ROOT/'evaluation/reports/llm_transport_role_separator_v1_2_analysis_20261002.json'
ROLE_LOCK=ROOT/'evaluation/substrate_capability/llm_transport_role_separator_v1_2_lock_20261002.json'
LOCK=ROOT/'evaluation/substrate_capability/task_graph_separator_discovery_audit_v1_lock_20261002.json'
OUT=ROOT/'evaluation/reports/task_graph_separator_discovery_audit_v1_20261002.json'
REPS=3;SEARCH_REPEATS=3
def digest(p):
 p=Path(p);return {'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def sources():return {'artifacts':[digest(p) for p in (PROTOCOL,RUNNER,ANALYZER,MODE_CAPTURE,MODE_LOCK,TRANSPORT_CAPTURE,TRANSPORT_LOCK,ROLE_CAPTURE,ROLE_ANALYSIS,ROLE_LOCK)],'workers':REPS,'search_repeats':SEARCH_REPEATS}
def graph(m,n):return {'nodes':list(range(m+n)),'left':m,'right':n,'edges':[(i,m+j) for i in range(m) for j in range(n)]}
def components(g,removed):
 left=set(g['nodes'])-set(removed);adj={x:set() for x in left}
 for a,b in g['edges']:
  if a in left and b in left:adj[a].add(b);adj[b].add(a)
 result=[]
 while left:
  root=min(left);left.remove(root);stack=[root];comp=[]
  while stack:
   u=stack.pop();comp.append(u)
   for v in sorted(adj[u]&left,reverse=True):left.remove(v);stack.append(v)
  result.append(sorted(comp))
 return sorted(result,key=lambda c:(len(c),c))
def search(g):
 t=time.perf_counter_ns();tested=0;best=None;answers=[]
 for k in range(len(g['nodes'])+1):
  found=[]
  for tup in itertools.combinations(g['nodes'],k):
   tested+=1;parts=components(g,set(tup))
   if len(parts)>=2:found.append({'removed':list(tup),'components':parts})
  if found:best=k;answers=found;break
 return {'minimum_size':best,'minimum_separators':answers,'tested_subsets':tested,'elapsed_ns':time.perf_counter_ns()-t}
def worker(rep):
 before=sources();out={}
 for name,g in [('K4_8',graph(4,8)),('K8_8',graph(8,8))]:
  edge_count=32 if name=='K4_8' else 64
  times=[];base=None
  for _ in range(SEARCH_REPEATS):
   r=search(g);sig=(r['minimum_size'],r['minimum_separators'],r['tested_subsets'])
   if base is None:base=sig
   if sig!=base:raise RuntimeError('separator search result varied within worker')
   times.append(r['elapsed_ns']);last=r
  out[name]={'node_count':len(g['nodes']),'edge_count':len(g['edges']),'connected_before_removal':len(components(g,set()))==1,
   'search_result':last,'repeat_times_ns':times,'repeat_results_stable':True,'edge_count_expected':len(g['edges'])==edge_count}
 return {'replicate':rep,'pid':os.getpid(),'graphs':out,'source_start':before,'source_end':sources()}
def main():
 args=sys.argv[1:]
 if args[:1]==['--worker']:print(json.dumps(worker(int(args[1])),sort_keys=True,separators=(',',':')));return 0
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite lock or output')
  LOCK.write_text(json.dumps({'schema':'TaskGraphSeparatorDiscoveryAuditV1Lock','sources':sources()},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if args!=['--run']:raise SystemExit('usage: --lock, --run, or --worker REP')
 lock=json.loads(LOCK.read_text());before=sources()
 if before!=lock['sources']:raise SystemExit('source/capture drift from lock')
 # Validate the input captures before spending search time.
 mc=json.loads(MODE_CAPTURE.read_text());tc=json.loads(TRANSPORT_CAPTURE.read_text());ra=json.loads(ROLE_ANALYSIS.read_text())
 if not all(mc['checks'].values()) or not all(tc['checks'].values()) or not ra['gates_pass']:raise SystemExit('an upstream capture/analyzer gate failed')
 env={**os.environ,'PYTHONPATH':f"{ROOT}:{os.environ.get('PYTHONPATH','')}"};runs=[]
 for rep in range(REPS):
  p=subprocess.run([sys.executable,str(RUNNER),'--worker',str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=600)
  if p.returncode:raise SystemExit(p.stderr[-3000:])
  r=json.loads(p.stdout.strip());runs.append(r);print(f"rep={rep} pid={r['pid']} K4,8={r['graphs']['K4_8']['search_result']['minimum_size']} K8,8={r['graphs']['K8_8']['search_result']['minimum_size']}",flush=True)
 after=sources();checks={'three_fresh_workers':len(runs)==REPS and len({r['pid'] for r in runs})==REPS,'source_stable':before==lock['sources']==after,
  'worker_locks_stable':all(r['source_start']==lock['sources']==r['source_end'] for r in runs),'all_repeats_stable':all(g['repeat_results_stable'] for r in runs for g in r['graphs'].values()),
  'both_input_captures_pass':all(mc['checks'].values()) and all(tc['checks'].values()) and ra['gates_pass'],
  'expected_connected_topologies':all(r['graphs']['K4_8']['connected_before_removal'] and r['graphs']['K4_8']['edge_count_expected'] and r['graphs']['K8_8']['connected_before_removal'] and r['graphs']['K8_8']['edge_count_expected'] for r in runs),
  'expected_minima':all(r['graphs']['K4_8']['search_result']['minimum_size']==4 and r['graphs']['K8_8']['search_result']['minimum_size']==8 for r in runs)}
 OUT.write_text(json.dumps({'schema':'TaskGraphSeparatorDiscoveryAuditV1Capture','lock_sha256':hashlib.sha256(LOCK.read_bytes()).hexdigest(),'sources':before,'post_run_sources':after,'checks':checks,'runs':runs},indent=2,sort_keys=True)+'\n')
 print(json.dumps({'capture':OUT.relative_to(ROOT).as_posix(),'checks':checks},indent=2));return 0 if all(checks.values()) else 1
if __name__=='__main__':raise SystemExit(main())
