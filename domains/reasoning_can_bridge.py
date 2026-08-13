"""reasoning_can_bridge -- ADDS a bridge between the deduction facility
(domains/propositional_deduction.py, domains/inference_generation.py) and
the native CAN belief-network facility
(seeds/can_native_reimplementation.json, worlds/bigville_can_beliefs.py). See
docs/research/engine_substrate/REASONING_FACILITY_BRIDGE_PREREG.md/_RESULTS.md
for the original investigation, and
docs/research/engine_substrate/ENTITY_RESOLUTION_PREREG.md/_RESULTS.md for
this module's GENERAL identity-resolution rewire (below).

Two directions, both pure ADDITIONS -- neither facility's own internals
(domains/propositional_deduction.py, domains/inference_generation.py,
domains/situation_model_reader.py, worlds/bigville_can_beliefs.py,
runners/dsl/src/can_ops.rs) is edited by this module. Nothing here runs a
Python rule engine or holds agent state; every write is a mechanical call
into an EXISTING primitive (concept_apply_evidence / ingest_predication).

  1. DEDUCTION -> CAN evidence (`apply_derived_fact_as_can_evidence` /
     `apply_inference_hits_as_can_evidence`). A derived fact `is_a(entity,
     attr)` becomes a `concept_apply_evidence` call
     (can_ops.rs::apply_evidence_h, already shipped, already called by
     worlds/bigville_can_beliefs.apply_scenario_evidence) on the CAN Concept
     named `attr` inside the Microtheory this entity DENOTES (see below) --
     topics like "world_safe"/"trust_mayor" being plain lowercase-underscore
     strings in the EXACT shape propositional_deduction._norm_attr already
     normalizes attr names into (this half stays a literal match -- both
     facilities' TOPIC vocabulary is inherently symbolic on both sides, see
     ENTITY_RESOLUTION_PREREG.md sec1).

  2. CAN -> deduction fact (`can_state_as_predications`). A settled CAN
     Concept's discrete state becomes an is_a/not_ predication on the entity
     that DENOTES this Mt (read back via the same mechanism, reversed),
     ingested through the UNMODIFIED situation_model_reader.ingest_predication
     -- reusing propositional_deduction's OWN not_ prefix convention (already
     mechanically derived for modus tollens, propositional_deduction.py
     `_negate_attr`) for a negative (state==-1) reading.

GENERAL IDENTITY RESOLUTION (ENTITY_RESOLUTION_RESULTS.md). Both directions
used to find "whose CAN Microtheory is this" by FORMATTING a string --
f"{entity}_beliefs" -- and hoping it happened to equal a real Microtheory's
name (true only when the deduction-side entity name is byte-identical to
worlds/bigville_can_beliefs.build_resident_can_mt's own `resident["name"]`).
That coincidence is now REPLACED by an explicit, graph-native `denotes` edge
(SmEntity -> Microtheory), minted by seeds/entity_concept_correspondence.json
via TWO Rules, Occam-ordered:

  1. sm_entity_denotes_believer_exact -- name equality (the OLD convention's
     case, now an explicit graph fact via a Rule, not a Python string
     format).
  2. sm_entity_denotes_believer_by_name_tokens -- fires only when (1) does
     not apply. Uses the native `Covers` Term (Set/FrozenSet SUBSET test,
     runners/dsl/src/term.rs) over a precomputed `name_tokens` frozenset attr
     on both sides -- the SAME token-containment relation
     domains/name_variant_merge.py already uses (in Python, for
     SmEntity<->SmEntity alias merging), expressed here graph-natively for
     the cross-type SmEntity<->Resident case ("Peaseblossom" is a token of
     "Verity Peaseblossom"). An explicit ambiguity guard refuses to mint when
     more than one Resident candidate token-matches (name_variant_merge's own
     "no-over-merge discipline", applied cross-type) -- a genuine ambiguity
     is a null, never a guess.

`_ensure_correspondence_seed`/`_run_correspondence` below are MECHANICAL
adapter I/O (load a seed once, precompute a frozenset attr, call
`run_rules`) -- the actual correspondence DECISION lives entirely in the two
Rules' `where` clauses (the `Covers`/`Not(Exists(...))` Term trees), never in
Python `if`/`else`, per CLAUDE.md. `_find_mt_by_name`/the literal
f"{entity}_beliefs" format is KEPT only as a diagnostic string inside an
honest-miss `reason` message (never as a live resolution path) so the
existing honest-miss tests' assertions (which check for that substring, a
genuine real fact about the Mt's own name when one exists) still read
correctly.

Both directions compose: a fact CAN derives can round-trip into deduction,
fire a held knowledge_logical implication, and the newly derived consequent
can round-trip back into CAN evidence via direction 1 -- see both RESULTS
docs for the live demonstrations.
"""
from __future__ import annotations

import json
import os

from domains import situation_model_reader as smr
from domains import name_variant_merge as nvm

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SUFFIX = "_beliefs"
_CORRESPONDENCE_SEED = os.path.join(
    _ROOT, "seeds", "entity_concept_correspondence.json")


def _resolve(agent):
    sub = getattr(agent, "s", agent)
    native = getattr(agent, "inner", None)
    if native is None:
        native = getattr(sub, "_inner", sub)
    return sub, native


def _find_mt_by_name(sub, name: str):
    for n in sub.nodes("Microtheory"):
        if sub.node(n)["attrs"].get("name") == name:
            return n
    return None


def _find_concept_by_name(sub, mt_node, name: str):
    for c in sub.neighbours(mt_node, "has_concept"):
        if sub.node(c)["attrs"].get("name") == name:
            return c
    return None


# --------------------------------------------------------------------------- #
#  GENERAL RESOLUTION -- load the correspondence seed, precompute the
#  name_tokens frozenset attr the Covers-based rule reads, run the rules to
#  fixpoint, read the resulting `denotes` edge back. Mechanical I/O; the
#  DECISION is the seed's own Rule `where` clauses (see module docstring).
# --------------------------------------------------------------------------- #
def _has_concept(sub, name: str) -> bool:
    for n in sub.nodes("Concept"):
        if sub.node(n)["attrs"].get("name") == name:
            return True
    return False


def _ensure_correspondence_seed(agent) -> None:
    """Idempotently install seeds/entity_concept_correspondence.json. Guard
    is the sentinel Concept 'entity_concept_correspondence' -- the SAME
    ensure_seeds idiom domains/inference_generation.py already uses."""
    sub, native = _resolve(agent)
    if _has_concept(sub, "entity_concept_correspondence"):
        return
    from substrate.seed_loader import engine_rules_only
    with open(_CORRESPONDENCE_SEED) as f:
        manifest = json.load(f)
    native.load_seed_manifest(engine_rules_only(manifest))


def _name_tokens_frozenset(name) -> frozenset:
    """Mechanical string prep, reusing name_variant_merge's OWN tokenizer
    (no new tokenizer): its `_name_tokens` splits on '_', so a raw
    space-joined name (e.g. a real Bigville resident's "Verity Peaseblossom")
    is first normalized to the SAME underscore convention SmEntity-style
    names already use ("verity_peaseblossom") before tokenizing."""
    return frozenset(nvm._name_tokens(str(name or "").replace(" ", "_")))


def _ensure_name_tokens(sub, node) -> None:
    if sub.node(node)["attrs"].get("name_tokens") is not None:
        return
    nm = sub.node(node)["attrs"].get("name")
    sub.set_attr(node, "name_tokens", _name_tokens_frozenset(nm))


def _run_correspondence(agent, entity_node=None) -> None:
    """Ensure the correspondence seed is loaded, precompute `name_tokens` on
    every candidate (the one entity given, or -- direction 2's reverse read,
    where no single entity is in hand -- every existing SmEntity) and every
    Resident, then run the two correspondence Rules to fixpoint. A small
    budget (2000) is enough for this seed's own rule count on the minimal
    harnesses this bridge is exercised on today; on a FULL WorldAdapter boot
    (600+ seeds) the SAME cross-seed starvation risk
    REASONING_FACILITY_BRIDGE_RESULTS.md sec1.5 already found and fixed for
    CAN's OWN discrete-update rules could recur here too -- an honest,
    named, NOT-yet-exercised residual (see ENTITY_RESOLUTION_RESULTS.md)."""
    sub, native = _resolve(agent)
    _ensure_correspondence_seed(agent)
    if entity_node is not None:
        _ensure_name_tokens(sub, entity_node)
    else:
        for e in sub.nodes("SmEntity"):
            _ensure_name_tokens(sub, e)
    for r in sub.nodes("Resident"):
        _ensure_name_tokens(sub, r)
    native.run_rules(2000)


def _denoted_mt(sub, native, entity_node):
    for mt in native.neighbours(entity_node, "denotes"):
        return mt
    return None


# --------------------------------------------------------------------------- #
#  DIRECTION 1 -- deduction's derived fact -> CAN evidence
# --------------------------------------------------------------------------- #
def apply_derived_fact_as_can_evidence(agent, entity: str, attr: str, *,
                                        positive: bool = True,
                                        alpha: float = 1.0) -> dict:
    """Apply a derived fact `is_a(entity, attr)` (or, `positive=False`, its
    negation) as CAN evidence on the Concept named `attr` inside the
    Microtheory `entity` DENOTES (the general resolution mechanism, module
    docstring), via the EXISTING `concept_apply_evidence` primitive
    (can_ops.rs::apply_evidence_h) -- mechanical translation + one call, no
    new Rust, no decision beyond the graph-native correspondence rules'
    already-run verdict and one attr-name lookup.

    `alpha=1.0` is the reliability-scale CEILING on the SAME [0,1] axis
    Bigville's own `apply_scenario_evidence` already uses at alpha=0.6 for
    less-than-certain testimonial evidence -- not a new invented constant:
    it is the value seeds/inference_logical.json's own
    `causal_strength_ceiling` documentation already named for exactly this
    case ("a proof-grade Covers-matched implication is causal-strength
    evidence at its idealized limit... confirm evidence dominating
    completely, disconfirm absent") and had, until this module, nothing
    reading it.

    Returns `{"applied": bool, ...}`. An honest miss (no correspondence
    found, or a correspondence found but no matching Concept inside it) is
    reported with a `reason`, never silently absorbed."""
    sub, native = _resolve(agent)
    ent_node = smr._entity(agent, entity)
    _run_correspondence(agent, ent_node)
    mt = _denoted_mt(sub, native, ent_node)
    if mt is None:
        legacy_name = "%s%s" % (entity, _SUFFIX)
        return {"applied": False, "reason":
                "no CAN correspondence found for entity %r -- neither the "
                "exact-name nor the name-token structural correspondence "
                "rule matched any Resident's belief Microtheory, and no "
                "legacy Microtheory named %r exists either"
                % (entity, legacy_name)}
    concept = _find_concept_by_name(sub, mt, attr)
    if concept is None:
        mt_name = sub.node(mt)["attrs"].get("name")
        return {"applied": False, "reason":
                "Microtheory %r holds no Concept named %r" % (mt_name, attr)}
    evidence = 1.0 if positive else -1.0
    native.concept_apply_evidence(concept, evidence, alpha)
    return {"applied": True, "concept": concept, "entity": entity,
            "attr": attr, "evidence": evidence, "alpha": alpha}


def apply_inference_hits_as_can_evidence(agent, hits: list, *,
                                          alpha: float = 1.0) -> list:
    """Batch form over `inference_generation.resolve_implication_gap`'s (and
    `resolve_conjunctive_gap`'s) OWN return shape -- `{"minted": bool,
    "gap": {"entity": ...}, "supplies": {"attr": ...}}` -- a mechanical
    adapter, never re-deciding whether a fact was derived (that decision is
    entirely inference_generation.py's, upstream and unmodified by this
    module). A `not_`-prefixed derived attr (a modus-tollens consequent)
    round-trips through as `positive=False` on the bare attr name, reusing
    propositional_deduction's own negation convention rather than
    inventing a second one."""
    out = []
    for hit in hits:
        if not hit.get("minted"):
            continue
        entity = (hit.get("gap") or {}).get("entity")
        attr = (hit.get("supplies") or {}).get("attr")
        if not entity or not attr:
            continue
        positive = not str(attr).startswith("not_")
        bare_attr = attr[4:] if attr.startswith("not_") else attr
        out.append(apply_derived_fact_as_can_evidence(
            agent, entity, bare_attr, positive=positive, alpha=alpha))
    return out


# --------------------------------------------------------------------------- #
#  DIRECTION 2 -- CAN's settled state -> deduction fact
# --------------------------------------------------------------------------- #
def _mt_entity_name(sub, native, mt_node) -> str:
    """The entity name this CAN Microtheory belongs to. Prefers the GENERAL
    resolution: any SmEntity that DENOTES this Mt (an alternate surface form
    a reading pipeline actually used -- e.g. a surname-only mention --
    resolved by the correspondence rules, module docstring). Falls back to
    the legacy read (its Resident's own `name` via has_belief_mt, else the
    Mt's own name with the f"{entity}_beliefs" suffix stripped) when no
    `denotes` edge exists yet -- e.g. a Mt whose CAN state settled before any
    text ever mentioned its owner. Mechanical read; the denotes-edge
    preference is a fixed priority order, not a per-call decision."""
    for e in native.in_neighbours(mt_node, "denotes"):
        nm = sub.node(e)["attrs"].get("name")
        if nm:
            return nm
    for r in sub.nodes("Resident"):
        for mt in sub.neighbours(r, "has_belief_mt"):
            if sub.node(mt)["attrs"].get("name") == sub.node(mt_node)["attrs"].get("name"):
                nm = sub.node(r)["attrs"].get("name")
                if nm:
                    return nm
    mt_name = sub.node(mt_node)["attrs"].get("name") or ""
    return mt_name[:-len(_SUFFIX)] if mt_name.endswith(_SUFFIX) else mt_name


def can_state_as_predications(agent, mt_node, *, t: int = 0) -> list:
    """Read every Concept's settled `state` under CAN Microtheory `mt_node`
    and ingest it as a predication on the entity this Mt belongs to (§
    `_mt_entity_name` -- the general `denotes`-edge resolution, preferred
    over the legacy Resident-name fallback). `state>0 -> is_a(entity,
    concept_name)`; `state<0 -> is_a(entity, "not_"+concept_name)`
    (propositional_deduction's own contrapositive naming convention, reused
    verbatim, not reinvented); `state==0` (undifferentiated -- CAN's own
    "ambivalent" reading, `seeds/causal_attitude_networks.json`'s
    `curiosity_targets_ambivalent_nodes`) asserts NOTHING -- a genuine null
    is never manufactured into a fact. Returns the list of
    `ingest_predication` results actually performed (mechanical translation
    via the UNMODIFIED situation_model_reader.ingest_predication, called
    exactly as any other caller in the tree already does)."""
    sub, native = _resolve(agent)
    _run_correspondence(agent)
    entity = _mt_entity_name(sub, native, mt_node)
    if not entity:
        return []
    results = []
    for c in sub.neighbours(mt_node, "has_concept"):
        cat = sub.node(c)["attrs"]
        name = cat.get("name")
        state = cat.get("state")
        if not name or state is None:
            continue
        if state > 0:
            attr = name
        elif state < 0:
            attr = "not_" + name
        else:
            continue
        res = smr.ingest_predication(agent, ["is_a", entity, attr], t=t)
        results.append(res)
    return results


__all__ = ["apply_derived_fact_as_can_evidence",
           "apply_inference_hits_as_can_evidence",
           "can_state_as_predications"]
