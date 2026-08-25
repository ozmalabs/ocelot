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


def test_stress_FREEZES_the_learning_state_rather_than_concluding_mastery(arms):
    """What P1 became after the fix, and the delta is the whole point.

    MEASURED BEFORE (v1.0.0): residual 0, progress 0, attended 0 — the compressed
    item was dropped from attention with exactly the profile of something
    mastered. That was the defect this line of work found.

    AFTER (v1.1.0): residual and progress are still 0, but only because the chain
    never ran on an unassessable tick — they are the item's untouched initial
    state, not a verdict — and the item stays attended. Stress freezes what the
    agent knows about the item; it no longer concludes anything about it."""
    c = arms["compressed"]
    assert c["residual"] == 0.0, "an unarrived observation produced a residual"
    assert c["learning_progress"] == 0.0
    assert c["attended"] == 1.0, (
        "the compressed item was dropped from attention — the pipeline is still "
        "reading a frozen state as a mastery verdict")


def test_blindness_no_longer_reads_as_mastery(arms):
    """THE FIX. Previously every field `learning_progress_curiosity` computed was
    identical for an agent that had mastered an item and one that could not
    perceive it — the same collapse `loss == information_loss` was at the manifold,
    one layer up, and live in a shipped seed.

    `learning_progress_curiosity` v1.1.0 skips the residual→progress→gate chain on
    an unassessable tick, so a zero residual is never fabricated from an
    observation that did not arrive. The two arms must now differ."""
    c, m = arms["compressed"], arms["mastered"]
    differing = [f for f in LEARNING_FIELDS if c[f] != m[f]]
    assert differing, (
        "blindness is still indistinguishable from mastery on every learning "
        "field — the assessability guard is not reaching the pipeline")
    assert c["attended"] == 1.0 and m["attended"] == 0.0, (
        f"the compressed item must stay attended and the mastered one must not: "
        f"{c['attended']} vs {m['attended']}")
    assert c["interest"] > 0.0 and m["interest"] == 0.0, (
        f"interest decayed on a tick that established nothing: {c['interest']}")


def test_the_residual_is_never_FABRICATED_from_an_unarrived_observation(arms):
    """The mechanism behind the fix, pinned separately from its consequence. The
    compressed arm's residual is not a measured zero — it is the item's untouched
    initial state, because the chain never ran."""
    c = arms["compressed"]
    assert c["residual"] == 0.0 and c["learning_progress"] == 0.0
    assert c["obs_established"] == 0.0, "the gate did not mark the tick"


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


def test_going_blind_MID_LEARNING_preserves_the_residual_it_had_earned():
    """THE TEST THAT MAKES THE PIPELINE GUARDS LOAD-BEARING, and it exists because
    mutation testing said they were not.

    Every other arm here starts from a zero residual, so a FABRICATED zero and a
    PRESERVED zero are the same number — the very collapse under test, reproduced
    inside the measurement. Dropping the assessability guards from `lp_residual`
    and friends changed nothing until this arm existed.

    An agent that has learned something about an item and then loses the ability
    to perceive it must KEEP what it established. Overwriting that with zero would
    not merely fail to learn — it would erase prior learning and report mastery
    for the erasure."""
    s = M._summary(M._run(False, LEARNABLE, blind_after=12))
    assert s["obs_established"] == 0.0, "the arm is not actually blind at the end"
    assert s["residual"] > 0.0, (
        f"the residual was overwritten with zero once the agent went blind "
        f"({s['residual']}) — an unarrived observation is erasing established "
        f"learning and reading as mastery")
    assert s["attended"] == 1.0, "the item was dropped from attention while unresolved"
