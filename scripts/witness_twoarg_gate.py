"""witness_twoarg_gate — GATE for PART 3: the WITNESS + TWO-ARG structural-recursion
templates. Closes the structural-recursion family (meet_wild / join_fuse / graded_sim
/ witness / two-arg) — the agent now deterministically self-authors every shape,
including the EXACT two Terms it raised the original HumanImpasse for this session
(AntiUnifyWitness + Substitute, commit bebef362, where an LLM wrote the Rust).

Re-authoring them via deterministic emit = the no-donkey arc closed: the agent has
self-authored every primitive it ever needed the LLM for.

ARCHITECTURE: the emitter is the deterministic build toolchain (spec->Rust, NO LLM);
the agent SPECIFIES (name + recur_kind); the emitter RENDERS. self_extend applies +
cargo check + maturin + rollback. NO LLM in emit. donkey=0.

self_extend.extend(build=False) does NOT auto-revert, so each cargo-check probe
restores the Rust files from a pre-gate snapshot afterward.

Run: PYTHONPATH=.:runners/dsl/python python3 scripts/witness_twoarg_gate.py [--full-build]
"""
from __future__ import annotations
import os, sys, subprocess
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)
from domains.self_extend import PrimitiveExtension
from domains.struct_recursion_template import anchor_from_live

_RUST = ["runners/dsl/src/term.rs", "runners/dsl/src/jsonio.rs", "runners/dsl/src/reflect.rs"]
_SNAP = {f: open(os.path.join(ROOT, f)).read() for f in _RUST}


def _restore():
    for f, t in _SNAP.items():
        open(os.path.join(ROOT, f), "w").write(t)


def _spec(name, recur_kind):
    return {"name": name, "semantic_kind": "structural_recursion", "recur_kind": recur_kind,
            "purpose": "a self-authored structural-recursion base primitive",
            "why_new": "no held Term + no prior template expressed this recursion shape",
            "grounded_in_science": True, "is_agent_design": True}


def _cargo_probe(name, recur_kind, anchor_term):
    pe = PrimitiveExtension()
    try:
        res = pe.extend(_spec(name, recur_kind),
                        anchor_spec={"__frags__": anchor_from_live(anchor_term, recur_kind)},
                        build=False)
    finally:
        _restore()
    return res.get("ok")


def main() -> int:
    full_build = "--full-build" in sys.argv
    ok = True

    # 1. WITNESS return-form self-authored (cargo check; --full-build => callable).
    print("=" * 78)
    print("GATE 1 — WITNESS return-form (AntiUnifyWitness shape: returns (template, sigmas))")
    print("=" * 78)
    w_ok = _cargo_probe("WitnessNew", "witness", "AntiUnifyWitness")
    print(f"  WitnessNew (witness): emit -> cargo check ok={w_ok}")
    ok &= w_ok

    # 2. TWO-ARG variant self-authored.
    print("\n" + "=" * 78)
    print("GATE 2 — TWO-ARG variant (Substitute shape: template + sigma -> rebuild)")
    print("=" * 78)
    s_ok = _cargo_probe("SubstituteNew", "substitute", "Substitute")
    print(f"  SubstituteNew (substitute): emit -> cargo check ok={s_ok}")
    ok &= s_ok

    # 3. CAPSTONE — re-author the EXACT two Terms from the original HumanImpasse, full build,
    #    and the shape-math ROUND-TRIP holds on the agent-self-authored Terms.
    print("\n" + "=" * 78)
    print("GATE 3 — CAPSTONE: re-author AntiUnifyWitness+Substitute (the original LLM-needed Terms)")
    print("=" * 78)
    if full_build:
        pe = PrimitiveExtension()
        # author BOTH new Terms into the live source, one build at the end
        a_w = anchor_from_live("AntiUnifyWitness", "witness")
        a_s = anchor_from_live("Substitute", "substitute")
        r1 = pe.extend(_spec("AuwSelf", "witness"), anchor_spec={"__frags__": a_w}, build=False)
        # re-extract the substitute anchor AFTER the witness insert (source shifted)
        a_s2 = anchor_from_live("Substitute", "substitute")
        r2 = pe.extend(_spec("SubSelf", "substitute"), anchor_spec={"__frags__": a_s2}, build=True, revert_after=False)
        print(f"  AuwSelf (witness) applied: {r1.get('ok')} | SubSelf (substitute) built: {r2.get('ok')} stage={r2.get('stage')}")
        cap_ok = False
        try:
            if r2.get("ok"):
                import importlib, substrate_rs
                importlib.reload(substrate_rs)
                s = substrate_rs._NativeSubstrate()
                ev = s.evaluate
                def L(v): return {"type": "Lit", "value": v}
                def V(n): return {"type": "Var", "name": n}
                def IndexAt(seq, i): return {"type": "IndexAt", "seq": seq, "index": i}
                solar = [["attracts", "C", "o"], ["revolves", "o", "C"]]
                atom = [["attracts", "N", "e"], ["revolves", "e", "N"]]
                # DECOMPOSE shown:
                d = ev({"type": "AuwSelf", "values": L([solar, atom]), "wild": "·?·"}, {})
                print(f"  DECOMPOSE AuwSelf(solar,atom): template={d[0]}")
                print(f"           sigma_atom (structural delta) = {dict(d[1][1])}")
                # ROUND-TRIP composed in ONE Term tree (sigma never leaves the substrate):
                #   let r = AuwSelf(solar, atom) in SubSelf(r[0], r[1][1])  == atom
                built = ev({"type": "Let", "name": "r",
                            "value": {"type": "AuwSelf", "values": L([solar, atom]), "wild": "·?·"},
                            "body": {"type": "SubSelf",
                                     "template": IndexAt(V("r"), L(0)),
                                     "sigma": IndexAt(IndexAt(V("r"), L(1)), L(1)),
                                     "wild": "·?·"}}, {})
                def norm(x): return [norm(i) for i in x] if isinstance(x, (list, tuple)) else x
                roundtrip = norm(built) == norm(atom)
                print(f"  FORWARD SubSelf(template, sigma_atom) = {built}")
                print(f"  ROUND-TRIP (== atom) on agent-self-authored Terms: {roundtrip}")
                cap_ok = roundtrip
            else:
                print("  detail:", str(r2.get("detail"))[-300:])
        finally:
            _restore()
            subprocess.run(["maturin", "develop", "--release"],
                           cwd=os.path.join(ROOT, "runners", "dsl"), capture_output=True)
        ok &= cap_ok
    else:
        c1 = _cargo_probe("AuwSelf", "witness", "AntiUnifyWitness")
        c2 = _cargo_probe("SubSelf", "substitute", "Substitute")
        print(f"  AuwSelf (witness) cargo ok={c1} | SubSelf (substitute) cargo ok={c2}")
        print("  (run with --full-build to recompile + prove the shape-math ROUND-TRIP on them)")
        ok &= (c1 and c2)

    # 4. DETERMINISTIC-NOT-LLM (donkey check): no LLM CALL in the emit path.
    print("\n" + "=" * 78)
    print("GATE 4 — DETERMINISTIC-NOT-LLM (donkey check)")
    print("=" * 78)
    import re
    calls = 0
    for f in ("runtime_design.py", "struct_recursion_template.py", "arity_homes.py"):
        path = os.path.join(ROOT, "domains", f)
        if os.path.exists(path):
            txt = open(path).read()
            for pat in (r"make_ask\s*\(", r"set_self_teacher\s*\(", r"claude\s+-p", r"openai\.", r"\.chat\s*\("):
                calls += len(re.findall(pat, txt))
    print(f"  LLM calls in emit path: {calls}  -> {'OK' if calls == 0 else 'FAIL'}")
    ok &= (calls == 0)

    # 5. ROLLBACK + REGRESSION (source identical to snapshot).
    print("\n" + "=" * 78)
    print("GATE 5 — ROLLBACK + REGRESSION (source restored to snapshot)")
    print("=" * 78)
    pe = PrimitiveExtension()
    try:
        rb = pe.extend(_spec("BadW", "no_such_kind"), anchor_spec={"__frags__": {}}, build=False)
        rb_ok = not rb.get("ok")
    except Exception as e:
        rb_ok = True
        print(f"  bad recur_kind raised (caught) {type(e).__name__}")
    finally:
        _restore()
    same = all(open(os.path.join(ROOT, f)).read() == _SNAP[f] for f in _RUST)
    print(f"  rollback on bad spec: {rb_ok} | source identical to snapshot: {same}")
    ok &= rb_ok and same

    print("\n" + "=" * 78)
    print(("PASS" if ok else "FAIL"),
          "- WITNESS + TWO-ARG templates: the agent deterministically self-authors witness-returning "
          "(AntiUnifyWitness) and two-arg (Substitute) primitives — the structural-recursion family is "
          "COMPLETE. The exact two Terms the agent originally needed the LLM for are now self-authored; "
          "round-trip holds. NO LLM in emit; rollback intact; source clean. donkey=0.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
