"""AbusiveN3BeliefPropagationWorld -- a MECHANICAL abuser/victim/peer-network
world for the ABUSIVE-DYNAMICS N3 rung (block 304000, "belief propagation of
the abuser's lies" -- ABUSIVE_RELATIONSHIPS_NETWORK.md Part E, N3; Part B4).

Composes TWO already-built substrates, unmodified:
  * N1's credibility-asymmetry loop (`seeds/abusive_n1_credibility_loop.json`,
    block 298000) -- the abuser/victim dyad (itself riding
    `snap_frustration`/`arousal_window_coreg`, both UNMODIFIED) AND the
    per-NetworkNode `belief_gap` credibility read-off. N3 depends on this
    seed DIRECTLY and reuses its rules VERBATIM -- no credibility dynamics
    are reimplemented here.
  * `seeds/abusive_n3_belief_propagation.json` (this rung's own ONE new
    rule) -- `n3_peer_belief_update`, the neighbour-to-neighbour propagation
    N1's own "Honest residuals" names as explicitly out of its scope ("five
    INDEPENDENT observers...no neighbour-to-neighbour update").

TOPOLOGY (ABUSIVE_N3_BELIEF_PROPAGATION_PREREG.md Sec. 2) -- 8 NetworkNode
agents, TWO kinds:
  * DIRECT observers (`d1`, `d2`) -- observe the abuser's stated face
    directly (N1's own `observes_stated`, `observes_private=0.0`), exactly
    like N1's own "outsider" nodes. Pure corruption SOURCES: they carry NO
    outgoing `peer_of` edge, so `n3_peer_belief_update` never matches them --
    their belief is governed ENTIRELY by N1's own `n1_network_credibility_
    stated` rule.
  * INDIRECT nodes (`i1`..`i6`) -- carry `observes_private=2.0`, a SENTINEL
    value N1's own two credibility rules never match (`Eq(observes_private,
    0.0)` / `Eq(observes_private, 1.0)` both fail for `2.0`), so N1's rules
    skip them entirely and their `belief_gap` is governed SOLELY by
    `n3_peer_belief_update`'s neighbour-mean pull. They have NO direct
    observation edge to the abuser -- the genuinely new population this rung
    adds. Wired as (`nn -> pp` meaning "nn pulls toward pp's belief"):
      i1 -> d1                     (1 hop from the abuser via d1)
      i2 -> i1                     (2 hops)              -- ANCHOR POSITION
      i3 -> i2                     (3 hops, i2's downstream neighbour #1)
      i4 -> i2                     (3 hops, i2's downstream neighbour #2)
      i5 -> i1, i5 -> i2           (2 hops via EITHER path, both tracing
                                     back to d1 -- the PLURALISTIC-IGNORANCE
                                     probe: i5 double-counts d1's corruption
                                     through two correlated, not independent,
                                     routes)
      i6 -> d2                     (1 hop from the abuser via d2, on a
                                     SEPARATE branch entirely disjoint from
                                     i2's subtree -- the FAR/insulated
                                     discipline check: the anchor at i2
                                     should have NO effect on i6)

TWO ARMS (ABUSIVE_N3_BELIEF_PROPAGATION_PREREG.md Sec. 2.4):
  * NO_ANCHOR  -- i2 is a plain indirect node (`observes_private=2.0`, no
                  observation edge to the abuser at all). Corrupted belief
                  should propagate unimpeded down i2's whole subtree
                  (i3, i4, i5).
  * ANCHOR     -- IDENTICAL topology (the SAME `peer_of` edges, including
                  i2's own outgoing `peer_of -> i1`), except i2 ADDITIONALLY
                  carries `observes_held -> abuser`, `observes_victim ->
                  victim`, and `observes_private=1.0` -- reusing N1's OWN
                  `n1_network_credibility_private` rule, UNMODIFIED, to pin
                  i2's belief every tick to the uncorrupted, victim-favouring
                  formula. Rule ORDER (`n3_peer_belief_update`=35 < N1's
                  credibility rules=40) means i2's own peer pull fires first
                  and is then OVERWRITTEN, in the SAME `run_rules()` pass, by
                  the pinned private-face computation -- i2 never drifts, but
                  its downstream readers (i3, i4, i5) DO read its (now
                  pinned) belief_gap. **FAILABLE:** i3/i4's belief-gap must
                  be LESS corrupted (CI-separated toward the victim) than in
                  the NO_ANCHOR arm; i6 (topologically disjoint from i2)
                  must NOT differ between arms (the anchor's effect is
                  LOCAL, not a network-wide fix).

ARCHITECTURE RULE COMPLIANCE (CLAUDE.md): this file is a WORLD ADAPTER.
Every decision -- the dyad dynamics, the abuser's stated face, each node's
credibility belief (direct OR peer-propagated), WHICH nodes a node's belief
moves toward -- is the graph's decision, entirely inside the (unmodified)
`abusive_n1_credibility_loop` seed and this rung's one new rule in
`abusive_n3_belief_propagation.json`. The adapter's only "conditionals" are
(i) WHICH ARM to build (an experimental-arm selection made ONCE per
trajectory, exactly as every prior rung in this line) and (ii) mechanically
DELIVERING each tick's observed graph facts onto each node's observation-
count attrs (reused VERBATIM from N1's/N2's own `step()` -- applied
UNCONDITIONALLY to all 8 nodes; N1's own rules simply never match a node
whose `observes_private` sentinel is `2.0`, so the incremented counts on an
indirect node are inert, unused data, never a judgement) and the tick
counter every node's peer-update rule reads (`tick_epoch`, mechanically
incremented, exactly like N1's/N2's own tick counters). The `peer_of`
topology (WHICH node reads FROM which) is assigned ONCE at construction --
mechanical per-node wiring identical in kind to N1's own `observes_private =
1.0 if i==0 else 0.0` -- never a live decision responding to graph state.
NO reward/punishment anywhere.
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

# ---- FROZEN world constants (pre-registered, ABUSIVE_N3_BELIEF_PROPAGATION_PREREG.md)
SETPOINT = 0.0

# abuser (snap_frustration, block 242000 defaults) -- BYTE-IDENTICAL to
# N1's/N2's own frozen constants; N3 reuses N1's exact dyad mechanism.
ABUSER_HALF_WIDTH = 100.0
K_ACC = 1.0
LEAK = 0.02
DISCHARGE = 0.90
RECOVER_FLOOR = 25.0

# victim (arousal_window_coreg, block 239000 defaults) -- same convention
VICTIM_HALF_WIDTH = 10.0
K_SELF = 0.15
K_CO = 0.35

TRICKLE_MAG = 5.0
TRICKLE_JITTER_FRAC = 0.10

# credibility loop (N1 defaults, reused verbatim -- N3 does not re-sweep
# these; a direct-observer's own belief_gap trajectory here is IDENTICAL to
# N1's own measured BASELINE trend, PREREG Sec. 3)
CHARM_WEIGHT = 1.0
CLAIM_WEIGHT = 1.0
INSTABILITY_DISCOUNT_WEIGHT = 3.0
HARM_DISCOUNT_WEIGHT = 3.0

# N3-specific, pilot-informed (PREREG Sec. 3)
PEER_PULL_RATE = 0.05

# The sentinel `observes_private` value for a node with NO direct observation
# channel to the abuser at all -- N1's OWN two credibility rules require
# `observes_private == 0.0` (stated-face) or `== 1.0` (held-face/private);
# any OTHER value is matched by NEITHER rule, so N1's credibility machinery
# skips the node entirely and `n3_peer_belief_update` is the only rule that
# ever touches its `belief_gap`. Disclosed, not a magic number: this reuses
# N1's own discriminator attr, extended with a third value.
NO_DIRECT_OBSERVATION = 2.0


class AbusiveN3BeliefPropagationWorld:
    """One ABUSER Agent + one VICTIM Agent (N1's dyad, unmodified) and a
    Network of 8 NetworkNode agents -- two DIRECT observers (pure corruption
    sources) and six INDIRECT, peer-only nodes wired into a propagation
    chain/branch (Sec. above). NO decision here -- only world delivery +
    mechanical per-tick bookkeeping + read-back."""

    def __init__(self, *, anchor=False,
                 abuser_half_width=ABUSER_HALF_WIDTH,
                 victim_half_width=VICTIM_HALF_WIDTH,
                 leak=LEAK, k_acc=K_ACC, discharge=DISCHARGE,
                 recover_floor=RECOVER_FLOOR, k_self=K_SELF, k_co=K_CO,
                 trickle_mag=TRICKLE_MAG,
                 charm_weight=CHARM_WEIGHT, claim_weight=CLAIM_WEIGHT,
                 instability_discount_weight=INSTABILITY_DISCOUNT_WEIGHT,
                 harm_discount_weight=HARM_DISCOUNT_WEIGHT,
                 peer_pull_rate=PEER_PULL_RATE):
        self.trickle_mag = float(trickle_mag)
        self.anchor = bool(anchor)
        self.peer_pull_rate = float(peer_pull_rate)

        self.s = srs.Substrate()
        self.inner = self.s._inner
        self.root = self.s.add_node("Agent", {"role": "n3_root"})
        for seed in ("affective_state_core", "snap_frustration", "arousal_window_coreg",
                     "abusive_n1_credibility_loop", "abusive_n3_belief_propagation"):
            self.inner.load_seed_manifest(manifest_for(seed), self.root)

        # ---------------------------------------------------------- ABUSER
        # N1's own contract, byte-identical (is_abuser=1.0, deception_on=1.0
        # fixed ON in every arm -- the arms manipulate the network's belief-
        # propagation topology only, never the abuser's own deception).
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
        # The victim is ALWAYS coupled (attended_by the abuser) in every arm
        # of this rung -- N1 already established (and gates) that an
        # uncoupled victim produces belief_gap==0.0 identically, so a
        # propagation rung with nothing corrupted to propagate would be
        # vacuous; N3's OWN manipulated variable is the anchor, not the
        # dyad coupling (matching PRIVATE_FACE_CONTROL's own "single
        # manipulated variable" discipline).
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

        self.inner.add_edge_unchecked(self.victim, "attended_by", self.abuser)

        # ------------------------------------------------------- NETWORK
        self.network = self.s.add_node("Network", {"name": "network"})

        def _mk_node(name, observes_private):
            nn = self.s.add_node("NetworkNode", dict(
                name=name,
                observes_private=float(observes_private),
                charm_weight=float(charm_weight), claim_weight=float(claim_weight),
                instability_discount_weight=float(instability_discount_weight),
                harm_discount_weight=float(harm_discount_weight),
                seen_charm=0.0, seen_harm_direct=0.0,
                seen_victim_claim=0.0, seen_victim_unstable=0.0,
                cred_abuser=0.0, cred_victim=0.0, belief_gap=0.0,
                tick_epoch=0.0, peer_epoch=0.0,
                peer_pull_rate=float(peer_pull_rate)))
            self.inner.add_edge_unchecked(self.network, "has_member", nn)
            return nn

        # DIRECT observers -- N1-shape "outsiders", pure corruption sources.
        self.d1 = _mk_node("d1", 0.0)
        self.d2 = _mk_node("d2", 0.0)
        for d in (self.d1, self.d2):
            self.inner.add_edge_unchecked(d, "observes_stated", self.abuser)
            self.inner.add_edge_unchecked(d, "observes_victim", self.victim)

        # INDIRECT nodes -- sentinel observes_private, no observation edge.
        self.i1 = _mk_node("i1", NO_DIRECT_OBSERVATION)
        self.i2 = _mk_node("i2", 1.0 if self.anchor else NO_DIRECT_OBSERVATION)
        self.i3 = _mk_node("i3", NO_DIRECT_OBSERVATION)
        self.i4 = _mk_node("i4", NO_DIRECT_OBSERVATION)
        self.i5 = _mk_node("i5", NO_DIRECT_OBSERVATION)
        self.i6 = _mk_node("i6", NO_DIRECT_OBSERVATION)

        if self.anchor:
            # the ONLY topology delta between arms: i2 gains a direct,
            # uncorrupted observation edge (N1's own private-face insider
            # mechanism), reusing n1_network_credibility_private VERBATIM.
            self.inner.add_edge_unchecked(self.i2, "observes_held", self.abuser)
            self.inner.add_edge_unchecked(self.i2, "observes_victim", self.victim)

        # peer_of topology (nn -> pp means "nn pulls toward pp's belief"),
        # IDENTICAL in both arms.
        self.inner.add_edge_unchecked(self.i1, "peer_of", self.d1)
        self.inner.add_edge_unchecked(self.i2, "peer_of", self.i1)
        self.inner.add_edge_unchecked(self.i3, "peer_of", self.i2)
        self.inner.add_edge_unchecked(self.i4, "peer_of", self.i2)
        self.inner.add_edge_unchecked(self.i5, "peer_of", self.i1)
        self.inner.add_edge_unchecked(self.i5, "peer_of", self.i2)
        self.inner.add_edge_unchecked(self.i6, "peer_of", self.d2)

        self.direct_nodes = [self.d1, self.d2]
        self.indirect_nodes = [self.i1, self.i2, self.i3, self.i4, self.i5, self.i6]
        self.nodes = self.direct_nodes + self.indirect_nodes

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
        bg = {name: self._attrs(getattr(self, name))["belief_gap"]
              for name in ("d1", "d2", "i1", "i2", "i3", "i4", "i5", "i6")}
        return dict(
            epoch=self.epoch,
            abuser_arousal=aa["arousal"], abuser_frustration=aa["frustration"],
            abuser_snap_count=aa["snap_count"], abuser_stated_charm=aa["stated_charm"],
            victim_arousal=va["arousal"], victim_dysregulated=va["dysregulated"],
            victim_half_width=vw["half_width"],
            **{f"belief_gap_{k}": v for k, v in bg.items()})

    # ------------------------------------------------------------------- step
    def step(self, *, tension=False, jitter=0.0):
        """Advance one tick: (optionally) arm the abuser's tension trickle,
        let the GRAPH decide the dyad + the abuser's stated face
        (run_rules), MECHANICALLY deliver each node's per-tick observation
        counts + tick counter (a world fact, applied UNCONDITIONALLY to all
        8 nodes -- N1's own credibility rules simply never match a node
        whose observes_private sentinel is 2.0, so the counts landing on an
        indirect node are inert), let the GRAPH decide each node's
        credibility belief AND peer-propagated belief (run_rules again),
        read off."""
        self.epoch += 1
        e = float(self.epoch)
        if tension:
            self.s.set_attr(self.gb, "magnitude", float(self.trickle_mag + jitter))
            self.s.set_attr(self.gb, "armed", 1.0)
        self.s.set_attr(self.aaff, "tick_epoch", e)
        self.s.set_attr(self.vaff, "tick_epoch", e)
        self.inner.run_rules()

        # ---- mechanical per-tick observation bookkeeping (world fact -> attr)
        # reused VERBATIM from N1's/N2's own step() -- no credibility or
        # propagation dynamics are reimplemented here, applied UNCONDITIONALLY
        # to every node (N1's rules gate on observes_private themselves).
        stated_charm = self._attrs(self.aaff)["stated_charm"]
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
            self.s.set_attr(nn, "tick_epoch", e)
        self.inner.run_rules()

        r = self.readout()
        self.log.append(r)
        return r

    def run_trajectory(self, T, *, rng=None):
        """Deliver T ticks of the constant, jittered tension trickle -- the
        SAME abuser-side driver in EVERY arm (only the anchor's presence at
        i2 differs)."""
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
