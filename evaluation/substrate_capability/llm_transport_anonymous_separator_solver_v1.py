#!/usr/bin/env python3
"""Anonymous graph-only separator search followed by generic exact conditioning."""
from __future__ import annotations
import hashlib,itertools,json,os,platform,resource,subprocess,sys,time
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT)]
EXPORT=Path('/applications/data/model_graph_work/transport_L12_13.npz')
RUNNER=Path(__file__).resolve();BASE_PROTOCOL=ROOT/'docs/research/engine_substrate/LLM_TRANSPORT_ANONYMOUS_SEPARATOR_SOLVER_V1_PREREG_20261002.md'
PREV_PROTOCOL=ROOT/'docs/research/engine_substrate/LLM_TRANSPORT_ANONYMOUS_SEPARATOR_SOLVER_V1_2_AMENDMENT_20261002.md'
PROTOCOL=ROOT/'docs/research/engine_substrate/LLM_TRANSPORT_ANONYMOUS_SEPARATOR_SOLVER_V1_3_AMENDMENT_20261003.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_llm_transport_anonymous_separator_solver_v1.py'
PRIOR=ROOT/'evaluation/reports/llm_transport_task_graph_exact_census_v1_1_20261002.json'
PRIOR_LOCK=ROOT/'evaluation/substrate_capability/llm_transport_task_graph_exact_census_v1_1_lock_20261002.json'
ROLE_CAPTURE=ROOT/'evaluation/reports/llm_transport_role_separator_v1_2_20261002.json'
ROLE_ANALYSIS=ROOT/'evaluation/reports/llm_transport_role_separator_v1_2_analysis_20261002.json'
ROLE_LOCK=ROOT/'evaluation/substrate_capability/llm_transport_role_separator_v1_2_lock_20261002.json'
SEED=ROOT/'seeds/can_native_reimplementation.json'
PILOT_CAPTURE=ROOT/'evaluation/reports/llm_transport_anonymous_separator_solver_v1_20261002.json'
V1_1_CAPTURE=ROOT/'evaluation/reports/llm_transport_anonymous_separator_solver_v1_1_20261002.json'
V1_1_LOCK=ROOT/'evaluation/substrate_capability/llm_transport_anonymous_separator_solver_v1_1_lock_20261002.json'
V1_2_CAPTURE=ROOT/'evaluation/reports/llm_transport_anonymous_separator_solver_v1_2_20261002.json'
V1_2_LOCK=ROOT/'evaluation/substrate_capability/llm_transport_anonymous_separator_solver_v1_2_lock_20261002.json'
LOCK=ROOT/'evaluation/substrate_capability/llm_transport_anonymous_separator_solver_v1_3_lock_20261003.json'
OUT=ROOT/'evaluation/reports/llm_transport_anonymous_separator_solver_v1_3_20261003.json'
REPS=3;K=8;VOCAB=(-1.,0.,1.);TOL=1e-8
def digest(p):
 p=Path(p);b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def sources():
 from substrate_rs import _native
 return {'runner':digest(RUNNER),'base_protocol':digest(BASE_PROTOCOL),'v1_1_amendment':digest(PREV_PROTOCOL),'v1_3_amendment':digest(PROTOCOL),'analyzer':digest(ANALYZER),'v1_pilot_capture':digest(PILOT_CAPTURE),'v1_1_failed_capture':digest(V1_1_CAPTURE),'v1_1_failed_lock':digest(V1_1_LOCK),'v1_2_capture':digest(V1_2_CAPTURE),'v1_2_lock':digest(V1_2_LOCK),'prior_capture':digest(PRIOR),'prior_lock':digest(PRIOR_LOCK),'role_capture':digest(ROLE_CAPTURE),'role_analysis':digest(ROLE_ANALYSIS),'role_lock':digest(ROLE_LOCK),'seed':digest(SEED),'sources':[digest(ROOT/p) for p in ('domains/llm_native_graph.py','domains/can_junction_tree.py','domains/graph_treewidth.py')],'native':digest(Path(_native.__file__).resolve()),'native_manifest':digest(ROOT/'runners/dsl/python/substrate_rs/_native.build.json'),'export':digest(EXPORT),'replicates':REPS,'heldout_rows':10,'conditions':['learned','shuffled'],'k':K,'vocab':list(VOCAB),'ridge':1.,'shuffle_seed':0,'tolerance':TOL,'anonymization_seed_formula':'20261003 + replicate*1000; stable within worker'}
def nid(v):return int(v.value if hasattr(v,'value') else v)
def energy(s,u,p):return -sum(float(h)*float(s[v]) for v,h in u.items())-sum(float(w)*float(s[a])*float(s[b]) for (a,b),w in p.items())
def components(nodes,edges,removed):
 left=set(nodes)-set(removed);adj={v:set() for v in left}
 for a,b in edges:
  if a in left and b in left:adj[a].add(b);adj[b].add(a)
 out=[]
 while left:
  root=min(left);left.remove(root);stack=[root];comp=[]
  while stack:
   u=stack.pop();comp.append(u)
   for v in adj[u]&left:left.remove(v);stack.append(v)
  out.append(sorted(comp))
 return sorted(out,key=lambda x:(len(x),x))
def propose(nodes,edges):
 tested=0
 for k in range(len(nodes)+1):
  found=[]
  for sep in itertools.combinations(sorted(nodes),k):
   tested+=1;cs=components(nodes,edges,set(sep))
   if len(cs)>=2:found.append({'separator':list(sep),'components':cs})
  if found:return found,tested,k
 return [],tested,None
def conditioned(nodes,edges,u,p,separator,comps):
 t0=time.perf_counter_ns();sep=tuple(separator);best=float('inf');beststate=None
 sep_set=set(sep);inside=[(a,b,w) for (a,b),w in p.items() if a in sep_set and b in sep_set]
 prepared=[]
 for comp in comps:
  cset=set(comp);internal=[(a,b,w) for (a,b),w in p.items() if a in cset and b in cset]
  boundary=[(a,b,w) for (a,b),w in p.items() if (a in cset) != (b in cset)]
  configurations=[dict(zip(comp,vals)) for vals in itertools.product(VOCAB,repeat=len(comp))]
  prepared.append((comp,cset,internal,boundary,configurations))
 for values in itertools.product(VOCAB,repeat=len(sep)):
  fixed=dict(zip(sep,values));score=-sum(u[v]*fixed[v] for v in sep)-sum(w*fixed[a]*fixed[b] for a,b,w in inside);state=dict(fixed)
  for comp,cset,internal,boundary,configurations in prepared:
   localbest=float('inf');localstate=None
   for assignment in configurations:
    e=-sum(u[v]*assignment[v] for v in comp)
    e-=sum(w*assignment[a]*assignment[b] for a,b,w in internal)
    for a,b,w in boundary:
     if a in cset:e-=w*assignment[a]*fixed[b]
     else:e-=w*assignment[b]*fixed[a]
    if e<localbest:localbest=e;localstate=assignment
   score+=localbest;state.update(localstate)
  if score<best:best=score;beststate=state
 return beststate,best,time.perf_counter_ns()-t0
def worker(rep):
 import substrate_rs as sr
 import domains.can_junction_tree as cjt
 from domains.graph_treewidth import min_fill_upper_bound,build_elimination_triangulation
 from domains import llm_native_graph as lng
 start=sources();z=np.load(EXPORT);T=lng.fit_transport(z['tr_c0'],z['tr_c1'],ridge=1.);flat=T.flatten().copy();np.random.default_rng(0).shuffle(flat);Ts=flat.reshape(T.shape);rows=[]
 seed=20261003+rep*1000;perm=np.random.default_rng(seed).permutation(16);proposal_cache={}
 for i,(x0,x1) in enumerate(zip(z['ho_c0'],z['ho_c1'])):
  target=np.where(x1[:K]>=0,1.,-1.)
  for ci,(cond,W) in enumerate((('learned',T),('shuffled',Ts))):
   sub=sr.Substrate();mt,n0,n1,d0,d1=lng.build_transport_factor_graph(sub,[str(SEED)],W,x0,n_modes0=K,n_modes1=K,temperature=1.,field_scale=1.,transport_scale=1.,discrete_mode='3state',bidirectional=True)
   net=cjt.can_network_from_mt(sub,mt);native_nodes=list(net['nodes']);native_edges=list(net['edges']);u0={nid(v):float(h) for v,h in net['unary'].items()};p0={tuple(sorted(map(nid,k))):float(v) for k,v in net['pairwise'].items()}
   # A stable opaque permutation within worker permits reuse by exact anonymous topology signature.
   mapping={nid(v):int(perm[j]) for j,v in enumerate(native_nodes)}
   nodes=list(range(len(native_nodes)));edges=[tuple(sorted((mapping[nid(a)],mapping[nid(b)]))) for a,b in native_edges]
   u={mapping[v]:h for v,h in u0.items()};p={tuple(sorted((mapping[a],mapping[b]))):w for (a,b),w in p0.items()}
   before_states={nid(v):float(sub.node(v)['attrs'].get('state',0.)) for v in n0+n1}
   # Uninstrumented monolithic baseline on the same factors.
   mf=min_fill_upper_bound(native_nodes,native_edges);tri=build_elimination_triangulation(native_nodes,native_edges,mf['elimination_order']);width=max((len(b)-1 for b in tri['bags'].values()),default=0)
   jt0=time.perf_counter_ns();jt=cjt.junction_tree_map(native_nodes,native_edges,net['unary'],{frozenset(k):v for k,v in net['pairwise'].items()},VOCAB,order=mf['elimination_order']);jt_ns=time.perf_counter_ns()-jt0
   jt_state={mapping[nid(v)]:float(value) for v,value in jt['state'].items()};jt_sign=[1. if jt_state[mapping[nid(v)]]>=0 else -1. for v in n1]
   signature=(tuple(nodes),tuple(sorted(edges)));cache_hit=signature in proposal_cache
   if cache_hit:candidates,tested,k=proposal_cache[signature];proposal_ns=0
   else:
    search0=time.perf_counter_ns();candidates,tested,k=propose(nodes,edges);proposal_ns=time.perf_counter_ns()-search0
    proposal_cache[signature]=(candidates,tested,k)
   candidate=candidates[0]
   s,e,solver_ns=conditioned(nodes,edges,u,p,candidate['separator'],candidate['components'])
   cp=[1. if s[mapping[nid(v)]]>=0 else -1. for v in n1]
   solved={'separator':candidate['separator'],'components':candidate['components'],'energy':e,'solver_ns':solver_ns,'state':{str(q):v for q,v in s.items()},'target_prediction':cp}
   selected={'state':s,'energy':e,'separator':candidate['separator']}
   route_ns=proposal_ns+solver_ns
   direct=energy(selected['state'],u,p);pred=[1. if selected['state'][mapping[nid(v)]]>=0 else -1. for v in n1]
   after=cjt.can_network_from_mt(sub,mt);after_state={nid(v):float(sub.node(v)['attrs'].get('state',0.)) for v in n0+n1}
   unchanged=(u0=={nid(v):float(h) for v,h in after['unary'].items()} and p0=={tuple(sorted(map(nid,k))):float(v) for k,v in after['pairwise'].items()} and before_states==after_state)
   rows.append({'heldout_index':i,'condition':cond,'anon_seed':seed,'proposal_cache_hit':cache_hit,'topology_signature_sha256':hashlib.sha256(json.dumps([len(nodes),sorted(edges)]).encode()).hexdigest(),'anonymous_ids':sorted(mapping.values()),'anon_map_by_native_order':[mapping[nid(v)] for v in native_nodes],'anonymous_edges':[list(e) for e in edges],'anonymous_unary':[[v,h] for v,h in sorted(u.items())],'anonymous_pair_factors':[[a,b,w] for (a,b),w in sorted(p.items())],'nodes':len(nodes),'edges':len(edges),'connected':len(components(nodes,edges,set()))==1,
    'width':int(mf['treewidth']),'certified_width':width,'candidate_count':len(candidates),'minimum_separator_size':k,'subsets_tested':tested,'proposal_candidates':candidates,'solved_candidate':solved,
    'selected_separator':selected['separator'],'selected_prediction':pred,'jt_energy':float(jt['energy']),'jt_direct_rescore':energy(jt_state,u,p),'selected_energy':selected['energy'],'selected_direct_rescore':direct,
    'state_valid':all(v in VOCAB for v in selected['state'].values()),'conditioned_prediction':pred,'jt_prediction':jt_sign,'target':target.tolist(),
    'conditioned_accuracy':float(np.mean(np.asarray(pred)==target)),'timing_ns':{'proposal':proposal_ns,'candidate_solver':solver_ns,'proposal_plus_solver':route_ns,'junction_tree':jt_ns},'no_mutation':unchanged})
 return {'replicate':rep,'pid':os.getpid(),'rows':rows,'unique_topology_count':len(proposal_cache),'proposal_searches':len(proposal_cache),'proposal_search_ns_total':sum(r['timing_ns']['proposal'] for r in rows),'cache_hits':sum(r['proposal_cache_hit'] for r in rows),'source_start':start,'source_end':sources(),'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
def main():
 args=sys.argv[1:]
 if args[:1]==['--worker']:print(json.dumps(worker(int(args[1])),sort_keys=True,separators=(',',':')));return 0
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite lock/capture')
  LOCK.write_text(json.dumps({'schema':'LlmTransportAnonymousSeparatorSolverV1_3Lock','sources':sources()},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if args!=['--run']:raise SystemExit('usage: --lock, --run, or --worker REP')
 lock=json.loads(LOCK.read_text());before=sources()
 if before!=lock['sources']:raise SystemExit('source drift from lock')
 prior=json.loads(PRIOR.read_text());role=json.loads(ROLE_ANALYSIS.read_text())
 if not all(prior['checks'].values()) or not role['gates_pass']:raise SystemExit('upstream transport gates are not passing')
 from domains.engine_provenance import build_is_stale
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit('native engine stale: '+'; '.join(stale))
 env={**os.environ,'PYTHONPATH':f"{ROOT/'runners/dsl/python'}:{ROOT}:{os.environ.get('PYTHONPATH','')}"};runs=[];fail=[]
 for rep in range(REPS):
  q=subprocess.run([sys.executable,str(RUNNER),'--worker',str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=1800)
  if q.returncode:fail.append({'replicate':rep,'error':q.stderr[-3000:]});continue
  r=json.loads(q.stdout);runs.append(r);print(f"rep={rep} pid={r['pid']} cells={len(r['rows'])}",flush=True)
 after=sources();cells=[c for r in runs for c in r['rows']]
 checks={'three_fresh_workers':len(runs)==REPS and len({r['pid'] for r in runs})==REPS,'no_failures':not fail,'coverage_60':all(len(r['rows'])==20 for r in runs),
  'expected_connected_graphs':all(c['connected'] and c['nodes']==16 and c['edges']==64 and c['width']==c['certified_width']==8 for c in cells),
  'anonymous_ids_and_cache_reuse':all(r['unique_topology_count']==1 and r['proposal_searches']==1 and r['cache_hits']==19 and all(c['anon_seed']==20261003+r['replicate']*1000 and sorted(c['anon_map_by_native_order'])==list(range(16)) for c in r['rows']) for r in runs),
  'valid_minimum_candidates':all(c['minimum_separator_size']==8 and c['candidate_count']==2 and c['subsets_tested']==39203 and len(c['proposal_candidates'])==2 and all(len(s['separator'])==8 and len(s['components'])==8 for s in c['proposal_candidates']) and c['solved_candidate']['separator']==c['proposal_candidates'][0]['separator'] for c in cells),
  'selected_candidate_energy_parity':all(abs(c['solved_candidate']['energy']-c['jt_energy'])<TOL for c in cells),
  'selected_candidate_state_valid':all(all(float(v) in VOCAB for v in c['solved_candidate']['state'].values()) for c in cells),
  'selected_candidate_sign_parity':all(c['solved_candidate']['target_prediction']==c['jt_prediction'] for c in cells),
  'exact_energy_and_direct_rescore':all(abs(c['jt_energy']-c['selected_energy'])<TOL and abs(c['selected_energy']-c['selected_direct_rescore'])<TOL and abs(c['jt_energy']-c['jt_direct_rescore'])<TOL for c in cells),
  'exact_returned_sign_parity':all(c['conditioned_prediction']==c['jt_prediction'] for c in cells),'valid_states':all(c['state_valid'] for c in cells),'no_mutation':all(c['no_mutation'] for c in cells),
  'source_locks_stable':before==lock['sources']==after and all(r['source_start']==lock['sources']==r['source_end'] for r in runs)}
 OUT.write_text(json.dumps({'schema':'LlmTransportAnonymousSeparatorSolverV1_3Capture','lock_sha256':hashlib.sha256(LOCK.read_bytes()).hexdigest(),'sources':before,'post_run_sources':after,'checks':checks,'failures':fail,'runs':runs},indent=2,sort_keys=True)+'\n')
 print(json.dumps({'capture':OUT.relative_to(ROOT).as_posix(),'checks':checks,'failures':len(fail)},indent=2));return 0 if all(checks.values()) else 1
if __name__=='__main__':raise SystemExit(main())
