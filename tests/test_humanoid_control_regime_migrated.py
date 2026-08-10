import json
from pathlib import Path

from substrate.world_adapter import WorldAdapter


ROOT = Path(__file__).resolve().parents[1]


def _edge(agent, source, edge_type, target):
    agent.inner.add_edge_unchecked(source, edge_type, target, {})


def _episode(agent, **overrides):
    attrs = {
        "phase": "locomotion",
        "regime_monitor_enabled": 1.0,
        "regime_clock_seq": 10.0,
        "regime_evidence_seq": 0.0,
        "regime_evidence_horizon_actions": 2.0,
        "regime_ordinal": 0.0,
        "regime_max_ordinal": 2.0,
        "regime_escalation_requested": 0.0,
        "regime_escalation_count": 0.0,
        "regime_last_escalation_seq": 0.0,
        "regime_applied_ordinal": 0.0,
        "regime_last_cycle_count": 0.0,
        "regime_best_progress": 0.0,
        "locomotor_cycle_count": 0.0,
        "maximum_directed_progress": 0.0,
        "active_gait_attractor_ordinal": 2.0,
        "active_residual_regime_ordinal": 18.0,
        "residual_regime_window_sample_count": 0.0,
        "residual_regime_window_complete": 0.0,
        "render_first_suspended": 0.0,
        "async_trust_epoch": 0.0,
        "recovery_mode": 0.0,
        "online_phase_learning": 0.0,
        "gait_surprise_streak": 0.0,
        "locomotor_prior_reset_seq": 0.0,
    }
    attrs.update(overrides)
    regime_keys = {
        key: value for key, value in attrs.items()
        if key.startswith("regime_")
    }
    episode = agent.s.add_node("HumanoidEpisode", attrs)
    regime = agent.s.add_node("EmbodiedMotorProgramEpisode", regime_keys)
    _edge(agent, agent.agent, "has_humanoid_episode", episode)
    _edge(agent, episode, "has_humanoid_control_regime", regime)
    _edge(agent, agent.agent, "holds_control_regime", regime)
    policy = agent.s.nodes("HumanoidPolicy")[0]
    old = next(
        regime
        for regime in agent.inner.neighbours(
            policy, "has_humanoid_residual_regime"
        )
        if agent.s.node(regime)["attrs"]["ordinal"] == 18.0
    )
    _edge(agent, episode, "evaluates_humanoid_residual_regime", old)
    return episode, regime


def test_absent_support_evidence_demotes_to_walking_and_invalidates_trust():
    agent = WorldAdapter(seeds=(
        "control_regime_escalation",
        "humanoid_control_regime",
    ))
    episode, regime = _episode(agent)
    agent.tick()
    episode_attrs = agent.s.node(episode)["attrs"]
    regime_attrs = agent.s.node(regime)["attrs"]
    assert regime_attrs["regime_ordinal"] == 1.0
    assert episode_attrs["regime_applied_ordinal"] == 1.0
    assert episode_attrs["active_gait_attractor_ordinal"] == 0.0
    assert episode_attrs["active_residual_regime_ordinal"] == 0.0
    assert episode_attrs["render_first_suspended"] == 1.0
    assert episode_attrs["async_trust_epoch"] == 10.0


def test_new_support_cycle_refreshes_evidence_without_escalation():
    agent = WorldAdapter(seeds=(
        "control_regime_escalation",
        "humanoid_control_regime",
    ))
    episode, regime = _episode(
        agent,
        regime_clock_seq=3.0,
        regime_evidence_seq=2.0,
        locomotor_cycle_count=1.0,
    )
    agent.tick()
    attrs = agent.s.node(regime)["attrs"]
    assert attrs["regime_ordinal"] == 0.0
    assert attrs["regime_evidence_seq"] == 3.0
    assert attrs["regime_last_cycle_count"] == 1.0


def test_seed_declares_generic_escalation_dependency():
    seed = json.loads(
        (ROOT / "seeds" / "humanoid_control_regime.json").read_text()
    )
    assert seed["depends_on"] == [
        "humanoid_adaptation",
        "control_regime_escalation",
    ]
