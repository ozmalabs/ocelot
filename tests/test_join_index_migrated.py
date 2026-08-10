"""test_join_index_migrated — R10 join-index wave gate.

R10 was the last open residual named by the agent's OWN exhausted trail
(docs/comprehension_decision_ledger.md Wave 3): `rule_mention_resolves_to_
concept`'s match pattern -- `(agent, knows_concept, c)` x `(m, has_mention,
mention)` -- shares NO match variable between its two edges; only the
`where`-clause `Eq(Attr(mention,"text"), Attr(c,"name"))` connects them. The
matcher (runners/dsl/src/rewrite.rs::extend_each) had no way to see that
where-clause connection, so it enumerated the full cartesian product of
held Concepts x accumulated Mentions before filtering -- O(concepts x
mentions), measured as the dominant rule cost (~36ms of a 39ms rule budget
in a 118ms shadow read, growing with conversation length).

THE FIX (engine-side, `runners/dsl/src/rewrite.rs` + `substrate.rs` --
outside `domains/proposal_install.ALLOWED_INSTALL_FILES`, see this file's
final test and the build report for why rung-4's own template surface
cannot reach this bottleneck): a declarative `IndexJoinHint` on the rule
(`seeds/intent.json`'s new `"index_hints"` key) tells the matcher "once
`mention` is bound, probe the declared `(Concept, name)` attr index instead
of scanning every `knows_concept` edge" -- index-THEN-verify, so a stale or
absent index can only widen the search, never fabricate a match. The attr
index itself (`TypedGraph::attr_indices`, `graph.rs`) is INCREMENTALLY
maintained on every node insert/set_attr/delete -- not epoch-cached -- so
correctness can never lag a mutation.

Four gates:
  1. correctness under mutation -- adding/removing a Concept mid-
     conversation changes resolvability IMMEDIATELY, no restart.
  2. the rule-variant swap: the CURRENT (hinted) seed rule and the OLD
     (unhinted, pre-R10) rule body resolve an identical fixture to
     BYTE-IDENTICAL refers_to edges -- the hint changes only cost, never
     behaviour. Swap and revert use the exact remove_rule/add_rule-by-
     exported-name primitive `reflective_faculty.perform_adoptions` uses
     (the mechanical core of the adoption pipeline) -- this fix is
     behaviour-preserving so the Experiment/judge apparatus around it
     doesn't apply, only its install primitive does.
  3. a latency smoke gate: the hinted rule is materially cheaper than the
     unhinted rule at a conversation scale where the unindexed join is
     measurably expensive (loose bound -- shared-machine safe, per the
     precedent in test_shadow_read_migrated.py).
  4. the rung-4 write-surface guardrail was NOT widened to smuggle this
     fix through -- `ALLOWED_INSTALL_FILES` is unchanged; this is an
     honest engine-side change, not a rung-4 install.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

import pytest
import substrate_rs as srs
from substrate.seed_loader import manifest_for

RULE_NAME = "rule_mention_resolves_to_concept"

# The EXACT pre-R10 rule body (no index_hints) -- same match/where/effects
# as seeds/intent.json's rule, minus the hint. Used for the swap/revert gate
# and as the "before" arm of the latency comparison.
_OLD_RULE_JSON = {
    "name": RULE_NAME,
    "match": [
        ["agent", "knows_concept", "c"],
        ["m", "has_mention", "mention"],
    ],
    "where": {
        "type": "And",
        "items": [
            {
                "type": "Eq",
                "a": {"key": "text", "type": "Attr", "node": {"name": "mention", "type": "Var"}},
                "b": {"key": "name", "type": "Attr", "node": {"name": "c", "type": "Var"}},
            },
            {
                "type": "Not",
                "arg": {
                    "type": "Exists", "var_name": "_ign",
                    "predicate": {"value": True, "type": "Lit"},
                    "source": {"type": "Neighbours", "edge_type": "refers_to",
                               "node": {"name": "mention", "type": "Var"}},
                },
            },
        ],
    },
    "effects": [["add_edge", "mention", "refers_to", "c"]],
}


def _boot():
    """Bare substrate + agent, seeded with ONLY the `intent` seed -- enough
    to install rule_mention_resolves_to_concept and nothing else this test
    needs to reason about. Mirrors substrate/boot_core.py's own pattern
    (a single load_seed_manifest call), same idiom
    domains/performance_self_improvement.py._ensure_seed uses for a single
    on-demand seed."""
    s = srs.Substrate()
    inner = s._inner
    agent = s.add_node("Agent", {})
    inner.load_seed_manifest(manifest_for("intent"), agent)
    return s, inner, agent


def _teach_concept(s, inner, agent, name: str):
    c = s.add_node("Concept", {"name": name})
    inner.add_edge_unchecked(agent, "knows_concept", c)
    return c


def _mention(s, inner, text: str):
    m = s.add_node("Message", {})
    mtn = s.add_node("Mention", {"text": text})
    inner.add_edge_unchecked(m, "has_mention", mtn)
    return m, mtn


def _resolved_concept(s, inner, mention_nid):
    hits = inner.neighbours(mention_nid, "refers_to")
    return hits[0] if hits else None


def _rule_us(s, name):
    # rule_costs() reports one entry per RULE SLOT, including tombstoned
    # (removed) ones sharing the same name (cost pinned at 0 once inactive)
    # -- sum rather than take-first so a prior remove_rule/add_rule swap in
    # the same substrate can never accidentally read the DEAD slot's cost.
    return sum(micros for rname, micros, count, prog in s._inner.rule_costs() if rname == name)


def _exported_idx(inner, name: str):
    exported = inner.export_rules()
    for i, r in enumerate(exported):
        if isinstance(r, dict) and r.get("active", True) and r.get("name") == name:
            return i
    return None


# --------------------------------------------------------------------------
# 1. correctness under mutation -- add/remove a Concept mid-conversation.
# --------------------------------------------------------------------------
def test_mid_conversation_concept_add_resolves_immediately():
    s, inner, agent = _boot()
    # The seed's index_hints must have auto-declared the index at add_rule
    # time (substrate.rs) -- no separate declare_attr_index call needed.
    assert inner.has_attr_index("Concept", "name")

    _m1, mtn1 = _mention(s, inner, "europa")
    inner.run_rules(50)
    assert _resolved_concept(s, inner, mtn1) is None, \
        "no Concept named 'europa' is held yet -- must stay unresolved"

    # Teach the concept mid-conversation (mechanical: add_node + edge).
    europa_c = _teach_concept(s, inner, agent, "europa")
    inner.run_rules(50)
    assert _resolved_concept(s, inner, mtn1) == europa_c, \
        "the ALREADY-INGESTED mention must resolve the moment the " \
        "concept exists -- no restart, no re-declare, live index"

    # A brand-new mention of the same word resolves on the very next pass.
    _m2, mtn2 = _mention(s, inner, "europa")
    inner.run_rules(50)
    assert _resolved_concept(s, inner, mtn2) == europa_c


def test_removed_concept_is_immediately_ungroundable():
    s, inner, agent = _boot()
    ganymede_c = _teach_concept(s, inner, agent, "ganymede")
    _m1, mtn1 = _mention(s, inner, "ganymede")
    inner.run_rules(50)
    assert _resolved_concept(s, inner, mtn1) == ganymede_c

    # Remove the concept entirely (remove_node) -- graph.rs's index_node
    # bookkeeping drops it from the attr index on delete (attr_index_drops_
    # node_on_delete, graph.rs).
    inner.remove_node(ganymede_c)

    _m2, mtn2 = _mention(s, inner, "ganymede")
    inner.run_rules(50)
    assert _resolved_concept(s, inner, mtn2) is None, \
        "a mention of a word whose ONLY concept was just deleted must " \
        "NOT resolve -- proves the index entry, not just the graph " \
        "edge, is gone immediately"


# --------------------------------------------------------------------------
# 2. the rule-variant swap -- byte-identical resolution, swap + revert safe.
# --------------------------------------------------------------------------
def _run_fixture(s, inner, agent):
    """A small deterministic fixture: 3 concepts, 5 mentions (2 resolvable
    to distinct concepts, 2 to the same concept, 1 ungroundable). Returns
    the resolved {mention_text: concept_name or None} map."""
    names = ["mercury", "venus", "earth"]
    concepts = {n: _teach_concept(s, inner, agent, n) for n in names}
    mention_texts = ["mercury", "venus", "mercury", "earth", "pluto"]
    mentions = [_mention(s, inner, t) for t in mention_texts]
    inner.run_rules(200)
    out = {}
    for (t, (_m, mtn)) in zip(mention_texts, mentions):
        c = _resolved_concept(s, inner, mtn)
        out[str(mtn)] = None if c is None else next(
            (n for n, cid in concepts.items() if cid == c), "<unknown>")
    return out


def test_variant_swap_is_byte_identical_and_revert_is_safe():
    # Arm A: the CURRENT seed rule (hinted).
    s_new, inner_new, agent_new = _boot()
    result_new = _run_fixture(s_new, inner_new, agent_new)

    # Arm B: swap the hinted rule out for the exact pre-R10 body, using the
    # SAME remove_rule/add_rule-by-exported-name primitive
    # reflective_faculty.perform_adoptions uses.
    s_old, inner_old, agent_old = _boot()
    idx = _exported_idx(inner_old, RULE_NAME)
    assert idx is not None
    assert inner_old.remove_rule(idx)
    new_idx = inner_old.add_rule(_OLD_RULE_JSON)
    assert new_idx is not None
    result_old = _run_fixture(s_old, inner_old, agent_old)

    assert result_new == result_old, \
        f"hinted vs unhinted resolution diverged: {result_new} != {result_old}"
    # Sanity on the fixture itself -- not a vacuous comparison.
    assert None in result_new.values(), "the 'pluto' mention must stay ungrounded in BOTH arms"
    assert list(result_new.values()).count("mercury") == 2

    # REVERT: swap the hinted rule back in on arm B, prove it's still safe
    # (re-resolves identically -- no residual state corruption from the
    # remove/add cycle).
    idx2 = _exported_idx(inner_old, RULE_NAME)
    assert inner_old.remove_rule(idx2)
    hinted_json = dict(_OLD_RULE_JSON)
    hinted_json["index_hints"] = [{
        "for_var": "c", "via_var": "mention", "via_key": "text",
        "node_type": "Concept", "this_key": "name",
    }]
    reverted_idx = inner_old.add_rule(hinted_json)
    assert reverted_idx is not None
    # A FRESH mention resolves the same way after the revert.
    pallas_c = _teach_concept(s_old, inner_old, agent_old, "pallas")
    _m, mtn = _mention(s_old, inner_old, "pallas")
    inner_old.run_rules(50)
    assert _resolved_concept(s_old, inner_old, mtn) == pallas_c


# --------------------------------------------------------------------------
# 3. latency smoke gate -- hinted materially cheaper at scale.
# --------------------------------------------------------------------------
def test_hinted_rule_is_materially_cheaper_at_scale():
    N = 150
    # Unhinted arm.
    s_old, inner_old, agent_old = _boot()
    idx = _exported_idx(inner_old, RULE_NAME)
    inner_old.remove_rule(idx)
    inner_old.add_rule(_OLD_RULE_JSON)
    for i in range(N):
        _teach_concept(s_old, inner_old, agent_old, f"concept_{i}")
    for i in range(N):
        _mention(s_old, inner_old, f"concept_{i}")
    inner_old.reset_rule_costs()
    inner_old.run_rules(400)
    old_us = _rule_us(s_old, RULE_NAME)

    # Hinted arm (the seed as-shipped).
    s_new, inner_new, agent_new = _boot()
    for i in range(N):
        _teach_concept(s_new, inner_new, agent_new, f"concept_{i}")
    for i in range(N):
        _mention(s_new, inner_new, f"concept_{i}")
    inner_new.reset_rule_costs()
    inner_new.run_rules(400)
    new_us = _rule_us(s_new, RULE_NAME)

    print(f"\nR10 latency smoke: unhinted={old_us}us hinted={new_us}us "
          f"(N={N} concepts x {N} mentions)")
    # Loose bound -- shared-machine safe (this repo's own precedent,
    # test_shadow_read_migrated.py): a real index-vs-scan difference at this
    # N should be at least 3x, not a razor's-edge assertion on absolute ms.
    assert new_us * 3 < old_us or old_us < 200, (
        f"expected the hinted rule to be materially cheaper at N={N}: "
        f"old={old_us}us new={new_us}us")


# --------------------------------------------------------------------------
# 4. the rung-4 guardrail was not widened to smuggle this fix through.
# --------------------------------------------------------------------------
def test_allowed_install_files_not_widened():
    from domains.proposal_install import ALLOWED_INSTALL_FILES
    assert ALLOWED_INSTALL_FILES == {"term.rs", "jsonio.rs", "reflect.rs", "py.rs", "shape.rs"}, (
        "R10's engine fix lives in rewrite.rs/substrate.rs -- outside rung-4's "
        "write surface. It must NOT have been smuggled in by widening the "
        "allowlist; the fix went through direct engine authorship (documented "
        "as exactly that), not proposal_install.install_proposal.")
