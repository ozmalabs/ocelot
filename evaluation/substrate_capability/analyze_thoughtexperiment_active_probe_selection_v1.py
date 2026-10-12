#!/usr/bin/env python3
"""Analyze the locked active probe selection capture."""
import json, statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'evaluation/reports/thoughtexperiment_active_probe_selection_v1_raw_20261002.json'
OUT=ROOT/'evaluation/reports/thoughtexperiment_active_probe_selection_v1_analysis_20261002.json'
doc=json.loads(RAW.read_text()); rows=[(w,c) for w in doc['workers'] for c in w['conditions']]
summary={}
for rate in (0,50,90,99):
 group=[c for _,c in rows if c['alias_rate_percent']==rate]
 summary[str(rate)]={'n':len(group),'selector_discrimination_rate':sum(bool(c['choice'].get('ok')) and c['choice'].get('entropy_bits')>0 for c in group)/len(group),
  'correct_key_survival_rate':sum(c['survivors']==['key'] for c in group)/len(group),'heldout_accuracy_rate':sum(c['heldout_accuracy'] for c in group)/len(group),
  'random_discrimination_rate':sum(c['random_probe_discriminates'] for c in group)/len(group),'mean_selector_ms':statistics.mean(c['selector_wall_ns'] for c in group)/1e6,
  'mean_oracle_discriminator_fraction':statistics.mean(c['actual_discriminator_count']/c['pool_size'] for c in group)}
checks={'all_sources_stable':all(w['source_stable'] for w in doc['workers']),'all_16_selectors_valid_and_discriminating':all(c['choice'].get('ok') and c['choice'].get('entropy_bits')>0 for _,c in rows),
 'all_16_select_key_and_holdout':all(c['survivors']==['key'] and c['heldout_accuracy'] for _,c in rows)}
out={'schema':'ThoughtexperimentActiveProbeSelectionV1Analysis','checks':checks,'summary_by_alias_rate':summary,'scope':'Finite supplied hypotheses and candidate pool only; not open-ended learning or structural self-improvement.'}
OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
