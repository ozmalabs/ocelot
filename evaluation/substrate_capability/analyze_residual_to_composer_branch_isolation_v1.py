#!/usr/bin/env python3
"""Independent acceptance gates for branch-isolated residual cue derivation."""
import hashlib,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/residual_to_composer_branch_isolation_v1_lock_20261002.json'
CAPTURE=ROOT/'evaluation/reports/residual_to_composer_branch_isolation_v1_20261002.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 lock=json.loads(LOCK.read_text());data=json.loads(CAPTURE.read_text());rows=data.get('workers',[]);errors=[]
 if data.get('lock_sha256')!=sha(LOCK):errors.append('lock hash mismatch')
 if data.get('sources')!=lock.get('sources'):errors.append('capture sources differ from lock')
 if len(rows)!=len(lock.get('tasks',[])):errors.append('worker count mismatch')
 if len({r.get('worker') for r in rows})!=len(rows):errors.append('worker identifiers not unique')
 for r in rows:
  task=r.get('task',{});kind=task.get('kind');name=task.get('id');positive=kind=='opposite'
  if not r.get('source_stable'):errors.append(f'{name}: source drift')
  b=r.get('branch',{});p=r.get('primary',{});g=r.get('grounding',{})
  if not b.get('branch_changed'):errors.append(f'{name}: exploration branch had no recorded change')
  for field in ('unchanged_during_branch','rules_unchanged_during_branch','revision_unchanged_during_branch','only_residual_returned'):
   if not p.get(field):errors.append(f'{name}: primary {field} failed')
  if p.get('new_node_ids')!=[p.get('returned_residual_id')]:errors.append(f'{name}: primary did not receive exactly one residual node')
  if positive:
   score=g.get('heldout_score') or {}
   if not(g.get('built') and g.get('kind')=='flip_comparison' and g.get('target')=='hop_descend_gradient'):
    errors.append(f'{name}: wrong/no held-operator proposal')
   if not p.get('target_rule_preserved'):errors.append(f'{name}: primary target rule changed')
   if not p.get('returned_candidate_present'):errors.append(f'{name}: candidate absent from returned residual')
   if not(score.get('oracle_pass') and score.get('primary_preserved') and score.get('receipt_verified')):
    errors.append(f'{name}: heldout utility or scoring isolation failed')
  elif name=='target_absent':
   if not g.get('built') is False:errors.append(f'{name}: proposal built despite absent target')
   if not p.get('target_rule_preserved'):errors.append(f'{name}: absent-target primary changed')
  elif g.get('built'):
   errors.append(f'{name}: false proposal on abstention control')
 summary={'workers':len(rows),'positive_cases':sum(r.get('task',{}).get('kind')=='opposite' for r in rows),
  'abstention_controls':sum(r.get('task',{}).get('kind')!='opposite' for r in rows),
  'primary_isolation_passes':sum(bool(r.get('primary',{}).get('unchanged_during_branch') and r.get('primary',{}).get('only_residual_returned')) for r in rows),
  'branch_rule_additions':{r['task']['id']:r.get('branch',{}).get('rule_count_delta') for r in rows},
  'median_snapshot_fork_ms':statistics.median(r.get('branch',{}).get('fork_ns',0) for r in rows)/1e6}
 result={'schema':'ResidualToComposerBranchIsolationV1Analysis','gates_pass':not errors,'errors':errors,'summary':summary}
 out=CAPTURE.with_name('residual_to_composer_branch_isolation_v1_analysis_20261002.json')
 out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True));return int(bool(errors))
if __name__=='__main__':sys.exit(main())
