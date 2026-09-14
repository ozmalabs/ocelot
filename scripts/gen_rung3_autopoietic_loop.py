"""Block 345000 — RUNG 3: the autopoietic loop closes teacher-free over held knowledge.

The generation arc's culmination: the entity converses with ITSELF with no external
teacher in the cycle, over knowledge it ALREADY holds — select a topic (curiosity),
self-answer it from held is-a edges via the grammar-owned realizer, monitor its own
answer (parse-back), and enqueue what it could not recover (the residual) as the next
gap. HONESTLY BOUNDED: genuinely-unknown topics have nothing to derive from, so the
loop does NOT fabricate — for those the external ASK floor remains, and whether to
invoke it is the caller's CHOICE (on_unknown).

Falsifiable claims (a SPY counts every external-answerer call):
  C1  AUTONOMOUS SELECTION: given a substrate pre-seeded with is-a knowledge and a
      filed knowledge SelfConcern, run_autopoietic_step selects that topic with no
      external topic injection.
  C2  TEACHER-FREE CLOSURE: the held-knowledge self-answer produces a grammar-realized
      clause, parse-back recoverable==True coverage>=1.0, and the external answerer
      (ask spy) is called ZERO times.
  C3  RESIDUAL -> NEXT GAP: a residual concept is filed as a new SelfConcern that
      reflective_faculty._run_self_gaps then surfaces — still no external call this step.
  C4  HONESTY FALSIFIER: with EMPTY held knowledge for a topic, self_answer returns
      answered=False / reason='no_held_knowledge' and fabricates NO clause.
  C5  RETURN-vs-ASK IS CHOOSABLE: on an unknown topic, on_unknown='ask' invokes the
      ask spy (once); on_unknown='return' does NOT — the choice point is real.

Pure graph, teacher-free grounding (no LLM), no substrate .so write path. Run:
  PYTHONPATH=runners/dsl/python:. python3 scripts/gen_rung3_autopoietic_loop.py
"""
from __future__ import annotations

import json

from substrate_rs import _native

from domains import llm_knowledge_seed as ks
from domains import self_dialogue as sd
from domains import reflective_faculty as rf


class AskSpy:
    """Counts external-answerer invocations — the teacher floor we must NOT touch on
    the held-knowledge path."""
    def __init__(self):
        self.calls = []

    def __call__(self, topic):
        self.calls.append(topic)
        return {"answered_by": "external_teacher", "topic": topic}  # stub


def _seed_world():
    s = _native.Substrate()
    # HELD knowledge (build_knowledge_mt, substrate-only at query time)
    ks.build_knowledge_mt(s, ["seeds/can_native_reimplementation.json"],
                          [("poodle", "dog"), ("dog", "mammal"),
                           ("sparrow", "bird"), ("bird", "animal")],
                          relation="isa")
    ag = s.add_node("Agent", {"name": "jabberwock"})
    # a filed curiosity concern (what curiosity autonomously chose to pursue)
    sc = s.add_node("SelfConcern", {"status": "noted", "source": "implicit",
                                    "kind": "knowledge", "content": "poodle"})
    s.add_edge_unchecked(ag, "has_self_concern", sc)
    return s


def main() -> int:
    print("=" * 74)
    print("RUNG 3 — autopoietic loop closes teacher-free over held knowledge (blk 345)")
    print("=" * 74)
    s = _seed_world()
    spy = AskSpy()

    # C1 + C2: autonomous selection + teacher-free closure.
    rec = sd.run_autopoietic_step(s, on_unknown="ask", ask_fn=spy)
    c1 = (rec["topic"] == "poodle")
    c2 = (rec["answered"] and rec["surface"]
          and (rec["verdict"] or {}).get("recoverable") is True
          and (rec["verdict"] or {}).get("coverage", 0) >= 1.0
          and rec["teacher_called"] is False
          and len(spy.calls) == 0)
    print("\nC1 autonomous selection: topic=%r -> %s" % (rec["topic"], c1))
    print("C2 teacher-free closure: surface=%r cov=%s recoverable=%s ask_spy_calls=%d -> %s"
          % (rec["surface"], (rec["verdict"] or {}).get("coverage"),
             (rec["verdict"] or {}).get("recoverable"), len(spy.calls), c2))

    # C3: enqueue a residual and confirm reflective_faculty surfaces it.
    sd.enqueue_residual(s, ["carnivore"])   # a concept the saying did not recover
    gaps = rf._run_self_gaps(s)
    contents = {c["content"] for c in gaps.get("concerns", [])}
    c3 = ("carnivore" in contents and len(spy.calls) == 0)
    print("C3 residual->next gap: 'carnivore' in filed gaps=%s (gaps=%d) ask_spy=%d -> %s"
          % ("carnivore" in contents, gaps.get("count"), len(spy.calls), c3))

    # C4: honesty falsifier — empty held knowledge, NO fabrication.
    ans_unknown = sd.self_answer(s, "unicorn", on_unknown="return")
    c4 = (ans_unknown["answered"] is False
          and ans_unknown.get("reason") == "no_held_knowledge"
          and ans_unknown["surface"] == "")
    print("C4 honesty falsifier (unicorn, no held knowledge): answered=%s reason=%s "
          "surface=%r -> %s" % (ans_unknown["answered"], ans_unknown.get("reason"),
                                ans_unknown["surface"], c4))

    # C5: return-vs-ask is a real choice.
    spy_ret = AskSpy()
    sd.self_answer(s, "griffin", on_unknown="return", ask_fn=spy_ret)
    ret_calls = len(spy_ret.calls)
    spy_ask = AskSpy()
    r_ask = sd.self_answer(s, "griffin", on_unknown="ask", ask_fn=spy_ask)
    ask_calls = len(spy_ask.calls)
    c5 = (ret_calls == 0 and ask_calls == 1 and r_ask.get("source") == "external_ask")
    print("C5 return-vs-ask choosable: on_unknown='return' spy=%d, 'ask' spy=%d "
          "(source=%s) -> %s" % (ret_calls, ask_calls, r_ask.get("source"), c5))

    allpass = c1 and c2 and c3 and c4 and c5
    print("\n--- claims ---")
    for name, ok in [("C1 autonomous selection", c1), ("C2 teacher-free closure", c2),
                     ("C3 residual->next gap", c3), ("C4 honesty falsifier", c4),
                     ("C5 return-vs-ask choosable", c5)]:
        print("  %-30s %s" % (name, "PASS" if ok else "FAIL"))
    verdict = ("RUNG 3 PASS: the autopoietic loop closes teacher-free over HELD "
               "knowledge (select->self-answer->monitor->residual->next gap, zero "
               "external calls); unknown topics do not fabricate; the ASK floor is a "
               "real, choosable option" if allpass else "RUNG 3 FALSIFIED (see above)")
    print("\nVERDICT: %s" % verdict)
    print("=" * 74)
    print("SUMMARY_JSON " + json.dumps({
        "c1": c1, "c2": c2, "c3": c3, "c4": c4, "c5": c5,
        "topic": rec["topic"], "surface": rec["surface"],
        "coverage": (rec["verdict"] or {}).get("coverage"),
        "held_path_teacher_calls": len(spy.calls),
        "note": "closed loop over ALREADY-HELD knowledge; genuinely-unknown topics "
                "need the external floor (choosable on_unknown)"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
