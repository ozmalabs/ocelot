#!/usr/bin/env python3
"""Exact separator-conditioning comparison on varied Qwen3 transport graphs."""
from __future__ import annotations
import hashlib,itertools,json,os,platform,subprocess,sys,time
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT)]
RUNNER=Path(__file__).resolve();ANALYZER=ROOT/'evaluation/substrate_capability/analyze_llm_transport_varied_topology_solver_v1_3.py'
PROTOCOL=ROOT/'docs/research/engine_substrate/LLM_TRANSPORT_VARIED_TOPOLOGY_SOLVER_V1_3_AMENDMENT_20261003.md'
SEED=ROOT/'seeds/can_native_reimplementation.json';UP=ROOT/'evaluation/reports/llm_cross_model_transport_v1_1_20261002.json'
UPLOCK=ROOT/'evaluation/substrate_capability/llm_cross_model_transport_v1_1_lock_20261002.json'
UPAN=ROOT/'evaluation/reports/llm_cross_model_transport_v1_1_analysis_20261002.json'
CENSUS=ROOT/'evaluation/reports/llm_transport_varied_topology_separator_census_v1_2_20261003.json'
CENSUSLOCK=ROOT/'evaluation/substrate_capability/llm_transport_varied_topology_separator_census_v1_2_lock_20261003.json'
CENSUSAN=ROOT/'evaluation/reports/llm_transport_varied_topology_separator_census_v1_2_analysis_20261003.json'
MODELS={m:ROOT/f'evaluation/reports/llm_cross_model_transport_v1_{m}.npz' for m in ('qwen3_0_6b','qwen3_1_7b')}
V1_BASE_PROTOCOL=ROOT/'docs/research/engine_substrate/LLM_TRANSPORT_VARIED_TOPOLOGY_SOLVER_V1_PREREG_20261003.md'
V1_1_AMENDMENT=ROOT/'docs/research/engine_substrate/LLM_TRANSPORT_VARIED_TOPOLOGY_SOLVER_V1_1_AMENDMENT_20261003.md'
V1_2_RUNNER=ROOT/'evaluation/substrate_capability/llm_transport_varied_topology_solver_v1_2.py'
V1_2_ANALYZER=ROOT/'evaluation/substrate_capability/analyze_llm_transport_varied_topology_solver_v1_2.py'
V1_2_PROTOCOL=ROOT/'docs/research/engine_substrate/LLM_TRANSPORT_VARIED_TOPOLOGY_SOLVER_V1_2_AMENDMENT_20261003.md'
V1_2_LOCK=ROOT/'evaluation/substrate_capability/llm_transport_varied_topology_solver_v1_2_lock_20261003.json'
V1_2_CAPTURE=ROOT/'evaluation/reports/llm_transport_varied_topology_solver_v1_2_20261003.json'
V1_2_ANALYSIS=ROOT/'evaluation/reports/llm_transport_varied_topology_solver_v1_2_analysis_20261003.json'
LOCK=ROOT/'evaluation/substrate_capability/llm_transport_varied_topology_solver_v1_3_lock_20261003.json'
OUT=ROOT/'evaluation/reports/llm_transport_varied_topology_solver_v1_3_20261003.json'
REPS=3;K=8;FANINS=(1,2,4,8);VOCAB=(-1.,0.,1.);TOL=1e-8
def digest(p):
 p=Path(p);return {'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def sources():
 from substrate_rs import _native
 paths=[RUNNER,ANALYZER,PROTOCOL,V1_BASE_PROTOCOL,V1_1_AMENDMENT,V1_2_RUNNER,V1_2_ANALYZER,V1_2_PROTOCOL,V1_2_LOCK,V1_2_CAPTURE,V1_2_ANALYSIS,SEED,UP,UPLOCK,UPAN,CENSUS,CENSUSLOCK,CENSUSAN,ROOT/'domains/llm_native_graph.py',ROOT/'domains/can_junction_tree.py',ROOT/'domains/graph_treewidth.py',ROOT/'runners/dsl/python/substrate_rs/_native.build.json',Path(_native.__file__).resolve()]
 for p in MODELS.values():paths.extend((p,p.with_suffix('.provenance.json'),p.with_suffix('.tokenization.json')))
 return {'artifacts':[digest(p) for p in paths],'replicates':REPS,'fanins':list(FANINS),'models':list(MODELS),'hops':[[10,11],[11,12],[12,13],[13,14]],'heldout_count':10,'mode_count':K,'ridge':1.,'vocabulary':list(VOCAB),'anonymization_seed_formula':'20261003 + replicate*1000'}
def nid(v):return int(v.value if hasattr(v,'value') else v)
def components(nodes,edges,removed):
 left=set(nodes)-set(removed);adj={v:set() for v in left}
 for a,b in edges:
  if a in left and b in left:adj[a].add(b);adj[b].add(a)
 out=[]
 while left:
  root=min(left);left.remove(root);stack=[root];part=[]
  while stack:
   u=stack.pop();part.append(u)
   for v in adj[u]&left:left.remove(v);stack.append(v)
  out.append(sorted(part))
 return sorted(out,key=lambda c:(len(c),c))
def propose(nodes,edges):
 tested=0
 for k in range(len(nodes)+1):
  found=[]
  for s in itertools.combinations(sorted(nodes),k):
   tested+=1;cc=components(nodes,edges,set(s))
   if len(cc)>=2:found.append({'separator':list(s),'components':cc})
  if found:return k,tested,found
 return None,tested,[]
def energy(state,unary,pair):
 return -sum(float(h)*state[v] for v,h in unary.items())-sum(float(w)*state[a]*state[b] for (a,b),w in pair.items())
def prepare_components(comps,edges):
 start=time.perf_counter_ns();prepared=[]
 from domains.graph_treewidth import min_fill_upper_bound
 for comp in comps:
  cset=set(comp);ce=[e for e in edges if e[0] in cset and e[1] in cset]
  if len(comp)<=5:configs=[dict(zip(comp,vals)) for vals in itertools.product(VOCAB,repeat=len(comp))];order=None
  else:configs=None;order=min_fill_upper_bound(comp,ce)['elimination_order']
  prepared.append((comp,cset,ce,configs,order))
 return prepared,time.perf_counter_ns()-start
def bind_component_factors(prepared,pair):
 start=time.perf_counter_ns();bound=[]
 for comp,cset,ce,configs,order in prepared:
  internal=[(a,b,w) for (a,b),w in pair.items() if a in cset and b in cset];boundary=[(a,b,w) for (a,b),w in pair.items() if (a in cset)!=(b in cset)]
  bound.append((comp,cset,internal,boundary,ce,configs,order))
 return bound,time.perf_counter_ns()-start
def conditioned(nodes,unary,pair,separator,prepared,cjt):
 start=time.perf_counter_ns();sep=tuple(separator);sep_set=set(sep);best=float('inf');beststate=None
 inside=[(a,b,w) for (a,b),w in pair.items() if a in sep_set and b in sep_set]
 for vals in itertools.product(VOCAB,repeat=len(sep)):
  fixed=dict(zip(sep,vals));score=-sum(unary[v]*fixed[v] for v in sep)-sum(w*fixed[a]*fixed[b] for a,b,w in inside);state=dict(fixed)
  for comp,cset,internal,boundary,ce,configs,order in prepared:
   if configs is not None:
    localbest=float('inf');localstate=None
    for assn in configs:
     e=-sum(unary[v]*assn[v] for v in comp)-sum(w*assn[a]*assn[b] for a,b,w in internal)
     for a,b,w in boundary:
      if a in cset:e-=w*assn[a]*fixed[b]
      else:e-=w*assn[b]*fixed[a]
     if e<localbest:localbest=e;localstate=assn
   else:
    local_unary={v:unary[v] for v in comp}
    for a,b,w in boundary:
     if a in cset:local_unary[a]+=w*fixed[b]
     else:local_unary[b]+=w*fixed[a]
    local_pair={frozenset((a,b)):w for a,b,w in internal}
    result=cjt.junction_tree_map(comp,ce,local_unary,local_pair,VOCAB,order=order);localbest=float(result['energy']);localstate={v:float(result['state'][v]) for v in comp}
   score+=localbest;state.update(localstate)
  if score<best:best=score;beststate=state
 return beststate,best,time.perf_counter_ns()-start
def worker(rep):
 import substrate_rs as sr
 import domains.can_junction_tree as cjt
 from domains.graph_treewidth import min_fill_upper_bound,build_elimination_triangulation
 from domains import llm_native_graph as lng
 from domains.engine_provenance import build_is_stale
 stale=build_is_stale(str(ROOT))
 if stale:raise RuntimeError('native engine stale: '+'; '.join(stale))
 before=sources();up=json.loads(UP.read_text());census=json.loads(CENSUS.read_text());census_keys={(g['model'],g['fan_in'],g['source_signature']) for r in census['runs'] for g in r['graphs']};perm=np.random.default_rng(20261003+rep*1000).permutation(16);cache={};rows=[]
 from substrate.seed_loader import engine_rules_only
 sub=sr.Substrate();seed0=time.perf_counter_ns();sub.load_seed_manifest(engine_rules_only(json.loads(SEED.read_text())));seed_init_ns=time.perf_counter_ns()-seed0
 for model,path in MODELS.items():
  z=np.load(path);tr=z['tr_c'];ho=z['ho_c'];layers=[int(v) for v in z['layers']];Ts=[lng.fit_transport(tr[h],tr[h+1],ridge=1.) for h in range(len(layers)-1)]
  up_rows=[r for run in up['runs'] if run['model']==model for r in run['rows']]
  for h,T in enumerate(Ts):
   for i in range(ho.shape[1]):
    x0=ho[h,i];x1=ho[h+1,i];dom0=np.argsort(-np.abs(x0))[:K]
    for fan in FANINS:
     W=np.zeros_like(T)
     for q in range(K):
      keep=np.argsort(-np.abs(T[q,dom0]),kind='stable')[:fan];W[q,dom0[keep]]=T[q,dom0[keep]]
     match=[r for r in up_rows if r['source_layer']==layers[h] and r['heldout_index']==i and r['fan_in']==fan]
     if len(match)!=3:raise RuntimeError(f'upstream cell multiplicity {model}/{layers[h]}/{i}/{fan}: {len(match)}')
     expected_topo=match[0]['topology_signature']
     build0=time.perf_counter_ns();mt,n0,n1,d0,d1=lng.build_transport_factor_graph(sub,[],W,x0,n_modes0=K,n_modes1=K,temperature=1.,field_scale=1.,transport_scale=1.,discrete_mode='3state',bidirectional=True);build_ns=time.perf_counter_ns()-build0
     ext0=time.perf_counter_ns();net=cjt.can_network_from_mt(sub,mt);extract_ns=time.perf_counter_ns()-ext0
     native_nodes=list(net['nodes']);un0={nid(v):float(a) for v,a in net['unary'].items()};p0={tuple(sorted(map(nid,k))):float(v) for k,v in net['pairwise'].items()};edges0=[tuple(sorted(map(nid,e))) for e in net['edges']]
     native_order=[nid(v) for v in n0+n1];pos={v:q for q,v in enumerate(native_order)}
     source_edges=sorted([list(sorted((pos[a],pos[b]))) for a,b in edges0]);source_signature=hashlib.sha256(json.dumps(source_edges).encode()).hexdigest()
     if source_signature!=expected_topo:raise RuntimeError(f'upstream topology mismatch {model}/{layers[h]}/{i}/{fan}')
     if (model,fan,source_signature) not in census_keys:raise RuntimeError('topology absent from separator census')
     mapping={v:int(perm[q]) for q,v in enumerate(native_order)};nodes=list(range(16));edges=sorted([tuple(sorted((mapping[a],mapping[b]))) for a,b in edges0]);unary={mapping[v]:a for v,a in un0.items()};pair={tuple(sorted((mapping[a],mapping[b]))):w for (a,b),w in p0.items()}
     before_state={nid(v):float(sub.node(v)['attrs'].get('state',0.)) for v in n0+n1}
     order0=time.perf_counter_ns();mf=min_fill_upper_bound(native_nodes,edges0);order_ns=time.perf_counter_ns()-order0;tri=build_elimination_triangulation(native_nodes,edges0,mf['elimination_order']);certified_width=max((len(b)-1 for b in tri['bags'].values()),default=0)
     jt0=time.perf_counter_ns();jt=cjt.junction_tree_map(native_nodes,edges0,net['unary'],{frozenset(k):v for k,v in net['pairwise'].items()},VOCAB,order=mf['elimination_order']);jt_ns=time.perf_counter_ns()-jt0
     jt_state={mapping[nid(v)]:float(jt['state'][nid(v)]) for v in native_nodes};jt_e=float(jt['energy']);jt_rescore=energy(jt_state,unary,pair);jt_pred=[1. if jt_state[mapping[nid(v)]]>=0 else -1. for v in n1]
     sig=hashlib.sha256(json.dumps([16,edges]).encode()).hexdigest();hit=sig in cache
     if hit:k,tested,cands,prepared,component_precompute_ns=cache[sig];proposal_ns=0;component_precompute_ns=0
     else:
      pstart=time.perf_counter_ns();k,tested,cands=propose(nodes,edges);proposal_ns=time.perf_counter_ns()-pstart;prepared,component_precompute_ns=prepare_components(cands[0]['components'],edges);cache[sig]=(k,tested,cands,prepared,component_precompute_ns)
     chosen=cands[0];bound,factor_bind_ns=bind_component_factors(prepared,pair);state,solved_e,solver_ns=conditioned(nodes,unary,pair,chosen['separator'],bound,cjt);direct=energy(state,unary,pair);pred=[1. if state[mapping[nid(v)]]>=0 else -1. for v in n1]
     post=cjt.can_network_from_mt(sub,mt);after_state={nid(v):float(sub.node(v)['attrs'].get('state',0.)) for v in n0+n1};unchanged=(before_state==after_state and un0=={nid(v):float(a) for v,a in post['unary'].items()} and p0=={tuple(sorted(map(nid,key))):float(v) for key,v in post['pairwise'].items()})
     row={'model':model,'source_layer':layers[h],'target_layer':layers[h+1],'heldout_index':i,'fan_in':fan,'source_topology_signature':source_signature,'anonymous_topology_signature':sig,'anonymous_edges':[list(e) for e in edges],'anonymous_map_by_native_order':[mapping[v] for v in native_order],'anonymous_unary':[[v,a] for v,a in sorted(unary.items())],'anonymous_pair_factors':[[a,b,w] for (a,b),w in sorted(pair.items())],'target_nodes_anonymous':[mapping[nid(v)] for v in n1],'conditioned_state':[[v,a] for v,a in sorted(state.items())],'jt_state':[[v,a] for v,a in sorted(jt_state.items())],'minimum_separator_size':k,'subsets_tested':tested,'proposal_candidates':cands,'cache_hit':hit,'timing_ns':{'graph_build':build_ns,'factor_extract':extract_ns,'minfill_order':order_ns,'junction_tree':jt_ns,'proposal':proposal_ns,'component_precompute':component_precompute_ns,'factor_bind':factor_bind_ns,'conditioned_solver':solver_ns},'width':int(mf['treewidth']),'certified_width':certified_width,'jt_energy':jt_e,'jt_direct_rescore':jt_rescore,'conditioned_energy':float(solved_e),'conditioned_direct_rescore':direct,'jt_prediction':jt_pred,'conditioned_prediction':pred,'target':np.where(x1[:K]>=0,1.,-1.).tolist(),'state_valid':all(v in VOCAB for v in state.values()),'no_mutation':unchanged}
     rows.append(row)
     progress=OUT.with_name(OUT.stem+f'_rep{rep}.progress.jsonl')
     with progress.open('a') as f:f.write(json.dumps(row,separators=(',',':'))+'\n');f.flush()
   print(f'rep={rep} model={model} hop={layers[h]} completed={len(rows)}',file=sys.stderr,flush=True)
 after=sources();return {'replicate':rep,'pid':os.getpid(),'rows':rows,'seed_init_ns':seed_init_ns,'unique_topologies':len(cache),'proposal_searches':len(cache),'cache_hits':sum(r['cache_hit'] for r in rows),'source_start':before,'source_end':after}
def main():
 args=sys.argv[1:]
 if args[:1]==['--worker']:print(json.dumps(worker(int(args[1])),sort_keys=True,separators=(',',':')));return 0
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite existing lock/capture')
  LOCK.write_text(json.dumps({'schema':'LlmTransportVariedTopologySolverV1Lock','sources':sources()},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if args!=['--run']:raise SystemExit('usage: --lock, --run, or --worker REP')
 lock=json.loads(LOCK.read_text());before=sources()
 if before!=lock['sources']:raise SystemExit('source drift from lock')
 up=json.loads(UP.read_text());un=json.loads(UPAN.read_text());ce=json.loads(CENSUS.read_text());ca=json.loads(CENSUSAN.read_text())
 if not all(up['checks'].values()) or not un.get('gates_pass') or not all(ce['checks'].values()) or not ca.get('gates_pass'):raise SystemExit('upstream evidence gates failed')
 env={**os.environ,'PYTHONPATH':f"{ROOT/'runners/dsl/python'}:{ROOT}:{os.environ.get('PYTHONPATH','')}"};runs=[];fail=[]
 for rep in range(REPS):
  import tempfile
  progress=OUT.with_name(OUT.stem+f'_rep{rep}.progress.jsonl')
  if progress.exists():progress.unlink()
  with tempfile.TemporaryFile(mode='w+t') as stdout:
   q=subprocess.run([sys.executable,str(RUNNER),'--worker',str(rep)],cwd=ROOT,env=env,text=True,stdout=stdout,timeout=3600)
   if q.returncode:fail.append({'replicate':rep,'error':f'worker exited {q.returncode}'});continue
   stdout.seek(0);x=json.loads(stdout.read());runs.append(x);print(f"rep={rep} pid={x['pid']} rows={len(x['rows'])} proposals={x['proposal_searches']} hits={x['cache_hits']}",flush=True)
 after=sources();checks={'three_fresh_workers':len(runs)==REPS and len({r['pid'] for r in runs})==REPS,'no_failures':not fail,'full_320_case_grid':all(len(r['rows'])==320 for r in runs),'source_stable':before==lock['sources']==after and all(r['source_start']==lock['sources']==r['source_end'] for r in runs),'upstream_gates':all(up['checks'].values()) and un.get('gates_pass') and all(ce['checks'].values()) and ca.get('gates_pass'),'topology_reconstruction_and_census_join':all((r['model'],r['fan_in'],r['source_topology_signature']) in {(g['model'],g['fan_in'],g['source_signature']) for cr in ce['runs'] for g in cr['graphs']} for w in runs for r in w['rows']),'exact_energy_and_direct_rescore':all(abs(r['jt_energy']-r['conditioned_energy'])<TOL and abs(r['jt_energy']-r['jt_direct_rescore'])<TOL and abs(r['conditioned_energy']-r['conditioned_direct_rescore'])<TOL for w in runs for r in w['rows']),'exact_prediction_parity':all(r['jt_prediction']==r['conditioned_prediction'] for w in runs for r in w['rows']),'width_certificates':all(r['width']==r['certified_width'] for w in runs for r in w['rows']),'valid_states_and_no_mutation':all(r['state_valid'] and r['no_mutation'] for w in runs for r in w['rows'])}
 OUT.write_text(json.dumps({'schema':'LlmTransportVariedTopologySolverV1_3Capture','lock_sha256':hashlib.sha256(LOCK.read_bytes()).hexdigest(),'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),'sources':before,'post_run_sources':after,'checks':checks,'failures':fail,'runs':runs},indent=2,sort_keys=True)+'\n');print(json.dumps({'capture':OUT.relative_to(ROOT).as_posix(),'checks':checks,'failures':len(fail)},indent=2));return int(not all(checks.values()))
if __name__=='__main__':raise SystemExit(main())
