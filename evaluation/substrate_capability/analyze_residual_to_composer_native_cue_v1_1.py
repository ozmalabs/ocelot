#!/usr/bin/env python3
"""Corrected independent analysis for the native residual cue capture."""
from __future__ import annotations
import hashlib,json,statistics,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/residual_to_composer_native_cue_v1_lock_20261003.json'
CAPTURE=ROOT/'evaluation/reports/residual_to_composer_native_cue_v1_20261003.json'
OUT=ROOT/'evaluation/reports/residual_to_composer_native_cue_v1_1_analysis_20261003.json'
RUNNER=ROOT/'evaluation/substrate_capability/measure_residual_to_composer_native_cue_v1.py'
INITIAL_ANALYSIS=ROOT/'evaluation/reports/residual_to_composer_native_cue_v1_analysis_20261003.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 lock=json.loads(LOCK.read_text());data=json.loads(CAPTURE.read_text());rows=data.get('workers',[]);errors=[]
 if data.get('lock_sha256')!=sha(LOCK):errors.append('raw capture does not bind to source lock')
 if data.get('sources')!=lock.get('sources'):errors.append('raw source manifest differs from lock')
 if len(rows)!=len(lock.get('tasks',[])) or len(rows)!=13:errors.append('incomplete worker panel')
 if len({r.get('worker') for r in rows})!=len(rows):errors.append('worker IDs not unique')
 expected={row['id']:row for row in lock['tasks']}
 for r in rows:
  task=r['task'];name=task['id'];positive=task['kind']=='opposite';candidate=r['candidate'];primary=r['primary'];baseline=r['baseline']
  if task!=expected.get(name):errors.append(f'{name}: task differs from lock')
  if not r.get('source_stable'):errors.append(f'{name}: worker source drift')
  if baseline.get('proposal_built'):errors.append(f'{name}: baseline proposed without native cue rule')
  if positive:
   score=candidate.get('heldout_score') or {}
   if not(candidate.get('derived_cue') and candidate.get('native_cue_rule_observed_fired')):
    errors.append(f'{name}: native rule failed to derive cue')
   if not(candidate.get('proposal_built') and candidate.get('operator')=='flip_comparison'
          and candidate.get('target')=='hop_descend_gradient'):
    errors.append(f'{name}: expected graph-composed proposal absent')
   if not(score.get('oracle_pass') and score.get('receipt_verified') and score.get('primary_preserved')):
    errors.append(f'{name}: held-out behavior or score isolation failed')
   if not candidate.get('target_rule_preserved_in_primary') or not primary.get('returned_candidate_present'):
    errors.append(f'{name}: proposal preservation/return failed')
  elif name=='target_absent':
   if not candidate.get('derived_cue'):errors.append(f'{name}: action-relation cue should be derived')
   if candidate.get('proposal_built'):errors.append(f'{name}: proposal emitted without target')
  elif candidate.get('derived_cue') or candidate.get('proposal_built'):
   errors.append(f'{name}: false cue/proposal on negative control')
  if not(candidate.get('branch_changed') and baseline.get('branch_changed')):
   errors.append(f'{name}: expected isolated branch work missing')
  if not(primary.get('unchanged_during_branch') and primary.get('rules_unchanged_during_branch')
         and primary.get('revision_unchanged_during_branch') and primary.get('only_residual_returned')):
   errors.append(f'{name}: primary isolation or compact return failed')
  if primary.get('new_node_ids') != [primary.get('returned_residual_id')]:
   errors.append(f'{name}: primary did not gain exactly the returned residual')
 positive=[r for r in rows if r['task']['kind']=='opposite']
 controls=[r for r in rows if r['task']['kind'] not in ('opposite','absent_target')]
 forks=[(r['baseline']['fork_ns']+r['candidate']['fork_ns'])/1e6 for r in rows]
 summary={'workers':len(rows),'positive_cases':len(positive),'negative_controls':len(controls),
  'absent_target_controls':sum(r['task']['id']=='target_absent' for r in rows),
  'native_positive_cues':sum(bool(r['candidate']['derived_cue']) for r in positive),
  'target_absent_cues':sum(bool(r['candidate']['derived_cue']) for r in rows if r['task']['id']=='target_absent'),
  'false_control_cues':sum(bool(r['candidate']['derived_cue']) for r in controls),
  'heldout_positive_passes':sum(bool((r['candidate'].get('heldout_score') or {}).get('oracle_pass')) for r in positive),
  'false_control_proposals':sum(bool(r['candidate']['proposal_built']) for r in rows if r['task']['kind']!='opposite'),
  'baseline_proposals':sum(bool(r['baseline']['proposal_built']) for r in rows),
  'primary_isolation_and_compact_return':sum(bool(r['primary']['unchanged_during_branch']
      and r['primary']['only_residual_returned']) for r in rows),
  'median_native_induction_ms':statistics.median(r['candidate']['induction_ns'] for r in rows)/1e6,
  'median_candidate_grounding_ms':statistics.median(r['candidate']['grounding_ns'] for r in rows)/1e6,
  'median_raw_baseline_grounding_ms':statistics.median(r['baseline']['grounding_ns'] for r in rows)/1e6,
  'median_two_branch_fork_ms':statistics.median(forks),
  'candidate_branch_rule_delta_range':[min(r['candidate']['branch_rule_count_delta'] for r in rows),
                                         max(r['candidate']['branch_rule_count_delta'] for r in rows)],
  'candidate_branch_node_delta_range':[min(r['candidate']['branch_node_delta'] for r in rows),
                                         max(r['candidate']['branch_node_delta'] for r in rows)]}
 manifest_errors=[]
 for rel,digest in lock['sources']['files'].items():
  p=ROOT/rel
  if not p.exists() or sha(p)!=digest:manifest_errors.append(rel)
 binary=Path(lock['sources']['native_binary']['path'])
 if not binary.exists() or sha(binary)!=lock['sources']['native_binary']['sha256']:
  manifest_errors.append('native_binary')
 if manifest_errors:errors.append('current source lock mismatch: '+', '.join(manifest_errors))
 report={'schema':'ResidualToComposerNativeCueV1_1Analysis','generated_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
  'input_hashes':{'lock_sha256':sha(LOCK),'capture_sha256':sha(CAPTURE),'runner_sha256':sha(RUNNER),
                  'initial_analysis_sha256':sha(INITIAL_ANALYSIS)},
  'gates_pass':not errors,'errors':errors,'summary':summary,
  'analysis_note':'The original v1 analyzer recorded branch fork times in the raw capture but omitted them from its summary, yielding a misleading 0.0 ms field. This v1.1 independent analysis uses the captured baseline and candidate fork_ns values; it does not change the raw capture or behavior criteria.'}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'analysis':OUT.relative_to(ROOT).as_posix(),'gates_pass':report['gates_pass'],
  'errors':errors,'summary':summary},sort_keys=True));return int(bool(errors))
if __name__=='__main__':raise SystemExit(main())
