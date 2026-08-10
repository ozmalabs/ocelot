"""test_frame_harvest — the machine-readable lexical-semantic frameworks (VerbNet
selectional restrictions, a WordNet-derived CoreLex of systematic-polysemy dot-types,
WordNet meronymy) are HARVESTED into graph-resident SelectionalFrame + MetonymyPattern
SEED DATA in the EXACT committed shape, so the SAME coherence-repair coercion rule
family (domains/cognitive_disambiguation.py + seeds/metonymy_patterns.json v2) fires
over the enlarged inventory with NO code change to the rule.

Gates:
  (a) COVERAGE — hundreds-to-thousands of SelectionalFrames + tens-to-hundreds of
      MetonymyPatterns, vs the ~4-6 hand-seeded.
  (b) EXISTING GATES SUBSUMED — the hand-seeded verbs still resolve to their AUTHORED
      frames (not shadowed by a harvested hypernym); the harvest does not break them.
  (c) EXTENDS — a NEW coercion the hand-seeded set did not cover fires from harvested
      data, verbatim ('narrate Dickens' -> his works; 'London reported' -> its govt),
      the SAME rule, no code change.
  (d) LOADS + FIRES — the harvested nodes install via the seed manifest + the SAME
      _wire_satisfied_by + fire the SAME committed rule.
  DONKEY=0 — the harvester is fetch+parse+emit (corpus APIs), no LLM, no `import re`.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_frame_harvest.py -p no:randomly -q -s
"""
from __future__ import annotations

import ast
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core                       # noqa: E402
from domains import dictionary_lexicon as dl                    # noqa: E402
from domains import cognitive_disambiguation as cd              # noqa: E402
from domains import frame_harvest as fh                         # noqa: E402

_SEED = os.path.join(ROOT, "seeds", "metonymy_patterns.json")
_HARVEST = os.path.join(ROOT, "domains", "frame_harvest.py")


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


def _fresh():
    dl.warm_wordnet("en")
    s, node = boot_core()
    ag = _Agent(s, node)
    cd.ensure_metonymy_codebook(ag)
    return ag


def _person(s, name):
    return s.add_node("SmEntity", {"name": name, "coref_category": "person",
                                   "coref_animate": 1.0, "coref_mentions": 2.0})


def _place(s, name):
    return s.add_node("SmEntity", {"name": name, "coref_category": "location",
                                   "coref_animate": 0.0, "coref_mentions": 2.0})


def _event(s, verb, role, arg):
    ev = s.add_node("SmEvent", {"verb": verb, "surface": verb})
    s._inner.add_edge_unchecked(ev, role, arg)
    return ev


# --------------------------------------------------------------------------- #
#  (a) COVERAGE.
# --------------------------------------------------------------------------- #
def test_coverage_hundreds_of_harvested_nodes():
    seed = json.load(open(_SEED))
    frames = [n for n in seed["nodes"] if n["type"] == "SelectionalFrame"]
    pats = [n for n in seed["nodes"] if n["type"] == "MetonymyPattern"]
    harv_f = [n for n in frames if n["attrs"].get("harvested")]
    harv_p = [n for n in pats if n["attrs"].get("harvested")]
    hand_f = [n for n in frames if not n["attrs"].get("harvested")]
    hand_p = [n for n in pats if not n["attrs"].get("harvested")]
    # the hand-seeded head is preserved verbatim (4 frames + 5 patterns).
    assert len(hand_f) == 4 and len(hand_p) == 5
    # the harvest is orders of magnitude larger.
    assert len(harv_f) >= 1000, len(harv_f)
    assert len(harv_p) >= 40, len(harv_p)
    print("COVERAGE frames hand=%d harvested=%d | patterns hand=%d harvested=%d"
          % (len(hand_f), len(harv_f), len(hand_p), len(harv_p)))


def test_harvested_nodes_carry_the_exact_committed_fields():
    seed = json.load(open(_SEED))
    for n in seed["nodes"]:
        if n["type"] == "SelectionalFrame" and n["attrs"].get("harvested"):
            at = n["attrs"]
            assert "." in str(at["verb_synset"])          # a WordNet synset name
            assert at["role"] in ("theme", "agent")
            assert isinstance(at["accepts"], list) and at["accepts"]
            assert "." in str(at["meton_target_root"])    # a WordNet root
        if n["type"] == "MetonymyPattern" and n["attrs"].get("harvested"):
            at = n["attrs"]
            assert at["source_category"]                  # a TYPE, not a name
            assert "." in str(at["target_synset"])        # a WordNet synset target
            assert at["qualia_role"] in ("AGENTIVE", "CONSTITUTIVE", "TELIC")
            # harvested patterns are a RESERVED candidate inventory (seed convention).
            assert float(at.get("reserved", 0.0)) == 1.0


# --------------------------------------------------------------------------- #
#  (b) EXISTING GATES SUBSUMED — hand verbs resolve to their AUTHORED frames.
# --------------------------------------------------------------------------- #
def test_hand_seeded_verbs_not_shadowed_by_harvest():
    ag = _fresh()
    assert cd.verb_frame(ag, "read", "theme")["verb_synset"] == "read.v.01"
    assert cd.verb_frame(ag, "won", "theme")["verb_synset"] == "win.v.01"
    assert cd.verb_frame(ag, "meet", "theme")["verb_synset"] == "meet.v.01"
    assert cd.verb_frame(ag, "announced", "agent")["verb_synset"] == "announce.v.01"
    # announce stays an AGENT-only frame — no harvested hypernym leaks a theme frame.
    assert cd.verb_frame(ag, "announced", "theme") is None
    # and the hand shift still fires, byte-for-byte.
    ev = _event(ag.s, "read", "theme", _person(ag.s, "shakespeare"))
    cd.metonymic_redecode(ag, "")
    assert cd.event_theme(ag, ev)["name"] == "shakespeare_works"


# --------------------------------------------------------------------------- #
#  (c) EXTENDS — a NEW coercion from harvested data, the SAME rule, verbatim.
# --------------------------------------------------------------------------- #
def test_extends_new_theme_verb_from_harvest():
    # 'narrate' was NOT hand-seeded (only 'read' was); its author_works coercion comes
    # entirely from the harvested VerbNet narrate.v.01 communication-theme frame.
    ag = _fresh()
    assert not any(n["attrs"].get("verb_synset") == "narrate.v.01"
                   and not n["attrs"].get("harvested")
                   for n in json.load(open(_SEED))["nodes"]
                   if n["type"] == "SelectionalFrame")     # not a hand frame
    ev = _event(ag.s, "narrate", "theme", _person(ag.s, "dickens"))
    rep = cd.metonymic_redecode(ag, "")
    assert cd.event_theme(ag, ev)["name"] == "dickens_works"
    sh = rep["shifts"][0]
    assert sh["pattern"] == "author_works"
    assert sh["reading"] == "narrate dickens = narrate dickens's works"


def test_extends_new_agent_verb_from_harvest():
    # 'broadcast' was NOT hand-seeded (only 'announce' was); its place_government agent
    # coercion comes from a harvested VerbNet +organization agent frame.
    ag = _fresh()
    ev = _event(ag.s, "broadcast", "agent", _place(ag.s, "london"))
    cd.metonymic_redecode(ag, "")
    names = [ag.s.node(x)["attrs"]["name"]
             for x in ag.s._inner.neighbours(ev, "agent")]
    assert names == ["london_government"]


# --------------------------------------------------------------------------- #
#  (d) LOADS + FIRES the SAME rule (no rule change).
# --------------------------------------------------------------------------- #
def test_loads_and_fires_same_committed_rule():
    from substrate_rs import ext
    ag = _fresh()
    # the committed coerce_* rules are what fire — disabling run_rules kills the shift.
    ev = _event(ag.s, "narrate", "theme", _person(ag.s, "dickens"))
    orig = ext.run_rules
    cd.ext.run_rules = lambda *a, **k: 0
    try:
        rep = cd.metonymic_redecode(ag, "")
    finally:
        cd.ext.run_rules = orig
    assert rep["shifts"] == []                              # Python did not re-bind
    assert cd.event_theme(ag, ev)["name"] == "dickens"      # untouched
    rep2 = cd.metonymic_redecode(ag, "")
    assert cd.event_theme(ag, ev)["name"] == "dickens_works"  # the RULE re-bound it


# --------------------------------------------------------------------------- #
#  DONKEY=0 — the harvester is fetch+parse+emit, no LLM, no `import re`.
# --------------------------------------------------------------------------- #
def test_harvester_is_donkey_zero_no_regex_no_llm():
    tree = ast.parse(open(_HARVEST).read())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(a.name != "re" for a in node.names)
        if isinstance(node, ast.ImportFrom):
            assert node.module != "re"
    src = open(_HARVEST).read().lower()
    assert "openai" not in src and "anthropic" not in src


def test_reemit_is_idempotent():
    # re-running the harvest strips prior harvested nodes and re-appends — the hand
    # head + rule count are invariant.
    before = json.load(open(_SEED))
    n_rules_before = len(before["rules"])
    hand_before = [n for n in before["nodes"] if not n["attrs"].get("harvested")]
    rep = fh.build_and_emit(write=True)
    after = json.load(open(_SEED))
    assert len(after["rules"]) == n_rules_before           # rules untouched
    hand_after = [n for n in after["nodes"] if not n["attrs"].get("harvested")]
    assert hand_before == hand_after                       # hand head byte-identical
    assert rep["harvested_frames"] >= 1000
