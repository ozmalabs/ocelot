"""The agent draws from VAGUELY similar concepts: it abstracts the structural shape
of concepts across ALL its domains and TRANSFERS them into the speech problem.
"""
import os
import sys
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate_rs import (Substrate, Gt, Minus, Div, Max, And, Attr, Lit, Var)
from domains.analogy import abstract_patterns, generate_by_transfer


def _render(d):
    if not isinstance(d, dict):
        return str(d)
    ty = d.get("type")
    if ty == "Attr":
        return d["key"]
    if ty == "Lit":
        return str(d["value"])
    if ty == "Var":
        return d["name"]
    if ty in ("Gt", "Lt", "Div", "Minus", "Eq"):
        op = {"Gt": ">", "Lt": "<", "Div": "/", "Minus": "-", "Eq": "="}[ty]
        return f"({_render(d['a'])} {op} {_render(d['b'])})"
    if ty in ("And", "Or", "Max", "Min", "Plus"):
        items = list(d["items"])
        sep = {"And": " & ", "Or": " | ", "Plus": " + "}.get(ty)
        if sep:
            return "(" + sep.join(_render(i) for i in items) + ")"
        return f"{ty.lower()}(" + ", ".join(_render(i) for i in items) + ")"
    return ty


def main():
    s = Substrate()
    V = Var("s")

    def add(name, origin, term):
        s.add_node("Concept", {"name": name, "origin": origin,
                               "predicate": term.to_dict()})

    # The agent's cross-domain concepts — its BREADTH. In the full agent these come
    # from its vision / physics / chess / phonology seeds; each is a Term-tree.
    add("center_surround", "vision",
        Gt(a=Minus(a=Attr(V, "center"), b=Attr(V, "surround")), b=Lit(0.1)))
    add("scale_invariant_ratio", "physics",
        Gt(a=Div(a=Attr(V, "force"), b=Attr(V, "area")), b=Lit(1.0)))
    add("dominates_neighbours", "chess",
        Gt(a=Attr(V, "x"), b=Max(items=(Attr(V, "y"), Attr(V, "z")))))
    add("local_peak", "phonology",
        And(items=(Gt(a=Attr(V, "b"), b=Attr(V, "l")),
                   Gt(a=Attr(V, "b"), b=Attr(V, "r")))))

    pats = abstract_patterns(s)
    print("the agent abstracts the SHAPE of concepts across ALL its domains")
    print("(hollowing out the domain-specific operands, keeping the form):\n")
    for name, origin, skel in pats:
        print(f"   {origin:>9}:{name:<22} -> shape  {_render(skel)}")

    print("\nnow it TRANSFERS those shapes into SPEECH — drawing ideas from")
    print("vaguely-similar concepts instead of generating blindly:\n")
    bands = [f"band12_{i}" for i in range(12)]
    rng = random.Random(3)
    for _ in range(8):
        name, origin, term = generate_by_transfer(pats, bands, rng)
        print(f"   drew from {origin}:{name:<22} ->  {_render(term)}")

    print("\n  A 'center_surround' from VISION becomes a speech spectral contrast;")
    print("  a 'scale_invariant_ratio' from PHYSICS becomes a formant ratio. The")
    print("  agent's breadth seeds its generation; the compression selector then")
    print("  keeps the transfers that generalise.")


if __name__ == "__main__":
    main()
