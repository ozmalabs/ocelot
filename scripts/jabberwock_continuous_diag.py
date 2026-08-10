"""Diagnose the continuous-sentence recognition floor (WER ~1.0): is it (a) OPEN-VOCAB
coverage (test words never taught -> uncorrectable), (b) recognition quality, or
(c) segmentation count? Measures each at moderate scale on real LibriSpeech.

Reports:
  - overall WER (the floored baseline)
  - VOCAB COVERAGE ceiling: fraction of test reference words ever grounded in training
    (the max recall any recogniser could reach with this vocab) -> if low, open-vocab
    is the floor and 'fixing recognition' cannot help until the vocab is covered.
  - segmentation: hypothesised words vs reference words (insertion/deletion pressure).

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_continuous_diag.py [n_train] [n_test]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import scripts.librispeech_wer as L
from substrate_rs import Substrate
from domains.stt_pipeline import STTPipeline, STTParams


def main():
    n_train = int(sys.argv[1]) if len(sys.argv) > 1 else 400
    n_test = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    pairs = L.gather_pairs(limit=n_train + 300)
    speakers = sorted(set(p[1] for p in pairs))
    test_spk = set(speakers[-6:])
    train = [p for p in pairs if p[1] not in test_spk][:n_train]
    test = [p for p in pairs if p[1] in test_spk][:n_test]
    print("=" * 84)
    print("CONTINUOUS RECOGNITION FLOOR — diagnosis")
    print("=" * 84)
    print(f"  train {len(train)} utts / test {len(test)} utts (held-out speakers)")

    sub = Substrate()
    fs0 = L.load_flac(train[0][0])[1]
    pipe = STTPipeline(STTParams(sample_rate=fs0)); pipe.attach(sub)
    vc = {}
    t0 = time.time()
    for i, (path, sp, ch, ut, tr) in enumerate(train):
        s, fs = L.load_flac(path)
        if pipe.params.sample_rate != fs:
            pipe = STTPipeline(STTParams(sample_rate=fs)); pipe.attach(sub)
        try:
            pipe.teach_via_valleys(sub, s, tr, vote_counts=vc); sub.tick(50000)
        except Exception:
            continue
        if (i + 1) % 100 == 0:
            print(f"   trained {i+1}/{len(train)}  [{time.time()-t0:.0f}s]", flush=True)
    grounded = set(w for (_sk, w) in vc.keys())
    print(f"  trained: {len(train)} utts, grounded vocab = {len(grounded)} distinct words")

    total_ref = total_err = 0
    cov_hit = cov_tot = 0
    hyp_words = ref_words = 0
    for (path, sp, ch, ut, tr) in test:
        s, fs = L.load_flac(path)
        ref = L.normalise(tr)
        try:
            hyp = L.normalise(pipe.transcribe_via_votes(sub, s, vc))
        except Exception:
            hyp = []
        total_err += L.levenshtein_words(ref, hyp); total_ref += len(ref)
        ref_words += len(ref); hyp_words += len(hyp)
        for w in ref:
            cov_tot += 1; cov_hit += (w.lower() in grounded)

    wer = total_err / max(total_ref, 1)
    print("\n" + "=" * 84)
    print(f"  overall WER                : {wer:.3f}   (floored baseline)")
    print(f"  VOCAB COVERAGE ceiling     : {cov_hit/max(cov_tot,1):.3f}  "
          f"({cov_hit}/{cov_tot} test ref words were ever grounded)")
    print(f"  segmentation hyp/ref words : {hyp_words}/{ref_words} = {hyp_words/max(ref_words,1):.2f}x")
    print("=" * 84)
    cov = cov_hit / max(cov_tot, 1)
    if cov < 0.6:
        print(f"  -> OPEN-VOCAB is the floor: {1-cov:.0%} of test words were NEVER taught -> uncorrectable.")
        print("     Fixing continuous recognition needs large-vocab coverage (orders more data), not a")
        print("     better matcher. WER ~1.0 is mostly OOV + the prototype's weak grounding.")
    else:
        print("  -> vocab is covered; the floor is recognition/segmentation (fixable by the learned recogniser).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
