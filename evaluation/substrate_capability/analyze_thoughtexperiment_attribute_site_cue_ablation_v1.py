#!/usr/bin/env python3
"""Independent checks for attribute-site cue-ablation capture."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=ROOT/'evaluation/reports/thoughtexperiment_attribute_site_cue_ablation_v1_20261002.json'
d=json.loads(p.read_text());rows=d['conditions'];by={c:[] for c in ('answer_bearing','direction_omitted','source_only','destination_only')}
for r in rows:by[r['condition']].append(r)
checks={
 'four_workers_each_condition':len(rows)==16 and all(len(v)==4 for v in by.values()),
 'both_opposing_fixture_candidates_available':all({'swap_term_leaf:bad_score->good_score','swap_term_leaf:good_score->bad_score'}.issubset(set(r['ordered_swap_candidate_labels'])) for r in rows),
 'answer_bearing_selects_forward':all(r['built'] and r['operator']=='swap_term_leaf' and r['site']=="Attr key 'bad_score' -> 'good_score'" for r in by['answer_bearing']),
 'direction_omitted_abstains':all(not r['built'] for r in by['direction_omitted']),
 'source_only_abstains':all(not r['built'] for r in by['source_only']),
 'destination_only_abstains':all(not r['built'] for r in by['destination_only']),
 'primary_rule_preserved':all(r['primary_unchanged'] for r in rows),
 'positive_composer_results_have_target':all(r['target']=='classify_meter_delta' for r in rows if r['built']),
}
out={'schema':'AttributeSiteCueAblationV1Analysis','checks':checks,'all_checks_pass':all(checks.values()),
 'summary':{k:{'built':sum(bool(r['built']) for r in v),'abstained':sum(not r['built'] for r in v)} for k,v in by.items()},
 'interpretation':'Cue-conditioned ordered-site selection reproduced; site direction is not inferred when the cue omits it.'}
print(json.dumps(out,indent=2,sort_keys=True))
if not out['all_checks_pass']:raise SystemExit(1)
