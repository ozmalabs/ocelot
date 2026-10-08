#!/usr/bin/env python3
"""Fixed-width node-count scaling for exact binary pairwise MAP inference."""
from __future__ import annotations
import hashlib,importlib.util,json,os,platform,subprocess,sys,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT)]
RUNNER=Path(__file__).resolve()
PROTOCOL=ROOT/'docs/research/engine_substrate/CAN_EDGE_MATCHED_INFERENCE_NODE_SCALE_V1_PREREG_20261002.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_can_edge_matched_inference_node_scale_v1.py'
BASE_RUNNER=ROOT/'evaluation/substrate_capability/can_edge_matched_inference_cost_v1_4.py'
BASE_LOCK=ROOT/'evaluation/substrate_capability/can_edge_matched_inference_cost_v1_4_lock_20261002.json'
BASE_CAPTURE=ROOT/'evaluation/reports/can_edge_matched_inference_cost_v1_4_20261002.json'
BASE_ANALYSIS=ROOT/'evaluation/reports/can_edge_matched_inference_cost_v1_4_20261002_analysis.json'
LOCK=ROOT/'evaluation/substrate_capability/can_edge_matched_inference_node_scale_v1_lock_20261002.json'
OUT=ROOT/'evaluation/reports/can_edge_matched_inference_node_scale_v1_20261002.json'
SIZES=(126,252,504); WIDTHS=(6,9); FAMILIES=('grid','sparse_partial_qtree'); REPLICATES=3

def digest(path):
 raw=path.read_bytes();return {'path':path.relative_to(ROOT).as_posix(),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def load_v14():
 spec=importlib.util.spec_from_file_location('inference_node_scale_v14',BASE_RUNNER)
 module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module);return module
def source_lock():
 from substrate_rs import _native
 return {'runner':digest(RUNNER),'protocol':digest(PROTOCOL),'analyzer':digest(ANALYZER),
  'base_runner':digest(BASE_RUNNER),'base_lock':digest(BASE_LOCK),'base_capture':digest(BASE_CAPTURE),
  'base_analysis':digest(BASE_ANALYSIS),'base_sources':load_v14().source_lock(),
  'loaded_native_binary':digest(Path(_native.__file__).resolve()),
  'sizes':list(SIZES),'widths':list(WIDTHS),'families':list(FAMILIES),'replicates':REPLICATES}
def worker(n,q,family,rep):
 base=load_v14().load_base()
 base.N=n
 base.GEN.N=n
 row=base.worker(q,family,rep)
 row.update({'node_count_requested':n,'worker_pid':os.getpid()})
 return row
def main():
 args=sys.argv[1:]
 if args[:1]==['--worker']:
  print(json.dumps(worker(int(args[1]),int(args[2]),args[3],int(args[4])),sort_keys=True,separators=(',',':')));return 0
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite lock/capture')
  LOCK.write_text(json.dumps({'schema':'CanEdgeMatchedInferenceNodeScaleV1Lock','sources':source_lock()},indent=2,sort_keys=True)+'\n')
  print(LOCK.relative_to(ROOT));return 0
 if args!=['--run']:raise SystemExit('usage: --lock, --run, or --worker N Q FAMILY REP')
 lock=json.loads(LOCK.read_text())
 if source_lock()!=lock['sources']:raise SystemExit('source/input drift from lock')
 from domains.engine_provenance import build_is_stale
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit('native engine stale: '+'; '.join(stale))
 env={**os.environ,'PYTHONPATH':f"{ROOT/'runners/dsl/python'}:{ROOT}:{os.environ.get('PYTHONPATH','')}"}
 rows=[]
 for n in SIZES:
  for q in WIDTHS:
   for rep in range(REPLICATES):
    for family in FAMILIES:
     p=subprocess.run([sys.executable,str(RUNNER),'--worker',str(n),str(q),family,str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=600)
     if p.returncode:raise RuntimeError(f'N={n} q={q} family={family} rep={rep}: {p.stderr[-3000:]}')
     row=json.loads(p.stdout.strip());rows.append(row)
     print(f"N={n} q={q} {family} rep={rep} JTcert={row['timing_ns']['jt_certificate_wall']/1e6:.2f}ms traced={row['traced_peak_bytes']['jt_certificate']}",flush=True)
 post=source_lock()
 checks={'complete_workers':len(rows)==36,'fresh_worker_pids':len({r['worker_pid'] for r in rows})==36,
  'full_cell_coverage':all(sum(r['node_count_requested']==n and r['width']==q and r['family']==f for r in rows)==REPLICATES for n in SIZES for q in WIDTHS for f in FAMILIES),
  'node_edge_counts':all(r['nodes']==r['node_count_requested'] and r['edges']==r['expected_edges'] for r in rows),
  'certificate_width_q':all(r['certificate_width']==r['width'] for r in rows),
  'exact_extraction':all(r['extraction_exact'] for r in rows),
  'oracle_and_direct_rescore':all(abs(r[k]-r['oracle_energy'])<1e-8 for r in rows for k in ('minfill_energy','certificate_energy','minfill_direct_energy','certificate_direct_energy')),
  'profile_reconciliation':all(r['decomposition_profiles']['minfill']['max_bag_size']==r['minfill_bag_size'] and r['decomposition_profiles']['certificate']['max_bag_size']==r['certificate_bag_size'] for r in rows),
  'no_mutation':all(r['no_mutation'] for r in rows),'pre_post_source_match':post==lock['sources']}
 OUT.write_text(json.dumps({'schema':'CanEdgeMatchedInferenceNodeScaleV1Results','lock_sha256':hashlib.sha256(LOCK.read_bytes()).hexdigest(),
  'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),'sources':source_lock(),'post_run_sources':post,
  'configuration':{'sizes':SIZES,'widths':WIDTHS,'families':FAMILIES,'replicates':REPLICATES},
  'claim_boundary':'fixed-width exact binary pairwise MAP cost on two synthetic edge-matched families; no natural-task size or topology prevalence estimate',
  'checks':checks,'runs':rows},indent=2,sort_keys=True)+'\n')
 print(json.dumps({'capture':OUT.relative_to(ROOT).as_posix(),'checks':checks},indent=2))
 if not all(checks.values()):raise SystemExit('node scaling gate failed')
if __name__=='__main__':main()
