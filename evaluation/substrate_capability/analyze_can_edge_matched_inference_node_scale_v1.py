#!/usr/bin/env python3
"""Independent integrity checks and scaling summaries for node-scale inference."""
from __future__ import annotations
import hashlib,importlib.util,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RUNNER=ROOT/'evaluation/substrate_capability/can_edge_matched_inference_node_scale_v1.py'
LOCK=ROOT/'evaluation/substrate_capability/can_edge_matched_inference_node_scale_v1_lock_20261002.json'
CAP=ROOT/'evaluation/reports/can_edge_matched_inference_node_scale_v1_20261002.json'
BASE_ANALYSIS=ROOT/'evaluation/reports/can_edge_matched_inference_cost_v1_4_20261002_analysis.json'
OUT=ROOT/'evaluation/reports/can_edge_matched_inference_node_scale_v1_20261002_analysis.json'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load_runner():
 spec=importlib.util.spec_from_file_location('inference_node_scale_analysis',RUNNER)
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def analyze():
 r=load_runner();cap=json.loads(CAP.read_text());lock=json.loads(LOCK.read_text());base=json.loads(BASE_ANALYSIS.read_text());rows=cap.get('runs',[]);checks=[]
 def check(name,ok):checks.append((name,bool(ok)))
 check('schema',cap.get('schema')=='CanEdgeMatchedInferenceNodeScaleV1Results')
 check('capture_lock',cap.get('lock_sha256')==sha(LOCK))
 check('input_source_lock',cap.get('sources')==lock.get('sources')==r.source_lock())
 check('postrun_source_lock',cap.get('post_run_sources')==lock.get('sources'))
 check('base_v1_4_analysis',base.get('passed')==base.get('total')==40)
 check('worker_count',len(rows)==36)
 check('capture_gates',all(cap.get('checks',{}).values()))
 check('unique_fresh_workers',len({x.get('worker_pid') for x in rows})==36)
 for n in r.SIZES:
  for q in r.WIDTHS:
   for fam in r.FAMILIES:
    cell=[x for x in rows if (x['node_count_requested'],x['width'],x['family'])==(n,q,fam)]
    check(f'{n}_q{q}_{fam}_replicates',len(cell)==r.REPLICATES)
    check(f'{n}_q{q}_{fam}_oracle',all(abs(x[k]-x['oracle_energy'])<1e-8 for x in cell for k in ('minfill_energy','certificate_energy','minfill_direct_energy','certificate_direct_energy')))
    check(f'{n}_q{q}_{fam}_certificate',all(x['certificate_width']==q for x in cell))
    check(f'{n}_q{q}_{fam}_isolation',all(x['no_mutation'] for x in cell))
 def median(cell,key):return statistics.median(x['timing_ns'][key] for x in cell)/1e6
 summaries=[]
 for q in r.WIDTHS:
  for fam in r.FAMILIES:
   baseline=[x for x in rows if (x['node_count_requested'],x['width'],x['family'])==(r.SIZES[0],q,fam)]
   for n in r.SIZES:
    cell=[x for x in rows if (x['node_count_requested'],x['width'],x['family'])==(n,q,fam)]
    timings=('runtime_extraction','minfill_order','oracle','jt_minfill_wall','jt_certificate_wall')
    summaries.append({'nodes':n,'width':q,'family':fam,'replicates':len(cell),
     'median_ms':{k:median(cell,k) for k in timings},
     'range_ms':{k:[min(x['timing_ns'][k] for x in cell)/1e6,max(x['timing_ns'][k] for x in cell)/1e6] for k in timings},
     'median_certificate_traced_peak_bytes':int(statistics.median(x['traced_peak_bytes']['jt_certificate'] for x in cell)),
     'median_certificate_message_entries':int(statistics.median(x['decomposition_profiles']['certificate']['message_entries'] for x in cell)),
     'median_process_peak_rss_kib':int(statistics.median(x['process_peak_rss_kib'] for x in cell)),
     'ratio_to_n126':{'jt_minfill_wall':median(cell,'jt_minfill_wall')/median(baseline,'jt_minfill_wall'),
                      'jt_certificate_wall':median(cell,'jt_certificate_wall')/median(baseline,'jt_certificate_wall'),
                      'traced_certificate_peak':statistics.median(x['traced_peak_bytes']['jt_certificate'] for x in cell)/statistics.median(x['traced_peak_bytes']['jt_certificate'] for x in baseline)}})
 result={'schema':'CanEdgeMatchedInferenceNodeScaleV1Analysis','passed':sum(ok for _,ok in checks),'total':len(checks),
  'checks':[{'name':name,'passed':ok} for name,ok in checks],'worker_count':len(rows),'cells':summaries,
  'interpretation':'Fixed-width node-count scaling on two synthetic edge-matched binary pairwise graph families at one host; no natural graph distribution or general scaling claim.'}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 print(f"{result['passed']}/{result['total']} checks; {OUT.relative_to(ROOT)}")
 return 0 if all(ok for _,ok in checks) else 1
if __name__=='__main__':raise SystemExit(analyze())
