"""GATE: the native CMVN primitive == the agent's composed CMVN Term-tree (same
numbers), and it makes frames() fast on full utterances (the LVCSR frontend wall).

  fidelity : _native.cmvn output vs the per-cell Term-eval fallback, max abs diff.
  speed    : frames() on a full ~6s LibriSpeech utterance (was ~136s on the Term loop).
  null     : a flat band (var->0) must not blow up (eps outside sqrt).
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "runners", "dsl", "python"))
import numpy as np
import domains.cmvn as C
import scripts.librispeech_wer as L
from domains.filter_settings import cochleagram

rng = np.random.default_rng(0)


def _fallback(M, **kw):
    """Force the Term-tree fallback by hiding the native primitive."""
    import substrate_rs
    nat = substrate_rs._native
    saved = nat.cmvn
    try:
        del nat.cmvn                      # AttributeError -> except: pass -> fallback
    except Exception:
        pass
    try:
        return C.apply_cmvn(M, **kw)
    finally:
        nat.cmvn = saved


def main():
    print("=" * 78)
    print("CMVN NATIVE PRIMITIVE GATE")
    print("=" * 78)

    # 1) fidelity on random + real matrices, mean+var and mean-only
    worst = 0.0
    for trial in range(6):
        nf = int(rng.integers(8, 120)); nb = 32
        M = rng.standard_normal((nf, nb)).astype(np.float64) * rng.uniform(0.2, 3.0)
        for dv in (True, False):
            a = C.apply_cmvn(M, do_variance=dv)          # native
            b = _fallback(M, do_variance=dv)             # agent Term-tree
            d = float(np.max(np.abs(a.astype(np.float64) - b.astype(np.float64))))
            worst = max(worst, d)
    print(f"  fidelity (native vs Term-tree) max abs diff: {worst:.2e}")
    fid_ok = worst < 1e-4

    # 2) flat-band null: a constant band must stay finite (var=0, eps outside sqrt)
    Mf = rng.standard_normal((20, 32)).astype(np.float64)
    Mf[:, 7] = 5.0                                        # flat band
    of = C.apply_cmvn(Mf, do_variance=True)
    flat_ok = np.all(np.isfinite(of)) and abs(float(of[:, 7].std())) < 1e-3

    # 3) speed: frames() on a full real utterance
    from scripts.jabberwock_reads_oov_from_phones import frames
    x, fs = L.load_flac(L.gather_pairs(limit=1)[0][0])
    t = time.time(); M, _e = frames(x); dt = time.time() - t
    print(f"  flat-band finite + collapsed: {flat_ok}")
    print(f"  frames() full utterance ({len(x)/fs:.1f}s -> {M.shape}): {dt:.2f}s")
    speed_ok = dt < 5.0 and np.all(np.isfinite(M))

    print("=" * 78)
    ok = fid_ok and flat_ok and speed_ok
    print(f"  fidelity {'OK' if fid_ok else 'FAIL'} | flat-null {'OK' if flat_ok else 'FAIL'} | "
          f"speed {'OK' if speed_ok else 'FAIL'}")
    print(f"  {'GATE PASS' if ok else 'GATE FAIL'}: native CMVN == agent Term-tree, "
          f"frontend no longer walls on full utterances.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
