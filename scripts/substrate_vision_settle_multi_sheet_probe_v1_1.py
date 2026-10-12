#!/usr/bin/env python3
"""Probe whether vision_settle's global SUnit fold crosses World roots."""
from __future__ import annotations

import hashlib
import json
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "seeds/vision_settle.json"
PREREG = ROOT / "docs/research/engine_substrate/SUBSTRATE_VISION_SETTLE_MULTI_SHEET_PROBE_V1_1_AMENDMENT_20260925.md"
OUT = ROOT / "evaluation/reports/substrate_vision_settle_multi_sheet_probe_v1_1_20260925.json"
CAP = 10_000


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def one_arm(sr, seed_doc, b_state):
    from substrate.seed_loader import engine_rules_only
    outer = sr.Substrate()
    inner = outer._inner
    manifest = dict(engine_rules_only(seed_doc))
    manifest["rules"] = [r for r in manifest.get("rules", []) if r.get("name") == "st_settle"]
    if len(manifest["rules"]) != 1:
        raise RuntimeError("expected only vision_settle.st_settle")
    inner.load_seed_manifest(manifest)
    params = inner.nodes("SettleParams")
    if len(params) != 1:
        raise RuntimeError(f"loaded vision_settle manifest supplied {len(params)} SettleParams nodes")
    inner.set_attr(params[0], "settle", 1.0)
    roots, cells = [], []
    for label, state in (("A", 1.0), ("B", b_state)):
        root = inner.add_node("World", {"name": label, "step": 0.0})
        pair = [inner.add_node("SUnit", {"act": state, "aff": 0.0,
                                             "aff_step": 0.0, "act_next": 0.0})
                for _ in range(2)]
        inner.add_edge_unchecked(root, "has_sunit", pair[0], {})
        inner.add_edge_unchecked(root, "has_sunit", pair[1], {})
        inner.add_edge_unchecked(pair[0], "sunit_neighbour", pair[1], {})
        inner.add_edge_unchecked(pair[1], "sunit_neighbour", pair[0], {})
        roots.append(root); cells.append(pair)
    progress = inner.run_rules(CAP)
    state_after = [[float(inner.node(u)["attrs"].get("act_next", 0.0)) for u in pair]
                   for pair in cells]
    return {"b_initial_act": b_state, "progress": progress,
            "a_act_next": state_after[0], "b_act_next": state_after[1],
            "complete": progress < CAP}


def main():
    import substrate_rs as sr
    from substrate_rs import _native
    from domains.engine_provenance import engine_provenance
    doc = json.loads(SEED.read_text())
    arms = [one_arm(sr, doc, b_state) for b_state in (0.0, 1.0)]
    result = {
        "run_id": "vision-settle-multi-sheet-coupling-probe-20260925",
        "protocol_path": str(PREREG.relative_to(ROOT)),
        "arms": arms,
        "expected_a_act_next": [0.5, 0.0],
        "both_arms_run_rule": all(a["progress"] > 0 and a["complete"] for a in arms),
        "a_matches_global_mean_prediction": all(
            abs(got - expected) <= 1e-7
            for arm, expected in zip(arms, (0.5, 0.0)) for got in arm["a_act_next"]),
        "changing_b_changes_a": arms[0]["a_act_next"] != arms[1]["a_act_next"],
        "provenance": {
            "python": sys.version, "platform": platform.platform(),
            "runner_sha256": sha(Path(__file__)), "protocol_sha256": sha(PREREG),
            "seed_sha256": sha(SEED), "native_extension_path": str(Path(_native.__file__).resolve()),
            "native_extension_sha256": sha(Path(_native.__file__).resolve()),
            "engine_provenance": engine_provenance(),
            "source_sha256": {name: sha(ROOT / "runners/dsl/src" / name)
                              for name in ("rewrite.rs", "substrate.rs", "term.rs", "py.rs")},
        },
    }
    result["pass"] = (result["both_arms_run_rule"] and result["a_matches_global_mean_prediction"]
                      and result["changing_b_changes_a"])
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "arms": arms,
                      "checks": {k: result[k] for k in (
                          "both_arms_run_rule", "a_matches_global_mean_prediction",
                          "changing_b_changes_a", "pass")}}, indent=2))
    if not result["pass"]:
        raise SystemExit("vision multi-sheet coupling probe did not match its preregistered prediction")


if __name__ == "__main__":
    main()
