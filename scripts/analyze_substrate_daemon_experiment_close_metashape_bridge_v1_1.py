#!/usr/bin/env python3
"""Gate the fresh-process close-action residual/mint replication."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/substrate_daemon_experiment_close_metashape_bridge_v1_1_20260926.json'
LOCK=ROOT/'evaluation/substrate_capability/daemon_experiment_close_metashape_bridge_v1_1_lock_20260926.json'
OUT=ROOT/'evaluation/reports/substrate_daemon_experiment_close_metashape_bridge_v1_1_analysis_20260926.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());obs=raw['added_observations'];metas=raw['added_meta_shapes']
    residual_predicates=[sorted(r[0] for r in x['attrs'].get('residual',[])) for x in obs]
    gates={
      'source_and_protocol_lock_match':raw['lock_sha256']==sha(LOCK) and raw['protocol_sha256']==sha(ROOT/'docs/research/engine_substrate/SUBSTRATE_DAEMON_EXPERIMENT_CLOSE_METASHAPE_BRIDGE_V1_1_AMENDMENT_20260926.md') and all(len(v)==64 for v in raw['source_sha256'].values()),
      'growth_dependencies_loaded':raw['seed_load']['loaded']==2 and raw['seed_load']['total']==2 and not raw['seed_load']['failed'],
      'persistence_guard_active':raw['persistence_disabled'] is True,
      'both_experiment_closures_completed':len(raw['experiments'])==2 and all(x['attrs'].get('taught') is True for x in raw['experiments']),
      'both_observations_recognized_with_locked_residuals':[x['attrs'].get('status') for x in obs]==['recognized','recognized'] and residual_predicates==[['axis_tag','topic'],['axis_tag','topic']],
      'one_support_two_growth_mint':len(metas)==1 and metas[0]['attrs'].get('source')=='meta_shape_growth' and metas[0]['attrs'].get('support')==2,
    }
    out={'schema_version':1,'run_id':raw['run_id'],'gates':gates,'admitted':all(gates.values()),
         'observed':{'observation_statuses':[x['attrs'].get('status') for x in obs],'observation_residuals':[x['attrs'].get('residual') for x in obs],'new_meta_shapes':[{'name':x['attrs'].get('name'),'support':x['attrs'].get('support')} for x in metas]},
         'interpretation':'The v1.1 fresh-process capture reproduces the status pattern that failed v1 preregistration: both graph-ready conclusions are marked taught; both ShapeObservations are status recognized with residual predicates axis_tag and topic; the growth rule mints one MetaShape with support 2. This is a reproducible controlled close-action-to-symbolic-mint bridge. The residual fields expose two varying properties, but this fixture does not establish that the abstraction is useful, safe, or generalizes.',
         'limitations':['Two harness-authored supported conclusions, not experimentally generated evidence.','One independent process replication beyond v1.','No downstream transfer, false-mint, forgetting, or long-run graph-growth measurement.']}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':str(OUT),'admitted':out['admitted'],'gates':gates},indent=2));return 0 if out['admitted'] else 1
if __name__=='__main__':raise SystemExit(main())
