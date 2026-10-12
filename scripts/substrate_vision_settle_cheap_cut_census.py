#!/usr/bin/env python3
"""Static dependency-cut census for the authored vision_settle rules."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "seeds/vision_settle.json"
PREREG = ROOT / "docs/research/engine_substrate/SUBSTRATE_VISION_SETTLE_CHEAP_CUT_CENSUS_PREREG_20260925.md"
OUT = ROOT / "evaluation/reports/substrate_vision_settle_cheap_cut_census_20260925.json"
N_VALUES, FRAME_SIZES = (16, 64, 256, 1024), (4, 16, 64)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def walk(obj):
    if isinstance(obj, dict):
        yield obj
        for value in obj.values():
            yield from walk(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from walk(value)


def has_local_neighbor_act_fold(rule):
    for term in walk(rule):
        if term.get("type") != "Fold":
            continue
        source = term.get("source", {})
        if source.get("type") != "Neighbours" or source.get("edge_type") != "sunit_neighbour":
            continue
        if any(x.get("type") == "Attr" and x.get("key") == "act" for x in walk(term.get("body"))):
            return True
    return False


def has_global_sunit_act_fold(rule):
    for term in walk(rule):
        if term.get("type") != "Fold":
            continue
        source = term.get("source", {})
        if source.get("type") != "NodesOfType" or source.get("node_type") != "SUnit":
            continue
        if any(x.get("type") == "Attr" and x.get("key") == "act" for x in walk(term.get("body"))):
            return True
    return False


def main():
    doc = json.loads(SEED.read_text())
    rules = {r["name"]: r for r in doc["rules"]}
    settle, commit = rules["st_settle"], rules["st_commit"]
    local = has_local_neighbor_act_fold(settle)
    global_read = has_global_sunit_act_fold(settle)
    match_edges = settle["match"]
    has_sunit_match = (settle.get("match_type") == "SUnit" and match_edges == [["r", "has_sunit", "u"]])
    writes_next = any(e[:3] == ["set_attr", "u", "act_next"] for e in settle["effects"])
    commit_copies = any(e[:3] == ["set_attr", "u", "act"] and
                        e[3].get("__term__", {}).get("type") == "Attr" and
                        e[3]["__term__"].get("key") == "act_next" for e in commit["effects"])
    cases = []
    for n in N_VALUES:
        for k in FRAME_SIZES:
            if n % k:
                continue
            frames = n // k
            cases.append({
                "units": n, "frame_units": k, "frame_count": frames,
                "global_input_incidences": n * n,
                "cross_frame_input_incidences": n * (n - k),
                "cross_frame_incidence_share": (n - k) / n,
                "external_state_per_frame": n - k,
                "complete_dependency_graph_treewidth": n - 1,
            })
    global_folds = [t for t in walk(settle) if t.get("type") == "Fold" and
                    t.get("source", {}).get("type") == "NodesOfType" and
                    t["source"].get("node_type") == "SUnit"]
    source_substrate = (ROOT / "runners/dsl/src/substrate.rs").read_text()
    source_rewrite = (ROOT / "runners/dsl/src/rewrite.rs").read_text()
    scoped_mt_api = bool(re.search(r"pub fn run_rules_scoped\s*\([\s\S]{0,500}?scope_mt:\s*Option<NodeID>", source_substrate))
    mt_owned_has_concept = ("pub fn mt_owned_nodes" in source_rewrite and
                            "graph.neighbours(mt, Some(has_concept))" in source_rewrite)
    payload = {
        "run_id": "vision-settle-cheap-cut-static-census-20260925",
        "evidence_type": "static_source_census_symbolic_counts_not_runtime_measurements",
        "protocol_path": str(PREREG.relative_to(ROOT)),
        "source_signature": {
            "settle_batch": bool(settle.get("batch")), "commit_batch": bool(commit.get("batch")),
            "one_sunit_membership_match": has_sunit_match,
            "settle_writes_act_next": writes_next, "commit_copies_act_next_to_act": commit_copies,
            "local_neighbor_act_fold": local, "global_all_sunit_act_fold": global_read,
            "global_fold_filter_references_world_or_frame": any(
                "where" in t or "predicate" in t for t in global_folds),
        },
        "inference": "Global NodesOfType(SUnit) Act fold makes every SUnit output depend on every SUnit input; the primal dependency graph is K_N.",
        "cases": cases,
        "scope_api_source": {
            "run_rules_scoped_argument": "scope_mt: Option<NodeID>" if scoped_mt_api else None,
            "owned_nodes": "scope Microtheory plus one has_concept hop" if mt_owned_has_concept else None,
            "arbitrary_sunit_frame_api_found": False,
        },
        "provenance": {
            "seed_sha256": sha(SEED), "protocol_sha256": sha(PREREG),
            "runner_sha256": sha(Path(__file__)),
            "substrate_rs_sha256": sha(ROOT / "runners/dsl/src/substrate.rs"),
            "rewrite_rs_sha256": sha(ROOT / "runners/dsl/src/rewrite.rs"),
        },
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)),
                      "source_signature": payload["source_signature"],
                      "cases": cases, "provenance": payload["provenance"]}, indent=2))
    required = (settle.get("batch") and commit.get("batch") and has_sunit_match
                and writes_next and commit_copies and local and global_read)
    if not required:
        raise SystemExit("vision_settle rule no longer matches the preregistered dependency signature")


if __name__ == "__main__":
    main()
