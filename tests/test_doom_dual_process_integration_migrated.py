"""Real Doom control seam: PSI state -> dual process -> ControlBundle."""
from __future__ import annotations

import pytest

pytest.importorskip("substrate_rs")

from domains.control_bundle import ControlBundleAdapter
from domains.doom_dual_process_ingest import DoomDualProcessAdapter
from substrate.world_adapter import WorldAdapter


def _fixture():
    agent = WorldAdapter(seeds=("dual_process_core",))
    game = agent.s.add_node("WorldInstance", {})
    controls = ControlBundleAdapter(agent, game, [
        {"axis": "longitudinal", "controls": ["forward", "backward"]},
        {"axis": "angular", "controls": ["turn_left", "turn_right"]},
        {"axis": "interaction", "role": "operate", "controls": ["use"]},
    ])
    doom = DoomDualProcessAdapter(agent, controls)
    return agent, game, controls, doom


def _footprint(_tokens):
    return {
        "expected_goal_work": 2.0,
        "expected_information_gain": 0.5,
        "recoverability": 1.0,
    }


def _candidate_for(agent, context, token):
    for candidate in agent.inner.neighbours(
            context, "has_system_one_candidate"):
        controls = agent.inner.neighbours(candidate, "proposes_control")
        if len(controls) == 1:
            attrs = agent.s.node(controls[0])["attrs"]
            if attrs["token"] == token:
                return candidate
    raise AssertionError(f"no candidate for {token}")


def _receipt(doom, action_id, observed_epoch, status="applied"):
    return doom.observe_action_receipt({
        "action_id": int(action_id),
        "status": status,
        "authored_world_tick": int(action_id),
        "expires_world_tick": int(action_id) + 6,
        "receipt_world_tick": int(action_id) + 1,
        "applied_world_tick": (
            int(action_id) + 1 if status == "applied" else -1),
    }, observed_epoch=observed_epoch)


def test_doom_epochs_create_graph_context_candidates_and_latest_psi_state():
    agent, game, controls, doom = _fixture()
    try:
        first = doom.observe_epoch(
            epoch=1, health=100, ammo=50, new_cells=0,
            attention_refused=0)
        intent, report = doom.deliberate(first, 1, _footprint)
        controls.enact(intent, 1)
        assert report["system_one_commits"] + report[
            "system_two_escalations"] == 1

        second = doom.observe_epoch(
            epoch=2, health=25, ammo=4, damage_taken=3,
            new_cells=2, moved=True, attention_refused=0)
        intent, _ = doom.deliberate(second, 2, _footprint)
        controls.enact(intent, 2)

        assert len(agent.inner.neighbours(
            game, "has_current_dual_process_context")) == 1
        assert len(agent.inner.neighbours(
            second, "has_system_one_candidate")) == len(controls.controls)
        assert agent.s.node(doom.drives["health"])["attrs"][
            "c_d"] == pytest.approx(25.0)
        assert agent.s.node(doom.drives["ammo"])["attrs"][
            "c_d"] == pytest.approx(4.0)
        assert all(
            agent.s.node(drive)["attrs"]["doom_observation_epoch"] == 2
            for drive in doom.drives.values())
        leading = agent.inner.neighbours(
            doom.modulators, "leading_drive")
        assert len(leading) == 1
        mode = agent.inner.neighbours(
            agent.agent, "has_network_mode_state")
        samples = agent.inner.neighbours(
            agent.agent, "has_network_mode_sample")
        assert len(mode) == len(samples) == 1
        mode_attrs = agent.s.node(mode[0])["attrs"]
        assert mode_attrs["epoch"] == 2
        assert mode_attrs["task_demand"] == pytest.approx(1.0)
        assert mode_attrs["interoceptive_urgency"] == pytest.approx(0.92)
        assert agent.s.node(samples[0])["attrs"]["source_kind"] == (
            "doom_observation")
    finally:
        agent.close()


def test_canonical_affect_reaches_dual_choice_and_use_remains_reachable():
    agent, game, controls, doom = _fixture()
    try:
        context = doom.observe_epoch(
            epoch=1, health=100, ammo=50, new_cells=0,
            attention_refused=0)
        intent, report = doom.deliberate(context, 1, _footprint)
        action = controls.enact(intent, 1)

        assert agent.inner.neighbours(
            context, "uses_affective_state") == [doom.affect]
        affect = agent.s.node(doom.affect)["attrs"]
        assert affect["epoch"] >= 0
        assert "use" in action
        use = _candidate_for(agent, context, "use")
        forward = _candidate_for(agent, context, "forward")
        assert agent.s.node(use)["attrs"]["system_one_score"] > (
            agent.s.node(forward)["attrs"]["system_one_score"])
        assert report["system_one_commits"] == 1
        assert agent.s.node(game)["attrs"]["chosen_source"] == "dual_process"
    finally:
        agent.close()


def test_verified_system_two_result_persists_into_future_control_candidate():
    agent, _game, controls, doom = _fixture()
    try:
        first = doom.observe_epoch(
            epoch=1, health=100, ammo=50, attention_refused=0)
        # Raw controller estimates are graph data. This fixture makes active
        # cognition worth its cost without choosing a control in Python.
        for key, value in {
            "system_two_expected_utility": 10.0,
            "system_two_reliability": 1.0,
            "system_two_latency": 0.0,
            "system_two_effort": 0.0,
        }.items():
            agent.inner.set_attr(first, key, value)
        intent, report = doom.deliberate(first, 1, _footprint)
        first_action = controls.enact(intent, 1)
        assert report["needs_system_two"] is True
        assert first_action
        _receipt(doom, 1, 2)

        # Give the next epoch an unequivocal fast default. This is persistent
        # graph prior state, not a host-selected action.
        agent.inner.set_attr(
            controls.controls["use"], "doom_predicted_value", 10.0)
        second = doom.observe_epoch(
            epoch=2, health=100, ammo=50, new_cells=1, moved=True,
            attention_refused=0)
        for key, value in {
            "system_two_expected_utility": -10.0,
            "system_two_reliability": 0.0,
            "system_two_latency": 10.0,
            "system_two_effort": 10.0,
        }.items():
            agent.inner.set_attr(second, key, value)
        intent, second_report = doom.deliberate(second, 2, _footprint)
        controls.enact(intent, 2)
        # The fresh decision itself is confidently System 1. The cycle still
        # services the independent learning-only request created from the
        # preceding action's now-available outcome.
        assert agent.s.node(second)["attrs"]["route"] == "system_one"
        assert second_report["system_one_commits"] == 1

        learned_token = first_action[0]
        control = controls.controls[learned_token]
        memory = agent.s.node(control)["attrs"]
        assert memory["doom_experience_count"] == 1
        assert memory["doom_predicted_value"] > 0.0
        assert memory["doom_consolidation_strength"] > 0.0

        third = doom.observe_epoch(
            epoch=3, health=100, ammo=50, new_cells=0, moved=False,
            attention_refused=0)
        doom.deliberate(third, 3, _footprint)
        future = agent.s.node(
            _candidate_for(agent, third, learned_token))["attrs"]
        assert future["predicted_value"] == pytest.approx(
            memory["doom_predicted_value"])
        assert future["consolidation_strength"] == pytest.approx(
            memory["doom_consolidation_strength"])
    finally:
        agent.close()


def test_causally_later_kill_closes_graph_resident_action_attempt():
    agent, _game, controls, doom = _fixture()
    try:
        first = doom.observe_epoch(
            epoch=1, health=100, ammo=50, attention_refused=0)
        for key, value in {
            "system_two_expected_utility": 10.0,
            "system_two_reliability": 1.0,
            "system_two_latency": 0.0,
            "system_two_effort": 0.0,
        }.items():
            agent.inner.set_attr(first, key, value)
        intent, _ = doom.deliberate(first, 1, _footprint)
        controls.enact(intent, 1)
        _receipt(doom, 1, 2)

        second = doom.observe_epoch(
            epoch=2, health=100, ammo=50, attention_refused=0,
            kill_delta=1)
        intent, _ = doom.deliberate(second, 2, _footprint)
        controls.enact(intent, 2)

        outcomes = agent.s.nodes("SystemTwoOutcome")
        assert len(outcomes) == 1
        attrs = agent.s.node(outcomes[0])["attrs"]
        assert attrs["status"] == "consolidated"
        assert attrs["actual_value"] == 1.0
        assert attrs["verified"] == 1
        assert attrs["action_id"] == 1
        assert attrs["source_epoch"] == 1
        attempts = agent.s.nodes("DoomActionAttempt")
        assert any(
            agent.s.node(node)["attrs"]["action_id"] == 1
            and agent.s.node(node)["attrs"]["status"] == "successful"
            for node in attempts)
        assert "_pending_outcome" not in doom.__dict__
    finally:
        agent.close()


def test_no_effect_waits_for_causal_window_before_failure():
    agent, _game, controls, doom = _fixture()
    try:
        first = doom.observe_epoch(
            epoch=1, health=100, ammo=50, attention_refused=0)
        for key, value in {
            "system_two_expected_utility": 10.0,
            "system_two_reliability": 1.0,
            "system_two_latency": 0.0,
            "system_two_effort": 0.0,
        }.items():
            agent.inner.set_attr(first, key, value)
        intent, _ = doom.deliberate(first, 1, _footprint)
        controls.enact(intent, 1)
        _receipt(doom, 1, 2)

        for epoch in (2, 3, 4):
            context = doom.observe_epoch(
                epoch=epoch, health=100, ammo=50, attention_refused=0)
            intent, _ = doom.deliberate(context, epoch, _footprint)
            controls.enact(intent, epoch)
            assert not agent.s.nodes("SystemTwoOutcome")

        context = doom.observe_epoch(
            epoch=5, health=100, ammo=50, attention_refused=0)
        intent, _ = doom.deliberate(context, 5, _footprint)
        controls.enact(intent, 5)
        outcomes = agent.s.nodes("SystemTwoOutcome")
        assert len(outcomes) == 1
        attrs = agent.s.node(outcomes[0])["attrs"]
        assert attrs["status"] == "revalued"
        assert attrs["actual_value"] == -1.0
        assert attrs["action_id"] == 1
    finally:
        agent.close()


def test_incomplete_or_empty_manifest_cannot_activate():
    agent, game, _controls, doom = _fixture()
    try:
        observation = agent.s.add_node("DoomStateObservation", {
            "epoch": 99, "health": 100.0, "ammo": 50.0,
            "damage_taken": 0.0, "respawned": 0.0, "new_cells": 0.0,
            "moved": 0.0, "kill_delta": 0.0, "attention_refused": 0.0,
            "motion_count": 0.0, "salience_count": 0.0,
            "doom_outcome_consumed": 0,
        })
        context = agent.s.add_node("DualProcessContext", {
            "status": "preparing", "epoch": 99, "manifest_complete": 0,
            "expected_candidate_count": 1,
        })
        agent.inner.add_edge_unchecked(
            agent.agent, "has_dual_process_context", context)
        agent.inner.add_edge_unchecked(
            context, "observes_doom_state", observation)
        agent.inner.add_edge_unchecked(
            game, "has_current_dual_process_context", context)

        agent.tick()
        assert agent.s.node(context)["attrs"]["status"] == "preparing"
        assert not agent.inner.neighbours(
            context, "has_system_two_escalation")

        agent.inner.set_attr(context, "manifest_complete", 1)
        agent.tick()
        assert agent.s.node(context)["attrs"]["status"] == "preparing"
        assert not agent.inner.neighbours(
            context, "has_system_two_escalation")
    finally:
        agent.close()


def test_transport_expiry_closes_attempt_without_punishing_control():
    agent, _game, controls, doom = _fixture()
    try:
        context = doom.observe_epoch(
            epoch=1, health=100, ammo=50, attention_refused=0)
        for key, value in {
            "system_two_expected_utility": 10.0,
            "system_two_reliability": 1.0,
            "system_two_latency": 0.0,
            "system_two_effort": 0.0,
        }.items():
            agent.inner.set_attr(context, key, value)
        intent, _ = doom.deliberate(context, 1, _footprint)
        action = controls.enact(intent, 1)
        assert action

        _receipt(doom, 1, 2, status="expired_stale")
        next_context = doom.observe_epoch(
            epoch=2, health=100, ammo=50, attention_refused=0)
        doom.deliberate(next_context, 2, _footprint)

        attempts = agent.s.nodes("DoomActionAttempt")
        attempt = next(
            node for node in attempts
            if agent.s.node(node)["attrs"]["action_id"] == 1)
        attrs = agent.s.node(attempt)["attrs"]
        assert attrs["status"] == "transport_expired"
        assert attrs["transport_status"] == "expired_stale"
        assert not agent.s.nodes("SystemTwoOutcome")
        assert agent.s.node(controls.controls[action[0]])["attrs"][
            "doom_experience_count"] == 0
    finally:
        agent.close()


def test_intent_authorization_is_authored_by_graph_and_fails_closed():
    agent, _game, _controls, doom = _fixture()
    try:
        context = doom.observe_epoch(
            epoch=1, health=100, ammo=50, attention_refused=0)
        intent, _ = doom.deliberate(
            context, 1, lambda _tokens: {
                "expected_goal_work": 0.0,
                "expected_information_gain": 0.0,
                "recoverability": 0.0,
                "externality": 100.0,
            })
        attrs = agent.s.node(intent)["attrs"]
        assert attrs["status"] == "deferred"
        assert attrs["authorization_source"] == (
            "graph_information_commitment")
        assert attrs["authorization_decision"] == "wait_or_refine"
    finally:
        agent.close()


def test_transient_doom_episode_graph_is_bounded_but_controls_persist():
    agent, _game, controls, doom = _fixture()
    try:
        agent.inner.set_attr(
            controls.controls["use"], "doom_predicted_value", 1000.0)
        control_ids = set(controls.controls.values())
        for epoch in range(1, 41):
            context = doom.observe_epoch(
                epoch=epoch, health=100, ammo=50, attention_refused=0)
            for key, value in {
                "system_two_expected_utility": -100.0,
                "system_two_reliability": 0.0,
                "system_two_latency": 100.0,
                "system_two_effort": 100.0,
            }.items():
                agent.inner.set_attr(context, key, value)
            intent, _ = doom.deliberate(context, epoch, _footprint)
            controls.enact(intent, epoch)

        assert set(agent.s.nodes("Control")) == control_ids
        assert len(agent.s.nodes("DualProcessContext")) <= 9
        assert len(agent.s.nodes("DoomStateObservation")) <= 9
        assert len(agent.s.nodes("SystemOneCandidate")) <= (
            9 * len(controls.controls))
        assert len(agent.s.nodes("ControlBundle")) <= 9
        assert len(agent.s.nodes("ActionIntent")) <= 9
    finally:
        agent.close()


def test_active_cognition_attempts_outcomes_and_escalations_are_bounded():
    agent, _game, controls, doom = _fixture()
    try:
        control_ids = set(controls.controls.values())
        for epoch in range(1, 61):
            context = doom.observe_epoch(
                epoch=epoch, health=100, ammo=50, attention_refused=0)
            for key, value in {
                "system_two_expected_utility": 10.0,
                "system_two_reliability": 1.0,
                "system_two_latency": 0.0,
                "system_two_effort": 0.0,
            }.items():
                agent.inner.set_attr(context, key, value)
            intent, _ = doom.deliberate(context, epoch, _footprint)
            controls.enact(intent, epoch)
            _receipt(doom, epoch, epoch + 1)

        assert set(agent.s.nodes("Control")) == control_ids
        # Nine retained epochs plus the three-epoch unresolved causal tail and
        # at most one boundary record. A retained episode can hold both its
        # decision request and its distinct learning request. None of these
        # pools grows with runtime.
        assert len(agent.s.nodes("DualProcessContext")) <= 13
        assert len(agent.s.nodes("SystemTwoEscalation")) <= 18
        assert len(agent.s.nodes("DoomActionAttempt")) <= 13
        assert len(agent.s.nodes("SystemTwoOutcome")) <= 9
        assert agent.s.node(doom.lifecycle_policy)["attrs"][
            "archived_outcome_count"] > 0
    finally:
        agent.close()
