"""The jabberwock AUTHORS its own `predicted_overlap` — the term that makes avatar tracking
robust to the eye splitting/merging a region. (Its own design: "the avatar is whatever moves
the way your action says it should — track by prediction-matched overlap over CONSERVED CELL-SETS.")

The gap: it has cy/cx/drow/dcol per Region, but those centroids are corrupted by split/merge
(the colour-3 avatar jumps drow −18). It needs to ask, instead: after an action with KNOWN
displacement d, does a cell-set SHIFTED BY d land on the next frame? That number — the fraction
of prev cells whose (row+drow, col+dcol) hits a now cell — is invariant to how the eye re-partitions
the cells, because it is computed over the cell SET, not over region identities.

Flow mirrors scripts/jabberwock_authors_shape_sense.py:
  1. INTROSPECT the gap as an Impasse.
  2. PERCEIVE — build synthetic prev/now cell-sets: a block that MOVED UP (avatar), and a block
     that SHRANK IN PLACE (the depleting meter), as `within`-covered set nodes over cells.
  3. CONSULT the Claude-teacher for the ONLY novel part — the DECISION of the DSL Term, composed
     from primitives it already owns.
  4. AUTHOR — register the term; VERIFY: moved-by-d overlaps HIGH at d, LOW at no-shift, and the
     in-place shrink overlaps LOW at d. Repair loop. Persist as seeds/avatar_tracking.json.
"""
from __future__ import annotations
import json, re, sys
sys.path.insert(0, "."); sys.path.insert(0, "scripts")
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from scripts.claude_teacher import make_ask

PRIMS = """You may use ONLY these DSL term forms (JSON). Each is a node {"type": ...}:
  {"type":"Var","name":"prev"}        # the PREVIOUS-frame cell-set (a covering node)
  {"type":"Var","name":"now"}         # the CURRENT-frame cell-set (a covering node)
  {"type":"Var","name":"drow"}        # the action's known ROW displacement (a number, e.g. -1 for Up)
  {"type":"Var","name":"dcol"}        # the action's known COL displacement (a number)
  {"type":"Lit","value":1}
  {"type":"Attr","node":<term>,"key":"row"}                       # a cell's int "row" / "col"
  {"type":"InNeighbours","node":<term>,"edge_type":"within"}      # the member cells of a set (a set of cells)
  {"type":"Count","source":<set>}                                 # size of a set
  {"type":"Sum","source":<set>,"var_name":"p","value":<term in p>}# sum a value over the set
  {"type":"Filter","source":<set>,"var_name":"q","predicate":<bool term in q>}  # subset where predicate holds
  {"type":"Plus","items":[<term>,...]}                            # a+b+...
  {"type":"Minus","a":<term>,"b":<term>}
  {"type":"Div","a":<term>,"b":<term>}
  {"type":"Eq","a":<term>,"b":<term>}                             # a == b
  {"type":"And","items":[<bool>,...]}
  {"type":"Gt","a":<term>,"b":<term>}                             # a > b
  {"type":"IfThenElse","cond":<bool>,"then":<term>,"other":<term>}
  {"type":"Min","items":[<term>,...]}
  {"type":"Let","name":"n","value":<term>,"body":<term in Var n>}
A set node S has member cells via InNeighbours(S,"within"); each cell has int attrs "row","col"."""

QUESTION = """You are the reasoning of a graph-native agent tracking its avatar. You see two cell-sets:
`prev` (a thing's cells last frame) and `now` (this frame), and you KNOW the displacement (drow,dcol)
your last action should have produced (Up => drow=-1,dcol=0). You need ONE NUMBER in [0,1]:

  predicted_overlap = (how many cells of `prev`, once SHIFTED by (drow,dcol), land exactly on a cell of
                       `now`) divided by (the number of cells in `prev`).

A prev cell p "lands on" now if there exists a now cell q with q.row == p.row+drow AND q.col == p.col+dcol.
This is ~1 when the set really translated by (drow,dcol) (the avatar moved as the action predicted),
and small when the set shrank/grew in place or moved differently (a depleting meter, a split blob).
It must be computed over the cell SETS, so it is unaffected by how the cells are grouped into regions.

{prims}

Compose it as ONE DSL Term over the variables prev, now, drow, dcol. (Hint you may use or ignore:
Sum over prev's cells; for each prev cell test EXISTENCE of a matching now cell with Filter+Count>0
capped at 1; divide the total by Count of prev's cells.)

Output ONLY the raw JSON term between the markers, no prose, no backticks:
@@@term
<the JSON term>
@@@end{err}"""


def make_set(agent, cells):
    """A covering set node over `cells` (list of (row,col)); each cell -within-> set."""
    s = agent.s.add_node("CellSet", {"n": len(cells)})
    for (r, c) in cells:
        cell = agent.s.add_node("ShapeCell", {"row": int(r), "col": int(c)})
        agent.inner.add_edge_unchecked(cell, "within", s)
    return s


def run(max_repair=3):
    agent = WorldAdapter(seeds=()); load_all_seeds(agent)

    # 1. INTROSPECT
    imp = agent.s.add_node("Impasse", {"reason": "avatar_tracking",
        "question": "the eye splits/merges my avatar so its centroid drow/dcol is corrupt; I need a "
                    "descriptor that says whether a cell-set shifted by my action's known displacement "
                    "lands on the next frame — overlap over conserved cell-sets, not fragile regions."})
    print("GAP:", agent.s.node(imp)["attrs"]["question"], flush=True)

    # 2. PERCEIVE — synthetic prev/now cell-sets
    prev = make_set(agent, [(5, 5), (5, 6), (6, 5), (6, 6)])           # a 2x2 block last frame
    now_up = make_set(agent, [(4, 5), (4, 6), (5, 5), (5, 6)])         # AVATAR: same block, moved UP 1
    now_meter = make_set(agent, [(6, 5), (6, 6)])                      # METER: shrank in place (no shift)
    now_split = make_set(agent, [(4, 5), (4, 6), (5, 5)])             # avatar moved up but eye dropped a cell
    print("test sets: prev(2x2), now_up(moved up 1), now_meter(shrank in place), now_split(moved up, 1 cell lost)",
          flush=True)

    ask = make_ask(timeout=300.0, preamble="")
    prior = ""
    for attempt in range(1, max_repair + 2):
        print(f"\n--- consult attempt {attempt} ---", flush=True)
        reply = ask(QUESTION.format(prims=PRIMS, err=prior))
        m = re.search(r"@@@term\s*(.+?)\s*@@@end", reply or "", re.DOTALL)
        if not m:
            prior = "\n\nReturn ONLY the JSON between @@@term and @@@end."; print("unusable reply", flush=True); continue
        try:
            term = json.loads(m.group(1).strip())
        except Exception as e:
            prior = f"\n\nYour JSON did not parse: {e}. Return valid JSON only."; print("bad json:", e, flush=True); continue

        def po(prev_s, now_s, dr, dc):
            return float(agent.inner.evaluate(term, {"prev": prev_s, "now": now_s, "drow": dr, "dcol": dc}))
        try:
            up_at_up   = po(prev, now_up, -1, 0)     # moved up, tested at Up's displacement -> HIGH
            up_at_zero = po(prev, now_up, 0, 0)       # moved up, tested at no-shift           -> LOWER
            meter_at_up = po(prev, now_meter, -1, 0)  # shrank in place, tested at Up           -> LOW
            split_at_up = po(prev, now_split, -1, 0)  # moved up, 1 cell lost                   -> HIGH-ish
        except Exception as e:
            prior = f"\n\nEvaluating your term raised: {type(e).__name__}: {e}. Fix the term."
            print("eval raised:", e, flush=True); continue
        print(f"  predicted_overlap: moved@Up={up_at_up:.3f} moved@no-shift={up_at_zero:.3f} "
              f"meter@Up={meter_at_up:.3f} split@Up={split_at_up:.3f}", flush=True)
        agent.s.add_node("TaughtHint", {"question": "predicted_overlap", "answer": json.dumps(term)[:4000]})

        # VERIFY: the real translation pops at its displacement; in-place change and wrong-shift don't
        ok = (up_at_up >= 0.8 and meter_at_up <= 0.3 and up_at_up > up_at_zero + 0.2
              and split_at_up >= 0.6)
        if ok:
            agent.register_concept("predicted_overlap", term)
            agent.s.add_node("Concept", {"name": "predicted_overlap", "domain": "perception",
                "provenance": "jabberwock-authored: prediction-matched overlap over cell-sets for avatar tracking"})
            seed = {"id": "avatar_tracking", "version": "1.0.0", "depends_on": ["region_grouping"],
                    "description": "The jabberwock's self-authored `predicted_overlap`: the fraction of a "
                    "prev cell-set that, shifted by an action's known displacement (drow,dcol), lands on the "
                    "now cell-set. Anchors avatar identity/tracking to KNOWN MOTION over conserved cell-sets, "
                    "robust to the eye splitting/merging regions. The basis for motion-action-correlation "
                    "avatar tracking (avatar_correlate / avatar_track_advance / is_translation).",
                    "nodes": [], "edges": [], "productions": [],
                    "concepts": [{"name": "predicted_overlap", "domain": "perception", "definition": term}]}
            with open("seeds/avatar_tracking.json", "w") as fh:
                json.dump(seed, fh, indent=2)
            print("\n✓ the jabberwock AUTHORED `predicted_overlap`, composed from its own primitives and "
                  "verified: a real translation overlaps HIGH at its action's displacement, an in-place "
                  "shrink (meter) and a wrong shift overlap LOW, and a split (1 cell lost) still reads HIGH.",
                  flush=True)
            print("  persisted to seeds/avatar_tracking.json", flush=True)
            return True
        prior = (f"\n\nYour term ran but FAILED. Required: moved@Up>=0.80 (got {up_at_up:.3f}), "
                 f"meter@Up<=0.30 (got {meter_at_up:.3f}), moved@Up > moved@no-shift+0.2 "
                 f"(got {up_at_up:.3f} vs {up_at_zero:.3f}), split@Up>=0.60 (got {split_at_up:.3f}). "
                 f"It must count prev cells whose (row+drow,col+dcol) equals some now cell, over Count(prev).")
        print("verify failed; feeding back.", flush=True)
    print("\n✗ did not land a verified term.", flush=True)
    return False


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
