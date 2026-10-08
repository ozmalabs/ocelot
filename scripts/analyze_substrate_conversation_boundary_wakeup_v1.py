#!/usr/bin/env python3
"""Independent full/required/omitted boundary-wakeup audit."""
import hashlib,json,random
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/substrate_conversation_boundary_wakeup_v1_20260926.json'
LOCK=ROOT/'evaluation/substrate_capability/conversation_boundary_wakeup_lock_20260926.json'
SIZES=(2,4,8);REPS=3;ARMS=('full','required','omitted');SEED=20260929
PATHS={'protocol_sha256':ROOT/'docs/research/engine_substrate/SUBSTRATE_CONVERSATION_BOUNDARY_WAKEUP_PREREG_20260926.md','runner_sha256':ROOT/'scripts/substrate_conversation_boundary_wakeup_v1.py','analyzer_sha256':ROOT/'scripts/analyze_substrate_conversation_boundary_wakeup_v1.py','base_runner_sha256':ROOT/'scripts/substrate_conversation_readonly_boundary_v1.py','seed_sha256':ROOT/'seeds/conversation_deliberation_phase4a.json','materializer_sha256':ROOT/'domains/conversation_deliberation.py','rewrite_sha256':ROOT/'runners/dsl/src/rewrite.rs','substrate_sha256':ROOT/'runners/dsl/src/substrate.rs','py_binding_sha256':ROOT/'runners/dsl/src/py.rs'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 d=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());runs=d['runs'];expected=[(n,r,a) for n in SIZES for r in range(REPS) for a in ARMS];random.Random(SEED).shuffle(expected);cells={(x['size'],x['replicate'],x['arm']):x for x in runs}
 checks={'raw_lock_equal':d['locked_inputs']==lock,'lock_hash_equal':d['lock_sha256']==sha(LOCK),'source_hashes_current':lock=={k:sha(v) for k,v in PATHS.items()},'worker_count_27':len(runs)==27,'unique_worker_pids':len({x['pid'] for x in runs})==27,'complete_balanced_matrix':len(cells)==27 and set(cells)==set(expected),'locked_randomized_schedule':d['schedule']==[list(x) for x in expected],'native_hash_consistent':len({x['native_extension_sha256'] for x in runs})==1 and runs[0]['native_extension_sha256']==d['native_extension_sha256']}
 for x in runs:
  n=x['size'];checks.setdefault('baseline_fixed_points_expected',True);checks['baseline_fixed_points_expected'] &= x['baseline_fixed_point']=='fixed_point' and x['baseline_expected']
  checks.setdefault('boundary_ownership',True);checks['boundary_ownership'] &= x['boundary_count']==n-1 and x['boundary_owner_sizes']==[2]*(n-1)
  checks.setdefault('scoring_rule_reads_shared_value',True);checks['scoring_rule_reads_shared_value'] &= x['score_rule_boundary_read']
  checks.setdefault('closure_preserves_evidence',True);checks['closure_preserves_evidence'] &= x['mutated_boundary_value']==4.0
  checks.setdefault('all_terminal_probes_zero_work_fixed_point',True);checks['all_terminal_probes_zero_work_fixed_point'] &= x['terminal_full_probe']['status']=='fixed_point' and x['terminal_full_probe']['progress_steps']==0
  if x['arm']=='full':checks.setdefault('full_arm_expected_winners',True);checks['full_arm_expected_winners'] &= x['all_final_decisions']
  if x['arm']=='required':checks.setdefault('required_arm_schedule_and_state',True);checks['required_arm_schedule_and_state'] &= x['executed_frames']==[0,1] and x['omitted_frames']==[] and x['all_final_decisions'] and x['recovery_progress']==0
  if x['arm']=='omitted':checks.setdefault('omitted_arm_schedule',True);checks['omitted_arm_schedule'] &= x['executed_frames']==[0] and x['omitted_frames']==[1]
 pairs=[]
 for n in SIZES:
  for r in range(REPS):
   f,req,omit=cells[n,r,'full'],cells[n,r,'required'],cells[n,r,'omitted']
   pairs.append({'size':n,'replicate':r,'baseline_equal':f['baseline_projection']==req['baseline_projection']==omit['baseline_projection'],'required_matches_full':req['final_projection']==f['final_projection'],'required_recovery_zero':req['recovery_progress']==0,'omission_detected':omit['pre_repair_projection']!=f['final_projection'],'omitted_recovery_positive':omit['recovery_progress']>0,'omitted_recovers_exactly':omit['final_projection']==f['final_projection']})
 checks['baseline_projection_equal_all_arms']=all(p['baseline_equal'] for p in pairs)
 checks['required_notifications_match_full']=all(p['required_matches_full'] and p['required_recovery_zero'] for p in pairs)
 checks['omitted_wakeup_detected_all_cases']=all(p['omission_detected'] and p['omitted_recovery_positive'] for p in pairs)
 checks['omitted_cases_recover_exactly']=all(p['omitted_recovers_exactly'] for p in pairs)
 report={'checks':checks,'all_checks_pass':all(checks.values()),'pairs':pairs,'raw_sha256':sha(RAW),'lock_sha256':sha(LOCK),'claim_boundary':d['claim_boundary']};out=ROOT/'evaluation/reports/substrate_conversation_boundary_wakeup_v1_analysis_20260926.json';out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps({'analysis':str(out),'all_checks_pass':report['all_checks_pass'],'checks':checks,'pairs':pairs},indent=2))
if __name__=='__main__':main()
