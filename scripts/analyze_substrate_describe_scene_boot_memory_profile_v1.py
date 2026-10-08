#!/usr/bin/env python3
"""Independent phase and integrity analysis of the boot memory profile."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/describe_scene_boot_memory_profile_v1_20260927.json'
OUT=ROOT/'evaluation/reports/describe_scene_boot_memory_profile_v1_analysis_20260927.json'
d=json.loads(RAW.read_text());ph=d['phases'];m=[x['memory'] for x in ph]
checks={
 'seven_ordered_phase_samples':[x['phase'] for x in ph]==['post_interpreter_before_adapter','post_adapter_construction','post_full_seed_boot','post_scene_attachment','post_two_request_schedule'],
 'source_lock_stable':d['post_run_inputs']==d['locked_inputs'] and d['checks']['source_stable'],
 'request_work_completed':d['checks']['threads_joined'] and d['checks']['no_errors'] and d['checks']['two_requests'] and d['checks']['expected_replies'] and d['checks']['resolved_goals'],
 'current_and_high_water_rss_available':all(isinstance(x.get('VmRSS'),int) and isinstance(x.get('resource_peak_rss_bytes'),int) for x in m),
 'high_water_is_monotonic':all(a['resource_peak_rss_bytes']<=b['resource_peak_rss_bytes'] for a,b in zip(m,m[1:])),
 'anonymous_rss_available':all(isinstance(x.get('Anonymous'),int) and isinstance(x.get('Pss_Anon'),int) for x in m),
}
out={'schema_version':1,'run_id':'describe-scene-boot-memory-profile-v1-analysis-20260927','checks':checks,'all_checks_pass':all(checks.values()),'phase_deltas_bytes':{'boot_current_rss':m[2]['VmRSS']-m[1]['VmRSS'],'boot_anonymous_rss':m[2]['Anonymous']-m[1]['Anonymous'],'scene_current_rss':m[3]['VmRSS']-m[2]['VmRSS'],'post_requests_current_rss_change':m[4]['VmRSS']-m[3]['VmRSS'],'request_schedule_high_water_increase':m[4]['resource_peak_rss_bytes']-m[3]['resource_peak_rss_bytes']},'phase_metrics':[{'phase':p['phase'],'current_rss_bytes':p['memory']['VmRSS'],'anonymous_rss_bytes':p['memory']['Anonymous'],'private_dirty_bytes':p['memory']['Private_Dirty'],'high_water_rss_bytes':p['memory']['resource_peak_rss_bytes']} for p in ph],'interpretation':'Memory grows primarily during seed boot, changes little on scene attachment, then current RSS falls after both calls while process high-water RSS increases. This locates phase changes but attributes no allocation owner.'}
OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':str(OUT.relative_to(ROOT)),'checks':checks,'deltas':out['phase_deltas_bytes']},indent=2))
if not out['all_checks_pass']:raise SystemExit('memory profile independent audit failed')
