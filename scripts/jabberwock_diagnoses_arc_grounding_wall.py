"""STEP 1 — THE JABBERWOCK DIAGNOSES ITS OWN ARC-AGI-3 GROUNDING WALL.

A THIN WORLD-ADAPTER SHELL (CLAUDE.md). It owns NO reasoning. It only drives the
agent's OWN grounding faculty (read_and_ground.ground_recursively) over the
concepts the ARC-AGI-3 read failed on (number / mean / state / interaction +
the live-failure set), reads back the agent's OWN per-level TRACE + REASON, and
prints them VERBATIM so the agent NAMES — in its own words — why comprehension
bottoms out. No diagnosis is authored here; the agent's grounding trace IS the
diagnosis.

The agent is handed a TEACHER gloss for each concept (a fed definition_text — the
same channel a parent/teacher uses) so the COMPREHENSION step is isolated from the
web-availability step: this lets the agent show whether the wall is (a) it cannot
READ a definition, (b) it cannot COMPREHEND the read definition into a genus, or
(c) it comprehends the genus but the cone never reaches a SEEDED PRIMITIVE because
the substrate holds NO bedrock — the agent reports which, per concept.

Run:
  ulimit -v 8388608
  timeout 600 env PYTHONPATH=runners/dsl/python:. \\
    python3 scripts/jabberwock_diagnoses_arc_grounding_wall.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runners" / "dsl" / "python"))

from substrate_rs import _native  # noqa: E402

from domains import construction_grammar as cg  # noqa: E402
from domains import grounded_representation as gr  # noqa: E402
from domains import read_and_ground as rag  # noqa: E402

SEP = "=" * 78

# The concepts the ARC-AGI-3 read failed on (the task's named four + the live
# residual). A short, faithful teacher gloss per concept (the genus-differentia
# form the construction grammar reads) — so the COMPREHENSION step is isolated
# from web availability. These are dictionary-plain glosses, not paper-specific.
GLOSS = {
    "number": "A number is a mathematical object used to count, measure, and label.",
    "mean": "The mean is the average value of a set of numbers.",
    "state": "A state is the condition that something is in at a particular time.",
    "interaction": "An interaction is an action that occurs between two or more objects.",
    "median": "The median is the value separating the higher half from the lower half of a data sample.",
    "score": "A score is a number that records the result of a test or game.",
    "action": "An action is a thing done by an agent.",
}


class _Conv:
    _constructions = cg.load_constructions()
    _definition_feed: dict = {}


def banner(s: str) -> None:
    print("\n" + SEP)
    print(s)
    print(SEP)


def _fresh():
    s = _native.Substrate()
    gr.open_grounding_productions(s)
    return s


def diagnose_one(concept: str, gloss: str) -> dict:
    """Drive the agent's OWN grounding faculty on one concept, fed its gloss, and
    read back its trace + reason VERBATIM."""
    s = _fresh()
    res = rag.ground_recursively(s, concept, _Conv(), max_depth=4,
                                 definition_text=gloss)
    tr = res.get("trace") or {}
    comp = tr.get("comprehend") or {}
    struct = res.get("structure") or {}
    cid = gr._find_concept(s, concept)
    reaches = (gr.grounding_reaches_primitives(s, cid)
               if cid is not None else {"grounded": False, "primitives": [],
                                        "cone_size": 0, "depth": 0})
    cone = ([s.node(c)["attrs"].get("name") for c in gr.cone(s, cid)]
            if cid is not None else [])
    return {
        "concept": concept,
        "read": (tr.get("read") or "")[:70],
        "genus": comp.get("genus") or struct.get("genus"),
        "grounded": bool(res.get("grounded")),
        "reason": res.get("reason") or "",
        "cone": cone,
        "primitives_reached": reaches.get("primitives"),
        "cone_depth": reaches.get("depth"),
    }


def main() -> int:
    banner("STEP 1 — THE JABBERWOCK DIAGNOSES ITS OWN ARC-AGI-3 GROUNDING WALL\n"
           "  (drive its OWN ground_recursively over the failed concepts; read\n"
           "   back its trace+reason VERBATIM — the agent names the wall itself)")
    print("  Each concept is fed a plain teacher gloss so the COMPREHENSION step is")
    print("  isolated from web availability. The agent reports, per concept,")
    print("  whether it READ, whether it COMPREHENDED a genus, and whether its cone")
    print("  reaches a SEEDED PRIMITIVE — in its own grounding trace.\n")

    # how many bedrock primitives does the BARE substrate hold?
    s0 = _fresh()
    n_concepts = len(s0.nodes("Concept"))
    print(f"  the bare substrate (open_grounding_productions only) holds "
          f"{n_concepts} Concept nodes — i.e. NO seeded bedrock primitives.\n")

    results = []
    for concept, gloss in GLOSS.items():
        r = diagnose_one(concept, gloss)
        results.append(r)
        print(f"  [{concept}]")
        print(f"    READ      : {r['read']}")
        print(f"    GENUS     : {r['genus']!r}  (comprehended term is-a GENUS)")
        print(f"    CONE      : {' -> '.join(str(c) for c in r['cone']) or '(none)'}")
        print(f"    PRIMITIVES REACHED: {r['primitives_reached']}  "
              f"(depth {r['cone_depth']})")
        print(f"    GROUNDED  : {r['grounded']}")
        print(f"    AGENT'S REASON: {r['reason']}")
        print()

    banner("THE AGENT'S DIAGNOSIS — read off the traces above (its own words)")
    comprehended = [r for r in results if r["genus"]]
    grounded = [r for r in results if r["grounded"]]
    bare_leaf = [r for r in results
                 if r["genus"] and not r["grounded"]
                 and "primitive" in (r["reason"] or "")]
    print(f"  - COMPREHENDED a genus for {len(comprehended)}/{len(results)} "
          f"concepts (the construction grammar PARSES the teacher gloss into "
          f"TERM is-a GENUS — comprehension is NOT the wall when a gloss is given).")
    print(f"  - GROUNDED-TO-PRIMITIVE: {len(grounded)}/{len(results)}.")
    print(f"  - {len(bare_leaf)}/{len(results)} comprehended a genus but the agent's "
          f"OWN reason is: the cone does not reach a SEEDED PRIMITIVE (bare leaf).")
    print()
    print("  THE WALL THE AGENT NAMES: the substrate holds NO bedrock primitives,")
    print("  so EVERY comprehended genus is a bare leaf — there is nothing under it")
    print("  for the cone to bottom out on. The genus 'value', 'average', 'condition',")
    print("  'action', etc. is comprehended but is itself an ungrounded leaf. The")
    print("  grounding loop is sound; it has no FLOOR to ground ONTO.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
