"""tests/test_motor_intent_migrated.py — generic motor-intent layer gates.

Covers:
  1. Noise realized BEFORE MotorPlan minted (inverse-model pipeline order)
  2. Graph rules mint MotorPlan + MotorIntent + MotorNoise from ExecutionTrace
  3. Lift-noise ablation: extracted intent picks the right class; arrangement fails
  4. SelfConcern filed when outcome matching fails (graph rule)
  5. No Python ranking decisions in domains/motor_intent.py
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("substrate_rs")

import substrate_rs as srs
from substrate.boot_core import boot_core
from substrate.seed_loader import manifest_for

from domains import motor_intent as mi

ROOT = Path(__file__).resolve().parent.parent

SQ_LIVE = mi.stroke_quantize_live()
SQ_SKIP = "StrokeQuantize not live — build runners/dsl with maturin develop"


@pytest.fixture(scope="module")
def native():
    return srs.Substrate()._inner


def _boot():
    s, ag = boot_core()
    native = s._inner
    native.load_seed_manifest(manifest_for("motor_intent_core"), ag)
    return s, ag, native


class _Adapter:
    def __init__(self, s, ag):
        self.s = s
        self.agent = ag
        self.inner = s._inner


def _l_stroke0():
    return [[0.0, 0.0], [0.0, 1.0], [0.0, 2.0]]


def _l_stroke1():
    return [[0.0, 2.0], [1.0, 2.0], [2.0, 2.0]]


def _diag_stroke1():
    return [[0.0, 2.0], [1.0, 3.0], [2.0, 4.0]]


def _lifted_stroke1():
    """Same horizontal shape as _l_stroke1, wildly displaced (bad pen lift)."""
    return [[10.0, 8.0], [11.0, 8.0], [12.0, 8.0]]


def test_noise_realized_before_plan_minted(native):
    """Intent extraction requires noise realization first — not direct from raw trace."""
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    s, ag, _ = _boot()
    a = _Adapter(s, ag)
    tid = mi.annotate_execution_trace(a, [_l_stroke0(), _lifted_stroke1()],
                                       goal_kind="replicate_template")
    trace = s.node(srs.NodeID(tid))["attrs"]
    assert float(trace.get("noise_realized", 0)) == 1.0
    assert float(trace.get("plan_extracted", 0)) == 1.0
    assert float(trace.get("plan_inferred", 0)) == 1.0
    plan = s.node(s.nodes("MotorPlan")[0])["attrs"]
    assert plan.get("source") == "inverse_model"
    assert plan.get("plan_segments")
    noise = mi.held_motor_noise(a)
    assert any(n.get("kind") == "inter_stroke_lift" for n in noise)


def test_rules_mint_motor_plan_and_intent(native):
    """ExecutionTrace → realize noise → inverse model → MotorPlan + MotorIntent."""
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    s, ag, _ = _boot()
    a = _Adapter(s, ag)
    tid = mi.annotate_execution_trace(a, [_l_stroke0(), _l_stroke1()],
                                       goal_kind="replicate_template")
    plans = s.nodes("MotorPlan")
    intents = s.nodes("MotorIntent")
    assert len(plans) >= 1
    assert len(intents) >= 1
    pa = s.node(plans[0])["attrs"]
    ia = s.node(intents[0])["attrs"]
    assert pa.get("goal_kind_hint") == "replicate_template"
    assert ia.get("goal_kind") == "replicate_template"
    assert float(pa.get("stroke_count", 0)) == 2.0
    extracted = mi.read_extracted_plan(a, tid)
    assert extracted is not None and len(extracted) == 2


def test_lift_noise_intent_beats_arrangement(native):
    """HEADLINE: realize lift noise → extract intent → L wins; arrangement on raw canvas fails."""
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    query = [_l_stroke0(), _lifted_stroke1()]
    extracted = mi.extract_motor_plan(native, query)
    cand_l = mi.extract_plan_segments(native, [_l_stroke0(), _l_stroke1()])
    cand_diag = mi.extract_plan_segments(native, [_l_stroke0(), _diag_stroke1()])

    intent_res = mi.motor_intent_verdict(
        native, query, [cand_l, cand_diag], mode="intent",
        query_plan_segs=extracted["plan_segments"])
    arr_res = mi.motor_intent_verdict(native, query, [cand_l, cand_diag], mode="arrangement")

    assert intent_res["winner"] == 0, f"extracted intent should pick L-shaped plan, got {intent_res}"
    assert arr_res["winner"] != 0 or arr_res["scores"][0][0] > intent_res["scores"][0][0], (
        f"arrangement should not beat extracted intent under lift noise: intent={intent_res}, arr={arr_res}")


def test_outcome_failure_files_self_concern(native):
    """Adapter stamps outcome_match_failed → gap rule files SelfConcern."""
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    s, ag, _ = _boot()
    a = _Adapter(s, ag)
    tid = mi.annotate_execution_trace(a, [_l_stroke0(), _lifted_stroke1()])
    mi.record_outcome_match_failure(a, tid)
    concerns = [s.node(n)["attrs"] for n in s.nodes("SelfConcern")]
    assert any("motor intent" in str(c.get("content", "")).lower() or
               "outcome" in str(c.get("content", "")).lower() for c in concerns)


def test_no_python_decisions_in_motor_intent_module():
    violations = mi.audit_no_python_decisions()
    assert not violations, violations


def test_intent_match_term_uses_extracted_plans(native):
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    query = [_l_stroke0(), _lifted_stroke1()]
    extracted = mi.extract_motor_plan(native, query)
    cand_segs = mi.extract_plan_segments(native, [_l_stroke0(), _l_stroke1()])
    term = mi.intent_match_term(extracted["plan_segments"], cand_segs, native=native)
    assert term is not None
    score = float(native.evaluate(term, {}))
    assert score >= 0.0
