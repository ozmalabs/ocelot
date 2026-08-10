"""StructuredDataWorld generalisation test.

Builds a 100+ entry training bank across JSON/YAML/TOML/XML/CSV/INI with
varied corruptions; runs it through the world (which calls the teacher
when it sees a NEW (format, corruption) shape and otherwise re-uses the
grounded ParsingStrategy). Then runs a 30+ entry held-out bank with the
teacher DISABLED — the substrate must succeed on its grounded strategies
alone or fail honestly.

Reports:
  * teacher_call rate over training (binned per 10) — should drop toward 0
  * held-out accuracy overall + by category (same-shape, novel-corruption,
    ambiguous)
  * grounded node counts (FormatID / CorruptionPattern / ParsingStrategy)
  * a list of held-out shapes the substrate had no grounded strategy for
  * example failures

Per gamma-substrate/CLAUDE.md this is a world-adapter / harness script —
no agent reasoning lives here. The substrate's strategy table (in the
graph) IS the learned knowledge; we just measure it.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))

from substrate_rs import _native
from domains.structured_data_world import (
    StructuredDataWorld,
    teacher_stub,
    _detect_format,
    _detect_corruption,
    _values_equal,
)


# ---------------------------------------------------------------------------
# Banks
# ---------------------------------------------------------------------------


def _t(text: str, expected: Any, category: str = "training",
       shape: str | None = None) -> dict:
    return {"text": text, "expected": expected, "category": category,
            "shape": shape}


def training_bank() -> list[dict]:
    """100+ training entries with varied content + corruption distribution
    described in the spec."""
    bank: list[dict] = []

    # --- 25 clean (~5 per format) ----------------------------------------

    # JSON (5)
    bank += [
        _t('{"x": 1}', {"x": 1}, shape="clean_json"),
        _t('{"name": "alice", "age": 30}',
           {"name": "alice", "age": 30}, shape="clean_json"),
        _t('[1, 2, 3, 4]', [1, 2, 3, 4], shape="clean_json"),
        _t('{"users": [{"id": 1}, {"id": 2}]}',
           {"users": [{"id": 1}, {"id": 2}]}, shape="clean_json"),
        _t('{"nested": {"deep": {"k": 7}}}',
           {"nested": {"deep": {"k": 7}}}, shape="clean_json"),
    ]

    # YAML (5)
    bank += [
        _t("k: 1\n", {"k": 1}, shape="clean_yaml"),
        _t("name: bob\nage: 25\n",
           {"name": "bob", "age": 25}, shape="clean_yaml"),
        _t("colours:\n  - red\n  - blue\n",
           {"colours": ["red", "blue"]}, shape="clean_yaml"),
        _t("server:\n  host: localhost\n  port: 8080\n",
           {"server": {"host": "localhost", "port": 8080}},
           shape="clean_yaml"),
        _t("items:\n  - id: 1\n    name: a\n  - id: 2\n    name: b\n",
           {"items": [{"id": 1, "name": "a"}, {"id": 2, "name": "b"}]},
           shape="clean_yaml"),
    ]

    # TOML (5)
    bank += [
        _t("k = 1\n", {"k": 1}, shape="clean_toml"),
        _t('name = "carol"\nage = 28\n',
           {"name": "carol", "age": 28}, shape="clean_toml"),
        _t("nums = [10, 20, 30]\n",
           {"nums": [10, 20, 30]}, shape="clean_toml"),
        _t('[server]\nhost = "localhost"\nport = 9000\n',
           {"server": {"host": "localhost", "port": 9000}},
           shape="clean_toml"),
        _t('title = "doc"\n[meta]\nversion = "1.0"\n',
           {"title": "doc", "meta": {"version": "1.0"}},
           shape="clean_toml"),
    ]

    # XML (5)
    bank += [
        _t("<r><a>1</a></r>", {"a": 1}, shape="clean_xml"),
        _t("<person><name>dan</name><age>40</age></person>",
           {"name": "dan", "age": 40}, shape="clean_xml"),
        _t("<nums><n>1</n><n>2</n><n>3</n></nums>",
           [1, 2, 3], shape="clean_xml"),
        _t("<cfg><host>a</host><port>80</port></cfg>",
           {"host": "a", "port": 80}, shape="clean_xml"),
        _t("<lst><item><k>1</k></item><item><k>2</k></item></lst>",
           [{"k": 1}, {"k": 2}], shape="clean_xml"),
    ]

    # CSV (5) — heuristics will currently classify CSV as 'unknown' /
    # something else; this set probes whether the world adapter even sees
    # CSV as a known format. (Honesty: we expect a generalisation ceiling
    # to surface here.)
    bank += [
        _t("a,b\n1,2\n", [["a", "b"], ["1", "2"]], shape="clean_csv"),
        _t("name,age\nalice,30\nbob,25\n",
           [["name", "age"], ["alice", "30"], ["bob", "25"]],
           shape="clean_csv"),
        _t("x,y,z\n1,2,3\n4,5,6\n",
           [["x", "y", "z"], ["1", "2", "3"], ["4", "5", "6"]],
           shape="clean_csv"),
        _t("id\n1\n2\n3\n",
           [["id"], ["1"], ["2"], ["3"]], shape="clean_csv"),
        _t("k,v\nfoo,bar\n",
           [["k", "v"], ["foo", "bar"]], shape="clean_csv"),
    ]

    # INI (5) — same story as CSV; the heuristics currently fold INI
    # into TOML or YAML.
    bank += [
        _t("[s]\nk = 1\n", {"s": {"k": "1"}}, shape="clean_ini"),
        _t("[server]\nhost = localhost\nport = 80\n",
           {"server": {"host": "localhost", "port": "80"}},
           shape="clean_ini"),
        _t("[app]\nname = demo\n[debug]\nlevel = info\n",
           {"app": {"name": "demo"}, "debug": {"level": "info"}},
           shape="clean_ini"),
        _t("[a]\nk1 = v1\nk2 = v2\n",
           {"a": {"k1": "v1", "k2": "v2"}}, shape="clean_ini"),
        _t("[main]\nthreads = 4\n",
           {"main": {"threads": "4"}}, shape="clean_ini"),
    ]

    # --- 20 trailing-comma JSON / YAML ----------------------------------

    bank += [
        _t('{"a": 1, "b": 2,}', {"a": 1, "b": 2}, shape="json_trailing"),
        _t('[1, 2, 3,]', [1, 2, 3], shape="json_trailing"),
        _t('{"x": 5,}', {"x": 5}, shape="json_trailing"),
        _t('{"a": 1, "b": [2, 3,],}',
           {"a": 1, "b": [2, 3]}, shape="json_trailing"),
        _t('{"k": "v",}', {"k": "v"}, shape="json_trailing"),
        _t('[true, false, null,]',
           [True, False, None], shape="json_trailing"),
        _t('{"nums": [1, 2,], "ok": true,}',
           {"nums": [1, 2], "ok": True}, shape="json_trailing"),
        _t('{"a": 1,}', {"a": 1}, shape="json_trailing"),
        _t('[[1, 2,], [3, 4,],]',
           [[1, 2], [3, 4]], shape="json_trailing"),
        _t('{"users": [{"id": 1,}, {"id": 2,},],}',
           {"users": [{"id": 1}, {"id": 2}]}, shape="json_trailing"),
        _t('{"a": "b",}', {"a": "b"}, shape="json_trailing"),
        _t('[10,]', [10], shape="json_trailing"),
        _t('{"only": 1,}', {"only": 1}, shape="json_trailing"),
        _t('{"q": [1, 2, 3,]}', {"q": [1, 2, 3]}, shape="json_trailing"),
        _t('{"d": {"e": 1,},}', {"d": {"e": 1}}, shape="json_trailing"),
        # YAML flow-style trailing comma (treated similarly):
        _t('{a: 1, b: 2,}', {"a": 1, "b": 2}, shape="json_trailing"),
        _t('[1, 2, 3, 4,]', [1, 2, 3, 4], shape="json_trailing"),
        _t('{"k1": 1, "k2": 2, "k3": 3,}',
           {"k1": 1, "k2": 2, "k3": 3}, shape="json_trailing"),
        _t('{"arr": [1,], "v": 2,}',
           {"arr": [1], "v": 2}, shape="json_trailing"),
        _t('{"pair": ["a", "b",],}',
           {"pair": ["a", "b"]}, shape="json_trailing"),
    ]

    # --- 15 unquoted keys (JSON-style) ----------------------------------

    bank += [
        _t('{a: 1}', {"a": 1}, shape="json_unquoted"),
        _t('{name: "alice"}', {"name": "alice"}, shape="json_unquoted"),
        _t('{x: 1, y: 2}', {"x": 1, "y": 2}, shape="json_unquoted"),
        _t('{a: 1, b: 2, c: 3}',
           {"a": 1, "b": 2, "c": 3}, shape="json_unquoted"),
        _t('{nums: [1, 2, 3]}', {"nums": [1, 2, 3]},
           shape="json_unquoted"),
        _t('{server: {host: "a", port: 80}}',
           {"server": {"host": "a", "port": 80}}, shape="json_unquoted"),
        _t('{ok: true}', {"ok": True}, shape="json_unquoted"),
        _t('{empty: null}', {"empty": None}, shape="json_unquoted"),
        _t('{count: 42}', {"count": 42}, shape="json_unquoted"),
        _t('{a: 1, b: "two"}',
           {"a": 1, "b": "two"}, shape="json_unquoted"),
        _t('{user: {id: 1}}', {"user": {"id": 1}}, shape="json_unquoted"),
        _t('{ts: 1700000000}', {"ts": 1700000000},
           shape="json_unquoted"),
        _t('{k: [1, 2]}', {"k": [1, 2]}, shape="json_unquoted"),
        _t('{outer: {inner: 9}}',
           {"outer": {"inner": 9}}, shape="json_unquoted"),
        _t('{a: 1.5}', {"a": 1.5}, shape="json_unquoted"),
    ]

    # --- 15 missing closer ----------------------------------------------

    bank += [
        _t('{"a": 1', {"a": 1}, shape="json_missing"),
        _t('{"a": {"b": 1}', {"a": {"b": 1}}, shape="json_missing"),
        _t('[1, 2, 3', [1, 2, 3], shape="json_missing"),
        _t('{"x": [1, 2', {"x": [1, 2]}, shape="json_missing"),
        _t('{"a": 1, "b": 2',
           {"a": 1, "b": 2}, shape="json_missing"),
        _t('{"k": "v"', {"k": "v"}, shape="json_missing"),
        _t('[[1, 2], [3, 4',
           [[1, 2], [3, 4]], shape="json_missing"),
        _t('{"users": [{"id": 1}, {"id": 2}',
           {"users": [{"id": 1}, {"id": 2}]}, shape="json_missing"),
        _t('{"nested": {"a": {"b": 5}', {"nested": {"a": {"b": 5}}},
           shape="json_missing"),
        _t('[true, false', [True, False], shape="json_missing"),
        _t('{"q": [1, 2, 3', {"q": [1, 2, 3]},
           shape="json_missing"),
        _t('{"obj": {"x": 1}, "n": 5',
           {"obj": {"x": 1}, "n": 5}, shape="json_missing"),
        _t('{"a": "b", "c": "d"',
           {"a": "b", "c": "d"}, shape="json_missing"),
        _t('{"deep": [[1', {"deep": [[1]]}, shape="json_missing"),
        _t('{"a": 1, "b": [2, 3]',
           {"a": 1, "b": [2, 3]}, shape="json_missing"),
    ]

    # --- 10 mixed corruptions -------------------------------------------
    # Two corruptions in one input. Honest: the world adapter's detector
    # picks ONE corruption class per text, so these probe how teacher
    # generalises — sometimes the first repair fixes both, sometimes not.

    bank += [
        # trailing comma + unquoted key
        _t('{a: 1, b: 2,}', {"a": 1, "b": 2}, shape="mixed_corr"),
        _t('{x: 5,}', {"x": 5}, shape="mixed_corr"),
        _t('{name: "z", age: 1,}',
           {"name": "z", "age": 1}, shape="mixed_corr"),
        # unquoted key + missing brace
        _t('{a: 1, b: 2', {"a": 1, "b": 2}, shape="mixed_corr"),
        _t('{k: "v"', {"k": "v"}, shape="mixed_corr"),
        # trailing comma + missing brace
        _t('{"a": 1, "b": 2,', {"a": 1, "b": 2}, shape="mixed_corr"),
        _t('[1, 2, 3,', [1, 2, 3], shape="mixed_corr"),
        # all three
        _t('{a: 1,', {"a": 1}, shape="mixed_corr"),
        _t('{a: 1, b: [2, 3,', {"a": 1, "b": [2, 3]},
           shape="mixed_corr"),
        _t('{x: [1, 2,', {"x": [1, 2]}, shape="mixed_corr"),
    ]

    # --- 10 misnested ---------------------------------------------------
    # XML mismatched tags + JSON bracket/brace mismatch.

    bank += [
        _t("<a>1</b>", None, shape="misnested"),
        _t("<root><a>1</b></root>", None, shape="misnested"),
        _t("<x><y>2</z></x>", None, shape="misnested"),
        _t("<a><b>1</a></b>", None, shape="misnested"),
        _t("<r><a>1</a><b>2</c></r>", None, shape="misnested"),
        _t('{"a": [1, 2}', None, shape="misnested"),
        _t('[1, 2}', None, shape="misnested"),
        _t('{"a": 1]', None, shape="misnested"),
        _t("<x>1</X>", None, shape="misnested"),
        _t("<a><b/></c>", None, shape="misnested"),
    ]

    # --- 5 empty/whitespace ---------------------------------------------

    bank += [
        _t("", None, shape="empty"),
        _t("   ", None, shape="empty"),
        _t("\n\n", None, shape="empty"),
        _t("\t", None, shape="empty"),
        _t("  \n  \t\n", None, shape="empty"),
    ]

    return bank


def heldout_bank() -> list[dict]:
    """30+ held-out entries probing generalisation:
       * same-shape: same (fmt, corruption) as training, novel content
       * novel-corruption: new sub-types
       * ambiguous: could be parsed multiple ways
    """
    bank: list[dict] = []

    # --- same-shape (substrate has grounded strategy; new content) ------
    # 12 entries

    bank += [
        _t('{"new_key": 99}', {"new_key": 99},
           category="same_shape", shape="clean_json"),
        _t('[100, 200, 300]', [100, 200, 300],
           category="same_shape", shape="clean_json"),
        _t("flag: yes\ncount: 7\n", {"flag": True, "count": 7},
           category="same_shape", shape="clean_yaml"),
        _t('greeting = "hello"\n', {"greeting": "hello"},
           category="same_shape", shape="clean_toml"),
        _t("<doc><title>x</title></doc>", {"title": "x"},
           category="same_shape", shape="clean_xml"),
        _t('{"a": 99, "b": "novel",}', {"a": 99, "b": "novel"},
           category="same_shape", shape="json_trailing"),
        _t('{novel_key: "novel_val"}', {"novel_key": "novel_val"},
           category="same_shape", shape="json_unquoted"),
        _t('{"completely": "different"',
           {"completely": "different"},
           category="same_shape", shape="json_missing"),
        _t("<a>5</b>", None,
           category="same_shape", shape="misnested"),
        _t("", None, category="same_shape", shape="empty"),
        _t('{"deep": {"deeper": [1, 2, 3]}}',
           {"deep": {"deeper": [1, 2, 3]}},
           category="same_shape", shape="clean_json"),
        _t('{a: 1, b: 2, c: 3,}',
           {"a": 1, "b": 2, "c": 3},
           category="same_shape", shape="mixed_corr"),
    ]

    # --- novel-corruption (substrate has NOT seen this corruption sub
    # type — the heuristic may classify as unknown_*_error, and the
    # teacher stub may itself fail). 12 entries.

    bank += [
        # JSON with leading non-JSON text
        _t('garbage text {"a": 1}', {"a": 1},
           category="novel_corruption", shape="json_leading_text"),
        # JSON with trailing non-JSON text
        _t('{"a": 1} trailing junk', {"a": 1},
           category="novel_corruption", shape="json_trailing_text"),
        # JSON with single quotes instead of double
        _t("{'a': 1}", {"a": 1},
           category="novel_corruption", shape="json_single_quotes"),
        # YAML with mixed tab+space indent
        _t("k:\n\t  v: 1\n", {"k": {"v": 1}},
           category="novel_corruption", shape="yaml_mixed_indent"),
        # JSON with comment (not standard)
        _t('{"a": 1 /* note */}', {"a": 1},
           category="novel_corruption", shape="json_comment"),
        # JSON with hex number
        _t('{"a": 0x1A}', {"a": 26},
           category="novel_corruption", shape="json_hex"),
        # YAML with smart quotes
        _t('k: “v”\n', {"k": "v"},
           category="novel_corruption", shape="yaml_smart_quotes"),
        # JSON with python-style True/None
        _t('{"a": True, "b": None}', {"a": True, "b": None},
           category="novel_corruption", shape="json_python_literals"),
        # TOML with JSON-style braces
        _t('user = {"name": "x"}\n', {"user": {"name": "x"}},
           category="novel_corruption", shape="toml_json_inline"),
        # XML self-closing variant
        _t("<r><a/></r>", {"a": None},
           category="novel_corruption", shape="xml_self_closing"),
        # JSON with unescaped newline in string
        _t('{"a": "line1\nline2"}', {"a": "line1\nline2"},
           category="novel_corruption", shape="json_unescaped_newline"),
        # JSON with NaN
        _t('{"a": NaN}', None,  # legitimately unparseable
           category="novel_corruption", shape="json_nan"),
    ]

    # --- ambiguous (multiple valid parses) — 6 entries -------------------

    bank += [
        # could be YAML "key: 1" mapping OR plain text
        _t("foo: 1\n", {"foo": 1},
           category="ambiguous", shape="yaml_or_text"),
        # could be JSON array OR YAML flow sequence
        _t("[1, 2, 3]", [1, 2, 3],
           category="ambiguous", shape="json_or_yaml_flow"),
        # naked number (JSON null/literal, or text)
        _t("42", 42, category="ambiguous", shape="naked_number"),
        # naked bool
        _t("true", True, category="ambiguous", shape="naked_bool"),
        # could be TOML 'a = 1' OR JSON5 etc.
        _t('a = 1\nb = 2\n', {"a": 1, "b": 2},
           category="ambiguous", shape="toml_or_ini"),
        # could be empty array (JSON) or empty YAML flow
        _t("[]", [], category="ambiguous", shape="empty_collection"),
    ]

    return bank


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


class _NoTeacher:
    """Held-out test guard: any call raises. The world adapter's
    code-path that asks the teacher gets blocked; failures are honest
    instead of being papered over by the teacher stub."""

    def __init__(self):
        self.calls = 0

    def __call__(self, gap: str, text: str) -> dict:
        self.calls += 1
        # Return a 'no parse' spec so the substrate can ground it as a
        # failure record rather than crashing the run; we still record
        # this as a teacher-call which counts as a generalisation failure.
        return {"format": "unknown", "corruption_pattern": "unhandled",
                "parsed": None,
                "reasoning": "teacher disabled in held-out test"}


def run_training(world: StructuredDataWorld, bank: list[dict]) -> list[dict]:
    log = world.run()
    # Decorate with category + shape for downstream reporting.
    for i, e in enumerate(log):
        e["category"] = bank[i].get("category", "training")
        e["shape"] = bank[i].get("shape")
    return log


def run_heldout(s, bank: list[dict]) -> tuple[list[dict], int]:
    """Run held-out bank with teacher disabled. Returns (log,
    blocked_teacher_calls)."""
    no_teacher = _NoTeacher()
    world = StructuredDataWorld(s, bank, no_teacher)
    log = world.run()
    for i, e in enumerate(log):
        e["category"] = bank[i].get("category")
        e["shape"] = bank[i].get("shape")
    return log, no_teacher.calls


def bin_calls(log: list[dict], bin_size: int = 10) -> list[dict]:
    bins = []
    n = len(log)
    for start in range(0, n, bin_size):
        chunk = log[start:start + bin_size]
        bins.append({
            "range": (start + 1, start + len(chunk)),
            "teacher_calls": sum(e["teacher_calls"] for e in chunk),
            "matched": sum(1 for e in chunk if e["matched"]),
            "size": len(chunk),
        })
    return bins


def short(s: str, n: int = 40) -> str:
    r = s.replace("\n", "\\n").replace("\t", "\\t")
    return r if len(r) <= n else r[:n - 3] + "..."


def report(train_log: list[dict],
           heldout_log: list[dict],
           blocked_teacher: int,
           s,
           out_json: Path) -> None:
    print("=" * 76)
    print("StructuredDataWorld generalisation test")
    print("=" * 76)

    n_train = len(train_log)
    train_teach = sum(e["teacher_calls"] for e in train_log)
    train_match = sum(1 for e in train_log if e["matched"])

    print(f"Training bank size: {n_train}")
    print(f"Training teacher calls (cumulative): {train_teach}")
    print(f"Training matched: {train_match}/{n_train}"
          f" ({100*train_match/n_train:.1f}%)")
    print()

    # Saturation point: first bin where teacher_calls drops to 0 and
    # stays at 0.
    bins = bin_calls(train_log, 10)
    print("Training teacher calls per 10-input bin:")
    saturated_at: int | None = None
    for b in bins:
        lo, hi = b["range"]
        print(f"  inputs {lo:3d}-{hi:3d}: teacher_calls={b['teacher_calls']}"
              f"  matched={b['matched']}/{b['size']}")
    # Earliest cumulative input number after which no further teacher call
    # is ever issued.
    last_call_at = None
    for i, e in enumerate(train_log, 1):
        if e["teacher_calls"]:
            last_call_at = i
    if last_call_at is not None:
        saturated_at = last_call_at + 1
        print(f"Last teacher call at input #{last_call_at};"
              f" saturated from #{saturated_at}.")
    else:
        print("No teacher calls in training (every shape was a no-op).")
    print()

    # Held-out
    n_held = len(heldout_log)
    held_match = sum(1 for e in heldout_log if e["matched"])
    print(f"Held-out bank size: {n_held}")
    print(f"Held-out matched: {held_match}/{n_held}"
          f" ({100*held_match/n_held:.1f}%)  (NO teacher)")
    print(f"Held-out attempts that hit no grounded strategy"
          f" (would have called teacher): {blocked_teacher}")
    print()

    # By category
    cats: dict[str, list[dict]] = {}
    for e in heldout_log:
        cats.setdefault(e["category"], []).append(e)
    print("Held-out by category:")
    for cat, items in cats.items():
        m = sum(1 for e in items if e["matched"])
        print(f"  {cat:20s}: {m}/{len(items)}"
              f" ({100*m/len(items):.1f}%)")
    print()

    # Grounded knowledge
    print("Grounded knowledge after training:")
    print(f"  FormatID nodes:           {len(s.nodes('FormatID'))}")
    print(f"  CorruptionPattern nodes:  {len(s.nodes('CorruptionPattern'))}")
    print(f"  ParsingStrategy nodes:    {len(s.nodes('ParsingStrategy'))}")
    print(f"  Observation nodes:        "
          f"{len(s.nodes('StructuredDataObservation'))}")
    print()

    # Generalisation ceiling: held-out shapes that found no grounded
    # strategy.
    print("Generalisation ceiling — held-out shapes with NO grounded"
          " strategy (substrate had to ask the teacher, which was"
          " disabled):")
    ungrounded = [(e["shape"], e["text"], e["expected"], e["parsed"])
                  for e in heldout_log
                  if len(e["gaps_asked"]) > 0]
    if not ungrounded:
        print("  (none — every held-out input matched a grounded shape)")
    else:
        seen_shapes: set[str] = set()
        for shape, text, expected, parsed in ungrounded:
            key = shape or "<unlabelled>"
            if key in seen_shapes:
                continue
            seen_shapes.add(key)
            print(f"  shape={key}")
            print(f"    text     : {short(repr(text), 60)}")
            print(f"    expected : {short(repr(expected), 60)}")
            print(f"    parsed   : {short(repr(parsed), 60)}")
    print()

    # Example failures (max 10)
    failures = [e for e in heldout_log if not e["matched"]]
    print(f"Example failures (showing up to 10 of {len(failures)}):")
    for e in failures[:10]:
        print(f"  category={e['category']}  shape={e['shape']}")
        print(f"    text     : {short(repr(e['text']), 60)}")
        print(f"    expected : {short(repr(e['expected']), 60)}")
        print(f"    parsed   : {short(repr(e['parsed']), 60)}")
        print(f"    fmt/corr : {e['format_id']}/{e['corruption']}")
    print()

    # Dump per-input JSON
    full = {
        "training": [
            {
                "text": e["text"],
                "expected_repr": repr(e["expected"]),
                "parsed_repr": repr(e["parsed"]),
                "format_id": e["format_id"],
                "corruption": e["corruption"],
                "matched": e["matched"],
                "teacher_calls": e["teacher_calls"],
                "gaps_asked": e["gaps_asked"],
                "category": e["category"],
                "shape": e["shape"],
            } for e in train_log
        ],
        "heldout": [
            {
                "text": e["text"],
                "expected_repr": repr(e["expected"]),
                "parsed_repr": repr(e["parsed"]),
                "format_id": e["format_id"],
                "corruption": e["corruption"],
                "matched": e["matched"],
                "teacher_calls": e["teacher_calls"],
                "gaps_asked": e["gaps_asked"],
                "category": e["category"],
                "shape": e["shape"],
            } for e in heldout_log
        ],
        "summary": {
            "n_train": n_train,
            "n_held": n_held,
            "train_teacher_calls": train_teach,
            "train_matched": train_match,
            "held_matched": held_match,
            "held_would_call_teacher": blocked_teacher,
            "grounded": {
                "format_ids": len(s.nodes("FormatID")),
                "corruption_patterns": len(s.nodes("CorruptionPattern")),
                "parsing_strategies": len(s.nodes("ParsingStrategy")),
                "observations": len(s.nodes("StructuredDataObservation")),
            },
        },
    }
    out_json.write_text(json.dumps(full, indent=2, default=str))
    print(f"Per-input log written to: {out_json}")


def main() -> int:
    s = _native.Substrate()
    train = training_bank()
    held = heldout_bank()
    print(f"Training bank: {len(train)} entries")
    print(f"Held-out bank: {len(held)} entries")
    print()

    world = StructuredDataWorld(s, train, teacher_stub)
    train_log = run_training(world, train)

    held_log, blocked = run_heldout(s, held)

    out_json = ROOT / "scripts" / "generalisation_test.log.json"
    report(train_log, held_log, blocked, s, out_json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
