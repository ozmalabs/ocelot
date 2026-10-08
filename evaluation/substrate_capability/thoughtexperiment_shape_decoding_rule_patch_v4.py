#!/usr/bin/env python3
"""Measure per-thread CPU and timed phases in shape-decoding rehearsal waves."""
from __future__ import annotations
import hashlib,json,os,platform,statistics,subprocess,sys,threading,time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
RUNNER=Path(__file__).resolve();LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_shape_decoding_rule_patch_v4_lock_20261001.json';RAW=ROOT/'evaluation/reports/thoughtexperiment_shape_decoding_rule_patch_v4_raw_20261001.json'
BACKENDS=('native_full_copy_scoped','native_shared_graph_pages_scoped');MODES=('sequential','concurrent');FANOUT=8;SIZE=100000;PATCHES=('python_export','native_by_name')
SOURCES=('docs/research/engine_substrate/THOUGHTEXPERIMENT_SHAPE_DECODING_RULE_PATCH_V4_PREREG_20261001.md','docs/research/engine_substrate/THOUGHTEXPERIMENT_SHAPE_DECODING_RULE_PATCH_V4_AMENDMENT_20261001.md','docs/research/engine_substrate/THOUGHTEXPERIMENT_SHAPE_DECODING_CONCURRENCY_PROFILE_V3_RESULTS_20261001.md','evaluation/substrate_capability/thoughtexperiment_shape_decoding_rule_patch_v4.py','evaluation/substrate_capability/thoughtexperiment_self_correction_copy_comparison_v1.py','domains/self_correction.py','domains/collapse_model.py','domains/imagination.py','domains/reflective_faculty.py','substrate/boot_core.py','seeds/shape_decode_loop.json','runners/dsl/python/substrate_rs/__init__.py','runners/dsl/src/cow_paged_vec.rs','runners/dsl/src/graph.rs','runners/dsl/src/grammar.rs','runners/dsl/src/checker.rs','runners/dsl/src/term.rs','runners/dsl/src/substrate.rs','runners/dsl/src/py.rs','runners/dsl/src/persist.rs','domains/engine_provenance.py')
def sha(path):return 'sha256:'+hashlib.sha256(Path(path).read_bytes()).hexdigest()
def host_info():
 try:quota=Path('/sys/fs/cgroup/cpu.max').read_text().strip()
 except OSError:quota=None
 status=Path('/proc/self/status').read_text();allowed=next((x.split(':',1)[1].strip() for x in status.splitlines() if x.startswith('Cpus_allowed_list:')),None)
 return {'platform':platform.platform(),'logical_cpus':os.cpu_count(),'cpus_allowed_list':allowed,'cgroup_cpu_max':quota}
def worker(backend,mode,rep,patch_method):
 from evaluation.substrate_capability.thoughtexperiment_self_correction_copy_comparison_v1 import make_fixture
 from domains.collapse_model import predict_collapse
 from domains.self_correction import imagine_and_check_convergence
 before={p:sha(ROOT/p) for p in SOURCES};sub,native,candidate,_wrong,observations=make_fixture(SIZE)
 baseline=predict_collapse(sub,horizon=3,imagine_steps=2,focus_hops=1,snapshot_backend=backend,record_trace=False)
 revision=native.experiment_graph_rule_revision();counts=(native.node_count(),native.edge_count());rules=json.dumps(native.export_rules(),sort_keys=True,default=str)
 barrier=threading.Barrier(FANOUT) if mode=='concurrent' else None
 def rehearse(_):
  if barrier:barrier.wait()
  wall0=time.perf_counter_ns();cpu0=time.thread_time_ns()
  result=imagine_and_check_convergence(sub,candidate,model_before=baseline,horizon=3,imagine_steps=2,experiment_focus_nodes=observations,focus_hops=1,snapshot_backend=backend,_prediction_snapshot_backend=backend,_measure_phases=True,_native_rule_patch=(patch_method=='native_by_name'),record_trace=False)
  cpu=(time.thread_time_ns()-cpu0)/1e6;wall=(time.perf_counter_ns()-wall0)/1e6;phases=result['phase_timings_ms']
  return {'wall_ms':wall,'thread_cpu_ms':cpu,'converges':bool(result['converges']),'inert':bool(result['inert']),'applied_targets':sorted(result['applied']),'residual_before':float(result['model_before'].residual),'residual_after':float(result['model_after'].residual),'frontier_growth_after':float(result['model_after'].frontier_growth_rate),'steps_run':int(result['model_after'].imagine_steps_run),'n_conclusions':int(result['imagined'].n_conclusions),'conclusions':result['imagined'].conclusions,'derived_only':result['imagined'].derived_only,'phase_timings_ms':phases}
 start=time.perf_counter_ns()
 if mode=='concurrent':
  with ThreadPoolExecutor(max_workers=FANOUT) as pool:results=list(pool.map(rehearse,range(FANOUT)))
 else:results=[rehearse(i) for i in range(FANOUT)]
 wave_ms=(time.perf_counter_ns()-start)/1e6
 primary_unchanged=native.experiment_graph_rule_revision()==revision and (native.node_count(),native.edge_count())==counts and json.dumps(native.export_rules(),sort_keys=True,default=str)==rules
 after={p:sha(ROOT/p) for p in SOURCES}
 return {'pid':os.getpid(),'backend':backend,'mode':mode,'patch_method':patch_method,'replicate':rep,'fanout':FANOUT,'size':SIZE,'candidate':candidate['label'],'wave_wall_ms':wave_ms,'sum_thread_cpu_ms':sum(r['thread_cpu_ms'] for r in results),'cpu_overlap_factor':sum(r['thread_cpu_ms'] for r in results)/wave_ms,'valid_results':sum(r['converges'] and not r['inert'] and 'sd_mint_quantum' in r['applied_targets'] for r in results),'results':results,'primary_unchanged':primary_unchanged,'source_hashes_before':before,'source_hashes_after':after,'sources_stable':before==after}
def signature(r):
 keys=('converges','inert','applied_targets','residual_before','residual_after','frontier_growth_after','steps_run','n_conclusions','conclusions','derived_only')
 return json.dumps({k:r[k] for k in keys},sort_keys=True,default=str)
def main():
 if len(sys.argv)==6 and sys.argv[1]=='--worker':print(json.dumps(worker(sys.argv[2],sys.argv[3],int(sys.argv[4]),sys.argv[5]),sort_keys=True,default=str));return 0
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit('stale native engine: '+'; '.join(stale))
 env={**os.environ,'PYTHONPATH':f"{ROOT/'runners/dsl/python'}:{ROOT}"};rows=[]
 for rep in range(3):
  backend_order=BACKENDS if rep%2==0 else tuple(reversed(BACKENDS))
  mode_order=MODES if rep%2==0 else tuple(reversed(MODES))
  for patch_method in PATCHES:
   for mode in mode_order:
    for backend in backend_order:
     p=subprocess.run([sys.executable,str(RUNNER),'--worker',backend,mode,str(rep),patch_method],cwd=ROOT,env=env,text=True,capture_output=True,check=True)
     rows.append(json.loads(p.stdout.strip().splitlines()[-1]))
 lock=json.loads(LOCK.read_text());source_lock=all(sha(ROOT/p)==h for p,h in lock['sources'].items())
 from substrate_rs import _native
 binary=Path(_native.__file__).resolve();binary_lock=sha(binary)==lock['native_binary']['sha256']
 gates={'24_unique_fresh_processes':len(rows)==24 and len({r['pid'] for r in rows})==24,'source_binary_lock':source_lock and binary_lock and all(r['sources_stable'] for r in rows),'shape_oracle':all(r['valid_results']==FANOUT and r['candidate']=='dedup_identity_fix' for r in rows),'primary_isolation':all(r['primary_unchanged'] for r in rows),'mode_signature_parity':all(len({signature(x) for r in rows if (r['backend'],r['mode'],r['patch_method'])==(b,m,q) for x in r['results']})==1 for b in BACKENDS for m in MODES for q in PATCHES),'cross_backend_semantic_parity':all(len({signature(x) for r in rows if r['mode']==m and r['patch_method']==q for x in r['results']})==1 for m in MODES for q in PATCHES),'patch_method_semantic_parity':all(len({signature(x) for r in rows if r['patch_method']==q for x in r['results']})==1 for q in PATCHES),'cpu_and_phases_valid':all(r['sum_thread_cpu_ms']>=0 and all(float(x['phase_timings_ms'][k])>=0 for x in r['results'] for k in ('branch_snapshot_and_setup','candidate_rule_patch','model_after_prediction')) for r in rows)}
 summaries=[]
 for q in PATCHES:
  for b in BACKENDS:
   for m in MODES:
    rs=[r for r in rows if (r['backend'],r['mode'],r['patch_method'])==(b,m,q)];phase_names=('branch_snapshot_and_setup','candidate_rule_patch','model_after_prediction')
    phases={k:statistics.median(float(x['phase_timings_ms'][k]) for r in rs for x in r['results']) for k in phase_names}
    phases['prediction_internal.bounded_forward_look']=statistics.median(float(x['phase_timings_ms']['prediction_internal']['bounded_forward_look']) for r in rs for x in r['results'])
    summaries.append({'patch_method':q,'backend':b,'mode':m,'median_wave_wall_ms':statistics.median(r['wave_wall_ms'] for r in rs),'median_sum_thread_cpu_ms':statistics.median(r['sum_thread_cpu_ms'] for r in rs),'median_cpu_overlap_factor':statistics.median(r['cpu_overlap_factor'] for r in rs),'median_phase_wall_ms':phases})
 capture={'schema':'ThoughtexperimentShapeDecodingRulePatchV4','captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':host_info(),'engine_fingerprint':rust_source_fingerprint(str(ROOT)),'native_binary':{'path':str(binary),'sha256':sha(binary)},'lock_sha256':sha(LOCK),'source_hashes':rows[0]['source_hashes_before'],'protocol':{'size':SIZE,'fanout':FANOUT,'backends':list(BACKENDS),'modes':list(MODES),'patch_methods':list(PATCHES),'repeats_per_cell':3,'warmups':0},'rows':rows,'summaries':summaries,'gates':gates}
 RAW.parent.mkdir(parents=True,exist_ok=True);RAW.write_text(json.dumps(capture,indent=2,sort_keys=True)+'\n');print(json.dumps({'gates':gates,'summaries':summaries,'host':capture['host'],'raw':str(RAW)},indent=2,sort_keys=True));return 0 if all(gates.values()) else 1
if __name__=='__main__':raise SystemExit(main())
