#!/usr/bin/env python3
"""Validate and summarize the structural composer edge-density capture."""
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/structural_composer_edge_density_v1_lock_20261002.json'
DATA=ROOT/'evaluation/reports/structural_composer_edge_density_v1_20261002.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 l=json.loads(LOCK.read_text());d=json.loads(DATA.read_text())
 assert d['lock_sha256']==sha(LOCK) and d['sources']==l['sources']
 keyed={(x['family'],x['edges_per_node'],x['replicate']):x for x in d['rows']}
 expected={(f,e,r) for f in l['families'] for e in l['edges_per_node'] for r in range(l['replicates'])}
 assert set(keyed)==expected and len(keyed)==len(expected)
 for (f,e,r),x in keyed.items():
  target,op,site=l['expected'][f]
  assert x['nodes']==l['nodes'] and x['edges']==l['nodes']*e
  assert x['built'] and x['target']==target and x['operator']==op and x['site']==site
  assert x['primary_rules_unchanged'] and x['node_insert_ns']>0 and x['edge_insert_ns']>=0 and x['compose_ns']>0
 print(f'all {len(keyed)} trials have exact graph counts, expected proposals, and primary isolation')
 for f in l['families']:
  for e in l['edges_per_node']:
   rs=[keyed[(f,e,r)] for r in range(l['replicates'])]
   t=[x['compose_ns'] for x in rs]
   mem=[x['rss_edges_delta_bytes'] for x in rs if x['rss_edges_delta_bytes'] is not None]
   print(f"{f:25} edges/node={e}: compose_median_ms={statistics.median(t)/1e6:.3f}; "+
    f"range_ms={min(t)/1e6:.3f}-{max(t)/1e6:.3f}; edge_RSS_delta_median_KiB="+
    (f"{statistics.median(mem)/1024:.1f}" if mem else 'n/a'))
if __name__=='__main__':main()
