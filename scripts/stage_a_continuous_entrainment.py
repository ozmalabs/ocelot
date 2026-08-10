"""Stage A — entrained-theta oscillator on CONTINUOUS rhythmic speech.

THE TEST (the "nursery-rhyme" prediction). An entrained theta oscillator is the
ACTIVE syllable-clock: it needs RHYTHM — several syllable cycles — to phase-lock.
Isolated short words (the Speech-Commands parallel build, mostly monosyllabic)
give barely one cycle: the HARD case for an oscillator. Continuous speech carries
a real syllable rhythm, so the oscillator should ENTRAIN and beat the passive
envelope-peak counter; the gap should WIDEN with utterance length (more cycles to
lock). Nursery rhymes are exaggerated regular meter precisely to entrain a child's
theta clock — the oscillator's proper domain.

WHAT IS COMPARED (per LibriSpeech utterance, cross-speaker):
  TRUE syllable count = sum over the transcript's words of the word's CMUdict
                        syllable count (= # of stress-bearing vowel phonemes, the
                        phonemes ending in a stress digit 0/1/2 — the standard
                        CMUdict syllabification). Source: CMU Pronouncing
                        Dictionary via nltk (123,455 entries). Words absent from
                        CMUdict fall back to an owned orthographic vowel-group
                        heuristic (stated below); the count of fallback words is
                        reported so the dictionary coverage is auditable.
  (a) ACTIVE  oscillator count  = prosody_syllable.entrain_theta (Stage A).
  (b) PASSIVE peak-counter count = prosody_syllable.extract_syllables (baseline).

Per utterance we score the absolute count error |pred - true| for each, and the
exact-count hit. Results are BINNED by true syllable count (short 1-3 vs mid 4-7
vs long 8+) to expose whether the active advantage GROWS with rhythm.

DONKEY BOUNDARY. Both readers are owned envelope DSP with FROZEN constants (no
net, no fit, nothing swept on this test set — see prosody_syllable.py). The true
count comes from a pronunciation dictionary (world knowledge), never from audio.
This is a world-adapter MEASUREMENT script: it decodes audio, runs the two
transducers, and tallies error against the dictionary. No agent reasoning, no
CortexLoop, no graph state. Held-out is automatic — neither transducer has any
fitted parameter, so every speaker is "held out."

Run:
    python -m scripts.stage_a_continuous_entrainment [n_utts] [seed]
"""
import os
import re
import sys
import random

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domains import prosody_syllable as P
from scripts.sentence_learning import gather_pairs, load_flac_8k


# ---------------------------------------------------------------------------
# TRUE syllable count from the CMU Pronouncing Dictionary (world knowledge).
# ---------------------------------------------------------------------------

def _load_cmudict():
    import nltk
    try:
        from nltk.corpus import cmudict
        return cmudict.dict()
    except LookupError:
        nltk.download("cmudict", quiet=True)
        from nltk.corpus import cmudict
        return cmudict.dict()


_VOWEL_RE = re.compile(r"[aeiouy]+")


def _orth_syllables(word):
    """Owned orthographic fallback for words absent from CMUdict: count vowel
    GROUPS, drop a silent trailing 'e', floor at 1. Standard heuristic; used
    only for out-of-dictionary tokens (count reported)."""
    w = re.sub(r"[^a-z]", "", word.lower())
    if not w:
        return 0
    groups = _VOWEL_RE.findall(w)
    n = len(groups)
    if w.endswith("e") and not w.endswith(("le", "ie")) and n > 1:
        n -= 1
    return max(1, n)


def true_count(transcript, cmu):
    """Sum of CMUdict syllable counts over the transcript words. A word's
    syllable count = number of phonemes carrying a stress digit (CMUdict marks
    every vowel phoneme with a trailing 0/1/2). Returns (count, n_words,
    n_fallback)."""
    words = re.findall(r"[a-zA-Z']+", transcript.lower())
    total = 0
    n_fallback = 0
    for w in words:
        prons = cmu.get(w)
        if prons:
            # first pronunciation; syllables = stress-digit-bearing phonemes
            syl = sum(1 for ph in prons[0] if ph[-1].isdigit())
            total += max(1, syl)
        else:
            total += _orth_syllables(w)
            n_fallback += 1
    return total, len(words), n_fallback


# ---------------------------------------------------------------------------
# Binning by true syllable count (rhythm available to the oscillator).
# ---------------------------------------------------------------------------

BINS = [
    ("short 1-3",  1, 3),
    ("mid 4-7",    4, 7),
    ("long 8-15",  8, 15),
    ("xlong 16+", 16, 10**9),
]


def bin_for(true_syll):
    for name, lo, hi in BINS:
        if lo <= true_syll <= hi:
            return name
    return BINS[-1][0]


def main():
    n_utts = int(sys.argv[1]) if len(sys.argv) > 1 else 400
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    random.seed(seed)

    print(f"[stage-a] loading CMUdict ...", flush=True)
    cmu = _load_cmudict()
    print(f"[stage-a] CMUdict entries: {len(cmu)}", flush=True)

    pairs = gather_pairs()
    print(f"[stage-a] LibriSpeech dev-clean utterances available: {len(pairs)}",
          flush=True)
    if not pairs:
        print("[stage-a] NO DATA — /tmp/LibriSpeech/dev-clean empty. ABORT.")
        return

    random.shuffle(pairs)
    pairs = pairs[:n_utts]

    # per-utterance records
    recs = []  # (true, active, passive, bin_name, speaker, n_fallback, n_words)
    speakers = set()
    total_fallback = 0
    total_words = 0

    for i, (path, sp, ch, ut, transcript) in enumerate(pairs):
        tc, nw, nfb = true_count(transcript, cmu)
        if tc <= 0:
            continue
        try:
            x, _ = load_flac_8k(path)
        except Exception as e:
            print(f"[stage-a] decode fail {path}: {e}", flush=True)
            continue
        active, _ = P.entrain_theta(x)
        passive, _ = P.extract_syllables(x)
        b = bin_for(tc)
        recs.append((tc, active, passive, b, sp, nfb, nw))
        speakers.add(sp)
        total_fallback += nfb
        total_words += nw
        if (i + 1) % 50 == 0:
            print(f"[stage-a] processed {i+1}/{len(pairs)} "
                  f"(records {len(recs)})", flush=True)

    if not recs:
        print("[stage-a] NO RECORDS. ABORT.")
        return

    trues   = np.array([r[0] for r in recs], dtype=float)
    actives = np.array([r[1] for r in recs], dtype=float)
    passives= np.array([r[2] for r in recs], dtype=float)

    def stats(pred):
        err = np.abs(pred - trues)
        return err.mean(), (pred == trues).mean(), \
               (pred / trues).mean()  # mean ratio pred/true (bias)

    a_mae, a_hit, a_ratio = stats(actives)
    p_mae, p_hit, p_ratio = stats(passives)

    print("\n" + "=" * 74)
    print("STAGE A — entrained theta oscillator vs passive peak-counter")
    print("          on CONTINUOUS LibriSpeech (cross-speaker)")
    print("=" * 74)
    print(f"utterances scored : {len(recs)}")
    print(f"distinct speakers : {len(speakers)} (every speaker held out — "
          f"no fitted params)")
    print(f"dict coverage     : {total_words - total_fallback}/{total_words} "
          f"words in CMUdict ({100*(total_words-total_fallback)/max(1,total_words):.1f}%); "
          f"{total_fallback} orthographic-fallback words")
    print(f"true syll / utt   : mean {trues.mean():.1f}  "
          f"min {int(trues.min())}  max {int(trues.max())}")
    print("-" * 74)
    print(f"{'reader':<22}{'mean|err|':>12}{'exact-hit':>12}{'pred/true':>12}")
    print(f"{'ACTIVE oscillator':<22}{a_mae:>12.3f}{a_hit:>12.3f}{a_ratio:>12.3f}")
    print(f"{'PASSIVE peak-count':<22}{p_mae:>12.3f}{p_hit:>12.3f}{p_ratio:>12.3f}")
    print("-" * 74)

    # per-bin error curves
    print(f"\n{'bin':<12}{'n':>6}{'true_mean':>11}"
          f"{'active|err|':>13}{'passive|err|':>14}{'gap(p-a)':>11}")
    print("-" * 74)
    bin_rows = []
    for name, lo, hi in BINS:
        idx = np.array([j for j, r in enumerate(recs) if r[3] == name])
        if idx.size == 0:
            continue
        ae = np.abs(actives[idx] - trues[idx]).mean()
        pe = np.abs(passives[idx] - trues[idx]).mean()
        gap = pe - ae   # positive => oscillator better
        bin_rows.append((name, idx.size, trues[idx].mean(), ae, pe, gap))
        print(f"{name:<12}{idx.size:>6}{trues[idx].mean():>11.1f}"
              f"{ae:>13.3f}{pe:>14.3f}{gap:>+11.3f}")
    print("-" * 74)

    # ---- VERDICT ----
    overall_better = a_mae < p_mae
    # does the gap GROW with length? compare shortest vs longest populated bin
    grow = None
    if len(bin_rows) >= 2:
        first_gap = bin_rows[0][5]
        last_gap = bin_rows[-1][5]
        grow = last_gap > first_gap
    print("\nVERDICT")
    print(f"  overall: oscillator {'BEATS' if overall_better else 'does NOT beat'} "
          f"passive (mean|err| {a_mae:.3f} vs {p_mae:.3f})")
    if grow is not None:
        print(f"  rhythm:  active-advantage gap "
              f"{'GROWS' if grow else 'does NOT grow'} with utterance length "
              f"(short bin gap {bin_rows[0][5]:+.3f} -> "
              f"long bin gap {bin_rows[-1][5]:+.3f})")
    if overall_better and grow:
        print("  => PREDICTION CONFIRMED: the active interface entrains on "
              "continuous rhythmic speech and the advantage widens with rhythm.")
    elif overall_better:
        print("  => PARTIAL: oscillator wins overall but advantage does not "
              "clearly grow with length.")
    else:
        print("  => KILL: the oscillator does NOT beat the passive counter on "
              "continuous speech. The active-entrainment approach is wrong here "
              "(entrainment fails / envelope too noisy cross-speaker).")
    print("=" * 74)
    print("STAGE_A_CONTINUOUS_COMPLETED", flush=True)


if __name__ == "__main__":
    main()
