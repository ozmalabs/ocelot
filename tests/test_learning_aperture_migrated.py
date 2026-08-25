"""THE LEARNING HALF — gate for `seeds/learning_aperture_gate.json`.

Prereg: STRESS_COMPRESSES_APERTURE_PREREG.md addendum (block 366500).

`lp_residual` computes `residual = |obs - held|`. An observation the agent cannot
resolve arrives looking like what it already predicted, so the residual is ZERO —
and in `learning_progress_curiosity` zero is not "I could not tell", it is the
signal for "I have mastered this". A compressed learner is therefore dropped from
attention AS IF LEARNED.

The test that carries the finding is
`test_compressed_and_mastered_are_indistinguishable_in_the_learning_signal`. It is
a defect report against a shipped seed, not a feature.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
pytest.importorskip("substrate_rs")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

# NB: the sibling suite guards on matplotlib; this one does not need it —
# `learning_progress_measure` imports numpy, not matplotlib, and copying that
# guard across silently SKIPPED this entire file on its first run.
import learning_aperture_measure as M  # noqa: E402

LEARNABLE = [0, 3, 6, 9, 12, 15, 18, 21]
MASTERED = [0, 0, 0, 0, 0, 0, 0, 0]
LEARNING_FIELDS = ("residual", "fast_res", "slow_res", "learning_progress",
                   "smoothed_progress", "interest", "attended")


@pytest.fixture(scope="module")
def arms():
    return {
        "learnable": M._summary(M._run(False, LEARNABLE)),
        "compressed": M._summary(M._run(True, LEARNABLE)),
        "mastered": M._summary(M._run(False, MASTERED)),
    }


def test_a_regulated_agent_learns_the_learnable_item(arms):
    """P5, the positive control. Without it every zero below is consistent with a
    pipeline that never ran."""
    a = arms["learnable"]
    assert a["residual"] > 0.0, "the regulated agent saw no residual at all"
    assert a["learning_progress"] != 0.0
    assert a["attended"] == 1.0
    assert a["obs_established"] == 1.0


def test_stress_makes_the_item_look_LEARNED(arms):
    """P1. Not "the signal degrades" — the item is dropped from attention with
    exactly the profile of something mastered."""
    c = arms["compressed"]
    assert c["residual"] == 0.0
    assert c["learning_progress"] == 0.0
    assert c["attended"] == 0.0


def test_compressed_and_mastered_are_indistinguishable_in_the_learning_signal(arms):
    """THE FINDING, and it is a defect in a shipped seed rather than a feature.

    Every field `learning_progress_curiosity` computes is identical for an agent
    that has mastered an item and an agent that cannot perceive it. This is the
    same collapse as `loss == information_loss` was at the manifold, one layer up:
    residual-zero-because-mastered and residual-zero-because-blind are one number.

    If this test ever fails, the seed has grown a way to tell them apart, which is
    the fix — update the results document rather than this expectation."""
    c, m = arms["compressed"], arms["mastered"]
    for field in LEARNING_FIELDS:
        assert c[field] == m[field], (
            f"{field} differs ({c[field]} vs {m[field]}) — the learning signal "
            f"now distinguishes blindness from mastery")


def test_only_establishment_separates_them(arms):
    """P3. The distinction exists only because the gate writes it; nothing in
    `learning_progress_curiosity` reads it yet, which is the point."""
    assert arms["compressed"]["obs_established"] == 0.0
    assert arms["mastered"]["obs_established"] == 1.0


@pytest.mark.parametrize("ticks", [24, 48, 96, 192])
def test_exposure_does_not_recover_the_compressed_learner(ticks):
    """P4, matching the manifold half. A gain is a thing more exposure overcomes;
    an aperture is not. Eight times the exposure changes nothing."""
    s = M._summary(M._run(True, LEARNABLE, ticks=ticks))
    assert s["max_residual"] == 0.0, f"exposure {ticks} produced a residual"
    assert s["max_progress"] == 0.0


def test_the_gate_actually_fires():
    """The anti-confound. The first run of this measurement was WRONG: the guard
    compared `obs` to its gated value, which in the compressed arm already equalled
    `held`, so the rule never fired and the residual-zero result reproduced with no
    gate present at all. `obs_established` is the witness that the rule ran, and it
    is asserted here as well as in the arms so a future regression cannot make this
    file pass while measuring nothing."""
    compressed = M._summary(M._run(True, LEARNABLE))
    assert compressed["obs_established"] == 0.0, (
        "the gate did not fire — this suite would be measuring the item's "
        "initial state, not a compressed observation")
    assert compressed["obs"] == 0.0
