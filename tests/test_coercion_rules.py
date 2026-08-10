"""test_coercion_rules — the COERCION PAIR (metonymy + role/eponym re-bind) is now a
GRAPH-RESIDENT COHERENCE-REPAIR RULE FAMILY fired by the substrate's rule engine,
NOT a Python dispatch.

Gates the re-expression in domains/cognitive_disambiguation.py +
seeds/metonymy_patterns.json:

  (b) IT IS A RULE — the coercion decision is a graph-resident Rule (match/where/
      effects) fired by run_rules. The seed carries the three rules; and BEHAVIOURALLY,
      disabling the rule engine (run_rules -> no-op) makes the re-bind NOT happen —
      proof the DECISION is the rule, not Python. A structural check shows no Python
      metonym-mint / theme|agent edge-rebind in metonymic_redecode / coherence_check.
  (c) FIXED-POINT / INTEGRATION — several interdependent repairs (a place->team theme
      shift, a place->government agent shift, a person->prize role re-bind) settle in
      ONE run_rules fixed-point, no hand-sequenced multi-pass; a re-run is a no-op.
  (d) MINT-AS-DATA — container->content added as DATA (un-reserve the pattern + add a
      drinking frame + re-wire satisfied_by) makes 'drank the glass' re-bind to the
      contents via the SAME rule, no code change.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_coercion_rules.py -p no:randomly -q -s
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
from substrate_rs import ext                                    # noqa: E402
from domains import dictionary_lexicon as dl                    # noqa: E402
from domains import cognitive_disambiguation as cd              # noqa: E402

_MODULE = os.path.join(ROOT, "domains", "cognitive_disambiguation.py")
_SEED = os.path.join(ROOT, "seeds", "metonymy_patterns.json")


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


def _event(s, verb, surface, role, arg):
    ev = s.add_node("SmEvent", {"verb": verb, "surface": surface})
    s._inner.add_edge_unchecked(ev, role, arg)
    return ev


# --------------------------------------------------------------------------- #
#  (b) IT IS A RULE — the seed carries the coercion rules, and the engine (not
#      Python) makes the re-bind.
# --------------------------------------------------------------------------- #
def test_seed_carries_the_coercion_rules():
    seed = json.load(open(_SEED))
    rules = {r["name"]: r for r in seed.get("rules", [])}
    assert {"coerce_theme", "coerce_agent", "coerce_role_named_after"} <= set(rules)
    # each is a real engine rule: match + where + effects, and the effect RE-BINDS the
    # slot edge (del_edge + add_edge) — the DECISION is in the rule, as graph data.
    for name in ("coerce_theme", "coerce_agent", "coerce_role_named_after"):
        r = rules[name]
        assert r["match"] and r["where"] and r["effects"]
        ops = [e[0] for e in r["effects"]]
        assert "del_edge" in ops and "add_edge" in ops
    # the metonymy legs mint the referent in the effect (find-or-mint), not in Python.
    assert any(e[0] == "add_node_if_absent" for e in rules["coerce_theme"]["effects"])


def test_rules_are_registered_and_fire_via_run_rules():
    ag = _fresh()
    before = ext.rule_count(ag.s)
    # the codebook is already loaded by _fresh(); loading again is a guarded no-op.
    cd.ensure_metonymy_codebook(ag)
    assert ext.rule_count(ag.s) == before          # idempotent install
    # a violation the rule resolves, via run_rules (no Python dispatch touched it).
    ev = _event(ag.s, "read", "read", "theme", _person(ag.s, "shakespeare"))
    rep = cd.metonymic_redecode(ag, "")
    assert cd.event_theme(ag, ev)["name"] == "shakespeare_works"
    assert rep["shifts"] and rep["shifts"][0]["verdict"] == "re_decoded"


def test_disabling_the_engine_kills_the_rebind_so_it_is_the_rule():
    # THE PROOF: if the coercion were Python, it would still fire with the rule engine
    # disabled. It does NOT — the re-bind is the graph-resident rule, fired by
    # run_rules. Monkeypatch run_rules to a no-op and show the theme is UNTOUCHED.
    ag = _fresh()
    ev = _event(ag.s, "read", "read", "theme", _person(ag.s, "shakespeare"))
    orig = ext.run_rules
    cd.ext.run_rules = lambda *a, **k: 0           # disable the engine
    try:
        rep = cd.metonymic_redecode(ag, "")
    finally:
        cd.ext.run_rules = orig
    assert rep["shifts"] == []                     # Python did NOT re-bind
    assert cd.event_theme(ag, ev)["name"] == "shakespeare"   # theme untouched
    # and with the engine on, the SAME graph re-binds — the rule is the difference.
    rep2 = cd.metonymic_redecode(ag, "")
    assert cd.event_theme(ag, ev)["name"] == "shakespeare_works"
    assert rep2["shifts"] and rep2["shifts"][0]["pattern"] == "author_works"


def _fn_source(tree, name):
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError("no function %r" % name)


def test_no_python_rebind_or_mint_in_the_coercion_functions():
    # STRUCTURAL: neither metonymic_redecode nor the coherence_check role pass MINTS a
    # metonym SmEntity or REBINDS a theme/agent edge in Python — the mutation is the
    # rule's effect. (compose_named_compounds still writes named_after; out of scope.)
    tree = ast.parse(open(_MODULE).read())
    for fn in ("metonymic_redecode", "coherence_check"):
        src = ast.get_source_segment(open(_MODULE).read(), _fn_source(tree, fn))
        # no minted_metonym written from Python in these functions
        assert "minted_metonym\": 1.0" not in src and "'minted_metonym': 1.0" not in src
        # no theme/agent edge re-bind from Python here (the rule does del_edge/add_edge)
        for banned in ('add_edge_unchecked(ev, "theme"', 'add_edge_unchecked(ev, role',
                       'add_edge_unchecked(ev, "agent"', "remove_edge(ev, \"theme\"",
                       "remove_edge(ev, role"):
            assert banned not in src, (fn, banned)


# --------------------------------------------------------------------------- #
#  (c) FIXED-POINT / INTEGRATION — several interdependent repairs settle in ONE
#      run_rules pass, no hand-sequenced 2-pass.
# --------------------------------------------------------------------------- #
def test_fixed_point_settles_all_repairs_in_one_run():
    ag = _fresh()
    cd.ensure_head_codebook(ag)
    s = ag.s
    # three repairs that were previously TWO separate Python passes (metonymy +
    # role) now co-fire in one fixed-point:
    ev_team = _event(s, "win", "won", "theme", _place(s, "france"))       # place->team
    ev_govt = _event(s, "announce", "announced", "agent", _place(s, "washington"))  # place->govt
    nobel = _person(s, "nobel")
    ev_role = _event(s, "win", "won", "theme", nobel)                     # person->prize
    cd.compose_named_compounds(ag, "She won the Nobel Prize.")            # named_after (Python)
    # ONE ingest prep + ONE run_rules — no Python sequencing between repairs.
    cd._prep_frames(ag)
    cd._prep_acquire(ag)
    cd._mark_subject(ag, None)
    steps = ext.run_rules(s)
    assert steps >= 3                              # at least the three repairs fired
    assert cd.event_theme(ag, ev_team)["name"] == "france_team"
    assert [s.node(x)["attrs"].get("name")
            for x in s._inner.neighbours(ev_govt, "agent")] == ["washington_government"]
    assert cd.event_theme(ag, ev_role)["name"] == "nobel_prize"
    # CONVERGED: a re-run is a no-op (fixed point reached).
    assert ext.run_rules(s) == 0


# --------------------------------------------------------------------------- #
#  (d) MINT-AS-DATA — a new comprehension case is NEW DATA, not new code.
# --------------------------------------------------------------------------- #
def test_container_content_mint_as_data():
    ag = _fresh()
    s = ag.s
    # BEFORE: container_content is reserved (no exercised slot) — 'drank the glass'
    # cannot shift.
    glass0 = s.add_node("SmEntity", {"name": "glass", "coref_category": "container",
                                     "coref_animate": 0.0, "coref_mentions": 1.0})
    ev0 = _event(s, "drink", "drank", "theme", glass0)
    rep0 = cd.metonymic_redecode(ag, "")
    assert rep0["shifts"] == []                    # no drink frame yet -> no shift
    assert cd.event_theme(ag, ev0)["name"] == "glass"

    # ADD DATA ONLY: un-reserve the container_content pattern + add a drinking frame +
    # re-wire satisfied_by. No code change to the rule.
    for pn in s.nodes("MetonymyPattern"):
        if s.node(pn)["attrs"].get("pattern") == "container_content":
            s.set_attr(pn, "reserved", 0.0)
    s.add_node("SelectionalFrame", {"verb_synset": "drink.v.01", "role": "theme",
               "accepts": ["object", "substance", "liquid", "food", "beverage"],
               "meton_target_root": "content.n.05"})
    cd._wire_satisfied_by(ag)

    # NOW the SAME rule fires on a fresh 'drank the glass'.
    glass = s.add_node("SmEntity", {"name": "glass", "coref_category": "container",
                                    "coref_animate": 0.0, "coref_mentions": 1.0})
    ev = _event(s, "drink", "drank", "theme", glass)
    rep = cd.metonymic_redecode(ag, "")
    after = cd.event_theme(ag, ev)
    assert after["name"] == "glass_contents"       # re-bound to the CONTENT
    assert after["category"] == "object"
    shift = [x for x in rep["shifts"] if x["rebound_from"] == "glass"][0]
    assert shift["pattern"] == "container_content"
    assert shift["reading"] == "drank glass = drank the contents of glass"
    assert cd.metonymic_shift(ag, "glass_contents") == "glass stands for the contents of glass"
