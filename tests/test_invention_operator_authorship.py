"""P14.04 candidate operator graph authoring and human-gated promotion."""
from evaluation.process_mastery.harness import Agent


SEEDS = ("process_laws", "process_proof_adoption", "invention_operator_authorship")


def _agent():
    return Agent(extra_seeds=SEEDS,
                 policy_overrides={"InventionOperatorAuthorshipPolicy": {
                     "enabled": 1.0, "max_resource_work": 32,
                 }})


def _request(agent, *, recipe="commutator_square", left="commutator", right="commutator"):
    request = agent.s.add_node("OperatorCompositionRequest", {
        "name": "request_1", "status": "draft", "recipe": recipe,
        "left_operator": left, "right_operator": right,
        "candidate_name": "commutator_square_v1",
    })
    agent.s.add_edge(agent.ag, "has_operator_composition_request", request, {})
    return request


def _candidate(agent):
    _request(agent)
    agent.run(max_ticks=12)
    candidates = agent.nodes("CandidateOperator", name="commutator_square_v1")
    assert len(candidates) == 1
    return candidates[0]


def _measure(agent, candidate, *, gain=1, invariant_checks=20, parent_checks=20,
             proof_failures=0, work=12):
    agent.s.set_attr(candidate, "development_yield", 8)
    agent.s.set_attr(candidate, "parent_development_yield", 8 - gain)
    agent.s.set_attr(candidate, "invariant_checks", invariant_checks)
    agent.s.set_attr(candidate, "parent_invariant_checks", parent_checks)
    agent.s.set_attr(candidate, "proof_failures", proof_failures)
    agent.s.set_attr(candidate, "candidate_work", work)
    agent.s.set_attr(candidate, "status", "measured")


def test_new_combinator_is_graph_authored():
    agent = _agent()
    candidate = _candidate(agent)
    attrs = agent.attrs(candidate)
    assert attrs["authoring"] == "native_graph_rule"
    assert attrs["grammar"] == "held_algebra_v1"
    roots = agent.native.neighbours(candidate, "has_expression_root")
    assert len(roots) == 1
    root = roots[0]
    assert agent.attrs(root)["operator"] == "compose"
    children = agent.native.neighbours(root, "expr_child")
    assert len(children) == 2
    assert {agent.attrs(n)["operator"] for n in children} == {"commutator"}
    leaves = [n for child in children for n in agent.native.neighbours(child, "expr_child")]
    assert len(leaves) == 4
    assert {agent.attrs(n)["name"] for n in leaves} == {"a", "b"}


def test_unsafe_template_rejected():
    agent = _agent()
    request = _request(agent, recipe="python_eval", left="python", right="shell")
    agent.run(max_ticks=12)
    assert agent.attrs(request)["status"] == "rejected"
    assert agent.attrs(request)["rejection_reason"] == "operator_outside_held_algebra_template"
    assert not agent.nodes("CandidateOperator")


def test_candidate_cannot_change_criteria():
    agent = _agent()
    criterion = agent.s.add_node("CriterionPolicy", {"name": "frozen", "min_gain": 1.0})
    before = dict(agent.attrs(criterion))
    candidate = _candidate(agent)
    _measure(agent, candidate)
    agent.run(max_ticks=12)
    assert agent.attrs(candidate)["status"] == "awaiting_human"
    assert agent.attrs(criterion) == before


def test_promotion_requires_existing_gate():
    agent = _agent()
    candidate = _candidate(agent)
    _measure(agent, candidate)
    agent.run(max_ticks=12)
    assert agent.attrs(candidate)["status"] == "awaiting_human"
    assert not agent.nodes("InventionOperator", name="commutator_square_v1")
    approval = agent.s.add_node("OperatorPromotionApproval", {
        "status": "approved", "approval_kind": "human",
        "candidate_name": "commutator_square_v1",
        "criteria_digest": "pmb-v1-frozen-criteria",
    })
    agent.s.add_edge(agent.ag, "has_promotion_approval", approval, {})
    agent.run(max_ticks=12)
    assert agent.attrs(candidate)["status"] == "promoted"
    authored = agent.nodes("InventionOperator", name="commutator_square_v1")
    assert len(authored) == 1
    assert agent.attrs(authored[0])["approval_kind"] == "human"


def test_operator_lineage_retained():
    agent = _agent()
    candidate = _candidate(agent)
    _measure(agent, candidate)
    agent.run(max_ticks=12)
    approval = agent.s.add_node("OperatorPromotionApproval", {
        "status": "approved", "approval_kind": "human",
        "candidate_name": "commutator_square_v1",
        "criteria_digest": "pmb-v1-frozen-criteria",
    })
    agent.s.add_edge(agent.ag, "has_promotion_approval", approval, {})
    agent.run(max_ticks=12)
    authored = agent.nodes("InventionOperator", name="commutator_square_v1")[0]
    parent = agent.native.neighbours(authored, "parent_operator")
    candidate_edge = agent.native.neighbours(authored, "derived_from_candidate")
    assert len(parent) == len(candidate_edge) == 1
    assert agent.attrs(parent[0])["name"] == "commutator"
    assert candidate_edge == [candidate]
    assert agent.attrs(authored)["rollback_target"] == "commutator"
