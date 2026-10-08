#!/usr/bin/env python3
"""Validate and summarize native graph build throughput capture."""
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/native_graph_build_scaling_v1_lock_20261002.json'
DATA=ROOT/'evaluation/reports/native_graph_build_scaling_v1_20261002.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 l=json.loads(LOCK.read_text());d=json.loads(DATA.read_text())
 assert d['lock_sha256']==sha(LOCK) and d['sources']==l['sources']
 expected={(n,e,r) for n in l['node_counts'] for e in l['edge_multipliers'] for r in range(l['replicates'])}
 keyed={(x['nodes'],x['edge_multiplier'],x['replicate']):x for x in d['rows']}
 assert set(keyed)==expected and len(keyed)==len(expected)
 for (n,e,r),x in keyed.items():
  assert x['edges']==n*e and x['node_insert_ns']>0 and x['edge_insert_ns']>=0
  assert x['node_throughput_per_s']>0 and x['peak_total_delta_bytes']>=0
 print(f"all {len(keyed)} fresh-process measurements have exact graph counts and complete timing/RSS")
 for n in l['node_counts']:
  for e in l['edge_multipliers']:
   rs=[keyed[(n,e,r)] for r in range(l['replicates'])]
   nodes=statistics.median(x['node_throughput_per_s'] for x in rs)
   edgetimes=statistics.median(x['edge_insert_ns'] for x in rs)/1e9
   edge_rate=(statistics.median(x['edge_throughput_per_s'] for x in rs) if e else None)
   rss=statistics.median(x['peak_total_delta_bytes'] for x in rs)/1048576
   print(f"nodes={n:7} edges/node={e}: node_rate={nodes:,.0f}/s; "+
    (f"edge_rate={edge_rate:,.0f}/s; " if edge_rate is not None else f"edge_time={edgetimes:.6f}s; ")+f"peak_RSS_delta={rss:.1f} MiB")
if __name__=='__main__':main()
