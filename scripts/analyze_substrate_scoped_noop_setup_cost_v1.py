#!/usr/bin/env python3
"""Independent validation and robust summaries for scoped no-op cost probe."""
from __future__ import annotations

import hashlib
import json
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
REPORT = ROOT / "evaluation/reports/substrate_scoped_noop_setup_cost_v1_20260926.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def percentile(values, q):
    values = sorted(values)
    if len(values) == 1:
        return values[0]
    pos = (len(values) - 1) * q
    low = int(math.floor(pos)); high = int(math.ceil(pos))
    return values[low] + (values[high] - values[low]) * (pos - low)


def slope(xs, ys):
    mx, my = statistics.mean(xs), statistics.mean(ys)
    den = sum((x - mx) ** 2 for x in xs)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den if den else 0.0


def main():
    data = json.loads(REPORT.read_text())
    paths = {"protocol": ROOT / "docs/research/engine_substrate/SUBSTRATE_SCOPED_NOOP_SETUP_COST_PREREG_20260926.md",
             "runner": ROOT / "scripts/substrate_scoped_noop_setup_cost_v1.py",
             "graph_rs": ROOT / "runners/dsl/src/graph.rs", "substrate_rs": ROOT / "runners/dsl/src/substrate.rs",
             "rewrite_rs": ROOT / "runners/dsl/src/rewrite.rs", "py_rs": ROOT / "runners/dsl/src/py.rs",
             "scale_audit_rs": ROOT / "runners/dsl/src/scale_audit.rs",
             "native": ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so"}
    integrity = {k: sha(p) == data["inputs"][k] for k, p in paths.items()}
    from domains.engine_provenance import build_is_stale, rust_source_fingerprint
    integrity["rust_source_fingerprint"] = rust_source_fingerprint(str(ROOT)) == data["inputs"]["rust_source_fingerprint"]
    integrity["build_current"] = not build_is_stale(str(ROOT))
    checks, per_api = [], defaultdict(lambda: defaultdict(list))
    by_cell = []
    for row in data["rows"]:
        count = int(row["active_rule_count"])
        for rep in row["repetitions"]:
            for arm in rep["arms"]:
                counters = arm["global_counters"]
                check = {
                    "zero_progress_and_state_parity": arm["all_calls_fixed_point"] and arm["state_unchanged"] and arm["before"] == arm["after"],
                    "correct_rule_count": int(arm["before"]["rule_count"]) == count,
                    "audit_off_is_zero": not arm["audit_enabled"] or None,
                    "candidate_term_counters_zero": int(counters.get("cand_enum", 0)) == 0 and int(counters.get("term_evals_total", 0)) == 0,
                    "per_rule_counters_disabled": int(arm["per_rule_rows"]) == 0,
                }
                if not arm["audit_enabled"]:
                    check["audit_off_is_zero"] = all(int(v) == 0 for v in counters.values())
                else:
                    check["audit_off_is_zero"] = True
                if arm["audit_enabled"] and count > 0 and arm["api"].startswith("scoped"):
                    check["scoped_attempt_count_exact"] = int(counters.get("rule_enumerations", 0)) == count * int(arm["calls"])
                else:
                    check["scoped_attempt_count_exact"] = True
                checks.append(check)
                per_api[(arm["api"], bool(arm["audit_enabled"]))][count].append(float(arm["ns_per_call"]))
            by_cell.append((count, rep["repeat"], {(a["api"], bool(a["audit_enabled"])): a for a in rep["arms"]}))
    summaries = []
    for api in data["apis"]:
        for enabled in (False, True):
            groups = per_api[(api, enabled)]
            xs, ys = [], []
            for count in data["rule_counts"]:
                vals = groups[int(count)]
                med = statistics.median(vals)
                xs.append(int(count)); ys.append(med)
                summaries.append({"api": api, "audit_enabled": enabled, "active_rule_count": int(count),
                                  "repeats": len(vals), "median_ns_per_call": med,
                                  "p10_ns_per_call": percentile(vals, 0.10),
                                  "p90_ns_per_call": percentile(vals, 0.90)})
            if api.startswith("scoped"):
                # Add fitted slope metadata to the first row for this arm.
                for item in summaries:
                    if item["api"] == api and item["audit_enabled"] == enabled:
                        item["fitted_ns_per_active_rule"] = slope(xs, ys)
    paired_report_over_basic = []
    for count in data["rule_counts"]:
        for enabled in (False, True):
            diffs = []
            for cell_count, rep, arms in by_cell:
                if cell_count == count:
                    diffs.append(float(arms[("scoped_report", enabled)]["ns_per_call"]) - float(arms[("scoped_basic", enabled)]["ns_per_call"]))
            paired_report_over_basic.append({"active_rule_count": int(count), "audit_enabled": enabled,
                                             "median_report_minus_basic_ns_per_call": statistics.median(diffs)})
    all_pass = all(integrity.values()) and all(all(x.values()) for x in checks)
    result = {"protocol_id": data["protocol_id"], "integrity": integrity, "all_gates_pass": all_pass,
              "repeat_arm_checks": checks, "per_api_summaries": summaries,
              "paired_scoped_report_minus_basic": paired_report_over_basic}
    out = REPORT.with_name("substrate_scoped_noop_setup_cost_v1_20260926_analysis.json")
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    compact_keys = ("api", "audit_enabled", "active_rule_count", "median_ns_per_call", "p10_ns_per_call", "p90_ns_per_call", "fitted_ns_per_active_rule")
    compact = [{k: x[k] for k in compact_keys if k in x} for x in summaries]
    print(json.dumps({"analysis": str(out), "all_gates_pass": all_pass, "integrity": integrity,
                      "summaries": compact, "report_minus_basic": paired_report_over_basic}, indent=2))
    if not all_pass:
        raise SystemExit("integrity or independent no-op setup gate failed")


if __name__ == "__main__":
    main()
