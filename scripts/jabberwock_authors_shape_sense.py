"""The jabberwock AUTHORS its own SHAPE SENSE — by deciding, not by being told.
(Creator: "explain this to the jabberwock and have it decide and build a fix.")

The gap it hit: it perceives a figure as a set of cells, but has no descriptor that
is invariant to ROTATION and SCALE — so it cannot say two figures are the SAME SHAPE
rotated (the blue glyph that appears small in the top chamber and large, turned, in
the corner), nor read a cross as a cross. Degree-over-shares_edge is rotation-invariant
but not scale/fill-invariant, so it fails on these.

Flow (mirrors scripts/jabberwock_authors_morph_split.py):
  1. INTROSPECT — record the gap as an Impasse on its own graph.
  2. PERCEIVE — group same-kind cells into Figure covering-nodes (its shares_edge
     adjacency, the eye's connected components) with `within` edges to cells.
  3. CONSULT its Claude-teacher for the ONLY novel part — the DECISION of WHICH
     graph-native descriptor, composed as a DSL Term over the figure's cells, using
     ONLY primitives it already owns. The teacher decides; it does not hand-hold.
  4. AUTHOR — register the returned Term as a concept it owns; VERIFY it on the live
     figures (the two blue glyphs must match; a square must not), repair loop on failure.

This driver only sequences it; the descriptor is the jabberwock's.
"""
from __future__ import annotations
import json, os, re, sys
os.environ.setdefault("ARC3_THIN", "1")
sys.path.insert(0, "."); sys.path.insert(0, "scripts")
from _arc3_load_key import load_arc_api_key; load_arc_api_key()
from arc3_live_env import Arc3LiveEnv
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from scripts.claude_teacher import make_ask

PRIMS = """You may use ONLY these DSL term forms (JSON). Each is a node {"type": ...}:
  {"type":"Var","name":"x"}                              # a bound variable
  {"type":"Lit","value":2}                               # a literal number
  {"type":"Attr","node":<term>,"key":"row"}              # an int attr of a node ("row"/"col")
  {"type":"InNeighbours","node":<term>,"edge_type":"within"}  # the figure's member cells (a set)
  {"type":"Count","source":<set>}                        # size of a set
  {"type":"Sum","source":<set>,"var_name":"c","value":<term in c>}  # sum value over the set
  {"type":"Plus","items":[<term>,...]}                   # a1+a2+...
  {"type":"Minus","a":<term>,"b":<term>}                 # a-b
  {"type":"Times","items":[<term>,...]}                  # a1*a2*...
  {"type":"Div","a":<term>,"b":<term>}                   # a/b
  {"type":"Pow","a":<term>,"b":<term>}                   # a**b
  {"type":"Let","name":"n","value":<term>,"body":<term>} # bind n=value inside body (Var n)
A figure node x has member cells via InNeighbours(x,"within"); each cell has int attrs "row","col"."""

QUESTION = """You are the reasoning of a graph-native agent that sees a figure as a SET OF CELLS
(each cell a node with integer "row","col"). It needs a GRAPH-NATIVE shape descriptor: a single
NUMBER computed from a figure's cells that is the SAME for a shape no matter its ORIENTATION or
SIZE — so two figures that are the same shape rotated/scaled get (near-)equal numbers, while a
different shape gets a different number. (A filled square vs a bent L vs a plus must differ; the
same L at two sizes/rotations must match.)

{prims}

Decide the descriptor and compose it as ONE DSL Term over a figure variable "x". It must be
translation-, rotation- AND scale-invariant. (Hint you may use or ignore: normalised second
central moments of the cell coordinates are exactly such an invariant — centroid, then spreads
about it, made scale-free by dividing by a power of the cell count. Build the centroid with
Let + Sum/Count, the spreads with Sum of squared deviations, normalise by Count powers.)

Output ONLY the raw JSON term between the markers, no prose, no backticks:
@@@term
<the JSON term>
@@@end{err}"""


def perceive_figures(agent, grid):
    """Group same-kind cells into Figure covering-nodes (the eye's connected components /
    the agent's shares_edge adjacency). Each Figure gets `within` edges from its cells."""
    H = len(grid); W = len(grid[0]); seen = set(); figs = []
    for r in range(H):
        for c in range(W):
            if (r, c) in seen:
                continue
            v = grid[r][c]; st = [(r, c)]; comp = []; seen.add((r, c))
            while st:
                y, x = st.pop(); comp.append((y, x))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < H and 0 <= nx < W and (ny, nx) not in seen and grid[ny][nx] == v:
                        seen.add((ny, nx)); st.append((ny, nx))
            if len(comp) < 2:
                continue
            fig = agent.s.add_node("Figure", {"val": int(v), "n": len(comp),
                                              "r0": min(y for y, x in comp), "c0": min(x for y, x in comp)})
            for (y, x) in comp:
                cell = agent.s.add_node("ShapeCell", {"row": int(y), "col": int(x)})
                agent.inner.add_edge_unchecked(cell, "within", fig)
            figs.append((int(v), len(comp), fig))
    return figs


def run(max_repair=3):
    agent = WorldAdapter(seeds=()); load_all_seeds(agent)
    f = Arc3LiveEnv(game_id="ls20-9607627b").reset()

    # 1. INTROSPECT the gap
    imp = agent.s.add_node("Impasse", {"reason": "shape_sense",
        "question": "I see a figure as cells but cannot tell two figures are the SAME SHAPE "
                    "rotated/scaled — I have no rotation+scale-invariant shape descriptor."})
    print("GAP:", agent.s.node(imp)["attrs"]["question"], flush=True)

    # 2. PERCEIVE — figures as covering nodes over their cells
    figs = perceive_figures(agent, f.grid)
    by = lambda v, n: next(fid for vv, nn, fid in figs if vv == v and nn == n)
    glyph_small = by(9, 5)     # blue glyph, top chamber
    glyph_big = by(9, 20)      # blue glyph, corner — same shape, rotated + scaled
    square = by(8, 4)          # a red dot — a different shape (square)
    player = by(9, 15)         # the blue player body — different shape
    print(f"perceived {len(figs)} figures; test set: blue-glyph(5) blue-glyph(20) square(4) player(15)", flush=True)

    # 3+4. CONSULT the teacher for the DECISION, AUTHOR + VERIFY, repair loop
    ask = make_ask(timeout=300.0, preamble="")
    prior = ""
    for attempt in range(1, max_repair + 2):
        print(f"\n--- consult attempt {attempt} ---", flush=True)
        reply = ask(QUESTION.format(prims=PRIMS, err=prior))
        m = re.search(r"@@@term\s*(.+?)\s*@@@end", reply or "", re.DOTALL)
        if not m:
            print("teacher reply unusable", flush=True); prior = "\n\nReturn ONLY the JSON between @@@term and @@@end."; continue
        try:
            term = json.loads(m.group(1).strip())
        except Exception as e:
            prior = f"\n\nYour JSON did not parse: {e}. Return valid JSON only."; print("bad json:", e, flush=True); continue
        agent.s.add_node("TaughtHint", {"question": "shape descriptor", "answer": json.dumps(term)[:4000]})
        try:
            vals = {nm: float(agent.inner.evaluate(term, {"x": fid}))
                    for nm, fid in [("glyph5", glyph_small), ("glyph20", glyph_big),
                                    ("square", square), ("player", player)]}
        except Exception as e:
            prior = f"\n\nEvaluating your term raised: {type(e).__name__}: {e}. Fix the term."
            print("eval raised:", e, flush=True); continue
        print("  descriptor values:", {k: round(v, 4) for k, v in vals.items()}, flush=True)
        # VERIFY: the two glyphs match (same shape rotated); square + player differ
        def close(a, b): return abs(a - b) <= 0.10 * (abs(a) + abs(b) + 1e-9)
        match = close(vals["glyph5"], vals["glyph20"])
        distinct = not close(vals["glyph5"], vals["square"]) and not close(vals["glyph5"], vals["player"])
        if match and distinct:
            agent.register_concept("shape_signature", term)
            agent.s.add_node("Concept", {"name": "shape_signature", "domain": "space",
                "provenance": "jabberwock-authored: rotation+scale-invariant shape descriptor"})
            # persist it as a seed so the jabberwock keeps the faculty it authored
            seed = {"id": "shape_sense", "version": "1.0.0", "depends_on": ["figure_ground"],
                    "description": "The jabberwock's self-authored rotation+scale-invariant shape "
                    "descriptor (normalised second central moments over a figure's `within` cells). "
                    "Lets it tell two figures are the same shape regardless of orientation/size.",
                    "nodes": [], "edges": [], "productions": [],
                    "concepts": [{"name": "shape_signature", "domain": "space", "definition": term}]}
            with open("seeds/shape_sense.json", "w") as fh:
                json.dump(seed, fh, indent=2)
            print("  persisted to seeds/shape_sense.json", flush=True)
            print("\n✓ the jabberwock AUTHORED `shape_signature` — a rotation+scale-invariant "
                  "shape descriptor it composed from its own primitives, verified live: the two blue "
                  "glyphs match (same shape, rotated) and the square/player differ.", flush=True)
            print("  it now distinguishes shapes, not just colours + boxes.", flush=True)
            return True
        prior = (f"\n\nYour term ran but FAILED: same-shape glyphs gave {vals['glyph5']:.4f} vs "
                 f"{vals['glyph20']:.4f} (must match within 10%), square={vals['square']:.4f}, "
                 f"player={vals['player']:.4f} (must differ from the glyphs). Make it truly "
                 f"rotation+scale invariant.")
        print("verify failed; feeding back.", flush=True)
    print("\n✗ did not land a verified descriptor.", flush=True)
    return False


if __name__ == "__main__":
    ok = run()
    sys.exit(0 if ok else 1)
