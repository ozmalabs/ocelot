#!/usr/bin/env python3
"""Exact-inference census over all resident CANs in Bigville's cast100."""
from __future__ import annotations
import hashlib,importlib.util,itertools,json,os,platform,statistics,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT)]
RUNNER=Path(__file__).resolve()
PROTOCOL=ROOT/'docs/research/engine_substrate/BIGVILLE_POPULATION_EXACT_INFERENCE_CENSUS_V1_PREREG_20261002.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_bigville_population_exact_inference_census_v1.py'
REPLAY=ROOT/'scripts/substrate_bigville_can_runtime_partition_replay_v3_1.py'
CAST=ROOT/'seeds/bigville_cast100.json';CAN_SEED=ROOT/'seeds/can_native_reimplementation.json'
BUILDER=ROOT/'worlds/bigville_can_beliefs.py'
LOCK=ROOT/'evaluation/substrate_capability/bigville_population_exact_inference_census_v1_lock_20261002.json'
OUT=ROOT/'evaluation/reports/bigville_population_exact_inference_census_v1_20261002.json'
REPLICATES=3; TOL=1e-8; VOCAB=(-1.0,0.0,1.0)
def digest(path):
 raw=path.read_bytes();return {'path':path.relative_to(ROOT).as_posix(),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def load_replay():
 spec=importlib.util.spec_from_file_location('bigville_partition_replay_v31',REPLAY)
 m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m);return m
def source_lock():
 from substrate_rs import _native
 return {'runner':digest(RUNNER),'protocol':digest(PROTOCOL),'analyzer':digest(ANALYZER),
  'replay_builder':digest(REPLAY),'cast':digest(CAST),'can_seed':digest(CAN_SEED),'bigville_builder':digest(BUILDER),
  'solver_sources':[digest(ROOT/p) for p in ('domains/can_junction_tree.py','domains/graph_treewidth.py')],
  'native_binary':digest(Path(_native.__file__).resolve()),'native_build_manifest':digest(ROOT/'runners/dsl/python/substrate_rs/_native.build.json'),
  'replicates':REPLICATES,'resident_count':100,'vocabulary':list(VOCAB),'tolerance':TOL,
  'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()}
def energy(state,unary,pair):
 return -sum(float(h)*float(state[v]) for v,h in unary.items())-sum(float(w)*float(state[a])*float(state[b]) for (a,b),w in pair.items())
def exhaustive(nodes,unary,pair):
 best=float('inf');arg=None;count=0
 for values in itertools.product(VOCAB,repeat=len(nodes)):
  state=dict(zip(nodes,values));score=energy(state,unary,pair);count+=1
  if score<best:best,arg=score,state
 return best,arg,count
def profile(nodes,edges,order):
 from domains.graph_treewidth import build_elimination_triangulation
 tri=build_elimination_triangulation(nodes,edges,order);bags=tri['bags']
 sizes=[len(b) for b in bags.values()]
 return {'max_bag_size':max(sizes,default=0),'width':max((x-1 for x in sizes),default=0),
  'message_entries':sum(3**(x-1) for x in sizes),'bag_assignments':sum(3**x for x in sizes)}
def worker(rep):
 import substrate_rs as sr
 import domains.can_junction_tree as cjt
 from domains.graph_treewidth import min_fill_upper_bound
 from worlds import bigville_can_beliefs as bigville
 replay=load_replay();cast=json.loads(CAST.read_text())['residents'];seed=json.loads(CAN_SEED.read_text())
 if len(cast)!=100:raise RuntimeError('cast must contain all 100 residents')
 started=source_lock();build_start=time.perf_counter_ns()
 built=replay.build(sr,cast,seed,bigville)
 outer,inner,residents,mts,concepts,frame_nodes,node_frame,directed,cross,refs,node_flat=built
 build_ns=time.perf_counter_ns()-build_start
 graphs=[];oracle_rows=[];local_results=[];extract_start=time.perf_counter_ns()
 for i,mt in enumerate(mts):
  net=cjt.can_network_from_mt(inner,mt)
  nodes=list(net['nodes']);edges=[tuple(sorted(e)) for e in net['edges']]
  if len(nodes)!=5 or len(net['pairwise'])!=5:raise RuntimeError(f'resident {i} unexpected CAN graph size')
  graphs.append({'nodes':nodes,'edges':edges,'unary':dict(net['unary']),'pair':{tuple(sorted(k)):v for k,v in net['pairwise'].items()},'vocab':tuple(net['vocab'])})
 extraction_ns=time.perf_counter_ns()-extract_start
 allnodes=[];alledges=[];unary={};pair={};
 for g in graphs:
  allnodes.extend(g['nodes']);alledges.extend(g['edges']);unary.update(g['unary']);pair.update(g['pair'])
 if len(set(allnodes))!=500 or len(alledges)!=500 or len(cross)!=0:raise RuntimeError('full population graph structure differs from registered frame model')
 local_widths=[];local_profiles=[];local_oracle_total=0.0;local_assignment_total=0;local_times=[]
 for i,g in enumerate(graphs):
  mf=min_fill_upper_bound(g['nodes'],g['edges']);order=mf['elimination_order'];pr=profile(g['nodes'],g['edges'],order)
  if pr['width']!=2:raise RuntimeError(f'resident {i} certified width differs from expected exact component width')
  best,state,assignments=exhaustive(g['nodes'],g['unary'],g['pair']);local_oracle_total+=best;local_assignment_total+=assignments
  t=time.perf_counter_ns();result=cjt.junction_tree_map(g['nodes'],g['edges'],g['unary'],{frozenset(k):v for k,v in g['pair'].items()},g['vocab'],order=order);local_times.append(time.perf_counter_ns()-t)
  rescored=energy(result['state'],g['unary'],g['pair'])
  local_results.append({'resident_position':i,'effective_bins':int(residents[i]['params']['resolution_bins']),
   'nodes':len(g['nodes']),'undirected_edges':len(g['pair']),'width':pr['width'],'oracle_energy':best,
   'jt_energy':float(result['energy']),'direct_rescore':rescored,'valid_state':all(x in VOCAB for x in result['state'].values()),
   'assignments_enumerated':assignments,'timing_ns':int(local_times[-1]),'message_entries':pr['message_entries']})
  local_widths.append(pr['width']);local_profiles.append(pr)
 # Each extracted frame has disjoint node IDs and no cross-frame factor, so union is the unmodified whole model.
 from domains.graph_treewidth import build_elimination_triangulation
 mf_start=time.perf_counter_ns();global_mf=min_fill_upper_bound(allnodes,alledges);global_order=global_mf['elimination_order'];global_order_ns=time.perf_counter_ns()-mf_start
 global_profile=profile(allnodes,alledges,global_order)
 before={nid:dict(inner.node(ref)['attrs']) for nid,ref in refs.items()}
 t=time.perf_counter_ns();whole=cjt.junction_tree_map(allnodes,alledges,unary,{frozenset(k):v for k,v in pair.items()},VOCAB,order=global_order);global_jt_ns=time.perf_counter_ns()-t
 whole_rescore=energy(whole['state'],unary,pair)
 after={nid:dict(inner.node(ref)['attrs']) for nid,ref in refs.items()}
 post=source_lock()
 bins=[int(r['params']['resolution_bins']) for r in residents]
 return {'replicate':rep,'worker_pid':os.getpid(),'resident_count':len(residents),'nodes':len(allnodes),'undirected_edges':len(pair),
  'directed_causal_edges':len(directed),'cross_frame_edges':len(cross),'frame_sizes':[len(x) for x in frame_nodes],
  'certified_widths':local_widths,'effective_bins':bins,'local_results':local_results,'local_oracle_total':local_oracle_total,
  'local_assignment_total':local_assignment_total,'local_jt_median_ns':int(statistics.median(local_times)),
  'local_jt_total_ns':sum(local_times),
  'global_minfill_width':int(global_mf['treewidth']),'global_profile':global_profile,
  'whole_jt_energy':float(whole['energy']),'whole_direct_rescore':whole_rescore,
  'whole_matches_local_oracle':abs(float(whole['energy'])-local_oracle_total)<TOL,
  'all_local_oracles_match':all(abs(r['jt_energy']-r['oracle_energy'])<TOL and abs(r['direct_rescore']-r['oracle_energy'])<TOL and r['valid_state'] for r in local_results),
  'whole_matches_oracle':abs(float(whole['energy'])-local_oracle_total)<TOL and abs(whole_rescore-local_oracle_total)<TOL,
  'no_state_mutation':before==after,'timing_ns':{'population_build':build_ns,'runtime_extraction_all_frames':extraction_ns,
    'global_minfill_order':global_order_ns,'whole_population_jt':global_jt_ns},
  'source_lock_start':started,'source_lock_end':post}
def main():
 args=sys.argv[1:]
 if args[:1]==['--worker']:
  print(json.dumps(worker(int(args[1])),sort_keys=True,separators=(',',':')));return 0
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite lock/capture')
  LOCK.write_text(json.dumps({'schema':'BigvillePopulationExactInferenceCensusV1Lock','sources':source_lock()},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if args!=['--run']:raise SystemExit('usage: --lock, --run, or --worker REP')
 lock=json.loads(LOCK.read_text())
 if source_lock()!=lock['sources']:raise SystemExit('source/input drift from lock')
 from domains.engine_provenance import build_is_stale
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit('native engine stale: '+'; '.join(stale))
 env={**os.environ,'PYTHONPATH':f"{ROOT/'runners/dsl/python'}:{ROOT}:{os.environ.get('PYTHONPATH','')}"};rows=[]
 for rep in range(REPLICATES):
  p=subprocess.run([sys.executable,str(RUNNER),'--worker',str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=600)
  if p.returncode:raise RuntimeError(f'replicate={rep}: {p.stderr[-3000:]}')
  row=json.loads(p.stdout.strip());rows.append(row)
  print(f"rep={rep} workers={row['worker_pid']} residents={row['resident_count']} nodes={row['nodes']} global_width={row['global_minfill_width']} globalJT={row['timing_ns']['whole_population_jt']/1e6:.2f}ms localJTmedian={row['local_jt_median_ns']/1e6:.3f}ms",flush=True)
 post=source_lock();checks={'replicate_count':len(rows)==REPLICATES,'fresh_processes':len({r['worker_pid'] for r in rows})==REPLICATES,
  'full_cast_census':all(r['resident_count']==100 and len(r['local_results'])==100 for r in rows),
  'expected_model_shape':all(r['nodes']==500 and r['undirected_edges']==500 and r['directed_causal_edges']==1000 and r['cross_frame_edges']==0 and set(r['frame_sizes'])=={5} for r in rows),
  'all_local_exact_oracles':all(r['all_local_oracles_match'] for r in rows),'whole_matches_local_oracle':all(r['whole_matches_oracle'] and r['whole_matches_local_oracle'] for r in rows),
  'width_certificates':all(set(r['certified_widths'])=={2} and r['global_minfill_width']==2 and r['global_profile']['width']==2 for r in rows),
  'no_mutation':all(r['no_state_mutation'] for r in rows),'worker_source_locks':all(r['source_lock_start']==lock['sources']==r['source_lock_end'] for r in rows),
  'pre_post_lock':post==lock['sources']}
 payload={'schema':'BigvillePopulationExactInferenceCensusV1Results','lock_sha256':hashlib.sha256(LOCK.read_bytes()).hexdigest(),
  'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),'sources':source_lock(),'post_run_sources':post,
  'configuration':{'replicates':REPLICATES,'residents_per_replicate':100,'states_per_concept':3},
  'claim_boundary':'complete census of one authored/generated Bigville population with disconnected-by-design resident CANs; not natural cheap-cut prevalence',
  'checks':checks,'runs':rows}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'capture':OUT.relative_to(ROOT).as_posix(),'checks':checks},indent=2))
 if not all(checks.values()):raise SystemExit('population inference census gate failed')
if __name__=='__main__':main()
