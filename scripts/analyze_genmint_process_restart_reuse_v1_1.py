#!/usr/bin/env python3
"""Amended independent analysis: bind omitted cell labels from locked schedule and split acquisition from persistence."""
from __future__ import annotations
import hashlib,json,random,statistics
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/genmint_process_restart_reuse_v1_20260930.json'
LOCK=ROOT/'evaluation/substrate_capability/genmint_process_restart_reuse_v1_lock_20260930.json'
RUNNER=ROOT/'scripts/genmint_process_restart_reuse_v1.py'
LOCKED_ANALYZER=ROOT/'scripts/analyze_genmint_process_restart_reuse_v1.py'
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_GENMINT_PROCESS_RESTART_REUSE_V1_PREREG_20260930.md'
MATRICES=('prior_matrix','shearA','shearB');LAYOUTS=('adjacent_01','opposite_03');ARMS=('continuous_enabled','restart_enabled','restart_disabled');REPS=5;K=16;SEED=20260930
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 d=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());ws=d['workers'];jobs=[(m,l,a,r) for m in MATRICES for l in LAYOUTS for a in ARMS for r in range(1,REPS+1)];random.Random(SEED).shuffle(jobs);schedule=[[m,l,a,r] for m,l,a,r in jobs]
 label_ok=len(ws)==90 and d['schedule']==schedule
 for i,w in enumerate(ws):
  if 'train' not in w:label_ok=False;continue
  tr=w['train'];arm='continuous_enabled' if w.get('role')=='continuous' else ('restart_enabled' if tr.get('enabled') else 'restart_disabled')
  derived=[tr.get('matrix_name'),tr.get('layout'),arm,tr.get('replicate')]
  if derived!=d['schedule'][i]:label_ok=False
  w.update({'matrix_name':derived[0],'layout':derived[1],'arm':derived[2],'replicate':derived[3]})
 by_cell={(w['matrix_name'],w['layout'],w['arm'],w['replicate']):w for w in ws if 'worker_failure' not in w};groups=defaultdict(list)
 for w in ws:
  if 'worker_failure' not in w:groups[(w['matrix_name'],w['layout'],w['arm'])].append(w)
 no_fail=all('worker_failure' not in w for w in ws)
 all_inputs=True;restored=True;ckpt=True;pid_list=[];route_when_acquired=True;exact_when_acquired=True;disabled_no_training_gen=True;repeat_stable=True
 for w in ws:
  if 'worker_failure' in w:continue
  m,l,a,rep=w['matrix_name'],w['layout'],w['arm'],w['replicate'];tr=w['train'];gen=tr.get('acquired_expected_generator');pid_list.append(w.get('producer_pid'))
  all_inputs &= len(w['applications'])==K and tr['enabled']==(a!='restart_disabled') and tr['replicate']==rep
  if a=='continuous_enabled':all_inputs &= w['producer_pid']==w['consumer_pid']
  else:
   pid_list.append(w.get('consumer_pid'));all_inputs &= w['producer_pid']!=w['consumer_pid']
   rc=w.get('restore_checks',{});restored &= rc.get('graph_exact') is True and rc.get('grammar_exact') is True and rc.get('rules_semantically_exact') is True and w.get('checkpoint_io_matches') is True
   ckpt &= w.get('checkpoint_bytes',0)>0 and rc.get('checkpoint_bytes')==w.get('checkpoint_bytes') and rc.get('checkpoint_sha256')==w.get('checkpoint_sha256')
  for app in w['applications']:
   if a!='restart_disabled' and gen:
    route_when_acquired &= app['route']=='training_acquired' and app['selected_generator']==gen['name'] and app['selected_matrix']==tr['matrix']
    exact_when_acquired &= app['exact_target_match'] and app['independent_predictions']==app['target']
   elif a=='restart_disabled':disabled_no_training_gen &= app['route']!='training_acquired'
 for cells in groups.values():
  signatures={json.dumps((w['train']['train_status'],(w['train'].get('acquired_expected_generator') or {}).get('name'),[(a['status'],a['route'],a['selected_matrix'],a['exact_target_match']) for a in w['applications']]),sort_keys=True) for w in cells}
  repeat_stable &= len(signatures)==1
 pids_unique=len(pid_list)==len(set(pid_list)) and None not in pid_list
 cells_complete=len(by_cell)==90 and len(groups)==18 and all(len(v)==REPS for v in groups.values())
 paired=[]
 def sig(w):return [(a['status'],a['route'],a['selected_generator'],a['selected_matrix'],a['independent_predictions'],a['exact_target_match']) for a in w['applications']]
 for m in MATRICES:
  for l in LAYOUTS:
   for r in range(1,REPS+1):
    c=by_cell[(m,l,'continuous_enabled',r)];re=by_cell[(m,l,'restart_enabled',r)];off=by_cell[(m,l,'restart_disabled',r)]
    paired.append({'matrix':m,'layout':l,'replicate':r,'continuous_restart_semantic_parity':sig(c)==sig(re),'acquisition_succeeded':c['train'].get('acquired_expected_generator') is not None and re['train'].get('acquired_expected_generator') is not None,'continuous_wall_s':c['outer_worker_wall_s'],'restart_wall_s':re['outer_worker_wall_s'],'disabled_wall_s':off['outer_worker_wall_s'],'restart_minus_continuous_ms':1000*(re['outer_worker_wall_s']-c['outer_worker_wall_s']),'restart_minus_disabled_ms':1000*(re['outer_worker_wall_s']-off['outer_worker_wall_s']),'checkpoint_bytes':re.get('checkpoint_bytes'),'checkpoint_write_ms':1000*re.get('checkpoint_write_wall_s',0),'restore_ms':1000*re.get('restore_wall_s',0),'peak_rss_kib':{'continuous':c['peak_rss_kib'],'restart':re['peak_rss_kib'],'disabled':off['peak_rss_kib']}})
 task_matrix_parity=all(x['continuous_restart_semantic_parity'] for x in paired)
 acquisition_by={}
 for m in MATRICES:
  for l in LAYOUTS:
   acquisition_by[f'{m}/{l}']={arm:sum(bool(by_cell[(m,l,arm,r)]['train'].get('acquired_expected_generator')) for r in range(1,REPS+1)) for arm in ('continuous_enabled','restart_enabled')}
 checks={'source_lock_matches_capture':d.get('lock_sha256')==sha(LOCK) and d.get('locked_inputs')==lock['inputs'],'locked_runner_and_original_analyzer_hashes_match':lock['inputs']['source_sha256']['scripts/genmint_process_restart_reuse_v1.py']==sha(RUNNER) and lock['inputs']['source_sha256']['scripts/analyze_genmint_process_restart_reuse_v1.py']==sha(LOCKED_ANALYZER),'preregistered_protocol_hash_matches':lock['inputs']['source_sha256']['docs/research/engine_substrate/SUBSTRATE_GENMINT_PROCESS_RESTART_REUSE_V1_PREREG_20260930.md']==sha(PROTOCOL),'exact_90_cell_schedule_and_label_binding':label_ok,'no_worker_failures':no_fail,'all_cells_present_once':cells_complete,'all_process_ids_unique':pids_unique,'reconstructed_inputs_and_arm_semantics_valid':all_inputs,'restart_graph_grammar_rule_parity':restored,'checkpoint_bytes_and_hash_reconcile':ckpt,'all_acquired_enabled_generators_selected_on_heldouts':route_when_acquired,'all_acquired_enabled_predictions_match_independent_targets':exact_when_acquired,'disabled_control_never_credited_with_training_acquisition':disabled_no_training_gen,'repeat_outcomes_stable':repeat_stable,'continuous_and_restart_enabled_semantics_match':task_matrix_parity}
 summaries=[]
 for arm in ARMS:
  xs=[w for w in ws if w.get('arm')==arm and 'worker_failure' not in w]
  def med(f):return statistics.median(f(w) for w in xs)
  acquired=sum(bool(w['train'].get('acquired_expected_generator')) for w in xs)
  summaries.append({'arm':arm,'sequences':len(xs),'acquisition_successes':acquired,'acquisition_failures':(len(xs)-acquired if arm!='restart_disabled' else None),'acquisition_rate':(acquired/len(xs) if arm!='restart_disabled' and xs else None),'median_end_to_end_wall_s':med(lambda w:w['outer_worker_wall_s']),'median_train_closure_wall_ms':1000*med(lambda w:w['train']['train_closure_wall_s']),'median_application_closure_wall_ms':1000*med(lambda w:w['application_closure_wall_s']),'median_checkpoint_bytes':med(lambda w:w.get('checkpoint_bytes',0)),'median_checkpoint_write_ms':1000*med(lambda w:w.get('checkpoint_write_wall_s',0)),'median_restore_ms':1000*med(lambda w:w.get('restore_wall_s',0)),'median_peak_rss_kib':med(lambda w:w['peak_rss_kib']),'correct_heldout_calls_all_routes':sum(a['exact_target_match'] for w in xs for a in w['applications']),'heldout_calls':sum(len(w['applications']) for w in xs),'route_counts':dict(Counter(a['route'] for w in xs for a in w['applications'])),'training_acquired_heldout_calls':sum(a['route']=='training_acquired' for w in xs for a in w['applications']),'training_acquired_exact_calls':sum(a['route']=='training_acquired' and a['exact_target_match'] for w in xs for a in w['applications'])})
 group_delta=defaultdict(list)
 for p in paired:group_delta[(p['matrix'],p['layout'])].append(p)
 stratum_summary=[]
 for (m,l),xs in group_delta.items():stratum_summary.append({'matrix':m,'layout':l,'pairs':len(xs),'acquisition_successes':sum(x['acquisition_succeeded'] for x in xs),'median_restart_minus_continuous_ms':statistics.median(x['restart_minus_continuous_ms'] for x in xs),'median_restart_minus_disabled_ms':statistics.median(x['restart_minus_disabled_ms'] for x in xs),'restart_faster_than_disabled_pairs':sum(x['restart_minus_disabled_ms']<0 for x in xs)})
 result={'analysis_schema':'GenMintProcessRestartReuseAnalysisV1_1','all_checks_pass':all(checks.values()),'checks':checks,'failed_checks':[k for k,v in checks.items() if not v],'raw_sha256':sha(RAW),'lock_sha256':sha(LOCK),'original_locked_analyzer_sha256':sha(LOCKED_ANALYZER),'amended_analyzer_sha256':sha(Path(__file__)),'acquisition_by_matrix_layout':acquisition_by,'summaries':summaries,'strata':stratum_summary,'paired':paired,'pooled_paired_costs':{'restart_minus_continuous_median_ms':statistics.median(x['restart_minus_continuous_ms'] for x in paired),'restart_minus_disabled_median_ms':statistics.median(x['restart_minus_disabled_ms'] for x in paired),'restart_faster_than_continuous_pairs':sum(x['restart_minus_continuous_ms']<0 for x in paired),'restart_faster_than_disabled_pairs':sum(x['restart_minus_disabled_ms']<0 for x in paired),'pairs':len(paired),'acquired_pair_median_restart_minus_disabled_ms':statistics.median(x['restart_minus_disabled_ms'] for x in paired if x['acquisition_succeeded']),'acquired_pair_restart_faster_than_disabled_pairs':sum(x['restart_minus_disabled_ms']<0 for x in paired if x['acquisition_succeeded']),'acquired_pairs':sum(x['acquisition_succeeded'] for x in paired)},'limits':['six fixed 2-D integer-linear matrix/layout cells; five repeats measure reproducibility, not task diversity','only acquisition-success sequences count for post-acquisition selected-reuse claims','local graph/grammar/rule JSON checkpoint is not crash or power-loss durability','does not measure substrate meta-learning, autonomous task selection, natural-task prevalence, or general capability']}
 out=ROOT/'evaluation/reports/genmint_process_restart_reuse_v1_1_analysis_20260930.json';out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'analysis':str(out),'all_checks_pass':result['all_checks_pass'],'failed_checks':result['failed_checks'],'acquisition_by_cell':acquisition_by,'summaries':summaries,'strata':stratum_summary,'pooled_paired_costs':result['pooled_paired_costs']},indent=2))
if __name__=='__main__':main()
