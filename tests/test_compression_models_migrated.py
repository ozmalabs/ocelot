"""TWO COMPRESSIONS, NOT ONE — and they need different cures.

"Stress compresses aperture" turns out to name two mechanically different things,
and `STRESS_COMPRESSES_APERTURE_RESULTS.md` measured only one of them:

  A  DIMENSIONAL — a dimension you could resolve is removed. STIPULATED: something
     must supply the mask, and nothing in the substrate derives it.
  B  TEMPORAL — how far ahead you can audit shortens. DERIVED: the projection
     budget is already a represented resource.

Both raise `information_loss` and both zero `resolved`, so from the outside they
present as the same deficit. They are distinguishable in the record, and — the
part that matters — they respond to opposite interventions.

`test_the_published_inertness_result_is_specific_to_the_dimensional_model` is the
honest one: the "evidence is inert at 42x" headline is a property of A, which was
stipulated, and would have FAILED under B.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
pytest.importorskip("substrate_rs")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runners" / "dsl" / "python"))
from substrate.world_adapter import WorldAdapter  # noqa: E402

TARGET = [[0.0, 0.0], [0.0, 0.0], [0.0, 0.0]]
BOUNDS = [[1.0, 1.0], [1.0, 1.0], [1.0, 1.0]]
ESCAPING = [[0.0, 0.0], [0.2, 0.1], [0.1, 9.0]]   # escapes at t=3, in dimension 1
FULL = [[1.0, 1.0]]
BLIND_D1 = [[1.0, 0.0]]
FIELDS = ("support", "resolved", "loss", "information_loss", "retained_width")


def _probe(mask, budget):
    a = WorldAdapter(seeds=())
    g = a.s
    ep = g.add_node("Episode", {"future_manifold_target": TARGET,
                                "future_manifold_bounds": BOUNDS})
    attrs = {"future_manifold_projection_budget": float(budget),
             "future_manifold_physical_horizon": 3.0}
    if mask is not None:
        attrs["future_manifold_resolved_dims"] = mask
    pol = g.add_node("ManifoldPolicy", attrs)
    cand = g.add_node("Candidate", {"future_manifold_values": ESCAPING})
    term = lambda f: {"type": "FutureManifoldProjection",
                      "episode": {"type": "Var", "name": "e"},
                      "policy": {"type": "Var", "name": "p"},
                      "source": {"type": "Var", "name": "c"}, "field": f}
    env = {"e": ep, "p": pol, "c": cand}
    return {f: a.inner.evaluate(term(f), env) for f in FIELDS}


def test_a_healthy_observer_sees_the_escape():
    """Control. Both deficits below are departures from this."""
    r = _probe(FULL, 8)
    assert r["loss"] == 1.0 and r["information_loss"] == 0.0
    assert r["resolved"] == 1.0 and r["retained_width"] == 1.0


def test_both_compressions_present_as_the_same_deficit():
    """From outside they are one thing: unresolved, nothing seen, information
    unestablished. This is why they were conflated in the first place."""
    for r in (_probe(BLIND_D1, 8), _probe(FULL, 1)):
        assert r["support"] == 1.0, "a compression falsified well-posedness"
        assert r["resolved"] == 0.0
        assert r["loss"] == 0.0
        assert r["information_loss"] > 0.0


def test_retained_width_DISCRIMINATES_them():
    """The record separates them without any intervention.

    Dimensional compression blinds one dimension and leaves the others genuinely
    established. Temporal truncation establishes NOTHING, because retention over
    the requested horizon is unknowable once any tick in it went unaudited."""
    assert _probe(BLIND_D1, 8)["retained_width"] == 1.0, (
        "dimensional compression lost a dimension it should still have retained")
    assert _probe(FULL, 1)["retained_width"] == 0.0, (
        "a truncated audit claimed retention over ticks it never reached")


def test_temporal_compression_is_GRADED_by_the_resource():
    """A second discriminator, and the reason B is the derivable model: its
    deficit is a function of a represented resource, so it moves when the
    resource moves. A's does not."""
    graded = [_probe(FULL, b)["information_loss"] for b in (1, 2, 8)]
    assert graded == sorted(graded, reverse=True) and graded[0] > graded[-1], graded
    flat = [_probe(BLIND_D1, b)["information_loss"] for b in (8, 16, 64)]
    assert len(set(flat)) == 1, f"dimensional loss varied with budget: {flat}"


def test_the_published_inertness_result_is_specific_to_the_dimensional_model():
    """THE HONEST TEST.

    `STRESS_COMPRESSES_APERTURE_RESULTS.md` reports that evidence at 42x the
    horizon does not move a compressed agent, and treats that as a property of
    stress. It is a property of the DIMENSIONAL model, which that rung stipulated.
    Under the TEMPORAL model — the one the substrate can actually derive, since
    the budget is a represented resource — the same gate recovers completely.

    Both halves are asserted here so the conditionality cannot be lost."""
    assert _probe(BLIND_D1, 64)["resolved"] == 0.0, (
        "dimensional compression became recoverable — the published result's "
        "mechanism claim would need retracting")
    recovered = _probe(FULL, 8)
    assert recovered["resolved"] == 1.0 and recovered["loss"] == 1.0, (
        "temporal compression did NOT recover with budget — then the two models "
        "are not distinguishable by intervention after all")
