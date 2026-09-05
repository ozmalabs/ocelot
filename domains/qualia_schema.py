"""qualia_schema — VALIDATE a built qualia space against its own declared schema.

The creator's steering question: "what are the edge and shape of things — is the
current representation useful — we want to actually create a schema of Qualia
space." `seeds/qualia_space.json` already carries the space's CONTENT (the typed
`QualiaDimension` axes + the `DimensionEdgeRole` map). What it did not carry was
its own EDGES made checkable: the value DOMAIN of each coordinate, and the
INVARIANTS a well-formed space holds. `tools/build_qualia_space_seed.py` now
emits a `QualiaSchema` descriptor node stating exactly those; this module is the
inverse — it reads that descriptor off the graph and checks that a built space,
and any signature drawn from it, conform.

WHAT A COORDINATE IS. A concept's signature (domains/analogy_search.
concept_signature) is a frozenset of `(dimension, predicate, value)` 3-tuples —
its coordinates in qualia space. The dimension's FAMILY (the prefix before ':')
fixes the admissible shape of predicate + value:

  lexical:<role>    a token value (a type/category name, or a role edge's target
                    TYPE — structure-mapping). CLOSED: the axis must be declared.
  dynamical:<axis>  pred "field", value an INTEGER step k in the axis's
                    [-half_width, half_width]\\{0}. CLOSED.
  vocab:<kind>      a shape-vocabulary keyword hit; slot-string value. CLOSED.
  relational:<edge> an untyped edge axis (no seeded role). OPEN — a mint candidate.
  attr:<key>        plain content (name/definition/…). OPEN.
  phenomenal:<x>    felt axes grown by minting. OPEN by design.

"CLOSED" means a coordinate on that family MUST name a declared QualiaDimension;
"OPEN" means any axis of that prefix is admissible (the honestly-untyped residue
+ the grown phenomenal family). This split is the space's real EDGE: the
structured backbone is fixed, the growth surface is left open on purpose.

WHAT THIS MODULE IS NOT. It makes NO decisions about a concept's meaning and
mutates nothing — it is a pure READ + CHECK over the graph, the same posture as
the signature builder it validates. The schema it enforces lives as graph DATA
(the QualiaSchema + QualiaDimension nodes), not in this Python; swapping the
descriptor changes what "well-formed" means without touching this code.

Public surface:
  · load_schema(substrate)                    -> the descriptor as a dict, or None
  · validate_dimension_codebook(substrate)    -> Report over the QualiaDimension nodes
  · validate_signature(substrate, sig)        -> Report over one signature's tuples
  · validate_concept(substrate, node, *, overlay=False) -> build + validate a concept
  · validate_qualia_space(substrate, concepts=None, *, overlay=False) -> whole-space Report

A `Report` is truthy iff `ok` (no violations). Each violation names the invariant
it breaks and the offending coordinate, so a caller (or a test) sees WHY.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Optional

import domains.analogy_search as asr

#: The families whose coordinates MUST name a declared QualiaDimension. The
#: complement (attr/relational/phenomenal) is OPEN — any axis of that prefix is
#: admissible. Read from the descriptor at validate-time; this is the fallback
#: only when a descriptor predates the `closed` flag.
_FALLBACK_CLOSED = frozenset({"lexical", "dynamical", "vocab"})

SCHEMA_NODE_TYPE = "QualiaSchema"


@dataclass
class Report:
    """The result of a validation pass. Truthy iff no violations.

    `violations` is a list of `(invariant_id, message)`; `checked` counts the
    coordinates/dimensions inspected (so a caller can tell a clean pass from a
    vacuous one — a validator that checked nothing is not a validator)."""
    violations: list = field(default_factory=list)
    checked: int = 0

    @property
    def ok(self) -> bool:
        return not self.violations

    def __bool__(self) -> bool:
        return self.ok

    def fail(self, invariant_id: str, message: str) -> None:
        self.violations.append((invariant_id, message))

    def merge(self, other: "Report") -> "Report":
        self.violations.extend(other.violations)
        self.checked += other.checked
        return self

    def __repr__(self) -> str:
        head = "Report(ok)" if self.ok else "Report(%d violation(s))" % len(
            self.violations)
        body = "".join("\n  [%s] %s" % (i, m) for i, m in self.violations)
        return "%s checked=%d%s" % (head, self.checked, body)


def _sub(substrate):
    return getattr(substrate, "s", substrate)


# --------------------------------------------------------------------------- #
# Read the schema descriptor + the dimension codebook off the graph.
# --------------------------------------------------------------------------- #
def load_schema(substrate) -> Optional[dict]:
    """The `QualiaSchema` descriptor as a plain dict, or None when the seed that
    carries it is not installed. Pure read; the JSON-string attrs (families,
    reserved_field_attrs, invariants) are decoded back to structures."""
    sub = _sub(substrate)
    try:
        nodes = list(sub.nodes(SCHEMA_NODE_TYPE))
    except Exception:
        return None
    if not nodes:
        return None
    a = dict(sub.node(nodes[0])["attrs"])
    for k in ("families", "reserved_field_attrs", "invariants"):
        v = a.get(k)
        if isinstance(v, str):
            try:
                a[k] = json.loads(v)
            except Exception:
                a[k] = None
    return a


def _dimension_index(substrate) -> dict:
    """name -> QualiaDimension attrs, for every declared axis. The codebook the
    signature builder also reads (via analogy_search._qualia_schema); read here
    directly so validation does not depend on that cache being warm."""
    sub = _sub(substrate)
    out: dict = {}
    try:
        for n in sub.nodes("QualiaDimension"):
            a = sub.node(n)["attrs"]
            nm = a.get("name")
            if nm:
                out[str(nm)] = a
    except Exception:
        pass
    return out


def _family_of(dimension: str) -> str:
    """The family prefix of a dimension name ('lexical:telic' -> 'lexical')."""
    return str(dimension).split(":", 1)[0]


def _closed_families(schema: dict) -> frozenset:
    fams = (schema or {}).get("families") or {}
    closed = {f for f, spec in fams.items()
              if isinstance(spec, dict) and spec.get("closed")}
    return frozenset(closed) if closed else _FALLBACK_CLOSED


# --------------------------------------------------------------------------- #
# Codebook validation — the DECLARED axes are themselves well-formed.
# --------------------------------------------------------------------------- #
def validate_dimension_codebook(substrate) -> Report:
    """Check the QualiaDimension nodes conform to the schema: every axis names a
    known family, a `field:` axis carries a positive quantum + half_width, and a
    non-field axis does not masquerade as one. This validates the SPACE's own
    backbone before any concept is placed in it."""
    rep = Report()
    schema = load_schema(substrate)
    if schema is None:
        rep.fail("schema_present",
                 "no QualiaSchema descriptor on the graph — is "
                 "seeds/qualia_space.json installed?")
        return rep
    fams = set((schema.get("families") or {}).keys())
    dims = _dimension_index(substrate)
    for name, a in dims.items():
        rep.checked += 1
        fam = str(a.get("family") or "")
        if fam and fam not in fams:
            rep.fail("dimension_declared",
                     "dimension %r has family %r not in the schema families %s"
                     % (name, fam, sorted(fams)))
        src = str(a.get("source") or "")
        if src.startswith("field:"):
            q, hw = a.get("quantum"), a.get("half_width")
            if q is None or float(q) <= 0:
                rep.fail("value_in_domain",
                         "field axis %r has non-positive/absent quantum %r"
                         % (name, q))
            if hw is None or int(hw) <= 0:
                rep.fail("value_in_domain",
                         "field axis %r has non-positive/absent half_width %r"
                         % (name, hw))
    return rep


# --------------------------------------------------------------------------- #
# Per-coordinate validation — the heart of the checker.
# --------------------------------------------------------------------------- #
def _check_coord(coord, schema: dict, dims: dict, reserved: set,
                 closed: frozenset, rep: Report) -> None:
    """Validate ONE `(dimension, predicate, value)` coordinate against the
    schema. Records a violation (never raises) so a Report gathers every problem
    in one pass rather than aborting on the first."""
    # coord_arity — a coordinate is exactly a 3-tuple.
    if not isinstance(coord, (tuple, list)) or len(coord) != 3:
        rep.fail("coord_arity",
                 "coordinate %r is not a (dimension, predicate, value) 3-tuple"
                 % (coord,))
        return
    dim, pred, val = str(coord[0]), str(coord[1]), coord[2]
    fam = _family_of(dim)

    # vocab is CLOSED by KIND, not by codebook membership: a vocab:<kind> axis
    # is produced by shape-vocabulary keyword matching, not declared as a
    # QualiaDimension. Check the kind is in the schema's declared set.
    if fam == "vocab":
        kinds = ((schema.get("families") or {}).get("vocab") or {}).get("kinds")
        kind = dim.split(":", 1)[1] if ":" in dim else ""
        if kinds and kind not in kinds:
            rep.fail("dimension_declared",
                     "vocab coordinate names kind %r not in the declared vocab "
                     "kinds %s (coord %r)" % (kind, kinds, coord))
            return
        if not isinstance(val, str):
            rep.fail("value_in_domain",
                     "vocab coordinate value %r is not a slot string (coord %r)"
                     % (val, coord))
            return
        return

    # dimension_declared — a CLOSED-family coordinate must name a declared axis.
    if fam in closed and dim not in dims:
        rep.fail("dimension_declared",
                 "coordinate on closed family %r names undeclared dimension %r "
                 "(coord %r)" % (fam, dim, coord))
        return

    # dynamical_is_produced_not_hand_set — a raw field attr must never appear as
    # an attr:* coordinate (its home is the quantised dynamical axis).
    if fam == "attr" and pred in reserved:
        rep.fail("dynamical_is_produced_not_hand_set",
                 "raw CAN field %r surfaced as an attr:* coordinate — dynamical "
                 "content must be produced on its dynamical axis, not hand-set "
                 "(coord %r)" % (pred, coord))
        return

    # no_can_bookkeeping — a native mechanism counter must never be an attr:*.
    if fam == "attr" and asr._is_can_bookkeeping_attr(pred.lower()):
        rep.fail("no_can_bookkeeping",
                 "CAN mechanism counter %r surfaced as an attr:* coordinate — "
                 "mechanism, not qualia content (coord %r)" % (pred, coord))
        return

    # value_in_domain — the value shape is fixed by the family.
    if fam == "dynamical":
        # pred is "field"; value is an integer step k in [-hw, hw]\{0}.
        if pred != "field":
            rep.fail("value_in_domain",
                     "dynamical coordinate %r has predicate %r, expected 'field'"
                     % (coord, pred))
            return
        if isinstance(val, bool) or not isinstance(val, int):
            rep.fail("value_in_domain",
                     "dynamical value %r is not an integer step (coord %r)"
                     % (val, coord))
            return
        a = dims.get(dim, {})
        hw = int(a.get("half_width") or 0)
        if hw and not (-hw <= val <= hw):
            rep.fail("value_in_domain",
                     "dynamical step %d out of the axis range [-%d, %d] "
                     "(coord %r)" % (val, hw, hw, coord))
            return
        if val == 0:
            rep.fail("value_in_domain",
                     "dynamical step 0 must be OMITTED (the shared default), not "
                     "carried as a coordinate (coord %r)" % (coord,))
            return
    else:
        # every other family carries a token/slot-string value.
        if not isinstance(val, str):
            rep.fail("value_in_domain",
                     "non-dynamical coordinate value %r is not a string token "
                     "(coord %r)" % (val, coord))
            return


def validate_signature(substrate, signature) -> Report:
    """Validate one signature (a set/frozenset of coordinates) against the
    schema. Checks every coordinate's arity, dimension declaration, value domain,
    and the no-leak invariants. Does NOT check the cross-signature invariants
    (overlay superset, commitment-iff-identity) — those need two signatures; see
    `validate_concept`."""
    rep = Report()
    schema = load_schema(substrate)
    if schema is None:
        rep.fail("schema_present", "no QualiaSchema descriptor on the graph")
        return rep
    dims = _dimension_index(substrate)
    reserved = set(schema.get("reserved_field_attrs") or [])
    closed = _closed_families(schema)
    for coord in (signature or ()):
        rep.checked += 1
        _check_coord(coord, schema, dims, reserved, closed, rep)
    return rep


# --------------------------------------------------------------------------- #
# Concept-level validation — build the signature and check its invariants,
# including the ones that relate the crystallised and overlay readings.
# --------------------------------------------------------------------------- #
def validate_concept(substrate, concept_node, *, overlay: bool = False) -> Report:
    """Build a concept's signature (crystallised, and the overlay too) and
    validate BOTH the per-coordinate schema AND the cross-reading invariants:

      * overlay_superset_of_crystallised — the overlay ⊇ the crystallised set,
        and the axes it adds are exactly overlay dynamical axes;
      * commitment_iff_identity — dynamical:commitment is in the crystallised
        signature iff the concept's identity_field rounds to a nonzero step.

    `overlay` selects which reading is returned as the primary checked signature;
    both are built regardless so the relation between them is checkable."""
    sub = _sub(substrate)
    cryst = asr.concept_signature(sub, concept_node, overlay=False)
    over = asr.concept_signature(sub, concept_node, overlay=True)
    rep = validate_signature(sub, over if overlay else cryst)

    schema = load_schema(sub)
    dims = _dimension_index(sub)

    # overlay_superset_of_crystallised — the live reading only ADDS axes.
    if not (cryst <= over):
        missing = cryst - over
        rep.fail("overlay_superset_of_crystallised",
                 "crystallised coordinates absent from the overlay: %r"
                 % (sorted(missing),))
    added_dims = {c[0] for c in (over - cryst)}
    for d in added_dims:
        a = dims.get(d, {})
        # an axis the overlay ADDS must be an overlay dynamical axis; an added
        # coordinate on a crystallised axis would mean the overlay changed the
        # standing shape, which it must not.
        if not (a.get("overlay") and _family_of(d) == "dynamical"):
            rep.fail("overlay_superset_of_crystallised",
                     "overlay added coordinates on non-overlay axis %r (the "
                     "live reading must only add overlay dynamical axes)" % d)

    # commitment_iff_identity — commitment present iff identity_field != 0-step.
    try:
        attrs = sub.node(concept_node)["attrs"]
    except Exception:
        attrs = {}
    commit_dim = None
    for name, a in dims.items():
        if str(a.get("source")) == "field:identity_field" and not a.get("overlay"):
            commit_dim = name
            break
    if commit_dim is not None:
        a = dims[commit_dim]
        k = asr._round_to_vocab(attrs.get("identity_field"),
                                float(a.get("quantum") or 1.0),
                                int(a.get("half_width") or 1))
        present = any(c[0] == commit_dim for c in cryst)
        if (k is not None) != present:
            rep.fail("commitment_iff_identity",
                     "identity_field rounds to %r but %s in the crystallised "
                     "signature (commitment must be present iff identity is "
                     "nonzero)"
                     % (k, "commitment IS present" if present
                        else "commitment is ABSENT"))
    return rep


def validate_qualia_space(substrate, concepts=None, *,
                          overlay: bool = False) -> Report:
    """Validate a whole built space: the dimension codebook is well-formed, and
    every named concept's signature conforms (per-coordinate + cross-reading
    invariants).

    `concepts` is an iterable of Concept node ids; when None, every `Concept` on
    the graph is checked. Returns one merged `Report` — truthy iff the entire
    space conforms. This is the single entry a caller (or a test) uses to answer
    'is this space well-formed against its own schema?'"""
    sub = _sub(substrate)
    rep = validate_dimension_codebook(sub)
    if concepts is None:
        try:
            concepts = list(sub.nodes("Concept"))
        except Exception:
            concepts = []
    for c in concepts:
        rep.merge(validate_concept(sub, c, overlay=overlay))
    return rep


__all__ = [
    "Report", "SCHEMA_NODE_TYPE",
    "load_schema", "validate_dimension_codebook", "validate_signature",
    "validate_concept", "validate_qualia_space",
]
