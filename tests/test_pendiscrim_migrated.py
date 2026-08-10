"""RUN 58 unit gates -- THE DISCRIMINATION FACULTY ON PEN DATA. Pure statistics + mechanical
adapter checks over the DigiLeTs multi-stroke subset; NO seed writes, NO agent decisions. Every
test asserts a property of the run-58 falsifier machinery (reusing run 57's discrimination.py,
run 48's DigiLeTs loader, and run 50's relational_variation) so the STAGE-1 cheap falsifier that
DECIDES the whole run is exercised before it is trusted.
"""
from __future__ import annotations

import hashlib
import os
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

from domains import discrimination as disc
from domains import pen_world as pw
import scripts.jabberwock_omniglot_run58_pendiscrim as r58

STROKE_SHAPES_SEED = os.path.join(ROOT, "seeds", "stroke_shapes.json")
_HAS_DIGILETS = os.path.isdir(pw.DIGILETS_RAW_DIR) and bool(pw._digilets_participant_files())


def _md5(path):
    return hashlib.md5(open(path, "rb").read()).hexdigest() if os.path.exists(path) else "MISSING"


# --------------------------------------------------------------------------------------------- #
#  (1) MULTI-STROKE FILTER -- pen-up BREAK -> >=2 valid strokes; class qualifies by fraction.
# --------------------------------------------------------------------------------------------- #
def test_valid_strokes_and_multistroke_flag():
    single = {"strokes": [np.zeros((5, 2))]}
    two = {"strokes": [np.zeros((5, 2)), np.ones((4, 2))]}
    degenerate_second = {"strokes": [np.zeros((5, 2)), np.ones((1, 2))]}  # 2nd stroke <2 pts
    assert not r58._is_multistroke(single)
    assert r58._is_multistroke(two)
    # a stroke with <2 points is not a valid stroke, so this is single-stroke -> NOT multi.
    assert not r58._is_multistroke(degenerate_second)
    assert len(r58._valid_strokes(two)) == 2
    assert len(r58._valid_strokes(degenerate_second)) == 1


def test_qualifying_classes_by_fraction():
    # class 0: 3/4 multi-stroke (>=0.5 -> qualifies); class 1: 1/4 (does not).
    samples = (
        [{"class": 0, "strokes": [np.zeros((3, 2)), np.ones((3, 2))]} for _ in range(3)]
        + [{"class": 0, "strokes": [np.zeros((3, 2))]}]
        + [{"class": 1, "strokes": [np.zeros((3, 2)), np.ones((3, 2))]}]
        + [{"class": 1, "strokes": [np.zeros((3, 2))]} for _ in range(3)]
    )
    q = r58.qualifying_classes(samples, frac=0.5)
    assert 0 in q and 1 not in q


# --------------------------------------------------------------------------------------------- #
#  (2) FISHER ON PEN RELATIONS -- slot_discriminability computes, separating > non-separating.
# --------------------------------------------------------------------------------------------- #
def test_fisher_on_pen_relations_computes_and_ranks():
    # a SEPARATING slot: class means far apart, tight within. a NON-separating slot: means equal.
    per_class = {
        "sep": {"a": [0.0, 0.1, -0.1], "b": [5.0, 5.1, 4.9], "c": [10.0, 9.9, 10.1]},
        "flat": {"a": [0.0, 5.0, 10.0], "b": [0.0, 5.0, 10.0], "c": [0.0, 5.0, 10.0]},
    }
    fish = disc.slot_discriminability(per_class)
    assert np.isfinite(fish["sep"]) and np.isfinite(fish["flat"])
    assert fish["sep"] > 1.0                     # strongly separating
    assert fish["flat"] < 0.5                     # coincident means -> ~0 between-var
    assert fish["sep"] > fish["flat"]


# --------------------------------------------------------------------------------------------- #
#  (3) JUNCTION RELATIONS DERIVE ON A REAL DIGILETS MULTI-STROKE SAMPLE.
# --------------------------------------------------------------------------------------------- #
@pytest.mark.skipif(not _HAS_DIGILETS, reason="DigiLeTs corpus not present")
def test_junction_relations_on_real_digilets_multistroke():
    samples = pw.load_digilets_samples(limit_writers=4)
    ms = [s for s in samples if r58._is_multistroke(s)]
    assert ms, "expected multi-stroke DigiLeTs instances"
    s0 = ms[0]
    strokes = r58._valid_strokes(s0)
    prof = disc.junction_profile(strokes)
    total = prof["frac_none"] + prof["frac_ee"] + prof["frac_em"] + prof["frac_mm"]
    assert abs(total - 1.0) < 1e-9              # fractions over all stroke pairs sum to 1
    for v in prof.values():
        assert 0.0 <= v <= 1.0
    # attachment_relations emit one relation per unordered stroke pair.
    rels = disc.attachment_relations(strokes)
    n = len(strokes)
    assert len(rels) == n * (n - 1) // 2


# --------------------------------------------------------------------------------------------- #
#  (4) CROSS-WRITER EPISODE CONSTRUCTION -- exemplar/query for the TRUE class are DIFFERENT writers.
# --------------------------------------------------------------------------------------------- #
@pytest.mark.skipif(not _HAS_DIGILETS, reason="DigiLeTs corpus not present")
def test_cross_writer_episode_construction():
    samples = pw.load_digilets_samples(limit_writers=12)
    ms = [s for s in samples if r58._is_multistroke(s)]
    classes = r58.qualifying_classes(samples, frac=0.5)[:6]
    idx = r58._index_by_writer_class(ms, classes)
    eps = r58._draw_episodes(idx, classes, n_episodes=30, seed=123)
    assert len(eps) > 0
    for e in eps:
        tw = e["ex_writer_true"]
        qw = e["q_writer"]
        assert tw != qw, "exemplar and query of the TRUE class must be different writers"
        assert 0 <= e["true_idx"] < len(classes)


# --------------------------------------------------------------------------------------------- #
#  (5) SEED-GUARD -- loading + composition must not touch seeds/stroke_shapes.json.
# --------------------------------------------------------------------------------------------- #
@pytest.mark.skipif(not _HAS_DIGILETS, reason="DigiLeTs corpus not present")
def test_seed_guard_unchanged_across_composition():
    import substrate_rs as srs
    from domains.character_compose import compose_character_signature
    import scripts.jabberwock_omniglot_dynamic_quantization as gate
    before = _md5(STROKE_SHAPES_SEED)
    samples = pw.load_digilets_samples(limit_writers=4)
    ms = [s for s in samples if r58._is_multistroke(s)]
    native = srs.Substrate()._inner
    sp = [(st.tolist(), "s") for st in r58._valid_strokes(ms[0])]
    comp = compose_character_signature(native, sp, turn_bins=gate.DK["turn_bins"])
    assert comp["signature"]                    # produced a signature
    after = _md5(STROKE_SHAPES_SEED)
    assert before == after, "composition must not write seeds/stroke_shapes.json"


def test_donkey_zero_in_this_test_process():
    # this test module never imports torch; the faculty is torch-free by construction.
    assert "torch" not in sys.modules
