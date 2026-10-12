#!/usr/bin/env python3
"""Passwise state trace and sliced-closure equivalence for v1.7 fixture."""
from __future__ import annotations
import hashlib,json,platform,sys,time
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts'),str(ROOT/'runners/dsl/python')]
import substrate_vision_shared_substrate_multisheet_task_pilot_v1_4 as base
from domains.complex_cells import grating,binarize
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_VISION_SHARED_SUBSTRATE_MULTI_SHEET_TASK_PILOT_V1_8_PREREG_20260927.md'
LOCK=ROOT/'evaluation/substrate_capability/vision_shared_substrate_multisheet_task_pilot_v1_8_lock_20260927.json'
OUT=ROOT/'evaluation/reports/substrate_vision_shared_substrate_multisheet_task_pilot_v1_8_20260927.json'
PREPARED=ROOT/'evaluation/reports/substrate_vision_shared_substrate_multisheet_task_pilot_v1_7_prepared_graph_20260927.json'
RAW17=ROOT/'evaluation/reports/substrate_vision_shared_substrate_multisheet_task_pilot_v1_7_20260927.json'
LOCK17=ROOT/'evaluation/substrate_capability/vision_shared_substrate_multisheet_task_pilot_v1_7_lock_20260927.json'
MAX_PASSES=512

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def source_inputs():
 return {'protocol_sha256':sha(PROTOCOL),'runner_sha256':sha(__file__),'prepared_checkpoint_sha256':sha(PREPARED),'v1_7_raw_sha256':sha(RAW17),'v1_7_lock_sha256':sha(LOCK17),'base_inputs':base.source_inputs(),'python':platform.python_version(),'platform':platform.platform()}
def exact_digest(graph):return hashlib.sha256(json.dumps(graph,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def state(s,ua,ub):
 return {str(u):{k:s.node(u)['attrs'].get(k) for k in ('act','theta','rate','act_step','rate_step','bursting')} for u in ua+ub}
def build(scope,prepared,expected_hash):
 from scripts.substrate_vision_shared_substrate_multisheet_task_pilot_v1_4 import build_pair
 s,(wa,wb),(ua,ub),top,_=build_pair(20260934,scope=='root_scoped');inner=s._inner
 if top['retina_ids']!=json.loads(RAW17.read_text())['topology']['retina_ids'] or top['unit_ids']!=json.loads(RAW17.read_text())['topology']['unit_ids']:raise RuntimeError(f'{scope}: identity mismatch')
 inner.graph_from_dict(prepared)
 if base.graph_digest(inner.graph_to_dict())!=expected_hash:raise RuntimeError(f'{scope}: prepared graph restore mismatch')
 return s,inner,(wa,wb),(ua,ub),top

def inputs_for(s,worlds,frames):
 for w,frame in zip(worlds,frames):
  nodes=[w.cells[(r,c)] for r in range(w.h) for c in range(w.w)]
  on=[w.cells[(r,c)] for r in range(w.h) for c in range(w.w) if frame[r,c]>.5]
  off=[w.cells[(r,c)] for r in range(w.h) for c in range(w.w) if frame[r,c]<=.5]
  step=float(s.node(w.retina)['attrs'].get('step',0.0))+10.0;s.set_attr(w.retina,'step',step)
  if on:s.set_attr_many(on,'bursting',1.0);s.set_attr_many(on,'last_burst',step)
  if off:s.set_attr_many(off,'bursting',0.0);s.set_attr_many(off,'last_burst',-999.0)
  s.set_attr_many(nodes,'state','rested')
 s.set_attr_many(s.nodes('Unit'),'bursting',0.0)

def run_full(s,inner,worlds,frames):
 inputs_for(s,worlds,frames);report=inner.run_rules_report(200000,True);return report,exact_digest(inner.graph_to_dict())
def run_sliced(s,inner,worlds,units,frames,label,trace_file=None):
 inputs_for(s,worlds,frames);ua,ub=units;start=state(s,ua,ub);d0=exact_digest(inner.graph_to_dict());seen={d0:0};passes=[];status='';cycle_start=None;cycle_period=None;sum_progress=0
 for idx in range(MAX_PASSES):
  before=state(s,ua,ub);report=inner.run_rules_report(1,False);sum_progress+=int(report['progress_steps']);after=state(s,ua,ub);dig=exact_digest(inner.graph_to_dict())
  row={'pass':idx+1,'status':report['status'],'progress_steps':int(report['progress_steps']),'budget_overshoot':int(report['budget_overshoot']),'passes_completed':int(report['passes_completed']),'before':before,'after':after,'graph_sha256':dig}
  passes.append(row)
  if trace_file:
   trace_file.write(json.dumps({'scope_condition':label,**row},separators=(',',':'))+'\n');trace_file.flush()
  if report['status']=='fixed_point':status='fixed_point';break
  if dig in seen:
   status='repeated_graph_state';cycle_start=seen[dig];cycle_period=(idx+1)-cycle_start;break
  seen[dig]=idx+1
 else:status='pass_cap_reached'
 return {'scope_condition':label,'initial_graph_sha256':d0,'initial_state':start,'status':status,'cycle_start_pass_index':cycle_start,'cycle_period_passes':cycle_period,'passes':passes,'passes_completed':len(passes),'progress_steps_sum':sum_progress,'terminal_graph_sha256':exact_digest(inner.graph_to_dict())}

def main():
 if sys.argv[1:]==['--lock']:
  LOCK.parent.mkdir(parents=True,exist_ok=True);LOCK.write_text(json.dumps({'locked_inputs':source_inputs()},indent=2,sort_keys=True)+'\n');print(LOCK);return
 locked=source_inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text())['locked_inputs']!=locked:raise SystemExit('missing/stale source lock')
 checkpoint=json.loads(PREPARED.read_text());prepared=checkpoint['graph'];prepared_hash=checkpoint['prepared_graph_sha256']
 if base.graph_digest(prepared)!=prepared_hash:raise RuntimeError('prepared checkpoint digest mismatch')
 from scripts.rung8_lib import H,W
 blank=np.zeros((H,W),dtype=np.float32);a=binarize(grating((H,W),45.0,.3,4.0));b=binarize(grating((H,W),0.0,0.0,4.0))
 conds=[('both_blank',blank,blank),('b_only_exact',blank,b),('a_only_exact',a,blank),('both_exact',a,b)]
 out={'run_id':'vision-shared-substrate-closure-pass-trace-v1.8-20260927','locked_inputs':locked,'prepared_graph_sha256':prepared_hash,'scopes':{},'preflight':[]}
 tracepath=OUT.with_suffix('.trace.jsonl');OUT.parent.mkdir(parents=True,exist_ok=True)
 with tracepath.open('w') as tf:
  # Preflight: exact parity between ordinary closure and one-pass-sliced execution.
  for scope,name,af,bf in (('root_scoped','b_only_exact',blank,b),('global','both_exact',a,b)):
   s,inner,(wa,wb),(ua,ub),_=build(scope,prepared,prepared_hash)
   full_report,full_hash=run_full(s,inner,(wa,wb),(af,bf));full_progress=int(full_report['progress_steps']);full_passes=int(full_report['passes_completed']);full_status=full_report['status']
   # Rebuild a fresh twin so scheduler scratch state is not carried into the sliced arm.
   st,si,(wta,wtb),(uta,utb),_=build(scope,prepared,prepared_hash);slice_result=run_sliced(st,si,(wta,wtb),(uta,utb),(af,bf),f'preflight_result_{scope}_{name}',tf)
   pre={'scope':scope,'condition':name,'full_status':full_status,'full_progress_steps':full_progress,'full_passes':full_passes,'full_graph_sha256':full_hash,'sliced_status':slice_result['status'],'sliced_progress_steps':slice_result['progress_steps_sum'],'sliced_passes':slice_result['passes_completed'],'sliced_graph_sha256':slice_result['terminal_graph_sha256'],'graph_equal':full_hash==slice_result['terminal_graph_sha256'],'status_equal':full_status==slice_result['status'],'work_equal':full_progress==slice_result['progress_steps_sum'] and full_passes==slice_result['passes_completed']}
   out['preflight'].append(pre)
  out['slicing_equivalence']=all(x['graph_equal'] and x['status_equal'] and x['work_equal'] for x in out['preflight'])
  if not out['slicing_equivalence']:
   out['trace_interpretation_valid']=False
   OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');raise SystemExit('one-pass slicing failed full-closure equivalence; traces preserved, interpretation withheld')
  for scope in ('root_scoped','global'):
   rows=[]
   for name,af,bf in conds:
    s,inner,(wa,wb),(ua,ub),top=build(scope,prepared,prepared_hash)
    rr=run_sliced(s,inner,(wa,wb),(ua,ub),(af,bf),f'{scope}_{name}',tf);rr.update({'condition':name,'scope':scope,'a_pixels':int(np.count_nonzero(af)),'b_pixels':int(np.count_nonzero(bf)),'retina_step_before':23000,'a_unit_ids':[str(x) for x in ua],'b_unit_ids':[str(x) for x in ub]});rows.append(rr)
    OUT.with_suffix('.partial.json').write_text(json.dumps({'slicing_equivalence':True,'trace_file':str(tracepath.relative_to(ROOT)),'scope_results':out['scopes']|{scope:rows}},indent=2,sort_keys=True)+'\n')
    print(f'trace scope={scope} condition={name} status={rr["status"]} passes={rr["passes_completed"]} cycle={rr["cycle_start_pass_index"]}/{rr["cycle_period_passes"]}',flush=True)
   out['scopes'][scope]=rows
  out['trace_interpretation_valid']=True
 out['post_run_inputs']=source_inputs();out['source_stable']=out['post_run_inputs']==locked
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'output':str(OUT.relative_to(ROOT)),'source_stable':out['source_stable'],'slicing_equivalence':out['slicing_equivalence'],'trace_file':str(tracepath.relative_to(ROOT))},indent=2))
 if not out['source_stable']:raise SystemExit('source drift')
if __name__=='__main__':main()
