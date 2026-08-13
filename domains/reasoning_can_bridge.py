"""reasoning_can_bridge -- ADDS a thin, naming-convention bridge between the
deduction facility (domains/propositional_deduction.py,
domains/inference_generation.py) and the native CAN belief-network facility
(seeds/can_native_reimplementation.json, worlds/bigville_can_beliefs.py). See
docs/research/engine_substrate/REASONING_FACILITY_BRIDGE_PREREG.md /
_RESULTS.md for the investigation this module is the outcome of.

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
     named `attr` inside the Microtheory named f"{entity}_beliefs" -- the
     SAME naming convention worlds/bigville_can_beliefs.build_resident_
     can_mt already uses (Microtheory{name: f"{resident_name}_beliefs"},
     Concept{name: <topic>}, topics like "world_safe"/"trust_mayor" being
     plain lowercase-underscore strings in the EXACT shape
     propositional_deduction._norm_attr already normalizes attr names into).

     THIS IS A NARROW, NAMING-CONVENTION BRIDGE, NOT GENERAL ENTITY
     RESOLUTION. `SmEntity` (deduction's open-vocabulary story/text referent
     pool) and `Concept` (CAN's pre-authored belief-network proposition
     pool, scoped per-believer Microtheory) are, per the investigation,
     genuinely disjoint node populations with no existing linking
     mechanism. This bridge works exactly when the deduction-side entity
     name and a CAN-network owner's name coincide (by construction, e.g. a
     Bigville resident's own name) -- it does not solve cross-
     representation coreference (e.g. "Tweety" vs "the bird" vs a
     resident's own name spelled differently), which remains real,
     unbuilt, and precisely sized in the RESULTS doc.

  2. CAN -> deduction fact (`can_state_as_predications`). A settled CAN
     Concept's discrete state becomes an is_a/not_ predication on the SAME
     entity name (read back off the Microtheory's own name, same
     convention, or its Resident via has_belief_mt when present), ingested
     through the UNMODIFIED situation_model_reader.ingest_predication --
     reusing propositional_deduction's OWN not_ prefix convention (already
     mechanically derived for modus tollens, propositional_deduction.py
     `_negate_attr`) for a negative (state==-1) reading, so this direction
     introduces NO new naming scheme either.

Both directions compose: a fact CAN derives can round-trip into deduction,
fire a held knowledge_logical implication, and the newly derived consequent
can round-trip back into CAN evidence via direction 1 -- see the RESULTS doc
for the live demonstration.
"""
from __future__ import annotations

from domains import situation_model_reader as smr

_SUFFIX = "_beliefs"


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
#  DIRECTION 1 -- deduction's derived fact -> CAN evidence
# --------------------------------------------------------------------------- #
def apply_derived_fact_as_can_evidence(agent, entity: str, attr: str, *,
                                        positive: bool = True,
                                        alpha: float = 1.0) -> dict:
    """Apply a derived fact `is_a(entity, attr)` (or, `positive=False`, its
    negation) as CAN evidence on the Concept named `attr` inside
    f"{entity}_beliefs"'s Microtheory, via the EXISTING
    `concept_apply_evidence` primitive (can_ops.rs::apply_evidence_h) --
    mechanical translation + one call, no new Rust, no decision beyond the
    two name lookups below.

    `alpha=1.0` is the reliability-scale CEILING on the SAME [0,1] axis
    Bigville's own `apply_scenario_evidence` already uses at alpha=0.6 for
    less-than-certain testimonial evidence -- not a new invented constant:
    it is the value seeds/inference_logical.json's own
    `causal_strength_ceiling` documentation already named for exactly this
    case ("a proof-grade Covers-matched implication is causal-strength
    evidence at its idealized limit... confirm evidence dominating
    completely, disconfirm absent") and had, until this module, nothing
    reading it.

    Returns `{"applied": bool, ...}`. An honest miss (no matching Mt, or no
    matching Concept inside it) is reported with a `reason`, never silently
    absorbed."""
    sub, native = _resolve(agent)
    mt_name = "%s%s" % (entity, _SUFFIX)
    mt = _find_mt_by_name(sub, mt_name)
    if mt is None:
        return {"applied": False, "reason":
                "no CAN Microtheory named %r -- no naming-convention "
                "correspondence found for entity %r" % (mt_name, entity)}
    concept = _find_concept_by_name(sub, mt, attr)
    if concept is None:
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
def _mt_entity_name(sub, mt_node) -> str:
    """The entity name this CAN Microtheory belongs to: its Resident's own
    `name` (has_belief_mt), when one exists, else the Mt's own name with the
    f"{entity}_beliefs" suffix stripped -- the SAME convention direction 1
    uses, read backwards. Mechanical read, not a decision."""
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
    `_mt_entity_name`). `state>0 -> is_a(entity, concept_name)`; `state<0 ->
    is_a(entity, "not_"+concept_name)` (propositional_deduction's own
    contrapositive naming convention, reused verbatim, not reinvented);
    `state==0` (undifferentiated -- CAN's own "ambivalent" reading,
    `seeds/causal_attitude_networks.json`'s `curiosity_targets_ambivalent_
    nodes`) asserts NOTHING -- a genuine null is never manufactured into a
    fact. Returns the list of `ingest_predication` results actually
    performed (mechanical translation via the UNMODIFIED
    situation_model_reader.ingest_predication, called exactly as any other
    caller in the tree already does)."""
    sub, _ = _resolve(agent)
    entity = _mt_entity_name(sub, mt_node)
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
