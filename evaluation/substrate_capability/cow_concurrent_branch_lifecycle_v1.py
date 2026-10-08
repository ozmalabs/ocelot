#!/usr/bin/env python3
"""Build, source-lock, and measure concurrent Substrate snapshot lifecycles."""
from __future__ import annotations
import hashlib, json, os, platform, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
CRATE=ROOT/"evaluation/substrate_capability/fixtures/cow_concurrent_lifecycle/Cargo.toml"
ANALYZER=ROOT/"scripts/analyze_cow_concurrent_branch_lifecycle_v1.py"
RAW=ROOT/"evaluation/reports/cow_concurrent_branch_lifecycle_v1.json"
SOURCES=(
 "evaluation/substrate_capability/cow_concurrent_branch_lifecycle_v1.py",
 "scripts/analyze_cow_concurrent_branch_lifecycle_v1.py",
 "evaluation/substrate_capability/fixtures/cow_concurrent_lifecycle/Cargo.toml",
 "evaluation/substrate_capability/fixtures/cow_concurrent_lifecycle/Cargo.lock",
 "evaluation/substrate_capability/fixtures/cow_concurrent_lifecycle/src/main.rs",
 "runners/dsl/src/substrate.rs","runners/dsl/src/graph.rs","runners/dsl/src/cow_paged_vec.rs",
 "runners/dsl/src/cow_sharded_map.rs","runners/dsl/src/py.rs",
 "runners/dsl/python/substrate_rs/_native.build.json",
)
def sha(path:Path)->str:return "sha256:"+hashlib.sha256(path.read_bytes()).hexdigest()
def main()->int:
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit("stale native engine: "+"; ".join(stale))
 env=dict(os.environ);env["CARGO_TARGET_DIR"]=str(ROOT/"runners/dsl/target")
 command=["cargo","run","--offline","--release","--manifest-path",str(CRATE)]
 done=subprocess.run(command,cwd=ROOT,env=env,text=True,capture_output=True)
 if done.returncode:raise SystemExit(done.stderr[-8000:])
 measured=json.loads(done.stdout)
 required={(n,f,b) for n in (10000,50000) for f in (1,4,16) for b in ("shared_snapshot","eager_copy")}
 rows=measured["rows"]
 if len(rows)!=60:raise SystemExit(f"expected 60 backend/repetition rows, found {len(rows)}")
 for row in rows:
  if not row["all_semantics_pass"] or not row["primary_unchanged"]:
   raise SystemExit(f"semantic gate failed: {row}")
  if not row["all_live_bytes_increased"] or not row["cancel_reduced_live_bytes"]:
   raise SystemExit(f"live allocation gate failed: {row}")
  if not row["mutation_adjusted_reclamation_pass"] or row["mutation_adjusted_after_drop_bytes"]!=0:
   raise SystemExit(f"adjusted branch reclamation gate failed: {row}")
 if {(r["size_nodes"],r["fanout"],r["backend"]) for r in rows}!=required:
  raise SystemExit("measurement cell coverage mismatch")
 rustc=subprocess.run(["rustc","-Vv"],text=True,capture_output=True,check=True).stdout
 binary=ROOT/"runners/dsl/target/release/cow-concurrent-lifecycle-probe"
 capture={"schema":"CowConcurrentBranchLifecycleCaptureV1",
  "host":{"platform":platform.platform(),"machine":platform.machine(),"logical_cpu_count":os.cpu_count(),"rustc_verbose":rustc},
  "engine_fingerprint":rust_source_fingerprint(str(ROOT)),
  "runner":{"path":str(Path(__file__).resolve()),"sha256":sha(Path(__file__).resolve())},
  "probe_binary":{"path":str(binary),"sha256":sha(binary)},
  "source_sha256":{p:sha(ROOT/p) for p in SOURCES},
  "protocol":{"sizes_nodes":[10000,50000],"fanouts":[1,4,16],"repeats_per_cell":5,
   "backends":["shared_snapshot","eager_copy"],"backend_order":"counterbalanced by repetition",
   "alloc_metric":"live bytes requested from Rust System allocator; thread-only and same-backend fork/drop controls are captured separately",
   "branch_count_control":"mutated wave minus same-backend fork/drop/no-write wave; post-drop residual must equal zero",
   "limits":["one host and synthetic isolated-node graphs","allocator payload only, excluding metadata/RSS","not an application-serving throughput measurement"]},
  "cargo_command":command,"build_stderr_sha256":"sha256:"+hashlib.sha256(done.stderr.encode()).hexdigest(),
  "build_stderr_tail":done.stderr[-1500:],"measurements":measured}
 RAW.parent.mkdir(parents=True,exist_ok=True);RAW.write_text(json.dumps(capture,indent=2,sort_keys=True)+"\n")
 subprocess.run([sys.executable,str(ANALYZER)],cwd=ROOT,env=env,check=True)
 print(json.dumps({"rows":len(rows),"cells":len(required),"capture":str(RAW.relative_to(ROOT))},sort_keys=True))
 return 0
if __name__=="__main__":raise SystemExit(main())
