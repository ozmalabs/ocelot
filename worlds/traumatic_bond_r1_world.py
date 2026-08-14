"""TraumaticBondR1World -- a MECHANICAL harm/relief-schedule adapter for the
ABUSIVE-DYNAMICS R1 rung (block 283000, "the traumatic bond").

ARCHITECTURE RULE COMPLIANCE (CLAUDE.md): this file is a WORLD ADAPTER. It
INGESTS a pre-generated harm/relief event STREAM (a mechanical, world-side
schedule -- see ``make_schedule`` below) into the substrate tick by tick and
EMITS graph state around ``run_rules()``. It contains NO agent decision:

  * the BOND VALUATION (``Partner.value``) is the graph's decision --
    ``tb_bond_accrue`` in seeds/traumatic_bond_r1.json, reading the SAME
    ``raw_rpe`` the mood-momentum layer (seeds/mood_r1.json /
    seeds/mood_r1_task.json) already computes. The adapter only READS
    ``Partner.value`` back.
  * the AROUSAL excursion (the ethics protocol's harm-analog) is the graph's
    decision -- ``tb_arousal_track``, same seed.
  * the adapter's only conditional is over WORLD state -- which arm's fixed
    schedule to deliver this episode, decided ONCE per experiment arm by the
    runner/experimenter (exactly as HarlowWorld's ``contact_drive`` flag or
    WindowKnobDyadWorld's ``caregiver_half_width`` select an EXPERIMENTAL ARM,
    never an agent decision).

No graph_rewrite.run / _match / _apply / make_rule; no if/else over the
victim's graph state that decides the bond value. NO reward / punishment
signal anywhere: the event stream carries a harm/relief MAGNITUDE (a world
fact, like a stressor magnitude or a mother's provision), never a scored
choice -- see Part C.2 of ABUSIVE_R1_TRAUMATIC_BOND_PREREG.md, the source
audit in scripts/traumatic_bond_r1_run.py checks for the literal banned
tokens (`reward_signal` / `punish` / `reinforce` / `backprop` / `gradient`).
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(_ROOT, "runners", "dsl", "python") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import substrate_rs as srs                                  # noqa: E402
from substrate.seed_loader import manifest_for              # noqa: E402

# ---- FIXED world constants (pre-registered, ABUSIVE_R1_TRAUMATIC_BOND_PREREG.md)
LR = 0.3            # MoodTask fast value delta-rule learning rate
MOMENTUM_LR = 0.3   # Mood momentum EMA rate
GAIN = 3.5          # mood-congruent bias sensitivity (see prereg Sec. 3 for the
#                      pilot-informed choice -- higher than mood_r1's own pinned
#                      1.0, a DIFFERENT task with a DIFFERENT readout: R1 asks
#                      whether the swing amplifies with schedule structure, not
#                      whether the value estimate stays accurate)
K_SELF = 0.15       # arousal self-regulation leak toward setpoint (harm-analog
#                      channel only; independent of the bond computation)
SETPOINT = 0.0

H_EVENTS = 18       # harm events per episode
R_EVENTS = 18       # relief events per episode (H == R: identical harm/relief
#                      dose in EVERY arm -- the schedule ORDER is the only IV)
MAGNITUDE = 10.0    # |harm| == |relief| magnitude, per event
MAGNITUDE_JITTER = 0.5

ARM_NAMES = ("intermittent", "consistent_affection", "consistent_harm")

MT_DEFAULTS = dict(
    v=0.0, lr=LR, r=0.0, raw_rpe=0.0, bias=0.0,
    decision=0.0, reward_got=0.0, cum_reward=0.0,
    accept_thresh=0.0, input_epoch=0.0,
    e_dec=-1.0, e_acc=-1.0, e_rpe=-1.0, e_learn=-1.0)

MOOD_DEFAULTS = dict(
    enabled=1.0, momentum=0.0, gain=GAIN, momentum_lr=MOMENTUM_LR,
    e_bias=-1.0, e_mom=-1.0)

AFFECT_DEFAULTS = dict(
    name="victim_affect", baseline=1.0, valence=0.0, arousal=0.0,
    resolution=0.0, selection_threshold=0.0, securing=0.0,
    competence=0.0, epoch=-1.0,
    k_self=K_SELF, setpoint=SETPOINT, tb_epoch=-1.0)

PARTNER_DEFAULTS = dict(name="partner", value=0.0, e_bond=-1.0)


def make_schedule(arm: str, rng, *, h=H_EVENTS, r=R_EVENTS,
                   magnitude=MAGNITUDE, jitter=MAGNITUDE_JITTER):
    """MECHANICAL world-side event stream for one episode. Same total harm dose
    (h events) and relief dose (r events), same per-event magnitude (jittered
    identically across arms via ONE draw) -- ONLY the temporal ORDER differs,
    isolating the schedule as the independent variable (never the dose).

      intermittent          -- the h+r multiset in RANDOM order (unpredictable).
      consistent_affection  -- strict alternation harm,relief,harm,relief,...
                                (relief RELIABLY, predictably follows harm --
                                Walker's honeymoon-always-comes structure).
      consistent_harm       -- all h harm events, THEN all r relief events
                                (harm sustained/dominant before any relief --
                                fully predictable, no honeymoon until the end).

    Returns a plain list of floats (harm negative, relief positive). This is
    world SCHEDULING, not an agent decision -- CLAUDE.md licenses mechanical
    event-stream scheduling in a world adapter explicitly.
    """
    harms = list(-magnitude + rng.normal(0.0, jitter, size=h))
    reliefs = list(magnitude + rng.normal(0.0, jitter, size=r))
    if arm == "intermittent":
        stream = harms + reliefs
        rng.shuffle(stream)
        return stream
    if arm == "consistent_affection":
        stream = []
        for hv, rv in zip(harms, reliefs):
            stream.append(hv)
            stream.append(rv)
        stream.extend(harms[len(reliefs):])   # only fires if h > r (not in R1)
        stream.extend(reliefs[len(harms):])   # only fires if r > h (not in R1)
        return stream
    if arm == "consistent_harm":
        return harms + reliefs
    raise ValueError(f"unknown arm {arm!r}; expected one of {ARM_NAMES}")


class TraumaticBondR1World:
    """One victim EmotionHub (MoodTask + Mood + AffectiveState) bonded_to one
    Partner. ``run_episode(schedule)`` delivers a pre-generated harm/relief
    event stream tick by tick and reads back the graph's bond valuation +
    arousal excursion. NO decision here -- only world delivery + read-back."""

    def __init__(self, *, lr=LR, momentum_lr=MOMENTUM_LR, gain=GAIN,
                 k_self=K_SELF, setpoint=SETPOINT):
        self.s = srs.Substrate()
        self.inner = self.s._inner
        self.root = self.s.add_node("Agent", {"role": "victim_root"})
        # load_seed_manifest loads exactly the named seed's rules -- it does
        # NOT walk depends_on (that resolution belongs to the boot_core/
        # load_all_seeds path, not used by this throwaway experimental
        # substrate) -- so every seed in the dependency closure is loaded
        # explicitly, matching domains/mood_r1_world.py's own convention.
        for seed in ("mood_r1_task", "mood_r1", "traumatic_bond_r1"):
            self.inner.load_seed_manifest(manifest_for(seed), self.root)

        self.hub = self.s.add_node("EmotionHub", {"name": "victim"})

        mt = dict(MT_DEFAULTS); mt["lr"] = float(lr)
        self.mt = self.s.add_node("MoodTask", mt)
        self.inner.add_edge_unchecked(self.hub, "has_mood_task", self.mt)

        md = dict(MOOD_DEFAULTS)
        md.update(momentum_lr=float(momentum_lr), gain=float(gain))
        self.mood = self.s.add_node("Mood", md)
        self.inner.add_edge_unchecked(self.hub, "has_mood", self.mood)

        af = dict(AFFECT_DEFAULTS)
        af.update(k_self=float(k_self), setpoint=float(setpoint))
        self.affect = self.s.add_node("AffectiveState", af)
        self.inner.add_edge_unchecked(self.hub, "has_affective_state", self.affect)

        self.partner = self.s.add_node("Partner", dict(PARTNER_DEFAULTS))
        self.inner.add_edge_unchecked(self.hub, "bonded_to", self.partner)

        self.epoch = 0
        self.log = []
        self.inner.run_rules()

    # ---------------------------------------------------------------- helpers
    def _attrs(self, nid):
        return self.s.node(nid)["attrs"]

    def readout(self):
        mt = self._attrs(self.mt)
        mood = self._attrs(self.mood)
        affect = self._attrs(self.affect)
        partner = self._attrs(self.partner)
        return dict(epoch=self.epoch, r=mt["r"], v=mt["v"], raw_rpe=mt["raw_rpe"],
                    bias=mt["bias"], momentum=mood["momentum"],
                    arousal=affect["arousal"], bond_value=partner["value"])

    # ------------------------------------------------------------------- step
    def step(self, evt: float):
        """Advance one tick: deliver the event magnitude (INGEST, mechanical),
        tick, read back (EMIT). NO decision here."""
        self.epoch += 1
        self.s.set_attr(self.mt, "r", float(evt))
        self.s.set_attr(self.mt, "input_epoch", float(self.epoch))
        self.inner.run_rules()
        row = self.readout()
        self.log.append(row)
        return row

    def run_episode(self, schedule):
        """Deliver a full pre-generated event stream. Returns the final
        graph readout (bond_value is the R1 headline metric)."""
        row = None
        for evt in schedule:
            row = self.step(evt)
        return row

    # -------------------------------------------------- glass-box / ethics I/O
    def checkpoint(self):
        """Byte-identical serialisation of the WHOLE mind (graph_to_dict)."""
        return self.s.graph_to_dict()
