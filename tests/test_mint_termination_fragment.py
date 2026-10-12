from scripts.analyze_mint_termination_fragment import analyze, self_check


def test_mint_fragment_self_check_includes_unbound_edge_label_contrast():
    result = self_check()
    assert result["fixtures"]["recursive_finite_key"]["accepted"] is True
    assert result["fixtures"]["edge_type_is_not_binding"]["accepted"] is False
    assert result["fixtures"]["edge_type_is_not_binding"]["progress_steps_upper_bound"] is None


def test_mint_fragment_rejects_effect_endpoint_named_like_match_edge_type():
    result = analyze(
        [{"match": [["source", "link", "target"]],
          "effects": [["add_edge", "link", "next", "target", {}]]}],
        initial_node_ids=["n0", "n1"],
        initial_edges=[["n0", "link", "n1"]],
    )
    assert result["accepted"] is False
    assert any("endpoints must be bound" in reason for reason in result["reasons"])


def test_mint_fragment_rejects_add_edge_over_attributed_initial_edge_type():
    result = analyze(
        [{"match": [["source", "link", "target"]],
          "effects": [["add_edge", "source", "link", "target", {}]]}],
        initial_node_ids=["n0", "n1"],
        initial_edges=[["n0", "link", "n1", {"weight": 1}]],
    )
    assert result["accepted"] is False
    assert any("may replace attributes" in reason for reason in result["reasons"])


def test_empty_add_edge_collision_on_attributed_edge_reports_progress_without_growth():
    from substrate_rs import _native

    substrate = _native.Substrate()
    source = substrate.add_node("Concept", {})
    target = substrate.add_node("Concept", {})
    substrate.add_edge_unchecked(source, "link", target, {"weight": 1})
    substrate.add_rule({
        "name": "empty_attribute_collision",
        "match": [["source", "link", "target"]],
        "effects": [["add_edge", "source", "link", "target", {}]],
    })

    report = substrate.run_rules_report(10, False)

    assert report["status"] == "fixed_point"
    assert report["progress_steps"] == 1
    assert report["last_progress_rule"] == "empty_attribute_collision"
    assert substrate.edge_count() == 1


def test_conversation_scoped_rule_firing_capture_commits_graph_history():
    from substrate_rs import _native

    substrate = _native.Substrate()
    agent = substrate.add_node("Agent", {})
    inbound = substrate.add_node("Message", {"text": "turn one"})
    source = substrate.add_node("Concept", {})
    target = substrate.add_node("Concept", {})
    substrate.add_edge_unchecked(source, "link", target, {})
    substrate.add_rule({
        "name": "history_receipt_rule",
        "match": [["source", "link", "target"]],
        "effects": [["add_edge", "source", "other", "target", {}]],
    })

    substrate.begin_turn_rule_firing_capture()
    substrate.run_rules(10)
    ledger_id = substrate.commit_turn_rule_firing_capture(inbound, agent)
    history_nodes = substrate.nodes("RuleFiringHistory")

    assert ledger_id is not None
    assert len(history_nodes) == 1
    first = substrate.node(history_nodes[0])["attrs"]
    assert first["schema"] == "rule_firing_history.v1"
    assert first["last_rule_name"] == "history_receipt_rule"
    assert first["last_inbound_message_id"] == inbound.value
    assert first["settlement_sequence"] == 1
    assert history_nodes[0] in substrate.neighbours(
        agent, "has_rule_firing_history")

    # A later turn with no progressing rules keeps the last actual firing.
    second_inbound = substrate.add_node("Message", {"text": "turn two"})
    substrate.begin_turn_rule_firing_capture()
    substrate.run_rules(10)
    assert substrate.commit_turn_rule_firing_capture(second_inbound, agent) is None
    assert len(substrate.nodes("RuleFiringHistory")) == 1
    unchanged = substrate.node(history_nodes[0])["attrs"]
    assert unchanged["last_rule_name"] == "history_receipt_rule"
    assert unchanged["settlement_sequence"] == 1

    persisted = substrate.graph_to_dict()
    restored = _native.Substrate()
    restored.graph_from_dict(persisted)
    restored_history = restored.nodes("RuleFiringHistory")
    assert len(restored_history) == 1
    assert restored.node(restored_history[0])["attrs"]["last_rule_name"] \
        == "history_receipt_rule"


def test_mint_fragment_rejects_incomplete_or_duplicate_initial_graph_inventory():
    rule = [{"match": [["source", "link", "target"]],
             "effects": [["add_edge", "source", "link", "target", {}]]}]
    missing_endpoint = analyze(rule, ["n0"], [["n0", "link", "n1"]])
    duplicate_fact = analyze(
        rule, ["n0", "n1"], [["n0", "link", "n1"], ["n0", "link", "n1"]])
    duplicate_node = analyze(rule, ["n0", "n0"], [])
    missing_isolated = analyze(rule, ["n0", "n1"], [["n0", "link", "n1"]])
    with_isolated = analyze(rule, ["n0", "n1", "isolated"], [["n0", "link", "n1"]])

    assert missing_endpoint["accepted"] is False
    assert duplicate_fact["accepted"] is False
    assert duplicate_node["accepted"] is False
    assert with_isolated["accepted"] is True
    assert with_isolated["initial_node_count"] == 3
    assert with_isolated["progress_steps_upper_bound"] > missing_isolated["progress_steps_upper_bound"]
    assert all(report["progress_steps_upper_bound"] is None
               for report in (missing_endpoint, duplicate_fact, duplicate_node))
