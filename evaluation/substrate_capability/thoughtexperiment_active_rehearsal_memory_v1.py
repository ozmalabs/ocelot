#!/usr/bin/env python3
"""Sample full-process memory during an actual corrective thoughtexperiment."""
from __future__ import annotations
import hashlib,json,os,platform,random,re,subprocess,sys,threading,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python")]
RUNNER=Path(__file__).resolve();HELPER=ROOT/"evaluation/substrate_capability/thoughtexperiment_self_correction_copy_comparison_v1.py"
LOCK=ROOT/"evaluation/substrate_capability/thoughtexperiment_active_rehearsal_memory_v1_lock_20261001.json"
RAW=ROOT/"evaluation/reports/thoughtexperiment_active_rehearsal_memory_v1_raw_20261001.json"
RESULT=ROOT/"docs/research/engine_substrate/THOUGHTEXPERIMENT_ACTIVE_REHEARSAL_MEMORY_V1_RESULTS_20261001.md"
SOURCES=("docs/research/engine_substrate/THOUGHTEXPERIMENT_ACTIVE_REHEARSAL_MEMORY_V1_PREREG_20261001.md","docs/research/engine_substrate/THOUGHTEXPERIMENT_ACTIVE_REHEARSAL_MEMORY_V1_AMENDMENT_20261001.md","evaluation/substrate_capability/thoughtexperiment_active_rehearsal_memory_v1.py","evaluation/substrate_capability/thoughtexperiment_self_correction_copy_comparison_v1.py","domains/self_correction.py","domains/collapse_model.py","domains/imagination.py","domains/reflective_faculty.py","substrate/boot_core.py","seeds/shape_decode_loop.json","runners/dsl/python/substrate_rs/__init__.py","runners/dsl/src/cow_paged_vec.rs","runners/dsl/src/graph.rs","runners/dsl/src/grammar.rs","runners/dsl/src/checker.rs","runners/dsl/src/term.rs","runners/dsl/src/substrate.rs","runners/dsl/src/py.rs","runners/dsl/src/persist.rs")
BACKENDS=("native_full_copy_scoped","native_shared_graph_pages_scoped")
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def smaps():
 out={}
 for line in Path('/proc/self/smaps_rollup').read_text().splitlines():
  k,sep,v=line.partition(':')
  if sep and k in {'Rss','Pss','Pss_Anon','Pss_File','Pss_Shmem','Private_Clean','Private_Dirty','Shared_Clean','Shared_Dirty','Swap'}:out[k]=int(v.strip().split()[0])*1024
 return out
def noise_digest(sub):
 h=hashlib.sha256()
 for node in sub.nodes('ThoughtexperimentNoise'):
  attrs=sub.node(node)['attrs'];h.update(json.dumps(attrs,sort_keys=True,separators=(',',':')).encode());h.update(b'\n')
 return h.hexdigest()
def obs_digest(sub,ids):
 return hashlib.sha256(json.dumps([sub.node(n)['attrs'] for n in ids],sort_keys=True,separators=(',',':')).encode()).hexdigest()
def noise_edges_unchanged(sub,size):
 nodes=sorted(((int(sub.node(n)['attrs']['ordinal']),n) for n in sub.nodes('ThoughtexperimentNoise')),key=lambda x:x[0])
 if len(nodes)!=size or [ordinal for ordinal,_ in nodes]!=list(range(size)):return False
 for i,(_ordinal,node) in enumerate(nodes):
  actual=list(sub.neighbours(node,'te_noise_next'))
  expected=[nodes[i+1][1]] if i+1<size else []
  if actual!=expected:return False
 return True
def worker(size,backend,rep):
 from evaluation.substrate_capability.thoughtexperiment_self_correction_copy_comparison_v1 import make_fixture
 from domains.self_correction import imagine_and_check_convergence
 source_before={p:sha(ROOT/p) for p in SOURCES};sub,native,correct,wrong,observations=make_fixture(size)
 if correct['label']!='dedup_identity_fix':raise RuntimeError('expected positive correction candidate')
 counts=(native.node_count(),native.edge_count());rules_before=json.dumps(native.export_rules(),sort_keys=True,default=str)
 expected_noise_hash=hashlib.sha256()
 for i in range(size):expected_noise_hash.update((json.dumps({'ordinal':i,'partition':i%32,'payload':'x'*24},sort_keys=True,separators=(',',':'))+'\n').encode())
 expected_noise=expected_noise_hash.hexdigest()
 expected_obs=obs_digest(sub,observations)
 baseline=smaps();samples=[baseline];stop=threading.Event()
 def sample_loop():
  while not stop.wait(.01):
   try:samples.append(smaps())
   except (OSError,ValueError):pass
 monitor=threading.Thread(target=sample_loop,name='smaps-sampler',daemon=True);monitor.start()
 start=time.perf_counter_ns()
 result=imagine_and_check_convergence(sub,correct,horizon=3,imagine_steps=2,experiment_focus_nodes=observations,focus_hops=1,snapshot_backend=backend)
 duration=(time.perf_counter_ns()-start)/1e6
 samples.append(smaps());stop.set();monitor.join()
 after=smaps();rules_after=json.dumps(native.export_rules(),sort_keys=True,default=str)
 actual_noise=noise_digest(sub);actual_obs=obs_digest(sub,observations);noise_edges_ok=noise_edges_unchanged(sub,size)
 peaks={k:max(s.get(k,0) for s in samples) for k in baseline}
 signatures={k:peaks[k]-baseline[k] for k in peaks}
 out={'pid':os.getpid(),'size':size,'backend':backend,'replicate':rep,'sample_interval_ms':10,'sample_count':len(samples),'duration_ms':duration,'converges':bool(result['converges']),'inert':bool(result['inert']),'applied':result['applied'],'residual_before':float(result['model_before'].residual),'residual_after':float(result['model_after'].residual),'frontier_growth_before':float(result['model_before'].frontier_growth_rate),'frontier_growth_after':float(result['model_after'].frontier_growth_rate),'steps_run':result['model_after'].imagine_steps_run,'n_conclusions':result['imagined'].n_conclusions,'conclusions':result['imagined'].conclusions,'derived_only':result['imagined'].derived_only,'base_counts_before':list(counts),'base_counts_after':[native.node_count(),native.edge_count()],'rules_unchanged':rules_before==rules_after,'noise_graph_unchanged':expected_noise==actual_noise and noise_edges_ok,'observations_unchanged':expected_obs==actual_obs,'baseline_bytes':baseline,'peak_bytes':peaks,'peak_delta_bytes':signatures,'after_bytes':after,'source_before':source_before,'source_after':{p:sha(ROOT/p) for p in SOURCES}}
 out['source_stable']=out['source_before']==out['source_after'];return out
def main():
 if len(sys.argv)==5 and sys.argv[1]=='--worker':print(json.dumps(worker(int(sys.argv[2]),sys.argv[3],int(sys.argv[4])),sort_keys=True,separators=(',',':'),default=str));return 0
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit('stale native engine: '+'; '.join(stale))
 env={**os.environ,'PYTHONPATH':f"{ROOT/'runners/dsl/python'}:{ROOT}"};jobs=[]
 for size in (100000,200000):
  order=list(BACKENDS)
  for rep in range(3):
   if rep%2:order=list(reversed(BACKENDS))
   for backend in order:jobs.append((size,backend,rep))
 rows=[]
 for size,backend,rep in jobs:
  p=subprocess.run([sys.executable,str(RUNNER),'--worker',str(size),backend,str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,check=True)
  rows.append(json.loads(p.stdout.strip().splitlines()[-1]))
 groups={(n,b):[r for r in rows if r['size']==n and r['backend']==b] for n in (100000,200000) for b in BACKENDS}
 def signature(r):return json.dumps({k:r[k] for k in ('converges','inert','residual_before','residual_after','frontier_growth_before','frontier_growth_after','steps_run','n_conclusions','conclusions','derived_only')},sort_keys=True,default=str)
 gates={
  'six_fresh_process_cells':len({r['pid'] for r in rows})==len(rows)==12,
  'source_hashes_stable':all(r['source_stable'] for r in rows),
  'positive_oracle_all_runs':all(r['converges'] and not r['inert'] for r in rows),
  'primary_rules_and_task_inputs_preserved':all(r['rules_unchanged'] and r['noise_graph_unchanged'] and r['observations_unchanged'] for r in rows),
  'backend_semantic_parity':all(
   {signature(r) for r in groups[(n,BACKENDS[0])]}=={signature(r) for r in groups[(n,BACKENDS[1])]} and
   len({signature(r) for r in groups[(n,BACKENDS[0])]+groups[(n,BACKENDS[1])]})==1
   for n in (100000,200000))}
 summaries=[]
 for size in (100000,200000):
  for backend in BACKENDS:
   rr=groups[(size,backend)];keys=('Rss','Pss','Private_Dirty','Private_Clean','Shared_Dirty','Shared_Clean')
   summaries.append({'size':size,'backend':backend,'repeats':len(rr),'median_baseline_bytes':{k:sorted(r['baseline_bytes'][k] for r in rr)[1] for k in keys},'median_peak_bytes':{k:sorted(r['peak_bytes'][k] for r in rr)[1] for k in keys},'median_peak_delta_bytes':{k:sorted(r['peak_delta_bytes'][k] for r in rr)[1] for k in keys},'all_converge':all(r['converges'] for r in rr),'all_input_and_rule_checks_pass':all(r['rules_unchanged'] and r['noise_graph_unchanged'] and r['observations_unchanged'] for r in rr)})
 from substrate_rs import _native as native_module
 binary=Path(native_module.__file__).resolve()
 capture={'schema':'ThoughtexperimentActiveRehearsalMemoryV1','captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'engine_fingerprint':rust_source_fingerprint(str(ROOT)),'native_binary':{'path':str(binary),'sha256':'sha256:'+sha(binary)},'runner':{'path':str(RUNNER.relative_to(ROOT)),'sha256':'sha256:'+sha(RUNNER)},'sources':rows[0]['source_before'],'protocol':{'sizes':[100000,200000],'backends':list(BACKENDS),'repeats_per_cell':3,'warmups':0,'sampler_interval_ms':10,'task':'positive sd_mint_quantum dedup_identity_fix; horizon=3; two imagination steps; three-observation one-hop focus','metrics':'current Linux smaps_rollup baseline, sampled peak during operation, and peak-minus-baseline delta','worker_count':len(rows)},'rows':rows,'summaries':summaries,'gates':gates}
 RAW.write_text(json.dumps(capture,indent=2,sort_keys=True)+'\n')
 lines=['# Active thoughtexperiment rehearsal memory v1 — results','',f"**Result:** {sum(gates.values())}/{len(gates)} amended confirmatory gates pass across the preregistered panel.",'','This panel samples current full-process RSS/PSS while the positive self-correction rehearsal actually predicts and reads out its residual. The graph fixture, loaded rules, candidate, and observations are retained. The primary may gain the normal durable correction trace; the gates verify that the noise graph, source observations, and rewrite rules remain unchanged. Timing is instrumented and descriptive because the 10 ms sampler perturbs scheduling.','','| Added nodes | Backend | Baseline PSS | Peak PSS | Peak ΔPSS | Peak ΔPrivate Dirty | Runs converged |','|---:|---|---:|---:|---:|---:|---:|']
 for s in summaries:lines.append(f"| {s['size']:,} | `{s['backend']}` | {s['median_baseline_bytes']['Pss']/1048576:.1f} MiB | {s['median_peak_bytes']['Pss']/1048576:.1f} MiB | {s['median_peak_delta_bytes']['Pss']/1048576:.2f} MiB | {s['median_peak_delta_bytes']['Private_Dirty']/1048576:.2f} MiB | {sum(r['converges'] for r in groups[(s['size'],s['backend'])])}/3 |")
 lines += ["", "Interpret these as one synthetic positive correction family on one Linux host. The active operation uses branch prediction and residual readout, but does not cover the negative correction arm, parallel candidate batches, kernel peak RSS, or unrelated graph families. The sampler may miss peaks shorter than its interval; no timing superiority is inferred. The initial attempt's extra primary-edge-count gate was invalid because the production path intentionally writes durable trace nodes/edges; its raw capture is retained as a [harness diagnostic](../../../evaluation/reports/thoughtexperiment_active_rehearsal_memory_v1_initial_diagnostic_raw_20261001.json). The amended gate checks task-input and rule preservation.", "", "## Artifacts", "", "- [Preregistration](THOUGHTEXPERIMENT_ACTIVE_REHEARSAL_MEMORY_V1_PREREG_20261001.md)", "- [Amendment](THOUGHTEXPERIMENT_ACTIVE_REHEARSAL_MEMORY_V1_AMENDMENT_20261001.md)", "- [Pre-run lock](../../../evaluation/substrate_capability/thoughtexperiment_active_rehearsal_memory_v1_lock_20261001.json)", "- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_active_rehearsal_memory_v1.py)", "- [Initial diagnostic](../../../evaluation/reports/thoughtexperiment_active_rehearsal_memory_v1_initial_diagnostic_raw_20261001.json)", "- [Confirmatory raw capture](../../../evaluation/reports/thoughtexperiment_active_rehearsal_memory_v1_raw_20261001.json)"]
 RESULT.write_text('\n'.join(lines)+'\n');print(json.dumps({'gates':gates,'summaries':summaries},indent=2,sort_keys=True));return 0 if all(gates.values()) else 1
if __name__=='__main__':raise SystemExit(main())
