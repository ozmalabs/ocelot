#!/usr/bin/env python3
"""Measure per-thread CPU and timed phases in shape-decoding rehearsal waves."""
from __future__ import annotations
import cProfile,hashlib,json,os,platform,pstats,statistics,subprocess,sys,threading,time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
RUNNER=Path(__file__).resolve();LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_shape_decoding_python_native_profile_v3_lock_20261001.json';RAW=ROOT/'evaluation/reports/thoughtexperiment_shape_decoding_python_native_profile_v3_raw_20261001.json'
BACKENDS=('native_full_copy_scoped','native_shared_graph_pages_scoped');MODES=('sequential','concurrent');FANOUT=8;SIZE=100000
SOURCES=('docs/research/engine_substrate/THOUGHTEXPERIMENT_SHAPE_DECODING_PYTHON_NATIVE_PROFILE_V3_PREREG_20261001.md','docs/research/engine_substrate/THOUGHTEXPERIMENT_SHAPE_DECODING_PYTHON_NATIVE_PROFILE_V3_AMENDMENT_20261001.md','docs/research/engine_substrate/THOUGHTEXPERIMENT_SHAPE_DECODING_PYTHON_NATIVE_PROFILE_V2_RESULTS_20261001.md','docs/research/engine_substrate/THOUGHTEXPERIMENT_SHAPE_DECODING_CONCURRENCY_PROFILE_V3_RESULTS_20261001.md','docs/research/engine_substrate/THOUGHTEXPERIMENT_SHAPE_DECODING_RULE_PATCH_V4_RESULTS_20261001.md','evaluation/substrate_capability/thoughtexperiment_shape_decoding_python_native_profile_v3.py','evaluation/substrate_capability/thoughtexperiment_self_correction_copy_comparison_v1.py','domains/self_correction.py','domains/collapse_model.py','domains/imagination.py','domains/reflective_faculty.py','substrate/boot_core.py','seeds/shape_decode_loop.json','runners/dsl/python/substrate_rs/__init__.py','runners/dsl/src/cow_paged_vec.rs','runners/dsl/src/graph.rs','runners/dsl/src/grammar.rs','runners/dsl/src/checker.rs','runners/dsl/src/term.rs','runners/dsl/src/substrate.rs','runners/dsl/src/py.rs','runners/dsl/src/persist.rs','domains/engine_provenance.py')
def sha(path):return 'sha256:'+hashlib.sha256(Path(path).read_bytes()).hexdigest()
def host_info():
 try:quota=Path('/sys/fs/cgroup/cpu.max').read_text().strip()
 except OSError:quota=None
 status=Path('/proc/self/status').read_text();allowed=next((x.split(':',1)[1].strip() for x in status.splitlines() if x.startswith('Cpus_allowed_list:')),None)
 return {'platform':platform.platform(),'logical_cpus':os.cpu_count(),'cpus_allowed_list':allowed,'cgroup_cpu_max':quota}
def worker(backend,mode,rep):
 from evaluation.substrate_capability.thoughtexperiment_self_correction_copy_comparison_v1 import make_fixture
 from domains.collapse_model import predict_collapse
 from domains.self_correction import imagine_and_check_convergence
 before={p:sha(ROOT/p) for p in SOURCES};sub,native,candidate,_wrong,observations=make_fixture(SIZE)
 baseline=predict_collapse(sub,horizon=3,imagine_steps=2,focus_hops=1,snapshot_backend=backend,record_trace=False)
 revision=native.experiment_graph_rule_revision();counts=(native.node_count(),native.edge_count());rules=json.dumps(native.export_rules(),sort_keys=True,default=str)
 barrier=threading.Barrier(FANOUT) if mode=='concurrent' else None
 def rehearse(index):
  if barrier:barrier.wait()
  wall0=time.perf_counter_ns();cpu0=time.thread_time_ns()
  # cProfile with a thread CPU timer is valid in isolated sequential runs only.
  profiled=mode=='sequential'
  profiler=cProfile.Profile(timer=time.thread_time_ns,timeunit=1e-9) if profiled else None
  if profiler:profiler.enable()
  result=imagine_and_check_convergence(sub,candidate,model_before=baseline,horizon=3,imagine_steps=2,experiment_focus_nodes=observations,focus_hops=1,snapshot_backend=backend,_prediction_snapshot_backend=backend,_measure_phases=True,_native_rule_patch=True,record_trace=False)
  if profiler:profiler.disable()
  cpu=(time.thread_time_ns()-cpu0)/1e6;wall=(time.perf_counter_ns()-wall0)/1e6;phases=result['phase_timings_ms']
  sites=[];python_cpu=0.0;c_cpu=0.0
  if profiler:
   prof=pstats.Stats(profiler)
   for (filename,line,name),(_cc,_nc,self_s,_cum_s,_callers) in prof.stats.items():
    self_ms=float(self_s)*1000
    if filename=='~':c_cpu+=self_ms
    else:python_cpu+=self_ms
    if self_ms>0:sites.append({'filename':filename,'line':line,'name':name,'self_cpu_ms':self_ms,'kind':'c' if filename=='~' else 'python'})
  sites.sort(key=lambda x:x['self_cpu_ms'],reverse=True)
  return {'wall_ms':wall,'thread_cpu_ms':cpu,'profiled':profiled,'python_self_cpu_ms':python_cpu,'c_call_self_cpu_ms':c_cpu,'profiled_cpu_ms':python_cpu+c_cpu,'top_profile_sites':sites[:20],'converges':bool(result['converges']),'inert':bool(result['inert']),'applied_targets':sorted(result['applied']),'residual_before':float(result['model_before'].residual),'residual_after':float(result['model_after'].residual),'frontier_growth_after':float(result['model_after'].frontier_growth_rate),'steps_run':int(result['model_after'].imagine_steps_run),'n_conclusions':int(result['imagined'].n_conclusions),'conclusions':result['imagined'].conclusions,'derived_only':result['imagined'].derived_only,'phase_timings_ms':phases}
 start=time.perf_counter_ns()
 if mode=='concurrent':
  with ThreadPoolExecutor(max_workers=FANOUT) as pool:results=list(pool.map(rehearse,range(FANOUT)))
 else:results=[rehearse(i) for i in range(FANOUT)]
 wave_ms=(time.perf_counter_ns()-start)/1e6
 primary_unchanged=native.experiment_graph_rule_revision()==revision and (native.node_count(),native.edge_count())==counts and json.dumps(native.export_rules(),sort_keys=True,default=str)==rules
 after={p:sha(ROOT/p) for p in SOURCES}
 return {'pid':os.getpid(),'backend':backend,'mode':mode,'replicate':rep,'fanout':FANOUT,'size':SIZE,'candidate':candidate['label'],'wave_wall_ms':wave_ms,'sum_thread_cpu_ms':sum(r['thread_cpu_ms'] for r in results),'cpu_overlap_factor':sum(r['thread_cpu_ms'] for r in results)/wave_ms,'python_self_cpu_ms':sum(r['python_self_cpu_ms'] for r in results),'c_call_self_cpu_ms':sum(r['c_call_self_cpu_ms'] for r in results),'profiled_cpu_ms':sum(r['profiled_cpu_ms'] for r in results),'top_profile_sites':[site for r in results for site in r['top_profile_sites']],'valid_results':sum(r['converges'] and not r['inert'] and 'sd_mint_quantum' in r['applied_targets'] for r in results),'results':results,'primary_unchanged':primary_unchanged,'source_hashes_before':before,'source_hashes_after':after,'sources_stable':before==after}
def signature(r):
 keys=('converges','inert','applied_targets','residual_before','residual_after','frontier_growth_after','steps_run','n_conclusions','conclusions','derived_only')
 return json.dumps({k:r[k] for k in keys},sort_keys=True,default=str)
def main():
 if len(sys.argv)==5 and sys.argv[1]=='--worker':print(json.dumps(worker(sys.argv[2],sys.argv[3],int(sys.argv[4])),sort_keys=True,default=str));return 0
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit('stale native engine: '+'; '.join(stale))
 env={**os.environ,'PYTHONPATH':f"{ROOT/'runners/dsl/python'}:{ROOT}"};rows=[]
 for rep in range(3):
  backend_order=BACKENDS if rep%2==0 else tuple(reversed(BACKENDS))
  mode_order=MODES if rep%2==0 else tuple(reversed(MODES))
  for mode in mode_order:
   for backend in backend_order:
    p=subprocess.run([sys.executable,str(RUNNER),'--worker',backend,mode,str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,check=True)
    rows.append(json.loads(p.stdout.strip().splitlines()[-1]))
 lock=json.loads(LOCK.read_text());source_lock=all(sha(ROOT/p)==h for p,h in lock['sources'].items())
 from substrate_rs import _native
 binary=Path(_native.__file__).resolve();binary_lock=sha(binary)==lock['native_binary']['sha256']
 gates={'12_unique_fresh_processes':len(rows)==12 and len({r['pid'] for r in rows})==12,'source_binary_lock':source_lock and binary_lock and all(r['sources_stable'] for r in rows),'shape_oracle':all(r['valid_results']==FANOUT and r['candidate']=='dedup_identity_fix' for r in rows),'primary_isolation':all(r['primary_unchanged'] for r in rows),'mode_signature_parity':all(len({signature(x) for r in rows if (r['backend'],r['mode'])==(b,m) for x in r['results']})==1 for b in BACKENDS for m in MODES),'cross_backend_semantic_parity':all(len({signature(x) for r in rows if r['mode']==m for x in r['results']})==1 for m in MODES),'cpu_and_phases_valid':all(r['sum_thread_cpu_ms']>=0 and all(float(x['phase_timings_ms'][k])>=0 for x in r['results'] for k in ('branch_snapshot_and_setup','candidate_rule_patch','model_after_prediction')) for r in rows),'profile_totals_close_to_profiled_thread_cpu':all(abs(sum(x['profiled_cpu_ms'] for x in r['results'])-sum(x['thread_cpu_ms'] for x in r['results'] if x['profiled']))<=max(1.0,sum(x['thread_cpu_ms'] for x in r['results'] if x['profiled'])*.05) for r in rows),'python_and_c_profile_sites_present':all(any(x['profiled'] and x['python_self_cpu_ms']>0 and x['c_call_self_cpu_ms']>0 and bool(x['top_profile_sites']) for x in r['results']) for r in rows if r['mode']=='sequential'),'profile_scope_matches_mode':all(sum(x['profiled'] for x in r['results'])==(FANOUT if r['mode']=='sequential' else 0) for r in rows)}
 summaries=[]
 for b in BACKENDS:
  for m in MODES:
   rs=[r for r in rows if (r['backend'],r['mode'])==(b,m)];phase_names=('branch_snapshot_and_setup','candidate_rule_patch','model_after_prediction')
   phases={k:statistics.median(float(x['phase_timings_ms'][k]) for r in rs for x in r['results']) for k in phase_names}
   phases['prediction_internal.bounded_forward_look']=statistics.median(float(x['phase_timings_ms']['prediction_internal']['bounded_forward_look']) for r in rs for x in r['results'])
   py_ms=statistics.median(r['python_self_cpu_ms'] for r in rs);c_ms=statistics.median(r['c_call_self_cpu_ms'] for r in rs);cpu_ms=statistics.median(r['sum_thread_cpu_ms'] for r in rs)
   sites={}
   for r in rs:
    for site in r['top_profile_sites']:
     key=(site['kind'],site['filename'],str(site['line']),site['name']);sites[key]=sites.get(key,0.0)+site['self_cpu_ms']
   top=[{'kind':k[0],'filename':k[1],'line':k[2],'name':k[3],'self_cpu_ms_sum':v} for k,v in sorted(sites.items(),key=lambda kv:kv[1],reverse=True)[:20]]
   summaries.append({'backend':b,'mode':m,'median_wave_wall_ms':statistics.median(r['wave_wall_ms'] for r in rs),'median_sum_thread_cpu_ms':cpu_ms,'median_cpu_overlap_factor':statistics.median(r['cpu_overlap_factor'] for r in rs),'median_python_self_cpu_ms':py_ms if m=='sequential' else None,'median_c_call_self_cpu_ms':c_ms if m=='sequential' else None,'median_python_cpu_fraction':py_ms/max(1e-9,py_ms+c_ms) if m=='sequential' else None,'median_c_call_cpu_fraction':c_ms/max(1e-9,py_ms+c_ms) if m=='sequential' else None,'top_profile_sites':top,'median_phase_wall_ms':phases})
 capture={'schema':'ThoughtexperimentShapeDecodingPythonNativeProfileV3','captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':host_info(),'engine_fingerprint':rust_source_fingerprint(str(ROOT)),'native_binary':{'path':str(binary),'sha256':sha(binary)},'lock_sha256':sha(LOCK),'source_hashes':rows[0]['source_hashes_before'],'protocol':{'size':SIZE,'fanout':FANOUT,'backends':list(BACKENDS),'modes':list(MODES),'repeats_per_cell':3,'warmups':0},'rows':rows,'summaries':summaries,'gates':gates}
 RAW.parent.mkdir(parents=True,exist_ok=True);RAW.write_text(json.dumps(capture,indent=2,sort_keys=True)+'\n');print(json.dumps({'gates':gates,'summaries':summaries,'host':capture['host'],'raw':str(RAW)},indent=2,sort_keys=True));return 0 if all(gates.values()) else 1
if __name__=='__main__':raise SystemExit(main())
