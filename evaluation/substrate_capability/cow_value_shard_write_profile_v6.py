#!/usr/bin/env python3
"""Source-locked capture for CowShardedMap value-shard write profile v6."""
import argparse, hashlib, json, os, pathlib, platform, subprocess, sys, time

ROOT = pathlib.Path(__file__).resolve().parents[2]
DSL = ROOT / "runners/dsl"
BIN = DSL / "target/release/cow_value_shard_write_profile_v6"
FILES = [
    "docs/research/engine_substrate/COW_VALUE_SHARD_WRITE_AMPLIFICATION_V6_PREREG_20261006.md",
    "evaluation/substrate_capability/cow_value_shard_write_profile_v6.py",
    "evaluation/substrate_capability/analyze_cow_value_shard_write_profile_v6.py",
    "runners/dsl/src/cow_sharded_map.rs", "runners/dsl/src/graph.rs",
    "runners/dsl/src/bin/cow_value_shard_write_profile_v6.rs",
    "runners/dsl/Cargo.toml", "runners/dsl/Cargo.lock",
]
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def versions(cmd): return subprocess.check_output(cmd, text=True).strip()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lock", action="store_true")
    ap.add_argument("--repeats", type=int, default=21)
    ap.add_argument("--out", type=pathlib.Path, default=ROOT/"evaluation/reports/cow_value_shard_write_profile_v6_raw_20261006.json")
    args = ap.parse_args()
    subprocess.run(["cargo", "build", "--release", "--bin", "cow_value_shard_write_profile_v6"], cwd=DSL, check=True)
    lock_path = ROOT/"evaluation/substrate_capability/cow_value_shard_write_profile_v6_lock_20261006.json"
    lock = {"date":"2026-10-06", "rustc":versions(["rustc","--version"]), "cargo":versions(["cargo","--version"]), "platform":platform.platform(), "source_sha256":{p:sha(ROOT/p) for p in FILES}, "binary_sha256":sha(BIN), "binary_bytes":BIN.stat().st_size}
    if args.lock:
        lock_path.write_text(json.dumps(lock,indent=2)+"\n")
        print(lock_path)
        return
    if not lock_path.exists(): raise SystemExit("missing --lock capture; run with --lock first")
    expected=json.loads(lock_path.read_text())
    if expected != lock: raise SystemExit("source or binary differs from locked capture")
    rows=[]
    for n in (7164,16384,50771):
        for shards in (64,128,256,512):
            for arm in ("cow","eager"):
                raw=subprocess.check_output([str(BIN),str(n),str(shards),str(args.repeats),arm],text=True)
                row=json.loads(raw); row["captured_at_epoch_s"]=time.time(); rows.append(row)
                print(f"captured N={n} S={shards} arm={arm}",flush=True)
    doc={"lock":lock_path.relative_to(ROOT).as_posix(),"lock_sha256":sha(lock_path),"rows":rows}
    args.out.parent.mkdir(parents=True,exist_ok=True); args.out.write_text(json.dumps(doc,indent=2)+"\n")
    print(args.out)
if __name__ == "__main__": main()
