from __future__ import annotations

from evaluation.native_cycle_measurement import measure_native_cycle
import evaluation.native_cycle_measurement as native_cycle_measurement
from evaluation.native_authority_audit import audit_python_cognitive_branches
from domains.question_driver import QuestionDriver, QuestionPack


def _assert_bounded(result):
    assert result["resource_assertions"] == {
        "bounded_steps": True,
        "bounded_graph": True,
        "bounded_rss": True,
        "rss_measured": True,
        "replay_equal": True,
    }


def test_bounded_native_cycle_measurement_records_native_and_graph_evidence():
    result = measure_native_cycle(iterations=3, warmup=1)
    assert result["schema"] == "native-cycle-measurement-v3"
    assert result["profile"] == "fast"
    assert result["iterations"] == 3
    assert result["replay_equal"] is True
    assert result["replay_difference"] is None
    assert result["steps"] == [0, 0, 0]
    assert result["graph"]["node_count"] >= 2
    assert result["graph"]["edge_count"] >= 1
    assert result["latency_ms"]["min"] >= 0
    assert result["peak_rss_bytes"] > 0
    assert result["rss_assertion"] == {
        "basis": "workload_rss_growth",
        "measured_field": "rss_delta_bytes",
        "limit_field": "resource_limits.rss_growth_bytes",
        "limit_bytes": 100 * 1024 * 1024,
        "absolute_fields_observability_only": True,
    }
    assert result["resource_limits"]["rss_bytes"] == 1024 * 1024 * 1024
    assert result["rss_delta_bytes"] <= result["resource_limits"]["rss_growth_bytes"]
    _assert_bounded(result)


def test_bounded_rss_uses_workload_growth_not_full_pytest_process_peak(monkeypatch):
    readings = iter((2 * 1024 * 1024 * 1024, 2 * 1024 * 1024 * 1024 + 1024 * 1024))
    monkeypatch.setattr(native_cycle_measurement, "_current_rss_bytes", lambda: next(readings))

    result = measure_native_cycle(iterations=1, warmup=0, profile="fast")

    assert result["rss_before_bytes"] == 2 * 1024 * 1024 * 1024
    assert result["rss_after_bytes"] == 2 * 1024 * 1024 * 1024 + 1024 * 1024
    assert result["peak_rss_bytes"] == result["rss_after_bytes"]
    assert result["rss_delta_bytes"] == 1024 * 1024
    assert result["resource_assertions"]["bounded_rss"] is True
    assert result["rss_assertion"]["basis"] == "workload_rss_growth"


def test_native_cycle_probe_transition_is_graph_authored_and_bounded():
    result = measure_native_cycle(iterations=1, warmup=0)
    assert result["reports"][0]["steps"] == 1
    assert result["steps"] == [1]
    probe = next(node for node in result["graph"]["nodes"] if node["type"] == "Phase7ANativeProbe")
    assert probe["attrs"]["ran"] == 1


def test_native_profiles_measure_depth_recovery_and_long_dialogue_with_replay():
    fast = measure_native_cycle(iterations=2, warmup=1, profile="fast")
    deep = measure_native_cycle(iterations=2, warmup=0, profile="deep")
    recovery = measure_native_cycle(iterations=2, warmup=0, profile="recovery")
    dialogue = measure_native_cycle(iterations=2, warmup=0, profile="long_dialogue")

    assert deep["replay_equal"] is True
    assert recovery["replay_equal"] is True
    assert dialogue["replay_equal"] is True
    _assert_bounded(deep)
    _assert_bounded(recovery)
    _assert_bounded(dialogue)
    assert deep["steps"][0] > fast["steps"][0]
    assert recovery["steps"][0] > fast["steps"][0]
    assert dialogue["graph"]["node_count"] > fast["graph"]["node_count"]
    assert dialogue["graph"]["edge_count"] > fast["graph"]["edge_count"]
    assert max(deep["steps"]) <= 512
    assert max(recovery["steps"]) <= 512
    assert max(dialogue["steps"]) <= 512


def test_dense_graph_profile_is_bounded_and_native_trace_is_authoritative():
    result = measure_native_cycle(iterations=2, warmup=0, profile="dense_graph")

    assert result["replay_equal"] is True
    assert result["graph"]["node_count"] == 22
    assert result["graph"]["edge_count"] == 44
    _assert_bounded(result)
    authority = result["native_authority"]
    assert authority["outcome_source"] == "native_trace"
    assert authority["python_outcome_selection"] is False
    assert authority["native_trace_observed"] is True
    assert authority["native_step_trace_alignment"] is True
    assert authority["graph_changed_after_native_cycle"] is True

    before = [node for node in authority["pre_cycle_graph"]["nodes"]
              if node["type"] == "Phase7DenseCandidate"]
    after = [node for node in result["graph"]["nodes"]
             if node["type"] == "Phase7DenseCandidate"]
    assert {node["attrs"]["resolved"] for node in before} == {0}
    assert {node["attrs"]["resolved"] for node in after} == {1}


def test_ambiguity_profile_preserves_native_authority_across_competing_candidates():
    result = measure_native_cycle(iterations=2, warmup=0, profile="ambiguity")

    assert result["replay_equal"] is True
    _assert_bounded(result)
    authority = result["native_authority"]
    assert authority["outcome_source"] == "native_trace"
    assert authority["python_outcome_selection"] is False
    assert authority["native_trace_observed"] is True
    assert authority["native_step_trace_alignment"] is True
    assert authority["graph_changed_after_native_cycle"] is True
    candidates = [node for node in result["graph"]["nodes"]
                  if node["type"] == "Phase7AmbiguousCandidate"]
    assert len(candidates) == 8
    assert {node["attrs"]["state"] for node in candidates} == {1}
    assert result["graph"]["node_count"] == 18
    assert result["graph"]["edge_count"] == 24


def test_repeated_gap_profile_covers_native_detect_and_repair_envelope():
    result = measure_native_cycle(iterations=2, warmup=0, profile="repeated_gaps")

    assert result["replay_equal"] is True
    # One native rule application advances all matching gaps; the second
    # native rule then advances the repaired state.  Steps are rule firings,
    # not a Python loop over gap nodes.
    assert result["steps"][0] == 2
    assert max(result["steps"]) <= 512
    _assert_bounded(result)
    authority = result["native_authority"]
    assert authority["outcome_source"] == "native_trace"
    assert authority["python_outcome_selection"] is False
    assert authority["native_trace_observed"] is True
    assert authority["native_step_trace_alignment"] is True
    gaps = [node for node in result["graph"]["nodes"]
            if node["type"] == "Phase7RepeatedGap"]
    assert len(gaps) == 8
    assert {node["attrs"]["state"] for node in gaps} == {2}
    assert result["graph"]["node_count"] == 18
    assert result["graph"]["edge_count"] == 16


def test_phase7e_broader_loads_keep_replay_and_native_authority():
    extended = measure_native_cycle(iterations=2, warmup=0, profile="extended_dialogue")
    ambiguous = measure_native_cycle(iterations=2, warmup=0, profile="high_ambiguity")
    growth = measure_native_cycle(iterations=2, warmup=0, profile="graph_growth")

    for result in (extended, ambiguous, growth):
        assert result["replay_equal"] is True
        _assert_bounded(result)
        authority = result["native_authority"]
        assert authority["outcome_source"] == "native_trace"
        assert authority["python_outcome_selection"] is False
        assert authority["native_trace_observed"] is True
        assert authority["native_step_trace_alignment"] is True
        assert authority["graph_changed_after_native_cycle"] is True

    # Canonical graph residence includes native rule nodes/edges, as in the
    # existing dense profile; the workload payload itself is 96/96.
    assert extended["graph"]["node_count"] == 106
    assert extended["graph"]["edge_count"] == 104
    assert extended["steps"] == [1, 0]
    assert ambiguous["graph"]["node_count"] == 42
    assert ambiguous["graph"]["edge_count"] == 72
    assert ambiguous["steps"] == [1, 0]
    assert growth["graph"]["node_count"] == 58
    assert growth["graph"]["edge_count"] == 152
    assert growth["steps"] == [1, 0]

    extended_events = [node for node in extended["graph"]["nodes"]
                       if node["type"] == "Phase7ExtendedDialogueEvent"]
    assert len(extended_events) == 96
    assert {node["attrs"]["processed"] for node in extended_events} == {1}
    growth_candidates = [node for node in growth["graph"]["nodes"]
                         if node["type"] == "Phase7GraphGrowthCandidate"]
    assert len(growth_candidates) == 48
    assert {node["attrs"]["resolved"] for node in growth_candidates} == {1}


def test_phase3_to_phase6_workloads_are_graph_authored_and_resource_bounded():
    expected_types = {
        "phase3_async": "Phase3AsyncResidual",
        "phase4_deliberation": "Phase4DeliberationCandidate",
        "phase5_recurrence": "Phase5RecurrenceIdentity",
        "phase6_production": "Phase6ProductionSurface",
    }
    for profile, node_type in expected_types.items():
        result = measure_native_cycle(iterations=2, warmup=0, profile=profile)
        _assert_bounded(result)
        assert result["replay_equal"] is True
        assert result["rss_before_bytes"] > 0
        assert result["rss_after_bytes"] > 0
        assert result["rss_delta_bytes"] >= 0
        authority = result["native_authority"]
        assert authority["graph_authored_workload"] is True
        assert authority["outcome_source"] == "native_trace"
        assert authority["python_outcome_selection"] is False
        assert authority["native_trace_observed"] is True
        assert authority["native_step_trace_alignment"] is True
        assert authority["native_trace_rule_ids"]
        nodes = [node for node in result["graph"]["nodes"] if node["type"] == node_type]
        assert len(nodes) == result["workload_size"]
        assert result["graph"]["node_count"] <= result["resource_limits"]["nodes"]
        assert result["graph"]["edge_count"] <= result["resource_limits"]["edges"]


def test_python_cognitive_branch_audit_reports_migration_debt_explicitly():
    audit = audit_python_cognitive_branches(".")
    assert audit["schema"] == "native-authority-python-branch-audit-v2"
    assert audit["files_scanned"] > 0
    assert audit["finding_count"] == len(audit["findings"])
    assert audit["total_call_count"] == audit["finding_count"] + audit["bound_count"]
    bound = [item for item in audit["bound_calls"]
             if item["cluster"] == "question_driver.deliberation_pump"]
    assert len(bound) == 1
    assert bound[0]["authority"] == "native_graph_bound"
    assert bound[0]["provenance"] == "native_trace:question_driver_deliberation"
    assert bound[0]["exception_rule"] == "question_driver_deliberation_native_trace_v1"
    assert not any(item["file"] == "domains/question_driver.py"
                   and item["function"] == "_native_deliberation_cycle"
                   for item in audit["findings"])
    assert audit["status"] in {"clean", "review_required"}
    # Existing Python orchestration is intentionally not silently promoted to
    # native authority.  The audit must expose it for the next migration.
    for finding in audit["findings"]:
        assert finding["authority"] == "requires_native_boundary_review"


def test_curiosity_topic_settlement_is_native_and_receipted():
    from domains.curiosity_topic_ingest import maintain_topic_interest
    from substrate.world_adapter import WorldAdapter

    wa = WorldAdapter(seeds=())
    maintain_topic_interest(wa, {"topic": "unfamiliar concept"}, 1,
                            attempt_ground=False)
    receipts = list(wa.s.nodes("NativeCuriosityReceipt"))
    assert len(receipts) == 1
    attrs = wa.s.node(receipts[0])["attrs"]
    assert attrs["provenance"] == "native_rule_readback:curiosity_topic_selection"
    assert attrs["outcome_source"] == "native_rule_readback"
    assert attrs["python_outcome_selection"] is False
    audit = audit_python_cognitive_branches(".")
    bound = [item for item in audit["bound_calls"]
             if item["cluster"] == "curiosity_topic_selection.native_settlement"]
    assert len(bound) == 1


def test_cognitive_tick_native_schedule_is_receipted_without_reflex_credit():
    from substrate.world_adapter import WorldAdapter

    wa = WorldAdapter(seeds=())
    wa.cognitive_tick(max_steps=1)
    receipts = list(wa.s.nodes("NativeCognitiveCycleReceipt"))
    assert len(receipts) == 1
    attrs = wa.s.node(receipts[0])["attrs"]
    assert attrs["schedule"] == "cognitive_legacy"
    assert attrs["provenance"] == "native_cycle_readback:cognitive_legacy"
    assert attrs["outcome_source"] == "native_cycle_readback"
    assert attrs["python_outcome_selection"] is False
    audit = audit_python_cognitive_branches(".")
    bound = [item for item in audit["bound_calls"]
             if item["cluster"] == "world_adapter.cognitive_cycle"]
    assert len(bound) == 1


def test_master_tick_native_schedule_is_receipted_separately():
    from substrate.world_adapter import WorldAdapter

    wa = WorldAdapter(seeds=())
    result = wa.master_tick()
    receipts = list(wa.s.nodes("NativeMasterCycleReceipt"))
    assert len(receipts) == 1
    attrs = wa.s.node(receipts[0])["attrs"]
    assert attrs["schedule"] == "master_legacy"
    assert attrs["provenance"] == "native_cycle_readback:master_legacy"
    assert attrs["outcome_source"] == "native_cycle_readback"
    assert attrs["python_outcome_selection"] is False
    assert result["cycle"]["steps"] == attrs["steps"]
    audit = audit_python_cognitive_branches(".")
    bound = [item for item in audit["bound_calls"]
             if item["cluster"] == "world_adapter.master_cycle"]
    assert len(bound) == 1


def test_live_world_cognitive_delegations_reuse_bound_native_cycle():
    audit = audit_python_cognitive_branches(".")
    for function, cluster in (
        ("live", "world_adapter.live_native_cycle_delegation"),
        ("live_examined", "world_adapter.live_examined_native_cycle_delegation"),
    ):
        bound = [item for item in audit["bound_calls"]
                 if item["cluster"] == cluster]
        assert len(bound) == 1
        assert bound[0]["function"] == function
        assert bound[0]["boundary"] == "delegation_to_bound_native_cycle_only"
        assert bound[0]["outcome_source"] == "native_cycle_readback"


def test_actor_goal_action_settlement_is_native_and_receipted():
    from domains import actor_goals
    from substrate.world_adapter import WorldAdapter

    wa = WorldAdapter(seeds=())
    created = actor_goals.annotate_actor_action(
        wa,
        {"predications": [["fund", "_", "renewable_energy_project"]],
         "construction": "passive"},
        [("COP", "was"), ("PPART", "funded"), ("BY", "by")],
        ["A renewable energy project", "oil company"],
    )
    assert created
    receipts = list(wa.s.nodes("NativeActorGoalReceipt"))
    assert len(receipts) == 1
    attrs = wa.s.node(receipts[0])["attrs"]
    assert attrs["provenance"] == "native_rule_readback:actor_goal_settlement"
    assert attrs["outcome_source"] == "native_rule_readback"
    assert attrs["python_outcome_selection"] is False
    audit = audit_python_cognitive_branches(".")
    bound = [item for item in audit["bound_calls"]
             if item["cluster"] == "actor_goals.actor_action_settlement"]
    assert len(bound) == 1


def test_disclaimer_candidate_settlement_is_native_and_receipted():
    from domains import actor_goals
    from substrate.world_adapter import WorldAdapter

    wa = WorldAdapter(seeds=())
    created = actor_goals.annotate_disclaimer_candidates(
        wa, "I am not responsible for that action")
    assert created
    receipts = list(wa.s.nodes("NativeDisclaimerReceipt"))
    assert len(receipts) == 1
    attrs = wa.s.node(receipts[0])["attrs"]
    assert attrs["provenance"] == "native_rule_readback:disclaimer_codebook"
    assert attrs["outcome_source"] == "native_rule_readback"
    assert attrs["python_outcome_selection"] is False
    audit = audit_python_cognitive_branches(".")
    bound = [item for item in audit["bound_calls"]
             if item["cluster"] == "actor_goals.disclaimer_settlement"]
    assert len(bound) == 1


def test_action_pair_settlement_is_native_and_receipted():
    from domains import actor_goals
    from substrate.world_adapter import WorldAdapter

    wa = WorldAdapter(seeds=())
    root = wa.agent
    first = wa.s.add_node("ActorAction", {
        "actor": "oil_company", "verb": "fund", "object": "renewable_energy",
    })
    second = wa.s.add_node("ActorAction", {
        "actor": "oil_company", "verb": "oppose", "object": "renewable_energy",
    })
    wa.inner.add_edge_unchecked(root, "has_actor_action", first)
    wa.inner.add_edge_unchecked(root, "has_actor_action", second)
    created = actor_goals.annotate_action_pairs(wa)
    assert created
    receipts = list(wa.s.nodes("NativeActionPairReceipt"))
    assert len(receipts) == 1
    attrs = wa.s.node(receipts[0])["attrs"]
    assert attrs["provenance"] == "native_rule_readback:action_pair_codebook"
    assert attrs["outcome_source"] == "native_rule_readback"
    assert attrs["python_outcome_selection"] is False
    audit = audit_python_cognitive_branches(".")
    bound = [item for item in audit["bound_calls"]
             if item["cluster"] == "actor_goals.action_pair_settlement"]
    assert len(bound) == 1


def test_epistemic_assessment_is_native_and_receipted():
    from domains import actor_goals
    from substrate.world_adapter import WorldAdapter

    wa = WorldAdapter(seeds=())
    readings = actor_goals.assess_epistemic_lean(wa)
    receipts = list(wa.s.nodes("NativeEpistemicAssessmentReceipt"))
    assert len(receipts) == 1
    attrs = wa.s.node(receipts[0])["attrs"]
    assert attrs["reading_count"] == len(readings)
    assert attrs["provenance"] == "native_rule_readback:epistemic_assessment"
    assert attrs["outcome_source"] == "native_rule_readback"
    assert attrs["python_outcome_selection"] is False
    audit = audit_python_cognitive_branches(".")
    bound = [item for item in audit["bound_calls"]
             if item["cluster"] == "actor_goals.epistemic_assessment"]
    assert len(bound) == 2


def test_actor_rule_authoring_execution_is_native_and_receipted():
    from domains import actor_goals
    from substrate.world_adapter import WorldAdapter

    wa = WorldAdapter(seeds=())
    actor_goals.ensure_conflicting_goals_defaults(wa)
    actor_goals.annotate_disclaimer_candidates(
        wa, "I am not responsible for that action")
    result = actor_goals.ensure_conflicting_goals_rule(wa)
    assert result is True
    receipts = list(wa.s.nodes("NativeActorRuleAuthoringReceipt"))
    assert receipts
    attrs = wa.s.node(receipts[-1])["attrs"]
    assert attrs["provenance"] == (
        "native_rule_readback:actor_goal_authored_rule")
    assert attrs["outcome_source"] == "native_rule_readback"
    assert attrs["python_outcome_selection"] is False
    audit = audit_python_cognitive_branches(".")
    bound = [item for item in audit["bound_calls"]
             if item["cluster"] == "actor_goals.authored_rule_execution"]
    assert len(bound) == 1


def test_meaning_inference_slot_settlement_is_native_and_receipted():
    from domains import meaning_inference
    from substrate.world_adapter import WorldAdapter

    wa = WorldAdapter(seeds=())
    concept = wa.s.add_node("Concept", {"name": "bird"})
    wa.inner.add_edge_unchecked(wa.agent, "has_concept", concept)
    created = meaning_inference.annotate_predication_slots(
        wa, {"predications": [["is", "bird", "animal"]]})
    assert created
    receipts = list(wa.s.nodes("NativeMeaningInferenceReceipt"))
    assert len(receipts) == 1
    attrs = wa.s.node(receipts[0])["attrs"]
    assert attrs["provenance"] == (
        "native_rule_readback:selectional_inference")
    assert attrs["outcome_source"] == "native_rule_readback"
    assert attrs["python_outcome_selection"] is False
    audit = audit_python_cognitive_branches(".")
    bound = [item for item in audit["bound_calls"]
             if item["cluster"] == "meaning_inference.predication_slot_settlement"]
    assert len(bound) == 1


def test_meaning_inference_fact_settlement_is_native_and_receipted():
    from domains import meaning_inference
    from substrate.world_adapter import WorldAdapter

    wa = WorldAdapter(seeds=())
    concept = wa.s.add_node("Concept", {"name": "bird"})
    wa.inner.add_edge_unchecked(wa.agent, "has_concept", concept)
    created = meaning_inference.annotate_predication_facts(
        wa, {"predications": [["is_a", "bird", "animal"]]})
    assert created
    receipts = list(wa.s.nodes("NativeMeaningInferenceReceipt"))
    assert len(receipts) == 1
    attrs = wa.s.node(receipts[0])["attrs"]
    assert attrs["provenance"] == (
        "native_rule_readback:definitional_inference")
    assert attrs["outcome_source"] == "native_rule_readback"
    assert attrs["python_outcome_selection"] is False
    audit = audit_python_cognitive_branches(".")
    bound = [item for item in audit["bound_calls"]
             if item["cluster"] == "meaning_inference.predication_fact_settlement"]
    assert len(bound) == 1


def test_meaning_inference_morphology_settlement_is_native_and_receipted():
    from domains import meaning_inference
    from substrate.world_adapter import WorldAdapter

    wa = WorldAdapter(seeds=())
    concept = wa.s.add_node("Concept", {"name": "florbitis", "oov": 1.0,
                                         "is_pronoun": 0.0})
    wa.inner.add_edge_unchecked(wa.agent, "has_concept", concept)
    created = meaning_inference.annotate_affix_candidates(
        wa, {"predications": [["is", "florbitis", "animal"]]})
    assert created
    receipts = list(wa.s.nodes("NativeMeaningInferenceReceipt"))
    assert len(receipts) == 1
    attrs = wa.s.node(receipts[0])["attrs"]
    assert attrs["provenance"] == (
        "native_rule_readback:morphological_inference")
    assert attrs["outcome_source"] == "native_rule_readback"
    assert attrs["python_outcome_selection"] is False
    audit = audit_python_cognitive_branches(".")
    bound = [item for item in audit["bound_calls"]
             if item["cluster"] == "meaning_inference.morphology_settlement"]
    assert len(bound) == 1


def test_meaning_inference_relational_signature_settlement_is_native_and_receipted():
    from domains import meaning_inference
    from substrate.world_adapter import WorldAdapter

    wa = WorldAdapter(seeds=())
    concept = wa.s.add_node("Concept", {"name": "bird", "oov": 0.0})
    slot = wa.s.add_node("PredicationSlot", {
        "slot": "subject", "relation": "fear", "rel_verb_class": "event",
    })
    wa.inner.add_edge_unchecked(slot, "fills", concept)
    wa.inner.add_edge_unchecked(wa.agent, "has_predication_slot", slot)
    created = meaning_inference.annotate_relational_signatures(wa, {})
    assert created
    receipts = list(wa.s.nodes("NativeMeaningInferenceReceipt"))
    assert len(receipts) == 1
    attrs = wa.s.node(receipts[0])["attrs"]
    assert attrs["provenance"] == (
        "native_rule_readback:structural_analogy")
    assert attrs["outcome_source"] == "native_rule_readback"
    assert attrs["python_outcome_selection"] is False
    audit = audit_python_cognitive_branches(".")
    bound = [item for item in audit["bound_calls"]
             if item["cluster"] == "meaning_inference.relational_signature_settlement"]
    assert len(bound) == 1


def test_recount_scene_settlement_is_native_and_receipted():
    from domains import recount_faculty
    from substrate.world_adapter import WorldAdapter

    class _World:
        def _add_lex_entry(self, *args, **kwargs):
            return None

    wa = WorldAdapter(seeds=())
    result = recount_faculty.project_read_scene(
        wa, _World(), "Bird chased cat.",
        {"spine": {
            "textbase": [{"predications": [["chase", "bird", "cat"]],
                          "sentence": "Bird chased cat."}],
            "ingests": [{"predication": ["chase", "bird", "cat"]}],
        }})
    assert result["n_events"] == 1
    receipts = list(wa.s.nodes("NativeRecountReceipt"))
    assert len(receipts) == 1
    attrs = wa.s.node(receipts[0])["attrs"]
    assert attrs["provenance"] == (
        "native_rule_readback:recount_realization")
    assert attrs["outcome_source"] == "native_rule_readback"
    assert attrs["python_outcome_selection"] is False
    audit = audit_python_cognitive_branches(".")
    bound = [item for item in audit["bound_calls"]
             if item["cluster"] == "recount_faculty.read_scene_settlement"]
    assert len(bound) == 1


def test_media_analysis_passive_and_intent_settlement_is_native():
    from domains import media_analysis
    from substrate.world_adapter import WorldAdapter

    wa = WorldAdapter(seeds=())
    created = media_analysis.annotate_passive_predication(
        wa,
        {"construction": "passive", "predications": [["fund", "_", "technology"]],
         "clause": "The technology was funded."},
        [("COP", "was"), ("PPART", "funded"), ("BY", "by")],
        ["The technology", "the oil company"],
    )
    assert created
    observation = wa.s.add_node("FramingObservation", {
        "device": "agent_deletion", "verb": "fund", "patient": "technology",
    })
    wa.inner.add_edge_unchecked(wa.agent, "has_framing_observation", observation)
    assert media_analysis.annotate_intent_signals(
        wa, "The technology was funded.")
    receipts = list(wa.s.nodes("NativeMediaAnalysisReceipt"))
    clusters = {wa.s.node(n)["attrs"].get("cluster") for n in receipts}
    assert "media_analysis.passive_settlement" in clusters
    assert "media_analysis.intent_signal_settlement" in clusters
    assert all(wa.s.node(n)["attrs"]["outcome_source"] ==
               "native_rule_readback" for n in receipts)
    audit = audit_python_cognitive_branches(".")
    for cluster in ("media_analysis.passive_settlement",
                    "media_analysis.intent_signal_settlement"):
        assert len([item for item in audit["bound_calls"]
                    if item["cluster"] == cluster]) == 1


def test_media_analysis_relational_noun_settlement_is_native():
    from domains import media_analysis
    from substrate.world_adapter import WorldAdapter

    wa = WorldAdapter(seeds=())
    created = media_analysis.annotate_relational_noun(
        wa, {"clause": "states rights"}, ["states", "rights"])
    assert created
    receipts = list(wa.s.nodes("NativeMediaAnalysisReceipt"))
    matching = [wa.s.node(n)["attrs"] for n in receipts
                if wa.s.node(n)["attrs"].get("cluster") ==
                "media_analysis.relational_noun_settlement"]
    assert len(matching) == 1
    assert matching[0]["mention_count"] == len(created)
    assert matching[0]["provenance"] == (
        "native_rule_readback:relational_noun_analysis")
    assert matching[0]["outcome_source"] == "native_rule_readback"
    assert matching[0]["python_outcome_selection"] is False
    audit = audit_python_cognitive_branches(".")
    bound = [item for item in audit["bound_calls"]
             if item["cluster"] ==
             "media_analysis.relational_noun_settlement"]
    assert len(bound) == 1


def test_recount_reasoning_settlement_receipts_native_execution(monkeypatch):
    from types import SimpleNamespace
    from domains import recount_faculty

    class FakeSub:
        def __init__(self):
            self.created = []

        def add_node(self, node_type, attrs):
            node = f"{node_type}:{len(self.created)}"
            self.created.append((node, node_type, attrs))
            return node

    class FakeNative:
        def run_rules(self):
            return 7

    sub = FakeSub()
    agent = SimpleNamespace(s=sub, inner=FakeNative())
    monkeypatch.setattr(recount_faculty, "build_recount_faculty", lambda _agent: None)
    monkeypatch.setattr(recount_faculty.cr, "read_and_comprehend",
                        lambda _agent, _text: {"ok": True})
    monkeypatch.setattr(recount_faculty, "project_read_scene",
                        lambda *_args: {"scene": "scene", "residuals": []})
    monkeypatch.setattr(recount_faculty, "world_receive_recount", lambda *_args: None)
    monkeypatch.setattr(recount_faculty, "recount_report", lambda *_args, **_kwargs: {
        "lines": [], "productions": [], "accepted": [], "n_goals": 0,
        "n_subgoals": 0, "skipped_known_to_audience": [], "connectives": [],
        "elide_leading": [], "elide_trailing": [],
    })
    monkeypatch.setattr(recount_faculty, "smooth_scene_prose", lambda lines, **_kwargs: "")

    recount_faculty.recount_what_read(agent, object(), object(), "article")
    receipts = [attrs for _node, node_type, attrs in sub.created
                if node_type == "NativeRecountReceipt" and
                attrs.get("cluster") ==
                "recount_faculty.recount_reasoning_settlement"]
    assert len(receipts) == 1
    assert receipts[0]["native_steps"] == 7
    assert receipts[0]["provenance"] == (
        "native_rule_readback:recount_reasoning")
    assert receipts[0]["outcome_source"] == "native_rule_readback"
    assert receipts[0]["python_outcome_selection"] is False


def test_recount_analysis_reasoning_settlement_receipts_native_execution(monkeypatch):
    from types import SimpleNamespace
    from domains import recount_faculty

    class FakeSub:
        def __init__(self):
            self.created = []

        def add_node(self, node_type, attrs):
            node = f"{node_type}:{len(self.created)}"
            self.created.append((node, node_type, attrs))
            return node

    class FakeNative:
        def run_rules(self):
            return 9

    sub = FakeSub()
    agent = SimpleNamespace(s=sub, inner=FakeNative())
    monkeypatch.setattr(recount_faculty, "recount_what_read",
                        lambda *_args, **_kwargs: {
                            "prose": "surface", "lines": [], "productions": [],
                            "accepted": [], "n_goals": 0, "n_subgoals": 0,
                            "residuals": [], "skipped_known_to_audience": [],
                            "comprehension": {},
                        })
    monkeypatch.setattr(recount_faculty, "project_analysis_scene",
                        lambda *_args: {"scene": "analysis-scene", "n_readings": 2})
    monkeypatch.setattr(recount_faculty, "world_receive_recount", lambda *_args: None)
    monkeypatch.setattr(recount_faculty, "recount_report", lambda *_args, **_kwargs: {
        "lines": [], "productions": [], "accepted": [], "n_goals": 0,
        "n_subgoals": 0, "skipped_known_to_audience": [],
    })
    monkeypatch.setattr(recount_faculty, "smooth_scene_prose", lambda lines, **_kwargs: "")

    recount_faculty.analyse_what_read(agent, object(), object(), "article")
    receipts = [attrs for _node, node_type, attrs in sub.created
                if node_type == "NativeRecountReceipt" and
                attrs.get("cluster") ==
                "recount_faculty.analysis_reasoning_settlement"]
    assert len(receipts) == 1
    assert receipts[0]["reading_count"] == 2
    assert receipts[0]["native_steps"] == 9
    assert receipts[0]["provenance"] == (
        "native_rule_readback:recount_analysis_reasoning")
    assert receipts[0]["outcome_source"] == "native_rule_readback"
    assert receipts[0]["python_outcome_selection"] is False


def test_recount_analysis_scene_settlement_receipts_native_execution(monkeypatch):
    from types import SimpleNamespace
    from domains import recount_faculty

    class FakeSub:
        def __init__(self):
            self.created = []

        def add_node(self, node_type, attrs):
            node = f"{node_type}:{len(self.created)}"
            self.created.append((node, node_type, attrs))
            return node

        def nodes(self, _node_type):
            return []

    class FakeNative:
        def run_rules(self):
            return 11

    sub = FakeSub()
    agent = SimpleNamespace(s=sub, inner=FakeNative())
    monkeypatch.setattr(recount_faculty.ag, "_wire_codebook_by_key",
                        lambda *_args, **_kwargs: None)
    monkeypatch.setattr(recount_faculty, "bridge_lexicon_entry",
                        lambda *_args, **_kwargs: None)

    result = recount_faculty.project_analysis_scene(agent, object(), "article")
    assert result == {"scene": "Scene:0", "n_readings": 0}
    receipts = [attrs for _node, node_type, attrs in sub.created
                if node_type == "NativeRecountReceipt" and
                attrs.get("cluster") ==
                "recount_faculty.analysis_scene_settlement"]
    assert len(receipts) == 1
    assert receipts[0]["reading_count"] == 0
    assert receipts[0]["native_steps"] == 11
    assert receipts[0]["provenance"] == (
        "native_rule_readback:recount_analysis_scene")
    assert receipts[0]["outcome_source"] == "native_rule_readback"
    assert receipts[0]["python_outcome_selection"] is False


def test_conceptualizer_candidate_monitor_settlement_is_native(monkeypatch):
    from types import SimpleNamespace
    from domains import conceptualizer

    class FakeSub:
        def __init__(self):
            self.created = []

        def add_node(self, node_type, attrs):
            node = f"{node_type}:{len(self.created)}"
            self.created.append((node, node_type, attrs))
            return node

        def nodes(self, _node_type):
            return []

    class FakeNative:
        def run_rules(self, _budget):
            return 13

        def add_edge_unchecked(self, *_args):
            return None

        def neighbours(self, _node, _edge_type):
            return []

    sub = FakeSub()
    agent = SimpleNamespace(s=sub, inner=FakeNative())
    monkeypatch.setattr(conceptualizer, "_ensure_output_candidate_commit_rule",
                        lambda _native: None)
    monkeypatch.setattr(
        "domains.self_target_monitor.score_self_target",
        lambda *_args, **_kwargs: {
            "recoverable": True, "coverage": 1.0, "missing": [],
            "recovered": ["concept"], "mode": "focused",
        })

    result = conceptualizer.scan_and_monitor(
        agent, [], candidate="A grounded sentence.",
        intended_concepts=["concept"])
    assert len(result) == 1
    receipts = [attrs for _node, node_type, attrs in sub.created
                if node_type == "NativeConceptualizerReceipt" and
                attrs.get("cluster") ==
                "conceptualizer.monitor_candidate_settlement"]
    assert len(receipts) == 1
    assert receipts[0]["native_steps"] == 13
    assert receipts[0]["provenance"] == (
        "native_rule_readback:conceptualizer_candidate_commit")
    assert receipts[0]["outcome_source"] == "native_rule_readback"
    assert receipts[0]["python_outcome_selection"] is False


def test_inference_generation_part_of_settlement_is_native(monkeypatch):
    from types import SimpleNamespace
    from domains import inference_generation

    class FakeSub:
        def __init__(self):
            self.created = []

        def has_edge(self, *_args):
            return False

        def add_edge(self, *_args):
            return None

        def add_node(self, node_type, attrs):
            node = f"{node_type}:{len(self.created)}"
            self.created.append((node, node_type, attrs))
            return node

    class FakeNative:
        def run_rules(self, _budget):
            return 17

    sub = FakeSub()
    agent = SimpleNamespace(s=sub, inner=FakeNative())
    monkeypatch.setattr(inference_generation.smr, "_entity",
                        lambda _agent, name, unit=None: f"entity:{name}")
    monkeypatch.setattr(inference_generation, "_resolve",
                        lambda _agent: (sub, agent.inner, None))

    result = inference_generation._mint_part_of(agent, "leaf", "tree")
    assert result == {"entity": "leaf", "whole": "tree"}
    receipts = [attrs for _node, node_type, attrs in sub.created
                if node_type == "NativeInferenceGenerationReceipt"]
    assert len(receipts) == 1
    assert receipts[0]["native_steps"] == 17
    assert receipts[0]["provenance"] == (
        "native_rule_readback:inference_generation")
    assert receipts[0]["outcome_source"] == "native_rule_readback"
    assert receipts[0]["python_outcome_selection"] is False


def test_reading_drive_tick_delegates_to_bound_native_cycle(monkeypatch):
    from types import SimpleNamespace
    from domains import reading_drive
    from evaluation.native_authority_audit import audit_python_cognitive_branches

    states = iter(((("language", "pending"),), (("language", "done"),),
                   (("language", "done"),)))
    calls = []
    fake = SimpleNamespace(
        cognitive_tick=lambda: calls.append(True),
    )
    monkeypatch.setattr(reading_drive, "_statuses", lambda _ad: next(states))
    reading_drive._tick_reading(fake, max_ticks=8)
    assert len(calls) == 3
    audit = audit_python_cognitive_branches(".")
    bound = [item for item in audit["bound_calls"]
             if item["cluster"] == "reading_drive.native_cognitive_tick_delegation"]
    assert len(bound) == 1
    assert bound[0]["boundary"] == "delegation_to_bound_native_cycle_only"


def test_reasoning_can_correspondence_settlement_is_native(monkeypatch):
    from types import SimpleNamespace
    from domains import reasoning_can_bridge

    class FakeSub:
        def __init__(self):
            self.created = []

        def nodes(self, _node_type):
            return []

        def add_node(self, node_type, attrs):
            node = f"{node_type}:{len(self.created)}"
            self.created.append((node, node_type, attrs))
            return node

    class FakeNative:
        def run_rules(self, _budget):
            return 19

    sub = FakeSub()
    native = FakeNative()
    agent = SimpleNamespace(s=sub, inner=native)
    monkeypatch.setattr(reasoning_can_bridge, "_resolve",
                        lambda _agent: (sub, native))
    monkeypatch.setattr(reasoning_can_bridge, "_ensure_correspondence_seed",
                        lambda _agent: None)

    reasoning_can_bridge._run_correspondence(agent)
    receipts = [attrs for _node, node_type, attrs in sub.created
                if node_type == "NativeReasoningCANBridgeReceipt"]
    assert len(receipts) == 1
    assert receipts[0]["native_steps"] == 19
    assert receipts[0]["provenance"] == (
        "native_rule_readback:reasoning_can_bridge")
    assert receipts[0]["outcome_source"] == "native_rule_readback"
    assert receipts[0]["python_outcome_selection"] is False


def test_ast_to_rule_expression_settlement_is_native():
    import ast
    from domains.ast_to_rule import Migrator

    migrator = Migrator()
    term = migrator.expr_term(ast.parse("unknown_name").body[0].value)
    assert term == {"type": "Var", "name": "unknown_name"}
    receipts = [migrator.s.node(n)["attrs"] for n in
                migrator.s.nodes("NativeASTToRuleReceipt")
                if migrator.s.node(n)["attrs"].get("cluster") ==
                "ast_to_rule.expression_settlement"]
    assert len(receipts) == 1
    assert receipts[0]["provenance"] == "native_rule_readback:ast_to_term"
    assert receipts[0]["outcome_source"] == "native_rule_readback"
    assert receipts[0]["python_outcome_selection"] is False


def test_question_driver_deliberation_receipt_is_native_and_event_scoped():
    driver = QuestionDriver()
    driver.drive(QuestionPack(text="What is beyond the wall?"))
    receipts = driver.s.nodes("NativeDeliberationReceipt")
    assert receipts
    attrs = driver.s.node(receipts[-1])["attrs"]
    assert attrs["cluster"] == "question_driver.deliberation_pump"
    assert attrs["provenance"] == "native_trace:question_driver_deliberation"
    assert attrs["outcome_source"] == "native_trace"
    assert attrs["schedule"] == "default"
    assert isinstance(attrs["rule_ids"], list)
    assert "turn" not in attrs


def test_speech_act_classification_is_native_bound_and_receipted():
    """The next communication call after question_driver is one native
    rule-readback boundary, not a Python kind decision."""
    from evaluation.native_authority_audit import audit_python_cognitive_branches
    from substrate.world_adapter import WorldAdapter
    from domains.comprehend_text import comprehend_text

    audit = audit_python_cognitive_branches(".")
    bound = [item for item in audit["bound_calls"]
             if item["cluster"] == "comprehend_text.speech_act_classification"]
    assert len(bound) == 1
    assert bound[0]["provenance"] == (
        "native_rule_readback:speech_act_classification")
    assert bound[0]["exception_rule"] == (
        "comprehend_text_speech_act_native_readback_v1")
    assert not any(item["file"] == "domains/comprehend_text.py"
                   and item["function"] == "_classify_kind_rules"
                   for item in audit["findings"])

    agent = WorldAdapter(seeds=())
    comp = comprehend_text(agent, "Why is the sky blue?")
    assert comp.kind == "question"
    receipts = agent.s.nodes("NativeSpeechActReceipt")
    assert receipts
    attrs = agent.s.node(receipts[-1])["attrs"]
    assert attrs["native_rule"] == "sak_kind_question"
    assert attrs["outcome_source"] == "native_rule_readback"
    assert attrs["python_outcome_selection"] is False


def test_conceptualizer_native_pipeline_is_bound_and_receipted():
    from evaluation.native_authority_audit import audit_python_cognitive_branches
    from substrate.world_adapter import WorldAdapter
    from domains import conceptualizer

    audit = audit_python_cognitive_branches(".")
    bound = [item for item in audit["bound_calls"]
             if item["cluster"] == "conceptualizer.native_pipeline"]
    assert len(bound) == 3
    assert all(item["function"] == "run_pipeline"
               and item["boundary"] == "native_rule_execution_only"
               and item["outcome_source"] == "native_rule_readback"
               and item["python_outcome_selection"] is False
               for item in bound)
    assert not any(item["file"] == "domains/conceptualizer.py"
                   and item["function"] == "run_pipeline"
                   for item in audit["findings"])

    agent = WorldAdapter(seeds=())
    conceptualizer.run_pipeline(agent, [], rounds=0, tick_budget=1)
    receipts = agent.s.nodes("NativeConceptualizerReceipt")
    assert receipts
    attrs = agent.s.node(receipts[-1])["attrs"]
    assert attrs["provenance"] == (
        "native_rule_readback:conceptualizer_pipeline")
    assert attrs["outcome_source"] == "native_rule_readback"
    assert attrs["python_outcome_selection"] is False


def test_scene_materialization_is_native_bound_and_receipted():
    """Scene ingestion is a native materialization boundary, not a Python
    communication/outcome decision."""
    from evaluation.native_authority_audit import audit_python_cognitive_branches
    from substrate.world_adapter import WorldAdapter
    from domains.conversation_action import attach_scene

    audit = audit_python_cognitive_branches(".")
    bound = [item for item in audit["bound_calls"]
             if item["cluster"] == "conversation_action.scene_materialization"]
    assert len(bound) == 1
    assert bound[0]["file"] == "domains/conversation_action.py"
    assert bound[0]["function"] == "attach_scene"
    assert bound[0]["call"] == "run_rules"
    assert bound[0]["provenance"] == (
        "native_rule_readback:scene_percept_materialization")
    assert bound[0]["exception_rule"] == (
        "conversation_action_scene_percept_materialization_v1")
    assert not any(item["file"] == "domains/conversation_action.py"
                   and item["function"] == "attach_scene"
                   for item in audit["findings"])

    agent = WorldAdapter(seeds=())
    scene = attach_scene(agent, [{"kind": "object", "colour": "blue"}])
    receipts = agent.s.nodes("NativeSceneMaterializationReceipt")
    assert receipts
    attrs = agent.s.node(receipts[-1])["attrs"]
    assert attrs["scene"] == scene
    assert attrs["percept_count"] == 1
    assert attrs["native_rule"] == (
        "conversation_action_scene_percept_materialization_v1")
    assert attrs["provenance"] == (
        "native_rule_readback:scene_percept_materialization")
    assert attrs["outcome_source"] == "native_rule_readback"
    assert attrs["python_outcome_selection"] is False
    assert "turn" not in attrs


def test_utterance_phrase_annotation_is_native_bound_and_receipted():
    """Phrase emission is mechanical; downstream annotation crosses one
    explicitly recorded native rule boundary."""
    from evaluation.native_authority_audit import audit_python_cognitive_branches
    from substrate.world_adapter import WorldAdapter
    from domains import actor_goals

    audit = audit_python_cognitive_branches(".")
    bound = [item for item in audit["bound_calls"]
             if item["cluster"] == "actor_goals.utterance_phrase_annotation"]
    assert len(bound) == 1
    assert bound[0]["file"] == "domains/actor_goals.py"
    assert bound[0]["function"] == "annotate_utterance_phrases"
    assert bound[0]["call"] == "run_rules"
    assert bound[0]["provenance"] == (
        "native_rule_readback:utterance_phrase_annotation")
    assert bound[0]["exception_rule"] == (
        "actor_goals_utterance_phrase_annotation_v1")
    assert not any(item["file"] == "domains/actor_goals.py"
                   and item["function"] == "annotate_utterance_phrases"
                   for item in audit["findings"])

    agent = WorldAdapter(seeds=())
    created = actor_goals.annotate_utterance_phrases(
        agent, "The system learns from experience.")
    receipts = agent.s.nodes("NativeUtterancePhraseAnnotationReceipt")
    assert created
    assert receipts
    attrs = agent.s.node(receipts[-1])["attrs"]
    assert attrs["cluster"] == "actor_goals.utterance_phrase_annotation"
    assert attrs["provenance"] == (
        "native_rule_readback:utterance_phrase_annotation")
    assert attrs["native_rule"] == (
        "actor_goals_utterance_phrase_annotation_v1")
    assert attrs["utterance_phrase_count"] == len(created)
    assert attrs["outcome_source"] == "native_rule_readback"
    assert attrs["python_outcome_selection"] is False
    assert "turn" not in attrs
