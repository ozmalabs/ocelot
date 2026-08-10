"""test_tech_dimensions — the TECH-MICROTHEORY build makes the last five anchored domains EDGE-LEARNED
(2026-07-04). DISCRIMINATIVE, donkey=0 (true member concepts taught as graph data). Mirror of
test_taught_dimensions (the gaming/literary/period build) for the tech domains.

After the gaming/literary/period build the concept->dimension edge-learner (`concept_graph`) placed
26/31 domains by edges; the last five stayed ANCHORED because their has_concept edges were ZERO
(computer_architecture, mathematics) or DIFFUSE (cloud_infrastructure, art_design_drawing,
communication). `scripts/teach_tech_microtheories.py` teaches a true member-concept microtheory for
each (two levels where sensible) and registers the four crossable ones as labelled region anchors in
`concept_graph._REGION_ANCHORS`. This gate proves:

  1. the five tech microtheories EXIST as graph data + PERSIST (reboot re-loads them);
  2. the four crossable domains now EDGE-LEARN in their CORRECT world (computer_architecture /
     cloud_infrastructure -> modern_tech; mathematics / art_design_drawing -> universal), lifting the
     tech AREAS tier 7/12 -> 11/12; `communication` is measured honestly and STAYS anchored (split);
  3. the VANE PARTITION is preserved: mathematics / communication / art familiar (universal),
     computer_architecture / cloud foreign (modern) — the verbatim adapted answer is unchanged;
  4. the DISCRIMINATIVE CONTROL still holds (game_theory etc. stay anchored — the new anchors don't
     break it);
  5. cloud_infrastructure / art_design_drawing co-descend DEEPER (depth 3) via their sub-microtheories;
  6. no regression: the prior gaming/literary/period reference worlds stay edge in their world.
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pytest

from domains import concept_graph as cg
from domains import audience_adaptation as aa

VANE = ["ethics", "virtue", "philosophy", "morality", "propriety", "courtesy"]
DEV = ["python", "rust", "algorithm", "compiler", "server", "database"]
AREAS = ["engineering", "video_coding_theory", "computer_architecture", "communication",
         "mathematics", "databases_and_storage", "embedded_iot_realtime",
         "security_and_cryptography", "art_design_drawing", "cloud_infrastructure",
         "machine_learning", "philosophy"]

# The five domains this build taught, with their assigned CORRECT world (communication measured).
MODERN_CROSSED = ("computer_architecture", "cloud_infrastructure")
UNIVERSAL_CROSSED = ("mathematics", "art_design_drawing")
MEASURED_SPLIT = "communication"     # genuinely diffuse -> stays anchored, resolves universal


@pytest.fixture(scope="module")
def agent():
    pytest.importorskip("substrate_rs")
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


# =========================================================================== #
#  1. THE TECH MICROTHEORIES EXIST AS GRAPH DATA + PERSIST (reboot-proof).
# =========================================================================== #

def test_tech_microtheories_are_graph_data(agent):
    """The five tech microtheories + their sub-worlds are Microtheory nodes with has_concept edges,
    read straight from the live graph after a seed boot."""
    mts = {agent.s.node(n)["attrs"].get("name") for n in agent.s.nodes("Microtheory")}
    for expected in ("computer_architecture", "microarchitecture", "mathematics", "geometry",
                     "cloud_infrastructure", "container_orchestration", "art_design_drawing",
                     "classical_drawing", "communication"):
        assert expected in mts, expected
    # the single-node domains carry rich descendable bags; the concept edges exist for all.
    for anchor in ("cloud_infrastructure", "art_design_drawing", "communication"):
        assert cg.bag_size(agent, anchor) >= 8, anchor


def test_tech_seed_manifests_persist_on_disk(agent):
    """The teach persisted to seed manifests under seeds/ — a fresh boot (`load_all_seeds` globs
    seeds/*.json) re-installs them, so the knowledge survives reboot (reboot-proof)."""
    for sid, mt in (("computer_architecture_microtheory", "computer_architecture"),
                    ("microarchitecture_microtheory", "microarchitecture"),
                    ("mathematics_microtheory", "mathematics"),
                    ("geometry_microtheory", "geometry"),
                    ("cloud_infrastructure_anchor_microtheory", "cloud_infrastructure"),
                    ("container_orchestration_microtheory", "container_orchestration"),
                    ("art_design_drawing_anchor_microtheory", "art_design_drawing"),
                    ("classical_drawing_microtheory", "classical_drawing"),
                    ("communication_anchor_microtheory", "communication")):
        path = os.path.join(ROOT, "seeds", f"{sid}.json")
        assert os.path.exists(path), path
        d = json.load(open(path))
        assert d["microtheory"]["name"] == mt
        assert len(d["concepts"]) >= 8


# =========================================================================== #
#  2. THE FOUR CROSSABLE DOMAINS NOW EDGE-LEARN IN THEIR CORRECT WORLD;
#     communication stays anchored (measured honestly); coverage rises.
# =========================================================================== #

def test_crossable_domains_edge_learn_in_correct_world(agent):
    """computer_architecture / cloud_infrastructure -> modern_tech (edge); mathematics /
    art_design_drawing -> universal (edge). Each edge-learned in the CORRECT world by its assigned
    nature — modern computing foreign to Vane, timeless maths/drawing familiar to him."""
    for c in MODERN_CROSSED:
        assert cg.world_dimension(agent, c) == (cg.REGION_MODERN, "edge"), c
    for c in UNIVERSAL_CROSSED:
        assert cg.world_dimension(agent, c) == (cg.REGION_UNIVERSAL, "edge"), c


def test_communication_measured_stays_split(agent):
    """`communication` is genuinely DIFFUSE (a timeless human sense — language/message/rhetoric — AND a
    technical networking sense — protocol/packet/bandwidth). Measured honestly it does NOT cross: its
    edges split (clarity < 2/3), so it STAYS anchored and resolves `universal` via the anchor fallback
    (familiar to Vane). NOT forced across — reported, not registered as an anchor."""
    conf = cg.region_confidence(agent, MEASURED_SPLIT)
    assert conf["clarity"] < cg._CLARITY_FLOOR                    # genuinely split
    assert conf["edge"] is False                                 # so not edge-learned
    region, source = cg.world_dimension(agent, MEASURED_SPLIT)
    assert source == "anchor" and region == cg.REGION_UNIVERSAL  # universal via fallback (Vane-familiar)


def test_coverage_rises_to_near_complete(agent):
    """COVERAGE (headline): the tech AREAS tier rises 7/12 -> 11/12 (only communication stays anchored),
    and the combined tech+reference tier reaches ~97%."""
    areas = cg.connectivity_report(agent, AREAS)
    assert areas["edge"] == 11 and areas["n"] == 12
    REF = ["video_games", "bioshock", "portal", "glados", "game", "player",
           "literature", "carroll", "jabberwock", "rabbit_hole", "red_queen", "alice",
           "period_thought", "virtue", "rhetoric", "blacksmithing", "moral_philosophy",
           "propriety", "courtesy"]
    both = cg.connectivity_report(agent, AREAS + REF)
    assert both["edge_fraction"] >= 0.95                          # ~100% combined coverage


# =========================================================================== #
#  3. VANE PARTITION PRESERVED (the correctness guard) — verbatim answer.
# =========================================================================== #

def test_vane_partition_preserved(agent):
    """The Vane partition is unchanged: mathematics / communication / art_design_drawing FAMILIAR
    (universal, live), computer_architecture / cloud_infrastructure FOREIGN (modern). Frame stays
    {universal}."""
    assert cg.frame_dimensions(agent, VANE) == {cg.REGION_UNIVERSAL}
    for familiar in ("mathematics", "communication", "art_design_drawing"):
        assert cg.is_foreign_to_frame(agent, familiar, VANE) is False, familiar
    for foreign in ("computer_architecture", "cloud_infrastructure"):
        assert cg.is_foreign_to_frame(agent, foreign, VANE) is True, foreign


def test_vane_adapted_answer_verbatim(agent):
    """The adapted 'How are you organised?' content is verbatim unchanged from HEAD: the universal
    domains land, the modern-tech ones collapse to the umbrella — mathematics / communication / art
    familiar, computer_architecture / cloud in the umbrella."""
    r = aa.adapt_concepts(agent, AREAS, {"id": "Cornelius Vane", "observed": True,
                                         "known_concepts": VANE, "register": "formal",
                                         "formal_cues": 2.0})
    assert " ".join(r["adapted"]) == ("engineering communication mathematics art_design_drawing "
                                      "philosophy certain modern arts unfamiliar in your world")
    for foreign in ("computer_architecture", "cloud_infrastructure", "machine_learning"):
        assert foreign in r["foreign"] and foreign not in r["adapted"]


# =========================================================================== #
#  4. DISCRIMINATIVE CONTROL — the new anchors don't break the ambiguous ones.
# =========================================================================== #

def test_discriminative_control_still_holds(agent):
    """The new anchors do NOT accidentally cross a genuinely-ambiguous concept: `game_theory`,
    `moral_algorithm` (edges split, clarity < 2/3) and `compilers` (zero-edge, best == 0) all STAY
    anchored. Same low degree as the crossing domains, opposite verdict — decided by clarity."""
    for split in ("game_theory", "moral_algorithm"):
        conf = cg.region_confidence(agent, split)
        assert conf["clarity"] < cg._CLARITY_FLOOR, (split, conf["clarity"])
        assert conf["edge"] is False and cg.world_dimension(agent, split)[1] == "anchor", split
    zero = cg.region_confidence(agent, "compilers")
    assert zero["best"] == 0.0 and zero["edge"] is False


# =========================================================================== #
#  5. DEEPER N-DESCENT — a sub-microtheory gives another rung (depth 3).
# =========================================================================== #

def test_deeper_descent_via_sub_microtheory(agent):
    """A sub-microtheory adds a deeper rung: `container_orchestration` co-descends
    modern -> cloud_infrastructure -> container_orchestration (depth 3); `classical_drawing`
    co-descends universal -> art_design_drawing -> classical_drawing (depth 3). Two concepts in the
    same tech world co-descend deep before forking; across worlds they fork at rung 1 (depth 0)."""
    co = cg.descend(agent, "container_orchestration")
    assert co["depth"] >= 3 and co["path"] == [cg.REGION_MODERN, "cloud_infrastructure",
                                               "container_orchestration"]
    cd = cg.descend(agent, "classical_drawing")
    assert cd["depth"] >= 3 and cd["path"] == [cg.REGION_UNIVERSAL, "art_design_drawing",
                                               "classical_drawing"]
    # cross-world concepts fork at rung 1 (depth 0); same-world share the region (depth >= 1).
    assert cg.shared_depth(agent, "container_orchestration", ["classical_drawing"]) == 0
    assert cg.shared_depth(agent, "cloud_infrastructure", ["container_orchestration"]) >= 1


# =========================================================================== #
#  6. NO REGRESSION — the prior reference worlds keep their world + edge source.
# =========================================================================== #

def test_no_regression_prior_reference_worlds(agent):
    """The gaming/literary/period reference worlds are undisturbed: bioshock / video_games modern,
    carroll / virtue / rhetoric / literature universal, all still edge-learned; the strong tech domains
    (machine_learning, neural_networks, computer_vision) still modern."""
    for c in ("bioshock", "video_games", "machine_learning", "neural_networks", "computer_vision"):
        assert cg.world_dimension(agent, c) == (cg.REGION_MODERN, "edge"), c
    for c in ("carroll", "virtue", "rhetoric", "literature", "period_thought", "philosophy"):
        assert cg.world_dimension(agent, c) == (cg.REGION_UNIVERSAL, "edge"), c
