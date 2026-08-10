"""bigville R20 (block 268000) -- COUNCIL MEETINGS & the NOTICEBOARD: two-tier
governance + the public written record.

Governance runs on SCHEDULED two-tier meetings + a public written record, all
graph-native: a PUBLIC session (the mayor's ADDRESS, perceived by attending
townsfolk) then a PRIVATE session (council-only, OCCLUDED -- R19 observe-vs-hear)
where the collective decision_value over the council backing-graph sets the
outcome. The public-discussion content does or does not move the private decision
-- a captured council (John's) shows ~0 correlation (theatre / structure), a
responsive one +1 (agency); the correlation is READ OFF the graph (a measurement).
The mayor's public ADDRESS vs the private DECISION is the 234 stated!=held atom at
INSTITUTIONAL scale. The decision is WRITTEN by ONE council member (a biased clerk
DISTORTS the minutes) and POSTED on the noticeboard; a resident LEARNS it only via
R1 access + R18 literacy.

No governance decision lives in Python -- every convene / address / vote / decision
/ occlusion / gap / minutes / promulgation / reading is a seed rule
(bigville_council_gov / bigville_council_board). The adapter arms one meeting,
wires edges, ticks and reads (source-audit at the foot). ZERO new Rust. The seeds
are self_load_only. Gates mirror BIGVILLE_COUNCIL_PREREG.md.
"""
from __future__ import annotations

import json
import os
import re
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_council_world import BigvilleCouncilWorld    # noqa: E402


def _council(captured, *, premium=50, base=10):
    # base_position == the mayor's benevolent stated_position (10): the honest
    # baseline. malice adds the self_serving_premium on top -> the 234 gap. So
    # ablating malice collapses the held decision back onto the address (gap 0).
    w = BigvilleCouncilWorld()
    w.add_council(captured=captured)
    w.add_mayor("mayor", stated_position=10)
    for nm in ("a", "b", "c"):
        w.add_member(nm, base_position=base, self_serving_premium=premium,
                     is_clerk=(nm == "a"), clerk_bias=0.0)
    return w


def _pearson(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx == 0 or syy == 0:
        return 0.0
    return sxy / (sxx ** 0.5 * syy ** 0.5)


# ================================================== G-two-tier-meeting
def test_public_session_perceived_private_occluded():
    """A scheduled meeting convenes on the R3 cadence, fires the mayor's public
    ADDRESS (attendees perceive it), then the private DECISION (attendees do NOT
    perceive it while the private tier is on -- the room where it happened)."""
    w = _council(captured=0)
    w.add_resident("t", literate=1, at_hall=1)
    r = w.convene(now_day=6, cadence=3, public_demand=25, private_on=1, malice_on=0)
    assert r["convened"] == 1, "on-cadence meeting convenes"
    assert r["public_address"] == 10.0, "the mayor's benevolent address is public"
    # HEADLINE of the tier split: the town HEARS the address, not the decision.
    assert w.heard_address_of("t") == 1 and w.knows_address_of("t") == 10.0, \
        "attendee perceives the PUBLIC address"
    assert w.heard_decision_of("t") == 0, \
        "attendee does NOT perceive the PRIVATE decision (occluded room)"
    w.close()


def test_off_cadence_no_meeting_control():
    """CONTROL (R3 scheduling is load-bearing): off the cadence the meeting does not
    convene -- no address, no decision."""
    w = _council(captured=0)
    w.add_resident("t", literate=1, at_hall=1)
    r = w.convene(now_day=7, cadence=3, public_demand=25)   # 7 % 3 != 0
    assert r["convened"] == 0, "off-cadence -> no meeting"
    assert w.heard_address_of("t") == 0, "nothing is perceived"
    w.close()


def test_ablate_private_tier_decision_becomes_public():
    """ABLATION (transparency counterfactual): drop the private tier (private_on=0)
    -> the town now perceives the held decision too (the deliberation is public)."""
    w = _council(captured=1)
    w.add_resident("t", literate=1, at_hall=1)
    r = w.convene(now_day=0, cadence=1, public_demand=15, private_on=0, malice_on=1)
    assert w.heard_decision_of("t") == 1, "private ablated -> town hears the decision"
    assert w.knows_decision_of("t") == r["held_decision"], "and it is the true decision"
    # and with the private tier ON, the SAME council's decision stays occluded
    w2 = _council(captured=1)
    w2.add_resident("t", literate=1, at_hall=1)
    w2.convene(now_day=0, cadence=1, public_demand=15, private_on=1, malice_on=1)
    assert w2.heard_decision_of("t") == 0, "private on -> occluded (the contrast)"
    w.close(); w2.close()


def test_decision_is_collective_over_backing_graph():
    """The private decision is the collective decision_value = the MEAN vote over the
    council backing-graph (has_member), not one member's fiat. Every captured member
    votes base+premium; the decision is their mean."""
    w = _council(captured=1, base=10, premium=50)
    r = w.convene(now_day=0, cadence=1, public_demand=15, malice_on=1)
    assert w.vote_of("a") == 60.0 and w.vote_of("b") == 60.0 and w.vote_of("c") == 60.0, \
        "each captured member votes base(10)+malice*premium(50)=60"
    assert r["held_decision"] == 60.0, "collective decision = mean vote over has_member"
    w.close()


# =============================== G-public-influence-or-theatre (HEADLINE, MEASURED)
def test_responsive_council_correlates_captured_does_not():
    """HEADLINE (agency vs structure, MEASURED). Correlate public-discussion content
    (public_demand) with the private decision across meetings. A RESPONSIVE council
    tracks the demand -> r ~ +1 (public voice reaches the lever = AGENCY); a CAPTURED
    council (John's) ignores it -> the decision never moves -> r ~ 0 (ritual over a
    pre-made decision = STRUCTURE). The measurement, not an assertion."""
    demands = [10, 15, 20, 25, 30, 35]
    resp, capt = [], []
    for D in demands:
        wr = _council(captured=0)
        resp.append(wr.convene(now_day=0, cadence=1, public_demand=D,
                               malice_on=0)["held_decision"])
        wr.close()
        wc = _council(captured=1)
        capt.append(wc.convene(now_day=0, cadence=1, public_demand=D,
                               malice_on=1)["held_decision"])
        wc.close()
    r_resp, r_capt = _pearson(demands, resp), _pearson(demands, capt)
    assert r_resp > 0.99, ("responsive should track demand (agency)", resp, r_resp)
    assert abs(r_capt) < 0.01, ("captured decision is fixed (theatre)", capt, r_capt)
    # glass-box: the responsive decision IS the demand; the captured one is constant.
    assert resp == demands, ("responsive decision == public demand", resp)
    assert len(set(capt)) == 1, ("captured decision never moves", capt)


# ==================================================== G-institutional-stated!=held
def test_institutional_stated_ne_held_and_malice_ablation():
    """The mayor's public ADDRESS vs the private DECISION is the 234 atom at
    INSTITUTIONAL scale: a benevolent address over a self-serving decision is a
    readable gap. ABLATE John's malice (malice_on=0) -> the members' held position
    collapses to the base = the address -> the gap CLOSES."""
    w = _council(captured=1)
    r = w.convene(now_day=0, cadence=1, public_demand=15, malice_on=1)
    assert r["public_address"] == 10.0, "benevolent public face"
    assert r["held_decision"] == 60.0, "self-serving private decision (base+premium)"
    assert r["stated_held_gap"] == 50.0, "the institutional stated!=held gap is readable"
    w.close()
    wf = _council(captured=1)
    rf = wf.convene(now_day=0, cadence=1, public_demand=15, malice_on=0)
    assert rf["stated_held_gap"] == 0.0, "ablate malice -> address==decision -> gap closes"
    assert rf["public_address"] == rf["held_decision"], "no gap without malice"
    wf.close()


# ==================================================== G-noticeboard-promulgates
def _board_world(*, clerk_bias=0, gate=1):
    w = BigvilleCouncilWorld()
    w.add_council(captured=1)
    w.add_mayor("mayor", stated_position=10)
    w.add_member("clerk", base_position=40, self_serving_premium=20,
                 is_clerk=1, clerk_bias=clerk_bias)
    w.add_member("b", base_position=40, self_serving_premium=20)
    w.add_resident("lit_near", literate=1, at_hall=1)
    w.add_resident("ill_near", literate=0, at_hall=1)
    w.add_resident("lit_far", literate=1, at_hall=0)
    w.convene(now_day=0, cadence=1, public_demand=15, malice_on=1)
    w.post_notice(literacy_gate_on=gate)
    return w


def test_noticeboard_promulgation_gated_by_literacy_and_access():
    """The decision is POSTED (officially known) but LEARNING it is gated by R1
    access + R18 literacy: only the literate resident AT the hall learns it; the
    illiterate-at-hall and the literate-but-DISTANT resident do NOT -- the law is
    officially known yet personally UNKNOWN (unequal ignorance-of-the-law)."""
    w = _board_world(clerk_bias=0, gate=1)
    assert w.officially_known() == 1, "the notice is officially promulgated"
    assert w.knows_law_flag_of("lit_near") == 1, "literate + at hall -> learns the law"
    assert w.knows_law_flag_of("ill_near") == 0, "illiterate at hall -> does NOT learn"
    assert w.knows_law_flag_of("lit_far") == 0, "literate but distant -> does NOT learn"
    # the unequal state: officially known (globally) yet personally unknown (locally)
    assert w.knows_law_of("ill_near") == 0.0 and w.knows_law_of("lit_far") == 0.0
    w.close()


def test_biased_clerk_distorts_the_record():
    """The minutes are WRITTEN by ONE council member -- an owned act. A BIASED clerk
    DISTORTS the record: recorded != the true held_decision (institutional 234). The
    faithful clerk records it truthfully."""
    biased = _board_world(clerk_bias=7, gate=1)
    dec = biased.held_decision()
    assert biased.recorded() == dec + 7.0, "biased clerk: recorded = decision + bias"
    assert biased.knows_law_of("lit_near") == dec + 7.0, \
        "the reader learns the DISTORTED record, not the true decision"
    biased.close()
    faithful = _board_world(clerk_bias=0, gate=1)
    assert faithful.recorded() == faithful.held_decision(), "faithful clerk: no distortion"
    faithful.close()


def test_ablate_literacy_gate_uniform_knowledge():
    """ABLATE the literacy gating (literacy_gate_on=0) -> the illiterate resident AT
    the hall now learns the law too (uniform knowledge among those with access) --
    literacy was load-bearing for the inequity."""
    w = _board_world(clerk_bias=0, gate=0)
    assert w.knows_law_flag_of("ill_near") == 1, "gate ablated -> illiterate learns it"
    assert w.knows_law_flag_of("lit_near") == 1, "and the literate still does"
    # access is STILL required: the distant resident learns nothing even ungated
    assert w.knows_law_flag_of("lit_far") == 0, "R1 access still binds (distant unknown)"
    w.close()


# ==================================================================== discipline
def _strip_py(src: str) -> str:
    src = re.sub(r'"""[\s\S]*?"""', "", src)
    src = re.sub(r"'''[\s\S]*?'''", "", src)
    src = re.sub(r"#.*", "", src)
    src = re.sub(r'"[^"\n]*"', '""', src)
    src = re.sub(r"'[^'\n]*'", "''", src)
    return src


def test_no_python_governance_decision_source_audit():
    """Source-audit: every governance DECISION is a seed rule, not Python. The
    adapter arms one meeting, wires edges, ticks and reads -- it never COMPUTES a
    vote / decision / gap / minutes / reading outcome in Python."""
    world_src = open(os.path.join(_ROOT, "worlds", "bigville_council_world.py")).read()
    world_src = re.sub(r"MEMBER_DEFAULTS\s*=\s*dict\([\s\S]*?\)\n", "", world_src, count=1)
    world_src = re.sub(r"RESIDENT_DEFAULTS\s*=\s*dict\([\s\S]*?\)\n", "", world_src, count=1)
    code = _strip_py(world_src)
    for banned in ("graph_rewrite", "gr.run", "gr._match", "gr._apply", "make_rule"):
        assert banned not in code, "adapter must not run/author the Python rule engine"
    # the decision parameters live in rule `where`s, never in an adapter branch
    for param in ("captured", "malice_on", "self_serving_premium", "clerk_bias",
                  "literacy_gate_on", "literate", "at_hall", "public_demand"):
        assert ("if " + param) not in code, \
            "decision parameter %s must live in a rule, not an adapter branch" % param
    gov = json.load(open(os.path.join(_ROOT, "seeds", "bigville_council_gov.json")))
    board = json.load(open(os.path.join(_ROOT, "seeds", "bigville_council_board.json")))
    rule_names = {r["name"] for r in gov["rules"]} | {r["name"] for r in board["rules"]}
    assert rule_names == {
        "cm_convene", "cm_public_address", "cm_attendee_hears_address",
        "cm_member_vote", "cm_private_decision", "cm_attendee_hears_decision",
        "cm_institutional_gap", "cm_clerk_writes", "cm_post_notice",
        "cm_resident_reads",
    }, "the ten governance decisions are RULES"


def test_seeds_self_load_only_and_no_new_rust():
    """Both seeds are self_load_only (loaded ONLY by this adapter -> cannot affect
    any other suite) and compose EXISTING DSL Terms only (no new Rust). Engine
    provenance asserts the INVARIANT (source_match in {own, shared}) -- never a
    pinned md5 (lesson 7b)."""
    gov = json.load(open(os.path.join(_ROOT, "seeds", "bigville_council_gov.json")))
    board = json.load(open(os.path.join(_ROOT, "seeds", "bigville_council_board.json")))
    for seed in (gov, board):
        assert seed.get("self_load_only") is True, "%s must be self_load_only" % seed["id"]
        assert seed.get("depends_on") == [], "%s stands alone" % seed["id"]
    from domains.engine_provenance import engine_provenance
    p = engine_provenance()
    assert p["source_match"] in ("own", "shared"), p
    used = set()
    for d in (gov, board):
        used |= set(re.findall(r'"type":\s*"([A-Z][A-Za-z]+)"', json.dumps(d)))
    known = {"Attr", "Var", "Lit", "Plus", "Minus", "Times", "IDiv", "Mod", "Abs",
             "Sum", "Count", "Neighbours", "Eq", "Lt", "Lte", "Gte", "Gt", "And",
             "Or", "Not", "IfThenElse", "Argmin", "Argmax", "Exists"}
    assert used <= known, f"unexpected Term(s) -- new Rust? {used - known}"
