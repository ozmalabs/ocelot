#!/usr/bin/env python3
"""Independent integrity and linear-work analysis for describe-rule candidate scale v1."""
import json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/describe_rule_concept_candidate_scale_v1_20260927.json'
OUT=ROOT/'evaluation/reports/describe_rule_concept_candidate_scale_v1_analysis_20260927.json'
RULES={'recognise_a_counter','recognise_a_thing_that_stays_put','recognise_a_thing_that_moves_itself'}
def main():
 p=json.loads(RAW.read_text());runs=p['runs'];sizes=(0,64,256,1024,4096)
 checks={'15_workers':len(runs)==15,'unique_pids':len({r.get('pid') for r in runs})==15,
 '3_replicates_each':all(sum(r.get('distractor_count')==n for r in runs)==3 for n in sizes),
 'locked_inputs_stable':p['post_run_inputs']==p['locked_inputs'] and all(r.get('source_stable') and r.get('worker_inputs_before')==p['locked_inputs']==r.get('worker_inputs_after') for r in runs),
 'all_returned_and_fixedpoint':all(r.get('worker_returncode')==0 and r['settle_report']['status']=='fixed_point' for r in runs),
 'exact_classification_parity':all(r['exact_positive_classification'] and len(r['actual_edges'])==3 and r['actual_edges']==r['expected_edges'] for r in runs)}
 formulas=[]
 for r in runs:
  by_rule={}
  for row in r['per_rule_audit']:by_rule.setdefault(row['rule_name'],{})[row['metric']]=row['count']
  c=r['concept_population'];complete=set(by_rule)==RULES and all(by_rule[name].get('candidate_pairs')==c+3 and by_rule[name].get('term_evaluations')==4*c+18 for name in RULES)
  formulas.append({'distractors':r['distractor_count'],'concept_population':c,'replicate':r['replicate'],'per_rule_counts':{name:{'candidate_pairs':by_rule.get(name,{}).get('candidate_pairs'),'term_evaluations':by_rule.get(name,{}).get('term_evaluations')} for name in sorted(RULES)},'formula_matches':complete})
 checks['per_rule_linear_formula_all_workers']=all(x['formula_matches'] for x in formulas)
 summary=[]
 for n in sizes:
  group=[r for r in runs if r['distractor_count']==n];c=n+3
  candidates=[sum(x['count'] for x in r['per_rule_audit'] if x['metric']=='candidate_pairs') for r in group]
  terms=[sum(x['count'] for x in r['per_rule_audit'] if x['metric']=='term_evaluations') for r in group]
  summary.append({'distractors':n,'concept_population':c,'replicates':len(group),'candidate_pairs_per_worker':candidates,'term_evaluations_per_worker':terms,
   'candidate_pairs_median':int(statistics.median(candidates)),'term_evaluations_median':int(statistics.median(terms)),
   'wall_ms_median':statistics.median(r['wall_ns'] for r in group)/1e6,'cpu_ms_median':statistics.median(r['cpu_ns'] for r in group)/1e6,
   'peak_rss_bytes_median':int(statistics.median(r['peak_rss_bytes'] for r in group))})
 result={'schema_version':1,'raw_report':str(RAW.relative_to(ROOT)),'checks':checks,'all_checks_pass':all(checks.values()),'summary_by_size':summary,'per_rule_formula':{'candidate_pairs':'C + 3','term_evaluations':'4*C + 18','C':'total Concepts in the Microtheory, including the three positive target Concepts'},'claim_boundary':'Independent per-worker formula confirmation for three source-derived recognition rules, one Scene with three Percepts, and synthetic negative distractors through C=4,099. Does not model repeated full-seed closure, other Microtheories, all six recognition rules, or natural vocabulary distributions.'}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'analysis':str(OUT.relative_to(ROOT)),'checks':checks,'summary_by_size':summary},indent=2))
 if not result['all_checks_pass']:raise SystemExit(1)
if __name__=='__main__':main()
