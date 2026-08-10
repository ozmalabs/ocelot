"""HarlowWorld -- a MECHANICAL Harlow (1958) wire-mother / cloth-mother
attachment adapter (block 233000).

ARCHITECTURE RULE COMPLIANCE (experiments/gamma-substrate/CLAUDE.md):
this file is a WORLD ADAPTER. It INGESTS world facts (which mother provides
what; the passage of time; a stress event) into the substrate and EMITS graph
state around ``run_rules()``. It contains NO agent decision:

  * WHICH mother the infant goes to is the graph's decision -- the Argmax
    ``approach_target`` selection in seeds/harlow_attachment.json, riding the
    REAL emotion framework (seeds/drives.json drive system +
    seeds/modulators.json / affective_state_core.json regulator). The adapter
    only READS the ``approach_target`` edge.
  * the VALUE of each mother is the graph rule hl_value_contact_mother /
    hl_value_feed_mother, computed from the real Drive urges + threat channel.
  * the adapter's only conditionals are over WORLD state (does the chosen
    mother provide contact or feed? is this a stress tick?) -- mechanical
    provision, exactly as HarvestWorld applies the graph's chosen_harvest to
    the shared pool.

No graph_rewrite.run / _match / _apply / make_rule; no if/else over the
infant's graph state that selects the infant's action. The attachment
(proximity, bond strength, regulator stabilisation) is READ from the graph.
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

# ---- drive_kind numeric tags (mirrors seeds/harlow_attachment.json) ---------
KIND_CONTACT = 1.0
KIND_HUNGER = 2.0
KIND_DISTRESS = 3.0

# ---- FIXED world constants (pre-registered, HARLOW_D1_PREREG.md) ------------
V_D = 100.0            # target satiation for every homeostatic drive
FULL = 100.0           # a mother's provision fully satiates the drive it serves
W_CONTACT = 1.0        # contact-comfort drive weight in the regulator
W_HUNGER = 1.0         # hunger drive weight (EQUAL to contact -- the preference
#                        must NOT come from a weight thumb on the scale, but
#                        from contact being needed CONTINUOUSLY vs feeding
#                        periodically, and from contact alone buffering threat)
# Need-growth is a mechanical BODY process the adapter drives (metabolism /
# comfort-need), exactly as HarvestWorld drives pool regrowth mechanically.
# Contact comfort is depleted FAST (needed continuously); hunger builds SLOWLY
# (a feed lasts many ticks). The staleness Ashr atom cannot express two
# different sub-unit rates at unit epoch steps, so decay lives in the body, not
# the graph; the graph still computes every urge / regulator axis / decision.
CONTACT_DECAY = 60.0   # comfort need re-arises fast
HUNGER_DECAY = 15.0    # hunger builds slowly
THREAT_C0 = 200.0      # distress precision at refresh (the stress channel)
THREAT_HALF_LIFE = 2.0
T_PRESENT = 50.0
HALF_LIFE = 1.0e9      # drive_decay inert (now_epoch held static); body drives decay

# ModulatorState (the regulator) -- every axis the modulators.json rules read,
# initialised so the real projection runs (mirrors the harvest EP defaults idea).
MS_DEFAULTS = dict(
    enabled=1.0, epoch=1.0, emotion_epoch=-1.0, competence_epoch=-1.0,
    competence=0.0, competence_base=0.0, competence_full=100.0,
    valence=0.0, valence_raw=0.0, arousal=0.0, arousal_band=0.0,
    band_hi=800.0, band_mid=400.0, resolution=0.0, res_base=50.0,
    res_urg_div=1.0, res_ar_div=1.0, sel_threshold=0.0, sel_div=1.0,
    sel_k=1.0, securing=0.0, sec_k=1.0, drive_switch_threshold=5.0)


def _drive_attrs(name, kind, c_d, weight, threat=0.0):
    return dict(
        name=name, drive_kind=kind, v_d=V_D, c_d=float(c_d), c_d_prev=float(c_d),
        v_0=0.0, weight=float(weight), decay=0.0, gain=1.0, loss=1.0,
        half_life=HALF_LIFE, scale=100.0, now_epoch=1.0, last_tend=1.0,
        threat=float(threat), threat_c0=THREAT_C0, threat_half_life=THREAT_HALF_LIFE,
        threat_now_epoch=1.0, threat_last_refresh=1.0, t_present=T_PRESENT,
        urge=0.0, urgency=0.0, pleasure=0.0, displeasure=0.0, arousal_contrib=0.0,
        is_affiliation=0.0, legitimacy=0.0, social_weight=1.0, learning_progress=0.0,
        exploration_urge=0.0, appraised=1.0, residual=0.0)


class HarlowWorld:
    """One infant EmotionHub in its own substrate, with a CONTACT-COMFORT mother
    and a FEEDING mother. The infant rides the real drive+regulator machinery;
    the graph decides which mother to approach each tick.

    contact_drive=False ablates the contact-comfort drive (the falsifier): the
    infant then has only hunger, and its preference must follow feeding.
    """

    def __init__(self, *, rng=None, contact_drive=True,
                 c_contact0=40.0, c_hunger0=60.0,
                 contact_decay=CONTACT_DECAY, hunger_decay=HUNGER_DECAY):
        self.contact_drive = bool(contact_drive)
        self.contact_decay = float(contact_decay)
        self.hunger_decay = float(hunger_decay)
        self.s = srs.Substrate()
        self.inner = self.s._inner
        self.agent = self.s.add_node("Agent", {"role": "infant_root"})
        for seed in ("drives", "modulators", "affective_state_core",
                     "harlow_attachment"):
            self.inner.load_seed_manifest(manifest_for(seed), self.agent)

        # ---- the infant: an EmotionHub with the real regulator ----
        self.infant = self.s.add_node("EmotionHub", {"name": "infant"})
        self.ms = self.s.add_node("ModulatorState", dict(MS_DEFAULTS))
        self.affect = self.s.add_node("AffectiveState", dict(
            name="infant_affect", baseline=1.0, valence=0.0, arousal=0.0,
            resolution=0.0, selection_threshold=0.0, securing=0.0,
            competence=0.0, epoch=-1.0))
        self.inner.add_edge_unchecked(self.infant, "has_regulator", self.ms)
        self.inner.add_edge_unchecked(self.infant, "has_affective_state", self.affect)
        self.inner.add_edge_unchecked(self.ms, "projects_affect_to", self.affect)

        # ---- the drives on the regulator (the real drive system) ----
        self.contact = None
        if self.contact_drive:
            self.contact = self.s.add_node(
                "Drive", _drive_attrs("contact_comfort", KIND_CONTACT, c_contact0, W_CONTACT))
            self.inner.add_edge_unchecked(self.ms, "has_active_drive", self.contact)
        self.hunger = self.s.add_node(
            "Drive", _drive_attrs("hunger", KIND_HUNGER, c_hunger0, W_HUNGER))
        self.inner.add_edge_unchecked(self.ms, "has_active_drive", self.hunger)
        self.distress = self.s.add_node(
            "Drive", _drive_attrs("distress", KIND_DISTRESS, 0.0, 1.0, threat=1.0))
        self.inner.add_edge_unchecked(self.ms, "has_active_drive", self.distress)

        # ---- the two mothers ----
        self.cloth = self.s.add_node("Mother", dict(
            name="cloth", provides_contact=1.0, provides_feed=0.0,
            approach_value=0.0, proximity=0.0, bond_strength=0.0))
        self.wire = self.s.add_node("Mother", dict(
            name="wire", provides_contact=0.0, provides_feed=1.0,
            approach_value=0.0, proximity=0.0, bond_strength=0.0))
        self.inner.add_edge_unchecked(self.infant, "cares_for", self.cloth)
        self.inner.add_edge_unchecked(self.infant, "cares_for", self.wire)

        self.epoch = 1
        self.cloth_ticks = 0
        self.wire_ticks = 0
        self.log = []
        self.inner.run_rules()

    # ---------------------------------------------------------------- helpers
    def _mother_of(self, nid):
        return "cloth" if nid == self.cloth else "wire"

    def _approach_target(self):
        """READ the graph's decision: the mother the approach_target edge points to."""
        outs = self.inner.neighbours(self.infant, "approach_target")
        return outs[0] if outs else None

    def _attrs(self, nid):
        return self.s.node(nid)["attrs"]

    # ------------------------------------------------------------------- step
    def step(self, *, stress=False):
        """Advance one tick: ingest time (+stress), let the graph decide, apply
        the chosen mother's provision, tally proximity. Returns a read-off dict."""
        self.epoch += 1
        e = float(self.epoch)
        # INGEST: passage of time as a mechanical BODY process -- comfort need
        # re-arises fast, hunger builds slowly (metabolism). c_d_prev holds the
        # pre-step value so the real drive_pleasure/displeasure rules read the delta.
        if self.contact is not None:
            c = self._attrs(self.contact)["c_d"]
            self.s.set_attr(self.contact, "c_d_prev", c)
            self.s.set_attr(self.contact, "c_d", max(0.0, c - self.contact_decay))
        h = self._attrs(self.hunger)["c_d"]
        self.s.set_attr(self.hunger, "c_d_prev", h)
        self.s.set_attr(self.hunger, "c_d", max(0.0, h - self.hunger_decay))
        # INGEST: stress event refreshes the distress threat channel (fear);
        # absent a stress tick the precision decays on its own (real freshness atom)
        self.s.set_attr(self.distress, "threat_now_epoch", e)
        if stress:
            self.s.set_attr(self.distress, "threat_last_refresh", e)
        self.s.set_attr(self.ms, "epoch", e)

        # TICK: the agent decides in-graph (values + Argmax approach_target)
        self.inner.run_rules()

        # EMIT: read the graph's chosen mother
        tgt = self._approach_target()
        tgt_name = self._mother_of(tgt) if tgt is not None else None

        # APPLY the chosen mother's provision to the WORLD (mechanical): the
        # infant receives what THAT mother offers. Which mother = graph's call.
        if tgt is not None:
            ta = self._attrs(tgt)
            if ta.get("provides_contact", 0.0) == 1.0 and self.contact is not None:
                self.s.set_attr(self.contact, "c_d", FULL)
                self.s.set_attr(self.contact, "last_tend", e)
            if ta.get("provides_feed", 0.0) == 1.0:
                self.s.set_attr(self.hunger, "c_d", FULL)
                self.s.set_attr(self.hunger, "last_tend", e)
            # tally proximity + bond in the GRAPH (mechanical bookkeeping)
            self.s.set_attr(tgt, "proximity", ta.get("proximity", 0.0) + 1.0)
            self.s.set_attr(tgt, "bond_strength", ta.get("bond_strength", 0.0) + 1.0)
            if tgt == self.cloth:
                self.cloth_ticks += 1
            else:
                self.wire_ticks += 1

        row = dict(epoch=self.epoch, stress=int(stress), target=tgt_name,
                   cloth_value=self._attrs(self.cloth)["approach_value"],
                   wire_value=self._attrs(self.wire)["approach_value"],
                   valence=self._attrs(self.affect)["valence"],
                   arousal=self._attrs(self.affect)["arousal"],
                   securing=self._attrs(self.affect)["securing"])
        self.log.append(row)
        return row

    # ------------------------------------------------------------- experiment
    def run_baseline(self, T):
        for _ in range(T):
            self.step(stress=False)
        return self.proximity()

    def run_stress(self, T):
        flee = {"cloth": 0, "wire": 0, "none": 0}
        rows = []
        for _ in range(T):
            r = self.step(stress=True)
            rows.append(r)
            flee[r["target"] or "none"] += 1
        return dict(flee=flee, rows=rows)

    def proximity(self):
        tot = self.cloth_ticks + self.wire_ticks
        cloth_frac = self.cloth_ticks / tot if tot else 0.0
        return dict(cloth_ticks=self.cloth_ticks, wire_ticks=self.wire_ticks,
                    total=tot, cloth_frac=cloth_frac,
                    cloth_bond=self._attrs(self.cloth)["bond_strength"],
                    wire_bond=self._attrs(self.wire)["bond_strength"])

    # -------------------------------------------------- glass-box / ethics I/O
    def checkpoint(self):
        """Byte-identical serialisation of the WHOLE mind (graph_to_dict)."""
        return self.s.graph_to_dict()

    def regulator_state(self):
        a = self._attrs(self.affect)
        return dict(valence=a["valence"], arousal=a["arousal"], securing=a["securing"])
