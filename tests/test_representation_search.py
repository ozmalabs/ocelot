"""P11.01 semantic-freeze tests for frame and description invariants."""
import json

from evaluation.process_mastery.harness import Agent
from evaluation.process_mastery.representation_cost import (
    package_description_bits, total_training_bits,
)


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


def test_graph_rule_adopts_only_lowest_verified_training_package():
    agent = Agent(extra_seeds=("representation_search",),
                  policy_overrides={"RepresentationSearchPolicy": {"enabled": 1.0},
                                    "InventionPolicy": {"enabled": 0.0}})
    s, ag = agent.s, agent.ag
    req = s.add_node("RepresentationSearchRequest", {
        "owner_id": "owner-a", "source_epoch": 1, "model_epoch": 2,
        "frame_epoch": 3, "training_split_id": "dev-a", "candidate_cap": 4,
        "operation_id": "op-1", "search_epoch": 1, "status": "funding_pending",
    })
    s.add_edge(ag, "has_representation_search_request", req, {})
    fund = s.add_node("ThinkingBudgetRequest", {
        "requester_kind": "representation_search", "status": "approved",
        "debited_epoch": 1, "operation_id": "op-1"})
    s.add_edge(req, "funded_by_request", fund, {})
    proposals = []
    for name, bits in (("large", 1000), ("small", 100)):
        p = s.add_node("RepresentationProposal", {
            "name": name, "status": "verified_candidate", "owner_id": "owner-a",
            "source_epoch": 1, "model_epoch": 2, "frame_epoch": 3,
            "training_split_id": "dev-a", "candidate_cap": 4,
            "package_cost_complete": True, "heldout_used_for_selection": False,
            "forced_frame_preserved": True, "discriminating_evidence": True,
            "training_total_bits": bits, "candidate_id": name,
            "next_frame_epoch": 4, "source_frame_id": "f3", "target_frame_id": "f4"})
        s.add_edge(req, "has_candidate_proposal", p, {})
        s.add_edge(ag, "has_representation_proposal", p, {})
        validation = s.add_node("RepresentationHeldoutValidation", {
            "candidate_id": name, "status": "scored_frozen_heldout",
            "training_model_epoch": 2, "heldout_used_for_selection": False,
            "refit_on_heldout": False, "exceptions_added": False,
            "target_effect_verified": True, "wrong_frame_acceptance": False,
            "solve_loss_pp": 0.0, "candidate_total_bits": 80,
            "baseline_total_bits": 120})
        s.add_edge(p, "has_heldout_validation", validation, {})
        proposals.append(p)
    for _ in range(6):
        s.tick(1000)
    attrs = [s.node(p)["attrs"] for p in proposals]
    assert [a["status"] for a in attrs].count("adopted") == 1
    chosen = next(a for a in attrs if a["status"] == "adopted")
    assert chosen["name"] == "small"
    assert chosen["transition_from_frame"] == "f3"
    assert chosen["transition_to_frame"] == "f4"
    assert chosen["recall_invalidated"] and chosen["transfer_invalidated"]


def test_graph_rule_funds_one_bounded_representation_search():
    agent = Agent(extra_seeds=("representation_search", "process_transfer"),
                  policy_overrides={"RepresentationSearchPolicy": {"enabled": 1.0},
                                    "ProcessTransferPolicy": {"enabled": 1.0}},
                  budget={"enabled": 1.0, "remaining": 3.0,
                          "refill_per_epoch": 0.0, "last_refill_epoch": 0.0})
    s, ag = agent.s, agent.ag
    mode = next(iter(s.neighbours(ag, "has_network_mode_state")))
    epoch = s.node(mode)["attrs"]["epoch"]
    req = s.add_node("RepresentationSearchRequest", {
        "owner_id": "owner-b", "source_epoch": 7, "model_epoch": 2,
        "frame_epoch": 5, "training_split_id": "dev-b", "candidate_cap": 16,
        "operation_id": "search-b", "search_epoch": epoch,
        "training_only": True, "status": "requested"})
    s.add_edge(ag, "has_representation_search_request", req, {})
    for _ in range(6):
        s.tick(1000)
    funded = list(s.neighbours(req, "funded_by_request"))
    assert len(funded) == 1
    attrs = s.node(funded[0])["attrs"]
    assert attrs["requester_kind"] == "representation_search"
    assert attrs["source_key"] == "search-b"
    assert s.node(req)["attrs"]["status"] == "funding_pending"


def test_heldout_can_reject_training_choice_but_cannot_replace_it():
    agent = Agent(extra_seeds=("representation_search",),
                  policy_overrides={"RepresentationSearchPolicy": {"enabled": 1.0}})
    s, ag = agent.s, agent.ag
    req = s.add_node("RepresentationSearchRequest", {
        "owner_id": "owner-h", "source_epoch": 1, "model_epoch": 2,
        "frame_epoch": 3, "training_split_id": "dev-h", "candidate_cap": 4,
        "operation_id": "op-h", "search_epoch": 6, "status": "funding_pending"})
    s.add_edge(ag, "has_representation_search_request", req, {})
    fund = s.add_node("ThinkingBudgetRequest", {"requester_kind": "representation_search",
                                                 "status": "approved", "debited_epoch": 6,
                                                 "operation_id": "op-h"})
    s.add_edge(req, "funded_by_request", fund, {})
    nodes = []
    for name, train_bits, held_bits in (("train-winner", 100, 300),
                                        ("heldout-favorite", 200, 50)):
        p = s.add_node("RepresentationProposal", {
            "candidate_id": name, "status": "verified_candidate", "owner_id": "owner-h",
            "source_epoch": 1, "model_epoch": 2, "frame_epoch": 3,
            "training_split_id": "dev-h", "candidate_cap": 4,
            "package_cost_complete": True, "heldout_used_for_selection": False,
            "forced_frame_preserved": True, "discriminating_evidence": True,
            "training_total_bits": train_bits})
        validation = s.add_node("RepresentationHeldoutValidation", {
            "candidate_id": name, "status": "scored_frozen_heldout",
            "training_model_epoch": 2, "heldout_used_for_selection": False,
            "refit_on_heldout": False, "exceptions_added": False,
            "target_effect_verified": True, "wrong_frame_acceptance": False,
            "solve_loss_pp": 0.0, "candidate_total_bits": held_bits,
            "baseline_total_bits": 150})
        s.add_edge(req, "has_candidate_proposal", p, {})
        s.add_edge(ag, "has_representation_proposal", p, {})
        s.add_edge(p, "has_heldout_validation", validation, {})
        nodes.append(p)
    for _ in range(5):
        s.tick(1000)
    states = [s.node(p)["attrs"]["status"] for p in nodes]
    assert states == ["selected_for_heldout_validation", "verified_candidate"]
    assert not any(x == "adopted" for x in states)
    assert s.node(req)["attrs"]["status"] == "holdout_pending"


def test_graph_rule_verifies_training_cost_and_discrimination_before_selection():
    agent = Agent(extra_seeds=("representation_search",),
                  policy_overrides={"RepresentationSearchPolicy": {"enabled": 1.0}})
    s, ag = agent.s, agent.ag
    req = s.add_node("RepresentationSearchRequest", {"owner_id": "owner-d",
        "source_epoch": 1, "model_epoch": 2, "frame_epoch": 3,
        "training_split_id": "train-d", "candidate_cap": 16})
    s.add_edge(ag, "has_representation_search_request", req, {})
    passing = s.add_node("RepresentationProposal", {"candidate_id": "pass",
        "status": "candidate", "owner_id": "owner-d", "source_epoch": 1,
        "model_epoch": 2, "frame_epoch": 3, "package_bits": 80})
    passing_validation = s.add_node("RepresentationDevelopmentValidation", {
        "candidate_id": "pass", "status": "scored_frozen_training",
        "training_split_id": "train-d", "training_model_epoch": 2,
        "package_bits": 80, "residual_bits": 24, "total_bits": 104,
        "discriminating_rows": 3, "heldout_used": False})
    failing = s.add_node("RepresentationProposal", {"candidate_id": "fail",
        "status": "candidate", "owner_id": "owner-d", "source_epoch": 1,
        "model_epoch": 2, "frame_epoch": 3, "package_bits": 80})
    failing_validation = s.add_node("RepresentationDevelopmentValidation", {
        "candidate_id": "fail", "status": "scored_frozen_training",
        "training_split_id": "train-d", "training_model_epoch": 2,
        "package_bits": 80, "residual_bits": 24, "total_bits": 105,
        "discriminating_rows": 2, "heldout_used": False})
    for proposal, validation in ((passing, passing_validation),
                                 (failing, failing_validation)):
        s.add_edge(req, "has_candidate_proposal", proposal, {})
        s.add_edge(proposal, "has_development_validation", validation, {})
    for _ in range(5):
        s.tick(1000)
    assert s.node(passing)["attrs"]["status"] == "verified_candidate"
    assert s.node(passing)["attrs"]["training_total_bits"] == 104
    assert s.node(failing)["attrs"]["status"] == "candidate"


def test_graph_owned_training_select_then_heldout_adoption_chain():
    agent = Agent(extra_seeds=("representation_search",),
                  policy_overrides={"RepresentationSearchPolicy": {"enabled": 1.0}})
    s, ag = agent.s, agent.ag
    req = s.add_node("RepresentationSearchRequest", {"owner_id": "owner-e",
        "source_epoch": 1, "model_epoch": 2, "frame_epoch": 3,
        "training_split_id": "train-e", "candidate_cap": 16,
        "operation_id": "op-e", "search_epoch": 7, "status": "funding_pending"})
    s.add_edge(ag, "has_representation_search_request", req, {})
    fund = s.add_node("ThinkingBudgetRequest", {"requester_kind": "representation_search",
        "status": "approved", "debited_epoch": 7, "operation_id": "op-e"})
    s.add_edge(req, "funded_by_request", fund, {})
    proposal = s.add_node("RepresentationProposal", {"candidate_id": "candidate-e",
        "status": "candidate", "owner_id": "owner-e", "source_epoch": 1,
        "model_epoch": 2, "frame_epoch": 3, "training_split_id": "train-e",
        "candidate_cap": 16, "package_cost_complete": True,
        "heldout_used_for_selection": False, "forced_frame_preserved": True,
        "package_bits": 90, "next_frame_epoch": 4,
        "source_frame_id": "frame-3", "target_frame_id": "frame-4"})
    dev = s.add_node("RepresentationDevelopmentValidation", {
        "candidate_id": "candidate-e", "status": "scored_frozen_training",
        "training_split_id": "train-e", "training_model_epoch": 2,
        "package_bits": 90, "residual_bits": 10, "total_bits": 100,
        "discriminating_rows": 5, "heldout_used": False})
    heldout = s.add_node("RepresentationHeldoutValidation", {
        "candidate_id": "candidate-e", "status": "scored_frozen_heldout",
        "training_model_epoch": 2, "heldout_used_for_selection": False,
        "refit_on_heldout": False, "exceptions_added": False,
        "target_effect_verified": True, "wrong_frame_acceptance": False,
        "solve_loss_pp": 1.0, "candidate_total_bits": 95,
        "baseline_total_bits": 120})
    s.add_edge(req, "has_candidate_proposal", proposal, {})
    s.add_edge(ag, "has_representation_proposal", proposal, {})
    s.add_edge(proposal, "has_development_validation", dev, {})
    s.add_edge(proposal, "has_heldout_validation", heldout, {})
    for _ in range(8):
        s.tick(1000)
    attrs = s.node(proposal)["attrs"]
    assert attrs["status"] == "adopted"
    assert attrs["training_total_bits"] == 100
    assert attrs["adopted_frame_epoch"] == 4
    assert attrs["transition_from_frame"] == "frame-3"
    assert attrs["transition_to_frame"] == "frame-4"


def test_graph_rule_mints_candidate_from_acquired_transform_evidence():
    agent = Agent(extra_seeds=("representation_search", "process_transfer"),
                  policy_overrides={"RepresentationSearchPolicy": {"enabled": 1.0},
                                    "ProcessTransferPolicy": {"enabled": 1.0}},
                  budget={"enabled": 1.0, "remaining": 3.0,
                          "refill_per_epoch": 0.0, "last_refill_epoch": 0.0})
    s, ag = agent.s, agent.ag
    mode = next(iter(s.neighbours(ag, "has_network_mode_state")))
    epoch = s.node(mode)["attrs"]["epoch"]
    req = s.add_node("RepresentationSearchRequest", {
        "owner_id": "owner-c", "source_epoch": 7, "model_epoch": 2,
        "frame_epoch": 5, "training_split_id": "dev-c", "candidate_cap": 16,
        "operation_id": "search-c", "search_epoch": epoch,
        "training_only": True, "status": "requested"})
    source = s.add_node("ProcessSchema", {"name": "source-process", "kind": "permutation",
                                          "operator": "swap", "params": [1, 0], "source_epoch": 7,
                                          "model_epoch": 2, "frame_epoch": 5})
    target = s.add_node("ProcessDomain", {"name": "target-domain", "kind": "permutation",
                                         "probe_epoch": 3})
    fmap = s.add_node("RepresentationMap", {"forward_map": [1, 0], "inverse_map": [1, 0],
                                             "is_bijection": True, "inverse_verified": True,
                                             "complete_separating_set": True,
                                             "source_epoch": 7, "target_frame_epoch": 5})
    evidence = s.add_node("RepresentationTransformEvidence", {
        "candidate_id": "candidate-c", "status": "acquired_transform",
        "owner_id": "owner-c", "source_epoch": 7, "model_epoch": 2,
        "frame_epoch": 5, "target_frame_epoch": 5, "source_frame_id": "sf-5",
        "target_frame_id": "tf-5", "training_split_id": "dev-c",
        "canonical_package": {"model": "m", "map": [1, 0], "decoder": "d"},
        "package_bits": 320, "training_residual_bits": 16,
        "training_total_bits": 336, "package_cost_complete": True,
        "forced_frame_preserved": True, "discriminating_evidence": True})
    s.add_edge(ag, "has_representation_search_request", req, {})
    s.add_edge(req, "has_transform_evidence", evidence, {})
    s.add_edge(evidence, "has_transfer_map", fmap, {})
    s.add_edge(evidence, "has_source_process", source, {})
    s.add_edge(evidence, "has_target_domain", target, {})
    transfer_fund = s.add_node("ThinkingBudgetRequest", {
        "requester_kind": "process_transfer", "status": "approved",
        "debited_epoch": 3, "terminal_status": "completed"})
    s.add_edge(ag, "has_thinking_budget_request", transfer_fund, {})
    s.add_edge(transfer_fund, "draws_on_thinking_budget", s.nodes("ThinkingBudget")[0], {})
    for _ in range(12):
        s.tick(1000)
    proposals = list(s.neighbours(req, "has_candidate_proposal"))
    assert len(proposals) == 1, {
        "request_status": s.node(req)["attrs"].get("status"),
        "fund_attrs": [{k: s.node(n)["attrs"].get(k) for k in
                        ("status", "debited_epoch", "operation_id", "requester_kind")}
                       for n in s.neighbours(req, "funded_by_request")],
        "evidence": s.node(evidence)["attrs"],
    }
    attrs = s.node(proposals[0])["attrs"]
    assert attrs["candidate_id"] == "candidate-c"
    assert attrs["canonical_package"] == {"model": "m", "map": [1, 0], "decoder": "d"}
    assert attrs["training_total_bits"] == 336
    assert attrs["status"] == "candidate"
    assert attrs["heldout_used_for_selection"] is False
    assert list(s.neighbours(proposals[0], "uses_transfer_map")) == [fmap]
    assert list(s.neighbours(proposals[0], "transfers_source_schema")) == [source]
    assert list(s.neighbours(proposals[0], "transfers_to_domain")) == [target]
    proposal = proposals[0]
    development = s.add_node("RepresentationDevelopmentValidation", {
        "candidate_id": "candidate-c", "status": "scored_frozen_training",
        "training_split_id": "dev-c", "training_model_epoch": 2,
        "package_bits": 320, "residual_bits": 16, "total_bits": 336,
        "discriminating_rows": 4, "heldout_used": False})
    heldout = s.add_node("RepresentationHeldoutValidation", {
        "candidate_id": "candidate-c", "status": "scored_frozen_heldout",
        "training_model_epoch": 2, "heldout_used_for_selection": False,
        "refit_on_heldout": False, "exceptions_added": False,
        "target_effect_verified": True, "wrong_frame_acceptance": False,
        "solve_loss_pp": 0.0, "candidate_total_bits": 340,
        "baseline_total_bits": 400})
    s.add_edge(proposal, "has_development_validation", development, {})
    s.add_edge(proposal, "has_heldout_validation", heldout, {})
    for _ in range(6):
        s.tick(1000)
    assert s.node(proposal)["attrs"]["status"] == "adopted"
    transfer_candidates = list(s.neighbours(ag, "has_process_transfer_candidate"))
    assert len(transfer_candidates) == 1
    candidate = transfer_candidates[0]
    candidate_attrs = s.node(candidate)["attrs"]
    assert candidate_attrs["composed_target_program"] == [1, 0]
    observed = agent.native.evaluate(
        {"type": "ProcessApply", "p": {"type": "Var", "name": "p"},
         "state": {"type": "Var", "name": "state"}},
        {"p": candidate_attrs["composed_target_program"], "state": [0, 1]})
    assert observed == [1, 0]
    receipt = s.add_node("ProcessTransferVerification", {
        "status": "verified", "verification_kind": "fresh_native_target_effect",
        "candidate_id": "candidate-c->target-domain", "source_epoch": 7,
        "target_probe_epoch": 3, "composition_order": "f_after_g_after_f_inv",
        "receipt_id": "native-effect-c"})
    s.add_edge(candidate, "has_target_verification", receipt, {})
    for _ in range(4):
        s.tick(1000)
    assert len([n for n in s.nodes("ProcessSchema")
                if s.node(n)["attrs"].get("provenance") == "verified_process_transfer"]) == 1


def test_canonical_cost_counts_mapping_decoder_and_residuals():
    package = {key: {} for key in (
        "basis", "grain", "aperture", "latent_schema", "model", "parameters",
        "forward_map", "inverse_map", "exceptions", "decoder",
        "retained_residuals", "lost_residuals", "escape_residuals")}
    minimal = package_description_bits(package)
    with_map = {**package, "forward_map": {"0": 1, "1": 0},
                "inverse_map": {"0": 1, "1": 0},
                "decoder": {"code": "decode"}}
    assert package_description_bits(with_map) > minimal
    assert total_training_bits(with_map, [{"id": "r1"}, {"id": "r2"}],
                               bits_per_record=12) == package_description_bits(with_map) + 24


def test_canonical_cost_rejects_incomplete_or_nonfinite_package():
    package = {key: {} for key in (
        "basis", "grain", "aperture", "latent_schema", "model", "parameters",
        "forward_map", "inverse_map", "exceptions", "decoder",
        "retained_residuals", "lost_residuals", "escape_residuals")}
    package.pop("decoder")
    try:
        package_description_bits(package)
        assert False, "decoder omission must be rejected"
    except ValueError:
        pass
    package["decoder"] = {"nan": float("nan")}
    try:
        package_description_bits(package)
        assert False, "non-finite costs must be rejected"
    except ValueError:
        pass
