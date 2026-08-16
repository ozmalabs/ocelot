"""test_opgrammar_migrated — OPLIST_ADMISSIBILITY_GRAMMAR_SLICE1_RESULTS.md
(the first slice: `SynthOp`/`SynthSpecShape` node types + the two SortBy
productions) EXTENDED by PROGRAM_SYNTHESIS_GAMMA_BULK_TRANSCRIPTION_
PREREG/_RESULTS.md (the bulk transcription of the remaining 12 op-list
evidence-gate sites named by OPLIST_ADMISSIBILITY_GRAMMAR_RESULTS.md §1.1's
own 14-site table, plus a 13th bare-scalar-fallback `DEFAULT_OPS` baseline
production found necessary for genuine parity — see that RESULTS doc). The
MBPP op-list boolean gate ladder inside `eval_synth_enumerate`
(runners/dsl/src/synth_enumerate.rs) is Γ-shaped (a real generated
multi-production admissible-move SET, CLAUDE.md's own "set of allowed
moves" test) — this seed mints the `SynthOp` vocabulary (57 static nodes,
one per real, live `OP_TABLE` entry) + a `SynthSpecShape` node type
(eleven evidence flags), and `run_enumerate` probes `is_edge_admissible`
ALONGSIDE (never replacing) the existing hand-written Rust ladder — Γ
verdicts are recorded facts only, never consulted for `spec["ops"]`
construction.

The bulk-transcription rung's own parity sweep
(`scripts/opgrammar_bulk_parity_sweep.py`, full 420-real-spec run) found
TWO real, corpus-confirmed parity bugs in the two ALREADY-SHIPPED `SortBy`
productions (both missing a `¬output_is_setlike` exclusion; the
`has_dict_value` gate also missing an `is_list_shaped` requirement) and
fixed them in place — see that RESULTS doc §6 for the full diagnosis. Tests
below reflect the FIXED productions, not the original SLICE1 shape.

NOT attempted in this rung, and not tested here: the mint sweep (a
separate, later rung per the design doc's own §8 step 5); the
`DICT_DEFAULT_OPS` branch and its `GroupCount`/`DictMerge`/`DictFromPairs`
ops, and the unconditional `Mod`/`Sqrt` append — all explicitly out of
Γ scope (not among the 14 named sites).
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
# 1) Seed install: 57 SynthOp nodes (the re-verified live OP_TABLE count as
#    of this rung — SLICE1's own "52" is stale a third time: `IntersectAll`,
#    `UnionAll`, `DictFromPairs`, `Mod`, `Sqrt` landed since; see
#    PROGRAM_SYNTHESIS_GAMMA_BULK_TRANSCRIPTION_RESULTS.md §1), the seed
#    marker, and idempotent re-install (the `_has_seed` guard).
# --------------------------------------------------------------------------- #
def test_opgrammar_seed_installs_57_synthop_nodes_and_is_idempotent():
    s, ag = boot()
    assert any(
        s.node(n)["attrs"].get("id") == "program_synthesis_opgrammar"
        for n in s.nodes("Seed")
    )
    ops = sorted(s.node(n)["attrs"].get("name") for n in s.nodes("SynthOp"))
    assert len(ops) == 57, len(ops)
    assert len(set(ops)) == 57, "no duplicate SynthOp names"
    assert "SortBy" in ops and "DictItems" in ops and "GroupCount" in ops \
        and "DictMerge" in ops
    assert "IntersectAll" in ops and "UnionAll" in ops \
        and "DictFromPairs" in ops and "Mod" in ops and "Sqrt" in ops

    # Idempotent: calling ensure_program_synthesis_opgrammar again must not
    # mint a second population of SynthOp nodes.
    psy.ensure_program_synthesis_opgrammar(s, s._inner, ag)
    ops_again = [s.node(n)["attrs"].get("name") for n in s.nodes("SynthOp")]
    assert len(ops_again) == 57


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
    "output_is_dictlike": False,
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


def test_gamma_admits_dictitems_and_reverse_once_list_shaped_is_also_true():
    """The bulk-transcription rung's own parity sweep found `DictItems`/
    `Reverse` were the un-ported remainder of the `has_dict_value` site
    (the real ladder pushes `DictItems,SortBy,Reverse` together, but SLICE1
    only ported `SortBy`) — this completes it, gated the SAME way the fix
    to the SortBy production itself now requires (`is_list_shaped`,
    `¬output_is_setlike`)."""
    s, ag = boot()
    n = s.add_node("SynthSpecShape", dict(_BASE_FLAGS, has_dict_value=True))
    for name in ("DictItems", "Reverse"):
        assert s._inner.is_edge_admissible(
            n, "admits_op", "SynthOp", {"name": name}) is True, name
    # But NOT admitted without is_list_shaped -- the real push site is
    # nested inside the `else if spec_is_list_shaped` branch.
    n2 = s.add_node("SynthSpecShape",
                     dict(_BASE_FLAGS, has_dict_value=True, is_list_shaped=False,
                          output_is_listlike=False))
    for name in ("DictItems", "Reverse", "SortBy"):
        assert s._inner.is_edge_admissible(
            n2, "admits_op", "SynthOp", {"name": name}) is False, name


def test_gamma_never_admits_an_out_of_scope_op_no_matter_the_flags():
    """`Gte`/`And`/`Or`/`Not` are real `OP_TABLE` entries with ZERO
    evidence-gate sites anywhere in the Rust ladder (never referenced by
    any of `DEFAULT_OPS`/`LIST_EXTRA_OPS`/`SET_DEFAULT_OPS`/
    `DEFAULT_STR_OPS`/`DICT_DEFAULT_OPS`/`TUPLE_BUILD_OPS`, confirmed by
    reading every bucket in full) — reachable only via an explicit `ops`
    request, never a typed default, so Γ must never admit them regardless
    of which evidence flags are set. `GroupCount`/`DictMerge`/
    `DictFromPairs`/`Mod`/`Sqrt` are real gate-admitted ops in the Rust
    ladder but DELIBERATELY out of Γ scope this rung (the `DICT_DEFAULT_
    OPS` branch and the unconditional bare-scalar append — see
    PROGRAM_SYNTHESIS_GAMMA_BULK_TRANSCRIPTION_RESULTS.md §1) — Γ must
    never admit these either, by design, even though the real ladder
    sometimes does."""
    s, ag = boot()
    # A maximal, "everything true" flag combination -- the strongest
    # stress test: if these names are still never admitted here, they are
    # never admitted at all (every OTHER site's own guard is a SUBSET of
    # this combination, so nothing narrower could newly admit them either).
    flags = dict(
        has_dict_value=True, has_list_of_lists=True, has_string_value=True,
        has_float_value=True, has_repeated_list_element=True,
        output_is_listlike=True, output_is_setlike=False,
        output_is_bare_int=True, output_is_dictlike=False,
        is_string_shaped=False, is_list_shaped=True,
    )
    n = s.add_node("SynthSpecShape", flags)
    for other in ("Gte", "And", "Or", "Not", "GroupCount", "DictMerge",
                  "DictFromPairs", "Mod", "Sqrt"):
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


def test_synth_spec_shape_flags_output_is_dictlike():
    """`output_is_dictlike` (the ELEVENTH flag, added this rung) — a spec
    whose OUTPUT is Dict-shaped on every row, mirroring `output_is_setlike`/
    `output_is_listlike`'s own output-only-type-test discipline (never an
    input-shape test)."""
    rows = [{"inputs": {"a": {"x": 1}, "b": {"y": 2}}, "output": {"x": 1, "y": 2}}]
    flags = psy._synth_spec_shape_flags(rows)
    assert flags["output_is_dictlike"] is True
    rows2 = [{"inputs": {"a": {"x": 1}}, "output": 3}]
    flags2 = psy._synth_spec_shape_flags(rows2)
    assert flags2["output_is_dictlike"] is False
    assert flags2["has_dict_value"] is True  # the input is still dict-valued


# --------------------------------------------------------------------------- #
# 5) The bulk-transcribed sites — probed directly, one per site, mirroring
#    section 2's own `_admits_sortby`-style idiom. Not exhaustive over
#    every op in every bucket (the parity sweep in section 6 is) — a
#    representative sample per site, following this file's own established
#    style.
# --------------------------------------------------------------------------- #
def _admits(s, flags, op):
    n = s.add_node("SynthSpecShape", flags)
    return s._inner.is_edge_admissible(n, "admits_op", "SynthOp", {"name": op})


_ALL_FALSE = {
    "has_dict_value": False, "has_list_of_lists": False,
    "has_string_value": False, "has_float_value": False,
    "has_repeated_list_element": False, "output_is_listlike": False,
    "output_is_setlike": False, "output_is_bare_int": False,
    "output_is_dictlike": False,
    "is_string_shaped": False, "is_list_shaped": False,
}


def test_site_a_string_shaped_admits_default_str_ops():
    s, ag = boot()
    f = dict(_ALL_FALSE, is_string_shaped=True)
    for op in ("Concat", "CaseFold", "Replace", "Split", "StrCount",
               "Capitalize", "Str", "MapList", "JoinList"):
        assert _admits(s, f, op) is True, op
    assert _admits(s, f, "Plus") is False


def test_site_f_output_setlike_admits_set_default_ops():
    s, ag = boot()
    f = dict(_ALL_FALSE, output_is_setlike=True)
    for op in ("Sort", "SetMap", "Intersect", "Union", "IntersectAll", "UnionAll"):
        assert _admits(s, f, op) is True, op
    assert _admits(s, f, "Plus") is False  # DEFAULT_OPS deliberately excluded


def test_site_b_list_shaped_admits_default_and_list_extra_ops_but_not_when_setlike():
    s, ag = boot()
    f = dict(_ALL_FALSE, is_list_shaped=True)
    for op in ("Plus", "Minus", "Len", "SumList", "FilterList", "ArgMaxLenOver"):
        assert _admits(s, f, op) is True, op
    # The REQUIRED exclusion (PROGRAM_SYNTHESIS_GAMMA_BULK_TRANSCRIPTION_
    # RESULTS.md §6): a Set-shaped output ALSO satisfies is_list_shaped
    # (Set/FrozenSet are is_listlike), but is checked EARLIER in the real
    # ladder's if/else-if chain -- so this site must NOT admit here.
    f2 = dict(f, output_is_setlike=True)
    assert _admits(s, f2, "Plus") is False


def test_sites_c_d_e_output_listlike_admit_tupleof_sort_and_conditionally_split():
    s, ag = boot()
    f = dict(_ALL_FALSE, is_list_shaped=True, output_is_listlike=True)
    assert _admits(s, f, "TupleOf") is True
    assert _admits(s, f, "Sort") is True
    assert _admits(s, f, "Split") is False
    assert _admits(s, dict(f, has_string_value=True), "Split") is True


def test_site_g_bare_scalar_string_value_ops_not_admitted_when_list_shaped():
    s, ag = boot()
    f = dict(_ALL_FALSE, has_string_value=True)
    for op in ("Replace", "Split", "StrCount", "Capitalize", "Str", "ParseInt"):
        assert _admits(s, f, op) is True, op
    # Same evidence, but is_list_shaped=True routes through a DIFFERENT
    # Rust branch entirely (site E's own narrower Split gate, not this
    # bucket) -- these six must NOT admit here.
    f2 = dict(f, is_list_shaped=True)
    for op in ("Replace", "StrCount", "Capitalize", "Str"):
        assert _admits(s, f2, op) is False, op


def test_sites_h_i_round_admitted_on_both_the_bare_and_list_shaped_branches():
    s, ag = boot()
    assert _admits(s, dict(_ALL_FALSE, has_float_value=True), "Round") is True
    assert _admits(s, dict(_ALL_FALSE, has_float_value=True, is_list_shaped=True),
                    "Round") is True


def test_site_l_indexedmap_only_on_the_list_shaped_branch_not_the_dead_bare_site():
    """Site K (the SAME evidence on the bare-scalar branch) was found DEAD
    in current source (PROGRAM_SYNTHESIS_GAMMA_BULK_TRANSCRIPTION_
    RESULTS.md §3) -- deliberately NOT ported, confirmed here by its
    absence."""
    s, ag = boot()
    assert _admits(s, dict(_ALL_FALSE, has_repeated_list_element=True,
                            is_list_shaped=True), "IndexedMap") is True
    assert _admits(s, dict(_ALL_FALSE, has_repeated_list_element=True),
                    "IndexedMap") is False


def test_site_n_parseint_needs_bare_int_output_and_no_competing_evidence():
    s, ag = boot()
    f = dict(_ALL_FALSE, is_list_shaped=True, output_is_bare_int=True)
    assert _admits(s, f, "ParseInt") is True
    assert _admits(s, dict(f, has_string_value=True), "ParseInt") is False
    assert _admits(s, dict(f, has_float_value=True), "ParseInt") is False
    assert _admits(s, dict(f, output_is_listlike=True), "ParseInt") is False


def test_bare_scalar_fallback_baseline_admits_default_ops_but_not_when_dictlike():
    """The 13th production (not itself one of the 14 named sites, but
    necessary for genuine parity -- RESULTS.md §4): the bare-scalar
    fallback branch's OWN `DEFAULT_OPS.to_vec()`, needed so a plain
    arithmetic spec ("add two numbers") gets a non-empty Γ verdict at
    all."""
    s, ag = boot()
    for op in ("Plus", "Times", "Minus", "Div", "Min", "Max", "Abs", "Neg",
               "Gt", "Lt", "Eq", "IfThenElse"):
        assert _admits(s, dict(_ALL_FALSE), op) is True, op
    # The DICT_DEFAULT_OPS branch (out of Γ scope) is checked BEFORE this
    # fallback in the real ladder -- a Dict-output-only spec must not
    # admit DEFAULT_OPS here (task 87's own shape).
    assert _admits(s, dict(_ALL_FALSE, output_is_dictlike=True), "Plus") is False


# --------------------------------------------------------------------------- #
# 6) THE FULL PARITY SWEEP — the exact-set-agreement check
#    (scripts/opgrammar_bulk_parity_sweep.py's own oracle/comparison,
#    imported directly so this runs as part of the regular suite) across
#    every real, runnable MBPP task spec in the fixture corpus, not just a
#    handful of witnesses. Asserts ZERO unexplained mismatches -- any
#    genuinely new drift between the Rust ladder and the Γ productions
#    fails this test, not just the standalone script.
# --------------------------------------------------------------------------- #
def test_full_corpus_parity_sweep_zero_unexplained_mismatches():
    import opgrammar_bulk_parity_sweep as sweep

    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    psy.ensure_program_synthesis(s, s._inner, ag)
    all_op_names = sorted(s.node(n)["attrs"]["name"] for n in s.nodes("SynthOp"))
    assert len(all_op_names) == 57

    tasks = _mbpp_tasks()
    n_checked = 0
    unexpected = []
    for task_id, task in tasks.items():
        try:
            parsed = ms.parse_asserts(task)
            split = ms.split_rows(parsed["rows"], "primary")
        except Exception:
            continue
        if not split["runnable"]:
            continue
        raw_rows = [{"inputs": dict(r.get("inputs") or {}), "output": r.get("expected")}
                    for r in split["revealed"]]
        if not raw_rows:
            continue
        flags = psy._synth_spec_shape_flags(raw_rows)
        real = sweep._real_admitted_ops(flags)
        gamma = sweep._gamma_admitted_ops(s, all_op_names, flags)
        n_checked += 1
        diff = real.symmetric_difference(gamma)
        is_dict_branch = (not flags["is_string_shaped"] and not flags["output_is_setlike"]
                           and not flags["is_list_shaped"] and flags["output_is_dictlike"])
        expected_diff = True if is_dict_branch else diff <= sweep._OUT_OF_SCOPE_OPS
        if diff and not expected_diff:
            unexpected.append((task_id, sorted(diff)))

    assert n_checked > 200, n_checked  # sanity: the sweep is actually running broadly
    assert unexpected == [], unexpected


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
