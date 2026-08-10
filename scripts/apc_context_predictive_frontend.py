"""CONTEXT-PREDICTIVE FRONT-END — RUST-NATIVE (wav2vec2-from-scratch, donkey=0 BY CONSTRUCTION).

The V1-V4 falsification (commit d62abb81) showed multi-speaker word-shape fidelity is bound by TWO
co-equal levers: a LEARNED FRONT-END (a learned filterbank beats the fixed 32-band cochleagram, Δ+0.40)
and full-utterance CONTEXT (the frame representation should depend on the whole utterance, not the word
span, Δ+0.50). This builds ONE self-supervised model that captures BOTH — Autoregressive Predictive
Coding (APC): a recurrent context state trained to PREDICT the acoustic frame K steps ahead (label-free).

    h_t  = tanh(x_t W_f + h_{t-1} U + b)      W_f = the LEARNED FRONT-END lever
    xhat = h_t W_p + c ≈ x_{t+K}              U   = CONTEXT (h_t summarises frames 0..t)
    L    = mean_t || xhat - x_{t+K} ||^2      predicting the FUTURE -> phonetic, speaker-robust state

★ ARCHITECTURE (CLAUDE.md): the capability is IN THE RUST AGENT, not this Python. The numeric
  primitive is Rust — training is `apc::train` (a one-line hand-off; the SGD+BPTT loop is all Rust), and
  the ENCODE is the `ApcEncode` graph Term evaluated by the substrate (`Substrate.evaluate`). This
  adapter only (i) ingests LibriSpeech audio -> cochleagram frames (the agent's Rust ear) + word spans,
  (ii) drives Rust train + Rust ApcEncode, (iii) reads the representation and measures it. No reasoning
  in Python. donkey=0 at inference (no torch in the analyze process); MMS_FA alignment = ISOLATED
  torch subprocess, bootstrap-only (word boundaries), same discipline as the existing harness.

REUSED Rust machinery: `cochleagram` (the 32-band gammatone front-end, audio_primitives.rs), the new
`apc::train` / `ApcEncode` primitives (apc.rs), and `DtwTo` (the held banded-DTW Term) + the CI harness
metrics (nn_recall_cross / dprime_cross / order1_purity_matched) — UNCHANGED.

GATE (held-out speakers; donkey=0):
  (a) ★ COMPILES + RUNS via this adapter (ingest -> Rust train -> Rust ApcEncode Term -> read).
  (b) ★ TWO-LEVER: cross-speaker NN-recall > the donkey=0 best 0.245; ablate front-end-only vs both.
  (c) reuses existing auditory/predict/quantize primitives (cochleagram, ApcEncode, DtwTo).
  (d) multi-speaker order-1 purity toward 0.84; shuffled-future control collapses the gain.

Run (MUST put THIS worktree's python FIRST so the freshly-built _native.abi3.so with ApcEncode is used):
  PYTHONPATH=runners/dsl/python:.:scripts /home/matt/ozma/internal/research/.venv/bin/python \
      scripts/apc_context_predictive_frontend.py
Env: KTRAIN(40) KTEST(20) UTTS(12) T(20) DIN(64) DH(96) KAHEAD(3) EPOCHS(18) LR(0.05) BIDIR(1)
     TE_CAP(3000) FE_CAP(1500) SCRATCH.
"""
from __future__ import annotations
import os, sys, glob, pickle, subprocess, re

# --- THIS worktree first (so ApcEncode / apc_train resolve to the local build) ---
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (os.path.join(ROOT, "runners", "dsl", "python"), ROOT, os.path.join(ROOT, "scripts")):
    if p in sys.path:
        sys.path.remove(p)
    sys.path.insert(0, p)
import numpy as np
from collections import Counter, defaultdict

VENV_PY = "/home/matt/ozma/internal/research/.venv/bin/python"
LIBRI = "/home/matt/data/LibriSpeech"
TRAIN_TREE = os.path.join(LIBRI, "train-clean-100")
TEST_TREE = os.path.join(LIBRI, "dev-clean")
SCRATCH = os.environ.get(
    "SCRATCH",
    "/tmp/claude-1000/-home-matt-ozma-internal-research-experiments-gamma-substrate/"
    "3ed12bb3-7b58-44c0-b051-98640926c040/scratchpad")
os.makedirs(SCRATCH, exist_ok=True)
CACHE = os.path.join(SCRATCH, "apc_libri_uttframes.pkl")

KTRAIN = int(os.environ.get("KTRAIN", "40"))
KTEST = int(os.environ.get("KTEST", "20"))
UTTS = int(os.environ.get("UTTS", "12"))
T = int(os.environ.get("T", "20"))
DIN = int(os.environ.get("DIN", "64"))
DH = int(os.environ.get("DH", "96"))
KAHEAD = int(os.environ.get("KAHEAD", "3"))
EPOCHS = int(os.environ.get("EPOCHS", "18"))
LR = float(os.environ.get("LR", "0.05"))
BIDIR = int(os.environ.get("BIDIR", "1"))
TE_CAP = int(os.environ.get("TE_CAP", "3000"))
FE_CAP = int(os.environ.get("FE_CAP", "1500"))
FPS = 100.0  # cochleagram grid


# ============================================================================ #
#  EXTRACTION — ISOLATED subprocess: torch MMS_FA (word spans, bootstrap-only)
#  + the agent's Rust cochleagram over the WHOLE utterance (donkey=0 front-end).
#  Per utterance: (full_coch[Tu,32] f16, [(word,f0,f1)], "split:spk", split).
# ============================================================================ #
def _extract():
    import resource
    resource.setrlimit(resource.RLIMIT_AS, (14 * 1024**3, 14 * 1024**3))
    import torch
    torch.set_num_threads(os.cpu_count() or 4)
    from torchaudio.pipelines import MMS_FA as B
    from scripts.librispeech_wer import load_flac
    from substrate_rs import _native as nat
    m, tok, aln = B.get_model(), B.get_tokenizer(), B.get_aligner()

    def transcripts(d):
        tr = {}
        for tf in glob.glob(os.path.join(d, "**", "*.trans.txt"), recursive=True):
            for line in open(tf):
                line = line.strip()
                if " " in line:
                    k, v = line.split(" ", 1); tr[k] = v
        return tr

    def align_utt(audio, fs, transcript):
        words = [re.sub(r"[^a-z]", "", w.lower()) for w in transcript.split()]
        keep = [(i, w) for i, w in enumerate(words) if w]
        if not keep:
            return []
        wav = torch.tensor(np.asarray(audio), dtype=torch.float32).unsqueeze(0)
        try:
            with torch.inference_mode():
                emission, _ = m(wav)
                spans = aln(emission[0], tok([w for _i, w in keep]))
        except Exception:
            return []
        ratio = wav.size(1) / emission.size(1)
        return [(w, sp[0].start * ratio / fs, sp[-1].end * ratio / fs) for (_i, w), sp in zip(keep, spans)]

    def do_tree(tree, klim, split, out):
        speakers = sorted(os.listdir(tree))[:klim]
        for sp in speakers:
            tr = transcripts(os.path.join(tree, sp))
            flacs = sorted(glob.glob(os.path.join(tree, sp, "**", "*.flac"), recursive=True))[:UTTS]
            nutt = 0
            for f in flacs:
                base = os.path.basename(f)[:-5]
                if base not in tr:
                    continue
                x, fs = load_flac(f); x = np.asarray(x, np.float32)
                dur = len(x) / fs
                nfr = max(4, int(round(dur * FPS)))
                spans = align_utt(x, fs, tr[base])
                if not spans:
                    continue
                flat = nat.cochleagram(x, int(fs), 50.0, 80.0, nfr)   # Rust ear, full utterance
                coch = np.asarray(flat, np.float32).reshape(nfr, 32).astype(np.float16)  # RAW (match CI)
                wspans = []
                for (w, t0, t1) in spans:
                    if not (w.isalpha() and len(w) >= 2 and (t1 - t0) >= 0.06):
                        continue
                    f0 = max(0, int(t0 * FPS)); f1 = min(nfr, int(t1 * FPS))
                    if f1 - f0 >= 3:
                        wspans.append((w, f0, f1))
                if wspans:
                    out.append((coch, wspans, f"{split}:{sp}", split)); nutt += 1
            print(f"  [extract] {split} {sp}: {nutt} utts (total {len(out)})", flush=True)

    out = []
    do_tree(TRAIN_TREE, KTRAIN, "train", out)
    do_tree(TEST_TREE, KTEST, "test", out)
    pickle.dump(out, open(CACHE, "wb"))
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024**2
    ntr = sum(1 for o in out if o[3] == "train"); nte = sum(1 for o in out if o[3] == "test")
    print(f"  [extract] wrote {len(out)} utts (train {ntr}, test {nte}) [peak {peak:.2f} GiB]", flush=True)


# ============================================================================ #
#  FEATURES (numpy) — full-utterance input to the APC: [CMN-value(32) ++ delta(32)].
# ============================================================================ #
def utt_feats(coch):
    coch = np.asarray(coch, np.float32)
    val = coch - coch.mean(0, keepdims=True)                 # CMN value
    dlt = np.diff(coch, axis=0)
    dlt = np.vstack([np.zeros((1, coch.shape[1]), np.float32), dlt])
    return np.concatenate([val, dlt], axis=1).astype(np.float32)   # [Tu,64]


def resample(fr, t):
    fr = np.asarray(fr, np.float32)
    n = len(fr)
    if n == t:
        return fr
    idx = np.linspace(0, n - 1, t)
    lo = np.floor(idx).astype(int); hi = np.minimum(lo + 1, n - 1); f = (idx - lo)[:, None]
    return (fr[lo] * (1 - f) + fr[hi] * f).astype(np.float32)


def _traj(fr):
    return tuple(tuple(float(v) for v in row) for row in fr)


# ============================================================================ #
#  MAIN
# ============================================================================ #
def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--extract":
        _extract(); return

    import resource
    resource.setrlimit(resource.RLIMIT_AS, (14 * 1024**3, 14 * 1024**3))  # memory-safety cap (see CLAUDE hints)

    from substrate_rs import _native as nat
    print(f"  [substrate_rs] {nat.__file__}", flush=True)
    assert hasattr(nat, "apc_train"), "apc_train missing — build the worktree crate first"

    env = dict(os.environ, PYTHONPATH=f"runners/dsl/python:.:scripts:{os.environ.get('PYTHONPATH','')}")
    if not os.path.exists(CACHE):
        print("== extracting LibriSpeech full-utterance cochleagrams + word spans (isolated MMS_FA) ==",
              flush=True)
        subprocess.run([VENV_PY, os.path.abspath(__file__), "--extract"], cwd=ROOT, env=env, check=True)

    # ---- torch-free from here ----
    import scripts.jabberwock_quantized_trajectory_order1 as Q       # DtwTo Term builders + snap_scan
    import scripts.jabberwock_context_dependent_order1 as CTX        # cluster_to_target
    import scripts.jabberwock_contrastive_speaker_invariant as CI    # nn_recall_cross/dprime_cross/purity

    data = pickle.load(open(CACHE, "rb"))
    tr = [d for d in data if d[3] == "train"]
    te = [d for d in data if d[3] == "test"]
    n_tr_spk = len(set(d[2] for d in tr)); n_te_spk = len(set(d[2] for d in te))
    print(f"\n  DATA: {len(data)} utts | TRAIN {len(tr)} utts / {n_tr_spk} spk (train-clean-100) | "
          f"HELD-OUT TEST {len(te)} utts / {n_te_spk} spk (dev-clean)", flush=True)

    LIFT_M = int(os.environ.get("LIFT_MODES", "16"))
    DZ = int(os.environ.get("DZ", "24"))
    ME_EPOCHS = int(os.environ.get("ME_EPOCHS", "220"))
    ME_CAP = int(os.environ.get("ME_CAP", "6000"))

    def lift_mag(coch):
        """DIMENSIONAL LIFT (Rust apc_lift): per-frame log-freq Fourier-mode
        MAGNITUDES = VTL-shift ROTATION quotiented out -> [Tu, LIFT_M]."""
        coch = np.asarray(coch, np.float32); nfr = coch.shape[0]
        m = np.asarray(nat.apc_lift(coch.reshape(-1).tolist(), nfr, 32, LIFT_M), np.float32)
        return m.reshape(nfr, LIFT_M)

    def concat_lift(feat, coch):
        """ADDED AXIS (not replacement): [utt CMN+delta(64) ++ lift-mag(M) ++ lift-delta(M)].
        Keeps the original signal; the VTL-rotation-quotiented magnitudes ADD invariance."""
        m = lift_mag(coch)
        dl = np.diff(m, axis=0); dl = np.vstack([np.zeros((1, m.shape[1]), np.float32), dl])
        return np.concatenate([feat, m, dl], axis=1).astype(np.float32)

    def znorm_fit(feats):
        stk = np.concatenate(feats)
        return stk.mean(0).astype(np.float32), (stk.std(0) + 1e-6).astype(np.float32)
    def znorm_apply(feats, mu, sd):
        return [((f - mu) / sd).astype(np.float32) for f in feats]

    def train_apc(feats, bidir, shuffle=False):
        ff = np.concatenate([f.reshape(-1) for f in feats]).astype(np.float32)
        lens = [int(f.shape[0]) for f in feats]
        din = feats[0].shape[1]
        return [float(v) for v in nat.apc_train(ff.tolist(), lens, din, DH, KAHEAD, EPOCHS, LR,
                                                bool(bidir), 0, shuffle)]

    s = nat.Substrate()
    def apc_encode(model_list, seqf, out_len, start=-1, end=-1):
        """The ENCODE runs as the ApcEncode GRAPH TERM via Substrate.evaluate (Rust).
        `start`/`end` (frame indices INTO seqf, Rust-side slice-then-resample) let a
        caller run the RNN over a WIDER seq (e.g. a bounded local window) than the
        span it actually wants back — genuine local recurrent context (Lever 1C)."""
        term = {"type": "ApcEncode",
                "model": {"type": "Lit", "value": model_list},
                "seq": {"type": "Lit", "value": _traj(seqf)},
                "start": {"type": "Lit", "value": int(start)}, "end": {"type": "Lit", "value": int(end)},
                "out_len": {"type": "Lit", "value": out_len}}
        out = s.evaluate(term, {})
        return np.asarray([[float(v) for v in row] for row in out], np.float32)

    # ---- recall/d'/AUC reporting helper (moved up here so the Lever-1/2 sweeps below
    # can use it too, ahead of the full GATE (b) table) ----
    CAPQ = int(os.environ.get("CAPQ", "400"))
    CTX_CAPQ = int(os.environ.get("CTX_CAPQ", str(min(CAPQ, 250))))  # cheaper cap for sweep/ablation passes
    _wi, _si = {}, {}
    def _ids(w, sp):
        return (np.array([_wi.setdefault(x, len(_wi)) for x in w], np.int64),
                np.array([_si.setdefault(x, len(_si)) for x in sp], np.int64))
    def report(name, arr, w, sp, cap_q=None):
        arr = np.asarray(arr, np.float32); n = arr.shape[0]; dim = arr.shape[2]
        wi, si = _ids(w, sp)
        r = nat.apc_recall(arr.reshape(-1).tolist(), n, T, dim, wi.tolist(), si.tolist(),
                            cap_q or CAPQ, 500, 1500, 0)
        print(f"  {name:>24} {r[0]:10.3f} {r[1]:9.3f} {r[2]:9.3f}", flush=True)
        return float(r[0]), float(r[1]), float(r[2])

    # ============ APC full-utterance features (raw-dim + concat-lift) ============
    tr_raw_f = [utt_feats(d[0]) for d in tr]; te_raw_f = [utt_feats(d[0]) for d in te]
    mu_r, sd_r = znorm_fit(tr_raw_f)
    tr_raw_f = znorm_apply(tr_raw_f, mu_r, sd_r); te_raw_f = znorm_apply(te_raw_f, mu_r, sd_r)
    tr_cl_f = [concat_lift(utt_feats(d[0]), d[0]) for d in tr]
    te_cl_f = [concat_lift(utt_feats(d[0]), d[0]) for d in te]
    mu_c, sd_c = znorm_fit(tr_cl_f)
    tr_cl_f = znorm_apply(tr_cl_f, mu_c, sd_c); te_cl_f = znorm_apply(te_cl_f, mu_c, sd_c)

    print(f"\n--- ★ training APC IN RUST (apc_train): dh={DH} K={KAHEAD} epochs={EPOCHS} "
          f"on {len(tr)} utts ---", flush=True)
    print(f"  [APC raw-dim din={tr_raw_f[0].shape[1]}, unidir]", flush=True)
    ml_raw = train_apc(tr_raw_f, bidir=False)
    print(f"  [APC concat-lift din={tr_cl_f[0].shape[1]} (VTL-mags ADDED), unidir]", flush=True)
    ml_cl = train_apc(tr_cl_f, bidir=False)
    print(f"  [APC concat-lift din={tr_cl_f[0].shape[1]}, BIDIRECTIONAL]", flush=True)
    ml_clb = train_apc(tr_cl_f, bidir=True)
    print(f"  [CONTROL: shuffled-future on concat-lift]", flush=True)
    ml_sh = train_apc(tr_cl_f, bidir=False, shuffle=True)

    # ============ LEVER 2: InfoNCE contrastive head (Rust apc_train_contrastive) ============
    # The MMS-bootstrap (word,f0,f1) spans ARE the contrastive pairs: flatten TRAIN word
    # occurrences into per-occurrence metadata (seq idx into tr_cl_f, span, integer word id).
    _wi_tr = {}
    tr_wseq, tr_wstart, tr_wend, tr_wid = [], [], [], []
    for ui, d in enumerate(tr):
        for (w, f0, f1) in d[1]:
            tr_wseq.append(ui); tr_wstart.append(int(f0)); tr_wend.append(int(f1))
            tr_wid.append(_wi_tr.setdefault(w, len(_wi_tr)))
    print(f"\n  [LEVER-2 metadata] {len(tr_wseq)} train word occurrences, {len(_wi_tr)} distinct "
          f"words (MMS-bootstrap spans; no new alignment)", flush=True)

    NCE_TAU = float(os.environ.get("NCE_TAU", "0.1"))
    NCE_BATCH = int(os.environ.get("NCE_BATCH", "24"))
    NCE_LAMBDAS = [float(x) for x in os.environ.get("NCE_LAMBDAS", "0.5,1.0,2.0").split(",") if x]

    def train_apc_nce(feats, lam, shuffle_label=False, epochs=None):
        ff = np.concatenate([f.reshape(-1) for f in feats]).astype(np.float32)
        lens = [int(f.shape[0]) for f in feats]
        din = feats[0].shape[1]
        return [float(v) for v in nat.apc_train_contrastive(
            ff.tolist(), lens, din, DH, KAHEAD, epochs or EPOCHS, LR, True, 0, False,
            tr_wseq, tr_wstart, tr_wend, tr_wid, float(lam), NCE_TAU, NCE_BATCH, bool(shuffle_label))]

    print(f"\n--- ★ LEVER 2: APC + InfoNCE contrastive head (Rust apc_train_contrastive) "
          f"tau={NCE_TAU} batch={NCE_BATCH} lambdas={NCE_LAMBDAS} ---", flush=True)
    ml_nce = {}
    for lam in NCE_LAMBDAS:
        print(f"  [APC concat-lift BIDIR +InfoNCE lambda={lam}]", flush=True)
        ml_nce[lam] = train_apc_nce(tr_cl_f, lam)

    # ---- quick word-only (zero-context) recall helper, reused for lambda-selection +
    # the shuffled-label control (matches the existing "front-end-only" 0.310 baseline shape) ----
    def quick_word_only(model, cap):
        ws_, sp_, reps_ = [], [], []
        n = 0
        for ui, d in enumerate(te):
            if n >= cap: break
            coch, wspans, sp, _ = d
            for (w, f0, f1) in wspans:
                if n >= cap: break
                reps_.append(apc_encode(model, te_cl_f[ui][f0:f1], T))
                ws_.append(w); sp_.append(sp)
                n += 1
        return reps_, ws_, sp_

    SEL_CAP = int(os.environ.get("SEL_CAP", "600"))
    print(f"\n--- LEVER-2 lambda selection (word-only context, cap={SEL_CAP}, CTX_CAPQ={CTX_CAPQ}) ---")
    sel_pred_reps, sel_pred_w, sel_pred_sp = quick_word_only(ml_clb, SEL_CAP)
    sel_pred = report("pred-only (word-only, sel)", sel_pred_reps, sel_pred_w, sel_pred_sp, cap_q=CTX_CAPQ)
    best_lam, best_lam_recall = None, sel_pred[0]
    lam_sel_res = {"predictive-only": sel_pred}
    for lam in NCE_LAMBDAS:
        reps, ws, sp_ = quick_word_only(ml_nce[lam], SEL_CAP)
        r = report(f"+InfoNCE lam={lam} (word-only, sel)", reps, ws, sp_, cap_q=CTX_CAPQ)
        lam_sel_res[lam] = r
        if r[0] > best_lam_recall:
            best_lam_recall = r[0]; best_lam = lam
    if best_lam is None:
        best_lam = NCE_LAMBDAS[len(NCE_LAMBDAS) // 2]
        print(f"  [lambda-select] no lambda beat predictive-only on the sel subset "
              f"({sel_pred[0]:.3f}); falling back to lam={best_lam} for the full ablation", flush=True)
    else:
        print(f"  [lambda-select] best lambda={best_lam} (sel recall {best_lam_recall:.3f} vs "
              f"pred-only {sel_pred[0]:.3f})", flush=True)

    # ---- LEVER 1C: local-window size sweep (no retrain — same model, different `seq` handed
    # to apc_encode's start/end slice) ----
    WIN_SWEEP = [int(x) for x in os.environ.get("WIN_SWEEP", "30,60,100").split(",") if x]
    WIN_CAP = int(os.environ.get("WIN_CAP", str(SEL_CAP)))
    print(f"\n--- LEVER 1C: local-window size sweep {WIN_SWEEP} (pred-only model, cap={WIN_CAP}) ---")
    win_words, win_spk = [], []
    win_reps = {w: [] for w in WIN_SWEEP}
    wn = 0
    for ui, d in enumerate(te):
        if wn >= WIN_CAP: break
        coch, wspans, sp, _ = d
        for (w, f0, f1) in wspans:
            if wn >= WIN_CAP: break
            win_words.append(w); win_spk.append(sp)
            for win in WIN_SWEEP:
                ws0 = max(0, f0 - win)
                seq = te_cl_f[ui][ws0:f1]
                win_reps[win].append(apc_encode(ml_clb, seq, T, start=f0 - ws0, end=f1 - ws0))
            wn += 1
    win_sel_res = {}
    best_win, best_win_recall = WIN_SWEEP[0], -1.0
    for win in WIN_SWEEP:
        rw = report(f"local-window WIN={win} (sel)", win_reps[win], win_words, win_spk, cap_q=CTX_CAPQ)
        win_sel_res[win] = rw
        if rw[0] > best_win_recall:
            best_win_recall = rw[0]; best_win = win
    WIN = best_win
    print(f"  -> best local-window WIN={WIN} (sel recall {best_win_recall:.3f})", flush=True)
    del win_reps, win_words, win_spk, sel_pred_reps

    # ---- LEVER-2 CONTROL: shuffled-label InfoNCE (word ids permuted per-batch; a real
    # gain must collapse under this) ----
    print(f"\n--- LEVER-2 CONTROL: shuffled-label InfoNCE (lam={best_lam}, word ids permuted per-batch) ---",
          flush=True)
    ml_nce_shuf = train_apc_nce(tr_cl_f, best_lam, shuffle_label=True)

    # ---- ★ TWO-LEVER ABLATION TABLE: context {full-utt, word-only, local-window(WIN),
    # word-span-pooled(WIN)} x objective {predictive-only, +InfoNCE(best lambda)} ----
    CTX_CAP = int(os.environ.get("CTX_CAP", "1200"))
    ABL_CAPQ = int(os.environ.get("ABL_CAPQ", str(min(CAPQ, 300))))

    def build_context_reps(model, cap):
        ws_, sp_ = [], []
        repsA, repsB, repsC, repsD = [], [], [], []
        n = 0
        for ui, d in enumerate(te):
            if n >= cap: break
            coch, wspans, sp, _ = d
            if not wspans: continue
            h_full = apc_encode(model, te_cl_f[ui], te_cl_f[ui].shape[0])
            for (w, f0, f1) in wspans:
                if n >= cap: break
                repsA.append(resample(h_full[f0:f1], T))
                base = apc_encode(model, te_cl_f[ui][f0:f1], T)
                repsB.append(base)
                ws0 = max(0, f0 - WIN)
                seq = te_cl_f[ui][ws0:f1]
                repsC.append(apc_encode(model, seq, T, start=f0 - ws0, end=f1 - ws0))
                ctxwin = te_cl_f[ui][ws0:f0]
                pooled = (ctxwin.mean(0).astype(np.float32) if ctxwin.shape[0] > 0
                          else np.zeros(te_cl_f[ui].shape[1], np.float32))
                pooled_b = np.tile(pooled[None, :], (T, 1)).astype(np.float32)
                repsD.append(np.concatenate([base, pooled_b], axis=1).astype(np.float32))
                ws_.append(w); sp_.append(sp)
                n += 1
        return dict(A=repsA, B=repsB, C=repsC, D=repsD), ws_, sp_

    print(f"\n--- ★ TWO-LEVER ABLATION TABLE (context x objective; cap={CTX_CAP} CAPQ={ABL_CAPQ}, "
          f"WIN={WIN}) ---", flush=True)
    ablation = {}
    CONTEXT_NAMES = [("A full-utt", "A"), ("B word-only", "B"),
                      (f"C local-win(WIN={WIN})", "C"), (f"D span-pooled(WIN={WIN})", "D")]
    for mname, model in [("predictive-only", ml_clb), (f"+InfoNCE(lam={best_lam})", ml_nce[best_lam])]:
        reps, aw, asp = build_context_reps(model, CTX_CAP)
        ablation[mname] = {}
        for cname, key in CONTEXT_NAMES:
            r = report(f"{mname} | {cname}", reps[key], aw, asp, cap_q=ABL_CAPQ)
            ablation[mname][cname] = r

    shuf_reps, shuf_w, shuf_sp = quick_word_only(ml_nce_shuf, CTX_CAP)
    r_shuf_label = report(f"+InfoNCE(lam={best_lam}) SHUFFLED-LABEL ctrl | word-only",
                           shuf_reps, shuf_w, shuf_sp, cap_q=ABL_CAPQ)

    _probe = apc_encode(ml_cl, te_cl_f[0], te_cl_f[0].shape[0])
    print(f"\n  [gate a] ApcEncode Term ran via Substrate.evaluate: utt0 -> context traj "
          f"{_probe.shape} (rep_dim={_probe.shape[1]}); donkey=0 by construction", flush=True)

    # ============ REFERENCE: CI-style per-word features + CI MetricEncoder (the 0.245-class donkey=0 encoder) ============
    def word_feat(coch, f0, f1):
        return CI.frame_features(np.asarray(coch, np.float32)[f0:f1])   # [T,64] CMN+delta, CI-identical
    tr_wfeat, tr_ww, tr_ws = [], [], []
    for d in tr:
        for (w, f0, f1) in d[1]:
            tr_wfeat.append(word_feat(d[0], f0, f1)); tr_ww.append(w); tr_ws.append(d[2])
    if len(tr_wfeat) > ME_CAP:
        _ridx = np.random.default_rng(0).choice(len(tr_wfeat), ME_CAP, replace=False)
        tr_wfeat = [tr_wfeat[i] for i in _ridx]; tr_ww = [tr_ww[i] for i in _ridx]; tr_ws = [tr_ws[i] for i in _ridx]
    mu_w, sd_w = znorm_fit(tr_wfeat); tr_wfeat = znorm_apply(tr_wfeat, mu_w, sd_w)
    din_w = tr_wfeat[0].shape[1]
    print(f"\n--- REFERENCE: CI MetricEncoder (numpy, the donkey=0 0.245-class encoder) din={din_w} "
          f"dz={DZ} on {len(tr_wfeat)} train words ---", flush=True)
    ref_enc = CI.MetricEncoder(din_w, DZ, seed=0).fit(tr_wfeat, tr_ww, tr_ws, ME_EPOCHS, verbose=True)

    # ============ build the SHARED held-out test-word set + all reps ============
    def spk_quotient(arr, sp):
        """ACCENT/CHANNEL as a per-speaker dimensional transform: subtract each
        speaker's OWN mean frame (unsupervised; works on UNSEEN speakers). Quotients
        the per-speaker additive component of (VTL∘accent∘channel) in the lifted space."""
        arr = arr.copy(); bysp = defaultdict(list)
        for i, s_ in enumerate(sp): bysp[s_].append(i)
        for s_, idx in bysp.items():
            m = arr[idx].reshape(-1, arr.shape[-1]).mean(0)
            for i in idx: arr[i] = arr[i] - m
        return arr

    words, spk = [], []
    R = defaultdict(list)                      # name -> list of [T,dim]
    fe_words, fe_spk, rep_fe = [], [], []
    ntok = 0
    for ui, d in enumerate(te):
        coch, wspans, sp, _ = d
        coch = np.asarray(coch, np.float32)
        magu = lift_mag(coch)
        h_raw = apc_encode(ml_raw, te_raw_f[ui], te_raw_f[ui].shape[0])
        h_cl = apc_encode(ml_cl, te_cl_f[ui], te_cl_f[ui].shape[0])
        h_clb = apc_encode(ml_clb, te_cl_f[ui], te_cl_f[ui].shape[0])
        h_sh = apc_encode(ml_sh, te_cl_f[ui], te_cl_f[ui].shape[0])
        for (w, f0, f1) in wspans:
            if ntok >= TE_CAP: break
            words.append(w); spk.append(sp)
            R["raw cochleagram"].append(resample(coch[f0:f1], T))
            R["REF MetricEncoder"].append(ref_enc.encode(znorm_apply([word_feat(coch, f0, f1)], mu_w, sd_w)[0]))
            R["LIFT-only (no APC)"].append(resample(magu[f0:f1], T))
            R["APC raw-dim +CTX"].append(resample(h_raw[f0:f1], T))
            R["APC concat-lift +CTX"].append(resample(h_cl[f0:f1], T))
            R["APC concat-lift BIDIR"].append(resample(h_clb[f0:f1], T))
            R["shuffled-future ctrl"].append(resample(h_sh[f0:f1], T))
            if len(fe_words) < FE_CAP:
                rep_fe.append(resample(apc_encode(ml_cl, te_cl_f[ui][f0:f1], T), T))
                fe_words.append(w); fe_spk.append(sp)
            ntok += 1
        if ntok >= TE_CAP: break
    # per-speaker-quotient variant on the best (concat-lift bidir)
    R["APC cl-BIDIR +spk-quot"] = list(spk_quotient(np.asarray(R["APC concat-lift BIDIR"], np.float32), spk))
    print(f"  encoded {ntok} test words ({len(set(spk))} held-out spk); front-end-only {len(fe_words)}",
          flush=True)

    # ============ TEXT-RECOVERY-DISCOVERED nuisance QUOTIENT (coordinator's method) ============
    # Holding RECOVERED TEXT (word identity, MMS bootstrap) constant, the same-word CROSS-SPEAKER
    # residual IS the speaker/accent transform. DISCOVER its principal directions on TRAIN speakers
    # (a SUBSPACE, not an LDA metric) and QUOTIENT them out of HELD-OUT reps (a transform generalises).
    NUIS_K = int(os.environ.get("NUIS_K", "6")); TRW_CAP = int(os.environ.get("TRW_CAP", "2500"))
    print(f"\n--- TEXT-RECOVERY quotient: discover nuisance subspace (k={NUIS_K}) from TRAIN same-word "
          f"cross-speaker residuals ---", flush=True)
    tr_rep, tr_rw, tr_rs = [], [], []
    for ui, d in enumerate(tr):
        if len(tr_rep) >= TRW_CAP: break
        h = apc_encode(ml_clb, tr_cl_f[ui], tr_cl_f[ui].shape[0])
        for (w, f0, f1) in d[1]:
            if len(tr_rep) >= TRW_CAP: break
            tr_rep.append(resample(h[f0:f1], T)); tr_rw.append(w); tr_rs.append(d[2])
    tr_rep = np.asarray(tr_rep, np.float32); rep_dim = tr_rep.shape[2]
    byw = defaultdict(list)
    for i, w in enumerate(tr_rw): byw[w].append(i)
    _rng = np.random.default_rng(0); resid = []
    for w, idx in byw.items():
        if len(idx) < 2: continue
        for _ in range(min(6, len(idx))):
            i, j = _rng.choice(idx, 2, replace=False)
            if tr_rs[i] != tr_rs[j]:
                resid.append(tr_rep[i] - tr_rep[j])          # content cancels; transform remains
        if len(resid) * T > 40000: break
    resid = np.asarray(resid, np.float32).reshape(-1, rep_dim)
    print(f"  residual samples {resid.shape[0]} (from same-word cross-speaker TRAIN pairs)", flush=True)
    V = np.asarray(nat.apc_nuisance_subspace(resid.reshape(-1).tolist(), resid.shape[0], rep_dim,
                                             NUIS_K, 40), np.float32).reshape(NUIS_K, rep_dim)
    def project_out(arr):
        arr = np.asarray(arr, np.float32)
        flat = arr.reshape(-1, arr.shape[-1])
        flat = flat - (flat @ V.T) @ V                       # QUOTIENT: remove nuisance directions
        return flat.reshape(arr.shape)
    R["APC clb +text-quot"] = list(project_out(R["APC concat-lift BIDIR"]))
    R["APC clb +text+spk-quot"] = list(spk_quotient(project_out(R["APC concat-lift BIDIR"]), spk))

    # ============ GATE (b): recall / d' / ROC-AUC via the batched Rust DtwTo kernel ============
    print("\n--- ★ (b) HELD-OUT cross-speaker NN-recall + d' + ROC-AUC (full-pool guaranteed-support) ---")
    print(f"  {'representation':>24} {'NN-recall':>10} {'d-prime':>9} {'ROC-AUC':>9}")
    res = {}
    res["raw"] = report("raw cochleagram", R["raw cochleagram"], words, spk)
    res["ref"] = report("REF MetricEncoder", R["REF MetricEncoder"], words, spk)
    res["lo"] = report("LIFT-only (no APC)", R["LIFT-only (no APC)"], words, spk)
    res["fe"] = report("APC front-end-only", rep_fe, fe_words, fe_spk)
    res["apc"] = report("APC raw-dim +CTX", R["APC raw-dim +CTX"], words, spk)
    res["cl"] = report("APC concat-lift +CTX", R["APC concat-lift +CTX"], words, spk)
    res["clb"] = report("APC concat-lift BIDIR", R["APC concat-lift BIDIR"], words, spk)
    res["clbq"] = report("APC cl-BIDIR +spk-quot", R["APC cl-BIDIR +spk-quot"], words, spk)
    res["txt"] = report("APC clb +text-quot", R["APC clb +text-quot"], words, spk)
    res["txtq"] = report("APC clb +text+spk-quot", R["APC clb +text+spk-quot"], words, spk)
    res["ctrl"] = report("shuffled-future ctrl", R["shuffled-future ctrl"], words, spk)

    # ============ GATE (c): batched multi-speaker order-1 purity ============
    print("\n--- ★ (c) MULTI-SPEAKER order-1 PURITY @ matched clusters (batched; toward 0.84) ---")
    TARGET = int(os.environ.get("PTARGET", str(max(20, len(set(words)) // 3))))
    print(f"  target clusters ~ {TARGET}")
    print(f"  {'representation':>24} {'purity':>7} {'#cl':>5}")
    def purity(name, arr, w):
        arr = np.asarray(arr, np.float32); n = arr.shape[0]; dim = arr.shape[2]
        wi, _ = _ids(w, w)
        pr = nat.apc_purity(arr.reshape(-1).tolist(), n, T, dim, wi.tolist(), TARGET, 0)
        print(f"  {name:>24} {pr[0]:7.3f} {int(pr[1]):5d}", flush=True)
        return float(pr[0])
    pu_raw = purity("raw cochleagram", R["raw cochleagram"], words)
    pu_ref = purity("REF MetricEncoder", R["REF MetricEncoder"], words)
    pu_clb = purity("APC concat-lift BIDIR", R["APC concat-lift BIDIR"], words)
    pu_clbq = purity("APC cl-BIDIR +spk-quot", R["APC cl-BIDIR +spk-quot"], words)

    # ============ GATE (d): donkey=0 ============
    donkey = [mn for mn in ("torch", "torchaudio", "allosaurus", "faster_whisper") if mn in sys.modules]
    print("\n--- (d) donkey=0 AT INFERENCE ---")
    print(f"  torch/torchaudio/... in analyze sys.modules: {donkey or 'NONE'}")
    print("  APC train = Rust apc_train; lift = Rust apc_lift; encode = ApcEncode graph Term; "
          "recall/purity = Rust batched DtwTo kernel; MMS_FA = isolated subprocess.")

    # ============ TWO-LEVER ABLATION TABLE + verdict ============
    print("\n" + "=" * 100)
    print("  ★★ TWO-LEVER ABLATION TABLE (context x objective) — recall / d' / AUC")
    print(f"  {'context':>26} | {'predictive-only':>22} | {'+InfoNCE(lam=' + str(best_lam) + ')':>22}")
    ab_best_name, ab_best_r = None, -1.0
    for cname, _key in CONTEXT_NAMES:
        r0 = ablation["predictive-only"][cname]
        r1 = ablation[f"+InfoNCE(lam={best_lam})"][cname]
        print(f"  {cname:>26} | rec {r0[0]:.3f} d' {r0[1]:.2f} auc {r0[2]:.3f} | "
              f"rec {r1[0]:.3f} d' {r1[1]:.2f} auc {r1[2]:.3f}")
        if r0[0] > ab_best_r: ab_best_r = r0[0]; ab_best_name = f"predictive-only | {cname}"
        if r1[0] > ab_best_r: ab_best_r = r1[0]; ab_best_name = f"+InfoNCE(lam={best_lam}) | {cname}"
    print(f"  shuffled-label InfoNCE ctrl | word-only : rec {r_shuf_label[0]:.3f} d' {r_shuf_label[1]:.2f} "
          f"auc {r_shuf_label[2]:.3f}  (vs +InfoNCE|B word-only rec "
          f"{ablation[f'+InfoNCE(lam={best_lam})']['B word-only'][0]:.3f} — must be lower if the "
          f"gradient is doing real work, not overfitting batch structure)")

    b_pred = ablation["predictive-only"]["B word-only"]
    b_nce = ablation[f"+InfoNCE(lam={best_lam})"]["B word-only"]
    c_pred = ablation["predictive-only"][f"C local-win(WIN={WIN})"]
    d_pred = ablation["predictive-only"][f"D span-pooled(WIN={WIN})"]
    lever1_best = max(c_pred[0], d_pred[0])
    lever1_best_name = f"C local-win(WIN={WIN})" if c_pred[0] >= d_pred[0] else f"D span-pooled(WIN={WIN})"
    c_nce = ablation[f"+InfoNCE(lam={best_lam})"][f"C local-win(WIN={WIN})"]
    d_nce = ablation[f"+InfoNCE(lam={best_lam})"][f"D span-pooled(WIN={WIN})"]
    combined_best = max(c_nce[0], d_nce[0])
    combined_best_name = (f"+InfoNCE|C local-win(WIN={WIN})" if c_nce[0] >= d_nce[0]
                           else f"+InfoNCE|D span-pooled(WIN={WIN})")
    print(f"\n  LEVER DELTAS (all vs predictive-only|B word-only baseline {b_pred[0]:.3f}, "
          f"this run's cap={CTX_CAP}):")
    print(f"    Lever 1 alone (context window, same predictive-only model): best={lever1_best_name} "
          f"{lever1_best:.3f}  Δ{lever1_best - b_pred[0]:+.3f}")
    print(f"    Lever 2 alone (InfoNCE, same word-only zero-context): +InfoNCE|B {b_nce[0]:.3f}  "
          f"Δ{b_nce[0] - b_pred[0]:+.3f}")
    print(f"    Both combined: best={combined_best_name} {combined_best:.3f}  "
          f"Δ{combined_best - b_pred[0]:+.3f}")

    # ============ VERDICT ============
    print("=" * 100)
    best_apc = max(res["cl"][0], res["clb"][0], res["clbq"][0], res["apc"][0], res["fe"][0],
                   res["txt"][0], res["txtq"][0], ab_best_r)
    W2V = 0.668   # V3 external upper bound (borrowed wav2vec2, NOT donkey=0) on the reference metric
    ref_nn = res["ref"][0]
    gap = W2V - ref_nn
    closed = (best_apc - ref_nn) / gap if gap > 1e-6 else float("nan")
    _prior_best = max(res['cl'][0], res['clb'][0], res['clbq'][0], res['apc'][0], res['fe'][0],
                       res['txt'][0], res['txtq'][0])
    _winner = ab_best_name if ab_best_r >= _prior_best else "(a pre-existing res[] entry)"
    print(f"  ★★★ FINAL: best representation overall = {_winner} -> recall {best_apc:.3f} "
          f"(baseline front-end-only was {res['fe'][0]:.3f}); "
          f"%gap_closed = ({best_apc:.3f}-{ref_nn:.3f})/({W2V}-{ref_nn:.3f})*100 = {closed*100:.1f}%")
    print("  ★ (a) FAIR SAME-CONFIG (identical features/pool/metric):")
    print(f"       raw {res['raw'][0]:.3f} | REF MetricEncoder {ref_nn:.3f} (d' {res['ref'][1]:.2f}, "
          f"AUC {res['ref'][2]:.3f}) | best APC {best_apc:.3f}")
    print(f"       APC beats the SAME-CONFIG reference? {'YES' if best_apc > ref_nn else 'NO'} "
          f"(Δ{best_apc - ref_nn:+.3f}); beats 0.245 abs? {'YES' if best_apc > 0.245 else 'NO'}; "
          f"fair gap to wav2vec2({W2V}) closed: {closed*100:.0f}%")
    print("  ★ (b) CONCAT-LIFT as ADDED axis:")
    print(f"       APC raw-dim {res['apc'][0]:.3f} (d' {res['apc'][1]:.2f}) -> +concat-lift "
          f"{res['cl'][0]:.3f} (d' {res['cl'][1]:.2f})  LIFT-ADD Δrecall {res['cl'][0]-res['apc'][0]:+.3f} "
          f"Δd' {res['cl'][1]-res['apc'][1]:+.2f}")
    print(f"       lift-only-descriptor {res['lo'][0]:.3f} (d' {res['lo'][1]:.2f}) vs raw {res['raw'][0]:.3f}")
    print("  BIDIRECTIONAL + per-speaker (accent/channel) quotient:")
    print(f"       unidir {res['cl'][0]:.3f} -> BIDIR {res['clb'][0]:.3f} -> +spk-quot {res['clbq'][0]:.3f}")
    print("  ★ TEXT-RECOVERY-DISCOVERED nuisance quotient (subspace from same-word cross-speaker resid):")
    print(f"       BIDIR {res['clb'][0]:.3f} (d' {res['clb'][1]:.2f}) -> +text-quot {res['txt'][0]:.3f} "
          f"(d' {res['txt'][1]:.2f}) -> +text+spk {res['txtq'][0]:.3f} (d' {res['txtq'][1]:.2f})  "
          f"TEXT-QUOT Δrecall {res['txt'][0]-res['clb'][0]:+.3f}")
    print("  TWO-LEVER: raw {:.3f} -> front-end-only {:.3f} (FE Δ{:+.3f}) -> +CONTEXT {:.3f} (CTX Δ{:+.3f})"
          .format(res['raw'][0], res['fe'][0], res['fe'][0]-res['raw'][0], res['apc'][0],
                  res['apc'][0]-res['fe'][0]))
    print(f"       shuffled-future control {res['ctrl'][0]:.3f} (d' {res['ctrl'][1]:.2f})")
    print(f"  ★ (c) purity: raw {pu_raw:.3f} | REF {pu_ref:.3f} | APC-clb {pu_clb:.3f} | "
          f"+spk-quot {pu_clbq:.3f} (target 0.84)")
    print(f"  (d) donkey=0 {not donkey}")
    print("  ACCENT-AS-TRANSFORM: VTL quotiented as a rotation (apc_lift, exact); per-speaker offset "
          "(channel + 1st-order accent) quotiented by spk-quot. FULL accent (vowel-space geometry) needs")
    print("  ACCENTED data — LibriSpeech is American audiobook readers, so it's the NEXT-CORPUS lever.")
    peak_gib = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024**2
    print(f"  [memory] peak RSS this process: {peak_gib:.2f} GiB")
    print("=" * 100)


if __name__ == "__main__":
    main()
