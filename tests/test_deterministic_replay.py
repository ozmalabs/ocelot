from __future__ import annotations

import json

from scripts.deterministic_replay import (
    EpisodeSpec,
    differential_replay,
    first_divergence,
    load_episode_spec,
    save_episode_spec,
)


def _spec() -> EpisodeSpec:
    return EpisodeSpec(
        episode_id="probe:7",
        profile={"identity": "generic-proving-ground", "scenario": "fault-a"},
        initial_state={"x": 1.0, "heading": 2.0},
        reference_schedule=({"action": 4, "reference": {"x": 3.0}},),
        fault_specification={"kind": "authority_loss", "group": 2},
        event_timing={"fault_onset_action": 4},
        exogenous={
            "random_streams": {"gust": {"algorithm": "portable", "seed": 7}},
            "gust_sequence": [[0.1, 0.0, -0.1], [0.0, 0.2, 0.0]],
        },
        rates={"action_frequency_hz": 10, "physics_frequency_hz": 400},
        controller={"name": "generic-controller", "version": "1"},
        seeds={"episode_seed": 7},
        crash_predicates={"loss": ["ground_contact"]},
        ambiguity_choices={"fault_mapping": "declared-profile"},
    )


def test_episode_spec_is_canonical_and_self_hashing(tmp_path):
    spec = _spec()
    payload = spec.to_dict()
    assert payload["schema_version"] == "episode-spec-v1"
    assert spec.verify_hash(payload)
    path = tmp_path / "episode.json"
    save_episode_spec(spec, path)
    assert load_episode_spec(path).to_dict() == payload

    tampered = json.loads(path.read_text())
    tampered["initial_state"]["x"] = 9.0
    path.write_text(json.dumps(tampered))
    try:
        load_episode_spec(path)
    except ValueError as exc:
        assert "hash mismatch" in str(exc)
    else:  # pragma: no cover - assertion is the useful failure message
        raise AssertionError("tampered manifest was accepted")


def test_first_divergence_reports_earliest_decision_field():
    baseline = [
        {"request_seq": 1, "tokens": ["hold"], "effector_position": [0.0]},
        {"request_seq": 2, "tokens": ["hold"], "effector_position": [0.0]},
    ]
    candidate = [
        {"request_seq": 1, "tokens": ["hold"], "effector_position": [0.0]},
        {"request_seq": 2, "tokens": ["pitch-up"], "effector_position": [0.1]},
    ]
    divergence = first_divergence(baseline, candidate)
    assert divergence == {
        "action_index": 1,
        "request_seq": 2,
        "field": "tokens",
        "baseline": ["hold"],
        "candidate": ["pitch-up"],
        "kind": "observable_decision_or_control",
    }


def test_differential_replay_requires_the_same_manifest():
    spec = _spec().to_dict()
    baseline = {"episode_spec": spec, "trace": [], "metrics": {"crash": False}}
    candidate = {"episode_spec": spec, "trace": [], "metrics": {"crash": True}}
    result = differential_replay(baseline, candidate)
    assert result["manifest_match"] is True
    assert result["outcome_changed"] is True
