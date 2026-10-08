#!/usr/bin/env python3
"""Source-locked microbenchmark for edge identity candidate extraction."""
from __future__ import annotations
import hashlib, json, platform, statistics, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
SOURCE = ROOT / "domains/edit_ops.py"
RUNNER = Path(__file__).resolve()
OUT = ROOT / "evaluation/reports/edge_identity_site_scaling_v1_20261002.json"
LOCK = ROOT / "evaluation/substrate_capability/edge_identity_site_scaling_v1_lock_20261002.json"
COUNTS = (1, 2, 4, 8, 16, 32, 64, 128, 256)
TRIALS, WARMUPS = 7, 2

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def frozen() -> dict:
    return {"domains/edit_ops.py": sha(SOURCE),
            "evaluation/substrate_capability/measure_edge_identity_site_scaling_v1.py": sha(RUNNER),
            "python": sys.version, "platform": platform.platform()}

def synthetic_rule(m: int) -> dict:
    attrs = {f"f{i:03d}": {"__term__": {"type": "Attr",
             "node": {"type": "Var", "name": "input"}, "key": f"f{i:03d}"}}
             for i in range(m)}
    return {"match": [["agent", "has_input", "input"]],
            "effects": [["add_node", "fresh", "SyntheticGoal", attrs],
                        ["add_edge", "agent", "has_goal", "fresh"]]}

def main() -> int:
    from domains.edit_ops import find_edge_identity_sites
    if sys.argv[1:] == ["--lock"]:
        if LOCK.exists() or OUT.exists(): raise SystemExit("refusing to overwrite existing capture")
        LOCK.write_text(json.dumps({"schema":"EdgeIdentitySiteScalingV1Lock",
          "sources":frozen(), "attribute_counts":COUNTS, "warmups":WARMUPS,
          "trials":TRIALS, "scope":"site extraction only; synthetic direct bound Attr values"},
          indent=2, sort_keys=True)+"\n")
        print(LOCK.relative_to(ROOT)); return 0
    if sys.argv[1:] != ["--run"]: raise SystemExit("usage: --lock or --run")
    lock = json.loads(LOCK.read_text())
    if frozen() != lock["sources"]: raise SystemExit("source drift from lock")
    rows=[]
    for m in lock["attribute_counts"]:
        rule=synthetic_rule(m)
        for _ in range(WARMUPS): find_edge_identity_sites(rule)
        times=[]; sites=None
        for _ in range(TRIALS):
            t=time.perf_counter_ns(); got=find_edge_identity_sites(rule)
            times.append(time.perf_counter_ns()-t); sites=got
        attrs=[s for s in sites if s.get("scope")=="node_attrs"]
        expected=m + m*(m-1)//2 + (1 if m>2 else 0)
        rows.append({"attribute_fields":m,"total_sites":len(sites),"attribute_sites":len(attrs),
          "expected_attribute_sites":expected,"median_ns":int(statistics.median(times)),
          "trial_ns":times})
    if frozen() != lock["sources"]: raise SystemExit("source drift during capture")
    OUT.write_text(json.dumps({"schema":"EdgeIdentitySiteScalingV1Results",
      "lock_sha256":sha(LOCK),"sources":frozen(),"rows":rows},indent=2,sort_keys=True)+"\n")
    print(OUT.relative_to(ROOT)); return 0

if __name__ == "__main__": raise SystemExit(main())
