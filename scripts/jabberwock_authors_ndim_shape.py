"""The jabberwock re-authors SHAPE as an arbitrary-N-dimensional VECTOR of diverse
features — because a scalar (or a naive moment vector) collapses shape and is
confidently wrong on the next collision.
(Creator: "the problem here is it being confidently wrong - this should be an arbitrary
N dimensional fix and the shapes should be arbitrary.")

Verified offline: moments alone conflate scale and shape (a 2x shape moves farther than
a shape change). What holds up is a vector of COMPLEMENTARY rotation+scale-robust
features — fill (solidity), I1 (spread), I2 (elongation) — compared by DISTANCE. Shapes
are arbitrary: near = same shape, far = different, a graded distance not a collapse.
is_cross becomes "near the cross prototype in that space, AND not too far to be sure"
(a confidence guard) — so the agent is uncertain rather than confidently wrong. The Vec
is EXTENSIBLE: append more features (arm-tips, holes) for finer resolution.
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
  Var{name}  Lit{value}  Attr{node,key}("row"/"col")
  InNeighbours{node:Var x, edge_type:"within"}                  the figure's cells
  Count{source}   Sum{source,var_name:"c",value:<expr in c>}
  MinOver{source,var_name:"c",value:<expr>,default:Lit 0}  MaxOver{...}    bbox extent
  Plus{items:[..]} Minus{a,b} Times{items:[..]} Div{a,b} Pow{a,b}
  Let{name,value,body}                                          bind a value in body
  Vec{items:[<expr>,<expr>,...]}                                a VECTOR value"""

Q = """Author `shape_descriptor` over a figure "x": a VECTOR of three rotation+scale-robust features
(NOT a scalar — a scalar maps a cross and a box to the same number). With n = Count(cells),
cx = Sum(row)/n, cy = Sum(col)/n, and per cell dr=(row-cx), dc=(col-cy):

  fill = n / ((MaxOver row - MinOver row + 1) * (MaxOver col - MinOver col + 1))     (solidity: box~1, cross~0.5)
  m20 = Sum(dr*dr) ; m02 = Sum(dc*dc) ; m11 = Sum(dr*dc)
  I1  = (m20 + m02) / (n*n)                          (total spread)
  I2  = ((m20-m02)^2 + 4*m11^2) / (n^4)              (elongation)

Return Vec([ fill, Times(5, I1), Times(20, I2) ]) — the 5 and 20 put the features in a comparable
range. Build it with nested Let (n, cx, cy, then the sums). Keep it a Vec so more features can be
appended later.

{prims}

Output ONLY the JSON term between the markers:
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

    rot = lambda cs: [(c, -r) for r, c in cs]
    scl = lambda cs: [(2 * r + dr, 2 * c + dc) for r, c in cs for dr in (0, 1) for dc in (0, 1)]
    plus = [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)]
    box = [(r, c) for r in range(3) for c in range(3)]
    L = [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)]
    T = [(0, 0), (0, 1), (0, 2), (1, 1), (2, 1)]
    base = {"plus": plus, "box": box, "L": L, "T": T}
    figs = {k: fig(v) for k, v in base.items()}
    figs.update({k + "_rot": fig(rot(v)) for k, v in base.items()})
    figs.update({k + "_2x": fig(scl(v)) for k, v in base.items()})
    same = [(k, k + "_rot") for k in base] + [(k, k + "_2x") for k in base]      # must be NEAR
    diff = [(a, b) for a in base for b in base if a < b]                          # must be FAR

    def vec(term, f):
        return [float(z) for z in agent.inner.evaluate(term, {"x": f})]

    ask = make_ask(timeout=300.0, preamble="")
    prior = ""
    for attempt in range(1, max_repair + 2):
        print(f"--- consult attempt {attempt} ---", flush=True)
        m = re.search(r"@@@term\s*(.+?)\s*@@@end", ask(Q.format(prims=PRIMS, err=prior)) or "", re.DOTALL)
        if not m:
            prior = "\n\nReturn ONLY the JSON between @@@term and @@@end."; continue
        try:
            term = json.loads(m.group(1).strip())
        except Exception as e:
            prior = f"\n\nJSON parse error: {e}."; print("  bad json:", e, flush=True); continue
        try:
            V = {k: vec(term, f) for k, f in figs.items()}
        except Exception as e:
            prior = f"\n\nEval raised {type(e).__name__}: {e}. Fix the term."; print("  raised:", e, flush=True); continue
        d = lambda a, b: math.dist(V[a], V[b])
        print("  dim =", len(V["plus"]), flush=True)
        sd = max(d(a, b) for a, b in same); df = min(d(a, b) for a, b in diff)
        print(f"  max same(rotation/scale)-dist = {sd:.3f}   min distinct-dist = {df:.3f}", flush=True)
        for a, b in diff:
            print(f"    {a:4s}~{b:4s} {d(a,b):.3f}", flush=True)
        if sd < df:
            thr = round((sd + df) / 2, 4)
            # is_cross = near the PLUS prototype (a baked descriptor) within a confidence
            # radius; far shapes are NOT asserted to be crosses (uncertain, not wrong).
            plus_vec = V["plus"]; near_plus = min(d("plus", k) for k in base if k != "plus")
            radius = round((sd + near_plus) / 2, 4)
            DESC = {"type": "Holds", "concept": "shape_descriptor", "node": {"type": "Var", "name": "x"}}
            mag = lambda a, b: {"type": "Magnitude", "arg": {"type": "VecSub", "a": a, "b": b}}
            same_shape = {"type": "Lt", "a": mag(DESC, {"type": "Holds", "concept": "shape_descriptor",
                          "node": {"type": "Var", "name": "y"}}), "b": {"type": "Lit", "value": thr}}
            is_cross = {"type": "Lt", "a": mag(DESC, {"type": "Vec", "items": [{"type": "Lit", "value": v} for v in plus_vec]}),
                        "b": {"type": "Lit", "value": radius}}
            agent.register_concept("shape_descriptor", term)
            seed = json.load(open(SEED))
            seed["concepts"] = [c for c in seed["concepts"] if c["name"] not in
                                ("shape_descriptor", "same_shape", "is_cross", "shape_signature")]
            seed["concepts"] += [{"name": "shape_descriptor", "domain": "space", "definition": term},
                                 {"name": "same_shape", "domain": "space", "definition": same_shape},
                                 {"name": "is_cross", "domain": "space", "definition": is_cross}]
            json.dump(seed, open(SEED, "w"), indent=2)
            print(f"\n✓ N-dim shape_descriptor authored (3 features, extensible); same_shape thr={thr}, "
                  f"is_cross radius={radius}. Shape is a VECTOR — arbitrary shapes separated by "
                  f"distance, with a confidence guard. Persisted.", flush=True)
            return True
        prior = (f"\n\nNOT separable: a same-shape (rotation/scale) pair was as far as {sd:.3f} while a "
                 f"distinct-shape pair was only {df:.3f}. Check fill (n/bbox) and the I1/I2 formulas.")
        print("  not separable; feeding back.", flush=True)
    print("\n✗ not landed.", flush=True)
    return False


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
