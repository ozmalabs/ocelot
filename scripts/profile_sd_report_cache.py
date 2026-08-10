#!/usr/bin/env python3
"""Profile SD full-report reuse against a same-engine cache-busted control.

The control varies ``beam`` between the three field projections. On an exact
single-part decode this does not change the answer, but it makes the requests
semantically distinct cache keys. Thus both arms run in one binary and differ
only in whether the full report can be reused.
"""
from __future__ import annotations

import argparse
import gc
import json
from pathlib import Path
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from domains.engine_provenance import engine_preamble, provenance_line  # noqa: E402

engine_preamble()

from substrate.boot_core import boot_core  # noqa: E402
from substrate_rs import _native  # noqa: E402


AUDIT = _native.Substrate
SIGNATURE = [["cell", i // 4, i % 4, f"v{i % 4}"] for i in range(8)]


def run_once(codebook_size: int, cache_busted: bool) -> dict:
    substrate, agent = boot_core()
    native = substrate._inner
    native.add_production({
        "src": {"type": "Agent", "var": "agent"},
        "edge_type": "has_sd_profile_probe",
        "tgt": {"type": "SdProfileProbe", "var": "probe"},
        "provenance": "profile:sd_report_cache",
    })
    for index in range(codebook_size):
        signature = SIGNATURE if index == 0 else [
            ["other", index, relation] for relation in range(len(SIGNATURE))
        ]
        substrate.add_node("ShapeSignature", {
            "name": f"held_{index}", "kind": "faculty", "faculty": f"held_{index}",
            "signature": json.dumps(signature),
        })
    probe = substrate.add_node(
        "SdProfileProbe", {"signature": SIGNATURE, "status": "pending"})
    substrate.add_edge(agent, "has_sd_profile_probe", probe)

    effects = []
    for index, field in enumerate((None, "residual", "covered_count")):
        term = {
            "type": "ShapeDecode",
            "goal": {"type": "Attr", "node": {"type": "Var", "name": "probe"},
                     "key": "signature"},
            "beam": 3 + index if cache_busted else 3,
            "max_steps": 8,
            "cand_k": 3,
        }
        if field is not None:
            term["field"] = field
        effects.append(["set_attr", "probe", f"projection_{index}", {"__term__": term}])
    effects.append(["set_attr", "probe", "status", "done"])
    native.add_rule({
        "name": "profile_sd_report_cache",
        "match_type": "SdProfileProbe",
        "match": [["agent", "has_sd_profile_probe", "probe"]],
        "where": {"type": "Eq",
                  "a": {"type": "Attr", "node": {"type": "Var", "name": "probe"},
                        "key": "status"},
                  "b": {"type": "Lit", "value": "pending"}},
        "effects": effects,
    })

    gc.collect()
    AUDIT.scale_audit_reset()
    AUDIT.scale_audit_set_enabled(True)
    started = time.perf_counter_ns()
    try:
        native.run_rules()
    finally:
        elapsed_ns = time.perf_counter_ns() - started
        AUDIT.scale_audit_set_enabled(False)
    counters = dict(AUDIT.scale_audit_snapshot())
    return {
        "wall_ns": elapsed_ns,
        "shape_decode_invocations": counters.get("term_eval:ShapeDecode", 0),
        "shape_decode_units": counters.get("term_unit:ShapeDecode", 0),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--codebook-sizes", type=int, nargs="+", default=[1, 16, 64])
    parser.add_argument("--repetitions", type=int, default=21)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    rows = []
    for size in args.codebook_sizes:
        arms = {}
        for name, busted in (("cached", False), ("cache_busted_control", True)):
            samples = [run_once(size, busted) for _ in range(args.repetitions)]
            arms[name] = {
                "median_wall_ns": int(statistics.median(s["wall_ns"] for s in samples)),
                "shape_decode_invocations": samples[0]["shape_decode_invocations"],
                "shape_decode_units": samples[0]["shape_decode_units"],
            }
        arms["speedup"] = (
            arms["cache_busted_control"]["median_wall_ns"]
            / arms["cached"]["median_wall_ns"]
        )
        rows.append({"codebook_size": size, **arms})
        print(size, json.dumps(arms, sort_keys=True))

    result = {"engine": provenance_line(), "repetitions": args.repetitions, "rows": rows}
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
