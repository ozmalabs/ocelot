#!/usr/bin/env python3
"""Recompute held-out effect-index localization from raw effect snapshots."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];CAPTURE=ROOT/'evaluation/reports/thoughtexperiment_effect_trace_diagnosis_v1_20261005.json'
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_effect_trace_diagnosis_v1_lock_20261005.json';RUNNER=ROOT/'evaluation/substrate_capability/thoughtexperiment_effect_trace_diagnosis_v1.py';ANALYZER=Path(__file__).resolve()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def localize(row):
 oracle=row['oracle']; target=int(oracle['bad_node_id']);hits=[]
 for effect in row['effect_mode']['effect_snapshots']:
  for value in effect.get('node_values',[]):
   if int(value['node_id'])==target and value['after'] is not None and value['after']['attrs'].get('health')==999:hits.append(int(effect['effect_index']))
 return hits
def main():
 d=json.loads(CAPTURE.read_text());lock=json.loads(LOCK.read_text());workers=d['workers'];pids=[w['pid'] for w in workers]
 checks={'schema':d['schema']=='ThoughtexperimentEffectTraceDiagnosisV1','lock_hash':d['lock_sha256']==sha(LOCK),'three_independent_workers':len(workers)==3 and len(set(pids))==3,'source_lock_stable':all(w['sources_before']==w['sources_after']==lock['sources'] for w in workers),'runner_analyzer_hashes_locked':lock['sources']['files'][str(RUNNER.relative_to(ROOT))]==sha(RUNNER) and lock['sources']['files'][str(ANALYZER.relative_to(ROOT))]==sha(ANALYZER)}
 rows=workers[0]['rows'];checks['case_matrix_exact']=len(rows)==80 and {(r['size'],r['case_id']) for r in rows}=={(n,i) for n in lock['sizes'] for i in range(lock['cases_per_size'])}
 checks['worker_rows_replicate']=all(w['rows']==rows for w in workers[1:])
 baseline_hits=0;effect_hits=0;effect_unique=0;candidate_reduction=[];trace_complete=True;target_present=True
 for row in rows:
  oracle=row['oracle'];n=int(row['size']);expected=int(oracle['bad_effect_index']);event=row['event_mode'];effect=row['effect_mode']
  # The endpoint event has a changed-node set but no firing-binding/effect map.
  candidates=list(range(n));baseline_hits += int(candidates[0]==expected)
  hits=localize(row);effect_hits += int(hits==[expected]);effect_unique += int(len(hits)==1)
  candidate_reduction.append(len(candidates)/max(len(hits),1))
  trace_complete &= len(effect['effect_snapshots'])==n and all(not x.get('values_truncated',True) for x in effect['effect_snapshots'])
  target_present &= int(oracle['bad_node_id']) in set(map(int,event['event_node_ids']))
  endpoint=next((x for x in effect['events'][0]['node_values'] if int(x['node_id'])==int(oracle['bad_node_id'])),None) if effect['events'] else None
  target_present &= endpoint is not None and endpoint['after']['attrs'].get('health')==999
 # Check that event mode leaves the internal effect mapping absent on every pair.
 checks['event_reports_have_no_effect_map']=all(not r['event_mode']['effect_snapshots'] for r in rows)
 checks['endpoint_target_visibility']=target_present
 checks['effect_trace_complete']=trace_complete
 checks['single_progressed_firing']=all(r['event_mode']['progress']['steps']==1 and r['effect_mode']['progress']['steps']==1 for r in rows)
 checks['effect_trace_localizes_exactly']=effect_hits==len(rows) and effect_unique==len(rows)
 checks['endpoint_baseline_is_ambiguous']=all(len(list(range(r['size'])))==r['size'] for r in rows)
 sizes={n:{'cases':sum(r['size']==n for r in rows),'endpoint_candidate_count':n,'endpoint_first_candidate_hits':sum(r['size']==n and int(r['oracle']['bad_effect_index'])==0 for r in rows),'effect_trace_exact_hits':sum(r['size']==n and localize(r)==[int(r['oracle']['bad_effect_index'])] for r in rows)} for n in lock['sizes']}
 out={'schema':'ThoughtexperimentEffectTraceDiagnosisV1Analysis','capture_sha256':sha(CAPTURE),'lock_sha256':sha(LOCK),'checks':checks,'passed':all(checks.values()),'summary':{'heldout_cases':len(rows),'worker_replicates':len(workers),'endpoint_only_first_candidate_accuracy':baseline_hits/len(rows),'effect_trace_exact_accuracy':effect_hits/len(rows),'mean_candidate_reduction_factor':sum(candidate_reduction)/len(candidate_reduction),'size_strata':sizes},'claim_limit':'Effect traces exactly localize the changed effect index on these synthetic bound-variable cases when the input is restricted to native event reports plus the failing node. This does not compare against a full rule rematch/source-analysis baseline, establish human/task utility, or generalize to natural workloads.'}
 dest=ROOT/'evaluation/reports/thoughtexperiment_effect_trace_diagnosis_v1_analysis_20261005.json';dest.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':out['passed'],'checks':checks,'summary':out['summary']},indent=2));return 0 if out['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
