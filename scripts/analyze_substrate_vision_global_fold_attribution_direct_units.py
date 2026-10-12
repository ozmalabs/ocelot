#!/usr/bin/env python3
"""Independent counter-conservation and uninstrumented-parity audit."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];RAW=ROOT/'evaluation/reports/substrate_vision_global_fold_attribution_direct_units_20260925.json';LOCK=ROOT/'evaluation/substrate_capability/vision_global_fold_attribution_direct_units_lock_20260925.json';OUT=ROOT/'evaluation/reports/substrate_vision_global_fold_attribution_direct_units_analysis_20260925.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 d=json.loads(RAW.read_text());l=json.loads(LOCK.read_text());p=d['provenance'];summaries=[]
 for n in (2,4,8,16):
  group=[a for a in d['arms'] if a['n_side']==n];parts={}
  for a in group:
   g=a['global_counters'];pr=a['per_rule_counters'];selected={x['metric']:x['count'] for x in a['selected_rule_counters']}
   parts[a['variant']]={'rule':a['rule_name'],'progress':a['progress'],'selected_rule':selected,'global_candidate_tests':g.get('cand_tested',0),'global_term_evaluations':g.get('term_evals_total',0),'global_term_units':g.get('term_units_total',0),'nodesoftype_invocations':selected.get('NodesOfType',0),'direct_nodesoftype_units':g.get('term_unit:NodesOfType',0),'per_rule_candidate_tests':sum(x['count'] for x in pr if x['metric']=='candidate_tests'),'per_rule_term_evaluations':sum(x['count'] for x in pr if x['metric']=='term_evaluations'),'per_rule_term_units':sum(x['count'] for x in pr if x['metric']=='term_units')}
  n_units=group[0]['n_units'];global_calls=parts['global']['selected_rule'].get('NodesOfType',0);scoped_calls=parts['scoped']['selected_rule'].get('NodesOfType',0);extra_calls=global_calls-scoped_calls
  direct_delta=parts['global']['direct_nodesoftype_units']-parts['scoped']['direct_nodesoftype_units']
  summaries.append({'n_side':n,'n_units':n_units,'extra_global_nodesoftype_invocations':extra_calls,'inferred_extra_node_values_materialized':extra_calls*n_units,'direct_nodesoftype_unit_delta':direct_delta,'direct_counter_matches_derived':direct_delta==extra_calls*n_units,'variants':parts})
 conservation=all(x['global_candidate_tests']==x['per_rule_candidate_tests'] and x['global_term_evaluations']==x['per_rule_term_evaluations'] and x['global_term_units']==x['per_rule_term_units'] for s in summaries for x in s['variants'].values())
 checks={'lock_hashes_match':l['hashes']['runner']==p['runner_sha256'] and l['hashes']['protocol']==p['protocol_sha256'] and l['hashes']['scale_raw']==p['scale_raw_sha256'] and l['hashes']['seed']==p['seed_sha256'],'analyzer_hash':l['hashes']['analyzer']==sha(Path(__file__)),'native_extension_match':l['native_extension_sha256']==p['native_extension_sha256'],'engine_matches_source':p['engine_provenance']['source_match'] in ('own','shared') and not p['engine_provenance']['stale_rust'],'8_arms':len(d['arms'])==8,'instrumented_uninstrumented_progress_and_state_match':all(a['matches_uninstrumented']['progress'] and a['matches_uninstrumented']['activations'] for a in d['arms']),'counter_conservation':conservation,'selected_rule_present':all(a['selected_rule_counters'] and a['rule_name'] in {x['rule_name'] for x in a['per_rule_counters']} for a in d['arms']),'direct_nodesoftype_units_match_derived':all(x['direct_counter_matches_derived'] for x in summaries)}
 out={'run_id':'vision-global-fold-attribution-independent-audit-v1.1','raw_sha256':sha(RAW),'lock_sha256':sha(LOCK),'analyzer_sha256':sha(Path(__file__)),'by_size':summaries,'checks':checks,'pass':all(checks.values()),'claim_boundary':['Counters come from opt-in native instrumentation, whose timing overhead is excluded.','Four sizes, one seed, one synthetic single-sheet rule family; no asymptotic or natural-prevalence claim.','Candidate and Term counters attribute matcher and Term work, not every cost in the engine.']}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':str(OUT.relative_to(ROOT)),'checks':checks,'pass':out['pass'],'by_size':summaries},indent=2))
 if not out['pass']:raise SystemExit('counter attribution audit failed')
if __name__=='__main__':main()
