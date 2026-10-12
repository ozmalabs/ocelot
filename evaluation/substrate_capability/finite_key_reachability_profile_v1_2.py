#!/usr/bin/env python3
"""Source-locked crossover replication for a restricted reachability profile."""
from __future__ import annotations
import hashlib,itertools,json,resource,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'scripts')]
from domains.engine_provenance import engine_preamble,assert_measuring_engine
engine_preamble()
from substrate_rs import _native
from analyze_mint_termination_fragment import analyze
RUNNER=Path(__file__).resolve();ANALYZER=ROOT/'evaluation/substrate_capability/analyze_finite_key_reachability_profile_v1_2.py';PROTOCOL=ROOT/'docs/research/engine_substrate/FINITE_KEY_REACHABILITY_PROFILE_V1_2_PREREG_20261005.md'
LOCK=ROOT/'evaluation/substrate_capability/finite_key_reachability_profile_v1_2_lock_20261005.json';OUT=ROOT/'evaluation/reports/finite_key_reachability_profile_v1_2_20261005.json'
SOURCES=('scripts/analyze_mint_termination_fragment.py','runners/dsl/src/py.rs','runners/dsl/src/rewrite.rs','runners/dsl/src/graph.rs','runners/dsl/src/substrate.rs','runners/dsl/src/term.rs','runners/dsl/src/jsonio.rs','runners/dsl/python/substrate_rs/__init__.py','runners/dsl/python/substrate_rs/_native.build.json','runners/dsl/Cargo.lock')
PROFILE=[{'name':'direct_link','match':[['x','link','y']],'effects':[['add_edge','x','reachable','y',{}]]},{'name':'transitive_link','match':[['x','reachable','y'],['y','link','z']],'effects':[['add_edge','x','reachable','z',{}]]}]
NEGATIVE=[{'name':'unrestricted_mint','match':[['x','link','y']],'effects':[['add_node','w','Fresh',{'tag':'unbounded'}]]}]
TOPOLOGIES=('binary_tree','ternary_tree');SIZES=(64,128);REPS=15;Q_VALUES=(1,2,4,8,16,32)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def edges_for(kind,n):
 arity={'binary_tree':2,'ternary_tree':3}[kind]
 return [(p,c) for p in range(n) for c in range(arity*p+1,arity*p+arity+1) if c<n]
def design():return {'profile':PROFILE,'negative_control':NEGATIVE,'topologies':list(TOPOLOGIES),'sizes':list(SIZES),'repetitions':REPS,'query_batch_counts':list(Q_VALUES),'each_batch_queries_all_sources':True,'alternate_query_arm_order':True,'crossover_rule':'median paired ratio < 1 and at least 12/15 repetitions favor materialization','max_steps_slack':10}
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
 return sorted(seen)
def one_case(kind,n,rep):
 pairs=edges_for(kind,n);spec=analyze(PROFILE,[f'n{i}' for i in range(n)],[[f'n{a}','link',f'n{b}',{}] for a,b in pairs])
 if not spec['accepted']:raise RuntimeError('restricted profile rejected')
 t=time.perf_counter_ns();c=time.process_time_ns();sub=_native.Substrate();ids=[sub.add_node('Vertex',{'ordinal':i}) for i in range(n)]
 for a,b in pairs:sub.add_edge_unchecked(ids[a],'link',ids[b])
 setup_w=time.perf_counter_ns()-t;setup_c=time.process_time_ns()-c
 t=time.perf_counter_ns();c=time.process_time_ns()
 for rule in PROFILE:sub.add_rule(rule)
 install_w=time.perf_counter_ns()-t;install_c=time.process_time_ns()-c
 t=time.perf_counter_ns();c=time.process_time_ns();report=sub.run_rules_report(spec['progress_steps_upper_bound']+10,False);closure_w=time.perf_counter_ns()-t;closure_c=time.process_time_ns()-c
 native_index={node:i for i,node in enumerate(ids)};oracle=[bfs(n,pairs,i) for i in range(n)]
 direct={'type':'ReachableFrom','node':{'type':'Var','name':'start'},'edge_type':'link'};lookup={'type':'Neighbours','node':{'type':'Var','name':'start'},'edge_type':'reachable'}
 mat={(int(e['src']),int(e['tgt'])) for e in sub.graph_to_dict()['edges'] if e['type']=='reachable'};expected={(i,j) for i,row in enumerate(oracle) for j in row}
 def batch(term):return [sorted(native_index[v] for v in sub.evaluate(term,{'start':node})) for node in ids]
 sweep={}
 for q in Q_VALUES:
  direct_first=((rep+q.bit_length())%2==0)
  def timed(term):
   t=time.perf_counter_ns();c=time.process_time_ns();ans=None
   for _ in range(q):ans=batch(term)
   return ans,time.perf_counter_ns()-t,time.process_time_ns()-c
  if direct_first:
   da,dw,dc=timed(direct);ma,mw,mc=timed(lookup)
  else:
   ma,mw,mc=timed(lookup);da,dw,dc=timed(direct)
  sweep[str(q)]={'direct_wall_ns':dw,'direct_cpu_ns':dc,'materialized_wall_ns':mw,'materialized_cpu_ns':mc,'direct_answers_exact':da==oracle,'materialized_answers_exact':ma==oracle,'direct_total_wall_ns':setup_w+dw,'direct_total_cpu_ns':setup_c+dc,'profile_total_wall_ns':setup_w+install_w+closure_w+mw,'profile_total_cpu_ns':setup_c+install_c+closure_c+mc,'materialization_favored':setup_w+install_w+closure_w+mw < setup_w+dw,'direct_measured_first':direct_first}
 return {'topology':kind,'n':n,'replicate':rep,'edges':pairs,'edge_count':len(pairs),'reachable_pairs':len(expected),'oracle':oracle,'materialized_pair_count':len(mat),'materialized_exact':mat==expected,'checker':spec,'closure_report':report,'setup_wall_ns':setup_w,'setup_cpu_ns':setup_c,'install_wall_ns':install_w,'install_cpu_ns':install_c,'closure_wall_ns':closure_w,'closure_cpu_ns':closure_c,'sweep':sweep,'peak_rss_bytes':int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1024 if sys.platform.startswith('linux') else 1))}
def main():
 if sys.argv[1:]==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing overwrite')
  LOCK.write_text(json.dumps({'schema':'FiniteKeyReachabilityProfileV1_2Lock','locked_inputs':lock_inputs()},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 before=lock_inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=before:raise SystemExit('missing or stale lock')
 cases=[]
 for i,(kind,n,rep) in enumerate(itertools.product(TOPOLOGIES,SIZES,range(1,REPS+1)),1):
  row=one_case(kind,n,rep);cases.append(row);print(f'{i}/60 {kind} N={n} rep={rep}',flush=True)
 after=lock_inputs();out={'schema':'FiniteKeyReachabilityProfileV1_2','locked_inputs':before,'post_run_inputs':after,'cases':cases,'passed':before==after and len(cases)==60,'claim_limit':'targeted timing replication on two synthetic tree families; no natural-task prevalence or general scaling claim'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':out['passed'],'cases':len(cases),'output':OUT.relative_to(ROOT).as_posix()}));return 0 if out['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
