"""Run faster-whisper on the same LibriSpeech subset for honest
throughput / memory comparison vs the substrate STT.

NOT a quality comparison — whisper produces text, substrate produces
emergent signs. Until we ground signs to LibriSpeech transcripts
(step 2 of the plan), there's no shared output surface for WER. What
we CAN compare today: how many seconds of audio each system
processes per wall-clock second, peak memory, and cold-start cost.

The substrate runs (see scripts/librispeech_benchmark.py) measure
the same files; cross-reference for an apples-to-apples wall-clock
result.
"""
import os
import re
import sys
import time
import resource

import av
import numpy as np

from faster_whisper import WhisperModel


DATA_DIR = '/tmp/LibriSpeech/dev-clean'
_FN_RE = re.compile(r'(\d+)-(\d+)-(\d+)\.flac')


def list_files(limit=None):
    files = []
    for root, _, names in os.walk(DATA_DIR):
        for fn in names:
            m = _FN_RE.match(fn)
            if not m:
                continue
            files.append(os.path.join(root, fn))
    files.sort()
    return files[:limit] if limit else files


def load_flac(path):
    c = av.open(path)
    s = c.streams.audio[0]
    arr = np.concatenate([
        f.to_ndarray().flatten().astype(np.float32)
        for f in c.decode(s)
    ])
    rate = s.rate
    c.close()
    return arr, rate, len(arr) / rate


def peak_mem_mb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', default='tiny',
                        help='whisper model size (tiny / base / small)')
    parser.add_argument('--limit', type=int, default=200,
                        help='number of LibriSpeech files to process')
    parser.add_argument('--threads', type=int, default=1,
                        help='CPU threads for inference (1 = single-thread, '
                             'matches substrate which is single-process)')
    args = parser.parse_args()

    files = list_files(limit=args.limit)
    print(f'Loading faster-whisper "{args.model}" (CPU, '
          f'{args.threads} threads)...', flush=True)
    t_load = time.time()
    model = WhisperModel(args.model, device='cpu', compute_type='int8',
                          cpu_threads=args.threads)
    load_ms = (time.time() - t_load) * 1000
    print(f'Loaded in {load_ms:.0f} ms. Mem after load: '
          f'{peak_mem_mb():.0f} MB', flush=True)

    total_audio_s = 0.0
    total_wall_s = 0.0
    first_file_wall = None
    failures = 0
    for i, path in enumerate(files):
        try:
            samples, fs, dur = load_flac(path)
            total_audio_s += dur
            t0 = time.time()
            segments, _ = model.transcribe(samples, language='en',
                                              beam_size=1)
            # Force consume the generator to actually do the work.
            for _ in segments:
                pass
            dt = time.time() - t0
            total_wall_s += dt
            if first_file_wall is None:
                first_file_wall = dt
        except Exception as e:
            print(f'  FAIL {path}: {e}', flush=True)
            failures += 1
            continue
        if (i + 1) % 25 == 0:
            rtf = total_audio_s / total_wall_s if total_wall_s > 0 else 0
            print(f'  {i+1}/{len(files)}  audio={total_audio_s:.1f}s  '
                  f'wall={total_wall_s:.1f}s  RTF={rtf:.1f}×  '
                  f'mem={peak_mem_mb():.0f} MB', flush=True)

    print()
    print('=' * 72)
    print(f'faster-whisper {args.model} on LibriSpeech dev-clean subset')
    print('=' * 72)
    print(f'files processed:      {len(files) - failures}/{len(files)}  '
          f'(failures: {failures})')
    print(f'total audio:          {total_audio_s:.1f} s '
          f'({total_audio_s/60:.1f} min)')
    print(f'total wall (inference): {total_wall_s:.1f} s')
    print(f'real-time factor (RTF): {total_audio_s/total_wall_s:.1f}× '
          f'(audio_sec / wall_sec)')
    print(f'avg per-file inference: '
          f'{total_wall_s/max(len(files)-failures,1)*1000:.0f} ms')
    print(f'cold-start (first file): {first_file_wall*1000:.0f} ms')
    print(f'peak memory:          {peak_mem_mb():.0f} MB')


if __name__ == '__main__':
    main()
