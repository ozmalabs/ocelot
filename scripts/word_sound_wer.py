"""WordSoundWorld — pre-segmented (audio, word) pair learning.

Uses faster-whisper purely as a forced aligner: it gives us
word-level (start, end) timestamps per utterance. We slice the
audio at those boundaries and feed the substrate a sequence of
short (audio_segment, word) pairs. Each segment is ~one word
long.

The substrate then learns the sign↔word correspondence
unambiguously — every sign produced from a one-word audio
segment is grounded to that one word. Vote counting (per-(sign,
word) tallies) accumulates clean signal across training.

This is "the world seeds the words" — the agent inhabits a world
where (sound, word) pairing is part of the world's structure,
not something it has to derive from raw audio. Mirrors how
children learn language: words pointed at + demonstrated.
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
from domains.stt_pipeline import STTPipeline, STTParams, _node_sort_key


DATA_DIR = '/tmp/LibriSpeech/dev-clean'
_FN_RE = re.compile(r'(\d+)-(\d+)-(\d+)\.flac')
_WORD_RE = re.compile(r"[A-Z']+")


def gather_pairs(limit=None):
    out = []
    for root, _, names in os.walk(DATA_DIR):
        for fn in names:
            m = _FN_RE.match(fn)
            if not m:
                continue
            sp, ch, ut = m.groups()
            out.append((os.path.join(root, fn), sp, ch, ut))
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


def normalise_word(w):
    return w.upper().strip("'-.,?!:;").replace("'", "").strip()


def force_align(whisper_model, samples, fs):
    """Use whisper word-level timestamps to slice this utterance
    into (audio_segment, word) pairs. Returns a list of (segment,
    word) tuples; segment is a numpy float32 array, word is the
    normalised word string."""
    segments, _ = whisper_model.transcribe(
        samples, language='en', beam_size=1,
        word_timestamps=True,
    )
    pairs = []
    for seg in segments:
        if not seg.words:
            continue
        for w in seg.words:
            word = normalise_word(w.word)
            if not word:
                continue
            start_i = max(0, int(w.start * fs))
            end_i = min(len(samples), int(w.end * fs))
            if end_i - start_i < int(0.03 * fs):
                continue  # < 30 ms; too short to be a real word
            seg_audio = samples[start_i:end_i]
            pairs.append((seg_audio, word))
    return pairs


def levenshtein_words(ref, hyp):
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


def teach_pair(sub, pipe, segment, word, vote_counts):
    """Ingest a one-word audio segment; ground every produced sign
    to the word's Concept; bump vote count. The simplest possible
    grounding — segment IS the word, no alignment problem."""
    if len(segment) < 100:
        return 0
    signs = pipe.ingest(sub, segment)
    if not signs:
        return 0
    # Find or mint the word's Concept.
    nid = None
    for c in sub.nodes("Concept"):
        if sub.node(c)["attrs"].get("name") == word.lower():
            nid = c
            break
    if nid is None:
        nid = sub.add_node("Concept", {"name": word.lower(),
                                          "origin": "word_sound_world"})
    from substrate_rs import speech as _sp
    rust_sub = sub._inner if hasattr(sub, "_inner") else sub
    n_grounded = 0
    for sign in signs:
        key = (_node_sort_key(sign), word.lower())
        vote_counts[key] = vote_counts.get(key, 0) + 1
        if nid not in list(sub.neighbours(sign, "denotes")):
            _sp.ground_sign(rust_sub, sign, nid)
            n_grounded += 1
    return n_grounded


def predict_word(sub, pipe, segment, vote_counts):
    """Ingest a one-word audio segment; emit the word with the
    most votes across the produced signs."""
    if len(segment) < 100:
        return None
    signs = pipe.ingest(sub, segment)
    if not signs:
        return None
    # Tally votes across signs in this segment.
    word_score: dict[str, int] = {}
    for sign in signs:
        sk = _node_sort_key(sign)
        for (sign_key, word), cnt in vote_counts.items():
            if sign_key != sk:
                continue
            word_score[word] = word_score.get(word, 0) + cnt
    if not word_score:
        return None
    return max(word_score.items(), key=lambda kv: kv[1])[0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=80,
                        help='LibriSpeech utterances to use')
    parser.add_argument('--test_speakers', type=int, default=2)
    parser.add_argument('--whisper_model', default='tiny')
    parser.add_argument('--report_every', type=int, default=10)
    args = parser.parse_args()

    files = gather_pairs(limit=args.limit)
    speakers = sorted(set(p[1] for p in files))
    test_speakers = set(speakers[-args.test_speakers:])
    train_files = [f for f in files if f[1] not in test_speakers]
    test_files = [f for f in files if f[1] in test_speakers]
    print(f'utterances:    {len(files)}')
    print(f'train (speakers={len(speakers) - len(test_speakers)}): '
          f'{len(train_files)}')
    print(f'test  (speakers={len(test_speakers)}): {len(test_files)}')

    print(f'\nLoading faster-whisper "{args.whisper_model}" '
          f'for forced alignment...', flush=True)
    from faster_whisper import WhisperModel
    aligner = WhisperModel(args.whisper_model, device='cpu',
                              compute_type='int8', cpu_threads=1)

    print('\nForced-aligning training audio...', flush=True)
    t0 = time.time()
    train_pairs = []
    for i, (path, sp, ch, ut) in enumerate(train_files):
        samples, fs = load_flac(path)
        pairs = force_align(aligner, samples, fs)
        train_pairs.extend([(p, w, fs) for p, w in pairs])
        if (i + 1) % args.report_every == 0:
            print(f'  align {i+1}/{len(train_files)}  '
                  f'{len(train_pairs)} word-pairs', flush=True)
    print(f'aligned {len(train_pairs)} train pairs in '
          f'{time.time() - t0:.1f}s')

    print('\nForced-aligning test audio (refs)...', flush=True)
    t0 = time.time()
    test_pairs = []  # list of (utt_id, [(segment, word), ...], ref_words)
    for i, (path, sp, ch, ut) in enumerate(test_files):
        samples, fs = load_flac(path)
        pairs = force_align(aligner, samples, fs)
        # Reference word sequence — from whisper alignment so it
        # matches what we get on test (we're benchmarking the
        # substrate's ability to relearn whisper's word output,
        # given clean per-word audio).
        ref_words = [normalise_word(w) for _, w in pairs]
        test_pairs.append((f'{sp}-{ch}-{ut}', pairs, fs, ref_words))
        if (i + 1) % args.report_every == 0:
            print(f'  align {i+1}/{len(test_files)}', flush=True)
    print(f'aligned {len(test_pairs)} test utterances in '
          f'{time.time() - t0:.1f}s')

    sub = Substrate()
    pipe = STTPipeline(STTParams(sample_rate=fs))
    pipe.attach(sub)

    print('\n--- training (substrate sees one-word segments) ---',
            flush=True)
    t0 = time.time()
    vote_counts: dict = {}
    grounded = 0
    for i, (segment, word, seg_fs) in enumerate(train_pairs):
        if pipe.params.sample_rate != seg_fs:
            pipe = STTPipeline(STTParams(sample_rate=seg_fs))
            pipe.attach(sub)
        grounded += teach_pair(sub, pipe, segment, word, vote_counts)
        sub.tick(50000)
        if (i + 1) % 200 == 0:
            n_concepts = sum(1 for _ in sub.nodes('Concept'))
            n_signs = sum(1 for _ in sub.nodes('AcousticSign'))
            print(f'  train {i+1}/{len(train_pairs)}  '
                  f'concepts={n_concepts}  signs={n_signs}  '
                  f'grounded_total={grounded}  '
                  f'{(i+1) / (time.time() - t0):.1f} pairs/sec',
                  flush=True)
    train_wall = time.time() - t0
    print(f'training done: {train_wall:.1f}s')

    print('\n--- testing ---', flush=True)
    t0 = time.time()
    total_ref = 0
    total_err = 0
    samples_shown = 0
    for utt_id, pairs, seg_fs, ref_words in test_pairs:
        hyp_words = []
        for segment, _ in pairs:
            w = predict_word(sub, pipe, segment, vote_counts)
            if w:
                hyp_words.append(w.upper())
        err = levenshtein_words(ref_words, hyp_words)
        total_ref += len(ref_words)
        total_err += err
        if samples_shown < 5:
            samples_shown += 1
            print(f'  {utt_id}:')
            print(f'    REF [{len(ref_words):3}]: {" ".join(ref_words[:15])}{"..." if len(ref_words) > 15 else ""}')
            print(f'    HYP [{len(hyp_words):3}]: {" ".join(hyp_words[:15])}{"..." if len(hyp_words) > 15 else ""}')
            print(f'    ERR        : {err}/{len(ref_words)} = '
                  f'{err / max(len(ref_words), 1):.3f}')
    test_wall = time.time() - t0

    print('\n========================================')
    print('Substrate STT — pre-aligned WordSoundWorld')
    print('========================================')
    print(f'train pairs   : {len(train_pairs)} word-segments')
    print(f'test utt      : {len(test_pairs)}  '
          f'({total_ref} reference words)')
    print(f'train wall    : {train_wall:.1f}s')
    print(f'test wall     : {test_wall:.1f}s')
    print(f'total errors  : {total_err}')
    if total_ref:
        print(f'overall WER   : {total_err / total_ref:.3f}')


if __name__ == "__main__":
    main()
