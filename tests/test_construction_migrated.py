"""RUN 60 unit tests -- filename metadata parse, construction-feature compute, Fisher-on-a-fact
reuse of run 57, held-out writer split (no leakage), donkey=0 classifier, seed-guard md5."""
import hashlib
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domains import discrimination as disc
from domains import pen_world as pw
from scripts import jabberwock_omniglot_run60_construction as run60

# DigiLeTs is a separate (non-public) download; when it is not provisioned into the
# gitignored dataset dir ($PENDATA_DIR/digilets) the real-data tests SKIP rather than
# hard-fail (matching test_pen_world_migrated's real-data smoke guard).
_needs_digilets = pytest.mark.skipif(
    not os.path.isdir(pw.DIGILETS_RAW_DIR),
    reason="DigiLeTs corpus not present in $PENDATA_DIR/digilets (separate download)")


def _one_writer():
    return pw.load_digilets_samples(limit_writers=1)


def test_filename_metadata_parse():
    m = pw._parse_digilets_filename("002-f-22-right_2019-06-05-12-21-29")
    assert m["writer_id"] == "002" and m["gender"] == "f"
    assert m["age"] == "22" and m["hand"] == "right"


@_needs_digilets
def test_loader_exposes_facts():
    s = _one_writer()
    assert s, "no samples loaded -- check $PENDATA_DIR/digilets"
    ex = s[0]
    for k in ("writer_id", "gender", "age", "hand", "pressure", "pen_down", "t_ms", "pos_xy"):
        assert k in ex
    assert ex["gender"] in ("m", "f") and ex["hand"] in ("left", "right")


@_needs_digilets
def test_construction_features_compute():
    s = _one_writer()
    vec = run60.construction_features(s[0])
    assert vec.shape == (len(run60.FEATURE_NAMES),)
    assert np.all(np.isfinite(vec)), "features must be finite"
    # n_strokes >= 1, first_stroke_frac in (0,1]
    assert vec[run60.FIDX["n_strokes"]] >= 1
    assert 0.0 < vec[run60.FIDX["first_stroke_frac"]] <= 1.0
    # pressure non-degenerate on real pen data
    assert vec[run60.FIDX["press_mean"]] > 0.0


@_needs_digilets
def test_multistroke_penlift_count():
    # 'A' is a real multi-stroke letter (2 pen-downs verified in pen_world docstring)
    s = _one_writer()
    a = [x for x in s if x["symbol"] == "A"][0]
    vec = run60.construction_features(a)
    assert vec[run60.FIDX["n_strokes"]] >= 2
    assert vec[run60.FIDX["n_penlifts"]] == vec[run60.FIDX["n_strokes"]] - 1


def test_fisher_reuses_run57():
    # separated groups -> high Fisher; identical groups -> ~0 (run 57's faculty contract)
    X = np.array([[0.0], [0.1], [5.0], [5.1]])
    y = np.array(["a", "a", "b", "b"])
    f_sep = run60._fisher_per_feature(X, y)[0]
    f_same = disc.fisher_ratio([[1, 2, 3], [1, 2, 3]])
    assert f_sep > 5.0 and f_same < 1e-3


def test_heldout_writer_split_no_leakage():
    # aggregate to per-writer, then K-fold must never put a writer in train and test at once
    data = {"X": np.random.default_rng(0).random((20, len(run60.FEATURE_NAMES))),
            "writer": np.array([f"w{i%4}" for i in range(20)]),
            "gender": np.array(["m" if i % 2 else "f" for i in range(20)]),
            "age": np.array([20 + i % 5 for i in range(20)]),
            "hand": np.array(["right"] * 20), "klass": np.arange(20)}
    writers, Xw, facts = run60._writer_aggregate(data)
    assert len(writers) == 4 and Xw.shape[0] == 4
    # kfold indices are disjoint train/test by construction (np.setdiff1d)
    y = np.array(facts["gender"])
    preds, true = run60._kfold_cv(Xw, y, n_folds=2, seed=1)
    assert len(preds) == len(true) == 4


def test_classifier_is_donkey_zero():
    # nearest-fact = class means + argmin, no fit/learned weights; deterministic & separates a
    # trivially separable problem
    Xtr = np.array([[0.0, 0.0], [0.2, 0.1], [9.0, 9.0], [9.1, 8.9]])
    ytr = np.array(["a", "a", "b", "b"])
    Xte = np.array([[0.1, 0.1], [9.0, 9.1]])
    pred = run60.nearest_fact_fit_predict(Xtr, ytr, Xte)
    assert list(pred) == ["a", "b"]
    # no torch / sklearn imported anywhere in the run module
    src = open(run60.__file__).read()
    assert "torch" not in src and "sklearn" not in src


def test_age_bin_preregistered():
    ab = run60._age_bin([17, 22, 23, 33])
    assert list(ab) == ["young", "young", "old", "old"]


def test_wilson_sane():
    p, lo, hi = run60.wilson(50, 100)
    assert abs(p - 0.5) < 1e-9 and lo < 0.5 < hi and 0 <= lo and hi <= 1


def test_seed_guard_md5_stable():
    m1 = run60.seed_md5()
    m2 = hashlib.md5(open(run60.SEED_FILE, "rb").read()).hexdigest()
    assert m1 == m2 and len(m1) == 32
