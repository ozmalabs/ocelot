"""tests/test_arrangement_codebook_migrated.py — RUN 28 LEVER 2 gates: the sd loop wired at
ARRANGEMENT (character) grain (`domains/arrangement_codebook.py`). Hermetic, direct
composed-signature fixtures (mirrors `tests/test_homework_characters_migrated.py::
test_arrangement_disagreement_detected_when_families_agree`'s own established style — a
composed `ShapeSignature`-format relation list is plain data, no dataset/geometry needed to
exercise recognize/mint/weight logic directly).

THE WALL (run 27's traced diagnosis): `character_compose.recognize_or_mint_character`/
`grow_character_quantum` already existed, fully unit-tested in isolation
(`tests/test_character_composition_migrated.py`), but had ZERO call sites outside that test
file — `homework_loop.mark_characters` composed a signature and scored its own round-trip
stability, but never asked "does this arrangement match anything held" or "should this
arrangement be REMEMBERED." This suite gates the THIN WIRING (`arrangement_codebook.
mint_or_recognize_character_reading`) plus the NEW stability-weighted persistence channel
(`update_relation_stability`/`weighted_arrangement_score`)."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytest.importorskip("substrate_rs")

from substrate.boot_core import boot_core
from domains import arrangement_codebook as ac
from domains import character_compose as cc
from domains import homework_loop as hl
from domains import reflective_faculty as rf
from domains.teach import teach as _real_teach


@pytest.fixture(autouse=True)
def _isolate_seed_writes(tmp_path, monkeypatch):
    """Redirect teach() persistence to a tmp dir — unit-test mints must never land in the
    boot seed (seeds/character_shapes.json); the live graph install is unaffected."""
    monkeypatch.setattr(
        cc, "teach",
        lambda *a, **k: _real_teach(*a, **{**k, "seeds_dir": tmp_path}))


def _boot():
    s, ag = boot_core()
    native = s._inner
    rf._ensure_shape_decode_loop(s, native, ag)
    return s, ag, native


def _sig(rel0: tuple, rel1: tuple) -> list:
    """A minimal two-stroke composed character signature -- SAME `strokeq`/`cpose_*` on every
    call, only the `rel` arrangement varies. Mirrors
    `test_homework_characters_migrated.py::test_arrangement_disagreement_detected_when_
    families_agree`'s own direct-signature fixture style."""
    return [["strokeq", 0, "a"], ["strokeq", 1, "b"],
            ["rel", 0, *rel0], ["rel", 1, *rel1],
            ["cpose_x", 1], ["cpose_y", 2], ["cpose_o", 3], ["cpose_s", 4]]


# ===========================================================================
# Gate 1 — two synthetic characters with the SAME stroke multiset but DIFFERENT arrangement
# mint DISTINCT character quanta.
# ===========================================================================
def test_same_multiset_different_arrangement_mints_distinct_quanta():
    s, ag, native = _boot()
    sig1 = _sig((1, 2, 3, 4), (5, 6, 7, 8))
    # Deliberately NOT a uniform per-dimension transform of sig1: the two strokes' own "rel"
    # deltas at each pooled slot disagree with each other (stroke 0's x delta is +8, stroke
    # 1's is -4, etc.) -- TransformDecode's own (predicate,slot) pooling cannot explain this
    # as identity + one consistent delta, so it is a genuinely NEW arrangement, not a rung-1
    # transform of sig1.
    sig2 = _sig((9, 9, 9, 9), (1, 1, 1, 1))

    res1 = ac.mint_or_recognize_character_reading(s, sig1)
    assert res1["minted"] is True and res1["installed"] is True
    res2 = ac.mint_or_recognize_character_reading(s, sig2)
    assert res2["minted"] is True and res2["installed"] is True

    assert res1["name"] != res2["name"], "distinct arrangements must mint DISTINCT quanta"
    vocab = ac.character_vocabulary_report(s)
    assert vocab["total"] == 2
    assert {res1["name"], res2["name"]} == set(vocab["names"])


# ===========================================================================
# Gate 2 — reading a minted character again RECOGNIZES it (idempotent, no re-mint).
# ===========================================================================
def test_reading_a_minted_character_again_recognizes_it():
    s, ag, native = _boot()
    sig1 = _sig((1, 2, 3, 4), (5, 6, 7, 8))
    res1 = ac.mint_or_recognize_character_reading(s, sig1)
    assert res1["minted"] is True
    before = ac.character_vocabulary_report(s)["total"]

    res2 = ac.mint_or_recognize_character_reading(s, sig1)
    assert res2["minted"] is False, "re-reading the IDENTICAL arrangement must recognize, not mint"
    assert res2["name"] == res1["name"]
    after = ac.character_vocabulary_report(s)["total"]
    assert after == before, "no new quantum on a repeat read"


def test_reading_a_never_before_seen_arrangement_still_mints_after_others_are_held():
    """Sanity companion to gate 1/2: minting one arrangement must not make an UNRELATED,
    genuinely novel arrangement fall through as a false "recognized" via the codebook's own
    direct rung-1 transform check."""
    s, ag, native = _boot()
    sig1 = _sig((1, 2, 3, 4), (5, 6, 7, 8))
    ac.mint_or_recognize_character_reading(s, sig1)
    sig2 = _sig((9, 9, 9, 9), (1, 1, 1, 1))
    res2 = ac.mint_or_recognize_character_reading(s, sig2)
    assert res2["minted"] is True
    assert ac.character_vocabulary_report(s)["total"] == 2


# ===========================================================================
# Gate 3 — a persistently unstable relation's weight FALLS across babble reps; a stable one
# HOLDS at its ceiling.
# ===========================================================================
def test_unstable_relation_weight_falls_while_stable_relation_holds():
    s, ag, native = _boot()
    ref_sig = _sig((1, 2, 3, 4), (5, 6, 7, 8))
    res = ac.mint_or_recognize_character_reading(s, ref_sig)
    quantum = res["name"]

    # `rel:1:o` (stroke 1's orientation slot, value 7 in ref_sig) is the ONLY relation that
    # ever mismatches across every simulated rep -- every other key matches every time.
    unstable_obs = _sig((1, 2, 3, 4), (5, 6, 99, 8))

    for _ in range(25):
        out = ac.update_relation_stability(s, quantum, ref_sig, unstable_obs)
        assert out["updated"] is True

    weights = ac.relation_weights(s, quantum)
    assert weights["rel:1:o"] < ac.DEFAULT_WEIGHT, (
        f"a relation that mismatches on EVERY rep must fall below the default weight, "
        f"got {weights['rel:1:o']}")
    assert weights["rel:1:o"] <= ac.MIN_WEIGHT + 1e-6 or weights["rel:1:o"] < 0.5, (
        "25 consecutive mismatches must drive the weight well down toward the floor")
    for stable_key in ("rel:0:x", "rel:0:y", "rel:0:o", "rel:0:s", "rel:1:x", "rel:1:y",
                       "rel:1:s", "cpose_x", "cpose_y", "cpose_o", "cpose_s"):
        assert weights.get(stable_key, ac.DEFAULT_WEIGHT) >= ac.MAX_WEIGHT - 1e-6, (
            f"a relation that matched on EVERY rep must stay at/near the ceiling: "
            f"{stable_key}={weights.get(stable_key)}")


def test_update_relation_stability_on_missing_quantum_is_an_honest_noop():
    s, ag, native = _boot()
    out = ac.update_relation_stability(s, "no_such_quantum", _sig((1, 2, 3, 4), (5, 6, 7, 8)),
                                       _sig((1, 2, 3, 4), (5, 6, 7, 8)))
    assert out == {"updated": False, "reason": "no such character quantum",
                  "name": "no_such_quantum"}


# ===========================================================================
# Gate 4 — the STABILITY-WEIGHTED round-trip score is >= the UNWEIGHTED (all-weights-1.0)
# score for the SAME persistently-unstable-relation observation.
# ===========================================================================
def test_weighted_score_recovers_more_than_unweighted_for_a_known_unstable_relation():
    s, ag, native = _boot()
    ref_sig = _sig((1, 2, 3, 4), (5, 6, 7, 8))
    res = ac.mint_or_recognize_character_reading(s, ref_sig)
    quantum = res["name"]
    unstable_obs = _sig((1, 2, 3, 4), (5, 6, 99, 8))     # ONLY rel:1:o mismatches.

    # BEFORE any learning: every weight defaults to DEFAULT_WEIGHT (1.0) -- the weighted score
    # must equal the plain unweighted (uniform-credit) score exactly.
    baseline = ac.weighted_arrangement_score(s, quantum, ref_sig, unstable_obs)
    n = baseline["n"]
    unweighted_score = (n - 1) / n     # exactly one of n comparable relations mismatches.
    assert baseline["score"] == pytest.approx(unweighted_score)

    # Teach it: this SAME relation mismatches on every rep, everything else always matches.
    for _ in range(25):
        ac.update_relation_stability(s, quantum, ref_sig, unstable_obs)

    learned = ac.weighted_arrangement_score(s, quantum, ref_sig, unstable_obs)
    assert learned["score"] > baseline["score"], (
        "down-weighting a PROVEN-unstable relation must raise the arrangement score for an "
        "observation whose only disagreement is on that exact relation -- it should count for "
        "less against the character, not the same as an unpredictable disagreement elsewhere")
    assert learned["score"] >= unweighted_score, (
        "the stability-weighted score must never fall BELOW the naive unweighted score for "
        "this fixture")


def test_weighted_score_on_perfect_match_is_one():
    s, ag, native = _boot()
    ref_sig = _sig((1, 2, 3, 4), (5, 6, 7, 8))
    res = ac.mint_or_recognize_character_reading(s, ref_sig)
    quantum = res["name"]
    scored = ac.weighted_arrangement_score(s, quantum, ref_sig, ref_sig)
    assert scored["score"] == pytest.approx(1.0)


# ===========================================================================
# Gate 5 — homework_loop wiring is OPT-IN: every pre-existing caller (flag untouched) behaves
# byte-identically (no character-grain mint, no new MarkedItem fields set).
# ===========================================================================
def test_mark_characters_character_codebook_is_opt_in_and_off_by_default():
    import numpy as np
    from domains import glyph_motor_world as gmw

    s, ag, native = _boot()
    down = gmw._sample_stroke("line", [0.0, 0.0, 0.0, -1.0], 12)
    right = gmw._sample_stroke("line", [0.0, -1.0, 1.0, -1.0], 12)
    from domains import stroke_codebook as sc
    sc.build_stroke_codebook(s, sources=[("down", down.tolist()), ("right", right.tolist())],
                             include_pickle=False)
    concatenated = np.concatenate([down, right], axis=0)
    dk = hl._default_dk()
    dk.update(min_span=len(concatenated) // 2, max_span=len(concatenated) // 2,
             max_knots=len(concatenated))
    char_items = [{"id": "char0", "class_id": "A", "strokes": [concatenated.tolist()]}]

    marked_off = hl.mark_characters(s, char_items, dk=dk)
    assert marked_off[0].n_mints_character_reading == 0
    assert marked_off[0].character_quantum is None
    assert ac.character_vocabulary_report(s)["total"] == 0, (
        "with the lever OFF (default), no character-grain quantum may be installed")

    marked_on = hl.mark_characters(s, char_items, dk=dk, enable_character_codebook=True)
    assert ac.character_vocabulary_report(s)["total"] >= 1, (
        "with the lever ON, reading this novel arrangement must grow the character codebook"
    )
    assert marked_on[0].character_quantum is not None


# ===========================================================================
# Gate 6 — no-Python-decision source audit (mirrors test_homework_loop_migrated.py's own
# test_homework_loop_no_python_decisions).
# ===========================================================================
def test_arrangement_codebook_no_python_decisions():
    src = Path(ac.__file__).read_text()
    banned = re.compile(r"\.arg(?:min|max)\(|(?<!\w)np\.arg(?:min|max)\b", re.IGNORECASE)
    minmax_key = re.compile(r"(?<!\w)(?:min|max)\(.*?key\s*=", re.IGNORECASE)
    sort_key = re.compile(r"\.sort\(\s*key\s*=\s*lambda\s+\w+\s*:\s*(.+?)\)")
    score_kw = ("score", "emission", "vscore", "fit", "dist", "count", "covered", "vote")

    assert not banned.search(src), (
        "arrangement_codebook.py must not call argmin/argmax in Python -- ranking DECISIONS "
        "are held Terms (Sum/IfThenElse/Eq), never a Python argmin/argmax over scores")
    assert not minmax_key.search(src)
    violations = [m.group(1).strip() for m in sort_key.finditer(src)
                 if any(kw in m.group(1).lower() for kw in score_kw)]
    assert not violations, f"sort(key=...) over an apparent SCORE expression: {violations!r}"
    # A BARE `isinstance(x, list)` (no tuple) silently drops live native.evaluate() results
    # (Rust sequences surface as Python tuples) -- `isinstance(x, (list, tuple))` is fine and
    # must NOT be flagged.
    bare_list_isinstance = re.compile(r"isinstance\([^,]+,\s*list\s*\)")
    assert not bare_list_isinstance.search(src), (
        f"bare isinstance(..., list) found (must accept tuples too): "
        f"{bare_list_isinstance.search(src).group(0)!r}")
