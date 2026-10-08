#!/usr/bin/env python3
"""Attribute the measured shape-axis thoughtexperiment cost to phases."""
from __future__ import annotations
import hashlib,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
RUNNER=Path(__file__).resolve();LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_shape_decoding_phase_profile_v1_lock_20261001.json';RAW=ROOT/'evaluation/reports/thoughtexperiment_shape_decoding_phase_profile_v1_raw_20261001.json'
BACKENDS=('native_full_copy_scoped','native_shared_graph_pages_scoped')
SOURCES=('docs/research/engine_substrate/THOUGHTEXPERIMENT_SHAPE_DECODING_PHASE_PROFILE_V1_PREREG_20261001.md','evaluation/substrate_capability/thoughtexperiment_shape_decoding_phase_profile_v1.py','evaluation/substrate_capability/thoughtexperiment_self_correction_copy_comparison_v1.py','domains/self_correction.py','domains/collapse_model.py','domains/imagination.py','domains/reflective_faculty.py','substrate/boot_core.py','seeds/shape_decode_loop.json','runners/dsl/python/substrate_rs/__init__.py','runners/dsl/src/cow_paged_vec.rs','runners/dsl/src/graph.rs','runners/dsl/src/grammar.rs','runners/dsl/src/checker.rs','runners/dsl/src/term.rs','runners/dsl/src/substrate.rs','runners/dsl/src/py.rs','runners/dsl/src/persist.rs','domains/engine_provenance.py')
def sha(path):return 'sha256:'+hashlib.sha256(Path(path).read_bytes()).hexdigest()
def worker(backend,rep):
 from evaluation.substrate_capability.thoughtexperiment_self_correction_copy_comparison_v1 import make_fixture
 from domains.collapse_model import predict_collapse
 from domains.self_correction import imagine_and_check_convergence
 before={p:sha(ROOT/p) for p in SOURCES};sub,native,candidate,_wrong,obs=make_fixture(100000)
 baseline=predict_collapse(sub,horizon=3,imagine_steps=2,focus_hops=1,snapshot_backend=backend,record_trace=False)
 revision=native.experiment_graph_rule_revision();counts=(native.node_count(),native.edge_count());rules=json.dumps(native.export_rules(),sort_keys=True,default=str)
 start=time.perf_counter_ns();result=imagine_and_check_convergence(sub,candidate,model_before=baseline,horizon=3,imagine_steps=2,experiment_focus_nodes=obs,focus_hops=1,snapshot_backend=backend,_prediction_snapshot_backend=backend,_measure_phases=True,record_trace=False);wall=(time.perf_counter_ns()-start)/1e6
 after={p:sha(ROOT/p) for p in SOURCES};phases=result['phase_timings_ms'];outer=('branch_snapshot_and_setup','candidate_rule_patch','model_after_prediction')
 return {'pid':os.getpid(),'backend':backend,'replicate':rep,'candidate':candidate['label'],'converges':bool(result['converges']),'inert':bool(result['inert']),'applied_targets':sorted(result['applied']),'wall_ms':wall,'phase_timings_ms':phases,'outer_phase_sum_ms':sum(float(phases[k]) for k in outer),'primary_unchanged':native.experiment_graph_rule_revision()==revision and (native.node_count(),native.edge_count())==counts and json.dumps(native.export_rules(),sort_keys=True,default=str)==rules,'source_hashes_before':before,'source_hashes_after':after,'sources_stable':before==after}
def main():
 if len(sys.argv)==4 and sys.argv[1]=='--worker':print(json.dumps(worker(sys.argv[2],int(sys.argv[3])),sort_keys=True,default=str));return 0
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit('stale native engine: '+'; '.join(stale))
 env={**os.environ,'PYTHONPATH':f"{ROOT/'runners/dsl/python'}:{ROOT}"};rows=[]
 for rep in range(3):
  order=BACKENDS if rep%2==0 else tuple(reversed(BACKENDS))
  for backend in order:
   p=subprocess.run([sys.executable,str(RUNNER),'--worker',backend,str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,check=True)
   rows.append(json.loads(p.stdout.strip().splitlines()[-1]))
 lock=json.loads(LOCK.read_text());source_lock=all(sha(ROOT/p)==h for p,h in lock['sources'].items())
 from substrate_rs import _native
 binary=Path(_native.__file__).resolve();binary_lock=sha(binary)==lock['native_binary']['sha256']
 gates={'six_fresh_processes':len(rows)==6 and len({r['pid'] for r in rows})==6,'source_binary_lock':source_lock and binary_lock and all(r['sources_stable'] for r in rows),'positive_shape_oracle':all(r['candidate']=='dedup_identity_fix' and r['converges'] and not r['inert'] and 'sd_mint_quantum' in r['applied_targets'] for r in rows),'primary_isolation':all(r['primary_unchanged'] for r in rows),'phase_fields_present_nonnegative':all(all(float(r['phase_timings_ms'][k])>=0 for k in ('branch_snapshot_and_setup','candidate_rule_patch','model_after_prediction')) and all(float(v)>=0 for v in r['phase_timings_ms']['initial_branch_internal'].values()) and all(float(v)>=0 for v in r['phase_timings_ms']['prediction_internal'].values()) for r in rows),'outer_phases_within_wall_tolerance':all(r['outer_phase_sum_ms']<=r['wall_ms']*1.25 for r in rows)}
 summaries=[]
 for backend in BACKENDS:
  rs=[r for r in rows if r['backend']==backend];keys=('branch_snapshot_and_setup','candidate_rule_patch','model_after_prediction')
  med={k:sorted(float(r['phase_timings_ms'][k]) for r in rs)[1] for k in keys}
  for section in ('initial_branch_internal','prediction_internal'):
   for name in sorted(set.intersection(*(set(r['phase_timings_ms'][section]) for r in rs))):med[f'{section}.{name}']=sorted(float(r['phase_timings_ms'][section][name]) for r in rs)[1]
  summaries.append({'backend':backend,'median_wall_ms':sorted(r['wall_ms'] for r in rs)[1],'median_phase_ms':med})
 capture={'schema':'ThoughtexperimentShapeDecodingPhaseProfileV1','captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'engine_fingerprint':rust_source_fingerprint(str(ROOT)),'native_binary':{'path':str(binary),'sha256':sha(binary)},'lock_sha256':sha(LOCK),'source_hashes':rows[0]['source_hashes_before'],'protocol':{'noise_nodes':100000,'candidate':'sd_mint_quantum/dedup_identity_fix','backends':list(BACKENDS),'repeats_per_backend':3,'warmups':0},'rows':rows,'summaries':summaries,'gates':gates}
 RAW.parent.mkdir(parents=True,exist_ok=True);RAW.write_text(json.dumps(capture,indent=2,sort_keys=True)+'\n');print(json.dumps({'gates':gates,'summaries':summaries,'raw':str(RAW)},indent=2,sort_keys=True));return 0 if all(gates.values()) else 1
if __name__=='__main__':raise SystemExit(main())
