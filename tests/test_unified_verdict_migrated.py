"""RUN 56 -- unit gate for the UNIFIED LOG-ODDS NATIVE DERIVATION
(`domains/unified_verdict.py`).

Covers the launch brief's pre-registered unit requirements:
  * COMMENSURABILITY: geometry and relation terms are in the SAME log-odds units -- a synthetic with
    equal-magnitude geo and rel residuals under equal precision contributes EQUALLY (the scale
    reconciliation is real, not nominal);
  * GUARD-REDUCTION: `prec_rel=0` (and `prec_stroke=0`) -> the unified verdict is BYTE-IDENTICAL to
    the whole-shape argmin (so geometry-only == SC+TPS baseline; it structurally cannot badly
    underperform whole-shape);
  * PER-INSTANCE ARBITRATION: a geo-AMBIGUOUS synthetic (near-equal whole across candidates,
    differing rel) -> the relation term FLIPS the argmin vs GUARD; a geo-DECISIVE synthetic (whole
    clearly separates) -> the relation term does NOT flip it (geometry dominates);
  * AMORTIZATION: source audit -- ONE evaluation per candidate, no search/MCMC/anneal loop;
  * the verdict is a held `Argmin` -- no Python min/max/argmin/sorted decision anywhere;
  * the seed-guard md5 (this module never writes the stroke seed).

Runs under system python3 (pure Term-builder + numpy arithmetic; the held Argmin needs
`substrate_rs`, imported lazily inside the tests that evaluate).
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

import substrate_rs as srs
from domains import unified_verdict as uv

STROKE_SHAPES_SEED = os.path.join(ROOT, "seeds", "stroke_shapes.json")


def _native():
    return srs.Substrate()._inner


def _md5(path):
    if not os.path.exists(path):
        return "MISSING"
    return hashlib.md5(open(path, "rb").read()).hexdigest()


# ------------------------------------------------------------------------------------------- #
#  Precision = 1 / within-true-class variance (the concept's predicted distribution width).
# ------------------------------------------------------------------------------------------- #
def test_part_precision_is_inverse_variance():
    resids = [0.10, 0.12, 0.08, 0.11, 0.09]
    assert abs(uv.part_precision(resids) - 1.0 / float(np.var(resids))) < 1e-6
    # a tighter (lower-variance) part reads a HIGHER precision -- the concept predicts it sharply.
    tight = uv.part_precision([0.10, 0.101, 0.099])
    loose = uv.part_precision([0.10, 0.30, 0.50])
    assert tight > loose
    # empty / degenerate -> finite eps-floored precision, never a crash.
    assert np.isfinite(uv.part_precision([]))
    assert np.isfinite(uv.part_precision([0.2, 0.2, 0.2]))


# ------------------------------------------------------------------------------------------- #
#  COMMENSURABILITY -- equal-magnitude geo and rel residuals under equal precision contribute
#  equally (the log-odds scale reconciliation is genuine).
# ------------------------------------------------------------------------------------------- #
def test_geometry_and_relation_terms_are_commensurate():
    native = _native()
    r = 0.37
    # candidate A: all its residual is in GEOMETRY (whole=r, rel=0).
    cost_geo = float(native.evaluate(
        uv.unified_cost_term(whole=r, stroke=0.0, rel=0.0,
                             prec_whole=1.0, prec_stroke=0.0, prec_rel=1.0), {}))
    # candidate B: the SAME magnitude, all in RELATION (whole=0, rel=r).
    cost_rel = float(native.evaluate(
        uv.unified_cost_term(whole=0.0, stroke=0.0, rel=r,
                             prec_whole=1.0, prec_stroke=0.0, prec_rel=1.0), {}))
    assert abs(cost_geo - cost_rel) < 1e-9        # equal magnitude + equal precision -> equal cost.
    assert abs(cost_geo - (r * r)) < 1e-9         # and it IS precision * residual^2 (log-odds).


# ------------------------------------------------------------------------------------------- #
#  GUARD-REDUCTION -- prec_rel=0 (prec_stroke=0) reduces to the whole-shape argmin byte-identically.
# ------------------------------------------------------------------------------------------- #
def test_guard_reduction_reduces_to_whole_shape_argmin():
    native = _native()
    # rel/stroke would prefer candidate 0/2, but geometry-only MUST pick lowest whole (candidate 1).
    per_cand = [dict(whole=0.9, stroke=0.0, rel=0.0),
                dict(whole=0.3, stroke=9.0, rel=9.0),      # lowest whole -> must win when rel off.
                dict(whole=0.7, stroke=0.0, rel=0.0)]
    guard = uv.unified_verdict_pred(native, per_cand,
                                    prec_whole=2.3, prec_stroke=0.0, prec_rel=0.0)
    assert guard == 1
    # and it equals a plain argmin over the whole residual (the SC+TPS verdict), for any prec_whole.
    whole_argmin = int(np.argmin([c["whole"] for c in per_cand]))
    assert guard == whole_argmin


# ------------------------------------------------------------------------------------------- #
#  PER-INSTANCE ARBITRATION -- the load-bearing check: relations decide iff geometry is ambiguous.
# ------------------------------------------------------------------------------------------- #
def test_relation_flips_verdict_when_geometry_ambiguous():
    native = _native()
    # GEO-AMBIGUOUS: candidates 0 and 1 have NEAR-EQUAL whole; candidate 1 is truly right and its
    # relation residual is clearly lower. Geometry alone (GUARD) picks 0 by a hair; the unified
    # verdict lets the confident relation term OVERRIDE and pick 1.
    amb = [dict(whole=0.300, stroke=0.0, rel=0.90),
           dict(whole=0.305, stroke=0.0, rel=0.05),        # true: whole ~tied, rel decisive.
           dict(whole=0.800, stroke=0.0, rel=0.80)]
    guard = uv.unified_verdict_pred(native, amb, prec_whole=10.0, prec_stroke=0.0, prec_rel=0.0)
    unified = uv.unified_verdict_pred(native, amb, prec_whole=10.0, prec_stroke=0.0, prec_rel=10.0)
    assert guard == 0                       # geometry alone picks the hair-lower whole.
    assert unified == 1                     # relation OVERRIDES under ambiguity -> the true class.
    assert uv.geo_margin(amb) < 0.05        # and this episode IS geo-ambiguous (tiny top-2 gap).


def test_relation_does_not_flip_verdict_when_geometry_decisive():
    native = _native()
    # GEO-DECISIVE: candidate 0's whole is CLEARLY lowest (a large top-2 residual gap), so the
    # squared geometry separation exceeds the relation separation -- a relation term that mildly
    # prefers another candidate must NOT override; geometry dominates.
    dec = [dict(whole=0.100, stroke=0.0, rel=0.50),        # decisive geometry winner.
           dict(whole=0.550, stroke=0.0, rel=0.20),        # relation "prefers" this, but geo says no.
           dict(whole=0.700, stroke=0.0, rel=0.45)]
    guard = uv.unified_verdict_pred(native, dec, prec_whole=10.0, prec_stroke=0.0, prec_rel=0.0)
    unified = uv.unified_verdict_pred(native, dec, prec_whole=10.0, prec_stroke=0.0, prec_rel=10.0)
    assert guard == 0
    assert unified == 0                     # geometry decisive -> relation cannot flip it.
    assert uv.geo_margin(dec) > 0.5         # and this episode IS geo-decisive (large top-2 gap).


def test_empty_pool_is_honest_noncrash():
    native = _native()
    assert uv.unified_verdict_pred(native, [], prec_whole=1.0, prec_stroke=0.0, prec_rel=1.0) == -1


# ------------------------------------------------------------------------------------------- #
#  Amortization -- ONE evaluation per candidate, no search over concept parameters (source audit).
# ------------------------------------------------------------------------------------------- #
def _code_only(path):
    raw = open(path).read()
    raw = re.sub(r'"""(?:.|\n)*?"""', "", raw)
    raw = re.sub(r"'''(?:.|\n)*?'''", "", raw)
    raw = re.sub(r"#.*", "", raw)
    return raw.lower()


def test_amortization_no_search_loop_source_audit():
    code = _code_only(os.path.join(ROOT, "domains", "unified_verdict.py"))
    for banned in ("mcmc", "anneal", "metropolis", "gibbs", "propose_", "while ", "random."):
        assert banned not in code, banned


def test_unified_verdict_no_python_decisions():
    src = _code_only(os.path.join(ROOT, "domains", "unified_verdict.py"))
    for banned in ("np.argmin", "np.argmax", "sorted(", ".sort("):
        assert banned not in src, banned
    for banned in (r"\bmin\(", r"\bmax\(", r"\bargmin\(", r"\bargmax\("):
        assert not re.search(banned, src), banned


def test_seed_guard_md5_unchanged():
    before = _md5(STROKE_SHAPES_SEED)
    native = _native()
    per_cand = [dict(whole=0.4, stroke=0.1, rel=0.2), dict(whole=0.2, stroke=0.3, rel=0.1)]
    uv.unified_verdict_pred(native, per_cand, prec_whole=1.0, prec_stroke=1.0, prec_rel=1.0)
    uv.part_precision([0.1, 0.2, 0.3])
    uv.geo_margin(per_cand)
    after = _md5(STROKE_SHAPES_SEED)
    assert before == after
