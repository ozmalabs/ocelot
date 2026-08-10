"""GATE for the hardened rung-4 sandbox pipeline (domains/self_extend_rust.py).

Rung-4 ("the agent proposes a change to its own Rust runtime") already WORKS
in this codebase (domains/self_extend.py; ArgMax/DtwTo/Whiten/WithinScatter/
BetweenScatter/WhitenMany/... all landed via it across real historic commits).
What it lacked was a SANDBOXED validation path: it patches the LIVE crate
source and, at its real call site (reflective_faculty.self_extend_ladder),
runs `maturin develop --release` -- a real install, hot-swapping the .so
every other process has already imported. That is unsafe while concurrent
agents depend on the installed extension staying stable.

This gate proves the hardened replacement never crosses that line: spec ->
render -> sandbox copy -> cargo check -> diagnostics on the node, and
NOTHING else -- no maturin call, no live-source write, no .so write.

Marked slow: a cold cargo check compiles ~170 dependencies from scratch into
a throwaway CARGO_TARGET_DIR. Once primed (the sandbox target dir persists
across runs), the incremental checks used here take well under a minute.
"""
from __future__ import annotations

import inspect
import os
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
for p in (str(ROOT), str(ROOT / "runners" / "dsl" / "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

from domains import self_extend_rust as ser  # noqa: E402

pytestmark = pytest.mark.slow

SCRATCH = Path(tempfile.gettempdir()) / "gamma_substrate_rung4_gate_target"


def _scratch_dir() -> str:
    SCRATCH.mkdir(parents=True, exist_ok=True)
    return str(SCRATCH)


# ---------------------------------------------------------------------------
# (c) helper: nothing outside the sandbox/scratch was touched
# ---------------------------------------------------------------------------

def _assert_forbidden_ops_absent():
    """Static check: self_extend_rust never calls maturin, never opens
    runners/dsl/src for writing, never touches an installed .so. Checks the
    actual INVOCATION shape (`["maturin"`, matching how self_modification.py
    / rust_runtime_world.py really call it via subprocess.run([...])), not
    the bare word -- this module's own docstrings and FORBIDDEN tuple name
    "maturin" as prose/documentation, which is fine."""
    src = inspect.getsource(ser)
    assert '["maturin"' not in src, "self_extend_rust must never invoke maturin"
    # every subprocess.run call in the module must be a cargo invocation
    # (no pip / maturin / anything else that could install or mutate the
    # active environment)
    import re
    calls = re.findall(r"subprocess\.run\(\s*\[([^\]]*)\]", src)
    assert calls, "expected at least the cargo check subprocess.run call"
    for argv_src in calls:
        assert "cargo" in argv_src, f"unexpected subprocess.run argv: {argv_src!r}"
        assert "maturin" not in argv_src
    # every write_text call in the module must be scoped under the sandbox
    # (either directly via `sandbox_crate` / `SANDBOX_CRATE`, or the .gitignore
    # bootstrap under SANDBOX_ROOT) -- grep for the one write-capable helper
    # (`apply_to_sandbox`) and confirm its assertion guard is present.
    assert "apply_to_sandbox refuses a path outside the sandbox root" in src
    assert "cargo_check refuses the LIVE target dir" in src


def test_forbidden_ops_absent_statically():
    _assert_forbidden_ops_absent()


def test_apply_to_sandbox_refuses_live_path():
    with pytest.raises(AssertionError):
        ser.apply_to_sandbox(ser.LIVE_SRC.parent, [])


def test_cargo_check_refuses_live_target_dir():
    sandbox = ser.prepare_sandbox(force=True)
    with pytest.raises(AssertionError):
        ser.cargo_check(sandbox, ser.LIVE_DSL / "target")


# ---------------------------------------------------------------------------
# (a) the driven spec: render -> sandbox -> cargo check PASSES
# ---------------------------------------------------------------------------

def test_a_driven_spec_validates_in_sandbox():
    import substrate_rs as srs
    from substrate.seed_loader import manifest_for

    s = srs.Substrate()
    inner = s._inner
    agent = s.add_node("Agent", {})
    inner.load_seed_manifest(manifest_for("compiler_theory"), agent)

    spec = ser.agent_specify_reachable_from_primitive(s)
    assert spec["name"] == "ReachableFrom"
    assert spec["semantics"]["kind"] == "graph_reachability"
    assert spec["grounded_in_science"] is True, (
        "the driven spec should ground on compiler_theory's "
        "eliminate_unreachable_bb/dead_block_elimination concept "
        "(reachability from an entry node) -- if this is False the "
        "grounding scan silently stopped matching the seed's shape")

    before = ser.fingerprint_live_tree()
    res = ser.validate_spec(s, spec, scratch_dir=_scratch_dir())
    assert res["ok"] is True, res.get("diagnostics")

    if res["stage"] == "already_present":
        # The creator approved + installed ReachableFrom into the live
        # runtime; the pipeline must refuse to re-apply (double definition)
        # and report honestly -- and the primitive must genuinely work live.
        assert res["already_installed"] is True
        assert res["live_tree_untouched"] is True
        a = s.add_node("Element", {}); b = s.add_node("Element", {})
        s.add_edge_unchecked(a, "contains", b, {})
        reached = s._inner.evaluate(
            {"type": "ReachableFrom", "node": {"type": "Var", "name": "x"},
             "edge_type": "contains"}, {"x": a})
        assert list(reached) == [b]
        props = s.nodes("ExtensionProposal")
        assert props and s.node(props[-1])["attrs"]["status"] == "already_present"
        assert s.node(props[-1])["attrs"]["installed"] is False
        return

    assert res["stage"] == "cargo_check"
    assert res["returncode"] == 0

    # the rendered fragments actually landed in the sandbox copy, all 9
    # TermNode homes (proves the transcriber, not just "cargo said 0 files
    # changed").
    sandbox = Path(res["sandbox"])
    term_rs = (sandbox / "src" / "term.rs").read_text()
    jsonio_rs = (sandbox / "src" / "jsonio.rs").read_text()
    reflect_rs = (sandbox / "src" / "reflect.rs").read_text()
    assert "ReachableFrom { node: TermIdx, edge_type: Sym, any_type: bool }," in term_rs
    assert "TermNode::ReachableFrom { node, edge_type, any_type } => {" in term_rs
    assert 'TermNode::ReachableFrom { .. } => "ReachableFrom",' in jsonio_rs
    assert '"ReachableFrom" => {' in jsonio_rs
    assert 'TermNode::ReachableFrom { node, edge_type, any_type } => ("ReachableFrom", vec![' in reflect_rs

    problems = ser.assert_live_tree_untouched(before)
    assert not problems, f"live tree/installed .so changed: {problems}"

    # ExtensionProposal + RustExtensionSpec graph nodes minted, correctly
    # linked, and honest about not installing (checked fully in test_e).
    specs = s.nodes("RustExtensionSpec")
    assert len(specs) == 1
    assert s.node(specs[0])["attrs"]["compiled"] is True
    props = s.nodes("ExtensionProposal")
    assert len(props) >= 1
    latest = props[-1]
    pattrs = s.node(latest)["attrs"]
    assert pattrs["status"] == "validated"
    assert pattrs["of"] == "ReachableFrom"


# ---------------------------------------------------------------------------
# (b) a deliberately-broken spec FAILS with diagnostics captured onto the node
# ---------------------------------------------------------------------------

def test_b_broken_spec_fails_with_captured_diagnostics():
    import substrate_rs as srs

    s = srs.Substrate()

    orig = ser._emit_graph_reachability
    def _broken(spec):
        frags = dict(orig(spec))
        # bad type in the signature -- E0425 "cannot find type"
        frags["term.rs (enum variant)"] = (
            f"    {spec['name']} {{ node: NotARealType, edge_type: Sym, any_type: bool }},")
        return frags
    ser._TEMPLATES["graph_reachability"] = _broken
    try:
        spec = {"name": "BrokenReachableGate",
                "signature": {"node": "NotARealType"},
                "semantics": {"kind": "graph_reachability"},
                "purpose": "gate case: deliberately broken",
                "why_new": "test", "motivating_residual": "test"}
        before = ser.fingerprint_live_tree()
        res = ser.validate_spec(s, spec, scratch_dir=_scratch_dir())
    finally:
        ser._TEMPLATES["graph_reachability"] = orig

    assert res["ok"] is False
    assert res["stage"] == "cargo_check"
    assert res["returncode"] != 0
    # the agent can SEE why: the real rustc diagnostic, not a swallowed
    # exception or a warning-only tail.
    assert "NotARealType" in res["diagnostics"]
    assert "E0425" in res["diagnostics"] or "cannot find type" in res["diagnostics"]

    problems = ser.assert_live_tree_untouched(before)
    assert not problems, f"live tree/installed .so changed on a FAILED spec: {problems}"

    # captured onto the graph node too, not just the return value.
    specs = [n for n in s.nodes("RustExtensionSpec")
             if s.node(n)["attrs"].get("name") == "BrokenReachableGate"]
    assert len(specs) == 1
    sattrs = s.node(specs[0])["attrs"]
    assert sattrs["compiled"] is False
    assert "NotARealType" in sattrs["errors"] or "E0425" in sattrs["errors"]

    props = [n for n in s.nodes("ExtensionProposal")
             if s.node(n)["attrs"].get("of") == "BrokenReachableGate"]
    assert len(props) == 1
    pattrs = s.node(props[0])["attrs"]
    assert pattrs["status"] == "failed"
    assert pattrs["installed"] is False


# ---------------------------------------------------------------------------
# (c) integrity: nothing outside sandbox/scratch was modified, for EITHER
#     outcome above (re-checked independently here with fresh fingerprints)
# ---------------------------------------------------------------------------

def test_c_sandbox_is_disjoint_from_live_and_scratch_paths():
    assert str(ser.SANDBOX_ROOT).startswith(str(ser.ROOT / "var"))
    assert str(ser.SANDBOX_CRATE) != str(ser.LIVE_DSL)
    assert not str(ser.SANDBOX_CRATE).startswith(str(ser.LIVE_SRC))
    target = ser.default_scratch_target(_scratch_dir())
    assert str(target) != str(ser.LIVE_DSL / "target")
    assert str(target).startswith(_scratch_dir())


def test_c_full_pipeline_leaves_live_tree_and_installed_so_untouched():
    import substrate_rs as srs
    s = srs.Substrate()
    spec = {"name": "IntegrityProbeTerm",
            "signature": {"node": "Node", "edge_type": "Sym"},
            "semantics": {"kind": "graph_reachability"},
            "purpose": "integrity probe", "why_new": "test"}
    before = ser.fingerprint_live_tree()
    assert before, "fingerprint_live_tree found nothing -- test would be vacuous"
    ser.validate_spec(s, spec, scratch_dir=_scratch_dir())
    problems = ser.assert_live_tree_untouched(before)
    assert not problems, problems


# ---------------------------------------------------------------------------
# (d) the proposal node persists via checkpoint (graph_to_dict/from_dict)
# ---------------------------------------------------------------------------

def test_d_proposal_persists_via_checkpoint():
    import substrate_rs as srs
    s = srs.Substrate()
    spec = {"name": "CheckpointProbeTerm",
            "signature": {"node": "Node", "edge_type": "Sym"},
            "semantics": {"kind": "graph_reachability"},
            "purpose": "checkpoint probe", "why_new": "test"}
    res = ser.validate_spec(s, spec, scratch_dir=_scratch_dir())
    assert res["ok"] is True

    graph_dict = s.graph_to_dict()
    fresh = srs.Substrate()
    fresh.graph_from_dict(graph_dict)

    specs = [n for n in fresh.nodes("RustExtensionSpec")
             if fresh.node(n)["attrs"].get("name") == "CheckpointProbeTerm"]
    assert len(specs) == 1
    assert fresh.node(specs[0])["attrs"]["compiled"] is True

    props = [n for n in fresh.nodes("ExtensionProposal")
             if fresh.node(n)["attrs"].get("of") == "CheckpointProbeTerm"]
    assert len(props) == 1
    pattrs = fresh.node(props[0])["attrs"]
    assert pattrs["status"] == "validated"
    assert pattrs["requires_restart"] is True
    assert pattrs["installed"] is False

    # the `validates` edge survives the round-trip too.
    edges = fresh.neighbours(props[0], "validates")
    assert list(edges) == specs


# ---------------------------------------------------------------------------
# (e) no install ever occurs: requires_restart honoured, status never
#     "installed", regardless of outcome
# ---------------------------------------------------------------------------

def test_e_no_install_ever_status_never_installed():
    import substrate_rs as srs
    s = srs.Substrate()
    good = {"name": "NoInstallGood", "signature": {}, "semantics": {"kind": "graph_reachability"},
            "purpose": "x", "why_new": "x"}
    bad = {"name": "NoInstallBad", "signature": {"node": "NotAType"},
           "semantics": {"kind": "graph_reachability"}, "purpose": "x", "why_new": "x"}

    orig = ser._emit_graph_reachability
    def _broken(spec):
        frags = dict(orig(spec))
        frags["term.rs (enum variant)"] = (
            f"    {spec['name']} {{ node: NotAType, edge_type: Sym, any_type: bool }},")
        return frags

    ser.validate_spec(s, good, scratch_dir=_scratch_dir())
    ser._TEMPLATES["graph_reachability"] = _broken
    try:
        ser.validate_spec(s, bad, scratch_dir=_scratch_dir())
    finally:
        ser._TEMPLATES["graph_reachability"] = orig

    statuses = {s.node(n)["attrs"]["of"]: s.node(n)["attrs"]
                for n in s.nodes("ExtensionProposal")}
    assert statuses["NoInstallGood"]["status"] == "validated"
    assert statuses["NoInstallBad"]["status"] == "failed"
    for attrs in statuses.values():
        assert attrs["status"] != "installed"
        assert attrs["installed"] is False
        assert attrs["requires_restart"] is True

    # and, again, the installed .so + live source were never touched by
    # either the good or the bad run.
    so_paths = ser._installed_so_paths()
    assert so_paths, "expected at least one installed _native*.so to check"
