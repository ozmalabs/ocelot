#!/usr/bin/env python3
"""RR4, widened — is the transfer a property of one hand-checked triple, or
of the corpus?

Runs the full algebraic transfer over every parallelogram
`rr4_find_parallelogram.py` discovered, and reports, per triple:

  L  losslessness   Substitute(template, sigma_i) == i for ALL THREE of a,b,c
  D  disjointness   P (a->b paths) and Q (a->c paths) share no path
  N  novelty        x is absent from the whole seed corpus

Only the deep firing test (rr4_analogical_transfer.py step 5) is not run
here — each cell needs a bespoke discriminating graph. This measures the
algebra; that measures the behaviour, once, deeply.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "runners", "dsl", "python"))

import substrate_rs as srs  # noqa: E402

WILD = "·?·"
_N = srs.Substrate()._inner


def ev(t):
    return _N.evaluate(t, {})


def lit(v):
    return {"type": "Lit", "value": v}


def sigma_lit(pairs):
    return {"type": "Lit", "value": {"__dict__": [[list(k), v] for k, v in pairs.items()]}}


def py(v):
    if isinstance(v, (tuple, list)):
        return [py(x) for x in v]
    if isinstance(v, dict):
        return {k: py(x) for k, x in v.items()}
    return v


def all_rules():
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
            if isinstance(r, dict) and r.get("name"):
                yield fn, r


def main():
    tri = json.load(open(os.path.join(HERE, "scratch_rr", "rr4_parallelograms.json")))
    by_name = {}
    corpus = set()
    for fn, r in all_rules():
        if isinstance(r.get("where"), dict) and isinstance(r.get("match"), list):
            by_name.setdefault(r["name"], {"match": r["match"], "where": r["where"]})
            corpus.add(json.dumps(r["match"], sort_keys=True) + "|" +
                       json.dumps(r["where"], sort_keys=True))

    L = D = Nn = both = 0
    total = 0
    for t in tri:
        a, b, c = t["a"], t["b"], t["c"]
        if not all(n in by_name for n in (a, b, c)):
            continue
        A, B, C = by_name[a], by_name[b], by_name[c]
        total += 1
        template, sigmas = ev({"type": "AntiUnifyWitness",
                               "values": lit((A, B, C)), "wild": WILD})
        sA, sB, sC = (dict(s) for s in sigmas)
        lossless = all(
            py(ev({"type": "Substitute", "template": lit(template),
                   "sigma": sigma_lit(sg), "wild": WILD})) == orig
            for sg, orig in ((sA, A), (sB, B), (sC, C)))
        P = {p for p in sA if sA[p] != sB.get(p)}
        Q = {p for p in sA if sA[p] != sC.get(p)}
        disjoint = bool(P) and bool(Q) and not (P & Q)
        L += lossless
        D += disjoint
        if not (lossless and disjoint):
            continue
        sX = dict(sC)
        sX.update({p: sB[p] for p in P})
        X = py(ev({"type": "Substitute", "template": lit(template),
                   "sigma": sigma_lit(sX), "wild": WILD}))
        novel = (json.dumps(X["match"], sort_keys=True) + "|" +
                 json.dumps(X["where"], sort_keys=True)) not in corpus
        Nn += novel
        both += novel

    print(f"parallelogram triples tested        : {total}")
    print(f"  L  algebra lossless on all 3 rules: {L}/{total}")
    print(f"  D  P and Q disjoint               : {D}/{total}")
    print(f"  N  x novel (absent from corpus)   : {Nn}/{total}")
    print(f"  ==> transfers that are lossless AND well-defined AND novel: {both}/{total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
