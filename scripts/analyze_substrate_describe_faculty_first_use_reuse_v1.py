#!/usr/bin/env python3
"""Independent summary for the locked first-use/reuse capture."""
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/describe_faculty_first_use_reuse_v1_1_20260927.json'
OUT=ROOT/'evaluation/reports/describe_faculty_first_use_reuse_v1_1_analysis_20260927.json'
LOCK=ROOT/'evaluation/substrate_capability/describe_faculty_first_use_reuse_v1_1_lock_20260927.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def seconds(ns):return ns/1e9
def stats(vals):return {'median':statistics.median(vals),'min':min(vals),'max':max(vals),'replicates':vals}
def analyze():
 d=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text())['locked_inputs']; checks=dict(d['checks'])
 checks['raw_lock_matches_registry']=d['locked_inputs']==lock
 checks['source_closure_matches_capture']=d['locked_inputs']['runtime_inputs']['runtime_inputs']['source_sha256']['world_adapter']=='517cec9914d600ca4572fbc96436f5319f6d60d2ef3f0903ee921c25d7b9cb12'
 arms={}
 for arm in ('lazy','prebuilt'):
  rs=[r for r in d['runs'] if r['arm']==arm]
  metrics={'boot_wall_s':stats([seconds(r['boot_wall_ns']) for r in rs]),'boot_cpu_s':stats([seconds(r['boot_process_cpu_ns']) for r in rs]),
   'request_1_wall_s':stats([seconds(r['requests'][0]['wall_ns']) for r in rs]),'request_1_cpu_s':stats([seconds(r['requests'][0]['process_cpu_ns']) for r in rs]),
   'request_2_wall_s':stats([seconds(r['requests'][1]['wall_ns']) for r in rs]),'request_2_cpu_s':stats([seconds(r['requests'][1]['process_cpu_ns']) for r in rs]),
   'peak_rss_gib':stats([r['peak_rss_bytes']/2**30 for r in rs]),'rss_after_phase_gib':stats([next(p['memory']['VmRSS'] for p in r['phases'] if p['phase']==('after_scene' if arm=='lazy' else 'after_prebuild'))/2**30 for r in rs]),
   'request_new_rules':[[x['new_rules'] for x in r['requests']] for r in rs]}
  if arm=='prebuilt':metrics.update({'faculty_setup_wall_s':stats([seconds(r['faculty_setup']['wall_ns']) for r in rs]),'faculty_setup_cpu_s':stats([seconds(r['faculty_setup']['process_cpu_ns']) for r in rs]),'faculty_setup_rule_deltas':[r['faculty_setup']['rule_count_after']-r['phases'][2]['rule_count'] for r in rs]})
  arms[arm]=metrics
 checks['all_independent_gates_pass']=all(checks.values())
 out={'schema_version':1,'raw_sha256':sha(RAW),'lock_sha256':sha(LOCK),'checks':checks,'all_checks_pass':all(checks.values()),'by_arm':arms,
  'derived_comparison':{'lazy_first_request_wall_median_s':arms['lazy']['request_1_wall_s']['median'],'prebuild_plus_first_request_wall_median_s':arms['prebuilt']['faculty_setup_wall_s']['median']+arms['prebuilt']['request_1_wall_s']['median'],'prebuilt_plus_first_request_cpu_median_s':arms['prebuilt']['faculty_setup_cpu_s']['median']+arms['prebuilt']['request_1_cpu_s']['median']},
  'claim_boundary':'The explicit setup and lazy request are different timing boundaries. Their summed medians are descriptive and are not paired within the same process. This route fixture does not establish task prevalence, rule necessity, or scaling.'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'output':str(OUT.relative_to(ROOT)),'checks':checks,'medians':{k:{name:v['median'] for name,v in arm.items() if isinstance(v,dict) and 'median' in v} for k,arm in arms.items()}},indent=2))
 if not out['all_checks_pass']:raise SystemExit('independent analysis gates failed')
if __name__=='__main__':analyze()
