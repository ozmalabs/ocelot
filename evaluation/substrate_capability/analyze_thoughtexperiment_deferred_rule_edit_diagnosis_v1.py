#!/usr/bin/env python3
"""Independent gates for deferred SetRuleClause diagnosis."""
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_deferred_rule_edit_diagnosis_v1_lock_20261005.json'
CAP=ROOT/'evaluation/reports/thoughtexperiment_deferred_rule_edit_diagnosis_v1_20261005.json'
OUT=CAP.with_name('thoughtexperiment_deferred_rule_edit_diagnosis_v1_analysis_20261005.json')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 lock=json.loads(LOCK.read_text()); cap=json.loads(CAP.read_text()); errors=[]
 if cap.get('lock_sha256')!=sha(LOCK):errors.append('capture lock hash mismatch')
 ws=cap.get('workers',[]); iso=cap.get('isolated',[])
 if len(ws)!=3 or len({w.get('pid') for w in ws})!=3:errors.append('worker count/PID uniqueness')
 if len(iso)!=12 or len({r.get('pid') for r in iso})!=12:errors.append('isolated count/PID uniqueness')
 allrows=[]
 for w in ws:
  if w.get('sources_before')!=lock['sources'] or w.get('sources_after')!=lock['sources']:errors.append('worker source lock mismatch')
  rows=w.get('rows',[]);controls=w.get('no_cause_controls',[])
  if {r.get('arm') for r in rows}!={'endpoint_blind','endpoint_rematch','target_trace','rule_change_receipt'}:errors.append('worker arm matrix incomplete')
  if len(controls)!=4:errors.append('worker controls incomplete')
  allrows+=rows
  for r in rows:
   if not r.get('primary_unchanged'):errors.append(f"worker {w.get('worker')} {r.get('arm')}: primary changed")
   if r.get('deferred_event_count')!=1 or len(r.get('deferred_rule_changes',[]))!=1:errors.append('expected one deferred committed rule change')
   ch=(r.get('deferred_rule_changes') or [{}])[0]
   if not(ch.get('committed') and ch.get('field')=='where' and ch.get('revision')==ch.get('previous_revision',-9)+1 and ch.get('content_hash')!=ch.get('previous_content_hash')):errors.append('rule change receipt invalid')
   if r.get('arm') in ('target_trace','rule_change_receipt') and [x.get('effect_index') for x in r.get('deferred_effect_origins',[])]!=[1]:errors.append('deferred source effect origin not exact')
   if r.get('arm') in ('target_trace','rule_change_receipt') and (r.get('candidates')!=[1] or r.get('found_necessary_effect')!=1 or r.get('attempts')!=1):errors.append(f"{r.get('arm')}: attribution/necessity failed")
   if r.get('arm')=='endpoint_blind' and (r.get('candidates')!=[0,1,2,3] or r.get('found_necessary_effect')!=1 or r.get('attempts')!=2):errors.append('blind baseline mismatch')
   if r.get('arm')=='endpoint_rematch' and (r.get('candidates')!=[0,1,2,3] or r.get('found_necessary_effect')!=1 or r.get('attempts')!=2):errors.append('rematch baseline mismatch')
   if r.get('found_necessary_effect')==1 and not any(x.get('effect_index')==1 and x.get('marker_after_omission') for x in r.get('outcomes',[])):errors.append('held-out probe necessity witness missing')
  for r in controls:
   if not r.get('primary_unchanged'):errors.append('control changed primary')
   if r.get('arm') in ('endpoint_rematch','target_trace','rule_change_receipt') and (r.get('candidates') or r.get('found_necessary_effect') is not None):errors.append('no-cause policy did not abstain')
 for r in iso:
  if r.get('sources_before')!=lock['sources'] or r.get('sources_after')!=lock['sources']:errors.append('isolated source lock mismatch')
  if not r.get('primary_unchanged'):errors.append('isolated primary changed')
  if r.get('arm') in ('target_trace','rule_change_receipt') and (r.get('candidates')!=[1] or r.get('found_necessary_effect')!=1):errors.append('isolated targeted outcome failed')
 summary={}
 for arm in ('endpoint_blind','endpoint_rematch','target_trace','rule_change_receipt'):
  vals=[r['wall_ns']/1e6 for r in iso if r['arm']==arm]
  summary[arm]={'isolated_replicates':len(vals),'median_wall_ms':statistics.median(vals) if vals else None,'candidate_attempts':sorted(r['attempts'] for r in iso if r['arm']==arm)}
 result={'schema':'ThoughtexperimentDeferredRuleEditDiagnosisV1Analysis','gates_pass':not errors,'errors':errors,'summary':{'workers':len(ws),'isolated_runs':len(iso),'unique_worker_pids':len({w.get('pid') for w in ws}),'unique_isolated_pids':len({r.get('pid') for r in iso}),'all_primary_states_unchanged':all(r.get('primary_unchanged') for r in allrows+iso),'policy_metrics':summary}}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True));return int(bool(errors))
if __name__=='__main__':raise SystemExit(main())
