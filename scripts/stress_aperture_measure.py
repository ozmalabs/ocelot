"""STRESS COMPRESSES APERTURE — confirmatory measure (block 366000).

Prereg: docs/research/engine_substrate/STRESS_COMPRESSES_APERTURE_PREREG.md,
committed before this file ran.

Measures the MANIFOLD half only. The learning half is a named, unbuilt prediction
in prereg §2 and is not touched here.

Python is a world adapter: it writes affect/policy attrs, ticks, and reads the
native audit back. Every field measured is computed in Rust by
`future_manifold::projection_field` / `feasible_selection`.
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))
from substrate.world_adapter import WorldAdapter  # noqa: E402

OUTDIR = os.path.join(ROOT, "results", "stress_aperture")

# Two dimensions. The escape lives in dimension 1 -- the one stress removes.
TARGET = [[0.0, 0.0], [0.0, 0.0], [0.0, 0.0]]
BOUNDS = [[1.0, 1.0], [1.0, 1.0], [1.0, 1.0]]
HELD = [[0.0, 0.0], [0.2, 0.1], [0.1, 0.0]]        # inside the tube throughout
ESCAPING = [[0.0, 0.0], [0.2, 0.1], [0.1, 9.0]]    # leaves it, in dimension 1
FULL = [[1.0, 1.0]]
STRESSED = [[1.0, 0.0]]                            # dimension 1 no longer resolvable


def _bench(dysregulated, evidence_strength=8.0):
    a = WorldAdapter(seeds=())
    a.inner.load_seed_manifest(
        json.load(open(os.path.join(ROOT, "seeds", "stress_aperture.json"))), a.agent)
    g = a.s
    ep = g.add_node("Episode", {"future_manifold_target": TARGET,
                                "future_manifold_bounds": BOUNDS})
    pol = g.add_node("ManifoldPolicy", {
        # evidence strength = how much of the horizon the agent can afford to audit
        "future_manifold_projection_budget": float(evidence_strength),
        "future_manifold_physical_horizon": 3.0})
    aff = g.add_node("AffectiveState", {
        "dysregulated": 1.0 if dysregulated else 0.0,
        "stress_resolves": STRESSED, "regulated_resolves": FULL})
    g.add_edge(aff, "gates_projection", pol)
    held = g.add_node("Candidate", {"future_manifold_values": HELD, "intervention": 1.0})
    esc = g.add_node("Candidate", {"future_manifold_values": ESCAPING, "intervention": 1.0})
    a.inner.run_rules(1_000_000)
    return a, ep, pol, [held, esc]


def _term(field):
    """The shipped `FutureManifoldProjection` Term — the same path the native
    manifold tests use, so nothing here is a second implementation."""
    return {"type": "FutureManifoldProjection",
            "episode": {"type": "Var", "name": "ep"},
            "policy": {"type": "Var", "name": "po"},
            "source": {"type": "Var", "name": "src"},
            "field": field}


def _read(a, ep, pol, cand):
    env = {"ep": ep, "po": pol, "src": cand}
    return {f: a.inner.evaluate(_term(f), env)
            for f in ("support", "resolved", "loss", "information_loss",
                      "retained_width")}


def _selection(a, ep, pol, cands):
    return a.inner.feasible_selection(ep, pol, cands)


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    out = {"prereg": "STRESS_COMPRESSES_APERTURE_PREREG.md", "block": 366000, "cells": {}}

    for label, dys in (("regulated", False), ("dysregulated", True)):
        a, ep, pol, cands = _bench(dys)
        out["cells"][label] = {
            "compressed": a.s.node(pol)["attrs"].get("sa_compressed"),
            "escaping": _read(a, ep, pol, cands[1]),
            "held": _read(a, ep, pol, cands[0]),
            "selection": _selection(a, ep, pol, cands),
        }

    # G-evidence-is-inert: sweep the evidence strength on the stressed arm
    out["evidence_sweep"] = []
    for strength in (1.0, 3.0, 8.0, 32.0, 128.0):
        a, ep, pol, cands = _bench(True, evidence_strength=strength)
        out["evidence_sweep"].append(
            {"strength": strength, "escaping": _read(a, ep, pol, cands[1])})

    with open(os.path.join(OUTDIR, "results.json"), "w") as f:
        json.dump(out, f, indent=1)

    print("=== STRESS COMPRESSES APERTURE (real engine) ===\n")
    for label, c in out["cells"].items():
        e = c["escaping"]
        print(f"  {label:13s} compressed={c['compressed']}  "
              f"loss={e['loss']}  information_loss={e['information_loss']}  "
              f"resolved={e['resolved']}  retained_width={e['retained_width']}")
        s = c["selection"]
        if s is not None:
            print(f"  {'':13s} selection: unestablished={len(s['unestablished'])} "
                  f"feasible={len(s['feasible'])} selected={len(s['selected'])} "
                  f"withheld_minimal={len(s['withheld_minimal'])}")
        else:
            print(f"  {'':13s} selection: FAILED CLOSED (None)")
    print("\n  evidence sweep on the stressed arm:")
    for row in out["evidence_sweep"]:
        e = row["escaping"]
        print(f"    strength={row['strength']:6.1f} -> loss={e['loss']} "
              f"information_loss={e['information_loss']} resolved={e['resolved']}")
    print(f"\n  wrote {os.path.join(OUTDIR, 'results.json')}")


if __name__ == "__main__":
    main()
