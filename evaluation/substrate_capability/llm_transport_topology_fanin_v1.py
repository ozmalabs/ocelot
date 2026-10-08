#!/usr/bin/env python3
"""Measure exact-inference cost and signal under learned transport sparsity."""
from __future__ import annotations
import hashlib,itertools,json,os,platform,resource,statistics,subprocess,sys,time
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT)]
EXPORT=Path('/applications/data/model_graph_work/transport_L12_13.npz')
RUNNER=Path(__file__).resolve();PROTOCOL=ROOT/'docs/research/engine_substrate/LLM_TRANSPORT_TOPOLOGY_FANIN_V1_PREREG_20261002.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_llm_transport_topology_fanin_v1.py'
PRIOR_SCALE=ROOT/'evaluation/reports/llm_transport_treewidth_scale_v1_20261002.json'
PRIOR_COST=ROOT/'evaluation/reports/llm_transport_task_graph_cost_v1_20261002.json'
SEED=ROOT/'seeds/can_native_reimplementation.json'
LOCK=ROOT/'evaluation/substrate_capability/llm_transport_topology_fanin_v1_lock_20261002.json'
OUT=ROOT/'evaluation/reports/llm_transport_topology_fanin_v1_20261002.json'
REPLICATES=3;K=8;FANINS=(1,2,4,8);VOCAB=(-1.0,0.0,1.0);TOL=1e-8
def digest(p):
 b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def source_lock():
 from substrate_rs import _native
 return {'runner':digest(RUNNER),'protocol':digest(PROTOCOL),'analyzer':digest(ANALYZER),'prior_scale_capture':digest(PRIOR_SCALE),'prior_cost_capture':digest(PRIOR_COST),'seed':digest(SEED),
  'sources':[digest(ROOT/p) for p in ('domains/llm_native_graph.py','domains/can_junction_tree.py','domains/graph_treewidth.py','domains/can_native_bp.py')],
  'native_binary':digest(Path(_native.__file__).resolve()),'native_build_manifest':digest(ROOT/'runners/dsl/python/substrate_rs/_native.build.json'),
  'export':digest(EXPORT),'replicates':REPLICATES,'mode_count':K,'fanins':list(FANINS),'vocabulary':list(VOCAB),'ridge':1.0,'tolerance':TOL}
def nid(v):return int(v.value if hasattr(v,'value') else v)
def direct_energy(state,unary,pair):
 return -sum(float(h)*float(state[v]) for v,h in unary.items())-sum(float(w)*float(state[a])*float(state[b]) for (a,b),w in pair.items())
def oracle(src,dst,unary,pair):
 states=np.asarray(list(itertools.product(VOCAB,repeat=K)),dtype=float);sp={v:i for i,v in enumerate(src)};dp={v:i for i,v in enumerate(dst)};J=np.zeros((K,K))
 for (a,b),w in pair.items():
  if a in sp and b in dp:J[dp[b],sp[a]]=float(w)
  elif b in sp and a in dp:J[dp[a],sp[b]]=float(w)
  else:raise ValueError('unexpected non-bipartite factor')
 h0=np.asarray([unary[v] for v in src]);h1=np.asarray([unary[v] for v in dst]);drive=states@J.T+h1
 scores=-drive[:,:,None]*np.asarray(VOCAB)[None,None,:];ix=np.argmin(scores,axis=2);total=-(states@h0)+np.take_along_axis(scores,ix[:,:,None],axis=2)[:,:,0].sum(axis=1)
 best=int(np.argmin(total));return float(total[best]),np.asarray(VOCAB)[ix[best]].tolist()
def components(nodes,edges):
 adj={v:set() for v in nodes}
 for a,b in edges:adj[a].add(b);adj[b].add(a)
 unseen=set(nodes);out=[]
 while unseen:
  root=next(iter(unseen));seen={root};stack=[root]
  while stack:
   u=stack.pop()
   for v in adj[u]-seen:seen.add(v);stack.append(v)
  unseen-=seen;out.append(len(seen))
 return sorted(out)
def worker(rep):
 import substrate_rs as sr
 import domains.can_junction_tree as cjt
 from domains.graph_treewidth import min_fill_upper_bound,build_elimination_triangulation
 from domains.can_native_bp import run_loopy_bp
 from domains import llm_native_graph as lng
 before=source_lock();z=np.load(EXPORT);T=lng.fit_transport(z['tr_c0'],z['tr_c1'],ridge=1.0);rows=[]
 for i,(x0,x1) in enumerate(zip(z['ho_c0'],z['ho_c1'])):
  dom0=np.argsort(-np.abs(x0))[:K]
  for r in FANINS:
   W=np.zeros_like(T)
   for target in range(K):
    vals=np.abs(T[target,dom0]);keep=np.argsort(-vals,kind='stable')[:r];W[target,dom0[keep]]=T[target,dom0[keep]]
   sub=sr.Substrate();t=time.perf_counter_ns();mt,n0,n1,d0,d1=lng.build_transport_factor_graph(sub,[str(SEED)],W,x0,n_modes0=K,n_modes1=K,temperature=1.0,field_scale=1.0,transport_scale=1.0,discrete_mode='3state',bidirectional=True);build_ns=time.perf_counter_ns()-t
   t=time.perf_counter_ns();net=cjt.can_network_from_mt(sub,mt);extract_ns=time.perf_counter_ns()-t
   nodes=list(net['nodes']);edges=list(net['edges']);unary=dict(net['unary']);pair={tuple(sorted(e)):float(w) for e,w in net['pairwise'].items()};src=[nid(v) for v in n0];dst=[nid(v) for v in n1]
   expected_u={src[j]:float(x0[d0[j]]) for j in range(K)};expected_u.update({v:0.0 for v in dst})
   expected_p={tuple(sorted((src[j],dst[q]))):float(W[d1[q],d0[j]]) for j in range(K) for q in range(K) if float(W[d1[q],d0[j]])!=0.0}
   extraction=(set(unary)==set(expected_u) and all(abs(unary[a]-b)<TOL for a,b in expected_u.items()) and set(pair)==set(expected_p) and all(abs(pair[a]-b)<TOL for a,b in expected_p.items()) and net['discrete_mode']=='3state' and tuple(net['vocab'])==VOCAB)
   sig=(dict(unary),dict(pair),tuple(nodes),tuple(sorted(tuple(sorted(e)) for e in edges)));state0={nid(v):float(sub.node(v)['attrs'].get('state',0.0)) for v in n0+n1}
   t=time.perf_counter_ns();mf=min_fill_upper_bound(nodes,edges);order_ns=time.perf_counter_ns()-t;tri=build_elimination_triangulation(nodes,edges,mf['elimination_order']);width=max((len(b)-1 for b in tri['bags'].values()),default=0)
   t=time.perf_counter_ns();jt=cjt.junction_tree_map(nodes,edges,unary,{frozenset(e):w for e,w in pair.items()},VOCAB,order=mf['elimination_order']);jt_ns=time.perf_counter_ns()-t
   state={nid(v):float(jt['state'][nid(v)]) for v in nodes};rescore=direct_energy(state,unary,pair);exact_pred=[1.0 if state[v]>=0 else -1.0 for v in dst];oracle_e,oracle_pred=oracle(src,dst,unary,pair)
   t=time.perf_counter_ns();bp=run_loopy_bp(sub,mt,combine='max_product');bp_ns=time.perf_counter_ns()-t;bp_pred=lng.read_transport_modes(bp,n1).tolist()
   linear_drive=W[:K,dom0]@x0[dom0];linear_pred=np.where(linear_drive>=0,1.0,-1.0).tolist();post=cjt.can_network_from_mt(sub,mt);state1={nid(v):float(sub.node(v)['attrs'].get('state',0.0)) for v in n0+n1}
   after=(dict(post['unary']),{tuple(sorted(e)):float(v) for e,v in post['pairwise'].items()},tuple(post['nodes']),tuple(sorted(tuple(sorted(e)) for e in post['edges'])))
   target=np.where(x1[:K]>=0,1.0,-1.0);local={nid(v):j for j,v in enumerate(n0+n1)};topo=hashlib.sha256(json.dumps(sorted(tuple(sorted((local[a],local[b]))) for a,b in edges)).encode()).hexdigest()
   rows.append({'heldout_index':i,'fan_in':r,'nodes':len(nodes),'edges':len(edges),'pair_factors':len(pair),'component_sizes':components(nodes,edges),'topology_signature':topo,'width':int(mf['treewidth']),'triangulation_width':width,'exact_extraction':extraction,
    'jt_energy':float(jt['energy']),'oracle_energy':oracle_e,'direct_rescore':rescore,'oracle_prediction':oracle_pred,'exact_prediction':exact_pred,'bp_prediction':bp_pred,'linear_prediction':linear_pred,'target':target.tolist(),
    'exact_accuracy':float(np.mean(np.asarray(exact_pred)==target)),'bp_accuracy':float(np.mean(np.asarray(bp_pred)==target)),'linear_accuracy':float(np.mean(np.asarray(linear_pred)==target)),
    'no_mutation':sig==after and state0==state1,'timing_ns':{'graph_construction':build_ns,'factor_extraction':extract_ns,'minfill_order':order_ns,'junction_tree':jt_ns,'belief_propagation':bp_ns}})
 end=source_lock();return {'replicate':rep,'worker_pid':os.getpid(),'input_cells':len(rows),'rows':rows,'source_lock_start':before,'source_lock_end':end,'process_peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
def main():
 args=sys.argv[1:]
 if args[:1]==['--worker']:
  print(json.dumps(worker(int(args[1])),sort_keys=True,separators=(',',':')));return 0
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite lock/capture')
  LOCK.write_text(json.dumps({'schema':'LlmTransportTopologyFaninV1Lock','sources':source_lock()},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if args!=['--run']:raise SystemExit('usage: --lock, --run, or --worker REP')
 lock=json.loads(LOCK.read_text())
 if source_lock()!=lock['sources']:raise SystemExit('source/export drift from lock')
 from domains.engine_provenance import build_is_stale
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit('native engine stale: '+'; '.join(stale))
 env={**os.environ,'PYTHONPATH':f"{ROOT/'runners/dsl/python'}:{ROOT}:{os.environ.get('PYTHONPATH','')}"};runs=[];failures=[]
 for rep in range(REPLICATES):
  try:
   p=subprocess.run([sys.executable,str(RUNNER),'--worker',str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=900)
   if p.returncode:raise RuntimeError(p.stderr[-3000:])
   r=json.loads(p.stdout.strip());runs.append(r);print(f"rep={rep} pid={r['worker_pid']} cells={len(r['rows'])} r1_width={statistics.median(c['width'] for c in r['rows'] if c['fan_in']==1)}",flush=True)
  except Exception as e:failures.append({'replicate':rep,'error':type(e).__name__+': '+str(e)})
 post=source_lock();cells=[c for run in runs for c in run['rows']]
 checks={'three_fresh_workers':len(runs)==3 and len({r['worker_pid'] for r in runs})==len(runs),'no_failures':not failures,'full_grid':all(r['input_cells']==40 and len(r['rows'])==40 for r in runs),
  'expected_graph_nodes':all(c['nodes']==16 for c in cells),'retained_edge_counts':all(c['pair_factors']==8*c['fan_in'] for c in cells),'width_certificates':all(c['width']==c['triangulation_width'] for c in cells),
  'exact_factor_extraction':all(c['exact_extraction'] for c in cells),'jt_oracle_rescore':all(abs(c['jt_energy']-c['oracle_energy'])<TOL and abs(c['direct_rescore']-c['oracle_energy'])<TOL for c in cells),
  'valid_predictions':all(all(len(c[k])==K for k in ('exact_prediction','bp_prediction','linear_prediction','target')) for c in cells),'no_mutation':all(c['no_mutation'] for c in cells),
  'worker_locks':all(r['source_lock_start']==lock['sources']==r['source_lock_end'] for r in runs),'pre_post_lock':post==lock['sources']}
 OUT.write_text(json.dumps({'schema':'LlmTransportTopologyFaninV1Results','lock_sha256':hashlib.sha256(LOCK.read_bytes()).hexdigest(),'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),'sources':source_lock(),'post_run_sources':post,'configuration':{'replicates':REPLICATES,'heldout_inputs':10,'mode_count':K,'fanins':FANINS,'vocabulary':VOCAB,'ridge':1.0},'checks':checks,'failures':failures,'runs':runs},indent=2,sort_keys=True)+'\n')
 print(json.dumps({'capture':OUT.relative_to(ROOT).as_posix(),'checks':checks,'failure_count':len(failures)},indent=2))
 if not all(checks.values()):raise SystemExit('transport topology fan-in experiment failed')
 return 0
if __name__=='__main__':raise SystemExit(main())
