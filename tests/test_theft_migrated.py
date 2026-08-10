"""bigville R44 (block 337000): THEFT AS A MEANINGFUL ACTION AND LAW -- ownership (336000)
wired into recognition + court. Taking is a world-fact; theft is recognized; a recognized
theft is charged, tried by a juror collapse, and a guilty verdict restitutes. Gates mirror
BIGVILLE_THEFT_PREREG.md.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_theft_world import BigvilleTheftWorld   # noqa: E402


def _town(quorum=2.0, thief_lawful=0.2, wit_doubt=0.3):
    w = BigvilleTheftWorld(quorum=quorum)
    w.add_agent("Owner", lawfulness=0.9)
    w.add_agent("Thief", lawfulness=thief_lawful)
    for n in ("Wit1", "Wit2", "Wit3"):
        w.add_agent(n, lawfulness=0.8, doubt=wit_doubt)
    w.add_item("cloak", holder="Owner")
    w.claim_ownership("Owner", "cloak")
    return w


# ------------------------------------------------------ G-take-is-a-world-fact
def test_taking_is_a_world_fact_the_substrate_never_forbids():
    w = _town()
    # nobody has recognized the ownership yet -- the take still physically succeeds
    w.take("Thief", "cloak")
    assert w.holder_of("cloak") == "Thief", "anyone can physically take what another holds"


# ------------------------------------------------------ G-recognized-theft-charged-tried-restituted (headline)
def test_recognized_theft_is_charged_tried_and_restituted():
    w = _town(quorum=2.0)
    for r in ("Owner", "Wit1", "Wit2", "Wit3"):
        w.recognize_ownership(r, "cloak")            # the town recognizes the owner
    for j in ("Wit1", "Wit2", "Wit3"):
        w.make_juror(j)
    w.take("Thief", "cloak")
    assert w.theft_standing("cloak") == 3, "the lawful witnesses recognize the theft"
    assert w.is_charged("cloak"), "recognized theft (>= quorum) is a chargeable offense"
    assert w.verdict("cloak") == "guilty", "the juror collapse finds guilt"
    assert w.was_restored("cloak") and w.holder_of("cloak") == "Owner", \
        "a guilty verdict restitutes -- the cloak returns to the recognized owner"


# ------------------------------------------------------ G-unrecognized-property-no-theft (headline / falsifier)
def test_property_nobody_recognizes_cannot_be_stolen():
    w = _town(quorum=2.0)
    for j in ("Wit1", "Wit2", "Wit3"):
        w.make_juror(j)
    # NO ONE recognizes the owner's claim
    w.take("Thief", "cloak")
    assert w.theft_standing("cloak") == 0, "unrecognized property is seen by no witness"
    assert not w.is_charged("cloak"), "no recognized owner -> no theft -> no charge"
    assert w.holder_of("cloak") == "Thief", "the taking stands; it simply is not a crime"


# ------------------------------------------------------ G-agents-diverge
def test_the_thiefs_allies_do_not_recognize_the_theft():
    w = BigvilleTheftWorld(quorum=2.0)
    w.add_agent("Owner", lawfulness=0.9); w.add_agent("Thief", lawfulness=0.2)
    w.add_agent("L1", lawfulness=0.85); w.add_agent("L2", lawfulness=0.85)
    w.add_agent("C1", lawfulness=0.3); w.add_agent("C2", lawfulness=0.3)
    w.set_ally_of_taker("C1"); w.set_ally_of_taker("C2")
    w.add_item("purse", holder="Owner"); w.claim_ownership("Owner", "purse")
    for r in ("Owner", "L1", "L2", "C1", "C2"):
        w.recognize_ownership(r, "purse")
    w.take("Thief", "purse")
    assert w.theft_standing("purse") == 2, \
        "the lawful recognize the theft; the thief's allies collapse 'innocent' -- agents diverge"


# ------------------------------------------------------ G-own-property-is-not-theft
def test_taking_your_own_recognized_property_is_not_theft():
    w = BigvilleTheftWorld(quorum=1.0)
    w.add_agent("Owner", lawfulness=0.9)
    for n in ("Wit1", "Wit2"):
        w.add_agent(n, lawfulness=0.8)
    w.add_item("hat", holder="Wit1")                 # someone else holds the owner's hat
    w.claim_ownership("Owner", "hat")
    for r in ("Owner", "Wit1", "Wit2"):
        w.recognize_ownership(r, "hat")
    for j in ("Wit1", "Wit2"):
        w.make_juror(j)
    w.take("Owner", "hat")                           # the owner reclaims his own hat
    assert w.theft_standing("hat") == 0 and not w.is_charged("hat"), \
        "taking one's own recognized property is not theft"


# ------------------------------------------------------ G-consent-is-not-theft
def test_a_consented_transfer_is_not_theft():
    w = BigvilleTheftWorld(quorum=1.0)
    w.add_agent("Owner", lawfulness=0.9); w.add_agent("Friend", lawfulness=0.5)
    for n in ("Wit1", "Wit2"):
        w.add_agent(n, lawfulness=0.8)
    w.add_item("book", holder="Owner"); w.claim_ownership("Owner", "book")
    for r in ("Owner", "Wit1", "Wit2"):
        w.recognize_ownership(r, "book")
    w.consent("book")                                # the owner lends it
    w.take("Friend", "book")
    assert w.theft_standing("book") == 0 and not w.is_charged("book"), \
        "a taking the owner consented to is not theft"


# ------------------------------------------------------ G-acquittal-no-restitution (the verdict is a real collapse)
def test_a_doubting_jury_acquits_and_nothing_is_restituted():
    w = BigvilleTheftWorld(quorum=1.0)
    w.add_agent("Owner", lawfulness=0.9); w.add_agent("Thief", lawfulness=0.2)
    # jurors with overwhelming reasonable doubt
    for n in ("J1", "J2", "J3"):
        w.add_agent(n, lawfulness=0.8, doubt=9.0)
    w.add_item("ring", holder="Owner"); w.claim_ownership("Owner", "ring")
    for r in ("Owner", "J1", "J2", "J3"):
        w.recognize_ownership(r, "ring")
    for j in ("J1", "J2", "J3"):
        w.make_juror(j)
    w.take("Thief", "ring")
    assert w.is_charged("ring"), "the theft is recognized and charged"
    assert w.verdict("ring") == "acquitted", "but a doubting jury collapses to acquit"
    assert not w.was_restored("ring") and w.holder_of("ring") == "Thief", \
        "an acquittal restitutes nothing -- the verdict is a genuine collapse, not automatic"


# ------------------------------------------------------ G-ownership-emerges-from-recognition (headline)
def test_ownership_emerges_from_the_recognition_collapse():
    # a LEGITIMATE claim: law-abiding residents DECIDE to recognize it (not seeded)
    w = BigvilleTheftWorld(quorum=2.0)
    w.add_agent("Owner", lawfulness=0.9)
    for n in ("W1", "W2", "W3"):
        w.add_agent(n, lawfulness=0.8, deference=0.8, prop_skepticism=0.4)
    w.add_item("cloak", holder="Owner")
    w.claim_ownership("Owner", "cloak", legitimacy=0.8)     # no recognize_ownership calls
    w.settle()
    assert w.recognizers("cloak") >= 3 and w.owner_of("cloak") == "Owner", \
        "a legitimate claim gathers recognition from the law-abiding -- ownership emerges"
    # a USURPER'S low-legitimacy grab gathers little recognition
    u = BigvilleTheftWorld(quorum=2.0)
    u.add_agent("Usurper", lawfulness=0.2)
    for n in ("W1", "W2", "W3"):
        u.add_agent(n, lawfulness=0.8, deference=0.8, prop_skepticism=0.4)
    u.add_item("crown", holder="Usurper")
    u.claim_ownership("Usurper", "crown", legitimacy=0.15)
    u.settle()
    assert u.recognizers("crown") == 0 and u.owner_of("crown") is None, \
        "an illegitimate grab is not recognized -- not really owner"


# ------------------------------------------------------ G-emergent-theft
def test_theft_rests_on_emergent_not_seeded_ownership():
    w = BigvilleTheftWorld(quorum=2.0)
    w.add_agent("Owner", lawfulness=0.9); w.add_agent("Thief", lawfulness=0.2)
    for n in ("W1", "W2", "W3"):
        w.add_agent(n, lawfulness=0.8)
    w.add_item("cloak", holder="Owner")
    w.claim_ownership("Owner", "cloak", legitimacy=0.8)     # ownership emerges, not seeded
    for j in ("W1", "W2", "W3"):
        w.make_juror(j)
    w.take("Thief", "cloak")
    assert w.is_charged("cloak") and w.verdict("cloak") == "guilty", \
        "taking emergently-recognized property is theft, charged and tried"


# ------------------------------------------------------ G-fine-and-damages (headline)
def test_a_guilty_verdict_imposes_damages_and_a_fine_coin_conserved():
    w = BigvilleTheftWorld(quorum=2.0, fine_rate=0.5)
    w.add_agent("Owner", lawfulness=0.9, coin=10.0)
    w.add_agent("Thief", lawfulness=0.2, coin=20.0)
    for n in ("W1", "W2", "W3"):
        w.add_agent(n, lawfulness=0.8)
    w.add_item("gem", holder="Owner", value=8.0)
    w.claim_ownership("Owner", "gem", legitimacy=0.8)
    for j in ("W1", "W2", "W3"):
        w.make_juror(j)
    t0, o0, c0 = w.coin("Thief"), w.coin("Owner"), w.court_coin()
    w.take("Thief", "gem")
    assert w.verdict("gem") == "guilty"
    assert w.damages("gem") == 8.0 and w.fine("gem") == 4.0, "damages = value, fine = value*rate"
    assert w.coin("Owner") == o0 + 8.0, "the victim is compensated (damages) AND gets the item back"
    assert w.court_coin() == c0 + 4.0, "the court collects the fine"
    assert w.coin("Thief") == t0 - 12.0, "the offender pays damages + fine"
    assert round((w.coin("Thief") - t0) + (w.coin("Owner") - o0) + (w.court_coin() - c0), 6) == 0.0, \
        "coin is conserved -- nothing invented"
    assert w.was_restored("gem") and w.holder_of("gem") == "Owner", "restitution still returns the goods"


# ------------------------------------------------------ G-fine-bounded-by-means
def test_the_penalty_is_bounded_by_ability_to_pay_and_the_rest_is_debt():
    w = BigvilleTheftWorld(quorum=2.0, fine_rate=0.5)
    w.add_agent("Owner", lawfulness=0.9, coin=0.0)
    w.add_agent("Pauper", lawfulness=0.2, coin=3.0)          # cannot cover 8 + 4 = 12
    for n in ("W1", "W2", "W3"):
        w.add_agent(n, lawfulness=0.8)
    w.add_item("gem", holder="Owner", value=8.0)
    w.claim_ownership("Owner", "gem", legitimacy=0.8)
    for j in ("W1", "W2", "W3"):
        w.make_juror(j)
    w.take("Pauper", "gem")
    assert w.verdict("gem") == "guilty"
    assert w.coin("Pauper") == 0.0, "the offender pays everything they have"
    assert w.coin("Owner") == 3.0 and w.court_coin() == 0.0, "damages first, then fine -- capped at means"
    assert w.debt("gem") == 9.0, "the uncollected remainder is debt -- no coin invented"
    assert round((w.coin("Pauper") - 3.0) + w.coin("Owner") + w.court_coin(), 6) == 0.0, "coin conserved"


# ------------------------------------------------------ G-constable-collects-debt (headline)
def _debt_rig(*, duty=0.9, benefit=1.0, betrayal=0.0, update_gain=1.0, recognize=True, thief_coin=3.0):
    w = BigvilleTheftWorld(quorum=2.0, fine_rate=0.5)
    w.add_agent("Owner", coin=0.0); w.add_agent("Thief", lawfulness=0.2, coin=thief_coin)
    for n in ("W1", "W2", "W3"):
        w.add_agent(n, lawfulness=0.8)
    w.add_constable("Bob", duty=duty)
    # how Bob FEELS about the thief: his first-class Bond, EVOLVED (Step D) from a benefit/betrayal
    # HISTORY by bigville_bond_update -- warmth = affect_affection - affect_resentment.
    w.constable_bond("Thief", benefit=benefit, betrayal=betrayal, update_gain=update_gain)
    if recognize:
        for r in ("Owner", "W1", "W2", "W3"):
            w.recognize_constable(r)
    w.add_item("gem", holder="Owner", value=8.0)
    w.claim_ownership("Owner", "gem", legitimacy=0.8)
    for j in ("W1", "W2", "W3"):
        w.make_juror(j)
    w.take("Thief", "gem")
    return w


def test_the_constable_collects_the_debt_over_time():
    w = _debt_rig(thief_coin=3.0)
    assert w.debt("gem") == 9.0 and w.debt_damages("gem") == 5.0 and w.debt_fine("gem") == 4.0
    assert w.constable_choice() == "enforce" and w.constable_authority() == 4
    w.earn("Thief", 5.0)                 # collects the victim's damages first
    assert w.coin("Owner") == 8.0 and w.debt_damages("gem") == 0.0 and w.debt("gem") == 4.0
    assert w.court_coin() == 0.0, "the fine is not touched until the damages are cleared"
    w.earn("Thief", 10.0)               # then the court's fine
    assert w.court_coin() == 4.0 and w.debt("gem") == 0.0, "the constable clears the whole debt over time"
    assert w.collected() == 9.0, "the constable's collected total is the whole debt"
    # coin conserved across the whole process: 3 initial + 15 earned = Owner + Court + Thief
    assert round(w.coin("Owner") + w.court_coin() + w.coin("Thief"), 6) == 18.0


# ------------------------------------------------------ G-fond-constable-forbears (relational feeling)
def test_a_constable_who_feels_warmly_toward_the_debtor_forbears():
    # Bob feels strongly for the debtor (his brother): a large BENEFIT history EVOLVED his
    # affection past his duty (warmth = affect_affection - affect_resentment > duty).
    w = _debt_rig(duty=0.5, benefit=9.0)
    assert w.constable_choice() == "forbear", \
        "forbearance is HOW HE FEELS (evolved Bond warmth > duty), not a knob"
    w.earn("Thief", 20.0)
    assert w.debt("gem") == 9.0 and w.coin("Owner") == 3.0, \
        "he does not collect from someone he cares about more than his duty"
    # the SAME dutiful constable enforces on someone whose BETRAYAL earned his resentment
    e = _debt_rig(duty=0.5, benefit=1.0, betrayal=3.0)
    assert e.constable_choice() == "enforce", \
        "resentment (negative warmth) means the same duty enforces -- it is the relationship, not the office"


# ------------------------------------------------------ G-unrecognized-constable-cannot-collect
def test_an_unrecognized_constable_cannot_lawfully_collect():
    w = _debt_rig(recognize=False)
    assert w.constable_authority() == 0, "no one recognizes the office"
    w.earn("Thief", 20.0)
    assert w.debt("gem") == 9.0, "a self-styled constable the town does not recognize cannot collect"


# ------------------------------------------------------ G-feeling-is-evolved (6.4 Step D falsifier)
def test_the_constable_feeling_is_evolved_not_a_static_scalar():
    """FALSIFIER for the bond-evolution claim: the constable's warmth is EVOLVED by
    bigville_bond_update from a benefit/betrayal history, not a static seeded scalar. The
    documented bond falsifier is update_gain=0 -- it FREEZES the bond at its 0 prior. So the
    SAME large benefit history that makes a fond constable forbear (update_gain=1) does nothing
    when the dynamics are off (update_gain=0): affection stays 0, warmth 0 < duty, he enforces.
    Proves con_duty reads the EVOLVED bond, not a preset feeling."""
    warm = _debt_rig(duty=0.5, benefit=9.0, update_gain=1.0)
    assert warm.constable_choice() == "forbear", "the evolved warmth (benefit history) forbears"
    frozen = _debt_rig(duty=0.5, benefit=9.0, update_gain=0.0)
    assert frozen.constable_choice() == "enforce", \
        "update_gain=0 freezes the bond -- no history moves the feeling, so the same benefit forbears NOT"


# ------------------------------------------------------ G-no-python-decision (source audit)
def test_no_python_decides_theft_or_law():
    src = open(os.path.join(_ROOT, "worlds", "bigville_theft_world.py")).read()
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "_match", "_apply"):
        assert forbidden not in src, f"adapter must not run a rule engine: {forbidden}"
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_theft.json")))
    names = {r["name"] for r in seed["rules"]}
    assert {"th_take", "th_recognize_theft", "th_standing", "th_charge", "th_refer",
            "th_restitution", "own_decide", "own_grant", "th_penalty",
            "con_office", "con_duty", "th_collect"} <= names, names
    # 6.1/6.4 Step B: theft COMPOSES bigville_recognition -- it depends on it and the ownership
    # count is the CANONICAL rc_count (parameterised over the claim node), NOT a theft-local copy.
    assert "bigville_recognition" in seed.get("depends_on", []), \
        "theft must depend on bigville_recognition (the count is composed, not re-authored)"
    assert "own_recognition" not in names, \
        "the duplicated ownership count is deleted -- the count rule lives in bigville_recognition"
    rec = json.load(open(os.path.join(_ROOT, "seeds", "bigville_recognition.json")))
    rc_count = [r for r in rec["rules"] if r["name"] == "rc_count"][0]
    assert ["r", "recognizes", "claim"] in rc_count["match"] and "Count" in json.dumps(rc_count), \
        "the canonical count matches a recognizes edge (per-claim) and Counts recognizers"
    # theft's WIRE to recognition: a witness collapses theft only if it recognizes the owner's claim
    recog = [r for r in seed["rules"] if r["name"] == "th_recognize_theft"][0]
    assert "recognizes" in json.dumps(recog), \
        "theft recognition READS the recognizes edge (the composed wire to bigville_recognition)"
    # 6.3/6.4 Step C: theft COMPOSES bigville_court -- the verdict is the court's collapse,
    # NOT a theft-local jury. th_vote/th_cast_guilty/th_verdict are DELETED; th_charge mints a
    # court Charge/Matter (about_subject + town has_charge) that agent_judgment's jc_conclude
    # collapses and bigville_court's ct_verdict decides.
    assert "bigville_court" in seed.get("depends_on", []), \
        "theft must depend on bigville_court (the verdict is composed, not re-authored)"
    for gone in ("th_vote", "th_cast_guilty", "th_verdict"):
        assert gone not in names, f"{gone} must be deleted -- the verdict lives in bigville_court"
    charge = [r for r in seed["rules"] if r["name"] == "th_charge"][0]
    cbody = json.dumps(charge)
    assert "about_subject" in cbody and "has_charge" in cbody, \
        "th_charge must mint the court's Charge/Matter (about_subject + town has_charge)"
    # the actual verdict is the collapse in agent_judgment + the aggregation in bigville_court.
    judg = json.load(open(os.path.join(_ROOT, "seeds", "agent_judgment.json")))
    assert "jc_conclude" in {r["name"] for r in judg["rules"]} and "Argmax" in json.dumps(judg), \
        "the verdict must be agent_judgment's Argmax collapse"
    court = json.load(open(os.path.join(_ROOT, "seeds", "bigville_court.json")))
    assert {"ct_hear", "ct_condemn", "ct_verdict_guilty", "ct_verdict_acquit"} <= \
        {r["name"] for r in court["rules"]}, "the aggregated verdict lives in bigville_court"
    # the constable's authority is recognition (Count), and collection is a DECISION (collapse)
    co = [r for r in seed["rules"] if r["name"] == "con_office"][0]
    assert "Count" in json.dumps(co) and "recognizes_office" in json.dumps(co), \
        "the constable's authority must be Count(recognizers), not a title"
    cd = [r for r in seed["rules"] if r["name"] == "con_duty"][0]
    assert "DutyStance" in json.dumps(cd) and "Argmax" in json.dumps(cd), \
        "enforcement must be a duty-vs-feeling collapse"
    # the feeling is the FIRST-CLASS Bond(A->B), not an ad-hoc scalar
    assert ["con", "holds_bond", "bond"] in cd["match"] and ["bond", "toward", "debtor"] in cd["match"], \
        "the constable's feeling must be his held Bond toward the debtor (bigville_bond_update)"
    assert "affect_affection" in json.dumps(cd) and "affect_resentment" in json.dumps(cd), \
        "warmth = affect_affection - affect_resentment (the same quantity fast_bond reads)"
    # 6.4 Step D: theft COMPOSES bigville_bond_update -- the constable's Bond EVOLVES from a
    # benefit/betrayal history, it is not an adapter-seeded static scalar.
    assert "bigville_bond_update" in seed.get("depends_on", []), \
        "theft must depend on bigville_bond_update (the constable's feeling evolves)"
    bu = json.load(open(os.path.join(_ROOT, "seeds", "bigville_bond_update.json")))
    bu_names = {r["name"] for r in bu["rules"]}
    assert {"bond_event_benefit", "bond_event_betrayal"} <= bu_names, \
        "the evolving warmth rides bond_event_benefit / bond_event_betrayal"
    # ownership recognition is now a COLLAPSE (own_decide over OwnStance), not seeded
    od = [r for r in seed["rules"] if r["name"] == "own_decide"][0]
    assert "OwnStance" in json.dumps(od) and "Argmax" in json.dumps(od), \
        "ownership recognition must be a decision collapse"
    # the fine transfers coin conservatively (a Min on the offender's balance)
    pen = [r for r in seed["rules"] if r["name"] == "th_penalty"][0]
    assert "Min" in json.dumps(pen) and "fine_rate" in json.dumps(pen), \
        "the penalty must be bounded by ability to pay (no coin invented)"
    blob = json.dumps(seed)
    assert '"owns"' not in blob, "owner is still not a world fact -- no owns edge"
    # theft is a COLLAPSE over stances, and its weight is a COUNT of recognizers
    recog = [r for r in seed["rules"] if r["name"] == "th_recognize_theft"][0]
    assert "TheftStance" in json.dumps(recog) and "Argmax" in json.dumps(recog), \
        "theft recognition must be a collapse, not a flag"
    standing = [r for r in seed["rules"] if r["name"] == "th_standing"][0]
    assert "Count" in json.dumps(standing) and "sees_theft" in json.dumps(standing), \
        "recognized theft = Count(witnesses), like authority"


# ------------------------------------------------------ G-count-is-composed (6.1/6.4 Step B falsifier)
def test_the_ownership_count_genuinely_moved_to_bigville_recognition():
    """FALSIFIER for the composition claim: the ownership-recognition count is NO LONGER a
    theft-local rule -- it lives in bigville_recognition (rc_count). If we load ONLY
    bigville_theft (without its recognition dependency) and seed a recognized OwnershipClaim,
    the count is NEVER computed (recognition stays 0). Loading recognition too restores it.
    This proves the count was composed out, not duplicated."""
    import substrate_rs
    from substrate.seed_loader import manifest_for

    def _rig(load_recognition):
        e = substrate_rs.Substrate()._inner
        if load_recognition:
            e.load_seed_manifest(manifest_for("bigville_recognition"), None)
        e.load_seed_manifest(manifest_for("bigville_theft"), None)
        town = e.add_node("Town", {"name": "B"})
        item = e.add_node("Item", {"name": "cloak"})
        owner = e.add_node("Agent", {"name": "Owner"})
        claim = e.add_node("OwnershipClaim", {"claimant": "Owner", "recognition": 0.0, "legitimacy": 0.0})
        e.add_edge_unchecked(claim, "over", item)
        e.add_edge_unchecked(claim, "by", owner)
        for nm in ("A", "B", "C"):
            a = e.add_node("Agent", {"name": nm, "alive": 1.0})
            e.add_edge_unchecked(town, "has_resident", a)
            e.add_edge_unchecked(a, "recognizes", claim)
        for _ in range(4):
            e.force_all_dirty(); e.run_rules(1000000)
        return float(e.node(claim)["attrs"].get("recognition", 0.0))

    assert _rig(load_recognition=False) == 0.0, \
        "theft ALONE no longer counts recognizers -- the count genuinely moved to bigville_recognition"
    assert _rig(load_recognition=True) == 3.0, \
        "composing bigville_recognition (rc_count) restores the per-claim count"


# ------------------------------------------------------ G-verdict-is-composed (6.3/6.4 Step C falsifier)
def test_the_verdict_genuinely_moved_to_bigville_court():
    """FALSIFIER for the court-composition claim: the verdict is NO LONGER a theft-local jury
    (th_vote/th_verdict are deleted) -- it is agent_judgment's jc_conclude aggregated by
    bigville_court's ct_verdict. Without those rules loaded, a recognized theft is charged but
    NEVER reaches a verdict (status stays 'filed'; the goods are not restituted). Composing the
    court decides it (guilty -> restituted). Proves the verdict was composed out, not duplicated."""
    import substrate_rs
    from substrate.seed_loader import manifest_for

    def _rig(load_court):
        e = substrate_rs.Substrate()._inner
        e.load_seed_manifest(manifest_for("bigville_recognition"), None)
        if load_court:
            e.load_seed_manifest(manifest_for("agent_judgment"), None)
            e.load_seed_manifest(manifest_for("bigville_court"), None)
        e.load_seed_manifest(manifest_for("bigville_theft"), None)
        town = e.add_node("Town", {"name": "B"})
        court = e.add_node("Court", {"quorum": 2.0, "fine_rate": 0.5, "coin": 0.0})
        e.add_edge_unchecked(town, "has_court", court)
        tr = e.add_node("Treasury", {"collected": 0.0}); e.add_edge_unchecked(town, "has_treasury", tr)
        # the TheftStance / Stance codebooks are SEED DATA now (Step E) -- installed by loading
        # bigville_theft above, not minted here.
        owner = e.add_node("Agent", {"name": "Owner", "alive": 1.0, "lawfulness": 0.9,
                                     "ally_taker": 0.0, "standing": 0.0})
        thief = e.add_node("Agent", {"name": "Thief", "alive": 1.0, "take_armed": 0.0,
                                     "lawfulness": 0.2, "standing": 0.0})
        for n in (owner, thief):
            e.add_edge_unchecked(town, "has_resident", n)
        item = e.add_node("Item", {"name": "cloak", "value": 4.0, "taken": 0.0, "consented": 0.0,
                                   "charged": 0.0, "restored": 0.0, "theft_standing": 0.0})
        e.add_edge_unchecked(owner, "holds", item)
        claim = e.add_node("OwnershipClaim", {"claimant": "Owner", "recognition": 0.0, "legitimacy": 0.0})
        e.add_edge_unchecked(claim, "over", item); e.add_edge_unchecked(claim, "by", owner)
        jurors = []
        for i in range(3):
            j = e.add_node("Agent", {"name": f"J{i}", "alive": 1.0, "lawfulness": 0.8,
                                     "ally_taker": 0.0, "doubt": 0.3, "standing": 0.0})
            e.add_edge_unchecked(town, "has_resident", j)
            e.add_edge_unchecked(j, "recognizes", claim)          # recognizes the ownership
            e.add_edge_unchecked(town, "on_council", j)           # seated on the judging panel
            e.add_edge_unchecked(town, "governs", j)
            e.set_attr(j, "credence", 0.8); e.set_attr(j, "punitiveness", -0.3)
            jurors.append(j)
        e.add_edge_unchecked(owner, "recognizes", claim)
        e.add_edge_unchecked(thief, "taking", item); e.set_attr(thief, "take_armed", 1.0)
        for _ in range(8):
            e.force_all_dirty(); e.run_rules(1000000)
        off = None
        for src in e.in_neighbours(item, "over_offense"):
            off = src
        return None if off is None else e.node(off)["attrs"].get("status", "filed"), \
            e.node(item)["attrs"].get("restored", 0.0)

    status_no, restored_no = _rig(load_court=False)
    assert status_no == "filed" and float(restored_no) != 1.0, \
        "without the court, a charged theft NEVER reaches a verdict -- the verdict moved out"
    status_yes, restored_yes = _rig(load_court=True)
    assert status_yes == "guilty" and float(restored_yes) == 1.0, \
        "composing bigville_court (jc_conclude + ct_verdict) decides it guilty and restitutes"
