#!/usr/bin/env python3
"""Native full-closure replay of v1.9 global joint-sheet cap cases."""
from __future__ import annotations
import hashlib,json,math,platform,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'scripts'),str(ROOT/'runners/dsl/python')]
import substrate_vision_shared_substrate_multisheet_task_pilot_v1_4 as base
import substrate_vision_shared_substrate_multisheet_task_pilot_v1_9 as v19
from domains.complex_cells import grating,binarize
PR=ROOT/'docs/research/engine_substrate/SUBSTRATE_VISION_SHARED_SUBSTRATE_MULTI_SHEET_TASK_PILOT_V1_9_1_AMENDMENT_20260927.md'
LOCK=ROOT/'evaluation/substrate_capability/vision_shared_substrate_multisheet_task_pilot_v1_9_1_lock_20260927.json'
OUT=ROOT/'evaluation/reports/substrate_vision_shared_substrate_multisheet_task_pilot_v1_9_1_20260927.json'
RAW19=ROOT/'evaluation/reports/substrate_vision_shared_substrate_multisheet_task_pilot_v1_9_20260927.json'
AN19=ROOT/'evaluation/reports/substrate_vision_shared_substrate_multisheet_task_pilot_v1_9_analysis_20260927.json'
L19=ROOT/'evaluation/substrate_capability/vision_shared_substrate_multisheet_task_pilot_v1_9_lock_20260927.json'
MAX=1_600_000

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def source_inputs():return {'amendment_sha256':sha(PR),'runner_sha256':sha(__file__),'v1_9_raw_sha256':sha(RAW19),'v1_9_analysis_sha256':sha(AN19),'v1_9_lock_sha256':sha(L19),'base_inputs':base.source_inputs(),'platform':platform.platform(),'python':platform.python_version()}
def main():
 if sys.argv[1:]==['--lock']:
  LOCK.parent.mkdir(parents=True,exist_ok=True);LOCK.write_text(json.dumps({'locked_inputs':source_inputs()},indent=2,sort_keys=True)+'\n');print(LOCK);return
 locked=source_inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text())['locked_inputs']!=locked:raise SystemExit('missing/stale source lock')
 raw=json.loads(RAW19.read_text());checkpoint=json.loads(v19.PREPARED.read_text());prepared=checkpoint['graph'];ph=checkpoint['prepared_graph_sha256']
 caps=[x for x in raw['scope_results']['global'] if x['termination']=='pass_cap_reached']
 rows=[]
 from scripts.rung8_lib import H,W
 blank=__import__('numpy').zeros((H,W),dtype=__import__('numpy').float32)
 for i,old in enumerate(caps,1):
  name=old['condition'];parts=name.split('_');theta=float(parts[1]);phase_label=float(parts[3]);phase=0.0 if phase_label==0.0 else (math.pi/2 if abs(phase_label-math.pi/2)<1e-5 else phase_label);frame=binarize(grating((H,W),theta,phase,4.0))
  if not name.endswith('_both'):raise RuntimeError(f'not both-sheet cap case: {name}')
  s,inner,(wa,wb),(ua,ub),top=v19.build('global',prepared,ph)
  delivered=v19.inputs(s,(wa,wb),(frame,frame));start_hash=v19.exact_digest(inner.graph_to_dict());t0=time.perf_counter()
  report=inner.run_rules_report(MAX,True);elapsed=time.perf_counter()-t0
  end_hash=base.graph_digest(inner.graph_to_dict())
  row={'condition':name,'theta':theta,'phase':phase,'a_pixels':delivered[0],'b_pixels':delivered[1],
       'a_retinal_bursts':sum(float(s.node(u)['attrs'].get('bursting',0.0)) for u in wa.cells.values()),
       'b_retinal_bursts':sum(float(s.node(u)['attrs'].get('bursting',0.0)) for u in wb.cells.values()),
       'start_graph_sha256':start_hash,'end_graph_sha256':end_hash,'status':report['status'],'progress_steps':int(report['progress_steps']),
       'passes_completed':int(report['passes_completed']),'budget_overshoot':int(report['budget_overshoot']),'elapsed_s':elapsed,
       'A_act_sum':sum(float(s.node(u)['attrs'].get('act',0.0)) for u in ua),'B_act_sum':sum(float(s.node(u)['attrs'].get('act',0.0)) for u in ub)}
  rows.append(row);OUT.with_suffix('.partial.json').write_text(json.dumps({'cases':rows},indent=2,sort_keys=True)+'\n')
  print(f'replay {i}/{len(caps)} {name} status={row["status"]} passes={row["passes_completed"]} progress={row["progress_steps"]} elapsed={elapsed:.1f}s',flush=True)
 final=source_inputs();out={'run_id':'vision-global-joint-cap-native-replay-v1.9.1-20260927','locked_inputs':locked,'post_run_inputs':final,'source_stable':locked==final,'pass_count':len(caps),'progress_cap':MAX,'v1_9_prepared_graph_sha256':ph,'cases':rows}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':str(OUT.relative_to(ROOT)),'source_stable':out['source_stable'],'cases':len(rows)},indent=2))
 if not out['source_stable']:raise SystemExit('source drift')
if __name__=='__main__':main()
