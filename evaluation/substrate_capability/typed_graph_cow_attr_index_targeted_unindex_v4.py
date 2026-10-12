#!/usr/bin/env python3
"""Capture the targeted-unindex variant with the locked v3 graph probe."""
from __future__ import annotations
import hashlib, json, platform, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CRATE = ROOT / "runners/dsl"
NAME = "typed_graph_cow_attr_index_mutation_v3"
BIN = CRATE / "target/release" / NAME
PROTOCOL = ROOT / "docs/research/engine_substrate/TYPED_GRAPH_COW_ATTR_INDEX_TARGETED_UNINDEX_V4_PREREG_20261006.md"
RUNNER = Path(__file__).resolve()
ANALYZER = ROOT / "evaluation/substrate_capability/analyze_typed_graph_cow_attr_index_targeted_unindex_v4.py"
LOCK = ROOT / "evaluation/substrate_capability/typed_graph_cow_attr_index_targeted_unindex_v4_lock_20261006.json"
OUT = ROOT / "evaluation/reports/typed_graph_cow_attr_index_targeted_unindex_v4_raw_20261006.json"
SOURCES = ("runners/dsl/src/graph.rs", "runners/dsl/src/cow_sharded_map.rs",
           "runners/dsl/src/bin/typed_graph_cow_attr_index_mutation_v3.rs",
           "runners/dsl/Cargo.toml", "runners/dsl/Cargo.lock")

def sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()

def command(args: list[str]) -> str:
    return subprocess.run(args, cwd=CRATE, check=True, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.strip()

def inputs() -> dict:
    return {"protocol_sha256": sha(PROTOCOL), "runner_sha256": sha(RUNNER),
            "analyzer_sha256": sha(ANALYZER),
            "source_sha256": {s: sha(ROOT / s) for s in SOURCES},
            "binary_sha256": sha(BIN), "rustc": command(["rustc", "--version"]),
            "cargo": command(["cargo", "--version"])}

def main() -> int:
    subprocess.run(["cargo", "build", "--release", "--bin", NAME], cwd=CRATE, check=True)
    current = inputs()
    if sys.argv[1:] == ["--lock"]:
        LOCK.write_text(json.dumps({"schema": "TypedGraphCowAttrIndexTargetedUnindexV4Lock",
                                    "locked_inputs": current}, indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT)); return 0
    if sys.argv[1:]: raise SystemExit("usage: typed_graph_cow_attr_index_targeted_unindex_v4.py [--lock]")
    if not LOCK.is_file() or json.loads(LOCK.read_text()).get("locked_inputs") != current:
        raise SystemExit("missing/stale lock; build and run with --lock first")
    raw = json.loads(command([str(BIN), "7164,16384,50771", "21"]))
    after = inputs()
    if current != after: raise SystemExit("source changed during run")
    if len(raw.get("cells", [])) != 3: raise SystemExit("unexpected cell count")
    for cell in raw["cells"]:
        if not cell["baseline_queries_exact"]: raise SystemExit("baseline index query mismatch")
        if len(cell["mutation_samples"]) != 4: raise SystemExit("unexpected mutation panel")
        for row in cell["mutation_samples"]:
            for key in ("shared_semantics", "eager_semantics"):
                if len(row[key]) != 21 or not all(row[key]):
                    raise SystemExit(f"semantic/isolation gate failed: {cell['nodes']} {row['name']} {key}")
    payload = {"schema": "TypedGraphCowAttrIndexTargetedUnindexV4Raw", "locked_inputs": current,
               "post_run_inputs": after, "source_stable": current == after,
               "host": {"platform": platform.platform(), "machine": platform.machine()},
               "protocol": {"nodes": [7164, 16384, 50771], "repeats": 21,
                            "operations": ["set_attr", "insert", "delete", "retype"],
                            "arms": ["clone_sharing_graph_pages", "clone_eager"],
                            "probe_source": "v3 mutation probe; rebuilt against targeted-unindex v4 graph source"},
               "capture": raw}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(OUT.relative_to(ROOT)); return 0

if __name__ == "__main__": raise SystemExit(main())
