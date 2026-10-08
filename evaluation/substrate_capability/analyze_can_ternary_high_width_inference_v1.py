#!/usr/bin/env python3
"""Validate ternary high-width capture and paired binary comparison."""
from __future__ import annotations
import hashlib,importlib.util,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RUNNER=ROOT/'evaluation/substrate_capability/can_ternary_high_width_inference_v1.py'
LOCK=ROOT/'evaluation/substrate_capability/can_ternary_high_width_inference_v1_lock_20261002.json'
CAP=ROOT/'evaluation/reports/can_ternary_high_width_inference_v1_20261002.json'
OUT=ROOT/'evaluation/reports/can_ternary_high_width_inference_v1_20261002_analysis.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load_runner():
 spec=importlib.util.spec_from_file_location('ternary_high_width_analyzer',RUNNER);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def analyze():
 r=load_runner();cap=json.loads(CAP.read_text());lock=json.loads(LOCK.read_text());rows=cap.get('runs',[]);binary=json.loads(r.BASELINE_CAPTURE.read_text());base={(x['width'],x['family'],x['replicate']):x for x in binary['runs']};checks=[]
 def check(n,ok):checks.append((n,bool(ok)))
 check('schema',cap.get('schema')=='CanTernaryHighWidthInferenceV1Results')
 check('capture_lock',cap.get('lock_sha256')==sha(LOCK))
 check('source_lock',cap.get('sources')==lock.get('sources')==r.source_lock())
 check('postrun_lock',cap.get('post_run_sources')==lock.get('sources'))
 check('binary_capture_source_lock',binary.get('sources')==lock['sources']['baseline_sources'])
 check('worker_count',len(rows)==18)
 check('no_recorded_failures',not cap.get('failures'))
 check('capture_gates',all(cap.get('checks',{}).values()))
 check('fresh_pids',len({x.get('worker_pid') for x in rows})==18)
 check('same_native_binary',lock['sources']['loaded_native_binary']['sha256']==lock['sources']['baseline_sources']['loaded_native_binary']['sha256'])
 check('same_solver_sources',all(next(x for x in lock['sources']['domain_inputs']['solver_sources'] if x['path']==p)==next(x for x in lock['sources']['baseline_sources']['base_input_lock']['sources'] if x['path']==p) for p in ('domains/can_junction_tree.py','domains/graph_treewidth.py')))
 check('same_generator',lock['sources']['domain_inputs']['generator']==lock['sources']['baseline_sources']['generator'])
 check('same_base_worker',lock['sources']['domain_inputs']['base_runner']==lock['sources']['baseline_sources']['base_runner'])
 check('binary_fixture_coverage',all((x['width'],x['family'],x['replicate']) in base and (x['seed'],x['nodes'],x['edges'])==(base[(x['width'],x['family'],x['replicate'])]['seed'],base[(x['width'],x['family'],x['replicate'])]['nodes'],base[(x['width'],x['family'],x['replicate'])]['edges']) for x in rows))
 check('all_ternary_oracles',all(x['mode']=='3state' and x['vocabulary']==[-1.0,0.0,1.0] and x['certificate_width']==x['width'] and x['extraction_exact'] and x['no_mutation'] and all(abs(x[k]-x['oracle_energy'])<r.TOL for k in ('minfill_energy','certificate_energy','minfill_direct_energy','certificate_direct_energy')) for x in rows))
 check('cell_coverage',all(sum((x['width'],x['family'])==(q,f) for x in rows)==r.REPLICATES for q in r.WIDTHS for f in r.FAMILIES))
 def med(xs,key):return statistics.median(x['timing_ns'][key] for x in xs)/1e6
 cells=[]
 for q in r.WIDTHS:
  for fam in r.FAMILIES:
   tern=[x for x in rows if (x['width'],x['family'])==(q,fam)];binrows=[base[(q,fam,x['replicate'])] for x in tern]
   q6=[x for x in rows if (x['width'],x['family'])==(r.WIDTHS[0],fam)]
   cells.append({'width':q,'family':fam,'replicates':len(tern),'ternary_median_ms':{k:med(tern,k) for k in ('minfill_order','oracle','jt_minfill_wall','jt_certificate_wall')},
    'binary_median_ms':{k:med(binrows,k) for k in ('minfill_order','oracle','jt_minfill_wall','jt_certificate_wall')},
    'ternary_to_binary_ratio':{k:med(tern,k)/med(binrows,k) for k in ('oracle','jt_minfill_wall','jt_certificate_wall')},
    'ternary_ratio_to_q6':{'jt_certificate_wall':med(tern,'jt_certificate_wall')/med(q6,'jt_certificate_wall')},
    'traced_peak_bytes':int(statistics.median(x['traced_peak_bytes']['jt_certificate'] for x in tern)),
    'minfill_width_counts':{str(w):sum(x['minfill_width']==w for x in tern) for w in sorted({x['minfill_width'] for x in tern})}})
 result={'schema':'CanTernaryHighWidthInferenceV1Analysis','passed':sum(ok for _,ok in checks),'total':len(checks),
  'checks':[{'name':n,'passed':ok} for n,ok in checks],'worker_count':len(rows),'cells':cells,
  'interpretation':'Supported ternary exact MAP through q=8 on two synthetic N=120 graph families. Binary ratios use only source/native/fixture-matched v1.4 rows and do not estimate natural workload prevalence.'}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(f"{result['passed']}/{result['total']} checks; {OUT.relative_to(ROOT)}")
 return 0 if all(ok for _,ok in checks) else 1
if __name__=='__main__':raise SystemExit(analyze())
