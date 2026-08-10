"""RUNG 232000 gate tests — ISOLATE THE CLEAN TRIPLE via residual-after-explaining-
the-avatar. Every claim is gated against the GROUND-TRUTH raw cell-diff, never a
self-report. Default-OFF byte-identical: this file exercises ONLY new code
(worlds/arc_ls20_triple.py) which reuses 224's tracker + 231's colour-eye
recogniser + 229's grounder unchanged.
"""
import sys
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
for _p in (str(_ROOT), str(_ROOT / "scripts"), str(_ROOT / "runners" / "dsl" / "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.arc_ls20_triple import (  # noqa: E402
    TripleReachScenario, learn_and_isolate, isolate_triple, raw_diff_isolation,
    residual_after_avatar, avatar_explained_cells,
)
from worlds.arc_ls20_see import raw_changed_cells  # noqa: E402
from worlds.arc_ls20_percell_track import LiveObjectTracker  # noqa: E402
from worlds.arc_ls20_percell import Percell  # noqa: E402

_BASE = 232000


def _drive(seed, near_miss=False):
    sc = TripleReachScenario(np.random.default_rng(seed), near_miss=near_miss)
    ag = Percell()
    tr = LiveObjectTracker(ag)
    frames = sc.approach()
    for i in range(len(frames) - 1):
        tr.observe(frames[i], frames[i + 1], "move_down")
    before, reach, after = sc.frames()
    iso = isolate_triple(before, reach, after, tr, "move_down", sc.locus)
    return sc, iso, before, reach, after


def test_ground_truth_is_a_real_raw_diff():
    """raw_changed_cells is a genuine integer cell-diff of two frames."""
    a = np.zeros((6, 6), dtype=np.int64)
    b = a.copy(); b[2, 3] = 7; b[4, 1] = 9
    assert raw_changed_cells(a, b) == {(2, 3), (4, 1)}


def test_residual_is_observed_minus_predicted_avatar():
    """The held-prediction residual is EXACTLY the cells where the actual reach
    frame differs from the avatar-EXPLAINED prediction (a real array identity)."""
    sc, iso, before, reach, after = _drive(_BASE)
    # reconstruct the predicted frame the same way and verify the identity
    ag = Percell(); tr = LiveObjectTracker(ag)
    frames = sc.approach()
    for i in range(len(frames) - 1):
        tr.observe(frames[i], frames[i + 1], "move_down")
    predicted = np.asarray(tr.predict(before, "move_down"))
    assert iso["residual_cells"] == residual_after_avatar(predicted, reach)
    assert iso["avatar_cells"] == avatar_explained_cells(before, predicted)


def test_residual_isolates_all_three_and_excludes_avatar():
    """HEADLINE: on the on-cell reach the residual contains all three effect regions
    (subset of the ground-truth effect cells) AND excludes every avatar cell."""
    for seed in range(_BASE, _BASE + 8):
        sc, iso, *_ = _drive(seed)
        assert iso["all_three"], f"seed {seed}: not all three isolated"
        assert iso["residual_excludes_avatar"], f"seed {seed}: residual contains avatar"
        assert sc.effect_gt["indicator"] <= iso["residual_cells"]
        assert sc.effect_gt["destination"] <= iso["residual_cells"]
        assert sc.effect_gt["rotation"] <= iso["residual_cells"]


def test_residual_explains_avatar_nontrivially():
    """The tracker's translate ACTUALLY predicts the avatar (avatar footprint ==
    ground truth, non-empty) so residual ∩ avatar == 0 is real confound-removal,
    not a vacuous empty-prediction pass."""
    for seed in range(_BASE, _BASE + 8):
        sc, iso, *_ = _drive(seed)
        assert len(iso["avatar_cells"]) > 0
        assert iso["avatar_cells"] == sc.avatar_gt
        assert iso["avatar_overlap"] == 0


def test_rotation_recognised_as_rot90_k():
    """The ISOLATED exit-glyph rotation reads as rot90:k via 227's UNCHANGED
    recogniser, matching the ground-truth k."""
    for seed in range(_BASE, _BASE + 8):
        sc, iso, *_ = _drive(seed)
        assert iso["exit_rotation"]
        assert iso["rotation_key"] == f"rot90:{sc.k}", (iso["rotation_key"], sc.k)


def test_near_miss_does_not_certify_the_triple():
    """A NEAR-MISS (avatar one quantum hop short, effects absent) yields NO triple —
    the triple is a sufficient on-cell reach certificate."""
    for seed in range(_BASE, _BASE + 8):
        _sc, iso, *_ = _drive(seed, near_miss=True)
        assert not iso["all_three"]
        assert not iso["exit_rotation"]


def test_no_explanation_control_contains_the_avatar():
    """The raw before->reach diff (no avatar explanation) ALWAYS contains the avatar
    cells — the confound 231 hit. The residual removes it."""
    for seed in range(_BASE, _BASE + 8):
        sc, iso, before, reach, after = _drive(seed)
        raw = raw_diff_isolation(before, reach, after, sc.locus)
        assert sc.avatar_gt <= raw["changed_cells"], "raw diff must contain the avatar"
        assert iso["avatar_overlap"] == 0, "residual must not"


def test_powered_isolation_is_ci_separated_from_control():
    """A powered mini-sweep: clean isolation on the residual vs the no-explanation
    control, CI-separated (residual all-clean, control never excludes the avatar)."""
    from arc_ls20_see_measure import wilson, sep
    n = 32
    clean = 0
    ctl = 0
    for seed in range(_BASE, _BASE + n):
        sc, iso, before, reach, after = _drive(seed)
        subset = (sc.effect_gt["indicator"] <= iso["residual_cells"] and
                  sc.effect_gt["destination"] <= iso["residual_cells"] and
                  sc.effect_gt["rotation"] <= iso["residual_cells"])
        clean += bool(iso["all_three"] and iso["residual_excludes_avatar"] and subset)
        raw = raw_diff_isolation(before, reach, after, sc.locus)
        ctl += bool(not (sc.avatar_gt <= raw["changed_cells"]))
    assert sep(wilson(clean, n), wilson(ctl, n)), (clean, ctl)
    assert clean == n and ctl == 0


def test_source_audit_isolation_is_predict_and_residual_no_hardcoded_location():
    """The isolation reads NO scenario ground truth in its decision, hardcodes NO
    effect location, and IS predict-and-residual reusing 224+231."""
    from arc_ls20_triple_measure import source_audit
    a = source_audit()
    assert a["clean"], a
    assert a["isolation_is_predict_and_residual"]
    assert a["isolation_reads_no_scenario_ground_truth_in_decision"]
    assert a["no_hardcoded_effect_location_literal"]
    assert a["reuses_224_tracker_and_231_recogniser"]


def test_fix_is_new_code_reusing_shared_unchanged():
    """Default-OFF byte-identical: the isolation imports the tracker + recogniser +
    grounder from the shared modules (does not reimplement them)."""
    src = (_ROOT / "worlds" / "arc_ls20_triple.py").read_text()
    assert "from worlds.arc_ls20_percell_track import LiveObjectTracker" in src
    assert "recognise_rotation" in src and "ground_destination_flash" in src
    # it must NOT define its own eye / tracker / recogniser
    assert "class ColourChangeEye" not in src
    assert "class LiveObjectTracker" not in src
    assert "def _recognise_transform" not in src
