"""tests/test_run29_consume_migrated.py — RUN 29 (CONSUME) gates: the two run-28-named
unwired sinks now WIRED. Run 28 built the arrangement-grain sd loop
(`domains/arrangement_codebook.py`: `mint_or_recognize_character_reading`/
`update_relation_stability`/`weighted_arrangement_score`) but nothing CONSUMED it — the
round-trip comparator scored arrangement unweighted, and the eval proposal path read only the
stroke codebook. This suite gates the three consumption points added in run 29:

  (a) MARKING CONSUMES WEIGHTS — `homework_loop._apply_stability_weighting` (called from
      `mark_characters` when `use_stability_weights=True`) overrides a HELD item's
      `arrangement_score` with `arrangement_codebook.weighted_arrangement_score`'s own read of
      the recognized quantum's persisted `relation_weights`, reporting the plain value
      alongside as `arrangement_score_unweighted` — never silently replaced.
  (b) BABBLE PERSISTS TO THE HELD QUANTUM — `babble_characters`' own per-rep arrangement-
      instability tally (mechanism (e)) now ALSO calls `update_relation_stability` on
      `WorksheetItem.character_quantum` (threaded through `assign()`, new field), so a
      practice session's own observations land on the SAME graph-resident quantum the NEXT
      `mark_characters` call reads back — closing the loop `arrangement_codebook.py`'s own
      module docstring named as unwired ("stability weights ... nothing reads").
  (c) EVAL PROPOSAL CONSUMES THE CHARACTER CODEBOOK (pooled-prior modality) —
      `arrangement_codebook.pooled_relation_kind_reliability`/`pooled_prior_coverage_term`/
      `propose_top_k_pooled_prior`: a GLOBAL per-relation-KIND reliability prior pooled from
      every held character quantum's own `relation_weights`, applied as a WEIGHTED twin of
      `abs_read._coverage_term`'s naive coverage — a proposal MODALITY meant to be UNIONED with
      the existing naive-coverage shortlist (run-25's own "different angles don't overlap"
      precedent), not a per-quantum direct-match signal (the character codebook holds only
      practice-alphabet arrangements, none from eval alphabets — a direct match there would be
      honestly near-zero, see `arrangement_codebook.py`'s own new module-section docstring).

Hermetic, direct composed-signature + synthetic-corner-ink fixtures — mirrors
`tests/test_arrangement_codebook_migrated.py`'s own established style (no dataset needed)."""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("substrate_rs")

import substrate_rs as srs
from substrate.boot_core import boot_core
from domains import arrangement_codebook as ac
from domains import character_compose as cc
from domains import glyph_motor_world as gmw
from domains import homework_loop as hl
from domains import reflective_faculty as rf
from domains import stroke_codebook as sc
from domains.teach import teach as _real_teach


@pytest.fixture(autouse=True)
def _isolate_seed_writes(tmp_path, monkeypatch):
    """Redirect teach() persistence to a tmp dir — unit-test mints must never land in the boot
    seed (seeds/character_shapes.json); the live graph install is unaffected. Same pattern
    `tests/test_arrangement_codebook_migrated.py` already establishes."""
    monkeypatch.setattr(
        cc, "teach",
        lambda *a, **k: _real_teach(*a, **{**k, "seeds_dir": tmp_path}))


def _boot():
    s, ag = boot_core()
    native = s._inner
    rf._ensure_shape_decode_loop(s, native, ag)
    return s, ag, native


def _sig(rel0: tuple, rel1: tuple) -> list:
    """Same minimal two-stroke composed-signature fixture
    `tests/test_arrangement_codebook_migrated.py::_sig` already establishes — only the `rel`
    arrangement varies call to call."""
    return [["strokeq", 0, "a"], ["strokeq", 1, "b"],
            ["rel", 0, *rel0], ["rel", 1, *rel1],
            ["cpose_x", 1], ["cpose_y", 2], ["cpose_o", 3], ["cpose_s", 4]]


def _corner_fixture(s):
    """The SAME real-ink merge-inducing corner-character fixture
    `tests/test_homework_characters_migrated.py::_corner_char_fixture` establishes — duplicated
    locally per this codebase's own established small-local-duplication convention."""
    down_pts = gmw._sample_stroke("line", [0.0, 0.0, 0.0, -1.0], 24)
    right_start = down_pts[-1]
    right_pts = gmw._sample_stroke(
        "line", [right_start[0], right_start[1], right_start[0] + 1.0, right_start[1]], 24)
    sc.build_stroke_codebook(
        s, sources=[("down", down_pts.tolist()), ("right", right_pts.tolist())],
        include_pickle=False)
    concatenated = np.concatenate([down_pts, right_pts], axis=0)
    n_knots = len(concatenated)
    half = n_knots // 2
    dk = hl._default_dk()
    dk.update(min_span=half, max_span=half, max_knots=n_knots)
    char_items = [{"id": "char0", "class_id": "A", "strokes": [concatenated.tolist()]}]
    return char_items, dk


def _save_graph(s, path: str) -> None:
    """Run 26/27/28's own fixed persistence recipe, reproduced verbatim (`graph_to_dict()`
    alone crashes on reload — grammar + rules must ride along)."""
    blob = {"graph": s.graph_to_dict(), "grammar": s.grammar_to_json(),
            "rules": s._inner.export_rules()}
    with open(path, "w") as f:
        json.dump(blob, f)


def _load_graph(path: str):
    with open(path) as f:
        blob = json.load(f)
    s = srs.Substrate()
    s.graph_from_dict(blob["graph"])
    for p in blob["grammar"]["productions"]:
        try:
            s._inner.add_production(p)
        except Exception:
            pass
    if "rules" in blob:
        s._inner.import_rules(blob["rules"])
    return s


# ===========================================================================
# (a) MARKING CONSUMES WEIGHTS — the weighted arrangement subscore moves in the RIGHT
# direction (>= unweighted) once a genuinely unstable relation has been down-weighted, on the
# SAME merge/split-style fixture family `test_arrangement_codebook_migrated.py`'s own gate 4
# uses (a known single-relation instability against an otherwise-perfect fixture).
# ===========================================================================
def test_weighted_marking_scores_at_least_unweighted_when_instability_down_weighted():
    s, ag, native = _boot()
    ref_sig = _sig((1, 2, 3, 4), (5, 6, 7, 8))
    res = ac.mint_or_recognize_character_reading(s, ref_sig)
    quantum = res["name"]
    # ONLY rel:1:o (stroke 1's orientation slot) ever mismatches -- everything else agrees.
    unstable_obs = _sig((1, 2, 3, 4), (5, 6, 99, 8))
    for _ in range(25):
        ac.update_relation_stability(s, quantum, ref_sig, unstable_obs)
    weights = ac.relation_weights(s, quantum)
    assert weights["rel:1:o"] < ac.DEFAULT_WEIGHT, "precondition: the relation must be learned unstable"

    orig_groups = [[(0, 1, "a")], [(1, 2, "b")]]
    re_groups = [[(0, 1, "a")], [(1, 2, "b")]]
    scored = hl._character_round_trip_score(s, native, orig_groups, re_groups, ref_sig, unstable_obs)
    assert scored["arrangement_score"] < 1.0, "precondition: the plain formula must see a residual"

    weighted = hl._apply_stability_weighting(s, scored, quantum, True, ref_sig, unstable_obs, True)
    assert weighted["arrangement_score_unweighted"] == pytest.approx(scored["arrangement_score"]), (
        "the plain unweighted value must be reported alongside, never discarded")
    assert weighted["arrangement_score"] > weighted["arrangement_score_unweighted"], (
        "a relation PROVEN unstable, once down-weighted, must count for LESS against this "
        "exact observation's own arrangement score than the naive uniform-credit formula did")
    assert weighted["overall"] == pytest.approx(
        (weighted["family_score"] + weighted["count_score"] + weighted["arrangement_score"]) / 3.0
    ), "overall must be recomputed by the SAME fixed-formula mean, on the NEW arrangement value"


def test_weighted_marking_is_a_noop_when_flag_off_or_quantum_not_held():
    s, ag, native = _boot()
    ref_sig = _sig((1, 2, 3, 4), (5, 6, 7, 8))
    res = ac.mint_or_recognize_character_reading(s, ref_sig)
    quantum = res["name"]
    orig_groups = [[(0, 1, "a")], [(1, 2, "b")]]
    scored = hl._character_round_trip_score(s, native, orig_groups, orig_groups, ref_sig, ref_sig)

    off = hl._apply_stability_weighting(s, scored, quantum, True, ref_sig, ref_sig, False)
    expected = dict(scored, arrangement_score_unweighted=None)
    assert off == expected, "use_weights=False must leave every field byte-identical"

    not_held = hl._apply_stability_weighting(s, scored, quantum, False, ref_sig, ref_sig, True)
    assert not_held == expected, (
        "a quantum that was just MINTED this call (not a HELD recognition) must not trigger "
        "the override either -- its weights are all still DEFAULT_WEIGHT, a costless no-op is "
        "the honest contract, not an accidental override")


# ===========================================================================
# Flag-off byte-compat — an EXISTING real-ink scenario (the corner merge fixture) reproduces
# exactly whether or not the new kwarg is passed at all.
# ===========================================================================
def test_flag_off_byte_compat_reproduces_existing_scenario():
    s1, ag1, native1 = _boot()
    char_items1, dk1 = _corner_fixture(s1)
    old_way = hl.mark_characters(s1, char_items1, dk=dk1, enable_character_codebook=True)

    s2, ag2, native2 = _boot()
    char_items2, dk2 = _corner_fixture(s2)
    new_way = hl.mark_characters(s2, char_items2, dk=dk2, enable_character_codebook=True,
                                 use_stability_weights=False)

    assert old_way[0].round_trip_score == new_way[0].round_trip_score
    assert old_way[0].family_score == new_way[0].family_score
    assert old_way[0].count_score == new_way[0].count_score
    assert old_way[0].arrangement_score == new_way[0].arrangement_score
    assert old_way[0].character_quantum == new_way[0].character_quantum
    assert old_way[0].arrangement_score_unweighted is None
    assert new_way[0].arrangement_score_unweighted is None


# ===========================================================================
# (b) BABBLE PERSISTS TO THE HELD QUANTUM — a worksheet item carrying `character_quantum`
# gets its per-rep arrangement observations written back onto that SAME graph node.
# ===========================================================================
def test_assign_threads_character_quantum_onto_worksheet_items():
    s, ag, native = _boot()
    char_items, dk = _corner_fixture(s)
    marked = hl.mark_characters(s, char_items, dk=dk, enable_character_codebook=True)
    assert marked[0].character_quantum is not None
    ws = hl.assign(marked)
    assert ws.items[0].character_quantum == marked[0].character_quantum

    # A pre-existing (run-26/27) stroke-grain caller never sets character_quantum -- the field
    # must default to None, not crash `assign()`.
    marked_stroke_grain = hl.mark(s, [{"id": "s0", "class_id": "A",
                                       "points": [[0.0, 0.0], [1.0, 0.0], [2.0, 0.0]]}])
    ws2 = hl.assign(marked_stroke_grain)
    if ws2.items:
        assert ws2.items[0].character_quantum is None


def test_babble_characters_persists_relation_weights_onto_the_recognized_quantum():
    s, ag, native = _boot()
    char_items, dk = _corner_fixture(s)
    marked = hl.mark_characters(s, char_items, dk=dk, enable_character_codebook=True)
    quantum = marked[0].character_quantum
    assert quantum is not None
    before = dict(ac.relation_weights(s, quantum))

    ws = hl.assign(marked)
    assert ws.items and ws.items[0].character_quantum == quantum
    hl.babble_characters(s, ws, reps_per_item=8, rng_seed=3, jitter_bins=1)

    after = ac.relation_weights(s, quantum)
    assert after != {}, (
        "babble_characters must have written AT LEAST one relation_weights observation onto "
        "the recognized quantum's own graph node")
    # Every stored weight must stay within the module's own declared bounds -- a plumbing sanity
    # check, not a re-derivation of the EMA math (already gated by
    # test_arrangement_codebook_migrated.py's own gate 3).
    assert all(ac.MIN_WEIGHT - 1e-9 <= w <= ac.MAX_WEIGHT + 1e-9 for w in after.values())


def test_babble_characters_is_a_noop_on_relation_weights_when_no_quantum_held():
    """A worksheet item with `character_quantum=None` (the run-26/27 default, or run 28's own
    `enable_character_codebook=False`) must leave the character codebook exactly as it was --
    no crash, no spurious quantum touched."""
    s, ag, native = _boot()
    char_items, dk = _corner_fixture(s)
    marked = hl.mark_characters(s, char_items, dk=dk)   # lever OFF -- byte-identical default.
    assert marked[0].character_quantum is None
    ws = hl.assign(marked)
    assert ws.items[0].character_quantum is None

    before = ac.character_vocabulary_report(s)["total"]
    hl.babble_characters(s, ws, reps_per_item=4, rng_seed=1, jitter_bins=0)
    after = ac.character_vocabulary_report(s)["total"]
    assert after == before == 0


# ===========================================================================
# Weights persist across a save/load round-trip (the run 26/27/28 `_save_graph` recipe).
# ===========================================================================
def test_relation_weights_persist_across_save_load_round_trip(tmp_path):
    s, ag, native = _boot()
    ref_sig = _sig((1, 2, 3, 4), (5, 6, 7, 8))
    res = ac.mint_or_recognize_character_reading(s, ref_sig)
    quantum = res["name"]
    unstable_obs = _sig((1, 2, 3, 4), (5, 6, 99, 8))
    for _ in range(10):
        ac.update_relation_stability(s, quantum, ref_sig, unstable_obs)
    weights_before = ac.relation_weights(s, quantum)
    assert weights_before["rel:1:o"] < ac.DEFAULT_WEIGHT

    path = str(tmp_path / "run29_graph.json")
    _save_graph(s, path)
    s2 = _load_graph(path)

    weights_after = ac.relation_weights(s2, quantum)
    assert weights_after == weights_before, (
        "relation_weights is plain graph-node attr data -- it must survive the SAME "
        "graph_to_dict/grammar_to_json/export_rules round trip every other run-26/27/28 "
        "checkpoint already relies on")


# ===========================================================================
# (c) EVAL PROPOSAL CONSUMES THE CHARACTER CODEBOOK — pooled relation-kind reliability prior,
# computed from >= 2 quanta, reweights a coverage comparison deterministically.
# ===========================================================================
def test_pooled_relation_kind_reliability_from_two_quanta_reweights_deterministically():
    s, ag, native = _boot()
    sig_a = _sig((1, 2, 3, 4), (5, 6, 7, 8))
    quantum_a = ac.mint_or_recognize_character_reading(s, sig_a)["name"]
    sig_b = _sig((9, 9, 9, 9), (1, 1, 1, 1))
    quantum_b = ac.mint_or_recognize_character_reading(s, sig_b)["name"]
    assert quantum_a != quantum_b

    # Quantum A: rel:1:o proves unstable. Quantum B: rel:0:x proves unstable. Every other
    # relation on both quanta matches every rep (stays at the ceiling).
    unstable_obs_a = _sig((1, 2, 3, 4), (5, 6, 99, 8))
    unstable_obs_b = _sig((99, 9, 9, 9), (1, 1, 1, 1))
    for _ in range(25):
        ac.update_relation_stability(s, quantum_a, sig_a, unstable_obs_a)
        ac.update_relation_stability(s, quantum_b, sig_b, unstable_obs_b)

    prior = ac.pooled_relation_kind_reliability(s)
    assert set(prior) >= {"x", "y", "o", "s", "cpose_x", "cpose_y", "cpose_o", "cpose_s"}
    # 'o' pools quantum A's own fallen rel:1:o alongside three steady observations (A's rel:0:o,
    # B's rel:0:o/rel:1:o) -- the pool must land STRICTLY between the floor and the ceiling,
    # neither single quantum's own extreme.
    assert ac.MIN_WEIGHT < prior["o"] < ac.MAX_WEIGHT
    assert ac.MIN_WEIGHT < prior["x"] < ac.MAX_WEIGHT
    # 'y' is never destabilized by EITHER quantum -- must stay at the ceiling.
    assert prior["y"] == pytest.approx(ac.MAX_WEIGHT)

    query = [["strokeq", 0, "z"], ["rel", 0, 1, 2, 3, 4], ["cpose_x", 1]]
    exemplar_match = [["strokeq", 0, "z"], ["rel", 0, 1, 2, 3, 4], ["cpose_x", 1]]
    exemplar_miss = [["strokeq", 0, "other"], ["rel", 0, 9, 9, 9, 9], ["cpose_x", 99]]
    term_match = ac.pooled_prior_coverage_term(query, exemplar_match, prior)
    term_miss = ac.pooled_prior_coverage_term(query, exemplar_miss, prior)
    score_match = native.evaluate(term_match, {})
    score_miss = native.evaluate(term_miss, {})
    assert score_match > score_miss
    # Deterministic: re-evaluating the SAME held Term gives the identical score.
    assert native.evaluate(term_match, {}) == pytest.approx(score_match)
    assert native.evaluate(term_miss, {}) == pytest.approx(score_miss)


def test_pooled_relation_kind_reliability_is_empty_when_no_quanta_held():
    s, ag, native = _boot()
    assert ac.pooled_relation_kind_reliability(s) == {}
    # An empty prior must fall back to `default_weight` -- never crash, never fabricate.
    query = [["strokeq", 0, "z"], ["rel", 0, 1, 2, 3, 4]]
    exemplar = [["strokeq", 0, "z"], ["rel", 0, 1, 2, 3, 4]]
    term = ac.pooled_prior_coverage_term(query, exemplar, {}, default_weight=1.0)
    assert native.evaluate(term, {}) == pytest.approx(2.0)


def test_propose_top_k_pooled_prior_ranks_the_true_exemplar_first_on_a_clean_match():
    s, ag, native = _boot()
    sig_a = _sig((1, 2, 3, 4), (5, 6, 7, 8))
    quantum_a = ac.mint_or_recognize_character_reading(s, sig_a)["name"]
    sig_b = _sig((9, 9, 9, 9), (1, 1, 1, 1))
    ac.mint_or_recognize_character_reading(s, sig_b)
    unstable_obs_a = _sig((1, 2, 3, 4), (5, 6, 99, 8))
    for _ in range(25):
        ac.update_relation_stability(s, quantum_a, sig_a, unstable_obs_a)
    prior = ac.pooled_relation_kind_reliability(s)

    query = _sig((1, 2, 3, 4), (5, 6, 7, 8))
    exemplars = [_sig((9, 9, 9, 9), (1, 1, 1, 1)), _sig((1, 2, 3, 4), (5, 6, 7, 8))]
    order = ac.propose_top_k_pooled_prior(native, query, exemplars, prior, k=2)
    assert order[0] == 1, "the byte-identical exemplar must propose first"
    assert set(order) == {0, 1}


# ===========================================================================
# Source audit — no Python decision was introduced by any run-29 addition (the WHOLE-FILE
# scans `test_arrangement_codebook_migrated.py::test_arrangement_codebook_no_python_decisions`
# / `test_homework_loop_migrated.py::test_homework_loop_no_python_decisions` already re-run
# over the modified files on every collection; this gate additionally pins that the two NEW
# entry points this run adds are actually present with the expected shape).
# ===========================================================================
def test_run29_new_entry_points_exist_with_expected_shape():
    import inspect

    assert "use_stability_weights" in inspect.signature(hl.mark_characters).parameters
    assert "use_stability_weights" in inspect.signature(hl.cycle_characters).parameters
    assert "character_quantum" in {f.name for f in __import__("dataclasses").fields(hl.WorksheetItem)}
    assert "arrangement_score_unweighted" in {
        f.name for f in __import__("dataclasses").fields(hl.MarkedItem)}
    for name in ("pooled_relation_kind_reliability", "pooled_prior_coverage_term",
                 "propose_top_k_pooled_prior"):
        assert hasattr(ac, name), f"arrangement_codebook.{name} must exist"


def test_run29_additions_source_audit():
    banned = re.compile(r"\.arg(?:min|max)\(|(?<!\w)np\.arg(?:min|max)\b", re.IGNORECASE)
    minmax_key = re.compile(r"(?<!\w)(?:min|max)\(.*?key\s*=", re.IGNORECASE)
    bare_list_isinstance = re.compile(r"isinstance\([^,]+,\s*list\s*\)")
    for mod, src in ((hl, Path(hl.__file__).read_text()), (ac, Path(ac.__file__).read_text())):
        assert not banned.search(src), f"{mod.__name__}: argmin/argmax found in Python"
        assert not minmax_key.search(src), f"{mod.__name__}: min/max(key=...) found in Python"
        assert not bare_list_isinstance.search(src), (
            f"{mod.__name__}: bare isinstance(..., list) found (must accept tuples too)")
