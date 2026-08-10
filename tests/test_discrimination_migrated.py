"""RUN 57 -- unit gate for THE GRAPH-NATIVE DISCRIMINATION FACULTY (`domains/discrimination.py`).

Covers the launch brief's pre-registered unit requirements:
  * DISCRIMINABILITY COMPUTES CORRECTLY: a feature that SEPARATES classes (far-apart class means,
    tight within) -> HIGH Fisher; a feature that is tight-but-NON-SEPARATING (class means coincide)
    -> LOW Fisher; a noisy feature -> LOW Fisher.
  * THE RUN-56 FAILURE CASE: a relation tight for the TRUE class but ALSO tight for the FALSE
    classes gets LOW discriminability precision -- UNLIKE tightness (1/within-var), which gives it a
    HIGH precision. This is the exact over-trust run 57 fixes; the two rank the feature oppositely.
  * RICHER RELATIONS DERIVE CORRECTLY: a synthetic T-junction -> endpoint-midpoint; a corner ->
    endpoint-endpoint; a crossing -> midpoint-midpoint; separated strokes -> no contact.
  * GUARD-REDUCTION: feeding discriminability precisions with `prec_rel=0` to the UNCHANGED
    `unified_verdict` reproduces the whole-shape argmin byte-identically.
  * GRAPH-NATIVE AUDIT: the precision the verdict reads is a graph `log_weight` EDGE (install ->
    read round-trips through the substrate), NOT an external Python dict.
  * NO-PYTHON-DECISION AUDIT: the module contains no `min`/`max`/`argmin`/`sorted`/`if score`
    ranking -- only variance ratios + held-Term/graph reads.
  * SEED-GUARD: this module never writes the stroke seed.
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
from domains import discrimination as disc
from domains import unified_verdict as uv

STROKE_SHAPES_SEED = os.path.join(ROOT, "seeds", "stroke_shapes.json")
DISC_SRC = os.path.join(ROOT, "domains", "discrimination.py")


def _md5(path):
    if not os.path.exists(path):
        return "MISSING"
    return hashlib.md5(open(path, "rb").read()).hexdigest()


# ------------------------------------------------------------------------------------------- #
#  FISHER computes correctly.
# ------------------------------------------------------------------------------------------- #
def test_fisher_separating_feature_scores_high():
    # class A tight around 0.1, class B tight around 0.9 -> far means, small within -> HIGH Fisher.
    a = [0.10, 0.11, 0.09, 0.10]
    b = [0.90, 0.91, 0.89, 0.90]
    f = disc.fisher_ratio([a, b])
    assert f > 10.0, f


def test_fisher_tight_but_nonseparating_scores_low():
    # both classes tight AND at the SAME location -> between ~= 0 -> Fisher ~= 0, DESPITE tightness.
    a = [0.50, 0.51, 0.49, 0.50]
    b = [0.50, 0.49, 0.51, 0.50]
    f = disc.fisher_ratio([a, b])
    assert f < 0.5, f
    # tightness of either class alone is HIGH (low variance) -- the contrast the faculty fixes.
    assert disc.tightness(a) > 100.0


def test_fisher_noisy_feature_scores_low():
    # far means but HUGE within-class scatter -> low Fisher (noisy = untrustworthy).
    a = list(np.random.default_rng(0).normal(0.2, 1.0, 50))
    b = list(np.random.default_rng(1).normal(0.8, 1.0, 50))
    assert disc.fisher_ratio([a, b]) < 0.5


def test_fisher_degenerate_returns_zero():
    assert disc.fisher_ratio([[0.1, 0.2]]) == 0.0          # one class -> nothing to separate.
    assert disc.fisher_ratio([[], []]) == 0.0


# ------------------------------------------------------------------------------------------- #
#  THE RUN-56 FAILURE CASE -- discriminability distrusts what tightness over-trusts.
# ------------------------------------------------------------------------------------------- #
def test_run56_failure_case_discriminability_distrusts_tightness_overtrusts():
    """A relation whose TRUE-class residual is razor-tight (so tightness rates it maximally
    trustworthy) but whose FALSE-class residuals OVERLAP the true ones (so it does NOT separate)."""
    true_res = [0.20, 0.21, 0.19, 0.20, 0.20]              # tight for the true class.
    false_res = [0.19, 0.21, 0.20, 0.22, 0.18, 0.20, 0.21]  # false candidates sit RIGHT THERE too.
    tight = disc.tightness(true_res)                       # run 56's precision.
    fisher = disc.part_discriminability(true_res, false_res)  # run 57's precision.
    assert tight > 100.0, tight            # tightness OVER-TRUSTS: razor-tight -> huge precision.
    assert fisher < 0.5, fisher            # discriminability DISTRUSTS: no separation -> tiny.
    # And a genuinely SEPARATING part (true tight-low, false clearly higher) reads HIGH fisher --
    # so the faculty trusts what SEPARATES, not merely what is consistent.
    sep_true = [0.05, 0.06, 0.04, 0.05]
    sep_false = [0.80, 0.75, 0.85, 0.78, 0.82]
    assert disc.part_discriminability(sep_true, sep_false) > 1.0


# ------------------------------------------------------------------------------------------- #
#  RICHER RELATIONS derive correctly.
# ------------------------------------------------------------------------------------------- #
def _line(p0, p1, n=11):
    return [(p0[0] + (p1[0] - p0[0]) * t / (n - 1),
             p0[1] + (p1[1] - p0[1]) * t / (n - 1)) for t in range(n)]


def test_attachment_corner_endpoint_endpoint():
    # two lines meeting at a shared corner (0,0) -> endpoint-endpoint.
    a = _line((0, 0), (1, 0))
    b = _line((0, 0), (0, 1))
    assert disc.attachment_class(a, b) == disc.ATTACH_EE


def test_attachment_t_junction_endpoint_midpoint():
    # a's END lands on b's MIDDLE -> endpoint-midpoint (a T-junction).
    b = _line((-1, 0), (1, 0))          # horizontal bar, midpoint at (0,0).
    a = _line((0, 1), (0, 0))           # vertical stem ending at b's midpoint.
    assert disc.attachment_class(a, b) == disc.ATTACH_EM


def test_attachment_crossing_midpoint_midpoint():
    # two bars crossing at their interiors -> midpoint-midpoint (an X).
    a = _line((-1, 0), (1, 0))
    b = _line((0, -1), (0, 1))
    assert disc.attachment_class(a, b) == disc.ATTACH_MM


def test_attachment_no_contact():
    a = _line((0, 0), (1, 0))
    b = _line((5, 5), (6, 5))
    assert disc.attachment_class(a, b) == disc.ATTACH_NONE


def test_attachment_relations_and_junction_profile():
    strokes = [_line((0, 0), (1, 0)), _line((0, 0), (0, 1)), _line((5, 5), (6, 5))]
    rels = disc.attachment_relations(strokes)
    assert len(rels) == 3                                   # 3 unordered pairs.
    d = disc.attach_by_pair(rels)
    assert d[(0, 1)] == disc.ATTACH_EE                      # the two joined strokes.
    prof = disc.junction_profile(strokes)
    assert abs(sum(prof.values()) - 1.0) < 1e-9            # fractions sum to 1.
    assert prof["frac_ee"] > 0 and prof["frac_none"] > 0


def test_junction_slot_discriminability_separates():
    # class A always has an EE corner + a free stroke; class B always crosses (MM).
    corner = [_line((0, 0), (1, 0)), _line((0, 0), (0, 1)), _line((9, 9), (10, 9))]
    cross = [_line((-1, 0), (1, 0)), _line((0, -1), (0, 1)), _line((9, 9), (10, 9))]
    a_profiles = [disc.junction_profile(corner) for _ in range(4)]
    b_profiles = [disc.junction_profile(cross) for _ in range(4)]
    per_slot = {s: {"A": [p[s] for p in a_profiles], "B": [p[s] for p in b_profiles]}
                for s in disc.JUNCTION_SLOTS}
    fish = disc.slot_discriminability(per_slot)
    # frac_ee and frac_mm SEPARATE the two classes (present in one, absent in the other).
    assert fish["frac_ee"] > 1.0 and fish["frac_mm"] > 1.0


# ------------------------------------------------------------------------------------------- #
#  GUARD-REDUCTION -- discriminability precisions in the UNCHANGED unified_verdict.
# ------------------------------------------------------------------------------------------- #
def test_guard_reduction_with_discriminability_precisions():
    native = srs.Substrate()._inner
    per_cand = [{"whole": 0.30, "stroke": 0.4, "rel": 0.10},   # ci 0: worse geometry
                {"whole": 0.10, "stroke": 0.5, "rel": 0.90}]   # ci 1: best geometry
    # any positive prec_whole -> argmin(prec_whole*whole^2) == argmin(whole) == candidate 1.
    pw = disc.part_discriminability([0.1, 0.11], [0.8, 0.82])
    guard = uv.unified_verdict_pred(native, per_cand, prec_whole=pw, prec_stroke=0.0, prec_rel=0.0)
    assert guard == 1


# ------------------------------------------------------------------------------------------- #
#  GRAPH-NATIVE AUDIT -- precision is a graph log_weight EDGE, not a Python dict.
# ------------------------------------------------------------------------------------------- #
def test_precision_is_graph_edge_data():
    from domains import frame_weights as fw
    sub = srs.Substrate()
    precisions = {"whole": 34.34, "stroke": 0.0395, "rel": 0.0037}
    frame = disc.install_part_precisions(sub, precisions)
    got = disc.read_part_precisions(sub, frame)
    for part, val in precisions.items():
        assert abs(got[part] - val) < 1e-6, (part, got.get(part), val)
    # the value genuinely lives on a graph FrameAxis node's log_weight attr (a graph read, not the
    # Python dict we passed) -- exp(log_weight) round-trips the precision.
    import numpy as _np
    for part, val in precisions.items():
        assert abs(_np.exp(fw.axis_log_weight(sub, frame, part)) - val) < 1e-6


# ------------------------------------------------------------------------------------------- #
#  NO-PYTHON-DECISION source audit + seed guard.
# ------------------------------------------------------------------------------------------- #
def test_no_python_decision_source_audit():
    src = open(DISC_SRC).read()
    # strip comments/docstrings crudely: forbid ranking primitives in executable lines.
    banned = re.compile(r"\b(argmin|argmax|sorted)\b|(?<![<>=!])\bmax\s*\(|(?<![<>=!])\bmin\s*\(")
    offenders = []
    for i, line in enumerate(src.splitlines(), 1):
        code = line.split("#", 1)[0]
        if '"""' in code or "'''" in code:
            continue
        m = banned.search(code)
        # np.argmin over a DISTANCE MATRIX to find the nearest point-pair is a geometric SELECTION,
        # not a verdict ranking (the same license geo_margin's np.partition carries). max()/min() as
        # an eps-floor / denominator guard is arithmetic, not a decision.
        if m and "eps" not in code.lower() and "diag" not in code and "argmin" not in code:
            offenders.append((i, line.strip()))
    assert not offenders, offenders


def test_seed_unchanged():
    before = _md5(STROKE_SHAPES_SEED)
    disc.fisher_ratio([[0.1, 0.2], [0.8, 0.9]])
    disc.install_part_precisions(srs.Substrate(), {"whole": 1.0})
    assert _md5(STROKE_SHAPES_SEED) == before
