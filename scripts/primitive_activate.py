"""LIVE ACTIVATION — the agent authors a primitive AND makes it callable.

The full self-extension loop end to end, for real, on the LIVE runtime:
  specify (fresh ArgMin) -> mechanically_draft -> validate (cargo check, isolated
  copy) -> install into the LIVE runners/dsl/src (with backups) -> ACTIVATE
  (maturin develop + .so sync) -> VERIFY the primitive is callable in a fresh
  Python process. Any failure rolls the live tree back byte-for-byte.

This is the heavy, deliberate step: it rebuilds the shared wheel. No LLM — the
agent specified the primitive from its own science; the mechanical emitter wrote
the Rust; maturin builds it; the new primitive computes.

  run:  python scripts/primitive_activate.py
"""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
LIVE_SRC = ROOT / "runners" / "dsl" / "src"

from substrate_rs import _native
from domains import runtime_design as rd
from domains.code_writing_cortex import CodeWritingCortex

# ArgMin{items} is the dual of the existing ArgMax{items}: index of the MIN.
VERIFY_TERM = {"type": "ArgMin", "items": [
    {"type": "Lit", "value": 3.0},
    {"type": "Lit", "value": 9.0},
    {"type": "Lit", "value": 1.0},
]}
VERIFY_EXPECT = 2   # min 1.0 is at index 2


def _verify_in_fresh_process() -> tuple[bool, str]:
    """Evaluate an ArgMin term in a FRESH python (loads the rebuilt .so)."""
    code = (
        "import substrate_rs._native as n; s=n.Substrate(); "
        f"print(s.evaluate({json.dumps(VERIFY_TERM)}))"
    )
    p = subprocess.run([sys.executable, "-c", code],
                       capture_output=True, text=True, timeout=120)
    out = (p.stdout or "").strip()
    if p.returncode != 0:
        return False, (p.stderr or "")[-400:]
    return out == str(VERIFY_EXPECT), f"evaluated -> {out!r} (expect {VERIFY_EXPECT})"


def _rule(t):
    print("\n" + "=" * 70 + f"\n{t}\n" + "=" * 70)


def main() -> int:
    s = _native.Substrate()
    cortex = CodeWritingCortex(s, agent=None, repo_root=ROOT)
    cortex.install()

    _rule("1. SPECIFY + DRAFT (agent composes its own Rust, no LLM)")
    spec = rd.agent_specify_fresh_reduce_primitive(s, LIVE_SRC / "term.rs")
    op = spec["name"]
    print(f"  fresh primitive: {op!r} ({spec['reduce_op']}) — {spec['purpose']}")
    tgt = cortex.set_target(op, {"total_ms": 0.0, "count": 0})
    draft = cortex.mechanically_draft(tgt)
    if draft is None:
        print("  FAILED: no draft"); return 1
    frags = json.loads(s.node(draft)["attrs"]["fragments_json"])
    print(f"  drafted {len(frags)} splice fragments")

    _rule("2. VALIDATE (cargo check on an isolated copy)")
    val = cortex.compile_and_test(draft)
    cortex.attach_validation(draft, val)
    print(f"  compile_ok={val['compile_ok']}  notes={val.get('notes','')[:80]}")
    if not val["compile_ok"]:
        print("  cargo check failed on the copy — NOT touching the live tree.")
        return 1

    _rule("3. INSTALL into the LIVE tree (with per-file backups)")
    inst = cortex.install_multi_home_primitive(draft)  # target_src_dir=None -> live
    iattrs = s.node(inst)["attrs"]
    print(f"  spliced {iattrs['n_fragments']} fragments into {iattrs['files']}")
    backups = json.loads(iattrs.get("backups", "{}"))
    print(f"  backups: {list(backups.values())}")

    try:
        _rule("4. ACTIVATE (maturin develop — rebuild the live extension)")
        print("  building (this is the heavy step) ...", flush=True)
        act = cortex.activate_installed_primitive(inst, timeout_s=900)
        print(f"  built={act['built']}  so_synced={act.get('so_synced')}")
        if not act["built"]:
            print("  BUILD FAILED:\n" + act["stderr_tail"])
            raise RuntimeError("build failed")

        _rule("5. VERIFY (call ArgMin in a fresh process on the rebuilt .so)")
        ok, detail = _verify_in_fresh_process()
        print(f"  {detail}")
        if not ok:
            raise RuntimeError("verification failed")
        print("\n  ✓ ArgMin is LIVE — the agent authored a primitive and it "
              "computes.")
    except Exception as exc:
        _rule("ROLLBACK (restoring the live tree byte-for-byte)")
        restored = cortex.rollback_install(inst)
        print(f"  restored {restored} from backup; reason: {exc}")
        print("  NOTE: the live .so may need a rebuild to drop the (reverted) "
              "primitive; the SOURCE tree is back to its original state.")
        return 1

    # success: drop the now-redundant backups (git history is the real backup)
    for b in backups.values():
        try:
            Path(b).unlink()
        except Exception:
            pass
    _rule("DONE — draft -> validate -> install -> ACTIVATE -> callable")
    print(f"  {op}{{items}} now lives in the runtime and is callable from "
          f"Python. Live activation closed.")
    print("  honest: the live .so was rebuilt (maturin develop); the source "
          "changes to term.rs/jsonio.rs/reflect.rs are real + committable.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
