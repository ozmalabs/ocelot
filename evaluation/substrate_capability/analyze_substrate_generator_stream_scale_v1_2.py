#!/usr/bin/env python3
"""Post-capture corrected analysis for the generated-pool streaming scale capture."""
from __future__ import annotations
import hashlib,json,math,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
LOCK=ROOT/'evaluation/substrate_capability/substrate_generator_stream_scale_v1_1_lock_20261002.json'
RAW=ROOT/'evaluation/reports/substrate_generator_stream_scale_v1_1_raw_20261002.json'
OUT=ROOT/'evaluation/reports/substrate_generator_stream_scale_v1_2_analysis_20261002.json'
def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def finite(v):
 if isinstance(v,float):return math.isfinite(v)
 if isinstance(v,dict):return all(finite(x) for x in v.values())
 if isinstance(v,(list,tuple)):return all(finite(x) for x in v)
 return True
def main():
 lock=json.loads(LOCK.read_text());raw=json.loads(RAW.read_text())
 checks={k:True for k in ('source_native_lock','complete_unique_grid','batch_stream_semantic_parity',
  'heldout_coverage_parity','finite_resource_measurements','training_labels_fixed',
  'all_pool_hypotheses_fit_anchor','incomplete_stops_explicit','caps_respected','worker_source_stability')}
 if raw.get('lock_sha256')!=sha(LOCK):checks['source_native_lock']=False
 for rel,digest in lock['sources'].items():
  if rel in ('loaded_native_binary','native_build_manifest'):
   path=ROOT/('runners/dsl/python/substrate_rs/_native.build.json' if rel=='native_build_manifest' else json.loads(LOCK.read_text())['engine']['native_path'])
  else:path=ROOT/rel
  if not path.exists() or sha(path)!=digest:checks['source_native_lock']=False
 from domains.engine_provenance import build_is_stale
 if build_is_stale(str(ROOT)):checks['source_native_lock']=False
 rows=raw.get('workers',[]);expected=3*3*3*2
 if len(rows)!=expected or len({(r['size_cap'],r['probe_count'],r['replicate'],r['mode']) for r in rows})!=expected:
  checks['complete_unique_grid']=False
 if len({r.get('pid') for r in rows})!=expected:checks['complete_unique_grid']=False
 if lock.get('training')!={'n':1,'output':1} or any(r.get('training_example_count')!=1 for r in rows):
  checks['training_labels_fixed']=False
 by={(r['size_cap'],r['probe_count'],r['replicate'],r['mode']):r for r in rows}
 grouped={};metrics=[]
 for size in lock['sizes']:
  for p in lock['probe_counts']:
   for rep in range(lock['replicates']):
    b=by.get((size,p,rep,'batch'));s=by.get((size,p,rep,'stream'))
    if b is None or s is None:continue
    keys=('halt_reason','explored_terms','distinct_behaviors','hypothesis_count','hypothesis_sha256',
          'training_consistent_hypothesis_count')
    if any(b.get(k)!=s.get(k) for k in keys):checks['batch_stream_semantic_parity']=False
    if any(b.get(k)!=s.get(k) for k in ('target_hypothesis_present','heldout_exact_hypothesis_count','heldout_exact_terms')):
     checks['heldout_coverage_parity']=False
    for row in (b,s):
     if not row.get('source_stable'):checks['worker_source_stability']=False
     if not finite(row):checks['finite_resource_measurements']=False
     if row.get('training_consistent_hypothesis_count')!=row.get('hypothesis_count'):
      checks['all_pool_hypotheses_fit_anchor']=False
     if row.get('complete')!=(row.get('halt_reason')=='max_size'):
      checks['incomplete_stops_explicit']=False
     if (row.get('hypothesis_count',0)>lock['hypothesis_limit'] or row.get('probe_count')!=p
       or row.get('heldout_count')!=4 or row.get('explored_terms',0)<row.get('distinct_behaviors',0)
       or row.get('process_peak_rss_native_units',0)<=0 or row.get('synthesis_wall_ns',0)<=0
       or row.get('synthesis_cpu_ns',0)<=0):checks['caps_respected']=False
     for term in row.get('heldout_exact_terms',[]):
      preds=term.get('heldout_predictions',[])
      answers=[n*(n+1)//2 for n in lock['heldout']]
      if len(preds)!=4 or any(not isinstance(a,(int,float)) or abs(float(a)-y)>1e-9 for a,y in zip(preds,answers)):
       checks['heldout_coverage_parity']=False
     if len(row.get('heldout_exact_terms',[]))!=row.get('heldout_exact_hypothesis_count'):
      checks['heldout_coverage_parity']=False
     grouped.setdefault((size,p,row['mode']),[]).append(row)
     metrics.append(row)
 summary={}
 for size in lock['sizes']:
  for p in lock['probe_counts']:
   key=f'size{size}_probes{p}';summary[key]={}
   for mode in ('batch','stream'):
    rr=[by[(size,p,rep,mode)] for rep in range(lock['replicates']) if (size,p,rep,mode) in by]
    if not rr:continue
    summary[key][mode]={'completion_count':sum(r['complete'] for r in rr),'replicates':len(rr),
     'median_wall_ms':statistics.median(r['synthesis_wall_ns'] for r in rr)/1e6,
     'median_cpu_ms':statistics.median(r['synthesis_cpu_ns'] for r in rr)/1e6,
     'median_peak_rss_kib':statistics.median(r['process_peak_rss_native_units'] for r in rr),
     'median_hypothesis_heap_kib':statistics.median(r['approx_hypothesis_heap_bytes'] for r in rr)/1024,
     'median_explored_terms':statistics.median(r['explored_terms'] for r in rr),
     'median_hypothesis_count':statistics.median(r['hypothesis_count'] for r in rr),
     'target_present_count':sum(r['target_hypothesis_present'] for r in rr),
     'median_exact_heldout_hypotheses':statistics.median(r['heldout_exact_hypothesis_count'] for r in rr)}
   if 'batch' in summary[key] and 'stream' in summary[key]:
    b=summary[key]['batch'];s=summary[key]['stream']
    s['wall_ratio_stream_over_batch']=s['median_wall_ms']/b['median_wall_ms']
    s['peak_rss_ratio_stream_over_batch']=s['median_peak_rss_kib']/b['median_peak_rss_kib']
 result={'schema':'SubstrateGeneratorStreamScaleV1_2PostCaptureCorrection','checks':checks,
  'passed_checks':sum(checks.values()),'check_count':len(checks),'all_checks_pass':all(checks.values()),
  'cells':summary,'interpretation':'Paired one-family version-space construction cost and memory comparison. Incomplete pools remain outcomes; no general rung-three tractability claim follows.'}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
 print(json.dumps({'all_checks_pass':result['all_checks_pass'],'passed_checks':result['passed_checks'],
  'check_count':len(checks),'analysis':str(OUT)},indent=2))
 return 0 if result['all_checks_pass'] else 1
if __name__=='__main__':raise SystemExit(main())
