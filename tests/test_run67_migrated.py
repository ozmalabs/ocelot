"""test_run67_migrated.py -- unit gates for RUN 67 (discriminative cursive reading).

Gates:
  * reuse run 66's learned model READ-ONLY (checkpoint md5 unchanged);
  * writer-adaptive picks the BEST-not-medoid allograph on a synthetic;
  * letter-weighted (Fisher) distance UP-WEIGHTS the discriminative region;
  * trie-beam NARROWS the candidate set + collapses to a lexicon word on an ambiguous synthetic;
  * seed guard: seeds/stroke_shapes.json md5 UNCHANGED.
"""
from __future__ import annotations

import hashlib
import os

import numpy as np
import pytest

import scripts.jabberwock_cursive_read_run67 as r67

CANON_N = r67.CANON_N
REAL_SEED = r67.STROKE_SHAPES_SEED
RUN66_CKPT = r67.RUN66_CKPT


def _md5(p):
    with open(p, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


@pytest.fixture(scope="module")
def native():
    import substrate_rs as srs
    return srs.Substrate()._inner


# --------------------------------------------------------------------------------------------- #
def test_reuse_run66_model_readonly():
    """load_model reuses run 66's learned canons; run66 checkpoints untouched (READ-ONLY)."""
    lett = os.path.join(RUN66_CKPT, "letters.json")
    before = _md5(lett)
    model = r67.load_model()
    assert model["canons"], "no run66 canons loaded"
    n_forms = sum(len(v) for v in model["canons"].values())
    assert n_forms > 20, f"too few reused allographs: {n_forms}"
    # canon frame shape.
    some = next(v for v in model["canons"].values() if v)
    assert some[0].shape == (CANON_N, 2)
    assert _md5(lett) == before, "run66 letters.json was modified -- must be READ-ONLY"


def test_fisher_weights_finite_and_discriminative():
    """Fisher weights are finite, mean-normalized to ~1, and NOT all-equal (they DO find separating
    dims -- the run-57 faculty is doing work over the aligned letter frame)."""
    model = r67.load_model()
    fw = model["fisher_w"]
    assert fw.shape == (CANON_N, 2)
    assert np.isfinite(fw).all()
    assert abs(fw.mean() - 1.0) < 1e-6
    assert fw.max() > 1.5 * fw.min(), "Fisher weights are flat -- no discriminative structure found"


def test_writer_adaptive_best_not_medoid(native):
    """WRITER-ADAPTIVE takes the BEST allograph to the query span; MEDOID uses allograph 0. On a
    synthetic class with two DISTINCT allographs where the query matches allograph 1 (not the
    medoid 0), adaptive cost << medoid cost."""
    # two distinct canonical forms (a line vs an arc), CANON_N points.
    t = np.linspace(0, 1, CANON_N)
    formA = np.stack([t, np.zeros_like(t)], 1)                     # straight (medoid, allo 0).
    formB = np.stack([t, 0.5 * np.sin(np.pi * t)], 1)              # arced   (allo 1).
    model = {
        "canons": {10: [formA, formB]},                            # class 'a' has both allographs.
        "sqrt_uniform": np.ones((CANON_N, 2)),
        "sqrt_fisher": np.ones((CANON_N, 2)),
    }
    # query == allograph 1 (the writer's actual style is the arc, not the medoid line).
    q = formB.copy()
    vecs = r67.letter_cost_vectors(native, q, model)
    li = 0  # class 10 -> letter index 0.
    medoid_cost = vecs["medoid_uniform"][li]
    adaptive_cost = vecs["adaptive_uniform"][li]
    assert adaptive_cost < medoid_cost - 1e-6, (adaptive_cost, medoid_cost)
    assert adaptive_cost < 1e-3, f"adaptive should ~match allo1 exactly: {adaptive_cost}"


def test_letter_weighted_upweights_discriminative_region(native):
    """The LETTER-WEIGHTED path (native weighted DtwTo) up-weights the discriminative region: with
    weights concentrated on the second half of the stroke, a candidate that differs THERE scores
    far worse than one that differs only in the (down-weighted) first half."""
    t = np.linspace(0, 1, CANON_N)
    base = np.stack([t, np.zeros_like(t)], 1)
    half = CANON_N // 2
    # weights: ~0 on first half, high on second half (the "separating" region).
    w = np.ones((CANON_N, 2))
    w[:half] = 0.05
    w[half:] = 1.95
    sqrt_w = np.sqrt(w)
    diff_early = base.copy(); diff_early[:half, 1] += 0.3          # differs in down-weighted region.
    diff_late = base.copy(); diff_late[half:, 1] += 0.3           # differs in up-weighted region.
    d_early = r67.weighted_dtw(native, base, diff_early, sqrt_w)
    d_late = r67.weighted_dtw(native, base, diff_late, sqrt_w)
    assert d_late > d_early, (d_late, d_early)


def test_trie_beam_narrows_and_collapses():
    """The trie-beam NARROWS the next-letter set to trie children and COLLAPSES to a lexicon word,
    even when the raw per-letter argmax would pick a non-word. Lexicon {cat,car,dog}; at position 0
    a spurious cheap 'z' (not a trie child) is EXCLUDED; the beam picks a real word."""
    trie = r67.build_trie(["cat", "car", "dog"])
    L = 3

    def cost_row(cheap_letter, other=5.0):
        row = [other] * 26
        row[ord(cheap_letter) - ord("a")] = 0.0
        return row

    # raw per-letter argmax would read 'z','a','r' (z is cheapest at pos 0) -- NOT a word.
    C = [cost_row("z"), cost_row("a"), cost_row("r")]
    # sanity: raw argmax is a non-word.
    assert r67.per_letter_argmax(C, L) == "zar"
    pred, trace = r67.trie_beam(trie, C, L)
    assert pred in {"cat", "car", "dog"}, pred
    assert pred == "car", pred                                     # trie forces a word; 'r' at pos 2.
    # narrowing: position 0 considered only trie roots {c,d}, NOT 'z' (26 -> few).
    assert trace[0] == {"c", "d"}, trace[0]
    assert "z" not in trace[0]


def test_seed_guard_md5_unchanged(native):
    """Running the run-67 comparison machinery leaves the REAL boot seed md5 UNCHANGED."""
    before = _md5(REAL_SEED)
    model = r67.load_model()
    q = np.stack([np.linspace(0, 1, CANON_N), np.zeros(CANON_N)], 1)
    r67.letter_cost_vectors(native, q, model)
    assert _md5(REAL_SEED) == before, "seeds/stroke_shapes.json md5 changed!"
