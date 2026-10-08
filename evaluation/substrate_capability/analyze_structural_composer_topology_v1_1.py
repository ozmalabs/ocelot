#!/usr/bin/env python3
"""Validate the targeted actor-identity topology follow-up."""
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/structural_composer_topology_v1_1_lock_20261002.json'
DATA=ROOT/'evaluation/reports/structural_composer_topology_v1_1_20261002.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 l=json.loads(LOCK.read_text());d=json.loads(DATA.read_text())
 assert d['lock_sha256']==sha(LOCK) and d['sources']==l['sources']
 assert len(d['rows'])==len(l['layouts'])*l['replicates']
 for layout in l['layouts']:
  rs=[x for x in d['rows'] if x['layout']==layout]
  assert len(rs)==l['replicates'] and {x['replicate'] for x in rs}==set(range(l['replicates']))
  for x in rs:
   target,op,site=l['expected']['actor_recipient_identity']
   assert x['nodes']==100000 and x['edge_count']==400000
   assert (x['built'],x['target'],x['operator'],x['site'],x['primary_rules_unchanged'])==(True,target,op,site,True)
   if layout=='hub':assert x['max_out_degree']==4000
   else:assert x['max_out_degree']==4
   assert x['within_cluster_edges']==(400000 if layout=='clustered' else 0)
  ts=[x['compose_ns'] for x in rs]
  print(f"{layout:15} median_ms={statistics.median(ts)/1e6:.3f}; range_ms={min(ts)/1e6:.3f}-{max(ts)/1e6:.3f}; "+
   f"max_out/in={max(x['max_out_degree'] for x in rs)}/{max(x['max_in_degree'] for x in rs)}")
 print(f"all {len(d['rows'])} trials pass proposal, count, topology, and isolation gates")
if __name__=='__main__':main()
