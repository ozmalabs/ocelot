"""jabberwock_extends_runtime — the RUNG-4 driver: the agent proposes a change
to its own Rust runtime, entirely sandboxed, and this script reports what
happened. This is the deliverable the creator reads.

Prints, in order:
  1. THE AUDIT — rung-4's real state before this hardening (works, but
     unsandboxed; see domains/self_extend_rust.py's module docstring for the
     full account).
  2. THE AGENT'S SPEC — a RustExtensionSpec authored the same way every other
     rung-4 primitive in this codebase has been authored (the agent_specify_*
     pattern in domains/runtime_design.py): inspect what's grounded, name the
     residual, specify the primitive. Here: `ReachableFrom`, closing the
     transitive-closure gap worlds/browser.py names explicitly ("the DSL has
     no transitive-closure Term").
  3. THE RENDERED DIFF — every home the mechanical transcriber touched, in
     the SANDBOX copy only.
  4. THE CARGO CHECK OUTCOME — pass/fail + diagnostics, timing.
  5. SANDBOX-INTEGRITY PROOF — md5 fingerprints of the live crate + the
     installed extension(s), unchanged before/after.
  6. THE APPROVAL RUNBOOK — the exact, human-run steps to go from a
     "validated" ExtensionProposal to an actual installed primitive. This
     script NEVER performs those steps; `--apply` (below) is a documented
     no-op unless a human explicitly confirms, and even then it only prints
     the commands -- it does not run maturin either. Installation is not
     this script's job.

Usage:
    PYTHONPATH=.:runners/dsl/python python3 scripts/jabberwock_extends_runtime.py
    PYTHONPATH=.:runners/dsl/python python3 scripts/jabberwock_extends_runtime.py --apply
        (--apply only PRINTS the human runbook more prominently; it still
        never writes to runners/dsl or calls maturin -- see RUNBOOK below.)
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

from domains import self_extend_rust as ser  # noqa: E402

SCRATCH_DEFAULT = os.environ.get(
    "SELF_EXTEND_SCRATCH",
    os.path.join(os.path.expanduser("~"), ".cache", "gamma_substrate_self_extend"))

RUNBOOK = """
=======================================================================
APPROVAL RUNBOOK — turning a "validated" ExtensionProposal into a real,
installed primitive. NONE of these steps run automatically. A HUMAN runs
them, on purpose, after reading the diagnostics above.
=======================================================================

This script (and domains/self_extend_rust.py underneath it) NEVER calls
maturin and NEVER writes to runners/dsl/src. It only proves, in a sandbox,
that the agent's proposed Rust compiles. Two concurrent agents currently
depend on the installed extension staying stable — do not skip the review
step below just because cargo check was green in the sandbox.

  1. Review the rendered diff (printed above, or re-derive it):

       PYTHONPATH=.:runners/dsl/python python3 -c "
       from domains import self_extend_rust as ser
       frags = ser.render_spec(<the spec dict>)
       for k, v in frags.items(): print(f'--- {k} ---\\n{v}\\n')"

  2. Re-run the sandbox check yourself if any time has passed (the live
     tree may have moved since validation):

       PYTHONPATH=.:runners/dsl/python python3 scripts/jabberwock_extends_runtime.py

  3. Confirm no other agent has in-flight changes to runners/dsl/src
     (git status / ask in the team channel) -- the installed .so is
     shared; a rebuild mid-use of another process is the exact failure
     mode this sandbox was built to avoid.

  4. Apply the SAME patch to the LIVE tree (by hand, or by reusing the
     existing, real, live-source pipeline this module deliberately does
     NOT call):

       from domains.self_extend import PrimitiveExtension
       pe = PrimitiveExtension()
       pe.extend(<the spec, with semantic_kind = its rung-4 kind>, build=True)

     `PrimitiveExtension.extend` is real and already works (ArgMax, DtwTo,
     Whiten, WithinScatter, BetweenScatter, WhitenMany, and the whole
     structural-recursion family all landed through it) -- it snapshots
     every touched file, applies, runs `cargo check`, then `maturin
     develop --release`, and restores everything on ANY failure. This is
     the ONLY step in this entire runbook that touches runners/dsl/src or
     calls maturin, and it is not run by this script.

  5. `maturin develop --release` hot-swaps the installed `_native*.so`
     (`domains/self_modification.py:SelfModification._sync_native`) for
     every NEW Python process from that point on; PROCESSES ALREADY
     RUNNING keep the old binary (the old inode stays mapped) until they
     restart. Coordinate a restart window with the other agent(s).

  6. Mark the ExtensionProposal node `installed: true` AFTER step 4/5
     succeed (mechanical bookkeeping, not this module's job -- it always
     writes `installed: false`).

NOTE: domains/rust_runtime_world.py (`RustRuntimeWorld.checkpoint_and_
restart`) is a THIRD existing surface that can write DesignedFile /
DesignedPatch nodes straight to a live workspace, run `cargo build`, and
by DEFAULT (`do_install=True`) run `maturin develop --release` -- with no
sandbox and no approval gate. It was NOT invoked anywhere in building this
pipeline. It should get the same sandbox-first treatment before it is
driven again; flagged here so the creator sees it, not fixed in this pass
(out of this task's file scope).
=======================================================================
"""


def _print_header(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def _boot_grounding_substrate():
    """A LIGHTWEIGHT substrate carrying just the seed the spec grounds
    against (compiler_theory) -- not the full load_all_seeds boot, so this
    driver stays independent of in-flight work on other seed manifests
    (composer migration etc. own seeds/*, not touched here)."""
    import substrate_rs as srs
    from substrate.seed_loader import manifest_for
    s = srs.Substrate()
    inner = s._inner
    agent = s.add_node("Agent", {})
    try:
        inner.load_seed_manifest(manifest_for("compiler_theory"), agent)
    except Exception as e:  # noqa: BLE001
        print(f"  (grounding seed load failed, continuing ungrounded: {e})")
    return s


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                     help="print the approval runbook more prominently (never installs)")
    ap.add_argument("--scratch", default=SCRATCH_DEFAULT)
    args = ap.parse_args()

    _print_header("1. AUDIT — rung-4's state BEFORE this hardening")
    print(
        "  domains/self_extend.py:PrimitiveExtension is REAL and has landed real\n"
        "  primitives across historic commits (ArgMax 13e1d38a, the self-mod Layer-B\n"
        "  0b3ad6dd, the structural-recursion family b3065f51 -- grep TermNode::ArgMax /\n"
        "  DtwTo / Whiten / WithinScatter / BetweenScatter / WhitenMany in\n"
        "  runners/dsl/src/term.rs to see them live today). rung-4 WORKS.\n\n"
        "  But it operates on the LIVE crate (runners/dsl/src/*.rs) and its real call\n"
        "  site (reflective_faculty.self_extend_ladder, rung-4 branch) calls\n"
        "  PrimitiveExtension.extend(..., build=True) -> maturin develop --release,\n"
        "  hot-swapping the installed _native*.so. A cargo-check-only probe\n"
        "  (build=False) that SUCCEEDS also does not revert -- only a FAILURE\n"
        "  triggers rollback (domains/self_extend.py:extend). scripts/witness_\n"
        "  twoarg_gate.py and scripts/emitter_generalisation_gate.py both call it\n"
        "  live and restore by hand in a try/finally. Safe for one agent; not safe\n"
        "  while two concurrent agents depend on the installed extension staying put.\n\n"
        "  This driver uses domains/self_extend_rust.py instead: same agent-authored\n"
        "  spec, same mechanical transcriber, but sandboxed end to end -- never writes\n"
        "  to runners/dsl/src, never calls maturin, never touches an installed .so.")

    _print_header("2. THE AGENT'S SPEC")
    substrate = _boot_grounding_substrate()
    spec = ser.agent_specify_reachable_from_primitive(substrate)
    print(f"  name:               {spec['name']}")
    print(f"  semantics.kind:     {spec['semantics']['kind']}")
    print(f"  grounded_in_science:{spec['grounded_in_science']}")
    print(f"  purpose:            {spec['purpose']}")
    print(f"  why_new:            {spec['why_new']}")
    print(f"  motivating_residual:{spec['motivating_residual']}")
    print(f"  composition_attempt:{spec['semantics']['composition_attempt']}")
    print(f"  reduces_to:         {spec['semantics']['reduces_to']}")

    _print_header("3. RENDERED DIFF (sandbox copy only)")
    frags = ser.render_spec(spec)
    for key in sorted(frags):
        print(f"\n  --- {key} ---")
        for line in frags[key].splitlines():
            print(f"    {line}")

    _print_header("4. SANDBOX PIPELINE — apply, cargo check")
    before = ser.fingerprint_live_tree()
    t0 = time.time()
    result = ser.validate_spec(substrate, spec, scratch_dir=args.scratch)
    dt = time.time() - t0
    print(f"  ok:            {result['ok']}")
    print(f"  stage:         {result['stage']}")
    print(f"  returncode:    {result.get('returncode')}")
    print(f"  cargo seconds: {result.get('seconds')}")
    print(f"  wall seconds:  {dt:.1f}")
    print(f"  sandbox path:  {result.get('sandbox')}")
    print(f"  files touched: {result.get('files_touched')}")
    if not result["ok"]:
        print("\n  DIAGNOSTICS (the agent can read WHY this failed):")
        for line in str(result.get("diagnostics", ""))[:2000].splitlines():
            print(f"    {line}")

    _print_header("5. SANDBOX-INTEGRITY PROOF")
    problems = ser.assert_live_tree_untouched(before)
    print(f"  live tree + installed .so fingerprints checked: {len(before)}")
    print(f"  changed: {len(problems)}")
    if problems:
        print("  VIOLATIONS (should never happen):")
        for p in problems:
            print(f"    {p}")
    else:
        print("  CLEAN -- runners/dsl/src and every installed _native*.so are "
              "byte-identical to before this run.")

    _print_header("6. GRAPH-RESIDENT RECORD")
    specs = [n for n in substrate.nodes("RustExtensionSpec")
             if substrate.node(n)["attrs"].get("name") == spec["name"]]
    props = [n for n in substrate.nodes("ExtensionProposal")
             if substrate.node(n)["attrs"].get("of") == spec["name"]]
    if specs:
        print(f"  RustExtensionSpec #{specs[-1]}: {substrate.node(specs[-1])['attrs']}")
    if props:
        print(f"  ExtensionProposal #{props[-1]}: {substrate.node(props[-1])['attrs']}")

    print(RUNBOOK)
    if args.apply:
        print(">>> --apply was passed: this script STILL did not install anything.")
        print(">>> Follow the runbook above by hand; there is no automatic path.")

    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
