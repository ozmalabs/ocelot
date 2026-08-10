"""FIXPOINT SETTLE — the engine defect, and the POSITIVE CONTROL for the
instrument that found it.

Two independent things are gated here.

1. `run_rules` must not return over unsettled state. The engine reproduction
   lives in Rust (`substrate.rs::run_rules_returns_over_unsettled_state_
   when_attr_write_follows_structural_dirty`), but `cargo test` cannot link
   this crate under its default flags (pyo3 `extension-module`; recorded twice
   in VISION_PROTOCOL.md as pre-existing). So the same shape is gated HERE,
   through the shipped engine, where it actually runs in CI.

2. `assert_settled` (`domains/motion_group_world.py`) is POSITIVE-CONTROLLED.
   It fired once, on its first firing, and then discarded 0 of 160 runs. That
   is exactly the shape of a check that has stopped being ABLE to fire, and
   "0/160" means nothing until the check is shown to go red on a field that IS
   unsettled. These tests construct that field.
"""
import math

import pytest

from substrate.boot_core import boot_core, load_seeds_into
import domains.motion_group_world as mgw


# --------------------------------------------------------------------------
# 1. THE ENGINE DEFECT — run_rules must not report a fixed point over
#    unsettled state.
# --------------------------------------------------------------------------

def _settle_graph(s, *, pre_open_gate: bool, with_churn: bool = True):
    """The minimal three-rule shape, built through the shipped engine.

        chain:  s1 -[step]-> s2 -[step]-> s3
        gate:   s3 -[gate]-> n1
        link:   n1 -[link]-> n2          (STABLE — never added to)

        churn     : ?a -[step]-> ?b  where ?a.on == 1
                    => ?b.on = 1 ; add ?b -[tag]-> ?b
        open_gate : ?p -[gate]-> ?q  where ?p.on == 1  => ?q.go = 1
        consume   : ?x -[link]-> ?y  where ?x.go == 1 && |tag(?x)| == 0
                    => mint Marker

    `consume` reads Edge(tag), so `churn` dirties it STRUCTURALLY (correctly
    leaving its semi-naive cursor intact). `open_gate` then writes Attr(go) in
    the SAME pass, when `consume` is already dirty. Before the fix,
    `dirty_by_writeset` skipped it and never cleared its cursor, so `consume`
    enumerated zero on its stable `link` edge and never saw the flip.
    """
    s.add_production({
        "provenance": "test:fixpoint_settle",
        "src": {"type": "N", "var": "a"},
        "edge_type": "tag",
        "tgt": {"type": "N", "var": "b"},
    })

    def _attr(var, key):
        return {"type": "Attr", "node": {"type": "Var", "name": var}, "key": key}

    s._inner.load_seed_manifest({
        "id": "fixpoint_settle_probe",
        "version": "1.0.0",
        "depends_on": [],
        "rules": ([] if not with_churn else [
            {
                "name": "fs_churn",
                "match": [["a", "step", "b"]],
                "where": {"type": "Eq", "a": _attr("a", "on"),
                          "b": {"type": "Lit", "value": 1.0}},
                "effects": [
                    ["set_attr_if_different", "b", "on", 1.0],
                    ["add_edge", "b", "tag", "b"],
                ],
            },
        ]) + [
            {
                "name": "fs_open_gate",
                "match": [["p", "gate", "q"]],
                "where": {"type": "Eq", "a": _attr("p", "on"),
                          "b": {"type": "Lit", "value": 1.0}},
                "effects": [["set_attr_if_different", "q", "go", 1.0]],
            },
            {
                "name": "fs_consume",
                "match": [["x", "link", "y"]],
                "where": {"type": "And", "items": [
                    {"type": "Eq", "a": _attr("x", "go"),
                     "b": {"type": "Lit", "value": 1.0}},
                    {"type": "Eq",
                     "a": {"type": "Count", "source": {
                         "type": "Neighbours",
                         "node": {"type": "Var", "name": "x"},
                         "edge_type": "tag"}},
                     "b": {"type": "Lit", "value": 0.0}},
                ]},
                "effects": [["add_node_if_absent", "m", "Marker", {"go": 1.0}]],
            },
        ],
    })

    s1 = s.add_node("N", {"on": 1})
    s2 = s.add_node("N", {})
    s3 = s.add_node("N", {})
    n1 = s.add_node("N", {"go": 1} if pre_open_gate else {})
    n2 = s.add_node("N", {})

    s.add_edge_unchecked(s1, "step", s2)
    s.add_edge_unchecked(s2, "step", s3)
    s.add_edge_unchecked(s3 if with_churn else s1, "gate", n1)
    s.add_edge_unchecked(n1, "link", n2)
    return n1


@pytest.mark.parametrize("pre_open_gate", [False, True])
def test_run_rules_reaches_a_real_fixed_point(pre_open_gate):
    """A settled `run_rules` must be IDEMPOTENT: running it again does nothing.

    That is the whole contract, and it is checkable without knowing anything
    about the rules — which is why it is the right gate. Before the fix, the
    non-pre-opened arm returned a "fixed point" with work outstanding.
    """
    s, ag = boot_core()
    n1 = _settle_graph(s, pre_open_gate=pre_open_gate)

    s._inner.run_rules(1000)
    before = len(s.nodes("Marker"))
    extra_steps = s._inner.run_rules(1000)
    after = len(s.nodes("Marker"))

    assert extra_steps == 0, (
        f"run_rules returned claiming a fixed point, but a second call made "
        f"{extra_steps} further steps — it had not settled"
    )
    assert before == after == 1, (
        f"consume's where-clause is TRUE on n1 -[link]-> n2 "
        f"(go={s.node(n1)['attrs'].get('go')}) and must have fired exactly "
        f"once; got {before} Markers, {after} after a re-run"
    )


# --------------------------------------------------------------------------
# 2. THE INSTRUMENT'S POSITIVE CONTROL — assert_settled must be ABLE to fire.
# --------------------------------------------------------------------------

def _settled_field():
    """A small real motion field, run to its fixpoint through the real seed."""
    vf = [[[0.0, 0.0] for _ in range(4)] for _ in range(4)]
    for r in range(4):
        for c in range(4):
            # two coherent groups, well separated in velocity
            vf[r][c] = [3.0, 0.0] if c < 2 else [0.0, 3.0]
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_motion_group"])
    h = mgw.add_mfield(s, vf)
    mgw.settle(s, marm=1.0, mcontrast=1.0, mtol_exact=0.0, max_steps=200_000)
    return s, h


def test_assert_settled_passes_on_a_genuinely_settled_field():
    """P2 — the check must NOT false-positive. Without this, a check that
    always returns red would 'pass' the positive control below."""
    s, h = _settled_field()
    chk = mgw.assert_settled(s, h)
    assert chk["cells_without_tolerance"] == 0, chk
    assert chk["unsettled_pairs"] == 0, chk


def test_assert_settled_GOES_RED_on_an_unsettled_flood():
    """P1a — POSITIVE CONTROL on limb (b). Plant the exact defect the motion
    rung observed: a cell retaining an admissible neighbour that carries a
    SMALLER label. The check must count it."""
    s, h = _settled_field()
    assert mgw.assert_settled(s, h)["unsettled_pairs"] == 0

    # Raise one cell's label above its (velocity-identical, hence admissible)
    # right-hand neighbour — precisely a half-propagated flood.
    idx = h["index"]
    victim = idx[(0, 0)]
    neighbour_label = float(s.node(idx[(1, 0)])["attrs"].get("mlabel", -1.0))
    s.set_attr(victim, "mlabel", neighbour_label + 10.0)

    chk = mgw.assert_settled(s, h)
    assert chk["unsettled_pairs"] > 0, (
        "assert_settled is a DEAD INSTRUMENT: a cell with an admissible "
        f"neighbour carrying a smaller label was not counted — {chk}"
    )


def test_assert_settled_GOES_RED_when_the_tolerance_broadcast_missed_a_cell():
    """P1b — POSITIVE CONTROL on limb (a). The broadcast failing to reach a
    cell is the OTHER thing the check claims to detect, and it is the one that
    made the flood silently run under exact equality."""
    s, h = _settled_field()
    assert mgw.assert_settled(s, h)["cells_without_tolerance"] == 0

    s.set_attr(h["index"][(2, 3)], "mtol_done", 0.0)

    chk = mgw.assert_settled(s, h)
    assert chk["cells_without_tolerance"] > 0, (
        "assert_settled is a DEAD INSTRUMENT on its tolerance limb: a cell "
        f"with mtol_done=0 was not counted — {chk}"
    )


def test_two_rules_alone_do_NOT_reproduce_the_defect():
    """THE DISCRIMINATOR — the defect REQUIRES the third rule.

    With `fs_churn` removed, `fs_open_gate`'s attr write is the ONLY thing that
    touches `fs_consume`, which is therefore CLEAN at that moment — so
    `dirty_by_writeset` reaches the cursor-clear and `fs_consume` re-matches
    fully. It settles even on the PRE-FIX engine.

    This is what bounds the condition. The bare "stable-edge attr-gated" story
    is NOT sufficient: the `dirty_by_writeset` mitigation genuinely closes it.
    What leaks is specifically the THREE-RULE INTRA-PASS RACE, where a
    STRUCTURAL dirty from a third rule arrives FIRST and makes the consumer
    already-dirty when the attr write lands.
    """
    s, ag = boot_core()
    n1 = _settle_graph(s, pre_open_gate=False, with_churn=False)
    s._inner.run_rules(1000)
    assert s.node(n1)["attrs"].get("go") == 1.0, "precondition: gate opened"
    assert len(s.nodes("Marker")) == 1, (
        "two rules alone must settle — if this fails, the condition is broader "
        "than the three-rule race and the results doc is wrong"
    )
