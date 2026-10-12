#!/usr/bin/env python3
"""Compare monolithic exact MAP with exact mode-conditioned decomposition."""
from __future__ import annotations
import hashlib,itertools,json,os,platform,resource,subprocess,sys,time,tracemalloc
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT)]
EXPORT=Path('/applications/data/model_graph_work/transport_L12_13.npz')
RUNNER=Path(__file__).resolve(); BASE_PROTOCOL=ROOT/'docs/research/engine_substrate/LLM_TRANSPORT_ROLE_SEPARATOR_V1_PREREG_20261002.md'
PREV_PROTOCOL=ROOT/'docs/research/engine_substrate/LLM_TRANSPORT_ROLE_SEPARATOR_V1_1_AMENDMENT_20261002.md'
PROTOCOL=ROOT/'docs/research/engine_substrate/LLM_TRANSPORT_ROLE_SEPARATOR_V1_2_AMENDMENT_20261002.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_llm_transport_role_separator_v1.py'
BASE_RUNNER=ROOT/'evaluation/substrate_capability/llm_transport_task_graph_cost_v1.py'
BASE_ANALYSIS=ROOT/'evaluation/reports/llm_transport_task_graph_cost_v1_analysis_20261002.json'
PRIOR=ROOT/'evaluation/reports/llm_transport_task_graph_exact_census_v1_1_20261002.json'
BASE_CAPTURE=ROOT/'evaluation/reports/llm_transport_task_graph_cost_v1_20261002.json'
SEED=ROOT/'seeds/can_native_reimplementation.json'
LOCK=ROOT/'evaluation/substrate_capability/llm_transport_role_separator_v1_2_lock_20261002.json'
OUT=ROOT/'evaluation/reports/llm_transport_role_separator_v1_2_20261002.json'
R=3;K=8;VOCAB=(-1.,0.,1.);TOL=1e-8
def digest(p):
 b=Path(p).read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def sources():
 from substrate_rs import _native
 return {'runner':digest(RUNNER),'base_protocol':digest(BASE_PROTOCOL),'v1_1_sign_parity_amendment':digest(PREV_PROTOCOL),'v1_2_timing_amendment':digest(PROTOCOL),'analyzer':digest(ANALYZER),'baseline_runner':digest(BASE_RUNNER),'baseline_analysis':digest(BASE_ANALYSIS),'baseline_capture':digest(BASE_CAPTURE),'prior_capture':digest(PRIOR),'seed':digest(SEED),'sources':[digest(ROOT/p) for p in ('domains/llm_native_graph.py','domains/can_junction_tree.py','domains/graph_treewidth.py')],'native':digest(Path(_native.__file__).resolve()),'native_manifest':digest(ROOT/'runners/dsl/python/substrate_rs/_native.build.json'),'export':digest(EXPORT),'replicates':R,'k':K,'vocab':list(VOCAB),'ridge':1.0,'shuffle_seed':0,'tolerance':TOL}
def nid(v):return int(v.value if hasattr(v,'value') else v)
def energy(s,u,p):return -sum(float(h)*float(s[v]) for v,h in u.items())-sum(float(w)*float(s[a])*float(s[b]) for (a,b),w in p.items())
def connected(nodes,edges):
 adj={nid(v):set() for v in nodes}
 for a,b in edges:adj[nid(a)].add(nid(b));adj[nid(b)].add(nid(a))
 seen={next(iter(adj))};stack=list(seen)
 while stack:
  for v in adj[stack.pop()]-seen:seen.add(v);stack.append(v)
 return len(seen)==len(adj)
def conditioned(source_ids,target_ids,u,p):
 # Rows enumerate target states; columns are source variables.
 assignments=np.asarray(list(itertools.product(VOCAB,repeat=len(target_ids))),dtype=np.float64)
 wi=np.asarray([[p[tuple(sorted((a,b)))] for b in target_ids] for a in source_ids],dtype=np.float64)
 hu=np.asarray([u[a] for a in source_ids],dtype=np.float64);hv=np.asarray([u[b] for b in target_ids],dtype=np.float64)
 t=time.perf_counter_ns()
 interaction=assignments@wi.T
 costs=np.stack([interaction+hu[None,:],np.zeros_like(interaction),-interaction-hu[None,:]],axis=2)
 # cost axis corresponds to -1, 0, +1 source values.
 best_ix=np.argmin(costs,axis=2);best_cost=np.min(costs,axis=2)
 total=-(assignments*hv[None,:]).sum(axis=1)+best_cost.sum(axis=1)
 ix=int(np.argmin(total));ss=assignments[ix]
 src=np.asarray(VOCAB,dtype=np.float64)[best_ix[ix]]
 state={**{v:float(x) for v,x in zip(source_ids,src)},**{v:float(x) for v,x in zip(target_ids,ss)}}
 return state,float(total[ix]),time.perf_counter_ns()-t
def worker(rep):
 import substrate_rs as sr
 import domains.can_junction_tree as cjt
 from domains.graph_treewidth import min_fill_upper_bound,build_elimination_triangulation
 from domains.can_native_bp import run_loopy_bp
 from domains import llm_native_graph as lng
 start=sources();z=np.load(EXPORT);T=lng.fit_transport(z['tr_c0'],z['tr_c1'],ridge=1.0);flat=T.flatten().copy();np.random.default_rng(0).shuffle(flat);Ts=flat.reshape(T.shape);rows=[]
 for i,(x0,x1) in enumerate(zip(z['ho_c0'],z['ho_c1'])):
  target=np.where(x1[:K]>=0,1.,-1.)
  for cond,W in (('learned',T),('shuffled',Ts)):
   sub=sr.Substrate();mt,n0,n1,d0,d1=lng.build_transport_factor_graph(sub,[str(SEED)],W,x0,n_modes0=K,n_modes1=K,temperature=1.,field_scale=1.,transport_scale=1.,discrete_mode='3state',bidirectional=True)
   net=cjt.can_network_from_mt(sub,mt);nodes=list(net['nodes']);edges=list(net['edges']);u={nid(v):float(h) for v,h in net['unary'].items()};p={tuple(sorted(map(nid,k))):float(v) for k,v in net['pairwise'].items()}
   src=[nid(v) for v in n0];dst=[nid(v) for v in n1];state_before={nid(v):float(sub.node(v)['attrs'].get('state',0.)) for v in n0+n1}
   order=min_fill_upper_bound(nodes,edges);cert=build_elimination_triangulation(nodes,edges,order['elimination_order']);width=max((len(b)-1 for b in cert['bags'].values()),default=0)
   t=time.perf_counter_ns();jt=cjt.junction_tree_map(nodes,edges,net['unary'],{frozenset(k):v for k,v in net['pairwise'].items()},VOCAB,order=order['elimination_order']);jt_ns=time.perf_counter_ns()-t
   jt_state={nid(k):float(v) for k,v in jt['state'].items()};jt_energy=energy(jt_state,u,p)
   part_state,part_energy,part_ns=conditioned(src,dst,u,p)
   tracemalloc.start();tracemalloc.reset_peak();trace_state,trace_energy,_=conditioned(src,dst,u,p);_,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
   direct=energy(part_state,u,p);bp=run_loopy_bp(sub,mt,combine='max_product');bp_pred=lng.read_transport_modes(bp,n1)
   pred=[1. if part_state[v]>=0 else -1. for v in dst];jt_pred=[1. if jt_state[v]>=0 else -1. for v in dst]
   after=cjt.can_network_from_mt(sub,mt);state_after={nid(v):float(sub.node(v)['attrs'].get('state',0.)) for v in n0+n1};unmutated=(set(after['nodes'])==set(nodes) and {tuple(sorted(map(nid,k))):float(v) for k,v in after['pairwise'].items()}==p and {nid(k):float(v) for k,v in after['unary'].items()}==u and state_before==state_after)
   rows.append({'heldout_index':i,'condition':cond,'nodes':len(nodes),'edges':len(edges),'width':int(order['treewidth']),'certified_width':width,'connected':connected(nodes,edges),
    'jt_energy':float(jt['energy']),'jt_direct_rescore':jt_energy,'conditioned_energy':part_energy,'conditioned_direct_rescore':direct,
    'conditioned_state_valid':all(v in VOCAB for v in part_state.values()),'conditioned_repeat_stable':part_state==trace_state and abs(part_energy-trace_energy)<TOL,'conditioned_prediction':pred,'jt_prediction':jt_pred,'bp_prediction':[float(v) for v in bp_pred],'target':target.tolist(),
    'conditioned_accuracy':float(np.mean(np.asarray(pred)==target)),'bp_accuracy':float(np.mean(np.asarray(bp_pred)==target)),
    'timing_ns':{'junction_tree':jt_ns,'conditioned_solver':part_ns},'conditioned_traced_peak_bytes':peak,'no_mutation':unmutated})
 return {'replicate':rep,'pid':os.getpid(),'rows':rows,'source_start':start,'source_end':sources(),'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
def main():
 args=sys.argv[1:]
 if args[:1]==['--worker']:print(json.dumps(worker(int(args[1])),sort_keys=True,separators=(',',':')));return 0
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite lock/capture')
  LOCK.write_text(json.dumps({'schema':'LlmTransportRoleSeparatorV1Lock','sources':sources()},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if args!=['--run']:raise SystemExit('usage: --lock, --run, or --worker REP')
 lock=json.loads(LOCK.read_text());before=sources()
 if before!=lock['sources']:raise SystemExit('source drift from lock')
 from domains.engine_provenance import build_is_stale
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit('native engine stale: '+'; '.join(stale))
 env={**os.environ,'PYTHONPATH':f"{ROOT/'runners/dsl/python'}:{ROOT}:{os.environ.get('PYTHONPATH','')}"};runs=[];fail=[]
 for rep in range(R):
  p=subprocess.run([sys.executable,str(RUNNER),'--worker',str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=1200)
  if p.returncode:fail.append({'replicate':rep,'error':p.stderr[-3000:]});continue
  x=json.loads(p.stdout);runs.append(x);print(f"rep={rep} pid={x['pid']} cells={len(x['rows'])}",flush=True)
 after=sources();cells=[q for x in runs for q in x['rows']]
 checks={'three_fresh_workers':len(runs)==R and len({x['pid'] for x in runs})==R,'no_failures':not fail,'full_coverage':all(len(x['rows'])==20 for x in runs),
 'expected_connected_width8_graphs':all(x['connected'] and x['width']==x['certified_width']==8 for x in cells),'energy_parity':all(abs(x['jt_energy']-x['conditioned_energy'])<TOL and abs(x['jt_energy']-x['conditioned_direct_rescore'])<TOL for x in cells),
 'state_validity':all(x['conditioned_state_valid'] for x in cells),'no_mutation':all(x['no_mutation'] for x in cells),'source_stable':before==lock['sources']==after and all(x['source_start']==lock['sources']==x['source_end'] for x in runs)}
 OUT.write_text(json.dumps({'schema':'LlmTransportRoleSeparatorV1Capture','lock_sha256':hashlib.sha256(LOCK.read_bytes()).hexdigest(),'sources':before,'post_run_sources':after,'checks':checks,'failures':fail,'runs':runs},indent=2,sort_keys=True)+'\n');print(json.dumps({'checks':checks,'capture':OUT.relative_to(ROOT).as_posix()},indent=2));return 0 if all(checks.values()) else 1
if __name__=='__main__':raise SystemExit(main())
