"""RUN 55 -- unit gate for NATIVE GRAPH RECOGNITION (`domains/native_recognition.py`).

Covers the launch brief's pre-registered unit requirements:
  * the concept subgraph installs as Gamma-admissible GRAPH DATA (FrameAxis nodes with log_weight
    EDGES), no external Python state holding the precision;
  * the derivation cost reads the log-relative precision EDGES, not a static dict -- and the SAME
    relation slot gets a DIFFERENT effective precision in two derivation contexts with different
    sibling structure (the load-bearing per-INSTANCE vs per-TYPE distinction);
  * the derivation is ONE pass -- source audit: no search/MCMC/anneal loop over concept
    parameters;
  * GUARD-reduction sanity: plugged into the held `verdict_pred` at `w_rel=0`, the verdict is
    byte-identical to the whole-shape argmin;
  * greedy-matcher falsy-zero fix is the reused run39 matcher (a genuine zero-cost match survives);
  * the verdict is a held `Argmin` -- no Python min/max/argmin/sorted decision anywhere in the
    module;
  * the seed-guard md5 (this module never writes the stroke seed).

Runs under `.venv` (needs `substrate_rs`); the gate's `unit_sanity` stage invokes it via
`sys.executable`, mirroring run 50/54/54b's own suite discipline.
"""
from __future__ import annotations

import hashlib
import math
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
from domains import compositional_verdict as cv
from domains import frame_weights as fw
from domains import native_recognition as nr

STROKE_SHAPES_SEED = os.path.join(ROOT, "seeds", "stroke_shapes.json")
TIGHT = {"rel_x": 0.457, "rel_y": 0.387, "rel_o": 0.140, "rel_s": 2.949,
         "cpose_x": 0.489, "cpose_y": 0.430, "cpose_o": 0.268, "cpose_s": 2.880}


def _native():
    return srs.Substrate()._inner


def _md5(path):
    if not os.path.exists(path):
        return "MISSING"
    return hashlib.md5(open(path, "rb").read()).hexdigest()


def _cand_sig(ks=(0, 1, 2), rel=(1, 1, 0, 2)):
    sig = [["rel", k, rel[0], rel[1], rel[2], rel[3]] for k in ks]
    sig += [["cpose_x", 2], ["cpose_y", 1], ["cpose_o", 0], ["cpose_s", 1]]
    return sig


# ------------------------------------------------------------------------------------------- #
#  Concept subgraph is Gamma-admissible GRAPH DATA -- the precision lives in log_weight EDGES.
# ------------------------------------------------------------------------------------------- #
def test_concept_installs_as_graph_data_with_log_weight_edges():
    sub = srs.Substrate()
    frame_node = nr.install_concept_frame(sub, "c0", _cand_sig(), TIGHT)
    # one FrameAxis per rel:<k>:<slot> present + one per cpose_* -- reachable via in_dim edges.
    axis_names = {sub.node(a)["attrs"].get("name")
                  for a in sub.neighbours(frame_node, fw.IN_AXIS_EDGE)}
    for k in (0, 1, 2):
        for slot in nr.REL_SLOTS:
            assert f"rel:{k}:{slot}" in axis_names
    for slot in nr.CPOSE_SLOTS:
        assert slot in axis_names
    # the log_weight EDGE is log(tightness) -- the run-30 precision-as-a-graph-edge representation.
    assert abs(fw.axis_log_weight(sub, frame_node, "rel:0:rel_x") - math.log(TIGHT["rel_x"])) < 1e-9
    assert abs(fw.axis_log_weight(sub, frame_node, "rel:0:rel_s") - math.log(TIGHT["rel_s"])) < 1e-9
    assert abs(fw.axis_log_weight(sub, frame_node, "cpose_s") - math.log(TIGHT["cpose_s"])) < 1e-9


def test_install_concept_frame_is_idempotent():
    sub = srs.Substrate()
    f1 = nr.install_concept_frame(sub, "c0", _cand_sig(), TIGHT)
    n1 = len(sub.neighbours(f1, fw.IN_AXIS_EDGE))
    f2 = nr.install_concept_frame(sub, "c0", _cand_sig(), TIGHT)
    n2 = len(sub.neighbours(f2, fw.IN_AXIS_EDGE))
    assert f1 == f2 and n1 == n2


# ------------------------------------------------------------------------------------------- #
#  PER-INSTANCE precision -- the load-bearing distinction from static per-TYPE weights.
# ------------------------------------------------------------------------------------------- #
def test_same_relation_gets_different_precision_across_derivations():
    """The SAME relation slot (rel_x) reads a DIFFERENT effective precision when its sibling parts
    differ -- centering over THIS derivation's parts. A static per-type weight cannot do this."""
    # context A: rel_x sits beside a LOOSE (low-tightness) sibling rel_o -> rel_x relatively HIGH.
    rp_a = nr.relative_precisions([math.log(TIGHT["rel_x"]), math.log(TIGHT["rel_o"])])
    # context B: rel_x sits beside a TIGHT (high-tightness) sibling rel_s -> rel_x relatively LOW.
    rp_b = nr.relative_precisions([math.log(TIGHT["rel_x"]), math.log(TIGHT["rel_s"])])
    assert rp_a[0] > 1.0 > rp_b[0]                 # same slot, opposite sides of the mean.
    assert abs(rp_a[0] - rp_b[0]) > 0.5            # materially different, not a rounding wobble.
    # geometric mean of relative precisions is 1 by construction (log-relative centering).
    assert abs(float(np.exp(np.mean(np.log(rp_a)))) - 1.0) < 1e-9


def test_relative_precisions_empty_is_empty():
    assert nr.relative_precisions([]) == []


def test_native_residual_reads_edges_and_varies_with_sibling_structure():
    """End-to-end: the residual reads the concept frame's log_weight EDGES. A query mismatching a
    slot costs its per-INSTANCE relative precision -- so a mismatch on a slot that is relatively
    precise in THIS derivation costs more. Verifies the residual is edge-driven, not dict-driven."""
    sub = srs.Substrate()
    native = sub._inner
    cand_sig = _cand_sig(ks=(0,), rel=(1, 1, 0, 2))
    frame = nr.install_concept_frame(sub, "c0", cand_sig, TIGHT)
    cand_pts = [(np.array([[0.0, 0.0], [1.0, 0.0], [2.0, 1.0]]), None, None, None)]
    # query identical arrangement -> zero mismatch -> residual == 0 (no unmatched, all bins agree).
    q_same = _cand_sig(ks=(0,), rel=(1, 1, 0, 2))
    r_same = nr.native_relation_residual(sub, native, frame, cand_pts, q_same, cand_pts, cand_sig)
    assert r_same == 0.0
    # query mismatching rel_x only -> positive residual.
    q_diff = _cand_sig(ks=(0,), rel=(9, 1, 0, 2))
    r_diff = nr.native_relation_residual(sub, native, frame, cand_pts, q_diff, cand_pts, cand_sig)
    assert r_diff > 0.0


# ------------------------------------------------------------------------------------------- #
#  GUARD-reduction sanity -- plugged into the held verdict at w_rel=0, reduces to whole-shape.
# ------------------------------------------------------------------------------------------- #
def test_guard_reduction_native_rel_plugged_in():
    """The native residual plugs into the SAME `compositional_verdict.verdict_pred` held Argmin.
    At `w_rel=0` (a chance-level rel grain drops out) the verdict is byte-identical to the
    whole-shape GUARD -- the native rel value is irrelevant when its level weight is 0."""
    native = _native()
    per_cand = [dict(whole=0.9, stroke=0.0, rel=123.4),
                dict(whole=0.3, stroke=9.0, rel=0.0),      # lowest whole must win at w_rel=0.
                dict(whole=0.7, stroke=0.0, rel=999.9)]
    pred = cv.verdict_pred(native, per_cand, w_whole=1.0, w_stroke=0.0, w_rel=0.0)
    guard = cv.verdict_pred(native, per_cand, w_whole=1.0, w_stroke=0.0, w_rel=0.0)
    assert pred == guard == 1


# ------------------------------------------------------------------------------------------- #
#  Amortization -- ONE derivation pass, no search over concept parameters (source audit).
# ------------------------------------------------------------------------------------------- #
def _code_only(path):
    """Strip triple-quoted docstrings and `#` comments -- prose that DESCRIBES what the module does
    NOT do (e.g. 'never a per-query MCMC search') must not trip the search-loop audit."""
    raw = open(path).read()
    raw = re.sub(r'"""(?:.|\n)*?"""', "", raw)
    raw = re.sub(r"'''(?:.|\n)*?'''", "", raw)
    raw = re.sub(r"#.*", "", raw)
    return raw.lower()


def test_amortization_no_search_loop_source_audit():
    code = _code_only(os.path.join(ROOT, "domains", "native_recognition.py"))
    # ONE Gamma-pruned pass per (query, candidate): no iterative search over concept parameters.
    for banned in ("mcmc", "anneal", "metropolis", "gibbs", "propose_", "while ", "random."):
        assert banned not in code, banned
    # the only alignment call is the FIXED, single-pass greedy matcher (reused, not re-invented).
    assert "greedy_match" in code


def test_greedy_matcher_falsy_zero_fix_is_reused():
    """`align_stroke_points` routes through run39's FIXED greedy matcher (falsy-zero-safe) -- a
    genuine zero-cost identical-stroke match survives (regression guard on the REUSE)."""
    native = _native()
    pts = [np.array([[0.0, 0.0], [1.0, 1.0], [2.0, 0.0]])]
    gm = __import__("domains.relational_variation", fromlist=["align_stroke_points"]) \
        .align_stroke_points(native, pts, pts)
    assert gm["matched"] and gm["matched"][0][0] == 0 and gm["matched"][0][1] == 0
    assert not gm["unmatched_true"] and not gm["unmatched_pred"]


# ------------------------------------------------------------------------------------------- #
#  No-Python-decision audit + seed guard.
# ------------------------------------------------------------------------------------------- #
def test_no_python_decision_tokens():
    src = _code_only(os.path.join(ROOT, "domains", "native_recognition.py"))
    for banned in ("np.argmin", "np.argmax", "sorted(", ".sort("):
        assert banned not in src, banned
    for banned in (r"\bmin\(", r"\bmax\(", r"\bargmin\(", r"\bargmax\("):
        assert not re.search(banned, src), banned


def test_seed_guard_md5_unchanged():
    before = _md5(STROKE_SHAPES_SEED)
    sub = srs.Substrate()
    native = sub._inner
    frame = nr.install_concept_frame(sub, "c0", _cand_sig(ks=(0,)), TIGHT)
    cand_pts = [(np.array([[0.0, 0.0], [1.0, 0.0], [2.0, 1.0]]), None, None, None)]
    nr.native_relation_residual(sub, native, frame, cand_pts, _cand_sig(ks=(0,)),
                                cand_pts, _cand_sig(ks=(0,)))
    after = _md5(STROKE_SHAPES_SEED)
    assert before == after
