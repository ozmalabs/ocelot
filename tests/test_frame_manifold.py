"""test_frame_manifold — THE INTERLOCUTOR MANIFOLD AS A FRAME (the creator's Frame ontology,
2026-07-04), and how AUDIENCE-ADAPTATION + REFERENCE-LIVENESS now fall out of FRAME-MEMBERSHIP,
replacing the coarse cue-table classifiers. DISCRIMINATIVE, donkey=0.

  * a Frame is a set of DIMENSIONS with relative log weighting (domains/frame.py);
  * the interlocutor's manifold is built AS A FRAME from what they weight (type + register);
  * "is concept X foreign?" == "is X's dimension NOT in the interlocutor's frame?" (a query);
  * "is referent R live?" == "is R's world a dimension of the interlocutor's frame?" (a query);
  * the SAME correct outputs are reproduced (Vane adapts, gamer BioShock live, rabbit-hole
    universal) — now falling out of frame-membership, and it GENERALIZES.
"""
from __future__ import annotations

import inspect
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pytest

from domains import frame as fr
from domains import audience_adaptation as aa
from domains import sense_of_reference as sr


AREAS = ["engineering", "video_coding_theory", "computer_architecture", "communication",
         "mathematics", "databases_and_storage", "embedded_iot_realtime",
         "security_and_cryptography", "art_design_drawing", "cloud_infrastructure",
         "machine_learning", "philosophy"]

VANE = {"id": "Cornelius Vane", "observed": True,
        "known_concepts": ["ethics", "virtue", "philosophy", "morality", "propriety", "courtesy"]}
TECHNICAL = {"id": "dev", "observed": True,
             "known_concepts": ["python", "rust", "algorithm", "compiler", "server", "database"]}
DEFAULT = {"id": "user", "observed": False, "known_concepts": []}

GAMER = {"id": "gamer", "observed": True,
         "known_concepts": ["bioshock", "rapture", "respawn", "playthrough", "controller"]}
WYK = "Would you kindly open the door for me?"


@pytest.fixture(scope="module")
def agent():
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


# =========================================================================== #
#  MANIFOLD-AS-FRAME — the interlocutor's frame is the set of worlds they weight.
# =========================================================================== #

def test_vane_frame_lacks_the_modern_tech_dimension(agent):
    """Vane's manifold (formal, committed period) is a frame with the `universal` world but NOT the
    `modern_tech` world — modern-tech concepts have no dimension to land on."""
    f = aa.interlocutor_frame(agent, VANE)
    assert fr.in_frame(f, aa.DIM_UNIVERSAL, agent) is True
    assert fr.in_frame(f, aa.DIM_MODERN_TECH, agent) is False       # the modern world is absent


def test_technical_and_default_frames_hold_the_modern_tech_dimension(agent):
    """A technical manifold — and an unobserved/default one — holds the modern world, so nothing
    modern is foreign (the firing gate is folded into which dims the frame carries)."""
    assert fr.in_frame(aa.interlocutor_frame(agent, TECHNICAL), aa.DIM_MODERN_TECH, agent) is True
    assert fr.in_frame(aa.interlocutor_frame(agent, DEFAULT), aa.DIM_MODERN_TECH, agent) is True


# =========================================================================== #
#  AUDIENCE-ADAPTATION VIA FRAME-MEMBERSHIP (headline) — Vane reproduced.
# =========================================================================== #

def test_audience_adaptation_is_a_frame_membership_query(agent):
    """The foreign-check is now a FRAME QUERY, not the cue table: a concept is foreign IFF its
    dimension is not in the interlocutor's frame."""
    f = aa.interlocutor_frame(agent, VANE)
    split = aa.split_by_manifold(agent, AREAS, VANE)
    for c in AREAS:
        foreign_by_frame = not fr.in_frame(f, aa.concept_dimension(c), agent)
        if c in split["foreign"]:
            assert foreign_by_frame, c                              # foreign <=> dimension absent
        else:
            # live either because its dimension is in the frame, or grounded-known common ground.
            assert (not foreign_by_frame) or (c in split["grounded_known"]), c
    # and the source really routes through frame.in_frame (not the retired cue-table branch).
    assert "in_frame" in inspect.getsource(aa.split_by_manifold)


def test_vane_adapts_reproduced_verbatim(agent):
    """Reproduce the Vane adaptation verbatim — modern-tech collapsed to the umbrella, period domains
    land — now via frame-membership."""
    r = aa.adapt_concepts(agent, AREAS, VANE)
    assert r["adapted_flag"] is True
    assert " ".join(r["adapted"]) == ("engineering communication mathematics art_design_drawing "
                                       "philosophy certain modern arts unfamiliar in your world")
    for foreign in ("video_coding_theory", "cloud_infrastructure", "machine_learning"):
        assert foreign in r["foreign"] and foreign not in r["adapted"]


def test_technical_keeps_full_list_and_default_byte_identical(agent):
    assert aa.adapt_concepts(agent, AREAS, TECHNICAL)["adapted"] == AREAS
    assert aa.adapt_concepts(agent, AREAS, DEFAULT)["adapted"] == AREAS


def test_grounded_modern_concept_rescued_by_frame_path(agent):
    """GENERALIZES per-concept: a modern concept Vane actually holds is rescued LIVE (observed common
    ground overrides the frame), while the rest of the modern world stays foreign."""
    vane_knows_ml = dict(VANE)
    vane_knows_ml["known_concepts"] = VANE["known_concepts"] + ["machine_learning"]
    split = aa.split_by_manifold(agent, AREAS, vane_knows_ml)
    assert "machine_learning" in split["live"] and "machine_learning" in split["grounded_known"]
    assert "video_coding_theory" in split["foreign"]               # rest of the modern world still out


def test_live_through_converse_adapts_for_a_formal_register():
    """LIVE end-to-end: a formal-register greeting then 'How are you organised?' -> adapted answer,
    the modern-tech domains collapsed via the manifold frame."""
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    a.converse("Good day. I am Cornelius Vane, a humble scholar of natural philosophy.",
               a.classify_speech_act("Good day."))
    reply = a.converse("How are you organised?", a.classify_speech_act("How are you organised?"))
    assert reply.startswith("I am organised into")
    assert "unfamiliar in your world" in reply
    for foreign in ("video_coding_theory", "cloud_infrastructure", "machine_learning"):
        assert foreign not in reply
    for live in ("mathematics", "philosophy", "engineering"):
        assert live in reply


# =========================================================================== #
#  REFERENCE-LIVENESS VIA FRAME-MEMBERSHIP — gamer BioShock / Vane / universal.
# =========================================================================== #

def test_reference_frame_holds_the_worlds_the_manifold_weights():
    """The manifold's reference frame (value form) carries the `universal` world always, plus each
    world-type the manifold has evidence for — the dimensions reference-liveness queries."""
    gamer_frame = sr.manifold_reference_frame(GAMER["known_concepts"], "gamer")
    assert fr.in_frame(gamer_frame, "gamer") is True
    assert fr.in_frame(gamer_frame, "universal") is True
    vane_frame = sr.manifold_reference_frame(VANE["known_concepts"], "formal")
    assert fr.in_frame(vane_frame, "gamer") is False               # the gamer world is absent


def test_would_you_kindly_live_for_gamer_speech_pattern_for_vane():
    """The minimal pair reproduced via frame-membership: BioShock's world (`gamer`) is IN the gamer
    frame -> live; it is ABSENT from Vane's formal frame -> a plain speech pattern."""
    g = sr.decode_reference(GAMER, WYK)
    v = sr.decode_reference(VANE, WYK)
    assert g["is_reference"] is True and g["liveness"] == "live" and g["source"] == "BioShock"
    assert v["is_reference"] is False and v["liveness"] == "speech_pattern"
    assert g["phrase"] == v["phrase"]                              # SAME string, opposite call
    assert g["residual"] == [] and v["residual"] != []            # residual contract from membership


def test_graduated_concept_universal_in_every_frame():
    """'down the rabbit hole' has graduated to the `universal` dimension — in EVERY frame, live for
    any manifold."""
    for manifold in (GAMER, VANE, {"known_concepts": []}):
        v = sr.decode_reference(manifold, "we went down the rabbit hole on this")
        assert v["is_reference"] is True and v["liveness"] == "concept"


def test_reference_liveness_source_routes_through_frame():
    assert "in_frame" in inspect.getsource(sr.decode_reference)
    assert "collapse_residual" not in inspect.getsource(sr.decode_reference)


# =========================================================================== #
#  CONTEXT + SHAPE FRAMES — the context/shape are already weighted dim-sets.
# =========================================================================== #

def test_context_frame_weights_salient_dims_above_steady(agent):
    """The context model exposed AS A FRAME: its codebook dims, the salient ones log-weighted above
    the steady ones (salience = the relative weighting)."""
    from domains import context_model as cm
    cm.observe_turn(agent, "hello there friend", {"place": "chat"})
    cf = cm.context_frame(agent)
    dims = fr.frame_dims(cf, agent)
    assert set(dims) >= set(cm.SEEDED_DIMS)
    salient = set((getattr(agent, "_last_context_turn", None) or {}).get("salient_dims") or [])
    for d in salient:
        # a salient dim sits strictly above a steady one when both are present.
        steady = [x for x in dims if x not in salient]
        if steady:
            assert fr.relative_weight(cf, d, steady[0], agent=agent) > 0.0


def test_shape_frame_log_weighted_by_realisation_count(agent):
    """The agent's SHAPE exposed AS A FRAME: the meta-shapes log-weighted by realisation count, so the
    'Nx the next' ratio reads straight off the frame as a relative weight (= log of the count ratio)."""
    import math
    from domains.reflective_faculty import shape_frame
    from domains.analogical_thinking import metashape_realisation_counts
    sf = shape_frame(agent)
    counts = metashape_realisation_counts(agent)
    ranked = sorted(counts.items(), key=lambda kv: -kv[1])
    assert len(ranked) >= 2 and ranked[0][0] in fr.frame_dims(sf, agent)
    primary, second = ranked[0], ranked[1]
    if second[1]:
        rw = fr.relative_weight(sf, primary[0], second[0], agent=agent)
        assert math.exp(rw) == pytest.approx((primary[1] + 1.0) / (second[1] + 1.0), rel=1e-6)
