"""Reconsider — substrate-level budget loop.

The bare-Substrate analogue of CuriousAgent's reconsider machinery.
Each Capability declares a `tick_budget_ms`; when the world adapter
reports a per-tick wall-cost above that budget, the Reconsider Rule
flips the Capability's `mode` to a cheaper alternative ("passive").
When cost drops well below budget, the reverse Rule flips back to
"active".

Domain Rules opt into regulation by adding a `regulated_by` edge
from one of their match-clause nodes to a Capability, and a
where-clause gate `cap.mode == "active"` (or whatever modes the
domain defines). The substrate, not the domain, decides when to
throttle.

Singletons:
  SubstrateRoot — one per substrate, carries substrate-wide attrs
    (last_tick_ms, tick_count). World adapters call
    `ensure_substrate_root` and write per-tick wall-time after
    each `sub.tick()`.
  Capability — per regulated subsystem. World adapters / seeds
    call `ensure_capability` to declare them with budget + initial
    mode.

This module ONLY ships the productions + the two Reconsider Rules
+ the helper functions. No domain knowledge — chunking et al wire
themselves to a Capability of their choosing.
"""
from __future__ import annotations


_RECONSIDER_PRODUCTIONS = [
    # SubstrateRoot ↔ Capability ownership.
    ("SubstrateRoot", "has_capability", "Capability",
     "reconsider:root_has_capability"),
    # Domains tag their lex / op / config nodes with regulated_by
    # to opt into mode-gating. Declare the kinds that currently
    # subscribe; add more as new ones land.
    ("AcousticLexicon", "regulated_by", "Capability",
     "reconsider:lex_regulated_by_capability"),
    ("Operation", "regulated_by", "Capability",
     "reconsider:op_regulated_by_capability"),
    # Assessment — agent's reasoned diagnosis when first-line
    # responses (mode flip) don't resolve compute pressure. Names
    # a cause + recommended_action; an apply Rule reads the
    # recommendation and takes the targeted action.
    ("Capability", "has_assessment", "Assessment",
     "reconsider:cap_has_assessment"),
]


def _enc(v):
    from substrate_rs import Term
    if isinstance(v, Term):
        return {"__term__": v.to_dict()}
    return v


def _reconsider_throttle_rule() -> dict:
    """When per-tick cost exceeds the Capability's budget AND mode
    is currently "active", flip to "passive" — and snapshot the
    lex's n_signs so the release rule can tell whether learning
    has actually progressed since."""
    from substrate_rs import And, Attr, Eq, Gt, Lit, Var
    where = And(items=(
        Eq(a=Attr(Var("cap"), "mode"), b=Lit("active")),
        Gt(a=Attr(Var("root"), "last_tick_ms"),
           b=Attr(Var("cap"), "tick_budget_ms")),
    ))
    return {
        "id": "reconsider_throttle",
        "match": [
            ["root", "has_capability", "cap"],
            ["lex", "regulated_by", "cap"],
        ],
        "where": where.to_dict(),
        "effect": [
            ["set_attr", "cap", "mode", "passive"],
            ["set_attr", "cap", "throttled_at_tick_ms",
             _enc(Attr(Var("root"), "last_tick_ms"))],
            ["set_attr", "cap", "signs_at_throttle",
             _enc(Attr(Var("lex"), "n_signs"))],
        ],
    }


def _reconsider_release_rule() -> dict:
    """Release back to "active" only when BOTH (a) the per-tick
    cost is well under budget AND (b) something has changed since
    throttle — n_signs has grown, meaning there's new learning
    material to chew on. Without (b) the agent would oscillate:
    passive ticks are always cheap, so the agent would always
    retry, only to immediately re-throttle on the next expensive
    active tick."""
    from substrate_rs import (
        And, Attr, Div, Eq, Gt, Lit, Lt, Var,
    )
    where = And(items=(
        Eq(a=Attr(Var("cap"), "mode"), b=Lit("passive")),
        Lt(a=Attr(Var("root"), "last_tick_ms"),
           b=Div(a=Attr(Var("cap"), "tick_budget_ms"),
                   b=Lit(4))),
        Gt(a=Attr(Var("lex"), "n_signs"),
           b=Attr(Var("cap"), "signs_at_throttle")),
    ))
    return {
        "id": "reconsider_release",
        "match": [
            ["root", "has_capability", "cap"],
            ["lex", "regulated_by", "cap"],
        ],
        "where": where.to_dict(),
        "effect": [
            ["set_attr", "cap", "mode", "active"],
            ["set_attr", "cap", "released_at_tick_ms",
             _enc(Attr(Var("root"), "last_tick_ms"))],
        ],
    }


# Assessment thresholds. When mode is already passive but cost
# still exceeds budget AND the substrate has accumulated enough
# bigrams (proxy for follows-pile size, since compose walks both),
# the agent's diagnose Rule mints an Assessment fingering
# compose's match-enumeration as the cause and recommending
# escalation to mode=off. The pile is "substantial" earlier than
# you'd think — compose's O(follows × compositional_signs) cost
# starts hurting around a few thousand follows edges, which means
# ~50 bigrams (signs participate in roughly 30 bigrams each
# during the early growth phase).
_ASSESS_BIGRAM_PILE_THRESHOLD = 30


def _assess_compose_pressure_rule() -> dict:
    """Multi-variable diagnose: mode already passive, tick cost
    still > budget, bigram pile substantial. Mints an Assessment
    explicitly naming the cause + recommending the targeted
    action — the agent reasoning about why the first response
    didn't work and what to try next.

    Dedup via cap.has_assessment cardinality: if there's already
    an active Assessment of this kind, don't mint a duplicate."""
    from substrate_rs import (
        And, Attr, Count, Eq, Exists, Filter, Gt, Gte, Lit, Neighbours,
        Var, Not,
    )
    n_bigrams = Count(source=Neighbours(Var("lex"), "tracks_bigram"))
    existing_assessment = Exists(
        source=Neighbours(Var("cap"), "has_assessment"),
        var_name="a",
        predicate=Eq(a=Attr(Var("a"), "kind"),
                       b=Lit("compute_pressure")),
    )
    where = And(items=(
        Eq(a=Attr(Var("cap"), "mode"), b=Lit("passive")),
        Gt(a=Attr(Var("root"), "last_tick_ms"),
           b=Attr(Var("cap"), "tick_budget_ms")),
        Gte(a=n_bigrams, b=Lit(_ASSESS_BIGRAM_PILE_THRESHOLD)),
        Not(arg=existing_assessment),
    ))
    return {
        "id": "assess_compose_pressure",
        "match": [
            ["root", "has_capability", "cap"],
            ["lex", "regulated_by", "cap"],
        ],
        "where": where.to_dict(),
        "effect": [
            ["add_node", "a", "Assessment", {
                "kind": "compute_pressure",
                "cause": "follows_pile_unbounded",
                "recommended_action": "escalate_to_off",
                "tick_ms_at_diagnosis": _enc(Attr(Var("root"), "last_tick_ms")),
                "signs_at_diagnosis": _enc(Attr(Var("lex"), "n_signs")),
            }],
            ["add_edge", "cap", "has_assessment", "a"],
        ],
    }


def _act_on_assessment_rule() -> dict:
    """Read an Assessment's recommended_action and apply it.
    Targeted intervention; the Assessment itself remains as a
    graph-resident record of why the action was taken (and the
    recovery rule reads it to decide when to revert)."""
    from substrate_rs import And, Attr, Eq, Lit, Not, Var
    where = And(items=(
        Eq(a=Attr(Var("a"), "recommended_action"),
           b=Lit("escalate_to_off")),
        Not(arg=Eq(a=Attr(Var("a"), "acted_on"), b=Lit(True))),
    ))
    return {
        "id": "act_on_assessment_escalate",
        "match": [["cap", "has_assessment", "a"]],
        "where": where.to_dict(),
        "effect": [
            ["set_attr", "cap", "mode", "off"],
            ["set_attr", "a", "acted_on", True],
        ],
    }


def _escalate_to_utterance_pile_rule() -> dict:
    """Second-level diagnose: when the first Assessment
    (follows_pile_unbounded) has already been acted on AND cost is
    STILL above budget, the substrate's stream-data accumulation
    (Utterances + their attached intermediate data) is the deeper
    cause. Mint Assessment(cause="utterance_pile_unbounded") so
    the broader GC Rule can fire."""
    from substrate_rs import (
        And, Attr, Eq, Exists, Gt, Lit, Neighbours, Not, Var,
    )
    already_follows = Exists(
        source=Neighbours(Var("cap"), "has_assessment"),
        var_name="a1",
        predicate=And(items=(
            Eq(a=Attr(Var("a1"), "cause"),
               b=Lit("follows_pile_unbounded")),
            Eq(a=Attr(Var("a1"), "acted_on"), b=Lit(True)),
        )),
    )
    already_utts = Exists(
        source=Neighbours(Var("cap"), "has_assessment"),
        var_name="a2",
        predicate=Eq(a=Attr(Var("a2"), "cause"),
                      b=Lit("utterance_pile_unbounded")),
    )
    where = And(items=(
        Gt(a=Attr(Var("root"), "last_tick_ms"),
           b=Attr(Var("cap"), "tick_budget_ms")),
        already_follows,
        Not(arg=already_utts),
    ))
    return {
        "id": "escalate_to_utterance_pile",
        "match": [
            ["root", "has_capability", "cap"],
            ["lex", "regulated_by", "cap"],
        ],
        "where": where.to_dict(),
        "effect": [
            ["add_node", "a", "Assessment", {
                "kind": "compute_pressure",
                "cause": "utterance_pile_unbounded",
                "recommended_action": "gc_utterances",
                "tick_ms_at_diagnosis": _enc(Attr(Var("root"), "last_tick_ms")),
                "signs_at_diagnosis": _enc(Attr(Var("lex"), "n_signs")),
            }],
            ["add_edge", "cap", "has_assessment", "a"],
        ],
    }


def _recover_from_assessment_rule() -> dict:
    """When learning has clearly resumed (n_signs grew by ≥15
    since the Assessment was authored), the cause it diagnosed no
    longer applies. Delete the Assessment + return mode to active
    so the agent gives the full pipeline another shot.

    Threshold is conservative: every off→active transition has to
    rebuild the follows pile until it hits compose pressure again,
    so we want long off periods relative to short active bursts.
    """
    from substrate_rs import (
        And, Attr, Eq, Gte, Lit, Minus, Var,
    )
    where = And(items=(
        Eq(a=Attr(Var("a"), "kind"), b=Lit("compute_pressure")),
        Gte(a=Minus(a=Attr(Var("lex"), "n_signs"),
                      b=Attr(Var("a"), "signs_at_diagnosis")),
            b=Lit(15)),
    ))
    return {
        "id": "recover_from_assessment",
        "match": [
            ["cap", "has_assessment", "a"],
            ["lex", "regulated_by", "cap"],
        ],
        "where": where.to_dict(),
        "effect": [
            ["set_attr", "cap", "mode", "active"],
            ["del_node", "a"],
        ],
    }


def install_reconsider(substrate) -> None:
    """Productions + the two Reconsider Rules. Singleton
    SubstrateRoot + Capability nodes are minted lazily via
    ensure_substrate_root / ensure_capability."""
    for src_t, et, tgt_t, prov in _RECONSIDER_PRODUCTIONS:
        try:
            substrate.add_production({
                "src": {"type": src_t, "var": "src"},
                "edge_type": et,
                "tgt": {"type": tgt_t, "var": "tgt"},
                "provenance": prov,
            })
        except Exception:
            pass
    for builder in (_reconsider_throttle_rule,
                     _reconsider_release_rule,
                     _assess_compose_pressure_rule,
                     _act_on_assessment_rule,
                     _escalate_to_utterance_pile_rule,
                     _recover_from_assessment_rule):
        substrate.add_node("Rule", builder())


def ensure_substrate_root(substrate):
    """Find or create the SubstrateRoot singleton. World adapters
    call this on startup so the Reconsider Rule has an anchor."""
    for n in substrate.nodes("SubstrateRoot"):
        return n
    return substrate.add_node("SubstrateRoot", {
        "last_tick_ms": 0.0,
        "tick_count": 0,
    })


def ensure_capability(substrate, root, *, name,
                        tick_budget_ms: float, mode: str = "active"):
    """Find or create a Capability with the given name + budget on
    the given root. Returns the Capability node id."""
    for cap in substrate.neighbours(root, "has_capability"):
        if substrate.node(cap)["attrs"].get("name") == name:
            return cap
    cap = substrate.add_node("Capability", {
        "name": name,
        "mode": mode,
        "tick_budget_ms": float(tick_budget_ms),
    })
    substrate.add_edge(root, "has_capability", cap)
    return cap


__all__ = [
    "install_reconsider",
    "ensure_substrate_root",
    "ensure_capability",
    "_RECONSIDER_PRODUCTIONS",
]
