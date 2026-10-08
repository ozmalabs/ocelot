#!/usr/bin/env python3
"""Independent acceptance gates for residual-to-composer cue derivation v1."""
import hashlib,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/residual_to_composer_cue_derivation_v1_lock_20261002.json'
CAPTURE=ROOT/'evaluation/reports/residual_to_composer_cue_derivation_v1_20261002.json'
RUNNER=ROOT/'evaluation/substrate_capability/measure_residual_to_composer_cue_derivation_v1.py'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 lock=json.loads(LOCK.read_text());data=json.loads(CAPTURE.read_text());rows=data['workers'];errors=[]
 if data.get('lock_sha256')!=sha(LOCK):errors.append('lock hash mismatch')
 if data.get('sources')!=lock.get('sources'):errors.append('capture source hashes differ from lock')
 if len(rows)!=len(lock.get('tasks',[])):errors.append('worker count mismatch')
 for row in rows:
  name=row['task']['id'];positive=row['task']['kind']=='opposite'
  if not row.get('source_stable'):errors.append(f'{name}: source drift')
  if positive:
   if row['derived_cue'] is None:errors.append(f'{name}: failed to derive cue')
   g=row['grounding'];score=row.get('heldout_score') or {}
   if not (g.get('built') and g.get('kind')=='flip_comparison' and g.get('target')=='hop_descend_gradient'):
    errors.append(f'{name}: wrong/no proposal')
   if not g.get('primary_rule_preserved'):errors.append(f'{name}: primary rule mutated')
   if not score.get('oracle_pass') or not score.get('primary_preserved') or not score.get('receipt_verified'):
    errors.append(f'{name}: heldout utility/isolation/receipt failed')
  elif name=='target_absent':
   if row['derived_cue'] is None:errors.append(f'{name}: cue derivation should succeed before grounding')
   if row['grounding'].get('built'):errors.append(f'{name}: proposed despite absent target')
   if not row['grounding'].get('primary_rule_preserved'):errors.append(f'{name}: absent target state changed')
  else:
   if row['derived_cue'] is not None:errors.append(f'{name}: should abstain')
   if row['grounding'].get('built'):errors.append(f'{name}: false proposal')
   if name=='target_absent' and row['grounding'].get('target')=='hop_descend_gradient':
    errors.append(f'{name}: proposed absent target')
 summary={'workers':len(rows),'positive_cases':sum(r['task']['kind']=='opposite' for r in rows),
  'abstention_controls':sum(r['task']['kind']!='opposite' for r in rows),
  'positive_proposal_passes':sum(bool(r['grounding'].get('built')) for r in rows if r['task']['kind']=='opposite'),
  'false_proposals':sum(bool(r['grounding'].get('built')) for r in rows if r['task']['kind']!='opposite'),
  'median_induction_ms':statistics.median(r['induction']['wall_ns'] for r in rows)/1e6,
  'median_grounding_ms':statistics.median(r['grounding']['wall_ns'] for r in rows)/1e6,
  'rule_side_effects':[{'case':r['task']['id'],'added_count':len(r['grounding']['active_rule_additions']),
    'induced_rules':[name for name in r['grounding']['active_rule_additions'] if 'induced_' in name],
    'removed_count':len(r['grounding']['active_rule_removals'])} for r in rows]}
 result={'schema':'ResidualToComposerCueDerivationV1Analysis','gates_pass':not errors,'errors':errors,'summary':summary}
 out=CAPTURE.with_name('residual_to_composer_cue_derivation_v1_analysis_20261002.json')
 out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 print(json.dumps(result,indent=2,sort_keys=True))
 return 1 if errors else 0
if __name__=='__main__':sys.exit(main())
