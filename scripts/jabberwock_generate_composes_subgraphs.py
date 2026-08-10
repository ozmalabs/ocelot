"""GENERATE-COMPOSES-SUBGRAPHS: the agent GROWS its own candidate term-space graph-natively. A rule mints a
new Term-subgraph by adding a Term.<Op> node whose child.<field> edges point at EXISTING candidate roots
(subgraph SHARING = library reuse by reference) — the term twin of GENERATE_LADDER (which mints coeff
candidates). Staged composition from the leaves {x, y} reaches absdiff:
  GEN_MINUS : mint Minus(x,y) and Minus(y,x)          (Term.Minus, child.a/child.b -> leaf roots)
  GEN_GTE   : mint Gte(x,y)                            (Term.Gte)
  GEN_ITE   : mint Ite(Gte(x,y), Minus(x,y), Minus(y,x)) = absdiff   (Term.IfThenElse, cond/then/other)
Then the ported SEARCH (per-candidate, EvalSubgraph on the example stream) GATES the one matching all
examples. Every step is a graph Rule; the agent generates AND searches its own term-space. donkey=0.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_generate_composes_subgraphs.py
"""
from __future__ import annotations
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds

def V(n): return {"type": "Var", "name": n}
def A(n, k): return {"type": "Attr", "node": V(n), "key": k}
def L(v): return {"type": "Lit", "value": v}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def And(*x): return {"type": "And", "items": list(x)}
def Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def Gte(a, b): return {"type": "Gte", "a": a, "b": b}
def Plus(*x): return {"type": "Plus", "items": list(x)}
def Ite(c, t, e): return {"type": "IfThenElse", "cond": c, "then": t, "other": e}
def Nb(n, et): return {"type": "Neighbours", "node": V(n), "edge_type": et}
def Pick(src): return {"type": "Pick", "source": src}
def Eval(node): return {"type": "EvalSubgraph", "node": node}

EXAMPLES = [(3, 0, 3), (0, 5, 5), (4, 4, 0), (2, 7, 5), (9, 1, 8)]   # absdiff(x,y)=|x-y|
N = float(len(EXAMPLES))

def cand(role, label):
    return {"role": role, "label": label, "mc": 0.0, "mframe": -1.0, "is_winner": 0.0}

# --- GENERATE rules: compose Term-subgraphs by pointing child.* edges at existing candidate roots ---
GEN_MINUS = {"id": "gen_minus", "name": "gen_minus",
    "match": [["lib", "has_cand", "cx"], ["cx", "has_term", "rx"], ["lib", "has_cand", "cy"], ["cy", "has_term", "ry"]],
    "where": And(Eq(A("cx", "role"), L("x")), Eq(A("cy", "role"), L("y")), Eq(A("lib", "genA"), L(0.0))),
    "effects": [
        ["add_node", "mxy", "Term.Minus", {}], ["add_edge", "mxy", "child.a", "rx"], ["add_edge", "mxy", "child.b", "ry"],
        ["add_node", "cmxy", "Candidate", cand("diff_xy", "x-y")], ["add_edge", "cmxy", "has_term", "mxy"], ["add_edge", "lib", "has_cand", "cmxy"],
        ["add_node", "myx", "Term.Minus", {}], ["add_edge", "myx", "child.a", "ry"], ["add_edge", "myx", "child.b", "rx"],
        ["add_node", "cmyx", "Candidate", cand("diff_yx", "y-x")], ["add_edge", "cmyx", "has_term", "myx"], ["add_edge", "lib", "has_cand", "cmyx"],
        ["set_attr", "lib", "genA", 1.0]]}

GEN_GTE = {"id": "gen_gte", "name": "gen_gte",
    "match": [["lib", "has_cand", "cx"], ["cx", "has_term", "rx"], ["lib", "has_cand", "cy"], ["cy", "has_term", "ry"]],
    "where": And(Eq(A("cx", "role"), L("x")), Eq(A("cy", "role"), L("y")), Eq(A("lib", "genB"), L(0.0))),
    "effects": [
        ["add_node", "g", "Term.Gte", {}], ["add_edge", "g", "child.a", "rx"], ["add_edge", "g", "child.b", "ry"],
        ["add_node", "cg", "Candidate", cand("cmp", "x>=y")], ["add_edge", "cg", "has_term", "g"], ["add_edge", "lib", "has_cand", "cg"],
        ["set_attr", "lib", "genB", 1.0]]}

GEN_ITE = {"id": "gen_ite", "name": "gen_ite",
    "match": [["lib", "has_cand", "cc"], ["cc", "has_term", "rc"],
              ["lib", "has_cand", "ct"], ["ct", "has_term", "rt"],
              ["lib", "has_cand", "ce"], ["ce", "has_term", "re"]],
    "where": And(Eq(A("cc", "role"), L("cmp")), Eq(A("ct", "role"), L("diff_xy")),
                 Eq(A("ce", "role"), L("diff_yx")), Eq(A("lib", "genC"), L(0.0))),
    "effects": [
        ["add_node", "it", "Term.IfThenElse", {}],
        ["add_edge", "it", "child.cond", "rc"], ["add_edge", "it", "child.then", "rt"], ["add_edge", "it", "child.other", "re"],
        ["add_node", "cabs", "Candidate", cand("absdiff", "ite(x>=y, x-y, y-x)")], ["add_edge", "cabs", "has_term", "it"], ["add_edge", "lib", "has_cand", "cabs"],
        ["set_attr", "lib", "genC", 1.0]]}

# --- SEARCH (parallel, per candidate): EvalSubgraph each candidate on the example; GATE the all-matcher ---
ACTIVE = Eval(Pick(Nb("cand", "has_term")))
MEASURE = {"id": "ts_measure", "name": "ts_measure",
    "match": [["h", "es_pred", "o"], ["lib", "has_cand", "cand"]],
    "where": Gt(A("o", "frame"), A("cand", "mframe")),
    "effects": [
        ["set_attr", "cand", "mc", {"__term__": Ite(Eq(ACTIVE, A("o", "expected")), Plus(A("cand", "mc"), L(1.0)), L(0.0))}],
        ["set_attr", "cand", "mframe", {"__term__": A("o", "frame")}]]}
GATE = {"id": "ts_gate", "name": "ts_gate",
    "match": [["lib", "has_cand", "cand"]],
    "where": And(Gte(A("cand", "mc"), L(N)), Eq(A("lib", "solved"), L(0.0))),
    "effects": [["set_attr", "lib", "solved", 1.0], ["set_attr", "cand", "is_winner", 1.0]]}


def main():
    a = WorldAdapter(seeds=()); load_all_seeds(a)
    donkey = {"n": 0}; a.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])
    s, I = a.s, a.inner

    print("=" * 94)
    print("GENERATE-COMPOSES-SUBGRAPHS — the agent grows its own term-space by composing Term-subgraphs (rules)")
    print("=" * 94)

    o = s.add_node("Observable", {"x": 0.0, "y": 0.0, "expected": 0.0, "frame": 0.0})
    hub = s.add_node("ObsHub", {}); I.add_edge_unchecked(hub, "es_pred", o)
    lib = s.add_node("CandLib", {"genA": 0.0, "genB": 0.0, "genC": 0.0, "solved": 0.0})
    # the ONLY seeds: the two leaves x, y (materialised Term-subgraphs). The agent composes the rest.
    for role in ("x", "y"):
        root = I.add_term_subgraph(A("o", role))
        c = s.add_node("Candidate", cand(role, role)); I.add_edge_unchecked(c, "has_term", root)
        I.add_edge_unchecked(lib, "has_cand", c)
    print("  seeded leaves: x, y   (the agent composes Minus/Gte/Ite subgraphs itself)")

    for r in (GEN_MINUS, GEN_GTE, GEN_ITE, MEASURE, GATE):
        I.add_rule(r)

    for step in range(1, 200):
        x, y, exp = EXAMPLES[(step - 1) % len(EXAMPLES)]
        I.set_attr(o, "x", float(x)); I.set_attr(o, "y", float(y))
        I.set_attr(o, "expected", float(exp)); I.set_attr(o, "frame", float(step))
        I.run_rules()
        if s.node(lib)["attrs"].get("solved") == 1.0:
            break

    cands = [s.node(c)["attrs"] for c in I.neighbours(lib, "has_cand")]
    composed = sorted(c.get("label") for c in cands if c.get("role") not in ("x", "y"))
    winner = next((c.get("label") for c in cands if c.get("is_winner") == 1.0), None)
    print(f"\n  the agent COMPOSED these Term-subgraphs from the leaves: {composed}")
    print(f"  the per-candidate graph-rule search GATED: {winner!r}")
    print("\n" + "=" * 94)
    print(f"  donkey (LLM calls): {donkey['n']}")
    ok = winner == "ite(x>=y, x-y, y-x)"
    print(f"  {'PASS' if ok else 'FAIL'} — GENERATE composed the candidate term-space graph-natively (Term.<Op> nodes")
    print("  with child.* edges into existing roots = subgraph sharing), and the SEARCH selected absdiff. The")
    print("  agent now generates AND searches its own term-space, in run_rules, donkey=0. Scaling deeper needs")
    print("  GUIDED generation (cost/typed steering) — the frontier the review named — not flat composition.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
