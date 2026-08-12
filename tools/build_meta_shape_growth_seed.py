#!/usr/bin/env python3
"""Emit `seeds/meta_shape_growth.json` — THE META-SHAPE GRAIN'S GROWTH LADDER.

`SHAPE_AUDIT.md` finding #1: `seeds/shape_vocabulary.json` holds 11 `MetaShape`
+ 13 `ShapePrinciple` nodes and *nothing in the tree mints one at runtime* —
"the sd loop's fourth rung is not wired to the faculty named 'shape'." This
seed wires it, and wires the three rungs ABOVE the mint too, because
`shape_decode.rs::load_parts` is GRAIN-AGNOSTIC: it reads any
`codebook_type`-typed node carrying `name` + `signature`. So `ShapeDecode`,
`TransformDecode` and `DimInfer` all point at `codebook_type: "MetaShape"` here
with ZERO new Rust — the same four-rung Occam ladder every other grain has:

  rung 1  msg_decode / msg_recognize            exact structural cover
  rung 2  msg_transform_decode / ..._transformed  a uniform per-dimension delta
  rung 3  msg_infer_dimension / ..._dim           a generator-composed residual
  prior   msg_recognize_prior                     the KEYWORD bootstrap
  rung 4  msg_mint_shape                          novelty — mint a new MetaShape

The keyword prior sits BELOW rungs 1-3 and ABOVE the mint deliberately: the
eleven SEEDED MetaShapes carry no `signature` at all, so rungs 1-3 are dormant
on them and keywords are the honest bootstrap — the weakest evidence, run last
before minting.

The epoch counter is `meta_codebook_epoch`, NOT the sd loop's own
`codebook_epoch`: a MetaShape mint does not grow the `ShapeSignature` codebook,
so re-arming the other grain's observations would be churn, not correctness.

Run: python3 tools/build_meta_shape_growth_seed.py
"""
from __future__ import annotations

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "seeds", "meta_shape_growth.json")

OBS = "ShapeObservation"
OBSERVED_EDGE = "observed_shape"
CODEBOOK = "MetaShape"


# --- Term shorthands (this file EMITS graph data; it makes no decisions) ----
def var(n):
    return {"type": "Var", "name": n}


def attr(n, k):
    return {"type": "Attr", "node": var(n), "key": k}


def lit(v):
    return {"type": "Lit", "value": v}


def eq(a, b):
    return {"type": "Eq", "a": a, "b": b}


def ne(a, b):
    return {"type": "Not", "arg": eq(a, b)}


def and_(*items):
    return {"type": "And", "items": list(items)}


def count(src):
    return {"type": "Count", "source": src}


def nbrs(n, et):
    return {"type": "Neighbours", "node": var(n), "edge_type": et}


def sd(field=None):
    t = {"type": "ShapeDecode", "goal": attr("obs", "signature"),
         "codebook_type": CODEBOOK, "beam": 3, "max_steps": 8, "cand_k": 3,
         "wild_objects": False}
    if field:
        t["field"] = field
    return t


def td(field=None):
    t = {"type": "TransformDecode", "goal": attr("obs", "signature"),
         "codebook_type": CODEBOOK, "max_dims": 2}
    if field:
        t["field"] = field
    return t


def di(field=None):
    t = {"type": "DimInfer", "goal": attr("obs", "signature"),
         "codebook_type": CODEBOOK, "max_dims": 2}
    if field:
        t["field"] = field
    return t


def mint(field=None):
    t = {"type": "MetaShapeMint", "observation": var("obs"),
         "obs_type": OBS, "status_value": "residual"}
    if field:
        t["field"] = field
    return t


def prior():
    """The keyword-prior verdict — `RecogniseShape` over the observation's own
    STRUCTURAL signature (attribute keys as relation predicates), not over the
    lossy flat string `teach.py:93` used to build."""
    return {"type": "RecogniseShape", "text": attr("obs", "signature")}


def T(term):
    return {"__term__": term}


MATCH = [["ag", OBSERVED_EDGE, "obs"]]

STATUS = lambda v: eq(attr("obs", "status"), lit(v))          # noqa: E731
NOT_MINTED = eq(count(nbrs("obs", "minted_shape")), lit(0))

# RUNG 1 HIT REQUIRES POSITIVE EVIDENCE, NOT AN ABSENT RESIDUAL.
# Learned the hard way while building this seed, and it is exactly the hazard
# `shape_decode.rs` itself warns about ("an absence produced by a LOOKUP is not
# evidence of a measurement"): when NO held MetaShape carries a `signature`,
# `ShapeDecode` returns `{authored: false, reason: "no held parts ..."}` — with
# NO `residual` key at all. `Count(None)` is 0, so a bare "residual is empty"
# guard reads a codebook that could not even be consulted as FULL COVERAGE and
# recognises every observation against nothing. Measured live: all four probe
# observations came back `recognized` with a meaningless `covered_by` before
# this was tightened. So the hit condition is `covered_count > 0` AND the
# residual empty — something was actually covered.
#
# AND RUNG 1 IS `Covers`, NOT `ShapeDecode`'S LITERAL SET COVER — a grain
# difference, measured, not assumed. Every other grain's codebook holds LITERAL
# parts, so `sd_decode`'s literal decode (`wild_objects: false`) is the right
# rung 1 there. THIS codebook holds anti-unified lgg PATTERNS: a minted entry's
# signature is `[["buyer", WILD], ["is_a", "traderecord"], ...]`, and a literal
# set cover can never match `["buyer", "erin"]` against `["buyer", WILD]`.
# `Covers` is the dual primitive that does (`term.rs::covers_value`, "WILD
# matches anything") and is exactly what `AntiUnify` is paired with everywhere
# else in this tree. Verified live before rewiring: `Covers(minted_core,
# near_variant) == True` while `ShapeDecode(near_variant, codebook="MetaShape")`
# returned no coverage at all.
#
# `FixedCount(pattern) > 0` is REQUIRED, not decoration: an all-WILD pattern
# covers every observation, so a degenerate entry would swallow the whole grain.
#
# OPEN ARITY, and why the Term is `CoversOpen` rather than `Covers`
# (META_SHAPE_ARITY_AND_KEY_SEPARATOR_FIXES, 2026-08-12; the defect
# `SHAPE_TYPE_VOCABULARY_SPIKE.md` §3.3.1 predicted from source and this rung
# reproduced live). `Covers` lands on `covers_value`'s `Tuple | List` arm,
# which requires `pt.len() == it.len()` — so a minted k-relation MetaShape
# could only ever cover an observation with EXACTLY k relations, and the same
# item carrying one extra attribute fell through every rung to `residual`.
#
# The question this guard asks is SUBSUMPTION — does this held generalisation
# APPLY to this item — and subsumption is superset-tolerant by definition
# (`covers_value`'s own `Dict` arm already says so: "instance may carry extra
# keys"). The list encoding was chosen for `AntiUnify`'s sake (a relation is a
# POSITIONAL `[predicate, value]` pair), not because arity-exactness was
# wanted. `CoversOpen` splits the two levels: relation SET outside, positional
# tuple inside — which is also what `shape_decode::covers_relation` has always
# done one layer down, so this restores consistency rather than inventing
# semantics.
#
# `FixedCount(pattern) > 0` is REQUIRED, not decoration: an all-WILD pattern
# covers every observation, so a degenerate entry would swallow the whole
# grain. It matters MORE under open arity, not less.
def _covers(shape_var):
    return and_({"type": "Gt",
                 "a": {"type": "FixedCount", "pattern": attr(shape_var, "signature")},
                 "b": lit(0)},
                {"type": "CoversOpen",
                 "pattern": attr(shape_var, "signature"),
                 "instance": attr("obs", "signature")})


RUNG1_HIT = {"type": "Exists",
             "source": {"type": "NodesOfType", "node_type": CODEBOOK},
             "var_name": "cms", "predicate": _covers("cms")}
RUNG1_FAILED = {"type": "Not", "arg": RUNG1_HIT}
RUNG2_DONE = and_(eq(attr("obs", "transform_checked"), lit(1)),
                  ne(attr("obs", "transform_explained"), lit(1)))
RUNG3_DONE = and_(eq(attr("obs", "dim_checked"), lit(1)),
                  ne(attr("obs", "dim_explained"), lit(1)))

# A held MetaShape whose `name` equals the keyword prior's verdict. Used both
# ways: its presence is the prior HIT, its absence is the RESIDUAL. Expressed
# as an Exists rather than a null-comparison so the same term serves both and
# no `Lit(null)` idiom is needed.
PRIOR_HIT = {"type": "Exists", "source": {"type": "NodesOfType", "node_type": CODEBOOK},
             "var_name": "pms", "predicate": eq(attr("pms", "name"), prior())}

RULES = [
    # ---------------- rung 1 : exact structural cover ---------------------
    dict(
        name="msg_decode",
        comment=(
            "RUNG 1, DEQUANTIZE at the META-SHAPE grain: a pending "
            "ShapeObservation is decoded against the held MetaShape codebook "
            "via the UNCHANGED ShapeDecode Term, pointed at "
            "codebook_type='MetaShape'. This works with zero new Rust because "
            "shape_decode.rs::load_parts is grain-agnostic — it reads any "
            "codebook_type-typed node carrying `name` + `signature`. The "
            "eleven SEEDED MetaShapes carry no signature and are simply "
            "skipped by load_parts, which is why the keyword prior "
            "(msg_recognize_prior) still exists below."),
        match_type=OBS, match=MATCH,
        where=STATUS("pending"),
        effects=[
            ["set_attr", "obs", "decode", T(sd())],
            ["set_attr", "obs", "residual", T(sd("residual"))],
            ["set_attr", "obs", "covered_count", T(sd("covered_count"))],
            ["set_attr", "obs", "decoded_epoch", T(attr("ag", "meta_codebook_epoch"))],
            ["set_attr", "obs", "status", "decoded"],
        ],
    ),
    dict(
        name="msg_recognize",
        comment=(
            "RUNG 1 HIT: an empty residual means the held meta-shape codebook "
            "fully explains this observation — recognised, no graph growth. "
            "covered_by is recovered by the SAME FixedCount(AntiUnify(...)) "
            "specificity metric sd_recognize uses, over MetaShape instead of "
            "ShapeSignature — a DERIVED specificity, never an asserted "
            "ordinal (contrast SHAPE_AUDIT.md §2.3)."),
        match_type=OBS, match=MATCH,
        where=and_(STATUS("decoded"), RUNG1_HIT),
        effects=[
            ["set_attr", "obs", "status", "recognized"],
            ["set_attr", "obs", "covered_by", T({
                "type": "Attr", "key": "name",
                "node": {"type": "Argmax",
                         "source": {"type": "Filter",
                                    "source": {"type": "NodesOfType", "node_type": CODEBOOK},
                                    "var_name": "cms",
                                    "predicate": _covers("cms")},
                         "var_name": "cms",
                         "value": {"type": "FixedCount",
                                   "pattern": attr("cms", "signature")},
                         "default": None}})],
        ],
    ),
    # ---------------- rung 2 : transform in the existing basis -------------
    dict(
        name="msg_transform_decode",
        comment=(
            "RUNG 2 at the meta-shape grain: before minting a 25th entry, ask "
            "whether the residual is an ALREADY-HELD meta-shape stepping by ONE "
            "uniform per-dimension delta. At this grain a relation is "
            "[predicate, value] and the predicate slot is never transformable, "
            "so what rung 2 catches here is a held shape whose VALUE slots are "
            "consistently substituted — the same shape re-instantiated, which "
            "is recognition, not novelty. Same TransformDecode Term, "
            "codebook_type='MetaShape'."),
        match_type=OBS, match=MATCH,
        where=and_(STATUS("decoded"), RUNG1_FAILED,
                   ne(attr("obs", "transform_checked"), lit(1))),
        effects=[
            ["set_attr", "obs", "transform", T(td())],
            ["set_attr", "obs", "transform_explained", T(td("explained"))],
            ["set_attr", "obs", "transform_checked", 1],
        ],
    ),
    dict(
        name="msg_recognize_transformed",
        comment="RUNG 2 HIT — recognised under transformation, not minted.",
        match_type=OBS, match=MATCH,
        where=and_(STATUS("decoded"), eq(attr("obs", "transform_explained"), lit(1)),
                   NOT_MINTED),
        effects=[
            ["set_attr", "obs", "status", "recognized_transformed"],
            ["set_attr", "obs", "covered_by", T(td("base"))],
        ],
    ),
    # ---------------- rung 3 : infer the dimension -------------------------
    dict(
        name="msg_infer_dimension",
        comment=(
            "RUNG 3 at the meta-shape grain: a residual rung 2 could not "
            "explain gets ONE look at a missing dimension through the held "
            "DimensionGenerator codebook, via the UNCHANGED DimInfer Term. "
            "HONEST EXPECTATION, registered: a meta-shape signature's slots are "
            "STRINGS, not integer coordinates, so DimInfer's generators "
            "(rotation90 / reflections / scale2 / modular — all coordinate "
            "maps) have nothing to act on and this rung is a GRACEFUL NO-OP at "
            "this grain today. It is wired anyway because the ladder's shape is "
            "the point and because a future meta-shape signature carrying "
            "ordered/numeric slots would light it up for free."),
        match_type=OBS, match=MATCH,
        where=and_(STATUS("decoded"), RUNG1_FAILED, RUNG2_DONE,
                   ne(attr("obs", "dim_checked"), lit(1))),
        effects=[
            ["set_attr", "obs", "dim_infer", T(di())],
            ["set_attr", "obs", "dim_explained", T(di("explained"))],
            ["set_attr", "obs", "dim_checked", 1],
        ],
    ),
    dict(
        name="msg_recognize_dim",
        comment="RUNG 3 HIT — a missing dimension explains the residual.",
        match_type=OBS, match=MATCH,
        where=and_(STATUS("decoded"), eq(attr("obs", "dim_explained"), lit(1)),
                   NOT_MINTED),
        effects=[
            ["set_attr", "obs", "status", "recognized_dim"],
            ["set_attr", "obs", "covered_by", T(di("base"))],
        ],
    ),
    # ---------------- the keyword prior (bootstrap) ------------------------
    dict(
        name="msg_recognize_prior",
        comment=(
            "THE KEYWORD PRIOR — the bootstrap rung, reached only after rungs "
            "1-3 have all failed, because it is the WEAKEST evidence in the "
            "ladder and the only one that can reach the eleven seeded, "
            "signature-less MetaShapes. It runs the FIXED RecogniseShape "
            "scorer over the observation's own STRUCTURAL signature: attribute "
            "keys are scored as relation PREDICATES and outrank prose, "
            "distinct keyword hits break what used to be broken "
            "alphabetically, and a genuine tie returns None (SHAPE_AUDIT.md "
            "§2.5's three stacked defects). No verdict ⇒ no MetaShape has that "
            "name ⇒ this rule cannot fire and msg_residual does."),
        match_type=OBS, match=MATCH,
        where=and_(STATUS("decoded"), RUNG1_FAILED, RUNG2_DONE, RUNG3_DONE, PRIOR_HIT),
        effects=[
            ["set_attr", "obs", "status", "recognized_prior"],
            ["set_attr", "obs", "covered_by", T(prior())],
        ],
    ),
    dict(
        name="msg_residual",
        comment=(
            "THE RESIDUAL: every rung failed and the keyword prior returned no "
            "verdict (either nothing scored, or the contest was genuinely tied "
            "— which the fixed scorer now reports honestly instead of "
            "resolving alphabetically). This is where the gap USED to die: "
            "teach.py fell back to the item's own domain/topic string and the "
            "codebook never grew. It is now a mint candidate."),
        match_type=OBS, match=MATCH,
        where=and_(STATUS("decoded"), RUNG1_FAILED, RUNG2_DONE, RUNG3_DONE,
                   {"type": "Not", "arg": PRIOR_HIT}),
        effects=[["set_attr", "obs", "status", "residual"]],
    ),
    # ---------------- rung 4 : mint ---------------------------------------
    dict(
        name="msg_mint_shape",
        comment=(
            "RUNG 4 — DYNAMIC QUANTIZATION AT THE META-SHAPE GRAIN, the mint "
            "SHAPE_AUDIT.md finding #1 reports is absent from the whole tree. "
            "Fires only when MetaShapeMint reports `mintable`, which requires "
            "ALL of: the residual's predicate-set key has RECURRED across >= 2 "
            "residual observations (recurrence is the definition of idiom — "
            "two is the smallest cardinality at which 'recurs' is defined, not "
            "a swept knob); the anti-unified core fixes at least one leaf "
            "(structural non-triviality, not a coverage fraction); and this "
            "observation is the group's canonical minter (lowest node id — the "
            "same Argmin canonical pick SHAPE_AUDIT.md §2.7 explicitly rejects "
            "as Pattern A), so a group of N mints ONCE per pass, not N times. "
            "Mint-once across passes is the name guard, and the name is derived "
            "from the SORTED predicate set — order-independent and untruncated, "
            "unlike the CapabilityAxis key §3.1 documents. The minted "
            "ShapePrinciple carries the shared predicates as `keywords` so "
            "every existing reader (analogical_thinking._vocab_hits / "
            "shape_hits / metashape_realisation_counts / the reflective "
            "self-shape faculty) sees the new entry through the interface it "
            "already uses. Bumping meta_codebook_epoch re-arms msg_redecode."),
        match_type=OBS, match=MATCH,
        where=and_(STATUS("residual"), NOT_MINTED,
                   eq(mint("mintable"), lit(1)),
                   {"type": "Not", "arg": {
                       "type": "Exists",
                       "source": {"type": "NodesOfType", "node_type": CODEBOOK},
                       "var_name": "ems",
                       "predicate": eq(attr("ems", "name"), mint("name"))}}),
        effects=[
            ["add_node", "ms", CODEBOOK, {
                "name": T(mint("name")),
                "signature": T(mint("signature")),
                "support": T(mint("support")),
                "minted": 1,
                "source": "meta_shape_growth",
            }],
            ["add_node", "pr", "ShapePrinciple", {
                "name": T(mint("name")),
                "keywords": T(mint("keys")),
                "minted": 1,
                "source": "meta_shape_growth",
            }],
            ["add_edge", "ms", "has_principle", "pr"],
            ["add_edge", "obs", "minted_shape", "ms"],
            ["set_attr", "obs", "status", "minted"],
            ["set_attr", "ag", "meta_codebook_epoch",
             T({"type": "Plus", "items": [attr("ag", "meta_codebook_epoch"), lit(1)]})],
        ],
    ),
    # ---------------- re-decode : the loop closes --------------------------
    dict(
        name="msg_redecode",
        comment=(
            "CODEBOOK GROWTH CLOSES THE LOOP: any observation last decoded "
            "under an older meta_codebook_epoch re-arms to 'pending', so "
            "msg_decode re-runs it against the GROWN codebook — mint → "
            "re-decode → recognize, driven by the run_rules fixpoint, with no "
            "Python iteration anywhere. The rung flags are cleared back to 0 "
            "(there is no unset_attr op; 0 is falsy for the Not(Eq(_,1)) "
            "guards and distinct from the 1 they test for) so each rung gets a "
            "fresh look at the NEW residual instead of reading stale flags."),
        match_type=OBS, match=MATCH,
        where=and_(
            {"type": "Or", "items": [STATUS(s) for s in (
                "recognized", "recognized_transformed", "recognized_dim",
                "recognized_prior", "residual", "minted")]},
            {"type": "Lt", "a": attr("obs", "decoded_epoch"),
             "b": attr("ag", "meta_codebook_epoch")}),
        effects=[
            ["set_attr", "obs", "status", "pending"],
            ["set_attr", "obs", "decoded_epoch", T(attr("ag", "meta_codebook_epoch"))],
            ["set_attr", "obs", "transform_checked", 0],
            ["set_attr", "obs", "transform_explained", 0],
            ["set_attr", "obs", "dim_checked", 0],
            ["set_attr", "obs", "dim_explained", 0],
        ],
    ),
]

MANIFEST = {
    "id": "meta_shape_growth",
    "version": "1.1.0",
    "depends_on": ["shape_vocabulary"],
    "description": (
        "THE META-SHAPE GRAIN'S GROWTH LADDER. SHAPE_AUDIT.md finding #1: the "
        "agent's meta-shape vocabulary is a closed, hand-authored 11-entry "
        "table with no mint path anywhere in the tree — 'the sd loop's fourth "
        "rung is not wired to the faculty named shape'. This seed wires the "
        "whole four-rung Occam ladder at that grain by pointing the UNCHANGED "
        "ShapeDecode / TransformDecode / DimInfer Terms at "
        "codebook_type='MetaShape' (load_parts is grain-agnostic), with the "
        "FIXED keyword scorer as the bootstrap rung below them and a new "
        "MetaShapeMint Term as rung 4. Emitted by "
        "tools/build_meta_shape_growth_seed.py."),
    "microtheory": {"name": "meta_shape_growth",
                    "description": "the meta-shape codebook grows on residual"},
    "nodes": [],
    "edges": [],
    # Γ PRODUCTIONS, DECLARED — not left empty. CLAUDE.md's "SHAPES, NOT
    # NUMBERS" section names the exact failure this avoids: "454 of 634
    # rule-carrying seed manifests declare zero Γ productions, 159 of which mint
    # edges from rule effects", and the bigville finding that a whole subsystem
    # can exist with `"productions": []`. Every edge type this seed's rules mint
    # or match on is declared here, so the admissibility grammar GENERATES the
    # allowed moves instead of the checker being bypassed.
    "productions": [
        {"provenance": "meta_shape_growth:observed_shape",
         "src": {"type": "Agent", "var": "ag"},
         "edge_type": OBSERVED_EDGE,
         "tgt": {"type": OBS, "var": "obs"}},
        {"provenance": "meta_shape_growth:minted_shape",
         "src": {"type": OBS, "var": "obs"},
         "edge_type": "minted_shape",
         "tgt": {"type": CODEBOOK, "var": "ms"}},
        {"provenance": "meta_shape_growth:has_principle",
         "src": {"type": CODEBOOK, "var": "ms"},
         "edge_type": "has_principle",
         "tgt": {"type": "ShapePrinciple", "var": "pr"}},
    ],
    "rules": RULES,
}

if __name__ == "__main__":
    with open(OUT, "w") as f:
        json.dump(MANIFEST, f, indent=1)
        f.write("\n")
    print(f"wrote {OUT} ({len(RULES)} rules)")
