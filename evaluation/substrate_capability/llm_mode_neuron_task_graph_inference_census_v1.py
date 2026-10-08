#!/usr/bin/env python3
"""Exact-inference census on all held-out LLM mode-neuron graph inputs."""
from __future__ import annotations
import hashlib,itertools,json,os,platform,resource,subprocess,sys,time,tracemalloc
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT)]
EXPORT=Path('/applications/data/model_graph_work/mode_export_L12b.npz')
RUNNER=Path(__file__).resolve()
PROTOCOL=ROOT/'docs/research/engine_substrate/LLM_MODE_NEURON_TASK_GRAPH_INFERENCE_CENSUS_V1_PREREG_20261002.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_llm_mode_neuron_task_graph_inference_census_v1.py'
PRIOR_RUNNER=ROOT/'scripts/llm_native_graph_levers_measure.py'
PRIOR_PROTOCOL=ROOT/'docs/research/psychology_affect/NATIVE_GRAPH_APERTURE_PREREG.md'
PRIOR_RESULTS=ROOT/'docs/research/psychology_affect/NATIVE_GRAPH_APERTURE_RESULTS.md'
SEED=ROOT/'seeds/can_native_reimplementation.json'
LOCK=ROOT/'evaluation/substrate_capability/llm_mode_neuron_task_graph_inference_census_v1_lock_20261002.json'
OUT=ROOT/'evaluation/reports/llm_mode_neuron_task_graph_inference_census_v1_20261002.json'
REPLICATES=3;N_NEUR=8;N_MODES=4;VOCAB=(-1.0,0.0,1.0);TOL=1e-8
def digest(path):
 raw=path.read_bytes();return {'path':path.relative_to(ROOT).as_posix(),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def source_lock():
 from substrate_rs import _native
 return {'runner':digest(RUNNER),'protocol':digest(PROTOCOL),'analyzer':digest(ANALYZER),
  'prior_runner':digest(PRIOR_RUNNER),'prior_protocol':digest(PRIOR_PROTOCOL),'prior_results':digest(PRIOR_RESULTS),'seed':digest(SEED),
  'sources':[digest(ROOT/p) for p in ('domains/llm_native_graph.py','domains/can_junction_tree.py','domains/graph_treewidth.py')],
  'native_binary':digest(Path(_native.__file__).resolve()),'native_build_manifest':digest(ROOT/'runners/dsl/python/substrate_rs/_native.build.json'),
  'export':{'path':str(EXPORT),'bytes':EXPORT.stat().st_size,'sha256':hashlib.sha256(EXPORT.read_bytes()).hexdigest()},
  'replicates':REPLICATES,'neuron_count':N_NEUR,'mode_count':N_MODES,'vocabulary':list(VOCAB),'tolerance':TOL}
def nid(x):return int(x.value if hasattr(x,'value') else x)
def factor_oracle(order,unary,pair):
 factors=[];ops=0
 for v,h in unary.items():factors.append(((v,),{(x,):-float(h)*float(x) for x in VOCAB}))
 for (a,b),w in pair.items():factors.append(((a,b),{(x,y):-float(w)*float(x)*float(y) for x in VOCAB for y in VOCAB}))
 for v in order:
  bucket=[f for f in factors if v in f[0]];factors=[f for f in factors if v not in f[0]]
  scope=tuple(sorted({x for s,_ in bucket for x in s}));rest=tuple(x for x in scope if x!=v);table={}
  for vals in itertools.product(VOCAB,repeat=len(rest)):
   ctx=dict(zip(rest,vals));best=float('inf')
   for val in VOCAB:
    ctx[v]=val;score=0.0
    for fs,ft in bucket:score+=ft[tuple(ctx[x] for x in fs)]
    ops+=len(bucket);best=min(best,score)
   table[vals]=best
  factors.append((rest,table))
 total=0.0
 for scope,table in factors:
  if scope:raise AssertionError('oracle left a nonconstant factor')
  total+=table[()]
 return total,ops
def direct_energy(state,unary,pair):
 return -sum(float(h)*float(state[v]) for v,h in unary.items())-sum(float(w)*float(state[a])*float(state[b]) for (a,b),w in pair.items())
def components(nodes,edges):
 adj={v:set() for v in nodes}
 for a,b in edges:adj[a].add(b);adj[b].add(a)
 seen=set();out=[]
 for v in nodes:
  if v in seen:continue
  stack=[v];seen.add(v);comp=[]
  while stack:
   u=stack.pop();comp.append(u)
   for w in adj[u]-seen:seen.add(w);stack.append(w)
  out.append(comp)
 return out
def worker(rep):
 import substrate_rs as sr
 import domains.can_junction_tree as cjt
 from domains.graph_treewidth import min_fill_upper_bound,build_elimination_triangulation
 from domains import llm_native_graph as lng
 started=source_lock();z=np.load(EXPORT);modes=z['modes'];mean=z['mean'];wc=z['Wc'];xs=z['ho_x'];neuron_idx=z['neuron_idx'];
 if len(xs)!=10:raise RuntimeError('registered export must contain all 10 held-out inputs')
 rows=[];topologies=[]
 for i,x in enumerate(xs):
  coeffs,_=lng.coarse_mode_state(modes,mean,wc,x)
  selected,field,_=lng.refine_to_neurons(modes,coeffs,n_neurons=N_NEUR)
  nidx=neuron_idx[:N_NEUR]
  selected=[int(v) for v in np.asarray(selected).tolist()]
  if selected!=[int(v) for v in nidx]:raise RuntimeError('refinement order differs from exported top-loading neuron order')
  construct_start=time.perf_counter_ns();sub=sr.Substrate();mt,ncs,mcs,dom=lng.build_mode_neuron_factor_graph(sub,[str(SEED)],modes,coeffs,nidx,field,
   temperature=1.0,mode_field_scale=0.0,neuron_field_scale=1.0,incidence_scale=1.0,n_modes=N_MODES,discrete_mode='3state')
  construct_ns=time.perf_counter_ns()-construct_start
  extract_start=time.perf_counter_ns();net=cjt.can_network_from_mt(sub,mt);extract_ns=time.perf_counter_ns()-extract_start
  nodes=list(net['nodes']);edges=[tuple(e) for e in net['edges']]
  unary=dict(net['unary']);pair={tuple(sorted(k)):float(v) for k,v in net['pairwise'].items()}
  before=(dict(unary),dict(pair),tuple(nodes),tuple(sorted(tuple(sorted(e)) for e in edges)))
  node_pos={nid(c):i for i,c in enumerate(ncs+mcs)};topologies.append(tuple(sorted(tuple(sorted((node_pos[a],node_pos[b]))) for a,b in edges)))
  mode_ids=[nid(v) for v in mcs]
  expected_unary={nid(v):float(field[j]) for j,v in enumerate(ncs)}
  expected_unary.update({nid(v):0.0 for v in mcs})
  expected_pair={tuple(sorted((nid(mcs[mi]),nid(ncs[ni])))):float(modes[m, nidx[ni]])
   for mi,m in enumerate(dom) for ni in range(len(nidx)) if float(modes[m,nidx[ni]])!=0.0}
  exact_extraction=(net['discrete_mode']=='3state' and tuple(net['vocab'])==VOCAB and len(nodes)==N_NEUR+N_MODES
   and set(unary)==set(expected_unary) and all(abs(unary[k]-v)<TOL for k,v in expected_unary.items())
   and set(pair)==set(expected_pair) and all(abs(pair[k]-v)<TOL for k,v in expected_pair.items()))
  state_before={nid(v):float(sub.node(v)['attrs'].get('state',0.0)) for v in ncs+mcs}
  order_start=time.perf_counter_ns();mf=min_fill_upper_bound(nodes,edges);mf_ns=time.perf_counter_ns()-order_start
  tri=build_elimination_triangulation(nodes,edges,mf['elimination_order'])
  cert_width=max((len(b)-1 for b in tri['bags'].values()),default=0)
  oracle_start=time.perf_counter_ns();oracle,oracle_ops=factor_oracle(nodes,unary,pair);oracle_ns=time.perf_counter_ns()-oracle_start
  tracemalloc.start();jt_start=time.perf_counter_ns();jt=cjt.junction_tree_map(nodes,edges,unary,{frozenset(k):v for k,v in pair.items()},VOCAB,order=mf['elimination_order']);jt_ns=time.perf_counter_ns()-jt_start;_,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
  state={nid(k):float(v) for k,v in jt['state'].items()};rescore=direct_energy(state,unary,pair)
  mode_states=[state[v] for v in mode_ids]
  target=np.where(coeffs[dom]>=0,1.0,-1.0);pred=np.where(np.asarray(mode_states)>=0,1.0,-1.0)
  net_after=cjt.can_network_from_mt(sub,mt);after=(dict(net_after['unary']),{tuple(sorted(k)):float(v) for k,v in net_after['pairwise'].items()},tuple(net_after['nodes']),tuple(sorted(tuple(sorted(e)) for e in net_after['edges'])))
  state_after={nid(v):float(sub.node(v)['attrs'].get('state',0.0)) for v in ncs+mcs}
  comps=components(nodes,edges)
  rows.append({'heldout_index':i,'nodes':len(nodes),'undirected_factors':len(pair),'directed_edges_in_graph':len(edges),
   'component_count':len(comps),'component_sizes':sorted(len(c) for c in comps),'connected':len(comps)==1,
   'mode_neuron_edges':sum((a in set(mode_ids)) != (b in set(mode_ids)) for a,b in pair),
   'vocabulary':list(net['vocab']),'mode_target':target.tolist(),'mode_prediction':pred.tolist(),
   'mode_sign_agreement':float(np.mean(target==pred)),'minfill_width_certificate':int(mf['treewidth']),'triangulation_width':cert_width,
   'oracle_energy':oracle,'jt_energy':float(jt['energy']),'direct_rescore':rescore,'oracle_operations':oracle_ops,
   'exact_extraction':exact_extraction,
   'no_mutation':before==after and state_before==state_after and all(v in VOCAB for v in state.values()),
   'timing_ns':{'graph_construction':construct_ns,'runtime_extraction':extract_ns,'minfill_order':mf_ns,'oracle':oracle_ns,'junction_tree':jt_ns},'traced_peak_bytes':peak})
 post=source_lock()
 return {'replicate':rep,'worker_pid':os.getpid(),'input_count':len(rows),'topology_signatures':[list(map(list,t)) for t in topologies],
  'all_topologies_identical':len(set(topologies))==1,'rows':rows,'source_lock_start':started,'source_lock_end':post,
  'process_peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
def main():
 args=sys.argv[1:]
 if args[:1]==['--worker']:
  print(json.dumps(worker(int(args[1])),sort_keys=True,separators=(',',':')));return 0
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite lock/capture')
  LOCK.write_text(json.dumps({'schema':'LlmModeNeuronTaskGraphInferenceCensusV1Lock','sources':source_lock()},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if args!=['--run']:raise SystemExit('usage: --lock, --run, or --worker REP')
 lock=json.loads(LOCK.read_text())
 if source_lock()!=lock['sources']:raise SystemExit('source/export drift from lock')
 from domains.engine_provenance import build_is_stale
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit('native engine stale: '+'; '.join(stale))
 env={**os.environ,'PYTHONPATH':f"{ROOT/'runners/dsl/python'}:{ROOT}:{os.environ.get('PYTHONPATH','')}"};runs=[];failures=[]
 for rep in range(REPLICATES):
  try:
   p=subprocess.run([sys.executable,str(RUNNER),'--worker',str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=600)
   if p.returncode:raise RuntimeError(p.stderr[-3000:])
   row=json.loads(p.stdout.strip());runs.append(row)
   print(f"rep={rep} pid={row['worker_pid']} inputs={row['input_count']} width={row['rows'][0]['minfill_width_certificate']} edges={row['rows'][0]['undirected_factors']} agreement={sum(x['mode_sign_agreement'] for x in row['rows'])/len(row['rows']):.3f}",flush=True)
  except Exception as e:failures.append({'replicate':rep,'error':type(e).__name__+': '+str(e)})
 post=source_lock();checks={'replicates':len(runs)==REPLICATES,'failure_free':not failures,'fresh_pids':len({x['worker_pid'] for x in runs})==len(runs),
  'ten_heldout_each':all(x['input_count']==10 and len(x['rows'])==10 for x in runs),
  'all_connected':all(z['connected'] for x in runs for z in x['rows']),'topology_stable':all(x['all_topologies_identical'] for x in runs),
  'expected_sizes':all(z['nodes']==12 and z['undirected_factors']==z['mode_neuron_edges'] for x in runs for z in x['rows']),
  'all_extraction_exact':all(z['exact_extraction'] for x in runs for z in x['rows']),
  'width_profile_reconciles':all(z['minfill_width_certificate']==z['triangulation_width'] for x in runs for z in x['rows']),
  'oracle_and_rescore':all(abs(z[k]-z['oracle_energy'])<TOL for x in runs for z in x['rows'] for k in ('jt_energy','direct_rescore')),
  'no_mutation':all(z['no_mutation'] for x in runs for z in x['rows']),
  'worker_locks':all(x['source_lock_start']==lock['sources']==x['source_lock_end'] for x in runs),'pre_post_lock':post==lock['sources']}
 OUT.write_text(json.dumps({'schema':'LlmModeNeuronTaskGraphInferenceCensusV1Results','lock_sha256':hashlib.sha256(LOCK.read_bytes()).hexdigest(),
  'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),'sources':source_lock(),'post_run_sources':post,
  'configuration':{'replicates':REPLICATES,'heldout_rows_per_worker':10,'neurons':N_NEUR,'modes':N_MODES,'vocabulary':VOCAB},
  'claim_boundary':'all ten heldout inputs from one real model/layer export on a fixed authored connected 8-neuron/4-mode incidence graph; not broad language capability or natural frame prevalence',
  'checks':checks,'failures':failures,'runs':runs},indent=2,sort_keys=True)+'\n')
 print(json.dumps({'capture':OUT.relative_to(ROOT).as_posix(),'checks':checks,'failure_count':len(failures)},indent=2))
 if not all(checks.values()):raise SystemExit('task graph inference census failed')
if __name__=='__main__':main()
