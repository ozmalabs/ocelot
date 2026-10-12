#!/usr/bin/env python3
"""Independent checks for crossed full-composition scaling capture."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/edge_identity_full_compose_crossed_scaling_v1_2_lock_20261003.json'
DATA=ROOT/'evaluation/reports/edge_identity_full_compose_crossed_scaling_v1_2_20261003.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 l=json.loads(LOCK.read_text());d=json.loads(DATA.read_text())
 assert d['lock_sha256']==sha(LOCK) and d['sources']==l['sources']
 assert len(d['rows'])==len(l['cells'])==15
 seen=[]
 for row,(f,n) in zip(d['rows'],l['cells']):
  assert (row['fields'],row['unrelated_nodes'])==(f,n)
  assert len(row['trials'])==l['trials_per_cell']
  for t in row['trials']:
   seen.append(t)
   expected=f+f*(f-1)//2+(1 if f>2 else 0)
   assert t['fields']==f and t['unrelated_nodes']==n
   assert t['enumerated_sites']<=l['candidate_cap']
   assert t['expected_attribute_sites']==expected
   assert t['materialized_target_sites']==t['enumerated_sites']
   assert t['built'] and t['operator']==l['expected_operator'] and t['site']==l['expected_site']
   assert t['selected_actor_verb'] and t['primary_rule_store_unchanged']
   assert t['compose_ns']>0 and t['graph_setup_ns']>=0
 assert len(seen)==45
 print('PASS: 15 crossed cells, 45 trials; all caps, site counts, exact selections, and rule-store invariants hold')
 for f in l['fields']:
  for n in l['unrelated_nodes']:
   row=next(r for r in d['rows'] if r['fields']==f and r['unrelated_nodes']==n)
   vals=[t['compose_ns'] for t in row['trials']]
   sites=row['trials'][0]['enumerated_sites']
   print(f'fields={f:2d} nodes={n:5d} sites={sites:3d} median_compose_ms={row["median_compose_ns"]/1e6:.3f} range_ms={min(vals)/1e6:.3f}-{max(vals)/1e6:.3f}')
if __name__=='__main__':main()
