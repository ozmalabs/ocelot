"""The jabberwock lifts the PHONE-MODEL CAPACITY — energy channel + nonlinear model.

The sub-word recognizer's binding floor is the per-frame phone model (~0.13), NOT
alignment/decode/measure (commits 23d528de, 4e56f158 — EM plateaus, deltas help). Two
named levers from the diagnosis:

  (1) ENERGY CHANNEL. The cochleagram is L2-NORMALISED PER FRAME at bank time, so per-
      frame ENERGY (the band-magnitude that cues stops' bursts and fricatives' frication)
      is divided out and discarded. The banked pickles store ONLY the normalised shape
      (every row-norm == 1.0). We RE-BANK a held set of words from RAW audio (whisper
      word-timed spans, exactly the existing oov-bank path) so frames() hands back the
      per-frame energy `e` alongside the shape, and ADD a log-energy + delta channel to
      the per-frame feature. Earned/derived from the signal — no borrowed weights.

  (2) NONLINEAR phone model. The encoder is a single LINEAR PCA->LDA; phones are not
      linearly separable. We expand with EARNED RANDOM FOURIER FEATURES (cos(Wx+b), W,b
      random-init from-scratch — an explicit RBF-kernel feature map, nonlinear in the
      input) BEFORE the LDA, then keep the per-frame DECISION graph-native (nearest
      phone-centroid, the existing emission). RFF is the cheap nonlinearity: one matmul,
      no gradient descent, no torch, no borrowed net.

ABLATION (isolates each lever): baseline / +energy / +nonlinear / +both, each with its
per-frame COMPUTE COST (the phone model is the cheapest, highest-frequency layer — runs
per frame on every utterance — so a capacity gain only "saves every time" if it STAYS
cheap; we report cost so a heavy variant that kills the cheapness is flagged).

DISCRIMINATIVE / EARNED: the model trained on REAL phone labels beats the SAME
architecture untrained (random RFF + random LDA, no fit) and trained on SCRAMBLED labels.
Per-phone stops/fricatives breakdown (where energy should help most).

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=runners/dsl/python:.:scripts PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u scripts/jabberwock_phone_capacity.py [n_test] [n_bank_utt]
"""
from __future__ import annotations
import os, sys, time, pickle
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
from collections import Counter, defaultdict
import substrate_rs as srs
import scripts.librispeech_wer as L
from scripts.jabberwock_reads_oov_from_phones import frames, phones as cmu_phones, STOP
from scripts.jabberwock_learned_encoder import _fit_pca, _fit_lda
from scripts.jabberwock_subword_recognizer import best_window_match
from domains.speech_world import SpeechWorld

CACHE = os.path.join(os.path.dirname(__file__), os.pardir, ".bigtmp", "phone_capacity_bank.pkl")

# phone classes where ENERGY should help most (bursts / frication)
_STOP = set("P T K B D G".split())
_FRIC = set("F V S Z SH ZH TH DH HH".split())
_AFFR = set("CH JH".split())
_ENERGY_CUED = _STOP | _FRIC | _AFFR


# ----------------------------------------------------------------------------- re-bank
def rebank(n_bank_utt, n_dev_utt):
    """Re-bank words from RAW audio retaining per-frame energy. Returns
    train=[(word, M_norm, e, phones)], dev=[...]. Cached (regenerable, NOT committed)."""
    if os.path.exists(CACHE):
        d = pickle.load(open(CACHE, "rb"))
        if d.get("nb") >= n_bank_utt and d.get("nd") >= n_dev_utt:
            return d["train"], d["dev"]
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    sw = SpeechWorld(srs.Substrate(), whisper_model="base.en")
    pairs = L.gather_pairs(limit=None)
    by_spk = defaultdict(list)
    for (path, sp, _ch, _ut, _tr) in pairs:
        by_spk[sp].append(path)
    spks = sorted(by_spk)
    train_spk, dev_spk = spks[:-9], spks[-9:]   # disjoint speakers, dev held out

    def harvest(spk_list, n_utt):
        out = []; n = 0
        for sp in spk_list:
            for path in by_spk[sp]:
                x, fs = L.load_flac(path); x = np.asarray(x, float)
                for (w, t0, t1) in sw.transcribe_lang_timed(x, fs, "en"):
                    w = "".join(c for c in w.lower() if c.isalpha())
                    ph = cmu_phones(w)
                    if not ph or not w.isalpha():
                        continue
                    seg = x[int(t0 * fs):int(t1 * fs)]
                    if seg.size < int(0.05 * fs):
                        continue
                    M, e = frames(seg)            # M = per-frame L2-normalised shape; e = per-frame energy
                    if M.shape[0] < 3:
                        continue
                    out.append((w, M.astype(np.float32), e.astype(np.float32), [str(p) for p in ph]))
                n += 1
                if n >= n_utt:
                    break
            if n >= n_utt:
                break
        return out

    print(f"  re-banking from RAW audio (energy retained): {n_bank_utt} train utts, {n_dev_utt} dev utts...", flush=True)
    t0 = time.time()
    train = harvest(train_spk, n_bank_utt)
    dev = harvest(dev_spk, n_dev_utt)
    print(f"  banked {len(train)} train words, {len(dev)} dev words [{time.time()-t0:.0f}s]", flush=True)
    pickle.dump({"train": train, "dev": dev, "nb": n_bank_utt, "nd": n_dev_utt}, open(CACHE, "wb"))
    return train, dev


# ------------------------------------------------------------------ per-frame features
def feat_shape(M, W=4):
    """per-frame context (t-W..t+W) of the L2-normalised spectral SHAPE + delta, L2.
    This is the BASELINE feature (matches jabberwock_earns_phone_model.ctxd)."""
    M = np.asarray(M, float); n, nb = M.shape
    d = np.vstack([np.zeros((1, nb)), np.diff(M, axis=0)])
    Pm = np.pad(M, ((W, W), (0, 0)), mode="edge")
    Pd = np.pad(d, ((W, W), (0, 0)), mode="edge")
    out = np.empty((n, (2 * W + 1) * nb * 2))
    for t in range(n):
        v = np.concatenate([Pm[t:t + 2 * W + 1].reshape(-1), Pd[t:t + 2 * W + 1].reshape(-1)])
        out[t] = v / max(np.linalg.norm(v), 1e-9)
    return out


def feat_energy(e, W=4):
    """per-frame ENERGY context: log-energy + delta-log-energy, contextualised over the
    window, z-scored within the utterance. The channel discarded by per-frame L2-norm."""
    e = np.asarray(e, float); n = len(e)
    le = np.log(e + 1e-6)
    le = (le - le.mean()) / (le.std() + 1e-9)        # within-utt z-score (speaker/gain invariant)
    dle = np.concatenate([[0.0], np.diff(le)])
    Pl = np.pad(le, (W, W), mode="edge")
    Pd = np.pad(dle, (W, W), mode="edge")
    out = np.empty((n, (2 * W + 1) * 2))
    for t in range(n):
        out[t] = np.concatenate([Pl[t:t + 2 * W + 1], Pd[t:t + 2 * W + 1]])
    return out


def build_X(items, use_energy):
    """concat per-frame features over all banked words; return X, Y (phone labels), pjs."""
    Xs, Ys = [], []
    for (_w, M, e, ph) in items:
        fs_ = feat_shape(M)
        if use_energy:
            fs_ = np.concatenate([fs_, feat_energy(e)], axis=1)
        n, P = len(fs_), len(ph)
        Xs.append(fs_)
        Ys.extend(ph[int(i * P / n)] for i in range(n))   # flat-start proportional labels
    return np.concatenate(Xs), Ys


# ------------------------------------------------------------------------ the encoder
class PhoneEncoder:
    """EARNED encoder: PCA -> [optional RANDOM-FOURIER nonlinearity] -> LDA, then
    per-phone GMM centroids. The per-frame DECISION (nearest centroid) is graph-native."""
    def __init__(self, nonlinear, rff_dim=600, gamma=None, seed=0):
        self.nonlinear = nonlinear; self.rff_dim = rff_dim; self.gamma = gamma; self.seed = seed

    def _rff(self, Z):
        return np.cos(Z @ self.Wr + self.br) * np.sqrt(2.0 / self.Wr.shape[1])

    def fit(self, X, Y, K=4):
        self.phones = sorted(set(Y)); self.pi = {p: i for i, p in enumerate(self.phones)}
        nP = len(self.phones)
        P = min(120, X.shape[0] - nP - 1)
        self.mu, self.Wp = _fit_pca(X, P)
        Z = (X - self.mu) @ self.Wp
        if self.nonlinear:
            rng = np.random.default_rng(self.seed)
            if self.gamma is None:
                # median-heuristic RBF bandwidth on a sample
                s = Z[rng.choice(len(Z), min(2000, len(Z)), replace=False)]
                med = np.median(np.linalg.norm(s[:500, None] - s[None, :500], axis=2)) + 1e-9
                self.gamma = 1.0 / (2 * med ** 2)
            self.Wr = rng.normal(0, np.sqrt(2 * self.gamma), size=(P, self.rff_dim))
            self.br = rng.uniform(0, 2 * np.pi, size=self.rff_dim)
            Z = self._rff(Z)
        self.Wl = _fit_lda(Z, Y, k=min(Z.shape[1], nP - 1))
        E = self._enc_proj(Z)
        # GMM-like per-phone centroids (k-means, K each)
        cent, cphone = [], []; rng = np.random.default_rng(0)
        for p in self.phones:
            Zp = E[[i for i in range(len(Y)) if Y[i] == p]]
            if len(Zp) == 0:
                continue
            Cc = Zp[rng.choice(len(Zp), min(K, len(Zp)), replace=False)].copy()
            for _ in range(6):
                lab = (((Zp[:, None, :] - Cc[None]) ** 2).sum(2)).argmin(1)
                for k in range(len(Cc)):
                    m = Zp[lab == k]
                    if len(m):
                        Cc[k] = m.mean(0)
            for c in Cc:
                cent.append(c); cphone.append(self.pi[p])
        self.cent = np.array(cent)
        self.cent /= np.clip(np.linalg.norm(self.cent, axis=1, keepdims=True), 1e-9, None)
        self.cphone = np.array(cphone)
        return self

    def _enc_proj(self, Z):
        R = Z @ self.Wl
        return R / np.clip(np.linalg.norm(R, axis=1, keepdims=True), 1e-9, None)

    def encode(self, X):
        Z = (np.asarray(X) - self.mu) @ self.Wp
        if self.nonlinear:
            Z = self._rff(Z)
        return self._enc_proj(Z)

    def predict(self, X):
        """graph-native per-frame emission decision: nearest phone-centroid (cosine)."""
        sims = self.encode(X) @ self.cent.T
        return self.cphone[sims.argmax(1)]


# ----------------------------------------------------------------------------- the eval
def per_frame_acc(enc, items, use_energy):
    Xd, Yd = build_X(items, use_energy)
    pred = enc.predict(Xd)
    return np.mean([enc.phones[pred[i]] == Yd[i] for i in range(len(Yd))]), pred, Yd


def per_class_acc(enc, pred, Yd, classes):
    """accuracy restricted to frames whose TRUE phone is in `classes`."""
    idx = [i for i in range(len(Yd)) if Yd[i] in classes]
    if not idx:
        return float("nan"), 0
    return np.mean([enc.phones[pred[i]] == Yd[i] for i in idx]), len(idx)


def content_recall(enc, n_test, use_energy):
    """boundary-free content recall on continuous utterances (like-for-like w/ baseline),
    + discriminative AUC (present vs absent content words)."""
    def decode(M, e):
        fs_ = feat_shape(M)
        if use_energy:
            fs_ = np.concatenate([fs_, feat_energy(e)], axis=1)
        idx = enc.predict(fs_)
        seq, prev = [], -1
        for k in idx:
            if k != prev:
                seq.append(enc.phones[k]); prev = k
        return seq

    pairs = L.gather_pairs(limit=n_test + 300)
    spk = sorted(set(p[1] for p in pairs)); test_spk = set(spk[-6:])
    test = [p for p in pairs if p[1] in test_spk][:n_test]
    func = set()  # function words filtered via STOP + length
    def is_content(w): return w not in STOP and len(w) >= 4 and cmu_phones(w)
    vocab = sorted({w for w in (cmu_phones and []) } |
                   {w for w in set(w for (_p, _s, _c, _u, tr) in test for w in L.normalise(tr))
                    if is_content(w)})
    rng = np.random.default_rng(0)
    rx35 = rx50 = tot = 0; pos, neg = [], []
    for (path, sp, ch, ut, tr) in test:
        try:
            M, e = frames(L.load_flac(path)[0])
        except Exception:
            continue
        pseq = decode(M, e)
        present = set(w.lower() for w in L.normalise(tr))
        inw = [w for w in present if is_content(w)]
        for w in inw:
            tgt = [str(x) for x in cmu_phones(w)]
            d = best_window_match(pseq, tgt)
            tot += 1; rx35 += (d <= 0.35); rx50 += (d <= 0.50); pos.append(d)
        cand = [w for w in vocab if w not in present]
        for w in (rng.choice(cand, min(len(inw), len(cand)), replace=False) if cand else []):
            neg.append(best_window_match(pseq, [str(x) for x in cmu_phones(w)]))
    pos = np.array(pos); neg = np.array(neg)
    auc = float(np.mean(pos[:, None] < neg[None, :])) if len(pos) and len(neg) else 0.0
    return rx35 / max(tot, 1), rx50 / max(tot, 1), auc, tot


def pickle_bank_crosscheck():
    """ROBUSTNESS: does the nonlinear lever lift the ORIGINAL committed pickle-bank
    representation (per-frame 0.128, jabberwock_earns_phone_model)? The pickle bank stores
    only L2-normalised frames (no energy), so only the NONLINEAR lever is testable here —
    a positive lift confirms the nonlinear gain is not an artifact of the re-banked data."""
    from scripts.jabberwock_earns_phone_model import ctxd
    from scripts.jabberwock_subword_recognizer import _load_ph
    tr = _load_ph("train-clean-100_*.pkl", 12)[:8000]
    dv = _load_ph("dev-clean_*.pkl", 12)[:1500]
    ph_set = sorted({p for _w, _f, ph in tr for p in ph}); pix = {p: i for i, p in enumerate(ph_set)}

    def feats(items):
        Xs, Ys = [], []
        for (_w, fr, ph) in items:
            cx = ctxd(fr); n, P = len(cx), len(ph)
            Xs.append(cx); Ys.extend(ph[int(i * P / n)] for i in range(n))
        return np.concatenate(Xs), Ys
    Xtr, Ytr = feats(tr); Xde, Yde = feats(dv)
    out = {}
    for nonlin in (False, True):
        enc = PhoneEncoder(nonlinear=nonlin).fit(Xtr, Ytr)
        pred = enc.predict(Xde)
        out[nonlin] = np.mean([enc.phones[pred[i]] == Yde[i] for i in range(len(Yde))])
    return out[False], out[True]


def main():
    n_test = int(sys.argv[1]) if len(sys.argv) > 1 else 25
    n_bank = int(sys.argv[2]) if len(sys.argv) > 2 else 360
    train, dev = rebank(n_bank, 90)
    print("=" * 88)
    print("PHONE-MODEL CAPACITY — energy channel + nonlinear (RFF), ablation + cost + controls")
    print("=" * 88)
    print(f"  train words={len(train)}  dev words={len(dev)}  (re-banked from raw audio, energy retained)")

    variants = [
        ("baseline (shape, linear)", False, False),
        ("+energy            ",      True,  False),
        ("+nonlinear (RFF)   ",      False, True),
        ("+both              ",      True,  True),
    ]
    results = {}
    for name, use_e, nonlin in variants:
        Xtr, Ytr = build_X(train, use_e)
        enc = PhoneEncoder(nonlinear=nonlin).fit(Xtr, Ytr)
        # per-frame cost: time to encode+decide one frame (matmul cost, amortized per utterance)
        Xd, Yd = build_X(dev, use_e)
        nrep = max(1, 200000 // max(len(Xd), 1))
        t0 = time.perf_counter()
        for _ in range(nrep):
            enc.predict(Xd)
        cost_us = (time.perf_counter() - t0) / (nrep * len(Xd)) * 1e6   # microseconds / frame
        acc, pred, Yd = per_frame_acc(enc, dev, use_e)
        stop_acc, ns = per_class_acc(enc, pred, Yd, _STOP)
        fric_acc, nf = per_class_acc(enc, pred, Yd, _FRIC)
        results[name] = (acc, cost_us, stop_acc, fric_acc, enc, use_e)
        print(f"  [{name}] per-frame acc {acc:.3f}  cost {cost_us:6.2f} us/frame  "
              f"stops {stop_acc:.3f} fric {fric_acc:.3f}", flush=True)

    base_acc = results["baseline (shape, linear)"][0]
    chance = 1.0 / len(results["baseline (shape, linear)"][4].phones)
    print(f"  (chance per-frame ~{chance:.3f})")

    # ---- DISCRIMINATIVE / EARNED controls on the best variant (+both) ----
    print("\n" + "-" * 88)
    print("  DISCRIMINATIVE / EARNED controls (+both: energy + nonlinear)")
    Xtr, Ytr = build_X(train, True)
    real = PhoneEncoder(nonlinear=True).fit(Xtr, Ytr)
    racc = per_frame_acc(real, dev, True)[0]
    # untrained: random RFF + random LDA projection (NO fit on labels), same arch
    unt = PhoneEncoder(nonlinear=True); unt.phones = real.phones; unt.pi = real.pi
    unt.mu, unt.Wp = real.mu, real.Wp
    rng = np.random.default_rng(7)
    Z = (Xtr - unt.mu) @ unt.Wp
    unt.gamma = real.gamma; unt.Wr = rng.normal(0, np.sqrt(2 * real.gamma), (unt.Wp.shape[1], real.rff_dim))
    unt.br = rng.uniform(0, 2 * np.pi, real.rff_dim)
    unt.Wl = rng.normal(0, 1, (real.rff_dim, real.Wl.shape[1]))   # random projection, no LDA fit
    Erand = unt._enc_proj(unt._rff(Z))
    # centroids from random projection of REAL features (so only the SEPARATION is unlearned)
    cent, cphone = [], []
    for p in unt.phones:
        Zp = Erand[[i for i in range(len(Ytr)) if Ytr[i] == p]]
        if len(Zp):
            cent.append(Zp.mean(0)); cphone.append(unt.pi[p])
    unt.cent = np.array(cent); unt.cent /= np.clip(np.linalg.norm(unt.cent, axis=1, keepdims=True), 1e-9, None)
    unt.cphone = np.array(cphone)
    uacc = per_frame_acc(unt, dev, True)[0]
    # scrambled labels: same arch, fit on SHUFFLED phone labels
    Ys = list(Ytr); np.random.default_rng(3).shuffle(Ys)
    scr = PhoneEncoder(nonlinear=True).fit(Xtr, Ys)
    sacc = per_frame_acc(scr, dev, True)[0]
    print(f"  real-trained {racc:.3f}  vs  untrained(random proj) {uacc:.3f}  vs  scrambled-labels {sacc:.3f}")
    print(f"  -> training does the work: {'PASS' if racc > uacc + 0.02 and racc > sacc + 0.02 else 'FAIL'}")

    # ---- content recall: baseline vs +both ----
    print("\n" + "-" * 88)
    print("  boundary-free content recall (continuous utts) + discriminative AUC")
    b35, b50, bauc, bt = content_recall(results["baseline (shape, linear)"][4], n_test, False)
    e35, e50, eauc, et = content_recall(real, n_test, True)
    print(f"  baseline: @0.35 {b35:.3f}  @0.50 {b50:.3f}  AUC {bauc:.3f}  ({bt} words)")
    print(f"  +both   : @0.35 {e35:.3f}  @0.50 {e50:.3f}  AUC {eauc:.3f}  ({et} words)")

    # ---- ROBUSTNESS: nonlinear lever on the original committed pickle-bank (0.128) ----
    print("\n" + "-" * 88)
    print("  ROBUSTNESS: nonlinear lever on the ORIGINAL pickle-bank representation (committed 0.128)")
    pb_lin, pb_nl = pickle_bank_crosscheck()
    print(f"  pickle-bank linear (=committed) {pb_lin:.3f}  ->  +nonlinear (RFF) {pb_nl:.3f}  (+{pb_nl-pb_lin:+.3f})")

    print("\n" + "=" * 88)
    best = max((results[n][0], n) for n in results)
    print(f"  per-frame: baseline {base_acc:.3f} -> best {best[0]:.3f} ({best[1].strip()})  "
          f"(+{best[0]-base_acc:+.3f})")
    print(f"  content recall @0.50: {b50:.3f} -> {e50:.3f}   AUC {bauc:.3f} -> {eauc:.3f}")
    print(f"  HONEST FLOOR: real phone models reach 0.5-0.7; we are at {best[0]:.3f}.")
    print("=" * 88)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
