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
