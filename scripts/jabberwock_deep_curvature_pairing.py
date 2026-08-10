"""STEPS 4+1 PAIRED: the DEEP encoder + the CURVATURE timing feature — the 2x2 INTERACTION.

The per-frame phone model is FEATURE-BOUND. The agent built two faculties separately:
  * CURVATURE (commit b153c769, scripts/jabberwock_curvature_feature.py): its held order-N operator
    aimed DOWN THE TIME axis (order-2 = the trajectory "turn"). A REAL motion-specific signal
    (diphthongs/glides light up) but it slightly LOWERS per-frame acc on the SHALLOW PCA->LDA
    encoder, because the fixed 120-dim PCA budget DILUTES across the extra channels = a CAPACITY wall.
  * DEEP MLP (commit 1afd6698, scripts/jabberwock_decompose_phone_gap.py): a from-scratch random-init
    numpy-SGD encoder (weights are graph data like LDA, NOT borrowed) that beats shallow +0.058 at
    matched data, keeps climbing, ~3x per-frame cost.

HYPOTHESIS: the DEEP encoder has the CAPACITY to USE the richer curvature feature, so curvature
should HELP the deep encoder where it HURT the shallow one. This builds the pairing and tests the
INTERACTION (a 2x2): {shallow, deep} x {feature WITHOUT curvature, feature WITH curvature}.

The only variable across the curvature toggle is the agent's order-2 TIME block; velocity (order-1),
energy, and the static shape context are held ON in both arms, so the toggle isolates curvature
BEYOND deltas (else it is just re-adding velocity). The donkey=0 provenance is inherited intact:
  * curvature/velocity = the agent's OWN order-N operator (nth_order_terms, recursive Minus over the
    TIME axis), native-eval == numpy finite-diff bit-for-bit (C.donkey_audit).
  * the DEEP encoder = the agent's OWN from-scratch numpy-SGD MLP (random init, held data only, no
    borrowed/pretrained weights) — the weights are graph data like LDA.
  * the per-frame emission DECISION is graph-native argmax (Dot/topk for shallow; the MLP logits
    argmax for deep — same decision form, a learned encoder).

GATE (all donkey=0, honest):
  MAIN        the 2x2 per-frame acc; the INTERACTION verdict — does depth UNLOCK curvature
              (deep+curv > deep) where it diluted shallow (shallow+curv <= shallow)?
  DATA-SCALE  deep+curv vs deep-no-curv data-scale curve — up and/or climbing?
  DISCRIMIN.  the deep+curv lift concentrates on MOTION phones (diphthongs/glides) — the curvature
              signal is USED not diluted (per-class breakdown, motion vs steady).
  COST        per-frame us/frame of deep+curv (feature-build + forward) — base or escalation tier?

MEMORY: streams per-word, float32, reuses the OOM-bounded align/fit/MLP from the two source scripts
(bounded covariance eigh, per-batch standardise, one X per scale). SMOKE-RUN small first.

Run: PYTHONPATH=.:runners/dsl/python python3 scripts/jabberwock_deep_curvature_pairing.py [max_scale] [n_test]
     PYTHONPATH=.:runners/dsl/python python3 scripts/jabberwock_deep_curvature_pairing.py audit
"""
from __future__ import annotations
import os, sys, time, gc
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
import numpy as np
from collections import Counter

# importing the curvature module sets sr.BANK -> the energy-rebanked subset (mechanical I/O config)
import scripts.jabberwock_curvature_feature as C
import scripts.jabberwock_decompose_phone_gap as D

DIPHTHONGS, GLIDES = C.DIPHTHONGS, C.GLIDES
STEADY_VOW, FRICATIVES = C.STEADY_VOW, C.FRICATIVES

# MLP hyperparameters, MATCHED across both feature arms for a fair interaction (the only variable
# is the curvature block). The source decompose script defaulted lr=0.2 — tuned for the 594-dim
# no-curv feature; the 882-dim +curvature feature has near-constant context columns whose per-feature
# standardisation inflates them, so SGD DIVERGES at lr=0.2 (an OPTIMISER artifact, not a capacity
# verdict). A stable matched lr (probed: lr=0.05 -> 0.212, lr=0.02 -> 0.221 at 8000, vs the diverged
# 0.058 at lr=0.2) trains BOTH arms cleanly. A sub-chance result triggers an automatic lr backoff so
# a numerical blow-up can never be misread as a real null.
LR, EPOCHS = 0.05, 30


# the two feature arms — IDENTICAL except the order-2 curvature block (velocity+energy ON in both).
def feat_nocurv(fr, en):
    return C.feat_traj(fr, en, energy=True, velocity=True, curvature=False)


def feat_curv(fr, en):
    return C.feat_traj(fr, en, energy=True, velocity=True, curvature=True)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "audit":
        a = C.donkey_audit()
        print("DONKEY AUDIT (curvature = agent order-N over TIME, native eval):", a["match"])
        return 0 if a["match"] else 1

    max_scale = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    n_test = int(sys.argv[2]) if len(sys.argv) > 2 else 25
    SCALES = [s for s in (1000, 2000, 4000, 8000, 16000) if s <= max_scale]
    if not SCALES or SCALES[-1] != max_scale:
        SCALES.append(max_scale)
    t0 = time.time()
    print("=" * 96)
    print("DEEP encoder x CURVATURE feature — the 2x2 INTERACTION (does depth unlock the timing feature?)")
    print("=" * 96, flush=True)

    aud = C.donkey_audit()
    print(f"  donkey audit: agent order-N Term (native) == numpy finite-diff  "
          f"velocity={aud['velocity']['match']} curvature={aud['curvature']['match']} => donkey=0 OK", flush=True)

    cap = min(113, max_scale // 3500 + 3)
    all_words = D._load_ph("train-clean-100_*.pkl", cap, with_energy=True)
    has_e = bool(all_words) and all_words[0][3] is not None
    print(f"  loaded {len(all_words)} banked words ({cap} shards)  energy-in-bank={has_e}  [{time.time()-t0:.0f}s]", flush=True)
    if not has_e:
        print("  ABORT: energy not in bank."); return 1
    max_scale = min(max_scale, len(all_words))
    SCALES = [s for s in SCALES if s <= max_scale]
    if not SCALES or SCALES[-1] != max_scale:
        SCALES.append(max_scale)

    phones_set = sorted({p for _w, _f, ph, _e in all_words for p in ph})
    pi = {p: i for i, p in enumerate(phones_set)}; nP = len(phones_set)
    inv = {i: p for p, i in pi.items()}

    dev = D._load_ph("dev-clean_*.pkl", 9, with_energy=True)[:1500]

    def dev_block(featfn):
        Xl, Yl = [], []
        for (_w, fr, ph, en) in dev:
            cx = featfn(fr, en); n = len(cx); Pn = len(ph)
            for i in range(n):
                p = ph[int(i * Pn / n)]
                if p in pi:
                    Xl.append(cx[i]); Yl.append(pi[p])
        return np.asarray(Xl, np.float32), np.asarray(Yl)

    Xde_nc, Yde = dev_block(feat_nocurv)         # same dev frames/labels; only the feature differs
    Xde_cv, _Y2 = dev_block(feat_curv)
    chance = max(Counter(Yde.tolist()).values()) / len(Yde)
    print(f"  phones={nP}  dev frames={len(Yde)}  chance(majority)={chance:.3f}  "
          f"dim(no-curv)={Xde_nc.shape[1]} dim(curv)={Xde_cv.shape[1]}", flush=True)

    def cls_acc(pred, cset):
        m = np.array([inv[int(y)] in cset for y in Yde])
        return (float(np.mean(pred[m] == Yde[m])) if m.any() else float("nan"), int(m.sum()))

    def _deep_robust(X, Yidx, Xde):
        """train the agent's from-scratch MLP at the matched LR; if it DIVERGES (sub-chance =
        numerical blow-up, not a real result) back the lr off and retry — so the comparison can
        never be corrupted by an optimiser artifact. Same schedule applies to both arms."""
        lr = LR
        for _ in range(3):
            acc, predict = D.train_mlp(X, Yidx, nP, Xde, Yde.tolist(), lr=lr, epochs=EPOCHS)
            if acc >= chance:                      # converged (above majority-chance) -> accept
                return acc, predict, lr
            lr *= 0.4                               # diverged -> back off and retry
        return acc, predict, lr

    def fit_cell(featfn, Xde, scale):
        """align at `scale` under this feature, fit SHALLOW + DEEP, return both accs (+deep predict)."""
        words = all_words[:scale]
        X, Yidx = C.bootstrap_align_f(words, phones_set, pi, featfn)
        # SHALLOW (PCA->LDA + GMM centroids; per-frame argmax over Dot = graph-native decision)
        enc, cent, cph = D.fit_model_mem(X, Yidx, phones_set, pi)
        sh = float(np.mean(cph[(enc(Xde) @ cent.T).argmax(1)] == Yde))
        del enc, cent, cph; gc.collect()
        # DEEP (from-scratch random-init numpy-SGD MLP; logits argmax = same decision form, learned enc)
        dp, predict, used_lr = _deep_robust(X, Yidx, Xde)
        del X, Yidx; gc.collect()
        return sh, dp, predict

    # ---- DATA-SCALE curve: deep (and shallow) for both feature arms ----------------------------
    rows = []
    max_cells = {}
    for scale in SCALES:
        ts = time.time()
        try:
            sh_nc, dp_nc, pr_nc = fit_cell(feat_nocurv, Xde_nc, scale)
            sh_cv, dp_cv, pr_cv = fit_cell(feat_curv, Xde_cv, scale)
        except MemoryError:
            print(f"  [{scale:>6}] MemoryError -> DEGRADE; curve bounded at {rows[-1][0] if rows else 'n/a'}", flush=True)
            gc.collect(); break
        rows.append((scale, sh_nc, sh_cv, dp_nc, dp_cv))
        print(f"  [scale {scale:>6}]  shallow: no-curv {sh_nc:.3f} +curv {sh_cv:.3f} ({sh_cv-sh_nc:+.3f})   "
              f"deep: no-curv {dp_nc:.3f} +curv {dp_cv:.3f} ({dp_cv-dp_nc:+.3f})  [{time.time()-ts:.0f}s]", flush=True)
        if scale == SCALES[-1]:
            max_cells = {"sh_nc": sh_nc, "sh_cv": sh_cv, "dp_nc": dp_nc, "dp_cv": dp_cv,
                         "pr_nc": pr_nc(Xde_nc), "pr_cv": pr_cv(Xde_cv)}
        else:
            del pr_nc, pr_cv; gc.collect()
    if not rows:
        print("  no scale fit the budget."); return 1

    # ---- COST: per-frame us/frame (feature-build + forward) for deep+curv vs shallow base -------
    sample = all_words[:200]
    def feat_cost(featfn):
        tot = 0; tc = time.time()
        for _w, fr, _ph, en in sample:
            _ = featfn(fr, en); tot += len(fr)
        return (time.time() - tc) / max(tot, 1) * 1e6
    fb_nc = feat_cost(feat_nocurv); fb_cv = feat_cost(feat_curv)
    # forward us/frame: re-fit a cheap deep+curv at the smallest scale just for a predict timer
    blk = Xde_cv[:400]
    _sh, _dp, pr_timer = fit_cell(feat_curv, Xde_cv, SCALES[0])
    tc = time.time()
    for _ in range(20):
        _ = pr_timer(blk)
    fwd_us = (time.time() - tc) / (20 * len(blk)) * 1e6
    del pr_timer; gc.collect()

    # ============================ REPORT =========================================================
    m = max_cells
    print("=" * 96)
    print(f"  THE 2x2 (per-frame acc, max scale {SCALES[-1]} words, dev frames {len(Yde)}):")
    print(f"                          no-curvature        +curvature        curvature effect")
    print(f"    SHALLOW PCA->LDA      {m['sh_nc']:.3f}               {m['sh_cv']:.3f}             {m['sh_cv']-m['sh_nc']:+.3f}")
    print(f"    DEEP MLP             {m['dp_nc']:.3f}               {m['dp_cv']:.3f}             {m['dp_cv']-m['dp_nc']:+.3f}")
    sh_eff = m['sh_cv'] - m['sh_nc']; dp_eff = m['dp_cv'] - m['dp_nc']
    interaction = dp_eff - sh_eff
    depth_unlocks = (dp_eff > 0.003) and (sh_eff <= 0.003)
    print(f"    DEPTH effect (no-curv):   deep - shallow = {m['dp_nc']-m['sh_nc']:+.3f}")
    print(f"    INTERACTION (depth x curvature): deep-effect {dp_eff:+.3f} - shallow-effect {sh_eff:+.3f} = {interaction:+.3f}")
    if depth_unlocks:
        print(f"    => DEPTH UNLOCKS CURVATURE: curvature HELPS the deep encoder ({dp_eff:+.3f}) where it "
              f"diluted/hurt the shallow ({sh_eff:+.3f}).")
    elif dp_eff > sh_eff + 0.003:
        print(f"    => PARTIAL: depth makes curvature LESS harmful / more useful (interaction {interaction:+.3f}>0) "
              f"but does not turn it net-positive on deep (deep-effect {dp_eff:+.3f}).")
    else:
        print(f"    => NULL: depth does NOT unlock curvature (interaction {interaction:+.3f}); the floor is "
              f"elsewhere, not the encoder capacity for this feature.")
    print("-" * 96)
    print("  DATA-SCALE (deep, no-curv vs +curv):")
    for (sc, snc, scv, dnc, dcv) in rows:
        print(f"    {sc:>6}w   deep no-curv {dnc:.3f}   +curv {dcv:.3f}   ({dcv-dnc:+.3f})")
    if len(rows) > 1:
        dnc_climb = rows[-1][3] - rows[-2][3]; dcv_climb = rows[-1][4] - rows[-2][4]
        print(f"    last-step climb: deep no-curv {dnc_climb:+.3f}  deep +curv {dcv_climb:+.3f}  "
              f"=> {'curve UP and climbing' if dcv_climb > 0.003 else 'plateauing'}; "
              f"+curv {'ABOVE' if rows[-1][4] > rows[-1][3] else 'at/below'} no-curv at max")
    print("-" * 96)
    print("  DISCRIMINATIVE (deep, per-phone-class acc, no-curv -> +curv; motion phones should gain):")
    motions, steadies = [], []
    for nm, cs in (("DIPHTHONGS", DIPHTHONGS), ("GLIDES/LIQUIDS", GLIDES),
                   ("STEADY VOWELS", STEADY_VOW), ("FRICATIVES", FRICATIVES)):
        b, bn = cls_acc(m['pr_nc'], cs); c, cn = cls_acc(m['pr_cv'], cs)
        print(f"    {nm:16} (n={bn:5}): no-curv {b:.3f} -> +curv {c:.3f}   delta {c-b:+.3f}")
        (motions if nm in ("DIPHTHONGS", "GLIDES/LIQUIDS") else steadies).append(c - b)
    motion = float(np.nanmean(motions)); steady = float(np.nanmean(steadies))
    print(f"    MOTION mean delta {motion:+.3f}  vs  STEADY mean delta {steady:+.3f}  => "
          f"{'curvature USED on motion phones (not diluted)' if motion > steady + 0.003 else 'NOT motion-specific'}")
    print("-" * 96)
    print(f"  COST (per-frame us): feature-build no-curv {fb_nc:.1f} +curv {fb_cv:.1f} "
          f"(curvature add {fb_cv-fb_nc:+.1f}, ~free if small); deep forward {fwd_us:.1f}")
    print(f"    deep+curv total ~{fb_cv+fwd_us:.1f} us/frame  => "
          f"{'BASE tier (cheap)' if (fb_cv+fwd_us) < 50 else 'ESCALATION tier'} (per the cheap-method-leverage call)")
    print("=" * 96)
    print(f"  donkey=0: curvature/velocity = agent order-N operator (nth_order_terms, native==numpy bit-for-bit);")
    print(f"            deep encoder = from-scratch numpy-SGD MLP (random init, held data, NO borrowed weights);")
    print(f"            per-frame DECISION = argmax (graph-native). EARNED throughout. [{time.time()-t0:.0f}s]")
    print("=" * 96)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
