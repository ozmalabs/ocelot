#!/usr/bin/env python3
"""Independent report checks for anonymized two-family transfer panel."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_anonymized_cause_site_transfer_v1_lock_20261002.json'
ORDERS=ROOT/'evaluation/reports/thoughtexperiment_anonymized_cause_site_transfer_v1_orders_20261002.json'
SCORES=ROOT/'evaluation/reports/thoughtexperiment_anonymized_cause_site_transfer_v1_scores_20261002.json'
OUT=ROOT/'evaluation/reports/thoughtexperiment_anonymized_cause_site_transfer_v1_analysis_20261002.json'
TARGETS={'recurrence':'mrl_offer_due_once','conversation':'reply_to_adjacency_pair'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def analyze():
    lock=json.loads(LOCK.read_text());orders=json.loads(ORDERS.read_text());scores=json.loads(SCORES.read_text());checks=[]
    checks += [('order_lock',orders.get('lock_sha256')==sha(LOCK)),('score_lock',scores.get('lock_sha256')==sha(LOCK)),
      ('order_score_link',scores.get('orders_sha256')==sha(ORDERS)),('source_lock',orders.get('sources')==lock['sources']==scores.get('sources')),
      ('worker_count',len(orders.get('workers',[]))==lock['workers']==len(scores.get('workers',[])))]
    score_workers={x['worker']:x for x in scores.get('workers',[])}
    for row in orders.get('workers',[]):
      i=row['worker'];sw=score_workers.get(i,{})
      checks.append((f'w{i}_source_stable',row['source_stable'] and sw.get('source_stable') is True))
      for fam,target in TARGETS.items():
        o=row['families'][fam];s=sw.get('families',{}).get(fam,{});d=o['discovery'];source=o['candidate_source_map'];rules=o['candidate_rules']
        wins=[r['proposal_id'] for r in o['training_outcomes'] if all(t['correct'] for t in r['trials'])]
        selected=o['decision'].get('proposal_id');score_rows={r['proposal_id']:r for r in s.get('candidate_scores',[])}
        chosen=score_rows.get(selected,{}).get('heldout',[])
        keys=(f'w{i}_{fam}_',)
        checks.extend([
          (keys[0]+'trace_complete',d['event_count']>0 and d['dropped']==0),
          (keys[0]+'shadow_writer',d['shadow_writer_seen'] is True and d['productive_writer_count']>=2),
          (keys[0]+'noop_seen',d['noop_attempt_seen'] is True),
          (keys[0]+'anonymized',d['target_name_passed_to_discovery'] is False and d['cue_passed_to_discovery'] is False and d['original_names_passed_to_discovery'] is False),
          (keys[0]+'candidate_set_replayed',s.get('discovery_replayed') is True and len(rules)==d['candidate_count'] and set(score_rows)==set(rules)),
          (keys[0]+'target_in_candidates',any(source.get(pid)==target for pid in rules)),
          (keys[0]+'single_train_winner',len(wins)==1),
          (keys[0]+'selector_picks_winner',selected in wins),
          (keys[0]+'selected_target_rule',o.get('selected_source')==target and source.get(selected)==target),
          (keys[0]+'heldout_selected_passes',len(chosen)==lock['repeats'] and all(t['correct'] for t in chosen)),
          (keys[0]+'all_candidates_scored',len(score_rows)==d['candidate_count']),
          (keys[0]+'controls_abstain',all(not c.get('proposal_id') for c in o['controls'].values())),
        ])
    result={'schema':'ThoughtexperimentAnonymizedCauseSiteTransferV1Analysis','passed':sum(ok for _,ok in checks),
      'total':len(checks),'checks':[{'name':name,'passed':bool(ok)} for name,ok in checks],
      'interpretation':'Two authored-family transfer result with anonymized rule identifiers, shadow/no-op controls and externally generated task labels; this is not autonomous diagnosis or a natural-task generality estimate.'}
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(f"{result['passed']}/{result['total']} checks; {OUT.relative_to(ROOT)}")
    return 0 if all(ok for _,ok in checks) else 1
if __name__=='__main__':raise SystemExit(analyze())
