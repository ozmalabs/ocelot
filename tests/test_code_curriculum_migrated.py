"""CODE-CURRICULUM: the jabberwock LEARNS through its own surfaces, measured.

Part A -- the named seam: a promoted `code_write` StandingConcern grounds
DIRECTLY into the CODE-4 compose path (scripts/jabberwock_daemon.py's
`_process_code_write_standing`, wired into `_concern_tick`) instead of the
generic induce_concern/ground_concern capability-axis machinery; on
exhaustion the SAME `experiments_exhausted`/`exhausted_note` trail every
other concern kind surfaces through names teach-by-example
(seeds/code_write_gap.json's `note_code_write_composition_exhausted`).

Part B -- the hand-curated teach-by-example / predication / read-growth
batches, and the deterministic before/after measurement protocol
(domains/code_curriculum.py's `scan_repo_functions` / `run_write_battery`).

Part C -- PUBLISHED CURRICULUM ingestion (domains/code_curriculum.py): a
REAL published lesson document (bundled verbatim excerpts from Think
Python 2e, chapter 6 "Fruitful functions" -- tests/fixtures/code_curriculum/,
provenance.json) is a MIXED-REGISTER document; code blocks are found BY
SHAPE (the existing register-source codebook) and taught with lesson
provenance; a beyond-boundary lesson files gaps, never a fabricated shape.

Run: PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 python3 -m pytest \
     tests/test_code_curriculum_migrated.py -p no:randomly -q
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
          os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

srs = pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter          # noqa: E402
from substrate.boot_all import load_all_seeds             # noqa: E402
from domains import code_reading as cdr                   # noqa: E402
from domains import code_write_growth as cwg              # noqa: E402
from domains import code_curriculum as cc                 # noqa: E402
from domains.teach import teach                           # noqa: E402
import scripts.jabberwock_daemon as jd                     # noqa: E402

FIXTURE_DIR = os.path.join(ROOT, "tests", "fixtures", "code_curriculum")
CORPUS_DIR = "tests/fixtures/code_curriculum/measurement_corpus"


@pytest.fixture(autouse=True)
def _no_real_seed_writes(monkeypatch):
    monkeypatch.setenv("OZMA_SEED_PERSIST_DISABLED", "1")


@pytest.fixture()
def full_agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


def _nid(n):
    return str(n.value if hasattr(n, "value") else n)


def _code_write_concern(agent, content):
    for n in agent.s.nodes("SelfConcern"):
        at = agent.s.node(n)["attrs"]
        if at.get("kind") == "code_write" and at.get("content") == content:
            return n
    return None


# =========================================================================== #
#  PART A -- the named seam: code_write StandingConcern grounds through the
#  daemon's real self-improvement spine, not the generic capability-axis path.
# =========================================================================== #
def test_code_write_concern_promotes_and_grounds_through_daemon_spine(full_agent):
    a = full_agent
    req = "Write a function that triples a number."
    reply = a.converse(req)
    assert "don't hold a shape" in reply
    sc = _code_write_concern(a, req)
    assert sc is not None

    res = jd.promote_self_concern(a, _nid(sc))
    assert res["ok"] and res["kind"] == "code_write" and res["pipeline"] == "code_write"
    # the ORIGINAL concern's status flips to 'promoted' (the generic promote
    # contract) -- resolve_code_write_gap must still recognise it there.
    assert a.s.node(sc)["attrs"]["status"] == "promoted"

    jd._concern_tick(a)
    standing = None
    for n in a.s.nodes("StandingConcern"):
        if a.s.node(n)["attrs"].get("name") == f"promoted_self_concern_{res['self_concern']}":
            standing = n
    assert standing is not None
    st = a.s.node(standing)["attrs"]
    assert st["status"] == "processed"
    # the mechanical outcome datum _process_code_write_standing records.
    assert st["code_write_compose_ok"] == 1.0
    assert "composed_triple" in (st.get("code_write_compose_reason") or "")

    a.comprehend()
    assert a.s.node(sc)["attrs"]["status"] == "resolved"
    reply2 = a.converse(req)
    assert "Here is the function" in reply2


def test_code_write_concern_exhausts_honestly_through_daemon_spine(full_agent):
    a = full_agent
    req = "Write a function that reverses a string."
    a.converse(req)
    sc = _code_write_concern(a, req)
    assert sc is not None
    res = jd.promote_self_concern(a, _nid(sc))
    assert res["ok"]
    jd._concern_tick(a)
    a.comprehend()

    import domains.reflective_faculty as rf
    status = rf._run_self_improvement_status(a.s)
    row = next(s for s in status["standing"]
              if s["name"] == f"promoted_self_concern_{res['self_concern']}")
    assert row["exhausted"] is True
    assert "teach-by-example" in row["exhausted_note"]
    # the ORIGINAL concern stays open (never silently marked resolved).
    assert a.s.node(sc)["attrs"]["status"] != "resolved"


def test_promote_relations_route_code_write_never_experiment_or_comprehend_first():
    relations, pipeline = jd._promote_relations_for_concern(
        "code_write", ["reverses", "string"], "REVERSES")
    assert pipeline == "code_write"
    assert relations[0] == ["compose", "SHAPE", "from", "PREDICATION"]
    heads = {r[0] for r in relations}
    assert "test" not in heads and "comprehend" not in heads


def test_code_write_gap_is_refreshable_seed_for_the_edited_rules():
    assert "code_write_gap" in jd._REFRESHABLE_SEEDS


# =========================================================================== #
#  PART B -- teach-by-example curriculum entry + predication-teach + compose
#  slice, end to end through the SAME daemon spine part A wired.
# =========================================================================== #
def test_teach_by_example_curriculum_entry_end_to_end(full_agent):
    a = full_agent
    req = "Write a function that clamps a number between a lower and upper bound."
    src = "def clamp(x, lo, hi):\n    return lo if x < lo else (hi if x > hi else x)\n"
    assert "don't hold a shape" in a.converse(req)
    res = cwg.teach_write_shape_from_example(a, src, request_text=req)
    assert res["ok"], res
    assert res["validate"]["agree"] is True
    reply = a.converse(req)
    assert "Here is the function" in reply
    ns: dict = {}
    exec(reply.split("Here is the function:\n\n", 1)[1], ns)  # noqa: S102
    fn = ns["generated_function"]
    assert fn(5, 0, 10) == 5 and fn(-5, 0, 10) == 0 and fn(50, 0, 10) == 10


def test_hand_curated_batch_honest_split_between_learned_and_gapped(full_agent):
    a = full_agent
    ok_cases = [
        ("Write a function that flips the sign of a number.",
         "def sign_flip(x):\n    return -x\n"),
        ("Write a function that sums the squares of a list of numbers.",
         "def sum_of_squares(items):\n"
         "    total = 0\n    for x in items:\n        total += x ** 2\n    return total\n"),
    ]
    beyond_cases = [
        ("Write a function that computes the absolute difference of two numbers.",
         "def abs_diff(a, b):\n    return abs(a - b)\n"),          # unheld Call leaf
        ("Write a function that counts the positive numbers in a list.",
         "def count_positives(items):\n"
         "    count = 0\n    for x in items:\n"
         "        if x > 0:\n            count += 1\n    return count\n"),  # cond accumulate
    ]
    for req, src in ok_cases:
        a.converse(req)
        res = cwg.teach_write_shape_from_example(a, src, request_text=req)
        assert res["ok"], res
    for req, src in beyond_cases:
        a.converse(req)
        res = cwg.teach_write_shape_from_example(a, src, request_text=req)
        assert res["ok"] is False and "reason" in res


def test_predication_teach_and_compose_slice_through_daemon_spine(full_agent):
    a = full_agent
    req = "Write a function that quintuples a number."
    assert "don't hold a shape" in a.converse(req)
    t = teach(a, "Concept", {"name": "quintuple", "multiplier_factor": 5.0,
                             "description": "multiply by five"},
             category="write_shape_predication")
    assert t["node"] is not None
    sc = _code_write_concern(a, req)
    assert sc is not None
    res = jd.promote_self_concern(a, _nid(sc))
    assert res["ok"]
    jd._concern_tick(a)
    a.comprehend()
    reply = a.converse(req)
    assert "Here is the function" in reply
    ns: dict = {}
    exec(reply.split("Here is the function:\n\n", 1)[1], ns)  # noqa: S102
    assert ns["generated_function"](3) == 15.0


def test_read_mint_on_unseen_shape_files_naming_gap(full_agent):
    a = full_agent
    src = "def countdown(n):\n    while n > 0:\n        n -= 1\n    return n\n"
    r = cdr.read_function(a, src, "countdown")
    assert r.get("minted") is True
    assert r.get("construction") == "learned_code_while_return"
    a.comprehend()
    gaps = cwg.pending_naming_gaps(a)
    assert "learned_code_while_return" in [g["content"] for g in gaps]


# =========================================================================== #
#  MEASUREMENT PROTOCOL -- deterministic on a small fixture corpus (isolated
#  from the live repo tree, so a concurrent session editing domains/*.py can
#  never flake this gate).
# =========================================================================== #
def test_scan_repo_functions_deterministic_on_fixture_corpus(full_agent):
    a = full_agent
    scan = cc.scan_repo_functions(a, [CORPUS_DIR])
    assert scan["n_files"] == 2
    assert scan["n_functions"] == 3
    assert scan["counts"]["construction_recognized"] == 3
    assert scan["counts"]["term_emittable"] == 2
    assert scan["counts"]["predict_correct"] == 2
    names = sorted(row["name"] for row in scan["rows"])
    assert names == ["add", "is_positive", "loopy"]
    loopy = next(row for row in scan["rows"] if row["name"] == "loopy")
    assert loopy["emittable"] is False
    assert loopy["construction"] == "learned_code_while_return"


def test_write_battery_measures_before_after_delta(full_agent):
    a = full_agent
    battery = ["Write a function that flips the sign of a number.",
              "Write a function that returns the larger of two numbers."]
    before = cc.run_write_battery(a, battery)
    assert before["n_ok"] == 1   # only the held starter shape answers
    a.converse(battery[0])
    res = cwg.teach_write_shape_from_example(
        a, "def sign_flip(x):\n    return -x\n", request_text=battery[0])
    assert res["ok"]
    after = cc.run_write_battery(a, battery)
    assert after["n_ok"] == 2


# =========================================================================== #
#  PART C -- PUBLISHED CURRICULUM: one REAL lesson document, end to end.
# =========================================================================== #
def _lesson(name: str) -> str:
    return open(os.path.join(FIXTURE_DIR, name)).read()


def test_published_lesson_code_block_detected_by_shape():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    text = _lesson("lesson_boolean_functions.txt")
    regions = cc.code_regions(a, text)
    assert regions, "no region decoded as the 'code' family"
    joined = "\n".join(r["text"] for r in regions)
    assert "def is_divisible" in joined


def test_published_lesson_teaches_a_shape_with_lesson_provenance_and_paired_request_succeeds(full_agent):
    a = full_agent
    text = _lesson("lesson_boolean_functions.txt")
    # SHORT paired request: ShapeDecode's fit erodes with unrelated filler
    # tokens (a real, verified property of the engine, not a defect this
    # wave should paper over) -- a terse request keyed on the shape's own
    # content word ('divisible') is the realistic, honest phrasing.
    req = "Write a function that tests divisible."
    learned = cc.learn_functions_from_lesson(
        a, text, lesson_source="lesson_boolean_functions.txt")
    ok_rows = [r for r in learned if r["ok"]]
    assert ok_rows, learned
    assert ok_rows[0]["shape"] == "taught_is_divisible"
    # provenance landed on the taught ShapeSignature (capability_report reads
    # it back, never re-derives it).
    report = cc.capability_report(a)
    published = report["learned_from_published"]
    assert any(r["name"] == "taught_is_divisible"
              and r["lesson_source"] == "lesson_boolean_functions.txt"
              for r in published)
    # a PAIRED request (the SAME division-predicate content word) succeeds --
    # the shape was learned by the agent's OWN reading, not hand-authored.
    reply = a.converse(req)
    assert "Here is the function" in reply
    ns: dict = {}
    exec(reply.split("Here is the function:\n\n", 1)[1], ns)  # noqa: S102
    fn = ns["generated_function"]
    assert fn(6, 3) is True and fn(6, 4) is False


def test_published_beyond_boundary_lesson_files_gaps_not_shapes(full_agent):
    a = full_agent
    text = _lesson("lesson_incremental_development.txt")
    res = cc.learn_from_lesson(a, text, lesson_source="lesson_incremental_development.txt")
    # every distance() variant that actually reached the emitter (the
    # placeholder scaffolding step) is a real, validated shape -- but the
    # exercise line ("...write a function called hypotenuse...") is a
    # genuine unanswered request: no held shape covers it, so it must file
    # a code_write capability gap, never a fabricated hypotenuse shape.
    a.comprehend()
    gaps = cwg.pending_code_write_gaps(a)
    gap_contents = [g["content"] for g in gaps]
    assert any("hypotenuse" in c for c in gap_contents), gap_contents
    report = cc.capability_report(a)
    assert not any("hypotenuse" in (r.get("name") or "") for r in report["learned_from_published"])
    assert res["requests"], "the exercise line was never attempted through the request path"


def test_published_lesson_pipeline_is_deterministic_no_network():
    """Two independent fresh agents reading the SAME bundled fixture text
    learn the SAME shapes -- no network call, no randomness.

    WHOLE-CURRICULUM WAVE 2: the fixture's FIRST `is_divisible` definition
    (an explicit `if x % y == 0: return True / else: return False`) was
    previously beyond the emitter's boundary (branching return statements
    were not yet a Term-emittable shape) and reported `ok: False`; only
    the SECOND definition (`return x % y == 0`, a bare comparison) taught
    successfully. `branching_return` now emits the first one too, so
    BOTH definitions teach -- both named `taught_is_divisible` (the shape
    name derives from the function name, not the construction), a
    genuine capability gain, not a regression."""
    a1 = WorldAdapter(seeds=())
    load_all_seeds(a1)
    a2 = WorldAdapter(seeds=())
    load_all_seeds(a2)
    text = _lesson("lesson_boolean_functions.txt")
    r1 = cc.learn_functions_from_lesson(a1, text, lesson_source="x")
    r2 = cc.learn_functions_from_lesson(a2, text, lesson_source="x")
    shapes1 = sorted(r["shape"] for r in r1 if r["ok"])
    shapes2 = sorted(r["shape"] for r in r2 if r["ok"])
    assert shapes1 == shapes2 == ["taught_is_divisible", "taught_is_divisible"]


# =========================================================================== #
#  SELF-ACCOUNT -- the code-capability reader.
# =========================================================================== #
def test_self_account_reports_growth_by_provenance(full_agent):
    a = full_agent
    assert "have not grown it yet" in a.converse("What can you do with code now?")
    text = _lesson("lesson_boolean_functions.txt")
    cc.learn_functions_from_lesson(a, text, lesson_source="lesson_boolean_functions.txt")
    note = a.converse("What can you do with code now?")
    assert "learned from published material" in note
    assert "taught_is_divisible" in note
    assert "lesson_boolean_functions.txt" in note
