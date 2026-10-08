#!/usr/bin/env python3
"""Frozen-state orientation/phase panel with phase-aware response and exact cycles."""
from __future__ import annotations
import hashlib,json,platform,sys,time
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts'),str(ROOT/'runners/dsl/python')]
import substrate_vision_shared_substrate_multisheet_task_pilot_v1_4 as base
from domains.complex_cells import grating,binarize
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_VISION_SHARED_SUBSTRATE_MULTI_SHEET_TASK_PILOT_V1_9_PREREG_20260927.md'
CONTRACT=ROOT/'docs/research/engine_substrate/SUBSTRATE_VISION_RESPONSE_PHASE_CONTRACT_V1_9_20260927.md'
LOCK=ROOT/'evaluation/substrate_capability/vision_shared_substrate_multisheet_task_pilot_v1_9_lock_20260927.json'
OUT=ROOT/'evaluation/reports/substrate_vision_shared_substrate_multisheet_task_pilot_v1_9_20260927.json'
TRACE=OUT.with_suffix('.trace.jsonl')
PREPARED=ROOT/'evaluation/reports/substrate_vision_shared_substrate_multisheet_task_pilot_v1_7_prepared_graph_20260927.json'
V17=ROOT/'evaluation/reports/substrate_vision_shared_substrate_multisheet_task_pilot_v1_7_20260927.json'
L17=ROOT/'evaluation/substrate_capability/vision_shared_substrate_multisheet_task_pilot_v1_7_lock_20260927.json'
V18=ROOT/'evaluation/reports/substrate_vision_shared_substrate_multisheet_task_pilot_v1_8_20260927.json'
A18=ROOT/'evaluation/reports/substrate_vision_shared_substrate_multisheet_task_pilot_v1_8_analysis_20260927.json'
L18=ROOT/'evaluation/substrate_capability/vision_shared_substrate_multisheet_task_pilot_v1_8_lock_20260927.json'
MAX_PASSES=512;MAX_WORK=1_600_000;STEP=23010

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def source_inputs():
 return {'protocol_sha256':sha(PROTOCOL),'contract_sha256':sha(CONTRACT),'runner_sha256':sha(__file__),'prepared_checkpoint_sha256':sha(PREPARED),'v1_7_raw_sha256':sha(V17),'v1_7_lock_sha256':sha(L17),'v1_8_raw_sha256':sha(V18),'v1_8_analysis_sha256':sha(A18),'v1_8_lock_sha256':sha(L18),'base_inputs':base.source_inputs(),'python':platform.python_version(),'platform':platform.platform()}
def exact_digest(g):return hashlib.sha256(json.dumps(g,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def build(scope,prepared,expected_hash):
 s,(wa,wb),(ua,ub),top,_=base.build_pair(20260934,scope=='root_scoped');inner=s._inner
 inner.graph_from_dict(prepared)
 if base.graph_digest(inner.graph_to_dict())!=expected_hash:raise RuntimeError(f'{scope}: restored graph mismatch')
 return s,inner,(wa,wb),(ua,ub),top
def compact_state(s,ua,ub):
 def layer(units):
  return {k:[float(s.node(u)['attrs'].get(k,0.0)) for u in units] for k in ('act','theta','rate','act_step','rate_step','bursting')}
 return {'A':layer(ua),'B':layer(ub)}
def summarize(vals):
 a=np.asarray(vals,dtype=float)
 return {'sum':float(a.sum()),'min':float(a.min(initial=0.0)),'max':float(a.max(initial=0.0)),'active':int(np.count_nonzero(a>1e-9))}
def inputs(s,worlds,frames):
 active=[]
 for w,f in zip(worlds,frames):
  nodes=[w.cells[(r,c)] for r in range(w.h) for c in range(w.w)]
  on=[w.cells[(r,c)] for r in range(w.h) for c in range(w.w) if f[r,c]>.5]
  off=[w.cells[(r,c)] for r in range(w.h) for c in range(w.w) if f[r,c]<=.5]
  step=float(s.node(w.retina)['attrs'].get('step',0.0))+10.0;s.set_attr(w.retina,'step',step)
  if on:s.set_attr_many(on,'bursting',1.0);s.set_attr_many(on,'last_burst',step)
  if off:s.set_attr_many(off,'bursting',0.0);s.set_attr_many(off,'last_burst',-999.0)
  s.set_attr_many(nodes,'state','rested');active.append(int(len(on)))
 s.set_attr_many(s.nodes('Unit'),'bursting',0.0)
 return active
def run_condition(scope,name,af,bf,prepared,prepared_hash,trace_f):
 s,inner,(wa,wb),(ua,ub),top=build(scope,prepared,prepared_hash);pixels=inputs(s,(wa,wb),(af,bf));step=float(s.node(wa.retina)['attrs']['step'])
 observed=(sum(float(s.node(u)['attrs'].get('bursting',0.0)) for u in wa.cells.values()),sum(float(s.node(u)['attrs'].get('bursting',0.0)) for u in wb.cells.values()))
 if step!=STEP or float(s.node(wb.retina)['attrs']['step'])!=STEP:raise RuntimeError('unexpected endpoint Retina step')
 initial_graph=inner.graph_to_dict();d0=exact_digest(initial_graph);seen={d0:0};passes=[];rate_write=None;progress_sum=0;status='pass_cap_reached';cycle_start=None;cycle_period=None
 for ix in range(MAX_PASSES):
  before=compact_state(s,ua,ub);rep=inner.run_rules_report(1,False);progress=int(rep['progress_steps']);progress_sum+=progress
  after=compact_state(s,ua,ub);g=inner.graph_to_dict();digest=exact_digest(g)
  changed={layer:{k:sum(x!=y for x,y in zip(before[layer][k],after[layer][k])) for k in before[layer]} for layer in ('A','B')}
  row={'pass':ix+1,'status':rep['status'],'progress_steps':progress,'budget_overshoot':int(rep['budget_overshoot']),'graph_sha256':digest,'changed_units':changed,'state':after}
  passes.append(row);trace_f.write(json.dumps({'scope':scope,'condition':name,**row},separators=(',',':'))+'\n');trace_f.flush()
  if rate_write is None and all(all(int(x)==int(step) for x in after[layer]['rate_step']) for layer in ('A','B')):
   mismatch=[]
   for layer in ('A','B'):
    for i,(act,theta,rate) in enumerate(zip(after[layer]['act'],after[layer]['theta'],after[layer]['rate'])):
     err=abs(max(act-theta,0.0)-rate)
     if err>1e-9:mismatch.append({'layer':layer,'unit':i,'act':act,'theta':theta,'rate':rate,'error':err})
   rate_write={'pass':ix+1,'step':step,'state':after,'equation_mismatches':mismatch}
  if rep['status']=='fixed_point':status='fixed_point';break
  if digest in seen:status='repeated_graph_state';cycle_start=seen[digest];cycle_period=(ix+1)-cycle_start;break
  seen[digest]=ix+1
 if progress_sum>MAX_WORK:status='progress_cap_reached'
 if status=='pass_cap_reached':status='pass_cap_reached'
 if status=='repeated_graph_state':orbit=[r['state'] for r in passes if r['pass']>cycle_start]
 else:orbit=[]
 orbit_stats={}
 for layer in ('A','B'):
  orbit_stats[layer]={}
  for field in ('act','rate','theta'):
   if orbit:
    arr=np.asarray([o[layer][field] for o in orbit],dtype=float)
    orbit_stats[layer][field]={'unit_min':arr.min(axis=0).tolist(),'unit_max':arr.max(axis=0).tolist(),'unit_mean':arr.mean(axis=0).tolist()}
   elif status=='fixed_point':orbit_stats[layer][field]={'unit_min':passes[-1]['state'][layer][field],'unit_max':passes[-1]['state'][layer][field],'unit_mean':passes[-1]['state'][layer][field]}
 return {'scope':scope,'condition':name,'a_pixels':pixels[0],'b_pixels':pixels[1],'a_retinal_bursts':observed[0],'b_retinal_bursts':observed[1],'retina_step':step,'initial_graph_sha256':d0,'termination':status,'passes_completed':len(passes),'progress_steps':progress_sum,'cycle_start_pass_index':cycle_start,'cycle_period_passes':cycle_period,'rate_write_snapshot':rate_write,'terminal_state':passes[-1]['state'] if passes else None,'post_settle_orbit_statistics':orbit_stats,'pass_records':passes}
def main():
 if sys.argv[1:]==['--lock']:
  LOCK.parent.mkdir(parents=True,exist_ok=True);LOCK.write_text(json.dumps({'locked_inputs':source_inputs()},indent=2,sort_keys=True)+'\n');print(LOCK);return
 locked=source_inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text())['locked_inputs']!=locked:raise SystemExit('missing/stale source lock')
 c=json.loads(PREPARED.read_text());prepared=c['graph'];ph=c['prepared_graph_sha256']
 if base.graph_digest(prepared)!=ph:raise RuntimeError('prepared checkpoint hash mismatch')
 from scripts.rung8_lib import H,W
 blank=np.zeros((H,W),dtype=np.float32);conditions=[('both_blank',blank,blank)]
 for theta in (0.0,45.0,90.0,135.0):
  for phase in (0.0,float(np.pi/2)):
   f=binarize(grating((H,W),theta,phase,4.0));tag=f'theta_{int(theta)}_phase_{phase:.6f}'
   conditions.extend([(f'{tag}_B_only',blank,f),(f'{tag}_A_only',f,blank),(f'{tag}_both',f,f)])
 output={'run_id':'vision-shared-substrate-orientation-phase-response-panel-v1.9-20260927','locked_inputs':locked,'prepared_graph_sha256':ph,'conditions_per_scope':len(conditions),'scope_results':{'root_scoped':[],'global':[]}}
 OUT.parent.mkdir(parents=True,exist_ok=True)
 with TRACE.open('w') as tf:
  for scope in ('root_scoped','global'):
   for idx,(name,af,bf) in enumerate(conditions,1):
    row=run_condition(scope,name,af,bf,prepared,ph,tf);output['scope_results'][scope].append(row)
    OUT.with_suffix('.partial.json').write_text(json.dumps(output,indent=2,sort_keys=True)+'\n')
    print(f'panel scope={scope} condition={idx}/{len(conditions)} name={name} end={row["termination"]} passes={row["passes_completed"]} rate_mismatch={len(row["rate_write_snapshot"]["equation_mismatches"]) if row["rate_write_snapshot"] else "missing"}',flush=True)
 output['post_run_inputs']=source_inputs();output['source_stable']=output['post_run_inputs']==locked
 OUT.write_text(json.dumps(output,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'output':str(OUT.relative_to(ROOT)),'source_stable':output['source_stable'],'condition_count':len(conditions),'scopes':list(output['scope_results'])},indent=2))
 if not output['source_stable']:raise SystemExit('source drift')
if __name__=='__main__':main()
