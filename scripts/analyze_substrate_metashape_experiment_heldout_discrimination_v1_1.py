#!/usr/bin/env python3
"""Adjudicate independent held-out MetaShape transfer replication."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/substrate_metashape_experiment_heldout_discrimination_v1_1_20260926.json'
LOCK=ROOT/'evaluation/substrate_capability/metashape_experiment_heldout_discrimination_v1_1_lock_20260926.json'
OUT=ROOT/'evaluation/reports/substrate_metashape_experiment_heldout_discrimination_v1_1_analysis_20260926.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());ph={p['phase']:p for p in raw['phases']}
    train,pos,neg=(ph[k] for k in ('training_pair','positive_holdout','negative_control'));shape=raw['minted_training_shape']
    gates={
      'source_and_protocol_lock_match':raw['lock_sha256']==sha(LOCK) and raw['protocol_sha256']==sha(ROOT/'docs/research/engine_substrate/SUBSTRATE_METASHAPE_EXPERIMENT_HELDOUT_DISCRIMINATION_V1_1_AMENDMENT_20260926.md') and all(len(h)==64 for h in raw['source_sha256'].values()),
      'dependency_closure_loads_cleanly':raw['seed_load']['loaded']==2 and raw['seed_load']['total']==2 and not raw['seed_load']['failed'],
      'persistence_guard_active':raw['persistence_disabled'] is True,
      'training_pair_mints_one_support_two_shape':len(train['observations'])==2 and len(train['new_meta_shapes'])==1 and train['new_meta_shapes'][0]['attrs'].get('support')==2 and train['new_meta_shapes'][0]['attrs'].get('name')==shape,
      'positive_holdout_uses_minted_shape':len(pos['observations'])==1 and pos['observations'][0]['attrs'].get('status')=='recognized' and pos['observations'][0]['attrs'].get('covered_by')==shape and not pos['new_meta_shapes'],
      'negative_control_refused_by_minted_shape':len(neg['observations'])==1 and neg['observations'][0]['attrs'].get('covered_by')!=shape and not neg['new_meta_shapes'],
      'negative_control_has_residual_status':neg['observations'][0]['attrs'].get('status')=='residual',
    }
    out={'schema_version':1,'run_id':raw['run_id'],'gates':gates,'admitted':all(gates.values()),
         'observed':{'minted_shape':shape,'positive_covered_by':pos['observations'][0]['attrs'].get('covered_by'),'negative_status':neg['observations'][0]['attrs'].get('status'),'negative_residual':neg['observations'][0]['attrs'].get('residual')},
         'interpretation':'An independent fresh-process run reproduces the v1 support-2 mint, transfer to one supported held-out summary, and refusal of one refuted summary differing in fixed answer. This is replication of a narrow authored pattern, not a broad false-positive estimate.',
         'limitations':['One independent exact replication; one pattern and one positive/negative holdout pair.','Authored outcomes do not test evidence validity.','No prevalence, cross-domain, or broad generalization claim.']}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':str(OUT),'admitted':out['admitted'],'gates':gates},indent=2));return 0 if out['admitted'] else 1
if __name__=='__main__':raise SystemExit(main())
