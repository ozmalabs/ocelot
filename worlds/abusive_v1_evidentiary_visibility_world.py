"""AbusiveV1EvidentiaryVisibilityWorld -- a MECHANICAL abuser/victim/network
world for the ABUSIVE-DYNAMICS V1 rung (block 364000, "evidentiary
visibility: does a discrete, victim-independent incident trace protect
credibility a purely diffuse pattern cannot earn?" --
ABUSIVE_RELATIONSHIPS_VISIBILITY_SCOPING.md Part E, V1).

Reuses N1's own dyad (`seeds/snap_frustration.json` block 242000 + `seeds/
arousal_window_coreg.json` block 239000, BOTH UNMODIFIED) BYTE-IDENTICALLY,
in BOTH of V1's arms -- there is no dyad-side manipulation anywhere in V1
(unlike N1's own NON_DYSREGULATED_CONTROL or PRIVATE_FACE_CONTROL arms).
The ONLY manipulated variable between V1's two arms is whether this adapter
ever delivers a nonzero `seen_incident` observation to the network.

TWO ARMS (ABUSIVE_V1_EVIDENTIARY_VISIBILITY_PREREG.md):
  * INCIDENT_VISIBLE   -- N1's own BASELINE dyad, byte-identical, PLUS the
                           adapter delivers `seen_incident` increments to
                           every network node whenever the abuser's own
                           `snap_count` has just increased since the
                           previous tick. Prediction: `belief_gap` should be
                           measurably LOWER than the control -- the abuser's
                           own discrete conduct now counts against him.
  * INCIDENT_INVISIBLE -- literally N1's own BASELINE arm, restated
                           byte-identically (the failable control): the
                           adapter simply never delivers `seen_incident`
                           (it stays 0 throughout, exactly the pre-V1
                           world). Discipline check: this arm's `belief_gap`
                           must reproduce N1's own already-published
                           BASELINE number (2370.81 at T=1000).

The abuser's own tension-driven snap dynamics are IDENTICAL across both
arms -- same GoalBlock tension trickle, same seed per trajectory index --
so harm is not merely matched, it is structurally identical by
construction: this is literally the same trajectory replayed with one
observation channel switched on or off (scoping doc Part B3).

ARCHITECTURE RULE COMPLIANCE (CLAUDE.md): this file is a WORLD ADAPTER.
Every decision -- frustration accumulation, the snap threshold, discharge,
recovery, the victim's entrainment, and the network's credibility
belief-update (cred_abuser/cred_victim/belief_gap) -- is the graph's
decision, entirely inside `seeds/snap_frustration.json` / `seeds/
arousal_window_coreg.json` (both UNMODIFIED) and this rung's two new rules
in `seeds/abusive_v1_evidentiary_visibility.json`. The adapter's only
"conditionals" are (i) WHICH ARM to build (an experimental-arm selection
made ONCE per trajectory, exactly as every prior rung in this line) and
(ii) mechanically DELIVERING each tick's observed graph facts onto each
network node's observation-count attrs -- a per-tick tally, never a
judgement about what a node should BELIEVE (that is the credibility rule's
job, entirely).

`seen_incident`'s delivery uses the SAME counter-DELTA-observer idiom R3's
own `r3_prior_track_narrow`/`_widen` already established
(`wot.narrow_count > wot.pn_last_narrow`, ABUSIVE_R3_COERCIVE_CONTROL_
PREREG.md Sec. 2.3): the "last seen" reference (`v1_last_seen_snap_count`)
is a GRAPH ATTRIBUTE on the abuser's own AffectiveState node, owned by this
world's own construction (never a Python variable -- state lives in the
substrate) -- a mechanical read/compare/deliver/update of graph facts,
NEVER a read of the transient `in_snap`/`snapped` flags (the hazard N1's
own Sec. 2.1 documented at length: those flags reset within the SAME
`run_rules()` fixpoint pass at these frozen constants, before any
post-fixpoint Python read can observe them as `1`).

`seen_charm` is delivered as a mechanical per-tick constant (`+=1.0`)
rather than via a restated `n1_abuser_stated_charm`-shaped rule: reading
that rule directly shows it always evaluates to `stated_charm=1.0`
unconditionally under `deception_on=1` (fixed ON in every one of N1's own
arms) -- a structural constant at V1's own single-dyad operating point (V1
has no private-face-control arm to justify keeping the conditional
branch), so the constant delivery reproduces the SAME numeric behaviour
byte-identically, with one fewer rule (matching Part E's "exactly two new
rules" scope).

NO reward/punishment anywhere: the tension trickle is a world-delivered
fact (mechanically identical to a goal-block magnitude in
239000/242000/298000), never a scored choice.
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

# ---- FROZEN world constants (pre-registered, ABUSIVE_V1_EVIDENTIARY_VISIBILITY_PREREG.md)
SETPOINT = 0.0

# abuser (snap_frustration, block 242000 defaults -- BYTE-IDENTICAL to N1's
# own frozen constants, since V1 reuses the exact same abuser mechanism).
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

# network -- N1's own values, reused unchanged, PLUS incident_discount_weight
# (V1-specific, pilot-informed -- see PREREG Sec. 3)
N_NETWORK_NODES = 5
CHARM_WEIGHT = 1.0
CLAIM_WEIGHT = 1.0
INSTABILITY_DISCOUNT_WEIGHT = 3.0
INCIDENT_DISCOUNT_WEIGHT = 3.0  # placeholder default -- overridden per PREREG Sec. 4's pilot-chosen value


class AbusiveV1EvidentiaryVisibilityWorld:
    """One ABUSER Agent (snap_frustration, unmodified, byte-identical to
    N1's own), one VICTIM Agent (arousal_window_coreg, unmodified, plus this
    rung's own frustration-routed entrainment -- ALWAYS coupled, N1's own
    BASELINE dyad in both arms), and a Network of NetworkNode agents whose
    reputation belief about both parties is entirely graph-rule-computed.
    NO decision here -- only world delivery + mechanical per-tick
    observation-count bookkeeping + read-back."""

    def __init__(self, *, deliver_incident=True,
                 n_network_nodes=N_NETWORK_NODES,
                 abuser_half_width=ABUSER_HALF_WIDTH,
                 victim_half_width=VICTIM_HALF_WIDTH,
                 leak=LEAK, k_acc=K_ACC, discharge=DISCHARGE,
                 recover_floor=RECOVER_FLOOR, k_self=K_SELF, k_co=K_CO,
                 trickle_mag=TRICKLE_MAG,
                 charm_weight=CHARM_WEIGHT, claim_weight=CLAIM_WEIGHT,
                 instability_discount_weight=INSTABILITY_DISCOUNT_WEIGHT,
                 incident_discount_weight=INCIDENT_DISCOUNT_WEIGHT):
        self.trickle_mag = float(trickle_mag)
        self.deliver_incident = bool(deliver_incident)
        self.n_network_nodes = int(n_network_nodes)

        self.s = srs.Substrate()
        self.inner = self.s._inner
        self.root = self.s.add_node("Agent", {"role": "v1_root"})
        for seed in ("affective_state_core", "snap_frustration", "arousal_window_coreg",
                     "abusive_v1_evidentiary_visibility"):
            self.inner.load_seed_manifest(manifest_for(seed), self.root)

        # ---------------------------------------------------------- ABUSER
        # snap_frustration's full contract, plus is_abuser=1.0 (read by
        # v1_victim_entrainment) and v1_last_seen_snap_count=0.0 -- the
        # counter-DELTA-observer's own "last seen" reference, a GRAPH
        # attribute this world's own construction owns (never a Python
        # variable). No deception_on/stated_charm keys: v1's seen_charm
        # delivery is a mechanical constant (module docstring), so no rule
        # anywhere reads or writes those keys.
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
            v1_last_seen_snap_count=0.0))
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
        # snap_frustration-specific key (matching N1's own omission list, so
        # snap_arousal_track never accidentally matches the victim). ALWAYS
        # attended_by the abuser -- V1 has no non-dysregulated-control arm;
        # both of V1's arms share this IDENTICAL dyad (scoping doc Part B3's
        # "harm-matching" note: structurally identical by construction).
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

        # --------------------------------------------------------- NETWORK
        # A Network hub + N NetworkNode members. Every member reads the
        # abuser's STATED face (observes_stated) and the victim's
        # presentation (observes_victim) -- V1 has no private-face-insider
        # variant, so every node is an "ordinary" node under the ONE shared
        # v1_network_credibility_incident_aware rule.
        self.network = self.s.add_node("Network", {"name": "network"})
        self.nodes = []
        for i in range(self.n_network_nodes):
            nn = self.s.add_node("NetworkNode", dict(
                name=f"node_{i}",
                charm_weight=float(charm_weight), claim_weight=float(claim_weight),
                instability_discount_weight=float(instability_discount_weight),
                incident_discount_weight=float(incident_discount_weight),
                seen_charm=0.0, seen_incident=0.0,
                seen_victim_claim=0.0, seen_victim_unstable=0.0,
                cred_abuser=0.0, cred_victim=0.0, belief_gap=0.0))
            self.inner.add_edge_unchecked(self.network, "has_member", nn)
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
        return dict(
            epoch=self.epoch,
            abuser_arousal=aa["arousal"], abuser_frustration=aa["frustration"],
            abuser_snap_count=aa["snap_count"],
            victim_arousal=va["arousal"], victim_dysregulated=va["dysregulated"],
            victim_in_episode=va["in_episode"],
            victim_half_width=vw["half_width"],
            belief_gap_mean=(sum(r["belief_gap"] for r in nn_rows) / len(nn_rows)),
            cred_abuser_mean=(sum(r["cred_abuser"] for r in nn_rows) / len(nn_rows)),
            cred_victim_mean=(sum(r["cred_victim"] for r in nn_rows) / len(nn_rows)),
            seen_incident_mean=(sum(r["seen_incident"] for r in nn_rows) / len(nn_rows)),
            seen_charm_mean=(sum(r["seen_charm"] for r in nn_rows) / len(nn_rows)))

    # ------------------------------------------------------------------- step
    def step(self, *, tension=False, jitter=0.0):
        """Advance one tick: (optionally) arm the abuser's tension trickle,
        let the GRAPH decide the dyad (run_rules), MECHANICALLY deliver each
        node's per-tick observation counts (a world fact, never a
        judgement), let the GRAPH decide each node's credibility belief
        (run_rules again), read off."""
        self.epoch += 1
        e = float(self.epoch)
        if tension:
            self.s.set_attr(self.gb, "magnitude", float(self.trickle_mag + jitter))
            self.s.set_attr(self.gb, "armed", 1.0)
        self.s.set_attr(self.aaff, "tick_epoch", e)
        self.s.set_attr(self.vaff, "tick_epoch", e)
        self.inner.run_rules()

        # ---- mechanical per-tick observation bookkeeping (world fact -> attr)
        # seen_charm: a mechanical constant fact (module docstring) --
        # numerically byte-identical to N1's own stated_charm=1.0 broadcast
        # at these frozen constants (deception_on fixed ON).
        victim_unstable = self._attrs(self.vaff)["dysregulated"]

        # seen_incident: counter-DELTA-observer idiom (R3's own
        # r3_prior_track_narrow/_widen), applied to the abuser's OWN
        # snap_count. The "last seen" reference lives ON THE GRAPH
        # (v1_last_seen_snap_count) -- a mechanical read/compare/deliver/
        # update of graph facts, never a Python variable, never a read of
        # the transient in_snap/snapped flags.
        cur_snap_count = self._attrs(self.aaff)["snap_count"]
        last_snap_count = self._attrs(self.aaff)["v1_last_seen_snap_count"]
        incident_this_tick = self.deliver_incident and (cur_snap_count > last_snap_count)
        self.s.set_attr(self.aaff, "v1_last_seen_snap_count", cur_snap_count)

        for nn in self.nodes:
            a = self._attrs(nn)
            self.s.set_attr(nn, "seen_charm", a["seen_charm"] + 1.0)
            self.s.set_attr(nn, "seen_victim_claim", a["seen_victim_claim"] + 1.0)
            self.s.set_attr(nn, "seen_victim_unstable", a["seen_victim_unstable"] + victim_unstable)
            if incident_this_tick:
                self.s.set_attr(nn, "seen_incident", a["seen_incident"] + 1.0)
        self.inner.run_rules()

        r = self.readout()
        self.log.append(r)
        return r

    def run_trajectory(self, T, *, rng=None):
        """Deliver T ticks of the constant, jittered tension trickle -- the
        SAME abuser-side driver in EVERY arm (only whether the adapter
        delivers seen_incident differs)."""
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
