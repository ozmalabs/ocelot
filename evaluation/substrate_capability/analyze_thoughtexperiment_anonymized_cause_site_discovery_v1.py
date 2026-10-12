#!/usr/bin/env python3
"""Replay blinded cause/site discovery order and held-out gates."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_anonymized_cause_site_discovery_v1_lock_20261002.json'
ORDERS=ROOT/'evaluation/reports/thoughtexperiment_anonymized_cause_site_discovery_v1_orders_20261002.json'
SCORES=ROOT/'evaluation/reports/thoughtexperiment_anonymized_cause_site_discovery_v1_scores_20261002.json'
OUT=ROOT/'evaluation/reports/thoughtexperiment_anonymized_cause_site_discovery_v1_analysis_20261002.json'
TARGET='mrl_offer_due_once';SHADOW='shadow_writer'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def analyze():
    lock=json.loads(LOCK.read_text());orders=json.loads(ORDERS.read_text());scores=json.loads(SCORES.read_text());checks=[]
    checks.extend([('lock_order_binding',orders.get('lock_sha256')==sha(LOCK)),
      ('lock_score_binding',scores.get('lock_sha256')==sha(LOCK) and scores.get('orders_sha256')==sha(ORDERS)),
      ('worker_count',len(orders.get('workers',[]))==lock['workers']==len(scores.get('workers',[]))),
      ('source_lock',orders.get('sources')==lock['sources'] and scores.get('sources')==lock['sources'])])
    score_by={r['worker']:r for r in scores.get('workers',[])}
    for row in orders.get('workers',[]):
        i=row['worker'];disc=row['discovery'];score=score_by.get(i,{});rules=row['candidate_rules'];source=row['private_evaluator_source_map']
        train_ok={r['proposal_id']:all(x['correct'] for x in r['outcomes']) for r in row['training_outcomes']}
        winners=[pid for pid,v in train_ok.items() if v]
        selected=row['decision'].get('proposal_id');score_rows={r['proposal_id']:r for r in score.get('candidate_scores',[])}
        selected_rows=score_rows.get(selected,{}).get('heldout',[])
        checks.extend([
          (f'w{i}_source_stable',row['source_stable'] and score.get('source_stable') is True),
          (f'w{i}_trace_complete',disc['dropped']==0 and disc['event_count']>0),
          (f'w{i}_correlated_writer',disc['shadow_writer_seen'] is True and SHADOW in set(source.values())),
          (f'w{i}_noop_control',disc['noop_attempt_seen'] is True),
          (f'w{i}_anonymized_inputs',not any(disc.get(k,True) for k in ('original_rule_names_passed_to_discovery','target_name_passed_to_discovery','cue_passed_to_discovery'))),
          (f'w{i}_bounded_candidates',disc['candidate_count']==6 and len(rules)==6 and disc['active_rule_count']>disc['candidate_count']),
          (f'w{i}_exactly_one_train_winner',len(winners)==1),
          (f'w{i}_selected_train_winner',selected in winners),
          (f'w{i}_target_source_selected',row.get('selected_source')==TARGET and source.get(selected)==TARGET),
          (f'w{i}_heldout_pass',len(selected_rows)==lock['repeats'] and all(x['correct'] for x in selected_rows)),
          (f'w{i}_controls_abstain',all(not c.get('proposal_id') for c in row['controls'].values())),
          (f'w{i}_scores_replay',score.get('discovery_replayed') is True and set(score_rows)==set(rules)),
        ])
    result={'schema':'ThoughtexperimentAnonymizedCauseSiteDiscoveryV1Analysis','passed':sum(ok for _,ok in checks),
      'total':len(checks),'checks':[{'name':n,'passed':bool(ok)} for n,ok in checks],
      'interpretation':'Single-family anonymized-evidence proposal selection with one correlated writer and a no-op control. Candidate generation/scoring/oracle remain host orchestrated; this is not autonomous residual interpretation or a broad capability estimate.'}
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(f"{result['passed']}/{result['total']} checks; {OUT.relative_to(ROOT)}")
    return 0 if all(ok for _,ok in checks) else 1
if __name__=='__main__':raise SystemExit(analyze())
