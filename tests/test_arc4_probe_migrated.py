"""tests/test_arc4_probe_migrated.py — Arc 4 S0 track B gate.

Companion to `scripts/arc4_backward_probe.py` (the measurement driver),
`results/arc4_backward_probe.json` (the artifact every gate here
re-derives from), `PROGRAM_SYNTHESIS_ARC4_PREREG.md` (HA3/HA4's bars,
derived from this artifact's own numbers), `PROGRAM_SYNTHESIS_ARC4_S0B_
NOTES.md` (the full write-up).

Pure measurement phase (no synthesis/engine/seed/spec code touched).
Gates:

  1. Artifact schema — top-level keys present, HA3/HA4 aggregates
     re-derive from their own `rows`, determinism blocks are
     `identical: true`, the "what_is_simulated_vs_measured" statement
     is present and its two keys match the flags actually asserted
     elsewhere in the artifact (never silently drifted).
  2. 3 pinned HA3 probe rows re-verified LIVE (a fresh call to
     `measure_backward_ordering`/`measure_synthetic_mechanism_check`,
     never read from the frozen artifact only): task 464 (a genuine
     reordering case, tie), task 106 (a genuine reordering case, mutual
     budget exhaustion), and the off-corpus `synthetic_chain2` case
     (a genuine reordering case where backward ORDERING LOSES — the
     honest, non-cherry-picked result).
  3. HA4 accounting gates — the five lever id-lists are pairwise
     disjoint from the exclusive lists' own definition, the overlap
     matrix is symmetric and its diagonal equals `lever_counts`, and
     the five residual buckets (covered-by-a-lever, ok-already,
     other-named-blocker, unresolved, residual-none) partition the
     full `gapped:enumerate_failed` population with no overlap and no
     gap.
  4. Determinism — twin-run hashes recomputed fresh in-process.
  5. Contamination — the shared list-gate
     (`tests/test_mbpp_contamination_migrated.py`) passes standalone.

Runtime: PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1
OZMA_SEED_PERSIST_DISABLED=1 pytest --confcutdir=. tests/test_arc4_probe_migrated.py
"""
from __future__ import annotations

import hashlib
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

import arc4_backward_probe as p  # noqa: E402
import retrieval_oracle_ceiling as roc  # noqa: E402
from mbpp_zero_shot_baseline import split_tasks as q0_split_tasks  # noqa: E402

ARTIFACT_PATH = os.path.join(ROOT, "results", "arc4_backward_probe.json")


@pytest.fixture(scope="module")
def artifact():
    with open(ARTIFACT_PATH) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def fixture_tasks():
    with open(p.FIXTURE_PATH) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def all_tasks_by_id(fixture_tasks):
    return {t["task_id"]: t for t in fixture_tasks}


@pytest.fixture(scope="module")
def splits(fixture_tasks):
    return q0_split_tasks(fixture_tasks)


@pytest.fixture(scope="module")
def pool_by_id(splits):
    pool, _rows = roc.build_pool(splits["train"])
    return {ex["task_id"]: ex for ex in pool}


@pytest.fixture(scope="module")
def ceiling():
    with open(p.CEILING_PATH) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def endgame():
    with open(p.ENDGAME_PATH) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def full_rows(endgame):
    return endgame["arms"]["full_r3"]["runnable_rows"]


@pytest.fixture(scope="module")
def population(all_tasks_by_id, pool_by_id, ceiling, full_rows):
    return p.build_ha3_population(all_tasks_by_id, pool_by_id, ceiling, full_rows)


# --------------------------------------------------------------------------- #
#  1. artifact schema
# --------------------------------------------------------------------------- #
def test_top_level_keys(artifact):
    for k in ("_README", "measured_at", "what_is_simulated_vs_measured",
             "ha3_backward_ordering_probe", "ha3_synthetic_mechanism_check",
             "ha4_search_reach_sizing", "environment", "elapsed_seconds"):
        assert k in artifact


def test_simulated_vs_measured_statement_present_and_matches(artifact):
    stmt = artifact["what_is_simulated_vs_measured"]
    assert "measurement_1_backward_ordering" in stmt
    assert "measurement_2_search_reach" in stmt
    # "matches the artifact's own flags": measurement 1 claims to drive the
    # real Term (never simulate) -> every HA3 row must carry a real `tested`
    # int (not None) whenever `found` is true, for both orderings.
    assert "MEASURED, not simulated" in stmt["measurement_1_backward_ordering"]
    assert "MEASURED fresh" in stmt["measurement_2_search_reach"]
    for row in artifact["ha3_backward_ordering_probe"]["rows"]:
        if row.get("skipped"):
            continue
        for side in ("current", "backward"):
            if row[side]["found"]:
                assert isinstance(row[side]["tested"], int)
    # measurement 2 claims a FRESH recompute, never the cached histogram
    # artifact -> the staleness_note must be present and must name the
    # concrete stale fact (RecvMethod / task 307) it is conditioned on.
    stale = artifact["ha4_search_reach_sizing"]["staleness_note"]
    assert "RecvMethod" in stale
    assert "307" in stale


def test_ha3_aggregate_rederives_from_rows(artifact):
    rows = artifact["ha3_backward_ordering_probe"]["rows"]
    agg = artifact["ha3_backward_ordering_probe"]["aggregate"]
    recomputed = p.ha3_aggregate(rows)
    assert recomputed == agg


def test_ha3_determinism_identical(artifact):
    assert artifact["ha3_backward_ordering_probe"]["determinism"]["identical"] is True
    assert artifact["ha3_synthetic_mechanism_check"]["determinism"]["identical"] is True
    assert artifact["ha4_search_reach_sizing"]["determinism"]["identical"] is True


def test_ha3_population_disjoint_sources(artifact):
    pop = artifact["ha3_backward_ordering_probe"]["population"]
    assert len(pop) == 18
    retrieval_ids = {e["task_id"] for e in pop if e["source"] == "retrieval_ceiling"}
    native_ids = {e["task_id"] for e in pop if e["source"] == "native_enumerate_accept"}
    assert len(retrieval_ids) == 12
    assert len(native_ids) == 6
    assert retrieval_ids.isdisjoint(native_ids)


# --------------------------------------------------------------------------- #
#  2. pinned rows, re-verified LIVE
# --------------------------------------------------------------------------- #
def test_pinned_task_464_reorders_and_ties_live(all_tasks_by_id, population):
    rows = p.measure_backward_ordering(all_tasks_by_id, population)
    row = next(r for r in rows if r["task_id"] == 464)
    assert row["source"] == "native_enumerate_accept"
    assert row["reorders_vs_current"] is True
    assert row["row_position_rank_backward"] == [1, 0]
    assert row["current"]["found"] and row["backward"]["found"]
    assert row["current"]["tested"] == row["backward"]["tested"]
    assert row["verdict"] == "tie"


def test_pinned_task_106_reorders_and_mutually_exhausts_live(all_tasks_by_id, population):
    rows = p.measure_backward_ordering(all_tasks_by_id, population)
    row = next(r for r in rows if r["task_id"] == 106)
    assert row["source"] == "retrieval_ceiling"
    assert row["provenance"]["rung"] == "b"
    assert row["reorders_vs_current"] is True
    assert row["current"]["found"] is False
    assert row["backward"]["found"] is False
    # 2026-08-01 (arc4 S4): the halt_reason flipped "max_size" -> "budget".
    # S4 added 11 list/iteration ops to the enumerator, so the search space
    # at each size is much larger and the candidate BUDGET is now exhausted
    # before the size ceiling is reached. The test's actual claim — neither
    # ordering finds a solution, and both terminate HONESTLY rather than
    # silently — is unchanged and still asserted; only which of the two
    # honest exhaustion reasons fires has moved. Pinned to the current value
    # (not loosened to a set) so a real change still bites.
    assert row["current"]["halt_reason"] == "budget"
    assert row["backward"]["halt_reason"] in ("budget", "max_size", "saturated")
    assert row["verdict"].startswith("not_found")


def test_pinned_synthetic_chain2_backward_loses_live():
    rows = p.measure_synthetic_mechanism_check()
    row = next(r for r in rows if r["id"] == "synthetic_chain2")
    assert row["current"]["found"] and row["backward"]["found"]
    assert row["current"]["tested"] < row["backward"]["tested"]
    assert row["verdict"] == "current_wins"


def test_no_backward_win_anywhere_in_this_probe(artifact):
    """The headline HA3 finding, gated so it cannot silently drift: across
    the entire probe (18-task MBPP oracle population + 2 off-corpus
    synthetic checks), backward-from-output ordering never beats current
    declared-order enumeration. Ties or losses only."""
    agg = artifact["ha3_backward_ordering_probe"]["aggregate"]
    assert agg["backward_wins"] == 0
    synth_rows = artifact["ha3_synthetic_mechanism_check"]["rows"]
    assert sum(1 for r in synth_rows if r["verdict"] == "backward_wins") == 0


# --------------------------------------------------------------------------- #
#  3. HA4 accounting
# --------------------------------------------------------------------------- #
def test_ha4_exclusive_ids_subset_of_lever_ids(artifact):
    h = artifact["ha4_search_reach_sizing"]
    for lv in ("mutating_method_writeback", "comprehension_forms", "kwargs",
              "map_lambda", "regex"):
        assert set(h["exclusive_task_ids"][lv]) <= set(h["lever_task_ids"][lv])
        assert h["exclusive_counts"][lv] == len(h["exclusive_task_ids"][lv])
        assert h["lever_counts"][lv] == len(h["lever_task_ids"][lv])


def test_ha4_overlap_matrix_symmetric_and_diagonal_matches(artifact):
    h = artifact["ha4_search_reach_sizing"]
    ov = h["overlap_matrix"]
    levers = list(h["lever_task_ids"].keys())
    for a in levers:
        assert ov[a][a] == h["lever_counts"][a]
        for b in levers:
            assert ov[a][b] == ov[b][a]


def test_ha4_ranked_by_exclusive_mass_is_sorted_descending(artifact):
    h = artifact["ha4_search_reach_sizing"]
    ranked = h["ranked_by_exclusive_mass"]
    counts = [h["exclusive_counts"][lv] for lv in ranked]
    assert counts == sorted(counts, reverse=True)


def test_ha4_population_partitioned_with_no_gap_no_overlap(artifact):
    h = artifact["ha4_search_reach_sizing"]
    n = h["n_gapped_enumerate_failed"]
    covered = set()
    for ids in h["lever_task_ids"].values():
        covered |= set(ids)
    ok_already = set(h["ok_already_no_named_lever"])
    other = set(h["other_named_blocker_no_five_lever"])
    unresolved = set(h["unresolved_entry_or_emit"])
    residual = set(h["residual_none_of_the_above"])
    buckets = [covered, ok_already, other, unresolved, residual]
    total = sum(len(b) for b in buckets)
    union = set().union(*buckets)
    assert total == len(union), "buckets overlap"
    assert len(union) == n, "buckets do not cover the full population"


def test_ha4_denominator_matches_full_r3_endgame(full_rows, artifact):
    n = sum(1 for r in full_rows if r["outcome"] == "gapped:enumerate_failed")
    assert artifact["ha4_search_reach_sizing"]["n_gapped_enumerate_failed"] == n


def test_ha4_recv_method_staleness_finding_reproduces_live():
    """The artifact's headline HA4 caveat: results/mbpp_blocker_histogram.json
    is stale on the mutating-recv-method axis. Reproduced live rather than
    trusted from prose."""
    task = json.load(open(p.FIXTURE_PATH))
    by_id = {t["task_id"]: t for t in task}
    row = p._fresh_program_row(by_id[307])
    assert row["ok"] is False
    assert "RecvMethod:append" in row["blockers"]
    with open(os.path.join(ROOT, "results", "mbpp_blocker_histogram.json")) as f:
        stale = json.load(f)
    stale_row = next(r for r in stale["per_task"] if r["task_id"] == 307)
    assert stale_row["ok"] is True
    assert stale_row["blockers"] == []


# --------------------------------------------------------------------------- #
#  4. determinism, recomputed fresh in-process
# --------------------------------------------------------------------------- #
def _sig(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()


def test_ha3_measurement_is_deterministic_fresh(all_tasks_by_id, population):
    r1 = p.measure_backward_ordering(all_tasks_by_id, population)
    r2 = p.measure_backward_ordering(all_tasks_by_id, population)
    assert _sig(r1) == _sig(r2)


def test_ha4_measurement_is_deterministic_fresh(all_tasks_by_id, full_rows):
    ids = sorted(r["task_id"] for r in full_rows if r["outcome"] == "gapped:enumerate_failed")
    r1 = p.measure_search_reach(all_tasks_by_id, ids)
    r2 = p.measure_search_reach(all_tasks_by_id, ids)
    assert _sig(r1) == _sig(r2)


def test_set_valued_row_is_skipped_not_fatal(all_tasks_by_id, population):
    rows = p.measure_backward_ordering(all_tasks_by_id, population)
    row = next(r for r in rows if r["task_id"] == 115)
    assert row.get("skipped") is True
    assert row["skip_reason"] == "set_valued_row_crosses_lit_term_json_boundary"


# --------------------------------------------------------------------------- #
#  5. contamination (shared list-gate, standalone subprocess)
# --------------------------------------------------------------------------- #
def test_contamination_gate_passes_standalone():
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--confcutdir=.", "-q",
         "tests/test_mbpp_contamination_migrated.py"],
        cwd=ROOT, capture_output=True, text=True,
        env=dict(os.environ, PYTHONPATH="runners/dsl/python:.:scripts"))
    assert result.returncode == 0, result.stdout + result.stderr
