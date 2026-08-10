"""Install the WELL-POSEDNESS conjunct into `bo_mint_owned` (seed v1.2.0).

An authoring tool that EMITS seed data (tools/* is explicitly in the allowed
class -- it is not agent runtime). Run once; idempotent.

WHAT IT ADDS, AND WHY (VISION_FIGADJ_WELLPOSED_PREREG.md §2):

`bo_mint_owned` imports Zhou/Friedman/von der Heydt's assignment rule, whose
whole content is the CANCELLATION of the shared border |B|:

    |B|/perim(R) > |B|/perim(Q)   <=>   perim(R) < perim(Q)

That cancellation is a TWO-PARTY statement. It presupposes the border under
assignment is ONE length shared by TWO sides. When a single contour cell of R
faces two DIFFERENT enclosed components, that one cell is the whole of R's
shared border with EACH of them -- the same length is claimed in full by two
competitions at once, the claimed fractions sum to more than one, and |B| is
not a quantity that cancels. There is no well-posed competition there to win,
so the rule DECLINES -- exactly as it already declines a tie.

NOT a size test: it never mentions size and refuses a large component whose
contour cell is wedged between two rivals just as readily.

NO literal: structurally the twin of the single-ground-closure conjunct already
present in all four mint rules, generalised from the ground side to the rival
side. Its only literals are the 0.5 discriminators over the 0/1 `bg` flag.

Gated as `Or(bown_wp < 0.5, <well-posed>)` so the committed v1.1.0 replacement
reproduces byte-identically at the 0.0 default (§9).
"""
from __future__ import annotations

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "seeds", "vision_border_ownership.json")


def attr(var, key):
    return {"type": "Attr", "node": {"type": "Var", "name": var}, "key": key}


def enclosed_rival(var, of="R"):
    """`var` is an enclosed cell of a component OTHER than R's."""
    return [
        {"type": "Lt", "a": attr(var, "bg"), "b": {"type": "Lit", "value": 0.5}},
        {"type": "Not", "arg": {"type": "Eq",
                                "a": attr(var, "glabel"),
                                "b": attr(of, "glabel")}},
    ]


def wellposed():
    """Not Exists a member cell facing TWO DISTINCT enclosed rivals."""
    members = {
        "type": "Filter",
        "source": {"type": "NodesOfType", "node_type": "Cell"},
        "var_name": "f",
        "predicate": {"type": "And", "items": [
            {"type": "Eq", "a": attr("f", "glabel"), "b": attr("R", "glabel")},
            {"type": "Lt", "a": attr("f", "bg"),
             "b": {"type": "Lit", "value": 0.5}},
        ]},
    }
    nbrs = lambda v: {"type": "Neighbours",  # noqa: E731
                      "node": {"type": "Var", "name": v},
                      "edge_type": "neighbour", "any_type": False}
    inner = {"type": "Exists", "source": nbrs("f"), "var_name": "n2",
             "predicate": {"type": "And", "items": [
                 *enclosed_rival("n2"),
                 {"type": "Not", "arg": {"type": "Eq",
                                         "a": attr("n2", "glabel"),
                                         "b": attr("n1", "glabel")}},
             ]}}
    outer = {"type": "Exists", "source": nbrs("f"), "var_name": "n1",
             "predicate": {"type": "And", "items": [*enclosed_rival("n1"),
                                                    inner]}}
    return {"type": "Not",
            "arg": {"type": "Exists", "source": members, "var_name": "f",
                    "predicate": outer}}


def flag_off(key):
    return {"type": "Lt",
            "a": {"type": "Attr",
                  "node": {"type": "PickUnique",
                           "source": {"type": "NodesOfType",
                                      "node_type": "BorderOwnParams"}},
                  "key": key},
            "b": {"type": "Lit", "value": 0.5}}


def main():
    with open(PATH) as fh:
        seed = json.load(fh)

    rules = {r["name"]: r for r in seed["rules"]}
    owned = rules["bo_mint_owned"]
    conj = {"type": "Or", "items": [flag_off("bown_wp"), wellposed()]}

    if conj in owned["where"]["items"]:
        print("already installed -- no change")
        return

    # Appended LAST: the two O(N) graph aggregates before it are the expensive
    # gates, and this one is the most expensive of all (a neighbour-pair scan
    # over every member). Cheap-first ordering is the seed's own convention.
    owned["where"]["items"].append(conj)
    owned["comment"] += (
        " v1.2.0 -- WELL-POSEDNESS. The Zhou cancellation of |B| is a TWO-PARTY"
        " statement: it presupposes the border under assignment is ONE length"
        " shared by TWO sides. If a single contour cell of R faces two"
        " DIFFERENT enclosed components, that one cell is the whole of R's"
        " shared border with EACH of them, the same length is claimed in full"
        " by two competitions at once, the claimed fractions sum to more than"
        " one, and |B| does not cancel -- `perim(R) < perim(Q)` no longer"
        " stands for `|B|/perim(R) > |B|/perim(Q)`. There is no well-posed"
        " competition to win, so the rule HOLDS IT OPEN, exactly as it holds a"
        " TIE open and as bo_mint_gestalt holds a size tie open. NOT a size"
        " test -- it never mentions size, and refuses a large component whose"
        " contour cell is wedged between two rivals just as readily; that it"
        " eliminates the single-cell speckle false mints is a CONSEQUENCE of"
        " rim=1 being both the global minimum of the perimeter statistic (so a"
        " singleton wins every competition unconditionally) and maximally"
        " shared. §13: NO literal -- structurally the twin of the"
        " single-ground-closure conjunct already in all four mint rules,"
        " generalised from the ground side to the rival side; its only literals"
        " are the 0.5 discriminators over the 0/1 bg flag. Armed by"
        " bown_wp>0.5; at the 0.0 default the Or short-circuits and the"
        " committed v1.1.0 replacement is byte-identical (§9). See"
        " VISION_FIGADJ_WELLPOSED_PREREG.md.")

    for node in seed["nodes"]:
        if node["type"] == "BorderOwnParams":
            node["attrs"].setdefault("bown_wp", 0.0)

    seed["version"] = "1.2.0"
    seed["description"] += (
        " v1.2.0 -- WELL-POSEDNESS: bo_mint_owned holds open a competition"
        " whose shared border is claimed in full by two rivals at once (a"
        " member cell facing two distinct enclosed components), because |B|"
        " cancels only between TWO parties. Armed by bown_wp, OFF by default."
        " See VISION_FIGADJ_WELLPOSED_PREREG.md.")

    with open(PATH, "w") as fh:
        json.dump(seed, fh, indent=1)
        fh.write("\n")
    print("installed well-posedness conjunct; seed now v1.2.0")


if __name__ == "__main__":
    main()
