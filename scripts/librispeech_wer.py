"""Substrate STT WER on LibriSpeech dev-clean.

Pairs each FLAC with its known transcript from the per-chapter
.trans.txt files. Splits by speaker into train / test so the agent
never sees a test speaker's audio at grounding time. Trains via
STTPipeline.teach_aligned (proportional sign↔word alignment, see
domains/stt_pipeline.py), then transcribes the test set and
computes word error rate.

Reports WER overall + per speaker.
"""
import argparse
import os
import re
import sys
import time

import av
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))

from substrate_rs import Substrate
from domains.stt_pipeline import STTPipeline, STTParams


DATA_DIR = '/tmp/LibriSpeech/dev-clean'
_FN_RE = re.compile(r'(\d+)-(\d+)-(\d+)\.flac')
_WORD_RE = re.compile(r"[A-Z']+")


def gather_pairs(limit=None):
    """Walk dev-clean; for each FLAC, find its transcript line in
    the sibling <speaker>-<chapter>.trans.txt. Returns a list of
    (path, speaker, chapter, utt_id, transcript)."""
    out = []
    for root, _, names in os.walk(DATA_DIR):
        # Parse the transcript once per chapter directory.
        trans = {}
        for fn in names:
            if not fn.endswith('.trans.txt'):
                continue
            with open(os.path.join(root, fn)) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split(' ', 1)
                    if len(parts) != 2:
                        continue
                    trans[parts[0]] = parts[1]
        for fn in names:
            m = _FN_RE.match(fn)
            if not m:
                continue
            sp, ch, ut = m.groups()
            utt_id = f"{sp}-{ch}-{ut}"
            if utt_id not in trans:
                continue
            out.append((os.path.join(root, fn), sp, ch, ut,
                          trans[utt_id]))
    out.sort()
    return out[:limit] if limit else out


def load_flac(path):
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


def normalise(text):
    """Word-level normalisation: lowercase + extract alpha-words."""
    return _WORD_RE.findall(text.upper())


def levenshtein_words(ref, hyp):
    """Word-level edit distance. Standard O(M*N) DP."""
    m, n = len(ref), len(hyp)
    if m == 0:
        return n
    if n == 0:
        return m
    prev = list(range(n + 1))
    curr = [0] * (n + 1)
    for i in range(1, m + 1):
        curr[0] = i
        for j in range(1, n + 1):
            cost = 0 if ref[i - 1] == hyp[j - 1] else 1
            curr[j] = min(prev[j] + 1, curr[j - 1] + 1,
                           prev[j - 1] + cost)
        prev, curr = curr, prev
    return prev[n]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=None,
                        help='cap on total pairs (train + test)')
    parser.add_argument('--test_speakers', type=int, default=8,
                        help='number of speakers to hold out for test')
    parser.add_argument('--report_every', type=int, default=50)
    args = parser.parse_args()

    pairs = gather_pairs(limit=args.limit)
    speakers = sorted(set(p[1] for p in pairs))
    print(f'Pairs: {len(pairs)}  Speakers: {len(speakers)}')
    test_speakers = set(speakers[-args.test_speakers:])
    train_pairs = [p for p in pairs if p[1] not in test_speakers]
    test_pairs = [p for p in pairs if p[1] in test_speakers]
    print(f'  train: {len(train_pairs)} pairs from '
          f'{len(speakers) - len(test_speakers)} speakers')
    print(f'  test:  {len(test_pairs)} pairs from '
          f'{len(test_speakers)} speakers')

    sub = Substrate()
    pipe = STTPipeline(STTParams(sample_rate=16000))
    pipe.attach(sub)

    print('\n--- training ---', flush=True)
    t0 = time.time()
    train_signs = 0
    train_words = 0
    grounded = 0
    vote_counts: dict = {}
    for i, (path, sp, ch, ut, transcript) in enumerate(train_pairs):
        samples, fs = load_flac(path)
        if pipe.params.sample_rate != fs:
            pipe = STTPipeline(STTParams(sample_rate=fs))
            pipe.attach(sub)
        try:
            r = pipe.teach_via_valleys(sub, samples, transcript,
                                          vote_counts=vote_counts)
        except Exception as e:
            print(f'  FAIL teach {path}: {e}', flush=True)
            continue
        sub.tick(50000)
        train_signs += r['signs']
        train_words += r['words']
        grounded += r['signs_grounded']
        if (i + 1) % args.report_every == 0:
            n_concepts = sum(1 for _ in sub.nodes('Concept'))
            n_signs = sum(1 for _ in sub.nodes('AcousticSign'))
            print(f'  train {i+1}/{len(train_pairs)}  '
                  f'concepts={n_concepts}  signs={n_signs}  '
                  f'grounded_total={grounded}  '
                  f'{(i+1) / (time.time() - t0):.2f} files/sec',
                  flush=True)
    train_wall = time.time() - t0
    print(f'\nTraining done: {train_wall:.1f}s, '
          f'{train_signs} signs over {train_words} words, '
          f'{grounded} grounding edges minted')

    print('\n--- testing ---', flush=True)
    t0 = time.time()
    total_ref = 0
    total_err = 0
    per_speaker = {}
    sample_outputs = []
    for i, (path, sp, ch, ut, transcript) in enumerate(test_pairs):
        samples, fs = load_flac(path)
        ref = normalise(transcript)
        try:
            hyp_text = pipe.transcribe_via_votes(sub, samples,
                                                     vote_counts)
        except Exception as e:
            print(f'  FAIL transcribe {path}: {e}', flush=True)
            continue
        hyp = normalise(hyp_text)
        err = levenshtein_words(ref, hyp)
        total_ref += len(ref)
        total_err += err
        d = per_speaker.setdefault(sp, [0, 0])
        d[0] += len(ref)
        d[1] += err
        if i < 5:
            sample_outputs.append((ref, hyp, err, len(ref)))
        if (i + 1) % args.report_every == 0:
            wer = total_err / max(total_ref, 1)
            print(f'  test {i+1}/{len(test_pairs)}  '
                  f'words_seen={total_ref}  WER={wer:.3f}', flush=True)
    test_wall = time.time() - t0

    print('\n========================================')
    print('Substrate STT — LibriSpeech dev-clean WER')
    print('========================================')
    print(f'train pairs:    {len(train_pairs)}')
    print(f'test pairs:     {len(test_pairs)}')
    print(f'train wall:     {train_wall:.1f}s')
    print(f'test wall:      {test_wall:.1f}s')
    print(f'total ref words:{total_ref}')
    print(f'total errors:   {total_err}')
    if total_ref:
        print(f'overall WER:    {total_err / total_ref:.3f}')

    print(f'\nPer-speaker WER:')
    for sp, (r, e) in sorted(per_speaker.items()):
        print(f'  {sp:8} ref={r:5} err={e:5} WER={e / max(r, 1):.3f}')

    print(f'\nFirst {len(sample_outputs)} test predictions:')
    for ref, hyp, err, n in sample_outputs:
        print(f'  REF [{n}w]: {" ".join(ref[:20])}{"..." if len(ref) > 20 else ""}')
        print(f'  HYP        : {" ".join(hyp[:20])}{"..." if len(hyp) > 20 else ""}')
        print(f'  ERR        : {err}/{n} = {err/max(n,1):.3f}')
        print()


if __name__ == "__main__":
    main()
