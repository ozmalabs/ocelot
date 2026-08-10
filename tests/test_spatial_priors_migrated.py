"""tests/test_spatial_priors_migrated.py — RUN 21's LEARNED SPATIAL PRIORS lever
(domains/spatial_priors.py). Hermetic, synthetic composed-signatures only (hand-built
`strokeq`/`rel` relation lists) — Omniglot stays a scripts/ gate, pytest is synthetic, the
SAME discipline `tests/test_character_composition_migrated.py`/`tests/test_ink_decode_
migrated.py` already follow.

1. Hygiene (test_mine_rejects_non_background_alphabet) — mining a non-`background`-split
   alphabet name raises, BEFORE any file/graph access (the background-only hygiene gate).
2. Mining mechanics (test_accumulate_character_stats_counts_correctly) — the pure counting
   step on a hand-built composed signature produces the exact expected histograms.
3. Peakedness (test_prior_diagnostics_peaked_vs_flat) — a heavily-skewed mined table reports
   LOW entropy / HIGH peakedness; a uniform one reports near-zero peakedness — the
   "intermediate gate" diagnostic the design asks to read BEFORE any accuracy number.
4. Separation (test_arrangement_log_prior_separates_plausible_from_implausible) — two
   composed signatures sharing the SAME stroke-identity multiset (a geometric/coverage TIE)
   but differing in "rel" bins: one matches the learned position mode, one is a bin the mined
   table never observed — the learned-prior candidate scores a HIGHER (less negative)
   log-prior, exactly the synthetic gate the launch instructions ask for.
5. Byte-identity at lambda=0 (test_lambda_zero_byte_identical_to_base_error) — the combined
   Term reduces to the base error term's OWN value regardless of the log-prior, verified via
   direct Term evaluation (no held-Argmin decision needed to see the identity).
6. End-to-end tie-break (test_combined_verdict_breaks_a_geometric_tie) — TWO candidates with
   an IDENTICAL (held-fixed) base error (a controlled tie, `Lit` stand-in) separated ONLY by
   `arrangement_log_prior` under `lam>0`: the held Argmin picks the candidate the learned
   prior favours; `lam=0` reproduces the tie (both candidates score identically, the
   fallback `shortlist[0]` wins) — the additivity/control-reproduction discipline.
7. Persist/load round-trip (test_persist_and_load_round_trip) — `teach()`-installed
   `SpatialPrior` nodes read back via `load_spatial_priors` reproduce the mined histograms
   exactly (the "seed byproduct" pathway, mechanical graph read-back).
8. Source audit (test_no_python_decision_source_audit) — `domains/spatial_priors.py` contains
   no Python argmin/argmax/sort-by-score/branch-on-computed-score outside the documented
   mechanical-staging functions (`arrangement_log_prior`'s own lookup+sum is a VALUE
   computation, never a comparison between candidates)."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytest.importorskip("substrate_rs")

import substrate_rs as srs

from domains import spatial_priors as sp

ROOT = Path(__file__).resolve().parent.parent


# --------------------------------------------------------------------------- #
#  1. HYGIENE
# --------------------------------------------------------------------------- #
def test_mine_rejects_non_background_alphabet():
    with pytest.raises(AssertionError, match="hygiene violation"):
        sp.mine_spatial_priors(object(), {"turn_bins": 12}, ["definitely_not_a_real_alphabet_xyz"],
                                ["01"])


def test_mine_split_is_a_module_constant():
    # Hygiene is a CONSTANT, never a caller-supplied flag prone to misuse.
    assert sp.MINE_SPLIT == "background"


# --------------------------------------------------------------------------- #
#  2. MINING MECHANICS
# --------------------------------------------------------------------------- #
def _composed(strokeq_rel_pairs) -> list:
    """Hand-build a minimal composed signature: `strokeq_rel_pairs` = [(name, (dx,dy,do,ds)), ...]
    in draw order k=0..n-1."""
    sig = []
    for k, (name, rel) in enumerate(strokeq_rel_pairs):
        sig.append(["strokeq", k, name])
        sig.append(["rel", k, *rel])
    return sig


def test_accumulate_character_stats_counts_correctly():
    from collections import defaultdict
    pc = defaultdict(lambda: {d: defaultdict(int) for d in sp.DIMS})
    pt = defaultdict(int)
    tc = defaultdict(lambda: {d: defaultdict(int) for d in sp.DIMS})
    tt = defaultdict(int)
    turn_bins = 12

    sig = _composed([("A", (1, 2, 3, 4)), ("B", (5, 6, -2, 1))])
    sp._accumulate_character_stats(sig, pc, pt, tc, tt, turn_bins)

    assert pt["A"] == 1 and pt["B"] == 1
    assert pc["A"]["dx"][1] == 1 and pc["A"]["dy"][2] == 1
    assert pc["A"]["do"][3] == 1 and pc["A"]["ds"][4] == 1
    assert pc["B"]["dx"][5] == 1 and pc["B"]["do"][-2] == 1

    # ONE transition A->B: dx=5-1=4, dy=6-2=4, do=wrap(-2-3,12), ds=1-4=-3.
    assert tt["A"] == 1 and "B" not in tt
    assert tc["A"]["dx"][4] == 1
    assert tc["A"]["dy"][4] == 1
    assert tc["A"]["ds"][-3] == 1
    expected_do = sp.cc._wrap_signed_bin(-2 - 3, turn_bins)
    assert tc["A"]["do"][expected_do] == 1

    # A SECOND character reusing the SAME identities accumulates (pooling across characters).
    sig2 = _composed([("A", (1, 2, 3, 4))])
    sp._accumulate_character_stats(sig2, pc, pt, tc, tt, turn_bins)
    assert pt["A"] == 2 and pc["A"]["dx"][1] == 2


# --------------------------------------------------------------------------- #
#  3. PEAKEDNESS DIAGNOSTIC
# --------------------------------------------------------------------------- #
def test_prior_diagnostics_peaked_vs_flat():
    peaked = {"position_counts": {"A": {"dx": {0: 100}, "dy": {0: 100}, "do": {0: 100}, "ds": {0: 100}}},
              "position_totals": {"A": 100},
              "transition_counts": {}, "transition_totals": {}}
    flat = {"position_counts": {"A": {"dx": {0: 25, 1: 25, 2: 25, 3: 25}, "dy": {0: 100},
                                       "do": {0: 100}, "ds": {0: 100}}},
            "position_totals": {"A": 100},
            "transition_counts": {}, "transition_totals": {}}

    diag_peaked = sp.prior_diagnostics(peaked)
    diag_flat = sp.prior_diagnostics(flat)
    # A single-bin histogram has zero entropy/undefined max-entropy -> peakedness pinned at 1.0.
    assert diag_peaked["mean_peakedness"] == pytest.approx(1.0)
    # The flat "dx" row (4 equally-likely bins) has ZERO peakedness (entropy == max entropy).
    dx_row = next(r for r in diag_flat["rows"] if r["dim"] == "dx")
    assert dx_row["peakedness"] == pytest.approx(0.0, abs=1e-9)
    assert diag_flat["mean_peakedness"] < diag_peaked["mean_peakedness"]


# --------------------------------------------------------------------------- #
#  4. SEPARATION — the launch instructions' own synthetic gate: "two candidates geometrically
#     tied ... separated only by arrangement plausibility under the learned priors (build the
#     prior nodes by hand in the test)."
# --------------------------------------------------------------------------- #
def _hand_built_priors(grid=6, turn_bins=12, scale_bins=6):
    """A hand-built mined table (no real mining): quantum "A" is ALWAYS observed at rel bin
    (1, 1, 0, 3) in the background data (peaked position prior); nothing else is ever seen at
    that identity."""
    position_counts = {"A": {"dx": {1: 50}, "dy": {1: 50}, "do": {0: 50}, "ds": {3: 50}}}
    position_totals = {"A": 50}
    transition_counts, transition_totals = {}, {}
    return {"position_counts": position_counts, "position_totals": position_totals,
            "transition_counts": transition_counts, "transition_totals": transition_totals,
            "_position_global": sp._global_histograms(position_counts),
            "_transition_global": sp._global_histograms(transition_counts)}


def test_arrangement_log_prior_separates_plausible_from_implausible():
    priors = _hand_built_priors()
    plausible = _composed([("A", (1, 1, 0, 3))])          # matches the learned mode exactly.
    implausible = _composed([("A", (5, 5, 5, 0))])         # a bin NEVER observed for "A".

    logp_good = sp.arrangement_log_prior(plausible, priors, grid=6, turn_bins=12, scale_bins=6)
    logp_bad = sp.arrangement_log_prior(implausible, priors, grid=6, turn_bins=12, scale_bins=6)
    assert logp_good > logp_bad


# --------------------------------------------------------------------------- #
#  5. BYTE-IDENTITY AT lambda=0
# --------------------------------------------------------------------------- #
def test_lambda_zero_byte_identical_to_base_error():
    s = srs.Substrate()
    native = s._inner
    base = {"type": "Lit", "value": 3.75}
    term0 = sp.spatial_prior_plus_marginal_term(base, log_prior_value=-999.0, lam=0.0)
    term_nonzero = sp.spatial_prior_plus_marginal_term(base, log_prior_value=-999.0, lam=1.0)
    v0 = native.evaluate(term0, {})
    v_nonzero = native.evaluate(term_nonzero, {})
    v_base = native.evaluate(base, {})
    assert v0 == pytest.approx(v_base)
    assert v_nonzero != pytest.approx(v_base)


# --------------------------------------------------------------------------- #
#  6. END-TO-END TIE-BREAK
# --------------------------------------------------------------------------- #
def test_combined_verdict_breaks_a_geometric_tie():
    priors = _hand_built_priors()
    plausible = _composed([("A", (1, 1, 0, 3))])
    implausible = _composed([("A", (5, 5, 5, 0))])
    candidate_composed = [plausible, implausible]

    def _score(ci: int, lam: float) -> float:
        native = srs.Substrate()._inner
        logp = sp.arrangement_log_prior(candidate_composed[ci], priors, grid=6, turn_bins=12,
                                         scale_bins=6)
        # A controlled TIE: the base error is IDENTICAL for both candidates (a Lit stand-in,
        # per this module's own docstring — isolates the prior's separating power).
        term = sp.spatial_prior_plus_marginal_term({"type": "Lit", "value": 0.0}, logp, lam)
        return float(native.evaluate(term, {}))

    # lam=0: both candidates score IDENTICALLY (the tie is real, not hidden by the prior).
    assert _score(0, 0.0) == pytest.approx(_score(1, 0.0))
    # lam=1: candidate 0 (the plausible arrangement) scores LOWER (better, Argmin convention).
    assert _score(0, 1.0) < _score(1, 1.0)

    # Now the SAME thing through the actual multi-candidate combinator + held Argmin.
    native = srs.Substrate()._inner

    def _argmin_pairs_term(pairs):
        return {"type": "Argmin", "source": {"type": "Lit", "value": pairs}, "var_name": "c",
                "value": {"type": "IndexAt", "seq": {"type": "Var", "name": "c"},
                          "index": {"type": "Lit", "value": 0}}, "default": None}

    pairs = [(_score(ci, 1.0), ci) for ci in (0, 1)]
    winner = native.evaluate(_argmin_pairs_term(pairs), {})
    assert winner is not None and int(winner[1]) == 0


# --------------------------------------------------------------------------- #
#  7. PERSIST / LOAD ROUND-TRIP
# --------------------------------------------------------------------------- #
def test_persist_and_load_round_trip(tmp_path):
    s = srs.Substrate()
    from collections import defaultdict
    pc = defaultdict(lambda: {d: defaultdict(int) for d in sp.DIMS})
    pt = defaultdict(int)
    tc = defaultdict(lambda: {d: defaultdict(int) for d in sp.DIMS})
    tt = defaultdict(int)
    sig = _composed([("Q1", (2, 2, 1, 1)), ("Q2", (4, 4, -1, 2))])
    sp._accumulate_character_stats(sig, pc, pt, tc, tt, turn_bins=12)
    mined = {
        "position_counts": {n: {d: dict(c) for d, c in dm.items()} for n, dm in pc.items()},
        "position_totals": dict(pt),
        "transition_counts": {n: {d: dict(c) for d, c in dm.items()} for n, dm in tc.items()},
        "transition_totals": dict(tt),
        "n_chars": 1, "turn_bins": 12, "grid": 6, "scale_bins": 6,
    }
    res = sp.persist_spatial_priors(s, mined, category="spatial_priors_test", seeds_dir=tmp_path)
    assert res["installed"] == len(mined["position_counts"]) + len(mined["transition_counts"])

    loaded = sp.load_spatial_priors(s)
    assert loaded["position_totals"] == mined["position_totals"]
    assert loaded["position_counts"]["Q1"]["dx"] == mined["position_counts"]["Q1"]["dx"]
    assert loaded["transition_totals"] == mined["transition_totals"]
    seed_path = tmp_path / "spatial_priors_test.json"
    assert seed_path.exists()


# --------------------------------------------------------------------------- #
#  8. SOURCE AUDIT — no Python argmin/argmax/sort-over-scores outside the documented
#     mechanical-staging functions.
# --------------------------------------------------------------------------- #
def test_no_python_decision_source_audit():
    src = (ROOT / "domains" / "spatial_priors.py").read_text()
    for pattern in (r"\bnp\.argmax\b", r"\bnp\.argmin\b", r"\bbuiltins\.max\(.*key=",
                    r"^\s*max\(.*key=", r"^\s*min\(.*key="):
        assert not re.search(pattern, src, re.MULTILINE), f"found a Python decision: {pattern}"


# =============================================================================================#
#  RUN 22 — FINE-KEYED CONDITIONING (git show -s d46ac9b3, run 21's diagnosis: the coarse
#  `strokeq`-keyed position table collapsed to ONE identity carrying 14,675/14,676 background
#  observations). Additive: every test above still exercises the byte-identical coarse-only
#  path; these exercise the NEW fine-identity machinery in isolation, hermetic/synthetic only.
# =============================================================================================#
def _line_points(x0=0.0, y0=0.0, dx=1.0, dy=0.0, n=6) -> list:
    return [[x0 + dx * t / (n - 1), y0 + dy * t / (n - 1)] for t in range(n)]


_BENT = [[0.0, 0.0], [0.3, 0.05], [0.6, 0.3], [1.0, 1.0]]


# --------------------------------------------------------------------------- #
#  9. HYGIENE — the fine miner asserts the SAME background-only gate.
# --------------------------------------------------------------------------- #
def test_mine_fine_rejects_non_background_alphabet():
    with pytest.raises(AssertionError, match="hygiene violation"):
        sp.mine_spatial_priors_fine(object(), {"turn_bins": 12},
                                     ["definitely_not_a_real_alphabet_xyz"], ["01"])


# --------------------------------------------------------------------------- #
#  10. FINE IDENTITY KEY — pose-invariant (same shape, different position/orientation/scale
#      -> the SAME key), shape-sensitive (a genuinely different shape -> a different key).
# --------------------------------------------------------------------------- #
def test_fine_identity_key_invariant_to_pose_but_sensitive_to_shape():
    native = srs.Substrate()._inner
    straight_here = _line_points(0.0, 0.0, 1.0, 0.0)
    straight_elsewhere = _line_points(5.0, 5.0, 0.0, 2.0)   # same SHAPE, different pos/orient/scale

    k1 = sp._fine_identity_key(native, straight_here, "line", segments=8, grid=8, scale_bins=8)
    k2 = sp._fine_identity_key(native, straight_elsewhere, "line", segments=8, grid=8, scale_bins=8)
    k3 = sp._fine_identity_key(native, _BENT, "line", segments=8, grid=8, scale_bins=8)

    assert k1 == k2                       # invariant to pose
    assert k1 != k3                       # sensitive to a genuinely different shape
    assert k1.startswith("line::")        # coarse-name-prefixed, per this module's own docstring


# --------------------------------------------------------------------------- #
#  11. `_accumulate_character_stats` — the `identity_by_k` override (additive kwarg).
# --------------------------------------------------------------------------- #
def test_accumulate_character_stats_with_identity_by_k_override():
    from collections import defaultdict
    pc = defaultdict(lambda: {d: defaultdict(int) for d in sp.DIMS})
    pt = defaultdict(int)
    tc = defaultdict(lambda: {d: defaultdict(int) for d in sp.DIMS})
    tt = defaultdict(int)
    turn_bins = 12

    # Two strokes sharing the SAME coarse identity "A" (run 21's collapse) but given DISTINCT
    # fine identities via the override.
    sig = _composed([("A", (1, 2, 3, 4)), ("A", (5, 6, -2, 1))])
    identity_by_k = {0: "A::finehash1", 1: "A::finehash2"}
    sp._accumulate_character_stats(sig, pc, pt, tc, tt, turn_bins, identity_by_k=identity_by_k)

    assert pt["A::finehash1"] == 1 and pt["A::finehash2"] == 1
    assert "A" not in pt                      # the coarse name is never used as a key when
                                               # identity_by_k is supplied.
    assert tt["A::finehash1"] == 1            # the transition is keyed on the PREDECESSOR's
                                               # own fine identity.


# --------------------------------------------------------------------------- #
#  12. FINE IDENTITY DIAGNOSTICS — diversity + dominance.
# --------------------------------------------------------------------------- #
def test_fine_identity_diagnostics_reports_diversity_and_dominance():
    mined_fine = {"position_counts": {"a::1": {}, "a::2": {}, "b::1": {}},
                  "position_totals": {"a::1": 900, "a::2": 50, "b::1": 50}}
    diag = sp.fine_identity_diagnostics(mined_fine, min_obs=10)
    assert diag["n_distinct_fine_keys"] == 3
    assert diag["n_fine_keys_with_min_obs"] == 3
    assert diag["total_observations"] == 1000
    assert diag["dominant_key_share"] == pytest.approx(0.9)

    # A key BELOW min_obs is counted in n_distinct but not n_fine_keys_with_min_obs.
    sparse = {"position_counts": {"a::1": {}, "a::2": {}},
              "position_totals": {"a::1": 900, "a::2": 3}}
    diag2 = sp.fine_identity_diagnostics(sparse, min_obs=10)
    assert diag2["n_distinct_fine_keys"] == 2
    assert diag2["n_fine_keys_with_min_obs"] == 1


# --------------------------------------------------------------------------- #
#  13. FINE KEY COVERAGE — TEST-time recall against a mined position_totals table.
# --------------------------------------------------------------------------- #
def test_fine_key_coverage_measures_recall_against_position_totals():
    native = srs.Substrate()._inner
    straight = _line_points(0.0, 0.0, 1.0, 0.0)
    key_straight = sp._fine_identity_key(native, straight, "line", segments=8, grid=8, scale_bins=8)
    position_totals = {key_straight: 50}      # only the "straight" fine key is well-observed
    stroke_points_by_char = [[(straight, "line")], [(_BENT, "line")]]

    cov = sp.fine_key_coverage(native, stroke_points_by_char, position_totals, segments=8,
                                grid=8, scale_bins=8, min_obs=10)
    assert cov["n_total_strokes"] == 2
    assert cov["n_covered"] == 1
    assert cov["coverage"] == pytest.approx(0.5)


# --------------------------------------------------------------------------- #
#  14. THE PRE-REGISTERED BRANCH VERDICT — STOP on ANY of the three failing diagnostics.
# --------------------------------------------------------------------------- #
def test_fine_prior_branch_verdict_stops_on_any_failing_diagnostic():
    good_diversity = {"n_fine_keys_with_min_obs": 25}
    bad_diversity = {"n_fine_keys_with_min_obs": 5}
    peaked = {"mean_peakedness": 0.5}
    flat = {"mean_peakedness": 0.05}
    covered = {"coverage": 0.6}
    uncovered = {"coverage": 0.1}

    v = sp.fine_prior_branch_verdict(good_diversity, peaked, covered)
    assert v["proceed_to_accuracy"] is True
    assert not (v["fails_diversity"] or v["fails_peakedness"] or v["fails_coverage"])

    v2 = sp.fine_prior_branch_verdict(bad_diversity, peaked, covered)
    assert v2["proceed_to_accuracy"] is False and v2["fails_diversity"]

    v3 = sp.fine_prior_branch_verdict(good_diversity, flat, covered)
    assert v3["proceed_to_accuracy"] is False and v3["fails_peakedness"]

    v4 = sp.fine_prior_branch_verdict(good_diversity, peaked, uncovered)
    assert v4["proceed_to_accuracy"] is False and v4["fails_coverage"]


# --------------------------------------------------------------------------- #
#  15. `arrangement_log_prior_fine` — USES the fine table when well-observed (the fine table's
#      OWN preference wins, even when it CONTRADICTS the coarse table).
# --------------------------------------------------------------------------- #
def test_arrangement_log_prior_fine_uses_fine_table_when_well_observed():
    native = srs.Substrate()._inner
    straight = _line_points(0.0, 0.0, 1.0, 0.0)
    fine_key = sp._fine_identity_key(native, straight, "A", segments=8, grid=8, scale_bins=8)

    priors_fine = {
        "position_counts": {fine_key: {"dx": {1: 50}, "dy": {1: 50}, "do": {0: 50}, "ds": {3: 50}}},
        "position_totals": {fine_key: 50},
        "transition_counts": {}, "transition_totals": {},
    }
    priors_coarse = _hand_built_priors()
    # The COARSE table says the OPPOSITE bin is plausible for "A" -- proves the FINE table,
    # not the coarse fallback, actually decides the score below.
    priors_coarse["position_counts"]["A"] = {"dx": {5: 50}, "dy": {5: 50}, "do": {5: 50}, "ds": {0: 50}}
    priors_coarse["_position_global"] = sp._global_histograms(priors_coarse["position_counts"])

    stroke_points = [(straight, "A")]
    matches_fine = _composed([("A", (1, 1, 0, 3))])       # the FINE table's own mode
    matches_coarse = _composed([("A", (5, 5, 5, 0))])     # the COARSE table's own mode

    logp_fine = sp.arrangement_log_prior_fine(matches_fine, stroke_points, priors_fine,
                                               priors_coarse, native=native, grid=6, turn_bins=12,
                                               scale_bins=6, segments=8, min_obs=10)
    logp_coarse = sp.arrangement_log_prior_fine(matches_coarse, stroke_points, priors_fine,
                                                 priors_coarse, native=native, grid=6, turn_bins=12,
                                                 scale_bins=6, segments=8, min_obs=10)
    assert logp_fine > logp_coarse


# --------------------------------------------------------------------------- #
#  16. `arrangement_log_prior_fine` — BACKS OFF to the coarse table when the fine identity is
#      UNDER-observed (below `min_obs`).
# --------------------------------------------------------------------------- #
def test_arrangement_log_prior_fine_backs_off_to_coarse_when_underpopulated():
    native = srs.Substrate()._inner
    straight = _line_points(0.0, 0.0, 1.0, 0.0)
    fine_key = sp._fine_identity_key(native, straight, "A", segments=8, grid=8, scale_bins=8)

    priors_fine = {
        "position_counts": {fine_key: {"dx": {9: 3}, "dy": {9: 3}, "do": {9: 3}, "ds": {9: 3}}},
        "position_totals": {fine_key: 3},          # BELOW min_obs=10 -> must back off.
        "transition_counts": {}, "transition_totals": {},
    }
    priors_coarse = _hand_built_priors()             # "A" always at (1,1,0,3) in the coarse table.

    stroke_points = [(straight, "A")]
    matches_coarse = _composed([("A", (1, 1, 0, 3))])
    mismatches_coarse = _composed([("A", (5, 5, 5, 0))])

    logp_good = sp.arrangement_log_prior_fine(matches_coarse, stroke_points, priors_fine,
                                               priors_coarse, native=native, grid=6, turn_bins=12,
                                               scale_bins=6, segments=8, min_obs=10)
    logp_bad = sp.arrangement_log_prior_fine(mismatches_coarse, stroke_points, priors_fine,
                                              priors_coarse, native=native, grid=6, turn_bins=12,
                                              scale_bins=6, segments=8, min_obs=10)
    assert logp_good > logp_bad               # backed off to the COARSE table's own preference.


# --------------------------------------------------------------------------- #
#  17. PERSIST / LOAD ROUND-TRIP — the fine table, coexisting cleanly with the coarse reader.
# --------------------------------------------------------------------------- #
def test_persist_and_load_fine_round_trip(tmp_path):
    s = srs.Substrate()
    mined_fine = {
        "position_counts": {"line::abc123": {"dx": {1: 5}}},
        "position_totals": {"line::abc123": 5},
        "transition_counts": {"line::abc123": {"dx": {2: 3}}},
        "transition_totals": {"line::abc123": 3},
        "fine_to_coarse": {"line::abc123": "line"},
    }
    res = sp.persist_spatial_priors_fine(s, mined_fine, category="spatial_priors_fine_test",
                                          seeds_dir=tmp_path)
    assert res["installed"] == 2

    loaded = sp.load_spatial_priors_fine(s)
    assert loaded["position_totals"]["line::abc123"] == 5
    assert loaded["transition_totals"]["line::abc123"] == 3
    assert loaded["fine_to_coarse"]["line::abc123"] == "line"

    # Coexists cleanly on the same SpatialPrior node type -- the COARSE reader sees nothing here.
    coarse_loaded = sp.load_spatial_priors(s)
    assert "line::abc123" not in coarse_loaded["position_totals"]
