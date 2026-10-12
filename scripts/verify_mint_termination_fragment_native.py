#!/usr/bin/env python3
"""Check admitted mint-fragment rules through the live native loader/scheduler."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANALYZER_PATH = ROOT / "scripts/analyze_mint_termination_fragment.py"
sys.path.insert(0, str(ROOT / "scripts"))
from analyze_mint_termination_fragment import analyze  # noqa: E402

RULE = {"name": "recursive_finite_key", "match": [["x", "link", "y"]], "effects": [
    ["add_node_if_absent", "w", "Witness", {"tag": "shared"}],
    ["add_edge", "y", "link", "w", {}],
]}
EXPECTED_ACCESS = {
    "reads": ["edge:link", "type:Witness"],
    "term_edge_reads": [],
    "writes": ["attr:tag", "edge:link", "type:Witness"],
    "reads_any": False,
    "writes_any": False,
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    env = {**os.environ, "PYTHONPATH": f"{ROOT / 'runners/dsl/python'}:{ROOT}"}
    stale = subprocess.check_output(
        [sys.executable, "-c", "from domains.engine_provenance import build_is_stale; print('\\n'.join(build_is_stale('.')))"]
        , cwd=ROOT, env=env, text=True).strip()
    if stale:
        raise SystemExit(f"native build is stale:\n{stale}")
    from substrate_rs import _native

    s = _native.Substrate()
    # The classifier receives the complete logical graph at the point closure
    # starts, including the two seed nodes and their asserted initial edge.
    analysis = analyze([RULE], ["seed0", "seed1"],
                       [["seed0", "link", "seed1"]])
    rid = s.add_rule(RULE)
    raw_access = s.rule_access_sets()[rid]
    access = {"name": raw_access[1], "active": raw_access[2], "reads": raw_access[3],
              "term_edge_reads": raw_access[4], "writes": raw_access[5],
              "reads_any": raw_access[6], "writes_any": raw_access[7]}
    access_exact = {k: access[k] for k in EXPECTED_ACCESS} == EXPECTED_ACCESS

    # Exercise a rule first at empty state, then enable it via a post-install edge
    # insertion. The second report must wake the registered reader and close.
    empty_report = s.run_rules_report(100, False)
    a, b = s.add_node("Seed"), s.add_node("Seed")
    s.add_edge_unchecked(a, "link", b)
    triggered_report = s.run_rules_report(100, False)
    final_nodes, final_edges = s.node_count(), s.edge_count()
    exact_state = final_nodes == 3 and final_edges == 3 and \
        s.has_edge(a, "link", b) and s.has_edge(b, "link", _native.NodeID(2)) and \
        s.has_edge(_native.NodeID(2), "link", _native.NodeID(2))
    report_ok = empty_report["status"] == "fixed_point" and triggered_report["status"] == "fixed_point"
    progress_with_trigger = triggered_report["progress_steps"] == 2
    observed_le_bound = triggered_report["progress_steps"] <= analysis["progress_steps_upper_bound"]

    source_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    native_so = ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so"
    result = {
        "schema_version": 1,
        "run_id": f"mint-native-parity-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}",
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "runner_sha256": source_hash,
        "analyzer_sha256": hashlib.sha256(ANALYZER_PATH.read_bytes()).hexdigest(),
        "native_sha256": hashlib.sha256(native_so.read_bytes()).hexdigest(),
        "python": sys.version.split()[0], "platform": platform.platform(),
        "rule_spec": RULE, "classifier": analysis,
        "native_rule_index": rid, "native_access": access, "expected_access": EXPECTED_ACCESS,
        "access_set_exact": access_exact,
        "empty_state_report": empty_report, "post_mutation_report": triggered_report,
        "final_state": {"node_count": final_nodes, "edge_count": final_edges,
                        "expected_node_count": 3, "expected_edge_count": 3,
                        "expected_edges_present": exact_state},
        "progress_bound": analysis["progress_steps_upper_bound"],
        "observed_progress_within_bound": observed_le_bound,
        "checks": {"classifier_accepts": analysis["accepted"], "access_set_exact": access_exact,
                   "reports_reach_fixed_point": report_ok, "triggered_progress_is_two": progress_with_trigger,
                   "exact_expected_state": exact_state, "progress_within_bound": observed_le_bound},
        "all_checks_pass": all([analysis["accepted"], access_exact, report_ok, progress_with_trigger,
                                 exact_state, observed_le_bound]),
        "claim_limit": "one native-loaded synthetic rule and one post-install edge mutation; not general scheduler completeness",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_checks_pass": result["all_checks_pass"], "checks": result["checks"]}, sort_keys=True))
    return 0 if result["all_checks_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
