"""CODE-4: THE AGENT GROWS ITS OWN CODE FACULTY (domains/code_write_growth.py,
seeds/code_write_gap.json, seeds/write_shape_predication.json,
seeds/code_write_request_cues.json).

The final wave of the code arc: growth is handed to the agent's own loops.

  * GAP PIPELINE — an out-of-vocabulary write request abstains (CODE-3,
    unchanged) AND files SelfConcern{kind:'code_write'} via the
    note_code_write_gap rule (the note_unhandled_instruction_gap precedent:
    mechanical outcome datum + a rule that decides; dedup + mint-once).
  * TEACH BY EXAMPLE (the must-land) — the human pastes a real function in
    chat; the agent READS it (CODE-1/2), validates the read Term by running,
    TEACHES it as a new write shape (teach(), the cue-adoption precedent);
    the ORIGINAL request now succeeds; the resolve_code_write_gap rule marks
    the gap resolved from the taught shape's own taught_for provenance.
  * COMPOSE FROM PREDICATION — "doubles"/"triples" resolve against the held
    morphological vocabulary and compose Times(Var,k) from held Terms;
    outside that small family the trail EXHAUSTS HONESTLY, naming
    teach-by-example as the remaining close.
  * CUE CONCEPTS — looks_like_write_request's word sets are held Concepts
    (parity gated: existing phrasings byte-identical; a taught phrasing
    routes; unrelated turns never hijacked).
  * IDENTIFIER GROUNDING — identifier words case-split and run through the
    EXISTING teacher chain (ground_unknowns), previously a dead end.
  * VALIDATE-BY-RUNNING GATES THE REPLY — a written function is exec'd in
    isolation against the agent's own model prediction; disagreement blocks
    the hand-over (honest reply + gap datum).
  * READ-CODEBOOK RESIDUAL — a minted learned_code_* construction (generic
    placeholder desc) files a low-priority naming gap, once.
  * SOURCE AUDIT — code_write_growth.py uses sanctioned surfaces only.

Run: PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 python3 -m pytest \
     tests/test_code_growth_migrated.py -p no:randomly -q
"""
from __future__ import annotations

import ast
import json
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
from domains import code_writing as cw                    # noqa: E402
from domains import code_write_growth as cwg              # noqa: E402


@pytest.fixture(autouse=True)
def _no_real_seed_writes(monkeypatch):
    # The durable teach() guard: chat-path teaching in these tests must never
    # mutate the real boot seed files (the twice-bitten runs-47/48 lesson).
    monkeypatch.setenv("OZMA_SEED_PERSIST_DISABLED", "1")


@pytest.fixture()
def full_agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


@pytest.fixture()
def agent():
    return WorldAdapter()   # CORE_SEEDS boot -- the CODE-3 surface


REQ = "Write a function that doubles a number."
EXAMPLE = "def double(n):\n    return n * 2\n"


# =========================================================================== #
#  (1) THE HEADLINE — OOV request -> gap -> teach-by-example in chat -> the
#      original request succeeds -> validates -> the gap resolves (rule).
# =========================================================================== #
def test_teach_by_example_closes_the_write_gap_end_to_end(full_agent):
    a = full_agent
    # OOV request abstains honestly (CODE-3 contract, unchanged) ...
    reply1 = a.converse(REQ)
    assert "don't hold a shape" in reply1
    # ... AND files the gap (note_code_write_gap, graph rule).
    gaps = cwg.pending_code_write_gaps(a)
    assert [g["content"] for g in gaps] == [REQ]
    assert gaps[0]["status"] == "noted"
    assert gaps[0]["source"] == "implicit"

    # dedup + mint-once: repeating the request files nothing new.
    a.converse(REQ)
    assert len(cwg.pending_code_write_gaps(a)) == 1

    # The human pastes a real example function in chat; the agent reads it,
    # learns the shape, and shows the original request now working.
    reply2 = a.converse(EXAMPLE)
    assert "learned the shape 'taught_double'" in reply2
    assert "def generated_function(n):" in reply2

    # The original request now succeeds through the normal path.
    reply3 = a.converse(REQ)
    assert "Here is the function" in reply3
    src = reply3.split("Here is the function:\n\n", 1)[1]
    ns: dict = {}
    exec(src, ns)  # noqa: S102 -- gate exec of the agent's written source
    assert ns["generated_function"](7) == 14

    # The gap resolves in the agent's own rule pass, from the taught shape's
    # taught_for provenance -- a graph decision, not a Python status write.
    a.comprehend()
    concerns = [at for at in cwg.pending_code_write_gaps(a)]
    # pending_* returns un-retired concerns of the kind; the resolved one
    # must now carry status='resolved'.
    assert concerns and all(c["status"] == "resolved" for c in concerns
                            if c["content"] == REQ)


def test_taught_shape_persists_as_a_teach_record(full_agent, tmp_path):
    a = full_agent
    a.converse(REQ)
    out = cwg.teach_write_shape_from_example(a, EXAMPLE, request_text=REQ,
                                             seeds_dir=tmp_path)
    assert out["ok"], out
    assert out["validate"]["agree"] is True
    manifest = json.loads((tmp_path / "code_write_constructions.json").read_text())
    names = [n["attrs"]["name"] for n in manifest["nodes"]]
    assert "taught_double" in names
    node = next(n for n in manifest["nodes"]
                if n["attrs"]["name"] == "taught_double")
    assert node["attrs"]["kind"] == "code_write_construction"
    assert node["attrs"]["taught_for"] == REQ
    tmpl = json.loads(node["attrs"]["ground_template"])
    assert tmpl["term"]["type"] == "Times"


def test_unreadable_example_is_refused_never_fabricated(full_agent):
    a = full_agent
    # A function whose body CODE-1/2 cannot emit a Term for (a while loop)
    # must be an honest refusal, not a fabricated shape.
    out = cwg.teach_write_shape_from_example(
        a, "def spin(n):\n    while n > 0:\n        n -= 1\n    return n\n")
    assert out["ok"] is False
    assert "reason" in out


# =========================================================================== #
#  (2) COMPOSE FROM PREDICATION — the example-free close, and its honest
#      exhausted boundary.
# =========================================================================== #
def test_nl_promote_composes_from_predication_and_resolves(full_agent):
    a = full_agent
    req = "Write a function that triples a number."
    assert "don't hold a shape" in a.converse(req)
    assert [g["content"] for g in cwg.pending_code_write_gaps(a)] == [req]

    res = cwg.work_on_code_write_gap(a, "Work on the triples gap.")
    assert res["ok"], res
    assert res["shape"] == "composed_triple"
    assert res["term"]["type"] == "Times"
    assert res["validate"]["agree"] is True

    a.comprehend()
    assert all(g["status"] == "resolved"
               for g in cwg.pending_code_write_gaps(a) if g["content"] == req)

    reply = a.converse(req)
    assert "Here is the function" in reply
    ns: dict = {}
    exec(reply.split("Here is the function:\n\n", 1)[1], ns)  # noqa: S102
    assert ns["generated_function"](5) == 15.0


def test_composition_exhausts_honestly_outside_the_held_family(full_agent):
    a = full_agent
    req = "Write a function that reverses a string."
    a.converse(req)
    res = cwg.work_on_code_write_gap(a, "Work on the reverses gap.")
    assert res["ok"] is False
    assert "composition exhausted" in res["reason"]
    assert "teach-by-example" in res["reason"]
    # the gap stays noted, awaiting the example.
    assert any(g["content"] == req and g["status"] == "noted"
               for g in cwg.pending_code_write_gaps(a))


# =========================================================================== #
#  (3) CUE CONCEPTS — parity + teachable phrasing.
# =========================================================================== #
_EXISTING_PHRASINGS = [
    ("Write a function that returns the larger of two numbers.", True),
    ("Create a function that returns the sum of two numbers.", True),
    ("Implement a method that returns the count of items in a list.", True),
    ("What is the weather like today?", False),
    ("Tell me about the moon.", False),
]


@pytest.mark.parametrize("text,expected", _EXISTING_PHRASINGS)
def test_cue_concept_parity_existing_phrasings_byte_identical(full_agent, text, expected):
    # graph-held cue sets and the retired closed Python sets agree exactly.
    assert cw.looks_like_write_request(text, full_agent) is expected
    assert cw.looks_like_write_request(text) is expected


def test_taught_new_phrasing_routes(full_agent, tmp_path):
    a = full_agent
    text = "Author a function that returns the sum of two numbers."
    assert cw.looks_like_write_request(text, a) is False
    from domains.teach import teach
    teach(a, "Concept", {"name": "author", "code_request_role": "write_verb"},
          category="code_write_request_cues", seeds_dir=tmp_path)
    assert cw.looks_like_write_request(text, a) is True
    # and through converse: the taught phrasing reaches the write path.
    reply = a.converse(text)
    assert "def generated_function(" in reply


def test_minimal_boot_without_cue_seed_falls_back_to_closed_sets(agent):
    # a CORE_SEEDS boot holds no cue Concepts -> the closed-set fallback
    # classifies byte-identically (parity for every pre-existing caller).
    for text, expected in _EXISTING_PHRASINGS:
        assert cw.looks_like_write_request(text, agent) is expected


# =========================================================================== #
#  (4) IDENTIFIER GROUNDING — through the existing teacher chain.
# =========================================================================== #
def test_identifier_words_ground_through_teacher_chain(agent):
    seen: list = []
    agent._self_teacher = lambda w: seen.append(w) or None
    cwg.ground_identifier_words(agent, ["total_weight", "camelCaseName"])
    # case-split words, deduped, through the SAME per-word teacher loop.
    assert seen == ["total", "weight", "camel", "case", "name"]


def test_identifier_grounding_noops_without_teacher(agent):
    assert cwg.ground_identifier_words(agent, ["total_weight"]) == []


def test_teach_by_example_grounds_the_examples_identifiers(full_agent):
    a = full_agent
    seen: list = []
    a._self_teacher = lambda w: seen.append(w) or None
    a.converse(REQ)
    out = cwg.teach_write_shape_from_example(a, EXAMPLE, request_text=REQ,
                                             seeds_dir=None)
    assert out["ok"]
    assert "double" in seen


# =========================================================================== #
#  (5) VALIDATE-BY-RUNNING gates the reply.
# =========================================================================== #
def test_validate_by_running_blocks_a_deliberately_broken_write(agent, monkeypatch):
    # the monkeypatch-guarded precedent (CODE-2's exec gate): sabotage the
    # function-grain renderer so the written source disagrees with the
    # agent's own model prediction -- the reply must refuse the hand-over.
    def broken(agent_, name, args, term, docstring=None):
        return "def %s(%s):\n    return 999\n" % (name, ", ".join(args))
    monkeypatch.setattr(cw, "write_function", broken)
    reply = agent.converse("Write a function that returns the larger of two numbers.")
    assert "def generated_function" not in reply
    assert "disagrees with my own prediction" in reply


def test_validate_by_running_passes_a_faithful_write(agent):
    reply = agent.converse("Write a function that returns the larger of two numbers.")
    assert "Here is the function" in reply


def test_validator_reports_exec_failure_honestly():
    out = cwg.validate_written_function_by_running(
        "def f(a):\n    return b\n", "f", ["a"], {"a": 1}, 1)
    assert out["ran"] is False and out["agree"] is False


# =========================================================================== #
#  (6) READ-CODEBOOK RESIDUAL — a minted shape files a naming gap, once.
# =========================================================================== #
def test_minted_construction_files_naming_gap_once(full_agent):
    a = full_agent
    src = "def either(a, b):\n    return a or b\n"
    r = cdr.read_function(a, src, "either")
    assert r.get("minted") is True
    a.comprehend()
    gaps = cwg.pending_naming_gaps(a)
    assert [g["content"] for g in gaps] == ["learned_code_boolop"]
    # re-reading the same shape re-files nothing (already-held mint + dedup).
    cdr.read_function(a, src, "either")
    a.comprehend()
    assert len(cwg.pending_naming_gaps(a)) == 1


# =========================================================================== #
#  (7) SOURCE AUDIT — sanctioned surfaces only.
# =========================================================================== #
def test_code_write_growth_source_audit():
    path = os.path.join(ROOT, "domains", "code_write_growth.py")
    tree = ast.parse(open(path).read())
    # (a) no Python rule engine, ever.
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [a.name for a in node.names]
            mod = getattr(node, "module", "") or ""
            assert "graph_rewrite" not in mod and \
                   all("graph_rewrite" not in n for n in names)
    # (b) exec appears ONLY inside the validator (the sanctioned isolated
    # run-check), never anywhere else in the module.
    exec_owners = set()
    for fn in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
        for node in ast.walk(fn):
            if isinstance(node, ast.Call) and \
                    isinstance(node.func, ast.Name) and node.func.id == "exec":
                exec_owners.add(fn.name)
    assert exec_owners == {"validate_written_function_by_running"}


def test_code3_gates_unaffected_by_growth_wiring(agent):
    # CODE-3's own contract on the unchanged starter vocabulary.
    result = cw.write_function_from_request(
        agent, "Write a function that returns the larger of two numbers.")
    assert result["ok"] and result["construction"] == "max_of_two"
    result2 = cw.write_function_from_request(
        agent, "Write a function that sorts a list of numbers.")
    assert result2["ok"] is False
