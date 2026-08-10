"""AUTHOR seeds/vision_border_ownership.json v1.1.0 from v1.0.0.

Authoring tooling ONLY (CLAUDE.md: `tools/*` are one-off scripts that EMIT seed
manifests; not agent runtime). It DERIVES the new rules from the incumbent's own
term trees by STRUCTURAL LOCATION -- never a substring edit, never a hand-retyped
copy -- so the incumbent path is byte-identical by construction.

WHAT CHANGES (VISION_FIGADJ_REPLACEMENT_PREREG.md):

  `G_figadj` -- "refuse this component if ANY of its cells touches ANY cell of
  ANY other enclosed component" -- encodes ISOLATION, not objecthood. It is true
  of a synthetic raster (figure on blank ground) and false of a photograph (a
  scene is a PARTITION; objects abut objects). It refuses 93.4% of 12,319
  enclosed components on real frames.

  The replacement, from the seed's OWN cited basis (Zhou/Friedman/von der Heydt
  2000: ownership of an IDENTICAL local edge FLIPS with the global figure --
  ownership is CONTEXTUAL and COMPETITIVE):

      A shared boundary is ASSIGNED, not disqualifying. Where two enclosed
      regions abut, ownership of the shared border goes to the side better
      explained as owning it -- the side whose OWN perimeter that border
      accounts for more of. The shared border length |B| is common to both
      sides, so |B|/perim(R) > |B|/perim(Q)  <=>  perim(R) < perim(Q).
      A TIE IS HELD OPEN (no proto), reusing bo_mint_gestalt's size-tie
      precedent.

  So the incumbent's inner predicate ("n is an abutting cell of another enclosed
  component") gains ONE conjunct: `Not(Lt(R.rim, n.rim))` -- refuse only if R
  does NOT strictly win the ownership competition. Contact alone no longer
  vetoes; only a LOST COMPETITION does.

§13 -- NO NEW THRESHOLD. The only new comparison is `Lt` between two MEASURED
counts (rim vs rim). The tie is equality. The `0.5` literals introduced are
boolean discriminators over the 0/1 `bg` flag and the 0/1 `bown_own` flag --
the same class the value-flood rung's AST audit found for all 18 incumbent
`0.5`s. NO literal is compared against `val`, `rim`, or any count.

§9 -- BYTE-IDENTITY WHERE BEHAVIOUR MUST NOT MOVE. `bo_mint_enclosed` keeps its
term tree EXACTLY and gains only the mutual-exclusion flag guard
`Lt(bown_own, 0.5)`; `bown_own` defaults to 0.0, so every existing caller runs
the incumbent predicate unchanged. The replacement lives in a SEPARATE rule
`bo_mint_owned`, armed only by `bown_own > 0.5`.

COST -- `rim` is MATERIALISED as a cell attribute by `bo_rim` (gated on the
floods being SETTLED, reusing the incumbent's own settled sub-term) rather than
recomputed inside the mint gate. Recomputing it in-gate is O(N) per abutting
pair per root and was measured-by-estimate at ~10^9 term evaluations per corpus;
materialising it is O(N) per cell, once, after settling.

MONOTONICITY -- before `bo_rim` fires, every `rim` is 0, so `Lt(0, 0)` is false
and the gate REFUSES. Rims can therefore only turn a refusal into a mint, never
a mint into a regret; the `Not Exists ProtoObject at this root` guard is never
asked to retract.
"""
from __future__ import annotations

import copy
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED = os.path.join(ROOT, "seeds", "vision_border_ownership.json")


# --- structural locators (NEVER a substring selector) ------------------------
def rule_by_name(seed, name):
    hits = [r for r in seed["rules"] if r["name"] == name]
    if len(hits) != 1:
        raise SystemExit(f"expected exactly one rule {name!r}, got {len(hits)}")
    return hits[0]


def flag_gate(term):
    """Is this term the `bown > 0.5` flag gate?"""
    return (term.get("type") == "Gt"
            and term.get("a", {}).get("type") == "Attr"
            and term["a"].get("key") == "bown"
            and term["a"].get("node", {}).get("type") == "PickUnique"
            and term.get("b", {}).get("type") == "Lit"
            and term["b"].get("value") == 0.5)


def is_figadj(term):
    """Is this term the G_figadj conjunct?

    Shape: Not(Exists(source=Filter(NodesOfType Cell, f: f.glabel == R.glabel
    and f.bg < 0.5), f, Exists(Neighbours(f, neighbour), n,
    And(Not(Eq(n.glabel, R.glabel)), Lt(n.bg, 0.5))))).
    Located by that structure, then CONFIRMED by the variable names and the
    attribute keys it touches -- no text matching anywhere.
    """
    if term.get("type") != "Not":
        return False
    ex = term.get("arg", {})
    if ex.get("type") != "Exists" or ex.get("var_name") != "f":
        return False
    src = ex.get("source", {})
    if src.get("type") != "Filter" or src.get("var_name") != "f":
        return False
    if src.get("source", {}).get("node_type") != "Cell":
        return False
    inner = ex.get("predicate", {})
    if inner.get("type") != "Exists" or inner.get("var_name") != "n":
        return False
    if inner.get("source", {}).get("type") != "Neighbours":
        return False
    pred = inner.get("predicate", {})
    if pred.get("type") != "And" or len(pred.get("items", [])) != 2:
        return False
    a, b = pred["items"]
    return (a.get("type") == "Not"
            and a.get("arg", {}).get("type") == "Eq"
            and a["arg"]["a"].get("key") == "glabel"
            and a["arg"]["b"].get("key") == "glabel"
            and b.get("type") == "Lt"
            and b.get("a", {}).get("key") == "bg")


def find_one(term, pred, path=()):
    """Every location in `term` where `pred` holds, as (parent, key/index)."""
    out = []
    if isinstance(term, dict):
        if pred(term):
            out.append(path)
        for k, v in term.items():
            out += find_one(v, pred, path + (k,))
    elif isinstance(term, list):
        for i, v in enumerate(term):
            out += find_one(v, pred, path + (i,))
    return out


def at(obj, path):
    for k in path:
        obj = obj[k]
    return obj


def put(obj, path, value):
    for k in path[:-1]:
        obj = obj[k]
    obj[path[-1]] = value


# --- term constructors -------------------------------------------------------
def var(n):
    return {"type": "Var", "name": n}


def attr(node, key):
    return {"type": "Attr", "node": node, "key": key}


def lit(v):
    return {"type": "Lit", "value": v}


def params_attr(key):
    return attr({"type": "PickUnique",
                 "source": {"type": "NodesOfType",
                            "node_type": "BorderOwnParams"}}, key)


def rim_count(label_term):
    """perim(X) as a MEASURED COUNT: the number of enclosed cells whose glabel
    is `label_term` and which have at least one neighbour of a different glabel
    -- i.e. the region's own contour, in cells. A count, not a threshold."""
    return {
        "type": "Count",
        "source": {
            "type": "Filter",
            "source": {"type": "NodesOfType", "node_type": "Cell"},
            "var_name": "w",
            "predicate": {
                "type": "And",
                "items": [
                    {"type": "Eq", "a": attr(var("w"), "glabel"),
                     "b": label_term},
                    {"type": "Lt", "a": attr(var("w"), "bg"), "b": lit(0.5)},
                    {"type": "Exists",
                     "source": {"type": "Neighbours", "node": var("w"),
                                "edge_type": "neighbour", "any_type": False},
                     "var_name": "u",
                     "predicate": {"type": "Not", "arg": {
                         "type": "Eq", "a": attr(var("u"), "glabel"),
                         "b": label_term}}},
                ],
            },
        },
    }


def main():
    with open(SEED) as fh:
        seed = json.load(fh)
    if seed["version"] != "1.0.0":
        raise SystemExit(f"expected v1.0.0 on disk, found {seed['version']}")

    enclosed = rule_by_name(seed, "bo_mint_enclosed")
    incumbent_body = copy.deepcopy(enclosed)

    # --- locate G_figadj STRUCTURALLY ---------------------------------------
    hits = find_one(enclosed["where"], is_figadj)
    if len(hits) != 1:
        raise SystemExit(f"expected exactly ONE G_figadj conjunct, found "
                         f"{len(hits)}: {hits}")
    figadj_path = hits[0]
    print(f"[locate] G_figadj at where{list(figadj_path)}")

    # --- locate the SETTLED sub-term (reused verbatim by bo_rim) ------------
    settled = copy.deepcopy(enclosed["where"]["items"][3])
    if settled.get("type") != "And" or len(settled["items"]) != 2:
        raise SystemExit("settled sub-term not where expected")
    print("[locate] settled sub-term reused verbatim by bo_rim")

    # --- 1. bo_rim: materialise the contour count on every enclosed cell ----
    my_rim = rim_count(attr(var("R"), "glabel"))
    bo_rim = {
        "name": "bo_rim",
        "comment": (
            "MATERIALISE perim(component) as a cell attribute. rim = the number "
            "of ENCLOSED cells sharing this cell's glabel that have at least one "
            "neighbour of a DIFFERENT glabel -- the region's own contour, in "
            "cells. Gated on bown_own>0.5 (the competitive-ownership arm) and on "
            "the floods being SETTLED (the incumbent's own settled sub-term, "
            "reused verbatim) so glabel is final before any count is taken. "
            "Re-fires while its own value disagrees with the count, so it "
            "settles to a fixpoint like bo_label; idempotent once settled. "
            "MEASURED QUANTITY, no threshold (§13): the only literals are the "
            "0.5 boolean discriminators over the 0/1 bg and bown_own flags."),
        "match": [["field", "has_cell", "R"]],
        "where": {"type": "And", "items": [
            {"type": "Gt", "a": params_attr("bown"), "b": lit(0.5)},
            {"type": "Gt", "a": params_attr("bown_own"), "b": lit(0.5)},
            {"type": "Lt", "a": attr(var("R"), "bg"), "b": lit(0.5)},
            settled,
            {"type": "Not", "arg": {"type": "Eq",
                                    "a": attr(var("R"), "rim"),
                                    "b": copy.deepcopy(my_rim)}},
        ]},
        "effects": [["set_attr", "R", "rim",
                     {"__term__": copy.deepcopy(my_rim)}]],
    }

    # --- 2. bo_mint_owned: the incumbent tree with ONE conjunct added -------
    owned = copy.deepcopy(enclosed)
    owned["name"] = "bo_mint_owned"
    owned["comment"] = (
        "MINT a ProtoObject for an enclosed component that OWNS ITS WHOLE "
        "CONTOUR. Byte-identical to bo_mint_enclosed EXCEPT that the G_figadj "
        "conjunct's inner predicate gains Not(Lt(R.rim, n.rim)): an abutting "
        "cell `n` of another enclosed component refuses R only if R does NOT "
        "STRICTLY WIN the ownership competition against n's component. "
        "DERIVATION (Zhou/Friedman/von der Heydt 2000, the basis this seed "
        "already cites): a shared border is ASSIGNED, not disqualifying; it "
        "goes to the side whose own perimeter it accounts for more of, and "
        "since the shared length |B| is common to both sides, "
        "|B|/perim(R) > |B|/perim(Q) <=> perim(R) < perim(Q). A TIE "
        "(perim equal) is HELD OPEN -- no proto -- exactly as bo_mint_gestalt "
        "holds its size tie open. Contact alone no longer vetoes; only a lost "
        "competition does, which is what makes ownership CONTEXTUAL rather "
        "than a test for ISOLATION. §13: the new comparison is between two "
        "MEASURED counts and introduces no literal. Armed by bown_own>0.5; "
        "with the flag at its 0.0 default this rule never fires and "
        "bo_mint_enclosed runs unchanged (§9).")

    # arm it: bown_own > 0.5 (and keep the incumbent's own bown > 0.5)
    fg = find_one(owned["where"], flag_gate)
    if len(fg) != 1:
        raise SystemExit(f"expected ONE flag gate in bo_mint_owned, got {fg}")
    put(owned["where"], fg[0] + ("__replace__",), None)  # placeholder guard
    del at(owned["where"], fg[0])["__replace__"]
    owned["where"]["items"].insert(
        1, {"type": "Gt", "a": params_attr("bown_own"), "b": lit(0.5)})

    # the ONE structural change: extend the inner predicate
    fa_hits = find_one(owned["where"], is_figadj)
    if len(fa_hits) != 1:
        raise SystemExit("G_figadj not located in the copy")
    figadj = at(owned["where"], fa_hits[0])
    inner_and = figadj["arg"]["predicate"]["predicate"]
    inner_and["items"].append({
        "type": "Not",
        "arg": {"type": "Lt",
                "a": attr(var("R"), "rim"),
                "b": attr(var("n"), "rim")}})
    print("[derive] bo_mint_owned = bo_mint_enclosed + Not(Lt(R.rim, n.rim))")

    # --- 3. mutual exclusion: the incumbent is OFF when the arm is ON -------
    enclosed["where"]["items"].insert(
        1, {"type": "Lt", "a": params_attr("bown_own"), "b": lit(0.5)})

    # --- 4. the flag itself, OFF by default ---------------------------------
    for n in seed["nodes"]:
        if n["type"] == "BorderOwnParams":
            n["attrs"]["bown_own"] = 0.0

    # --- 5. splice, bump ----------------------------------------------------
    names = [r["name"] for r in seed["rules"]]
    seed["rules"].insert(names.index("bo_mint_enclosed"), bo_rim)
    names = [r["name"] for r in seed["rules"]]
    seed["rules"].insert(names.index("bo_mint_enclosed") + 1, owned)
    seed["version"] = "1.1.0"
    seed["description"] += (
        " v1.1.0 -- COMPETITIVE BORDER OWNERSHIP replaces the isolation test. "
        "bo_mint_enclosed's G_figadj ('the figure is a hole in ONE surface') "
        "refuses a component if ANY cell touches ANY other enclosed component: "
        "true of a synthetic raster, FALSE of a photograph, where a scene is a "
        "PARTITION and objects abut objects (it refused 93.4% of 12,319 real "
        "enclosed components -- VISION_VALUE_FLOOD_RESULTS.md). bo_mint_owned "
        "assigns the shared border instead of being disqualified by it: the "
        "side whose own perimeter the border accounts for more of owns it "
        "(perim(R) < perim(Q), the shared length cancelling), a TIE IS HELD "
        "OPEN, and perim is materialised as Cell.rim by bo_rim. No new "
        "threshold (§13): a comparison of two measured counts. Armed by "
        "BorderOwnParams.bown_own, OFF by default, so the incumbent path is "
        "byte-identical (§9). See VISION_FIGADJ_REPLACEMENT_PREREG.md.")

    # --- 6. the incumbent tree must be UNCHANGED except the flag guard ------
    check = copy.deepcopy(enclosed)
    removed = check["where"]["items"].pop(1)
    if removed.get("a", {}).get("key") != "bown_own":
        raise SystemExit("guard insertion landed in the wrong slot")
    if json.dumps(check, sort_keys=True) != json.dumps(incumbent_body,
                                                       sort_keys=True):
        raise SystemExit("INCUMBENT TREE MOVED -- §9 violated, refusing to write")
    print("[§9] bo_mint_enclosed byte-identical modulo the mutual-exclusion guard")

    with open(SEED, "w") as fh:
        json.dump(seed, fh, indent=1)
        fh.write("\n")
    print(f"[written] {SEED} v{seed['version']} "
          f"rules={[r['name'] for r in seed['rules']]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
