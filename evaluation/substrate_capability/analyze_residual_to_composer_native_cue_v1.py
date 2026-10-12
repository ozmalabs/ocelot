#!/usr/bin/env python3
"""Independent gates for native residual cue derivation v1."""
from __future__ import annotations
import hashlib,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/residual_to_composer_native_cue_v1_lock_20261003.json'
CAPTURE=ROOT/'evaluation/reports/residual_to_composer_native_cue_v1_20261003.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 lock=json.loads(LOCK.read_text());data=json.loads(CAPTURE.read_text());rows=data.get('workers',[]);errors=[]
 if data.get('lock_sha256')!=sha(LOCK):errors.append('lock hash mismatch')
 if data.get('sources')!=lock.get('sources'):errors.append('capture sources differ from lock')
 if len(rows)!=len(lock.get('tasks',[])):errors.append('worker count mismatch')
 if len({r.get('worker') for r in rows})!=len(rows):errors.append('worker IDs not unique')
 for r in rows:
  t=r['task'];name=t['id'];positive=t['kind']=='opposite';c=r['candidate'];p=r['primary'];b=r['baseline']
  if not r.get('source_stable'):errors.append(f'{name}: source drift')
  if b.get('proposal_built'):errors.append(f'{name}: raw baseline unexpectedly proposed')
  if not b.get('branch_changed'):errors.append(f'{name}: baseline branch did not record induction work')
  if not c.get('branch_changed'):errors.append(f'{name}: candidate branch did not change')
  if not (p.get('unchanged_during_branch') and p.get('rules_unchanged_during_branch')
          and p.get('revision_unchanged_during_branch')):errors.append(f'{name}: primary changed during exploration')
  if not p.get('only_residual_returned'):errors.append(f'{name}: exploratory state leaked during return')
  if len(p.get('new_node_ids',[]))!=1 or p['new_node_ids']!=[p.get('returned_residual_id')]:
   errors.append(f'{name}: primary did not receive exactly one residual')
  if positive:
   score=c.get('heldout_score') or {}
   if not(c.get('derived_cue') and c.get('native_cue_rule_observed_fired')):
    errors.append(f'{name}: native rule did not derive cue')
   if not(c.get('proposal_built') and c.get('operator')=='flip_comparison'
          and c.get('target')=='hop_descend_gradient'):
    errors.append(f'{name}: wrong/no candidate proposal')
   if not(c.get('target_rule_preserved_in_primary') and p.get('returned_candidate_present')):
    errors.append(f'{name}: target or returned-candidate boundary failed')
   if not(score.get('oracle_pass') and score.get('receipt_verified') and score.get('primary_preserved')):
    errors.append(f'{name}: held-out utility/receipt/isolation failed')
  elif name=='target_absent':
   if not c.get('derived_cue'):errors.append(f'{name}: expected cue from residual relation')
   if c.get('proposal_built'):errors.append(f'{name}: proposal emitted without target')
   if not c.get('target_rule_preserved_in_primary'):errors.append(f'{name}: absent target state changed')
  elif c.get('derived_cue') or c.get('proposal_built'):
   errors.append(f'{name}: false cue or proposal on control')
 summary={'workers':len(rows),'positive_cases':sum(r['task']['kind']=='opposite' for r in rows),
  'controls':sum(r['task']['kind']!='opposite' for r in rows),
  'native_cue_successes':sum(bool(r['candidate'].get('derived_cue')) for r in rows),
  'heldout_positive_passes':sum(bool((r['candidate'].get('heldout_score') or {}).get('oracle_pass'))
                                 for r in rows if r['task']['kind']=='opposite'),
  'false_cues':sum(bool(r['candidate'].get('derived_cue')) for r in rows
                   if r['task']['kind'] not in ('opposite','absent_target')),
  'false_proposals':sum(bool(r['candidate'].get('proposal_built')) for r in rows
                        if r['task']['kind']!='opposite'),
  'baseline_proposals':sum(bool(r['baseline'].get('proposal_built')) for r in rows),
  'primary_isolation_and_return':sum(bool(r['primary'].get('unchanged_during_branch')
      and r['primary'].get('only_residual_returned')) for r in rows),
  'median_native_rule_induction_ms':statistics.median(r['candidate']['induction_ns'] for r in rows)/1e6,
  'median_composer_grounding_ms':statistics.median(r['candidate']['grounding_ns'] for r in rows)/1e6,
  'median_baseline_grounding_ms':statistics.median(r['baseline'].get('grounding_ns',0) for r in rows)/1e6,
  'median_experiment_fork_ms':statistics.median(r.get('fork_ns',0) for r in rows)/1e6}
 result={'schema':'ResidualToComposerNativeCueV1Analysis','gates_pass':not errors,
         'errors':errors,'summary':summary}
 out=CAPTURE.with_name('residual_to_composer_native_cue_v1_analysis_20261003.json')
 out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True))
 return int(bool(errors))
if __name__=='__main__':sys.exit(main())
