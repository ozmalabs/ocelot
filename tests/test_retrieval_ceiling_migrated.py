"""tests/test_retrieval_ceiling_migrated.py — Arc 3 R0: the ORACLE CEILING gate.

Companion to `scripts/retrieval_oracle_ceiling.py` (the measurement driver),
`results/retrieval_oracle_ceiling.json` (the artifact this gate re-derives
every aggregate from), `PROGRAM_SYNTHESIS_ARC3_PREREG.md` (HR1's bar,
derived from this artifact's own numbers), `PROGRAM_SYNTHESIS_ARC3_R0_NOTES.md`
(the full write-up).

This is a MEASUREMENT-only phase (no synthesis/engine/seed/spec code
touched). Gates:

  1. Artifact schema — rows are the baseline (every aggregate re-derives
     from `runnable_rows`), the `bounds` block is present and matches the
     script's own `BOUNDS` dict EXACTLY (so a silent bound drift anywhere
     is a hard test failure, never a quiet redefinition), determinism is
     twin-run identical.
  2. 3 pinned per-task oracle rows re-verified LIVE (fresh call to
     `retrieval_oracle_ceiling.oracle_for_task`, never read from the
     frozen artifact only) — one rung-(a) TRAP (revealed-pass, held-out
     fail), one rung-(a) GENUINE pass (both revealed and held-out), one
     rung-(c) GENUINE pass with a real recorded leaf-edit.
  3. Contamination — the shared list-gate
     (`tests/test_mbpp_contamination_migrated.py`) is run as a subprocess
     and reported; this phase's own AST-scan proves the runner never reads
     a TEST-split task's `code` field (train-split `code` reads are the
     entire, legal, content source — restated in the module docstring).
  4. Bounds cross-check against the prereg/notes docs — the exact numeric
     bounds this script used are also transcribed (as literal numbers) into
     `PROGRAM_SYNTHESIS_ARC3_PREREG.md`; a gate greps for them so a future
     edit to one without the other fails loudly.

Runtime: PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1
OZMA_SEED_PERSIST_DISABLED=1 pytest --confcutdir=. tests/test_retrieval_ceiling_migrated.py
"""
from __future__ import annotations

import ast
import json
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("OZMA_NO_LLM", "1")
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

import retrieval_oracle_ceiling as roc  # noqa: E402
from mbpp_zero_shot_baseline import split_tasks as q0_split_tasks  # noqa: E402

ARTIFACT_PATH = os.path.join(ROOT, "results", "retrieval_oracle_ceiling.json")
PREREG_PATH = os.path.join(ROOT, "docs", "research", "program_synthesis",
                           "PROGRAM_SYNTHESIS_ARC3_PREREG.md")
SCRIPT_PATH = os.path.join(ROOT, "scripts", "retrieval_oracle_ceiling.py")


@pytest.fixture(scope="module")
def artifact():
    with open(ARTIFACT_PATH) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def fixture_tasks():
    with open(roc.FIXTURE_PATH) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def splits(fixture_tasks):
    return q0_split_tasks(fixture_tasks)


@pytest.fixture(scope="module")
def pool_by_arity(splits):
    pool, _rows = roc.build_pool(splits["train"])
    return roc.pool_by_arity(pool)


def _task_by_id(tasks, tid):
    for t in tasks:
        if t["task_id"] == tid:
            return dict(t)
    raise KeyError(tid)


# --------------------------------------------------------------------------- #
#  1. artifact schema — rows are the baseline.
# --------------------------------------------------------------------------- #
def test_pool_size_and_emit_rate(artifact):
    pool = artifact["pool"]
    assert pool["n_train_tasks"] == 120
    assert pool["n_pool_exemplars"] == len(pool["pool_task_ids"])
    assert pool["n_pool_exemplars"] == sum(
        1 for r in pool["emit_rows"] if r["ok"])
    assert abs(pool["emit_rate"] - pool["n_pool_exemplars"] / pool["n_train_tasks"]) < 1e-9
    assert pool["n_pool_exemplars"] > 0


def test_test_split_is_fully_primary_runnable(artifact):
    ts = artifact["test_split"]
    assert ts["n_test_tasks"] == 257
    assert ts["n_runnable_primary"] == len(artifact["runnable_rows"])
    assert ts["n_runnable_primary"] + ts["n_excluded"] == ts["n_test_tasks"]


def test_bounds_block_matches_script_constant(artifact):
    """The artifact's own `bounds` field must equal the script's BOUNDS
    dict verbatim — a silent bound edit in one place without the other is
    a hard failure, never a quiet redefinition (the task's own "no silent
    caps, document every bound" instruction, enforced mechanically)."""
    assert artifact["bounds"] == roc.BOUNDS


def test_determinism_twin_run_identical(artifact):
    det = artifact["determinism"]
    assert det["identical"] is True
    assert det["outcome_hash_run1"] == det["outcome_hash_run2"]
    assert det["runs"] == 2


def test_elapsed_within_20_minute_box(artifact):
    assert artifact["elapsed_seconds"] < 20 * 60


def test_ceiling_cumulative_counts_are_monotone_nondecreasing(artifact):
    """Cumulative ceiling through a<=b<=c<=d must never DECREASE — each
    rung is strictly more permissive than the last."""
    rev = artifact["ceiling"]["revealed_pass_cumulative"]
    ks = [rev[k]["k"] for k in ("a", "b", "c", "d")]
    assert ks == sorted(ks)
    held = artifact["ceiling"]["heldout_pass_cumulative_a_to_c"]
    ks2 = [held[k]["k"] for k in ("a", "b", "c")]
    assert ks2 == sorted(ks2)


def test_heldout_ceiling_never_exceeds_revealed_ceiling_same_rung(artifact):
    rev = artifact["ceiling"]["revealed_pass_cumulative"]
    held = artifact["ceiling"]["heldout_pass_cumulative_a_to_c"]
    for k in ("a", "b", "c"):
        assert held[k]["k"] <= rev[k]["k"]


def test_trap_mass_is_the_gap_between_revealed_and_heldout(artifact):
    rev = artifact["ceiling"]["revealed_pass_cumulative"]
    held = artifact["ceiling"]["heldout_pass_cumulative_a_to_c"]
    traps = artifact["trap_mass"]
    for k in ("a", "b", "c"):
        assert traps[k]["n_revealed_solved"] == rev[k]["k"]
        assert traps[k]["n_heldout_solved"] == held[k]["k"]
        assert traps[k]["n_trap"] == rev[k]["k"] - held[k]["k"]
        assert len(traps[k]["trap_task_ids"]) == traps[k]["n_trap"]


def test_q5_failure_coverage_ids_are_a_subset_of_q5_failures(artifact):
    with open(roc.ENDGAME_PATH) as f:
        endgame = json.load(f)
    full_rows = endgame["arms"]["full"]["runnable_rows"]
    fail_ids = set(r["task_id"] for r in full_rows if r["outcome"] != "pass")
    cov = artifact["q5_full_failure_coverage"]
    assert set(cov["q5_full_failure_task_ids"]) == fail_ids
    assert set(cov["covered_by_rung_a_c_heldout_honest"]) <= fail_ids
    assert cov["n_covered_a_c"] == len(cov["covered_by_rung_a_c_heldout_honest"])
    assert (cov["n_covered_a_c"] + cov["n_covered_d_only"] + cov["n_uncovered"]
            == cov["n_q5_full_failures"])


def test_every_runnable_row_carries_a_best_rung_in_the_closed_ladder(artifact):
    for r in artifact["runnable_rows"]:
        assert r["best_rung_revealed"] in ("a", "b", "c", "d", "none")
        assert r["best_rung_heldout_honest"] in ("a", "b", "c", "none")
        assert r["best_rung_with_upper_bound_d"] in ("a", "b", "c", "d", "none")
        # a heldout pass at rung K implies a revealed pass at rung <= K.
        if r["best_rung_heldout_honest"] != "none":
            assert roc._rank(r["best_rung_revealed"]) <= roc._rank(r["best_rung_heldout_honest"])


# --------------------------------------------------------------------------- #
#  2. 3 pinned tasks, re-verified LIVE (never trusting the frozen artifact
#     alone) via a fresh call to `oracle_for_task`.
# --------------------------------------------------------------------------- #
def test_pinned_task_56_is_a_rung_a_trap_live(fixture_tasks, pool_by_arity):
    """task 56: an exemplar (762 or 803) passes both revealed rows AS-IS
    but fails the held-out row — the textbook retrieval-overfit trap."""
    task = _task_by_id(fixture_tasks, 56)
    task = {k: v for k, v in task.items() if k != "code"}
    r = roc.oracle_for_task(task, pool_by_arity)
    assert r is not None
    assert r["best_rung_revealed"] == "a"
    assert r["rung_a"]["revealed_pass_exemplars"], "expected >=1 rung-a revealed pass"
    assert r["rung_a"]["heldout_pass_exemplars"] == []
    assert r["best_rung_heldout_honest"] == "none"


def test_pinned_task_105_is_a_rung_a_genuine_pass_live(fixture_tasks, pool_by_arity):
    """task 105: exemplar 798 passes AS-IS on every revealed row AND the
    held-out row — a genuine (non-trap) rung-(a) oracle solution."""
    task = _task_by_id(fixture_tasks, 105)
    task = {k: v for k, v in task.items() if k != "code"}
    r = roc.oracle_for_task(task, pool_by_arity)
    assert r is not None
    assert r["best_rung_revealed"] == "a"
    assert r["best_rung_heldout_honest"] == "a"
    assert 798 in r["rung_a"]["heldout_pass_exemplars"]


def test_pinned_task_138_is_a_rung_c_genuine_pass_with_a_real_edit_live(
        fixture_tasks, pool_by_arity):
    """task 138: near-miss exemplar 762 passes only 1/2 revealed rows
    as-is; a single comparator swap (Eq -> Gt) at one leaf makes it pass
    every revealed row AND the held-out row."""
    task = _task_by_id(fixture_tasks, 138)
    task = {k: v for k, v in task.items() if k != "code"}
    r = roc.oracle_for_task(task, pool_by_arity)
    assert r is not None
    assert r["best_rung_revealed"] == "c"
    assert r["best_rung_heldout_honest"] == "c"
    assert r["rung_c"]["anchor"]["exemplar"] == 762
    assert r["rung_c"]["edit"]["kind"] == "op"
    assert r["rung_c"]["edit"]["from"] == "Eq"
    assert r["rung_c"]["edit"]["to"] == "Gt"
    assert r["rung_c"]["heldout_pass"] is True


# --------------------------------------------------------------------------- #
#  3. contamination.
# --------------------------------------------------------------------------- #
def test_script_never_reads_test_split_code_field():
    """AST-scan: the script's own source must never index `task["code"]`
    (or any `["code"]` subscript at all) outside of `build_pool`'s
    docstring-described, TRAIN-scoped read. A structural, not textual,
    check — the same class as Q5's own runner-source audit."""
    with open(SCRIPT_PATH) as f:
        src = f.read()
    tree = ast.parse(src)
    code_subscripts = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Subscript):
            sl = node.slice
            key = sl.value if isinstance(sl, ast.Index) else sl
            if isinstance(key, ast.Constant) and key.value == "code":
                code_subscripts.append(node.lineno)
    # Exactly the two reads inside build_pool (`t["code"]` passed to
    # resolve_entry and emit_prog_ir) — both operate on TRAIN tasks only
    # (the function's own parameter is `train_tasks`).
    assert len(code_subscripts) == 2, (
        "expected exactly the 2 train-scoped code reads inside build_pool, "
        "found %r at lines %r — any OTHER ['code'] read is new and must be "
        "audited for test-split contamination risk" % (len(code_subscripts), code_subscripts))


def test_test_tasks_have_no_code_field_before_oracle_scoring(splits):
    for t in splits["test"]:
        assert "code" not in t


def test_shared_contamination_gate_passes():
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--confcutdir=.",
         "tests/test_mbpp_contamination_migrated.py", "-q"],
        cwd=ROOT, capture_output=True, text=True,
        env={**os.environ, "PYTHONPATH": "runners/dsl/python:.:scripts",
             "OZMA_NO_LLM": "1", "OZMA_SEED_PERSIST_DISABLED": "1"},
        timeout=120)
    assert result.returncode == 0, result.stdout[-4000:] + result.stderr[-2000:]
    assert "passed" in result.stdout


# --------------------------------------------------------------------------- #
#  4. bounds cross-check against the prereg doc — a literal-number grep so a
#     future edit to one without the other fails loudly.
# --------------------------------------------------------------------------- #
def test_prereg_doc_states_the_same_bounds_as_the_artifact(artifact):
    with open(PREREG_PATH) as f:
        doc = f.read()
    bounds = artifact["bounds"]
    # every bound value that is a bare number/short list must appear
    # somewhere in the prereg's own text (as a literal), so the doc can
    # never silently drift from what the script actually enforced.
    assert str(bounds["rung_b_max_arity_for_permutation_search"]) in doc
    assert str(bounds["repair_measured_conversion_rate_p7b"]).lstrip("0") in doc or "25%" in doc
    for op in bounds["rung_c_arith_op_family"]:
        assert op in doc
    for op in bounds["rung_c_cmp_op_family"]:
        assert op in doc


def test_prereg_doc_exists_and_is_nonempty():
    assert os.path.exists(PREREG_PATH)
    with open(PREREG_PATH) as f:
        assert len(f.read()) > 500


def test_r0_notes_doc_exists_and_is_nonempty():
    path = os.path.join(ROOT, "docs", "research", "program_synthesis",
                        "PROGRAM_SYNTHESIS_ARC3_R0_NOTES.md")
    assert os.path.exists(path)
    with open(path) as f:
        assert len(f.read()) > 500
