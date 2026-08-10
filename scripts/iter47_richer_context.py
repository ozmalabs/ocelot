"""iter47_richer_context — ENRICH the top-down context node from a BIGRAM to a
TRIGRAM (and 4-gram) with KATZ/STUPID-BACKOFF, wired into continuous word recognition.

THE ENRICHMENT (docs/agent_loop_iteration47_richer_context.md):
iter-46 wired the agent's OWN bigram transition model P(w | prev) as one more
likelihood node in the SAME variadic Argmax-of-product as every audio cue, and the
HAT x CONTEXT peer combine. Validated on continuous gold-span words: +0.055 lift on
the 14-way ctx-covered subset, COLLAPSING under the word-order shuffle (real sequential
context), and "more context -> more lift" (14-way > 12-way). The next enrichment is a
LONGER HISTORY.

iter-47 replaces P(w | prev) with a higher-order n-gram, BACKED OFF:

    P_ctx(w | prev2, prev1)  =  trigram if the (prev2,prev1) context is seen,
                                else BACK OFF to bigram P(w | prev1),
                                else BACK OFF to unigram P(w)

This is STUPID-BACKOFF (Brants et al. 2007) — pure COUNTS with a fixed backoff
discount lambda, the agent's own statistics (the sentence_learning transition counting
generalised to a longer history). NO neural LM, NO fit, NO weight, NO gradient. The
audio cue-graph (the "hat") is UNCHANGED — the only change is the n-gram order of the
single top-down likelihood node. It still enters as ONE extra_lik_channel, combined by
the SAME product and the SAME HAT x CONTEXT peer combine as iter-46.

THE DECISIVE READ: does the RICHER context (trigram / 4-gram) lift MORE than the
bigram (+0.055)? Does the lift still COLLAPSE under the word-order shuffle? And what is
the per-order CONTEXT COVERAGE (the trigram context is SPARSER than the bigram's 93.7%
— backoff handles the sparse contexts; report the coverage per order).

THE CONTROL — WORD-ORDER SHUFFLE (per order): rebuild every n-gram order's counts from
a GLOBALLY-SHUFFLED word stream (frequency preserved, order destroyed). The lift MUST
collapse at every order; if a higher order survives the shuffle it is a frequency prior.

VENUE: continuous LibriSpeech gold-span words (faster-whisper forced alignment), the
iter-46 context venue, held-out SPEAKERS (LOSO). Reuses iter46's gather/restrict/fold
machinery; the ONLY new code is the n-gram-with-backoff transition model + a gather that
keeps the FULL preceding history (not just one prev word).

Run:
  PYTHONUNBUFFERED=1 python -m scripts.iter47_richer_context \
      [n_spk] [utts] [min_ex] [max_vocab]
"""
import os
import random
import sys
import time
from collections import defaultdict

import numpy as np

sys.path.insert(0, '/home/matt/ozma/internal/research/experiments/gamma-substrate')

import scripts.sentence_learning as SL
import scripts.enriched_hvpt_accept as EH
import scripts.iter36_continuous_graph as IC
import scripts.iter46_topdown_context as I46
from scripts.iter15_goldspan_gate import gold_spans


# ---------------------------------------------------------------------------
# Gather gold-span words KEEPING the FULL per-utterance preceding HISTORY. iter-46's
# gather records only one prev word; the n-gram needs the preceding TWO (or more). We
# store hist_map = {speaker: [ (w_{-1}, w_{-2}, w_{-3}, ...)  truncated, ... ]} aligned
# to voice_audio clip order, where the tuple is the preceding words MOST-RECENT-FIRST
# (history[0] = prev1, history[1] = prev2, ...). Read from the FULL gold sequence so a
# dropped short word still serves as context (the iter-46 fix that gives 93.7% bigram
# coverage). max_hist = how many preceding words to retain (>= the max n-gram order - 1).
# ---------------------------------------------------------------------------

def gather_gold_words_hist(n_spk, utts_per_spk, wmodel, min_dur=0.10, max_hist=3):
    pairs = SL.gather_pairs()
    by_spk = defaultdict(list)
    for p in pairs:
        by_spk[p[1]].append(p)
    spk_sorted = sorted(by_spk, key=lambda s: -len(by_spk[s]))[:n_spk]
    voice_audio = {}
    hist_map = {}
    t0 = time.time()
    for s in spk_sorted:
        ps = list(by_spk[s])
        random.shuffle(ps)
        clips = []
        hists = []
        for path, sp, ch, ut in [(p[0], p[1], p[2], p[3]) for p in ps[:utts_per_spk]]:
            try:
                x, fs = SL.load_flac_8k(path)
            except Exception:
                continue
            try:
                gs = gold_spans(wmodel, path)
            except Exception:
                gs = []
            # history = the preceding words of THIS utterance, most-recent-first, read
            # from the FULL gold sequence (dropped short words still serve as context).
            history = []  # history[0] = prev1, history[1] = prev2, ...
            for w, ts, te in gs:
                if len(w) < 1:
                    continue
                a = max(0, int(round(ts * fs)))
                b = min(len(x), int(round(te * fs)))
                keep = (len(w) >= 3) and ((b - a) / fs >= min_dur) and (b - a >= 8)
                if keep:
                    clips.append((np.ascontiguousarray(x[a:b]), fs, w))
                    hists.append(tuple(history[:max_hist]))
                # advance context: push this word to front of history.
                history = [w] + history
        if clips:
            voice_audio[s] = clips
            hist_map[s] = hists
        print(f"  [{s}] {len(clips)} gold-word clips "
              f"({time.time()-t0:.0f}s)", flush=True)
    return voice_audio, hist_map


def restrict_hist(voice_audio, hist_map, min_exemplars, max_vocab,
                  min_speakers=2, cap_per_word_per_spk=8):
    """iter46.restrict_ordered, carrying hist_map (tuples) through the SAME filter+cap."""
    word_spk = defaultdict(set)
    word_count = defaultdict(int)
    for s, clips in voice_audio.items():
        for _, _, w in clips:
            word_spk[w].add(s)
            word_count[w] += 1
    vocab = {w for w in word_count
             if len(word_spk[w]) >= min_speakers and word_count[w] >= min_exemplars}
    ranked = sorted(vocab, key=lambda w: (-len(word_spk[w]), -word_count[w]))
    vocab = set(ranked[:max_vocab])
    out_va = {}
    out_hist = {}
    for s, clips in voice_audio.items():
        kept_clips = []
        kept_hist = []
        per_word = defaultdict(int)
        hists = hist_map[s]
        for (x, fs, w), hv in zip(clips, hists):
            if w in vocab and per_word[w] < cap_per_word_per_spk:
                kept_clips.append((x, fs, w))
                kept_hist.append(hv)
                per_word[w] += 1
        if kept_clips:
            out_va[s] = kept_clips
            out_hist[s] = kept_hist
    return out_va, out_hist, vocab


# ---------------------------------------------------------------------------
# THE N-GRAM-WITH-BACKOFF CONTEXT NODE — the agent's higher-order transition model.
# Counts n-grams up to order N over the TRAIN-speaker word sequences; emits, per held
# query, P_ctx(w | history) via STUPID-BACKOFF: use the highest-order context that was
# SEEN in training, else multiply by lambda and back off one order, recursively, down to
# the unigram. Pure COUNTS + a fixed backoff discount (no fit, no LM, no weight). The
# train PAIRS now carry the full history tuple: (history_tuple, target_word).
# ---------------------------------------------------------------------------

def build_ngram_model(train_pairs, candidates, order, alpha=1.0):
    """Count n-grams up to `order` (order=2 bigram, 3 trigram, 4 four-gram) over the
    TRAIN-speaker (history, target) observations. history is most-recent-first
    (history[0]=prev1, ...). Returns a list of per-order tables, table[k] keyed by the
    k-word context TUPLE (most-recent-first), value = {w: smoothed prob}; index 0 is the
    UNIGRAM (context-free). All Laplace-smoothed over the candidate lexicon (counting,
    not fitting). Also returns the raw context COUNT per order so stupid-backoff can
    decide 'was this context seen?'."""
    cand = list(candidates)
    K = len(cand)
    # raw counts per order: counts[k][ctx_tuple][target] (k = context length).
    counts = [defaultdict(lambda: defaultdict(float)) for _ in range(order)]
    for hist, tgt in train_pairs:
        if tgt not in candidates:
            continue
        # k=0 is the unigram (empty context); k=1 conditions on prev1; etc.
        for k in range(order):
            if k == 0:
                ctx = ()
            else:
                if len(hist) < k:
                    break  # not enough history for this order
                ctx = tuple(hist[:k])
            counts[k][ctx][tgt] += 1.0
    # smoothed probability tables per order.
    tables = []
    for k in range(order):
        tbl = {}
        for ctx, nexts in counts[k].items():
            tot = sum(nexts.values()) + alpha * K
            tbl[ctx] = {w: (nexts.get(w, 0.0) + alpha) / tot for w in cand}
        tables.append(tbl)
    # raw context observation count per order (for the 'seen?' test).
    raw = [{ctx: sum(nx.values()) for ctx, nx in counts[k].items()} for k in range(order)]
    return tables, raw


def ngram_likelihoods(held_hist, tables, raw, candidates, order, lam=0.4):
    """One {w: P_ctx(w | history)} per held query, in clip order, via STUPID-BACKOFF.
    Start at the highest order whose context tuple was SEEN in training; if the
    (order-1)-word context is unseen, multiply this order's contribution-weight by `lam`
    and back off one shorter context, recursively, down to the unigram (always present).
    The returned distribution is the backed-off mixture, renormalised — one likelihood
    channel exactly like the bigram node (so the SAME combine machinery applies).

    Also returns, per query, the EFFECTIVE order actually used (= the longest seen
    context), so we can report per-order coverage honestly."""
    cand = list(candidates)
    K = len(cand)
    uni = tables[0].get((), {w: 1.0 / K for w in cand})
    out = []
    eff_order = []
    for hist in held_hist:
        # find the highest order k (<= order-1) whose context was seen.
        best_k = 0
        for k in range(min(order - 1, len(hist)), 0, -1):
            ctx = tuple(hist[:k])
            if ctx in tables[k] and raw[k].get(ctx, 0.0) > 0:
                best_k = k
                break
        if best_k == 0:
            out.append(dict(uni))
            eff_order.append(1)  # unigram fallback
            continue
        # stupid-backoff: weight = lam^(top_order - k) for each order present, summed.
        # top order present = best_k; we mix best_k down to unigram with lam discounts.
        mix = {w: 0.0 for w in cand}
        wsum = 0.0
        for k in range(best_k, -1, -1):
            if k == 0:
                tbl = uni
            else:
                ctx = tuple(hist[:k])
                if ctx not in tables[k] or raw[k].get(ctx, 0.0) <= 0:
                    continue
                tbl = tables[k][ctx]
            wk = lam ** (best_k - k)
            for w in cand:
                mix[w] += wk * tbl.get(w, 1.0 / K)
            wsum += wk
        if wsum > 0:
            mix = {w: v / wsum for w, v in mix.items()}
        else:
            mix = dict(uni)
        out.append(mix)
        eff_order.append(best_k + 1)  # n-gram order = context length + 1
    return out, eff_order


def hist_word_order_shuffle(train_pairs, seed=0):
    """The DECISIVE control, generalised to histories: keep the history positions + the
    target frequency, but break the history->target ASSOCIATION by permuting the targets
    across pairs. Every n-gram order rebuilt on this MUST collapse to ~the unigram, so
    the top-down lift MUST vanish at EVERY order — proving real sequential context."""
    rng = random.Random(seed + 4242)
    hists = [h for (h, _) in train_pairs]
    tgts = [t for (_, t) in train_pairs]
    rng.shuffle(tgts)
    return list(zip(hists, tgts))


# ---------------------------------------------------------------------------
# Build one LOSO fold's train/held HISTORY sequences in build_fold order (so the
# context channel aligns to the held queries). Mirrors iter46.fold_prev_sequences but
# carries the full history tuple.
# ---------------------------------------------------------------------------

def fold_hist_sequences(voice_audio, hist_map, held_voice):
    train_voices = [v for v in voice_audio if v != held_voice]
    held_hist = list(hist_map[held_voice])
    held_words = [w for (_, _, w) in voice_audio[held_voice]]
    train_pairs = []
    for v in train_voices:
        for (_, _, w), hv in zip(voice_audio[v], hist_map[v]):
            train_pairs.append((hv, w))
    return held_hist, held_words, train_pairs


# ---------------------------------------------------------------------------
# Score one fold across n-gram ORDERS. For each order in `orders` (2=bigram baseline,
# 3=trigram, 4=4-gram) compute: bottom-up vs +n-gram (real) vs +n-gram (word-shuffle),
# in BOTH the 28-factor product AND the HAT x CONTEXT peer combine, plus the per-order
# effective-order coverage. The audio HAT is computed ONCE (unchanged across orders).
# ---------------------------------------------------------------------------

def score_fold_ngrams(voice_audio, hist_map, held_voice, orders, rounds=2,
                      alpha=1.0, lam=0.4, skip_axs=True):
    fold = EH.build_fold(voice_audio, held_voice, rounds, shuffle=False,
                         skip_axs=skip_axs)
    tw, hw = fold["train_words"], fold["held_words"]
    many_tr, many_he = fold["many_train"], fold["many_held"]
    ot_tr, ot_he = fold["ortho_train"], fold["ortho_held"]
    vec_tr = many_tr + ot_tr
    vec_he = many_he + ot_he
    candidates = sorted(set(tw))

    held_hist, hp_words, train_pairs = fold_hist_sequences(
        voice_audio, hist_map, held_voice)
    assert hp_words == hw, (
        f"held-word order mismatch (fold {hw[:5]} vs hist_map {hp_words[:5]}) — "
        "the context channel would be misaligned to the queries")

    # bottom-up ONLY (the iters 33-45 cue-graph product, no top-down) — shared baseline.
    bu_pred = EH.heldout_combined(vec_tr, vec_he, tw, hw, return_preds=True)
    bottom_up = float(np.mean([int(p == w) for p, w in zip(bu_pred, hw)])) if hw else 0.0

    # the audio HAT posterior (collapsed bottom-up product) — computed ONCE, unchanged.
    hat_post = I46._bottomup_posterior(vec_tr, vec_he, tw, candidates)
    hat_pred = [max(d, key=d.get) for d in hat_post]
    hat_alone = float(np.mean([int(p == w) for p, w in zip(hat_pred, hw)])) if hw else 0.0

    # shuffled training pairs (the decisive control) — one shuffle, reused per order.
    shuf_pairs = hist_word_order_shuffle(train_pairs)

    frozen = EH.heldout_1nn(fold["frozen_train"], tw, fold["frozen_held"], hw)

    def subset_acc(preds, mask):
        idx = [i for i, m in enumerate(mask) if m]
        return (float(np.mean([int(preds[i] == hw[i]) for i in idx])), len(idx)) \
            if idx else (0.0, 0)

    per_order = {}
    for order in orders:
        # REAL n-gram model + likelihoods.
        tables, raw = build_ngram_model(train_pairs, candidates, order, alpha=alpha)
        ctx_lik, eff = ngram_likelihoods(held_hist, tables, raw, candidates, order, lam)
        # the n-gram CONTEXT COVERAGE = queries whose effective order == the full order
        # (i.e. the (order-1)-word context was actually seen in training, NOT backed off).
        full_ctx = [e >= order for e in eff]
        n_full = sum(full_ctx)
        # ANY-context coverage = effective order >= 2 (used at least the bigram, not pure
        # unigram fallback) — the population where top-down can act AT ALL.
        any_ctx = [e >= 2 for e in eff]
        n_any = sum(any_ctx)

        # SHUFFLE n-gram model + likelihoods (same order).
        s_tables, s_raw = build_ngram_model(shuf_pairs, candidates, order, alpha=alpha)
        s_ctx_lik, _ = ngram_likelihoods(held_hist, s_tables, s_raw, candidates,
                                         order, lam)

        # 28-factor product combine (n-gram node as one extra channel).
        td_pred = EH.heldout_combined(vec_tr, vec_he, tw, hw,
                                      extra_lik_channels=[ctx_lik], return_preds=True)
        sh_pred = EH.heldout_combined(vec_tr, vec_he, tw, hw,
                                      extra_lik_channels=[s_ctx_lik], return_preds=True)
        bu_td = float(np.mean([int(p == w) for p, w in zip(td_pred, hw)])) if hw else 0.0
        bu_sh = float(np.mean([int(p == w) for p, w in zip(sh_pred, hw)])) if hw else 0.0

        # HAT x CONTEXT peer combine.
        hatxtd_pred = I46._hat_times_context(hat_post, ctx_lik, candidates)
        hatxsh_pred = I46._hat_times_context(hat_post, s_ctx_lik, candidates)

        # node ALONE (diagnostic).
        ctx_alone = float(np.mean(
            [int(max(d, key=d.get) == w) for d, w in zip(ctx_lik, hw)])) if hw else 0.0
        ctx_alone_sh = float(np.mean(
            [int(max(d, key=d.get) == w) for d, w in zip(s_ctx_lik, hw)])) if hw else 0.0

        # subsets: ANY-context (e>=2) is the decisive population (top-down can act);
        # also FULL-order (e>=order) to show the richer-context effect where it bites.
        cov_bu, n_any2 = subset_acc(bu_pred, any_ctx)
        cov_td, _ = subset_acc(td_pred, any_ctx)
        cov_sh, _ = subset_acc(sh_pred, any_ctx)
        cov_hat, _ = subset_acc(hat_pred, any_ctx)
        cov_hatxtd, _ = subset_acc(hatxtd_pred, any_ctx)
        cov_hatxsh, _ = subset_acc(hatxsh_pred, any_ctx)
        # full-order subset (only meaningful for order >= 3).
        f_bu, _ = subset_acc(bu_pred, full_ctx)
        f_hat, _ = subset_acc(hat_pred, full_ctx)
        f_hatxtd, _ = subset_acc(hatxtd_pred, full_ctx)
        f_hatxsh, _ = subset_acc(hatxsh_pred, full_ctx)

        per_order[order] = {
            "bu_td": bu_td, "bu_sh": bu_sh,
            "ctx_alone": ctx_alone, "ctx_alone_sh": ctx_alone_sh,
            "n_full_ctx": n_full, "n_any_ctx": n_any,
            "cov_bu": cov_bu, "cov_td": cov_td, "cov_sh": cov_sh,
            "cov_hat": cov_hat, "cov_hatxtd": cov_hatxtd, "cov_hatxsh": cov_hatxsh,
            "n_any": n_any2,
            "f_bu": f_bu, "f_hat": f_hat, "f_hatxtd": f_hatxtd, "f_hatxsh": f_hatxsh,
            "n_full": n_full,
        }

    return {
        "held_voice": held_voice, "n_held": len(hw), "n_train": len(tw),
        "n_cands": len(candidates),
        "bottom_up": bottom_up, "hat_alone": hat_alone, "frozen": frozen,
        "per_order": per_order,
    }


def _report(r, orders):
    print(f"\n--- held-out {r['held_voice']} (held {r['n_held']} train {r['n_train']}, "
          f"{r['n_cands']} cands) ---", flush=True)
    print(f"  bottom-up ONLY {r['bottom_up']:.3f}   hat {r['hat_alone']:.3f}   "
          f"frozen {r['frozen']:.3f}", flush=True)
    for o in orders:
        po = r["per_order"][o]
        name = {2: "BIGRAM", 3: "TRIGRAM", 4: "4-GRAM"}.get(o, f"{o}-GRAM")
        print(f"  [{name}] full-ctx={po['n_full_ctx']} any-ctx={po['n_any_ctx']}  "
              f"node-alone {po['ctx_alone']:.3f} (shuf {po['ctx_alone_sh']:.3f})",
              flush=True)
        print(f"    any-ctx subset (n={po['n_any']}): bu {po['cov_bu']:.3f}  "
              f"hatxctx {po['cov_hatxtd']:.3f} (Δ {po['cov_hatxtd']-po['cov_hat']:+.3f})  "
              f"hatxshuf {po['cov_hatxsh']:.3f} (Δ {po['cov_hatxsh']-po['cov_hat']:+.3f})",
              flush=True)


def main():
    n_spk = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    utts = int(sys.argv[2]) if len(sys.argv) > 2 else 50
    min_ex = int(sys.argv[3]) if len(sys.argv) > 3 else 6
    max_vocab = int(sys.argv[4]) if len(sys.argv) > 4 else 14
    alpha = float(os.environ.get("ALPHA", "1.0"))
    lam = float(os.environ.get("LAMBDA", "0.4"))
    rounds = int(os.environ.get("ROUNDS", "2"))
    orders = [2, 3, 4]
    max_hist = max(orders) - 1
    random.seed(1)
    np.random.seed(1)

    print("=" * 72, flush=True)
    print("ITER-47 — RICHER TOP-DOWN CONTEXT (n-gram + stupid-backoff)", flush=True)
    print("  recognition = Argmax_lex [ bottom-up audio cues x top-down n-gram-prior ]",
          flush=True)
    print(f"  n_spk={n_spk} utts/spk={utts} min_ex={min_ex} max_vocab={max_vocab} "
          f"alpha={alpha} lambda={lam} rounds={rounds} orders={orders}", flush=True)
    print("  top-down = the agent's OWNED n-gram transition counts + stupid-backoff +",
          flush=True)
    print("  lexicon, combine-all, no-fit / no-LM. CONTROL = the WORD-ORDER shuffle.",
          flush=True)
    print("=" * 72, flush=True)

    # AUDIT the combine-all product — UNCHANGED from iter-46: the n-gram node still
    # enters as exactly ONE extra Attr factor (the n-gram ORDER changes how the single
    # likelihood dict is computed, NOT the combine structure). 20 gammatone + 7 ortho +
    # 1 top-down = 28 factors, NO Max/Sort/Pick/If/Div/Weight/Mul.
    n_channels = 20 + len(EH.ORTHO_NAMES) + 1
    ok, msg = IC.audit_combine_all_term(n_channels)
    print(f"\nCOMBINE-ALL AUDIT (bottom-up+top-down, n={n_channels} factors: "
          f"20 gammatone + {len(EH.ORTHO_NAMES)} ortho + 1 top-down n-gram): {msg}",
          flush=True)
    if not ok:
        print("  AUDIT FAILED — aborting.", flush=True)
        return

    from faster_whisper import WhisperModel
    wmodel = WhisperModel("tiny", device="cpu", compute_type="int8")

    print("\nForced alignment + ordered gold-word slicing (full history)...", flush=True)
    va_raw, hist_raw = gather_gold_words_hist(n_spk, utts, wmodel, max_hist=max_hist)
    va, hist_map, vocab = restrict_hist(va_raw, hist_raw, min_ex, max_vocab)
    n_clips = sum(len(c) for c in va.values())
    chance = 1.0 / max(len(vocab), 1)
    print(f"\nshared cross-speaker vocab ({len(vocab)} words, chance {chance:.3f}): "
          f"{sorted(vocab)}", flush=True)
    print(f"speakers kept: {sorted(va)}  total clips: {n_clips}", flush=True)

    # global context coverage per order (sanity: how often is the k-word context present
    # in the held queries' histories at all — before train-seen test).
    allhist = [hv for s in hist_map for hv in hist_map[s]]
    for k in range(1, max(orders)):
        have = sum(1 for hv in allhist if len(hv) >= k)
        print(f"context present (history has >= {k} preceding word(s)): "
              f"{have}/{len(allhist)} ({have/max(len(allhist),1):.3f})", flush=True)

    if len(va) < 3 or len(vocab) < 2:
        print("Too few speakers/vocab — aborting.", flush=True)
        return

    speakers = sorted(va)
    real = []
    for held in speakers:
        if len(va.get(held, [])) < 2:
            continue
        r = score_fold_ngrams(va, hist_map, held, orders, rounds=rounds,
                              alpha=alpha, lam=lam)
        _report(r, orders)
        real.append(r)

    if not real:
        print("\nNo scorable folds.", flush=True)
        return

    bu = float(np.mean([r["bottom_up"] for r in real]))
    hat = float(np.mean([r["hat_alone"] for r in real]))
    fr = float(np.mean([r["frozen"] for r in real]))

    print("\n" + "=" * 72, flush=True)
    print(f"VERDICT (mean over {len(real)} held-out speakers, chance {chance:.3f})",
          flush=True)
    print("=" * 72, flush=True)
    print(f"  bottom-up ONLY (cue-graph, iters 33-45)   {bu:.3f}", flush=True)
    print(f"  audio HAT alone                           {hat:.3f}", flush=True)
    print(f"  frozen                                    {fr:.3f}", flush=True)

    # POOLED per-order metrics on the ANY-context subset (the iter-46 decisive
    # population, generalised: queries whose effective order >= 2). Weighted by subset n.
    print("\n  --- ANY-CONTEXT subset (effective order >= 2; the only place top-down",
          flush=True)
    print("      can act), HAT x CONTEXT peer combine, pooled over folds ---", flush=True)
    print(f"  {'order':<8}{'cov':>6}{'hat':>8}{'+ctx':>8}{'Δ':>9}"
          f"{'+shuf':>9}{'Δshuf':>9}{'full-ctx-cov':>14}", flush=True)
    order_summary = {}
    for o in orders:
        n_any = sum(r["per_order"][o]["n_any"] for r in real)
        n_full = sum(r["per_order"][o]["n_full"] for r in real)
        if n_any:
            chat = sum(r["per_order"][o]["cov_hat"] * r["per_order"][o]["n_any"]
                       for r in real) / n_any
            ctd = sum(r["per_order"][o]["cov_hatxtd"] * r["per_order"][o]["n_any"]
                      for r in real) / n_any
            csh = sum(r["per_order"][o]["cov_hatxsh"] * r["per_order"][o]["n_any"]
                      for r in real) / n_any
        else:
            chat = ctd = csh = 0.0
        lift = ctd - chat
        shuf_lift = csh - chat
        order_summary[o] = {"n_any": n_any, "n_full": n_full, "hat": chat,
                            "ctx": ctd, "lift": lift, "shuf_lift": shuf_lift}
        name = {2: "bigram", 3: "trigram", 4: "4-gram"}.get(o, f"{o}-gram")
        print(f"  {name:<8}{n_any:>6}{chat:>8.3f}{ctd:>8.3f}{lift:>+9.3f}"
              f"{csh:>9.3f}{shuf_lift:>+9.3f}{n_full:>14}", flush=True)

    # also report the 28-factor product full-set numbers per order (diluted; for record).
    print("\n  --- full-set HAT x CONTEXT (all queries incl. unigram fallback) per order"
          " ---", flush=True)
    for o in orders:
        name = {2: "bigram", 3: "trigram", 4: "4-gram"}.get(o, f"{o}-gram")
        btd = float(np.mean([r["per_order"][o]["bu_td"] for r in real]))
        bsh = float(np.mean([r["per_order"][o]["bu_sh"] for r in real]))
        ca = float(np.mean([r["per_order"][o]["ctx_alone"] for r in real]))
        cas = float(np.mean([r["per_order"][o]["ctx_alone_sh"] for r in real]))
        print(f"  {name:<8} 28-factor product bu+td {btd:.3f} (shuf {bsh:.3f})  "
              f"node-alone {ca:.3f} (shuf {cas:.3f})", flush=True)

    # THE DECISIVE READS.
    print("\n" + "=" * 72, flush=True)
    print("DECISIVE READ", flush=True)
    print("=" * 72, flush=True)
    big = order_summary.get(2, {})
    tri = order_summary.get(3, {})
    four = order_summary.get(4, {})
    bl = big.get("lift", 0.0)
    tl = tri.get("lift", 0.0)
    fl = four.get("lift", 0.0)
    print(f"  bigram  lift {bl:+.3f}  (shuf {big.get('shuf_lift',0):+.3f})  "
          f"full-ctx coverage {big.get('n_full',0)}/{big.get('n_any',0)}", flush=True)
    print(f"  trigram lift {tl:+.3f}  (shuf {tri.get('shuf_lift',0):+.3f})  "
          f"full-ctx coverage {tri.get('n_full',0)}/{tri.get('n_any',0)}", flush=True)
    print(f"  4-gram  lift {fl:+.3f}  (shuf {four.get('shuf_lift',0):+.3f})  "
          f"full-ctx coverage {four.get('n_full',0)}/{four.get('n_any',0)}", flush=True)

    def collapses(s):
        return (s["lift"] > 0) and (s["shuf_lift"] < s["lift"] * 0.5)
    tri_collapses = collapses(tri) if tri else False
    four_collapses = collapses(four) if four else False
    richer_more = (tl > bl + 1e-6) or (fl > bl + 1e-6)

    print("\n  Q1: does the RICHER context (trigram / 4-gram) lift MORE than the bigram?",
          flush=True)
    print(f"      trigram {tl:+.3f} vs bigram {bl:+.3f}  -> "
          f"{'YES (trigram > bigram)' if tl > bl + 1e-6 else 'NO'}", flush=True)
    print(f"      4-gram  {fl:+.3f} vs bigram {bl:+.3f}  -> "
          f"{'YES (4-gram > bigram)' if fl > bl + 1e-6 else 'NO'}", flush=True)
    print("\n  Q2: does the richer lift still COLLAPSE under the word-order shuffle?",
          flush=True)
    print(f"      trigram collapses: {'YES' if tri_collapses else 'NO'}  "
          f"(real {tl:+.3f} -> shuf {tri.get('shuf_lift',0):+.3f})", flush=True)
    print(f"      4-gram  collapses: {'YES' if four_collapses else 'NO'}  "
          f"(real {fl:+.3f} -> shuf {four.get('shuf_lift',0):+.3f})", flush=True)

    print("\n  VERDICT:", flush=True)
    if richer_more and (tri_collapses or four_collapses):
        print("  >>> MORE CONTEXT -> MORE LIFT, CONFIRMED. The richer (trigram/4-gram)",
              flush=True)
        print("      top-down lifts continuous recognition MORE than the bigram, AND the",
              flush=True)
        print("      lift still collapses under the word-order shuffle (real sequential",
              flush=True)
        print("      context, not frequency). The path is richer top-down. (agent's own",
              flush=True)
        print("      n-gram counts + stupid-backoff, combine-all, no-fit/no-LM.)", flush=True)
    elif (tri.get("n_full", 0) < tri.get("n_any", 1) * 0.5) and not richer_more:
        print("  >>> SPARSITY TRADEOFF: the trigram context is too sparse on this venue",
              flush=True)
        print("      (low full-order coverage); backoff -> ~bigram, so the richer order",
              flush=True)
        print("      does NOT lift more. A BIGGER venue is needed for higher-order n-grams.",
              flush=True)
        print("      (Honest: the bigram remains the operative order here.)", flush=True)
    else:
        print("  >>> NULL / MIXED: richer context does not clearly lift more here. Report",
              flush=True)
        print("      the residual; the per-order coverage + shuffle controls stand.",
              flush=True)

    print("\nHONEST: gold word spans isolate recognition from segmentation; the top-down",
          flush=True)
    print("node is the agent's OWNED n-gram transition counts + stupid-backoff (no LM, no",
          flush=True)
    print("fit, no weight), combined into the SAME variadic Argmax-of-product / HAT x",
          flush=True)
    print("CONTEXT peer combine as the bigram. Trigram context is SPARSER than bigram",
          flush=True)
    print("(per-order coverage reported); backoff handles the sparse contexts. The",
          flush=True)
    print("word-order shuffle is the decisive control at every order.", flush=True)


if __name__ == "__main__":
    main()
