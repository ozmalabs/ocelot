"""Cascade net — the new net type: a residual cascade of local-delta blocks.

Each block is a weak self-training net (fixed random features + a local NLMS
delta-rule readout — the same primitive as net_collapse). The cascade stacks
them so each block learns the SURPRISE the previous block could not explain:
`residual ← target − Σ(prior blocks)`, passed up the stack. Depth by
successive refinement of the residual — online gradient boosting with local-
delta readouts, no backprop, no external optimizer, one update per
observation.

This is the "stacked delta-rule net" the 2026 literature sweep flagged as
unclaimed territory (no published work combines multi-layer depth with fully
local per-layer adaptation). It is the DEPTH complement of the composite net's
BREADTH: composite = which shape (extensive/frontier), cascade = how finely
(intensive/refinement) — the two unbounded axes.

Mechanical host I/O only: mint the structure, drive the (Rust) forward/train.
"""
from __future__ import annotations

import numpy as np


def _nid(x):
    return x.value if hasattr(x, "value") else int(x)


def mint_cascade(substrate, name):
    return substrate.add_node("CascadeNet", {"name": str(name)})


def add_block(substrate, cascade, *, order, in_dim, out_dim, hidden=8, seed=1,
              w1_scale=1.5):
    """Add one weak block: fixed random ReLU features + a ZERO readout. Kept
    deliberately small — depth, not width, is where the cascade gets its
    capacity."""
    s = substrate
    rng = np.random.default_rng(seed)
    asm = s.add_node("NetworkAssemblage",
                     {"input_dim": in_dim, "output_dim": out_dim, "order": int(order)})
    sid = s.add_node("AssemblageStep", {"order": 0, "dim_behavior": "transform"})
    s.add_edge(asm, "has_step", sid, {})
    w = {"W1": (rng.standard_normal((hidden, in_dim)) * w1_scale).tolist(),
         "b1": (rng.standard_normal(hidden) * 0.3).tolist(),
         "W2": [[0.0] * hidden for _ in range(out_dim)], "b2": [0.0] * out_dim}
    for role, dat in w.items():
        wt = s.add_node("WeightTensor", {"role": role, "data": dat})
        s.add_edge(sid, "has_weight", wt, {})
    s.add_edge(cascade, "has_block", asm, {})
    return asm


def build(substrate, name, *, n_blocks, in_dim, out_dim, hidden=8, seed=0):
    """Mint a cascade of `n_blocks` weak blocks."""
    c = mint_cascade(substrate, name)
    for k in range(n_blocks):
        add_block(substrate, c, order=k, in_dim=in_dim, out_dim=out_dim,
                  hidden=hidden, seed=seed + k + 1)
    return c


def forward(substrate, cascade, feature):
    return list(substrate.cascade_forward(_nid(cascade), [float(v) for v in feature]))


def train_step(substrate, cascade, feature, target, eta):
    """One residual-cascade collapse step; returns the final surprise Σr²."""
    return float(substrate.cascade_collapse_step(
        _nid(cascade), [float(v) for v in feature],
        [float(v) for v in target], float(eta)))
