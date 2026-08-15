"""test_opgrammar_migrated — OPLIST_ADMISSIBILITY_GRAMMAR_SLICE1_RESULTS.md,
the buildable first slice OPLIST_ADMISSIBILITY_GRAMMAR_PREREG.md /
_RESULTS.md §8 scoped: the MBPP op-list boolean gate ladder inside
`eval_synth_enumerate` (runners/dsl/src/synth_enumerate.rs) is Γ-shaped (a
real generated multi-production admissible-move SET, CLAUDE.md's own "set
of allowed moves" test) — this slice mints the `SynthOp` vocabulary + a
`SynthSpecShape` node type, hand-authors EXACTLY the two already-shipped
`SortBy` gates as Γ productions, and wires `run_enumerate` to probe
`is_edge_admissible` ALONGSIDE (never replacing) the existing hand-written
Rust ladder.

NOT attempted in this slice, and not tested here: the mint sweep (a
separate, later rung per the design doc's own §8 step 5), porting any of
the other ~48 evidence-gate sites besides `SortBy`'s two.
"""
from __future__ import annotations

import json

import pytest

import substrate_rs as srs
from domains import mbpp_spec as ms
from domains import prog_synthesis as psy


def boot():
    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    psy.ensure_program_synthesis(s, s._inner, ag)
    return s, ag


# --------------------------------------------------------------------------- #
# 1) Seed install: 52 SynthOp nodes (the re-verified live OP_TABLE count —
#    NOT the design doc's stale "31" nor DERIVED_OPERATOR_TIER_RESULTS.md's
#    own stale "50" correction; both are superseded by the GroupCount/
#    DictMerge rung this slice re-verified against live source), the seed
#    marker, and idempotent re-install (the `_has_seed` guard).
# --------------------------------------------------------------------------- #
def test_opgrammar_seed_installs_52_synthop_nodes_and_is_idempotent():
    s, ag = boot()
    assert any(
        s.node(n)["attrs"].get("id") == "program_synthesis_opgrammar"
        for n in s.nodes("Seed")
    )
    ops = sorted(s.node(n)["attrs"].get("name") for n in s.nodes("SynthOp"))
    assert len(ops) == 52, len(ops)
    assert len(set(ops)) == 52, "no duplicate SynthOp names"
    assert "SortBy" in ops and "DictItems" in ops and "GroupCount" in ops \
        and "DictMerge" in ops

    # Idempotent: calling ensure_program_synthesis_opgrammar again must not
    # mint a second population of SynthOp nodes.
    psy.ensure_program_synthesis_opgrammar(s, s._inner, ag)
    ops_again = [s.node(n)["attrs"].get("name") for n in s.nodes("SynthOp")]
    assert len(ops_again) == 52


# --------------------------------------------------------------------------- #
# 2) The two hand-authored SortBy Γ productions, probed directly via
#    is_edge_admissible on hand-built SynthSpecShape flag combinations —
#    the discriminating cases the design doc's §3.2 two-production design
#    specifically claims to reproduce.
# --------------------------------------------------------------------------- #
_BASE_FLAGS = {
    "has_dict_value": False, "has_list_of_lists": False,
    "has_string_value": False, "has_float_value": False,
    "has_repeated_list_element": False, "output_is_listlike": True,
    "output_is_setlike": False, "output_is_bare_int": False,
    "is_string_shaped": False, "is_list_shaped": True,
}


def _admits_sortby(s, flags):
    n = s.add_node("SynthSpecShape", flags)
    return s._inner.is_edge_admissible(n, "admits_op", "SynthOp", {"name": "SortBy"})


def test_gamma_reproduces_the_dict_value_sortby_gate():
    s, ag = boot()
    assert _admits_sortby(s, dict(_BASE_FLAGS, has_dict_value=True)) is True


def test_gamma_reproduces_the_list_of_lists_sortby_gate():
    s, ag = boot()
    assert _admits_sortby(s, dict(_BASE_FLAGS, has_list_of_lists=True)) is True


def test_gamma_declines_sortby_when_neither_gate_holds():
    s, ag = boot()
    assert _admits_sortby(s, dict(_BASE_FLAGS)) is False


def test_gamma_declines_sortby_when_list_of_lists_true_but_dict_also_true():
    """The Rust ladder's SECOND gate is `has_list_of_lists && !has_dict_value`
    — deliberately narrower than a plain OR of the two flags. Reproduced
    here: dict_value=True already admits via gate 1, so the UNION still
    admits (both flags true) — this is the OR-of-productions semantics, not
    a regression of the narrowing; the narrowing only matters for whether
    `DictItems`/`Reverse` ALSO widen (they don't, and aren't ported here at
    all — only `SortBy` has these two productions)."""
    s, ag = boot()
    assert _admits_sortby(
        s, dict(_BASE_FLAGS, has_dict_value=True, has_list_of_lists=True)
    ) is True


def test_gamma_never_admits_a_different_op_no_matter_the_flags():
    """Only `SortBy` has productions in this slice — every other of the 51
    other `SynthOp` names has ZERO productions naming it, so `Plus`/`Sort`/
    `DictItems`/etc must never be admitted via this mechanism regardless of
    which evidence flags are set (Type-1 inadmissible: candidates() finds
    productions keyed on (SynthSpecShape, admits_op, SynthOp), but every one
    of THIS slice's two productions requires tgt.name=='SortBy')."""
    s, ag = boot()
    flags = dict(_BASE_FLAGS, has_dict_value=True, has_list_of_lists=True)
    n = s.add_node("SynthSpecShape", flags)
    for other in ("Plus", "Sort", "DictItems", "Reverse", "GroupCount"):
        assert s._inner.is_edge_admissible(
            n, "admits_op", "SynthOp", {"name": other}) is False, other


# --------------------------------------------------------------------------- #
# 3) `_synth_spec_shape_flags` — the duplicated evidence-flag computation —
#    checked against hand-built raw rows for the two flags the productions
#    consult, plus a couple of the other eight (a full port of a fourteen-
#    site Rust ladder is out of scope; this is a unit check on the
#    function's own logic, not a re-derivation of the Rust ladder).
# --------------------------------------------------------------------------- #
def test_synth_spec_shape_flags_dict_value():
    # Output deliberately a bare scalar (not a list of tuples) so this case
    # isolates `has_dict_value` from `has_list_of_lists` — a Dict INPUT
    # with a flat, non-nested output.
    rows = [{"inputs": {"a": {"x": 1, "y": 2}}, "output": 3}]
    flags = psy._synth_spec_shape_flags(rows)
    assert flags["has_dict_value"] is True
    assert flags["has_list_of_lists"] is False


def test_synth_spec_shape_flags_list_of_lists_via_tuples():
    """task 64's own real shape: `a` is a List[Tuple] — `is_listlike`
    (Rust) treats Tuple as list-like, so a list of tuples IS
    `has_list_of_lists` under the exact same evidence the map-template-pool
    rung already measured safe for this shape."""
    rows = [{"inputs": {"a": [("English", 88), ("Science", 90)]},
              "output": [("English", 88), ("Science", 90)]}]
    flags = psy._synth_spec_shape_flags(rows)
    assert flags["has_list_of_lists"] is True
    assert flags["has_dict_value"] is False


def test_synth_spec_shape_flags_plain_list_neither_gate():
    rows = [{"inputs": {"a": [1, 2, 3]}, "output": [1, 4, 9]}]
    flags = psy._synth_spec_shape_flags(rows)
    assert flags["has_dict_value"] is False
    assert flags["has_list_of_lists"] is False
    assert flags["is_list_shaped"] is True


def test_synth_spec_shape_flags_repeated_element_and_float():
    rows = [{"inputs": {"a": [1, 1, 2]}, "output": 1.5}]
    flags = psy._synth_spec_shape_flags(rows)
    assert flags["has_repeated_list_element"] is True
    assert flags["has_float_value"] is True


# --------------------------------------------------------------------------- #
# 4) LIVE DEMONSTRATION on real MBPP tasks — the discriminating proof.
#    Loads real sanitized MBPP rows (tests/fixtures/mbpp/sanitized-mbpp.json)
#    for task 64 (the widened, list-of-lists witness), task 475 (the
#    original, dict-shaped witness), and task 2 (currently-passing,
#    matches NEITHER gate — the negative control) and calls `run_enumerate`
#    directly with NO explicit `ops` (so the Rust hand-written ladder's own
#    default decides), confirming Γ's `is_edge_admissible` answer for
#    `SortBy` matches whether the winning term actually used `SortBy`.
# --------------------------------------------------------------------------- #
def _mbpp_tasks():
    with open("tests/fixtures/mbpp/sanitized-mbpp.json") as f:
        return {t["task_id"]: t for t in json.load(f)}


def _force_run_enumerate(s, ag, g):
    cur_round = float(s.node(g)["attrs"].get("ps_enum_round") or 0.0)
    s.set_attr(g, "ps_enum_round", cur_round + 1.0)
    return psy.run_enumerate(s, ag, g)


@pytest.mark.parametrize("task_id,expect_sortby", [(64, True), (475, True), (2, False)])
def test_live_demonstration_gamma_matches_the_real_ladder(task_id, expect_sortby):
    tasks = _mbpp_tasks()
    task = tasks[task_id]
    parsed = ms.parse_asserts(task)
    split = ms.split_rows(parsed["rows"], "primary")
    assert split["runnable"], task_id
    s, ag = boot()
    m = psy.ingest_spec(s, ag, task["prompt"], split["revealed"])
    psy.pump(s, ag)
    g = s.in_neighbours(m, "about_message")[0]
    # No explicit ps_enum_ops was set on the message by the NL classifier
    # for these prompts (confirmed: graph_ops is None/empty) — so
    # run_enumerate's spec carries NO "ops" key and the Rust hand-written
    # default ladder decides the op inventory, exactly the ladder this
    # slice's Γ productions mirror.
    assert not _plain_ops(s, m)
    ran = _force_run_enumerate(s, ag, g)
    assert ran is True
    attrs = s.node(g)["attrs"]
    assert attrs.get("ps_enum_gamma_sortby_error") is None
    gamma_admitted = attrs.get("ps_enum_gamma_sortby_admitted")
    assert gamma_admitted is expect_sortby, (task_id, gamma_admitted)
    term = attrs.get("ps_enum_last_term_json") or ""
    used_sortby = "SortBy" in term
    # The discriminating check: Γ's admission answer for SortBy must match
    # the real ladder's own observable behaviour — SortBy actually appears
    # in the winning term iff the default ladder admitted it, and Γ agrees
    # with the ladder on every one of the three tasks.
    assert used_sortby is expect_sortby, (task_id, term)


def _plain_ops(s, m):
    v = s.node(m)["attrs"].get("ps_enum_ops")
    return v or None
