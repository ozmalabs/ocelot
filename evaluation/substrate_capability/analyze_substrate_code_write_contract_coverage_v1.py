#!/usr/bin/env python3
"""Independent analysis of narrow-contract aliasing versus a discriminating case."""
import json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'evaluation/reports/substrate_code_write_contract_coverage_v1_raw_20261001.json'
LOCK=ROOT/'evaluation/substrate_capability/substrate_code_write_contract_coverage_v1_lock_20261001.json'
PRELOCK=ROOT/'evaluation/substrate_capability/substrate_code_write_contract_coverage_v1_lock_20261001_pre_analysis_amendment.json'
OUT=ROOT/'evaluation/reports/substrate_code_write_contract_coverage_v1_analysis_20261001.json'
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());prelock=json.loads(PRELOCK.read_text());ws=raw['workers']
 assert raw['lock']==raw['post_lock']==prelock
 assert lock['active']==prelock['active'] and lock['trees']==prelock['trees']
 assert {k:v for k,v in lock['files'].items() if not k.endswith('analyze_substrate_code_write_contract_coverage_v1.py')} == {k:v for k,v in prelock['files'].items() if not k.endswith('analyze_substrate_code_write_contract_coverage_v1.py')}
 assert len(ws)==4 and all(w.get('kind')=='worker' for w in ws) and len({w['pid'] for w in ws})==4
 assert all(w['source_stable'] and w['before']==w['after']==lock['active'] for w in ws)
 assert sorted((w['arm'],w['rep']) for w in ws)==[(a,r) for a in ('aliasing_narrow','discriminating_wide') for r in (1,2)]
 narrow=[w for w in ws if w['arm']=='aliasing_narrow'];wide=[w for w in ws if w['arm']=='discriminating_wide']
 narrow_exact=0;heldout_total=0
 for w in narrow:
  t=w['teach'];assert t['ok'] and t['contract_validation']['ok'] and len(t['contract_validation']['checked'])==2
  for c in t['contract_validation']['checked']:
   x=c['inputs']['value'];expected=x*x
   assert x in (0,1) and c['expected']==expected and c['native_output']==x and c['python_output']==x
  assert w['taught_identity_present']
  assert w['written'].get('ok') is True and w['written'].get('construction')=='taught_identity'
  for c in w['heldout']:
   x=c['input']['value'];y=x*x;heldout_total+=1
   narrow_exact += type(c['native']) is int and c['native']==y and type(c['python']) is int and c['python']==y
 for w in wide:
  t=w['teach'];assert not t['ok'] and t['contract_validation']['ok'] is False
  cv=t['contract_validation'];assert cv['failed_index']==2 and cv['expected']==4 and cv['native_output']==2 and cv['python_output']==2
  assert not w['taught_identity_present']
  assert w['written'].get('ok') is False
 result={'schema':'SubstrateCodeWriteContractCoverageV1Analysis','workers':4,'source_lock_stable':True,
  'narrow_contract_admitted':len(narrow),'narrow_contract_rows_exact':sum(len(w['teach']['contract_validation']['checked']) for w in narrow),
  'narrow_contract_heldout_total':heldout_total,'narrow_contract_heldout_square_exact':narrow_exact,
  'wide_discriminating_contract_refused':len(wide),'wide_refusal_taught_identity_shapes':sum(w['taught_identity_present'] for w in wide),
  'observed_total_shape_count_delta_by_arm':{a:[w['shape_count_after']-w['shape_count_before'] for w in ws if w['arm']==a] for a in ('aliasing_narrow','discriminating_wide')},
  'median_boot_seconds':statistics.median(w['boot_ns'] for w in ws)/1e9,
  'median_acquisition_ms_by_arm':{a:statistics.median(w['acquire_ns'] for w in ws if w['arm']==a)/1e6 for a in ('aliasing_narrow','discriminating_wide')},
  'median_peak_rss_bytes':statistics.median(w['peak_rss_bytes'] for w in ws),
  'interpretation':'The contract gate rejects a mismatch only when supplied observations distinguish it. It does not itself select informative inputs or establish complete task semantics. Total signature counts changed during the combined read/teach call and are not attributed to teaching; the specific taught_identity signature is the acquisition outcome.'}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
