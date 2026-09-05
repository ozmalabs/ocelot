"""trait_modulator_bridge — the BIDIRECTIONAL bridge connecting the agent's
crystallised TRAIT VECTOR (the SLOW cognitive-personality layer,
domains/disposition.py) to its MicroPsi ModulatorState (the FAST affect layer,
seeds/modulators.json).

WHAT THIS IS
------------
The agent has two affect-relevant layers that must be COUPLED, not siloed:

  · the SLOW layer — the crystallised trait vector (openness / abstraction /
    skepticism), each a real CAN `Concept` in the `agent_disposition` Mt whose
    `identity_field` (mirrored to `<trait>_field`) moves only under sustained
    evidence via the engine's own `can_native_identity_field_feedback` rule. This
    is the STANDING TEMPERAMENT: it changes over many ticks, with hysteresis.

  · the FAST layer — the ModulatorState (resolution / sel_threshold / securing /
    competence), recomputed EVERY tick by the modulator rules from the live drive
    state. This is the MOMENTARY affect: it swings tick-to-tick with urgency and
    arousal.

The set-point-bias stage (`setpoint_bias_formulas`) added three CONSTANT ADDITIVE
offsets — `abstraction_bias`, `openness_bias`, `skepticism_bias` — to the three
modulator formulas (mod_resolution / mod_sel_threshold / mod_securing), each
defaulted to 0 (bias-free == today). Those offsets are the WRITE HOOK this bridge
drives. This module is the two-way COUPLING between the layers:

  (A) TRAIT -> MODULATOR (the set-point).  `sync_traits_to_modulator` writes each
      crystallised trait LEVEL into the ModulatorState bias attr its biased
      formula reads:
          openness    level -> ms.openness_bias    (shifts sel_threshold)
          abstraction level -> ms.abstraction_bias (shifts resolution)
          skepticism  level -> ms.skepticism_bias  (shifts securing)
      The standing temperament thereby shifts the modulator BASELINE — the drives
      still regulate AROUND the shifted set-point (the offset is a constant, so it
      cancels in every drive-driven delta; proven in the prior stage).

  (B) MODULATOR/DRIVE -> TRAIT (crystallisation from lived experience).
      `crystallise_traits_from_modulator` reads the LIVE ModulatorState + leading
      drive back as trait EVIDENCE and hands it to `disposition.relax_trait`, so
      the trait crystallises from what the agent actually FELT/DID, not only from
      externally-injected evidence:
          sustained HIGH resolution                 => abstraction crystallises UP
          sustained HIGH securing / exploration_urge => skepticism crystallises UP
          sustained LOW sel_threshold / HIGH competence => openness crystallises UP
      The DECISION (how far the trait moves) is the CAN rule's — this module only
      reads modulator attrs, turns them into a signed sigma + tick budget, and
      hands them to the native relaxation. NO Python computes affect.

MIRRORS can_self_worth_bridge.py
--------------------------------
Pure world-adapter/harness code (CLAUDE.md's architecture rule). Every function
is (a) mechanical construction / location of the opt-in modulator state via the
ESTABLISHED loaders + builders (drives + modulators + affective_state_core seeds,
EmotionHub + ModulatorState + Drive as doom_dual_process_ingest / harlow_world
build them — NOT a parallel one), or (b) mechanical BOUNDARY I/O feeding the
native relaxation. No decision is made here: direction A copies a produced trait
level onto a set-point attr; direction B copies a produced modulator value into
the SAME `relax_trait` evidence channel `disposition_homeostasis_step` already
uses. The trait Concept stays the SLOW crystallised layer; the ModulatorState is
the FAST layer. `agent_disposition` REFERENCES the spine — it does not duplicate
affect computation.

THE SCALE (trait_level -> bias magnitude) — DOCUMENTED, PROPORTIONAL, HONEST
---------------------------------------------------------------------------
`trait_level` is the QUANTISED standing trait, an integer in [-4, +4]
(disposition._TRAIT_QUANTUM=1.0 / half_width=4). Each level maps to a bias by a
per-trait linear step chosen PROPORTIONAL to that formula's own drive-term swing,
so the bias MEANINGFULLY shifts the set-point WITHOUT SWAMPING the regulation:

    bias = (trait_level - neutral_ref[trait]) * STEP[trait]

Measured drive-term magnitudes (prior-stage live probe: urgency~600, arousal~36,
competence~25, and the modulator_emergence CANON / harlow ranges):
  · resolution   ~= res_base(500) + urgency/res_urg_div(~150) - arousal(~36) ~ 600.
    The URGENCY term (the thing the drives move) swings by ~150 across the drive
    range. STEP_ABSTRACTION = 30 => level +4 shifts resolution by +120, COMPARABLE
    to but not exceeding the urgency swing: a strong-abstraction agent reaches for
    broader/more-abstract processing, but a screaming drive still dominates.
  · sel_threshold ~= weight*urgency/sel_div - sel_k*(competence_full-competence)
    - openness_bias. This term is the LARGEST (hundreds to low thousands). The
    competence term swings by ~sel_k*competence_full = ~100. STEP_OPENNESS = 25
    => level +4 lowers the threshold by 100, comparable to the competence swing:
    a very-open agent commits/mints markedly more readily, but not unconditionally.
  · securing     ~= exploration_urge + (competence_full-competence) - sec_k*weight
    + skepticism_bias, magnitude ~100. The competence term swings by ~100.
    STEP_SKEPTICISM = 15 => level +4 raises securing by 60, a clear but
    sub-dominant vigilance shift.

NEUTRAL REFERENCE — why default == today for the MODULATOR path too
-------------------------------------------------------------------
The safe-default trait vector is openness -1, abstraction 0, skepticism 0
(disposition's seeded defaults). For the bias path to preserve TODAY's emergent
emotion at default, the DEFAULT temperament must map to ZERO bias on every axis:

  · abstraction / skepticism default to level 0, and their neutral_ref is 0, so
    (0 - 0)*STEP = 0. Trivially bias-free at default.
  · openness defaults to level -1 (mildly conservative — today's mint stance).
    A raw `level * STEP` map would write a NONZERO openness_bias at the -1 default,
    changing sel_threshold and BREAKING default == today for the modulator path.
    So openness's neutral_ref is its OWN DEFAULT SEED (-1): (-1 - -1)*STEP = 0.
    This is the honest, defensible choice — the -1 default openness IS "today's
    behaviour" everywhere else in the system (relation_grounding.MintPolicy treats
    levels -1 and 0 identically as conservative), so the modulator set-point must
    ALSO treat the default temperament as its neutral point. openness only shifts
    the threshold as it crystallises AWAY from its standing default: more permissive
    than default => lower threshold; more conservative than default => higher.

So: an agent with NO agent_disposition traits leaves the bias attrs at 0 (the
sync is a no-op read of absent traits => their seeded defaults => 0 bias). An
agent with the seeded DEFAULT traits writes 0 to ALL THREE bias attrs — the
modulator/emotion path is byte-identical to today. Only a trait that has
crystallised AWAY from its default writes a nonzero bias.

TIMESCALE SEPARATION — why (A) and (B) together do NOT run away
---------------------------------------------------------------
(A) writes a set-point bias FROM the trait; (B) moves the trait FROM the
modulator. Naively that is a positive-feedback loop. It does NOT run away because
the two layers live on DIFFERENT TIMESCALES, structurally:

  · (A) is INSTANT and BOUNDED: the bias is a quantised trait level times a small
    integer step, clamped to [-4,+4] levels. A trait at its ceiling writes a fixed
    maximal bias and CANNOT grow further no matter how many times (A) runs.
  · (B) is SLOW and HYSTERETIC: `relax_trait` moves `identity_field` by at most
    ONE ±1 quantum per strictly-later tick, and only after the evidence LEDGER's
    log-odds sign flips (can_native_identity_field_feedback). It takes many
    consecutive same-sign modulator ticks to move the trait one level.

So the fast layer (modulator, recomputed every tick) settles ENTIRELY within a
single trait quantum's worth of time; the trait integrates the modulator's
SUSTAINED sign over a long window and moves at most one level per crystallisation
step. The trait ceiling caps the bias; the ledger hysteresis + per-tick quantum
cap the trait's speed. The loop is a slow servo toward a temperament consistent
with sustained affect, not a runaway — exactly the SLOW-crystallised /
FAST-momentary split the two layers are designed around.

THE TRAIT -> DRIVE HOMEOSTATIC REGULATION TABLE (tasks 3+4)
-----------------------------------------------------------
disposition.disposition_homeostasis_step regulates ONE trait (openness) from ONE
substrate signal. This module GENERALISES that to a trait->drive table: each
DRIVE-regulated trait reads a GOVERNING drive/modulator deficit as signed
evidence and crystallises via the SAME relax_trait relaxation. `personality_
homeostasis_step` runs the whole table (openness + abstraction + skepticism) in
one call.

  trait        governing drive/modulator   deficit read              => evidence
  -----------  ---------------------------  ------------------------  -----------
  abstraction  COMPETENCE (mod_competence)  competence < competence_lo => -1 (concrete)
                                            competence >= hi mark      => +1 (abstract)
  skepticism   EXPLORATION/CERTAINTY        exploration_urge > unc_hi  => +1 (demand certainty)
               (exploration_urge/securing)  exploration_urge < unc_lo  => -1 (certainty confirmed)
  openness     — NO clean drive             graph pollution/starvation => own homeostasis

Python only READS the drive number and hands relax_trait a SIGN; HOW FAR the
trait moves is the CAN identity-feedback rule integrating the sign over ticks. A
NEUTRAL drive (competence 0 / exploration_urge 0) injects 0 evidence => the
trait does not drift (default == today). REUSES the existing mod_competence
accumulator and mod_securing/exploration_urge — no new drivers, no new drives.

THE OPENNESS RECONCILIATION — the honest call (task 4)
------------------------------------------------------
openness's pollution/starvation homeostasis was tested against a COMPETENCE
reframe ("minting garbage = low competence at referent-forming; finding-nothing =
low competence at the analogy task"). The mapping is a STRETCH, not a clean
completion, for two structural reasons, so openness KEEPS its substrate-hygiene
homeostasis and is documented as the ONE trait that does not complete the drive
model:

  1. BIDIRECTIONAL REMEDY BY FAILURE TYPE. openness has TWO orthogonal witnesses
     that push OPPOSITE ways on the trait: pollution (junk minted) => conservative
     (mint LESS), starvation (nothing found) => permissive (mint MORE). A single
     competence scalar is UNIDIRECTIONAL — low competence has one remedy
     (replenish / pick easier tasks). It cannot encode a signal whose remedy flips
     with the KIND of failure, not its magnitude. abstraction/skepticism have no
     such split (competence low is unambiguously "go concrete", uncertainty high
     is unambiguously "demand more evidence"), which is exactly why they DO
     complete cleanly.

  2. WRONG SUBSTRATE FOR THE SIGNAL. openness reads STATIC GRAPH-HYGIENE facts
     (thin minted-leaf share, dark relational surface), not a drive's need-
     satisfaction accumulator. mod_competence integrates `learning_progress` off
     the drives; routing openness through it would require INVENTING a mapping
     from "thin-leaf share" to "learning_progress" — precisely the new-driver
     invention this stage forbids.

So the table has TWO clean completions (abstraction<-competence,
skepticism<-exploration) and ONE honest exception (openness stays on
substrate-hygiene). personality_homeostasis_step runs both regulators, keeping
them separate because their signals are different in kind.
"""
from __future__ import annotations

from typing import Optional

import domains.disposition as disp

# --------------------------------------------------------------------------- #
# Vocabulary — the edges/attrs the modulator spine already uses (NOT invented).
# --------------------------------------------------------------------------- #
#: Agent -> EmotionHub edge, the ad-hoc wiring the doom ingest adapters add
#: (add_edge_unchecked; no production admits it — it is host wiring, not a rule
#: edge). We locate an existing hub through it and mint it the same way.
EMOTION_HUB_EDGE = "has_emotion_hub"
MODULATOR_STATE_EDGE = "has_modulator_state"
ACTIVE_DRIVE_EDGE = "has_active_drive"
LEADING_DRIVE_EDGE = "leading_drive"

#: The three modulator bias attrs the biased formulas read (added by the
#: setpoint_bias_formulas stage, defaulted to 0). This bridge WRITES them from
#: the trait levels; absent, each reads Value::None => additive identity 0.
ABSTRACTION_BIAS_ATTR = "abstraction_bias"   # -> mod_resolution baseline
OPENNESS_BIAS_ATTR = "openness_bias"         # -> mod_sel_threshold baseline
SKEPTICISM_BIAS_ATTR = "skepticism_bias"     # -> mod_securing baseline

# --------------------------------------------------------------------------- #
# DIRECTION A — the trait_level -> bias SCALE (documented in the module gloss).
#
# {trait: (bias_attr, step, neutral_ref)}. bias = (level - neutral_ref)*step.
# step is proportional to that formula's own drive-term swing (see gloss);
# neutral_ref is the trait's DEFAULT level so the seeded-default temperament maps
# to 0 bias (default == today for the modulator/emotion path).
# --------------------------------------------------------------------------- #
_BIAS_SPEC = {
    "abstraction": (ABSTRACTION_BIAS_ATTR, 30.0, 0),   # default level 0
    "openness":    (OPENNESS_BIAS_ATTR,    25.0, -1),  # default level -1 (== today)
    "skepticism":  (SKEPTICISM_BIAS_ATTR,  15.0, 0),   # default level 0
}


def trait_bias(level: int, trait: str) -> float:
    """The documented set-point bias for a trait at a quantised `level`: a
    per-trait linear step off the trait's DEFAULT (neutral_ref) level. Pure
    arithmetic — the SCALE, no graph I/O. A level equal to the trait's default
    maps to 0.0 (bias-free); deviations shift the set-point proportionally to the
    formula's drive-term swing. Returns 0.0 for a trait with no bias hook."""
    spec = _BIAS_SPEC.get(trait)
    if spec is None:
        return 0.0
    _attr, step, neutral_ref = spec
    return float(int(level) - int(neutral_ref)) * float(step)


# --------------------------------------------------------------------------- #
# DIRECTION B — the modulator/drive read-back thresholds -> trait evidence sign.
#
# Each trait crystallises from a SUSTAINED modulator/drive condition. These are
# the read thresholds that turn a live modulator value into a signed sigma for
# `relax_trait` (the SAME evidence channel disposition_homeostasis_step uses).
# The sign is the DECISION-FREE mechanical mapping; how far the trait moves is
# the CAN identity-feedback rule's, integrating the sustained sign.
#
# Thresholds are set to the modulator knobs' own reference points so "high"/"low"
# means what the modulator layer itself means by it:
#   · resolution HIGH := > resolution_hi (the modulator's own high-resolution
#     mark, MS_DEFAULTS resolution_hi=450) => abstraction UP; LOW := < resolution_lo
#     (200) => abstraction DOWN.
#   · securing HIGH := > securing_hi (50) OR leading exploration_urge > 0 =>
#     skepticism UP (outward vigilance / demand for evidence sustained).
#   · sel_threshold LOW := < sel_threshold_hi (200) AND competence HIGH
#     (>= competence_full - competence_lo, i.e. the agent is succeeding and
#     committing readily) => openness UP; a HIGH threshold with LOW competence =>
#     openness DOWN (the agent is straining, committing little => more conservative).
# All thresholds READ the ModulatorState's own knobs (falling back to the
# MS_DEFAULTS values), so a world that tuned its knobs is respected.
# --------------------------------------------------------------------------- #
_RES_HI_DEFAULT = 450.0
_RES_LO_DEFAULT = 200.0
_SEC_HI_DEFAULT = 50.0
_SEL_HI_DEFAULT = 200.0
_COMP_FULL_DEFAULT = 100.0
_COMP_LO_DEFAULT = 30.0


# --------------------------------------------------------------------------- #
# Modulator-state construction / location — reuse the established builder.
# --------------------------------------------------------------------------- #
#: Healthy ModulatorState knob defaults — the SAME set the modulator_emergence
#: measure / harlow builders use (build_modulator_seeds' rules read these). The
#: three bias offsets default 0 (bias-free == today) until sync writes them.
_MS_DEFAULTS = dict(
    enabled=1.0, competence=0.0, competence_base=0.0,
    epoch=0.0, competence_epoch=-1.0, emotion_epoch=-1.0,
    drive_switch_threshold=0.0,
    competence_full=100.0, competence_lo=30.0,
    band_hi=600.0, band_mid=150.0,
    res_base=500.0, res_urg_div=4.0, res_ar_div=1.0,
    resolution_lo=200.0, resolution_hi=450.0,
    abstraction_bias=0.0, openness_bias=0.0, skepticism_bias=0.0,
    sel_div=1.0, sel_k=1.0, sel_threshold_hi=200.0,
    sec_k=1.0, securing_hi=50.0, uncertainty_hi=100.0,
    residual_thresh=100.0, w_supergraph=1.0,
    valence_raw=0.0, valence=0.0, arousal=0.0, arousal_band=0.0,
    resolution=0.0, sel_threshold=0.0, securing=0.0,
)

#: A single active/leading drive with nonzero urgency so the LEAD_MATCH formulas
#: fire and populate resolution/sel_threshold/securing. v_d != c_d => nonzero
#: urgency; scale as the measure harness uses. A fully-generic engaged drive.
_DRIVE_DEFAULTS = dict(
    name=0.0, v_d=1000.0, c_d=400.0, c_d_prev=400.0, v_0=0.0, weight=1.0,
    decay=0.0, gain=0.0, loss=0.0, half_life=1_000_000.0, last_tend=0.0,
    now_epoch=0.0, scale=1000.0,
    urge=0.0, urgency=0.0, pleasure=0.0, displeasure=0.0, arousal_contrib=0.0,
    threat=0.0, threat_c0=1024.0, threat_half_life=1.0, threat_now_epoch=0.0,
    threat_last_refresh=0.0, t_present=256.0, threat_precision=0.0,
    threat_persists=0.0, appraised=1.0, residual=0.0, learning_progress=0.0,
    value_progress=0.0, valued_goal=0.0, goal_blocked=0.0, blocker_present=0.0,
    contamination=0.0, loss_object=0.0, explore=0.0, was_engaged=0.0,
    supergraph_value=0.0, exploration_urge=0.0, is_affiliation=0.0,
    legitimacy=0.0, social_weight=1.0,
)


def _ensure_modulator_seeds(native, agent_node=None) -> bool:
    """Idempotently load the drives + modulators + affective_state_core seeds —
    the ESTABLISHED spine (drives.json's urge/urgency rules, modulators.json's
    biased formulas, affective_state_core's leading-drive selector). Guarded by a
    rule-name sentinel exactly as doom_dual_process_ingest._ensure_seed does, so
    a substrate that already loaded them is not doubled. Returns True when the
    LOAD-BEARING seeds (drives + modulators) are present, False on a non-live
    handle or if those fail to load (honest no-op).

    affective_state_core carries agent-role refs, so it needs the Agent root node
    (as doom_dual_process_ingest / harlow_world pass `agent.agent`); we load it
    only when an `agent_node` is available. It is NOT load-bearing here — we mark
    the leading drive directly (the measure-harness path), so LEAD_MATCH is
    satisfied without the selector. Its absence degrades gracefully."""
    if not hasattr(native, "run_rules") or not hasattr(native, "load_seed_manifest"):
        return False
    try:
        from substrate.seed_loader import manifest_for
        names = {row.get("name") for row in native.export_rules()}
        if "drive_urge" not in names:
            native.load_seed_manifest(manifest_for("drives"), None)
        if "mod_valence" not in names:
            native.load_seed_manifest(manifest_for("modulators"), None)
    except Exception:
        return False
    # affective_state_core (leading-drive selector + affect projection): OPTIONAL,
    # agent-scoped. Load it only with an Agent root; never fatal.
    try:
        names = {row.get("name") for row in native.export_rules()}
        if agent_node is not None and \
                "psi_select_initial_leading_drive" not in names:
            from substrate.seed_loader import manifest_for
            native.load_seed_manifest(
                manifest_for("affective_state_core"), agent_node)
    except Exception:
        pass
    return True


def _find_modulator_state(native, agent_node):
    """Locate an existing ModulatorState, first-found-wins: prefer the one wired
    to the Agent hub (has_emotion_hub -> has_modulator_state), else the first
    EmotionHub's modulator, else a bare scan of ModulatorState nodes. Mirrors
    disposition._find_disposition_mt's prefer-edge-then-scan idiom. Returns
    (hub, ms) or (None, None)."""
    # (1) via the Agent hub.
    if agent_node is not None:
        try:
            for hub in native.neighbours(agent_node, EMOTION_HUB_EDGE):
                mss = list(native.neighbours(hub, MODULATOR_STATE_EDGE))
                if mss:
                    return hub, mss[0]
        except Exception:
            pass
    # (2) via any EmotionHub.
    try:
        for hub in native.nodes("EmotionHub"):
            mss = list(native.neighbours(hub, MODULATOR_STATE_EDGE))
            if mss:
                return hub, mss[0]
    except Exception:
        pass
    # (3) a bare ModulatorState scan (no hub wiring).
    try:
        mss = list(native.nodes("ModulatorState"))
        if mss:
            return None, mss[0]
    except Exception:
        pass
    return None, None


def _leading_drive(native, ms):
    """The ModulatorState's current leading drive (first-found), or None."""
    try:
        ds = list(native.neighbours(ms, LEADING_DRIVE_EDGE))
        return ds[0] if ds else None
    except Exception:
        return None


def ensure_modulator_state(agent, *, drive_over: Optional[dict] = None,
                           ms_over: Optional[dict] = None, run: bool = True):
    """Idempotent: return the agent's live (hub, ms) ModulatorState, minting it
    (wired to the Agent hub via has_emotion_hub) with a healthy default knob set
    + one engaged leading drive if this graph has none. REUSES the established
    modulator spine (drives + modulators + affective_state_core seeds, EmotionHub
    + ModulatorState + Drive nodes as doom_dual_process_ingest / harlow_world
    build them) — NOT a parallel affect system.

    On first build it loads the seeds, mints the hub/ms/drive, wires
    has_active_drive + leading_drive (so the LEAD_MATCH formulas fire), and (with
    `run`) ticks once so resolution/sel_threshold/securing/competence populate.
    `ms_over`/`drive_over` override the default knobs/drive for a probe.

    Returns (hub, ms) — hub may be None if only a bare ModulatorState existed —
    or (None, None) on a non-live substrate. Never mints a second ModulatorState
    once one exists (first-found-wins)."""
    sub = disp._sub(agent)
    if sub is None:
        return None, None
    native = disp._native(sub)
    ag = disp._agent_node(agent)

    hub, ms = _find_modulator_state(native, ag)
    if ms is not None:
        return hub, ms

    if not _ensure_modulator_seeds(native, ag):
        return None, None
    try:
        hub = native.add_node("EmotionHub", {"domain": "trait_bridge"})
        if ag is not None:
            native.add_edge_unchecked(ag, EMOTION_HUB_EDGE, hub)
        ms_attrs = dict(_MS_DEFAULTS)
        if ms_over:
            ms_attrs.update({k: float(v) for k, v in ms_over.items()})
        ms = native.add_node("ModulatorState", ms_attrs)
        native.add_edge_unchecked(hub, MODULATOR_STATE_EDGE, ms)

        dr_attrs = dict(_DRIVE_DEFAULTS)
        if drive_over:
            dr_attrs.update({k: float(v) for k, v in drive_over.items()})
        drive = native.add_node("Drive", dr_attrs)
        native.add_edge_unchecked(ms, ACTIVE_DRIVE_EDGE, drive)
        # Mark the leading drive directly (the measure-harness path) so LEAD_MATCH
        # is satisfied even if affective_state_core's selector has not run yet;
        # psi_select_initial_leading_drive is idempotent (Count(leading)==0 guard).
        native.add_edge_unchecked(ms, LEADING_DRIVE_EDGE, drive)
        if run:
            native.run_rules()
        return hub, ms
    except Exception:
        return None, None


# --------------------------------------------------------------------------- #
# DIRECTION A — TRAIT -> MODULATOR (the set-point).
# --------------------------------------------------------------------------- #
def sync_traits_to_modulator(agent, *, ensure_traits: bool = False,
                             run: bool = True) -> dict:
    """DIRECTION A: write each crystallised trait LEVEL into the ModulatorState
    bias attr its biased formula reads — the standing temperament shifts the
    modulator set-point. Mechanical boundary I/O: read the produced trait level
    (disposition.trait_level), map it through the documented SCALE (trait_bias),
    write the bias attr. NO decision, NO affect computed here.

        openness    level -> ms.openness_bias    (lowers sel_threshold when > default)
        abstraction level -> ms.abstraction_bias (raises resolution   when > default)
        skepticism  level -> ms.skepticism_bias  (raises securing      when > default)

    SAFE DEFAULT: `ensure_traits=False` (the default) reads absent traits as
    their SEEDED defaults WITHOUT minting a disposition Mt — so a bare agent
    reads openness -1 / abstraction 0 / skepticism 0, which the SCALE maps to
    0 bias on ALL THREE (openness's neutral_ref is its -1 default). The write is
    then byte-identical to the default (0 => 0), and the modulator/emotion path
    is UNCHANGED from today. Set `ensure_traits=True` to mint the vector first.

    With `run` (default), ticks once after writing so the biased formulas
    recompute resolution/sel_threshold/securing off the new baseline.

    Returns {levels, biases, ms, hub, wrote} — the read trait levels, the written
    bias values, the ms/hub nodes, and whether a live write happened. A no-op
    (empty dict fields) on a non-live substrate."""
    hub, ms = ensure_modulator_state(agent, run=False)
    if ms is None:
        return {"levels": {}, "biases": {}, "ms": None, "hub": None,
                "wrote": False}
    native = disp._native(disp._sub(agent))

    levels, biases = {}, {}
    for trait, (attr, _step, _ref) in _BIAS_SPEC.items():
        level = disp.trait_level(agent, trait, ensure=ensure_traits)
        bias = trait_bias(level, trait)
        levels[trait] = level
        biases[trait] = bias
        try:
            native.set_attr(ms, attr, float(bias))
        except Exception:
            pass
    if run:
        try:
            native.run_rules()
        except Exception:
            pass
    return {"levels": levels, "biases": biases, "ms": ms, "hub": hub,
            "wrote": True}


# --------------------------------------------------------------------------- #
# DIRECTION B — MODULATOR/DRIVE -> TRAIT (crystallisation from lived experience).
# --------------------------------------------------------------------------- #
def modulator_trait_evidence(agent, *, ms=None) -> dict:
    """Read the LIVE ModulatorState + leading drive and turn each sustained
    condition into a SIGNED trait evidence sigma (-1 / 0 / +1) — the mechanical,
    decision-free mapping direction B feeds to relax_trait. Pure reads + the
    documented threshold comparisons; NO trait is moved here, NO affect computed.

    Returns {abstraction, openness, skepticism, readings} where each trait key is
    a signed evidence sigma and `readings` is the raw modulator vector observed
    (resolution/securing/sel_threshold/competence/exploration_urge + the knob
    thresholds used). A trait whose condition is neither high nor low reads 0
    (no evidence => relax_trait is a no-op for it)."""
    native = disp._native(disp._sub(agent))
    if ms is None:
        _hub, ms = ensure_modulator_state(agent, run=False)
    if ms is None:
        return {"abstraction": 0.0, "openness": 0.0, "skepticism": 0.0,
                "readings": {}}
    a = native.node(ms)["attrs"]

    def g(key, default):
        try:
            v = a.get(key)
            return float(default if v is None else v)
        except Exception:
            return float(default)

    resolution = g("resolution", 0.0)
    securing = g("securing", 0.0)
    sel_threshold = g("sel_threshold", 0.0)
    competence = g("competence", 0.0)
    res_hi = g("resolution_hi", _RES_HI_DEFAULT)
    res_lo = g("resolution_lo", _RES_LO_DEFAULT)
    sec_hi = g("securing_hi", _SEC_HI_DEFAULT)
    sel_hi = g("sel_threshold_hi", _SEL_HI_DEFAULT)
    comp_full = g("competence_full", _COMP_FULL_DEFAULT)
    comp_lo = g("competence_lo", _COMP_LO_DEFAULT)

    lead = _leading_drive(native, ms)
    exploration_urge = 0.0
    if lead is not None:
        try:
            v = native.node(lead)["attrs"].get("exploration_urge")
            exploration_urge = float(0.0 if v is None else v)
        except Exception:
            exploration_urge = 0.0

    # ABSTRACTION <- resolution: sustained HIGH resolution (reaching for broad/
    # structural processing) crystallises abstraction UP; sustained LOW DOWN.
    abstraction = 0.0
    if resolution > res_hi:
        abstraction = 1.0
    elif resolution < res_lo:
        abstraction = -1.0

    # SKEPTICISM <- securing / exploration_urge: sustained outward vigilance
    # (high securing) or a live exploration/uncertainty urge crystallises the
    # demand-for-evidence trait UP.
    skepticism = 0.0
    if securing > sec_hi or exploration_urge > 0.0:
        skepticism = 1.0

    # OPENNESS <- sel_threshold / competence: committing readily (LOW threshold)
    # WHILE succeeding (HIGH competence) crystallises openness UP; straining (HIGH
    # threshold + LOW competence) crystallises it DOWN toward conservative.
    openness = 0.0
    comp_high = competence >= (comp_full - comp_lo)
    comp_low = competence < comp_lo
    if sel_threshold < sel_hi and comp_high:
        openness = 1.0
    elif sel_threshold >= sel_hi and comp_low:
        openness = -1.0

    return {
        "abstraction": abstraction, "openness": openness, "skepticism": skepticism,
        "readings": {
            "resolution": resolution, "securing": securing,
            "sel_threshold": sel_threshold, "competence": competence,
            "exploration_urge": exploration_urge,
            "resolution_hi": res_hi, "resolution_lo": res_lo,
            "securing_hi": sec_hi, "sel_threshold_hi": sel_hi,
            "competence_full": comp_full, "competence_lo": comp_lo,
        },
    }


def crystallise_traits_from_modulator(agent, *, ms=None, ticks: int = 1,
                                      run_modulator: bool = False) -> dict:
    """DIRECTION B: read the live ModulatorState/leading-drive back as trait
    EVIDENCE and let the CAN identity-feedback rule crystallise each trait — the
    trait moves from what the agent actually FELT/DID, not just injected evidence.

    Pipeline (all boundary I/O + the native relaxation):
      1. (optional) `run_modulator` ticks the modulator rules first so the read
         reflects the CURRENT drive state.
      2. `modulator_trait_evidence` — mechanical reads of resolution/securing/
         sel_threshold/competence + the leading drive's exploration_urge, turned
         into a signed sigma per trait against the modulator's OWN knob thresholds.
      3. For each nonzero sigma, drive the trait's Concept through the SAME
         native `can_native_identity_field_feedback` mechanism `relax_trait` uses
         (set the Concept's `state` sigma, advance the shared disposition-Mt tick,
         run the rules), but BATCHED across all evidenced traits on the same ticks
         so each moves toward its OWN sigma independently. The DECISION (how far
         each trait moves) is the rule's — one ±1 quantum per strictly-later tick,
         gated on the evidence ledger's log-odds sign. This module never
         hand-writes the crystallised trait; it only supplies the sigma.

    SLOW layer: even with strong sustained modulator readings, each call moves a
    trait by at most `ticks` quanta — the trait integrates the modulator's
    sustained sign over many ticks (the timescale separation that prevents the
    A<->B loop running away; see the module gloss).

    Returns {evidence, levels_before, levels_after, moved} — the signed evidence
    per trait, each trait's level before/after, and which traits moved. A no-op
    on a non-live substrate."""
    hub, ms = ensure_modulator_state(agent, run=run_modulator) if ms is None \
        else (None, ms)
    if ms is None:
        return {"evidence": {}, "levels_before": {}, "levels_after": {},
                "moved": []}
    if run_modulator and ms is not None:
        try:
            disp._native(disp._sub(agent)).run_rules()
        except Exception:
            pass

    ev = modulator_trait_evidence(agent, ms=ms)
    traits = ("abstraction", "openness", "skepticism")
    levels_before = {t: disp.trait_level(agent, t, ensure=True) for t in traits}
    native = disp._native(disp._sub(agent))
    sub = disp._sub(agent)
    ag = disp._agent_node(agent)
    dmt = disp._find_disposition_mt(sub, ag)

    # BATCHED relaxation — set the sustained sigma on EVERY evidenced trait's
    # Concept at once, then advance the SHARED disposition-Mt tick and run the
    # native rules ONCE per step. This is `relax_trait`'s exact mechanism (set
    # `state`, step `can_tick`, run_rules, mirror `identity_field`) applied to
    # all traits SIMULTANEOUSLY. It must be batched, NOT looped per-trait:
    # relax_trait advances the shared tick each call, and a Concept whose sigma
    # is 0 during a tick DECAYS one quantum toward 0 (the identity-feedback
    # rule's own behaviour) — so relaxing traits one-at-a-time would decay the
    # already-moved ones. Driving every evidenced Concept together on the same
    # ticks keeps each trait moving toward ITS OWN sigma independently (the
    # per-trait independence disposition guarantees), the DECISION still the CAN
    # rule's. No affect computed here; only the produced sigma is supplied.
    moved = []
    active = {}
    for t in traits:
        sigma = float(ev.get(t) or 0.0)
        if sigma:
            concept = disp.ensure_trait(agent, t)
            if concept is not None:
                active[t] = (concept, 1.0 if sigma > 0 else -1.0)
    if active and dmt is not None:
        try:
            # SNAPSHOT every disposition Concept's crystallised state before the
            # relaxation. Advancing the shared Mt tick + run_rules DECAYS any
            # Concept whose sigma is 0 one quantum toward 0 (the identity-feedback
            # rule's own behaviour), which would silently erode an ESTABLISHED
            # temperament on a trait this call has NO evidence for. Only evidenced
            # traits should move; we restore the rest to their pre-call fields
            # afterward so an untouched crystallised trait is genuinely unchanged.
            snapshot = {}
            for c in sub.neighbours(dmt, "has_concept"):
                ca = native.node(c)["attrs"]
                snapshot[c] = {
                    "identity_field": float(ca.get("identity_field") or 0.0),
                    "identity_evidence_confirm":
                        int(ca.get("identity_evidence_confirm") or 0),
                    "identity_evidence_disconfirm":
                        int(ca.get("identity_evidence_disconfirm") or 0),
                    "state": float(ca.get("state") or 0.0),
                }
            active_concepts = {c for (c, _s) in active.values()}

            base = int(native.node(dmt)["attrs"].get("can_tick") or 0)
            for i in range(max(1, int(ticks))):
                native.set_attr(dmt, "can_tick", base + i + 1)
                for _t, (concept, sigma) in active.items():
                    native.set_attr(concept, "state", sigma)
                native.run_rules(3000)
            # clear the sustained sigma and mirror the produced fields for each
            # evidenced trait.
            for t, (concept, _sigma) in active.items():
                native.set_attr(concept, "state", 0.0)
                disp._mirror_produced_fields(native, concept, disp.trait_spec(t))
            # RESTORE every NON-evidenced Concept to its snapshot (it must not have
            # moved — no evidence was injected for it), then re-mirror it.
            for c, snap in snapshot.items():
                if c in active_concepts:
                    continue
                native.set_attr(c, "identity_field", snap["identity_field"])
                native.set_attr(c, "identity_evidence_confirm",
                                snap["identity_evidence_confirm"])
                native.set_attr(c, "identity_evidence_disconfirm",
                                snap["identity_evidence_disconfirm"])
                native.set_attr(c, "state", snap["state"])
                cattrs = native.node(c)["attrs"]
                trait_name = cattrs.get("trait")
                if trait_name in disp.TRAIT_REGISTRY:
                    disp._mirror_produced_fields(
                        native, c, disp.trait_spec(trait_name))
        except Exception:
            pass
    levels_after = {t: disp.trait_level(agent, t, ensure=False) for t in traits}
    for t in traits:
        if levels_after[t] != levels_before[t]:
            moved.append(t)
    return {"evidence": {t: ev.get(t, 0.0) for t in traits},
            "levels_before": levels_before, "levels_after": levels_after,
            "moved": moved}


# --------------------------------------------------------------------------- #
# THE TRAIT -> DRIVE HOMEOSTATIC REGULATION TABLE (tasks 3+4).
#
# disposition.disposition_homeostasis_step regulates ONE trait (openness) from
# ONE substrate signal (graph pollution vs starvation). This is the GENERALISATION
# to a TRAIT -> DRIVE table: each cognitive-style trait has a GOVERNING drive /
# modulator whose live deficit is read as signed trait EVIDENCE and integrated by
# the SAME CAN identity-feedback relaxation (relax_trait) — the trait crystallises
# SLOWLY from the FAST drive state, exactly the servo the bridge is built around.
#
# The table (data, not code — the row is (trait, governing drive/modulator, the
# read, the MicroPsi grounding); the driver functions below all share one shape):
#
#   trait        governing drive / modulator      reads                 MicroPsi grounding
#   -----------  -------------------------------  --------------------  --------------------------------
#   abstraction  COMPETENCE (mod_competence)       ms.competence vs      low competence => coarse/concrete
#                                                  competence_lo / hi    processing (drop resolution/order);
#                                                                        high competence => reach for abstraction.
#   skepticism   EXPLORATION/CERTAINTY            leading drive          exploration_urge = the heuristic for
#                (mod_securing / exploration_urge) exploration_urge vs   the DEGREE OF UNCERTAINTY; high urge /
#                                                  uncertainty_hi        low certainty => demand more evidence
#                                                                        before accepting (skepticism UP);
#                                                                        certainty confirmed => relax DOWN.
#   openness     — (NO clean drive; see below)     graph pollution vs    substrate-hygiene homeostasis, NOT a
#                                                  starvation            drive. disposition_homeostasis_step.
#
# WHY THE DECISION IS THE CAN's, NOT PYTHON's.  Each driver READS the governing
# drive/modulator number and hands relax_trait a SIGN (+1/-1) and a tick budget.
# HOW FAR the trait moves is the identity-feedback rule integrating that sign over
# ticks (one +/-1 quantum per strictly-later tick, gated on the evidence ledger's
# log-odds flip). Python computes NO trait value; it only classifies the drive
# state as surplus / deficit / neutral.
#
# NEUTRAL DRIVE => ~0 EVIDENCE => NO DRIFT (default == today).  A drive at its
# resting/unmeasured state injects 0 evidence, so a fresh agent whose drives have
# no activity does NOT drift its personality:
#   · abstraction: competence == 0 is the UNMEASURED state (no learning_progress
#     accumulated yet) — read as NEUTRAL (0), never as "low". Evidence fires only
#     when competence is a MEASURED low (0 < competence < competence_lo) or a
#     measured high (competence >= competence_full - competence_lo).
#   · skepticism: exploration_urge == 0 (no uncertainty signalled) => 0. Fires +1
#     only above uncertainty_hi; fires -1 (certainty confirmed) only when an
#     explicit low-but-active uncertainty is present (0 < urge < uncertainty_lo).
# So the seeded-default modulator build (competence 0, exploration_urge 0) drives
# NOTHING — proven in the neutral-drive no-drift test.
# --------------------------------------------------------------------------- #
_UNCERTAINTY_HI_DEFAULT = 100.0
#: A live exploration_urge BELOW this (but > 0 — an ACTIVE, low-uncertainty drive)
#: is "certainty confirmed": it relaxes skepticism DOWN. urge == 0 is the
#: unmeasured/neutral state and injects NOTHING (no drift), so the confirm mark is
#: strictly positive.
_UNCERTAINTY_LO_DEFAULT = 25.0


def _ms_reading(agent, ms):
    """Locate/return (native, ms, attrs) for a live ModulatorState, minting the
    opt-in state if absent (a homeostasis step is an explicit act, so mint-if-
    absent is correct — same stance as disposition_homeostasis_step's
    ensure_disposition). Returns (native, None, {}) on a non-live substrate."""
    native = disp._native(disp._sub(agent))
    if ms is None:
        _hub, ms = ensure_modulator_state(agent, run=False)
    if ms is None:
        return native, None, {}
    try:
        return native, ms, native.node(ms)["attrs"]
    except Exception:
        return native, ms, {}


def competence_trait_evidence(agent, *, ms=None) -> dict:
    """ABSTRACTION <- the COMPETENCE drive/modulator (mod_competence).

    Reads the live ms.competence accumulator against the modulator's OWN
    competence_lo / (competence_full - competence_lo) marks (the SAME
    competence_lo the fear/anxiety region predicates use for 'low competence')
    and returns a signed abstraction sigma:

      competence >= competence_full - competence_lo  => +1  (reach for abstraction)
      0 < competence < competence_lo                 => -1  (drop to concrete/coarse —
                                                             MicroPsi 'low competence -> coarse')
      competence == 0  (unmeasured, no learning yet)  =>  0  (NEUTRAL — no drift)
      competence in the mid band                      =>  0  (neutral)

    Pure reads + threshold compares; the DECISION (how far) is relax_trait's.
    Returns {sigma, competence, competence_lo, competence_hi}."""
    native, ms, a = _ms_reading(agent, ms)
    if ms is None:
        return {"sigma": 0.0, "competence": 0.0, "competence_lo": 0.0,
                "competence_hi": 0.0}

    def g(key, default):
        v = a.get(key)
        return float(default if v is None else v)

    competence = g("competence", 0.0)
    comp_lo = g("competence_lo", _COMP_LO_DEFAULT)
    comp_full = g("competence_full", _COMP_FULL_DEFAULT)
    comp_hi = comp_full - comp_lo

    sigma = 0.0
    if competence == 0.0:
        sigma = 0.0                      # UNMEASURED == neutral, never "low"
    elif competence >= comp_hi:
        sigma = 1.0                      # high competence => reach for abstraction
    elif competence < comp_lo:
        sigma = -1.0                     # measured-low competence => concrete/coarse
    return {"sigma": sigma, "competence": competence,
            "competence_lo": comp_lo, "competence_hi": comp_hi}


def exploration_trait_evidence(agent, *, ms=None) -> dict:
    """SKEPTICISM <- the EXPLORATION/CERTAINTY drive (exploration_urge, the same
    signal mod_securing reads).

    MicroPsi: 'the strength of the exploration urge is the heuristic for the
    degree of uncertainty in the situation.' High uncertainty (a large
    exploration_urge / an unresolved certainty deficit) means the agent should
    demand MORE evidence before accepting a correspondence — skepticism UP.
    Certainty CONFIRMED (a low-but-active urge) relaxes it DOWN.

      exploration_urge >  uncertainty_hi           => +1  (high uncertainty: skepticism UP)
      0 < exploration_urge < uncertainty_lo         => -1  (certainty confirmed: skepticism DOWN)
      exploration_urge == 0  (no signal / default)  =>  0  (NEUTRAL — no drift)
      exploration_urge in the mid band              =>  0  (neutral)

    Reads the leading drive's exploration_urge (the modulator layer's own
    uncertainty signal) against ms.uncertainty_hi. Pure reads; relax_trait
    decides how far. Returns {sigma, exploration_urge, uncertainty_hi,
    uncertainty_lo, securing}."""
    native, ms, a = _ms_reading(agent, ms)
    if ms is None:
        return {"sigma": 0.0, "exploration_urge": 0.0, "uncertainty_hi": 0.0,
                "uncertainty_lo": 0.0, "securing": 0.0}

    def g(key, default):
        v = a.get(key)
        return float(default if v is None else v)

    unc_hi = g("uncertainty_hi", _UNCERTAINTY_HI_DEFAULT)
    unc_lo = _UNCERTAINTY_LO_DEFAULT
    securing = g("securing", 0.0)

    lead = _leading_drive(native, ms)
    exploration_urge = 0.0
    if lead is not None:
        try:
            v = native.node(lead)["attrs"].get("exploration_urge")
            exploration_urge = float(0.0 if v is None else v)
        except Exception:
            exploration_urge = 0.0

    sigma = 0.0
    if exploration_urge == 0.0:
        sigma = 0.0                      # no uncertainty signalled => neutral
    elif exploration_urge > unc_hi:
        sigma = 1.0                      # high uncertainty => demand more certainty
    elif exploration_urge < unc_lo:
        sigma = -1.0                     # certainty confirmed => relax skepticism
    return {"sigma": sigma, "exploration_urge": exploration_urge,
            "uncertainty_hi": unc_hi, "uncertainty_lo": unc_lo,
            "securing": securing}


# --------------------------------------------------------------------------- #
# SKEPTICISM <- PREDICTION ERROR (the accepted-then-falsified driver).
#
# THE HONEST GAP THIS CLOSES.  exploration_trait_evidence regulates skepticism
# from STANDING UNCERTAINTY (the exploration_urge, a proxy for "how sure am I
# right now"). That is the DISPOSITION-to-explore read, not a learning signal:
# it never notices when the agent ACCEPTED something and was later WRONG. The
# real MicroPsi certainty signal is the OTHER half of the exploration need —
# "Confirmation of uncertain expectations increases certainty and reduces the
# urge; violations or missing predictions increase it" (MICROPSI_STUDY §Cognitive
# needs). A FALSIFIED acceptance is exactly a violated expectation about
# something the agent had already committed to; it should crystallise skepticism
# UP. A sustained run of CONFIRMED acceptances is certainty earned; it should
# relax skepticism DOWN.
#
# THE EXISTING DISCONFIRMATION SIGNAL WE WIRE TO (no invention).  The substrate
# ALREADY records an accepted-then-falsified event: grounded_representation.
# ground_concept(sense_aware=True) reads a NEW definition against what the agent
# already HOLDS for a term, and when the new genus is DISJOINT from the held
# built_from parts it flags the concept `genus_surprise=1` + `needs_reevaluation=1`
# (grounded_representation.py) — "a held grounding was contradicted; do not
# silently overwrite, flag for re-evaluation". That is a genuine PREDICTION
# ERROR on a previously-accepted commitment: the agent grounded the term one way,
# a later reading falsified the genus it committed to. Symmetrically, a grounding
# the agent holds that was NEVER surprised (`structurally_grounded=1` and no
# `genus_surprise`) is a CONFIRMED acceptance — an expectation that held.
#
# We READ those flags as a MAGNITUDE + SIGN and hand relax_trait a signed sigma.
# The DECISION (how far skepticism moves) is the CAN relaxation integrating the
# evidence; Python only counts the surprised vs confirmed groundings and hands a
# sign. This is the SAME sigma/ledger channel exploration_trait_evidence feeds —
# the two skepticism reads SUM into skepticism's single batched relaxation, they
# do not fight (see personality_homeostasis_step).
#
# NEUTRAL => 0 (default == today).  A graph with NO grounded acceptances (no
# structurally_grounded concepts) and NO surprises injects 0 evidence — a fresh
# agent that has accepted nothing does not drift. Only an OBSERVED disconfirmation
# (or an observed run of confirmations) moves the trait.
# --------------------------------------------------------------------------- #
#: A grounding is a CONFIRMED acceptance when the agent structurally grounded it
#: (`structurally_grounded`) OR gave it a built_from genus, and it was NOT later
#: flagged `genus_surprise`. A grounding flagged `genus_surprise` is the
#: FALSIFIED acceptance (the held genus was contradicted by a later reading).
_GENUS_SURPRISE_ATTR = "genus_surprise"
_STRUCTURALLY_GROUNDED_ATTR = "structurally_grounded"


def _count_grounding_outcomes(sub) -> "tuple[int, int]":
    """(confirmed, falsified): scan the graph for the agent's grounded
    acceptances and split them into CONFIRMED (a held structural grounding that
    was never surprised) and FALSIFIED (a held grounding flagged `genus_surprise`
    — the accepted-then-later-contradicted event grounded_representation records).
    A pure mechanical scan of graph state — NO decision, NO affect. A Concept is
    counted as an acceptance only if it is actually GROUNDED (structurally_grounded
    or genus_surprise set), so an ungrounded corpus contributes nothing (neutral).

    This is the DISCONFIRMATION read the skepticism prediction-error driver
    integrates: falsified acceptances are the violated-expectation signal
    (skepticism UP), confirmed acceptances the earned-certainty signal (DOWN)."""
    confirmed = 0
    falsified = 0
    try:
        for cid in sub.nodes("Concept"):
            try:
                a = sub.node(cid)["attrs"]
            except Exception:
                continue
            surprised = bool(a.get(_GENUS_SURPRISE_ATTR))
            grounded = bool(a.get(_STRUCTURALLY_GROUNDED_ATTR))
            if surprised:
                falsified += 1          # accepted, then genus contradicted
            elif grounded:
                confirmed += 1          # accepted, held, never contradicted
    except Exception:
        return (0, 0)
    return (confirmed, falsified)


def skepticism_prediction_error_evidence(agent, *, sub=None) -> dict:
    """SKEPTICISM <- PREDICTION ERROR: the accepted-then-falsified driver.

    Reads the substrate's OWN disconfirmation record — the `genus_surprise`
    flag grounded_representation.ground_concept writes when a HELD grounding's
    genus is contradicted by a later reading (a violated expectation about
    something previously accepted) — and the CONFIRMED acceptances (held
    structural groundings never surprised), and returns a SIGNED skepticism
    sigma:

      any FALSIFIED acceptance present            => +1  (burned once: skepticism UP)
      only CONFIRMED acceptances (none falsified)  => -1  (earned trust: skepticism DOWN)
      no acceptances at all (nothing grounded)     =>  0  (NEUTRAL — no drift)

    THE SIGN, NOT THE DISTANCE.  Like every other trait driver in this module,
    Python reads the numbers and hands a SIGN (+1/-1/0); HOW FAR skepticism moves
    is the CAN identity-feedback rule integrating the sign over ticks (one ±1
    quantum per tick, gated on the evidence-ledger log-odds flip). A single big
    disconfirmation therefore moves skepticism by a BOUNDED amount (one quantum
    per relaxation tick, capped at the ±4 ceiling) — the discrete event cannot
    jump the slow trait; the ledger integrates it. `magnitude` (the falsified /
    confirmed counts and their ratio) is returned for transparency and for a
    caller that wants to spend more `ticks` on a stronger error, but it does NOT
    scale the per-tick step — the trait stays a slow, hysteretic servo.

    FALSIFICATION DOMINATES.  If ANY held grounding is currently flagged
    `genus_surprise`, the sign is +1 regardless of how many confirmations
    coexist: an unresolved contradiction is the live violated expectation the
    agent must answer (become more demanding), the MicroPsi 'violations increase
    the certainty urge' rule. Confirmations relax skepticism only once there are
    NO outstanding falsifications — earned trust is the ABSENCE of live
    disconfirmation, not an average against it.

    NEUTRAL => 0 (default == today).  A graph with nothing grounded (a fresh
    agent, or one that has accepted nothing) reads (0,0) => 0 evidence => the
    trait does not drift.

    Pure reads + the documented classification; NO trait is moved here. Returns
    {sigma, confirmed, falsified, error_ratio}."""
    if sub is None:
        sub = disp._sub(agent)
    if sub is None:
        return {"sigma": 0.0, "confirmed": 0, "falsified": 0,
                "error_ratio": 0.0}
    confirmed, falsified = _count_grounding_outcomes(sub)

    sigma = 0.0
    if falsified > 0:
        sigma = 1.0                      # a live violated expectation => skeptical
    elif confirmed > 0:
        sigma = -1.0                     # only confirmations => earned trust, relax
    total = confirmed + falsified
    error_ratio = (falsified / total) if total else 0.0
    return {"sigma": sigma, "confirmed": confirmed, "falsified": falsified,
            "error_ratio": error_ratio}


def drive_trait_evidence(agent, *, ms=None) -> dict:
    """The whole DRIVE-REGULATED row of the trait->drive table at once: the
    signed evidence for every DRIVE-regulated trait, read from its governing
    drive/modulator. openness is NOT here — it is regulated by graph hygiene, not
    a drive (see the module gloss / disposition.disposition_homeostasis_step).

    SKEPTICISM has TWO governing reads that SUM (see personality_homeostasis_step
    and skepticism_prediction_error_evidence): the STANDING-UNCERTAINTY read
    (exploration_trait_evidence — "how sure am I right now") and the
    PREDICTION-ERROR read (skepticism_prediction_error_evidence — "was something
    I accepted later proved wrong"). This function reports the standing-uncertainty
    read as skepticism's `readings.exploration` component (the prediction-error
    read is folded in at personality_homeostasis_step, where the graph scan
    belongs); `readings.prediction_error` carries the disconfirmation read so the
    combined sign is transparent to the demo/tests.

    Returns {abstraction, skepticism, readings} — the per-trait sigma and the raw
    drive/modulator numbers observed (for transparency / the demo). `skepticism`
    here is the SUM-clamped sign of both reads."""
    _native, ms, _a = _ms_reading(agent, ms)
    comp = competence_trait_evidence(agent, ms=ms)
    expl = exploration_trait_evidence(agent, ms=ms)
    pred = skepticism_prediction_error_evidence(agent)
    # SUM the two skepticism reads (standing uncertainty + prediction error) into
    # one sign — they do NOT fight, they combine into skepticism's single
    # relaxation. A +1 falsification and a -1 confirmed-certainty cancel to 0
    # (no net demand this step); two agreeing reads reinforce to a single +1/-1
    # (the relaxation still moves at most one quantum/tick — the sum sets the
    # SIGN, the CAN rule sets the distance).
    skep_sum = float(expl["sigma"]) + float(pred["sigma"])
    skepticism = 0.0 if skep_sum == 0.0 else (1.0 if skep_sum > 0 else -1.0)
    return {
        "abstraction": comp["sigma"],
        "skepticism": skepticism,
        "readings": {"competence": comp, "exploration": expl,
                     "prediction_error": pred},
    }


def _batched_relax(agent, evidence: dict, *, ticks: int) -> dict:
    """Drive a set of {trait: sigma} through the SHARED disposition-Mt native
    relaxation, BATCHED on the same ticks (relax_trait's exact mechanism applied
    to many Concepts at once) so each evidenced trait moves toward its OWN sigma
    while a trait with NO evidence this step is NOT eroded by the shared-tick
    decay. Snapshots + restores every non-evidenced disposition Concept, exactly
    as crystallise_traits_from_modulator does. Returns {levels_before,
    levels_after, moved}. The DECISION (how far) is the CAN rule's."""
    sub = disp._sub(agent)
    native = disp._native(sub)
    ag = disp._agent_node(agent)
    dmt = disp._find_disposition_mt(sub, ag)

    traits = tuple(evidence.keys())
    levels_before = {t: disp.trait_level(agent, t, ensure=True) for t in traits}

    active = {}
    for t in traits:
        sigma = float(evidence.get(t) or 0.0)
        if sigma:
            concept = disp.ensure_trait(agent, t)
            if concept is not None:
                active[t] = (concept, 1.0 if sigma > 0 else -1.0)

    if active and dmt is not None:
        try:
            snapshot = {}
            for c in sub.neighbours(dmt, "has_concept"):
                ca = native.node(c)["attrs"]
                snapshot[c] = {
                    "identity_field": float(ca.get("identity_field") or 0.0),
                    "identity_evidence_confirm":
                        int(ca.get("identity_evidence_confirm") or 0),
                    "identity_evidence_disconfirm":
                        int(ca.get("identity_evidence_disconfirm") or 0),
                    "state": float(ca.get("state") or 0.0),
                }
            active_concepts = {c for (c, _s) in active.values()}

            base = int(native.node(dmt)["attrs"].get("can_tick") or 0)
            for i in range(max(1, int(ticks))):
                native.set_attr(dmt, "can_tick", base + i + 1)
                for _t, (concept, sigma) in active.items():
                    native.set_attr(concept, "state", sigma)
                native.run_rules(3000)
            for t, (concept, _sigma) in active.items():
                native.set_attr(concept, "state", 0.0)
                disp._mirror_produced_fields(native, concept, disp.trait_spec(t))
            for c, snap in snapshot.items():
                if c in active_concepts:
                    continue
                native.set_attr(c, "identity_field", snap["identity_field"])
                native.set_attr(c, "identity_evidence_confirm",
                                snap["identity_evidence_confirm"])
                native.set_attr(c, "identity_evidence_disconfirm",
                                snap["identity_evidence_disconfirm"])
                native.set_attr(c, "state", snap["state"])
                cattrs = native.node(c)["attrs"]
                trait_name = cattrs.get("trait")
                if trait_name in disp.TRAIT_REGISTRY:
                    disp._mirror_produced_fields(
                        native, c, disp.trait_spec(trait_name))
        except Exception:
            pass

    levels_after = {t: disp.trait_level(agent, t, ensure=False) for t in traits}
    moved = [t for t in traits if levels_after[t] != levels_before[t]]
    return {"levels_before": levels_before, "levels_after": levels_after,
            "moved": moved}


def drive_homeostasis_step(agent, *, ms=None, ticks: int = 1,
                           run_modulator: bool = False) -> dict:
    """ONE homeostatic step for the DRIVE-regulated traits (abstraction +
    skepticism): read each trait's governing drive/modulator deficit as signed
    evidence and let the CAN relaxation integrate it. The drive-side analog of
    disposition.disposition_homeostasis_step (which regulates openness from graph
    hygiene). Over repeated steps a sustained competence regime crystallises
    abstraction UP/DOWN and a sustained exploration/uncertainty regime
    crystallises skepticism UP/DOWN — PRODUCED by the relaxation, not hand-set.

    A neutral drive state (competence 0, exploration_urge 0) yields all-zero
    evidence => a no-op (no drift). Returns {evidence, readings, levels_before,
    levels_after, moved}."""
    _native, ms, _a = _ms_reading(agent, ms)
    if ms is None:
        return {"evidence": {}, "readings": {}, "levels_before": {},
                "levels_after": {}, "moved": []}
    if run_modulator:
        try:
            disp._native(disp._sub(agent)).run_rules()
        except Exception:
            pass
    ev = drive_trait_evidence(agent, ms=ms)
    evidence = {"abstraction": ev["abstraction"], "skepticism": ev["skepticism"]}
    out = _batched_relax(agent, evidence, ticks=ticks)
    return {"evidence": evidence, "readings": ev["readings"],
            "levels_before": out["levels_before"],
            "levels_after": out["levels_after"], "moved": out["moved"]}


def personality_homeostasis_step(agent, *, mint_result: Optional[dict] = None,
                                 analogies: Optional[list] = None,
                                 ms=None, ticks: int = 1,
                                 deadband: float = 0.15,
                                 run_modulator: bool = False) -> dict:
    """RUN THE WHOLE TRAIT -> DRIVE REGULATION TABLE in one call: openness (from
    graph pollution/starvation) + abstraction (from the competence drive) +
    skepticism (from the exploration/certainty drive), each reading its GOVERNING
    signal and crystallising via the same CAN relaxation. The single entry point
    the task asks for — the generalisation of disposition_homeostasis_step from
    openness-only to the full personality vector.

    THREE SIGNALS, TWO KINDS, ONE BATCHED RELAXATION.  The three traits read
    signals that are different IN KIND (see the openness reconciliation in the
    module gloss):

      · OPENNESS is regulated by SUBSTRATE HYGIENE (thin minted leaves vs dark
        relational surface) — NOT a drive. Its evidence sign comes from
        disposition.homeostasis_signals' `net` (starved => +, polluted => -,
        balanced within `deadband` => 0). It is the ONE trait that does not
        complete the drive model; forcing it onto competence would be a reframe
        (its remedy is bidirectional by FAILURE TYPE — pollution down, starvation
        up — which a single unidirectional competence scalar cannot encode), so it
        keeps its own hygiene signal.

      · ABSTRACTION + SKEPTICISM are DRIVE-regulated: their evidence signs come
        from competence_trait_evidence / exploration_trait_evidence.

    SKEPTICISM HAS TWO READS THAT SUM (the prediction-error driver).  skepticism
    is now regulated by BOTH:
      · the STANDING-UNCERTAINTY read (exploration_trait_evidence): the live
        exploration_urge, MicroPsi's heuristic for "how uncertain am I right now"
        — high urge => +1 (demand certainty), confirmed low urge => -1.
      · the PREDICTION-ERROR read (skepticism_prediction_error_evidence): the
        accepted-then-falsified signal — a HELD grounding the agent committed to
        that a later reading CONTRADICTED (grounded_representation's
        `genus_surprise` flag). A live falsification => +1 (burned once, become
        more demanding); only confirmed acceptances => -1 (earned trust, relax).
    drive_trait_evidence SUMS the two into skepticism's single sign: they do NOT
    fight — they are the two halves of the MicroPsi certainty need (the standing
    urge to explore + the learned violation/confirmation of expectations). A +1
    falsification and a -1 confirmed-certainty cancel to 0 (no net demand this
    step); two agreeing reads reinforce to one +1/-1. The SUM sets the SIGN; the
    CAN relaxation still moves skepticism at most one quantum/tick toward it, so
    a single big disconfirmation is bounded — it cannot jump the slow trait.

    All three signs are then fed to ONE batched relaxation on the shared
    disposition Mt. This MUST be a single batch, not two separate homeostasis
    passes: each pass advances the shared can_tick and a Concept with sigma 0
    during a tick DECAYS one quantum (the identity-feedback rule's own behaviour),
    so running openness's relaxation and the drive relaxation as SEPARATE passes
    would have each erode the other's freshly-moved traits. Batching every
    evidenced trait onto the SAME ticks moves each toward ITS OWN sign at the same
    1-quantum/tick rate, and the snapshot/restore leaves any UN-evidenced trait
    exactly where it was — the per-trait independence disposition guarantees,
    preserved across all three regulators at once.

    The live overlay pull for openness is still written (dynamical:disposition_
    pull reads the momentary homeostatic pressure), matching
    disposition_homeostasis_step.

    NEUTRAL => NO DRIFT.  A balanced graph (|net| < deadband) => 0 openness
    evidence; a neutral drive (competence 0, exploration_urge 0) => 0 abstraction
    and 0 standing-uncertainty skepticism; and a graph with NOTHING grounded
    (no accepted groundings, no falsifications) => 0 prediction-error skepticism.
    A fresh agent does not drift its personality.

    NO RUNAWAY.  Every trait moves at most `ticks` quanta per call, capped at
    +/-4; the drives/graph are the FAST layer, the trait the SLOW one — the same
    servo timescale-separation the bridge is built on. Proven convergent in the
    demo/tests.

    Returns {evidence, signals, readings, pull, vector_before, vector_after,
    moved} — the per-trait evidence sign, the openness graph signals, the
    drive/modulator readings, the openness overlay pull, the whole trait vector
    before/after, and which traits moved."""
    disp.ensure_traits(agent)
    vector_before = disp.trait_vector(agent, ensure=True)

    # OPENNESS evidence — graph-hygiene homeostasis (the one non-drive trait).
    sig = disp.homeostasis_signals(agent, mint_result=mint_result,
                                   analogies=analogies)
    net = float(sig["net"])
    openness_ev = 0.0
    if abs(net) >= float(deadband):
        openness_ev = 1.0 if net > 0 else -1.0

    # ABSTRACTION + SKEPTICISM evidence — the drive-regulated row. SKEPTICISM
    # additionally reads the PREDICTION-ERROR signal (accepted-then-falsified),
    # which is a GRAPH fact (grounded_representation's genus_surprise flag), not a
    # drive read — so it is honored even on a graph with no modulator state. When
    # a modulator state exists, drive_trait_evidence sums both skepticism reads;
    # when it does not, we still read the prediction-error alone.
    _native, ms, _a = _ms_reading(agent, ms)
    if run_modulator and ms is not None:
        try:
            disp._native(disp._sub(agent)).run_rules()
        except Exception:
            pass
    if ms is not None:
        drive_ev = drive_trait_evidence(agent, ms=ms)
    else:
        pred = skepticism_prediction_error_evidence(agent)
        drive_ev = {"abstraction": 0.0, "skepticism": float(pred["sigma"]),
                    "readings": {"prediction_error": pred}}

    evidence = {
        "openness": openness_ev,
        "abstraction": float(drive_ev.get("abstraction") or 0.0),
        "skepticism": float(drive_ev.get("skepticism") or 0.0),
    }

    # ONE batched relaxation across ALL three traits (see the docstring — a single
    # batch is required so the passes do not erode each other on the shared Mt).
    out = _batched_relax(agent, evidence, ticks=ticks)

    # LIVE overlay pull for openness (the momentary homeostatic pressure), mirroring
    # disposition_homeostasis_step's pull_disposition write.
    pull = 0.0
    if openness_ev:
        try:
            pull = disp.pull_disposition(agent, net)
        except Exception:
            pull = 0.0

    vector_after = disp.trait_vector(agent, ensure=False)
    moved = [t for t in vector_after
             if vector_after[t] != vector_before.get(t)]
    return {"evidence": evidence, "signals": sig,
            "readings": drive_ev.get("readings", {}), "pull": pull,
            "vector_before": vector_before, "vector_after": vector_after,
            "moved": moved}


__all__ = [
    "EMOTION_HUB_EDGE", "MODULATOR_STATE_EDGE",
    "ABSTRACTION_BIAS_ATTR", "OPENNESS_BIAS_ATTR", "SKEPTICISM_BIAS_ATTR",
    "trait_bias",
    "ensure_modulator_state",
    "sync_traits_to_modulator",
    "modulator_trait_evidence", "crystallise_traits_from_modulator",
    # the trait -> drive homeostatic regulation table (tasks 3+4)
    "competence_trait_evidence", "exploration_trait_evidence",
    "skepticism_prediction_error_evidence",
    "drive_trait_evidence", "drive_homeostasis_step",
    "personality_homeostasis_step",
]
