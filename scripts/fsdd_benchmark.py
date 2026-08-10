"""Substrate STT on the Free Spoken Digit Dataset.

Goals:
  1. Process all 3000 recordings without crashing.
  2. Report on phoneme inventory growth, sign minting, vocabulary
     consistency across speakers, accuracy of transcribe.
  3. Iterate on params if coverage is incomplete.
"""
import sys
sys.path.insert(0, '/home/matt/ozma/internal/research/experiments/gamma-substrate')

import os
import re
import time
from collections import Counter, defaultdict

import av
import numpy as np

from substrate_rs import Substrate
from domains.stt_pipeline import STTPipeline, STTParams


RECORDINGS_DIR = '/tmp/fsdd/recordings'


# FSDD filename format: <digit>_<speaker>_<index>.wav
_FN_RE = re.compile(r'(\d)_([a-z]+)_(\d+)\.wav')


def list_files():
    files = []
    for fn in sorted(os.listdir(RECORDINGS_DIR)):
        m = _FN_RE.match(fn)
        if not m:
            continue
        digit, speaker, idx = m.groups()
        files.append((os.path.join(RECORDINGS_DIR, fn),
                      digit, speaker, int(idx)))
    return files


def load_wav(path):
    c = av.open(path)
    s = c.streams.audio[0]
    arr = np.concatenate([
        f.to_ndarray().flatten().astype(np.float32)
        for f in c.decode(s)
    ])
    rate = s.rate
    c.close()
    peak = max(float(np.abs(arr).max()), 1.0)
    return (arr / peak * 0.7).astype(np.float32), rate


def ingest_all(pipe, sub, files, limit=None):
    """Process every file. Track per-file sign result + timing.
    Returns list of (digit, speaker, idx, sign_nids, n_phonemes_seen, dt_s)."""
    results = []
    start = time.time()
    for i, (path, digit, speaker, idx) in enumerate(files):
        if limit and i >= limit:
            break
        samples, fs = load_wav(path)
        # The pipeline's sample_rate was set on construction; FSDD
        # is 8 kHz, our default is 22050. Reuse if matches; else
        # rebuild pipeline.
        if pipe.params.sample_rate != fs:
            pipe = STTPipeline(STTParams(sample_rate=fs))
            pipe.attach(sub)
        t0 = time.time()
        try:
            signs = pipe.ingest(sub, samples)
        except Exception as e:
            print(f"  FAIL {path}: {e}")
            results.append((digit, speaker, idx, None, None, None))
            continue
        dt = time.time() - t0
        n_phon = sum(1 for _ in sub.nodes("Phoneme"))
        results.append((digit, speaker, idx, signs, n_phon, dt))
        if (i + 1) % 100 == 0:
            elapsed = time.time() - start
            rate = (i + 1) / elapsed
            print(f"  {i+1}/{len(files)}  "
                  f"phonemes={n_phon}  "
                  f"signs={sum(1 for _ in sub.nodes('AcousticSign'))}  "
                  f"{rate:.1f} files/sec  "
                  f"elapsed {elapsed:.1f}s")
    return results, pipe


def report(sub, pipe, results):
    """Summarise what the substrate learned across the corpus."""
    print()
    print("=" * 70)
    print("FSDD substrate-STT benchmark report")
    print("=" * 70)

    successes = [r for r in results if r[3] is not None]
    failures = len(results) - len(successes)
    print(f"\nProcessed: {len(successes)}/{len(results)}  "
          f"failures: {failures}")

    n_phon = sum(1 for _ in sub.nodes("Phoneme"))
    n_sign = sum(1 for _ in sub.nodes("AcousticSign"))
    n_utt = sum(1 for _ in sub.nodes("Utterance"))
    print(f"Substrate state: {n_phon} Phonemes, "
          f"{n_sign} AcousticSigns, {n_utt} Utterances")

    # Sign reuse: how many distinct signs per file? In an ideal world,
    # all 300 instances of "1" would resolve to 1 sign (= cross-
    # speaker, cross-instance recognition). Realistically we expect
    # 50-300 signs per digit, lower = more invariance.
    digit_signs = defaultdict(Counter)
    speaker_signs = defaultdict(Counter)
    file_count_per_digit = Counter()
    for digit, speaker, idx, signs, _, _ in successes:
        for s in signs:
            digit_signs[digit][s] += 1
            speaker_signs[speaker][s] += 1
        file_count_per_digit[digit] += 1
    print(f"\nPer-digit lexicon size (lower = more cross-speaker"
          f" invariance):")
    print(f"  {'digit':<6}{'files':<8}{'distinct signs':<18}{'most-used / files':<20}")
    for digit in sorted(digit_signs):
        c = digit_signs[digit]
        n_files = file_count_per_digit[digit]
        distinct = len(c)
        top_count = c.most_common(1)[0][1] if c else 0
        print(f"  {digit:<6}{n_files:<8}{distinct:<18}"
              f"{top_count}/{n_files}")

    # Cross-digit sign overlap: a sign that fires across many digits
    # is junk (universal pattern). A sign that fires for one digit is
    # discriminative.
    sign_digit_purity: dict = {}
    for digit, counter in digit_signs.items():
        for sig, n in counter.items():
            d = sign_digit_purity.setdefault(sig, Counter())
            d[digit] = n
    pure_signs = sum(1 for d in sign_digit_purity.values()
                       if len(d) == 1)
    polysemic = sum(1 for d in sign_digit_purity.values()
                      if len(d) > 1)
    print(f"\nSigns by digit-purity:")
    print(f"  pure (one digit only):   {pure_signs}")
    print(f"  polysemic (multi-digit): {polysemic}")

    # Speaker-invariance: did any sign fire for the SAME digit
    # across multiple speakers? Best-case the agent should not need
    # speaker info to recognise a digit.
    n_cross_speaker_signs = 0
    speaker_per_sign: dict = {}
    for digit, speaker, idx, signs, _, _ in successes:
        for s in signs:
            speaker_per_sign.setdefault(s, set()).add(speaker)
    for s, sp_set in speaker_per_sign.items():
        if len(sp_set) > 1:
            n_cross_speaker_signs += 1
    print(f"\nSpeaker invariance:")
    print(f"  signs fired by >1 speaker: {n_cross_speaker_signs}")
    print(f"  signs fired by 1 speaker:  "
          f"{len(speaker_per_sign) - n_cross_speaker_signs}")

    # Timing.
    times = [r[5] for r in successes if r[5] is not None]
    if times:
        total = sum(times)
        print(f"\nTiming:")
        print(f"  total processing: {total:.1f}s")
        print(f"  per file: avg={np.mean(times)*1000:.1f}ms "
              f"median={np.median(times)*1000:.1f}ms "
              f"max={max(times)*1000:.1f}ms")


def main():
    files = list_files()
    print(f"Found {len(files)} files in {RECORDINGS_DIR}")
    if not files:
        print("No files — check the path?")
        return

    # FSDD is 8 kHz. Pipeline params must match.
    sub = Substrate()
    pipe = STTPipeline(STTParams(sample_rate=8000))
    pipe.attach(sub)

    print(f"\nProcessing all {len(files)} files...")
    results, pipe = ingest_all(pipe, sub, files)
    report(sub, pipe, results)


if __name__ == "__main__":
    main()
