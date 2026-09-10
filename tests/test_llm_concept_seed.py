"""Block 328000 — tests for concept-seed extraction
(`domains/llm_concept_seed.py`). The operator fit is pure numpy (always runs);
the substrate settle is gated on `substrate_rs`. Elicitation of real word
vectors needs the model and is exercised by the block-328 scripts.
"""
from __future__ import annotations

import numpy as np
import pytest

from domains import llm_concept_seed as cs


def _have_substrate():
    try:
        import substrate_rs  # noqa: F401
        return True
    except Exception:
        return False


_need_substrate = pytest.mark.skipif(
    not _have_substrate(),
    reason="substrate_rs absent (run with PYTHONPATH=runners/dsl/python)")

SEEDS = ["seeds/can_native_reimplementation.json"]


def test_fit_opposite_operator_shape_and_symmetry():
    # a toy antonym geometry: opposites are negations, so W ~ -I recovers them.
    rng = np.random.default_rng(0)
    d = 16
    families = {}
    pairs = []
    for i in range(6):
        v = rng.standard_normal(d).astype(np.float32)
        families["p%d" % i] = v
        families["n%d" % i] = -v          # its opposite is the negation
        pairs.append(("p%d" % i, "n%d" % i))
    W = cs.fit_opposite_operator(families, pairs, ridge=1e-3)
    assert W.shape == (d, d)
    # W should map a vector toward its opposite (negative cosine with itself)
    v = families["p0"]
    pred = W @ v
    cos = float(pred @ (-v) / (np.linalg.norm(pred) * np.linalg.norm(v) + 1e-9))
    assert cos > 0.5                      # points toward the negation (opposite)


def test_apply_operator_retrieve_picks_opposite_on_toy():
    rng = np.random.default_rng(1)
    d = 16
    vecs = {}
    pairs = []
    words = []
    for i in range(6):
        v = rng.standard_normal(d).astype(np.float32)
        vecs["p%d" % i] = v
        vecs["n%d" % i] = -v
        pairs.append(("p%d" % i, "n%d" % i))
        words += ["p%d" % i, "n%d" % i]
    W = cs.fit_opposite_operator(vecs, pairs, ridge=1e-3)
    # on this clean toy, the operator retrieves the true opposite
    assert cs.apply_operator_retrieve(W, vecs, "p0", words) == "n0"


@_need_substrate
def test_opposite_settle_negative_coupling_gives_opposite():
    from substrate_rs import _native
    s = _native.Substrate()
    st = cs.opposite_settle(s, SEEDS, "hot", "cold", coupling=-2.0, clamp_a=1.0)
    assert st == -1.0                     # clamp +1 -> partner settles opposite
    s2 = _native.Substrate()
    st2 = cs.opposite_settle(s2, SEEDS, "hot", "cold", coupling=-2.0,
                             clamp_a=-1.0)
    assert st2 == 1.0                     # clamp -1 -> partner settles opposite


@_need_substrate
def test_positive_coupling_control_gives_same_not_opposite():
    # the shuffled-sign control: a POSITIVE coupling settles the partner to the
    # SAME state — the wrong answer for "opposite", confirming the sign carries
    # the concept's dynamics.
    from substrate_rs import _native
    s = _native.Substrate()
    st = cs.opposite_settle(s, SEEDS, "a", "b", coupling=+2.0, clamp_a=1.0)
    assert st == 1.0                      # same-sign, not opposite
