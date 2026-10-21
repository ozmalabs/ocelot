"""D6.1 executable contract for lattice-preserving detached rotation work."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "seeds" / "analog_imagery.json"
GENERATOR = ROOT / "scripts" / "gen_analog_imagery_seed.py"
for path in (ROOT, ROOT / "runners" / "dsl" / "python"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
pytest.importorskip("substrate_rs")
from substrate.world_adapter import WorldAdapter

LATTICE = (0, 90, 180, 270)


def shortest_rotation(source_angle: int, target_angle: int) -> tuple[int, ...]:
    """Return signed 90-degree increments on the registered square lattice."""
    if source_angle not in LATTICE or target_angle not in LATTICE:
        raise ValueError("angle is outside the registered lattice")
    clockwise = ((target_angle - source_angle) % 360) // 90
    counterclockwise = ((source_angle - target_angle) % 360) // 90
    if clockwise <= counterclockwise:
        return (90,) * clockwise
    return (-90,) * counterclockwise


def rotate(points: frozenset[tuple[int, int]], direction: int) -> frozenset[tuple[int, int]]:
    """One exact quarter turn, normalized to the minimum row/column origin."""
    if direction == 90:
        transformed = {(c, -r) for r, c in points}
    elif direction == -90:
        transformed = {(-c, r) for r, c in points}
    else:
        raise ValueError("only quarter-turn increments are supported")
    min_r = min(r for r, _ in transformed)
    min_c = min(c for _, c in transformed)
    return frozenset((r - min_r, c - min_c) for r, c in transformed)


def rotate_ordered(points, direction):
    transformed = [(c, -r) if direction == 90 else (-c, r) for r, c in points]
    min_r = min(r for r, _ in transformed)
    min_c = min(c for _, c in transformed)
    return [(r - min_r, c - min_c) for r, c in transformed]


@dataclass(frozen=True)
class ImageryBuffer:
    source: frozenset[tuple[int, int]]
    imagined: frozenset[tuple[int, int]]
    witnesses: tuple[frozenset[tuple[int, int]], ...]
    grounded: bool = False


def imagine_rotation(source, source_angle, target_angle):
    state = frozenset(source)
    witnesses = [state]
    for step in shortest_rotation(source_angle, target_angle):
        state = rotate(state, step)
        witnesses.append(state)
    return ImageryBuffer(frozenset(source), state, tuple(witnesses))


def test_angle_wrap_and_identity():
    assert shortest_rotation(270, 0) == (90,)
    assert shortest_rotation(0, 270) == (-90,)
    assert shortest_rotation(180, 180) == ()
    source = {(0, 0), (0, 1), (1, 1)}
    assert imagine_rotation(source, 90, 90).imagined == frozenset(source)


def test_intermediate_witnesses():
    buffer = imagine_rotation({(0, 0), (0, 1), (1, 1)}, 0, 180)
    assert len(buffer.witnesses) == 3
    assert buffer.witnesses[0] == buffer.source
    assert buffer.witnesses[-1] == buffer.imagined
    assert buffer.witnesses[1] != buffer.witnesses[0]


def test_buffer_never_grounds():
    buffer = imagine_rotation({(0, 0), (0, 1)}, 0, 90)
    assert buffer.grounded is False
    assert buffer.source == frozenset({(0, 0), (0, 1)})


def test_cost_counts_executed_transforms():
    for start, end, expected in ((0, 0, 0), (0, 90, 1), (0, 180, 2), (270, 0, 1)):
        assert len(imagine_rotation({(0, 0), (0, 1)}, start, end).witnesses) - 1 == expected


def test_arbitrary_angles_remain_unresolved():
    try:
        shortest_rotation(0, 45)
    except ValueError:
        pass
    else:
        raise AssertionError("unsupported arbitrary angle was accepted")


def _runtime(shape, steps, *, budget=4):
    agent = WorldAdapter(seeds=["analog_imagery"])
    policy = agent.s.nodes("AnalogImageryPolicy")[0]
    agent.s.set_attr(policy, "enabled", 1.0)
    resource = agent.s.nodes("ThinkingBudget")[0]
    agent.s.set_attr(resource, "enabled", 1.0)
    agent.s.set_attr(resource, "remaining", float(budget))
    observation = agent.s.add_node("Observation", {"signature": [tuple(p) for p in sorted(shape)], "status": "observed"})
    request = agent.s.add_node("AnalogImageryRequest", {
        "request_id": "imagery-request", "rotation_steps": list(steps),
        "step_count": len(steps), "step_index": 0,
        "buffer_size": 0, "current_shape": [list(point) for point in sorted(shape)],
        "source_observation": str(observation), "status": "running", "cost": 0,
    })
    try:
        agent.inner.add_edge_unchecked(agent.s.nodes("Agent")[0], "has_analog_imagery_request", request, {})
    except TypeError:
        agent.inner.add_edge_unchecked(agent.s.nodes("Agent")[0], "has_analog_imagery_request", request)
    return agent, observation, request, resource


def _verification_receipt(agent, request, observation, status):
    receipt = agent.s.add_node("ImageryShapeVerification", {
        "receipt_id": f"verify:{agent.s.node(request)['attrs']['request_id']}",
        "request_id": agent.s.node(request)["attrs"]["request_id"],
        "source_observation": str(observation), "verification_status": status,
    })
    agent.inner.add_edge_unchecked(request, "has_shape_verification", receipt)
    return receipt


def test_generator_reproduces_committed_seed_exactly():
    before = SEED.read_bytes()
    subprocess.run([sys.executable, str(GENERATOR)], cwd=ROOT, check=True,
                   capture_output=True, text=True)
    assert SEED.read_bytes() == before


def test_budget_exhausts_unresolved():
    agent, _, request, _ = _runtime(frozenset({(0, 0), (0, 1)}), (90, 90), budget=1)
    agent.tick()
    attrs = agent.s.node(request)["attrs"]
    assert attrs["status"] == "unresolved"
    assert attrs["stop_reason"] == "budget_exhausted"
    assert attrs["grounded"] == 0


def test_shape_verified_after_rotation():
    shape = frozenset({(0, 0), (0, 1), (1, 1)})
    agent, observation, request, budget = _runtime(shape, (90,))
    agent.tick()
    attrs = agent.s.node(request)["attrs"]
    expected = rotate_ordered(sorted(shape), 90)
    assert attrs["status"] == "awaiting_verification"
    assert attrs["current_shape"] == [tuple(point) for point in expected]
    assert attrs["grounded"] == 0
    assert "shape_verified" not in attrs
    _verification_receipt(agent, request, observation, "verified")
    agent.tick()
    attrs = agent.s.node(request)["attrs"]
    assert attrs["status"] == "proposed"
    assert attrs["shape_verified"] is True
    assert attrs["grounded"] == 0
    assert attrs["buffer_status"] == "expired"
    assert agent.s.node(observation)["attrs"]["signature"] == [tuple(p) for p in sorted(shape)]
    assert agent.s.node(budget)["attrs"]["remaining"] == 3.0


def test_buffer_growth_bounded():
    shape = frozenset({(0, 0), (0, 1)})
    agent, _, request, _ = _runtime(shape, (90, 90, 90), budget=8)
    agent.tick()
    attrs = agent.s.node(request)["attrs"]
    assert attrs["status"] == "awaiting_verification"
    assert attrs["buffer_size"] == 3
    assert len(agent.s.neighbours(request, "has_imagery_witness")) == 3
    _verification_receipt(agent, request, agent.s.nodes("Observation")[0], "verified")
    agent.tick()
    assert agent.s.node(request)["attrs"]["buffer_status"] == "expired"


def test_failed_verifier_rejects_shape_proposal():
    shape = frozenset({(0, 0), (0, 1)})
    agent, observation, request, _ = _runtime(shape, (90,))
    agent.tick()
    _verification_receipt(agent, request, observation, "mismatch")
    agent.tick()
    attrs = agent.s.node(request)["attrs"]
    assert attrs["status"] == "unresolved"
    assert attrs["stop_reason"] == "shape_verification_failed"
    assert attrs["grounded"] == 0


def test_runtime_refuses_arbitrary_increment():
    agent, _, request, _ = _runtime(frozenset({(0, 0), (0, 1)}), (45,), budget=4)
    agent.tick()
    attrs = agent.s.node(request)["attrs"]
    assert attrs["status"] == "unresolved"
    assert attrs["stop_reason"] == "unsupported_rotation_step"
    assert attrs["grounded"] == 0
