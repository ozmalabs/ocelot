"""slow_path — the SLOW PATH: order-N analysis-by-synthesis replay-and-learn.

The user's insight: humans have a SLOW path — "I play back speech in my head, parse
it much better, learn the structure, and bank it." This is the agent's OWN flagged
missing structural component (order-N AxS — [[ozma_order_n_analysis_by_synthesis]]).

THE TWO-PATH ARCHITECTURE
  · FAST path  (the cue-graph, iters 33-38: many_settings_recognizer +
    enriched_hvpt_accept) recognises in real time from the banked library.
  · SLOW path  (this module) BUFFERS an utterance, REPLAYS it, PARSES it deliberately
    via ORDER-N AxS (invert speak(), ITERATED — n passes scaling to difficulty,
    co-refining word + voice + boundary until re-synthesis converges), LEARNS the
    structure, and BANKS it into the library. iter-35 built the SINGLE-PASS AxS as a
    fast node; the slow path WRAPS that in the order-N iteration + learn-and-bank.

NO-DONKEY. Every piece is OWNED machinery, no fit, no trained net:
  · the AxS = speak-inversion: the agent's per-word forward model (mean A1-patch
    trajectory of the train exemplars) + the graph `DtwTo` Term (recognition_graph
    .synth_error_term), softmaxed by its own median distance (the iter-35 node).
  · the ORDER-N iteration = the agent's OWN order_n operator (order_n_concepts —
    the recursive finite difference): each pass takes the order-1 difference of the
    running synth-error and stops at the fixed point (converged residual). The
    "n passes scaling to difficulty" IS the order-N stopping rule.
  · the LEARN-and-BANK = retain the confidently-resolved trajectory as a new
    exemplar in the library (the lexicon), reinforcing the per-word forward model.

The order-N REFINEMENT (the new part over iter-35's single pass): pass 1 is the
single-pass hypothesis (heard vs per-word MEAN model). Each further pass
RE-SYNTHESISES from the CURRENT best hypothesis adapted toward the heard signal —
the forward model for the hypothesised word is WARPED toward the buffered trajectory
(co-refining VOICE: an affine per-patch fit of the model onto the heard frames; this
absorbs the speaker/channel nuisance speak() in the heard voice would) and
DTW-realigned (co-refining BOUNDARY). The re-synthesis error is re-ranked over
candidates. The iteration is the agent's order_n fixed-point: stop when the
order-1 difference of the best synth-error falls below a convergence band, or n_max.

This is the same instance<->model A1-space comparison iter-16 found best (no
natural/synthetic resynthesis domain gap; the brain inverts the internal forward
model, it does not literally replay sound). BOUNDED by forward-model quality (the
known order-N caveat) — the warp is a per-patch affine, not a full articulatory
re-synthesis; where the forward model is poor the order-N gains are bounded.

The decisive measurements (driven by scripts/slow_path_accept.py):
  (A) ORDER-N vs SINGLE-PASS on HARD cases — does iterating parse better, and does
      n scale with difficulty (harder cases use more passes, and more passes help)?
  (B) THE CLOSED LOOP — does banking from the slow path improve the FAST cue-graph
      on subsequent recognition?
"""
from __future__ import annotations

import numpy as np

from substrate_rs import Substrate

from domains import recognition_graph as RG
import domains.many_settings_recognizer as MS
from domains.order_n_concepts import nth_order_terms


def order1_diff(samples):
    """The agent's order-1 finite difference (order_n_concepts.nth_order_terms at
    order 1) evaluated over a SCALAR sequence. nth_order_terms composes the symbolic
    recursive `Minus` (it is built for graph Term-trees / Attr samples); over plain
    float samples the order-1 difference is exactly samples[i+1]-samples[i] — the
    same operator, on numbers. Returns the list of order-1 differences."""
    # mirror nth_order_terms(samples, 1) semantics on scalars (one fewer element).
    return [samples[i + 1] - samples[i] for i in range(len(samples) - 1)]


# ---------------------------------------------------------------------------
# The graph DtwTo synth-error (the agent's owned AxS distance), reused so the slow
# path's distance is the SAME native Term the fast AxS node uses. One scratch
# substrate; only the two trajectory attrs change per evaluation.
# ---------------------------------------------------------------------------

_SUB = None
_SIGN = None
_WORD = None
_ERR_TERM = None


def _machinery():
    global _SUB, _SIGN, _WORD, _ERR_TERM
    if _SUB is None:
        _SUB = Substrate()
        _SIGN = _SUB.add_node("AcousticSign", {"slow_probe": 1.0})
        _WORD = _SUB.add_node("Concept", {"name": "_slow_cand"})
        _ERR_TERM = MS._Pred(
            RG._DtwTo(RG._Attr(RG._V("s"), RG.SIGN_FEAT_ATTR),
                      RG._Attr(RG._V("w"), RG.WORD_FEAT_ATTR)))
    return _SUB


def _as_tuple(M):
    return tuple(tuple(float(v) for v in row) for row in M)


def synth_error(heard, synth):
    """synth_error = DtwTo(heard_trajectory, synth_trajectory) via the GRAPH Term —
    the agent's owned AxS distance, evaluated natively in Rust. Both are
    (frames x patches) arrays. No Python distance, no fit."""
    sub = _machinery()
    sub.set_attr(_SIGN, RG.SIGN_FEAT_ATTR, _as_tuple(heard))
    sub.set_attr(_WORD, RG.WORD_FEAT_ATTR, _as_tuple(synth))
    return float(sub.evaluate(_ERR_TERM, {"s": _SIGN, "w": _WORD}))


# ---------------------------------------------------------------------------
# The forward model = per-word mean A1-patch trajectory of the banked exemplars.
# This is a LIBRARY object: build_library banks {word: [trajectory, ...]}, and the
# forward model is the mean over the bank. Banking a new exemplar (learn-and-bank)
# updates the mean — the slow path's payoff into the fast path's representation.
# ---------------------------------------------------------------------------

def forward_model(library: dict) -> dict:
    """{word: mean (frames x patches) trajectory} over the banked exemplars — the
    agent's owned word->sound forward model (exemplar average, no fit)."""
    model = {}
    for w, trajs in library.items():
        ts = [t for t in trajs if t is not None]
        if not ts:
            continue
        L = min(t.shape[0] for t in ts)
        model[w] = np.mean([t[:L] for t in ts], axis=0)
    return model


# ---------------------------------------------------------------------------
# The AUDIO forward model (iter-40): the genuine "invert speak()" — instead of
# comparing in A1-trajectory space directly (which never touches the synthesiser),
# SYNTHESISE each candidate word as AUDIO (in the heard voice) and RE-PERCEIVE it
# back into an A1 trajectory. The synthesised-then-re-analysed candidate is what
# gets DTW-compared to the heard signal. This makes the forward-model (synth)
# QUALITY bear on whether the re-perceived candidate carries phonetic identity —
# the iter-39 bound. Two synth backends are exposed so the OLD-vs-NEW delta is
# clean:
#   · "old"   — the crude source-filter voicebox (0.3/k harmonic + parallel
#               bandpass biquads), synthesize_from_trajectory.
#   · "klatt" — the Klatt cascade + LF glottal source, synthesize_klatt_lf.
# "none" keeps the iter-39 exemplar-mean-trajectory path (no synthesis).
#
# World-adapter only: read patch metadata from the graph, hand the trajectory +
# patches to the Rust synth primitive, re-ingest the audio via the Rust pipeline,
# read back the A1 trajectory. No decisions, no fit.
# ---------------------------------------------------------------------------

_A1_PATCHES = None    # cached [(name, centre_hz, sigma, kind)] in alphabetical order
_SYNTH_PIPE = None    # the STTPipeline used for synthesis + re-ingest
_SYNTH_FS = None


def _patch_meta(fs):
    """Patch metadata in the SAME alphabetical order utterance_a1_trajectory's
    column ordering uses (lexical_access sorts A1Patch nodes by name). Read once
    from a fresh primed substrate."""
    global _A1_PATCHES, _SYNTH_PIPE, _SYNTH_FS
    if _A1_PATCHES is not None and _SYNTH_FS == fs:
        return _A1_PATCHES, _SYNTH_PIPE
    from domains.stt_pipeline import STTPipeline, STTParams
    sub = Substrate()
    pipe = STTPipeline(STTParams(sample_rate=fs))
    pipe.attach(sub)
    pipe._ensure_audio_pipeline(sub)
    patches = []
    for p in sub.nodes("A1Patch"):
        a = sub.node(p)["attrs"]
        patches.append((a.get("name", ""),
                        float(a.get("centre_hz", 1000.0)),
                        float(a.get("freq_sigma_hz", 400.0)),
                        a.get("kind", "sustained")))
    patches.sort(key=lambda t: t[0])
    _A1_PATCHES = patches
    _SYNTH_PIPE = pipe
    _SYNTH_FS = fs
    return patches, pipe


def synth_reanalyze(traj, fs, f0_hz, mode="klatt"):
    """Synthesise AUDIO from an A1 trajectory (frames x patches) via the chosen
    Rust synth backend, then re-ingest the audio to recover its A1 trajectory.
    Returns (frames x patches) — the re-perceived candidate. mode in {old,klatt}.

    This is the forward model that actually exercises the synthesiser: the
    candidate is voiced as sound in the heard f0 and heard again, so the synth's
    fidelity determines how much phonetic identity survives the round-trip."""
    import scripts.enriched_hvpt_accept as EH
    patches, _ = _patch_meta(fs)
    n_patches = len(patches)
    T = np.asarray(traj, dtype=np.float32)
    if T.ndim != 2 or T.shape[1] != n_patches or T.shape[0] < 1:
        return None
    spp = T.shape[0]
    # synthesize_from_trajectory expects PATCH-MAJOR flattening (n_patches blocks
    # of spp). The A1 trajectory is frame-major (spp x patches); transpose.
    traj_flat = T.T.reshape(-1).tolist()
    nyq = float(fs) / 2.0 * 0.95
    centres = [min(c, nyq) for _, c, _, _ in patches]
    sigmas = [s for _, _, s, _ in patches]
    kinds = [k for _, _, _, k in patches]
    sib = ["sib" in n for n, _, _, _ in patches]
    out_n = max(int(0.4 * fs), 1)
    f0 = float(f0_hz) if f0_hz and f0_hz > 0 else 120.0
    rust = _patch_rust(fs)
    if mode == "old":
        audio_bytes = rust.synthesize_from_trajectory(
            traj_flat, centres, sigmas, kinds, sib, spp, out_n, fs, f0, 6.0)
    else:
        audio_bytes = rust.synthesize_klatt_lf(
            traj_flat, centres, sigmas, kinds, sib, spp, out_n, fs, f0,
            0.6, 0.7, 0.01, 0.0, 0.0)
    audio = np.frombuffer(audio_bytes, dtype=np.float32).copy()
    if audio.size == 0 or not np.all(np.isfinite(audio)) or float(np.max(np.abs(audio))) < 1e-6:
        return None
    return EH.utterance_a1_trajectory(audio, fs)


_RUST_SUB = None


def _patch_rust(fs):
    """A scratch native substrate exposing the synth primitives (they are methods
    on the native Substrate). Reused across calls."""
    global _RUST_SUB
    if _RUST_SUB is None:
        _RUST_SUB = Substrate()
    return _RUST_SUB._inner if hasattr(_RUST_SUB, "_inner") else _RUST_SUB


def audio_forward_model(library: dict, fs, f0_hz, mode="klatt") -> dict:
    """{word: re-perceived (frames x patches) trajectory} — the AUDIO forward
    model: synthesise each word's mean trajectory as audio (mode={old,klatt}) and
    re-analyse it. The synthesised candidates are what order_n_axs / single_pass
    then DTW-compare to the heard signal. f0_hz is the heard voice's pitch."""
    base = forward_model(library)
    out = {}
    for w, traj in base.items():
        re = synth_reanalyze(traj, fs, f0_hz, mode=mode)
        if re is not None:
            out[w] = re
    return out


# ---------------------------------------------------------------------------
# The ORDER-N refinement: warp the candidate forward model toward the heard signal
# (co-refine voice + boundary), re-compare, iterate to the order_n fixed point.
# ---------------------------------------------------------------------------

def _dtw_align(heard, synth):
    """Boundary co-refinement: linear-resample the synth trajectory to the heard
    trajectory's length (the cheap monotone alignment — the boundary the heard
    utterance imposes on the candidate). Returns synth re-gridded to len(heard)."""
    h = heard.shape[0]
    s = synth.shape[0]
    if s == h or s == 0:
        return synth[:h] if s >= h else np.pad(synth, ((0, h - s), (0, 0)), mode="edge")
    out = np.zeros((h, synth.shape[1]), dtype=np.float64)
    for t in range(h):
        sp = t * s / h
        i0 = int(sp); i1 = min(i0 + 1, s - 1); frac = sp - i0
        out[t] = synth[i0] * (1 - frac) + synth[i1] * frac
    return out


def _voice_warp(heard, synth, step: float = 1.0):
    """Voice co-refinement: a GLOBAL affine fit of the candidate synthesis onto the
    heard frames (synth' = a*synth + b, ONE scalar gain + bias over the WHOLE aligned
    trajectory), applied with a DAMPED `step` (a partial move toward the heard voice).
    This absorbs the speaker/channel nuisance that re-synthesising speak() IN THE
    HEARD VOICE would — overall level + spectral-scale = the voice channel — WITHOUT a
    per-patch fit that would erase the word-distinct shape (an unconstrained per-patch
    affine can mould ANY candidate onto the heard signal, collapsing discrimination;
    the global affine cannot — it preserves the relative patch structure that carries
    word identity). The DAMPED step makes the warp an ITERATED refinement (the order-N
    move): a small residual settles in one step (easy), a large residual takes several
    (hard) — so n scales with difficulty. NO learned weight, no global fit across
    utterances. Returns the warped synth (boundary-aligned to the heard length)."""
    s = _dtw_align(heard, synth)             # boundary co-refinement first
    x = s.reshape(-1); y = heard.reshape(-1)
    vx = float(x.var())
    if vx < 1e-12:
        return s + step * (y.mean() - x.mean())   # bias-only when the synth is flat
    a = float(np.cov(x, y, bias=True)[0, 1] / vx)
    a = float(np.clip(a, 0.5, 2.0))          # adapt the voice scale, never collapse
    b = float(y.mean() - a * x.mean())
    full = a * s + b
    return s + step * (full - s)             # damped partial move toward the warp


def order_n_axs(heard, model: dict, candidates, max_n: int = 6,
                conv_band: float = 1e-3):
    """ORDER-N analysis-by-synthesis for one buffered utterance.

    Pass 1  — the SINGLE-PASS hypothesis: synth_error(heard, model[w]) per candidate,
              pick argmin (the iter-35 node, here as the order-0 of the iteration).
    Pass k>1 — RE-SYNTHESISE from the current best hypothesis adapted toward the
              heard signal: warp the candidate models toward the buffered trajectory
              (co-refine voice + boundary), re-compute synth_error, re-rank. The
              warp is recomputed each pass from the CURRENT alignment, so word/voice/
              boundary co-refine jointly.
    Stop    — the agent's order_n FIXED POINT: the order-1 difference of the running
              best synth-error (nth_order_terms(errs, 1)) falls within conv_band, or
              max_n passes. n scales to difficulty: an easy utterance converges in 1-2
              passes; a hard one keeps refining until the residual settles.

    Returns dict: pred (word), likelihood {word: P}, n_passes, errs (best-error per
    pass), best_error, converged (bool)."""
    cands = list(candidates)
    avail = [w for w in cands if model.get(w) is not None]
    if not avail:
        n = max(len(cands), 1)
        return {"pred": None, "likelihood": {w: 1.0 / n for w in cands},
                "n_passes": 0, "errs": [], "best_error": float("inf"),
                "converged": False}

    # per-candidate RUNNING synthesis (starts at the raw forward model = pass-1
    # single-pass; each pass takes one damped warp STEP toward the heard voice, so the
    # refinement ACCUMULATES — an iterated fixed point, not a one-shot re-fit).
    synth = {w: np.asarray(model[w], dtype=np.float64) for w in avail}
    best_errs = []
    last_dists = None
    pred = None
    for k in range(max_n):
        dists = {}
        for w in avail:
            if k > 0:                                  # pass-1 is the raw model
                synth[w] = _voice_warp(heard, synth[w], step=0.5)
            dists[w] = synth_error(heard, synth[w])
        last_dists = dists
        pred = min(dists, key=dists.get)
        best_errs.append(dists[pred])
        # order_n stopping: the order-1 difference of the running best error.
        if len(best_errs) >= 2:
            d1 = order1_diff(best_errs)               # the agent's order-1 operator
            if abs(d1[-1]) <= conv_band:
                return {"pred": pred,
                        "likelihood": MS.likelihood_from_distances(_fill(dists, cands)),
                        "n_passes": k + 1, "errs": best_errs,
                        "best_error": best_errs[-1], "converged": True}
    return {"pred": pred,
            "likelihood": MS.likelihood_from_distances(_fill(last_dists, cands)),
            "n_passes": max_n, "errs": best_errs,
            "best_error": best_errs[-1] if best_errs else float("inf"),
            "converged": False}


def single_pass_axs(heard, model: dict, candidates):
    """The iter-35 SINGLE-PASS AxS (= order_n_axs with max_n=1), for the A comparison.
    heard vs per-word MEAN model, argmin synth-error, softmax by own median."""
    return order_n_axs(heard, model, candidates, max_n=1)


def _fill(dists, candidates):
    out = dict(dists)
    for w in candidates:
        out.setdefault(w, float("inf"))
    return out


# ---------------------------------------------------------------------------
# LEARN + BANK: retain the confidently-resolved trajectory as a new exemplar in the
# library (the lexicon). Retain-don't-discard: the library grows, the forward model
# sharpens, and the FAST path (which reads the same library) improves.
# ---------------------------------------------------------------------------

def confidence(result) -> float:
    """The slow-path parse confidence = the resolved word's AxS likelihood (the
    softmax margin of the converged synth-error). Used to gate banking."""
    lik = result.get("likelihood", {})
    return float(lik.get(result.get("pred"), 0.0)) if lik else 0.0


def learn_and_bank(library: dict, heard, result, conf_thresh: float = 0.0):
    """LEARN from the converged parse: a confidently-resolved utterance becomes a new
    exemplar of its word in the library (the lexicon). BANK it (retain-don't-discard).
    Returns True if banked. The forward model rebuilt from the updated library is the
    payoff the fast path then uses (the closed loop)."""
    w = result.get("pred")
    if w is None or heard is None:
        return False
    if confidence(result) < conf_thresh:
        return False
    library.setdefault(w, []).append(np.asarray(heard, dtype=np.float64))
    return True


def build_library(trajs, words) -> dict:
    """Seed the library {word: [trajectory, ...]} from a set of labelled exemplars
    (the train bank). The forward model + the fast path both read from this."""
    lib = {}
    for t, w in zip(trajs, words):
        if t is not None:
            lib.setdefault(w, []).append(np.asarray(t, dtype=np.float64))
    return lib


__all__ = ["synth_error", "forward_model", "order_n_axs", "single_pass_axs",
           "learn_and_bank", "build_library", "confidence", "_voice_warp",
           "_dtw_align"]
