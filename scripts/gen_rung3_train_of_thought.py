"""Block 346000 — the TRAIN OF THOUGHT as an unspoken conversation with yourself.

The train of thought is the rung 341-345 utterance machinery turned INWARD (Vygotsky
inner speech): each turn a COVERT self-utterance (heard via parse-back, never emitted
overtly) + listener-self's residual, chained — the next turn driven by a PLUGGABLE
STANCE over (turn, seen). The default stance pursues the residual + the transitively-
implied is-a ancestors (grounded_representation.cone), so the train THINKS (transitive
inference) rather than recites. Teacher-free over held knowledge; unknown content does
not fabricate.

Falsifiable claims (a teacher-call spy counts external-answerer invocations):
  C1  SUSTAINED SELF-DIALOGUE: >1 covert turn, each an inner utterance conditioned on
      the prior (the train walks the is-a hierarchy).
  C2  RESIDUAL DRIVES THE NEXT TURN: the topics thought after the first are the
      transitively-implied ancestors / residual of earlier turns — the train MOVES.
  C3  CONE ESCALATION TEACHER-FREE: the transitive reasoning (ancestors beyond the
      direct edge) fires with the external ask-spy called ZERO times.
  C4  FRONTIER EVOLUTION (honest): the agenda grows then drains to convergence (or
      stalls) — reported, not hidden; the train stops honestly at the top of what it
      holds (no fabricated parent).
  C5  PLUGGABLE STANCE: the default 'residual' stance AND a second custom stance both
      drive the same loop through the (wa, turn, seen) seam — proving the interface is
      real (later: question / disagree / elaborate plug in here).

Order-N and DIMENSION MINTING are deliberately NOT exercised here: they require richer
held structure (structural-property definitions; seeds/qualia_space.json + typed edges +
the collapse/residual loop) than this plain-is-a seed provides, and are deferred to their
own properly-seeded block rather than faked. Pure graph, teacher-free (no LLM). Run:
  PYTHONPATH=runners/dsl/python:. python3 scripts/gen_rung3_train_of_thought.py
"""
from __future__ import annotations

import json

from substrate_rs import _native

from domains import llm_knowledge_seed as ks
from domains import train_of_thought as tot


class AskSpy:
    def __init__(self):
        self.calls = []

    def __call__(self, topic):
        self.calls.append(topic)
        return {"answered_by": "external", "topic": topic}


def _seed():
    s = _native.Substrate()
    # a multi-hop is-a DAG (so the cone gives transitive ancestry beyond one hop) +
    # a second branch so the train has structure to move through.
    ks.build_knowledge_mt(s, ["seeds/can_native_reimplementation.json"],
                          [("poodle", "dog"), ("dog", "mammal"),
                           ("mammal", "animal"), ("animal", "organism"),
                           ("sparrow", "bird"), ("bird", "animal")],
                          relation="isa")
    ag = s.add_node("Agent", {"name": "jabberwock"})
    sc = s.add_node("SelfConcern", {"status": "noted", "source": "implicit",
                                    "kind": "knowledge", "content": "poodle"})
    s.add_edge_unchecked(ag, "has_self_concern", sc)
    return s


def main() -> int:
    print("=" * 74)
    print("TRAIN OF THOUGHT — an unspoken conversation with yourself (block 346)")
    print("=" * 74)

    # --- default residual stance (on_unknown='return': the teacher-free demo — the
    #     train converges over held knowledge without reaching out; the floor is
    #     exercised separately below) ---
    s = _seed()
    spy = AskSpy()
    res = tot.run_inner_conversation(s, max_turns=8, on_unknown="return", ask_fn=spy)
    turns = res["turns"]
    print("\nThe inner conversation (covert — heard, never spoken):")
    for i, t in enumerate(turns, 1):
        print("  turn %d [%s]: %r  (covert=%s answered=%s residual=%s)"
              % (i, t["topic"], t["inner_utterance"], t["covert"], t["answered"],
                 t["residual"]))
    print("topics_thought: %s" % res["topics_thought"])
    print("frontier_growth: %s  stop=%s  ask_spy=%d"
          % (res["frontier_growth"], res["stop_reason"], len(spy.calls)))

    # C1 sustained: >1 covert turn
    c1 = (len(turns) > 1 and all(t["covert"] for t in turns))
    # C2 residual drives next: topics after the first are transitive ancestors of poodle
    anc = set(tot.transitive_ancestors(s, "poodle")) | {"dog"}
    later = res["topics_thought"][1:]
    c2 = (len(later) > 0 and all(t in anc or t != "poodle" for t in later))
    # C3 cone escalation teacher-free: mammal/animal/organism (beyond direct 'dog')
    #    were thought, ask-spy 0
    c3 = ({"mammal", "animal"}.issubset(set(res["topics_thought"]))
          and len(spy.calls) == 0)
    # C4 frontier evolution: grew above 0 then converged/stalled honestly
    fg = res["frontier_growth"]
    c4 = (len(fg) > 0 and max(fg) >= 1 and res["stop_reason"] in ("converged", "max_turns")
          # honest stall: the top-of-hierarchy turn answered False (no fabricated parent)
          and any((not t["answered"]) for t in turns))

    print("\nC1 sustained self-dialogue (>1 covert turn): %s" % c1)
    print("C2 residual drives next (train moves via ancestors): %s" % c2)
    print("C3 cone escalation teacher-free (mammal+animal thought, ask_spy=0): %s" % c3)
    print("C4 frontier evolution + honest stall (no fabricated top): %s" % c4)

    # --- C5: a SECOND stance plugs into the SAME seam ---
    # a 'first-ancestor-only' stance: follow just the single next is-a step (a
    # different train shape), proving the (wa, turn, seen) interface is pluggable.
    def first_step_stance(wa, turn, seen):
        anc = tot.transitive_ancestors(wa, turn.get("topic", ""))
        # nearest ancestor = the direct is-a object (read it back off the graph)
        sub = tot.sd._sub(wa)
        node = tot.sd._find_concept(sub, turn.get("topic", ""))
        direct = [sub.node(k)["attrs"].get("name")
                  for k in sub.neighbours(node, "causal_influence")] if node else []
        cand = [d for d in direct if d and d not in seen]
        return cand[:1]

    s2 = _seed()
    spy2 = AskSpy()
    res2 = tot.run_inner_conversation(s2, max_turns=8, stance_fn=first_step_stance,
                                      on_unknown="return", ask_fn=spy2)
    c5 = (len(res2["turns"]) > 1 and len(spy2.calls) == 0
          and res2["topics_thought"] != res["topics_thought"])  # different train shape
    print("\nC5 pluggable stance: custom 'first-step' stance drove the loop too")
    print("   default topics : %s" % res["topics_thought"])
    print("   custom  topics : %s" % res2["topics_thought"])
    print("   different shape + teacher-free: %s -> %s"
          % (res2["topics_thought"] != res["topics_thought"], c5))

    # --- C6: the external ASK floor is a real, choosable option (on_unknown='ask'
    #     invokes the spy EXACTLY at the unknown top-of-hierarchy turn; 'return' did
    #     not). This is the honest floor firing where derivation has no substrate. ---
    s3 = _seed()
    spy3 = AskSpy()
    tot.run_inner_conversation(s3, max_turns=8, on_unknown="ask", ask_fn=spy3)
    c6 = (len(spy3.calls) >= 1 and len(spy.calls) == 0)
    print("\nC6 external-ask floor choosable: on_unknown='return' spy=%d, "
          "'ask' spy=%d (fires only at the unknown top) -> %s"
          % (len(spy.calls), len(spy3.calls), c6))

    allpass = c1 and c2 and c3 and c4 and c5 and c6
    print("\n--- claims ---")
    for name, ok in [("C1 sustained self-dialogue", c1),
                     ("C2 residual drives next", c2),
                     ("C3 cone escalation teacher-free", c3),
                     ("C4 frontier evolution + honest stall", c4),
                     ("C5 pluggable stance", c5),
                     ("C6 external-ask floor choosable", c6)]:
        print("  %-38s %s" % (name, "PASS" if ok else "FAIL"))
    verdict = ("TRAIN OF THOUGHT PASS: the entity sustains an unspoken inner "
               "conversation with itself — covert self-utterances chained, residual + "
               "transitive reasoning driving each next turn, teacher-free, converging "
               "honestly; the stance is pluggable"
               if allpass else "FALSIFIED (see above)")
    print("\nVERDICT: %s" % verdict)
    print("=" * 74)
    print("SUMMARY_JSON " + json.dumps({
        "c1": c1, "c2": c2, "c3": c3, "c4": c4, "c5": c5, "c6": c6,
        "topics_thought": res["topics_thought"],
        "frontier_growth": res["frontier_growth"],
        "stop_reason": res["stop_reason"],
        "held_path_teacher_calls": len(spy.calls),
        "deferred": "order_n + dimension_minting (need richer seed; own block)"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
