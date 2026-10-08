#!/usr/bin/env python3
"""Independent count, exclusion, and provenance checks for current-source site scaling."""
from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RUNNER=ROOT/'evaluation/substrate_capability/measure_edge_identity_site_scaling_current_source_v1_1.py'
LOCK=ROOT/'evaluation/substrate_capability/edge_identity_site_scaling_current_source_v1_1_lock_20261003.json'
CAPTURE=ROOT/'evaluation/reports/edge_identity_site_scaling_current_source_v1_1_20261003.json'
OUT=ROOT/'evaluation/reports/edge_identity_site_scaling_current_source_v1_1_analysis_20261003.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 spec=importlib.util.spec_from_file_location('site_scaling_runner',RUNNER)
 runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
 lock=json.loads(LOCK.read_text());capture=json.loads(CAPTURE.read_text());rows=capture['rows']
 expected=list(lock['attribute_counts'])
 checks={
  'schema':capture.get('schema')=='EdgeIdentitySiteScalingCurrentSourceV1_1Results',
  'complete_field_count_matrix':[r['attribute_fields'] for r in rows]==expected,
  'formula_and_relation_counts':all(r['attribute_sites']==r['expected_attribute_sites']==
      (r['attribute_fields']+r['attribute_fields']*(r['attribute_fields']-1)//2+(1 if r['attribute_fields']>2 else 0))
      and r['total_sites']==r['attribute_sites']+1 for r in rows),
  'direct_field_coverage':all(r['eligible_fields']==[f'f{i:03d}' for i in range(r['attribute_fields'])] for r in rows),
  'unsupported_fields_excluded':all(r['excluded_constant_or_computed'] for r in rows),
  'timing_samples_complete':all(len(r['trial_ns'])==lock['trials'] and all(x>=0 for x in r['trial_ns']) and
      r['median_ns']==sorted(r['trial_ns'])[len(r['trial_ns'])//2] for r in rows),
  'capture_source_lock_consistent':capture.get('sources')==lock['sources'] and runner.frozen()==lock['sources'],
  'capture_bound_to_lock':capture.get('lock_sha256')==sha(LOCK),
  'current_edit_ops_hash_locked':lock['sources'].get('domains/edit_ops.py')==sha(ROOT/'domains/edit_ops.py'),
  'runner_analyzer_protocol_amendment_locked':all(k in lock['sources'] for k in (
      'evaluation/substrate_capability/measure_edge_identity_site_scaling_current_source_v1_1.py',
      'evaluation/substrate_capability/analyze_edge_identity_site_scaling_current_source_v1_1.py',
      'protocol','amendment')),
 }
 report={'schema':'EdgeIdentitySiteScalingCurrentSourceV1_1Analysis','checks':checks,
   'all_checks_pass':all(checks.values()),'field_counts':len(rows),
   'summary':[{'attribute_fields':r['attribute_fields'],'sites':r['total_sites'],
      'attribute_sites':r['attribute_sites'],'median_ms':r['median_ns']/1e6} for r in rows],
   'capture_sha256':sha(CAPTURE)}
 if OUT.exists():raise SystemExit('refusing to overwrite analysis')
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
 print(json.dumps(report,indent=2))
 if not report['all_checks_pass']:raise SystemExit('independent analysis failed')
if __name__=='__main__':main()
