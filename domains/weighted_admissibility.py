"""weighted_admissibility — iter-48: the WEIGHTED ADMISSIBILITY RULE GRAPH.

THE USER: "they need weight — almost like a weighted admissibility rule graph."

iter-45's wall (docs/agent_loop_iteration45_ordern_interpolation.md): the EQUAL,
symmetric Argmax-of-product over every (cue x order) node SURFACES which order each
channel wants (the per-channel best-order diagnostic is unambiguous: gammatone
spectral channels want order-2 curvature; sparse/orthogonal cues want order-0) but
CANNOT ACT on it. A wrong-order node is informative-but-WRONG (its likelihood is
peaked at the wrong word, NOT near-flat), so it DILUTES the product. The equal product
gives every node the SAME say everywhere; the unreliable node drags the reliable.

THE FORM (this iter): weight each node by its MEASURED reliability —

    score(w) = PROD_i  P_i(w) ^ weight_i          (a graph Times of Pow terms)
    predict(s) = Argmax_w score(w)

A reliable node (weight -> 1) counts in full; an unreliable / wrong-order node
(weight -> 0) is raised toward P^0 = 1 (FLAT, regardless of how peaked-wrong its raw
likelihood was) so it CANNOT dilute the product. This is the weighted admissibility
rule graph: the structure stays binary-admissible (every node is in the product), the
RULES carry weights. P^0 == 1 == "this rule is inadmissible here, abstain"; P^1 ==
full say; fractional == partial reliability.

THE IN-THESIS LINE (DERIVED, NOT SEARCHED — the hard constraint). The weight MUST be
the agent's MEASURED reliability, NOT a swept / fit / gradient parameter:

    weight_i = max(0, (acc_i - chance) / (1 - chance))

where acc_i is node i's HELD-OUT accuracy MEASURED ON THE TRAIN FOLDS ONLY (inner
leave-one-speaker-out over the train speakers — the same yardstick iter-42 used),
chance = 1/n_candidates (DERIVED, not a knob). This is the node's above-chance
reliability normalised to [0,1]:
  · a node at chance      -> weight 0   -> P^0 = 1 (abstains, cannot dilute)
  · a perfectly reliable node -> weight 1 -> full say
There is NO free parameter to tune: chance is derived; the map (acc - chance)/(1 -
chance) is the fixed reliability normalisation; the accuracy is a MEASUREMENT. We do
NOT try weight values and keep the best (that is the forbidden negative-space search).
iter-45's per-channel best-order diagnostic IS this reliability map, re-used as the
weight — surfaced as a measurement, now ACTED on.

NO-DONKEY: the weight is a measurement (inner-LOSO accuracy, computed by the same
adapter math the harness uses) translated to a graph attr; the COMBINATION decision is
the graph Term (Argmax of Times-of-Pow, evaluated by substrate.evaluate). No fit, no
gradient, no learned weight, no sweep. LOSO-clean: weights from TRAIN folds only; the
held voice's tokens never enter any reliability measurement.
"""
from __future__ import annotations

import numpy as np

import domains.many_settings_recognizer as MS


# ---------------------------------------------------------------------------
# The weighted decision Term:  Argmax_w  PROD_i  Pow(P_i(w), weight_i).
# Each node i contributes Pow(Attr(w, p_ch{i}), Attr(w, w_ch{i})) — the per-candidate
# likelihood raised to the node's measured-reliability weight. The weight is a graph
# attr (constant across candidates within a fold: it is the NODE's reliability, not a
# per-candidate value), set per fold by the adapter from the inner-LOSO measurement.
# ---------------------------------------------------------------------------

def weight_attr(i: int) -> str:
    """Attr key for node i's measured-reliability weight on a candidate word node."""
    return f"w_ch{i}"


def _Pow(a, b):
    return {"type": "Pow", "a": a, "b": b}


def weighted_score_term(n_channels: int) -> dict:
    """score(w) = PROD_i Pow(P_i(w), weight_i) — the WEIGHTED admissibility product as
    a graph Term (a variadic Times over per-node Pow(likelihood, weight)). The equal
    combine-all (many_settings_recognizer.many_settings_score_term) is the special case
    weight_i == 1 for all i; here each node carries its MEASURED reliability weight.
    NO selection, NO hand-weight: every node stays in the product; the weights are the
    measured reliabilities the adapter populated per fold."""
    return MS._Times([
        _Pow(MS._Attr(MS._V("w"), MS.channel_attr(i)),
             MS._Attr(MS._V("w"), weight_attr(i)))
        for i in range(n_channels)
    ])


def predict_weighted_term(n_channels: int) -> dict:
    """predict(s) = Argmax over candidate words of PROD_i Pow(P_i(w|s), weight_i).
    The whole WEIGHTED admissibility decision as graph data — the SAME Argmax-of-score
    shape every recogniser uses, the score being the reliability-weighted product over
    the nodes' per-candidate likelihoods."""
    return MS._Argmax(MS._NodesWhere("Concept", MS.WORD_ATTR, MS._Lit(1.0)), "w",
                      weighted_score_term(n_channels))


# ---------------------------------------------------------------------------
# The reliability MEASUREMENT (inner leave-one-speaker-out on the TRAIN folds only).
# For each node, hold out one train speaker, build the node's per-word evidence from the
# remaining train speakers, predict the held-out train speaker's tokens, average over
# all inner folds -> acc_i. weight_i = max(0, (acc_i - chance)/(1 - chance)). This is a
# MEASUREMENT (the same yardstick the harness scores with), computed with NO test
# leakage (the outer-held voice is not in train at all) and NO sweep.
# ---------------------------------------------------------------------------

def reliability_to_weight(acc: float, chance: float) -> float:
    """The fixed (NOT searched) reliability -> weight map: above-chance accuracy
    normalised to [0,1]. acc==chance -> 0 (abstain, P^0=1); acc==1 -> 1 (full say).
    chance is DERIVED (1/n_candidates), not a knob; the map has no free parameter."""
    if not np.isfinite(acc):
        return 0.0
    if chance >= 1.0:
        return 0.0
    w = (acc - chance) / (1.0 - chance)
    return float(max(0.0, w))


__all__ = ["weight_attr", "weighted_score_term", "predict_weighted_term",
           "reliability_to_weight"]
