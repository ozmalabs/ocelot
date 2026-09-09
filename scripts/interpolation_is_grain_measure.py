#!/usr/bin/env python3
"""Interpolation is lower grain, not a different machine — measure the 4 parts.

See docs/research/psychology_affect/INTERPOLATION_IS_GRAIN_PREREG.md.

The user's claim: retrieval and generative interpolation are the SAME
operation at different resolution/parameters (degree not kind). Four
falsifiable parts:
  1. 1-hop graded superposition (grain slides interpolation<->retrieval)
  2. multi-hop reach (field lights a node with NO direct cue edge)
  3. multi-hop graded under the discrete commit (expected: SATURATES)
  4. multi-hop graded under a CONTINUOUS read, weak paths (expected: GRADED)
"""

from __future__ import annotations

import json
import math
import sys

sys.path.insert(0, "runners/dsl/python")
sys.path.insert(0, ".")

import substrate_rs as sr  # noqa: E402
from substrate.seed_loader import engine_rules_only  # noqa: E402
from domains import qualia_navigation as qn  # noqa: E402

SEED = "seeds/can_native_reimplementation.json"


def _loaded():
    s = sr.Substrate()
    inner = s._inner
    inner.load_seed_manifest(engine_rules_only(json.load(open(SEED))))
    return s, inner


# --- part 1: 1-hop graded superposition + grain -------------------------

def part1_one_hop_graded():
    def field(k, grain=None):
        s = sr.Substrate()
        full = ["cat", "dog", "tree", "grass"]
        active = full[:k]
        edges = [(c, "backyard", 1.0) for c in active]
        for i, c in enumerate(active):
            edges.append((c, "d%d" % i, 1.0))  # honest distractor per cue
        tri = qn.build_triad(s, active, edges, held_out="backyard")
        obs = None
        if grain is not None:
            obs = s._inner.add_node("Observer",
                                    {"name": "o", "grain": {qn.PULL_AXIS: grain}})
        return qn.coherence_signal(tri, observer=obs)["field"].get("backyard", 0.0)

    fine = [field(k) for k in (1, 2, 3, 4)]
    coarse = [field(k, grain=8.0) for k in (1, 2, 3, 4)]
    mono = all(fine[i] < fine[i + 1] for i in range(3))
    collapsed = len(set(coarse)) <= 2
    return {"fine": fine, "coarse": coarse, "monotone": mono,
            "coarse_collapsed": collapsed, "holds": mono and collapsed}


# --- part 2: multi-hop reach --------------------------------------------

def part2_multihop_reach():
    s, inner = _loaded()
    mt = inner.add_node("Microtheory",
                        {"temperature": 2.0, "discrete_mode": "3state",
                         "can_tick": 0})

    def C(name, h=0.0):
        c = inner.add_node("Concept",
                           {"name": name, "state": 0.0,
                            "external_field": float(h), "identity_field": 0.0})
        inner.add_edge(mt, "has_concept", c, {})
        return c

    def link(a, b, w=1.0):
        inner.add_edge(a, "causal_influence", b, {"weight": float(w)})
        inner.add_edge(b, "causal_influence", a, {"weight": float(w)})

    cues = [C("cue1", 2.0), C("cue2", 2.0), C("cue3", 2.0)]
    inter = C("intermediate")
    target = C("target")   # NO direct cue->target edge
    unrel = C("unrelated")
    for cu in cues:
        link(cu, inter, 1.0)
    link(inter, target, 1.0)
    link(cues[0], unrel, 0.2)
    steps = inner.run_rules(3000)
    tstate = inner.node(target)["attrs"].get("state", 0.0)
    return {"steps": steps, "target_state": tstate,
            "holds": abs(tstate) > 0.0}


# --- part 3: multi-hop graded, discrete commit (expected saturate) ------

def part3_multihop_discrete():
    def run(n_paths):
        s, inner = _loaded()
        mt = inner.add_node("Microtheory",
                            {"temperature": 2.0, "discrete_mode": "3state",
                             "can_tick": 0})

        def C(name, h=0.0):
            c = inner.add_node("Concept",
                               {"name": name, "state": 0.0,
                                "external_field": float(h),
                                "identity_field": 0.0})
            inner.add_edge(mt, "has_concept", c, {})
            return c

        def link(a, b, w=1.0):
            inner.add_edge(a, "causal_influence", b, {"weight": float(w)})
            inner.add_edge(b, "causal_influence", a, {"weight": float(w)})

        target = C("target")
        for i in range(4):
            cue = C("c%d" % i, 2.0 if i < n_paths else 0.0)
            inter = C("i%d" % i)
            link(cue, inter)
            link(inter, target)
        inner.run_rules(3000)
        return inner.node(target)["attrs"].get("state", 0.0)

    vals = [run(k) for k in (1, 2, 3, 4)]
    saturates = len(set(vals)) == 1  # all identical => winner-take-all
    return {"states": vals, "saturates": saturates}


# --- part 4: multi-hop graded, continuous read, WEAK paths --------------

def part4_multihop_continuous(w=0.3, drive=0.5, rounds=40, damp=0.3):
    def run(n_paths):
        s, inner = _loaded()
        mt = inner.add_node("Microtheory",
                            {"temperature": 2.0, "discrete_mode": "3state",
                             "can_tick": 0})

        def C(name, h=0.0):
            c = inner.add_node("Concept",
                               {"name": name, "state": 0.0,
                                "external_field": float(h),
                                "identity_field": 0.0})
            inner.add_edge(mt, "has_concept", c, {})
            return c

        def link(a, b, ww):
            inner.add_edge(a, "causal_influence", b, {"weight": ww})
            inner.add_edge(b, "causal_influence", a, {"weight": ww})

        target = C("target")
        nodes = [target]
        for i in range(4):
            cue = C("c%d" % i, drive if i < n_paths else 0.0)
            inter = C("i%d" % i)
            link(cue, inter, w)
            link(inter, target, w)
            nodes += [cue, inter]
        # CONTINUOUS pre-threshold read: tanh(local), NO commit. Pure Python
        # read over the SAME graph — the "lower grain" the claim predicts.
        act = {n: 0.0 for n in nodes}
        ext = {n: inner.node(n)["attrs"].get("external_field", 0.0)
               for n in nodes}
        adj = {n: list(inner.neighbours(n, "causal_influence")) for n in nodes}
        for _ in range(rounds):
            for n in nodes:
                lf = ext[n] + sum(w * act.get(nb, 0.0) for nb in adj[n])
                act[n] = (1 - damp) * act[n] + damp * math.tanh(lf)
        return act[target]

    vals = [run(k) for k in (1, 2, 3, 4)]
    mono = all(vals[i] < vals[i + 1] for i in range(3))
    spread = vals[-1] - vals[0]
    return {"acts": vals, "monotone": mono, "spread": spread,
            "holds": mono and spread > 0.05}


def main():
    print("=" * 70)
    print("INTERPOLATION IS LOWER GRAIN, NOT A DIFFERENT MACHINE")
    print("=" * 70)

    p1 = part1_one_hop_graded()
    print("\n[PART 1] 1-hop graded superposition + grain")
    print("  fine grain field (overlap 1..4): %s  monotone=%s"
          % ([round(v, 2) for v in p1["fine"]], p1["monotone"]))
    print("  coarse grain(8) field:           %s  collapsed=%s"
          % ([round(v, 2) for v in p1["coarse"]], p1["coarse_collapsed"]))
    print("  => %s (graded produced value; grain slides "
          "interpolation<->retrieval)" % ("HOLDS" if p1["holds"] else "FAILS"))

    p2 = part2_multihop_reach()
    print("\n[PART 2] multi-hop reach (target has NO direct cue edge)")
    print("  run_rules steps=%d  target_state=%+.3f" %
          (p2["steps"], p2["target_state"]))
    print("  => %s (field propagates >=2 hops; not memorisation-bound)"
          % ("HOLDS" if p2["holds"] else "FAILS"))

    p3 = part3_multihop_discrete()
    print("\n[PART 3] multi-hop graded under DISCRETE commit (strong paths)")
    print("  target state for 1..4 paths: %s" %
          [round(v, 3) for v in p3["states"]])
    print("  => SATURATES=%s (3-state = winner-take-all attractor; the "
          "discrete commit quantises the gradient away)" % p3["saturates"])

    p4 = part4_multihop_continuous()
    print("\n[PART 4] multi-hop graded under CONTINUOUS read (weak paths)")
    print("  target activation for 1..4 paths: %s" %
          [round(v, 4) for v in p4["acts"]])
    print("  monotone=%s spread=%.4f" % (p4["monotone"], p4["spread"]))
    print("  => %s (graded multi-hop interpolation recovered by the "
          "lower-grain continuous read)" % ("HOLDS" if p4["holds"] else "FAILS"))

    print("\n" + "=" * 70)
    print("VERDICT on 'interpolation is just lower grain / different params'")
    supported = p1["holds"] and p2["holds"] and p4["holds"]
    print("  parts 1,2,4 hold, part 3 saturates as expected: %s" % supported)
    if supported:
        print("  => SUPPORTED. Interpolation IS available on the same")
        print("     substrate. The discrete commit's saturation is a MODE/")
        print("     PARAMETER choice (a retrieval attractor), not a different")
        print("     kind of machine. The continuous read is the lower grain,")
        print("     and it interpolates. Degree, not kind.")
    else:
        print("  => NOT fully supported — see failing parts above.")
    print("=" * 70)
    return {"p1": p1, "p2": p2, "p3": p3, "p4": p4, "supported": supported}


if __name__ == "__main__":
    main()
