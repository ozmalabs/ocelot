"""Ask Jabberwock what L5 (reflective/meta) needs to compose.

L5 from the runner design (commit a64c7dc) is the reflective layer —
Γ representable as G subgraph, operations on Γ from within Π,
JIT codegen producing native code per kernel, OSR for deopt.

L1 + L2 have composition pattern Mts. L5 doesn't yet. This script
walks Jabberwock's vocabulary for L5-relevant primitives so the
pattern Mt can be composed from what's there rather than from my
assumptions.
"""
from __future__ import annotations

import importlib, inspect, re, sys
from pathlib import Path

sys.path.insert(0, "/home/matt/ozma/internal/research/experiments/gamma-substrate")

from substrate_rs import _native


def fresh_substrate():
    s = _native.Substrate()
    for st in ("Microtheory","Concept","Rule","PaperAxiom"):
        for tt in ("Microtheory","Concept","Rule","PaperAxiom"):
            for et in ("has_concept","has_rule","genlMt"):
                try: s.add_production({'src':{'type':st,'var':'s'},'edge_type':et,'tgt':{'type':tt,'var':'t'},'where':None,'weight':{'type':'Lit','value':1.0},'provenance':'l5'})
                except: pass
    return s


def install_all(s):
    dd = Path(__file__).resolve().parent.parent / "domains"
    for f in sorted(dd.glob("*.py")):
        if f.name.startswith("__"): continue
        src = f.read_text()
        for m in re.finditer(r"^def (install_\w+_seed)\(", src, re.MULTILINE):
            try:
                mod = importlib.import_module(f"domains.{f.stem}")
                fn = getattr(mod, m.group(1))
                pos = [p for p in inspect.signature(fn).parameters.values()
                       if p.kind in (inspect.Parameter.POSITIONAL_ONLY,
                                     inspect.Parameter.POSITIONAL_OR_KEYWORD)
                       and p.default is inspect.Parameter.empty]
                if len(pos) == 1:
                    fn(s)
            except: continue
    try:
        from domains.paper_reader import install_paper1_as_theory
        install_paper1_as_theory(s)
    except: pass


def find_in_mt(s, mt_name, keywords, max_results=20):
    mt = None
    for m in s.nodes("Microtheory"):
        if str(s.node(m)["attrs"].get("name","")).lower() == mt_name:
            mt = m
            break
    if mt is None: return []
    out = []
    for c in s.neighbours(mt, "has_concept"):
        a = s.node(c)["attrs"]
        text = (str(a.get("name","")) + " " + str(a.get("definition",""))).lower()
        hits = sum(1 for k in keywords if k in text)
        if hits >= 1:
            out.append({"name": str(a.get("name","")), "hits": hits})
    out.sort(key=lambda x: -x["hits"])
    return out[:max_results]


def main():
    s = fresh_substrate()
    install_all(s)

    print("=" * 72)
    print("L5 (REFLECTIVE/META) — primitives in Jabberwock's vocabulary")
    print("=" * 72)
    print()

    queries = [
        ("Γ-as-data + introspection", "reflection_metaprogramming",
         {"grammar","data","reflection","reflective","introspection",
          "intercession","metaobject","tower","quote","eval","homoicon",
          "self_mod"}),
        ("Codegen + JIT machinery", "compilers",
         {"jit","codegen","tier","trace","method","compile","ir","ssa",
          "dynasm","cranelift","backend","cabac","inline","speculation"}),
        ("Safepoints + OSR (compilers)", "compilers",
         {"safepoint","osr","deopt","stack_walk","frame","patch"}),
        ("Meta-circular interpretation", "compilers",
         {"meta","interpreter","tracing","circular"}),
        ("Foundational reflection (axiom 3 reference)", "reflection_metaprogramming",
         {"axiom","compound_loop","fixed_point","y_combinator","quine"}),
    ]
    for label, mt, kws in queries:
        print(f"  {label} (from {mt}):")
        results = find_in_mt(s, mt, kws)
        for r in results[:10]:
            print(f"    · {r['name']}")
        print()


if __name__ == "__main__":
    main()
