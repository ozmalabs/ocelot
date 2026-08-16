"""test_engineering_residual_gap_migrated -- Proposal 3 (measured-residual
filing), DESIGN_REVIEW_CAPABILITY_EXPANSION_PREREG.md sec4;
docs/research/engine_substrate/MEASURED_RESIDUAL_FILING_PREREG.md /
MEASURED_RESIDUAL_FILING_RESULTS.md.

seeds/engineering_residual_gap.json's two rules (note_engineering_residual_gap
/ retire_resolved_engineering_residual_gap) mirror gap_awareness.json's own
dedup/retire discipline (note_unresolved_topic_gap / retire_duplicate_gap)
verbatim, pointed at EngineeringResidual fact nodes a diagnostic script
mechanically ingests (domains.engineering_residual_ingest.ingest_taxonomy)
instead of a Goal/Message outcome. These tests exercise the SAME `agent`
fixture pattern as tests/test_gap_awareness_migrated.py: a full seed-loaded
WorldAdapter, not the real jabberwock daemon.
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
import domains.engineering_residual_ingest as eri
import domains.reflective_faculty as rf


@pytest.fixture()
def agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


# A schema-accurate taxonomy dict -- the exact {outcome: {"n": count,
# "task_ids": [...]}} shape mbpp_endgame_battery.taxonomy() and (via reuse)
# ceiling3_diag_sweep.py's own ingest_engineering_residuals both build.
def _taxonomy(**outcomes):
    return {k: {"n": n, "task_ids": list(range(n))} for k, n in outcomes.items()}


def _engineering_concerns(a, *, include_retired=False):
    out = []
    for sc in a.s.nodes("SelfConcern"):
        at = a.s.node(sc)["attrs"]
        if at.get("kind") != "engineering_residual":
            continue
        if not include_retired and at.get("status") == "retired":
            continue
        out.append(at)
    return out


def test_ingest_mints_one_selfconcern_per_population(agent):
    tax = _taxonomy(**{
        "gapped:enumerate_failed": 67,
        "accepted_holdout_fail": 60,
        "not_recognized": 1,
    })
    eri.ingest_taxonomy(agent.s, agent.agent, source_script="t1", taxonomy=tax)
    concerns = _engineering_concerns(agent)
    assert len(concerns) == 3, "one SelfConcern per POPULATION, never per task-id"
    contents = {c["content"] for c in concerns}
    assert contents == {
        "t1:gapped:enumerate_failed", "t1:accepted_holdout_fail", "t1:not_recognized",
    }
    for c in concerns:
        assert c["status"] == "noted"
        assert c["source"] == "implicit"
        # the count/task_ids are carried on the concern (readback convenience),
        # but granularity is still population-grain: exactly one node per
        # outcome bucket, never one per task_id in that bucket.
        assert isinstance(c["count"], int) and c["count"] > 0


def test_pass_bucket_never_mints_a_gap(agent):
    tax = _taxonomy(**{"pass": 88, "accepted_holdout_fail": 60})
    eri.ingest_taxonomy(agent.s, agent.agent, source_script="t2", taxonomy=tax)
    concerns = _engineering_concerns(agent)
    assert len(concerns) == 1
    assert concerns[0]["content"] == "t2:accepted_holdout_fail"
    assert not any(c["content"].endswith(":pass") for c in concerns)


def test_reingest_identical_taxonomy_is_deduped(agent):
    tax = _taxonomy(**{"gapped:enumerate_failed": 67, "accepted_holdout_fail": 60})
    eri.ingest_taxonomy(agent.s, agent.agent, source_script="t3", taxonomy=tax)
    n1 = len(_engineering_concerns(agent))
    eri.ingest_taxonomy(agent.s, agent.agent, source_script="t3", taxonomy=tax)
    n2 = len(_engineering_concerns(agent))
    assert n1 == 2
    assert n2 == n1, "re-ingesting the SAME measurement must not duplicate concerns"


def test_count_zero_retires_the_concern_others_stay_live(agent):
    tax = _taxonomy(**{
        "gapped:enumerate_failed": 67,
        "accepted_holdout_fail": 60,
        "not_recognized": 1,
    })
    eri.ingest_taxonomy(agent.s, agent.agent, source_script="t4", taxonomy=tax)
    assert len(_engineering_concerns(agent)) == 3

    tax2 = dict(tax)
    tax2["accepted_holdout_fail"] = {"n": 0, "task_ids": []}
    eri.ingest_taxonomy(agent.s, agent.agent, source_script="t4", taxonomy=tax2)

    live = _engineering_concerns(agent)
    all_concerns = _engineering_concerns(agent, include_retired=True)
    retired = [c for c in all_concerns if c["status"] == "retired"]
    assert len(live) == 2, "the re-measured-to-zero population must retire"
    assert len(retired) == 1
    assert retired[0]["content"] == "t4:accepted_holdout_fail"
    assert {c["content"] for c in live} == {"t4:gapped:enumerate_failed", "t4:not_recognized"}


def test_population_vanishing_from_taxonomy_also_retires(agent):
    """Absence is zero (CLAUDE.md's own unknown-is-absence-first-class
    precedent) -- a population that simply disappears from a later taxonomy
    (not just count->0) retires exactly like an explicit zero."""
    tax = _taxonomy(**{"gapped:enumerate_failed": 67, "accepted_holdout_fail": 60})
    eri.ingest_taxonomy(agent.s, agent.agent, source_script="t5", taxonomy=tax)
    tax2 = _taxonomy(**{"gapped:enumerate_failed": 67})  # accepted_holdout_fail vanished
    eri.ingest_taxonomy(agent.s, agent.agent, source_script="t5", taxonomy=tax2)
    live = _engineering_concerns(agent)
    assert len(live) == 1
    assert live[0]["content"] == "t5:gapped:enumerate_failed"


def test_run_self_gaps_surfaces_engineering_residual_with_zero_new_plumbing(agent):
    tax = _taxonomy(**{"gapped:enumerate_failed": 67, "accepted_holdout_fail": 60})
    eri.ingest_taxonomy(agent.s, agent.agent, source_script="t6", taxonomy=tax)
    gaps = rf._run_self_gaps(agent.s)
    eng = [c for c in gaps["concerns"] if c["kind"] == "engineering_residual"]
    assert len(eng) == 2
    contents = {c["content"] for c in eng}
    assert contents == {"t6:gapped:enumerate_failed", "t6:accepted_holdout_fail"}
    # by_source groups it under 'implicit', the same source note_solve_
    # exhausted_gap/note_unresolved_topic_gap already use, with zero new
    # entries in reflective_faculty._GAP_SOURCE_ORDER.
    assert "implicit" in gaps["by_source"]


def test_converse_what_gaps_do_you_have_surfaces_it(agent):
    tax = _taxonomy(**{"accepted_holdout_fail": 60})
    eri.ingest_taxonomy(agent.s, agent.agent, source_script="t7", taxonomy=tax)
    reply = agent.converse("what gaps do you have?")
    assert "t7:accepted_holdout_fail" in reply
    assert "engineering_residual" in reply


def test_two_source_scripts_never_collide(agent):
    eri.ingest_taxonomy(agent.s, agent.agent, source_script="script_a",
                        taxonomy=_taxonomy(**{"accepted_holdout_fail": 60}))
    eri.ingest_taxonomy(agent.s, agent.agent, source_script="script_b",
                        taxonomy=_taxonomy(**{"accepted_holdout_fail": 12}))
    concerns = _engineering_concerns(agent)
    contents = {c["content"] for c in concerns}
    assert contents == {"script_a:accepted_holdout_fail", "script_b:accepted_holdout_fail"}
