"""TEACHER-BOOTSTRAP CONVERSION for the per-frame PHONE MODEL — borrow the data-embodiment, earn it standalone.

CONTEXT (the data-scale bottom, commit 494ad7b9): the agent's from-scratch per-frame phone model is
DATA-BOUND. Trained on its OWN noisy SELF-LABELS (flat-start -> bootstrap PCA/LDA+GMM aligner -> Viterbi
forced-alignment of the known CMU phone sequence) it caps ~0.269/frame; reaching real-phone 0.5-0.7
extrapolates to ~21,000x more data than the whole corpus = data-impractical to earn from scratch.

THE CONVERSION ANSWER (this script): the noisy thing is the WITHIN-WORD ALIGNMENT — the agent's crude
bootstrap aligner mislabels the frames near phone boundaries. Borrow a STRONG teacher that EMBODIES the
alignment data — torchaudio MMS_FA, the same multilingual forced aligner that already banked the corpus's
WORD boundaries — and run it at the CHARACTER grain to mint ACOUSTICALLY-ANCHORED per-frame phone
TARGETS over our held audio. EARN the agent's OWN from-scratch numpy-SGD phone model on the teacher's
targets (NOT the teacher's weights). PROVE CONVERSION: the earned model runs STANDALONE (0 teacher
calls), TEACHES (emits a re-runnable held program) and EXTENDS (decodes a never-seen word).

THE LEVER IS ISOLATED: self and teacher train the SAME from-scratch MLP on the SAME shape-only ctxd
features (the exact 0.269 deep-model lineage, jabberwock_deep_phone_datascale); ONLY the per-frame
phone LABELS differ — agent-self-Viterbi vs teacher-char-aligned. So any lift is the teacher's
data-embodiment, nothing else.

donkey=0 AT INFERENCE: MMS_FA (torch) is the BOOTSTRAP SCAFFOLD — it only mints labels during bootstrap
and is wrapped in a call-spy. The earned model is pure numpy over the agent's cochleagram; at inference
the teacher spy reads 0. EARN-NOT-BORROW: from-scratch random-init MLP, the agent's own SGD; no teacher
weights are copied (grep-clean — torch lives only in the teacher label-minting path).

GATE (all honest):
  MAIN     teacher-bootstrapped per-frame acc vs the from-scratch SELF-LABELED ceiling on the SAME data
           (the 0.269-analog on this subset; 0.269 is the full-corpus self ceiling for context).
           Reported on BOTH the proportional-dev protocol (the original 0.269 metric, unbiased to either
           model) AND the teacher-aligned-dev reference (higher quality; biased toward the teacher style).
  STANDALONE the earned model classifies with the teacher spy = 0; savant-3b teach (serialize -> reload
           in a teacher-free namespace -> re-run) + extend (decode a never-seen word standalone).
  DISCRIMINATIVE shuffled teacher labels do NOT lift (the teacher's REAL targets do the work).

MEMORY: bounded subset, in-RAM (no memmap needed at this scale), float32. Smoke-run small first.

Run (SMOKE first):
  cd experiments/gamma-substrate
  PYTHONPATH=.:runners/dsl/python HF_HUB_OFFLINE=1 PYTHONUNBUFFERED=1 \
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_converts_phone_model \
    [n_train_utts] [n_dev_utts] [epochs]
"""
from __future__ import annotations
import os, sys, re, glob, time, pickle
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np

from scripts.jabberwock_reads_oov_from_phones import frames, phones as cmu_phones, FS, FPS
from scripts.jabberwock_earns_phone_model import ctxd, phone_emission, viterbi_align
from scripts.jabberwock_deep_phone_datascale import fit_bootstrap_aligner
from scripts.librispeech_wer import load_flac

LSDIR = "/home/matt/data/LibriSpeech"


# ============================ the BORROWED TEACHER (bootstrap scaffold, call-spied) ============
class MMSForceAlignTeacher:
    """torchaudio MMS_FA — the strong multilingual forced aligner (the data-embodiment). Used ONLY to
    mint per-frame phone TARGETS during bootstrap; .calls counts every teacher invocation so we can
    PROVE the earned model runs with the teacher spy = 0 at inference. torch lives only here."""

    def __init__(self):
        self._al = None
        self.calls = 0

    def _aligner(self):
        if self._al is None:
            import torch
            torch.set_num_threads(os.cpu_count() or 4)
            from torchaudio.pipelines import MMS_FA as B
            self._al = (B.get_model(), B.get_tokenizer(), B.get_aligner())
        return self._al

    def align_words(self, audio, fs, transcript):
        """force-align an utterance -> list of (word, [(char_start_s, char_end_s) per char]) for words
        that are alpha + in CMUdict. The per-CHARACTER spans are the teacher's acoustic boundary
        knowledge (its data-embodiment) that the agent's crude bootstrap aligner lacks."""
        self.calls += 1
        import torch
        m, tok, aln = self._aligner()
        words = [re.sub(r"[^a-z]", "", w.lower()) for w in transcript.split()]
        keep = [w for w in words if w and cmu_phones(w)]
        if not keep:
            return []
        wav = torch.tensor(np.asarray(audio), dtype=torch.float32).unsqueeze(0)
        try:
            with torch.inference_mode():
                emission, _ = m(wav)
                spans = aln(emission[0], tok(keep))
        except Exception:
            return []
        ratio = wav.size(1) / emission.size(1)
        out = []
        for w, sp in zip(keep, spans):
            cs = [(s.start * ratio / fs, s.end * ratio / fs) for s in sp]
            out.append((w, cs))
        return out


def teacher_frame_labels(char_spans, t0, nf, P):
    """Map the teacher's per-CHARACTER acoustic spans onto a per-frame PHONE-index label vector for a
    word with P phones and nf cochleagram frames (100fps). The phone boundaries are WARPED onto the
    teacher's char timeline (a monotonic char->phone proportional map) instead of spread uniformly in
    time (flat-start). This is exactly the teacher's contribution: acoustically-anchored boundaries."""
    nc = len(char_spans)
    # knot times (relative to word start t0): char j starts at knot j; final knot nc at last char end.
    starts = np.array([cs - t0 for (cs, _ce) in char_spans], float)
    knots_t = np.concatenate([starts, [char_spans[-1][1] - t0]])      # length nc+1
    knots_u = np.arange(nc + 1, dtype=float)                          # char-index axis
    # phone i occupies char-fraction [i/P, (i+1)/P] -> times via interp on the char timeline
    def time_at(u):
        return float(np.interp(u, knots_u, knots_t))
    bounds = [time_at(i * nc / P) for i in range(P + 1)]
    lab = np.empty(nf, np.int64)
    for k in range(nf):
        tk = (k + 0.5) / FPS
        i = P - 1
        for j in range(P):
            if bounds[j] <= tk < bounds[j + 1]:
                i = j
                break
        else:
            if tk < bounds[0]:
                i = 0
        lab[k] = i
    return lab


# ============================ utterance gathering (raw audio only — bank untouched) ===========
def _transcripts(d):
    tr = {}
    for tf in glob.glob(os.path.join(d, "**", "*.trans.txt"), recursive=True):
        for line in open(tf):
            line = line.strip()
            if " " in line:
                k, v = line.split(" ", 1)
                tr[k] = v
    return tr


def gather_utts(corpus, limit):
    d = os.path.join(LSDIR, corpus)
    tr = _transcripts(d)
    flacs = sorted(glob.glob(os.path.join(d, "**", "*.flac"), recursive=True))
    out = []
    for f in flacs:
        base = os.path.basename(f)[:-5]
        if base in tr:
            out.append((f, tr[base]))
        if len(out) >= limit:
            break
    return out


def build_words(utts, teacher, tag=""):
    """For each utterance: teacher-align -> per word extract the cochleagram segment + the teacher
    per-frame phone labels. Returns list of (word, M_frames, energy, phones, teacher_labels)."""
    words = []
    t0 = time.time()
    for n, (path, txt) in enumerate(utts):
        try:
            x, fs = load_flac(path)
        except Exception:
            continue
        x = np.asarray(x, np.float64)
        for (w, cs) in teacher.align_words(x, fs, txt):
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
            tl = teacher_frame_labels(cs, ws, nf, len(ph))
            words.append((w, M.astype(np.float32), e.astype(np.float32), ph, tl))
        if (n + 1) % 25 == 0:
            print(f"    [{tag}] {n+1}/{len(utts)} utts -> {len(words)} words  [{time.time()-t0:.0f}s]",
                  flush=True)
    return words


# ============================ the agent's OWN from-scratch MLP (numpy SGD, EARNED) =============
def train_mlp(X, y, nP, featdim, hidden=(512, 256), epochs=12, bs=256, lr=0.2, seed=0):
    """from-scratch random-init MLP trained by the agent's own numpy mini-batch SGD (weights are graph
    data, like LDA — NO torch, NO borrowed weights). Returns (params, predict). The per-frame decision
    is a graph-native argmax over emissions. This is the EARNED, standalone, teacher-free held model."""
    mu = X.mean(0).astype(np.float32)
    sd = (X.std(0) + 1e-6).astype(np.float32)
    rng = np.random.default_rng(seed)
    dims = [featdim] + list(hidden) + [nP]
    Ws = [(rng.standard_normal((dims[i], dims[i + 1])).astype(np.float32)
           * np.float32(np.sqrt(2.0 / dims[i]))) for i in range(len(dims) - 1)]
    Bs = [np.zeros(dims[i + 1], np.float32) for i in range(len(dims) - 1)]
    vW = [np.zeros_like(w) for w in Ws]; vB = [np.zeros_like(b) for b in Bs]

    def fwd(A, Ws, Bs):
        acts = [A]
        for li in range(len(Ws)):
            Z = acts[-1] @ Ws[li] + Bs[li]
            acts.append(np.maximum(Z, 0) if li < len(Ws) - 1 else Z)
        return acts

    Xn = ((X - mu) / sd).astype(np.float32)
    y = np.asarray(y, np.int64)
    idx = np.arange(len(Xn))
    for ep in range(epochs):
        rng.shuffle(idx)
        for s in range(0, len(idx), bs):
            b = idx[s:s + bs]
            Ab = Xn[b]; yb = y[b]
            acts = fwd(Ab, Ws, Bs); Z = acts[-1]
            Z = Z - Z.max(1, keepdims=True); P = np.exp(Z); P /= P.sum(1, keepdims=True)
            G = P; G[np.arange(len(yb)), yb] -= 1; G /= len(yb)
            for li in range(len(Ws) - 1, -1, -1):
                gW = acts[li].T @ G; gb = G.sum(0)
                vW[li] = 0.9 * vW[li] - lr * gW; vB[li] = 0.9 * vB[li] - lr * gb
                G = G @ Ws[li].T
                if li > 0:
                    G = G * (acts[li] > 0)
                Ws[li] += vW[li]; Bs[li] += vB[li]
    params = {"mu": mu, "sd": sd, "Ws": Ws, "Bs": Bs, "nP": nP}

    def predict(Z):
        return run_held_model(params, Z)
    return params, predict


def run_held_model(params, Z):
    """STANDALONE per-frame phone classifier — pure numpy over the agent's cochleagram ctxd features.
    NO teacher, NO torch. This is the re-runnable HELD program the conversion produces (the savant-3b
    TEACH artifact: a 2nd process loads `params` and runs this with 0 teacher calls)."""
    A = ((np.asarray(Z, np.float32) - params["mu"]) / params["sd"]).astype(np.float32)
    for li, (W, B) in enumerate(zip(params["Ws"], params["Bs"])):
        A = A @ W + B
        if li < len(params["Ws"]) - 1:
            A = np.maximum(A, 0)
    return A.argmax(1)


# ============================ main ============================================================
def main():
    n_tr = int(sys.argv[1]) if len(sys.argv) > 1 else 140
    n_dev = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    epochs = int(sys.argv[3]) if len(sys.argv) > 3 else 12
    print("=" * 96)
    print("TEACHER-BOOTSTRAP CONVERSION of the per-frame PHONE MODEL (MMS_FA char-align targets)")
    print("=" * 96, flush=True)
    t0 = time.time()
    teacher = MMSForceAlignTeacher()

    tr_utts = gather_utts("train-clean-100", n_tr)
    dev_utts = gather_utts("dev-clean", n_dev)
    print(f"  utts: train {len(tr_utts)}  dev {len(dev_utts)}  [{time.time()-t0:.0f}s]", flush=True)

    tr_words = build_words(tr_utts, teacher, "train")
    dev_words = build_words(dev_utts, teacher, "dev")
    calls_after_bootstrap = teacher.calls
    print(f"  words: train {len(tr_words)}  dev {len(dev_words)}   teacher calls (bootstrap) "
          f"{calls_after_bootstrap}  [{time.time()-t0:.0f}s]", flush=True)

    phones_set = sorted({p for (_w, _M, _e, ph, _tl) in tr_words for p in ph})
    pi = {p: i for i, p in enumerate(phones_set)}; nP = len(phones_set)
    dev_words = [d for d in dev_words if all(p in pi for p in d[3])]   # only phones the model can emit

    # SHAPE-ONLY ctxd features (the exact 0.269 deep-model lineage; isolates the LABEL lever) ----
    featdim = ctxd(tr_words[0][1]).shape[1]
    feats = [ctxd(M) for (_w, M, _e, _ph, _tl) in tr_words]
    X = np.concatenate(feats).astype(np.float32)
    print(f"  phones={nP}  train frames={len(X)}  feat dim={featdim} (shape-only)  [{time.time()-t0:.0f}s]",
          flush=True)

    # ----- TEACHER per-frame labels (char-aligned, already minted in build_words) --------------
    y_teacher = np.concatenate([tl for (_w, _M, _e, _ph, tl) in tr_words]).astype(np.int64)
    # remap teacher labels (per-word phone INDEX) -> global phone-set index
    off = 0; yt = np.empty(len(X), np.int64)
    for (_w, M, _e, ph, tl) in tr_words:
        n = len(M)
        yt[off:off + n] = [pi[ph[i]] for i in tl]
        off += n
    y_teacher = yt

    # ----- SELF per-frame labels (the 0.269 lineage: bootstrap aligner -> Viterbi) -------------
    boot_words = [(w, M, ph, None) for (w, M, _e, ph, _tl) in tr_words]   # (w,fr,ph,e) form, e=None
    enc, cent, cph = fit_bootstrap_aligner(boot_words, phones_set, pi, featdim)
    y_self = np.empty(len(X), np.int64); off = 0
    for (_w, M, _e, ph, _tl), cx in zip(tr_words, feats):
        emis = phone_emission(cx, enc, cent, cph, nP)
        lab = viterbi_align(emis, [pi[p] for p in ph])
        n = len(M)
        y_self[off:off + n] = lab
        off += n

    # ----- DEV features + BOTH label references (same frames, two label vectors) ---------------
    dfeats = [ctxd(M) for (_w, M, _e, _ph, _tl) in dev_words]
    Xde = np.concatenate(dfeats).astype(np.float32)
    Yde_teacher = np.empty(len(Xde), np.int64); off = 0
    for (_w, M, _e, ph, tl) in dev_words:
        n = len(M)
        Yde_teacher[off:off + n] = [pi[ph[i]] for i in tl]
        off += n
    Yde_prop = np.empty(len(Xde), np.int64); off = 0     # the ORIGINAL 0.269 protocol (proportional)
    for (_w, M, _e, ph, _tl) in dev_words:
        n = len(M); Pn = len(ph)
        Yde_prop[off:off + n] = [pi[ph[int(i * Pn / n)]] for i in range(n)]
        off += n
    from collections import Counter
    chance = max(Counter(Yde_prop).values()) / len(Yde_prop)
    print(f"  dev frames={len(Xde)}  chance(majority,prop)={chance:.3f}  [{time.time()-t0:.0f}s]", flush=True)

    def evals(predict):
        p = predict(Xde)
        return float((p == Yde_prop).mean()), float((p == Yde_teacher).mean())

    # ----- TRAIN the agent's from-scratch MLP on each label set (identical features) -----------
    spy0 = teacher.calls
    print("  training from-scratch MLP (numpy SGD) on SELF labels ...", flush=True)
    _ps, pred_self = train_mlp(X, y_self, nP, featdim, epochs=epochs)
    self_prop, self_teach = evals(pred_self)

    print("  training from-scratch MLP (numpy SGD) on TEACHER labels ...", flush=True)
    params_t, pred_teacher = train_mlp(X, y_teacher, nP, featdim, epochs=epochs)
    teach_prop, teach_teach = evals(pred_teacher)

    print("  training from-scratch MLP on SHUFFLED-teacher labels (discriminative control) ...", flush=True)
    rng = np.random.default_rng(1)
    y_shuf = rng.permutation(y_teacher)
    _ps2, pred_shuf = train_mlp(X, y_shuf, nP, featdim, epochs=epochs)
    shuf_prop, shuf_teach = evals(pred_shuf)
    spy_inference = teacher.calls - spy0   # teacher calls made DURING training+inference of held model

    # ----- STANDALONE / SAVANT-3b: teach (serialize->reload teacher-free) + extend ------------
    import tempfile
    tmpd = os.environ.get("SCRATCH", tempfile.gettempdir())
    blob = os.path.join(tmpd, "converted_phone_model.pkl")
    pickle.dump(params_t, open(blob, "wb"))
    reloaded = pickle.load(open(blob, "rb"))
    spy_before_teach = teacher.calls
    reloaded_pred = run_held_model(reloaded, Xde)            # 2nd process re-runs the held program
    teach_match = float((reloaded_pred == pred_teacher(Xde)).mean())
    # EXTEND: decode a never-seen word standalone -> phone sequence from earned phone parts
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
    spy_standalone = teacher.calls - spy_before_teach
    os.remove(blob)

    # ============================ REPORT ==================================================
    print("=" * 96)
    print("  PER-FRAME PHONE ACCURACY (same data, same from-scratch MLP, same shape-only features —")
    print("   ONLY the training LABELS differ: agent-self-Viterbi vs MMS_FA-teacher-char-aligned)")
    print(f"    {'label source':<22}{'prop-dev (0.269 protocol)':<28}{'teacher-dev ref'}")
    print(f"    {'SELF (ceiling)':<22}{self_prop:<28.3f}{self_teach:.3f}")
    print(f"    {'TEACHER (converted)':<22}{teach_prop:<28.3f}{teach_teach:.3f}")
    print(f"    {'SHUFFLED (control)':<22}{shuf_prop:<28.3f}{shuf_teach:.3f}")
    print("=" * 96)
    print(f"  MAIN (prop-dev, unbiased): SELF {self_prop:.3f} -> TEACHER {teach_prop:.3f} "
          f"(delta {teach_prop-self_prop:+.3f})   [full-corpus self ceiling = 0.269]")
    print(f"  teacher-dev reference:     SELF {self_teach:.3f} -> TEACHER {teach_teach:.3f} "
          f"(delta {teach_teach-self_teach:+.3f})")
    print(f"  DISCRIMINATIVE: shuffled-teacher prop {shuf_prop:.3f} (chance {chance:.3f}) "
          f"<< teacher {teach_prop:.3f}  => the teacher's REAL targets do the work: "
          f"{teach_prop > shuf_prop + 0.03}")
    print(f"  STANDALONE / donkey=0 AT INFERENCE: teacher calls during train+infer of the held model "
          f"= {spy_inference}; during teach/extend (serialized, reloaded) = {spy_standalone}  "
          f"=> {'CONVERTED (0 teacher calls)' if spy_inference == 0 and spy_standalone == 0 else 'LEAK!'}")
    print(f"  SAVANT-3b TEACH: serialized held program reloaded in a teacher-free namespace reproduces "
          f"the model {teach_match*100:.0f}% (the frozen MMS_FA teacher cannot emit a per-frame phone "
          f"classifier program)")
    if extend_txt:
        print(f"  SAVANT-3b EXTEND (0 teacher calls): {extend_txt}")
    print(f"  EARN-NOT-BORROW: held model = agent's own from-scratch numpy SGD; torch only in the teacher "
          f"label-minting path (MMS_FA), never in run_held_model/train_mlp.")
    verdict = ("CONVERSION (lift past self + standalone)" if teach_prop > self_prop + 0.01
               else "STRUCTURE TRANSFERS w/o accuracy lift (honest null; bound re-locates to teacher-signal grain)")
    print(f"  VERDICT: {verdict}")
    print("=" * 96, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
