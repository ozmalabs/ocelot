"""Falsification test: "this speech agent learns FAR MORE from sentences
than from isolated words."

Isolated words (FSDD digits) carry no sequence, no context, no prediction.
Sentences carry an ordered stream of units. If the agent genuinely learns
more from sentences, ingesting continuous speech should yield STRUCTURE that
isolated words cannot give:

  (a) a recurring LEXICON emerging from continuous speech (signs recur via
      the pipeline's DTW merge — recurrence rate > 0 and rising over time);
  (b) TRANSITION structure between units: conditional next-sign entropy
      H(next|cur) << unigram H(next);
  (c) above-chance PREDICTION of the next sign from the current one on a
      held-out test split (bigram argmax), COLLAPSING to chance when the
      sign order is shuffled (proving the structure is sequential, not
      mere frequency).

This is a world-adapter measurement script. It ingests LibriSpeech audio
through STTPipeline.ingest (the agent's perception), reads out the ordered
sign-id sequence per utterance, and computes statistics on the agent's
OUTPUT. No agent reasoning lives here.

Run:
    python -m scripts.sentence_learning [n_utts] [n_speakers]

Honest test — reports the real numbers, including a null result.
"""
import math
import os
import random
import re
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate_rs import Substrate
from domains.stt_pipeline import STTPipeline, STTParams

DATA_DIR = "/tmp/LibriSpeech/dev-clean"
_FN_RE = re.compile(r"(\d+)-(\d+)-(\d+)\.flac")


def gather_pairs():
    """Walk dev-clean; pair each FLAC with its transcript. Returns
    (path, speaker, chapter, utt_id, transcript)."""
    out = []
    for root, _, names in os.walk(DATA_DIR):
        trans = {}
        for fn in names:
            if not fn.endswith(".trans.txt"):
                continue
            with open(os.path.join(root, fn)) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split(" ", 1)
                    if len(parts) == 2:
                        trans[parts[0]] = parts[1]
        for fn in names:
            m = _FN_RE.match(fn)
            if not m:
                continue
            sp, ch, ut = m.groups()
            utt_id = f"{sp}-{ch}-{ut}"
            if utt_id in trans:
                out.append((os.path.join(root, fn), sp, ch, ut,
                            trans[utt_id]))
    out.sort()
    return out


def load_flac_8k(path):
    """Decode a FLAC and resample to 8 kHz (the pipeline's rate)."""
    import av
    c = av.open(path)
    s = c.streams.audio[0]
    arr = np.concatenate([
        f.to_ndarray().flatten().astype(np.float32)
        for f in c.decode(s)
    ])
    rate = s.rate
    c.close()
    peak = max(float(np.abs(arr).max()), 1.0)
    arr = (arr / peak * 0.7).astype(np.float32)
    if rate == 16000:
        try:
            from scipy.signal import decimate
            arr = decimate(arr, 2).astype(np.float32)
        except Exception:
            arr = arr[::2].astype(np.float32)
    elif rate != 8000:
        # nearest-integer decimation fallback
        factor = max(1, round(rate / 8000))
        arr = arr[::factor].astype(np.float32)
    return np.ascontiguousarray(arr), 8000


def entropy(counts):
    """Shannon entropy (bits) of a count dict / list."""
    vals = list(counts.values()) if isinstance(counts, dict) else list(counts)
    tot = sum(vals)
    if tot <= 0:
        return 0.0
    h = 0.0
    for v in vals:
        if v <= 0:
            continue
        p = v / tot
        h -= p * math.log2(p)
    return h


def conditional_next_entropy(bigrams):
    """H(next|cur) = sum_cur P(cur) * H(next|cur). bigrams: dict
    cur -> dict(next -> count)."""
    total = sum(sum(d.values()) for d in bigrams.values())
    if total <= 0:
        return 0.0
    h = 0.0
    for cur, nexts in bigrams.items():
        n_cur = sum(nexts.values())
        h += (n_cur / total) * entropy(nexts)
    return h


def unigram_predict(train_seqs, test_seqs):
    """Context-FREE baseline: always predict the globally most-frequent
    next sign (and top-3 most frequent). This is the pure-frequency
    predictor — it uses NO sequential structure. Sentence-aware
    prediction must beat THIS to show it learned order, not frequency."""
    freq = {}
    for seq in train_seqs:
        for b in seq[1:]:
            freq[b] = freq.get(b, 0) + 1
    ranked = [s for s, _ in sorted(freq.items(), key=lambda kv: -kv[1])]
    top1_sign = ranked[0] if ranked else None
    top3_set = set(ranked[:3])
    n = top1 = top3 = 0
    for seq in test_seqs:
        for b in seq[1:]:
            n += 1
            if b == top1_sign:
                top1 += 1
            if b in top3_set:
                top3 += 1
    if n == 0:
        return 0.0, 0.0, 0
    return top1 / n, top3 / n, n


def bigram_predict(train_seqs, test_seqs, lexicon_size):
    """Learn bigram transitions on train; predict next sign on test
    by argmax P(next|cur). Returns (top1, top3, chance, n_pred)."""
    bigrams = {}
    for seq in train_seqs:
        for a, b in zip(seq, seq[1:]):
            bigrams.setdefault(a, {}).setdefault(b, 0)
            bigrams[a][b] += 1
    # Precompute ranked predictions per current sign.
    ranked = {}
    for cur, nexts in bigrams.items():
        ranked[cur] = [s for s, _ in sorted(nexts.items(),
                                             key=lambda kv: -kv[1])]
    n_pred = 0
    top1 = 0
    top3 = 0
    for seq in test_seqs:
        for a, b in zip(seq, seq[1:]):
            preds = ranked.get(a)
            if not preds:
                # unseen context: cannot predict above chance; count as
                # a prediction (miss) so we don't cherry-pick.
                n_pred += 1
                continue
            n_pred += 1
            if preds[0] == b:
                top1 += 1
            if b in preds[:3]:
                top3 += 1
    chance = 1.0 / max(lexicon_size, 1)
    if n_pred == 0:
        return 0.0, 0.0, chance, 0
    return top1 / n_pred, top3 / n_pred, chance, n_pred


def main():
    random.seed(1)
    n_utts = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    n_speakers = int(sys.argv[2]) if len(sys.argv) > 2 else 6

    pairs = gather_pairs()
    speakers = sorted(set(p[1] for p in pairs))
    print(f"LibriSpeech dev-clean: {len(pairs)} utterances, "
          f"{len(speakers)} speakers")
    chosen_spk = speakers[:n_speakers]
    sel = [p for p in pairs if p[1] in chosen_spk]
    random.shuffle(sel)
    sel = sel[:n_utts]
    print(f"Using {len(sel)} utterances from {n_speakers} speakers "
          f"{chosen_spk}")

    sub = Substrate()
    pipe = STTPipeline(STTParams(sample_rate=8000))
    pipe.attach(sub)
    pipe._ensure_audio_pipeline(sub)

    # --- ingest sentences; record ordered sign-id sequences ---------
    sequences = []           # list of [sign_key, ...] per utterance
    recurrence_curve = []    # running recurrence rate after each utt
    seen_signs = set()
    total_tokens = 0
    repeat_tokens = 0
    import time
    t0 = time.time()
    for i, (path, sp, ch, ut, transcript) in enumerate(sel):
        samples, _ = load_flac_8k(path)
        try:
            signs = pipe.ingest(sub, samples)
        except Exception as e:
            print(f"  FAIL ingest {path}: {e}", flush=True)
            continue
        sub.tick(50000)
        # sign NodeID -> stable key. The pipeline reuses the SAME sign
        # NodeID when a sound recurs (DTW merge), so identity = recurrence.
        seq = []
        for s in signs:
            v = getattr(s, "value", None)
            key = v if v is not None else repr(s)
            seq.append(key)
            total_tokens += 1
            if key in seen_signs:
                repeat_tokens += 1
            else:
                seen_signs.add(key)
        if seq:
            sequences.append(seq)
        recurrence_curve.append(
            (i + 1, len(seen_signs), total_tokens,
             repeat_tokens / max(total_tokens, 1)))
        if (i + 1) % 50 == 0:
            print(f"  ingested {i+1}/{len(sel)}  signs_seen="
                  f"{len(seen_signs)}  tokens={total_tokens}  "
                  f"recurrence={repeat_tokens / max(total_tokens,1):.3f}  "
                  f"({time.time()-t0:.0f}s)", flush=True)

    lexicon_size = len(seen_signs)
    overall_recurrence = repeat_tokens / max(total_tokens, 1)
    print("\n==================================================")
    print("(1) LEXICON GROWTH / RECURRENCE")
    print("==================================================")
    print(f"utterances ingested : {len(sequences)}")
    print(f"total sign tokens   : {total_tokens}")
    print(f"distinct signs      : {lexicon_size}")
    print(f"overall recurrence  : {overall_recurrence:.3f} "
          f"(fraction of tokens that repeat an already-seen sign)")
    # Recurrence rate over time — early vs late thirds.
    if len(recurrence_curve) >= 6:
        third = len(recurrence_curve) // 3
        early = recurrence_curve[third - 1][3]
        late = recurrence_curve[-1][3]
        # marginal recurrence in the last third (new tokens only)
        a = recurrence_curve[2 * third - 1]
        b = recurrence_curve[-1]
        dtok = b[2] - a[2]
        drep = (b[3] * b[2]) - (a[3] * a[2])
        marg_late = drep / max(dtok, 1)
        print(f"recurrence early(1/3 in): {early:.3f}   "
              f"final: {late:.3f}   rising={'YES' if late > early else 'no'}")
        print(f"marginal recurrence (last third only): {marg_late:.3f}")

    # --- transition structure ---------------------------------------
    print("\n==================================================")
    print("(2) TRANSITION STRUCTURE")
    print("==================================================")
    unigram = {}
    bigrams = {}
    for seq in sequences:
        for a, b in zip(seq, seq[1:]):
            unigram[b] = unigram.get(b, 0) + 1
            bigrams.setdefault(a, {}).setdefault(b, 0)
            bigrams[a][b] += 1
    h_next = entropy(unigram)
    h_next_cur = conditional_next_entropy(bigrams)
    max_h = math.log2(max(lexicon_size, 1)) if lexicon_size > 1 else 0.0
    print(f"H(next)      (unigram next-sign entropy) : {h_next:.3f} bits")
    print(f"H(next|cur)  (conditional on current)    : {h_next_cur:.3f} bits")
    print(f"max possible (log2 lexicon)              : {max_h:.3f} bits")
    print(f"information gain H(next)-H(next|cur)     : "
          f"{h_next - h_next_cur:.3f} bits  "
          f"({'structure' if h_next_cur < h_next - 1e-6 else 'NONE'})")

    # --- prediction: train/test split -------------------------------
    print("\n==================================================")
    print("(3) PREDICTION (the key test)")
    print("==================================================")
    seqs = [s for s in sequences if len(s) >= 2]
    random.shuffle(seqs)
    split = int(0.8 * len(seqs))
    train_seqs, test_seqs = seqs[:split], seqs[split:]
    print(f"train utterances: {len(train_seqs)}   "
          f"test utterances: {len(test_seqs)}")

    t1, t3, chance, npred = bigram_predict(train_seqs, test_seqs, lexicon_size)
    u1, u3, _ = unigram_predict(train_seqs, test_seqs)
    print(f"\nBASELINES:")
    print(f"  uniform chance   : {chance:.4f} (1/|lexicon|)")
    print(f"  frequency-only   : top-1 {u1:.3f}  top-3 {u3:.3f}  "
          f"(predict globally most-frequent sign, NO context)")
    print(f"\nSENTENCES (bigram, real order):")
    print(f"  predictions made : {npred}")
    print(f"  top-1 accuracy   : {t1:.3f}   (chance 1/|lex| = {chance:.4f})")
    print(f"  top-3 accuracy   : {t3:.3f}")
    print(f"  top-1 / chance   : {t1 / max(chance, 1e-9):.1f}x")
    print(f"  top-1 / frequency: {t1 / max(u1, 1e-9):.2f}x  "
          f"(>1 means CONTEXT helps beyond raw frequency)")

    # --- shuffled contrast ------------------------------------------
    print("\n==================================================")
    print("(4) SHUFFLE CONTRAST (destroy sequence, keep frequency)")
    print("==================================================")
    # Pool ALL tokens, shuffle, re-chunk into same-length pseudo-utts.
    # This keeps the unigram frequency distribution but destroys order.
    all_tokens = [tok for seq in seqs for tok in seq]
    lengths = [len(seq) for seq in seqs]
    random.shuffle(all_tokens)
    shuf_seqs = []
    idx = 0
    for L in lengths:
        shuf_seqs.append(all_tokens[idx:idx + L])
        idx += L
    random.shuffle(shuf_seqs)
    s_train, s_test = shuf_seqs[:split], shuf_seqs[split:]
    st1, st3, schance, snpred = bigram_predict(s_train, s_test, lexicon_size)
    print(f"SHUFFLED (frequency preserved, order destroyed):")
    print(f"  predictions made : {snpred}")
    print(f"  top-1 accuracy   : {st1:.3f}   (chance {schance:.4f})")
    print(f"  top-3 accuracy   : {st3:.3f}")
    print(f"  top-1 / chance   : {st1 / max(schance, 1e-9):.1f}x")

    # --- verdict ----------------------------------------------------
    print("\n==================================================")
    print("VERDICT")
    print("==================================================")
    has_lexicon = overall_recurrence > 0.05 and lexicon_size < total_tokens
    has_struct = h_next_cur < h_next - 1e-6
    # The rigorous bar: context (bigram) must beat the pure-frequency
    # predictor, AND must drop toward frequency level when shuffled.
    beats_freq = t1 > u1 * 1.10
    predicts = t1 > chance * 1.5 and t1 > 0.0
    collapses = st1 < t1 * 0.7
    print(f"(i)   lexicon emerging (recurrence>0)     : "
          f"{'YES' if has_lexicon else 'NO'} "
          f"(recurrence={overall_recurrence:.3f}, {lexicon_size} signs)")
    print(f"(ii)  H(next|cur) < H(next)               : "
          f"{'YES' if has_struct else 'NO'} "
          f"(gain {h_next - h_next_cur:.2f} bits)")
    print(f"(iii) prediction above chance             : "
          f"{'YES' if predicts else 'NO'} "
          f"(top1={t1:.3f} vs chance={chance:.4f})")
    print(f"(iii+) context beats raw frequency        : "
          f"{'YES' if beats_freq else 'NO'} "
          f"(bigram {t1:.3f} vs frequency {u1:.3f})")
    print(f"(iv)  collapses when shuffled             : "
          f"{'YES' if collapses else 'NO'} "
          f"(sentence {t1:.3f} -> shuffled {st1:.3f})")
    success = has_lexicon and has_struct and predicts and beats_freq and collapses
    print(f"\n>>> {'SUCCESS' if success else 'FAILS / PARTIAL'}: the agent "
          f"{'DOES' if success else 'does NOT cleanly'} demonstrate "
          f"sequential structure learned from sentences "
          f"that isolated words cannot give.")
    if not has_lexicon:
        print("    CAVEAT: recurrence near zero — no lexicon emerged "
              "(every token a fresh sign id). With no lexicon there is "
              "nothing to predict over; the test fails at step (i).")


if __name__ == "__main__":
    main()
