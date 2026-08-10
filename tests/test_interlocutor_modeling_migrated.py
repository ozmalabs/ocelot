"""test_interlocutor_modeling_migrated — INTERLOCUTOR-AS-MODELED-PARTICIPANT
(Wave 2026-07-11): "does it treat the chat like an actual discussion where it
models the interlocutor? because it can do that, and should." A live,
per-turn Party model (domains/interlocutor_model.py) already accumulated
register/style/mood/name/known-words; this wave wires the MENTAL-STATE legs
that were built-and-tested but never called from `converse()`:

  1. TOLD-STATUS (the Gricean quantity gate): `converse()` points the agent at
     the turn's addressee (`set_addressee`) and every SUBSTANTIVE reply grows
     that specific party's `believed_concepts` (`_finish_turn_reply` /
     `_grow_believed_concepts`, shared with `_communicative_action`'s
     existing structured-goal path) — per-party, never bleeding across
     parties.

  2. GOAL OWNERSHIP: every conversational Goal mint (conversation_action,
     question_driver, reading_drive) gets a `wanted_by` edge to the active
     Party (`interlocutor_model.wanted_by`) — a mint-time provenance fact.

  3. TWO-LEVEL ATTITUDE TRACKING (redesigned mid-wave, twice, per explicit
     course correction — "unreliable narrator... most centroid introspection
     is surface level at best" + "not just a track record - by shape
     matching and priors"): LEVEL 1 is an immutable `Assertion` node ("the
     party SAID this verbatim sentence at this turn"); LEVEL 2 is the reused
     `character_tom` belief-world/goal grounding, TAGGED with
     `source='self_report'` and a `confidence` derived from PRIORS-BY-SHAPE-
     MATCHING (a small `InterlocutorShape` codebook, `interlocutor_model.
     decode_shape`) blended n-weighted with the party's own individual track
     record (`effective_reliability`) — structural evidence (the creator-
     origin rule, `seeds/interlocutor_trust.json`) overrides outright. A
     correction later REVISES Level 2's confidence; Level 1 (what was
     literally said) is never touched.

  4. ONE consuming rule for the Gricean maxim vocabulary
     (`seeds/conversation_grice.json::reply_topic_repeat_known` — the
     maxim of QUANTITY): a repeat-topic turn is answered "As I mentioned,
     ..." instead of flatly restating; an explicit re-ask (an elaboration
     cue) is unaffected.

  5. THE USER-FACING PROOF: `reflective_faculty._run_interlocutor_model`
     ("what do you know about me?") renders who/what-they-asked/said-vs-
     modeled/the reliability calibration — all four strata visible and
     distinct.

A genuine pre-existing bug was found and fixed en route:
`character_tom._find_attitude_marker` excluded any word ALREADY classified
in the shared marker lexicon — including the ATTITUDE class's OWN seed forms
(believe/think/know/want/hope/fear/wish/doubt), so "I think X" (a BASE-FORM
first-person self-report, this wave's entire subject matter) never fired;
only a conjugated third-person form ("Sally thinks X") slipped through by
accident. Fixed to exclude only a DIFFERENT class's word — the 18 pre-
existing tests/test_character_tom.py cases are the regression gate for that
fix, still green (see the broad-bench tail in the wave report).
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

from substrate.world_adapter import WorldAdapter                       # noqa: E402
from substrate.boot_all import load_all_seeds                          # noqa: E402
from domains import interlocutor_model as im                           # noqa: E402
from domains import character_tom as ctom                              # noqa: E402
from domains.reflective_faculty import _ensure_seed_chain, reflect     # noqa: E402

jd = pytest.importorskip("jabberwock_daemon")


def _agent(shadow_read=True):
    a = WorldAdapter(seeds=(), shadow_read=shadow_read)
    load_all_seeds(a)
    return a


def _active_party(a):
    for n in a.s.nodes("Interlocutor"):
        if a.s.node(n)["attrs"].get("active"):
            return n
    return None


# --------------------------------------------------------------------------- #
#  1. TOLD-STATUS — per-party, never bleeding.
# --------------------------------------------------------------------------- #
def test_told_status_grows_believed_concepts_for_this_party_only():
    a = _agent()
    a.converse("Hi, I am Ada.", speech_act="statement")
    a.learn_from_teacher("what is zqxbelt", {
        "answer": "zqxbelt is a made up test concept",
        "learn": [{"phrase": "zqxbelt"}]})
    a.converse("What do you know about zqxbelt?", speech_act="question")
    ada = _active_party(a)
    believed_ada = set(a.s.node(ada)["attrs"].get("believed_concepts") or [])
    assert "zqxbelt" in believed_ada, "a substantive reply must grow THIS party's believed_concepts"

    # a context gap + a style break re-attributes to a SECOND party.
    a.converse("Good morning. I trust this finds you well.",
              speech_act="statement", context={"time_gap": True})
    carl = _active_party(a)
    assert carl != ada, "the discontinuity must re-attribute to a fresh party"
    believed_carl = set(a.s.node(carl)["attrs"].get("believed_concepts") or [])
    assert "zqxbelt" not in believed_carl, "a second party must NOT inherit what the first was told"


def test_honest_floor_reply_is_not_substantive():
    a = _agent()
    a.converse("Hi, I am Dana.", speech_act="statement")
    before = set(a.s.node(_active_party(a))["attrs"].get("believed_concepts") or [])
    a.converse("thanks", speech_act="thanks")
    after = set(a.s.node(_active_party(a))["attrs"].get("believed_concepts") or [])
    assert after == before, "a bare social-act / honest-floor turn must not seed believed_concepts"


# --------------------------------------------------------------------------- #
#  2. GOAL OWNERSHIP.
# --------------------------------------------------------------------------- #
def test_goal_is_wanted_by_the_active_party():
    a = _agent()
    a.converse("Hi, I am Eve.", speech_act="statement")
    eve = _active_party(a)
    a.converse("What do you know about qzxfrance?", speech_act="question")
    goals = [g for g in a.inner.neighbours(a.agent, "has_goal")
             if a.s.node(g)["attrs"].get("kind") == "answer_topic"
             and a.s.node(g)["attrs"].get("concept") == "qzxfrance"]
    assert goals, "the question must mint an answer_topic Goal"
    owners = list(a.inner.neighbours(goals[0], "wanted_by"))
    assert owners == [eve], "the Goal must be wanted_by the party who asked"


def test_requested_by_renders_in_self_improvement_status():
    a = _agent()
    a.converse("Hi, I am Frank.", speech_act="statement")
    frank = _active_party(a)
    import domains.topic_grounding as _tg
    orig = _tg.ground_topic
    _tg.ground_topic = lambda ag, phrase, **kw: None
    try:
        a.converse("What do you know about qzxungroundable?", speech_act="question")
        a.comprehend()
    finally:
        _tg.ground_topic = orig
    sc = None
    for n in a.inner.neighbours(a.agent, "has_self_concern"):
        at = a.s.node(n)["attrs"]
        if at.get("kind") == "knowledge" and at.get("content") == "qzxungroundable":
            sc = n
            break
    assert sc is not None, "the unresolved topic must file a knowledge gap"
    res = jd.promote_self_concern(a, str(sc.value if hasattr(sc, "value") else sc))
    assert res.get("ok")
    standing = None
    for n in a.s.nodes("StandingConcern"):
        if a.s.node(n)["attrs"].get("about") == "qzxungroundable":
            standing = n
    assert standing is not None
    assert a.s.node(standing)["attrs"].get("requested_by") == "Frank", (
        "requester provenance must propagate from the Goal's wanted_by edge")
    state = reflect("self_improvement_status", None, a.s)
    assert "requested by Frank" in state["note"]


# --------------------------------------------------------------------------- #
#  3. TWO-LEVEL ATTITUDE TRACKING.
# --------------------------------------------------------------------------- #
def test_belief_self_report_mints_assertion_and_tagged_level2():
    a = _agent()
    a.converse("Hi, I am Gale.", speech_act="statement")
    gale = _active_party(a)
    a.converse("I think the moon is made of cheese.", speech_act="statement")

    asserted = list(a.inner.neighbours(gale, "asserted"))
    assert len(asserted) == 1, "the self-report must mint exactly one Level-1 Assertion"
    assertion = asserted[0]
    aat = a.s.node(assertion)["attrs"]
    assert aat.get("content") == "I think the moon is made of cheese."
    assert aat.get("flavor") == "belief"

    level2 = None
    for n in a.s.nodes("SmEntity"):
        at = a.s.node(n)["attrs"]
        if at.get("nested") and at.get("belief_holder") == "Gale":
            level2 = n
            break
    assert level2 is not None, "the reused character_tom construction must mint the nested belief entity"
    l2at = a.s.node(level2)["attrs"]
    assert l2at.get("source") == "self_report"
    assert l2at.get("confidence") is not None and 0.0 < l2at["confidence"] < 1.0
    assert list(a.inner.neighbours(level2, "about_assertion")) == [assertion]

    # the agent's OWN knowledge (a HeldAnswer/Concept fact) is unaffected —
    # this never touches the actual-world SmEntity pool.
    real_moon = [n for n in a.s.nodes("SmEntity")
                if a.s.node(n)["attrs"].get("name") == "moon" and not a.s.node(n)["attrs"].get("nested")]
    assert not real_moon or a.s.node(real_moon[0])["attrs"].get("source") != "self_report"


def test_desire_self_report_mints_their_want():
    a = _agent()
    a.converse("Hi, I am Hank.", speech_act="statement")
    a.converse("I want the daemon to be faster.", speech_act="statement")
    found = False
    for n in a.s.nodes("SmEvent"):
        at = a.s.node(n)["attrs"]
        if at.get("verb") == "want" and at.get("idx_protagonist") == "Hank":
            found = True
            assert at.get("source") == "self_report"
            assert at.get("confidence") is not None
    assert found, "'I want X' must ground Hank's own SmEvent{verb:want}"


def test_bare_nominal_mints_no_attitude():
    a = _agent()
    a.converse("Hi, I am Ivy.", speech_act="statement")
    ivy = _active_party(a)
    a.converse("The weather today.", speech_act="statement")
    assert list(a.inner.neighbours(ivy, "asserted")) == [], (
        "a bare nominal (no attitude verb) must mint no Assertion")


def test_question_does_not_mint_a_self_report():
    """A question containing an attitude-class verb ('know') in main-verb
    position is NOT a self-report — it is a question TO the agent."""
    a = _agent()
    a.converse("Hi, I am Jan.", speech_act="statement")
    jan = _active_party(a)
    a.converse("What do you know about koalas?", speech_act="question")
    assert list(a.inner.neighbours(jan, "asserted")) == [], (
        "a question must not be mis-decoded as the interlocutor's own self-report")


def test_hedged_phrasing_lowers_confidence():
    a = _agent()
    a.converse("Hi, I am Kim.", speech_act="statement")
    kim = _active_party(a)
    a.converse("I think the moon is made of cheese.", speech_act="statement")
    plain_conf = None
    for n in a.s.nodes("SmEntity"):
        at = a.s.node(n)["attrs"]
        if at.get("nested") and at.get("belief_holder") == "Kim":
            plain_conf = at.get("confidence")
    assert plain_conf is not None

    b = _agent()
    b.converse("Hi, I am Lee.", speech_act="statement")
    b.converse("I guess maybe the moon is made of cheese.", speech_act="statement")
    hedged_conf = None
    for n in b.s.nodes("SmEntity"):
        at = b.s.node(n)["attrs"]
        if at.get("nested") and at.get("belief_holder") == "Lee":
            hedged_conf = at.get("confidence")
    assert hedged_conf is not None
    assert hedged_conf < plain_conf, "hedged phrasing must yield a LOWER Level-2 confidence"


# --------------------------------------------------------------------------- #
#  3b. PRIORS BY SHAPE-MATCHING + STRUCTURAL EVIDENCE (course corrections 2/3).
# --------------------------------------------------------------------------- #
def test_creator_origin_is_structural_evidence_not_a_shape_prior():
    a = _agent()
    _ensure_seed_chain(a.s, a.inner, a.agent, ("jabberwock_creator",))
    a.converse("Hi, I am Matthew.", speech_act="statement")
    matt = _active_party(a)
    a.converse("I think the substrate needs more testing.", speech_act="statement")
    at = a.s.node(matt)["attrs"]
    assert at.get("self_report_reliability_source") == "creator_origin"
    assert at.get("self_report_reliability") == pytest.approx(0.9)
    eff = im.effective_reliability(a, matt)
    assert eff["source"] == "creator_origin"
    assert eff["value"] == pytest.approx(0.9)


def test_fresh_party_gets_a_shape_prior_with_zero_track_record():
    a = _agent()
    a.converse("The system throughput regression correlates with the cache eviction policy.",
              speech_act="statement")
    party = _active_party(a)
    shape = im.decode_shape(a, party)
    eff = im.effective_reliability(a, party)
    assert eff["n"] == 0
    assert eff["value"] == pytest.approx(shape["prior"])
    assert shape["name"] is not None


def test_poor_fit_party_gets_the_wide_default_interval():
    a = _agent()
    party = im._active_party(a)  # no turns observed at all -> no dominant features
    shape = im.decode_shape(a, party)
    assert shape["name"] == "default_uncalibrated"
    assert shape["interval"] == pytest.approx(0.35)


# --------------------------------------------------------------------------- #
#  3c. TOM CAPACITY (4th course correction: "realistically, some humans
#      barely have theory of mind").
# --------------------------------------------------------------------------- #
def test_tom_capacity_present_with_shape_prior_default():
    a = _agent()
    a.converse("do it now.", speech_act="statement")
    terse_party = _active_party(a)
    terse_tom = im.effective_tom_capacity(a, terse_party)
    assert terse_tom is not None

    b = _agent()
    b.converse("The system throughput regression correlates with the cache eviction policy.",
              speech_act="statement")
    precise_party = _active_party(b)
    precise_tom = im.effective_tom_capacity(b, precise_party)
    reply = b.converse("What do you know about me?", speech_act="question")
    assert "theory-of-mind" in reply.lower() or precise_tom == pytest.approx(0.5)


def test_grice_low_tom_party_gets_plain_repeat():
    """A low-ToM party's literal repeat is licensed as a genuine re-ask (task 4
    tom_capacity guard) -- served plainly, not 'As I mentioned'. tom_capacity
    is RECOMPUTED fresh every shadow-read turn from the party's own
    accumulated shape fit (never a static Python override, per the wave's own
    design), so this establishes a naturally terse-imperative party (a
    strong 4/4 fit, tom_capacity_prior=0.3, below the 0.4 threshold) via
    several short imperative turns BEFORE the topic question, rather than
    hand-setting the attr (which the next shadow-read turn would just
    overwrite)."""
    a = _agent()
    a.converse("do it now.", speech_act="statement")
    a.converse("go now.", speech_act="statement")
    a.converse("stop it.", speech_act="statement")
    party = _active_party(a)
    assert im.effective_tom_capacity(a, party) < 0.4
    a.learn_from_teacher("what is qzxlow", {
        "answer": "qzxlow is a made up test concept", "learn": [{"phrase": "qzxlow"}]})
    a.converse("What do you know about qzxlow?", speech_act="question")
    r2 = a.converse("What do you know about qzxlow?", speech_act="question")
    assert not r2.startswith("As I mentioned"), (
        "a low-tom party's repeat must be served plainly, not read as a Gricean violation")


def test_grice_default_tom_party_still_gets_prefix():
    """Parity: a party whose shape fit does NOT depress tom_capacity below
    the threshold keeps today's Gricean-repeat behavior (the guard fails
    open, per its own documented default)."""
    a = _agent()
    a.converse("Hi, I am Zed.", speech_act="statement")
    a.learn_from_teacher("what is qzxhigh", {
        "answer": "qzxhigh is a made up test concept", "learn": [{"phrase": "qzxhigh"}]})
    a.converse("What do you know about qzxhigh?", speech_act="question")
    r2 = a.converse("What do you know about qzxhigh?", speech_act="question")
    assert r2.startswith("As I mentioned")


def test_blend_shifts_between_early_and_later_turns():
    a = _agent()
    a.converse("Hi, I am Nia.", speech_act="statement")
    nia = _active_party(a)
    a.converse("I think X is true.", speech_act="statement")
    eff_early = im.effective_reliability(a, nia)
    for i in range(6):
        a.converse(f"That was wrong about thing {i}.", speech_act="statement")
        a.converse("I think Y is true.", speech_act="statement")
    eff_late = im.effective_reliability(a, nia)
    assert eff_late["n"] > eff_early["n"]
    assert eff_late["value"] != eff_early["value"], (
        "the SAME phrasing's confidence must shift as individual evidence accrues")


# --------------------------------------------------------------------------- #
#  4. CORRECTIONS revise Level 2, never Level 1.
# --------------------------------------------------------------------------- #
def test_correction_revises_level2_confidence_leaves_assertion_untouched():
    a = _agent()
    a.converse("Hi, I am Omar.", speech_act="statement")
    omar = _active_party(a)
    a.learn_from_teacher("what is the moon", {
        "answer": "the moon is a natural satellite of earth", "learn": [{"phrase": "moon"}]})
    a.converse("What do you know about the moon?", speech_act="question")
    a.converse("I think the moon is made of cheese.", speech_act="statement")

    level2 = None
    for n in a.s.nodes("SmEntity"):
        at = a.s.node(n)["attrs"]
        if at.get("nested") and at.get("belief_holder") == "Omar":
            level2 = n
    assert level2 is not None
    conf_before = a.s.node(level2)["attrs"]["confidence"]
    asserted_before = [a.s.node(x)["attrs"]["content"] for x in a.inner.neighbours(omar, "asserted")]

    # "wrong" is a gap_awareness deficiency cue AND "moon" was just told.
    a.converse("moon is wrong.", speech_act="statement")

    mid = a._last_turn_inbound
    assert a.s.node(mid)["attrs"].get("contradicted_by_interlocutor") == "moon"
    conf_after = a.s.node(level2)["attrs"]["confidence"]
    assert conf_after < conf_before, "a direct contradiction must LOWER the Level-2 confidence"
    assert a.s.node(level2)["attrs"].get("revision_count") == 1
    # Level 1 (what was literally said) is untouched.
    asserted_after = [a.s.node(x)["attrs"]["content"] for x in a.inner.neighbours(omar, "asserted")]
    assert asserted_after[:len(asserted_before)] == asserted_before, (
        "correcting the model must never rewrite what was actually SAID")
    assert int(a.s.node(omar)["attrs"].get("self_report_contradiction_count", 0)) >= 1


# --------------------------------------------------------------------------- #
#  5. GRICE — quantity maxim.
# --------------------------------------------------------------------------- #
def test_grice_repeat_topic_gets_as_i_mentioned_prefix():
    a = _agent()
    a.converse("Hi, I am Priya.", speech_act="statement")
    a.learn_from_teacher("what is qzxfoo", {
        "answer": "qzxfoo is a made up test concept", "learn": [{"phrase": "qzxfoo"}]})
    r1 = a.converse("What do you know about qzxfoo?", speech_act="question")
    assert r1 == "qzxfoo is a made up test concept"
    r2 = a.converse("What do you know about qzxfoo?", speech_act="question")
    assert r2 == "As I mentioned, qzxfoo is a made up test concept"
    goals = [g for g in a.inner.neighbours(a.agent, "has_goal")
             if a.s.node(g)["attrs"].get("kind") == "answer_topic"
             and a.s.node(g)["attrs"].get("concept") == "qzxfoo"
             and a.s.node(g)["attrs"].get("repeats_known") == 1.0]
    assert goals, "the repeat must mark repeats_known=1.0 on the Goal"


def test_grice_elaboration_cue_is_untouched():
    a = _agent()
    a.converse("Hi, I am Quinn.", speech_act="statement")
    a.learn_from_teacher("what is qzxbar", {
        "answer": "qzxbar is a made up test concept", "learn": [{"phrase": "qzxbar"}]})
    a.converse("What do you know about qzxbar?", speech_act="question")
    r2 = a.converse("What else do you know about qzxbar?", speech_act="question")
    assert not r2.startswith("As I mentioned"), (
        "an elaboration/continuation cue must not be treated as a Gricean repeat")


# --------------------------------------------------------------------------- #
#  6. INTROSPECTION — "what do you know about me?"
# --------------------------------------------------------------------------- #
def test_interlocutor_model_reader_answers_from_the_model():
    a = _agent()
    a.converse("Hi, I am Rosa.", speech_act="statement")
    a.converse("I think the moon is made of cheese.", speech_act="statement")
    reply = a.converse("What do you know about me?", speech_act="question")
    assert "Rosa" in reply
    assert "You said" in reply and "I model you as likely believing" in reply
    assert "I weight your self-reports" in reply


def test_self_route_parity_unaffected():
    a = _agent()
    a.converse("Hi, I am Sam.", speech_act="statement")
    reply = a.converse("What are you?", speech_act="question")
    assert "Sam" not in reply
    assert "interlocutor" not in reply.lower()


# --------------------------------------------------------------------------- #
#  7. SHADOW-OFF PARITY — the wave must be byte-identical with shadow_read off.
# --------------------------------------------------------------------------- #
def test_shadow_off_replies_match_shadow_on_content_path():
    """With shadow_read off, the attitude/priors machinery never runs (it
    lives entirely inside `_shadow_read_turn`), so a topic-answer reply is
    byte-identical to a shadow_read=False baseline. Told-status/wanted_by
    (task 1/2) are NOT gated by shadow_read (they are the always-on told-
    status/provenance contract) so they still apply -- this checks the part
    of the wave that IS shadow-gated stays inert."""
    off = _agent(shadow_read=False)
    off.converse("Hi, I am Tia.", speech_act="statement")
    off.learn_from_teacher("what is qzxbaz", {
        "answer": "qzxbaz is a made up test concept", "learn": [{"phrase": "qzxbaz"}]})
    r = off.converse("What do you know about qzxbaz?", speech_act="question")
    assert r == "qzxbaz is a made up test concept"
    tia = _active_party(off)
    assert list(off.inner.neighbours(tia, "asserted")) == [], (
        "no Assertion is minted when shadow_read is off")


# --------------------------------------------------------------------------- #
#  8. Seed hygiene — canon round-trip, churn-free reconcile, InterlocutorShape
#     node reconciliation on resume.
# --------------------------------------------------------------------------- #
def test_seed_canon_round_trip_and_reconcile_churn_free():
    for fname, needs_refreshable in (
        ("conversation_grice.json", True),
        ("interlocutor_trust.json", True),
    ):
        d = json.load(open(os.path.join(ROOT, "seeds", fname)))
        for r in d["rules"]:
            body = {k: v for k, v in r.items() if k != "active"}
            c1 = jd._canon_rule_body(body)
            c2 = jd._canon_rule_body(json.loads(json.dumps(body)))
            assert c1 and c1 == c2, r["name"]
        if needs_refreshable:
            assert fname[:-5] in jd._REFRESHABLE_SEEDS

    a = WorldAdapter()

    def _shape_names():
        return [a.s.node(n)["attrs"].get("name") for n in a.s.nodes("InterlocutorShape")]

    assert "default_uncalibrated" not in _shape_names()
    added = jd._reconcile_seed_typed_nodes(a, "InterlocutorShape", "name")
    assert added > 0
    assert _shape_names().count("default_uncalibrated") == 1
    assert jd._reconcile_seed_typed_nodes(a, "InterlocutorShape", "name") == 0

    n1 = jd._reconcile_seed_rules(a)
    assert n1 > 0
    n2 = jd._reconcile_seed_rules(a)
    assert n2 == 0, "a second reconcile pass on an already-reconciled graph must install/refresh nothing"


# --------------------------------------------------------------------------- #
#  9. Live daemon-shaped smoke transcript.
# --------------------------------------------------------------------------- #
def test_live_daemon_shaped_smoke_transcript(capsys):
    a = WorldAdapter(seeds=(), shadow_read=True)
    load_all_seeds(a)
    turns = [
        ("Hi, I'm Uma.", "statement"),
        ("I think the new scheduler is faster.", "statement"),
        ("I want the tests to run in parallel.", "statement"),
        ("What do you know about me?", "question"),
    ]
    transcript = []
    for text, act in turns:
        reply = a.converse(text, speech_act=act)
        transcript.append((text, reply))
    for said, reply in transcript:
        print(f"  Uma: {said}")
        print(f"  Jabberwock: {reply}")
    final = transcript[-1][1]
    assert "Uma" in final
    assert "You said" in final
    assert "I weight your self-reports" in final
