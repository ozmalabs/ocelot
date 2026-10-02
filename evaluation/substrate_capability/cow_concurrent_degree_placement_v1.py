#!/usr/bin/env python3
"""Run source-locked concurrent CoW degree/placement measurements."""
from __future__ import annotations
import hashlib,json,os,platform,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
CRATE=ROOT/"evaluation/substrate_capability/fixtures/cow_concurrent_degree_placement/Cargo.toml"
ANALYZER=ROOT/"scripts/analyze_cow_concurrent_degree_placement_v1.py"
RAW=ROOT/"evaluation/reports/cow_concurrent_degree_placement_v1.json"
SOURCES=("evaluation/substrate_capability/cow_concurrent_degree_placement_v1.py","scripts/analyze_cow_concurrent_degree_placement_v1.py",
 "evaluation/substrate_capability/fixtures/cow_concurrent_degree_placement/Cargo.toml",
 "evaluation/substrate_capability/fixtures/cow_concurrent_degree_placement/Cargo.lock",
 "evaluation/substrate_capability/fixtures/cow_concurrent_degree_placement/src/main.rs",
 "runners/dsl/src/substrate.rs","runners/dsl/src/graph.rs","runners/dsl/src/cow_paged_vec.rs",
 "runners/dsl/src/cow_sharded_map.rs","runners/dsl/src/value.rs","runners/dsl/python/substrate_rs/_native.build.json")
def sha(p):return "sha256:"+hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit("stale native engine: "+"; ".join(stale))
 env=dict(os.environ);env["CARGO_TARGET_DIR"]=str(ROOT/"runners/dsl/target")
 command=["cargo","run","--offline","--release","--manifest-path",str(CRATE)]
 run=subprocess.run(command,cwd=ROOT,env=env,text=True,capture_output=True)
 if run.returncode:raise SystemExit(run.stderr[-8000:])
 measured=json.loads(run.stdout);rows=measured["rows"]
 if len(rows)!=384:raise SystemExit(f"expected 384 rows, got {len(rows)}")
 for row in rows:
  if not row["all_semantics_pass"] or not row["primary_unchanged"]:raise SystemExit(f"semantic gate failed: {row}")
  if not row["all_live_bytes_increased"] or not row["cancel_reduced_live_bytes"]:raise SystemExit(f"live/cancel gate failed: {row}")
  if not row["adjusted_reclamation_pass"] or row["mutation_adjusted_after_drop_bytes"]!=0:raise SystemExit(f"reclamation gate failed: {row}")
 binary=ROOT/"runners/dsl/target/release/cow-concurrent-degree-placement-probe"
 rustc=subprocess.run(["rustc","-Vv"],text=True,capture_output=True,check=True).stdout
 capture={"schema":"CowConcurrentDegreePlacementCaptureV1","host":{"platform":platform.platform(),"machine":platform.machine(),"logical_cpu_count":os.cpu_count(),"rustc_verbose":rustc},
  "engine_fingerprint":rust_source_fingerprint(str(ROOT)),"runner":{"path":str(Path(__file__).resolve()),"sha256":sha(Path(__file__))},
  "probe_binary":{"path":str(binary),"sha256":sha(binary)},"source_sha256":{p:sha(ROOT/p) for p in SOURCES},
  "protocol":{"topologies":["path","regular_four","star","grid"],"sizes_nodes":[10000,50000],
   "target_policies":["clustered","spread","low_out_degree","high_out_degree"],"write_density_percent":[1,10],
   "fanout":16,"repeats_per_backend_cell":3,"payload_bytes":128,"backends":["shared_snapshot","eager_copy"],
   "backend_order":"counterbalanced by repetition","degree_metric":"selected nodes' original out-degree: min, upper median, max, sum",
   "alloc_measure":"requested live Rust System allocator payload bytes; thread-only and same-backend fork/drop controls",
   "claim_scope":"synthetic graph degree/placement interactions; one host; not natural-task or serving evidence"},
  "cargo_command":command,"build_stderr_sha256":"sha256:"+hashlib.sha256(run.stderr.encode()).hexdigest(),
  "build_stderr_tail":run.stderr[-1200:],"measurements":measured}
 RAW.parent.mkdir(parents=True,exist_ok=True);RAW.write_text(json.dumps(capture,indent=2,sort_keys=True)+"\n")
 subprocess.run([sys.executable,str(ANALYZER)],cwd=ROOT,env=env,check=True)
 print(json.dumps({"rows":len(rows),"capture":str(RAW.relative_to(ROOT))},sort_keys=True))
if __name__=="__main__":raise SystemExit(main())
