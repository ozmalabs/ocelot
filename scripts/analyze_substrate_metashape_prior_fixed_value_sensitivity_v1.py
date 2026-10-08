#!/usr/bin/env python3
"""Summarize rung-specific sensitivity over the locked 40-case panel."""
import hashlib,json
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/substrate_metashape_prior_fixed_value_sensitivity_v1_20260926.json'
LOCK=ROOT/'evaluation/substrate_capability/metashape_prior_fixed_value_sensitivity_v1_lock_20260926.json'
OUT=ROOT/'evaluation/reports/substrate_metashape_prior_fixed_value_sensitivity_v1_analysis_20260926.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());phases=raw['phases']
 counts=defaultdict(Counter);target=Counter();new_shape_control_count=0;obs_count=0
 for p in phases:
  for entry in p['observations']:
   o=entry['observation'];status=o.get('status','missing');covered=o.get('covered_by');shape=p.get('target_shape')
   obs_count+=1;counts[(p['kind'],p['family'])][status]+=1
   if p['kind'] not in ('training','positive'):
    if status=='recognized' and covered==shape:target['structural_target']+=1
    elif status=='recognized_prior' and covered==shape:target['prior_same_target']+=1
    elif status=='recognized_prior':target['prior_other']+=1
    elif status=='residual':target['residual']+=1
    else:target['other']+=1
    if p.get('new_meta_shapes'):new_shape_control_count+=len(p['new_meta_shapes'])
 summary={f'{kind}|{family}':dict(c) for (kind,family),c in sorted(counts.items())}
 gates={
  'source_and_protocol_lock_match':raw['lock_sha256']==sha(LOCK) and raw['protocol_sha256']==sha(ROOT/'docs/research/engine_substrate/SUBSTRATE_METASHAPE_PRIOR_FIXED_VALUE_SENSITIVITY_V1_PREREG_20260926.md') and all(len(x)==64 for x in raw['source_sha256'].values()),
  'seed_dependency_closure_complete':raw['seed_load']['loaded']==2 and raw['seed_load']['total']==2 and not raw['seed_load']['failed'],
  'persistence_disabled':raw['persistence_disabled'] is True,
  'all_locked_observations_captured':obs_count==40 and len(phases)==36,
  'native_extension_provenance_present':len(raw['native_extension_sha256'])==64,
 }
 result={'schema_version':1,'run_id':raw['run_id'],'admitted':all(gates.values()),'gates':gates,
  'outcome_counts':{'observations':obs_count,'controls':sum(sum(v.values()) for k,v in counts.items() if k[0] not in ('training','positive')),'control_rung_counts':dict(target),'new_shapes_minted_during_controls':new_shape_control_count},
  'by_phase_and_family':summary,
  'interpretation':'The sensitivity sweep measures how observations are classified across exact structural recognition, weak keyword-prior attribution, and residual outcomes. Keep the per-family/per-control table visible: recognized_prior is not equivalent to exact structural coverage. The panel is authored and does not estimate semantic error prevalence.',
  'limitations':['One process, four schemas, four fixed substitutions plus missing/extra/type controls per schema.','No semantic task oracle or downstream utility is measured.','No independent process replication yet.']}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':str(OUT),'admitted':result['admitted'],'gates':gates,'counts':result['outcome_counts']},indent=2));return 0 if result['admitted'] else 1
if __name__=='__main__':raise SystemExit(main())
