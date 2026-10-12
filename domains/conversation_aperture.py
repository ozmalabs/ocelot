"""The conversation TURN RING: the reading aperture applied to dialogue.

Reading keeps a salience-ordered bounded buffer of N retained traces at its
current aperture and folds what falls out of the ring into lossy gists and
salience cells (domains/reading_scope.py `enforce_trace_buffer`; capacity from
the held `reading_derive_trace_capacity` Program over a per-register
ApertureBudget row). A conversation now does the same with its turns:

  * ATTENDED (full resolution): the last N concluded interlocutor turns keep
    their `agent received m` edge, so every rule that matches
    `["agent","received","m"]` sees the ring, not the whole session.
    N = reading_norms.effective_turn_capacity: the SAME Program over the
    conversational row's turn_capacity_* attrs, widened once under eviction
    pressure (rule `conversation_widen_turn_capacity_once`).
  * ARCHIVED: an evicted turn loses `received`, gains `agent remembers m`, and
    keeps every attr and edge (text, outcome, interprets, about_message ...),
    so concerns, replays and experiment judges still reach it.
  * SHAPE (conceptual): before a turn can leave the ring the graph has folded
    it into the conversation's TurnShape tier -- one node per turn class
    (e.g. an unanswered evidence signature, a reader-disagreement pair) with
    `has_member` / `first_member` edges -- and the history rules read the
    shape (seeds/unanswered_gap.json, seeds/comprehension_health.json).

This module is the mechanical driver only (the reading_scope twin): it never
decides what a turn means. Which turns are eligible, and their retention
salience, are graph data the seed rules write (`turn_salience`, set only once
the turn is concluded AND folded into its shapes); eviction order is
salience ascending, then age (node id) ascending -- exactly the reading ring's
order. A turn with no `turn_salience` yet is never evicted.
"""
from __future__ import annotations

from typing import Optional


def _ring(agent):
    """The singleton TurnRing node (seeds/conversation_turn_ring.json), or None."""
    try:
        for n in agent.inner.neighbours(agent.agent, "has_turn_ring"):
            if agent.s.has_node(n):
                return n
    except Exception:  # noqa: BLE001
        return None
    return None


def _policy_enabled(agent) -> bool:
    try:
        for n in agent.inner.neighbours(agent.agent, "has_turn_ring_policy"):
            if agent.s.has_node(n):
                return agent.s.node(n)["attrs"].get("enabled") == 1
    except Exception:  # noqa: BLE001
        return False
    return False


def attended_turns(agent) -> list:
    """(node, salience, age) for every attended interlocutor turn in the ring
    that the graph has made eligible (turn_salience set)."""
    out = []
    for m in agent.inner.neighbours(agent.agent, "received"):
        if not agent.s.has_node(m):
            continue
        at = agent.s.node(m)["attrs"]
        if at.get("from") != "interlocutor" or at.get("turn_salience") is None:
            continue
        out.append((m, float(at["turn_salience"]), int(m.value)))
    return out


def enforce_turn_buffer(agent, capacity: Optional[int] = None) -> list:
    """Bound the attended ring to `capacity` eligible turns (default: the held
    effective_turn_capacity). While over bound, evict the lowest-salience,
    oldest turn: remove `agent received m`, add `agent remembers m`, stamp
    turn_evicted=1 -- nothing else changes. Records eviction pressure on the
    TurnRing (reading_norms.record_eviction_pressure, the reading datum).
    Returns the evicted turns. A no-op unless the ring seed is loaded and its
    policy is enabled."""
    ring = _ring(agent)
    if ring is None or not _policy_enabled(agent):
        return []
    from domains import reading_norms as rn
    if capacity is None:
        widened = agent.s.node(ring)["attrs"].get("capacity_widened") == 1.0
        capacity = rn.effective_turn_capacity(agent, "conversational", widened=widened)
    evicted = []
    turns = attended_turns(agent)
    if len(turns) <= capacity:
        return evicted
    turns.sort(key=lambda t: (t[1], t[2]))          # salience asc, then age asc (oldest)
    for m, sal, _age in turns[:len(turns) - capacity]:
        try:
            agent.inner.remove_edge(agent.agent, "received", m)
            agent.inner.add_edge_unchecked(agent.agent, "remembers", m)
            agent.inner.set_attr(m, "turn_evicted", 1.0)
        except Exception:  # noqa: BLE001 -- a failed eviction leaves the turn attended
            continue
        # the turn's interpretations leave the attended set with it (rules that
        # match `agent holds_interpretation i` then see the ring's turns only);
        # the `interprets` edge stays, so the archive still reaches them
        try:
            for i in agent.inner.in_neighbours(m, "interprets"):
                if agent.inner.has_edge(agent.agent, "holds_interpretation", i):
                    agent.inner.remove_edge(agent.agent, "holds_interpretation", i)
                    agent.inner.add_edge_unchecked(agent.agent, "remembers_interpretation", i)
        except Exception:  # noqa: BLE001
            pass
        rn.record_eviction_pressure(agent.s, ring, sal)
        evicted.append(m)
    return evicted


__all__ = ["enforce_turn_buffer", "attended_turns"]
