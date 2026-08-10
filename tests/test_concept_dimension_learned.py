"""test_concept_dimension_learned — LEARN A CONCEPT'S DIMENSION FROM ITS EDGES (concept_graph.py +
the audience_adaptation / sense_of_reference rewire). DISCRIMINATIVE, donkey=0.

The mechanism: a concept's position in the frame geometry is a LOG-NUMBER read off its EDGES, via an
N-STEP RECURSIVE COARSE-TO-FINE DESCENT (dynamic-quantization recursed). Rung 1 = the coarse WORLD
region (the exponent); the recursion's tail = the fine within-region log-position (the mantissa);
depth is dynamic per concept (foveated). FOREIGNNESS / LIVENESS = DEPTH OF CO-DESCENT: how deep a
concept's path runs together with the interlocutor's frame before it forks — learned from edges,
RELATIVE to the frame, not an absolute modern-tech cue table.

HONEST connectivity is MEASURED here, not assumed (the hard honesty guard): the has_concept
neighbourhood edge-learns most concepts; the zero-edge ones (computer_architecture, compilers,
mathematics) + one generic tie (communication) fall to a small labelled seed anchor, reported.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import inspect

import pytest

from domains import concept_graph as cg
from domains import audience_adaptation as aa
from domains import sense_of_reference as sr

VANE = ["ethics", "virtue", "philosophy", "morality", "propriety", "courtesy"]
DEV = ["python", "rust", "algorithm", "compiler", "server", "database"]
AREAS = ["engineering", "video_coding_theory", "computer_architecture", "communication",
         "mathematics", "databases_and_storage", "embedded_iot_realtime",
         "security_and_cryptography", "art_design_drawing", "cloud_infrastructure",
         "machine_learning", "philosophy"]
VANE_FOREIGN = {"video_coding_theory", "computer_architecture", "databases_and_storage",
                "embedded_iot_realtime", "security_and_cryptography", "cloud_infrastructure",
                "machine_learning"}


@pytest.fixture(scope="module")
def agent():
    pytest.importorskip("substrate_rs")
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


# =========================================================================== #
#  1. TWO-STEP / N-STEP — a concept resolves to a recursive (dimension, ...) PATH
#     with a fine within-region MANTISSA, all from edges.
# =========================================================================== #

def test_recursive_descent_path_from_edges(agent):
    """A concept descends coarse->fine into a PATH read from its has_concept edges: rung 1 = the
    world region, rung 2 = the nearest region-anchor microtheory, rung 3 = its home microtheory. A
    concept-BEARING modern domain resolves several rungs; a zero-edge one stops early (foveated)."""
    ml = cg.descend(agent, "machine_learning")
    assert ml["path"][0] == cg.REGION_MODERN            # rung 1: exponent = the coarse dimension
    assert ml["depth"] >= 3                             # edges resolve it deep (neural_networks, ...)
    assert "neural_networks" in ml["path"]              # co-descends with the ML sub-region
    # a zero-edge concept stops early — depth is DYNAMIC / foveated, not a fixed 2.
    ca = cg.descend(agent, "compilers")
    assert cg.bag_size(agent, "compilers") <= 2          # the graph never grounded compilers (no microtheory)
    assert ca["depth"] < ml["depth"]


def test_mantissa_central_higher_than_peripheral(agent):
    """The MANTISSA (rung tail = fine within-region log-position) ranks a CENTRAL concept above a
    PERIPHERAL one in the SAME dimension: ethics sits central in `universal` (close to the philosophy
    anchor), gastronomy sits peripheral — both universal, but ethics carries the higher mantissa."""
    central = cg.descend(agent, "ethics")["mantissa"][cg.REGION_UNIVERSAL]
    peripheral = cg.descend(agent, "gastronomy")["mantissa"][cg.REGION_UNIVERSAL]
    assert cg.world_dimension(agent, "ethics")[0] == cg.REGION_UNIVERSAL
    assert cg.world_dimension(agent, "gastronomy")[0] == cg.REGION_UNIVERSAL
    assert central > peripheral                          # central concept: higher fine log-position


def test_shared_path_depth_is_the_closeness(agent):
    """Depth of CO-DESCENT is the closeness measure: two modern-tech concepts share several rungs
    before forking (deep); a modern-tech concept and one of Vane's ethics concepts fork at rung 1
    (depth 0). ml/cloud (both modern) co-descend deeper than ml/ethics (cross-region)."""
    same_region = cg.shared_depth(agent, "machine_learning", ["cloud_infrastructure"])
    cross_region = cg.shared_depth(agent, "machine_learning", ["ethics"])
    assert same_region >= 1                              # share at least the modern region
    assert cross_region == 0                             # fork at rung 1 -> maximally foreign


# =========================================================================== #
#  2. RELATIVE FOREIGNNESS (headline) — foreign iff the concept's dimension is
#     graph-distant from the INTERLOCUTOR'S FRAME dimensions (learned, not a table).
# =========================================================================== #

def test_frame_dimensions_are_edge_derived(agent):
    """The interlocutor's frame = the dimensions THEIR OWN concepts occupy (edge-placed), not a hand
    table. Vane's ethics/virtue concepts all place in `universal` -> frame = {universal}; a developer's
    python/rust/compiler concepts pull in `modern_tech` too."""
    assert cg.frame_dimensions(agent, VANE) == {cg.REGION_UNIVERSAL}
    assert cg.REGION_MODERN in cg.frame_dimensions(agent, DEV)


def test_relative_foreignness_vane_vs_technical(agent):
    """The SAME concept, opposite call, decided by the FRAME (relative, not absolute): a modern-tech
    concept is FOREIGN to Vane's universal frame (forks at rung 1) but LIVE for a technical frame
    (co-descends). This is the edge-learned form of the audience-adaptation headline."""
    for modern in ("machine_learning", "cloud_infrastructure", "video_coding_theory"):
        assert cg.is_foreign_to_frame(agent, modern, VANE) is True
        assert cg.is_foreign_to_frame(agent, modern, DEV) is False


def test_reproduces_the_exact_vane_partition_from_edges(agent):
    """The full AREAS partition Vane sees is reproduced by the edge-learned dimension (the exact set
    the old cue table produced) — modern-tech domains foreign, period/universal domains live."""
    for c in AREAS:
        foreign = cg.is_foreign_to_frame(agent, c, VANE)
        assert foreign == (c in VANE_FOREIGN), (c, foreign)


def test_generalizes_to_a_novel_concept_the_cue_table_never_listed(agent):
    """GENERALIZATION: a concept the retired 60-token cue table never listed is placed CORRECTLY by
    its edges alone. `computer_vision` (a real concept-bearing tech microtheory, absent from the old
    table) edge-places modern -> foreign to Vane, live for a developer; `rhetoric` places universal."""
    region, source = cg.world_dimension(agent, "computer_vision")
    assert region == cg.REGION_MODERN and source == "edge"     # learned from edges, not the anchor
    assert cg.is_foreign_to_frame(agent, "computer_vision", VANE) is True
    assert cg.is_foreign_to_frame(agent, "computer_vision", DEV) is False
    assert cg.world_dimension(agent, "rhetoric")[0] == cg.REGION_UNIVERSAL


def test_adapt_concepts_still_reproduces_the_headline(agent):
    """End-to-end through audience_adaptation (now edge-backed): Vane's modern-tech domains are
    abstracted, universal ones land — the live faculty is edge-learned."""
    r = aa.adapt_concepts(agent, AREAS, {"id": "Cornelius Vane", "observed": True,
                                         "known_concepts": VANE, "register": "formal",
                                         "formal_cues": 2.0})
    assert r["adapted_flag"] is True
    for f in ("machine_learning", "cloud_infrastructure", "video_coding_theory"):
        assert f in r["foreign"] and f not in r["adapted"]
    for live in ("mathematics", "philosophy", "engineering"):
        assert live in r["adapted"]


# =========================================================================== #
#  3. REFERENCE-LIVENESS relative + learned (coarse axis) — via the same edges.
# =========================================================================== #

def test_reference_liveness_via_edges_graduated_and_modern(agent):
    """Reference liveness expressed as the edge-learned coarse dimension co-descent: a UNIVERSAL /
    graduated referent (`down the rabbit hole` -> `rabbit_hole`) is live for EVERY frame (close to
    all); a modern-tech referent is live for a technical frame but a plain speech pattern (foreign) for
    Vane's period frame — the minimal-pair shape, learned from edges."""
    for frame in (VANE, DEV, []):
        assert sr.liveness_via_edges(agent, "rabbit_hole", frame)["live"] is True
    ml_vane = sr.liveness_via_edges(agent, "machine_learning", VANE)
    ml_dev = sr.liveness_via_edges(agent, "machine_learning", DEV)
    assert ml_vane["live"] is False and ml_vane["dimension"] == cg.REGION_MODERN   # speech pattern
    assert ml_dev["live"] is True                                                  # live allusion


# =========================================================================== #
#  4. CONNECTIVITY SUFFICIENCY — measured explicitly (the hard honesty guard).
# =========================================================================== #

def test_connectivity_report_measures_edge_vs_anchor(agent):
    """The report states WHERE edges sustain learning vs where they fall to the anchor. The
    concept-BEARING domains are edge-placed. Since the tech-microtheory build
    (seeds/computer_architecture_microtheory.json + mathematics_ + cloud_ + art_) the once-anchored
    computer_architecture / mathematics / cloud / art now edge-learn too; the genuinely-anchored
    residual is `communication` (genuinely DIFFUSE — a timeless human sense AND a technical networking
    sense — so its edges split and clarity stays < 2/3). `compilers` (a zero-edge domain still absent
    a taught microtheory) also stays anchored. The majority is edge-learned."""
    rep = cg.connectivity_report(agent, AREAS)
    assert rep["edge_fraction"] >= 0.5                   # most of AREAS is genuinely edge-learned
    by = {r["concept"]: r["source"] for r in rep["rows"]}
    assert by["machine_learning"] == "edge" and by["video_coding_theory"] == "edge"
    assert by["computer_architecture"] == "edge"         # now taught + edge-learned (was anchor)
    # the honestly-reported shortfall: `communication` stays anchored (genuinely diffuse, clarity < 2/3).
    assert by["communication"] == "anchor"
    assert cg.bag_size(agent, "compilers") <= 2 and cg.world_dimension(agent, "compilers")[1] == "anchor"


# =========================================================================== #
#  5. CUE TABLE RETIRED / DEMOTED — no 60-token modern-tech table survives.
# =========================================================================== #

def test_modern_tech_cue_table_retired():
    """`_MODERN_TECH_CUES` (the 60-token table) is GONE from audience_adaptation; the world dimension
    is edge-learned via concept_graph. The only surviving token list is the small labelled seed anchor
    in concept_graph, honestly demoted (used for zero-edge / agent-less callers)."""
    assert not hasattr(aa, "_MODERN_TECH_CUES")
    # the demoted anchor is small and labelled (a fraction of the retired 60-token table).
    assert len(cg._SEED_ANCHOR_MODERN) < 45
    # audience_adaptation carries no bespoke ML classifier.
    src = inspect.getsource(aa)
    for bad in (".fit(", ".backward(", "import numpy", "import torch", "sklearn"):
        assert bad not in src


def test_type_cues_demoted_and_documented():
    """`_TYPE_CUES` survives ONLY as the agent-less niche world-type anchor (the reference decode path
    carries a manifold dict, not a substrate) and is documented as the demoted residual; the
    edge-learned path is `liveness_via_edges`."""
    assert hasattr(sr, "liveness_via_edges")             # the edge-learned reference liveness exists
    src = inspect.getsource(sr)
    assert "DEMOTED" in src and "edge-learned" in src.lower()
