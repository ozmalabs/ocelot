#!/usr/bin/env python3
"""Independent analyzer for GenMint process-restart persistence/reuse v1."""
from __future__ import annotations
import hashlib,json,random,statistics,sys
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
from scripts import genmint_matrix_family_reuse_probe_v3 as fixtures
RAW=ROOT/'evaluation/reports/genmint_process_restart_reuse_v1_20260930.json'
LOCK=ROOT/'evaluation/substrate_capability/genmint_process_restart_reuse_v1_lock_20260930.json'
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_GENMINT_PROCESS_RESTART_REUSE_V1_PREREG_20260930.md'
RUNNER=ROOT/'scripts/genmint_process_restart_reuse_v1.py'
REPS=5;SEED=20260930;MATRICES=('prior_matrix','shearA','shearB');LAYOUTS=('adjacent_01','opposite_03');ARMS=('continuous_enabled','restart_enabled','restart_disabled');K=16
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def expected_data(matrix,layout):
 m=fixtures.MAPS[matrix];idx=set(fixtures.LAYOUTS[layout]);base=[];target=[]
 for i,(r,c) in enumerate(fixtures.POINTS):
  b,y=fixtures.make_row('p0' if i in idx else 'p1',r,c,m);base.append(b);target.append(y)
 return m,sorted(idx),base,target
def main():
 d=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());workers=d['workers']
 jobs=[(m,l,a,r) for m in MATRICES for l in LAYOUTS for a in ARMS for r in range(1,REPS+1)];rng=random.Random(SEED);rng.shuffle(jobs);schedule=[[m,l,a,r] for m,l,a,r in jobs]
 checks={'protocol_tag':d['schema']=='GenMintProcessRestartReuseV1','lock_matches':d['locked_inputs']==lock['inputs'] and d['lock_sha256']==sha(LOCK),'runner_hash_matches':lock['inputs']['source_sha256']['scripts/genmint_process_restart_reuse_v1.py']==sha(RUNNER),'analyzer_hash_matches':lock['inputs']['source_sha256']['scripts/analyze_genmint_process_restart_reuse_v1.py']==sha(Path(__file__)),'protocol_hash_matches':lock['inputs']['source_sha256']['docs/research/engine_substrate/SUBSTRATE_GENMINT_PROCESS_RESTART_REUSE_V1_PREREG_20260930.md']==sha(PROTOCOL),'exact_90_cell_schedule':len(workers)==90 and d['schedule']==schedule,'no_worker_failures':all('worker_failure' not in w for w in workers),'all_cells_present_once':len({(w.get('matrix_name'),w.get('layout'),w.get('arm'),w.get('replicate')) for w in workers})==90}
 inputs_ok=True;checkpoint_ok=True;pid_ok=True;all_enabled_routes=True;all_enabled_exact=True;restart_restore=True;disabled_no_acquisition=True;groups=defaultdict(list);by_cell={}
 pids=[]
 for w in workers:
  if 'worker_failure' in w:continue
  tr=w['train'];m,l=tr['matrix_name'],tr['layout'];rep=tr['replicate'];a=('continuous_enabled' if w['role']=='continuous' else ('restart_enabled' if tr['enabled'] else 'restart_disabled'));w.update({'matrix_name':m,'layout':l,'arm':a,'replicate':rep});groups[(m,l,a)].append(w);by_cell[(m,l,a,rep)]=w
  tr=w['train'];em,p0,b,t=expected_data(m,l)
  inputs_ok &= tr['matrix']==em and tr['p0_indices']==p0 and tr['training_base']==b and tr['training_target']==t and tr['replicate']==rep and len(w['applications'])==K
  pids.append(w.get('producer_pid'))
  if a=='continuous_enabled':pid_ok &= w.get('producer_pid')==w.get('consumer_pid')
  else:
   pids.append(w.get('consumer_pid'));pid_ok &= w.get('producer_pid')!=w.get('consumer_pid')
   restore=w.get('restore_checks',{});restart_restore &= all(restore.get(k) is True for k in ('graph_exact','grammar_exact','rules_semantically_exact')) and w.get('checkpoint_io_matches') is True
   checkpoint_ok &= w.get('checkpoint_bytes',0)>0 and len(w.get('checkpoint_sha256',''))==64 and restore.get('checkpoint_bytes')==w.get('checkpoint_bytes') and restore.get('checkpoint_sha256')==w.get('checkpoint_sha256')
  gen=tr.get('acquired_expected_generator')
  if a!='restart_disabled':
   all_enabled_routes &= gen is not None and all(x['route']=='training_acquired' and x['selected_generator']==gen['name'] and x['selected_matrix']==em for x in w['applications'])
   all_enabled_exact &= all(x['exact_target_match'] and x['independent_predictions']==x['target'] for x in w['applications'])
  else:disabled_no_acquisition &= gen is None and all(x['route']!='training_acquired' for x in w['applications'])
  for i,x in enumerate(w['applications']):
   coords=fixtures.HELDOUT[i];hb=[];ht=[]
   for j,(r,c) in enumerate(coords):
    x0,y0=fixtures.make_row('p0' if j%2==0 else 'p1',r,c,em);hb.append(x0);ht.append(y0)
   inputs_ok &= x['task_index']==i and x['base']==hb and x['target']==ht
 checks['independent_input_reconstruction']=bool(inputs_ok)
 checks['unique_process_ids']=len(pids)==len(set(pids)) and None not in pids
 checks['checkpoint_size_and_hash_reconcile']=bool(checkpoint_ok)
 checks['restart_graph_grammar_rule_parity']=bool(restart_restore)
 checks['enabled_generator_selected_for_all_heldouts']=bool(all_enabled_routes)
 checks['enabled_predictions_match_independent_targets']=bool(all_enabled_exact)
 checks['disabled_control_has_no_training_acquisition']=bool(disabled_no_acquisition)
 checks['five_replicates_each_cell']=len(groups)==18 and all(len(v)==REPS for v in groups.values())
 checks['repeat_outcomes_stable']=all(len({json.dumps((w['train']['train_status'],(w['train'].get('acquired_expected_generator') or {}).get('name'),[(x['status'],x['route'],x['selected_matrix'],x['exact_target_match']) for x in w['applications']]),sort_keys=True) for w in vs})==1 for vs in groups.values())
 paired=[]
 for m in MATRICES:
  for l in LAYOUTS:
   for r in range(1,REPS+1):
    c=by_cell[(m,l,'continuous_enabled',r)];re=by_cell[(m,l,'restart_enabled',r)];off=by_cell[(m,l,'restart_disabled',r)]
    def sig(w):return [(x['status'],x['route'],x['selected_generator'],x['selected_matrix'],x['independent_predictions'],x['exact_target_match']) for x in w['applications']]
    paired.append({'matrix':m,'layout':l,'replicate':r,'continuous_restart_semantic_parity':sig(c)==sig(re),'continuous_enabled_wall_s':c.get('outer_worker_wall_s'),'restart_enabled_wall_s':re.get('outer_worker_wall_s'),'restart_disabled_wall_s':off.get('outer_worker_wall_s'),'checkpoint_bytes':re.get('checkpoint_bytes'),'checkpoint_write_wall_s':re.get('checkpoint_write_wall_s'),'checkpoint_restore_wall_s':re.get('restore_wall_s'),'continuous_train_closure_s':c['train']['train_closure_wall_s'],'restart_train_closure_s':re['train']['train_closure_wall_s'],'continuous_application_closure_s':c['application_closure_wall_s'],'restart_application_closure_s':re['application_closure_wall_s'],'peak_rss_kib':{'continuous':c.get('peak_rss_kib'),'restart_enabled':re.get('peak_rss_kib'),'restart_disabled':off.get('peak_rss_kib')}})
 checks['continuous_vs_restart_enabled_semantic_parity']=all(x['continuous_restart_semantic_parity'] for x in paired)
 summaries=[]
 for arm in ARMS:
  xs=[w for w in workers if w.get('arm')==arm and 'worker_failure' not in w]
  def med(fn):return statistics.median(fn(w) for w in xs)
  summaries.append({'arm':arm,'sequences':len(xs),'median_outer_wall_s':med(lambda w:w['outer_worker_wall_s']),'median_boot_wall_s':med(lambda w:w['train']['boot_wall_s']),'median_train_closure_wall_s':med(lambda w:w['train']['train_closure_wall_s']),'median_application_closure_wall_s':med(lambda w:w['application_closure_wall_s']),'median_checkpoint_bytes':med(lambda w:w.get('checkpoint_bytes',0)),'median_checkpoint_write_ms':1000*med(lambda w:w.get('checkpoint_write_wall_s',0)),'median_restore_ms':1000*med(lambda w:w.get('restore_wall_s',0)),'median_peak_rss_kib':med(lambda w:w['peak_rss_kib']),'median_expected_generator_acquired':sum(bool(w['train'].get('acquired_expected_generator')) for w in xs),'exact_heldout_calls':sum(x['exact_target_match'] for w in xs for x in w['applications']),'heldout_calls':sum(len(w['applications']) for w in xs)})
 result={'analysis_schema':'GenMintProcessRestartReuseAnalysisV1','all_checks_pass':all(checks.values()),'checks':checks,'failed_checks':[k for k,v in checks.items() if not v],'raw_sha256':sha(RAW),'lock_sha256':sha(LOCK),'analyzer_sha256':sha(Path(__file__)),'summaries':summaries,'paired':paired,'claim_boundary':d['claim_boundary'],'limits':['one authored 2-D integer-linear generator family','six fixed matrix/layout cells; replicates estimate runtime reproducibility, not task diversity','process restart is a clean local JSON checkpoint boundary, not crash/power-loss durability','does not measure meta-learning, autonomous task selection, or general capability']}
 out=ROOT/'evaluation/reports/genmint_process_restart_reuse_v1_20260930_analysis.json';out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'analysis':str(out),'all_checks_pass':result['all_checks_pass'],'failed_checks':result['failed_checks'],'summaries':summaries},indent=2))
if __name__=='__main__':main()
