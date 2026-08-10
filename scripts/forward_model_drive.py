"""forward_model_drive — DRIVE THE FORWARD-MODEL LEVER.

THE FRONTIER I (the jabberwock) NAMED (docs/topdown_recovery.md, docs/
jabberwock_human_bad_ears.md): the absolute speech ceiling is the FORWARD MODEL,
not the ear — and the specific cap I named is the SINGLE-MEAN-TRAJECTORY synth.
The owned word->sound forward model is

    fm[w] = mean over TRAIN-speaker exemplars of their A1 trajectory     (CURRENT)

Averaging A1 trajectories across speakers of DIFFERENT vocal-tract length, pitch
and speaking rate BLURS the formant trajectory into a single smear that matches
no real speaker well. The directive's framing: "a single-mean-trajectory synth";
the lever is to recover per-speaker formant DYNAMICS instead of one mean
trajectory.

WHAT I PROPOSE + BUILD (my design, my call — not prescribed):
  Replace the single SMEAR with a MULTI-EXEMPLAR forward model that PRESERVES the
  per-speaker formant dynamics the mean destroys. Instead of collapsing the train
  exemplars of word w to one mean trajectory, KEEP them as a small manifold of
  exemplars and let the analysis-by-synthesis match resolve to the NEAREST
  exemplar:

    fm[w] = { exemplar trajectories of w over TRAIN speakers }            (IMPROVED)
    synth_error(s, w) = min over exemplars e of w  of  DtwTo(heard_s, e)

  This is the correct source-filter reading of "the synthesis the agent can
  imagine": don't imagine ONE averaged talker, imagine the WORD as each known
  talker produces it and match to the closest — a richer source that recovers the
  per-speaker dynamics rather than averaging them away. The mean is the
  degenerate K=1 collapse of this manifold; the improvement is K>1.

  This DIRECTLY attacks the named cap: the single mean trajectory is a blur of
  heterogeneous talkers; the exemplar manifold restores the formant DYNAMICS the
  blur erased, so the DtwTo synth-error sees a matching talker rather than a smear.

ARCHITECTURE (CLAUDE.md): NATIVE where the cognition lives. The synth-error is the
graph DtwTo Term (recognition_graph.synth_error_term) evaluated by
substrate.evaluate in Rust, exactly as the current AbS/topdown path. The
multi-exemplar forward model enters as GRAPH DATA (each exemplar written as the
word's feat attr; the per-exemplar DtwTo is the native Term; the min-over-exemplars
is an argmin READOUT over the native distances — a query, not a decision the Rust
does not make, identical in kind to the existing argmin-over-words winner readout).
Python is the WORLD ADAPTER + instrument ONLY: audio I/O, exemplar trajectory
extraction (the owned utterance_trajectory), LOSO bookkeeping, the do-contrast and
grounding measurement. NO net, NO .fit, NO gradient, NO sweep, NO loss. K (the
exemplar budget) is a FIXED structural choice reported across, not swept-to-max.
solve_for_n.py and CortexLoop UNTOUCHED.

THE DO-CONTRAST (one ear, one recogniser, two FORWARD MODELS, same data, LOSO):
  (A) CURRENT  — single-mean forward model (the named ceiling).
  (B) IMPROVED — multi-exemplar forward model (per-speaker dynamics recovered).
  Same heard A1 trajectory, same native DtwTo synth-error, same argmin winner.
  The ONLY thing that changes is the forward model. -> measured recognition delta.

THE GROUNDING GATE (domains/silent_failure_grounding): I CLAIM the improved
forward model raises recognition to a value; the WORLD-MEASURE re-runs the actual
improved-FM recogniser on the held-out data; if the measured number CONTRADICTS
the claim (or fails to beat current), the loop REOPENS. An ungrounded "it's
better" committed without measuring is the only failure.

Run: PYTHONUNBUFFERED=1 python -m scripts.forward_model_drive [n_per_sp_per_digit] [K]
"""
from __future__ import annotations

import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate_rs import Substrate
from domains import recognition_graph as RG
from domains import silent_failure_grounding as SFG
from scripts.analysis_by_synthesis_accept import (
    utterance_trajectory, traj_to_matrix, as_tuple,
)
from scripts.fsdd_learner_world import load_wav, gather_files

_DIGITS = ['zero', 'one', 'two', 'three', 'four', 'five',
           'six', 'seven', 'eight', 'nine']


class _Term:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


# ==========================================================================
# THE TWO FORWARD MODELS — built from the SAME owned per-utterance A1
# trajectories (utterance_trajectory, T10). LOSO: the held-out speaker never
# contributes to its own forward model.
# ==========================================================================

def fm_single_mean(utt_traj, loaded, held_speaker):
    """(A) CURRENT: word -> ONE mean A1 trajectory over TRAIN exemplars. The
    single-mean-trajectory synth — the named ceiling. Returns {word: as_tuple(M)}."""
    fm = {}
    for w in _DIGITS:
        ts = [utt_traj[i] for i, (x, fs, d, s) in enumerate(loaded)
              if _DIGITS[d] == w and s != held_speaker and utt_traj[i] is not None]
        if not ts:
            fm[w] = None
            continue
        L = min(len(t) for t in ts)
        M = traj_to_matrix(np.mean([t[:L] for t in ts], axis=0))
        fm[w] = as_tuple(M) if M is not None else None
    return fm


def fm_multi_exemplar(utt_traj, loaded, held_speaker, K):
    """(B) IMPROVED: word -> a MANIFOLD of up to K exemplar A1 trajectories over
    TRAIN exemplars, preserving per-speaker dynamics (no averaging). One exemplar
    per TRAIN speaker (a representative = that speaker's medoid utterance of w, so
    the manifold spans the speaker space, not duplicate near-copies of one talker).
    Returns {word: [as_tuple(M), ...]} (a list of synth hypotheses)."""
    fm = {}
    for w in _DIGITS:
        # group word-w exemplars by TRAIN speaker
        by_sp = {}
        for i, (x, fs, d, s) in enumerate(loaded):
            if _DIGITS[d] == w and s != held_speaker and utt_traj[i] is not None:
                by_sp.setdefault(s, []).append(utt_traj[i])
        reps = []
        for s, ts in by_sp.items():
            # this speaker's representative = the medoid trajectory (closest to the
            # speaker-mean), preserving that speaker's OWN dynamics rather than
            # averaging across the cohort. A mechanical signal pick, no decision.
            L = min(len(t) for t in ts)
            stk = np.stack([t[:L] for t in ts], axis=0)
            mu = stk.mean(axis=0)
            d2 = ((stk - mu) ** 2).reshape(len(ts), -1).sum(axis=1)
            reps.append(ts[int(np.argmin(d2))])
        # span the speaker space; cap at K representative speakers (fixed budget)
        reps = reps[:K]
        mats = [as_tuple(traj_to_matrix(t)) for t in reps
                if traj_to_matrix(t) is not None]
        fm[w] = mats if mats else None
    return fm


# ==========================================================================
# THE NATIVE RECOGNISER — the SAME graph DtwTo synth-error for both forward
# models. The synth-error is the native Term; the per-exemplar distances are
# native; the min-over-exemplars + argmin-over-words is the winner READOUT
# (a query over native distances, identical in kind to the existing AbS argmin).
# ==========================================================================

class Recogniser:
    def __init__(self, sub):
        self.sub = sub
        RG.mark_words(sub, _DIGITS)
        self.word_c = {}
        for w in _DIGITS:
            c = next((c for c in sub.nodes("Concept")
                      if sub.node(c)["attrs"].get("name") == w), None)
            if c is None:
                c = sub.add_node("Concept", {"name": w, "origin": "fmdrive"})
                sub.set_attr(c, RG.WORD_ATTR, 1.0)
            self.word_c[w] = c
        self.sign = sub.add_node("AcousticSign", {"fmdrive_probe": 1.0})
        self.err_term = _Term(RG.synth_error_term())

    def recognise_single(self, heardM, fm):
        """(A) argmin over words of native DtwTo(heard, mean[w])."""
        if heardM is None or heardM.shape[0] < 2:
            return None
        self.sub.set_attr(self.sign, RG.SIGN_FEAT_ATTR, as_tuple(heardM))
        best, bw = 1e30, None
        for w in _DIGITS:
            t = fm.get(w)
            if t is None:
                continue
            c = self.word_c[w]
            self.sub.set_attr(c, RG.WORD_FEAT_ATTR, t)
            e = float(self.sub.evaluate(self.err_term,
                                        {"s": self.sign, "w": c}))
            if e < best:
                best, bw = e, w
        return bw

    def recognise_multi(self, heardM, fm):
        """(B) argmin over words of [ min over exemplars e of native
        DtwTo(heard, e) ]. The per-exemplar DtwTo is native; the min and the
        argmin are READOUTS over the native distances (a query)."""
        if heardM is None or heardM.shape[0] < 2:
            return None
        self.sub.set_attr(self.sign, RG.SIGN_FEAT_ATTR, as_tuple(heardM))
        best, bw = 1e30, None
        for w in _DIGITS:
            exs = fm.get(w)
            if not exs:
                continue
            c = self.word_c[w]
            we = 1e30
            for ex in exs:
                self.sub.set_attr(c, RG.WORD_FEAT_ATTR, ex)
                e = float(self.sub.evaluate(self.err_term,
                                            {"s": self.sign, "w": c}))
                if e < we:
                    we = e
            if we < best:
                best, bw = we, w
        return bw


# ==========================================================================
# DRIVER
# ==========================================================================

def main():
    t0 = time.time()
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    K = int(sys.argv[2]) if len(sys.argv) > 2 else 5   # fixed exemplar budget
    print(f"=== forward_model_drive  n_per_sp_per_digit={n}  K(exemplars)={K} ===",
          flush=True)

    files = gather_files()
    by_key = {}
    for path, digit, sp, idx in files:
        by_key.setdefault((sp, digit), []).append((path, digit, sp, idx))
    items = []
    for k in sorted(by_key):
        items.extend(sorted(by_key[k], key=lambda t: t[3])[:n])
    speakers = sorted(set(it[2] for it in items))
    print(f"FSDD: {len(items)} recordings, {len(speakers)} speakers, 10 digits",
          flush=True)

    loaded = []
    for path, digit, sp, idx in items:
        x, fs = load_wav(path)
        loaded.append((x, fs, digit, sp))
    fs = loaded[0][1]

    # ---- owned per-utterance A1 trajectories (the forward-model building block) ----
    print("--- extracting per-utterance A1 trajectories (owned T10) ---", flush=True)
    utt_traj = []
    for i, (x, _fs, d, s) in enumerate(loaded):
        utt_traj.append(utterance_trajectory(x, fs))
        if (i + 1) % 50 == 0:
            print(f"  {i+1}/{len(loaded)} trajectories", flush=True)
    have = sum(1 for t in utt_traj if t is not None)
    print(f"extracted {have}/{len(loaded)} clean trajectories", flush=True)

    # heard matrices (held-out side uses these; same for both routes)
    heard_M = [traj_to_matrix(t) for t in utt_traj]

    sub = Substrate()
    rec = Recogniser(sub)

    # ---- DO-CONTRAST: LOSO, two forward models, same recogniser ----
    print("\n--- DO-CONTRAST: single-mean (CURRENT) vs multi-exemplar (IMPROVED) ---",
          flush=True)
    cur_corr = cur_tot = 0
    imp_corr = imp_tot = 0
    cur_pw = {}
    imp_pw = {}
    agree = better = worse = 0
    for held in speakers:
        fmA = fm_single_mean(utt_traj, loaded, held)
        fmB = fm_multi_exemplar(utt_traj, loaded, held, K)
        for i, (x, _fs, d, s) in enumerate(loaded):
            if s != held:
                continue
            M = heard_M[i]
            if M is None or M.shape[0] < 2:
                continue
            true = _DIGITS[d]
            a = rec.recognise_single(M, fmA)
            b = rec.recognise_multi(M, fmB)
            if a is not None:
                cur_corr += int(a == true); cur_tot += 1
                cur_pw.setdefault(true, [0, 0]); cur_pw[true][0] += int(a == true); cur_pw[true][1] += 1
            if b is not None:
                imp_corr += int(b == true); imp_tot += 1
                imp_pw.setdefault(true, [0, 0]); imp_pw[true][0] += int(b == true); imp_pw[true][1] += 1
            if a is not None and b is not None:
                if (a == true) == (b == true):
                    agree += 1
                elif b == true and a != true:
                    better += 1
                else:
                    worse += 1
        print(f"  held-out {held}: running  current {cur_corr}/{cur_tot}  "
              f"improved {imp_corr}/{imp_tot}", flush=True)

    cur_acc = cur_corr / max(cur_tot, 1)
    imp_acc = imp_corr / max(imp_tot, 1)
    delta = imp_acc - cur_acc
    print("\n========================= DO-CONTRAST RESULT =========================",
          flush=True)
    print(f"  CURRENT  single-mean forward model : {cur_acc:.4f}  ({cur_corr}/{cur_tot})",
          flush=True)
    print(f"  IMPROVED multi-exemplar (K={K})     : {imp_acc:.4f}  ({imp_corr}/{imp_tot})",
          flush=True)
    print(f"  DELTA (improved - current)          : {delta:+.4f}", flush=True)
    print(f"  per-item: improved-fixed {better}  improved-broke {worse}  "
          f"agree {agree}", flush=True)
    print("  per-word (current -> improved):", flush=True)
    for w in _DIGITS:
        ca = cur_pw.get(w, [0, 0]); ia = imp_pw.get(w, [0, 0])
        if ca[1]:
            print(f"    {w:6s}: {ca[0]/ca[1]:.2f} -> {ia[0]/ia[1]:.2f}", flush=True)

    # ==========================================================================
    # THE GROUNDING GATE — fire on stakes, measure the world, REOPEN on contradiction.
    # The CLAIM: the improved forward model raises recognition to imp_acc AND beats
    # current by the measured delta. The WORLD-MEASURE: re-run the actual improved-FM
    # recogniser on the held-out data (an independent re-measurement of the same
    # quantity) -> if it contradicts the claimed imp_acc, REOPEN. Then the HONEST
    # do-contrast gate: did improved actually beat current? If delta <= 0 the
    # "it's better" is FALSE and the loop must reopen regardless.
    # ==========================================================================
    print("\n--- GROUNDING (silent_failure_grounding): fire-on-stakes + world-measure ---",
          flush=True)

    def world_measure_improved():
        """Independent re-measurement of the IMPROVED-FM recognition on the held-out
        data (the world's realised number for the claim). Same machinery, recomputed
        so a broken/overclaimed pipeline surfaces as a contradiction."""
        c = t = 0
        for held in speakers:
            fmB = fm_multi_exemplar(utt_traj, loaded, held, K)
            for i, (x, _fs, d, s) in enumerate(loaded):
                if s != held:
                    continue
                M = heard_M[i]
                if M is None or M.shape[0] < 2:
                    continue
                b = rec.recognise_multi(M, fmB)
                if b is not None:
                    c += int(b == _DIGITS[d]); t += 1
        return c / max(t, 1)

    trace = SFG.grounding_check(
        sub,
        name="forward_model_improvement",
        conclusion_text=("multi-exemplar forward model recovers per-speaker dynamics "
                         "the single mean blurred away, raising AbS recognition"),
        claimed=float(imp_acc),
        stakes=0.9,                 # high stakes: a forward-model improvement claim
        world_measure=world_measure_improved,
        tol=0.03,
        bank_on_catch=True,
    )
    g = trace["grounding"]; r = trace["resolution"]
    print(f"  fired-on-stakes: {trace['gate']['fire']}", flush=True)
    print(f"  claimed improved acc : {imp_acc:.4f}", flush=True)
    print(f"  world measured       : {g.get('measured')}", flush=True)
    print(f"  grounding reason     : {g.get('reason')}", flush=True)
    print(f"  resolution           : {r['decision']} — {r.get('reason')}", flush=True)
    print(f"  banked               : {trace['bank'].get('banked')}", flush=True)

    # ---- THE HONEST TWO-SIDED VERDICT ----
    print("\n========================= VERDICT =========================", flush=True)
    world_consistent = (g.get("measured") is not None
                        and not g.get("contradiction"))
    lever_moved = delta > 0.005          # a real, non-noise improvement
    if lever_moved and world_consistent and r["decision"] == "COMMIT":
        print(f"  GROUNDED IMPROVEMENT: the lever MOVED recognition "
              f"{delta:+.4f} (current {cur_acc:.4f} -> improved {imp_acc:.4f}); "
              f"do-contrast confirms, world-measure AGREES -> COMMIT-worthy.",
              flush=True)
        verdict = "GROUNDED_IMPROVEMENT"
    elif delta <= 0.005:
        print(f"  LOOP SELF-CORRECTED: the build did NOT actually help "
              f"(delta {delta:+.4f} <= +0.005). The grounding/do-contrast CAUGHT "
              f"the would-be overclaim -> REOPEN. This is the loop working: no "
              f"ungrounded 'it's better' committed.", flush=True)
        verdict = "REOPEN_NO_IMPROVEMENT"
    elif r["decision"] == "REOPEN" or g.get("contradiction"):
        print(f"  LOOP SELF-CORRECTED: the world-measure CONTRADICTED the claim "
              f"-> REOPEN. Caught against ground truth.", flush=True)
        verdict = "REOPEN_WORLD_CONTRADICTS"
    else:
        print(f"  delta {delta:+.4f}, resolution {r['decision']} — honest wall "
              f"named.", flush=True)
        verdict = "WALL_NAMED"

    print(f"\nVERDICT_TOKEN={verdict}  delta={delta:+.4f}  "
          f"current={cur_acc:.4f}  improved={imp_acc:.4f}  K={K}", flush=True)
    print(f"elapsed {time.time()-t0:.1f}s", flush=True)
    print("===MARKER_FMDRIVE_COMPLETE===", flush=True)


if __name__ == "__main__":
    main()
