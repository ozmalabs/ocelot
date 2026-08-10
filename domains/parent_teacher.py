"""parent_teacher — the PARENT for the self-directed speech world (first piece).

The user's correction: *"it isn't all babble."* Real children do not learn by
pure self-directed sampling; they learn inside a DYAD with a caregiver who
SIMPLIFIES (child-directed speech), NAMES the referent (ostensive naming with the
competitors suppressed), and TEACHES AT THE RIGHT LEVEL (Vygotsky's Zone of
Proximal Development, scaffolding with gradual release). This module is the FIRST
and highest-leverage piece of that PARENT, per docs/research_parental_teaching.md
§(4): the ADAPTIVE SCAFFOLDED CURRICULUM + OSTENSIVE NAMING.

WHAT THE PARENT DOES (and only this):
  1. ZPD CURRICULUM — picks the cell at the agent's MEASURED level (just above
     mastered, below too-hard), with gradual release (advance as the agent masters)
     and intensify-on-difficulty. The pick is a GRAPH Term (ZPD_PICK_TERM, an
     Argmax over cells) fed by the agent's OWN held-out measure (held_cookie_rate,
     the ungameable yardstick). The parent only MEASURES the level and exposes it on
     the cells; the DECISION stays a graph Term the agent evaluates.
  2. OSTENSIVE NAMING with a RESTRICTED COMPETITOR SET — when teaching a word the
     parent gives the LABEL (the learning TARGET, banked) AND restricts the agent's
     guess to a few competitors (not the full lexicon). The research's key finding:
     joint attention's real lever is competitor-SUPPRESSION, not pointing. The label
     is NOT the answer at guess time — the agent still RECOGNISES the clip; the label
     is what to bank and the cookie is the feedback.
  3. IDS REGISTER (child-directed speech) — the parent speaks the teaching clip
     SLOWED + PITCHED (espeak -s / -p), the register that measurably aids early word
     learning. Boundary TTS only.

THE DONKEY BOUNDARY (policed here, explicitly):
  · The PARENT may SPEAK (IDS-register TTS), NAME (give the label/competitor set),
    and PICK-LEVEL (the ZPD Argmax over the agent's held-out rate). The PARENT must
    NEVER do RECOGNITION. The agent's grounding/recognition (blind_guess over its
    own exemplars in its own feature space), front end, and the held-out yardstick
    stay the agent's.
  · The ZPD pick is a GRAPH Term fed by the agent's held-out measure — not a Python
    if/else that decides the syllabus (CLAUDE.md).
  · The ostensive label is the LEARNING TARGET (what to bank), NOT the answer at
    guess time. The UNGAMEABLE held-out probe (full lexicon, never restricted) stays
    the yardstick so teaching cannot inflate measured capability.
  · An LLM-as-parent is allowed ONLY as the teacher (speak / name / pick-level via a
    pluggable ask() channel, nothing stored on the agent — the teacher_hook /
    llm_partner shape). It is NEVER the recognizer.

This is a WORLD ADAPTER (CLAUDE.md): Python here translates I/O (IDS TTS params,
the competitor set, the curriculum stage table) and exposes measurements onto the
cells. Every DECISION — the pick, the guess, the learn — is a graph Term / Rule.
"""
from __future__ import annotations

import os
import subprocess
import tempfile

import numpy as np

import domains.many_settings_recognizer as MS
import domains.self_directed_speech_world as W
from substrate_rs import (Attr, Lit, Var, Argmax, And, Gt, Gte, Lt,
                          IfThenElse, Plus)


# ---------------------------------------------------------------------------
# (1) IDS-REGISTER TTS — child-directed speech. The parent speaks the teaching
# clip SLOWED + PITCHED (the register that aids early word learning). espeak
# exposes -s (words/min) and -p (pitch 0-99). Boundary DSP/TTS ONLY — the clip is
# still ingested by the agent's OWN front end and recognised by the agent.
# ---------------------------------------------------------------------------

# IDS register defaults: slower than the ~175 wpm espeak default, raised pitch.
# These are register PARAMETERS (world I/O), not agent state.
IDS_RATE_WPM = 110          # slower (child-directed cadence)
IDS_PITCH = 75              # higher (raised f0 / expanded contour)

# the held-out rate at/above which the parent has released IDS scaffolding and speaks
# in the test (ADS) register — so the bank ends register-matched to the yardstick
# (move 2, REGISTER-GATING; see _register_gate_term below). Defined here so
# install_parent can default to it.
IDS_RELEASE_DEFAULT = 0.60


# ---------------------------------------------------------------------------
# (1a) REAL / PEDAGOGICAL render — Lingua Libre clear-speech clips.
#
# Lingua Libre (gateless, multilingual, CC) gives REAL isolated-word clear-speech
# pronunciations (citation form). When the taught word is COVERED by the corpus in
# this language, the PARENT teaches with a real recording instead of synthetic
# espeak — the genuine "second-language-learning" teaching voice. This is the
# scaffold-register RENDERER; the REGISTER_GATE_TERM decision (IDS vs ADS) is
# UNCHANGED — only the audio the parent utters for the scaffold register swaps from
# synthetic-IDS to real-clear-speech. Held-out speakers are excluded here so the
# teaching clips never leak the held-out probe's speakers (the LOSO yardstick).
# DONKEY BOUNDARY: the corpus is the WORLD's teaching speech (the parent SPEAKS a
# real recording); the agent grounds + recognises it, never inverts it.
# ---------------------------------------------------------------------------

# module-global RNG seed for the deterministic pedagogical clip pick (reproducible
# teaching across a run; not agent state).
_PED_RNG = np.random.default_rng(0)


def ped_clip(word, lang, held_speakers=None, rng=None):
    """Return a REAL Lingua Libre clip (audio float32, fs) for `word` in `lang`,
    EXCLUDING any held-out speakers, or None if the corpus lacks the word. Pure world
    I/O: the parent draws a real clear-speech recording. The held_speakers exclusion
    keeps the teaching set disjoint from the cross-speaker held-out probe (the
    ungameable yardstick) — held-out speakers are never spoken as teaching clips."""
    if not W.ll_available(lang):
        return None
    idx = W.ll_index(lang)
    paths = idx.get(word) or []
    if held_speakers:
        held = set(held_speakers)
        keep = []
        for p in paths:
            m = W._LL_FN.match(os.path.basename(p))
            if m and m.group(2) in held:
                continue
            keep.append(p)
        paths = keep
    if not paths:
        return None
    r = rng if rng is not None else _PED_RNG
    path = paths[int(r.integers(len(paths)))]
    return W.load_ll_clip(path)


def parent_say(word, lang, register="IDS", held_speakers=None,
               use_real=True) -> tuple:
    """Voice `word` in `lang` in the PARENT's register, resampled to 8 kHz mono
    (matching the world's other sources). register="IDS" -> slowed + pitched
    child-directed speech; register="ADS" -> the plain adult espeak (the world's
    `tts`). For the SCAFFOLD (IDS) register, if `use_real` and the word is COVERED by
    the Lingua Libre pedagogical corpus, the parent teaches with a REAL clear-speech
    recording (excluding held_speakers) instead of synthetic espeak; espeak is the
    fallback for uncovered words. Returns (audio float32, fs). Pure world I/O — the
    parent SPEAKS; the agent recognises the clip, never inverts it (no-donkey)."""
    if register != "IDS":
        return W.tts(word, lang)
    # PEDAGOGICAL render branch: a real clear-speech clip for the scaffold register
    # when the corpus covers the word; otherwise fall through to synthetic IDS.
    if use_real:
        real = ped_clip(word, lang, held_speakers=held_speakers)
        if real is not None:
            return real
    voice = W._ESPEAK_VOICE.get(lang, "en")
    exe = W._which("espeak-ng") or W._which("espeak")
    if exe is None:                       # no espeak -> fall back to plain world TTS
        return W.tts(word, lang)
    with tempfile.TemporaryDirectory() as d:
        raw = os.path.join(d, "raw.wav")
        out = os.path.join(d, "out.wav")
        subprocess.run([exe, "-v", voice, "-s", str(IDS_RATE_WPM),
                        "-p", str(IDS_PITCH), "-w", raw, word],
                       check=True, capture_output=True)
        if W._which("ffmpeg"):
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw,
                            "-ar", str(W._TARGET_FS), "-ac", "1",
                            "-sample_fmt", "s16", out],
                           check=True, capture_output=True)
            return W._read_wav(out)
        return W._read_wav(raw)


# ---------------------------------------------------------------------------
# (2) THE ZPD PICK as a GRAPH Term (the scaffolded curriculum).
#
# The PARENT picks the cell at the agent's MEASURED level: just ABOVE mastered,
# BELOW too-hard. This is the Zone of Proximal Development — teaching just above
# the learner's independent level, the opposite of the deficit-only self-pick (which
# always lunges at the hardest/worst cell, where the agent cannot yet learn).
#
# The pick is an Argmax over CurriculumCell of a ZPD-BAND PRIORITY fed by the cell's
# held_cookie_rate (the agent's OWN ungameable held-out measure). The priority:
#   · PEAKS inside the band  (mastered_floor <= rate < mastery_ceiling): teach here.
#   · is LOW for mastered cells   (rate >= mastery_ceiling): gradual release, move on.
#   · is LOW for too-hard cells   (rate <  mastered_floor): not yet learnable alone;
#       the parent does not abandon them — the curriculum-stage gate (below) brings
#       them into reach by advancing only when the floor cells are mastered.
#   · within the band, prefers the cell CLOSEST to mastery (the steepest gradient,
#       Bruner's "right thing at the right time") + an explore bonus for under-probed
#       cells so every band cell is visited.
#
# The DECISION is this Term, evaluated natively by substrate.evaluate; the adapter
# only READS its value (the same pattern PICK_TERM / GUESS_TERM use). NO Python sort,
# NO Python conditional chooses the cell — and it is fed by the held-out rate, so the
# parent teaches at the agent's true (ungamed) level.
# ---------------------------------------------------------------------------

def _zpd_pick_term():
    C = Var("C")
    rate = Attr(C, "held_cookie_rate")
    floor = Attr(C, "zpd_floor")          # below this the cell is too hard (skip)
    ceil = Attr(C, "zpd_ceiling")         # at/above this the cell is mastered (release)
    # in_band = floor <= rate < ceiling. Both bounds are cell attrs the parent sets,
    # so the band ADAPTS per cell (the adapter measures + exposes the level).
    above_floor = Gte(a=rate, b=floor)
    below_ceil = Lt(a=rate, b=ceil)
    in_band = And(items=(above_floor, below_ceil))
    # within the band, prefer the cell CLOSEST to mastery (rate near the ceiling) so
    # the parent rides the steepest learnable gradient — the ZPD's upper edge.
    closeness = rate                      # higher rate (still < ceiling) = closer
    # explore bonus: visit under-probed band cells first. A small constant added
    # while the cell has fewer than zpd_min_visits live attempts, so every band cell
    # is taught before the closeness gradient takes over; it vanishes once probed.
    min_visits = Attr(C, "zpd_min_visits")
    seen = Attr(C, "live_attempts")
    explore = IfThenElse(Gt(a=min_visits, b=seen), Lit(1.0), Lit(0.0))
    # band priority: a large in-band base (so any band cell beats any out-of-band
    # cell) + closeness + explore. Out-of-band cells get 0 -> never chosen while a
    # band cell exists. (When NO cell is in band — all mastered or all too-hard — the
    # Argmax falls through to the highest closeness, which the stage gate then advances.)
    band_priority = IfThenElse(
        in_band,
        Plus(items=(Lit(10.0), closeness, explore)),
        # out of band: rank by closeness to the band from BELOW (too-hard cells just
        # under the floor are the next to unlock) so the fallthrough is sensible.
        rate)
    return MS._Pred(Argmax(
        source={"type": "NodesWhere", "node_type": "CurriculumCell",
                "attr_key": "is_cell", "value": Lit(1.0).to_dict()},
        var_name="C", value=band_priority.to_dict(), default=None).to_dict())


ZPD_PICK_TERM = _zpd_pick_term()


def zpd_pick_cell(substrate):
    """The PARENT's scaffolded curriculum choice: evaluate the ZPD_PICK_TERM Argmax
    natively and return the chosen CurriculumCell node (the cell at the agent's ZPD —
    just above mastered, below too-hard). The decision is the graph Term, fed by the
    agent's held-out rate; this only reads its value."""
    return substrate.evaluate(ZPD_PICK_TERM, {})


# ---------------------------------------------------------------------------
# (3) THE CURRICULUM STAGE GATE (gradual release / acquisition order).
#
# The natural curriculum runs concrete-single-words first, then more, then harder
# sources (noise, cross-speaker FSDD). The PARENT walks an ORDERED list of stages and
# UNLOCKS the next only when the current stage's cells are MASTERED (held-out rate >=
# ceiling) — Bruner's gradual release. An UNLOCKED cell is in the curriculum (is_cell
# = 1); a LOCKED cell is excluded from the ZPD Argmax (is_cell = 0) so the parent
# never teaches above the agent's reach.
#
# The MASTERY judgement is the agent's held-out rate (its yardstick). The adapter only
# reads it and flips is_cell — no Python decides WHAT to teach, the ZPD Term does; the
# gate only governs WHICH cells are in scope, by the agent's measured mastery.
# ---------------------------------------------------------------------------

# Acquisition order over the world's SOURCE axis (easiest synthetic -> hardest real).
# Each stage is unlocked when every cell of the previous stage is mastered.
STAGE_ORDER = ["espeak", "piper", "noise", "fsdd"]


def _stage_index(source) -> int:
    return STAGE_ORDER.index(source) if source in STAGE_ORDER else len(STAGE_ORDER)


def install_parent(substrate, zpd_floor=0.30, zpd_ceiling=0.80,
                   zpd_min_visits=8.0, release_threshold=0.60,
                   ids_release=IDS_RELEASE_DEFAULT) -> dict:
    """Install the PARENT over the existing speech world: a Parent graph node owning
    the ZPD band parameters, and the ZPD attrs on every CurriculumCell (the band the
    pick Term reads). Idempotent — safe to call on a resumed save (adds the parent
    attrs a pre-parent cell lacks without disturbing learned rates/banks).

    The PARENT reads the agent's OWN held_cookie_rate; it sets only the band bounds
    and the stage-lock (is_cell). Returns {parent, zpd_pick_term}."""
    nat = W._native(substrate)
    for src_t, et, tgt_t, prov in (
        ("SpeechWorldRoot", "parented_by", "Parent", "parent:link"),
        ("Parent", "teaches", "CurriculumCell", "parent:teaches"),
    ):
        try:
            substrate.add_production({"src": {"type": src_t, "var": "a"},
                                      "edge_type": et,
                                      "tgt": {"type": tgt_t, "var": "b"},
                                      "provenance": prov})
        except Exception:
            pass
    root = next((n for n in substrate.nodes("SpeechWorldRoot")), None)
    parent = next((n for n in substrate.nodes("Parent")), None)
    if parent is None:
        parent = substrate.add_node("Parent", {
            "origin": "parent_teacher",
            "zpd_floor": float(zpd_floor),
            "zpd_ceiling": float(zpd_ceiling),
            "zpd_min_visits": float(zpd_min_visits),
            # RELEASE threshold (gradual release): a stage unlocks the next when its
            # cells reach this "good enough" held-out rate. Distinct from (and below)
            # the ZPD ceiling so the curriculum keeps PROGRESSING — a cell does not
            # have to be near-perfect before the parent introduces the next, harder
            # source (children move on from "good enough", not from mastery).
            "release_threshold": float(release_threshold),
            # REGISTER-GATING release: the held-out rate at/above which the parent
            # stops scaffolding in IDS and speaks the ADS test register, so the bank
            # ends register-matched to the yardstick (the IDS-hurts fix).
            "ids_release": float(ids_release),
            "unlocked_stage": 0,          # how many acquisition stages are open
        })
        if root is not None:
            try:
                substrate.add_edge(root, "parented_by", parent)
            except Exception:
                pass
    # expose the ZPD band onto every cell (the band the pick Term reads). Defaults a
    # pre-parent (resumed) cell lacks; do not clobber an already-set band.
    for c in substrate.nodes("CurriculumCell"):
        a = substrate.node(c)["attrs"]
        if "zpd_floor" not in a:
            substrate.set_attr(c, "zpd_floor", float(zpd_floor))
        if "zpd_ceiling" not in a:
            substrate.set_attr(c, "zpd_ceiling", float(zpd_ceiling))
        if "zpd_min_visits" not in a:
            substrate.set_attr(c, "zpd_min_visits", float(zpd_min_visits))
        if "ids_release" not in a:
            substrate.set_attr(c, "ids_release", float(ids_release))
        try:
            substrate.add_edge(parent, "teaches", c)
        except Exception:
            pass
    return {"parent": parent, "zpd_pick_term": ZPD_PICK_TERM}


def apply_stage_gate(substrate) -> dict:
    """GRADUAL RELEASE: unlock the next acquisition stage iff every cell of the
    current open stage is MASTERED (held-out rate >= its ceiling). LOCKED cells are
    excluded from the ZPD Argmax (is_cell = 0); UNLOCKED cells are in scope
    (is_cell = 1). The MASTERY judgement is the agent's held-out yardstick; this only
    reads it and flips scope. Returns {unlocked_stage, advanced, locked, open}.

    NO Python decides what to teach — the ZPD Term does; this governs which cells are
    in scope by the agent's measured mastery (the parent teaching at the right level
    and releasing as competence grows)."""
    parent = next((n for n in substrate.nodes("Parent")), None)
    if parent is None:
        return {"unlocked_stage": 0, "advanced": False, "locked": [], "open": []}
    cells = list(substrate.nodes("CurriculumCell"))
    pa = substrate.node(parent)["attrs"]
    open_stage = int(pa.get("unlocked_stage", 0))
    release = float(pa.get("release_threshold", 0.60))

    def stage_of(c):
        return _stage_index(substrate.node(c)["attrs"].get("source"))

    # Is the current open stage "good enough" to release the next? Every cell at this
    # stage has held-out >= the release threshold. An EMPTY stage (no cells in this
    # world's grid, e.g. piper offline) is trivially passed so it does not block
    # release to the next populated stage.
    def stage_mastered(stage):
        scoped = [c for c in cells if stage_of(c) == stage]
        if not scoped:
            return True                   # empty stage — skip it (no gate)
        for c in scoped:
            a = substrate.node(c)["attrs"]
            if float(a.get("held_cookie_rate", 0.0)) < release:
                return False
        return True

    advanced = False
    # advance as far as consecutive mastery allows (clears empty + mastered stages).
    while open_stage < len(STAGE_ORDER) - 1 and stage_mastered(open_stage):
        open_stage += 1
        advanced = True
    substrate.set_attr(parent, "unlocked_stage", int(open_stage))

    locked, open_cells = [], []
    for c in cells:
        a = substrate.node(c)["attrs"]
        in_scope = stage_of(c) <= open_stage
        substrate.set_attr(c, "is_cell", 1.0 if in_scope else 0.0)
        (open_cells if in_scope else locked).append(a.get("name"))
    return {"unlocked_stage": open_stage, "advanced": advanced,
            "locked": sorted(locked), "open": sorted(open_cells)}


# ---------------------------------------------------------------------------
# (4) OSTENSIVE NAMING — the restricted competitor set + the learning target.
#
# When teaching a word, the PARENT gives the LABEL (banked as the learning target)
# and restricts the agent's guess to a few COMPETITORS (the highlight-target /
# suppress-competitors lever). The competitor set is drawn from the cell's vocab
# AROUND the target — a handful of confusable neighbours, not the full lexicon. The
# label is NOT the answer: the agent still RECOGNISES the clip within the restricted
# set; the cookie is the feedback. The held-out probe never restricts.
# ---------------------------------------------------------------------------

def competitor_set(vocab, target, k=4, rng=None) -> list:
    """The restricted competitor set the parent narrows the agent's guess to: the
    target plus up to k-1 OTHER words from the cell's vocab. This is the
    'suppress competitors' lever (the research's strongest result). Pure I/O — it
    scopes the candidate pool; the agent still recognises within it. NEVER used on
    the held-out yardstick (which always sees the full lexicon)."""
    others = [w for w in vocab if w != target]
    if rng is not None:
        others = list(others)
        rng.shuffle(others)
    chosen = [target] + others[:max(0, k - 1)]
    return chosen


# ---------------------------------------------------------------------------
# (5) REGISTER-GATING — IDS -> ADS developmentally (the IDS-hurts fix).
#
# The first piece found IDS HURT: banking slowed+pitched IDS exemplars and then
# testing on an ADS yardstick is a TRAIN/TEST register MISMATCH — the IDS
# neighbours pollute the 1-NN bank. That is exactly the developmental-gating the
# literature describes IN REVERSE: IDS aids word learning EARLY (when the learner is
# far from mastery) and its necessity DECLINES as competence grows (only larger-
# vocabulary infants learned from ADS). The fix is to GATE the register on the cell's
# measured mastery: speak IDS while the cell is FAR FROM MASTERY (scaffolding), and
# transition to ADS as the agent masters (gradual release), so the agent ENDS grounded
# in the register the held-out (ADS) yardstick uses. No residual mismatch.
#
# The register CHOICE is a GRAPH Term fed by the cell's held_cookie_rate (the agent's
# OWN ungameable held-out measure): register = IDS while rate < ids_release, ADS at/
# above it. The parent only MEASURES the level and reads the Term's value; the
# DECISION is the graph Term. The held-out yardstick stays ADS, full-lexicon.
# ---------------------------------------------------------------------------

def _register_gate_term():
    """A graph boolean Term: TRUE when the cell is still far enough from mastery that
    the parent should scaffold with IDS (held_cookie_rate < ids_release), FALSE once
    mastered enough to transition to the ADS test register. Fed by the agent's OWN
    held-out rate; the decision is this Term, the adapter only reads its value."""
    C = Var("C")
    rate = Attr(C, "held_cookie_rate")
    release = Attr(C, "ids_release")
    return MS._Pred(Lt(a=rate, b=release).to_dict())


REGISTER_GATE_TERM = _register_gate_term()


def gated_register(substrate, cell) -> str:
    """The PARENT's developmentally-gated register for one cell: IDS while the cell
    is below its ids_release held-out rate (scaffolding, far from mastery), ADS once
    at/above it (gradual release toward the test register). The decision is the graph
    REGISTER_GATE_TERM, fed by the agent's held-out rate; this only reads its value.
    Returns 'IDS' or 'ADS'."""
    use_ids = bool(substrate.evaluate(REGISTER_GATE_TERM, {"C": cell}))
    return "IDS" if use_ids else "ADS"


# ---------------------------------------------------------------------------
# (6) RECASTS — the contingent corrective feedback (richer than the cookie).
#
# After the agent's BLIND guess, the PARENT re-utters the CORRECT word in the
# currently-gated register — the recast. This is contingent corrective input
# (Nelson; Contrast theory): the agent gets the correct FORM, not just a right/wrong
# bit. It is the SOCIAL, EXTERNAL version of the agent's own order-N forward model
# (the parent re-utters / speaks the target). On a MISS the recast also yields a
# (guess, truth) CONTRAST PAIR: the same teaching slot produced two ways.
#
# THE DONKEY BOUNDARY: the PARENT only UTTERS the recast (TTS, world I/O). The AGENT
# BANKS it — banking is the cookie's effect, done by the world adapter via
# W.bank_exemplar, the same grounding mechanism a cookie uses. The recast is the
# LEARNING TARGET, never the guess-time answer (the agent already committed its blind
# guess before the recast). The held-out probe never sees a recast.
# ---------------------------------------------------------------------------

def recast_clip(truth, lang, register="IDS", held_speakers=None,
                use_real=True) -> tuple:
    """The PARENT re-utters the CORRECT word `truth` in `lang` in the gated register
    — the recast clip the agent banks as the learning target. Pure world I/O: the
    parent SPEAKS the correct form (a REAL Lingua Libre clear-speech clip when the
    word is covered and use_real, else synthetic IDS/ADS); the agent grounds it.
    register is the developmentally-gated register (gated_register) so the recast
    tracks toward the ADS test register as the agent masters. held_speakers are
    excluded from the real-clip pick so teaching never leaks the held-out probe.
    Returns (audio float32, fs)."""
    return parent_say(truth, lang, register=register,
                      held_speakers=held_speakers, use_real=use_real)


def bank_recast(substrate, truth, cell_key, lang, register="IDS",
                guess=None, guess_clip=None, held_speakers=None,
                use_real=True) -> dict:
    """LEARN from the recast: the PARENT re-utters the correct word in the gated
    register and the AGENT BANKS it as an exemplar of the true word (the cookie's
    grounding mechanism, W.bank_exemplar — admissible structure, not a gradient
    reward). On a MISS with the agent's own guess clip available, ALSO bank the
    agent's guess clip under the TRUTH label as the contrast member (per Contrast
    theory: the agent banks the contrast — its-guess-vs-correct — for the true word),
    so the same teaching slot grounds the target from two productions.

    The PARENT only UTTERS (recast_clip); the banking is the agent's grounding. The
    recast is the learning TARGET, never the guess-time answer. Returns a small dict
    summary {recast_banked, contrast_banked}."""
    rx, rfs = recast_clip(truth, lang, register=register,
                          held_speakers=held_speakers, use_real=use_real)
    W.bank_exemplar(substrate, truth, cell_key, rx, rfs)
    contrast = False
    # On a MISS, the agent banks the contrast pair: the clip it MISHEARD, re-labelled
    # to the TRUTH (the correct form the recast gave). The agent now has, for the true
    # word, an exemplar that previously pulled toward the wrong label — the contrast
    # the recast resolves. (Only when guess != truth and the guess clip is supplied;
    # the held-out probe never banks.)
    if guess is not None and guess != truth and guess_clip is not None:
        gx, gfs = guess_clip
        W.bank_exemplar(substrate, truth, cell_key, gx, gfs)
        contrast = True
    return {"recast_banked": True, "contrast_banked": contrast}


__all__ = [
    "IDS_RATE_WPM", "IDS_PITCH", "parent_say", "ped_clip",
    "ZPD_PICK_TERM", "zpd_pick_cell",
    "STAGE_ORDER", "install_parent", "apply_stage_gate",
    "competitor_set",
    "IDS_RELEASE_DEFAULT", "REGISTER_GATE_TERM", "gated_register",
    "recast_clip", "bank_recast",
]
