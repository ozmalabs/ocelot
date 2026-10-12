#!/usr/bin/env python3
"""Report all gates and per-family contrasts for the multi-schema transfer panel."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/substrate_metashape_multischema_transfer_panel_v1_20260926.json'
LOCK=ROOT/'evaluation/substrate_capability/metashape_multischema_transfer_panel_v1_lock_20260926.json'
OUT=ROOT/'evaluation/reports/substrate_metashape_multischema_transfer_panel_v1_analysis_20260926.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());ph={(p['phase'],p['item_type']):p for p in raw['phases']}
    families=sorted(raw['shape_by_family']);train_ok=positive_ok=negative_refused=negative_residual=0;rows=[]
    for family in families:
        tr,pos,neg=(ph[(label,family)] for label in ('training','positive_holdout','negative_control'))
        shape=raw['shape_by_family'][family]
        minted=(len(tr['new_meta_shapes'])==1 and tr['new_meta_shapes'][0]['attrs'].get('support')==2 and shape is not None)
        pos_covered=bool(shape and pos['observations'][0]['attrs'].get('covered_by')==shape and pos['observations'][0]['attrs'].get('status')=='recognized')
        neg_refused=pos_refused=bool(shape and neg['observations'][0]['attrs'].get('covered_by')!=shape)
        neg_resid=neg['observations'][0]['attrs'].get('status')=='residual'
        train_ok+=minted;positive_ok+=pos_covered;negative_refused+=neg_refused;negative_residual+=neg_resid
        rows.append({'item_type':family,'minted_shape':shape,'training_minted_support_two':minted,
                     'positive_status':pos['observations'][0]['attrs'].get('status'),'positive_covered_by':pos['observations'][0]['attrs'].get('covered_by'),'positive_uses_target_shape':pos_covered,
                     'negative_status':neg['observations'][0]['attrs'].get('status'),'negative_covered_by':neg['observations'][0]['attrs'].get('covered_by'),'negative_refused_by_target_shape':neg_refused,'negative_residual':neg_resid})
    gates={
      'source_and_protocol_lock_match':raw['lock_sha256']==sha(LOCK) and raw['protocol_sha256']==sha(ROOT/'docs/research/engine_substrate/SUBSTRATE_METASHAPE_MULTISCHEMA_TRANSFER_PANEL_V1_PREREG_20260926.md') and all(len(h)==64 for h in raw['source_sha256'].values()),
      'dependency_closure_loads_cleanly':raw['seed_load']['loaded']==2 and raw['seed_load']['total']==2 and not raw['seed_load']['failed'],
      'persistence_guard_active':raw['persistence_disabled'] is True,
      'all_four_training_schemas_mint_support_two_shapes':train_ok==4,
      'all_four_positive_holdouts_use_target_shape':positive_ok==4,
      'all_four_negative_controls_refused_by_target_shape':negative_refused==4,
      'all_four_negative_controls_remain_residual':negative_residual==4,
    }
    out={'schema_version':1,'run_id':raw['run_id'],'gates':gates,'admitted':all(gates.values()),
         'counts':{'training_mint_pass':train_ok,'positive_target_transfer_pass':positive_ok,'negative_target_refusal_pass':negative_refused,'negative_residual_pass':negative_residual,'families':len(families)},
         'families':rows,
         'interpretation':'This panel does not pass its preregistered generalization gates. Only three of four families mint a new support-2 shape; only three positive holdouts are covered by their intended minted shapes. Only one of four negative controls is left residual and refused by its target pattern. One family is absorbed by a preexisting spatial_dynamics pattern, and two minted schemas cover their fixed-field negative despite the changed field. These are exact structural matcher outcomes on authored probes, not estimates of semantic false-positive frequency.',
         'limitations':['Single process and four authored schemas.','The “negative” labels mark designed fixed-field mismatches; semantic task truth is not independently established.','No independent process replication yet.']}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':str(OUT),'admitted':out['admitted'],'gates':gates,'counts':out['counts']},indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
