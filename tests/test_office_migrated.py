"""bigville R48 (block 358000): jobs/roles are AGENT-CREATED, ADVERTISED, applied-for,
appointed, delegated -- never hardcoded, never magically filled. A role is created in
response to need (council by decree / owner directly), the opening is made known (note /
word of mouth / direct ask), people DECIDE whether to apply, the delegator selects among
APPLICANTS, and the office outlives its holder. Gates mirror the seed description.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_office_world import BigvilleOfficeWorld as Office   # noqa: E402


def _recognized_council(w_competence=1.0, w_loyalty=0.5):
    w = Office(); w.add_council(w_competence=w_competence, w_loyalty=w_loyalty)
    for r in ("V1", "V2", "V3"):
        w.recognize_council(r)
    return w


# ------------------------------------------------------ G-role-created-by-decree (headline)
def test_the_council_creates_a_role_only_by_decree():
    w = _recognized_council()
    w.add_resident("Alfred", competence=0.9, loyalty=0.6, want_work=0.9, reservation=0.2)
    w.run()
    assert w.offices() == [], "no role is hardcoded -- nothing exists until decreed"
    w.decree_role("constable")
    assert w.office_exists("constable"), "the council decrees a role into existence (its bureaucracy)"


# ------------------------------------------------------ G-owner-creates-directly
def test_an_overloaded_owner_creates_a_role_directly():
    w = Office(); w.add_council()
    w.add_owner("Innkeeper", w_competence=1.0, w_loyalty=0.5)
    w.add_resident("Cookie", competence=0.8, loyalty=0.5, want_work=0.9, reservation=0.2)
    w.add_establishment("Innkeeper", "Inn", workload=10.0, capacity=4.0, needed_role="cook")
    w.run()
    assert w.office_exists("cook"), "an overloaded owner conceives a role directly -- no decree needed"


# ------------------------------------------------------ G-not-magically-filled-must-advertise (headline)
def test_an_opening_is_not_magically_known_it_must_be_advertised():
    w = _recognized_council()
    w.add_resident("Alfred", competence=0.9, loyalty=0.6, want_work=0.9, reservation=0.2)
    w.decree_role("constable")
    assert w.aware("constable") == [] and w.applicants("constable") == [] and not w.is_filled("constable"), \
        "before advertising, nobody knows of the opening -- it is not magically filled"
    w.advertise("constable")
    assert "Alfred" in w.aware("constable"), "a posted note is heard"
    assert "Alfred" in w.applicants("constable") and w.holder_of("constable") == "Alfred", \
        "he learns of it, applies, and is selected"


# ------------------------------------------------------ G-only-applicants-considered (headline)
def test_you_cannot_be_appointed_to_a_job_you_did_not_apply_for():
    w = _recognized_council()
    w.add_resident("Keen", competence=0.6, loyalty=0.6, want_work=0.9, reservation=0.2)
    w.add_resident("Content", competence=0.99, loyalty=0.9, want_work=0.1, reservation=0.8)  # best, but won't apply
    w.decree_role("constable"); w.advertise("constable")
    assert "Content" in w.aware("constable"), "Content heard of the opening"
    assert "Content" not in w.applicants("constable"), "but a content person DECIDES not to apply"
    assert w.holder_of("constable") == "Keen", \
        "the most able resident is not appointed because he never applied -- only applicants are considered"


# ------------------------------------------------------ G-word-of-mouth
def test_word_of_mouth_spreads_the_opening():
    w = _recognized_council()
    w.add_resident("Insider", competence=0.5, loyalty=0.5, want_work=0.0, reservation=0.9)  # hears, won't apply
    w.add_resident("Friend", competence=0.7, loyalty=0.6, want_work=0.9, reservation=0.2)   # only hears via Insider
    w.knows("Insider", "Friend")
    w.decree_role("clerk"); w.advertise("clerk")
    assert "Friend" in w.aware("clerk"), "awareness spread from Insider to Friend by word of mouth"
    assert w.holder_of("clerk") == "Friend", "Friend applied and got the post"


# ------------------------------------------------------ G-direct-ask
def test_the_creator_can_directly_ask_a_person():
    w = _recognized_council()
    w.add_resident("Chosen", competence=0.8, loyalty=0.7, want_work=0.6, reservation=0.2)
    w.add_resident("Other", competence=0.99, loyalty=0.99, want_work=0.9, reservation=0.1)  # never asked
    w.decree_role("beadle")
    w.ask("Chosen", "beadle")                     # a direct ask, no public advert
    assert w.aware("beadle") == ["Chosen"], "only the asked person becomes aware"
    assert w.holder_of("beadle") == "Chosen", "the asked person accepts (applies) and is appointed"


# ------------------------------------------------------ G-selection-is-a-decision
def test_the_selection_among_applicants_is_a_decision():
    skilled, loyal = dict(competence=0.9, loyalty=0.5, want_work=0.9, reservation=0.2), \
                     dict(competence=0.4, loyalty=0.95, want_work=0.9, reservation=0.2)
    merit = _recognized_council(w_competence=1.0, w_loyalty=0.2)
    merit.add_resident("Skilled", **skilled); merit.add_resident("Loyal", **loyal)
    merit.decree_role("constable"); merit.advertise("constable")
    assert merit.holder_of("constable") == "Skilled", "a merit council selects the able applicant"
    cronies = _recognized_council(w_competence=0.2, w_loyalty=1.0)
    cronies.add_resident("Skilled", **skilled); cronies.add_resident("Loyal", **loyal)
    cronies.decree_role("constable"); cronies.advertise("constable")
    assert cronies.holder_of("constable") == "Loyal", "a loyalty-prizing council selects the loyal applicant"


# ------------------------------------------------------ G-delegated-authority
def test_the_holders_authority_is_the_councils_delegated():
    w = _recognized_council()
    w.add_resident("Con", competence=0.8, loyalty=0.7, want_work=0.9, reservation=0.2)
    w.decree_role("constable"); w.advertise("constable")
    assert w.delegated_authority("Con") == 3.0, "the constable's authority IS the council's (3 recognizers)"
    for r in ("V1", "V2", "V3"):
        w.unrecognize_council(r)
    assert w.delegated_authority("Con") == 0.0, "when the council loses recognition, the delegated authority evaporates"


# ------------------------------------------------------ G-vacancy-and-succession (headline)
def test_the_office_outlives_its_holder_and_a_successor_is_found():
    w = _recognized_council()
    w.add_resident("Alfred", competence=0.9, loyalty=0.6, want_work=0.9, reservation=0.2)
    w.decree_role("constable"); w.advertise("constable")
    assert w.holder_of("constable") == "Alfred"
    w.kill("Alfred")                              # falls down a well; no one else has applied
    assert not w.is_filled("constable") and w.holder_of("constable") is None, \
        "the office is vacated -- it outlives its holder, and nobody is magically installed"
    # a new job-seeker appears and hears the standing opening -> the office is filled again
    w.add_resident("Successor", competence=0.85, loyalty=0.6, want_work=0.9, reservation=0.2)
    w.run()
    assert w.holder_of("constable") == "Successor", "a successor is found the same way (hear -> apply -> select)"


# ------------------------------------------------------ G-advertise-via-noticeboard (headline)
def test_a_job_is_advertised_by_posting_a_note_on_the_square_board():
    w = _recognized_council()
    w.add_resident("Alfred", competence=0.9, loyalty=0.6, want_work=0.9, reservation=0.2)
    w.add_resident("Homebody", competence=0.99, loyalty=0.9, want_work=0.9, reservation=0.1)  # never visits
    w.decree_role("constable")
    w.advertise_on_board("constable", poster="Beadle")     # pin a job-note on the square's board
    assert "Alfred" not in w.aware("constable"), "posting alone does not reach those who are not at the square"
    w.go_to_square("Alfred")                                # Alfred visits and reads the board
    assert "Alfred" in w.aware("constable"), "he reads the posted job-note -> aware of the opening"
    assert w.holder_of("constable") == "Alfred", "he applies and is appointed"
    assert "Homebody" not in w.aware("constable"), \
        "someone who never visits the square never learns of the job (the board is local)"


# ------------------------------------------------------ G-no-python-decision (source audit)
def test_no_python_decides_offices():
    src = open(os.path.join(_ROOT, "worlds", "bigville_office_world.py")).read()
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "_match", "_apply"):
        assert forbidden not in src, f"adapter must not run a rule engine: {forbidden}"
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_office.json")))
    names = {r["name"] for r in seed["rules"]}
    assert {"of_council_create", "of_owner_create", "of_hear_notice", "of_word_of_mouth",
            "of_apply_decide", "of_select", "of_install", "of_delegate", "of_vacate"} <= names, names
    # applying is a collapse; selection is over APPLICANTS (in-edges), not a hidden pool
    ap = json.dumps([r for r in seed["rules"] if r["name"] == "of_apply_decide"][0])
    assert "ApplyStance" in ap and "Argmax" in ap, "applying is a decision collapse"
    sel = [r for r in seed["rules"] if r["name"] == "of_select"][0]
    assert "applies_to" in json.dumps(sel), "selection is among those who APPLIED"
