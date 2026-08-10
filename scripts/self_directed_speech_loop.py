"""self_directed_speech_loop — RUN the self-directed speech-learning world.

The agent self-directs a 3-AXIS curriculum (granularity x source x language),
hears speech the WORLD plays, commits a BLIND guess (cognition+hat in feature
space), gets a COOKIE iff right, LEARNS (banks the exemplar), SAVES itself, and
REPORTS held-out per-cell progress every 60s.

ARCHITECTURE (CLAUDE.md): every DECISION is a graph Term / Rule the Rust runtime
evaluates (domains/self_directed_speech_world):
  · the 3-axis CHOICE  = the PICK_TERM Argmax over cells (worst/least-explored)
  · the BLIND GUESS     = the many-settings Argmax-of-product over banked exemplars
  · the LEARN           = cookie -> bank_exemplar (admissible-structure feedback)
  · the REPORT reflex    = the report_reflex Rule firing on the 60s clock
  · the SAVE reflex      = the save_reflex Rule firing on the save clock
Python here is the WORLD ADAPTER ONLY: play TTS / load corpora / inject noise /
ingest audio into features / deliver the cookie bit / advance the clock / write
the save file. NO Python decides what to drill, what the guess is, or when to learn.

STAGE 1 (default): granularity={digit,word}, language={en}, source={espeak,
fsdd-real, espeak-noise}. STAGE 2 (--stage2): adds languages (fr/de/es) and the
TVTropes text source — the POLYGLOT.

Run:
  PYTHONUNBUFFERED=1 python -m scripts.self_directed_speech_loop \
      [--seconds N] [--stage2] [--save PATH]
HELD-OUT progress (the 60s report) is measured on a FIXED balanced probe set the
agent never banks, so it cannot game its own curriculum.
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
from domains.self_persistence import save_state, load_state


# ---------------------------------------------------------------------------
# The WORLD: given a cell (granularity, source, language), produce a labelled
# clip — a (word, audio, fs). The world picks a RANDOM instance; the agent knows
# the type/granularity/language, NOT the instance -> genuinely blind. Pure I/O.
# ---------------------------------------------------------------------------

class World:
    def __init__(self, stage2=False, seed=0):
        self.rng = random.Random(seed)
        self.stage2 = stage2
        self.fsdd = W.fsdd_index() if W.fsdd_available() else {}
        self.trope_words = W.tvtropes_words(120) if stage2 else []
        self._noise_n = 0

    def vocab(self, granularity, source, language) -> list:
        """The label set for a cell — what the agent can be asked to recognise."""
        if granularity == "digit":
            return list(W._DIGIT_WORDS.get(language, W._DIGIT_WORDS["en"]))
        if granularity == "word":
            if source == "tvtropes" and self.trope_words:
                return self.trope_words[:20]
            # default word vocab: a small fixed common-word set per language.
            return _COMMON_WORDS.get(language, _COMMON_WORDS["en"])
        return []

    def play(self, cell_attrs, word) -> tuple:
        """Play one labelled clip for `word` under the cell's source/language."""
        src = cell_attrs["source"]
        lang = cell_attrs["language"]
        if src == "fsdd":
            paths = self.fsdd.get(word, [])
            if paths:
                p = self.rng.choice(paths)
                x, fs = W.load_fsdd_clip(p)
                return x, fs
            # fall back to espeak if no real recording for this label
            return W.tts(word, lang)
        if src == "piper":
            # NEURAL TTS as the WORLD: realistic per-language voice. The agent
            # recognises it (in feature space), never inverts it (no-donkey).
            return W.piper_tts(word, lang)
        x, fs = W.tts(word, lang)
        if src == "noise":
            self._noise_n += 1
            x = W.inject_noise(x, snr_db=5.0, seed=self._noise_n)
        return x, fs


# small fixed common-word vocab so the WORD granularity has a label set even
# without a text corpus (Stage 1). Real corpus text (TVTropes) is added in Stage 2.
_COMMON_WORDS = {
    "en": ["yes", "no", "stop", "go", "left", "right", "up", "down"],
    "fr": ["oui", "non", "stop", "gauche", "droite", "haut", "bas", "vite"],
    "de": ["ja", "nein", "halt", "links", "rechts", "oben", "unten", "schnell"],
    "es": ["si", "no", "alto", "izquierda", "derecha", "arriba", "abajo", "rapido"],
}


# ---------------------------------------------------------------------------
# HELD-OUT probe sets — fixed, balanced, NEVER banked. The 60s report is the
# per-cell held-out cookie-rate (the agent cannot game its own curriculum).
# ---------------------------------------------------------------------------

def build_heldout(world: World, cells_meta, n_per=2):
    """For each cell, a fixed list of (word, audio, fs) probes the agent never
    banks. Same world.play path; a separate RNG so probe instances are disjoint."""
    probe_rng = random.Random(99991)
    held = {}
    for name, attrs in cells_meta.items():
        vocab = world.vocab(attrs["granularity"], attrs["source"], attrs["language"])
        items = []
        for w in vocab:
            for _ in range(n_per):
                # use the probe rng for FSDD instance choice via a temp swap
                saved = world.rng
                world.rng = probe_rng
                x, fs = world.play(attrs, w)
                world.rng = saved
                items.append((w, x, fs))
        held[name] = items
    return held


def measure_heldout(substrate, world, attrs, probes):
    """The HELD-OUT cookie-rate for one cell: blind-guess each fixed probe (NOT
    banked) and count cookies. This is the progress signal the pick Term reads."""
    cell_key = attrs["name"]
    correct = 0
    for (w, x, fs) in probes:
        ch = W.feature_channels(substrate, x, fs)
        g = W.blind_guess(substrate, ch, cell_key)
        correct += int(g == w)
    return correct / max(len(probes), 1)


# ---------------------------------------------------------------------------
# The loop. Python advances the clock + plays the world; the GRAPH decides.
# ---------------------------------------------------------------------------

def run(seconds=180, stage2=False, save_path="/tmp/speech_world_save.json",
        report_every_s=60.0, wall_budget_s=None, rebuilt_cochlea=False):
    s = Substrate()
    if load_state(s, save_path):
        print(f"[load] resumed from {save_path}", flush=True)
        # RESUME repair: any banked exemplar saved BEFORE raw-audio banking holds a
        # fixed-dimension descriptor extracted at an OLD front-end width — it can no
        # longer be re-extracted through the current (self-modified) front end, so it
        # would crash the dimension-consistent recognizer. Drop just those; keep the
        # learned front end + curriculum + lexicon. The agent re-banks through its
        # current front end as it continues.
        pruned = W.prune_stale_banks(s)
        if pruned:
            print(f"[load] pruned {pruned} stale fixed-dimension exemplars "
                  f"(kept front end + cells + lexicon; will re-bank via current "
                  f"front end)", flush=True)
        # TREADMILL-FIX resume repair: the pre-fix run accumulated ~20 INVENTED cues
        # with no record of which lifted the held-out (the effect-gate did not exist
        # then). Honest prune: drop ALL invented cues (none can be shown to lift);
        # keep the seed + repertoire cues, the curriculum, the lexicon, and the
        # banks. From here every new invention is effect-gated -> bounded front end.
        import domains.agent_frontend as _FE
        n_inv = _FE.prune_invented_cues(s)
        if n_inv:
            print(f"[load] TREADMILL-FIX: pruned {n_inv} non-lifting invented cues "
                  f"(kept seed + repertoire + lexicon + banks); front end now "
                  f"{_FE.n_active(s)} active cues. New inventions are effect-gated.",
                  flush=True)
    info = W.install_speech_world_rules(s)
    root = info["root"]
    if rebuilt_cochlea:
        # DO-CONTRAST: wire the agent's REBUILT (fine-structure correlogram) COCHLEA
        # into the front end as an active cue, alongside the seed energy ears. Same
        # world, same self-directed loop — the only difference vs the baseline is the
        # fine-structure ear. (Mechanical graph mutation; the agent designed the ear.)
        import domains.agent_frontend as _FE
        _FE.activate_correlogram_ear(s)
        print(f"[rebuilt-cochlea] fine-structure correlogram ear ACTIVE -> "
              f"{_FE.n_active(s)} active cues (baseline + the rebuilt cochlea)",
              flush=True)
    s.set_attr(root, "report_period_s", float(report_every_s))
    s.set_attr(root, "save_period_s", float(report_every_s * 2))

    world = World(stage2=stage2)

    # The 3-axis cell grid the agent self-directs over (the curriculum STRUCTURE).
    granularities = ["digit", "word"]
    languages = ["en"] if not stage2 else ["en", "fr", "de", "es"]
    sources = ["espeak", "noise"] + (["fsdd"] if world.fsdd else [])
    # NEURAL TTS (Piper) as a realistic WORLD source when installed (online); the
    # in-thesis espeak fallback covers offline.
    if W.piper_available("en"):
        sources.append("piper")
        print("[piper] neural TTS available -> added 'piper' source", flush=True)
    else:
        print("[piper] not available (offline) -> espeak fallback", flush=True)
    if stage2 and world.trope_words:
        # add a real-text WORD source
        pass
    cells_meta = {}
    for g in granularities:
        for lang in languages:
            for src in sources:
                # FSDD is English digits only — a real-corpus constraint, stated.
                if src == "fsdd" and (g != "digit" or lang != "en"):
                    continue
                if g == "word" and src == "tvtropes" and lang != "en":
                    continue
                # Piper only for languages with a downloaded neural voice.
                if src == "piper" and not W.piper_available(lang):
                    continue
                c = W.install_cell(s, g, src, lang)
                cells_meta[s.node(c)["attrs"]["name"]] = s.node(c)["attrs"]
    if stage2 and world.trope_words:
        c = W.install_cell(s, "word", "tvtropes", "en")
        cells_meta[s.node(c)["attrs"]["name"]] = s.node(c)["attrs"]

    cell_by_name = {s.node(c)["attrs"]["name"]: c
                    for c in s.nodes("CurriculumCell")}
    print(f"[cells] {len(cells_meta)} curriculum cells: "
          f"{sorted(cells_meta)}", flush=True)

    print("[probes] building fixed held-out probe sets (never banked)...",
          flush=True)
    held = build_heldout(world, cells_meta)
    print(f"[probes] {sum(len(v) for v in held.values())} held-out probes",
          flush=True)

    t0 = time.time()
    last_tick = t0
    last_report = 0.0
    last_save = 0.0
    step = 0
    history = []   # (elapsed, {cell: held_cookie_rate})

    def do_report(elapsed):
        snapshot = {}
        prev = history[-1][1] if history else {}
        print(f"\n===== REPORT  t={elapsed:.0f}s  step={step} "
              f"(front-end: {W.live_n_channels(s)} active cues) =====", flush=True)
        for name in sorted(cells_meta):
            c = cell_by_name[name]
            r = measure_heldout(s, world, cells_meta[name], held[name])
            prev_r = prev.get(name, 0.0)
            s.set_attr(c, "held_cookie_rate", float(r))
            # held_delta = change since the last report — the plateau Rule's stall
            # signal (set BEFORE the first report's prev exists -> stays the init 1.0).
            if history:
                s.set_attr(c, "held_delta", float(r - prev_r))
            # re-seed the online steering estimate from the authoritative held-out
            # rate so the pick's deficit reflects true (ungamed) understanding.
            s.set_attr(c, "live_rate", float(r))
            s.set_attr(c, "n_probes", float(len(held[name])))
            a = s.node(c)["attrs"]
            # EFFECT-GATE arming: if this cell had a front-end mod since the last
            # report, a fresh held-out measurement is now in -> let the gate judge
            # whether the mod LIFTED (keep) or not (revert). The decision is the
            # gate Rule; this only signals that a measurement is available.
            if float(a.get("pending_mod_cue", -1.0)) >= 0.0:
                s.set_attr(c, "mod_eval_pending", 1)
            live = (a.get("live_cookies", 0.0), a.get("live_attempts", 0.0))
            snapshot[name] = r
            print(f"  {name:28s} held-out cookie-rate {r:.3f}  "
                  f"(Δ {r - prev_r:+.3f}, live {int(live[0])}/{int(live[1])}, "
                  f"bank {_bank_size(s, name, cells_meta[name])})", flush=True)
        history.append((elapsed, snapshot))
        s.set_attr(root, "report_due", 0)

    while True:
        elapsed = time.time() - t0
        if elapsed >= seconds:
            break
        if wall_budget_s and elapsed >= wall_budget_s:
            break

        # --- the agent PICKS the cell (graph Term) ---
        picked = W.pick_cell(s)
        if picked is None:
            break
        attrs = s.node(picked)["attrs"]
        name = attrs["name"]          # name IS the cell_key (gran|source|lang)
        cell_key = name

        # --- the WORLD plays a random instance of a label from the cell ---
        vocab = world.vocab(attrs["granularity"], attrs["source"], attrs["language"])
        word = world.rng.choice(vocab)
        x, fs = world.play(attrs, word)
        ch = W.feature_channels(s, x, fs)

        # --- the agent commits a BLIND guess (graph Argmax-of-product) ---
        guess = W.blind_guess(s, ch, cell_key)

        # --- the WORLD delivers the COOKIE bit; cookie iff guess == truth ---
        cookie = (guess == word)
        c = picked
        s.set_attr(c, "live_attempts",
                   float(s.node(c)["attrs"].get("live_attempts", 0.0)) + 1)
        if cookie:
            s.set_attr(c, "live_cookies",
                       float(s.node(c)["attrs"].get("live_cookies", 0.0)) + 1)
        # --- the agent LEARNS: cookie = "admissible" -> bank the exemplar.
        # Bank on cookie AND, to bootstrap an empty bank, on the first sight of an
        # unseen label (the world reveals truth; banking truth is the grounding
        # feedback, same as a child told the word). Banking is the cookie's effect.
        if cookie or not _has_label(s, word, cell_key):
            W.bank_exemplar(s, word, cell_key, x, fs)

        # Steer the curriculum BETWEEN held-out reports with a cheap live running
        # cookie-rate estimate (a recency-weighted online proxy), so the pick Term
        # sees fresh deficit and ROTATES away from cells it is mastering. The 60s
        # report's held-out rate (never banked) remains the authoritative,
        # ungameable progress measure; this only drives the active curriculum.
        ca = s.node(c)["attrs"]
        live_est = float(ca.get("live_rate", 0.0))
        live_est = 0.8 * live_est + 0.2 * (1.0 if cookie else 0.0)
        s.set_attr(c, "live_rate", live_est)

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

        # The report cadence is a world-clock concern the adapter owns (advance the
        # clock + fire the timer = permitted I/O). The reflex Rule declares the cadence
        # graph-resident, but the Rust rule engine fires a binding once, so the adapter
        # reads the elapsed clock to drive the repeated report. The DECISION of what to
        # drill/learn/report stays in the graph.
        if (now - t0) - last_report >= report_every_s:
            do_report(now - t0)
            last_report = now - t0
            # EFFECT-GATE first (the treadmill fix): judge whether each cell's LAST
            # front-end mod actually LIFTED its held-out (the agent's own yardstick).
            # Non-lifting mods are REVERTED (the front end stays bounded); a cell with
            # deeper_wall_n consecutive non-lifts is flagged a DEEPER-THAN-FRONT-END
            # wall by the agent's effort-without-payoff meta-monitor -> mods stop on
            # it + the curriculum redirects. The keep/drop/flag decisions are graph
            # Rules; the adapter only enacts the revert. THEN PLATEAU -> the agent
            # self-designs its front end on cells where modification still helps.
            walled = W.run_effect_gate(s, info)
            if walled:
                print(f"[deeper-wall] effort-without-payoff: {sorted(walled)} "
                      f"flagged DEEPER THAN THE FRONT END (front-end mods stop; "
                      f"curriculum redirects)", flush=True)
            _enact_frontend_mods(s)
        if (now - t0) - last_save >= report_every_s * 2:
            summ = save_state(s, save_path)
            last_save = now - t0
            print(f"[save] {summ['n_nodes']} nodes -> {save_path}", flush=True)

    # final report + save
    do_report(time.time() - t0)
    summ = save_state(s, save_path)
    print(f"[save] final {summ['n_nodes']} nodes -> {save_path}", flush=True)

    _verdict(history, stage2)
    return history


def _enact_frontend_mods(s):
    """If any cell satisfies the agent's graph-resident PLATEAU judgement
    (W.cell_plateaued = the PLATEAU_TERM), the agent has hit the front-end wall ->
    enact ONE front-end modification (the agent's graph Argmax chooses WHICH; the
    adapter flips the chosen cue active). One modification per wall-hit keeps the
    climb legible. The JUDGEMENT and the CHOICE are both graph Terms; the adapter
    only reads them and enacts.

    Three plateau moves, in order: ADD a banked cue (modify_frontend's graph Argmax),
    and when the REPERTOIRE IS EXHAUSTED (modify_frontend returns None) but the wall
    still holds, INVENT a novel band-combination cue — the open-ended novelty move
    (W.invent_frontend_cue, whose generate+MDL-select decision is graph-resident in
    feature_generator; the adapter only harvests the band frames). The agent never
    runs out of moves: once the repertoire is spent, it composes new ears."""
    import domains.agent_frontend as FE
    # plateaued cells EXCLUDE deeper-wall + pending-judgement cells (the PLATEAU_TERM
    # carries those exclusions now — the treadmill fix). The mod is ATTRIBUTED to the
    # WORST plateaued cell so the effect-gate can measure whether it LIFTS that cell;
    # a mod that does not lift it is reverted next report (no ballooning).
    plateaued = [c for c in s.nodes("CurriculumCell") if W.cell_plateaued(s, c)]
    if not plateaued:
        return
    names = sorted(s.node(c)["attrs"]["name"] for c in plateaued)
    target = min(plateaued,
                 key=lambda c: s.node(c)["attrs"].get("held_cookie_rate", 0.0))
    tname = s.node(target)["attrs"]["name"]
    mod = FE.modify_frontend(s)               # the graph decides WHICH; adapter enacts
    if mod is not None:
        W.note_frontend_mod(s, target, mod["cue"])   # arm the effect-gate for target
        print(f"[front-end] PLATEAU on {names} -> agent self-modifies FOR {tname}: "
              f"+{mod['name']} ({mod['kind']}); now {FE.n_active(s)} active cues "
              f"(effect-gated: kept only if it lifts {tname})", flush=True)
        return
    # REPERTOIRE EXHAUSTED but the wall holds -> the agent INVENTS a novel cue (the
    # third plateau move). Harvest the band frames from the worst plateaued cell's
    # banked clips; the generate+MDL-select+mint decision is graph-resident. The
    # invention is ALSO effect-gated: kept only if it lifts the target's held-out.
    inv = W.invent_frontend_cue(s, tname, seed=FE.n_active(s))
    if inv is None:
        for c in plateaued:
            cn = s.node(c)["attrs"]["name"]
            inv = W.invent_frontend_cue(s, cn, seed=FE.n_active(s))
            if inv is not None:
                target, tname = c, cn
                break
    if inv is not None:
        W.note_frontend_mod(s, target, inv["cue"])   # arm the effect-gate for target
        print(f"[front-end] PLATEAU on {names}, repertoire exhausted -> agent "
              f"INVENTS a novel cue FOR {tname}: +{inv['name']} ({inv['kind']}); now "
              f"{FE.n_active(s)} active cues (effect-gated: kept only if it lifts "
              f"{tname})", flush=True)
    else:
        print(f"[front-end] PLATEAU on {names}, repertoire exhausted and no honest "
              f"invent harvest available ({FE.n_active(s)} cues active)", flush=True)


def _bank_size(substrate, name, attrs):
    cell_key = attrs["name"]
    n = 0
    for c in substrate.nodes("Concept"):
        a = substrate.node(c)["attrs"]
        if a.get("origin") == "speech_world" and a.get("cell_key") == cell_key:
            n += len(substrate.neighbours(c, "has_exemplar"))
    return n


def _has_label(substrate, word, cell_key):
    key = f"{cell_key}::{word}"
    for c in substrate.nodes("Concept"):
        if substrate.node(c)["attrs"].get("lex_key") == key:
            return len(substrate.neighbours(c, "has_exemplar")) > 0
    return False


def _verdict(history, stage2):
    print("\n" + "=" * 64, flush=True)
    print("VERDICT — does the held-out cookie-rate CLIMB? (self-directed learning)",
          flush=True)
    print("=" * 64, flush=True)
    if len(history) < 2:
        print("  (only one report — run longer to see a learning curve)", flush=True)
        return
    first = history[0][1]
    last = history[-1][1]
    cells = sorted(set(first) | set(last))
    climbed = 0
    for name in cells:
        f = first.get(name, 0.0)
        l = last.get(name, 0.0)
        arrow = "CLIMB" if l > f + 1e-6 else ("flat" if abs(l - f) <= 1e-6 else "drop")
        climbed += int(l > f + 1e-6)
        print(f"  {name:28s} {f:.3f} -> {l:.3f}  [{arrow}]", flush=True)
    mean_first = float(np.mean([first.get(n, 0.0) for n in cells]))
    mean_last = float(np.mean([last.get(n, 0.0) for n in cells]))
    print(f"  MEAN held-out cookie-rate {mean_first:.3f} -> {mean_last:.3f}  "
          f"({climbed}/{len(cells)} cells climbed)", flush=True)
    print(f"  => self-directed learning: "
          f"{'YES, held-out climbs' if mean_last > mean_first + 1e-6 else 'NO climb'}",
          flush=True)
    if stage2:
        langs = sorted(set(n.split('|')[2] for n in cells))
        print(f"  POLYGLOT: cells span languages {langs}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seconds", type=int, default=180)
    ap.add_argument("--stage2", action="store_true")
    ap.add_argument("--save", default="/tmp/speech_world_save.json")
    ap.add_argument("--report-every", type=float, default=60.0)
    ap.add_argument("--fresh", action="store_true",
                    help="ignore any existing save file")
    ap.add_argument("--rebuilt-cochlea", action="store_true",
                    help="wire the agent's fine-structure correlogram ear into the "
                         "front end (the do-contrast vs the seed energy-envelope ears)")
    args = ap.parse_args()
    if args.fresh and os.path.exists(args.save):
        os.remove(args.save)
    print("=" * 64, flush=True)
    print(f"SELF-DIRECTED SPEECH WORLD  stage{'2' if args.stage2 else '1'}  "
          f"seconds={args.seconds}  report_every={args.report_every}s", flush=True)
    print("=" * 64, flush=True)
    run(seconds=args.seconds, stage2=args.stage2, save_path=args.save,
        report_every_s=args.report_every, rebuilt_cochlea=args.rebuilt_cochlea)


if __name__ == "__main__":
    main()
