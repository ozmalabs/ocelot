#!/usr/bin/env python3
"""Validate full-composer graph scaling v1.1 capture."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/full_structural_composer_graph_scaling_v1_1_lock_20261002.json'
DATA=ROOT/'evaluation/reports/full_structural_composer_graph_scaling_v1_1_20261002.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 l=json.loads(LOCK.read_text());d=json.loads(DATA.read_text())
 assert d['lock_sha256']==sha(LOCK) and d['sources']==l['sources']
 assert [r['unrelated_nodes'] for r in d['rows']]==l['capture_order']
 for row in d['rows']:
  assert len(row['trials'])==l['trials']
  assert all(t['built'] and t['operator']==l['expected_operator'] and
   t['site']==l['expected_site'] and t['primary_rules_unchanged'] for t in row['trials'])
 print('all 15 measured trials emitted the expected repair and preserved active primary rules')
 for row in d['rows']:
  vals=[t['compose_ns'] for t in row['trials']]
  print(f"unrelated_nodes={row['unrelated_nodes']}: median_ms={row['median_compose_ns']/1e6:.3f}; "+
   f"range_ms={min(vals)/1e6:.3f}-{max(vals)/1e6:.3f}; setup_median_ms={row['median_noise_setup_ns']/1e6:.3f}")
if __name__=='__main__':main()
