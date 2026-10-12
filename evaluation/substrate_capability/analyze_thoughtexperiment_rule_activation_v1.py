#!/usr/bin/env python3
"""Independent gate checks for the rule-activation capture."""
import json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_rule_activation_v1_lock_20261003.json'
RAW=ROOT/'evaluation/reports/thoughtexperiment_rule_activation_v1_20261003.json'
OUT=ROOT/'evaluation/reports/thoughtexperiment_rule_activation_v1_analysis_20261003.json'
sys.path.insert(0,str(ROOT/'evaluation/substrate_capability'))
import thoughtexperiment_rule_activation_v1 as runner
lock=json.loads(LOCK.read_text());raw=json.loads(RAW.read_text())
assert runner.frozen()==lock['sources']
assert raw['lock_sha256']==runner.sha(LOCK)
rows=raw['rows']
checks={
 'eight_family_worker_captures':len(rows)==8 and {(r['family'],r['worker']) for r in rows}=={(f,w) for f in ('recurrence','conversation') for w in range(4)},
 'accepted_candidate_repairs_task':all(r['outcome']['correct'] for r in rows),
 'accepted_candidate_installed':all(r['rule_store_changed'] and r['successor_active'] and not r['target_active'] for r in rows),
 'stale_revision_refused_without_rule_change':all(r['controls']['stale_rejected'] and r['controls']['stale_unchanged'] for r in rows),
 'malformed_candidate_refused_without_rule_change':all(r['controls']['malformed_rejected'] and r['controls']['malformed_unchanged'] for r in rows),
 'source_hashes_stable':runner.frozen()==raw['sources'] and raw['sources']==lock['sources']}
analysis={'schema':'ThoughtexperimentRuleActivationV1Analysis','checks':checks,'passed':sum(checks.values()),'total':len(checks),
 'medians_ms':{'activation':statistics.median(r['activation_ns'] for r in rows)/1e6,
 'post_activation_execution':statistics.median(r['execution_ns'] for r in rows)/1e6},
 'limits':['two authored task families and four workers each','fault, candidate class, selection label and task oracle are supplied by harness',
 'activation mutates only fresh experimental substrates','does not establish autonomous authorization, persistent utility or concurrent policy']}
OUT.write_text(json.dumps(analysis,indent=2,sort_keys=True)+'\n')
print(json.dumps(analysis,indent=2,sort_keys=True))
if not all(checks.values()): raise SystemExit(1)
