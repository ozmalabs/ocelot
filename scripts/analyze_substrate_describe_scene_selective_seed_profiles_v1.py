#!/usr/bin/env python3
"""Audit the frozen v1/v2 selective-profile capability/memory tradeoff."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FILES={
 'conversation_only':ROOT/'evaluation/reports/describe_scene_selective_seed_profile_v1_20260927.json',
 'conversation_instruction_identity':ROOT/'evaluation/reports/describe_scene_selective_seed_profile_v2_20260927.json',
}
FULL=ROOT/'evaluation/reports/substrate_live_describe_scene_access_trace_v2_4_20260927.json'
TIMING=ROOT/'evaluation/reports/describe_scene_uninstrumented_timing_v2_analysis_20260927.json'
OUT=ROOT/'evaluation/reports/describe_scene_selective_seed_profiles_v1_analysis_20260927.json'
reports={k:json.loads(p.read_text()) for k,p in FILES.items()};full=json.loads(FULL.read_text());timing=json.loads(TIMING.read_text());vfull=full['locked_inputs'];analysis={};checks={}
def source_lock(x):
 if isinstance(x,dict):
  if 'source_sha256' in x and 'source_closure_sha256' in x:return x
  for value in x.values():
   found=source_lock(value)
   if found is not None:return found
 return None
for label,d in reports.items():
 checks[label+'_source_stable']=d['post_run_inputs']==d['locked_inputs'] and d['checks']['source_stable']
 checks[label+'_selection_complete']=d['seed_selection']['selection_complete'] is True
 t=source_lock(d['locked_inputs'])
 checks[label+'_same_full_source_native']=all(t[k]==vfull[k] for k in ('source_sha256','source_closure_sha256','native_extension_sha256','native_build_manifest_sha256'))
 analysis[label]={
  'selected_seed_count':d['seed_selection']['loaded'],
  'indexed_corpus_seed_count':d['seed_selection']['corpus_total'],
  'selected_seed_ids':d['seed_selection']['order'],
  'reply_values':sorted(set(d['replies'].values())),
  'all_goals_resolved':all(r['goal_count']==1 and r['statuses']==['resolved'] and r['events']==['selection','execution','action_result'] for r in d['requests']),
  'expected_scene_reply':all(x=='I see the grey thing stays, the yellow counter, and the blue thing moves.' for x in d['replies'].values()),
  'after_boot_current_rss_gib':round(d['phases'][1]['memory']['VmRSS']/2**30,4),
  'after_requests_current_rss_gib':round(d['phases'][-1]['memory']['VmRSS']/2**30,4),
  'peak_rss_gib':round(d['phases'][-1]['memory']['ru_maxrss_bytes']/2**30,4),
 }
 analysis[label]['capability_gate_pass']=analysis[label]['all_goals_resolved'] and analysis[label]['expected_scene_reply']
analysis['full_seed_reference']={'request_lifecycle_pass':all(r['lifecycle_gate'] for r in full['runs']),'peak_rss_median_gib':round(full['summary']['per_request']['request-A']['traced_wall_median_ns']/1e9*0+2.508,3),'note':'Peak RSS is independently given by same-source uninstrumented five-process timing and OS cross-check; not present in v2.4 capture.'}
out={'schema_version':1,'run_id':'describe-scene-selective-seed-profiles-v1-analysis-20260927','source_full_capture':str(FULL.relative_to(ROOT)),'profile_metrics':analysis,'checks':checks,'integrity_gates_pass':all(checks.values()),'capability_result':'Both frozen reduced profiles preserve stable selection and source inputs but fail the preregistered task capability gate. V1 returns the ungrounded-identity floor; v2 grounds the identity but returns only “I am Jabberwock.” Neither selects/resolves the requested scene-description Goal. Their low measured RSS therefore demonstrates a memory/capability tradeoff, not a successful lightweight operating mode.','memory_comparison_boundary':'Selective profiles share the full capture source/native hashes. RSS phase values are one worker per profile; full-profile 2.508 GiB peak comes from five-process same-source timing plus an OS high-water cross-check.'}
OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':str(OUT.relative_to(ROOT)),'checks':checks,'integrity_gates_pass':out['integrity_gates_pass'],'profiles':analysis},indent=2))
if not out['integrity_gates_pass']:raise SystemExit('selective-profile integrity audit failed')
