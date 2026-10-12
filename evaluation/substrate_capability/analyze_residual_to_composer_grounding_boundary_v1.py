#!/usr/bin/env python3
"""Validate the residual-to-composer grounding boundary capture."""
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/residual_to_composer_grounding_boundary_v1_lock_20261002.json'
DATA=ROOT/'evaluation/reports/residual_to_composer_grounding_boundary_v1_20261002.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 l=json.loads(LOCK.read_text());d=json.loads(DATA.read_text());rows=d['workers']
 assert d['lock_sha256']==sha(LOCK) and d['sources']==l['sources']
 assert len(rows)==l['workers'] and {x['worker'] for x in rows}==set(range(l['workers']))
 for x in rows:
  target=x['authored_cue_control']
  assert x['source_stable'] and x['fault_outcome']['actual']!=x['fault_outcome']['expected']
  assert x['induction']['minted'] and x['induction']['name_hint_supplied'] is False
  assert x['induction']['residual_predicates']==['actual','expected']
  assert x['raw_residual_grounding']['grounded'] is False
  assert 'NO held structural relation' in x['raw_residual_grounding']['wall']
  assert x['raw_residual_grounding']['primary_rule_preserved']
  assert target['built'] and target['target']=='hop_descend_gradient' and target['kind']=='flip_comparison'
  assert target['target_rule_preserved_during_composition']
 print(f'all {len(rows)} paired trials reproduce generic-residual refusal and authored-cue proposal gates')
 print(f"median induce_concern={statistics.median(x['induction']['wall_ns'] for x in rows)/1e6:.3f} ms; "+
  f"median raw grounding refusal={statistics.median(x['raw_residual_grounding']['wall_ns'] for x in rows)/1e6:.3f} ms")
 print('actual→expected:',', '.join(f"{x['fault_outcome']['actual']}→{x['fault_outcome']['expected']}" for x in rows))
if __name__=='__main__':main()
