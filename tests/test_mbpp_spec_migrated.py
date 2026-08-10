"""tests/test_mbpp_spec_migrated.py — Arc 2 Q2 gates for `domains/mbpp_spec.py`
/ `seeds/mbpp_request_cues.json`.

Six gate classes (task brief, PROGRAM_SYNTHESIS_ARC2_PREREG.md §0/§4):
  1. Per-form parser units — every supported form (incl. the three new
     Q1/Q2-boundary forms: math_isclose tol, set_wrapper unordered, raw
     set literals) and every named-refused form.
  2. Protocol-split units — the three preregistered protocols, pinned
     examples, official flagged protocol_distinct.
  3. Equivalence-on-overlap vs Q0-A's `mbpp_zero_shot_baseline.
     classify_assert`, imported READ-ONLY, over the WHOLE 427-task
     vendored corpus.
  4. Signature-facts units.
  5. Cue-seed loads clean + a train-only provenance list-gate (mines the
     120 TRAIN prompts itself, independently of the seed's own claimed
     `train_count`/`provenance` fields — a reproducible check, not a
     trust of the seed's own bookkeeping) + this module's own
     contamination scan (the existing `tests/test_mbpp_contamination_
     migrated.py`'s SCAN_TARGETS list is owned by a sibling track and is
     not touched here; this seed is not on that list, so this file
     carries an equivalent scan against ITS OWN new artifact).
  6. Determinism.

Runtime: PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1
OZMA_SEED_PERSIST_DISABLED=1 pytest --confcutdir=. tests/test_mbpp_spec_migrated.py
"""
from __future__ import annotations

import ast
import json
import os
import re
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("OZMA_NO_LLM", "1")
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

from domains import mbpp_spec as ms  # noqa: E402
import mbpp_zero_shot_baseline as mzb  # noqa: E402 — Q0-A's frozen parser, read-only

FIXTURE_PATH = os.path.join(ROOT, "tests", "fixtures", "mbpp", "sanitized-mbpp.json")
SEED_PATH = os.path.join(ROOT, "seeds", "mbpp_request_cues.json")


@pytest.fixture(scope="module")
def all_tasks():
    with open(FIXTURE_PATH) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def test_tasks(all_tasks):
    return sorted([t for t in all_tasks if 11 <= t["task_id"] <= 510],
                  key=lambda t: t["task_id"])


@pytest.fixture(scope="module")
def train_tasks(all_tasks):
    return sorted([t for t in all_tasks if t["task_id"] >= 601],
                  key=lambda t: t["task_id"])


def _task(all_tasks, tid):
    return next(t for t in all_tasks if t["task_id"] == tid)


# --------------------------------------------------------------------------- #
#  1a. per-form parser units — SUPPORTED forms.
# --------------------------------------------------------------------------- #
def test_supports_bare_int_call_eq():
    r = ms.classify_assert("assert f(1, 2) == 3")
    assert r == {"ok": True, "func_name": "f", "args": [1, 2], "expected": 3}


def test_supports_call_on_right_side():
    r = ms.classify_assert("assert 3 == f(1, 2)")
    assert r["ok"] and r["func_name"] == "f" and r["args"] == [1, 2] and r["expected"] == 3


def test_supports_list_and_str_values():
    r = ms.classify_assert("assert f([1, 2, 3]) == 'ab'")
    assert r == {"ok": True, "func_name": "f", "args": [[1, 2, 3]], "expected": "ab"}


def test_supports_math_isclose_with_explicit_rel_tol(all_tasks):
    t = _task(all_tasks, 82)  # volume_sphere — real corpus math.isclose task
    r = ms.classify_assert(t["test_list"][0])
    assert r["ok"] is True
    assert r["func_name"] == "volume_sphere"
    assert r["args"] == [10]
    assert r["expected"] == 4188.790204786391
    assert r["tol"] == 0.001


def test_math_isclose_defaults_tol_when_rel_tol_absent():
    r = ms.classify_assert("assert math.isclose(f(1), 2.0)")
    assert r["ok"] is True
    assert r["tol"] == pytest.approx(1e-09)


def test_math_isclose_rejects_nonliteral_tol():
    r = ms.classify_assert("assert math.isclose(f(1), 2.0, rel_tol=g())")
    assert r == {"ok": False, "reason": "math_isclose_nonliteral_tol"}


def test_supports_set_wrapper_as_unordered_row(all_tasks):
    t = _task(all_tasks, 111)  # common_in_nested_lists — real corpus set-wrapper task
    r = ms.classify_assert(t["test_list"][2])  # "...==set([4])"
    assert r["ok"] is True
    assert r["func_name"] == "common_in_nested_lists"
    assert r["expected"] == frozenset({4})
    assert r["unordered"] is True


def test_set_wrapper_peels_list_literal_rhs():
    r = ms.classify_assert("assert set(f(1)) == set([3, 1, 2])")
    assert r["ok"] is True
    assert r["expected"] == frozenset({1, 2, 3})
    assert r["unordered"] is True
    # order-insensitive: a differently-ordered literal is the SAME row.
    r2 = ms.classify_assert("assert set(f(1)) == set([1, 2, 3])")
    assert r2["expected"] == r["expected"]


def test_supports_raw_set_literal_as_top_level_expected(all_tasks):
    t = _task(all_tasks, 473)  # tuple_intersection — raw {..} literal AS expected
    r = ms.classify_assert(t["test_list"][0])
    assert r["ok"] is True
    assert r["expected"] == {(4, 5), (3, 4), (5, 6)}
    assert isinstance(r["expected"], (set, frozenset))
    assert r["unordered"] is True, "top-level set expected must flag unordered"


def test_supports_raw_set_literal_nested_in_arg_without_unordered_flag(all_tasks):
    t = _task(all_tasks, 115)  # empty_dit([{1,2},{},{}]) == False
    r = ms.classify_assert(t["test_list"][1])
    assert r["ok"] is True
    assert r["func_name"] == "empty_dit"
    assert r["args"] == [[{1, 2}, {}, {}]]
    assert r["expected"] is False
    assert "unordered" not in r, "a set NESTED in an arg is data, not a comparator flag"


def test_supports_top_level_set_arg(all_tasks):
    t = _task(all_tasks, 582)  # my_dict({10}) == False
    r = ms.classify_assert(t["test_list"][0])
    assert r["ok"] is True
    assert r["args"] == [{10}]
    assert r["expected"] is False
    assert "unordered" not in r


# --------------------------------------------------------------------------- #
#  1b. per-form parser units — NAMED-REFUSED forms (honest exclusions).
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("stmt,reason", [
    ("assert f(x", "syntax_error"),
    ("x = 1", "not_single_assert_stmt"),
    ("assert f(1)", "boolean_expression:bare_call"),
    ("assert f(1) and g(2)", "boolean_expression:boolop"),
    ("assert not f(1)", "boolean_expression:unaryop"),
    ("assert f(1) < 2", "non_eq_compare:Lt"),
    ("assert f(1) == 2 == g(3)", "chained_compare"),
    ("assert f(1, k=2) == 3", "call_has_kwargs"),
    ("assert f(*a) == 3", "starred_args"),
    ("assert f(g(1)) == 3", "non_literal_args"),
    ("assert f(1) == x", "non_literal_expected"),
    ("assert obj.method(1) == 3", "attribute_call"),
    ("assert f(1) == g(1)", "multi_call"),
    ("assert sorted(f(1)) == sorted([1, 2])", "sorted_wrapper"),
    ("assert list(f(1)) == list([1, 2])", "list_wrapper"),
    ("assert tuple(f(1)) == tuple((1, 2))", "tuple_wrapper"),
])
def test_refuses_named_unsupported_forms(stmt, reason):
    r = ms.classify_assert(stmt)
    assert r == {"ok": False, "reason": reason}


def test_refuses_sys_getsizeof_multi_call(all_tasks):
    t = _task(all_tasks, 596)
    r = ms.classify_assert(t["test_list"][0])
    assert r == {"ok": False, "reason": "multi_call"}


# --------------------------------------------------------------------------- #
#  1c. parse_asserts — row assembly, order, and the tol/unordered fields.
# --------------------------------------------------------------------------- #
def test_parse_asserts_row_schema_and_order(all_tasks):
    t = _task(all_tasks, 82)
    parsed = ms.parse_asserts(t)
    assert len(parsed["rows"]) == 3
    assert parsed["unparseable"] == []
    for row in parsed["rows"]:
        assert set(row.keys()) == {"inputs", "expected", "tol"}
        assert list(row["inputs"].keys()) == ["a"]


def test_parse_asserts_reports_unparseable_form_and_text():
    t = {"test_list": ["assert f(1) == x", "assert f(1, 2) == 3"]}
    parsed = ms.parse_asserts(t)
    assert parsed["unparseable"] == [
        {"form": "non_literal_expected", "assert_text": "assert f(1) == x"}]
    assert len(parsed["rows"]) == 1


def test_parse_asserts_never_reads_code_field():
    """A task dict lacking `code` entirely must parse identically to one
    that has it — parse_asserts touches only `test_list`."""
    t = {"test_list": ["assert f(1, 2) == 3"], "code": "def f(a, b): return a + b"}
    t_stripped = {"test_list": ["assert f(1, 2) == 3"]}
    assert ms.parse_asserts(t) == ms.parse_asserts(t_stripped)


# --------------------------------------------------------------------------- #
#  2. protocol-split units.
# --------------------------------------------------------------------------- #
_ROWS3 = [{"inputs": {"a": 1}, "expected": 1},
          {"inputs": {"a": 2}, "expected": 2},
          {"inputs": {"a": 3}, "expected": 3}]


def test_primary_reveals_all_but_last():
    s = ms.split_rows(_ROWS3, "primary")
    assert s["runnable"] is True
    assert s["revealed"] == _ROWS3[:2]
    assert s["held_out"] == _ROWS3[2:]
    assert "protocol_distinct" not in s


def test_official_reveals_everything_and_flags_protocol_distinct():
    s = ms.split_rows(_ROWS3, "official")
    assert s["runnable"] is True
    assert s["revealed"] == _ROWS3
    assert s["held_out"] == _ROWS3
    assert s["protocol_distinct"] is True


def test_stress_reveals_only_the_first():
    s = ms.split_rows(_ROWS3, "stress")
    assert s["runnable"] is True
    assert s["revealed"] == _ROWS3[:1]
    assert s["held_out"] == _ROWS3[1:]


@pytest.mark.parametrize("protocol", ["primary", "stress"])
def test_primary_and_stress_exclude_single_row_as_insufficient_holdout(protocol):
    s = ms.split_rows(_ROWS3[:1], protocol)
    assert s["runnable"] is False
    assert s["excluded_reason"] == "insufficient_holdout"


@pytest.mark.parametrize("protocol", ["primary", "official", "stress"])
def test_zero_rows_excluded_as_no_parseable_rows(protocol):
    s = ms.split_rows([], protocol)
    assert s["runnable"] is False
    assert s["excluded_reason"] == "no_parseable_rows"


def test_official_runnable_with_a_single_row():
    s = ms.split_rows(_ROWS3[:1], "official")
    assert s["runnable"] is True
    assert s["revealed"] == s["held_out"] == _ROWS3[:1]


def test_unknown_protocol_raises():
    with pytest.raises(ValueError):
        ms.split_rows(_ROWS3, "bogus")


def test_primary_runnable_requires_at_least_two_rows_matches_q0a_stress_rule(all_tasks):
    """PRIMARY and STRESS share the same >=2-row runnability threshold as
    Q0-A's original (now-STRESS) rule — verified on a real single-parseable-
    assert-shaped case is not present in the vendored fixture, so this is a
    synthetic boundary check, not a corpus claim."""
    one_row = _ROWS3[:1]
    assert ms.split_rows(one_row, "primary")["runnable"] is False
    assert ms.split_rows(one_row, "stress")["runnable"] is False
    two_rows = _ROWS3[:2]
    assert ms.split_rows(two_rows, "primary")["runnable"] is True
    assert ms.split_rows(two_rows, "stress")["runnable"] is True


# --------------------------------------------------------------------------- #
#  3. equivalence-on-overlap vs Q0-A's classify_assert (whole 427-corpus).
# --------------------------------------------------------------------------- #
def test_equivalence_on_overlap_with_q0a_parser_whole_corpus(all_tasks):
    """For every assert BOTH parsers accept, the extracted row (func_name,
    args, expected) must be byte-identical — this module is a strict
    SUPERSET, never a divergent reinterpretation, of Q0-A's frozen
    baseline parser."""
    n_both_ok = 0
    n_baseline_ok_mine_rejects = 0
    n_mine_new_forms = 0
    for t in all_tasks:
        for stmt in t["test_list"]:
            b = mzb.classify_assert(stmt)
            m = ms.classify_assert(stmt)
            if b["ok"]:
                if not m["ok"]:
                    n_baseline_ok_mine_rejects += 1
                    continue
                n_both_ok += 1
                assert m["func_name"] == b["func_name"], (t["task_id"], stmt)
                assert m["args"] == b["args"], (t["task_id"], stmt)
                assert m["expected"] == b["expected"], (t["task_id"], stmt)
            elif m["ok"]:
                n_mine_new_forms += 1
    # a superset must never reject something the baseline accepted.
    assert n_baseline_ok_mine_rejects == 0
    # sanity: both actually overlap substantially, and this module DOES add
    # new coverage (math_isclose 39 + set_wrapper 15 + raw-set 6 = 60,
    # measured on the full 427-task vendored corpus).
    assert n_both_ok > 1200
    assert n_mine_new_forms == 60


def test_residual_unparseable_taxonomy_is_the_named_three_classes(all_tasks):
    """Everything this module still refuses, corpus-wide, is one of the
    three classes already present zero-shot in the corpus (§2 of
    PROGRAM_SYNTHESIS_ARC2_Q0_BASELINE.md's own taxonomy, scoped down to
    what remains after this module's three extensions) — a residual
    named honestly, not silently absorbed."""
    reasons = set()
    n = 0
    for t in all_tasks:
        for stmt in t["test_list"]:
            r = ms.classify_assert(stmt)
            if not r["ok"]:
                reasons.add(r["reason"])
                n += 1
    assert reasons == {"boolean_expression:bare_call", "boolean_expression:unaryop",
                       "multi_call"}
    assert n == 25


def test_all_257_test_tasks_are_primary_runnable(test_tasks):
    """THE headline PRIMARY-protocol finding this phase lands: every
    TEST-split task now has >=2 parseable rows (0/257 assert_unparseable,
    0/257 insufficient_holdout under PRIMARY) — the three new forms land
    exactly where Q0-A's own 17-task assert_unparseable mass lived. This
    is a PARSEABILITY claim, not a synthesizability one (see
    PROGRAM_SYNTHESIS_ARC2_Q2_NOTES.md's honest residual on task 124's
    complex-number value domain)."""
    n_runnable = 0
    unparseable_ids = []
    for t in test_tasks:
        rows = ms.parse_asserts(t)["rows"]
        split = ms.split_rows(rows, "primary")
        if split["runnable"]:
            n_runnable += 1
        else:
            unparseable_ids.append(t["task_id"])
    assert unparseable_ids == []
    assert n_runnable == len(test_tasks) == 257


# --------------------------------------------------------------------------- #
#  4. signature-facts units.
# --------------------------------------------------------------------------- #
def test_signature_facts_from_two_arg_task(all_tasks):
    t = _task(all_tasks, 2)  # similar_elements(tuple, tuple)
    sf = ms.signature_facts(t)
    assert sf["func_name"] == "similar_elements"
    assert sf["arg_count"] == 2
    assert sf["arg_types"] == ["tuple", "tuple"]
    assert sf["consistent_arity"] is True
    assert sf["complete"] is True


def test_signature_facts_never_reads_code_field(all_tasks):
    t = dict(_task(all_tasks, 2))
    t_stripped = {k: v for k, v in t.items() if k != "code"}
    assert ms.signature_facts(t) == ms.signature_facts(t_stripped)


def test_signature_facts_func_name_from_math_isclose_first_assert(all_tasks):
    t = _task(all_tasks, 82)
    sf = ms.signature_facts(t)
    assert sf["func_name"] == "volume_sphere"
    assert sf["arg_count"] == 1
    assert sf["arg_types"] == ["int"]
    assert sf["return_type"] == "float"


def test_signature_facts_func_name_from_set_wrapper_first_assert(all_tasks):
    t = _task(all_tasks, 111)
    sf = ms.signature_facts(t)
    assert sf["func_name"] == "common_in_nested_lists"
    assert sf["arg_count"] == 1


def test_signature_facts_honest_when_zero_parseable_rows():
    t = {"test_list": ["assert f(1) == g(2)"]}
    sf = ms.signature_facts(t)
    assert sf["complete"] is False
    assert sf["arg_count"] is None
    assert sf["n_rows_used"] == 0
    assert sf["func_name"] == "f"  # mechanical scan still finds it (unparseable != nameless)


def test_signature_facts_flags_inconsistent_arity():
    t = {"test_list": ["assert f(1) == 1", "assert f(1, 2) == 3"]}
    sf = ms.signature_facts(t)
    assert sf["consistent_arity"] is False
    assert sf["complete"] is False


def test_signature_facts_arg_count_matches_reference_function_sample(all_tasks):
    """Measurement-only spot check (contamination-sanctioned: reads
    `code` to verify, never to seed anything) on 10 real TEST-split tasks
    spanning arities 1-3 — the fuller sweep (all 257) is in
    PROGRAM_SYNTHESIS_ARC2_Q2_NOTES.md, not re-run per-test to keep this
    suite's runtime small."""
    sample_ids = [11, 12, 14, 16, 17, 18, 19, 20, 56, 57]
    for tid in sample_ids:
        t = _task(all_tasks, tid)
        sf = ms.signature_facts(t)
        tree = ast.parse(t["code"])
        true_count = next(len(n.args.args) for n in ast.walk(tree)
                          if isinstance(n, ast.FunctionDef) and n.name == sf["func_name"])
        assert sf["arg_count"] == true_count, (tid, sf, true_count)


# --------------------------------------------------------------------------- #
#  5a. request_facts — closed-fallback behaviour (no agent).
# --------------------------------------------------------------------------- #
def test_request_facts_recognizes_python_function_frame():
    rf = ms.request_facts("Write a python function to check if a number is prime.")
    assert rf["verb_frame"] == "write_a_python_function_to"
    assert rf["request_body"] == "check if a number is prime."
    assert rf["constraint_hits"] == ["prime"]


def test_request_facts_recognizes_plain_function_frame():
    rf = ms.request_facts("Write a function to sort a given tuple.")
    assert rf["verb_frame"] == "write_a_function_to"
    assert "tuple" in rf["constraint_hits"]


def test_request_facts_other_when_no_frame_matches():
    rf = ms.request_facts("This is not an imperative write request at all.")
    assert rf["verb_frame"] == "other"
    assert rf["request_body"] == "This is not an imperative write request at all."


def test_request_facts_multiple_constraint_hits_sorted():
    rf = ms.request_facts("Write a function to find the sum of the even and odd numbers.")
    assert rf["constraint_hits"] == sorted(rf["constraint_hits"])
    assert set(rf["constraint_hits"]) >= {"even", "odd", "sum"}


def test_request_facts_all_test_prompts_are_mechanical_no_crash(test_tasks):
    """Never raises on any real TEST-split prompt — a pure translation
    function must not throw on well-formed benchmark prose."""
    for t in test_tasks:
        rf = ms.request_facts(t["prompt"])
        assert isinstance(rf["verb_frame"], str)
        assert isinstance(rf["request_body"], str)
        assert isinstance(rf["constraint_hits"], list)


# --------------------------------------------------------------------------- #
#  5b. cue seed — loads clean, node counts, and its own contamination scan.
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def seed_manifest():
    with open(SEED_PATH) as f:
        return json.load(f)


def test_seed_manifest_shape(seed_manifest):
    assert seed_manifest["id"] == "mbpp_request_cues"
    assert seed_manifest["depends_on"] == ["code_write_request_cues"]
    frames = [n for n in seed_manifest["nodes"]
             if n["attrs"]["code_request_role"] == "mbpp_verb_frame"]
    words = [n for n in seed_manifest["nodes"]
            if n["attrs"]["code_request_role"] == "mbpp_constraint_word"]
    assert len(frames) == 6
    assert len(words) == 44
    assert len(seed_manifest["nodes"]) == 50
    assert seed_manifest["edges"] == []
    assert seed_manifest["productions"] == []
    for n in seed_manifest["nodes"]:
        assert n["type"] == "Concept"
        assert isinstance(n["attrs"]["train_count"], int) and n["attrs"]["train_count"] >= 1
        assert n["attrs"]["provenance"]


def test_seed_loads_clean_via_load_seed_manifest():
    import substrate_rs as srs
    from substrate.seed_loader import manifest_for

    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    s._inner.load_seed_manifest(manifest_for("code_write_request_cues"), ag)
    summary = s._inner.load_seed_manifest(manifest_for("mbpp_request_cues"), ag)
    assert summary["rules_skipped"] == []
    assert summary["reflexes_skipped"] == []
    assert summary["nodes"] == 50
    concepts = [s.node(n)["attrs"] for n in s.nodes("Concept")]
    assert sum(1 for c in concepts if c.get("code_request_role") == "mbpp_verb_frame") == 6
    assert sum(1 for c in concepts if c.get("code_request_role") == "mbpp_constraint_word") == 44


class _FakeAgent:
    def __init__(self, sub):
        self.s = sub


@pytest.fixture(scope="module")
def booted_agent():
    import substrate_rs as srs
    from substrate.seed_loader import manifest_for

    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    s._inner.load_seed_manifest(manifest_for("code_write_request_cues"), ag)
    s._inner.load_seed_manifest(manifest_for("mbpp_request_cues"), ag)
    return _FakeAgent(s)


def test_request_facts_with_held_seed_matches_closed_fallback(booted_agent, test_tasks):
    """PARITY (the code_write_request_cues precedent): the held-Concept
    path and the closed-fallback path must classify identically — this
    seed's initial vocabulary IS the fallback, verbatim."""
    for t in test_tasks[:40]:
        assert ms.request_facts(t["prompt"], agent=booted_agent) == \
            ms.request_facts(t["prompt"], agent=None)


def test_module_fallback_sets_match_seed_exactly(seed_manifest):
    seed_frames = sorted(n["attrs"]["name"] for n in seed_manifest["nodes"]
                         if n["attrs"]["code_request_role"] == "mbpp_verb_frame")
    seed_words = sorted(n["attrs"]["name"] for n in seed_manifest["nodes"]
                        if n["attrs"]["code_request_role"] == "mbpp_constraint_word")
    assert sorted(ms._MBPP_VERB_FRAMES_FALLBACK) == seed_frames
    assert sorted(ms._MBPP_CONSTRAINT_WORDS_FALLBACK) == seed_words


def test_train_only_provenance_list_gate(seed_manifest, train_tasks):
    """The binding contamination requirement: every cue Concept's `name`
    must be independently verifiable as occurring in a TRAIN-split
    prompt (task_id >= 601) — mined HERE, fresh, not trusted from the
    seed's own `train_count`/`provenance` bookkeeping. A word or phrase
    that does not actually occur in any train prompt fails this gate."""
    train_prompts_lower = [t["prompt"].lower() for t in train_tasks]

    for n in seed_manifest["nodes"]:
        at = n["attrs"]
        name = at["name"]
        role = at["code_request_role"]
        if role == "mbpp_verb_frame":
            hits = sum(1 for p in train_prompts_lower if p.startswith(name))
        elif role == "mbpp_constraint_word":
            hits = sum(1 for p in train_prompts_lower
                      if name in set(re.findall(r"[a-z']+", p)))
        else:
            pytest.fail("unexpected code_request_role %r" % role)
        assert hits >= 1, "cue %r has ZERO train occurrences — not earned" % name
        assert hits == at["train_count"], (
            "seed's claimed train_count for %r (%d) does not match a fresh "
            "mining pass (%d)" % (name, at["train_count"], hits))


def test_generic_vocab_words_absent_from_train_are_correctly_excluded(train_tasks):
    """The 12 words from the existing generic 55-word constraint vocabulary
    (scripts/mbpp_blocker_histogram.CONSTRAINT_VOCAB — itself mined from
    the FULL 427-task corpus, test included, so NOT itself a valid
    contamination-safe source) that have ZERO train occurrences must be
    ABSENT from this seed."""
    import mbpp_blocker_histogram as mbh
    train_prompts_lower = [t["prompt"].lower() for t in train_tasks]
    zero_train = set()
    for w in mbh.CONSTRAINT_VOCAB:
        hits = sum(1 for p in train_prompts_lower
                  if w in set(re.findall(r"[a-z']+", p)))
        if hits == 0:
            zero_train.add(w)
    assert zero_train == {"armstrong", "camel", "duplicate", "factorial",
                          "frequency", "kth", "negative", "palindrome",
                          "positive", "snake", "substring", "unique"}
    assert zero_train.isdisjoint(ms._MBPP_CONSTRAINT_WORDS_FALLBACK)


_WS_RE = re.compile(r"\s+")
_MIN_PROMPT_LEN = 20
_MIN_CODE_LINE_LEN = 15


def _normalize(s: str) -> str:
    return _WS_RE.sub(" ", s.strip().lower())


def test_mbpp_request_cues_seed_has_no_test_split_contamination(all_tasks):
    """This module's own equivalent of tests/test_mbpp_contamination_
    migrated.py's scan (that file's SCAN_TARGETS list is a sibling
    track's and is not touched here — this seed is not on it). Same
    normalization, same forbidden-substring construction, applied
    directly to `seeds/mbpp_request_cues.json`."""
    test_split = [t for t in all_tasks if 11 <= t["task_id"] <= 510]
    forbidden = []
    for t in test_split:
        p = _normalize(t["prompt"])
        if len(p) >= _MIN_PROMPT_LEN:
            forbidden.append(p)
        for line in t["code"].splitlines():
            nl = _normalize(line)
            if len(nl) >= _MIN_CODE_LINE_LEN:
                forbidden.append(nl)
    assert len(forbidden) > 200

    with open(SEED_PATH, "r", errors="replace") as f:
        raw = f.read()
    norm = _normalize(raw)
    hits = [sub for sub in forbidden if sub in norm]
    assert hits == [], "test-split contamination found in mbpp_request_cues.json: %r" % hits[:5]


# --------------------------------------------------------------------------- #
#  6. determinism.
# --------------------------------------------------------------------------- #
def test_parse_asserts_is_deterministic(test_tasks):
    for t in test_tasks[:30]:
        assert ms.parse_asserts(t) == ms.parse_asserts(t)


def test_signature_facts_is_deterministic(test_tasks):
    for t in test_tasks[:30]:
        assert ms.signature_facts(t) == ms.signature_facts(t)


def test_request_facts_is_deterministic_with_held_seed(booted_agent, test_tasks):
    for t in test_tasks[:30]:
        assert ms.request_facts(t["prompt"], agent=booted_agent) == \
            ms.request_facts(t["prompt"], agent=booted_agent)
