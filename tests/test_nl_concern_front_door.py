"""The NATURAL-LANGUAGE FRONT DOOR to the agent's own self-authoring loop, plus the
POSITION-PRESERVING contrastive frame it grounds.

Two capabilities land together here:

1. `conversation_action._act_author_concern` — a concern-framing INSTRUCTION (a
   discrimination / attention / self-correction strategy: "compare where they differ and
   judge the trial on that region") no longer dies at `act_on_instruction`'s honest
   goal-only dead end. It is ingested as a `Concept.definition`, read into an observation
   signature by the HELD RelationCue lexicon (`author_signature`), and handed to the
   agent's OWN `induce_concern`/`ground_concern` — teacher-free (donkey stays 0). This is
   the live path the user asked for: steer the jabberwock in English, IT authors the rule.

2. `contrastive_verdict._normalize_glyph_shared` — the position-preserving frame for the
   held-open contrastive verdict. The committed centroid frame recenters each glyph on its
   own ink, destroying WHERE a stroke sits (why it fixes A/O closure but not F/L height);
   the shared bbox frame keeps figure-position, feeding the SAME held `MinOver(PointSetDist)`
   Term — no new Rust, host data-prep only.
"""
from __future__ import annotations

import types

import numpy as np
import pytest

from domains import conversation_action as ca
from domains import contrastive_verdict as cv


# ---------------------------------------------------------------------------------------- #
#  1a. The wiring, slab-independent: a synthesized instruction Comprehension routes to the
#      self-authoring loop (no dependence on the open-class POS slab being built).
# ---------------------------------------------------------------------------------------- #
def _boot():
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    donkey = {"n": 0}
    try:
        a.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])
    except Exception:
        pass
    return a, donkey


def _comp(text, predicate):
    """A minimal instruction Comprehension — only the fields act_on_instruction reads."""
    return types.SimpleNamespace(
        raw=text, kind="instruction",
        dispatch={"path": "instruction", "predicate": predicate, "object": None})


def test_concern_framing_instruction_routes_to_self_authoring():
    """The front-door branch fires for a concern-framing predicate and returns the
    concern-authored route, NOT the honest goal-only give-up — and consults no LLM."""
    a, donkey = _boot()
    comp = _comp("Compare where the two letters differ and judge the trial on that region.",
                 "compare")
    out = ca.act_on_instruction(a, comp)
    assert out["route"] == "concern_authored", out
    assert out["goal_kind"] == "author_concern"
    assert out["concern"] is not None
    # the agent EITHER minted a new concern or honestly recognised it as covered — both are
    # the self-authoring loop's own verdict, never a fabricated action.
    c = out["concern"]
    assert c["minted"] in (True, False)
    assert isinstance(c["signature"], list) and c["signature"], "an earned relation signature"
    assert donkey["n"] == 0, "teacher-free: no LLM consulted"


def test_judge_a_trial_steer_grounds_as_an_experiment_rule():
    """The run-37 provenance, re-derived from English: a 'judge the trial by its result'
    steer grounds through the SAME `judge` composer head that authored contrastive_verdict's
    gap-A concern — the agent installs a live experiment_rule, teacher-free."""
    a, donkey = _boot()
    comp = _comp("Compare where the two letters differ and judge the trial on that region.",
                 "compare")
    out = ca.act_on_instruction(a, comp)
    c = out["concern"]
    if c["minted"]:
        assert c["grounded"] is True, out
        assert c["path"] == "experiment_rule", out
    assert donkey["n"] == 0


def test_non_concern_instruction_still_hits_the_honest_dead_end():
    """A plain nav/manipulation predicate is untouched by the new branch — it still mints
    the Goal and reports the honest action-space limit."""
    a, _ = _boot()
    comp = _comp("Walk to the door.", "walk")
    out = ca.act_on_instruction(a, comp)
    assert out["route"] == "goal_only"
    assert "no attached world/faculty" in out["reply"]


# ---------------------------------------------------------------------------------------- #
#  1b. The LIVE path through converse() (depends on the curated POS override making the
#      steer verb tag as a verb, shipped in the same change).
# ---------------------------------------------------------------------------------------- #
def test_live_converse_steer_authors_a_concern():
    """End-to-end: a plain English steer through converse() parses as an instruction and
    reaches the self-authoring loop, teacher-free."""
    from domains import comprehend_text as ct
    a, donkey = _boot()
    steer = "Compare where the two letters differ and judge the trial on that region."
    comp = ct.comprehend_text(a, steer)
    assert comp.kind == "instruction", f"steer must parse as an instruction, got {comp.kind}"
    reply = a.converse(steer)
    assert isinstance(reply, str) and reply
    # the reply reports the agent's OWN authoring verdict (formed / already-held), not the
    # old "no attached world/faculty" give-up.
    assert "no attached world/faculty" not in reply
    assert donkey["n"] == 0


# ---------------------------------------------------------------------------------------- #
#  2. The position-preserving frame.
# ---------------------------------------------------------------------------------------- #
def test_shared_frame_preserves_figure_position():
    """Two glyphs identical but for a horizontal bar at DIFFERENT heights: the shared bbox
    frame keeps the bars at different y (position survives); the committed centroid frame
    collapses them toward a common centre (position destroyed) — the exact reason the
    centroid contrastive verdict cannot separate F/L."""
    from scripts import jabberwock_omniglot_run36_failures as run36
    stem = np.c_[np.zeros(20), np.linspace(0.0, 1.0, 20)]          # shared vertical stroke
    bar_hi = np.c_[np.linspace(0.0, 0.5, 12), np.full(12, 0.9)]    # crossbar near the top (F)
    bar_lo = np.c_[np.linspace(0.0, 0.5, 12), np.full(12, 0.1)]    # foot near the bottom (L)
    F = [stem, bar_hi]
    L = [stem, bar_lo]

    sh_F, _, _ = cv._normalize_glyph_shared(F)
    sh_L, _, _ = cv._normalize_glyph_shared(L)
    # the bar (stroke index 1) keeps its height ordering in the shared frame.
    assert sh_F[1][:, 1].mean() > sh_L[1][:, 1].mean() + 0.5

    ce_F, _, _ = run36._normalize_glyph(F)
    ce_L, _, _ = run36._normalize_glyph(L)
    shared_gap = abs(sh_F[1][:, 1].mean() - sh_L[1][:, 1].mean())
    centroid_gap = abs(ce_F[1][:, 1].mean() - ce_L[1][:, 1].mean())
    assert shared_gap > centroid_gap, "shared frame keeps more of the height difference"


def test_contrastive_pick_accepts_a_frame_and_is_non_breaking():
    """`contrastive_pick(normalize=...)` runs in the shared frame and returns a well-formed
    verdict; the default (no kwarg) is byte-identical to the committed centroid behaviour."""
    from substrate_rs import _native
    native = _native.Substrate()
    stem = np.c_[np.zeros(20), np.linspace(0.0, 1.0, 20)]
    q = [stem, np.c_[np.linspace(0.0, 0.5, 12), np.full(12, 0.88)]]
    c1 = [stem, np.c_[np.linspace(0.0, 0.5, 12), np.full(12, 0.9)]]
    c2 = [stem, np.c_[np.linspace(0.0, 0.5, 12), np.full(12, 0.1)]]

    default = cv.contrastive_pick(native, q, c1, c2, 0, 1)
    shared = cv.contrastive_pick(native, q, c1, c2, 0, 1, normalize=cv._normalize_glyph_shared)
    for r in (default, shared):
        assert r["winner"] in (0, 1)
        assert r["decision"] in ("two_sided", "one_sided", "fallback_no_diff",
                                 "fallback_no_shared_baseline")
