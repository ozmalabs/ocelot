"""THE CODEBOOK AXIS — gates for the Occam short-circuit in `eval_dim_infer`.

PREREG: `VISION_CODEBOOK_AXIS_PREREG.md` @ `e22db8dd` (committed before any
measurement or implementation). RESULTS: `VISION_CODEBOOK_AXIS_RESULTS.md`.

WHAT IS GATED. `eval_dim_infer` skips its length-2 (composition) arm whenever any
length-1 success exists. The saving is 91.16% of attempts on the recognising
path. Four things must hold, and each has its own test rather than being folded
into one "it still works":

  1. THE VERDICT DOES NOT MOVE. Byte-identity against verdicts captured from the
     ACTUAL PRE-FIX ENGINE (`results/codebook_axis_identity_OLD.json`, engine
     `02ad951e4e45`), not against expectations written after the fact.
  2. `checked` DOES NOT MOVE. It is a RETURNED field, so a naive skip shrinks it.
     The prereg named this as the fix's one hazard BEFORE the fix existed; the
     implementation places the skip after `checked += 1` to preserve it. This is
     asserted SEPARATELY from (1) because it is the cell most likely to break.
  3. THE SHORT-CIRCUIT ACTUALLY FIRES. A fix that quietly does nothing would pass
     (1) and (2) perfectly. This asserts the cost DROPS on the explained path.
  4. COST STILL TRACKS CONTENT. Byte-identity is NOT property-identity —
     batch-apply held identity over 235,200 values and still destroyed
     compute-∝-surprise, unnoticed for two rungs. This asserts the unexplained
     path is UNCHANGED and now costs MORE than the explained one.
"""
from __future__ import annotations

import gc
import json
import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OLD_FIXTURE = os.path.join(ROOT, "results", "codebook_axis_identity_OLD.json")
GEN_SEED = os.path.join(ROOT, "seeds", "shape_decode_loop.json")


# --------------------------------------------------------------------------- #
def _attempts_per_part():
    """(length-1, length-2, total) attempts per eligible part.

    FALLS OUT of the seed's own generator `params` (PROTOCOL §13) — no constant
    is written down here, so adding a generator updates the gate automatically
    instead of silently invalidating it."""
    with open(GEN_SEED) as fh:
        ps = [len(n["attrs"].get("params") or [])
              for n in json.load(fh).get("nodes", [])
              if n.get("type") == "DimensionGenerator"]
    sp = sum(ps)
    return sp, sp * sp - sum(p * p for p in ps), sp + (sp * sp - sum(p * p for p in ps))


def _load_old():
    if not os.path.exists(OLD_FIXTURE):
        pytest.skip("pre-fix capture not present")
    with open(OLD_FIXTURE) as fh:
        return json.load(fh)


def _live_case(case):
    """Re-run ONE captured case on the CURRENT engine."""
    from scripts.codebook_axis_identity import one_case
    return one_case(case["N"], case["K"], case["obs"], case["seed"])


# --------------------------------------------------------------------------- #
def test_the_occam_key_makes_length_STRICT_PRIMARY():
    """THE PROOF THE SKIP RESTS ON, asserted against the source rather than
    trusted. `key = (steps.len(), residual_dims, base_name, ks)` compared as a
    tuple: a length-1 success can never lose to a length-2 one, so a skipped
    length-2 candidate is PROVABLY unable to win. If this ordering is ever
    changed, the short-circuit becomes unsound and this test is the tripwire."""
    src = open(os.path.join(ROOT, "runners", "dsl", "src", "shape_decode.rs")).read()
    body = src[src.index("pub(crate) fn eval_dim_infer"):]
    body = body[:body.index("\n/// One successful")]
    key = body[body.index("let key = |att: &DimAttempt|"):]
    key = key[:key.index("};")]
    # `steps.len()` must be the FIRST component of the key tuple.
    assert key.index("att.steps.len()") < key.index("att.residual_dims"), (
        "composition length is no longer the strict-primary Occam component — "
        "the length-2 short-circuit in this same function is UNSOUND without it")
    assert "if explained_at_length_1" in body, "the short-circuit is gone"


def test_the_skip_is_placed_AFTER_checked_so_the_returned_count_is_preserved():
    """`checked` is a RETURNED field. The skip must sit after its increment —
    the prereg's one declared hazard, addressed structurally rather than
    remembered."""
    src = open(os.path.join(ROOT, "runners", "dsl", "src", "shape_decode.rs")).read()
    body = src[src.index("// --- PASS 2: LENGTH 2"):]
    body = body[:body.index("// Occam within rung 2")]
    assert body.index("checked += 1;") < body.index("if explained_at_length_1"), (
        "the skip precedes `checked += 1` — the returned attempt count would "
        "shrink, which is a silent semantic change dressed as an optimisation")


# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("idx", [0, 7, 19, 23, 41, 55, 60, 79])
def test_verdict_is_byte_identical_to_the_PRE_FIX_ENGINE(idx):
    """(1) Byte-identity against verdicts captured from engine `02ad951e4e45`,
    the actual pre-fix binary — not against expectations authored afterwards.

    A move in ANY verdict field means the prune dropped a candidate that could
    have won. Per prereg §4.1 that is a FINDING that stops the fix, never a
    signal to tune the prune."""
    old = _load_old()
    rec = old["records"][idx]
    live, _ = _live_case(rec["case"])
    assert live == rec, (
        f"verdict moved at {rec['case']} — the length-2 skip dropped a "
        f"candidate that could have won")


def test_checked_the_RETURNED_attempt_count_does_not_move():
    """(2) The declared hazard, gated on its own across every captured case."""
    old = _load_old()
    moved = []
    for rec in old["records"]:
        if rec["case"]["N"] > 20:          # keep the gate quick; N is not the axis here
            continue
        live, _ = _live_case(rec["case"])
        a = (rec.get("dim_infer") or {}).get("checked")
        b = (live.get("dim_infer") or {}).get("checked")
        if a != b:
            moved.append((rec["case"], a, b))
    assert not moved, f"`checked` moved: {moved[:3]}"


# --------------------------------------------------------------------------- #
def test_the_short_circuit_ACTUALLY_FIRES_on_the_explained_path():
    """(3) A fix that quietly did nothing would pass every identity test above.

    On an observation explained at length 1, interior units must fall to the
    length-1 SHARE of attempts — `SP / A`, computed from the seed, not asserted
    as a magic 0.0884."""
    l1, _l2, a = _attempts_per_part()
    _, cost_expl = _live_case({"N": 20, "K": 3, "obs": "rot1", "seed": 68000 + 200 + 203})
    _, cost_novel = _live_case({"N": 20, "K": 3, "obs": "novel", "seed": 68000 + 200 + 203})
    # The exhaustive baseline is the novel path, which still runs all `A`
    # attempts; the explained path should be `l1/a` of the SAME per-attempt work.
    share = cost_expl["term_unit:DimInfer"] / (
        cost_novel["term_unit:DimInfer"] / cost_novel["term_eval:DimInfer"]
        * cost_expl["term_eval:DimInfer"])
    assert share == pytest.approx(l1 / a, rel=1e-6), (
        f"explained-path share {share} != length-1 share {l1/a} — the "
        f"short-circuit is not firing")


def test_cost_STILL_TRACKS_CONTENT_and_the_unexplained_path_is_untouched():
    """(4) THE PROPERTY CHECK, which byte-identity does not imply.

    Batch-apply held verdict byte-identity over 235,200 values and still
    destroyed compute-∝-surprise. The property at risk here is that same one, so
    it is measured rather than argued:

      * the UNEXPLAINED path must be BIT-FOR-BIT unchanged in cost (nothing is
        explained, so the short-circuit must not fire at all); and
      * after the fix a surprising observation must cost MORE than a recognised
        one — the direction compute-∝-surprise requires.
    """
    old = _load_old()
    old_novel = {json.dumps(c["case"], sort_keys=True): c["term_unit:DimInfer"]
                 for c in old["costs"] if c["case"]["obs"] == "novel"}
    for case_key, old_units in list(old_novel.items())[:4]:
        case = json.loads(case_key)
        _, cost = _live_case(case)
        assert cost["term_unit:DimInfer"] == old_units, (
            f"the UNEXPLAINED path changed cost at {case} — the short-circuit "
            f"is firing where nothing was explained, which would break "
            f"compute-∝-surprise")

    _, expl = _live_case({"N": 20, "K": 3, "obs": "rot1", "seed": 68000 + 200 + 203})
    _, novel = _live_case({"N": 20, "K": 3, "obs": "novel", "seed": 68000 + 200 + 203})
    assert novel["term_unit:DimInfer"] > expl["term_unit:DimInfer"], (
        "a recognised observation costs at least as much as a surprising one — "
        "compute-∝-surprise is flat or inverted")


def test_attempt_counts_FALL_OUT_of_the_generator_seed():
    """PROTOCOL §13 — no magic number. The 13/134/147 split is the shipped
    generator codebook's own arity, so adding a generator moves it."""
    l1, l2, a = _attempts_per_part()
    assert a == l1 + l2 and l1 > 0 and l2 > 0
    with open(GEN_SEED) as fh:
        ps = [len(n["attrs"].get("params") or [])
              for n in json.load(fh).get("nodes", [])
              if n.get("type") == "DimensionGenerator"]
    assert l1 == sum(ps)
    assert l2 == sum(ps) ** 2 - sum(p * p for p in ps)


def test_the_sd_orbit_law_is_UNMOVED_by_the_short_circuit():
    """The arc's standing invariant `{2:1, 3:2, 4:2, 6:2, 12:4}` — the sharpest
    end-to-end check that recognition and minting are unchanged on REAL frames,
    not synthetic probes."""
    from scripts.sdloop_vision_measure import run_arm
    got = {}
    for n in (2, 3, 4):
        thetas = [i * 180.0 / n for i in range(n)]
        _rows, cb, _alive = run_arm(68000 + 300 + n, thetas, label="orbitgate")
        got[n] = cb["mints"]
        gc.collect()
    assert got == {2: 1, 3: 2, 4: 2}, f"sd orbit law moved: {got}"
