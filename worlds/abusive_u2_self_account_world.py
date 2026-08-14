"""AbusiveU2SelfAccountWorld -- a MECHANICAL abuser/victim/network world for
the ABUSIVE-DYNAMICS U2 rung (block 306000, "self-serving self-account,
sincerely held, no stated-vs-held split" --
ABUSIVE_RELATIONSHIPS_UNINTENTIONAL_SCOPING.md Part E, U2; the last rung of
the unintentional/no-deliberate-deception companion dimension).

Composes N1's own dyad machinery (self-contained restatement -- see
seeds/abusive_u2_self_account.json's own provenance for why N1's seed file is
NOT depended on directly, matching U0's/U1's own precedent) with a network
that observes ONE genuinely-held `SelfAccount.magnitude` -- there is no
second, separately-tracked "true" value the abuser is hiding; the discounted
value IS what the abuser sincerely reports every tick.

TWO ARMS (ABUSIVE_U2_SELF_ACCOUNT_PREREG.md):
  * MINIMIZED      -- `minimization_discount < 1.0`: SelfAccount.magnitude is
                       a genuine fraction of the abuser's true frustration.
                       THE LOOP: predicted to entrap (belief-gap favours the
                       abuser) via a SINCERE, undirected minimization, no
                       Argmax, no choice, no second "true" value withheld.
  * ZERO_DISCOUNT  -- `minimization_discount == 1.0`: SelfAccount.magnitude
                       EXACTLY equals the true frustration -- an abuser with
                       fully accurate self-perception, still sincerely
                       reporting it. FAILABLE: must show the belief-gap NOT
                       favouring the abuser -- if it does, minimization
                       specifically is not the driver (most likely the
                       victim-side instability discount alone is sufficient,
                       reported straight, not rescued).

The abuser's own dyad mechanism (`snap_frustration`, block 242000, UNMODIFIED)
and the victim's entrainment (`arousal_window_coreg`, block 239000,
UNMODIFIED) are IDENTICAL across both arms -- the ONLY manipulated variable
reaching the network is the SINGLE declared constant `minimization_discount`.

ARCHITECTURE RULE COMPLIANCE (CLAUDE.md): this file is a WORLD ADAPTER. Every
decision -- frustration accumulation, the snap threshold, discharge, recovery,
the victim's entrainment, the abuser's self-account magnitude, and the
network's credibility belief-update (cred_abuser/cred_victim/belief_gap) -- is
the graph's decision, entirely inside `seeds/snap_frustration.json` /
`seeds/arousal_window_coreg.json` (both UNMODIFIED) and this rung's three
rules in `seeds/abusive_u2_self_account.json`. The adapter's only
"conditionals" are (i) WHICH ARM to build (an experimental-arm selection made
ONCE per trajectory, exactly as every prior rung), and (ii) mechanically
DELIVERING each tick's observed graph fact (SelfAccount.magnitude vs the
abuser's own recover_floor -- reused verbatim, not invented) onto each
network node's observation-COUNT attrs -- a per-tick tally, never a judgement
about what a node should BELIEVE (that is `u2_network_credibility`'s job,
entirely). NO reward/punishment anywhere: the tension trickle is a
world-delivered fact (mechanically identical to a goal-block magnitude in
239000/242000/298000/310000), never a scored choice.
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(_ROOT, "runners", "dsl", "python") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import substrate_rs as srs                                   # noqa: E402
from substrate.seed_loader import manifest_for                # noqa: E402

# ---- FROZEN world constants (pre-registered, ABUSIVE_U2_SELF_ACCOUNT_PREREG.md)
SETPOINT = 0.0

# abuser (snap_frustration, block 242000 defaults -- BYTE-IDENTICAL to N1's/
# U0's/U1's own frozen constants, since U2 reuses the exact same abuser
# mechanism).
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

# network -- U2-specific, pilot-informed (see PREREG Sec. 3). claim_weight
# and instability_discount_weight are reused UNCHANGED from N1's/U1's own
# operating point (U2's own claim is about minimization_discount and
# charm_weight, not a re-litigation of the victim-side discount).
N_NETWORK_NODES = 5
CHARM_WEIGHT = 3.0
CLAIM_WEIGHT = 1.0
INSTABILITY_DISCOUNT_WEIGHT = 3.0

ARM_NAMES = ("minimized", "zero_discount")

# minimization_discount per arm (pilot-chosen, see PREREG Sec. 3).
MINIMIZATION_DISCOUNT = {"minimized": 0.3, "zero_discount": 1.0}


class AbusiveU2SelfAccountWorld:
    """One ABUSER Agent (snap_frustration, unmodified, byte-identical to
    N1's/U0's/U1's own) carrying a SelfAccount node (this rung's own new
    content), one VICTIM Agent (arousal_window_coreg, unmodified, plus U2's
    own frustration-routed entrainment, byte-identical to N1's), and a
    Network of NetworkNode agents whose reputation belief is entirely
    graph-rule-computed. NO decision here -- only world delivery + mechanical
    per-tick observation-count bookkeeping + read-back."""

    def __init__(self, arm="minimized", *,
                 abuser_half_width=ABUSER_HALF_WIDTH, victim_half_width=VICTIM_HALF_WIDTH,
                 leak=LEAK, k_acc=K_ACC, discharge=DISCHARGE, recover_floor=RECOVER_FLOOR,
                 k_self=K_SELF, k_co=K_CO, trickle_mag=TRICKLE_MAG,
                 n_network_nodes=N_NETWORK_NODES,
                 charm_weight=CHARM_WEIGHT, claim_weight=CLAIM_WEIGHT,
                 instability_discount_weight=INSTABILITY_DISCOUNT_WEIGHT,
                 minimization_discount=None):
        if arm not in ARM_NAMES:
            raise ValueError(f"unknown arm {arm!r}; expected one of {ARM_NAMES}")
        self.arm = arm
        if minimization_discount is None:
            minimization_discount = MINIMIZATION_DISCOUNT[arm]

        self.trickle_mag = float(trickle_mag)
        self.n_network_nodes = int(n_network_nodes)
        self.recover_floor = float(recover_floor)

        self.s = srs.Substrate()
        self.inner = self.s._inner
        self.root = self.s.add_node("Agent", {"role": "u2_root"})
        for seed in ("affective_state_core", "snap_frustration", "arousal_window_coreg",
                     "abusive_u2_self_account"):
            self.inner.load_seed_manifest(manifest_for(seed), self.root)

        # ---------------------------------------------------------- ABUSER
        # snap_frustration's full contract, plus is_abuser=1.0 (read by
        # u2_victim_entrainment/u2_self_account). NO deception_on/stated_charm
        # -- U2 has no stated-vs-held split anywhere.
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
            tick_epoch=0.0, leak_epoch=0.0))
        self.inner.add_edge_unchecked(self.abuser, "has_affective_state", self.aaff)

        hw_a = float(abuser_half_width)
        self.awot = self.s.add_node("WindowOfTolerance", dict(
            name="abuser_window", lo=-hw_a, hi=hw_a, half_width=hw_a))
        self.inner.add_edge_unchecked(self.abuser, "has_window", self.awot)

        self.gb = self.s.add_node("GoalBlock", dict(
            name="tension_trigger", magnitude=0.0, armed=0.0))
        self.inner.add_edge_unchecked(self.abuser, "has_goal_block", self.gb)

        # The ONE new node this rung adds: SelfAccount. `magnitude` is
        # computed by u2_self_account (= minimization_discount * frustration)
        # every tick; there is no second, separately-tracked "true" value
        # anywhere -- this IS the abuser's held, sincerely-reported account.
        self.sa = self.s.add_node("SelfAccount", dict(
            name="abuser_self_account",
            minimization_discount=float(minimization_discount),
            magnitude=0.0))
        self.inner.add_edge_unchecked(self.abuser, "has_self_account", self.sa)

        # ---------------------------------------------------------- VICTIM
        # arousal_window_coreg's full contract; identical to N1's/U1's own.
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

        # attended_by is STATIC across the whole trajectory (matching N1's
        # BASELINE exactly) -- U2, like N1's BASELINE, has no phase schedule.
        self.inner.add_edge_unchecked(self.victim, "attended_by", self.abuser)

        # --------------------------------------------------------- NETWORK
        # A Network hub + N NetworkNode members, ALL observes_self_account
        # (no stated/held split -- every node reads the SAME sincere account).
        self.network = self.s.add_node("Network", {"name": "network"})
        self.nodes = []
        for i in range(self.n_network_nodes):
            nn = self.s.add_node("NetworkNode", dict(
                name=f"node_{i}",
                credibility_on=1.0,
                charm_weight=float(charm_weight), claim_weight=float(claim_weight),
                instability_discount_weight=float(instability_discount_weight),
                seen_mild=0.0, seen_severe=0.0,
                seen_victim_claim=0.0, seen_victim_unstable=0.0,
                cred_abuser=0.0, cred_victim=0.0, belief_gap=0.0))
            self.inner.add_edge_unchecked(self.network, "has_member", nn)
            self.inner.add_edge_unchecked(nn, "observes_self_account", self.abuser)
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
        sa = self._attrs(self.sa)
        nn_rows = [self._attrs(nn) for nn in self.nodes]
        return dict(
            epoch=self.epoch,
            abuser_arousal=aa["arousal"], abuser_frustration=aa["frustration"],
            abuser_snap_count=aa["snap_count"],
            self_account_magnitude=sa["magnitude"],
            victim_arousal=va["arousal"], victim_dysregulated=va["dysregulated"],
            victim_half_width=vw["half_width"],
            belief_gap_mean=(sum(r["belief_gap"] for r in nn_rows) / len(nn_rows)),
            cred_abuser_mean=(sum(r["cred_abuser"] for r in nn_rows) / len(nn_rows)),
            cred_victim_mean=(sum(r["cred_victim"] for r in nn_rows) / len(nn_rows)))

    # ------------------------------------------------------------------- step
    def step(self, *, jitter=0.0):
        """Advance one tick: arm the tension trickle (U2 has no phase
        schedule -- the trickle is armed every tick, matching N1's BASELINE),
        let the GRAPH decide the dyad + the abuser's self-account (run_rules),
        MECHANICALLY deliver each node's per-tick observation counts (a world
        fact, never a judgement), let the GRAPH decide each node's
        credibility belief (run_rules again), read off."""
        self.epoch += 1
        e = float(self.epoch)
        self.s.set_attr(self.gb, "magnitude", float(self.trickle_mag + jitter))
        self.s.set_attr(self.gb, "armed", 1.0)
        self.s.set_attr(self.aaff, "tick_epoch", e)
        self.s.set_attr(self.vaff, "tick_epoch", e)
        self.inner.run_rules()

        # ---- mechanical per-tick observation bookkeeping (world fact -> attr)
        # "mild"/"severe" is a threshold read on SelfAccount.magnitude against
        # the abuser's OWN recover_floor (snap_frustration's own, already-
        # existing "still genuinely elevated" threshold -- reused verbatim,
        # not a new invented cutoff, mirroring N1's own frustration >
        # recover_floor pattern exactly, per the scoping doc's own text).
        magnitude = self._attrs(self.sa)["magnitude"]
        mild = 1.0 if magnitude <= self.recover_floor else 0.0
        severe = 1.0 - mild
        victim_unstable = self._attrs(self.vaff)["dysregulated"]
        for nn in self.nodes:
            a = self._attrs(nn)
            self.s.set_attr(nn, "seen_mild", a["seen_mild"] + mild)
            self.s.set_attr(nn, "seen_severe", a["seen_severe"] + severe)
            self.s.set_attr(nn, "seen_victim_claim", a["seen_victim_claim"] + 1.0)
            self.s.set_attr(nn, "seen_victim_unstable", a["seen_victim_unstable"] + victim_unstable)
        self.inner.run_rules()

        r = self.readout()
        self.log.append(r)
        return r

    def run_trajectory(self, T, *, rng=None):
        """Deliver T ticks of the constant, jittered tension trickle -- the
        SAME abuser-side driver in EVERY arm (only minimization_discount
        differs)."""
        for _ in range(T):
            jitter = 0.0
            if rng is not None:
                jitter = float(rng.normal(0.0, self.trickle_mag * TRICKLE_JITTER_FRAC))
            self.step(jitter=jitter)
        return self.log

    # -------------------------------------------------- glass-box / ethics I/O
    def checkpoint(self):
        """Byte-identical serialisation of the WHOLE mind (graph_to_dict)."""
        return self.s.graph_to_dict()
