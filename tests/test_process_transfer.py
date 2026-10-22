"""P11 exact transfer gates; unknown and lossy maps abstain."""
def _inverse(p):
    result = [0] * len(p)
    for i, x in enumerate(p):
        result[x] = i
    return result


def _mapped_process(source_program, forward, inverse, target_state, source_state):
    """Apply f ∘ g ∘ f⁻¹ in the frozen right-to-left composition order."""
    if len(forward) != len(inverse) or sorted(forward) != list(range(len(forward))) or \
            sorted(inverse) != list(range(len(inverse))):
        return None
    if any(inverse[forward[x]] != x for x in range(len(forward))):
        return None
    if sorted(source_state) != list(range(len(source_state))) or len(source_state) != len(forward):
        return None
    # Permutation source program maps each index to its next index.
    target_program = [None] * len(forward)
    for x in range(len(forward)):
        target_program[forward[x]] = forward[source_program[inverse[forward[x]]]]
    predicted = [target_state[target_program[i]] for i in range(len(target_state))]
    return target_program, predicted


def _verify(candidate, fresh_state, observed_target_state, epochs):
    if candidate.get("wrong_frame") or candidate.get("nonconjugate"):
        return False
    if candidate.get("epochs") != epochs or not candidate.get("complete_separating_set"):
        return False
    result = _mapped_process(candidate["source_program"], candidate["forward"],
                             candidate["inverse"], fresh_state,
                             candidate["source_state"])
    return result is not None and result[1] == observed_target_state


def test_unseen_target_process_transfers():
    f = [2, 0, 1]
    inv = _inverse(f)
    # g_A is a one-step rotation; target transition is its conjugate.
    program, _ = _mapped_process([1, 2, 0], f, inv, [0, 1, 2], [0, 1, 2])
    candidate = {"source_program": [1, 2, 0], "forward": f, "inverse": inv,
                 "source_state": [0, 1, 2], "complete_separating_set": True,
                 "epochs": {"source": 2, "target": 4}}
    target = [0, 1, 2]
    observed = [target[program[i]] for i in range(3)]
    assert _verify(candidate, target, observed, candidate["epochs"])


def test_wrong_frame_rejected():
    candidate = {"wrong_frame": True}
    assert not _verify(candidate, [0], [0], {})


def test_nonconjugate_control_abstains():
    candidate = {"nonconjugate": True}
    assert not _verify(candidate, [0], [0], {})


def test_transferred_effect_reverified():
    f = [1, 0]
    inv = _inverse(f)
    candidate = {"source_program": [1, 0], "forward": f, "inverse": inv,
                 "source_state": [0, 1], "complete_separating_set": True,
                 "epochs": {"source": 1, "target": 3}}
    assert _verify(candidate, [0, 1], [1, 0], candidate["epochs"])
    assert not _verify(candidate, [0, 1], [0, 1], candidate["epochs"])


def test_one_way_map_is_not_exact_conjugation():
    assert not _verify({"forward": [0, 0], "inverse": [0]}, [0, 1], [0, 1], {})
