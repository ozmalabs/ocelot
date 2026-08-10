"""recognition_architecture — the agent builds the recognizer it asked for.

Perception is no longer the bottleneck; the DECISION stage is. The agent's old
`predict_one` collapsed its rich per-sign perception to one global signature and a
flat DTW/NB vote — it threw away accuracy the perception already provided (a plain
both-ears kNN beats it). Asked what it wants, the agent said: its features are
GLOBAL thresholds that can't sharpen one distinction without blurring others; it
wants to use a discriminating feature only WHEN telling a confused pair apart —
pairwise / contextual recognition.

This assembles that as a TWO-STAGE recognizer the agent designs from its OWN state,
the runtime_design pattern (the agent decides WHAT; a mechanical generator emits
HOW; the decision is graph-resident Term-trees evaluated natively):

  Stage 1 — GLOBAL, BOTH EARS.  A speaker-invariant nearest-centroid score per word
    over the FULL perception of both ears: the gammatone trajectory (sharp in time)
    AND the FFT trajectory (sharp in frequency). Per-word centroids are the mean of
    each ear's L2-normalised trajectory over the training (non-test) speakers. The
    per-word score is a graph Term:  Dot(clip_gam, centroid_gam) + Dot(clip_fft,
    centroid_fft)  (cosine, since both are unit vectors). ArgMax over the ten word
    scores is the top word; the ranked scores give a candidate list. This integrates
    both ears — exactly the perception the old global signature did not.

  Stage 2 — PAIRWISE / CONTEXTUAL (the thing it asked for).  When Stage 1's top two
    are a pair the agent has a GROUNDED discriminating cue for (an `assessed_cue`
    Concept it minted in cue_assessment.agent_assess_cues, from its own Confusions),
    decide between just those two with THAT cue — the feature used ONLY in the
    context where it discriminates, never globally. The tie-break is a graph
    Term-tree:

      tie_break(clip | top2={A,B}) =
        IfThenElse( |cue(clip) − a_cue_mean| < |cue(clip) − b_cue_mean|, A, B )

    where cue(·) is the assessed cue's own composed predicate (an onset-tilt, a
    formant ArgMax from the sharp FFT ear, ...) and a/b_cue_mean are that cue's
    per-word means over the training speakers. The agent picks WHICH pairs get a
    tie-break and WHICH cue from its state (its Confusions × its grounded cues) —
    not hand-picked.

The agent decides WHAT (which pairs, which cue — read from its graph); the generator
here emits HOW (assembles the centroid scores + the per-pair tie-break Terms). Python
is only the world-adapter measurement harness: ingest a clip, read its trajectories,
evaluate the agent's Term-trees, read the decision back out. See
[[ozma_agent_builds_pairwise]] / [[ozma_agent_designs_runtime]] /
[[ozma_concepts_in_gamma]] / [[ozma_recognition_in_graph]].
"""
from __future__ import annotations

import numpy as np


# --- Term wrapper (the established pattern: a dict with ._json the wrapper reads)
class _T:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def _norm(v: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(v))
    return v / n if n > 0 else v


# ===========================================================================
#  Stage 1 — the global both-ears exemplar (kNN) score, graph-resident.
#
#  The old global signature (one centroid per word) is too coarse here — a single
#  mean per word loses the within-word spread the verified 61% both-ears kNN keeps.
#  So Stage 1 is exemplar-based, matching that baseline: every training clip is an
#  exemplar carrying BOTH ears, and a test clip scores against each exemplar with a
#  graph Term  Dot(clip_gam, ex_gam) + Dot(clip_fft, ex_fft)  (cosine, both unit
#  vectors). The global top-k exemplars vote for the word — kNN, both ears. The
#  per-exemplar similarity is the graph Term (the scoring); the top-k vote is
#  mechanical adapter readout (as ordering ten floats was).
# ===========================================================================

def _exemplar_score_term(exemplar) -> dict:
    """Both-ears similarity of the clip Var `s` to one exemplar node, as a graph
    Term:  Dot(s.traj_n, ex.gam) + Dot(s.fft_n, ex.fft). The exemplar's vectors are
    read by Attr off the exemplar node `e` (bound in the env), so one Term serves
    every exemplar — no giant Lit vectors baked per word."""
    return {"type": "Plus", "items": [
        {"type": "Dot",
         "a": {"type": "Attr", "node": {"type": "Var", "name": "s"}, "key": "traj_n"},
         "b": {"type": "Attr", "node": {"type": "Var", "name": "e"}, "key": "gam"}},
        {"type": "Dot",
         "a": {"type": "Attr", "node": {"type": "Var", "name": "s"}, "key": "fft_n"},
         "b": {"type": "Attr", "node": {"type": "Var", "name": "e"}, "key": "fft"}},
    ]}


_EXEMPLAR_TERM = _exemplar_score_term(None)


def learn_word_centroids(substrate, train, words: list, k: int = 5) -> "NodeID":
    """Stage 1 fit (adapter): store every training clip as a both-ears EXEMPLAR node
    linked to a graph `RecognizerArchitecture` node. `train` is a list of
    (word, gammatone_vec, fft_vec), each L2-normalised. (Kept the historical name;
    the architecture is exemplar/kNN, not a single centroid.) `k` is the kNN vote
    size, recorded on the arch. Returns the architecture node id."""
    arch = substrate.add_node("RecognizerArchitecture", {
        "origin": "recognition_architecture",
        "stage1": "both_ears_knn", "knn_k": int(k),
        "words": list(words)})
    try:
        substrate.add_production({
            "src": {"type": "RecognizerArchitecture", "var": "a"},
            "edge_type": "has_exemplar",
            "tgt": {"type": "AcousticExemplar", "var": "b"},
            "provenance": "recognition_architecture:has_exemplar"})
    except Exception:
        pass
    for w, g, f in train:
        ex = substrate.add_node("AcousticExemplar", {
            "word": w, "gam": _norm(np.asarray(g, float)).astype(float).tolist(),
            "fft": _norm(np.asarray(f, float)).astype(float).tolist()})
        try:
            substrate.add_edge(arch, "has_exemplar", ex)
        except Exception:
            pass
    return arch


def _exemplars(substrate, arch):
    return list(substrate.neighbours(arch, "has_exemplar"))


def _attach_clip(substrate, arch, gam: np.ndarray, fft: np.ndarray):
    """Adapter: attach a test clip's L2-normalised both-ears trajectories to a fresh
    AcousticClip node `s`, so the per-exemplar Stage-1 score Term (reading s.traj_n /
    s.fft_n) evaluates against this clip. Returns the clip node id."""
    return substrate.add_node("AcousticClip", {
        "traj_n": _norm(gam).astype(float).tolist(),
        "fft_n": _norm(fft).astype(float).tolist()})


def stage1_rank(substrate, arch, clip, words: list, exemplars=None,
                with_margin: bool = False):
    """Stage-1 kNN ranking, both ears: score the clip against every exemplar with the
    agent's similarity Term, take the global top-k, vote. Returns words ranked
    best-first (by vote count, then summed similarity). The SCORING is the graph
    Term; the top-k vote is mechanical adapter readout.

    `with_margin=True` also returns a CONFIDENCE margin for the top-1 vs top-2 word:
    (summed top-k similarity of top1 − that of top2). A small margin means Stage 1 is
    genuinely ambiguous between its two candidates — the only context where a Stage-2
    tie-break is allowed to override (lever 1, low-confidence gating)."""
    from collections import Counter
    exs = exemplars if exemplars is not None else _exemplars(substrate, arch)
    k = int(substrate.node(arch)["attrs"].get("knn_k", 5))
    sims = []
    for ex in exs:
        sc = float(substrate.evaluate(_T(_EXEMPLAR_TERM), {"s": clip, "e": ex}))
        sims.append((sc, substrate.node(ex)["attrs"].get("word")))
    sims.sort(reverse=True)
    topk = sims[:k]
    votes = Counter(w for _, w in topk)
    simsum: dict = {}
    for sc, w in topk:
        simsum[w] = simsum.get(w, 0.0) + sc
    # rank every word: words in the top-k by (votes, summed sim); the rest after,
    # by their single best exemplar similarity (so a full ranking always exists).
    best_sim: dict = {}
    for sc, w in sims:
        if w not in best_sim:
            best_sim[w] = sc
    ranked = sorted(words, key=lambda w: (-(votes.get(w, 0)),
                                          -simsum.get(w, 0.0),
                                          -best_sim.get(w, -1e9)))
    if not with_margin:
        return ranked
    top1, top2 = ranked[0], ranked[1]
    margin = simsum.get(top1, 0.0) - simsum.get(top2, 0.0)
    return ranked, float(margin)


# ===========================================================================
#  Stage 2 — the pairwise / contextual tie-break, designed from the agent's state.
#
#  Two principled levers fix the diagnosed flaw (the cue SHAPE transfers across
#  speakers but the ABSOLUTE training threshold does not — it drifts under speaker
#  change and flips correct Stage-1 answers):
#
#  Lever 1 (gating, in the harness/stage1_rank): a tie-break may only override a
#    LOW-CONFIDENCE Stage-1 decision (small top1-vs-top2 margin). When Stage 1 is
#    confident, trust it. The margin cut is read from the data (bottom tertile of the
#    margin distribution), not a magic constant.
#
#  Lever 2 (speaker-relative cue, here): drop the absolute boundary. The agent's own
#    science (speaker_norm.py): vocal-tract length shifts ALL formants by the SAME
#    amount, so a quantity that CO-MOVES with the cue, subtracted, cancels the speaker
#    term. We build a co-moving REFERENCE Term per cue (the per-utterance mean formant
#    for formant cues; the per-utterance mean band energy for energy cues) and decide
#    on the speaker-RELATIVE cue  (cue − ref)  against likewise-referenced training
#    means. The transferable ORDER survives; the drifting absolute boundary is gone.
# ===========================================================================


def _reference_term(spec: dict, res: int) -> dict | None:
    """A co-moving REFERENCE Term for a cue — a quantity that shifts WITH the cue under
    a speaker change, so (cue − ref) is speaker-relative (the agent's VTL/level
    normalisation principle, speaker_norm.py). Chosen by cue family:

      formant cues (f1/f2/f2-f1) : per-utterance MEAN formant bin over the whole sharp
        FFT spectrum — VTL scales every formant by the same log-shift; subtracting the
        mean formant cancels it (exactly speaker_norm.vtl).
      band-energy cues           : per-utterance MEAN band energy over the gammatone
        spectrum — loudness/channel level shifts every band together; subtracting the
        mean level cancels it.

    Returns None when no principled co-moving reference applies (then lever 2 falls
    back to the absolute decision for that pair)."""
    from domains.hint_grounding import (FFT_RES, F1_LO_HZ, F2_HI_HZ,
                                        _fft_band_range, _F)
    cue = spec.get("cue", "")
    if cue in ("f1_formant", "f2_formant", "f2_minus_f1"):
        # mean formant position across the F1..F2 sharp-FFT region (co-moves with VTL)
        lo, hi = _fft_band_range(FFT_RES, F1_LO_HZ, F2_HI_HZ)
        if hi <= lo:
            return None
        wam = {"type": "ArgMax", "items": [_F(FFT_RES, j) for j in range(lo, hi)]}
        # ArgMax index here is the peak bin of the whole region; it co-moves with the
        # per-formant ArgMax under a uniform VTL shift, so cue − ref is VTL-relative.
        return wam
    # energy / tilt / movement cues read gammatone band attrs — the co-moving
    # reference is the clip's mean band energy (level), the term speaker_norm flips on.
    if cue in ("onset_tilt", "ending_nasal", "vowel_height",
               "onset_level", "ending_level", "movement"):
        bands = [{"type": "Attr", "node": {"type": "Var", "name": "s"},
                  "key": f"band{res}_{i}"} for i in range(res)]
        return {"type": "Div", "a": {"type": "Plus", "items": bands},
                "b": {"type": "Lit", "value": float(res)}}
    return None

def agent_design_tiebreaks(substrate, train, res: int) -> list:
    """The agent designs Stage 2 from its OWN state: for every confusion pair it has
    GROUNDED a discriminating cue for (an `assessed_cue` Concept it minted from its
    Confusions in cue_assessment.agent_assess_cues), specify a contextual tie-break
    over that cue. NOT hand-picked — read from the Confusion × assessed_cue graph.

    Each spec carries the pair (A,B), the cue name + its composed predicate Term, and
    the cue's per-word means (a_cue_mean / b_cue_mean) measured on the training
    speakers — the only learned Stage-2 parameters. Returns the spec list."""
    # the agent's grounded contextual cues (one per confused pair it could crack)
    cues = {}
    for c in substrate.nodes("Concept"):
        a = substrate.node(c)["attrs"]
        if a.get("feature_kind") != "assessed_cue":
            continue
        pair = a.get("pair", "")
        if "/" not in pair:
            continue
        X, Y = pair.split("/", 1)
        cues[(X, Y)] = {"cue": a.get("cue"), "predicate": a.get("predicate"),
                        "fisher": float(a.get("fisher", 0.0)),
                        "baseline": float(a.get("baseline", 0.0))}
    # the agent's confusions, strongest first — only pairs it actually confuses get
    # a contextual tie-break (the context where the cue is worth using).
    confs = sorted(
        ((substrate.node(c)["attrs"].get("true_word"),
          substrate.node(c)["attrs"].get("pred_word"),
          int(substrate.node(c)["attrs"].get("count", 0)))
         for c in substrate.nodes("Confusion")),
        key=lambda x: -x[2])

    specs = []
    seen = set()
    for A, B, n in confs:
        key = frozenset((A, B))
        if key in seen:
            continue
        entry = cues.get((A, B)) or cues.get((B, A))
        if entry is None:
            continue
        pred = entry["predicate"]
        # the cue's per-word means on the training speakers (Stage-2 parameters):
        # evaluate the cue's own predicate over each word's training clips.
        am = _cue_mean(substrate, pred, train, A)
        bm = _cue_mean(substrate, pred, train, B)
        if am is None or bm is None:
            continue
        seen.add(key)
        spec = {"A": A, "B": B, "count": n, "cue": entry["cue"],
                "predicate": pred, "a_cue_mean": am, "b_cue_mean": bm,
                "fisher": entry["fisher"], "baseline": entry["baseline"]}
        # lever 2: a SPEAKER-RELATIVE version of the same decision. Build the cue's
        # co-moving reference Term and measure the referenced means (cue − ref) on the
        # SAME training speakers, so the relative decision uses a boundary that
        # cancels the speaker (VTL/level) term instead of drifting with it.
        ref = _reference_term(spec, res)
        if ref is not None:
            rel = {"type": "Minus", "a": pred, "b": ref}
            ra = _cue_mean(substrate, rel, train, A)
            rb = _cue_mean(substrate, rel, train, B)
            if ra is not None and rb is not None:
                spec["ref_term"] = ref
                spec["rel_predicate"] = rel
                spec["a_rel_mean"] = ra
                spec["b_rel_mean"] = rb
        specs.append(spec)
    # record the agent's Stage-2 design as graph state (the pairs it chose + cues).
    arch = next((a for a in substrate.nodes("RecognizerArchitecture")), None)
    if arch is not None:
        substrate.set_attr(arch, "tiebreak_pairs",
                           [f"{s['A']}/{s['B']}:{s['cue']}" for s in specs])
    return specs


def _cue_mean(substrate, predicate: dict, train_signs, word: str):
    """Mean of the cue's predicate over a word's training clips. `train_signs` is a
    list of (word, sign_node) — the cue reads per-sign band/fft attrs, so it must be
    evaluated on real enriched signs, not on the centroid vector."""
    vals = []
    for w, sign in train_signs:
        if w != word:
            continue
        try:
            vals.append(float(substrate.evaluate(_T(predicate), {"s": sign})))
        except Exception:
            pass
    vals = [v for v in vals if v == v]
    return (sum(vals) / len(vals)) if vals else None


def tiebreak_term(spec: dict) -> dict:
    """Stage-2 tie-break for one pair as a graph Term: pick A when the clip's cue is
    closer to A's cue-mean, else B. The cue used ONLY in the {A,B} context.

      IfThenElse( |cue(s) − a_mean| < |cue(s) − b_mean|,  1 (=A),  0 (=B) )
    """
    cue = spec["predicate"]
    da = {"type": "Abs", "arg": {"type": "Minus", "a": cue,
          "b": {"type": "Lit", "value": float(spec["a_cue_mean"])}}}
    db = {"type": "Abs", "arg": {"type": "Minus", "a": cue,
          "b": {"type": "Lit", "value": float(spec["b_cue_mean"])}}}
    return {"type": "IfThenElse",
            "cond": {"type": "Lt", "a": da, "b": db},
            "then": {"type": "Lit", "value": 1.0},
            "else": {"type": "Lit", "value": 0.0}}


def stage2_decide(substrate, top2, signs, tb_index, relative: bool = False) -> str:
    """When Stage-1's top two are a pair the agent has a contextual tie-break for,
    decide between just those two with the agent's cue — evaluated natively on the
    clip's signs, AVERAGED (the same per-sign-mean the training cue means use, so the
    comparison against the training means is consistent). `signs` is the clip's
    AcousticSigns. Returns the chosen word (or top2[0] if no tie-break applies).

    `relative=True` (lever 2) uses the SPEAKER-RELATIVE form of the same decision when
    the spec has one: the clip's cue minus its own co-moving reference (cue − ref),
    compared against the likewise-referenced training means (a_rel_mean / b_rel_mean).
    The speaker (VTL/level) term cancels in both the clip value and the boundary, so
    the decision survives a speaker change. Falls back to the absolute form when the
    cue has no principled reference."""
    a, b = top2[0], top2[1]
    spec = tb_index.get((a, b)) or tb_index.get((b, a))
    if spec is None:
        return a
    if isinstance(signs, (list, tuple)):
        sg = list(signs)
    elif signs is None:
        return a
    else:
        sg = [signs]
    use_rel = relative and ("rel_predicate" in spec)
    cue = spec["rel_predicate"] if use_rel else spec["predicate"]
    am = spec["a_rel_mean"] if use_rel else spec["a_cue_mean"]
    bm = spec["b_rel_mean"] if use_rel else spec["b_cue_mean"]
    vals = []
    for s in sg:
        try:
            vals.append(float(substrate.evaluate(_T(cue), {"s": s})))
        except Exception:
            pass
    vals = [v for v in vals if v == v]
    if not vals:
        return a
    cval = sum(vals) / len(vals)
    # the agent's tie-break decision (graph form tiebreak_term) over the clip's mean
    # cue: closer to A's mean -> A, else B. Used ONLY in the {A,B} context.
    pick_A = abs(cval - am) < abs(cval - bm)
    return spec["A"] if pick_A else spec["B"]


def two_stage_decide(substrate, arch, clip, gam, fft, signs, words, tb_index,
                     exemplars=None, margin_cut: float | None = None,
                     relative: bool = True):
    """The full two-stage recognizer the agent assembled, with both fixes.

    Stage 1 ranks all words by the both-ears kNN score and reports a confidence margin
    (top1 − top2 summed similarity). Stage 2 applies the agent's contextual tie-break
    to the top two ONLY when (lever 1) Stage 1 is low-confidence — margin below
    `margin_cut` (the data-driven bottom-tertile cut; None = always fire, the old
    behaviour) — and uses the SPEAKER-RELATIVE cue when `relative` (lever 2). When
    Stage 1 is confident, its answer is trusted unchanged. Returns (prediction,
    stage1_top1, margin)."""
    ranked, margin = stage1_rank(substrate, arch, clip, words,
                                 exemplars=exemplars, with_margin=True)
    top1 = ranked[0]
    if margin_cut is not None and margin > margin_cut:
        return top1, top1, margin          # confident — trust Stage 1
    pred = stage2_decide(substrate, (ranked[0], ranked[1]), signs, tb_index,
                         relative=relative)
    return pred, top1, margin


__all__ = ["learn_word_centroids", "stage1_rank", "agent_design_tiebreaks",
           "tiebreak_term", "stage2_decide", "two_stage_decide", "_attach_clip",
           "_reference_term"]
