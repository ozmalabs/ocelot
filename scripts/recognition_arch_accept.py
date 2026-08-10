"""Acceptance test for the agent's two-stage recognition architecture.

Held-out speaker (jackson), 10-way FSDD, speaker-INDEPENDENT (Stage-1 centroids
and Stage-2 cue means are fit on NON-jackson speakers only; jackson is the test
set). Honest: reports the real numbers — Stage-1 global-only vs the full
two-stage (global + the agent's contextual tie-breaks) vs the 61% both-ears-kNN
baseline, with per-confused-pair fixes and a confusion delta. No tuning to force a
win; if the pairwise stage doesn't help, the numbers say so.

The agent DESIGNS Stage 2 from its own state: it develops (accumulating Confusion
nodes), grounds a discriminating cue per confused pair (cue_assessment), then
recognition_architecture reads its Confusions × grounded cues to decide which pairs
get a contextual tie-break and which cue. We measure; we do not choose for it.
"""
from __future__ import annotations

import os
import random
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

import scripts.ask_agent as ask
import scripts.fsdd_learner_world as fl
from domains.acoustic_resolution import (enrich_sign_bands, enrich_sign_windows,
                                         enrich_sign_fft, get_resolution)
from domains.cue_assessment import agent_assess_cues
from domains.recognition_architecture import (
    learn_word_centroids, agent_design_tiebreaks, stage2_decide,
    stage1_rank, _attach_clip, tiebreak_term)

WORDS = list(fl._DIGITS)


def _norm(v):
    n = float(np.linalg.norm(v))
    return v / n if n > 0 else v


def _clip_perception(sub, pipe, samples, res):
    """Ingest one clip; return (gammatone_centroid_vec, fft_centroid_vec, signs).
    Both ears, mean over the clip's signs (the same both-ears summary the 61% kNN
    baseline uses). Signs are enriched (bands/windows/fft) so cue predicates run."""
    pipe.ingest(sub, samples)
    sub.tick(50000)
    st = None
    for n in sub.nodes("AudioStream"):
        st = n
    signs = fl._collect_signs_from_stream(sub, st) if st else []
    if not signs:
        return None, None, []
    enrich_sign_bands(sub, resolution=res, signs=signs)
    enrich_sign_windows(sub, resolution=res, signs=signs)
    enrich_sign_fft(sub, signs=signs)
    g, f = [], []
    for s in signs:
        a = sub.node(s)["attrs"]
        t, ft = a.get("trajectory"), a.get("fft_trajectory")
        if t:
            g.append(np.array(t, dtype=float))
        if ft:
            f.append(np.array(ft, dtype=float))
    if not g:
        return None, None, signs
    gv = _norm(np.mean(g, axis=0))
    fv = _norm(np.mean(f, axis=0)) if f else np.zeros(1024)
    return gv, fv, signs


def main():
    random.seed(7)
    # 1) develop the agent so it accumulates Confusions (its self-built state).
    print("developing the agent (accumulating its confusions)...", flush=True)
    sub, pipe, dev_test, vc, rec = ask._develop(cycles=8)
    res = get_resolution(sub)
    print(f"  developed: resolution={res}, "
          f"{len(sub.nodes('Confusion'))} confusion nodes, "
          f"dev recognition {rec['correct']}/{rec['total']}")

    # 2) the agent grounds a discriminating cue per confused pair (its own cues).
    grounded = agent_assess_cues(sub, pipe, dev_test, res, fisher_floor=0.6)
    print(f"  agent grounded {len(grounded)} contextual cues from its confusions:")
    for X, Y, cue, fish, base in grounded:
        print(f"    {X}/{Y:<7} -> {cue:<12} (fisher {fish:.2f} vs whole-word {base:.2f})")

    # 3) gather both-ears perception for ALL files, split by speaker.
    print("gathering both-ears perception (held-out = jackson)...", flush=True)
    af = fl.gather_files(limit=None)
    train, test = [], []          # (word, gam_vec, fft_vec, [signs])
    train_signs = []              # (word, sign) for Stage-2 cue means
    for path, digit, sp, idx in af:
        s, fs = fl.load_wav(path)
        gv, fv, signs = _clip_perception(sub, pipe, s, res)
        if gv is None:
            continue
        w = fl._DIGITS[digit]
        if sp == "jackson":
            test.append((w, gv, fv, signs))
        else:
            train.append((w, gv, fv))
            for sg in signs:
                train_signs.append((w, sg))

    # 4) Stage 1: the agent fits both-ears centroids on the training speakers.
    arch = learn_word_centroids(
        sub, [(w, g, f) for (w, g, f) in train], WORDS)

    # 5) Stage 2: the agent designs its contextual tie-breaks from its own state.
    specs = agent_design_tiebreaks(sub, train_signs, res)
    tb_index = {}
    for sp_ in specs:
        tb_index[(sp_["A"], sp_["B"])] = sp_
    print(f"\nthe agent chose {len(specs)} pairs to tie-break (from its Confusions "
          f"x grounded cues):")
    for sp_ in specs:
        print(f"    {sp_['A']}/{sp_['B']:<7} via {sp_['cue']:<12} "
              f"(a_mean {sp_['a_cue_mean']:.3f}  b_mean {sp_['b_cue_mean']:.3f}  "
              f"fisher {sp_['fisher']:.2f})")

    # 6) evaluate a 4-row ablation on the held-out speaker. First pass: cache each
    #    clip's Stage-1 ranking + confidence margin (so the margin cut is data-driven).
    from domains.recognition_architecture import _exemplars, stage1_rank as s1rank
    exemplars = _exemplars(sub, arch)
    rows = []     # (w, signs, ranked, margin)
    for w, gv, fv, signs in test:
        clip = _attach_clip(sub, arch, gv, fv)
        ranked, margin = s1rank(sub, arch, clip, WORDS, exemplars=exemplars,
                                with_margin=True)
        rows.append((w, signs, ranked, margin))

    n = len(rows)
    # lever 1: the gating cut = bottom TERTILE of the Stage-1 margin distribution.
    # Stage 2 may only override when the clip's margin is in this low-confidence band
    # (data-driven, no magic constant).
    margins = sorted(r[3] for r in rows)
    margin_cut = margins[max(0, len(margins) // 3 - 1)]    # ~33rd percentile
    n_low = sum(1 for r in rows if r[3] <= margin_cut)

    def _decide(ranked, signs, *, gate: bool, relative: bool, margin: float):
        """One ablation cell's decision for a clip. `gate`: only override low-margin
        Stage-1. `relative`: speaker-relative cue (lever 2)."""
        top1 = ranked[0]
        if gate and margin > margin_cut:
            return top1                                  # confident — trust Stage 1
        return stage2_decide(sub, (ranked[0], ranked[1]), signs, tb_index,
                             relative=relative)

    # the four conditions + accounting. Per-pair fixed/broke is tracked for the FULL
    # fix (gating + speaker-relative) — the deliverable architecture.
    targeted = {frozenset((s["A"], s["B"])): s for s in specs}
    cells = {"s1": 0, "old": 0, "gate": 0, "full": 0}
    s1_conf = Counter()
    full_conf = Counter()
    pair_fix = {k: {"s1_wrong_fixed": 0, "s1_right_broken": 0, "n": 0,
                    "changed": 0} for k in targeted}
    for w, signs, ranked, margin in rows:
        top1 = ranked[0]
        old = _decide(ranked, signs, gate=False, relative=False, margin=margin)
        gate = _decide(ranked, signs, gate=True, relative=False, margin=margin)
        full = _decide(ranked, signs, gate=True, relative=True, margin=margin)
        cells["s1"] += (top1 == w)
        cells["old"] += (old == w)
        cells["gate"] += (gate == w)
        cells["full"] += (full == w)
        s1_conf[(w, top1)] += 1
        full_conf[(w, full)] += 1
        key = frozenset((ranked[0], ranked[1]))
        if key in targeted and (margin <= margin_cut):    # the full fix can fire here
            pair_fix[key]["n"] += 1
            if top1 != full:
                pair_fix[key]["changed"] += 1
                if top1 != w and full == w:
                    pair_fix[key]["s1_wrong_fixed"] += 1
                elif top1 == w and full != w:
                    pair_fix[key]["s1_right_broken"] += 1

    s2_conf = full_conf      # confusion-delta block below reports the full fix
    print(f"\n================  ACCEPTANCE (held-out jackson, 10-way, "
          f"chance 10%, n={n})  ================")
    print(f"  lever-1 gating: margin cut = {margin_cut:.4f} (bottom tertile); "
          f"{n_low}/{n} clips eligible for a tie-break\n")
    print(f"  {'condition':<42}  accuracy")
    print(f"  {'-'*42}  --------")
    print(f"  {'1) Stage-1 global only (both ears)':<42}  "
          f"{100*cells['s1']/n:5.1f}%  ({cells['s1']}/{n})")
    print(f"  {'2) OLD absolute 2-stage (always fire)':<42}  "
          f"{100*cells['old']/n:5.1f}%  ({cells['old']}/{n})")
    print(f"  {'3) gating ONLY (absolute cue, low-margin)':<42}  "
          f"{100*cells['gate']/n:5.1f}%  ({cells['gate']}/{n})")
    print(f"  {'4) gating + speaker-relative (FULL FIX)':<42}  "
          f"{100*cells['full']/n:5.1f}%  ({cells['full']}/{n})")
    print(f"  {'-'*42}")
    print(f"  {'both-ears-kNN baseline (verified)':<42}    61.0%  (reference)")
    print(f"\n  full-fix delta vs Stage-1: {cells['full']-cells['s1']:+d} clips "
          f"({100*(cells['full']-cells['s1'])/n:+.1f} pts)")

    print(f"\n  per-pair effect of the FULL FIX (gating + speaker-relative; fires "
          f"only when Stage-1 top-2 = the pair AND low-confidence):")
    if not pair_fix:
        print("    (no pairs targeted)")
    for key, st in pair_fix.items():
        a, b = tuple(key)
        print(f"    {a}/{b:<7}: fired on {st['n']:>2} clips  | "
              f"changed {st['changed']:>2}  | fixed {st['s1_wrong_fixed']}  "
              f"broke {st['s1_right_broken']}")

    # confusion delta on the targeted pairs (both directions).
    print(f"\n  confusion-cell delta on targeted pairs (Stage1 -> 2-stage; "
          f"negative = fewer confusions = better):")
    for key in targeted:
        a, b = tuple(key)
        for (x, y) in ((a, b), (b, a)):
            d = s2_conf[(x, y)] - s1_conf[(x, y)]
            if s1_conf[(x, y)] or s2_conf[(x, y)]:
                print(f"    heard '{x}' as '{y}': {s1_conf[(x,y)]} -> "
                      f"{s2_conf[(x,y)]}  ({d:+d})")

    # cue-transfer diagnostic: does the cue keep discriminative SHAPE on the
    # held-out speaker, and does the TRAINING threshold still sit between the
    # held-out per-word means? (Speaker shift can keep the shape but move the
    # absolute boundary — the heart of why an absolute-threshold tie-break hurts.)
    from domains.recognition_architecture import _T
    print(f"\n  cue transfer to held-out jackson "
          f"(shape kept? training threshold still valid?):")
    for sp_ in specs:
        A_, B_, pred = sp_["A"], sp_["B"], sp_["predicate"]
        va, vb = [], []
        for w, gv, fv, signs in test:
            if not signs:
                continue
            vs = []
            for s in signs:
                try:
                    vs.append(float(sub.evaluate(_T(pred), {"s": s})))
                except Exception:
                    pass
            if not vs:
                continue
            (va if w == A_ else vb if w == B_ else []).append(np.mean(vs))
        if not va or not vb:
            continue
        ja, jb = float(np.mean(va)), float(np.mean(vb))
        thr = (sp_["a_cue_mean"] + sp_["b_cue_mean"]) / 2.0
        order_kept = (sp_["a_cue_mean"] >= sp_["b_cue_mean"]) == (ja >= jb)
        thr_valid = min(ja, jb) <= thr <= max(ja, jb)
        print(f"    {A_}/{B_:<7} {sp_['cue']:<12}: jackson A={ja:+.3f} B={jb:+.3f} "
              f"thr={thr:+.3f}  shape {'KEPT' if order_kept else 'LOST'}, "
              f"threshold {'valid' if thr_valid else 'MIS-CALIBRATED'}")

    s1_ok, s2_ok = cells["s1"], cells["full"]
    print(f"\n  VERDICT (full fix = gating + speaker-relative): ", end="")
    if s2_ok > s1_ok and s2_ok / n > 0.61:
        print("full fix BEATS both Stage-1-only AND the 61% baseline.")
    elif s2_ok > s1_ok:
        print(f"full fix beats Stage-1-only ({100*s2_ok/n:.1f}% > "
              f"{100*s1_ok/n:.1f}%) but {'beats' if s2_ok/n>0.61 else 'does NOT beat'}"
              f" the 61% baseline.")
    elif s2_ok == s1_ok:
        print("full fix is NEUTRAL vs Stage-1 (gating suppressed all flips, or "
              "they cancel) — Stage 1 carries it.")
    else:
        print("full fix still HURTS vs Stage-1 — speaker-relative + gating did not "
              "recover it (see per-condition table + per-pair).")
    print(f"  lever attribution: gating-only {100*cells['gate']/n:.1f}% vs "
          f"old-absolute {100*cells['old']/n:.1f}% (gating recovers "
          f"{cells['gate']-cells['old']:+d}); "
          f"speaker-relative adds {cells['full']-cells['gate']:+d} on top.")


if __name__ == "__main__":
    main()
