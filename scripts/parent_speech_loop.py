"""parent_speech_loop — the honest A/B: PARENT-TAUGHT vs SELF-PICK babble.

Does TEACHING help? This runs the two regimes from the SAME fresh start, judged by
the SAME ungameable held-out probe (full lexicon, never restricted), and shows the
held-out learning curves for both:

  SELF-PICK babble  (the current world): the agent picks its own cell (PICK_TERM,
    deficit + explore), the world plays a random instance, the agent BLIND-guesses
    over the FULL cell lexicon, cookie iff right, banks on cookie/first-sight.

  PARENT-TAUGHT (the new PARENT, first piece): the PARENT picks the cell at the
    agent's MEASURED ZPD (ZPD_PICK_TERM, fed by the held-out rate), with the
    curriculum-stage gate (gradual release: harder sources unlock only on mastery),
    speaks the word in IDS register, and OSTENSIVELY NAMES it — the agent guesses
    within a RESTRICTED COMPETITOR SET (not the full lexicon), gets the cookie, and
    banks the IDS clip as the learning target. A FREE-PLAY track is kept (a fraction
    of turns are self-pick, full-lexicon babble) — joint attention is not the only
    route to grounding (the literature is a dyad of teaching AND exploration).

THE DONKEY BOUNDARY (policed): the PARENT speaks / names / picks-level; it NEVER
recognises. The agent's blind_guess over its own exemplars in its own feature space
is the recognizer in BOTH regimes. The ZPD pick is a graph Term fed by the agent's
held-out measure. The ostensive label is the learning TARGET (what to bank), NOT the
answer — the agent still guesses. The held-out probe is ALWAYS full-lexicon,
restrict_to=None, so teaching cannot inflate the measured capability.

Run:
  PYTHONUNBUFFERED=1 python -m scripts.parent_speech_loop \
      [--seconds N] [--report-every S] [--out /tmp/parent_ab.json]

Both regimes start from a FRESH substrate (no save reuse) so the comparison is fair.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate_rs import Substrate
import domains.self_directed_speech_world as W
import domains.parent_teacher as P
from scripts.self_directed_speech_loop import (World, build_heldout,
                                               measure_heldout, _has_label,
                                               _bank_size)


# ---------------------------------------------------------------------------
# (3) LARGER LEXICONS — a bigger WORD vocabulary drawn from the real TVTropes text
# corpus. A random self-pick syllabus over a LARGE lexicon strands the learner (it
# samples too thinly to ground any word), which is exactly the regime the parent's
# scaffolding is FOR (teach a few words at the agent's level, master, release). The
# digit grid (10 words) is too small for a random self-pick to strand — the larger
# lexicon is where teaching should win. This World subclass only widens the WORD
# vocab; everything else (play, the held-out path) is the unchanged world adapter.
# ---------------------------------------------------------------------------

class ScaledWorld(World):
    def __init__(self, lexicon_size=40, seed=0):
        super().__init__(stage2=False, seed=seed)
        # draw a larger real-text lexicon from TVTropes (concrete, frequency-first
        # tokens). Fall back to the small fixed common-word set if no corpus.
        words = W.tvtropes_words(max(lexicon_size * 3, 120))
        self._big_lexicon = words[:lexicon_size] if words else None

    def vocab(self, granularity, source, language):
        if granularity == "word" and self._big_lexicon and language == "en":
            return list(self._big_lexicon)
        return super().vocab(granularity, source, language)


def _setup(seed=0, scaled=False, lexicon_size=40):
    # Two fresh substrates in ONE process reuse NodeIDs from zero with the same seed
    # cues, so the world's per-exemplar feature cache (keyed on node-id + front-end
    # signature) would cross-contaminate the second regime with the first's vectors.
    # Clear it between regimes — this A/B is the only place two substrates coexist; the
    # live single-process loop never needs it.
    W.reset_caches()
    s = Substrate()
    W.install_speech_world_rules(s)
    world = ScaledWorld(lexicon_size=lexicon_size, seed=seed) if scaled \
        else World(stage2=False, seed=seed)
    languages = ["en"]
    sources = ["espeak", "noise"] + (["fsdd"] if world.fsdd else [])
    if W.piper_available("en"):
        sources.append("piper")
    # the digit grid (10 words) + (when scaled) a LARGER-lexicon WORD grid drawn from
    # the real TVTropes corpus. The big word vocab is where a random self-pick strands
    # the learner and the parent's scaffolding has room to win.
    granularities = ["digit"] + (["word"] if scaled else [])
    cells_meta = {}
    for g in granularities:
        for lang in languages:
            for src in sources:
                # FSDD is real-human ENGLISH DIGITS only — no word recordings exist.
                if src == "fsdd" and (g != "digit" or lang != "en"):
                    continue
                if src == "piper" and not W.piper_available(lang):
                    continue
                c = W.install_cell(s, g, src, lang)
                cells_meta[s.node(c)["attrs"]["name"]] = s.node(c)["attrs"]
    cell_by_name = {s.node(c)["attrs"]["name"]: c
                    for c in s.nodes("CurriculumCell")}
    # held-out probes: 2 per word for the digit grid; with a large word lexicon 2-per
    # is already a big balanced probe set — keep n_per modest so a report is fast.
    held = build_heldout(world, cells_meta, n_per=2)
    return s, world, cells_meta, cell_by_name, held


def _report(s, world, cells_meta, cell_by_name, held, label, elapsed, step,
            prev):
    """Measure the SAME ungameable held-out (full lexicon, restrict_to=None) for
    every cell and print + return the snapshot. Identical probe for both regimes."""
    snap = {}
    print(f"\n--- [{label}] REPORT t={elapsed:.0f}s step={step} "
          f"(front-end {W.live_n_channels(s)} cues) ---", flush=True)
    for name in sorted(cells_meta):
        c = cell_by_name[name]
        r = measure_heldout(s, world, cells_meta[name], held[name])  # full lexicon
        s.set_attr(c, "held_cookie_rate", float(r))
        if prev:
            s.set_attr(c, "held_delta", float(r - prev.get(name, 0.0)))
        s.set_attr(c, "live_rate", float(r))
        s.set_attr(c, "n_probes", float(len(held[name])))
        snap[name] = r
        pr = prev.get(name, 0.0)
        print(f"   {name:24s} held-out {r:.3f} (Δ {r - pr:+.3f}, "
              f"bank {_bank_size(s, name, cells_meta[name])})", flush=True)
    return snap


# ---------------------------------------------------------------------------
# REGIME A — self-pick babble (the existing world's curriculum).
# ---------------------------------------------------------------------------

def run_selfpick(seconds, report_every, seed=0, scaled=False, lexicon_size=40):
    s, world, cells_meta, cell_by_name, held = _setup(seed, scaled=scaled,
                                                      lexicon_size=lexicon_size)
    t0 = time.time()
    last_report = 0.0
    step = 0
    history = []
    prev = {}
    while time.time() - t0 < seconds:
        picked = W.pick_cell(s)                       # the agent's deficit self-pick
        if picked is None:
            break
        attrs = s.node(picked)["attrs"]
        cell_key = attrs["name"]
        vocab = world.vocab(attrs["granularity"], attrs["source"], attrs["language"])
        word = world.rng.choice(vocab)
        x, fs = world.play(attrs, word)
        ch = W.feature_channels(s, x, fs)
        guess = W.blind_guess(s, ch, cell_key)        # FULL lexicon (self-directed)
        cookie = (guess == word)
        s.set_attr(picked, "live_attempts",
                   float(attrs.get("live_attempts", 0.0)) + 1)
        if cookie:
            s.set_attr(picked, "live_cookies",
                       float(s.node(picked)["attrs"].get("live_cookies", 0.0)) + 1)
        if cookie or not _has_label(s, word, cell_key):
            W.bank_exemplar(s, word, cell_key, x, fs)
        ca = s.node(picked)["attrs"]
        s.set_attr(picked, "live_rate",
                   0.8 * float(ca.get("live_rate", 0.0)) + 0.2 * (1.0 if cookie else 0.0))
        step += 1
        if (time.time() - t0) - last_report >= report_every:
            prev = _report(s, world, cells_meta, cell_by_name, held,
                           "self-pick", time.time() - t0, step, prev)
            history.append((time.time() - t0, prev))
            last_report = time.time() - t0
    prev = _report(s, world, cells_meta, cell_by_name, held, "self-pick",
                   time.time() - t0, step, prev)
    history.append((time.time() - t0, prev))
    return history


# ---------------------------------------------------------------------------
# REGIME B — the FULL PARENT: ZPD pick + ostensive naming + RECASTS (move 1) +
# REGISTER-GATING IDS->ADS (move 2) + (scaled lexicon, move 3) + free-play.
#
# The three moves, layered on the committed ZPD-curriculum + ostensive naming:
#   (1) RECASTS      — after the agent's blind guess the PARENT re-utters the CORRECT
#                      word (in the gated register); the AGENT banks the recast (and,
#                      on a miss, the guess-vs-correct contrast pair). Richer than the
#                      cookie: the correct FORM, contingent on the agent's attempt.
#   (2) REGISTER-GATE — the parent speaks IDS while the cell is far from mastery
#                      (held-out < ids_release) and transitions to ADS as it masters,
#                      so the bank ends register-matched to the ADS yardstick (fixes
#                      the first-piece IDS-hurts train/test mismatch). The register is
#                      a GRAPH Term fed by the agent's held-out rate (P.gated_register).
#   (3) SCALE        — a larger TVTropes WORD lexicon + longer budgets (in _setup /
#                      the caller) so a random self-pick strands the learner and
#                      gradual release reaches the hard (FSDD) cell.
# ---------------------------------------------------------------------------

def run_parent(seconds, report_every, seed=0, free_play_frac=0.25,
               competitor_k=4, use_ids=True, bank_on_miss=True,
               use_recasts=True, register_gate=True, scaled=False,
               lexicon_size=40):
    s, world, cells_meta, cell_by_name, held = _setup(seed, scaled=scaled,
                                                      lexicon_size=lexicon_size)
    P.install_parent(s)
    P.apply_stage_gate(s)                  # boot: only the easiest stage open
    t0 = time.time()
    last_report = 0.0
    step = 0
    history = []
    prev = {}
    fp_rng = random.Random(seed + 7)
    while time.time() - t0 < seconds:
        free_play = fp_rng.random() < free_play_frac
        if free_play:
            picked = W.pick_cell(s)        # FREE-PLAY: the agent self-directs
        else:
            picked = P.zpd_pick_cell(s)    # the PARENT picks at the agent's ZPD
        if picked is None:
            picked = W.pick_cell(s)
        if picked is None:
            break
        attrs = s.node(picked)["attrs"]
        cell_key = attrs["name"]
        vocab = world.vocab(attrs["granularity"], attrs["source"], attrs["language"])
        word = world.rng.choice(vocab)

        # In BOTH tracks the clip the agent HEARS is the cell's own source (the same
        # register the held-out probe uses) — so the IDS register is an ADDED prosodic
        # exemplar, never a substitute (no train/test register confound). The world
        # plays the natural clip; the parent's IDS is layered on top of the bank.
        x, fs = world.play(attrs, word)
        if free_play:
            # free-play / non-ostensive track: full-lexicon guess, self-directed bank.
            restrict = None
        else:
            # TAUGHT track: OSTENSIVE NAMING — the agent guesses within a RESTRICTED
            # COMPETITOR SET (suppress competitors, the research's strongest lever).
            # The label (word) is the learning TARGET, NOT the answer: the agent still
            # recognises the clip; the restricted set only narrows attention.
            restrict = P.competitor_set(vocab, word, k=competitor_k, rng=fp_rng)

        ch = W.feature_channels(s, x, fs)
        # the agent RECOGNISES (its own blind_guess); restrict_to only scopes the
        # candidate pool on the taught track (NEVER on the held-out yardstick).
        guess = W.blind_guess(s, ch, cell_key, restrict_to=restrict)
        cookie = (guess == word)
        s.set_attr(picked, "live_attempts",
                   float(attrs.get("live_attempts", 0.0)) + 1)
        if cookie:
            s.set_attr(picked, "live_cookies",
                       float(s.node(picked)["attrs"].get("live_cookies", 0.0)) + 1)
        # (2) REGISTER-GATING: the parent's register for THIS clip is the graph Term
        # P.gated_register, fed by the cell's held-out rate — IDS while far from
        # mastery (scaffold), ADS as it masters (release toward the test register), so
        # the bank ends register-matched to the ADS yardstick. Decision = the Term;
        # this only reads it. (register_gate=False -> always IDS, the first-piece
        # always-on behaviour, for the ablation.)
        register = P.gated_register(s, picked) if register_gate else "IDS"
        # LEARN. On the taught track the label is GIVEN (ostensive naming = fast
        # mapping), so the world clip is banked as the learning target even on a miss
        # (a child told the word banks it). The PARENT additionally provides a
        # register-gated (IDS early / ADS as mastered) exemplar of the SAME word. On
        # free-play the self-directed rule (cookie/first-sight) applies.
        if free_play:
            if cookie or not _has_label(s, word, cell_key):
                W.bank_exemplar(s, word, cell_key, x, fs)
        else:
            # ostensive naming: the label is given, so bank the world clip as the
            # learning target. bank_on_miss=True banks even on a miss (a child told the
            # word banks it); False uses the same cookie/first-sight discipline as
            # self-pick, isolating the ZPD+ostensive CURRICULUM lever from the banking
            # policy. use_ids adds the register-gated prosodic variant on top.
            if bank_on_miss or cookie or not _has_label(s, word, cell_key):
                W.bank_exemplar(s, word, cell_key, x, fs)
                if use_ids:
                    ids_x, ids_fs = P.parent_say(word, attrs["language"],
                                                 register=register)
                    W.bank_exemplar(s, word, cell_key, ids_x, ids_fs)
            # (1) RECASTS — the contingent corrective feedback: AFTER the agent's blind
            # guess, the PARENT re-utters the CORRECT word in the gated register and the
            # AGENT banks it (richer than the cookie: the correct FORM). On a MISS the
            # agent ALSO banks the guess-vs-correct CONTRAST pair (the clip it misheard,
            # re-labelled to the truth). The recast is the LEARNING TARGET, never the
            # guess-time answer (the guess is already committed above). The PARENT only
            # UTTERS; the banking is the agent's grounding (no-donkey).
            if use_recasts:
                # the recast clip (a fresh correct-form utterance) is ALWAYS banked.
                # The guess-vs-correct CONTRAST pair (re-label the misheard world clip
                # to the truth) is only added when the world clip was NOT already banked
                # above (i.e. clean-banking mode) — otherwise it would double-bank the
                # same clip. So pass guess_clip only when bank_on_miss is off.
                gclip = None if bank_on_miss else (x, fs)
                P.bank_recast(s, word, cell_key, attrs["language"],
                              register=register, guess=guess, guess_clip=gclip)
        ca = s.node(picked)["attrs"]
        s.set_attr(picked, "live_rate",
                   0.8 * float(ca.get("live_rate", 0.0)) + 0.2 * (1.0 if cookie else 0.0))
        step += 1
        if (time.time() - t0) - last_report >= report_every:
            prev = _report(s, world, cells_meta, cell_by_name, held,
                           "parent", time.time() - t0, step, prev)
            history.append((time.time() - t0, prev))
            gate = P.apply_stage_gate(s)   # gradual release on measured mastery
            if gate["advanced"]:
                print(f"   [parent] GRADUAL RELEASE -> stage {gate['unlocked_stage']}; "
                      f"open {gate['open']}", flush=True)
            last_report = time.time() - t0
    prev = _report(s, world, cells_meta, cell_by_name, held, "parent",
                   time.time() - t0, step, prev)
    history.append((time.time() - t0, prev))
    return history


# ---------------------------------------------------------------------------
# The comparison + verdict.
# ---------------------------------------------------------------------------

def _mean_curve(history, cells):
    return [(t, float(np.mean([snap.get(n, 0.0) for n in cells])))
            for t, snap in history]


def _verdict(self_hist, parent_hist):
    cells = sorted(set().union(*[set(s) for _, s in self_hist],
                               *[set(s) for _, s in parent_hist]))
    self_curve = _mean_curve(self_hist, cells)
    parent_curve = _mean_curve(parent_hist, cells)
    print("\n" + "=" * 68, flush=True)
    print("VERDICT — does the PARENT (ZPD + ostensive naming) help vs self-pick?",
          flush=True)
    print("=" * 68, flush=True)
    print("  HELD-OUT mean cookie-rate (SAME ungameable full-lexicon probe):",
          flush=True)
    print("    self-pick: " +
          "  ".join(f"{t:.0f}s={r:.3f}" for t, r in self_curve), flush=True)
    print("    parent   : " +
          "  ".join(f"{t:.0f}s={r:.3f}" for t, r in parent_curve), flush=True)
    sp_final = self_curve[-1][1]
    pa_final = parent_curve[-1][1]
    sp_first = self_curve[0][1]
    pa_first = parent_curve[0][1]
    print(f"\n  self-pick : {sp_first:.3f} -> {sp_final:.3f}", flush=True)
    print(f"  parent    : {pa_first:.3f} -> {pa_final:.3f}", flush=True)
    higher = pa_final > sp_final + 1e-6
    # faster = parent reaches self-pick's FINAL level earlier (or higher at matched t)
    print(f"\n  HIGHER held-out at end?  {'YES' if higher else 'no'} "
          f"(parent {pa_final:.3f} vs self {sp_final:.3f}, "
          f"Δ {pa_final - sp_final:+.3f})", flush=True)
    # per-cell breakdown at the end
    print("\n  per-cell held-out at end (self -> parent):", flush=True)
    last_self = self_hist[-1][1]
    last_parent = parent_hist[-1][1]
    for n in cells:
        print(f"    {n:24s} {last_self.get(n, 0.0):.3f} -> "
              f"{last_parent.get(n, 0.0):.3f}", flush=True)
    # FAIR view: the parent's gradual release intentionally locks harder cells until
    # mastery, so a whole-grid mean penalises it for cells it deliberately deferred.
    # Compare ALSO on the cells the parent actually REACHED (banked > 0 at end).
    reached = [n for n in cells if last_parent.get(n, 0.0) > 0.0]
    if reached:
        rs = float(np.mean([last_self.get(n, 0.0) for n in reached]))
        rp = float(np.mean([last_parent.get(n, 0.0) for n in reached]))
        print(f"\n  on REACHED cells only {sorted(reached)}:", flush=True)
        print(f"    self {rs:.3f}  vs  parent {rp:.3f}  "
              f"(Δ {rp - rs:+.3f})", flush=True)
    print(f"\n  => {'PARENT HELPS (taught beats babble on the honest yardstick)' if higher else 'no benefit on the WHOLE-GRID held-out yardstick (report honestly)'}",
          flush=True)
    return {"self_curve": self_curve, "parent_curve": parent_curve,
            "cells": cells, "higher": higher,
            "self_final": sp_final, "parent_final": pa_final,
            "per_cell_self": last_self, "per_cell_parent": last_parent}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seconds", type=int, default=300)
    ap.add_argument("--report-every", type=float, default=60.0)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--free-play-frac", type=float, default=0.25)
    ap.add_argument("--no-ids", action="store_true",
                    help="parent does NOT add IDS-register exemplars (isolate the "
                         "ZPD+ostensive lever from the register effect)")
    ap.add_argument("--no-bank-on-miss", action="store_true",
                    help="parent uses the SAME cookie/first-sight banking as self-pick "
                         "(isolate the curriculum lever from the banking policy)")
    ap.add_argument("--no-recasts", action="store_true",
                    help="ABLATE move 1: parent does NOT recast the correct word")
    ap.add_argument("--no-register-gate", action="store_true",
                    help="ABLATE move 2: parent always speaks IDS (no IDS->ADS gate)")
    ap.add_argument("--scaled", action="store_true",
                    help="move 3: add a LARGER TVTropes WORD lexicon grid")
    ap.add_argument("--lexicon-size", type=int, default=40,
                    help="number of words in the scaled WORD lexicon")
    ap.add_argument("--parent-only", action="store_true",
                    help="run ONLY the FULL PARENT in the scaled world (the long live "
                         "run), no A/B — the taught dyad as the agent's environment")
    ap.add_argument("--out", default="/tmp/parent_ab.json")
    args = ap.parse_args()
    if args.parent_only:
        print("=" * 68, flush=True)
        print(f"FULL PARENT — LIVE RUN in the scaled world  seconds={args.seconds}  "
              f"report_every={args.report_every}s  lexicon={args.lexicon_size}  "
              f"recasts={not args.no_recasts}  register_gate={not args.no_register_gate}",
              flush=True)
        print("  (the taught dyad as the agent's environment: ZPD + ostensive + "
              "recasts + IDS->ADS register-gating + gradual release)", flush=True)
        print("=" * 68, flush=True)
        ph = run_parent(args.seconds, args.report_every, seed=args.seed,
                        free_play_frac=args.free_play_frac,
                        use_ids=not args.no_ids,
                        bank_on_miss=not args.no_bank_on_miss,
                        use_recasts=not args.no_recasts,
                        register_gate=not args.no_register_gate,
                        scaled=True, lexicon_size=args.lexicon_size)
        with open(args.out, "w") as f:
            json.dump({"parent_hist": ph}, f, indent=2)
        print(f"\n[done] full-parent live history -> {args.out}", flush=True)
        print("[MARKER] PARENT_LIVE_COMPLETE", flush=True)
        return
    print("=" * 68, flush=True)
    print(f"PARENT vs SELF-PICK  seconds={args.seconds} (each regime)  "
          f"report_every={args.report_every}s  free_play={args.free_play_frac}  "
          f"scaled={args.scaled} (lex={args.lexicon_size})  "
          f"recasts={not args.no_recasts}  register_gate={not args.no_register_gate}",
          flush=True)
    print("=" * 68, flush=True)

    print("\n##### REGIME A: SELF-PICK BABBLE #####", flush=True)
    self_hist = run_selfpick(args.seconds, args.report_every, seed=args.seed,
                             scaled=args.scaled, lexicon_size=args.lexicon_size)
    print("\n##### REGIME B: FULL PARENT (ZPD + ostensive + recasts + reg-gate) #####",
          flush=True)
    parent_hist = run_parent(args.seconds, args.report_every, seed=args.seed,
                             free_play_frac=args.free_play_frac,
                             use_ids=not args.no_ids,
                             bank_on_miss=not args.no_bank_on_miss,
                             use_recasts=not args.no_recasts,
                             register_gate=not args.no_register_gate,
                             scaled=args.scaled, lexicon_size=args.lexicon_size)

    res = _verdict(self_hist, parent_hist)
    with open(args.out, "w") as f:
        json.dump({"self_hist": self_hist, "parent_hist": parent_hist,
                   "verdict": {k: v for k, v in res.items()
                               if k != "per_cell_self" and k != "per_cell_parent"}},
                  f, indent=2)
    print(f"\n[done] curves -> {args.out}", flush=True)
    print("[MARKER] PARENT_AB_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
