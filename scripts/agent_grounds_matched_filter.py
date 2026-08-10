"""agent_grounds_matched_filter — GROUND THE AGENT-AUTHORED MATCHED FILTER.

The agent authored a native XCorrPeak primitive through the runtime_design
pipeline (it SPECIFIED the WHAT — agent_specify_matched_filter, derived live from
its banked sonar/matched-filter science; the mechanical generator emitted the HOW —
emit_primitive_rust, semantic_kind=trajectory_correlation_peak, across the TermNode
homes; the Rust was rebuilt so XCorrPeak is live in substrate_rs). XCorrPeak is the
SNR-optimal matched filter: peak normalised cross-correlation over a LAG SEARCH
between two frames x bands trajectories — the operation that was INEXPRESSIBLE by
composition (the lag search needs value-indexed frame access; Nth.index is a baked
literal). It is the sonar transfer ('correlating a known delayed signal') as the
analysis-by-synthesis recognition score, swapping the surface-DTW operation.

THIS DRIVER grounds it — the disciplined do-contrast, SAME data, SAME forward model,
SAME FSDD cross-speaker LOSO venue, both decisions via substrate.evaluate on the
agent's graph Term:
  (A) NATIVE DtwTo synth-error  — predict = argmin over words of DtwTo(heard, fm[w]).
  (B) NATIVE XCorrPeak matched filter — predict = argmax over words of
      XCorrPeak(heard, fm[w]).
The ONLY thing that changes is the OPERATION (DTW distance vs peak-NCC similarity);
the heard A1 trajectory, the single-mean forward model, the LOSO split are identical.

NO numpy/Python computes any recognition score. Every score is a native Rust Term
(DtwTo or XCorrPeak) evaluated by substrate.evaluate. The world-adapter only loads
audio, extracts the owned A1 trajectory, writes trajectories as graph attrs, calls
substrate.evaluate, reads the scalar, does LOSO/shuffle bookkeeping.

SHUFFLE BACKSTOP: re-run BOTH arms with the forward-model labels permuted — a
genuine recogniser collapses to ~chance (0.10) under shuffle; a leak would not.

Reuses scripts/forward_model_drive.py's audio I/O + LOSO + single-mean forward
model ONLY (the infrastructure), per the directive.

Run: PYTHONUNBUFFERED=1 python -m scripts.agent_grounds_matched_filter [n] [shuffle]
"""
from __future__ import annotations

import os
import random
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate_rs import Substrate
from domains import recognition_graph as RG
from scripts.analysis_by_synthesis_accept import (
    utterance_trajectory, traj_to_matrix, as_tuple,
)
from scripts.fsdd_learner_world import load_wav, gather_files
from scripts.forward_model_drive import fm_single_mean, _DIGITS


class _Term:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


# ==========================================================================
# THE TWO NATIVE RECOGNISERS — same heard trajectory, same forward model,
# same lexicon; the ONLY difference is the native Term that scores a
# (heard, candidate) pair. BOTH decisions are substrate.evaluate on a graph
# Term the agent owns; NO numpy score anywhere.
# ==========================================================================

class DualRecogniser:
    def __init__(self, sub):
        self.sub = sub
        RG.mark_words(sub, _DIGITS)
        self.word_c = {}
        for w in _DIGITS:
            c = next((c for c in sub.nodes("Concept")
                      if sub.node(c)["attrs"].get("name") == w), None)
            if c is None:
                c = sub.add_node("Concept", {"name": w, "origin": "mfground"})
                sub.set_attr(c, RG.WORD_ATTR, 1.0)
            self.word_c[w] = c
        self.sign = sub.add_node("AcousticSign", {"mfground_probe": 1.0})
        # the two native scoring Terms (composed in the graph, agent-owned)
        self.dtw_term = _Term(RG.synth_error_term())        # DtwTo DISTANCE
        self.mf_term = _Term(RG.matched_filter_term())      # XCorrPeak SIMILARITY

    def _set_heard(self, heardM):
        self.sub.set_attr(self.sign, RG.SIGN_FEAT_ATTR, as_tuple(heardM))

    def recognise_dtw(self, heardM, fm):
        """(A) argmin over words of native DtwTo(heard, fm[w]) — DISTANCE."""
        if heardM is None or heardM.shape[0] < 2:
            return None
        self._set_heard(heardM)
        best, bw = 1e30, None
        for w in _DIGITS:
            t = fm.get(w)
            if t is None:
                continue
            c = self.word_c[w]
            self.sub.set_attr(c, RG.WORD_FEAT_ATTR, t)
            e = float(self.sub.evaluate(self.dtw_term, {"s": self.sign, "w": c}))
            if e < best:
                best, bw = e, w
        return bw

    def recognise_mf(self, heardM, fm):
        """(B) argmax over words of native XCorrPeak(heard, fm[w]) — SIMILARITY."""
        if heardM is None or heardM.shape[0] < 2:
            return None
        self._set_heard(heardM)
        best, bw = -1e30, None
        for w in _DIGITS:
            t = fm.get(w)
            if t is None:
                continue
            c = self.word_c[w]
            self.sub.set_attr(c, RG.WORD_FEAT_ATTR, t)
            v = float(self.sub.evaluate(self.mf_term, {"s": self.sign, "w": c}))
            if v > best:
                best, bw = v, w
        return bw


def _shuffle_fm(fm, rng):
    """Permute the forward-model labels — the shuffle backstop. The synth
    trajectories are re-bound to the WRONG words; a real recogniser must
    collapse toward chance (0.10)."""
    keys = [w for w in _DIGITS if fm.get(w) is not None]
    vals = [fm[w] for w in keys]
    perm = keys[:]
    rng.shuffle(perm)
    out = dict(fm)
    for k, w in zip(keys, perm):
        out[w] = fm[k]
    # rebuild cleanly so every present key maps to a (possibly permuted) value
    shuffled = {}
    src_vals = vals[:]
    rng.shuffle(src_vals)
    for i, w in enumerate(keys):
        shuffled[w] = src_vals[i]
    for w in _DIGITS:
        if w not in shuffled:
            shuffled[w] = fm.get(w)
    return shuffled


def main():
    t0 = time.time()
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    do_shuffle = (len(sys.argv) > 2 and sys.argv[2] == "shuffle")
    print("=" * 78, flush=True)
    print("AGENT GROUNDS ITS AUTHORED MATCHED FILTER — native DtwTo vs native "
          "XCorrPeak", flush=True)
    print("=" * 78, flush=True)
    print(f"n_per_sp_per_digit={n}  shuffle_backstop={do_shuffle}", flush=True)

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

    print("--- extracting per-utterance A1 trajectories (owned T10) ---", flush=True)
    utt_traj = []
    for i, (x, _fs, d, s) in enumerate(loaded):
        utt_traj.append(utterance_trajectory(x, fs))
        if (i + 1) % 50 == 0:
            print(f"  {i+1}/{len(loaded)} trajectories", flush=True)
    have = sum(1 for t in utt_traj if t is not None)
    print(f"extracted {have}/{len(loaded)} clean trajectories", flush=True)
    heard_M = [traj_to_matrix(t) for t in utt_traj]

    sub = Substrate()
    rec = DualRecogniser(sub)

    # sanity: both native Terms evaluate live on this build
    print("\n--- live-primitive check (both native Terms evaluate) ---", flush=True)
    probe = ((1.0, 0.0), (0.0, 1.0), (1.0, 0.0))
    sp_sign = sub.add_node("AcousticSign", {})
    sp_w = sub.add_node("Concept", {"name": "probe"})
    sub.set_attr(sp_sign, RG.SIGN_FEAT_ATTR, probe)
    sub.set_attr(sp_w, RG.WORD_FEAT_ATTR, probe)
    dtw_self = float(sub.evaluate(_Term(RG.synth_error_term()),
                                  {"s": sp_sign, "w": sp_w}))
    mf_self = float(sub.evaluate(_Term(RG.matched_filter_term()),
                                 {"s": sp_sign, "w": sp_w}))
    print(f"  native DtwTo(self)     = {dtw_self:.4f}  (expect 0.0, a distance)",
          flush=True)
    print(f"  native XCorrPeak(self) = {mf_self:.4f}  (expect ~1.0, a similarity)",
          flush=True)
    if abs(mf_self - 1.0) > 1e-6:
        print("  WARN: XCorrPeak self-similarity != 1.0 — check the build", flush=True)

    # ---- DO-CONTRAST: LOSO, ONE forward model, two native operations ----
    print("\n--- DO-CONTRAST: native DtwTo distance vs native XCorrPeak (LOSO) ---",
          flush=True)
    dtw_corr = dtw_tot = 0
    mf_corr = mf_tot = 0
    dtw_pw = {}
    mf_pw = {}
    rng = random.Random(1234)
    for held in speakers:
        fm = fm_single_mean(utt_traj, loaded, held)
        fm_use = _shuffle_fm(fm, rng) if do_shuffle else fm
        for i, (x, _fs, d, s) in enumerate(loaded):
            if s != held:
                continue
            M = heard_M[i]
            if M is None or M.shape[0] < 2:
                continue
            true = _DIGITS[d]
            a = rec.recognise_dtw(M, fm_use)
            b = rec.recognise_mf(M, fm_use)
            if a is not None:
                dtw_corr += int(a == true); dtw_tot += 1
                dtw_pw.setdefault(true, [0, 0]); dtw_pw[true][0] += int(a == true); dtw_pw[true][1] += 1
            if b is not None:
                mf_corr += int(b == true); mf_tot += 1
                mf_pw.setdefault(true, [0, 0]); mf_pw[true][0] += int(b == true); mf_pw[true][1] += 1
        print(f"  held-out {held}: running  DtwTo {dtw_corr}/{dtw_tot}  "
              f"XCorrPeak {mf_corr}/{mf_tot}", flush=True)

    dtw_acc = dtw_corr / max(dtw_tot, 1)
    mf_acc = mf_corr / max(mf_tot, 1)
    delta = mf_acc - dtw_acc
    print("\n========================= DO-CONTRAST RESULT =========================",
          flush=True)
    print(f"  (A) NATIVE DtwTo  synth-error      : {dtw_acc:.4f}  ({dtw_corr}/{dtw_tot})",
          flush=True)
    print(f"  (B) NATIVE XCorrPeak matched filter: {mf_acc:.4f}  ({mf_corr}/{mf_tot})",
          flush=True)
    print(f"  DELTA (matched filter - DtwTo)     : {delta:+.4f}", flush=True)
    print(f"  chance (10 digits)                 : 0.1000", flush=True)
    print("  per-word (DtwTo -> XCorrPeak):", flush=True)
    for w in _DIGITS:
        da = dtw_pw.get(w, [0, 0]); ma = mf_pw.get(w, [0, 0])
        if da[1]:
            print(f"    {w:6s}: {da[0]/da[1]:.2f} -> {ma[0]/ma[1]:.2f}", flush=True)

    # ---- HONEST VERDICT ----
    print("\n========================= VERDICT =========================", flush=True)
    if do_shuffle:
        print("  SHUFFLE BACKSTOP: forward-model labels permuted. A genuine "
              "recogniser collapses toward chance (0.10).", flush=True)
        dtw_ok = dtw_acc < 0.20
        mf_ok = mf_acc < 0.20
        print(f"  DtwTo collapses to chance     : {dtw_ok} (acc {dtw_acc:.4f})",
              flush=True)
        print(f"  XCorrPeak collapses to chance : {mf_ok} (acc {mf_acc:.4f})",
              flush=True)
        verdict = "SHUFFLE_BACKSTOP"
    else:
        # both native; the matched filter is the agent-authored primitive.
        mf_above = mf_acc > 0.15            # above chance at all
        if delta > 0.01:
            print(f"  MATCHED FILTER WINS: the agent-authored XCorrPeak beats the "
                  f"native DtwTo {delta:+.4f} ({dtw_acc:.4f} -> {mf_acc:.4f}) on the "
                  f"SAME data/forward-model/venue. The sonar transfer cashed.",
                  flush=True)
            verdict = "MATCHED_FILTER_WINS"
        elif delta < -0.01:
            print(f"  HONEST NULL: the matched filter UNDERperforms DtwTo {delta:+.4f} "
                  f"({dtw_acc:.4f} -> {mf_acc:.4f}). The primitive is AUTHORED + LIVE "
                  f"and evaluates natively; on this venue the peak-NCC operation does "
                  f"not beat surface-DTW. The wall is the OPERATION's fit to A1 "
                  f"trajectories, not the runtime self-extension (which succeeded).",
                  flush=True)
            verdict = "HONEST_NULL_MF_BELOW_DTW"
        else:
            print(f"  TIE: matched filter ~ DtwTo (delta {delta:+.4f}). The authored "
                  f"primitive evaluates natively and tracks the DtwTo baseline; no "
                  f"clear operation advantage on this venue.", flush=True)
            verdict = "TIE"
        print(f"  matched filter above chance: {mf_above} (acc {mf_acc:.4f} vs 0.10)",
              flush=True)

    print(f"\nVERDICT_TOKEN={verdict}  delta={delta:+.4f}  "
          f"dtw={dtw_acc:.4f}  xcorr={mf_acc:.4f}", flush=True)
    print(f"elapsed {time.time()-t0:.1f}s", flush=True)
    print("===MARKER_MF_GROUND_COMPLETE===", flush=True)
    return verdict


if __name__ == "__main__":
    main()
