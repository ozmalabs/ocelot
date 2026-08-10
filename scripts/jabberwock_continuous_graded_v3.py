"""Continuous fix v3 — FEATURE RECONCILIATION: apply the strong-feature TRANSFORMS
(peel speaker + velocity, which earned the 0.75 isolated lift) to the continuous path's
A1-patch trajectories, then graded-match in THAT space.

v2 failed because it matched the RAW A1-patch trajectory (no speaker peel, no velocity).
The 0.75 recogniser's power is the TRANSFORM: per-frame L2 -> peel the per-patch mean
(speaker shape) -> append velocity (residual). Apply that same transform to the A1-patch
(no slow cochleagram needed; A1-patch is already a fixed 32-frame spectral trajectory),
build per-word exemplars, and recover dropped signs by fixed-length COSINE in the
peeled+velocity space (fast). Strong matcher in a strong feature space, inside the REAL
transcribe (graded= fallback).

Head-to-head WER (held-out speakers): baseline vs graded.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_continuous_graded_v3.py [n_train] [n_test]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
from domains.self_modification import SelfModification

PIPE = "domains/stt_pipeline.py"
OLD_SIG = ("    def transcribe_via_votes(self, sub, audio_samples: np.ndarray,\n"
           "                                 vote_counts: dict,\n"
           "                                 prefer_composed: bool = True) -> str:")
NEW_SIG = ("    def transcribe_via_votes(self, sub, audio_samples: np.ndarray,\n"
           "                                 vote_counts: dict,\n"
           "                                 prefer_composed: bool = True, graded=None) -> str:")
OLD_FB = ("                    best_word = sub.node(c)[\"attrs\"].get(\"name\")\n"
          "            if best_word and (not out_words or out_words[-1] != best_word):")
NEW_FB = ("                    best_word = sub.node(c)[\"attrs\"].get(\"name\")\n"
          "            if best_word is None and graded is not None:\n"
          "                best_word = graded(sub, sign)\n"
          "            if best_word and (not out_words or out_words[-1] != best_word):")


def strong_feat(traj):
    """The strong-feature transform on an A1-patch trajectory: per-frame L2 -> peel the
    per-patch mean (speaker shape) -> append velocity (residual) -> flatten + L2."""
    t = np.asarray(traj, float)
    n = len(t) // 25
    if n < 2:
        return None
    A = t[:n * 25].reshape(n, 25)
    A = A / np.clip(np.linalg.norm(A, axis=1, keepdims=True), 1e-9, None)   # per-frame L2
    P = A - A.mean(0)                                                       # peel speaker shape
    V = np.vstack([np.zeros((1, 25)), np.diff(P, axis=0)])                  # velocity (residual)
    # fixed length: A1-patch frame count varies; resample P,V to L=16
    Lf = 16
    def rs(X):
        m = len(X)
        if m == Lf:
            return X
        idx = np.linspace(0, m - 1, Lf); lo = np.floor(idx).astype(int); hi = np.clip(lo + 1, 0, m - 1)
        w = (idx - lo)[:, None]
        return X[lo] * (1 - w) + X[hi] * w
    F = np.concatenate([rs(P), rs(V)], axis=1).reshape(-1)
    return F / max(np.linalg.norm(F), 1e-9)


def main():
    n_train = int(sys.argv[1]) if len(sys.argv) > 1 else 250
    n_test = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    mod = SelfModification()
    print("=" * 86)
    print("CONTINUOUS FIX v3 — feature reconciliation (peel+velocity on A1-patch), strong cosine")
    print("=" * 86)
    for label, old, new in [("signature +graded", OLD_SIG, NEW_SIG), ("graded fallback", OLD_FB, NEW_FB)]:
        if new in mod.read(PIPE):
            print(f"  [skip] {label}")
        else:
            r = mod.edit(PIPE, old, new); print(f"  [edit] {label}: ok={r.get('ok')}")
            if not r.get("ok"):
                return 1
    mod.reload_python("domains.stt_pipeline")

    import scripts.librispeech_wer as L
    from substrate_rs import Substrate
    from domains.stt_pipeline import STTPipeline, STTParams, _node_sort_key

    pairs = L.gather_pairs(limit=n_train + 300)
    spk = sorted(set(p[1] for p in pairs)); test_spk = set(spk[-6:])
    train = [p for p in pairs if p[1] not in test_spk][:n_train]
    test = [p for p in pairs if p[1] in test_spk][:n_test]
    print(f"  train {len(train)} / test {len(test)} (held-out speakers)")
    sub = Substrate(); fs0 = L.load_flac(train[0][0])[1]
    pipe = STTPipeline(STTParams(sample_rate=fs0)); pipe.attach(sub)
    vc = {}; t0 = time.time()
    for i, (path, sp, ch, ut, tr) in enumerate(train):
        s, fs = L.load_flac(path)
        if pipe.params.sample_rate != fs:
            pipe = STTPipeline(STTParams(sample_rate=fs)); pipe.attach(sub)
        try:
            pipe.teach_via_valleys(sub, s, tr, vote_counts=vc); sub.tick(50000)
        except Exception:
            continue
        if (i + 1) % 100 == 0:
            print(f"   trained {i+1}/{len(train)} [{time.time()-t0:.0f}s]", flush=True)

    best = {}
    for (sk, w), c in vc.items():
        if sk not in best or c > best[sk][1]:
            best[sk] = (w, c)
    vw = {sk: wc[0] for sk, wc in best.items()}
    E, WD = [], []
    for n in sub.nodes("AcousticSign"):
        k = _node_sort_key(n); tj = sub.node(n)["attrs"].get("trajectory")
        if k in vw and tj:
            f = strong_feat(tj)
            if f is not None:
                E.append(f); WD.append(vw[k])
    E = np.array(E)
    print(f"  strong exemplars: {len(E)}  (dim {E.shape[1] if len(E) else 0})", flush=True)

    def graded(sub_, sign):
        tj = sub_.node(sign)["attrs"].get("trajectory")
        if not tj or not len(E):
            return None
        f = strong_feat(tj)
        if f is None:
            return None
        return WD[int((E @ f).argmax())]

    def wer(g):
        te = ref = hyp = 0
        for (path, sp, ch, ut, tr) in test:
            s, fs = L.load_flac(path)
            if pipe.params.sample_rate != fs:
                continue
            rf = L.normalise(tr)
            h = L.normalise(pipe.transcribe_via_votes(sub, s, vc, graded=(graded if g else None)))
            te += L.levenshtein_words(rf, h); ref += len(rf); hyp += len(h)
        return te / max(ref, 1), hyp, ref

    bw, bh, ref = wer(False); gw, gh, _ = wer(True)
    print("\n" + "=" * 86)
    print(f"  EXACT baseline           : WER {bw:.3f}   hyp/ref {bh}/{ref} = {bh/max(ref,1):.2f}x")
    print(f"  + GRADED (peel+vel A1)   : WER {gw:.3f}   hyp/ref {gh}/{ref} = {gh/max(ref,1):.2f}x")
    print("=" * 86)
    print(f"  delta WER (baseline - graded) = {bw-gw:+.3f}  -> "
          f"{'FEATURE RECONCILIATION HELPS' if bw-gw > 0.02 else 'still no net gain'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
