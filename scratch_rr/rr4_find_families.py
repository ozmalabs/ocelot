#!/usr/bin/env python3
"""RR4 step 1 — find real seed-rule families that share one anti-unified
template, so the parallelogram (b = T(a), x = T(c)) is actually defined.

A "family" here is a set of rules whose `where` clauses have the IDENTICAL
tree skeleton (same node types, same key sets, same list lengths at every
position) and differ only at scalar leaves. That is the condition under
which `AntiUnifyWitness`'s Dict arm — which generalises over SHARED keys
only — is lossless, i.e. `Substitute(template, sigma_i) == i` exactly.

Read-only.
"""
import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def skeleton(node):
    """The tree with every scalar leaf replaced by a hole — the family key."""
    if isinstance(node, dict):
        return ("D", tuple(sorted((k, skeleton(v)) for k, v in node.items())))
    if isinstance(node, list):
        return ("L", tuple(skeleton(x) for x in node))
    return ("_",)


def leaf_paths(node, path=()):
    """Every scalar-leaf path, so a family's variation can be read off."""
    if isinstance(node, dict):
        for k in sorted(node):
            yield from leaf_paths(node[k], path + (k,))
    elif isinstance(node, list):
        for i, x in enumerate(node):
            yield from leaf_paths(x, path + (i,))
    else:
        yield path, node


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
            if not (isinstance(r, dict) and isinstance(r.get("where"), dict)):
                continue
            w = r["where"]
            n_leaves = sum(1 for _ in leaf_paths(w))
            if not (3 <= n_leaves <= 40):
                continue
            fams[skeleton(w)].append((fn, r["name"], w))

    big = [(k, v) for k, v in fams.items() if len(v) >= 3]
    big.sort(key=lambda kv: -len(kv[1]))
    print(f"families (identical skeleton, 3..40 leaves, >=3 members): {len(big)}")

    shown = 0
    for _key, members in big:
        # how many leaf positions actually VARY across the family?
        paths = [p for p, _ in leaf_paths(members[0][2])]
        varying = []
        for p in paths:
            vals = {json.dumps(dict(leaf_paths(m[2]))[p], sort_keys=True) for m in members}
            if len(vals) > 1:
                varying.append((p, sorted(vals)[:4]))
        if not (1 <= len(varying) <= 4):
            continue
        seeds_in = {m[0] for m in members}
        print(f"\n--- {len(members)} members, {len(varying)} varying leaf position(s), "
              f"seeds: {sorted(seeds_in)[:3]}")
        for m in members[:6]:
            print(f"      {m[1]}  (seeds/{m[0]})")
        for p, vals in varying:
            print(f"    varies at {'.'.join(map(str,p))}: {vals}")
        shown += 1
        if shown >= 8:
            break
    return 0


if __name__ == "__main__":
    sys.exit(main())
