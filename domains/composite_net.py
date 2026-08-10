"""Composite net — a net NESTED out of component shape-specialists.

The lens: a net doesn't have to be a specialist at a content DOMAIN. It runs
on SHAPE, and because shape is substrate-universal, a specialist at one shape
is a generalist over every domain that instantiates it. A CompositeNet nests
many such components (same design, different shape jurisdiction) and routes an
input to the component covering its shape — grounded shape-residual, never a
trained gate (the confidently-wrong-outside-basin failure a softmax router
has, this doesn't). No component covers the input's shape ⇒ defer to cognition.

This is the decoupled, honest form of what MoE gropes toward: components are
independent, each self-trains (via the engine's net_collapse), each is gated
by its OWN grounded shape-basin, and composition is by the substrate — not a
single end-to-end backprop with an opaque learned router.

Mechanical host I/O only: mint the graph structure, read the routed forward
back. Phase 2 (mint-on-residual growth, the worth-its-footprint admission
economy, cognition chaining components) builds on this.
"""
from __future__ import annotations

import numpy as np


def _nid(x):
    return x.value if hasattr(x, "value") else int(x)


def sig_keys(signature):
    """A signature's shape-quanta as flat keys — the routing tokens. Each
    relation tuple → 'a|b|c'. This is the shape the component is a specialist
    at; it is modality-invariant by construction (the quantizer already threw
    the content away)."""
    return ["|".join(str(x) for x in rel) for rel in signature]


def mint_composite(substrate, name):
    """Mint an empty CompositeNet node."""
    return substrate.add_node("CompositeNet", {"name": str(name)})


def add_component(substrate, composite, *, name, basin_parts, in_dim, out_dim,
                  basin_threshold=0.4, hidden=160, seed=1):
    """Add a shape-specialist component to the composite: a self-training
    ReflexNet whose jurisdiction is `basin_parts` (the shape-quanta keys it
    handles) wrapping a fresh zero-readout net. It self-trains via the engine
    (net_collapse) exactly like any reflex net."""
    s = substrate
    rng = np.random.default_rng(seed)
    asm = s.add_node("NetworkAssemblage", {"input_dim": in_dim, "output_dim": out_dim})
    sid = s.add_node("AssemblageStep", {"order": 0, "dim_behavior": "transform"})
    s.add_edge(asm, "has_step", sid, {})
    w = {"W1": (rng.standard_normal((hidden, in_dim)) * 1.2).tolist(),
         "b1": (rng.standard_normal(hidden) * 0.3).tolist(),
         "W2": [[0.0] * hidden for _ in range(out_dim)], "b2": [0.0] * out_dim}
    for role, dat in w.items():
        wt = s.add_node("WeightTensor", {"role": role, "data": dat})
        s.add_edge(sid, "has_weight", wt, {})
    rn = s.add_node("ReflexNet", {
        "name": str(name), "status": "self_training", "enabled": 0.0,
        "eta": 0.5, "converge_tol": 0.01,
        "basin_parts": [str(k) for k in basin_parts],
        "basin_threshold": float(basin_threshold)})
    s.add_edge(rn, "net_assemblage", asm, {})
    s.add_edge(composite, "has_component", rn, {})
    return rn, asm


def route(substrate, composite, feature, signature):
    """Route + evaluate: the winning shape-specialist's output, the component
    that fired (or None = deferred to cognition), and the residual fraction."""
    out, comp, resid = substrate.composite_forward(
        _nid(composite), [float(v) for v in feature], sig_keys(signature))
    return (list(out) if out else None), (None if comp < 0 else comp), resid
