"""node_admissibility_graphs — iter-49: ADMISSIBILITY GRAPHS ON THE NODES THEMSELVES.

THE USER: "the finer grain is admissibility graphs on the nodes themselves."

iter-48 (docs/agent_loop_iteration48_weighted_admissibility.md) found per-NODE
reliability is too COARSE. The wall (iter-45): a wrong-order node is
informative-but-WRONG — confidently peaked at the WRONG word on a SPECIFIC contrast
(e.g. b/d), but HIGH on AVERAGE over all words. A single per-node weight can only
down-weight that node by its AVERAGE reliability, so its weight stays high and it KEEPS
diluting on exactly the contrasts it gets wrong. The dilution is per-(word/contrast);
the iter-48 weight is per-node — the wrong GRANULARITY.

THE FIX (this iter) — each (cue x order) node gets its OWN admissibility (sub-)graph: a
per-WORD reliability `weight_i(w)`, measured inner-LOSO on TRAIN speakers only, GATING
that node's contribution TO THAT WORD:

    score(w) = PROD_i  P_i(w) ^ weight_i(w)            (a graph Times of Pow terms)
    predict(s) = Argmax_w score(w)

where weight_i(w) is now PER-CANDIDATE — the node's measured reliability for word w
specifically, NOT its average over all words. A node admissible/reliable for w counts in
full (P^~1); a node NOT admissible for w (confidently-wrong when it claims w) ABSTAINS on
w (P^0 = 1 — cannot dilute the w hypothesis). So the wrong-order node abstains on the
contrasts it is not admissible for, and the per-contrast dilution disappears.

THE RECURSIVE (G, Gamma) — admissibility all the way down. The recognition is admissible
iff its node-combination is; each NODE is admissible (for THIS contrast) iff its own
sub-graph (its measured per-word reliability) says so. iter-48's per-node weight is the
special case weight_i(w) == weight_i for all w; iter-45's equal combine-all is the further
special case weight_i(w) == 1.

THE GATE — a per-word CONVEX BLEND toward the node's FLAT reference (NOT a per-word
exponent). iter-48 gated by P_i(w)^weight_i (a node-CONSTANT exponent, so the whole node
scaled uniformly across words). A per-word EXPONENT is WRONG: since 0<=P<=1, P^0 = 1 is
the LARGEST possible contribution, so abstaining-by-exponent INFLATES exactly the words the
node is bad at (it boosts the inadmissible hypothesis). The correct per-contrast abstain
makes an inadmissible node contribute a WORD-NEUTRAL value that drops out of the Argmax:

    gated_i(w) = weight_i(w) * P_i(w) + (1 - weight_i(w)) * u_i

where u_i is the node's FLAT reference (uniform 1/n_candidates — word-independent). When
admissible (weight->1): full P_i(w). When NOT admissible (weight->0): the flat u_i, the
SAME for every candidate -> contributes equally to all words -> cancels in the Argmax (the
node truly ABSTAINS on that contrast, neither diluting nor inflating). score(w) =
PROD_i gated_i(w); the gate is a graph Term (Plus of Times — the convex blend). equal
weights (all 1) recover the equal combine-all PROD_i P_i(w) exactly.

THE PER-WORD RELIABILITY MEASUREMENT (the node's admissibility sub-graph). For node i and
word w, measured by inner leave-one-speaker-out on the TRAIN speakers only:

    weight_i(w) = max(0, (rel_i(w) - chance) / (1 - chance))

where rel_i(w) is the node's PRECISION for w on inner-LOSO train tokens: of the held-out
train tokens the node CLAIMED were w (its likelihood peaked at w), the fraction that were
TRULY w. This is exactly the per-contrast admissibility the wall needs: a node that
confidently CLAIMS w but is usually WRONG when it claims w has low rel_i(w) -> abstains on
w (P^0) -> stops diluting the w hypothesis. chance = 1/n_candidates (DERIVED). A node that
never claims w has no precision sample for w -> its weight for w falls back to the node's
overall (per-node, iter-48) reliability (a graceful, no-leakage default — see
measure_per_contrast_reliabilities).

NO-DONKEY / NO-FIT (auditable): weight_i(w) is a MEASUREMENT (inner-LOSO precision on
TRAIN speakers, the same argmax-likelihood the harness scores with), translated to a
per-candidate graph attr. The COMBINATION decision is the graph Term (Argmax of
Times-of-Pow, evaluated by substrate.evaluate). No fit, no gradient, no learned weight,
no sweep. LOSO-clean: the held voice's tokens never enter any reliability measurement.
Equal/all-admissible recovers iter-45's equal combine-all exactly.
"""
from __future__ import annotations

import numpy as np

import domains.many_settings_recognizer as MS
from domains.weighted_admissibility import weight_attr, reliability_to_weight

__all__ = [
    "weight_attr", "flat_attr", "per_contrast_weight", "reliability_to_weight",
    "gated_score_term", "predict_weighted_term",
]


def flat_attr(i: int) -> str:
    """Attr key for node i's FLAT reference (uniform 1/n_candidates) — the word-neutral
    value an inadmissible node blends toward so it drops out of the Argmax."""
    return f"u_ch{i}"


def per_contrast_weight(precision: float, chance: float) -> float:
    """The node's admissibility-sub-graph value for one word: above-chance PRECISION
    normalised to [0,1] (the SAME fixed map iter-48 uses, now per-contrast). precision is
    the node's inner-LOSO precision for the word (of the tokens it CLAIMED were the word,
    the fraction truly that word). No free parameter; chance DERIVED."""
    return reliability_to_weight(precision, chance)


def _Plus(items): return {"type": "Plus", "items": items}
def _Minus(a, b): return {"type": "Minus", "a": a, "b": b}


def _gated(i: int) -> dict:
    """gated_i(w) = weight_i(w)*P_i(w) + (1 - weight_i(w))*u_i — the per-word CONVEX BLEND
    of node i's likelihood toward its flat reference, by the node's per-contrast
    admissibility. weight==1 -> P_i(w); weight==0 -> u_i (word-neutral, abstains). A graph
    Term (Plus of Times); NO exponent, so an inadmissible node never inflates a word."""
    w = MS._Attr(MS._V("w"), weight_attr(i))
    p = MS._Attr(MS._V("w"), MS.channel_attr(i))
    u = MS._Attr(MS._V("w"), flat_attr(i))
    return _Plus([
        MS._Times([w, p]),
        MS._Times([_Minus(MS._Lit(1.0), w), u]),
    ])


def gated_score_term(n_channels: int) -> dict:
    """score(w) = PROD_i gated_i(w) — the per-CONTRAST admissibility product as a graph
    Term (a variadic Times over per-node convex-blend gates). Each node's likelihood is
    blended toward its flat reference by its per-word admissibility weight before the
    product; an inadmissible node contributes the word-neutral flat value and abstains.
    All weights == 1 recovers the equal combine-all PROD_i P_i(w). NO fit, NO exponent."""
    return MS._Times([_gated(i) for i in range(n_channels)])


def predict_weighted_term(n_channels: int) -> dict:
    """predict(s) = Argmax over candidate words of PROD_i gated_i(w). The whole per-contrast
    admissibility decision as graph data — the SAME Argmax-of-score shape every recogniser
    uses, the score being the per-contrast-admissibility-gated product over the nodes'
    per-candidate likelihoods."""
    return MS._Argmax(MS._NodesWhere("Concept", MS.WORD_ATTR, MS._Lit(1.0)), "w",
                      gated_score_term(n_channels))
