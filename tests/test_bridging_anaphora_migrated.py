"""test_bridging_anaphora_migrated — the minimal set-membership primitive the descent
authored when 'The Travelling Musicians' hit the floor: a singular pronoun that
denotes an INDIVIDUAL of a salient plural group.

The gap the descent surfaced (not a guess): bridging anaphora was NOT BUILT — a
singular pronoun ('him') has no singular antecedent, the coref number filter
(correctly) excludes the plural group ('robbers'), so the conflict scatters onto a
junk token and the OPPOSITION structure never forms. The fix is graph-native, in
coref Terms + the arc-opposition Argmax, never a Python solution:

  · ANIMACY  — a predicate adjective/adverb glom ('asleep') is filtered out of the
               animate pronoun pool (`_is_nonnominal_modifier` + `_agreement_term`);
  · BRIDGING — a singular animate pronoun whose NUMBER-RELAXED Argmax winner is a
               plural animate group (outscoring every surviving singular) mints a
               `member_of` that group and binds to it (`resolve_pronoun`);
  · MEMBERSHIP — a member's bound events ARE its group's
               (`propagate_member_participation`), so the dog biting the member
               counts as opposing the group and the antagonist Argmax RE-DERIVES
               `decided_by='opposition'`;
  · REVISABLE — the minted member is a weak `FeatureBelief(member_of)`; the same
               native explanation-collapse Argmax that revises a mis-gendered
               sparrow flips it to `reader_wrong` under piled confusion.

Nothing here names an antagonist or chooses a repair — the agent's own Terms do.
"""
from __future__ import annotations

import pytest

from substrate.boot_core import boot_core
from domains import dictionary_lexicon as dl
from domains import comprehension_reader as cr
from domains import coref_entities as ce
from domains import narrative_structure as ns
import domains.reading_corpus as rc


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


@pytest.fixture(scope="module")
def _warm():
    dl.warm_wordnet("en")
    return True


def _fresh():
    return _Agent(*boot_core())


# --------------------------------------------------------------------------- #
#  ANIMACY — a non-nominal modifier is not an animate referent.
# --------------------------------------------------------------------------- #
def test_nonnominal_modifier_detected(_warm):
    """'asleep' is adj/adverb-only in WordNet -> caught; a real noun and an unknown
    coinage are NOT (tight: only adj/adverb-with-no-noun-sense is demoted)."""
    assert ce._is_nonnominal_modifier("asleep") is True
    assert ce._is_nonnominal_modifier("dog") is False          # has a noun synset
    assert ce._is_nonnominal_modifier("Jabberwock") is False   # no WordNet entry at all
    assert ce._is_nonnominal_modifier("two words here") is False  # multi-token


def test_asleep_demoted_from_animate(_warm):
    """A nounified 'asleep' entity carries coref_animate == 0.0 and so is NOT an
    animate antecedent; a person-agreeing pronoun cannot bind it."""
    agent = _fresh()
    ce._touch_entity(agent, "they soon fell asleep", "asleep", "theme", 1)
    sub = agent.s
    got = [n for n in sub.nodes("SmEntity") if sub.node(n)["attrs"].get("name") == "asleep"]
    assert got, "asleep entity was not minted"
    assert float(sub.node(got[0])["attrs"].get("coref_animate")) == 0.0


# --------------------------------------------------------------------------- #
#  BRIDGING + MEMBERSHIP + the antagonist RE-DERIVATION (end-to-end on TM).
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def _tm(_warm):
    grimm = [s for s in rc.SOURCES if s["key"] == "grimm"]
    units = {u["label"]: u for u in rc.load_units(sources=grimm)}
    if "THE TRAVELLING MUSICIANS" not in units:
        pytest.skip("Grimm corpus not cached — TM tale unavailable")
    agent = _fresh()
    cr.read_and_comprehend(agent, units["THE TRAVELLING MUSICIANS"]["text"],
                           window=2, max_sentences=60)
    prot = ns.protagonist_by_arc_agency(agent)
    ant = ns.antagonist_by_arc_opposition(agent, prot=prot)
    return agent, prot, ant


def test_tm_antagonist_decided_by_opposition(_tm):
    """The agent's OWN arc-opposition Argmax re-derives robbers as antagonist by
    OPPOSITION (co_participation > 0) — the honest 'agency+salience' limit is gone."""
    _agent, prot, ant = _tm
    assert prot.get("protagonist") == "dog"
    assert ant.get("antagonist") == "robbers"
    assert ant.get("decided_by") == "opposition"
    assert float(ant.get("co_participation") or 0.0) >= 1.0


def test_tm_member_individuated_and_bridged(_tm):
    """A singular `robber` was individuated with a `member_of -> robbers` edge, and
    its bite-event participation was mirrored onto the group."""
    agent, _prot, _ant = _tm
    sub, native = agent.s, agent.inner
    bridged = []
    for m in sub.nodes("SmEntity"):
        grp = list(native.neighbours(m, "member_of"))
        if grp:
            bridged.append((sub.node(m)["attrs"].get("name"),
                            [sub.node(g)["attrs"].get("name") for g in grp]))
    assert bridged, "no member_of bridge was minted"
    assert any("robbers" in groups for _, groups in bridged)
    # the member's conflict propagated to the group: a bite event names robbers as theme
    bite_group = False
    for e in sub.nodes("SmEvent"):
        if sub.node(e)["attrs"].get("verb") == "bite":
            th = {native.node(t)["attrs"].get("name") for t in native.neighbours(e, "theme")}
            if "robbers" in th:
                bite_group = True
    assert bite_group, "member participation did not propagate to the group"


def test_tm_member_belief_is_revisable(_tm):
    """The minted member is a WEAK reader FeatureBelief(member_of) — a revisable
    inference, not a hard commitment."""
    agent, _prot, _ant = _tm
    sub = agent.s
    member = None
    for m in sub.nodes("SmEntity"):
        if list(agent.inner.neighbours(m, "member_of")):
            member = sub.node(m)["attrs"].get("name")
            break
    assert member is not None
    b = ce._belief_read(agent, member, "member_of")
    assert b is not None
    assert b.get("source") == ce._SOURCE_READER
    assert float(b.get("confidence")) == float(ce._SURPRISE_EV_W)


# --------------------------------------------------------------------------- #
#  REVISABILITY — the same generic collapse Argmax overturns member_of.
# --------------------------------------------------------------------------- #
def test_member_of_belief_collapses_to_reader_wrong_under_conflict(_warm):
    """No conflict -> keep; piled confusion -> the native explanation collapse flips
    the member_of belief to reader_wrong (feature-generic, inherited from gender)."""
    agent = _fresh()
    ce._ensure_explanations(agent)
    ce._belief_set(agent, "robber", "member_of", "robbers",
                   source=ce._SOURCE_READER, confidence=float(ce._SURPRISE_EV_W), turn=1)
    assert ce._explain_surprise(agent, "robber", "member_of", ev=0.0) == "keep"
    for _ in range(4):
        ce._belief_conflict_bump(agent, "robber", "member_of")
    cc = float(ce._belief_read(agent, "robber", "member_of").get("conflict_count"))
    assert ce._explain_surprise(agent, "robber", "member_of", ev=cc) == "reader_wrong"
