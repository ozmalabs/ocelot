#!/usr/bin/env python3
"""Independent integrity/factor analysis for the full-seed describe-rule scale panel."""
import json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/describe_rule_full_seed_candidate_scale_v1_20260927.json'
OUT=ROOT/'evaluation/reports/describe_rule_full_seed_candidate_scale_v1_analysis_20260927.json'
RULES={'recognise_a_counter','recognise_a_thing_that_stays_put','recognise_a_thing_that_moves_itself'}
def main():
 p=json.loads(RAW.read_text());runs=p['runs'];cells=[(1,0),(1,4096),(4,0),(4,4096)]
 checks={'eight_unique_workers':len(runs)==8 and len({r.get('pid') for r in runs})==8,
 'two_per_factorial_cell':all(sum(r.get('scene_count')==s and r.get('distractor_count')==d for r in runs)==2 for s,d in cells),
 'locked_inputs_match':p['post_run_inputs']==p['locked_inputs'] and all(r.get('source_stable') and r.get('worker_inputs_before')==p['locked_inputs']==r.get('worker_inputs_after') for r in runs),
 'all_workers_fixedpoint_and_exact_outputs':all(r.get('worker_returncode')==0 and r['settle_report']['status']=='fixed_point' and r['classification_exact'] and r['no_distractor_classification'] for r in runs),
 'full_seed_boot_replicates':all(r['boot_loaded']==731 and r['boot_failure_count']==11 for r in runs),
 'only_three_rules_active':all(len(r['active_rule_names_after_tombstone'])==3 and set(r['active_rule_names_after_tombstone'])==RULES for r in runs),
 'one_target_each':all(r['baseline_graph_counts']['target_concept_counts']=={k:1 for k in ('a_counter','a_thing_that_stays_put','a_thing_that_moves_itself')} for r in runs),
 'background_graph_constant':len({json.dumps(r['baseline_graph_counts'],sort_keys=True) for r in runs})==1}
 # Check cross-worker candidate-count reconciliation and derive an empirical formula.
 base_members=runs[0]['baseline_graph_counts']['has_concept_memberships'];per_worker=[]
 for r in runs:
  per={}
  for x in r['per_rule_audit']:
   per.setdefault(x['rule_name'],{})[x['metric']]=x['count']
  c=r['final_has_concept_memberships'];s=r['scene_count']
  candidate_formula={name:counts.get('candidate_pairs')==s*(c+3) for name,counts in per.items() if name in RULES}
  per_worker.append({'scenes':s,'percepts':3*s,'distractors':r['distractor_count'],'memberships':c,
   'per_rule':{name:{'candidate_pairs':per.get(name,{}).get('candidate_pairs'),'term_evaluations':per.get(name,{}).get('term_evaluations')} for name in sorted(RULES)},
   'empirical_candidate_formula_match':len(candidate_formula)==3 and all(candidate_formula.values())})
 checks['rule_candidate_counts_reconcile']=all(x['empirical_candidate_formula_match'] for x in per_worker)
 summary=[]
 for s,d in cells:
  group=[r for r in runs if r['scene_count']==s and r['distractor_count']==d]
  all_cp=[sum(x['count'] for x in r['per_rule_audit'] if x['metric']=='candidate_pairs') for r in group]
  all_te=[sum(x['count'] for x in r['per_rule_audit'] if x['metric']=='term_evaluations') for r in group]
  by_rule={}
  for name in sorted(RULES):
   rs=[]
   for r in group:
    vals={x['metric']:x['count'] for x in r['per_rule_audit'] if x['rule_name']==name}
    rs.append({'candidate_pairs':vals.get('candidate_pairs'),'term_evaluations':vals.get('term_evaluations')})
   by_rule[name]={'replicate_counts':rs,'candidate_pairs_median':int(statistics.median(x['candidate_pairs'] for x in rs)),
                  'term_evaluations_median':int(statistics.median(x['term_evaluations'] for x in rs))}
  summary.append({'scenes':s,'percepts':3*s,'distractors':d,'concept_memberships':group[0]['final_has_concept_memberships'],'replicates':len(group),
   'total_candidate_pairs_median':int(statistics.median(all_cp)),'total_term_evaluations_median':int(statistics.median(all_te)),
   'audited_closure_wall_ms_median':statistics.median(r['wall_ns'] for r in group)/1e6,
   'audited_closure_cpu_ms_median':statistics.median(r['cpu_ns'] for r in group)/1e6,
   'boot_wall_ms_median':statistics.median(r['boot_wall_ns'] for r in group)/1e6,
   'faculty_wall_ms_median':statistics.median(r['faculty_wall_ns'] for r in group)/1e6,
   'per_rule':by_rule})
 report={'schema_version':1,'raw_report':str(RAW.relative_to(ROOT)),'checks':checks,'all_checks_pass':all(checks.values()),
  'base_graph':runs[0]['baseline_graph_counts'],'summary_by_cell':summary,'per_worker_formula_audit':per_worker,
  'observed_candidate_count_identity':'For these cells, each target rule reports candidate_pairs = S * (M + 3), where S is the number of 3-Percept Scenes and M is total has_concept memberships after adding distractors. This is a descriptive identity of the measured fixtures, not a general engine theorem.',
  'claim_boundary':'Full-seed graph and real faculty source, with only three target rules active during measured closure. Other rules are tombstoned; this is not full-route closure or natural workload scaling.'}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps({'analysis':str(OUT.relative_to(ROOT)),'checks':checks,'summary_by_cell':[{'scenes':x['scenes'],'distractors':x['distractors'],'memberships':x['concept_memberships'],'candidates':x['total_candidate_pairs_median'],'terms':x['total_term_evaluations_median'],'wall_ms':x['audited_closure_wall_ms_median']} for x in summary]},indent=2))
 if not report['all_checks_pass']:raise SystemExit(1)
if __name__=='__main__':main()
