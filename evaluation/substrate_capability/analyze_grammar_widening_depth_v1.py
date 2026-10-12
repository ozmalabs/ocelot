#!/usr/bin/env python3
"""Independent source, panel, setting, and fractional-holdout replay."""
import hashlib,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'evaluation/substrate_capability'))
import grammar_widening_depth_v1 as runner
from substrate_rs import _native
LOCK=ROOT/'evaluation/substrate_capability/grammar_widening_depth_v1_lock_20261003.json';RAW=ROOT/'evaluation/reports/grammar_widening_depth_v1_20261003.json';OUT=ROOT/'evaluation/reports/grammar_widening_depth_v1_analysis_20261003.json'
lock=json.loads(LOCK.read_text());raw=json.loads(RAW.read_text());native=_native.Substrate();
assert runner.source_map()==lock['sources']==raw['sources']
assert raw['lock_sha256']==hashlib.sha256(LOCK.read_bytes()).hexdigest()
prior=json.loads(runner.PANEL_LOCK.read_text());expected=[p for p in prior['panels'] if p['task'] in runner.TASKS]
coverage=len(raw['workers'])==10 and len(lock['panels'])==10
coverage &= [(w['task'],w['worker'],w['training'],w['selection_pool']) for w in raw['workers']]==[(p['task'],p['worker'],p['training'],p['selection_pool']) for p in expected]
settings=True;scores=True;by={t:{str(k):{'panels':0,'exact_candidate_panels':0,'timeout_panels':0,'candidate_count':0,'median_wall_s':0,'median_cpu_s':0,'exact_candidates':0} for k in runner.SIZES} for t in runner.TASKS};cost={t:{k:[] for k in runner.SIZES} for t in runner.TASKS}
for w in raw['workers']:
 for arm in w['arms']:
  k=arm['max_size'];task=w['task'];summary=by[task][str(k)];summary['panels']+=1;summary['timeout_panels']+=int(arm['halt_reason']=='timeout');summary['candidate_count']+=len(arm['hypotheses']);cost[task][k].append((arm['wall_ns']/1e9,arm['cpu_ns']/1e9))
  settings &= k in runner.SIZES and tuple(arm['ops'])==runner.OPS[task] and arm['timeout_s']==runner.TIMEOUT
  exact=0
  for h in arm['hypotheses']:
   s=runner.score(native,task,h['term']);scores &= s==h['heldout'];exact+=int(s['exact'])
  summary['exact_candidates']+=exact;summary['exact_candidate_panels']+=int(exact>0)
for t in runner.TASKS:
 for k in runner.SIZES:
  a=by[t][str(k)];a['median_wall_s']=statistics.median(x[0] for x in cost[t][k]);a['median_cpu_s']=statistics.median(x[1] for x in cost[t][k])
checks={'ten_locked_panels_replayed':bool(coverage),'two_grammar_arms_and_fixed_settings':bool(settings),'all_candidate_holdouts_rescored':bool(scores),'source_lock_and_capture_binding':runner.source_map()==raw['sources']==lock['sources'] and raw['lock_sha256']==hashlib.sha256(LOCK.read_bytes()).hexdigest()}
analysis={'schema':'GrammarWideningDepthV1Analysis','checks':checks,'passed':sum(checks.values()),'total':len(checks),'by_task_and_size':by,'interpretation':'Task-informed primitive widening recovers an exact model only when the bounded search finds it; this does not measure autonomous primitive selection. Compare recovery, timeout, and cost across the frozen panels.','limits':['two harness-authored numeric target families','operator hint is supplied from target task identity','five frozen panels per family','finite fractional holdout and one host','partial search results may occur before timeout']}
OUT.write_text(json.dumps(analysis,indent=2,sort_keys=True)+'\n');print(json.dumps(analysis,indent=2,sort_keys=True))
if not all(checks.values()):raise SystemExit(1)
