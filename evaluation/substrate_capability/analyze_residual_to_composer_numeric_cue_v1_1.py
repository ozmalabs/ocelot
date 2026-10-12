#!/usr/bin/env python3
"""Corrected independent analysis for the numeric residual cue capture."""
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/residual_to_composer_numeric_cue_v1_lock_20261003.json'
CAPTURE=ROOT/'evaluation/reports/residual_to_composer_numeric_cue_v1_20261003.json'
INITIAL=ROOT/'evaluation/substrate_capability/analyze_residual_to_composer_numeric_cue_v1.py'
OUT=ROOT/'evaluation/reports/residual_to_composer_numeric_cue_v1_1_analysis_20261003.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 lock=json.loads(LOCK.read_text());data=json.loads(CAPTURE.read_text());rows=data['workers'];errors=[]
 if data.get('lock_sha256')!=sha(LOCK):errors.append('lock hash mismatch')
 if data.get('sources')!=lock.get('sources'):errors.append('source lock mismatch')
 if len(rows)!=len(lock['tasks']) or len({r['worker'] for r in rows})!=len(rows):errors.append('worker coverage mismatch')
 vectors=lock['action_vector_encoding'];allowed={'actual_dx','actual_dy','expected_dx','expected_dy'}
 for r in rows:
  t=r['task'];c=r['candidate'];p=r['primary'];b=r['baseline'];name=t['id'];positive=t['kind']=='opposite'
  if not r.get('source_stable'):errors.append(f'{name}: source drift')
  if c.get('residual_has_action_labels') or c.get('opposite_pair_nodes') or c.get('opposite_pair_edges'):
   errors.append(f'{name}: label or pair ontology leaked into candidate graph')
  obs={str(k):str(v) for k,v in r.get('observation_passed_to_induction',[])}
  if set(obs)-allowed:errors.append(f'{name}: nonnumeric/label input to concern induction')
  for prefix,action in [('actual',r['raw_residual'].get('actual')),('expected',r['raw_residual'].get('expected'))]:
   vec=vectors.get(action)
   for axis,suffix in [('x','dx'),('y','dy')]:
    key=f'{prefix}_{suffix}'
    if vec is None:
     if key in obs:errors.append(f'{name}: unexpected component {key}')
    elif obs.get(key)!=str(vec[0 if axis=='x' else 1]):errors.append(f'{name}: wrong encoded component {key}')
  if b.get('proposal_built') or not b.get('branch_changed'):errors.append(f'{name}: invalid raw baseline')
  if not c.get('branch_changed'):errors.append(f'{name}: candidate branch unchanged')
  if not(p.get('unchanged_during_branch') and p.get('rules_unchanged_during_branch')
      and p.get('revision_unchanged_during_branch') and p.get('only_residual_returned')):
   errors.append(f'{name}: primary isolation/return failed')
  if positive:
   score=c.get('heldout_score') or {}
   if not(c.get('derived_cue') and c.get('native_cue_rule_observed_fired')
       and c.get('proposal_built') and c.get('operator')=='flip_comparison'
       and c.get('target')=='hop_descend_gradient'):
    errors.append(f'{name}: positive cue/proposal mismatch')
   if not(score.get('oracle_pass') and score.get('receipt_verified') and score.get('primary_preserved')):
    errors.append(f'{name}: held-out oracle failed')
  elif name=='target_absent':
   if not c.get('derived_cue') or c.get('proposal_built') or not c.get('target_rule_preserved_in_primary'):
    errors.append(f'{name}: target-absent gate failed')
  elif c.get('derived_cue') or c.get('proposal_built'):errors.append(f'{name}: false positive control')
 summary={'workers':len(rows),'positive_cases':sum(r['task']['kind']=='opposite' for r in rows),
  'ordinary_controls':sum(r['task']['kind'] not in ('opposite','absent_target') for r in rows),
  'target_absent_controls':sum(r['task']['id']=='target_absent' for r in rows),
  'cue_successes':sum(bool(r['candidate'].get('derived_cue')) for r in rows),
  'heldout_positive_passes':sum(bool((r['candidate'].get('heldout_score') or {}).get('oracle_pass')) for r in rows if r['task']['kind']=='opposite'),
  'false_control_cues':sum(bool(r['candidate'].get('derived_cue')) for r in rows if r['task']['kind'] not in ('opposite','absent_target')),
  'false_proposals':sum(bool(r['candidate'].get('proposal_built')) for r in rows if r['task']['kind']!='opposite'),
  'pair_codebook_nodes':sum(r['candidate'].get('opposite_pair_nodes',0) for r in rows),
  'action_labeled_residuals':sum(bool(r['candidate'].get('residual_has_action_labels')) for r in rows),
  'median_two_branch_fork_ms':statistics.median(r['fork_ms'] for r in rows),
  'median_native_induction_ms':statistics.median(r['candidate']['induction_ns'] for r in rows)/1e6,
  'median_composer_grounding_ms':statistics.median(r['candidate']['grounding_ns'] for r in rows)/1e6}
 result={'schema':'ResidualToComposerNumericCueV1_1Analysis','gates_pass':not errors,'errors':errors,
  'analysis_note':'Corrects the initial analyzer fork summary: raw capture stores combined fork time as fork_ms. Behavioral criteria are rechecked independently.',
  'input_hashes':{'lock_sha256':sha(LOCK),'capture_sha256':sha(CAPTURE),'initial_analyzer_sha256':sha(INITIAL)},'summary':summary}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True));return int(bool(errors))
if __name__=='__main__':raise SystemExit(main())
