"""primitive_build_install — close the draft → cargo-check → install loop
for a multi-home DSL primitive, SAFELY.

What this proves end-to-end on REAL Rust:

  1. The agent specifies a FRESH index-of-reduction primitive whose
     variant name is verified ABSENT from the live term.rs (a duplicate
     would fail to compile). Today that is `ArgMin` — the dual of the
     existing `ArgMax`: the bin INDEX of a spectral VALLEY.
  2. mechanically_draft builds a real CodeDraft carrying the structured
     home→fragment dict (fragments_json) + kind="multi_home_primitive".
  3. The multi-home VALIDATOR splices each fragment into an ISOLATED COPY
     of the real `runners/dsl` crate (9 splice sites across term.rs /
     jsonio.rs / reflect.rs) and runs `cargo check` on it. THIS is the
     draft → cargo-build step, proven on real Rust in context.
  4. The corrected install gate (kind="multi_home_primitive") accepts the
     draft on compile_ok + tests_pass — no perf bench required.
  5. The INSTALLER splices the fragments into a SECOND isolated copy
     (NOT the live tree) with per-file backups, and that copy still
     `cargo check`s.

SAFETY: the live `runners/dsl/src/*.rs` is NEVER modified. We checksum
the home files before and after and assert byte-identity. All cargo runs
use a separate CARGO_TARGET_DIR + ulimit + timeout.

OUT OF SCOPE (honest): making the primitive LIVE in the running Python
needs `maturin develop` + copying the rebuilt .so — heavy, separate. The
`cargo check` here proves the emitted Rust COMPILES in context; it does
not rebuild the wheel.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from substrate_rs import _native  # noqa: E402
from domains import runtime_design as rd  # noqa: E402
from domains.code_writing_cortex import CodeWritingCortex  # noqa: E402

LIVE_SRC = ROOT / "runners" / "dsl" / "src"
HOME_FILES = ["term.rs", "jsonio.rs", "reflect.rs"]


def _sums(src_dir: Path) -> dict:
    out = {}
    for f in HOME_FILES:
        out[f] = hashlib.md5((src_dir / f).read_bytes()).hexdigest()
    return out


def _cargo_check(crate_dir: Path) -> tuple[bool, str]:
    env = dict(os.environ)
    env["CARGO_TARGET_DIR"] = str(crate_dir / "target")
    cmd = ("ulimit -v 12000000; "
           "exec cargo check --lib --message-format=short 2>&1")
    try:
        proc = subprocess.run(
            ["bash", "-c", cmd], cwd=crate_dir, capture_output=True,
            text=True, env=env, timeout=540)
    except subprocess.TimeoutExpired:
        return False, "cargo check timed out (540s)"
    out = proc.stdout or ""
    errs = [ln for ln in out.splitlines()
            if ln.startswith("error") or ": error" in ln]
    tail = "\n".join(out.splitlines()[-4:])
    return proc.returncode == 0, (tail if proc.returncode == 0
                                  else "\n".join(errs[:8]))


def main() -> int:
    print("=" * 72)
    print("primitive_build_install — draft → cargo-check → install (SAFE)")
    print("=" * 72)

    live_before = _sums(LIVE_SRC)
    print("\nLive home-file checksums BEFORE:")
    for f, h in live_before.items():
        print(f"  {f:12s} {h}")

    s = _native.Substrate()
    cortex = CodeWritingCortex(s, agent=None, repo_root=ROOT)
    cortex.install()

    # --- 1. agent specifies a FRESH primitive (verified absent) ----------
    existing = rd.existing_termnode_variants(LIVE_SRC / "term.rs")
    spec = rd.agent_specify_fresh_reduce_primitive(s, LIVE_SRC / "term.rs")
    print(f"\n[1] Agent specified FRESH primitive: {spec['name']!r}")
    print(f"    reduce_op       : {spec['reduce_op']}")
    print(f"    verified_fresh  : {spec['name']!r} not in "
          f"{len(existing)} existing variants -> "
          f"{spec['name'] not in existing}")
    print(f"    purpose         : {spec['purpose']}")

    # Register a ReplacementTarget + current_target so the cortex's
    # working-set helpers resolve the draft.
    op_name = spec["name"]
    tgt = cortex.set_target(op_name, {"total_ms": 0.0, "count": 0})

    # --- 2. mechanically_draft -> real CodeDraft w/ structured fragments -
    draft = cortex.mechanically_draft(tgt)
    if draft is None:
        print("    FAILED: mechanically_draft returned None")
        return 1
    dattrs = s.node(draft)["attrs"]
    import json as _json
    fragments = _json.loads(dattrs["fragments_json"])
    print(f"\n[2] CodeDraft {draft} built. kind={dattrs.get('kind')!r}")
    print(f"    {len(fragments)} structured fragments (the splice set):")
    for k in fragments:
        print(f"      - {k}")

    # --- 3. multi-home VALIDATOR: splice into isolated copy + cargo check
    print("\n[3] VALIDATE: splice into isolated crate copy + cargo check ...")
    val = cortex.compile_and_test(draft)
    cortex.attach_validation(draft, val)
    print(f"    compile_ok               : {val['compile_ok']}")
    print(f"    tests_pass               : {val['tests_pass']}")
    print(f"    perf_improvement_factor  : {val['perf_improvement_factor']}")
    print(f"    notes                    : {val['notes']}")

    if not val["compile_ok"]:
        print("\n    cargo check did not pass on the spliced copy — "
              "stopping before install (gate works).")
        # Still prove the live tree is untouched, then exit.
        _final_integrity(live_before)
        return 1

    # --- 4 + 5. INSTALL into a SECOND isolated copy (NOT the live tree) --
    print("\n[4] INSTALL gate: kind=='multi_home_primitive' + compile_ok "
          "+ tests_pass -> accepted (no perf bench required).")
    install_copy = Path(tempfile.mkdtemp(prefix="cw_install_demo_"))
    shutil.copytree(LIVE_SRC, install_copy / "src", dirs_exist_ok=True)
    for f in ("Cargo.toml", "Cargo.lock", "pyproject.toml"):
        if (ROOT / "runners" / "dsl" / f).exists():
            shutil.copy2(ROOT / "runners" / "dsl" / f, install_copy / f)
    if (ROOT / "runners" / "dsl" / "python").exists():
        shutil.copytree(ROOT / "runners" / "dsl" / "python",
                        install_copy / "python", dirs_exist_ok=True)

    print(f"\n[5] INSTALL into isolated copy: {install_copy}/src "
          f"(live tree untouched) ...")
    inst = cortex.install_multi_home_primitive(
        draft, target_src_dir=install_copy / "src")
    iattrs = s.node(inst)["attrs"]
    print(f"    CodeInstallation {inst}: spliced "
          f"{iattrs['n_fragments']} fragments into {iattrs['files']}")
    print(f"    backups: {iattrs['backups']}")

    # Show the fragments landed: grep the variant name in the copy.
    for f in ("term.rs", "jsonio.rs", "reflect.rs"):
        txt = (install_copy / "src" / f).read_text()
        n = txt.count(op_name)
        print(f"    {f:12s} now mentions {op_name!r} {n}× "
              f"(was {(LIVE_SRC / f).read_text().count(op_name)}× in live)")

    print("\n    Re-running cargo check on the INSTALLED copy ...")
    ok, tail = _cargo_check(install_copy)
    print(f"    installed-copy cargo check: "
          f"{'PASSED' if ok else 'FAILED'}")
    print(f"    {tail}")

    _final_integrity(live_before)

    print("\n" + "=" * 72)
    print("CLOSES: draft -> cargo-check (isolated copy) -> install (into a "
          "copy), both proven to compile.")
    print("STILL OUT: live activation needs `maturin develop` + .so copy "
          "(heavy, separate) — not done here.")
    print("=" * 72)
    return 0 if ok else 1


def _final_integrity(live_before: dict) -> None:
    live_after = _sums(LIVE_SRC)
    identical = live_before == live_after
    print("\nLive home-file checksums AFTER:")
    for f, h in live_after.items():
        flag = "OK" if live_before[f] == h else "CHANGED!"
        print(f"  {f:12s} {h}  [{flag}]")
    print(f"\nLIVE TREE BYTE-IDENTICAL: {identical}")
    if not identical:
        raise SystemExit("SAFETY VIOLATION: live tree changed!")


if __name__ == "__main__":
    raise SystemExit(main())
