#!/usr/bin/env python3
"""Post-hoc target-blind query-utility analysis over v3 sealed captures."""
from __future__ import annotations
import hashlib,json,statistics
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CAPTURE=ROOT/'evaluation/reports/native_candidate_adequacy_v3_20261005.json'
ANALYSIS=ROOT/'evaluation/reports/native_candidate_adequacy_v3_analysis_20261005.json'
SCRIPT=Path(__file__).resolve();OUT=ROOT/'evaluation/reports/native_candidate_adequacy_probe_utility_v1_20261005.json'
BUDGETS=(1,2,4,8)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
 raw=json.loads(CAPTURE.read_text());analysis=json.loads(ANALYSIS.read_text())
 by_worker={(r['task'],r['worker']):r for r in analysis['per_panel']}
 summaries={mode:{b:Counter() for b in BUDGETS} for mode in ('candidate_positive','uniform')};rows=[]
 for w in raw['workers']:
  p=w['panel'];task=p['task_for_scorer_only'];worker=p['worker'];a=by_worker[(task,worker)];chosen=a['selected']
  if chosen is None:continue
  tests=[e for e in w['examples'] if e['split']=='test']
  seed=f'native-candidate-adequacy-probe-utility-v1:replicate:{worker}'
  rank=lambda e:hashlib.sha256((seed+':'+json.dumps(e['row'],separators=(',',':'))).encode()).hexdigest()
  modes={'candidate_positive':[e for e in tests if e['predictions'][chosen] is True],'uniform':tests}
  panel={'task':task,'worker':worker,'selected_candidate':chosen,'selected_correctly':chosen==task}
  for mode,pool in modes.items():
   ordered=sorted(pool,key=rank)
   for budget in BUDGETS:
    query=ordered[:budget];hits=sum(e['predictions'][chosen] is not e['label'] for e in query)
    s=summaries[mode][budget];s['candidate_selected_panels']+=1;s['queries']+=len(query);s['panels_with_counterexample']+=int(hits>0);s['counterexamples_found']+=hits
    s['eligible_pool_rows']+=len(pool);s['eligible_counterexample_rows']+=sum(e['predictions'][chosen] is not e['label'] for e in pool)
    if task in ('additive','product'):
     s['control_panels']+=1;s['control_panels_with_false_help']+=int(hits>0)
    elif task=='opposition':
     s['opposition_panels']+=1;s['opposition_panels_with_counterexample']+=int(hits>0)
    panel.setdefault(mode,{})[str(budget)]={'eligible_rows':len(pool),'candidate_counterexample_rows':sum(e['predictions'][chosen] is not e['label'] for e in pool),'queries':len(query),'counterexamples_found':hits,'help_triggered':hits>0}
  rows.append(panel)
 report={'schema':'NativeCandidateAdequacyProbeUtilityV1Exploratory','capture_sha256':sha(CAPTURE),'base_analysis_sha256':sha(ANALYSIS),'analyzer_sha256':sha(SCRIPT),'budgets':list(BUDGETS),'query_seed_policy':'replicate-index only; task identifier excluded','target_identity_used_in_query_ranking':False,'policy':'For each baseline-selected candidate, hash-rank held-out inputs without labels. Compare all rows with rows where the selected candidate predicts true. A queried candidate/label mismatch is a counterexample and triggers help. Labels are consulted only after each deterministic query set is fixed.','per_policy':{mode:{str(b):dict(c) for b,c in vals.items()} for mode,vals in summaries.items()},'panels':rows,'interpretation_limit':'Post-hoc exploratory reuse of v3 captures; not confirmatory because query budgets and policies were specified after the v3 outcomes. Existing held-out labels support utility estimation only. A fresh preregistered cohort is required.'}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':OUT.relative_to(ROOT).as_posix(),'candidate_positive':report['per_policy']['candidate_positive'],'uniform':report['per_policy']['uniform']}));return 0
if __name__=='__main__':raise SystemExit(main())
