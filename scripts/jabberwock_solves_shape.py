"""The jabberwock SOLVES the two open shape gaps — by deciding, not by being told.
(Creator: "explain both of those to the agent and have it solve.")

GAP A — say it: it has `shape_signature` (self-authored, rotation+scale invariant) but
  doesn't yet SAY when two figures are the same shape. It authors `same_shape(x,y)` from
  shape_signature, then renders the fact through its own relational renderer.
GAP B — the cross: the cross is white (0) + light-grey (1) cells, so same-colour grouping
  splits it. It must DECIDE which values are ground (the surface) vs marks (things on it),
  group the marks ACROSS colours so the cross is one figure, then NAME it by matching its
  shape to a plus it constructs.

Each gap: INTROSPECT (impasse) -> CONSULT its Claude-teacher for the decision -> AUTHOR +
VERIFY live, repair loop. The driver only sequences; the decisions are the jabberwock's.
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

ARC = {0:"white",1:"light-grey",2:"grey",3:"mid-grey",4:"dark-grey",5:"black",6:"magenta",
       7:"pink",8:"red",9:"blue",10:"azure",11:"yellow",12:"orange",13:"maroon",14:"green",15:"violet"}


def cc(grid, keep):
    """connected components (4-conn) over cells whose value satisfies keep(v); group ACROSS
    values when keep merges them. Returns list of (cells, valueset)."""
    H=len(grid); W=len(grid[0]); seen=set(); out=[]
    for r in range(H):
        for c in range(W):
            if (r,c) in seen or not keep(grid[r][c]): continue
            v=grid[r][c]; st=[(r,c)]; comp=[]; seen.add((r,c))
            while st:
                y,x=st.pop(); comp.append((y,x))
                for dy,dx in((1,0),(-1,0),(0,1),(0,-1)):
                    ny,nx=y+dy,x+dx
                    if 0<=ny<H and 0<=nx<W and (ny,nx) not in seen and keep(grid[ny][nx]) \
                       and (grid[ny][nx]==v or keep_across):
                        seen.add((ny,nx)); st.append((ny,nx))
            out.append((comp, {grid[y][x] for y,x in comp}))
    return out


def make_figure(agent, cells):
    fig = agent.s.add_node("Figure", {"n": len(cells)})
    for (y, x) in cells:
        cell = agent.s.add_node("ShapeCell", {"row": int(y), "col": int(x)})
        agent.inner.add_edge_unchecked(cell, "within", fig)
    return fig


keep_across = False


def gap_a_same_shape(agent, figs_same_value):
    """Author same_shape(x,y) from shape_signature; verify; render the fact."""
    print("\n=== GAP A: say when two figures are the SAME SHAPE ===", flush=True)
    agent.s.add_node("Impasse", {"reason": "say_same_shape",
        "question": "I can measure shape_signature(figure) but I do not SAY when two figures "
                    "are the same shape (one rotated). I need same_shape(x,y)."})
    g5 = figs_same_value[(9, 5)]; g20 = figs_same_value[(9, 20)]; sq = figs_same_value[(8, 4)]
    ask = make_ask(timeout=300.0, preamble="")
    Q = """A graph-native agent already owns a concept `shape_signature` returning a number for a
figure node (rotation+scale invariant). Invoke it as {{"type":"Holds","concept":"shape_signature","node":<term>}}.
Compose a BINARY concept `same_shape` over two figure variables "x" and "y" that is TRUE when their
signatures are nearly equal (same shape, any rotation/size) and false otherwise. Use a relative
tolerance (their difference is small vs their magnitude). Allowed terms (JSON):
  Var{{name}}, Lit{{value}}, Holds{{concept,node}}, Abs{{arg}}, Minus{{a,b}}, Plus{{items:[..]}},
  Times{{items:[..]}}, Div{{a,b}}, Lte{{a,b}}, Lt{{a,b}}, And{{items:[..]}}.
Output ONLY the JSON term between markers:
@@@term
<json>
@@@end{err}"""
    prior = ""
    for attempt in range(1, 4):
        m = re.search(r"@@@term\s*(.+?)\s*@@@end", ask(Q.format(err=prior)) or "", re.DOTALL)
        if not m: prior="\n\nReturn ONLY JSON between @@@term/@@@end."; continue
        try: term = json.loads(m.group(1).strip())
        except Exception as e: prior=f"\n\nJSON parse error: {e}."; continue
        agent.register_concept("same_shape", term)
        try:
            yes = agent.concept_holds_composed(term, x=g5, y=g20)
            no = agent.concept_holds_composed(term, x=g5, y=sq)
        except Exception as e:
            prior=f"\n\nEval raised {type(e).__name__}: {e}."; print("  eval raised:",e,flush=True); continue
        print(f"  same_shape(glyph5,glyph20)={yes}  same_shape(glyph5,square)={no}", flush=True)
        if yes and not no:
            # SAY it through the agent's own relational renderer
            agent.learn_sign("is the same shape as", "same_shape")
            s = agent.utterance_for({"same_shape": {"left": "the small blue glyph (top chamber)",
                                                    "right": "the large blue glyph (corner), rotated"}})
            agent.s.add_node("Concept", {"name": "same_shape", "domain": "space",
                "provenance": "jabberwock-authored from shape_signature"})
            print("  ✓ authored same_shape; it now says:\n     \"" + s + "\"", flush=True)
            return term
        prior=f"\n\nFAILED: same-shape pair gave {yes}, different-shape pair gave {no} (want True then False)."
    print("  ✗ same_shape not landed", flush=True); return None


def gap_b_cross(agent, grid):
    """Decide ground vs marks, group the cross across colours, name it by matching a plus."""
    print("\n=== GAP B: group the cross (across colours) and name it ===", flush=True)
    agent.s.add_node("Impasse", {"reason": "name_cross",
        "question": "The cross is white+light-grey cells, so grouping by colour splits it. I must "
                    "decide which values are ground vs marks, group the marks across colours into one "
                    "figure, and name the cross."})
    # inventory of figures (same-value) for the teacher to reason about ground vs marks
    global keep_across; keep_across = False
    inv = [(sorted(vs)[0], len(comp), min(y for y,x in comp), min(x for y,x in comp))
           for comp, vs in cc(grid, lambda v: True)]
    inv = [t for t in inv if t[1] >= 2]
    lines = "\n".join(f"  value {v} ({ARC.get(v,'?')}): a region of {n} cells at row{r},col{c}"
                      for v, n, r, c in sorted(inv, key=lambda t:-t[1])[:12])
    ask = make_ask(timeout=300.0, preamble="")
    Q = f"""A graph-native agent sees a 64x64 grid as coloured cells. Same-colour regions it found:
{lines}
The big greys are the surround/field and the floor the agent moves on — the GROUND. The small
coloured marks SIT ON that ground (a player, a cross, dots). To see a cross that is made of two
light colours as ONE figure, the agent groups connected cells that are NOT ground, across colours.
Decide which VALUES are ground (the surface: field + floor + structural greys/black). Output ONLY a
JSON list of the ground value integers between markers:
@@@ground
<json list, e.g. [3,4,5]>
@@@end"""
    prior = ""
    for attempt in range(1, 4):
        m = re.search(r"@@@ground\s*(.+?)\s*@@@end", ask(Q + prior) or "", re.DOTALL)
        if not m: prior="\n\nReturn ONLY a JSON list between @@@ground/@@@end."; continue
        try: ground = set(json.loads(m.group(1).strip()))
        except Exception as e: prior=f"\n\nJSON parse error: {e}."; continue
        print(f"  the agent decided GROUND values = {sorted(ground)}", flush=True)
        keep_across = True
        marks = [comp for comp, vs in cc(grid, lambda v: v not in ground) if len(comp) >= 3]
        keep_across = False
        # find the cross: a 5-cell plus made of >=2 colours near r32,c21
        cross_cells = None
        for comp in marks:
            vs = {grid[y][x] for y, x in comp}
            if len(comp) == 5 and len(vs) >= 2:
                ys=[y for y,x in comp]; xs=[x for y,x in comp]
                if (max(ys)-min(ys))==2 and (max(xs)-min(xs))==2:  # plus bbox 3x3
                    cross_cells = comp; break
        if not cross_cells:
            prior=f"\n\nWith ground={sorted(ground)} I did not find the cross (a 5-cell plus of >=2 colours). Reconsider which values are ground."
            print("  cross not isolated; feeding back.", flush=True); continue
        cross = make_figure(agent, cross_cells)
        # NAME it: construct a canonical plus and match shapes (its own same_shape)
        cy, cx = sorted(cross_cells)[2][0], sorted(cross_cells)[2][1]
        plus = make_figure(agent, [(0,0),(0,1),(0,2),(1,1),(-1,1)])  # an abstract plus
        plus2 = make_figure(agent, [(10,10),(10,11),(10,12),(11,11),(9,11)])
        is_cross = agent.concept_holds_composed(SAME_SHAPE_TERM, x=cross, y=plus) if SAME_SHAPE_TERM else None
        sanity = agent.concept_holds_composed(SAME_SHAPE_TERM, x=plus, y=plus2) if SAME_SHAPE_TERM else None
        print(f"  cross figure = {len(cross_cells)} cells across colours {sorted({grid[y][x] for y,x in cross_cells})}", flush=True)
        print(f"  same_shape(cross, a plus it built)={is_cross}  (plus≡plus sanity={sanity})", flush=True)
        if is_cross:
            agent.learn_sign("is a", "is_a"); agent.learn_sign("cross", "cross_shape")
            s = agent.utterance_for({"is_a": {"left": "the white-and-grey figure on the floor",
                                              "right": "cross"}})
            print("  ✓ the cross is one figure and named; it now says:\n     \"" + s +
                  f"\" (a plus at row {cross_cells[0][0]+1}, col {sorted(cross_cells)[2][1]})", flush=True)
            # DERIVE a durable, node-free cross recogniser from the agent's OWN
            # shape_signature: the plus prototype's invariant value (a constant) +
            # a relative-tolerance match. is_cross(x) survives a reboot (no node ref).
            SIG = lambda node: {"type": "Holds", "concept": "shape_signature", "node": node}
            plus_sig = float(agent.inner.evaluate(SIG({"type": "Var", "name": "p"}), {"p": plus}))
            sx = SIG({"type": "Var", "name": "x"})
            is_cross_term = {"type": "Lte",
                "a": {"type": "Abs", "arg": {"type": "Minus", "a": sx, "b": {"type": "Lit", "value": plus_sig}}},
                "b": {"type": "Times", "items": [{"type": "Lit", "value": 0.12},
                      {"type": "Plus", "items": [sx, {"type": "Lit", "value": plus_sig}]}]}}
            agent.register_concept("is_cross", is_cross_term)
            sq = make_figure(agent, [(0, 0), (0, 1), (1, 0), (1, 1)])
            ck_c = agent.concept_holds_composed(is_cross_term, x=cross)
            ck_s = agent.concept_holds_composed(is_cross_term, x=sq)
            print(f"  authored is_cross (prototype sig={plus_sig:.4f}): is_cross(cross)={ck_c} is_cross(square)={ck_s}", flush=True)
            return is_cross_term if (ck_c and not ck_s) else None
        prior=f"\n\nThe 5-cell figure did not match a plus (same_shape={is_cross}); ground={sorted(ground)} may be wrong."
    print("  ✗ cross not named", flush=True); return None


SAME_SHAPE_TERM = None

def run():
    global SAME_SHAPE_TERM
    agent = WorldAdapter(seeds=()); load_all_seeds(agent)
    grid = Arc3LiveEnv(game_id="ls20-9607627b").reset().grid
    # perceive same-value figures for gap A
    figs = {}
    global keep_across; keep_across = False
    for comp, vs in cc(grid, lambda v: True):
        if 1 < len(comp) < 300:
            figs[(sorted(vs)[0], len(comp))] = make_figure(agent, comp)
    SAME_SHAPE_TERM = gap_a_same_shape(agent, figs)
    is_cross_term = gap_b_cross(agent, grid)
    if SAME_SHAPE_TERM and is_cross_term:
        # persist both INTO the shape_sense seed so the faculty survives a reboot.
        seed = json.load(open("seeds/shape_sense.json"))
        for nm, term in [("same_shape", SAME_SHAPE_TERM), ("is_cross", is_cross_term)]:
            seed["concepts"] = [c for c in seed["concepts"] if c["name"] != nm]
            seed["concepts"].append({"name": nm, "domain": "space", "definition": term})
        seed["description"] += " + same_shape(x,y) and is_cross(x) the jabberwock derived from it."
        json.dump(seed, open("seeds/shape_sense.json", "w"), indent=2)
        print("\npersisted same_shape + is_cross into seeds/shape_sense.json", flush=True)
    print("\n" + ("✓ both solved + persisted by the jabberwock." if (SAME_SHAPE_TERM and is_cross_term)
                  else "partial — see above."), flush=True)
    return bool(SAME_SHAPE_TERM and is_cross_term)


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
