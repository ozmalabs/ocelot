"""THE AGENT AUTHORS A CLASSIFY-BY-CODEBOOK-JOIN RULE ITSELF.

The rule-authoring faculty (procedural_reader.read_method -> binding_resolver.
derive_binding -> method_synthesis.synthesise_rule_from_method) is extended to
author a NEW rule SHAPE: the "classify-by-codebook-join" that every media_analysis
/ actor_goals slice is an instance of (mint_agent_deletion / mint_actor_goal):

    match:  [agent -has_FACT-> f], [agent -has_CODEBOOK-> c]
    where:  Eq(f.<key>, c.<key>)  [Eq-join]  AND <scalar guards>  AND Not Exists <dedup>
    effects: add_node NEW {fields copied from BOTH f and c} + add_edge link

Before this, the synthesiser's effect templates (recompute / add_edge / del_edge /
set_attr / add_node) each anchored on ONE relation and could not express a two-
source Eq-JOIN against a codebook + a mint of a fresh typed node with fields from
both matched vars. These tests prove the AGENT reads a plain method, GROUNDS the
binding against its OWN domain graph, SYNTHESISES a rule of the target shape,
installs it, and it FIRES -- with NO hand-written rule.

donkey=0: OZMA_NO_LLM=1, no model anywhere, no `import re`.
"""
import json
import os
from pathlib import Path

os.environ.setdefault("OZMA_NO_LLM", "1")

import pytest

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains import procedural_reader as pr
from domains import binding_resolver as br
from domains import method_synthesis as ms


CLASSIFY_METHOD = "When a signal's kind matches a tag's kind, classify a hit."


def _agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


def _seed_toy_domain(a):
    """A tiny toy domain the agent ingests: two agent-held collections -- Signals
    (the FACT) and Tags (the CODEBOOK) -- joined on `kind`. Seeded in the TEST,
    never in a shipped seed."""
    s, inner, ag = a.s, a.inner, a.agent
    sig_match = s.add_node("Signal", {"kind": "ping", "sig": "s1", "live": 1.0})
    sig_dead = s.add_node("Signal", {"kind": "ping", "sig": "s2", "live": 0.0})
    sig_nomatch = s.add_node("Signal", {"kind": "pong", "sig": "s3", "live": 1.0})
    tag = s.add_node("Tag", {"kind": "ping", "label": "PINGCLASS"})
    for n in (sig_match, sig_dead, sig_nomatch):
        inner.add_edge_unchecked(ag, "has_signal", n)
    inner.add_edge_unchecked(ag, "has_tag", tag)
    return {"match": sig_match, "dead": sig_dead, "nomatch": sig_nomatch, "tag": tag}


# --------------------------------------------------------------------------- #
#  where-tree structural reads (mechanical)
# --------------------------------------------------------------------------- #
def _flatten(where):
    """Every node in a where-tree (recurse And/Not/Exists.predicate)."""
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
    """A cross-variable Eq(Attr(Var va, .), Attr(Var vb, .)) anywhere in where."""
    for nd in _flatten(where):
        if nd.get("type") != "Eq":
            continue
        a, b = nd.get("a"), nd.get("b")
        if (_is_attr_of(a, va) and _is_attr_of(b, vb)) or (_is_attr_of(a, vb) and _is_attr_of(b, va)):
            return nd
    return None


def _scalar_guard(where, var):
    """An Eq(Attr(Var var, .), Lit .) -- a scalar guard on a matched var."""
    for nd in _flatten(where):
        if nd.get("type") != "Eq":
            continue
        a, b = nd.get("a"), nd.get("b")
        if _is_attr_of(a, var) and isinstance(b, dict) and b.get("type") == "Lit":
            return nd
    return None


def _not_exists_dedup(where, node_type):
    for nd in _flatten(where):
        if nd.get("type") == "Exists" and \
                (nd.get("source") or {}).get("node_type") == node_type:
            return nd
    return None


# --------------------------------------------------------------------------- #
#  1. the reader reads the join + classify clauses
# --------------------------------------------------------------------------- #
def test_reader_reads_classify_join_clause():
    a = _agent()
    model = pr.read_method(a, CLASSIFY_METHOD, name="toyc")
    step = model["steps"][0]
    trig, main = step["trigger"], step["main"]
    assert trig and trig["kind"] == "join", trig
    assert trig["fact_type"] == "signal" and trig["fact_key"] == "kind"
    assert trig["codebook_type"] == "tag" and trig["codebook_key"] == "kind"
    assert main["kind"] == "action" and main["effect"] == "classify"
    assert main["patient"] == "hit"          # the classification type


# --------------------------------------------------------------------------- #
#  2. the synthesised rule has the target CLASSIFY-BY-CODEBOOK-JOIN shape
# --------------------------------------------------------------------------- #
def _supplied_binding():
    return {
        "fact_edge": "has_signal", "codebook_edge": "has_tag",
        "classification_edge": "has_hit",
        "node_types": {"signal": "Signal", "tag": "Tag", "hit": "Hit"},
        "guards": [["live", 1.0]],
        "fact_carry": ["sig", "kind"],
        "codebook_carry": {"label": "label"},
        "literal_attrs": {"classified": 1.0},
        "dedup_keys": ["sig"],
    }


def test_synthesised_rule_has_target_shape():
    a = _agent()
    model = pr.read_method(a, CLASSIFY_METHOD, name="toyc")
    res = ms.synthesise_rule_from_method(a, model, _supplied_binding(), install=False)
    assert not res.get("wall"), res
    rule = res["rules"][0]

    # two matches, both anchored on the agent hub, on the FACT and CODEBOOK edges
    match = rule["match"]
    assert len(match) == 2, match
    assert match[0] == ["agent", "has_signal", "f"]
    assert match[1] == ["agent", "has_tag", "c"]

    where = rule["where"]
    # the Eq-JOIN between the two matched vars (f.kind == c.kind)
    join = _cross_var_eq_join(where, "f", "c")
    assert join is not None, "no cross-var Eq-join in where"
    # a scalar guard on the fact (f.live == 1.0)
    assert _scalar_guard(where, "f") is not None, "no scalar guard on the fact var"
    # a Not-Exists dedup over the minted classification type
    assert _not_exists_dedup(where, "Hit") is not None, "no Not-Exists dedup over Hit"

    # effects: mint a fresh Hit carrying fields from BOTH f and c, + a link edge
    effs = rule["effects"]
    add_node = next(e for e in effs if e[0] == "add_node")
    assert add_node[2] == "Hit"
    attrs = add_node[3]
    from_f = [k for k, v in attrs.items()
              if isinstance(v, dict) and _is_attr_of(v.get("__term__"), "f")]
    from_c = [k for k, v in attrs.items()
              if isinstance(v, dict) and _is_attr_of(v.get("__term__"), "c")]
    assert from_f, "no field copied FROM the fact var"
    assert from_c, "no field copied FROM the codebook var"
    assert any(e == ["add_edge", "agent", "has_hit", "cls"] for e in effs), effs


# --------------------------------------------------------------------------- #
#  3. the agent authors it (supplied binding) -> it FIRES, guards, dedups
# --------------------------------------------------------------------------- #
def test_agent_authored_classify_rule_fires():
    a = _agent()
    model = pr.read_method(a, CLASSIFY_METHOD, name="toyc")
    # NO hand-written rule: the agent synthesises + installs from the read model
    res = ms.synthesise_rule_from_method(a, model, _supplied_binding(), install=True)
    assert not res.get("wall") and res.get("installed"), res

    nodes = _seed_toy_domain(a)
    s, inner = a.s, a.inner
    inner.run_rules(10000)

    hits = s.nodes("Hit")
    assert len(hits) == 1, "expected exactly one classification"
    ha = s.node(hits[0])["attrs"]
    assert ha["sig"] == "s1"                  # the matching, live signal
    assert ha["kind"] == "ping"               # join key carried from the fact
    assert ha["label"] == "PINGCLASS"         # verdict carried from the codebook
    assert ha["classified"] == 1.0            # literal

    # dedup: a second fixpoint mints no duplicate
    inner.run_rules(10000)
    assert len(s.nodes("Hit")) == 1

    # the guard blocked the dead signal (live=0) and the join blocked kind=pong
    classified_sigs = {s.node(h)["attrs"]["sig"] for h in s.nodes("Hit")}
    assert classified_sigs == {"s1"}


# --------------------------------------------------------------------------- #
#  4. the agent GROUNDS the binding itself (no hand-supplied vocab) -> fires
# --------------------------------------------------------------------------- #
def test_agent_grounds_binding_and_fires():
    a = _agent()
    nodes = _seed_toy_domain(a)                # domain present before grounding
    model = pr.read_method(a, CLASSIFY_METHOD, name="toyc")
    gb = br.derive_binding(a, model)           # the agent grounds it
    binding = gb["binding"]
    # the structural binding is fully grounded from the domain graph
    assert binding.get("fact_edge") == "has_signal"
    assert binding.get("codebook_edge") == "has_tag"
    assert binding.get("classification_edge") == "has_hit"
    assert binding.get("node_types", {}).get("hit") == "Hit"
    # a codebook field to carry was found (fields from BOTH sides)
    assert binding.get("codebook_carry")

    res = ms.synthesise_rule_from_method(a, model, binding, install=True)
    assert not res.get("wall"), res
    # target shape survives the grounded binding
    assert _cross_var_eq_join(res["rules"][0]["where"], "f", "c") is not None

    s, inner = a.s, a.inner
    inner.run_rules(10000)
    hits = s.nodes("Hit")
    # the grounded binding carries the JOIN (kind==kind) but NOT the `live` guard
    # (the minimal text "classify a hit" names no guard -- honestly underspecified),
    # so BOTH ping signals (s1 live, s2 dead) classify and the pong signal (s3)
    # does not: the Eq-join is proven; the guard is the honest remainder.
    sigs = {s.node(h)["attrs"]["sig"] for h in hits}
    assert sigs == {"s1", "s2"}, sigs
    assert all(s.node(h)["attrs"]["label"] == "PINGCLASS" for h in hits)
    # dedup holds on a second fixpoint
    inner.run_rules(10000)
    assert len(s.nodes("Hit")) == 2


# --------------------------------------------------------------------------- #
#  5. the synthesised skeleton matches the shipped actor-goal exemplar
# --------------------------------------------------------------------------- #
def _skeleton(rule):
    """The structural skeleton of a classify-by-codebook-join rule, comparable
    across the toy and the shipped actor-goal exemplar: (#matches on has_ edges
    from one hub, has a cross-var Eq-join, has a scalar-guard Eq-to-Lit, has a
    Not-Exists dedup, mints a node, links it)."""
    match = rule["match"]
    hub = match[0][0]
    two_has_matches = (len(match) >= 2
                       and all(m[0] == hub and m[1].startswith("has_") for m in match[:2]))
    va, vb = match[0][2], match[1][2]
    where = rule["where"]
    has_join = _cross_var_eq_join(where, va, vb) is not None
    has_guard = any(_scalar_guard(where, v) is not None for v in (va, vb))
    has_dedup = any(nd.get("type") == "Exists" for nd in _flatten(where))
    effs = rule["effects"]
    mints = any(e[0] == "add_node" for e in effs)
    links = any(e[0] == "add_edge" for e in effs)
    return {"two_has_matches": two_has_matches, "has_join": has_join,
            "has_guard": has_guard, "has_dedup": has_dedup,
            "mints": mints, "links": links}


def test_synthesised_shape_matches_shipped_actor_goal_exemplar():
    a = _agent()
    model = pr.read_method(a, CLASSIFY_METHOD, name="toyc")
    res = ms.synthesise_rule_from_method(a, model, _supplied_binding(), install=False)
    toy = _skeleton(res["rules"][0])

    seed = json.loads((Path(__file__).resolve().parent.parent
                       / "seeds" / "actor_goals.json").read_text())
    exemplar = next(r for r in seed["rules"] if r["name"] == "mint_actor_goal")
    real = _skeleton(exemplar)

    # the SHAPE the agent authored is the SAME shape the shipped rule has
    assert toy == real, (toy, real)
    assert all(toy.values()), toy


# --------------------------------------------------------------------------- #
#  6. existing effect branches are byte-unchanged (light regression)
# --------------------------------------------------------------------------- #
def test_existing_effect_branches_unchanged():
    a = _agent()
    ivm = ("A view depends on its source. "
           "When the source changes, the view becomes stale. "
           "Recompute a stale view from its source.")
    m1 = pr.read_method(a, ivm, name="ivm")
    r1 = ms.synthesise_rule_from_method(
        a, m1, {"value_attr": "val", "aggregate": {"op": "Count", "edge": "has_mention"}},
        install=False)
    assert r1.get("effect") == "recompute" and not r1.get("wall")
    assert r1["rules"][0]["name"] == "synth_recompute_ivm"

    b = _agent()
    task = "When a task is marked done, add a completed edge from the task to its owner."
    m2 = pr.read_method(b, task, name="task")
    r2 = ms.synthesise_rule_from_method(
        b, m2, {"role_relation": "owned_by", "state_attr": {"done": "done"}}, install=False)
    assert r2.get("effect") == "add_edge" and not r2.get("wall")
    assert r2["rules"][0]["name"] == "synth_add_edge_task"
    # single-relation match (the OLD shape), unchanged
    assert r2["rules"][0]["match"] == [["task", "owned_by", "owner"]]


# =========================================================================== #
#  COMPOUND multi-word collection TYPES — the named wall now widened.
#
#  "a signal's kind" is a single-word type ('signal'); the recurring real slice
#  (mint_actor_goal) joins COMPOUND-typed collections ("an actor action's verb
#  matches an action goal's verb"). The reader now splits each join side at the
#  possessive: the OWNER (possibly multi-word) is the collection TYPE, the
#  possessed noun the KEY; the classification clause reads a compound TYPE too
#  ("classify a writer intent" -> WriterIntent, not Writer). The binding grounds
#  the compound type to its held has_<compound> collection edge. Novel compound
#  types (WriterAction / ActionIntent / WriterIntent) mirror the shipped
#  ActorAction / ActionGoal STRUCTURE without colliding with the shipped
#  actor_goals rule (which would also fire on the real types).
# =========================================================================== #
COMPOUND_METHOD = ("When a writer action's verb matches an action intent's verb, "
                   "classify a writer intent.")


def _seed_compound_domain(a):
    """Two agent-held COMPOUND-typed collections: WriterActions (the FACT) and
    ActionIntents (the CODEBOOK), joined on `verb`. Seeded in the TEST only."""
    s, inner, ag = a.s, a.inner, a.agent
    d_match = s.add_node("WriterAction", {"author": "ann", "verb": "fund", "topic": "solar"})
    d_nomatch = s.add_node("WriterAction", {"author": "bob", "verb": "ignore", "topic": "x"})
    intent = s.add_node("ActionIntent", {"verb": "fund", "intent": "support"})
    for n in (d_match, d_nomatch):
        inner.add_edge_unchecked(ag, "has_writer_action", n)
    inner.add_edge_unchecked(ag, "has_action_intent", intent)
    return {"match": d_match, "nomatch": d_nomatch, "intent": intent}


def test_reader_reads_compound_typed_join_clause():
    a = _agent()
    model = pr.read_method(a, COMPOUND_METHOD, name="mwi")
    step = model["steps"][0]
    trig, main = step["trigger"], step["main"]
    assert trig and trig["kind"] == "join", trig
    # the COMPOUND owner is the collection TYPE (not just its first word), the
    # possessed noun the KEY — the possessive 's is the boundary.
    assert trig["fact_type"] == "writer action" and trig["fact_key"] == "verb", trig
    assert trig["codebook_type"] == "action intent" and trig["codebook_key"] == "verb", trig
    assert main["kind"] == "action" and main["effect"] == "classify"
    # the classification TYPE is the compound trailing NP, not just the head noun
    assert main["node_type"] == "writer intent", main


def test_agent_authors_compound_typed_join_rule_and_fires():
    """The point: the agent reads a COMPOUND-typed classify method, GROUNDS the
    binding against its OWN domain graph (two compound collections), SYNTHESISES
    the two-source Eq-join rule, installs it, and it FIRES — NO hand-written rule."""
    a = _agent()
    _seed_compound_domain(a)                    # domain present before grounding
    model = pr.read_method(a, COMPOUND_METHOD, name="mwi")
    gb = br.derive_binding(a, model)            # the agent grounds the COMPOUND types
    binding = gb["binding"]

    # each compound collection type grounded to its held has_<compound> edge
    assert binding.get("fact_edge") == "has_writer_action", binding
    assert binding.get("codebook_edge") == "has_action_intent", binding
    assert binding.get("classification_edge") == "has_writer_intent", binding
    nt = binding.get("node_types", {})
    assert nt.get("writer action") == "WriterAction", nt
    assert nt.get("action intent") == "ActionIntent", nt
    assert nt.get("writer intent") == "WriterIntent", nt
    # a codebook field to carry (fields from BOTH sides)
    assert binding.get("codebook_carry"), binding

    res = ms.synthesise_rule_from_method(a, model, binding, install=True)
    assert not res.get("wall") and res.get("installed"), res
    rule = res["rules"][0]

    # TWO matches, both on has_<compound> edges from the agent hub
    match = rule["match"]
    assert len(match) == 2, match
    assert match[0] == ["agent", "has_writer_action", "f"], match
    assert match[1] == ["agent", "has_action_intent", "c"], match

    # the Eq-JOIN on the shared 'verb' field between the two compound collections
    join = _cross_var_eq_join(rule["where"], "f", "c")
    assert join is not None, "no cross-var Eq-join in where"

    # effect mints the COMPOUND classification type, fields from BOTH matched vars
    effs = rule["effects"]
    add_node = next(e for e in effs if e[0] == "add_node")
    assert add_node[2] == "WriterIntent", add_node
    attrs = add_node[3]
    from_f = [k for k, v in attrs.items()
              if isinstance(v, dict) and _is_attr_of(v.get("__term__"), "f")]
    from_c = [k for k, v in attrs.items()
              if isinstance(v, dict) and _is_attr_of(v.get("__term__"), "c")]
    assert from_f, "no field copied FROM the fact var"
    assert from_c, "no field copied FROM the codebook var"
    assert any(e == ["add_edge", "agent", "has_writer_intent", "cls"] for e in effs), effs

    # it FIRES: only the joining writer action (verb 'fund') classifies; the
    # non-joining one ('ignore') does not.
    s, inner = a.s, a.inner
    inner.run_rules(10000)
    wi = s.nodes("WriterIntent")
    assert len(wi) == 1, "expected exactly one compound classification"
    at = s.node(wi[0])["attrs"]
    assert at["author"] == "ann"                # carried from the fact var
    assert at["verb"] == "fund"                 # the join key
    assert at["intent"] == "support"            # carried from the codebook var
    # dedup holds across a second fixpoint
    inner.run_rules(10000)
    assert len(s.nodes("WriterIntent")) == 1


def _supplied_compound_binding():
    """A richer binding for the compound method that NAMES the guard + rename the
    minimal prose does not — proving the compound SHAPE reaches the full shipped
    mint_actor_goal skeleton (guard + dedup + mint-from-both), the honest remainder
    being that the bare sentence names no guard, not that the shape cannot express
    one."""
    return {
        "fact_edge": "has_writer_action", "codebook_edge": "has_action_intent",
        "classification_edge": "has_writer_intent",
        "node_types": {"writer action": "WriterAction",
                       "action intent": "ActionIntent",
                       "writer intent": "WriterIntent"},
        "guards": [["actor_role", "agent"]],       # the guard the shipped rule has
        "fact_carry": ["author", "verb"],
        "codebook_carry": {"surface_goal": "intent"},   # rename intent -> surface_goal
        "literal_attrs": {"agency": "author"},
        "dedup_keys": ["author", "verb"],
    }


def test_compound_shape_reaches_shipped_actor_goal_skeleton():
    """The compound-typed rule the agent authors has the SAME structural skeleton
    as the shipped mint_actor_goal (two has_ matches on one hub, cross-var Eq-join,
    scalar guard, Not-Exists dedup, mints + links) once the binding names the guard.
    Proves the widened faculty reaches the real target's shape from COMPOUND types."""
    a = _agent()
    model = pr.read_method(a, COMPOUND_METHOD, name="mwi")
    res = ms.synthesise_rule_from_method(a, model, _supplied_compound_binding(),
                                         install=False)
    assert not res.get("wall"), res
    toy = _skeleton(res["rules"][0])

    seed = json.loads((Path(__file__).resolve().parent.parent
                       / "seeds" / "actor_goals.json").read_text())
    exemplar = next(r for r in seed["rules"] if r["name"] == "mint_actor_goal")
    real = _skeleton(exemplar)

    assert toy == real, (toy, real)
    assert all(toy.values()), toy


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-q"]))
