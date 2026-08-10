"""LANGUAGE -> PERCEPTION LOOP, end-to-end on REAL cochleagram audio (donkey=0 at inference).

The CULMINATING INTEGRATION of two threads:
  * TEXT -> TRANSFORM-PRIOR (jabberwock_text_to_transform_prior): recover an accent's dimensional
    transform from EYE-DIALECT TEXT (voicing-aware g2p -> phoneme-sub rules + formant shift-vectors).
  * APC LEARNED FRONT-END (apc.rs): a Rust-native context-predictive front-end + the exact VTL
    rotation lift (apc_lift) + nuisance-subspace quotient (apc_nuisance_subspace).

THE LOOP (all agent-faculty / held Rust ops; no torch/LLM in the decision process):
  text (eye-dialect)
    --[voicing-aware g2p + Peterson-Barney formants + VecSub]-->  shift-vector in FORMANT space
    --[apc_formant_bands, infra piece 2]-->                        shift-vector in COCHLEAGRAM-BAND space
    --[prototype-gated ADD on REAL LibriSpeech cochleagrams]-->    an ACCENT injected on real audio
    --[prototype-gated SUBTRACT of the SAME text-recovered dirs]-->the acoustic QUOTIENT
    --[ApcEncode graph Term]-->                                    the learned APC representation
    --[held DtwTo + apc_recall]-->                                 does canonical vs accented SNAP?

★ UPGRADED POSITIVE CONTROL on REAL cochleagrams (vs the text thread's formant-space synthetic one):
  the transform is applied to / quotiented from REAL LibriSpeech cochleagrams and the LEARNED APC
  representation built on them. A RANDOM-direction quotient (same per-rule magnitude) is the
  discriminative control — it must NOT snap.

WIRING (infra piece 3): the text-recovered directions ALSO SEED the APC-rep nuisance-subspace
  projection — synthetic same-word (accented - canonical) rep residuals -> apc_nuisance_subspace ->
  project the accent direction out of held-out accented reps.

donkey=0: no torch/torchaudio/allosaurus/whisper in THIS process. The cochleagrams are read from a
  pre-extracted cache (the Rust ear over LibriSpeech; MMS_FA word spans were an isolated bootstrap
  subprocess when the cache was built, same discipline as apc_context_predictive_frontend.py).

Run (worktree python FIRST so the freshly-built _native with apc_formant_bands is used):
  PYTHONPATH=runners/dsl/python:.:scripts /home/matt/ozma/internal/research/.venv/bin/python \
      scripts/apc_language_perception_loop.py
Env: SMOKE(0) UTTS_TR(120) T(18) DH(64) KAHEAD(3) EPOCHS(10) SIGMA(0.35) ALPHA(0.7) RADIUS(0.09)
"""
from __future__ import annotations
import os, sys, pickle, resource

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (os.path.join(ROOT, "runners", "dsl", "python"), ROOT, os.path.join(ROOT, "scripts")):
    if p in sys.path:
        sys.path.remove(p)
    sys.path.insert(0, p)

import numpy as np
from collections import defaultdict

import substrate_rs as srs
from substrate_rs import _native as nat, Lit, Term
import scripts.jabberwock_text_to_transform_prior as TT

SCRATCH = os.environ.get(
    "SCRATCH",
    "/tmp/claude-1000/-home-matt-ozma-internal-research-experiments-gamma-substrate/"
    "3ed12bb3-7b58-44c0-b051-98640926c040/scratchpad")
CACHE = os.path.join(SCRATCH, "apc_libri_uttframes.pkl")

SMOKE = int(os.environ.get("SMOKE", "0"))
UTTS_TR = int(os.environ.get("UTTS_TR", "120"))
T = int(os.environ.get("T", "18"))
DH = int(os.environ.get("DH", "64"))
KAHEAD = int(os.environ.get("KAHEAD", "3"))
EPOCHS = int(os.environ.get("EPOCHS", "10"))
LR = float(os.environ.get("LR", "0.05"))
SIGMA = float(os.environ.get("SIGMA", "0.35"))     # band-render log-freq bump width
ALPHA = float(os.environ.get("ALPHA", "0.7"))      # accent strength (fraction of frame energy)
RADIUS = float(os.environ.get("RADIUS", "0.09"))   # prototype-gate radius (shape-space L2^2)
NUIS_K = int(os.environ.get("NUIS_K", "4"))
TOK_CAP = int(os.environ.get("TOK_CAP", "1200"))
PAIR_CAP = int(os.environ.get("PAIR_CAP", "500"))
if SMOKE:
    UTTS_TR, EPOCHS, TOK_CAP, PAIR_CAP = 25, 3, 200, 120

ACCENT = "irish_traveller_pikey"   # pikey: LOT-fronting (O->a) + TH-stopping (voiced D->d, voiceless T->t)


def _peak():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024 ** 2)


def _traj(fr):
    return tuple(tuple(float(v) for v in row) for row in fr)


def resample(fr, t):
    fr = np.asarray(fr, np.float32)
    n = len(fr)
    if n == t:
        return fr
    idx = np.linspace(0, n - 1, t)
    lo = np.floor(idx).astype(int); hi = np.minimum(lo + 1, n - 1); f = (idx - lo)[:, None]
    return (fr[lo] * (1 - f) + fr[hi] * f).astype(np.float32)


def utt_feats(coch):
    """APC input = [CMN value(32) ++ delta(32)] — identical to the APC front-end adapter."""
    coch = np.asarray(coch, np.float32)
    val = coch - coch.mean(0, keepdims=True)
    dlt = np.diff(coch, axis=0)
    dlt = np.vstack([np.zeros((1, coch.shape[1]), np.float32), dlt])
    return np.concatenate([val, dlt], axis=1).astype(np.float32)


# ============================================================================================== #
#  INFRA PIECE 2 — text-recovered shift-vectors rendered into COCHLEAGRAM-BAND space (Rust render)
# ============================================================================================== #
def band_shifts(recovered):
    """For every phoneme-substitution rule with a source AND target phoneme, render both phonemes
    into the 32-band cochleagram space (nat.apc_formant_bands) and take the L1-normalised SHAPE
    difference = the text-recovered accent direction in band space. Returns list of dicts."""
    shifts = []
    for r in recovered:
        src, tgt = r["src"], r["tgt"]
        if tgt is None or src not in TT.PHONEME_FORMANTS or tgt not in TT.PHONEME_FORMANTS:
            continue
        if r["kind"] not in ("vowel_shift", "th_stopping", "th_fronting"):
            continue
        fs = TT.PHONEME_FORMANTS[src]; ft = TT.PHONEME_FORMANTS[tgt]
        bs = np.asarray(nat.apc_formant_bands(float(fs[0]), float(fs[1]), float(fs[2]), SIGMA), np.float32)
        bt = np.asarray(nat.apc_formant_bands(float(ft[0]), float(ft[1]), float(ft[2]), SIGMA), np.float32)
        bs = bs / (bs.sum() + 1e-9); bt = bt / (bt.sum() + 1e-9)   # spectral SHAPE (L1)
        shifts.append({"src": src, "tgt": tgt, "kind": r["kind"], "voiced": r.get("voiced", False),
                       "src_shape": bs, "tgt_shape": bt, "dshape": (bt - bs).astype(np.float32)})
    return shifts


def _apply_dir(coch, shifts, gate, rng=None):
    """Prototype-gated per-frame vector op on a REAL cochleagram (no oracle phoneme labels).
    gate='src' -> ADD the shift where the frame's SHAPE matches a rule SOURCE (inject accent).
    gate='tgt' -> SUBTRACT where the frame matches a rule TARGET (quotient it out).
    gate='rand' -> SUBTRACT a RANDOM direction (per-rule magnitude preserved) at the tgt-matched
                   frames (discriminative control). `dshape` sums to ~0 so frame ENERGY is preserved."""
    coch = np.asarray(coch, np.float32).copy()
    nfr = coch.shape[0]
    E = coch.sum(1, keepdims=True) + 1e-9
    shape = coch / E
    for i in range(nfr):
        best, bd, bdir = None, 1e9, None
        for r in shifts:
            proto = r["src_shape"] if gate == "src" else r["tgt_shape"]
            d = float(np.sum((shape[i] - proto) ** 2))
            if d < bd:
                bd = d
                if gate == "src":
                    best, bdir = r, +r["dshape"]
                elif gate == "tgt":
                    best, bdir = r, -r["dshape"]
                else:  # rand: random direction, same L2 magnitude as this rule's dshape
                    g = rng.normal(0, 1, coch.shape[1]).astype(np.float32)
                    g = g - g.mean()                                   # keep energy-preserving
                    g = g / (np.linalg.norm(g) + 1e-9) * float(np.linalg.norm(r["dshape"]))
                    best, bdir = r, -g
        if best is not None and bd < RADIUS:
            coch[i] = np.maximum(coch[i] + ALPHA * float(E[i, 0]) * bdir, 0.0)
    return coch


# ============================================================================================== #
#  DTW snap metric (held DtwTo Term) + pooled cross-accent recall (batched Rust apc_recall kernel)
# ============================================================================================== #
def snap(s, canon, cond, words, spk, cap, seed=0):
    """Mean same-word CROSS-speaker DtwTo distance between a canonical token and a `cond` token."""
    rng = np.random.default_rng(seed)
    byw = defaultdict(list)
    for i, w in enumerate(words):
        byw[w].append(i)
    pairs = []
    for w, idx in byw.items():
        if len(idx) < 2:
            continue
        for _ in range(min(8, len(idx) * 2)):
            i, j = rng.choice(idx, 2, replace=False)
            if spk[i] != spk[j]:
                pairs.append((i, j))
    rng.shuffle(pairs); pairs = pairs[:cap]
    ds = [float(s.evaluate(Term("DtwTo", a=Lit(_traj(canon[i])), b=Lit(_traj(cond[j]))), {}))
          for (i, j) in pairs]
    return float(np.mean(ds)) if ds else float("nan")


def recall(arr, words, spk):
    arr = np.asarray(arr, np.float32); n, t, dim = arr.shape
    wi = {}; si = {}
    w = np.array([wi.setdefault(x, len(wi)) for x in words], np.int64)
    sp = np.array([si.setdefault(x, len(si)) for x in spk], np.int64)
    r = nat.apc_recall(arr.reshape(-1).tolist(), n, t, dim, w.tolist(), sp.tolist(), 400, 500, 1500, 0)
    return float(r[0]), float(r[1]), float(r[2])   # recall, d', auc


def main():
    resource.setrlimit(resource.RLIMIT_AS, (10 * 1024 ** 3, 10 * 1024 ** 3))
    if not os.path.exists(CACHE):
        print(f"BLOCKED: no cochleagram cache at {CACHE} — run apc_context_predictive_frontend.py "
              f"--extract first (isolated MMS_FA bootstrap).")
        return
    print(f"  [substrate_rs] {nat.__file__}", flush=True)
    assert hasattr(nat, "apc_formant_bands"), "apc_formant_bands missing — rebuild the crate"

    # ---------- STEP A: recover the accent transform from TEXT (voicing-aware) ----------
    s = srs.Substrate()
    pnode = TT.seed_phoneme_formants(s); TT.seed_voicing_lexicon(s)
    at, recovered = TT.recover(s, pnode, ACCENT, TT.ACCENTS[ACCENT])
    shifts = band_shifts(recovered)
    print(f"\n== LANGUAGE->PERCEPTION LOOP on REAL cochleagrams | accent='{ACCENT}' ==")
    print(f"  text-recovered rules (voicing-aware g2p):")
    for r in recovered:
        v = " voiced/edh" if r.get("voiced") else (" voiceless/theta" if r["src"] == "T" else "")
        sh = f"  dF=({r['shift'][0]:+.0f},{r['shift'][1]:+.0f},{r['shift'][2]:+.0f})Hz" if r["shift"] else ""
        print(f"      {r['src']:>3} -> {str(r['tgt']):<8} [{r['kind']:<11}]{v:<16}{sh}")
    print(f"  INFRA PIECE 2 — {len(shifts)} shift-vector(s) rendered into COCHLEAGRAM-BAND space "
          f"(apc_formant_bands, sigma={SIGMA}):")
    for r in shifts:
        print(f"      {r['src']}->{r['tgt']} [{r['kind']}] band-shift L2={np.linalg.norm(r['dshape']):.4f}")

    # ---------- STEP B: real cochleagrams (held-out speakers = dev-clean) ----------
    data = pickle.load(open(CACHE, "rb"))
    tr = [d for d in data if d[3] == "train"][:UTTS_TR]
    te = [d for d in data if d[3] == "test"]
    src_ph = {r["src"] for r in shifts}
    def undergoes(w):                       # does the word contain a source phoneme of the accent?
        return any(p in src_ph for p in TT.g2p_voiced(w))
    print(f"\n  DATA: train {len(tr)} utts | held-out test {len(te)} utts "
          f"({len(set(d[2] for d in te))} dev-clean spk)  [peak {_peak():.2f} GiB]", flush=True)

    # ---------- STEP C: train the APC learned front-end on REAL train cochleagrams (Rust) ----------
    tr_feats = [utt_feats(np.asarray(d[0], np.float32)) for d in tr]
    stk = np.concatenate(tr_feats); mu, sd = stk.mean(0), stk.std(0) + 1e-6
    tr_feats = [((f - mu) / sd).astype(np.float32) for f in tr_feats]
    ff = np.concatenate([f.reshape(-1) for f in tr_feats]).astype(np.float32)
    lens = [int(f.shape[0]) for f in tr_feats]
    din = tr_feats[0].shape[1]
    print(f"  training APC front-end IN RUST (apc_train din={din} dh={DH} K={KAHEAD} epochs={EPOCHS} "
          f"on {len(tr)} real utts)...", flush=True)
    model = [float(v) for v in nat.apc_train(ff.tolist(), lens, din, DH, KAHEAD, EPOCHS, LR, False, 0, False)]

    ns = nat.Substrate()   # native substrate for the ApcEncode dict-term (Rust graph eval)
    def apc_encode(featseq):
        term = {"type": "ApcEncode", "model": {"type": "Lit", "value": model},
                "seq": {"type": "Lit", "value": _traj(featseq)},
                "start": {"type": "Lit", "value": -1}, "end": {"type": "Lit", "value": -1},
                "out_len": {"type": "Lit", "value": int(featseq.shape[0])}}
        return np.asarray([[float(v) for v in row] for row in ns.evaluate(term, {})], np.float32)

    # ---------- STEP D: apply accent + quotient on REAL cochleagrams, then APC-encode ----------
    rng = np.random.default_rng(0)
    words, spk = [], []
    COND = ["canon", "acc", "textq", "randq"]           # cochleagram-band-space word slices
    band = {c: [] for c in COND}
    apc = {c: [] for c in COND}
    ntok = 0
    for d in te:
        if ntok >= TOK_CAP:
            break
        coch = np.asarray(d[0], np.float32); sp = d[2]
        wspans = [(w, f0, f1) for (w, f0, f1) in d[1] if undergoes(w)]
        if not wspans:
            continue
        acc = _apply_dir(coch, shifts, "src")              # inject the text-recovered accent
        tq = _apply_dir(acc, shifts, "tgt")                # quotient with the SAME text dirs
        rq = _apply_dir(acc, shifts, "rand", rng)          # random-direction control
        cutt = {"canon": coch, "acc": acc, "textq": tq, "randq": rq}
        # encode each condition's full utterance through the APC front-end, then slice words
        hutt = {}
        for c in COND:
            f = utt_feats(cutt[c]); f = ((f - mu) / sd).astype(np.float32)
            hutt[c] = apc_encode(f)
        for (w, f0, f1) in wspans:
            if ntok >= TOK_CAP:
                break
            words.append(w); spk.append(sp)
            for c in COND:
                band[c].append(resample(cutt[c][f0:f1], T))
                apc[c].append(resample(hutt[c][f0:f1], T))
            ntok += 1
    for c in COND:
        band[c] = np.asarray(band[c], np.float32); apc[c] = np.asarray(apc[c], np.float32)
    nw = len(set(words))
    print(f"  encoded {ntok} accent-bearing test words ({nw} distinct, {len(set(spk))} held-out spk)  "
          f"[peak {_peak():.2f} GiB]", flush=True)

    # ---------- STEP E: INFRA PIECE 3 — text-seeded APC-rep nuisance-subspace quotient ----------
    # residual = (accented rep - canonical rep) per word = the rep-space IMAGE of the text-recovered
    # accent direction; its principal subspace is projected OUT of the held-out accented reps.
    resid = (apc["acc"] - apc["canon"]).reshape(-1, apc["canon"].shape[-1])
    rep_dim = resid.shape[1]
    V = np.asarray(nat.apc_nuisance_subspace(resid.reshape(-1).tolist(), resid.shape[0], rep_dim,
                                             NUIS_K, 40), np.float32).reshape(NUIS_K, rep_dim)
    flat = apc["acc"].reshape(-1, rep_dim)
    apc["textNq"] = (flat - (flat @ V.T) @ V).reshape(apc["acc"].shape)
    # random-subspace control for the rep-space projection
    Vr = rng.normal(0, 1, (NUIS_K, rep_dim)).astype(np.float32)
    Vr /= (np.linalg.norm(Vr, axis=1, keepdims=True) + 1e-9)
    apc["randNq"] = (flat - (flat @ Vr.T) @ Vr).reshape(apc["acc"].shape)

    # ---------- STEP F: does the text-recovered quotient RECOVER canonical word-shape? ----------
    print(f"\n--- ★ SNAP on REAL cochleagram-BAND space (held DtwTo; LOWER=canonical/accented snap) ---")
    b_ideal = snap(s, band["canon"], band["canon"], words, spk, PAIR_CAP)
    b_raw = snap(s, band["canon"], band["acc"], words, spk, PAIR_CAP)
    b_txt = snap(s, band["canon"], band["textq"], words, spk, PAIR_CAP)
    b_rnd = snap(s, band["canon"], band["randq"], words, spk, PAIR_CAP)
    b_frac = (b_raw - b_txt) / max(b_raw - b_ideal, 1e-9)
    print(f"      canonical-vs-canonical (floor)          : {b_ideal:.4f}")
    print(f"      canonical-vs-ACCENTED  (raw gap)         : {b_raw:.4f}")
    print(f"      canonical-vs-accented +TEXT-quotient     : {b_txt:.4f}   -> {b_frac*100:.0f}% removed")
    print(f"      canonical-vs-accented +RANDOM-quotient   : {b_rnd:.4f}   (discriminative control)")
    snap_band = b_txt < b_raw - 1e-3 and b_txt < b_rnd - 1e-3
    print(f"      => {'SNAP (text beats raw AND random)' if snap_band else 'NO SNAP'}")

    print(f"\n--- ★ SNAP in the LEARNED APC representation (held DtwTo) ---")
    a_ideal = snap(s, apc["canon"], apc["canon"], words, spk, PAIR_CAP)
    a_raw = snap(s, apc["canon"], apc["acc"], words, spk, PAIR_CAP)
    a_txt = snap(s, apc["canon"], apc["textq"], words, spk, PAIR_CAP)
    a_rnd = snap(s, apc["canon"], apc["randq"], words, spk, PAIR_CAP)
    a_txtN = snap(s, apc["canon"], apc["textNq"], words, spk, PAIR_CAP)
    a_rndN = snap(s, apc["canon"], apc["randNq"], words, spk, PAIR_CAP)
    a_frac = (a_raw - a_txt) / max(a_raw - a_ideal, 1e-9)
    print(f"      canonical-vs-canonical (floor)               : {a_ideal:.4f}")
    print(f"      canonical-vs-ACCENTED  (raw gap)             : {a_raw:.4f}")
    print(f"      +TEXT cochleagram-quotient                   : {a_txt:.4f}   -> {a_frac*100:.0f}% removed")
    print(f"      +RANDOM cochleagram-quotient (control)       : {a_rnd:.4f}")
    print(f"      +TEXT-seeded rep nuisance-subspace (piece 3) : {a_txtN:.4f}")
    print(f"      +RANDOM rep-subspace (control)               : {a_rndN:.4f}")
    snap_apc = a_txt < a_raw - 1e-3 and a_txt < a_rnd - 1e-3
    snap_nq = a_txtN < a_raw - 1e-3 and a_txtN < a_rndN - 1e-3
    print(f"      => cochleagram-quotient {'SNAP' if snap_apc else 'NO SNAP'} | "
          f"text-seeded rep-subspace {'SNAP' if snap_nq else 'NO SNAP'}")

    # ---------- STEP G: cross-accent NN-recall (does quotient restore word identity?) ----------
    print(f"\n--- ★ CROSS-ACCENT NN-recall (pool canonical + <condition>; batched Rust DtwTo) ---")
    def pooled(cond):
        arr = np.concatenate([apc["canon"], apc[cond]], 0)
        w = words + words; sp = [x + "|c" for x in spk] + [x + "|a" for x in spk]
        return recall(arr, w, sp)
    for label, cond in [("canon+accented (raw)", "acc"), ("canon+TEXT-quot", "textq"),
                        ("canon+RANDOM-quot", "randq"), ("canon+TEXT-rep-subspace", "textNq")]:
        r = pooled(cond)
        print(f"      {label:>26}:  recall {r[0]:.3f}  d' {r[1]:.2f}  AUC {r[2]:.3f}")

    # ---------- donkey=0 ----------
    donkey = [m for m in ("torch", "torchaudio", "allosaurus", "faster_whisper", "openai")
              if m in sys.modules]
    print(f"\n--- donkey=0 AT INFERENCE ---")
    print(f"  torch/torchaudio/allosaurus/whisper/openai in sys.modules: {donkey or 'NONE'}")
    print(f"  loop = voicing-aware g2p + VecSub (held) + apc_formant_bands (Rust render) + "
          f"prototype vector-op + apc_train/ApcEncode (Rust) + DtwTo/apc_recall (held).")
    print(f"  peak {_peak():.2f} GiB")
    print("=" * 96)
    print(f"  VERDICT: real-cochleagram SNAP (band) {'YES' if snap_band else 'NO'} | "
          f"APC SNAP {'YES' if snap_apc else 'NO'} | text-seeded rep-subspace {'YES' if snap_nq else 'NO'} | "
          f"donkey=0 {not donkey}")
    print(f"  REAL-ACCENTED CORPUS: none with per-word labels on /home/matt/data (no naming_corpus/"
          f"repeating_corpus, no Jellyfin media, no L2/ESL). LibriSpeech=American readers; AMI=meetings")
    print(f"  (multi-accent but spontaneous, no word alignment); LibriTTS=no accent labels. The remaining")
    print(f"  dependency is a per-word-aligned ACCENTED corpus (e.g. an L2/ESL naming/repeating set).")


if __name__ == "__main__":
    main()
