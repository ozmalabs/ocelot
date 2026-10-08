#!/usr/bin/env python3
"""Independent candidate-rehydration and stale-revision gates."""
import hashlib,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/residual_cow_candidate_rehydration_v1_lock_20261002.json'
CAP=ROOT/'evaluation/reports/residual_cow_candidate_rehydration_v1_20261002.json'
OUT=ROOT/'evaluation/reports/residual_cow_candidate_rehydration_v1_analysis_20261002.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 lock=json.loads(LOCK.read_text());data=json.loads(CAP.read_text());rows=data['rows'];errors=[]
 if data.get('lock_sha256')!=sha(LOCK):errors.append('lock hash mismatch')
 if data.get('sources')!=lock.get('sources'):errors.append('source snapshot mismatch')
 if len(rows)!=4:errors.append('expected four workers')
 for r in rows:
  name=r['task']['id'];p=r['proposal'];ret=r['return']
  if not r['source_stable']:errors.append(f'{name}: source drift')
  if not r['host_unchanged_before_return']:errors.append(f'{name}: host changed during exploration')
  if not (p['built'] and p['kind']=='flip_comparison' and p['target']=='hop_descend_gradient'):
   errors.append(f'{name}: wrong proposal')
  for label,score in [('pre-return',r['pre_return_score']),('rehydrated',ret['replayed_score'])]:
   if not (score.get('oracle_pass') and score.get('receipt_verified') and score.get('primary_preserved')):
    errors.append(f'{name}: {label} scoring/receipt gate failed')
  if r['pre_return_score'].get('task_cases')!=ret['replayed_score'].get('task_cases'):
   errors.append(f'{name}: rehydrated candidate outcomes differ from pre-return outcomes')
  if not (ret['candidate_digest_matches'] and ret['candidate_semantic_identity'] and ret['receipt_node_present']):
   errors.append(f'{name}: candidate readback mismatch')
  if not ret['host_rules_unchanged']:errors.append(f'{name}: host rule store changed')
 if rows and not (rows[0]['return']['stale_revision_rejected'] and rows[0]['return']['stale_attempt_host_unchanged']):
  errors.append('stale revision was not safely rejected')
 summary={'workers':len(rows),'rehydrated_candidates_pass':sum(bool(r['return']['replayed_score'].get('oracle_pass')) for r in rows),
  'returned_residual_nodes':sum(r['return']['host_graph_delta_counts'][0] for r in rows),
  'median_fork_ms':statistics.median(r['timing_ns']['fork'] for r in rows)/1e6,
  'median_return_ms':statistics.median(r['timing_ns']['adopt'] for r in rows)/1e6,
  'stale_revision_rejected':bool(rows and rows[0]['return']['stale_revision_rejected'])}
 result={'schema':'ResidualCowCandidateRehydrationV1Analysis','gates_pass':not errors,'errors':errors,'summary':summary}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True));return int(bool(errors))
if __name__=='__main__':sys.exit(main())
