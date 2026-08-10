"""Emit `seeds/vision_identity_seam.json` — ARM B of the identity-seam rung.

A seed BUILDER: it emits graph data and contains no agent logic. Every decision
this rung makes lives in the rules below, as Terms.

ARM B keeps the sd loop's TOPOLOGY (decode -> gate -> mint -> grow -> epoch ->
re-decode) and replaces exactly one thing: the recognition predicate. The stock
loop accepts an observation as "already held" when `Count(residual) == 0` over a
COMPOSITIONAL decode of the whole parts library. Arm B instead accepts it when
its best NORMALIZED CROSS-CORRELATION score against the held codebook STRICTLY
EXCEEDS the best score the SAME comparator achieves, in the SAME substrate,
against the SAME codebook, on calibration noise probes.

THE FLOOR IS MEASURED, NEVER CHOSEN (protocol section 13). No numeric threshold
appears anywhere below; the only literals are structural (0, 1, 1.0) and the
`MaxOver` empty-source sentinel -1e18. `tests/test_identity_seam_migrated.py`
asserts exactly that.

NO new Rust and NO new Term: Dot, MaxOver, Argmax, Filter, IfThenElse, Gt, Lt,
Count, Neighbours, NodesOfType, IndexAt, Plus, Eq, Not, And all pre-exist.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "seeds" / "vision_identity_seam.json"

SENTINEL = -1e18


# ---------------------------------------------------------------- Term helpers
def var(n):
    return {"type": "Var", "name": n}


def attr(node, key):
    return {"type": "Attr", "node": node, "key": key}


def lit(v):
    return {"type": "Lit", "value": v}


def eq(a, b):
    return {"type": "Eq", "a": a, "b": b}


def not_(a):
    return {"type": "Not", "arg": a}


def and_(*items):
    return {"type": "And", "items": list(items)}


def gt(a, b):
    return {"type": "Gt", "a": a, "b": b}


def lt(a, b):
    return {"type": "Lt", "a": a, "b": b}


def term(t):
    return {"__term__": t}


#: The seam is ARMED only when `IdentitySeamParams.seam > 0.5`. The seed ships
#: 0.0 (protocol section 9), so installing it changes nothing until a
#: measurement explicitly arms it with a blind write.
ARMED = gt(
    {"type": "Count",
     "source": {"type": "Filter",
                "source": {"type": "NodesOfType",
                           "node_type": "IdentitySeamParams"},
                "var_name": "sp",
                "predicate": gt(attr(var("sp"), "seam"), lit(0.5))}},
    lit(0))


def held_codebook(v="sig"):
    """The seam's OWN codebook: signatures this seam grew from pixels.

    Scoped to `seam_grown == 1.0` rather than all `ShapeSignature`s, because
    `boot_core` installs 17 non-pixel-derived signatures that carry no `nvals`.
    Arm B's codebook therefore starts EMPTY and grows only from percepts --
    declared in the pre-registration section 4 as a known arm asymmetry."""
    return {"type": "Filter",
            "source": {"type": "NodesOfType", "node_type": "ShapeSignature"},
            "var_name": v,
            "predicate": eq(attr(var(v), "seam_grown"), lit(1.0))}


def ncc(v="sig"):
    """THE VERDICT (V3). One `Dot` of two unit-centred 36-vectors IS normalized
    cross-correlation -- the normalization lives in the adapter's encoding, as
    in `vision_verdict_comparator`. No Sqrt, no Div, no guarded division."""
    return {"type": "Dot",
            "a": attr(var("obs"), "nvals"),
            "b": attr(var(v), "nvals")}


BEST_SCORE = {"type": "MaxOver", "source": held_codebook(), "var_name": "sig",
              "value": ncc(), "default": lit(SENTINEL)}

#: `default: null` so an EMPTY codebook yields None, never a fabricated winner
#: (the `xf_identify` precedent).
BEST_NAME = attr({"type": "Argmax", "source": held_codebook(),
                  "var_name": "sig", "value": ncc(),
                  "default": None}, "name")

#: THE MEASURED FLOOR. `MaxOver` the agent's OWN calibration-noise observations
#: of the score each achieves against the SAME codebook. Hub-anchored via
#: `Neighbours(ag, "observed")` -- never a global `NodesOfType` grab
#: (protocol section 12.1).
FLOOR = {"type": "MaxOver",
         "source": {"type": "Filter",
                    "source": {"type": "Neighbours", "node": var("ag"),
                               "edge_type": "observed", "any_type": False},
                    "var_name": "g",
                    "predicate": eq(attr(var("g"), "probe_kind"), lit("G2c"))},
         "var_name": "g", "value": attr(var("g"), "is_max"),
         "default": lit(SENTINEL)}

#: The decision, inlined (never read back from an attr written in the same
#: effects list) -- the `vd_refuse` precedent, so the verdict cannot depend on
#: effect ordering.
EXCEEDS_FLOOR = gt(attr(var("obs"), "is_max"), FLOOR)

OBS_MATCH = [["ag", "observed", "obs"]]


def rule(name, comment, where, effects, match=None):
    return {"name": name, "comment": comment, "match_type": "Observation",
            "match": match or OBS_MATCH, "where": where, "effects": effects}


RULES = [
    rule(
        "is_recalib",
        "RE-ARM THE FLOOR WHEN THE CODEBOOK GROWS. A floor measured against a "
        "codebook of 3 is not the floor for a codebook of 300: as K grows the "
        "best noise score drifts UP, and a frozen floor would silently stop "
        "refusing. Epoch-driven, exactly as `sd_redecode` re-arms decode.",
        and_(ARMED,
             eq(attr(var("obs"), "probe_kind"), lit("G2c")),
             lt(attr(var("obs"), "calib_epoch"),
                attr(var("ag"), "codebook_epoch"))),
        [["set_attr", "obs", "status", "is_pending"],
         ["set_attr", "obs", "is_scored", 0],
         ["set_attr", "obs", "calib_epoch",
          term(attr(var("ag"), "codebook_epoch"))]]),

    rule(
        "is_score",
        "Score this observation against the held codebook. Fires for real "
        "observations AND for the G2c calibration probes -- the floor must be "
        "the same comparator on the same codebook, or it is not a floor.",
        and_(ARMED,
             eq(attr(var("obs"), "status"), lit("is_pending")),
             not_(eq(attr(var("obs"), "is_scored"), lit(1)))),
        [["set_attr", "obs", "is_max", term(BEST_SCORE)],
         ["set_attr", "obs", "is_scored", 1]]),

    rule(
        "is_calib_done",
        "A scored calibration probe leaves `is_pending` so it never mints and "
        "never blocks `is_decide`'s ordering guard. G2c DEFINES the floor; it "
        "is not itself a thing to be identified.",
        and_(ARMED,
             eq(attr(var("obs"), "probe_kind"), lit("G2c")),
             eq(attr(var("obs"), "is_scored"), lit(1)),
             eq(attr(var("obs"), "status"), lit("is_pending"))),
        [["set_attr", "obs", "status", "is_calib"]]),

    rule(
        "is_decide",
        "THE DECISION, and the whole rung turns on it. Held iff this "
        "observation's best score STRICTLY EXCEEDS the floor the same "
        "comparator achieves on noise against the same codebook. The ordering "
        "guard (no observation still pending-and-unscored) makes the floor "
        "complete before it is read -- the `vd_refuse` two-layer precedent, "
        "with the fixpoint doing the sequencing and the adapter doing none.",
        and_(ARMED,
             eq(attr(var("obs"), "status"), lit("is_pending")),
             eq(attr(var("obs"), "is_scored"), lit(1)),
             not_(eq(attr(var("obs"), "probe_kind"), lit("G2c"))),
             eq({"type": "Count",
                 "source": {"type": "Filter",
                            "source": {"type": "Neighbours", "node": var("ag"),
                                       "edge_type": "observed",
                                       "any_type": False},
                            "var_name": "g",
                            "predicate": and_(
                                eq(attr(var("g"), "status"),
                                   lit("is_pending")),
                                not_(eq(attr(var("g"), "is_scored"),
                                        lit(1))))}},
                lit(0))),
        [["set_attr", "obs", "is_floor", term(FLOOR)],
         ["set_attr", "obs", "identified_as",
          term({"type": "IfThenElse", "cond": EXCEEDS_FLOOR,
                "then": BEST_NAME, "other": lit("novel")})],
         ["set_attr", "obs", "status",
          term({"type": "IfThenElse", "cond": EXCEEDS_FLOOR,
                "then": lit("is_held"), "other": lit("is_novel")})]]),

    rule(
        "is_mint",
        "GROW THE CODEBOOK. A percept the graph could not tell from noise "
        "becomes a held identity in its own right, and the epoch bump re-arms "
        "the floor against the codebook it just joined. The `vq_grow_quantum` "
        "pattern, plus `nvals` -- which `vq_grow_quantum` does not copy, and "
        "without which a grown signature would be invisible to the verdict.",
        and_(ARMED,
             eq(attr(var("obs"), "status"), lit("is_novel")),
             eq({"type": "Count",
                 "source": {"type": "Neighbours", "node": var("obs"),
                            "edge_type": "is_minted", "any_type": False}},
                lit(0))),
        [["add_node", "ss", "ShapeSignature",
          {"name": term({"type": "IndexAt",
                         "seq": attr(var("obs"), "key"), "index": lit(0)}),
           "faculty": term({"type": "IndexAt",
                            "seq": attr(var("obs"), "key"), "index": lit(0)}),
           "signature": term(attr(var("obs"), "signature")),
           "dim_types": term(attr(var("obs"), "dim_types")),
           "nvals": term(attr(var("obs"), "nvals")),
           "kind": "faculty",
           "seam_grown": term(lit(1.0))}],
         ["add_edge", "obs", "is_minted", "ss"],
         ["set_attr", "obs", "identified_as",
          term({"type": "IndexAt",
                "seq": attr(var("obs"), "key"), "index": lit(0)})],
         ["set_attr", "obs", "status", "is_minted"],
         ["set_attr", "ag", "codebook_epoch",
          term({"type": "Plus",
                "items": [attr(var("ag"), "codebook_epoch"), lit(1.0)]})]]),
]

SEED = {
    "id": "vision_identity_seam",
    "version": "1.0.0",
    "depends_on": ["shape_decode_loop"],
    "description": (
        "THE PERCEPT->IDENTITY SEAM, arm B (VISION_IDENTITY_SEAM_PREREG.md, "
        "seeds 72000-72999). A region recognised in one frame is decided to be "
        "THE SAME HELD IDENTITY in the next -- or, if the graph cannot tell it "
        "from noise, it is minted as a new one and the codebook grows. Keeps "
        "the sd loop's topology and replaces only the recognition verdict: "
        "V3 normalized cross-correlation against a MEASURED noise floor, in "
        "place of `Count(residual)==0` over a compositional decode. SHIPS OFF "
        "(IdentitySeamParams.seam = 0.0) and is not in any default boot set, "
        "so every committed result reproduces byte-identically (section 9). "
        "No new Rust, no new Term, and NO NUMERIC THRESHOLD anywhere."),
    "nodes": [{"local_id": 0, "type": "IdentitySeamParams",
               "attrs": {"seam": 0.0}}],
    "edges": [],
    "productions": [
        {"subject_type": "Observation", "edge_type": "is_minted",
         "object_type": "ShapeSignature"}],
    "rules": RULES,
}


def main():
    OUT.write_text(json.dumps(SEED, indent=1) + "\n")
    blob = json.dumps(RULES)
    print(f"wrote {OUT}  ({len(RULES)} rules, {len(blob)} bytes of rule JSON)")
    # The section 13 self-check, here as well as in the gate: the only numeric
    # literals may be structural or the MaxOver sentinel.
    import re
    nums = {float(m) for m in re.findall(r'"value":\s*(-?[\d.e+]+)', blob)}
    print("numeric literals in rules:", sorted(nums))
    assert nums <= {0.0, 1.0, 0.5, SENTINEL}, f"magic number: {nums}"


if __name__ == "__main__":
    main()
