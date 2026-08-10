#!/usr/bin/env python3
"""CROSS-FRAME IDENTITY — POST-HOC DIAGNOSTICS.

*** NOT a pre-registered result. Nothing in `VISION_CROSSFRAME_IDENTITY_RESULTS.md`
    §2 (the arms) depends on this file; it exists to characterise two defects the
    confirmatory run surfaced, so the next rung can be pre-registered against
    them rather than rediscovering them. ***

D1 — THE CODEBOOK WAS 33-WAY, NOT 16-WAY. `boot_core` + `shape_decode_loop`
     install 17 `ShapeSignature` nodes of their own, and the seed's Argmax
     ranges over `NodesOfType(ShapeSignature)`. Measures how many, and whether
     they are structurally capable of covering a `["cell", ...]` relation at all.

D2 — ONE BASE FRAME'S ANSWERS WERE NON-REPRODUCIBLE. In the confirmatory run,
     every one of base frame 18's 272 probes (C1, k=4) returned the held
     signature `fractal` while reporting `xf_ntied == 1` and a true-region score
     equal to `xf_max` -- i.e. Argmax disagreed with an Eq-filter over the SAME
     ShapeDecode Term inside one rule application. Replays it under identical
     seeds and identical process history.

USAGE:
    PYTHONPATH=runners/dsl/python:. python scripts/crossframe_identity_diagnose.py
"""
from __future__ import annotations

import json
import os
import sys
import importlib.util as _iu

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from domains.engine_provenance import engine_preamble, provenance_line  # noqa: E402
engine_preamble()

import domains.seed_registry                    # noqa: F401,E402
import domains.crossframe_world as cw           # noqa: E402

_spec = _iu.spec_from_file_location(
    "crossframe_identity_measure",
    os.path.join(ROOT, "scripts", "crossframe_identity_measure.py"))
m = _iu.module_from_spec(_spec)
_spec.loader.exec_module(m)

ANOMALOUS_BASE = 18
REPLAY_UPTO = 20


def is_mine(name):
    return isinstance(name, str) and name.startswith("r") and name[1:].isdigit()


def main():
    out = {"provenance": provenance_line(),
           "kind": "POST-HOC DIAGNOSTIC — NOT a pre-registered result"}

    # --- D1 ---------------------------------------------------------------- #
    w = cw.CrossFrameWorld()
    pre = []
    for n in w.s.nodes("ShapeSignature"):
        a = w.s.node(n)["attrs"]
        sig = a.get("signature")
        try:
            rels = json.loads(sig) if isinstance(sig, str) else (sig or [])
        except Exception:                                   # noqa: BLE001
            rels = []
        preds = sorted({r[0] for r in rels if isinstance(r, list) and r})
        pre.append({"name": a.get("name"), "kind": a.get("kind"),
                    "n_relations": len(rels), "predicates": preds,
                    # ShapeDecode's covers_relation demands an identical
                    # predicate at slot 0, so a part with no "cell" predicate
                    # can never cover any relation this rung presents.
                    "can_cover_a_cell_relation": "cell" in preds})
    out["D1_preexisting_codebook"] = {
        "n_preexisting_shape_signatures": len(pre),
        "n_that_can_cover_a_cell_relation":
            sum(1 for p in pre if p["can_cover_a_cell_relation"]),
        "codebook_size_presented_to_argmax": len(pre) + 16,
        "chance_if_uniform_over_the_whole_codebook": 1.0 / (len(pre) + 16),
        "chance_pre_registered": 1.0 / 16,
        "entries": pre,
    }
    print(f"[D1] {len(pre)} pre-existing ShapeSignature nodes; "
          f"{sum(1 for p in pre if p['can_cover_a_cell_relation'])} can cover a "
          f"cell relation; codebook presented to Argmax = {len(pre) + 16}",
          flush=True)

    # --- D2 ---------------------------------------------------------------- #
    frames, meta = m.load_corpus("C1")
    replay = []
    for t in range(REPLAY_UPTO):
        rows, _ = m.run_base_frame(frames, t, m.K_HEADLINE,
                                   want_deltas=m.DELTAS, want_gates=True,
                                   seed=m.SEED_BLOCK + t)
        foreign = sum(1 for r in rows if not is_mine(r["said"]))
        replay.append({"base": t, "n_probes": len(rows), "foreign_wins": foreign})
        print(f"[D2] base {t}: foreign wins {foreign}/{len(rows)}", flush=True)
    out["D2_replay"] = {
        "corpus": "C1", "seeds_identical_to_confirmatory": True,
        "process_history_identical": True,
        "bases_replayed": REPLAY_UPTO,
        "confirmatory_foreign_wins_at_base_18": 272,
        "replay_foreign_wins_at_base_18":
            next(r["foreign_wins"] for r in replay if r["base"] == ANOMALOUS_BASE),
        "replay_foreign_wins_total": sum(r["foreign_wins"] for r in replay),
        "per_base": replay,
    }

    p = os.path.join(ROOT, "results", "crossframe_identity_diagnose.json")
    with open(p, "w") as fh:
        json.dump(out, fh, indent=1)
    print(f"[done] wrote {p}", flush=True)


if __name__ == "__main__":
    main()
