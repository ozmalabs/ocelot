"""TEACHER-BOOTSTRAP CONVERSION of the per-frame PHONE MODEL with a STRONG PHONE-GRAIN teacher (Allosaurus).

CONTEXT (the accuracy half that kept nulling): the conversion loop CONVERTS structure on speech 3x (standalone,
savant-3b, discriminative, donkey=0) but the ACCURACY lift nulled every time because no available teacher was
strong AT THE PHONE GRAIN. The last attempt (commit d589d764, scripts/jabberwock_converts_phone_model.py) used
torchaudio MMS_FA -- a CHARACTER force-aligner whose char->phone proportional targets were NO BETTER than the
agent's own bootstrap Viterbi self-alignment (self 0.155 -> teacher 0.136, no lift). The data-scale bottom:
from-scratch SELF-labeled per-frame phone model caps ~0.269 on the full corpus (~0.155 on a small matched
subset); reaching real-phone 0.5 extrapolates to ~21,000x more data than the whole corpus.

THE TEST NOW: a REAL phone recognizer (Allosaurus -- a universal IPA phone recognizer, the data-embodiment OF
the phone grain) mints per-frame PHONE targets. Does bootstrapping the held model on ITS targets finally LIFT
accuracy past the self-labeled ceiling AND stay CONVERTED (standalone)?

THE LEVER IS ISOLATED (the d589d764 lineage, unchanged): word SEGMENTATION still comes from MMS_FA (a WORD-grain
task it is good at -- it already banked the corpus word boundaries), and SELF vs TEACHER train the SAME
from-scratch numpy-SGD MLP (train_mlp) on the SAME shape-only ctxd features over the SAME word segments. ONLY the
per-frame phone LABELS differ: agent-self-Viterbi vs Allosaurus-phone-recognized. Any lift is the phone teacher's
data-embodiment, nothing else.

HOW THE PHONE TEACHER GIVES PER-FRAME TARGETS:
  * Allosaurus runs its acoustic model over the whole utterance -> per-frame log-probs over its 230-phone
    universal inventory at ~33.3 fps (window_shift 30ms), masked to the English (eng) subset (68 IPA units).
  * dense per-frame phone = argmax over masked log-probs; CTC blanks (idx 0) are forward-filled with the last
    emitted phone (the standard CTC-peak -> frame-segmentation densification).
  * IPA -> CMU/ARPAbet via IPA2ARPA (reported below; collapses length marks, aspiration, retroflex/post-alveolar
    variants onto the 39-phone ARPAbet set). Diphthongs (AY/AW/OY) are emitted by the teacher as vowel sequences
    (e.g. AY -> AA + IH) -- an HONEST phone-set granularity mismatch vs the CMU reference, noted in the verdict.
  * frame-rate alignment: each of OUR 100-fps cochleagram frames at absolute time t reads the teacher phone whose
    33.3-fps span covers t (explicit grid remap; no resampling of the audio twice).

donkey=0 AT INFERENCE: BOTH teachers (MMS_FA word-seg, Allosaurus phones) are BOOTSTRAP SCAFFOLDS -- used only to
mint labels, wrapped in call-spies, and FREED before training. The earned held model is pure numpy over the
agent's own cochleagram; at inference both spies read 0. EARN-NOT-BORROW: from-scratch random-init MLP, the
agent's own SGD; no teacher weights copied (torch/allosaurus live ONLY in the label-minting classes, never in
run_held_model / train_mlp).

MEMORY: BOTH teachers are loaded for the labeling pass then DELETED (gc + torch cache) BEFORE training; labels
are held as small int arrays. float32. Smoke-run small first.

Run (SMOKE first):
  cd experiments/gamma-substrate
  PYTHONPATH=.:runners/dsl/python HF_HUB_OFFLINE=1 PYTHONUNBUFFERED=1 \
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_converts_phone_model_allosaurus \
    [n_train_utts] [n_dev_utts] [epochs]
"""
from __future__ import annotations
import os, sys, gc, glob, time, pickle
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np

from scripts.jabberwock_reads_oov_from_phones import frames, phones as cmu_phones, FPS
from scripts.jabberwock_earns_phone_model import ctxd, phone_emission, viterbi_align
from scripts.jabberwock_deep_phone_datascale import fit_bootstrap_aligner
from scripts.librispeech_wer import load_flac
# REUSE the d589d764 lineage verbatim: same word-segmenter, same from-scratch MLP, same standalone runner.
from scripts.jabberwock_converts_phone_model import (
    MMSForceAlignTeacher, gather_utts, train_mlp, run_held_model,
)

LSDIR = "/home/matt/data/LibriSpeech"

# IPA (Allosaurus eng inventory, 68 units) -> CMU/ARPAbet (39-phone set). Length marks / aspiration / retroflex
# and post-alveolar variants collapse onto their ARPAbet base; the glottal stop -> T (its usual allophone).
IPA2ARPA = {
    "a": "AA", "aː": "AA", "b": "B", "d": "D", "d̠": "D",
    "e": "EH", "eː": "EY", "e̞": "EH", "f": "F", "h": "HH",
    "i": "IY", "iː": "IY", "j": "Y", "k": "K", "kʰ": "K",
    "l": "L", "m": "M", "n": "N", "o": "OW", "oː": "OW",
    "p": "P", "pʰ": "P", "r": "R", "s": "S", "t": "T", "tʰ": "T", "t̠": "T",
    "u": "UW", "uː": "UW", "v": "V", "w": "W", "x": "HH", "z": "Z",
    "æ": "AE", "ð": "DH", "øː": "ER", "ŋ": "NG",
    "ɐ": "AH", "ɐː": "AH", "ɑ": "AA", "ɑː": "AA", "ɒ": "AA", "ɒː": "AO",
    "ɔ": "AO", "ɔː": "AO", "ɘ": "AH", "ə": "AH", "əː": "ER",
    "ɛ": "EH", "ɛː": "EH", "ɜː": "ER", "ɡ": "G", "ɪ": "IH", "ɪ̯": "IH",
    "ɯ": "UW", "ɵː": "ER", "ɹ": "R", "ɻ": "R", "ʃ": "SH",
    "ʉ": "UW", "ʉː": "UW", "ʊ": "UH", "ʌ": "AH", "ʍ": "W", "ʒ": "ZH",
    "ʔ": "T", "θ": "TH",
}


# ============================ the STRONG PHONE TEACHER (bootstrap scaffold, call-spied) ========
class AllosaurusPhoneTeacher:
    """Allosaurus universal phone recognizer -- the phone-grain data-embodiment. Used ONLY to mint per-frame
    PHONE targets during bootstrap; .calls counts every invocation so we can PROVE the earned model runs with
    the spy = 0 at inference. allosaurus/torch live ONLY in this class."""

    def __init__(self):
        self._m = None
        self._mask = None
        self._shift = None
        self.calls = 0

    def _model(self):
        if self._m is None:
            from allosaurus.app import read_recognizer
            self._m = read_recognizer()
            self._mask = self._m.lm.inventory.get_mask("eng", approximation=self._m.lm.config.approximate)
            self._shift = float(self._m.lm.config.window_shift)
        return self._m, self._mask, self._shift

    def utt_frame_arpa(self, x, fs):
        """whole-utterance dense per-frame ARPAbet phones -> (times[s], arpa[str]). times = teacher-frame
        centers; arpa[k] is the ARPAbet phone active at frame k (CTC blanks forward-filled)."""
        self.calls += 1
        import numpy as _np
        from allosaurus.audio import Audio
        from allosaurus.am.utils import move_to_tensor
        m, mask, shift = self._model()
        au = Audio(samples=(_np.asarray(x, _np.float32) * 32768.0).astype(_np.int16), sample_rate=int(fs))
        feat = m.pm.compute(au)
        feats = _np.expand_dims(feat, 0)
        flen = _np.array([feat.shape[0]], _np.int32)
        tb, tl = move_to_tensor([feats, flen], m.config.device_id)
        logits = m.am(tb, tl).detach().numpy()[0].copy()
        logits = mask.mask_logits(logits)            # restrict to eng phones; blank stays idx 0
        arg = logits.argmax(1)
        arpa = _np.empty(len(arg), object)
        cur = None
        for i, a in enumerate(arg):
            if a != 0:
                ipa = mask.get_units([int(a)])[0]
                cur = IPA2ARPA.get(ipa, cur)         # unmapped -> hold previous (rare)
            arpa[i] = cur
        times = (_np.arange(len(arg)) + 0.5) * shift
        return times, arpa

    def free(self):
        self._m = None
        self._mask = None
        gc.collect()
        try:
            import torch
            torch.cuda.empty_cache()
        except Exception:
            pass


def arpa_at(times, arpa, t):
    """teacher ARPAbet phone active at absolute time t (nearest teacher frame center, clamped)."""
    k = int(np.searchsorted(times, t))
    if k <= 0:
        return arpa[0]
    if k >= len(times):
        return arpa[-1]
    # pick the closer of k-1, k
    return arpa[k] if (t - times[k - 1]) > (times[k] - t) else arpa[k - 1]


# ============================ labeling pass (both teachers, then FREED) =======================
def build_words(utts, mms, allo, tag=""):
    """For each utterance: MMS_FA word-align (word segments + CMU phones, the SAME segmentation as d589d764);
    Allosaurus per-frame phones for the WHOLE utterance; then per word slice the cochleagram + read the teacher
    ARPAbet phone at each of our 100-fps frame centers. Returns (word, M, e, cmu_phones, teacher_arpa_perframe)."""
    words = []
    t0 = time.time()
    for n, (path, txt) in enumerate(utts):
        try:
            x, fs = load_flac(path)
        except Exception:
            continue
        x = np.asarray(x, np.float64)
        wspans = mms.align_words(x, fs, txt)         # [(word, [(cs,ce) per char])]
        if not wspans:
            continue
        ttimes, tarpa = allo.utt_frame_arpa(x, fs)   # whole-utterance teacher phones
        for (w, cs) in wspans:
            ph = cmu_phones(w)
            if not ph:
                continue
            ws, we = cs[0][0], cs[-1][1]
            if we - ws < 0.05:
                continue
            seg = x[int(ws * fs):int(we * fs)]
            if seg.size < int(0.05 * fs):
                continue
            M, e = frames(seg)
            nf = len(M)
            lab = np.empty(nf, object)
            for k in range(nf):
                tk = ws + (k + 0.5) / FPS            # absolute time of our frame k
                lab[k] = arpa_at(ttimes, tarpa, tk)
            words.append((w, M.astype(np.float32), e.astype(np.float32), ph, lab))
        if (n + 1) % 25 == 0:
            print(f"    [{tag}] {n+1}/{len(utts)} utts -> {len(words)} words  [{time.time()-t0:.0f}s]",
                  flush=True)
    return words


# ============================ main ============================================================
def main():
    n_tr = int(sys.argv[1]) if len(sys.argv) > 1 else 140
    n_dev = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    epochs = int(sys.argv[3]) if len(sys.argv) > 3 else 12
    print("=" * 98)
    print("TEACHER-BOOTSTRAP CONVERSION of the per-frame PHONE MODEL -- STRONG phone teacher (Allosaurus)")
    print("=" * 98, flush=True)
    t0 = time.time()

    # ----- LABELING PASS: both teachers loaded, then FREED before training (memory discipline) -----
    mms = MMSForceAlignTeacher()
    allo = AllosaurusPhoneTeacher()
    tr_utts = gather_utts("train-clean-100", n_tr)
    dev_utts = gather_utts("dev-clean", n_dev)
    print(f"  utts: train {len(tr_utts)}  dev {len(dev_utts)}  [{time.time()-t0:.0f}s]", flush=True)

    tr_words = build_words(tr_utts, mms, allo, "train")
    dev_words = build_words(dev_utts, mms, allo, "dev")
    calls_bootstrap = mms.calls + allo.calls
    print(f"  words: train {len(tr_words)}  dev {len(dev_words)}   teacher calls (bootstrap) "
          f"MMS={mms.calls} Allo={allo.calls}  [{time.time()-t0:.0f}s]", flush=True)

    # FREE both teachers BEFORE training (OOM-safe) ------------------------------------------------
    mms_ref, allo_ref = mms, allo            # keep refs only to read .calls (no model held)
    allo.free()
    mms = None
    gc.collect()
    try:
        import torch
        torch.cuda.empty_cache()
    except Exception:
        pass

    # ----- GLOBAL phone set: CMU phones of train words UNION teacher ARPAbet labels (full coverage) -
    phones_set = sorted({p for (_w, _M, _e, ph, _tl) in tr_words for p in ph}
                        | {p for (_w, _M, _e, _ph, tl) in tr_words for p in tl if p is not None})
    pi = {p: i for i, p in enumerate(phones_set)}
    nP = len(phones_set)
    dev_words = [d for d in dev_words if all(p in pi for p in d[3])]   # only words the model can emit

    # ----- SHAPE-ONLY ctxd features (the exact 0.269 lineage; isolates the LABEL lever) -----------
    featdim = ctxd(tr_words[0][1]).shape[1]
    feats = [ctxd(M) for (_w, M, _e, _ph, _tl) in tr_words]
    X = np.concatenate(feats).astype(np.float32)
    print(f"  phones={nP}  train frames={len(X)}  feat dim={featdim} (shape-only)  [{time.time()-t0:.0f}s]",
          flush=True)

    # ----- TEACHER per-frame labels (Allosaurus ARPAbet -> global index; -1 if unmapped) ----------
    yt = np.empty(len(X), np.int64); off = 0
    for (_w, M, _e, _ph, tl) in tr_words:
        n = len(M)
        yt[off:off + n] = [pi.get(p, -1) for p in tl]
        off += n
    keep = yt >= 0                                    # drop the rare unmapped frame from training
    y_teacher = yt

    # ----- SELF per-frame labels (the 0.269 lineage: bootstrap aligner -> Viterbi over CMU seq) ----
    boot_words = [(w, M, ph, None) for (w, M, _e, ph, _tl) in tr_words]
    enc, cent, cph = fit_bootstrap_aligner(boot_words, phones_set, pi, featdim)
    y_self = np.empty(len(X), np.int64); off = 0
    for (_w, M, _e, ph, _tl), cx in zip(tr_words, feats):
        emis = phone_emission(cx, enc, cent, cph, nP)
        lab = viterbi_align(emis, [pi[p] for p in ph])
        n = len(M)
        y_self[off:off + n] = lab
        off += n

    # ----- DEV features + label references (proportional CMU = the 0.269 protocol; teacher = Allo) -
    dfeats = [ctxd(M) for (_w, M, _e, _ph, _tl) in dev_words]
    Xde = np.concatenate(dfeats).astype(np.float32)
    Yde_teacher = np.empty(len(Xde), np.int64); off = 0
    for (_w, M, _e, _ph, tl) in dev_words:
        n = len(M)
        Yde_teacher[off:off + n] = [pi.get(p, -1) for p in tl]
        off += n
    Yde_prop = np.empty(len(Xde), np.int64); off = 0
    for (_w, M, _e, ph, _tl) in dev_words:
        n = len(M); Pn = len(ph)
        Yde_prop[off:off + n] = [pi[ph[int(i * Pn / n)]] for i in range(n)]
        off += n
    from collections import Counter
    chance = max(Counter(Yde_prop).values()) / len(Yde_prop)
    teacher_own = float((Yde_teacher == Yde_prop).mean())   # the borrowed ceiling at the prop metric
    print(f"  dev frames={len(Xde)}  chance(majority,prop)={chance:.3f}  "
          f"teacher-own-acc(prop)={teacher_own:.3f}  [{time.time()-t0:.0f}s]", flush=True)

    def evals(predict):
        p = predict(Xde)
        return float((p == Yde_prop).mean()), float((p == Yde_teacher).mean())

    # ----- TRAIN the agent's from-scratch MLP on each label set (identical features) --------------
    spy0 = mms_ref.calls + allo_ref.calls
    print("  training from-scratch MLP (numpy SGD) on SELF labels ...", flush=True)
    _ps, pred_self = train_mlp(X, y_self, nP, featdim, epochs=epochs)
    self_prop, self_teach = evals(pred_self)

    print("  training from-scratch MLP (numpy SGD) on TEACHER (Allosaurus) labels ...", flush=True)
    params_t, pred_teacher = train_mlp(X[keep], y_teacher[keep], nP, featdim, epochs=epochs)
    teach_prop, teach_teach = evals(pred_teacher)
    # DECISIVE diagnostic: can the shape-only feature even FIT the strong teacher labels on TRAIN?
    # low train-fit => the feature/capacity is the wall (underfit), NOT the teacher or data/generalization.
    teach_fit = float((pred_teacher(X[keep]) == y_teacher[keep]).mean())

    print("  training from-scratch MLP on SHUFFLED-teacher labels (discriminative control) ...", flush=True)
    rng = np.random.default_rng(1)
    y_shuf = rng.permutation(y_teacher[keep])
    _ps2, pred_shuf = train_mlp(X[keep], y_shuf, nP, featdim, epochs=epochs)
    shuf_prop, shuf_teach = evals(pred_shuf)
    spy_inference = (mms_ref.calls + allo_ref.calls) - spy0

    # ----- STANDALONE / SAVANT-3b: teach (serialize->reload teacher-free) + extend ---------------
    import tempfile
    tmpd = os.environ.get("SCRATCH", tempfile.gettempdir())
    blob = os.path.join(tmpd, "converted_phone_model_allo.pkl")
    pickle.dump(params_t, open(blob, "wb"))
    reloaded = pickle.load(open(blob, "rb"))
    spy_before = mms_ref.calls + allo_ref.calls
    reloaded_pred = run_held_model(reloaded, Xde)
    teach_match = float((reloaded_pred == pred_teacher(Xde)).mean())
    seen = {w for (w, _M, _e, _ph, _tl) in tr_words}
    novel = next(((w, M, ph) for (w, M, _e, ph, _tl) in dev_words if w not in seen and len(ph) >= 4), None)
    extend_txt = ""
    if novel is not None:
        w, M, ph = novel
        idx = run_held_model(reloaded, ctxd(M))
        seq, prev = [], -1
        for k in idx:
            if k != prev:
                seq.append(phones_set[k]); prev = k
        extend_txt = f"'{w}' (unseen) -> earned phone seq {seq[:12]} | CMU {ph[:12]}"
    spy_standalone = (mms_ref.calls + allo_ref.calls) - spy_before
    os.remove(blob)

    # ============================ REPORT ======================================================
    print("=" * 98)
    print("  PER-FRAME PHONE ACCURACY (same data, same from-scratch MLP, same shape-only features --")
    print("   ONLY the training LABELS differ: agent-self-Viterbi vs Allosaurus-phone-recognized)")
    print(f"    {'label source':<24}{'prop-dev (0.269 protocol)':<28}{'teacher-dev ref'}")
    print(f"    {'SELF (ceiling)':<24}{self_prop:<28.3f}{self_teach:.3f}")
    print(f"    {'TEACHER (converted)':<24}{teach_prop:<28.3f}{teach_teach:.3f}")
    print(f"    {'SHUFFLED (control)':<24}{shuf_prop:<28.3f}{shuf_teach:.3f}")
    print("=" * 98)
    print(f"  MAIN (prop-dev, unbiased): SELF {self_prop:.3f} -> TEACHER {teach_prop:.3f} "
          f"(delta {teach_prop-self_prop:+.3f})   [full-corpus self ceiling = 0.269]")
    print(f"  TEACHER own per-frame acc (the borrowed ceiling, prop metric) = {teacher_own:.3f}; "
          f"earned standalone recovers {(teach_prop/teacher_own*100) if teacher_own>0 else 0:.0f}% of it")
    print(f"  DECISIVE DIAGNOSTIC: teacher-model TRAIN-FIT to the strong teacher labels = {teach_fit:.3f} "
          f"(teacher own-acc {teacher_own:.3f}) => shape-only feature {'UNDERFITS even strong labels = FEATURE/CAPACITY is the wall' if teach_fit < 0.45 else 'fits; bottleneck is generalization/data'}")
    print(f"  teacher-dev reference:     SELF {self_teach:.3f} -> TEACHER {teach_teach:.3f} "
          f"(delta {teach_teach-self_teach:+.3f})")
    print(f"  DISCRIMINATIVE: shuffled-teacher prop {shuf_prop:.3f} (chance {chance:.3f}) "
          f"<< teacher {teach_prop:.3f}  => real targets do the work: {teach_prop > shuf_prop + 0.03}")
    print(f"  STANDALONE / donkey=0 AT INFERENCE: teacher calls during train+infer = {spy_inference}; "
          f"during teach/extend = {spy_standalone}  "
          f"=> {'CONVERTED (0 teacher calls)' if spy_inference == 0 and spy_standalone == 0 else 'LEAK!'}")
    print(f"  SAVANT-3b TEACH: serialized held program reloaded teacher-free reproduces the model "
          f"{teach_match*100:.0f}% (the frozen teachers cannot emit a per-frame phone classifier program)")
    if extend_txt:
        print(f"  SAVANT-3b EXTEND (0 teacher calls): {extend_txt}")
    print(f"  EARN-NOT-BORROW: held model = agent's own from-scratch numpy SGD; allosaurus/torch ONLY in the "
          f"teacher label-minting classes, never in run_held_model/train_mlp.")
    converted = (teach_prop > self_prop + 0.01) and spy_inference == 0 and spy_standalone == 0
    if converted:
        verdict = ("CONVERSION COMPLETE on speech: strong phone teacher LIFTS acc past the self ceiling "
                   "AND the earned model is STANDALONE")
    elif spy_inference == 0 and spy_standalone == 0:
        verdict = ("STRUCTURE CONVERTS (standalone) but accuracy NULL -- bound re-locates (see deltas; "
                   "likely phone-set granularity / frame-rate / held-model capacity, NOT the teacher)")
    else:
        verdict = "LEAK -- not standalone"
    print(f"  VERDICT: {verdict}")
    print("=" * 98, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
