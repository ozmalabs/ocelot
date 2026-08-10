"""jabberwock_grounds_the_travelling_musicians — the agent grounds the OPPOSITION
graph-natively, DURING READING, via bridging anaphora it grew for itself.

THE OLD WRONG READING (measured, not asserted): on Grimm's 'The Travelling
Musicians' the arc-role reader named dog (protagonist) VS robbers (antagonist)
correctly, but the antagonist was `decided_by='agency+salience'` — the HONEST
LIMIT. The dog and the robbers shared ZERO bound events (`co_participation == 0`):
the pronoun-heavy conflict ("one of them ... the dog ... bit him in the leg") left
the singular pronoun 'him' with NO singular antecedent — the coref number filter
(correctly) excludes the plural group 'robbers' — so the bite's theme scattered
onto the junk token 'asleep' and the OPPOSITION structure never formed.

THE FLOOR THAT SURFACED (the descent, not a guess): bridging anaphora — a singular
pronoun denoting an INDIVIDUAL of a salient plural group — was NOT BUILT. That is
the meta-gap. It was authored as the minimal primitive, in GRAPH RULES + coref
Terms, never as a Python solution:

  · animacy (coref_entities `_is_nonnominal_modifier` + `_agreement_term`): a
    predicate adjective/adverb glom ('asleep') is NOT an animate referent — it is
    filtered out of the person/animate pronoun candidate pool;
  · bridging (coref_entities `resolve_pronoun`): a singular animate pronoun whose
    most-salient antecedent under a NUMBER-RELAXED Argmax is a plural animate GROUP
    (outscoring every surviving singular) INDIVIDUATES a `member_of` that group and
    binds to it — the SAME relaxed-vs-strict probe idiom the gender surprise runs,
    applied to NUMBER;
  · membership (coref_entities `propagate_member_participation`): a member's bound
    events ARE its group's, so the dog biting the individuated robber counts as the
    dog opposing the robbers.

Then the agent's OWN arc-opposition `Argmax` RE-DERIVES `decided_by='opposition'`
(`co_participation` 0 -> 1). No Python names the antagonist; nothing here decides.

The minted member is a REVISABLE inference (a weak `FeatureBelief(member_of)`): the
same native explanation-collapse Argmax that revises a mis-gendered sparrow will
flip it to `reader_wrong` if later confusion piles up.

donkey = 0 (no LLM), no `import re`, offline (cached Grimm). NEVER git.

  PYTHONPATH=runners/dsl/python:.:scripts python3 \
      scripts/jabberwock_grounds_the_travelling_musicians.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from substrate.boot_core import boot_core                       # noqa: E402
from domains import dictionary_lexicon as dl                    # noqa: E402
from domains import comprehension_reader as cr                  # noqa: E402
from domains import coref_entities as ce                        # noqa: E402
from domains import narrative_structure as ns                   # noqa: E402
import domains.reading_corpus as rc                             # noqa: E402

LABEL = "THE TRAVELLING MUSICIANS"


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


def _hr(t: str) -> None:
    print("\n" + "=" * 78 + "\n" + t + "\n" + "=" * 78)


def run() -> dict:
    dl.warm_wordnet("en")
    grimm = [s for s in rc.SOURCES if s["key"] == "grimm"]
    units = {u["label"]: u for u in rc.load_units(sources=grimm)}

    agent = _Agent(*boot_core())
    cr.read_and_comprehend(agent, units[LABEL]["text"], window=2, max_sentences=60)
    sub, native = agent.s, agent.inner

    prot = ns.protagonist_by_arc_agency(agent)
    ant = ns.antagonist_by_arc_opposition(agent, prot=prot)

    _hr("THE READING — protagonist VS antagonist (the agent's own Argmax)")
    print("  protagonist : %s (arc-agency=%s)" % (prot.get("protagonist"), prot.get("agency")))
    print("  antagonist  : %s  decided_by=%s  co_participation=%s"
          % (ant.get("antagonist"), ant.get("decided_by"), ant.get("co_participation")))

    _hr("THE BRIDGE THE AGENT GREW — a singular member individuated from the group")
    for m in sub.nodes("SmEntity"):
        grp = list(native.neighbours(m, "member_of"))
        if grp:
            gnames = [sub.node(g)["attrs"].get("name") for g in grp]
            print("  %r  member_of  %r  (revisable FeatureBelief)"
                  % (sub.node(m)["attrs"].get("name"), gnames))
            b = ce._belief_read(agent, sub.node(m)["attrs"].get("name"), "member_of")
            if b is not None:
                print("     belief: source=%s confidence=%s conflict_count=%s"
                      % (b.get("source"), b.get("confidence"), b.get("conflict_count", 0.0)))

    print("\n  the conflict events now bound to the group:")
    for e in sub.nodes("SmEvent"):
        ea = sub.node(e)["attrs"]
        if ea.get("verb") in ("bite", "kick"):
            ag = [native.node(a)["attrs"].get("name") for a in native.neighbours(e, "agent")]
            th = [native.node(t)["attrs"].get("name") for t in native.neighbours(e, "theme")]
            print("     verb=%-6s agent=%s theme=%s" % (ea.get("verb"), ag, th))

    flipped = ant.get("decided_by") == "opposition"
    _hr("RESULT")
    print("  agency+salience -> opposition:  %s" % flipped)
    print("  Nothing in this script decided it — the agent re-derived it from the")
    print("  bridging primitive it grew when the descent hit the floor.")
    return {"protagonist": prot.get("protagonist"),
            "antagonist": ant.get("antagonist"),
            "decided_by": ant.get("decided_by"),
            "co_participation": ant.get("co_participation"),
            "flipped": flipped}


if __name__ == "__main__":
    run()
