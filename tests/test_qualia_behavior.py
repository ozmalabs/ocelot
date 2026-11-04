"""P17 native consumer and significance acceptance tests."""
import json
from pathlib import Path

from substrate_rs import _native


ROOT = Path(__file__).resolve().parents[1]
SEEDS = ("default_mode_core", "thinking_budget", "qualia_space", "cognition_signature",
         "experience_signature", "qualia_acquisition", "qualia_behavior",
         "experiential_significance", "qualia_revision")


def _boot(*, budget=100.0):
    s = _native.Substrate()
    ag = s.add_node("Agent", {})
    for name in SEEDS:
        result = s.load_seed_manifest(json.loads((ROOT / "seeds" / f"{name}.json").read_text()), ag)
        assert result["rules_skipped"] == [], (name, result)
    mode = s.nodes("NetworkModeState")[0]
    s.set_attr(mode, "epoch", 10.0)
    b = s.nodes("ThinkingBudget")[0]
    for key, value in {"enabled": 1.0, "remaining": budget, "capacity": budget,
                       "capacity_ceiling": budget, "refill_per_epoch": 0.0,
                       "last_refill_epoch": 10.0}.items():
        s.set_attr(b, key, value)
    s.set_attr(s.nodes("QualiaAcquisitionPolicy")[0], "enabled", 1.0)
    s.set_attr(s.nodes("QualiaBehaviorPolicy")[0], "enabled", 1.0)
    s.set_attr(s.nodes("ExperientialSignificancePolicy")[0], "enabled", 1.0)
    s.set_attr(s.nodes("QualiaRevisionPolicy")[0], "enabled", 1.0)
    return s, ag


def _tick(s, rounds=50):
    for _ in range(rounds):
        if s.run_rules(5000) == 0:
            return
    raise AssertionError("qualia behavior rules failed to reach a fixpoint")


def _axis(s, ag, *, owner="owner-a", feature_key="contact-pattern", value="rough",
          action="repair", consequence="restored", context="learned-context"):
    dim_name = f"phenomenal:acquired:{owner}:{feature_key}"
    candidate = s.add_node("QualiaAxisCandidate", {
        "candidate_key": f"{owner}:{feature_key}", "dimension_id": dim_name,
        "owner_id": owner, "feature_key": feature_key, "feature_family": "tool_contact",
        "value_kind": "symbol", "model_epoch": 2, "frame_epoch": 5, "status": "validated"})
    dim = s.add_node("QualiaDimension", {
        "name": dim_name, "owner_id": owner, "family": "phenomenal",
        "feature_key": feature_key, "feature_family": "tool_contact", "acquired": 1.0,
        "acquisition_status": "standing", "source_epoch": 3, "model_epoch": 2,
        "frame_epoch": 5})
    witness = s.add_node("QualiaAcquisitionWitness", {
        "witness_id": f"{owner}:w1", "owner_id": owner, "episode_id": "learned-episode",
        "event_id": "learned-event", "context_id": context, "feature_key": feature_key,
        "feature_family": "tool_contact", "feature_value": value, "value_kind": "symbol",
        "action_id": action, "consequence_kind": "goal", "consequence_value": consequence,
        "source_epoch": 3, "model_epoch": 2, "frame_epoch": 5, "status": "observed"})
    s.add_edge(ag, "has_qualia_axis_candidate", candidate)
    s.add_edge(candidate, "has_acquisition_witness", witness)
    s.add_edge(ag, "has_qualia_dimension", dim)
    s.add_edge(ag, "has_qualia_acquisition_witness", witness)
    return candidate, dim, witness


def _fresh(s, ag, i, value="rough", *, owner="owner-a", feature_key="contact-pattern",
           source_epoch=3, model_epoch=2, frame_epoch=5, family="tool_contact", outcome=None,
           context=None, goal_effect=1.0):
    episode_id, event_id, feature_id = f"fresh-ep-{i}", f"fresh-ev-{i}", f"fresh-f-{i}"
    ep = s.add_node("ExperienceEpisode", {"owner_id": owner, "episode_id": episode_id,
        "context_id": context or f"fresh-context-{i}", "status": "observed"})
    ev = s.add_node("ExperienceEvent", {"owner_id": owner, "episode_id": episode_id,
        "event_id": event_id, "action_id": f"observed-action-{i}", "status": "observed",
        "event_role": "fresh_task", "world_epoch": 0,
        "source_epoch": source_epoch, "model_epoch": model_epoch, "frame_epoch": frame_epoch,
        "frame_id": f"frame-{i}"})
    feature = s.add_node("ExperienceFeatureObservation", {"owner_id": owner,
        "episode_id": episode_id, "event_id": event_id, "feature_id": feature_id,
        "feature_key": feature_key, "feature_family": family, "feature_value": value,
        "value_kind": "symbol", "grain": 0.0, "is_missing": False,
        "source_epoch": source_epoch, "model_epoch": model_epoch, "frame_epoch": frame_epoch,
        "status": "observed"})
    s.add_edge(ag, "has_experience_episode", ep)
    s.add_edge(ep, "has_experience_event", ev)
    s.add_edge(ev, "has_episode_feature", feature)
    if "fresh_task" == s.node(ev)["attrs"].get("event_role"):
        legal = ("repair", "continue") if family == "tool_contact" else (
            "repair-request", "normal-response")
        context_node = s.add_node("QualiaActionContext", {
            "owner_id": owner, "event_id": event_id, "source_epoch": source_epoch,
            "world_id": f"test-world:{i}", "world_epoch": 0,
            "legal_actions": list(legal), "status": "active"})
        s.add_edge(ag, "has_qualia_action_context", context_node)
    if outcome is not None:
        receipt = s.add_node("ExperienceOutcomeReceipt", {"owner_id": owner,
            "episode_id": episode_id, "event_id": event_id, "feature_id": feature_id,
            "receipt_id": f"receipt-{i}", "source_epoch": source_epoch,
            "model_epoch": model_epoch, "frame_epoch": frame_epoch,
            "status": "observed", "evidence_status": "observed",
            "consequence_kind": "goal", "consequence_value": outcome,
            "goal_effect": goal_effect})
        s.add_edge(feature, "has_outcome_receipt", receipt)
        return ep, ev, feature, receipt
    return ep, ev, feature, None


def test_acquired_axis_changes_new_prediction_and_action():
    s, ag = _boot()
    _axis(s, ag)
    _fresh(s, ag, 1)
    _tick(s)
    predictions = s.nodes("QualiaBehaviorPrediction")
    assert len(predictions) == 1
    pred = s.node(predictions[0])["attrs"]
    assert pred["predicted_consequence"] == "restored"
    assert pred["proposed_action_id"] == "repair"
    assert pred["status"] == "proposed"
    assert len(s.neighbours(predictions[0], "uses_qualia_dimension")) == 1
    assert len(s.neighbours(predictions[0], "uses_acquisition_witness")) == 1
    auth = s.nodes("QualiaActionAuthorization")
    assert len(auth) == 1
    assert s.node(auth[0])["attrs"]["action_id"] == "repair"
    assert s.node(auth[0])["attrs"]["status"] == "authorized"


def test_axis_knockout_blocks_supported_action():
    s, ag = _boot()
    _, dim, _ = _axis(s, ag)
    s.set_attr(dim, "acquisition_status", "contested")
    _fresh(s, ag, 1)
    _tick(s)
    assert not s.nodes("QualiaBehaviorPrediction")


def test_wrong_owner_axis_is_hidden():
    s, ag = _boot()
    _axis(s, ag, owner="owner-a")
    _fresh(s, ag, 1, owner="owner-b")
    _tick(s)
    assert not s.nodes("QualiaBehaviorPrediction")


def test_unknown_feature_does_not_become_false_zero_or_action():
    s, ag = _boot()
    _axis(s, ag, value="rough")
    _fresh(s, ag, 1, value="unseen")
    _tick(s)
    assert not s.nodes("QualiaBehaviorPrediction")


def test_stale_source_epoch_blocks_prediction():
    s, ag = _boot()
    _axis(s, ag)
    _fresh(s, ag, 1)
    event = s.nodes("ExperienceEvent")[0]
    s.set_attr(event, "source_epoch", 4)
    _tick(s)
    assert not s.nodes("QualiaBehaviorPrediction")


def test_shared_budget_denial_abstains_before_action_proposal():
    s, ag = _boot(budget=0.0)
    _axis(s, ag)
    _fresh(s, ag, 1)
    _tick(s)
    assert not s.nodes("QualiaBehaviorPrediction")
    request = next(n for n in s.nodes("ThinkingBudgetRequest")
                   if s.node(n)["attrs"].get("requester_kind") == "qualia_behavior_inference")
    assert s.node(request)["attrs"]["status"] == "denied"


def test_illegal_proposal_never_receives_native_authorization():
    s, ag = _boot()
    _axis(s, ag)
    _fresh(s, ag, 1)
    context = s.nodes("QualiaActionContext")[0]
    s.set_attr(context, "legal_actions", ["continue"])
    _tick(s)
    assert len(s.nodes("QualiaBehaviorPrediction")) == 1
    assert not s.nodes("QualiaActionAuthorization")


def test_verified_consequences_earn_contextual_significance_and_priority():
    s, ag = _boot()
    _axis(s, ag)
    _fresh(s, ag, 1, outcome="restored", context="same-context")
    _tick(s)
    _fresh(s, ag, 2, outcome="restored", context="same-context")
    _tick(s)
    sigs = s.nodes("ExperientialSignificance")
    assert len(sigs) == 1
    attrs = s.node(sigs[0])["attrs"]
    assert attrs["status"] == "standing"
    assert attrs["effect_category"] == "supportive"
    assert attrs["attention_priority"] == "reuse_candidate"
    assert len(s.neighbours(sigs[0], "supported_by")) == 2
    assert all(s.node(p)["attrs"]["attention_priority"] == "reuse_candidate"
               for p in s.nodes("QualiaBehaviorPrediction"))


def test_significance_is_context_sensitive_and_adverse_is_retained():
    s, ag = _boot()
    _axis(s, ag)
    _fresh(s, ag, 1, outcome="restored", context="context-a", goal_effect=1.0)
    _tick(s)
    _fresh(s, ag, 2, outcome="restored", context="context-a", goal_effect=1.0)
    _tick(s)
    _fresh(s, ag, 3, outcome="damaged", context="context-b", goal_effect=-1.0)
    _tick(s)
    sigs = s.nodes("ExperientialSignificance")
    assert {s.node(sig)["attrs"]["effect_category"] for sig in sigs} == {"supportive"}
    assert {s.node(sig)["attrs"]["context_id"] for sig in sigs} == {"context-a"}
    evidence = [s.node(node)["attrs"] for node in s.nodes("ExperientialSignificanceEvidence")]
    assert any(row["effect_category"] == "adverse" and row["context_id"] == "context-b"
               and row["observed_consequence"] == "damaged" for row in evidence)
    # A single reversal is retained but cannot earn a second standing category.
    assert all(s.node(sig)["attrs"]["attention_priority"] == "reuse_candidate" for sig in sigs)
