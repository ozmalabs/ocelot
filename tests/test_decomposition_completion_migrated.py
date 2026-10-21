"""A2.1 completion contract and A2.2 graph-rule execution gates."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "seeds" / "decomposition_completion.json"
GENERATOR = ROOT / "scripts" / "gen_decomposition_completion_seed.py"
for path in (ROOT, ROOT / "runners" / "dsl" / "python"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
pytest.importorskip("substrate_rs")
from substrate.world_adapter import WorldAdapter


@dataclass(frozen=True)
class ChildWork:
    child_id: str
    capability_keys: frozenset[str]
    status: str
    verified: bool
    model_epoch: int
    decomposition_epoch: int


@dataclass(frozen=True)
class ParentWork:
    required_keys: frozenset[str]
    model_epoch: int
    decomposition_epoch: int
    saturation: float
    impasse_status: str = "open"
    pre_completion_saturation: float | None = None


@dataclass(frozen=True)
class CompletionAssessment:
    completed_keys: frozenset[str]
    uncovered_keys: frozenset[str]
    outstanding_child_ids: frozenset[str]
    witness: bool
    parent_saturation: float
    impasse_status: str


def assess_completion(parent: ParentWork, children: tuple[ChildWork, ...]) -> CompletionAssessment:
    """A2.1 oracle: exact required-key coverage and current verified child work."""
    required = parent.required_keys
    eligible = tuple(
        child for child in children
        if child.status == "completed"
        and child.verified
        and child.model_epoch == parent.model_epoch
        and child.decomposition_epoch == parent.decomposition_epoch
    )
    completed = frozenset().union(*(child.capability_keys & required for child in eligible))
    uncovered = required - completed
    outstanding = frozenset(
        child.child_id for child in children
        if child.capability_keys & required and child not in eligible
    )
    witness = bool(required) and completed == required
    if witness:
        saturation = 1.0
    elif (parent.impasse_status == "resolved"
          and parent.pre_completion_saturation is not None):
        saturation = parent.pre_completion_saturation
    else:
        saturation = parent.saturation
    if witness and not outstanding:
        impasse_status = "resolved"
    elif not witness and parent.impasse_status == "resolved":
        impasse_status = "open"
    else:
        impasse_status = parent.impasse_status
    return CompletionAssessment(completed, uncovered, outstanding, witness,
                                saturation, impasse_status)


def _parent(*, required=("alpha", "beta"), model_epoch=4,
            decomposition_epoch=7, saturation=0.35, impasse_status="open",
            pre_completion_saturation=None):
    return ParentWork(frozenset(required), model_epoch, decomposition_epoch,
                      saturation, impasse_status, pre_completion_saturation)


def _child(child_id, keys, *, status="completed", verified=True,
           model_epoch=4, decomposition_epoch=7):
    return ChildWork(child_id, frozenset(keys), status, verified,
                     model_epoch, decomposition_epoch)


def test_partial_children_do_not_complete():
    result = assess_completion(_parent(), (_child("alpha-work", ("alpha",)),))
    assert result.witness is False
    assert result.completed_keys == {"alpha"}
    assert result.uncovered_keys == {"beta"}
    assert result.parent_saturation == 0.35
    assert result.impasse_status == "open"


def test_all_required_keys_complete_parent():
    result = assess_completion(_parent(), (
        _child("alpha-work", ("alpha",)), _child("beta-work", ("beta",)),
    ))
    assert result.witness is True
    assert result.completed_keys == {"alpha", "beta"}
    assert result.uncovered_keys == set()
    assert result.outstanding_child_ids == set()
    assert result.parent_saturation == 1.0
    assert result.impasse_status == "resolved"


def test_stale_child_reopens():
    parent = _parent(impasse_status="resolved", saturation=1.0,
                     pre_completion_saturation=0.35)
    result = assess_completion(parent, (
        _child("alpha-work", ("alpha",), model_epoch=3),
        _child("beta-work", ("beta",)),
    ))
    assert result.witness is False
    assert result.uncovered_keys == {"alpha"}
    assert result.outstanding_child_ids == {"alpha-work"}
    assert result.parent_saturation == 0.35
    assert result.impasse_status == "open"
    # A2.2 must invalidate the persisted completion witness and restore the
    # impasse when its model/decomposition epoch no longer matches.
    assert result.witness is False


def test_empty_children_never_complete():
    result = assess_completion(_parent(), ())
    assert result.witness is False
    assert result.completed_keys == set()
    assert result.uncovered_keys == {"alpha", "beta"}
    assert result.impasse_status == "open"
    assert assess_completion(_parent(required=()), ()).witness is False


def test_overlapping_children_use_required_key_union_not_child_count():
    result = assess_completion(_parent(), (
        _child("first", ("alpha", "beta")),
        _child("overlap", ("alpha",)),
    ))
    assert result.completed_keys == {"alpha", "beta"}
    assert result.witness is True
    assert result.impasse_status == "resolved"


def test_pending_overlapping_required_child_blocks_impasse_resolution():
    result = assess_completion(_parent(), (
        _child("complete", ("alpha", "beta")),
        _child("still-running", ("alpha",), status="pending", verified=False),
    ))
    assert result.witness is True
    assert result.parent_saturation == 1.0
    assert result.outstanding_child_ids == {"still-running"}
    assert result.impasse_status == "open"


def test_unverified_completed_child_is_not_completion_evidence():
    result = assess_completion(_parent(), (
        _child("alpha-work", ("alpha",)),
        _child("beta-work", ("beta",), verified=False),
    ))
    assert result.witness is False
    assert result.uncovered_keys == {"beta"}
    assert result.outstanding_child_ids == {"beta-work"}


def test_out_of_scope_child_keys_do_not_cover_required_keys():
    result = assess_completion(_parent(), (
        _child("unrelated", ("gamma",)),
        _child("alpha-work", ("alpha",)),
    ))
    assert result.witness is False
    assert result.completed_keys == {"alpha"}
    assert result.uncovered_keys == {"beta"}


def test_child_mean_saturation_is_not_completion_evidence():
    parent = _parent(saturation=0.9)
    result = assess_completion(parent, (
        _child("alpha-work", ("alpha",)),
    ))
    assert result.witness is False
    assert result.parent_saturation == 0.9


def _edge(agent, source, edge_type, target):
    try:
        agent.inner.add_edge_unchecked(source, edge_type, target, {})
    except TypeError:
        agent.inner.add_edge_unchecked(source, edge_type, target)


def _runtime(*, model_epoch=4, decomposition_epoch=7, enabled=True):
    agent = WorldAdapter(seeds=["decomposition_completion"])
    policies = agent.s.nodes("DecompositionCompletionPolicy")
    assert len(policies) == 1
    if enabled:
        agent.s.set_attr(policies[0], "enabled", 1.0)
    axis = agent.s.add_node("CapabilityAxis", {
        "saturation": 0.35, "model_epoch": model_epoch,
        "decomposition_epoch": decomposition_epoch,
    })
    impasse = agent.s.add_node("Impasse", {
        "kind": "escalation", "resolved": False,
    })
    _edge(agent, impasse, "needs_decomposition", axis)
    _edge(agent, impasse, "about_axis", axis)
    keys = {}
    for name in ("alpha", "beta"):
        key = agent.s.add_node("CapKey", {"name": name})
        _edge(agent, axis, "requires_key", key)
        keys[name] = key
    return agent, impasse, axis, keys


def _runtime_child(agent, axis, key, name, **attrs):
    child = agent.s.add_node("CapabilityAxis", {
        "completion_status": "completed", "completion_verified": 1,
        "model_epoch": 4, "decomposition_epoch": 7, **attrs,
    })
    _edge(agent, axis, "decomposes_into", child)
    _edge(agent, child, "requires_key", key)
    return child


def test_generator_reproduces_committed_seed_exactly():
    before = SEED.read_bytes()
    subprocess.run([sys.executable, str(GENERATOR)], cwd=ROOT, check=True,
                   capture_output=True, text=True)
    assert SEED.read_bytes() == before


def test_parent_impasse_settles_only_with_witness():
    agent, impasse, axis, keys = _runtime()
    _runtime_child(agent, axis, keys["alpha"], "alpha")
    agent.tick()
    assert agent.s.node(impasse)["attrs"].get("resolved") is False
    assert agent.s.node(axis)["attrs"]["saturation"] == pytest.approx(0.35)
    _runtime_child(agent, axis, keys["beta"], "beta")
    agent.tick()
    assert agent.s.node(impasse)["attrs"]["resolved"] is True
    assert agent.s.node(impasse)["attrs"]["completion_witness"] == 1
    assert agent.s.node(axis)["attrs"]["saturation"] == pytest.approx(1.0)


def test_completion_idempotent():
    agent, impasse, axis, keys = _runtime()
    _runtime_child(agent, axis, keys["alpha"], "alpha")
    _runtime_child(agent, axis, keys["beta"], "beta")
    assert agent.tick() > 0
    attrs = dict(agent.s.node(impasse)["attrs"])
    assert agent.tick() == 0
    assert agent.s.node(impasse)["attrs"] == attrs


@pytest.mark.parametrize("changed_epoch", ["model_epoch", "decomposition_epoch"])
def test_stale_epoch_invalidates_witness_and_reopens_parent(changed_epoch):
    agent, impasse, axis, keys = _runtime()
    _runtime_child(agent, axis, keys["alpha"], "alpha")
    _runtime_child(agent, axis, keys["beta"], "beta")
    agent.tick()
    agent.s.set_attr(axis, changed_epoch, 8)
    agent.tick()
    attrs = agent.s.node(impasse)["attrs"]
    assert attrs["completion_witness"] == 0
    assert attrs["resolved"] is False
    assert agent.s.node(axis)["attrs"]["saturation"] == pytest.approx(0.35)


def test_changed_required_coverage_invalidates_witness():
    agent, impasse, axis, keys = _runtime()
    alpha = _runtime_child(agent, axis, keys["alpha"], "alpha")
    _runtime_child(agent, axis, keys["beta"], "beta")
    agent.tick()
    agent.s.set_attr(alpha, "completion_verified", 0)
    agent.tick()
    assert agent.s.node(impasse)["attrs"]["completion_witness"] == 0
    assert agent.s.node(impasse)["attrs"]["resolved"] is False
    assert agent.s.node(axis)["attrs"]["saturation"] == pytest.approx(0.35)


def test_pending_overlapping_child_blocks_impasse_resolution():
    agent, impasse, axis, keys = _runtime()
    _runtime_child(agent, axis, keys["alpha"], "alpha")
    _runtime_child(agent, axis, keys["beta"], "beta")
    pending = agent.s.add_node("CapabilityAxis", {
        "completion_status": "pending", "completion_verified": 0,
        "model_epoch": 4, "decomposition_epoch": 7,
    })
    _edge(agent, axis, "decomposes_into", pending)
    _edge(agent, pending, "requires_key", keys["alpha"])
    agent.tick()
    assert agent.s.node(impasse)["attrs"].get("resolved") is False

