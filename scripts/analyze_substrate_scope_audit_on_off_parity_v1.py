#!/usr/bin/env python3
"""Independent audit-on/off state, settlement, and integrity verification."""
from __future__ import annotations

import hashlib
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
REPORT = ROOT / "evaluation/reports/substrate_scope_audit_on_off_parity_v1_20260926.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    data = json.loads(REPORT.read_text())
    files = {"protocol": ROOT / "docs/research/engine_substrate/SUBSTRATE_SCOPE_AUDIT_ON_OFF_PARITY_PREREG_20260926.md",
             "runner": ROOT / "scripts/substrate_scope_audit_on_off_parity_v1.py",
             "base_runner": ROOT / "scripts/substrate_frame_topology_matched_scale_v1.py",
             "graph_rs": ROOT / "runners/dsl/src/graph.rs", "substrate_rs": ROOT / "runners/dsl/src/substrate.rs",
             "rewrite_rs": ROOT / "runners/dsl/src/rewrite.rs", "py_rs": ROOT / "runners/dsl/src/py.rs",
             "scale_audit_rs": ROOT / "runners/dsl/src/scale_audit.rs",
             "native": ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so"}
    integrity = {k: sha(v) == data["inputs"][k] for k, v in files.items()}
    from domains.engine_provenance import build_is_stale, rust_source_fingerprint
    integrity["rust_source_fingerprint"] = rust_source_fingerprint(str(ROOT)) == data["inputs"]["rust_source_fingerprint"]
    integrity["build_current"] = not build_is_stale(str(ROOT))
    summaries, checks_all = [], []
    for row in data["rows"]:
        topo_checks = []
        wall = {"event_off": [], "event_on": [], "full_off": [], "full_on": []}
        for rep in row["repetitions"]:
            eo, en, fo, fn = (rep[x] for x in ("event_off", "event_on", "full_off", "full_on"))
            checks = {
                "event_audit_semantics_identical": all(eo["phases"][i]["projection"] == en["phases"][i]["projection"] for i in (0, 1)),
                "full_audit_semantics_identical": all(fo["phases"][i]["projection"] == fn["phases"][i]["projection"] for i in (0, 1)),
                "event_full_parity_both_modes": all(eo["phases"][i]["projection"] == fo["phases"][i]["projection"] == en["phases"][i]["projection"] == fn["phases"][i]["projection"] for i in (0, 1)),
                "event_queue_settled_and_all_owners_reported": all(p["settlement"]["complete"] and p["settlement"]["affected_owners"] == eo["frame_ids"] for arm in (eo, en) for p in arm["phases"]),
                "full_fixed_point_all_phases": all(p["status"] == "fixed_point" for arm in (fo, fn) for p in arm["phases"]),
                "audit_off_counters_zero": all(all(int(v) == 0 for v in p["audit"].values()) for arm in (eo, fo) for p in arm["phases"]),
                "audit_on_counters_nonzero": all(int(p["audit"].get("cand_enum", 0)) > 0 and int(p["audit"].get("term_evals_total", 0)) > 0 for arm in (en, fn) for p in arm["phases"]),
                "per_rule_audit_disabled": all(arm["per_rule_rows"] == 0 for arm in (eo, en, fo, fn)),
                "fixture_sizes_equal": all(arm["rule_count"] == 4 and len(arm["edges"]) == row["frame_count"] - 1 for arm in (eo, en, fo, fn)),
            }
            topo_checks.append(checks); checks_all.extend(checks.values())
            for name, arm in (("event_off", eo), ("event_on", en), ("full_off", fo), ("full_on", fn)):
                wall[name].append(sum(p["wall_ns"] for p in arm["phases"]) / 1e6)
        med = {k: statistics.median(v) for k, v in wall.items()}
        summaries.append({"topology": row["topology"], "repetitions": len(topo_checks),
                          "all_repeats_pass": all(all(c.values()) for c in topo_checks),
                          "median_event_off_ms": med["event_off"], "median_event_on_ms": med["event_on"],
                          "median_full_off_ms": med["full_off"], "median_full_on_ms": med["full_on"],
                          "event_audit_time_ratio": med["event_on"] / med["event_off"],
                          "full_audit_time_ratio": med["full_on"] / med["full_off"], "repeat_checks": topo_checks})
    result = {"protocol_id": data["protocol_id"], "integrity": integrity,
              "all_gates_pass": all(integrity.values()) and all(checks_all), "rows": summaries}
    out = REPORT.with_name("substrate_scope_audit_on_off_parity_v1_20260926_analysis.json")
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"analysis": str(out), "all_gates_pass": result["all_gates_pass"],
                      "integrity": integrity,
                      "rows": [{k: r[k] for k in ("topology", "repetitions", "all_repeats_pass", "median_event_off_ms", "median_event_on_ms", "event_audit_time_ratio", "median_full_off_ms", "median_full_on_ms", "full_audit_time_ratio")} for r in summaries]}, indent=2))
    if not result["all_gates_pass"]:
        raise SystemExit("integrity or independent audit-parity check failed")


if __name__ == "__main__":
    main()
