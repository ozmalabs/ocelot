#!/usr/bin/env python3
"""Untangled timing/allocation profile for model-derived transport inference."""
from __future__ import annotations
import hashlib,itertools,json,os,platform,resource,subprocess,sys,time,tracemalloc
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT)]
EXPORT=Path('/applications/data/model_graph_work/transport_L12_13.npz')
RUNNER=Path(__file__).resolve();PROTOCOL=ROOT/'docs/research/engine_substrate/LLM_TRANSPORT_TASK_GRAPH_COST_V1_PREREG_20261002.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_llm_transport_task_graph_cost_v1.py'
PRIOR=ROOT/'evaluation/reports/llm_transport_task_graph_exact_census_v1_1_20261002.json'
SEED=ROOT/'seeds/can_native_reimplementation.json'
LOCK=ROOT/'evaluation/substrate_capability/llm_transport_task_graph_cost_v1_lock_20261002.json'
OUT=ROOT/'evaluation/reports/llm_transport_task_graph_cost_v1_20261002.json'
REPLICATES=3;K=8;VOCAB=(-1.0,0.0,1.0);TOL=1e-8
def digest(p):
 b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def source_lock():
 from substrate_rs import _native
 return {'runner':digest(RUNNER),'protocol':digest(PROTOCOL),'analyzer':digest(ANALYZER),'prior_exact_capture':digest(PRIOR),'seed':digest(SEED),
  'sources':[digest(ROOT/p) for p in ('domains/llm_native_graph.py','domains/can_junction_tree.py','domains/graph_treewidth.py','domains/can_native_bp.py')],
  'native_binary':digest(Path(_native.__file__).resolve()),'native_build_manifest':digest(ROOT/'runners/dsl/python/substrate_rs/_native.build.json'),
  'export':digest(EXPORT),'replicates':REPLICATES,'mode_count':K,'vocabulary':list(VOCAB),'ridge':1.0,'shuffle_seed':0,'tolerance':TOL}
def nid(v):return int(v.value if hasattr(v,'value') else v)
def energy(state,unary,pair):
 return -sum(float(h)*float(state[v]) for v,h in unary.items())-sum(float(w)*float(state[a])*float(state[b]) for (a,b),w in pair.items())
def connect(nodes,edges):
 adj={v:set() for v in nodes}
 for a,b in edges:adj[a].add(b);adj[b].add(a)
 seen={nodes[0]};stack=[nodes[0]]
 while stack:
  u=stack.pop()
  for v in adj[u]-seen:seen.add(v);stack.append(v)
 return len(seen)==len(nodes)
def worker(rep):
 import substrate_rs as sr
 import domains.can_junction_tree as cjt
 from domains.graph_treewidth import min_fill_upper_bound,build_elimination_triangulation
 from domains.can_native_bp import run_loopy_bp
 from domains import llm_native_graph as lng
 before=source_lock();z=np.load(EXPORT);T=lng.fit_transport(z['tr_c0'],z['tr_c1'],ridge=1.0)
 flat=T.flatten().copy();np.random.default_rng(0).shuffle(flat);Ts=flat.reshape(T.shape);rows=[]
 for i,(x0,x1) in enumerate(zip(z['ho_c0'],z['ho_c1'])):
  target=np.where(x1[:K]>=0,1.0,-1.0)
  for cond,weights in (('learned',T),('shuffled',Ts)):
   t=time.perf_counter_ns();sub=sr.Substrate();substrate_ns=time.perf_counter_ns()-t
   t=time.perf_counter_ns();mt,n0,n1,d0,d1=lng.build_transport_factor_graph(sub,[str(SEED)],weights,x0,n_modes0=K,n_modes1=K,temperature=1.0,field_scale=1.0,transport_scale=1.0,discrete_mode='3state',bidirectional=True);build_ns=time.perf_counter_ns()-t
   t=time.perf_counter_ns();net=cjt.can_network_from_mt(sub,mt);extract_ns=time.perf_counter_ns()-t
   nodes=list(net['nodes']);edges=list(net['edges']);unary=dict(net['unary']);pair={tuple(sorted(k)):float(v) for k,v in net['pairwise'].items()}
   expected_u={nid(n0[j]):float(x0[d0[j]]) for j in range(K)};expected_u.update({nid(v):0.0 for v in n1})
   expected_p={tuple(sorted((nid(n0[j]),nid(n1[k])))):float(weights[d1[k],d0[j]]) for j in range(K) for k in range(K) if float(weights[d1[k],d0[j]])!=0.0}
   extraction_exact=(set(unary)==set(expected_u) and all(abs(unary[k]-v)<TOL for k,v in expected_u.items()) and set(pair)==set(expected_p) and all(abs(pair[k]-v)<TOL for k,v in expected_p.items()) and net['discrete_mode']=='3state' and tuple(net['vocab'])==VOCAB)
   state_before={nid(v):float(sub.node(v)['attrs'].get('state',0.0)) for v in n0+n1}
   node_pos={nid(v):j for j,v in enumerate(n0+n1)}
   topology=hashlib.sha256(json.dumps(sorted(tuple(sorted((node_pos[a],node_pos[b]))) for a,b in edges)).encode()).hexdigest()
   before_sig=(dict(unary),dict(pair),tuple(nodes),tuple(sorted(tuple(sorted(e)) for e in edges)))
   t=time.perf_counter_ns();mf=min_fill_upper_bound(nodes,edges);order_ns=time.perf_counter_ns()-t
   tri=build_elimination_triangulation(nodes,edges,mf['elimination_order']);tri_width=max((len(b)-1 for b in tri['bags'].values()),default=0)
   jt_args=(nodes,edges,unary,{frozenset(k):v for k,v in pair.items()},VOCAB)
   t=time.perf_counter_ns();jt=cjt.junction_tree_map(*jt_args,order=mf['elimination_order']);jt_ns=time.perf_counter_ns()-t
   state={nid(v):float(jt['state'][nid(v)]) for v in nodes};direct=energy(state,unary,pair);exact_pred=np.asarray([1.0 if state[nid(v)]>=0 else -1.0 for v in n1])
   t=time.perf_counter_ns();bp=run_loopy_bp(sub,mt,combine='max_product');bp_ns=time.perf_counter_ns()-t;bp_pred=lng.read_transport_modes(bp,n1)
   tracemalloc.start();tracemalloc.reset_peak();profile_jt=cjt.junction_tree_map(*jt_args,order=mf['elimination_order']);_,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
   profile_energy=energy({nid(v):float(profile_jt['state'][nid(v)]) for v in nodes},unary,pair)
   re=cjt.can_network_from_mt(sub,mt);after={nid(v):float(sub.node(v)['attrs'].get('state',0.0)) for v in n0+n1}
   after_sig=(dict(re['unary']),{tuple(sorted(k)):float(v) for k,v in re['pairwise'].items()},tuple(re['nodes']),tuple(sorted(tuple(sorted(e)) for e in re['edges'])))
   rows.append({'heldout_index':i,'condition':cond,'target':target.tolist(),'nodes':len(nodes),'edges':len(edges),'pair_factors':len(pair),'connected':connect(nodes,edges),
    'width':int(mf['treewidth']),'triangulation_width':tri_width,'topology_signature':topology,'exact_extraction':extraction_exact,'exact_energy':float(jt['energy']),'direct_energy':direct,'profile_energy':float(profile_energy),
    'exact_prediction':exact_pred.tolist(),'bp_prediction':np.asarray(bp_pred,dtype=float).tolist(),
    'exact_accuracy':float(np.mean(exact_pred==target)),'bp_accuracy':float(np.mean(np.asarray(bp_pred)==target)),
    'no_mutation':before_sig==after_sig and state_before==after,'traced_peak_bytes':peak,
    'timing_ns':{'substrate_init':substrate_ns,'graph_construction':build_ns,'factor_extraction':extract_ns,'minfill_order':order_ns,'junction_tree_uninstrumented':jt_ns,'belief_propagation':bp_ns}})
 after_lock=source_lock()
 return {'replicate':rep,'worker_pid':os.getpid(),'input_rows':len(rows),'rows':rows,'source_lock_start':before,'source_lock_end':after_lock,'process_peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
def main():
 args=sys.argv[1:]
 if args[:1]==['--worker']:
  print(json.dumps(worker(int(args[1])),sort_keys=True,separators=(',',':')));return 0
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite lock/capture')
  LOCK.write_text(json.dumps({'schema':'LlmTransportTaskGraphCostV1Lock','sources':source_lock()},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if args!=['--run']:raise SystemExit('usage: --lock, --run, or --worker REP')
 lock=json.loads(LOCK.read_text())
 if source_lock()!=lock['sources']:raise SystemExit('source/export drift from lock')
 from domains.engine_provenance import build_is_stale
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit('native engine is stale: '+'; '.join(stale))
 env={**os.environ,'PYTHONPATH':f"{ROOT/'runners/dsl/python'}:{ROOT}:{os.environ.get('PYTHONPATH','')}"};runs=[];failures=[]
 for rep in range(REPLICATES):
  try:
   p=subprocess.run([sys.executable,str(RUNNER),'--worker',str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=1200)
   if p.returncode:raise RuntimeError(p.stderr[-3000:])
   r=json.loads(p.stdout.strip());runs.append(r);x=[c for c in r['rows'] if c['condition']=='learned'];print(f"rep={rep} pid={r['worker_pid']} cells={len(r['rows'])} width={x[0]['width']} learned_exact={np.mean([c['exact_accuracy'] for c in x]):.3f}",flush=True)
  except Exception as e:failures.append({'replicate':rep,'error':type(e).__name__+': '+str(e)})
 post=source_lock();cells=[c for r in runs for c in r['rows']]
 paired_topology=all(r['rows'][2*i]['heldout_index']==r['rows'][2*i+1]['heldout_index'] and r['rows'][2*i]['condition']=='learned' and r['rows'][2*i+1]['condition']=='shuffled' and r['rows'][2*i]['topology_signature']==r['rows'][2*i+1]['topology_signature'] for r in runs for i in range(10))
 checks={'replicates':len(runs)==REPLICATES,'no_failures':not failures,'fresh_workers':len({r['worker_pid'] for r in runs})==len(runs),'full_coverage':all(r['input_rows']==20 and len(r['rows'])==20 for r in runs),
  'paired_topology_identical':paired_topology,
  'expected_connected_graphs':all(c['connected'] and c['nodes']==16 and c['pair_factors']==64 for c in cells),'exact_extraction':all(c['exact_extraction'] for c in cells),
  'width_certificates':all(c['width']==c['triangulation_width'] for c in cells),'energy_reconciles':all(abs(c['exact_energy']-c['direct_energy'])<TOL and abs(c['profile_energy']-c['exact_energy'])<TOL for c in cells),
  'prediction_vectors':all(len(c['exact_prediction'])==len(c['bp_prediction'])==len(c['target'])==K for c in cells),'no_mutation':all(c['no_mutation'] for c in cells),
  'worker_locks':all(r['source_lock_start']==lock['sources']==r['source_lock_end'] for r in runs),'pre_post_lock':post==lock['sources']}
 OUT.write_text(json.dumps({'schema':'LlmTransportTaskGraphCostV1Results','lock_sha256':hashlib.sha256(LOCK.read_bytes()).hexdigest(),'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),'sources':source_lock(),'post_run_sources':post,'configuration':{'replicates':REPLICATES,'rows_per_worker':10,'conditions':['learned','shuffled'],'modes':K,'vocabulary':VOCAB},'checks':checks,'failures':failures,'runs':runs},indent=2,sort_keys=True)+'\n')
 print(json.dumps({'capture':OUT.relative_to(ROOT).as_posix(),'checks':checks,'failure_count':len(failures)},indent=2))
 if not all(checks.values()):raise SystemExit('transport cost profile failed')
 return 0
if __name__=='__main__':raise SystemExit(main())
