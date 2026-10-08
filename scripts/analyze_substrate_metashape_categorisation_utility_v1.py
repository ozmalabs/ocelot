#!/usr/bin/env python3
"""Audit protocol/oracle conformance for categorisation utility v1."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/substrate_metashape_categorisation_utility_v1_20260926.json'
LOCK=ROOT/'evaluation/substrate_capability/metashape_categorisation_utility_v1_lock_20260926.json'
OUT=ROOT/'evaluation/reports/substrate_metashape_categorisation_utility_v1_analysis_20260926.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());q=raw['queries']
 expected={(fam,kind):('spatial_dynamics' if fam=='MotionRuleProbe' and kind!='type_changed' else ('family_shape' if kind in ('positive','extra_field') and fam!='MotionRuleProbe' else None)) for fam in ('FrameBindingProbe','MotionRuleProbe','ResourceTransferProbe','GoalTraceProbe') for kind in ('positive','fixed_value_change','fixed_field_omitted','extra_field','type_changed')}
 def conforms(x):
  gold=expected[(x['family'],x['query_kind'])]
  if gold=='family_shape':return x['gold_label']==raw['shape_by_family'][x['family']]
  return x['gold_label']==gold
 mismatches=[{'family':x['family'],'query_kind':x['query_kind'],'expected_protocol':expected[(x['family'],x['query_kind'])],'runner_gold':x['gold_label']} for x in q if not conforms(x)]
 gates={'source_lock_matches':raw['lock_sha256']==sha(LOCK) and raw['protocol_sha256']==sha(ROOT/'docs/research/engine_substrate/SUBSTRATE_METASHAPE_CATEGORISATION_UTILITY_PREREG_20260926.md'),'20_queries_captured':len(q)==20,'gold_vector_matches_protocol':not mismatches,'query_does_not_mutate_graph':raw['query_graph_counts_after_training']==raw['query_graph_counts_after'],'persistence_guard_active':raw['persistence_disabled'] is True}
 out={'schema_version':1,'run_id':raw['run_id'],'admitted':all(gates.values()),'gates':gates,'oracle_mismatches':mismatches,'interpretation':'V1 is inadmissible for capability scoring because its runner labels the MotionRule positive and extra-field cases as abstentions, contrary to the locked protocol which assigns spatial_dynamics. The raw decisions are preserved; no accuracy conclusion should be drawn from v1.', 'next_step':'Correct the gold-label encoding in a separately locked v1.1 run; do not alter or overwrite v1.'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':str(OUT),'admitted':out['admitted'],'gates':gates,'oracle_mismatches':mismatches},indent=2));return 0
if __name__=='__main__':main()
