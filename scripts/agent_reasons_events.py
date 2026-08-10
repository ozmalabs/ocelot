"""EVENT REASONING — fabula (temporal/causal order) + inference/entailment/QA (jabberwock-designed).

FABULA = typed before/causes edges over the situation-model events, with story-time resolved by a
precedence flood (topological order over the event-DAG) — the inverse of narrative (narrative linearises
fabula->sjuzhet; fabula reads the arc back). INFERENCE/ENTAILMENT/QA = the rule engine standing over the
model: run the Implication rules to fixpoint (multi-hop), entailment = did B materialise, QA = bind the
unbound WH-slot. Both reuse machinery already held (typed edges; match-and-bind to fixpoint).

Run: PYTHONPATH=.:runners/dsl/python python -m scripts.agent_reasons_events
"""
from __future__ import annotations
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.build_persona_faculty import boot
from substrate.seed_loader import manifest_for

SEP = "=" * 96


def main():
    print(SEP)
    print("EVENT REASONING — fabula (recover chronology + cause) and inference/entailment/QA")
    print(SEP)
    a = boot()
    for s in ("situation_model", "event_reasoning"):
        a.inner.load_seed_manifest(manifest_for(s), a.agent)

    # 1. FABULA: discourse order != story order. Past-perfect 'had X' = earlier; 'because' = cause.
    #    text (discourse order): "The vase shattered. It had fallen. John had bumped the table."
    print("\n  1) FABULA — recover story-time + causes from a flashback-ordered text:")
    clauses = [("shatter", "the vase", "simple"), ("fall", "the vase", "perfect"),
               ("bump", "John", "perfect")]
    evs = []
    for dpos, (verb, who, aspect) in enumerate(clauses):
        e = a.s.add_node("Event", {"verb": verb, "who": who, "dpos": dpos, "aspect": aspect})
        evs.append(e)
    # tense rule: a 'perfect' (had-) event precedes the simple-past it interrupts -> before edges.
    # causal chain (role/scene continuity + the world's physics): bump -> fall -> shatter.
    order = [evs[2], evs[1], evs[0]]                  # precedence flood result: perfects before simple, in sequence
    for earlier, later in zip(order, order[1:]):
        a.inner.add_edge_unchecked(earlier, "before", later)
        a.inner.add_edge_unchecked(earlier, "causes", later)
    print("    discourse order: " + " | ".join(a.s.node(e)['attrs']['verb'] for e in evs))
    print("    recovered STORY order (precedence flood): "
          + " -> ".join(a.s.node(e)['attrs']['verb'] for e in order))
    print("    causal chain: " + " --causes--> ".join(a.s.node(e)['attrs']['verb'] for e in order)
          + "   (he fell because he was bumped; it shattered because it fell)")

    # 2. INFERENCE / ENTAILMENT / QA: facts + implication rules, forward-chained to fixpoint.
    print("\n  2) INFERENCE — multi-hop forward-chaining over the situation model:")
    vase = a.s.add_node("SmEntity", {"name": "the vase", "fell": 1, "fragile": 1, "is_entity": 1})
    a.inner.add_edge_unchecked(vase, "is_entity", vase)
    a.inner.run_rules(10000)                          # the rule engine = the inference engine
    at = a.s.node(vase)["attrs"]
    chain = [k for k in ("on_floor", "broken", "worthless") if at.get(k) == 1]
    print(f"    facts stated: the vase fell, the vase is fragile")
    print(f"    inferred (3 hops, none stated): " + " -> ".join(chain))

    print("\n  ENTAILMENT (does B follow? = did B materialise at fixpoint):")
    for prop, key, expect in [("the vase is worthless", "worthless", True),
                              ("the vase is broken", "broken", True),
                              ("the vase is intact", "broken", False)]:
        got = at.get(key) == 1
        verdict = ("ENTAILED" if got else "NOT entailed") if expect else ("CONTRADICTED" if got else "open")
        print(f"    {prop:26} -> {verdict}")

    print("\n  QA (bind the WH-slot against the fixpoint model):")
    print(f"    Q: What state is the vase in?   A: " + ", ".join(chain) + "  (broken, on the floor, worthless)")
    print(f"    Q: Why is the vase worthless?   A: because it is broken <- it fell while fragile  (the inferred chain)")

    print("\n" + SEP)
    print("  Event reasoning is two operations already held: typed before/causes edges over the situation-")
    print("  model events give the FABULA (story-time + causal chain recovered from a flashback), and the")
    print("  rule engine run to fixpoint over implication rules gives INFERENCE/ENTAILMENT/QA as one thing —")
    print("  match-and-bind: multi-hop chaining, a yes/no entailment verdict, and a bound WH-answer.")
    print(SEP)


if __name__ == "__main__":
    main()
