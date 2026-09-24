"""Graph-resident discourse state and communicative-goal lifecycle.

This module is deliberately a small state faculty, not a reply router.  It
records discourse events and goal ownership in the graph and validates goal
transitions against an explicit lifecycle.  Surface language, turn-taking,
and answer selection remain outside this module.

The state is event-compatible rather than turn-dependent: an event may be an
utterance, observation, action result, or repair signal, and a pending
expectation may be closed by a defer/error outcome without manufacturing a
reply.
"""
from __future__ import annotations

from typing import Any, Mapping


SCHEMA = "discourse_state.v1"
GOAL_SCHEMA = "communicative_goal_lifecycle.v1"

TERMINAL_GOAL_STATES = frozenset({"resolved", "blocked", "repaired", "abandoned"})

_ALLOWED = {
    "proposed": frozenset({"selected", "blocked", "abandoned"}),
    "selected": frozenset({"executing", "blocked", "repaired", "abandoned"}),
    "executing": frozenset({"resolved", "blocked", "repaired", "abandoned"}),
    "blocked": frozenset({"repaired", "abandoned"}),
    "repaired": frozenset(),
    "resolved": frozenset(),
    "abandoned": frozenset(),
}


def _edge(agent, source, edge_type, target):
    """Add an edge through the adapter's existing unchecked graph boundary."""
    try:
        agent.inner.add_edge_unchecked(source, edge_type, target, {})
    except TypeError:
        agent.inner.add_edge_unchecked(source, edge_type, target)


def _has_edge(agent, source, edge_type, target):
    return target in set(agent.inner.neighbours(source, edge_type))


def _unique_node(agent, node_type, key, value):
    for node in agent.s.nodes(node_type):
        if agent.s.node(node)["attrs"].get(key) == value:
            return node
    return None


def ensure_common_ground(agent, state, *, addressee=None, bind_state=True):
    """Return the graph-resident common-ground ledger for ``state``.

    The ledger is deliberately participant-linked rather than transcript
    text: events contribute claims/evidence to it, and an addressee scope is
    part of the grounding relation. This keeps common ground usable for
    asynchronous events as well as turn-compatible dialogue without leaking
    claims between addressed participants.
    """
    # A ledger is scoped to the participant pair when an addressee is known.
    # Older ledgers without scope metadata remain usable only as the explicit
    # shared ledger; they are never silently reused for a scoped event.
    scope_addressee = addressee
    scope_key = ("shared" if addressee is None else
                 "addressee:%s" % str(addressee))
    grounds = agent.inner.neighbours(state, "has_common_ground")
    ground = None
    for candidate in grounds:
        cattrs = agent.s.node(candidate)["attrs"]
        if cattrs.get("scope_key", "shared") == scope_key:
            ground = candidate
            break
    if ground is None:
        ground = agent.s.add_node("CommonGround", {
            "schema": "common_ground.v1",
            "revision": 0,
            "claims": [],
            "participants": [],
            "scope_key": scope_key,
            "scope_addressee": scope_addressee,
        })
        _edge(agent, state, "has_common_ground", ground)
    if addressee is not None:
        if bind_state:
            _edge(agent, state, "for_addressee", addressee)
        participants = list(agent.s.node(ground)["attrs"].get("participants") or [])
        if addressee not in participants:
            participants.append(addressee)
            agent.inner.set_attr(ground, "participants", participants)
        _edge(agent, ground, "about_addressee", addressee)
    return ground


def ensure_discourse_state(agent, *, conversation_id="default", addressee=None):
    """Return the graph's one state node for ``conversation_id``.

    All mutable discourse fields live on this node.  The helper is idempotent
    so save/load and repeated event ingestion do not create parallel states.
    """
    state = _unique_node(agent, "DiscourseState", "conversation_id",
                         conversation_id)
    if state is None:
        state = agent.s.add_node("DiscourseState", {
            "schema": SCHEMA,
            "conversation_id": conversation_id,
            "current_topic": None,
            "active_frame": None,
            "open_repair": None,
            "pending_expectation": None,
            "common_ground_delta": [],
            "commitments": [],
            "unresolved_residuals": [],
            "event_index": 0,
        })
    if not _has_edge(agent, agent.agent, "has_discourse_state", state):
        _edge(agent, agent.agent, "has_discourse_state", state)
    if addressee is not None:
        ensure_common_ground(agent, state, addressee=addressee)
    return state


def record_event(agent, state, *, kind, speaker=None, addressee=None,
                 topic=None, expectation=None, interaction_mode="event",
                 payload=None):
    """Record one event and update only state-local discourse fields."""
    attrs = agent.s.node(state)["attrs"]
    index = int(attrs.get("event_index", 0))
    event = agent.s.add_node("DiscourseEvent", {
        "schema": "discourse_event.v1",
        "event_index": index,
        "kind": str(kind),
        "interaction_mode": str(interaction_mode),
        "topic": topic,
        "expectation": expectation,
        "payload": dict(payload or {}),
    })
    _edge(agent, state, "has_event", event)
    if speaker is not None:
        _edge(agent, event, "from_speaker", speaker)
    if addressee is not None:
        _edge(agent, event, "to_addressee", addressee)
        # Event recipients are participants in the grounded discourse even
        # when the event is asynchronous or addressed to the agent itself.
        # Keep the state's conversational addressee stable; the event-level
        # recipient is carried by ``to_addressee`` and the common-ground
        # participant ledger.
        ensure_common_ground(agent, state, addressee=addressee,
                             bind_state=False)
    delta = (payload or {}).get("common_ground_delta")
    # Claim deltas belong to the event's addressed ledger.  Unaddressed
    # observations use the explicit shared ledger; they do not leak into a
    # participant-scoped ledger.
    ground = ensure_common_ground(agent, state, addressee=addressee,
                                  bind_state=False)
    if delta is not None:
        claims = list(agent.s.node(ground)["attrs"].get("claims") or [])
        claims.append(delta)
        agent.inner.set_attr(ground, "claims", claims)
        agent.inner.set_attr(ground, "revision",
                             int(agent.s.node(ground)["attrs"].get("revision", 0)) + 1)
        _edge(agent, event, "contributes_to_common_ground", ground)
    updates = {"event_index": index + 1}
    if topic is not None:
        updates["current_topic"] = topic
    if expectation is not None:
        updates["pending_expectation"] = expectation
    for key, value in updates.items():
        agent.inner.set_attr(state, key, value)
    return event


def open_goal(agent, state, *, kind, origin_event, addressee=None,
              evidence=None, next_action=None):
    """Mint a proposed graph goal linked to its discourse origin."""
    goal = agent.s.add_node("Goal", {
        "schema": GOAL_SCHEMA,
        "kind": str(kind),
        "status": "proposed",
        "lifecycle_status": "proposed",
        "origin_event": origin_event,
        "next_action": next_action,
        "outcome": None,
    })
    _edge(agent, state, "has_active_goal", goal)
    _edge(agent, goal, "originated_in", origin_event)
    if addressee is None:
        addressees = agent.inner.neighbours(state, "for_addressee")
        addressee = addressees[0] if addressees else None
    if addressee is not None:
        _edge(agent, goal, "for_addressee", addressee)
    if evidence is not None:
        _edge(agent, goal, "supported_by", evidence)
    return goal


def transition_goal(agent, goal, target, *, event=None, outcome=None,
                    next_action=None, repair=None):
    """Apply one guarded lifecycle transition and expose its provenance.

    Invalid transitions fail loudly and leave the graph untouched.  A terminal
    transition records outcome data and moves the goal from the state's active
    goal relation to its closed-goal relation; it does not delete history.
    """
    attrs = agent.s.node(goal)["attrs"]
    current = attrs.get("lifecycle_status", attrs.get("status"))
    target = str(target)
    if target not in _ALLOWED.get(current, frozenset()):
        raise ValueError(f"invalid goal lifecycle transition: {current}->{target}")
    agent.inner.set_attr(goal, "lifecycle_status", target)
    agent.inner.set_attr(goal, "status", target)
    if event is not None:
        agent.inner.set_attr(goal, "last_transition_event", event)
        _edge(agent, goal, "transitioned_by", event)
    if outcome is not None:
        agent.inner.set_attr(goal, "outcome", outcome)
    if next_action is not None:
        agent.inner.set_attr(goal, "next_action", next_action)
    if repair is not None:
        agent.inner.set_attr(goal, "repair", repair)
    if target in TERMINAL_GOAL_STATES:
        for state in agent.s.nodes("DiscourseState"):
            if _has_edge(agent, state, "has_active_goal", goal):
                agent.inner.remove_edge(state, "has_active_goal", goal)
                _edge(agent, state, "has_closed_goal", goal)
    return goal


def close_expectation(agent, state, *, event, disposition, residual=None):
    """Close an adjacency expectation without requiring a reply event.

    ``disposition`` is one of ``fulfilled``, ``deferred``, or ``error``.
    Deferred/error are explicit cognitive outcomes, not conversational filler.
    """
    if disposition not in {"fulfilled", "deferred", "error"}:
        raise ValueError(f"unknown expectation disposition: {disposition}")
    agent.inner.set_attr(state, "expectation_disposition", disposition)
    agent.inner.set_attr(state, "expectation_closed_by", event)
    agent.inner.set_attr(state, "pending_expectation", None)
    if residual is not None:
        values = list(agent.s.node(state)["attrs"].get("unresolved_residuals") or [])
        values.append(residual)
        agent.inner.set_attr(state, "unresolved_residuals", values)
