#!/usr/bin/env python3
"""Validate and summarize the structural composer family scaling capture."""
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/structural_composer_family_scaling_v1_1_lock_20261002.json'
DATA=ROOT/'evaluation/reports/structural_composer_family_scaling_v1_1_20261002.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 lock=json.loads(LOCK.read_text());data=json.loads(DATA.read_text())
 assert data['lock_sha256']==sha(LOCK) and data['sources']==lock['sources']
 keyed={(x['family'],x['unrelated_nodes'],x['replicate']):x for x in data['trials']}
 expected_keys={(f,n,r) for f in lock['families'] for n in lock['unrelated_node_counts'] for r in range(lock['replicates'])}
 assert set(keyed)==expected_keys and len(data['trials'])==len(expected_keys)
 for (f,n,r),x in keyed.items():
  target,op,site=lock['expected'][f]
  assert x['built'] and x['target']==target and x['operator']==op and x['site']==site
  assert x['primary_rules_unchanged'] and x['compose_ns']>=0
 print(f"all {len(keyed)} trials selected their locked target/operator/site and preserved primary rules")
 for f in lock['families']:
  for n in lock['unrelated_node_counts']:
   rs=[keyed[(f,n,r)] for r in range(lock['replicates'])]
   ns=[x['compose_ns'] for x in rs]
   node_mem=[x['rss_noise_delta_bytes'] for x in rs if x['rss_noise_delta_bytes'] is not None]
   compose_mem=[x['rss_compose_delta_bytes'] for x in rs if x['rss_compose_delta_bytes'] is not None]
   memory=(f"median graph RSS delta={statistics.median(node_mem)/1024:.1f} KiB; "+
    f"composer RSS delta={statistics.median(compose_mem)/1024:.1f} KiB" if node_mem and compose_mem else 'RSS unavailable')
   print(f"{f:25} noise={n:5} median_ms={statistics.median(ns)/1e6:.3f} "+memory)
if __name__=='__main__':main()
