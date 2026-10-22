"""P11 exact transfer gates; unknown and lossy maps abstain."""
from evaluation.process_mastery.harness import Agent
from evaluation.process_mastery.process_transfer_worlds import (
    apply_program as apply_world_program, transfer_world, verify_world_conjugacy,
)
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


def test_graph_rule_requires_fresh_verified_target_effect():
    agent = Agent(extra_seeds=("process_transfer",),
                  policy_overrides={"ProcessTransferPolicy": {"enabled": 1.0},
                                    "InventionPolicy": {"enabled": 0.0}})
    s, ag = agent.s, agent.ag
    source = s.add_node("ProcessSchema", {"name": "rotate", "kind": "permutation",
                                          "operator": "rotate", "params": [1, 2, 0],
                                          "source_epoch": 2})
    target = s.add_node("ProcessDomain", {"name": "target", "kind": "permutation",
                                         "probe_epoch": 4})
    fmap = s.add_node("RepresentationMap", {"is_bijection": True, "inverse_verified": True,
                                             "source_epoch": 2, "target_frame_epoch": 3})
    candidate = s.add_node("ProcessTransferCandidate", {
        "candidate_id": "pt-1", "status": "candidate", "map_direction": "source_to_target",
        "source_epoch": 2, "model_epoch": 1, "target_frame_epoch": 3,
        "target_probe_epoch": 4, "search_epoch": 5, "nonconjugate": False,
        "wrong_frame": False, "complete_separating_set": True,
        "target_process_name": "transferred-rotate", "composed_target_program": [2, 0, 1]})
    request = s.add_node("ThinkingBudgetRequest", {"requester_kind": "process_transfer",
                                                    "status": "approved", "debited_epoch": 5,
                                                    "terminal_status": "completed"})
    verification = s.add_node("ProcessTransferVerification", {
        "status": "verified", "verification_kind": "fresh_native_target_effect",
        "candidate_id": "pt-1", "source_epoch": 2, "target_probe_epoch": 4,
        "composition_order": "f_after_g_after_f_inv", "receipt_id": "receipt-1"})
    for node, edge in ((source, "maps_source_schema"), (target, "targets_domain"),
                       (fmap, "uses_frame_map"), (verification, "has_target_verification"),
                       (request, "funded_by_request")):
        s.add_edge(candidate, edge, node, {})
    s.add_edge(request, "draws_on_thinking_budget", s.nodes("ThinkingBudget")[0], {})
    s.add_edge(ag, "has_process_transfer_candidate", candidate, {})
    for _ in range(5):
        s.tick(1000)
    transferred = [n for n in s.nodes("ProcessSchema")
                   if s.node(n)["attrs"].get("provenance") == "verified_process_transfer"]
    assert len(transferred) == 1
    assert s.node(transferred[0])["attrs"]["verification_receipt"] == "receipt-1"


def test_graph_rule_rejects_wrong_frame_even_with_receipt():
    agent = Agent(extra_seeds=("process_transfer",),
                  policy_overrides={"ProcessTransferPolicy": {"enabled": 1.0}})
    s, ag = agent.s, agent.ag
    source = s.add_node("ProcessSchema", {"name": "src", "operator": "op",
                                          "source_epoch": 1})
    target = s.add_node("ProcessDomain", {"name": "dst", "kind": "permutation",
                                         "probe_epoch": 2})
    fmap = s.add_node("RepresentationMap", {"is_bijection": True, "inverse_verified": True,
                                             "source_epoch": 1, "target_frame_epoch": 1})
    candidate = s.add_node("ProcessTransferCandidate", {
        "candidate_id": "bad", "status": "candidate", "map_direction": "source_to_target",
        "source_epoch": 1, "model_epoch": 0, "target_frame_epoch": 1,
        "target_probe_epoch": 2, "search_epoch": 3, "nonconjugate": False,
        "wrong_frame": True, "complete_separating_set": True,
        "target_process_name": "bad", "composed_target_program": [0]})
    request = s.add_node("ThinkingBudgetRequest", {"requester_kind": "process_transfer",
                                                    "status": "approved", "debited_epoch": 3,
                                                    "terminal_status": "completed"})
    verification = s.add_node("ProcessTransferVerification", {
        "status": "verified", "verification_kind": "fresh_native_target_effect",
        "candidate_id": "bad", "source_epoch": 1, "target_probe_epoch": 2,
        "composition_order": "f_after_g_after_f_inv", "receipt_id": "receipt-bad"})
    for node, edge in ((source, "maps_source_schema"), (target, "targets_domain"),
                       (fmap, "uses_frame_map"), (verification, "has_target_verification"),
                       (request, "funded_by_request")):
        s.add_edge(candidate, edge, node, {})
    s.add_edge(request, "draws_on_thinking_budget", s.nodes("ThinkingBudget")[0], {})
    s.add_edge(ag, "has_process_transfer_candidate", candidate, {})
    for _ in range(4):
        s.tick(1000)
    assert not [n for n in s.nodes("ProcessSchema")
                if s.node(n)["attrs"].get("provenance") == "verified_process_transfer"]


def test_graph_rule_composes_transfer_candidate_natively():
    agent = Agent(extra_seeds=("process_transfer",),
                  policy_overrides={"ProcessTransferPolicy": {"enabled": 1.0}})
    s, ag = agent.s, agent.ag
    f, f_inv = [2, 0, 1], [1, 2, 0]
    source = s.add_node("ProcessSchema", {"name": "source-rot", "kind": "permutation",
                                          "params": [1, 0, 2], "source_epoch": 2,
                                          "model_epoch": 1, "frame_epoch": 3})
    target = s.add_node("ProcessDomain", {"name": "target-domain", "kind": "permutation",
                                         "probe_epoch": 4})
    fmap = s.add_node("RepresentationMap", {"forward_map": f, "inverse_map": f_inv,
                                             "is_bijection": True, "inverse_verified": True,
                                             "complete_separating_set": True,
                                             "source_epoch": 2, "target_frame_epoch": 3})
    proposal = s.add_node("RepresentationProposal", {
        "candidate_id": "repr-1", "status": "adopted", "package_cost_complete": True,
        "source_epoch": 2, "model_epoch": 1, "frame_epoch": 3,
        "target_frame_epoch": 3})
    request = s.add_node("ThinkingBudgetRequest", {"requester_kind": "process_transfer",
                                                    "status": "approved", "debited_epoch": 4})
    for node, edge in ((source, "transfers_source_schema"),
                       (target, "transfers_to_domain"), (fmap, "uses_transfer_map")):
        s.add_edge(proposal, edge, node, {})
    s.add_edge(ag, "has_representation_proposal", proposal, {})
    s.add_edge(ag, "has_thinking_budget_request", request, {})
    s.add_edge(request, "draws_on_thinking_budget", s.nodes("ThinkingBudget")[0], {})
    for _ in range(5):
        s.tick(1000)
    candidates = list(s.neighbours(ag, "has_process_transfer_candidate"))
    assert len(candidates) == 1
    attrs = s.node(candidates[0])["attrs"]
    assert attrs["composed_target_program"] == [2, 1, 0]
    out = agent.native.evaluate(
        {"type": "ProcessApply", "p": {"type": "Var", "name": "p"},
         "state": {"type": "Var", "name": "state"}},
        {"p": attrs["composed_target_program"], "state": [0, 1, 2]})
    assert out == [2, 1, 0]


def test_registered_transfer_world_pairings_have_separating_effects():
    for pairing in ("permutation_relabel_4", "integer_matrix_basis_2"):
        for direction in ("forward", "reverse"):
            world = transfer_world(pairing, 19, direction)
            assert verify_world_conjugacy(world)
            for state in world["training_states"] + world["heldout_states"]:
                source_view = apply_world_program(world["kind"], state, world["forward_map"])
                target_effect = apply_world_program(world["kind"], source_view,
                                                    world["target_program"])
                source_effect = apply_world_program(world["kind"], state, world["source_program"])
                mapped_source_effect = apply_world_program(world["kind"], source_effect,
                                                           world["forward_map"])
                assert target_effect == mapped_source_effect
