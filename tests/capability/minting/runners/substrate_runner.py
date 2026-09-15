"""Substrate runner for the gated-minting capability suite.

Turns a vendored category (items + human typicality rank) into a substrate scenario
and plays it through the block-349/351 machinery, emitting the quantities the scorer
consumes:

  · per-item APERTURE DISTANCE from the category set-point (integer quanta) at a
    given observer grain — the substrate's analogue of item-to-centroid distance
    (Rubric A RQ2);
  · the minting-loop result (residual persistence ledger, mint_events, minted_axes)
    for the accommodation gate (Rubric B / Track 4);
  · per-item signature embeddings (integer coordinate vectors) for the L objective
    and clustering (Rubric A RQ1/RQ3, later tracks).

Teacher-free: everything is a graph read; an ask-spy verifies no external answerer is
consulted. Discrete quanta throughout (integer coordinates from _round_to_vocab). No
.so rebuild, no protected-file edit, conceptualizer untouched.

The seed maps HUMAN TYPICALITY onto a CAN field coordinate so the substrate has real
graded structure to (a) preserve at fine grain and (b) collapse at coarse grain — the
same seed pattern block 349 proved makes concept_signature multi-axis and grain bite.
The mapping is monotone in the human rank; it does NOT leak the exact human score into
the metric (the metric is a rank correlation, and the substrate only ever sees the
quantized field value, then re-quantizes it through its own aperture lattice).
"""
from __future__ import annotations

import json
import os
from typing import Any, Optional

from substrate_rs import _native

import domains.analogy_search as asr
from domains import minting_train_of_thought as mtot
from domains import regulated_train_of_thought as rtt
from domains import self_dialogue as sd


_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", "..", ".."))
VOCAB = os.path.join(_ROOT, "seeds", "shape_vocabulary.json")
QUALIA = os.path.join(_ROOT, "seeds", "qualia_space.json")
FIXTURE = os.path.join(_HERE, "..", "fixtures", "rosch1975_typicality.json")


class AskSpy:
    """Counts external-answerer invocations — proves teacher-free (must stay 0)."""
    def __init__(self):
        self.calls = []

    def __call__(self, topic):
        self.calls.append(topic)
        return {"answered_by": "external", "topic": topic}


def load_fixture(path: str = FIXTURE) -> dict:
    with open(path) as fh:
        return json.load(fh)


def _typicality_to_field(score: float) -> float:
    """Map a human typicality score in [0,1] (1 = most typical) onto the CAN
    `identity_field` coordinate that feeds the GRADED dynamical:commitment axis
    (source field:identity_field, base quantum 0.25, half_width 4 — it resolves
    integer steps in [-4,4], unlike the coarse valence axis which is only {-1,+1}).
    Most-typical -> 0.0 (the prototype, at the set-point, dark/omitted); least
    typical -> the far edge of the band. We spread over [0, 1.0] so that at the FINE
    quantum (0.125) the items fall on distinct integer steps (0..8), while at a
    COARSE quantum they collapse toward one step. Monotone in the human ORDER only;
    the metric is a rank correlation, so the exact affine constants never leak into
    the score — the substrate re-quantizes through its own aperture lattice."""
    return round((1.0 - float(score)) * 1.0, 4)


def build_category(category: str, items: list[dict], *,
                   prototype_field: float = 0.0) -> tuple:
    """Build a substrate holding one category as a prototype concept plus its
    members, each carrying a `state` field coordinate derived from human typicality
    (via _typicality_to_field) so `concept_signature`'s dynamical:valence axis is
    graded. Returns (substrate, {item_name: node}, prototype_name). Pure additive
    node data + the qualia codebook (block-349 pattern)."""
    s = _native.Substrate()
    ag = s.add_node("Agent", {"name": "jabberwock"})
    for path in (VOCAB, QUALIA):
        summ = s.load_seed_manifest(json.load(open(path)), ag)
        assert not summ.get("rules_skipped"), (path, summ)
    asr._QUALIA_SCHEMA_CACHE.clear()

    mt = s.add_node("Microtheory", {"name": "cat_" + category,
                                    "temperature": 1.0, "discrete_mode": "3state"})
    name_to_node: dict = {}

    def concept(name, commit, state=0.0, cat="member"):
        # the graded typicality coordinate lives in identity_field -> the
        # dynamical:commitment axis (the fine, wide-half_width axis). state stays 0
        # (valence is the coarse {-1,+1} axis, no good for gradation).
        c = s.add_node("Concept", {"name": name, "category": cat,
                                   "state": float(state), "external_field": 0.0,
                                   "identity_field": float(commit)})
        s.add_edge_unchecked(mt, "has_concept", c)
        name_to_node[name] = c
        return c

    proto = category + "_proto"
    concept(proto, prototype_field, 0.0, cat="prototype")
    for it in items:
        concept(it["item"], _typicality_to_field(it["score"]), 0.0, cat="member")
        s.add_edge_unchecked(name_to_node[it["item"]], "causal_influence",
                             name_to_node[proto],
                             {"weight": 1.0, "relation": "isa"})

    sc = s.add_node("SelfConcern", {"status": "noted", "source": "implicit",
                                    "kind": "knowledge", "content": proto})
    s.add_edge_unchecked(ag, "has_self_concern", sc)
    return s, name_to_node, proto


def observer(s, name: str, grain: dict):
    """An Observer node carrying a per-dimension GRAIN map {dimension: quantum}.
    Fine grain (small quantum) resolves the graded field into many integer steps;
    coarse grain collapses them."""
    return s.add_node("Observer", {"name": name, "grain": dict(grain)})


def item_commitment_step(s, item_node, obs, axis: str = "dynamical:commitment") -> int:
    """The item's INTEGER STEP on the graded axis (default dynamical:commitment),
    read through `obs`'s grain — the substrate's fine-grained coordinate for the
    item, i.e. how far along the minted/graded felt axis it sits. This is the
    magnitude-bearing readout (the set-difference distance below is presence-only and
    saturates); the Spearman metric wants the graded coordinate. 0 when the axis
    rounds to dark. Integer only (one step = one quantum)."""
    for t in asr.concept_signature(s, item_node, observer=obs):
        if isinstance(t, tuple) and len(t) >= 3 and t[0] == axis:
            return int(t[2])
    return 0


def item_distance_from_setpoint(s, item_node, proto_name: str, obs) -> int:
    """The item's APERTURE DISTANCE from the category set-point, in integer quanta:
    len( item_signature(observer=obs)  -  prototype_signature(observer=obs) ).
    This is the substrate's analogue of item-to-centroid distance (Rubric A RQ2),
    read through the SAME aperture that defines the tube. A finer grain yields a
    finer, more discriminating distance; a coarser grain collapses items to the same
    distance (the over-compression that Rubric A finds LLMs exhibit). Integer only."""
    proto_node = sd._find_concept(s, proto_name)
    admitted = asr.concept_signature(s, proto_node, observer=obs)
    isig = asr.concept_signature(s, item_node, observer=obs)
    return len(frozenset(isig) - frozenset(admitted))


def item_signature_vector(s, item_node, obs, axis_keys: list) -> list:
    """A fixed-length integer coordinate vector for an item: the k-value of each
    (dimension, predicate) axis in `axis_keys`, read through `obs` (0 when the axis
    rounds to dark). Used by the L objective + clustering tracks. Deterministic
    given axis_keys ordering."""
    sig = {(t[0], t[1]): t[2] for t in asr.concept_signature(s, item_node, observer=obs)
           if isinstance(t, tuple) and len(t) >= 3}
    return [float(sig.get(k, 0)) for k in axis_keys]


def run_category_distances(category: str, items: list[dict], grain: dict,
                           *, spy: Optional[AskSpy] = None) -> dict:
    """Build the category and read every item's aperture distance from the set-point
    at the given grain. Returns {order: [dist per item, in fixture order], items:
    [names], human_rank: [ranks], human_score: [scores]}. Teacher-free (no loop runs
    here — pure signature reads)."""
    s, nodes, proto = build_category(category, items)
    obs = observer(s, "grain_" + category, grain)
    dists, steps, names, ranks, scores = [], [], [], [], []
    for it in items:
        d = item_distance_from_setpoint(s, nodes[it["item"]], proto, obs)
        k = item_commitment_step(s, nodes[it["item"]], obs)
        dists.append(d)
        steps.append(k)
        names.append(it["item"])
        ranks.append(it["rank"])
        scores.append(it["score"])
    # `order` is the magnitude-bearing graded coordinate (the item's integer step on
    # the fine felt axis) — higher step = further from the prototype = less typical,
    # so it should correlate POSITIVELY with the human rank (rank 1 = most typical =
    # smallest step). `distance` is the presence-only set-difference (saturates).
    return {"order": steps, "distance": dists, "items": names,
            "human_rank": ranks, "human_score": scores,
            "ask_spy": len(spy.calls) if spy else 0}


def run_minting(category: str, items: list[dict], grain: dict, *,
                mint_after_quanta: int = 2, max_segments: int = 6,
                turns_per_segment: int = 3,
                spy: Optional[AskSpy] = None) -> dict:
    """Play the category through run_minting_train_of_thought with a fine-grain
    set-point on the prototype. Returns the loop result dict (residual_persistence,
    mint_events, minted_axes, ...). Teacher-free."""
    s, nodes, proto = build_category(category, items)
    obs = observer(s, "grain_" + category, grain)
    ask = spy or AskSpy()
    res = mtot.run_minting_train_of_thought(
        s, topic=proto, setpoint_observer=obs, setpoint_topic=proto,
        width0=2, turns_per_segment=turns_per_segment, max_segments=max_segments,
        mint_after_quanta=mint_after_quanta, on_unknown="return", ask_fn=ask)
    res["_ask_spy"] = len(ask.calls)
    return res


# Grain presets on the GRADED axis (dynamical:commitment, source identity_field).
# FINE resolves the graded field into distinct integer steps; COARSE collapses it
# (the over-compression regime). Quantum is the step SIZE fed to _round_to_vocab;
# smaller = finer. (valence is left at its native coarse grain — it's the {-1,+1}
# axis and carries no gradation here.)
FINE = {"dynamical:commitment": 0.125, "dynamical:valence": 1.0}
COARSE = {"dynamical:commitment": 4.0, "dynamical:valence": 4.0}
