#!/usr/bin/env python3
"""Independent gate/readback analysis for global per-rule paired workers."""
import hashlib,json,random,statistics
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/substrate_problem_shape_global_rule_attribution_20260925.json'
LOCK=ROOT/'evaluation/substrate_capability/problem_shape_global_rule_attribution_lock_20260925.json'
OUT=ROOT/'evaluation/reports/substrate_problem_shape_global_rule_attribution_analysis_20260925.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rule_totals(worker):
 out=defaultdict(int)
 for row in worker['records']:
  for x in row['all_rule_scale_audit']:
   out[(x['rule_name'],x['metric'])]+=int(x['count'])
 return out
def pct(v):
 if not v:return None
 if len(v)==1:return v[0]
 return v[min(len(v)-1,int(.025*len(v)))],v[min(len(v)-1,int(.975*len(v)))]
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text())
 if raw['provenance']['lock_sha256']!=sha(LOCK) or raw['provenance']['locked_inputs']!=lock:raise SystemExit('input lock mismatch')
 if lock['runner']!=sha(ROOT/'scripts/substrate_problem_shape_global_rule_attribution.py'):raise SystemExit('runner hash mismatch')
 if len(raw['pairs'])!=12 or not raw['all_gates_pass'] or not raw['unique_process_ids']:raise SystemExit('raw top-level gates fail')
 pids=[]; result={}
 for mix in ('recognition','recurrent_residual'):
  pairs=[p for p in raw['pairs'] if p['mix']==mix]
  if len(pairs)!=6 or not all(p['semantic_parity'] for p in pairs):raise SystemExit(f'{mix}: pair/semantic gate fail')
  orders={'baseline_first':sum(p['order'][0]=='baseline' for p in pairs),'candidate_first':sum(p['order'][0]=='candidate' for p in pairs)}
  if orders!={'baseline_first':3,'candidate_first':3}:raise SystemExit(f'{mix}: order balance fail')
  ratios=[p['wall_ratio'] for p in pairs];rng=random.Random(20260927+(0 if mix=='recognition' else 1));boots=[]
  for _ in range(50000):boots.append(statistics.median(rng.choice(ratios) for _ in ratios))
  boots.sort(); workers={a:[] for a in ('baseline','candidate')}; totals={a:[] for a in ('baseline','candidate')}; rule_runs={a:[] for a in ('baseline','candidate')}
  for pair in pairs:
   for arm,w in pair['arms'].items():
    pids.append(w['process_id']);workers[arm].append(w);totals[arm].append(w['global_scale_audit']);rule_runs[arm].append(rule_totals(w))
  all_keys=set().union(*(d.keys() for arm in rule_runs.values() for d in arm))
  per_rule={}
  for pair in pairs:
   if pair['arms']['baseline']['global_scale_audit']['rule_enumerations']!=pair['arms']['candidate']['global_scale_audit']['rule_enumerations']:
    raise SystemExit(f'{mix}: paired rule enumeration mismatch')
  for rule,metric in sorted(all_keys):
   per_rule.setdefault(rule,{})[metric]={}
   for arm in ('baseline','candidate'):
    vals=[d.get((rule,metric),0) for d in rule_runs[arm]]
    per_rule[rule][metric][arm]=statistics.median(vals)
    per_rule[rule][metric][arm+'_stable']=len(set(vals))==1
   per_rule[rule][metric]['delta_candidate_minus_baseline']=per_rule[rule][metric]['candidate']-per_rule[rule][metric]['baseline']
  global_sums={}
  for key in ('term_evals_total','cand_tested','rule_enumerations','where_evals','graph_writes','term_units_total'):
   b=[x[key] for x in totals['baseline']];c=[x[key] for x in totals['candidate']]
   if key!='rule_enumerations' and (len(set(b))!=1 or len(set(c))!=1):raise SystemExit(f'{mix}: global counter {key} not stable')
   if key=='rule_enumerations' and (max(b)-min(b)>32 or max(c)-min(c)>32):raise SystemExit(f'{mix}: rule-enumeration variation exceeds one per observation')
   bv,cv=statistics.median(b),statistics.median(c)
   global_sums[key]={'baseline_median':bv,'candidate_median':cv,'baseline_range':[min(b),max(b)],'candidate_range':[min(c),max(c)],'stable_within_arm':len(set(b))==1 and len(set(c))==1,'relative_reduction':(bv-cv)/bv if bv else None}
  ps={}
  for arm in ('baseline','candidate'):
   ps[arm]={'candidate_pairs':sum(d.get((rn,'candidate_pairs'),0) for rn in ('ps_decode','ps_recognize','ps_residual','ps_mint','ps_redecode') for d in rule_runs[arm])//6,
            'term_evaluations':sum(d.get((rn,'term_evaluations'),0) for rn in ('ps_decode','ps_recognize','ps_residual','ps_mint','ps_redecode') for d in rule_runs[arm])//6}
  per_rule_count_stability=all(z.get('baseline_stable',True) and z.get('candidate_stable',True) for metrics in per_rule.values() for metric,z in metrics.items() if metric in ('candidate_pairs','term_evaluations'))
  if not per_rule_count_stability:raise SystemExit(f'{mix}: per-rule candidate/term counters unstable')
  term_deltas=[]
  for rule,metrics in per_rule.items():
   if 'term_evaluations' in metrics:
    x=metrics['term_evaluations'];term_deltas.append({'rule':rule,'baseline':x['baseline'],'candidate':x['candidate'],'delta_candidate_minus_baseline':x['delta_candidate_minus_baseline'],'baseline_stable':x['baseline_stable'],'candidate_stable':x['candidate_stable']})
  term_deltas.sort(key=lambda x:abs(x['delta_candidate_minus_baseline']),reverse=True)
  result[mix]={'pair_count':6,'order_counts':orders,'all_semantic_gates_pass':True,'counter_values_stable_except_rule_enumeration_roundoff':True,'per_rule_work_counts_stable':per_rule_count_stability,'paired_rule_enumeration_counts_match':True,
    'wall_ratio_median':statistics.median(ratios),'wall_ratio_range':[min(ratios),max(ratios)],'wall_ratio_pair_bootstrap_95':[pct(boots)[0],pct(boots)[1]],
    'candidate_faster_pairs':sum(x<1 for x in ratios),'median_cpu_ratio':statistics.median(p['cpu_ratio'] for p in pairs),
    'global_scale_audit':global_sums,'problem_shape_totals':ps,'largest_per_rule_term_evaluation_deltas':term_deltas[:16],'per_rule_audit':per_rule,
    'median_peak_rss_bytes':{a:statistics.median(w['peak_rss_bytes'] for w in workers[a]) for a in workers}}
 if len(pids)!=24 or len(set(pids))!=24:raise SystemExit('PID uniqueness failed')
 out={'schema_version':1,'analysis':'problem-shape-global-rule-attribution-independent-readback','raw_sha256':sha(RAW),'lock_sha256':sha(LOCK),'all_gates_pass':True,'unique_process_ids':True,'summaries_by_mix':result,
 'interpretation_limit':raw['interpretation_limit']}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
