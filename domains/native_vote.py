"""native_vote — the k-NN MEL-MAJORITY VOTE as a graph-resident native Rust Term.

The exemplar baseline (the ~83.5% bank: mcu_infer / formant_trajectory_dynamics.py:370,
perception_composition.py / articulatory_gamma.py) makes its DECISION with a Python
``Counter([w for _, w in ds[:KNN_K]]).most_common(1)[0][0]`` — sort the train exemplars by
DTW distance to the query, take the k nearest, majority-vote their words. The DTW distance
itself is owned transduction (mi.dtw over log-mel matrices, numpy) and STAYS Python (the
flagged boundary); but the DECISION over those distances — top-k selection + majority — is
COGNITION and must be a graph Term, not a Python ``Counter``.

THE AGENT'S COMPOSITION (its own reasoning: a Fold/set-threaded top-k, NO new primitive).
The k-nearest majority is expressed entirely from primitives already in the grammar
(Argmax, Count, Filter, Lt, Eq, And, Attr, NodesWhere — all verified in
runners/dsl/src/term.rs + jsonio.rs):

  rank(e)  = Count( MelExemplar e2 : e2.mel_dist < e.mel_dist )      # how many are nearer
  in_topk(e) = rank(e) < k                                           # e is among the k nearest
  votes(w) = Count( MelExemplar e : e.mel_word == w  AND  in_topk(e) )
  predict  = Argmax over { Concept : is_word == 1 } of votes(w)

i.e. the vote = the word with the most exemplars among the k nearest. rank-via-Count is the
set-based realisation of the top-k the agent reasoned (no Sort/TopK primitive needed — the
nearest-k membership is a COUNT predicate). The DTW distances are graph attrs the world
adapter writes per query (transduction); the SELECTION + MAJORITY + ARGMAX is the native
evaluator.

OWNERSHIP not byte-fidelity (memory: ozma_native_migration_is_ownership_not_fidelity): the
rank<k membership admits ALL exemplars tied at the k-th distance, whereas Python's
``sorted()[:k]`` slices exactly k and breaks ties by list order. On distinct float DTW
distances (the overwhelming norm) the two are identical; on an exact tie at the boundary the
native vote counts every tied exemplar (the principled choice — no arbitrary list-order
tiebreak). Faithful where faithful; the boundary divergence is the agent owning the decision.

DONKEY-CLEAN: no net, no .fit, no gradient, no sweep, no learned weight. The Term is
evaluated by substrate.evaluate (native Rust). The Python here is world-adapter glue ONLY:
it banks the train exemplars as graph nodes and writes each one's (owned, numpy) DTW distance
to the current query as a graph attr, then reads back the argmax word.
"""
from __future__ import annotations


WORD_ATTR = "is_word"          # candidate-word marker (Concept nodes)
MEL_WORD_ATTR = "mel_word"     # the train exemplar's digit label
MEL_DIST_ATTR = "mel_dist"     # owned DTW distance from this exemplar to the current query


# ---- Term constructors (raw-dict, mirroring native_fusion / native_cognition) ----

def _V(n):
    return {"type": "Var", "name": n}


def _Lit(v):
    return {"type": "Lit", "value": v}


def _Attr(node, k):
    return {"type": "Attr", "node": node, "key": k}


def _Lt(a, b):
    return {"type": "Lt", "a": a, "b": b}


def _Lte(a, b):
    return {"type": "Lte", "a": a, "b": b}


def _Eq(a, b):
    return {"type": "Eq", "a": a, "b": b}


def _And(items):
    return {"type": "And", "items": items}


def _Count(src):
    return {"type": "Count", "source": src}


def _Filter(src, var, pred):
    return {"type": "Filter", "source": src, "var_name": var, "predicate": pred}


def _Argmax(src, var, val):
    return {"type": "Argmax", "source": src, "var_name": var,
            "value": val, "default": None}


def _MinOver(src, var, val):
    return {"type": "MinOver", "source": src, "var_name": var,
            "value": val, "default": None}


def _Plus(items):
    return {"type": "Plus", "items": items}


def _Minus(a, b):
    return {"type": "Minus", "a": a, "b": b}


def _Times(items):
    return {"type": "Times", "items": items}


def _NodesWhere(t, k, v):
    return {"type": "NodesWhere", "node_type": t, "attr_key": k, "value": v}


def _exemplar_set():
    """Every banked MelExemplar node (mel_word == any). NodesWhere needs an attr filter; we
    mark each exemplar with mel_is == 1 so this is a clean type+attr selection."""
    return _NodesWhere("MelExemplar", "mel_is", _Lit(1.0))


def _word_set():
    """The candidate-word node set: every Concept with is_word == 1."""
    return _NodesWhere("Concept", WORD_ATTR, _Lit(1.0))


def _rank_term(e_var: str) -> dict:
    """rank(e) = Count( MelExemplar ej : ej.mel_dist < e.mel_dist ) — how many banked
    exemplars are strictly NEARER the query than e. A fresh inner var (ej) so it does not
    shadow the outer Filter var. (Var names are leading-underscore-free: the native env
    binding only resolves non-underscore-prefixed Var names.)"""
    return _Count(_Filter(
        _exemplar_set(), "ej",
        _Lt(_Attr(_V("ej"), MEL_DIST_ATTR), _Attr(_V(e_var), MEL_DIST_ATTR)),
    ))


def votes_term(k: int) -> dict:
    """votes(w) = Count( MelExemplar ei : ei.mel_word == w  AND  rank(ei) < k ). The number of
    exemplars among the k nearest whose word is the candidate w."""
    in_topk = _Lt(_rank_term("ei"), _Lit(int(k)))
    same_word = _Eq(_Attr(_V("ei"), MEL_WORD_ATTR), _Attr(_V("w"), "word_id"))
    return _Count(_Filter(
        _exemplar_set(), "ei",
        _And([same_word, in_topk]),
    ))


def _word_nearest_dist_term(k: int) -> dict:
    """min over THIS word's top-k exemplars of its DTW distance — the distance of the word's
    NEAREST exemplar among the k nearest (a big default for words with no top-k exemplar). This
    is the native realisation of Counter.most_common's tiebreak: among words with equal vote
    count, Python returns the word inserted FIRST into the Counter, and the Counter is filled by
    iterating the k nearest in ASCENDING distance — so the first-inserted (tie-winning) word is
    the one whose nearest top-k exemplar is closest. MinOver over the word's in-top-k exemplars
    reproduces exactly that."""
    in_topk = _Lt(_rank_term("em"), _Lit(int(k)))
    same_word = _Eq(_Attr(_V("em"), MEL_WORD_ATTR), _Attr(_V("w"), "word_id"))
    word_topk = _Filter(_exemplar_set(), "em", _And([same_word, in_topk]))
    # MinOver returns the default (1e9) when the word has no top-k exemplar (vote count 0).
    return {"type": "MinOver", "source": word_topk, "var_name": "em",
            "value": _Attr(_V("em"), MEL_DIST_ATTR), "default": _Lit(1e9)}


def vote_score_term(k: int) -> dict:
    """score(w) = BIG * votes(w) - nearest_topk_dist(w). The integer vote count dominates (BIG
    >> any bounded distance), so the argmax is the MAJORITY word exactly; ties in vote count are
    broken by the smaller nearest-top-k distance — the faithful native realisation of
    Counter.most_common's insertion-order (= ascending-distance) tiebreak. NO new primitive:
    Plus / Times / Minus / MinOver, all already in the grammar."""
    BIG = 1e6
    return _Minus(_Times([_Lit(BIG), votes_term(k)]), _word_nearest_dist_term(k))


def predict_vote_term(k: int) -> dict:
    """predict = Argmax over candidate words of vote_score(w). The whole k-NN majority DECISION
    as graph data — the SAME Argmax-of-score shape the other native Terms use, the score being
    the top-k vote count (with the nearest-distance tiebreak).

    NOTE: the rank-via-Count realisation is O(N^2) (a nested Count per exemplar). It is the
    purest set-native top-k and is used by the isolated validation; the production path uses the
    threshold variant below (predict_vote_term_thr), which is O(N) and identical on distinct
    distances — the k-th-nearest distance is a per-query scalar statistic over the OWNED DTW
    distances (the same transduction category as the tau scales / n-gram counts already computed
    in Python), passed as a Lit; the SELECTION + MAJORITY + ARGMAX stay native."""
    return _Argmax(_word_set(), "w", vote_score_term(k))


# ---- O(N) threshold variant (production path) ----

THR_ATTR = "knn_thr"   # the k-th-nearest DTW distance (a per-query scalar; written on a Cfg node)


def _votes_thr_term() -> dict:
    """votes(w) = Count( MelExemplar e : e.mel_word == w  AND  e.mel_dist <= knn_thr ). The
    k-NN membership is the single threshold compare (e is among the k nearest iff its distance
    is <= the k-th-nearest distance) — O(1) per exemplar, no nested rank. The threshold is a
    Var('thr') bound at eval time to the per-query k-th-nearest distance (an owned scalar)."""
    in_topk = _Lte(_Attr(_V("ei"), MEL_DIST_ATTR), _V("thr"))
    same_word = _Eq(_Attr(_V("ei"), MEL_WORD_ATTR), _Attr(_V("w"), "word_id"))
    return _Count(_Filter(_exemplar_set(), "ei", _And([same_word, in_topk])))


def _word_nearest_dist_thr_term() -> dict:
    """min over THIS word's <=thr exemplars of its DTW distance — the nearest-distance tiebreak
    (the native realisation of Counter.most_common's ascending-distance insertion order)."""
    in_topk = _Lte(_Attr(_V("em"), MEL_DIST_ATTR), _V("thr"))
    same_word = _Eq(_Attr(_V("em"), MEL_WORD_ATTR), _Attr(_V("w"), "word_id"))
    word_topk = _Filter(_exemplar_set(), "em", _And([same_word, in_topk]))
    return {"type": "MinOver", "source": word_topk, "var_name": "em",
            "value": _Attr(_V("em"), MEL_DIST_ATTR), "default": _Lit(1e9)}


def vote_score_thr_term() -> dict:
    """score(w) = BIG*votes(w) - nearest_dist(w), with the O(N) threshold membership."""
    BIG = 1e6
    return _Minus(_Times([_Lit(BIG), _votes_thr_term()]), _word_nearest_dist_thr_term())


def predict_vote_thr_term() -> dict:
    """predict = Argmax over candidate words of the threshold vote_score. Var('thr') is the
    per-query k-th-nearest distance (owned scalar, bound at eval time)."""
    return _Argmax(_word_set(), "w", vote_score_thr_term())


# ---------------------------------------------------------------------------
# World-adapter glue: bank the train exemplars as graph nodes, write each one's (owned, numpy)
# DTW distance to the current query as a graph attr, evaluate the native Term, read back the
# argmax word. NO decision here — the decision is the Term.
# ---------------------------------------------------------------------------

def build_vote_substrate(Substrate, words, bank_words):
    """A Substrate with one Concept per candidate word (is_word==1, word_id == the digit) and
    one MelExemplar node per banked train exemplar (mel_is==1, mel_word == its digit). The DTW
    distance attr is written per query by feed_distances. Returns
    (substrate, {word: word_node}, [exemplar_node, ...]).

    word_id / mel_word are string-valued graph attrs the native Eq compares directly (no float
    coding needed — Eq compares Value::Str)."""
    s = Substrate()
    word_nodes = {}
    for w in words:
        nid = s.add_node("Concept", {"name": w})
        s.set_attr(nid, WORD_ATTR, 1.0)
        s.set_attr(nid, "word_id", w)
        word_nodes[w] = nid
    ex_nodes = []
    for w in bank_words:
        eid = s.add_node("MelExemplar", {})
        s.set_attr(eid, "mel_is", 1.0)
        s.set_attr(eid, MEL_WORD_ATTR, w)
        s.set_attr(eid, MEL_DIST_ATTR, 0.0)
        ex_nodes.append(eid)
    return s, word_nodes, ex_nodes


def native_vote(s, ex_nodes, dists, k, Pred):
    """Write the owned per-exemplar DTW distances (a list aligned with ex_nodes) onto the
    MelExemplar nodes and return the native-Term k-NN majority word — the O(N) THRESHOLD path:
    the k-th-nearest distance is the one owned scalar statistic over the DTW distances (the same
    transduction category as the tau medians / n-gram counts), bound as Var('thr'); the
    SELECTION (<=thr membership), MAJORITY (Count), and DECISION (Argmax) are the native Term.
    `Pred` is the evaluable-Term wrapper (formant_trajectory_dynamics._P / _Pred)."""
    for eid, d in zip(ex_nodes, dists):
        s.set_attr(eid, MEL_DIST_ATTR, float(d))
    # k-th-nearest distance (owned scalar over the owned DTW distances; transduction).
    kk = min(int(k), len(dists))
    thr = sorted(dists)[kk - 1] if kk >= 1 else float("inf")
    pick = s.evaluate(Pred(predict_vote_thr_term()), {"thr": float(thr)})
    return s.node(pick)["attrs"]["name"]


def native_vote_exact(s, ex_nodes, dists, k, Pred):
    """The PURE set-native rank-via-Count vote (O(N^2)); used by the isolated validation. Same
    decision as native_vote on distinct distances."""
    for eid, d in zip(ex_nodes, dists):
        s.set_attr(eid, MEL_DIST_ATTR, float(d))
    pick = s.evaluate(Pred(predict_vote_term(k)), {})
    return s.node(pick)["attrs"]["name"]


__all__ = [
    "WORD_ATTR", "MEL_WORD_ATTR", "MEL_DIST_ATTR",
    "votes_term", "predict_vote_term",
    "build_vote_substrate", "native_vote",
]
