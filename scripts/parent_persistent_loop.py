"""parent_persistent_loop — the PARENT integrated into the PERSISTENT main loop.

The long --parent-only A/B run (scripts/parent_speech_loop) was EPHEMERAL: both
regimes start fresh, no save/resume, and the bank was UNBOUNDED — a 40 min run
banked ~6480 espeak exemplars and was reaped (OOM) with everything lost. This loop
fixes that by integrating the PARENT into the persistent self-directed loop:

  · SAVE / RESUME via graph_to_dict (survives kills, persists across runs) — the
    agent's front end, curriculum, lexicon and (capped) banks reload from the save.
  · The PARENT's decisions stay GRAPH Terms/Rules (CLAUDE.md): the ZPD pick
    (P.ZPD_PICK_TERM), the register gate (P.REGISTER_GATE_TERM), the stage gate
    (mastery = the agent's held-out rate), ostensive naming (restricted competitor
    set), and recasts. The Python loop only ingests/emits/ticks/saves.
  · BANK CAP (world-adapter banking mechanics): W.cap_bank bounds per-(word, cell)
    exemplars to --bank-cap (default 200) most-recent, so memory is BOUNDED — no
    unbounded growth, no OOM.
  · LOSO PROBE (cross-speaker): alongside the existing clip-holdout FSDD probe
    (seen speakers, held-out clips) we add a LEAVE-ONE-SPEAKER-OUT probe — whole
    FSDD speakers are held out; the agent NEVER banks their clips (the run world's
    FSDD pool is restricted to TRAIN speakers). Each report shows BOTH
    digit|fsdd|en (seen-speaker) AND digit|fsdd|en LOSO (cross-speaker, the ~0.44
    wall). This measures whether the parent's teaching crosses speaker-invariance
    or only seen-speaker recognition.

THE DONKEY BOUNDARY (policed): the PARENT speaks / names / recasts / picks-level /
gates-register; it NEVER recognises. The agent's blind_guess over its own exemplars
is the recognizer. BOTH held-out probes are FULL-lexicon (restrict_to=None),
ungameable; the LOSO probe's speakers' clips are never banked.

Run:
  PYTHONUNBUFFERED=1 python -m scripts.parent_persistent_loop \
      [--seconds N] [--report-every S] [--save PATH] [--bank-cap N] \
      [--lexicon-size K] [--loso-speaker NAME] [--fresh]
"""
from __future__ import annotations

import argparse
import os
import random
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate_rs import Substrate
import domains.self_directed_speech_world as W
import domains.parent_teacher as P
from domains.self_persistence import save_state, load_state
from scripts.self_directed_speech_loop import (build_heldout, measure_heldout,
                                               _has_label, _bank_size,
                                               _enact_frontend_mods)
from scripts.parent_speech_loop import ScaledWorld


# ---------------------------------------------------------------------------
# LOSO world: the run's FSDD pool is restricted to TRAIN speakers, so the agent
# can NEVER bank a held-out speaker's clip. The held-out speaker(s) feed only the
# cross-speaker probe (built separately, below). Everything else is the scaled
# world adapter unchanged (a wider TVTropes WORD lexicon + the digit grid).
# ---------------------------------------------------------------------------

class LosoWorld(ScaledWorld):
    def __init__(self, lexicon_size=40, seed=0, loso_speakers=None):
        super().__init__(lexicon_size=lexicon_size, seed=seed)
        # restrict the playable/bankable FSDD pool to the TRAIN speakers (everything
        # except the held-out LOSO speakers). The held-out speakers' clips are never
        # in self.fsdd, so world.play / build_heldout can only ever draw TRAIN clips.
        self.loso_speakers = sorted(loso_speakers or [])
        if self.fsdd and self.loso_speakers:
            all_spk = W.fsdd_speakers()
            train_spk = [s for s in all_spk if s not in set(self.loso_speakers)]
            self.fsdd = W.fsdd_index_for(train_spk)
            self.train_speakers = train_spk
        else:
            self.train_speakers = W.fsdd_speakers()


def build_loso_probe(loso_speakers, n_per=4, seed=99993):
    """The CROSS-SPEAKER held-out probe: clips spoken by the HELD-OUT speakers, which
    the agent never banks (they are absent from the run world's FSDD pool). Returns a
    list of (word, audio, fs) for the digit|fsdd|en cell. Pure probe construction
    (world-adapter mechanics) — the held-out speakers' clips test speaker-invariant
    recognition the agent was never grounded on."""
    idx = W.fsdd_index_for(loso_speakers)
    rng = random.Random(seed)
    probes = []
    for w in W._DIGIT_WORDS["en"]:
        paths = idx.get(w, [])
        if not paths:
            continue
        rng.shuffle(paths)
        for p in paths[:n_per]:
            x, fs = W.load_fsdd_clip(p)
            probes.append((w, x, fs))
    return probes


def run(seconds, report_every_s=60.0, save_path="/tmp/parent_persistent_save.json",
        bank_cap=200, lexicon_size=40, loso_speakers=None,
        free_play_frac=0.25, competitor_k=4, seed=0):
    s = Substrate()
    resumed = load_state(s, save_path)
    if resumed:
        print(f"[load] resumed from {save_path}", flush=True)
        pruned = W.prune_stale_banks(s)
        if pruned:
            print(f"[load] pruned {pruned} stale fixed-dimension exemplars", flush=True)
        import domains.agent_frontend as _FE
        n_inv = _FE.prune_invented_cues(s)
        if n_inv:
            print(f"[load] pruned {n_inv} non-lifting invented cues; front end now "
                  f"{_FE.n_active(s)} active cues", flush=True)
    info = W.install_speech_world_rules(s)
    root = info["root"]
    s.set_attr(root, "report_period_s", float(report_every_s))
    s.set_attr(root, "save_period_s", float(report_every_s * 2))

    # the LOSO speaker split: hold out whole speakers. Default = the last speaker.
    all_spk = W.fsdd_speakers()
    if loso_speakers is None and all_spk:
        loso_speakers = [all_spk[-1]]
    loso_speakers = sorted(loso_speakers or [])

    world = LosoWorld(lexicon_size=lexicon_size, seed=seed,
                      loso_speakers=loso_speakers)
    if world.fsdd and loso_speakers:
        print(f"[loso] held-out speakers (never banked): {loso_speakers}; "
              f"train speakers: {world.train_speakers}", flush=True)

    # the cell grid: the digit grid + (scaled) a larger TVTropes WORD grid.
    languages = ["en"]
    sources = ["espeak", "noise"] + (["fsdd"] if world.fsdd else [])
    if W.piper_available("en"):
        sources.append("piper")
    granularities = ["digit", "word"]
    cells_meta = {}
    for g in granularities:
        for lang in languages:
            for src in sources:
                if src == "fsdd" and (g != "digit" or lang != "en"):
                    continue
                if src == "piper" and not W.piper_available(lang):
                    continue
                c = W.install_cell(s, g, src, lang)
                cells_meta[s.node(c)["attrs"]["name"]] = s.node(c)["attrs"]
    cell_by_name = {s.node(c)["attrs"]["name"]: c
                    for c in s.nodes("CurriculumCell")}
    print(f"[cells] {len(cells_meta)} curriculum cells: {sorted(cells_meta)}",
          flush=True)

    # install the PARENT (idempotent on a resumed save).
    P.install_parent(s)
    P.apply_stage_gate(s)

    # the two FSDD probes: clip-holdout (seen speakers, held-out clips — built from
    # the TRAIN-speaker pool via build_heldout) and LOSO (held-out speakers).
    held = build_heldout(world, cells_meta, n_per=2)
    fsdd_cell = "digit|fsdd|en"
    loso_probe = (build_loso_probe(loso_speakers, n_per=4)
                  if (world.fsdd and loso_speakers and fsdd_cell in cells_meta)
                  else [])
    n_held = sum(len(v) for v in held.values())
    print(f"[probes] {n_held} clip-holdout probes; {len(loso_probe)} LOSO "
          f"(cross-speaker) probes for {fsdd_cell}", flush=True)

    t0 = time.time()
    last_tick = t0
    last_report = 0.0
    last_save = 0.0
    step = 0
    history = []
    fp_rng = random.Random(seed + 7)

    def do_report(elapsed):
        snapshot = {}
        prev = history[-1][1] if history else {}
        print(f"\n===== REPORT t={elapsed:.0f}s step={step} "
              f"(front-end {W.live_n_channels(s)} cues, bank {W.bank_count(s)}) =====",
              flush=True)
        for name in sorted(cells_meta):
            c = cell_by_name[name]
            r = measure_heldout(s, world, cells_meta[name], held[name])
            prev_r = prev.get(name, 0.0)
            s.set_attr(c, "held_cookie_rate", float(r))
            if history:
                s.set_attr(c, "held_delta", float(r - prev_r))
            s.set_attr(c, "live_rate", float(r))
            s.set_attr(c, "n_probes", float(len(held[name])))
            a = s.node(c)["attrs"]
            if float(a.get("pending_mod_cue", -1.0)) >= 0.0:
                s.set_attr(c, "mod_eval_pending", 1)
            live = (a.get("live_cookies", 0.0), a.get("live_attempts", 0.0))
            snapshot[name] = r
            print(f"  {name:24s} held-out {r:.3f} (Δ {r - prev_r:+.3f}, "
                  f"live {int(live[0])}/{int(live[1])}, "
                  f"bank {_bank_size(s, name, cells_meta[name])})", flush=True)
        # the LOSO cross-speaker probe ALONGSIDE the clip-holdout FSDD cell — the same
        # full-lexicon ungameable blind_guess, on speakers the agent never banked.
        if loso_probe:
            loso_attrs = cells_meta[fsdd_cell]
            lr = measure_heldout(s, world, loso_attrs, loso_probe)
            prev_lr = prev.get("digit|fsdd|en LOSO", 0.0)
            snapshot["digit|fsdd|en LOSO"] = lr
            seen = snapshot.get(fsdd_cell, 0.0)
            print(f"  {'digit|fsdd|en LOSO':24s} held-out {lr:.3f} "
                  f"(Δ {lr - prev_lr:+.3f}, cross-speaker; seen-speaker {seen:.3f})",
                  flush=True)
        history.append((elapsed, snapshot))
        s.set_attr(root, "report_due", 0)

    while True:
        elapsed = time.time() - t0
        if elapsed >= seconds:
            break

        # --- the agent / parent PICKS the cell (graph Terms) ---
        free_play = fp_rng.random() < free_play_frac
        if free_play:
            picked = W.pick_cell(s)            # FREE-PLAY: the agent self-directs
        else:
            picked = P.zpd_pick_cell(s)        # the PARENT picks at the agent's ZPD
        if picked is None:
            picked = W.pick_cell(s)
        if picked is None:
            break
        attrs = s.node(picked)["attrs"]
        cell_key = attrs["name"]
        vocab = world.vocab(attrs["granularity"], attrs["source"], attrs["language"])
        word = world.rng.choice(vocab)
        x, fs = world.play(attrs, word)

        if free_play:
            restrict = None
        else:
            # OSTENSIVE NAMING: restricted competitor set (the label is the learning
            # TARGET, not the guess-time answer — the agent still recognises).
            restrict = P.competitor_set(vocab, word, k=competitor_k, rng=fp_rng)

        ch = W.feature_channels(s, x, fs)
        guess = W.blind_guess(s, ch, cell_key, restrict_to=restrict)
        cookie = (guess == word)
        s.set_attr(picked, "live_attempts",
                   float(attrs.get("live_attempts", 0.0)) + 1)
        if cookie:
            s.set_attr(picked, "live_cookies",
                       float(s.node(picked)["attrs"].get("live_cookies", 0.0)) + 1)

        # REGISTER-GATING: the parent's register for this clip is the graph Term
        # (IDS while far from mastery, ADS as mastered). Decision = the Term.
        register = P.gated_register(s, picked)
        if free_play:
            if cookie or not _has_label(s, word, cell_key):
                W.bank_exemplar(s, word, cell_key, x, fs)
        else:
            # ostensive naming: the label is given -> bank the world clip as the
            # learning target (a child told the word banks it); add the register-gated
            # IDS/ADS exemplar; recast the correct form.
            W.bank_exemplar(s, word, cell_key, x, fs)
            ids_x, ids_fs = P.parent_say(word, attrs["language"], register=register)
            W.bank_exemplar(s, word, cell_key, ids_x, ids_fs)
            P.bank_recast(s, word, cell_key, attrs["language"],
                          register=register, guess=guess, guess_clip=None)

        ca = s.node(picked)["attrs"]
        s.set_attr(picked, "live_rate",
                   0.8 * float(ca.get("live_rate", 0.0))
                   + 0.2 * (1.0 if cookie else 0.0))
        step += 1

        # --- advance the clock + tick -> the report/save reflex Rules fire ---
        now = time.time()
        s.set_attr(root, "secs_since_report",
                   float(s.node(root)["attrs"].get("secs_since_report", 0.0))
                   + (now - last_tick))
        s.set_attr(root, "secs_since_save",
                   float(s.node(root)["attrs"].get("secs_since_save", 0.0))
                   + (now - last_tick))
        last_tick = now
        s.tick(20000)

        if (now - t0) - last_report >= report_every_s:
            do_report(now - t0)
            last_report = now - t0
            # gradual release on measured mastery (the parent's stage gate).
            gate = P.apply_stage_gate(s)
            if gate["advanced"]:
                print(f"   [parent] GRADUAL RELEASE -> stage {gate['unlocked_stage']}; "
                      f"open {gate['open']}", flush=True)
            # the persistent loop's front-end self-design + effect-gate + meta-monitor.
            walled = W.run_effect_gate(s, info)
            if walled:
                print(f"[deeper-wall] effort-without-payoff: {sorted(walled)} "
                      f"flagged DEEPER THAN THE FRONT END", flush=True)
            _enact_frontend_mods(s)
            # BANK CAP: bound per-word exemplars so memory stays flat (no OOM).
            capped = W.cap_bank(s, cap=bank_cap)
            if capped:
                print(f"[bank-cap] pruned {capped} oldest exemplars "
                      f"(cap {bank_cap}/word); bank now {W.bank_count(s)}", flush=True)

        if (now - t0) - last_save >= report_every_s * 2:
            # cap before save so the persisted graph is also bounded.
            W.cap_bank(s, cap=bank_cap)
            summ = save_state(s, save_path)
            last_save = now - t0
            print(f"[save] {summ['n_nodes']} nodes, bank {W.bank_count(s)} "
                  f"-> {save_path}", flush=True)

    # final report + capped save
    do_report(time.time() - t0)
    W.cap_bank(s, cap=bank_cap)
    summ = save_state(s, save_path)
    print(f"[save] final {summ['n_nodes']} nodes, bank {W.bank_count(s)} "
          f"-> {save_path}", flush=True)

    _verdict(history, loso_speakers)
    print("[MARKER] PARENT_PERSISTENT_COMPLETE", flush=True)
    return history


def _verdict(history, loso_speakers):
    print("\n" + "=" * 68, flush=True)
    print("VERDICT — does the PARENT lift SEEN-SPEAKER and/or CROSS-SPEAKER (LOSO)?",
          flush=True)
    print("=" * 68, flush=True)
    if len(history) < 2:
        print("  (only one report — run longer to see a learning curve)", flush=True)
        return
    first, last = history[0][1], history[-1][1]
    cells = sorted(set(first) | set(last))
    for name in cells:
        f, l = first.get(name, 0.0), last.get(name, 0.0)
        arrow = "CLIMB" if l > f + 1e-6 else ("flat" if abs(l - f) <= 1e-6 else "drop")
        print(f"  {name:24s} {f:.3f} -> {l:.3f}  [{arrow}]", flush=True)
    seen0, seen1 = first.get("digit|fsdd|en", 0.0), last.get("digit|fsdd|en", 0.0)
    loso0, loso1 = (first.get("digit|fsdd|en LOSO", 0.0),
                    last.get("digit|fsdd|en LOSO", 0.0))
    print(f"\n  FSDD seen-speaker (clip-holdout): {seen0:.3f} -> {seen1:.3f}",
          flush=True)
    print(f"  FSDD cross-speaker (LOSO {loso_speakers}): {loso0:.3f} -> {loso1:.3f}",
          flush=True)
    print(f"\n  => Parent crosses the CROSS-SPEAKER wall? "
          f"{'YES (LOSO climbs)' if loso1 > loso0 + 1e-6 else 'NO (LOSO flat/down — teaching lifts only seen-speaker)'}",
          flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seconds", type=int, default=600)
    ap.add_argument("--report-every", type=float, default=60.0)
    ap.add_argument("--save", default="/tmp/parent_persistent_save.json")
    ap.add_argument("--bank-cap", type=int, default=200,
                    help="max exemplars kept per (word, cell) — bounds memory")
    ap.add_argument("--lexicon-size", type=int, default=40)
    ap.add_argument("--loso-speaker", action="append", default=None,
                    help="FSDD speaker name to HOLD OUT (repeatable); default = last")
    ap.add_argument("--free-play-frac", type=float, default=0.25)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--fresh", action="store_true",
                    help="ignore any existing save file")
    args = ap.parse_args()
    if args.fresh and os.path.exists(args.save):
        os.remove(args.save)
    print("=" * 68, flush=True)
    print(f"PARENT PERSISTENT LOOP  seconds={args.seconds}  "
          f"report_every={args.report_every}s  bank_cap={args.bank_cap}  "
          f"lexicon={args.lexicon_size}  save={args.save}", flush=True)
    print("  (the taught dyad integrated into the persistent main loop: ZPD + "
          "ostensive + recasts + IDS->ADS gate + gradual release + save/resume + "
          "bank cap + LOSO probe)", flush=True)
    print("=" * 68, flush=True)
    run(seconds=args.seconds, report_every_s=args.report_every,
        save_path=args.save, bank_cap=args.bank_cap,
        lexicon_size=args.lexicon_size, loso_speakers=args.loso_speaker,
        free_play_frac=args.free_play_frac, seed=args.seed)


if __name__ == "__main__":
    main()
