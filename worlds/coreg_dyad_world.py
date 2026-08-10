"""CoregDyadWorld -- a MECHANICAL infant/caregiver dyad world (block 239000)
for the AROUSAL / WINDOW-OF-TOLERANCE rung with CO-REGULATION.

ARCHITECTURE RULE COMPLIANCE (experiments/gamma-substrate/CLAUDE.md):
this file is a WORLD ADAPTER. It INGESTS world facts (a stressor arrives; the
caregiver is present/absent and regulated/dysregulated; the passage of a tick)
into the substrate and EMITS graph state around ``run_rules()``. It contains NO
agent decision:

  * WHETHER the infant is dysregulated, WHETHER co-regulation pulls it back,
    and WHETHER the window widens or narrows are ALL graph rules
    (seeds/arousal_window_coreg.json), riding the REAL emotion framework's
    AffectiveState.arousal (seeds/affective_state_core.json). The adapter only
    READS the arousal / window / dysregulated attributes back out.
  * the adapter's only conditionals are over WORLD state (is this a stress
    tick? is the caregiver present? is it regulated?) -- mechanical delivery,
    exactly as HarlowWorld (block 233000) applies a mother's provision.

No graph_rewrite.run / _match / _apply / make_rule; no if/else over the
infant's arousal that decides regulation. Regulation is READ from the graph.
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

# ---- FIXED world constants (pre-registered, AROUSAL_WOT_PREREG.md) ----------
SETPOINT = 0.0            # homeostatic arousal baseline (window centred here)
K_SELF = 0.15            # self-regulation leak gain (alone)
K_CO = 0.50             # co-regulation coupling gain (present caregiver)
CG_REGULATED_AROUSAL = 0.0     # a regulated caregiver sits at setpoint
CG_DYSREGULATED_AROUSAL = 120.0  # a dysregulated caregiver sits high (contagion)
WIDEN_DELTA = 2.0        # window half-width grown per supported episode
NARROW_DELTA = 2.0       # window half-width shrunk per unsupported episode
MIN_HALF_WIDTH = 5.0     # traumatised floor (small window, never negative)
SAFETY_STEP = 0.03       # safety-prior step per episode
SAFETY_PRIOR0 = 0.5      # neutral safety prior at birth
RETURN_CAP = 40          # ticks: censor an episode that never returns


class CoregDyadWorld:
    """One INFANT agent (real AffectiveState.arousal + a WindowOfTolerance band)
    and one CAREGIVER agent (present/absent, regulated/dysregulated). A stressor
    stream pushes the infant's arousal; the graph decides dysregulation,
    co-regulation, and window plasticity.

    caregiver_present=False  -> no attended_by edge (the infant is ALONE:
                                self-regulation only -- the failable control).
    regulated_caregiver=False -> the caregiver's own arousal is HIGH; the coupling
                                pulls the infant the WRONG way (the second failable
                                control).
    """

    def __init__(self, *, half_width0=30.0, stress_mag=100.0,
                 caregiver_present=True, regulated_caregiver=True,
                 k_self=K_SELF, k_co=K_CO):
        self.half_width0 = float(half_width0)
        self.stress_mag = float(stress_mag)
        self.caregiver_present = bool(caregiver_present)
        self.regulated_caregiver = bool(regulated_caregiver)

        self.s = srs.Substrate()
        self.inner = self.s._inner
        # a throwaway agent_root for the seed's neutral AffectiveState (unused);
        # the infant's working AffectiveState is created explicitly below.
        self.root = self.s.add_node("Agent", {"role": "dyad_root"})
        for seed in ("affective_state_core", "arousal_window_coreg"):
            self.inner.load_seed_manifest(manifest_for(seed), self.root)

        # ---- the INFANT: real AffectiveState.arousal + the window band ----
        self.infant = self.s.add_node("Agent", {"role": "infant"})
        self.iaff = self.s.add_node("AffectiveState", dict(
            name="infant_affect", baseline=1.0, valence=0.0, arousal=SETPOINT,
            resolution=0.0, selection_threshold=0.0, securing=0.0,
            competence=0.0, epoch=-1.0,
            # regulation control state (read/written by the rules)
            tick_epoch=0.0, sr_epoch=0.0, cr_epoch=0.0,
            k_self=float(k_self), k_co=float(k_co), setpoint=SETPOINT,
            dysregulated=0.0, dysreg_kind=0.0, in_episode=0.0, got_coreg=0.0))
        self.inner.add_edge_unchecked(self.infant, "has_affective_state", self.iaff)

        self.wot = self.s.add_node("WindowOfTolerance", dict(
            name="infant_window",
            lo=-self.half_width0, hi=self.half_width0, half_width=self.half_width0,
            widen_delta=WIDEN_DELTA, narrow_delta=NARROW_DELTA,
            min_half_width=MIN_HALF_WIDTH, safety_prior=SAFETY_PRIOR0,
            safety_step=SAFETY_STEP, widen_count=0.0, narrow_count=0.0))
        self.inner.add_edge_unchecked(self.infant, "has_window", self.wot)

        # a single reusable Stressor node (armed per stress tick -- glass-box)
        self.stressor = self.s.add_node("Stressor", dict(
            name="stressor", magnitude=self.stress_mag, armed=0.0, epoch=0.0))
        self.inner.add_edge_unchecked(self.infant, "has_stressor", self.stressor)

        # ---- the CAREGIVER: its own real AffectiveState.arousal ----
        cg_arousal = (CG_REGULATED_AROUSAL if self.regulated_caregiver
                      else CG_DYSREGULATED_AROUSAL)
        self.caregiver = self.s.add_node("Agent", {"role": "caregiver"})
        self.caff = self.s.add_node("AffectiveState", dict(
            name="caregiver_affect", baseline=1.0, valence=0.0, arousal=cg_arousal,
            resolution=0.0, selection_threshold=0.0, securing=0.0,
            competence=0.0, epoch=-1.0,
            regulated=(1.0 if self.regulated_caregiver else 0.0)))
        self.inner.add_edge_unchecked(self.caregiver, "has_affective_state", self.caff)
        # the caregiver's regulated flag also lives on the caregiver AGENT node,
        # because R6 (mark_coreg_support) reads it off the attended_by target.
        self.s.set_attr(self.caregiver, "regulated",
                        1.0 if self.regulated_caregiver else 0.0)

        # PRESENT => the co_regulation coupling exists (attended_by edge).
        if self.caregiver_present:
            self.inner.add_edge_unchecked(self.infant, "attended_by", self.caregiver)

        self.epoch = 0
        self.log = []
        self.inner.run_rules()

    # ---------------------------------------------------------------- helpers
    def _attrs(self, nid):
        return self.s.node(nid)["attrs"]

    def readout(self):
        a = self._attrs(self.iaff)
        w = self._attrs(self.wot)
        return dict(
            epoch=self.epoch, arousal=a["arousal"],
            dysregulated=a["dysregulated"], dysreg_kind=a["dysreg_kind"],
            in_episode=a["in_episode"], got_coreg=a["got_coreg"],
            lo=w["lo"], hi=w["hi"], half_width=w["half_width"],
            safety_prior=w["safety_prior"],
            widen_count=w["widen_count"], narrow_count=w["narrow_count"],
            caregiver_arousal=self._attrs(self.caff)["arousal"])

    # ------------------------------------------------------------------- step
    def step(self, *, stress=False):
        """Advance one tick: (optionally) arm the stressor, advance the tick
        clock, let the graph decide (push / dysreg / co-regulate / self-regulate
        / widen / narrow), read off. NO decision here -- only world delivery."""
        self.epoch += 1
        e = float(self.epoch)
        # INGEST: arm the stressor for this tick (a world event) + advance clock.
        if stress:
            self.s.set_attr(self.stressor, "armed", 1.0)
            self.s.set_attr(self.stressor, "epoch", e)
        self.s.set_attr(self.iaff, "tick_epoch", e)
        # TICK: the graph decides in-rule.
        self.inner.run_rules()
        r = self.readout()
        self.log.append(r)
        return r

    # -------------------------------------------------------------- episode
    def run_episode(self, cap=RETURN_CAP):
        """One stress episode: apply the stressor, then advance ticks until the
        infant SETTLES (in_episode back to 0) or the cap is hit.

        The HEADLINE metric is return_ticks: ticks from the stress tick to the
        RETURN TO THE WINDOW (dysregulated back to 0 -- fight/flight/freeze
        subsides). The episode stays open a little longer while arousal settles
        to setpoint, where the window's plasticity (widen/narrow) is applied
        once. A censored episode (never returns) reports return_ticks == cap."""
        r0 = self.step(stress=True)               # tick with the stressor
        # if the push never dysregulated (window already wider than the push),
        # the episode is a no-op: no plasticity fired.
        if r0["in_episode"] == 0.0 and r0["dysregulated"] == 0.0:
            return dict(return_ticks=0, settle_ticks=0, dysreg_duration=0,
                        censored=False, no_dysreg=True, final=r0)
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
                return_ticks = settle_ticks       # first tick back in the window
        censored = (return_ticks is None)
        if censored:
            return_ticks = cap
        return dict(return_ticks=return_ticks, settle_ticks=settle_ticks,
                    dysreg_duration=dur, censored=censored, no_dysreg=False,
                    final=r)

    # -------------------------------------------------- glass-box / ethics I/O
    def checkpoint(self):
        """Byte-identical serialisation of the WHOLE mind (graph_to_dict)."""
        return self.s.graph_to_dict()
