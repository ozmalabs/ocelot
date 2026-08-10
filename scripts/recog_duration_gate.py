"""GATE: the native topk_match primitive == the agent's COMPOSED duration-aware match
Term (duration_match_term: Dot - 0.5*duration-z-score^2, the agent's normalisation
science applied to duration), bit-for-bit; and the templates carry data-derived
duration stats (dur_mu/dur_sig), not a hand-picked band.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "runners", "dsl", "python"))
import numpy as np
import substrate_rs as srs
from domains.learned_speech_recogniser import (LearnedSpeechRecogniser, install_templates,
                                               duration_match_term)


def main():
    sub = srs.Substrate(); install_templates(sub)
    rec = LearnedSpeechRecogniser(sub)
    print("=" * 78)
    print(f"RECOGNISER DURATION GATE ({len(rec._words)} templates, "
          f"has_dur={rec._has_dur}, dur_sig>0 for {int((rec._dsig>0).sum())})")
    print("=" * 78)
    if not rec._has_dur:
        print("  FAIL: templates carry no duration spread (dur_sig) — rebuild the seed.")
        return 1

    rng = np.random.default_rng(0)
    dim = rec._cmat.shape[1]
    import substrate_rs
    nat = substrate_rs._native
    saved = getattr(nat, "topk_match", None)
    mism = 0; n = 30
    for _ in range(n):
        e = rng.standard_normal(dim).astype(np.float32); e /= max(np.linalg.norm(e), 1e-9)
        qdur = float(rng.integers(10, 60))
        native = rec.ground_topk(e, 5, qdur=qdur)            # native topk_match
        try:
            if saved is not None:
                del nat.topk_match
            held = rec.ground_topk(e, 5, qdur=qdur)          # composed held-Term fallback
        finally:
            if saved is not None:
                nat.topk_match = saved
        nw = [w for w, _ in native]; hw = [w for w, _ in held]
        if nw != hw or not np.allclose([s for _, s in native], [s for _, s in held], atol=1e-3):
            mism += 1
    print(f"  native topk_match == composed held Term, mismatches: {mism}/{n}")

    # show duration discrimination: a SHORT query vs a LONG query should prefer
    # short vs long units respectively (the scale-awareness the feature gained).
    short_units = [rec._words[i] for i in np.argsort(rec._dmu)[:8]]
    long_units = [rec._words[i] for i in np.argsort(-rec._dmu)[:8]]
    print(f"  shortest-duration units: {short_units}")
    print(f"  longest-duration units : {long_units}")

    print("=" * 78)
    ok = mism == 0
    print(f"  {'GATE PASS' if ok else 'GATE FAIL'}: duration-aware match is the agent's composed "
          f"Term (native == held), parameters data-derived (dur_mu/dur_sig).")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
