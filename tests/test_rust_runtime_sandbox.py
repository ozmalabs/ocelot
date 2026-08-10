"""GATE for the hardened rust_runtime_world sandbox pipeline
(domains/rust_runtime_world.py).

`RustRuntimeWorld` was the THIRD unguarded runtime-self-modification
surface flagged in commit 54bbecf4's runbook (the other two,
`domains/self_extend_rust.py` + `domains/proposal_install.py`, already got
the sandbox-first + human-approval treatment). It used to write agent
-authored DesignedFile/DesignedPatch content STRAIGHT into the live
`runners/dsl` workspace, run `cargo build`, and — by DEFAULT
(`do_install=True`) — run `maturin develop --release`, hot-swapping the
installed `_native*.so`. No sandbox, no approval gate.

This gate proves the hardened replacement never crosses that line:
DesignedFile/DesignedPatch -> sandbox copy -> cargo check -> diagnostics on
a DesignedRuntimeProposal node, and NOTHING else -- no maturin call, no
live-source write, no .so write, no network call to an LLM teacher unless
explicitly opted in.

NOTE ON THE LIVE TREE'S CURRENT STATE: a concurrent agent is actively
editing `runners/dsl/src` to extend the Term dialect in this same working
tree (see this module's task brief). That means a real `cargo check` on a
sandbox COPY of the CURRENT live tree may legitimately fail for reasons that
have nothing to do with this gate (the live tree may be mid-edit). The tests
below that need a DETERMINISTIC validated/failed outcome mock
`self_extend_rust.cargo_check`; the one test that runs a REAL cargo check
(`test_real_cargo_check_sandbox_end_to_end`, marked slow) tolerates EITHER
outcome and asserts the safety invariants (isolation, no live write) instead
of a specific compile result.
"""
from __future__ import annotations

import os
import sys
import tempfile
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
for p in (str(ROOT), str(ROOT / "runners" / "dsl" / "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

import substrate_rs as srs  # noqa: E402
from domains import self_extend_rust as ser  # noqa: E402
from domains import proposal_install as pi  # noqa: E402
from domains.rust_runtime_world import RustRuntimeWorld, RRW_SANDBOX_ROOT  # noqa: E402

SCRATCH = Path(tempfile.gettempdir()) / "gamma_substrate_rrw_gate_target"
SCRATCH.mkdir(parents=True, exist_ok=True)


def _scratch_dir() -> str:
    SCRATCH.mkdir(parents=True, exist_ok=True)
    return str(SCRATCH)


def fresh_world() -> tuple:
    s = srs.Substrate()
    w = RustRuntimeWorld(s, workspace_root=str(ser.LIVE_DSL))
    return s, w


# ---------------------------------------------------------------------------
# static: no maturin invocation, no live-tree write, anywhere in this module
# ---------------------------------------------------------------------------

def test_no_maturin_or_cargo_build_in_source():
    """Static check: the old `["cargo", "build", ...]` + `["maturin",
    "develop", ...]` calls are GONE from rust_runtime_world.py, not just
    unreachable by default. Mirrors test_rung4_sandbox's
    `_assert_forbidden_ops_absent`."""
    import inspect
    from domains import rust_runtime_world as rrw
    src = inspect.getsource(rrw)
    assert '["maturin"' not in src, "rust_runtime_world must never invoke maturin"
    assert "subprocess" not in src, (
        "rust_runtime_world should no longer shell out itself -- cargo check "
        "is delegated to self_extend_rust.cargo_check, which is the one "
        "audited subprocess call site")
    assert "cargo_check refuses the LIVE target dir" in inspect.getsource(ser), (
        "the reused self_extend_rust.cargo_check guard must still be present")


def test_designed_runtime_proposal_is_not_extension_proposal():
    """rust_runtime_world mints a DIFFERENT node type than rung-4's
    ExtensionProposal -- so install_proposal (which only ever looks up an
    id explicitly passed to it) never accidentally treats a free-form
    design as an installable, template-rendered spec."""
    import inspect
    from domains import rust_runtime_world as rrw
    src = inspect.getsource(rrw)
    assert 'self.s.add_node("DesignedRuntimeProposal"' in src
    assert 'self.s.add_node("ExtensionProposal"' not in src


# ---------------------------------------------------------------------------
# (a) defaults touch NOTHING live
# ---------------------------------------------------------------------------

def test_a_no_design_present_touches_nothing_live():
    s, w = fresh_world()
    before = ser.fingerprint_live_tree()
    result = w.checkpoint_and_restart(save_graph_to=str(SCRATCH / "cp_a1.json"))
    assert result["status"] == "no_design"
    problems = ser.assert_live_tree_untouched(before)
    assert not problems, problems


def test_a_true_defaults_write_no_file_under_workspace_root():
    """checkpoint_and_restart() with NO save_graph_to at all must not drop
    even a checkpoint JSON inside self.root (the live runners/dsl
    workspace) -- 'defaults touch nothing live' means the live workspace
    directory itself, not merely 'nothing that affects compilation'."""
    s, w = fresh_world()
    before_listing = set(ser.LIVE_DSL.glob("*"))
    result = w.checkpoint_and_restart()  # no save_graph_to
    assert result["status"] == "no_design"
    after_listing = set(ser.LIVE_DSL.glob("*"))
    assert after_listing == before_listing, (
        f"checkpoint_and_restart() with true defaults created file(s) "
        f"directly under the live workspace root: {after_listing - before_listing}")
    from domains.rust_runtime_world import RRW_CHECKPOINT_DEFAULT
    assert RRW_CHECKPOINT_DEFAULT.exists()
    assert not str(RRW_CHECKPOINT_DEFAULT).startswith(str(ser.LIVE_DSL))


def test_a_do_install_true_is_refused_not_run(monkeypatch):
    """The historic danger: do_install defaulted to True and ran maturin.
    Now do_install=True is an explicit REFUSAL -- and even under a design
    being present, nothing live is touched and no subprocess runs."""
    s, w = fresh_world()
    s.add_node("DesignedFile", {"path": "src/_never_written.rs",
                                  "content": "pub fn _unused() {}\n"})

    calls = []
    monkeypatch.setattr(ser, "cargo_check",
                         lambda *a, **k: calls.append(1) or {"ok": True, "returncode": 0,
                                                               "stdout": "", "stderr": "", "seconds": 0.0})

    before = ser.fingerprint_live_tree()
    result = w.checkpoint_and_restart(save_graph_to=str(SCRATCH / "cp_a2.json"),
                                       do_install=True)
    assert result["status"] == "install_refused"
    assert "maturin" not in result["reason"] or "never" in result["reason"] or "no longer" in result["reason"]
    assert not calls, "do_install=True must refuse before ever reaching cargo_check"
    problems = ser.assert_live_tree_untouched(before)
    assert not problems, problems
    assert not (ser.LIVE_SRC / "_never_written.rs").exists()


def test_a_route_to_sandbox_false_is_refused_not_a_live_write():
    s, w = fresh_world()
    s.add_node("DesignedFile", {"path": "src/_never_written2.rs", "content": "x"})
    before = ser.fingerprint_live_tree()
    result = w.checkpoint_and_restart(save_graph_to=str(SCRATCH / "cp_a3.json"),
                                       route_to_sandbox=False)
    assert result["status"] == "live_write_removed"
    problems = ser.assert_live_tree_untouched(before)
    assert not problems, problems
    assert not (ser.LIVE_SRC / "_never_written2.rs").exists()


# ---------------------------------------------------------------------------
# (b) a DesignedFile / DesignedPatch -> sandbox validation -> proposal minted
# ---------------------------------------------------------------------------

def test_b_designed_file_validates_in_sandbox_mocked_ok(monkeypatch):
    s, w = fresh_world()
    fid = s.add_node("DesignedFile", {
        "path": "src/_rrw_probe_ok.rs",
        "content": "pub fn _rrw_probe_ok() -> i32 { 1 }\n",
    })

    monkeypatch.setattr(ser, "cargo_check",
                         lambda *a, **k: {"ok": True, "returncode": 0,
                                           "stdout": "", "stderr": "", "seconds": 0.1})

    before = ser.fingerprint_live_tree()
    result = w.validate_designs_in_sandbox(scratch_dir=_scratch_dir())
    problems = ser.assert_live_tree_untouched(before)

    assert result["status"] == "validated"
    assert result["live_tree_untouched"] is True
    assert "src/_rrw_probe_ok.rs" in result["applied_files"]
    assert not problems, problems
    assert not (ser.LIVE_SRC / "_rrw_probe_ok.rs").exists(), (
        "the file must exist ONLY in the sandbox copy")
    sandboxed = Path(result["sandbox"]) / "src" / "_rrw_probe_ok.rs"
    assert sandboxed.exists() and sandboxed.read_text() == "pub fn _rrw_probe_ok() -> i32 { 1 }\n"

    props = s.nodes("DesignedRuntimeProposal")
    assert len(props) == 1
    pattrs = s.node(props[0])["attrs"]
    assert pattrs["status"] == "validated"
    assert pattrs["installed"] is False
    assert pattrs["requires_restart"] is True
    assert pattrs["live_tree_untouched"] is True
    # linked back to the DesignedFile it summarizes
    assert fid in list(s.neighbours(props[0], "summarizes"))


def test_b_designed_file_fails_in_sandbox_mocked_failure(monkeypatch):
    s, w = fresh_world()
    s.add_node("DesignedFile", {
        "path": "src/_rrw_probe_bad.rs",
        "content": "this is not valid rust\n",
    })

    monkeypatch.setattr(ser, "cargo_check",
                         lambda *a, **k: {"ok": False, "returncode": 101,
                                           "stdout": "", "stderr": "error[E0000]: fake\n",
                                           "seconds": 0.1})

    before = ser.fingerprint_live_tree()
    result = w.validate_designs_in_sandbox(scratch_dir=_scratch_dir())
    problems = ser.assert_live_tree_untouched(before)

    assert result["status"] == "failed"
    assert result["live_tree_untouched"] is True
    assert not problems, problems

    props = [n for n in s.nodes("DesignedRuntimeProposal")]
    assert len(props) == 1
    pattrs = s.node(props[0])["attrs"]
    assert pattrs["status"] == "failed"
    assert pattrs["installed"] is False


def test_b_designed_patch_anchor_surgery_lands_in_sandbox_only(monkeypatch):
    s, w = fresh_world()
    # anchor on real, stable text near the top of term.rs (a module-level
    # doc comment marker is too fragile; use the crate's own file header
    # convention instead -- any unique, long-lived line works for this
    # probe since we only assert isolation, not a specific compile result).
    term_rs = (ser.LIVE_SRC / "term.rs").read_text()
    anchor_line = next(l for l in term_rs.splitlines() if l.strip())
    s.add_node("DesignedPatch", {
        "target_path": "src/term.rs",
        "anchor": anchor_line,
        "position": "after",
        "content": "\n// _rrw_patch_probe\n",
    })

    monkeypatch.setattr(ser, "cargo_check",
                         lambda *a, **k: {"ok": True, "returncode": 0,
                                           "stdout": "", "stderr": "", "seconds": 0.1})

    before = ser.fingerprint_live_tree()
    result = w.validate_designs_in_sandbox(scratch_dir=_scratch_dir())
    problems = ser.assert_live_tree_untouched(before)

    assert "src/term.rs" in result["applied_patches"]
    assert not problems, problems
    assert "_rrw_patch_probe" not in term_rs  # never landed in the live read
    assert "_rrw_patch_probe" not in (ser.LIVE_SRC / "term.rs").read_text()
    sandboxed_term = (Path(result["sandbox"]) / "src" / "term.rs").read_text()
    assert "_rrw_patch_probe" in sandboxed_term


def test_b_run_cargo_check_false_skips_cargo_but_still_sandboxes():
    s, w = fresh_world()
    s.add_node("DesignedFile", {"path": "src/_rrw_probe_nocheck.rs", "content": "x"})
    before = ser.fingerprint_live_tree()
    result = w.validate_designs_in_sandbox(scratch_dir=_scratch_dir(), run_cargo_check=False)
    problems = ser.assert_live_tree_untouched(before)
    assert result["status"] == "applied_no_check"
    assert not problems, problems
    assert not (ser.LIVE_SRC / "_rrw_probe_nocheck.rs").exists()


# ---------------------------------------------------------------------------
# (c) a free-form design, even if coerced into the ExtensionProposal shape,
#     is refused by install_proposal's guardrails
# ---------------------------------------------------------------------------

def test_c_freeform_design_refused_by_install_proposal_guardrail4():
    """rust_runtime_world never mints an ExtensionProposal (test above), so
    install_proposal never sees a free-form design under normal operation.
    This proves the belt-and-suspenders claim in the module docstring: IF
    one were coerced into that shape anyway (spoofing a semantics_kind with
    no real render_spec template -- exactly what a DesignedFile/
    DesignedPatch would need to fake to pass as a RustExtensionSpec),
    install_proposal's guardrail 4 (fresh sandbox re-validation) refuses it
    before ever reaching the denylist or the real installer."""
    s = srs.Substrate()
    spec_id = s.add_node("RustExtensionSpec", {
        "name": "FreeformProbe",
        "semantics_kind": "designed_file_freeform",  # no template exists for this
        "compiled": True,
    })
    prop_id = s.add_node("ExtensionProposal", {
        "of": "FreeformProbe", "status": "validated",
        "installed": False, "requires_restart": True,
    })
    s.add_edge_unchecked(prop_id, "validates", spec_id, {})

    before = ser.fingerprint_live_tree()
    res = pi.install_proposal(s, prop_id, approver="test")
    problems = ser.assert_live_tree_untouched(before)

    assert res["ok"] is False
    assert "sandbox re-validation failed" in res["reason"]
    assert not problems, problems
    assert s.node(prop_id)["attrs"].get("installed") is not True


def test_c_allowed_install_files_denylist_unchanged():
    """Independent confirmation the denylist itself is exactly the small,
    real set of homes -- nothing under rust_runtime_world widens it."""
    assert pi.ALLOWED_INSTALL_FILES == {"term.rs", "jsonio.rs", "reflect.rs", "py.rs", "shape.rs"}
    assert "Cargo.toml" not in pi.ALLOWED_INSTALL_FILES
    assert "*" not in pi.ALLOWED_INSTALL_FILES


# ---------------------------------------------------------------------------
# (d) the LLM-teacher hatch is off by default: no network call
# ---------------------------------------------------------------------------

def test_d_invoke_teacher_default_makes_no_network_call(monkeypatch):
    s, w = fresh_world()
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key-should-never-be-used")

    def _boom(*a, **k):
        raise AssertionError("anthropic.Anthropic must never be constructed "
                              "when enable_network=False (default)")
    try:
        import anthropic
        monkeypatch.setattr(anthropic, "Anthropic", _boom)
    except ImportError:
        pass  # package not installed -- the gate is trivially satisfied

    result = w.invoke_teacher("add a Whatever primitive", dry_run=False)
    assert result["dry_run"] is True
    assert result["enable_network"] is False
    assert result["patches_created"] == []
    assert s.nodes("DesignedPatch") == []


def test_d_invoke_teacher_enable_network_true_without_key_still_no_call(monkeypatch):
    """enable_network=True opts INTO the trust surface, but with no API key
    present the method still can't call out -- proving enable_network is a
    gate, not a bypass of the existing no-key short-circuit."""
    s, w = fresh_world()
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    result = w.invoke_teacher("add a Whatever primitive", dry_run=False, enable_network=True)
    assert result["dry_run"] is True
    assert result["patches_created"] == []
    assert "ANTHROPIC_API_KEY" in result["note"]


# ---------------------------------------------------------------------------
# (e) no real maturin/live-install occurs anywhere in this module (proven by
#     construction: monkeypatched cargo_check above never invokes cargo for
#     real, and no test here calls domains.self_extend.PrimitiveExtension).
# ---------------------------------------------------------------------------

def test_e_primitive_extension_never_imported_or_invoked():
    """The module docstring PROSE names `PrimitiveExtension.extend` when
    pointing at the sanctioned installer a human should use by hand -- that
    mention is fine. What must never appear is an actual import or call
    site: this world must not construct or invoke it itself."""
    import inspect
    from domains import rust_runtime_world as rrw
    src = inspect.getsource(rrw)
    assert "import PrimitiveExtension" not in src
    assert "PrimitiveExtension()" not in src
    assert "self_extend.PrimitiveExtension()" not in src


def test_e_sandbox_crate_is_disjoint_from_self_extend_rust_sandbox_crate():
    """RRW_SANDBOX_ROOT is deliberately the SAME parent directory as
    self_extend_rust.SANDBOX_ROOT (so ser.cargo_check's own
    `startswith(SANDBOX_ROOT)` assertion can be reused as-is), but the
    actual CRATE COPY this world writes into must be a distinct sibling
    directory -- no file ever lands in both."""
    from domains.rust_runtime_world import RRW_SANDBOX_CRATE, RRW_SCRATCH_DEFAULT
    assert str(RRW_SANDBOX_ROOT) == str(ser.SANDBOX_ROOT)
    assert str(RRW_SANDBOX_CRATE) != str(ser.SANDBOX_CRATE)
    assert not str(RRW_SANDBOX_CRATE).startswith(str(ser.SANDBOX_CRATE))
    assert not str(ser.SANDBOX_CRATE).startswith(str(RRW_SANDBOX_CRATE))
    assert str(RRW_SCRATCH_DEFAULT) != str(ser.LIVE_DSL / "target")
    assert str(RRW_SANDBOX_ROOT).startswith(str(ser.ROOT / "var"))


# ---------------------------------------------------------------------------
# one REAL cargo check, end to end (slow; tolerant of either compile
# outcome -- see module docstring on the concurrent-agent caveat)
# ---------------------------------------------------------------------------

@pytest.mark.slow
def test_real_cargo_check_sandbox_end_to_end():
    s, w = fresh_world()
    s.add_node("DesignedFile", {
        "path": "src/_rrw_real_probe.rs",
        # Deliberately NOT referenced by any `mod` declaration anywhere, so
        # it plays no role in whether the crate compiles -- this test's
        # cargo-check OUTCOME just mirrors whatever the live tree's current
        # state is (possibly mid-edit by a concurrent agent); what this
        # test actually proves is the MECHANICS: a real cargo check ran,
        # against a real sandbox copy, and the live tree was untouched
        # either way.
        "content": "pub fn _rrw_real_probe() -> i32 { 42 }\n",
    })

    before = ser.fingerprint_live_tree()
    result = w.validate_designs_in_sandbox(scratch_dir=_scratch_dir(), timeout=1500)
    problems = ser.assert_live_tree_untouched(before)

    assert result["status"] in ("validated", "failed")
    assert "diagnostics" in result
    assert not problems, f"live tree/installed .so changed: {problems}"
    assert not (ser.LIVE_SRC / "_rrw_real_probe.rs").exists()

    props = s.nodes("DesignedRuntimeProposal")
    assert len(props) == 1
    pattrs = s.node(props[0])["attrs"]
    assert pattrs["status"] == result["status"]
    assert pattrs["installed"] is False
    assert pattrs["live_tree_untouched"] is True
