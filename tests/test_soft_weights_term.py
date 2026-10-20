"""Python tests for the `SoftWeights` Term (P2.C1.4 and P2.C1.5).

Covers:
1. Weight distribution over a graph node source matches a NumPy softmax reference
   to within 1e-12 across multiple positive temperatures.
2. Hard-limit (`T <= 0`) behaviour: unique maximum receives 1.0, tied maxima split
   1/k equally.
3. Non-numeric and missing attributes are skipped rather than zeroed; empty or
   all-skipped sources return `default` (or `[]` when `default` is omitted).
4. Composition with `Argmax` and `Nth` selects the highest-weight element.
5. Soft-exclusion recipe (P2.C1.5): `SoftWeights(value = score - penalty * excluded)`
   keeps an excluded candidate at nonzero weight that decreases monotonically as
   `penalty` increases.
"""
from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("substrate_rs")
from substrate_rs import _native


def _substrate_with_candidates(rows: list[dict]):
    s = _native.Substrate()
    s.add_production({
        "src": {"type": "Hub", "var": "a"},
        "edge_type": "has_cand",
        "tgt": {"type": "Cand", "var": "b"},
        "where": None,
        "weight": {"type": "Lit", "value": 1.0},
        "provenance": "test_soft_weights_term",
    })
    hub = s.add_node("Hub", {})
    ids = []
    for attrs in rows:
        n = s.add_node("Cand", dict(attrs))
        s.add_edge(hub, "has_cand", n)
        ids.append(n)
    return s, hub, ids


def _soft_weights_term(temp_val: float, default=None) -> dict:
    term = {
        "type": "SoftWeights",
        "source": {
            "type": "Neighbours",
            "node": {"type": "Var", "name": "h"},
            "edge_type": "has_cand",
        },
        "var_name": "c",
        "value": {
            "type": "Attr",
            "node": {"type": "Var", "name": "c"},
            "key": "score",
        },
        "temperature": {"type": "Lit", "value": float(temp_val)},
    }
    if default is not None:
        term["default"] = default
    return term


@pytest.mark.parametrize("temperature", [0.1, 0.5, 1.0, 2.5, 10.0])
def test_soft_weights_matches_numpy_reference_to_1e12(temperature: float):
    scores = [1.25, -0.5, 3.75, 2.0, 3.75]
    s, hub, ids = _substrate_with_candidates([{"score": sc} for sc in scores])

    pairs = s.evaluate(_soft_weights_term(temperature), {"h": hub})
    assert isinstance(pairs, list)
    assert len(pairs) == len(scores)

    # Order follows source.snapshot() order; look up each returned node's score
    got_nodes = [p[0] for p in pairs]
    got_weights = np.array([p[1] for p in pairs], dtype=np.float64)
    ordered_scores = np.array([s.node(nid)["attrs"]["score"] for nid in got_nodes], dtype=np.float64)

    shifted = (ordered_scores - np.max(ordered_scores)) / temperature
    ref_weights = np.exp(shifted) / np.sum(np.exp(shifted))

    assert np.allclose(got_weights, ref_weights, atol=1e-12, rtol=0.0)
    assert abs(float(np.sum(got_weights)) - 1.0) <= 1e-12


def test_soft_weights_hard_limit_and_tie_splitting():
    s, hub, ids = _substrate_with_candidates([
        {"score": 2.0},
        {"score": 5.0},
        {"score": 5.0},
        {"score": -1.0},
    ])
    pairs = s.evaluate(_soft_weights_term(0.0), {"h": hub})
    by_id = {nid: w for nid, w in pairs}
    assert by_id[ids[0]] == 0.0
    assert abs(by_id[ids[1]] - 0.5) <= 1e-12
    assert abs(by_id[ids[2]] - 0.5) <= 1e-12
    assert by_id[ids[3]] == 0.0


def test_soft_weights_skips_non_numeric_and_uses_default_when_empty():
    s, hub, ids = _substrate_with_candidates([
        {"score": 1.0},
        {"score": "not_numeric"},
        {},
        {"score": 1.0},
    ])
    pairs = s.evaluate(_soft_weights_term(1.0), {"h": hub})
    assert len(pairs) == 2
    for _nid, w in pairs:
        assert abs(w - 0.5) <= 1e-12

    s_empty, hub_empty, _ = _substrate_with_candidates([{"score": "bad"}, {}])
    fallback = s_empty.evaluate(
        _soft_weights_term(1.0, default={"type": "Lit", "value": "no_numeric_candidates"}),
        {"h": hub_empty},
    )
    assert fallback == "no_numeric_candidates"


def test_soft_weights_composes_with_argmax_and_nth():
    s, hub, ids = _substrate_with_candidates([
        {"score": 1.0},
        {"score": 9.0},
        {"score": 4.0},
    ])
    selector = {
        "type": "Nth",
        "items": {
            "type": "Argmax",
            "source": _soft_weights_term(0.5),
            "var_name": "pair",
            "value": {
                "type": "Nth",
                "items": {"type": "Var", "name": "pair"},
                "index": 1,
            },
        },
        "index": 0,
    }
    winner = s.evaluate(selector, {"h": hub})
    assert winner == ids[1]


def test_soft_exclusion_recipe_retains_nonzero_weight_that_falls_with_penalty():
    """P2.C1.5: Soft exclusion composed as `SoftWeights(value = score - penalty * excluded)`.
    An excluded candidate keeps nonzero weight at finite penalty and its weight
    decreases strictly as `penalty` grows.
    """
    s, hub, ids = _substrate_with_candidates([
        {"score": 5.0, "excluded": 1.0},  # high raw score, marked excluded
        {"score": 3.0, "excluded": 0.0},  # unexcluded alternative
        {"score": 2.0, "excluded": 0.0},  # second unexcluded alternative
    ])
    excluded_id = ids[0]

    def weight_at_penalty(penalty: float) -> float:
        term = {
            "type": "SoftWeights",
            "source": {
                "type": "Neighbours",
                "node": {"type": "Var", "name": "h"},
                "edge_type": "has_cand",
            },
            "var_name": "c",
            "value": {
                "type": "Minus",
                "a": {"type": "Attr", "node": {"type": "Var", "name": "c"}, "key": "score"},
                "b": {
                    "type": "Times",
                    "items": [
                        {"type": "Lit", "value": float(penalty)},
                        {"type": "Attr", "node": {"type": "Var", "name": "c"}, "key": "excluded"},
                    ],
                },
            },
            "temperature": {"type": "Lit", "value": 1.0},
        }
        pairs = dict(s.evaluate(term, {"h": hub}))
        return float(pairs[excluded_id])

    w0 = weight_at_penalty(0.0)
    w2 = weight_at_penalty(2.0)
    w5 = weight_at_penalty(5.0)
    w10 = weight_at_penalty(10.0)

    assert w0 > w2 > w5 > w10 > 0.0
    # At penalty=0 the excluded candidate leads; by penalty=5 an unexcluded candidate leads
    assert w0 > 0.5
    assert w5 < 0.2
