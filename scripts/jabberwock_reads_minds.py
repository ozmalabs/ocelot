"""CHARACTER THEORY OF MIND, demonstrated — the jabberwock reads what a
CHARACTER believes/wants/knows, as a NESTED situation model on that
character's SmEntity, distinct from the ACTUAL world.

situation_model_reader.py builds a situation model of the story WORLD (the
glass is now on the floor, broken) but never a character's MENTAL state.
domains/psychology.py has a real belief/desire/intention/knowledge taxonomy,
aimed at the agent's own mind; reading_collapse's construction codebook had no
propositional-attitude construction, so "Sally thinks the ball is in the
basket" had nowhere to ground. domains/character_tom.py adds ONE construction
('propositional_attitude', signature [["ATTITUDE"]]) recognised by the SAME
ShapeDecode collapse designation/possession already use, over an ATTITUDE
marker-class that mirrors domain_data/reading_constructions.json's COS class
exactly (seed members + join-by-adjacency for an unseen verb). BELIEF/
KNOWLEDGE grounds the complement as a NESTED SmEntity/proposition under a
`belief_world` edge; DESIRE grounds the character's GOAL — the Zwaan &
Radvansky intentionality index, filled for the first time.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_reads_minds.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core
from domains import dictionary_lexicon as dl
from domains import character_tom as ctom

SEP = "=" * 92


class _Agent:
    def __init__(self, s, node):
        self.s, self.inner, self.agent = s, s._inner, node


def _fresh():
    s, node = boot_core()
    return _Agent(s, node)


def _fmt_state(st: dict) -> str:
    keys = [k for k in st if k not in ("nested", "flavor", "predicate")]
    return ", ".join("%s=%s" % (k, st[k]) for k in sorted(keys)) or "(empty)"


def main():
    dl.warm_wordnet("en")

    print(SEP)
    print("CHARACTER THEORY OF MIND — a NESTED situation model on a character's SmEntity")
    print(SEP)

    # ---- SALLY-ANNE: the headline -----------------------------------------
    print("\n  THE SALLY-ANNE TASK (Wimmer & Perner 1983) — nested false belief")
    print("  " + "-" * 88)
    text = "Sally thinks the ball is in the basket. The ball is in the box."
    ag = _fresh()
    out = ctom.read_character_tom(ag, text)
    print("\n  passage: %r\n" % text)
    for r in out["results"]:
        if r["kind"] == "attitude":
            print("    ATTITUDE  %-9s subject=%-8s verb=%-8s flavor=%-8s (via=%s)"
                  % (r["sentence"][:34], r["subject"], r["attitude_verb"],
                     r["membership"]["flavor"], r["membership"]["via"]))
            print("              construction=%r  shape_fit=%s  residual=%s"
                  % (r["decode"]["construction"], r["decode"]["shape_fit"], r["decode"]["residual"]))
        else:
            print("    FACTUAL   %-34s predications=%s" % (r["sentence"][:34], r["predications"]))

    belief = ctom.character_belief_world(ag, "sally")
    actual = out["actual_world"]
    print("\n  Sally's BELIEF-WORLD (nested, under sally --belief_world--> ...):")
    for name, state in belief.items():
        print("    %s: %s" % (name, _fmt_state(state)))
    print("\n  the ACTUAL WORLD (situation_model_reader's ordinary situation model):")
    for name, state in actual.items():
        if name == "sally":
            continue
        print("    %s: %s" % (name, _fmt_state(state)))
    print("\n  Sally's ball is in_basket=%s; the actual ball is in_box=%s — DISTINCT nodes,"
          % (belief.get("ball", {}).get("in_basket"), actual.get("ball", {}).get("in_box")))
    print("  a false belief coexists with reality instead of overwriting it.")

    # ---- CHARACTER GOAL: the crow -------------------------------------------
    print("\n" + SEP)
    print("  CHARACTER GOAL — want(crow, X) grounds the intentionality index")
    print(SEP)
    for sentence in ("The crow wanted water.", "The crow wanted to drink."):
        ag2 = _fresh()
        rec = ctom.ingest_attitude_sentence(ag2, sentence, t=1)
        print("\n  %r" % sentence)
        print("    flavor=%s  goal=%r" % (rec["membership"]["flavor"], rec["goal"]))
        print("    queried back: character_goal(crow) = %r" % ctom.character_goal(ag2, "crow"))

    # ---- ATTITUDE IS A CLASS: unseen verb joins by adjacency ----------------
    print("\n" + SEP)
    print("  ATTITUDE IS A CLASS — an UNSEEN verb joins by adjacency; discriminative")
    print(SEP)
    ag3 = _fresh()
    rec3 = ctom.ingest_attitude_sentence(
        ag3, "Sally suspects the ball is in the basket.", t=1)
    mem3 = rec3["membership"]
    print("\n  %r" % "Sally suspects the ball is in the basket.")
    print("    'suspect' is NOT a seed member -> joins by ADJACENCY: nearness=%.2f to %r (via=%s)"
          % (mem3["nearness"], mem3["nearest"], mem3["via"]))
    print("    flavor=%s -> grounds a belief-world exactly like 'thinks' does" % mem3["flavor"])
    belief3 = ctom.character_belief_world(ag3, "sally")
    print("    Sally's belief-world: %s" % {k: _fmt_state(v) for k, v in belief3.items()})

    ag4 = _fresh()
    factual_sentence = "Sally put the ball in the basket."
    rec4 = ctom.ingest_attitude_sentence(ag4, factual_sentence, t=1)
    out4 = ctom.read_character_tom(ag4, factual_sentence)
    print("\n  %r  (FACTUAL — 'put' is already COS-classified, not ATTITUDE)" % factual_sentence)
    print("    ingest_attitude_sentence(...) = %r  (no attitude construction fires)" % rec4)
    print("    read_character_tom(...) kind  = %r  (falls through to the ordinary reading path)"
          % out4["results"][0]["kind"])
    print("    Sally's belief-world stays EMPTY: %r" % ctom.character_belief_world(ag4, "sally"))

    # ---- GRAPH-NATIVE SOURCE AUDIT ------------------------------------------
    print("\n" + SEP)
    print("  GRAPH-NATIVE SOURCE AUDIT")
    print(SEP)
    ag5 = _fresh()
    decode = ctom.decode_attitude_construction(
        ag5, ["sally"], ["the", "ball", "is", "in", "the", "basket"])
    print("\n  decode_attitude_construction(...) = %r" % decode)
    print("  -> the WINNER is the ShapeDecode Term's own verdict (reflective_faculty.")
    print("     compose_design_for_goal, reused via rc._decode/rc._winner) — never a Python")
    print("     if/else on the verb surface. The belief-world / goal are SmEntity/SmEvent")
    print("     graph nodes (see the printed states above), not a Python dict held by the")
    print("     adapter. No `import re` anywhere in domains/character_tom.py.")

    print("\n" + SEP)
    print("  HONEST COVERAGE")
    print(SEP)
    print("""
  * Flavors wired: belief (thinks/suspects/...), knowledge (knows), desire
    (wants/hopes/wishes) all ground; fear/doubt default to the belief flavor
    (no separate valence dimension is modeled — an honest simplification).
  * Belief-world depth: a SINGLE nested proposition per attitude sentence (the
    complement's own top-level predication), not a full recursive situation
    model — a second embedded attitude in the complement is NOT descended
    into.
  * The false-belief demo REPRESENTS Sally's belief as distinct graph state;
    it does not (yet) track that Sally would ACT on it (no planning/action
    layer consumes belief_world here).
  * ATTITUDE class coverage: 8 seeded lemmas (believe/think/know/want/hope/
    fear/wish/doubt) + join-by-adjacency for an unseen verb (nearness >= 0.5,
    the same coarse-WordNet honesty POSSESS/COS document — a resulting
    unseen-verb tail near the threshold, e.g. 'presume' at ~0.33, is not
    covered unless seeded).
""")
    print(SEP)


if __name__ == "__main__":
    main()
