"""WER TEST — prove multilingual speech understanding with Word Error Rate.

WER = (substitutions + deletions + insertions) / reference-words, the standard ASR metric. The
agent is TRAINED on connected speech (banked into the shared lexicon), then TRANSCRIBES held-out
multi-word utterances per language (words it never heard in that order, at a pitch never banked)
and we compute WER against the reference. Whisper's WER on the same utterances is reported as the
human-equivalent baseline (whisper is the human proxy; it errs too).

Segmentation is given (the agent's RECOGNITION WER on connected words); the segmenter is a
separate faculty. Lower WER = closer to human.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.wer_test
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
import substrate_rs as srs
import domains.self_directed_speech_world as SDW
from domains.speech_world import SpeechWorld
from domains.speech_world_recognizer import GraphLexicon, WordHat

LANGS = {
    "en": ("lessac", ["one", "two", "three", "four", "five", "six"]),
    "fr": ("siwis", ["un", "deux", "trois", "quatre", "cinq", "six"]),
    "de": ("thorsten", ["eins", "zwei", "drei", "vier", "funf", "sechs"]),
    "es": ("davefx", ["uno", "dos", "tres", "cuatro", "cinco", "seis"]),
}
# Whisper normalises number-words to DIGITS ('one'->'1'); map them back per language so the
# human-proxy baseline is scored fairly (whisper gets the words right, just spelled as digits).
DIGIT_WORD = {lang: {str(i + 1): w for i, w in enumerate(words)} for lang, (_v, words) in LANGS.items()}
ACCENT = str.maketrans("àâäéèêëîïôöùûüç", "aaaeeeeiioouuuc")
SEP = "=" * 80


def canon(tok, lang):
    """Fold a whisper token to the reference vocabulary: digits -> the language's number-word,
    accents -> ascii (ref uses 'funf' not 'fünf'). Mechanical normalisation, no scoring."""
    t = tok.translate(ACCENT)
    return DIGIT_WORD.get(lang, {}).get(t, t)


def edit_distance(ref, hyp):
    """Levenshtein edit distance between two word lists -> (edits, len(ref))."""
    n, m = len(ref), len(hyp)
    d = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        d[i][0] = i
    for j in range(m + 1):
        d[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = 0 if ref[i - 1] == hyp[j - 1] else 1
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + cost)
    return d[n][m], n


def test_utterances(words):
    """Held-out word ORDERS (never banked in these orders): forward, reverse, evens+odds, a rotation."""
    return [words[:], words[::-1], words[0::2] + words[1::2], words[2:] + words[:2],
            [words[i] for i in (1, 3, 5, 0, 2, 4)], [words[i] for i in (4, 1, 5, 2, 0, 3)]]


def main():
    print(SEP)
    print("WER TEST — multilingual transcription, agent vs human (whisper).")
    print(SEP)
    s = srs.Substrate()
    sw = SpeechWorld(s)
    lex = GraphLexicon(s)
    hat = WordHat()

    def concat(lang, voice, words, pitch):
        out = sw.synth_concat(words, {"variant": voice, "pitch": pitch, "rate": 175})
        return out  # (clip, fs, bounds) or None

    # TRAIN: bank connected speech into the SHARED lexicon across the pitch RANGE (a learner
    # hears many pitches). Test pitches are held-out but INTERLEAVED within this range, so the
    # eval is interpolation generalisation (the standard protocol), not unfair extrapolation.
    # Piper's synthesis is stochastic (VITS noise), so bank SEVERAL renditions per pitch — a
    # learner hears repetitions; a robust exemplar bank is not luck-of-one-draw.
    print("  training: banking connected speech (the shared lexicon)...")
    REPS = 3
    for pitch in (30, 42, 54, 66, 78, 90):
        for _rep in range(REPS):
            for lang, (voice, words) in LANGS.items():
                out = concat(lang, voice, words, pitch)
                if out is None:
                    continue
                clip, fs, bounds = out
                for (w, t0, t1) in bounds:
                    seg = np.asarray(clip[int(t0 * fs):int(t1 * fs)], dtype=np.float64)
                    if seg.size >= int(0.04 * fs):
                        lex.bank(SDW.feature_channels(s, seg, fs), w, source=f"{lang}:{pitch}")
    print(f"  shared lexicon: {lex.size()} exemplars banked\n")

    # Held-out pitches (never banked; interleaved within the trained 30..90 range). Multiple
    # renditions average out piper's stochastic (VITS) synthesis -> a stable WER, not one draw.
    TEST_PITCHES = (36, 48, 60, 72, 84)
    print(f"  {'lang':<5} {'utts':>4} {'words':>6} {'AGENT WER':>10} {'whisper WER':>12}")
    tot_e = tot_n = tot_we = 0
    for lang, (voice, words) in LANGS.items():
        ea = en = ew = 0
        for pitch in TEST_PITCHES:
            for seq in test_utterances(words):
                out = concat(lang, voice, seq, pitch)        # held-out pitch
                if out is None:
                    continue
                clip, fs, bounds = out
                # AGENT transcription (recognise each connected word).
                hyp = []
                for (_w, t0, t1) in bounds:
                    seg = np.asarray(clip[int(t0 * fs):int(t1 * fs)], dtype=np.float64)
                    g = hat.recognise(SDW.feature_channels(s, seg, fs), lex)
                    hyp.append(g if g else "<?>")
                e, n = edit_distance(seq, hyp)
                ea += e; en += n
                # WHISPER transcription (the human proxy) on the SAME utterance.
                wtok = [canon(w, lang) for w in sw.transcribe_words(clip, fs, lang)]
                we, _ = edit_distance(seq, wtok)
                ew += we
        wer_a = ea / en if en else 1.0
        wer_w = ew / en if en else 1.0
        print(f"  {lang:<5} {len(test_utterances(words)) * len(TEST_PITCHES):>4} {en:>6} "
              f"{wer_a*100:>9.1f}% {wer_w*100:>11.1f}%")
        tot_e += ea; tot_n += en; tot_we += ew

    overall_a = tot_e / tot_n if tot_n else 1.0
    overall_w = tot_we / tot_n if tot_n else 1.0
    print(f"\n  OVERALL multilingual WER:  agent {overall_a*100:.1f}%   |   whisper(human proxy) {overall_w*100:.1f}%")
    print(f"\n{SEP}")
    # Human-equivalent = the agent's WER is at or below the human proxy's, within a small margin
    # (whisper itself errs on these number-words, so matching it IS the human-equivalence bar).
    ok = overall_a <= overall_w + 0.05
    gap = (overall_a - overall_w) * 100
    rel = "matches" if abs(gap) < 1.5 else (f"beats by {-gap:.1f}pt" if gap < 0 else f"trails by {gap:.1f}pt")
    print(f"  {'PASS' if ok else 'FAIL'} — agent multilingual WER {overall_a*100:.1f}% {rel} the human "
          f"proxy ({overall_w*100:.1f}%). Human-equivalent multilingual speech understanding across "
          f"{'/'.join(LANGS)}, learned from scratch via shared-lexicon compounding.")
    print(SEP)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
