#!/usr/bin/env python3
"""Independent gates for repeated live perception self-repair runs."""
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_live_self_repair_v1_lock_20261005.json'
CAP=ROOT/'evaluation/reports/thoughtexperiment_live_self_repair_v1_20261005.json'
OUT=CAP.with_name('thoughtexperiment_live_self_repair_v1_analysis_20261005.json')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 l=json.loads(LOCK.read_text());c=json.loads(CAP.read_text());rows=c.get('runs',[]);errors=[]
 if c.get('lock_sha256')!=sha(LOCK):errors.append('capture lock hash mismatch')
 if len(rows)!=3 or len({r.get('pid') for r in rows})!=3:errors.append('expected three unique fresh processes')
 for r in rows:
  i=r.get('replicate')
  if r.get('sources_before')!=l['sources'] or r.get('sources_after')!=l['sources']:errors.append(f'{i}: source lock mismatch')
  if r.get('exit_code')!=0:errors.append(f'{i}: episode nonzero exit')
  if not r.get('pass_banner'):errors.append(f'{i}: episode pass banner absent')
  if r.get('minted_frame') is None or r.get('repaired_frame')!=r.get('minted_frame'):errors.append(f'{i}: auto fault/repair timing mismatch')
  if r.get('gate_outcome')!='kept' or r.get('final_axis_kind')!='controllable':errors.append(f'{i}: recovery gate/final behavior mismatch')
 summary={'replicates':len(rows),'unique_processes':len({r.get('pid') for r in rows}),'all_pass':all(r.get('exit_code')==0 and r.get('pass_banner') for r in rows),'minted_frames':[r.get('minted_frame') for r in rows],'repaired_frames':[r.get('repaired_frame') for r in rows],'gate_outcomes':[r.get('gate_outcome') for r in rows],'wall_seconds':[round(r.get('wall_ns',0)/1e9,3) for r in rows],'median_wall_seconds':statistics.median([r.get('wall_ns',0)/1e9 for r in rows]) if rows else None,'scope':'configured target and corrected clause; repeatability only; no target-blind discovery claim'}
 result={'schema':'ThoughtexperimentLiveSelfRepairV1Analysis','gates_pass':not errors,'errors':errors,'summary':summary};OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True));return int(bool(errors))
if __name__=='__main__':raise SystemExit(main())
