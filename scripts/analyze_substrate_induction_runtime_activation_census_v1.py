#!/usr/bin/env python3
"""Independent adjudication of the clean-boot induction activation capture."""
from __future__ import annotations
import hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/substrate_induction_runtime_activation_census_v1_20260926.json'
OUT=ROOT/'evaluation/reports/substrate_induction_runtime_activation_census_v1_analysis_20260926.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    raw=json.loads(RAW.read_text());cases={x['arm']:x for x in raw['cases']}
    core=cases['WorldAdapter_default_core'];conv=cases['selected_conversation_profile'];growth=cases['explicit_meta_shape_growth_dependency_closure']
    gates={
      'all_three_arms_present':len(cases)==3,
      'conversation_profile_loaded_without_failures':conv['before']['profile_loaded']==70 and not conv['before']['profile_failed'],
      'default_core_omits_shape_growth_seeds':not core['before']['shape_decode_loop_loaded'] and not core['before']['meta_shape_growth_loaded'],
      'conversation_profile_loads_shape_loop_but_not_meta_growth':conv['before']['shape_decode_loop_loaded'] and not conv['before']['meta_shape_growth_loaded'],
      'teaching_is_residual_inert_without_growth_rules':all(x['status']=='pending' for x in core['teach']+conv['teach']),
      'explicit_growth_path_processes_teaching':growth['before']['meta_shape_growth_loaded'] and [x['status'] for x in growth['teach']]==['residual','recognized'],
      'explicit_growth_path_mints_one_shape':len(growth['teach'][-1]['minted_shapes'])==1 and growth['teach'][-1]['minted_shapes'][0]=='ms_is_a_slot_a_slot_b',
      'learner_flags_absent_in_clean_profiles':all(all(v is None for v in c['before']['agent_flags'].values()) for c in (core,conv,growth)),
      'source_hashes_present':all(len(x)==64 for x in raw['source_sha256'].values()) and len(raw.get('native_extension_sha256',''))==64,
    }
    result={'schema_version':1,'run_id':raw['run_id'],'gates':gates,'admitted':all(gates.values()),'observed':{
      'default_core_seed_count':core['before']['loaded_seed_count'],
      'conversation_profile_seed_count':conv['before']['loaded_seed_count'],
      'conversation_profile_loaded':conv['before']['profile_loaded'],
      'teach_status_default_core':[x['status'] for x in core['teach']],
      'teach_status_conversation_profile':[x['status'] for x in conv['teach']],
      'teach_status_explicit_growth':[x['status'] for x in growth['teach']],
      'minted_growth_shape':growth['teach'][-1]['minted_shapes'],
    },'interpretation':'The current default WorldAdapter core does not install either shape_decode_loop or meta_shape_growth. The selected conversation profile installs shape_decode_loop but not meta_shape_growth; the two normal teach() observations remain pending. Explicitly selecting meta_shape_growth and its dependency installs the Rung-4 symbolic growth path; the same teach() surface produces residual then recognition with one minted MetaShape. This is activation evidence on these boot/teaching fixtures, not a population estimate or evidence of default autonomous learning.','limitations':['One process and one selected conversation-profile build.','The explicit-growth examples are authored and intentionally repeated.','This does not prove every call site or alternate boot profile has the same activation state.']}
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':str(OUT),'admitted':result['admitted'],'gates':gates},indent=2));return 0 if result['admitted'] else 1
if __name__=='__main__':raise SystemExit(main())
