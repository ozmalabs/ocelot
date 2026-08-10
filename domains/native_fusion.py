"""native_fusion — the NEW/SOTA hearing path's FUSION DECISION as a NATIVE Rust Term.

Rank-1 of the migration audit (a87613a4df1e5e200): the multi-pronged fusion decision
in the new path (scripts/articulatory_gamma.py ~600-611, scripts/perception_composition.py
~384-390) is a Python dict-comprehension argmax —

    log_a_h_c[w] = log_a_h[w] - max_w' log_a_h[w']        # formant prong, top-centred
    log_a_a_c[w] = log_a_a[w] - max_w' log_a_a[w']        # articulatory prong, top-centred
    logA[w]      = log_a_h_c[w] + w_art * log_a_a_c[w] + ng_logp[w]
    predict      = argmax_w logA[w]

Per CLAUDE.md the agent IS a typed graph in Rust; the recognition DECISION must be a
graph-resident Term, not a Python dict comprehension. The audit confirmed this is exactly
Argmax over Plus of Times — ALL primitives already exist (Argmax, Plus, Minus, Times,
MaxOver, Attr, Var, Lit, NodesWhere — verified present in runners/dsl/src/term.rs +
jsonio.rs), ZERO new primitives, and domains/weighted_admissibility.predict_weighted_term
already proves the Argmax-of-(graph score) pattern native.

THE NATIVE TERM (per candidate word w, with the top-centring done IN the graph):

    score(w) = Plus([
        Minus( Attr(w, log_a_h),  MaxOver_w'( Attr(w', log_a_h) ) ),          # formant prong, top-centred
        Times([ Lit(w_art),  Minus( Attr(w, log_a_a), MaxOver_w'( Attr(w', log_a_a) ) ) ]),  # articulatory, weighted
        Attr(w, ng_logp),                                                     # n-gram log-prior
    ])
    predict = Argmax over { Concept : is_word == 1 } of score(w)

The top-centring (subtract max_w') is a MaxOver over the SAME candidate-word set, evaluated
natively — so the Python wrapper does NOT pre-centre; it feeds the RAW per-prong
log-admissibilities (log_a_h, log_a_a) and the train-only n-gram log-prior (ng_logp) as
graph attrs, plus w_art (the train-measured reliability weight) as a Lit inside the Term.
The whole decision — centring, weighting, summing, argmax — is the native Rust evaluator.

DONKEY-CLEAN: no net, no .fit, no gradient, no sweep, no learned weight. The Term is
evaluated by substrate.evaluate (native Rust eval). The Python here is world-adapter glue
ONLY: it consumes the prong channels the existing recogniser computes (read-only) and
writes them as graph attrs, then reads back the argmax word. The fusion SCORING files
(articulatory_gamma.py, perception_composition.py) are NOT modified — they are read for the
prong logic; this module is a SEPARATE consumer.
"""
from __future__ import annotations

import domains.many_settings_recognizer as MS


WORD_ATTR = MS.WORD_ATTR  # "is_word"

# Per-word graph attrs the wrapper populates (RAW, un-centred — the graph centres them).
LOG_A_H_ATTR = "log_a_h"   # formant prong log-admissibility (raw)
LOG_A_A_ATTR = "log_a_a"   # articulatory prong log-admissibility (raw)
NG_LOGP_ATTR = "ng_logp"   # n-gram log-prior (train-only)
PREC_A_ATTR = "prec_a"     # AUX prong's TRAIN precision-when-it-asserts-this-word (track record)


# ---- Term constructors (mirror many_settings_recognizer / weighted_admissibility) ----

def _V(n):
    return {"type": "Var", "name": n}


def _Lit(v):
    return {"type": "Lit", "value": v}


def _Attr(node, k):
    return {"type": "Attr", "node": node, "key": k}


def _Plus(items):
    return {"type": "Plus", "items": items}


def _Minus(a, b):
    return {"type": "Minus", "a": a, "b": b}


def _Times(items):
    return {"type": "Times", "items": items}


def _MaxOver(src, var, val):
    return {"type": "MaxOver", "source": src, "var_name": var,
            "value": val, "default": None}


def _Argmax(src, var, val):
    return {"type": "Argmax", "source": src, "var_name": var,
            "value": val, "default": None}


def _NodesWhere(t, k, v):
    return {"type": "NodesWhere", "node_type": t, "attr_key": k, "value": v}


def _Div(a, b):
    return {"type": "Div", "a": a, "b": b}


def _Neg(a):
    return {"type": "Neg", "arg": a}


def _Sum(src, var, val):
    return {"type": "Sum", "source": src, "var_name": var, "value": val}


def _Count(src):
    return {"type": "Count", "source": src}


def _Min(items):
    return {"type": "Min", "items": items}


def _word_set():
    """The candidate-word node set: every Concept with is_word == 1 (the same source
    weighted_admissibility / many_settings use for the Argmax)."""
    return _NodesWhere("Concept", WORD_ATTR, _Lit(1.0))


def _top_centred(var_name: str, attr_key: str) -> dict:
    """Attr(var, attr) - MaxOver_w'(Attr(w', attr)) — the prong's log-admissibility minus
    the max over ALL candidate words (top-centring, so the best word = 0, others < 0). The
    MaxOver ranges over the same word set with a FRESH inner var so it does not shadow the
    outer Argmax var. Computed natively by the evaluator, NOT pre-centred in Python."""
    inner = "_w_top"
    return _Minus(
        _Attr(_V(var_name), attr_key),
        _MaxOver(_word_set(), inner, _Attr(_V(inner), attr_key)),
    )


def fusion_score_term(w_art: float) -> dict:
    """score(w) = log_a_h_c[w] + w_art * log_a_a_c[w] + ng_logp[w], with each prong
    top-centred IN the graph (Minus of Attr and MaxOver). w_art (the train-measured
    reliability weight) enters as a Lit inside a Times — a per-fold constant, exactly as
    the Python multiplies w_art * log_a_a_c[w]. A graph Plus of the three soft excluders."""
    return _Plus([
        _top_centred("w", LOG_A_H_ATTR),                                  # formant, top-centred
        _Times([_Lit(float(w_art)), _top_centred("w", LOG_A_A_ATTR)]),    # articulatory, weighted
        _Attr(_V("w"), NG_LOGP_ATTR),                                     # n-gram log-prior
    ])


def predict_fusion_term(w_art: float) -> dict:
    """predict(s) = Argmax over candidate words of fusion_score_term(w). The WHOLE
    multi-pronged fusion decision as graph data — the SAME Argmax-of-score shape
    weighted_admissibility.predict_weighted_term uses, the score being the top-centred
    soft-excluder sum the new hearing path fuses with."""
    return _Argmax(_word_set(), "w", fusion_score_term(w_art))


# =========================================================================================
#  PER-CONTEXT RELIABILITY WEIGHTING  (the fusion-weighting fix — the agent's design)
# =========================================================================================
#  THE GAP (commit 90b799c9): the multi-pronged fusion (60.6% TFS / 58.4% cutover) TRAILS
#  the formant-prong-alone (62.2%). w_art is a GLOBAL train constant, so the weak articulatory
#  prong is multiplied in at the SAME weight on EVERY token — including tokens where it is
#  locally flat/uncertain. There it drags the strong formant prong wherever they disagree
#  (the margin-error). A global weight cannot tell a token the weak prong KNOWS from a token
#  it doesn't.
#
#  THE FIX — weighted-admissibility, per-context. Each prong is a soft excluder; its weight
#  on THIS token is the GLOBAL reliability times a PER-CONTEXT TRUST factor = how PEAKED the
#  prong's own admissibility field is for this token (its DECISION MARGIN / confidence). The
#  signal is read off the prong's OWN top-centred scores — no extra data, no fit:
#
#      score_c_p(w) = Attr(w, p) - MaxOver_w'(Attr(w', p))            (<= 0, best word = 0)
#      conf_p       = -(1/N) * Sum_w score_c_p(w)                     ("mean depth" of the field)
#
#  conf_p is the average gap by which the rest of the field sits BELOW this prong's winner.
#    * FLAT field (the prong has no opinion here: every word near-equally admissible)
#      -> conf_p ~ 0  -> the prong DEFERS (its excluder flattens toward neutral, cannot corrupt).
#    * PEAKED field (one word clearly stands out) -> conf_p large -> the prong CONSTRAINS.
#  conf_p is composed from existing native Terms ONLY: Neg(Div(Sum_w(top_centred), Count)).
#  It needs no "second-max" primitive and adds nothing to the grammar.
#
#  The per-context prong weight = global_w_p * (conf_p / conf_ref_p). conf_ref_p is a TRAIN-
#  measured typical confidence (a Lit, per fold) that makes the two prongs' margins comparable
#  in scale (otherwise the prong with the larger raw spread would dominate by units, not trust).
#
#  SAFE (never below the best single prong): where the articulatory prong is flat/uncertain on
#  a token, conf_a -> 0 so its weight -> 0 and the formant prong decides that token ALONE — the
#  fusion cannot underperform formant-alone on the tokens the weak prong would have dragged.
#  Symmetrically the formant prong is also confidence-weighted, so where IT is uncertain the
#  others may help. ADDITIVE: where the weak prong is locally PEAKED *and* globally reliable
#  (its strong digits), conf_a is large and it still helps.
#
#  HONEST LIMIT: a prong can be confidently WRONG (peaked on the wrong word). Margin/peakiness
#  cannot catch that — it down-weights UNCERTAIN prongs (the dominant drag source: disagreement
#  born of the weak prong's fuzziness), not confidently-wrong ones. The driver measures whether
#  that is enough to clear 62.2%.
#  DONKEY: the whole decision — top-centring, the margin, the per-context weighting, the sum,
#  the argmax — is ONE native Term evaluated by substrate.evaluate. No net, no .fit, no gradient,
#  no sweep. conf_ref is a MEASUREMENT (median train margin), not a tuned knob.


def _confidence(attr_key: str) -> dict:
    """conf_p = -(1/N) * Sum_w (Attr(w,p) - MaxOver_w'(Attr(w',p)))  — the mean depth of the
    prong's top-centred admissibility field = its per-context decision margin / confidence.
    A FRESH summation var (_w_conf) ranges the word set so it does not shadow the outer Argmax
    var or the inner top-centring var. Native: Neg(Div(Sum(top_centred), Count))."""
    sv = "_w_conf"
    centred = _Minus(
        _Attr(_V(sv), attr_key),
        _MaxOver(_word_set(), "_w_top2", _Attr(_V("_w_top2"), attr_key)),
    )
    return _Neg(_Div(_Sum(_word_set(), sv, centred), _Count(_word_set())))


def fusion_score_term_pcw(w_art: float, conf_ref_a: float) -> dict:
    """PER-CONTEXT-WEIGHTED fused score:

        score(w) = log_a_h_c[w]                                  # ANCHOR — full weight, ALWAYS
                 + w_art * (conf_a/cref_a) * log_a_a_c[w]        # AUX — per-context-weighted
                 + ng_logp[w]

    ASYMMETRY IS THE SAFETY ARGUMENT. The formant prong is the 62.2% ANCHOR; it carries its
    FULL weight on every token (an unweighted soft excluder). The WEAK articulatory prong is
    the only one re-weighted per-context: its excluder is scaled by w_art * (conf_a/cref_a).
      * conf_a ~ 0 (articulatory FLAT here, no opinion) -> aux weight ~ 0 -> the ANCHOR decides
        the token ALONE -> fusion CANNOT underperform formant-alone on the dragged tokens.
      * conf_a large (articulatory PEAKED here) AND globally reliable (w_art > 0) -> the aux
        still helps (ADDITIVE), e.g. breaks an anchor near-tie on a digit it knows.
    We do NOT confidence-weight the anchor: down-weighting the strong prong where ITS field is
    flat (a hard token) would hand the decision to the weak prongs — the opposite of safe. The
    n-gram is a fixed prior (no per-token field) and stays unweighted.

    The per-context factor is CLAMPED to [0,1]: min(1, conf_a/cref_a). The AUX prong's weight can
    therefore only ever DROP BELOW its global w_art (when uncertain here), never rise ABOVE it.
    This makes per-context weighting a pure soft-EXCLUDER down-weighter — it can only REMOVE the
    drag the global weight caused, never grant the weak prong MORE trust than its measured global
    reliability. A single native Term."""
    wc_a = _Min([_Lit(1.0), _Div(_confidence(LOG_A_A_ATTR), _Lit(float(conf_ref_a)))])
    return _Plus([
        _top_centred("w", LOG_A_H_ATTR),                                       # formant ANCHOR (full weight)
        _Times([_Lit(float(w_art)), wc_a, _top_centred("w", LOG_A_A_ATTR)]),   # articulatory AUX (global x per-context)
        _Attr(_V("w"), NG_LOGP_ATTR),                                          # n-gram log-prior (unweighted)
    ])


def predict_fusion_term_pcw(w_art: float, conf_ref_a: float) -> dict:
    """predict(s) = Argmax over candidate words of fusion_score_term_pcw(...). The whole
    per-context-weighted multi-pronged fusion as graph data — same Argmax-of-score shape, the
    AUX prong weight now a per-context margin (the anchor unweighted) instead of a global Lit."""
    return _Argmax(_word_set(), "w", fusion_score_term_pcw(w_art, conf_ref_a))


# =========================================================================================
#  CORRECTNESS-KEYED TRUST  (gap 2, the named next from 7cd7f60e — the agent's fix)
# =========================================================================================
#  WHY pcw (margin) STALLED at 61.4% < formant-alone 62.2%: the residual drag is the AUX prong
#  being CONFIDENTLY WRONG on six (six->eight 68/300, six->seven 66/300). Margin measures
#  CONFIDENCE, not CORRECTNESS — a confidently-wrong prong has HIGH margin and keeps full weight
#  (Dunning-Kruger inside the fusion). Margin can only catch UNCERTAIN prongs; it cannot catch
#  a prong that is reliably wrong while certain.
#
#  THE FIX — a trust signal keyed to the AUX prong's per-ASSERTED-DIGIT CORRECTNESS = its TRACK
#  RECORD. On the TRAIN speakers ONLY, measure prec_a[d] = P(true == d | AUX prong asserts d) =
#  the fraction of train tokens, among those where the AUX prong's argmax is d, that are actually
#  d. This is the AUX prong's PRECISION-when-it-asserts-d — a MEASUREMENT of how reliable the
#  prong is at the moment it claims a digit. A prong reliably-wrong when it asserts "six" gets a
#  LOW prec_a["six"]; a prong reliably-right when it asserts "eight" gets a HIGH prec_a["eight"].
#
#  HOW IT WEIGHTS THE VOTE. The AUX prong's vote FOR a digit is its ASSERTION = argmax_w a_c(w).
#  The correctness-keyed trust on a token is prec_a[ that asserted digit ] — read NATIVELY as
#  Attr( Argmax_w a_c(w), prec_a ). When the AUX prong asserts "six" and prec_a["six"] is low,
#  its WHOLE excluder is scaled down on that token — catching the confident-wrongness margin
#  cannot. (prec_a is already in [0,1]: a precision, no clamp needed.)
#
#  COMBINED WITH MARGIN. The fused AUX trust is the PRODUCT of the two soft excluders:
#      trust_a(token) = min(1, conf_a/cref_a)  *  prec_a[ argmax_w a_c(w) ]
#  margin (in-context certainty) AND precision (the track record). The product is the soft-AND
#  of two reasons to DEFER: it is small whenever the AUX prong is EITHER uncertain here (low
#  margin) OR reliably-wrong on what it is asserting (low precision) — exactly the union of
#  failure modes the diagnosis names. Both factors are in [0,1], so the combined trust is in
#  [0,1] and the AUX weight w_art*trust_a can still only DROP BELOW its global w_art, never rise
#  (a pure soft-EXCLUDER down-weighter — it can only REMOVE drag). The formant ANCHOR stays at
#  full weight (the same safety argument: never hand a hard token to the weak prong).
#
#  DONKEY / TRAIN-ONLY SAFETY. prec_a is computed PER FOLD from that fold's TRAIN speakers only
#  (the LOSO held-out speaker is NEVER used to build the precision table — recomputed each fold).
#  This is a MEASUREMENT of the prong's track record, not a sweep-to-fit: no tuning against the
#  test, no per-test-token peeking, no gradient, no .fit. The whole decision — the AUX argmax,
#  the precision lookup, the margin, their product, the weighting, the sum, the argmax — is ONE
#  native Term via substrate.evaluate (Argmax / Attr / Min / Div / Times / Plus all already in
#  term.rs; zero new primitives, no Rust).


def _aux_assertion() -> dict:
    """Argmax_w' (top-centred AUX field) = the digit the AUX prong ASSERTS this token (its own
    winner). A FRESH var (_w_assert) ranges the word set; the value is the AUX prong's top-centred
    score so the argmax is the AUX prong's most-admissible word. Native Argmax -> a node."""
    av = "_w_assert"
    centred = _Minus(
        _Attr(_V(av), LOG_A_A_ATTR),
        _MaxOver(_word_set(), "_w_top3", _Attr(_V("_w_top3"), LOG_A_A_ATTR)),
    )
    return _Argmax(_word_set(), av, centred)


def _correctness_trust() -> dict:
    """prec_a[ argmax_w a_c(w) ] — the AUX prong's TRAIN precision on the digit IT asserts this
    token. Attr of the AUX-assertion node (native): Attr(Argmax_w aux_field, prec_a). In [0,1]."""
    return _Attr(_aux_assertion(), PREC_A_ATTR)


def fusion_score_term_ckt(w_art: float, conf_ref_a: float) -> dict:
    """CORRECTNESS-KEYED (+ margin) fused score:

        score(w) = log_a_h_c[w]                                              # ANCHOR — full weight
                 + w_art * min(1, conf_a/cref_a) * prec_a[argmax_a] * log_a_a_c[w]  # AUX trust
                 + ng_logp[w]

    The AUX prong's per-context weight is w_art times the PRODUCT of its margin trust
    min(1, conf_a/cref_a) and its correctness trust prec_a[asserted digit]. Defers when the AUX
    prong is EITHER uncertain here OR reliably-wrong on what it asserts. Same anchor-stays-full
    safety; the AUX weight can only drop below w_art (both factors <= 1). One native Term."""
    margin_t = _Min([_Lit(1.0), _Div(_confidence(LOG_A_A_ATTR), _Lit(float(conf_ref_a)))])
    corr_t = _correctness_trust()
    return _Plus([
        _top_centred("w", LOG_A_H_ATTR),                                            # formant ANCHOR
        _Times([_Lit(float(w_art)), margin_t, corr_t, _top_centred("w", LOG_A_A_ATTR)]),  # AUX
        _Attr(_V("w"), NG_LOGP_ATTR),                                               # n-gram prior
    ])


def fusion_score_term_ckt_min(w_art: float, conf_ref_a: float) -> dict:
    """Robustness variant — the two trust factors combined by MIN instead of PRODUCT:
        trust_a = min( min(1, conf_a/cref_a), prec_a[argmax_a] )
    Defers to whichever excluder is more pessimistic. Measured alongside the product to confirm
    the result is not an artifact of one combiner choice."""
    margin_t = _Min([_Lit(1.0), _Div(_confidence(LOG_A_A_ATTR), _Lit(float(conf_ref_a)))])
    corr_t = _correctness_trust()
    return _Plus([
        _top_centred("w", LOG_A_H_ATTR),
        _Times([_Lit(float(w_art)), _Min([margin_t, corr_t]), _top_centred("w", LOG_A_A_ATTR)]),
        _Attr(_V("w"), NG_LOGP_ATTR),
    ])


def fusion_score_term_corr_only(w_art: float) -> dict:
    """ABLATION — correctness trust ALONE (no margin): the AUX weight is w_art * prec_a[argmax_a].
    Isolates how much of the fix is the precision track record vs the margin."""
    return _Plus([
        _top_centred("w", LOG_A_H_ATTR),
        _Times([_Lit(float(w_art)), _correctness_trust(), _top_centred("w", LOG_A_A_ATTR)]),
        _Attr(_V("w"), NG_LOGP_ATTR),
    ])


def predict_fusion_term_ckt(w_art: float, conf_ref_a: float, combiner: str = "product") -> dict:
    """predict(s) = Argmax over candidate words of the correctness-keyed fused score. `combiner`
    selects how the margin and correctness trusts combine: 'product' (default), 'min', or
    'corr_only' (correctness alone, ablation)."""
    if combiner == "min":
        score = fusion_score_term_ckt_min(w_art, conf_ref_a)
    elif combiner == "corr_only":
        score = fusion_score_term_corr_only(w_art)
    else:
        score = fusion_score_term_ckt(w_art, conf_ref_a)
    return _Argmax(_word_set(), "w", score)


# ---------------------------------------------------------------------------
# World-adapter glue: build the candidate-word substrate, feed the prong channels as
# graph attrs, evaluate the native Term, read back the argmax word. NO decision here —
# the decision is the Term; this only translates the prong dicts into/out of the graph.
# ---------------------------------------------------------------------------

def build_word_substrate(Substrate, words):
    """A Substrate with one Concept node per candidate word (is_word == 1). Returns
    (substrate, {word: node_id}). Pure mechanical graph construction."""
    s = Substrate()
    nodes = {}
    for w in words:
        nid = s.add_node("Concept", {"name": w})
        s.set_attr(nid, WORD_ATTR, 1.0)
        nodes[w] = nid
    return s, nodes


def native_predict(s, word_nodes, log_a_h: dict, log_a_a: dict, ng_logp: dict,
                   w_art: float, Pred):
    """Feed the RAW (un-centred) prong channels as graph attrs and return the native-Term
    argmax word. log_a_h / log_a_a / ng_logp are {word: value}; w_art is the train weight.
    The Term does the top-centring + weighting + sum + argmax natively (substrate.evaluate).
    `Pred` is many_settings_recognizer._Pred (the evaluable Term wrapper)."""
    for w, nid in word_nodes.items():
        s.set_attr(nid, LOG_A_H_ATTR, float(log_a_h[w]))
        s.set_attr(nid, LOG_A_A_ATTR, float(log_a_a[w]))
        s.set_attr(nid, NG_LOGP_ATTR, float(ng_logp[w]))
    term = Pred(predict_fusion_term(w_art))
    pick_node = s.evaluate(term, {})
    return s.node(pick_node)["attrs"]["name"]


def native_confidence(s, word_nodes, log_a: dict, attr_key: str, Pred):
    """Evaluate the per-context confidence (mean depth of the top-centred field) of ONE prong
    natively, for a token whose per-word prong values are `log_a`. Used to MEASURE the train
    reference confidence per prong (conf_ref). Returns a float."""
    for w, nid in word_nodes.items():
        s.set_attr(nid, attr_key, float(log_a[w]))
    val = s.evaluate(Pred(_confidence(attr_key)), {})
    return float(val)


def native_predict_pcw(s, word_nodes, log_a_h: dict, log_a_a: dict, ng_logp: dict,
                       w_art: float, conf_ref_a: float, Pred):
    """PER-CONTEXT-WEIGHTED fusion: feed the RAW prong channels + ng-prior, plus the train
    reference AUX confidence (conf_ref_a) as a Lit, and return the native-Term argmax word. The
    Term computes the AUX prong's per-context confidence FROM these attrs, scales its excluder by
    w_art * confidence/conf_ref_a (the formant anchor stays full weight), sums, and argmaxes — all
    native (substrate.evaluate). Same I/O contract as native_predict; only the fusion weighting
    differs."""
    for w, nid in word_nodes.items():
        s.set_attr(nid, LOG_A_H_ATTR, float(log_a_h[w]))
        s.set_attr(nid, LOG_A_A_ATTR, float(log_a_a[w]))
        s.set_attr(nid, NG_LOGP_ATTR, float(ng_logp[w]))
    term = Pred(predict_fusion_term_pcw(w_art, conf_ref_a))
    pick_node = s.evaluate(term, {})
    return s.node(pick_node)["attrs"]["name"]


def native_predict_ckt(s, word_nodes, log_a_h: dict, log_a_a: dict, ng_logp: dict,
                       w_art: float, conf_ref_a: float, prec_a: dict, Pred,
                       combiner: str = "product"):
    """CORRECTNESS-KEYED fusion: feed the RAW prong channels + ng-prior + the AUX prong's TRAIN
    per-asserted-digit precision table (prec_a: {word: precision-when-AUX-asserts-it}) as the
    per-word PREC_A_ATTR, plus conf_ref_a as a Lit, and return the native-Term argmax word. The
    Term computes the AUX assertion (its argmax), looks up its precision, multiplies by the margin
    trust, scales the AUX excluder, sums, and argmaxes — all native (substrate.evaluate). Same I/O
    contract as native_predict_pcw; only the AUX trust now also carries the correctness key."""
    for w, nid in word_nodes.items():
        s.set_attr(nid, LOG_A_H_ATTR, float(log_a_h[w]))
        s.set_attr(nid, LOG_A_A_ATTR, float(log_a_a[w]))
        s.set_attr(nid, NG_LOGP_ATTR, float(ng_logp[w]))
        s.set_attr(nid, PREC_A_ATTR, float(prec_a[w]))
    term = Pred(predict_fusion_term_ckt(w_art, conf_ref_a, combiner))
    pick_node = s.evaluate(term, {})
    return s.node(pick_node)["attrs"]["name"]


__all__ = [
    "WORD_ATTR", "LOG_A_H_ATTR", "LOG_A_A_ATTR", "NG_LOGP_ATTR", "PREC_A_ATTR",
    "fusion_score_term", "predict_fusion_term",
    "fusion_score_term_pcw", "predict_fusion_term_pcw",
    "fusion_score_term_ckt", "fusion_score_term_ckt_min", "fusion_score_term_corr_only",
    "predict_fusion_term_ckt",
    "build_word_substrate", "native_predict", "native_predict_pcw", "native_predict_ckt",
    "native_confidence",
]
