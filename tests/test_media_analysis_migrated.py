"""AGENT DELETION (domains/media_analysis.py + seeds/media_analysis.json).

Halliday transitivity / critical discourse analysis: an agentless passive
BACKGROUNDS the responsible actor ("Shots were fired." — who fired them?
gone). "Police fired shots." (active) and "Shots were fired by soldiers."
(passive with the agent named) do not background anyone.

`reading_collapse._ground`'s passive_event mode already grounds a passive
clause as `[verb, '_', patient]` — the '_' IS the raw agent-absence signal
(untouched here — see reading_collapse.py's PASSIVE docstring for why a
naive "fill role_ids[-1] whenever a BY marker appears" was tried and
REJECTED: the real Aesop/Grimm parity corpus has a trailing BY attached to
an EMBEDDED reduced-relative participle, not the clause's own passive verb,
and filling it there would misattribute agency). This module is a SIBLING
annotator, mirroring domains/meaning_inference.py's architecture exactly:

ZERO PYTHON DECISIONS: domains/media_analysis.py only WRITES FACTS — one
`PassivePredication{verb, patient, agent, agent_filled}` per passive
reading, `agent`/`agent_filled` from a MECHANICAL, tightly-gated by-phrase
head read (exact clause shape [COP, PPART, BY], nothing else — see
`_by_agent_head`'s docstring). There is no `if verb in AGENTIVE_VERBS`
anywhere in Python — the JOIN (Eq(pp.verb, av.verb), gated on
Eq(pp.agent_filled, 0.0)) and the mint/dedup decision live entirely in
seeds/media_analysis.json's one rule (`mint_agent_deletion`).

Discriminative gates (donkey = 0):

  * HEADLINE — an agentless passive over a held AGENTIVE verb mints
    FramingObservation{device:'agent_deletion', verb, patient}.
  * DISCRIMINATIVE NULLS — a by-phrase agent (mechanically filled), an
    active-voice clause, and a non-agentive passive verb each mint NOTHING.
    Non-fabrication.
  * REVISABLE — the observation carries revisable:1.0.
  * SOURCE AUDIT — no regex in the reading path; the agent_deletion
    decision lives in the seed rule's Eq join, not a Python if/else.
  * TEACH-EXTENDS — teaching ONE new AgentiveVerb via teach() unlocks
    detection for a verb that produced nothing before the lesson, with no
    code change.
  * BYTE-PARITY — this module changes NO existing predication/decompose/
    read_clause field (see tests/test_reading_parity_migrated.py, run
    separately as the parity gate).

Every test uses a FUNCTION-SCOPED fresh agent (the `agent` fixture) and
reads exactly ONE clause — isolation-tested per the project's own documented
lesson: a shared-agent multi-sentence run previously masked a real
discriminative-null failure via PassivePredication's (verb, patient) dedup
key (e.g. 'fire'/'shots' from an agentless sentence silently absorbing a
LATER agented 'Shots were fired by soldiers.' on the SAME agent — the two
sentences happen to share (verb, patient)). Each test below is single-
sentence, single-agent, so that collision cannot occur here.

Run: PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 python3 -m pytest \
    tests/test_media_analysis_migrated.py -p no:randomly -q
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
from domains import media_analysis as ma              # noqa: E402


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


@pytest.fixture()
def agent():
    # function-scoped: each test gets a FRESH graph -- the PassivePredication/
    # FramingObservation dedup keys can never leak across tests.
    dl.warm_wordnet("en")
    s, node = boot_core()
    return _Agent(s, node)


def _deletions(a):
    return ma.held_framing_observations(a, device="agent_deletion")


# --------------------------------------------------------------------------- #
#  HEADLINE
# --------------------------------------------------------------------------- #
def test_headline_shots_were_fired(agent):
    r = rc.read_clause(agent, "Shots were fired.", write=True)
    assert r["predications"] == [["fire", "_", "shots"]], r

    obs = _deletions(agent)
    assert len(obs) == 1, obs
    assert obs[0]["verb"] == "fire", obs
    assert obs[0]["patient"] == "shots", obs
    assert obs[0]["revisable"] == 1.0, obs


def test_headline_a_civilian_was_killed(agent):
    r = rc.read_clause(agent, "A civilian was killed.", write=True)
    assert r["predications"] == [["kill", "_", "civilian"]], r

    obs = _deletions(agent)
    assert len(obs) == 1, obs
    assert obs[0]["verb"] == "kill", obs
    assert obs[0]["patient"] == "civilian", obs


def test_headline_the_bill_was_passed(agent):
    r = rc.read_clause(agent, "The bill was passed.", write=True)
    assert r["predications"] == [["pass", "_", "bill"]], r

    obs = _deletions(agent)
    assert len(obs) == 1, obs
    assert obs[0]["verb"] == "pass", obs
    assert obs[0]["patient"] == "bill", obs


# --------------------------------------------------------------------------- #
#  DISCRIMINATIVE NULLS — no fabrication.
# --------------------------------------------------------------------------- #
def test_null_by_phrase_agent_is_filled_not_deleted(agent):
    r = rc.read_clause(agent, "Shots were fired by soldiers.", write=True)
    # the byte-parity-frozen predication itself is untouched ('_' agent slot,
    # exactly as an agentless passive) -- the by-agent lives in the SEPARATE
    # PassivePredication fact this module writes.
    assert r["predications"] == [["fire", "_", "shots"]], r

    pp = [agent.s.node(n)["attrs"] for n in agent.s.nodes("PassivePredication")]
    assert len(pp) == 1, pp
    assert pp[0]["agent"] == "soldiers", pp
    assert pp[0]["agent_filled"] == 1.0, pp

    assert _deletions(agent) == []


def test_null_active_voice_mints_nothing(agent):
    r = rc.read_clause(agent, "Police fired shots.", write=True)
    assert r["construction"] != "passive", r
    assert agent.s.nodes("PassivePredication") == []
    assert _deletions(agent) == []


def test_null_non_agentive_passive_verb_mints_nothing(agent):
    # 'widen' is a perfectly ordinary regular-participle passive (PPART
    # detects fine) but is NOT a held AgentiveVerb -- the join never fires.
    # The PassivePredication fact is still written (unconditional annotation,
    # a passive reading with no matching AgentiveVerb row is not an error);
    # only the RULE's join declines.
    r = rc.read_clause(agent, "The road was widened.", write=True)
    assert r["predications"] == [["widen", "_", "road"]], r

    pp = [agent.s.node(n)["attrs"] for n in agent.s.nodes("PassivePredication")]
    assert len(pp) == 1, pp
    assert pp[0]["agent_filled"] == 0.0, pp

    assert _deletions(agent) == []


# --------------------------------------------------------------------------- #
#  HONEST RESIDUAL — irregular participles do not passive-detect at all (the
#  documented reading-layer boundary this module builds ON, not around): no
#  PassivePredication, no observation, no fabrication.
# --------------------------------------------------------------------------- #
def test_residual_irregular_participle_never_reaches_this_module(agent):
    r = rc.read_clause(agent, "The vase was broken.", write=True)
    assert r["predications"] == [], r
    assert agent.s.nodes("PassivePredication") == []
    assert _deletions(agent) == []


# --------------------------------------------------------------------------- #
#  SOURCE AUDIT
# --------------------------------------------------------------------------- #
def test_source_audit_no_regex_and_decision_lives_in_the_seed():
    mod_path = os.path.join(ROOT, "domains", "media_analysis.py")
    src = open(mod_path).read()
    lines = [ln.strip() for ln in src.splitlines()]
    assert "import re" not in lines and "import re as _re" not in lines
    assert "re.match" not in src and "re.search" not in src and "re.sub" not in src
    # the Python side never mints a FramingObservation directly and never
    # tests AgentiveVerb membership -- only the mechanical PassivePredication
    # fact. The join/mint/dedup decision is the seed rule's.
    assert 'add_node("FramingObservation"' not in src
    assert 'FramingObservation", {' not in src
    # no Python membership test standing in for the graph join (the pattern
    # this architecture always replaces: `if verb in AGENTIVE_VERBS`).
    for ln in lines:
        assert not (" in agentive" in ln.lower() and ln.startswith(("if ", "elif "))), ln


def test_source_audit_rule_carries_the_join_and_the_guard():
    import json
    seed_path = os.path.join(ROOT, "seeds", "media_analysis.json")
    seed = json.load(open(seed_path))
    rules = {r["name"]: r for r in seed["rules"]}
    rule = rules["mint_agent_deletion"]
    match_edges = {(m[0], m[1]) for m in rule["match"]}
    assert ("agent", "has_passive_predication") in match_edges, rule["match"]
    assert ("agent", "has_agentive_verb") in match_edges, rule["match"]

    where_text = json.dumps(rule["where"])
    # the Eq join between the predication's verb and the AgentiveVerb's verb.
    assert '"key": "verb"' in where_text
    # the agent=='_' guard, expressed as agent_filled==0.0 on the fact
    # (agent_filled is written FROM the mechanical by-phrase read; it is 0.0
    # exactly when the predication's agent slot is the literal '_').
    assert '"key": "agent_filled"' in where_text
    assert '"value": 0.0' in where_text


# --------------------------------------------------------------------------- #
#  TEACH-EXTENDS — teach() grows AgentiveVerb coverage; no code change.
# --------------------------------------------------------------------------- #
def test_agent_teaches_new_agentive_verb(agent, tmp_path):
    from domains.teach import teach

    # 'evict' is not seeded -- an agentless eviction passive mints nothing yet.
    r0 = rc.read_clause(agent, "Tenants were evicted.", write=True)
    assert r0["predications"] == [["evict", "_", "tenants"]], r0
    assert _deletions(agent) == []

    res = teach(agent, "AgentiveVerb", {"verb": "evict"},
                category="taught_agentive_verbs", seeds_dir=tmp_path)
    assert res["saved"] is True, res

    # NO re-read needed -- the taught row is new graph data; re-running the
    # agent's OWN standing rules against it is enough (the PassivePredication
    # from the read above already carries verb='evict'/agent_filled=0.0).
    # ensure_media_analysis_seed's reconcile-wire connects the freshly-taught
    # AgentiveVerb to the agent root (mechanical -- every held row is wired,
    # unconditionally); then the SAME standing rule sees it. (Mirrors
    # test_meaning_inference_migrated.py's test_agent_teaches_new_selectional_
    # coverage precedent exactly.)
    ma.ensure_media_analysis_seed(agent)
    agent.inner.run_rules()

    obs = _deletions(agent)
    assert len(obs) == 1, obs
    assert obs[0]["verb"] == "evict", obs
    assert obs[0]["patient"] == "tenants", obs

    taught_path = tmp_path / "taught_agentive_verbs.json"
    assert taught_path.exists()


# =========================================================================== #
#  UNSAID ROLE (domains/media_analysis.py + seeds/media_analysis.json).
#
#  "What is NOT being said" — the residual of a RELATIONAL NOUN /
#  nominalization. Generalises agent-deletion (there, the verb's AGENT role
#  is the residual) to NOMINAL hosts: "right" is a relational noun (a right
#  is always a right TO something), so RIGHT(holder, to:?) with an unfilled
#  complement is a residual — "a right to what?". DETECT, DO NOT FILL: the
#  output is the formulated QUESTION, never an answer.
#
#  `annotate_relational_noun` writes a MECHANICAL, codebook-independent
#  `NominalMention{noun, next_word}` per distinct content-word lemma in the
#  clause, unconditionally (see domains/media_analysis.py's UNSAID ROLE
#  docstring for why this is NOT gated on already-known RelationalNoun rows —
#  gating there was tried and broke teach-extends). The WHOLE decision — join
#  a NominalMention to a held RelationalNoun row by noun, and mint an
#  UnsaidRole iff the immediately-following token is NOT that row's expected
#  complement marker — lives in seeds/media_analysis.json's `mint_unsaid_role`
#  rule.
#
#  Every test uses a FUNCTION-SCOPED fresh agent and reads exactly ONE
#  clause (the same isolation discipline as the agent-deletion tests above).
# --------------------------------------------------------------------------- #
def _unsaid(a):
    return ma.held_unsaid_roles(a)


def _unsaid_pairs(a):
    return {(u["host"], u["role"]) for u in _unsaid(a)}


# --------------------------------------------------------------------------- #
#  HEADLINE
# --------------------------------------------------------------------------- #
def test_headline_states_rights(agent):
    r = rc.read_clause(agent, "The debate was about states' rights.", write=True)
    assert r["predications"] == [["is_a", "debate", "about_states_rights"]], r

    urs = _unsaid(agent)
    assert len(urs) == 1, urs
    assert urs[0]["host"] == "right", urs
    assert urs[0]["role"] == "to", urs
    assert urs[0]["question"] == "a right to what?", urs
    assert urs[0]["revisable"] == 1.0, urs
    assert urs[0]["filled"] == 0.0, urs


# --------------------------------------------------------------------------- #
#  MULTI-COMPLEMENT — 'killing' has TWO expected complements (of/by); both
#  absent here, so BOTH residuals fire.
# --------------------------------------------------------------------------- #
def test_multi_complement_the_killing_shocked_the_town(agent):
    r = rc.read_clause(agent, "The killing shocked the town.", write=True)
    assert r["predications"] == [["shocked", "killing", "town"]], r

    pairs = _unsaid_pairs(agent)
    assert pairs == {("killing", "of"), ("killing", "by")}, pairs
    questions = {u["question"] for u in _unsaid(agent)}
    assert questions == {"the killing of whom?", "killed by whom?"}, questions


# --------------------------------------------------------------------------- #
#  PARTIAL FILL — the 'of' complement IS present ('of the civilians'), so
#  only 'by' (never realised in this sentence) residual fires. Proves
#  detect-not-fill discriminates present vs absent PER complement.
# --------------------------------------------------------------------------- #
def test_partial_fill_of_present_by_absent(agent):
    r = rc.read_clause(agent, "The killing of the civilians shocked the town.", write=True)
    assert r["predications"] == [["of", "killing", "civilians_shocked_town"]], r

    pairs = _unsaid_pairs(agent)
    assert pairs == {("killing", "by")}, pairs
    assert ("killing", "of") not in pairs, pairs


# --------------------------------------------------------------------------- #
#  COMPLEMENT PRESENT NULL — 'right' immediately followed by its 'to'
#  complement ('to secede'): no residual, no fabrication.
# --------------------------------------------------------------------------- #
def test_null_complement_present_a_right_to_secede(agent):
    r = rc.read_clause(agent, "States have a right to secede.", write=True)
    assert r["predications"] == [["to", "states_have_right", "secede"]], r

    assert _unsaid(agent) == []


# --------------------------------------------------------------------------- #
#  NON-RELATIONAL NULL — a plain noun with no relational-noun row at all:
#  no NominalMention join target, no residual. Honest non-fabrication.
# --------------------------------------------------------------------------- #
def test_null_non_relational_noun_mints_nothing(agent):
    r = rc.read_clause(agent, "The table was brown.", write=True)
    assert r["predications"] == [["is_a", "table", "brown"]], r

    assert _unsaid(agent) == []


# --------------------------------------------------------------------------- #
#  DETECT-NOT-FILL AUDIT — the UnsaidRole records a QUESTION, never a filled
#  answer/value; no world-knowledge lookup lives in the annotator.
# --------------------------------------------------------------------------- #
def test_detect_not_fill_audit(agent):
    rc.read_clause(agent, "The debate was about states' rights.", write=True)
    urs = _unsaid(agent)
    assert len(urs) == 1, urs
    ur = urs[0]
    # the residual IS the question -- 'filled' stays 0.0 (nothing was filled).
    assert ur["filled"] == 0.0, ur
    assert "?" in ur["question"], ur
    # no fabricated answer field anywhere on the belief.
    for key in ("answer", "filler", "value", "fill", "resolved_to"):
        assert key not in ur, ur
    # 'slavery' (the thing "states' rights" is famously euphemistic for) is
    # never guessed, asserted, or present anywhere in the held belief.
    assert "slavery" not in json.dumps(ur).lower()

    mod_path = os.path.join(ROOT, "domains", "media_analysis.py")
    src = open(mod_path).read()
    # no world-knowledge lookup (dictionary/wiki/grounding) in this capability.
    for token in ("dictionary_lexicon", "wiki", "ground_unknowns", "answer_about"):
        assert token not in src, token


# --------------------------------------------------------------------------- #
#  SOURCE AUDIT
# --------------------------------------------------------------------------- #
def test_source_audit_unsaid_role_no_regex_and_decision_lives_in_the_seed():
    mod_path = os.path.join(ROOT, "domains", "media_analysis.py")
    src = open(mod_path).read()
    lines = [ln.strip() for ln in src.splitlines()]
    assert "import re" not in lines and "import re as _re" not in lines
    assert "re.match" not in src and "re.search" not in src and "re.sub" not in src
    # the Python side never mints an UnsaidRole directly and never tests
    # RelationalNoun membership -- only the mechanical NominalMention fact.
    assert 'add_node("UnsaidRole"' not in src
    assert 'UnsaidRole", {' not in src
    for ln in lines:
        assert not (" in relational" in ln.lower() and ln.startswith(("if ", "elif "))), ln


def test_source_audit_rule_carries_the_join_and_the_guard():
    seed_path = os.path.join(ROOT, "seeds", "media_analysis.json")
    seed = json.load(open(seed_path))
    rules = {r["name"]: r for r in seed["rules"]}
    rule = rules["mint_unsaid_role"]
    match_edges = {(m[0], m[1]) for m in rule["match"]}
    assert ("agent", "has_nominal_mention") in match_edges, rule["match"]
    assert ("agent", "has_relational_noun") in match_edges, rule["match"]

    where_text = json.dumps(rule["where"])
    # the Eq join between the mention's noun and the RelationalNoun's noun.
    assert '"key": "noun"' in where_text
    # the absence guard: NOT(next_word == complement_role).
    assert '"key": "next_word"' in where_text
    assert '"key": "complement_role"' in where_text


# --------------------------------------------------------------------------- #
#  TEACH-EXTENDS — teach() grows RelationalNoun coverage; no code change, no
#  re-read of the original clause needed (the mechanical NominalMention fact
#  was already written unconditionally at read time).
# --------------------------------------------------------------------------- #
def test_agent_teaches_new_relational_noun(agent, tmp_path):
    from domains.teach import teach

    # 'crackdown' is not seeded -- yields nothing yet (no join target).
    r0 = rc.read_clause(agent, "The crackdown continued.", write=True)
    assert r0["predications"] == [], r0
    assert _unsaid(agent) == []

    res = teach(agent, "RelationalNoun",
                {"noun": "crackdown", "complement_role": "on",
                 "theme": "domain", "question": "a crackdown on whom?"},
                category="taught_relational_nouns", seeds_dir=tmp_path)
    assert res["saved"] is True, res

    # NO re-read needed -- the mechanical NominalMention{'crackdown', next_word}
    # fact from the read above already exists; ensure_media_analysis_seed's
    # reconcile-wire connects the freshly-taught RelationalNoun to the agent
    # root, then the SAME standing rule joins them.
    ma.ensure_media_analysis_seed(agent)
    agent.inner.run_rules()

    urs = _unsaid(agent)
    assert len(urs) == 1, urs
    assert urs[0]["host"] == "crackdown", urs
    assert urs[0]["role"] == "on", urs
    assert urs[0]["question"] == "a crackdown on whom?", urs

    taught_path = tmp_path / "taught_relational_nouns.json"
    assert taught_path.exists()


# =========================================================================== #
#  POSIT INTENTIONALITY (domains/media_analysis.py + seeds/media_analysis.json).
#
#  Given a residual (a FramingObservation agent_deletion OR an UnsaidRole),
#  POSIT whether the omission is STRATEGIC (a rhetorical euphemism/agency-
#  hiding move) or INCIDENTAL — GRADED, DEFEASIBLE, honestly UNDETERMINED when
#  the signal is thin. Three signal families: REGISTER (register_source's own
#  ShapeDecode verdict, gated on ITS OWN `confident` flag — a bare short
#  clause never fabricates a register), RELEVANCE (Gricean: a HIGH-relevance
#  omission — the AGENT of an agentive verb, a relational noun's DEFINING
#  complement — vs a routinely-omitted LOW-relevance role), and SOURCE
#  (GATED: no `source` label reaches a bare-clause residual, so it never
#  contributes here — `source_weight` stays a Lit 0.0 on every mint rule).
#
#  `ensure_media_analysis_seed` teaches `register_source` ONE new register,
#  `official_statement` (impersonal / no-contraction / no-reference-marker —
#  a press-release/official-announcement shape), via that module's OWN public
#  `add_register` extension path (mirrors its own test suite's 'legalese'
#  precedent) — so the STRATEGIC register signal below is a REAL ShapeDecode
#  verdict on real text, probed and shown, never a fabricated register.
#
#  Every test uses a FUNCTION-SCOPED fresh agent and reads exactly ONE clause
#  (the same isolation discipline as every test above).
# --------------------------------------------------------------------------- #
def _attrs(a, posit=None):
    return ma.held_intent_attributions(a, posit=posit)


# --------------------------------------------------------------------------- #
#  HEADLINE STRATEGIC — unsaid_role ("states' rights") in a register
#  register_source's OWN decode_by_shape CONFIDENTLY classifies as the newly
#  taught 'official_statement' shape (probed below, not asserted blind).
# --------------------------------------------------------------------------- #
def test_headline_states_rights_strategic_register(agent):
    from domains import register_source as rs

    text = ("The department reaffirmed its longstanding commitment to states' "
            "rights as a founding constitutional principle guiding future "
            "policy decisions across the nation.")

    # PROBE FIRST — show decode_by_shape's own verdict on this text is a real,
    # confident 'official_statement' read (not asserted blind). ensure the
    # seed FIRST (mechanical setup, mirrors annotate_*'s own first call) so
    # the newly-taught 'official_statement' register is in the codebook the
    # probe queries -- otherwise the probe would be decoding against a
    # codebook that hasn't been extended yet.
    ma.ensure_media_analysis_seed(agent)
    d = rs.decode_by_shape(agent, text)
    assert d["register"] == "official_statement", d
    assert d["confident"] is True, d

    rc.read_clause(agent, text, write=True)
    urs = _unsaid(agent)
    assert len(urs) == 1 and urs[0]["host"] == "right" and urs[0]["role"] == "to", urs

    ias = _attrs(agent)
    assert len(ias) == 1, ias
    ia = ias[0]
    assert ia["residual_type"] == "unsaid_role", ia
    assert ia["residual_ref"] == "right|to", ia
    assert ia["register"] == "official_statement", ia
    assert ia["posit"] == "strategic", ia
    assert ia["confidence"] >= 0.7, ia
    assert ia["revisable"] == 1.0, ia
    assert "register" in ia["basis"] and "relevance" in ia["basis"], ia


# --------------------------------------------------------------------------- #
#  HEADLINE STRATEGIC — agent_deletion ("shots were fired") in the SAME
#  confidently-detected official_statement register.
# --------------------------------------------------------------------------- #
def test_headline_agent_deletion_strategic_register(agent):
    from domains import register_source as rs

    text = ("Several warning shots were fired outside the presidential compound "
            "during a tense standoff this morning.")

    ma.ensure_media_analysis_seed(agent)
    d = rs.decode_by_shape(agent, text)
    assert d["register"] == "official_statement", d
    assert d["confident"] is True, d

    r = rc.read_clause(agent, text, write=True)
    assert r["predications"] == [["fire", "_", "several_warning_shots"]], r
    obs = _deletions(agent)
    assert len(obs) == 1 and obs[0]["verb"] == "fire", obs

    ias = _attrs(agent)
    assert len(ias) == 1, ias
    ia = ias[0]
    assert ia["residual_type"] == "agent_deletion", ia
    assert ia["register"] == "official_statement", ia
    assert ia["posit"] == "strategic", ia
    assert ia["confidence"] >= 0.7, ia


# --------------------------------------------------------------------------- #
#  UNDETERMINED NULL — the CRITICAL DISCRIMINATION: the SAME verb ('fire'),
#  the SAME high-relevance omission, with NO register/source context (a bare
#  sentence — decode_by_shape is honestly not confident on so few words) posits
#  UNDETERMINED, never strategic. Compare directly against the headline test
#  above: identical relevance signal, different register context, different
#  (revisable) judgment.
# --------------------------------------------------------------------------- #
def test_undetermined_null_no_register_context(agent):
    from domains import register_source as rs

    text = "Shots were fired."
    ma.ensure_media_analysis_seed(agent)
    d = rs.decode_by_shape(agent, text)
    # PROBE: too few words for decode_by_shape's own confidence floor -- the
    # register signal is honestly ABSENT here, not guessed.
    assert d["confident"] is False, d

    r = rc.read_clause(agent, text, write=True)
    assert r["predications"] == [["fire", "_", "shots"]], r

    ias = _attrs(agent)
    assert len(ias) == 1, ias
    ia = ias[0]
    assert ia["residual_type"] == "agent_deletion", ia
    assert ia["register"] == "", ia            # no fabricated register
    assert ia["register_weight"] == 0.0, ia
    assert ia["posit"] == "undetermined", ia   # NOT strategic
    assert 0.15 < ia["confidence"] < 0.7, ia
    assert ia["revisable"] == 1.0, ia


# --------------------------------------------------------------------------- #
#  INCIDENTAL — a LOW-relevance omission ('growth OF/IN what', routinely left
#  implicit) in a NEUTRAL, confidently-detected register ('casual', LOW
#  strategic weight) posits incidental, not strategic.
# --------------------------------------------------------------------------- #
def test_incidental_low_relevance_neutral_register(agent):
    from domains import register_source as rs

    text = ("I really can't get over how much growth there's been this year! "
            "He won't stop bragging about it and honestly neither will she, "
            "don't you think that's funny?")
    ma.ensure_media_analysis_seed(agent)
    d = rs.decode_by_shape(agent, text)
    assert d["register"] == "casual", d
    assert d["confident"] is True, d

    rc.read_clause(agent, text, write=True)
    pairs = _unsaid_pairs(agent)
    assert pairs == {("growth", "of"), ("growth", "in")}, pairs

    ias = _attrs(agent)
    assert len(ias) == 2, ias
    for ia in ias:
        assert ia["residual_type"] == "unsaid_role", ia
        assert ia["register"] == "casual", ia
        assert ia["register_weight"] == 0.0, ia
        assert ia["posit"] == "incidental", ia   # NOT strategic
        assert ia["confidence"] <= 0.15, ia


# --------------------------------------------------------------------------- #
#  GRADED / REVISABLE / DISCRIMINATION AUDIT — the four scenarios above never
#  collapse to a single posit (a probe that marks everything strategic is a
#  FAIL); confidence is a genuine gradient, not a flag.
# --------------------------------------------------------------------------- #
def test_discrimination_is_not_uniform():
    seen_posits = set()
    seen_confidences = set()
    for name, text in (
        ("unsaid_strategic", "The department reaffirmed its longstanding "
         "commitment to states' rights as a founding constitutional principle "
         "guiding future policy decisions across the nation."),
        ("agent_deletion_strategic", "Several warning shots were fired outside "
         "the presidential compound during a tense standoff this morning."),
        ("bare_undetermined", "Shots were fired."),
        ("incidental_growth", "I really can't get over how much growth "
         "there's been this year! He won't stop bragging about it and "
         "honestly neither will she, don't you think that's funny?"),
    ):
        dl.warm_wordnet("en")
        s, node = boot_core()
        a = _Agent(s, node)
        rc.read_clause(a, text, write=True)
        for ia in ma.held_intent_attributions(a):
            seen_posits.add(ia["posit"])
            seen_confidences.add(round(ia["confidence"], 2))
    assert seen_posits == {"strategic", "undetermined", "incidental"}, seen_posits
    assert len(seen_confidences) >= 3, seen_confidences


# --------------------------------------------------------------------------- #
#  SOURCE AUDIT — no regex; the Python side writes MECHANICAL facts only
#  (register/relevance_key), never a posit value or a threshold comparison;
#  the combine + three-way decision live entirely in the seed rules.
# --------------------------------------------------------------------------- #
def test_source_audit_intent_no_regex_and_decision_lives_in_the_seed():
    mod_path = os.path.join(ROOT, "domains", "media_analysis.py")
    src = open(mod_path).read()
    lines = [ln.strip() for ln in src.splitlines()]
    assert "import re" not in lines and "import re as _re" not in lines
    assert "re.match" not in src and "re.search" not in src and "re.sub" not in src
    # never mints IntentAttribution directly, and never assigns a posit
    # literal -- the posit is a Lit value on the MATCHING seed rule only.
    assert 'add_node("IntentAttribution"' not in src
    assert 'IntentAttribution", {' not in src
    assert '"posit": "strategic"' not in src
    assert '"posit": "incidental"' not in src
    assert '"posit": "undetermined"' not in src
    # no Python threshold comparison standing in for the rule's Gte/Lte/Gt/Lt.
    for ln in lines:
        assert not (ln.startswith(("if ", "elif ")) and "confidence" in ln
                    and (">=" in ln or "<=" in ln)), ln


def test_source_audit_intent_rules_carry_the_combine_and_thresholds():
    seed_path = os.path.join(ROOT, "seeds", "media_analysis.json")
    seed = json.load(open(seed_path))
    rules = {r["name"]: r for r in seed["rules"]}
    for name in ("mint_intent_attribution_strategic",
                "mint_intent_attribution_incidental",
                "mint_intent_attribution_undetermined"):
        assert name in rules, rules.keys()
        rule = rules[name]
        match_edges = {(m[0], m[1]) for m in rule["match"]}
        assert ("agent", "has_intent_signal") in match_edges, rule["match"]
        assert ("agent", "has_strategic_register") in match_edges, rule["match"]
        assert ("agent", "has_relevance_weight") in match_edges, rule["match"]
        where_text = json.dumps(rule["where"])
        assert '"type": "Plus"' in where_text, where_text
        assert '"key": "strategic_weight"' in where_text, where_text
        assert '"key": "relevance_weight"' in where_text, where_text
        effects_text = json.dumps(rule["effects"])
        assert '"posit"' in effects_text, effects_text
        # source is explicitly gated -- a Lit 0.0 on every rule, never a join.
        assert '"source_weight": 0.0' in effects_text, effects_text
    # the strategic/incidental thresholds are the SAME two numbers on all
    # three rules (a single, shared collapse policy, not three ad hoc ones).
    for name in ("mint_intent_attribution_strategic",
                "mint_intent_attribution_incidental",
                "mint_intent_attribution_undetermined"):
        where_text = json.dumps(rules[name]["where"])
        assert ('"value": 0.7' in where_text) or ('"value": 0.15' in where_text), where_text


# --------------------------------------------------------------------------- #
#  TEACH-EXTENDS — teaching a NEW RelevanceWeight row changes the posit for a
#  matching residual, no code change. Before teaching, 'reform' (a seeded
#  RelationalNoun) has NO relevance row, so the join fails entirely and
#  NOTHING is minted (honest silence, not a fabricated 'undetermined' either --
#  the codebook genuinely does not cover this role yet).
# --------------------------------------------------------------------------- #
def test_agent_teaches_new_relevance_weight_changes_posit(agent, tmp_path):
    from domains.teach import teach
    from domains import register_source as rs

    text = ("The department announced sweeping reform as part of a broader "
            "legislative package addressing longstanding structural concerns "
            "across the nation.")
    ma.ensure_media_analysis_seed(agent)
    d = rs.decode_by_shape(agent, text)
    assert d["register"] == "official_statement" and d["confident"] is True, d

    rc.read_clause(agent, text, write=True)
    urs = _unsaid(agent)
    assert len(urs) == 1 and urs[0]["host"] == "reform" and urs[0]["role"] == "of", urs

    # BEFORE teaching: no RelevanceWeight row for 'role:reform:of' -- the
    # rules' join has nothing to bind, so NOTHING mints yet.
    assert _attrs(agent) == []

    res = teach(agent, "RelevanceWeight", {"key": "role:reform:of", "relevance_weight": 0.45},
                category="taught_relevance_weights", seeds_dir=tmp_path)
    assert res["saved"] is True, res

    # NO re-read needed -- the mechanical IntentSignal fact from the read
    # above already carries relevance_key='role:reform:of'; reconcile-wire +
    # re-running the agent's OWN standing rules is enough.
    ma.ensure_media_analysis_seed(agent)
    agent.inner.run_rules()

    ias = _attrs(agent)
    assert len(ias) == 1, ias
    assert ias[0]["residual_ref"] == "reform|of", ias
    assert ias[0]["posit"] == "strategic", ias
    assert ias[0]["confidence"] >= 0.7, ias

    taught_path = tmp_path / "taught_relevance_weights.json"
    assert taught_path.exists()
