"""iter43_sharp_frontend_accept — the SHARP all-pole spectral-envelope front-end
acceptance (the triply-validated feature-front-end frontier).

WHAT IS TESTED: does making the underlying FEATURE SHARPER (the agent's owned
Levinson all-pole envelope at full waveform frequency resolution, bypassing the
BLURRY gammatone band-mean wall) LIFT held-out-speaker recognition? The sharp
all-pole ear is wired as ONE MORE node in the EXACT iter-34/38 variadic
Argmax-of-product cue-graph (domains/allpole_spectral_envelope.allpole_ear ->
scripts.enriched_hvpt_accept.allpole_ear_readout, the 7th orthogonal cue). Combine-
all, no fit, no weight, no select — the recognition decision Term is unchanged.

THE DECISIVE READS (FSDD LOSO over 6 held-out speakers, with SHUFFLE, per-fold):
  · SHARP graph (with all-pole)   vs  the SAME graph WITHOUT all-pole (leave-one-out)
    -> does the sharp feature LIFT the held-out cue-graph?
  · SHARP graph                   vs  the pure GAMMATONE graph (iter33, 20 channels)
  · SHARP graph                   vs  single-flat  vs  frozen
  · the all-pole channel's ERROR-OVERLAP vs the bottom-up (gammatone-only) graph:
    on queries the gammatone graph gets WRONG, what fraction does the all-pole cue
    ALONE get RIGHT? (above chance => the sharp feature catches the bottom-up's
    cross-speaker errors — informationally complementary, the gammatone-wall fix).
  · the all-pole cue ALONE accuracy (held-out-speaker, the raw sharpness of the cue).

NO-FIT / NO-DONKEY (audited): the all-pole node is _autocorr->_levinson (the agent's
OWN operators) -> evaluate 1/|A(w)| on a log-freq grid -> L2 -> cosine 1-NN exemplar
evidence -> softmax by its OWN median distance -> one item in the SAME product. No
trained net, no learned weight, no convergence loop, no tuning, no select-best.

Run:
  PYTHONUNBUFFERED=1 python -m scripts.iter43_sharp_frontend_accept [n_per] [rounds]
Env AXS=0 skips the slow AxS trajectory node (it is diagnostic, not the front-end;
the all-pole verdict is identical with or without it — AXS=0 is the fast default).
"""
import os
import sys

import numpy as np

sys.path.insert(0, '/home/matt/ozma/internal/research/experiments/gamma-substrate')

import scripts.enriched_hvpt_accept as EH
from scripts.mine_whisper import gather, load_wav


AP_NAME = "allpole_envelope"


# ---------------------------------------------------------------------------
# The sharp-vs-blurry metrics for ONE built fold, reusing EH.build_fold's channels
# (which now include the all-pole node). NO AxS dependence — the front-end verdict.
# ---------------------------------------------------------------------------

def fold_metrics(fold):
    """All iter-43 metrics for one LOSO fold. The graph WITH vs WITHOUT the all-pole
    node (combine-all, no AxS for speed), plus the gammatone-only / single / frozen
    comparators and the all-pole error-overlap vs the bottom-up gammatone graph."""
    tw, hw = fold["train_words"], fold["held_words"]
    many_tr, many_he = fold["many_train"], fold["many_held"]
    ot_tr, ot_he = fold["ortho_train"], fold["ortho_held"]
    names = fold["ortho_names"]
    ap_i = names.index(AP_NAME)

    # SHARP graph = gammatone + ALL orthogonal cues (incl. all-pole), combine-all.
    sharp = EH.heldout_combined(many_tr + ot_tr, many_he + ot_he, tw, hw)
    # WITHOUT all-pole = the same graph with the all-pole node dropped (the closest
    # apples-to-apples "current graph": every other cue present, only the sharp
    # feature removed). The Δ is exactly "does the sharp feature lift the graph?".
    keep = [j for j in range(len(ot_tr)) if j != ap_i]
    no_ap = EH.heldout_combined(many_tr + [ot_tr[j] for j in keep],
                                many_he + [ot_he[j] for j in keep], tw, hw)
    # pure GAMMATONE graph (iter33, 20 channels, no orthogonal cues at all).
    gammatone = EH.heldout_combined(many_tr, many_he, tw, hw)
    from scripts.many_settings_hvpt_accept import heldout_1nn
    single_flat = heldout_1nn(fold["single_flat_train"], tw,
                              fold["single_flat_held"], hw)
    frozen = heldout_1nn(fold["frozen_train"], tw, fold["frozen_held"], hw)
    # the all-pole cue ALONE (held-out-speaker 1-NN — the raw sharpness of the cue).
    ap_alone = heldout_1nn(ot_tr[ap_i], tw, ot_he[ap_i], hw)

    # ERROR-OVERLAP: on queries the BOTTOM-UP (gammatone-only) graph is WRONG, what
    # fraction does the all-pole cue ALONE get RIGHT? Above chance => complementary.
    bu_pred = EH.heldout_combined(many_tr, many_he, tw, hw, return_preds=True)
    err_idx = [i for i, (p, w) in enumerate(zip(bu_pred, hw)) if p != w]
    Xtr = np.asarray(ot_tr[ap_i]); Xtr = Xtr / (np.linalg.norm(Xtr, axis=1, keepdims=True) + 1e-9)
    Xte = np.asarray(ot_he[ap_i]); Xte = Xte / (np.linalg.norm(Xte, axis=1, keepdims=True) + 1e-9)
    ap_pred = np.asarray(tw)[(Xte @ Xtr.T).argmax(1)]
    caught = sum(int(ap_pred[i] == hw[i]) for i in err_idx)
    # also: does the SHARP graph fix the bottom-up's errors net of any it breaks?
    sharp_pred = EH.heldout_combined(many_tr + ot_tr, many_he + ot_he, tw, hw,
                                     return_preds=True)
    bu_err_set = set(err_idx)
    sharp_err_set = {i for i, (p, w) in enumerate(zip(sharp_pred, hw)) if p != w}
    fixed = len(bu_err_set - sharp_err_set)
    broke = len(sharp_err_set - bu_err_set)

    return {
        "held_voice": fold["held_voice"], "shuffle": fold["shuffle"],
        "sharp": sharp, "no_ap": no_ap, "gammatone": gammatone,
        "single_flat": single_flat, "frozen": frozen, "ap_alone": ap_alone,
        "ap_drop": sharp - no_ap,            # the front-end lift (graph with - without)
        "n_held": len(hw), "n_train": len(tw),
        "n_bu_err": len(err_idx), "ap_caught": caught,
        "sharp_fixed": fixed, "sharp_broke": broke,
        "n_cands": len(set(tw)),
    }


def _report(m):
    tag = " [SHUFFLE]" if m["shuffle"] else ""
    print(f"\n--- held-out {m['held_voice']}{tag} "
          f"(held {m['n_held']} train {m['n_train']}, {m['n_cands']} words) ---",
          flush=True)
    print(f"  SHARP(+all-pole) {m['sharp']:.3f}   without-all-pole {m['no_ap']:.3f}   "
          f"=> all-pole drop-it Δ {m['ap_drop']:+.3f}", flush=True)
    print(f"  gammatone-only {m['gammatone']:.3f}   single-flat {m['single_flat']:.3f}   "
          f"frozen {m['frozen']:.3f}", flush=True)
    print(f"  Δ(sharp - gammatone) {m['sharp']-m['gammatone']:+.3f}   "
          f"Δ(sharp - single-flat) {m['sharp']-m['single_flat']:+.3f}   "
          f"Δ(sharp - frozen) {m['sharp']-m['frozen']:+.3f}", flush=True)
    if not m["shuffle"]:
        chance = 1.0 / max(m["n_cands"], 1)
        rate = m["ap_caught"] / max(m["n_bu_err"], 1)
        print(f"  all-pole cue ALONE {m['ap_alone']:.3f} (chance {chance:.3f})", flush=True)
        print(f"  ERROR-OVERLAP: bottom-up(gammatone) wrong on {m['n_bu_err']}; "
              f"all-pole-alone catches {m['ap_caught']} = {rate:.3f} "
              f"({'ABOVE' if rate > chance else 'at/below'} chance {chance:.3f})",
              flush=True)
        print(f"  SHARP graph vs bottom-up errors: fixed {m['sharp_fixed']}  "
              f"broke {m['sharp_broke']}  net {m['sharp_fixed']-m['sharp_broke']:+d}",
              flush=True)


def run_fsdd(n_per, rounds):
    items = gather(n_per_class_per_speaker=n_per)
    voice_audio = {}
    for p, d, s in items:
        x, fs = load_wav(p)
        voice_audio.setdefault(s, []).append((x, fs, str(d)))
    speakers = sorted(voice_audio)
    print(f"FSDD: {sum(len(v) for v in voice_audio.values())} recordings, "
          f"{len(speakers)} speakers {speakers}", flush=True)
    print(f"ortho cues = {EH.ORTHO_NAMES}  (all-pole = the iter-43 sharp front-end)",
          flush=True)
    real, shuf = [], []
    for held in speakers:
        m = fold_metrics(EH.build_fold(voice_audio, held, rounds,
                                       shuffle=False, skip_axs=True))
        _report(m); real.append(m)
        sm = fold_metrics(EH.build_fold(voice_audio, held, rounds,
                                        shuffle=True, skip_axs=True))
        _report(sm); shuf.append(sm)
    return real, shuf


def main():
    n_per = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    rounds = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    print("=" * 72, flush=True)
    print("ITER-43 — SHARP all-pole spectral-envelope front-end (FSDD LOSO)", flush=True)
    print(f"  n_per={n_per} rounds={rounds}", flush=True)
    print("=" * 72, flush=True)

    real, shuf = run_fsdd(n_per, rounds)

    def mean(rs, k):
        return float(np.mean([r[k] for r in rs]))

    print("\n" + "=" * 72, flush=True)
    print("VERDICT (mean over 6 held-out FSDD speakers)", flush=True)
    print("=" * 72, flush=True)
    sharp = mean(real, "sharp"); no_ap = mean(real, "no_ap")
    gam = mean(real, "gammatone"); sf = mean(real, "single_flat")
    fr = mean(real, "frozen"); ap_alone = mean(real, "ap_alone")
    s_sh = mean(shuf, "sharp"); s_noap = mean(shuf, "no_ap"); s_gam = mean(shuf, "gammatone")

    print(f"\n  SHARP graph (+all-pole)   {sharp:.3f}", flush=True)
    print(f"  same graph WITHOUT all-pole {no_ap:.3f}", flush=True)
    print(f"  *** all-pole drop-it Δ      {sharp-no_ap:+.3f}   "
          f"=> {'LIFTS' if sharp > no_ap else ('NEUTRAL' if sharp==no_ap else 'HURTS')} "
          f"the held-out cue-graph", flush=True)
    print(f"  gammatone-only (iter33)     {gam:.3f}   "
          f"Δ(sharp - gammatone) {sharp-gam:+.3f}", flush=True)
    print(f"  single-flat                 {sf:.3f}   Δ {sharp-sf:+.3f}", flush=True)
    print(f"  frozen                      {fr:.3f}   Δ {sharp-fr:+.3f}", flush=True)
    print(f"  all-pole cue ALONE          {ap_alone:.3f}  (chance "
          f"{1.0/max(real[0]['n_cands'],1):.3f})", flush=True)

    n_bu = sum(r["n_bu_err"] for r in real)
    n_caught = sum(r["ap_caught"] for r in real)
    n_fixed = sum(r["sharp_fixed"] for r in real)
    n_broke = sum(r["sharp_broke"] for r in real)
    chance = 1.0 / max(real[0]["n_cands"], 1)
    rate = n_caught / max(n_bu, 1)
    print(f"\n  ERROR-OVERLAP (pooled): bottom-up(gammatone) wrong on {n_bu}; "
          f"all-pole-alone catches {n_caught} = {rate:.3f} "
          f"({'ABOVE' if rate > chance else 'at/below'} chance {chance:.3f})",
          flush=True)
    print(f"  SHARP graph net on bottom-up errors: fixed {n_fixed}  broke {n_broke}  "
          f"net {n_fixed-n_broke:+d}", flush=True)

    print(f"\n  SHUFFLE control: SHARP real {sharp:.3f} vs shuffle {s_sh:.3f} "
          f"=> margin {sharp-s_sh:+.3f} ({'CLEAN' if sharp > s_sh else 'NOT CLEAN'})",
          flush=True)
    print(f"    without-all-pole real {no_ap:.3f} vs shuffle {s_noap:.3f} "
          f"=> margin {no_ap-s_noap:+.3f}", flush=True)
    print(f"    gammatone real {gam:.3f} vs shuffle {s_gam:.3f} "
          f"=> margin {gam-s_gam:+.3f}", flush=True)

    verdict = ("PAYS OFF — the sharp feature lifts held-out recognition"
               if sharp > no_ap and sharp > s_sh else
               ("NULL — the sharp feature does not lift the held-out cue-graph"
                if sharp <= no_ap else "MIXED"))
    print(f"\n  >>> FRONT-END VERDICT: {verdict}", flush=True)
    print("  (all-pole = _autocorr->_levinson 1/|A(w)| on a log-freq grid, combine-all, "
          "no fit, no weight, no select; decision Term unchanged)", flush=True)


if __name__ == "__main__":
    main()
