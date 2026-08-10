"""Why the agent's segmenter over-segments the 100 fps frames() grid, and which of
its OWN designed options fixes it — measured, parameter-free, on real LibriSpeech.

frames() runs 100 fps (~34 frames/word); the segmenter eval that gave ~1 chunk/word
ran frames_of (capped 64 frames/utt, ~3-4 frames/word). local_min trough density
scales with frame count -> ~9x finer grid -> ~5.6x over-segmentation.

Candidate fixes, ALL from the agent's own design space (no swept knob):
  - corpus TP   : estimate the TP structure over ALL utterances (statistical
                  learning over the corpus), not one utterance in isolation. The
                  real pass segmented each utt with its own sparse bigrams.
  - RLE merge   : collapse runs of the SAME unit before reading troughs. A self-
                  transition (a->a) is the maximum-TP pair = the limit case of the
                  segmenter's OWN "merge high-TP runs" step; collapsing it makes the
                  unit stream grid-INVARIANT (doubling fps just lengthens runs).
  - iterate     : the agent's bottom-up build (chunks become the new alphabet;
                  re-chunk) climbs phone-scale troughs -> word-scale, with the
                  structural degenerate-TP stop deciding when.

Metric (identical to jabberwock_segmenter_localmin_eval): word-boundary F1 (tol
0.06s, vs proportional word boundaries) + chunks/words ratio (target ~1.0).
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
import substrate_rs as srs
import scripts.librispeech_wer as L
from scripts.context_invariant_librispeech_accept import (
    proportional_word_boundaries, chunk_boundary_times, boundary_f1)
from scripts.jabberwock_reads_oov_from_phones import frames, FS, FPS
from scripts.context_invariant_librispeech_accept import kmeans, quantize, words_of
from domains.forward_segmentation import forward_segment


def rle(units):
    """Collapse runs of the same unit -> (symbols, frame_lengths). Grid-invariant
    pre-merge: the agent's max-TP self-transition merge, the limit case."""
    syms, lens = [], []
    for u in units:
        if syms and syms[-1] == u:
            lens[-1] += 1
        else:
            syms.append(u); lens.append(1)
    return syms, lens


def main():
    n_utts = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    pairs = L.gather_pairs(limit=n_utts + 60)[:n_utts]
    print("=" * 92)
    print("SEGMENTER on the 100 fps frames() grid — which agent-designed option fixes over-seg")
    print("=" * 92)

    Ms, times_, words_seqs, durs = [], [], [], []
    t0 = time.time()
    for i, (path, sp, ch, ut, tr) in enumerate(pairs):
        try:
            x, fs = L.load_flac(path); M, _e = frames(x)
        except Exception:
            continue
        dur = len(x) / FS
        Ms.append(M); durs.append(dur)
        times_.append(list(np.linspace(0, dur, len(M))))
        words_seqs.append(words_of(tr))
        if (i + 1) % 10 == 0:
            print(f"  framed {i+1}/{n_utts} [{time.time()-t0:.0f}s]", flush=True)
    print(f"  framed {len(Ms)} utts @ {FPS}fps "
          f"(mean {np.mean([len(M) for M in Ms]):.0f} frames, "
          f"{np.mean([len(M)/max(len(w),1) for M, w in zip(Ms, words_seqs)]):.1f} frames/word)",
          flush=True)

    C = kmeans(np.concatenate(Ms, 0), 48)
    unit_seqs = [quantize(M, C) for M in Ms]

    def f1_ratio(seqs, frame_lens, npass, mode):
        """Segment the (possibly RLE'd) corpus, score F1 + chunks/words. frame_lens
        maps each symbol to its frame count so chunk boundaries -> frame times."""
        sub = srs.Substrate()                       # fresh: no stale Transitions
        res = forward_segment(sub, seqs, n_passes=npass, boundary_mode=mode,
                              bidirectional=True)
        chunked = res["chunked"] or [[(u,) for u in s] for s in seqs]
        f1 = nch = nw = n = 0.0
        for chunks, fl, times, words in zip(chunked, frame_lens, times_, words_seqs):
            # frames per chunk = sum of its symbols' frame lengths (flatten chunk)
            cuts_fr, pos = [], 0
            flat = []
            for c in chunks:
                k = c if isinstance(c, tuple) else (c,)
                flat.append(sum(1 for _ in _flatten(k)))
            # map symbol index -> frame length via fl, accumulate per chunk
            sidx = 0; clens_fr = []
            for c in chunks:
                m = sum(1 for _ in _flatten(c if isinstance(c, tuple) else (c,)))
                clens_fr.append(sum(fl[sidx:sidx + m])); sidx += m
            con_b = chunk_boundary_times(times, clens_fr)
            true_b = proportional_word_boundaries(words, 0.0, times[-1] if times else 0.0)
            f1 += boundary_f1(con_b, true_b, 0.06)[2]
            nch += len(chunks); nw += max(len(words), 1); n += 1
        return f1 / max(n, 1), nch / max(nw, 1)

    # frame-length tables: raw = 1 frame/unit; rle = run lengths
    raw_lens = [[1] * len(s) for s in unit_seqs]
    rle_pairs = [rle(s) for s in unit_seqs]
    rle_seqs = [p[0] for p in rle_pairs]
    rle_lens = [p[1] for p in rle_pairs]
    print(f"  raw units/utt {np.mean([len(s) for s in unit_seqs]):.0f} -> "
          f"RLE units/utt {np.mean([len(s) for s in rle_seqs]):.0f} "
          f"(RLE units/word {np.mean([len(s)/max(len(w),1) for s, w in zip(rle_seqs, words_seqs)]):.1f})",
          flush=True)

    print(f"\n   {'config (agent design)':46} {'F1':>6} {'chunks/words':>13}")
    configs = [
        ("local_min 1pass, raw 100fps (current)",   unit_seqs, raw_lens, 1, "local_min"),
        ("local_min 2pass, raw",                     unit_seqs, raw_lens, 2, "local_min"),
        ("local_min 1pass, RLE merge",               rle_seqs,  rle_lens, 1, "local_min"),
        ("median   1pass, RLE merge",                rle_seqs,  rle_lens, 1, "median"),
        ("prominent 1pass, raw 100fps",              unit_seqs, raw_lens, 1, "prominent"),
        ("prominent 1pass, RLE merge",               rle_seqs,  rle_lens, 1, "prominent"),
        ("prominent 2pass, RLE merge",               rle_seqs,  rle_lens, 2, "prominent"),
    ]
    best = (0.0, None)
    for name, seqs, fl, npass, mode in configs:
        f1, ratio = f1_ratio(seqs, fl, npass, mode)
        flag = "  <- ~1 chunk/word" if 0.7 <= ratio <= 1.4 else ""
        print(f"   {name:46} {f1:6.3f} {ratio:13.2f}{flag}", flush=True)
        if f1 > best[0]:
            best = (f1, name, ratio)
    print("=" * 92)
    print(f"  best F1 (agent-designed): {best[1]} -> F1 {best[0]:.3f}, chunks/words {best[2]:.2f}")
    return 0


def _flatten(t):
    for x in t:
        if isinstance(x, tuple):
            yield from _flatten(x)
        else:
            yield x


if __name__ == "__main__":
    raise SystemExit(main())
