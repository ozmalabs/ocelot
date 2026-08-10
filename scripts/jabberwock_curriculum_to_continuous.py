"""The jabberwock iterates the curriculum UP to continuous speech — you cannot skip to the end.

Creator: "iterate the curriculum up to continuous speech. you cannot skip to the end." A child
climbs the difficulty ladder: CLEAREST isolated words -> moderate -> reduced -> CONTINUOUS, each
stage's model force-aligning the next harder tier (bootstrap), accumulating cleaner labels. The
clear-first stage already beat flat-start (+28%); now stage all the way to continuous.

  tiers (frames-per-phone, hardness ascending): t1 clearest isolated -> t2 moderate -> t3 reduced
  isolated -> t4 CONTINUOUS utterances (co-articulated, long, the destination).
  stage 0: fit on t1 with proportional alignment (clean — long well-separated phones).
  stage k: the current model VITERBI FORCE-ALIGNS tier k -> add -> refit. Climb.

Measures per-frame phone acc (fixed model-independent isolated-dev set) at each stage, and the
DESTINATION: continuous-dev per-frame for the curriculum model vs FLAT-START straight on
continuous (the thing that couldn't skip to the end).

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_curriculum_to_continuous.py [cap] [n_cont]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
import scripts.librispeech_wer as L
from scripts.jabberwock_reads_oov_from_phones import frames, phones as cmu_phones
from scripts.jabberwock_subword_recognizer import _load_ph
from scripts.jabberwock_earns_phone_model import ctxd, fit_model, phone_emission, viterbi_align
from scripts.jabberwock_earns_acoustic_phonetic import gather, utt_phones


def fpp(fr, ph):
    return len(fr) / max(len(ph), 1)


def proportional(items, cap):
    X, Y = [], []
    for fr, ph in items:
        cx = ctxd(fr); n = len(cx); P = len(ph)
        for i in range(n):
            X.append(cx[i]); Y.append(ph[int(i * P / n)])
        if len(X) >= cap:
            break
    return np.array(X), Y


def force_align(items, enc, cent, cph, pi, phset, cap):
    """current model Viterbi-force-aligns each (frames, phone_list) -> (feature, phone) pairs."""
    nP = len(phset); X, Y = [], []
    for fr, ph in items:
        seq = [p for p in ph if p in pi]
        if len(seq) < 1 or len(fr) < len(seq):
            continue
        cx = ctxd(fr)
        labs = viterbi_align(phone_emission(cx, enc, cent, cph, nP), [pi[p] for p in seq])
        for i in range(len(cx)):
            X.append(cx[i]); Y.append(phset[labs[i]])
        if len(X) >= cap:
            break
    return np.array(X), Y


def eval_model(enc, cent, cph, phset, pi, Xde, Yde):
    keep = [k for k in range(len(Yde)) if Yde[k] in pi]
    pred = cph[(enc(Xde[keep]) @ cent.T).argmax(1)]
    return float(np.mean([phset[pred[i]] == Yde[keep[i]] for i in range(len(keep))]))


def main():
    cap = int(sys.argv[1]) if len(sys.argv) > 1 else 35000
    n_cont = int(sys.argv[2]) if len(sys.argv) > 2 else 250
    tr = _load_ph("train-clean-100_*.pkl", 12)
    dv = _load_ph("dev-clean_*.pkl", 12)
    phset = sorted({p for _w, _f, ph in tr for p in ph}); pi = {p: i for i, p in enumerate(phset)}
    fv = np.array([fpp(fr, ph) for _w, fr, ph in tr])
    hi, mid = np.percentile(fv, 66), np.percentile(fv, 33)
    def tier(data, kind):
        out = []
        for w, fr, ph in data:
            v = fpp(fr, ph)
            if (kind == "t1" and v >= hi) or (kind == "t2" and mid <= v < hi) or (kind == "t3" and v < mid):
                out.append((fr, ph))
        return out
    print("=" * 82)
    print(f"CURRICULUM UP TO CONTINUOUS — t1 clearest >= {hi:.1f} f/phone, t3 reduced < {mid:.1f}")
    print("=" * 82)

    # fixed model-independent eval: isolated dev words, proportional (clean enough for trajectory)
    devX, devY = proportional([(fr, ph) for _w, fr, ph in dv], 15000)
    # continuous train + dev items
    cont_tr = [(frames(L.load_flac(p)[0])[0], utt_phones(t)) for p, t in gather("train-clean-100", n_cont)]
    cont_dv = [(frames(L.load_flac(p)[0])[0], utt_phones(t)) for p, t in gather("dev-clean", 120)]
    print(f"  framed continuous: train {len(cont_tr)}  dev {len(cont_dv)}", flush=True)

    # ---- the climb: t1 (proportional) -> force-align t2 -> t3 -> continuous ----
    t0 = time.time()
    X, Y = proportional([(fr, ph) for fr, ph in tier(tr, "t1")], cap)
    enc, cent, cph = fit_model(X, Y, phset, pi)
    print(f"  stage 0  t1 clearest (proportional)     : iso-dev per-frame {eval_model(enc,cent,cph,phset,pi,devX,devY):.3f}", flush=True)
    plan = [("t2 moderate", tier(tr, "t2")), ("t3 reduced", tier(tr, "t3")), ("CONTINUOUS", cont_tr)]
    for k, (name, items) in enumerate(plan, 1):
        Xk, Yk = force_align(items, enc, cent, cph, pi, phset, cap)
        X = np.concatenate([X, Xk]); Y = Y + list(Yk)
        enc, cent, cph = fit_model(X, Y, phset, pi)
        print(f"  stage {k}  +{name:22}: iso-dev per-frame {eval_model(enc,cent,cph,phset,pi,devX,devY):.3f}", flush=True)
    cur_enc, cur_cent, cur_cph = enc, cent, cph

    # DESTINATION: continuous-dev per-frame, curriculum (force-align dev with final model) vs flat-start
    cXd, cYd = force_align(cont_dv, cur_enc, cur_cent, cur_cph, pi, phset, 15000)
    cur_cont = eval_model(cur_enc, cur_cent, cur_cph, phset, pi, cXd, cYd)
    # flat-start: train straight on continuous (proportional, no curriculum)
    fX, fY = proportional(cont_tr, cap)
    f_enc, f_cent, f_cph = fit_model(fX, fY, phset, pi)
    fXd, fYd = force_align(cont_dv, f_enc, f_cent, f_cph, pi, phset, 15000)
    flat_cont = eval_model(f_enc, f_cent, f_cph, phset, pi, fXd, fYd)
    print(f"  CONTINUOUS-dev per-frame (CIRCULAR, self-aligned): flat {flat_cont:.3f}  curriculum {cur_cont:.3f}")

    # ---- the MODEL-INDEPENDENT destination test: sub-lexical route AUC on continuous ----
    from scripts.jabberwock_subword_recognizer import best_window_match
    from collections import Counter
    func = set(w for w, _ in Counter(w for w, _, _ in tr).most_common(50))
    def is_content(w): return w not in func and len(w) >= 4 and cmu_phones(w)
    vocab = sorted({w for w, _, _ in tr if is_content(w)})
    def decode(enc, cent, cph, M):
        idx = cph[(enc(ctxd(M)) @ cent.T).argmax(1)]; seq, prev = [], -1
        for k in idx:
            if k != prev:
                seq.append(phset[k]); prev = k
        return seq
    rng = np.random.default_rng(0)
    devpairs = gather("dev-clean", 30)
    def auc_of(enc, cent, cph):
        pos, neg = [], []
        for path, trx in devpairs:
            try:
                M = frames(L.load_flac(path)[0])[0]
            except Exception:
                continue
            pseq = decode(enc, cent, cph, M)
            present = set(w.lower() for w in L.normalise(trx))
            inw = [w for w in present if is_content(w)]
            for w in inw:
                pos.append(best_window_match(pseq, [str(x) for x in cmu_phones(w)]))
            for w in rng.choice([v for v in vocab if v not in present], min(len(inw), 50), replace=False):
                neg.append(best_window_match(pseq, [str(x) for x in cmu_phones(w)]))
        pos, neg = np.array(pos), np.array(neg)
        return float(np.mean(pos[:, None] < neg[None, :])) if len(pos) and len(neg) else 0.0
    cur_auc = auc_of(cur_enc, cur_cent, cur_cph)
    flat_auc = auc_of(f_enc, f_cent, f_cph)
    print("=" * 82)
    print(f"  DESTINATION (model-independent, present-vs-absent content AUC on continuous):")
    print(f"     FLAT-START {flat_auc:.3f}   CURRICULUM {cur_auc:.3f}   (0.5 = chance)")
    print(f"  [{time.time()-t0:.0f}s]")
    print("=" * 82)
    print(f"  {'CURRICULUM CROSSES CHANCE on continuous content (AUC>0.55)' if cur_auc > 0.55 else 'continuous content still ~chance — staging helps per-frame but does not yet cross the recognition floor'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
