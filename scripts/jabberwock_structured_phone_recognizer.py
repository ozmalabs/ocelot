"""Reshape PER-FRAME phone recognition as GENERATIVE-INVERSION + ARTICULATORY COMPOSITION.

THE REFRAME (the creator's spec): the per-frame phone model needed ~21,000x the held corpus to
reach 0.5-0.7 (commit 494ad7b9) because it was posed as PER-FRAME DISCRIMINATIVE CLASSIFICATION
(frame -> 39-way label, from-scratch MLP) — a shape that must LEARN from examples everything the
structure already knows. An impractical data requirement is a symptom that the FORMULATION is wrong.
The arc PROVED structure-replaces-data before (handwriting AbS beat the learned feature +11pp on the
SAME data). The fix here: go back to the structured shape — recognize each frame by INVERTING a held
articulatory/VTL forward model (render-and-compare), with phones as COMPOSED distinctive features
(voicing, place, manner, height, backness) SHARED across phones.

THREE structured levers (all donkey=0, earn-not-borrow, no LLM, no borrowed weights):
  (1) PROTOTYPES FROM PRACTICAL DATA — per-phone band prototypes from a FEW exemplars (small N words),
      NOT a big training set.
  (2) FORWARD MODEL / INVERSION — recognize a frame by the phone whose prototype best RENDERS it under
      the held speaker normalisation (VTL band-warp, speech_abs_earner.warp_bands). render-and-compare
      via a held cosine distance; argmax = the decision (the existing AbS path's form). The speaker
      physics IS the structure: a few exemplars calibrate, the warp generalises across speakers.
  (3) COMPOSITIONAL — decompose each phone prototype into SHARED articulatory feature-templates
      (a factorial linear model: phone-proto = sum of its active feature-token band-templates). A
      feature template (e.g. place=alveolar) is ESTIMATED FROM ALL PHONES THAT SHARE IT, so the model
      learns ~the few shared axes, not 39 independent classes = the data-efficiency multiplier.

GATE (the reframe made falsifiable):
  MAIN  — per-frame acc vs CALIBRATION SIZE N for STRUCTURED (compositional AbS) vs the DISCRIMINATIVE
          MLP, same per-frame band feature, same dev set. PREDICTION: structure flat-high at small N
          (physics/features carry it), MLP steep-from-low (data-hungry). Report both curves honestly.
  DISCRIMINATIVE — (a) the VTL forward model MATTERS: vs a degenerate identity render (no warp);
                   (b) COMPOSITION beats a FLAT per-phone prototype at small N (feature sharing helps);
                   (c) SCRAMBLED feature decomposition loses the data-efficiency (structure does the work).

Features are the HELD cochlear band frames already in /home/matt/data/phonebank (produced by the held
cochlea ops). The VTL warp is the held forward model (speech_abs_earner). numpy is adapter-only
(prototype/least-squares/warp math + the from-scratch MLP's own SGD). No LLM, no pretrained weights.

Run (SMOKE first):  PYTHONPATH=runners/dsl/python:.:scripts \
       /home/matt/ozma/internal/research/.venv/bin/python \
       scripts/jabberwock_structured_phone_recognizer.py [max_words] [n_dev_words]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
from collections import Counter
from scripts.jabberwock_subword_recognizer import _load_ph
from scripts.jabberwock_earns_phone_model import viterbi_align   # HELD monotonic forced alignment
from domains.speech_abs_earner import warp_bands   # HELD VTL forward model (band-axis warp)

ALPHAS = np.array([0.85, 0.92, 1.0, 1.08, 1.18])   # candidate VTL factors; INCLUDES 1.0 so the warp
#                                                    model is a strict superset of the no-warp control
#                                                    (the degenerate forward model = ALPHAS_NOWARP)
ALPHAS_NOWARP = [1.0]                  # degenerate identity render (no speaker inversion)
NB = 32                               # cochlear bands per frame (the held-bank frame width)
CTXW = 3                              # +-CTXW context window (band-trajectory over time, like the lineage)


# ------------------------------------------------------------ ARTICULATORY FEATURE TABLE -----
# Each ARPAbet phone -> its set of distinctive/articulatory feature-VALUE tokens. Tokens are SHARED
# across phones (place=alveolar is one token used by T D S Z N L R), which is the whole point: a
# feature-template estimated from ALL phones bearing that token pools data across them. Standard
# distinctive-feature phonology (Chomsky-Halle / IPA), held structure — NOT borrowed weights.
_VOWEL = lambda h, b, r: {"manner=vowel", "voice=+", f"height={h}", f"back={b}", f"round={r}"}
_CONS = lambda m, v, p: {f"manner={m}", f"voice={v}", f"place={p}"}
PHONE_FEATURES = {
    # vowels: height(high/mid/low) x backness(front/central/back) x round(+/-)
    "IY": _VOWEL("high", "front", "-"),  "IH": _VOWEL("high", "front", "-"),
    "EH": _VOWEL("mid", "front", "-"),   "AE": _VOWEL("low", "front", "-"),
    "AH": _VOWEL("mid", "central", "-"), "ER": _VOWEL("mid", "central", "-") | {"rhotic"},
    "AA": _VOWEL("low", "back", "-"),    "AO": _VOWEL("mid", "back", "+"),
    "UH": _VOWEL("high", "back", "+"),   "UW": _VOWEL("high", "back", "+"),
    "OW": _VOWEL("mid", "back", "+"),    "OY": _VOWEL("mid", "back", "+") | {"diph"},
    "AW": _VOWEL("low", "central", "+") | {"diph"}, "AY": _VOWEL("low", "front", "-") | {"diph"},
    "EY": _VOWEL("mid", "front", "-") | {"diph"},
    # stops
    "P": _CONS("stop", "-", "bilabial"),  "B": _CONS("stop", "+", "bilabial"),
    "T": _CONS("stop", "-", "alveolar"),  "D": _CONS("stop", "+", "alveolar"),
    "K": _CONS("stop", "-", "velar"),     "G": _CONS("stop", "+", "velar"),
    # fricatives
    "F": _CONS("fricative", "-", "labiodental"),  "V": _CONS("fricative", "+", "labiodental"),
    "TH": _CONS("fricative", "-", "dental"),       "DH": _CONS("fricative", "+", "dental"),
    "S": _CONS("fricative", "-", "alveolar"),      "Z": _CONS("fricative", "+", "alveolar"),
    "SH": _CONS("fricative", "-", "postalveolar"), "ZH": _CONS("fricative", "+", "postalveolar"),
    "HH": _CONS("fricative", "-", "glottal"),
    # affricates
    "CH": _CONS("affricate", "-", "postalveolar"), "JH": _CONS("affricate", "+", "postalveolar"),
    # nasals
    "M": _CONS("nasal", "+", "bilabial"), "N": _CONS("nasal", "+", "alveolar"),
    "NG": _CONS("nasal", "+", "velar"),
    # liquids / glides
    "L": _CONS("liquid", "+", "alveolar"), "R": _CONS("liquid", "+", "postalveolar") | {"rhotic"},
    "W": _CONS("glide", "+", "bilabial"),  "Y": _CONS("glide", "+", "palatal"),
}


def build_feature_matrix(phones_set, feature_map=None):
    """phone-index -> feature-token indicator (nP x K), with an always-on intercept token. The rows of
    the fitted W are the SHARED feature-templates; a phone's prototype = its indicator row @ W."""
    fmap = feature_map if feature_map is not None else PHONE_FEATURES
    tokens = sorted({t for p in phones_set for t in fmap.get(p, set())})
    tok_i = {t: i for i, t in enumerate(tokens)}
    A = np.zeros((len(phones_set), len(tokens) + 1), np.float32)
    A[:, 0] = 1.0                                  # intercept (the global mean band-template)
    for pi, p in enumerate(phones_set):
        for t in fmap.get(p, set()):
            A[pi, tok_i[t] + 1] = 1.0
    return A, tokens


# ------------------------------------------------------------ FEATURES + LABELS --------------
def norm_frames(fr, W=CTXW):
    """Per-frame feature = a BLOCK-STRUCTURED context+delta band-trajectory, kept warpable: log-
    compressed cochlear frames stacked over t-W..t+W, plus the delta (velocity) channel, as
    (2*(2W+1)) sub-blocks of NB bands each, then L2-normalised. Holds local dynamics (a single frame
    was too weak, ~chance) WHILE preserving the per-NB-band frequency axis the VTL warp acts on (every
    sub-block warps with the same alpha = a tract shift across the whole window). Shared by BOTH
    structured and MLP, so the comparison is purely method, not feature."""
    M = np.log1p(np.maximum(np.asarray(fr, np.float32), 0.0))
    n, nb = M.shape
    d = np.vstack([np.zeros((1, nb), np.float32), np.diff(M, axis=0)])
    Pm = np.pad(M, ((W, W), (0, 0)), mode="edge")
    Pd = np.pad(d, ((W, W), (0, 0)), mode="edge")
    out = np.empty((n, 2 * (2 * W + 1) * nb), np.float32)
    for t in range(n):
        v = np.concatenate([Pm[t:t + 2 * W + 1].reshape(-1), Pd[t:t + 2 * W + 1].reshape(-1)])
        out[t] = v / max(np.linalg.norm(v), 1e-9)
    return out


def word_feats(words, pi):
    """Per-word (feature-matrix, phone-index-sequence). Skips words with an out-of-set phone."""
    out = []
    for (w, fr, ph, *_e) in words:
        F = norm_frames(fr)
        if len(F) == 0 or not ph or any(p not in pi for p in ph):
            continue
        out.append((F, [pi[p] for p in ph]))
    return out


def fit_bootstrap_means(wf, nP, dim):
    """FIXED bootstrap aligner: per-phone mean feature from FLAT-START (proportional) labels on a chunk.
    Used ONLY to mint clean forced-alignment labels (shared infrastructure, identical across the whole
    N-sweep — exactly the lineage's deep-datascale protocol), NOT a model under test."""
    S = np.zeros((nP, dim), np.float64); C = np.zeros(nP, np.float64)
    for F, pj in wf:
        n = len(F); P = len(pj)
        for i in range(n):
            p = pj[int(i * P / n)]; S[p] += F[i]; C[p] += 1
    M = S / np.maximum(C[:, None], 1.0)
    return (M / np.maximum(np.linalg.norm(M, axis=1, keepdims=True), 1e-9)).astype(np.float32)


def aligned_labels(wf, boot_means):
    """Force-align each word's frames to its KNOWN phone sequence (held Viterbi monotonic alignment)
    under the fixed bootstrap emission (cosine to phone means) -> clean per-frame phone labels. Much
    less boundary noise than proportional, lifting every method off the chance floor so they SEPARATE."""
    Xs, ys = [], []
    for F, pj in wf:
        emis = F @ boot_means.T                      # (n x nP) cosine emission
        lab = viterbi_align(emis, pj)                # monotonic forced alignment to pj
        Xs.append(F); ys.append(np.asarray(lab, np.int64))
    return np.concatenate(Xs), np.concatenate(ys)


# ------------------------------------------------------------ STRUCTURED (AbS) ---------------
def fit_flat_prototypes(X, y, nP):
    """FLAT structured model: per-phone prototype = mean band frame of that phone's calibration frames.
    No feature sharing — each of the nP classes estimated independently (data-starved at small N)."""
    protos = np.zeros((nP, X.shape[1]), np.float32)
    for p in range(nP):
        m = X[y == p]
        protos[p] = m.mean(0) if len(m) else 0.0
    return protos


def fit_compositional_prototypes(X, y, A):
    """COMPOSITIONAL structured model: a factorial linear fit X ~= A_frame @ W, where A_frame is each
    frame's phone feature-token indicator and W (K x bands) holds the SHARED feature-templates. Solved
    by least squares (pooled across all phones sharing a token). proto[p] = A[p] @ W. The data-
    efficiency multiplier: ~K shared templates estimated from ALL data, not nP independent classes."""
    Af = A[y]                                   # (frames x K) per-frame feature indicators
    W, *_ = np.linalg.lstsq(Af, X, rcond=None)  # (K x bands) shared feature-templates
    return (A @ W).astype(np.float32)           # (nP x bands) composed phone prototypes


def _warp_blocks(protos, alpha, nb=NB):
    """Apply the held VTL band-warp (speech_abs_earner.warp_bands) to EVERY NB-band sub-block of the
    block-structured feature, with the same alpha (one tract shift across the whole context+delta
    window). protos (nP x nblocks*nb) -> warped (nP x nblocks*nb)."""
    nP, dim = protos.shape; nblk = dim // nb
    out = np.empty_like(protos)
    for b in range(nblk):
        blk = protos[:, b * nb:(b + 1) * nb]            # (nP x nb)
        out[:, b * nb:(b + 1) * nb] = warp_bands(blk.T, alpha).T   # warp_bands wants (bands x cols)
    return out


def _warped_bank(protos, alphas):
    """Render each phone prototype under every candidate VTL warp (the held forward model), L2-normalise.
    Returns (nP*nalpha x dim) bank + index back to phone. Recognition = nearest warped render."""
    nP, dim = protos.shape
    bank = np.empty((nP * len(alphas), dim), np.float32)
    for ai, al in enumerate(alphas):
        bank[ai * nP:(ai + 1) * nP] = _warp_blocks(protos, al)
    bn = np.linalg.norm(bank, axis=1, keepdims=True)
    return bank / np.maximum(bn, 1e-8), nP


def predict_structured(Xdev, protos, alphas=ALPHAS):
    """INVERT the forward model per frame: argmax over phones of max-over-VTL cosine(frame, warp(proto)).
    The decision is an argmax over a held render-and-compare distance (the AbS path's form). donkey=0."""
    bank, nP = _warped_bank(protos, alphas)
    sims = Xdev @ bank.T                          # (frames x nP*nalpha)
    sims = sims.reshape(len(Xdev), len(alphas), nP).max(1)   # min-distance over VTL = max cosine
    return sims.argmax(1)


# ------------------------------------------------------------ DISCRIMINATIVE MLP -------------
def train_mlp(X, y, nP, Xdev, hidden=128, epochs=30, bs=256, lr=0.3, seed=0):
    """The data-hungry shape: a from-scratch random-init MLP (one hidden ReLU layer), the agent's OWN
    numpy SGD (weights are graph data; NO torch, NO pretrained). Same per-frame band feature, same dev.
    Per-frame decision = graph-native argmax over logits. donkey=0."""
    rng = np.random.default_rng(seed)
    mu = X.mean(0); sd = X.std(0) + 1e-6
    Xn = ((X - mu) / sd).astype(np.float32)
    Xdn = ((Xdev - mu) / sd).astype(np.float32)
    d = X.shape[1]
    W1 = (rng.standard_normal((d, hidden)) * np.sqrt(2.0 / d)).astype(np.float32)
    b1 = np.zeros(hidden, np.float32)
    W2 = (rng.standard_normal((hidden, nP)) * np.sqrt(2.0 / hidden)).astype(np.float32)
    b2 = np.zeros(nP, np.float32)
    vW1 = np.zeros_like(W1); vb1 = np.zeros_like(b1); vW2 = np.zeros_like(W2); vb2 = np.zeros_like(b2)
    n = len(Xn)
    for _ep in range(epochs):
        idx = rng.permutation(n)
        for s in range(0, n, bs):
            bi = idx[s:s + bs]; A0 = Xn[bi]; yb = y[bi]
            H = np.maximum(A0 @ W1 + b1, 0)
            Z = H @ W2 + b2
            Z -= Z.max(1, keepdims=True); P = np.exp(Z); P /= P.sum(1, keepdims=True)
            G = P; G[np.arange(len(yb)), yb] -= 1; G /= len(yb)
            gW2 = H.T @ G; gb2 = G.sum(0)
            Gh = (G @ W2.T) * (H > 0)
            gW1 = A0.T @ Gh; gb1 = Gh.sum(0)
            for prm, g, v in ((W2, gW2, vW2), (b2, gb2, vb2), (W1, gW1, vW1), (b1, gb1, vb1)):
                v *= 0.9; v -= lr * g; prm += v
    H = np.maximum(Xdn @ W1 + b1, 0)
    return (H @ W2 + b2).argmax(1)


# ------------------------------------------------------------ MAIN ---------------------------
def main():
    max_words = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    n_dev = int(sys.argv[2]) if len(sys.argv) > 2 else 1500
    t0 = time.time()
    print("=" * 100)
    print("STRUCTURED per-frame phone recognition — generative-inversion + articulatory composition")
    print("=" * 100, flush=True)

    # load calibration (train-clean) + dev (held-out) ---------------------------------------------
    shards_needed = max(1, max_words // 3500 + 2)
    cal = _load_ph("train-clean-100_*.pkl", shards_needed)[:max_words]
    dev = _load_ph("dev-clean_*.pkl", 4)[:n_dev]
    phones_set = sorted({p for _w, _f, ph, *_ in cal for p in ph})
    pi = {p: i for i, p in enumerate(phones_set)}; nP = len(phones_set)
    missing = [p for p in phones_set if p not in PHONE_FEATURES]
    print(f"  phones={nP}  cal words={len(cal)}  dev words={len(dev)}  bands={np.asarray(cal[0][1]).shape[1]}"
          f"  feature-table covers {nP-len(missing)}/{nP}  [{time.time()-t0:.0f}s]", flush=True)
    if missing:
        print(f"  WARNING uncovered phones: {missing}")

    A_true, tokens = build_feature_matrix(phones_set)
    print(f"  articulatory decomposition: {len(tokens)} shared feature tokens (+intercept) for {nP} phones"
          f"  -> {A_true.shape[1]} params vs {nP} flat prototypes", flush=True)

    cal_wf = word_feats(cal, pi)
    dev_wf = word_feats(dev, pi)
    dim = cal_wf[0][0].shape[1]
    # FIXED bootstrap aligner (fit once on a chunk; same across the whole N-sweep) -----------------
    boot_means = fit_bootstrap_means(cal_wf[:min(1000, len(cal_wf))], nP, dim)
    print(f"  feature dim={dim} ({dim//NB} NB-blocks)  bootstrap aligner on {min(1000,len(cal_wf))} words"
          f"  [{time.time()-t0:.0f}s]", flush=True)

    # dev features + forced-aligned labels (clean, shared, model-independent) -----------------------
    Xdev, ydev = aligned_labels(dev_wf, boot_means)
    chance = max(Counter(ydev.tolist()).values()) / len(ydev)
    print(f"  dev frames={len(Xdev)}  chance(majority)={chance:.3f}  [{time.time()-t0:.0f}s]", flush=True)

    # per-word aligned frame stacks so a prefix of WORDS maps to a clean prefix of FRAMES ----------
    word_X, word_y = [], []
    for F, pj in cal_wf:
        emis = F @ boot_means.T
        word_X.append(F); word_y.append(np.asarray(viterbi_align(emis, pj), np.int64))

    Ns = [n for n in (20, 50, 100, 200, 500, 1000, 2000) if n <= len(word_X)]
    if len(word_X) not in Ns:
        Ns.append(len(word_X))

    def cal_prefix(nw):
        return np.concatenate(word_X[:nw]), np.concatenate(word_y[:nw])

    rng = np.random.default_rng(7)
    scram = rng.permutation(nP)                 # scrambled phone->feature-set assignment (self-consistent)
    A_scram = A_true[scram]

    print("=" * 100)
    print(f"  {'N(words)':>9} {'frames':>8} | {'STRUCT-comp':>11} {'STRUCT-flat':>11} {'MLP':>7} |"
          f" {'comp-noWarp':>11} {'comp-scram':>10}")
    print("-" * 100, flush=True)
    rows = []
    for nw in Ns:
        Xc, yc = cal_prefix(nw)
        # structured: compositional AbS, flat-prototype AbS
        comp = fit_compositional_prototypes(Xc, yc, A_true)
        flat = fit_flat_prototypes(Xc, yc, nP)
        acc_comp = float((predict_structured(Xdev, comp) == ydev).mean())
        acc_flat = float((predict_structured(Xdev, flat) == ydev).mean())
        # discriminative MLP (same feature, same dev)
        acc_mlp = float((train_mlp(Xc, yc, nP, Xdev) == ydev).mean())
        # controls: compositional with NO warp (degenerate forward model); SCRAMBLED features
        acc_nowarp = float((predict_structured(Xdev, comp, alphas=ALPHAS_NOWARP) == ydev).mean())
        comp_scr = fit_compositional_prototypes(Xc, yc, A_scram)
        acc_scram = float((predict_structured(Xdev, comp_scr) == ydev).mean())
        rows.append((nw, len(Xc), acc_comp, acc_flat, acc_mlp, acc_nowarp, acc_scram))
        print(f"  {nw:>9} {len(Xc):>8} | {acc_comp:>11.3f} {acc_flat:>11.3f} {acc_mlp:>7.3f} |"
              f" {acc_nowarp:>11.3f} {acc_scram:>10.3f}  [{time.time()-t0:.0f}s]", flush=True)

    # ---- DIAGNOSTIC: does composition rescue RARE/ZERO-calibration phones? ------------------------
    # The compositional claim's MECHANISM: a phone seen 0 times in calibration can still be placed via
    # its SHARED feature templates (estimated from other phones), where the flat per-phone mean is just
    # zero. Tests whether feature-sharing buys zero-shot generalisation even if aggregate acc ties.
    Xc0, yc0 = cal_prefix(Ns[0])
    seen = set(np.unique(yc0).tolist())
    rare = [p for p in range(nP) if p not in seen]
    comp0 = fit_compositional_prototypes(Xc0, yc0, A_true)
    flat0 = fit_flat_prototypes(Xc0, yc0, nP)
    pc = predict_structured(Xdev, comp0); pf = predict_structured(Xdev, flat0)
    rare_mask = np.isin(ydev, rare)
    nrare = int(rare_mask.sum())
    if nrare:
        rc = float((pc[rare_mask] == ydev[rare_mask]).mean())
        rf = float((pf[rare_mask] == ydev[rare_mask]).mean())
        print(f"  RARE-PHONE diagnostic at N={Ns[0]}: {len(rare)} phones unseen in calibration, "
              f"{nrare} dev frames -> comp recall {rc:.3f} vs flat {rf:.3f} ({rc-rf:+.3f})", flush=True)
    else:
        print(f"  RARE-PHONE diagnostic at N={Ns[0]}: all {nP} phones seen in calibration "
              f"(no zero-shot phones to test).", flush=True)

    # ---- VERDICT ---------------------------------------------------------------------------------
    print("=" * 100)
    smallN = rows[0]; bigN = rows[-1]
    print(f"  MAIN — data-practicality (chance={chance:.3f}):")
    print(f"    at SMALL N={smallN[0]}: struct-comp {smallN[2]:.3f}  vs  MLP {smallN[4]:.3f}"
          f"   (struct {'WINS' if smallN[2] > smallN[4] else 'does NOT beat'} the MLP by "
          f"{smallN[2]-smallN[4]:+.3f})")
    print(f"    at LARGE N={bigN[0]}: struct-comp {bigN[2]:.3f}  vs  MLP {bigN[4]:.3f}"
          f"   (gap {bigN[2]-bigN[4]:+.3f})")
    s_rise = bigN[2] - smallN[2]; m_rise = bigN[4] - smallN[4]
    print(f"    SHAPE: struct rises {s_rise:+.3f} over the sweep (flat-high if small),"
          f"  MLP rises {m_rise:+.3f} (steep-from-low if large)")
    # small-N regime where structure beats the MLP
    win_Ns = [r[0] for r in rows if r[2] > r[4]]
    print(f"    structure beats the MLP at N in: {win_Ns if win_Ns else 'NONE'}")
    print(f"  DISCRIMINATIVE:")
    print(f"    forward-model MATTERS (warp vs identity render) at N={smallN[0]}: {smallN[2]:.3f} vs "
          f"{smallN[5]:.3f} (+{smallN[2]-smallN[5]:.3f})   at N={bigN[0]}: {bigN[2]:.3f} vs {bigN[5]:.3f} "
          f"(+{bigN[2]-bigN[5]:.3f})")
    print(f"    COMPOSITION beats FLAT prototypes at N={smallN[0]}: {smallN[2]:.3f} vs {smallN[3]:.3f} "
          f"({smallN[2]-smallN[3]:+.3f})   at N={bigN[0]}: {bigN[2]:.3f} vs {bigN[3]:.3f} "
          f"({bigN[2]-bigN[3]:+.3f})")
    print(f"    SCRAMBLED features lose the structure at N={smallN[0]}: comp {smallN[2]:.3f} vs scram "
          f"{smallN[6]:.3f} ({smallN[2]-smallN[6]:+.3f})")
    print(f"  donkey=0: per-frame decision = argmax over held render-and-compare (VTL forward model +"
          f" cochlear features); from-scratch MLP = agent's own numpy SGD. No LLM, no borrowed weights.")
    print("=" * 100, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
