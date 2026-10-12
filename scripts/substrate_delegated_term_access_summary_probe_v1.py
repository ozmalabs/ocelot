#!/usr/bin/env python3
"""Ensure delegated graph-reading Terms conservatively report reads_any."""
from __future__ import annotations

import json
import hashlib
from pathlib import Path
from substrate_rs import _native

V = lambda name: {"type": "Var", "name": name}
L = lambda value: {"type": "Lit", "value": value}
CASES = {
    "motor_compose": {"type": "MotorCompose", "episode": V("ep"), "policy": V("po"), "candidate": V("ca")},
    "future_manifold_projection": {"type": "FutureManifoldProjection", "episode": V("ep"), "policy": V("po"), "source": V("src"), "field": "value"},
    "future_manifold_selection": {"type": "FutureManifoldSelection", "episode": V("ep"), "policy": V("po"), "candidates": V("cs"), "field": "selected"},
    "transform_decode": {"type": "TransformDecode", "goal": L([])},
    "dim_infer": {"type": "DimInfer", "goal": L([])},
    "gen_infer": {"type": "GenInfer", "goal": L([])},
    "net_forward": {"type": "NetForward", "assemblage": V("a"), "inputs": L([])},
    "enigma_crib": {"type": "EnigmaCrib", "candidate": V("c")},
    "enigma_bombe": {"type": "EnigmaBombe", "candidate": V("c")},
    "enigma_bombe_witness": {"type": "EnigmaBombeWitness", "candidate": V("c")},
    "track_identity_correspondence": {"type": "TrackIdentityCorrespondence", "prev": V("p"), "cur": V("c"), "feature_key": "features", "radius": L(1.0)},
}

def main() -> None:
    root = Path(__file__).resolve().parents[1]
    rows = []
    for name, term in CASES.items():
        sub = _native.Substrate()
        sub.add_rule({"name": f"access_summary_{name}", "match": [["a", "probe_edge", "b"]], "where": term, "effects": []})
        access = sub.rule_access_sets()[0]
        rows.append({"case": name, "reads_any": bool(access[6]), "read_keys": list(access[3])})
    checks = {"all_delegated_graph_terms_are_wildcard_readers": all(row["reads_any"] for row in rows), "eleven_families_present": len(rows) == 11}
    extension = root / "runners/dsl/python/substrate_rs/_native.abi3.so"
    report = {
        "schema_version": 1,
        "run_id": "substrate-delegated-term-access-summary-probe-v1-20260926",
        "claim_boundary": "Checks static wildcard summaries for selected delegated graph-reading Terms; does not prove dynamic trace completeness or helper behavior.",
        "provenance": {
            "native_extension_sha256": hashlib.sha256(extension.read_bytes()).hexdigest(),
            "source_sha256": hashlib.sha256((root / "runners/dsl/src/rewrite.rs").read_bytes()).hexdigest(),
            "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
        "checks": checks,
        "cases": rows,
    }
    output = root / "evaluation/reports/substrate_delegated_term_access_summary_probe_v1_20260926.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": checks, "cases": rows, "output": str(output)}, indent=2))
    if not all(checks.values()):
        raise SystemExit("delegated Term static access summary probe failed")

if __name__ == "__main__":
    main()
