"""tests/test_mbpp_diet_migrated.py — Arc 2 Q3 gates: THE PAIRED DIET.

PROGRAM_SYNTHESIS_ARC2_PLAN.md sec2 Q3 / PROGRAM_SYNTHESIS_ARC2_Q3_NOTES.md.
Gates:
  1. mining determinism (twin-run byte-identical `mine_diet` output);
  2. provenance completeness — every minted node (chunk / bigram /
     affinity) in `seeds/mbpp_train_diet.json` carries `source_task_ids`,
     every id in [601, +inf) — a list-gate, never a count;
  3. seed loads clean via `load_seed_manifest` + idempotent install
     (`domains.prog_chunk_growth.ensure_mbpp_train_diet`);
  4. the trigger-coverage headline number is DERIVED from the artifact's
     own per-chunk rows (never quoted bare);
  5. the leave-N-out transfer probe's 3 pinned holdout tasks RE-VERIFY
     LIVE (one mined-chunk-used case, one bigram-lattice-improved-without-
     a-chunk case, one honest not-used case) — under a protected CONTROL
     arm (starter codebook + arc-1 bigrams only, no diet);
  6. contamination — this phase's own scan of its OWN new artifacts
     (mirroring the Q2 precedent: the shared list-gate's SCAN_TARGETS is
     owned by the sibling Q0-A track and is not extended here), PLUS the
     shared gate itself is reported green in PROGRAM_SYNTHESIS_ARC2_Q3_
     NOTES.md (run separately, not re-imported here to avoid coupling to
     its internal fixtures twice over);
  7. the arc-1 chunk suite (`test_prog_chunks_migrated.py`, 11 tests)
     stays green — reported in the notes doc (this phase's extensions to
     `domains/prog_chunk_growth.py` are strictly additive: two new
     functions + one new installer, zero edits to existing bodies).

Run (worktree engine discipline):
    PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 \
        OZMA_SEED_PERSIST_DISABLED=1 pytest --confcutdir=. \
        tests/test_mbpp_diet_migrated.py -q
"""
from __future__ import annotations

import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import substrate_rs as srs  # noqa: E402

from domains import prog_chunk_growth as pcg  # noqa: E402
import mbpp_train_diet as mtd  # noqa: E402

RESULTS_PATH = os.path.join(ROOT, "results", "mbpp_train_diet.json")
SEED_PATH = os.path.join(ROOT, "seeds", "mbpp_train_diet.json")


def _term_live(term, env) -> bool:
    s = srs.Substrate()
    try:
        s._inner.evaluate(term, env)
        return True
    except ValueError as e:
        if "UnknownTermType" in str(e):
            return False
        raise


if not _term_live({"type": "ShapeDecode", "goal": {"type": "Var", "name": "g"},
                   "beam": 1, "max_steps": 2, "cand_k": 1, "field": "",
                   "wild_objects": False}, {"g": [["p", "x"]]}) or \
   not _term_live({"type": "ProgEval",
                   "prog": {"type": "ProgSeq", "stmts": []},
                   "env": None, "oracles": None, "fuel": 5, "field": ""}, {}):
    pytest.skip("ShapeDecode/ProgEval not present in the installed "
                "substrate_rs binary — rebuild runners/dsl. Honest skip.",
                allow_module_level=True)


@pytest.fixture(scope="module")
def train_tasks():
    return mtd.load_train_tasks()


@pytest.fixture(scope="module")
def results_artifact():
    with open(RESULTS_PATH) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def seed_manifest():
    with open(SEED_PATH) as f:
        return json.load(f)


# --------------------------------------------------------------------------- #
#  0 — scope sanity: exactly the 120 train tasks, all task_id >= 601.
# --------------------------------------------------------------------------- #
def test_train_split_is_120_tasks_all_ge_601(train_tasks):
    assert len(train_tasks) == 120
    assert all(t["task_id"] >= 601 for t in train_tasks)


# --------------------------------------------------------------------------- #
#  1 — mining determinism (twin-run byte-identical `mine_diet`).
# --------------------------------------------------------------------------- #
def test_mine_diet_is_byte_deterministic(train_tasks):
    d1 = mtd.mine_diet(train_tasks)
    d2 = mtd.mine_diet(train_tasks)
    assert mtd._canonical_blob(d1) == mtd._canonical_blob(d2)


def test_shipped_artifact_records_byte_identical_twin_run(results_artifact):
    det = results_artifact["determinism"]
    assert det["runs"] == 2
    assert det["byte_identical"] is True
    assert det["sha256_run1"] == det["sha256_run2"]


# --------------------------------------------------------------------------- #
#  2 — provenance completeness: every node carries source_task_ids, every
#      id is train-only (>=601, never in the test split [11,510]).
# --------------------------------------------------------------------------- #
def test_every_seed_node_carries_train_only_source_task_ids(seed_manifest):
    missing = []
    contaminated = []
    for n in seed_manifest["nodes"]:
        ids = n["attrs"].get("source_task_ids")
        if not ids:
            missing.append(n)
            continue
        for tid in ids:
            if not (tid >= 601):
                contaminated.append((n["attrs"].get("name") or n["type"], tid))
    assert missing == [], "nodes with no source_task_ids provenance: %r" % (missing,)
    assert contaminated == [], (
        "non-train-split task ids found in seed provenance: %r" % (contaminated,))


def test_seed_node_count_matches_results_row_counts(results_artifact, seed_manifest):
    n_chunks = len(results_artifact["chunks"]["chunks"])
    n_bigrams = len(results_artifact["bigrams"]["bigrams"])
    n_affinity = len(results_artifact["affinity"]["affinity_rows"])
    by_type = {}
    for n in seed_manifest["nodes"]:
        by_type[n["type"]] = by_type.get(n["type"], 0) + 1
    assert by_type.get("ShapeSignature", 0) == n_chunks
    assert by_type.get("ConstructionBigram", 0) == n_bigrams
    assert by_type.get("ConstructionAffinity", 0) == n_affinity


def test_no_test_split_task_ids_anywhere_in_results_artifact(results_artifact):
    """A direct, mechanical id-range audit of the shipped MEASUREMENT
    artifact (distinct from — and stronger for THIS artifact's shape than
    — the shared substring gate, since this artifact embeds derived WORDS
    and STRUCTURE, not verbatim prompt/code text)."""
    for row in results_artifact["emit"]["rows"]:
        assert row["task_id"] >= 601
    for c in results_artifact["chunks"]["chunks"]:
        assert all(tid >= 601 for tid in c["source_task_ids"])
    for b in results_artifact["bigrams"]["bigrams"]:
        assert all(tid >= 601 for tid in b["source_task_ids"])
    for a in results_artifact["affinity"]["affinity_rows"]:
        assert all(tid >= 601 for tid in a["source_task_ids"])
    probe = results_artifact["leave_n_out_probe"]
    assert all(tid >= 601 for tid in probe["mine_set_task_ids"])
    assert all(tid >= 601 for tid in probe["holdout_task_ids"])


# --------------------------------------------------------------------------- #
#  3 — seed loads clean via load_seed_manifest + idempotent install.
# --------------------------------------------------------------------------- #
def _boot():
    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    from domains import prog_synthesis as psy
    psy.ensure_program_synthesis(s, s._inner, ag)
    return s, ag


def test_seed_loads_clean_via_manifest_for():
    from substrate.seed_loader import manifest_for
    manifest = manifest_for("mbpp_train_diet")
    assert manifest["id"] == "mbpp_train_diet"
    assert len(manifest["nodes"]) > 0
    s = srs.Substrate()
    summary = s._inner.load_seed_manifest(manifest, None)
    assert summary.get("rules_skipped") in (None, [], 0)
    assert summary.get("reflexes_skipped") in (None, [], 0)
    assert summary["nodes"] == len(manifest["nodes"])


def test_ensure_mbpp_train_diet_installs_once_and_is_idempotent():
    s, ag = _boot()
    n1 = pcg.ensure_mbpp_train_diet(s, s._inner, ag)
    assert n1 > 0
    n2 = pcg.ensure_mbpp_train_diet(s, s._inner, ag)
    assert n2 == 0   # Seed-marker guard: no duplicate install

    names = [s.node(n)["attrs"].get("name") for n in s.nodes("ShapeSignature")
            if s.node(n)["attrs"].get("provenance") == "mbpp_train_chunk"]
    assert len(names) == len(set(names)), "duplicate chunk names after double install"


def test_ensure_mbpp_train_diet_boards_bigrams_additively_alongside_arc1():
    """Installing the mbpp_train diet must never remove/rewrite the arc-1
    P3-corpus ConstructionBigram population — both provenances coexist."""
    s, ag = _boot()   # ensure_program_synthesis already boarded arc-1 bigrams
    arc1_before = sum(1 for n in s.nodes("ConstructionBigram")
                      if s.node(n)["attrs"].get("source") == "prog_construction_scan.json")
    assert arc1_before > 0
    pcg.ensure_mbpp_train_diet(s, s._inner, ag)
    arc1_after = sum(1 for n in s.nodes("ConstructionBigram")
                     if s.node(n)["attrs"].get("source") == "prog_construction_scan.json")
    mbpp_after = sum(1 for n in s.nodes("ConstructionBigram")
                     if s.node(n)["attrs"].get("provenance") == "mbpp_train")
    assert arc1_after == arc1_before, "arc-1 bigram rows were disturbed"
    assert mbpp_after > 0


def test_chunk_names_use_a_distinct_namespace_from_arc1_and_self_taught(seed_manifest):
    import re
    names = [n["attrs"]["name"] for n in seed_manifest["nodes"]
            if n["type"] == "ShapeSignature"]
    assert names, "no mined chunks in the seed"
    for name in names:
        assert re.match(r"^mck_[a-z0-9_]+_n[0-9]+_q[0-9]+$", name), name
        assert not name.startswith("ck_")
        assert not name.startswith("ckt_")
        assert len(name) <= 40


# --------------------------------------------------------------------------- #
#  4 — trigger-coverage headline, derived from the artifact's own rows.
# --------------------------------------------------------------------------- #
def test_trigger_coverage_headline_is_derived_from_rows(results_artifact):
    chunks = results_artifact["chunks"]["chunks"]
    assert len(chunks) > 0
    derived_with_trigger = sum(1 for c in chunks if c["trigger_tokens"])
    reported = results_artifact["chunks"]["totals"]["with_nonzero_trigger"]
    assert derived_with_trigger == reported
    # the arc-1 P7-C baseline was 2/15 cueable-with-trigger (quoted, not
    # recomputed — a historical record, PROGRAM_SYNTHESIS_P7C.md sec2.3).
    arc1_fraction = 2 / 15
    this_fraction = derived_with_trigger / len(chunks)
    assert this_fraction > arc1_fraction, (
        "Q3's paired-prompt triggers did not improve on arc-1's code-derived "
        "2/15 cueable-with-trigger baseline: %r vs %r" % (this_fraction, arc1_fraction))


def test_every_chunk_carries_derived_prompt_tokens_honestly(results_artifact):
    """Every chunk reports its full scored candidate list, whether or not
    it ended up cueable — the P7-C honesty convention (`derived_tokens`
    always populated; `trigger_tokens` empty only when structurally
    excluded)."""
    for c in results_artifact["chunks"]["chunks"]:
        assert "derived_prompt_tokens" in c
        if c["cue_excluded"] is not None:
            assert c["trigger_tokens"] == []


# --------------------------------------------------------------------------- #
#  5 — leave-N-out probe: 3 pinned holdout tasks re-verify LIVE, under a
#      protected CONTROL arm (never claim usage a control could explain).
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def probe(train_tasks):
    return mtd.leave_n_out_probe(train_tasks)


def _row(probe, task_id):
    for r in probe["rows"]:
        if r["task_id"] == task_id:
            return r
    raise KeyError(task_id)


def test_probe_scope_is_100_mine_20_holdout(probe):
    assert probe["n_mine"] == 100
    assert probe["n_holdout"] == 20
    assert set(probe["mine_set_task_ids"]).isdisjoint(probe["holdout_task_ids"])


def test_pinned_task_788_uses_a_mined_chunk_the_control_cannot_produce(probe):
    r = _row(probe, 788)
    assert r["used"] is True
    assert r["used_mined_chunk"] is True
    assert str(r["diet"]["construction"]).startswith("mck_")
    assert r["control"]["construction"] is None


def test_pinned_task_809_bigram_content_improves_lattice_without_a_chunk(probe):
    r = _row(probe, 809)
    assert r["used"] is True
    assert r["used_mined_chunk"] is False
    assert r["diverged_from_control"] is True
    # same construction identity in both arms (a starter shape, found via
    # the codebook rung in EITHER arm) -- the divergence is the LATTICE
    # rung succeeding only once the mbpp_train bigram rows are present.
    assert r["control"]["construction"] == r["diet"]["construction"]
    assert r["control"]["rungs"]["lattice"] is None
    assert r["diet"]["rungs"]["lattice"] == 1.0


def test_pinned_task_798_is_an_honest_not_used_null(probe):
    r = _row(probe, 798)
    assert r["used"] is False
    assert r["used_mined_chunk"] is False
    assert r["diverged_from_control"] is False
    # the OUTCOME (status/construction/rungs/spine) is identical between
    # arms -- `manifest_nodes_installed` legitimately differs (0 vs 41),
    # it is bookkeeping, not outcome.
    outcome_keys = ("status", "construction", "rungs", "spine_labels")
    assert {k: r["control"][k] for k in outcome_keys} == \
        {k: r["diet"][k] for k in outcome_keys}


def test_probe_reports_a_nonzero_usage_count(probe):
    assert probe["n_used"] >= 1
    assert probe["n_used"] <= probe["n_holdout"]


# --------------------------------------------------------------------------- #
#  6 — this phase's OWN contamination scan of its OWN new artifacts (the
#      Q2 precedent: the shared gate's SCAN_TARGETS is owned by the
#      sibling Q0-A track and is not extended here).
# --------------------------------------------------------------------------- #
def test_own_contamination_scan_of_new_artifacts_is_clean():
    import re as _re
    ws_re = _re.compile(r"\s+")

    def normalize(s):
        return ws_re.sub(" ", s.strip().lower())

    with open(os.path.join(ROOT, "tests", "fixtures", "mbpp", "sanitized-mbpp.json")) as f:
        tasks = json.load(f)
    test_tasks = [t for t in tasks if 11 <= t["task_id"] <= 510]
    forbidden = []
    for t in test_tasks:
        p = normalize(t["prompt"])
        if len(p) >= 20:
            forbidden.append(p)
        for line in t["code"].splitlines():
            nl = normalize(line)
            if len(nl) >= 15:
                forbidden.append(nl)
    assert len(forbidden) > 200

    for path in (RESULTS_PATH, SEED_PATH,
                os.path.join(ROOT, "scripts", "mbpp_train_diet.py")):
        with open(path, errors="replace") as f:
            raw = normalize(f.read())
        hits = [sub for sub in forbidden if sub in raw]
        assert hits == [], "%s contains test-split content: %r" % (path, hits[:5])
