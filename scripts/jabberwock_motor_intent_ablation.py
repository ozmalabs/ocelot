#!/usr/bin/env python3
"""jabberwock_motor_intent_ablation — lift-noise ablation for the generic motor-intent layer.

Boots the FULL Jabberwock seed closure (`WorldAdapter` + `load_all_seeds`), then runs
the headline falsifier: same stroke shapes, wild inter-stroke lift → intent verdict
stable, arrangement verdict degrades. Results go to results/motor_intent_ablation.json.

Mechanical host I/O only (CLAUDE.md): runs held-Term verdicts, writes JSON. No decisions.

Run:
  OZMA_SEED_PERSIST_DISABLED=1 OZMA_NO_LLM=1 PYTHONPATH=.:runners/dsl/python \\
    python3 scripts/jabberwock_motor_intent_ablation.py
"""
from __future__ import annotations

import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
os.environ.setdefault("OZMA_NO_LLM", "1")

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds

from domains import motor_intent as mi


def _l0():
    return [[0.0, 0.0], [0.0, 1.0], [0.0, 2.0]]


def _l1():
    return [[0.0, 2.0], [1.0, 2.0], [2.0, 2.0]]


def _lifted1():
    return [[10.0, 8.0], [11.0, 8.0], [12.0, 8.0]]


def _diag1():
    return [[0.0, 2.0], [1.0, 3.0], [2.0, 4.0]]


def _installed_seed_ids(adapter) -> set[str]:
    """Full-boot provenance is SeedSummary nodes, not Seed{id} (boot_core)."""
    out = set()
    for n in adapter.s.nodes("SeedSummary"):
        sid = adapter.s.node(n)["attrs"].get("seed_id")
        if sid:
            out.add(sid)
    return out


def main() -> int:
    if not mi.stroke_quantize_live():
        print("SKIP: StrokeQuantize not built — run maturin develop in runners/dsl")
        return 0

    t0 = time.time()
    print("Booting full Jabberwock (load_all_seeds)…", flush=True)
    adapter = WorldAdapter(seeds=())
    rep = load_all_seeds(adapter)
    boot_s = time.time() - t0
    native = adapter.s._inner

    seed_ids = _installed_seed_ids(adapter)
    has_motor_intent = "motor_intent_core" in seed_ids
    has_standing = "standing_motor_intent_concern" in seed_ids

    print(f"  loaded {rep.get('loaded', '?')}/{rep.get('total', '?')} seeds in {boot_s:.1f}s")
    print(f"  motor_intent_core={'yes' if has_motor_intent else 'NO'}  "
          f"standing_motor_intent_concern={'yes' if has_standing else 'no'}")
    if rep.get("failed"):
        print(f"  seed failures: {len(rep['failed'])}")

    query = [_l0(), _lifted1()]
    extracted = mi.extract_motor_plan(native, query)
    cand_l = mi.extract_plan_segments(native, [_l0(), _l1()])
    cand_diag = mi.extract_plan_segments(native, [_l0(), _diag1()])

    intent = mi.motor_intent_verdict(
        native, query, [cand_l, cand_diag], mode="intent",
        query_plan_segs=extracted["plan_segments"])
    arrangement = mi.motor_intent_verdict(native, query, [cand_l, cand_diag], mode="arrangement")

    tid = mi.annotate_execution_trace(adapter, query, goal_kind="replicate_template")
    noise = mi.held_motor_noise(adapter)
    intent_wins = intent.get("winner") == 0
    intent_score = intent["scores"][0][0] if intent.get("scores") else float("inf")
    arr_score = arrangement["scores"][0][0] if arrangement.get("scores") else float("inf")
    ablation_pass = intent_wins and arr_score > intent_score * 5.0
    if ablation_pass:
        mi.record_outcome_match_failure(adapter, tid)

    concerns = [adapter.s.node(n)["attrs"] for n in adapter.s.nodes("SelfConcern")]

    out = {
        "boot_seconds": round(boot_s, 2),
        "seeds_loaded": rep.get("loaded"),
        "seeds_total": rep.get("total"),
        "motor_intent_core_installed": has_motor_intent,
        "standing_motor_intent_concern_installed": has_standing,
        "intent_verdict": intent,
        "arrangement_verdict": arrangement,
        "intent_correct": intent_wins,
        "intent_score": intent_score,
        "arrangement_score": arr_score,
        "lift_noise_ablation_pass": ablation_pass,
        "noise_realized": True,
        "motor_noise": noise,
        "extracted_plan_segments": extracted["plan_segments"],
        "trace_id": tid,
        "motor_intents": mi.held_motor_intents(adapter),
        "self_concerns": [{"content": c.get("content"), "kind": c.get("kind"),
                           "source": c.get("source")} for c in concerns],
        "node_count": len(list(adapter.s.nodes())),
    }
    os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
    path = os.path.join(ROOT, "results", "motor_intent_ablation.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(json.dumps(out, indent=2))
    print(f"wrote {path}")
    return 0 if out["lift_noise_ablation_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
