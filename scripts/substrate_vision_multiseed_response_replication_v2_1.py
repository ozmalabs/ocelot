#!/usr/bin/env python3
"""Apply the locked v1.9 response protocol to each v2.0 adapted checkpoint."""
from __future__ import annotations
import hashlib,json,platform,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts'),str(ROOT/'runners/dsl/python')]
import substrate_vision_shared_substrate_multisheet_task_pilot_v1_4 as base
import substrate_vision_shared_substrate_multisheet_task_pilot_v1_9 as panel
from domains.complex_cells import grating,binarize
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_VISION_MULTI_SEED_RESPONSE_REPLICATION_V2_1_PREREG_20260927.md'
LOCK=ROOT/'evaluation/substrate_capability/vision_multiseed_response_replication_v2_1_lock_20260927.json'
OUT=ROOT/'evaluation/reports/vision_multiseed_response_replication_v2_1_20260927.json'
TRACE=OUT.with_suffix('.trace.jsonl')
CHECKPOINT_DIR=ROOT/'evaluation/reports/vision_multiseed_checkpoints_v2_0'
SEEDS=(20260935,20260936,20260937)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(g):return base.graph_digest(g)
def source_inputs():
 return {'protocol_sha256':sha(PROTOCOL),'runner_sha256':sha(__file__),'v1_9_runner_sha256':sha(panel.__file__),'v1_9_contract_sha256':sha(panel.CONTRACT),'v1_9_prereg_sha256':sha(panel.PROTOCOL),'v1_9_lock_sha256':sha(panel.LOCK),'v2_0_runner_sha256':sha(ROOT/'scripts/substrate_vision_multiseed_checkpoint_replication_v2_0.py'),'v2_0_lock_sha256':sha(ROOT/'evaluation/substrate_capability/vision_multiseed_checkpoint_replication_v2_0_lock_20260927.json'),'checkpoints':{str(s):sha(CHECKPOINT_DIR/f'seed_{s}.json') for s in SEEDS},'python':platform.python_version(),'platform':platform.platform()}
def conditions():
 from scripts.rung8_lib import H,W
 blank=np.zeros((H,W),dtype=np.float32);out=[('both_blank',blank,blank)]
 for theta in (0.0,45.0,90.0,135.0):
  for phase in (0.0,float(np.pi/2)):
   f=binarize(grating((H,W),theta,phase,4.0));tag=f'theta_{int(theta)}_phase_{phase:.6f}'
   out.extend([(f'{tag}_B_only',blank,f),(f'{tag}_A_only',f,blank),(f'{tag}_both',f,f)])
 return out
def main():
 if sys.argv[1:]==['--lock']:
  LOCK.parent.mkdir(parents=True,exist_ok=True);LOCK.write_text(json.dumps({'locked_inputs':source_inputs()},indent=2,sort_keys=True)+'\n');print(LOCK);return
 locked=source_inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text())['locked_inputs']!=locked:raise SystemExit('missing/stale source lock')
 prior=json.loads(OUT.read_text()) if OUT.exists() else {'run_id':'vision-multiseed-response-replication-v2.1-20260927','locked_inputs':locked,'seeds':{str(s):[] for s in SEEDS}}
 if prior.get('locked_inputs')!=locked:raise SystemExit('partial output source lock mismatch')
 original=base.build_pair
 with TRACE.open('a') as tf:
  for seed in SEEDS:
   key=str(seed);cp=json.loads((CHECKPOINT_DIR/f'seed_{seed}.json').read_text());graph=cp['graph'];gh=cp['prepared_graph_sha256']
   if digest(graph)!=gh:raise SystemExit(f'seed {seed} checkpoint hash mismatch')
   prior['seeds'].setdefault(key,[]);done={r['condition'] for r in prior['seeds'][key]}
   def build_for_seed(_ignored,scoped,_seed=seed):return original(_seed,scoped)
   base.build_pair=build_for_seed
   try:
    for idx,(name,af,bf) in enumerate(conditions(),1):
     if name in done:continue
     print(f'seed={seed} condition={idx}/25 name={name}',flush=True)
     row=panel.run_condition('root_scoped',name,af,bf,graph,gh,tf);row['seed']=seed;row['checkpoint_sha256']=gh
     prior['seeds'][key].append(row);prior['seeds'][key].sort(key=lambda r:next(i for i,x in enumerate(conditions()) if x[0]==r['condition']))
     prior['source_stable']=source_inputs()==locked;OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(prior,indent=2,sort_keys=True)+'\n')
     print(f'seed={seed} condition={idx}/25 termination={row["termination"]} passes={row["passes_completed"]} progress={row["progress_steps"]}',flush=True)
   finally:base.build_pair=original
 prior['source_stable']=source_inputs()==locked;prior['expected_conditions_per_seed']=25;prior['complete']=all(len(prior['seeds'].get(str(s),[]))==25 for s in SEEDS)
 OUT.write_text(json.dumps(prior,indent=2,sort_keys=True)+'\n')
 if not prior['source_stable']:raise SystemExit('source drift')
 print(json.dumps({'output':str(OUT.relative_to(ROOT)),'complete':prior['complete'],'conditions_per_seed':{k:len(v) for k,v in prior['seeds'].items()}},indent=2))
if __name__=='__main__':main()
