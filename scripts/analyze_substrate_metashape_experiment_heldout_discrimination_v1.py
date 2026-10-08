#!/usr/bin/env python3
"""Adjudicate held-out and fixed-field control behavior of one minted MetaShape."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/substrate_metashape_experiment_heldout_discrimination_v1_20260926.json'
LOCK=ROOT/'evaluation/substrate_capability/metashape_experiment_heldout_discrimination_v1_lock_20260926.json'
OUT=ROOT/'evaluation/reports/substrate_metashape_experiment_heldout_discrimination_v1_analysis_20260926.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());ph={p['phase']:p for p in raw['phases']}
    train,pos,neg=(ph[k] for k in ('training_pair','positive_holdout','negative_control'))
    shape=raw['minted_training_shape']
    gates={
      'source_and_protocol_lock_match':raw['lock_sha256']==sha(LOCK) and raw['protocol_sha256']==sha(ROOT/'docs/research/engine_substrate/SUBSTRATE_METASHAPE_EXPERIMENT_HELDOUT_DISCRIMINATION_PREREG_20260926.md') and all(len(h)==64 for h in raw['source_sha256'].values()),
      'dependency_closure_loads_cleanly':raw['seed_load']['loaded']==2 and raw['seed_load']['total']==2 and not raw['seed_load']['failed'],
      'persistence_guard_active':raw['persistence_disabled'] is True,
      'training_pair_mints_one_support_two_shape':len(train['observations'])==2 and len(train['new_meta_shapes'])==1 and train['new_meta_shapes'][0]['attrs'].get('support')==2 and train['new_meta_shapes'][0]['attrs'].get('name')==shape,
      'positive_holdout_uses_minted_shape':len(pos['observations'])==1 and pos['observations'][0]['attrs'].get('status')=='recognized' and pos['observations'][0]['attrs'].get('covered_by')==shape and not pos['new_meta_shapes'],
      'negative_control_refused_by_minted_shape':len(neg['observations'])==1 and neg['observations'][0]['attrs'].get('covered_by')!=shape and not neg['new_meta_shapes'],
      'negative_control_has_residual_status':neg['observations'][0]['attrs'].get('status')=='residual',
    }
    out={'schema_version':1,'run_id':raw['run_id'],'gates':gates,'admitted':all(gates.values()),
         'observed':{'minted_shape':shape,'training_statuses':[x['attrs'].get('status') for x in train['observations']],'positive_status':pos['observations'][0]['attrs'].get('status'),'positive_covered_by':pos['observations'][0]['attrs'].get('covered_by'),'negative_status':neg['observations'][0]['attrs'].get('status'),'negative_covered_by':neg['observations'][0]['attrs'].get('covered_by'),'negative_residual':neg['observations'][0]['attrs'].get('residual')},
         'interpretation':'The minted experiment-summary MetaShape transfers to one new supported summary and refuses one refuted summary whose fixed answer field differs. This is one support-2 schema-specific positive/negative pair, not a general false-positive rate or evidence that experiment conclusions are valid.',
         'limitations':['One minted pattern and one positive plus one negative holdout.','Support/refutation labels are authored by the harness; no outcome adjudication is tested.','No transfer to ordinary conversation or other node schemas is claimed.']}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':str(OUT),'admitted':out['admitted'],'gates':gates},indent=2));return 0 if out['admitted'] else 1
if __name__=='__main__':raise SystemExit(main())
