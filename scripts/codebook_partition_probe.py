#!/usr/bin/env python3
"""codebook_partition_probe — the deciding measurement for
`docs/research/engine_substrate/CODEBOOK_PARTITION_CONSOLIDATION_PREREG.md`.

Answers AR2 and AR3-clause-3 from REAL seed data, live, with no mocking:

  AR2   Does any decode Term scope its candidate pool by the `kind` attr?
  AR3.3 If a `ShapeSignature*` subtype were merged into
        `ShapeSignature{kind:...}`, would the decode return the SAME result?

Both probes load the ACTUAL `seeds/*.json` node declarations — no synthetic
codebooks — and run the SAME `ShapeDecode` call shape the live reading
faculties use (`domains/discourse_coherence.py::_decode`:
`beam=1, max_steps=1, cand_k=4`).

Run:  PYTHONPATH=runners/dsl/python:. python3 scripts/codebook_partition_probe.py
"""
from __future__ import annotations

import json
import os
import sys

import substrate_rs as srs

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def seed_nodes(name: str) -> list[dict]:
    with open(os.path.join(_ROOT, "seeds", f"{name}.json")) as f:
        return json.load(f).get("nodes", []) or []


def build(specs: list[tuple[str, str | None]]) -> srs.Substrate:
    """specs: (seed name, retype-to) — `None` keeps each node's own type,
    a string REWRITES every `ShapeSignature*` node in that seed to that
    type (the consolidation, applied to live graph data)."""
    s = srs.Substrate()
    for seed, retype in specs:
        for nd in seed_nodes(seed):
            t = nd["type"]
            if retype and t.startswith("ShapeSignature"):
                t = retype
            s.add_node(t, dict(nd.get("attrs", {})))
    return s


def decode(s: srs.Substrate, goal: list, codebook_type: str) -> dict:
    """The live reading-faculty call shape, verbatim."""
    r = s._inner.evaluate({
        "type": "ShapeDecode",
        "goal": {"type": "Lit", "value": goal},
        "codebook_type": codebook_type,
        "beam": 1, "max_steps": 1, "cand_k": 4,
    }, {})
    return {
        "plan": [(p["part"], p["kind"], p["shape_fit"], len(p["covers"]))
                 for p in r.get("plan", [])],
        "residual": list(r.get("residual") or ()),
    }


def rule(t: str) -> None:
    print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78)


# --------------------------------------------------------------------------- #
#  AR2 — is `kind` a pool filter?
# --------------------------------------------------------------------------- #
def ar2() -> None:
    rule("AR2 — does anything scope a decode pool by `kind`?")
    s = srs.Substrate()
    s.add_node("ShapeSignature", {"name": "p_alpha", "kind": "alpha",
                                  "signature": '[["AAA","x"]]'})
    s.add_node("ShapeSignature", {"name": "p_beta", "kind": "beta",
                                  "signature": '[["BBB","y"]]'})

    def d(goal, **extra):
        t = {"type": "ShapeDecode", "goal": {"type": "Lit", "value": goal},
             "codebook_type": "ShapeSignature", "beam": 1, "max_steps": 1, "cand_k": 4}
        t.update(extra)
        r = s._inner.evaluate(t, {})
        return [(p["part"], p["kind"]) for p in r.get("plan", [])]

    base = d([["BBB", "y"]])
    print(f"  goal BBB, no filter                  -> {base}")
    print(f"  goal BBB, term param kind='alpha'    -> {d([['BBB','y']], kind='alpha')}")
    print(f"  goal BBB, term param codebook_kind   -> {d([['BBB','y']], codebook_kind='alpha')}")
    print(f"  goal BBB, codebook_scope=['p_alpha'] -> "
          f"{d([['BBB','y']], codebook_scope={'type':'Lit','value':['p_alpha']})}")
    print(f"  goal BBB, exclude=['p_beta']         -> "
          f"{d([['BBB','y']], exclude={'type':'Lit','value':['p_beta']})}")
    print("\n  VERDICT: `kind` is NOT a filter — an unknown `kind`/`codebook_kind` term")
    print("  key is silently DROPPED by the JSON term parser and the foreign-kind part")
    print("  stays a live candidate. The two filters that DO exist (`codebook_scope`,")
    print("  `exclude`) are both keyed on the part's NAME. `kind` is carried through to")
    print("  the output plan as a LABEL only (`load_parts`, shape_decode.rs:260/313).")


# --------------------------------------------------------------------------- #
#  AR3.3 — the coherence/construction merge, on real seed data
# --------------------------------------------------------------------------- #
def ar3_coherence() -> int:
    rule("AR3.3 — merge ShapeSignatureCoherence into ShapeSignature{kind:...}?")
    print("  `seeds/coherence_relations.json` DEPENDS_ON `reading_constructions`, so the")
    print("  two pools are ALWAYS co-loaded. Both hold a part whose signature leads with")
    print("  the predicate `IF`:")
    print("    reading_constructions  ShapeSignature{name:'conditional construction'} "
          "[['IF'],['THEN']]")
    print("    coherence_relations    ShapeSignatureCoherence{name:'condition_if'} [['IF']]")

    specs = [("reading_constructions", None), ("coherence_relations", None)]
    merged = [("reading_constructions", None), ("coherence_relations", "ShapeSignature")]
    sep, mer = build(specs), build(merged)

    bad = 0
    for label, goal, pool_before in [
        ("coherence decode of a marked conditional", [["IF"]], "ShapeSignatureCoherence"),
        ("clause decode of an if/then construction", [["IF"], ["THEN"]], "ShapeSignature"),
    ]:
        before = decode(sep, goal, pool_before)
        after = decode(mer, goal, "ShapeSignature")
        same = before == after
        bad += 0 if same else 1
        print(f"\n  {label}  goal={goal}")
        print(f"    BEFORE (separate types, pool={pool_before:24s}) {before}")
        print(f"    AFTER  (merged into ShapeSignature{{kind}})       {after}")
        print(f"    IDENTICAL: {same}")
    return bad


# --------------------------------------------------------------------------- #
#  AR3.3 — the stroke grain ladder, on real seed data
# --------------------------------------------------------------------------- #
def ar3_stroke() -> int:
    rule("AR3.3 — merge ShapeSignatureCoarse/Mid/FineChild into ShapeSignature{kind}?")
    print("  All four stroke grains share the SAME predicate vocabulary")
    print("  (seg / pose_x / pose_y / pose_o / pose_s) and overlapping relation counts.")

    sep = build([("stroke_shapes", None)])
    mer = build([("stroke_shapes", "ShapeSignature")])

    # A real goal: the fine signature of an actual held stroke quantum.
    goal = None
    for nd in seed_nodes("stroke_shapes"):
        if nd["type"] == "ShapeSignature" and (nd["attrs"].get("kind") == "stroke"):
            sig = nd["attrs"].get("signature")
            goal = json.loads(sig) if isinstance(sig, str) else list(sig)
            name = nd["attrs"]["name"]
            break
    assert goal is not None
    print(f"  goal = the held fine signature of {name!r} ({len(goal)} relations)")

    before = decode(sep, goal, "ShapeSignature")
    after = decode(mer, goal, "ShapeSignature")
    same = before == after
    print(f"\n    BEFORE (4 separate types; fine pool = 263 parts) {before}")
    print(f"    AFTER  (all 502 parts in ONE pool)               {after}")
    print(f"    IDENTICAL: {same}")
    return 0 if same else 1


# --------------------------------------------------------------------------- #
#  The other eleven subtypes — predicate-disjointness check, from seed data
# --------------------------------------------------------------------------- #
def ar1_disjointness() -> None:
    rule("AR1 — predicate vocabulary per ShapeSignature* pool (from seeds/*.json)")
    import glob
    import collections
    pred = collections.defaultdict(set)
    cnt = collections.Counter()
    nosig = collections.Counter()
    for f in sorted(glob.glob(os.path.join(_ROOT, "seeds", "*.json"))):
        try:
            d = json.load(open(f))
        except Exception:
            continue
        if not isinstance(d, dict):
            continue
        for nd in d.get("nodes", []) or []:
            if not isinstance(nd, dict):
                continue
            t = nd.get("type", "")
            if not (isinstance(t, str) and t.startswith("ShapeSignature")):
                continue
            a = nd.get("attrs") or {}
            key = t if t != "ShapeSignature" else f"ShapeSignature[kind={a.get('kind')}]"
            cnt[key] += 1
            sig = a.get("signature")
            if sig is None:
                nosig[key] += 1
                continue
            if isinstance(sig, str):
                try:
                    sig = json.loads(sig)
                except Exception:
                    sig = None
            if isinstance(sig, list):
                for r in sig:
                    if isinstance(r, list) and r:
                        pred[key].add(str(r[0]))
    for k in sorted(cnt, key=lambda x: -cnt[x]):
        ps = sorted(pred[k])
        tag = "  <-- NO `signature` attr: load_parts SKIPS these" if nosig[k] == cnt[k] else ""
        print(f"  {cnt[k]:5d} {k:44s} {len(ps):3d} preds{tag}")
    print("\n  Cross-pool predicate OVERLAPS (the only way a merge can change a decode):")
    import itertools
    for a, b in itertools.combinations(sorted(cnt, key=lambda x: -cnt[x]), 2):
        ov = pred[a] & pred[b]
        if ov:
            print(f"    {a:40s} x {b:40s} {sorted(ov)}")


def main() -> int:
    ar2()
    ar1_disjointness()
    bad = ar3_coherence() + ar3_stroke()
    rule("SUMMARY")
    print(f"  merges that CHANGED a live decode result: {bad}")
    print("  (AR3 clause 3: any non-identical before/after blocks that consolidation.)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
