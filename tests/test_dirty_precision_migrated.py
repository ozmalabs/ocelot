"""GATE — DIRTY-PROPAGATION PRECISION (block 187000).

Prereg `DIRTY_PRECISION_PREREG.md`, committed ALONE before any number.

What this pins:

* **BYTE-IDENTITY (the primary gate).** `precise_dirty` ON must produce a graph
  IDENTICAL to the committed over-approximate path. Skipping a genuinely-clean
  rule is a no-op BY DEFINITION — this proves it on real workloads rather than
  asserting it.
* **THE WRONG-PRECISION FALSIFIER.** An over-aggressive predicate that skips
  genuinely-dirty rules MUST break byte-identity. Without this the gate above
  would be vacuous.
* **THE NO-OP-WRITE SKIP.** A `set_attr` that does not change the stored value
  dirties NOTHING under the precise path, and the graph is unchanged either way.
* **NO FREE LUNCH.** When every rule genuinely reads what was written, the
  precise path marks EXACTLY as many rules as the blanket — it can skip nothing,
  so it must not pretend to.
* **THE DEFAULT IS OFF** and `term.rs` carries none of this rung.

Self-contained: builds its own substrates, loads no fixture, needs no `data/`.
"""
from __future__ import annotations

import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.world_adapter import WorldAdapter  # noqa: E402


def _canon(obj):
    if isinstance(obj, float):
        return "f" + repr(obj)
    if isinstance(obj, bool):
        return "b" + repr(obj)
    if isinstance(obj, int):
        return "i" + repr(obj)
    if isinstance(obj, (list, tuple)):
        return "[" + ",".join(_canon(x) for x in obj) + "]"
    if isinstance(obj, dict):
        return "{" + ",".join(repr(k) + ":" + _canon(obj[k])
                              for k in sorted(obj, key=repr)) + "}"
    return repr(obj)


def _dump(inner):
    return _canon(inner.graph_to_dict())


# --------------------------------------------------------------- workloads ----
def _chain_agent(precise=False, wrong=False, n_chain=6, n_groups=4):
    """N independent rule CHAINS over their own node types, plus a where-clause
    rule per group. Each group's material is real, so a group left un-dirtied
    would visibly lose work. External writes drive it (the path this rung
    touches), never rule effects alone."""
    agent = WorldAdapter(seeds=())
    inner = agent.inner
    inner.set_precise_dirty(precise)
    if wrong:
        inner.set_dirty_overaggressive(True)
    for g in range(n_groups):
        for k in range(n_chain):
            inner.add_rule({
                "name": f"chain_g{g}_r{k}",
                "match": [["s", f"e_g{g}_{k}", "t"]],
                "effects": [["add_edge", "s", f"e_g{g}_{k + 1}", "t", {}],
                            ["set_attr_if_different", "t", f"v{k}", float(k)]],
            })
        inner.add_rule({
            "name": f"guard_g{g}",
            "match": [["s", f"e_g{g}_0", "t"]],
            "where": {"type": "Gt",
                      "a": {"type": "Attr", "node": {"type": "Var", "name": "s"},
                            "key": "level"},
                      "b": {"type": "Lit", "value": 2.0}},
            "effects": [["set_attr_if_different", "t", "flagged", 1.0]],
        })
        # A second where-rule per group reading a DIFFERENT attr. The committed
        # blanket wakes it on any external write; the precise path must not,
        # because `other` was not written. This is the rule that makes the
        # reduction measurable rather than definitional.
        inner.add_rule({
            "name": f"other_g{g}",
            "match": [["s", f"e_g{g}_0", "t"]],
            "where": {"type": "Gt",
                      "a": {"type": "Attr", "node": {"type": "Var", "name": "s"},
                            "key": "other"},
                      "b": {"type": "Lit", "value": 2.0}},
            "effects": [["set_attr_if_different", "t", "othered", 1.0]],
        })
    return agent


def _run_chain(precise=False, wrong=False, levels=(0.0, 1.0, 5.0, 5.0, 9.0)):
    agent = _chain_agent(precise, wrong)
    srcs = []
    for g in range(4):
        s = agent.s.add_node(f"Src{g}", {"level": 0.0})
        t = agent.s.add_node(f"Tgt{g}", {"level": 0.0})
        agent.inner.add_edge_unchecked(s, f"e_g{g}_0", t)
        srcs.append(s)
    agent.inner.run_rules()
    for lv in levels:
        for s in srcs:
            agent.s.set_attr(s, "level", lv)
        agent.inner.run_rules()
    return _dump(agent.inner)


def _run_scheduler(precise=False, wrong=False):
    """A REAL committed seed set (`cognitive_areas` + `cognitive_scheduler`) with
    the scheduler scenario the seizure tests use — external writes, task status
    churn, node deletion."""
    agent = WorldAdapter(seeds=())
    for name in ("cognitive_areas", "cognitive_scheduler"):
        path = os.path.join(ROOT, "seeds", name + ".json")
        agent.inner.load_seed_manifest(json.load(open(path)), agent.agent)
    agent.inner.set_precise_dirty(precise)
    if wrong:
        agent.inner.set_dirty_overaggressive(True)
    made = []
    for a in range(3):
        area = agent.s.add_node("CognitiveArea", {
            "name": f"g{a}", "status": "active", "input_epoch": 2,
            "logical_tick": 0, "desired_workers": 1, "effort": 0.0,
            "last_residual_epoch": -1})
        dst = agent.s.add_node("CognitiveArea", {
            "name": f"d{a}", "status": "active", "input_epoch": 1,
            "logical_tick": 0, "desired_workers": 1, "effort": 0.0,
            "last_residual_epoch": -1})
        agent.inner.add_edge_unchecked(area, "projects_to", dst)
        res = agent.s.add_node("Residual", {"epoch": 5 + a})
        agent.inner.add_edge_unchecked(area, "has_residual", res)
        load = agent.s.add_node("AreaLoad", {
            "queued": 3, "failed": 0, "fold_conflicts": 0,
            "capacity_workers": 2})
        agent.inner.add_edge_unchecked(area, "has_area_load", load)
        for i in range(3):
            t = agent.s.add_node("CognitiveTask", {
                "status": "pending", "kind": "abs_diff_energy",
                "payload": [float(i), float(i + 1)], "input_epoch": 2,
                "salience": 0.9 - 0.1 * i, "logical_time": i,
                "area": f"g{a}", "order": 2, "effort": 1})
            agent.inner.add_edge_unchecked(area, "has_task", t)
        made.append(area)
    for _ in range(4):
        agent.inner.run_cognitive_tasks(1)
        agent.inner.run_rules()
    # A DELETION, so the precise path's remove_node branch is exercised.
    for nd in list(agent.s.nodes("CognitiveTask"))[:2]:
        agent.s.remove_node(nd)
    agent.inner.run_rules()
    d = json.loads(json.dumps(agent.inner.graph_to_dict()))
    for node in d.get("nodes", []):
        if node.get("type") in ("AreaLoad", "TaskResult"):
            node["attrs"].pop("service_wall_micros", None)
            node["attrs"].pop("wall_micros", None)
    return _canon(d)


WORKLOADS = {"chain": _run_chain, "scheduler": _run_scheduler}


# ------------------------------------------------------------------ tests -----
def test_the_default_is_OFF():
    """Nothing in the committed tree turns precision on; a fresh substrate is on
    the committed blanket path."""
    agent = WorldAdapter(seeds=())
    agent.inner.set_dirty_telemetry(True)
    n = agent.s.add_node("Probe", {"v": 1.0})
    # Under the blanket, a same-value write is still a WRITE (no skip). The
    # telemetry counts it and records that it changed nothing.
    agent.s.set_attr(n, "v", 1.0)
    m = agent.inner.dirty_marks()
    assert m["attr_writes"] == 1
    assert m["noop_attr_writes"] == 1, "same-value write must be SEEN as a no-op"


@pytest.mark.parametrize("wl", sorted(WORKLOADS))
def test_precise_dirty_is_BYTE_IDENTICAL_to_the_over_approximate_path(wl):
    """THE PRIMARY GATE. A rule the precise path declines to wake is one that
    could not have progressed — so the final graph must be identical, node ids,
    edges, float bits and all."""
    fn = WORKLOADS[wl]
    over, precise = fn(False), fn(True)
    assert over == precise, f"{wl}: precise-dirty CHANGED the graph"


@pytest.mark.parametrize("wl", sorted(WORKLOADS))
def test_the_WRONG_precision_predicate_BREAKS_byte_identity(wl):
    """THE FALSIFIER that makes the gate above non-vacuous. Drop the `reads_any`
    and `Type` disjuncts — an over-aggressive predicate that skips genuinely
    dirty rules — and the graph MUST diverge. If this ever passes silently, the
    byte-identity claim above proves nothing."""
    fn = WORKLOADS[wl]
    good, bad = fn(True), fn(True, wrong=True)
    assert good != bad, (
        f"{wl}: the over-aggressive predicate did NOT diverge — the "
        "byte-identity gate is vacuous on this workload")


def test_a_noop_write_dirties_NOTHING_under_precision_and_the_graph_is_unchanged():
    """VALUE-LEVEL precision. Writing the value that is already stored cannot
    change any binding or any where-clause, so it must wake nobody — and the
    graph must be bit-identical to not having written at all."""
    for precise in (False, True):
        agent = _chain_agent(precise=precise)
        s = agent.s.add_node("Src0", {"level": 7.0})
        t = agent.s.add_node("Tgt0", {"level": 0.0})
        agent.inner.add_edge_unchecked(s, "e_g0_0", t)
        agent.inner.run_rules()
        before = _dump(agent.inner)
        agent.inner.set_dirty_telemetry(True)
        agent.inner.reset_dirty_marks()
        agent.s.set_attr(s, "level", 7.0)          # THE SAME VALUE
        marks = agent.inner.dirty_marks()
        dirty = agent.inner.dirty_rule_count()
        after = _dump(agent.inner)
        assert before == after, "a same-value write must leave the graph identical"
        assert marks["noop_attr_writes"] == 1
        if precise:
            assert marks["external"] == 0, "no-op write must wake NOBODY"
            assert dirty == 0, "no-op write must leave zero dirty rules"
        else:
            assert marks["external"] > 0, (
                "the committed blanket wakes every where-rule even on a no-op "
                "— this is the control that makes the skip meaningful")


def test_a_CHANGING_write_wakes_FEWER_rules_under_precision_but_still_wakes_the_readers():
    """THE MECHANISM CLAIM. A write of one attr key must wake strictly fewer
    rules than the blanket, and must still wake every rule that reads that key
    through a where-clause."""
    marks = {}
    for precise in (False, True):
        agent = _chain_agent(precise=precise)
        s = agent.s.add_node("Src0", {"level": 0.0})
        t = agent.s.add_node("Tgt0", {"level": 0.0})
        agent.inner.add_edge_unchecked(s, "e_g0_0", t)
        agent.inner.run_rules()
        agent.inner.set_dirty_telemetry(True)
        agent.inner.reset_dirty_marks()
        agent.s.set_attr(s, "level", 99.0)         # a REAL change
        marks[precise] = agent.inner.dirty_marks()["external"]
        # The four `guard_g*` rules read Attr("level") in a where-clause; they
        # are exactly the rules that MUST wake.
        assert agent.inner.dirty_rule_count() >= 4
    assert marks[True] < marks[False], (
        f"precise woke {marks[True]}, blanket woke {marks[False]} — precision "
        "must be a STRICT reduction on this workload")


def test_NO_FREE_LUNCH_when_every_rule_reads_what_was_written():
    """When nothing can be skipped, precision must not pretend to skip. Every
    rule here reads the written key in a where-clause, so the precise mark count
    must EQUAL the blanket's."""
    marks = {}
    for precise in (False, True):
        agent = WorldAdapter(seeds=())
        agent.inner.set_precise_dirty(precise)
        s = agent.s.add_node("NflSrc", {"v": 0.0})
        t = agent.s.add_node("NflTgt", {"v": 0.0})
        agent.inner.add_edge_unchecked(s, "nfl_edge", t)
        for i in range(16):
            agent.inner.add_rule({
                "name": f"nfl_{i}",
                "match": [["s", "nfl_edge", "t"]],
                "where": {"type": "Gt",
                          "a": {"type": "Attr",
                                "node": {"type": "Var", "name": "s"}, "key": "v"},
                          "b": {"type": "Lit", "value": 1e18}},
                "effects": [["set_attr_if_different", "t", "v", 1.0]],
            })
        agent.inner.run_rules()
        agent.inner.set_dirty_telemetry(True)
        agent.inner.reset_dirty_marks()
        agent.s.set_attr(s, "v", 1.0)
        marks[precise] = agent.inner.dirty_marks()["external"]
    assert marks[True] == marks[False] == 16, (
        f"precise={marks[True]} blanket={marks[False]} — with every rule "
        "reading the written key there is NOTHING to skip")


def test_ONE_SHARED_ATTRIBUTE_KEEPS_EVERY_AREA_AWAKE_the_rungs_NEGATIVE():
    """THE RUNG'S NEGATIVE, pinned at the mechanism grain.

    On the real eye all six areas stay dirty on every photon tick even under
    precision, because eight rules across those six areas all read ONE attribute
    key — `input_epoch`, the shared epoch stamp — and one write to it wakes them
    all. KEY-level precision cannot break that; only INSTANCE-level could (no
    rule reads `input_epoch` on the node the write lands on).

    This reproduces that shape synthetically: N areas, one rule each, all
    reading the SAME key through a where-clause, and one write on a node no rule
    matches. Every area wakes, under precision, by construction."""
    agent = WorldAdapter(seeds=())
    agent.inner.set_precise_dirty(True)
    areas = [f"area{i}" for i in range(6)]
    for i, a in enumerate(areas):
        agent.inner.add_rule({
            "name": f"reader_{i}", "area": a,
            "match": [["s", "shared_edge", "t"]],
            "where": {"type": "Gt",
                      "a": {"type": "Attr", "node": {"type": "Var", "name": "s"},
                            "key": "epoch_stamp"},
                      "b": {"type": "Lit", "value": 1e18}},
            "effects": [["set_attr_if_different", "t", f"seen{i}", 1.0]],
        })
    s = agent.s.add_node("SharedSrc", {"epoch_stamp": 0.0})
    t = agent.s.add_node("SharedTgt", {})
    agent.inner.add_edge_unchecked(s, "shared_edge", t)
    # A node NO rule matches on — the analogue of the retina ROOT.
    root = agent.s.add_node("UnmatchedRoot", {"epoch_stamp": 0.0})
    agent.inner.run_rules()
    assert agent.inner.dirty_rule_count() == 0
    # ONE write, of a key every area reads, on a node no rule reads it ON.
    agent.s.set_attr(root, "epoch_stamp", 1.0)
    woke = agent.inner.dirty_area_names()
    assert sorted(woke) == sorted(areas), (
        f"expected every area awake from ONE shared-key write, got {woke}")
    assert agent.inner.dirty_rule_count() == len(areas)
    # And the reason is nameable: every one of them reads that key.
    readers = {r for r, _a in agent.inner.rules_reading_attr("epoch_stamp")}
    assert readers == {f"reader_{i}" for i in range(len(areas))}


def test_term_rs_carries_NONE_of_this_rung():
    """NO new Term enum variant. The rung is an engine method + PyO3 only."""
    src = open(os.path.join(ROOT, "runners", "dsl", "src", "term.rs")).read()
    for token in ("precise_dirty", "mark_external_write", "dirty_overaggressive",
                  "dirty_marks"):
        assert token not in src, f"term.rs mentions {token} — this rung must not touch it"
