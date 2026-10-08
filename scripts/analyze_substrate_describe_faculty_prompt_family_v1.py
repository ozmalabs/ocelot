#!/usr/bin/env python3
"""Independent route/capability analysis of the prompt-family capture."""
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/describe_faculty_prompt_family_v1_20260927.json'
LOCK=ROOT/'evaluation/substrate_capability/describe_faculty_prompt_family_v1_lock_20260927.json'
OUT=ROOT/'evaluation/reports/describe_faculty_prompt_family_v1_analysis_20260927.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 d=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text())['locked_inputs'];runs=d['runs']
 checks={'ten_workers_present':len(runs)==10,'ten_unique_processes':len({r.get('pid') for r in runs})==10,'all_source_locks_stable':all(r.get('source_stable') and r.get('locked_inputs')==lock==r.get('post_run_inputs') for r in runs),'all_full_seed_boots_loaded':all(r.get('boot_loaded',0)>0 for r in runs),'capture_parent_lock_stable':d['post_run_inputs']==d['locked_inputs']==lock}
 by_condition={}
 for name in ('canonical','tell_see','describe_scene','report_observe','self_identity_control'):
  rs=[r for r in runs if r.get('condition')==name]
  per=[]
  for r in rs:
   per.append({'replicate':r['replicate'],'final_routes':[a.get('route') for a in r.get('action_observations',[])],
    'scene_handler_calls':len(r.get('scene_route_calls',[])),'faculty_calls':len(r.get('ensure_calls',[])),
    'faculty_rule_deltas':[x['new_rules'] for x in r.get('ensure_calls',[])], 'request_rule_delta':r.get('request_rule_delta'),
    'reply':r.get('reply'),'goal_kinds':[g.get('kind') for g in r.get('goals',[])],
    'resolved_lifecycle':all(g.get('status')=='resolved' and g.get('events')==['selection','execution','action_result'] for g in r.get('goals',[])),
    'scene_colours_present':all(c in (r.get('reply') or '').lower() for c in ('grey','yellow','blue')),
    'request_wall_s':r.get('request_wall_ns',0)/1e9,'request_cpu_s':r.get('request_process_cpu_ns',0)/1e9,
    'peak_rss_gib':r.get('peak_rss_bytes',0)/2**30})
  lat=[x['request_wall_s'] for x in per]
  by_condition[name]={'replicate_count':len(rs),'workers':per,'median_request_wall_s':statistics.median(lat) if lat else None,
    'observed_final_routes':sorted({route for x in per for route in x['final_routes']}),
    'faculty_construction_in_all_replicates':bool(rs) and all(x['faculty_calls']==1 and x['faculty_rule_deltas']==[18] for x in per),
    'semantic_scene_gate_in_all_replicates':bool(rs) and all(x['scene_colours_present'] and x['goal_kinds']==['describe_scene'] and x['resolved_lifecycle'] for x in per)}
 checks['canonical_capability_replicates_pass']=by_condition['canonical']['semantic_scene_gate_in_all_replicates'] and by_condition['canonical']['faculty_construction_in_all_replicates']
 checks['paraphrase_capability_replicates_pass']=all(by_condition[k]['semantic_scene_gate_in_all_replicates'] for k in ('tell_see','describe_scene','report_observe'))
 checks['self_report_control_avoids_describe_faculty']=all(not x['faculty_calls'] and not x['scene_handler_calls'] and x['final_routes']==['self_report'] and x['goal_kinds']==['report_self'] and x['resolved_lifecycle'] for x in by_condition['self_identity_control']['workers'])
 out={'schema_version':1,'raw_sha256':sha(RAW),'lock_sha256':sha(LOCK),'integrity_checks':checks,'integrity_pass':all(checks[k] for k in ('ten_workers_present','ten_unique_processes','all_source_locks_stable','all_full_seed_boots_loaded','capture_parent_lock_stable')),
  'capability_gate_pass':checks['canonical_capability_replicates_pass'] and checks['paraphrase_capability_replicates_pass'] and checks['self_report_control_avoids_describe_faculty'],'by_condition':by_condition,
  'interpretation':'The source-stratified panel fails its preregistered paraphrase capability gate. Two paraphrases enter the describe handler and construct faculty, but then fall through to self_report; the remaining paraphrase receives a gap reply without entering the handler. The control avoids describe-faculty construction but ordinary closure adds six rules, so total request rule delta is not a valid proxy for faculty minting.'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'output':str(OUT.relative_to(ROOT)),'integrity_pass':out['integrity_pass'],'capability_gate_pass':out['capability_gate_pass'],'by_condition':{k:{'routes':v['observed_final_routes'],'faculty_built':v['faculty_construction_in_all_replicates'],'semantic_pass':v['semantic_scene_gate_in_all_replicates'],'median_request_wall_s':v['median_request_wall_s']} for k,v in by_condition.items()}},indent=2))
 if not out['integrity_pass']:raise SystemExit('prompt-family capture integrity failure')
if __name__=='__main__':main()
