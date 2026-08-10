"""BigvilleTheftWorld -- bigville R44 (block 337000): THEFT AS A MEANINGFUL ACTION AND LAW.

Wires ownership (336000) into the recognition + court machinery. Taking is a world-fact
(anyone can physically take what another holds); theft is a RECOGNIZED frame (witnesses
collapse on whether a taking is theft); a recognized theft feeds the law (charge -> juror
collapse -> verdict -> restitution). Property nobody recognizes cannot be stolen.

A WORLD ADAPTER. No take/recognize/charge/verdict/restitution DECISION in Python -- th_*
and own_* are seed rules. The adapter mints agents/items/claims, seeds recognition and
alliances, arms a `take`, and reads the graph.
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import substrate_rs                                     # noqa: E402
from substrate.seed_loader import manifest_for          # noqa: E402


class BigvilleTheftWorld:
    def __init__(self, *, quorum=1.0, fine_rate=0.5):
        self.eng = substrate_rs.Substrate()._inner
        # bigville_theft depends_on bigville_recognition (Step B: the canonical count rc_count)
        # and bigville_court (Step C: the verdict is the court's collapse, not theft's own).
        # bigville_court's verdict rides agent_judgment's jc_conclude; ct_sentence needs a Treasury.
        self.eng.load_seed_manifest(manifest_for("bigville_recognition"), None)
        self.eng.load_seed_manifest(manifest_for("agent_judgment"), None)
        self.eng.load_seed_manifest(manifest_for("bigville_court"), None)
        # Step D: the constable's Bond EVOLVES from a benefit/betrayal history (not a static scalar).
        self.eng.load_seed_manifest(manifest_for("bigville_bond_update"), None)
        self.eng.load_seed_manifest(manifest_for("bigville_theft"), None)
        self._town = self.eng.add_node("Town", {"name": "Bigville"})
        self._court = self.eng.add_node("Court", {"quorum": float(quorum),
                                                  "fine_rate": float(fine_rate), "coin": 0.0})
        self.eng.add_edge_unchecked(self._town, "has_court", self._court)
        # THE canonical fine sink (design-audit 6.10): the town Treasury, the same coffer
        # bigville_court's ct_sentence fines -- theft's fine/damages now flow here, not court.coin.
        self._treasury = self.eng.add_node("Treasury", {"collected": 0.0})
        self.eng.add_edge_unchecked(self._town, "has_treasury", self._treasury)
        # Step E (adapter shrink): the collapse stance codebooks (TheftStance / OwnStance /
        # DutyStance for the theft/ownership/duty collapses, and the graded Stance codebook the
        # court's jurors collapse over) are now SEED DATA -- shipped in bigville_theft.json's
        # `nodes` and installed by the loader, not minted here. The adapter only builds the
        # per-scenario world (town/court/treasury + agents/items/claims/bonds), arms, and reads.
        self._agents = {}
        self._items = {}
        self._claims = {}     # item -> OwnershipClaim node
        self._constable = None

    def _run(self):
        for _ in range(6):
            self.eng.force_all_dirty()
            self.eng.run_rules(1000000)

    # ------------------------------------------------------------------ ingest
    def add_agent(self, name, *, lawfulness=0.7, ally_taker=0.0, doubt=0.3, alive=1,
                  coin=0.0, deference=0.8, prop_skepticism=0.4):
        a = self.eng.add_node("Agent", {"name": name, "lawfulness": float(lawfulness),
                                        "ally_taker": float(ally_taker), "doubt": float(doubt),
                                        "alive": float(alive), "take_armed": 0.0, "coin": float(coin),
                                        "deference": float(deference),
                                        "prop_skepticism": float(prop_skepticism),
                                        "standing": 0.0,
                                        "theft_choice": "", "own_choice": ""})
        self.eng.add_edge_unchecked(self._town, "has_resident", a)
        self._agents[name] = a
        return a

    def add_institution(self, name):
        node = self.eng.add_node("Institution", {"name": name})
        self._agents[name] = node          # can own / be a victim, but is not a resident-witness
        return node

    def make_juror(self, name):
        """Seat an existing resident on the court's judging panel (design-audit 6.3): the juror
        is on_council AND a governed agent, so agent_judgment's jc_conclude fires per juror and
        the verdict is the court's collapse (ct_verdict), not theft's own th_vote. The juror's
        THEFT lean (lawfulness*theft_standing - doubt) is reproduced through jc_conclude's lean
        (weight*credence + punitiveness - deference*standing): credence = lawfulness,
        punitiveness = -doubt, and the defendant's standing is 0 so the deference term vanishes
        (leaving the juror's ownership `deference`, which own_decide still reads, untouched)."""
        a = self._agents[name]
        attrs = self.eng.node(a)["attrs"]
        self.eng.add_edge_unchecked(self._town, "on_council", a)
        self.eng.add_edge_unchecked(self._town, "governs", a)
        self.eng.set_attr(a, "credence", float(attrs.get("lawfulness", 0.0)))
        self.eng.set_attr(a, "punitiveness", -float(attrs.get("doubt", 0.0)))

    def add_constable(self, name, *, duty=0.9, coin=0.0):
        """The constable -- an office-holder whose JOB is to collect debt. Enforcement is the
        constable's DECISION (duty vs how he FEELS about the debtor), lawful only if the office is
        RECOGNIZED. His forbearance is not a knob -- it is his felt regard toward the person
        (see `constable_feels`)."""
        c = self.add_agent(name, lawfulness=0.9, coin=coin)
        self.eng.set_attr(c, "duty", float(duty))
        self.eng.set_attr(c, "collected", 0.0)
        self.eng.set_attr(c, "authority", 0.0)
        self.eng.add_edge_unchecked(self._town, "has_constable", c)
        self._constable = name
        return c

    def constable_bond(self, toward, *, benefit=0.0, betrayal=0.0, update_gain=1.0,
                       trust=0.0, tie_strength=0.0):
        """How the constable FEELS about a person: the first-class directed Bond(A->B)
        (bigville_bond_update, block 277000) -- con -holds_bond-> Bond -toward-> them, carrying the
        six signed relational emotions. con_duty reads warmth = affect_affection - affect_resentment.

        Step D (design-audit 6.4): the feeling is EVOLVED by the bond dynamics from a benefit/
        betrayal HISTORY, not seeded as a final scalar. The adapter seeds the Bond with the
        bond-update knobs (update_gain>0, pos_weight, neg_weight, reappraise_factor) at a NEUTRAL
        0 prior, attaches BondEvent nodes (a positive `benefit` event -- the debtor once helped the
        constable; a negative `betrayal` event -- a default/slight), then runs the dynamics so
        bond_event_benefit raises affect_affection and bond_event_betrayal raises affect_resentment
        (re-appraising affection down). update_gain=0 freezes the bond (the documented falsifier)."""
        b = self.eng.add_node("Bond", {"affect_affection": 0.0, "affect_resentment": 0.0,
                                       "affect_trust": float(trust), "affect_gratitude": 0.0,
                                       "affect_contempt": 0.0, "affect_fear": 0.0,
                                       "attraction": 0.0, "belief_trust": 0.0,
                                       "tie_strength": float(tie_strength),
                                       "update_gain": float(update_gain), "pos_weight": 0.2,
                                       "neg_weight": 0.2, "reappraise_factor": 0.5, "tie_erode": 0.0})
        self.eng.add_edge_unchecked(self._agents[self._constable], "holds_bond", b)
        self.eng.add_edge_unchecked(b, "toward", self._agents[toward])
        if benefit > 0:
            ev = self.eng.add_node("BondEvent", {"valence": 1.0, "magnitude": float(benefit),
                                                 "applied": 0.0})
            self.eng.add_edge_unchecked(b, "has_event", ev)
        if betrayal > 0:
            ev = self.eng.add_node("BondEvent", {"valence": -1.0, "magnitude": float(betrayal),
                                                 "applied": 0.0})
            self.eng.add_edge_unchecked(b, "has_event", ev)
        self._run()          # EVOLVE the bond from its history before the constable reads it
        return b

    def recognize_constable(self, recognizer):
        """A resident recognizes the constable's office (authority = Count of these)."""
        self.eng.add_edge_unchecked(self._agents[recognizer], "recognizes_office",
                                    self._agents[self._constable])

    def earn(self, name, amount):
        """The debtor earns income -- the constable collects against it on the next settle."""
        a = self._agents[name]
        self.eng.set_attr(a, "coin", float(self.eng.node(a)["attrs"].get("coin", 0.0)) + float(amount))
        self._run()

    def add_item(self, name, *, holder, value=4.0):
        it = self.eng.add_node("Item", {"name": name, "value": float(value), "taken": 0.0,
                                        "consented": 0.0, "charged": 0.0, "restored": 0.0,
                                        "theft_standing": 0.0})
        self.eng.add_edge_unchecked(self._agents[holder], "holds", it)
        self._items[name] = it
        return it

    def claim_ownership(self, owner, item, *, legitimacy=0.0):
        """`owner` claims the item, with a `legitimacy` (provenance). Ownership is real only as far
        as it is RECOGNIZED. legitimacy>0 lets residents DECIDE recognition (own_decide collapse);
        legitimacy=0 (default) recognizes no one -- use recognize_ownership to force it explicitly."""
        c = self.eng.add_node("OwnershipClaim", {"claimant": owner, "recognition": 0.0,
                                                 "legitimacy": float(legitimacy)})
        self.eng.add_edge_unchecked(c, "over", self._items[item])
        self.eng.add_edge_unchecked(c, "by", self._agents[owner])
        self._claims[item] = c
        return c

    def recognize_ownership(self, recognizer, item):
        """Force an explicit recognition edge (a manual override / seed). The emergent path is the
        own_decide collapse driven by claim legitimacy + each resident's disposition."""
        self.eng.add_edge_unchecked(self._agents[recognizer], "recognizes", self._claims[item])

    def settle(self):
        """Let the ownership-recognition collapse (and anything armed) reach fixpoint."""
        self._run()

    def set_ally_of_taker(self, name):
        """This resident is allied with the taker -- will not recognize the taking as theft."""
        self.eng.set_attr(self._agents[name], "ally_taker", 1.0)

    def consent(self, item):
        """The owner consented to the transfer -- taking it is not theft."""
        self.eng.set_attr(self._items[item], "consented", 1.0)

    def take(self, taker, item):
        """WORLD-FACT: the taker physically takes the item. Arms the take and settles the
        recognition -> charge -> verdict -> restitution cascade."""
        self.eng.add_edge_unchecked(self._agents[taker], "taking", self._items[item])
        self.eng.set_attr(self._agents[taker], "take_armed", 1.0)
        self._run()

    # ------------------------------------------------- glass-box read-offs
    def holder_of(self, item):
        for src in self.eng.in_neighbours(self._items[item], "holds"):
            return self.eng.node(src)["attrs"]["name"]
        return None
    def owner_of(self, item):
        """The RECOGNIZED owner (claimant with recognition > 0), or None."""
        c = self._claims.get(item)
        if c and float(self.eng.node(c)["attrs"].get("recognition", 0.0)) > 0:
            return self.eng.node(c)["attrs"]["claimant"]
        return None
    def theft_standing(self, item): return int(round(float(self.eng.node(self._items[item])["attrs"]["theft_standing"])))
    def is_charged(self, item): return float(self.eng.node(self._items[item])["attrs"].get("charged", 0.0)) == 1.0
    def _offense_over(self, item):
        for src in self.eng.in_neighbours(self._items[item], "over_offense"):
            return src
        return None
    def verdict(self, item):
        off = self._offense_over(item)
        if off is None: return None
        st = self.eng.node(off)["attrs"].get("status", "")
        if st == "guilty": return "guilty"
        if st == "acquitted": return "acquitted"
        return "undecided"
    def was_restored(self, item): return float(self.eng.node(self._items[item])["attrs"].get("restored", 0.0)) == 1.0
    def recognizers(self, item):
        """How many residents recognize the owner's claim (emergent or seeded)."""
        c = self._claims.get(item)
        return 0 if c is None else int(round(float(self.eng.node(c)["attrs"].get("recognition", 0.0))))
    def coin(self, name): return round(float(self.eng.node(self._agents[name])["attrs"].get("coin", 0.0)), 4)
    def court_coin(self):
        # the fine sink is the town Treasury now (design-audit 6.10), not court.coin.
        return round(float(self.eng.node(self._treasury)["attrs"].get("collected", 0.0)), 4)
    def _off_attr(self, item, k):
        off = self._offense_over(item)
        return None if off is None else round(float(self.eng.node(off)["attrs"].get(k, 0.0)), 4)
    def damages(self, item): return self._off_attr(item, "damages")
    def fine(self, item): return self._off_attr(item, "fine")
    def debt(self, item): return self._off_attr(item, "debt")
    def debt_damages(self, item): return self._off_attr(item, "debt_damages")
    def debt_fine(self, item): return self._off_attr(item, "debt_fine")
    def constable_authority(self):
        return int(round(float(self.eng.node(self._agents[self._constable])["attrs"].get("authority", 0.0))))
    def constable_choice(self):
        return self.eng.node(self._agents[self._constable])["attrs"].get("duty_choice", "")
    def collected(self):
        return round(float(self.eng.node(self._agents[self._constable])["attrs"].get("collected", 0.0)), 4)
