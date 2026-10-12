#!/usr/bin/env python3
"""Exact inference cost/accuracy across widths in a learned transport graph."""
from __future__ import annotations
import hashlib,itertools,json,os,platform,resource,subprocess,sys,time
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT)]
EXPORT=Path('/applications/data/model_graph_work/transport_L12_13.npz')
RUNNER=Path(__file__).resolve();PROTOCOL=ROOT/'docs/research/engine_substrate/LLM_TRANSPORT_TREEWIDTH_SCALE_V1_PREREG_20261002.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_llm_transport_treewidth_scale_v1.py'
PRIOR_COST=ROOT/'evaluation/reports/llm_transport_task_graph_cost_v1_20261002.json'
PRIOR_EXACT=ROOT/'evaluation/reports/llm_transport_task_graph_exact_census_v1_1_20261002.json'
SEED=ROOT/'seeds/can_native_reimplementation.json'
LOCK=ROOT/'evaluation/substrate_capability/llm_transport_treewidth_scale_v1_lock_20261002.json'
OUT=ROOT/'evaluation/reports/llm_transport_treewidth_scale_v1_20261002.json'
REPLICATES=3;WIDTHS=(1,2,4,6,8,10);VOCAB=(-1.0,0.0,1.0);TOL=1e-8
def digest(p):
 b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def source_lock():
 from substrate_rs import _native
 return {'runner':digest(RUNNER),'protocol':digest(PROTOCOL),'analyzer':digest(ANALYZER),'prior_cost_capture':digest(PRIOR_COST),'prior_exact_capture':digest(PRIOR_EXACT),'seed':digest(SEED),
  'sources':[digest(ROOT/p) for p in ('domains/llm_native_graph.py','domains/can_junction_tree.py','domains/graph_treewidth.py','domains/can_native_bp.py')],
  'native_binary':digest(Path(_native.__file__).resolve()),'native_build_manifest':digest(ROOT/'runners/dsl/python/substrate_rs/_native.build.json'),
  'export':digest(EXPORT),'replicates':REPLICATES,'widths':list(WIDTHS),'vocabulary':list(VOCAB),'ridge':1.0,'tolerance':TOL}
def nid(v):return int(v.value if hasattr(v,'value') else v)
def direct_energy(state,unary,pair):
 return -sum(float(h)*float(state[v]) for v,h in unary.items())-sum(float(w)*float(state[a])*float(state[b]) for (a,b),w in pair.items())
def exhaustive_bipartite_oracle(src_ids,dst_ids,unary,pair):
 """Enumerate source assignments, conditionally optimize independent targets."""
 k=len(src_ids);pos={v:i for i,v in enumerate(src_ids)};dpos={v:i for i,v in enumerate(dst_ids)}
 J=np.zeros((k,k),dtype=np.float64)
 for (a,b),w in pair.items():
  if a in pos and b in dpos:J[dpos[b],pos[a]]=float(w)
  elif b in pos and a in dpos:J[dpos[a],pos[b]]=float(w)
  else:raise ValueError('factor is not cross-partition')
 states=np.asarray(list(itertools.product(VOCAB,repeat=k)),dtype=np.float64)
 hs=np.asarray([float(unary[v]) for v in src_ids]);hd=np.asarray([float(unary[v]) for v in dst_ids])
 source_energy=-(states@hs)
 drives=states@J.T+hd[None,:]
 target_scores=-drives[:,:,None]*np.asarray(VOCAB,dtype=np.float64)[None,None,:]
 target_ix=np.argmin(target_scores,axis=2);target_energy=np.take_along_axis(target_scores,target_ix[:,:,None],axis=2)[:,:,0].sum(axis=1)
 total=source_energy+target_energy;best=int(np.argmin(total));pred=np.asarray(VOCAB,dtype=np.float64)[target_ix[best]]
 return float(total[best]),pred.tolist(),len(states)
def connected(nodes,edges):
 adj={v:set() for v in nodes}
 for a,b in edges:adj[a].add(b);adj[b].add(a)
 if not nodes:return False
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
 before=source_lock();z=np.load(EXPORT);T=lng.fit_transport(z['tr_c0'],z['tr_c1'],ridge=1.0);rows=[]
 for i,(x0,x1) in enumerate(zip(z['ho_c0'],z['ho_c1'])):
  for k in WIDTHS:
   t=time.perf_counter_ns();sub=sr.Substrate();init_ns=time.perf_counter_ns()-t
   t=time.perf_counter_ns();mt,n0,n1,d0,d1=lng.build_transport_factor_graph(sub,[str(SEED)],T,x0,n_modes0=k,n_modes1=k,temperature=1.0,field_scale=1.0,transport_scale=1.0,discrete_mode='3state',bidirectional=True);build_ns=time.perf_counter_ns()-t
   t=time.perf_counter_ns();net=cjt.can_network_from_mt(sub,mt);extract_ns=time.perf_counter_ns()-t
   nodes=list(net['nodes']);edges=list(net['edges']);unary=dict(net['unary']);pair={tuple(sorted(e)):float(w) for e,w in net['pairwise'].items()}
   src=[nid(v) for v in n0];dst=[nid(v) for v in n1]
   expected_u={src[j]:float(x0[d0[j]]) for j in range(k)};expected_u.update({v:0.0 for v in dst})
   expected_p={tuple(sorted((src[j],dst[q]))):float(T[d1[q],d0[j]]) for j in range(k) for q in range(k) if float(T[d1[q],d0[j]])!=0.0}
   exact_extract=(set(unary)==set(expected_u) and all(abs(unary[a]-b)<TOL for a,b in expected_u.items()) and set(pair)==set(expected_p) and all(abs(pair[a]-b)<TOL for a,b in expected_p.items()) and net['discrete_mode']=='3state' and tuple(net['vocab'])==VOCAB)
   before_sig=(dict(unary),dict(pair),tuple(nodes),tuple(sorted(tuple(sorted(e)) for e in edges)));state0={nid(v):float(sub.node(v)['attrs'].get('state',0.0)) for v in n0+n1}
   t=time.perf_counter_ns();mf=min_fill_upper_bound(nodes,edges);order_ns=time.perf_counter_ns()-t
   tri=build_elimination_triangulation(nodes,edges,mf['elimination_order']);cert=max((len(b)-1 for b in tri['bags'].values()),default=0)
   t=time.perf_counter_ns();jt=cjt.junction_tree_map(nodes,edges,unary,{frozenset(e):w for e,w in pair.items()},VOCAB,order=mf['elimination_order']);jt_ns=time.perf_counter_ns()-t
   state={nid(v):float(jt['state'][nid(v)]) for v in nodes};rescore=direct_energy(state,unary,pair);prediction=[1.0 if state[v]>=0 else -1.0 for v in dst]
   oracle,oracle_pred,oracle_assignments=exhaustive_bipartite_oracle(src,dst,unary,pair)
   t=time.perf_counter_ns();bp=run_loopy_bp(sub,mt,combine='max_product');bp_ns=time.perf_counter_ns()-t;bp_pred=lng.read_transport_modes(bp,n1).tolist()
   post=cjt.can_network_from_mt(sub,mt);after_sig=(dict(post['unary']),{tuple(sorted(e)):float(w) for e,w in post['pairwise'].items()},tuple(post['nodes']),tuple(sorted(tuple(sorted(e)) for e in post['edges'])))
   state1={nid(v):float(sub.node(v)['attrs'].get('state',0.0)) for v in n0+n1};target=np.where(x1[:k]>=0,1.0,-1.0)
   pos={nid(v):q for q,v in enumerate(n0+n1)};topo=hashlib.sha256(json.dumps(sorted(tuple(sorted((pos[a],pos[b]))) for a,b in edges)).encode()).hexdigest()
   rows.append({'heldout_index':i,'k':k,'nodes':len(nodes),'edges':len(edges),'pair_factors':len(pair),'connected':connected(nodes,edges),'topology_signature':topo,
    'width':int(mf['treewidth']),'triangulation_width':cert,'exact_extraction':exact_extract,'jt_energy':float(jt['energy']),'direct_rescore':rescore,'oracle_energy':oracle,'oracle_target_prediction':oracle_pred,'oracle_source_assignments':oracle_assignments,
    'exact_prediction':prediction,'bp_prediction':bp_pred,'target':target.tolist(),'exact_accuracy':float(np.mean(np.asarray(prediction)==target)),'bp_accuracy':float(np.mean(np.asarray(bp_pred)==target)),
    'no_mutation':before_sig==after_sig and state0==state1,'timing_ns':{'substrate_init':init_ns,'graph_construction':build_ns,'factor_extraction':extract_ns,'minfill_order':order_ns,'junction_tree':jt_ns,'belief_propagation':bp_ns}})
 end=source_lock()
 return {'replicate':rep,'worker_pid':os.getpid(),'input_cells':len(rows),'rows':rows,'source_lock_start':before,'source_lock_end':end,'process_peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
def main():
 args=sys.argv[1:]
 if args[:1]==['--worker']:
  print(json.dumps(worker(int(args[1])),sort_keys=True,separators=(',',':')));return 0
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite lock/capture')
  LOCK.write_text(json.dumps({'schema':'LlmTransportTreewidthScaleV1Lock','sources':source_lock()},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if args!=['--run']:raise SystemExit('usage: --lock, --run, or --worker REP')
 lock=json.loads(LOCK.read_text())
 if source_lock()!=lock['sources']:raise SystemExit('source/export drift from lock')
 from domains.engine_provenance import build_is_stale
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit('native engine is stale: '+'; '.join(stale))
 env={**os.environ,'PYTHONPATH':f"{ROOT/'runners/dsl/python'}:{ROOT}:{os.environ.get('PYTHONPATH','')}"};runs=[];failures=[]
 for rep in range(REPLICATES):
  try:
   p=subprocess.run([sys.executable,str(RUNNER),'--worker',str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=1800)
   if p.returncode:raise RuntimeError(p.stderr[-3000:])
   r=json.loads(p.stdout.strip());runs.append(r);print(f"rep={rep} pid={r['worker_pid']} cells={len(r['rows'])} k10_jt_ms={np.median([q['timing_ns']['junction_tree']/1e6 for q in r['rows'] if q['k']==10]):.1f}",flush=True)
  except Exception as e:failures.append({'replicate':rep,'error':type(e).__name__+': '+str(e)})
 post=source_lock();cells=[c for r in runs for c in r['rows']]
 checks={'three_fresh_workers':len(runs)==3 and len({r['worker_pid'] for r in runs})==len(runs),'no_failures':not failures,'full_grid':all(r['input_cells']==60 and len(r['rows'])==60 for r in runs),
  'all_connected':all(c['connected'] for c in cells),'exact_factor_extraction':all(c['exact_extraction'] for c in cells),'width_certificates':all(c['width']==c['triangulation_width'] for c in cells),
  'jt_oracle_rescore':all(abs(c['jt_energy']-c['oracle_energy'])<TOL and abs(c['direct_rescore']-c['oracle_energy'])<TOL for c in cells),'valid_vectors':all(len(c['exact_prediction'])==len(c['bp_prediction'])==len(c['target'])==c['k'] for c in cells),
  'no_mutation':all(c['no_mutation'] for c in cells),'worker_locks':all(r['source_lock_start']==lock['sources']==r['source_lock_end'] for r in runs),'pre_post_lock':post==lock['sources']}
 OUT.write_text(json.dumps({'schema':'LlmTransportTreewidthScaleV1Results','lock_sha256':hashlib.sha256(LOCK.read_bytes()).hexdigest(),'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),'sources':source_lock(),'post_run_sources':post,'configuration':{'replicates':REPLICATES,'heldout_inputs':10,'mode_counts':WIDTHS,'vocabulary':VOCAB,'ridge':1.0},'checks':checks,'failures':failures,'runs':runs},indent=2,sort_keys=True)+'\n')
 print(json.dumps({'capture':OUT.relative_to(ROOT).as_posix(),'checks':checks,'failure_count':len(failures)},indent=2))
 if not all(checks.values()):raise SystemExit('transport treewidth scaling failed')
 return 0
if __name__=='__main__':raise SystemExit(main())
