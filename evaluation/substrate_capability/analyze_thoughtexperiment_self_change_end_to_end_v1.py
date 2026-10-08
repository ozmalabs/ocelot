#!/usr/bin/env python3
"""Independent paired backend and full self-change lifecycle gates."""
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_self_change_end_to_end_v1_lock_20261005.json'
CAP=ROOT/'evaluation/reports/thoughtexperiment_self_change_end_to_end_v1_20261005.json'
OUT=CAP.with_name('thoughtexperiment_self_change_end_to_end_v1_analysis_20261005.json')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 l=json.loads(LOCK.read_text());c=json.loads(CAP.read_text());ws=c.get('workers',[]);errors=[];flat=[]
 if c.get('lock_sha256')!=sha(LOCK):errors.append('capture lock hash mismatch')
 if len(ws)!=3 or len({w.get('pid') for w in ws})!=3:errors.append('worker count/PID uniqueness')
 for w in ws:
  if w.get('sources_before')!=l['sources'] or w.get('sources_after')!=l['sources']:errors.append('source lock mismatch')
  if set(w.get('order',[]))!={'full_copy','shared_graph_pages'}:errors.append('backend pair/order missing')
  rows={r.get('backend'):r for r in w.get('results',[])}
  if set(rows)!={'full_copy','shared_graph_pages'}:errors.append('backend result pair incomplete')
  for backend,r in rows.items():
   flat.append(r)
   if r.get('faultprobe_target_uid')!=0 or r.get('target_uid_bound_after_selection') in (None,0):errors.append(f'{backend}: target identity was not withheld until post-selection CAS binding')
   if r.get('candidate_families')!=['threshold_adjustment'] or r.get('selected_family')!='threshold_adjustment' or r.get('selected_count')!=1:errors.append(f'{backend}: graph candidate generation/selection mismatch')
   if r.get('training_outputs')!=[True,False] or r.get('no_op_outputs')!=[False,False] or r.get('placebo_outputs')!=[False,False] or r.get('training_gain')!=10:errors.append(f'{backend}: measured training/no-op/placebo outcomes mismatch')
   if r.get('target_revision_after_rehearsal')!=0:errors.append(f'{backend}: rehearsal modified the primary target')
   if r.get('canary_outputs')!=[True,True,True,False,False]:errors.append(f'{backend}: disjoint canary outcome mismatch')
   rec=r.get('candidate_branch_patch_receipt') or {}
   if not(rec.get('revision')==1 and rec.get('previous_revision')==0 and rec.get('inverse_clause')=={'type':'Lit','value':False}):errors.append(f'{backend}: candidate branch patch receipt invalid')
   if r.get('commits')!=1 or r.get('committed_patch_status')!='committed' or r.get('target_revision_after_commit')!=1:errors.append(f'{backend}: Rust CAS commit did not occur exactly once')
   if r.get('final_outputs')!=[True,False] or not r.get('final_correct'):errors.append(f'{backend}: post-commit fresh task verification failed')
   t=r.get('timing_ns',{});keys=('training_rehearsal_candidate_noop_placebo','selection_tick','canary_rehearsal','commit_tick','final_verification')
   if any(not isinstance(t.get(k),int) or t[k]<=0 for k in keys):errors.append(f'{backend}: phase timing missing/invalid')
  if len(rows)==2:
   a,b=(rows[k] for k in ('full_copy','shared_graph_pages'))
   for k in ('candidate_families','proposed_clause','training_outputs','no_op_outputs','placebo_outputs','selected_family','canary_outputs','commits','target_revision_after_commit','committed_patch_status','final_outputs','candidate_branch_patch_receipt'):
    if a.get(k)!=b.get(k):errors.append(f'worker {w.get("worker")}: backend semantic mismatch in {k}')
 phases=flat[0]['timing_ns'].keys() if flat else []
 metrics={}
 for backend in ('full_copy','shared_graph_pages'):
  rows=[r for r in flat if r['backend']==backend]
  metrics[backend]={k:statistics.median([r['timing_ns'][k]/1e6 for r in rows]) for k in phases}
 result={'schema':'ThoughtexperimentSelfChangeEndToEndV1Analysis','gates_pass':not errors,'errors':errors,'summary':{'workers':len(ws),'unique_worker_pids':len({w.get('pid') for w in ws}),'paired_lifecycles':len(flat)//2,'all_lifecycles_pass':len(flat)==6 and not errors,'median_phase_ms_by_backend':metrics,'scope':'one supplied threshold-sensitivity signal and authored task; graph candidate, measured branch outcomes, held-out canary, guarded commit; no open-ended induction claim'}}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True));return int(bool(errors))
if __name__=='__main__':raise SystemExit(main())
