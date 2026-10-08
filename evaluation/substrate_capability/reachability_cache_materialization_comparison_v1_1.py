#!/usr/bin/env python3
"""Compare native ReachableFrom memoization with explicit finite-key materialization."""
from __future__ import annotations
import hashlib,itertools,json,resource,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'scripts')]
from domains.engine_provenance import engine_preamble,assert_measuring_engine
engine_preamble()
from substrate_rs import _native
from analyze_mint_termination_fragment import analyze
RUNNER=Path(__file__).resolve();ANALYZER=ROOT/'evaluation/substrate_capability/analyze_reachability_cache_materialization_comparison_v1_1.py';PROTOCOL=ROOT/'docs/research/engine_substrate/REACHABILITY_CACHE_MATERIALIZATION_COMPARISON_V1_1_AMENDMENT_20261005.md'
LOCK=ROOT/'evaluation/substrate_capability/reachability_cache_materialization_comparison_v1_1_lock_20261005.json';OUT=ROOT/'evaluation/reports/reachability_cache_materialization_comparison_v1_1_20261005.json'
SOURCES=('scripts/analyze_mint_termination_fragment.py','runners/dsl/src/py.rs','runners/dsl/src/rewrite.rs','runners/dsl/src/graph.rs','runners/dsl/src/substrate.rs','runners/dsl/src/term.rs','runners/dsl/src/jsonio.rs','runners/dsl/python/substrate_rs/__init__.py','runners/dsl/python/substrate_rs/_native.build.json','runners/dsl/Cargo.lock')
PROFILE=[{'name':'direct_link','match':[['x','link','y']],'effects':[['add_edge','x','reachable','y',{}]]},{'name':'transitive_link','match':[['x','reachable','y'],['y','link','z']],'effects':[['add_edge','x','reachable','z',{}]]}]
NEGATIVE=[{'name':'unrestricted_mint','match':[['x','link','y']],'effects':[['add_node','w','Fresh',{'tag':'unbounded'}]]}]
TOPOLOGIES=('binary_tree','ternary_tree');SIZES=(64,128);READERS=(1,4,16);REPS=5

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def edges_for(kind,n):
 a={'binary_tree':2,'ternary_tree':3}[kind];return [(p,c) for p in range(n) for c in range(a*p+1,a*p+a+1) if c<n]
def design():return {'topologies':list(TOPOLOGIES),'sizes':list(SIZES),'reader_rule_counts':list(READERS),'repetitions':REPS,'arms':['direct_cache_off','direct_cache_on','materialized_profile'],'reader_where':'Gte(Count(ReachableFrom(x, link)), 0)','arm_order':'cyclic rotation by cell/repetition index','profile':PROFILE,'negative_control':NEGATIVE,'max_steps_slack':10}
def lock_inputs():
 p=assert_measuring_engine();return {'runner_sha256':sha(RUNNER),'analyzer_sha256':sha(ANALYZER),'protocol_sha256':sha(PROTOCOL),'engine_fingerprint':p['source_fingerprint'],'native_sha256':sha(Path(_native.__file__).resolve()),'source_sha256':{x:sha(ROOT/x) for x in SOURCES},'design':design()}
def bfs(n,edges,start):
 adj=[[] for _ in range(n)]
 for a,b in edges:adj[a].append(b)
 seen=set();todo=list(adj[start])
 while todo:
  x=todo.pop()
  if x==start or x in seen:continue
  seen.add(x);todo.extend(adj[x])
 return sorted(seen)
def reader_rule(i,typ):
 q={'type':'ReachableFrom' if typ=='reachable' else 'Neighbours','node':{'type':'Var','name':'x'},'edge_type':'link' if typ=='reachable' else 'reachable'}
 return {'name':f'reader_{i}','match':[['x','query_source','q']],'where':{'type':'Gte','a':{'type':'Count','source':q},'b':{'type':'Lit','value':0}},'effects':[]}
def build(kind,n,cache):
 t=time.perf_counter_ns();c=time.process_time_ns();sub=_native.Substrate();sub.set_reachable_cache(cache);ids=[sub.add_node('Vertex',{'ordinal':i}) for i in range(n)]
 for a,b in edges_for(kind,n):sub.add_edge_unchecked(ids[a],'link',ids[b])
 for node in ids:sub.add_edge_unchecked(node,'query_source',ids[0])
 return sub,ids,time.perf_counter_ns()-t,time.process_time_ns()-c
def timed_run(sub,budget):
 t=time.perf_counter_ns();c=time.process_time_ns();r=sub.run_rules_report(budget,False);return dict(r),time.perf_counter_ns()-t,time.process_time_ns()-c
def one_arm(kind,n,r,arm):
 cache=arm=='direct_cache_on';sub,ids,setup_wall,setup_cpu=build(kind,n,cache);t=time.perf_counter_ns();c=time.process_time_ns();profile_install=profile_closure=profile_cpu=profile_install_cpu=0
 if arm=='materialized_profile':
  for rule in PROFILE:sub.add_rule(rule)
  profile_install=time.perf_counter_ns()-t;profile_install_cpu=time.process_time_ns()-c
  spec=analyze(PROFILE,[f'n{i}' for i in range(n)],[[f'n{a}','link',f'n{b}',{}] for a,b in edges_for(kind,n)])
  t=time.perf_counter_ns();c=time.process_time_ns();pr=dict(sub.run_rules_report(spec['progress_steps_upper_bound']+10,False));profile_closure=time.perf_counter_ns()-t;profile_cpu=time.process_time_ns()-c
 else:pr=None
 t=time.perf_counter_ns();c=time.process_time_ns()
 for i in range(r):sub.add_rule(reader_rule(i,'reachable' if arm!='materialized_profile' else 'neighbours'))
 reader_install=time.perf_counter_ns()-t;reader_install_cpu=time.process_time_ns()-c
 stats_before=dict(sub.reachable_cache_stats());rr,rw,rc=timed_run(sub,1000000);stats=dict(sub.reachable_cache_stats())
 graph=sub.graph_to_dict();rel={(int(e['src']),int(e['tgt'])) for e in graph['edges'] if e['type']=='reachable'}
 expected={(i,j) for i in range(n) for j in bfs(n,edges_for(kind,n),i)}
 query={'type':'ReachableFrom','node':{'type':'Var','name':'x'},'edge_type':'link'} if arm!='materialized_profile' else {'type':'Neighbours','node':{'type':'Var','name':'x'},'edge_type':'reachable'}
 observed=[len(sub.evaluate(query,{'x':node})) for node in ids]
 expected_counts=[len(bfs(n,edges_for(kind,n),i)) for i in range(n)]
 report_ok=rr.get('status')=='fixed_point' and rr.get('progress_steps')==0
 profile_ok=arm!='materialized_profile' or (pr and pr.get('status')=='fixed_point' and rel==expected)
 expected_matches=n*r
 return {'arm':arm,'graph_nodes':len(graph['nodes']),'graph_edges':len(graph['edges']),'materialized_pairs':len(rel),'materialized_exact':rel==expected if arm=='materialized_profile' else True,'observed_query_counts':observed,'expected_query_counts':expected_counts,'query_counts_exact':observed==expected_counts,'profile_report':pr,'reader_report':rr,'reader_report_ok':report_ok,'expected_reader_evaluations':expected_matches,'cache_stats':stats,'cache_activity_since_start':{k:int(stats.get(k,0)-stats_before.get(k,0)) for k in stats},'graph_setup_wall_ns':setup_wall,'graph_setup_cpu_ns':setup_cpu,'reader_install_wall_ns':reader_install,'reader_install_cpu_ns':reader_install_cpu,'profile_install_wall_ns':profile_install,'profile_install_cpu_ns':profile_install_cpu,'profile_closure_wall_ns':profile_closure,'profile_closure_cpu_ns':profile_cpu,'reader_wall_ns':rw,'reader_cpu_ns':rc,'total_wall_ns':setup_wall+reader_install+profile_install+profile_closure+rw,'total_cpu_ns':setup_cpu+reader_install_cpu+profile_install_cpu+profile_cpu+rc,'profile_ok':profile_ok,'peak_rss_bytes':int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1024 if sys.platform.startswith('linux') else 1))}
def one_case(kind,n,r,rep,cell_index):
 spec=analyze(PROFILE,[f'n{i}' for i in range(n)],[[f'n{a}','link',f'n{b}',{}] for a,b in edges_for(kind,n)])
 if not spec['accepted']:raise RuntimeError('profile refused')
 arms=['direct_cache_off','direct_cache_on','materialized_profile'];rotation=(rep+cell_index)%3;order=arms[rotation:]+arms[:rotation]
 rows={a:one_arm(kind,n,r,a) for a in order}
 return {'topology':kind,'n':n,'reader_rules':r,'replicate':rep,'edge_count':len(edges_for(kind,n)),'checker':spec,'arm_order':order,'arms':rows}
def main():
 if sys.argv[1:]==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing overwrite')
  LOCK.write_text(json.dumps({'schema':'ReachabilityCacheMaterializationV1_1Lock','locked_inputs':lock_inputs()},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 before=lock_inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=before:raise SystemExit('missing or stale source lock')
 cases=[]
 for ix,(kind,n,r,rep) in enumerate(itertools.product(TOPOLOGIES,SIZES,READERS,range(1,REPS+1))):
  c=one_case(kind,n,r,rep,ix);cases.append(c);print(f'{len(cases)}/60 {kind} N={n} readers={r} rep={rep}',flush=True)
 after=lock_inputs();out={'schema':'ReachabilityCacheMaterializationV1_1','locked_inputs':before,'post_run_inputs':after,'cases':cases,'passed':before==after and len(cases)==60,'claim_limit':'controlled native no-op rule workload; comparison is not natural task prevalence or general cache policy'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':out['passed'],'cases':len(cases),'output':OUT.relative_to(ROOT).as_posix()}));return 0 if out['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
