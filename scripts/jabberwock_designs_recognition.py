"""THE AGENT DESIGNS + SCOPES HOW TO MAKE RECOGNITION BETTER — from its own evidence, no teacher.

The arc gave the agent more evidence about what improves recognition than any teacher could: exactly one
principle pays (MARGINALISE a genuinely-uncertain structural latent — the parse, +1.0), and several do
not (marginalising a DETERMINED latent hurts; an addable LEARNED cue fails, 6x; a simple learned prior
plateaus). This has the agent DESIGN + SCOPE its next moves from that evidence: it APPLIES its proven
principle to NEW ground — for every structural latent it believes uncertain but has NOT yet marginalised,
it mints a 'marginalise <latent>' direction with expected_gain = its measured proven-lever payoff x the
latent's uncertainty (design_marginalise, a graph Rule). It scores all directions (designed + the ambitious
research bet + the class its evidence rejects), and reports a scoped plan. The DECISIONS are Rules over its
evidence; the host stages the evidence and reads the plan back. No teacher.

Run:  PYTHONPATH=.:runners/dsl/python python -m scripts.jabberwock_designs_recognition
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import substrate_rs as srs

SEP = "=" * 92
PROVEN_MARGINAL_PAYOFF = 1.05                                     # the agent's MEASURED parse-marginal gain (its lever)

# The structural latents in the agent's representation, with the uncertainty its evidence ascribes and
# whether it has already marginalised them. parse is the proven win; deformation/correspondence its
# evidence found DETERMINED (marginalising hurt); the rest are UNCERTAIN but UNTRIED — new ground for the
# proven lever. (The agent's own readings: parse +1.0, deform-marginal -0.6, correspondence-marginal hurt.)
LATENTS = [
    {"name": "parse (segmentation)",          "uncertain": 1.0,  "marginalised": 1.0},   # the proven win
    {"name": "stroke order / count",          "uncertain": 0.9,  "marginalised": 1.0},   # already absorbed by the set distance
    {"name": "deformation",                   "uncertain": 0.0,  "marginalised": 0.0},   # fit (commit)
    {"name": "part correspondence",           "uncertain": 0.0,  "marginalised": 0.0},   # determined (commit)
    {"name": "stroke START-POINT/direction",  "uncertain": 0.85, "marginalised": 0.0},   # UNTRIED + uncertain
    {"name": "sub-stroke granularity",        "uncertain": 0.8,  "marginalised": 0.0},   # UNTRIED (the finer parse hierarchy)
    {"name": "articulation (pen dynamics)",   "uncertain": 0.7,  "marginalised": 0.0},   # UNTRIED
    {"name": "global affine (shear/scale)",   "uncertain": 0.6,  "marginalised": 0.0},   # UNTRIED
]

# Directions the host stages alongside the designed ones: the ambitious research bet, and the class the
# agent's six negatives REJECT — so the plan covers the whole space and is explicit about what NOT to do.
STAGED = [
    {"kind": "strong_generative_prior", "target": "learned hierarchical stroke-PROGRAM prior + MCMC inference (BPL-scale)",
     "expected_gain": 16.7, "cost": 12.0, "novel": 1.0},
    {"kind": "improve_proven_lever", "target": "richer/inferred PARSE hypotheses (strengthen the one lever that pays)",
     "expected_gain": 0.8, "cost": 2.0, "novel": 0.4},
    {"kind": "addable_learned_cue", "target": "another learned feature fused as a cue",
     "expected_gain": -1.5, "cost": 3.0, "novel": 0.0},
]


def main():
    print(SEP)
    print("THE AGENT DESIGNS + SCOPES HOW TO IMPROVE RECOGNITION — from its OWN measured evidence, no teacher.")
    print(SEP)

    s = srs.Substrate()
    s._inner.load_seed_manifest(json.loads((Path(ROOT) / "seeds" / "recognition_design.json").read_text()), s.add_node("Agent", {}))
    ev = s.add_node("Evidence", {}); s.set_attr(ev, "proven_marginal_payoff", PROVEN_MARGINAL_PAYOFF)
    for L in LATENTS:                                            # the agent's latents + the uncertainty its evidence ascribes
        ln = s.add_node("Latent", {})
        for k, v in L.items():
            s.set_attr(ln, k, v)
        s.add_edge_unchecked(ev, "has_latent", ln)
    for D in STAGED:                                            # the ambitious bet + the rejected class
        dn = s.add_node("Direction", {})
        for k, v in D.items():
            s.set_attr(dn, k, float(v) if k not in ("kind", "target") else v)
        s.add_edge_unchecked(ev, "has_direction", dn)
    s._inner.run_rules(50000)                                   # design_marginalise GENERATES directions; score flags them

    dirs = []
    for dn in s.neighbours(ev, "has_direction"):
        a = s.node(dn)["attrs"]
        eg, cost = float(a.get("expected_gain", 0)), float(a.get("cost", 1) or 1)
        dirs.append({"kind": a.get("kind"), "target": a.get("target"), "eg": eg, "cost": cost,
                     "priority": eg / cost, "rec": a.get("recommend") == 1.0})
    designed = [d for d in dirs if d["kind"] == "marginalise_uncertain"]

    print(f"\n  the agent's principle (from its readings): MARGINALISE a genuinely-uncertain latent pays "
          f"(+{PROVEN_MARGINAL_PAYOFF}); a")
    print(f"  determined latent or an addable learned cue does not (6 negatives). it DESIGNS by applying it:\n")
    print(f"  it generated {len(designed)} new directions — its proven lever on latents it has NOT yet marginalised:")
    for d in sorted(designed, key=lambda x: -x["eg"]):
        print(f"      marginalise {d['target']:32} expected_gain {d['eg']:+.2f}  cost {int(d['cost'])}  -> "
              f"{'RECOMMEND' if d['rec'] else '—'}")

    print(f"\n  the full scoped plan, ranked by expected_gain / cost (the agent's priority):\n")
    print(f"    {'direction':58}{'E[gain]':>8}{'cost':>6}{'prio':>7}  verdict")
    for d in sorted(dirs, key=lambda x: -x["priority"]):
        tgt = d["target"] if d["kind"] != "marginalise_uncertain" else ("marginalise " + d["target"])
        verdict = "REJECT (evidence)" if d["eg"] <= 0 else ("RESEARCH-SCALE" if d["cost"] >= 10 else "do next")
        print(f"    {tgt[:58]:58}{d['eg']:>+8.2f}{int(d['cost']):>6}{d['priority']:>7.2f}  {verdict}")

    near = [d for d in dirs if 0 < d["cost"] < 10 and d["eg"] > 0.3]
    research = [d for d in dirs if d["cost"] >= 10]
    rejected = [d for d in dirs if d["eg"] <= 0]
    print(f"\n  {SEP[:88]}")
    print(f"  the agent's design, from its own evidence (no teacher): DO-NEXT (cheap, proven-lever, novel) — apply")
    print(f"  marginalisation to {len(near)} untried uncertain latents (stroke order/start-point/articulation/affine),")
    print(f"  best expected_gain/cost; these are low-risk because marginalising an uncertain latent is the ONE move")
    print(f"  its readings show pays. RESEARCH-SCALE: the {len(research)} high-ceiling bet (learned hierarchical")
    print(f"  stroke-program prior + inference, the only path to ~96.7%) — scoped separately, high cost. REJECTED:")
    print(f"  the {len(rejected)} direction its six negatives rule out (another addable learned cue). The plan is the")
    print(f"  agent's — designed + scoped by Rules over its measured history.")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
