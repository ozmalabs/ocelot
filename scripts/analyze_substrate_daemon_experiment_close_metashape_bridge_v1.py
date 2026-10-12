#!/usr/bin/env python3
"""Preserve the preregistered outcome, including its status-criterion miss."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/substrate_daemon_experiment_close_metashape_bridge_v1_20260926.json'
LOCK=ROOT/'evaluation/substrate_capability/daemon_experiment_close_metashape_bridge_v1_lock_20260926.json'
OUT=ROOT/'evaluation/reports/substrate_daemon_experiment_close_metashape_bridge_v1_analysis_20260926.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());obs=raw['added_observations']
    statuses=[x['attrs'].get('status') for x in obs]
    gates={
      'source_and_protocol_lock_match':raw['lock_sha256']==sha(LOCK) and raw['protocol_sha256']==sha(ROOT/'docs/research/engine_substrate/SUBSTRATE_DAEMON_EXPERIMENT_CLOSE_METASHAPE_BRIDGE_PREREG_20260926.md') and all(len(v)==64 for v in raw['source_sha256'].values()),
      'growth_dependency_closure_loaded':raw['seed_load']['loaded']==2 and raw['seed_load']['total']==2 and not raw['seed_load']['failed'] and raw['seed_load']['selected_order']==['shape_vocabulary','meta_shape_growth'],
      'persistence_guard_active':raw['persistence_disabled'] is True,
      'both_experiments_closed':len(raw['experiments'])==2 and all(x['attrs'].get('taught') is True for x in raw['experiments']),
      'two_new_observations':len(obs)==2,
      'preregistered_residual_then_recognized_statuses':statuses==['residual','recognized'],
      'new_meta_shape_minted':len(raw['added_meta_shapes'])>=1 and all(x['attrs'].get('source')=='meta_shape_growth' for x in raw['added_meta_shapes']),
    }
    out={'schema_version':1,'run_id':raw['run_id'],'preregistered_gates':gates,'admitted':all(gates.values()),
         'observed':{'observation_statuses':statuses,'observation_residuals':[x['attrs'].get('residual') for x in obs],'new_meta_shapes':[{'name':x['attrs'].get('name'),'support':x['attrs'].get('support'),'signature':x['attrs'].get('signature')} for x in raw['added_meta_shapes']]},
         'interpretation':'The daemon close hook did teach both ready experiment conclusions, and the growth rules minted a MetaShape with support 2. However, the preregistered residual-then-recognized status gate failed: both observations were labeled recognized while carrying non-empty residual fields. Preserve this as a preregistered criterion miss and investigate the recognition/residual semantics separately; do not count it as an admitted pass.',
         'next_question':'On exact independent replay, are both records again recognized with axis_tag/topic residuals and does the growth rule mint the same support-2 abstraction?'}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':str(OUT),'admitted':out['admitted'],'gates':gates},indent=2));return 0 if out['admitted'] else 2
if __name__=='__main__':raise SystemExit(main())
