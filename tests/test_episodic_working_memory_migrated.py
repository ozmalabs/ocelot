"""Focused gates for executable episodic and working memory.

The test only supplies mechanically translated observations, requests, clocks,
and gate commands.  All binding, retrieval, replay, consolidation,
reconsolidation, capacity decisions, interference and expiry run as Rust-
executed graph Rules from ``episodic_working_memory_core``.
"""
from __future__ import annotations

import pytest

pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter


def _fresh():
    return WorldAdapter(seeds=("episodic_working_memory_core",))


def _edge(agent, src, edge_type, tgt):
    try:
        agent.inner.add_edge_unchecked(src, edge_type, tgt, {})
    except TypeError:
        agent.inner.add_edge_unchecked(src, edge_type, tgt)


def _nodes(agent, node_type):
    return [
        node
        for node in agent.s.nodes()
        if agent.s.node(node)["type"] == node_type
    ]


def _attrs(agent, node):
    return agent.s.node(node)["attrs"]


def _experience(
    agent,
    *,
    event_key,
    cue_key,
    context_key="doom-room",
    schema_name="door_affordance",
    epoch=1.0,
    salience=0.5,
    surprise=0.5,
    value=0.5,
    provenance_kind="perceived",
    state_kind="world_state",
    state_summary="experienced world state",
):
    context = agent.s.add_node("MemoryContext", {"context_key": context_key})
    schema = agent.s.add_node("MemorySchema", {"name": schema_name})
    event = agent.s.add_node(
        "EpisodicEvent",
        {
            "event_key": event_key,
            "cue_key": cue_key,
            "epoch": float(epoch),
            "salience": float(salience),
            "surprise": float(surprise),
            "value": float(value),
            "observation_status": "observed",
            "provenance_kind": provenance_kind,
            "state_kind": state_kind,
            "state_summary": state_summary,
        },
    )
    _edge(agent, agent.agent, "experienced_event", event)
    _edge(agent, event, "in_context", context)
    _edge(agent, event, "instantiates_schema", schema)
    return event, context, schema


def _retrieval(agent, cue_key, epoch):
    request = agent.s.add_node(
        "MemoryRetrievalRequest",
        {"status": "pending", "cue_key": cue_key, "epoch": float(epoch)},
    )
    _edge(agent, agent.agent, "has_memory_retrieval_request", request)
    return request


def _cycle(agent, epoch, mode="wake"):
    cycle = agent.s.add_node(
        "MemoryCycle",
        {"status": "pending", "mode": mode, "epoch": float(epoch)},
    )
    _edge(agent, agent.agent, "has_memory_cycle", cycle)
    return cycle


def _gate(
    agent,
    operation,
    epoch,
    *,
    content=None,
    slot=None,
    task="doom",
    priority=0.5,
):
    gate = agent.s.add_node(
        "WorkingMemoryGate",
        {
            "status": "pending",
            "operation": operation,
            "epoch": float(epoch),
            "task_context_key": task,
            "priority": float(priority),
        },
    )
    _edge(agent, agent.agent, "has_working_memory_gate", gate)
    if content is not None:
        _edge(agent, gate, "targets_content", content)
    if slot is not None:
        _edge(agent, gate, "targets_slot", slot)
    return gate


def _clock(agent, epoch):
    clock = agent.s.add_node("MemoryClock", {"epoch": float(epoch)})
    _edge(agent, agent.agent, "has_memory_clock", clock)
    return clock


def test_seed_is_dormant_and_does_not_mint_memory_without_input():
    agent = _fresh()

    assert len(_nodes(agent, "EpisodicMemoryPolicy")) == 1
    assert len(_nodes(agent, "WorkingMemoryPolicy")) == 1
    before = len(agent.s.nodes())
    assert agent.tick() == 0
    assert agent.tick() == 0
    assert len(agent.s.nodes()) == before


def test_observed_event_is_bound_once_with_context_and_nonobserved_provenance():
    agent = _fresh()
    event, context, schema = _experience(
        agent,
        event_key="opened-door-1",
        cue_key="door",
        epoch=7,
        salience=0.8,
        surprise=0.9,
        value=0.7,
    )

    assert agent.tick() > 0
    episodes = _nodes(agent, "Episode")
    assert len(episodes) == 1
    episode = episodes[0]
    attrs = _attrs(agent, episode)
    assert attrs["episode_key"] == "opened-door-1"
    assert attrs["context_key"] == "doom-room"
    assert attrs["provenance_kind"] == "episodic_trace"
    assert attrs["observation_status"] == "not_observed"
    assert list(agent.inner.neighbours(episode, "bound_event")) == [event]
    assert list(agent.inner.neighbours(episode, "in_context")) == [context]
    assert list(agent.inner.neighbours(episode, "instantiates_schema")) == [
        schema
    ]

    # Fixed-point and later ticks cannot bind the same observed event twice.
    count = len(agent.s.nodes())
    assert agent.tick() == 0
    assert len(_nodes(agent, "Episode")) == 1
    assert len(agent.s.nodes()) == count


def test_legacy_memory_rules_defer_rich_episode_consolidation_to_replay():
    agent = WorldAdapter(
        seeds=("memory_core", "episodic_working_memory_core")
    )
    agent.inner.set_attr(agent.agent, "tick", 100.0)
    agent.inner.set_attr(agent.agent, "episode_consolidation_age", 1.0)
    _experience(
        agent,
        event_key="rich-event",
        cue_key="rich-cue",
        epoch=1,
        salience=2.0,
        surprise=1.0,
        value=1.0,
    )

    agent.tick()
    episode = _nodes(agent, "Episode")[0]

    assert _attrs(agent, episode)["memory_architecture"] == (
        "episodic_working_memory_v1"
    )
    assert _attrs(agent, episode)["consolidated"] is False
    assert _nodes(agent, "SemanticSupport") == []

    _cycle(agent, 101, "offline")
    agent.tick()
    assert _attrs(agent, episode)["consolidated"] is True
    assert len(_nodes(agent, "SemanticSupport")) == 1


def test_imagined_recalled_and_predicted_material_cannot_launder_as_episode():
    agent = _fresh()
    for index, provenance in enumerate(("imagined", "recalled", "predicted")):
        event, _, _ = _experience(
            agent,
            event_key=f"spoof-{index}",
            cue_key=f"spoof-{index}",
            provenance_kind=provenance,
        )
        # Even a malformed upstream node claiming it was observed is rejected
        # because admission requires a grounded/perceived evidence lineage.
        assert _attrs(agent, event)["observation_status"] == "observed"

    agent.tick()

    assert _nodes(agent, "Episode") == []

    _experience(
        agent,
        event_key="grounded-event",
        cue_key="grounded",
        provenance_kind="grounded",
    )
    agent.tick()
    assert len(_nodes(agent, "Episode")) == 1


def test_overlapping_cues_remain_separate_and_lower_completion_confidence():
    agent = _fresh()
    _experience(agent, event_key="door-a", cue_key="door", context_key="room-a")
    _experience(agent, event_key="door-b", cue_key="door", context_key="room-b")

    agent.tick()

    episodes = _nodes(agent, "Episode")
    assert len(episodes) == 2
    assert {_attrs(agent, ep)["episode_key"] for ep in episodes} == {
        "door-a",
        "door-b",
    }
    assert all(
        _attrs(agent, ep)["separation_status"] == "overlap_detected"
        for ep in episodes
    )
    assert all(
        _attrs(agent, ep)["completion_confidence_cap"] == pytest.approx(0.5)
        for ep in episodes
    )


def test_partial_cue_retrieval_is_bounded_uncertain_and_reconsolidated():
    agent = _fresh()
    first, _, _ = _experience(
        agent,
        event_key="door-low",
        cue_key="door",
        context_key="hall",
        salience=0.1,
        surprise=0.1,
        value=0.1,
    )
    best, _, _ = _experience(
        agent,
        event_key="door-high",
        cue_key="door",
        context_key="atrium",
        salience=0.9,
        surprise=1.0,
        value=0.8,
    )
    agent.tick()
    request = _retrieval(agent, "door", 4)

    assert agent.tick() > 0

    recalls = _nodes(agent, "RecallCandidate")
    assert len(recalls) == 1
    recall = recalls[0]
    attrs = _attrs(agent, recall)
    assert attrs["candidate_limit"] == 1.0
    assert attrs["completion_kind"] == "partial_cue_completion"
    # The cue collision is represented as uncertainty rather than hidden by
    # an apparently exact recalled answer.
    assert attrs["confidence"] == pytest.approx(0.5)
    assert attrs["uncertainty"] == pytest.approx(0.5)
    assert attrs["provenance_kind"] == "recalled"
    assert attrs["observation_status"] == "not_observed"
    assert attrs["reconsolidation_status"] == "completed"
    recalled_events = list(agent.inner.neighbours(recall, "reconstructs_event"))
    assert recalled_events == [best]
    assert recalled_events != [first]
    assert _attrs(agent, request)["candidate_count"] == 1.0

    traces = _nodes(agent, "ReconsolidationTrace")
    assert len(traces) == 1
    assert _attrs(agent, traces[0])["change_scope"] == "retrieval_history_only"
    assert _attrs(agent, traces[0])["observation_status"] == "not_observed"
    assert _nodes(agent, "Observation") == []


def test_unknown_cue_returns_explicit_insufficient_information():
    agent = _fresh()
    request = _retrieval(agent, "never-seen", 3)

    agent.tick()

    outcomes = _nodes(agent, "RecallOutcome")
    assert len(outcomes) == 1
    assert _attrs(agent, outcomes[0])["status"] == "insufficient_information"
    assert _attrs(agent, outcomes[0])["uncertainty"] == 1.0
    assert _attrs(agent, outcomes[0])["observation_status"] == "not_observed"
    assert _attrs(agent, request)["candidate_count"] == 0.0
    assert _nodes(agent, "RecallCandidate") == []


def test_actual_recall_candidate_reconstructs_content_bearing_world_belief():
    agent = WorldAdapter(
        seeds=("episodic_working_memory_core", "generative_world_model")
    )
    _experience(
        agent,
        event_key="remembered-room",
        cue_key="room",
        epoch=7,
        state_kind="room",
        state_summary="a remembered room with a closed door",
    )
    agent.tick()
    episode = _nodes(agent, "Episode")[0]
    assert _attrs(agent, episode)["state_kind"] == "room"
    assert _attrs(agent, episode)["state_summary"] == (
        "a remembered room with a closed door"
    )
    assert _attrs(agent, episode)["epoch"] == 7.0
    assert _attrs(agent, episode)["tick"] == 7.0

    request = _retrieval(agent, "room", 9)
    agent.tick()

    candidate = list(
        agent.inner.neighbours(request, "has_recall_candidate")
    )[0]
    assert candidate in list(
        agent.inner.neighbours(agent.agent, "has_memory_transient")
    )
    reconstructed = list(
        agent.inner.neighbours(candidate, "has_reconstructed_belief")
    )
    assert len(reconstructed) == 1
    belief = _attrs(agent, reconstructed[0])
    assert belief["state_kind"] == "room"
    assert belief["state_summary"] == "a remembered room with a closed door"
    assert belief["memory_epoch"] == 7.0
    assert belief["provenance_kind"] == "remembered"
    assert belief["observation_status"] == "not_observed"
    assert _attrs(agent, candidate)["status"] == "recalled"
    assert _attrs(agent, candidate)["retrieval_status"] == "recalled"
    assert _attrs(agent, candidate)["belief_reconstruction_status"] == (
        "completed"
    )


def test_prioritized_wake_and_offline_replay_builds_semantic_support():
    agent = _fresh()
    _experience(
        agent,
        event_key="routine",
        cue_key="corridor",
        schema_name="safe_route",
        salience=0.4,
        surprise=0.1,
        value=0.3,
    )
    high_event, _, schema = _experience(
        agent,
        event_key="surprising",
        cue_key="secret-door",
        schema_name="safe_route",
        salience=0.7,
        surprise=1.0,
        value=0.8,
    )
    agent.tick()

    wake = _cycle(agent, 10, "wake")
    agent.tick()

    replays = _nodes(agent, "ReplayTrace")
    supports = _nodes(agent, "SemanticSupport")
    assert len(replays) == 1
    assert len(supports) == 1
    replayed_episode = list(
        agent.inner.neighbours(replays[0], "replays_episode")
    )[0]
    assert list(agent.inner.neighbours(replayed_episode, "bound_event")) == [
        high_event
    ]
    assert _attrs(agent, replays[0])["priority_basis"] == (
        "salience_surprise_value_novelty"
    )
    assert _attrs(agent, replays[0])["observation_status"] == "not_observed"
    assert list(agent.inner.neighbours(supports[0], "supports_schema")) == [
        schema
    ]
    assert _attrs(agent, supports[0])["support_count"] == 1.0
    assert _attrs(agent, supports[0])["observation_status"] == "not_observed"
    assert _attrs(agent, wake)["replay_count"] == 1.0

    # A later offline replay updates actual semantic support rather than merely
    # toggling an episode flag.
    _cycle(agent, 11, "offline")
    agent.tick()
    assert len(_nodes(agent, "SemanticSupport")) == 1
    assert _attrs(agent, supports[0])["support_count"] == 2.0
    assert _attrs(agent, supports[0])["uncertainty"] < 0.5


def test_working_memory_all_five_gates_and_expiry():
    agent = _fresh()
    first = agent.s.add_node("Concept", {"name": "door-location"})
    updated = agent.s.add_node("Concept", {"name": "open-door-action"})

    input_gate = _gate(agent, "input", 1, content=first, priority=0.7)
    agent.tick()
    slots = _nodes(agent, "WorkingMemorySlot")
    assert len(slots) == 1
    slot = slots[0]
    assert list(agent.inner.neighbours(slot, "holds_content")) == [first]
    assert _attrs(agent, input_gate)["status"] == "processed"

    update_gate = _gate(
        agent,
        "update",
        2,
        content=updated,
        slot=slot,
        priority=0.8,
    )
    agent.tick()
    assert _attrs(agent, update_gate)["result"] == "updated"
    assert list(agent.inner.neighbours(slot, "holds_content")) == [updated]

    original_expiry = _attrs(agent, slot)["expires_epoch"]
    maintain_gate = _gate(agent, "maintain", 6, slot=slot)
    agent.tick()
    assert _attrs(agent, maintain_gate)["result"] == "maintained"
    assert _attrs(agent, slot)["expires_epoch"] > original_expiry

    output_gate = _gate(agent, "output", 7, slot=slot)
    agent.tick()
    outputs = _nodes(agent, "WorkingMemoryOutput")
    assert len(outputs) == 1
    assert list(agent.inner.neighbours(outputs[0], "outputs_content")) == [
        updated
    ]
    assert _attrs(agent, outputs[0])["observation_status"] == "not_observed"

    clear_gate = _gate(agent, "clear", 8, slot=slot)
    agent.tick()
    assert _attrs(agent, clear_gate)["result"] == "cleared"
    assert _attrs(agent, slot)["status"] == "cleared"
    assert list(agent.inner.neighbours(slot, "holds_content")) == []

    # A separately maintained slot expires when its bounded maintenance
    # interval lapses.
    expiring_content = agent.s.add_node("Concept", {"name": "temporary-target"})
    _gate(agent, "input", 9, content=expiring_content)
    agent.tick()
    expiring_slot = [
        held
        for held in _nodes(agent, "WorkingMemorySlot")
        if _attrs(agent, held)["status"] == "active"
    ][0]
    _clock(agent, _attrs(agent, expiring_slot)["expires_epoch"])
    agent.tick()
    assert _attrs(agent, expiring_slot)["status"] == "expired"
    assert _attrs(agent, expiring_slot)["terminal_reason"] == (
        "maintenance_lapsed"
    )
    assert list(agent.inner.neighbours(expiring_slot, "holds_content")) == []


def test_working_memory_capacity_uses_task_context_for_interference_or_refusal():
    agent = _fresh()
    policy = _nodes(agent, "WorkingMemoryPolicy")[0]
    agent.inner.set_attr(policy, "maximum_slots", 2.0)

    low = agent.s.add_node("Concept", {"name": "low-priority-chat-item"})
    high = agent.s.add_node("Concept", {"name": "high-priority-chat-item"})
    _gate(agent, "input", 1, content=low, task="chat", priority=0.1)
    agent.tick()
    _gate(agent, "input", 2, content=high, task="chat", priority=0.9)
    agent.tick()

    doom_item = agent.s.add_node("Concept", {"name": "incoming-projectile"})
    interference_gate = _gate(
        agent,
        "input",
        3,
        content=doom_item,
        task="doom",
        priority=1.0,
    )
    agent.tick()

    active = [
        slot
        for slot in _nodes(agent, "WorkingMemorySlot")
        if _attrs(agent, slot)["status"] == "active"
    ]
    assert len(active) == 2
    reused = list(agent.inner.neighbours(interference_gate, "reused_slot"))
    assert len(reused) == 1
    victim = reused[0]
    assert _attrs(agent, victim)["interference_count"] == 1.0
    assert _attrs(agent, victim)["last_replacement_reason"] == (
        "cross_task_interference"
    )
    assert list(agent.inner.neighbours(victim, "holds_content")) == [doom_item]

    # With all active slots now in one task, another item in that same context
    # cannot choose a cross-task victim and is honestly refused.
    for slot in active:
        agent.inner.set_attr(slot, "task_context_key", "doom")
    excess = agent.s.add_node("Concept", {"name": "extra-doom-item"})
    refused_gate = _gate(
        agent,
        "input",
        4,
        content=excess,
        task="doom",
        priority=1.0,
    )
    agent.tick()
    results = list(agent.inner.neighbours(refused_gate, "has_gate_result"))
    assert len(results) == 1
    assert _attrs(agent, results[0])["status"] == "refused"
    assert _attrs(agent, results[0])["reason"] == "capacity_limit"
    assert len(
        [
            slot
            for slot in _nodes(agent, "WorkingMemorySlot")
            if _attrs(agent, slot)["status"] == "active"
        ]
    ) == 2


def test_simultaneous_input_gates_are_serialized_before_capacity_admission():
    agent = _fresh()
    policy = _nodes(agent, "WorkingMemoryPolicy")[0]
    agent.inner.set_attr(policy, "maximum_slots", 2.0)

    gates = []
    for index in range(5):
        content = agent.s.add_node("Concept", {"name": f"simultaneous-{index}"})
        gates.append(
            _gate(
                agent,
                "input",
                1,
                content=content,
                task="same-task",
                priority=0.5,
            )
        )

    agent.tick()

    active = [
        slot
        for slot in _nodes(agent, "WorkingMemorySlot")
        if _attrs(agent, slot)["status"] == "active"
    ]
    assert len(active) == 2
    assert all(_attrs(agent, gate)["status"] == "processed" for gate in gates)
    results = [
        list(agent.inner.neighbours(gate, "has_gate_result"))[0]
        for gate in gates
    ]
    assert sum(_attrs(agent, result)["status"] == "accepted" for result in results) == 2
    assert sum(_attrs(agent, result)["status"] == "refused" for result in results) == 3


def test_working_memory_output_offers_content_to_functional_broadcast():
    agent = WorldAdapter(
        seeds=(
            "affective_state_core",
            "dual_process_core",
            "motor_core",
            "adaptive_control_core",
            "episodic_working_memory_core",
        )
    )
    content = agent.s.add_node("Concept", {"name": "door-is-now-open"})
    _gate(agent, "input", 1, content=content, priority=0.8)
    agent.tick()
    slot = _nodes(agent, "WorkingMemorySlot")[0]

    output_gate = _gate(agent, "output", 2, slot=slot)
    agent.tick()

    output = list(
        agent.inner.neighbours(output_gate, "has_working_memory_output")
    )[0]
    candidate = list(
        agent.inner.neighbours(output, "offered_as_broadcast_candidate")
    )[0]
    assert _attrs(agent, candidate)["source_kind"] == "working_memory_output"
    assert _attrs(agent, candidate)["provenance_kind"] == (
        "working_memory_retrieval"
    )
    assert _attrs(agent, candidate)["observation_status"] == "not_observed"
    assert list(agent.inner.neighbours(candidate, "about_content")) == [content]

    broadcasts = _nodes(agent, "FunctionalBroadcast")
    assert len(broadcasts) == 1
    assert list(
        agent.inner.neighbours(broadcasts[0], "broadcasts_content")
    ) == [content]
    assert _attrs(agent, broadcasts[0])["source_kind"] == (
        "working_memory_output"
    )


def test_recall_replay_and_working_outputs_are_pruned_by_memory_clock():
    agent = _fresh()
    _experience(agent, event_key="event", cue_key="cue")
    agent.tick()
    _retrieval(agent, "cue", 2)
    _cycle(agent, 2, "wake")
    content = agent.s.add_node("Concept", {"name": "held"})
    _gate(agent, "input", 2, content=content)
    agent.tick()
    slot = _nodes(agent, "WorkingMemorySlot")[0]
    _gate(agent, "output", 2, slot=slot)
    agent.tick()

    assert _nodes(agent, "RecallCandidate")
    assert _nodes(agent, "ReplayTrace")
    assert _nodes(agent, "WorkingMemoryOutput")
    assert _nodes(agent, "ReconsolidationTrace")

    _clock(agent, 20)
    agent.tick()

    assert _nodes(agent, "RecallCandidate") == []
    assert _nodes(agent, "ReplayTrace") == []
    assert _nodes(agent, "WorkingMemoryOutput") == []
    assert _nodes(agent, "ReconsolidationTrace") == []
