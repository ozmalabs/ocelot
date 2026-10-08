#!/usr/bin/env python3
"""Independent outcome and source-lock checks for persistent adoption."""
import json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_persistent_adoption_v1_lock_20261003.json'
RAW=ROOT/'evaluation/reports/thoughtexperiment_persistent_adoption_v1_20261003.json'
OUT=ROOT/'evaluation/reports/thoughtexperiment_persistent_adoption_v1_analysis_20261003.json'
sys.path.insert(0,str(ROOT/'evaluation/substrate_capability'))
import thoughtexperiment_persistent_adoption_v1 as runner
lock=json.loads(LOCK.read_text());raw=json.loads(RAW.read_text());rows=raw['rows']
assert runner.frozen()==lock['sources']
assert raw['sources']==lock['sources']
assert raw['lock_sha256']==runner.sha(LOCK)
persistent=[r for r in rows if r['family'] in ('recurrence','conversation')]
rollbacks=[r for r in rows if r['family']=='rollback']
checks={
 'eight_two_batch_same_substrate_runs':len(persistent)==8 and all(r['same_substrate'] for r in persistent),
 'selected_repairs_work_in_both_batches':all(r['first']['correct'] and r['second']['correct'] for r in persistent),
 'all_four_regression_triggers_fail':len(rollbacks)==4 and all(r['failure_detected'] for r in rollbacks),
 'all_four_rollbacks_restore_source_and_recover':all(r['rollback_succeeded'] and r['source_rule_active'] and r['recovered']['correct'] for r in rollbacks),
 'source_lock_stable':runner.frozen()==raw['sources']==lock['sources']}
analysis={'schema':'ThoughtexperimentPersistentAdoptionV1Analysis','checks':checks,'passed':sum(checks.values()),'total':len(checks),
 'medians_ms':{'selected_activation':statistics.median(r['activation_ns'] for r in persistent)/1e6,
  'rollback':statistics.median(r['rollback_ns'] for r in rollbacks)/1e6},
 'limitations':['two authored task families and four workers per family','fault, candidate choice and task oracle are harness supplied',
  'rollback trigger is an observed failure on a deliberately known-bad candidate','no autonomous trigger threshold or long-run natural workload']}
OUT.write_text(json.dumps(analysis,indent=2,sort_keys=True)+'\n')
print(json.dumps(analysis,indent=2,sort_keys=True))
if not all(checks.values()):raise SystemExit(1)
