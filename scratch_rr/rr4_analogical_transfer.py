#!/usr/bin/env python3
"""RR4 — ANALOGICAL TRANSFER over real rules: b = T(a), x = T(c).

The parallelogram, on three REAL seed rules that already exist in this tree:

  a = pd_decide         (seeds/bigville_action_decide.json)
        match  (town -has_actor-> maker)
        where  Attr(maker, "decide_armed") == 1.0
  b = po_observe        (seeds/bigville_action_decide.json)
        match  (town -has_actor-> maker)
        where  Attr(maker, "observe_armed") == 1.0
  c = af_choose_action  (seeds/bigville_affect_decide.json)
        match  (m -is_at-> cur)
        where  Attr(m, "decide_armed") == 1.0

Two INDEPENDENT dimensions, discovered mechanically (rr4_find_parallelogram.py),
not chosen by hand:

  P = a->b  : WHAT IS ARMED          {where.a.items.0.key}
  Q = a->c  : WHICH BINDING IT IS READ ON
                                     {match.0.0, match.0.1, match.0.2,
                                      where.a.items.0.node.name}

P and Q are disjoint, so the fourth corner is defined and — verified against
the whole corpus — MISSING:

  x = T(c)  : match (m -is_at-> cur), where Attr(m, "observe_armed") == 1.0

Every shape-math step is a real engine call: `AntiUnifyWitness` computes the
MEET and the witnesses, `Substitute` computes the JOIN. Python does only set
arithmetic over the returned witness PATHS (which paths belong to T) and the
mechanical I/O of installing the result. The final step is not a syntax
check: x is installed as a real rule and run, and its firing is compared
against b's and c's on a graph built to discriminate all three.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "runners", "dsl", "python"))

import substrate_rs as srs  # noqa: E402

WILD = "·?·"
WILDV = (WILD,)
_N = srs.Substrate()._inner


def ev(t):
    return _N.evaluate(t, {})


def lit(v):
    return {"type": "Lit", "value": v}


def sigma_lit(pairs):
    """A sigma is a Dict whose KEYS are position-PATH tuples. Plain JSON
    cannot carry that; `persist.rs`'s `{"__dict__": [[k, v], ...]}` tagged
    form can, and `Lit` decodes it."""
    return {"type": "Lit", "value": {"__dict__": [[list(k), v] for k, v in pairs.items()]}}


def find_rules(names):
    out = {}
    sd = os.path.join(HERE, "seeds")
    for fn in sorted(os.listdir(sd)):
        if not fn.endswith(".json"):
            continue
        try:
            blob = json.load(open(os.path.join(sd, fn)))
        except Exception:
            continue
        if not isinstance(blob, dict):
            continue
        for r in blob.get("rules", []) or []:
            if isinstance(r, dict) and r.get("name") in names and r["name"] not in out:
                out[r["name"]] = (fn, r)
    return out


def py(v):
    """Engine Value -> plain JSON-able Python (lists, not tuples)."""
    if isinstance(v, tuple):
        return [py(x) for x in v]
    if isinstance(v, list):
        return [py(x) for x in v]
    if isinstance(v, dict):
        return {k: py(x) for k, x in v.items()}
    return v


def main():
    names = ["pd_decide", "po_observe", "af_choose_action"]
    found = find_rules(set(names))
    for n in names:
        if n not in found:
            print(f"!! {n} not found in seeds/ — aborting")
            return 1
    A_r, B_r, C_r = (found[n][1] for n in names)
    A = {"match": A_r["match"], "where": A_r["where"]}
    B = {"match": B_r["match"], "where": B_r["where"]}
    C = {"match": C_r["match"], "where": C_r["where"]}

    print("=" * 78)
    print("RR4 — analogical transfer on real corpus rules")
    print("=" * 78)
    for n in names:
        fn, r = found[n]
        print(f"  {n:<18} seeds/{fn}")

    # ---- 1. the MEET, with witnesses: one engine call -----------------
    auw = {"type": "AntiUnifyWitness", "values": lit((A, B, C)), "wild": WILD}
    template, sigmas = ev(auw)
    sA, sB, sC = (dict(s) for s in sigmas)
    print(f"\n1. AntiUnifyWitness([a,b,c]) -> template + 3 witnesses")
    print(f"   WILD paths in the template (= where the three differ): {len(sA)}")
    for p in sorted(sA, key=repr):
        print(f"     {'.'.join(map(str,p)):<28} a={sA[p]!r:<18} b={sB[p]!r:<18} c={sC[p]!r}")

    # ---- 2. losslessness on ALL THREE, before trusting anything ------
    print("\n2. round trip Substitute(template, sigma_i) == i, for each real rule")
    ok = True
    for nm, sg, orig in (("a", sA, A), ("b", sB, B), ("c", sC, C)):
        got = py(ev({"type": "Substitute", "template": lit(template),
                     "sigma": sigma_lit(sg), "wild": WILD}))
        same = got == orig
        ok &= same
        print(f"     {nm}: {same}")
    if not ok:
        print("   !! the algebra is lossy on this family — transfer NOT attempted")
        return 1

    # ---- 3. T = the a->b difference ----------------------------------
    P = {p for p in sA if sA[p] != sB[p]}
    Q = {p for p in sA if sA[p] != sC[p]}
    print(f"\n3. T := the a->b difference")
    print(f"     P (a->b) = {sorted('.'.join(map(str,p)) for p in P)}")
    print(f"     Q (a->c) = {sorted('.'.join(map(str,p)) for p in Q)}")
    print(f"     disjoint : {not (P & Q)}  <- required for the parallelogram to be defined")
    T = {p: sB[p] for p in P}

    # ---- 4. x := T(c) -------------------------------------------------
    sX = dict(sC)
    sX.update(T)
    X = py(ev({"type": "Substitute", "template": lit(template),
               "sigma": sigma_lit(sX), "wild": WILD}))
    print(f"\n4. x := Substitute(template, sigma_c (+) T)")
    print(f"     x.match = {json.dumps(X['match'])}")
    print(f"     x.where = {json.dumps(X['where'])}")
    print(f"     x != a : {X != A}   x != b : {X != B}   x != c : {X != C}")
    corpus = {json.dumps(r[1].get("match"), sort_keys=True) + "|" +
              json.dumps(r[1].get("where"), sort_keys=True)
              for r in _all_rules()}
    xkey = json.dumps(X["match"], sort_keys=True) + "|" + json.dumps(X["where"], sort_keys=True)
    print(f"     x is ABSENT from the whole seed corpus ({len(corpus)} distinct "
          f"match|where recognisers): {xkey not in corpus}")

    # ---- 5. does it actually WORK? install and fire -------------------
    #
    # The full 2x2 grid the parallelogram claims exists:
    #
    #                        decide_armed        observe_armed
    #   has_actor binding    a = pd_decide       b = po_observe
    #   is_at     binding    c = af_choose       x = THE MISSING CORNER
    #
    # Each cell should fire EXACTLY ONE of the four rules. Note the two rows
    # bind opposite ENDPOINTS -- a/b read the match triple's TARGET var,
    # c/x read its SOURCE var -- which is itself part of dimension Q, so
    # each cell places the armed attr on the endpoint its own row reads.
    print("\n5. install x as a real rule and run the full 2x2 grid")

    def recogniser(nm, obj, flag, endpoint):
        return {"name": nm, "match": obj["match"], "where": obj["where"],
                "effects": [["set_attr", obj["match"][0][endpoint], flag, 1.0]]}

    RULES = [
        ("a", recogniser("a_pd_decide", A, "fired_a", 2)),
        ("b", recogniser("b_po_observe", B, "fired_b", 2)),
        ("c", recogniser("c_af_choose_action", C, "fired_c", 0)),
        ("x", recogniser("x_TRANSFERRED", X, "fired_x", 0)),
    ]

    GRID = [
        ("has_actor", "decide_armed",  "tgt", "a"),
        ("has_actor", "observe_armed", "tgt", "b"),
        ("is_at",     "decide_armed",  "src", "c"),
        ("is_at",     "observe_armed", "src", "x"),   # <- the missing corner
    ]

    all_ok = True
    for et, armed, endpoint, expect in GRID:
        s = srs.Substrate()
        s.add_production({"src": {"type": "Actor", "var": "s"}, "edge_type": et,
                          "tgt": {"type": "Place", "var": "t"}})
        n_src = s.add_node("Actor", {armed: 1.0} if endpoint == "src" else {})
        n_tgt = s.add_node("Place", {armed: 1.0} if endpoint == "tgt" else {})
        s.add_edge(n_src, et, n_tgt)
        for _, r in RULES:
            s._inner.add_rule(r)
        s._inner.run_rules()
        attrs = dict(s.node(n_src)["attrs"])
        attrs.update(s.node(n_tgt)["attrs"])
        fired = [k for k, _ in RULES if attrs.get("fired_" + k)]
        good = fired == [expect]
        all_ok &= good
        star = "  <-- THE MISSING CORNER" if expect == "x" else ""
        print(f"     {'OK ' if good else 'BAD'}  {et:<10} x {armed:<14} -> fired={fired or ['(none)']}"
              f"  expected=['{expect}']{star}")

    print(f"\n   ==> every cell fires exactly the rule the analogy predicts: {all_ok}")
    print(f"   ==> x is a REAL rule, absent from the corpus, derived only by "
          f"AntiUnifyWitness + Substitute over three held rules")
    return 0 if all_ok else 1


def _all_rules():
    sd = os.path.join(HERE, "seeds")
    for fn in sorted(os.listdir(sd)):
        if not fn.endswith(".json"):
            continue
        try:
            blob = json.load(open(os.path.join(sd, fn)))
        except Exception:
            continue
        if not isinstance(blob, dict):
            continue
        for r in blob.get("rules", []) or []:
            if isinstance(r, dict) and r.get("match") is not None:
                yield (fn, r)


if __name__ == "__main__":
    sys.exit(main())
