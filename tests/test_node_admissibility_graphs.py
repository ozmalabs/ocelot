"""Locks for iter-49 node-admissibility-graphs: each node's weight is PER candidate word
(its admissibility sub-graph), set as a per-word graph attr; the per-node gate is a CONVEX
BLEND toward the node's flat reference (NOT a per-word exponent — that would inflate the
inadmissible word); a node inadmissible on a contrast (weight->0) contributes the
word-neutral flat value (abstains, drops out of the Argmax) while saying full on the
contrasts it is admissible for; all-1 weights recover iter-45's equal product; the
per-contrast precision map is the fixed no-parameter map; no-fit/no-donkey source audit."""
import ast
import math
import os

import numpy as np
import pytest

import domains.node_admissibility_graphs as NA
import domains.many_settings_recognizer as MS
from substrate_rs import Substrate


def test_per_contrast_weight_is_the_fixed_precision_map():
    """weight_i(w) = max(0,(precision-chance)/(1-chance)) — same fixed map, per-word."""
    chance = 0.1
    assert NA.per_contrast_weight(chance, chance) == 0.0           # at chance -> abstain
    assert math.isclose(NA.per_contrast_weight(1.0, chance), 1.0)  # perfect -> full say
    assert NA.per_contrast_weight(0.0, chance) == 0.0              # never right -> 0
    mid = NA.per_contrast_weight(0.55, chance)
    assert math.isclose(mid, (0.55 - 0.1) / 0.9, rel_tol=1e-9)


def test_gate_is_convex_blend_toward_flat():
    """gated_i(w) = weight*P + (1-weight)*u. weight=1 -> P; weight=0 -> u (the flat
    reference); mid -> the blend. A graph Term (Plus of Times), evaluated by the substrate.
    NO exponent: the abstain value is the word-neutral u, not P^0=1."""
    s = Substrate()
    c = s.add_node("Concept", {"name": "x"}); s.set_attr(c, MS.WORD_ATTR, 1.0)
    s.set_attr(c, MS.channel_attr(0), 0.8)
    s.set_attr(c, NA.flat_attr(0), 0.25)
    term = MS._Pred(NA.gated_score_term(1))
    # admissible -> P
    s.set_attr(c, NA.weight_attr(0), 1.0)
    assert math.isclose(s.evaluate(term, {"w": c}), 0.8, rel_tol=1e-9)
    # inadmissible -> flat u (word-neutral), NOT 1.0 (would be P^0)
    s.set_attr(c, NA.weight_attr(0), 0.0)
    assert math.isclose(s.evaluate(term, {"w": c}), 0.25, rel_tol=1e-9)
    # mid -> the convex blend
    s.set_attr(c, NA.weight_attr(0), 0.5)
    assert math.isclose(s.evaluate(term, {"w": c}), 0.5 * 0.8 + 0.5 * 0.25, rel_tol=1e-9)


def test_inadmissible_node_abstains_not_inflates():
    """A node confidently-peaked at the WRONG word but inadmissible there contributes the
    SAME flat value to every candidate (drops out of the Argmax) — it does NOT inflate the
    wrong word (the per-exponent bug). Admissible nodes then decide the contrast."""
    cands = ["bee", "dee"]
    flat = 1.0 / len(cands)
    s = Substrate()
    wc = {}
    for w in cands:
        n = s.add_node("Concept", {"name": w}); s.set_attr(n, MS.WORD_ATTR, 1.0)
        wc[w] = n
    # node 0: confidently (wrongly) peaks "bee" but is INADMISSIBLE for both -> abstains.
    s.set_attr(wc["bee"], MS.channel_attr(0), 0.99); s.set_attr(wc["bee"], NA.weight_attr(0), 0.0)
    s.set_attr(wc["dee"], MS.channel_attr(0), 0.01); s.set_attr(wc["dee"], NA.weight_attr(0), 0.0)
    # node 1: admissible, correctly favours "dee".
    s.set_attr(wc["bee"], MS.channel_attr(1), 0.3); s.set_attr(wc["bee"], NA.weight_attr(1), 1.0)
    s.set_attr(wc["dee"], MS.channel_attr(1), 0.7); s.set_attr(wc["dee"], NA.weight_attr(1), 1.0)
    for w in cands:
        for i in range(2):
            s.set_attr(wc[w], NA.flat_attr(i), flat)
    term = MS._Pred(NA.predict_weighted_term(2))
    pick = s.node(s.evaluate(term, {}))["attrs"]["name"]
    assert pick == "dee"  # the abstaining wrong node did NOT inflate "bee"


def test_all_admissible_recovers_equal_product():
    """All per-word weights == 1 -> the per-contrast Argmax picks the SAME word as the
    EQUAL combine-all (iter-45) — the fully-admissible special case."""
    cands = ["a", "b", "c"]
    n = 4
    rng = np.random.RandomState(0)
    s_eq = Substrate(); s_pc = Substrate()
    wc_eq = {}; wc_pc = {}
    for w in cands:
        e = s_eq.add_node("Concept", {"name": w}); s_eq.set_attr(e, MS.WORD_ATTR, 1.0)
        p = s_pc.add_node("Concept", {"name": w}); s_pc.set_attr(p, MS.WORD_ATTR, 1.0)
        wc_eq[w] = e; wc_pc[w] = p
    for ci in range(n):
        liks = rng.dirichlet(np.ones(len(cands)))
        for w, prob in zip(cands, liks):
            s_eq.set_attr(wc_eq[w], MS.channel_attr(ci), float(prob))
            s_pc.set_attr(wc_pc[w], MS.channel_attr(ci), float(prob))
            s_pc.set_attr(wc_pc[w], NA.weight_attr(ci), 1.0)   # all admissible -> blend = P
            s_pc.set_attr(wc_pc[w], NA.flat_attr(ci), 1.0 / len(cands))
    eq_term = MS._Pred(MS.predict_many_settings_term(n))
    pc_term = MS._Pred(NA.predict_weighted_term(n))
    eq_pick = s_eq.node(s_eq.evaluate(eq_term, {}))["attrs"]["name"]
    pc_pick = s_pc.node(s_pc.evaluate(pc_term, {}))["attrs"]["name"]
    assert eq_pick == pc_pick


def test_no_fit_no_donkey_source_audit():
    """The module source (docstrings stripped) contains no fit/gradient/net/sweep."""
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "domains", "node_admissibility_graphs.py")
    with open(path) as f:
        tree = ast.parse(f.read())
    for node in ast.walk(tree):
        if (isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef,
                              ast.Module)) and ast.get_docstring(node)):
            node.body = node.body[1:] if (node.body and isinstance(node.body[0], ast.Expr)
                                          and isinstance(node.body[0].value, ast.Constant)
                                          and isinstance(node.body[0].value.value, str)) \
                else node.body
    src = ast.unparse(tree).lower()
    for forbidden in ("fit(", "backward", "gradient", "optimizer", "nn.", "torch",
                      "sklearn", ".train(", "loss", ".predict(", "classifier"):
        assert forbidden not in src, f"forbidden token in source: {forbidden}"


if __name__ == "__main__":
    pytest.main([__file__, "-q"])
