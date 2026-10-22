"""P12.01 source/interface fixtures, not a runtime imitation claim.

P12.02 will replace these boundary fixtures with native graph-rule lifecycle
tests. For now they make attribution, missingness, body mapping and the
non-teacher observation route explicit at the world-event boundary.
"""
from __future__ import annotations


def _episode(*, source_kind="witnessed_interaction", actor="peer",
             learner="agent-root", actor_body="peer-body",
             learner_body="agent-body", observed_actions=None,
             coverage=None, body_map=None):
    return {
        "schema_version": 1,
        "episode_id": "episode-1",
        "source_epoch": 4,
        "owner_id": learner,
        "observer_id": learner,
        "actor_id": actor,
        "actor_body_id": actor_body,
        "learner_body_id": learner_body,
        "source_kind": source_kind,
        "observed_actions": observed_actions or [],
        "coverage": coverage or {"status": "complete", "visible_orders": [0]},
        "body_map": body_map,
    }


def test_observed_actor_not_self():
    episode = _episode(observed_actions=[{"order": 0, "actor_id": "peer",
                                          "action": "press", "event_id": "event-0"}])
    event = episode["observed_actions"][0]
    assert event["actor_id"] == episode["actor_id"]
    assert event["actor_id"] != episode["owner_id"]
    assert episode["source_kind"] == "witnessed_interaction"


def test_missing_step_unknown():
    episode = _episode(
        observed_actions=[{"order": 0, "actor_id": "peer", "action": "open"}],
        coverage={"status": "partial", "visible_orders": [0],
                  "missing_orders": [1], "missing_means": "unknown"})
    assert episode["coverage"]["missing_means"] == "unknown"
    assert [row["order"] for row in episode["observed_actions"]] == [0]


def test_body_mismatch_blocks_trial():
    episode = _episode(body_map={"source_body_id": "other-body",
                                 "target_body_id": "agent-body",
                                 "source_epoch": 4, "target_epoch": 2,
                                 "status": "mismatch"})
    mapping = episode["body_map"]
    assert mapping["source_body_id"] != episode["actor_body_id"]
    assert mapping["status"] != "verified"


def test_no_directed_teaching_required():
    episode = _episode(source_kind="witnessed_interaction")
    assert episode["source_kind"] == "witnessed_interaction"
    assert "teacher_id" not in episode
    assert "teaching_intent" not in episode
