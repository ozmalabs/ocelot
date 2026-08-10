"""SnapGoalBlockWorld -- a MECHANICAL goal-blocked world (block 242000) for the
FRUSTRATED / ANGRY SNAPPING rung (Ross Greene's explosive child: "kids do well
if they can"). An agent pursues a goal that is repeatedly BLOCKED; each block is
a frustration event. The agent has a REAL AffectiveState.arousal + a
WindowOfTolerance (239000) whose UPPER bound is the snap threshold; a settable
window WIDTH; a trigger stream (goal-block events); optionally an attributable
BLOCKING AGENT (vs an impersonal obstacle); optionally a regulated/absent
caregiver (239000 co-regulation).

ARCHITECTURE RULE COMPLIANCE (experiments/gamma-substrate/CLAUDE.md): this file
is a WORLD ADAPTER. It INGESTS world facts (a goal-block arrives with a
magnitude; a blocker agent is or is not present; a caregiver is or is not
present, regulated or not; the passage of a tick) into the substrate and EMITS
graph state around ``run_rules()``. Every decision -- accumulate the frustration
residual, couple arousal, FIRE THE SNAP at the window's upper bound, DIRECT it by
attribution (anger vs undirected distress), discharge, recover, co-regulate -- is
a graph RULE in ``seeds/snap_frustration.json``, riding the REAL
AffectiveState.arousal + 239000's WindowOfTolerance node and reusing sd_blend's
leaky-EMA form. The adapter's ONLY conditionals are over WORLD state (is this a
block tick? is a blocker present? is a caregiver present?). No graph_rewrite.run
/ _match / _apply / make_rule; no if/else over arousal that decides a snap -- the
snap is READ from the graph. NO reward / punishment anywhere: the snap is a STATE
with a legible cause, never a badness.
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

# ---- FROZEN pre-registered constants (SNAP_PREREG.md) ------------------------
SETPOINT = 0.0
K_ACC = 1.0            # each goal-block integrates its full magnitude (glass-box)
LEAK = 0.02           # sd_blend leak toward 0 (the leaky half of the integrator)
K_CO = 0.60           # 239000 co-regulation pull gain (regulated caregiver)
DISCHARGE = 0.90      # fraction of the residual discharged on a snap
RECOVER_FLOOR = 15.0  # residual below which the snap latch clears (recovered)
TRIGGER_MAG = 10.0    # the small, fixed immediate trigger magnitude
DEFAULT_HALF_WIDTH = 100.0
SNAP_CAP = 30         # max consecutive blocks in a run (censor if never snaps)


class SnapGoalBlockWorld:
    """One AGENT with a REAL AffectiveState.arousal + a WindowOfTolerance band
    whose WIDTH is a settable knob, a GoalBlock trigger source, and optionally an
    attributable Blocker agent and/or a caregiver. The GRAPH decides every snap /
    attribution / discharge / co-regulation; the world only delivers events and
    reads state back.

    blocker_present=True  -> a Blocker Agent + a ``blocked_by`` edge (the block is
                             attributable -> the snap DIRECTS at it: anger).
    blocker_present=False -> an impersonal Obstacle node, NO ``blocked_by`` edge
                             (undirected distress).
    caregiver_present=False -> no caregiver (the agent is ALONE).
    caregiver_regulated     -> the caregiver's ``regulated`` flag (1 co-regulates,
                               0 does not -- a dysregulated caregiver).
    """

    def __init__(self, *, half_width=DEFAULT_HALF_WIDTH, trigger_mag=TRIGGER_MAG,
                 blocker_present=False, caregiver_present=False,
                 caregiver_regulated=1.0, k_acc=K_ACC, leak=LEAK, k_co=K_CO,
                 discharge=DISCHARGE, recover_floor=RECOVER_FLOOR,
                 setpoint=SETPOINT):
        self.half_width = float(half_width)
        self.trigger_mag = float(trigger_mag)
        self.blocker_present = bool(blocker_present)
        self.caregiver_present = bool(caregiver_present)

        self.s = srs.Substrate()
        self.inner = self.s._inner
        self.root = self.s.add_node("Agent", {"role": "snap_root"})
        for seed in ("affective_state_core", "snap_frustration"):
            self.inner.load_seed_manifest(manifest_for(seed), self.root)

        # ---- the AGENT: REAL AffectiveState.arousal + a WindowOfTolerance ----
        self.agent = self.s.add_node("Agent", {"role": "agent"})
        self.aff = self.s.add_node("AffectiveState", dict(
            name="agent_affect", baseline=1.0, valence=0.0, arousal=setpoint,
            resolution=0.0, selection_threshold=0.0, securing=0.0, competence=0.0,
            epoch=-1.0,
            frustration=0.0, setpoint=float(setpoint), k_acc=float(k_acc),
            leak=float(leak), k_co=float(k_co), discharge=float(discharge),
            recover_floor=float(recover_floor),
            snapped=0.0, in_snap=0.0, snap_count=0.0, snap_magnitude=0.0,
            snap_directed=0.0, snap_undirected=0.0, last_trigger_mag=0.0,
            tick_epoch=0.0, leak_epoch=0.0, cr_epoch=0.0))
        self.inner.add_edge_unchecked(self.agent, "has_affective_state", self.aff)

        hw = self.half_width
        self.wot = self.s.add_node("WindowOfTolerance", dict(
            name="agent_window", lo=-hw, hi=hw, half_width=hw, min_half_width=5.0))
        self.inner.add_edge_unchecked(self.agent, "has_window", self.wot)

        # the trigger source: one re-armable GoalBlock (its magnitude = the trigger)
        self.gb = self.s.add_node("GoalBlock", dict(
            name="goal_block", magnitude=self.trigger_mag, armed=0.0))
        self.inner.add_edge_unchecked(self.agent, "has_goal_block", self.gb)

        # ---- the blocker: attributable AGENT vs impersonal OBSTACLE ----
        self.blocker = None
        if self.blocker_present:
            self.blocker = self.s.add_node("Agent", {"role": "blocker"})
            # attributable => the abductive ToM edge the attribution rule reads.
            self.inner.add_edge_unchecked(self.agent, "blocked_by", self.blocker)
        else:
            # an impersonal obstacle: present in the world but NOT an attributable
            # agent (no blocked_by edge) -> the snap stays undirected.
            self.obstacle = self.s.add_node("Obstacle", {"name": "obstacle"})

        # ---- the caregiver: a 239000 co-regulation partner (optional) ----
        self.caregiver = self.caff = None
        if self.caregiver_present:
            self.caregiver = self.s.add_node("Agent", {"role": "caregiver"})
            self.caff = self.s.add_node("AffectiveState", dict(
                name="caregiver_affect", baseline=1.0, valence=0.0, arousal=setpoint,
                epoch=-1.0, frustration=0.0, setpoint=float(setpoint),
                regulated=float(caregiver_regulated)))
            self.inner.add_edge_unchecked(
                self.caregiver, "has_affective_state", self.caff)
            self.inner.add_edge_unchecked(self.agent, "attended_by", self.caregiver)

        self.epoch = 0
        self.log = []
        self.inner.run_rules()

    # ---------------------------------------------------------------- helpers
    def _attrs(self, nid):
        return self.s.node(nid)["attrs"]

    def readout(self):
        a = self._attrs(self.aff)
        w = self._attrs(self.wot)
        return dict(
            epoch=self.epoch, arousal=a["arousal"], frustration=a["frustration"],
            snapped=a["snapped"], in_snap=a["in_snap"], snap_count=a["snap_count"],
            snap_magnitude=a["snap_magnitude"], snap_directed=a["snap_directed"],
            snap_undirected=a["snap_undirected"], last_trigger_mag=a["last_trigger_mag"],
            lo=w["lo"], hi=w["hi"], half_width=w["half_width"])

    # ------------------------------------------------------------------- step
    def step(self, *, block=False):
        """Advance one tick: (optionally) arm a goal-block, advance the tick
        clock, let the GRAPH decide (accumulate / couple / snap / attribute /
        discharge / recover / co-regulate), read off. NO decision here -- only
        world delivery + read-back of the graph's decisions."""
        self.epoch += 1
        e = float(self.epoch)
        if block:
            self.s.set_attr(self.gb, "armed", 1.0)
        self.s.set_attr(self.aff, "tick_epoch", e)
        self.inner.run_rules()
        r = self.readout()
        self.log.append(r)
        return r

    # ----------------------------------------------------- measurement helpers
    def run_until_snap(self, cap=SNAP_CAP):
        """Deliver a goal-block EVERY tick until the GRAPH fires a snap
        (snap_count 0->1) or the cap is hit. blocks_to_snap = the block index at
        the snap; censored (never snaps) -> blocks_to_snap == cap."""
        for i in range(1, cap + 1):
            r = self.step(block=True)
            if r["snap_count"] >= 1.0:
                return dict(blocks_to_snap=i, snapped=True, censored=False,
                            snap_magnitude=r["snap_magnitude"],
                            last_trigger_mag=r["last_trigger_mag"], final=r)
        return dict(blocks_to_snap=cap, snapped=False, censored=True,
                    snap_magnitude=r["snap_magnitude"],
                    last_trigger_mag=r["last_trigger_mag"], final=r)

    def snapped_after_prior_blocks(self, n_prior):
        """DISPROPORTION TEETH probe: deliver n_prior IDENTICAL goal-blocks (build
        the accumulated residual), verify NO snap occurred during the build, then
        deliver ONE MORE identical block (the trigger) and READ whether THAT block
        fired a snap. The trigger magnitude is the SAME in every arm -- only the
        prior residual differs. Returns the graph's verdict, never a decision."""
        for _ in range(n_prior):
            self.step(block=True)
        pre = self.readout()["snap_count"]
        r = self.step(block=True)                 # the identical trigger block
        fired = r["snap_count"] > pre
        return dict(snapped_on_trigger=int(fired), prior_snaps=int(pre),
                    residual_before_trigger=self.log[-2]["frustration"] if len(self.log) >= 2 else 0.0,
                    snap_magnitude=r["snap_magnitude"],
                    last_trigger_mag=r["last_trigger_mag"], final=r)

    def arousal_trajectory(self):
        """The arousal value at each logged tick -- for the gradual-build vs
        abrupt-output contrast (arousal ramps continuously; snap_count steps)."""
        return [(row["epoch"], row["arousal"], row["snap_count"]) for row in self.log]

    def directed_at_edges(self):
        """The attribution TARGET(s): directed_at edges the graph minted."""
        blob = self.s.graph_to_dict()
        return [(e["src"], e["tgt"]) for e in blob["edges"]
                if e["type"] == "directed_at"]

    # -------------------------------------------------- glass-box / ethics I/O
    def checkpoint(self):
        """Byte-identical serialisation of the WHOLE mind (graph_to_dict)."""
        return self.s.graph_to_dict()
