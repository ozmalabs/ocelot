#!/usr/bin/env python3
"""Measure owner-frame discovery and dynamic boundary-index maintenance."""
from __future__ import annotations
import copy,hashlib,importlib.util,json,os,platform,random,resource,subprocess,sys,time
from collections import Counter
from pathlib import Path
from domains.engine_provenance import engine_preamble,provenance_line,rust_source_fingerprint
engine_preamble()
from substrate_rs import _native
ROOT=Path(__file__).resolve().parents[1]
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_BIGVILLE_BOUNDARY_INDEX_COST_PREREG_20260926.md'
LOCK=ROOT/'evaluation/substrate_capability/bigville_boundary_index_cost_lock_20260926.json'
OUT=ROOT/'evaluation/reports/substrate_bigville_boundary_index_cost_v1_20260926.json'
BASE=ROOT/'scripts/substrate_bigville_can_runtime_partition_replay_v3_1.py'
CAST=ROOT/'seeds/bigville_cast100.json';SEED=ROOT/'seeds/can_native_reimplementation.json';BUILDER=ROOT/'worlds/bigville_can_beliefs.py'
TOPOLOGIES=('ring','star','random_connected');REPS=3;SAMPLES=31;SCHEDULE_SEED=20260927;FRAME_SIZE=5;FRAME_COUNT=100
FILES=['scripts/substrate_bigville_boundary_index_cost_v1.py','scripts/analyze_substrate_bigville_boundary_index_cost_v1.py','docs/research/engine_substrate/SUBSTRATE_BIGVILLE_BOUNDARY_INDEX_COST_PREREG_20260926.md','scripts/substrate_bigville_can_runtime_partition_replay_v3_1.py','seeds/bigville_cast100.json','seeds/can_native_reimplementation.json','worlds/bigville_can_beliefs.py','domains/engine_provenance.py','runners/dsl/src/graph.rs','runners/dsl/src/rewrite.rs','runners/dsl/src/substrate.rs','runners/dsl/src/py.rs','runners/dsl/python/substrate_rs/_native.build.json']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load_base():
 spec=importlib.util.spec_from_file_location('bigville_boundary_base',BASE)
 if spec is None or spec.loader is None:raise RuntimeError('cannot load authored Bigville graph builder')
 mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
def topology_pairs(topology,rep,count=100):
 if topology=='ring':return [(i,(i+1)%count) for i in range(count)]
 if topology=='star':return [(0,i) for i in range(1,count)]
 rng=random.Random(20260925+rep*1009);pairs=[]
 for child in range(1,count):pairs.append((rng.randrange(child),child))
 have={tuple(sorted(x)) for x in pairs};candidates=[(i,j) for i in range(count) for j in range(i+1,count) if (i,j) not in have];rng.shuffle(candidates);pairs.extend(candidates[:count-len(pairs)])
 return pairs
def owner_map(inner,ref_by_id,mts,nid):
 mt_pos={nid(mt):i for i,mt in enumerate(mts)};out={}
 for node,ref in ref_by_id.items():
  owners=[nid(x) for x in inner.in_neighbours(ref,'has_concept')]
  if len(owners)!=1 or owners[0] not in mt_pos:raise ValueError('concept has missing/ambiguous live owner')
  out[int(node)]=mt_pos[owners[0]]
 return out
def live_edges(inner,ref_by_id,nid):
 out=[]
 for node in sorted(ref_by_id):
  for other in inner.neighbours(ref_by_id[node],'causal_influence'):
   out.append((int(node),nid(other)))
 return out
def build_index(edges_flat,owner_flat):
 undirected={tuple(sorted((int(a),int(b)))) for a,b in edges_flat if int(a)!=int(b)}
 cross={e for e in undirected if owner_flat[e[0]]!=owner_flat[e[1]]}
 return {'cross_edges':cross}
def index_profile(index,owner_flat):
 degrees=Counter();boundary={};pairs=Counter();edge_inc=Counter()
 for a,b in index['cross_edges']:
  fa,fb=owner_flat[a],owner_flat[b];degrees[a]+=1;degrees[b]+=1;pairs[tuple(sorted((fa,fb)))]+=1;edge_inc[fa]+=1;edge_inc[fb]+=1
 for node,deg in degrees.items():boundary.setdefault(owner_flat[node],[]).append(node)
 sizes=[len(boundary.get(f,())) for f in range(FRAME_COUNT)];inc=[edge_inc[f] for f in range(FRAME_COUNT)]
 return {'undirected_cross_edges':len(index['cross_edges']),'directed_cross_edges':2*len(index['cross_edges']),'active_boundary_frames':sum(x>0 for x in sizes),'boundary_node_ids_by_frame':{str(f):sorted(v) for f,v in sorted(boundary.items())},'boundary_sizes_by_frame':sizes,'incident_cross_edges_by_frame':inc,'owner_pair_edge_multiplicity':{f'{a}:{b}':v for (a,b),v in sorted(pairs.items())},'max_boundary_size':max(sizes,default=0),'max_frame_fanout':max(inc,default=0)}
def mutate_index(idx,owner_flat,add_flat=(),remove_flat=()):
 result={'cross_edges':set(idx['cross_edges'])}
 for pair in remove_flat:
  edge=tuple(sorted(map(int,pair)))
  if owner_flat[edge[0]]!=owner_flat[edge[1]]:result['cross_edges'].discard(edge)
 for pair in add_flat:
  edge=tuple(sorted(map(int,pair)))
  if owner_flat[edge[0]]!=owner_flat[edge[1]]:result['cross_edges'].add(edge)
 return result
def timed_samples(fn,n=SAMPLES):
 fn();values=[]
 for _ in range(n):
  t=time.perf_counter_ns();fn();values.append(time.perf_counter_ns()-t)
 return values
def worker(topology,rep):
 import substrate_rs as sr
 from substrate_rs import _native
 from domains import engine_provenance as ep
 from worlds import bigville_can_beliefs as bigville
 base=load_base();cast=json.loads(CAST.read_text())['residents'];seed=json.loads(SEED.read_text())
 t0=time.perf_counter_ns();(outer,inner,residents,mts,concepts,frame_nodes,node_frame,edges,cross,ref_by_id,node_flat)=base.build(sr,cast,seed,bigville);full_build_ns=time.perf_counter_ns()-t0
 if len(frame_nodes)!=FRAME_COUNT or set(map(len,frame_nodes))!={FRAME_SIZE} or cross:raise RuntimeError('baseline partition precondition failed')
 nid=base.nid;initial_owner={int(k):int(v) for k,v in node_frame.items()};mapped_owner=owner_map(inner,ref_by_id,mts,nid)
 if mapped_owner!=initial_owner:raise RuntimeError('live has_concept owner map does not match runtime frame partition')
 owner_flat={int(node_flat[n]):f for n,f in mapped_owner.items()}
 if len(owner_flat)!=FRAME_COUNT*FRAME_SIZE or set(owner_flat.values())!=set(range(FRAME_COUNT)):raise RuntimeError('bad flat owner projection')
 initial_live=live_edges(inner,ref_by_id,nid);initial_flat=[(node_flat[a],node_flat[b]) for a,b in initial_live]
 index=build_index(initial_flat,owner_flat);initial_profile=index_profile(index,owner_flat)
 def owner_call():return owner_map(inner,ref_by_id,mts,nid)
 def live_call():return live_edges(inner,ref_by_id,nid)
 def rebuild_call():return index_profile(build_index([(node_flat[a],node_flat[b]) for a,b in live_call()],owner_flat),owner_flat)
 def record(stage,mutation_ns,adds=(),removes=()):
  nonlocal index
  live=live_call();flat=[(node_flat[a],node_flat[b]) for a,b in live]
  owner_times=timed_samples(owner_call);edge_times=timed_samples(live_call)
  rebuild_times=timed_samples(lambda: index_profile(build_index(flat,owner_flat),owner_flat))
  incr_times=timed_samples(lambda: index_profile(mutate_index(index,owner_flat,adds,removes),owner_flat)) if adds or removes else [0]*SAMPLES
  next_index=mutate_index(index,owner_flat,adds,removes);rebuilt=index_profile(build_index(flat,owner_flat),owner_flat);incremental=index_profile(next_index,owner_flat)
  owner_now=owner_call()
  if owner_now!=initial_owner:raise RuntimeError('owner membership changed in a link-only sequence')
  if len(live)!=len(edges) or set(live)!=set(edges):raise RuntimeError('caller directed-edge projection differs from live native graph')
  if rebuilt!=incremental:raise RuntimeError('incremental boundary index diverges from full rebuild')
  index=next_index
  return {'stage':stage,'raw_graph_mutation_ns':mutation_ns,'owner_discovery_samples_ns':owner_times,'live_edge_extraction_samples_ns':edge_times,'boundary_rebuild_samples_ns':rebuild_times,'incremental_update_samples_ns':incr_times,'profile':rebuilt,'owner_frame_count':len(set(owner_now.values())),'owner_frame_sizes':[sum(v==f for v in owner_now.values()) for f in range(FRAME_COUNT)]}
 checkpoints=[];all_pairs=topology_pairs(topology,rep);removed=all_pairs[::3];active={};id_pairs={};flat_pairs={}
 def add_pair(pair,weight):
  a,b=pair;ra=concepts[a]['world_safe'];rb=concepts[b]['world_safe'];aid,bid=nid(ra),nid(rb)
  inner.add_edge_unchecked(ra,'causal_influence',rb,{'weight':weight});inner.add_edge_unchecked(rb,'causal_influence',ra,{'weight':weight})
  edges.extend(((aid,bid),(bid,aid)));cross.extend(((aid,bid),(bid,aid)))
  fpair=(int(node_flat[aid]),int(node_flat[bid]));flat_pairs[pair]=fpair;id_pairs[pair]=(aid,bid);active[pair]=weight
 def remove_pair(pair):
  aid,bid=id_pairs.pop(pair);ra,rb=ref_by_id[aid],ref_by_id[bid]
  inner.remove_edge(ra,'causal_influence',rb);inner.remove_edge(rb,'causal_influence',ra)
  edges.remove((aid,bid));edges.remove((bid,aid));cross.remove((aid,bid));cross.remove((bid,aid));active.pop(pair)
 checkpoints.append(record('runtime_partition_baseline',0))
 t=time.perf_counter_ns()
 for pair in all_pairs:add_pair(pair,0.2)
 mut=time.perf_counter_ns()-t
 checkpoints.append(record('insert_cross_links',mut,[flat_pairs[p] for p in all_pairs]))
 # Evidence writes do not alter graph structure; include a stable checkpoint control.
 checkpoints.append(record('authored_evidence_update',0))
 t=time.perf_counter_ns()
 for pair in removed:remove_pair(pair)
 mut=time.perf_counter_ns()-t
 checkpoints.append(record('delete_one_third',mut,removes=[flat_pairs[p] for p in removed]))
 # Reweight native edges by replacement; topology index should need no update.
 t=time.perf_counter_ns();to_replace=list(active)
 for pair in to_replace:
  remove_pair(pair);add_pair(pair,0.35)
 mut=time.perf_counter_ns()-t
 checkpoints.append(record('reweight_remaining',mut))
 t=time.perf_counter_ns()
 for pair in removed:add_pair(pair,0.35)
 mut=time.perf_counter_ns()-t
 checkpoints.append(record('reinsert_deleted_pairs',mut,[flat_pairs[p] for p in removed]))
 t=time.perf_counter_ns();to_remove=list(active)
 for pair in to_remove:remove_pair(pair)
 mut=time.perf_counter_ns()-t
 checkpoints.append(record('remove_all_cross_links',mut,removes=[flat_pairs[p] for p in to_remove]))
 native=Path(_native.__file__).resolve()
 return {'topology':topology,'replicate':rep,'pid':os.getpid(),'pair_count':len(all_pairs),'removed_pair_count':len(removed),'full_graph_build_and_initial_partition_ns':full_build_ns,'baseline_profile':initial_profile,'owner_frame_count':len(frame_nodes),'owner_frame_sizes':[len(x) for x in frame_nodes],'node_frame':{str(k):v for k,v in node_frame.items()},'checkpoints':checkpoints,'peak_rss_kib':int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),'native_path':str(native),'native_sha256':sha(native),'engine_provenance':provenance_line()}
def main():
 lock_data={'schema_version':1,'locked_inputs':{'files_sha256':{p:sha(ROOT/p) for p in FILES},'native_path':str(Path(_native.__file__).resolve()),'native_sha256':sha(Path(_native.__file__).resolve()),'rust_source_fingerprint':rust_source_fingerprint(str(ROOT))},'design':{'topologies':list(TOPOLOGIES),'replicates':REPS,'timing_samples_per_operation':SAMPLES,'schedule_seed':SCHEDULE_SEED,'frame_count':FRAME_COUNT,'frame_size':FRAME_SIZE}}
 if sys.argv[1:]==['--lock']:print(json.dumps(lock_data,indent=2,sort_keys=True));return
 if len(sys.argv)==4 and sys.argv[1]=='--worker':print(json.dumps(worker(sys.argv[2],int(sys.argv[3])),sort_keys=True));return
 if not LOCK.exists() or json.loads(LOCK.read_text())!=lock_data:raise SystemExit('missing/changed pre-run lock')
 env=dict(os.environ);env['PYTHONPATH']=f"{ROOT}:{ROOT/'runners/dsl/python'}:{env.get('PYTHONPATH','')}"
 stale=subprocess.check_output([sys.executable,'-c',"from domains.engine_provenance import build_is_stale; print('\\n'.join(build_is_stale('.')))"] ,cwd=ROOT,env=env,text=True).strip()
 if stale:raise SystemExit('native build stale:\n'+stale)
 jobs=[(t,r) for t in TOPOLOGIES for r in range(REPS)];random.Random(SCHEDULE_SEED).shuffle(jobs);runs=[];start=time.perf_counter()
 for topology,rep in jobs:
  p=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker',topology,str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,check=True,timeout=180)
  row=json.loads(p.stdout);runs.append(row);print(f"{topology} rep={rep} pid={row['pid']} frames={row['owner_frame_count']}",flush=True)
 native=Path(_native.__file__).resolve();out={'protocol':'BIGVILLE_BOUNDARY_INDEX_COST_V1','locked_inputs':lock_data,'lock_sha256':sha(LOCK),'engine':provenance_line(),'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'environment':{'python':sys.version,'platform':platform.platform()},'schedule':jobs,'workers':runs,'worker_count':len(runs),'parent_elapsed_seconds':time.perf_counter()-start,'native':{'path':str(native),'sha256':sha(native)},'claim_boundary':'authored Bigville owner-frame and boundary-index construction/update costs; no rule closure or natural-task prevalence claim'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':str(OUT),'workers':len(runs)},indent=2))
if __name__=='__main__':main()
