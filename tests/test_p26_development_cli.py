import json

from scripts import run_p22_development_probe as cli


def test_p26_search_can_continue_from_digest_bound_training_checkpoint(
        tmp_path, monkeypatch):
    parent = object()
    binding = {"schema": "p22_training_continuation_parent_v1",
               "checkpoint_digest": "parent-digest"}
    monkeypatch.setattr(cli, "_continuation_parent_from_artifact",
                        lambda *_args: (parent, binding))
    received = {}

    def run_probe(**kwargs):
        received.update(kwargs)
        return {"status": "training_only_development"}

    monkeypatch.setattr(cli, "run_p22_training_proposal_probe", run_probe)
    output = tmp_path / "p26.json"
    monkeypatch.setattr("sys.argv", ["run_p22_development_probe.py",
        "--family", "loopover", "--training-draws", "50", "51", "52", "53",
        "--training-goal-relation", "distinct", "--validation-start", "0",
        "--validation-count", "0", "--per-request-attempt-ceiling", "15000",
        "--global-attempt-ceiling", "120000", "--search-ticks", "120",
        "--discovery-attempt-limit-per-request", "10000",
        "--transfer-reserve-per-request", "5000", "--effect-dedup",
        "--continuation-parent-artifact", str(tmp_path / "parent.json"),
        "--continuation-parent-record-path", "parent_checkpoint",
        "--continuation-parent-digest", "parent-digest",
        "--output", str(output)])

    assert cli.main() == 0
    assert received["parent_checkpoint"] is parent
    assert received["training_draws"] == (50, 51, 52, 53)
    assert received["global_attempt_ceiling"] == 120000
    assert received["per_request_attempt_ceiling"] == 15000
    assert received["discovery_attempt_limit_per_request"] == 10000
    assert received["transfer_reserve_per_request"] == 5000
    assert received["effect_dedup_enabled"] is True
    assert received["validation_draws"] == ()
    assert json.loads(output.read_text())["training_continuation_binding"] == {
        **binding, "family": "loopover", "training_draws": [50, 51, 52, 53],
        "training_goal_relation": "distinct", "validation_draws": []}
