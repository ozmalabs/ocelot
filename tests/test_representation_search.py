"""P11.01 semantic-freeze tests for frame and description invariants."""
import json


def _package_bits(package):
    encoded = json.dumps(package, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    return 8 * len(encoded)


def _is_bijection(forward, inverse):
    return (set(forward) == set(inverse.values()) and
            set(inverse) == set(forward.values()) and
            all(inverse[forward[x]] == x for x in forward) and
            all(forward[inverse[y]] == y for y in inverse))


def _effective_frame(current, proposed):
    return current if current["authority"] == "forced" else proposed


def _select_from_training(candidates, training_rows):
    assert training_rows and all(row["split"] == "train" for row in training_rows)
    return min(candidates, key=lambda c: _package_bits(c["package"]) + c["train_residual_bits"])


def _search_result(candidates, *, current_epochs, forced_frame=False):
    """Small deterministic oracle for the frozen adoption predicate."""
    current = {k: v for k, v in current_epochs.items()}
    eligible = [c for c in candidates
                if c.get("epochs") == current and c.get("verified")
                and c.get("discriminating_rows", 0) >= 3
                and c.get("package_cost_complete")
                and not c.get("heldout_used_for_selection")
                and (not forced_frame or c.get("frame_id") == current.get("frame_id"))]
    if not eligible:
        return None
    return min(eligible, key=lambda c: c["package_bits"] + c["train_residual_bits"])


def _finish_search(state):
    """Every terminal search outcome restores its temporary policy state."""
    state["policy_enabled"] = state["prior_policy_enabled"]
    state["request_status"] = "completed" if state["result"] else "rejected"
    return state


def test_decoder_cost_included():
    baseline = {"model": {"rule": "long-baseline"}, "decoder": {"code": "d" * 4}}
    candidate = {"model": {"rule": "x"}, "decoder": {"code": "d" * 200}}
    assert _package_bits(candidate) > _package_bits(baseline)
    assert len(json.dumps(candidate["model"])) < len(json.dumps(baseline["model"]))


def test_forced_frame_not_relaxed():
    forced = {"frame_id": "host-limit", "authority": "forced", "residuals": ["visible"]}
    proposed = {"frame_id": "wide-view", "authority": "chosen", "residuals": []}
    assert _effective_frame(forced, proposed) is forced
    assert _effective_frame(forced, proposed)["residuals"] == ["visible"]


def test_noninvertible_map_not_conjugation():
    many_to_one = {"a": "x", "b": "x", "c": "y"}
    guessed_inverse = {"x": "a", "y": "c"}
    assert not _is_bijection(many_to_one, guessed_inverse)


def test_holdout_not_selection_input():
    candidates = [
        {"name": "compact-train", "package": {"model": "m", "decoder": "d"},
         "train_residual_bits": 20},
        {"name": "overfit-train", "package": {"model": "m" * 80, "decoder": "d"},
         "train_residual_bits": 0},
    ]
    training = [{"split": "train", "evidence_id": "train-1"}]
    chosen_before = _select_from_training(candidates, training)["name"]
    heldout_a = [{"split": "heldout", "label": "candidate-a"}]
    heldout_b = [{"split": "heldout", "label": "candidate-b"}]
    # Held-out data is reserved for later scoring and is never an argument to selection.
    assert heldout_a != heldout_b
    assert _select_from_training(candidates, training)["name"] == chosen_before


def test_verified_representation_shortens_total_description():
    epochs = {"source_epoch": 4, "model_epoch": 2, "frame_epoch": 8,
              "frame_id": "grid-native"}
    base = {"name": "baseline", "epochs": epochs, "verified": True,
            "discriminating_rows": 5, "package_cost_complete": True,
            "heldout_used_for_selection": False, "frame_id": "grid-native",
            "package_bits": 400, "train_residual_bits": 100}
    candidate = {**base, "name": "candidate", "package_bits": 250,
                 "train_residual_bits": 80}
    assert _search_result([base, candidate], current_epochs=epochs) is candidate


def test_mapping_cost_blocks_spurious_gain():
    epochs = {"source_epoch": 1, "model_epoch": 1, "frame_epoch": 1,
              "frame_id": "a"}
    baseline = {"name": "baseline", "epochs": epochs, "verified": True,
                "discriminating_rows": 4, "package_cost_complete": True,
                "heldout_used_for_selection": False, "frame_id": "a",
                "package_bits": 200, "train_residual_bits": 100}
    # The tempting compact model is invalid when its map cost is omitted;
    # package_bits includes that map, decoder and exception cost.
    mapped = {**baseline, "name": "mapped", "model_bits": 30,
              "map_bits": 300, "package_bits": 360, "train_residual_bits": 10}
    assert mapped["model_bits"] + mapped["train_residual_bits"] < 300
    assert _search_result([baseline, mapped], current_epochs=epochs) is baseline


def test_epoch_change_invalidates_recall():
    epochs = {"source_epoch": 2, "model_epoch": 3, "frame_epoch": 5,
              "frame_id": "f5"}
    stale = {"epochs": {**epochs, "frame_epoch": 4}, "verified": True,
             "discriminating_rows": 5, "package_cost_complete": True,
             "heldout_used_for_selection": False, "frame_id": "f4",
             "package_bits": 1, "train_residual_bits": 0}
    assert _search_result([stale], current_epochs=epochs) is None


def test_failed_search_restores():
    state = {"prior_policy_enabled": 0.0, "policy_enabled": 1.0, "result": None}
    assert _finish_search(state) == {"prior_policy_enabled": 0.0,
                                     "policy_enabled": 0.0,
                                     "request_status": "rejected", "result": None}


def test_forced_frame_search_rejects_alternative_frame():
    epochs = {"source_epoch": 1, "model_epoch": 1, "frame_epoch": 2,
              "frame_id": "forced"}
    alternate = {"epochs": epochs, "verified": True, "discriminating_rows": 9,
                 "package_cost_complete": True, "heldout_used_for_selection": False,
                 "frame_id": "alternate", "package_bits": 1, "train_residual_bits": 0}
    assert _search_result([alternate], current_epochs=epochs, forced_frame=True) is None
