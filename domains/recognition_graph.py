"""recognition_graph — recognition AS A GRAPH TERM-TREE, owned by the agent.

The recognition decision — which word a sign is — is no longer Python (predict_one's
Naive-Bayes + blend + argmax). It is a native Term-tree the agent evaluates and,
crucially, can MODIFY: per-feature weights are graph attrs it adjusts.

    score(sign, word) = Σ  over  f ∈ ( exhibits(sign) ∩ signature(word) )  of  weight_f
    predict(sign)     = the word concept maximising score        (Argmax over words)

Built entirely from the substrate's OWN DSL — Sum, Intersect, Neighbours, Argmax,
Attr — so the agent can do-contrast a feature's weight, reweight it, or recompose
the scorer the same way it reweights any predicate today. This moves recognition
INTO the agent's reality, per the architecture rule (a decision is a Rule/Term, not
Python). The agent could not "work out" the recogniser before because it was a
Python function outside the graph; now the recogniser is graph data it owns.

Verified (synthetic): scores the right word and the weight attrs change the scores.
See [[ozma_concepts_in_gamma]] / [[ozma_entity_not_program]] /
[[ozma_meta_abilities_are_leverage]].
"""
from __future__ import annotations

WEIGHT_KEY = "rec_weight"          # per-feature recognition weight (the agent's lever)
SIG_EDGE = "has_phonological_marker"
WORD_ATTR = "is_word"


class _Pred:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def _V(n): return {"type": "Var", "name": n}
def _Lit(v): return {"type": "Lit", "value": v}
def _Attr(node, k): return {"type": "Attr", "node": node, "key": k}
def _Nb(node, e): return {"type": "Neighbours", "node": node, "edge_type": e,
                          "any_type": False}
def _Inter(a, b): return {"type": "Intersect", "a": a, "b": b}
def _Sum(src, var, val): return {"type": "Sum", "source": src, "var_name": var,
                                 "value": val}
def _Argmax(src, var, val): return {"type": "Argmax", "source": src,
                                    "var_name": var, "value": val, "default": None}
def _NodesWhere(t, k, v): return {"type": "NodesWhere", "node_type": t,
                                  "attr_key": k, "value": v}


def score_term(weight_key: str = WEIGHT_KEY) -> dict:
    """score(s, w) = Σ_{f ∈ exhibits(s) ∩ signature(w)} weight_f — a graph Term-tree.
    Uses the sign var `s` (from env) and the word var `w` (bound by the Argmax)."""
    return _Sum(_Inter(_Nb(_V("s"), "exhibits"), _Nb(_V("w"), SIG_EDGE)),
                "f", _Attr(_V("f"), weight_key))


def predict_term(weight_key: str = WEIGHT_KEY) -> dict:
    """predict(s) = argmax over the word concepts of score(s, w) — a graph Term-tree.
    The whole recognition DECISION, as data the agent owns."""
    return _Argmax(_NodesWhere("Concept", WORD_ATTR, _Lit(1.0)), "w",
                   score_term(weight_key))


# ---- analysis-by-synthesis (AxS): recognition by INVERTING the forward model --
#
# The decision keeps the SAME argmax-of-score shape as predict_term; only the
# SCORE sub-term changes — from "Σ feature weights" (bottom-up, instance↔instance)
# to "-synth_error(s, w)" (analysis-by-synthesis, instance↔canonical-synthesis).
#
#   synth_error(s, w) = DTW( features(s) , features(speak(w | voice(s))) )
#   predict_axs(s)    = argmax_w  -synth_error(s, w)
#
# This is the missing STRUCTURE (Stevens-Halle AxS / motor theory / Hickok-Poeppel
# dorsal stream): recognise by re-generating each candidate in the HEARD voice and
# picking the minimum prediction error, so speaker/coarticulation nuisance is
# absorbed into the forward model and the residual is phonetic identity.
#
# SPLIT (honest, per the task): synthesis stays at the I/O boundary (the adapter
# calls speak() in voice(s), front-ends it, and writes the resulting trajectory
# onto the candidate word as an attr). The DTW kernel is the new Rust Term
# (DtwTo). The DECISION — the argmax over candidates of -DtwTo — is composed and
# evaluated in the GRAPH. So: synthesis at the boundary, distance + decision in
# the graph.

SIGN_FEAT_ATTR = "axs_heard_feat"      # heard trajectory written on the sign
WORD_FEAT_ATTR = "axs_synth_feat"      # candidate synthesis written on the word


def _Neg(a): return {"type": "Neg", "arg": a}
def _DtwTo(a, b): return {"type": "DtwTo", "a": a, "b": b}
def _PointSetDist(a, b): return {"type": "PointSetDist", "a": a, "b": b}
def _DeformDist(a, b): return {"type": "DeformDist", "a": a, "b": b}
def _SmoothDeformDist(a, b): return {"type": "SmoothDeformDist", "a": a, "b": b}
def _TpsDeformDist(a, b): return {"type": "TpsDeformDist", "a": a, "b": b}
def _ShapeContextDist(a, b): return {"type": "ShapeContextDist", "a": a, "b": b}
def _ScTpsDist(a, b): return {"type": "ScTpsDist", "a": a, "b": b}


def synth_error_term(sign_attr: str = SIGN_FEAT_ATTR,
                     word_attr: str = WORD_FEAT_ATTR) -> dict:
    """synth_error(s, w) = DtwTo(features(s), synth_features(w)) — a graph Term.
    Both buffers are graph attrs (frames x bands tuples) the adapter populated:
    features(s) on the sign `s`, the candidate's synthesis-in-voice(s) on word `w`.
    The DTW itself is the new Rust primitive; this is just the composition."""
    return _DtwTo(_Attr(_V("s"), sign_attr), _Attr(_V("w"), word_attr))


def predict_synth_term(sign_attr: str = SIGN_FEAT_ATTR,
                       word_attr: str = WORD_FEAT_ATTR) -> dict:
    """predict_axs(s) = argmax over candidate words of -synth_error(s, w).
    Same argmax shape as predict_term; the SCORE is now -DtwTo(...) — the whole
    analysis-by-synthesis DECISION as graph data the agent owns."""
    return _Argmax(_NodesWhere("Concept", WORD_ATTR, _Lit(1.0)), "w",
                   _Neg(synth_error_term(sign_attr, word_attr)))


def pointset_error_term(sign_attr: str = SIGN_FEAT_ATTR,
                        word_attr: str = WORD_FEAT_ATTR) -> dict:
    """pointset_error(s, w) = PointSetDist(features(s), synth_features(w)) — a graph Term.
    The ORDER-INVARIANT analogue of synth_error_term: the same two trajectory buffers, but
    matched as point SETS (symmetric Modified Hausdorff) so pen-ORDER / stroke-count variability
    between writers does not penalise a true match. The set distance is the new Rust primitive."""
    return _PointSetDist(_Attr(_V("s"), sign_attr), _Attr(_V("w"), word_attr))


def predict_pointset_term(sign_attr: str = SIGN_FEAT_ATTR,
                          word_attr: str = WORD_FEAT_ATTR) -> dict:
    """predict_ps(s) = argmax over candidate words of -pointset_error(s, w). Same argmax shape
    as predict_synth_term; the SCORE is now -PointSetDist (an order-invariant shape distance, so
    argmax of its negation, exactly like DtwTo). The whole order-invariant recognition DECISION
    as graph data the agent owns."""
    return _Argmax(_NodesWhere("Concept", WORD_ATTR, _Lit(1.0)), "w",
                   _Neg(pointset_error_term(sign_attr, word_attr)))


CONTEXT_PRIMED_ATTR = "context_primed"   # top-down support a candidate gets from the reading context
LEXWORD_ATTR = "is_lexword"              # a lexicon word (a known symbol sequence)
SLOT_EDGE = "has_slot"                   # LexWord --has_slot--> Slot (pos + template feature)
POS_ATTR = "pos"                         # position index, on both the written marks and the word slots


def _Pick(src): return {"type": "Pick", "source": src}


def word_error_term(slot_edge: str = SLOT_EDGE, pos_attr: str = POS_ATTR,
                    sign_attr: str = SIGN_FEAT_ATTR, slot_feat: str = WORD_FEAT_ATTR) -> dict:
    """word_error(W) = sum over W's slots s of PointSetDist( the written mark AT position s.pos , s's
    template form ). The whole-word visual fit: every position scored against the word's expected symbol,
    the mark at each position fetched by a position join (NodesWhere Mark pos == slot pos). The lexicon
    word as a single recognition unit — the join is in the graph, not the host."""
    mark_at = _Pick(_NodesWhere("Mark", pos_attr, _Attr(_V("s"), pos_attr)))
    return _Sum(_Nbrs(_V("W"), slot_edge), "s",
                _PointSetDist(_Attr(mark_at, sign_attr), _Attr(_V("s"), slot_feat)))


def predict_word_term(slot_edge: str = SLOT_EDGE, pos_attr: str = POS_ATTR,
                      sign_attr: str = SIGN_FEAT_ATTR, slot_feat: str = WORD_FEAT_ATTR) -> dict:
    """predict_word(written) = argmax over LEXICON words of -word_error(W). The whole-word lexical decode:
    the known word that best explains ALL the written positions wins, and so dictates each letter — even
    individually-ambiguous ones (the word-superiority effect at scale). Same argmax shape as the per-symbol
    recogniser, but the unit is a lexicon WORD (a sequence), the score a sum over its positions. The
    lexicon is graph data (LexWord/Slot nodes); the decode is this held Term, no new Rust."""
    return _Argmax(_NodesWhere("LexWord", LEXWORD_ATTR, _Lit(1.0)), "W",
                   _Neg(word_error_term(slot_edge, pos_attr, sign_attr, slot_feat)))


def predict_context_term(lam: float = 0.0, sign_attr: str = SIGN_FEAT_ATTR,
                         word_attr: str = WORD_FEAT_ATTR,
                         primed_attr: str = CONTEXT_PRIMED_ATTR) -> dict:
    """predict_in_context(s) = argmax over candidate words of [ -pointset_error(s, w) + lam * primed(w) ].
    The Interactive-Activation reading decision: the per-symbol VISUAL score plus a TOP-DOWN context
    term — lam * the candidate's `context_primed` (spread onto it by the reading context, see the
    prime_successors Rule). lam=0 is pure bottom-up vision; lam>0 lets a primed-but-visually-second
    candidate win, so context disambiguates an ambiguous symbol (the word-superiority effect). The
    priming is a Rule; this Term just composes the held visual score with the primed support."""
    score = _Plus([_Neg(pointset_error_term(sign_attr, word_attr)),
                   _Times([_Lit(lam), _Attr(_V("w"), primed_attr)])])
    return _Argmax(_NodesWhere("Concept", WORD_ATTR, _Lit(1.0)), "w", score)


def deform_error_term(sign_attr: str = SIGN_FEAT_ATTR,
                      word_attr: str = WORD_FEAT_ATTR) -> dict:
    """deform_error(s, w) = DeformDist(features(s), synth_features(w)) — a graph Term. The BPL
    TOKEN-MODEL analogue: fit the candidate's written form to the mark with a small affine
    deformation and score the order-invariant residual PLUS a penalty on the deformation's
    non-rigidity (allowed but costed). The deformable fit is the new Rust primitive."""
    return _DeformDist(_Attr(_V("s"), sign_attr), _Attr(_V("w"), word_attr))


def predict_deform_term(sign_attr: str = SIGN_FEAT_ATTR,
                        word_attr: str = WORD_FEAT_ATTR) -> dict:
    """predict_deform(s) = argmax over candidate words of -deform_error(s, w). Same argmax shape as
    predict_synth_term; the SCORE is now -DeformDist (a deformable, order-invariant distance with a
    generative token penalty). The whole BPL-token-style recognition DECISION as graph data."""
    return _Argmax(_NodesWhere("Concept", WORD_ATTR, _Lit(1.0)), "w",
                   _Neg(deform_error_term(sign_attr, word_attr)))


# ---------------------------------------------------------------------------
# PART-NESTED recognition — the agent's HIERARCHICAL composition. Its shape
# faculty files part-composed character matching under hierarchical_invariance_
# buildup (NOT the flat prediction_minus_observation of the whole-figure match),
# so the decision must NEST: a character is a composition of STROKE parts, and
# the character score composes per-stroke matches over a part correspondence —
# exactly the way speech nests sub-unit models within words. Built by NESTING the
# agent's held PointSetDist stroke-matcher (one primitive) under graph reductions
# (Sum / MinOver / Neighbours) it already owns — no new primitive, the richness is
# in the composition. Both the candidate word `w` and the sign `s` carry their
# strokes as Stroke parts (w --STROKE_EDGE--> Stroke{PTS_ATTR}) in a SHARED
# normalised frame, so a stroke's POSITION is part of its point set and the match
# respects stroke layout (the relations) for free.
# ---------------------------------------------------------------------------

STROKE_EDGE = "has_stroke"
PTS_ATTR = "stroke_pts"


def _Nbrs(node, e): return {"type": "Neighbours", "node": node, "edge_type": e, "any_type": False}
def _MinOver(src, var, val): return {"type": "MinOver", "source": src, "var_name": var,
                                     "value": val, "default": None}
def _Count(src): return {"type": "Count", "source": src}
def _Div(a, b): return {"type": "Div", "a": a, "b": b}
def _Plus(items): return {"type": "Plus", "items": items}


def _directed_part_dist(from_var: str, to_var: str, stroke_edge: str, pts_attr: str) -> dict:
    """mean over `from`'s strokes of ( min over `to`'s strokes of PointSetDist(stroke, stroke) ) —
    the directed part-correspondence distance: every part of `from` is explained by its best-
    matching part of `to`. Order- AND count-tolerant (a min over all `to` parts, averaged)."""
    inner = _MinOver(_Nbrs(_V(to_var), stroke_edge), "sq",
                     _PointSetDist(_Attr(_V("sc"), pts_attr), _Attr(_V("sq"), pts_attr)))
    total = _Sum(_Nbrs(_V(from_var), stroke_edge), "sc", inner)
    return _Div(total, _Count(_Nbrs(_V(from_var), stroke_edge)))


def partnested_error_term(stroke_edge: str = STROKE_EDGE, pts_attr: str = PTS_ATTR) -> dict:
    """part_error(s, w) = directed(w->s) + directed(s->w) — the SYMMETRIC part-correspondence
    distance between the sign `s` and candidate word `w`, each a composition of Stroke parts. The
    hierarchical (nested) analogue of pointset_error_term: matching is at the PART level and the
    character score composes the part matches. Built from held Terms; the only kernel is PointSetDist."""
    d_sw = _directed_part_dist("w", "s", stroke_edge, pts_attr)
    d_ws = _directed_part_dist("s", "w", stroke_edge, pts_attr)
    return _Plus([d_sw, d_ws])


def predict_partnested_term(stroke_edge: str = STROKE_EDGE, pts_attr: str = PTS_ATTR) -> dict:
    """predict_part(s) = argmax over candidate words of -part_error(s, w). Same argmax shape as the
    flat recognisers; the SCORE is the nested part-correspondence distance — the agent's
    hierarchical composition (character = composed strokes), the genuine generative-richness step
    that graph nesting (not a monolithic kernel) provides."""
    return _Argmax(_NodesWhere("Concept", WORD_ATTR, _Lit(1.0)), "w",
                   _Neg(partnested_error_term(stroke_edge, pts_attr)))


# ---------------------------------------------------------------------------
# GENERATIVE RE-RENDER — the generative-program faculty's harder piece, graph-native. BPL recognises by
# treating the exemplar as a generative PROGRAM and RE-RENDERING it (re-deforming its parts) to explain
# the query, scoring fit + the token-level deformation cost. Here that is the part correspondence with
# the per-part distance = SmoothDeformDist (deform the exemplar's part onto the query's part; the
# deformation cost in SmoothDeformDist IS the token prior). Composes the held SmoothDeformDist primitive
# inside the part-nested graph reduction — NO new Rust; the richness is the composition.
# ---------------------------------------------------------------------------

def _directed_render_part(from_var: str, to_var: str, edge: str, pts_attr: str) -> dict:
    """mean over `from`'s parts of ( min over `to`'s parts of SmoothDeformDist(part, part) ) — each
    part of `from` is RE-RENDERED (smoothly deformed) onto its best-matching part of `to`."""
    inner = _MinOver(_Nbrs(_V(to_var), edge), "sq",
                     _SmoothDeformDist(_Attr(_V("sc"), pts_attr), _Attr(_V("sq"), pts_attr)))
    return _Div(_Sum(_Nbrs(_V(from_var), edge), "sc", inner), _Count(_Nbrs(_V(from_var), edge)))


def generative_render_error_term(edge: str = STROKE_EDGE, pts_attr: str = PTS_ATTR) -> dict:
    """render_error(s, w) = directed(w->s) + directed(s->w) with each part RE-RENDERED by deformation —
    the symmetric per-part generative re-render distance (the exemplar's program re-deformed to the
    query and back). The deformation cost per part is the token prior."""
    return _Plus([_directed_render_part("w", "s", edge, pts_attr),
                  _directed_render_part("s", "w", edge, pts_attr)])


def predict_generative_render_term(edge: str = STROKE_EDGE, pts_attr: str = PTS_ATTR) -> dict:
    """predict_render(s) = argmax over candidate words of -generative_render_error(s, w) — recognition
    by re-rendering each candidate's program (its parts, smoothly re-deformed) to explain the mark."""
    return _Argmax(_NodesWhere("Concept", WORD_ATTR, _Lit(1.0)), "w",
                   _Neg(generative_render_error_term(edge, pts_attr)))


def predict_smooth_render_sc_term(render_w: float = 0.25, sc_w: float = 1.6,
                                  edge: str = STROKE_EDGE, pts_attr: str = PTS_ATTR) -> dict:
    """The fusion with the GENERATIVE RE-RENDER part cue replacing the rigid part cue: smooth whole +
    render_w * per-part-re-render + sc_w * shape-context. argmax over candidates of -error."""
    err = _Plus([smoothdeform_error_term(),
                 _Times([_Lit(render_w), generative_render_error_term(edge, pts_attr)]),
                 _Times([_Lit(sc_w), shapecontext_error_term()])])
    return _Argmax(_NodesWhere("Concept", WORD_ATTR, _Lit(1.0)), "w", _Neg(err))


# ---------------------------------------------------------------------------
# MARGINALISING JOINT INFERENCE — the move the agent's reasoning + every failed single piece pointed
# to. The PARSE is uncertain (writer-inconsistent); rather than COMMIT to one (parse inference, the MAP
# parse), each drawing carries K PARSE HYPOTHESES (parts at K thresholds, drawing --has_parse--> ParseHyp
# --has_stroke--> Stroke), and the part distance MARGINALISES over the parse-pairings via a soft-min
# (log-sum-exp): softmin_b(d) = -1/b * log( sum over (query-parse, cand-parse) of exp(-b * partdist) ).
# As b->inf this is the min (commit to the best parse); a finite b AVERAGES over plausible parses — the
# Bayesian marginalisation. Graph-native: composes the held part distance under Sum/Exp/Log Terms.
# ---------------------------------------------------------------------------

PARSE_EDGE = "has_parse"


def _Exp(a): return {"type": "Exp", "arg": a}
def _Log(a): return {"type": "Log", "arg": a}


def _parse_pair_dist(qh_var: str, ch_var: str, edge: str, pts_attr: str) -> dict:
    """The symmetric part-correspondence distance between two PARSE HYPOTHESIS nodes (their has_stroke
    parts) — partdist for one (query-parse, candidate-parse) pairing."""
    return _Plus([_directed_part_dist(qh_var, ch_var, edge, pts_attr),
                  _directed_part_dist(ch_var, qh_var, edge, pts_attr)])


def _soft_directed_part_dist(from_var: str, to_var: str, stroke_edge: str, pts_attr: str,
                             beta_corr: float) -> dict:
    """As _directed_part_dist, but the part CORRESPONDENCE is MARGINALISED, not committed: every part of
    `from` is explained by a SOFT-MIN over `to`'s parts (-1/beta_corr * log sum exp(-beta_corr * dist))
    instead of the hard min. beta_corr -> inf recovers the hard min (commit to the best part-pairing);
    finite beta_corr AVERAGES over the uncertain correspondence — the Bayesian token-to-token assignment."""
    soft = _Neg(_Div(_Log(_Sum(_Nbrs(_V(to_var), stroke_edge), "sq",
                               _Exp(_Times([_Lit(-beta_corr),
                                            _PointSetDist(_Attr(_V("sc"), pts_attr), _Attr(_V("sq"), pts_attr))])))),
                     _Lit(beta_corr)))
    total = _Sum(_Nbrs(_V(from_var), stroke_edge), "sc", soft)
    return _Div(total, _Count(_Nbrs(_V(from_var), stroke_edge)))


def _joint_pair_dist(qh_var: str, ch_var: str, edge: str, pts_attr: str, beta_corr: float) -> dict:
    """Symmetric part distance for one parse-pairing with the CORRESPONDENCE marginalised (soft both ways)."""
    return _Plus([_soft_directed_part_dist(qh_var, ch_var, edge, pts_attr, beta_corr),
                  _soft_directed_part_dist(ch_var, qh_var, edge, pts_attr, beta_corr)])


def _MahalLeaf(a, b): return {"type": "MahalLeaf", "a": a, "b": b}
def _MahalFull(a, b): return {"type": "MahalFull", "a": a, "b": b}
def _DeformGen(a, b): return {"type": "DeformGen", "a": a, "b": b}

NORM_PTS_ATTR = "norm_pts"        # a leaf's normalised shape (the MahalLeaf observation)
PRIM_MODEL_ATTR = "prim_model"    # a leaf's learned primitive model [mean ++ inv_std] (the generative leaf)
DEFGEN_MODEL_ATTR = "defgen_model"  # [part-shape mean ++ deformation modes ++ inv_var] (the agent's generative leaf)
TYPEGEN_MODEL_ATTR = "typegen_model"  # [support pose-canonical shape ++ type FULL precision] (the full-BPL token model)
POSE_PTS_ATTR = "pose_pts"            # a part's POSE-CANONICAL shape (position removed; for the type token model)


def _recursive_leaf(from_var: str, to_var: str, pts_attr: str, leaf: str) -> dict:
    """The recursion's BASE CASE — the shape-match primitive. 'pointset' = the order-invariant geometric
    PointSetDist (fixed); 'mahal' = the GENERATIVE LEAF: the observed leaf (`from`'s normalised shape)
    scored under `to`'s learned per-primitive Gaussian (MahalLeaf over [mean ++ inv_std]) — BPL's token
    model AS the leaf, the agent's mapped residual. The layout is preserved by the recursion above it."""
    if leaf == "mahal":
        return _MahalLeaf(_Attr(_V(from_var), pts_attr), _Attr(_V(to_var), PRIM_MODEL_ATTR))
    if leaf == "mahalfull":
        return _MahalFull(_Attr(_V(from_var), pts_attr), _Attr(_V(to_var), PRIM_MODEL_ATTR))
    if leaf == "relfeat":                                        # a part's RELATION SIGNATURE (junction structure)
        return _SqEuclid(_Attr(_V(from_var), pts_attr), _Attr(_V(to_var), pts_attr))
    if leaf == "atomfeat":                                       # a part's LEARNED tiny-feature-atom descriptor:
        # compare two parts by the squared distance of their atom-firing descriptors (which of the agent's
        # tiny sparse_dict_learn detectors fire ON that part). The STRUCTURE (which part stands where) is the
        # recursion above; only the base-case similarity becomes the learned feature. Descriptors are
        # L2-normalised, so SqEuclid = 2(1 - cos) is monotone in cosine dissimilarity. The recursion's
        # soft-min wants a DISTANCE (smaller = more alike), which is exactly this.
        return _SqEuclid(_Attr(_V(from_var), pts_attr), _Attr(_V(to_var), pts_attr))
    if leaf.startswith("atomjoint"):                             # JOINT learned-feature leaf: atom descriptor +
        lam = float(leaf.split(":")[1]) if ":" in leaf else 0.3  # lam * centroid distance, so the part LAYOUT
        return _Plus([_SqEuclid(_Attr(_V(from_var), pts_attr), _Attr(_V(to_var), pts_attr)),  # (relation) rides the
                      _Times([_Lit(lam), _SqEuclid(_Attr(_V(from_var), "centroid"), _Attr(_V(to_var), "centroid"))])])  # same correspondence
    if leaf == "defgen":                                         # the agent-AUTHORED generative deformable leaf:
        return _DeformGen(_Attr(_V(from_var), pts_attr), _Attr(_V(to_var), DEFGEN_MODEL_ATTR))
    if leaf == "defgenmarg":                                     # the agent's deformation-MARGINAL leaf (Occam):
        return {"type": "DeformGenMarginal", "a": _Attr(_V(from_var), pts_attr), "b": _Attr(_V(to_var), DEFGEN_MODEL_ATTR)}
    if leaf.startswith("factored"):                              # Phase 3: ARRANGEMENT (position) carries identity,
        ps = leaf.split(":"); wp = float(ps[1]) if len(ps) > 1 else 1.0; ws = float(ps[2]) if len(ps) > 2 else 0.3
        return _Plus([_Times([_Lit(wp), _SqEuclid(_Attr(_V(from_var), "centroid"), _Attr(_V(to_var), "centroid"))]),
                      _Times([_Lit(ws), _DeformGen(_Attr(_V(from_var), pts_attr), _Attr(_V(to_var), DEFGEN_MODEL_ATTR))])])
    if leaf.startswith("joint"):                                 # JOINT leaf: shape + lambda * relation, ONE part,
        lam = float(leaf.split(":")[1]) if ":" in leaf else 0.3  # so the relation rides the SAME parse + correspondence
        return _Plus([_PointSetDist(_Attr(_V(from_var), pts_attr), _Attr(_V(to_var), pts_attr)),
                      _Times([_Lit(lam), _SqEuclid(_Attr(_V(from_var), REL_FEAT_ATTR), _Attr(_V(to_var), REL_FEAT_ATTR))])])
    if leaf.startswith("typegen"):
        # FULL-BPL token-model leaf: the SUPPORT part is assigned a discrete library TYPE (identity); the
        # query's POSE-CANONICAL shape is scored under that type's LEARNED FULL-COVARIANCE Gaussian, centred
        # on the SUPPORT's pose-canonical shape (the exemplar) — re-deforming the support to the query at a
        # cost set by the type's learned deformation covariance (correlated modes are cheap). To this we add
        # lam * the squared POSITION distance, so the part LAYOUT (the relation) rides the SAME correspondence
        # — the JOINT inference. Identity lives in the discrete type + position; deformation is free along the
        # type's covariance. `from`/`to` carry TYPEGEN_MODEL_ATTR = [support_pose_shape ++ type_precision] on
        # the candidate side and POSE_PTS_ATTR (the pose-canonical query shape) + "centroid" on both.
        parts = leaf.split(":"); lam = float(parts[1]) if len(parts) > 1 else 1.0
        scale = float(parts[2]) if len(parts) > 2 else 1.0      # divides the Mahalanobis shape term to the
        nllw = float(parts[3]) if len(parts) > 3 else 0.0       # weight on the type's NORMALISER (logdet/2 attr)
        sh = _MahalFull(_Attr(_V(from_var), POSE_PTS_ATTR), _Attr(_V(to_var), TYPEGEN_MODEL_ATTR))  # PointSet scale
        shape = _Div(sh, _Lit(scale)) if scale != 1.0 else sh   # so the soft-min temperature stays well-conditioned
        pos = _SqEuclid(_Attr(_V(from_var), "centroid"), _Attr(_V(to_var), "centroid"))
        relw = float(parts[4]) if len(parts) > 4 else 0.0       # weight on the LEARNED relation-grammar signature
        items = [shape, _Times([_Lit(lam), pos])]
        if nllw != 0.0:                                          # the proper Gaussian log-likelihood normaliser:
            items.append(_Times([_Lit(nllw), _Attr(_V(to_var), "type_nll")]))  # tight, specific types preferred
        if relw != 0.0:                                          # PIECE 2: the part's connectivity ROLE under the
            items.append(_Times([_Lit(relw),                    # learned relation grammar (soft membership vector),
                                  _SqEuclid(_Attr(_V(from_var), "rel_sig"), _Attr(_V(to_var), "rel_sig"))]))  # joint
        return _Plus(items)
    return _PointSetDist(_Attr(_V(from_var), pts_attr), _Attr(_V(to_var), pts_attr))


def _recursive_directed(from_var: str, to_var: str, edges, pts_attr: str, beta: float, lvl: int = 0,
                        leaf: str = "pointset") -> dict:
    """The GENERIC recursive operator (graph-native, unrolled over `edges`). At a leaf (no edges left) it is
    the shape-match primitive (PointSetDist, or the learned generative MahalLeaf). At an internal level it
    MARGINALISES the part correspondence: mean over `from`'s children (along edges[0]) of a SOFT-MIN over
    `to`'s children of the SAME operator one level down — recursing on the parts, bottoming out at the leaf.
    One operator, pattern-matching at level N, descending the decomposition; domain-free in `edges` + leaf."""
    if not edges:
        return _recursive_leaf(from_var, to_var, pts_attr, leaf)
    e = edges[0]
    fc, tc = f"rf{lvl}", f"rt{lvl}"                              # unique child vars per recursion level
    inner = _recursive_directed(fc, tc, edges[1:], pts_attr, beta, lvl + 1, leaf)
    soft = _Neg(_Div(_Log(_Sum(_Nbrs(_V(to_var), e), tc, _Exp(_Times([_Lit(-beta), inner])))), _Lit(beta)))
    return _Div(_Sum(_Nbrs(_V(from_var), e), fc, soft), _Count(_Nbrs(_V(from_var), e)))


def _recursive_pair(qh_var: str, ch_var: str, edges, pts_attr: str, beta: float, leaf: str = "pointset") -> dict:
    """Symmetric recursive part distance between two parse-hypothesis subtrees."""
    return _Plus([_recursive_directed(qh_var, ch_var, edges, pts_attr, beta, 0, leaf),
                  _recursive_directed(ch_var, qh_var, edges, pts_attr, beta, 100, leaf)])


def recursive_error_term(edges=("has_stroke", "has_substroke"), beta: float = 2.0, beta_parse: float = 2.0,
                         parse_edge: str = PARSE_EDGE, pts_attr: str = PTS_ATTR, leaf: str = "pointset") -> dict:
    """RECURSIVE recognition (graph-native): marginalise over the parse hypotheses (outer soft-min), and
    inside each pairing run the GENERIC recursive operator down the decomposition `edges` — the same
    soft-min correspondence at every level, bottoming out at the leaf (`pointset` fixed geometric, or
    `mahal` the learned generative primitive likelihood). Composes held Terms, no new Rust beyond MahalLeaf."""
    inner = _Sum(_Nbrs(_V("s"), parse_edge), "qh",
                 _Sum(_Nbrs(_V("w"), parse_edge), "ch",
                      _Exp(_Times([_Lit(-beta_parse), _recursive_pair("qh", "ch", list(edges), pts_attr, beta, leaf)]))))
    return _Neg(_Div(_Log(inner), _Lit(beta_parse)))


def predict_recursive_sc_term(part_w: float = 0.25, sc_w: float = 1.6, edges=("has_stroke", "has_substroke"),
                              beta: float = 2.0, beta_parse: float = 2.0, parse_edge: str = PARSE_EDGE,
                              pts_attr: str = PTS_ATTR, leaf: str = "pointset") -> dict:
    """The agent's authored program with the part cue replaced by the RECURSIVE operator: smooth whole +
    part_w * recursive(parse + parts + ...; leaf = pointset or the learned generative mahal) + sc_w * SC."""
    err = _Plus([smoothdeform_error_term(),
                 _Times([_Lit(part_w), recursive_error_term(edges, beta, beta_parse, parse_edge, pts_attr, leaf)]),
                 _Times([_Lit(sc_w), shapecontext_error_term()])])
    return _Argmax(_NodesWhere("Concept", WORD_ATTR, _Lit(1.0)), "w", _Neg(err))


REL_PARSE_EDGE = "has_relhyp"     # character -> relation HYPOTHESIS (junction structure at one threshold)
REL_PART_EDGE = "has_relpart"     # relation hypothesis -> its parts (each with a relation signature)
REL_FEAT_ATTR = "rel_feat"        # a part's junction signature, FLAT (the SqEuclid relfeat observation)
REL_FEAT_N_ATTR = "rel_feat_n"    # the same signature NESTED as endpoint-frames (the mahal_leaf observation)


def predict_recursive_rel_term(part_w: float = 0.25, sc_w: float = 1.6, rel_w: float = 0.0,
                               beta: float = 6.0, beta_parse: float = 2.0,
                               rel_beta: float = 2.0, rel_beta_h: float = 2.0, rel_leaf: str = "relfeat") -> dict:
    """Phase 1/2 of the agent's compositional-program plan: add stroke RELATIONS as INFERRED LATENTS,
    MARGINALISED (not the committed cue that hurt -14). The character carries K RELATION HYPOTHESES (the
    junction structure at K thresholds, has_relhyp -> RelHyp -> has_relpart -> parts with a rel_feat
    signature) and the SAME recursive marginal-descent averages over them, one level above the parse.
    rel_leaf='relfeat' = Phase 1 (raw SqEuclid over the signature); rel_leaf='mahal' = Phase 2, the GRAMMAR:
    the relation match is scored under a learned per-dimension precision (PRIM_MODEL_ATTR = [rel_feat ++
    inv_std], learned from background) -- the noisy junction-type dims down-weighted, the stable ones up --
    so the relation match becomes a learned generative prior rather than a raw signature. rel_w=0 = the peak."""
    rel_pts = REL_FEAT_ATTR if rel_leaf == "relfeat" else REL_FEAT_N_ATTR    # flat for SqEuclid, nested for mahal
    err = _Plus([smoothdeform_error_term(),
                 _Times([_Lit(part_w), recursive_error_term(("has_stroke",), beta, beta_parse, PARSE_EDGE, PTS_ATTR, "pointset")]),
                 _Times([_Lit(rel_w), recursive_error_term((REL_PART_EDGE,), rel_beta, rel_beta_h, REL_PARSE_EDGE, rel_pts, rel_leaf)]),
                 _Times([_Lit(sc_w), shapecontext_error_term()])])
    return _Argmax(_NodesWhere("Concept", WORD_ATTR, _Lit(1.0)), "w", _Neg(err))


def predict_recursive_joint_term(part_w: float = 0.25, sc_w: float = 1.6, rel_lambda: float = 0.0,
                                 beta: float = 6.0, beta_parse: float = 2.0) -> dict:
    """Phase 3 of the agent's plan: JOINT inference -- relations folded INTO the parse, not summed alongside.
    The parse's part cue and the relation cue are no longer two independent marginals added together (the
    Phase-1/2 form, which never paid); instead each part's leaf is shape + rel_lambda * relation, so the
    SINGLE recursive marginal-descent over parse hypotheses scores shape AND relation under the SAME part
    correspondence. A correspondence that aligns part shapes but misaligns their junction structure is now
    penalised -- the relation CONSTRAINS the parse correspondence rather than voting beside it. Each parse-
    hypothesis part carries stroke_pts + rel_feat (its junction signature within that parse). rel_lambda=0
    recovers the recursive peak; this is the real lever the arc says relations pay through (the joint, not a cue)."""
    err = _Plus([smoothdeform_error_term(),
                 _Times([_Lit(part_w), recursive_error_term(("has_stroke",), beta, beta_parse, PARSE_EDGE, PTS_ATTR, f"joint:{rel_lambda}")]),
                 _Times([_Lit(sc_w), shapecontext_error_term()])])
    return _Argmax(_NodesWhere("Concept", WORD_ATTR, _Lit(1.0)), "w", _Neg(err))


def full_joint_error_term(beta_parse: float = 2.0, beta_corr: float = 2.0, parse_edge: str = PARSE_EDGE,
                          edge: str = STROKE_EDGE, pts_attr: str = PTS_ATTR) -> dict:
    """FULL JOINT generative inference: marginalise over BOTH uncertain structural latents at once —
    the PARSE (soft-min over parse-hypothesis pairings, temperature beta_parse) AND, inside each pairing,
    the part CORRESPONDENCE (soft-min over part-to-part assignment, temperature beta_corr). The Bayesian
    marginal likelihood of the query under the candidate's generative program, integrating the structure
    it leaves uncertain (rather than max-ing one parse and one correspondence). Composes held Terms
    (nested Sum/Exp/Log over PointSetDist), no new Rust — the deformation stays COMMITTED (the arc's
    finding: a fit latent; marginalise the uncertain, commit the determined)."""
    inner = _Sum(_Nbrs(_V("s"), parse_edge), "qh",
                 _Sum(_Nbrs(_V("w"), parse_edge), "ch",
                      _Exp(_Times([_Lit(-beta_parse), _joint_pair_dist("qh", "ch", edge, pts_attr, beta_corr)]))))
    return _Neg(_Div(_Log(inner), _Lit(beta_parse)))


def predict_full_joint_sc_term(part_w: float = 0.25, sc_w: float = 1.6, beta_parse: float = 2.0,
                               beta_corr: float = 2.0, parse_edge: str = PARSE_EDGE,
                               edge: str = STROKE_EDGE, pts_attr: str = PTS_ATTR) -> dict:
    """The agent's authored program with the part cue replaced by FULL JOINT inference (parse AND
    correspondence marginalised): smooth whole + part_w * full-joint + sc_w * shape-context."""
    err = _Plus([smoothdeform_error_term(),
                 _Times([_Lit(part_w), full_joint_error_term(beta_parse, beta_corr, parse_edge, edge, pts_attr)]),
                 _Times([_Lit(sc_w), shapecontext_error_term()])])
    return _Argmax(_NodesWhere("Concept", WORD_ATTR, _Lit(1.0)), "w", _Neg(err))


def marginal_part_error_term(beta: float = 2.0, parse_edge: str = PARSE_EDGE,
                             edge: str = STROKE_EDGE, pts_attr: str = PTS_ATTR) -> dict:
    """marginal(s, w) = -1/beta * log( sum_{qh in parses(s)} sum_{ch in parses(w)} exp(-beta *
    partdist(qh, ch)) ) — the soft-min part distance MARGINALISED over both drawings' parse hypotheses.
    The Bayesian average over uncertain parses (vs committing to one). All held Terms."""
    inner = _Sum(_Nbrs(_V("s"), parse_edge), "qh",
                 _Sum(_Nbrs(_V("w"), parse_edge), "ch",
                      _Exp(_Times([_Lit(-beta), _parse_pair_dist("qh", "ch", edge, pts_attr)]))))
    return _Neg(_Div(_Log(inner), _Lit(beta)))


def predict_marginal_part_term(beta: float = 2.0, parse_edge: str = PARSE_EDGE,
                               edge: str = STROKE_EDGE, pts_attr: str = PTS_ATTR) -> dict:
    """Recognition by the parse-MARGINALISED part distance alone (argmax over candidates of -marginal)."""
    return _Argmax(_NodesWhere("Concept", WORD_ATTR, _Lit(1.0)), "w",
                   _Neg(marginal_part_error_term(beta, parse_edge, edge, pts_attr)))


def predict_smooth_marginal_sc_term(part_w: float = 0.25, sc_w: float = 1.6, beta: float = 2.0,
                                    parse_edge: str = PARSE_EDGE, edge: str = STROKE_EDGE,
                                    pts_attr: str = PTS_ATTR) -> dict:
    """The best fusion with the part cue MARGINALISED over parse hypotheses: smooth whole + part_w *
    marginal-part + sc_w * shape-context. The genuine BPL move — average over the uncertain parse."""
    err = _Plus([smoothdeform_error_term(),
                 _Times([_Lit(part_w), marginal_part_error_term(beta, parse_edge, edge, pts_attr)]),
                 _Times([_Lit(sc_w), shapecontext_error_term()])])
    return _Argmax(_NodesWhere("Concept", WORD_ATTR, _Lit(1.0)), "w", _Neg(err))


def deform_marginal_error_term(beta: float = 2.0, sign_attr: str = SIGN_FEAT_ATTR,
                               word_attr: str = WORD_FEAT_ATTR) -> dict:
    """deform_marginal(s, w) = -1/beta * log( exp(-beta * PointSetDist) + exp(-beta * SmoothDeformDist) )
    — the whole-figure distance MARGINALISED over the DEFORMATION: a soft-min over the RIGID (no-warp)
    and the SMOOTH (warp) hypotheses. beta->inf commits to the better one per pair; finite beta averages
    over how-much-to-deform — so it uses the rigid match where deformation isn't needed (no warp-cost
    penalty) and the warp where it is, integrating over the token deformation. Held Terms only."""
    a, b = _Attr(_V("s"), sign_attr), _Attr(_V("w"), word_attr)
    inner = _Plus([_Exp(_Times([_Lit(-beta), _PointSetDist(a, b)])),
                   _Exp(_Times([_Lit(-beta), _SmoothDeformDist(a, b)]))])
    return _Neg(_Div(_Log(inner), _Lit(beta)))


def predict_marginal_all_sc_term(part_w: float = 0.25, sc_w: float = 1.6,
                                 parse_beta: float = 2.0, deform_beta: float = 2.0,
                                 parse_edge: str = PARSE_EDGE, edge: str = STROKE_EDGE,
                                 pts_attr: str = PTS_ATTR) -> dict:
    """Fully marginalised fusion: the whole cue MARGINALISED over deformation + the part cue
    MARGINALISED over parse + shape-context. BPL's posture on BOTH uncertain latents (warp, parse)."""
    err = _Plus([deform_marginal_error_term(deform_beta),
                 _Times([_Lit(part_w), marginal_part_error_term(parse_beta, parse_edge, edge, pts_attr)]),
                 _Times([_Lit(sc_w), shapecontext_error_term()])])
    return _Argmax(_NodesWhere("Concept", WORD_ATTR, _Lit(1.0)), "w", _Neg(err))


def _Times(items): return {"type": "Times", "items": items}
def _Dot(a, b): return {"type": "Dot", "a": a, "b": b}
def _VecSub(a, b): return {"type": "VecSub", "a": a, "b": b}
def _SqEuclid(a, b): return _Dot(_VecSub(a, b), _VecSub(a, b))

BOW_ATTR = "bow_hist"
LEARN_FEAT_ATTR = "learn_feat"


def _directed_learned_part(from_var: str, to_var: str, edge: str, fa: str) -> dict:
    """mean over `from`'s parts of ( min over `to`'s parts of squared-Euclidean(learn_feat, learn_feat) )
    — the structure-preserving learned part correspondence: each part matched by POSITION (layout) +
    learned soft MEMBERSHIP (per-primitive shape encoding). Squared-Euclid = Dot(VecSub, VecSub)."""
    inner = _MinOver(_Nbrs(_V(to_var), edge), "sq",
                     _SqEuclid(_Attr(_V("sc"), fa), _Attr(_V("sq"), fa)))
    return _Div(_Sum(_Nbrs(_V(from_var), edge), "sc", inner), _Count(_Nbrs(_V(from_var), edge)))


def learned_partnested_error_term(edge: str = STROKE_EDGE, fa: str = LEARN_FEAT_ATTR) -> dict:
    """Symmetric structure-preserving LEARNED part-correspondence distance (both directions). The
    per-primitive deformation prior lives in the learned membership component of learn_feat."""
    return _Plus([_directed_learned_part("w", "s", edge, fa),
                  _directed_learned_part("s", "w", edge, fa)])


def predict_smooth_learnedpart_sc_term(lp_w: float = 0.25, sc_w: float = 1.6,
                                       edge: str = STROKE_EDGE, fa: str = LEARN_FEAT_ATTR) -> dict:
    """The agent's recommended move: replace the raw point-set part cue with the LEARNED part cue
    (per-primitive deformation prior, structure-preserving) inside the smooth+part+SC fusion."""
    err = _Plus([smoothdeform_error_term(),
                 _Times([_Lit(lp_w), learned_partnested_error_term(edge, fa)]),
                 _Times([_Lit(sc_w), shapecontext_error_term()])])
    return _Argmax(_NodesWhere("Concept", WORD_ATTR, _Lit(1.0)), "w", _Neg(err))


def predict_full_term(part_w: float = 0.25, sc_w: float = 1.6, bow_w: float = 0.6,
                      stroke_edge: str = STROKE_EDGE, pts_attr: str = PTS_ATTR,
                      bow_attr: str = BOW_ATTR) -> dict:
    """The full combine-all: smooth deformation + canonical parts + shape context + the LEARNED
    bag-of-primitives cue (cosine of the two L2-normalised histograms, via Dot — a SIMILARITY, so it
    SUBTRACTS from the error). The bow is the agent's learned sub-stroke vocabulary (composition cue),
    complementary to the geometric cues. argmax over candidates of -error."""
    err = _Plus([smoothdeform_error_term(),
                 _Times([_Lit(part_w), partnested_error_term(stroke_edge, pts_attr)]),
                 _Times([_Lit(sc_w), shapecontext_error_term()]),
                 _Times([_Lit(-bow_w), _Dot(_Attr(_V("s"), bow_attr), _Attr(_V("w"), bow_attr))])])
    return _Argmax(_NodesWhere("Concept", WORD_ATTR, _Lit(1.0)), "w", _Neg(err))


def smooth_combined_error_term(weight: float = 0.25, stroke_edge: str = STROKE_EDGE,
                               pts_attr: str = PTS_ATTR) -> dict:
    """combined(s, w) = smoothdeform_error(whole) + weight * part_error(canonical parts). Fuses the
    agent's two strongest cues: the smooth-deformation whole-figure match (its best holistic cue) and
    the canonical-parse part-nested cue — its combine-all move over its best complementary cues. The
    part weight is 0.25 (re-tuned for the strong smooth cue; the earlier 0.15 fit the weaker point-set)."""
    return _Plus([smoothdeform_error_term(), _Times([_Lit(weight),
                                                     partnested_error_term(stroke_edge, pts_attr)])])


def predict_smooth_combined_term(weight: float = 0.25, stroke_edge: str = STROKE_EDGE,
                                 pts_attr: str = PTS_ATTR) -> dict:
    """argmax over candidate words of -smooth_combined_error(s, w) — the fusion of the smooth-field
    whole-figure cue and the canonical-parse part cue, one decision (same argmax shape)."""
    return _Argmax(_NodesWhere("Concept", WORD_ATTR, _Lit(1.0)), "w",
                   _Neg(smooth_combined_error_term(weight, stroke_edge, pts_attr)))


REL_FEAT_ATTR = "rel_feat"


def predict_smooth_part_sc_rel_term(part_w: float = 0.25, sc_w: float = 1.6, rel_w: float = 0.3,
                                    stroke_edge: str = STROKE_EDGE, pts_attr: str = PTS_ATTR,
                                    rel_attr: str = REL_FEAT_ATTR) -> dict:
    """Add the RELATIONS cue (BPL stroke relations) to the best fusion: smooth whole + part_w*rigid
    parts + sc_w*shape-context + rel_w*part-correspondence-over-RELATION-SIGNATURE. The relation match
    reuses the squared-Euclid part correspondence (learned_partnested_error_term) over the junction
    signature attr — parts match by their connectivity ROLE (end/along/free junctions + endpoint
    positions), the writer-invariant topology that ties the parts into a character."""
    err = _Plus([smoothdeform_error_term(),
                 _Times([_Lit(part_w), partnested_error_term(stroke_edge, pts_attr)]),
                 _Times([_Lit(sc_w), shapecontext_error_term()]),
                 _Times([_Lit(rel_w), learned_partnested_error_term(stroke_edge, rel_attr)])])
    return _Argmax(_NodesWhere("Concept", WORD_ATTR, _Lit(1.0)), "w", _Neg(err))


def smooth_part_sc_error_term(part_w: float = 0.25, sc_w: float = 1.6,
                              stroke_edge: str = STROKE_EDGE, pts_attr: str = PTS_ATTR) -> dict:
    """Three-cue combine-all: the smooth-field whole-figure cue + the canonical-parse part cue + the
    SHAPE-CONTEXT descriptor cue. The descriptor (each point = the distribution of the others) is
    complementary to the deformation cue (how-much-warp), so it may add even at a modest standalone."""
    return _Plus([smoothdeform_error_term(),
                  _Times([_Lit(part_w), partnested_error_term(stroke_edge, pts_attr)]),
                  _Times([_Lit(sc_w), shapecontext_error_term()])])


def predict_smooth_part_sc_term(part_w: float = 0.25, sc_w: float = 1.6,
                                stroke_edge: str = STROKE_EDGE, pts_attr: str = PTS_ATTR) -> dict:
    """argmax over candidate words of -(smooth + part_w*parts + sc_w*shape_context) — the three-cue
    fusion of the agent's strongest deformation, part, and descriptor cues."""
    return _Argmax(_NodesWhere("Concept", WORD_ATTR, _Lit(1.0)), "w",
                   _Neg(smooth_part_sc_error_term(part_w, sc_w, stroke_edge, pts_attr)))


def combined_error_term(weight: float = 0.5, stroke_edge: str = STROKE_EDGE,
                        pts_attr: str = PTS_ATTR) -> dict:
    """combined(s, w) = pointset_error(whole) + weight * part_error(nested). The agent's COMBINE-
    ALL move (the same it uses to fuse speech cues): keep the ROBUST whole-figure match — which is
    immune to writer-inconsistent stroke segmentation — and ADD the part cue where it agrees, so the
    holistic shape carries it and the nested parts only sharpen. weight=0 reduces to the flat match."""
    return _Plus([pointset_error_term(), _Times([_Lit(weight),
                                                 partnested_error_term(stroke_edge, pts_attr)])])


def predict_combined_term(weight: float = 0.5, stroke_edge: str = STROKE_EDGE,
                          pts_attr: str = PTS_ATTR) -> dict:
    """predict_combined(s) = argmax over candidate words of -combined_error(s, w). The agent fuses
    its whole-figure and part-nested cues into one decision (combine-all), same argmax shape."""
    return _Argmax(_NodesWhere("Concept", WORD_ATTR, _Lit(1.0)), "w",
                   _Neg(combined_error_term(weight, stroke_edge, pts_attr)))


def smoothdeform_error_term(sign_attr: str = SIGN_FEAT_ATTR,
                            word_attr: str = WORD_FEAT_ATTR) -> dict:
    """smoothdeform_error(s, w) = SmoothDeformDist(features(s), synth_features(w)) — the "distortable
    canvas" replacement for deform_error_term: a SMOOTH non-rigid deformation field (the distortion
    cost IS the metric) rather than a global affine. The field optimisation is the Rust primitive."""
    return _SmoothDeformDist(_Attr(_V("s"), sign_attr), _Attr(_V("w"), word_attr))


def predict_smoothdeform_term(sign_attr: str = SIGN_FEAT_ATTR,
                              word_attr: str = WORD_FEAT_ATTR) -> dict:
    """predict_smoothdeform(s) = argmax over candidate words of -SmoothDeformDist(s, w). The paper's
    distortable-canvas recognition as graph data (same argmax shape; replaces predict_deform_term)."""
    return _Argmax(_NodesWhere("Concept", WORD_ATTR, _Lit(1.0)), "w",
                   _Neg(smoothdeform_error_term(sign_attr, word_attr)))


def tps_error_term(sign_attr: str = SIGN_FEAT_ATTR, word_attr: str = WORD_FEAT_ATTR) -> dict:
    """tps_error(s, w) = TpsDeformDist(features(s), synth_features(w)) — the principled thin-plate-
    spline warp: residual + BENDING ENERGY (the non-affine distortion is the metric), per Shape
    Contexts / Bookstein. The spline solve is the Rust primitive; the decision is the graph."""
    return _TpsDeformDist(_Attr(_V("s"), sign_attr), _Attr(_V("w"), word_attr))


def predict_tps_term(sign_attr: str = SIGN_FEAT_ATTR, word_attr: str = WORD_FEAT_ATTR) -> dict:
    """predict_tps(s) = argmax over candidate words of -TpsDeformDist(s, w) — the thin-plate-spline
    bending-energy recognition as graph data (same argmax shape; the principled SmoothDeformDist)."""
    return _Argmax(_NodesWhere("Concept", WORD_ATTR, _Lit(1.0)), "w",
                   _Neg(tps_error_term(sign_attr, word_attr)))


def shapecontext_error_term(sign_attr: str = SIGN_FEAT_ATTR, word_attr: str = WORD_FEAT_ATTR) -> dict:
    """sc_error(s, w) = ShapeContextDist(features(s), synth_features(w)) — the log-polar shape-context
    descriptor match (Belongie-Malik-Puzicha): each point described by the distribution of the
    others, matched by chi-squared. The descriptor + match is the Rust primitive."""
    return _ShapeContextDist(_Attr(_V("s"), sign_attr), _Attr(_V("w"), word_attr))


def predict_shapecontext_term(sign_attr: str = SIGN_FEAT_ATTR, word_attr: str = WORD_FEAT_ATTR) -> dict:
    """predict_sc(s) = argmax over candidate words of -ShapeContextDist(s, w) — shape-context
    recognition as graph data (same argmax shape)."""
    return _Argmax(_NodesWhere("Concept", WORD_ATTR, _Lit(1.0)), "w",
                   _Neg(shapecontext_error_term(sign_attr, word_attr)))


def sctps_error_term(sign_attr: str = SIGN_FEAT_ATTR, word_attr: str = WORD_FEAT_ATTR) -> dict:
    """sctps_error(s, w) = ScTpsDist(features(s), synth_features(w)) — the FULL Shape-Contexts
    distance: shape-context correspondences feeding a TPS, = SC matching cost + bending energy."""
    return _ScTpsDist(_Attr(_V("s"), sign_attr), _Attr(_V("w"), word_attr))


def predict_sctps_term(sign_attr: str = SIGN_FEAT_ATTR, word_attr: str = WORD_FEAT_ATTR) -> dict:
    """predict_sctps(s) = argmax over candidate words of -ScTpsDist(s, w) — the full Shape-Contexts
    recognition (descriptor correspondences + TPS bending) as graph data."""
    return _Argmax(_NodesWhere("Concept", WORD_ATTR, _Lit(1.0)), "w",
                   _Neg(sctps_error_term(sign_attr, word_attr)))


def install_recognition_weights(substrate, default: float = 1.0) -> int:
    """Give every feature concept a graph-resident, agent-adjustable recognition
    weight (`rec_weight`). THIS is the agent's lever on recognition: do-contrast a
    weight, reweight, and the recogniser responds — no Python edit. Returns count."""
    n = 0
    for c in substrate.nodes("Concept"):
        a = substrate.node(c)["attrs"]
        if (a.get("origin") == "phonology" or a.get("feature_kind")) \
                and a.get(WEIGHT_KEY) is None:
            substrate.set_attr(c, WEIGHT_KEY, float(default))
            n += 1
    return n


def mark_words(substrate, word_names) -> int:
    """Tag the candidate word concepts (`is_word`) so the recognition Term can range
    over them with NodesWhere. Mechanical setup, not a decision."""
    names = set(word_names)
    n = 0
    for c in substrate.nodes("Concept"):
        if substrate.node(c)["attrs"].get("name") in names:
            substrate.set_attr(c, WORD_ATTR, 1.0)
            n += 1
    return n


def recognize_sign(substrate, sign, weight_key: str = WEIGHT_KEY):
    """Evaluate the recognition Term on one sign — the agent's program runs natively.
    Returns the predicted word's name (or None)."""
    try:
        w = substrate.evaluate(_Pred(predict_term(weight_key)), {"s": sign})
    except Exception:
        return None
    return substrate.node(w)["attrs"].get("name") if w is not None else None


def measure_recognition(substrate, test_signs, weight_key: str = WEIGHT_KEY) -> float:
    """Payoff = fraction of test signs the GRAPH recogniser gets right.
    test_signs: [(sign_node, true_word_name)]. This is the do-contrast's payoff —
    recognition under the agent's own graph recogniser, so toggling a rec_weight
    actually moves it (unlike the band-mean predict_one, which ignored features)."""
    if not test_signs:
        return 0.0
    ok = sum(1 for s, w in test_signs
             if recognize_sign(substrate, s, weight_key) == w)
    return ok / len(test_signs)


def investigate_rec_weight(substrate, feature, measure_payoff,
                           band: float = 0.02) -> str:
    """The agent DO-CONTRASTS a feature's recognition weight — the same move it
    makes for any lever (meta_monitor.investigate), now over the graph recogniser.
    Measure recognition WITH the feature (rec_weight=1) vs WITHOUT (=0); three-way
    verdict from the MEASURED delta, never assumed:
        |delta| <= band -> disconnected_lever (the feature doesn't reach recognition)
        with  > without -> lever_helps       (the feature works)
        with  < without -> lever_harms       (the feature is counterproductive)
    Records the verdict + delta on the feature concept (graph data). Restores the
    weight; the tuning step decides what to set it to."""
    saved = substrate.node(feature)["attrs"].get(WEIGHT_KEY, 1.0)
    substrate.set_attr(feature, WEIGHT_KEY, 1.0)
    with_p = float(measure_payoff())
    substrate.set_attr(feature, WEIGHT_KEY, 0.0)
    without_p = float(measure_payoff())
    delta = with_p - without_p
    verdict = ("disconnected_lever" if abs(delta) <= band
               else "lever_helps" if delta > 0 else "lever_harms")
    substrate.set_attr(feature, "rec_verdict", verdict)
    substrate.set_attr(feature, "rec_delta", float(delta))
    substrate.set_attr(feature, WEIGHT_KEY, saved)
    return verdict


def agent_tune_recognition(substrate, measure_payoff, band: float = 0.02) -> dict:
    """The agent investigates EVERY recognition feature by do-contrast and tunes its
    OWN recogniser: keep what helps (rec_weight=1), zero what harms or doesn't
    connect. This is the thing it could not do while recognition was Python — work
    out which features (band-means, phonology, the dynamics) actually matter, and
    act on it. Returns {feature_name: verdict}."""
    feats = [c for c in substrate.nodes("Concept")
             if substrate.node(c)["attrs"].get(WEIGHT_KEY) is not None]
    results = {}
    for f in feats:
        v = investigate_rec_weight(substrate, f, measure_payoff, band)
        substrate.set_attr(f, WEIGHT_KEY, 1.0 if v == "lever_helps" else 0.0)
        results[substrate.node(f)["attrs"].get("name", f)] = v
    return results


# ---------------------------------------------------------------------------
# MATCHED-FILTER recognition — the SONAR transfer. Same shape as the DtwTo
# synth-error, but the SCORE is the native XCorrPeak (peak normalised cross-
# correlation over a lag search) instead of the DtwTo distance. The agent
# authored XCorrPeak via runtime_design (agent_specify_matched_filter +
# emit_primitive_rust); here it COMPOSES the recognition decision over it.
# XCorrPeak is a SIMILARITY (higher = better), the opposite sign of DtwTo's
# distance — so the decision is argmax of XCorrPeak directly (no Neg).
# ---------------------------------------------------------------------------

def _XCorrPeak(a, b): return {"type": "XCorrPeak", "a": a, "b": b}


def matched_filter_term(sign_attr: str = SIGN_FEAT_ATTR,
                        word_attr: str = WORD_FEAT_ATTR) -> dict:
    """mf_score(s, w) = XCorrPeak(features(s), synth_features(w)) — a graph Term.
    Both buffers are graph attrs (frames x bands tuples) the adapter populated:
    features(s) on the sign `s`, the candidate's synthesis-in-voice(s) on word `w`.
    The peak-NCC-over-lags itself is the native XCorrPeak Rust primitive; this is
    just the composition (the matched-filter analogue of synth_error_term)."""
    return _XCorrPeak(_Attr(_V("s"), sign_attr), _Attr(_V("w"), word_attr))


def predict_matched_filter_term(sign_attr: str = SIGN_FEAT_ATTR,
                                word_attr: str = WORD_FEAT_ATTR) -> dict:
    """predict_mf(s) = argmax over candidate words of XCorrPeak(s, w) — the whole
    matched-filter recognition DECISION as graph data. XCorrPeak is a similarity
    (peak NCC in [-1, 1], higher = better match), so the winner is the argmax
    DIRECTLY (unlike the DtwTo distance, which is argmax of -DtwTo)."""
    return _Argmax(_NodesWhere("Concept", WORD_ATTR, _Lit(1.0)), "w",
                   matched_filter_term(sign_attr, word_attr))


__all__ = ["score_term", "predict_term", "install_recognition_weights",
           "mark_words", "recognize_sign", "measure_recognition",
           "investigate_rec_weight", "agent_tune_recognition", "WEIGHT_KEY",
           "synth_error_term", "predict_synth_term",
           "pointset_error_term", "predict_pointset_term",
           "deform_error_term", "predict_deform_term",
           "smoothdeform_error_term", "predict_smoothdeform_term",
           "tps_error_term", "predict_tps_term",
           "shapecontext_error_term", "predict_shapecontext_term",
           "sctps_error_term", "predict_sctps_term",
           "partnested_error_term", "predict_partnested_term",
           "generative_render_error_term", "predict_generative_render_term",
           "predict_smooth_render_sc_term",
           "marginal_part_error_term", "predict_marginal_part_term",
           "predict_smooth_marginal_sc_term", "PARSE_EDGE",
           "full_joint_error_term", "predict_full_joint_sc_term",
           "recursive_error_term", "predict_recursive_sc_term", "NORM_PTS_ATTR", "PRIM_MODEL_ATTR",
           "TYPEGEN_MODEL_ATTR", "POSE_PTS_ATTR",
           "predict_recursive_rel_term", "predict_recursive_joint_term",
           "REL_PARSE_EDGE", "REL_PART_EDGE", "REL_FEAT_ATTR", "REL_FEAT_N_ATTR",
           "deform_marginal_error_term", "predict_marginal_all_sc_term",
           "predict_context_term", "CONTEXT_PRIMED_ATTR",
           "predict_word_term", "word_error_term", "LEXWORD_ATTR", "SLOT_EDGE", "POS_ATTR",
           "combined_error_term", "predict_combined_term",
           "smooth_combined_error_term", "predict_smooth_combined_term",
           "smooth_part_sc_error_term", "predict_smooth_part_sc_term",
           "predict_smooth_part_sc_rel_term", "REL_FEAT_ATTR",
           "predict_full_term", "BOW_ATTR",
           "learned_partnested_error_term", "predict_smooth_learnedpart_sc_term", "LEARN_FEAT_ATTR",
           "STROKE_EDGE", "PTS_ATTR",
           "matched_filter_term", "predict_matched_filter_term",
           "SIGN_FEAT_ATTR", "WORD_FEAT_ATTR"]
