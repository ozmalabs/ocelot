#!/usr/bin/env python3
"""Independent audit of multi-edge access-to-owner mapping and wakeups."""
import hashlib,json,random,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/substrate_conversation_multi_boundary_v1_20260926.json'
LOCK=ROOT/'evaluation/substrate_capability/conversation_multi_boundary_lock_20260926.json'
SIZES=(2,4,8);REPS=3;ARMS=('full','mapped_required','omitted');SEED=20260930
PATHS={'protocol_sha256':ROOT/'docs/research/engine_substrate/SUBSTRATE_CONVERSATION_MULTI_BOUNDARY_PREREG_20260926.md','runner_sha256':ROOT/'scripts/substrate_conversation_multi_boundary_v1.py','analyzer_sha256':ROOT/'scripts/analyze_substrate_conversation_multi_boundary_v1.py','base_runner_sha256':ROOT/'scripts/substrate_conversation_boundary_wakeup_v1.py','seed_sha256':ROOT/'seeds/conversation_deliberation_phase4a.json','materializer_sha256':ROOT/'domains/conversation_deliberation.py','rewrite_sha256':ROOT/'runners/dsl/src/rewrite.rs','substrate_sha256':ROOT/'runners/dsl/src/substrate.rs','py_binding_sha256':ROOT/'runners/dsl/src/py.rs'}
PLANS={2:{'0':4.0},4:{'0':4.0,'1':5.0},8:{'0':4.0,'1':5.0,'5':8.0}}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 d=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());runs=d['runs'];expected=[(n,r,a) for n in SIZES for r in range(REPS) for a in ARMS];random.Random(SEED).shuffle(expected);cells={(x['size'],x['replicate'],x['arm']):x for x in runs}
 checks={'raw_lock_equal':d['locked_inputs']==lock,'lock_hash_equal':d['lock_sha256']==sha(LOCK),'source_hashes_current':lock=={k:sha(v) for k,v in PATHS.items()},'worker_count_27':len(runs)==27,'unique_pids':len({x['pid'] for x in runs})==27,'complete_randomized_matrix':len(cells)==27 and set(cells)==set(expected),'locked_schedule':d['schedule']==[list(x) for x in expected],'native_hash_consistent':len({x['native_extension_sha256'] for x in runs})==1 and runs[0]['native_extension_sha256']==d['native_extension_sha256']}
 mapping=True;baseline=True;terminal=True;local=True;timing=True
 for x in runs:
  n=x['size'];plan=PLANS[n];want_edges={j:sorted((j,j+1)) for j in map(int,plan)};want_frames=sorted({f for fs in want_edges.values() for f in fs})
  mapping &= x['mutation_plan']==plan and x['derived_readers_by_edge']=={str(j):v for j,v in want_edges.items()} and x['derived_affected_frames']==want_frames==x['expected_affected_frames'] and x['declared_mapping_matches_live'] and x['declared_rule_boundary_read']
  baseline &= x['baseline_fixed_point']=='fixed_point' and x['baseline_expected']
  terminal &= x['terminal_probe']['status']=='fixed_point' and x['terminal_probe']['progress_steps']==0
  local &= x['candidate_locality']
  timing &= isinstance(x['mapping_ns'],int) and x['mapping_ns']>=0 and isinstance(x['reopen_ns'],int) and x['reopen_ns']>=0
  baseline &= x['boundary_values_after']==plan and x['all_final_decisions']
 checks['live_reader_owner_map_matches_expected']=bool(mapping);checks['baseline_and_expected_terminal_states']=bool(baseline);checks['zero_work_full_fixed_point_probes']=bool(terminal);checks['mutable_candidates_are_frame_local']=bool(local);checks['mapping_and_reopen_timings_present']=bool(timing)
 pairs=[]
 for n in SIZES:
  for r in range(REPS):
   f,m,o=cells[n,r,'full'],cells[n,r,'mapped_required'],cells[n,r,'omitted']
   pairs.append({'size':n,'replicate':r,'baseline_equal':f['baseline_projection']==m['baseline_projection']==o['baseline_projection'],'mapped_matches_full':m['final_projection']==f['final_projection'],'mapped_probe_zero':m['recovery_progress']==0,'omission_detected':o['pre_repair_projection']!=f['final_projection'],'omitted_recovery_positive':o['recovery_progress']>0,'omitted_recovered':o['final_projection']==f['final_projection']})
 checks['baseline_equal_across_arms']=all(p['baseline_equal'] for p in pairs)
 checks['derived_required_frames_match_full']=all(p['mapped_matches_full'] and p['mapped_probe_zero'] for p in pairs)
 checks['omitted_frame_detected_every_pair']=all(p['omission_detected'] and p['omitted_recovery_positive'] for p in pairs)
 checks['omission_recovers_exactly']=all(p['omitted_recovered'] for p in pairs)
 summaries=[]
 for n in SIZES:
  for arm in ARMS:
   xs=[cells[n,r,arm] for r in range(REPS)]
   summaries.append({'frames':n,'arm':arm,'replicates':len(xs),'affected_frames':xs[0]['derived_affected_frames'],'median_mapping_us':statistics.median(x['mapping_ns'] for x in xs)/1000,'median_reopen_us':statistics.median(x['reopen_ns'] for x in xs)/1000,'median_mutation_closure_ms':statistics.median(x['wall_ns'] for x in xs)/1e6,'median_progress_steps':statistics.median(x['mutation_closure']['progress_steps'] for x in xs),'median_frame_turns':statistics.median(x['frame_turns'] for x in xs),'median_catchup_steps':statistics.median(x['recovery_progress'] for x in xs)})
 report={'checks':checks,'all_checks_pass':all(checks.values()),'pairs':pairs,'summaries':summaries,'raw_sha256':sha(RAW),'lock_sha256':sha(LOCK),'claim_boundary':d['claim_boundary']};out=ROOT/'evaluation/reports/substrate_conversation_multi_boundary_v1_analysis_20260926.json';out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps({'analysis':str(out),'all_checks_pass':report['all_checks_pass'],'checks':checks,'summaries':summaries},indent=2))
if __name__=='__main__':main()
