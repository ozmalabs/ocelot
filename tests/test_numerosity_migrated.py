"""P7.05 graph-rule tests; symbolic NumberWorld remains separately tested."""
import json
from pathlib import Path

from substrate_rs import _native

from scripts.gen_numerosity_seed import build_seed
from domains.number_world import perceptual_scene_attrs

ROOT = Path(__file__).resolve().parents[1]


def _boot(enabled=True):
    s = _native.Substrate()
    ag = s.add_node("Agent", {})
    for name in ("default_mode_core", "thinking_budget", "qualia_space",
                 "cognition_signature", "experience_signature", "qualia_acquisition"):
        s.load_seed_manifest(json.loads((ROOT / "seeds" / f"{name}.json").read_text()), ag)
    result = s.load_seed_manifest(build_seed(), ag)
    assert result["rules_skipped"] == [], result
    s.set_attr(s.nodes("NumerosityPolicy")[0], "enabled", 1.0 if enabled else 0.0)
    s.set_attr(s.nodes("ThinkingBudget")[0], "enabled", 1.0)
    s.set_attr(s.nodes("ThinkingBudget")[0], "last_refill_epoch", 10.0)
    return s, ag


def _small_group(s, ag, name, count, *, owner="owner-a", epoch=2, frame=5):
    scene_attrs = perceptual_scene_attrs(scene_id=name, owner_id=owner,
        source_epoch=epoch, frame_epoch=frame, mode="small", scene_regions=count,
        individuation_status="clear")
    scene = s.add_node("NumerosityScene", scene_attrs)
    group = s.add_node("NumerosityGroup", {**scene_attrs, "group_id": name})
    s.add_edge(ag, "has_numerosity_scene", scene)
    s.add_edge(scene, "has_numerosity_group", group)
    s.add_edge(group, "observed_in_scene", scene)
    for i in range(count):
        obj = s.add_node("NumerosityObject", {"object_id": f"{name}-object-{i}",
            "owner_id": owner, "source_epoch": epoch, "frame_epoch": frame,
            "status": "observed"})
        s.add_edge(group, "has_individuated_object", obj)
    return group


def _aggregate_group(s, ag, name, area, density, *, area_u=.01, density_u=.01,
                     owner="owner-a", epoch=2, frame=5):
    scene_attrs = perceptual_scene_attrs(scene_id=name, owner_id=owner,
        source_epoch=epoch, frame_epoch=frame, mode="aggregate", scene_regions=1,
        occupied_area=area, density_signal=density,
        area_uncertainty=area_u, density_uncertainty=density_u)
    scene = s.add_node("NumerosityScene", scene_attrs)
    group = s.add_node("NumerosityGroup", {**scene_attrs, "group_id": name})
    s.add_edge(ag, "has_numerosity_scene", scene)
    s.add_edge(scene, "has_numerosity_group", group)
    s.add_edge(group, "observed_in_scene", scene)
    return group


def _request(s, ag, a, b, name):
    req = s.add_node("NumerosityCompareRequest", {"request_id": name,
        "owner_id": "owner-a", "source_epoch": 2, "frame_epoch": 5,
        "status": "pending", "result": None})
    s.add_edge(ag, "has_numerosity_request", req)
    s.add_edge(req, "compares_group_a", a)
    s.add_edge(req, "compares_group_b", b)
    return req


def _tick(s):
    for _ in range(20):
        if not s.run_rules(1000):
            return
    raise AssertionError("numerosity rules did not reach a fixpoint")


def test_small_sets_exact():
    s, ag = _boot()
    requests = []
    for count in range(5):
        a = _small_group(s, ag, f"small-a-{count}", count)
        b = _small_group(s, ag, f"small-b-{count}", 4)
        requests.append((count, _request(s, ag, a, b, f"small-compare-{count}")))
    _tick(s)
    for count, req in requests:
        attrs = s.node(req)["attrs"]
        assert attrs["result"] == ("LESS" if count < 4 else "SAME_WITHIN_RESOLUTION")
        assert attrs["method"] == "individuated_tokens"
        assert attrs["exact_a"] == count and attrs["exact_b"] == 4


def test_hidden_count_not_visible():
    s, ag = _boot()
    a = _aggregate_group(s, ag, "aggregate-a", 2.0, 3.0)
    b = _aggregate_group(s, ag, "aggregate-b", 1.0, 3.0)
    req = _request(s, ag, a, b, "aggregate-compare")
    _tick(s)
    assert s.node(req)["attrs"]["result"] == "MORE"
    assert "exact_count" not in s.node(a)["attrs"] and "exact_count" not in s.node(b)["attrs"]
    assert "hidden_count" not in s.node(req)["attrs"]
    assert s.node(req)["attrs"]["method"] == "aggregate_interval"


def test_area_density_conflict_abstains():
    s, ag = _boot()
    a = _aggregate_group(s, ag, "conflict-a", 4.0, 1.0)
    b = _aggregate_group(s, ag, "conflict-b", 2.0, 2.0)
    req = _request(s, ag, a, b, "conflict-compare")
    _tick(s)
    attrs = s.node(req)["attrs"]
    assert attrs["result"] == "UNKNOWN"
    assert attrs["method"] == "aggregate_interval"


def test_equal_ratio_scale_contract():
    s, ag = _boot()
    a1 = _aggregate_group(s, ag, "scale-a1", 2.0, 2.0)
    b1 = _aggregate_group(s, ag, "scale-b1", 1.0, 2.0)
    r1 = _request(s, ag, a1, b1, "scale-compare-1")
    a2 = _aggregate_group(s, ag, "scale-a2", 20.0, 2.0)
    b2 = _aggregate_group(s, ag, "scale-b2", 10.0, 2.0)
    r2 = _request(s, ag, a2, b2, "scale-compare-2")
    _tick(s)
    one, two = s.node(r1)["attrs"], s.node(r2)["attrs"]
    assert one["result"] == two["result"] == "MORE"
    assert abs(one["ratio_estimate"] - two["ratio_estimate"]) < 1e-9


def test_policy_disabled_by_default():
    s, ag = _boot(enabled=False)
    a = _small_group(s, ag, "disabled-a", 2)
    b = _small_group(s, ag, "disabled-b", 1)
    req = _request(s, ag, a, b, "disabled-compare")
    _tick(s)
    assert s.node(req)["attrs"]["status"] == "pending"
    assert s.node(req)["attrs"]["result"] is None


def test_percept_input_adapter_has_no_count_channel():
    attrs = perceptual_scene_attrs(scene_id="sensor-1", owner_id="owner-a",
        source_epoch=1, frame_epoch=2, mode="aggregate", scene_regions=64,
        occupied_area=3.5, density_signal=1.2, area_uncertainty=.2,
        density_uncertainty=.1)
    assert attrs["mode"] == "aggregate"
    assert "exact_count" not in attrs and "hidden_count" not in attrs
    try:
        perceptual_scene_attrs(scene_id="bad", owner_id="owner-a", source_epoch=1,
            frame_epoch=2, mode="aggregate", scene_regions=5000, occupied_area=1,
            density_signal=1, area_uncertainty=0, density_uncertainty=0)
    except ValueError:
        pass
    else:
        raise AssertionError("unbounded region input accepted")


def test_small_sets_above_limit_abstain():
    s, ag = _boot()
    a = _small_group(s, ag, "too-many-a", 5)
    b = _small_group(s, ag, "too-many-b", 4)
    req = _request(s, ag, a, b, "too-many-compare")
    _tick(s)
    assert s.node(req)["attrs"]["result"] == "UNKNOWN"
