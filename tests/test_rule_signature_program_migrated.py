"""test_rule_signature_program_migrated — gates for the GRAPH-RESIDENT
rule-signature computation (`RULE_SIGNATURE_TO_RUST_RESULTS.md`).

What is under test: `domains/rule_signature_program.py::where_signature_rows`
emitted to hub Program IR, INSTALLED in the graph as a Term subgraph, READ
BACK out of the graph, and executed by the Rust `ProgEval` — replacing the
Python `rule_signature` on the production path
(`domains/rule_signature.py::ensure_where_signature`, which
`_pick_acting_rule` / `_pick_reply_rule` both call).

The Python `rule_signature` is retained as the differential ORACLE and is
what byte-identity is measured against here. The exhaustive version of this
gate (all 2917 real seed `where` clauses) is
`scripts/rule_signature_program_gate.py`; this file runs a fast, bounded
subset so it can live in the bench.

Run: PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 \
     OZMA_SEED_PERSIST_DISABLED=1 python3 -m pytest --confcutdir=. \
     tests/test_rule_signature_program_migrated.py -p no:randomly -q
"""
from __future__ import annotations

import inspect
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

from domains import rule_signature as rsig  # noqa: E402
from domains.prog_ir_emit import emit_prog_ir  # noqa: E402
from domains.rule_signature import rule_signature  # noqa: E402
from domains.rule_signature_program import where_signature_rows  # noqa: E402


def _prog_eval_live() -> bool:
    s = srs.Substrate()
    try:
        s._inner.evaluate({"type": "ProgEval", "prog": {"type": "ProgSeq", "stmts": []},
                           "env": None, "oracles": None, "fuel": 5, "field": ""}, {})
        return True
    except ValueError as e:  # honest skip, never a fake pass (the P1 precedent)
        return "UnknownTermType" not in str(e)


pytestmark = pytest.mark.skipif(not _prog_eval_live(),
                                reason="engine has no ProgEval (rebuild required)")


SYNTHETIC = {
    "not-a-dict": ["a"],
    "no-type": {"a": 1},
    "scalar-atoms": {"type": "Foo", "a": True, "b": None, "c": 1.5, "d": 2, "e": "s"},
    "nested-list-atom": {"type": "Lit", "value": [["a", "b"], ["c"]]},
    "deep-list-atom": {"type": "Lit", "value": [[["x"], 2], 3]},
    "dict-atom": {"type": "Lit", "value": {"zz": 1, "aa": [2, 3], "mm": {"q": 4}}},
    "empty-list-atom": {"type": "Foo", "items": []},
    "mixed-list-is-not-a-term-list": {"type": "Foo",
                                      "items": [{"type": "Var", "name": "a"}, 7]},
    "term-list-repeats-a-var": {"type": "And",
                                "items": [{"type": "Var", "name": "p"},
                                          {"type": "Var", "name": "q"},
                                          {"type": "Var", "name": "p"}]},
    "two-binders": {"type": "Exists", "var_name": "mn",
                    "source": {"type": "NodesOfType", "node_type": "Mention"},
                    "where": {"type": "Exists", "var_name": "cc",
                              "source": {"type": "Var", "name": "mn"},
                              "where": {"type": "Eq",
                                        "a": {"type": "Var", "name": "cc"},
                                        "b": {"type": "Var", "name": "mn"}}}},
}


def _seed_where_clauses(limit_rows: int = 400):
    """Real `where` clauses from the seed corpus, bounded so the bench
    stays fast. The unbounded sweep is the standalone gate script."""
    out = []
    seeds = os.path.join(ROOT, "seeds")
    for fname in sorted(os.listdir(seeds)):
        if not fname.endswith(".json"):
            continue
        try:
            blob = json.load(open(os.path.join(seeds, fname)))
        except Exception:  # noqa: BLE001
            continue
        rules = blob.get("rules") if isinstance(blob, dict) else None
        for r in (rules or []):
            if not isinstance(r, dict) or not isinstance(r.get("where"), dict):
                continue
            sig = rule_signature(r["where"])
            if len(sig) <= limit_rows:
                out.append((f"{fname}:{r.get('name')}", r["where"], sig))
    return out


# ---------------------------------------------------------------------------
# 1. the program is emittable and fully engine-predictable
# ---------------------------------------------------------------------------

def test_program_emits_to_prog_ir_and_is_predictable():
    r = emit_prog_ir(inspect.getsource(where_signature_rows))
    assert r.get("ok") is True, r.get("blockers")
    # "predictable" == every extern it calls has a real native oracle, so no
    # part of the algorithm smuggles itself back out to a host callback.
    assert r["predictable"] is True
    assert set(r["native_oracles"]) == {"get", "isinstance", "keys", "len", "ord"}


def test_the_original_python_is_NOT_emittable_which_is_why_this_rewrite_exists():
    """The measured reason the algorithm had to be re-shaped rather than
    handed to the emitter as-is. If a later engine/emitter widening makes
    these emittable, this test failing is the signal to simplify."""
    from domains import rule_signature as _rs
    blocked = {}
    for fn in (_rs.rule_signature, _rs._collect_var_names, _rs._atomize):
        out = emit_prog_ir(inspect.getsource(fn))
        assert out.get("ok") is False
        blocked[fn.__name__] = out["blockers"]
    assert "DefFn" in blocked["rule_signature"]
    assert "RecvMethod:append" in blocked["_collect_var_names"]
    assert "IsinstanceMultiType" in blocked["_atomize"]


# ---------------------------------------------------------------------------
# 2. byte-identity — CPython twin and the graph-resident execution
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("name", sorted(SYNTHETIC))
def test_cpython_twin_is_byte_identical_on_synthetics(name):
    w = SYNTHETIC[name]
    assert frozenset(where_signature_rows(w)) == rule_signature(w)


def test_cpython_twin_is_byte_identical_on_the_real_seed_corpus():
    cases = _seed_where_clauses()
    assert len(cases) > 500, "seed corpus unexpectedly small — gate is not testing much"
    bad = [n for n, w, sig in cases if frozenset(where_signature_rows(w)) != sig]
    assert bad == []


def test_graph_resident_execution_is_byte_identical():
    """The REAL production path: install into a Substrate, read the IR back
    OUT of the graph, execute it there."""
    sub = srs.Substrate()
    for name in sorted(SYNTHETIC):
        w = SYNTHETIC[name]
        assert rsig.where_signature(sub, w) == rule_signature(w), name
    for name, w, sig in _seed_where_clauses(limit_rows=120)[:150]:
        assert rsig.where_signature(sub, w) == sig, name


def test_alpha_renaming_survives_the_engines_non_lexicographic_string_order():
    """Boundary 3 of the program's docstring, as a gate: the engine's own
    `sorted`/`Lt` over strings is INTERNER-SYMBOL-ID order, not
    lexicographic, and pass 1's key order fixes the variable numbering — so
    a clause whose binder order differs between the two orders is where a
    regression would show up first."""
    w = SYNTHETIC["two-binders"]
    got = rsig.where_signature(srs.Substrate(), w)
    assert got == rule_signature(w)
    assert ("ra", "", "var_name", "?0") in got
    assert ("ra", "where", "var_name", "?1") in got


# ---------------------------------------------------------------------------
# 3. residency — the computation is graph data, found and re-read from there
# ---------------------------------------------------------------------------

def test_program_is_installed_in_the_graph_and_read_back_from_it():
    sub = srs.Substrate()
    rsig._PROGRAM_CACHE.clear()
    ir, oracles = rsig.signature_program(sub)

    holders = [n for n in sub.nodes(rsig.SIGNATURE_PROGRAM_TYPE)
               if sub.node(n)["attrs"].get("name") == rsig.SIGNATURE_PROGRAM_NAME]
    assert len(holders) == 1
    root = sub.node(holders[0])["attrs"]["program_root"]

    # the IR handed to ProgEval is what the GRAPH holds, not what Python emitted
    back = sub._inner.term_subgraph_json(root)
    from_graph = json.loads(back) if isinstance(back, str) else back
    assert ir == from_graph
    # ... and it is a real Term subgraph, not an opaque blob
    assert from_graph["type"] == "ProgSeq"
    assert len(sub.nodes()) > 500   # ~857 Term nodes: the residency cost, measured

    # idempotent: a second call finds the held node, mints nothing
    rsig._PROGRAM_CACHE.clear()
    ir2, oracles2 = rsig.signature_program(sub)
    assert ir2 == ir and oracles2 == oracles
    assert len([n for n in sub.nodes(rsig.SIGNATURE_PROGRAM_TYPE)
                if sub.node(n)["attrs"].get("name") == rsig.SIGNATURE_PROGRAM_NAME]) == 1


def test_ensure_where_signature_mints_from_the_graph_resident_program():
    sub = srs.Substrate()
    rsig._PROGRAM_CACHE.clear()
    clause = SYNTHETIC["two-binders"]
    n = sub.add_node("RuleSummary", {"name": "probe",
                                     "rule_json": json.dumps({"where": clause})})
    touched = rsig.ensure_where_signature(sub)
    assert touched == 1
    stored = sub.node(n)["attrs"]["where_signature_json"]
    assert rsig._rows_from_jsonable(stored) == rule_signature(clause)
    # idempotent
    assert rsig.ensure_where_signature(sub) == 0


def test_a_trapping_clause_is_skipped_not_guessed():
    """The honest-degradation contract: a clause the graph-resident program
    cannot finish leaves the attr UNSET (production reads that as an
    abstain — its pre-wiring behaviour) rather than taking a value from a
    second, divergent implementation."""
    sub = srs.Substrate()
    rsig._PROGRAM_CACHE.clear()
    clause = SYNTHETIC["two-binders"]
    n = sub.add_node("RuleSummary", {"name": "probe",
                                     "rule_json": json.dumps({"where": clause})})
    old = rsig.SIGNATURE_PROGRAM_FUEL
    try:
        rsig.SIGNATURE_PROGRAM_FUEL = 5     # force fuel exhaustion
        with pytest.raises(rsig.SignatureProgramTrap):
            rsig.where_signature(sub, clause)
        assert rsig.ensure_where_signature(sub) == 0
        assert sub.node(n)["attrs"].get("where_signature_json") is None
    finally:
        rsig.SIGNATURE_PROGRAM_FUEL = old
