#!/usr/bin/env python3
"""Emit `seeds/analogy_search.json` — THE ANALOGY SEARCH AS A FIRST-CLASS
GRAPH SEED.

`SHAPE_AUDIT.md` §2.4, the diagnosis this seed closes: the analogy SEARCH
(`domains/analogical_thinking.py::find_analogies` / `_compute_analogy` /
`_finalise_analogy` / `think_harder`) "was never moved into the graph". It
ran as a Python triple-nested loop (source concept × target Mts × target
concept) computing, at five fixed abstraction orders, a set overlap of string
tokens — "not one of the five orders consults a concept's edges." The
parallelogram/systematicity verdict was the one structural quantity, and it too
was assembled in Python.

This seed makes the search a first-class graph loop, exactly as
`seeds/meta_shape_growth.json` did for the meta-shape codebook and
`seeds/problem_shape_growth.json` did for the problem grain — ONE grain over,
and with ZERO new Rust for the same reason `problem_shape_growth` needed none:
every decision is expressible with the existing generic Terms.

THE PIPELINE (run_rules fixpoint, NO Python iteration in the loop):

  ingest    domains/analogy_search.observe writes, per source concept, one
            AnalogyProbe{signature, ...} scoped by codebook_scope to the
            target field's ConceptShape parts. Mechanical ingest only —
            the same shape meta_shape.observe / induce_concern already are.

  ap_decode RUNG 1, DEQUANTIZE: the probe's signature is decoded against the
            held ConceptShape codebook via the UNCHANGED ShapeDecode Term,
            restricted to the probe's target field(s) by codebook_scope. The
            matched target concept is ShapeDecode's own DERIVED covered_by
            field; the residual is what the target concept did NOT explain.
            This is the field scan — the inner loop that used to be Python —
            done in Rust over WHATEVER structure the concept signature
            carries (relational edges when present, attrs + vocabulary axes
            otherwise). "Arbitrary shapes across fields", not a five-order
            dial.

  ap_match  a probe whose decode covered >=1 relation is a candidate analogy.
            Its shared structure is the FixedCount of the AntiUnify of the two
            signatures — a DERIVED specificity, the same metric sd_recognize /
            ps_recognize use, never an asserted ordinal. transform_key
            (precomputed by the shim as mechanical destructuring of the
            shared-predicate set) is the systematicity bucket.

  ap_systematic  SYSTEMATICITY / the parallelogram, as a graph verdict:
            two probes that realise the SAME transform_key are the two
            corner-pairs of one parallelogram and corroborate each other
            (Gentner's systematicity computed, not asserted). This is the
            Count(Filter(... Eq(transform_key))) recurrence idiom
            ps_mint already uses — the ONLY quantity no per-pair scorer can
            produce, and it needs no concept edges.

  ap_emit   the VERDICT and the honest non-answer. A candidate is retained
            as an Analogy node (+ an `implements` edge asserting structural
            correspondence) only when it is ALIGNED (shared structure fixes
            >=1 axis) OR CORROBORATED (another probe realises the same
            transform). A candidate that is neither is surface coincidence
            and is NOT emitted — RULES_AS_SHAPE_DESIGN_SPIKE.md §4.2's
            "make the bucket a FILTER, not a verdict", applied literally.

  ap_redecode  codebook growth (a caller adding fields / concepts and bumping
            analogy_codebook_epoch) re-arms decoded probes, closing the loop —
            the run_rules fixpoint IS the search.

Run: python3 tools/build_analogy_search_seed.py
"""
from __future__ import annotations

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "seeds", "analogy_search.json")

PROBE = "AnalogyProbe"
CODEBOOK = "ConceptShape"
OBSERVED_EDGE = "observed_probe"
EPOCH_ATTR = "analogy_codebook_epoch"
WILD = "·?·"


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


def gt(a, b):
    return {"type": "Gt", "a": a, "b": b}


def lt(a, b):
    return {"type": "Lt", "a": a, "b": b}


def and_(*items):
    return {"type": "And", "items": list(items)}


def or_(*items):
    return {"type": "Or", "items": list(items)}


def not_(arg):
    return {"type": "Not", "arg": arg}


def count(src):
    return {"type": "Count", "source": src}


def nbrs(n, et):
    return {"type": "Neighbours", "node": var(n), "edge_type": et}


def nodes_of_type(t):
    return {"type": "NodesOfType", "node_type": t}


def filter_(source, var_name, predicate):
    return {"type": "Filter", "source": source, "var_name": var_name,
            "predicate": predicate}


def exists(source, var_name, predicate):
    return {"type": "Exists", "source": source, "var_name": var_name,
            "predicate": predicate}


def T(term):
    return {"__term__": term}


# ShapeDecode over the ConceptShape codebook, scoped to the probe's own
# target-field part-name set (codebook_scope = Attr(probe, "scope")). The
# scope attr is written by the shim as the list of "field::name" part names
# belonging to the probe's target field(s); a source concept therefore only
# ever decodes against OTHER fields, never its own — cross-field by
# construction, which is the whole point ("work by shape across fields").
#
# codebook_scope's documented empty-set hazard (shape_decode.rs::apply_scope:
# an all-dropped / absent scope leaves the codebook UNRESTRICTED) is handled
# defensively two ways: (1) the shim only ever writes a NON-EMPTY scope, and
# (2) every ConceptShape part name is prefixed with its field ("field::name"),
# so even an accidental unrestricted decode cannot match a same-field concept
# (the source concept's own field prefix never appears among the target parts
# it is being compared against). Belt and braces, exactly the defense
# problem_shape.py used with its NEW node type.
# --------------------------------------------------------------------------- #
# The match is a NEAREST-STRUCTURAL-NEIGHBOUR over the target field, not a
# codebook COMPOSITION. ShapeDecode explains a goal as a PLAN OF PARTS and only
# reports covered_by for a single-part FULL cover — the wrong shape for
# analogy, which is PARTIAL structural overlap between two concepts. So the
# match is Argmax over the probe's scoped target parts of the shared-structure
# count FixedCount(AntiUnify(source.sig, part.sig)) — the same specificity
# metric sd_recognize / ps_recognize use, here ranking candidate PARTNERS
# rather than covering parts. All existing Terms; still zero new Rust.
#
# Scope: the candidate set is the ConceptShape parts whose name is In the
# probe's own `scope` list (the shim wrote it to the target field(s), minus the
# probe's own part). In is an existing Term; this is the cross-field / no-self
# guard, and it needs no codebook_scope machinery.
def _candidate_parts():
    return filter_(nodes_of_type(CODEBOOK), "mt",
                   {"type": "In",
                    "member": attr("mt", "name"),
                    "container": attr("obs", "scope")})


def _pair_lgg():
    """The anti-unification (lgg) of the probe's signature with a candidate
    target's signature (`mt`) — the SHARED SHAPE of the pair."""
    return {"type": "AntiUnify",
            "values": {"type": "SetT", "items": [
                attr("obs", "signature"),
                attr("mt", "signature")]}}


def _shared_fixed():
    """FixedCount of the pair's lgg — the DERIVED specificity, never an
    asserted ordinal (SHAPE_AUDIT.md §2.3)."""
    return {"type": "FixedCount", "pattern": _pair_lgg(), "wild": WILD}


def _best_partner():
    """The candidate target part that shares the MOST structure with the probe
    — Argmax over the scoped candidates of the shared-structure count. This is
    the analogical PARTNER: the concept in another field whose shape most
    resembles the source's. Ties resolve by the engine's deterministic Argmax.
    Returns the NODE (Argmax's contract); read its `name`/`signature` via Attr."""
    return {"type": "Argmax",
            "source": _candidate_parts(),
            "var_name": "mt",
            "value": _shared_fixed(),
            "default": None}


def _best_count():
    """The shared-structure count of the best partner, computed self-contained
    (does NOT read covered_by, which is being set in the same effect snapshot):
    FixedCount(AntiUnify(obs.sig, best_partner.sig))."""
    return {"type": "FixedCount",
            "pattern": {"type": "AntiUnify",
                        "values": {"type": "SetT", "items": [
                            attr("obs", "signature"),
                            {"type": "Attr", "key": "signature",
                             "node": _best_partner()}]}},
            "wild": WILD}


def _matched_sig():
    """The signature of the best partner (the part whose name == the recorded
    covered_by). `Attr(key=signature, node=Argmax(...))` — the exact
    node-then-field idiom ps_recognize uses. Pinned by covered_by so the
    single-element Argmax just re-selects it deterministically."""
    return {"type": "Attr", "key": "signature",
            "node": {"type": "Argmax",
                     "source": filter_(nodes_of_type(CODEBOOK), "m2",
                                       eq(attr("m2", "name"),
                                          attr("obs", "covered_by"))),
                     "var_name": "m2",
                     "value": lit(1),
                     "default": None}}


def _pair_lgg_matched():
    """The lgg of the probe's signature with the RECORDED best partner's
    signature (read by name via covered_by), for the post-decode ap_match /
    transform_key computations — where `mt` is no longer in scope."""
    return {"type": "AntiUnify",
            "values": {"type": "SetT", "items": [
                attr("obs", "signature"), _matched_sig()]}}


def _shared_fixed_matched():
    return {"type": "FixedCount", "pattern": _pair_lgg_matched(), "wild": WILD}


def _transform_key():
    """The systematicity key, DERIVED IN-RULE from the pair's own shared shape:
    the canonical JSON of the lgg (AntiUnify template) of source and its best
    partner. Two probes whose pairs share the IDENTICAL lgg are aligned on the
    same axes in the same way — the two corner-pairs of one parallelogram (the
    concept-grain analogue of analogical_thinking._canon_transform's residue
    key). ToJsonString is an existing Term — still zero new Rust."""
    return {"type": "ToJsonString", "value": _pair_lgg_matched()}


MATCH = [["ag", OBSERVED_EDGE, "obs"]]
STATUS = lambda v: eq(attr("obs", "status"), lit(v))          # noqa: E731

# A probe found a partner sharing >=1 structural axis — the MAC survivor.
# best_count is the shared-structure count of its best partner; > 0 means a
# genuine shared shape (not merely a name/definition-token coincidence, which
# does not survive AntiUnify unless the VALUE is identical too).
COVERED = gt(attr("obs", "best_count"), lit(0))

# The systematicity bucket: how many OTHER matched probes realise this probe's
# transform_key. > 0 ⇒ corroborated ⇒ the parallelogram fired. The exact
# recurrence-by-key idiom ps_mint uses, over the matched probe population. The
# empty-transform_key guard keeps probes that found no real shared shape (key
# = the lgg of nothing) from grouping into a spurious parallelogram.
_systematic_group = filter_(
    nodes_of_type(PROBE), "y",
    and_(ne(var("y"), var("obs")),
         ne(attr("obs", "transform_key"), lit("")),
         eq(attr("y", "transform_key"), attr("obs", "transform_key")),
         or_(eq(attr("y", "status"), lit("matched")),
             eq(attr("y", "status"), lit("aligned")),
             eq(attr("y", "status"), lit("emitted")))))
CORROBORATION = count(_systematic_group)

RULES = [
    # ---------------- rung 1 : the cross-field nearest-neighbour scan -----
    dict(
        name="ap_decode",
        comment=(
            "RUNG 1, THE CROSS-FIELD SCAN: a pending AnalogyProbe finds its "
            "best structural PARTNER among the target field(s) — Argmax over "
            "the scoped ConceptShape parts of FixedCount(AntiUnify(source.sig, "
            "part.sig)), the DERIVED shared-structure specificity. This is the "
            "scan that used to be a Python triple-nested loop (SHAPE_AUDIT.md "
            "§2.4), now a graph verdict over WHATEVER structure the concept "
            "signature carries — relational edges when the concept has them, "
            "attrs + vocabulary axes otherwise. 'Arbitrary shapes across "
            "fields', not a five-order string-token dial. covered_by is the "
            "best partner's field::name; best_count is its shared-structure "
            "count (the positive-evidence guard). The candidate set is scoped "
            "by In(part.name, obs.scope) to the target field(s) minus the "
            "probe's own part — cross-field and no-self by construction."),
        match_type=PROBE, match=MATCH,
        where=STATUS("pending"),
        effects=[
            ["set_attr", "obs", "covered_by",
             T({"type": "Attr", "key": "name", "node": _best_partner()})],
            ["set_attr", "obs", "best_count", T(_best_count())],
            ["set_attr", "obs", "decoded_epoch", T(attr("ag", EPOCH_ATTR))],
            ["set_attr", "obs", "status", "decoded"],
        ],
    ),
    # ---------------- the MAC survivor / no-match ------------------------
    dict(
        name="ap_no_match",
        comment=(
            "THE HONEST NON-ANSWER: a decoded probe whose best partner shares "
            "NO structural axis (best_count == 0 / no partner). No shared "
            "shape ⇒ no analogy. Terminal, distinct from a real match so the "
            "non-answer is inspectable in the graph."),
        match_type=PROBE, match=MATCH,
        where=and_(STATUS("decoded"), not_(COVERED)),
        effects=[["set_attr", "obs", "status", "no_match"]],
    ),
    dict(
        name="ap_match",
        comment=(
            "MAC SURVIVOR → the shared structure, DERIVED. A decoded probe "
            "that covered >=1 relation of some target concept records: "
            "struct_shared = FixedCount(AntiUnify(probe.sig, matched.sig)) — "
            "the same specificity metric sd_recognize/ps_recognize use, "
            "computed by Rust, never an asserted ordinal — and transform_key = "
            "ToJsonString(AntiUnify(probe.sig, matched.sig)), the canonical "
            "shared-shape key derived IN-RULE from the decode's own result "
            "(the shim never guesses a target it does not yet know). "
            "transform_key is the systematicity bucket ap_systematic groups "
            "on. Both read the matched target (name == covered_by) via one "
            "Argmax that binds `mt`."),
        match_type=PROBE, match=MATCH,
        where=and_(STATUS("decoded"), COVERED),
        effects=[
            ["set_attr", "obs", "struct_shared", T(_shared_fixed_matched())],
            ["set_attr", "obs", "transform_key", T(_transform_key())],
            ["set_attr", "obs", "status", "matched"],
        ],
    ),
    # ---------------- systematicity : the parallelogram -------------------
    dict(
        name="ap_systematic",
        comment=(
            "SYSTEMATICITY / THE PARALLELOGRAM, as a graph verdict. Two matched "
            "probes that realise the SAME transform_key differ from one another "
            "in exactly the same places by exactly the same amounts: they are "
            "the two corner-pairs of one parallelogram and each corroborates "
            "the other — Gentner's systematicity COMPUTED, not asserted, and "
            "the only quantity here no per-pair scorer can produce. This is the "
            "Count(Filter(... Eq(transform_key))) recurrence idiom ps_mint uses "
            "one grain over. corroboration is stamped on the probe so ap_emit "
            "and the shim can read the basis for the verdict."),
        match_type=PROBE, match=MATCH,
        where=and_(STATUS("matched"), gt(CORROBORATION, lit(0))),
        effects=[
            ["set_attr", "obs", "corroboration", T(CORROBORATION)],
            ["set_attr", "obs", "status", "aligned"],
        ],
    ),
    dict(
        name="ap_align_struct",
        comment=(
            "ALIGNED BY STRUCTURE ALONE: a matched probe whose anti-unify "
            "template fixes >=1 real axis (struct_shared > 0) is a genuine "
            "structural correspondence even without a second corroborating "
            "pair — the ALIGNED half of RULES_AS_SHAPE_DESIGN_SPIKE.md §4.2's "
            "filter. corroboration stays 0 (honestly: none was found), and the "
            "probe advances to `aligned` so ap_emit treats it identically to a "
            "corroborated one. A matched probe that is NEITHER aligned NOR "
            "corroborated stays `matched` and is NEVER emitted — surface "
            "coincidence reported as nothing, which is the point."),
        match_type=PROBE, match=MATCH,
        where=and_(STATUS("matched"), gt(attr("obs", "struct_shared"), lit(0)),
                   not_(gt(CORROBORATION, lit(0)))),
        effects=[
            ["set_attr", "obs", "corroboration", 0],
            ["set_attr", "obs", "status", "aligned"],
        ],
    ),
    # ---------------- the verdict : emit the Analogy ----------------------
    dict(
        name="ap_emit",
        comment=(
            "THE VERDICT. An aligned probe (structurally aligned OR corroborated "
            "by the parallelogram) becomes an Analogy node carrying the source "
            "and matched target concepts, the DERIVED struct_shared and "
            "corroboration, and an `implements` edge asserting the structural "
            "correspondence — written ONLY here, ONLY when structure was "
            "actually computed and positive (contrast SHAPE_AUDIT.md §2.4's "
            "hand-set `order_n >= 2` ordinal). Mint-once guarded by the "
            "already-emitted edge."),
        match_type=PROBE, match=MATCH,
        where=and_(STATUS("aligned"),
                   eq(count(nbrs("obs", "emitted_analogy")), lit(0))),
        effects=[
            ["add_node", "an", "Analogy", {
                "source_concept": T(attr("obs", "source_concept")),
                # The matched target is ShapeDecode's DERIVED covered_by — the
                # "field::name" part name of the concept this probe aligned to.
                # The shim strips the "field::" prefix on read-back (the field
                # is also carried explicitly as target_field). It cannot be a
                # preset attr: which target a source aligns to is DECIDED by the
                # decode, not known at ingest.
                "target_concept": T(attr("obs", "covered_by")),
                "source_mt": T(attr("obs", "source_field")),
                "target_mt": T(attr("obs", "target_field")),
                "struct_shared": T(attr("obs", "struct_shared")),
                "corroboration": T(attr("obs", "corroboration")),
                "covered_count": T(attr("obs", "best_count")),
                "transform_key": T(attr("obs", "transform_key")),
                "source": "analogy_search",
            }],
            ["add_edge", "obs", "emitted_analogy", "an"],
            ["set_attr", "obs", "status", "emitted"],
        ],
    ),
    # ---------------- re-decode : the loop closes -------------------------
    dict(
        name="ap_redecode",
        comment=(
            "CODEBOOK GROWTH CLOSES THE LOOP: a caller that adds fields or "
            "concepts to the ConceptShape codebook and bumps "
            "analogy_codebook_epoch re-arms any probe last decoded under an "
            "older epoch back to pending, so ap_decode re-runs it against the "
            "GROWN codebook — decode → match → systematicity → emit, driven by "
            "the run_rules fixpoint with no Python iteration anywhere. Mirrors "
            "sd_redecode / msg_redecode / ps_redecode exactly."),
        match_type=PROBE, match=MATCH,
        where=and_(
            or_(*[STATUS(s) for s in
                  ("decoded", "matched", "aligned", "emitted", "no_match")]),
            lt(attr("obs", "decoded_epoch"), attr("ag", EPOCH_ATTR))),
        effects=[
            ["set_attr", "obs", "status", "pending"],
            ["set_attr", "obs", "decoded_epoch", T(attr("ag", EPOCH_ATTR))],
        ],
    ),
]

MANIFEST = {
    "id": "analogy_search",
    "version": "1.0.0",
    "depends_on": ["shape_vocabulary"],
    "description": (
        "THE ANALOGY SEARCH AS A FIRST-CLASS GRAPH SEED — SHAPE_AUDIT.md §2.4. "
        "domains/analogical_thinking.py::find_analogies was 'never moved into "
        "the graph': a Python triple-nested loop over concept pairs scoring a "
        "set overlap of string tokens at five fixed orders, 'not one of which "
        "consults a concept's edges'. This seed makes the search a run_rules "
        "fixpoint one grain over from seeds/meta_shape_growth.json / "
        "problem_shape_growth.json, with ZERO new Rust (every decision is an "
        "existing generic Term, the same choice problem_shape_growth made): "
        "ap_decode runs the UNCHANGED ShapeDecode Term over a per-field-scoped "
        "ConceptShape codebook (the cross-field scan, in Rust, over ARBITRARY "
        "concept structure — relational edges when present, attrs + vocabulary "
        "axes otherwise); ap_match derives shared structure via "
        "FixedCount(AntiUnify(...)); ap_systematic fires the parallelogram as "
        "a Count(Filter(Eq(transform_key))) recurrence verdict; ap_emit writes "
        "an Analogy node + implements edge ONLY when aligned or corroborated. "
        "Emitted by tools/build_analogy_search_seed.py. Ingest: "
        "domains/analogy_search.observe."),
    "microtheory": {
        "name": "analogy_search",
        "description": ("the analogy search decodes each source concept against "
                        "other fields' concept shapes and grows analogies on "
                        "aligned or corroborated structure; tick-driven, no "
                        "Python loop"),
    },
    "nodes": [],
    "edges": [],
    # Γ PRODUCTIONS, DECLARED — CLAUDE.md "SHAPES, NOT NUMBERS": every edge type
    # these rules mint or match on is declared, so the admissibility grammar
    # generates the allowed moves instead of the checker being bypassed.
    "productions": [
        {"provenance": "analogy_search:observed_probe",
         "src": {"type": "Agent", "var": "ag"},
         "edge_type": OBSERVED_EDGE,
         "tgt": {"type": PROBE, "var": "obs"}},
        {"provenance": "analogy_search:emitted_analogy",
         "src": {"type": PROBE, "var": "obs"},
         "edge_type": "emitted_analogy",
         "tgt": {"type": "Analogy", "var": "an"}},
        # The `implements` edge the emitted Analogy asserts between the two real
        # Concept nodes is written by the SHIM (it holds the two node ids), not
        # by a rule — the same split reflective_faculty / analogical_thinking
        # already use for correspondence persistence, so no Concept-typed
        # production is declared here (the rule layer never touches Concepts).
    ],
    "rules": RULES,
}

if __name__ == "__main__":
    with open(OUT, "w") as f:
        json.dump(MANIFEST, f, indent=1)
        f.write("\n")
    print(f"wrote {OUT} ({len(RULES)} rules)")
