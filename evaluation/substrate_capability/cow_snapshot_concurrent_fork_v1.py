#!/usr/bin/env python3
"""Run and source-capture the native concurrent snapshot fork probe."""
import hashlib,json,os,platform,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from domains.engine_provenance import build_is_stale,rust_source_fingerprint
PROBE=ROOT/"evaluation/substrate_capability/fixtures/cow_snapshot_threads/Cargo.toml"
ANALYZER=ROOT/"scripts/analyze_cow_snapshot_concurrent_fork_v1.py"
RAW=ROOT/"evaluation/reports/cow_snapshot_concurrent_fork_v1.json"
SOURCES=("evaluation/substrate_capability/cow_snapshot_concurrent_fork_v1.py","scripts/analyze_cow_snapshot_concurrent_fork_v1.py","evaluation/substrate_capability/fixtures/cow_snapshot_threads/Cargo.toml","evaluation/substrate_capability/fixtures/cow_snapshot_threads/Cargo.lock","evaluation/substrate_capability/fixtures/cow_snapshot_threads/src/main.rs","runners/dsl/python/substrate_rs/_native.build.json","runners/dsl/src/substrate.rs","runners/dsl/src/graph.rs","runners/dsl/src/py.rs")
def sha(path):return "sha256:"+hashlib.sha256(Path(path).read_bytes()).hexdigest()
def main():
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit("stale native engine: "+"; ".join(stale))
 env=dict(os.environ);env["CARGO_TARGET_DIR"]=str(ROOT/"runners/dsl/target")
 cmd=["cargo","run","--offline","--release","--manifest-path",str(PROBE)]
 result=subprocess.run(cmd,cwd=ROOT,env=env,text=True,capture_output=True)
 if result.returncode:raise SystemExit(result.stderr[-6000:])
 measured=json.loads(result.stdout)
 binary=ROOT/"runners/dsl/target/release/cow-snapshot-threads-probe"
 rustc=subprocess.run(["rustc","-Vv"],text=True,capture_output=True,check=True).stdout
 capture={"schema":"CowSnapshotConcurrentForkCaptureV1","host":{"platform":platform.platform(),"machine":platform.machine(),"logical_cpu_count":os.cpu_count(),"rustc_verbose":rustc},"engine_fingerprint":rust_source_fingerprint(str(ROOT)),"runner":{"path":str(Path(__file__).resolve()),"sha256":sha(Path(__file__))},"probe_binary":{"path":str(binary),"sha256":sha(binary)},"sources":{p:sha(ROOT/p) for p in SOURCES},"cargo_command":cmd,"build_stderr_sha256":"sha256:"+hashlib.sha256(result.stderr.encode()).hexdigest(),"build_stderr_tail":result.stderr[-1500:],"measurements":measured}
 RAW.write_text(json.dumps(capture,indent=2,sort_keys=True)+"\n")
 subprocess.run([sys.executable,str(ANALYZER)],cwd=ROOT,env=env,check=True)
 print(json.dumps({"rows":len(measured["rows"]),"raw":str(RAW.relative_to(ROOT))},indent=2))
if __name__=="__main__":main()
