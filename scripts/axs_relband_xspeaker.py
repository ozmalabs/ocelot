"""axs_relband_xspeaker — GROUND the agent's chosen move: ANALYSIS-BY-SYNTHESIS in
the CONFIRMED relational-invariant representation (REL-BAND).

THE AGENT'S CHOICE (auditable, from its own machinery — scripts/agent_improves_
speech_decide.py): its gap_prioritiser ranking placed ANALYSIS-BY-SYNTHESIS /
forward-model / internal-synthesiser at the TOP of its compression ranking
(payoff=4, unifying speech_perception, perception_production_link, acoustic_cues,
generative_collapse_recovery_inverts_production). The held postulate
generative_collapse_recovery_inverts_production: "recovering causes from effects
is an INVERSE problem that needs a FORWARD model (articulation->acoustics) to
invert — an internal synthesiser the loop can run and match against."

THE MOVE, AND WHY IT IS NEW: the prior A-by-S (scripts/analysis_by_synthesis_
accept.py) inverted production in A1-PATCH space. But the agent's CONFIRMED decoder
is REL-BAND (relational band-rank + whole-unit self-similarity, domains/
relational_shape). The faithful inversion of production is in the SAME invariant
representation the decoder confirmed — so the forward model is the per-word
CANONICAL relational shape (the production process collapsed onto the carrier,
read in the invariant space), and recognition INVERTS it.

  forward_model(w) = mean over train-speaker exemplars of relational_shape(w)
                     = the word's canonical relational structure (production
                       collapsed onto the carrier, in the invariant space)
  recognise(s)     = argmax_w  - DtwTo( relational_shape(s), forward_model(w) )

This compares the heard instance to a CANONICAL SYNTHESIS (instance<->model), not
to other instances (instance<->instance). Per the postulate, per-speaker /
coarticulation nuisance is absorbed into the forward model, so the residual is
dominated by phonetic identity — the structural reason it should beat 1-NN cross-
speaker and possibly push the ~10-20-word wall. The DECISION is the agent's native
graph Term (recognition_graph.predict_synth_term: Argmax over word Concepts of
-DtwTo) — counts not nets, no .fit. The representation is the agent's owned
composed Term-trees (domains/relational_shape), evaluated natively.

ARMS (same exemplars, same native DtwTo, same LOSO speaker split):
  A  REL-BAND 1-NN   instance<->instance: the CONFIRMED decoder, the baseline to beat.
  B  AxS-REL-BAND    instance<->model: THE AGENT'S MOVE (per-word mean rel-shape
                     forward model, argmax -DtwTo, native graph decision).
  C  AxS-SHUFFLE     forward-model labels permuted -> must collapse to chance.

Run: python -m scripts.axs_relband_xspeaker [n_words] [n_train] [n_test] [n_anchors]
"""
from __future__ import annotations

import os
import sys
import time
import random
from collections import defaultdict

import numpy as np

sys.path.insert(0, '/home/matt/ozma/internal/research/experiments/gamma-substrate')

from substrate_rs import Substrate
from scripts.relational_shape_xspeaker import load_real, as_tuple
from scripts.invariant_units_accept import band_trajectory_matrix
from domains.relational_shape import relational_shape
from domains import recognition_graph as RG

SC = "/tmp/sc"


class _Pred:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def main():
    n_words = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    n_train = int(sys.argv[2]) if len(sys.argv) > 2 else 400
    n_test = int(sys.argv[3]) if len(sys.argv) > 3 else 400
    n_anchors = int(sys.argv[4]) if len(sys.argv) > 4 else 6
    random.seed(1)
    np.random.seed(1)
    t0 = time.time()

    avail = [w for w in sorted(os.listdir(SC))
             if os.path.isdir(os.path.join(SC, w)) and not w.startswith("_")
             and len([f for f in os.listdir(os.path.join(SC, w))
                      if f.endswith(".wav")]) > 200]
    words = avail[:n_words]
    chance = 1.0 / len(words)
    print("=" * 74, flush=True)
    print("ANALYSIS-BY-SYNTHESIS in REL-BAND space — cross-speaker Speech Commands",
          flush=True)
    print("=" * 74, flush=True)
    print(f"{len(words)}-way: {words}  (chance {100*chance:.1f}%)", flush=True)

    data = {}
    for w in words:
        for fn in sorted(os.listdir(os.path.join(SC, w))):
            if fn.endswith(".wav"):
                data.setdefault(w, []).append(
                    (os.path.join(SC, w, fn), fn.split("_")[0]))

    # Hold out whole SPEAKERS for test (train/test speakers DISJOINT) — same split
    # rule as the confirmed REL-BAND baseline (relational_shape_xspeaker).
    test_spk = set()
    for w in words:
        spks = sorted({s for _, s in data[w]})
        test_spk |= set(spks[::6])
    train = [(p, w, s) for w in words for p, s in data[w] if s not in test_spk]
    test = [(p, w, s) for w in words for p, s in data[w] if s in test_spk]
    random.shuffle(train)
    random.shuffle(test)
    train, test = train[:n_train], test[:n_test]
    print(f"train exemplars {len(train)} (disjoint speakers); "
          f"test {len(test)} from HELD-OUT speakers", flush=True)
    print(f"per-clip resolution: {100.0/max(len(test),1):.3f}%  "
          f"(n_anchors={n_anchors})", flush=True)

    def band_M(path):
        x, fs = load_real(path)
        M = band_trajectory_matrix(x, fs)
        return M if M is not None and len(M) >= 2 else None

    print(f"\nextracting band matrices ({time.time()-t0:.0f}s)...", flush=True)
    tr_band = [(band_M(p), w) for p, w, s in train]
    te_band = [(band_M(p), w) for p, w, s in test]
    tr_band = [(M, w) for M, w in tr_band if M is not None]
    te_band = [(M, w) for M, w in te_band if M is not None]
    print(f"  usable: {len(tr_band)} train, {len(te_band)} test "
          f"({time.time()-t0:.0f}s)", flush=True)

    # Compose the agent's CONFIRMED relational shape for every clip (native eval).
    print("composing RELATIONAL shapes (native substrate.evaluate)...", flush=True)
    tr_rel = [(relational_shape(M, n_anchors=n_anchors), w) for M, w in tr_band]
    te_rel = [(relational_shape(M, n_anchors=n_anchors), w) for M, w in te_band]
    tr_rel = [(R, w) for R, w in tr_rel if R is not None and len(R) >= 2]
    te_rel = [(R, w) for R, w in te_rel if R is not None and len(R) >= 2]
    print(f"  relational shapes composed: {len(tr_rel)} train, {len(te_rel)} test "
          f"({time.time()-t0:.0f}s)", flush=True)

    sub = Substrate()
    sign = sub.add_node("HeardSign", {})
    # native 1-NN DtwTo error over a (sign.rep, exemplar.rep) pair (ARM A)
    nn_err = _Pred(RG._DtwTo(RG._Attr(RG._V("s"), "rep"),
                             RG._Attr(RG._V("w"), "rep")))

    # ---- ARM A: REL-BAND 1-NN (the CONFIRMED decoder, instance<->instance) ----
    def run_1nn(tr_reprs, te_reprs, shuffle=False):
        ex_words = [w for _, w in tr_reprs]
        if shuffle:
            ex_words = list(ex_words)
            random.Random(7).shuffle(ex_words)
        exs = []
        for (M, _), w in zip(tr_reprs, ex_words):
            c = sub.add_node("Exemplar", {"word": w})
            sub.set_attr(c, "rep", as_tuple(M))
            exs.append((c, w))
        corr = tot = 0
        per_word = defaultdict(lambda: [0, 0])
        for M, w in te_reprs:
            sub.set_attr(sign, "rep", as_tuple(M))
            best_d, best_w = 1e18, None
            for c, ew in exs:
                d = sub.evaluate(nn_err, {"s": sign, "w": c})
                if d < best_d:
                    best_d, best_w = d, ew
            ok = int(best_w == w)
            corr += ok
            tot += 1
            per_word[w][0] += ok
            per_word[w][1] += 1
        for c, _ in exs:
            sub.remove_node(c)
        acc = corr / max(tot, 1)
        se = (acc * (1 - acc) / max(tot, 1)) ** 0.5
        return acc, se, corr, tot, dict(per_word)

    print("\n" + "=" * 74, flush=True)
    print("ARM A — REL-BAND 1-NN (CONFIRMED decoder, instance<->instance)", flush=True)
    print("=" * 74, flush=True)
    a_acc, a_se, a_c, a_t, a_pw = run_1nn(tr_rel, te_rel)
    print(f"[REL-BAND 1-NN]  {a_c}/{a_t} = {100*a_acc:.2f}%  "
          f"(SE {100*a_se:.2f}%, chance {100*chance:.1f}%)", flush=True)

    # ---- build the FORWARD MODEL: per-word CANONICAL relational shape ----
    # The production process collapsed onto the carrier, in the invariant space:
    # mean relational shape over train-speaker exemplars of the word. Variable-length
    # trajectories -> resample to a common frame count (median) before averaging
    # (a mechanical I/O alignment, not a fitted parameter).
    print("\n" + "=" * 74, flush=True)
    print("FORWARD MODEL — per-word CANONICAL relational shape "
          "(production collapsed, in the invariant space)", flush=True)
    print("=" * 74, flush=True)

    by_word = defaultdict(list)
    for R, w in tr_rel:
        by_word[w].append(np.asarray(R, dtype=np.float32))

    def _resample(R, L):
        n = len(R)
        if n == L:
            return R
        idx = np.linspace(0, n - 1, L)
        lo = np.floor(idx).astype(int)
        hi = np.minimum(lo + 1, n - 1)
        frac = (idx - lo)[:, None]
        return R[lo] * (1 - frac) + R[hi] * frac

    fwd_model = {}
    for w, Rs in by_word.items():
        L = int(np.median([len(R) for R in Rs]))
        L = max(L, 2)
        stack = np.stack([_resample(R, L) for R in Rs], axis=0)
        fwd_model[w] = stack.mean(axis=0).astype(np.float32)
        print(f"  {w:>8s}: {len(Rs):>3d} train exemplars -> canonical shape "
              f"{fwd_model[w].shape}", flush=True)

    # Mark the word Concepts so the native A-by-S argmax Term ranges over them, and
    # write the forward-model relational shape onto each as WORD_FEAT_ATTR.
    word_concept = {}
    for w in fwd_model:
        c = sub.add_node("Concept", {"name": w, "origin": "axs_relband"})
        sub.set_attr(c, RG.WORD_ATTR, 1.0)
        sub.set_attr(c, RG.WORD_FEAT_ATTR, as_tuple(fwd_model[w]))
        word_concept[w] = c

    axs_sign = sub.add_node("AcousticSign", {"axs_probe": 1.0})
    # THE AGENT'S NATIVE DECISION: argmax over word Concepts of -DtwTo(s, model(w)).
    pred_term = _Pred(RG.predict_synth_term())

    def run_axs(te_reprs, shuffle=False):
        # shuffle backstop: permute which canonical shape carries which label.
        cmap = dict(word_concept)
        if shuffle:
            ws = list(word_concept)
            shapes = [as_tuple(fwd_model[w]) for w in ws]
            random.Random(11).shuffle(shapes)
            for w, sh in zip(ws, shapes):
                sub.set_attr(word_concept[w], RG.WORD_FEAT_ATTR, sh)
        else:
            for w in word_concept:
                sub.set_attr(word_concept[w], RG.WORD_FEAT_ATTR,
                             as_tuple(fwd_model[w]))
        corr = tot = 0
        per_word = defaultdict(lambda: [0, 0])
        for M, w in te_reprs:
            sub.set_attr(axs_sign, RG.SIGN_FEAT_ATTR, as_tuple(M))
            pred = sub.evaluate(pred_term, {"s": axs_sign})
            pw = sub.node(pred)["attrs"].get("name") if pred is not None else None
            ok = int(pw == w)
            corr += ok
            tot += 1
            per_word[w][0] += ok
            per_word[w][1] += 1
        acc = corr / max(tot, 1)
        se = (acc * (1 - acc) / max(tot, 1)) ** 0.5
        return acc, se, corr, tot, dict(per_word)

    print("\n" + "=" * 74, flush=True)
    print("ARM B — AxS-REL-BAND (THE AGENT'S MOVE: instance<->model, native argmax "
          "-DtwTo)", flush=True)
    print("=" * 74, flush=True)
    b_acc, b_se, b_c, b_t, b_pw = run_axs(te_rel)
    print(f"[AxS-REL-BAND]  {b_c}/{b_t} = {100*b_acc:.2f}%  "
          f"(SE {100*b_se:.2f}%, chance {100*chance:.1f}%)", flush=True)

    print("\n" + "=" * 74, flush=True)
    print("ARM C — AxS-SHUFFLE (forward-model labels permuted -> must collapse)",
          flush=True)
    print("=" * 74, flush=True)
    c_acc, c_se, c_c, c_t, _ = run_axs(te_rel, shuffle=True)
    print(f"[AxS-SHUFFLE]  {c_c}/{c_t} = {100*c_acc:.2f}%  "
          f"(SE {100*c_se:.2f}%, chance {100*chance:.1f}%)", flush=True)

    # ---- VERDICT — read the numbers ----
    print("\n" + "=" * 74, flush=True)
    print("VERDICT — the agent's analysis-by-synthesis move, grounded", flush=True)
    print("=" * 74, flush=True)
    print(f"  A  REL-BAND 1-NN (baseline)   {a_c}/{a_t} = {100*a_acc:.2f}%  "
          f"(SE {100*a_se:.2f}%)", flush=True)
    print(f"  B  AxS-REL-BAND (agent move)  {b_c}/{b_t} = {100*b_acc:.2f}%  "
          f"(SE {100*b_se:.2f}%)", flush=True)
    print(f"  C  AxS-SHUFFLE (backstop)     {c_c}/{c_t} = {100*c_acc:.2f}%  "
          f"(SE {100*c_se:.2f}%, chance {100*chance:.1f}%)", flush=True)
    delta = 100 * (b_acc - a_acc)
    pooled = (a_se ** 2 + b_se ** 2) ** 0.5
    print(f"\n  DELTA B-A = {delta:+.2f} pp   (pooled SE {100*pooled:.2f} pp)",
          flush=True)
    if b_acc - a_acc > 2 * pooled:
        print("  -> A-by-S in REL-BAND space IMPROVES over the confirmed 1-NN "
              "decoder (> 2 SE).", flush=True)
    elif a_acc - b_acc > 2 * pooled:
        print("  -> A-by-S in REL-BAND space is WORSE than the 1-NN decoder "
              "(> 2 SE) — grounded null.", flush=True)
    else:
        print("  -> A-by-S ties the 1-NN decoder (within 2 SE) — no improvement "
              "this venue.", flush=True)
    if c_acc < a_acc - 2 * c_se:
        print("  -> shuffle backstop collapses: the win (if any) is in the "
              "label<->shape binding, not an artifact.", flush=True)
    print("\nper-word (true): word  1NN%  AxS%", flush=True)
    for w in words:
        ac = a_pw.get(w, [0, 1])
        bc = b_pw.get(w, [0, 1])
        print(f"  {w:>10s}  {100*ac[0]/max(ac[1],1):5.1f}  "
              f"{100*bc[0]/max(bc[1],1):5.1f}", flush=True)
    print(f"\ntotal time {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
