"""THE IDENTITY-COST ANATOMY — the rung's own gate.

Pre-registration `VISION_IDENTITY_COST_ANATOMY_PREREG.md` @ `9d7195da`.

These tests gate the *instrument and its invariants*, not the headline numbers.
A wall-clock figure is contaminable and is never asserted here; what IS asserted
is every relation that must hold for the reported profile to be readable:

  * the closed-form attempt model FALLS OUT of the shipped seed (PROTOCOL §13),
  * the counted units match that model EXACTLY on both paths,
  * the cross-rung control -- this harness reproduces the term-eval rung's
    COMMITTED counter values, so the measurement chain is verified against a
    number published before this rung existed,
  * G5 is handed off to Rust and its own red/green controls still hold,
  * the invocation count `I` is invariant in N and K (the fact the reducibility
    candidate rests on).
"""
from __future__ import annotations

import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

RESULTS = os.path.join(ROOT, "results", "identity_cost_anatomy.json")
RESULTS_PREFIX = os.path.join(ROOT, "results", "identity_cost_anatomy_PREFIX.json")

ica = pytest.importorskip("scripts.identity_cost_anatomy")


def _doc(path):
    if not os.path.exists(path):
        pytest.skip(f"{os.path.basename(path)} not present — run the harness")
    with open(path) as fh:
        return json.load(fh)


# --------------------------------------------------------------------------- #
# THE MODEL — falls out of the seed, never written down
# --------------------------------------------------------------------------- #
def test_attempt_model_falls_out_of_the_shipped_seed():
    """`A` is read from `shape_decode_loop.json`'s own generator params. If a
    generator is added or its params change, this moves — which is the point:
    no constant is chosen (PROTOCOL §13)."""
    params = ica.generator_params()
    assert params, "no DimensionGenerator params found in the seed"
    l1, l2, a = ica.attempts_per_part()
    assert l1 == sum(params)
    assert l2 == sum(params) ** 2 - sum(p * p for p in params)
    assert a == l1 + l2


def test_the_length_1_share_is_the_measured_saving_ratio():
    """The codebook fix's saving is exactly `l1 / A`. This ties the fix's
    published 0.0884 to the seed rather than to a remembered number."""
    l1, _l2, a = ica.attempts_per_part()
    assert abs(l1 / a - 0.0884) < 5e-4, f"length-1 share {l1/a} moved"


# --------------------------------------------------------------------------- #
# THE COUNTED UNITS MATCH THE CLOSED FORM ON BOTH PATHS
# --------------------------------------------------------------------------- #
def _model_units(inv, k, attempts, n_cells, slots):
    return inv * k * attempts * n_cells * (1 + slots)


def test_counted_units_match_the_closed_form_on_the_recognising_path():
    """POST-fix, the recognising path pays the LENGTH-1 arm only.

    units = I x K x l1 x N x (1+s), with I READ from `term_eval:DimInfer`
    (never assumed), so this tests loop STRUCTURE, not invocation count."""
    d = _doc(RESULTS)
    p = d["profile_exact"]
    l1, _l2, _a = ica.attempts_per_part()
    inv = next(r["term_eval"] for r in p["rows"] if r["variant"] == "DimInfer")
    got = next(r["term_unit"] for r in p["rows"] if r["variant"] == "DimInfer")
    want = _model_units(inv, p["K"], l1, p["n_cells"], ica.SLOTS)
    assert got == want, f"recognising path: {got} != {want}"


def test_counted_units_match_the_closed_form_on_the_novel_path():
    """The novel path cannot short-circuit — it pays the FULL `A`. That the
    same closed form holds with a different attempt count is what makes the
    path axis a measurement rather than a label."""
    d = _doc(RESULTS)
    p = d["profile_novel"]
    _l1, _l2, a = ica.attempts_per_part()
    inv = next(r["term_eval"] for r in p["rows"] if r["variant"] == "DimInfer")
    got = next(r["term_unit"] for r in p["rows"] if r["variant"] == "DimInfer")
    want = _model_units(inv, p["K"], a, p["n_cells"], ica.SLOTS)
    assert got == want, f"novel path: {got} != {want}"


# --------------------------------------------------------------------------- #
# THE CROSS-RUNG CONTROL — against a number committed before this rung
# --------------------------------------------------------------------------- #
def test_prefix_harness_reproduces_the_term_eval_rungs_committed_counters():
    """`VISION_TERM_EVAL_COUNTER_RESULTS.md` §2.2 committed, at N=142/K=1:
    `term_unit:DimInfer` = 1,419,432 and `term_evals_total` = 424.

    This rung's harness is independently written on a different seed block. That
    it reproduces both values EXACTLY on the pre-fix engine is the control that
    the measurement chain — harness, counters, engine — is sound. A profile that
    could not reproduce a published number would not be readable."""
    d = _doc(RESULTS_PREFIX)
    p = d["profile_exact"]
    assert p["n_cells"] == 142 and p["K"] == 1
    got = next(r["term_unit"] for r in p["rows"] if r["variant"] == "DimInfer")
    assert got == 1_419_432, f"term_unit:DimInfer {got} != committed 1,419,432"
    assert p["term_evals_total"] == 424


def test_the_fix_ratio_is_the_length_1_share_not_an_average():
    """pre/post counted ratio == A/l1 exactly, at the profile point."""
    a_doc, b_doc = _doc(RESULTS), _doc(RESULTS_PREFIX)
    post = next(r["term_unit"] for r in a_doc["profile_exact"]["rows"]
                if r["variant"] == "DimInfer")
    pre = next(r["term_unit"] for r in b_doc["profile_exact"]["rows"]
               if r["variant"] == "DimInfer")
    l1, _l2, a = ica.attempts_per_part()
    assert abs(pre / post - a / l1) < 1e-6


# --------------------------------------------------------------------------- #
# G5 — handed off to Rust; the red control must still fail
# --------------------------------------------------------------------------- #
def test_g5_is_handed_off_to_rust_and_its_red_control_still_fails():
    """A gate that has never been shown to fail has not been tested. The A8
    signature — alive, deterministic, conserved, CONSTANT — must read BLIND."""
    from scripts.scale_split_measure import AUDIT
    assert AUDIT.scale_audit_g5_verdict([253] * 7, [253] * 7) == "BLIND"
    assert AUDIT.scale_audit_g5_verdict([10, 20, 40, 80], [10] * 4) == "RESPONSIVE"
    assert AUDIT.scale_audit_g5_verdict([0] * 7, [0] * 7) == "INERT"


def test_the_reported_unit_counters_are_responsive_on_the_axes_they_are_reported_against():
    """PREREG §1: no profile is readable from a counter that has not been shown
    to move on the axis the profile is about."""
    d = _doc(RESULTS)
    for axis in ("N", "K"):
        rows = {r["counter"]: r["verdict"] for r in d["step0_g5"][axis]}
        assert rows.get("term_unit:DimInfer") == "RESPONSIVE", (axis, rows)
        assert rows.get("term_units_total") == "RESPONSIVE", (axis, rows)


def test_unattributed_units_stay_zero():
    """The diagnostic that SHOULD stay 0. A non-zero reading means units were
    charged outside any variant guard and the profile is misfiled."""
    d = _doc(RESULTS)
    for axis in ("N", "K", "P"):
        rows = {r["counter"]: r["verdict"] for r in d["step0_g5"][axis]}
        assert rows.get("term_units_unattributed") == "INERT", (axis, rows)
    assert d["profile_exact"]["term_units_unattributed"] == 0
    assert d["profile_novel"]["term_units_unattributed"] == 0


# --------------------------------------------------------------------------- #
# THE FACT THE REDUCIBILITY CANDIDATE RESTS ON
# --------------------------------------------------------------------------- #
def test_dim_infer_invocation_count_is_invariant_in_N_and_K():
    """`I` is CONSTANT across a 11.8x range of N and a 16x range of K.

    This is the load-bearing observation behind the named reducibility
    candidate: the invocation count is not a function of problem size, so it is
    a scheduling constant rather than data-driven work. Asserted as a measured
    invariant so a successor can detect if it ever stops holding.

    NOTE it is asserted as CONSTANT, not as REDUNDANT — this rung does not claim
    the invocations are redundant and builds no instrument to decide it."""
    d = _doc(RESULTS)
    for axis in ("N", "K"):
        row = next(r for r in d["step0_g5"][axis]
                   if r["counter"] == "term_eval:DimInfer")
        assert len(set(row["sweep"])) == 1, f"I varies on {axis}: {row['sweep']}"
        assert row["verdict"] == "BLIND", (axis, row["verdict"])


def test_the_path_axis_separates_the_two_arms():
    """exact vs novel must differ in BOTH invocation count and attempt count,
    otherwise the path axis is a label rather than a measurement."""
    d = _doc(RESULTS)
    ex, nv = d["profile_exact"], d["profile_novel"]
    i_ex = next(r["term_eval"] for r in ex["rows"] if r["variant"] == "DimInfer")
    i_nv = next(r["term_eval"] for r in nv["rows"] if r["variant"] == "DimInfer")
    assert i_ex != i_nv, "the two paths must not share an invocation count"
    u_ex = next(r["term_unit"] for r in ex["rows"] if r["variant"] == "DimInfer")
    u_nv = next(r["term_unit"] for r in nv["rows"] if r["variant"] == "DimInfer")
    assert u_nv > u_ex, "the unexplained path must cost MORE (compute-∝-surprise)"


def test_compute_proportional_to_surprise_points_the_right_way():
    """The codebook rung found the OLD code had this INVERTED and corrected it.
    Gated here so it cannot silently invert again."""
    d = _doc(RESULTS)
    u_ex = next(r["term_unit"] for r in d["profile_exact"]["rows"]
                if r["variant"] == "DimInfer")
    u_nv = next(r["term_unit"] for r in d["profile_novel"]["rows"]
                if r["variant"] == "DimInfer")
    assert u_nv / u_ex > 1.0, f"surprise/recognised = {u_nv/u_ex} — INVERTED"
