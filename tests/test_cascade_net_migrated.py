"""Cascade net — the new net type: a residual cascade of local-delta blocks.

Gates domains/cascade_net.py + the Rust cascade ops. The headline: DEPTH buys
capacity inside the constraint — a stack of deliberately-weak blocks, each
learning (local delta rule, no backprop) the SURPRISE the previous block left,
reaches lower error than one block on a target one block underfits. This is
the "stacked delta-rule net" the literature sweep flagged as unclaimed.
"""
from __future__ import annotations

import numpy as np
from substrate_rs import _native
from domains.cascade_net import build, forward, train_step

_NODE = ("CascadeNet", "NetworkAssemblage", "AssemblageStep", "WeightTensor")
_EDGE = ("has_block", "has_step", "has_weight")


def _fresh():
    s = _native.Substrate()
    for a in _NODE:
        for b in _NODE:
            for et in _EDGE:
                s.add_production({"src": {"type": a, "var": "s"}, "edge_type": et,
                                  "tgt": {"type": b, "var": "t"}, "where": None,
                                  "weight": {"type": "Lit", "value": 1.0}, "provenance": "t"})
    return s


def _fn(x):
    # a wiggly target a width-8 random-feature block underfits
    return float(np.sin(4.0 * x))


def _train_eval(n_blocks, hidden=8, epochs=300, seed=0):
    s = _fresh()
    c = build(s, "c", n_blocks=n_blocks, in_dim=1, out_dim=1, hidden=hidden, seed=seed)
    xs = [i / 25.0 for i in range(-25, 26)]
    test = [-0.83, -0.42, -0.05, 0.31, 0.67, 0.92]
    # Low base eta: each block does a small, stable NLMS step against a moving
    # residual, so the boosting compounds signal not noise.
    epoch_surprise = 0.0
    for epoch in range(epochs):
        eta = 0.1 / (1.0 + 0.02 * epoch)
        surprises = [train_step(s, c, [x], [_fn(x)], eta) for x in xs]
        epoch_surprise = sum(surprises) / len(surprises)  # mean Σr² over the epoch
    err = max(abs(forward(s, c, [x])[0] - _fn(x)) for x in test)
    return err, epoch_surprise


def test_cascade_forward_of_untrained_is_zero():
    s = _fresh()
    c = build(s, "c", n_blocks=3, in_dim=1, out_dim=1, hidden=8)
    assert abs(forward(s, c, [0.4])[0]) < 1e-9, "zero-readout blocks sum to 0"


def test_cascade_depth_beats_single_block():
    """A stack of weak blocks, each learning the previous block's residual by
    a local delta rule (no backprop), reaches lower error than one block on a
    target one block underfits. Depth-by-residual-refinement adds capacity,
    inside the local/online/no-backprop constraint."""
    e1, _ = _train_eval(n_blocks=1)
    e8, _ = _train_eval(n_blocks=8)
    assert e8 < e1, f"8-block cascade ({e8:.3f}) should beat 1 block ({e1:.3f})"
    assert e8 < 0.7 * e1, f"depth should meaningfully reduce error: {e1:.3f} -> {e8:.3f}"


def test_cascade_surprise_falls_with_depth():
    """The residual the whole cascade can't explain (Σr²) falls as blocks are
    added — each block strips out the surprise the previous left."""
    _, s1 = _train_eval(n_blocks=1)
    _, s6 = _train_eval(n_blocks=6)
    assert s6 < s1, f"deeper cascade leaves less surprise: {s1:.4f} -> {s6:.4f}"
