#!/usr/bin/env python3
"""Score paired teach filing-category decisions against the locked oracle."""
import hashlib,json
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/substrate_metashape_categorisation_utility_v1_2_20260926.json'
LOCK=ROOT/'evaluation/substrate_capability/metashape_categorisation_utility_v1_2_lock_20260926.json'
OUT=ROOT/'evaluation/reports/substrate_metashape_categorisation_utility_v1_2_analysis_20260926.json'
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_METASHAPE_CATEGORISATION_UTILITY_V1_2_AMENDMENT_20260926.md'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def metrics(rows,key):
 n=len(rows);correct=sum(r[key]['prediction']==r['gold_label'] for r in rows)
 abstain=[r for r in rows if r[key]['prediction'] is None]
 gold_none=sum(r['gold_label'] is None for r in rows)
 correct_abstain=sum(r[key]['prediction'] is None and r['gold_label'] is None for r in rows)
 return {'n':n,'correct':correct,'accuracy':correct/n if n else None,'covered':n-len(abstain),'coverage':(n-len(abstain))/n if n else None,
         'abstentions':len(abstain),'correct_abstentions':correct_abstain,'abstention_precision':correct_abstain/len(abstain) if abstain else None,
         'abstention_recall':correct_abstain/gold_none if gold_none else None,'gold_abstain_cases':gold_none}
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());rows=raw['queries']
 mismatches=[];order_ok=len(rows)==20
 for i,r in enumerate(rows):
  fam=r['family'];kind=r['query_kind']
  expected='spatial_dynamics' if fam=='MotionRuleProbe' and kind!='type_changed' else (raw['shape_by_family'][fam] if fam!='MotionRuleProbe' and kind in ('positive','extra_field') else None)
  if r['gold_label']!=expected:mismatches.append({'family':fam,'kind':kind,'expected':expected,'observed':r['gold_label']})
  if i%5 != ('positive','fixed_value_change','fixed_field_omitted','extra_field','type_changed').index(kind):order_ok=False
 per_family={}
 for fam in sorted({r['family'] for r in rows}):per_family[fam]={'baseline':metrics([r for r in rows if r['family']==fam],'baseline'),'trained':metrics([r for r in rows if r['family']==fam],'trained')}
 transitions=Counter((r['baseline']['prediction'] or '<ABSTAIN>',r['trained']['prediction'] or '<ABSTAIN>') for r in rows)
 gates={'source_protocol_and_lock_match':raw['lock_sha256']==sha(LOCK) and raw['protocol_sha256']==sha(PROTOCOL) and all(len(x)==64 for x in raw['source_sha256'].values()),
        'complete_growth_dependency_closure':raw['seed_load']['loaded']==2 and raw['seed_load']['total']==2 and not raw['seed_load']['failed'],
        'correct_protocol_gold_vector':not mismatches,
        'twenty_queries_in_locked_order':len(rows)==20 and order_ok,
        'query_phase_did_not_mutate_graph':raw['query_graph_counts_after_training']==raw['query_graph_counts_after'],
        'seed_persistence_disabled':raw['persistence_disabled'] is True}
 result={'schema_version':1,'run_id':raw['run_id'],'admitted':all(gates.values()),'gates':gates,'oracle_mismatches':mismatches,
         'baseline':metrics(rows,'baseline'),'trained':metrics(rows,'trained'),'per_family':per_family,
         'prediction_transitions':{f'{a} -> {b}':n for (a,b),n in sorted(transitions.items())},
         'interpretation':'On this locked synthetic filing-category oracle, adding three minted MetaShapes increases classifier coverage but decreases exact accuracy and abstention quality because the prior-only categoriser assigns minted labels to fixed-field, missing-field, and changed-type controls. The structural decoding results from the adjacent MetaShape panel do not determine this categoriser output: categorise_by_shape directly uses the shared keyword-prior scorer. This is task-specific evidence, not a natural-task rate.',
         'limitations':['Twenty synthetic queries over four schemas; one process.','Gold labels encode the preregistered schema/control design, not human semantic judgments.','No independent replication yet.']}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':str(OUT),'admitted':result['admitted'],'gates':gates,'baseline':result['baseline'],'trained':result['trained']},indent=2));return 0 if result['admitted'] else 1
if __name__=='__main__':raise SystemExit(main())
