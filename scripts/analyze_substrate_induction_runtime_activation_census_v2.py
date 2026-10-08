#!/usr/bin/env python3
"""Independent structural and behavioral gates for runtime activation census v2."""
import hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/substrate_induction_runtime_activation_census_v2_20260926.json'
OUT=ROOT/'evaluation/reports/substrate_induction_runtime_activation_census_v2_analysis_20260926.json'
def main():
    raw=json.loads(RAW.read_text()); arms={x['arm']:x for x in raw['cases']}
    full,chat,embodied=(arms[k] for k in ('daemon_full','daemon_chat','daemon_embodied'))
    gates={
      'three_daemon_fresh_boot_arms_present':set(arms)=={'daemon_full','daemon_chat','daemon_embodied'},
      'full_load_recorded_partial_failures':full['before']['loader_loaded']==729 and full['before']['loader_total']==740 and len(full['before']['loader_failed'])==11,
      'full_profile_has_meta_growth':full['before']['shape_decode_loop_loaded'] and full['before']['meta_shape_growth_loaded'] and full['before']['shape_vocabulary_loaded'],
      'full_teach_observations_reach_growth':[x['status'] for x in full['teach']]==['residual','recognized'] and full['teach'][-1]['new_meta_shapes']==['ms_is_a_slot_a_slot_b'],
      'chat_profile_excludes_growth_and_stays_pending':not chat['before']['meta_shape_growth_loaded'] and [x['status'] for x in chat['teach']]==['pending','pending'] and not chat['teach'][-1]['new_meta_shapes'],
      'embodied_profile_excludes_growth_and_stays_pending':not embodied['before']['meta_shape_growth_loaded'] and [x['status'] for x in embodied['teach']]==['pending','pending'] and not embodied['teach'][-1]['new_meta_shapes'],
      'inspected_flags_absent':all(v is None for arm in arms.values() for v in arm['before']['flags'].values()),
      'source_and_native_hashes_present':all(len(h)==64 for h in raw['source_sha256'].values()) and len(raw['native_extension_sha256'])==64,
    }
    out={'schema_version':2,'run_id':raw['run_id'],'gates':gates,'admitted':all(gates.values()),
         'observed':{k:{'seed_ids_selected_or_attempted':v['before']['seed_ids_selected_or_attempted'],'loader_loaded':v['before'].get('loader_loaded'),'loader_total':v['before'].get('loader_total'),'failed_seed_count':len(v['before'].get('loader_failed',v['before'].get('seed_load_failures',[]))),'shape_decode_loop_loaded':v['before']['shape_decode_loop_loaded'],'meta_shape_growth_loaded':v['before']['meta_shape_growth_loaded'],'statuses':[x['status'] for x in v['teach']],'new_meta_shapes':v['teach'][-1]['new_meta_shapes']} for k,v in arms.items()},
         'interpretation':'The daemon full fresh-boot path loads shape_decode_loop and meta_shape_growth despite 11 unrelated seed failures among 740 selected manifests; the repeated teaching fixture reaches residual then recognition and adds one MetaShape. The chat and embodied fresh-boot paths omit growth rules and leave the same fixture pending. This differs from the separately selected conversation evaluation profile, which also omits meta_shape_growth. These are controlled boot/fixture activation results, not natural teaching prevalence or capability-generalization estimates.',
         'limitations':['One process with fresh adapters; no checkpoint-resume arm.','Repeated authored relational-shape examples probe activation, not natural residual distributions or false-mint rates.','Full boot has 11 seed-load failures; captured list is preserved in raw data.']}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':str(OUT),'admitted':out['admitted'],'gates':gates},indent=2));return 0 if out['admitted'] else 1
if __name__=='__main__': raise SystemExit(main())
