"""TEMPORAL CROSS-ACTION PATTERN — the agent AUTHORS its own reading rule.

Two actions by the SAME actor on the SAME object, opposing in valence ACROSS
TIME, reveal a layered/temporal meta-goal that neither act shows alone: "the oil
company FUNDED the technology, then OPPOSED it." Individually each act is
plausible; together they are a support-then-undermine conflict — the "revealed
only across actions" layer (the explicit LATER slice the single-act
flag_conflicting_meta_goal docstring names).

THE HEADLINE PROVEN HERE: the agent AUTHORS the temporal-conflict rule ITSELF
from a plain English method + a TAUGHT codebook, through its OWN faculty
(procedural_reader.read_method -> binding_resolver.derive_binding ->
method_synthesis.synthesise_rule_from_method -> install). The ONLY Python written
for this slice is a MECHANICAL same-actor-same-object PAIRING annotator
(domains/actor_goals.annotate_action_pairs, world-adapter I/O, emits ONE
ActionPairFact per ordered same-actor-same-object pair keyed by a COMPOSITE
pair_key — UNCONDITIONALLY, no valence judgement, no `import re`), plus codebook
wiring and a reader. NO hand-written rule.

Reshaped to fit the agent's CURRENT 1-key classify-by-codebook-join shape: the
composite `pair_key` ('fund|oppose', order-preserving) makes the whole
cross-action signal a SINGLE Eq-join on ONE field — exactly what the agent can
author today. The pairing annotator makes NO decision about which pairs are
opposing; that is decided ENTIRELY by the AGENT-AUTHORED rule's Eq-join against
the taught OpposingActionPair codebook.

The COMPOUND-ACTOR parse residual (documented in domains/actor_goals.py: an
active-voice "The oil company opposed X." mis-splits because the head noun
'company' has a rare WordNet verb sense) is routed AROUND exactly as the
actor-goals suite already does — the passive-with-by-phrase construction, whose
by-phrase agent is read off the clause's own marker sequence, not the buggy
bare-SVO fallback. "The technology was opposed by the oil company." parses
cleanly (verb='oppose', patient='technology', actor='oil_company'). This slice
builds ON that reading residual, not around it.

donkey=0: OZMA_NO_LLM=1, no model anywhere, no `import re` in the reading path.

Run: PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 python3 -m pytest \
    tests/test_temporal_pattern_migrated.py -p no:randomly -q
"""
import json
import os
from pathlib import Path

os.environ.setdefault("OZMA_NO_LLM", "1")
# Never touch the real boot seeds — teach()'s live-graph add + category decision
# are unaffected; only the disk write to the REAL seed dir is skipped (an explicit
# tmp seeds_dir is still honoured — see the persistence test).
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

import pytest

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains import procedural_reader as pr
from domains import binding_resolver as br
from domains import method_synthesis as ms
from domains import actor_goals as ag
from domains import reading_collapse as rc
from domains import dictionary_lexicon as dl
from domains.teach import teach


# The plain method the agent reads — NO rule syntax, ordinary English.
METHOD = ("When an action pair fact's pair_key matches an opposing action pair's "
          "pair_key, classify a temporal conflict reading.")

# The taught codebook rows (the agent's OWN teach()) — ORDERED composite keys that
# name the meaningful support-then-undermine cross-action pairs.
PAIRS = [
    ("fund|oppose",
     "supports then undermines the same object -- a layered goal revealed across actions"),
    ("support|block",
     "supports then undermines the same object -- a layered goal revealed across actions"),
    ("promote|restrict",
     "supports then undermines the same object -- a layered goal revealed across actions"),
    ("sponsor|ban",
     "supports then undermines the same object -- a layered goal revealed across actions"),
]

# Passive-with-by-phrase clauses (routing around the documented compound-actor
# parse residual) conveying "the oil company FUNDED the technology, then OPPOSED
# it." Same actor 'oil_company', same object 'technology', verbs fund/oppose.
FUND_CLAUSE = "The technology was funded by the oil company."
OPPOSE_CLAUSE = "The technology was opposed by the oil company."


def _agent():
    dl.warm_wordnet("en")
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


def _read(a, *clauses):
    """Ingest clauses -> ActorAction facts (annotate_actor_action runs inside
    read_clause's write path), IN ORDER, so creation order == sentence order."""
    for c in clauses:
        rc.read_clause(a, c, write=True)


def _teach_pairs(a, pairs=PAIRS):
    for pk, note in pairs:
        teach(a, "OpposingActionPair", {"pair_key": pk, "note": note})
    ag.ensure_opposing_pair_codebook(a)


def _author_rule(a, *, install):
    """The agent authors the rule from the plain method + grounded binding. The
    codebook + at least one ActionPairFact must be present so derive_binding can
    GROUND the fact/codebook collections."""
    model = pr.read_method(a, METHOD, name="temporal_conflict")
    gb = br.derive_binding(a, model)
    res = ms.synthesise_rule_from_method(a, model, gb["binding"], install=install)
    return model, gb["binding"], res


# --------------------------------------------------------------------------- #
#  where-tree structural reads (mechanical) — same helpers as the authoring
#  join / surface-inversion tests, so shape assertions are apples-to-apples.
# --------------------------------------------------------------------------- #
def _flatten(where):
    out = []
    if not isinstance(where, dict):
        return out
    out.append(where)
    t = where.get("type")
    if t == "And":
        for it in where.get("items", []):
            out.extend(_flatten(it))
    elif t == "Not":
        out.extend(_flatten(where.get("arg")))
    elif t == "Exists":
        out.extend(_flatten(where.get("predicate")))
    return out


def _is_attr_of(x, var):
    return (isinstance(x, dict) and x.get("type") == "Attr"
            and isinstance(x.get("node"), dict)
            and x["node"].get("type") == "Var" and x["node"].get("name") == var)


def _cross_var_eq_join(where, va, vb):
    for nd in _flatten(where):
        if nd.get("type") != "Eq":
            continue
        a, b = nd.get("a"), nd.get("b")
        if (_is_attr_of(a, va) and _is_attr_of(b, vb)) or (_is_attr_of(a, vb) and _is_attr_of(b, va)):
            return nd
    return None


def _not_exists_dedup(where, node_type):
    for nd in _flatten(where):
        if nd.get("type") == "Exists" and \
                (nd.get("source") or {}).get("node_type") == node_type:
            return nd
    return None


# --------------------------------------------------------------------------- #
#  1. THE AUTHORSHIP PROOF — the rule is produced by the synthesiser from the
#     READ method, not hand-written; it has the target classify-by-join shape,
#     and it carries THREE fields from f (actor + object + pair_key) + note from c.
# --------------------------------------------------------------------------- #
def test_agent_authors_temporal_conflict_rule():
    a = _agent()
    _teach_pairs(a)
    _read(a, FUND_CLAUSE, OPPOSE_CLAUSE)
    ag.annotate_action_pairs(a)                    # a pair fact to ground on

    # the reader reads a plain sentence into a join+classify model
    model = pr.read_method(a, METHOD, name="temporal_conflict")
    step = model["steps"][0]
    trig, main = step["trigger"], step["main"]
    assert trig and trig["kind"] == "join", trig
    assert trig["fact_type"] == "action pair fact" and trig["fact_key"] == "pair_key"
    assert trig["codebook_type"] == "opposing action pair" and trig["codebook_key"] == "pair_key"
    assert main["effect"] == "classify"
    assert main["node_type"] == "temporal conflict reading", main

    # the agent grounds the binding against ITS OWN domain graph
    gb = br.derive_binding(a, model)
    binding = gb["binding"]
    assert binding["fact_edge"] == "has_action_pair", binding
    assert binding["codebook_edge"] == "has_opposing_action_pair", binding
    assert binding["classification_edge"] == "has_temporal_conflict_reading", binding
    assert binding["node_types"]["temporal conflict reading"] == "TemporalConflictReading"
    # THREE fields carried from the fact side + a field from the codebook side
    assert set(binding.get("fact_carry", [])) == {"actor", "object", "pair_key"}, binding
    assert binding.get("codebook_carry") == {"note": "note"}, binding

    # the SYNTHESISER produces the rule — NOT hand-written (name is the
    # synthesiser's own `synth_classify_*`, and no such rule ships in a seed).
    res = ms.synthesise_rule_from_method(a, model, binding, install=False)
    assert not res.get("wall"), res
    rule = res["rules"][0]
    assert rule["name"] == "synth_classify_temporal_conflict", rule["name"]
    assert _no_shipped_temporal_conflict_rule(), \
        "a TemporalConflictReading rule must NOT ship in a seed"

    # SHAPE: two has_ matches on the agent hub, on the fact + codebook edges
    match = rule["match"]
    assert match == [["agent", "has_action_pair", "f"],
                     ["agent", "has_opposing_action_pair", "c"]], match

    # the Eq-JOIN f.pair_key == c.pair_key + a Not-Exists dedup over the mint type
    eqj = _cross_var_eq_join(rule["where"], "f", "c")
    assert eqj is not None, rule["where"]
    assert eqj["a"]["key"] == "pair_key" and eqj["b"]["key"] == "pair_key", eqj
    assert _not_exists_dedup(rule["where"], "TemporalConflictReading") is not None

    # EFFECT: mint TemporalConflictReading carrying actor+object+pair_key FROM f +
    # note FROM c, linked off the agent hub.
    effs = rule["effects"]
    add_node = next(e for e in effs if e[0] == "add_node")
    assert add_node[2] == "TemporalConflictReading", add_node
    attrs = add_node[3]
    from_f = {k for k, v in attrs.items()
              if isinstance(v, dict) and _is_attr_of(v.get("__term__"), "f")}
    from_c = {k for k, v in attrs.items()
              if isinstance(v, dict) and _is_attr_of(v.get("__term__"), "c")}
    assert {"actor", "object", "pair_key"} <= from_f, attrs
    assert "note" in from_c, attrs
    assert any(e == ["add_edge", "agent", "has_temporal_conflict_reading", "cls"]
               for e in effs), effs


def _no_shipped_temporal_conflict_rule():
    """No seed file ships a rule that mints TemporalConflictReading — proving the
    ONLY such rule is the one the agent authored."""
    seeds = Path(__file__).resolve().parent.parent / "seeds"
    for p in seeds.glob("*.json"):
        try:
            m = json.loads(p.read_text())
        except Exception:
            continue
        if not isinstance(m, dict):
            continue
        for r in m.get("rules", []) or []:
            for eff in r.get("effects", []) or []:
                if isinstance(eff, list) and len(eff) >= 3 and \
                        eff[0] == "add_node" and eff[2] == "TemporalConflictReading":
                    return False
    return True


# --------------------------------------------------------------------------- #
#  2. FIRES — the agent-authored rule joins the taught composite key and mints a
#     temporal-conflict reading carrying all four fields.
# --------------------------------------------------------------------------- #
def test_authored_rule_fires_on_fund_then_oppose():
    a = _agent()
    _teach_pairs(a)
    _read(a, FUND_CLAUSE, OPPOSE_CLAUSE)
    pairs = ag.annotate_action_pairs(a)
    assert len(pairs) == 1, pairs                  # exactly one same-actor-same-object pair
    _, _, res = _author_rule(a, install=True)
    assert not res.get("wall") and res.get("installed"), res

    a.inner.run_rules(10000)
    readings = ag.held_temporal_conflicts(a)
    assert len(readings) == 1, readings
    r = readings[0]
    assert r["actor"] == "oil_company", r
    assert r["object"] == "technology", r
    assert r["pair_key"] == "fund|oppose", r
    assert "revealed across actions" in (r["note"] or ""), r

    # dedup: a second fixpoint mints no duplicate
    a.inner.run_rules(10000)
    assert len(ag.held_temporal_conflicts(a)) == 1


# --------------------------------------------------------------------------- #
#  3. DISCRIMINATION (the value) — a same-actor-same-object pair that is NOT
#     opposing, a different-object pair, a single action, and REVERSED order all
#     mint nothing.
# --------------------------------------------------------------------------- #
def test_non_opposing_pair_flags_nothing():
    a = _agent()
    _teach_pairs(a)
    # fund then EXPAND the same technology -> 'fund|expand', NOT a taught opposing
    # pair (expand is not an undermine) -> honest null.
    _read(a, FUND_CLAUSE, "The technology was expanded by the oil company.")
    pairs = ag.annotate_action_pairs(a)
    assert len(pairs) == 1                          # the pair IS emitted (no valence gate)...
    assert a.s.node(pairs[0])["attrs"]["pair_key"] == "fund|expand"
    _, _, res = _author_rule(a, install=True)
    assert not res.get("wall") and res.get("installed"), res
    a.inner.run_rules(10000)
    assert ag.held_temporal_conflicts(a) == []     # ...but the codebook does not name it


def test_different_object_flags_nothing():
    a = _agent()
    _teach_pairs(a)
    # fund the TECHNOLOGY, oppose the SOFTWARE — same actor, DIFFERENT objects:
    # no same-object pair exists, so nothing to join.
    _read(a, FUND_CLAUSE, "The software was opposed by the oil company.")
    pairs = ag.annotate_action_pairs(a)
    assert pairs == [], pairs                       # different object -> no pair at all
    _, _, res = _author_rule(a, install=True)
    # derive_binding still grounds off... nothing: with no ActionPairFact the
    # fact collection is absent, so authorship walls honestly here. Assert the
    # OUTCOME regardless: no reading is minted.
    if not res.get("wall"):
        a.inner.run_rules(10000)
    assert ag.held_temporal_conflicts(a) == []


def test_single_action_flags_nothing():
    a = _agent()
    _teach_pairs(a)
    _read(a, FUND_CLAUSE)                            # one action only, no pair
    pairs = ag.annotate_action_pairs(a)
    assert pairs == [], pairs
    _, _, res = _author_rule(a, install=True)
    if not res.get("wall"):
        a.inner.run_rules(10000)
    assert ag.held_temporal_conflicts(a) == []


def test_reversed_order_flags_nothing():
    a = _agent()
    _teach_pairs(a)
    # OPPOSE then FUND -> composite key 'oppose|fund', which is NOT taught (only
    # the support-then-undermine direction 'fund|oppose' is). Order is preserved
    # in the composite key, so the reverse direction is a distinct, un-taught key.
    _read(a, OPPOSE_CLAUSE, FUND_CLAUSE)
    pairs = ag.annotate_action_pairs(a)
    assert len(pairs) == 1
    assert a.s.node(pairs[0])["attrs"]["pair_key"] == "oppose|fund"
    _, _, res = _author_rule(a, install=True)
    assert not res.get("wall") and res.get("installed"), res
    a.inner.run_rules(10000)
    assert ag.held_temporal_conflicts(a) == []


# --------------------------------------------------------------------------- #
#  4. AGENT-GROWS-IT — teach a NEW opposing composite key ('praise|undermine');
#     a new same-actor-same-object praise-then-undermine pair now flags, with NO
#     code and NO rule change (the authored rule already joins the codebook).
# --------------------------------------------------------------------------- #
def test_teaching_a_pair_grows_coverage():
    a = _agent()
    _teach_pairs(a)
    _read(a, FUND_CLAUSE, OPPOSE_CLAUSE)
    ag.annotate_action_pairs(a)
    _, _, res = _author_rule(a, install=True)
    assert not res.get("wall") and res.get("installed"), res
    a.inner.run_rules(10000)
    base = {r["pair_key"] for r in ag.held_temporal_conflicts(a)}
    assert base == {"fund|oppose"}, base

    # a NEW praise-then-undermine pair on a DIFFERENT object the codebook does NOT
    # yet cover -> null delta (the pair fact is emitted, but 'praise|undermine' is
    # not taught).
    _read(a, "The startup was praised by the oil company.",
             "The startup was undermined by the oil company.")
    grown_pairs = ag.annotate_action_pairs(a)
    assert any(a.s.node(n)["attrs"]["pair_key"] == "praise|undermine" for n in grown_pairs)
    a.inner.run_rules(10000)
    assert {r["pair_key"] for r in ag.held_temporal_conflicts(a)} == base

    # teach the new opposing pair (the agent's OWN teach()) + reconcile-wire it —
    # NO rule or code change — and the SAME authored rule now flags it.
    teach(a, "OpposingActionPair",
          {"pair_key": "praise|undermine",
           "note": "supports then undermines the same object -- a layered goal revealed across actions"})
    ag.ensure_opposing_pair_codebook(a)
    a.inner.run_rules(10000)
    grown = {r["pair_key"] for r in ag.held_temporal_conflicts(a)}
    assert grown == {"fund|oppose", "praise|undermine"}, grown


# --------------------------------------------------------------------------- #
#  5. SOURCE AUDIT — no `import re`; the PAIRING annotator makes NO valence
#     decision (emits EVERY same-actor-same-object ordered pair, codebook-
#     independent); the DECISION (which pairs are opposing) is the AUTHORED rule.
# --------------------------------------------------------------------------- #
def test_source_audit_no_regex_no_valence_decision():
    src = (Path(__file__).resolve().parent.parent / "domains" / "actor_goals.py").read_text()
    for line in src.splitlines():
        s = line.strip()
        assert not (s == "import re" or s.startswith("import re ")
                    or s.startswith("import re,")), ("regex import in reading path: %r" % line)
        assert not s.startswith("import re;"), line
    assert "re.match" not in src and "re.search" not in src and "re.sub" not in src
    # Python never mints TemporalConflictReading or the codebook rows directly —
    # only the mechanical ActionPairFact. The join/mint/dedup decision is the
    # AGENT-AUTHORED rule's; the codebook rows are the agent's own teach().
    assert 'add_node("TemporalConflictReading"' not in src
    assert 'add_node("OpposingActionPair"' not in src

    # the annotator emits pairs UNCONDITIONALLY — identical output whether or not
    # any opposing-pair codebook is taught (no codebook-conditional decision).
    a1 = _agent()
    _read(a1, FUND_CLAUSE, OPPOSE_CLAUSE)
    n1 = len(ag.annotate_action_pairs(a1))
    a2 = _agent()
    _teach_pairs(a2)                                 # a full codebook present
    _read(a2, FUND_CLAUSE, OPPOSE_CLAUSE)
    n2 = len(ag.annotate_action_pairs(a2))
    assert n1 == n2 == 1, (n1, n2)                   # the codebook never gates emission

    # and it emits an ordered composite pair_key even for a NON-opposing pair
    # (no valence judgement in the annotator) — proving it enumerates, not decides.
    a3 = _agent()                                    # NO codebook taught
    _read(a3, FUND_CLAUSE, "The technology was expanded by the oil company.")
    ag.annotate_action_pairs(a3)
    keys = {a3.s.node(n)["attrs"]["pair_key"] for n in a3.s.nodes("ActionPairFact")}
    assert keys == {"fund|expand"}, keys            # emitted despite matching no codebook
    assert ag.held_temporal_conflicts(a3) == []     # and no reading without an authored rule


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-q"]))
