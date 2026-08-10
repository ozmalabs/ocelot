"""AchieveWorld -- a MECHANICAL single-agent achievement adapter (block 215000).

ARCHITECTURE RULE COMPLIANCE (see experiments/gamma-substrate/CLAUDE.md):
this file is a WORLD ADAPTER. It ingests the task mechanics and emits the
graph's decision around `run_rules()`. It contains NO agent decision:

  * the GRIEVANCE magnitude is the graph rule `gs_grievance_from_slights`
    (a Sum of scale2-decayed Slight contributions); this adapter only creates
    immutable Slight nodes and advances `now_epoch`, then READS `magnitude`.
  * the ACTION (how hard to work / whether to sabotage) is the graph rule
    `gs_choose_action` (Argmax over candidate Appraisals by total_value + amp);
    this adapter only READS `AchieveDecision.chosen_*`.
  * the amplification (`amp`) is the graph rules `gs_amplify_succeed` /
    `gs_amplify_destroy`, gated by the agent's `efficacy` knob.

No `graph_rewrite.run` / `gr.run` / `_match` / `_apply` / `make_rule`; no
`if/else` over an agent's graph state that selects an agent action. Every
conditional here is over WORLD/experiment configuration (which candidates to
publish, which epoch to advance to) -- mechanical.
"""
from __future__ import annotations
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(_ROOT, "runners", "dsl", "python") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from domains.photon_eye import GraphEye                        # noqa: E402
from domains.harvest_world import EP_DEFAULTS, APPR_DEFAULTS   # noqa: E402  (reuse the LANDED economy defaults)
from substrate.seed_loader import manifest_for                 # noqa: E402

# ---- FROZEN task constants (pre-registered, SPITE_TO_SUCCEED_PREREG.md §2) ----
B = 8            # benefit slope: succeed candidate individual_benefit = B * effort
EMAX = 14        # max effort
SMAX = 6         # max sabotage (destroy channel)
RIVAL_ACH0 = 4   # default rival standing = the un-slighted baseline optimum
HALF_LIFE0 = 4   # default grievance half-life (epochs)
EFF_HIGH = 10    # efficacy for a clear path to win
EFF_LOW = 0      # efficacy for no path


class AchieveWorld:
    """A single EmotionHub agent facing an achievement task, with a per-rival
    grievance built from slights. All decisions run in ONE run_rules() fixpoint."""

    def __init__(self, *, efficacy=EFF_HIGH, rival_ach=RIVAL_ACH0,
                 half_life=HALF_LIFE0, slights=None, observed=True):
        """slights: list of (magnitude, epoch) tuples (empty = un-slighted control)."""
        self.efficacy = int(efficacy)
        self.rival_ach = int(rival_ach)
        self.half_life = int(half_life)
        self.observed = 1.0 if observed else 0.0
        self.slights = list(slights or [])

        self.eye = GraphEye(n_az=4, n_el=4, adapt_rate=0.15,
                            context={"retina_2d": True, "synchronous": True,
                                     "worker_capacity": 1}).build()
        self.s = self.eye.substrate
        self.inner = self.s._inner
        self.inner.load_seed_manifest(manifest_for("core_emotions"), self.eye._agent)
        self.inner.load_seed_manifest(manifest_for("grievance_succeed"), self.eye._agent)

        # ---- the agent (mechanical construction) ----
        self.hub = self.s.add_node("EmotionHub", {})
        ep = dict(EP_DEFAULTS)
        ep.update(w_supergraph=0.0, mood_bias=0.0, comms_on=0.0)   # individual achievement
        epn = self.s.add_node("HeldEmotionParams", ep)
        self.inner.add_edge_unchecked(self.hub, "has_emotion_params", epn)

        gp = self.s.add_node("HeldGrievanceParams",
                             {"enabled": 1.0, "efficacy": float(self.efficacy)})
        self.inner.add_edge_unchecked(self.hub, "has_grievance_params", gp)

        self.gr = self.s.add_node("Grievance",
                                  {"magnitude": 0.0, "rival_ach": float(self.rival_ach),
                                   "now_epoch": 0.0, "half_life": float(self.half_life)})
        self.inner.add_edge_unchecked(self.hub, "has_grievance", self.gr)
        for (m, ep_i) in self.slights:
            sl = self.s.add_node("Slight", {"magnitude": float(m), "epoch": float(ep_i)})
            self.inner.add_edge_unchecked(self.gr, "from_slight", sl)

        self.dec = self.s.add_node("AchieveDecision",
                                   {"chosen_output": -1.0, "chosen_rival_harm": -1.0,
                                    "chosen_kind_succeed": -1.0, "chosen_effort": -1.0})
        self.inner.add_edge_unchecked(self.hub, "has_action_decision", self.dec)

        # ---- candidates: succeed (effort) + destroy (sabotage) ----
        self.cands = []
        for e in range(0, EMAX + 1):
            a = dict(APPR_DEFAULTS)
            a.update(individual_benefit=float(B * e), individual_cost=float(e * e),
                     supergraph_contribution=0.0, amp=0.0,
                     effort=float(e), output=float(e), rival_harm=0.0,
                     kind_succeed=1.0, kind_destroy=0.0, observed_by_rival=self.observed)
            self._add_candidate(a)
        for sab in range(1, SMAX + 1):
            a = dict(APPR_DEFAULTS)
            a.update(individual_benefit=float(-sab), individual_cost=0.0,
                     supergraph_contribution=0.0, amp=0.0,
                     effort=0.0, output=0.0, rival_harm=float(sab),
                     kind_succeed=0.0, kind_destroy=1.0, observed_by_rival=self.observed)
            self._add_candidate(a)

    def _add_candidate(self, attrs):
        apn = self.s.add_node("Appraisal", attrs)
        self.inner.add_edge_unchecked(self.hub, "has_appraisal", apn)   # core_emotions fires
        self.inner.add_edge_unchecked(self.hub, "has_candidate", apn)   # gs_choose_action ranges
        self.cands.append(apn)

    # ---- one settle at a given epoch: ingest epoch + reset amp, tick, read off ----
    def decide(self, now_epoch=0):
        self.s.set_attr(self.gr, "now_epoch", float(now_epoch))
        for c in self.cands:                       # mechanical amp reset (like harvest republishing)
            self.s.set_attr(c, "amp", 0.0)
        self.inner.run_rules()
        a = self.s.node(self.dec)["attrs"]
        return dict(
            grievance=int(self.s.node(self.gr)["attrs"]["magnitude"]),
            output=int(a["chosen_output"]),
            rival_harm=int(a["chosen_rival_harm"]),
            kind_succeed=int(a["chosen_kind_succeed"]),
            effort=int(a["chosen_effort"]),
        )

    def close(self):
        try:
            self.eye.stop()
        except Exception:
            pass
