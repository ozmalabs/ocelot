#!/usr/bin/env python3
"""Paired semantic parity panel for native and Python Thoughtexperiment rule patches."""
from __future__ import annotations
import copy,hashlib,json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
RUNNER=Path(__file__).resolve();LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_native_rule_patch_semantics_v1_lock_20261001.json';RAW=ROOT/'evaluation/reports/thoughtexperiment_native_rule_patch_semantics_v1_raw_20261001.json'
BACKENDS=('native_full_copy_scoped','native_shared_graph_pages_scoped');CASES=('replace_primary','remove_primary','absent_target','mixed_absent','replace_later_rule','replace_two_rules');SIZE=100000
SOURCES=('docs/research/engine_substrate/THOUGHTEXPERIMENT_NATIVE_RULE_PATCH_SEMANTICS_V1_PREREG_20261001.md','evaluation/substrate_capability/thoughtexperiment_native_rule_patch_semantics_v1.py','evaluation/substrate_capability/thoughtexperiment_shape_decoding_rule_patch_v4.py','evaluation/substrate_capability/thoughtexperiment_self_correction_copy_comparison_v1.py','domains/self_correction.py','domains/collapse_model.py','domains/imagination.py','domains/reflective_faculty.py','substrate/boot_core.py','seeds/shape_decode_loop.json','runners/dsl/python/substrate_rs/__init__.py','runners/dsl/src/py.rs','runners/dsl/src/substrate.rs','domains/engine_provenance.py')
def sha(p):return 'sha256:'+hashlib.sha256(Path(p).read_bytes()).hexdigest()
def make_cases(candidate,native):
 primary='sd_mint_quantum';later='sd_dedup_existing';rules={r['name']:r for r in native.export_rules() if r.get('active',True)}
 positive=copy.deepcopy(candidate['rules'][primary]);later_rule=copy.deepcopy(rules[later])
 return {
  'replace_primary':{'label':'replace_primary','rules':{primary:positive}},
  'remove_primary':{'label':'remove_primary','rules':{primary:None}},
  'absent_target':{'label':'absent_target','rules':{'missing_rule_for_semantics_probe':positive}},
  'mixed_absent':{'label':'mixed_absent','rules':{primary:positive,'missing_rule_for_semantics_probe':positive}},
  'replace_later_rule':{'label':'replace_later_rule','rules':{later:later_rule}},
  'replace_two_rules':{'label':'replace_two_rules','rules':{primary:positive,later:later_rule}},
 }
def signature(r):
 keys=('converges','inert','applied','model_after.residual','frontier_growth_after','steps_run','n_conclusions','conclusions','derived_only')
 return json.dumps({'converges':r['converges'],'inert':r['inert'],'applied':r['applied'],'model_after.residual':r['model_after'].residual,'frontier_growth_after':r['model_after'].frontier_growth_rate,'steps_run':r['model_after'].imagine_steps_run,'n_conclusions':r['imagined'].n_conclusions,'conclusions':r['imagined'].conclusions,'derived_only':r['imagined'].derived_only},sort_keys=True,default=str)
def worker(backend,case,rep):
 from evaluation.substrate_capability.thoughtexperiment_self_correction_copy_comparison_v1 import make_fixture
 from domains.collapse_model import predict_collapse
 from domains.self_correction import imagine_and_check_convergence
 before={p:sha(ROOT/p) for p in SOURCES};sub,native,candidate,_wrong,observations=make_fixture(SIZE)
 baseline=predict_collapse(sub,horizon=3,imagine_steps=2,focus_hops=1,snapshot_backend=backend,record_trace=False)
 cases=make_cases(candidate,native);revision=native.experiment_graph_rule_revision();counts=(native.node_count(),native.edge_count());rules=json.dumps(native.export_rules(),sort_keys=True,default=str)
 outputs=[]
 for method in (False,True):
  options={'model_before':baseline,'horizon':3,'imagine_steps':2,'experiment_focus_nodes':observations,'focus_hops':1,'snapshot_backend':backend,'record_trace':False}
  if not method:options['_native_rule_patch']=False
  result=imagine_and_check_convergence(sub,cases[case],**options)
  outputs.append({'native':method,'signature':signature(result),'applied':result['applied'],'inert':result['inert'],'converges':result['converges']})
 unchanged=native.experiment_graph_rule_revision()==revision and (native.node_count(),native.edge_count())==counts and json.dumps(native.export_rules(),sort_keys=True,default=str)==rules
 after={p:sha(ROOT/p) for p in SOURCES}
 return {'pid':os.getpid(),'backend':backend,'case':case,'replicate':rep,'outcomes':outputs,'paired_match':outputs[0]['signature']==outputs[1]['signature'],'primary_unchanged':unchanged,'sources_stable':before==after,'source_hashes_before':before}
def main():
 if len(sys.argv)==5 and sys.argv[1]=='--worker':print(json.dumps(worker(sys.argv[2],sys.argv[3],int(sys.argv[4])),sort_keys=True));return 0
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit('stale native engine: '+'; '.join(stale))
 env={**os.environ,'PYTHONPATH':f"{ROOT/'runners/dsl/python'}:{ROOT}"};rows=[]
 for rep in range(3):
  for case in CASES:
   for backend in (BACKENDS if (rep+CASES.index(case))%2==0 else tuple(reversed(BACKENDS))):
    p=subprocess.run([sys.executable,str(RUNNER),'--worker',backend,case,str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,check=True);rows.append(json.loads(p.stdout.strip().splitlines()[-1]))
 lock=json.loads(LOCK.read_text());source_lock=all(sha(ROOT/p)==h for p,h in lock['sources'].items())
 from substrate_rs import _native
 binary=Path(_native.__file__).resolve();binary_lock=sha(binary)==lock['native_binary']['sha256']
 gates={'36_unique_fresh_processes':len(rows)==36 and len({r['pid'] for r in rows})==36,'source_binary_lock':source_lock and binary_lock and all(r['sources_stable'] for r in rows),'paired_outcome_parity':all(r['paired_match'] for r in rows),'primary_isolation':all(r['primary_unchanged'] for r in rows),'expected_application':all((r['case']=='absent_target')==r['outcomes'][0]['inert'] and (r['case']=='absent_target')==r['outcomes'][1]['inert'] for r in rows),'all_cases_all_backends':len({(r['case'],r['backend']) for r in rows})==len(CASES)*len(BACKENDS)}
 capture={'schema':'ThoughtexperimentNativeRulePatchSemanticsV1','captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'engine_fingerprint':rust_source_fingerprint(str(ROOT)),'native_binary':{'path':str(binary),'sha256':sha(binary)},'lock_sha256':sha(LOCK),'protocol':{'size':SIZE,'cases':list(CASES),'backends':list(BACKENDS),'repeats_per_case_backend':3},'rows':rows,'gates':gates}
 RAW.parent.mkdir(parents=True,exist_ok=True);RAW.write_text(json.dumps(capture,indent=2,sort_keys=True)+'\n');print(json.dumps({'gates':gates,'raw':str(RAW)},indent=2));return 0 if all(gates.values()) else 1
if __name__=='__main__':raise SystemExit(main())
