#!/usr/bin/env python3
"""Rebuild the v2.4 aggregate from source-locked isolated worker records."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
import substrate_vision_two_sheet_current_source_scale_v2_4 as runner
LOCK=runner.LOCK;OUT=runner.OUT
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 lock=json.loads(LOCK.read_text())['locked_inputs']
 if lock!=runner.source_inputs():raise SystemExit('v2.4 source lock no longer matches current files')
 expected={runner.cell_id(s,n,sc,b,m) for s in runner.SEEDS for n in runner.SIZES for sc in runner.SCOPES for b in runner.B_STATES for m in runner.MODES}
 cells=[]
 for cid in sorted(expected):
  p=runner.CELLDIR/f'{cid}.json'
  if not p.is_file():raise SystemExit(f'missing worker record {cid}')
  row=json.loads(p.read_text())
  if row['cell_id']!=cid or row['source_stable'] is not True or row['source_lock_sha256']!=sha(LOCK):raise SystemExit(f'worker record failed source/identity gate: {cid}')
  cells.append(row)
 if len(cells)!=144 or len({x['cell_id'] for x in cells})!=144:raise SystemExit('worker cell set is not the registered 144')
 data={'run_id':'vision-two-sheet-current-source-scale-v2.4-20260927','locked_inputs':lock,'cells':cells,'source_stable':runner.source_inputs()==lock,'complete':True,'aggregation_reconciliation':{'method':'independent reconstruction from registered, individually locked cell records','cell_count':len(cells),'original_master_completion_check':'The runner output branch compared the 144 records to a hardcoded 96; all expected workers completed, but the master returned nonzero and did not write its aggregate.','master_completion_boolean_recomputed_from_registered_cell_set':True,'aggregator_sha256':sha(__file__),'worker_source_lock_sha256':sha(LOCK)}}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'output':str(OUT.relative_to(ROOT)),'cells':len(cells),'source_stable':data['source_stable'],'complete':data['complete'],'master_aggregate_reconciled':True},indent=2))
if __name__=='__main__':main()
