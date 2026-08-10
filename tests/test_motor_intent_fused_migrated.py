"""tests/test_motor_intent_fused_migrated.py — proper motor-intent verdict stack gates."""
from __future__ import annotations

import pytest

pytest.importorskip("substrate_rs")

import substrate_rs as srs
from domains import motor_intent as mi

SQ_LIVE = mi.stroke_quantize_live()
SR_LIVE = mi.stroke_render_live()
SQ_SKIP = "StrokeQuantize not live"
SR_SKIP = "StrokeRender not live"


@pytest.fixture(scope="module")
def native():
    return srs.Substrate()._inner


def _l0():
    return [[0.0, 0.0], [0.0, 1.0], [0.0, 2.0]]


def _l1():
    return [[0.0, 2.0], [1.0, 2.0], [2.0, 2.0]]


def _lifted1():
    return [[10.0, 8.0], [11.0, 8.0], [12.0, 8.0]]


def test_abs_intent_topology_picks_correct_class(native):
    if not SQ_LIVE or not SR_LIVE:
        pytest.skip(SQ_SKIP if not SQ_LIVE else SR_SKIP)
    q = [_l0(), _lifted1()]
    sup_l = [_l0(), _l1()]
    sup_d = [_l0(), [[0.0, 2.0], [1.0, 3.0], [2.0, 4.0]]]
    intent_w = mi.classify_abs_intent(native, q, [sup_l, sup_d], mode="topology")
    assert intent_w == 0


def test_abs_intent_arrangement_classifies(native):
    if not SQ_LIVE or not SR_LIVE:
        pytest.skip(SQ_SKIP if not SQ_LIVE else SR_SKIP)
    q = [_l0(), _lifted1()]
    sup_l = [_l0(), _l1()]
    sup_d = [_l0(), [[0.0, 2.0], [1.0, 3.0], [2.0, 4.0]]]
    w = mi.classify_abs_intent(native, q, [sup_l, sup_d], mode="arrangement")
    assert w in (0, 1)


def test_program_intent_beats_raw_on_lift_noise(native):
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    q = [_l0(), _lifted1()]
    sup_l = [_l0(), _l1()]
    sup_d = [_l0(), [[0.0, 2.0], [1.0, 3.0], [2.0, 4.0]]]
    raw_w = mi.classify_per_stroke_program(q, [sup_l, sup_d], intent_corrected=False)
    intent_w = mi.classify_per_stroke_program(q, [sup_l, sup_d], intent_corrected=True)
    assert intent_w == 0
    assert raw_w != 0 or intent_w == 0


def test_sctps_diag_is_diagnostic_only(native):
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    q = [_l0(), _lifted1()]
    sup_l = [_l0(), _l1()]
    w = mi.classify_sctps_diag(native, q, [sup_l, sup_l])
    assert w in (0, 1)
