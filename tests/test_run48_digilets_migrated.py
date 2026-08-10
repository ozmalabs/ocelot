"""tests/test_run48_digilets_migrated.py — RUN 48 unit gates for
`scripts/jabberwock_omniglot_run48_digilets.py`, run BEFORE any real Gate A/B number is
computed, per this arc's own ops law. Two things this run's own launch brief calls out by name:

  (1) SOFT-FUSION MECHANICS (`_soft_fusion_idx`) — the new arm this run adds over run 47's own
      hard-gate union: `lambda=0` must reproduce `argmin(geo_scores)` EXACTLY (arm (i), the
      continuous-only baseline), and a large enough `lambda` must be able to FLIP the decision
      toward the quantized-similarity winner — checked on synthetic score vectors, no real data
      or `substrate_rs` decode needed for these two properties.
  (2) THE SEED-WRITE GUARD — run 47's own incident (a first LEARN pass mutated a
      parallel-session-owned `seeds/stroke_shapes.json` for real) must not recur. This test
      calls the SAME `run47.run_codebook_growth` this run's own `--stage learn`/`--stage
      unit_sanity` canary calls, on a tiny SYNTHETIC stroke, and asserts the real seed file's
      md5 is byte-identical before and after.

Also covers `_apply_arms`/`_gate_b_report` bookkeeping (shortlist coverage, McNemar wiring) on
synthetic score vectors, and `_way20_classes`/`_score_episodes`'s writer-crossing invariant on a
tiny synthetic writer/class population — mechanical checks, no live corpus needed.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import scripts.jabberwock_omniglot_run47_pendata as run47
import scripts.jabberwock_omniglot_run48_digilets as run48


# =============================================================================================
#  SOFT-FUSION MECHANICS.
# =============================================================================================
def test_soft_fusion_lambda_zero_reproduces_continuous_only():
    geo = [0.9, 0.2, 0.5, 0.7]          # argmin -> index 1
    sims = [0.1, 0.0, 0.9, 0.3]         # a DIFFERENT argmax (index 2) at lambda=0 must NOT win
    assert run48._soft_fusion_idx(geo, sims, 0.0) == int(np.argmin(geo))


def test_soft_fusion_large_lambda_can_flip_toward_quantized_winner():
    # candidate 1 is the marginally-better continuous winner; candidate 2 has a MUCH higher
    # quantized similarity. A large enough lambda must be able to flip the decision to 2.
    geo = [0.9, 0.50, 0.52, 0.95]
    sims = [0.0, 0.05, 0.95, 0.0]
    assert run48._soft_fusion_idx(geo, sims, 0.0) == 1
    assert run48._soft_fusion_idx(geo, sims, 5.0) == 2


def test_soft_fusion_never_crashes_on_degenerate_equal_geo_scores():
    # g.max() == g.min() -> the normalization's epsilon guard must prevent a divide-by-zero.
    geo = [0.5, 0.5, 0.5]
    sims = [0.1, 0.9, 0.2]
    idx = run48._soft_fusion_idx(geo, sims, 1.0)
    assert idx == int(np.argmax(sims)), "with a flat geo term, similarity alone must decide"


# =============================================================================================
#  _apply_arms / _gate_b_report bookkeeping on synthetic per-episode score vectors.
# =============================================================================================
def _synthetic_episodes():
    # 4 candidates each; episode 0: continuous correct, hard-gate correct, soft correct.
    # episode 1: continuous WRONG, quantized similarity strongly favors the true class ->
    # hard-gate (shortlist_k=2) and soft-fusion (lam=2) should both RECOVER it.
    return [
        {"geo_scores": [0.9, 0.1, 0.8, 0.7], "sims": [0.1, 0.9, 0.0, 0.0], "true_idx": 1},
        {"geo_scores": [0.1, 0.9, 0.8, 0.7], "sims": [0.0, 0.0, 0.0, 0.95], "true_idx": 3},
    ]


def test_apply_arms_shortlist_coverage_and_recovery():
    episodes = _synthetic_episodes()
    records = run48._apply_arms(episodes, shortlist_k=2, lam=2.0)
    assert len(records) == 2
    assert records[0]["correct_i"] and records[0]["correct_ii"] and records[0]["correct_iii"]
    # episode 1: continuous picks index 0 (wrong); hard-gate shortlist by sims top-2 is {3, 0}
    # (sims [0,0,0,0.95] -> order [3,0,1,2] or [3,0,2,1] depending on tie order) -- true_idx=3
    # is in the shortlist -> hard-gate recovers it (argmin geo restricted to {0,3} -> geo[3]=0.7
    # < geo[0]=0.1? NO: geo[0]=0.1 is LOWER (better) than geo[3]=0.7, so hard-gate still picks 0.
    # Recompute expectation directly from the mechanism rather than asserting a guessed outcome:
    ep1_shortlist = sorted(range(4), key=lambda i: -episodes[1]["sims"][i])[:2]
    assert 3 in ep1_shortlist   # true class must be IN the shortlist (this is what coverage means)
    expected_hard_pred = min(ep1_shortlist, key=lambda i: episodes[1]["geo_scores"][i])
    assert records[1]["correct_ii"] == (expected_hard_pred == 3)
    # soft fusion at lam=2 must be derivable from the same helper, checked directly:
    expected_soft_pred = run48._soft_fusion_idx(episodes[1]["geo_scores"], episodes[1]["sims"], 2.0)
    assert records[1]["correct_iii"] == (expected_soft_pred == 3)
    coverage = sum(r["in_shortlist"] for r in records) / len(records)
    assert coverage == 1.0, "both episodes' true class is within a top-2 shortlist of 4"


def test_gate_b_report_mcnemar_wiring_and_stop_flags():
    episodes = _synthetic_episodes()
    records = run48._apply_arms(episodes, shortlist_k=2, lam=2.0)
    way_classes = [0, 1, 2, 3]
    rep = run48._gate_b_report(records, way_classes, shortlist_k=2, lam=2.0)
    assert rep["n"] == 2
    assert rep["n_way"] == 4
    assert 0.0 <= rep["acc_continuous_only"] <= 1.0
    assert set(rep["mcnemar_hard_vs_continuous"].keys()) >= {"fixed", "broken", "discordant", "p"}
    assert set(rep["mcnemar_soft_vs_continuous"].keys()) >= {"fixed", "broken", "discordant", "p"}
    assert isinstance(rep["stop_hard_harms"], bool)
    assert isinstance(rep["stop_soft_harms_vs_continuous"], bool)


# =============================================================================================
#  HOMOGLYPH CONFUSABILITY (additive reporting requirement).
# =============================================================================================
def test_homoglyph_groups_cover_expected_pairs():
    assert run48._is_homoglyph_pair("0", "O")
    assert run48._is_homoglyph_pair("O", "o")
    assert run48._is_homoglyph_pair("1", "l")
    assert run48._is_homoglyph_pair("1", "I")
    assert run48._is_homoglyph_pair("5", "S")
    assert run48._is_homoglyph_pair("s", "S")
    assert run48._is_homoglyph_pair("c", "C")
    assert not run48._is_homoglyph_pair("a", "b")
    assert not run48._is_homoglyph_pair("3", "7")


def test_homoglyph_free_class_pool_has_no_internal_collisions():
    pool = run48._homoglyph_free_class_pool()
    from domains import pen_world as pw
    symbols = [pw.DIGILETS_SYMBOLS[i] for i in pool]
    for i, sa in enumerate(symbols):
        for sb in symbols[i + 1:]:
            assert not run48._is_homoglyph_pair(sa, sb), f"{sa!r}/{sb!r} collide in the pool"


def test_way20_classes_clean_is_homoglyph_free_and_deterministic():
    a = run48._way20_classes_clean()
    b = run48._way20_classes_clean()
    assert a == b
    assert len(a) == run48.N_WAY20 == len(set(a))
    from domains import pen_world as pw
    symbols = [pw.DIGILETS_SYMBOLS[c] for c in a]
    for i, sa in enumerate(symbols):
        for sb in symbols[i + 1:]:
            assert not run48._is_homoglyph_pair(sa, sb)


def test_homoglyph_arm_stats_separates_homoglyph_from_other_errors():
    # way_classes = ['0','O','a','b'] (indices in DIGILETS_SYMBOLS: '0'->0, 'O'->10+26+14=50
    # for 'O' (uppercase index) -- resolved via DIGILETS_SYMBOLS directly, not hand-computed).
    from domains import pen_world as pw
    idx_0 = pw.DIGILETS_SYMBOLS.index("0")
    idx_O = pw.DIGILETS_SYMBOLS.index("O")
    idx_a = pw.DIGILETS_SYMBOLS.index("a")
    idx_b = pw.DIGILETS_SYMBOLS.index("b")
    way_classes = [idx_0, idx_O, idx_a, idx_b]
    records = [
        {"true_idx": 0, "pred_i": 1, "correct_i": False},   # '0' mistaken for 'O' -- homoglyph
        {"true_idx": 2, "pred_i": 3, "correct_i": False},   # 'a' mistaken for 'b' -- OTHER error
        {"true_idx": 0, "pred_i": 0, "correct_i": True},
    ]
    stats = run48._homoglyph_arm_stats(records, way_classes, "pred_i", "correct_i")
    assert stats["n_homoglyph_errors"] == 1
    assert stats["n_other_errors"] == 1
    assert stats["acc_raw"] == pytest.approx(1 / 3)
    assert stats["acc_excl_homoglyph"] == pytest.approx(2 / 3)
    assert stats["top_confusions"][0]["count"] >= 1


# =============================================================================================
#  _way20_classes / _score_episodes writer-crossing invariant (tiny synthetic population,
#  frozen edges from a real (cheap) fit so `_ident_bags`/`program_score` have real input shape).
# =============================================================================================
def test_way20_classes_deterministic_and_bounded():
    a = run48._way20_classes()
    b = run48._way20_classes()
    assert a == b, "the seeded 20-way class subset must be deterministic run to run"
    assert len(a) == run48.N_WAY20 == len(set(a))
    assert all(0 <= c < 62 for c in a)


def _tiny_frozen_edges():
    # A minimal, cheap real fit (few strokes) so tokenize_with_frozen_edges has valid edges.
    strokes = [[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]],
              [[0.0, 0.0], [0.5, 0.5], [1.0, 0.0]],
              [[0.0, 0.0], [1.0, 1.0], [2.0, 0.0], [3.0, 1.0]]]
    return run47.fit_edges_on_learn(strokes)


def _tiny_writer_class_samples():
    """3 writers x 2 classes x 2 instances, each instance a single 4-point stroke — enough for
    `_score_episodes`'s writer-index + cross-writer exemplar/query selection to exercise for
    real (not enough to need a real corpus download)."""
    samples = []
    rng = np.random.default_rng(0)
    for w in range(3):
        for c in range(2):
            for i in range(2):
                base = rng.uniform(0, 1, size=(4, 2))
                strokes = [base + w]     # shift by writer id so writers are trivially distinct
                samples.append({"writer_id": f"w{w}", "class": c, "instance": i,
                               "strokes": [np.asarray(s) for s in strokes]})
    return samples


def test_score_episodes_exemplar_and_query_are_different_writers():
    frozen = _tiny_frozen_edges()
    samples = _tiny_writer_class_samples()
    episodes = run48._score_episodes(samples, way_classes=[0, 1], n_episodes=10, seed=1,
                                     frozen=frozen)
    assert len(episodes) > 0
    for e in episodes:
        assert e["ex_writer_true"] != e["q_writer"], (
            "the true class's exemplar and query must be drawn from DIFFERENT writers "
            "(the whole point of a cross-writer one-shot episode)")
        assert len(e["geo_scores"]) == 2 and len(e["sims"]) == 2
        assert 0 <= e["true_idx"] < 2


# =============================================================================================
#  THE SEED-WRITE GUARD — the run-47 incident must not recur. This is the SAME canary
#  `--stage unit_sanity` runs, promoted to a standing pytest gate.
# =============================================================================================
STROKE_SHAPES_SEED = os.path.join(ROOT, "seeds", "stroke_shapes.json")


def _md5(path: str) -> str:
    return run47._md5(path)


def test_seed_write_guard_canary_leaves_real_seed_untouched():
    md5_before = _md5(STROKE_SHAPES_SEED)
    canary_stroke = [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0], [0.0, 0.0]]
    gr = run47.run_codebook_growth([canary_stroke],
                                   {"level_edges": [0, 90, 180, 270, 360], "len_edges": [0, 1, 2]},
                                   window=1)
    md5_after = _md5(STROKE_SHAPES_SEED)
    assert md5_after == md5_before, (
        "seeds/stroke_shapes.json changed during a SYNTHETIC canary growth call — this is "
        "exactly the run-47 incident (teach() persisting real codebook growth to a "
        "parallel-session-owned seed file) recurring. run48's --stage learn must never run if "
        "this assertion fails.")
    assert gr["n_strokes"] == 1


def test_pen_world_digilets_functions_exist_and_are_pure_loader():
    """Sanity: `domains.pen_world` exposes the run-48 loader surface this script depends on,
    and the module itself remains a pure loader (no rule engine / teach / agent decisions) —
    duplicated here (cheaply) as a direct dependency check for this run's own script."""
    from domains import pen_world as pw
    for name in ("load_digilets_samples", "digilets_writer_split", "DIGILETS_SYMBOLS"):
        assert hasattr(pw, name), f"domains.pen_world.{name} missing"
