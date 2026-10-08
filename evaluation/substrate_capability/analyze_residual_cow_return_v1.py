#!/usr/bin/env python3
"""Independent semantic and isolation gates for residual CoW return v1."""
import hashlib,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/residual_cow_return_v1_lock_20261002.json'
CAP=ROOT/'evaluation/reports/residual_cow_return_v1_20261002.json'
OUT=ROOT/'evaluation/reports/residual_cow_return_v1_analysis_20261002.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 lock=json.loads(LOCK.read_text());data=json.loads(CAP.read_text());rows=data['rows'];errors=[]
 if data.get('lock_sha256')!=sha(LOCK):errors.append('lock hash mismatch')
 if data.get('sources')!=lock.get('sources'):errors.append('source snapshot mismatch')
 if len(rows)!=26:errors.append(f'expected 26 rows; got {len(rows)}')
 for r in rows:
  name=f"{r['task']['id']}/{r['backend']}";positive=r['task']['kind']=='opposite'
  if not r['source_stable']:errors.append(f'{name}: source drift')
  if not r['host_unchanged_before_return']:errors.append(f'{name}: branch mutated host before return')
  if not r['proposal']['branch_target_preserved']:errors.append(f'{name}: branch target mutated')
  if positive:
   h=r.get('heldout_score') or {}
   if not (r['proposal']['built'] and r['proposal']['kind']=='flip_comparison' and r['proposal']['target']=='hop_descend_gradient'):
    errors.append(f'{name}: expected proposal missing/wrong')
   if not (h.get('oracle_pass') and h.get('receipt_verified') and h.get('primary_preserved')):errors.append(f'{name}: heldout/receipt gate failed')
   if not r['return']['applied']:errors.append(f'{name}: derived residual not returned')
  else:
   if r['proposal']['built']:errors.append(f'{name}: false proposal')
   if r['return']['applied']:errors.append(f'{name}: control residual should not be returned')
  if not r['return']['host_rule_store_preserved']:errors.append(f'{name}: host rule store changed')
  if not all(r['return'][k] for k in ('added_node_parity','added_edge_parity','changed_node_parity',
      'removed_node_parity','changed_edge_parity','removed_edge_parity')):
   errors.append(f'{name}: returned graph delta differs from branch')
 by={}
 for r in rows:by.setdefault(r['backend'],[]).append(r)
 summary={'rows':len(rows),'backends':{},'gate_errors':errors}
 for backend,rs in by.items():
  summary['backends'][backend]={'median_fork_ms':statistics.median(r['timing_ns']['fork'] for r in rs)/1e6,
   'median_induce_ms':statistics.median(r['timing_ns']['induce'] for r in rs)/1e6,
   'median_ground_ms':statistics.median(r['timing_ns']['ground'] for r in rs)/1e6,
   'median_adopt_ms':statistics.median([r['return']['adoption_ns'] for r in rs if r['return']['applied']])/1e6,
   'positive_returns':sum(r['return']['applied'] for r in rs),'positive_cases':sum(r['task']['kind']=='opposite' for r in rs),
   'control_false_proposals':sum(r['proposal']['built'] for r in rs if r['task']['kind']!='opposite'),
   'median_derived_nodes':statistics.median(r['residual']['derived_only']['nodes_added'].__len__() for r in rs if r['task']['kind']=='opposite'),
   'median_derived_edges':statistics.median(r['residual']['derived_only']['edges_added'].__len__() for r in rs if r['task']['kind']=='opposite')}
 result={'schema':'ResidualCowReturnV1Analysis','gates_pass':not errors,'summary':summary}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True));return int(bool(errors))
if __name__=='__main__':sys.exit(main())
