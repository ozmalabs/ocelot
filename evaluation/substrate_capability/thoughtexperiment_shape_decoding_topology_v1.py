#!/usr/bin/env python3
"""Locked node-count scaling panel for positive/negative shape-decoding rehearsals."""
from __future__ import annotations
import hashlib,json,os,platform,statistics,subprocess,sys,threading,time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
RUNNER=Path(__file__).resolve();LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_shape_decoding_topology_v1_lock_20261001.json';RAW=ROOT/'evaluation/reports/thoughtexperiment_shape_decoding_topology_v1_raw_20261001.json'
TOPOLOGIES=('path','star','grid','random4','observation_spokes');SIZE=100000;BACKENDS=('native_full_copy_scoped','native_shared_graph_pages_scoped');MODES=('sequential','concurrent');ARMS=('positive','negative');FANOUT=8
SOURCES=('docs/research/engine_substrate/THOUGHTEXPERIMENT_SHAPE_DECODING_TOPOLOGY_V1_PREREG_20261001.md','evaluation/substrate_capability/thoughtexperiment_shape_decoding_topology_v1.py','evaluation/substrate_capability/thoughtexperiment_self_correction_copy_comparison_v1.py','domains/self_correction.py','domains/collapse_model.py','domains/imagination.py','domains/reflective_faculty.py','substrate/boot_core.py','seeds/shape_decode_loop.json','runners/dsl/python/substrate_rs/__init__.py','runners/dsl/src/cow_paged_vec.rs','runners/dsl/src/graph.rs','runners/dsl/src/grammar.rs','runners/dsl/src/checker.rs','runners/dsl/src/term.rs','runners/dsl/src/substrate.rs','runners/dsl/src/py.rs','runners/dsl/src/persist.rs','domains/engine_provenance.py')
def sha(p):return 'sha256:'+hashlib.sha256(Path(p).read_bytes()).hexdigest()
def host_info():
 try:quota=Path('/sys/fs/cgroup/cpu.max').read_text().strip()
 except OSError:quota=None
 status=Path('/proc/self/status').read_text();allowed=next((x.split(':',1)[1].strip() for x in status.splitlines() if x.startswith('Cpus_allowed_list:')),None)
 return {'platform':platform.platform(),'logical_cpus':os.cpu_count(),'cpus_allowed_list':allowed,'cgroup_cpu_max':quota}
def signature(r):
 keys=('converges','inert','applied_targets','residual_before','residual_after','frontier_growth_after','steps_run','n_conclusions','conclusions','derived_only')
 return json.dumps({k:r[k] for k in keys},sort_keys=True,default=str)
def worker(topology,backend,mode,rep):
 from evaluation.substrate_capability.thoughtexperiment_self_correction_copy_comparison_v1 import make_fixture
 from domains.collapse_model import predict_collapse
 from domains.self_correction import imagine_and_check_convergence
 before={p:sha(ROOT/p) for p in SOURCES};sub,native,positive,negative,observations=make_fixture(SIZE)
 noise=sorted(sub.nodes('ThoughtexperimentNoise'),key=lambda n:sub.node(n)['attrs']['ordinal'])
 if topology!='path':
  for i in range(len(noise)-1):sub.remove_edge(noise[i],'te_noise_next',noise[i+1])
  edges=[]
  if topology=='star':edges=[(noise[0],noise[i]) for i in range(1,len(noise))]
  elif topology=='grid':
   width=int(len(noise)**0.5)
   for i in range(len(noise)):
    if i%width+1<width and i+1<len(noise):edges.append((noise[i],noise[i+1]))
    if i+width<len(noise):edges.append((noise[i],noise[i+width]))
  elif topology=='random4':
   import random
   rng=random.Random(341901)
   for i in range(len(noise)):
    for _ in range(2):
     j=rng.randrange(len(noise))
     if i!=j:edges.append((noise[i],noise[j]))
  elif topology=='observation_spokes':edges=[(observations[i%len(observations)],noise[i]) for i in range(len(noise))]
  else:raise ValueError(topology)
  for src,tgt in edges:sub.add_edge_unchecked(src,'te_noise_topology',tgt)
 baseline=predict_collapse(sub,horizon=3,imagine_steps=2,focus_hops=1,snapshot_backend=backend,record_trace=False)
 revision=native.experiment_graph_rule_revision();counts=(native.node_count(),native.edge_count());rules=json.dumps(native.export_rules(),sort_keys=True,default=str)
 candidates={'positive':positive,'negative':negative};order=ARMS if rep%2==0 else tuple(reversed(ARMS));arm_rows=[]
 for arm in order:
  candidate=candidates[arm];barrier=threading.Barrier(FANOUT) if mode=='concurrent' else None
  def rehearse(_):
   if barrier:barrier.wait()
   w0=time.perf_counter_ns();c0=time.thread_time_ns()
   result=imagine_and_check_convergence(sub,candidate,model_before=baseline,horizon=3,imagine_steps=2,experiment_focus_nodes=observations,focus_hops=1,snapshot_backend=backend,_prediction_snapshot_backend=backend,_measure_phases=True,record_trace=False)
   phases=result['phase_timings_ms'];cpu=(time.thread_time_ns()-c0)/1e6;wall=(time.perf_counter_ns()-w0)/1e6
   return {'wall_ms':wall,'thread_cpu_ms':cpu,'converges':bool(result['converges']),'inert':bool(result['inert']),'applied_targets':sorted(result['applied']),'residual_before':float(result['model_before'].residual),'residual_after':float(result['model_after'].residual),'frontier_growth_after':float(result['model_after'].frontier_growth_rate),'steps_run':int(result['model_after'].imagine_steps_run),'n_conclusions':int(result['imagined'].n_conclusions),'conclusions':result['imagined'].conclusions,'derived_only':result['imagined'].derived_only,'phase_timings_ms':phases}
  start=time.perf_counter_ns()
  if mode=='concurrent':
   with ThreadPoolExecutor(max_workers=FANOUT) as pool:results=list(pool.map(rehearse,range(FANOUT)))
  else:results=[rehearse(i) for i in range(FANOUT)]
  wall=(time.perf_counter_ns()-start)/1e6
  arm_rows.append({'arm':arm,'candidate':candidate['label'],'wave_wall_ms':wall,'sum_thread_cpu_ms':sum(r['thread_cpu_ms'] for r in results),'cpu_overlap_factor':sum(r['thread_cpu_ms'] for r in results)/wall,'results':results})
 primary_unchanged=native.experiment_graph_rule_revision()==revision and (native.node_count(),native.edge_count())==counts and json.dumps(native.export_rules(),sort_keys=True,default=str)==rules
 after={p:sha(ROOT/p) for p in SOURCES}
 return {'pid':os.getpid(),'topology':topology,'size_added_nodes':SIZE,'observed_node_count':counts[0],'observed_edge_count':counts[1],'backend':backend,'mode':mode,'replicate':rep,'fanout':FANOUT,'arms':arm_rows,'primary_unchanged':primary_unchanged,'source_hashes_before':before,'sources_stable':before==after}
def main():
 if len(sys.argv)==6 and sys.argv[1]=='--worker':print(json.dumps(worker(sys.argv[2],sys.argv[3],sys.argv[4],int(sys.argv[5])),sort_keys=True,default=str));return 0
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit('stale native engine: '+'; '.join(stale))
 env={**os.environ,'PYTHONPATH':f"{ROOT/'runners/dsl/python'}:{ROOT}"};rows=[]
 for rep in range(3):
  for topology in (TOPOLOGIES if rep%2==0 else tuple(reversed(TOPOLOGIES))):
   for mode in MODES:
    for backend in (BACKENDS if (rep+TOPOLOGIES.index(topology))%2==0 else tuple(reversed(BACKENDS))):
     p=subprocess.run([sys.executable,str(RUNNER),'--worker',topology,backend,mode,str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,check=True);rows.append(json.loads(p.stdout.strip().splitlines()[-1]))
 lock=json.loads(LOCK.read_text());source_lock=all(sha(ROOT/p)==h for p,h in lock['sources'].items())
 from substrate_rs import _native
 binary=Path(_native.__file__).resolve();binary_lock=sha(binary)==lock['native_binary']['sha256']
 gate={'60_unique_fresh_processes':len(rows)==60 and len({r['pid'] for r in rows})==60,'all_cells_present':len({(r['topology'],r['backend'],r['mode']) for r in rows})==len(TOPOLOGIES)*len(BACKENDS)*len(MODES),'source_native_lock':source_lock and binary_lock and all(r['sources_stable'] for r in rows),'primary_isolation':all(r['primary_unchanged'] for r in rows),'positive_task_oracle':all(all(x['converges'] and not x['inert'] and 'sd_mint_quantum' in x['applied_targets'] for a in r['arms'] if a['arm']=='positive' for x in a['results']) for r in rows),'negative_task_oracle':all(all(not x['converges'] and not x['inert'] and 'sd_mint_quantum' in x['applied_targets'] for a in r['arms'] if a['arm']=='negative' for x in a['results']) for r in rows),'cross_backend_mode_signature_parity':False,'positive_negative_semantics_contrast':False,'nonnegative_timings_and_counts':all(r['observed_node_count']>0 and r['observed_edge_count']>0 and all(a['wave_wall_ms']>0 and a['sum_thread_cpu_ms']>=0 and all(x['thread_cpu_ms']>=0 for x in a['results']) for a in r['arms']) for r in rows),'topology_node_edge_counts_stable':all(len({(r['observed_node_count'],r['observed_edge_count']) for r in rows if r['topology']==topology})==1 for topology in TOPOLOGIES)}
 # Exact result parity across backend and execution mode, grouped by size/arm.
 parity=True
 for topology in TOPOLOGIES:
  for arm in ARMS:
   for mode in MODES:
    signatures={signature(x) for r in rows if r['topology']==topology and r['mode']==mode for a in r['arms'] if a['arm']==arm for x in a['results']}
    if len(signatures)!=1:parity=False
 gate['cross_backend_mode_signature_parity']=parity
 contrast=True
 for topology in TOPOLOGIES:
  for backend in BACKENDS:
   for mode in MODES:
    pos={signature(x) for r in rows if (r['topology'],r['backend'],r['mode'])==(topology,backend,mode) for a in r['arms'] if a['arm']=='positive' for x in a['results']}
    neg={signature(x) for r in rows if (r['topology'],r['backend'],r['mode'])==(topology,backend,mode) for a in r['arms'] if a['arm']=='negative' for x in a['results']}
    if not pos or not neg or pos==neg:contrast=False
 gate['positive_negative_semantics_contrast']=contrast
 summaries=[]
 for topology in TOPOLOGIES:
  for backend in BACKENDS:
   for mode in MODES:
    rr=[r for r in rows if (r['topology'],r['backend'],r['mode'])==(topology,backend,mode)]
    for arm in ARMS:
     aa=[a for r in rr for a in r['arms'] if a['arm']==arm]
     phases=('branch_snapshot_and_setup','candidate_rule_patch','model_after_prediction')
     summaries.append({'topology':topology,'backend':backend,'mode':mode,'arm':arm,'median_wave_wall_ms':statistics.median(a['wave_wall_ms'] for a in aa),'median_sum_thread_cpu_ms':statistics.median(a['sum_thread_cpu_ms'] for a in aa),'median_cpu_overlap_factor':statistics.median(a['cpu_overlap_factor'] for a in aa),'median_phase_wall_ms':{k:statistics.median(x['phase_timings_ms'][k] for a in aa for x in a['results']) for k in phases}})
 gates=gate
 capture={'schema':'ThoughtexperimentShapeDecodingTopologyV1','captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':host_info(),'engine_fingerprint':rust_source_fingerprint(str(ROOT)),'native_binary':{'path':str(binary),'sha256':sha(binary)},'lock_sha256':sha(LOCK),'protocol':{'size_added_nodes':SIZE,'topologies':list(TOPOLOGIES),'backends':list(BACKENDS),'modes':list(MODES),'arms':list(ARMS),'fanout':FANOUT,'repeats_per_cell':3},'rows':rows,'summaries':summaries,'gates':gates}
 RAW.parent.mkdir(parents=True,exist_ok=True);RAW.write_text(json.dumps(capture,indent=2,sort_keys=True)+'\n');print(json.dumps({'gates':gates,'summaries':summaries,'raw':str(RAW)},indent=2,sort_keys=True));return 0 if all(gates.values()) else 1
if __name__=='__main__':raise SystemExit(main())
