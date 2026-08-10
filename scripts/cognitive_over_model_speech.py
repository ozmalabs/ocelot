"""THE COGNITIVE LEVEL over the MODEL SPINE — a SECOND native_collapse plug, at the WORD/MEANING grain,
GROUNDED THROUGH the model layer (NOT a parallel layer).

The creator's architecture: speech cognition is >=2 LOOPED-BACK layers — a COGNITIVE layer (meaning/intent/
word) PREDICTS a MODEL layer (gestural form) PREDICTS sensory acoustic, the whole stack grounded BOTTOM-UP by
external reality. The MODEL layer is built+validated (commit 0eab0937, scripts/one_model_looped_back_speech.py
+ speech_one_model_plug.py): M = render_dynamic (a gestural plan = phone-sequence -> a coarticulated acoustic
trajectory) + the held DtwTo inversion; its inventory theta is grounded externally by the held collapse
cognition. THIS file builds the COGNITIVE layer OVER it.

THE COGNITIVE LAYER IS THE SAME native_collapse FACULTY, ONE GRAIN UP (the recurring lesson — reuse, do not
build a parallel layer). The lower model-layer plug collapses a PHONE/acoustic manifold; the cognitive plug
collapses a WORD/construction manifold. Symbols = WORDS; sequences = the real word-stream (LibriSpeech reading
order = real language structure); the next-symbol predictor = the agent's HELD language faculty (a counted
word-transition / construction prior, grown by on_gap = grow Gamma). It is a SECOND DomainPlug into the SAME
held run_collapse, COUPLED to the model-layer plug.

THE COUPLING — cognition grounds THROUGH the model (the whole point):
  TOP-DOWN : the cognitive layer predicts the next WORD from context (the word-transition prior) -> the
             expected FORM (word -> phone-sequence, the held lexicon) -> the MODEL layer renders it (M).
  BOTTOM-UP: the real acoustic is inverted by the MODEL layer (M-inversion = held DtwTo over candidate word
             renders) -> a recovered WORD. The cognitive layer recovers MEANING by combining the model's
             acoustic evidence with its word-context prior (the manifold log-weight = acoustic-evidence +
             learned-prior, exactly native_collapse's BETA*agree + seq_lp form, one grain up).
  GROUNDED : the cognitive prediction is grounded when the model-recovered word matches the intent (the true
             word). SURPRISE = the held native term on the cognitive confidence at the true word; it falls as
             the model grounds (the model recovers words better -> the cognitive posterior sharpens). A word
             the model+prior cannot recover is a GAP -> on_gap LEARNS it (grow the lexicon + the transition).
  The cognitive layer is grounded THROUGH the model, NOT directly on acoustics: its 'observation' is the
  model's recovered word.

THE FALSIFIABLE GATES (mirroring the model spine, donkey=0):
  MAIN — GROUNDED-THROUGH-THE-MODEL: with the model layer GROUNDED (theta*), the cognitive layer grounds —
         word-level surprise falls, comprehension rises, the lexicon grows + word-transitions (constructions)
         emerge via the held run_collapse.
  DECISIVE ABLATION — MODEL-BYPASSED: with the model layer DEGENERATE (theta = the global mean, every word
         renders identically -> M cannot discriminate -> the acoustic evidence is uninformative), the
         cognitive layer can only guess from context, NOT ground on what was actually said -> surprise stays
         high, comprehension collapses toward prior-only. If cognition grounds even when the model is
         bypassed, the hierarchy claim FAILS. (Reported honestly either way.)
  TOP-DOWN HELPS (the hierarchy's bidirectional payoff): the cognitive word/context prior IMPROVES the model
         layer's recognition vs the model ALONE (lexical context disambiguates acoustically-confusable words).
  COLLAPSE-GROUNDING (cognitive grain): the held run_collapse drives word-level surprise->0 — pass-1 GAPS are
         the word-transitions the prior mispredicts, on_gap learns them, pass-2 GAPS -> ~0.

donkey=0: the cognitive predictor = the held language faculty (counted word-transition structure, grown by
on_gap = grow Gamma); GROUNDING = the held run_collapse + native_collapse SURPRISE term (evaluated in Rust);
the model inversion = the held DtwTo Term; the posterior/softmax is a numpy-adapter MEASUREMENT (as in every
held AbS script), the SURPRISE on it is the held native term. No LLM, no borrowed net, no gradient. XTTS unused.

Run (smoke): PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/cognitive_over_model_speech.py [--quick]
"""
from __future__ import annotations
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
from collections import Counter, defaultdict

import substrate_rs as _srs
from collapse_engine import DomainPlug, run_collapse
from scripts.native_collapse import native_surprise
from scripts.jabberwock_subword_recognizer import _load_ph
from scripts.dynamic_sequence_speech_abs import render_dynamic, dtw, majority_lexicon, FUNC
from scripts.speech_one_model_plug import collect_targets_few, ground_targets

# one held substrate for the native SURPRISE term (the cognition runs in Rust).
_S = _srs.Substrate()


# ============================================================================
# THE COGNITIVE DomainPlug — a SECOND plug into the HELD run_collapse, at the
# WORD grain. Mirror of scripts/speech_one_model_plug.make_speech_plug, but the
# opaque symbols are WORDS and the sequences are real word-streams. next_dist is
# the agent's learned word-transition (construction) prior with a generalisation
# fallback; on_gap LEARNS the word transition (grow Gamma). This IS the agent's
# held language faculty as the cognitive PREDICTOR.
# ============================================================================

def make_cognitive_plug(model, sequences, top_word):
    """A word-grain DomainPlug. `sequences` are real word-sequences (sentences in
    reading order). next_dist is the learned word-transition prior; an UNLEARNED
    context backs off to the GENERALISATION prior (the globally-commonest word).
    on_gap counts the real transition (grow Gamma = learn the construction).
    `model` (a dict, the graph-resident counts) starts EMPTY and is grown here."""
    seqs = [tuple(s) for s in sequences if len(s) >= 2]

    def next_dist(ctx):
        if len(ctx) < 1:
            return {}
        b = ctx[-1]
        if b in model and model[b]:                          # LEARNED transition (counts)
            tot = sum(model[b].values())
            return {o: n / tot for o, n in model[b].items()}
        return {top_word: 1.0}                                # GENERALISATION prior (wrong at most)

    def on_gap(ctx, missing):                                 # LEARN: count the transition (grow Gamma)
        b = ctx[-1]
        model.setdefault(b, {}).setdefault(missing, 0)
        model[b][missing] += 1

    return DomainPlug(name="cognitive_words", pool=seqs, train=seqs, targets=seqs,
                      seq_logprob=lambda seq: 0.0, next_dist=next_dist, on_gap=on_gap)


def cognitive_collapse(sequences):
    """Run the HELD collapse loop at the WORD grain. PASS 1: the generalisation prior mispredicts most
    word-transitions -> run_collapse localises the GAPS and on_gap learns them (the lexicon of transitions /
    constructions emerges). PASS 2: the model explains every transition -> ~0 gaps. Returns the GROWN word
    model + (gaps_pass1, gaps_pass2, transitions_learned)."""
    top_word = Counter(w for s in sequences for w in s).most_common(1)[0][0]
    model = {}
    plug = make_cognitive_plug(model, sequences, top_word)
    seq_lp = {s: 0.0 for s in plug.pool}
    r1 = run_collapse(plug, seq_lp)
    learned = sum(len(v) for v in model.values())
    r2 = run_collapse(plug, seq_lp)
    return model, len(r1.gaps), len(r2.gaps), learned


# ============================================================================
# THE COUPLING — cognition grounds THROUGH the model. For each word position the
# MODEL layer (M-inversion = held DtwTo over candidate word renders) supplies the
# acoustic evidence; the cognitive word-prior supplies the top-down context. The
# manifold log-weight lw = acoustic-evidence + learned-prior (exactly native_
# collapse's BETA*agree + seq_lp, one grain up). The posterior softmax is a numpy
# adapter MEASUREMENT; the SURPRISE on it is the held native term.
# ============================================================================

def _templates(vocab, lexicon, theta, durs):
    gm = np.mean(list(theta.values()), 0)
    dm = float(np.mean(list(durs.values())))
    return [render_dynamic(lexicon[w], theta, durs, gm, dm).tolist() for w in vocab]


def _prior_over_vocab(ctx, model, vocab, top_word, uni=None, floor=1e-3):
    """The cognitive top-down: the learned word-transition (bigram) prior restricted+renormalised to the
    candidate vocabulary (a small floor so an unseen-in-context vocab word is not impossible). An UNLEARNED
    context backs off — the held language faculty's n-gram back-off — to the UNIGRAM word-frequency
    distribution (which TRANSFERS across books) when supplied, else to the generalisation prior (top_word).
    This is the same counted back-off the native_collapse scorer uses, one grain up."""
    b = ctx[-1] if ctx else None
    raw = model.get(b, {}) if b is not None else {}
    if raw:
        p = np.array([raw.get(w, 0.0) + floor for w in vocab], float)
    elif uni:
        p = np.array([uni.get(w, 0.0) + floor for w in vocab], float)   # unigram back-off (transferable)
    else:
        p = np.array([(1.0 if w == top_word else 0.0) + floor for w in vocab], float)
    return p / p.sum()


def coupled_comprehension(utterances, vocab, lexicon, theta, durs, model, top_word,
                          uni=None, lam=1.0, acoustic_scale=None):
    """Process real utterances (word-sequences with real per-word audio). At each in-vocab position the
    cognitive manifold log-weight (exactly native_collapse's BETA*agree + seq_lp, one grain up) is
       lw(word) = la(word)  +  lam * log prior(word)
         la(word) = -(DTW(real frames, M-render(word)) - min) / scale   [the MODEL acoustic evidence]
         prior    = the cognitive word-transition prior over the vocab given the gold context
       posterior = softmax(lw)                                          [meaning recovered THROUGH M]
    In the MODEL-BYPASSED case M cannot discriminate (degenerate theta -> every DTW equal -> la == 0), so
    lw = lam*log prior and the posterior collapses to the prior alone — it cannot ground on what was said.
    Returns model_alone_acc (acoustic only), coupled_acc (acoustic+prior), prior_alone_acc (context only),
    surprise (held native term on the posterior confidence at the TRUE word), n positions."""
    templ = _templates(vocab, lexicon, theta, durs)
    vidx = {w: i for i, w in enumerate(vocab)}
    n = ma_ok = cp_ok = pri_ok = 0
    tot_sur = 0.0
    for utt in utterances:
        ctx = []
        for (w, fr) in utt:
            if w in vidx:
                O = np.asarray(fr, float).tolist()
                d = np.array([dtw(O, T) for T in templ])
                sc = acoustic_scale if acoustic_scale is not None else max(float(d.std()), 1e-6)
                la = -(d - d.min()) / sc                                  # MODEL acoustic log-evidence
                pri = _prior_over_vocab(ctx, model, vocab, top_word, uni)  # cognitive top-down prior
                lp = np.log(pri)
                lw = la + lam * lp                                        # manifold log-weight (BETA*agree+seq_lp)
                post = np.exp(lw - lw.max()); post = post / post.sum()    # posterior, grounded THROUGH M
                ti = vidx[w]
                ma_ok += int(la.argmax() == ti)                          # model alone (acoustic)
                cp_ok += int(lw.argmax() == ti)                          # coupled 2-level
                pri_ok += int(lp.argmax() == ti)                         # prior alone (context only)
                tot_sur += native_surprise(_S, float(post[ti]))          # held native SURPRISE term
                n += 1
            ctx.append(w)                                                # gold context (all words)
    n = max(n, 1)
    return {"model_alone_acc": ma_ok / n, "coupled_acc": cp_ok / n, "prior_alone_acc": pri_ok / n,
            "surprise": tot_sur / n, "n": n}


# ---------------------------------------------------------------- data helpers ----------------
def _ordered_stream(words):
    """The ordered word-stream (LibriSpeech reading order) with per-word real frames. (word, frames)."""
    return [(w, fr) for (w, fr, _ph) in words]


def _windows(stream, L):
    """Chunk the ordered stream into L-word windows = the cognitive word-sequences / pseudo-sentences."""
    return [stream[i:i + L] for i in range(0, len(stream), L) if len(stream[i:i + L]) >= 2]


# ---------------------------------------------------------------- driver ----------------------
def main():
    quick = "--quick" in sys.argv
    t0 = time.time()
    rng = np.random.default_rng(0)
    print("=" * 98)
    print("COGNITIVE LEVEL over the MODEL SPINE — a 2nd native_collapse plug (word grain), grounded THROUGH M")
    print("=" * 98, flush=True)

    cal = _load_ph("train-clean-100_*.pkl", 4 if quick else 10)
    dev = _load_ph("dev-clean_*.pkl", 3 if quick else 8)
    lexicon = majority_lexicon(cal + dev)
    print(f"  ordered stream: cal={len(cal)} words  dev={len(dev)} words   [{time.time()-t0:.0f}s]", flush=True)

    # ---- candidate vocabulary: content words with enough dev exemplars (the meaning units) -------------
    dev_count = Counter(w for w, _f, _p in dev)
    vocab = sorted([w for w, c in dev_count.items()
                    if w not in FUNC and len(w) >= 4 and c >= (4 if quick else 6) and w in lexicon])
    vocab = vocab[: (18 if quick else 28)]
    print(f"  candidate vocabulary (meaning units): {len(vocab)} words  (chance {1.0/len(vocab):.3f})  "
          f"e.g. {vocab[:6]}", flush=True)

    # ---- MODEL layer: seed theta from a few cal words, GROUND it on the real cal stream (held cognition) -
    N0 = 8 if quick else 12
    seed = [cal[i] for i in rng.permutation(len(cal))[:N0]]
    theta0, durs0 = collect_targets_few(seed)
    NG = 200 if quick else 500
    ground_words = cal[:NG]
    theta_star, durs_star, acoustic_traj = ground_targets(theta0, durs0, ground_words, passes=3, sigma=2.0)
    # the DEGENERATE (model-bypassed) inventory: every phone collapses to the global mean -> M cannot
    # discriminate words (the acoustic evidence is uninformative). durs kept so renders are well-formed.
    gm = np.mean(list(theta_star.values()), 0)
    theta_deg = {p: gm.copy() for p in theta_star}
    print(f"  MODEL layer: theta_0 {len(theta0)} phones -> grounded theta* {len(theta_star)} phones "
          f"(acoustic surprise {acoustic_traj[0]:.3f}->{acoustic_traj[-1]:.3f});  degenerate theta = global "
          f"mean   [{time.time()-t0:.0f}s]", flush=True)

    # ---- COGNITIVE layer: the held language faculty learns word-transitions via the held run_collapse ---
    cal_seqs = _windows([w for w, _f, _p in cal], 8)
    model, g1, g2, learned = cognitive_collapse(cal_seqs)
    cal_words = [w for w, _f, _p in cal]
    top_word = Counter(cal_words).most_common(1)[0][0]
    uni = Counter(cal_words)                                   # unigram back-off (held faculty, transferable)
    print(f"\n  --- COLLAPSE-GROUNDING (cognitive/word grain, held run_collapse) ---", flush=True)
    print(f"  pass-1 word-transition GAPS={g1} (the prior mispredicts -> on_gap LEARNED {learned} "
          f"transitions/constructions);  pass-2 GAPS={g2} (the word model explains every transition)",
          flush=True)

    # ---- test stream: the ordered dev stream as ONE running context (gold context + real per-word audio).
    # Every vocab occurrence is a scored position (maximising n); the bigram prior reads the preceding word.
    dev_stream = _ordered_stream(dev)
    if quick:
        dev_stream = dev_stream[:3000]
    test_utts = [dev_stream]

    # ============================ MAIN — GROUNDED THROUGH THE MODEL ================================
    print("\n  --- MAIN: cognitive layer grounds THROUGH the GROUNDED model (theta*) ---", flush=True)
    # surprise BEFORE model grounding (theta_0) vs AFTER (theta*): cognition grounds THROUGH the model, so
    # improving the lower model layer must lower the cognitive surprise.
    g_before = coupled_comprehension(test_utts, vocab, lexicon, theta0, durs0, model, top_word, uni)
    g_after = coupled_comprehension(test_utts, vocab, lexicon, theta_star, durs_star, model, top_word, uni)
    print(f"  cognitive SURPRISE (held native term) : theta_0 {g_before['surprise']:.3f}  ->  "
          f"theta* {g_after['surprise']:.3f}   (falls as the MODEL grounds)")
    print(f"  comprehension (coupled)               : theta_0 {g_before['coupled_acc']:.3f}  ->  "
          f"theta* {g_after['coupled_acc']:.3f}   (rises as the MODEL grounds)")
    print(f"  scored positions n={g_after['n']}  (chance {1.0/len(vocab):.3f})   [{time.time()-t0:.0f}s]",
          flush=True)

    # ============================ DECISIVE ABLATION — MODEL-BYPASSED ===============================
    print("\n  --- DECISIVE ABLATION: the cognitive layer with the MODEL BYPASSED (degenerate theta) ---",
          flush=True)
    g_bypass = coupled_comprehension(test_utts, vocab, lexicon, theta_deg, durs_star, model, top_word, uni)
    print(f"  GROUNDED-THROUGH-MODEL : surprise {g_after['surprise']:.3f}   comprehension "
          f"{g_after['coupled_acc']:.3f}")
    print(f"  MODEL-BYPASSED         : surprise {g_bypass['surprise']:.3f}   comprehension "
          f"{g_bypass['coupled_acc']:.3f}   (collapses toward prior-only {g_bypass['prior_alone_acc']:.3f})")
    bypass_fails = (g_bypass['surprise'] > g_after['surprise'] + 0.05) and \
                   (g_after['coupled_acc'] > g_bypass['coupled_acc'] + 0.05)
    print(f"  => cognition grounds ONLY THROUGH the model (bypass fails): {bypass_fails}   "
          f"[{time.time()-t0:.0f}s]", flush=True)

    # ============================ TOP-DOWN HELPS ===================================================
    print("\n  --- TOP-DOWN HELPS: the cognitive prior improves the model's recognition ---", flush=True)
    top_down_helps = g_after['coupled_acc'] > g_after['model_alone_acc'] + 1e-9
    print(f"  model-ALONE recognition (acoustic only)        : {g_after['model_alone_acc']:.3f}")
    print(f"  COUPLED 2-level (acoustic + cognitive prior)   : {g_after['coupled_acc']:.3f}")
    print(f"  => the cognitive word/context prior disambiguates the form: {top_down_helps} "
          f"(+{g_after['coupled_acc']-g_after['model_alone_acc']:+.3f})   [{time.time()-t0:.0f}s]", flush=True)

    # ============================ VERDICT =========================================================
    main_grounds = (g_after['surprise'] < g_before['surprise'] - 0.02) and \
                   (g_after['coupled_acc'] > g_before['coupled_acc'] + 0.01)
    collapse_ok = (g1 > 0) and (g2 <= max(1, int(0.05 * g1))) and (learned > 0)
    print("\n" + "=" * 98)
    print("  VERDICT:")
    print(f"    MAIN — grounded THROUGH the model (surprise falls, comprehension rises as M grounds) => "
          f"{'HOLDS' if main_grounds else 'PARTIAL'}")
    print(f"    DECISIVE — model-bypassed FAILS to ground (surprise stays high, comprehension collapses) => "
          f"{'HOLDS' if bypass_fails else 'FAILS (hierarchy claim broken)'}")
    print(f"    TOP-DOWN HELPS — cognitive prior improves the model's recognition                       => "
          f"{'HOLDS' if top_down_helps else 'NULL'}")
    print(f"    COLLAPSE-GROUNDING (word grain: surprise->0, lexicon/constructions emerge)             => "
          f"{'HOLDS' if collapse_ok else 'PARTIAL'}")
    print(f"    donkey=0: predictor=held language faculty (counted word-transitions, grown by on_gap); "
          f"GROUNDING=held run_collapse + native SURPRISE term; inversion=held DtwTo; no LLM/net/gradient.")
    print("=" * 98, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
