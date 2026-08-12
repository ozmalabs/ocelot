#!/usr/bin/env python3
"""RR1, widened — is the `AntiUnifyWitness`-alone equivalence a property of
one hand-picked pair, or of the corpus?

For every ordered pair (entry, obs) drawn from a real seed-rule sample,
under ENCODING A (FrozenSet of concrete rows, slot = absent row), check the
three identities the single-pair probe found:

  I1  Covers(entry, obs)              <->  sigma[entry] is EMPTY
  I2  sigma[obs] (as a set of rows)   ==   obs \\ entry          (the residual)
  I3  Substitute(template, sigma_obs) ==   obs                   (lossless)

Read-only; writes nothing to any graph.
"""
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "runners", "dsl", "python"))

import substrate_rs as srs  # noqa: E402
from domains.rule_signature import rule_signature  # noqa: E402

WILD = "·?·"
N = srs.Substrate()._inner


def ev(t):
    return N.evaluate(t, {})


def lit(v):
    return {"type": "Lit", "value": v}


def idx(seq, i):
    return {"type": "IndexAt", "seq": seq, "index": lit(i)}


def auw_term(vals):
    return {"type": "AntiUnifyWitness", "values": lit(tuple(vals)), "wild": WILD}


def main():
    seed_dir = os.path.join(HERE, "seeds")
    pool = []
    for fn in sorted(os.listdir(seed_dir)):
        if not fn.endswith(".json"):
            continue
        try:
            with open(os.path.join(seed_dir, fn)) as fh:
                blob = json.load(fh)
        except Exception:
            continue
        if not isinstance(blob, dict):
            continue
        for r in blob.get("rules", []) or []:
            if isinstance(r, dict) and isinstance(r.get("where"), dict) and r.get("name"):
                sig = rule_signature(r["where"])
                if 4 <= len(sig) <= 400:
                    pool.append((fn, r["name"], sig))

    print(f"corpus: {len(pool)} seed rules with a non-null `where` and 4..400 signature rows")

    rng = random.Random(20260812)
    rng.shuffle(pool)
    sample = pool[:300]

    # Pairs: (a) genuine sub-signature pairs (entry := obs minus k rows), which
    # is what a held codebook entry actually is, and (b) unrelated cross pairs
    # as negative controls.
    i1 = i2 = i3 = 0
    n_pos = n_neg = 0
    neg_ok = 0
    for _fn, _nm, obs in sample:
        rows = sorted(obs, key=repr)
        k = max(1, len(rows) // 8)
        entry = frozenset(rows[:-k])          # a real sub-signature (slots = absences)
        tmpl, sigmas = ev(auw_term([entry, obs]))
        s_entry, s_obs = dict(sigmas[0]), dict(sigmas[1])
        cov = ev({"type": "Covers", "pattern": lit(entry), "instance": lit(obs), "wild": WILD})
        n_pos += 1
        if bool(cov) == (len(s_entry) == 0):
            i1 += 1
        resid = frozenset(list(s_obs.values())[0]) if s_obs else frozenset()
        if resid == (obs - entry):
            i2 += 1
        rt = ev({"type": "Substitute", "template": idx(auw_term([entry, obs]), 0),
                 "sigma": idx(idx(auw_term([entry, obs]), 1), 1), "wild": WILD})
        if frozenset(rt) == obs:
            i3 += 1

    for i in range(0, len(sample) - 1, 2):
        a, b = sample[i][2], sample[i + 1][2]
        if a <= b:
            continue
        n_neg += 1
        tmpl, sigmas = ev(auw_term([a, b]))
        s_a = dict(sigmas[0])
        cov = ev({"type": "Covers", "pattern": lit(a), "instance": lit(b), "wild": WILD})
        if bool(cov) == (len(s_a) == 0):
            neg_ok += 1

    print(f"\nPOSITIVE pairs (entry is a real sub-signature of obs), n={n_pos}")
    print(f"  I1  Covers  <->  sigma[entry] empty          : {i1}/{n_pos}")
    print(f"  I2  sigma[obs] == obs \\ entry (the residual)  : {i2}/{n_pos}")
    print(f"  I3  Substitute(template, sigma_obs) == obs   : {i3}/{n_pos}")
    print(f"\nNEGATIVE pairs (unrelated rules), n={n_neg}")
    print(f"  I1  Covers  <->  sigma[entry] empty          : {neg_ok}/{n_neg}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
