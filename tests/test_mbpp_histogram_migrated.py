"""test_mbpp_histogram_migrated — arc 2 Q0-B gates for
`scripts/mbpp_blocker_histogram.py` / `results/mbpp_blocker_histogram.json`.

Per PROGRAM_SYNTHESIS_ARC2_PLAN.md §2-Q0 and PROGRAM_SYNTHESIS_ARC2_PREREG.md:
this is a pure MEASUREMENT script (no substrate boot, no agent decisions —
the `code_curriculum`/`prog_ir_statement_histogram` precedent), so its gates
are: determinism, schema/derivation honesty (every aggregate re-derivable
from the per-task rows), the emit_prog_ir-verdict-is-REAL gate (hand-pinned
blockers on two known tasks, proving nothing is approximated), and a
no-verbatim-code gate on the frozen artifact (the binding contamination
constraint: task_id lists and feature names only, never a code line).

Run: PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 \
     OZMA_SEED_PERSIST_DISABLED=1 python3 -m pytest --confcutdir=. \
     tests/test_mbpp_histogram_migrated.py -p no:randomly -q
"""
from __future__ import annotations

import json
import os
import sys
import warnings

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import mbpp_blocker_histogram as h

FIXTURE_DIR = os.path.join(ROOT, "tests", "fixtures", "mbpp")
ARTIFACT_PATH = os.path.join(ROOT, "results", "mbpp_blocker_histogram.json")


@pytest.fixture(scope="module")
def all_tasks():
    with open(os.path.join(FIXTURE_DIR, "sanitized-mbpp.json")) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def artifact():
    with open(ARTIFACT_PATH) as f:
        return json.load(f)


# --------------------------------------------------------------------------- #
#  DETERMINISM
# --------------------------------------------------------------------------- #
def test_determinism_on_a_30_task_slice(all_tasks):
    """The exact per-task computation (assert parsing + the REAL
    emit_prog_ir + sub-construct counting), run twice on the same 30-task
    slice, must be byte-identical after JSON serialization."""
    slice30 = all_tasks[:30]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r1 = h.measure(tasks_override=slice30)
        r2 = h.measure(tasks_override=slice30)
    s1 = json.dumps(r1, sort_keys=True)
    s2 = json.dumps(r2, sort_keys=True)
    assert s1 == s2
    assert r1["meta"]["n_tasks"] == 30


def test_full_corpus_measure_is_twin_run_deterministic(all_tasks):
    """UPDATED 2026-08-01 (Q1.5): this test used to assert `measure()`
    reproduces the FROZEN artifact byte-for-byte. That comparison is now
    invalid on its face, not a regression to chase: `measure()` calls the
    REAL, live `domains.prog_ir_emit.emit_prog_ir` (module docstring,
    "the emit_prog_ir-verdict-is-REAL gate"), and Q1.5 legitimately widened
    that emitter (ProgSlice, bitwise set-algebra, method-oracle recv form,
    ...), so a live re-run over the full 427-task corpus now correctly
    disagrees with the Q0-era frozen snapshot on many rows (see
    `test_known_task_2_bitand_is_set_intersection_not_bitwise` for one
    named example). `results/mbpp_blocker_histogram.json` stays frozen
    (arc-1 discipline: a snapshot is a historical record, never silently
    regenerated to match a later engine) — this test is converted to what
    it was ACTUALLY guarding against per its own docstring: module-level
    dicts/sets leaking state across a run. Two independent full-corpus
    runs must still agree with EACH OTHER byte-for-byte (the invariant
    `test_determinism_on_a_30_task_slice` already proves at smaller scale;
    this is the same check at full scale, now compared live-vs-live
    instead of live-vs-stale-snapshot)."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r1 = h.measure()
        r2 = h.measure()
    s1 = json.dumps(r1, indent=2, sort_keys=True)
    s2 = json.dumps(r2, indent=2, sort_keys=True)
    assert s1 == s2
    assert r1["meta"]["n_tasks"] == 427


# --------------------------------------------------------------------------- #
#  SCHEMA / DERIVATION HONESTY — every aggregate re-derives from per_task.
# --------------------------------------------------------------------------- #
def test_schema_top_level_keys(artifact):
    for key in ("meta", "program_side", "value_domain", "prompt_side",
                "curves", "per_task"):
        assert key in artifact
    assert artifact["meta"]["n_tasks"] == 427
    assert len(artifact["per_task"]) == 427
    assert sum(artifact["meta"]["split_counts"].values()) == 427
    assert artifact["meta"]["split_counts"] == {
        "fewshot": 7, "test": 257, "train": 120, "val": 43}


def test_program_side_counts_derive_from_per_task(artifact):
    rows = artifact["per_task"]
    ok_ids = {r["task_id"] for r in rows if r["ok"]}
    predictable_ids = {r["task_id"] for r in rows if r["predictable"]}
    assert len(ok_ids) == artifact["program_side"]["ok_count"]
    assert len(predictable_ids) == artifact["program_side"]["predictable_count"]
    assert artifact["program_side"]["blocked_count"] == 427 - len(ok_ids)
    # predictable implies ok (predictable is only ever set when ok).
    assert predictable_ids <= ok_ids

    blocker_recount = {}
    for r in rows:
        for b in r["blockers"]:
            blocker_recount[b] = blocker_recount.get(b, 0) + 1
    assert blocker_recount == artifact["program_side"]["blocker_counts"]


def test_blocker_top20_task_ids_match_per_task_rows(artifact):
    blocker_ids = artifact["program_side"]["blocker_top20"]["task_ids"]
    rows_by_id = {r["task_id"]: r for r in artifact["per_task"]}
    for blocker, ids in blocker_ids.items():
        for tid in ids:
            assert blocker in rows_by_id[tid]["blockers"]


def test_curves_reach_their_own_denominator(artifact):
    """Every candidate pool is exhaustive by construction (the P0
    precedent): the greedy curve must reach 100% of ITS OWN denominator —
    never-unlockable = 0, same as the arc-1 histogram's finding."""
    for name in ("value_domain_curve", "op_feature_curve", "joint_curve",
                 "joint_curve_q1_scoped"):
        curve = artifact["curves"][name]
        last = curve["steps"][-1]
        assert last["cumulative_unlocked"] == curve["denominator"]
        assert last["cumulative_pct"] == 100.0


def test_curve_steps_are_monotonic_and_sum_correctly(artifact):
    for name in ("value_domain_curve", "op_feature_curve", "joint_curve",
                 "joint_curve_q1_scoped"):
        steps = artifact["curves"][name]["steps"]
        prev = 0
        for s in steps:
            assert s["cumulative_unlocked"] >= prev
            prev = s["cumulative_unlocked"]
        # step 0's newly_unlocked is the floor; every later step's gain
        # plus the running total must equal cumulative_unlocked exactly.
        running = steps[0]["cumulative_unlocked"]
        for s in steps[1:]:
            running += s["newly_unlocked_count"]
            assert running == s["cumulative_unlocked"]


def test_value_domain_floor_is_arc1_registered_wall(artifact):
    assert artifact["meta"]["value_domain_floor"] == ["int", "list[int]"]


def test_type_coverable_plus_non_coverable_is_427(artifact):
    vd = artifact["value_domain"]
    assert vd["type_coverable_count"] + vd["non_type_coverable_count"] == 427
    assert len(vd["non_type_coverable_ids"]) == vd["non_type_coverable_count"]


def test_scoped_joint_curve_excludes_out_of_scope_tasks(artifact):
    scoped = artifact["curves"]["joint_curve_q1_scoped"]
    joint = artifact["curves"]["joint_curve"]
    assert scoped["denominator"] + scoped["excluded_out_of_scope_count"] == joint["denominator"]
    # every excluded id really does require an out-of-scope family somewhere
    rows_by_id = {r["task_id"]: r for r in artifact["per_task"]}
    out_of_scope_prefixes = ("stdlib_misc:", "misc_builtin:", "misc_method:",
                              "misc_structural:", "misc_opext:")
    out_of_scope_names = {"regex", "complex_numbers", "collections_module",
                           "graph_repr_gap"}
    for tid in scoped["excluded_out_of_scope_ids"]:
        row = rows_by_id[tid]
        fams = set(row["structural_families"]) | set(row.get("extern_families", []))
        assert any(f in out_of_scope_names or f.startswith(out_of_scope_prefixes)
                   for f in fams), (tid, fams)


# --------------------------------------------------------------------------- #
#  emit_prog_ir-VERDICT-IS-REAL — hand-pinned expectations on known tasks.
# --------------------------------------------------------------------------- #
def test_known_task_slice_subscript_blocker_matches_real_emitter(artifact):
    """task 9 `find_Rotations`: `tmp[i: i+n]` is a slice subscript — the
    REAL emit_prog_ir refuses it with exactly `SliceSubscript` (verified by
    hand against the reference source, not reimplemented here)."""
    rows_by_id = {r["task_id"]: r for r in artifact["per_task"]}
    row = rows_by_id[9]
    assert row["entry_function"] == "find_Rotations"
    assert row["ok"] is False
    assert row["blockers"] == ["SliceSubscript"]
    assert row["structural_families"] == ["slicing"]


def test_known_task_bitxor_blocker_matches_real_emitter(artifact):
    """task 6 `differ_At_One_Bit_Pos`: `is_Power_Of_Two(a ^ b)` — the `^`
    is a bitwise xor; the REAL emit_prog_ir refuses it as `OpExt:BitXor`."""
    rows_by_id = {r["task_id"]: r for r in artifact["per_task"]}
    row = rows_by_id[6]
    assert row["entry_function"] == "differ_At_One_Bit_Pos"
    assert row["ok"] is False
    assert row["blockers"] == ["OpExt:BitXor"]
    assert row["structural_families"] == ["bitwise_ops"]


def test_known_task_2_bitand_is_set_intersection_not_bitwise(artifact):
    """task 2 `similar_elements`: `set(test_tup1) & set(test_tup2)` — Python
    overloads `&` between int-bitwise-and and set-intersection; AT Q0 TIME
    the REAL emitter had no operand-type awareness at emit time, so it
    blocked BOTH uses identically as `OpExt:BitAnd`. This is exactly the
    real, measured finding the prereg's Q1 recommendation was built on:
    the `bitwise_ops` family this histogram groups is NOT purely integer
    bit-twiddling — some of its mass is set algebra wearing the same
    operator token (fixing "bitwise ops" for MBPP means fixing set
    intersection too, not only `a & b` on ints).

    UPDATED 2026-08-01 (Q1.5, MORE coverage, per the arc-1 P5-C precedent
    "update expectations only toward more coverage, append the frontier
    note"): `domains/prog_ir_emit.py` now emits set-`&` as the plain DSL
    `BitAnd` Term (type-blind — dispatch is the Q1 engine's runtime
    concern), and the Q1 engine already gives `BitAnd` real set-algebra
    semantics — so this task is now REPRESENTABLE AND PREDICTABLE. This
    is the task-2 finding actually getting fixed, not a regression; the
    LIVE re-check below is updated to assert exactly that. The FROZEN
    artifact row (`results/mbpp_blocker_histogram.json`, a Q0-era
    snapshot) is untouched and still correctly records the OLD,
    pre-widening verdict — asserted unchanged below."""
    from domains.prog_ir_emit import emit_prog_ir
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        res = emit_prog_ir(
            "def similar_elements(test_tup1, test_tup2):\n"
            "  res = tuple(set(test_tup1) & set(test_tup2))\n"
            "  return (res) ",
            name="similar_elements")
    assert res["ok"] is True
    assert res["predictable"] is True
    assert res["externs"] == ["set", "tuple"]
    # the frozen Q0-era artifact row is untouched — still the OLD verdict.
    rows_by_id = {r["task_id"]: r for r in artifact["per_task"]}
    row = rows_by_id[2]
    assert row["blockers"] == ["OpExt:BitAnd"]
    assert row["structural_families"] == ["bitwise_ops"]
    # the value-domain side still sees through the set()-wrap correctly
    # (the assert-parser fix this test also cross-checks):
    assert row["return_types"] == ["set[int]"]


def test_multi_def_task_resolves_the_called_entry(artifact):
    """task 592 defines binomial_Coeff + sum_Of_product; test_list calls
    sum_Of_product only — the entry-resolution rule must pick that one,
    not the first def in the file."""
    rows_by_id = {r["task_id"]: r for r in artifact["per_task"]}
    row = rows_by_id[592]
    assert row["entry_function"] == "sum_Of_product"


# --------------------------------------------------------------------------- #
#  VALUE-DOMAIN PARSER cross-checks (independent-implementation honesty).
# --------------------------------------------------------------------------- #
def test_math_isclose_is_a_recognized_float_tolerance_form():
    """The corpus-wide fact this script measured: every non-Name-func Call
    assert test is `math.isclose(...)` (13 tasks, 39 asserts) — this
    parser recognizes it as `float_tolerance` (a real, distinct form, not
    a garbage bucket), extracting arg/return types from the two literal
    operands either side of the tolerance call."""
    pr = h.parse_one_assert(
        "assert math.isclose(volume_sphere(10), 4188.79, rel_tol=0.001)",
        "volume_sphere")
    assert pr["form"] == "float_tolerance"
    assert pr["arg_types"] == ["int"]
    assert pr["return_type"] == "float"


def test_set_wrapper_and_raw_set_literal_are_classified():
    """Independent-parser cross-check note (PROGRAM_SYNTHESIS_ARC2_PREREG.md
    contamination/protocol section): this parser peels `set(...)` wraps on
    either side AND classifies a raw `{...}` set literal directly via
    `ast.Set` — two forms the sibling Q0-A baseline's `classify_assert`
    does not attempt (registered there as `set_wrapper`/`set_literal_value`
    unsupported forms). Both parsers are honest under their own scope; this
    is why this script's non-type-coverable count (2/427) is far lower than
    Q0-A's assert-level `assert_unparseable` count on the test split."""
    pr = h.parse_one_assert(
        "assert set(similar_elements((3,4),(5,4))) == set((4,))",
        "similar_elements")
    assert pr["form"] == "eq_literal"
    assert pr["return_type"] == "set[int]"
    assert "set" in pr["wraps"]

    pr2 = h.parse_one_assert("assert f(1) == {1, 2, 3}", "f")
    assert pr2["form"] == "eq_literal"
    assert pr2["return_type"] == "set[int]"


# --------------------------------------------------------------------------- #
#  NO-VERBATIM-CODE gate — the binding contamination constraint.
# --------------------------------------------------------------------------- #
def test_artifact_contains_no_code_or_prompt_keys(artifact):
    for row in artifact["per_task"]:
        assert "code" not in row
        assert "prompt" not in row
        assert "test_list" not in row


def test_artifact_contains_no_verbatim_reference_code_lines(all_tasks):
    """For a spread of tasks (varied split, varied length), a distinctive
    non-trivial line from the REFERENCE code must not appear verbatim
    anywhere in the artifact's raw JSON text."""
    with open(ARTIFACT_PATH) as f:
        artifact_text = f.read()
    sample_ids = {2, 3, 6, 9, 56, 82, 223, 592, 630, 751, 809}
    by_id = {t["task_id"]: t for t in all_tasks}
    checked = 0
    for tid in sample_ids:
        t = by_id.get(tid)
        if t is None:
            continue
        for line in t["code"].splitlines():
            stripped = line.strip()
            # A "distinctive" line: long enough that accidental collision
            # with a feature-name/type-tag string is not plausible.
            if len(stripped) >= 20 and not stripped.startswith("#"):
                assert stripped not in artifact_text, (tid, stripped)
                checked += 1
    assert checked >= len(sample_ids)  # every sampled task contributed >=1 line


def test_artifact_contains_no_full_prompt_text(all_tasks):
    with open(ARTIFACT_PATH) as f:
        artifact_text = f.read()
    for t in all_tasks[:40]:
        prompt = t["prompt"].strip()
        if len(prompt) >= 25:
            assert prompt not in artifact_text


# --------------------------------------------------------------------------- #
#  PROMPT-SIDE / VALUE-DOMAIN sanity (small unit checks, not corpus-wide).
# --------------------------------------------------------------------------- #
def test_request_form_classification():
    assert h.request_form("Write a function to find X.") == "write_a_function_to"
    assert h.request_form("Write a python function to find X.") == "write_a_python_function_to"
    assert h.request_form("Write a function that finds X.") == "write_a_function_that"
    assert h.request_form("Given a list, do X.") == "other"


def test_classify_literal_basic_types_and_containers():
    import ast
    assert h.classify_literal(ast.parse("5", mode="eval").body) == "int"
    assert h.classify_literal(ast.parse("-5", mode="eval").body) == "int"
    assert h.classify_literal(ast.parse("5.0", mode="eval").body) == "float"
    assert h.classify_literal(ast.parse("'a'", mode="eval").body) == "str"
    assert h.classify_literal(ast.parse("True", mode="eval").body) == "bool"
    assert h.classify_literal(ast.parse("None", mode="eval").body) == "none"
    assert h.classify_literal(ast.parse("[1, 2]", mode="eval").body) == "list[int]"
    assert h.classify_literal(ast.parse("[]", mode="eval").body) == "list[empty]"
    assert h.classify_literal(ast.parse("(1, 'a')", mode="eval").body) == "tuple[mixed]"
    assert h.classify_literal(ast.parse("{'a': 1}", mode="eval").body) == "dict"
    assert h.classify_literal(ast.parse("foo()", mode="eval").body) is None


def test_bool_is_not_conflated_with_int():
    """Python's bool is an int subclass — classify_literal must not tag a
    literal `True`/`False` as `int` (a real, MBPP-relevant distinction:
    `assert is_something(x) == True` is a bool-typed return, not int)."""
    import ast
    assert h.classify_literal(ast.parse("True", mode="eval").body) == "bool"
    assert h.classify_literal(ast.parse("1", mode="eval").body) == "int"
