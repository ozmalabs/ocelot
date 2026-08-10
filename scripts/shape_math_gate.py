"""shape_math_gate — GATE for SHAPE MATH (the lattice dual of the held AntiUnify).

Shape math = operating ON shapes: the DIFFERENCE between shapes (decompose), and
APPLYING a difference ("this is like X but with Y" — construct). It is the JOIN
direction of the subsumption lattice whose MEET the agent already held as
AntiUnify. Two additive Rust DSL Terms supply it:

  • AntiUnifyWitness(values, wild) -> (template, sigmas)  — the MEET that RETAINS
    its witnesses: the template is the lgg, the sigmas are the DIFFERENCE.
  • Substitute(template, sigma, wild) -> term               — the JOIN: apply a
    witness ("X but with Y" = move down the lattice), the inverse structural walk.

ARCHITECTURE: the reasoning is the two Rust Terms; the shape-math composition is a
Term TREE (Let + AntiUnifyWitness + IndexAt + Substitute) run by the Rust
evaluator. Python here is only: build the Term JSON (ingest) and read the result
(emit). No Python orchestration, no verdict/decision-if over graph state.

Run: PYTHONPATH=.:runners/dsl/python python3 scripts/shape_math_gate.py
"""
from __future__ import annotations
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)
import substrate_rs as srs

# --- Term builders (mechanical JSON construction — not reasoning) ---
def L(v): return {"type": "Lit", "value": v}
def V(n): return {"type": "Var", "name": n}
def Let(n, val, body): return {"type": "Let", "name": n, "value": val, "body": body}
def IndexAt(seq, i): return {"type": "IndexAt", "seq": seq, "index": i}
def AUW(vals): return {"type": "AntiUnifyWitness", "values": vals, "wild": "·?·"}
def AU(vals): return {"type": "AntiUnify", "values": vals, "wild": "·?·"}
def SUB(t, sig): return {"type": "Substitute", "template": t, "sigma": sig, "wild": "·?·"}

def dom(*r): return list(r)
def norm(x):
    return [norm(i) for i in x] if isinstance(x, (list, tuple)) else x

# systematicity read-out: does a higher-order CAUSE system survive (predicate-
# bearing in every slot)? — reads the AntiUnify residue, no decision.
def has_system(res):
    return isinstance(res, tuple) and any(
        isinstance(r, tuple) and r and r[0] == "CAUSE"
        and all(isinstance(x, tuple) and x and x[0] != "·?·" for x in r[1:])
        for r in res)


def main() -> int:
    s = srs._NativeSubstrate()
    ev = s.evaluate

    solar = dom(["attracts", "C", "o"], ["revolves", "o", "C"], ["greater", "C", "o"],
                ["CAUSE", ["attracts", "C", "o"], ["revolves", "o", "C"]])
    atom = dom(["attracts", "N", "e"], ["revolves", "e", "N"], ["greater", "N", "e"],
               ["CAUSE", ["attracts", "N", "e"], ["revolves", "e", "N"]])
    billiards = dom(["collide", "a", "b"], ["greater", "a", "b"], ["transfer", "a", "b"])

    ok = True

    # 1. DECOMPOSE (vice versa)
    d = ev(AUW(L([solar, atom])), {})
    G, sig_solar, sig_atom = d[0], d[1][0], d[1][1]
    decompose_ok = has_system(G) and sig_atom and sig_solar != sig_atom
    print("[DECOMPOSE] AntiUnifyWitness(solar, atom):")
    print("   generic G keeps CAUSE-system:", has_system(G))
    print("   difference sigma_atom (sample):", dict(list(sig_atom.items())[:3]), "...")
    print("   sigma differs solar vs atom (the C,o->N,e delta):", sig_solar != sig_atom,
          "->", "OK" if decompose_ok else "FAIL")
    ok &= decompose_ok

    # 2. FORWARD "X but with Y" — ONE Term tree, Rust-run
    forward = Let("d", AUW(L([solar, atom])),
                  SUB(IndexAt(V("d"), L(0)),
                      IndexAt(IndexAt(V("d"), L(1)), L(1))))
    constructed = ev(forward, {})
    fwd_ok = norm(constructed) == norm(atom)
    print("[FORWARD] Substitute(AntiUnifyWitness(solar,atom).template, sigma_atom) == atom:",
          fwd_ok, "->", "OK" if fwd_ok else "FAIL")
    ok &= fwd_ok

    # 3. STRUCTURAL VALIDITY — real sigma re-anti-unifies clean; wrong sigma does not
    real = ev(forward, {})
    re_real = ev(AU(L([list(real), atom])), {})
    real_clean = has_system(re_real) and norm(re_real) == norm(atom)
    wrong = ev(Let("d", AUW(L([solar, billiards])),   # no shared system -> flat template
                   SUB(IndexAt(V("d"), L(0)), IndexAt(IndexAt(V("d"), L(1)), L(1)))), {})
    re_wrong = ev(AU(L([list(wrong), atom])), {})
    wrong_degrades = not has_system(re_wrong)
    valid_ok = real_clean and wrong_degrades
    print("[VALIDITY] real sigma re-anti-unifies CLEAN:", real_clean,
          "| wrong/flat sigma DEGRADES:", wrong_degrades, "->", "OK" if valid_ok else "FAIL")
    ok &= valid_ok

    # 4. MATCHING INTACT — additive Terms must not change AntiUnify
    m1 = has_system(ev(AU(L([solar, atom])), {}))
    m2 = not has_system(ev(AU(L([solar, billiards])), {}))
    match_ok = m1 and m2
    print("[MATCHING] solar~atom MATCH:", m1, "| solar~billiards NO:", m2,
          "->", "OK" if match_ok else "FAIL")
    ok &= match_ok

    print("=" * 72)
    print(("PASS" if ok else "FAIL"),
          "- SHAPE MATH: construct/decompose 'X but with Y' as the lattice dual of "
          "the held matcher; structural (re-anti-unification-validated), not flat; "
          "matching intact. Reasoning = the two Rust Terms composed as a Term tree; "
          "no Python orchestration; donkey=0 (no LLM in the loop).")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
