"""Author `vision_border_ownership` v1.3.0 -- the CONTAINMENT SCOPE on the
rival set of `bo_mint_owned`.

A seed-manifest EMITTER (tools/ is authoring, not agent runtime). Every
decision it writes is a RULE; this file only assembles JSON.

Pre-registration: VISION_FIGADJ_NESTING_PREREG.md. Seeds 92000-92999.
Idempotent: re-running on a v1.3.0 seed is a no-op.
"""
from __future__ import annotations

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED = os.path.join(ROOT, "seeds", "vision_border_ownership.json")

FLAG = "bown_nest"


def flag_lt(key):
    """Attr(PickUnique(NodesOfType(BorderOwnParams)), key) < 0.5 -- the OFF arm."""
    return {"type": "Lt",
            "a": {"type": "Attr",
                  "node": {"type": "PickUnique",
                           "source": {"type": "NodesOfType",
                                      "node_type": "BorderOwnParams"}},
                  "key": key},
            "b": {"type": "Lit", "value": 0.5}}


def attr(var, key):
    return {"type": "Attr", "node": {"type": "Var", "name": var}, "key": key}


def not_contained(rival, qv, pv):
    """THE CONJUNCT (PREREG s1.4). Rival `rival` enters the competition only if
    its component has a neighbour that is neither itself nor R -- i.e. it is NOT
    a hole in R. A positive Exists over the graph's own adjacency: no Count, no
    size, no magnitude literal."""
    return {
        "type": "Exists",
        "source": {"type": "Filter",
                   "source": {"type": "NodesOfType", "node_type": "Cell"},
                   "var_name": qv,
                   "predicate": {"type": "And", "items": [
                       {"type": "Eq", "a": attr(qv, "glabel"),
                        "b": attr(rival, "glabel")},
                       {"type": "Lt", "a": attr(qv, "bg"),
                        "b": {"type": "Lit", "value": 0.5}}]}},
        "var_name": qv,
        "predicate": {
            "type": "Exists",
            "source": {"type": "Neighbours",
                       "node": {"type": "Var", "name": qv},
                       "edge_type": "neighbour", "any_type": False},
            "var_name": pv,
            "predicate": {"type": "And", "items": [
                {"type": "Not", "arg": {"type": "Eq", "a": attr(pv, "glabel"),
                                        "b": attr(rival, "glabel")}},
                {"type": "Not", "arg": {"type": "Eq", "a": attr(pv, "glabel"),
                                        "b": attr("R", "glabel")}}]}}}


def gated(rival, qv, pv):
    """Or(flag OFF, rival-is-not-contained) -- s9: at the 0.0 default the Or
    short-circuits and v1.2.0 is byte-identical."""
    return {"type": "Or", "items": [flag_lt(FLAG),
                                    not_contained(rival, qv, pv)]}


def already(items):
    return any(it.get("type") == "Or"
               and any(sub.get("type") == "Lt"
                       and sub.get("a", {}).get("key") == FLAG
                       for sub in it.get("items", []) if isinstance(sub, dict))
               for it in items if isinstance(it, dict))


V13 = (
    " v1.3.0 -- CONTAINMENT / NESTED FIGURE-GROUND. G_own_lost quantified `R "
    "must win` over ALL of R's borders, including the border with a component "
    "R ENCLOSES -- which is not part of R's outer contour at all, but the "
    "contour of R's own HOLE. Zhou/von der Heydt measure ownership OF AN EDGE "
    "WITH A SIDE, not of a region: a region is figure when it owns its OUTER "
    "contour, and a figure is routinely GROUND for a smaller figure on it. "
    "Where Q is entirely surrounded by R the shared border IS the whole of "
    "perim(Q), so |B|/perim(Q) == 1 identically for EVERY R -- pinned at its "
    "maximum by the geometry, not decided by the competition (the same "
    "degeneracy v1.2.0 found at rim=1, one level up); `perim(R) < perim(Q)` "
    "there reads a tautology, not a competition. So a CONTAINED rival is "
    "REMOVED from the competition (v1.2.0 held its case OPEN because there was "
    "no fact of the matter; here there is one and Zhou supplies it -- the "
    "hole's border belongs to the hole, R is ground THERE, and R's figurehood "
    "is decided on its outer contour). The SAME rival scoping applies to the "
    "v1.2.0 well-posedness conjunct: a non-rival cannot make a competition "
    "ill-posed, and the two conjuncts must range over ONE rival set or they "
    "disagree about what a rival is. s13: a positive Exists over the graph's "
    "own adjacency -- NO Count, NO size, NO magnitude literal; structurally "
    "the third instance of the seed's own single-surround closure test, "
    "applied to the rival's surround. It excludes a 1-cell hole and a 200-cell "
    "hole identically and excludes NO merely-abutting neighbour. Armed by "
    "bown_nest>0.5, OFF by default, so v1.2.0 is byte-identical (s9). "
    "See VISION_FIGADJ_NESTING_PREREG.md.")


def main():
    with open(SEED) as fh:
        seed = json.load(fh)

    if seed["version"] == "1.3.0":
        print("already v1.3.0 -- no-op")
        return

    assert seed["version"] == "1.2.0", seed["version"]
    params = [n for n in seed["nodes"] if n["type"] == "BorderOwnParams"]
    assert len(params) == 1
    params[0]["attrs"][FLAG] = 0.0                      # s9: default OFF

    owned = {r["name"]: r for r in seed["rules"]}["bo_mint_owned"]
    top = owned["where"]["items"]

    # ---- (1) G_own_lost: the rival `n` in the ownership competition -------
    gol = [it for it in top if it.get("type") == "And"
           and it["items"][0].get("arg", {}).get("source", {}).get("type")
           == "Filter"]
    assert len(gol) == 1, f"expected 1 G_own_lost conjunct, found {len(gol)}"
    npred = gol[0]["items"][0]["arg"]["predicate"]["predicate"]["items"]
    assert not already(npred)
    npred.append(gated("n", "q1", "p1"))

    # ---- (2) the v1.2.0 well-posedness conjunct: rivals n1 and n2 ---------
    wp = [it for it in top if it.get("type") == "Or"
          and any(sub.get("a", {}).get("key") == "bown_wp"
                  for sub in it["items"] if isinstance(sub, dict))]
    assert len(wp) == 1, f"expected 1 bown_wp-gated Or, found {len(wp)}"
    n1pred = wp[0]["items"][1]["arg"]["predicate"]["predicate"]["items"]
    n2 = [it for it in n1pred if it.get("type") == "Exists"]
    assert len(n2) == 1
    n2pred = n2[0]["predicate"]["items"]
    assert not already(n1pred) and not already(n2pred)
    n2pred.append(gated("n2", "q3", "p3"))
    n1pred.append(gated("n1", "q2", "p2"))

    seed["version"] = "1.3.0"
    seed["description"] = seed["description"] + V13
    owned["comment"] = owned["comment"] + V13

    with open(SEED, "w") as fh:
        json.dump(seed, fh, indent=1)
        fh.write("\n")
    print(f"written {SEED} -> v1.3.0 ({FLAG} default 0.0)")


if __name__ == "__main__":
    main()
