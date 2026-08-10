"""Locks for iter-48 weighted-admissibility: the weighted product is a graph Term
(Argmax of Times-of-Pow) evaluated by the substrate; the weight is a MEASUREMENT-derived
attr (the fixed (acc-chance)/(1-chance) map), NOT a fit/sweep; equal weights recover the
equal combine-all; no-fit/no-donkey audit on the module source."""
import ast
import math
import os

import numpy as np
import pytest

import domains.weighted_admissibility as WA
import domains.many_settings_recognizer as MS
from substrate_rs import Substrate


def test_pow_term_evaluates_through_substrate():
    """P^weight is computed by the graph evaluator (Pow Term), not Python."""
    s = Substrate()
    c = s.add_node("Concept", {"name": "x"})
    s.set_attr(c, MS.channel_attr(0), 0.8)
    s.set_attr(c, WA.weight_attr(0), 2.0)
    term = MS._Pred(WA.weighted_score_term(1))  # = Times([Pow(p_ch0, w_ch0)])
    val = s.evaluate(term, {"w": c})
    assert math.isclose(val, 0.8 ** 2.0, rel_tol=1e-9)


def test_reliability_to_weight_is_the_fixed_map():
    """weight = max(0, (acc-chance)/(1-chance)); no free parameter."""
    chance = 0.1
    assert WA.reliability_to_weight(chance, chance) == 0.0          # at chance -> abstain
    assert math.isclose(WA.reliability_to_weight(1.0, chance), 1.0) # perfect -> full say
    assert WA.reliability_to_weight(0.05, chance) == 0.0            # below chance -> 0
    mid = WA.reliability_to_weight(0.55, chance)
    assert math.isclose(mid, (0.55 - 0.1) / 0.9, rel_tol=1e-9)


def test_weight_zero_makes_node_flat():
    """A weight-0 node contributes P^0 = 1 regardless of its (peaked-wrong) likelihood,
    so it cannot dilute the product (the abstain property)."""
    s = Substrate()
    c = s.add_node("Concept", {"name": "x"})
    s.set_attr(c, MS.channel_attr(0), 0.999)  # peaked
    s.set_attr(c, WA.weight_attr(0), 0.0)     # but abstaining
    term = MS._Pred(WA.weighted_score_term(1))
    val = s.evaluate(term, {"w": c})
    assert math.isclose(val, 1.0, rel_tol=1e-9)


def test_equal_weights_recover_equal_product():
    """With every weight == 1, the weighted Argmax picks the SAME word as the equal
    combine-all Argmax over the same likelihoods (the special case = iter-45)."""
    cands = ["a", "b", "c"]
    n = 4
    # equal-product substrate (many_settings) and weighted substrate, same likelihoods.
    rng = np.random.RandomState(0)
    s_eq = Substrate(); s_w = Substrate()
    wc_eq = {}; wc_w = {}
    for w in cands:
        e = s_eq.add_node("Concept", {"name": w}); s_eq.set_attr(e, MS.WORD_ATTR, 1.0)
        wv = s_w.add_node("Concept", {"name": w}); s_w.set_attr(wv, MS.WORD_ATTR, 1.0)
        wc_eq[w] = e; wc_w[w] = wv
    for ci in range(n):
        liks = rng.dirichlet(np.ones(len(cands)))
        for w, p in zip(cands, liks):
            s_eq.set_attr(wc_eq[w], MS.channel_attr(ci), float(p))
            s_w.set_attr(wc_w[w], MS.channel_attr(ci), float(p))
            s_w.set_attr(wc_w[w], WA.weight_attr(ci), 1.0)
    eq_term = MS._Pred(MS.predict_many_settings_term(n))
    w_term = MS._Pred(WA.predict_weighted_term(n))
    eq_pick = s_eq.node(s_eq.evaluate(eq_term, {}))["attrs"]["name"]
    w_pick = s_w.node(s_w.evaluate(w_term, {}))["attrs"]["name"]
    assert eq_pick == w_pick


def test_no_fit_no_donkey_source_audit():
    """The module source (docstrings stripped) contains no fit/gradient/net/sweep."""
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "domains", "weighted_admissibility.py")
    with open(path) as f:
        tree = ast.parse(f.read())
    # strip docstrings
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
