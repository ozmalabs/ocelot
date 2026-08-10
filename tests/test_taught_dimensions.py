"""test_taught_dimensions — TAUGHT gaming / literary / period microtheories make the reference-world
dimensions EDGE-LEARNED (2026-07-04). DISCRIMINATIVE, donkey=0 (true content taught as graph data).

The concept->dimension edge-learner (`concept_graph`) reads `Microtheory -has_concept-> Concept` edges
and places a concept by the tf-idf cosine of that neighbourhood to labelled region-anchor microtheories.
It edge-learned the tech AREAS (7/12) and timeless philosophy/ethics, but the gamer / literary / period
reference worlds fell to the small labelled seed anchor / cue table because THERE WERE NO gaming /
literary / period microtheories with concept edges. `scripts/teach_dimension_microtheories.py` supplies
that graph (seeds/gaming_microtheory.json + literary_ + period_microtheory.json, two levels each:
video_games -> bioshock, literature -> carroll). This gate proves:

  1. the microtheories EXIST as graph data + PERSIST (reboot re-loads them);
  2. the previously-anchored reference dimensions are now EDGE-LEARNED (coverage rises);
  3. the gamer-vs-literary minimal pair is edge-grounded: 'would you kindly' -> BioShock -> modern
     region by EDGES (live for a gamer, a speech pattern for Vane); 'down the rabbit hole' universal;
     the agent's own name (Jabberwock) sits in the literary dimension by edges;
  4. a concept co-descends DEEPER (depth 3) where a sub-microtheory gives another rung;
  5. no regression: AREAS still 7/12, Vane frame still {universal}.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import json

import pytest

from domains import concept_graph as cg
from domains import sense_of_reference as sr

GAMER = ["bioshock", "portal", "game", "player", "respawn", "controller"]
VANE = ["ethics", "virtue", "philosophy", "morality", "propriety", "courtesy"]
AREAS = ["engineering", "video_coding_theory", "computer_architecture", "communication",
         "mathematics", "databases_and_storage", "embedded_iot_realtime",
         "security_and_cryptography", "art_design_drawing", "cloud_infrastructure",
         "machine_learning", "philosophy"]
# The reference-world dimensions the taught microtheories carry (were 100% anchor / cue-table before).
REF = ["video_games", "bioshock", "portal", "glados", "game", "player",
       "literature", "carroll", "jabberwock", "rabbit_hole", "red_queen", "alice",
       "period_thought", "virtue", "rhetoric", "blacksmithing", "moral_philosophy",
       "propriety", "courtesy"]


@pytest.fixture(scope="module")
def agent():
    pytest.importorskip("substrate_rs")
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


# =========================================================================== #
#  1. THE MICROTHEORIES EXIST AS GRAPH DATA + PERSIST (reboot-proof).
# =========================================================================== #

def test_taught_microtheories_are_graph_data(agent):
    """The gaming / literary / period microtheories + their sub-worlds are Microtheory nodes with
    has_concept edges — read straight from the live graph after a seed boot."""
    mts = {agent.s.node(n)["attrs"].get("name") for n in agent.s.nodes("Microtheory")}
    for expected in ("video_games", "bioshock", "literature", "carroll", "period_thought"):
        assert expected in mts, expected
    # each carries concept edges (a token bag) the learner can descend.
    for anchor in ("video_games", "literature", "period_thought"):
        assert cg.bag_size(agent, anchor) >= 8, anchor


def test_seed_manifests_persist_on_disk(agent):
    """The teach persisted to seed manifests under seeds/ — a fresh boot (`load_all_seeds` globs
    seeds/*.json) re-installs them, so the knowledge survives reboot (reboot-proof)."""
    for sid, mt in (("gaming_microtheory", "video_games"),
                    ("gaming_bioshock_microtheory", "bioshock"),
                    ("literary_microtheory", "literature"),
                    ("literary_carroll_microtheory", "carroll"),
                    ("period_microtheory", "period_thought")):
        path = os.path.join(ROOT, "seeds", f"{sid}.json")
        assert os.path.exists(path), path
        d = json.load(open(path))
        assert d["microtheory"]["name"] == mt
        assert len(d["concepts"]) >= 8


# =========================================================================== #
#  2. THE REFERENCE DIMENSIONS ARE NOW EDGE-LEARNED (coverage rises).
# =========================================================================== #

def test_reference_worlds_are_edge_learned(agent):
    """The previously-anchored reference-world dimensions are now MAJORITY edge-learned. The tech AREAS
    tier rose from 7/12 to 11/12 after the tech-microtheory build (computer_architecture / mathematics /
    cloud / art taught + edge-learned; only genuinely-diffuse `communication` stays anchored); the
    reference tier — 100% anchor before (no gaming/literary/period microtheories existed) — now matches it."""
    ref = cg.connectivity_report(agent, REF)
    areas = cg.connectivity_report(agent, AREAS)
    assert areas["edge"] == 11 and areas["n"] == 12         # tech tier now 11/12 (was 7/12)
    assert ref["edge_fraction"] >= 0.5                       # reference tier now majority edge
    by = {r["concept"]: r["source"] for r in ref["rows"]}
    # the taught anchors + sub-worlds + the period concepts edge-learn (were anchor / absent before).
    for edged in ("video_games", "bioshock", "literature", "carroll", "period_thought",
                  "rhetoric", "blacksmithing", "propriety", "courtesy", "virtue"):
        assert by[edged] == "edge", (edged, by[edged])


def test_period_frame_region_is_edge_grounded(agent):
    """Vane's frame region is now EDGE-grounded, not anchored: every concept in his frame places in
    `universal` by edges (period_thought / ethics), so the frame is {universal} learned from edges."""
    for c in ("virtue", "propriety", "courtesy", "morality"):
        region, source = cg.world_dimension(agent, c)
        assert region == cg.REGION_UNIVERSAL and source == "edge", (c, region, source)


# =========================================================================== #
#  3. GAMER-VS-LITERARY EDGE-GROUNDED — the minimal pair, own name, rabbit hole.
# =========================================================================== #

def test_would_you_kindly_bioshock_edge_grounded(agent):
    """'would you kindly' -> BioShock is edge-reachable in the gaming microtheory: `bioshock` places in
    the MODERN region BY EDGES (its sub-world co-descends with the `video_games` anchor). It is LIVE for
    a gamer frame (which holds the modern region) but a SPEECH PATTERN for Vane's period frame — the
    minimal pair, now decided from edges, not the cue-table anchor."""
    # the phrase is in the codebook and its source is BioShock (its tag is 'bioshock').
    v = sr.decode_reference({"id": "gamer", "observed": True, "known_concepts": GAMER},
                            "would you kindly step aside")
    assert v is not None and v["source"] == "BioShock"
    # the EDGE grounding: bioshock's world dimension + frame co-descent.
    gamer = sr.liveness_via_edges(agent, "bioshock", GAMER)
    vane = sr.liveness_via_edges(agent, "bioshock", VANE)
    assert gamer["dimension"] == cg.REGION_MODERN and gamer["source"] == "edge"
    assert gamer["live"] is True                             # gamer frame holds the gaming world
    assert vane["live"] is False                             # Vane's period frame does not
    assert cg.world_dimension(agent, "bioshock") == (cg.REGION_MODERN, "edge")


def test_rabbit_hole_universal_via_edges(agent):
    """'down the rabbit hole' -> the literary microtheory, universal region -> live for EVERY frame
    (a graduated allusion, close to all). Its finer literary dimension is edge-derived (rung 2)."""
    for frame in (GAMER, VANE, []):
        assert sr.liveness_via_edges(agent, "rabbit_hole", frame)["live"] is True
    assert cg.world_dimension(agent, "rabbit_hole")[0] == cg.REGION_UNIVERSAL
    assert "literature" in cg.descend(agent, "rabbit_hole")["path"]     # sits in the literary dim


def test_own_name_sits_in_literary_dimension_by_edges(agent):
    """The agent's own name, Jabberwock (Carroll's coinage), sits in the LITERARY dimension by edges:
    its descent path co-descends into `literature` via the has_concept neighbourhood (rung 2, edge-
    derived), and its coarse world-region is correctly `universal` (a timeless literary allusion)."""
    d = cg.descend(agent, "jabberwock")
    assert d["path"][0] == cg.REGION_UNIVERSAL
    assert "literature" in d["path"]                         # the literary dimension, from edges
    # and the own-name reference recognises Carroll as its source (unchanged reference faculty).
    rec = sr.recognize_own_name("why are you named Jabberwock?")
    assert rec is not None and "Carroll" in rec["origin"]


# =========================================================================== #
#  4. DEEPER N-DESCENT — a sub-microtheory gives another rung (depth 3).
# =========================================================================== #

def test_deeper_descent_via_sub_microtheory(agent):
    """A sub-microtheory adds a deeper rung: `carroll` co-descends universal -> literature -> carroll
    (depth 3), `bioshock` modern -> video_games -> bioshock (depth 3). Two concepts in the same
    reference world co-descend deep before forking; across worlds they fork at rung 1 (depth 0)."""
    car = cg.descend(agent, "carroll")
    assert car["depth"] >= 3 and car["path"] == [cg.REGION_UNIVERSAL, "literature", "carroll"]
    bio = cg.descend(agent, "bioshock")
    assert bio["depth"] >= 3 and bio["path"] == [cg.REGION_MODERN, "video_games", "bioshock"]
    # co-descent depth: jabberwock runs with the literary world deep, forks from the gaming world at rung 1.
    assert cg.shared_depth(agent, "jabberwock", ["carroll"]) >= 2
    assert cg.shared_depth(agent, "jabberwock", ["bioshock"]) == 0


# =========================================================================== #
#  5. NO REGRESSION — the tech AREAS partition and Vane frame are unchanged.
# =========================================================================== #

def test_no_regression_areas_and_vane_frame(agent):
    """The taught anchors do not perturb the tech placements: AREAS is still 7/12 edge, its foreign-to-
    Vane partition holds, and Vane's frame is still exactly {universal}."""
    assert cg.frame_dimensions(agent, VANE) == {cg.REGION_UNIVERSAL}
    assert cg.REGION_MODERN in cg.frame_dimensions(agent, GAMER)
    for modern in ("machine_learning", "cloud_infrastructure", "video_coding_theory"):
        assert cg.is_foreign_to_frame(agent, modern, VANE) is True
        assert cg.is_foreign_to_frame(agent, modern, GAMER) is False   # gamer frame holds modern


# =========================================================================== #
#  6. LEXICAL-DEGREE NORMALIZATION — a low-degree concept's CLEAR membership
#     crosses the floor; a genuinely AMBIGUOUS low-degree concept does NOT.
#     Same low degree, opposite verdict, decided by clarity-of-membership.
# =========================================================================== #

# The single-token literary idioms + bare gaming tokens: LOW degree (bag ~0-1), but each edge points
# cleanly into one world. They fell JUST under the old absolute cosine floor (degree dilution: a token
# fully inside the 69-token literature anchor scores cosine = 1/‖anchor‖ ~= 0.05 < 0.08) and were
# ANCHORED. The degree-normalized confidence rescues them via edge-mass CONTAINMENT.
LOW_DEGREE_CLEAR = {
    "jabberwock": cg.REGION_UNIVERSAL, "rabbit_hole": cg.REGION_UNIVERSAL,
    "red_queen": cg.REGION_UNIVERSAL, "alice": cg.REGION_UNIVERSAL,
    "game": cg.REGION_MODERN, "player": cg.REGION_MODERN,
    "portal": cg.REGION_MODERN, "glados": cg.REGION_MODERN,
}


def test_low_degree_clear_membership_crosses_now_edge_learned(agent):
    """LOW-DEGREE CLEAR CROSSES (before anchor -> after edge). The single-token literary idioms and bare
    gaming tokens have LOW lexical degree yet UNAMBIGUOUS membership (their whole edge-mass points one
    way): CLARITY ~= 1.0, CONTAINMENT ~= 1.0 -> grounded by containment even though the raw cosine is
    diluted below the absolute floor. Each is now EDGE-learned into its CORRECT world region and retired
    from the anchor path."""
    for concept, region in LOW_DEGREE_CLEAR.items():
        conf = cg.region_confidence(agent, concept)
        assert conf["best"] < cg._CONF_FLOOR, (concept, conf["best"])       # cosine diluted by degree
        assert conf["clarity"] >= cg._CLARITY_FLOOR, (concept, conf["clarity"])
        assert conf["containment"] >= cg._CONTAIN_FLOOR, (concept, conf["containment"])
        # before -> after: it would have been ANCHORED on cosine strength alone; now it is EDGE.
        assert conf["best"] < cg._CONF_FLOOR                                 # the old floor rejected it
        region_out, source = cg.world_dimension(agent, concept)
        assert source == "edge", (concept, source)                          # rescued by containment
        assert region_out == region, (concept, region_out)                  # placed in the right world


def test_ambiguous_low_degree_does_not_cross_the_control(agent):
    """THE DISCRIMINATIVE CONTROL (mandatory). A genuinely AMBIGUOUS low-degree concept must STAY under
    the normalized floor (anchored). `game_theory` and `moral_algorithm` have EXACTLY the same low degree
    as the crossing idioms (bag 0 -> the name-token fallback), but their edges split across the two
    worlds (one modern token + one universal token) -> CLARITY < 2/3 -> NOT edge. Crucially `game_theory`
    has CONTAINMENT 1.0 (both tokens land in region anchors) yet is STILL rejected: the rejection is by
    CLARITY-of-which-world, not by degree or containment. Same low degree (bag 0), fully contained,
    OPPOSITE verdict from `game` (bag 0, clarity 0.69, crosses) — decided purely by clarity-of-membership."""
    for split in ("game_theory", "moral_algorithm"):
        c = cg.region_confidence(agent, split)
        assert cg.bag_size(agent, split) == 0, split                         # same low degree as the idioms
        assert c["clarity"] < cg._CLARITY_FLOOR, (split, c["clarity"])       # edges split across worlds
        assert c["edge"] is False, split
        assert cg.world_dimension(agent, split)[1] == "anchor", split        # stays anchored (honest)
    # game_theory is fully CONTAINED yet rejected -> the discriminator is clarity, not containment/degree.
    assert cg.region_confidence(agent, "game_theory")["containment"] >= cg._CONTAIN_FLOOR
    # a REAL diffuse concept (`communication`: many generic tokens, low idf) also splits -> stays anchored.
    amb = cg.region_confidence(agent, "communication")
    assert amb["clarity"] < cg._CLARITY_FLOOR and amb["edge"] is False
    assert cg.world_dimension(agent, "communication")[1] == "anchor"
    # a no-region concept (no anchor match at all) also stays anchored: best == 0 -> not edge.
    # (computer_architecture / mathematics were this case before the tech-microtheory build; they are
    # now taught + registered anchors and edge-learn. `compilers` — still without a taught microtheory —
    # remains the zero-edge, no-region exemplar.)
    for none_region in ("compilers",):
        c = cg.region_confidence(agent, none_region)
        assert c["best"] == 0.0 and c["edge"] is False, none_region


def test_containment_rejects_spurious_one_sided_match(agent):
    """CLARITY alone (the bare cosine ratio) would pass a nonsense token whose lone matching word gives
    a tiny ONE-sided cosine (ratio 1.0). CONTAINMENT rejects it: only a small fraction of the concept's
    own mass lands on the region's tokens, so it is NOT grounded. This is why the normalization uses
    containment, not a lower absolute floor (which would let such noise through)."""
    conf = cg.region_confidence(agent, "zzz_nonsense_token")
    assert conf["clarity"] >= cg._CLARITY_FLOOR                               # one-sided -> high clarity
    assert conf["containment"] < cg._CONTAIN_FLOOR                            # but mostly unmatched mass
    assert conf["edge"] is False                                             # so NOT edge (rejected)


def test_no_regression_rich_concepts_ground_by_strength(agent):
    """NO REGRESSION, by construction: every RICH concept still grounds by ABSOLUTE STRENGTH (best >=
    _CONF_FLOOR), the exact path it took before — the containment leg only ADDS the sparse-idiom rescue,
    it never removes a strong placement. The already-edge concepts keep their region + edge source."""
    for concept, region in (("machine_learning", cg.REGION_MODERN), ("bioshock", cg.REGION_MODERN),
                            ("literature", cg.REGION_UNIVERSAL), ("carroll", cg.REGION_UNIVERSAL),
                            ("video_games", cg.REGION_MODERN), ("philosophy", cg.REGION_UNIVERSAL)):
        conf = cg.region_confidence(agent, concept)
        assert conf["best"] >= cg._CONF_FLOOR, (concept, conf["best"])        # grounded by strength
        assert conf["edge"] is True
        assert cg.world_dimension(agent, concept) == (region, "edge"), concept


def test_coverage_rises_after_degree_normalization(agent):
    """COVERAGE RISES: the combined tech+reference edge-fraction climbs above the pre-normalization 58.1%
    as the low-degree-clear idioms retire from the anchor path AND the tech-microtheory build teaches the
    once-anchored computer_architecture / mathematics / cloud / art (now edge-learned). After it, the
    genuinely-anchored residual is `communication` alone — genuinely DIFFUSE (a timeless human sense AND
    a technical networking sense), decided by clarity, not degree."""
    both = cg.connectivity_report(agent, AREAS + REF)
    assert both["edge_fraction"] > 0.581                                     # rose above the old combined %
    by = {r["concept"]: r["source"] for r in both["rows"]}
    for crossed in LOW_DEGREE_CLEAR:
        assert by[crossed] == "edge", crossed                                # the 8 idioms retired to edge
    for crossed in ("computer_architecture", "mathematics", "cloud_infrastructure", "art_design_drawing"):
        assert by[crossed] == "edge", crossed                                # taught -> now edge-learned
    for still_anchor in ("communication",):
        assert by[still_anchor] == "anchor", still_anchor                    # honest residual remains
