"""Architecture and preregistration gates for embodied adaptation.

Static gates always run.  The PyBullet smoke is an explicit skip when the
optional robot dependency is absent; absence is never counted as a pass.
"""
from __future__ import annotations

import ast
import importlib.util
import json
from pathlib import Path
import re
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT, ROOT / "runners" / "dsl" / "python"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

ADAPTER = ROOT / "domains" / "pybullet_robot_world.py"
RUNNER = ROOT / "scripts" / "jabberwock_embodied_adaptation.py"
SEED = ROOT / "seeds" / "embodied_adaptation.json"
SCOPE = ROOT / "docs" / "embodied_adaptation_scope.md"
PREREG = ROOT / "docs" / "embodied_adaptation_preregistration.md"
PILOT_DOC = ROOT / "docs" / "embodied_adaptation_engineering_pilot.md"
PILOT_RESULT = ROOT / "results" / "embodied_adaptation_engineering_pilot.json"
DAMAGE_DOC = ROOT / "docs" / "embodied_damage_wear_adaptation.md"
DAMAGE_RESULT = ROOT / "results" / "embodied_damage_wear_engineering_pilot.json"
DAMAGE_RUNNER = ROOT / "scripts" / "jabberwock_damage_wear_adaptation.py"
DAMAGE_NAV_V1 = ROOT / "results" / "embodied_damage_navigation_v1.json"
DAMAGE_NAV_V2 = ROOT / "results" / "embodied_damage_navigation_v2.json"
DAMAGE_NAV_V3 = ROOT / "results" / "embodied_damage_navigation_v3.json"
DAMAGE_NAV_V4 = ROOT / "results" / "embodied_damage_navigation_v4.json"
DAMAGE_NAV_PROTOCOL_V2 = (
    ROOT / "protocols" / "embodied_damage_navigation_v2.json"
)
DAMAGE_NAV_PROTOCOL_V3 = (
    ROOT / "protocols" / "embodied_damage_navigation_v3.json"
)
DAMAGE_NAV_PROTOCOL_V4 = (
    ROOT / "protocols" / "embodied_damage_navigation_v4.json"
)
NONHOLONOMIC_PROTOCOL_V1 = (
    ROOT / "protocols" / "embodied_nonholonomic_control_v1.json"
)
NONHOLONOMIC_PROTOCOL_V2 = (
    ROOT / "protocols" / "embodied_nonholonomic_control_v2.json"
)
NONHOLONOMIC_RESULT_V2 = (
    ROOT / "results" / "embodied_nonholonomic_control_v2.json"
)

BODIES = ("r2d2", "husky", "racecar")


def _prose(path: Path) -> str:
    return re.sub(r"\s+", " ", path.read_text(encoding="utf-8").lower())


def _functions(path: Path) -> dict[str, ast.FunctionDef | ast.AsyncFunctionDef]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {
        node.name: node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _function_source(path: Path, name: str) -> str:
    source = path.read_text(encoding="utf-8")
    node = _functions(path)[name]
    return ast.get_source_segment(source, node) or ""


def _rule(seed: dict, name: str) -> dict:
    return next(rule for rule in seed["rules"] if rule["name"] == name)


def test_scope_and_preregistration_name_the_exact_narrow_claim():
    scope = _prose(SCOPE)
    prereg = _prose(PREREG)

    for body in BODIES:
        assert body in scope
        assert f"`{body}`" in prereg
    for required in (
        "open-plane",
        "from scratch",
        "opaque actuator",
        "python is a physics peripheral",
        "obstacle navigation",
    ):
        assert required in scope
    assert "82001" in prereg
    assert "82002" not in prereg
    assert "exact pseudoreplicate" in prereg
    assert "never counted as additional evidence" in prereg
    for goal in ("(3, 0, 0)", "(0, 3, 0)", "(3, 3, 0)"):
        assert goal in prereg
    for metric in (
        "token coverage",
        "prediction",
        "normalized progress",
        "path efficiency",
        "raw-contact decision rate",
    ):
        assert metric in prereg
    assert "not run" in prereg
    assert "collision count is **not measured**" in prereg
    assert "failure of one morphology refuses the cross-morphology claim" in prereg


def test_preregistration_has_controls_nonvacuity_and_numeric_refusal_gates():
    text = _prose(PREREG)
    for control in (
        "no-learning control",
        "shuffled-model control",
        "cyclic permutation",
    ):
        assert control in text
    for nonvacuity in (
        "graph provenance is `1.0`",
        "token coverage `1.0`",
        "mutates all nine model counts",
        "changes zero `actionmodel`",
    ):
        assert nonvacuity in text
    for threshold in (
        "at least `10%`",
        "by at least `0.05`",
        "greater than `1e-4`",
    ):
        assert threshold in text
    assert "bare failure count is prohibited" in text


def test_seed_contains_the_graph_decision_learning_and_assessment_rules():
    seed = json.loads(SEED.read_text(encoding="utf-8"))
    assert seed["id"] == "embodied_adaptation"
    names = {rule["name"] for rule in seed["rules"]}
    assert {
        "ea_measure_goal_state",
        "ea_choose_babble_action",
        "ea_choose_model_action",
        "ea_choose_change_recalibration",
        "ea_choose_adaptation_probe",
        "ea_choose_no_learning_control",
        "ea_choose_random_control",
        "ea_choose_shuffled_model_control",
        "ea_open_motor_trial",
        "ea_learn_forward_model",
        "ea_close_no_learning_trial",
    } <= names

    serialized = json.dumps(seed).lower()
    for node_type in (
        "embodiedpolicy",
        "embodiedepisode",
        "actionmodel",
        "opa queactuator".replace(" ", ""),
        "motortrial",
        "transitionobservation",
    ):
        assert node_type in serialized
    assert "argmin" in serialized
    assert "prediction_error" in serialized
    assert "experience_count" in serialized
    for adaptive_field in (
        "error_ema",
        "volatility_ema",
        "surprise_trace",
        "fast_adaptation_rate",
        "slow_adaptation_rate",
        "plasticity_stop_epoch",
        "context_gain_forward",
        "context_gain_lateral",
        "context_gain_turn",
        "history_context_forward",
        "context_learning_rate",
        "candidate_active",
        "candidate_attempted",
        "candidate_error_sum",
        "candidate_promotion_count",
        "candidate_change_validated",
    ):
        assert adaptive_field in serialized


def test_checkpoint_decisions_are_receipt_backed_and_materialized_before_rollback():
    seed = json.loads(SEED.read_text(encoding="utf-8"))
    learning = _rule(seed, "ea_learn_forward_model")
    effects = learning["effects"]
    keys = [
        effect[2]
        for effect in effects
        if effect[0] == "set_attr"
    ]

    assert keys.index("candidate_promoted") < keys.index("mean_forward")
    assert keys.index("candidate_change_validated") < keys.index(
        "candidate_active"
    )
    assert keys.index("proposed_candidate_mean_forward") < keys.index(
        "mean_forward"
    )
    serialized = json.dumps(learning)
    assert "candidate_predicted_forward" in serialized
    assert "candidate_consolidated_error_sum" in serialized


def test_heading_escape_terminates_from_learned_sensorimotor_evidence():
    seed = json.loads(SEED.read_text(encoding="utf-8"))
    policy = next(
        node for node in seed["nodes"] if node["type"] == "EmbodiedPolicy"
    )["attrs"]
    chooser = _rule(seed, "ea_choose_model_action")
    trial = _rule(seed, "ea_open_motor_trial")
    learner = _rule(seed, "ea_learn_forward_model")
    observer = _rule(seed, "ea_close_no_learning_trial")
    measure = _rule(seed, "ea_measure_goal_state")
    serialized = json.dumps(chooser).lower()
    whole_seed = json.dumps(seed)

    assert seed["version"] == "1.7.0"
    assert policy["heading_escape_enabled"] == 1.0
    assert '"value": 24.0' not in whole_seed
    for removed in (
        "heading_alignment_weight",
        "minimum_progress_fraction",
        "max_heading_escape_actions",
        "heading_escape_count",
    ):
        assert removed not in policy
        assert removed not in whole_seed
    for field in (
        "last_action_goal_progress",
        "last_action_decision_kind",
        "goal_heading_error",
        "heading_escape_viable",
        "mean_forward",
        "mean_lateral",
        "mean_turn",
        "heading_escape",
        "two_step_distance",
    ):
        assert field in serialized
    assert '"type": "Argmin"' in json.dumps(chooser)
    assert '"type": "Argmax"' in json.dumps(chooser)
    assert json.dumps(chooser).count('"type": "Div"') >= 2
    assert '"type": "Let"' in json.dumps(chooser)
    assert "goal_heading_error_before" in json.dumps(trial)
    for receipt_rule in (learner, observer):
        receipt_json = json.dumps(receipt_rule)
        assert "last_heading_improvement" in receipt_json
        assert "heading_escape_viable" in receipt_json
        assert "goal_heading_error_before" in receipt_json
    assert "previous_goal_heading_error" in json.dumps(measure)
    assert "racecar" not in serialized


def test_nonholonomic_protocol_was_frozen_before_execution():
    protocol = json.loads(NONHOLONOMIC_PROTOCOL_V1.read_text(encoding="utf-8"))

    assert protocol["status"] == "frozen_before_execution"
    assert protocol["mechanism_version"] == "embodied_adaptation/1.5.0"
    assert protocol["primary_morphology"] == "racecar"
    assert len(protocol["cases"]) == 6
    assert len({case["seed"] for case in protocol["cases"]}) == 6
    assert all(case["seed"] >= 85301 for case in protocol["cases"])
    assert protocol["success_gates"]["racecar_wins_required"] == 4
    assert (
        protocol["success_gates"][
            "racecar_median_paired_advantage_minimum"
        ]
        == 0.05
    )


def test_nonholonomic_v2_uses_new_cases_and_fixed_mechanism():
    v1 = json.loads(NONHOLONOMIC_PROTOCOL_V1.read_text(encoding="utf-8"))
    v2 = json.loads(NONHOLONOMIC_PROTOCOL_V2.read_text(encoding="utf-8"))

    assert v2["status"] == "frozen_before_execution"
    assert v2["mechanism_version"] == "embodied_adaptation/1.5.1"
    assert v2["success_gates"] == v1["success_gates"]
    assert {
        case["seed"] for case in v1["cases"]
    }.isdisjoint(case["seed"] for case in v2["cases"])
    assert all(case["seed"] >= 86301 for case in v2["cases"])


def test_nonholonomic_v2_preserves_the_failed_strong_claim():
    import hashlib

    payload = json.loads(NONHOLONOMIC_RESULT_V2.read_text(encoding="utf-8"))
    protocol_bytes = NONHOLONOMIC_PROTOCOL_V2.read_bytes()
    evaluation = payload["evaluation"]
    racecar = evaluation["by_morphology"]["racecar"]

    assert payload["protocol_sha256"] == hashlib.sha256(
        protocol_bytes
    ).hexdigest()
    assert evaluation["primary_claim_passed"] is False
    assert racecar["enhanced_wins"] == 3
    assert racecar["comparisons"] == 6
    assert racecar["enhanced_median_progress"] > 0.6
    assert racecar["median_paired_advantage"] < 0.05
    assert (
        evaluation["gate_results"]["racecar_wins_required"] is False
    )
    assert (
        evaluation["gate_results"][
            "racecar_median_paired_advantage_minimum"
        ]
        is False
    )
    assert all(
        passed
        for gate, passed in evaluation["gate_results"].items()
        if gate not in {
            "racecar_wins_required",
            "racecar_median_paired_advantage_minimum",
        }
    )


def test_corrected_damage_navigation_receipt_latches_recalibration_atomically():
    seed = json.loads(SEED.read_text(encoding="utf-8"))
    learning = _rule(seed, "ea_learn_forward_model")
    effects = learning["effects"]
    keys = [
        effect[2]
        for effect in effects
        if effect[0] == "set_attr"
    ]

    assert "opened_recalibration" in json.dumps(learning)
    assert keys.index("opened_recalibration") < keys.index(
        "recalibration_remaining"
    )
    assert keys.index("opened_recalibration") < keys.index(
        "recalibration_cycles"
    )


def test_damage_navigation_results_preserve_failures_and_protocol_identity():
    import hashlib

    v1 = json.loads(DAMAGE_NAV_V1.read_text(encoding="utf-8"))
    v2 = json.loads(DAMAGE_NAV_V2.read_text(encoding="utf-8"))
    protocol_bytes = DAMAGE_NAV_PROTOCOL_V2.read_bytes()

    assert v1["evaluation"]["primary_claim_passed"] is False
    assert v2["evaluation"]["primary_claim_passed"] is False
    assert v2["protocol_sha256"] == hashlib.sha256(protocol_bytes).hexdigest()
    assert v2["evaluation"]["adaptive_wins"] == 10
    assert v2["evaluation"]["comparisons"] == 18
    assert (
        v2["evaluation"]["pooled_median_paired_advantage"]
        < 0.05
    )
    assert all(
        v2["evaluation"]["bounded_recalibration_audit"].values()
    )


def test_contextual_retest_fixes_body_sign_without_hiding_primary_failure():
    import hashlib

    v2 = json.loads(DAMAGE_NAV_V2.read_text(encoding="utf-8"))
    v3 = json.loads(DAMAGE_NAV_V3.read_text(encoding="utf-8"))
    protocol_bytes = DAMAGE_NAV_PROTOCOL_V3.read_bytes()
    evaluation = v3["evaluation"]

    assert v3["protocol_sha256"] == hashlib.sha256(protocol_bytes).hexdigest()
    assert evaluation["primary_claim_passed"] is False
    assert evaluation["adaptive_wins"] == 12
    assert evaluation["comparisons"] == 18
    assert evaluation["gate_results"][
        "median_paired_advantage_positive_in_every_morphology"
    ] is True
    assert evaluation["by_morphology"]["r2d2"][
        "median_paired_advantage"
    ] > 0.0
    assert v2["evaluation"]["by_morphology"]["r2d2"][
        "median_paired_advantage"
    ] < 0.0
    assert evaluation["gate_results"][
        "pooled_median_paired_advantage_minimum"
    ] is False
    assert all(evaluation["bounded_recalibration_audit"].values())
    assert all(
        row["context_models_nonzero"] == 9
        for row in v3["runs"]
        if row["arm"] != "healthy_reference"
    )


def test_checkpointed_retest_passes_all_frozen_gates_with_valid_rollbacks():
    import hashlib

    payload = json.loads(DAMAGE_NAV_V4.read_text(encoding="utf-8"))
    protocol_bytes = DAMAGE_NAV_PROTOCOL_V4.read_bytes()
    evaluation = payload["evaluation"]

    assert payload["protocol_sha256"] == hashlib.sha256(
        protocol_bytes
    ).hexdigest()
    assert evaluation["primary_claim_passed"] is True
    assert evaluation["adaptive_wins"] == 12
    assert evaluation["comparisons"] == 18
    assert evaluation["pooled_median_paired_advantage"] >= 0.05
    assert all(evaluation["gate_results"].values())
    assert all(evaluation["bounded_recalibration_audit"].values())
    assert evaluation["candidate_model_audit"] == {
        "hypotheses_opened": 124.0,
        "promotions": 18,
        "rollbacks": 18,
        "changed_models_validated": 64.0,
        "all_promotion_receipts_valid": True,
    }
    assert all(
        row["candidate_promotion_receipts_valid"]
        for row in payload["runs"]
        if row["arm"] == "adaptive_damage_navigation"
    )
    assert all(
        row["median_paired_advantage"] > 0.0
        for row in evaluation["by_morphology"].values()
    )


def test_learning_updates_models_but_control_cannot():
    seed = json.loads(SEED.read_text(encoding="utf-8"))
    learning = json.dumps(_rule(seed, "ea_learn_forward_model"))
    control = json.dumps(_rule(seed, "ea_close_no_learning_trial"))

    for learned_attr in (
        "experience_count",
        "mean_forward",
        "mean_lateral",
        "mean_turn",
        "contact_ema",
        "effort_ema",
    ):
        assert learned_attr in learning
        assert learned_attr not in control
    assert "no_learning_control" in control


def test_graph_seed_has_no_body_name_or_body_specific_action_table():
    seed_text = SEED.read_text(encoding="utf-8").lower()
    for body in BODIES:
        assert body not in seed_text
    for token in ("actuator_000", "actuator_001", "actuator_008"):
        assert token not in seed_text
    for directional_token in (
        '"forward"',
        '"backward"',
        '"turn_left"',
        '"turn_right"',
        '"steer"',
        '"throttle"',
    ):
        assert directional_token not in seed_text


def test_python_physics_boundary_has_no_policy_or_learning_surface():
    source = ADAPTER.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_roots = {
        alias.name.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported_roots.update(
        (node.module or "").split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    )
    assert imported_roots.isdisjoint({"substrate", "substrate_rs"})

    public = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not node.name.startswith("_")
    }
    assert public == {
        "actuator_options", "apply", "close", "observe", "reset", "set_goal", "step",
        "step_program",
    }
    assert not {
        "choose", "decide", "learn", "policy", "plan", "predict",
        "reward", "score", "navigate",
    } & public


def test_operational_python_never_branches_on_body_name():
    for function in ("actuator_options", "apply", "step", "observe", "_write_actuators"):
        body = _function_source(ADAPTER, function).lower()
        for morphology in BODIES:
            assert morphology not in body, (function, morphology)

    # Body-specific joint wiring is admitted anatomy, isolated in immutable
    # data.  Operational code may branch on the generic mechanism schema only.
    write_body = _function_source(ADAPTER, "_write_actuators")
    assert "hardware.mechanism" in write_body
    assert "selected_token" not in write_body
    assert "goal" not in write_body


def test_runner_creates_fresh_graph_inside_each_episode_and_only_enacts_graph_token():
    source = RUNNER.read_text(encoding="utf-8")
    run_source = _function_source(RUNNER, "run_episode")
    tree = ast.parse(source)

    names = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert not {
        "choose_action", "learn_model", "predict_action", "plan_path",
        "score_action", "reward_action",
    } & names
    assert 'WorldAdapter(seeds=("embodied_adaptation",))' in run_source
    assert "world.step(trial_token)" in run_source
    assert 'episode_attrs.get("selected_token")' in run_source
    assert "graph did not issue an action" in run_source
    assert "does not match selected" in run_source
    assert 'next_observation.get("last_actuator_token") == trial_token' in run_source
    assert 'agent.inner.set_attr(policy, "control_seed", float(seed))' in run_source

    for morphology in BODIES:
        assert morphology not in run_source.lower()
    assert "random.choice" not in source
    assert "numpy" not in source
    assert "mechanical_condition" not in _function_source(RUNNER, "_write_state")


def test_runner_result_contract_exposes_freshness_and_graph_provenance():
    source = _function_source(RUNNER, "run_episode")
    for field in (
        '"fresh_substrate": True',
        '"policy_owner": "rust_graph"',
        '"selected_token": token',
        '"decision_kind"',
        '"trial_status"',
        '"models": _model_rows',
    ):
        assert field in source


def test_runner_trace_contains_reproducible_transition_provenance():
    source = _function_source(RUNNER, "run_episode")
    for field in (
        '"trial_id":',
        '"outcome_id":',
        '"model_id":',
        '"trial_token":',
        '"receipt_verified":',
        '"pre_base_position":',
        '"post_base_position":',
        '"predicted_forward":',
        '"observed_forward":',
        '"model_experience_count_before":',
        '"model_experience_count_after":',
        '"goal_distance_before":',
        '"goal_distance_after":',
    ):
        assert field in source


def test_engineering_pilot_is_complete_nonvacuous_and_labelled_nonconfirmatory():
    pilot_doc = _prose(PILOT_DOC)
    assert "engineering pilot, not the confirmatory experiment" in pilot_doc
    assert "must not be presented as an untouched preregistered result" in pilot_doc

    payload = json.loads(PILOT_RESULT.read_text(encoding="utf-8"))
    assert payload["failures"] == []
    rows = payload["results"]
    modes = {
        "learning",
        "no_learning_control",
        "random_control",
        "shuffled_model_control",
    }
    assert {
        (row["morphology"], row["mode"])
        for row in rows
    } == {
        (morphology, mode)
        for morphology in BODIES
        for mode in modes
    }
    for row in rows:
        assert row["seed"] == 0
        assert row["steps"] == 120
        assert row["goal_position"] == [2.0, 0.0, 0.0]
        assert row["fresh_substrate"] is True
        assert row["policy_owner"] == "rust_graph"
        assert row["decision_count"] == 120.0
        assert len(row["action_alphabet"]) == 9
        assert len(row["trace"]) == 120
        assert all(
            transition["selected_token"] in row["action_alphabet"]
            for transition in row["trace"]
        )
        assert all(
            transition["selected_token"] == transition["trial_token"]
            and transition["receipt_verified"] == 1.0
            for transition in row["trace"]
        )
        assert len({transition["trial_id"] for transition in row["trace"]}) == 120
        assert len({transition["outcome_id"] for transition in row["trace"]}) == 120

        counts = [float(model["experience_count"]) for model in row["models"]]
        if row["mode"] == "learning":
            assert all(count >= 2.0 for count in counts)
            assert row["goal_reached_graph_assessment"] == 1.0
        elif row["mode"] == "shuffled_model_control":
            assert counts == [2.0] * 9
            assert row["goal_reached_graph_assessment"] == 0.0
        else:
            assert counts == [0.0] * 9
            assert row["goal_reached_graph_assessment"] == 0.0


def test_cli_failure_contract_is_structured_and_returns_failure():
    source = _function_source(RUNNER, "main")
    for field in (
        '"failures": failures',
        '"morphology": morphology',
        '"mode": mode',
        '"seed": args.seed',
        '"goal": list(args.goal)',
        '"steps": args.steps',
        '"babble_samples": args.babble_samples',
        '"epoch": getattr(exc, "epoch", None)',
        '"token": getattr(exc, "token", None)',
        '"error_type": type(exc).__name__',
        '"error": str(exc)',
        "return 1 if failures else 0",
    ):
        assert field in source


def test_damage_wear_pilot_is_matched_nonvacuous_and_honestly_scoped():
    prose = _prose(DAMAGE_DOC)
    for phrase in (
        "engineering pilot, not a confirmatory result",
        "same opaque action sequence",
        "same trajectory until the hidden mechanical change",
        "does not yet establish that active closed-loop navigation always benefits",
        "identifies changed consequences, not the semantic cause",
    ):
        assert phrase in prose

    payload = json.loads(DAMAGE_RESULT.read_text(encoding="utf-8"))
    assert payload["status"] == "engineering_pilot_not_confirmatory"
    assert payload["failures"] == []
    assert len(payload["results"]) == 12
    assert len(payload["summaries"]) == 6
    assert {
        (row["condition_name"], row["morphology"], row["mode"])
        for row in payload["results"]
    } == {
        (condition, morphology, mode)
        for condition in ("damage", "wear")
        for morphology in BODIES
        for mode in ("adaptive_probe", "frozen_probe_control")
    }
    for summary in payload["summaries"]:
        assert summary["same_graph_action_schedule"] is True
        assert summary["same_pre_onset_trajectory"] is True
        assert summary["adaptive_post_onset_surprises"] > 0.0
        assert summary["frozen_post_onset_surprises"] == 0.0
        assert summary["adaptive_fractional_error_recovery"] > 0.0
        assert summary["late_error_advantage"] > 0.0
    for row in payload["results"]:
        assert all(
            transition["selected_token"] == transition["trial_token"]
            and transition["receipt_verified"] == 1.0
            for transition in row["trace"]
        )
        counts = {float(model["experience_count"]) for model in row["models"]}
        if row["mode"] == "adaptive_probe":
            assert counts == {12.0}
            assert all(
                transition["trial_status"] == "learned"
                for transition in row["trace"]
            )
        else:
            assert counts == {5.0}
            assert all(
                transition["trial_status"] == "observed_no_learning"
                for transition in row["trace"][payload["onset_action"]:]
            )

    damage_source = DAMAGE_RUNNER.read_text(encoding="utf-8")
    assert "run_episode(" in damage_source
    assert "choose" not in {
        node.name
        for node in ast.walk(ast.parse(damage_source))
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def test_optional_random_control_seed_changes_graph_selected_schedule():
    if importlib.util.find_spec("pybullet") is None:
        pytest.skip("PyBullet absent: install requirements-robot.txt; not counted as pass")

    from scripts import jabberwock_embodied_adaptation as run

    first = run.run_episode(
        "r2d2",
        "random_control",
        steps=9,
        goal=(2.0, 0.0, 0.0),
        seed=82001,
        babble_samples=1,
    )
    second = run.run_episode(
        "r2d2",
        "random_control",
        steps=9,
        goal=(2.0, 0.0, 0.0),
        seed=82002,
        babble_samples=1,
    )
    first_tokens = [row["selected_token"] for row in first["trace"]]
    second_tokens = [row["selected_token"] for row in second["trace"]]
    assert first_tokens != second_tokens


def test_optional_damage_probe_adapts_under_identical_graph_actions():
    if importlib.util.find_spec("pybullet") is None:
        pytest.skip("PyBullet absent: install requirements-robot.txt; not counted as pass")

    from domains.pybullet_robot_world import MechanicalCondition
    from scripts import jabberwock_embodied_adaptation as run

    condition = MechanicalCondition(
        onset_action=27,
        abrupt_retention=(0.0, 1.0),
    )
    adaptive = run.run_episode(
        "r2d2",
        "adaptive_probe",
        steps=72,
        babble_samples=1,
        mechanical_condition=condition,
    )
    frozen = run.run_episode(
        "r2d2",
        "frozen_probe_control",
        steps=72,
        babble_samples=1,
        mechanical_condition=condition,
    )
    assert [
        row["selected_token"] for row in adaptive["trace"]
    ] == [
        row["selected_token"] for row in frozen["trace"]
    ]
    assert (
        adaptive["trace"][26]["post_base_position"]
        == frozen["trace"][26]["post_base_position"]
    )
    adaptive_late = sum(
        float(row["prediction_error"]) for row in adaptive["trace"][-9:]
    ) / 9.0
    frozen_late = sum(
        float(row["prediction_error"]) for row in frozen["trace"][-9:]
    ) / 9.0
    assert adaptive_late < frozen_late
    assert sum(float(row["surprise"]) for row in adaptive["trace"][27:]) > 0.0
    assert sum(float(row["surprise"]) for row in frozen["trace"][27:]) == 0.0


@pytest.mark.parametrize("morphology", BODIES)
def test_optional_smoke_learns_every_opaque_token_from_a_fresh_graph(morphology):
    if importlib.util.find_spec("pybullet") is None:
        pytest.skip("PyBullet absent: install requirements-robot.txt; not counted as pass")

    from scripts import jabberwock_embodied_adaptation as run

    assert Path(run.__file__).resolve().is_relative_to(ROOT)
    result = run.run_episode(
        morphology,
        "learning",
        steps=9,
        goal=(3.0, 0.0, 0.0),
        seed=82001,
        babble_samples=1,
    )
    assert result["fresh_substrate"] is True
    assert result["policy_owner"] == "rust_graph"
    assert len(result["action_alphabet"]) == 9
    assert len(result["trace"]) == 9
    assert {row["selected_token"] for row in result["trace"]} == set(
        result["action_alphabet"]
    )
    assert all(row["decision_kind"] == "motor_babble" for row in result["trace"])
    assert all(row["trial_status"] == "learned" for row in result["trace"])
    assert all(float(model["experience_count"]) == 1.0 for model in result["models"])
    assert any(
        abs(float(model[key])) > 1.0e-8
        for model in result["models"]
        for key in ("mean_forward", "mean_lateral", "mean_turn")
    )


def test_optional_smoke_no_learning_control_leaves_models_pristine():
    if importlib.util.find_spec("pybullet") is None:
        pytest.skip("PyBullet absent: install requirements-robot.txt; not counted as pass")

    from scripts import jabberwock_embodied_adaptation as run

    result = run.run_episode(
        "r2d2",
        "no_learning_control",
        steps=9,
        goal=(3.0, 0.0, 0.0),
        seed=82001,
        babble_samples=1,
    )
    assert len(result["trace"]) == 9
    assert all(
        row["decision_kind"] == "no_learning_control"
        for row in result["trace"]
    )
    assert all(
        row["trial_status"] == "observed_no_learning"
        for row in result["trace"]
    )
    for model in result["models"]:
        assert float(model["experience_count"]) == 0.0
        for key in (
            "mean_forward", "mean_lateral", "mean_turn",
            "contact_ema", "effort_ema",
        ):
            assert float(model[key]) == 0.0


@pytest.mark.parametrize(
    ("mode", "expected_kind", "steps"),
    (
        ("random_control", "random_control", 9),
        ("shuffled_model_control", "shuffled_model_control", 10),
    ),
)
def test_optional_smoke_additional_controls_are_graph_selected(
    mode, expected_kind, steps
):
    if importlib.util.find_spec("pybullet") is None:
        pytest.skip("PyBullet absent: install requirements-robot.txt; not counted as pass")

    from scripts import jabberwock_embodied_adaptation as run

    result = run.run_episode(
        "r2d2",
        mode,
        steps=steps,
        goal=(2.0, 0.0, 0.0),
        seed=82001,
        babble_samples=1,
    )
    assert result["fresh_substrate"] is True
    assert result["policy_owner"] == "rust_graph"
    assert all(
        row["selected_token"] in result["action_alphabet"]
        for row in result["trace"]
    )
    if mode == "random_control":
        assert all(row["decision_kind"] == expected_kind for row in result["trace"])
        assert all(float(model["experience_count"]) == 0.0 for model in result["models"])
    else:
        # Shuffled control first learns one sample per token, then enacts one
        # cyclically mis-associated model choice.
        assert all(
            row["decision_kind"] == "motor_babble"
            for row in result["trace"][:9]
        )
        assert result["trace"][-1]["decision_kind"] == expected_kind
        assert all(float(model["experience_count"]) == 1.0 for model in result["models"])
