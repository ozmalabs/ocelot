#!/usr/bin/env python3
"""Validate and summarize the graph-site materialization scaling capture."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/graph_site_materialization_scaling_v1_lock_20261002.json'
DATA=ROOT/'evaluation/reports/graph_site_materialization_scaling_v1_20261002.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 lock=json.loads(LOCK.read_text());data=json.loads(DATA.read_text())
 assert data['lock_sha256']==sha(LOCK) and data['sources']==lock['sources']
 expected={(n,m) for n in lock['unrelated_node_counts'] for m in lock['attribute_widths']}
 got={(r['unrelated_nodes'],r['attribute_fields']) for r in data['rows']}
 assert got==expected and len(data['rows'])==len(expected)
 for r in data['rows']:
  m=r['attribute_fields'];count=m+m*(m-1)//2+(1 if m>2 else 0)+1
  assert r['expected_edit_sites']==count and r['observed_edit_sites']==[count]*lock['trials']
  assert len(r['trial_ns'])==lock['trials'] and min(r['trial_ns'])>=0
 print('all 9 locked cells have exact site counts and complete nonnegative timings')
 for m in lock['attribute_widths']:
  rs=[r for r in data['rows'] if r['attribute_fields']==m]
  vals=[r['median_ns'] for r in rs]
  print(f"fields={m}: medians_ms="+', '.join(f"{n/1e6:.3f}" for n in vals)+
        f"; max/min={max(vals)/min(vals):.3f}x")
if __name__=='__main__':main()
