"""Corrected continuous fix step 1: STRONG graded fallback INSIDE the real
transcribe_via_votes (not a reimplementation).

Lessons from the null (d984aed5): (1) use the REAL transcribe walk; (2) use a STRONG
matcher (DtwTo, alignment-aware), not raw cosine. So: the agent edits its own pipeline
(SelfModification) to add an optional `graded` callable used ONLY in the no-vote branch;
the callable matches a dropped sign's A1-patch trajectory to the nearest TRAINED sign by
a cosine PRE-FILTER (cheap) -> DtwTo RESCORE (the held Term, strong) and inherits its word.

Same real walk + same segmentation; the only change is recovering dropped signs with the
strong matcher. Head-to-head WER (held-out speakers): baseline (graded=None) vs graded.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_continuous_graded_v2.py [n_train] [n_test] [M]
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


def _resh(tj):
    t = [float(x) for x in tj]
    n = len(t) // 25 if len(t) >= 25 else 1
    return [t[i * 25:(i + 1) * 25] for i in range(n)]


def _emb(tj):
    v = np.asarray(tj, float).ravel()
    return v / max(np.linalg.norm(v), 1e-9)


def main():
    n_train = int(sys.argv[1]) if len(sys.argv) > 1 else 250
    n_test = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    M = int(sys.argv[3]) if len(sys.argv) > 3 else 12

    mod = SelfModification()
    src = mod.read(PIPE)
    print("=" * 86)
    print("CONTINUOUS FIX v2 — strong graded fallback in the REAL transcribe (edit + measure)")
    print("=" * 86)
    for label, old, new in [("signature +graded", OLD_SIG, NEW_SIG), ("no-vote graded fallback", OLD_FB, NEW_FB)]:
        if new.split("\n")[1] if False else (new in mod.read(PIPE)):
            print(f"  [skip] {label}")
        else:
            r = mod.edit(PIPE, old, new)
            print(f"  [edit] {label}: ok={r.get('ok')}{' ROLLED BACK' if r.get('rolled_back') else ''}")
            if not r.get("ok"):
                print(f"         {r.get('result')}"); return 1
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
    vote_word = {sk: wc[0] for sk, wc in best.items()}
    E, TR, WD = [], [], []
    for n in sub.nodes("AcousticSign"):
        k = _node_sort_key(n); tj = sub.node(n)["attrs"].get("trajectory")
        if k in vote_word and tj and len(tj) >= 25:
            E.append(_emb(tj)); TR.append(_resh(tj)); WD.append(vote_word[k])
    E = np.array(E)
    inner = sub._inner
    print(f"  graded exemplars: {len(E)}", flush=True)

    def dtw(a, b):
        return float(inner.evaluate({"type": "DtwTo", "a": {"type": "Lit", "value": a},
                                     "b": {"type": "Lit", "value": b}}, {}))

    def graded(sub_, sign):
        tj = sub_.node(sign)["attrs"].get("trajectory")
        if not tj or len(tj) < 25 or not len(E):
            return None
        q = _emb(tj); top = np.argsort(-(E @ q))[:M]; qr = _resh(tj)
        bd, bw = 1e18, None
        for i in top:
            d = dtw(qr, TR[int(i)])
            if d < bd:
                bd, bw = d, WD[int(i)]
        return bw

    def wer(use_graded):
        te = ref = hyp = 0
        for (path, sp, ch, ut, tr) in test:
            s, fs = L.load_flac(path)
            if pipe.params.sample_rate != fs:
                continue
            rf = L.normalise(tr)
            h = L.normalise(pipe.transcribe_via_votes(sub, s, vc, graded=(graded if use_graded else None)))
            te += L.levenshtein_words(rf, h); ref += len(rf); hyp += len(h)
        return te / max(ref, 1), hyp, ref

    t1 = time.time(); base_w, base_h, ref = wer(False)
    grad_w, grad_h, _ = wer(True)
    print(f"  (test {time.time()-t1:.0f}s)")
    print("\n" + "=" * 86)
    print(f"  EXACT baseline : WER {base_w:.3f}   hyp/ref {base_h}/{ref} = {base_h/max(ref,1):.2f}x")
    print(f"  + GRADED DtwTo : WER {grad_w:.3f}   hyp/ref {grad_h}/{ref} = {grad_h/max(ref,1):.2f}x")
    print("=" * 86)
    print(f"  delta WER (baseline - graded) = {base_w-grad_w:+.3f}  -> "
          f"{'GRADED RECOVERY LOWERS WER' if base_w-grad_w > 0.02 else 'no net WER gain (recovered words still wrong)'}")
    mod.restore(PIPE)                                # leave the pipeline as found (additive change reverted)
    print("  (pipeline restored; graded= param is the proposed additive change)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
