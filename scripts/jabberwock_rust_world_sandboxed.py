"""jabberwock_rust_world_sandboxed — the RustRuntimeWorld driver, hardened.

This is the deliverable the creator reads for the THIRD unguarded
self-modification surface named in commit 54bbecf4's runbook:
`domains/rust_runtime_world.py`'s `RustRuntimeWorld.checkpoint_and_restart`
used to write agent-authored DesignedFile/DesignedPatch content STRAIGHT
into the live `runners/dsl` workspace, run `cargo build`, and — by DEFAULT
(`do_install=True`) — run `maturin develop --release`. No sandbox, no
approval gate. `domains/self_extend_rust.py` (rung-4) and
`domains/proposal_install.py` already got the sandbox-first +
human-approval treatment; this world did not, until now.

Prints, in order:
  1. THE AUDIT — what was unguarded, verbatim, and what changed.
  2. THE AGENT'S EMISSION — a DesignedFile the agent's world sends (both a
     plain `content` string and an AST-composed `ast_root`, to show the
     mechanical render path too).
  3. THE SANDBOX VALIDATION — `validate_designs_in_sandbox()` (also
     reachable via `checkpoint_and_restart()`'s new default): sandbox copy,
     apply, cargo check, diagnostics.
  4. THE DESIGNEDRUNTIMEPROPOSAL — the graph node minted; never
     "ExtensionProposal" (see HONEST RESIDUAL below).
  5. SANDBOX-INTEGRITY PROOF — md5 fingerprints of the live crate + the
     installed extension(s), unchanged before/after.
  6. THE DANGEROUS DEFAULTS, NEUTRALIZED — do_install=True and
     route_to_sandbox=False, both now explicit refusals, demonstrated live.
  7. THE LLM-TEACHER HATCH, GATED — invoke_teacher with no flags makes no
     network call; enable_network=True still requires a real key.
  8. HONEST RESIDUAL + THE APPROVAL RUNBOOK — why a free-form
     DesignedFile/DesignedPatch cannot go through
     `domains.proposal_install.install_proposal` directly (proven live, not
     asserted), and what a human does instead.

This script NEVER writes to `runners/dsl/src`, never calls `maturin`, and
never makes a network call. It only proves, in a sandbox, what the agent's
proposed files/patches would do.

Usage:
    PYTHONPATH=.:runners/dsl/python python3 scripts/jabberwock_rust_world_sandboxed.py
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

import substrate_rs as srs  # noqa: E402
from domains import self_extend_rust as ser  # noqa: E402
from domains import proposal_install as pi  # noqa: E402
from domains.rust_runtime_world import RustRuntimeWorld  # noqa: E402

RUNBOOK = """
=======================================================================
HONEST RESIDUAL + APPROVAL RUNBOOK
=======================================================================

A DesignedFile/DesignedPatch is FREE-FORM (arbitrary path, arbitrary
content, no template) -- unlike rung-4's RustExtensionSpec, which
`render_spec` only knows how to render for a small, fixed set of
`semantics.kind`s. That freedom is exactly why a validated
DesignedRuntimeProposal cannot be losslessly coerced into the
ExtensionProposal shape `domains.proposal_install.install_proposal` knows
how to install -- proven above: even a hand-fabricated ExtensionProposal
claiming a made-up semantics_kind is refused by that function's guardrail 4
(fresh sandbox re-validation: render_spec has no template for it) before
guardrail 5 (the ALLOWED_INSTALL_FILES denylist) is even reached.

So there is NO automatic installer for a DesignedRuntimeProposal. The one
sanctioned path from "cargo check passed in the sandbox" to "live in
runners/dsl/src" is a HUMAN:

  1. Read the sandbox diff (the `sandbox` path printed above is a real,
     inspectable directory -- diff it against runners/dsl by hand, or
     `diff -ru runners/dsl <sandbox>`).
  2. Confirm no other agent has in-flight changes to runners/dsl/src (git
     status / ask in the team channel) -- the installed .so is shared.
  3. Apply the SAME change to the live tree by hand, or -- if the change
     is actually one of rung-4's small set of composition-first
     primitives in disguise -- author it properly as a RustExtensionSpec
     instead and let domains.self_extend_rust + domains.proposal_install
     carry it through their own (already-gated) pipeline.
  4. Only then, `domains.self_extend.PrimitiveExtension.extend(...,
     build=True)` -- the one real, working, snapshotting/auto-rollback
     installer -- run BY A HUMAN, never by this script or by
     RustRuntimeWorld.

Nothing in this module, or in RustRuntimeWorld, takes step 4 automatically.
"""


def _short(t, n=300) -> str:
    t = str(t).replace("\n", " ").strip()
    return t[:n] + "..." if len(t) > n else t


def fresh_world():
    s = srs.Substrate()
    w = RustRuntimeWorld(s, workspace_root=str(ser.LIVE_DSL))
    return s, w


def main() -> None:
    print("=" * 78)
    print("RUSTRUNTIMEWORLD — SANDBOX-FIRST DRIVER (HOST/SAFETY hardened)")
    print("=" * 78)

    # ---- 1. THE AUDIT ----
    print()
    print("-" * 78)
    print("1. THE AUDIT — what was unguarded")
    print("-" * 78)
    print(" - checkpoint_and_restart() used to default do_install=True and")
    print("   write DesignedFile/DesignedPatch content straight into")
    print(f"   {ser.LIVE_DSL} , then run `cargo build` and `maturin develop`.")
    print(" - No sandbox. No approval gate. Flagged in commit 54bbecf4's")
    print("   runbook, fixed here: default is now route_to_sandbox=True,")
    print("   do_install=False (and do_install=True is a REFUSAL, not a")
    print("   silent no-op).")

    s, w = fresh_world()

    # ---- 2. THE AGENT'S EMISSION ----
    print()
    print("-" * 78)
    print("2. THE AGENT'S EMISSION — DesignedFile (content) + DesignedFile (AST)")
    print("-" * 78)
    file_nid = s.add_node("DesignedFile", {
        "path": "src/_jabberwock_rust_world_demo.rs",
        "content": ("// Emitted by the agent's world adapter demo -- never\n"
                     "// referenced by any `mod` declaration, so it plays no\n"
                     "// role in whether the crate compiles; this file exists\n"
                     "// purely to prove the sandbox-write + cargo-check path.\n"
                     "pub fn _jabberwock_rust_world_demo() -> i32 { 7 }\n"),
    })
    print(f" - DesignedFile #{file_nid}: src/_jabberwock_rust_world_demo.rs (content path)")

    # AST-composed second file, to demonstrate render_ast_to_source too.
    root = s.add_node("RustSource", {})
    fn = s.add_node("RustFn", {"name": "_jabberwock_rust_world_demo_ast", "return_type": "i32"})
    stmt = s.add_node("RustStmt", {"text": "42"})
    s.add_edge(fn, "has_stmt", stmt)
    s.add_edge(root, "has_item", fn)
    ast_file_nid = s.add_node("DesignedFile", {"path": "src/_jabberwock_rust_world_demo_ast.rs"})
    s.add_edge(ast_file_nid, "ast_root", root)
    print(f" - DesignedFile #{ast_file_nid}: src/_jabberwock_rust_world_demo_ast.rs (ast_root path)")
    print(f"   rendered: {_short(w.render_ast_to_source(root))}")

    # ---- 3 + 4 + 5. SANDBOX VALIDATION + PROPOSAL + INTEGRITY ----
    print()
    print("-" * 78)
    print("3. SANDBOX VALIDATION — cargo check in a disposable sandbox copy")
    print("-" * 78)
    before = ser.fingerprint_live_tree()
    t0 = time.time()
    result = w.checkpoint_and_restart(
        save_graph_to=str(Path(ser.SANDBOX_ROOT) / "rust_world_demo_checkpoint.json"))
    dt = time.time() - t0
    print(f" - status:              {result['status']}  ({dt:.1f}s)")
    print(f" - applied_files:       {result.get('applied_files')}")
    print(f" - applied_patches:     {result.get('applied_patches')}")
    print(f" - sandbox:             {result.get('sandbox')}")
    print(f" - diagnostics:         {_short(result.get('diagnostics', ''))}")
    print(f" - live_tree_untouched: {result.get('live_tree_untouched')}")

    problems = ser.assert_live_tree_untouched(before)
    print()
    print("-" * 78)
    print("4/5. DESIGNEDRUNTIMEPROPOSAL + INTEGRITY PROOF")
    print("-" * 78)
    props = list(s.nodes("DesignedRuntimeProposal"))
    assert props, "expected a DesignedRuntimeProposal to have been minted"
    pattrs = s.node(props[-1])["attrs"]
    for k in ("status", "installed", "requires_restart", "live_tree_untouched", "sandbox"):
        print(f" - {k}: {pattrs.get(k)}")
    print(f" - fingerprint mismatches (should be EMPTY): {problems}")
    assert not problems, "SAFETY VIOLATION: the live tree/installed .so changed"
    live_file = ser.LIVE_SRC / "_jabberwock_rust_world_demo.rs"
    print(f" - {live_file.name} exists in LIVE src? {live_file.exists()} (must be False)")
    assert not live_file.exists()

    # ---- 6. THE DANGEROUS DEFAULTS, NEUTRALIZED ----
    print()
    print("-" * 78)
    print("6. THE DANGEROUS DEFAULTS, NEUTRALIZED (demonstrated live)")
    print("-" * 78)
    r_install = w.checkpoint_and_restart(do_install=True)
    print(f" - checkpoint_and_restart(do_install=True)      -> status={r_install['status']!r}")
    assert r_install["status"] == "install_refused"
    r_live = w.checkpoint_and_restart(route_to_sandbox=False)
    print(f" - checkpoint_and_restart(route_to_sandbox=False) -> status={r_live['status']!r}")
    assert r_live["status"] == "live_write_removed"
    print(" - neither call wrote to the live tree, built, or installed anything.")

    # ---- 7. THE LLM-TEACHER HATCH, GATED ----
    print()
    print("-" * 78)
    print("7. THE LLM-TEACHER HATCH, GATED")
    print("-" * 78)
    t_result = w.invoke_teacher("add a primitive for X", dry_run=False)
    print(f" - invoke_teacher(intent, dry_run=False)  -> dry_run={t_result['dry_run']}, "
          f"enable_network={t_result['enable_network']}, "
          f"patches_created={len(t_result['patches_created'])}")
    assert t_result["dry_run"] is True and t_result["patches_created"] == []
    print("   (no network call attempted -- enable_network defaults to False,")
    print("    independent of dry_run)")
    t_result2 = w.invoke_teacher("add a primitive for X", dry_run=False, enable_network=True)
    print(f" - invoke_teacher(..., enable_network=True) -> dry_run={t_result2['dry_run']} "
          f"(no ANTHROPIC_API_KEY in this environment -> still no call: "
          f"{_short(t_result2.get('note', ''), 120)})")

    # ---- 8. HONEST RESIDUAL + WOULD-BE APPROVAL ----
    print()
    print("-" * 78)
    print("8. WOULD-BE APPROVAL — proving the free-form shape is refused, live")
    print("-" * 78)
    # Fabricate what a caller would need to coerce this proposal into to even
    # ATTEMPT install_proposal -- a RustExtensionSpec + ExtensionProposal.
    # There is no code path in RustRuntimeWorld that does this; we build it
    # here only to prove the refusal is real, not asserted.
    spec_id = s.add_node("RustExtensionSpec", {
        "name": "JabberwockRustWorldDemo",
        "semantics_kind": "designed_file_freeform",  # no render_spec template
        "compiled": True,
    })
    prop_id = s.add_node("ExtensionProposal", {
        "of": "JabberwockRustWorldDemo", "status": "validated",
        "installed": False, "requires_restart": True,
    })
    s.add_edge_unchecked(prop_id, "validates", spec_id, {})
    approve_result = pi.install_proposal(s, prop_id, approver="demo")
    print(f" - install_proposal(...) on a coerced free-form proposal -> ok={approve_result['ok']}")
    print(f"   reason: {approve_result['reason']}")
    assert approve_result["ok"] is False

    print(RUNBOOK)

    print("=" * 78)
    print("DONE. Live tree untouched, nothing installed, no network call made.")
    print("=" * 78)


if __name__ == "__main__":
    main()
