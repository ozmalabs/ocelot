"""relation_ingest — MECHANICAL adapter I/O: read the ROLE-CANONICAL RELATION
FRAME (seeds/relation_role_frame.json, graph data) and translate a domain's
role-keyed relations into positional tuples whose slots follow the Frame's
declared per-predicate role order.

ARCHITECTURE: this is admissible adapter work — translate external I/O (a domain
stated as {predicate: {role: filler}}) into the graph representation the held
AntiUnify Term consumes. It is NOT reasoning: it reads a DECLARED order from the
Frame and places each filler into its slot. No if/else over graph state, no
verdict, no decision. The MATCHING stays the held AntiUnify Term; this only fixes
the REPRESENTATION (consistent role-positioned tuples) so AntiUnify's positional
recursion aligns corresponding roles across domains under object renaming.

The convention (which role goes in which slot, consistently) lives in the Frame,
not here. If a relation's roles cannot be read from the stated input but would
need to be INFERRED, that is a HumanImpasse — this adapter does not infer roles.
"""
from __future__ import annotations
from typing import Any


def _schemas(agent) -> dict[str, list[str]]:
    """Read the Frame: {predicate -> declared role_order}. Mechanical graph read."""
    s = getattr(agent, "s", agent)
    out: dict[str, list[str]] = {}
    for n in s.nodes("RelationSchema"):
        a = s.node(n)["attrs"]
        pred = a.get("predicate")
        order = a.get("role_order")
        if pred and order:
            out[pred] = list(order)
    return out


def _order_relation(pred: str, role_args: dict[str, Any], schema: dict[str, list[str]]) -> tuple:
    """Place a relation's role-keyed args into the Frame's declared positional
    order. Higher-order args (whose filler is itself a relation tuple) are passed
    through recursively. Pure placement — no inference."""
    order = schema.get(pred)
    if order is None:
        # No declared schema -> NO canonical order is applied. The args are taken
        # in whatever order they were given (the Frame-OFF / unframed case). This
        # is not reasoning; it is the absence of the convention.
        vals = list(role_args.values())
    else:
        vals = [role_args[r] for r in order if r in role_args]
    placed = []
    for v in vals:
        if isinstance(v, dict) and "predicate" in v:        # nested relation filler
            placed.append(_order_relation(v["predicate"], v.get("args", {}), schema))
        else:
            placed.append(v)
    return tuple([pred] + placed)


def ingest_domain(agent, relations: list[dict], *, use_frame: bool = True) -> list[tuple]:
    """Translate a domain (list of {predicate, args:{role: filler}}) into positional
    relation tuples. With use_frame, slots follow the Frame's declared role order;
    without it, args are taken as given (the control). Mechanical I/O only."""
    schema = _schemas(agent) if use_frame else {}
    return [_order_relation(r["predicate"], r.get("args", {}), schema) for r in relations]
