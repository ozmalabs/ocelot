#!/usr/bin/env python3
"""Measure supported ternary exact MAP through certified width eight."""
from __future__ import annotations
import hashlib,importlib.util,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT)]
RUNNER=Path(__file__).resolve()
PROTOCOL=ROOT/'docs/research/engine_substrate/CAN_TERNARY_HIGH_WIDTH_INFERENCE_V1_PREREG_20261002.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_can_ternary_high_width_inference_v1.py'
DOMAIN_RUNNER=ROOT/'evaluation/substrate_capability/can_edge_matched_domain_cost_v1.py'
DOMAIN_PROTOCOL=ROOT/'docs/research/engine_substrate/CAN_EDGE_MATCHED_DOMAIN_COST_V1_PREREG_20261002.md'
DOMAIN_LOCK=ROOT/'evaluation/substrate_capability/can_edge_matched_domain_cost_v1_lock_20261002.json'
DOMAIN_CAPTURE=ROOT/'evaluation/reports/can_edge_matched_domain_cost_v1_20261002.json'
DOMAIN_ANALYSIS=ROOT/'evaluation/reports/can_edge_matched_domain_cost_v1_20261002_analysis.json'
BASELINE_RUNNER=ROOT/'evaluation/substrate_capability/can_edge_matched_inference_cost_v1_4.py'
BASELINE_LOCK=ROOT/'evaluation/substrate_capability/can_edge_matched_inference_cost_v1_4_lock_20261002.json'
BASELINE_CAPTURE=ROOT/'evaluation/reports/can_edge_matched_inference_cost_v1_4_20261002.json'
BASELINE_ANALYSIS=ROOT/'evaluation/reports/can_edge_matched_inference_cost_v1_4_20261002_analysis.json'
LOCK=ROOT/'evaluation/substrate_capability/can_ternary_high_width_inference_v1_lock_20261002.json'
OUT=ROOT/'evaluation/reports/can_ternary_high_width_inference_v1_20261002.json'
WIDTHS=(6,7,8);FAMILIES=('grid','sparse_partial_qtree');REPLICATES=3;N=120;TOL=1e-8
def digest(path):
 raw=path.read_bytes();return {'path':path.relative_to(ROOT).as_posix(),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def source_lock():
 from substrate_rs import _native
 domain=load(DOMAIN_RUNNER,'ternary_domain_base')
 return {'runner':digest(RUNNER),'protocol':digest(PROTOCOL),'analyzer':digest(ANALYZER),
  'domain_runner':digest(DOMAIN_RUNNER),'domain_protocol':digest(DOMAIN_PROTOCOL),'domain_lock':digest(DOMAIN_LOCK),
  'domain_capture':digest(DOMAIN_CAPTURE),'domain_analysis':digest(DOMAIN_ANALYSIS),
  'domain_inputs':domain.source_lock(),
  'baseline_runner':digest(BASELINE_RUNNER),'baseline_lock':digest(BASELINE_LOCK),
  'baseline_capture':digest(BASELINE_CAPTURE),'baseline_analysis':digest(BASELINE_ANALYSIS),
  'baseline_sources':load(BASELINE_RUNNER,'ternary_binary_baseline').source_lock(),
  'loaded_native_binary':digest(Path(_native.__file__).resolve()),
  'widths':list(WIDTHS),'families':list(FAMILIES),'replicates':REPLICATES,'nodes':N,'tolerance':TOL}
def worker(q,family,rep):
 before=source_lock();module=load(DOMAIN_RUNNER,'ternary_domain_worker');row=module.worker(q,family,rep,'3state');after=source_lock()
 row.update({'source_lock_start':before,'source_lock_end':after});return row
def main():
 args=sys.argv[1:]
 if args[:1]==['--worker']:
  print(json.dumps(worker(int(args[1]),args[2],int(args[3])),sort_keys=True,separators=(',',':')));return 0
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite lock/capture')
  LOCK.write_text(json.dumps({'schema':'CanTernaryHighWidthInferenceV1Lock','sources':source_lock()},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if args!=['--run']:raise SystemExit('usage: --lock, --run, or --worker Q FAMILY REP')
 lock=json.loads(LOCK.read_text())
 if source_lock()!=lock['sources']:raise SystemExit('source/input drift from lock')
 from domains.engine_provenance import build_is_stale
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit('native engine stale: '+'; '.join(stale))
 env={**os.environ,'PYTHONPATH':f"{ROOT/'runners/dsl/python'}:{ROOT}:{os.environ.get('PYTHONPATH','')}"};rows=[];failures=[]
 for q in WIDTHS:
  for rep in range(REPLICATES):
   for family in FAMILIES:
    cell={'width':q,'replicate':rep,'family':family}
    try:
     p=subprocess.run([sys.executable,str(RUNNER),'--worker',str(q),family,str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=900)
     if p.returncode:raise RuntimeError(p.stderr[-3000:])
     row=json.loads(p.stdout.strip());rows.append(row)
     print(f"q={q} {family} rep={rep} JTcert={row['timing_ns']['jt_certificate_wall']/1e6:.2f}ms traced={row['traced_peak_bytes']['jt_certificate']}",flush=True)
    except Exception as e:
     failures.append({**cell,'error':type(e).__name__+': '+str(e)});print(f"FAILED {cell}: {e}",file=sys.stderr,flush=True)
 post=source_lock();baseline=json.loads(BASELINE_CAPTURE.read_text());base_runs={(x['width'],x['family'],x['replicate']):x for x in baseline['runs']}
 checks={'worker_count':len(rows)==18,'failure_free':not failures,'fresh_worker_pids':len({r['worker_pid'] for r in rows})==len(rows),
  'complete_cells':all(sum((r['width'],r['family'])==(q,f) for r in rows)==REPLICATES for q in WIDTHS for f in FAMILIES),
  'fixture_match_binary_capture':all((r['width'],r['family'],r['replicate']) in base_runs and (r['seed'],r['nodes'],r['edges'])==(base_runs[(r['width'],r['family'],r['replicate'])]['seed'],base_runs[(r['width'],r['family'],r['replicate'])]['nodes'],base_runs[(r['width'],r['family'],r['replicate'])]['edges']) for r in rows),
  'node_edge_counts':all(r['nodes']==N and r['edges']==r['expected_edges'] for r in rows),
  'ternary_mode_extracted':all(r['mode']=='3state' and r['vocabulary']==[-1.0,0.0,1.0] and r['extraction_exact'] for r in rows),
  'certified_width':all(r['certificate_width']==r['width'] for r in rows),
  'oracle_parity':all(abs(r[k]-r['oracle_energy'])<TOL for r in rows for k in ('minfill_energy','certificate_energy','minfill_direct_energy','certificate_direct_energy')),
  'no_mutation':all(r['no_mutation'] for r in rows),'worker_source_locks':all(r['source_lock_start']==lock['sources']==r['source_lock_end'] for r in rows),
  'same_native_binary_as_binary_panel':lock['sources']['loaded_native_binary']['sha256']==lock['sources']['baseline_sources']['loaded_native_binary']['sha256'],
  'same_solver_sources_as_binary_panel':all(next(x for x in lock['sources']['domain_inputs']['solver_sources'] if x['path']==p)==next(x for x in lock['sources']['baseline_sources']['base_input_lock']['sources'] if x['path']==p) for p in ('domains/can_junction_tree.py','domains/graph_treewidth.py')),
  'pre_post_source_match':post==lock['sources']}
 OUT.write_text(json.dumps({'schema':'CanTernaryHighWidthInferenceV1Results','lock_sha256':hashlib.sha256(LOCK.read_bytes()).hexdigest(),
  'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),'sources':source_lock(),'post_run_sources':post,
  'configuration':{'nodes':N,'widths':WIDTHS,'families':FAMILIES,'mode':'3state','replicates':REPLICATES},
  'claim_boundary':'supported ternary exact MAP through q=8 on two synthetic graph families; binary comparisons only when source/build/fixture gates match',
  'checks':checks,'failures':failures,'runs':rows},indent=2,sort_keys=True)+'\n')
 print(json.dumps({'capture':OUT.relative_to(ROOT).as_posix(),'checks':checks,'failure_count':len(failures)},indent=2))
 if not all(checks.values()):raise SystemExit('ternary high-width gate failed')
if __name__=='__main__':main()
