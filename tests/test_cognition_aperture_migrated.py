"""Typed Observer adapter boundary tests; aperture authority remains upstream."""
import json

from substrate_rs import _native
from substrate.seed_loader import manifest_for
from scripts.gen_cognition_aperture_seed import ADAPTERS, OUT, build_seed
from tests.test_aperture_frame_migrated import _observer, _part, _resolves, FULL


def _boot(enabled=True):
    s = _native.Substrate()
    ag = s.add_node("Agent", {})
    loaded_ids = set()

    def load_closure(seed_id, explicit=None):
        if seed_id == "core":
            return
        if seed_id in loaded_ids:
            return
        manifest = explicit if explicit is not None else manifest_for(seed_id)
        for dependency in manifest.get("depends_on", ()):
            load_closure(str(dependency))
        summary = s.load_seed_manifest(manifest, ag)
        assert summary.get("rules_skipped") == [], (seed_id, summary)
        loaded_ids.add(seed_id)

    load_closure("cognition_aperture", build_seed())
    policy = s.nodes("CognitionAperturePolicy")[0]
    s.set_attr(policy, "enabled", 1.0 if enabled else 0.0)
    return s, ag


def _tick(s):
    for _ in range(20):
        if not s.run_rules(1000):
            return
    raise AssertionError("aperture adapters did not reach a fixpoint")


def _source(s, ag, adapter, key, owner, authority="chosen", epoch=3, value=1,
            observer=None, voi_status="unknown", voi_evidence_id=None):
    src = s.add_node("CognitionApertureSource", {
        "adapter_id": adapter, "source_key": key, "owner_id": owner,
        "frame_id": f"frame:{owner}", "source_epoch": epoch,
        "value_kind": "integer", "value": value, "missing": False,
        "tolerance": 0, "authority": authority,
        "voi_status": voi_status, "voi_evidence_id": voi_evidence_id,
        "dimension_id": f"observer:qualia:{key}" if adapter == "qualia_aperture" else "unused",
    })
    s.add_edge(ag, "has_cognition_aperture_source", src)
    if observer is not None:
        s.add_edge(src, "applies_to_observer", observer)
    return src


def _enable_budget(s, ag, remaining=1):
    modes = s.neighbours(ag, "has_network_mode_state")
    if modes:
        mode = modes[0]
    else:
        mode = s.add_node("NetworkModeState", {"epoch": 1.0, "mode": "awake"})
        s.add_edge(ag, "has_network_mode_state", mode)
    s.set_attr(mode, "epoch", 1.0)
    s.set_attr(mode, "mode", "awake")
    budget = s.nodes("ThinkingBudget")[0]
    for key, value in {"enabled": 1.0, "remaining": float(remaining),
                       "refill_per_epoch": 0.0, "last_refill_epoch": 1.0}.items():
        s.set_attr(budget, key, value)
    return mode, budget


def test_dependency_closure_and_generator_reproduction():
    assert json.loads(OUT.read_text()) == build_seed()
    s, _ = _boot()
    assert len(s.nodes("CognitionAperturePolicy")) == 1


def test_six_adapters_round_trip_as_distinct_dimensions():
    s, ag = _boot()
    for ix, adapter in enumerate(ADAPTERS):
        _source(s, ag, adapter, f"source-{ix}", "observer-a", value=ix)
    _tick(s)
    dims = [s.node(n)["attrs"] for n in s.nodes("CognitionApertureDimension")]
    assert {d["adapter_id"] for d in dims} == set(ADAPTERS)
    assert {d["dimension_id"] for d in dims} == {
        "observer:reading", "observer:dwell", "observer:difference_order",
        "observer:qualia:source-3", "observer:decode_scope", "observer:manifold_mask"}
    assert all(d["owner_id"] == "observer-a" and d["source_epoch"] == 3 for d in dims)


def test_two_observers_do_not_leak_and_forced_authority_is_preserved():
    s, ag = _boot()
    _source(s, ag, "reading", "a", "observer-a", "chosen", value=2)
    _source(s, ag, "reading", "b", "observer-b", "forced", value=5)
    _tick(s)
    dims = {s.node(n)["attrs"]["owner_id"]: s.node(n)["attrs"]
            for n in s.nodes("CognitionApertureDimension")}
    assert dims["observer-a"]["value"] == 2
    assert dims["observer-b"]["value"] == 5
    assert dims["observer-b"]["authority"] == "forced"
    assert s.nodes("FundedOperationRequest") == []


def test_disabled_policy_does_not_project():
    s, ag = _boot(enabled=False)
    _source(s, ag, "manifold_mask", "mask", "observer-a")
    _tick(s)
    assert s.nodes("CognitionApertureDimension") == []


def test_source_epoch_rebuilds_and_retires_projection():
    s, ag = _boot()
    src = _source(s, ag, "reading", "read", "observer-a")
    _tick(s)
    s.set_attr(src, "source_epoch", 4)
    s.set_attr(src, "value", 2)
    _tick(s)
    dims = [s.node(n)["attrs"] for n in s.nodes("CognitionApertureDimension")]
    assert sorted((d["source_epoch"], d["status"]) for d in dims) == [(3, "stale"), (4, "current")]


def _install_hidden_residual_case(s, ag, *, authority="chosen", name="observer-a"):
    observer = _observer(s, name)
    aperture = s.add_node("Aperture", {"name": "narrow", "resolves": ["pred", "val"]})
    s.add_edge(observer, "chose_aperture" if authority == "chosen" else "forced_aperture", aperture)
    s.add_edge(observer, "holds_part", _part(s, "barometer"))
    s.add_edge(observer, "perceives", _part(s, "tea_leaves"))
    source = _source(s, ag, "reading", f"source-{name}", name,
                     authority=authority, observer=observer,
                     voi_status="positive" if authority == "chosen" else "unknown",
                     voi_evidence_id=f"voi:{name}" if authority == "chosen" else None)
    return observer, source


def test_hidden_residual_probe_is_funded_once_and_terminal_state_restores():
    s, ag = _boot()
    mode, budget = _enable_budget(s, ag, remaining=1)
    observer, _source_node = _install_hidden_residual_case(s, ag)
    _tick(s)

    requests = [n for n in s.nodes("ThinkingBudgetRequest")
                if s.node(n)["attrs"].get("requester_kind") == "cognition_aperture_probe"]
    assert len(requests) == 1
    req = s.node(requests[0])["attrs"]
    assert req["status"] == "consumed"
    assert req["debited_epoch"] == 1.0
    assert s.node(budget)["attrs"]["remaining"] == 0.0
    assert s.node(mode)["attrs"]["epoch"] == s.node(observer)["attrs"]["ap_question_funded_epoch"]
    assert s.neighbours(observer, "probe_projected")
    assert set(_resolves(s, observer)) == set(FULL)
    assert s.node(observer)["attrs"]["ap_question_funding_required"] is True
    assert s.node(observer)["attrs"]["ap_question_funded"] is False


def test_denied_probe_does_not_run_or_retry_and_forced_frame_stays_forced():
    s, ag = _boot()
    _enable_budget(s, ag, remaining=0)
    observer, _ = _install_hidden_residual_case(s, ag)
    forced, _ = _install_hidden_residual_case(
        s, ag, authority="forced", name="observer-forced")
    _tick(s)

    requests = [n for n in s.nodes("ThinkingBudgetRequest")
                if s.node(n)["attrs"].get("requester_kind") == "cognition_aperture_probe"]
    assert len(requests) == 1
    assert s.node(requests[0])["attrs"]["status"] == "denied"
    assert s.neighbours(observer, "probe_projected") == []
    assert s.node(observer)["attrs"]["ap_question_funding_required"] is True
    assert s.node(observer)["attrs"]["ap_question_funded"] is False
    assert s.neighbours(forced, "probe_projected") == []
    assert s.neighbours(forced, "forced_aperture")
    assert s.nodes("ThinkingBudgetRequest")[0] == requests[0]


def test_unknown_voi_stays_unresolved_and_blocks_unfunded_probe():
    s, ag = _boot()
    _enable_budget(s, ag, remaining=2)
    observer = _observer(s, "observer-unknown-voi")
    aperture = s.add_node("Aperture", {"name": "narrow", "resolves": ["pred", "val"]})
    s.add_edge(observer, "chose_aperture", aperture)
    s.add_edge(observer, "holds_part", _part(s, "barometer"))
    s.add_edge(observer, "perceives", _part(s, "tea_leaves"))
    _source(s, ag, "reading", "unknown-voi", "observer-unknown-voi",
            authority="chosen", observer=observer)
    _tick(s)
    assert s.node(observer)["attrs"]["ap_question_funding_required"] is True
    assert s.neighbours(observer, "probe_projected") == []
    assert s.neighbours(observer, "has_cognition_aperture_request") == []
    assert s.node(s.nodes("ThinkingBudget")[0])["attrs"]["remaining"] == 2.0


def test_two_observers_share_budget_without_sharing_authorization():
    s, ag = _boot()
    _enable_budget(s, ag, remaining=1)
    first, _ = _install_hidden_residual_case(s, ag, name="observer-first")
    second, _ = _install_hidden_residual_case(s, ag, name="observer-second")
    _tick(s)

    requests = [n for n in s.nodes("ThinkingBudgetRequest")
                if s.node(n)["attrs"].get("requester_kind") == "cognition_aperture_probe"]
    assert len(requests) == 2
    statuses = [s.node(request)["attrs"]["status"] for request in requests]
    assert sorted(statuses) == ["consumed", "denied"]
    assert sum(bool(s.neighbours(n, "probe_projected")) for n in (first, second)) == 1
    blocked = next(observer for observer in (first, second)
                   if s.node(s.neighbours(observer, "has_cognition_aperture_request")[0])
                   ["attrs"]["status"] == "denied")
    assert s.node(blocked)["attrs"].get("ap_question_funded") is False
    assert s.node(s.nodes("ThinkingBudget")[0])["attrs"]["remaining"] == 0.0
