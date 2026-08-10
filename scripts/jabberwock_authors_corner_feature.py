"""The jabberwock authors the CONVEX-CORNER feature — the polygon-defining property the
shape library exposed as missing — and appends it, then rebuilds the library so the
colliding shapes (triangle vs T, cross vs diamond) separate.
(Creator: "have it author the corner feature and add it.")

A convex corner is a 2x2 window with exactly 1 filled cell — and each such window is OWNED
by its single filled cell, so it counts per cell (no empty positions to iterate, same
machinery as the Euler characteristic). C1 = Σ over cells of the 4 corner-windows whose
other 3 cells are empty. Rotation-invariant, scale-robust, and it tells a triangle (3-ish
corners) from a T, a cross from a diamond. Appended as a new descriptor dimension; the
library prototypes are recomputed; naming gets sharper.
"""
from __future__ import annotations
import json, os, re, sys, math
os.environ.setdefault("ARC3_THIN", "1")
sys.path.insert(0, "."); sys.path.insert(0, "scripts")
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from scripts.claude_teacher import make_ask
from scripts.jabberwock_builds_shape_library import LIB

SENSE = "seeds/shape_sense.json"
LIBSEED = "seeds/shape_library.json"

PRIMS = """DSL forms (JSON):
  Var{name} Lit{value} Attr{node,key}("row"/"col")
  InNeighbours{node:Var x, edge_type:"within"}                  the figure's cells
  Sum{source,var_name:"c",value:<expr in c>}                    Σ over cells
  Exists{source,var_name:"c2",predicate:<bool in c2 and outer c>}
  Not{arg}  And{items:[..]}  Eq{a,b}  IfThenElse{cond,then,other}
  Plus{items:[..]} Minus{a,b}"""

Q = """Author `convex_corners` over a figure "x": the count of CONVEX corners = the number of 2x2
windows containing exactly ONE filled cell. Each such window is owned by its single filled cell, so
count PER CELL c (no empty positions to iterate). For cell c at (row,col), with its 8 neighbours
  up=(row-1,col) down=(row+1,col) left=(row,col-1) right=(row,col+1)
  ul=(row-1,col-1) ur=(row-1,col+1) dl=(row+1,col-1) dr=(row+1,col+1),
add 1 for each of c's 4 corner-windows whose OTHER 3 cells are EMPTY:
  window1: ul, up, left  all empty
  window2: up, ur, right all empty
  window3: left, dl, down all empty
  window4: right, dr, down all empty
"a cell exists at (R,K)" = Exists over the cells of a c2 with Eq(Attr(c2,"row"),R) and Eq(Attr(c2,"col"),K),
R/K built from c with Plus/Minus/Attr; "empty" = Not(that Exists). Each window -> IfThenElse(And([
Not(ex), Not(ex), Not(ex)]), Lit 1, Lit 0). convex_corners = Sum over cells of (window1+window2+window3+window4).

{prims}

Output ONLY the JSON term between markers:
@@@term
<json>
@@@end{err}"""

EXPECT = {"square": 4, "triangle": 7, "diamond": 12, "cross": 8, "T_shape": 6, "L_shape": 5}


def run(max_repair=3):
    agent = WorldAdapter(seeds=()); load_all_seeds(agent)

    def fig(cells):
        f = agent.s.add_node("Figure", {})
        for (y, x) in cells:
            c = agent.s.add_node("ShapeCell", {"row": int(y), "col": int(x)})
            agent.inner.add_edge_unchecked(c, "within", f)
        return f

    figs = {k: fig(v) for k, v in LIB.items()}
    ask = make_ask(timeout=300.0, preamble="")
    prior = ""
    for attempt in range(1, max_repair + 2):
        print(f"--- consult attempt {attempt} ---", flush=True)
        m = re.search(r"@@@term\s*(.+?)\s*@@@end", ask(Q.format(prims=PRIMS, err=prior)) or "", re.DOTALL)
        if not m:
            prior = "\n\nReturn ONLY JSON between @@@term and @@@end."; continue
        try:
            cc = json.loads(m.group(1).strip())
        except Exception as e:
            prior = f"\n\nJSON parse error: {e}."; print("  bad json:", e, flush=True); continue
        try:
            got = {k: round(float(agent.inner.evaluate(cc, {"x": figs[k]}))) for k in EXPECT}
        except Exception as e:
            prior = f"\n\nEval raised {type(e).__name__}: {e}. Fix the term."; print("  raised:", e, flush=True); continue
        ok = all(got[k] == EXPECT[k] for k in EXPECT)
        for k in EXPECT:
            print(f"  convex_corners({k:9s}) = {got[k]}  (want {EXPECT[k]})  [{'ok' if got[k]==EXPECT[k] else 'WRONG'}]", flush=True)
        if not ok:
            prior = "\n\nWrong corner counts. Re-check the 4 windows and the 8 neighbour offsets."
            print("  feeding back.", flush=True); continue

        # APPEND as a new descriptor dimension + rebuild the library
        agent.register_concept("convex_corners", cc)
        sense = json.load(open(SENSE))
        desc = next(c["definition"] for c in sense["concepts"] if c["name"] == "shape_descriptor")
        def find_vec(t):
            if isinstance(t, dict):
                if t.get("type") == "Vec":
                    return t
                for v in t.values():
                    r = find_vec(v)
                    if r: return r
            elif isinstance(t, list):
                for v in t:
                    r = find_vec(v)
                    if r: return r
            return None
        find_vec(desc)["items"].append({"type": "Times", "items": [{"type": "Lit", "value": 0.25},
                          {"type": "Holds", "concept": "convex_corners", "node": {"type": "Var", "name": "x"}}]})
        agent.register_concept("shape_descriptor", desc)

        def vec(cells):
            return [round(float(z), 4) for z in agent.inner.evaluate(desc, {"x": fig(cells)})]
        newD = {nm: vec(cells) for nm, cells in LIB.items()}
        print(f"\n  descriptor dim now {len(newD['cross'])}; rebuilt library. colliding pairs:", flush=True)
        for a, b in [("triangle", "T_shape"), ("cross", "diamond")]:
            print(f"    {a}~{b} = {math.dist(newD[a],newD[b]):.3f}  (now separated)", flush=True)

        # persist: shape_sense (descriptor + convex_corners) + shape_library (rebuilt descriptors)
        sense["concepts"] = [c for c in sense["concepts"] if c["name"] != "convex_corners"]
        sense["concepts"].append({"name": "convex_corners", "domain": "shape", "definition": cc})
        for c in sense["concepts"]:
            if c["name"] == "shape_descriptor":
                c["definition"] = desc
        json.dump(sense, open(SENSE, "w"), indent=2)
        lib = json.load(open(LIBSEED))
        for node in lib["nodes"]:
            node["attrs"]["descriptor"] = json.dumps(newD[node["attrs"]["name"]])
        json.dump(lib, open(LIBSEED, "w"), indent=2)
        print("\n✓ the jabberwock authored convex_corners (the polygon-defining feature), appended it,\n"
              "  and rebuilt the library. A triangle and a T, a cross and a diamond, are now distinct.", flush=True)
        return True
    print("\n✗ not landed.", flush=True)
    return False


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
