#!/usr/bin/env python3
"""Independent oracle and integrity analysis for acquisition controls v1."""
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'evaluation/reports/substrate_code_write_acquisition_controls_v1_raw_20261001.json'
LOCK=ROOT/'evaluation/substrate_capability/substrate_code_write_acquisition_controls_v1_lock_20261001.json'
PRELOCK=ROOT/'evaluation/substrate_capability/substrate_code_write_acquisition_controls_v1_lock_20261001_pre_analysis_correction.json'
OUT=ROOT/'evaluation/reports/substrate_code_write_acquisition_controls_v1_analysis_20261001.json'
def oracle(e):
 x,lo,hi=e['value'],e['lower'],e['upper']; return lo if x<lo else hi if x>hi else x
def main():
 raw=json.loads(RAW.read_text()); lock=json.loads(LOCK.read_text()); prelock=json.loads(PRELOCK.read_text())
 assert raw['lock']==raw['post_lock']==prelock
 assert lock['active']==prelock['active'] and lock['trees']==prelock['trees']
 assert {k:v for k,v in lock['files'].items() if not k.endswith('analyze_substrate_code_write_acquisition_controls_v1.py')} == {k:v for k,v in prelock['files'].items() if not k.endswith('analyze_substrate_code_write_acquisition_controls_v1.py')}
 rows=raw['workers']; assert len(rows)==4 and all(r.get('kind')=='worker' for r in rows)
 assert len({r['pid'] for r in rows})==4 and all(r['source_stable'] and r['before']==r['after']==lock['active'] for r in rows)
 assert sorted((r['arm'],r['rep']) for r in rows)==[(a,i) for a in ('exposure_only','mismatched_teaching') for i in (1,2)]
 exposure=[r for r in rows if r['arm']=='exposure_only']; mismatch=[r for r in rows if r['arm']=='mismatched_teaching']
 assert all(r['baseline'].get('ok') is False for r in rows)
 assert all(r['shapes_after']==r['shapes_before'] and r['intervention'].get('term') is not None for r in exposure)
 for r in mismatch:
  assert r['intervention'].get('ok') is True
  assert r['intervention'].get('shape')==r['written'].get('construction')
  assert len(r['heldout'])==12
 exact_native=exact_python=total=0
 for r in mismatch:
  for c in r['heldout']:
   y=oracle(c['input']); total+=1; exact_native+=c['native']==y; exact_python+=c['python']==y
 result={'schema':'SubstrateCodeWriteAcquisitionControlsV1Analysis','workers':len(rows),
  'source_lock_stable':True,'exposure_only_workers':len(exposure),'exposure_shape_growth':[r['shapes_after']-r['shapes_before'] for r in exposure],
  'mismatched_teaching_workers':len(mismatch),'mismatch_admitted_and_selected':[r['written'].get('construction')==r['intervention'].get('shape') for r in mismatch],
  'mismatch_heldout_total':total,'mismatch_native_exact':exact_native,'mismatch_python_exact':exact_python,
  'mismatch_native_exact_rate':exact_native/total if total else None,'mismatch_python_exact_rate':exact_python/total if total else None,
  'median_boot_seconds':statistics.median(r['boot_ns'] for r in rows)/1e9,
  'median_intervention_ms_by_arm':{a:statistics.median(r['intervention_ns'] for r in rows if r['arm']==a)/1e6 for a in ('exposure_only','mismatched_teaching')},
  'median_peak_rss_bytes':statistics.median(r['peak_rss_bytes'] for r in rows),
  'interpretation':'Exposure-only growth is checked as a direct state delta. Mismatched teaching is evaluated against an independent clamp oracle; any admitted-and-selected mismatch with oracle failures demonstrates a semantic validation gap for this pair, not a general false-admission rate.'}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); print(json.dumps(result,indent=2))
if __name__=='__main__': main()
