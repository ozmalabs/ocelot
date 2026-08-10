"""shape_blend_gate — GATE for the BLEND (Unify / amalgam), the constructive DUAL
of AntiUnify, completing the shape-math algebra.

AntiUnify is the lattice MEET (abstract UP to the shared generic, WILDing
differences). Unify is the JOIN (combine DOWN to the most general specialisation
consistent with all) — the Fauconnier-Turner conceptual blend / Ontañón-Plaza
amalgam over the generic AntiUnify computes:
  • agreements kept (shared generic) • WILD holes filled from the concrete side
    (selective projection) • Dicts unified over the union of keys, Tuples
    element-wise, Sets unioned (EMERGENT structure in neither input alone)
  • genuine CONFLICT fused into a frozenset {a,b,…} — carries BOTH, SURFACES the
    conflict (a singleton/scalar ⇒ consistent; multi-member ⇒ conflict made
    explicit; never a silent drop).

ARCHITECTURE: the reasoning is the Rust Term `Unify` (+ held AntiUnify / Covers /
AntiUnifyWitness / Substitute); the composition is a Term-tree run by the Rust
evaluator (Let binds the blend, re-anti-unification validates it). Python only
builds the Term JSON and reads the result — no orchestration, no verdict/decision.

Run: PYTHONPATH=.:runners/dsl/python python3 scripts/shape_blend_gate.py
"""
from __future__ import annotations
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)
import substrate_rs as srs

def L(v): return {"type": "Lit", "value": v}
def V(n): return {"type": "Var", "name": n}
def Let(n, val, body): return {"type": "Let", "name": n, "value": val, "body": body}
def Vec(*items): return {"type": "Vec", "items": list(items)}
def UNI(vals): return {"type": "Unify", "values": vals, "wild": "·?·"}
def AU(vals): return {"type": "AntiUnify", "values": vals, "wild": "·?·"}
def AUW(vals): return {"type": "AntiUnifyWitness", "values": vals, "wild": "·?·"}
def SUB(t, sig): return {"type": "Substitute", "template": t, "sigma": sig, "wild": "·?·"}
def IndexAt(seq, i): return {"type": "IndexAt", "seq": seq, "index": i}

def dom(*r): return list(r)
def norm(x): return [norm(i) for i in x] if isinstance(x, (list, tuple)) else x
def keeps_struct(x): return isinstance(x, tuple) and len(x) and x[0] == "STRUCT"
def has_fused(x):
    if isinstance(x, frozenset) and len(x) > 1: return True
    if isinstance(x, (list, tuple)): return any(has_fused(i) for i in x)
    return False
def has_system(res):
    return isinstance(res, tuple) and any(
        isinstance(r, tuple) and r and r[0] == "CAUSE"
        and all(isinstance(x, tuple) and x and x[0] != "·?·" for x in r[1:]) for r in res)


def main() -> int:
    s = srs._NativeSubstrate()
    ev = s.evaluate
    ok = True

    house = ["STRUCT", ["function", "dwell"], ["location", "land"], ["occupant", "family"], ["rooms", "many"]]
    boat = ["STRUCT", ["function", "travel"], ["location", "water"], ["occupant", "crew"], ["hull", "floats"]]

    # 1. BLEND carries BOTH + EMERGENT + consistency handled
    blend = ev(UNI(L([house, boat])), {})
    flat = str(blend)
    keeps_generic = blend[0] == "STRUCT" and "function" in flat and "location" in flat
    emergent = all(k in flat for k in ("rooms", "many", "hull", "floats"))  # each input's own slot
    carries_both = all(k in flat for k in ("dwell", "travel", "land", "water", "family", "crew"))
    conflict_surfaced = has_fused(blend)
    blend_ok = keeps_generic and emergent and carries_both and conflict_surfaced
    print("[BLEND] Unify(house, boat) =")
    print("       ", blend)
    print("   keeps shared generic:", keeps_generic, "| emergent (both inputs' own slots):", emergent)
    print("   carries BOTH conflicting residuals:", carries_both, "| conflict SURFACED (fused):",
          conflict_surfaced, "->", "OK" if blend_ok else "FAIL")
    ok &= blend_ok

    # 2. VALIDITY: blend re-anti-unifies to the shared generic G with EACH input
    re_h = ev(Let("b", UNI(L([house, boat])), AU(Vec(V("b"), L(house)))), {})
    re_b = ev(Let("b", UNI(L([house, boat])), AU(Vec(V("b"), L(boat)))), {})
    valid_ok = keeps_struct(re_h) and keeps_struct(re_b)
    print("[VALIDITY] re-AntiUnify(blend, house) & (blend, boat) recover STRUCT generic:",
          valid_ok, "->", "OK" if valid_ok else "FAIL")
    ok &= valid_ok

    # 3. CONSISTENCY: agreeing inputs DON'T fuse the agreed slot (singleton ⇒ consistent)
    hA = ["STRUCT", ["function", "dwell"], ["rooms", "many"]]
    hB = ["STRUCT", ["function", "dwell"], ["garden", "big"]]
    cons = ev(UNI(L([hA, hB])), {})
    # the agreed slot 'function' stays the scalar 'dwell' (no spurious multi-member fusion there)
    func_slot = next((e for e in cons if isinstance(e, tuple) and e and e[0] == "function"), None)
    cons_ok = func_slot is not None and func_slot[1] == "dwell"
    print("[CONSISTENCY] agreeing inputs keep the agreed slot scalar (function='dwell', not fused):",
          cons_ok, "->", "OK" if cons_ok else "FAIL")
    ok &= cons_ok

    # 4. REGRESSION: forward / decompose / matching intact
    solar = dom(["attracts", "C", "o"], ["revolves", "o", "C"], ["greater", "C", "o"],
                ["CAUSE", ["attracts", "C", "o"], ["revolves", "o", "C"]])
    atom = dom(["attracts", "N", "e"], ["revolves", "e", "N"], ["greater", "N", "e"],
               ["CAUSE", ["attracts", "N", "e"], ["revolves", "e", "N"]])
    billiards = dom(["collide", "a", "b"], ["greater", "a", "b"], ["transfer", "a", "b"])
    fwd = ev(Let("d", AUW(L([solar, atom])),
                 SUB(IndexAt(V("d"), L(0)), IndexAt(IndexAt(V("d"), L(1)), L(1)))), {})
    reg_ok = (norm(fwd) == norm(atom)
              and has_system(ev(AU(L([solar, atom])), {}))
              and not has_system(ev(AU(L([solar, billiards])), {})))
    print("[REGRESSION] forward 'X but with Y' + decompose + matching (solar~atom MATCH, "
          "solar~billiards NO):", reg_ok, "->", "OK" if reg_ok else "FAIL")
    ok &= reg_ok

    print("=" * 74)
    print(("PASS" if ok else "FAIL"),
          "- BLEND (Unify/amalgam): combines two inputs over their shared generic — keeps "
          "the generic, selectively projects both residuals (emergent structure), and FUSES "
          "conflicts (carries both, surfaces the conflict). Validity by re-anti-unification; "
          "consistency handled (agree⇒scalar, conflict⇒fused-set); regressions intact. "
          "Reasoning = the Rust Unify Term composed as a Term tree; no Python orchestration; donkey=0.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
