#!/usr/bin/env python3
"""Build and run source-captured CoW write-density/locality panel."""
import hashlib, json, os, platform, random, shlex, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from domains.engine_provenance import build_is_stale, rust_source_fingerprint

FIXTURE = ROOT / "evaluation/substrate_capability/fixtures/cow_snapshot_write_density"
BIN = ROOT / "runners/dsl/target/release/cow-snapshot-write-density-probe"
ANALYZER = ROOT / "scripts/analyze_cow_snapshot_write_density_locality_v1.py"
RAW = ROOT / "evaluation/reports/cow_snapshot_write_density_locality_v1.json"
SOURCES = (
    "evaluation/substrate_capability/cow_snapshot_write_density_locality_v1.py",
    "scripts/analyze_cow_snapshot_write_density_locality_v1.py",
    "evaluation/substrate_capability/fixtures/cow_snapshot_write_density/Cargo.toml",
    "evaluation/substrate_capability/fixtures/cow_snapshot_write_density/Cargo.lock",
    "evaluation/substrate_capability/fixtures/cow_snapshot_write_density/src/main.rs",
    "runners/dsl/python/substrate_rs/_native.build.json",
    "runners/dsl/src/substrate.rs", "runners/dsl/src/graph.rs", "runners/dsl/src/rewrite.rs",
)

def sha(path):
    return "sha256:" + hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    stale = build_is_stale(str(ROOT))
    if stale:
        raise SystemExit("stale native engine: " + "; ".join(stale))
    pyflags = subprocess.run(["python3-config", "--embed", "--ldflags"], text=True, capture_output=True, check=True).stdout
    lib_dirs = [x[2:] for x in shlex.split(pyflags) if x.startswith("-L")]
    env = dict(os.environ)
    env["CARGO_TARGET_DIR"] = str(ROOT / "runners/dsl/target")
    env["LD_LIBRARY_PATH"] = ":".join(lib_dirs + [env.get("LD_LIBRARY_PATH", "")])
    link_args = []
    for flag in shlex.split(pyflags):
        if flag.startswith(("-L", "-l")):
            link_args.extend(["-C", "link-arg=" + flag])
    build = subprocess.run(
        ["cargo", "rustc", "--offline", "--release", "--manifest-path", str(FIXTURE / "Cargo.toml"),
         "--bin", "cow-snapshot-write-density-probe", "--", *link_args],
        cwd=ROOT, env=env, text=True, capture_output=True)
    if build.returncode:
        raise SystemExit("probe build failed:\n" + build.stderr[-6000:])
    combos = []
    for density in (0.01, 0.10, 0.50):
        combos.extend((density, locality) for locality in ("contiguous", "spread"))
    combos.append((1.0, "contiguous"))
    jobs = [(n, density, loc, r) for n in (10771, 50771) for density, loc in combos for r in range(5)]
    random.Random(20261001).shuffle(jobs)
    rows = []
    for i, (size, density, locality, repeat) in enumerate(jobs, 1):
        active = max(1, int(size * density))
        command = [str(BIN), str(size), "4", str(repeat), str(active), locality]
        proc = subprocess.Popen(command, cwd=ROOT, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        if proc.returncode:
            raise SystemExit(f"worker failed at size={size} density={density} locality={locality} repeat={repeat}: {stderr[-3000:]}")
        row = json.loads(stdout)
        row["worker_pid"] = proc.pid
        rows.append(row)
        print(f"[{i}/{len(jobs)}] nodes={size} active={active} locality={locality} repeat={repeat}", flush=True)
    capture = {
        "schema": "CowSnapshotWriteDensityLocalityCaptureV1",
        "host": {"platform": platform.platform(), "machine": platform.machine(), "logical_cpu_count": os.cpu_count(),
                 "rustc_verbose": subprocess.run(["rustc", "-Vv"], text=True, capture_output=True, check=True).stdout},
        "engine_fingerprint": rust_source_fingerprint(str(ROOT)),
        "binary": {"path": str(BIN), "sha256": sha(BIN)},
        "source_sha256": {p: sha(ROOT / p) for p in SOURCES},
        "protocol": {"fresh_processes": len(jobs), "random_seed": 20261001, "fanout": 4,
                     "build_command": build.args, "python_embed_ldflags": pyflags},
        "measurements": rows,
    }
    RAW.write_text(json.dumps(capture, indent=2, sort_keys=True) + "\n")
    subprocess.run([sys.executable, str(ANALYZER)], cwd=ROOT, env=env, check=True)
    print(json.dumps({"rows": len(rows), "raw": str(RAW.relative_to(ROOT))}, indent=2))

if __name__ == "__main__":
    main()
