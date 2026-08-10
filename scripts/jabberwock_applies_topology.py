"""The jabberwock APPLIES its mathematical understanding of TOPOLOGY to shape.
(Creator: "have it apply its understanding of topology from math to the shape process.")

It holds topology as knowledge (topology_open_sets, manifold) — the properties invariant
under continuous DEFORMATION. Its shape descriptor so far is all METRIC (fill, spread,
elongation) — those change under deformation. Topology offers a deformation-invariant
feature: the NUMBER OF HOLES (1st Betti number), via the Euler characteristic of the
cell complex:  X = (#cells) - (#4-adjacencies) + (#2x2 filled blocks),  holes = 1 - X
for a connected shape. A solid box -> 0, a ring/frame -> 1, two holes -> 2 — invariant
to any stretch/rotation/scale. It authors `holes` graph-natively from its cells, verifies
it on shapes of known topology, and APPENDS it as a new dimension of shape_descriptor
(the arbitrary-N vector growing a genuinely different KIND of feature).
"""
from __future__ import annotations
import json, os, re, sys, math
os.environ.setdefault("ARC3_THIN", "1")
sys.path.insert(0, "."); sys.path.insert(0, "scripts")
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from scripts.claude_teacher import make_ask

SEED = "seeds/shape_sense.json"

PRIMS = """DSL forms (JSON):
  Var{name} Lit{value} Attr{node,key}("row"/"col") Count{source}
  InNeighbours{node:Var x, edge_type:"within"}                          the figure's cells
  Sum{source,var_name:"c",value:<expr in c>}                            Σ over cells
  Exists{source,var_name:"c2",predicate:<bool expr in c2 and the outer c>}   does some cell satisfy it
  IfThenElse{cond,then,other}  And{items:[..]}  Eq{a,b}
  Plus{items:[..]} Minus{a,b}"""

Q = """You understand topology: properties invariant under continuous DEFORMATION. A shape's NUMBER OF
HOLES is such an invariant (a solid box has 0, a ring/frame has 1) — unlike fill/spread which change
under deformation. Author the concept `holes` over a figure "x" from its cells, via the Euler
characteristic of the cell complex:

  n = Count(cells)
  A = number of 4-adjacencies: for each cell c, add 1 if a cell exists at (row, col+1) and 1 if a
      cell exists at (row+1, col)   [each adjacency counted once]
  B = number of 2x2 filled blocks: for each cell c, add 1 if cells exist at (row,col+1), (row+1,col)
      AND (row+1,col+1)
  X = n - A + B ;  holes = 1 - X = 1 - n + A - B    (the shape is one connected piece)

Use Sum over the cells; test "a cell exists at (r,k)" with Exists over the cells whose predicate
matches a cell c2 with Eq(Attr(c2,"row"), <r>) and Eq(Attr(c2,"col"), <k>); coerce Exists to 1/0
with IfThenElse(<exists>, Lit 1, Lit 0). <r>,<k> are built from the outer cell c with Plus/Attr.

{prims}

Output ONLY the JSON term between markers:
@@@term
<json>
@@@end{err}"""


def run(max_repair=3):
    agent = WorldAdapter(seeds=()); load_all_seeds(agent)

    def fig(cells):
        f = agent.s.add_node("Figure", {})
        for (y, x) in cells:
            c = agent.s.add_node("ShapeCell", {"row": int(y), "col": int(x)})
            agent.inner.add_edge_unchecked(c, "within", f)
        return f

    box3 = [(r, c) for r in range(3) for c in range(3)]
    topo = {
        "solid box": (fig(box3), 0),
        "ring (hole)": (fig([p for p in box3 if p != (1, 1)]), 1),
        "plus": (fig([(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)]), 0),
        "solid 4x4": (fig([(r, c) for r in range(4) for c in range(4)]), 0),
        "two holes": (fig([(r, c) for r in range(3) for c in range(5) if (r, c) not in ((1, 1), (1, 3))]), 2),
    }
    print("GAP: the shape descriptor is metric (fill/spread/elongation) — it can't see a HOLE.\n", flush=True)

    ask = make_ask(timeout=300.0, preamble="")
    prior = ""
    for attempt in range(1, max_repair + 2):
        print(f"--- consult attempt {attempt} (applying topology) ---", flush=True)
        m = re.search(r"@@@term\s*(.+?)\s*@@@end", ask(Q.format(prims=PRIMS, err=prior)) or "", re.DOTALL)
        if not m:
            prior = "\n\nReturn ONLY JSON between @@@term and @@@end."; continue
        try:
            holes = json.loads(m.group(1).strip())
        except Exception as e:
            prior = f"\n\nJSON parse error: {e}."; print("  bad json:", e, flush=True); continue
        try:
            got = {k: round(float(agent.inner.evaluate(holes, {"x": f})), 3) for k, (f, _) in topo.items()}
        except Exception as e:
            prior = f"\n\nEval raised {type(e).__name__}: {e}. Fix the term."; print("  raised:", e, flush=True); continue
        ok = all(abs(got[k] - want) < 0.01 for k, (_, want) in topo.items())
        for k, (_, want) in topo.items():
            print(f"  holes({k:11s}) = {got[k]}  (want {want})  [{'ok' if abs(got[k]-want)<0.01 else 'WRONG'}]", flush=True)
        if not ok:
            prior = "\n\nWrong hole counts (ring must be 1, solid 0, two-holes 2). Recheck A (adjacencies) and B (2x2 blocks)."
            print("  feeding back.", flush=True); continue

        # APPLY: append holes as a new (topological) dimension of shape_descriptor.
        # The descriptor is wrapped in Let bindings, so find the Vec inside it.
        def find_vec(t):
            if isinstance(t, dict):
                if t.get("type") == "Vec":
                    return t
                for v in t.values():
                    r = find_vec(v)
                    if r:
                        return r
            elif isinstance(t, list):
                for v in t:
                    r = find_vec(v)
                    if r:
                        return r
            return None
        agent.register_concept("holes", holes)
        seed = json.load(open(SEED))
        desc = next(c["definition"] for c in seed["concepts"] if c["name"] == "shape_descriptor")
        find_vec(desc)["items"].append({"type": "Times", "items": [{"type": "Lit", "value": 0.5},
                              {"type": "Holds", "concept": "holes", "node": {"type": "Var", "name": "x"}}]})
        agent.register_concept("shape_descriptor", desc)
        # re-verify: box vs ring now separated by the topological dim; metric shapes unaffected
        def vec(f):
            return [float(z) for z in agent.inner.evaluate(desc, {"x": f})]
        vb, vr, vp = vec(topo["solid box"][0]), vec(topo["ring (hole)"][0]), vec(topo["plus"][0])
        print(f"\n  descriptor dim now {len(vb)} (topological dim appended)", flush=True)
        print(f"  box~ring distance = {math.dist(vb,vr):.3f}  (was 0 in the metric features — a hole now SEPARATES them)", flush=True)
        seed["concepts"] = [c for c in seed["concepts"] if c["name"] != "holes"]
        seed["concepts"].append({"name": "holes", "domain": "topology", "definition": holes})
        for c in seed["concepts"]:
            if c["name"] == "shape_descriptor":
                c["definition"] = desc
        json.dump(seed, open(SEED, "w"), indent=2)
        print("\n✓ the jabberwock applied topology: authored `holes` (Euler characteristic) and grew its\n"
              "  shape descriptor with a deformation-invariant dimension. A box and a ring are no longer\n"
              "  the same shape. Persisted.", flush=True)
        return True
    print("\n✗ topology not applied.", flush=True)
    return False


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
