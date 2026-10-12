#!/usr/bin/env python3
"""Timed, lower-overhead replay of the exact v2.1 multi-seed response panel."""
from __future__ import annotations
import hashlib,json,os,platform,resource,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts'),str(ROOT/'runners/dsl/python')]
import substrate_vision_shared_substrate_multisheet_task_pilot_v1_4 as base
import substrate_vision_shared_substrate_multisheet_task_pilot_v1_9 as panel
from domains.complex_cells import grating,binarize
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_VISION_MULTI_SEED_RESPONSE_COST_REPLAY_V2_2_PREREG_20260927.md'
LOCK=ROOT/'evaluation/substrate_capability/vision_multiseed_response_cost_replay_v2_2_lock_20260927.json'
OUT=ROOT/'evaluation/reports/vision_multiseed_response_cost_replay_v2_2_20260927.json'
CHECKPOINT_DIR=ROOT/'evaluation/reports/vision_multiseed_checkpoints_v2_0'
V21=ROOT/'evaluation/reports/vision_multiseed_response_replication_v2_1_20260927.json'
V21_ANALYSIS=ROOT/'evaluation/reports/vision_multiseed_response_replication_v2_1_analysis_20260927.json'
SEEDS=(20260935,20260936,20260937)
class NullTrace:
 def write(self,_):return 0
 def flush(self):return None
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def source_inputs():
 from domains.engine_provenance import engine_provenance
 from substrate_rs import _native
 return {'protocol_sha256':sha(PROTOCOL),'runner_sha256':sha(__file__),'v1_9_runner_sha256':sha(panel.__file__),'v1_9_contract_sha256':sha(panel.CONTRACT),'v1_9_prereg_sha256':sha(panel.PROTOCOL),'v1_9_source_lock_sha256':sha(panel.LOCK),'v2_1_response_sha256':sha(V21),'v2_1_analysis_sha256':sha(V21_ANALYSIS),'checkpoint_source_lock_sha256':sha(ROOT/'evaluation/substrate_capability/vision_multiseed_checkpoint_replication_v2_0_lock_20260927.json'),'checkpoints':{str(s):sha(CHECKPOINT_DIR/f'seed_{s}.json') for s in SEEDS},'native_extension_sha256':sha(Path(_native.__file__).resolve()),'engine_provenance':engine_provenance(),'python':platform.python_version(),'platform':platform.platform()}
def conditions():
 from scripts.rung8_lib import H,W
 blank=__import__('numpy').zeros((H,W),dtype=__import__('numpy').float32);out=[('both_blank',blank,blank)]
 np=__import__('numpy')
 for theta in (0.0,45.0,90.0,135.0):
  for phase in (0.0,float(__import__('math').pi/2)):
   frame=binarize(grating((H,W),theta,phase,4.0));tag=f'theta_{int(theta)}_phase_{phase:.6f}'
   out.extend([(f'{tag}_B_only',blank,frame),(f'{tag}_A_only',frame,blank),(f'{tag}_both',frame,frame)])
 return out
def rss_bytes():
 try:
  pages=int(Path('/proc/self/statm').read_text().split()[1]);return pages*os.sysconf('SC_PAGE_SIZE')
 except (OSError,ValueError,IndexError):return None
def peak_rss_bytes():
 value=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
 return int(value*(1024 if sys.platform.startswith('linux') else 1))
def timed_condition(seed,name,af,bf,graph,graph_hash):
 import numpy as np
 t0=time.perf_counter();cpu0=time.process_time();rss0=rss_bytes()
 s,inner,(wa,wb),(ua,ub),_=panel.build('root_scoped',graph,graph_hash)
 pixels=panel.inputs(s,(wa,wb),(af,bf));step=float(s.node(wa.retina)['attrs'].get('step',0.0))
 observed=(sum(float(s.node(u)['attrs'].get('bursting',0.0)) for u in wa.cells.values()),sum(float(s.node(u)['attrs'].get('bursting',0.0)) for u in wb.cells.values()))
 initial_digest=panel.exact_digest(inner.graph_to_dict());seen={initial_digest:0};progress_sum=0;engine_wall=0.0;engine_cpu=0.0;rate_write=None;status='pass_cap_reached';cycle_start=None;cycle_period=None;passes=0;terminal=None
 for ix in range(panel.MAX_PASSES):
  t1=time.perf_counter();c1=time.process_time();rep=inner.run_rules_report(1,False);engine_wall+=time.perf_counter()-t1;engine_cpu+=time.process_time()-c1
  passes=ix+1;progress=int(rep['progress_steps']);progress_sum+=progress;after=panel.compact_state(s,ua,ub)
  if rate_write is None and all(all(int(x)==int(step) for x in after[layer]['rate_step']) for layer in ('A','B')):
   mismatches=sum(abs(max(act-theta,0.0)-rate)>1e-9 for layer in ('A','B') for act,theta,rate in zip(after[layer]['act'],after[layer]['theta'],after[layer]['rate']))
   rate_write={'pass':passes,'step':step,'state':after,'equation_mismatches':mismatches}
  graph_now=inner.graph_to_dict();dg=panel.exact_digest(graph_now);terminal=after
  if rep['status']=='fixed_point':status='fixed_point';break
  if dg in seen:status='repeated_graph_state';cycle_start=seen[dg];cycle_period=passes-cycle_start;break
  seen[dg]=passes
 if progress_sum>panel.MAX_WORK:status='progress_cap_reached'
 cpu=time.process_time()-cpu0;wall=time.perf_counter()-t0
 return {'seed':seed,'condition':name,'a_pixels':pixels[0],'b_pixels':pixels[1],'a_retinal_bursts':observed[0],'b_retinal_bursts':observed[1],'retina_step':step,'checkpoint_sha256':graph_hash,'initial_graph_sha256':initial_digest,'termination':status,'passes_completed':passes,'progress_steps':progress_sum,'cycle_start_pass_index':cycle_start,'cycle_period_passes':cycle_period,'rate_write_snapshot':rate_write,'terminal_state':terminal,'engine_call_wall_seconds':engine_wall,'engine_call_process_cpu_seconds':engine_cpu,'condition_wall_seconds':wall,'condition_process_cpu_seconds':cpu,'rss_before_bytes':rss0,'rss_after_bytes':rss_bytes(),'process_peak_rss_bytes':peak_rss_bytes()}
def run_seed(seed,locked):
 part=OUT.with_name(OUT.stem+f'_seed_{seed}.json')
 data=json.loads(part.read_text()) if part.exists() else {'seed':seed,'locked_inputs':locked,'conditions':[]}
 if data.get('locked_inputs')!=locked:raise SystemExit(f'seed {seed}: partial output source lock mismatch')
 old=base.build_pair
 def build_for_seed(_ignored,scoped,_seed=seed):return old(_seed,scoped)
 base.build_pair=build_for_seed
 done={x['condition'] for x in data['conditions']}
 cp=json.loads((CHECKPOINT_DIR/f'seed_{seed}.json').read_text());graph=cp['graph'];gh=cp['prepared_graph_sha256']
 try:
  for ix,(name,af,bf) in enumerate(conditions(),1):
   if name in done:continue
   print(f'timed seed={seed} condition={ix}/25 name={name}',flush=True)
   row=timed_condition(seed,name,af,bf,graph,gh);data['conditions'].append(row);data['conditions'].sort(key=lambda x:next(i for i,c in enumerate(conditions()) if c[0]==x['condition']))
   data['source_stable']=source_inputs()==locked;data['process_peak_rss_bytes']=max(x['process_peak_rss_bytes'] for x in data['conditions'])
   part.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
   print(f'timed seed={seed} condition={ix}/25 end={row["termination"]} passes={row["passes_completed"]} closure_wall={row["engine_call_wall_seconds"]:.6f}s total_wall={row["condition_wall_seconds"]:.6f}s',flush=True)
 finally:base.build_pair=old
 data['complete']=len(data['conditions'])==25;data['source_stable']=source_inputs()==locked;part.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
 if not data['source_stable']:raise SystemExit(f'seed {seed}: source drift')
def main():
 if sys.argv[1:]==['--lock']:
  LOCK.parent.mkdir(parents=True,exist_ok=True);LOCK.write_text(json.dumps({'locked_inputs':source_inputs()},indent=2,sort_keys=True)+'\n');print(LOCK);return
 locked=source_inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text())['locked_inputs']!=locked:raise SystemExit('missing/stale source lock')
 if len(sys.argv)==3 and sys.argv[1]=='--seed':
  seed=int(sys.argv[2])
  if seed not in SEEDS:raise SystemExit('seed not registered')
  run_seed(seed,locked);return
 for seed in SEEDS:
  part=OUT.with_name(OUT.stem+f'_seed_{seed}.json')
  complete=part.exists() and json.loads(part.read_text()).get('complete') is True
  if not complete:subprocess.run([sys.executable,__file__,'--seed',str(seed)],cwd=ROOT,check=True)
 combined={'run_id':'vision-multiseed-response-cost-replay-v2.2-20260927','locked_inputs':locked,'seeds':{str(s):json.loads(OUT.with_name(OUT.stem+f'_seed_{s}.json').read_text()) for s in SEEDS},'source_stable':source_inputs()==locked,'complete':all(json.loads(OUT.with_name(OUT.stem+f'_seed_{s}.json').read_text()).get('complete') for s in SEEDS)}
 OUT.write_text(json.dumps(combined,indent=2,sort_keys=True)+'\n')
 if not combined['source_stable']:raise SystemExit('source drift')
 print(json.dumps({'output':str(OUT.relative_to(ROOT)),'complete':combined['complete'],'source_stable':combined['source_stable']},indent=2))
if __name__=='__main__':main()
