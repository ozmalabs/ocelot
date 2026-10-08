#!/usr/bin/env python3
"""Locked restricted finite-key reachability profile and direct-query comparison."""
from __future__ import annotations
import hashlib,itertools,json,platform,resource,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'scripts')]
from domains.engine_provenance import engine_preamble,assert_measuring_engine
engine_preamble()
from substrate_rs import _native
from analyze_mint_termination_fragment import analyze
RUNNER=Path(__file__).resolve();ANALYZER=ROOT/'evaluation/substrate_capability/analyze_finite_key_reachability_profile_v1.py';PROTOCOL=ROOT/'docs/research/engine_substrate/FINITE_KEY_REACHABILITY_PROFILE_V1_PREREG_20261005.md'
LOCK=ROOT/'evaluation/substrate_capability/finite_key_reachability_profile_v1_lock_20261005.json';OUT=ROOT/'evaluation/reports/finite_key_reachability_profile_v1_20261005.json'
SOURCES=('scripts/analyze_mint_termination_fragment.py','runners/dsl/src/py.rs','runners/dsl/src/rewrite.rs','runners/dsl/src/graph.rs','runners/dsl/src/substrate.rs','runners/dsl/src/term.rs','runners/dsl/src/jsonio.rs','runners/dsl/python/substrate_rs/__init__.py','runners/dsl/python/substrate_rs/_native.build.json','runners/dsl/Cargo.lock')
PROFILE=[{'name':'direct_link','match':[['x','link','y']],'effects':[['add_edge','x','reachable','y',{}]]},{'name':'transitive_link','match':[['x','reachable','y'],['y','link','z']],'effects':[['add_edge','x','reachable','z',{}]]}]
NEGATIVE=[{'name':'unrestricted_mint','match':[['x','link','y']],'effects':[['add_node','w','Fresh',{'tag':'unbounded'}]]}]
TOPOLOGIES=('path','binary_tree','four_layer_dag');SIZES=(8,16,32,64);REPS=3;SEED=20261005

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def edges_for(kind,n):
 if kind=='path':return [(i,i+1) for i in range(n-1)]
 if kind=='binary_tree':return [(p,c) for p in range(n) for c in (2*p+1,2*p+2) if c<n]
 if kind=='four_layer_dag':
  w=n//4;return [(a,b) for layer in range(3) for a in range(layer*w,(layer+1)*w) for b in range((layer+1)*w,(layer+2)*w)]
 raise KeyError(kind)
def design():return {'profile':PROFILE,'negative_control':NEGATIVE,'topologies':list(TOPOLOGIES),'sizes':list(SIZES),'repetitions':REPS,'seed':SEED,'direct_query_term':{'type':'ReachableFrom','node':{'type':'Var','name':'start'},'edge_type':'link'},'max_steps_slack':10}
def lock_inputs():
 prov=assert_measuring_engine();return {'runner_sha256':sha(RUNNER),'analyzer_sha256':sha(ANALYZER),'protocol_sha256':sha(PROTOCOL),'engine_fingerprint':prov['source_fingerprint'],'native_sha256':sha(Path(_native.__file__).resolve()),'source_sha256':{p:sha(ROOT/p) for p in SOURCES},'design':design()}
def bfs(n,edges,start):
 adj=[[] for _ in range(n)]
 for a,b in edges:adj[a].append(b)
 seen=set();stack=list(adj[start])
 while stack:
  x=stack.pop()
  if x==start or x in seen:continue
  seen.add(x);stack.extend(adj[x])
 return seen
def one_case(kind,n,rep,locked):
 pairs=edges_for(kind,n);spec=analyze(PROFILE,[f'n{i}' for i in range(n)],[[f'n{a}','link',f'n{b}',{}] for a,b in pairs]);
 if not spec['accepted']:raise RuntimeError('registered profile rejected by checker')
 setup_start=time.perf_counter_ns();setup_cpu=time.process_time_ns();sub=_native.Substrate();native_ids=[sub.add_node('Vertex',{'ordinal':i}) for i in range(n)]
 for a,b in pairs:sub.add_edge_unchecked(native_ids[a],'link',native_ids[b])
 for r in PROFILE:sub.add_rule(r)
 setup_wall=time.perf_counter_ns()-setup_start;setup_cpu_ns=time.process_time_ns()-setup_cpu
 native_index={node:i for i,node in enumerate(native_ids)}
 direct_start=time.perf_counter_ns();direct_cpu=time.process_time_ns();direct=[]
 term={'type':'ReachableFrom','node':{'type':'Var','name':'start'},'edge_type':'link'}
 for i,node in enumerate(native_ids):direct.append(sorted(native_index[v] for v in sub.evaluate(term,{'start':node})))
 direct_wall=time.perf_counter_ns()-direct_start;direct_cpu_ns=time.process_time_ns()-direct_cpu
 closure_start=time.perf_counter_ns();closure_cpu=time.process_time_ns();report=sub.run_rules_report(spec['progress_steps_upper_bound']+10,False);closure_wall=time.perf_counter_ns()-closure_start;closure_cpu_ns=time.process_time_ns()-closure_cpu
 graph=sub.graph_to_dict();actual={(int(e['src']),e['type'],int(e['tgt'])) for e in graph['edges'] if e['type']=='reachable'}
 expected={(i,'reachable',j) for i in range(n) for j in bfs(n,pairs,i)}
 oracle_sets=[sorted(bfs(n,pairs,i)) for i in range(n)]
 return {'topology':kind,'n':n,'replicate':rep,'initial_edges':pairs,'initial_edge_count':len(pairs),'expected_reachable_pairs':len(expected),'direct_reachable_by_source':direct,'oracle_reachable_by_source':oracle_sets,'checker':spec,'native_report':report,'native_graph_nodes':len(graph['nodes']),'native_graph_edges':len(graph['edges']),'materialized_reachable_edges':len(actual),'materialized_reachable_pairs':[list(x) for x in sorted(actual)],'exact_materialized_relation':actual==expected,'exact_direct_query':direct==oracle_sets,'direct_query_wall_ns':direct_wall,'direct_query_cpu_ns':direct_cpu_ns,'profile_setup_wall_ns':setup_wall,'profile_setup_cpu_ns':setup_cpu_ns,'profile_closure_wall_ns':closure_wall,'profile_closure_cpu_ns':closure_cpu_ns,'process_peak_rss_bytes':int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1024 if sys.platform.startswith('linux') else 1))}
def main():
 if sys.argv[1:]==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing overwrite')
  LOCK.write_text(json.dumps({'schema':'FiniteKeyReachabilityProfileV1Lock','locked_inputs':lock_inputs()},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 before=lock_inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=before:raise SystemExit('missing or stale restricted-profile lock')
 t=time.perf_counter_ns();cases=[]
 for kind,n,rep in itertools.product(TOPOLOGIES,SIZES,range(1,REPS+1)):
  row=one_case(kind,n,rep,before);cases.append(row);print(f"{len(cases)}/36 {kind} N={n} rep={rep} closure={row['native_report']['status']}",flush=True)
 after=lock_inputs();result={'schema':'FiniteKeyReachabilityProfileV1','locked_inputs':before,'post_run_inputs':after,'cases':cases,'elapsed_wall_ns':time.perf_counter_ns()-t,'checks':{'source_lock_stable':before==after,'exact_case_matrix':len(cases)==len(TOPOLOGIES)*len(SIZES)*REPS},'claim_limit':'one authored two-rule finite-key reachability profile over three finite DAG families; no current seed-root admission or unrestricted termination claim.'}
 result['passed']=all(result['checks'].values());OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':result['passed'],'cases':len(cases),'output':OUT.relative_to(ROOT).as_posix()}));return 0 if result['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
