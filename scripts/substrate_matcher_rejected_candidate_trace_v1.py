#!/usr/bin/env python3
"""Measure matcher candidate work absent from successful-binding trace rows."""
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
OUT = ROOT / "evaluation/reports/substrate_matcher_rejected_candidate_trace_v1_20260926.json"
V = lambda name: {"type": "Var", "name": name}
L = lambda value: {"type": "Lit", "value": value}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(candidate_count: int, traced: bool) -> dict:
    sub = _native.Substrate()
    pairs = []
    for i in range(candidate_count):
        src = sub.add_node("Candidate", {"accepted": 1 if i == 0 else 0})
        tgt = sub.add_node("Target", {})
        sub.add_edge_unchecked(src, "probe_edge", tgt, {})
        pairs.append((src, tgt))
    sub.add_rule({"name": f"candidate_filter_{candidate_count}",
                  "match": [["a", "probe_edge", "b"]],
                  "where": {"type": "Eq", "a": {"type": "Attr", "node": V("a"), "key": "accepted"},
                            "b": L(1)}, "effects": []})
    _native.Substrate.scale_audit_reset()
    _native.Substrate.scale_audit_set_enabled(True)
    _native.Substrate.runtime_access_trace_reset()
    _native.Substrate.runtime_access_trace_set_enabled(traced)
    outcome = sub.run_rules_report(20, False)
    events, dropped = sub.runtime_access_trace_snapshot()
    _native.Substrate.runtime_access_trace_set_enabled(False)
    audit = dict(_native.Substrate.scale_audit_snapshot())
    _native.Substrate.scale_audit_set_enabled(False)
    rows = [list(row) for row in events]
    return {"candidate_count": candidate_count, "trace_enabled": traced,
            "outcome": outcome, "events": rows,
            "event_count": sum(row[5] for row in rows), "dropped": dropped,
            "pattern_edge_events": sum(row[5] for row in rows if row[1] == "pattern_edge"),
            "candidate_attr_read_events": sum(row[5] for row in rows
                                                if row[1] == "term_attr_read" and row[3] == "accepted"),
            "scale_audit": audit}


def main() -> None:
    started = datetime.now(timezone.utc).isoformat()
    log_capture = start_console_capture("substrate-matcher-rejected-candidate-trace-v1-20260926")
    assert_measuring_engine()
    cells = []
    for n in (1, 9):
        plain, traced = run(n, False), run(n, True)
        cells.append({"candidate_count": n, "plain": plain, "traced": traced,
                      "semantic_match": (plain["outcome"]["progress_steps"], plain["outcome"]["status"])
                      == (traced["outcome"]["progress_steps"], traced["outcome"]["status"])})
    small, large = cells
    checks = {
        "engine_matches_current_source": True,
        "traced_untraced_semantics_match": all(c["semantic_match"] for c in cells),
        "plain_trace_is_empty": all(c["plain"]["event_count"] == 0 for c in cells),
        "candidate_counter_scales_1_to_9": (small["traced"]["scale_audit"].get("cand_tested") == 1
                                              and large["traced"]["scale_audit"].get("cand_tested") == 9),
        "successful_edge_trace_stays_one": all(c["traced"]["pattern_edge_events"] == 1 for c in cells),
        "predicate_reads_scale_with_candidates": (small["traced"]["candidate_attr_read_events"] == 1
                                                     and large["traced"]["candidate_attr_read_events"] == 9),
        "all_runs_settle": all(c[arm]["outcome"]["status"] == "fixed_point" for c in cells for arm in ("plain", "traced")),
        "no_trace_overflow": all(c["traced"]["dropped"] == 0 for c in cells),
    }
    source_files = ("runners/dsl/src/access_trace.rs", "runners/dsl/src/rewrite.rs",
                    "runners/dsl/src/scale_audit.rs", "scripts/substrate_matcher_rejected_candidate_trace_v1.py")
    print("probe checks before manifest capture:", json.dumps(checks, sort_keys=True), flush=True)
    log_ref = finish_console_capture(log_capture)
    run_manifest = capture_run_manifest(
        run_id="substrate-matcher-rejected-candidate-trace-v1-20260926",
        runner="scripts/substrate_matcher_rejected_candidate_trace_v1.py",
        protocol_files=("docs/research/engine_substrate/SUBSTRATE_BENCHMARK_PROTOCOL.md",
                        "docs/research/engine_substrate/SUBSTRATE_MATCHER_REJECTED_CANDIDATE_TRACE_V1_PREREG_20260926.md"),
        source_files=("runners/dsl/src/access_trace.rs", "runners/dsl/src/rewrite.rs",
                      "runners/dsl/src/scale_audit.rs", "runners/dsl/src/py.rs"),
        started_utc=started, exit_status=0 if all(checks.values()) else 1,
        stdout_stderr_capture=log_ref)
    ext = ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so"
    report = {"schema_version": 1, "run_id": "substrate-matcher-rejected-candidate-trace-v1-20260926",
              "claim_boundary": "Controlled one-edge candidate family confirms scale-audit candidate work and predicate reads while access trace records only accepted pattern-edge identity; not general matcher recall.",
              "environment": {"python": sys.version, "platform": platform.platform()},
              "provenance": {"commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                             "native_extension_sha256": sha(ext),
                             "native_build_manifest_sha256": sha(ROOT / "runners/dsl/python/substrate_rs/_native.build.json"),
                             "source_sha256": {p: sha(ROOT / p) for p in source_files}},
              "run_manifest": run_manifest, "checks": checks, "cells": cells}
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n")
    print(json.dumps({"checks": checks, "output": str(OUT)}, indent=2))
    if not all(checks.values()):
        raise SystemExit("matcher candidate trace probe failed")


if __name__ == "__main__":
    main()
