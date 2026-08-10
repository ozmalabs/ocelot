"""Composite net — a net nested out of component SHAPE-specialists.

Gates domains/composite_net.py + the Rust composite_forward op: a CompositeNet
routes an input to the component covering its SHAPE (grounded shape-residual,
not a trained gate), evaluates that component, and defers when no component
covers the shape. The headline is SHAPE-TRANSFER: a component whose
jurisdiction is a shape fires for that shape regardless of content domain — a
specialist at a shape is a generalist.
"""
from __future__ import annotations

import json
import os

import numpy as np
import pytest
from substrate_rs import _native
from domains.composite_net import (
    mint_composite, add_component, route, sig_keys,
)

_SEED = os.path.join(os.path.dirname(__file__), "..", "seeds", "reflex_net.json")

_NODE = ("CompositeNet", "ReflexNet", "NetworkAssemblage", "AssemblageStep",
         "WeightTensor", "ReflexObservation")
_EDGE = ("has_component", "net_assemblage", "has_step", "has_weight", "observes")


def _fresh():
    s = _native.Substrate()
    for a in _NODE:
        for b in _NODE:
            for et in _EDGE:
                s.add_production({"src": {"type": a, "var": "s"}, "edge_type": et,
                                  "tgt": {"type": b, "var": "t"}, "where": None,
                                  "weight": {"type": "Lit", "value": 1.0}, "provenance": "t"})
    rule = next(r for r in json.load(open(_SEED))["rules"]
                if r["name"] == "reflex_net_self_train_step")
    s.add_rule(rule)
    return s


def test_composite_routes_by_shape():
    """Two components with different shape jurisdictions; an input routes to
    the component covering ITS shape."""
    s = _fresh()
    comp = mint_composite(s, "c")
    fold, _ = add_component(s, comp, name="fold", basin_parts=["fold|1", "fold|2"],
                            in_dim=2, out_dim=1, seed=1)
    step, _ = add_component(s, comp, name="step", basin_parts=["step|0", "step|3"],
                            in_dim=2, out_dim=1, seed=2)

    _, c_fold, _ = route(s, comp, [0.3, 0.7], [["fold", "1"], ["fold", "2"]])
    _, c_step, _ = route(s, comp, [0.3, 0.7], [["step", "0"], ["step", "3"]])
    assert c_fold == fold.value, "fold-shaped input routes to the fold specialist"
    assert c_step == step.value, "step-shaped input routes to the step specialist"
    assert c_fold != c_step


def test_shape_transfer_specialist_is_generalist():
    """THE HEADLINE: a component whose jurisdiction is a SHAPE fires for that
    shape REGARDLESS of content domain — two inputs from different 'modalities'
    (different feature vectors) but the SAME shape signature route to the SAME
    component. The shape routes; the content only parametrizes the output."""
    s = _fresh()
    comp = mint_composite(s, "c")
    fold, _ = add_component(s, comp, name="fold", basin_parts=["fold|1", "fold|2"],
                            in_dim=2, out_dim=1, seed=1)

    # Same shape, two very different content vectors ("ink" vs "numbers").
    ink_out, c1, r1 = route(s, comp, [0.1, 0.9], [["fold", "1"], ["fold", "2"]])
    num_out, c2, r2 = route(s, comp, [0.8, 0.2], [["fold", "1"], ["fold", "2"]])

    assert c1 == fold.value and c2 == fold.value, \
        "the shape specialist fires for its shape in EITHER domain"
    assert r1 == 0.0 and r2 == 0.0, "both fully in the shape basin"
    # The shape routed both; the content parametrized different outputs.
    assert ink_out is not None and num_out is not None


def test_composite_defers_when_no_component_covers_shape():
    """An input whose shape-quanta are in NO component's jurisdiction is
    deferred (route returns None) — the seam goes to cognition."""
    s = _fresh()
    comp = mint_composite(s, "c")
    add_component(s, comp, name="fold", basin_parts=["fold|1", "fold|2"],
                  in_dim=2, out_dim=1, seed=1)
    out, chosen, resid = route(s, comp, [0.5, 0.5], [["zzznovel", "9"], ["qqq", "7"]])
    assert out is None and chosen is None, "unknown shape defers to cognition"
    assert resid == pytest.approx(1.0)


def test_composite_serves_winning_components_trained_output():
    """Each component self-trains independently (via the engine's net_collapse
    loop); the composite routes to the right one and serves ITS trained
    output. Route + train are one system."""
    s = _fresh()
    comp = mint_composite(s, "c")
    # A component whose within-shape parametrization is: output = mean(input).
    rn, asm = add_component(s, comp, name="avg", basin_parts=["avg|1"],
                            in_dim=2, out_dim=1, seed=1)
    # Self-train the component to compute mean(x) via engine collapse.
    rng = np.random.default_rng(0)
    obs = []
    for _ in range(40):
        x = rng.random(2)
        o = s.add_node("ReflexObservation",
                       {"status": "pending", "input_vec": x.tolist(),
                        "target": [float(x.mean())]})
        s.add_edge(o, "observes", rn, {})
        obs.append(o)
    for epoch in range(120):
        s.set_attr(rn, "eta", 0.5 / (1.0 + 0.03 * epoch))
        for o in obs:
            s.set_attr(o, "status", "pending")
        s.run_rules()

    out, chosen, _ = route(s, comp, [0.2, 0.8], [["avg", "1"]])
    assert chosen == rn.value, "routed to the avg specialist"
    assert abs(out[0] - 0.5) < 0.06, f"served the trained output ~mean, got {out}"


def test_sig_keys_is_modality_invariant():
    """The routing token IS the shape — the same relation-signature yields the
    same keys no matter what raw signal produced it."""
    assert sig_keys([["fold", "1"], ["stop", "x"]]) == ["fold|1", "stop|x"]
