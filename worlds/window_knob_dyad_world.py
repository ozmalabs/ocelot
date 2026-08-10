"""WindowKnobDyadWorld -- a MECHANICAL BIDIRECTIONAL infant/caregiver dyad world
(block 241000) for the WINDOW-AS-A-KNOB rung. DEEPENS block 239000's
CoregDyadWorld (worlds/coreg_dyad_world.py): reuses its FIXED world constants and
the REAL AffectiveState.arousal + WindowOfTolerance node, and adds two things
239000 left open --

  (1) window WIDTH as a settable INDEPENDENT VARIABLE (the knob):
      ``infant_half_width`` / ``caregiver_half_width`` set the tolerated band
      [lo,hi] = [-half_width, +half_width]; WIDTH = hi-lo = 2*half_width;
  (2) a BIDIRECTIONAL dyad: the caregiver now has its OWN dynamic arousal, its
      OWN window, and a ``regulated`` flag that flips when its arousal leaves its
      own band -- the infant's distress PULLS the caregiver (mutual entrainment),
      and a NARROW-window caregiver is pulled into CO-DYSREGULATION.

ARCHITECTURE RULE COMPLIANCE (experiments/gamma-substrate/CLAUDE.md):
this file is a WORLD ADAPTER. It INGESTS world facts (a stressor arrives; a
caregiver is present with a given window WIDTH; the passage of a tick) into the
substrate and EMITS graph state around ``run_rules()``. Every regulation /
coupling / dysregulation-onset DECISION is a graph rule
(seeds/window_knob_coreg.json), riding the REAL AffectiveState.arousal. The
adapter's only conditionals are over WORLD state (is this a stress tick? is a
caregiver present?). No graph_rewrite.run / _match / _apply / make_rule; no
if/else over arousal that decides regulation -- regulation is READ from the graph.
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
# REUSE block 239000's frozen world constants (extend, do not rebuild).
from worlds.coreg_dyad_world import (                       # noqa: E402
    SETPOINT, K_SELF, K_CO, MIN_HALF_WIDTH, RETURN_CAP)

# ---- NEW caregiver-side constants (pre-registered, WINDOW_KNOB_PREREG.md) ----
K_CG = 0.25       # caregiver's leaky-EMA pull gain TOWARD the infant (contagion)
K_CG_SELF = 0.30  # a REGULATED caregiver's self-regulation gain toward setpoint

# default window half-widths (the knob; overridden per experiment arm)
INFANT_HALF_WIDTH0 = 30.0
CAREGIVER_HALF_WIDTH0 = 90.0   # a WIDE, well-regulated caregiver by default


class WindowKnobDyadWorld:
    """One INFANT agent and (optionally) one CAREGIVER agent, BOTH with a REAL
    AffectiveState.arousal and a WindowOfTolerance band whose WIDTH is a settable
    knob. A stressor pushes the infant; the graph decides dysregulation, the
    bidirectional pulls, co-dysregulation, and return.

    caregiver_present=False -> no attended_by edge (the infant is ALONE:
                               self-regulation only; used for the single-agent
                               onset-threshold measurement).
    """

    def __init__(self, *, infant_half_width=INFANT_HALF_WIDTH0, stress_mag=100.0,
                 caregiver_present=True, caregiver_half_width=CAREGIVER_HALF_WIDTH0,
                 k_self=K_SELF, k_co=K_CO, k_cg=K_CG, k_cg_self=K_CG_SELF):
        self.infant_half_width = float(infant_half_width)
        self.caregiver_half_width = float(caregiver_half_width)
        self.stress_mag = float(stress_mag)
        self.caregiver_present = bool(caregiver_present)

        self.s = srs.Substrate()
        self.inner = self.s._inner
        self.root = self.s.add_node("Agent", {"role": "dyad_root"})
        for seed in ("affective_state_core", "window_knob_coreg"):
            self.inner.load_seed_manifest(manifest_for(seed), self.root)

        # ---- the INFANT: REAL AffectiveState.arousal + a WindowOfTolerance ----
        self.infant = self.s.add_node("Agent", {"role": "infant"})
        self.iaff = self.s.add_node("AffectiveState", dict(
            name="infant_affect", baseline=1.0, valence=0.0, arousal=SETPOINT,
            resolution=0.0, selection_threshold=0.0, securing=0.0,
            competence=0.0, epoch=-1.0,
            tick_epoch=0.0, sr_epoch=0.0, cr_epoch=0.0,
            k_self=float(k_self), k_co=float(k_co), setpoint=SETPOINT,
            dysregulated=0.0, dysreg_kind=0.0, in_episode=0.0,
            is_infant=1.0))   # discriminator: infant rules scope on this
        self.inner.add_edge_unchecked(self.infant, "has_affective_state", self.iaff)

        hw = self.infant_half_width
        self.wot = self.s.add_node("WindowOfTolerance", dict(
            name="infant_window", lo=-hw, hi=hw, half_width=hw,
            min_half_width=MIN_HALF_WIDTH))
        self.inner.add_edge_unchecked(self.infant, "has_window", self.wot)

        self.stressor = self.s.add_node("Stressor", dict(
            name="stressor", magnitude=self.stress_mag, armed=0.0, epoch=0.0))
        self.inner.add_edge_unchecked(self.infant, "has_stressor", self.stressor)

        # ---- the CAREGIVER: its OWN REAL arousal + its OWN window (the knob) ----
        self.caregiver = self.caff = self.cgwot = None
        if self.caregiver_present:
            self.caregiver = self.s.add_node("Agent", {"role": "caregiver"})
            self.caff = self.s.add_node("AffectiveState", dict(
                name="caregiver_affect", baseline=1.0, valence=0.0,
                arousal=SETPOINT, resolution=0.0, selection_threshold=0.0,
                securing=0.0, competence=0.0, epoch=-1.0,
                tick_epoch=0.0, cp_epoch=0.0, cs_epoch=0.0,
                k_cg=float(k_cg), k_cg_self=float(k_cg_self), setpoint=SETPOINT,
                regulated=1.0, dysregulated=0.0, dysreg_kind=0.0,
                is_infant=0.0))   # NOT the infant: infant rules must skip this
            self.inner.add_edge_unchecked(
                self.caregiver, "has_affective_state", self.caff)
            chw = self.caregiver_half_width
            self.cgwot = self.s.add_node("WindowOfTolerance", dict(
                name="caregiver_window", lo=-chw, hi=chw, half_width=chw,
                min_half_width=MIN_HALF_WIDTH))
            self.inner.add_edge_unchecked(self.caregiver, "has_window", self.cgwot)
            # PRESENT => the bidirectional coupling exists (attended_by edge).
            self.inner.add_edge_unchecked(self.infant, "attended_by", self.caregiver)

        self.epoch = 0
        self.log = []
        # episode-scoped observations of the graph's decisions (read-only).
        self.caregiver_ever_dysregulated = False
        self.caregiver_peak_arousal = 0.0
        self.inner.run_rules()

    # ---------------------------------------------------------------- helpers
    def _attrs(self, nid):
        return self.s.node(nid)["attrs"]

    def readout(self):
        a = self._attrs(self.iaff)
        w = self._attrs(self.wot)
        r = dict(
            epoch=self.epoch, arousal=a["arousal"],
            dysregulated=a["dysregulated"], dysreg_kind=a["dysreg_kind"],
            in_episode=a["in_episode"],
            lo=w["lo"], hi=w["hi"], half_width=w["half_width"])
        if self.caregiver_present:
            c = self._attrs(self.caff)
            cw = self._attrs(self.cgwot)
            r.update(caregiver_arousal=c["arousal"],
                     caregiver_regulated=c["regulated"],
                     caregiver_dysregulated=c["dysregulated"],
                     caregiver_half_width=cw["half_width"])
        return r

    # ------------------------------------------------------------------- step
    def step(self, *, stress=False):
        """Advance one tick: (optionally) arm the stressor, advance both tick
        clocks, let the GRAPH decide (push / dysreg / bidirectional pulls /
        co-dysregulation / return), read off. NO decision here -- only world
        delivery + read-back of the graph's decisions."""
        self.epoch += 1
        e = float(self.epoch)
        if stress:
            self.s.set_attr(self.stressor, "armed", 1.0)
            self.s.set_attr(self.stressor, "epoch", e)
        self.s.set_attr(self.iaff, "tick_epoch", e)
        if self.caregiver_present:
            self.s.set_attr(self.caff, "tick_epoch", e)
        self.inner.run_rules()
        r = self.readout()
        self.log.append(r)
        if self.caregiver_present:
            # READ (not decide) the co-dysregulation the graph produced.
            if r["caregiver_dysregulated"] == 1.0 or r["caregiver_regulated"] == 0.0:
                self.caregiver_ever_dysregulated = True
            self.caregiver_peak_arousal = max(
                self.caregiver_peak_arousal, r["caregiver_arousal"])
        return r

    # -------------------------------------------------------------- episode
    def run_episode(self, cap=RETURN_CAP):
        """One stress episode: apply the stressor, then advance ticks until the
        infant SETTLES (in_episode back to 0) or the cap is hit. return_ticks =
        ticks from the stress tick to the RETURN TO THE WINDOW (dysregulated back
        to 0). A censored episode (never returns) reports return_ticks == cap."""
        r0 = self.step(stress=True)
        if r0["in_episode"] == 0.0 and r0["dysregulated"] == 0.0:
            return dict(return_ticks=0, settle_ticks=0, dysreg_duration=0,
                        censored=False, no_dysreg=True,
                        caregiver_dysregulated=self.caregiver_ever_dysregulated,
                        caregiver_peak_arousal=self.caregiver_peak_arousal,
                        final=r0)
        dur = 1 if r0["dysregulated"] == 1.0 else 0
        settle_ticks = 0
        return_ticks = None
        r = r0
        while r["in_episode"] == 1.0 and settle_ticks < cap:
            r = self.step(stress=False)
            settle_ticks += 1
            if r["dysregulated"] == 1.0:
                dur += 1
            if return_ticks is None and r["dysregulated"] == 0.0:
                return_ticks = settle_ticks
        censored = (return_ticks is None)
        if censored:
            return_ticks = cap
        return dict(return_ticks=return_ticks, settle_ticks=settle_ticks,
                    dysreg_duration=dur, censored=censored, no_dysreg=False,
                    caregiver_dysregulated=self.caregiver_ever_dysregulated,
                    caregiver_peak_arousal=self.caregiver_peak_arousal, final=r)

    def dysregulates_on_push(self):
        """SINGLE-agent onset probe: apply the stressor for ONE tick and READ
        whether the GRAPH fired a dysregulation onset. The runner bisects the
        stressor magnitude over fresh worlds to find the onset THRESHOLD."""
        r = self.step(stress=True)
        return r["dysregulated"] == 1.0

    # -------------------------------------------------- glass-box / ethics I/O
    def checkpoint(self):
        """Byte-identical serialisation of the WHOLE mind (graph_to_dict)."""
        return self.s.graph_to_dict()
