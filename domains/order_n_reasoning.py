"""order_n_reasoning — the agent's EXISTING order-N operator, applied to the
conversation's grounded KnownFact graph.

The conversation world (domains/conversation_world.py) answers a question by a
SINGLE-HOP graph match: find the one KnownFact whose bound slots equal the
question's bound slots, read the queried slot off it. That is order-1 — a
directly stored fact.

This module LIFTS the agent's order-N operator (domains/order_n_concepts.py —
the recursive iterate-to-N: apply a STEP N times; 0=value, 1=first difference,
2=second difference, …) from SIGNALS to RELATIONS. The same move
order_n_postulates.py made for KNOWLEDGE (order-0 postulate -> order-1
implication -> … -> order-N) is made here for FACTS:

  • order-1  = a directly stored KnownFact (the current behaviour).
  • order-2  = CHAIN two facts sharing an entity:
               love(agent=Mary, patient=John) + live_in(agent=John, location=Paris)
               => the location of Mary's-beloved = Paris  (composed on John).
  • order-N  = chain N facts.
  • transitive closure is the order-N of a transitive relation:
               bigger_than(cat,dog) + bigger_than(dog,mouse) => bigger_than(cat,mouse)
               (order-2); to depth N.

What is REUSED vs NEW (honest):
  • REUSED — the iterate-to-N STRUCTURE of order_n_concepts.nth_order_terms:
    "apply one STEP `order` times, each step consuming the prior result". Here
    `_compose_step` IS that step (the order_n_concepts step is `_minus` over a
    signal; this step is "follow one more relation edge / compose one more
    KnownFact"). `chain_to_order` is the literal analogue of `nth_order_terms`'s
    `for _ in range(order): t = step(t)` loop.
  • REUSED — order_n_postulates' SELECTOR-as-compression + recursive frontier +
    derivation-chain-as-graph-node (SynthesizedGap). Here the selector prefers
    the SHORTEST coherent chain (fewest hops that resolves the slot), and the
    chain is recorded as a ReasoningChain node carrying the composed facts + the
    hop count = the ORDER.
  • REUSED — order_n_postulates' N-SCALING: it differentiates order 0 -> 1 ->
    … -> max_order. Here N scales with the QUESTION — start at order-1, raise the
    order until the queried slot resolves or max_order / no-progress. Per memory
    [[ozma_order_n_analysis_by_synthesis]]: "n passes scaling to difficulty".
  • NEW glue — the relational-composition step itself (entity-sharing join over
    KnownFact role slots), the slot-resolution stop test, and the transitive
    specialisation. This is the world-side wiring of the operator onto the
    KnownFact graph; it is mechanical (a graph walk), holds no decisions beyond
    the operator's own moves (compose / select-shortest / stop).

STOP (honest): resolved | max_order | no-progress. No chain -> the caller emits
"I don't know" — no fabrication. The reasoning chain is inspectable graph data,
like the self-monitor's MonitorPass trace.

See [[ozma_order_n_concepts]] / [[ozma_order_n_analysis_by_synthesis]] /
[[ozma_meta_abilities_are_leverage]].
"""
from __future__ import annotations

from typing import Any, Optional

# Content roles a KnownFact stores (mirrors conversation_world._FACT_SLOTS,
# minus the event). Includes the oblique-proform roles (time/cause/manner) +
# the comparative `standard`.
_ROLE_SLOTS = ("agent", "patient", "location", "recipient",
               "instrument", "source", "beneficiary", "topic",
               "time", "cause", "manner", "standard")
try:
    from domains import interrogative_reference as _ireg
    _WH = _ireg.ALL_PLACEHOLDERS
except Exception:  # pragma: no cover - keep order_n usable standalone
    _WH = ("?WHO", "?WHAT", "?WHERE", "?WHEN", "?WHY", "?HOW")


# ---------------------------------------------------------------------------
# A fact, read off a KnownFact node — the order-0 datum.
# ---------------------------------------------------------------------------

def _fact_attrs(s, nid) -> dict[str, Any]:
    return dict(s.node(nid)["attrs"])


def _fact_str(s, nid) -> str:
    a = _fact_attrs(s, nid)
    ev = a.get("event", "?")
    parts = [f"{r}={a[r]}" for r in _ROLE_SLOTS if isinstance(a.get(r), str)]
    return f"{ev}({', '.join(parts)})"


def _entities(a: dict[str, Any]) -> set[str]:
    """The entities a fact mentions (its filled role fillers, not the event)."""
    return {a[r] for r in _ROLE_SLOTS
            if isinstance(a.get(r), str) and a[r] not in _WH}


# ---------------------------------------------------------------------------
# The order-N STEP — follow one more relation edge (compose one more fact).
#
# This is the literal analogue of order_n_concepts._minus: the order_n_concepts
# step takes a list of signal samples and returns adjacent differences; THIS
# step takes a frontier of partial chains and returns each extended by one
# entity-sharing fact. Iterating it `order` times is chain_to_order, exactly as
# `for _ in range(order): t = [_minus(...)]` is nth_order_terms.
# ---------------------------------------------------------------------------

class _Partial:
    """A partial reasoning chain: the facts composed so far, the running set of
    'reached' entities, and the hop count (= order so far)."""
    __slots__ = ("facts", "reached", "order")

    def __init__(self, facts: list, reached: set[str], order: int):
        self.facts = facts          # list of KnownFact node ids, in chain order
        self.reached = reached      # entities reachable through this chain
        self.order = order          # hops = number of facts composed


def _compose_step(s, partials: list["_Partial"], all_facts: list,
                  used_global: set) -> list["_Partial"]:
    """ONE order-step over the KnownFact relation graph: extend every partial
    chain by one fact that SHARES an entity with the chain's reached-set. This
    is 'follow one more relation edge'. Returns the new (longer) partials.

    Mirrors order_n_concepts._minus applied across a list: each input yields
    its order-(k+1) successors. A fact already in the chain is not re-used (so
    the iteration terminates), exactly as the order-N finite difference drops
    one element per order."""
    out: list[_Partial] = []
    for p in partials:
        for fid in all_facts:
            if fid in p.facts:
                continue
            a = _fact_attrs(s, fid)
            ents = _entities(a)
            # entity-sharing join: this fact connects iff it mentions an
            # entity the chain has already reached.
            if ents & p.reached:
                out.append(_Partial(
                    facts=p.facts + [fid],
                    reached=p.reached | ents,
                    order=p.order + 1))
    return out


def chain_to_order(s, seed_facts: list, order: int) -> list["_Partial"]:
    """Iterate the compose-step exactly `order-1` times from the seed facts —
    the iterate-to-N machine of order_n_concepts, with `_compose_step` as the
    step. order==1 returns the seeds themselves (a directly stored fact);
    order==k returns all k-fact entity-sharing chains.

    This is the structural reuse: order_n_concepts does
        t = samples; for _ in range(order): t = step(t)
    we do
        t = seeds;   for _ in range(order-1): t = compose_step(t)."""
    t = [_Partial(facts=[f], reached=_entities(_fact_attrs(s, f)), order=1)
         for f in seed_facts]
    for _ in range(max(0, order - 1)):
        t = _compose_step(s, t, list(s.nodes("KnownFact")), set())
        if not t:                       # no-progress stop
            break
    return t


# ---------------------------------------------------------------------------
# The SELECTOR + STOP — resolve a queried (entity, relation) by the SHORTEST
# coherent chain; raise the order until it resolves / max_order / no-progress.
# ---------------------------------------------------------------------------

def _chain_resolves(s, p: "_Partial", queried_relation: str,
                    queried_slot: str, anchor_entity: str,
                    anchor_slot: str) -> Optional[dict[str, Any]]:
    """Does this composed chain answer the question? The LAST fact in the chain
    must instantiate the queried relation and fill the queried slot; the chain
    must START from the anchor entity. Returns the resolution dict or None.

    The 'queried relation' is the event the question asks about (e.g. live_in);
    the 'anchor' is the entity the question grounds out from (e.g. Mary). The
    chain composes anchor -> … -> a fact of the queried relation whose queried
    slot is the answer."""
    if not p.facts:
        return None
    # must originate at the anchor entity in its anchor slot.
    first = _fact_attrs(s, p.facts[0])
    if anchor_slot and first.get(anchor_slot) != anchor_entity:
        return None
    if anchor_entity not in _entities(first):
        return None
    last = _fact_attrs(s, p.facts[-1])
    if queried_relation and last.get("event") != queried_relation:
        return None
    val = last.get(queried_slot)
    if not isinstance(val, str) or val in _WH:
        return None
    return {"answer": val, "queried_slot": queried_slot,
            "queried_relation": queried_relation,
            "order": p.order,
            "facts": list(p.facts),
            "chain_str": " ⇒ ".join(_fact_str(s, f) for f in p.facts)}


def reason(s, anchor_entity: str, queried_relation: str, queried_slot: str,
           anchor_slot: str = "agent", max_order: int = 4,
           record: bool = True, jrol_patience: Optional[int] = None,
           progress_trace: Optional[list] = None) -> Optional[dict[str, Any]]:
    """Order-N inference over the KnownFact graph: find the SHORTEST chain that
    composes a fact of `queried_relation` (reading the answer off `queried_slot`)
    reachable from `anchor_entity`. N scales with the question: try order 1,
    then 2, … up to max_order, stopping at the FIRST order that resolves (the
    shortest-chain selector = compression). Returns the resolution + records a
    ReasoningChain node, or None ("I don't know") if nothing resolves.

    `max_order` is DYNAMIC — the caller (domains.dynamic_depth) sets it from the
    query's relevance budget, so a high-relevance question dives deep and a
    low-relevance one is capped at order-1.

    `jrol_patience` is the PERSEVERANCE cutoff (the taught perseverance_stage):
    when set, the dive ABANDONS early after this many consecutive order-steps
    that added NO new compositions (RATE of progress ~ 0, 'going nowhere'), even
    if max_order is not exhausted — instead of running a dead dive to the cap.
    None -> the legacy behaviour (stop only when the chain set stops growing,
    == jrol_patience 1). `progress_trace`, when a list is passed, is filled with
    a per-order {order, chains, progressed, stop?} record (the jROL derivative),
    so the caller can report WHY it stopped.

    HONEST: no chain -> None. No fabrication. The order it resolves at is the
    hop depth, embodying 'n scales with difficulty'."""
    patience = 1 if jrol_patience is None else max(1, int(jrol_patience))
    seeds = list(s.nodes("KnownFact"))
    if not seeds:
        return None
    prev_count = -1
    no_progress_run = 0
    for order in range(1, max_order + 1):
        chains = chain_to_order(s, seeds, order)
        if not chains:
            if progress_trace is not None:
                progress_trace.append({"order": order, "chains": 0,
                                       "progressed": False,
                                       "stop": "no_chain"})
            break                       # no-progress stop
        # shortest-chain selector: at the FIRST order that yields a resolution,
        # take it (and the cheapest among ties by fact count, already == order).
        resolved = [r for r in
                    (_chain_resolves(s, p, queried_relation, queried_slot,
                                     anchor_entity, anchor_slot)
                     for p in chains) if r]
        if resolved:
            best = min(resolved, key=lambda r: r["order"])
            best["max_order_reached"] = order
            if progress_trace is not None:
                progress_trace.append({"order": order, "chains": len(chains),
                                       "progressed": True, "stop": "resolved"})
            if record:
                best["node"] = _record_chain(s, best)
            return best
        # jROL perseverance: did the chain SET grow this step (a new usable
        # composition = progress)? Abandon after `patience` no-growth steps.
        progressed = len(chains) > prev_count
        if progress_trace is not None:
            progress_trace.append({"order": order, "chains": len(chains),
                                   "progressed": progressed})
        if progressed:
            no_progress_run = 0
        else:
            no_progress_run += 1
            if no_progress_run >= patience:
                if progress_trace is not None and progress_trace:
                    progress_trace[-1]["stop"] = "no_progress"
                break               # going nowhere -> abandon early
        prev_count = len(chains)
    return None


# ---------------------------------------------------------------------------
# Transitive specialisation — the order-N of a single transitive relation.
# bigger_than(cat,dog)+bigger_than(dog,mouse) => bigger_than(cat,mouse) etc.
# This is reason() restricted to one relation chained source-slot -> via a
# shared middle entity, with the QUESTION asking "is A R B?" (a yes/no), so the
# 'queried slot' is the chain's far end matching the asked target.
# ---------------------------------------------------------------------------

def reason_transitive(s, relation: str, subject: str, obj: str,
                      left_slot: str = "agent", right_slot: str = "patient",
                      max_order: int = 5, record: bool = True
                      ) -> Optional[dict[str, Any]]:
    """Transitive-closure inference: is `subject R obj` derivable by chaining
    `relation` facts subject -> … -> obj through shared middles? Each hop joins
    fact[i].right_slot == fact[i+1].left_slot. Returns the resolution (yes, with
    the chain + order) or None (not derivable -> honest 'I don't know').

    The order = number of `relation` facts composed; a direct stored
    bigger_than(cat,mouse) resolves at order-1, the two-hop derivation at
    order-2 — N again scaling with difficulty."""
    rel_facts = [f for f in s.nodes("KnownFact")
                 if _fact_attrs(s, f).get("event") == relation]
    if not rel_facts:
        return None
    # seeds: facts whose left_slot is the subject.
    seeds = [_Partial(facts=[f], reached={_fact_attrs(s, f).get(right_slot)},
                      order=1)
             for f in rel_facts
             if _fact_attrs(s, f).get(left_slot) == subject]
    prev_count = -1
    frontier = seeds
    for order in range(1, max_order + 1):
        # check resolution at this order: any chain whose last fact's right end
        # is the object.
        resolved = []
        for p in frontier:
            last = _fact_attrs(s, p.facts[-1])
            if last.get(right_slot) == obj:
                resolved.append({
                    "answer": "yes", "relation": relation,
                    "subject": subject, "object": obj,
                    "order": p.order, "facts": list(p.facts),
                    "chain_str": " ⇒ ".join(_fact_str(s, f) for f in p.facts),
                    "queried_relation": relation,
                    "queried_slot": right_slot})
        if resolved:
            best = min(resolved, key=lambda r: r["order"])
            best["max_order_reached"] = order
            if record:
                best["node"] = _record_chain(s, best)
            return best
        # extend each chain by one relation-fact whose left end == the chain's
        # current right end (the transitive join).
        nxt: list[_Partial] = []
        for p in frontier:
            right = _fact_attrs(s, p.facts[-1]).get(right_slot)
            for f in rel_facts:
                if f in p.facts:
                    continue
                a = _fact_attrs(s, f)
                if a.get(left_slot) == right:
                    nxt.append(_Partial(facts=p.facts + [f],
                                        reached=p.reached | {a.get(right_slot)},
                                        order=p.order + 1))
        if not nxt or len(nxt) == prev_count:
            break                       # no-progress stop
        prev_count = len(nxt)
        frontier = nxt
    return None


# ---------------------------------------------------------------------------
# Record the chain as graph data — inspectable, like a MonitorPass trace.
# ---------------------------------------------------------------------------

def _record_chain(s, res: dict[str, Any]):
    """Mint the order-N inference as a ReasoningChain node carrying the composed
    facts (composed_fact edges, in order) + the hop count = order. Returns the
    node id. Best-effort productions, the same idiom conversation_world uses."""
    try:
        s.add_production({
            "src": {"type": "ReasoningChain", "var": "a"},
            "edge_type": "composed_fact",
            "tgt": {"type": "KnownFact", "var": "b"},
            "where": None,
            "weight": {"type": "Lit", "value": 1.0},
            "provenance": "order_n_reasoning:composed_fact"})
    except Exception:
        pass
    rc = s.add_node("ReasoningChain", {
        "answer": res["answer"],
        "order": res["order"],
        "hops": res["order"],
        "queried_relation": res.get("queried_relation", ""),
        "queried_slot": res.get("queried_slot", ""),
        "chain": res["chain_str"],
        "origin": "order_n_reasoning",
        "operator": "order_n_concepts.iterate_to_N (lifted to relations)",
        "composed_by": "agent",
    })
    for i, fid in enumerate(res["facts"]):
        try:
            s.add_edge(rc, "composed_fact", fid, {"hop": i})
        except Exception:
            pass
    return rc


__all__ = ["reason", "reason_transitive", "chain_to_order"]
