"""ACTOR GOALS -- ABDUCTIVE EXPLANATION of a THIRD-PARTY actor's behaviour
(domains/actor_goals.py + seeds/actor_goals.json). Mirrors
tests/test_media_analysis_migrated.py's discipline exactly.

WHAT THIS SLICE DOES, for a THIRD-PARTY actor described in text (never the
conversation partner -- that is domains/interlocutor_model.py's business,
untouched here):

  1. AGENCY -- author (subject/agent of the action) vs recipient (patient/
     beneficiary), read from the predication's own structure + a teachable
     verb-class codebook (RecipientVerb).
  2. SURFACE GOAL -- a teachable ActionGoal codebook (fund/sponsor/donate/
     back/finance -> 'support') abducts the canonical goal an action serves.
  3. THE LAYERED-GOAL SIGNAL -- a teachable ActorProfile codebook (actor's
     declared core interest vs what it opposes) flags, never asserts, that
     an actor's action ALSO plausibly serves a higher-level goal conflicting
     with the action's own object domain.

SEMANTICS, load-bearing for every assertion below: `serves_conflicting_meta_
goal` is NOT "the surface action is fake" and never implicates the funded
object or its recipients/beneficiaries -- many things are true at once (a
funded renewable-energy project can be entirely genuine AND its funder can
hold a conflicting higher-level goal). The flag is scoped strictly to the
FUNDER's own ActorGoal node. A single act only makes this a DEFEASIBLE
POSSIBILITY (revisable:1.0) -- the temporal/cross-action PATTERN (and named
strategic schemas like Trojan Horse / Guilt-Based Action) is an explicit
LATER slice, not attempted here.

THE COMPOUND-ACTOR PARSE RESIDUAL (measured via probe, documented in
domains/actor_goals.py's module docstring): reading_collapse's bare active-
voice S-V-O fallback mis-splits a two-word premodified actor compound whose
head noun has a rare WordNet verb sense ('company') -- "The oil company
funded X." grounds as `['company', 'oil', 'funded_...']`, not `['fund',
'oil_company', ...]`. This is a PRE-EXISTING reading-layer limitation, out
of this slice's scope to fix (reading_collapse.py's marker-selection ladder
is not this slice's file). The tests below route a COMPOUND actor through
the SAME passive-with-by-phrase construction domains/media_analysis.py
already exploits for exactly this reason (a by-phrase agent is read off the
clause's own marker sequence, not the buggy bare-SVO fallback); a SINGLE-
WORD actor needs no such routing (the bare-SVO fallback never mis-fires on
a one-word actor -- verified directly).

Every test uses a FUNCTION-SCOPED fresh agent (isolation-tested per the
project's own documented lesson -- a shared-agent run can mask a
discriminative-null failure via a dedup key collision across sentences).

Run: PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 python3 -m pytest \
    tests/test_actor_goals_migrated.py -p no:randomly -q
"""
from __future__ import annotations

import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core            # noqa: E402
from domains import dictionary_lexicon as dl          # noqa: E402
from domains import reading_collapse as rc            # noqa: E402
from domains import actor_goals as ag                 # noqa: E402


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


@pytest.fixture()
def agent():
    # function-scoped: each test gets a FRESH graph -- ActorAction/ActorGoal
    # dedup keys can never leak across tests.
    dl.warm_wordnet("en")
    s, node = boot_core()
    return _Agent(s, node)


def _goals(a, agency=None):
    return ag.held_actor_goals(a, agency=agency)


# --------------------------------------------------------------------------- #
#  HEADLINE COVER -- the flagship layered-goal case.
# --------------------------------------------------------------------------- #
def test_headline_oil_company_funds_renewables(agent):
    # passive-with-by-phrase routes around the documented compound-actor
    # parse residual (see module docstring) while conveying the SAME
    # proposition as "The oil company funded a renewable energy project."
    r = rc.read_clause(agent, "A renewable energy project was funded by the oil company.", write=True)
    assert r["predications"] == [["fund", "_", "renewable_energy_project"]], r

    goals = _goals(agent, agency="author")
    assert len(goals) == 1, goals
    g = goals[0]
    assert g["actor"] == "oil_company", g
    assert g["agency"] == "author", g
    assert g["surface_goal"] == "support", g
    assert g["object"] == "renewable_energy", g
    assert g["serves_conflicting_meta_goal"] == 1.0, g
    assert g["meta_goal_core_interest"] == "fossil_fuels", g
    assert g["meta_goal_opposes"] == "renewable_energy", g
    assert g["revisable"] == 1.0, g
    # DETECT-NOT-FILL: the basis names the CONFLICT, never a fabricated
    # hidden-goal value.
    assert "fossil_fuels" in g["basis"] and "renewable_energy" in g["basis"], g
    assert "goal layer" in g["basis"], g
    # MECHANISM-AGNOSTIC: deception (deliberate) and an introspection gap
    # (sincere-but-self-opaque, Nisbett-Wilson confabulation) are NOT
    # distinguished by a single act. "deliberate" may appear only inside the
    # explicitly-hedged "(deliberate vs sincere-but-self-opaque) UNDETERMINED"
    # framing -- never as an unhedged assertion that the actor deliberately
    # concealed anything.
    assert g["mechanism"] == "undetermined", g
    assert "UNDETERMINED" in g["basis"], g
    assert "(deliberate vs sincere-but-self-opaque)" in g["basis"], g
    for bad in ("strategic", "deceptive", "insincere", "cover-up", "conscious"):
        assert bad not in g["basis"].lower(), g


# --------------------------------------------------------------------------- #
#  NO-COVER CONTROL -- the discrimination: cover must NOT fire for every
#  funder, only for a genuine actor-profile conflict.
# --------------------------------------------------------------------------- #
def test_no_cover_control_charity_funds_renewables(agent):
    # single-word actor -- the plain active bare-SVO path parses this
    # cleanly (verified: no compound-actor residual for a one-word actor).
    r = rc.read_clause(agent, "The charity funded a renewable energy project.", write=True)
    assert r["predications"] == [["funded", "charity", "renewable_energy_project"]], r

    goals = _goals(agent, agency="author")
    assert len(goals) == 1, goals
    g = goals[0]
    assert g["actor"] == "charity", g
    assert g["surface_goal"] == "support", g
    assert g["object"] == "renewable_energy", g
    # SAME object domain as the oil-company headline -- the discriminator is
    # the ACTOR's profile, not the object.
    assert g["serves_conflicting_meta_goal"] in (0.0, None, False), g


# --------------------------------------------------------------------------- #
#  ACTIVE VOICE, DIRECTLY -- the compound-actor parse residual named above is
#  FIXED at the reading layer (domains/reading_collapse.py's bare-S-V-O
#  fallback now routes its verb PICK through `_find_main_verb`, the SAME
#  held-signal main-verb ladder the event-clause path already trusts, guarded
#  so no clause the crude scan already read correctly is ever regressed --
#  see that module's own comment for the full audit). "The oil company
#  funded a renewable energy project." no longer needs the passive-with-by-
#  phrase workaround above; this module's UNCHANGED rules (mint_actor_goal /
#  flag_conflicting_meta_goal, seeds/actor_goals.json) fire straight off the
#  now-correct active-voice predication.
# --------------------------------------------------------------------------- #
def test_headline_active_voice_oil_company_funds(agent):
    r = rc.read_clause(agent, "The oil company funded a renewable energy project.", write=True)
    assert r["predications"] == [["funded", "oil_company", "renewable_energy_project"]], r

    goals = _goals(agent, agency="author")
    assert len(goals) == 1, goals
    g = goals[0]
    assert g["actor"] == "oil_company", g
    assert g["agency"] == "author", g
    assert g["surface_goal"] == "support", g
    assert g["object"] == "renewable_energy", g
    assert g["serves_conflicting_meta_goal"] == 1.0, g
    assert g["meta_goal_core_interest"] == "fossil_fuels", g
    assert g["meta_goal_opposes"] == "renewable_energy", g
    assert g["revisable"] == 1.0, g


def test_no_cover_control_active_voice_charity_funds(agent):
    # Control, isolation-tested in its own fresh agent: the SAME active-voice
    # construction, a non-conflicting actor -- cover must not fire.
    r = rc.read_clause(agent, "The charity funded a renewable energy project.", write=True)
    assert r["predications"] == [["funded", "charity", "renewable_energy_project"]], r

    goals = _goals(agent, agency="author")
    assert len(goals) == 1, goals
    g = goals[0]
    assert g["actor"] == "charity", g
    assert g["surface_goal"] == "support", g
    assert g["object"] == "renewable_energy", g
    assert g["serves_conflicting_meta_goal"] in (0.0, None, False), g


# --------------------------------------------------------------------------- #
#  SECOND COVER -- a distinct actor/profile pair, proving this isn't
#  hardcoded to the oil/renewables example.
# --------------------------------------------------------------------------- #
def test_second_cover_cigarette_company_funds_quit_smoking(agent):
    r = rc.read_clause(
        agent, "A quit-smoking program was funded by the cigarette company.", write=True)
    assert r["predications"] == [["fund", "_", "quit-smoking_program"]], r

    goals = _goals(agent, agency="author")
    assert len(goals) == 1, goals
    g = goals[0]
    assert g["actor"] == "cigarette_company", g
    assert g["object"] == "quit-smoking", g
    assert g["serves_conflicting_meta_goal"] == 1.0, g
    assert g["meta_goal_core_interest"] == "smoking", g
    assert g["meta_goal_opposes"] == "quit-smoking", g


# --------------------------------------------------------------------------- #
#  AGENCY RECIPIENT -- the actor is patient/beneficiary, not author; no
#  authored surface goal (honest).
# --------------------------------------------------------------------------- #
def test_agency_recipient_company_received_a_grant(agent):
    r = rc.read_clause(agent, "The company received a grant.", write=True)
    assert r["predications"] == [["received", "company", "grant"]], r

    aa = [agent.s.node(n)["attrs"] for n in agent.s.nodes("ActorAction")]
    assert len(aa) == 1, aa
    assert aa[0]["actor"] == "company", aa
    assert aa[0]["verb"] == "receive", aa   # participle-lemma normalised
    assert aa[0]["actor_role"] == "agent", aa   # RAW structural fact (grammatical subject)

    author_goals = _goals(agent, agency="author")
    assert author_goals == [], author_goals   # no authored goal minted for 'receive'

    recip_goals = _goals(agent, agency="recipient")
    assert len(recip_goals) == 1, recip_goals
    g = recip_goals[0]
    assert g["actor"] == "company", g
    assert g["agency"] == "recipient", g
    assert g["surface_goal"] == "", g
    assert g["serves_conflicting_meta_goal"] in (0.0, None, False), g


# --------------------------------------------------------------------------- #
#  DISCRIMINATIVE NULL -- active voice, non-actor-bearing, non-fund verb:
#  nothing fabricated.
# --------------------------------------------------------------------------- #
def test_null_unrelated_verb_mints_no_layered_goal(agent):
    r = rc.read_clause(agent, "The dog chased a ball.", write=True)
    assert r["predications"] == [["chased", "dog", "ball"]], r

    aa = [agent.s.node(n)["attrs"] for n in agent.s.nodes("ActorAction")]
    assert len(aa) == 1, aa   # ActorAction is written UNCONDITIONALLY...
    assert _goals(agent) == []   # ...but no ActorGoal mints -- 'chase' matches no codebook row.


# --------------------------------------------------------------------------- #
#  SOURCE AUDIT -- no regex; the decision lives in the seed rules.
# --------------------------------------------------------------------------- #
def test_source_audit_no_regex_and_decision_lives_in_the_seed():
    mod_path = os.path.join(ROOT, "domains", "actor_goals.py")
    src = open(mod_path).read()
    lines = [ln.strip() for ln in src.splitlines()]
    assert "import re" not in lines and "import re as _re" not in lines
    assert "re.match" not in src and "re.search" not in src and "re.sub" not in src
    # Python never mints ActorGoal directly, and never tests ActionGoal/
    # RecipientVerb/ActorProfile membership -- only the mechanical
    # ActorAction fact. The join/mint/dedup/flag decision is the seed's.
    assert 'add_node("ActorGoal"' not in src
    assert '"ActorGoal", {' not in src
    for ln in lines:
        assert not (" in action_goal" in ln.lower() and ln.startswith(("if ", "elif "))), ln
        assert not (" in recipient_verb" in ln.lower() and ln.startswith(("if ", "elif "))), ln
        assert not (" in actor_profile" in ln.lower() and ln.startswith(("if ", "elif "))), ln


def test_source_audit_rules_carry_the_joins_and_the_guards():
    seed_path = os.path.join(ROOT, "seeds", "actor_goals.json")
    seed = json.load(open(seed_path))
    rules = {r["name"]: r for r in seed["rules"]}

    mag = rules["mint_actor_goal"]
    match_edges = {(m[0], m[1]) for m in mag["match"]}
    assert ("agent", "has_actor_action") in match_edges, mag["match"]
    assert ("agent", "has_action_goal") in match_edges, mag["match"]
    where_text = json.dumps(mag["where"])
    assert '"key": "verb"' in where_text

    magr = rules["mint_actor_goal_recipient"]
    match_edges_r = {(m[0], m[1]) for m in magr["match"]}
    assert ("agent", "has_recipient_verb") in match_edges_r, magr["match"]

    fcmg = rules["flag_conflicting_meta_goal"]
    match_edges_f = {(m[0], m[1]) for m in fcmg["match"]}
    assert ("agent", "has_actor_goal") in match_edges_f, fcmg["match"]
    assert ("agent", "has_actor_profile") in match_edges_f, fcmg["match"]
    where_text_f = json.dumps(fcmg["where"])
    assert '"key": "opposes"' in where_text_f
    assert '"key": "object"' in where_text_f
    # the effect never writes anything but the ActorGoal node's own attrs
    # (the funder's own layer) -- no add_node/add_edge touching any other
    # node type, in particular never anything that reads as touching the
    # object/beneficiary.
    for eff in fcmg["effects"]:
        assert eff[0] == "set_attr" and eff[1] == "g", eff


# --------------------------------------------------------------------------- #
#  TEACH-EXTENDS -- teach() grows ActorProfile coverage; no code change.
#  coal_company is deliberately NOT pre-seeded (see seeds/actor_goals.json's
#  description) so this test proves the codebook is genuinely teachable.
# --------------------------------------------------------------------------- #
def test_agent_teaches_new_actor_profile(agent, tmp_path):
    from domains.teach import teach

    r0 = rc.read_clause(agent, "A clean energy startup was funded by the coal company.", write=True)
    assert r0["predications"] == [["fund", "_", "clean_energy_startup"]], r0

    pre = _goals(agent, agency="author")
    assert len(pre) == 1, pre
    assert pre[0]["actor"] == "coal_company", pre
    assert pre[0]["object"] == "clean_energy", pre
    assert pre[0]["serves_conflicting_meta_goal"] in (0.0, None, False), pre   # not yet flagged

    res = teach(agent, "ActorProfile",
                {"actor": "coal_company", "core_interest": "coal", "opposes": "clean_energy"},
                category="taught_actor_profiles", seeds_dir=tmp_path)
    assert res["saved"] is True, res

    # NO re-read needed -- the taught row is new graph data; reconcile-wire
    # + re-run the agent's OWN standing rules against it.
    ag.ensure_actor_goals_seed(agent)
    agent.inner.run_rules()

    post = _goals(agent, agency="author")
    assert len(post) == 1, post   # same ActorGoal node, now flagged
    assert post[0]["serves_conflicting_meta_goal"] == 1.0, post
    assert post[0]["meta_goal_core_interest"] == "coal", post
    assert post[0]["meta_goal_opposes"] == "clean_energy", post


# --------------------------------------------------------------------------- #
#  BYTE PARITY -- this module changes NO existing predication/decompose/
#  read_clause field (see tests/test_reading_parity_migrated.py, run
#  separately as the parity gate). Sanity-checked here too.
# --------------------------------------------------------------------------- #
def test_byte_parity_write_false_path_untouched(agent):
    r = rc.read_clause(agent, "The oil company funded a renewable energy project.", write=False)
    assert agent.s.nodes("ActorAction") == []
    assert agent.s.nodes("ActorGoal") == []
