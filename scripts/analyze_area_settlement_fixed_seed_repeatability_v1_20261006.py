#!/usr/bin/env python3
"""Analyze uninstrumented global workers under the fixed hash seed."""
from __future__ import annotations
import gzip, hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAPTURE = ROOT / "evaluation/reports/area_settlement_fixed_seed_repeatability_v1_20261006/capture.json.gz"
LOCK = ROOT / "evaluation/substrate_capability/area_settlement_fixed_seed_repeatability_v1_20261006_lock.json"
OUT = ROOT / "evaluation/reports/area_settlement_fixed_seed_repeatability_v1_analysis_20261006.json"
ANALYZER = Path(__file__).resolve()

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

raw = CAPTURE.read_bytes()
capture = json.loads(gzip.decompress(raw))
runs = capture["runs"]
checks = {
    "three_distinct_workers": len(runs) == 3 and len({r["pid"] for r in runs}) == 3,
    "source_lock_matches": json.loads(LOCK.read_text()) == capture["locked_inputs"],
    "source_stable": capture["post_run_inputs"] == capture["locked_inputs"] and all(r["worker_source_stable"] for r in runs),
    "fixed_hash_seed_zero": capture["environment"].get("PYTHONHASHSEED") == "0",
    "seven_turns": all(len(r["turns"]) == 7 for r in runs),
    "complete_final_snapshots": all(bool(r["turns"][-1].get("final_snapshot_zlib_b64")) for r in runs),
}
turns = []
for ti in range(7):
    rows = [r["turns"][ti] for r in runs]
    wls = [r["graph_wl_sha256"] for r in rows]
    replies = [r["reply"] for r in rows]
    counts = [(r["node_count"], r["edge_count"]) for r in rows]
    checks[f"wl_repeat__{ti}"] = len(set(wls)) == 1
    checks[f"reply_repeat__{ti}"] = len(set(replies)) == 1
    checks[f"count_repeat__{ti}"] = len(set(counts)) == 1
    turns.append({"turn_index": ti, "prompt": rows[0]["prompt"], "wl_by_worker": wls,
                  "reply_by_worker": replies, "node_edge_counts_by_worker": counts})
final_raw_hashes = [r["final_graph"]["sha256"] for r in runs]
final_wl_hashes = [r["final_graph"]["wl_sha256"] for r in runs]
checks["final_raw_graph_hash_repeat"] = len(set(final_raw_hashes)) == 1
checks["final_wl_graph_hash_repeat"] = len(set(final_wl_hashes)) == 1
failed = [k for k,v in checks.items() if not v]
analysis = {"schema_version": 1, "capture_sha256": hashlib.sha256(raw).hexdigest(),
    "capture_bytes_gzip": CAPTURE.stat().st_size, "lock_sha256": sha(LOCK),
    "analyzer_sha256": sha(ANALYZER), "checks": checks,
    "capture_integrity_pass": all(checks[k] for k in ("three_distinct_workers", "source_lock_matches", "source_stable", "fixed_hash_seed_zero", "seven_turns", "complete_final_snapshots")),
    "repeatability_pass": all(v for k,v in checks.items() if "repeat__" in k or "hash_repeat" in k),
    "all_checks_pass": not failed, "failed_checks": failed,
    "raw_final_graph_hashes": final_raw_hashes, "final_wl_hashes": final_wl_hashes,
    "turns": turns,
    "interpretation": "This is the original uninstrumented global worker under PYTHONHASHSEED=0. WL equality is an ID-independent structural invariant, not a complete isomorphism proof."}
OUT.write_text(json.dumps(analysis,indent=2,sort_keys=True)+"\n")
print(json.dumps({"analysis":str(OUT.relative_to(ROOT)),"capture_integrity_pass":analysis["capture_integrity_pass"],"repeatability_pass":analysis["repeatability_pass"],"failed_checks":failed},indent=2))
