#!/usr/bin/env python3
"""Source-locked exact-inference census for a learned LLM layer transport."""
from __future__ import annotations
import hashlib,itertools,json,os,platform,resource,subprocess,sys,time,tracemalloc
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT)]
EXPORT=Path('/applications/data/model_graph_work/transport_L12_13.npz')
RUNNER=Path(__file__).resolve()
PROTOCOL=ROOT/'docs/research/engine_substrate/LLM_TRANSPORT_TASK_GRAPH_EXACT_CENSUS_V1_1_PREREG_20261002.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_llm_transport_task_graph_exact_census_v1_1.py'
SEED=ROOT/'seeds/can_native_reimplementation.json'
LOCK=ROOT/'evaluation/substrate_capability/llm_transport_task_graph_exact_census_v1_1_lock_20261002.json'
OUT=ROOT/'evaluation/reports/llm_transport_task_graph_exact_census_v1_1_20261002.json'
REPLICATES=3;N_MODES=8;VOCAB=(-1.0,0.0,1.0);TOL=1e-8
def digest(p):
 b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def source_lock():
 from substrate_rs import _native
 return {'runner':digest(RUNNER),'protocol':digest(PROTOCOL),'analyzer':digest(ANALYZER),'seed':digest(SEED),
  'sources':[digest(ROOT/p) for p in ('domains/llm_native_graph.py','domains/can_junction_tree.py','domains/graph_treewidth.py','domains/can_native_bp.py')],
  'native_binary':digest(Path(_native.__file__).resolve()),'native_build_manifest':digest(ROOT/'runners/dsl/python/substrate_rs/_native.build.json'),
  'export':digest(EXPORT),'replicates':REPLICATES,'mode_count':N_MODES,'vocabulary':list(VOCAB),'ridge':1.0,'tolerance':TOL,'shuffle_seed':0}
def nid(v):return int(v.value if hasattr(v,'value') else v)
def factor_oracle(order,unary,pair):
 factors=[];ops=0
 for v,h in unary.items():factors.append(((v,),{(x,):-float(h)*float(x) for x in VOCAB}))
 for (a,b),w in pair.items():factors.append(((a,b),{(x,y):-float(w)*float(x)*float(y) for x in VOCAB for y in VOCAB}))
 for v in order:
  bucket=[f for f in factors if v in f[0]];factors=[f for f in factors if v not in f[0]]
  scope=tuple(sorted({x for s,_ in bucket for x in s}));rest=tuple(x for x in scope if x!=v);table={}
  for vals in itertools.product(VOCAB,repeat=len(rest)):
   ctx=dict(zip(rest,vals));best=float('inf')
   for value in VOCAB:
    ctx[v]=value;score=0.0
    for fs,ft in bucket:score+=ft[tuple(ctx[x] for x in fs)]
    ops+=len(bucket);best=min(best,score)
   table[vals]=best
  factors.append((rest,table))
 total=0.0
 for scope,table in factors:
  if scope:raise AssertionError('oracle left a nonconstant factor')
  total+=table[()]
 return total,ops
def energy(state,unary,pair):
 return -sum(float(h)*float(state[v]) for v,h in unary.items())-sum(float(w)*float(state[a])*float(state[b]) for (a,b),w in pair.items())
def connected(nodes,edges):
 adj={v:set() for v in nodes}
 for a,b in edges:adj[a].add(b);adj[b].add(a)
 if not nodes:return False
 seen={nodes[0]};stack=[nodes[0]]
 while stack:
  u=stack.pop()
  for v in adj[u]-seen:seen.add(v);stack.append(v)
 return len(seen)==len(nodes)
def graph_case(sub,T,x0,seedpath):
 from domains import llm_native_graph as lng
 from domains.can_junction_tree import can_network_from_mt
 mt,n0,n1,d0,d1=lng.build_transport_factor_graph(sub,[str(seedpath)],T,x0,n_modes0=N_MODES,n_modes1=N_MODES,
  temperature=1.0,field_scale=1.0,transport_scale=1.0,discrete_mode='3state',bidirectional=True)
 net=can_network_from_mt(sub,mt)
 ids0=[nid(v) for v in n0];ids1=[nid(v) for v in n1]
 return mt,net,n0,n1,ids0,ids1,np.asarray(d0,dtype=int),np.asarray(d1,dtype=int)
def worker(rep):
 import substrate_rs as sr
 import domains.can_junction_tree as cjt
 from domains.graph_treewidth import min_fill_upper_bound,build_elimination_triangulation
 from domains.can_native_bp import run_loopy_bp
 from domains import llm_native_graph as lng
 start_lock=source_lock();z=np.load(EXPORT);tr0,tr1,ho0,ho1=(z[k] for k in ('tr_c0','tr_c1','ho_c0','ho_c1'))
 T=lng.fit_transport(tr0,tr1,ridge=1.0)
 flat=T.flatten().copy();np.random.default_rng(0).shuffle(flat);Tshuffle=flat.reshape(T.shape)
 rows=[]
 for i,(x0,x1) in enumerate(zip(ho0,ho1)):
  result={'heldout_index':i,'target_signs':np.where(x1[:N_MODES]>=0,1.0,-1.0).tolist(),'conditions':{}}
  for name,weights in (('learned',T),('shuffled',Tshuffle)):
   sub=sr.Substrate();build_start=time.perf_counter_ns();mt,net,n0,n1,ids0,ids1,d0,d1=graph_case(sub,weights,x0,SEED);build_ns=time.perf_counter_ns()-build_start
   unary=dict(net['unary']);pair={tuple(sorted(k)):float(v) for k,v in net['pairwise'].items()};nodes=list(net['nodes']);edges=list(net['edges'])
   expected_unary={ids0[j]:float(x0[d0[j]]) for j in range(N_MODES)};expected_unary.update({v:0.0 for v in ids1})
   expected_pair={tuple(sorted((ids0[j],ids1[k]))):float(weights[d1[k],d0[j]]) for k in range(N_MODES) for j in range(N_MODES) if float(weights[d1[k],d0[j]])!=0.0}
   extraction_start=time.perf_counter_ns();net2=cjt.can_network_from_mt(sub,mt);extract_ns=time.perf_counter_ns()-extraction_start
   exact_extraction=(net2['discrete_mode']=='3state' and tuple(net2['vocab'])==VOCAB and set(unary)==set(expected_unary)
    and all(abs(unary[k]-v)<TOL for k,v in expected_unary.items()) and set(pair)==set(expected_pair)
    and all(abs(pair[k]-v)<TOL for k,v in expected_pair.items()))
   before=(dict(unary),dict(pair),tuple(nodes),tuple(sorted(tuple(sorted(e)) for e in edges)))
   state_before={nid(v):float(sub.node(v)['attrs'].get('state',0.0)) for v in n0+n1}
   order_start=time.perf_counter_ns();mf=min_fill_upper_bound(nodes,edges);order_ns=time.perf_counter_ns()-order_start
   tri=build_elimination_triangulation(nodes,edges,mf['elimination_order']);tri_width=max((len(b)-1 for b in tri['bags'].values()),default=0)
   oracle_start=time.perf_counter_ns();oracle,ops=factor_oracle(nodes,unary,pair);oracle_ns=time.perf_counter_ns()-oracle_start
   tracemalloc.start();jt_start=time.perf_counter_ns();jt=cjt.junction_tree_map(nodes,edges,unary,{frozenset(k):v for k,v in pair.items()},VOCAB,order=mf['elimination_order']);jt_ns=time.perf_counter_ns()-jt_start;_,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
   state={nid(k):float(v) for k,v in jt['state'].items()};rescore=energy(state,unary,pair);exact_pred=np.asarray([1.0 if state[v]>=0 else -1.0 for v in ids1])
   bp_start=time.perf_counter_ns();bp=run_loopy_bp(sub,mt,combine='max_product');bp_ns=time.perf_counter_ns()-bp_start
   bp_pred=lng.read_transport_modes(bp,n1)
   linear_drive=np.asarray([sum(float(weights[d1[k],d0[j]])*float(x0[d0[j]]) for j in range(N_MODES)) for k in range(N_MODES)])
   target=np.asarray(result['target_signs']);
   postnet=cjt.can_network_from_mt(sub,mt);after=(dict(postnet['unary']),{tuple(sorted(k)):float(v) for k,v in postnet['pairwise'].items()},tuple(postnet['nodes']),tuple(sorted(tuple(sorted(e)) for e in postnet['edges'])))
   state_after={nid(v):float(sub.node(v)['attrs'].get('state',0.0)) for v in n0+n1}
   result['conditions'][name]={'nodes':len(nodes),'edges':len(edges),'pair_factors':len(pair),'components_connected':connected(nodes,edges),
    'width':int(mf['treewidth']),'triangulation_width':tri_width,'exact_extraction':exact_extraction,'oracle_energy':oracle,'jt_energy':float(jt['energy']),'direct_rescore':rescore,'oracle_operations':ops,
    'exact_prediction':exact_pred.tolist(),'bp_prediction':np.asarray(bp_pred,dtype=float).tolist(),'linear_prediction':np.where(linear_drive>=0,1.0,-1.0).tolist(),
    'exact_accuracy':float(np.mean(exact_pred==target)),'bp_accuracy':float(np.mean(np.asarray(bp_pred)==target)),'linear_accuracy':float(np.mean(np.where(linear_drive>=0,1.0,-1.0)==target)),
    'no_mutation':before==after and state_before==state_after,'timing_ns':{'graph_construction':build_ns,'runtime_extraction':extract_ns,'minfill_order':order_ns,'oracle':oracle_ns,'junction_tree':jt_ns,'bp':bp_ns},'traced_peak_bytes':peak}
  rows.append(result)
 end_lock=source_lock()
 return {'replicate':rep,'worker_pid':os.getpid(),'input_count':len(rows),'rows':rows,'source_lock_start':start_lock,'source_lock_end':end_lock,'process_peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
def main():
 args=sys.argv[1:]
 if args[:1]==['--worker']:
  print(json.dumps(worker(int(args[1])),sort_keys=True,separators=(',',':')));return 0
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite lock/capture')
  LOCK.write_text(json.dumps({'schema':'LlmTransportTaskGraphExactCensusV1_1Lock','sources':source_lock()},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if args!=['--run']:raise SystemExit('usage: --lock, --run, or --worker REP')
 lock=json.loads(LOCK.read_text())
 if source_lock()!=lock['sources']:raise SystemExit('source/export drift from lock')
 from domains.engine_provenance import build_is_stale
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit('native engine is stale: '+'; '.join(stale))
 env={**os.environ,'PYTHONPATH':f"{ROOT/'runners/dsl/python'}:{ROOT}:{os.environ.get('PYTHONPATH','')}"};runs=[];failures=[]
 for rep in range(REPLICATES):
  try:
   p=subprocess.run([sys.executable,str(RUNNER),'--worker',str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=900)
   if p.returncode:raise RuntimeError(p.stderr[-3000:])
   row=json.loads(p.stdout.strip());runs.append(row)
   a=[z['conditions']['learned']['exact_accuracy'] for z in row['rows']];b=[z['conditions']['shuffled']['exact_accuracy'] for z in row['rows']]
   print(f"rep={rep} pid={row['worker_pid']} n={row['input_count']} width={row['rows'][0]['conditions']['learned']['width']} learned={np.mean(a):.3f} shuffled={np.mean(b):.3f}",flush=True)
  except Exception as e:failures.append({'replicate':rep,'error':type(e).__name__+': '+str(e)})
 post=source_lock();cells=[c for r in runs for row in r['rows'] for c in row['conditions'].values()]
 checks={'three_replicates':len(runs)==REPLICATES,'failure_free':not failures,'fresh_pids':len({r['worker_pid'] for r in runs})==len(runs),
  'ten_inputs_each':all(r['input_count']==10 and len(r['rows'])==10 for r in runs),'paired_conditions':all(set(row['conditions'])=={'learned','shuffled'} for r in runs for row in r['rows']),
  'connected_expected_graphs':all(c['components_connected'] and c['nodes']==16 and c['pair_factors']==64 for c in cells),'exact_extraction':all(c['exact_extraction'] for c in cells),
  'width_certificates':all(c['width']==c['triangulation_width'] for c in cells),'exact_energy':all(abs(c[k]-c['oracle_energy'])<TOL for c in cells for k in ('jt_energy','direct_rescore')),
  'valid_predictions':all(len(c['exact_prediction'])==len(c['bp_prediction'])==len(c['linear_prediction'])==8 for c in cells),
  'no_mutation':all(c['no_mutation'] for c in cells),'worker_source_locks':all(r['source_lock_start']==lock['sources']==r['source_lock_end'] for r in runs),'pre_post_lock':post==lock['sources']}
 OUT.write_text(json.dumps({'schema':'LlmTransportTaskGraphExactCensusV1_1Results','lock_sha256':hashlib.sha256(LOCK.read_bytes()).hexdigest(),'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),'sources':source_lock(),'post_run_sources':post,'configuration':{'replicates':REPLICATES,'heldout_rows_per_worker':10,'modes_per_layer':N_MODES,'vocabulary':VOCAB,'ridge':1.0},'claim_boundary':'one learned Qwen3-0.6B L12-to-L13 transport, eight selected source modes, eight targets, ten heldout transitions; no broad language or natural frame-prevalence claim','checks':checks,'failures':failures,'runs':runs},indent=2,sort_keys=True)+'\n')
 print(json.dumps({'capture':OUT.relative_to(ROOT).as_posix(),'checks':checks,'failure_count':len(failures)},indent=2))
 if not all(checks.values()):raise SystemExit('transport inference census failed')
 return 0
if __name__=='__main__':raise SystemExit(main())
