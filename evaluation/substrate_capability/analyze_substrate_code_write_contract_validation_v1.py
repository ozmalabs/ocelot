#!/usr/bin/env python3
"""Independent oracle analysis for code-write contract validation v1."""
import json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'evaluation/reports/substrate_code_write_contract_validation_v1_raw_20261001.json'
LOCK=ROOT/'evaluation/substrate_capability/substrate_code_write_contract_validation_v1_lock_20261001.json'
OUT=ROOT/'evaluation/reports/substrate_code_write_contract_validation_v1_analysis_20261001.json'
def main():
 raw=json.loads(RAW.read_text()); lock=json.loads(LOCK.read_text()); workers=raw['workers']
 assert raw['lock']==raw['post_lock']==lock
 assert len(workers)==4 and all(w.get('kind')=='worker' for w in workers)
 assert len({w['pid'] for w in workers})==4
 assert all(w['source_stable'] and w['before']==w['after']==lock['active'] for w in workers)
 assert sorted((w['arm'],w['rep']) for w in workers)==[(a,r) for a in ('aligned_parity','mismatched_parity_as_square') for r in (1,2)]
 aligned=[w for w in workers if w['arm']=='aligned_parity']; mismatch=[w for w in workers if w['arm']=='mismatched_parity_as_square']
 checked=0
 for w in aligned:
  r=w['result']; assert r['ok'] and r['shape']=='taught_parity' and r['contract_validation']['ok']
  assert w['taught_shape_present'] and w['shape_count_after']==w['shape_count_before']+1
  cases=r['contract_validation']['checked']; assert len(cases)==5
  for c in cases:
   x=c['inputs']['value']; expected=(x%2==0); checked+=1
   assert type(c['expected']) is bool and c['expected']==expected
   assert type(c['native_output']) is bool and c['native_output']==expected
   assert type(c['python_output']) is bool and c['python_output']==expected
 for w in mismatch:
  r=w['result']; assert not r['ok'] and r['contract_validation']['ok'] is False
  assert r['contract_validation']['failed_index']==0
  assert not w['taught_shape_present'] and w['shape_count_after']==w['shape_count_before']
  c=r['contract_validation']; x=c['checked'][0]['inputs']['value']; expected=x*x
  assert c['expected']==expected and c['native_output']!=expected and c['python_output']!=expected
 result={'schema':'SubstrateCodeWriteContractValidationV1Analysis','workers':4,'source_lock_stable':True,
  'aligned_admitted':len(aligned),'aligned_contract_cases_exact':checked,'mismatch_refused':len(mismatch),
  'mismatch_codebook_growth':sum(w['shape_count_after']-w['shape_count_before'] for w in mismatch),
  'mismatch_refusal_reason':'independent expected output disagreed with both native Term and rendered Python on first case',
  'median_boot_seconds':statistics.median(w['boot_ns'] for w in workers)/1e9,
  'median_acquisition_ms_by_arm':{a:statistics.median(w['acquire_ns'] for w in workers if w['arm']==a)/1e6 for a in ('aligned_parity','mismatched_parity_as_square')},
  'median_peak_rss_bytes':statistics.median(w['peak_rss_bytes'] for w in workers),
  'claim_boundary':'caller-supplied contract examples prevent the measured false transfer and permit the aligned parity example; correctness and coverage of those contract examples remain external assumptions'}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); print(json.dumps(result,indent=2))
if __name__=='__main__':main()
