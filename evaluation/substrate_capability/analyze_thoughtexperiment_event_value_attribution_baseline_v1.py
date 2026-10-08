#!/usr/bin/env python3
"""Independent validation of event-value attribution baseline capture."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];CAPTURE=ROOT/'evaluation/reports/thoughtexperiment_event_value_attribution_baseline_v1_20261005.json';LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_event_value_attribution_baseline_v1_lock_20261005.json';RUNNER=ROOT/'evaluation/substrate_capability/thoughtexperiment_event_value_attribution_baseline_v1.py';ANALYZER=Path(__file__).resolve()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 before=sha(ANALYZER);capture=json.loads(CAPTURE.read_text());lock=json.loads(LOCK.read_text());workers=capture['workers'];pids=[w['pid'] for w in workers]
 checks={'lock_matches_capture':capture['lock_sha256']==sha(LOCK),'source_lock_stable':all(w['sources_before']==w['sources_after']==lock['sources'] for w in workers),'runner_hash_matches_lock':lock['sources']['files']['evaluation/substrate_capability/thoughtexperiment_event_value_attribution_baseline_v1.py']==sha(RUNNER),'analyzer_hash_matches_lock':lock['sources']['files']['evaluation/substrate_capability/analyze_thoughtexperiment_event_value_attribution_baseline_v1.py']==before,'three_distinct_workers':len(workers)==3 and len(set(pids))==3,'worker_capture_rows_identical':all(w['fixtures']==workers[0]['fixtures'] for w in workers[1:]),'independent_analyzer_stable':before==sha(ANALYZER)}
 fixtures=workers[0]['fixtures'];names={f['fixture'] for f in fixtures};checks['direct_and_deferred_fixtures_present']=names=={'direct','deferred'}
 all_unique=True;all_modes=True;events_not_dropped=True;expected_events={'direct_writer','trans_frame_identity_assignment','trace_direct_control'}
 observed=set()
 for fixture in fixtures:
  summaries=fixture['summaries'];all_modes &= len({(v['status'],v['progress_steps'],v['passes_completed']) for v in summaries.values()})==1
  events=fixture['events'];observed|={e['rule_name'] for e in events};events_not_dropped &= fixture['dropped_events']==0
  changes=fixture['changes'];assignments=fixture['assignments']
  all_unique &= len(assignments)==len(changes) and all(a['change']==c for a,c in zip(assignments,changes)) and all(a['status']=='unique' and len(a['candidate_event_indices'])==1 for a in assignments)
 checks['ordinary_traced_and_exact_parity']=bool(all_modes);checks['each_changed_field_has_one_progressed_event']=bool(all_unique);checks['no_events_dropped']=bool(events_not_dropped);checks['expected_direct_and_deferred_writers_observed']=expected_events<=observed
 out={'schema':'ThoughtexperimentEventValueAttributionBaselineV1Analysis','capture_sha256':sha(CAPTURE),'lock_sha256':sha(LOCK),'checks':checks,'passed':all(checks.values()),'summary':{'workers':len(workers),'distinct_pids':len(set(pids)),'fixtures':len(fixtures),'changed_fields':sum(len(f['changes']) for f in fixtures),'uniquely_attributed_fields':sum(sum(a['status']=='unique' for a in f['assignments']) for f in fixtures),'ambiguous_fields':sum(sum(a['status']=='ambiguous' for a in f['assignments']) for f in fixtures),'uncovered_fields':sum(sum(a['status']=='uncovered' for a in f['assignments']) for f in fixtures),'observed_writers':sorted(observed)},'claim_limit':'external whole-settlement snapshots and current per-rule target events support uniquely matched field deltas only in these fixtures; not native per-firing before-images, ordered overlap attribution, causal necessity, diagnosis, or general self-repair.'}
 outpath=ROOT/'evaluation/reports/thoughtexperiment_event_value_attribution_baseline_v1_analysis_20261005.json';outpath.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':out['passed'],'checks':checks,'summary':out['summary']}));return 0 if out['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
