#!/usr/bin/env python3
"""Independent integrity and paired cost summaries for domain-cardinality panel."""
from __future__ import annotations
import hashlib,importlib.util,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RUNNER=ROOT/'evaluation/substrate_capability/can_edge_matched_domain_cost_v1.py'
LOCK=ROOT/'evaluation/substrate_capability/can_edge_matched_domain_cost_v1_lock_20261002.json'
CAP=ROOT/'evaluation/reports/can_edge_matched_domain_cost_v1_20261002.json'
OUT=ROOT/'evaluation/reports/can_edge_matched_domain_cost_v1_20261002_analysis.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load_runner():
 spec=importlib.util.spec_from_file_location('can_domain_cost_analyzer',RUNNER)
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def analyze():
 r=load_runner();cap=json.loads(CAP.read_text());lock=json.loads(LOCK.read_text());rows=cap.get('runs',[]);checks=[]
 def check(name,ok):checks.append((name,bool(ok)))
 check('schema',cap.get('schema')=='CanEdgeMatchedDomainCostV1Results')
 check('capture_lock',cap.get('lock_sha256')==sha(LOCK))
 check('source_lock',cap.get('sources')==lock.get('sources')==r.source_lock())
 check('postrun_lock',cap.get('post_run_sources')==lock.get('sources'))
 check('worker_count',len(rows)==36)
 check('capture_gates',all(cap.get('checks',{}).values()))
 check('unique_worker_pids',len({x.get('worker_pid') for x in rows})==36)
 cells=[]
 for q in r.WIDTHS:
  for fam in r.FAMILIES:
   for mode,vocab in r.MODES.items():
    cell=[x for x in rows if (x['width'],x['family'],x['mode'])==(q,fam,mode)]
    check(f'{fam}_q{q}_{mode}_replicates',len(cell)==r.REPLICATES)
    check(f'{fam}_q{q}_{mode}_domain',all(x['vocabulary']==list(vocab) and x['extraction_exact'] for x in cell))
    check(f'{fam}_q{q}_{mode}_oracle',all(abs(x[k]-x['oracle_energy'])<r.TOL for x in cell for k in ('minfill_energy','certificate_energy','minfill_direct_energy','certificate_direct_energy')))
    check(f'{fam}_q{q}_{mode}_width_isolation',all(x['certificate_width']==q and x['no_mutation'] for x in cell))
   binary=[x for x in rows if (x['width'],x['family'],x['mode'])==(q,fam,'2state')]
   ternary=[x for x in rows if (x['width'],x['family'],x['mode'])==(q,fam,'3state')]
   med=lambda xs,k:statistics.median(x['timing_ns'][k] for x in xs)/1e6
   cells.append({'width':q,'family':fam,'replicates':len(binary),'median_ms':{
    mode:{k:med([x for x in rows if (x['width'],x['family'],x['mode'])==(q,fam,mode)],k) for k in ('minfill_order','oracle','jt_minfill_wall','jt_certificate_wall')}
    for mode in ('2state','3state')},
    'ternary_to_binary_ratio':{k:med(ternary,k)/med(binary,k) for k in ('oracle','jt_minfill_wall','jt_certificate_wall')},
    'median_certificate_traced_peak_bytes':{mode:int(statistics.median(x['traced_peak_bytes']['jt_certificate'] for x in group)) for mode,group in (('2state',binary),('3state',ternary))},
    'minfill_widths':{mode:{str(w):sum(x['minfill_width']==w for x in group) for w in sorted({x['minfill_width'] for x in group})} for mode,group in (('2state',binary),('3state',ternary))}})
 result={'schema':'CanEdgeMatchedDomainCostV1Analysis','passed':sum(ok for _,ok in checks),'total':len(checks),
  'checks':[{'name':n,'passed':ok} for n,ok in checks],'worker_count':len(rows),'cells':cells,
  'interpretation':'Paired binary versus ternary exact MAP cost at fixed N, certified width, graph, and potentials on synthetic fixtures; one host and no natural workload prevalence estimate.'}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(f"{result['passed']}/{result['total']} checks; {OUT.relative_to(ROOT)}")
 return 0 if all(ok for _,ok in checks) else 1
if __name__=='__main__':raise SystemExit(analyze())
