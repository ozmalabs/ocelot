"""GATE: the native segment_units primitive == the agent's graph-resident boundary
Term path (bit-for-bit chunking), for all three boundary rules; and on the real 100
fps frames() grid the `prominent` rule fixes the over-segmentation (5.9x -> ~1.1x).

  fidelity : native forward_segment chunking == Term-path chunking (median /
             local_min / prominent), on synthetic + real unit sequences.
  fix      : prominent on real LibriSpeech @100fps -> chunks/word near 1 (was 5.9x).
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "runners", "dsl", "python"))
import numpy as np
import substrate_rs as srs
import domains.forward_segmentation as FS
import scripts.librispeech_wer as L
from scripts.jabberwock_reads_oov_from_phones import frames
from scripts.context_invariant_librispeech_accept import kmeans, quantize, words_of


def _term_chunked(seqs, mode, bidir):
    """forward_segment forced onto the graph-resident Term path (native hidden)."""
    import substrate_rs
    nat = substrate_rs._native
    saved = getattr(nat, "segment_units", None)
    try:
        if saved is not None:
            del nat.segment_units
    except Exception:
        pass
    try:
        sub = srs.Substrate()
        return FS.forward_segment(sub, seqs, n_passes=1, boundary_mode=mode,
                                  bidirectional=bidir)["chunked"]
    finally:
        if saved is not None:
            nat.segment_units = saved


def _native_chunked(seqs, mode, bidir):
    sub = srs.Substrate()
    return FS.forward_segment(sub, seqs, n_passes=1, boundary_mode=mode,
                              bidirectional=bidir)["chunked"]


def main():
    rng = np.random.default_rng(0)
    print("=" * 80)
    print("SEGMENTER NATIVE PRIMITIVE GATE")
    print("=" * 80)

    # synthetic integer unit sequences with structure (repeats + transitions)
    syn = []
    for _ in range(12):
        n = int(rng.integers(20, 120))
        syn.append([int(rng.integers(0, 24)) for _ in range(n)])

    # real units at 100 fps
    pairs = L.gather_pairs(limit=40)[:30]
    Ms, words = [], []
    for path, sp, ch, ut, tr in pairs:
        try:
            M, _e = frames(L.load_flac(path)[0])
        except Exception:
            continue
        Ms.append(M); words.append(words_of(tr))
    C = kmeans(np.concatenate(Ms, 0), 48)
    real = [[int(u) for u in quantize(M, C)] for M in Ms]

    ok = True
    for name, seqs in (("synthetic", syn), ("real@100fps", real)):
        for mode in ("median", "local_min", "prominent"):
            a = _native_chunked(seqs, mode, True)
            b = _term_chunked(seqs, mode, True)
            same = (a == b)
            ok = ok and same
            print(f"  {name:14} {mode:10} native==Term: {same}")
    print("-" * 80)

    # the fix: prominent vs local_min chunks/word on real @100fps
    t = time.time()
    prom = _native_chunked(real, "prominent", True)
    lm = _native_chunked(real, "local_min", True)
    dt = time.time() - t
    nw = sum(max(len(w), 1) for w in words)
    cw_prom = sum(len(c) for c in prom) / nw
    cw_lm = sum(len(c) for c in lm) / nw
    print(f"  real@100fps chunks/word: local_min {cw_lm:.2f}  ->  prominent {cw_prom:.2f}")
    print(f"  native segment {len(real)} utts x2 modes: {dt:.3f}s")
    fix_ok = 0.7 <= cw_prom <= 1.6 and cw_lm > 2.0

    print("=" * 80)
    res = ok and fix_ok
    print(f"  fidelity {'OK' if ok else 'FAIL'} | over-seg fix {'OK' if fix_ok else 'FAIL'}")
    print(f"  {'GATE PASS' if res else 'GATE FAIL'}: native segmenter == agent Term path; "
          f"prominent rule fixes 100fps over-segmentation.")
    return 0 if res else 1


if __name__ == "__main__":
    raise SystemExit(main())
