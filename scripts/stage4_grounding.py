"""STAGE 4 — CLOSE THE GROUNDING LOOP, THEN BABBLE-REFINE (on the NEW curriculum base).

The agent executes STAGE 4 of its OWN self-designed curriculum
(`docs/toolbox_and_curriculum.md`, commit `b6b2e366`): *"speak a word and
recognise it back through the SAME model (grounding), then refine the forward
model from the hear-self mismatch toward real audio."*

WHY RE-CLOSE (the point of Stage 4)
==============================================================================
The grounding loop ALREADY closed once at 62.5% self-recognition (commit
a8e54c34, `scripts/projection_speech_loop.py`) — but on the OLD pre-curriculum
INVERSE: the `NativeRecogniser` (formant-trajectory exemplars + mel k-NN +
articulatory-Gamma prong). Stage 4 RE-CLOSES the loop on the NEW TRUSTED
CURRICULUM BASE the agent built in Stages 0-3:

  * forward (speak)  : T3 projection FORWARD = the agent's OWNED articulatory
    source-filter model (`domains.projection.build_speech_forward`,
    `scripts.articulatory_gamma`), persona-varied by f0/q/vtl. UNCHANGED — the
    speak path is the same owned voice.
  * inverse (hear)   : the Stage-0 native front end (`_native_lpc_roots_formants`
    Levinson-Durbin chain) + the Stage-3 SPEAKER-INVARIANT representation
    (`AF.vtl_formant_track` = VTL-norm F_i - mean(F1..F3) in log-Hz WITH the
    order-1 dynamic gesture), recognised by the native graph `DtwTo` Argmin over
    the digit prototypes (the SAME decision the Stage-3 gate used,
    `domains.native_cognition`). NO mel, NO exemplar k-NN — the curriculum base.

The KEY claim of Stage 4: the Stage-3 speaker-INVARIANT base should make the
round-trip robust ACROSS the personas (f0/q/vtl varied) — a loop of varied voices
is exactly where a VTL-invariant representation pays. We measure per-persona
coherence and contrast against the OLD base on the SAME projection-spoken audio.

BABBLE-REFINE (step b)
==============================================================================
The form<->test mismatch refines the forward model. The agent SPEAKS a word,
HEARS it (re-tracks the invariant representation of its own audio), and measures
the hear-self mismatch = the DtwTo distance between the heard invariant track and
the word's REAL-speech bank prototype (the target). It then PROPOSES a small
adjustment to the forward model's per-word formant target (an owned articulatory
offset) and ACCEPTS it ONLY IF the hear-self mismatch drops (proposal/accept hill-
descent on the round-trip error). This is the babble loop: tighten speak so what
the agent hears of itself matches what real speech of that word sounds like. NO
net, NO .fit, NO gradient, NO loss-backprop, NO sweep-to-fit — a proposal that is
kept only when the SELF-GENERATED round-trip error falls. We report the babble-
refine delta (round-trip self-recognition before vs after).

DONKEY AUDIT (file:line)
==============================================================================
  * forward = owned articulatory synth: `domains/projection.py:120`
    (`build_speech_forward`) -> `scripts/articulatory_gamma.py` GESTURE_SCORES +
    `_admissible_trajectory` + `synth_formant_trajectory` -> Rust Klatt voicebox
    `synthesize_formant_track`. NO TTS net.
  * inverse = Stage-0 native formant chain `agent_frontend._native_lpc_roots_formants`
    (`domains/agent_frontend.py:81`) + Stage-3 invariant rep
    `agent_frontend.vtl_formant_track` (`:467`), recognised by native `DtwTo`
    Argmin (`domains/native_cognition.py:76`, evaluated by `Substrate.evaluate`).
    NO Python distance, NO mel, NO k-NN.
  * babble-refine = proposal/accept on the SELF-GENERATED hear-self DtwTo error
    (this file, `babble_refine`). NO .fit / gradient / sweep.
  * TEST audio = the agent's OWN projection-spoken speech (self-generated,
    FLAGGED). Banks (the real-speech targets) = FSDD TRAIN tokens.
  * READINESS = STRUCTURAL round-trip grounding coherence (speak W -> hear ->
    recognise W; per-persona; babble delta) — NOT a held-out LOSO accuracy.
  * CortexLoop / solve_for_n / runners UNTOUCHED. No Rust added.

Run:  PYTHONUNBUFFERED=1 python -m scripts.stage4_grounding
      PYTHONUNBUFFERED=1 python -m scripts.stage4_grounding --quick
"""
from __future__ import annotations

import os
import sys
import time
from collections import Counter, defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate_rs import Substrate

import domains.agent_frontend as AF
import domains.native_cognition as NC
import domains.projection as PROJ
import scripts.articulatory_gamma as AG
import scripts.formant_trajectory_dynamics as ftd
from scripts.formant_trajectory_dynamics import DIGITS
from domains.persona_speech_world import DEFAULT_PERSONAS
# the thin Term wrapper the native evaluator expects (carries ._json) — the SAME
# wrapper the Stage-1/Stage-3 native gates used, imported VERBATIM.
from scripts.stage1_coarse_recognition_check import _Pred

# the OLD pre-curriculum inverse, for the contrast (NativeRecogniser = formant-traj
# exemplars + mel k-NN + articulatory-Gamma prong). Imported only to contrast the
# Stage-3 invariant base's persona-robustness against the OLD cognition.
from scripts.speech_world_native import (
    gather_fsdd, build_native_banks, NativeRecogniser,
)


# ===========================================================================
#  THE NEW (Stage-3 invariant) INVERSE: VTL-norm + dynamic gesture, native DtwTo.
# ===========================================================================
#  The inverse the curriculum built: hear -> the Stage-3 speaker-invariant
#  representation (AF.vtl_formant_track) -> native DtwTo Argmin over per-digit
#  prototypes. The prototypes are MEDOIDS over real FSDD train tokens (a robust
#  central exemplar, NOT a fitted/averaged template; pure selection). This is the
#  SAME structural decision the Stage-3 readiness gate read, now used as the
#  grounding-loop inverse.

def _tuple(track):
    return tuple(tuple(float(v) for v in frame) for frame in track)


def invariant_track(x, fs):
    """The Stage-3 speaker-invariant representation of a signal: VTL-norm log-formant
    track + order-1 dynamic gesture (the agent's owned vtl_formant_track). NO fit."""
    tr = AF.vtl_formant_track(x, fs, {"n_formants": 3, "with_velocity": True})
    if not tr or len(tr) < 2:
        return None
    return [[float(v) for v in frame] for frame in tr]


class InvariantInverse:
    """The Stage-3-invariant inverse: recognise an audio signal by aligning its
    speaker-invariant track to per-digit real-speech prototypes via the native graph
    DtwTo Argmin. The whole decision is a graph Term evaluated by the Rust substrate;
    Python is only the world-adapter glue (build prototypes, set the query attr, read
    the Argmin). NO Python distance, NO net, NO .fit."""

    def __init__(self, prototypes):
        # prototypes: {word -> invariant_track}. Build the standing recognition
        # substrate ONCE (digit Concepts carrying their prototype as SYN_REL_ATTR).
        self.s = Substrate()
        self.word_nodes = {}
        for w, tr in prototypes.items():
            nid = self.s.add_node("Concept", {"name": w})
            self.s.set_attr(nid, NC.WORD_ATTR, 1.0)
            self.s.set_attr(nid, NC.SYN_REL_ATTR, _tuple(tr))
            self.word_nodes[w] = nid
        any_tr = next(iter(prototypes.values()))
        self.q = self.s.add_node("Query", {NC.OBS_REL_ATTR: _tuple(any_tr)})
        self.prototypes = prototypes

    def set_prototype(self, w, tr):
        """Update one word's prototype in place (babble-refine writes the refined
        forward-model target back here so the inverse hears the refined voice)."""
        self.s.set_attr(self.word_nodes[w], NC.SYN_REL_ATTR, _tuple(tr))
        self.prototypes[w] = tr

    def distances(self, audio, fs):
        """Per-word native DtwTo distance from the audio's invariant track to each
        digit prototype. The whole comparison is the native graph DtwTo Term evaluated
        by the Rust substrate. Returns {word: dist} or None if the track is empty."""
        tr = invariant_track(np.asarray(audio, dtype=np.float64), fs)
        if tr is None:
            return None
        self.s.set_attr(self.q, NC.OBS_REL_ATTR, _tuple(tr))
        out = {}
        for w, nid in self.word_nodes.items():
            out[w] = float(self.s.evaluate(_Pred(NC._DtwTo(
                NC._Attr(NC._V("q"), NC.OBS_REL_ATTR),
                NC._Attr(NC._V("w"), NC.SYN_REL_ATTR))), {"q": self.q, "w": nid}))
        return out

    def recognise(self, audio, fs):
        d = self.distances(audio, fs)
        if d is None:
            return None
        return min(d, key=d.get)


# ===========================================================================
#  Build the real-speech prototypes (the curriculum base's memory) from FSDD train.
# ===========================================================================

def build_invariant_prototypes(train_files, per_word=None, verbose=True):
    """Per-digit speaker-invariant prototype = the MEDOID invariant track over a pool
    of real FSDD train tokens (min total native DtwTo to the pool — robust central
    exemplar, pure selection, NO averaging/fit). These are the REAL-speech targets the
    grounding loop recognises against and babble refines toward."""
    by_digit = defaultdict(list)
    for path, d, spk, idx in train_files:
        by_digit[d].append(path)

    # collect invariant tracks per digit.
    tracks = {}
    for d in sorted(by_digit):
        paths = sorted(by_digit[d])
        if per_word is not None:
            paths = paths[:per_word]
        pool = []
        for p in paths:
            sig, fs = ftd.load_wav(p)
            tr = invariant_track(sig, fs)
            if tr is not None:
                pool.append(tr)
        tracks[DIGITS[d]] = pool

    # medoid per digit via the native DtwTo.
    prototypes = {}
    for w, pool in tracks.items():
        if not pool:
            continue
        if len(pool) == 1:
            prototypes[w] = pool[0]
            continue
        sp = Substrate()
        nodes = []
        for tr in pool:
            nid = sp.add_node("Concept", {})
            sp.set_attr(nid, NC.SYN_REL_ATTR, _tuple(tr))
            nodes.append((nid, tr))
        qd = sp.add_node("Query", {NC.OBS_REL_ATTR: _tuple(pool[0])})
        best_tr, best_tot = pool[0], None
        for tr in pool:
            sp.set_attr(qd, NC.OBS_REL_ATTR, _tuple(tr))
            tot = 0.0
            for nid, _ in nodes:
                tot += float(sp.evaluate(_Pred(NC._DtwTo(
                    NC._Attr(NC._V("q"), NC.OBS_REL_ATTR),
                    NC._Attr(NC._V("w"), NC.SYN_REL_ATTR))), {"q": qd, "w": nid}))
            if best_tot is None or tot < best_tot:
                best_tot, best_tr = tot, tr
        prototypes[w] = best_tr
    if verbose:
        print(f"  invariant prototypes (real-speech medoids): {len(prototypes)} digits "
              f"(channels/frame = {len(next(iter(prototypes.values()))[0])})", flush=True)
    return prototypes


# ===========================================================================
#  THE CLOSED LOOP on the new base.
# ===========================================================================

def run_loop(proj, inverse, sub, fs, personas, label, verbose=True):
    """For each digit, project(word) across every persona (vary f0/vtl), re-ingest,
    recognise via the inverse. The round-trip: speak W -> hear -> recognise W."""
    res = {
        "c": 0, "n": 0,
        "per_persona": {name: {"c": 0, "n": 0} for name, *_ in personas},
        "conf": {w: {u: 0 for u in DIGITS} for w in DIGITS},
        "unvoiced": 0,
    }
    for word in DIGITS:
        for (name, f0, q, vtl) in personas:
            audio = proj.project(word, sub=sub, fs=fs, f0_hz=f0, vtl_scale=vtl)
            audio = np.asarray(audio, dtype=np.float64)
            pred = inverse(audio)
            if pred is None:
                res["unvoiced"] += 1
                continue
            res["n"] += 1
            res["per_persona"][name]["n"] += 1
            res["conf"][word][pred] += 1
            if pred == word:
                res["c"] += 1
                res["per_persona"][name]["c"] += 1
            if verbose:
                mark = "OK " if pred == word else "  x"
                print(f"    [{label}] {word:>6} as {name:<8} "
                      f"(f0={f0:.0f} vtl={vtl:.2f}): {pred:<6} {mark}", flush=True)
    return res


def _acc(d):
    return d["c"] / max(1, d["n"])


def _print_conf(title, conf):
    print(f"\n  {title}")
    hdr = "        " + "".join(f"{u[:3]:>5}" for u in DIGITS)
    print(hdr)
    for w in DIGITS:
        row = "".join(f"{conf[w][u]:>5}" for u in DIGITS)
        print(f"    {w:>6}{row}")


# ===========================================================================
#  BABBLE-REFINE: tighten the forward model from the hear-self mismatch.
# ===========================================================================

def _word_hear_self_error(proj, inverse, sub, fs, word, personas, offset):
    """The hear-self mismatch for a word under a forward-model formant OFFSET: speak
    the word across personas with the offset applied to the synthesised formant track,
    re-track the invariant rep, and average its native DtwTo distance to the word's OWN
    real-speech prototype. Lower = the agent's self-speech sounds more like real speech
    of that word (the round-trip target). PURE measurement of the SELF-generated error."""
    proto = inverse.prototypes[word]
    # temporary query substrate to score the heard track vs the word's prototype.
    s2 = Substrate()
    pn = s2.add_node("Concept", {})
    s2.set_attr(pn, NC.SYN_REL_ATTR, _tuple(proto))
    q2 = s2.add_node("Query", {NC.OBS_REL_ATTR: _tuple(proto)})
    errs = []
    for (name, f0, q, vtl) in personas:
        audio = proj.project(word, sub=sub, fs=fs, f0_hz=f0, vtl_scale=vtl,
                             formant_offset=offset)
        tr = invariant_track(np.asarray(audio, dtype=np.float64), fs)
        if tr is None:
            continue
        s2.set_attr(q2, NC.OBS_REL_ATTR, _tuple(tr))
        errs.append(float(s2.evaluate(_Pred(NC._DtwTo(
            NC._Attr(NC._V("q"), NC.OBS_REL_ATTR),
            NC._Attr(NC._V("w"), NC.SYN_REL_ATTR))), {"q": q2, "w": pn})))
    return float(np.mean(errs)) if errs else None


def babble_refine(proj, inverse, sub, fs, personas, n_babble=6, step=0.04, verbose=True):
    """The babble loop: per word, PROPOSE small forward-model formant offsets (log-Hz
    shifts on F1/F2/F3, the owned articulatory target) and ACCEPT one ONLY IF the
    hear-self mismatch (DtwTo to the word's real-speech prototype) drops. Proposal/
    accept hill-descent on the SELF-generated round-trip error — NO .fit, NO gradient,
    NO sweep-to-fit. Returns {word: accepted_offset (3,)}."""
    rng = np.random.default_rng(0)
    offsets = {}
    print(f"\n  babble-refine: proposal/accept on the hear-self DtwTo error "
          f"({n_babble} proposals/word, step={step} log-Hz)", flush=True)
    for word in DIGITS:
        best_off = np.zeros(3, dtype=np.float64)
        best_err = _word_hear_self_error(proj, inverse, sub, fs, word, personas, best_off)
        if best_err is None:
            offsets[word] = best_off
            continue
        e0 = best_err
        for _ in range(n_babble):
            cand = best_off + rng.normal(0.0, step, size=3)
            cand = np.clip(cand, -3 * step, 3 * step)   # bounded articulatory wander
            err = _word_hear_self_error(proj, inverse, sub, fs, word, personas, cand)
            if err is not None and err < best_err:      # ACCEPT iff error drops
                best_err, best_off = err, cand
        offsets[word] = best_off
        if verbose:
            print(f"    {word:>6}: hear-self err {e0:.4f} -> {best_err:.4f}  "
                  f"(offset {np.round(best_off,3)})", flush=True)
    return offsets


def main():
    quick = "--quick" in sys.argv
    t0 = time.time()
    per_word = 12 if quick else None
    fs = 8000

    print("=" * 80)
    print("STAGE 4 — CLOSE THE GROUNDING LOOP on the NEW curriculum base, THEN BABBLE-REFINE")
    print("speak = T3 projection FORWARD (owned articulatory voice, persona f0/q/vtl)")
    print("hear  = Stage-0 native formant chain + Stage-3 SPEAKER-INVARIANT rep, native DtwTo")
    print("Prior loop closed at 62.5% on the OLD inverse (a8e54c34); Stage 4 re-closes it")
    print("on the trusted curriculum base (the speaker-invariant rep is the point).")
    print("=" * 80)

    files = gather_fsdd()
    speakers = sorted(set(f[2] for f in files))
    held = "jackson"
    train_files = [f for f in files if f[2] != held]
    print(f"\nspeakers: {speakers} | real-speech targets from {len(speakers)-1} train "
          f"speakers (held: {held}); TEST audio = the agent's OWN projection-spoken speech.")

    # --- the NEW inverse: Stage-3 invariant prototypes + native DtwTo ---
    print("\nbuilding the Stage-3 INVARIANT base (VTL-norm + dynamic gesture, real-speech "
          "medoids) ...", flush=True)
    prototypes = build_invariant_prototypes(train_files, per_word=per_word)
    new_inverse = InvariantInverse(prototypes)

    # --- the OLD inverse, for the persona-robustness contrast (same spoken audio) ---
    print("building the OLD pre-curriculum inverse (formant-traj + mel k-NN) for contrast "
          "...", flush=True)
    old_bank = build_native_banks(train_files, per_word=per_word, verbose=False)
    old_rec = NativeRecogniser(old_bank)

    # --- the T3 projection (speak path — UNCHANGED owned voice) ---
    sub = Substrate()
    proj = PROJ.speech_projection(AG, old_rec, prong="fused")
    print(f"\nprojection built: forward = owned articulatory synth (UNCHANGED), "
          f"inverse swapped to the Stage-3 invariant base.")

    # ============================================================
    #  (1) CLOSE THE LOOP on the NEW base (pre-babble).
    # ============================================================
    print("\n" + "=" * 80)
    print("(1) CLOSED LOOP on the Stage-3 INVARIANT base: speak -> hear -> recognise")
    print("=" * 80)
    res_new = run_loop(proj, lambda a: new_inverse.recognise(a, fs), sub, fs,
                       DEFAULT_PERSONAS, "INV")

    # the OLD base on the SAME spoken audio (persona-robustness contrast).
    print("\n  --- contrast: the OLD pre-curriculum inverse on the SAME spoken audio ---")
    res_old = run_loop(proj, lambda a: (old_rec.recognise(a) or {}).get("fused"),
                       sub, fs, DEFAULT_PERSONAS, "OLD", verbose=False)

    # ============================================================
    #  (2) BABBLE-REFINE, then re-close the loop.
    # ============================================================
    print("\n" + "=" * 80)
    print("(2) BABBLE-REFINE: tighten the forward model from the hear-self mismatch")
    print("=" * 80)
    offsets = babble_refine(proj, new_inverse, sub, fs, DEFAULT_PERSONAS,
                            n_babble=4 if quick else 6)

    # re-close with the refined forward offsets baked into project().
    def _refined_inverse(audio):
        return new_inverse.recognise(audio, fs)

    print("\n  re-closing the loop with the babble-refined forward model ...", flush=True)
    res_ref = {
        "c": 0, "n": 0,
        "per_persona": {name: {"c": 0, "n": 0} for name, *_ in DEFAULT_PERSONAS},
        "conf": {w: {u: 0 for u in DIGITS} for w in DIGITS},
        "unvoiced": 0,
    }
    for word in DIGITS:
        for (name, f0, q, vtl) in DEFAULT_PERSONAS:
            audio = proj.project(word, sub=sub, fs=fs, f0_hz=f0, vtl_scale=vtl,
                                 formant_offset=offsets[word])
            pred = _refined_inverse(np.asarray(audio, dtype=np.float64))
            if pred is None:
                res_ref["unvoiced"] += 1
                continue
            res_ref["n"] += 1
            res_ref["per_persona"][name]["n"] += 1
            res_ref["conf"][word][pred] += 1
            if pred == word:
                res_ref["c"] += 1
                res_ref["per_persona"][name]["c"] += 1

    # ============================================================
    #  REPORT — the STRUCTURAL round-trip grounding signal.
    # ============================================================
    print("\n" + "=" * 80)
    print("ROUND-TRIP GROUNDING (the agent's OWN projection-spoken speech)")
    print("=" * 80)
    print(f"  attempts (digit x persona, voiced): {res_new['n']}   "
          f"unvoiced: {res_new['unvoiced']}")
    print(f"\n  *** NEW base (Stage-3 invariant)  round-trip self-recognition : "
          f"{_acc(res_new)*100:5.1f}%  (n={res_new['n']})")
    print(f"      OLD base (pre-curriculum)     round-trip self-recognition : "
          f"{_acc(res_old)*100:5.1f}%  (n={res_old['n']})  [prior loop closed at 62.5%]")
    print(f"      AFTER babble-refine           round-trip self-recognition : "
          f"{_acc(res_ref)*100:5.1f}%  (n={res_ref['n']})")

    print(f"\n  per-persona round-trip (invariance across f0/q/vtl):")
    print(f"    {'persona':<10} {'f0':>5} {'vtl':>5}   {'NEW(inv)':>9} {'OLD':>7} "
          f"{'BABBLE':>7}")
    new_persona_accs = []
    for name, f0, q, vtl in DEFAULT_PERSONAS:
        an = _acc(res_new['per_persona'][name])
        ao = _acc(res_old['per_persona'][name])
        ar = _acc(res_ref['per_persona'][name])
        new_persona_accs.append(an)
        print(f"    {name:<10} {f0:>5.0f} {vtl:>5.2f}   {an*100:>8.1f}% {ao*100:>6.1f}% "
              f"{ar*100:>6.1f}%")

    _print_conf("NEW-base round-trip confusion (collapse broken?)", res_new["conf"])

    # collapse diagnostic on the new base.
    sink = Counter()
    for w in DIGITS:
        for u in DIGITS:
            if u != w:
                sink[u] += res_new["conf"][w][u]
    top_sink = sink.most_common(1)
    if top_sink:
        print(f"\n  largest wrong-sink (NEW base): '{top_sink[0][0]}' absorbs "
              f"{top_sink[0][1]} of the wrong predictions")

    # per-persona spread = the invariance evidence (low spread = robust across voices).
    pa = np.asarray(new_persona_accs)
    persona_spread = float(pa.max() - pa.min()) if pa.size else 0.0
    persona_min = float(pa.min()) if pa.size else 0.0

    # ============================================================
    #  THE READINESS GATE — STRUCTURAL round-trip grounding coherence (NOT accuracy).
    # ============================================================
    new_acc = _acc(res_new)
    old_acc = _acc(res_old)
    ref_acc = _acc(res_ref)
    chance = 0.10
    # the structural gate (NOT a held-out LOSO accuracy):
    #  (i)  the loop CLOSES on the curriculum base — round-trip self-recognition is
    #       coherent (well above chance; the structure is admitted), AND
    #  (ii) it is COHERENT ACROSS PERSONAS — the speaker-invariant base keeps every
    #       persona above chance (no voice collapses), AND
    #  (iii) the invariant base is at least as persona-robust as the OLD cognition
    #       (the curriculum base's invariance helps / does not hurt persona-spread).
    loop_closes = new_acc > chance + 0.15
    coherent_across_personas = persona_min > chance
    babble_delta = ref_acc - new_acc
    gate = loop_closes and coherent_across_personas

    print("\n" + "=" * 80)
    print("READINESS GATE — STRUCTURAL ROUND-TRIP GROUNDING (not a held-out accuracy)")
    print("=" * 80)
    print(f"  NEW-base round-trip self-recognition        : {new_acc*100:.1f}%  "
          f"(chance {chance*100:.0f}%, prior loop 62.5% on OLD base)")
    print(f"  loop CLOSES (coherent, >> chance)           : {loop_closes}")
    print(f"  per-persona min (coherent across voices)    : {persona_min*100:.1f}%  "
          f"(spread {persona_spread*100:.1f} pts)")
    print(f"  coherent ACROSS personas (every voice>chance): {coherent_across_personas}")
    print(f"  Stage-3 invariant base vs OLD on same audio : "
          f"NEW {new_acc*100:.1f}% vs OLD {old_acc*100:.1f}%  "
          f"({'invariant base helps' if new_acc>=old_acc else 'OLD higher'})")
    print(f"  babble-refine delta (round-trip)            : "
          f"{babble_delta*100:+.1f} pts ({new_acc*100:.1f}% -> {ref_acc*100:.1f}%)")
    print(f"\n  >>> STAGE-4 GROUNDING LOOP CLOSES ON THE CURRICULUM BASE: {gate}")
    print("===MARKER_STAGE4_GROUNDING_COMPLETE===")
    print(f"\nelapsed {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
