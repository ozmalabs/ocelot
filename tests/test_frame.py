"""test_frame — THE FRAME PRIMITIVE (domains/frame.py), the creator's founding ontology made
explicit (2026-07-04): a FRAME is a SET OF DIMENSIONS with RELATIVE LOG-SCALED WEIGHTING, graph-
resident as a Frame node + log-weighted Dimension edges. DISCRIMINATIVE, donkey=0.

The ops are GRAPH QUERIES (membership + weight), never classifiers:
  * build a frame, query in_frame / dimension_weight / frame_dims;
  * weights are LOG-scaled + RELATIVE — equal dims -> equal weights; a dominant dim -> +k log-steps;
    a dim NOT in the frame -> -inf (absent);
  * relative_weight(a, b) = log_weight(a) - log_weight(b) = log(a/b), frame-independent.
"""
from __future__ import annotations

import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pytest

from domains import frame as fr


@pytest.fixture(scope="module")
def agent():
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


# --------------------------------------------------------------------------- #
#  GRAPH FORM — a Frame node with in_dim edges to Dimension nodes.
# --------------------------------------------------------------------------- #

def test_frame_is_graph_resident_node_plus_dimension_edges(agent):
    f = fr.build_frame(agent, ["ethics", "philosophy", "period"], "t_graph")
    assert agent.s.node(f)["type"] == "Frame"
    # one in_dim edge per dimension, each to a Dimension node.
    dim_nodes = list(agent.s.neighbours(f, "in_dim"))
    names = {agent.s.node(n)["attrs"].get("name") for n in dim_nodes}
    assert names == {"ethics", "philosophy", "period"}
    for n in dim_nodes:
        assert agent.s.node(n)["type"] == "Dimension"


# --------------------------------------------------------------------------- #
#  MEMBERSHIP + WEIGHT — the queries that replace the cue-table decision.
# --------------------------------------------------------------------------- #

def test_in_frame_and_dimension_weight(agent):
    f = fr.build_frame(agent, ["ethics", "philosophy"], "t_member")
    assert fr.in_frame(f, "ethics", agent) is True
    assert fr.in_frame(f, "machine_learning", agent) is False       # absent -> not a member
    assert fr.dimension_weight(f, "ethics", agent=agent) == 0.0
    assert fr.dimension_weight(f, "machine_learning", agent=agent) == float("-inf")
    assert fr.frame_dims(f, agent) == ["ethics", "philosophy"]


def test_equal_dims_have_equal_log_weights(agent):
    """A frame with no dominant axis: all dims at equal (0.0) log-weight."""
    f = fr.build_frame(agent, ["a", "b", "c"], "t_equal")
    ws = [fr.dimension_weight(f, d, agent=agent) for d in ("a", "b", "c")]
    assert ws == [0.0, 0.0, 0.0]
    assert fr.relative_weight(f, "a", "b", agent=agent) == 0.0      # log(1/1) = 0


def test_dominant_dim_is_plus_k_log_steps(agent):
    """A dominant dimension (weight e^k times the others) sits +k log-steps above them."""
    f = fr.build_frame(agent, {"a": 1.0, "b": 1.0, "dom": math.e ** 2}, "t_dom")
    assert fr.dimension_weight(f, "dom", agent=agent) == pytest.approx(2.0)
    assert fr.dimension_weight(f, "a", agent=agent) == 0.0
    assert fr.relative_weight(f, "dom", "a", agent=agent) == pytest.approx(2.0)   # +k above


def test_min_weight_threshold(agent):
    """in_frame with a relative-weight floor: a dim below the threshold is treated as out."""
    f = fr.build_frame(agent, {"weak": 1.0, "strong": math.e ** 3}, "t_thresh")
    assert fr.in_frame(f, "weak", agent) is True                    # present
    assert fr.in_frame(f, "weak", agent, min_weight=1.0) is False   # but below the floor
    assert fr.in_frame(f, "strong", agent, min_weight=1.0) is True


def test_refresh_by_key_is_idempotent(agent):
    """Rebuilding under the same key refreshes the SAME frame node in place (a live view, not an
    accumulation) — the dimensions are replaced, not appended."""
    f1 = fr.build_frame(agent, ["a", "b"], "t_refresh")
    f2 = fr.build_frame(agent, ["c"], "t_refresh")
    assert f1 == f2                                                 # same node
    assert fr.frame_dims(f2, agent) == ["c"]                        # dims replaced
    assert fr.in_frame(f2, "a", agent) is False


# --------------------------------------------------------------------------- #
#  VALUE FORM — the frame's {dim: log_weight} twin (agent-less callers).
# --------------------------------------------------------------------------- #

def test_value_form_frame_same_semantics():
    """A plain {dim: log_weight} dict is a frame too (the value twin the agent-less reference faculty
    uses) — identical relative-log-weight semantics, no substrate needed."""
    vf = {"gamer": math.log(8.0), "universal": 0.0}
    assert fr.in_frame(vf, "gamer") is True
    assert fr.in_frame(vf, "formal") is False
    assert fr.dimension_weight(vf, "formal") == float("-inf")
    assert fr.relative_weight(vf, "gamer", "universal") == pytest.approx(math.log(8.0))


def test_pin_log_scaled_relative_weight(agent):
    """Pin: weights are LOG-scaled + RELATIVE. A frame built from linear weights {1, 2, 4} stores
    logs {0, log2, log4}; the relative weighting between any two is their log-ratio, frame-independent
    (adding a constant multiplier to all inputs leaves every relative_weight unchanged)."""
    f = fr.build_frame(agent, {"x": 1.0, "y": 2.0, "z": 4.0}, "t_pin")
    assert fr.dimension_weight(f, "y", agent=agent) == pytest.approx(math.log(2.0))
    assert fr.relative_weight(f, "z", "x", agent=agent) == pytest.approx(math.log(4.0))
    # scale ALL linear weights by 10 -> every relative weighting is identical (relative, not absolute).
    g = fr.build_frame(agent, {"x": 10.0, "y": 20.0, "z": 40.0}, "t_pin2")
    assert fr.relative_weight(g, "z", "x", agent=agent) == pytest.approx(
        fr.relative_weight(f, "z", "x", agent=agent))
