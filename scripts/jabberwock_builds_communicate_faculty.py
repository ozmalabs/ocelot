"""HAVE THE JABBERWOCK BUILD the communicate-on-instruction faculty ITSELF. I only frame the concern.

The concern, in the agent's grounding vocabulary: when it is told to DESCRIBE what it sees, then FOR EACH
thing it recognises it should MINT A SUBGOAL whose action is to PRODUCE AN UTTERANCE, and BUILD that
utterance FROM the recognition, through its language system. That is the communicate-action wired to
perception + goal decomposition.

The agent's own machinery does the building:
  induce_concern        — observe the concern's structure; if no held term-shape covers it, MINT it as a
                          CapabilityAxis (residual predicates).
  learn_term_for_concern— match the concern's signature to a held TERM-FAMILY (its own decision).
  ground_concern        — compose a callable term from held machinery (or honestly report the wall).

Whatever it grounds is ITS build; whatever it can't is an honest null pointing at the missing vocabulary
(the established fix: teach the missing RelationCues, then re-drive — not author it in Python). donkey=0.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_builds_communicate_faculty.py
"""
from __future__ import annotations
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains.reflective_faculty import induce_concern, learn_term_for_concern, ground_concern, reflect


def main():
    a = WorldAdapter(seeds=()); load_all_seeds(a)
    donkey = {"n": 0}; a.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])
    s = a.s

    print("=" * 92)
    print("THE JABBERWOCK BUILDS THE COMMUNICATE-ON-INSTRUCTION FACULTY ITSELF — I only frame the concern")
    print("=" * 92)

    # FRAME THE CONCERN (the agent's grounding vocabulary — relation tuples it perceives the shape of):
    obs = [
        ["told", "DESCRIBE", "what", "SEEN"],        # the instruction: describe what is seen
        ["for_each", "PERCEPT", "mint", "SUBGOAL"],   # decompose: a subgoal per recognised thing
        ["SUBGOAL", "produces", "UTTERANCE"],         # the subgoal's action is to produce an utterance
        ["build", "UTTERANCE", "from", "RECOGNITION"],# the content comes from what it recognised
    ]
    ind = induce_concern(a, obs, name_hint="communicate_what_i_see")
    key = ind.get("capability_key")
    learned = learn_term_for_concern(a, [key]) if key else {}
    grounded = ground_concern(a, [key]) if key else {}
    design = reflect("self_design", "communicate what I see when told to describe it", s)

    print(f"\n  [induce]  minted={ind.get('minted')}  residual_predicates={ind.get('residual_predicates')}")
    print(f"  [learn]   recognised term-family: {learned.get('term_family')}  "
          f"(shared_leaves={learned.get('shared_leaves')})")
    print(f"  [ground]  grounded={grounded.get('grounded')}  form={grounded.get('form')}")
    if grounded.get("grounded"):
        print(f"            term it built: {str(grounded.get('term'))[:200]}")
    else:
        print(f"            wall: {grounded.get('frontier') or grounded.get('reason')}")
    print(f"  [design]  composable machinery: {design.get('composable_machinery')}")
    if design.get("authored_plan"):
        print(f"            authored plan: {design.get('authored_plan')}")
    print(f"\n  donkey (LLM calls): {donkey['n']}")
    print("=" * 92)
    if grounded.get("grounded"):
        print("  The jabberwock GROUNDED the faculty from its own held machinery — its build, not mine.")
    else:
        print("  Honest null: it RECOGNISED the concern's shape but its relation lexicon lacks the cue(s) to")
        print("  ground it to a callable term. The faithful next step (the established pattern) is to TEACH it")
        print("  the missing relations as graph data, then RE-DRIVE — so it grounds and builds it itself.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
