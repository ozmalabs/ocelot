"""slow_path_accept — the SLOW PATH (order-N AxS replay-and-learn) decisive tests.

iter-39 (docs/agent_loop_iteration39_slow_path.md). Builds the agent's flagged
missing structural component: order-N analysis-by-synthesis learning machinery
([[ozma_order_n_analysis_by_synthesis]]). The slow path BUFFERS an utterance,
REPLAYS it, PARSES it via ORDER-N AxS (domains/slow_path — the agent's owned
forward model + the graph DtwTo + the order_n fixed-point iteration), LEARNS the
resolved structure, and BANKS it into the library; the FAST cue-graph
(scripts/enriched_hvpt_accept) then reads the enriched library.

THE TWO DECISIVE MEASUREMENTS:
  (A) ORDER-N vs SINGLE-PASS on HARD cases — does the iterated order-N AxS parse
      BETTER than the single pass, and does n scale with difficulty (harder cases use
      more passes, and more passes help)? Run on BOTH:
        · FSDD digits (the EASY venue — single-pass AxS already ~3x chance; iter-35
          found AxS redundant here, so order-N should be ~neutral) — the control.
        · CONTINUOUS cross-speaker gold-span words (the HARD venue — iter-36 found
          AxS FLIPS to complementary; this is where the slow path should pay off).
  (B) THE CLOSED LOOP — after the slow path banks confidently-resolved exemplars,
      does the FAST cue-graph improve on a held-out test set (before vs after)?

NO-DONKEY: every piece is owned (forward model = exemplar mean; AxS distance = the
graph DtwTo Term; order-N = the order_n operator's order-1 fixed point; learn-and-bank
= retain the trajectory). No fit, no trained net, no select-best, no global weight.

Run:
  python -m scripts.slow_path_accept digits [n_per]            # test A on FSDD
  python -m scripts.slow_path_accept continuous [n_spk] [utts] [min_ex] [max_vocab]
  python -m scripts.slow_path_accept loop [n_per]              # test B closed loop
  python -m scripts.slow_path_accept all                       # everything (slow)
"""
import os
import sys
import time
import random
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import scripts.enriched_hvpt_accept as EH
import domains.slow_path as SP
from scripts.mine_whisper import gather, load_wav


# iter-40: the forward-model SYNTH MODE.
#   "none"  — iter-39's exemplar-mean A1 trajectory, compared in A1 space directly
#             (never synthesises audio; the iter-39 baseline).
#   "old"   — synth+reanalyze through the CRUDE voicebox (synthesize_from_trajectory).
#   "klatt" — synth+reanalyze through Klatt cascade + LF glottal source.
# Set via env SLOW_SYNTH or the CLI; the model builder branches on it. The
# OLD-vs-NEW delta = "old" vs "klatt"; "none" is the iter-39 reference.
SYNTH_MODE = os.environ.get("SLOW_SYNTH", "none")
# A fixed synthesis f0 (the heard-voice pitch the candidate is voiced in). The
# slow path voices candidates in the heard voice; a single representative f0
# keeps the OLD-vs-NEW delta about SYNTH QUALITY, not f0 estimation.
SYNTH_F0 = float(os.environ.get("SLOW_SYNTH_F0", "150.0"))


def _build_model(library, fs):
    """Build the forward model under the active SYNTH_MODE. 'none' is the iter-39
    exemplar-mean trajectory; 'old'/'klatt' synthesise each candidate as audio and
    re-perceive it (the genuine invert-speak(), where synth quality bears)."""
    if SYNTH_MODE == "none":
        return SP.forward_model(library)
    return SP.audio_forward_model(library, fs, SYNTH_F0, mode=SYNTH_MODE)


# ---------------------------------------------------------------------------
# Helpers: build {speaker: [(x, fs, word), ...]} for FSDD and for continuous.
# ---------------------------------------------------------------------------

def fsdd_voice_audio(n_per):
    items = gather(n_per_class_per_speaker=n_per)
    va = {}
    for p, d, s in items:
        x, fs = load_wav(p)
        va.setdefault(s, []).append((x, fs, str(d)))
    return va


def continuous_voice_audio(n_spk, utts, min_ex, max_vocab):
    from faster_whisper import WhisperModel
    import scripts.iter36_continuous_graph as CG
    wmodel = WhisperModel("tiny", device="cpu", compute_type="int8")
    print("  forced alignment + gold-word slicing...", flush=True)
    raw = CG.gather_gold_words(n_spk, utts, wmodel)
    va, vocab = CG.restrict_to_shared_vocab(raw, min_ex, max_vocab)
    return va, vocab


def trajs_for(audio):
    """A1 trajectories for a [(word, x, fs), ...] list (the slow path's buffered
    replay representation = the same A1-patch extraction the fast AxS node uses)."""
    return [EH.utterance_a1_trajectory(x, fs) for (_, x, fs) in audio]


# ---------------------------------------------------------------------------
# TEST A — order-N vs single-pass, per LOSO fold, with the n-vs-difficulty curve.
# ---------------------------------------------------------------------------

# pass-CAP sweep: cap the order-N AxS at exactly this many passes (conv_band=0 so it
# always runs the full cap) — to measure "do MORE passes help?" monotonically.
PASS_CAPS = (1, 2, 4, 8)


def test_a_fold(va, held, max_n=10, conv_band=1e-4):
    train_audio = [(w, x, fs) for v in va if v != held for (x, fs, w) in va[v]]
    held_audio = [(w, x, fs) for (x, fs, w) in va[held]]
    tr_trajs = trajs_for(train_audio)
    he_trajs = trajs_for(held_audio)
    tr_words = [w for (w, _, _) in train_audio]
    cands = sorted(set(tr_words))
    fs_synth = held_audio[0][2] if held_audio else 8000
    model = _build_model(SP.build_library(tr_trajs, tr_words), fs_synth)

    rows = []   # per held query: (true, single_pred, ordn_pred, n_passes, sp_conf, cap_preds)
    for (w, x, fs), ht in zip(held_audio, he_trajs):
        sp = SP.single_pass_axs(ht, model, cands)
        on = SP.order_n_axs(ht, model, cands, max_n=max_n, conv_band=conv_band)
        # the pass-cap sweep (force exactly k passes, conv_band=0 = no early stop).
        cap_preds = {k: SP.order_n_axs(ht, model, cands, max_n=k,
                                       conv_band=0.0)["pred"] for k in PASS_CAPS}
        rows.append((w, sp["pred"], on["pred"], on["n_passes"],
                     SP.confidence(sp), cap_preds))
    return rows, cands


def summarize_test_a(all_rows, cands, label, chance):
    n = len(all_rows)
    sp_ok = sum(int(r[0] == r[1]) for r in all_rows)
    on_ok = sum(int(r[0] == r[2]) for r in all_rows)
    sp_acc = sp_ok / max(n, 1); on_acc = on_ok / max(n, 1)
    print(f"\n  [{label}] n={n}  chance {chance:.3f}", flush=True)
    print(f"    SINGLE-PASS AxS acc {sp_acc:.3f}", flush=True)
    print(f"    ORDER-N     AxS acc {on_acc:.3f}   "
          f"Δ(order-N - single) {on_acc - sp_acc:+.3f}  "
          f"=> {'order-N HELPS' if on_acc > sp_acc else 'order-N neutral/hurts'}",
          flush=True)
    passes = [r[3] for r in all_rows]
    print(f"    passes: mean {np.mean(passes):.2f}  range {min(passes)}-{max(passes)}",
          flush=True)

    # DOES MORE PASSES HELP? — the pass-CAP sweep: accuracy when order-N is capped at
    # exactly k passes (no early stop). Monotone rise = more passes help.
    print("    pass-cap sweep (acc @ exactly k passes; k=1 is single-pass):",
          flush=True)
    for k in PASS_CAPS:
        acc_k = sum(int(r[0] == r[5][k]) for r in all_rows) / max(n, 1)
        print(f"      @{k:>2} passes: {acc_k:.3f}", flush=True)

    # n-vs-DIFFICULTY: harder cases should use MORE passes (auto-stop count). Proxy for
    # difficulty = the single-pass got it WRONG (hard) vs RIGHT (easy).
    hard = [r for r in all_rows if r[0] != r[1]]      # single-pass got it WRONG
    easy = [r for r in all_rows if r[0] == r[1]]      # single-pass got it RIGHT
    if hard:
        hp = np.mean([r[3] for r in hard]); ep = np.mean([r[3] for r in easy]) if easy else 0
        print(f"    n-vs-difficulty: HARD (single-pass wrong) mean passes {hp:.2f} "
              f"vs EASY (single-pass right) {ep:.2f}  "
              f"=> {'harder uses MORE passes' if hp > ep else 'no pass-scaling'}",
              flush=True)
        # do the EXTRA passes RECOVER the hard cases the single pass missed?
        recovered = sum(int(r[0] == r[2]) for r in hard)
        broke = sum(int(r[0] == r[1] and r[0] != r[2]) for r in all_rows)
        print(f"    on the {len(hard)} single-pass FAILURES, order-N recovers "
              f"{recovered} ({recovered/len(hard):.3f}); it BREAKS {broke} "
              f"previously-correct  => net {recovered - broke:+d}", flush=True)
    return sp_acc, on_acc


def run_test_a_digits(n_per, max_n=6):
    print("=" * 72, flush=True)
    print(f"TEST A (EASY venue: FSDD digits, n_per={n_per}) — order-N vs single-pass",
          flush=True)
    print(f"  [forward-model SYNTH_MODE={SYNTH_MODE} f0={SYNTH_F0}]", flush=True)
    print("=" * 72, flush=True)
    va = fsdd_voice_audio(n_per)
    speakers = sorted(va)
    print(f"  FSDD {sum(len(v) for v in va.values())} recordings, "
          f"{len(speakers)} speakers {speakers}", flush=True)
    all_rows = []
    cands = None
    t0 = time.time()
    for held in speakers:
        rows, cands = test_a_fold(va, held, max_n=max_n)
        all_rows += rows
        sp = sum(int(r[0] == r[1]) for r in rows) / max(len(rows), 1)
        on = sum(int(r[0] == r[2]) for r in rows) / max(len(rows), 1)
        print(f"  held-out {held}: single {sp:.3f}  order-N {on:.3f}  "
              f"({time.time()-t0:.0f}s)", flush=True)
    return summarize_test_a(all_rows, cands, "FSDD digits", 0.10)


def run_test_a_continuous(n_spk, utts, min_ex, max_vocab, max_n=6):
    print("=" * 72, flush=True)
    print(f"TEST A (HARD venue: continuous cross-speaker gold-span words) — "
          f"order-N vs single-pass", flush=True)
    print("=" * 72, flush=True)
    va, vocab = continuous_voice_audio(n_spk, utts, min_ex, max_vocab)
    if len(va) < 3 or len(vocab) < 2:
        print("  too few speakers/vocab — skipping", flush=True)
        return None
    chance = 1.0 / len(vocab)
    print(f"  vocab ({len(vocab)}, chance {chance:.3f}): {sorted(vocab)}", flush=True)
    print(f"  speakers {sorted(va)}  clips {sum(len(v) for v in va.values())}",
          flush=True)
    all_rows = []
    cands = None
    t0 = time.time()
    for held in sorted(va):
        if len(va[held]) < 2:
            continue
        rows, cands = test_a_fold(va, held, max_n=max_n)
        all_rows += rows
        sp = sum(int(r[0] == r[1]) for r in rows) / max(len(rows), 1)
        on = sum(int(r[0] == r[2]) for r in rows) / max(len(rows), 1)
        print(f"  held-out {held}: single {sp:.3f}  order-N {on:.3f}  "
              f"n={len(rows)} ({time.time()-t0:.0f}s)", flush=True)
    return summarize_test_a(all_rows, cands, "continuous x-speaker", chance)


# ---------------------------------------------------------------------------
# TEST B — THE CLOSED LOOP: does banking from the slow path improve the FAST path?
#
# Split each held-out speaker's utterances into a SLOW-LEARN half and a FAST-TEST
# half. The fast cue-graph is the AxS node's standalone argmax (the fast path's
# AxS channel — the same single-pass AxS the fast graph uses), reading the LIBRARY.
# BEFORE: fast-path accuracy on the test half with the library = train exemplars
# only. SLOW: the slow path replays the learn half via order-N AxS, and BANKS the
# confidently-resolved trajectories (UNSUPERVISED — it uses its OWN parse label, not
# the truth). AFTER: fast-path accuracy on the SAME test half with the enriched
# library. The delta is the closed-loop payoff.
# ---------------------------------------------------------------------------

def fast_path_accuracy(model, test_trajs, test_words, cands):
    """The FAST path's AxS recognition over the test set, reading `model` (the
    forward model built from the current library). Single-pass argmax — the fast
    real-time decision the cue-graph uses (no order-N, no iteration). Returns acc."""
    ok = 0
    for ht, w in zip(test_trajs, test_words):
        r = SP.single_pass_axs(ht, model, cands)
        ok += int(r["pred"] == w)
    return ok / max(len(test_words), 1)


def test_b_fold(va, held, conf_thresh, max_n=6, seed=0):
    train_audio = [(w, x, fs) for v in va if v != held for (x, fs, w) in va[v]]
    held_audio = [(w, x, fs) for (x, fs, w) in va[held]]
    rng = random.Random(seed)
    rng.shuffle(held_audio)
    mid = len(held_audio) // 2
    learn_audio, test_audio = held_audio[:mid], held_audio[mid:]
    if not learn_audio or not test_audio:
        return None

    tr_trajs = trajs_for(train_audio)
    tr_words = [w for (w, _, _) in train_audio]
    cands = sorted(set(tr_words))

    learn_trajs = trajs_for(learn_audio)
    test_trajs = trajs_for(test_audio)
    test_words = [w for (w, _, _) in test_audio]

    fs_synth = test_audio[0][2] if test_audio else 8000

    # BEFORE: library = train exemplars only.
    library = SP.build_library(tr_trajs, tr_words)
    model_before = _build_model(library, fs_synth)
    acc_before = fast_path_accuracy(model_before, test_trajs, test_words, cands)

    # SLOW: replay the learn half via ORDER-N AxS and BANK confident parses.
    # UNSUPERVISED — banks under the slow path's OWN parse label (not the truth).
    banked = 0; bank_correct = 0
    for (w_true, x, fs), ht in zip(learn_audio, learn_trajs):
        model = _build_model(library, fs_synth)   # current (growing) forward model
        parse = SP.order_n_axs(ht, model, cands, max_n=max_n)
        if SP.learn_and_bank(library, ht, parse, conf_thresh=conf_thresh):
            banked += 1
            bank_correct += int(parse["pred"] == w_true)   # diagnostic only

    # AFTER: library = train + banked slow-path exemplars.
    model_after = _build_model(library, fs_synth)
    acc_after = fast_path_accuracy(model_after, test_trajs, test_words, cands)

    return {"held": held, "n_test": len(test_words), "n_learn": len(learn_audio),
            "acc_before": acc_before, "acc_after": acc_after,
            "banked": banked, "bank_correct": bank_correct}


def run_test_b(n_per, conf_thresh=0.0, max_n=6):
    print("=" * 72, flush=True)
    print(f"TEST B — THE CLOSED LOOP (FSDD, n_per={n_per}, conf_thresh={conf_thresh}): "
          f"does slow-path banking improve the fast path?", flush=True)
    print("=" * 72, flush=True)
    va = fsdd_voice_audio(n_per)
    speakers = sorted(va)
    print(f"  FSDD {len(speakers)} speakers; per fold: split held-out into "
          f"slow-learn / fast-test halves", flush=True)
    results = []
    t0 = time.time()
    for held in speakers:
        r = test_b_fold(va, held, conf_thresh, max_n=max_n)
        if r is None:
            continue
        results.append(r)
        print(f"  held-out {held}: before {r['acc_before']:.3f} -> after "
              f"{r['acc_after']:.3f}  Δ {r['acc_after']-r['acc_before']:+.3f}  "
              f"(banked {r['banked']}/{r['n_learn']}, of which {r['bank_correct']} "
              f"correct)  [{time.time()-t0:.0f}s]", flush=True)
    if not results:
        print("  no scorable folds", flush=True)
        return None
    bm = np.mean([r["acc_before"] for r in results])
    am = np.mean([r["acc_after"] for r in results])
    banked = sum(r["banked"] for r in results)
    bcorr = sum(r["bank_correct"] for r in results)
    nlearn = sum(r["n_learn"] for r in results)
    print(f"\n  MEAN fast-path acc  BEFORE {bm:.3f}  AFTER {am:.3f}  "
          f"Δ {am-bm:+.3f}  => {'CLOSED LOOP (banking helps)' if am > bm else 'loop does NOT close'}",
          flush=True)
    print(f"  banked {banked}/{nlearn} learn-half utts; {bcorr}/{banked} "
          f"({bcorr/max(banked,1):.3f}) of the banked labels were CORRECT "
          f"(unsupervised self-label purity)", flush=True)
    return bm, am


# ---------------------------------------------------------------------------
# THE TRUE-WORD-FAVOURING PROBE (iter-39's failure measurement, iter-40 redone).
# iter-39 found the forward model did NOT differentially favour the true word
# (warping the true word's model even RAISED its synth-error). The iter-40
# question: does a BETTER forward model (synth+reanalyze through Klatt+LF) now
# rank the true word LOWER (= favoured) than the OLD synth / no-synth? Reports,
# over many held utterances, the mean rank of the true word among candidates
# (lower = better) and the fraction where the true word is the argmin.
# Runs ALL THREE modes (none/old/klatt) in one pass for the direct delta.
# ---------------------------------------------------------------------------

def run_probe(n_per=2):
    print("=" * 72, flush=True)
    print(f"TRUE-WORD-FAVOURING PROBE (FSDD, n_per={n_per}) — none vs old vs klatt",
          flush=True)
    print("=" * 72, flush=True)
    va = fsdd_voice_audio(n_per)
    speakers = sorted(va)
    modes = ("none", "old", "klatt")
    agg = {m: {"ranks": [], "argmin_ok": 0, "n": 0} for m in modes}
    t0 = time.time()
    for held in speakers:
        train_audio = [(w, x, fs) for v in va if v != held for (x, fs, w) in va[v]]
        held_audio = [(w, x, fs) for (x, fs, w) in va[held]]
        tr_trajs = trajs_for(train_audio)
        tr_words = [w for (w, _, _) in train_audio]
        cands = sorted(set(tr_words))
        library = SP.build_library(tr_trajs, tr_words)
        fs_synth = held_audio[0][2] if held_audio else 8000
        base = SP.forward_model(library)
        models = {
            "none": base,
            "old": SP.audio_forward_model(library, fs_synth, SYNTH_F0, mode="old"),
            "klatt": SP.audio_forward_model(library, fs_synth, SYNTH_F0, mode="klatt"),
        }
        for (w, x, fs) in held_audio:
            ht = EH.utterance_a1_trajectory(x, fs)
            if ht is None:
                continue
            for m in modes:
                model = models[m]
                errs = {c: SP.synth_error(ht, model[c])
                        for c in cands if model.get(c) is not None}
                if not errs or w not in errs:
                    continue
                order = sorted(errs, key=errs.get)
                agg[m]["ranks"].append(order.index(w))
                agg[m]["argmin_ok"] += int(order[0] == w)
                agg[m]["n"] += 1
        print(f"  held-out {held} done ({time.time()-t0:.0f}s)", flush=True)
    print(f"\n  PROBE RESULTS (n={agg['none']['n']} held utterances, "
          f"{len(cands)} candidates, chance argmin {1/len(cands):.3f}, "
          f"chance mean-rank {(len(cands)-1)/2:.2f}):", flush=True)
    for m in modes:
        a = agg[m]
        if a["n"] == 0:
            continue
        mr = float(np.mean(a["ranks"]))
        am = a["argmin_ok"] / a["n"]
        print(f"    {m:6s}: true-word mean-rank {mr:.3f} (lower=better)  "
              f"argmin(=acc) {am:.3f}", flush=True)
    nr = float(np.mean(agg["none"]["ranks"])) if agg["none"]["ranks"] else None
    orr = float(np.mean(agg["old"]["ranks"])) if agg["old"]["ranks"] else None
    kr = float(np.mean(agg["klatt"]["ranks"])) if agg["klatt"]["ranks"] else None
    if kr is not None and orr is not None:
        print(f"\n  DELTA (true-word mean-rank; NEGATIVE = the model favours the "
              f"true word MORE):", flush=True)
        print(f"    klatt - old  = {kr - orr:+.3f}  "
              f"=> {'Klatt+LF favours the true word MORE than the old synth' if kr < orr else 'no gain over old synth'}",
              flush=True)
        print(f"    klatt - none = {kr - nr:+.3f}  "
              f"=> {'the audio round-trip favours the true word MORE than no-synth' if kr < nr else 'audio round-trip does not beat no-synth'}",
              flush=True)
    return agg


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    if mode == "probe":
        run_probe(int(sys.argv[2]) if len(sys.argv) > 2 else 2)
        return
    if mode == "digits":
        run_test_a_digits(int(sys.argv[2]) if len(sys.argv) > 2 else 4)
    elif mode == "continuous":
        a = sys.argv
        run_test_a_continuous(int(a[2]) if len(a) > 2 else 8,
                              int(a[3]) if len(a) > 3 else 30,
                              int(a[4]) if len(a) > 4 else 6,
                              int(a[5]) if len(a) > 5 else 12)
    elif mode == "loop":
        run_test_b(int(sys.argv[2]) if len(sys.argv) > 2 else 4,
                   conf_thresh=float(sys.argv[3]) if len(sys.argv) > 3 else 0.0)
    elif mode == "all":
        run_test_a_digits(4)
        run_test_b(4)
        run_test_a_continuous(8, 30, 6, 12)
    else:
        print(f"unknown mode {mode!r}", flush=True)


if __name__ == "__main__":
    main()
