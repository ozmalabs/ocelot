"""The jabberwock FIXES its own cross recogniser — it was calling a filled box a cross.
(Creator: "why does it think its body is a cross. it is a box.")

The gap: is_cross only checked shape_signature (the normalised 2nd moment = total
spread). A plus and a filled box have the SAME spread (both isotropic, 4-fold
symmetric) -> both score 0.16 -> both read as a cross. What separates them is that a
cross is SPARSE (arms, empty corners) while a box FILLS its bounding region. The agent
needs a feature that sees that, and a new is_cross that uses it.

It introspects the confusion, asks its teacher for the discriminating feature (composed
from primitives it owns + its own shape_signature), authors a new is_cross, verifies a
plus passes while boxes/dots fail, and persists it.
"""
from __future__ import annotations
import json, os, re, sys
os.environ.setdefault("ARC3_THIN", "1")
sys.path.insert(0, "."); sys.path.insert(0, "scripts")
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from scripts.claude_teacher import make_ask

SEED = "seeds/shape_sense.json"

PRIMS = """DSL term forms (JSON nodes {"type":...}):
  {"type":"Var","name":"x"}  {"type":"Lit","value":0.6}
  {"type":"Attr","node":<t>,"key":"row"}                         int attr "row"/"col" of a cell
  {"type":"InNeighbours","node":{"type":"Var","name":"x"},"edge_type":"within"}   the figure's cells (a set)
  {"type":"Count","source":<set>}                                size of a set
  {"type":"MinOver","source":<set>,"var_name":"c","value":<t in c>,"default":{"type":"Lit","value":0}}
  {"type":"MaxOver","source":<set>,"var_name":"c","value":<t in c>,"default":{"type":"Lit","value":0}}
  {"type":"Plus","items":[..]} {"type":"Minus","a":<t>,"b":<t>} {"type":"Times","items":[..]} {"type":"Div","a":<t>,"b":<t>}
  {"type":"Abs","arg":<t>} {"type":"Lte","a":<t>,"b":<t>} {"type":"Lt","a":<t>,"b":<t>} {"type":"And","items":[..]}
  {"type":"Holds","concept":"shape_signature","node":<t>}        invoke its 2nd-moment descriptor (a number)
A figure x: cells via InNeighbours(x,"within"); each cell has int "row","col"."""

Q = """A graph-native agent confused a filled BOX for a CROSS. Its `is_cross` only used
`shape_signature` (normalised 2nd moment = total spread), and a plus and a filled box have the SAME
spread (both 0.16, both isotropic/4-fold symmetric). The difference: a CROSS/plus is SPARSE — it has
arms and EMPTY CORNERS — while a BOX FILLS its bounding rectangle.

Author a NEW boolean concept `is_cross` over one figure "x" that is TRUE for a plus/cross and FALSE
for a filled box (and a small square). A good discriminator is the FILL RATIO = (number of cells) /
(bounding-box height x width): a box fills its box (~1.0), a plus leaves corners empty (~0.5). Build
the bbox from MinOver/MaxOver of row and col; require the fill to be clearly below full AND the spread
(Holds shape_signature) to be in the cross range (near 0.16, say within 0.05).

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

    cases = {
        "plus (a cross)": (fig([(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)]), True),
        "real ls20 cross": (fig([(31, 21), (32, 20), (32, 21), (32, 22), (33, 21)]), True),
        "filled 5x5 box (the body)": (fig([(y, x) for y in range(5) for x in range(5)]), False),
        "filled 3x3 box": (fig([(y, x) for y in range(3) for x in range(3)]), False),
        "2x2 dot": (fig([(0, 0), (0, 1), (1, 0), (1, 1)]), False),
    }
    agent.s.add_node("Impasse", {"reason": "cross_vs_box",
        "question": "is_cross calls a filled box a cross — a plus and a box share the same 2nd moment."})
    print("GAP: a plus and a filled box both score shape_signature 0.16, so is_cross fires on the box.\n", flush=True)

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
            res = {name: bool(agent.concept_holds_composed(term, x=f)) for name, (f, _) in cases.items()}
        except Exception as e:
            prior = f"\n\nEval raised {type(e).__name__}: {e}. Fix the term."; print("  eval raised:", e, flush=True); continue
        ok = all(res[name] == want for name, (_, want) in cases.items())
        for name, (_, want) in cases.items():
            mark = "ok" if res[name] == want else "WRONG"
            print(f"  is_cross({name}) = {res[name]}  (want {want})  [{mark}]", flush=True)
        if ok:
            agent.register_concept("is_cross", term)
            seed = json.load(open(SEED))
            seed["concepts"] = [c for c in seed["concepts"] if c["name"] != "is_cross"]
            seed["concepts"].append({"name": "is_cross", "domain": "space", "definition": term})
            json.dump(seed, open(SEED, "w"), indent=2)
            print("\n✓ the jabberwock fixed is_cross — a box is no longer a cross; persisted.", flush=True)
            return True
        prior = "\n\nSome verdicts were wrong (box must be False, plus must be True). Use the fill ratio."
        print("  feeding back.", flush=True)
    print("\n✗ not fixed.", flush=True)
    return False


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
