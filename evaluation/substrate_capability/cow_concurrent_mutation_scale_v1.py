#!/usr/bin/env python3
"""Run source-locked concurrent CoW topology/write-density measurements."""
from __future__ import annotations
import hashlib,json,os,platform,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
CRATE=ROOT/"evaluation/substrate_capability/fixtures/cow_concurrent_mutation_scale/Cargo.toml"
ANALYZER=ROOT/"scripts/analyze_cow_concurrent_mutation_scale_v1.py"
RAW=ROOT/"evaluation/reports/cow_concurrent_mutation_scale_v1.json"
SOURCES=("evaluation/substrate_capability/cow_concurrent_mutation_scale_v1.py","scripts/analyze_cow_concurrent_mutation_scale_v1.py",
 "evaluation/substrate_capability/fixtures/cow_concurrent_mutation_scale/Cargo.toml",
 "evaluation/substrate_capability/fixtures/cow_concurrent_mutation_scale/Cargo.lock",
 "evaluation/substrate_capability/fixtures/cow_concurrent_mutation_scale/src/main.rs",
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
 measured=json.loads(run.stdout)
 rows=measured["rows"]
 expected=3*2*2*2*2*3
 if len(rows)!=expected:raise SystemExit(f"expected {expected} rows, got {len(rows)}")
 for r in rows:
  if not r["all_semantics_pass"] or not r["primary_unchanged"]:raise SystemExit(f"semantic gate failed: {r}")
  if not r["all_live_bytes_increased"] or not r["cancel_reduced_live_bytes"]:raise SystemExit(f"allocation/cancel gate failed: {r}")
  if not r["adjusted_reclamation_pass"] or r["mutation_adjusted_after_drop_bytes"]!=0:raise SystemExit(f"reclamation gate failed: {r}")
 binary=ROOT/"runners/dsl/target/release/cow-concurrent-mutation-scale-probe"
 rustc=subprocess.run(["rustc","-Vv"],text=True,capture_output=True,check=True).stdout
 capture={"schema":"CowConcurrentMutationScaleCaptureV1","host":{"platform":platform.platform(),"machine":platform.machine(),"logical_cpu_count":os.cpu_count(),"rustc_verbose":rustc},
  "engine_fingerprint":rust_source_fingerprint(str(ROOT)),"runner":{"path":str(Path(__file__).resolve()),"sha256":sha(Path(__file__))},
  "probe_binary":{"path":str(binary),"sha256":sha(binary)},"source_sha256":{p:sha(ROOT/p) for p in SOURCES},
  "protocol":{"topologies":["path","star","grid"],"sizes_nodes":[10000,50000],"write_density_percent":[1,10],
   "fanouts":[4,16],"repeats_per_backend_cell":3,"payload_bytes":128,"backends":["shared_snapshot","eager_copy"],
   "backend_order":"counterbalanced by repetition","alloc_measure":"requested live Rust System allocator payload bytes with thread-only and same-backend fork/drop no-write controls",
   "claim_scope":"concurrent branch mutation, graph-topology interaction, and mutation allocation/reclamation; synthetic single-host study"},
  "cargo_command":command,"build_stderr_sha256":"sha256:"+hashlib.sha256(run.stderr.encode()).hexdigest(),
  "build_stderr_tail":run.stderr[-1200:],"measurements":measured}
 RAW.parent.mkdir(parents=True,exist_ok=True);RAW.write_text(json.dumps(capture,indent=2,sort_keys=True)+"\n")
 subprocess.run([sys.executable,str(ANALYZER)],cwd=ROOT,env=env,check=True)
 print(json.dumps({"rows":len(rows),"capture":str(RAW.relative_to(ROOT))},sort_keys=True))
if __name__=="__main__":main()
