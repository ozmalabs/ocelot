"""BigvilleViolWorld -- bigville R15 (block 263000): VIOLENCE, a simple SCALAR.
Inter-agent physical harm + the 247 evidence-and-proof enforcement pipeline. On
top of the proven R17 affect world (the decision_value trigger) -> R14 life world
(the ONE HEALTH variable + bl_death) -> R13 land / R9 council / R7 finance / R1
movement+energy through the MRO.

WHAT THIS ADDS (spec BIGVILLE_MOVEMENT_ECONOMY_SPEC.md §2.9 + §3 R15)
--------------------------------------------------------------------
  * THE ACT       -- a ViolentAct{amount,cost}. bv_trigger is the value-DECISION to
                     commit (snap_pressure + w_spite*spite_gain + hunger*
                     desperation_gain vs trigger_threshold, gated on energy>=cost);
                     bv_refrain is the decline arm. bv_harm_victim (health -=
                     amount, last_cause=5) + bv_cost_aggressor (energy -= cost).
  * THE PIPELINE  -- a Case learned by WITNESS (line-of-sight) OR REPORT (a
                     testimony Message); Evidence accrues (witness/testimony/
                     physical health-drop/alibi); bv_form_belief ABDUCES a verdict
                     (Argmax over the constable's held CaseGenerator codebook);
                     bv_sufficient_proof gates on confidence >= proof_threshold.
  * THE STATE     -- a Prosecution filed with the council; the council ADJUDICATES
                     over its backing-graph (Sum of vote over seated CouncilMembers)
                     -> a Conviction; a Sanction (warn/punish) by amount magnitude.
  * THE FIFTH     -- a large act drives health->0 -> R14 bl_death (death_cause=5);
                     bv_death_tag records death_by_violence=1.

ARCHITECTURE-RULE COMPLIANCE (experiments/gamma-substrate/CLAUDE.md)
-------------------------------------------------------------------
A WORLD ADAPTER. It SUBCLASSES R17 (BigvilleAffectWorld) by IMPORT, edits no
tracked file, holds NO agent decision. It ONLY does mechanical I/O: mint a person /
ViolentAct / Case / Evidence / CaseGenerator / Constable / Council / CouncilMember /
report Message (ingest); deliver world facts (an act's amount/cost; the constable's
line-of-sight; a filed report; an alibi; who sits the council and how each votes);
arm one-shots (consider_armed); run the Rust run_rules fixpoint; read state back.
EVERY decision -- the trigger (bv_trigger/bv_refrain), the harm/cost deltas, the
evidence gathering, the abductive belief (bv_form_belief), the proof threshold
(bv_sufficient_proof), the prosecution + council adjudication (bv_council_convict/
bv_council_acquit), the sanction (bv_warn/bv_punish), and the reused R14 bl_death --
is a seed RULE, never Python. NO reward/punishment token. NO new Rust.
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(_ROOT, "runners", "dsl", "python") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from substrate.seed_loader import manifest_for                        # noqa: E402
from worlds.bigville_affect_world import BigvilleAffectWorld          # noqa: E402

# the constable's held codebook (the two case generators he decodes against). A
# GUILTY generator predicts strong evidence; an INNOCENT one predicts none. The
# verdict is the Argmax by fit -- a RECONSTRUCTION, not a fact.
GUILTY_PREDICTS = 8.0
INNOCENT_PREDICTS = 0.0
PROOF_THRESHOLD = 5.0     # the decision_value: sufficient-proof confidence
WARN_THRESHOLD = 20.0     # amount <= this -> WARN, else PUNISH

# violence attrs set on every attacker so a rule never reads a missing key. energy
# (STAMINA) comes from the R1 make_char default (100.0).
VIOL_DEFAULTS = dict(
    snap_pressure=0.0, w_spite=0.0, spite_gain=5.0, hunger=0.0, desperation_gain=5.0,
    trigger_threshold=5.0, attack_amount=10.0, attack_cost=8.0,
    consider_armed=0.0, attacked=0.0, refrained=0.0, death_by_violence=0.0)


class BigvilleViolWorld(BigvilleAffectWorld):
    def __init__(self, **kw):
        super().__init__(**kw)
        for sid in ("bigville_viol_act", "bigville_viol_evidence",
                    "bigville_viol_prosecute", "bigville_viol_kill"):
            self.eng.load_seed_manifest(manifest_for(sid), None)
        self._constable = None
        self._council_node = None
        self._cases = {}          # case label -> Case nid
        self._members = {}        # member name -> CouncilMember nid

    # ================================================================ INGEST
    def make_attacker(self, name, cell, *, coin=0.0, energy=100.0, **kw):
        """A townsperson who can commit violence (the R17 villager + the viol
        attrs). Mechanical graph data -- the trigger PARAMETERS, not a decision."""
        m = self.make_villager(name, cell, coin=coin)
        self.eng.set_attr(m, "energy", float(energy))
        for k, v in VIOL_DEFAULTS.items():
            self.eng.set_attr(m, k, float(v))
        for k, v in kw.items():
            self.eng.set_attr(m, k, float(v))
        return m

    def set_attacker(self, name, **kw):
        """World-fact write of a trigger knob (snap_pressure / w_spite / hunger /
        attack_amount / attack_cost / energy ...). Mechanical."""
        m = self._movers[name]
        for k, v in kw.items():
            self.eng.set_attr(m, k, float(v))

    def consider(self, attacker, victim):
        """Arm the value-DECISION: attach a considers_violence edge attacker->victim
        and set consider_armed=1, then run. bv_trigger DECIDES whether to commit;
        bv_refrain is the decline arm. No decision here -- world delivery only."""
        a = self._movers[attacker]
        for old in list(self.eng.neighbours(a, "considers_violence")):
            self.eng.remove_edge_unchecked(a, "considers_violence", old)
        self.eng.add_edge_unchecked(a, "considers_violence", self._movers[victim])
        self.eng.set_attr(a, "attacked", 0.0)
        self.eng.set_attr(a, "refrained", 0.0)
        self.eng.set_attr(a, "consider_armed", 1.0)
        return self._run()

    # ------------------------------------------------------------ enforcement I/O
    def make_constable(self, *, proof_threshold=PROOF_THRESHOLD):
        """Mint the Constable (the enforcer) holding his two-generator codebook
        (guilty/innocent) + his proof_threshold. Mechanical graph data -- the HELD
        generators; the DECODE (bv_form_belief) is the rule."""
        con = self.eng.add_node("Constable", {"proof_threshold": float(proof_threshold)})
        guilty = self.eng.add_node("CaseGenerator",
                                   {"predicts_evidence": GUILTY_PREDICTS, "verdict": 1.0})
        innocent = self.eng.add_node("CaseGenerator",
                                     {"predicts_evidence": INNOCENT_PREDICTS, "verdict": 0.0})
        self.eng.add_edge_unchecked(con, "has_case_generator", guilty)
        self.eng.add_edge_unchecked(con, "has_case_generator", innocent)
        self._constable = con
        return con

    def make_council(self, *, warn_threshold=WARN_THRESHOLD):
        """Mint the Council (R9, the state that adjudicates a prosecution) + wire the
        constable's files_with edge. Mechanical graph data."""
        assert self._constable is not None, "make_constable first"
        c = self.eng.add_node("Council", {"warn_threshold": float(warn_threshold)})
        self.eng.add_edge_unchecked(self._constable, "files_with", c)
        self._council_node = c
        return c

    def add_council_member(self, name, *, vote, seated=True):
        """Seat a CouncilMember with a vote (+1 back conviction / -1 oppose). John's
        seat is a bloc that can BLOCK or PUSH (structural corruption). Mechanical --
        WHO sits + HOW each votes is a world fact; the Sum-over-seated ADJUDICATION
        is the rule."""
        m = self.eng.add_node("CouncilMember",
                              {"vote": float(vote), "is_seated": 1.0 if seated else 0.0})
        self._members[name] = m
        return m

    def seat(self, name, seated):
        """Ablate / restore a council seat (the clean structural counterfactual).
        Mechanical attr write."""
        self.eng.set_attr(self._members[name], "is_seated", 1.0 if seated else 0.0)

    def open_case(self, label, *, aggressor, victim, witnessed=False, amount=None):
        """Open a Case about an act (the incident exists in the world). known stays
        0 until a WITNESS or REPORT rule fires. `witnessed` delivers the constable's
        line-of-sight (a world fact, exactly as bigville_laws_enforcement delivers
        witnessed_act). amount is the true severity (glass-box)."""
        assert self._constable is not None, "make_constable first"
        if amount is None:
            amount = float(self.eng.node(self._movers[aggressor])["attrs"]
                           .get("attack_amount", 0.0))
        case = self.eng.add_node("Case", {
            "aggressor": aggressor, "amount": float(amount),
            "witnessed": 1.0 if witnessed else 0.0,
            "known": 0.0, "witness_logged": 0.0, "report_logged": 0.0,
            "physical_logged": 0.0, "belief_formed": 0.0, "verdict": 0.0,
            "confidence": 0.0, "proven": 0.0, "prosecuted": 0.0})
        self.eng.add_edge_unchecked(self._constable, "investigates", case)
        self.eng.add_edge_unchecked(case, "against_victim", self._movers[victim])
        self._cases[label] = case
        return case

    def report(self, label, reporter):
        """The victim or a bystander TELLS the constable -- a testimony Message
        (report) that opens the case via bv_report_evidence (the load-bearing report
        channel). Mechanical graph data."""
        msg = self.eng.add_node("Message", {"kind": "testimony", "from": reporter})
        self.eng.add_edge_unchecked(self._cases[label], "reported_by", msg)
        return msg

    def add_alibi(self, label, *, weight=-3.0):
        """Deliver CONTRADICTING evidence (an alibi -- external testimony that lowers
        the observed evidence weight below the generator midpoint). A world fact; the
        REJECTION is the abductive Argmax landing on innocent."""
        ev = self.eng.add_node("Evidence", {"kind": 4.0, "weight": float(weight)})
        self.eng.add_edge_unchecked(self._cases[label], "has_evidence", ev)
        return ev

    def investigate(self):
        """Run the whole 247 pipeline to fixpoint: gather evidence -> ABDUCE a belief
        -> gate on proof -> prosecute -> adjudicate over the council -> sanction. One
        run_rules fixpoint; no Python decision."""
        return self._run()

    # ================================================================ read-offs
    def _c(self, label):
        return self.eng.node(self._cases[label])["attrs"]

    def case_known(self, label):
        return float(self._c(label).get("known", 0.0)) == 1.0

    def verdict_of(self, label):
        """1.0 = guilty reconstruction, 0.0 = innocent. -1 if no belief formed."""
        a = self._c(label)
        if float(a.get("belief_formed", 0.0)) != 1.0:
            return -1.0
        return float(a.get("verdict", 0.0))

    def confidence_of(self, label):
        return float(self._c(label).get("confidence", 0.0))

    def is_proven(self, label):
        return float(self._c(label).get("proven", 0.0)) == 1.0

    def is_prosecuted(self, label):
        return float(self._c(label).get("prosecuted", 0.0)) == 1.0

    def _prosecution_for(self, label):
        who = self._c(label).get("aggressor")
        for nid in self.eng.nodes("Prosecution"):
            if self.eng.node(nid)["attrs"].get("about") == who:
                return nid
        return None

    def prosecution(self, label):
        nid = self._prosecution_for(label)
        return self.eng.node(nid)["attrs"] if nid is not None else None

    def is_convicted(self, label):
        p = self.prosecution(label)
        return p is not None and float(p.get("convicted", 0.0)) == 1.0

    def is_acquitted(self, label):
        p = self.prosecution(label)
        return p is not None and float(p.get("acquitted", 0.0)) == 1.0

    def sanction_kind(self, label):
        """0 = none, 1 = WARN (small amount), 2 = PUNISH (large amount)."""
        p = self.prosecution(label)
        return int(p.get("sanction_kind", 0.0)) if p is not None else 0

    def evidence_weight(self, label):
        """Glass-box: the accumulated observed evidence weight for the case."""
        tot = 0.0
        for ev in self.eng.neighbours(self._cases[label], "has_evidence"):
            tot += float(self.eng.node(ev)["attrs"].get("weight", 0.0))
        return tot

    # ---- act read-offs (mechanical) ----
    def attacked(self, name):
        return float(self.eng.node(self._movers[name])["attrs"].get("attacked", 0.0)) == 1.0

    def refrained(self, name):
        return float(self.eng.node(self._movers[name])["attrs"].get("refrained", 0.0)) == 1.0

    def acts(self):
        return list(self.eng.nodes("ViolentAct"))

    def death_by_violence(self, name):
        return float(self.eng.node(self._movers[name])["attrs"]
                     .get("death_by_violence", 0.0)) == 1.0
