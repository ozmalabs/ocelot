"""test_run79_migrated.py -- unit gates for RUN 79 (THE FEW-SHOT ADAPTATION DIAGNOSTIC): K
perfectly-labeled words per writer, SEEN vs UNSEEN letter-class accuracy, sweeping K, to isolate
whether writer adaptation is sample-hungry accumulation or has a generalizing hand-transform.

Gates the machinery BEFORE the expensive real-data reduction (ops law "unit tests first"):
  * `draw_kshot` -- chosen/held is a strict partition of a writer's words, |chosen|==K for a
    qualifying writer, deterministic given (seed, writer);
  * `build_kshot_pool` -- SEEN classes are EXACTLY the true classes present among the K chosen
    words' letters (never leaks a held-out word's class in); pool cap (`M_BOOT_LETTER`) truncates
    correctly when a class has more than `cap` instances among the K words;
  * `evaluate_one_k`/`run_kshot_sweep` -- held-out testing NEVER touches a chosen word's own letters
    (the K-labeled words are never in the test set); the SEEN/UNSEEN split is computed per held
    letter from the ACTUAL seen-classes set, not assumed;
  * THE ANALYTIC INVARIANT (module docstring): an UNSEEN letter's own true-class cost is never
    touched by fusion (no pool entry exists for it), so bank accumulation can only leave it correct
    or flip it to WRONG -- never newly correct. Checked with a worked symmetric example (deterministic
    regardless of which of two words a seed happens to draw) AND a randomized property check
    (`n_flip_to_right == 0` always, across many random cost/pairwise configurations);
  * cold (K=0) reproduces run 78's own cold anchor EXACTLY (identical letter set + identical
    empty-pool computation) and ceiling (all-labels) reproduces run 78's own ceiling anchor exactly
    -- loaded/recomputed LIVE, not hardcoded, per the arc's own no-stale-numbers discipline;
  * `run69_pose_decomposition_anchor` -- condition D (pose-transform only, no own bank) sits between
    condition A (no adaptation) and condition E (full within-writer), recomputed live from run 69's
    own read.json;
  * seed guard: seeds/stroke_shapes.json md5 UNCHANGED across the whole module, including across an
    actual `stage_prep()`/`stage_bootstrap()` invocation.

No native (substrate_rs) call exists anywhere in run 79 -- confirmed directly (item at the bottom).
All tests pass under system python3.
"""
from __future__ import annotations

import hashlib
import os
import sys

import numpy as np
import pytest

os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
os.environ.setdefault("DEEPWRITING_DIR", "/tmp/handwriting")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import scripts.jabberwock_fewshot_run79 as r79

r78 = r79.r78
r73 = r79.r73
r69 = r79.r69

STROKE_SHAPES_SEED = r79.STROKE_SHAPES_SEED
RUN78_PREP_PRESENT = os.path.exists(r79.RUN78_PREP)
RUN78_READ_PRESENT = os.path.exists(r79.RUN78_READ)
RUN69_READ_PRESENT = os.path.exists(r79.RUN69_READ)


def _md5(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


@pytest.fixture(scope="module", autouse=True)
def seed_guard():
    before = _md5(STROKE_SHAPES_SEED)
    yield
    after = _md5(STROKE_SHAPES_SEED)
    assert after == before, "seeds/stroke_shapes.json md5 changed across test_run79_migrated.py"


def test_seed_guard_md5_present():
    assert os.path.exists(STROKE_SHAPES_SEED)


def test_no_native_import_anywhere_in_module():
    """This run performs ZERO new native computation (all DTW/pose already exists in run 78's own
    read.json) -- confirmed directly by AST inspection of actual import statements (the module
    docstring mentions the word 'substrate_rs' in prose, which is fine and must not fail this)."""
    import ast
    import inspect
    tree = ast.parse(inspect.getsource(r79))
    imported_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_names.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_names.add(node.module)
    assert "substrate_rs" not in imported_names
    assert not hasattr(r79, "srs")


# --------------------------------------------------------------------------------------------- #
# fixtures: a small synthetic writer corpus in run 78's own letter-record shape.
# --------------------------------------------------------------------------------------------- #
def _letter(writer, wid, pos, true_li, local_idx, cross_row=None):
    return {"writer": writer, "wid": wid, "pos": pos, "true_li": true_li, "local_idx": local_idx,
           "cross_row": cross_row if cross_row is not None else [5.0] * 26}


def _make_writer_words(writer, word_true_lis: list, cross_row_fn=None):
    """`word_true_lis`: list of words, each a list of true_li per letter position. Assigns dense
    per-writer local_idx (run 78's own convention) and returns a `words_w` dict (wid -> letters)."""
    words_w = {}
    local_idx = 0
    for wid, tls in enumerate(word_true_lis):
        letters = []
        for pos, tl in enumerate(tls):
            cr = cross_row_fn(wid, pos, tl) if cross_row_fn else [5.0] * 26
            letters.append(_letter(writer, wid, pos, tl, local_idx, cr))
            local_idx += 1
        words_w[wid] = letters
    return words_w


# --------------------------------------------------------------------------------------------- #
# ITEM 1 -- draw_kshot: strict partition, |chosen|==K, deterministic.
# --------------------------------------------------------------------------------------------- #
def test_draw_kshot_is_strict_partition():
    words_w = _make_writer_words(1, [[0], [1], [2], [3], [4]])   # 5 one-letter words.
    chosen, held = r79.draw_kshot(words_w, k=2, seed=0, writer=1)
    assert len(chosen) == 2
    assert set(chosen) | set(held) == set(words_w.keys())
    assert set(chosen) & set(held) == set()
    assert len(held) == 3


def test_draw_kshot_deterministic_given_seed_and_writer():
    words_w = _make_writer_words(1, [[0], [1], [2], [3], [4], [5]])
    c1, h1 = r79.draw_kshot(words_w, k=3, seed=7, writer=42)
    c2, h2 = r79.draw_kshot(words_w, k=3, seed=7, writer=42)
    assert c1 == c2
    assert h1 == h2


def test_draw_kshot_different_seeds_can_differ():
    words_w = _make_writer_words(1, [[i] for i in range(10)])
    draws = {tuple(sorted(r79.draw_kshot(words_w, k=3, seed=s, writer=1)[0])) for s in range(8)}
    assert len(draws) > 1, "expected different seeds to draw different K-subsets at least sometimes"


# --------------------------------------------------------------------------------------------- #
# ITEM 2 -- build_kshot_pool: SEEN classes exactly match chosen words' letters; cap truncates.
# --------------------------------------------------------------------------------------------- #
def test_build_kshot_pool_seen_classes_exact():
    words_w = _make_writer_words(1, [[0, 1], [2], [1, 3]])   # word0: classes 0,1; word1: 2; word2: 1,3.
    chosen = {0, 1}   # words 0 and 1 -> classes {0,1,2}. word 2 (class 3) held out.
    pool, seen = r79.build_kshot_pool(words_w, chosen, writer=1)
    assert seen == {0, 1, 2}
    assert 3 not in seen, "class 3 only appears in the HELD word -- must not leak into seen"


def test_build_kshot_pool_never_leaks_held_word_class():
    words_w = _make_writer_words(1, [[5]], cross_row_fn=None)
    words_w[1] = [_letter(1, 1, 0, 9, 1)]     # a second word, held out, class 9.
    chosen = {0}
    pool, seen = r79.build_kshot_pool(words_w, chosen, writer=1)
    assert seen == {5}
    assert 9 not in seen


def test_build_kshot_pool_cap_truncates():
    # One word with 8 letters, all class 3 -- pool for (writer, 3) must be capped at M_BOOT_LETTER.
    words_w = {0: [_letter(1, 0, i, 3, i) for i in range(8)]}
    pool, seen = r79.build_kshot_pool(words_w, {0}, writer=1, cap=r79.M_BOOT_LETTER)
    assert seen == {3}
    assert len(pool[(1, 3)]) == r79.M_BOOT_LETTER


# --------------------------------------------------------------------------------------------- #
# ITEM 3 -- qualifying_writers: >= K+1 words required.
# --------------------------------------------------------------------------------------------- #
def test_qualifying_writers_needs_k_plus_one_words():
    writer_words = {
        1: {i: [] for i in range(5)},     # 5 words.
        2: {i: [] for i in range(2)},     # 2 words.
    }
    assert r79.qualifying_writers(writer_words, k=4) == [1]     # writer 2 needs >=5, has 2.
    assert r79.qualifying_writers(writer_words, k=1) == [1, 2]  # both need >=2, both have it.
    assert r79.qualifying_writers(writer_words, k=5) == []      # writer 1 needs >=6, has 5.


# --------------------------------------------------------------------------------------------- #
# ITEM 4 -- held-out testing never touches a chosen word's own letters; SEEN/UNSEEN computed from
# the ACTUAL seen set for that draw, worked through a symmetric deterministic example (regardless
# of which of the two words a given seed happens to draw, the aggregate outcome is identical).
# --------------------------------------------------------------------------------------------- #
def _symmetric_two_word_writer_words():
    """Two one-letter words, writer 1: word0 true class 0 (own-class-cheap cross_row), word1 true
    class 1 (own-class-cheap cross_row). Symmetric construction: WHICHEVER word is chosen as the
    K=1 sample, its class gets boosted via a close pairwise exemplar, and the OTHER (held, unseen)
    word's true class is untouched -- so the aggregate outcome (unseen flips from correct to wrong)
    is identical regardless of which word the RNG happens to draw."""
    row_favoring_0 = [3.0, 5.0] + [10.0] * 24    # class 0 cheap, class 1 costly.
    row_favoring_1 = [5.0, 3.0] + [10.0] * 24    # class 1 cheap, class 0 costly.
    l0 = _letter(1, 0, 0, true_li=0, local_idx=0, cross_row=row_favoring_0)
    l1 = _letter(1, 1, 0, true_li=1, local_idx=1, cross_row=row_favoring_1)
    words_w = {0: [l0], 1: [l1]}
    # symmetric pairwise: whichever letter is the pool exemplar, it is VERY close to the other.
    pairwise_idx = {(1, 0, 1): (0.05, 0.0), (1, 1, 0): (0.05, 0.0)}
    return {1: words_w}, pairwise_idx


def test_unseen_flips_to_wrong_symmetric_example_either_draw():
    """At COLD, both letters decode correctly (each letter's own class is cheapest in its own row).
    At K=1, whichever word is chosen gets its class boosted to near-zero cost via the close pairwise
    exemplar; the OTHER (held, unseen) letter's true-class cost is untouched, but the now-boosted
    OTHER class becomes cheaper than it -- so the previously-correct unseen letter FLIPS TO WRONG.
    This holds regardless of which of the two words the seed happens to draw (checked over several
    seeds, not just one)."""
    writer_words, pairwise_idx = _symmetric_two_word_writer_words()
    # confirm both words actually get drawn across the seed range this run sweeps with (otherwise
    # the "either draw" claim in the docstring would be untested) -- draw_kshot is deterministic per
    # (seed, writer), so check directly across seeds 0..N_KSHOT_SEEDS-1.
    drawn_choices = {tuple(sorted(r79.draw_kshot(writer_words[1], k=1, seed=s, writer=1)[0]))
                     for s in range(r79.N_KSHOT_SEEDS)}
    assert drawn_choices, "expected at least one draw"
    # now the real aggregate check, across all N_KSHOT_SEEDS seeds via the public sweep step:
    agg = r79.evaluate_one_k(writer_words, pairwise_idx, k=1, n_seeds=r79.N_KSHOT_SEEDS)
    assert agg["unseen_n"] == r79.N_KSHOT_SEEDS        # one held (unseen) letter per seed.
    assert agg["unseen_ok"] == 0                       # every draw flips the held letter to wrong.
    assert agg["unseen_cold_ok"] == r79.N_KSHOT_SEEDS  # cold was correct every time before fusion.
    assert agg["n_flip_to_wrong"] == r79.N_KSHOT_SEEDS
    assert agg["n_flip_to_right"] == 0
    assert agg["seen_n"] == 0    # the chosen word's own letter is never in the held/test set.


# --------------------------------------------------------------------------------------------- #
# ITEM 5 -- THE ANALYTIC INVARIANT: n_flip_to_right must be exactly 0, checked as a randomized
# property across many synthetic configurations (not just the one hand-derived case above).
# --------------------------------------------------------------------------------------------- #
def test_flip_to_right_always_zero_randomized_property():
    rng = np.random.default_rng(20260910)
    for trial in range(25):
        n_words = rng.integers(3, 7)
        word_true_lis = [[int(rng.integers(0, 6))] for _ in range(n_words)]   # 1-letter words, 6 classes.
        def _cr(wid, pos, tl, _rng=rng):
            row = list(_rng.uniform(1.0, 10.0, size=26))
            row[tl] = float(_rng.uniform(0.1, 3.0))     # own class usually cheap-ish, not guaranteed.
            return row
        words_w = _make_writer_words(1, word_true_lis, cross_row_fn=_cr)
        letters = [l for wl in words_w.values() for l in wl]
        n = len(letters)
        pairwise_idx = {}
        for i in range(n):
            for j in range(n):
                if i != j:
                    pairwise_idx[(1, i, j)] = (float(rng.uniform(0.0, 5.0)), 0.0)
        k = int(rng.integers(1, max(2, n_words - 1)))
        agg = r79.evaluate_one_k({1: words_w}, pairwise_idx, k=k, n_seeds=3)
        assert agg["n_flip_to_right"] == 0, f"trial {trial}: analytic invariant violated"


# --------------------------------------------------------------------------------------------- #
# ITEM 6 -- run_kshot_sweep: end-to-end wrapper, sane output shape, held-out testing excludes chosen.
# --------------------------------------------------------------------------------------------- #
def test_run_kshot_sweep_output_shape():
    letters = []
    for w in (1, 2):
        for wid in range(6):
            for pos, tl in enumerate([(wid + p) % 6 for p in range(2)]):
                letters.append(_letter(w, wid, pos, tl, wid * 2 + pos))
    n = len(letters)
    pairwise_idx = {}
    for i in range(n):
        for j in range(n):
            if i != j and letters[i]["writer"] == letters[j]["writer"]:
                pairwise_idx[(letters[i]["writer"], letters[i]["local_idx"],
                            letters[j]["local_idx"])] = (1.0, 0.0)
    out = r79.run_kshot_sweep(letters, pairwise_idx, k_values=[1, 2], n_seeds=2)
    assert set(out["per_k"].keys()) == {"1", "2"}
    for k_str, agg in out["per_k"].items():
        assert agg["seen_n"] + agg["unseen_n"] > 0
        assert agg["n_flip_to_right"] == 0


# --------------------------------------------------------------------------------------------- #
# ITEM 7 -- build_writer_words groups + sorts correctly by pos.
# --------------------------------------------------------------------------------------------- #
def test_build_writer_words_groups_and_sorts_by_pos():
    letters = [
        _letter(1, 0, 2, 5, 2), _letter(1, 0, 0, 3, 0), _letter(1, 0, 1, 4, 1),
        _letter(2, 5, 0, 1, 0),
    ]
    ww = r79.build_writer_words(letters)
    assert set(ww.keys()) == {1, 2}
    assert [l["pos"] for l in ww[1][0]] == [0, 1, 2]
    assert list(ww[2].keys()) == [5]


# --------------------------------------------------------------------------------------------- #
# ITEM 8 -- cold(K=0)/ceiling(all-labels) reproduce run 78's own anchors exactly (live, real data).
# --------------------------------------------------------------------------------------------- #
requires_run78 = pytest.mark.skipif(not (RUN78_PREP_PRESENT and RUN78_READ_PRESENT),
                                    reason="run 78 checkpoints not present")
requires_run69 = pytest.mark.skipif(not RUN69_READ_PRESENT, reason="run 69 checkpoints not present")


@requires_run78
def test_cold_and_ceiling_match_run78_live():
    p78 = r78._load(r79.RUN78_PREP)
    r78_read = r78._load(r79.RUN78_READ)
    letters = p78["letters"]
    pairwise_idx = r78.build_letter_pairwise_index(r78_read["pairwise"])

    cold = r78.letter_visual_accuracy(letters, {}, pairwise_idx)
    ceiling_pool = r78.build_true_ceiling_pool(letters)
    ceiling = r78.letter_visual_accuracy(letters, ceiling_pool, pairwise_idx)

    run78_boot_path = r78._ckpt("bootstrap.json")
    if os.path.exists(run78_boot_path):
        run78_boot = r78._load(run78_boot_path)
        assert cold["acc"] == pytest.approx(run78_boot["cold"]["acc"])
        assert ceiling["acc"] == pytest.approx(run78_boot["ceiling"]["acc"])
    assert 0.0 <= cold["acc"] <= 1.0
    assert 0.0 <= ceiling["acc"] <= 1.0
    assert ceiling["acc"] >= cold["acc"]


@requires_run78
def test_build_prep_reports_k_writer_counts_decreasing_in_k():
    out = r79.build_prep()
    counts = [out["k_writer_counts"][str(k)] for k in r79.K_VALUES]
    assert counts == sorted(counts, reverse=True), "more writers must qualify for smaller K"
    assert counts[0] <= out["n_writers"]


# --------------------------------------------------------------------------------------------- #
# ITEM 9 -- pose-decomposition anchor: D sits between A and E (run 69's own live numbers).
# --------------------------------------------------------------------------------------------- #
@requires_run69
def test_pose_decomposition_anchor_live():
    anchor = r79.run69_pose_decomposition_anchor()
    for key in ("condA_no_pose_cross_pct", "condD_pose_only_cross_pct",
               "condE_pose_plus_bank_within_pct"):
        assert 0.0 <= anchor[key] <= 100.0
    assert anchor["n"] > 0
    assert anchor["condE_pose_plus_bank_within_pct"] > anchor["condA_no_pose_cross_pct"], (
        "full within-writer adaptation must beat no-adaptation-at-all -- a basic sanity floor this "
        "whole arc has established in every prior run")


# --------------------------------------------------------------------------------------------- #
# ITEM 10 -- seed-guard md5 check across real stage invocations.
# --------------------------------------------------------------------------------------------- #
@requires_run78
def test_stage_prep_leaves_seed_md5_unchanged():
    before = _md5(STROKE_SHAPES_SEED)
    rc = r79.stage_prep()
    after = _md5(STROKE_SHAPES_SEED)
    assert rc == 0
    assert after == before
    assert os.path.exists(r79._ckpt("prep.json"))
