"""BigvilleLawWorld -- KNOWN LAWS + IN-GAME ENFORCEMENT (block 247000).

A MECHANICAL host layer that SUBCLASSES the proven bigville sim scaffold (block
245000/246000 ``BigvilleSimWorld``) and adds an enforcement cast -- a Constable
and a Council -- plus the graph-resident Law objects the inhabitants HOLD. It
does NOT edit any existing file: it imports the sim world, mints the law nodes,
and loads the additive ``bigville_laws_enforcement`` seed (the 5 enforcement
rules). Every enforcement DECISION is a graph rule; this adapter only does the
two admissible things:

  * INGEST -- the ONE new fact is WITNESSING, and it is the SAME occlusion gate
    the villagers already use: after John's held decision each tick, the
    Constable accrues ``witnessed_harm`` (and sets ``witnessed_act`` = the act it
    saw) ONLY when it has line-of-sight to the office AND John held harm. An
    occluded constable never accrues it. This is mechanical geometry -> a graph
    fact, no decision.
  * EMIT -- read the graph's enforcement decisions back out (Violation /
    EnforcementDecision / RemovalMotion / RemovalOutcome nodes, the Office
    state) for the gates + viewer.

NO agent decision here. WHETHER a witnessed act is a violation is the rule
bl_detect_violation (a decode of the perceived act against the held law's
`prohibits` pattern). WHETHER to enforce is bl_enforce/bl_decline (the enforcer's
own duty-vs-loyalty). WHETHER the council removes John is bl_council_removes (a
lawful motion + impartiality + a believing quorum). Not one of those is a Python
`if`. No graph_rewrite.run / gr.run / _match / _apply / make_rule. No Rust; the
enforcement seed is integer-native and reuses the drama's byte-identical engine.
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(_ROOT, "runners", "dsl", "python") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from worlds.bigville_sim_world import BigvilleSimWorld     # noqa: E402
from substrate.seed_loader import manifest_for             # noqa: E402

# ---- FIXED config (pre-registered, BIGVILLE_LAW_PREREG.md) -----------------
PROHIBIT_CODE = "PROHIBIT_OFFICE_HARM"      # the law John can violate
REMOVAL_CODE = "OFFICE_REMOVAL"             # the lawful instrument of Mary's counter
OFFICE_HARM = "office_harm"                 # the prohibited act (John's held UNDERMINE, from office)
DUTY_WEIGHT = 1.0                           # the enforcer's duty to the law
LOYALTY_IMPARTIAL = 0.0                     # an impartial constable
LOYALTY_CAPTURED = 2.0                      # John's lever (loyalty > duty -> declines)
COUNCIL_QUORUM = 3.0                        # a believing quorum for lawful removal

# constable posts (grounded LOS): the office-door beat WITNESSES the scheming;
# the square post is OCCLUDED from the enclosed office (verified by the sim's
# Bresenham line-of-sight query -- see BIGVILLE_LAW_PREREG.md).
CONSTABLE_WITNESS_PT = (10, 4)              # office-door beat -> LOS into the office
CONSTABLE_OCCLUDED_PT = (14, 8)            # town square -> office occluded by walls


class BigvilleLawWorld(BigvilleSimWorld):
    """The bigville sim + a KNOWN-LAWS enforcement layer.

    Knobs (all graph data, read by the enforcement rules):
      constable_sees_office : True -> constable posted with LOS to the office (it
                              WITNESSES the scheming); False -> posted in the
                              square, the office OCCLUDED (it witnesses nothing).
                              The ONLY difference between the two arms is geometry.
      constable_captured    : False -> impartial (loyalty_to_john=0 -> ENFORCES);
                              True -> John holds the lever (loyalty_to_john>duty ->
                              DECLINES). John also `appointed` the captured constable.
      council_impartial     : True -> the council may enact removal; False -> a
                              captured council never removes (the motion stalls).
      mary_knows_removal_law: True -> Mary HOLDS the removal law (can file a lawful
                              motion); False -> she holds no instrument (control:
                              her goal cannot act extra-legally).
    """

    def __init__(self, *, constable_sees_office=True, constable_captured=False,
                 council_impartial=True, mary_knows_removal_law=True,
                 john_psychopath=True, mary_tom=True, deception=True,
                 indifferent=False):
        super().__init__(john_psychopath=john_psychopath, mary_tom=mary_tom,
                         deception=deception, indifferent=indifferent)
        self.constable_sees_office = bool(constable_sees_office)
        self.constable_captured = bool(constable_captured)
        self.council_impartial = bool(council_impartial)
        self.mary_knows_removal_law = bool(mary_knows_removal_law)

        s, inner, d = self.s, self.inner, self.d
        # the enforcement RULES (additive seed; self_load_only -> never in a full boot)
        inner.load_seed_manifest(manifest_for("bigville_laws_enforcement"), d.eye._agent)

        # ---- LAWS: first-class graph objects the inhabitants HOLD ------------
        self.prohibition_law = s.add_node("Law", {
            "code": PROHIBIT_CODE, "kind": "prohibition", "prohibits": OFFICE_HARM,
            "removal_process": "none", "enabled": 1.0})
        self.removal_law = s.add_node("Law", {
            "code": REMOVAL_CODE, "kind": "removal", "prohibits": "none",
            "removal_process": "council_motion", "enabled": 1.0})
        self.laws = [self.prohibition_law, self.removal_law]

        # every inhabitant KNOWS the laws (they are KNOWN objects, not a hidden
        # constraint). Mary's REMOVAL-law knowledge is the lawful-instrument knob:
        # withheld -> she holds no removal instrument (control: no extra-legal path).
        for h in [d.john, self.reporter] + list(d.villagers):
            for law in self.laws:
                inner.add_edge_unchecked(h, "knows_law", law)
        inner.add_edge_unchecked(d.mary, "knows_law", self.prohibition_law)
        if self.mary_knows_removal_law:
            inner.add_edge_unchecked(d.mary, "knows_law", self.removal_law)

        # THE ELECTORATE: the 5 citizen villagers are the council's electors; the
        # press (reporter) is NOT (is_elector=0), so the quorum reads citizen
        # backing, not the newspaper's stance. Mechanical initial-condition data.
        for v in d.villagers:
            s.set_attr(v, "is_elector", 1.0)
        s.set_attr(self.reporter, "is_elector", 0.0)

        # ---- OFFICE: the in-graph consequence surface ------------------------
        self.office = s.add_node("Office", {
            "holder": "John", "hold": 1.0, "censures": 0.0, "removed": 0.0})
        inner.add_edge_unchecked(d.john, "holds_office", self.office)

        # ---- CONSTABLE: the enforcement-role agent (decides by rule) ---------
        loyalty = LOYALTY_CAPTURED if self.constable_captured else LOYALTY_IMPARTIAL
        self.constable = s.add_node("Constable", {
            "name": "constable", "enforce_on": 1.0,
            "witnessed_harm": 0.0, "witnessed_act": "none",
            "duty_weight": DUTY_WEIGHT, "loyalty_to_john": float(loyalty),
            "detected": 0.0, "enforced": 0.0})
        inner.add_edge_unchecked(self.constable, "knows_law", self.prohibition_law)
        inner.add_edge_unchecked(self.constable, "oversees_office", self.office)
        if self.constable_captured:
            # John holds the enforcement lever: he appointed the captured constable
            inner.add_edge_unchecked(d.john, "appointed", self.constable)
        self.pos["constable"] = (CONSTABLE_WITNESS_PT if self.constable_sees_office
                                 else CONSTABLE_OCCLUDED_PT)

        # ---- COUNCIL: the removal-law body (enacts the lawful counter) -------
        self.council = s.add_node("Council", {
            "name": "council", "impartial": 1.0 if self.council_impartial else 0.0,
            "quorum": COUNCIL_QUORUM, "acted": 0.0})
        inner.add_edge_unchecked(self.council, "knows_law", self.removal_law)
        inner.add_edge_unchecked(self.council, "oversees_office", self.office)

        # static LOS of the constable to the office event point (geometry gate)
        self._con_sees_office = self.perceives("constable", self.office_pt)

    # ------------------------------------------------------------------
    def _held_this_tick(self):
        """MECHANICAL read-back: John's HELD harm on the last utterance (0/1)."""
        if not self.d.utterances:
            return 0
        return int(max(0, self.s.node(self.d.utterances[-1])["attrs"]["held_hostile"]))

    def step(self):
        """One tick of the proven drama + sim (super), THEN the mechanical
        witnessing ingest (occlusion-gated) + one enforcement run_rules fixpoint.
        The enforcement rules DECIDE; this only translates geometry -> a fact."""
        frame = super().step()
        held = self._held_this_tick()
        # WITNESSING -- the SAME occlusion gate the villagers use. The constable
        # accrues the witnessed harm + names the act it saw ONLY under line-of-sight
        # to the office. Occluded -> nothing accrues -> detection never fires.
        if self._con_sees_office and held == 1:
            a = self.s.node(self.constable)["attrs"]
            self.s.set_attr(self.constable, "witnessed_harm", a["witnessed_harm"] + 1.0)
            self.s.set_attr(self.constable, "witnessed_act", OFFICE_HARM)
        # enforcement + lawful-counter rules fire here (detect/enforce/decline/
        # file-motion/council-remove), to fixpoint. No Python decides.
        self.inner.run_rules()
        frame["law"] = self.law_snapshot()
        return frame

    def run(self, T=20):
        for _ in range(T):
            self.step()
        return self.frames

    # -------------------- glass-box read-offs (EMIT) --------------------
    def _nodes_of(self, ntype):
        return [self.s.node(n)["attrs"] for n in self.s.nodes(ntype)]

    def _knows_law_map(self):
        """Which inhabitant HOLDS which law codes (read from knows_law edges)."""
        nodes, out = self._index()
        names = {self.d.john: "John", self.d.mary: "Mary", self.reporter: "reporter"}
        for i, v in enumerate(self.d.villagers):
            names[v] = "villager_%d" % i
        m = {}
        for src, nm in names.items():
            codes = []
            for (etype, tgt) in out.get(src, []):
                if etype == "knows_law" and tgt in nodes:
                    codes.append(nodes[tgt]["attrs"].get("code"))
            m[nm] = sorted(codes)
        return m

    def law_snapshot(self):
        """The full enforcement read-off: laws + who holds them, violations,
        enforcement decisions, the office state, and the lawful-counter trail."""
        con = self.s.node(self.constable)["attrs"]
        cou = self.s.node(self.council)["attrs"]
        off = self.s.node(self.office)["attrs"]
        return dict(
            laws=[dict(code=l["code"], kind=l["kind"], prohibits=l["prohibits"])
                  for l in self._nodes_of("Law")],
            laws_known_by=self._knows_law_map(),
            violations=[dict(about=x.get("about"), act=x.get("act"),
                             law_code=x.get("law_code"), witnessed_by=x.get("witnessed_by"))
                        for x in self._nodes_of("Violation")],
            enforcement=[dict(outcome=x.get("outcome"), by=x.get("by"),
                              reason=x.get("reason")) for x in self._nodes_of("EnforcementDecision")],
            office=dict(holder=off.get("holder"), hold=int(off.get("hold", 0)),
                        censures=int(off.get("censures", 0)), removed=int(off.get("removed", 0))),
            removal_motions=[dict(about=x.get("about"), by=x.get("by"),
                                  law_code=x.get("law_code")) for x in self._nodes_of("RemovalMotion")],
            removal_outcomes=[dict(outcome=x.get("outcome"), lawful=int(x.get("lawful", 0)))
                              for x in self._nodes_of("RemovalOutcome")],
            constable=dict(name=con.get("name"), sees_office=bool(self._con_sees_office),
                           witnessed_harm=int(con.get("witnessed_harm", 0)),
                           witnessed_act=con.get("witnessed_act"),
                           duty_weight=con.get("duty_weight"),
                           loyalty_to_john=con.get("loyalty_to_john"),
                           detected=int(con.get("detected", 0)),
                           enforced=int(con.get("enforced", 0))),
            council=dict(impartial=int(cou.get("impartial", 0)),
                         quorum=int(cou.get("quorum", 0)), acted=int(cou.get("acted", 0))),
            backs_mary_count=self.d.backs_mary_count())

    def _scheme_rate(self):
        """Fraction of ticks John HELD undermine, read from the utterance ledger
        (the sim world does not populate d.episode)."""
        utt = self.d.utterances
        if not utt:
            return 0.0
        held = sum(int(max(0, self.s.node(u)["attrs"]["held_hostile"])) for u in utt)
        return held / len(utt)

    def outcome(self):
        """A compact outcome record for the gates (deterministic)."""
        law = self.law_snapshot()
        return dict(
            ticks=self.tick,
            john_scheme_rate=self._scheme_rate(),
            law=law,
            n_violations=len(law["violations"]),
            enforced=any(e["outcome"] == "enforce" for e in law["enforcement"]),
            declined=any(e["outcome"] == "decline" for e in law["enforcement"]),
            censures=law["office"]["censures"],
            office_hold=law["office"]["hold"],
            removed=law["office"]["removed"],
            n_motions=len(law["removal_motions"]),
            lawfully_removed=any(o["lawful"] == 1 for o in law["removal_outcomes"]))
