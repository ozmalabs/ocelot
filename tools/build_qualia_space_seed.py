#!/usr/bin/env python3
"""Emit `seeds/qualia_space.json` — THE SCHEMA OF QUALIA SPACE.

The creator's directive: "what are the edge and shape of things — is the
current representation useful — effectively we want to create a schema of Qualia
space", and "humans don't have two qualia spaces — 'I'm not sure how I feel
about this' doesn't mean that at all. Implementing a genuine thought and
consciousness model is the goal."

ONE SPACE, NOT TWO. The old `analogy_search.concept_signature` flattened a
concept into an undifferentiated bag of `(predicate, value)` relations — no
schema, every axis the same kind of thing. This seed gives the space a
principled DIMENSIONAL structure: a `QualiaDimension` codebook whose entries are
the typed AXES a concept's meaning is organised along. A concept's signature
becomes its COORDINATES on whichever dimensions are evidenced — its shape in
qualia space.

Crucially the lexical-conceptual axes (what a thing IS/is-made-of/is-for/comes-
from) and the phenomenal-dynamical axes (what it is LIKE right now / standingly)
are AXES OF ONE SPACE, not two spaces. This is not a stipulation — the substrate
already runs it: an emotion, a regard, an arousal, the agent's own self-worth
are all `Concept` nodes carrying `state`/`external_field`/`identity_field`,
relaxed by the SAME continuous-attractor dynamics (`can_ops.rs`,
`can_self_worth_bridge.py`) as any concept the agent reasons about. Felt state
and object of thought are the same node type in the same field. This seed makes
that explicit.

THREE DIMENSION FAMILIES:

  lexical    — Pustejovsky's Generative-Lexicon qualia roles, the typed
               structure of what a concept IS. Already half-present in the tree
               (`frame_harvest.py::_QUALIA_BY_PAIR`, `seeds/metonymy_patterns
               .json::qualia_role`): FORMAL (what kind), CONSTITUTIVE (parts /
               material), TELIC (function / purpose), AGENTIVE (origin / how it
               comes about). SEEDED here — a stable backbone.

  dynamical  — the CAN field coordinates, the proto-phenomenal "what it is like".
               Read straight off the same `state`/`external_field`/
               `identity_field` attrs the engine already relaxes:
                 · valence     = sign of committed state       (−/0/+)
                 · commitment  = identity_field, quantized      (the CRYSTALLISED
                                 axis — "long-standing structural commitment...
                                 survives h-decay", can_ops.rs)
                 · pull        = external_field, quantized       (the LIVE OVERLAY
                                 — "time-varying... decay reduces this over time",
                                 read only in the overlay signature)
                 · activation  = current state magnitude          (live)
               `h_eff = external + identity` (can_ops.rs) is exactly why these
               are ONE space with the lexical axes and why the split between the
               crystallised signature (commitment/valence) and the live overlay
               (pull/activation) is the engine's own, not an imposition. The GAP
               between them — commitment≈0 while pull≠0 — is "I'm not sure how I
               feel about this": an UNSETTLED POINT, not a missing reading.
               SEEDED here.

  phenomenal — the felt axes beyond the raw CAN coordinates (modality, and
               whatever else the agent comes to distinguish). DELIBERATELY NOT
               fully seeded: like the sd-loop's CapabilityAxis / LatentDimension,
               new qualia dimensions are MINTED FROM RESIDUAL — structure the
               held axes cannot cover becomes a new axis. Getting the schema
               "right" means NOT pre-cutting it. Only a single bootstrap
               `phenomenal:modality` is seeded so the family exists; the rest is
               grown (a later rung wires the mint ladder, mirroring
               sd_mint_quantum / DimInfer at this grain).

A `QualiaDimension` node carries:
  name       — "lexical:telic", "dynamical:commitment", ...
  family     — "lexical" | "dynamical" | "phenomenal"
  source     — how a concept's coordinate on this axis is READ:
               "edge:<edge_type>"  (a relational qualia role — the edge's target
                                    type is the coordinate; structure-mapping),
               "field:<attr>"      (a CAN field attr, quantized),
               "attr:<attr>"       (a plain attribute value),
               "keyword"           (a shape-vocabulary keyword hit).
  overlay    — 1.0 iff this axis is a LIVE reading (only in the overlay
               signature, not the crystallised one); absent/0.0 = crystallised.
  quantum / half_width — for a `field:` axis, the _round_to_vocab lattice
               (k = round(x/quantum), clamped to ±half_width) so a continuous
               field becomes a discrete coordinate AntiUnify can intersect. The
               same in-frame-integer-k scheme the CAN tests use
               (tests/test_can_identity_feedback.py etc.: coarse 1.0/1,
               fine 0.25/4).
  seeded     — 1.0 for the backbone; a minted axis carries minted=1.0 instead.

The EDGE-ROLE MAP wires common relational edge types to their lexical qualia
role, so a concept's `has_part`/`causes`/`used_for` edges land on the right
axis (CONSTITUTIVE / AGENTIVE / TELIC) instead of the flat bag. Grounded in
`frame_harvest._QUALIA_BY_PAIR` (person•work=AGENTIVE, whole•part=CONSTITUTIVE,
artifact•function=TELIC).

Run: python3 tools/build_qualia_space_seed.py
"""
from __future__ import annotations

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "seeds", "qualia_space.json")


def _dim(name, family, source, *, overlay=False, quantum=None,
         half_width=None, gloss=""):
    attrs = {"name": name, "family": family, "source": source,
             "seeded": 1.0, "gloss": gloss}
    if overlay:
        attrs["overlay"] = 1.0
    if quantum is not None:
        attrs["quantum"] = float(quantum)
        attrs["half_width"] = float(half_width)
    return {"type": "QualiaDimension", "attrs": attrs}


# --- LEXICAL: Pustejovsky's qualia roles (the typed structure of what a
#     concept IS). The `source` names the edge families that evidence each role;
#     the signature builder maps a concept's actual edges onto these axes. ----
_LEXICAL = [
    _dim("lexical:formal", "lexical", "attr:category",
         gloss="FORMAL — what KIND of thing it is (its taxonomic type / "
               "is_a / category). Distinguishes it within a larger domain."),
    _dim("lexical:constitutive", "lexical", "edge:has_part,part_of,made_of,"
         "constitutes,contains,member_of",
         gloss="CONSTITUTIVE — what it is MADE OF / its parts / material / "
               "the whole it belongs to (whole•part, container•content)."),
    _dim("lexical:telic", "lexical", "edge:used_for,enables,serves,regulates,"
         "gates,controls,produces,for",
         gloss="TELIC — what it is FOR: its function, purpose, the role it "
               "plays (artifact•function)."),
    _dim("lexical:agentive", "lexical", "edge:causes,caused_by,creates,"
         "created_by,mints,derived_from,excites,inhibits,activates,suppresses",
         gloss="AGENTIVE — how it COMES ABOUT: its origin, what brings it into "
               "being or drives it (creator•creation, cause•effect)."),
]

# --- DYNAMICAL: the CAN field coordinates. The proto-phenomenal "what it is
#     like". Read off state/external_field/identity_field, quantized to the
#     CAN tests' own lattice. valence+commitment are CRYSTALLISED (in the
#     standing signature); pull+activation are LIVE (overlay only). ----------
_DYNAMICAL = [
    _dim("dynamical:valence", "dynamical", "field:state",
         quantum=1.0, half_width=1,
         gloss="VALENCE — sign of the concept's committed state (−/0/+). The "
               "coarsest felt axis: is this, standingly, a negative, neutral, "
               "or positive thing to the agent. Crystallised."),
    _dim("dynamical:commitment", "dynamical", "field:identity_field",
         quantum=0.25, half_width=4,
         gloss="COMMITMENT — the identity_field: the long-standing structural "
               "commitment that resists perturbation and survives decay "
               "(can_ops.rs). The CRYSTALLISED axis — how settled the agent's "
               "feeling about this has become. Experience turned to character."),
    _dim("dynamical:pull", "dynamical", "field:external_field", overlay=True,
         quantum=0.25, half_width=4,
         gloss="PULL — the external_field: the LIVE, time-varying evidence "
               "pulling on the concept right now, which decays (can_ops.rs). "
               "OVERLAY only — how the agent feels about this AT THIS MOMENT, "
               "before it settles. The gap between pull and commitment is "
               "'I'm not sure how I feel about this.'"),
    _dim("dynamical:activation", "dynamical", "field:state", overlay=True,
         quantum=0.25, half_width=4,
         gloss="ACTIVATION — the current state magnitude, live. How active / "
               "engaged the concept is in the agent's present processing. "
               "OVERLAY only."),
    _dim("dynamical:disposition", "dynamical", "field:disposition_field",
         quantum=1.0, half_width=4,
         gloss="DISPOSITION — the agent's COGNITIVE DISPOSITION as a felt, "
               "CAN-relaxable trait: its standing willingness to mint referents "
               "/ form associations, conservative (−) ↔ permissive (+). A REAL "
               "dynamical qualia axis on the AGENT (domains/disposition.py), the "
               "structural TWIN of self-worth (can_self_worth_bridge.py): a felt "
               "scalar on a resident CAN Concept, SEEDED with a starting "
               "temperament but PRODUCED/moved by the SAME "
               "can_native_identity_field_feedback dynamics as any other "
               "crystallised feeling. `disposition_field` is the crystallised "
               "STANDING trait — a mechanical mirror of the `identity_field` the "
               "native rule steps toward the sign of sustained disposition "
               "evidence (never hand-written mid-drive; the mirror copies what "
               "the relaxation produced).\n"
               "GRANULARITY (honest, measured — scripts/qualia_disposition_demo.py): "
               "UNLIKE dynamical:commitment (which SATURATES to {−4,0,+4} because "
               "quantum=0.25 clamps identity_field's very first ±1 step to ±4), "
               "disposition has quantum=1.0 = the field's OWN integer step size. "
               "can_native_identity_field_feedback moves identity_field by "
               "exactly ±1 per strictly-later tick (verified: sustained +σ gives "
               "identity_field 1,2,3,4,5,…), so quantum=1.0/half_width=4 renders "
               "identity_field=1→k=1, 2→2, 3→3, 4→4 and only CLAMPS at ≥5. That "
               "is a GENUINELY GRADED 9-level axis (−4…+4): the seeded starting "
               "temperaments (e.g. −2 conservative, 0 neutral, +2 open) read as "
               "distinct coordinates, and sustained evidence walks the level up/"
               "down one step at a time. The underlying field DOES take those "
               "graded integer values under the dynamics — the spread is real, "
               "not a quantiser illusion. (A wider magnitude would still be "
               "bounded by the ±1-per-tick step the rule uses for Lyapunov "
               "stability; the levels are the field's own, honestly reported.)"),
    _dim("dynamical:disposition_pull", "dynamical", "field:disposition_external",
         overlay=True, quantum=1.0, half_width=4,
         gloss="DISPOSITION_PULL — the LIVE, momentary openness pulling on the "
               "agent's disposition right now (the external_field of the "
               "disposition Concept, mirrored to `disposition_external`), before "
               "it settles into the standing trait. OVERLAY only — mirrors the "
               "valence(crystallised)/pull(overlay) split: the GAP between "
               "disposition_pull and disposition is 'I am being pulled toward "
               "opening up right now but my standing temperament has not moved.' "
               "quantum=1.0/half_width=4 as for the crystallised axis, so a live "
               "pull and a standing trait at the same level read as the same "
               "coordinate."),
]

# --- TRAIT VECTOR (the personality generalisation) ------------------------- #
# The single `disposition` axis above is now the `openness` component of a
# VECTOR of cognitive-style traits (domains/disposition.TRAIT_REGISTRY). Each
# extra trait is its OWN CAN-produced/crystallising/seeded axis on its OWN
# distribution, sharing the SAME machinery — so adding a trait is adding a ROW
# here (+ a registry entry), not new code. The axes are DATA-DRIVEN from the
# same table the runtime reads.
#
# `openness` == the old disposition and is ALREADY emitted above (with its full
# curated gloss + the back-compat axis name `dynamical:disposition`), so it is
# EXCLUDED here to avoid a duplicate. The remaining traits emit here.
#
# Each trait emits a CRYSTALLISED `dynamical:<trait>` (source
# `field:<trait>_field`) and a LIVE overlay `dynamical:<trait>_pull` (source
# `field:<trait>_external`), both quantum=1.0/half_width=4 — the graded 9-level
# scheme disposition proved (the field marches in integer ±1 steps, so each
# integer level is a distinct coordinate, not a saturating one).
#
# The rows mirror domains/disposition.TRAIT_REGISTRY. The builder keeps its own
# copy (rather than importing the runtime module) so the seed is buildable
# stand-alone; the runtime and this table are kept in lock-step by the
# tests/test_trait_vector back-compat gates.
_TRAIT_AXES = [
    # (trait, axis, field_attr, external_attr, gloss)
    ("abstraction", "dynamical:abstraction",
     "abstraction_field", "abstraction_external",
     "ABSTRACTION — the agent's standing pull toward high-order, structural "
     "mappings: concrete/surface (−) ↔ abstract/deep (+). A component of the "
     "cognitive-style VECTOR (domains/disposition.TRAIT_REGISTRY), its OWN "
     "CAN Concept in the agent_disposition Mt, PRODUCED/moved by the same "
     "can_native_identity_field_feedback dynamics as openness but INDEPENDENT "
     "of it (a separate Concept, its own field). Seeded NEUTRAL (0.0) and INERT "
     "in layer 1 (no consumer); layer 2 wires it to analogy order_n. "
     "quantum=1.0/half_width=4 — the graded 9-level scheme."),
    ("skepticism", "dynamical:skepticism",
     "skepticism_field", "skepticism_external",
     "SKEPTICISM — the agent's standing demand for evidence before accepting a "
     "correspondence: credulous (−) ↔ skeptical (+). A component of the "
     "cognitive-style VECTOR, its OWN CAN Concept in the agent_disposition Mt, "
     "PRODUCED/moved by the same identity-feedback dynamics but INDEPENDENT of "
     "openness and abstraction. Seeded NEUTRAL (0.0) and INERT in layer 1 (no "
     "consumer); layer 2 wires it to analogy min_score/recurrence. "
     "quantum=1.0/half_width=4 — the graded 9-level scheme."),
]

for _trait, _axis, _field, _ext, _gloss in _TRAIT_AXES:
    _DYNAMICAL.append(_dim(_axis, "dynamical", f"field:{_field}",
                           quantum=1.0, half_width=4, gloss=_gloss))
    _DYNAMICAL.append(_dim(_axis + "_pull", "dynamical", f"field:{_ext}",
                           overlay=True, quantum=1.0, half_width=4,
                           gloss=f"{_axis.split(':')[1].upper()}_PULL — the LIVE, "
                           "momentary pull on this trait right now (the "
                           f"external_field of the trait Concept, mirrored to "
                           f"`{_ext}`), before it settles into the standing "
                           "trait. OVERLAY only — the gap between the live pull "
                           "and the standing trait is 'I'm being pulled but my "
                           "temperament has not moved.' quantum=1.0/half_width=4 "
                           "as for the crystallised axis."))

# --- PHENOMENAL: felt axes beyond the raw CAN coordinates. DELIBERATELY only a
#     single bootstrap axis is seeded — the rest are MINTED from residual (the
#     sd_mint_quantum / DimInfer discipline), so the schema of qualia space is
#     GROWN, not pre-cut. "Getting it right means not pre-cutting it." ---------
_PHENOMENAL = [
    _dim("phenomenal:modality", "phenomenal", "keyword",
         gloss="MODALITY — the sensory/affective register a felt concept "
               "belongs to (visual, somatic, emotional, cognitive...). "
               "BOOTSTRAP only: the phenomenal family exists so minted axes "
               "have a home, but its members are grown from residual, never "
               "hand-enumerated (contrast the closed lexical backbone)."),
]

NODES = _LEXICAL + _DYNAMICAL + _PHENOMENAL

# The EDGE-ROLE MAP as graph data: which lexical qualia role a given outgoing
# edge type evidences. A DimensionEdgeRole node per (edge_type -> dimension), so
# the signature builder reads the mapping off the graph (extensible: teaching a
# new edge type its role is adding a node, not editing Python). Grounded in
# frame_harvest._QUALIA_BY_PAIR.
_EDGE_ROLE = {
    # constitutive — what it is MADE OF / its parts / material
    "has_part": "lexical:constitutive", "part_of": "lexical:constitutive",
    "made_of": "lexical:constitutive", "constitutes": "lexical:constitutive",
    "contains": "lexical:constitutive", "member_of": "lexical:constitutive",
    "composed_of": "lexical:constitutive",
    # telic — what it is FOR: function, purpose, role
    "used_for": "lexical:telic", "enables": "lexical:telic",
    "serves": "lexical:telic", "regulates": "lexical:telic",
    "gates": "lexical:telic", "controls": "lexical:telic",
    "produces": "lexical:telic", "grounds": "lexical:telic",
    # agentive — how it COMES ABOUT: origin, cause, what drives it
    "causes": "lexical:agentive", "caused_by": "lexical:agentive",
    "creates": "lexical:agentive", "created_by": "lexical:agentive",
    "derived_from": "lexical:agentive", "excites": "lexical:agentive",
    "inhibits": "lexical:agentive", "activates": "lexical:agentive",
    "suppresses": "lexical:agentive", "causal_influence": "lexical:agentive",
    "depends_on": "lexical:agentive",
    # FORMAL — the taxonomic backbone. `built_from`/`genls`/`is_a`/`kind_of`/
    # `subtype_of` are the is-a hypernymy edges the REAL booted corpus uses
    # (grounded_representation.GROUNDING_EDGE_TYPES, lexical_ontology_roots.json
    # — the WordNet unique-beginner tree). These are a concept's KIND, so they
    # land on lexical:formal, the same axis `category` does. Without this the
    # dominant real concept edges fell through to untyped `relational:` and the
    # existing Cyc-style taxonomy was invisible to the qualia signature.
    "built_from": "lexical:formal", "genls": "lexical:formal",
    "is_a": "lexical:formal", "kind_of": "lexical:formal",
    "subtype_of": "lexical:formal", "instance_of": "lexical:formal",
    "isa": "lexical:formal",
    # exhibits — a concept SHOWING a property/behaviour is a telic/functional
    # reading (what it does), the closest honest role.
    "exhibits": "lexical:telic",
}

for et, dim in sorted(_EDGE_ROLE.items()):
    NODES.append({"type": "DimensionEdgeRole",
                  "attrs": {"edge_type": et, "dimension": dim, "seeded": 1.0}})

# --- THE SCHEMA DESCRIPTOR — the space's EDGES and SHAPE, made checkable. --- #
# A single `QualiaSchema` node carrying (as JSON strings, since node attrs are
# scalars) the declared value-DOMAIN of each coordinate FAMILY and the INVARIANTS
# every built space must hold. This is what `domains/qualia_schema.validate_
# qualia_space` reads off the graph to check a built space conforms — the schema
# lives as graph DATA next to the QualiaDimension/DimensionEdgeRole codebook it
# describes, not as prose (the same choice the edge-role map already made).
#
# A coordinate is a `(dimension, predicate, value)` 3-tuple. The dimension's
# FAMILY (its prefix before ':') fixes the shape of predicate+value:
#
#   lexical:formal      pred ∈ {is_a, category}; value = a lowercase TYPE / category token
#   lexical:<role>      pred = the outgoing EDGE TYPE; value = the target's node TYPE
#                       (structure-mapping — the filler is abstracted to its type)
#   relational:<edge>   an UNTYPED edge axis (edge type carried no seeded role):
#                       pred = edge type; value = target node TYPE. A mint candidate.
#   dynamical:<axis>    pred = "field"; value = an INTEGER step k in [-half_width,
#                       +half_width], k ≠ 0 (a 0 coordinate is the shared default,
#                       omitted). The axis's quantum/half_width are on its
#                       QualiaDimension node.
#   vocab:<kind>        pred = a shape-vocabulary keyword; value = a slot string
#                       ("a|b" or "·"). kind ∈ {role, principle, shape}.
#   attr:<key>          pred = the attr key; value = its stringified value. The
#                       catch-all for plain content (name/definition/…), MINUS the
#                       reserved field attrs (below) and CAN bookkeeping.
#
# The families are CLOSED for the structured axes (lexical/dynamical/vocab) and
# OPEN for attr:/relational: (the honestly-untyped residue) and phenomenal:
# (grown by minting). "Closed" means a coordinate on that family must name a
# declared dimension; "open" means any dimension of that prefix is admissible.
_SCHEMA_FAMILIES = {
    # family-prefix -> {closed, predicates, value_kind, gloss}
    "lexical": {
        "closed": True,
        "predicates": ["is_a", "category", "<edge_type>"],
        "value_kind": "token",   # a lowercase type / category / target-type token
        "gloss": "Pustejovsky qualia roles — the typed structure of what a "
                 "concept IS. formal via type+category; constitutive/telic/"
                 "agentive via edges typed by the DimensionEdgeRole map. Value "
                 "is a lowercase token (a type or category name); for a role "
                 "axis it is the TARGET'S TYPE (structure-mapping, filler "
                 "abstracted).",
    },
    "dynamical": {
        "closed": True,
        "predicates": ["field"],
        "value_kind": "int_step",   # integer k in [-half_width, half_width], k != 0
        "gloss": "CAN field coordinates — the proto-phenomenal 'what it is "
                 "like', read off state/external_field/identity_field (and the "
                 "mirrored trait fields), quantised to an integer step. "
                 "Crystallised axes stand in the signature; overlay axes appear "
                 "only in the live reading.",
    },
    "vocab": {
        "closed": True,
        "kinds": ["role", "principle", "shape"],
        "predicates": ["<keyword>"],
        "value_kind": "slot_string",   # "a|b" joined sorted slots, or "·"
        "gloss": "Shape-vocabulary keyword hits — the bootstrap that keeps the "
                 "edge-poor booted corpus matchable. Weaker evidence than a "
                 "typed edge, honestly labelled on its own vocab:<kind> axis. "
                 "The KIND (role|principle|shape) is the closed set; the "
                 "keyword predicate is open (any shape-vocabulary term). A "
                 "vocab:<kind> axis is NOT a QualiaDimension codebook node — it "
                 "is produced by keyword matching against seeds/shape_"
                 "vocabulary.json, so it is validated by KIND, not by codebook "
                 "membership.",
    },
    "relational": {
        "closed": False,
        "predicates": ["<edge_type>"],
        "value_kind": "token",
        "gloss": "An outgoing edge whose type carries NO seeded lexical role — "
                 "still matched, honestly untyped. A candidate for minting into a "
                 "real qualia role. OPEN: any relational:<edge> is admissible.",
    },
    "attr": {
        "closed": False,
        "predicates": ["<attr_key>"],
        "value_kind": "token",
        "gloss": "The catch-all for plain content attributes (name/definition/…) "
                 "minus the reserved dynamical field attrs and the CAN mechanism "
                 "bookkeeping. OPEN: any attr:<key> is admissible.",
    },
    "phenomenal": {
        "closed": False,
        "predicates": ["keyword"],
        "value_kind": "token",
        "gloss": "Felt axes beyond the raw CAN coordinates. GROWN from residual "
                 "(the sd_mint_quantum discipline), never hand-enumerated — so "
                 "OPEN by design. Only a bootstrap phenomenal:modality is seeded.",
    },
}

# The attrs a Concept carries that are NOT `attr:` content: they are read as the
# dynamical axes (the three raw CAN fields + every mirrored trait field), so they
# must never also surface as an attr:* coordinate. Derived from the field: axes'
# own `source` — a single source of truth, not a hand-kept list.
_RESERVED_FIELD_ATTRS = sorted({
    d["attrs"]["source"].split(":", 1)[1]
    for d in _DYNAMICAL
} | {"state", "external_field", "identity_field"})

# The INVARIANTS a built space must hold. Each is (id, checkable-claim, gloss).
# `qualia_schema.validate_qualia_space` turns these into executable checks; they
# are stated here as the schema's own record of what "well-formed" means.
_SCHEMA_INVARIANTS = [
    ("coord_arity",
     "every coordinate is a (dimension, predicate, value) 3-tuple",
     "The signature is a frozenset of 3-tuples; nothing is a bare pair or a "
     "longer tuple. The dimension tag is what makes the space a schema."),
    ("dimension_declared",
     "every coordinate's dimension is either a declared QualiaDimension or an "
     "open-family axis (attr:/relational:/phenomenal:)",
     "A closed-family coordinate (lexical/dynamical/vocab) must name a dimension "
     "in the codebook; an open-family coordinate may name any axis of its "
     "prefix."),
    ("value_in_domain",
     "every coordinate's value lies in its family's declared value domain",
     "A dynamical value is an integer step in [-half_width, half_width]\\{0}; a "
     "lexical/vocab/attr/relational value is a token/slot-string. An out-of-range "
     "dynamical k or a non-integer field value is rejected."),
    ("dynamical_is_produced_not_hand_set",
     "no raw CAN field attr (state/external_field/identity_field/<trait>_field) "
     "appears as an attr:* coordinate",
     "The felt content has ONE home — the quantised dynamical axes. A raw field "
     "leaking in as attr:* would be a non-discriminative duplicate; its absence "
     "is the schema enforcing 'valence/commitment are produced, not hand-set'."),
    ("no_can_bookkeeping",
     "no CAN mechanism counter (identity/evidence ledger, *_tick/*_epoch gate) "
     "appears as an attr:* coordinate",
     "The native rules write per-Concept bookkeeping; it is mechanism, not "
     "qualia content, and is excluded at the signature source."),
    ("overlay_superset_of_crystallised",
     "the overlay signature is a superset of the crystallised one; the axes it "
     "adds are exactly the overlay dynamical axes",
     "h_eff = external + identity read as coordinates: the standing term is in "
     "the crystallised signature, the live term is the overlay. Their GAP is the "
     "unsettled point ('I'm not sure how I feel')."),
    ("dark_when_unrelaxed",
     "a concept with no dynamical field activity carries only non-dynamical "
     "(lexical/vocab/attr) coordinates",
     "A never-relaxed concept is dark on the dynamical axes rather than "
     "trivially matching every other concept at valence 0 — the zero coordinate "
     "is omitted, so absence is meaningful."),
    ("commitment_iff_identity",
     "dynamical:commitment is present in the crystallised signature iff "
     "identity_field rounds to a nonzero step",
     "Commitment is crystallised experience: it appears only once the identity "
     "field has settled away from zero, never before."),
]

_SCHEMA_NODE = {
    "type": "QualiaSchema",
    "attrs": {
        "name": "qualia_space_schema",
        "version": "1.0.0",
        "coord_arity": 3,
        "families": json.dumps(_SCHEMA_FAMILIES, sort_keys=True),
        "reserved_field_attrs": json.dumps(_RESERVED_FIELD_ATTRS),
        "invariants": json.dumps(_SCHEMA_INVARIANTS),
        "gloss": (
            "THE SCHEMA OF QUALIA SPACE, made checkable. Declares the value "
            "DOMAIN of each coordinate family and the INVARIANTS a built space "
            "must hold. A coordinate is (dimension, predicate, value); its "
            "family (prefix before ':') fixes predicate+value shape. Read by "
            "domains/qualia_schema.validate_qualia_space to check a built space "
            "conforms; the QualiaDimension nodes carry the per-axis quantum/"
            "half_width/overlay this descriptor references."),
    },
}
NODES.append(_SCHEMA_NODE)

# Assign sequential local_ids (the seed loader requires one per node).
for i, n in enumerate(NODES, start=1):
    n["local_id"] = i

MANIFEST = {
    "id": "qualia_space",
    "version": "1.0.0",
    "depends_on": ["shape_vocabulary"],
    "description": (
        "THE SCHEMA OF QUALIA SPACE — one typed-dimensional space over "
        "Concepts. A QualiaDimension codebook of typed AXES a concept's "
        "meaning is organised along, in three families: lexical (Pustejovsky "
        "FORMAL/CONSTITUTIVE/TELIC/AGENTIVE — what a concept IS, seeded, the "
        "backbone already half-present in frame_harvest/metonymy_patterns); "
        "dynamical (the CAN field coordinates valence/commitment/pull/"
        "activation read off state/external_field/identity_field — the "
        "proto-phenomenal 'what it is like', crystallised axes IN the "
        "signature + live axes read as an OVERLAY, per h_eff=external+identity "
        "in can_ops.rs); and phenomenal (felt axes beyond the raw fields, only "
        "a bootstrap modality seeded — the rest MINTED from residual like the "
        "sd-loop's CapabilityAxis, so the space is grown not pre-cut). Lexical "
        "and phenomenal are ONE space, not two: the substrate already stores "
        "emotion/regard/self-worth as Concepts in the same CAN field as any "
        "reasoned-about concept. A DimensionEdgeRole map wires edge types to "
        "their lexical role. A QualiaSchema descriptor node declares the value "
        "domain of each coordinate family + the invariants a built space must "
        "hold (checked by domains/qualia_schema.validate_qualia_space). Emitted "
        "by tools/build_qualia_space_seed.py. "
        "Read by domains/analogy_search.concept_signature (dimension-tagged "
        "coordinates); matched per-dimension by seeds/analogy_search.json."),
    "microtheory": {
        "name": "qualia_space",
        "description": ("the typed dimensional space a concept's shape lives "
                        "in; lexical + dynamical + (grown) phenomenal axes, "
                        "one space"),
    },
    "nodes": NODES,
    "edges": [],
    # Γ PRODUCTIONS: this seed is pure codebook DATA (no rules yet — the
    # per-dimension matcher and the mint ladder are later rungs). The
    # dimension/edge-role nodes are freestanding; no edge types are minted here,
    # so productions is empty BY CONTENT, not by omission (contrast the
    # zero-production hazard CLAUDE.md names — there are simply no edges).
    "productions": [],
}

if __name__ == "__main__":
    with open(OUT, "w") as f:
        json.dump(MANIFEST, f, indent=1)
        f.write("\n")
    print(f"wrote {OUT} "
          f"({len(NODES)} nodes: {len(_LEXICAL)} lexical + {len(_DYNAMICAL)} "
          f"dynamical + {len(_PHENOMENAL)} phenomenal + "
          f"{len(_EDGE_ROLE)} edge-role + 1 schema descriptor)")
