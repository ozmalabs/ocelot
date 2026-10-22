from evaluation.process_mastery.harness import Agent
from evaluation.process_mastery.native_process_execution import execute_selected, params_digest
from evaluation.process_mastery.linear_p15_v1 import _pair, _permutation


SEEDS = ("process_laws", "process_proof_adoption", "invention_operator_authorship",
         "recursive_process_improvement", "native_process_execution")


def _setup():
    agent = Agent(extra_seeds=SEEDS)
    for policy_type in ("InventionOperatorAuthorshipPolicy", "NativeProcessExecutionPolicy"):
        for node in agent.nodes(policy_type):
            agent.s.set_attr(node, "enabled", 1.0)
    for policy_type in ("RecursiveProcessImprovementPolicy", "SolverPolicy", "InventionPolicy",
                        "ProcessSchemaPolicy", "ProcessCurriculumPolicy"):
        for node in agent.nodes(policy_type):
            agent.s.set_attr(node, "enabled", 0.0)
    budgets = agent.nodes("ThinkingBudget")
    assert len(budgets) == 1
    for budget in budgets:
        agent.s.set_attr(budget, "enabled", 1.0)
        agent.s.set_attr(budget, "remaining", 1000.0)
        agent.s.set_attr(budget, "capacity", 1000.0)
    request = agent.s.add_node("OperatorCompositionRequest", {
        "name": "p16-dev", "status": "draft", "recipe": "commutator_square",
        "left_operator": "commutator", "right_operator": "commutator",
        "candidate_name": "commutator_square_v1"})
    agent.s.add_edge(agent.ag, "has_operator_composition_request", request, {})
    agent.run(max_ticks=12)
    candidate = agent.nodes("CandidateOperator", name="commutator_square_v1")[0]
    agent.s.set_attr(candidate, "source_epoch", 0.0)
    for key, value in {"development_yield": 8.0, "parent_development_yield": 7.0,
                       "invariant_checks": 8.0, "parent_invariant_checks": 8.0,
                       "proof_failures": 0.0, "candidate_work": 8.0,
                       "status": "measured"}.items():
        agent.s.set_attr(candidate, key, value)
    agent.run(max_ticks=12)
    approval = agent.s.add_node("OperatorPromotionApproval", {
        "status": "approved", "approval_kind": "human",
        "candidate_name": "commutator_square_v1",
        "criteria_digest": "pmb-v1-frozen-criteria"})
    agent.s.add_edge(agent.ag, "has_promotion_approval", approval, {})
    agent.run(max_ticks=12)
    candidate = agent.nodes("CandidateOperator", name="commutator_square_v1")[0]
    agent.add_domain("dev", "permutation", [[0, 1, 2, 3]], {})
    left_params, right_params, _ = _pair(139)
    left = agent.s.add_node("ProcessSchema", {"name": "bound-a", "kind": "permutation",
        "domain": "dev", "params": left_params, "status": "active", "source_epoch": 0,
        "source_digest": params_digest(left_params), "owner_agent": agent.ag})
    right = agent.s.add_node("ProcessSchema", {"name": "bound-b", "kind": "permutation",
        "domain": "dev", "params": right_params, "status": "active", "source_epoch": 0,
        "source_digest": params_digest(right_params), "owner_agent": agent.ag})
    agent.s.add_edge(agent.ag, "has_process_schema", left, {})
    agent.s.add_edge(agent.ag, "has_process_schema", right, {})
    task = agent.add_solve_task("dev", [0, 1, 2, 3], [3, 2, 1, 0])
    agent.s.add_edge(task, "has_process_input_a", left, {})
    agent.s.add_edge(task, "has_process_input_b", right, {})
    agent.run(max_ticks=12)
    execution = agent.nodes("NativeExecutionRequest", status="funded")[0]
    budget_request = agent.native.neighbours(execution, "has_execution_budget_request")[0]
    assert agent.s.node(budget_request)["attrs"]["status"] == "approved"
    assert agent.native.neighbours(budget_request, "draws_on_thinking_budget") == budgets
    assert agent.s.node(budget_request)["attrs"]["cost"] == 24.0
    assert agent.s.node(budget_request)["attrs"]["debited_epoch"] is not None
    return agent, candidate, task, execution


def test_graph_selected_expression_reaches_world():
    agent, _, task, request = _setup()
    initial = _permutation(149)
    result = execute_selected(agent, request, state=initial,
        authorize=lambda proposal: True,
        world_transition=lambda action: {"observed_state": [action[x] for x in initial]})
    assert result["status"] == "COMPLETED"
    assert result["receipt"]["observed_state"] == [result["proposal"]["action"][x] for x in initial]


def test_mutated_expression_changes_outcome():
    agent, candidate, _, request = _setup()
    root = agent.native.neighbours(candidate, "has_expression_root")[0]
    agent.s.set_attr(root, "operator", "unsupported")
    result = execute_selected(agent, request, state=_permutation(157),
        authorize=lambda proposal: True, world_transition=lambda action: {"observed_state": action})
    assert result["status"] == "ABSTAIN"


def test_missing_expression_abstains():
    agent, candidate, _, request = _setup()
    root = agent.native.neighbours(candidate, "has_expression_root")[0]
    agent.native.remove_edge(candidate, "has_expression_root", root)
    result = execute_selected(agent, request, state=_permutation(167),
        authorize=lambda proposal: True, world_transition=lambda action: {"observed_state": action})
    assert result["status"] == "ABSTAIN"


def test_missing_graph_bound_input_abstains():
    agent, _, _, request = _setup()
    source = agent.native.neighbours(request, "uses_process_input_a")[0]
    agent.native.remove_edge(request, "uses_process_input_a", source)
    result = execute_selected(agent, request, state=_permutation(171),
        authorize=lambda proposal: True, world_transition=lambda action: {"observed_state": action})
    assert result["status"] == "ABSTAIN"
    assert result["reason"] == "missing_or_ambiguous_source_or_expression"


def test_changed_input_epoch_abstains_before_execution():
    agent, _, _, request = _setup()
    source = agent.native.neighbours(request, "uses_process_input_a")[0]
    agent.s.set_attr(source, "source_epoch", 1.0)
    result = execute_selected(agent, request, state=_permutation(173),
        authorize=lambda proposal: True, world_transition=lambda action: {"observed_state": action})
    assert result["status"] == "ABSTAIN"
    assert result["reason"] == "stale_process_source"


def test_mutated_input_digest_abstains_before_execution():
    agent, _, _, request = _setup()
    source = agent.native.neighbours(request, "uses_process_input_a")[0]
    params = agent.s.node(source)["attrs"]["params"]
    agent.s.set_attr(source, "params", list(reversed(params)))
    result = execute_selected(agent, request, state=_permutation(179),
        authorize=lambda proposal: True, world_transition=lambda action: {"observed_state": action})
    assert result["status"] == "ABSTAIN"
    assert result["reason"] == "stale_or_unversioned_process_source_digest"


def test_revocation_blocks_execution():
    agent, _, _, request = _setup()
    agent.s.set_attr(request, "status", "revoked")
    result = execute_selected(agent, request, state=_permutation(179),
        authorize=lambda proposal: True, world_transition=lambda action: {"observed_state": action})
    assert result["status"] == "ABSTAIN"


def test_meter_includes_composition():
    agent, _, _, request = _setup()
    result = execute_selected(agent, request, state=_permutation(191),
        authorize=lambda proposal: True, world_transition=lambda action: {"observed_state": action})
    assert result["status"] == "COMPLETED"
    assert result["meter"]["compositions"] >= 1
