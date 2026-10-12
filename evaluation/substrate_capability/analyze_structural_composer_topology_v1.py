#!/usr/bin/env python3
"""Validate and summarize matched topology composer capture."""
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/structural_composer_topology_v1_lock_20261002.json'
DATA=ROOT/'evaluation/reports/structural_composer_topology_v1_20261002.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 l=json.loads(LOCK.read_text());d=json.loads(DATA.read_text())
 assert d['lock_sha256']==sha(LOCK) and d['sources']==l['sources']
 keyed={(x['family'],x['layout'],x['replicate']):x for x in d['rows']}
 expected={(f,layout,r) for f in l['families'] for layout in l['layouts'] for r in range(l['replicates'])}
 assert set(keyed)==expected and len(keyed)==len(expected)
 for (f,layout,r),x in keyed.items():
  target,op,site=l['expected'][f]
  assert x['nodes']==l['nodes'] and x['edge_count']==l['nodes']*l['edges_per_node']
  assert x['built'] and x['target']==target and x['operator']==op and x['site']==site and x['primary_rules_unchanged']
  assert x['node_insert_ns']>0 and x['edge_insert_ns']>0 and x['compose_ns']>0
  if layout in ('cyclic','clustered','random_regular'):assert x['max_out_degree']==4
  if layout=='hub':assert x['max_out_degree']==4000
  if layout=='clustered':assert x['within_cluster_edges']==400000
  if layout!='clustered':assert x['within_cluster_edges']==0
 print(f'all {len(keyed)} trials have matched graph counts, correct topology, expected proposals, and primary isolation')
 for f in l['families']:
  for layout in l['layouts']:
   rs=[keyed[(f,layout,r)] for r in range(l['replicates'])]
   ts=[x['compose_ns'] for x in rs]
   print(f"{f:25} {layout:15} compose_median_ms={statistics.median(ts)/1e6:.3f}; "+
    f"range_ms={min(ts)/1e6:.3f}-{max(ts)/1e6:.3f}; max_out/in={max(x['max_out_degree'] for x in rs)}/{max(x['max_in_degree'] for x in rs)}; "+
    f"median_build_ms={(statistics.median([x['node_insert_ns']+x['edge_insert_ns'] for x in rs]))/1e6:.1f}")
if __name__=='__main__':main()
