"""test_prog_read_gap_migrated — P2.5 gates: the reading frames wire into
the agent's standing gap machinery (PROGRAM_SYNTHESIS_PLAN.md; closes the
two recorded P2 residuals in PROGRAM_SYNTHESIS_P2_RUST_LUA.md §7).

RESIDUAL 1 — python uploads emit hub IR: `_ingest_source` now runs
`domains/prog_ir_emit.emit_prog_ir` per TOP-LEVEL function of an uploaded
.py and attaches ok reads as reflected Term subgraphs (`has_prog_ir`,
ProgEval-runnable) exactly the way the rust/lua path already did.

RESIDUAL 2 — blocked reads FILE gaps, as a GRAPH decision: the adapter
only records FACTS (`read_blocked=1.0`, `read_blockers="a,b"`,
`frame="rust|lua|python"` on the ingested document / function code-root
node — domains/file_ingest._record_read_blocked); the RULE
`note_prog_read_gap` (seeds/prog_read_gap.json, the gap_awareness.json
pattern: content-dedup Not-Exists guard + mint-once attr) DECIDES a
blocked read is a gap and mints SelfConcern{kind:'prog_read',
source:'implicit', status:'noted'} — entering the standing promote
pipeline and the `_run_self_gaps` surfacing reader with zero new plumbing.

Run (worktree engine discipline — the P1 note):
    pytest tests/test_prog_read_gap_migrated.py --confcutdir=. -q
"""
from __future__ import annotations

import os
import sys
import tempfile

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import substrate_rs as srs


def _prog_eval_live() -> bool:
    s = srs.Substrate()
    try:
        s._inner.evaluate({"type": "ProgEval",
                           "prog": {"type": "ProgSeq", "stmts": []},
                           "env": None, "oracles": None, "fuel": 10,
                           "field": ""}, {})
        return True
    except ValueError as e:
        if "UnknownTermType" in str(e):
            return False
        raise


if not _prog_eval_live():
    pytest.skip(
        "ProgEval Term not present in the installed substrate_rs binary — "
        "rebuild runners/dsl. Honest skip, not a fake pass.",
        allow_module_level=True)


PY_TWO_FUNCTIONS = """
def add_one(x):
    return x + 1

def uses_lambda(v):
    f = lambda y: y + 1
    return f(v)
"""

LUA_VARARGS = "function residual_varargs(...)\n  return 1\nend\n"


def _boot_agent():
    from substrate.boot_all import load_all_seeds
    from substrate.world_adapter import WorldAdapter
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    return agent


def _ingest_source_text(agent, text: str, filename: str) -> dict:
    import domains.file_ingest as fi
    suffix = os.path.splitext(filename)[1]
    with tempfile.NamedTemporaryFile("w", suffix=suffix, delete=False,
                                     encoding="utf-8") as f:
        f.write(text)
        path = f.name
    try:
        return fi.ingest_file(agent, path, filename=filename)
    finally:
        os.unlink(path)


def _prog_read_concerns(agent) -> list:
    out = []
    for sc in agent.inner.neighbours(agent.agent, "has_self_concern"):
        if not agent.inner.has_node(sc):
            continue
        at = agent.s.node(sc)["attrs"]
        if at.get("kind") == "prog_read":
            out.append(at)
    return out


# ---------------------------------------------------------------------------
# RESIDUAL 1 + 2, python frame — one upload, both halves.
# ---------------------------------------------------------------------------
def test_python_upload_emits_ir_and_blocked_fn_files_gap():
    agent = _boot_agent()
    out = _ingest_source_text(agent, PY_TWO_FUNCTIONS, "two_fns.py")
    assert out["kind"] == "source" and out["language"] == "python"
    assert out["n_functions"] == 2
    assert out["n_ir_ok"] == 1, "the emittable function must land as hub IR"
    assert out["ir_blockers"] == ["Lambda"]
    doc = out["document_id"]

    # the emittable function carries a reflected IR subgraph ProgEval RUNS.
    ir_roots = list(agent.inner.neighbours(doc, "has_prog_ir"))
    assert len(ir_roots) == 1
    assert agent.s.node(ir_roots[0])["attrs"].get("prog_name") == "add_one"
    res = agent.inner.evaluate(
        {"type": "ProgEval", "prog": {"type": "Var", "name": "p"},
         "env": {"type": "Var", "name": "envd"}, "oracles": None,
         "fuel": 500, "field": ""},
        {"p": ir_roots[0], "envd": {"x": 41}})
    assert res["trap"] is None and res["halted"] is True
    assert res["result"] == 42

    # the Lambda function carries the blocked-read FACTS on its OWN
    # code-root node (adapter records; no decision).
    blocked = [r for r in agent.inner.neighbours(doc, "has_code_root")
               if agent.s.node(r)["attrs"].get("read_blocked") == 1.0]
    assert len(blocked) == 1
    battrs = agent.s.node(blocked[0])["attrs"]
    assert battrs.get("frame") == "python"
    assert "Lambda" in battrs.get("read_blockers", "")
    # ... and aggregated on the document (what the rule reads).
    dattrs = agent.s.node(doc)["attrs"]
    assert dattrs.get("read_blocked") == 1.0
    assert dattrs.get("frame") == "python"

    # after run_rules the RULE has decided: a SelfConcern{kind:'prog_read'}
    # exists, blocker named, in the standing promote shape (status 'noted').
    agent.comprehend()
    concerns = _prog_read_concerns(agent)
    assert len(concerns) == 1
    c = concerns[0]
    assert c.get("status") == "noted" and c.get("source") == "implicit"
    assert "Lambda" in c.get("content", "")
    assert c.get("content", "").startswith("python")


# ---------------------------------------------------------------------------
# dedup — same blocked file twice → exactly one SelfConcern.
# ---------------------------------------------------------------------------
def test_same_blocked_file_twice_files_exactly_one_gap():
    agent = _boot_agent()
    _ingest_source_text(agent, PY_TWO_FUNCTIONS, "two_fns_a.py")
    _ingest_source_text(agent, PY_TWO_FUNCTIONS, "two_fns_b.py")
    agent.comprehend()
    agent.comprehend()  # fixpoint re-run must not duplicate either
    concerns = _prog_read_concerns(agent)
    assert len(concerns) == 1, (
        "the content-dedup Not-Exists guard must file one gap per distinct "
        f"blocked-read content, got: {concerns}")


# ---------------------------------------------------------------------------
# lua frame — a blocked upload files a gap NAMING THE FRAME; the gap
# surfaces through the existing reader.
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def lua_blocked_agent():
    pytest.importorskip("tree_sitter_lua")
    agent = _boot_agent()
    out = _ingest_source_text(agent, LUA_VARARGS, "va.lua")
    assert out["n_functions"] == 1 and out["n_ir_ok"] == 0
    agent.comprehend()
    return agent


def test_blocked_lua_upload_files_gap_naming_frame(lua_blocked_agent):
    concerns = _prog_read_concerns(lua_blocked_agent)
    assert len(concerns) == 1
    c = concerns[0]
    assert c.get("frame") == "lua"
    assert c.get("content", "").startswith("lua")
    assert "varargs" in c.get("content", "")
    assert c.get("status") == "noted" and c.get("source") == "implicit"


def test_prog_read_gap_surfaces_via_existing_reader(lua_blocked_agent):
    from domains.reflective_faculty import _run_self_gaps
    g = _run_self_gaps(lua_blocked_agent.s)
    assert g["count"] >= 1
    assert any(c["kind"] == "prog_read"
               and "lua read blocked: varargs" in c["content"]
               for c in g["concerns"])
    assert "lua read blocked: varargs" in g["note"]


# ---------------------------------------------------------------------------
# install idempotence — a LEAN agent (no load_all_seeds) gets the seed at
# source-ingest time, ONCE, and the rule still fires.
# ---------------------------------------------------------------------------
def test_seed_installs_idempotently_on_lean_agent():
    from substrate.world_adapter import WorldAdapter
    agent = WorldAdapter(seeds=())
    _ingest_source_text(agent, PY_TWO_FUNCTIONS, "lean_a.py")
    _ingest_source_text(agent, PY_TWO_FUNCTIONS, "lean_b.py")
    seed_nodes = [n for n in agent.s.nodes("Seed")
                  if agent.s.node(n)["attrs"].get("id") == "prog_read_gap"]
    assert len(seed_nodes) == 1, "install must be idempotent by Seed id"
    agent.comprehend()
    concerns = _prog_read_concerns(agent)
    assert len(concerns) == 1
    assert "Lambda" in concerns[0].get("content", "")
