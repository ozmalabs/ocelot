"""disposition — the agent's COGNITIVE PERSONALITY as a VECTOR of REAL,
CAN-relaxable DYNAMICAL QUALIA AXES on the agent.

WHAT THIS IS
------------
The agent's cognitive STYLE is not a single dial. It is a PERSONALITY: a vector
of independent traits (openness, abstraction, skepticism, …), each its own felt
scalar the substrate can genuinely RELAX and CRYSTALLISE, each seeded with a
starting temperament (a tweak) but PRODUCED and moved by the dynamics. People
sit on a DISTRIBUTION across MANY traits simultaneously, each moving with state.

ONE MECHANISM, N TRAITS (the generalisation)
--------------------------------------------
This module started life as a SINGLE `disposition` scalar. It is now generalised
to a TRAIT VECTOR without forking the mechanism: a small `TRAIT_REGISTRY` (a
data table: trait name -> starting seed, qualia axis name, field attrs, gloss)
defines the vector's components, and ALL traits share the SAME relaxation +
crystallisation + mirror machinery. The agent's `agent_disposition` Microtheory
holds ONE `Concept` PER TRAIT (separate Concepts => genuinely INDEPENDENT: no
shared field, each moved only by its own evidence), each carrying its own
`state`/`external_field`/`identity_field` relaxed by the identical native rules
and mirrored to its own `<trait>_field`/`<trait>_external` attrs that its
`dynamical:<trait>` / `dynamical:<trait>_pull` qualia axes read.

Adding a trait = adding a `TRAIT_REGISTRY` entry (+ its QualiaDimension axis in
tools/build_qualia_space_seed.py), NOT new code. Data-driven.

BACK-COMPAT: `openness` IS THE OLD DISPOSITION
----------------------------------------------
The registry's `openness` trait IS the original `disposition` scalar — same
Concept name (`disposition`), same field attr (`disposition_field`), same axis
(`dynamical:disposition`), same -1.0 conservative default. Every existing
single-disposition function (`ensure_disposition`, `disposition_level`,
`set_disposition_seed`, `relax_disposition`, …) is now a thin trait-keyed shim
over `openness`, so existing callers (relation_grounding.MintPolicy,
tests/test_disposition*.py) are UNCHANGED in behaviour. The other seeded traits
(abstraction, skepticism) default to a behaviourally NEUTRAL 0.0 and have NO
consumer this layer — they change nothing until a later layer wires them.

The agent's willingness to mint referents / form associations
(conservative ↔ permissive) — the `openness` trait — is not a static config
knob. It is a felt scalar the substrate can genuinely RELAX and CRYSTALLISE,
seeded with a starting temperament (a tweak) but PRODUCED and moved by the
dynamics — the seed gives the starting point, the dynamics give the realism.

STRUCTURALLY IDENTICAL TO SELF-WORTH
------------------------------------
`domains/can_self_worth_bridge.py` already established the pattern: a resident's
self-worth is a `Concept` carrying `state`/`external_field`/`identity_field`,
relaxed by the engine's OWN native rules (`can_native_update_3state`,
`can_native_identity_field_feedback`) and read back — never a Python
computation. Disposition is the SAME shape, one felt scalar over on the AGENT
instead of a resident. So this module builds the agent a resident-style CAN
Microtheory holding a single `disposition` Concept, seeds its starting
temperament, and lets the identical native dynamics move it.

THE QUALIA AXIS (seeds/qualia_space.json)
-----------------------------------------
`dynamical:disposition` reads `field:disposition_field` — the CRYSTALLISED
STANDING trait. `dynamical:disposition_pull` reads `field:disposition_external`
(overlay) — the LIVE momentary openness, mirroring the valence(crystallised)/
pull(overlay) split. Both are quantum=1.0/half_width=4: the field marches in
integer ±1 steps (that is exactly how `can_native_identity_field_feedback`
moves `identity_field`), so quantum=1.0 makes each integer level a distinct
coordinate — a GENUINELY GRADED 9-level axis, unlike `dynamical:commitment`
(quantum=0.25) which saturates to {−4,0,+4} on the first committed tick. See the
seed gloss and scripts/qualia_disposition_demo.py for the measured spread.

PRODUCED, NOT HAND-WRITTEN
--------------------------
The native rule writes `identity_field`. This module MIRRORS that produced value
into `disposition_field` (and `external_field` into `disposition_external`) after
each relaxation — a mechanical copy of what the dynamics produced, never a
hand-written crystallised outcome mid-drive. The SEED only sets the STARTING
identity_field; every later value is the rule's, not ours.

BOUNDARY I/O + MINT-IF-ABSENT, SAFE DEFAULT
-------------------------------------------
Mirrors the policy-node idiom (stopping_policy / auto_approve / relation_grounding
MintPolicy): `ensure_disposition` mints the disposition CAN state on first use
with a SAFE DEFAULT temperament (mildly conservative — today's behaviour);
`disposition_level` reads the quantised standing trait; `set_disposition_seed`
tweaks the starting point. Idempotent, first-found-wins, no decision in Python.
"""
from __future__ import annotations

from typing import Any, Optional

import domains.analogy_search as asr

#: Node/edge vocabulary for the agent's disposition CAN state.
DISPOSITION_MT_NAME = "agent_disposition"
DISPOSITION_CONCEPT_NAME = "disposition"
DISPOSITION_MT_EDGE = "has_disposition_mt"

#: The CRYSTALLISED standing-trait attr the `dynamical:disposition` axis reads
#: (source `field:disposition_field` in seeds/qualia_space.json) and the LIVE
#: overlay attr `dynamical:disposition_pull` reads (`field:disposition_external`).
#: These are MIRRORS of the native CAN fields the rules actually relax — a
#: mechanical copy of the produced value, so the qualia axis reads a real,
#: dynamics-produced number and never a hand-set one.
DISPOSITION_FIELD_ATTR = "disposition_field"        # ← mirror of identity_field
DISPOSITION_EXTERNAL_ATTR = "disposition_external"  # ← mirror of external_field

#: The SAFE DEFAULT starting temperament. Mildly CONSERVATIVE (−1.0): a fresh
#: agent that has never been driven reads a standing disposition_level of −1 —
#: exactly the conservative mint stance the rest of the system defaults to today
#: (relation_grounding.MintPolicy's require_noun_dominant_head=True bright line).
#: The seed is a STARTING POINT on `identity_field`; the dynamics move it from
#: there. Neutral would be 0.0, fully permissive +4.0.
DEFAULT_DISPOSITION_SEED = -1.0

#: The trait axis quantiser — MUST match the seed (dynamical:<trait> quantum=1.0
#: / half_width=4, the graded 9-level scheme disposition proved). Shared by ALL
#: traits: the field marches in integer ±1 steps (that is how
#: can_native_identity_field_feedback moves identity_field), so quantum=1.0 makes
#: each integer level a distinct coordinate. Single source of truth for the
#: read-back; the signature builder reads the SAME numbers off the QualiaDimension
#: node. `_DISPOSITION_*` names are kept for back-compat.
_TRAIT_QUANTUM = 1.0
_TRAIT_HALF_WIDTH = 4
_DISPOSITION_QUANTUM = _TRAIT_QUANTUM
_DISPOSITION_HALF_WIDTH = _TRAIT_HALF_WIDTH


# --------------------------------------------------------------------------- #
# THE TRAIT REGISTRY — the vector's components as DATA, not code.
#
# The personality is a VECTOR of independent cognitive-style traits. This table
# defines its components; ALL traits share the SAME relaxation/crystallisation/
# mirror machinery below (generalised, never forked). Adding a trait = adding a
# row here + its `dynamical:<trait>` axis in tools/build_qualia_space_seed.py.
# No new code.
#
# Each trait lives as its OWN `Concept` in the shared `agent_disposition` Mt
# (separate Concepts => genuinely INDEPENDENT: no shared field, each moved only
# by its own evidence), carrying the standard CAN fields + its own mirrored
# `<field_attr>` (crystallised) / `<external_attr>` (live overlay) that its
# `dynamical:<trait>` / `dynamical:<trait>_pull` qualia axes read.
#
# `openness` IS THE OLD DISPOSITION — same Concept name (`disposition`), same
# field attrs, same axis (`dynamical:disposition`), same -1.0 default — so every
# existing single-disposition caller is unchanged. The other traits default to a
# behaviourally NEUTRAL 0.0 and are INERT this layer (no consumer yet).
# --------------------------------------------------------------------------- #
class TraitSpec:
    """One component of the cognitive personality vector. Pure data — the seed
    (starting point on identity_field), the qualia axis names, the CAN Concept
    name, and the mirrored axis attrs the signature reads. No behaviour here;
    the shared machinery below reads these fields for every trait alike."""

    __slots__ = ("name", "seed", "axis", "pull_axis", "concept_name",
                 "field_attr", "external_attr", "gloss")

    def __init__(self, name, *, seed, axis, concept_name, field_attr,
                 external_attr, pull_axis=None, gloss=""):
        self.name = name
        self.seed = float(seed)
        self.axis = axis                       # dynamical:<trait> (crystallised)
        self.pull_axis = pull_axis or (axis + "_pull")   # overlay axis
        self.concept_name = concept_name       # the CAN Concept's `name`
        self.field_attr = field_attr           # mirror of identity_field
        self.external_attr = external_attr      # mirror of external_field
        self.gloss = gloss


#: The registry, ordered (dict preserves insertion order -> a stable vector).
#: openness == old disposition; abstraction/skepticism are seeded-neutral and
#: INERT this layer (layer 2 wires their consumers). To grow the personality,
#: add a row here and the matching axis in tools/build_qualia_space_seed.py.
TRAIT_REGISTRY: "dict[str, TraitSpec]" = {
    "openness": TraitSpec(
        "openness",
        seed=DEFAULT_DISPOSITION_SEED,          # -1.0, mildly conservative = today
        axis="dynamical:disposition",           # the OLD axis name (back-compat)
        concept_name=DISPOSITION_CONCEPT_NAME,  # "disposition" (back-compat)
        field_attr=DISPOSITION_FIELD_ATTR,      # "disposition_field" (back-compat)
        external_attr=DISPOSITION_EXTERNAL_ATTR,
        pull_axis="dynamical:disposition_pull",
        gloss="OPENNESS — the agent's standing willingness to mint referents / "
              "form associations, conservative (−) ↔ permissive (+). IS the old "
              "single `disposition` scalar; drives the MintPolicy gate."),
    "abstraction": TraitSpec(
        "abstraction",
        seed=0.0,                               # neutral, INERT this layer
        axis="dynamical:abstraction",
        concept_name="trait:abstraction",
        field_attr="abstraction_field",
        external_attr="abstraction_external",
        gloss="ABSTRACTION — the agent's standing pull toward high-order, "
              "structural mappings, concrete (−) ↔ abstract (+). Seeded neutral; "
              "will drive analogy order_n in layer 2 (INERT until then)."),
    "skepticism": TraitSpec(
        "skepticism",
        seed=0.0,                               # neutral, INERT this layer
        axis="dynamical:skepticism",
        concept_name="trait:skepticism",
        field_attr="skepticism_field",
        external_attr="skepticism_external",
        gloss="SKEPTICISM — the agent's standing demand for evidence before "
              "accepting a correspondence, credulous (−) ↔ skeptical (+). Seeded "
              "neutral; will drive analogy min_score/recurrence in layer 2 "
              "(INERT until then)."),
}

#: The back-compat trait: the single-disposition API is a shim over `openness`.
OPENNESS_TRAIT = "openness"


def trait_spec(trait) -> TraitSpec:
    """Resolve a trait name (or a TraitSpec) to its registry entry. Raises
    KeyError for an unknown trait — a typo is a programming error, not a silent
    neutral default (the registry is the closed set of the agent's traits)."""
    if isinstance(trait, TraitSpec):
        return trait
    return TRAIT_REGISTRY[trait]


def trait_names() -> "list[str]":
    """The ordered list of trait names — the personality vector's axes."""
    return list(TRAIT_REGISTRY.keys())


# --------------------------------------------------------------------------- #
# Substrate / agent handle plumbing (mirrors analogy_search / auto_approve).
# --------------------------------------------------------------------------- #
def _sub(agent):
    """The substrate handle. Accepts a wrapper carrying `.s` (the agent object
    the tests build) or a bare substrate — the same both-ways acceptance
    analogy_search._sub / relation_grounding._sub / auto_approve._sub use."""
    return getattr(agent, "s", agent)


def _native(sub):
    """The native engine handle (`run_rules`/`set_attr` live on `._inner` for a
    Python `Substrate` wrapper, or directly on a raw `_native.Substrate`)."""
    return getattr(sub, "_inner", sub)


def _agent_node(agent):
    """The Agent hub node. Mirrors analogy_search._agent_node: try the wrapper's
    own `.agent`/`.agent_node`/`._agent`, else find the single Agent hub by
    scan. Returns None when there is no Agent (a bare-Mt substrate)."""
    for name in ("agent", "agent_node", "_agent"):
        n = getattr(agent, name, None)
        if n is not None:
            return n
    sub = _sub(agent)
    try:
        nodes = sub.nodes("Agent")
        return nodes[0] if nodes else None
    except Exception:
        return None


def _find_disposition_mt(sub, agent_node=None):
    """The agent's disposition Microtheory, first-found-wins. Prefer the one
    wired to the Agent hub via `has_disposition_mt`; fall back to a scan by
    name (a bare substrate with no Agent hub). None when absent."""
    if agent_node is not None:
        try:
            for mt in sub.neighbours(agent_node, DISPOSITION_MT_EDGE):
                return mt
        except Exception:
            pass
    try:
        for mt in sub.nodes("Microtheory"):
            if sub.node(mt)["attrs"].get("name") == DISPOSITION_MT_NAME:
                return mt
    except Exception:
        pass
    return None


def _trait_concept(sub, mt, concept_name):
    """The single trait Concept in the shared disposition Mt named `concept_name`
    (first-found). Generalised over `_disposition_concept`: every trait's Concept
    lives in the SAME Mt, distinguished by name."""
    try:
        for c in sub.neighbours(mt, "has_concept"):
            if sub.node(c)["attrs"].get("name") == concept_name:
                return c
    except Exception:
        pass
    return None


def _disposition_concept(sub, mt):
    """The `disposition` (== openness) Concept in the disposition Mt. Back-compat
    shim over `_trait_concept`; kept because relation_grounding._disposition_
    derived_gate imports and calls it directly."""
    return _trait_concept(sub, mt, DISPOSITION_CONCEPT_NAME)


# --------------------------------------------------------------------------- #
# Seed loading — the CAN dynamics + the qualia axis, idempotent.
# --------------------------------------------------------------------------- #
def _ensure_seeds(sub) -> bool:
    """Idempotently install the CAN base + decay/identity rules (so the native
    relaxation + identity feedback can move the disposition field) AND the
    qualia_space seed (so the `dynamical:disposition` axis exists for the
    signature to read). Reuses the ESTABLISHED loaders — `ensure_can_seed`
    (which loads can_native_reimplementation + can_decay_identity, guarded) and
    a Seed-sentinel-guarded qualia_space load, exactly as analogy_search
    already composes them. Returns True on a live substrate, False otherwise
    (honest no-op, no raise)."""
    native = _native(sub)
    if not hasattr(native, "run_rules") or not hasattr(native, "add_node"):
        return False
    try:
        from domains.can_self_worth_bridge import ensure_can_seed
        ensure_can_seed(native)
    except Exception:
        return False
    # The qualia axis seed — only needed so concept_signature can read the
    # disposition coordinate; guarded by the same Seed/SeedSummary sentinel the
    # rest of the tree uses so a full boot that already loaded it is not
    # doubled.
    try:
        if not _has_qualia_seed(native):
            from substrate.seed_loader import engine_rules_only, manifest_for
            native.load_seed_manifest(engine_rules_only(manifest_for("qualia_space")))
            native.add_node("Seed", {"id": "qualia_space", "version": "1.0.0"})
    except Exception:
        pass  # the CAN dynamics are the load-bearing seed; the axis read
              # degrades gracefully if qualia_space is unavailable
    return True


def _install_productions(native) -> None:
    """Admit the Γ productions the disposition wiring needs — the native
    substrate enforces an admissibility grammar (edges rejected unless a
    production admits their (src_type, edge_type, tgt_type)), so the disposition
    Mt/Concept edges must be admitted before `add_edge`, exactly as
    worlds/bigville_can_beliefs.install_productions does for the self-worth CAN
    state. Idempotent: `add_production` is safe to repeat; a duplicate is
    swallowed."""
    for src_t, et, tgt_t in (
        ("Agent", DISPOSITION_MT_EDGE, "Microtheory"),
        ("Microtheory", "has_concept", "Concept"),
    ):
        try:
            native.add_production({
                "src": {"type": src_t, "var": "src"},
                "edge_type": et,
                "tgt": {"type": tgt_t, "var": "tgt"},
                "where": None,
                "weight": {"type": "Lit", "value": 1.0},
                "provenance": "disposition",
            })
        except Exception:
            pass


def _has_qualia_seed(native) -> bool:
    for typ, key in (("Seed", "id"), ("SeedSummary", "seed_id")):
        try:
            for n in native.nodes(typ):
                if native.node(n)["attrs"].get(key) == "qualia_space":
                    return True
        except Exception:
            continue
    # a graph that already carries QualiaDimension nodes has the axis regardless
    # of how it was loaded — treat that as "have" so we never double-load.
    try:
        return bool(native.nodes("QualiaDimension"))
    except Exception:
        return False


# --------------------------------------------------------------------------- #
# The trait CAN state — mint-if-absent with a seeded temperament (generalised).
# --------------------------------------------------------------------------- #
def _mirror_produced_fields(native, concept, spec: Optional[TraitSpec] = None) -> None:
    """Copy the PRODUCED native CAN fields onto the trait axis attrs the qualia
    signature reads: `identity_field → <field_attr>` (crystallised standing
    trait), `external_field → <external_attr>` (live pull). A mechanical mirror
    of whatever the dynamics produced — NOT a hand-written outcome. Called after
    every relaxation and after seeding the start point. `spec` defaults to the
    `openness` trait (the old disposition) for back-compat callers."""
    if spec is None:
        spec = TRAIT_REGISTRY[OPENNESS_TRAIT]
    attrs = native.node(concept)["attrs"]
    native.set_attr(concept, spec.field_attr,
                    float(attrs.get("identity_field") or 0.0))
    native.set_attr(concept, spec.external_attr,
                    float(attrs.get("external_field") or 0.0))


def _ensure_disposition_mt(sub, native, ag):
    """Return the shared `agent_disposition` Microtheory, minting it (wired to
    the Agent hub) if absent. ALL traits live in this ONE Mt (as separate
    Concepts). An ADAPTIVE, allow_h_drift, discrete_mode='static' Mt so
    can_native_identity_field_feedback moves each trait's identity_field purely
    from its own evidence — the SAME isolation tests/test_can_identity_feedback
    uses. Returns None on failure."""
    mt = _find_disposition_mt(sub, ag)
    if mt is not None:
        return mt
    try:
        _install_productions(native)
        mt = native.add_node("Microtheory", {
            "name": DISPOSITION_MT_NAME, "temperature": 1.0,
            "discrete_mode": "static", "can_tick": 0,
            "update_policy": "adaptive", "allow_h_drift": 1,
        })
        if ag is not None:
            native.add_edge(ag, DISPOSITION_MT_EDGE, mt, {})
        return mt
    except Exception:
        return None


def _mint_trait_concept(native, mt, spec: TraitSpec, start: float):
    """Mint ONE trait Concept in the shared Mt with the seeded starting
    temperament on `identity_field`. Every trait gets the identical CAN fields +
    identity-evidence ledger — the shared machinery, keyed only by the spec's
    Concept name and mirrored attrs. Returns the Concept node."""
    concept = native.add_node("Concept", {
        "name": spec.concept_name,
        "category": "disposition",   # all traits share the disposition category
        "trait": spec.name,          # which vector component this Concept is
        # standard CAN fields the native rules relax. identity_field carries the
        # SEEDED starting temperament (a starting standing commitment).
        "state": 0.0, "external_field": 0.0, "identity_field": start,
        # the identity-evidence ledger the feedback rule reads/writes.
        "identity_evidence_confirm": 0, "identity_evidence_disconfirm": 0,
        "identity_evidence_tick": -1, "identity_decay_tick": -1,
        "identity_field_tick": -1,
        # the mirrored axis attrs — seeded to the start so a fresh read (before
        # any drive) reflects the seeded temperament.
        spec.field_attr: start,
        spec.external_attr: 0.0,
    })
    native.add_edge(mt, "has_concept", concept, {})
    return concept


def ensure_trait(agent, trait, *, seed: Optional[float] = None):
    """Idempotent: return the agent's Concept for `trait`, minting it (in the
    shared `agent_disposition` Mt, wired to the Agent hub) with the trait's
    SEEDED starting temperament if this graph has none. Never mints a second
    Concept for a trait once one exists (first-found-wins). The generalised
    core `ensure_disposition` and `ensure_traits` both delegate to this.

    `seed` (default the trait's registry seed) is the STARTING standing trait,
    written to `identity_field` and mirrored to `<field_attr>`. A tweak of the
    STARTING POINT only; the dynamics move it from there. A second call NEVER
    re-seeds an existing Concept (it may have drifted) — use `set_trait_seed`.

    Returns the trait Concept, or None on a non-live substrate."""
    spec = trait_spec(trait)
    sub = _sub(agent)
    if sub is None:
        return None
    if not _ensure_seeds(sub):
        return None
    native = _native(sub)
    ag = _agent_node(agent)

    mt = _find_disposition_mt(sub, ag)
    if mt is not None:
        existing = _trait_concept(sub, mt, spec.concept_name)
        if existing is not None:
            return existing  # already minted; do NOT re-seed (may have drifted)

    start = float(spec.seed if seed is None else seed)
    try:
        mt = _ensure_disposition_mt(sub, native, ag)
        if mt is None:
            return None
        return _mint_trait_concept(native, mt, spec, start)
    except Exception:
        return None


def ensure_traits(agent, *, seeds: Optional[dict] = None) -> dict:
    """Mint the WHOLE personality vector: every registry trait's Concept, each
    with its seeded default (or a per-trait override in `seeds`). Idempotent —
    a trait already present is returned as-is (not re-seeded). Returns
    {trait_name: Concept} for the traits that exist on a live substrate (empty
    on a non-live substrate).

    This is the vector analog of `ensure_disposition`: one call mints the agent's
    entire cognitive personality with behaviourally-neutral seeded defaults
    (openness -1.0 = today; the rest 0.0 = inert)."""
    out = {}
    seeds = seeds or {}
    for name in TRAIT_REGISTRY:
        c = ensure_trait(agent, name, seed=seeds.get(name))
        if c is not None:
            out[name] = c
    return out


def ensure_disposition(agent, *, seed: Optional[float] = None):
    """Idempotent: return the agent's `disposition` (== `openness`) Concept.
    BACK-COMPAT shim over `ensure_trait(agent, 'openness')` — same Concept
    (`disposition`), same field attr, same -1.0 default, same Mt. Existing
    callers are unchanged.

    `seed` (default `DEFAULT_DISPOSITION_SEED` = −1.0, mildly conservative =
    today's behaviour) is the STARTING standing trait. A second call NEVER
    re-seeds an existing Concept — use `set_disposition_seed`.

    Returns the disposition Concept node, or None on a non-live substrate."""
    return ensure_trait(agent, OPENNESS_TRAIT, seed=seed)


# --------------------------------------------------------------------------- #
# Read-back — the quantised standing trait (generalised + back-compat shims).
# --------------------------------------------------------------------------- #
def _trait_concept_for_read(agent, spec, ensure):
    """Resolve the trait Concept for a read: mint-if-absent when `ensure`, else
    a non-minting lookup (returns None if absent — the caller uses the seeded
    default)."""
    sub = _sub(agent)
    if ensure:
        return ensure_trait(agent, spec.name)
    ag = _agent_node(agent)
    mt = _find_disposition_mt(sub, ag) if sub is not None else None
    return _trait_concept(sub, mt, spec.concept_name) if mt is not None else None


def trait_field(agent, trait, *, ensure: bool = True) -> float:
    """The RAW crystallised standing-trait value for `trait` (`<field_attr>`, a
    mirror of the produced `identity_field`). `ensure=True` mints-if-absent (so a
    fresh graph reads the seeded default); `ensure=False` reads a missing trait
    as the trait's seeded default WITHOUT minting (the off-by-default
    discipline). Mechanical read, no decision. Generalises `disposition_field`."""
    spec = trait_spec(trait)
    sub = _sub(agent)
    concept = _trait_concept_for_read(agent, spec, ensure)
    if concept is None:
        return float(spec.seed)
    try:
        return float(_native(sub).node(concept)["attrs"].get(
            spec.field_attr, spec.seed))
    except Exception:
        return float(spec.seed)


def trait_level(agent, trait, *, ensure: bool = True) -> int:
    """The QUANTISED standing trait — the agent's coordinate on the
    `dynamical:<trait>` qualia axis: an integer step in [−4, +4], the SAME
    `round(x/quantum)` clamp the signature builder applies (quantum=1.0,
    half_width=4). A field that rounds to 0 reads as 0. Generalises
    `disposition_level`."""
    raw = trait_field(agent, trait, ensure=ensure)
    k = asr._round_to_vocab(raw, _TRAIT_QUANTUM, _TRAIT_HALF_WIDTH)
    return 0 if k is None else int(k)


def trait_vector(agent, *, ensure: bool = True) -> dict:
    """The WHOLE personality read at once: {trait_name: trait_level} across every
    registry trait — the agent's position in the cognitive-style vector space.
    With `ensure=True` mints any absent trait to its seeded default first; with
    `ensure=False` reads absent traits as their seeded defaults without minting.

    This is the vector read the single scalar could never give: the agent is a
    POINT in an N-dimensional personality space, and this returns that point."""
    return {name: trait_level(agent, name, ensure=ensure)
            for name in TRAIT_REGISTRY}


def disposition_field(agent, *, ensure: bool = True) -> float:
    """The RAW crystallised standing openness value. BACK-COMPAT shim over
    `trait_field(agent, 'openness')` — same `disposition_field` attr, same -1.0
    default. `ensure=False` reads the safe default WITHOUT minting."""
    return trait_field(agent, OPENNESS_TRAIT, ensure=ensure)


def disposition_level(agent, *, ensure: bool = True) -> int:
    """The QUANTISED standing openness — the agent's `dynamical:disposition`
    coordinate in [−4, +4]. BACK-COMPAT shim over `trait_level(agent,
    'openness')`."""
    return trait_level(agent, OPENNESS_TRAIT, ensure=ensure)


# --------------------------------------------------------------------------- #
# Seed tweak — set the STARTING point (not the driven outcome). Generalised.
# --------------------------------------------------------------------------- #
def set_trait_seed(agent, trait, value: float):
    """Tweak a trait's STARTING temperament: mint-if-absent, then (re)write the
    given starting standing trait onto the Concept's `identity_field` and mirror
    it to `<field_attr>`. The seed knob — the STARTING POINT the dynamics move
    from. Resets the identity-evidence LEDGER (confirm/disconfirm → 0) so the
    new start is a clean temperament, not the old one plus fresh evidence. Use
    to place an agent on a trait's DISTRIBUTION; `relax_trait` MOVES it from
    there. Returns the resulting `trait_level`. Generalises
    `set_disposition_seed`."""
    spec = trait_spec(trait)
    concept = ensure_trait(agent, spec.name)
    if concept is None:
        return trait_level(agent, spec.name, ensure=False)
    native = _native(_sub(agent))
    start = float(value)
    try:
        native.set_attr(concept, "identity_field", start)
        native.set_attr(concept, "identity_evidence_confirm", 0)
        native.set_attr(concept, "identity_evidence_disconfirm", 0)
        native.set_attr(concept, spec.field_attr, start)
        _mirror_produced_fields(native, concept, spec)
    except Exception:
        pass
    return trait_level(agent, spec.name, ensure=False)


def set_disposition_seed(agent, value: float):
    """Tweak the STARTING openness temperament. BACK-COMPAT shim over
    `set_trait_seed(agent, 'openness', value)`. Returns the resulting
    `disposition_level`."""
    return set_trait_seed(agent, OPENNESS_TRAIT, value)


# --------------------------------------------------------------------------- #
# MOVEMENT — the trait moved BY THE DYNAMICS from evidence. Generalised.
# --------------------------------------------------------------------------- #
def relax_trait(agent, trait, evidence: float, *, ticks: int = 1,
                max_steps: int = 3000) -> int:
    """Move a trait by feeding TRAIT EVIDENCE through the engine's OWN
    `can_native_identity_field_feedback` rule — the trait is PRODUCED by the
    relaxation, not hand-written. Generalises `relax_disposition`; the mechanism
    is IDENTICAL for every trait (that is the point — one machinery, N traits).

    `evidence` is a signed signal on the trait's own axis; its SIGN is applied
    as the trait Concept's per-tick sigma (`state`) — the sustained-sigma drive
    the identity-feedback rule steps `identity_field` toward, one ±1 quantum per
    strictly-later tick. `ticks` is how many consecutive same-sign steps this
    evidence is worth.

    Because each trait is its OWN Concept, relaxing one trait touches ONLY that
    Concept's fields — traits move INDEPENDENTLY. The DECISION (how far the field
    moves) is the graph rule's. Afterward it MIRRORS the produced fields onto the
    trait's axis attrs. Returns the new `trait_level`. Zero evidence is a no-op.

    Under mixed evidence the trait has the hysteresis of a real standing
    temperament: an unestablished trait fed equal +/− stays near neutral; an
    established one resists occasional counter-evidence but reverses under
    sustained counter-evidence (the ledger log-odds flip)."""
    spec = trait_spec(trait)
    concept = ensure_trait(agent, spec.name)
    if concept is None:
        return trait_level(agent, spec.name, ensure=False)
    native = _native(_sub(agent))
    if not evidence:
        return trait_level(agent, spec.name, ensure=False)
    ag = _agent_node(agent)
    mt = _find_disposition_mt(_sub(agent), ag)
    if mt is None:
        return trait_level(agent, spec.name, ensure=False)
    sigma = 1.0 if evidence > 0 else -1.0
    try:
        base = int(native.node(mt)["attrs"].get("can_tick") or 0)
        for i in range(max(1, int(ticks))):
            native.set_attr(mt, "can_tick", base + i + 1)  # strictly-later epoch
            native.set_attr(concept, "state", sigma)        # sustain the sigma
            native.run_rules(max_steps)
        _mirror_produced_fields(native, concept, spec)
    except Exception:
        pass
    return trait_level(agent, spec.name, ensure=False)


def relax_disposition(agent, evidence: float, *, ticks: int = 1,
                      max_steps: int = 3000) -> int:
    """Move the agent's openness by feeding DISPOSITION EVIDENCE through the
    identity-feedback rule. BACK-COMPAT shim over `relax_trait(agent, 'openness',
    …)`. positive = MORE PERMISSIVE, negative = MORE CONSERVATIVE. Returns the
    new `disposition_level`."""
    return relax_trait(agent, OPENNESS_TRAIT, evidence, ticks=ticks,
                       max_steps=max_steps)


def pull_trait(agent, trait, amount: float, *, max_steps: int = 3000) -> float:
    """Apply a LIVE momentary PULL to a trait — the `dynamical:<trait>_pull`
    overlay axis, the "I'm being pulled right now" reading BEFORE it settles into
    the standing trait. Writes `amount` as the Concept's `external_field` (the
    live term of `h_eff = external + identity`), relaxes so it participates, and
    MIRRORS the produced `external_field` onto `<external_attr>`. The STANDING
    trait is unchanged by a single pull — the GAP between the live pull and the
    standing trait IS 'I'm not sure how I feel'. Returns the raw `<external_attr>`
    produced. Generalises `pull_disposition`."""
    spec = trait_spec(trait)
    concept = ensure_trait(agent, spec.name)
    if concept is None:
        return 0.0
    native = _native(_sub(agent))
    try:
        native.set_attr(concept, "external_field", float(amount))
        if hasattr(native, "force_all_dirty"):
            native.force_all_dirty()  # external_field written outside the
                                      # rule-effect path; otherwise no-op'd
        native.run_rules(max_steps)
        _mirror_produced_fields(native, concept, spec)
        return float(native.node(concept)["attrs"].get(spec.external_attr, 0.0))
    except Exception:
        return 0.0


def pull_disposition(agent, openness: float, *, max_steps: int = 3000) -> float:
    """Apply a LIVE momentary openness PULL. BACK-COMPAT shim over
    `pull_trait(agent, 'openness', openness)`. Returns the produced
    `disposition_external`."""
    return pull_trait(agent, OPENNESS_TRAIT, openness, max_steps=max_steps)


def crystallize_trait(agent, trait, *, run: bool = True) -> bool:
    """Tick the CAN identity dynamics once for the trait's Mt so a sustained live
    pull settles into the standing trait, then mirror the produced fields. The
    trait-scoped analog of analogy_search.crystallize. Returns True if ticked,
    False on a non-live substrate. Generalises `crystallize_disposition`."""
    spec = trait_spec(trait)
    concept = ensure_trait(agent, spec.name)
    if concept is None:
        return False
    native = _native(_sub(agent))
    ag = _agent_node(agent)
    mt = _find_disposition_mt(_sub(agent), ag)
    if mt is None:
        return False
    try:
        if run:
            base = int(native.node(mt)["attrs"].get("can_tick") or 0)
            native.set_attr(mt, "can_tick", base + 1)
            native.run_rules(3000)
        _mirror_produced_fields(native, concept, spec)
    except Exception:
        return False
    return True


def crystallize_disposition(agent, *, run: bool = True) -> bool:
    """Tick the openness dynamics once. BACK-COMPAT shim over
    `crystallize_trait(agent, 'openness')`."""
    return crystallize_trait(agent, OPENNESS_TRAIT, run=run)


def trait_signature(agent, trait, *, overlay: bool = False) -> frozenset:
    """The agent's own qualia signature AT a trait's Concept — the coordinates it
    occupies in qualia space, including its `dynamical:<trait>` (and, with
    `overlay=True`, `dynamical:<trait>_pull`) coordinate. A thin read over
    analogy_search.concept_signature, so the trait appears in the SAME
    dimensional space as any other felt concept (one space). Empty frozenset on a
    non-live substrate. Generalises `disposition_signature`."""
    spec = trait_spec(trait)
    concept = ensure_trait(agent, spec.name)
    if concept is None:
        return frozenset()
    return asr.concept_signature(_native(_sub(agent)), concept, overlay=overlay)


def personality_signature(agent, *, overlay: bool = False) -> dict:
    """The agent's PERSONALITY as a point in qualia space: {trait_name:
    dynamical:<trait> coordinate} across ALL traits — the whole vector's
    signature read at once. Each entry is the produced, quantised standing
    coordinate on that trait's axis (or None when the trait's coordinate rounds
    to the neutral floor the signature omits). This is the multi-axis personality
    signature the demo/tests read — distinct trait vectors give distinct points
    here."""
    out = {}
    for name, spec in TRAIT_REGISTRY.items():
        sig = trait_signature(agent, name, overlay=overlay)
        coord = None
        for t in sig:
            if t[0] == spec.axis:
                coord = t
                break
        out[name] = coord
    return out


def disposition_signature(agent, *, overlay: bool = False) -> frozenset:
    """The agent's own qualia signature at the openness (disposition) Concept.
    BACK-COMPAT shim over `trait_signature(agent, 'openness')`."""
    return trait_signature(agent, OPENNESS_TRAIT, overlay=overlay)


# --------------------------------------------------------------------------- #
# HOMEOSTASIS — the disposition self-regulates from REAL graph condition.
#
# WHAT THIS IS (blend layer 2)
# ----------------------------
# The disposition axis above is MOVEABLE, but on its own it moves only from
# evidence a caller hands it. This closes the loop: `disposition_homeostasis_step`
# READS the agent's real graph condition — the pollution and starvation signals
# the mint pipeline actually produces — and INJECTS them as disposition evidence,
# so the temperament tracks the state of the graph. Over repeated steps a
# POLLUTING regime (minting garbage, refusing everything) drives the disposition
# CONSERVATIVE, tightening the derived mint gate; a STARVED regime (dark
# relational axes, nothing minting, nothing analogising) drives it PERMISSIVE,
# loosening the gate. The gate self-regulates — a temperament that responds to
# state, not a static knob.
#
# THE SIGNALS ARE REAL, MECHANICAL GRAPH READS (no magic, no Python decision)
# ---------------------------------------------------------------------------
#   POLLUTION (=> negative evidence, tighten toward conservative):
#     · a HIGH recent mint REFUSAL-RATE (the mint gate is straining against a
#       flood of garbage candidates), read off a mint-pass result; AND/OR
#     · many THIN minted_referent LEAVES that never got elaborated — a
#       minted_referent Concept with no OUTGOING relational edges of its own is a
#       leaf the graph named but never grew (pollution: cheap fabrication that
#       earned nothing). Counted directly from graph state.
#   STARVATION (=> positive evidence, loosen toward permissive):
#     · the relational qualia axes staying DARK — few/no concepts carry any
#       telic/constitutive/agentive outgoing edge (the graph is not forming the
#       associations that light those axes); AND/OR
#     · find_analogies returning NOTHING (no structural correspondence found);
#       AND/OR
#     · a high DROP-RATE with LOW mint yield (the gate is refusing referents the
#       corpus genuinely names but the strict gate will not admit).
#
# THE DECISION IS THE RELAXATION, NOT A PYTHON if
# -----------------------------------------------
# This function COMPUTES the signed evidence magnitude from those reads, but it
# does NOT decide how far the disposition moves. It hands the signed evidence to
# `relax_disposition`, and the native `can_native_identity_field_feedback` rule
# integrates it (±1 quantum per tick toward the cumulative evidence log-odds sign,
# with the hysteresis of a real ledger). The Python here is boundary I/O: read
# graph counts, turn them into a sign + a tick budget, hand to the CAN rule.
#
# HONEST NOTE ON THE EVIDENCE CHANNEL
# -----------------------------------
# The crystallised standing trait (`identity_field`, mirrored to
# `disposition_field`) is moved ONLY by the sigma/evidence-ledger channel
# (`can_native_identity_evidence_sample` reads `state`'s sign; the FEEDBACK rule
# steps the field toward the ledger log-odds). `external_field` participates in
# the local-field sum but has NO path into the identity ledger — writing evidence
# there would move only the OVERLAY (`disposition_external`) and never crystallise.
# So this step drives the STANDING trait through the sigma channel (via
# relax_disposition) — the only channel that integrates evidence into the
# crystallised temperament — and ALSO mirrors the raw signed signal onto the
# overlay (`external_field`, via pull_disposition) so the momentary
# `dynamical:disposition_pull` reads the live homeostatic pressure. The standing
# MOVEMENT is the ledger integrating the evidence; the overlay is the live read.
# --------------------------------------------------------------------------- #

#: A minted_referent Concept is "thin/unelaborated" when it has NO outgoing
#: relational edge of its own — a leaf the graph named but never grew. These are
#: the relation cues a real (non-thin) concept would carry.
_ELABORATION_EDGE_TYPES = (
    "used_for", "enables", "serves", "regulates", "controls", "gates",
    "produces", "grounds", "exhibits",
    "has_part", "part_of", "made_of", "composed_of", "constitutes", "contains",
    "member_of",
    "causes", "caused_by", "creates", "created_by", "depends_on", "derived_from",
    "genls",
)


def _count_minted_referents(sub) -> tuple[int, int]:
    """(total_minted, thin_minted): how many Concepts carry `minted_referent`,
    and of those how many are THIN JUNK — genuinely unelaborated leaves. A minted
    referent counts as thin only when it is UNUSED: it has NO outgoing elaboration
    edge of its OWN *and* is NOT the target of any incoming relation edge from a
    real concept. A referent that IS wired as a relation target is doing its job
    (it lights the source's relational axis) — that is not pollution, it is the
    graph working. Only a leaf that nothing points at and that points at nothing
    is the 'thin leaf the corpus named but never grew' pollution witness. A pure
    mechanical scan of graph state."""
    total = 0
    thin = 0
    try:
        for cid in sub.nodes("Concept"):
            try:
                if not sub.node(cid)["attrs"].get("minted_referent"):
                    continue
            except Exception:
                continue
            total += 1
            used = False
            # (a) does it elaborate anything itself (outgoing relation)?
            for et in _ELABORATION_EDGE_TYPES:
                try:
                    if list(sub.neighbours(cid, et)):
                        used = True
                        break
                except Exception:
                    continue
            # (b) is it the target of an incoming relation (in use as a referent)?
            if not used:
                for et in _ELABORATION_EDGE_TYPES:
                    try:
                        if list(sub.in_neighbours(cid, et)):
                            used = True
                            break
                    except Exception:
                        continue
            if not used:
                thin += 1
    except Exception:
        return (0, 0)
    return (total, thin)


def _count_relational_lit(sub) -> tuple[int, int]:
    """(concepts_total, concepts_with_relation): how many held Concepts carry ANY
    outgoing telic/constitutive/agentive relation edge. A DARK relational surface
    (few lit) is the starvation witness — the graph is not forming the
    associations that light those qualia axes. Mechanical scan; INFRASTRUCTURE
    Concepts are EXCLUDED so they do not fake a dark corpus:
      · the disposition Concept itself (category=disposition) — bookkeeping;
      · CAN rule-doc Concepts the seed loads (names like `can_native_*`) — engine
        infrastructure, not corpus concepts;
      · minted_referent leaves — those are the POLLUTION witness (thin junk),
        counted separately, not part of the elaboration surface.
    Only genuine corpus Concepts remain, so a dark surface reads dark HONESTLY."""
    total = 0
    lit = 0
    try:
        for cid in sub.nodes("Concept"):
            try:
                a = sub.node(cid)["attrs"]
            except Exception:
                continue
            name = a.get("name") or ""
            if a.get("name") == DISPOSITION_CONCEPT_NAME:
                continue
            if a.get("category") == "disposition":
                continue
            if isinstance(name, str) and name.startswith("can_native"):
                continue
            if a.get("minted_referent"):
                continue
            total += 1
            for et in ("used_for", "enables", "serves", "regulates", "controls",
                       "gates", "produces", "has_part", "part_of", "made_of",
                       "composed_of", "contains", "member_of", "causes",
                       "caused_by", "creates", "created_by", "depends_on",
                       "derived_from"):
                try:
                    if list(sub.neighbours(cid, et)):
                        lit += 1
                        break
                except Exception:
                    continue
    except Exception:
        return (0, 0)
    return (total, lit)


def homeostasis_signals(agent, *, mint_result: Optional[dict] = None,
                        analogies: Optional[list] = None) -> dict:
    """Read the REAL graph-condition signals the homeostasis step integrates —
    pure mechanical graph reads, NO decision. Returns a dict:

      {minted_total, thin_minted, thin_ratio,
       concepts_total, relational_lit, relational_lit_ratio,
       refusal_rate, drop_rate, mint_yield, analogy_count,
       pollution, starvation, net}

    `mint_result` (optional): a dict returned by
    relation_grounding.mint_referents_from_relations — supplies the observed
    `refusal_rate`, `minted` yield, and the nested ground_relations `drop_rate`.
    `analogies` (optional): a find_analogies result list; when absent its count
    is 0.

    POLLUTION vs STARVATION are read from ORTHOGONAL graph facts, so the two
    regimes genuinely separate (an earlier design that fed refusal_rate into
    BOTH collapsed them to the same net). The two witnesses:

    POLLUTION in [0,1] — the negative-evidence (conservative) pressure. GARBAGE
      is arriving / entering: a HIGH recent mint refusal-rate (the gate straining
      against a flood of clause-fragment candidates) OR thin, unelaborated
      minted_referent leaves ACCUMULATING (junk that got through and never grew).
        pollution = max(refusal_rate, thin_ratio)
      Both are the task's named pollution signals; the thin-leaf term catches
      junk that slipped past a loose gate, the refusal term catches the pressure
      of junk arriving at a strict one.

    STARVATION in [0,1] — the positive-evidence (permissive) pressure, read from
      DIFFERENT facts than pollution so the regimes do not alias: the relational
      qualia surface staying DARK (few/no concepts carry any telic/constitutive/
      agentive edge — 1 - relational_lit_ratio), find_analogies returning NOTHING,
      and — when the gate refused everything it saw with ZERO mint yield (high
      drop/refusal but nothing entered) — a barren-yield term. Keyed off zero
      yield so it does not alias pollution's churn term.
        starvation = mean(dark_surface, [barren_yield], [empty_analogies])

    The regimes separate because pollution reads the MINT INPUT (refusal / thin
    leaves) while starvation reads the RELATIONAL OUTPUT (dark axes / no
    analogies): a polluting corpus floods the gate (high refusal) but need not
    leave the relational surface dark; a starved corpus leaves the relational
    surface dark and analogies empty. NET = starvation - pollution in [-1,1].

    `mint_result` (optional): from mint_referents_from_relations — supplies
    `refusal_rate`, `minted` yield, and the nested ground_relations `drop_rate`.
    `analogies` (optional): a find_analogies result list; contributes the
    empty-analogies starvation term only when provided."""
    sub = _sub(agent)
    minted_total, thin_minted = _count_minted_referents(sub)
    concepts_total, relational_lit = _count_relational_lit(sub)
    thin_ratio = (thin_minted / minted_total) if minted_total else 0.0
    rel_lit_ratio = (relational_lit / concepts_total) if concepts_total else 0.0
    # thin junk as a share of the WHOLE graph (real concepts + minted leaves) —
    # the honest pollution scale: a single thin leaf among many real concepts is
    # barely polluted; a graph swamped with thin leaves is heavily polluted. Used
    # for the pollution reading; `thin_ratio` (share of MINTED nodes) is reported
    # for transparency but is too brittle to drive the signal (it hits 1.0 on the
    # first thin leaf).
    graph_total = concepts_total + minted_total
    thin_share = (thin_minted / graph_total) if graph_total else 0.0

    refusal_rate = 0.0
    drop_rate = 0.0
    mint_yield = 0
    have_mint = mint_result is not None
    if mint_result:
        try:
            refusal_rate = float(mint_result.get("refusal_rate") or 0.0)
            mint_yield = int(mint_result.get("minted") or 0)
            gr = mint_result.get("ground_relations") or {}
            drop_rate = float(gr.get("drop_rate") or 0.0)
        except Exception:
            pass
    analogy_count = len(analogies) if analogies is not None else 0

    # POLLUTION — the MINT INPUT: junk actually PRESENT in the graph. Thin
    # unelaborated minted leaves as a SHARE OF THE WHOLE GRAPH (thin_share) — junk
    # that got through and never grew, scaled honestly so one leaf among many real
    # concepts is not read as total pollution. HONEST NOTE: the task lists a "high
    # mint refusal-rate" as an alternative pollution witness, but refusal-rate
    # proved AMBIGUOUS in practice — a strict gate REFUSING genuine referents (the
    # starved case) also has a high refusal-rate, so keying pollution on refusal
    # aliases starvation and both regimes collapse to the same net. The reliable
    # pollution witness is junk actually ENTERING and STAYING thin (thin_share):
    # you can only be polluted by garbage that got IN. So pollution is read off
    # the accumulated thin-leaf share; refusal_rate is reported for transparency
    # but does not drive the signal. (See the stage's honest report.)
    pollution = min(1.0, thin_share)

    # STARVATION — the RELATIONAL OUTPUT: dark relational surface + empty
    # analogies + (when the gate refused everything it saw, i.e. HIGH drop/refusal
    # with ZERO mint yield) the barren-yield term. Deliberately keyed off zero
    # yield so it does NOT alias pollution's churn term. Averaged over observed
    # contributors.
    starve_terms: list[float] = []
    if concepts_total:
        starve_terms.append(1.0 - rel_lit_ratio)          # dark relational surface
    if have_mint and mint_yield == 0:
        starve_terms.append(min(1.0, max(drop_rate, refusal_rate)))
    if analogies is not None:
        starve_terms.append(1.0 if analogy_count == 0 else 0.0)
    starvation = (sum(starve_terms) / len(starve_terms)) if starve_terms else 0.0

    net = starvation - pollution
    return {
        "minted_total": minted_total, "thin_minted": thin_minted,
        "thin_ratio": thin_ratio, "thin_share": thin_share,
        "concepts_total": concepts_total, "relational_lit": relational_lit,
        "relational_lit_ratio": rel_lit_ratio,
        "refusal_rate": refusal_rate, "drop_rate": drop_rate,
        "mint_yield": mint_yield, "analogy_count": analogy_count,
        "pollution": pollution, "starvation": starvation, "net": net,
    }


def disposition_homeostasis_step(agent, *, mint_result: Optional[dict] = None,
                                 analogies: Optional[list] = None,
                                 ticks: int = 1,
                                 deadband: float = 0.15) -> dict:
    """ONE homeostatic feedback step: read the agent's real graph condition
    (pollution vs starvation), inject it as disposition EVIDENCE, and let the CAN
    relaxation integrate it into the standing temperament. Over repeated steps a
    polluting regime drives the disposition conservative (tightening the derived
    mint gate); a starved regime drives it permissive (loosening it).

    Pipeline (all boundary I/O + one native relaxation):
      1. `homeostasis_signals` — mechanical reads of graph state (thin minted
         leaves, dark relational surface) plus the optional mint-pass / analogy
         observations. Produces a signed `net` pressure in [-1,1].
      2. If |net| is within `deadband` (default 0.15) the condition is BALANCED —
         no evidence is injected (a no-op tick; the disposition does not drift on
         noise). This is the neutral zone, not a decision about the field.
      3. Otherwise the SIGN of `net` is the disposition evidence: net > 0 (starved)
         => positive/permissive evidence; net < 0 (polluted) => negative/
         conservative evidence. It is handed to `relax_disposition`, which drives
         the sigma channel and lets `can_native_identity_field_feedback` step the
         crystallised trait (the DECISION — how far — is the rule's, not ours).
      4. The raw signed `net` is ALSO mirrored onto the live overlay via
         `pull_disposition`, so `dynamical:disposition_pull` reads the momentary
         homeostatic pressure (the live read; the standing movement is step 3).

    Returns {signals, evidence, level_before, level_after, moved, pull} — the
    observed signals, the injected evidence sign (or 0.0 in the deadband), the
    disposition_level before/after, whether it moved, and the overlay pull read.
    A step never HAND-WRITES the crystallised trait — every standing change is
    the relaxation's."""
    # ensure the disposition exists (a homeostasis step is an explicit act on the
    # temperament, so minting-if-absent here is correct — unlike the mint gate's
    # non-minting read).
    ensure_disposition(agent)
    level_before = disposition_level(agent, ensure=False)

    sig = homeostasis_signals(agent, mint_result=mint_result, analogies=analogies)
    net = float(sig["net"])

    evidence = 0.0
    pull = 0.0
    if abs(net) >= float(deadband):
        evidence = 1.0 if net > 0 else -1.0
        # STANDING movement — the sigma channel the identity ledger integrates.
        relax_disposition(agent, evidence, ticks=max(1, int(ticks)))
        # LIVE overlay — the momentary homeostatic pressure (raw signed net).
        try:
            pull = pull_disposition(agent, net)
        except Exception:
            pull = 0.0

    level_after = disposition_level(agent, ensure=False)
    return {
        "signals": sig,
        "evidence": evidence,
        "level_before": level_before,
        "level_after": level_after,
        "moved": level_after != level_before,
        "pull": pull,
    }


__all__ = [
    # vocabulary / registry
    "DISPOSITION_MT_NAME", "DISPOSITION_CONCEPT_NAME", "DISPOSITION_MT_EDGE",
    "DISPOSITION_FIELD_ATTR", "DISPOSITION_EXTERNAL_ATTR",
    "DEFAULT_DISPOSITION_SEED",
    "TraitSpec", "TRAIT_REGISTRY", "OPENNESS_TRAIT",
    "trait_spec", "trait_names",
    # trait-keyed API (the personality vector)
    "ensure_trait", "ensure_traits",
    "trait_field", "trait_level", "trait_vector",
    "set_trait_seed", "relax_trait", "pull_trait", "crystallize_trait",
    "trait_signature", "personality_signature",
    # back-compat single-disposition API (shims over openness)
    "ensure_disposition", "disposition_field", "disposition_level",
    "set_disposition_seed", "relax_disposition", "pull_disposition",
    "crystallize_disposition", "disposition_signature",
    # homeostasis
    "homeostasis_signals", "disposition_homeostasis_step",
]
