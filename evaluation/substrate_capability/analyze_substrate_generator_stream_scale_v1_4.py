#!/usr/bin/env python3
"""Analyze the explicitly resource-capped size-11 generator stress panel."""
from __future__ import annotations
import hashlib,json,math,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
LOCK=ROOT/'evaluation/substrate_capability/substrate_generator_stream_scale_v1_3_lock_20261002.json'
RAW=ROOT/'evaluation/reports/substrate_generator_stream_scale_v1_3_raw_20261002.json'
OUT=ROOT/'evaluation/reports/substrate_generator_stream_scale_v1_4_analysis_20261002.json'
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
 checks={k:True for k in ('source_native_lock','all_scheduled_outcomes_recorded','outcome_statuses_explicit',
  'complete_pair_pool_parity','complete_pair_heldout_parity','fixed_training_probe_design',
  'returned_pools_fit_anchor','complete_status_matches_halt_reason','completed_metrics_respect_caps',
  'incomplete_and_error_outcomes_preserved')}
 if raw.get('lock_sha256')!=sha(LOCK):checks['source_native_lock']=False
 for rel,digest in lock['sources'].items():
  if rel=='loaded_native_binary':path=ROOT/lock['engine']['native_path']
  elif rel=='native_build_manifest':path=ROOT/'runners/dsl/python/substrate_rs/_native.build.json'
  else:path=ROOT/rel
  if not path.exists() or sha(path)!=digest:checks['source_native_lock']=False
 from domains.engine_provenance import build_is_stale
 if build_is_stale(str(ROOT)):checks['source_native_lock']=False
 rows=raw.get('workers',[])
 expected={(z,p,r,m) for z in lock['sizes'] for p in lock['probe_counts']
  for r in range(lock['replicates']) for m in lock['modes']}
 keys=[(x.get('size_cap'),x.get('probe_count'),x.get('replicate'),x.get('mode')) for x in rows]
 if len(rows)!=len(expected) or set(keys)!=expected or len(set(keys))!=len(keys):checks['all_scheduled_outcomes_recorded']=False
 statuses={'completed','parent_timeout','address_space_failure','worker_error'}
 if any(x.get('capture_status') not in statuses for x in rows):checks['outcome_statuses_explicit']=False
 by={key:row for key,row in zip(keys,rows)};pair_status={}
 for size in lock['sizes']:
  for rep in range(lock['replicates']):
   b=by.get((size,12,rep,'batch'));s=by.get((size,12,rep,'stream'))
   if not b or not s:continue
   bc=b.get('capture_status')=='completed' and b.get('complete') is True
   sc=s.get('capture_status')=='completed' and s.get('complete') is True
   if bc and sc:
    fields=('halt_reason','explored_terms','distinct_behaviors','hypothesis_count','hypothesis_sha256',
     'training_consistent_hypothesis_count')
    if any(b.get(k)!=s.get(k) for k in fields):checks['complete_pair_pool_parity']=False
    if any(b.get(k)!=s.get(k) for k in ('target_hypothesis_present','heldout_exact_hypothesis_count','heldout_exact_terms')):
     checks['complete_pair_heldout_parity']=False
    status='both_complete'
   elif bc:status='batch_complete_only'
   elif sc:status='stream_complete_only'
   elif b.get('capture_status')=='completed' and s.get('capture_status')=='completed':status='both_returned_search_incomplete'
   else:status='at_least_one_no_worker_result'
   pair_status[f'size{size}_rep{rep}']=status
 complete_rows=[]
 for row in rows:
  if row.get('capture_status')!='completed':continue
  complete_rows.append(row)
  if row.get('training_example_count')!=1 or row.get('probe_count')!=12:
   checks['fixed_training_probe_design']=False
  if row.get('training_consistent_hypothesis_count')!=row.get('hypothesis_count'):
   checks['returned_pools_fit_anchor']=False
  if row.get('complete')!=(row.get('halt_reason')=='max_size'):
   checks['complete_status_matches_halt_reason']=False
  if (not finite(row) or row.get('hypothesis_count',0)>lock['hypothesis_limit']
   or row.get('explored_terms',0)<row.get('distinct_behaviors',0) or row.get('heldout_count')!=4
   or row.get('process_peak_rss_native_units',0)<=0 or row.get('synthesis_wall_ns',0)<=0
   or row.get('synthesis_cpu_ns',0)<=0 or row.get('address_space_limit_bytes')!=lock['address_space_limit_bytes']
   or row.get('parent_wall_ns',0)>lock['parent_timeout_s']*1e9+1e9):
   checks['completed_metrics_respect_caps']=False
  for exact in row.get('heldout_exact_terms',[]):
   expected_y=[n*(n+1)//2 for n in lock['heldout']];pred=exact.get('heldout_predictions',[])
   if len(pred)!=4 or any(not isinstance(x,(int,float)) or abs(float(x)-y)>1e-9 for x,y in zip(pred,expected_y)):
    checks['complete_pair_heldout_parity']=False
  if len(row.get('heldout_exact_terms',[]))!=row.get('heldout_exact_hypothesis_count'):
   checks['complete_pair_heldout_parity']=False
  if not row.get('source_stable') or row.get('pid') is None:checks['source_native_lock']=False
 if lock.get('training')!={'n':1,'output':1} or lock.get('probe_counts')!=[12]:checks['fixed_training_probe_design']=False
 seen_pids=[x.get('pid') for x in complete_rows]
 if len(seen_pids)!=len(set(seen_pids)):checks['incomplete_and_error_outcomes_preserved']=False
 summary={}
 for size in lock['sizes']:
  summary[str(size)]={}
  for mode in lock['modes']:
   rr=[x for x in rows if x.get('size_cap')==size and x.get('mode')==mode]
   done=[x for x in rr if x.get('capture_status')=='completed']
   summary[str(size)][mode]={'scheduled':len(rr),'worker_returned':len(done),
    'search_complete':sum(x.get('complete') is True for x in done),
    'internal_timeout':sum(x.get('halt_reason')=='timeout' for x in done),
    'parent_timeout':sum(x.get('capture_status')=='parent_timeout' for x in rr),
    'address_space_failure':sum(x.get('capture_status')=='address_space_failure' for x in rr),
    'worker_error':sum(x.get('capture_status')=='worker_error' for x in rr)}
   fields=(('median_synthesis_wall_ms','synthesis_wall_ns',1e6),('median_synthesis_cpu_ms','synthesis_cpu_ns',1e6),
    ('median_peak_rss_kib','process_peak_rss_native_units',1),('median_explored_terms','explored_terms',1),
    ('median_hypothesis_count','hypothesis_count',1),('median_exact_heldout_hypotheses','heldout_exact_hypothesis_count',1))
   for out,key,scale in fields:
    vals=[x[key] for x in done if key in x]
    summary[str(size)][mode][out]=statistics.median(vals)/scale if vals else None
   summary[str(size)][mode]['target_present_replicates']=sum(bool(x.get('target_hypothesis_present')) for x in done)
 result={'schema':'SubstrateGeneratorStreamScaleV1_4Analysis','checks':checks,
  'passed_checks':sum(checks.values()),'check_count':len(checks),'all_checks_pass':all(checks.values()),
  'pair_status':pair_status,'by_size_and_mode':summary,
  'interpretation':'Parent- and address-space-capped single-family search experiment; explicit incomplete outcomes are not generalized into a complexity claim.'}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
 print(json.dumps({'all_checks_pass':result['all_checks_pass'],'passed_checks':result['passed_checks'],
  'check_count':len(checks),'analysis':str(OUT)},indent=2))
 return 0 if result['all_checks_pass'] else 1
if __name__=='__main__':raise SystemExit(main())
