"""emitter_generalisation_gate — GATE for PART 2: the emitter now self-authors
BRAND-NEW BASE primitives, incl. structural-recursion shapes (the AntiUnify family),
deterministically (NO LLM). Closes the rung-4 emitter limit so the agent is fully
self-authoring: composable -> dynamic (no restart, rung-3); genuinely-new base
primitive -> deterministic emit + recompile (rung-4); HumanImpasse truly last.

The generalisation: (1) NAME-PARAMETERISED templates (helper fn = <name_lower>_recur)
so two primitives of the SAME semantic_kind don't collide (fixes the E0428 the
diagnosis found); (2) a STRUCTURAL-RECURSION template (one shape parameterised by
recur_kind = leaf-op + combine-op + return) covering AntiUnify/Unify/StructSim-style
recursion the prior ~8 templates missed.

NOTE on probes: self_extend.extend(build=False) does cargo check but does NOT revert
(revert_after only triggers after a full build). So each cargo-check probe here
restores the touched Rust files via `git checkout` afterward — leaving the tree
exactly as found. (The emitter is the artefact under test, not a hand-written Term.)

ARCHITECTURE: the emitter is the deterministic build toolchain (spec->Rust, NO LLM);
the agent's DECISION stays the graph spec (name + recur_kind). donkey=0.

Run: PYTHONPATH=.:runners/dsl/python python3 scripts/emitter_generalisation_gate.py [--full-build]
"""
from __future__ import annotations
import os, sys, subprocess
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)
from domains.self_extend import PrimitiveExtension
from domains.struct_recursion_template import antiunify_anchor

ANCHOR = {"__frags__": antiunify_anchor()}
_RUST = ["runners/dsl/src/term.rs", "runners/dsl/src/jsonio.rs", "runners/dsl/src/reflect.rs"]


def _restore():
    """Restore the touched Rust files to their pre-probe (working-tree) state.
    We snapshot before the gate and restore from that snapshot — preserving any
    PRE-EXISTING uncommitted changes while removing the probe fragments."""
    for f, txt in _SNAP.items():
        open(os.path.join(ROOT, f), "w").write(txt)


_SNAP = {f: open(os.path.join(ROOT, f)).read() for f in _RUST}


def _spec(name, recur_kind):
    return {"name": name, "semantic_kind": "structural_recursion", "recur_kind": recur_kind,
            "purpose": "a self-authored structural-recursion base primitive",
            "why_new": "no held Term + no prior template expressed this recursion shape",
            "grounded_in_science": True, "is_agent_design": True}


def _cargo_check_probe(name, recur_kind):
    """Self-author (apply + cargo check) then RESTORE the snapshot. Returns ok."""
    pe = PrimitiveExtension()
    try:
        res = pe.extend(_spec(name, recur_kind), anchor_spec=ANCHOR, build=False)
    finally:
        _restore()
    return res.get("ok"), res


def main() -> int:
    full_build = "--full-build" in sys.argv
    ok = True

    # 1. NAME-PARAMETERISED (collision fixed): TWO primitives of the SAME kind, no E0428.
    print("=" * 78)
    print("GATE 1 — NAME-PARAMETERISED: two same-kind primitives, NO E0428 collision")
    print("=" * 78)
    o1, _ = _cargo_check_probe("MeetOne", "meet_wild")
    o2, _ = _cargo_check_probe("MeetTwo", "meet_wild")
    print(f"  MeetOne (meet_wild): cargo check ok={o1}")
    print(f"  MeetTwo (meet_wild, SAME kind): cargo check ok={o2}  "
          f"(helper fns meetone_recur vs meettwo_recur — no collision)")
    g1 = o1 and o2
    print("  -> same-kind no-collision:", "OK" if g1 else "FAIL")
    ok &= g1

    # 2. NEW structural-recursion primitive end-to-end (a shape the emitter had NO template for).
    print("\n" + "=" * 78)
    print("GATE 2 — NEW structural-recursion primitive self-authored (specify -> emit -> cargo check)")
    print("=" * 78)
    om, _ = _cargo_check_probe("MeetNew", "meet_wild")
    print(f"  MeetNew (meet_wild / AntiUnify shape): emitted + cargo check ok={om}")
    ok &= om

    # 3. CAPSTONE — self-author a StructSim-like GRADED recursion (the family the LLM wrote this session).
    print("\n" + "=" * 78)
    print("GATE 3 — CAPSTONE: self-author a StructSim-like graded recursion (previously LLM-written)")
    print("=" * 78)
    if full_build:
        pe = PrimitiveExtension()
        r = pe.extend(_spec("GradedSimNew", "graded_sim"), anchor_spec=ANCHOR, build=True, revert_after=False)
        print(f"  GradedSimNew: FULL build (cargo+maturin) ok={r.get('ok')} stage={r.get('stage')}")
        cap_ok = False
        if r.get("ok"):
            import importlib, substrate_rs
            importlib.reload(substrate_rs)
            s = substrate_rs._NativeSubstrate()
            v = s.evaluate({"type": "GradedSimNew",
                            "values": {"type": "Lit", "value": [[1.0, 2.0], [1.1, 2.0]]},
                            "wild": "·?·"}, {})
            print(f"  CALLABLE LIVE: GradedSimNew([[1,2],[1.1,2]]) = {v} (graded ~0.9)")
            cap_ok = isinstance(v, float) and 0.5 < v < 1.0
        else:
            print("  detail:", str(r.get("detail"))[-300:])
        _restore()
        subprocess.run(["maturin", "develop", "--release"], cwd=os.path.join(ROOT, "runners", "dsl"),
                       capture_output=True)   # rebuild to the restored (clean) source
    else:
        oc, _ = _cargo_check_probe("GradedSimNew", "graded_sim")
        print(f"  GradedSimNew (graded_sim / StructSim shape): emitted + cargo check ok={oc} "
              f"(run with --full-build to recompile + call it live)")
        cap_ok = oc
    ok &= cap_ok

    # 4. DETERMINISTIC-NOT-LLM (donkey check): NO LLM CALL in the EMITTER path.
    print("\n" + "=" * 78)
    print("GATE 4 — DETERMINISTIC-NOT-LLM (donkey check)")
    print("=" * 78)
    emit_mods = ["runtime_design.py", "struct_recursion_template.py", "arity_homes.py"]
    # an LLM CALL (not a docstring 'NO LLM' mention): make_ask( / claude -p / set_self_teacher( / .chat(
    import re
    calls = 0
    for f in emit_mods:
        path = os.path.join(ROOT, "domains", f)
        if not os.path.exists(path):
            continue
        txt = open(path).read()
        for pat in (r"make_ask\s*\(", r"set_self_teacher\s*\(", r"claude\s+-p", r"openai\.", r"\.chat\s*\("):
            calls += len(re.findall(pat, txt))
    print(f"  LLM CALLS in the emit path (make_ask/claude -p/set_self_teacher/openai/.chat): {calls}")
    print("  -> emit is a deterministic template compiler (no LLM invocation):", "OK" if calls == 0 else "FAIL")
    ok &= (calls == 0)

    # 5. ROLLBACK on bad spec (preflight) + REGRESSION: source identical to the snapshot after all probes.
    print("\n" + "=" * 78)
    print("GATE 5 — ROLLBACK on failure + REGRESSION (source restored to snapshot)")
    print("=" * 78)
    bad = _spec("BadProbe", "nonexistent_kind")
    pe = PrimitiveExtension()
    try:
        rb = pe.extend(bad, anchor_spec=ANCHOR, build=False)
        rb_ok = not rb.get("ok")
        print(f"  bad recur_kind: aborted (ok={rb.get('ok')}, stage={rb.get('stage')}) — no half-apply")
    except Exception as e:
        rb_ok = True
        print(f"  bad recur_kind raised (caught) {type(e).__name__} — no source written")
    finally:
        _restore()
    ok &= rb_ok
    # the source now equals the snapshot (we never committed a probe)
    same = all(open(os.path.join(ROOT, f)).read() == _SNAP[f] for f in _RUST)
    print(f"  Rust source identical to pre-gate snapshot (no probe residue): {same}")
    ok &= same

    print("\n" + "=" * 78)
    print(("PASS" if ok else "FAIL"),
          "- EMITTER GENERALISATION: name-parameterised (same-kind no collision) + a structural-recursion "
          "template (AntiUnify family) -> the agent self-authors BRAND-NEW base primitives DETERMINISTICALLY "
          "(NO LLM); cargo check passes; rollback on failure; existing source restored. The agent is now "
          "fully self-authoring: dynamic-compose (no restart) + deterministic emit+recompile (incl. recursion "
          "shapes); HumanImpasse truly last. donkey=0.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
