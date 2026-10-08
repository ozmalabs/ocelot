#!/usr/bin/env python3
"""Independent audit of native rule-write owner routing on conversation frames."""
import hashlib,json,random,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/substrate_conversation_native_write_owner_v1_20260926.json'
LOCK=ROOT/'evaluation/substrate_capability/conversation_native_write_owner_lock_20260926.json'
SIZES=(2,4,8);REPS=3;ARMS=('full_oracle','native_required','native_omitted');SEED=20261001
PATHS={'protocol_sha256':ROOT/'docs/research/engine_substrate/SUBSTRATE_CONVERSATION_NATIVE_WRITE_OWNER_PREREG_20260926.md','runner_sha256':ROOT/'scripts/substrate_conversation_native_write_owner_v1.py','analyzer_sha256':ROOT/'scripts/analyze_substrate_conversation_native_write_owner_v1.py','base_runner_sha256':ROOT/'scripts/substrate_conversation_readonly_boundary_v1.py','seed_sha256':ROOT/'seeds/conversation_deliberation_phase4a.json','materializer_sha256':ROOT/'domains/conversation_deliberation.py','rewrite_sha256':ROOT/'runners/dsl/src/rewrite.rs','substrate_sha256':ROOT/'runners/dsl/src/substrate.rs','py_binding_sha256':ROOT/'runners/dsl/src/py.rs'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 d=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());runs=d['runs'];expected=[(n,r,a) for n in SIZES for r in range(REPS) for a in ARMS];random.Random(SEED).shuffle(expected);cells={(x['size'],x['replicate'],x['arm']):x for x in runs}
 checks={'raw_lock_equal':d['locked_inputs']==lock,'lock_hash_equal':d['lock_sha256']==sha(LOCK),'source_hashes_current':lock=={k:sha(v) for k,v in PATHS.items()},'worker_count_27':len(runs)==27,'unique_pids':len({x['pid'] for x in runs})==27,'complete_randomized_matrix':len(cells)==27 and set(cells)==set(expected),'locked_schedule':d['schedule']==[list(x) for x in expected],'native_hash_consistent':len({x['native_extension_sha256'] for x in runs})==1 and runs[0]['native_extension_sha256']==d['native_extension_sha256']}
 checks['baseline_expected_fixed_points']=all(x['baseline_status']=='fixed_point' and x['baseline_expected'] for x in runs)
 checks['writer_fired_and_reset']=all(x['boundary_value']==4.0 and x['trigger_active']==0.0 for x in runs)
 checks['full_snapshot_oracle_exact']=all(x['oracle_report']['exact_graph_state_diff'] is True and x['oracle_report']['status']=='fixed_point' for x in runs if x['arm']=='full_oracle')
 checks['native_report_lists_direct_owners']=all(x['writer_report']['affected_microtheories']==x['expected_writer_owners'] and not x['writer_report']['unmapped_owner_ids'] for x in runs if x['arm']!='full_oracle')
 checks['native_scoped_writer_reports_complete']=all(x['writer_report']['progress_steps']>0 and not x['writer_report']['hit_progress_budget'] and not x['writer_report']['deferred_effects_pending'] and x['writer_report']['frame_notifications_complete'] is False for x in runs if x['arm']!='full_oracle')
 checks['all_final_probes_zero_work']=all(x['terminal_probe']['status']=='fixed_point' and x['terminal_probe']['progress_steps']==0 for x in runs)
 checks['all_expected_decisions']=all(x['all_final_decisions'] for x in runs)
 pairs=[]
 for n in SIZES:
  for r in range(REPS):
   f,req,omit=cells[n,r,'full_oracle'],cells[n,r,'native_required'],cells[n,r,'native_omitted'];fo=f['writer_report'];wo=req['writer_report']
   pairs.append({'size':n,'replicate':r,'native_owner_names_equal_exact_oracle':wo['affected_microtheories']==fo['affected_microtheories'],'native_nodes_subset_exact_graph_delta':set(wo['affected_nodes'])<=set(fo['affected_nodes']),'native_edges_subset_exact_graph_delta':set(map(tuple,wo['affected_edges']))<=set(map(tuple,fo['affected_edges'])),'required_projection_matches_full':req['final_projection']==f['final_projection'],'required_queue_is_both_consumers':req['notified_consumers']==[0,1],'omission_detected':omit['pre_repair_projection']!=f['final_projection'],'omission_catchup_positive':omit['recovery_steps']>0,'omission_recovers':omit['final_projection']==f['final_projection'],'omitted_queue_skips_frame_1':omit['notified_consumers']==[0]})
 checks['native_owner_set_matches_exact_oracle']=all(p['native_owner_names_equal_exact_oracle'] for p in pairs)
 checks['native_targets_cover_snapshot_diff']=all(p['native_nodes_subset_exact_graph_delta'] and p['native_edges_subset_exact_graph_delta'] for p in pairs)
 checks['required_native_owner_schedule_parity']=all(p['required_projection_matches_full'] and p['required_queue_is_both_consumers'] for p in pairs)
 checks['omitted_owner_control_detected_and_recovered']=all(p['omission_detected'] and p['omission_catchup_positive'] and p['omission_recovers'] and p['omitted_queue_skips_frame_1'] for p in pairs)
 summaries=[]
 for n in SIZES:
  for arm in ARMS:
   xs=[cells[n,r,arm] for r in range(REPS)]
   key='oracle_call_ns' if arm=='full_oracle' else 'writer_call_ns'
   summaries.append({'frames':n,'arm':arm,'replicates':3,'median_report_oracle_call_us':statistics.median(x[key] for x in xs)/1000 if arm=='full_oracle' else None,'median_native_writer_report_us':statistics.median(x[key] for x in xs)/1000 if arm!='full_oracle' else None,'median_consumer_schedule_us':statistics.median(x['consumer_schedule_ns'] for x in xs)/1000,'median_recovery_steps':statistics.median(x['recovery_steps'] for x in xs)})
 report={'checks':checks,'all_checks_pass':all(checks.values()),'pairs':pairs,'summaries':summaries,'raw_sha256':sha(RAW),'lock_sha256':sha(LOCK),'claim_boundary':d['claim_boundary']};out=ROOT/'evaluation/reports/substrate_conversation_native_write_owner_v1_analysis_20260926.json';out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps({'analysis':str(out),'all_checks_pass':report['all_checks_pass'],'checks':checks,'summaries':summaries},indent=2))
if __name__=='__main__':main()
