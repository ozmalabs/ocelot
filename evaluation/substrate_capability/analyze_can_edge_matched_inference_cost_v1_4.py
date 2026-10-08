#!/usr/bin/env python3
"""Check higher-width inference replay and summarize costs against v1.3."""
import hashlib,importlib.util,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RUNNER=ROOT/'evaluation/substrate_capability/can_edge_matched_inference_cost_v1_4.py'
LOCK=ROOT/'evaluation/substrate_capability/can_edge_matched_inference_cost_v1_4_lock_20261002.json'
CAP=ROOT/'evaluation/reports/can_edge_matched_inference_cost_v1_4_20261002.json'
BASE=ROOT/'evaluation/reports/can_edge_matched_inference_cost_v1_3_20261002.json'
OUT=ROOT/'evaluation/reports/can_edge_matched_inference_cost_v1_4_20261002_analysis.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load_runner():
 spec=importlib.util.spec_from_file_location('inference_v1_4',RUNNER);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def analyze():
 cap=json.loads(CAP.read_text());lock=json.loads(LOCK.read_text());base=json.loads(BASE.read_text());r=load_runner();checks=[]
 checks.extend([('schema',cap.get('schema')=='CanEdgeMatchedInferenceCostV1_4Results'),
   ('capture_lock',cap.get('lock_sha256')==sha(LOCK)),('input_sources',cap.get('sources')==lock['sources']==r.source_lock()),
   ('postrun_sources',cap.get('post_run_sources')==lock['sources']),('worker_count',len(cap.get('runs',[]))==48),
   ('capture_gates',all(cap.get('checks',{}).values())),('historical_python_compatibility',r.historical_python_compatibility()),
   ('historical_v1_3_capture_lock',base['input_lock']==base['post_run_input_lock'])])
 rows=cap.get('runs',[])
 for q in r.WIDTHS:
  for fam in r.FAMILIES:
   cell=[x for x in rows if x['width']==q and x['family']==fam]
   checks.append((f'{fam}_q{q}_replicates',len(cell)==r.REPLICATES))
   checks.append((f'{fam}_q{q}_oracle',all(abs(x['minfill_energy']-x['oracle_energy'])<1e-8 and abs(x['certificate_energy']-x['oracle_energy'])<1e-8 and abs(x['minfill_direct_energy']-x['oracle_energy'])<1e-8 and abs(x['certificate_direct_energy']-x['oracle_energy'])<1e-8 for x in cell)))
   checks.append((f'{fam}_q{q}_width',all(x['certificate_width']==q for x in cell)))
   checks.append((f'{fam}_q{q}_unchanged',all(x['no_mutation'] for x in cell)))
 cells=[]
 def med(rows,key):return statistics.median(x['timing_ns'][key] for x in rows)/1e6
 for q in r.WIDTHS:
  for fam in r.FAMILIES:
   cell=[x for x in rows if x['width']==q and x['family']==fam]
   prev=[x for x in rows if x['width']==r.CONTROL_WIDTH and x['family']==fam]
   cells.append({'width':q,'family':fam,'replicates':len(cell),
     'minfill_width_counts':{str(w):sum(x['minfill_width']==w for x in cell) for w in sorted({x['minfill_width'] for x in cell})},
     'median_ms':{k:med(cell,k) for k in ('runtime_extraction','minfill_order','oracle','jt_minfill_wall','jt_certificate_wall')},
     'median_traced_peak_bytes':{k:int(statistics.median(x['traced_peak_bytes'][k] for x in cell)) for k in ('jt_minfill','jt_certificate')},
     'median_profile':{order:{k:int(statistics.median(x['decomposition_profiles'][order][k] for x in cell)) for k in ('message_entries','bag_assignments','estimated_inner_loop_iterations')} for order in ('minfill','certificate')},
     'ratio_to_q6_median_jt':{'minfill':med(cell,'jt_minfill_wall')/med(prev,'jt_minfill_wall'),'certificate':med(cell,'jt_certificate_wall')/med(prev,'jt_certificate_wall')}})
 result={'schema':'CanEdgeMatchedInferenceCostV1_4Analysis','passed':sum(ok for _,ok in checks),'total':len(checks),
   'checks':[{'name':name,'passed':bool(ok)} for name,ok in checks],'cells':cells,'worker_count':len(rows),
   'interpretation':'Higher-width exactness/cost on fixed-size synthetic binary pairwise families. Width and topology costs remain conditional on these fixtures and this host; comparison does not estimate the distribution of natural task widths.'}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(f"{result['passed']}/{result['total']} checks; {OUT.relative_to(ROOT)}")
 return 0 if all(ok for _,ok in checks) else 1
if __name__=='__main__':raise SystemExit(analyze())
