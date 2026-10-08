#!/usr/bin/env python3
"""Capture ordered by-type COW mutation semantics and timings."""
from __future__ import annotations
import hashlib, json, platform, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; CRATE=ROOT/'runners/dsl'
NAME='typed_graph_cow_attr_index_mutation_v3'; BIN=CRATE/'target/release'/NAME
PROTOCOL=ROOT/'docs/research/engine_substrate/TYPED_GRAPH_ORDERED_TYPE_INDEX_COW_V5_PREREG_20261006.md'
RUNNER=Path(__file__).resolve(); ANALYZER=ROOT/'evaluation/substrate_capability/analyze_ordered_type_index_cow_v5.py'
LOCK=ROOT/'evaluation/substrate_capability/ordered_type_index_cow_v5_lock_20261006.json'
OUT=ROOT/'evaluation/reports/ordered_type_index_cow_v5_raw_20261006.json'
SOURCES=('runners/dsl/src/graph.rs','runners/dsl/src/cow_paged_vec.rs','runners/dsl/src/cow_sharded_map.rs',
 'runners/dsl/src/bin/typed_graph_cow_attr_index_mutation_v3.rs','runners/dsl/Cargo.toml','runners/dsl/Cargo.lock')
def sha(p): return 'sha256:'+hashlib.sha256(Path(p).read_bytes()).hexdigest()
def cmd(args): return subprocess.run(args,cwd=CRATE,check=True,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE).stdout.strip()
def inputs():
 return {'protocol_sha256':sha(PROTOCOL),'runner_sha256':sha(RUNNER),'analyzer_sha256':sha(ANALYZER),
  'source_sha256':{s:sha(ROOT/s) for s in SOURCES},'binary_sha256':sha(BIN),
  'rustc':cmd(['rustc','--version']),'cargo':cmd(['cargo','--version'])}
def main():
 subprocess.run(['cargo','build','--release','--bin',NAME],cwd=CRATE,check=True)
 current=inputs()
 if sys.argv[1:]==['--lock']:
  LOCK.write_text(json.dumps({'schema':'OrderedTypeIndexCowV5Lock','locked_inputs':current},indent=2,sort_keys=True)+'\n')
  print(LOCK.relative_to(ROOT)); return 0
 if sys.argv[1:]: raise SystemExit('usage: ordered_type_index_cow_v5.py [--lock]')
 if not LOCK.is_file() or json.loads(LOCK.read_text()).get('locked_inputs')!=current: raise SystemExit('missing/stale source lock')
 raw=json.loads(cmd([str(BIN),'7164,16384,50771','21'])); after=inputs()
 if current!=after: raise SystemExit('source changed during capture')
 if len(raw.get('cells',[]))!=3 or not raw.get('reuse_compaction_controls_pass'): raise SystemExit('compaction/reuse control failed')
 for c in raw['cells']:
  if not c['baseline_queries_exact'] or not c['baseline_type_order_exact']: raise SystemExit('baseline gate failed')
  for r in c['mutation_samples']:
   for key in ('shared_semantics','eager_semantics','shared_order_semantics','eager_order_semantics'):
    if len(r[key])!=21 or not all(r[key]): raise SystemExit(f"mutation/order gate failed: {c['nodes']} {r['name']} {key}")
 payload={'schema':'OrderedTypeIndexCowV5Raw','locked_inputs':current,'post_run_inputs':after,'source_stable':current==after,
  'host':{'platform':platform.platform(),'machine':platform.machine()},'probe':raw,
  'protocol':{'nodes':[7164,16384,50771],'repeats':21,'ordered_tombstone_compaction_reuse_control':True}}
 OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n')
 print(OUT.relative_to(ROOT)); return 0
if __name__=='__main__': raise SystemExit(main())
