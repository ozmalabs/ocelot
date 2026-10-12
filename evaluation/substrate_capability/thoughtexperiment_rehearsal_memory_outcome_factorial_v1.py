#!/usr/bin/env python3
"""Measure active rehearsal memory for matched positive and negative candidates."""
from __future__ import annotations
import hashlib,json,os,platform,subprocess,sys,threading,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
RUNNER=Path(__file__).resolve();V1=ROOT/'evaluation/substrate_capability/thoughtexperiment_active_rehearsal_memory_v1.py'
HELPER=ROOT/'evaluation/substrate_capability/thoughtexperiment_self_correction_copy_comparison_v1.py'
RAW=ROOT/'evaluation/reports/thoughtexperiment_rehearsal_memory_outcome_factorial_v1_raw_20261001.json'
RESULT=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_REHEARSAL_MEMORY_OUTCOME_FACTORIAL_V1_RESULTS_20261001.md'
BACKENDS=('native_full_copy_scoped','native_shared_graph_pages_scoped');ARMS=('correct','wrong');SIZES=(100000,200000)
SOURCES=('docs/research/engine_substrate/THOUGHTEXPERIMENT_REHEARSAL_MEMORY_OUTCOME_FACTORIAL_V1_PREREG_20261001.md','evaluation/substrate_capability/thoughtexperiment_rehearsal_memory_outcome_factorial_v1.py','evaluation/substrate_capability/thoughtexperiment_active_rehearsal_memory_v1.py','evaluation/substrate_capability/thoughtexperiment_self_correction_copy_comparison_v1.py','domains/self_correction.py','domains/collapse_model.py','domains/imagination.py','domains/reflective_faculty.py','substrate/boot_core.py','seeds/shape_decode_loop.json','runners/dsl/python/substrate_rs/__init__.py','runners/dsl/src/cow_paged_vec.rs','runners/dsl/src/graph.rs','runners/dsl/src/grammar.rs','runners/dsl/src/checker.rs','runners/dsl/src/term.rs','runners/dsl/src/substrate.rs','runners/dsl/src/py.rs','runners/dsl/src/persist.rs')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def smaps():
 out={}
 for line in Path('/proc/self/smaps_rollup').read_text().splitlines():
  k,sep,v=line.partition(':')
  if sep and k in {'Rss','Pss','Pss_Anon','Pss_File','Pss_Shmem','Private_Clean','Private_Dirty','Shared_Clean','Shared_Dirty','Swap'}:out[k]=int(v.strip().split()[0])*1024
 return out
def input_signatures(sub,obs,size):
 noise=hashlib.sha256()
 for node in sub.nodes('ThoughtexperimentNoise'):
  attrs=sub.node(node)['attrs'];noise.update(json.dumps(attrs,sort_keys=True,separators=(',',':')).encode());noise.update(b'\n')
 nodes=sorted(((int(sub.node(n)['attrs']['ordinal']),n) for n in sub.nodes('ThoughtexperimentNoise')),key=lambda x:x[0])
 chain_ok=len(nodes)==size and [i for i,_ in nodes]==list(range(size))
 if chain_ok:
  for i,(_ordinal,node) in enumerate(nodes):
   if list(sub.neighbours(node,'te_noise_next'))!=([nodes[i+1][1]] if i+1<size else []):chain_ok=False;break
 obs_hash=hashlib.sha256(json.dumps([sub.node(n)['attrs'] for n in obs],sort_keys=True,separators=(',',':')).encode()).hexdigest()
 return noise.hexdigest(),chain_ok,obs_hash
def expected_noise(size):
 h=hashlib.sha256()
 for i in range(size):h.update((json.dumps({'ordinal':i,'partition':i%32,'payload':'x'*24},sort_keys=True,separators=(',',':'))+'\n').encode())
 return h.hexdigest()
def worker(size,arm,backend,rep):
 from evaluation.substrate_capability.thoughtexperiment_self_correction_copy_comparison_v1 import make_fixture
 from domains.self_correction import imagine_and_check_convergence
 before={p:sha(ROOT/p) for p in SOURCES};sub,native,positive,negative,obs=make_fixture(size);candidate=positive if arm=='correct' else negative
 if positive['label']!='dedup_identity_fix' or negative is positive:raise RuntimeError('candidate fixture mismatch')
 rules_before=json.dumps(native.export_rules(),sort_keys=True,default=str);baseline=smaps();samples=[baseline];stop=threading.Event()
 def sample_loop():
  while not stop.wait(.01):
   try:samples.append(smaps())
   except (OSError,ValueError):pass
 monitor=threading.Thread(target=sample_loop,daemon=True);monitor.start();start=time.perf_counter_ns()
 result=imagine_and_check_convergence(sub,candidate,horizon=3,imagine_steps=2,experiment_focus_nodes=obs,focus_hops=1,snapshot_backend=backend)
 duration=(time.perf_counter_ns()-start)/1e6;samples.append(smaps());stop.set();monitor.join();after=smaps()
 rules_ok=rules_before==json.dumps(native.export_rules(),sort_keys=True,default=str)
 noise_hash,noise_chain_ok,obs_hash=input_signatures(sub,obs,size)
 peaks={k:max(s.get(k,0) for s in samples) for k in baseline}
 out={'pid':os.getpid(),'size':size,'candidate_arm':arm,'candidate_label':candidate['label'],'backend':backend,'replicate':rep,'sample_interval_ms':10,'sample_count':len(samples),'duration_instrumented_ms':duration,'converges':bool(result['converges']),'inert':bool(result['inert']),'applied':result['applied'],'residual_before':float(result['model_before'].residual),'residual_after':float(result['model_after'].residual),'frontier_growth_before':float(result['model_before'].frontier_growth_rate),'frontier_growth_after':float(result['model_after'].frontier_growth_rate),'steps_run':result['model_after'].imagine_steps_run,'n_conclusions':result['imagined'].n_conclusions,'conclusions':result['imagined'].conclusions,'derived_only':result['imagined'].derived_only,'rules_unchanged':rules_ok,'noise_nodes_unchanged':noise_hash==expected_noise(size),'noise_chain_unchanged':noise_chain_ok,'observations_unchanged':obs_hash==hashlib.sha256(json.dumps([{'signature':[[f'zzzimag{i}','X']],'key':[f'zzzimag{i}'],'status':'pending'} for i in range(3)],sort_keys=True,separators=(',',':')).encode()).hexdigest(),'baseline_bytes':baseline,'peak_bytes':peaks,'peak_delta_bytes':{k:peaks[k]-baseline[k] for k in baseline},'after_bytes':after,'source_hashes_before':before,'source_hashes_after':{p:sha(ROOT/p) for p in SOURCES}}
 out['sources_stable']=out['source_hashes_before']==out['source_hashes_after'];return out
def signature(row):
 fields=('converges','inert','residual_before','residual_after','frontier_growth_before','frontier_growth_after','steps_run','n_conclusions','conclusions','derived_only')
 return json.dumps({k:row[k] for k in fields},sort_keys=True,default=str)
def main():
 if len(sys.argv)==6 and sys.argv[1]=='--worker':print(json.dumps(worker(int(sys.argv[2]),sys.argv[3],sys.argv[4],int(sys.argv[5])),sort_keys=True,separators=(',',':'),default=str));return 0
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit('stale native engine: '+'; '.join(stale))
 env={**os.environ,'PYTHONPATH':f"{ROOT/'runners/dsl/python'}:{ROOT}"};jobs=[]
 for size in SIZES:
  for arm in ARMS:
   order=list(BACKENDS)
   for rep in range(3):
    if rep%2:order=list(reversed(BACKENDS))
    for backend in order:jobs.append((size,arm,backend,rep))
 rows=[]
 for args in jobs:
  p=subprocess.run([sys.executable,str(RUNNER),'--worker',str(args[0]),args[1],args[2],str(args[3])],cwd=ROOT,env=env,text=True,capture_output=True,check=True)
  rows.append(json.loads(p.stdout.strip().splitlines()[-1]))
 groups={(s,a,b):[r for r in rows if r['size']==s and r['candidate_arm']==a and r['backend']==b] for s in SIZES for a in ARMS for b in BACKENDS}
 gates={'eight_cells_24_fresh_processes':len({r['pid'] for r in rows})==len(rows)==24,'stable_sources':all(r['sources_stable'] for r in rows),'correct_convergence':all(r['converges'] and not r['inert'] for r in rows if r['candidate_arm']=='correct'),'negative_nonconvergence':all(not r['converges'] and not r['inert'] for r in rows if r['candidate_arm']=='wrong'),'task_inputs_and_rules_preserved':all(r['rules_unchanged'] and r['noise_nodes_unchanged'] and r['noise_chain_unchanged'] and r['observations_unchanged'] for r in rows),'backend_semantic_parity':all({signature(r) for r in groups[(s,a,BACKENDS[0])]}=={signature(r) for r in groups[(s,a,BACKENDS[1])]} and len({signature(r) for r in groups[(s,a,BACKENDS[0])]+groups[(s,a,BACKENDS[1])]})==1 for s in SIZES for a in ARMS)}
 summaries=[]
 for size in SIZES:
  for arm in ARMS:
   for backend in BACKENDS:
    rr=groups[(size,arm,backend)];keys=('Rss','Pss','Private_Dirty','Private_Clean','Shared_Clean','Shared_Dirty')
    summaries.append({'size':size,'candidate_arm':arm,'backend':backend,'repeats':len(rr),'median_baseline_bytes':{k:sorted(r['baseline_bytes'][k] for r in rr)[1] for k in keys},'median_peak_bytes':{k:sorted(r['peak_bytes'][k] for r in rr)[1] for k in keys},'median_peak_delta_bytes':{k:sorted(r['peak_delta_bytes'][k] for r in rr)[1] for k in keys},'median_instrumented_ms':sorted(r['duration_instrumented_ms'] for r in rr)[1]})
 from substrate_rs import _native
 binary=Path(_native.__file__).resolve()
 capture={'schema':'ThoughtexperimentRehearsalMemoryOutcomeFactorialV1','captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'engine_fingerprint':rust_source_fingerprint(str(ROOT)),'native_binary':{'path':str(binary),'sha256':'sha256:'+sha(binary)},'runner':{'path':str(RUNNER.relative_to(ROOT)),'sha256':'sha256:'+sha(RUNNER)},'source_hashes':rows[0]['source_hashes_before'],'protocol':{'sizes':list(SIZES),'candidate_arms':list(ARMS),'backends':list(BACKENDS),'repeats_per_cell':3,'warmups':0,'sample_interval_ms':10,'task':'positive and first nonmatching sd_mint_quantum candidates; horizon=3; two imagination steps; three-observation one-hop focus','memory':'Linux current smaps_rollup baseline and sampled peak during active rehearsal'},'rows':rows,'summaries':summaries,'gates':gates}
 RAW.write_text(json.dumps(capture,indent=2,sort_keys=True)+'\n')
 lines=['# Thoughtexperiment rehearsal memory outcome factorial v1 — results','',f"**Result:** {sum(gates.values())}/{len(gates)} preregistered gates pass across 24 fresh processes.",'','Both arms run the established self-correction operation on matched high-node-count graphs. The positive candidate converges; the first nonmatching candidate does not. Memory sampling is current PSS/RSS every 10 ms during branch prediction and residual readout; timings remain instrumented and descriptive.','','| Nodes | Candidate | Backend | Baseline PSS | Peak PSS | Peak ΔPSS | Peak ΔPrivate Dirty | Converges |','|---:|---|---|---:|---:|---:|---:|---:|']
 for s in summaries:
  arm_label='dedup_identity_fix' if s['candidate_arm']=='correct' else 'first nonmatching default'
  rows_g=groups[(s['size'],s['candidate_arm'],s['backend'])]
  lines.append(f"| {s['size']:,} | `{arm_label}` | `{s['backend']}` | {s['median_baseline_bytes']['Pss']/1048576:.1f} MiB | {s['median_peak_bytes']['Pss']/1048576:.1f} MiB | {s['median_peak_delta_bytes']['Pss']/1048576:.2f} MiB | {s['median_peak_delta_bytes']['Private_Dirty']/1048576:.2f} MiB | {sum(r['converges'] for r in rows_g)}/3 |")
 lines += ['', 'This is a controlled comparison within one synthetic shape-decoding correction family. The negative arm is one candidate, not a distribution of failed experiments. The sampler can miss brief peaks; no timing claim is made. See the preceding positive-only [active rehearsal memory panel](THOUGHTEXPERIMENT_ACTIVE_REHEARSAL_MEMORY_V1_RESULTS_20261001.md) for the validated input/rule preservation amendment and retained initial diagnostic.', '', '## Artifacts', '', '- [Preregistration](THOUGHTEXPERIMENT_REHEARSAL_MEMORY_OUTCOME_FACTORIAL_V1_PREREG_20261001.md)', '- [Pre-run lock](../../../evaluation/substrate_capability/thoughtexperiment_rehearsal_memory_outcome_factorial_v1_lock_20261001.json)', '- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_rehearsal_memory_outcome_factorial_v1.py)', '- [Raw capture](../../../evaluation/reports/thoughtexperiment_rehearsal_memory_outcome_factorial_v1_raw_20261001.json)']
 RESULT.write_text('\n'.join(lines)+'\n');print(json.dumps({'gates':gates,'summaries':summaries},indent=2,sort_keys=True));return 0 if all(gates.values()) else 1
if __name__=='__main__':raise SystemExit(main())
