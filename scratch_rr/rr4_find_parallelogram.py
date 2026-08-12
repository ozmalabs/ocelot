#!/usr/bin/env python3
"""RR4 step 2 — find a real PARALLELOGRAM in the seed rule corpus.

`shape_math_grounding.md`'s Cluster 1 (the arrow/parallelogram view of
analogy): `b = T(a)`, `x = T(c)`. For that to be a genuine transfer and not
a relabelling, the three known corners must be arranged so that

    a and b differ ONLY on a set of paths P
    a and c differ ONLY on a DISJOINT set of paths Q

so that x — "c but with b's difference" — carries b's P-content and c's
Q-content, and is therefore neither b nor c. And for x to be genuinely NEW,
that (P from b, Q from c) combination must not already be a member of the
family.

Search over rule OBJECTS `{"match": ..., "where": ...}` (both halves — a
rule's applicability is both), read-only.
"""
import json
import os
import sys
from collections import defaultdict
from itertools import combinations

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def skeleton(n):
    if isinstance(n, dict):
        return ("D", tuple(sorted((k, skeleton(v)) for k, v in n.items())))
    if isinstance(n, list):
        return ("L", tuple(skeleton(x) for x in n))
    return ("_",)


def leaves(n, path=()):
    if isinstance(n, dict):
        for k in sorted(n):
            yield from leaves(n[k], path + (k,))
    elif isinstance(n, list):
        for i, x in enumerate(n):
            yield from leaves(x, path + (i,))
    else:
        yield path, n


def main():
    seed_dir = os.path.join(HERE, "seeds")
    fams = defaultdict(list)
    for fn in sorted(os.listdir(seed_dir)):
        if not fn.endswith(".json"):
            continue
        try:
            blob = json.load(open(os.path.join(seed_dir, fn)))
        except Exception:
            continue
        if not isinstance(blob, dict):
            continue
        for r in blob.get("rules", []) or []:
            if not (isinstance(r, dict) and isinstance(r.get("where"), dict)
                    and isinstance(r.get("match"), list) and r.get("name")):
                continue
            obj = {"match": r["match"], "where": r["where"]}
            k = sum(1 for _ in leaves(obj))
            if 4 <= k <= 30:
                fams[skeleton(obj)].append((fn, r["name"], obj, r))

    found = []
    for _key, members in fams.items():
        if len(members) < 3:
            continue
        lv = {m[1]: dict(leaves(m[2])) for m in members}
        names = [m[1] for m in members]
        present = {tuple(sorted(lv[n].items(), key=lambda kv: repr(kv))) for n in names}
        for a, b, c in combinations(names, 3):
            for (A, B, C) in ((a, b, c), (a, c, b), (b, a, c), (b, c, a), (c, a, b), (c, b, a)):
                P = {p for p in lv[A] if lv[A][p] != lv[B].get(p)}
                Q = {p for p in lv[A] if lv[A][p] != lv[C].get(p)}
                if not P or not Q or (P & Q):
                    continue
                x = dict(lv[C])
                for p in P:
                    x[p] = lv[B][p]
                key = tuple(sorted(x.items(), key=lambda kv: repr(kv)))
                if key in present:
                    continue          # the fourth corner already exists — not new
                found.append({
                    "seeds": sorted({m[0] for m in members}),
                    "a": A, "b": B, "c": C,
                    "P": sorted(".".join(map(str, p)) for p in P),
                    "Q": sorted(".".join(map(str, q)) for q in Q),
                    "family_size": len(members),
                })
    print(f"genuine parallelograms with a MISSING fourth corner: {len(found)}")
    seen = set()
    uniq = []
    for f in found:
        k = (f["a"], f["b"], f["c"])
        if k in seen:
            continue
        seen.add(k)
        uniq.append(f)
    print(f"distinct (a,b,c) triples: {len(uniq)}\n")
    for f in uniq[:12]:
        print(f"  a={f['a']}\n  b={f['b']}\n  c={f['c']}")
        print(f"    P (a->b paths) = {f['P']}")
        print(f"    Q (a->c paths) = {f['Q']}")
        print(f"    seeds={f['seeds']} family_size={f['family_size']}\n")
    json.dump(uniq[:200], open(os.path.join(HERE, "scratch_rr", "rr4_parallelograms.json"), "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
