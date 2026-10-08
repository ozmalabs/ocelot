#!/usr/bin/env python3
"""Measure sequential/concurrent scoped rehearsal on shape-axis correction."""
from __future__ import annotations
import hashlib,json,os,platform,subprocess,sys,threading,time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
RUNNER=Path(__file__).resolve();LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_shape_decoding_parallel_wave_v1_lock_20261001.json';RAW=ROOT/'evaluation/reports/thoughtexperiment_shape_decoding_parallel_wave_v1_raw_20261001.json'
BACKENDS=('native_full_copy_scoped','native_shared_graph_pages_scoped');FANOUTS=(1,2,4,8);MODES=('sequential','concurrent');SIZE=100000
SOURCES=('docs/research/engine_substrate/THOUGHTEXPERIMENT_SHAPE_DECODING_PARALLEL_WAVE_V1_PREREG_20261001.md','evaluation/substrate_capability/thoughtexperiment_shape_decoding_parallel_wave_v1.py','evaluation/substrate_capability/thoughtexperiment_self_correction_copy_comparison_v1.py','domains/self_correction.py','domains/collapse_model.py','domains/imagination.py','domains/reflective_faculty.py','substrate/boot_core.py','seeds/shape_decode_loop.json','runners/dsl/python/substrate_rs/__init__.py','runners/dsl/src/cow_paged_vec.rs','runners/dsl/src/graph.rs','runners/dsl/src/grammar.rs','runners/dsl/src/checker.rs','runners/dsl/src/term.rs','runners/dsl/src/substrate.rs','runners/dsl/src/py.rs','runners/dsl/src/persist.rs','domains/engine_provenance.py')
def sha(path):return 'sha256:'+hashlib.sha256(Path(path).read_bytes()).hexdigest()
def host_info():
 try:quota=Path('/sys/fs/cgroup/cpu.max').read_text().strip()
 except OSError:quota=None
 return {'platform':platform.platform(),'logical_cpus':os.cpu_count(),'cgroup_cpu_max':quota}
def smaps():
 out={}
 for line in Path('/proc/self/smaps_rollup').read_text().splitlines():
  k,sep,v=line.partition(':')
  if sep and k in {'Rss','Pss','Private_Clean','Private_Dirty','Shared_Clean','Shared_Dirty','Swap'}:out[k]=int(v.strip().split()[0])*1024
 return out
def worker(backend,fanout,mode,rep):
 from evaluation.substrate_capability.thoughtexperiment_self_correction_copy_comparison_v1 import make_fixture
 from domains.collapse_model import predict_collapse
 from domains.self_correction import imagine_and_check_convergence
 before={p:sha(ROOT/p) for p in SOURCES};sub,native,correct,_wrong,observations=make_fixture(SIZE)
 if correct.get('label')!='dedup_identity_fix':raise RuntimeError('shape correction fixture mismatch')
 model_before=predict_collapse(sub,horizon=3,imagine_steps=2,focus_hops=1,snapshot_backend=backend,record_trace=False)
 revision=native.experiment_graph_rule_revision();counts=(native.node_count(),native.edge_count());rules=json.dumps(native.export_rules(),sort_keys=True,default=str)
 gc_collect=__import__('gc').collect;gc_collect();baseline=smaps();samples=[baseline];stop=threading.Event()
 def sample():
  while not stop.wait(.01):
   try:samples.append(smaps())
   except (OSError,ValueError):pass
 monitor=threading.Thread(target=sample,daemon=True);monitor.start();start=time.perf_counter_ns()
 def rehearse(_):
  result=imagine_and_check_convergence(sub,correct,model_before=model_before,horizon=3,imagine_steps=2,experiment_focus_nodes=observations,focus_hops=1,snapshot_backend=backend,_prediction_snapshot_backend=backend,record_trace=False)
  return {'converges':bool(result['converges']),'inert':bool(result['inert']),'applied_targets':sorted(result['applied']),'residual_before':float(result['model_before'].residual),'residual_after':float(result['model_after'].residual),'frontier_growth_after':float(result['model_after'].frontier_growth_rate),'steps_run':int(result['model_after'].imagine_steps_run),'n_conclusions':int(result['imagined'].n_conclusions),'conclusions':result['imagined'].conclusions,'derived_only':result['imagined'].derived_only}
 if mode=='concurrent':
  with ThreadPoolExecutor(max_workers=fanout) as pool:results=list(pool.map(rehearse,range(fanout)))
 else:results=[rehearse(i) for i in range(fanout)]
 elapsed=(time.perf_counter_ns()-start)/1e6;samples.append(smaps());stop.set();monitor.join();after=smaps();peak={k:max(x.get(k,0) for x in samples) for k in baseline}
 unchanged=(native.experiment_graph_rule_revision()==revision and (native.node_count(),native.edge_count())==counts and json.dumps(native.export_rules(),sort_keys=True,default=str)==rules)
 after_hash={p:sha(ROOT/p) for p in SOURCES}
 return {'pid':os.getpid(),'backend':backend,'fanout':fanout,'mode':mode,'replicate':rep,'size':SIZE,'candidate':correct['label'],'wall_ms':elapsed,'experiments_per_second':fanout/(elapsed/1000),'samples':len(samples),'valid_results':sum(r['converges'] and not r['inert'] and 'sd_mint_quantum' in r['applied_targets'] for r in results),'results':results,'primary_unchanged':unchanged,'baseline_bytes':baseline,'peak_bytes':peak,'peak_delta_bytes':{k:peak[k]-baseline[k] for k in baseline},'after_bytes':after,'source_hashes_before':before,'source_hashes_after':after_hash,'sources_stable':before==after_hash}
def signature(row):
 fields=('converges','inert','applied_targets','residual_before','residual_after','frontier_growth_after','steps_run','n_conclusions','conclusions','derived_only')
 return json.dumps({k:row[k] for k in fields},sort_keys=True,default=str)
def main():
 if len(sys.argv)==6 and sys.argv[1]=='--worker':print(json.dumps(worker(sys.argv[2],int(sys.argv[3]),sys.argv[4],int(sys.argv[5])),sort_keys=True,default=str));return 0
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit('stale native engine: '+'; '.join(stale))
 env={**os.environ,'PYTHONPATH':f"{ROOT/'runners/dsl/python'}:{ROOT}"};rows=[]
 jobs=[(b,f,m,r) for r in range(3) for f in FANOUTS for b in (BACKENDS if r%2==0 else tuple(reversed(BACKENDS))) for m in (MODES if (r+f)%2==0 else tuple(reversed(MODES)))]
 for b,f,m,r in jobs:
  p=subprocess.run([sys.executable,str(RUNNER),'--worker',b,str(f),m,str(r)],cwd=ROOT,env=env,text=True,capture_output=True,check=True)
  rows.append(json.loads(p.stdout.strip().splitlines()[-1]))
 lock=json.loads(LOCK.read_text());source_lock=all(sha(ROOT/p)==h for p,h in lock['sources'].items())
 from substrate_rs import _native
 binary=Path(_native.__file__).resolve();binary_lock=sha(binary)==lock['native_binary']['sha256']
 groups={(b,f,m):[r for r in rows if (r['backend'],r['fanout'],r['mode'])==(b,f,m)] for b in BACKENDS for f in FANOUTS for m in MODES}
 signatures={(b,f):{signature(result) for m in MODES for row in rows if row['backend']==b and row['fanout']==f for result in row['results']} for b in BACKENDS for f in FANOUTS}
 parity={(f):{signature(result) for b in BACKENDS for m in MODES for row in rows if row['fanout']==f for result in row['results']} for f in FANOUTS}
 gates={'48_unique_fresh_processes':len(rows)==48 and len({r['pid'] for r in rows})==48,'source_binary_lock':source_lock and binary_lock and all(r['sources_stable'] for r in rows),'all_positive_shape_oracles':all(r['valid_results']==r['fanout'] for r in rows),'primary_isolation':all(r['primary_unchanged'] for r in rows),'backend_mode_semantic_parity':all(len(signatures[(b,f)])==1 for b in BACKENDS for f in FANOUTS),'cross_backend_semantic_parity':all(len(parity[f])==1 for f in FANOUTS)}
 summaries=[]
 for b in BACKENDS:
  for f in FANOUTS:
   row={'backend':b,'fanout':f}
   for m in MODES:
    rs=groups[(b,f,m)];row[m]={'median_wall_ms':sorted(x['wall_ms'] for x in rs)[1],'median_experiments_per_second':sorted(x['experiments_per_second'] for x in rs)[1],'median_peak_delta_pss_mib':sorted(x['peak_delta_bytes']['Pss']/1048576 for x in rs)[1],'median_peak_delta_rss_mib':sorted(x['peak_delta_bytes']['Rss']/1048576 for x in rs)[1],'median_samples':sorted(x['samples'] for x in rs)[1]}
   row['concurrent_speedup_vs_sequential']=row['sequential']['median_wall_ms']/row['concurrent']['median_wall_ms'];summaries.append(row)
 capture={'schema':'ThoughtexperimentShapeDecodingParallelWaveV1','captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':host_info(),'engine_fingerprint':rust_source_fingerprint(str(ROOT)),'native_binary':{'path':str(binary),'sha256':sha(binary)},'lock_sha256':sha(LOCK),'protocol':{'size':SIZE,'backends':list(BACKENDS),'fanouts':list(FANOUTS),'modes':list(MODES),'repeats_per_cell':3,'warmups':0,'sampler_ms':10},'source_hashes':rows[0]['source_hashes_before'],'rows':rows,'summaries':summaries,'gates':gates}
 RAW.parent.mkdir(parents=True,exist_ok=True);RAW.write_text(json.dumps(capture,indent=2,sort_keys=True)+'\n');print(json.dumps({'gates':gates,'summaries':summaries,'host':capture['host'],'raw':str(RAW)},indent=2,sort_keys=True));return 0 if all(gates.values()) else 1
if __name__=='__main__':raise SystemExit(main())
