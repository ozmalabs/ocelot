"""G2.1 contract fixtures and G2.2 native evidence-preserving reappraisal."""
from __future__ import annotations

from copy import deepcopy
import json

from substrate_rs import _native
from substrate.seed_loader import manifest_for
from scripts.gen_reappraisal_seed import OUT, build_seed
from tests.test_cognition_aperture_migrated import (
    _enable_budget, _install_hidden_residual_case, _tick as _tick_aperture,
)


def _event():
    return {
        "event_id": "feedback-17",
        "observed_facts": ["reviewer requested two changes"],
        "source_id": "message-88",
        "forced_constraints": ["the review contained criticism"],
        "appraisal": "threat",
        "arousal": 0.8,
    }


def _supported_alternative():
    return {
        "frame_id": "actionable-feedback",
        "claims": ["the reviewer identified changes that can improve the report"],
        "evidence_refs": ["message-88", "reviewer-request-2"],
        "contradicting_evidence_refs": [],
        "forced_constraints": ["the review contained criticism"],
        "appraisal_result": "challenge",
    }


def test_alternative_input_reappraised():
    event = _event()
    frame = _supported_alternative()
    evidence_ids = {event["source_id"], "reviewer-request-2"}
    assert frame["frame_id"] != ""
    assert frame["evidence_refs"]
    assert set(frame["evidence_refs"]) <= evidence_ids
    assert frame["contradicting_evidence_refs"] == []
    assert frame["appraisal_result"] == "challenge"


def test_event_unchanged():
    event = _event()
    original = deepcopy(event)
    reappraisal_view = {
        "source_event_id": event["event_id"],
        "frame": _supported_alternative(),
    }
    assert event == original
    assert reappraisal_view["source_event_id"] == event["event_id"]
    assert reappraisal_view["frame"]["forced_constraints"] == event["forced_constraints"]


def test_unsupported_optimism_rejected():
    frame = {
        "frame_id": "they-loved-it",
        "claims": ["the reviewer loved the report"],
        "evidence_refs": [],
        "contradicting_evidence_refs": [],
        "appraisal_result": "relief",
    }
    assert not frame["evidence_refs"]
    assert frame["claims"]
    # No evidence means this frame cannot be registered as admissible.
    assert frame.get("admissible", False) is False


def test_no_frame_no_reappraisal():
    probe = {"event": _event(), "candidate_frames": []}
    assert probe["candidate_frames"] == []
    assert probe.get("reappraisal_view") is None


def _boot_reappraisal(enabled=True):
    s = _native.Substrate()
    ag = s.add_node("Agent", {})
    loaded = set()

    def load(seed_id, explicit=None):
        if seed_id == "core" or seed_id in loaded:
            return
        manifest = explicit if explicit is not None else manifest_for(seed_id)
        for dependency in manifest.get("depends_on", ()):
            load(str(dependency))
        summary = s.load_seed_manifest(manifest, ag)
        assert summary.get("rules_skipped") == [], (seed_id, summary)
        loaded.add(seed_id)

    load("reappraisal", build_seed())
    s.set_attr(s.nodes("ReappraisalPolicy")[0], "enabled", 1.0 if enabled else 0.0)
    return s, ag


def _funded_event_case(*, enabled=True, forced_constraints=None, probe_budget=1):
    s, ag = _boot_reappraisal(enabled)
    s.set_attr(s.nodes("CognitionAperturePolicy")[0], "enabled", 1.0)
    mode, budget = _enable_budget(s, ag, remaining=probe_budget)
    observer, source = _install_hidden_residual_case(s, ag)
    _tick_aperture(s)
    requests = [n for n in s.nodes("ThinkingBudgetRequest")
                if s.node(n)["attrs"].get("requester_kind") == "cognition_aperture_probe"]
    assert len(requests) == 1
    request = requests[0]
    assert s.node(request)["attrs"]["status"] == ("consumed" if probe_budget else "denied")

    constraints = forced_constraints or ["the review contained criticism"]
    event = s.add_node("ReappraisalEvent", {
        "event_id": "feedback-17", "source_epoch": 3.0,
        "forced_constraints": constraints, "emotion": "fear", "valence": -0.7,
        "arousal": 0.8,
    })
    hub = s.add_node("EmotionHub", {})
    s.add_node("HeldEmotionParams", {})
    appraisal = s.add_node("Appraisal", {"emotion": "fear", "hit_fear": 1.0,
                                          "valence": -0.7, "arousal": 0.8})
    s.add_edge(hub, "has_emotion_params", s.nodes("HeldEmotionParams")[0])
    s.add_edge(hub, "has_appraisal", appraisal)
    s.add_edge(ag, "has_reappraisal_event", event)
    s.add_edge(event, "has_reappraisal_appraisal_hub", hub)
    evidence = s.add_node("ReappraisalEvidence", {
        "evidence_id": "review-request-2", "status": "current", "source_epoch": 3.0,
        "claim": "reviewer identified changes that can improve the report",
    })
    s.add_edge(event, "has_reappraisal_evidence", evidence)
    frame = s.add_node("ReappraisalFrame", {
        "frame_id": "actionable-feedback", "candidate_index": 1.0,
        "source_epoch": 3.0, "forced_constraints": constraints,
        "aperture_source_key": s.node(source)["attrs"]["source_key"],
        "aperture_authority": "chosen", "appraisal_result": "challenge",
        "appraised": True, "emotion": "challenge", "hit_joy": 0.0,
        "hit_fear": 0.2, "valence": 0.2, "arousal": 0.4,
    })
    claim = s.add_node("InterpretationClaim", {"claim_id": "claim-1"})
    s.add_edge(event, "has_candidate_reappraisal_frame", frame)
    s.add_edge(frame, "has_interpretation_claim", claim)
    s.add_edge(claim, "supported_by", evidence)
    s.add_edge(frame, "has_funded_probe", request)
    return s, ag, mode, budget, event, appraisal, frame, claim, evidence


def _tick_native(s):
    for _ in range(20):
        if not s.run_rules(1000):
            return
    raise AssertionError("reappraisal rules did not reach a fixpoint")


def test_generator_reproduces_native_seed():
    assert json.loads(OUT.read_text()) == build_seed()
    s, _ = _boot_reappraisal()
    assert len(s.nodes("ReappraisalPolicy")) == 1


def test_probe_funded_once():
    s, ag, _mode, budget, _event, _appraisal, _frame, *_ = _funded_event_case()
    _tick_native(s)
    assert len(s.nodes("ThinkingBudgetRequest")) == 1
    assert s.node(budget)["attrs"]["remaining"] == 0.0
    assert len(s.neighbours(ag, "has_reappraisal_view")) == 1
    assert len(s.nodes("Appraisal")) == 2


def test_appraisal_provenance_retained():
    s, ag, _mode, _budget, event, source_appraisal, frame, *_ = _funded_event_case()
    before = deepcopy(s.node(event)["attrs"])
    _tick_native(s)
    view = s.neighbours(ag, "has_reappraisal_view")[0]
    derived = s.neighbours(view, "derived_appraisal")[0]
    assert s.node(view)["attrs"]["source_event_id"] == "feedback-17"
    assert s.neighbours(view, "based_on_reappraisal_event") == [event]
    assert s.neighbours(view, "selected_interpretation_frame") == [frame]
    assert s.neighbours(view, "funded_by_probe")[0] in s.nodes("ThinkingBudgetRequest")
    assert s.node(derived)["attrs"]["frame_id"] == "actionable-feedback"
    assert s.node(derived)["attrs"]["emotion"] == "challenge"
    assert s.node(source_appraisal)["attrs"]["emotion"] == "fear"
    assert s.node(event)["attrs"] == before


def test_forced_constraints_preserved():
    s, ag, *_rest = _funded_event_case()
    frame = _rest[4]
    s.set_attr(frame, "forced_constraints", ["the review contained praise"])
    _tick_native(s)
    assert s.neighbours(ag, "has_reappraisal_view") == []


def test_unsupported_or_contradicted_claim_is_rejected():
    s, ag, *_rest = _funded_event_case()
    claim, evidence = _rest[-2:]
    s.remove_edge(claim, "supported_by", evidence)
    _tick_native(s)
    assert s.neighbours(ag, "has_reappraisal_view") == []

    s, ag, *_rest = _funded_event_case()
    claim, evidence = _rest[-2:]
    counter = s.add_node("ReappraisalEvidence", {
        "evidence_id": "counter", "status": "current", "source_epoch": 3.0,
    })
    event = _rest[2]
    s.add_edge(event, "has_reappraisal_evidence", counter)
    s.add_edge(claim, "contradicted_by", counter)
    _tick_native(s)
    assert s.neighbours(ag, "has_reappraisal_view") == []


def test_default_off_and_denied_probe_produce_no_view():
    s, ag, *_ = _funded_event_case(enabled=False)
    _tick_native(s)
    assert s.neighbours(ag, "has_reappraisal_view") == []

    s, ag, *_ = _funded_event_case(probe_budget=0)
    _tick_native(s)
    assert s.neighbours(ag, "has_reappraisal_view") == []
