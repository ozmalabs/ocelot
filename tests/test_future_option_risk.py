import math
import pytest
from domains.future_option_risk import FutureManifold, ManifoldProjection, ShapeSlice, evaluate_future_manifold
from domains.learning_safety import LearningSafetyContext

def tube(extra=()):
    return [{"time": t, "cells": {"core": {"weight": 2.0, "information": 2.0, "metadata": {"kind": "core"}}}, "links": []} for t in range(3)]
def m(**kw):
    x={"manifold_id":"m", "required_horizon":2, "minimum_width":1.0, "maximum_information_loss":0.0, "required_tube":tube()}; x.update(kw); return FutureManifold.from_mapping(x)
def p(**kw):
    x={"manifold_id":"m", "projected_tube":tube(), "action_count":1, "intervention_magnitude":0.5}; x.update(kw); return ManifoldProjection.from_mapping(x)

def test_allowed_and_residual_math():
    r=evaluate_future_manifold(m(),p()); assert r.allowed and r.reason=="allowed"; assert r.retained_width==2; assert r.information_loss==0

def test_verified_recovery_context_relaxes_declared_triangle():
    context = LearningSafetyContext(
        verified=True, reset_reachable=True, reset_cost_units=4,
        protective_support_available=True,
        protective_support_effectiveness=1.0,
        required_horizon_units=1, minimum_width_relaxation=2.0,
        information_loss_allowance=2.0,
    )
    # One missing horizon slice and one unit of width/loss are covered by the
    # graph-published recovery budget.
    projected_tube = tube()[:2]
    projected = p(projected_tube=projected_tube)
    r = evaluate_future_manifold(m(required_horizon=2, minimum_width=3.0), projected, context)
    assert r.allowed
    assert r.applied_bounds == (1, 1.0, 2.0)

def test_unverified_context_is_gate_off_identity():
    context = LearningSafetyContext(
        verified=False, reset_reachable=True, reset_cost_units=4,
        protective_support_available=True,
        protective_support_effectiveness=1.0,
        required_horizon_units=1, minimum_width_relaxation=10.0,
        information_loss_allowance=10.0,
    )
    assert evaluate_future_manifold(m(), p(projected_tube=tube()[:2]), context).reason == "insufficient_temporal_coverage"

def test_each_verified_recovery_path_is_sufficient_but_no_path_is_not():
    reset = LearningSafetyContext(
        verified=True, reset_reachable=True, reset_cost_units=4,
        protective_support_available=False, protective_support_effectiveness=0.0,
    )
    scaffold = LearningSafetyContext(
        verified=True, reset_reachable=False, reset_cost_units=4,
        protective_support_available=True, protective_support_effectiveness=0.5,
    )
    absent = LearningSafetyContext(
        verified=True, reset_reachable=False, reset_cost_units=4,
        protective_support_available=False, protective_support_effectiveness=0.0,
    )
    assert reset.active and scaffold.active and not absent.active

def test_recovery_context_does_not_admit_unrecoverable_escape():
    context = LearningSafetyContext(
        verified=True, reset_reachable=True, reset_cost_units=4,
        protective_support_available=True, protective_support_effectiveness=1.0,
        required_horizon_units=1, minimum_width_relaxation=10.0,
        information_loss_allowance=10.0,
    )
    projected_tube = tube()
    projected_tube[1]["cells"]["escape"] = {
        "weight": 1.0, "information": 0.0, "metadata": {"kind": "unrecoverable"},
    }
    projected = p(projected_tube=projected_tube)
    assert evaluate_future_manifold(m(), projected, context).reason == "outside_future_manifold"

def test_identity_mismatch(): assert evaluate_future_manifold(m(manifold_id="x"),p()).reason=="manifold_identity_mismatch"
def test_insufficient_temporal_coverage(): assert evaluate_future_manifold(m(),p(projected_tube=tube()[:2])).reason=="insufficient_temporal_coverage"

def test_escape_precedes_width_and_loss():
    q=tube(); q[1]["cells"]["escape"]={"weight":1,"information":1,"metadata":{}}; assert evaluate_future_manifold(m(minimum_width=9),p(projected_tube=q)).reason=="outside_future_manifold"
def test_width_then_loss():
    q=tube(); q[1]["cells"]={}; assert evaluate_future_manifold(m(minimum_width=1),p(projected_tube=q)).reason=="insufficient_width"
    assert evaluate_future_manifold(m(minimum_width=0,maximum_information_loss=0),p(projected_tube=q)).reason=="excess_information_loss"
def test_equal_width_lower_information_is_excess_loss():
    q=tube()
    for s in q: s["cells"]["core"]["information"]=1.0
    r=evaluate_future_manifold(m(),p(projected_tube=q))
    assert r.retained_width == 2.0 and r.information_loss == 1.0
    assert r.reason == "excess_information_loss"
def test_link_only_loss_has_valid_endpoint_witnesses():
    linked=[]
    for t in range(3):
        linked.append({"time":t,"cells":{"a":{"weight":1,"information":1,"metadata":{}},"b":{"weight":1,"information":1,"metadata":{}}},"links":[{"source":"a","target":"b","information":1}]})
    q=[dict(s,links=[]) for s in linked]
    r=evaluate_future_manifold(FutureManifold("m",2,1,0,linked),ManifoldProjection("m",q,0,0))
    assert r.lost_tube[0].links and {c[0] for c in r.lost_tube[0].cells} == {"a","b"}
def test_residual_contains_lost_cells_and_links():
    q=tube(); q[0]["cells"]={}; r=evaluate_future_manifold(m(),p(projected_tube=q)); assert r.lost_tube[0].cells and r.information_loss==2
@pytest.mark.parametrize("bad", [{"time":0,"cells":{"x":{"weight":1}},"links":[["x","z"]]}, {"time":0,"cells":{"x":{"weight":math.nan}},"links":[]}])
def test_shape_validation(bad):
    with pytest.raises(ValueError): p(projected_tube=[bad]+tube()[1:])
def test_metadata_mismatch_rejected():
    q=tube(); q[0]["cells"]["core"]["metadata"]={"kind":"other"}
    with pytest.raises(ValueError): evaluate_future_manifold(m(),p(projected_tube=q))
def test_duplicate_link_endpoints_rejected_even_with_different_information():
    q=tube()
    q[0]["cells"]["other"]={"weight":1,"information":1,"metadata":{}}
    q[0]["links"]=[{"source":"core","target":"other","information":1}, {"source":"core","target":"other","information":2}]
    with pytest.raises(ValueError): ManifoldProjection("m", q, 0, 0)
def test_shared_information_surplus_is_not_escape():
    q=tube()
    for s in q: s["cells"]["core"]["information"]=5
    r=evaluate_future_manifold(m(),p(projected_tube=q))
    assert r.reason == "allowed" and r.escape_width == 0 and r.information_loss == 0
def test_shared_link_information_surplus_is_not_escape():
    required=[]
    projected=[]
    for t in range(3):
        cells={"a":{"weight":1,"information":1,"metadata":{}},"b":{"weight":1,"information":1,"metadata":{}}}
        required.append({"time":t,"cells":cells,"links":[{"source":"a","target":"b","information":1}]})
        projected.append({"time":t,"cells":cells,"links":[{"source":"a","target":"b","information":3}]})
    r=evaluate_future_manifold(FutureManifold("m",2,1,0,required),ManifoldProjection("m",projected,0,0))
    assert r.reason == "allowed" and r.information_loss == 0
def test_mapping_round_trip():
    mm=m().as_mapping(); pp=p().as_mapping(); r=evaluate_future_manifold(mm,pp)
    assert FutureManifold.from_mapping(mm).as_mapping()==mm; assert ManifoldProjection.from_mapping(pp).as_mapping()==pp
    assert r.as_mapping()["reason"] == "allowed"
@pytest.mark.parametrize("old", [
    {"minimum_margin": 1}, {"projected_minimum_margin": 1},
    {"required_futures_lost": 0}, {"projection_horizon": 2}, {"arbitrary": 1},
])
def test_obsolete_and_unknown_top_level_keys_rejected(old):
    with pytest.raises(ValueError): FutureManifold.from_mapping({**m().as_mapping(), **old})
    with pytest.raises(ValueError): ManifoldProjection.from_mapping({**p().as_mapping(), **old})
def test_unknown_shape_keys_rejected():
    bad = {"time": 0, "cells": {"x": {"weight": 1, "information": 1, "metadata": {}, "old": 1}}, "links": []}
    with pytest.raises(ValueError): ShapeSlice.from_mapping(bad)
