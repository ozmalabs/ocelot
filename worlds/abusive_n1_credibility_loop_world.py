"""AbusiveN1CredibilityLoopWorld -- a MECHANICAL abuser/victim/network world
for the ABUSIVE-DYNAMICS N1 rung (block 298000, "the two-faced abuser + the
credibility-asymmetry loop" -- ABUSIVE_RELATIONSHIPS_NETWORK.md Part E, N1;
the NETWORK dimension's headline rung).

Composes TWO already-built substrates, unmodified:
  * the dyad line's abuser (`seeds/snap_frustration.json`, block 242000) +
    victim (`seeds/arousal_window_coreg.json`, block 239000) -- BYTE-IDENTICAL
    to R2's/R3's own single-anchor dyad (`worlds/abusive_r3_coercive_control_
    world.py`), restated here self-contained per this line's own convention
    (R3 restated R2's rule rather than depending on it).
  * the 234000 `stated!=held` readable-deception atom pointed at a SECOND
    audience (the network), in the exact shape `bigville_drama_social.json`'s
    `bd_john_public_face` (block 245000) already established, PLUS the
    multi-node reputation belief-update surface that same seed's
    `bd_villager_backs` already established (OPEN QUESTION #1 of
    ABUSIVE_RELATIONSHIPS_NETWORK.md: confirmed YES, already materialised, at
    block 245000 -- N1 reuses the RULE SHAPE, self-contained, never depending
    on that sibling demo's seed file).

THREE ARMS (ABUSIVE_N1_CREDIBILITY_LOOP_PREREG.md):
  * BASELINE            -- victim attended_by the abuser (dysregulates); every
                            network node reads only the abuser's STATED face.
                            THE LOOP: predicted to entrap (belief-gap widens
                            favouring the abuser as the victim's presentation
                            grows unstable).
  * PRIVATE_FACE_CONTROL -- IDENTICAL victim dyad (same dysregulation), but
                            ONE network node (`observes_private=1`) has a
                            DIRECT edge to the abuser's HELD state
                            (`observes_held`) instead of its stated face.
                            FAILABLE: that node's belief-gap must NOT favour
                            the abuser.
  * NON_DYSREGULATED_CONTROL -- the victim is simply NOT `attended_by` the
                            abuser (a mechanical world-adapter topology
                            choice, no new rule): the victim never
                            dysregulates and presents coherently throughout.
                            Every network node reads the stated face, exactly
                            as baseline. FAILABLE: belief-gap must NOT favour
                            the abuser despite the abuser's identical charm
                            broadcast.

The abuser's own tension-driven snap dynamics (the "held-intent-toward-the-
victim = harm/control", B1 of ABUSIVE_RELATIONSHIPS_NETWORK.md) are IDENTICAL
across all three arms -- same GoalBlock tension trickle, same seed per
trajectory index -- so the ONLY manipulated variable per comparison is (a)
whether the victim is coupled to the abuser (BASELINE/PRIVATE_FACE_CONTROL vs
NON_DYSREGULATED_CONTROL) or (b) whether one network node's observation edge
reaches the held state instead of the stated face (PRIVATE_FACE_CONTROL vs
BASELINE).

ARCHITECTURE RULE COMPLIANCE (CLAUDE.md): this file is a WORLD ADAPTER. Every
decision -- frustration accumulation, the snap threshold, discharge, recovery,
the victim's entrainment, the abuser's stated-face gap, and the network's
credibility belief-update (cred_abuser/cred_victim/belief_gap) -- is the
graph's decision, entirely inside `seeds/snap_frustration.json` /
`seeds/arousal_window_coreg.json` (both UNMODIFIED) and this rung's four new
rules in `seeds/abusive_n1_credibility_loop.json`. The adapter's only
"conditionals" are (i) WHICH ARM to build (an experimental-arm selection made
ONCE per trajectory, exactly as every prior rung in this line) and (ii)
mechanically DELIVERING each tick's observed graph facts (the abuser's
stated_charm / frustration-vs-recover_floor, the victim's dysregulated
flag) onto each network node's observation-COUNT attrs -- a per-tick
tally, never a judgement about
what a node should BELIEVE (that is the two credibility rules' job, entirely).
NO reward/punishment anywhere: the tension trickle is a world-delivered fact
(mechanically identical to a goal-block magnitude in 239000/242000/289000),
never a scored choice.
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

# ---- FROZEN world constants (pre-registered, ABUSIVE_N1_CREDIBILITY_LOOP_PREREG.md)
SETPOINT = 0.0

# abuser (snap_frustration, block 242000 defaults -- BYTE-IDENTICAL to R2's/
# R3's own frozen constants, since N1 reuses the exact same abuser mechanism).
ABUSER_HALF_WIDTH = 100.0
K_ACC = 1.0
LEAK = 0.02
DISCHARGE = 0.90
RECOVER_FLOOR = 25.0

# victim (arousal_window_coreg, block 239000 defaults -- same convention)
VICTIM_HALF_WIDTH = 10.0
K_SELF = 0.15
K_CO = 0.35

TRICKLE_MAG = 5.0
TRICKLE_JITTER_FRAC = 0.10

# network -- N1-specific, pilot-informed (see PREREG Sec. 3)
N_NETWORK_NODES = 5
CHARM_WEIGHT = 1.0
CLAIM_WEIGHT = 1.0
INSTABILITY_DISCOUNT_WEIGHT = 3.0
HARM_DISCOUNT_WEIGHT = 3.0


class AbusiveN1CredibilityLoopWorld:
    """One ABUSER Agent (snap_frustration, unmodified, byte-identical to
    R2's/R3's own), one VICTIM Agent (arousal_window_coreg, unmodified, plus
    this rung's own frustration-routed entrainment), and a Network of
    NetworkNode agents whose reputation belief about both parties is
    entirely graph-rule-computed. NO decision here -- only world delivery +
    mechanical per-tick observation-count bookkeeping + read-back."""

    def __init__(self, *, dysregulated_victim=True, private_face_node=False,
                 n_network_nodes=N_NETWORK_NODES,
                 abuser_half_width=ABUSER_HALF_WIDTH,
                 victim_half_width=VICTIM_HALF_WIDTH,
                 leak=LEAK, k_acc=K_ACC, discharge=DISCHARGE,
                 recover_floor=RECOVER_FLOOR, k_self=K_SELF, k_co=K_CO,
                 trickle_mag=TRICKLE_MAG,
                 charm_weight=CHARM_WEIGHT, claim_weight=CLAIM_WEIGHT,
                 instability_discount_weight=INSTABILITY_DISCOUNT_WEIGHT,
                 harm_discount_weight=HARM_DISCOUNT_WEIGHT):
        self.trickle_mag = float(trickle_mag)
        self.dysregulated_victim = bool(dysregulated_victim)
        self.private_face_node = bool(private_face_node)
        self.n_network_nodes = int(n_network_nodes)

        self.s = srs.Substrate()
        self.inner = self.s._inner
        self.root = self.s.add_node("Agent", {"role": "n1_root"})
        for seed in ("affective_state_core", "snap_frustration", "arousal_window_coreg",
                     "abusive_n1_credibility_loop"):
            self.inner.load_seed_manifest(manifest_for(seed), self.root)

        # ---------------------------------------------------------- ABUSER
        # snap_frustration's full contract, plus is_abuser=1.0 (read by
        # n1_victim_entrainment), deception_on=1.0 (n1_abuser_stated_charm,
        # fixed ON in every arm -- the arms manipulate the NETWORK's/VICTIM's
        # side, never the abuser's own deception, matching R1-R3's own
        # "identical driver, only structure/topology differs" discipline).
        self.abuser = self.s.add_node("Agent", {"role": "abuser"})
        self.aaff = self.s.add_node("AffectiveState", dict(
            name="abuser_affect", baseline=1.0, valence=0.0, arousal=SETPOINT,
            resolution=0.0, selection_threshold=0.0, securing=0.0,
            competence=0.0, epoch=-1.0, is_abuser=1.0,
            frustration=0.0, setpoint=float(SETPOINT), k_acc=float(k_acc),
            leak=float(leak), discharge=float(discharge),
            recover_floor=float(recover_floor),
            snapped=0.0, in_snap=0.0, snap_count=0.0, snap_magnitude=0.0,
            snap_directed=0.0, snap_undirected=0.0, last_trigger_mag=0.0,
            tick_epoch=0.0, leak_epoch=0.0,
            deception_on=1.0, stated_charm=0.0))
        self.inner.add_edge_unchecked(self.abuser, "has_affective_state", self.aaff)

        hw_a = float(abuser_half_width)
        self.awot = self.s.add_node("WindowOfTolerance", dict(
            name="abuser_window", lo=-hw_a, hi=hw_a, half_width=hw_a))
        self.inner.add_edge_unchecked(self.abuser, "has_window", self.awot)

        self.gb = self.s.add_node("GoalBlock", dict(
            name="tension_trigger", magnitude=0.0, armed=0.0))
        self.inner.add_edge_unchecked(self.abuser, "has_goal_block", self.gb)

        # ---------------------------------------------------------- VICTIM
        # arousal_window_coreg's full contract; deliberately carries NO
        # snap_frustration-specific key (matching R2/R3's own omission list,
        # so `snap_arousal_track` never accidentally matches the victim).
        self.victim = self.s.add_node("Agent", {"role": "victim"})
        self.vaff = self.s.add_node("AffectiveState", dict(
            name="victim_affect", baseline=1.0, valence=0.0, arousal=SETPOINT,
            resolution=0.0, selection_threshold=0.0, securing=0.0,
            competence=0.0, epoch=-1.0,
            tick_epoch=0.0, sr_epoch=0.0, pcr_epoch=0.0,
            k_self=float(k_self), k_co=float(k_co), setpoint=float(SETPOINT),
            dysregulated=0.0, dysreg_kind=0.0, in_episode=0.0, got_coreg=0.0))
        self.inner.add_edge_unchecked(self.victim, "has_affective_state", self.vaff)

        hw_v = float(victim_half_width)
        self.vwot = self.s.add_node("WindowOfTolerance", dict(
            name="victim_window", lo=-hw_v, hi=hw_v, half_width=hw_v,
            widen_delta=2.0, narrow_delta=2.0, min_half_width=5.0,
            safety_prior=0.5, safety_step=0.03, widen_count=0.0, narrow_count=0.0))
        self.inner.add_edge_unchecked(self.victim, "has_window", self.vwot)

        if self.dysregulated_victim:
            self.inner.add_edge_unchecked(self.victim, "attended_by", self.abuser)

        # --------------------------------------------------------- NETWORK
        # A Network hub + N NetworkNode members. Every member reads the
        # abuser's STATED face (observes_stated) and the victim's
        # presentation (observes_victim); in the PRIVATE_FACE_CONTROL arm,
        # exactly ONE member (the "insider") ALSO carries observes_held
        # instead -- a DIRECT structural edge to the abuser's held state --
        # and observes_private=1.0 selects the private-reading credibility
        # rule for that node only (n1_network_credibility_private).
        self.network = self.s.add_node("Network", {"name": "network"})
        self.nodes = []
        for i in range(self.n_network_nodes):
            is_insider = self.private_face_node and (i == 0)
            nn = self.s.add_node("NetworkNode", dict(
                name=f"node_{i}",
                observes_private=(1.0 if is_insider else 0.0),
                charm_weight=float(charm_weight), claim_weight=float(claim_weight),
                instability_discount_weight=float(instability_discount_weight),
                harm_discount_weight=float(harm_discount_weight),
                seen_charm=0.0, seen_harm_direct=0.0,
                seen_victim_claim=0.0, seen_victim_unstable=0.0,
                cred_abuser=0.0, cred_victim=0.0, belief_gap=0.0))
            self.inner.add_edge_unchecked(self.network, "has_member", nn)
            if is_insider:
                self.inner.add_edge_unchecked(nn, "observes_held", self.abuser)
            else:
                self.inner.add_edge_unchecked(nn, "observes_stated", self.abuser)
            self.inner.add_edge_unchecked(nn, "observes_victim", self.victim)
            self.nodes.append(nn)

        self.epoch = 0
        self.log = []
        self.inner.run_rules()

    # ---------------------------------------------------------------- helpers
    def _attrs(self, nid):
        return self.s.node(nid)["attrs"]

    def readout(self):
        aa = self._attrs(self.aaff)
        va = self._attrs(self.vaff)
        vw = self._attrs(self.vwot)
        nn_rows = [self._attrs(nn) for nn in self.nodes]
        row = dict(
            epoch=self.epoch,
            abuser_arousal=aa["arousal"], abuser_frustration=aa["frustration"],
            abuser_in_snap=aa["in_snap"], abuser_snapped=aa["snapped"],
            abuser_snap_count=aa["snap_count"], abuser_stated_charm=aa["stated_charm"],
            victim_arousal=va["arousal"], victim_dysregulated=va["dysregulated"],
            victim_in_episode=va["in_episode"],
            victim_half_width=vw["half_width"],
            belief_gap_mean=(sum(r["belief_gap"] for r in nn_rows) / len(nn_rows)),
            cred_abuser_mean=(sum(r["cred_abuser"] for r in nn_rows) / len(nn_rows)),
            cred_victim_mean=(sum(r["cred_victim"] for r in nn_rows) / len(nn_rows)))
        if self.private_face_node:
            row["insider_belief_gap"] = nn_rows[0]["belief_gap"]
            row["insider_cred_abuser"] = nn_rows[0]["cred_abuser"]
            outsiders = nn_rows[1:]
            row["outsider_belief_gap_mean"] = (sum(r["belief_gap"] for r in outsiders) / len(outsiders))
        return row

    # ------------------------------------------------------------------- step
    def step(self, *, tension=False, jitter=0.0):
        """Advance one tick: (optionally) arm the abuser's tension trickle,
        let the GRAPH decide the dyad + the abuser's stated face
        (run_rules), MECHANICALLY deliver each node's per-tick observation
        counts (a world fact, never a judgement), let the GRAPH decide each
        node's credibility belief (run_rules again), read off."""
        self.epoch += 1
        e = float(self.epoch)
        if tension:
            self.s.set_attr(self.gb, "magnitude", float(self.trickle_mag + jitter))
            self.s.set_attr(self.gb, "armed", 1.0)
        self.s.set_attr(self.aaff, "tick_epoch", e)
        self.s.set_attr(self.vaff, "tick_epoch", e)
        self.inner.run_rules()

        # ---- mechanical per-tick observation bookkeeping (world fact -> attr)
        stated_charm = self._attrs(self.aaff)["stated_charm"]
        # held-harm THIS TICK: `frustration > recover_floor` -- snap_frustration's
        # OWN, unmodified threshold for "still genuinely elevated" (the exact
        # condition its own `snap_recover` rule uses to decide the incident has
        # NOT yet resolved). Reused as the "held harm is live" observable
        # rather than `in_snap`/`snapped`, which were found (empirically, not
        # assumed) to be transient WITHIN one run_rules() fixpoint pass at
        # these frozen constants -- snap_discharge's same-pass reduction
        # already drops frustration below recover_floor before a post-fixpoint
        # read can see `in_snap==1`. `frustration` itself is a persistent
        # value with no such reset, and `recover_floor` is an EXISTING,
        # semantically-meaningful threshold (not a new magic number).
        held_harm = 1.0 if self._attrs(self.aaff)["frustration"] > self._attrs(self.aaff)["recover_floor"] else 0.0
        victim_unstable = self._attrs(self.vaff)["dysregulated"]
        for nn in self.nodes:
            a = self._attrs(nn)
            if a["observes_private"] == 1.0:
                self.s.set_attr(nn, "seen_harm_direct", a["seen_harm_direct"] + held_harm)
            else:
                self.s.set_attr(nn, "seen_charm", a["seen_charm"] + stated_charm)
            self.s.set_attr(nn, "seen_victim_claim", a["seen_victim_claim"] + 1.0)
            self.s.set_attr(nn, "seen_victim_unstable", a["seen_victim_unstable"] + victim_unstable)
        self.inner.run_rules()

        r = self.readout()
        self.log.append(r)
        return r

    def run_trajectory(self, T, *, rng=None):
        """Deliver T ticks of the constant, jittered tension trickle -- the
        SAME abuser-side driver in EVERY arm (only whether the victim is
        coupled, or which node observes what, differs)."""
        for _ in range(T):
            jitter = 0.0
            if rng is not None:
                jitter = float(rng.normal(0.0, self.trickle_mag * TRICKLE_JITTER_FRAC))
            self.step(tension=True, jitter=jitter)
        return self.log

    # -------------------------------------------------- glass-box / ethics I/O
    def checkpoint(self):
        """Byte-identical serialisation of the WHOLE mind (graph_to_dict)."""
        return self.s.graph_to_dict()
