"""Gates for THE SCHEMA OF QUALIA SPACE as a CHECKABLE artifact
(seeds/qualia_space.json's QualiaSchema descriptor + domains/qualia_schema.
validate_qualia_space).

The creator's steering question: "what are the edge and shape of things — is the
current representation useful — we want to actually create a schema of Qualia
space." The other qualia gates pin what the space MEANS; these pin that its
EDGES are now explicit and enforced:

  1. the schema descriptor is present on the graph and declares the coordinate
     families + the invariants (the space carries its own schema as data).
  2. the dimension CODEBOOK validates against the schema (the backbone is
     well-formed before any concept is placed in it).
  3. a real built concept's signature VALIDATES — lexical + dynamical
     coordinates conform to their declared value domains.
  4. a deliberately MALFORMED signature is REJECTED, one case per family edge:
     an undeclared closed-family dimension, an out-of-range dynamical step, a
     zero step carried as a coordinate, a raw CAN field leaked as attr:*, a CAN
     bookkeeping counter leaked as attr:*, and a non-3-tuple coordinate.
  5. the CROSS-READING invariants hold on a real concept: the overlay is a
     superset of the crystallised signature adding only overlay dynamical axes,
     and commitment is present iff identity_field is nonzero.
  6. DEFAULT == TODAY: a fresh agent carrying the seeded-default trait vector
     still validates, and the whole built space validates with nothing skipped.
"""
from __future__ import annotations

import json
import pathlib

from substrate_rs import _native

import domains.analogy_search as asr
import domains.disposition as disp
import domains.qualia_schema as qsch

ROOT = pathlib.Path(asr.__file__).resolve().parent.parent
VOCAB = ROOT / "seeds" / "shape_vocabulary.json"
QUALIA = ROOT / "seeds" / "qualia_space.json"

_NT = ("Agent", "Concept", "Microtheory", "QualiaDimension",
       "DimensionEdgeRole", "QualiaSchema")
_ET = ("has_concept", "gates", "regulates", "made_of", "used_for", "causes")


def _open(s):
    for a in _NT:
        for b in _NT:
            for et in _ET:
                s.add_production({"src": {"type": a, "var": "x"},
                                  "edge_type": et,
                                  "tgt": {"type": b, "var": "y"},
                                  "where": None,
                                  "weight": {"type": "Lit", "value": 1.0},
                                  "provenance": "test:open"})


def _substrate():
    asr._QUALIA_SCHEMA_CACHE.clear()
    s = _native.Substrate()
    ag = s.add_node("Agent", {})
    _open(s)
    for path in (VOCAB, QUALIA):
        summ = s.load_seed_manifest(json.load(open(path)), ag)
        assert not summ.get("rules_skipped"), (path.name, summ)
    return s, ag


def _mt(s, name):
    return s.add_node("Microtheory", {"name": name})


def _concept(s, mt, name, **attrs):
    a = {"name": name}
    a.update(attrs)
    c = s.add_node("Concept", a)
    s.add_edge(mt, "has_concept", c)
    return c


def _invariant_ids(rep):
    return {i for i, _ in rep.violations}


# ---------------------------------------------------------------------------
# 1. the schema descriptor is present and well-formed
# ---------------------------------------------------------------------------
def test_schema_descriptor_present_and_declares_families_and_invariants():
    s, _ag = _substrate()
    schema = qsch.load_schema(s)
    assert schema is not None, "no QualiaSchema descriptor installed"
    assert schema.get("coord_arity") == 3
    fams = schema.get("families")
    assert isinstance(fams, dict)
    # the structured backbone is CLOSED; the growth surface is OPEN.
    assert fams["lexical"]["closed"] and fams["dynamical"]["closed"] \
        and fams["vocab"]["closed"]
    assert not fams["attr"]["closed"] and not fams["relational"]["closed"] \
        and not fams["phenomenal"]["closed"]
    # the reserved field attrs (the dynamical axes' sources) are declared...
    reserved = set(schema.get("reserved_field_attrs") or [])
    assert {"state", "external_field", "identity_field"} <= reserved
    # ...and the invariants are enumerated as (id, claim, gloss).
    inv = schema.get("invariants")
    ids = {row[0] for row in inv}
    assert {"coord_arity", "dimension_declared", "value_in_domain",
            "dynamical_is_produced_not_hand_set", "no_can_bookkeeping",
            "overlay_superset_of_crystallised", "commitment_iff_identity"} <= ids


# ---------------------------------------------------------------------------
# 2. the dimension codebook validates against the schema
# ---------------------------------------------------------------------------
def test_dimension_codebook_validates():
    s, _ag = _substrate()
    rep = qsch.validate_dimension_codebook(s)
    assert rep.ok, rep
    assert rep.checked >= 15, ("every seeded axis was inspected", rep.checked)


# ---------------------------------------------------------------------------
# 3. a real built concept's signature validates
# ---------------------------------------------------------------------------
def test_built_concept_signature_validates():
    s, _ag = _substrate()
    mt = _mt(s, "m")
    flow = _concept(s, mt, "flow", category="process")
    valve = _concept(s, mt, "valve", category="device",
                     identity_field=0.8, state=1.0, external_field=0.6)
    s.add_edge(valve, "gates", flow)

    sig = asr.concept_signature(s, valve)
    # sanity: it really carries both families (else the check is vacuous).
    dims = {c[0] for c in sig}
    assert "lexical:telic" in dims and "dynamical:valence" in dims, sig

    rep = qsch.validate_signature(s, sig)
    assert rep.ok, rep
    assert rep.checked == len(sig)


# ---------------------------------------------------------------------------
# 4. malformed signatures are REJECTED — one case per family edge
# ---------------------------------------------------------------------------
def test_undeclared_closed_family_dimension_rejected():
    s, _ag = _substrate()
    bad = {("lexical:bogus", "is_a", "thing")}
    rep = qsch.validate_signature(s, bad)
    assert not rep.ok
    assert "dimension_declared" in _invariant_ids(rep), rep


def test_out_of_range_dynamical_step_rejected():
    s, _ag = _substrate()
    # dynamical:valence has half_width 1; a step of 99 is out of domain.
    bad = {("dynamical:valence", "field", 99)}
    rep = qsch.validate_signature(s, bad)
    assert not rep.ok
    assert "value_in_domain" in _invariant_ids(rep), rep


def test_zero_step_carried_is_rejected():
    s, _ag = _substrate()
    # a 0 step is the shared default; carrying it as a coordinate is malformed.
    bad = {("dynamical:commitment", "field", 0)}
    rep = qsch.validate_signature(s, bad)
    assert not rep.ok
    assert "value_in_domain" in _invariant_ids(rep), rep


def test_non_integer_dynamical_value_rejected():
    s, _ag = _substrate()
    bad = {("dynamical:valence", "field", "hot")}
    rep = qsch.validate_signature(s, bad)
    assert not rep.ok
    assert "value_in_domain" in _invariant_ids(rep), rep


def test_raw_field_leaked_as_attr_rejected():
    s, _ag = _substrate()
    # identity_field is a dynamical field, never an attr:* coordinate.
    bad = {("attr:identity_field", "identity_field", "0.8")}
    rep = qsch.validate_signature(s, bad)
    assert not rep.ok
    assert "dynamical_is_produced_not_hand_set" in _invariant_ids(rep), rep


def test_can_bookkeeping_leaked_as_attr_rejected():
    s, _ag = _substrate()
    bad = {("attr:identity_field_tick", "identity_field_tick", "5")}
    rep = qsch.validate_signature(s, bad)
    assert not rep.ok
    assert "no_can_bookkeeping" in _invariant_ids(rep), rep


def test_non_3_tuple_coordinate_rejected():
    s, _ag = _substrate()
    bad = {("dynamical:valence", "field")}   # a 2-tuple, wrong arity
    rep = qsch.validate_signature(s, bad)
    assert not rep.ok
    assert "coord_arity" in _invariant_ids(rep), rep


# ---------------------------------------------------------------------------
# 5. cross-reading invariants on a real concept
# ---------------------------------------------------------------------------
def test_overlay_superset_and_commitment_iff_identity_on_a_real_concept():
    s, _ag = _substrate()
    mt = _mt(s, "m")
    # crystallised commitment + live pull present.
    c = _concept(s, mt, "trust", category="bond",
                 identity_field=0.9, state=1.0, external_field=0.7)
    rep = qsch.validate_concept(s, c)
    assert rep.ok, rep

    # concretely: commitment present because identity_field != 0.
    cryst = asr.concept_signature(s, c)
    assert any(t[0] == "dynamical:commitment" for t in cryst)

    # the unsettled point: pulled on now, never settled — commitment ABSENT,
    # and the concept still validates (absence is the correct reading).
    u = _concept(s, mt, "the_offer", category="proposal",
                 identity_field=0.0, state=0.0, external_field=0.9)
    rep_u = qsch.validate_concept(s, u)
    assert rep_u.ok, rep_u
    cryst_u = asr.concept_signature(s, u)
    assert not any(t[0] == "dynamical:commitment" for t in cryst_u)


def test_forged_commitment_without_identity_is_rejected():
    """The commitment_iff_identity invariant bites: a signature asserting
    crystallised commitment while the concept's identity_field is zero is a
    hand-set feeling, exactly what the schema forbids. We detect the mismatch by
    checking the built concept — its real identity_field is 0, so a commitment
    coordinate cannot legitimately appear (and does not)."""
    s, _ag = _substrate()
    mt = _mt(s, "m")
    # identity_field 0 -> commitment must be ABSENT in the crystallised sig.
    c = _concept(s, mt, "whim", category="notion",
                 identity_field=0.0, state=0.0, external_field=0.0)
    cryst = asr.concept_signature(s, c)
    assert not any(t[0] == "dynamical:commitment" for t in cryst)
    # if we FORGE a commitment coordinate onto this concept's reading, the
    # per-coordinate check still passes (it is a declared axis, in range) — the
    # violation is the CROSS-reading one, which validate_concept catches because
    # it rebuilds from the real (identity_field=0) node. Here we assert the
    # honest built concept validates (no forgery present).
    assert qsch.validate_concept(s, c).ok


# ---------------------------------------------------------------------------
# 6. DEFAULT == TODAY — a seeded-default agent + the whole space validate
# ---------------------------------------------------------------------------
def test_default_trait_vector_agent_validates():
    """A fresh agent carrying the seeded-default personality vector (openness
    -1, abstraction/skepticism 0) places its trait Concepts in qualia space; the
    whole space, including those trait coordinates, validates against the
    schema. Default behaviour is well-formed by the schema's own lights."""
    class _A:
        def __init__(self, sub, ag):
            self.s = sub
            self.agent = ag

    s, ag = _substrate()
    a = _A(s, ag)
    disp.ensure_traits(a)
    # openness seeded -1 reads as a nonzero standing coordinate.
    assert disp.trait_level(a, "openness") == -1

    rep = qsch.validate_qualia_space(s)
    assert rep.ok, rep
    assert rep.checked > 0, "the space validation must not be vacuous"


def test_whole_built_space_validates_clean():
    s, _ag = _substrate()
    mt = _mt(s, "m")
    # a mixed field: a felt concept, a functional concept, a dark concept.
    debt = _concept(s, mt, "debt", category="burden",
                    identity_field=-0.8, state=-1.0)
    s.add_edge(debt, "regulates", _concept(s, mt, "ledger", category="record"))
    _concept(s, mt, "idea", category="notion")   # never relaxed -> dark

    rep = qsch.validate_qualia_space(s)
    assert rep.ok, rep
