#!/usr/bin/env python3
"""Paired one/two-effect measurement of shape-decode cache-key trace rows."""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from substrate_rs import _native
from domains.engine_provenance import assert_measuring_engine
from substrate_run_manifest import capture_run_manifest, finish_console_capture, start_console_capture

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/substrate_sd_cache_key_trace_probe_v1_20260926.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(effect_count: int, traced: bool) -> dict:
    sub = _native.Substrate()
    part = sub.add_node("CodebookPart", {"cache_marker": "cache-only", "name": "held"})
    generator = sub.add_node("DimensionGenerator", {"cache_marker": "generator-only"})
    a = sub.add_node("Probe", {})
    b = sub.add_node("Probe", {})
    sub.add_edge_unchecked(a, "trigger", b, {})
    term = {"type": "DimInfer", "goal": {"type": "Lit", "value": 0},
            "codebook_type": "CodebookPart", "exclude": None,
            "generator_type": "DimensionGenerator", "max_dims": 1,
            "field": "supported"}
    effects = [["set_attr", "x", f"out{i}", {"__term__": term}]
               for i in range(effect_count)]
    sub.add_rule({"name": f"sd_cache_effects_{effect_count}",
                  "match": [["x", "trigger", "y"]], "where": None,
                  "effects": effects})
    _native.Substrate.runtime_access_trace_reset()
    _native.Substrate.runtime_access_trace_set_enabled(traced)
    outcome = sub.run_rules_report(20, False)
    events, dropped = sub.runtime_access_trace_snapshot()
    _native.Substrate.runtime_access_trace_set_enabled(False)
    rows = [list(row) for row in events]
    query_counts = {}
    for row in rows:
        if row[1] == "term_index_query":
            query_counts[row[3]] = query_counts.get(row[3], 0) + row[5]
    fingerprint_attr_reads = sum(row[5] for row in rows
                                 if row[1] == "term_attr_read"
                                 and row[2] in (part, generator))
    fingerprint_type_reads = sum(row[5] for row in rows
                                 if row[1] == "term_type_read"
                                 and row[2] in (part, generator))
    outputs = {f"out{i}": sub.node(a)["attrs"].get(f"out{i}")
               for i in range(effect_count)}
    return {"effect_count": effect_count, "trace_enabled": traced,
            "outcome": outcome, "outputs": outputs, "events": rows,
            "event_count": sum(row[5] for row in rows), "dropped": dropped,
            "query_count_by_codebook_type": query_counts,
            "fingerprint_attr_read_events": fingerprint_attr_reads,
            "fingerprint_type_read_events": fingerprint_type_reads}


def main() -> None:
    started = datetime.now(timezone.utc).isoformat()
    log_capture = start_console_capture("substrate-sd-cache-key-trace-probe-v1-20260926")
    assert_measuring_engine()
    cells = []
    for count in (1, 2):
        plain, traced = run(count, False), run(count, True)
        cells.append({"effect_count": count, "plain": plain, "traced": traced,
                      "semantic_match": (plain["outcome"], plain["outputs"])
                      == (traced["outcome"], traced["outputs"])})
    one, two = cells
    types = ("CodebookPart", "DimensionGenerator")
    checks = {
        "engine_matches_current_source": True,
        "traced_untraced_semantics_match": all(c["semantic_match"] for c in cells),
        "plain_arms_emit_no_events": all(c["plain"]["event_count"] == 0 for c in cells),
        "one_effect_records_two_queries_per_type": all(one["traced"]["query_count_by_codebook_type"].get(t) == 2 for t in types),
        "two_effects_double_queries_per_type": all(two["traced"]["query_count_by_codebook_type"].get(t) == 4 for t in types),
        "all_traced_arms_settle": all(c["traced"]["outcome"]["status"] == "fixed_point" for c in cells),
        "no_trace_overflow": all(c["traced"]["dropped"] == 0 for c in cells),
    }
    source_files = ("runners/dsl/src/access_trace.rs", "runners/dsl/src/term.rs",
                    "runners/dsl/src/rewrite.rs", "scripts/substrate_sd_cache_key_trace_probe_v1.py")
    print("probe checks before manifest capture:", json.dumps(checks, sort_keys=True), flush=True)
    log_ref = finish_console_capture(log_capture)
    run_manifest = capture_run_manifest(
        run_id="substrate-sd-cache-key-trace-probe-v1-20260926",
        runner="scripts/substrate_sd_cache_key_trace_probe_v1.py",
        protocol_files=("docs/research/engine_substrate/SUBSTRATE_BENCHMARK_PROTOCOL.md",
                        "docs/research/engine_substrate/SUBSTRATE_SD_CACHE_KEY_TRACE_PROBE_V1_PREREG_20260926.md"),
        source_files=("runners/dsl/src/access_trace.rs", "runners/dsl/src/term.rs",
                      "runners/dsl/src/rewrite.rs", "runners/dsl/src/shape_decode.rs"),
        started_utc=started, exit_status=0 if all(checks.values()) else 1,
        stdout_stderr_capture=log_ref)
    ext = ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so"
    manifest = ROOT / "runners/dsl/python/substrate_rs/_native.build.json"
    report = {"schema_version": 1, "run_id": "substrate-sd-cache-key-trace-probe-v1-20260926",
              "claim_boundary": "Bounded paired probe confirms typed fingerprint query markers are emitted for each computed DimInfer key construction; no general access recall, hit/miss counter, overhead, or speedup claim.",
              "environment": {"python": sys.version, "platform": platform.platform()},
              "provenance": {"commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                             "native_extension_sha256": sha(ext),
                             "native_build_manifest_sha256": sha(manifest),
                             "source_sha256": {p: sha(ROOT / p) for p in source_files}},
              "run_manifest": run_manifest, "checks": checks, "cells": cells}
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n")
    print(json.dumps({"checks": checks, "output": str(OUT)}, indent=2))
    if not all(checks.values()):
        raise SystemExit("SD cache-key trace probe failed")


if __name__ == "__main__":
    main()
