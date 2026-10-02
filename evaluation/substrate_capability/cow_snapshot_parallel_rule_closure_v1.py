#!/usr/bin/env python3
"""Run, source-capture, and analyze native CoW parallel rule closures."""
import hashlib, json, os, platform, random, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from domains.engine_provenance import build_is_stale, rust_source_fingerprint

FIXTURE = ROOT / "evaluation/substrate_capability/fixtures/cow_snapshot_rule_closure"
BIN = ROOT / "runners/dsl/target/release/cow-snapshot-rule-closure-probe"
ANALYZER = ROOT / "scripts/analyze_cow_snapshot_parallel_rule_closure_v1.py"
RAW = ROOT / "evaluation/reports/cow_snapshot_parallel_rule_closure_v1.json"
SOURCES = (
    "evaluation/substrate_capability/cow_snapshot_parallel_rule_closure_v1.py",
    "scripts/analyze_cow_snapshot_parallel_rule_closure_v1.py",
    "evaluation/substrate_capability/fixtures/cow_snapshot_rule_closure/Cargo.toml",
    "evaluation/substrate_capability/fixtures/cow_snapshot_rule_closure/Cargo.lock",
    "evaluation/substrate_capability/fixtures/cow_snapshot_rule_closure/src/main.rs",
    "runners/dsl/python/substrate_rs/_native.build.json",
    "runners/dsl/src/substrate.rs", "runners/dsl/src/graph.rs",
    "runners/dsl/src/rewrite.rs", "runners/dsl/src/py.rs",
)

def sha(path):
    return "sha256:" + hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    stale = build_is_stale(str(ROOT))
    if stale:
        raise SystemExit("stale native engine: " + "; ".join(stale))
    env = dict(os.environ)
    env["LD_LIBRARY_PATH"] = "/home/linuxbrew/.linuxbrew/opt/python@3.13/lib:" + env.get("LD_LIBRARY_PATH", "")
    # Fixed seed gives a reproducible execution order while spreading sizes/fanouts.
    jobs = [(n, f, r) for n in (771, 10771, 50771) for f in (1, 4, 16) for r in range(5)]
    random.Random(20261001).shuffle(jobs)
    rows = []
    for index, (size, fanout, repeat) in enumerate(jobs):
        cmd = [str(BIN), str(size), str(fanout), str(repeat)]
        process = subprocess.Popen(cmd, cwd=ROOT, env=env, text=True,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        if process.returncode:
            raise SystemExit(f"probe failed at {size}/{fanout}/{repeat}: {stderr[-3000:]}")
        row = json.loads(stdout)
        row["worker_pid"] = process.pid
        rows.append(row)
        print(f"[{index+1}/{len(jobs)}] nodes={size} fanout={fanout} repeat={repeat}", flush=True)
    rustc = subprocess.run(["rustc", "-Vv"], text=True, capture_output=True, check=True).stdout
    capture = {
        "schema": "CowSnapshotParallelRuleClosureCaptureV1",
        "host": {"platform": platform.platform(), "machine": platform.machine(),
                 "logical_cpu_count": os.cpu_count(), "rustc_verbose": rustc},
        "engine_fingerprint": rust_source_fingerprint(str(ROOT)),
        "fixture_binary": {"path": str(BIN), "sha256": sha(BIN)},
        "source_sha256": {p: sha(ROOT / p) for p in SOURCES},
        "protocol": {"process_isolation": "one fresh process per row", "job_seed": 20261001,
                     "python_runtime_library": "/home/linuxbrew/.linuxbrew/opt/python@3.13/lib"},
        "measurements": rows,
    }
    RAW.write_text(json.dumps(capture, indent=2, sort_keys=True) + "\n")
    subprocess.run([sys.executable, str(ANALYZER)], cwd=ROOT, env=env, check=True)
    print(json.dumps({"rows": len(rows), "raw": str(RAW.relative_to(ROOT))}, indent=2))

if __name__ == "__main__":
    main()
