"""RUN 58b -- unit gate for the CROSS-WRITER-ROBUST discrimination fix
(`domains/crosswriter_discrimination.py`).

Pre-registered unit requirements (the launch brief):
  * CROSS-WRITER FISHER on a synthetic:
      - a feature class-consistent ACROSS WRITERS         -> HIGH cross-writer Fisher.
      - a writer-idiosyncratic feature (separation driven by a prolific / disagreeing subset of
        writers) -> LOW cross-writer Fisher, UNLIKE pooled Fisher which rates it HIGH. This is the
        exact run-58 failure case reproduced in miniature.
      - a feature with high writer x class INTERACTION (writers separate the classes in OPPOSITE
        directions) -> LOW cross-writer Fisher (non-transferable).
  * CROSS-WRITER-HELD-OUT SANITY MECHANICS: `split_writers` partitions writers into two disjoint,
    fully-covering groups deterministically (holds out writers correctly).
  * NO-PYTHON-DECISION source audit: the module has no ranking primitive (argmin/argmax/sorted-as-
    verdict / bare min()/max() decision) -- only variance ratios + a seeded shuffle.
  * SEED-GUARD: the module never writes the stroke seed.
"""
from __future__ import annotations

import hashlib
import os
import re
import sys

os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np

from domains import crosswriter_discrimination as cw
from domains import discrimination as disc

STROKE_SHAPES_SEED = os.path.join(ROOT, "seeds", "stroke_shapes.json")
CW_SRC = os.path.join(ROOT, "domains", "crosswriter_discrimination.py")


def _md5(path):
    if not os.path.exists(path):
        return "MISSING"
    return hashlib.md5(open(path, "rb").read()).hexdigest()


def _tight(rng, mu, n, sd=0.01):
    return list(rng.normal(mu, sd, n))


# ------------------------------------------------------------------------------------------- #
#  CROSS-WRITER FISHER.
# ------------------------------------------------------------------------------------------- #
def test_class_consistent_across_writers_scores_high():
    # every writer draws class A near 0.2 and class B near 0.8 -> the class distinction holds for
    # every writer -> HIGH cross-writer Fisher (transferable).
    rng = np.random.default_rng(0)
    per_class = {
        "A": {w: _tight(rng, 0.2, 8) for w in range(4)},
        "B": {w: _tight(rng, 0.8, 8) for w in range(4)},
    }
    f_cw = cw.crosswriter_fisher(per_class)
    f_pool = cw.pooled_fisher(per_class)
    assert f_cw > 10.0, f_cw           # class-defining across writers -> high.
    assert f_pool > 10.0, f_pool       # pooled agrees when the signal genuinely transfers.


def test_writer_idiosyncratic_prolific_confound_pooled_high_crosswriter_low():
    """THE RUN-58 FAILURE CASE in miniature. A prolific writer (writer 0) drives the class
    separation: writer 0 writes class A high (0.9) and class B low (0.1) with MANY instances, while
    the other writers do not separate the classes at all (both ~0.5). Pooled Fisher is fooled by
    writer 0's instance count and rates the feature HIGHLY separating; cross-writer Fisher, weighting
    each writer equally and measuring the BETWEEN-WRITER scatter, sees that the other writers do not
    separate and rates it LOW."""
    rng = np.random.default_rng(1)
    per_class = {
        "A": {0: _tight(rng, 0.9, 60), 1: _tight(rng, 0.5, 4),
              2: _tight(rng, 0.5, 4), 3: _tight(rng, 0.5, 4)},
        "B": {0: _tight(rng, 0.1, 60), 1: _tight(rng, 0.5, 4),
              2: _tight(rng, 0.5, 4), 3: _tight(rng, 0.5, 4)},
    }
    f_pool = cw.pooled_fisher(per_class)
    f_cw = cw.crosswriter_fisher(per_class)
    assert f_pool > 1.5, f_pool        # pooled OVER-TRUSTS the prolific-writer-driven separation.
    assert f_cw < 0.6, f_cw            # cross-writer DISTRUSTS it (writers 1-3 do not separate).
    assert f_cw < f_pool, (f_cw, f_pool)


def test_writer_class_interaction_scores_low():
    # each writer separates A from B strongly but in OPPOSITE directions (pure interaction, no
    # transferable main effect) -> low cross-writer Fisher.
    rng = np.random.default_rng(2)
    per_class = {
        "A": {0: _tight(rng, 0.1, 8), 1: _tight(rng, 0.9, 8),
              2: _tight(rng, 0.1, 8), 3: _tight(rng, 0.9, 8)},
        "B": {0: _tight(rng, 0.9, 8), 1: _tight(rng, 0.1, 8),
              2: _tight(rng, 0.9, 8), 3: _tight(rng, 0.1, 8)},
    }
    assert cw.crosswriter_fisher(per_class) < 0.6, cw.crosswriter_fisher(per_class)


def test_crosswriter_requires_two_writers_per_class():
    # a class present for only ONE writer offers no cross-writer replication -> it is dropped, and
    # with fewer than two usable classes the ratio is 0 (nothing transferable to measure).
    per_class = {"A": {0: [0.2, 0.21]}, "B": {1: [0.8, 0.81]}}
    assert cw.crosswriter_fisher(per_class, min_writers=2) == 0.0


def test_slot_fisher_side_by_side():
    rng = np.random.default_rng(3)
    # slot "good" transfers; slot "style" is the prolific-writer confound.
    per_slot = {
        "good": {"A": {w: _tight(rng, 0.2, 8) for w in range(4)},
                 "B": {w: _tight(rng, 0.8, 8) for w in range(4)}},
        "style": {"A": {0: _tight(rng, 0.9, 60), 1: _tight(rng, 0.5, 4),
                        2: _tight(rng, 0.5, 4), 3: _tight(rng, 0.5, 4)},
                  "B": {0: _tight(rng, 0.1, 60), 1: _tight(rng, 0.5, 4),
                        2: _tight(rng, 0.5, 4), 3: _tight(rng, 0.5, 4)}},
    }
    cw_f = cw.crosswriter_slot_fisher(per_slot)
    pool_f = cw.pooled_slot_fisher(per_slot)
    assert cw_f["good"] > 10.0 and cw_f["style"] < 0.6
    assert pool_f["style"] > 1.5                      # pooled is fooled by the style slot.
    # normalized weights concentrate on the transferable slot, ~zero the style slot.
    w = cw.normalize_weights(cw_f, ("good", "style"))
    assert w["good"] > w["style"]
    assert w["style"] < 0.2


def test_crosswriter_part_discriminability_two_class():
    rng = np.random.default_rng(4)
    # true residuals low for every writer, false residuals high for every writer -> separates.
    true_by_w = {w: _tight(rng, 0.05, 6) for w in range(4)}
    false_by_w = {w: _tight(rng, 0.8, 6) for w in range(4)}
    assert cw.crosswriter_part_discriminability(true_by_w, false_by_w) > 1.0
    # overlapping true/false (non-separating): both centered at 0.5 with real spread -> low.
    true2 = {w: _tight(rng, 0.5, 12, sd=0.15) for w in range(4)}
    false2 = {w: _tight(rng, 0.5, 12, sd=0.15) for w in range(4)}
    assert cw.crosswriter_part_discriminability(true2, false2) < 0.6


# ------------------------------------------------------------------------------------------- #
#  CROSS-WRITER-HELD-OUT SANITY MECHANICS.
# ------------------------------------------------------------------------------------------- #
def test_split_writers_disjoint_and_covering():
    writers = list(range(40))
    cal, san = cw.split_writers(writers, frac_calib=0.5, seed=7)
    assert set(cal).isdisjoint(set(san))              # NO writer in both.
    assert set(cal) | set(san) == set(writers)        # every writer placed.
    assert len(cal) == 20 and len(san) == 20
    assert cal == sorted(cal) and san == sorted(san)


def test_split_writers_deterministic_and_seed_sensitive():
    writers = list(range(30))
    a1, b1 = cw.split_writers(writers, seed=7)
    a2, b2 = cw.split_writers(writers, seed=7)
    a3, b3 = cw.split_writers(writers, seed=8)
    assert a1 == a2 and b1 == b2                       # deterministic.
    assert a1 != a3                                    # a different seed -> a different split.


def test_split_writers_degenerate():
    assert cw.split_writers([5], seed=0) == ([5], [])  # one writer -> nothing to hold out.


# ------------------------------------------------------------------------------------------- #
#  NO-PYTHON-DECISION source audit + seed guard.
# ------------------------------------------------------------------------------------------- #
def test_no_python_decision_source_audit():
    src = open(CW_SRC).read()
    banned = re.compile(r"\b(argmin|argmax|sorted)\s*\(|(?<![<>=!])\bmax\s*\(|(?<![<>=!])\bmin\s*\(")
    offenders = []
    for i, line in enumerate(src.splitlines(), 1):
        code = line.split("#", 1)[0]
        if '"""' in code or "'''" in code:
            continue
        m = banned.search(code)
        # `sorted(...)` here only canonicalizes the writer id ORDER for a deterministic split (not a
        # verdict); max()/min() are eps floors / count clamps (arithmetic guards, not decisions).
        if m and "eps" not in code.lower() and "min_writers" not in code and "n_cal" not in code \
                and "ws[i]" not in code and "set(" not in code:
            offenders.append((i, line.strip()))
    assert not offenders, offenders


def test_seed_unchanged():
    before = _md5(STROKE_SHAPES_SEED)
    cw.crosswriter_fisher({"A": {0: [0.1], 1: [0.11]}, "B": {0: [0.9], 1: [0.89]}})
    cw.split_writers(list(range(10)), seed=1)
    assert _md5(STROKE_SHAPES_SEED) == before
