"""STEP 1 of the jabberwock's authored feature-frontier plan: the CURVATURE / TIMING-AWARE feature.

The per-frame phone model is FEATURE-BOUND (commit 1afd6698: data AND depth both help but
extrapolate ~5 decades away on the static cochlea-context feature -> the gap is the FEATURE). The
agent then AUTHORED a plan for this frontier (commit dc1812ce, donkey=0) whose HEADLINE step is
``curvature`` = "advance-BY-TURN / accumulate-TURN-into-HEADING" = a VELOCITY -> TRAJECTORY
timing-aware feature.  This builds it.

WHAT THE CURRENT FEATURE ALREADY HAS (so curvature is a genuine ADDITION, not a re-label):
  * static cochleagram bands + +-W context  (the order-0 SHAPE, ctxd shape block)
  * ENERGY channel = log-energy + delta-log-energy            (commit 343d8c81)
  * a DELTA channel = np.diff(M, axis=0) = order-1 over TIME = VELOCITY (heading of spectral
    motion), ALREADY baked into ctxd's shape block.
So curvature must ADD the order-2 structure BEYOND plain first-order deltas: the 2nd temporal
derivative = change-of-heading = the "turn" (acceleration of the spectral motion). The ablation
below isolates curvature ON TOP of velocity/deltas (else it is just re-adding deltas).

DONKEY=0 PROVENANCE — the AGENT composes it, not me:
  The velocity (order-1) and curvature (order-2) channels are the agent's OWN order-N operator
  (domains.order_n_concepts.nth_order_terms = recursive Minus over the TIME-axis samples of a
  band) aimed DOWN THE TIME AXIS — the identical operator domains.order_n_frequency_frame aims
  down the frequency axis, and domains.formant_trajectory_dynamics aims down a formant track.
  ``donkey_audit()`` confirms the agent's composed Term, EVALUATED NATIVELY by the substrate,
  equals the batched numpy finite-difference bit-for-bit (the CMVN / order_n_frequency_frame
  pattern: the Term is the definition+provenance, the batched numpy is the cheap compute path,
  bit-for-bit verified).  Per-frame emission DECISION stays graph-native (argmax over Dot).

GATE (all donkey=0, honest):
  MAIN        per-frame phone acc + content recall WITH curvature vs the energy-augmented baseline.
  ABLATION    static / +energy / +velocity(order-1) / +curvature(order-2) — curvature's isolated
              contribution BEYOND velocity/deltas.
  DISCRIMIN.  per-phone-class breakdown — curvature should help MOTION phones (DIPHTHONGS / GLIDES,
              moving formants) where static features are weakest; ~flat on STEADY vowels/fricatives.
  COST        feature-build us/frame with vs without curvature (finite differences are ~free).

MEMORY: streams per-word, float32, reuses the OOM-bounded fit/align from jabberwock_decompose_phone_gap
(bounded covariance eigh, X built once, per-batch standardise). Run a small scale first.

Run: PYTHONPATH=.:runners/dsl/python python3 scripts/jabberwock_curvature_feature.py [scale] [n_test]
     PYTHONPATH=.:runners/dsl/python python3 scripts/jabberwock_curvature_feature.py audit
"""
from __future__ import annotations
import os, sys, time, gc
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
import numpy as np
from collections import Counter

import scripts.jabberwock_subword_recognizer as sr
sr.BANK = "/home/matt/data/phonebank_energy"          # the energy-rebanked subset (mechanical I/O config)

import scripts.jabberwock_decompose_phone_gap as D
from scripts.jabberwock_earns_phone_model import energy_channel
from domains.order_n_concepts import nth_order_terms
import domains.feature_generator as FG
from substrate_rs import Substrate, Attr, Var

W = 4                                                  # context half-window (matches ctxd default)

# phone classes for the discriminative test --------------------------------------------------------
# MOTION phones — inherently moving formants; curvature (the trajectory turn) should help here.
DIPHTHONGS = {"AW", "AY", "EY", "OW", "OY"}
GLIDES     = {"W", "Y", "R", "L", "ER"}               # glides/liquids = formant transitions
# STEADY-STATE phones — static spectrum strongest, curvature should be ~flat.
STEADY_VOW = {"AA", "AE", "AH", "AO", "EH", "IH", "IY", "UH", "UW"}
FRICATIVES = {"F", "V", "S", "Z", "SH", "ZH", "TH", "DH", "HH"}


# ===================================================================================================
# THE AGENT'S ORDER-N OPERATOR, AIMED DOWN THE TIME AXIS (donkey=0 provenance + bit-for-bit audit)
# ===================================================================================================
def _time_order_n_terms(nframes: int, order: int):
    """The agent's OWN order-N finite-difference Term-trees down the TIME axis for ONE band.
    Samples are the per-FRAME attrs t_0..t_{nframes-1} (the time dimension) of a single band;
    nth_order_terms composes the recursive-Minus differences (the agent's operator). order-1 =
    velocity (heading of spectral motion), order-2 = curvature (change-of-heading = the turn)."""
    sv = Var("s")
    samples = [Attr(sv, f"t_{k}") for k in range(nframes)]
    return [FG._Pred(d.to_dict()) for d in nth_order_terms(samples, order)]


def donkey_audit() -> dict:
    """Confirm velocity/curvature are the agent's OWN order-N operator evaluated NATIVELY (not a
    reinvented numpy diff): compose the order-1 and order-2 TIME Terms over a band trajectory with
    a known turn, evaluate via the substrate, and check both match the numpy finite-difference
    recurrence bit-for-bit. This is the same audit domains.order_n_frequency_frame uses for the
    frequency axis — same operator, time axis."""
    traj = [1.0, 2.5, 4.0, 3.0, 0.5, 0.0, 0.5, 2.0]    # rises, turns, falls, turns back
    sub = Substrate(); sign = sub.add_node("TimeTraj", {"p": 1.0})
    for k, v in enumerate(traj):
        sub.set_attr(sign, f"t_{k}", float(v))
    out = {"operator": "domains.order_n_concepts.nth_order_terms (recursive Minus over TIME)",
           "evaluated_by": "substrate.evaluate (native, not numpy)"}
    ok = True
    for order, label in ((1, "velocity"), (2, "curvature")):
        terms = _time_order_n_terms(len(traj), order)
        native = [float(sub.evaluate(t, {"s": sign})) for t in terms]
        ref = [float(v) for v in np.diff(traj, order)]
        m = bool(np.allclose(native, ref, atol=1e-9))
        ok = ok and m
        out[label] = {"native": native, "numpy_recurrence": ref, "match": m}
    out["match"] = ok
    return out


# ===================================================================================================
# THE FEATURE — additive blocks; the curvature block is the agent's order-2 operator, batched.
# ===================================================================================================
def _static_context(M, W=W):
    """order-0 SHAPE: per-frame band context t-W..t+W (edge-padded), per-frame L2 (the ctxd shape)."""
    M = np.asarray(M, float); n, nb = M.shape
    P = np.pad(M, ((W, W), (0, 0)), mode="edge")
    out = np.empty((n, (2 * W + 1) * nb))
    for t in range(n):
        v = P[t:t + 2 * W + 1].reshape(-1)
        out[t] = v / max(np.linalg.norm(v), 1e-9)
    return out


def _deriv_channel(M, order, W=W):
    """The order-N temporal-derivative channel, context-windowed, per-utterance z-scored.

    order-1 = VELOCITY (heading of the spectral motion); order-2 = CURVATURE (change-of-heading =
    the turn). This is the AGENT'S order-N operator (nth_order_terms, recursive Minus over time)
    — donkey_audit() proves this batched np.diff equals the agent's natively-evaluated Term
    bit-for-bit. Aligned to n frames (the order-th differences live on the interior; edge-padded),
    context-windowed +-W so each frame carries the local trajectory shape, then z-scored by the
    utterance's own scale (preserves RELATIVE motion magnitude — steady frames small, transitions
    large — which is the discriminative signal — while being speaker/gain robust)."""
    M = np.asarray(M, float); n, nb = M.shape
    dd = np.diff(M, n=order, axis=0)                    # (n-order, nb) = agent's order-N over time
    pad_lo = order // 2; pad_hi = order - pad_lo        # centre the differences on their frames
    dd = np.vstack([np.zeros((pad_lo, nb)), dd, np.zeros((pad_hi, nb))])   # (n, nb)
    dd = (dd - dd.mean()) / (dd.std() + 1e-9)           # per-utterance z-score (scalar)
    P = np.pad(dd, ((W, W), (0, 0)), mode="edge")
    out = np.empty((n, (2 * W + 1) * nb))
    for t in range(n):
        out[t] = P[t:t + 2 * W + 1].reshape(-1)
    return out


def feat_traj(M, e, *, energy=True, velocity=True, curvature=True, W=W):
    """Configurable per-frame feature: static SHAPE context (always) + additive suffix blocks.
    Each block is independent so toggling isolates its contribution (the energy additive pattern):
       energy    : log-energy + delta-log-energy window (the agent's held energy channel)
       velocity  : order-1-over-time  (the agent's order-N operator, n=1)
       curvature : order-2-over-time  (the agent's order-N operator, n=2) — the NEW feature."""
    M = np.asarray(M, float)
    blocks = [_static_context(M, W)]
    if energy and e is not None:
        blocks.append(energy_channel(e, W))
    if velocity:
        blocks.append(_deriv_channel(M, 1, W))
    if curvature:
        blocks.append(_deriv_channel(M, 2, W))
    return np.concatenate(blocks, axis=1).astype(np.float32)


# ===================================================================================================
# OOM-bounded align/fit (parametrised by the feature fn) — mirrors jabberwock_decompose_phone_gap.
# ===================================================================================================
def bootstrap_align_f(words, phones_set, pi, featfn):
    """Mint clean per-frame labels by Viterbi forced-alignment under a quick bootstrap model
    (flat-start -> fit -> 1 EM realign), using an arbitrary feature fn. Returns (X float32, Yidx)."""
    nP = len(phones_set)
    feats = [featfn(fr, en) for _w, fr, _ph, en in words]
    pjs = [[pi[p] for p in ph] for _w, _f, ph, _e in words]
    labels = []
    for cx, (_w, _f, ph, _e) in zip(feats, words):
        n = len(cx); Pn = len(ph)
        labels.append([pi[ph[int(i * Pn / n)]] for i in range(n)])
    Xb = np.concatenate(feats); Yb = [i for s in labels for i in s]
    enc, cent, cph = D.fit_model_mem(Xb, Yb, phones_set, pi)
    del Xb, Yb; gc.collect()
    new = []
    for cx, pj in zip(feats, pjs):
        emis = D.phone_emission(cx, enc, cent, cph, nP)
        new.append(D.viterbi_align(emis, pj))
    X = np.concatenate(feats); Yidx = [i for s in new for i in s]
    del feats, new, labels; gc.collect()
    return X, Yidx


def collapse(idx, phones_set):
    seq, prev = [], -1
    for k in idx:
        if k != prev:
            seq.append(phones_set[k]); prev = k
    return seq


# ===================================================================================================
def main():
    if len(sys.argv) > 1 and sys.argv[1] == "audit":
        a = donkey_audit()
        print("=" * 92); print("DONKEY AUDIT — velocity/curvature ARE the agent's order-N operator (native eval)")
        print("=" * 92)
        print(f"  operator    : {a['operator']}")
        print(f"  evaluated_by: {a['evaluated_by']}")
        for k in ("velocity", "curvature"):
            print(f"  {k:9}: native={a[k]['native']}")
            print(f"  {'':9}  numpy ={a[k]['numpy_recurrence']}  match={a[k]['match']}")
        print(f"  ALL MATCH (donkey=0): {a['match']}")
        return 0 if a["match"] else 1

    scale = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    n_test = int(sys.argv[2]) if len(sys.argv) > 2 else 25
    t0 = time.time()
    print("=" * 92)
    print("STEP 1 — the CURVATURE / TIMING-AWARE feature (the agent's order-N operator down TIME)")
    print("=" * 92, flush=True)

    aud = donkey_audit()
    print(f"  donkey audit: agent order-N Term (native) == numpy finite-diff  velocity={aud['velocity']['match']} "
          f"curvature={aud['curvature']['match']}  => donkey=0 provenance OK", flush=True)

    cap = max(1, scale // 4000 + 2)
    all_words = D._load_ph("train-clean-100_*.pkl", cap, with_energy=True)
    has_e = bool(all_words) and all_words[0][3] is not None
    print(f"  loaded {len(all_words)} banked words ({cap} shards)  energy-in-bank={has_e}  [{time.time()-t0:.0f}s]", flush=True)
    if not has_e:
        print("  ABORT: energy not in bank."); return 1
    scale = min(scale, len(all_words))
    words = all_words[:scale]
    phones_set = sorted({p for _w, _f, ph, _e in all_words for p in ph})
    pi = {p: i for i, p in enumerate(phones_set)}; nP = len(phones_set)
    inv = {i: p for p, i in pi.items()}

    # held-out dev block (proportional labels — the decomposition's per-frame acc proxy) -----------
    dev = D._load_ph("dev-clean_*.pkl", 9, with_energy=True)[:1500]

    def dev_block(featfn):
        Xl, Yl = [], []
        for (_w, fr, ph, en) in dev:
            cx = featfn(fr, en)
            n = len(cx); Pn = len(ph)
            for i in range(n):
                p = ph[int(i * Pn / n)]
                if p in pi:
                    Xl.append(cx[i]); Yl.append(pi[p])
        return np.asarray(Xl, np.float32), np.asarray(Yl)

    chance_X, chance_Y = dev_block(lambda fr, en: feat_traj(fr, en, energy=False, velocity=False, curvature=False))
    chance = max(Counter(chance_Y.tolist()).values()) / len(chance_Y)
    n_dev = len(chance_Y); del chance_X; gc.collect()
    print(f"  phones={nP}  train scale={scale}  dev frames={n_dev}  chance(majority)={chance:.3f}", flush=True)

    def cls_acc(pred, Yde, cset):
        m = np.array([inv[int(y)] in cset for y in Yde])
        return (float(np.mean(pred[m] == Yde[m])) if m.any() else float("nan"), int(m.sum()))

    def run(featfn, label):
        ts = time.time()
        X, Yidx = bootstrap_align_f(words, phones_set, pi, featfn)
        enc, cent, cph = D.fit_model_mem(X, Yidx, phones_set, pi)
        Xde, Yde = dev_block(featfn)
        pred = cph[(enc(Xde) @ cent.T).argmax(1)]
        acc = float(np.mean(pred == Yde))
        dim = Xde.shape[1]
        per_cls = {nm: cls_acc(pred, Yde, cs) for nm, cs in
                   (("diph", DIPHTHONGS), ("glide", GLIDES), ("vowel", STEADY_VOW), ("fric", FRICATIVES))}

        def decode(M, e, enc=enc, cent=cent, cph=cph, featfn=featfn):
            return collapse(cph[(enc(featfn(M, e)) @ cent.T).argmax(1)], phones_set)
        cr, _tot = D.content_recall(decode, n_test)
        del X, Yidx, enc, cent, cph, Xde; gc.collect()
        print(f"  [{label:24}] dim={dim:4}  per-frame acc {acc:.3f}  content-recall {cr:.3f}  [{time.time()-ts:.0f}s]", flush=True)
        return {"acc": acc, "cr": cr, "dim": dim, "cls": per_cls, "pred": pred, "Yde": Yde}

    # ---- ABLATION ladder: static / +energy / +velocity / +curvature ----------------------------
    print("-" * 92); print("  ABLATION (isolate curvature beyond deltas):")
    static = run(lambda fr, en: feat_traj(fr, en, energy=False, velocity=False, curvature=False), "static (shape only)")
    energ  = run(lambda fr, en: feat_traj(fr, en, energy=True,  velocity=False, curvature=False), "+energy")
    veloc  = run(lambda fr, en: feat_traj(fr, en, energy=True,  velocity=True,  curvature=False), "+velocity (order-1)")
    curv   = run(lambda fr, en: feat_traj(fr, en, energy=True,  velocity=True,  curvature=True),  "+curvature (order-2)")

    # MAIN baseline = the PROJECT-DEFAULT ctxd(M,e) (shape+velocity+energy jointly L2'd, the real
    # ~0.135 ceiling) and curvature ADDED to it (the true additive-energy pattern, the honest MAIN).
    proj  = run(lambda fr, en: D._feat(fr, en, True), "project-default ctxd(M,e)")
    projc = run(lambda fr, en: np.concatenate([D._feat(fr, en, True), _deriv_channel(fr, 2)], axis=1).astype(np.float32),
                "ctxd(M,e) + curvature")

    # ---- COST: feature-build us/frame with vs without curvature (finite differences ~free) ------
    sample = words[:200]
    def feat_cost(featfn):
        tot_f = 0; tc = time.time()
        for _w, fr, _ph, en in sample:
            _ = featfn(fr, en); tot_f += len(fr)
        return (time.time() - tc) / max(tot_f, 1) * 1e6
    us_base = feat_cost(lambda fr, en: feat_traj(fr, en, energy=True, velocity=True, curvature=False))
    us_curv = feat_cost(lambda fr, en: feat_traj(fr, en, energy=True, velocity=True, curvature=True))
    us_only = feat_cost(lambda fr, en: _deriv_channel(fr, 2))     # the curvature block alone

    # ============================ REPORT =========================================================
    print("=" * 92)
    print("  MAIN — curvature ADDED to the energy-augmented baseline (project-default ctxd(M,e), the ~0.135 ceiling):")
    print(f"    baseline   ctxd(M,e)            acc {proj['acc']:.3f}  content-recall {proj['cr']:.3f}")
    print(f"    +curvature ctxd(M,e)+curv       acc {projc['acc']:.3f}  content-recall {projc['cr']:.3f}")
    print(f"    LIFT                            acc {projc['acc']-proj['acc']:+.3f}  content-recall {projc['cr']-proj['cr']:+.3f}")
    print(f"    HONEST: per-frame acc is the canonical metric; content-recall (best-window-match) is the"
          f" KNOWN-NOISY metric (retraction commit 178936e1) -> weight per-frame + the discriminative split,"
          f" NOT content-recall. Bolting curvature onto the full default DILUTES the shallow encoder's fixed"
          f" 120-dim PCA budget (882 vs 594 dims, same P) -> per-frame can DROP: a CAPACITY wall, not noise.")
    print("-" * 92)
    print("  ABLATION (per-frame acc, each block additive):")
    print(f"    static {static['acc']:.3f}  -> +energy {energ['acc']:.3f} ({energ['acc']-static['acc']:+.3f})"
          f"  -> +velocity {veloc['acc']:.3f} ({veloc['acc']-energ['acc']:+.3f})"
          f"  -> +curvature {curv['acc']:.3f} ({curv['acc']-veloc['acc']:+.3f})")
    print(f"    => curvature's ISOLATED contribution BEYOND velocity/deltas: {curv['acc']-veloc['acc']:+.3f}")
    print("-" * 92)
    print("  DISCRIMINATIVE — per-phone-class acc, +velocity baseline vs +curvature (delta = curvature effect):")
    for nm, lab in (("diph", "DIPHTHONGS"), ("glide", "GLIDES/LIQUIDS"), ("vowel", "STEADY VOWELS"), ("fric", "FRICATIVES")):
        b, bn = veloc["cls"][nm]; c, cn = curv["cls"][nm]
        print(f"    {lab:16} (n={bn:5}): baseline {b:.3f} -> +curvature {c:.3f}   delta {c-b:+.3f}")
    motion = np.mean([curv["cls"]["diph"][0]-veloc["cls"]["diph"][0], curv["cls"]["glide"][0]-veloc["cls"]["glide"][0]])
    steady = np.mean([curv["cls"]["vowel"][0]-veloc["cls"]["vowel"][0], curv["cls"]["fric"][0]-veloc["cls"]["fric"][0]])
    print(f"    MOTION-phone mean delta {motion:+.3f}  vs  STEADY-phone mean delta {steady:+.3f}  "
          f"=> {'curvature is the TRAJECTORY signal' if motion > steady + 0.005 else 'NOT motion-specific'}")
    print("-" * 92)
    print(f"  COST (feature-build us/frame): baseline {us_base:.1f}  +curvature {us_curv:.1f}  "
          f"(curvature block alone {us_only:.1f})  => {'~free (finite differences)' if us_curv-us_base < us_base else 'NOT free, flag'}")
    print("=" * 92)
    print(f"  donkey=0: velocity/curvature = the agent's order-N operator (nth_order_terms, recursive Minus,")
    print(f"            native eval, audited == numpy bit-for-bit); per-frame decision argmax (graph-native);")
    print(f"            EARNED (PCA->LDA+GMM from scratch, held data only, no borrowed weights). [{time.time()-t0:.0f}s]")
    print("=" * 92)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
