"""Tunable parameter — graph-resident introspection of agent-tunable knobs.

A TunableParameter node names one mutable attr on some owner node
(typically an Operation, sometimes a domain object like an
AcousticLexicon) that the agent's tuning Rules adjust. Together
they form a queryable catalog: walking has_tunable from any node
yields every knob the agent is allowed to learn on.

The TP carries the META — attr_name, min, max, step, description —
but not the tuning LOGIC. Logic stays in per-knob graph Rules that
read a metric and rewrite the attr. The TP is what makes the tuning
DISCOVERABLE and what gives the bounds + step a place to live as
graph data (so the agent can edit them too).

Pattern for adding a new tunable:
    install: mint a TunableParameter via mint_tunable(owner, ...).
    Rule 1 (raise): match (tp, names_attr_on, op); where the metric
        crosses its high band AND op.<attr> < tp.max; effect:
        op.<attr> += tp.step.
    Rule 2 (lower): mirror.
The Rule's match must reference the TP so the rule can read its
bounds + step from graph data rather than hardcoding them.

Replacing per-Rule Lit constants with Attr(tp, "step") /
Attr(tp, "max") makes the tuning surface fully editable as graph
data — the agent can tune the bounds themselves (rate-of-learning
meta-tuning) by editing the TP node's attrs.
"""
from __future__ import annotations


_TP_PRODUCTIONS = [
    # has_tunable from any owner that exposes tunable attrs. We
    # declare it for the two kinds we currently use; add more as
    # new ownership patterns arise.
    ("Operation", "has_tunable", "TunableParameter",
     "tunable_parameter:op_has_tunable"),
    ("AcousticLexicon", "has_tunable", "TunableParameter",
     "tunable_parameter:lex_has_tunable"),
]


def install_tunable_parameter(substrate) -> None:
    """Productions only — TP nodes themselves are minted by each
    domain's installer / attach helper."""
    for src_t, et, tgt_t, prov in _TP_PRODUCTIONS:
        try:
            substrate.add_production({
                "src": {"type": src_t, "var": "src"},
                "edge_type": et,
                "tgt": {"type": tgt_t, "var": "tgt"},
                "provenance": prov,
            })
        except Exception:
            pass


def mint_tunable(substrate, owner_nid, *,
                   attr_name: str,
                   min_value: float,
                   max_value: float,
                   step: float,
                   description: str = "") -> int:
    """Create a TunableParameter for `attr_name` on `owner_nid`.
    Returns the new node's id. Idempotent: if a TP with the same
    attr_name already exists on this owner, returns it instead of
    minting a duplicate."""
    for tp in substrate.neighbours(owner_nid, "has_tunable"):
        if substrate.node(tp)["attrs"].get("attr_name") == attr_name:
            return tp
    tp = substrate.add_node("TunableParameter", {
        "attr_name": attr_name,
        "min": float(min_value),
        "max": float(max_value),
        "step": float(step),
        "description": description,
    })
    substrate.add_edge(owner_nid, "has_tunable", tp)
    return tp


__all__ = [
    "install_tunable_parameter",
    "mint_tunable",
    "_TP_PRODUCTIONS",
]
