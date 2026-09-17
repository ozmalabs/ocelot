"""Block 348 verification — regulated train of thought on the DISCRETE-QUANTA premise.

Teacher-free, pure graph. Exercises BOTH halves of the control law in QUANTIZED terms:
  (A) NARROW tube, trajectory INSIDE  -> width NARROWS (focus), converges.
  (B) tube the trajectory is OUTSIDE (start 'poodle', tube = the bird branch) -> width
      WIDENS step-by-step and the INTEGER deviation FALLS as widening steers toward tube.
Run: PYTHONPATH=runners/dsl/python:. python3 scripts/_verify_block348_regulated.py
"""
from __future__ import annotations

import json

from substrate_rs import _native

from domains import llm_knowledge_seed as ks
from domains import train_of_thought as tot
from domains import regulated_train_of_thought as rtot


class AskSpy:
    def __init__(self):
        self.calls = []

    def __call__(self, topic):
        self.calls.append(topic)
        return {"answered_by": "external", "topic": topic}


def _seed():
    s = _native.Substrate()
    ks.build_knowledge_mt(s, ["seeds/can_native_reimplementation.json"],
                          [("poodle", "dog"), ("beagle", "dog"), ("dog", "mammal"),
                           ("cat", "mammal"), ("mammal", "animal"),
                           ("sparrow", "bird"), ("robin", "bird"), ("bird", "animal"),
                           ("animal", "organism")],
                          relation="isa")
    ag = s.add_node("Agent", {"name": "jabberwock"})
    sc = s.add_node("SelfConcern", {"status": "noted", "source": "implicit",
                                    "kind": "knowledge", "content": "poodle"})
    s.add_edge_unchecked(ag, "has_self_concern", sc)
    return s


def main() -> int:
    print("=" * 74)
    print("REGULATED TRAIN OF THOUGHT — discrete-quanta control law (block 348)")
    print("=" * 74)

    # (A) NARROW tube, trajectory INSIDE -> NARROW/converge. Tube = poodle's own
    #     is-a cone; start on poodle so the trajectory stays inside.
    sA = _seed()
    spyA = AskSpy()
    rA = rtot.run_regulated_train_of_thought(
        sA, topic="poodle", width0=1, turns_per_segment=3, max_segments=6,
        on_unknown="return", ask_fn=spyA)
    print("\n(A) narrow tube, trajectory INSIDE (tube = poodle is-a cone):")
    print("    tube_region   : %s" % rA["tube_region"])
    print("    width_trace   : %s  (integer quanta)" % rA["width_trace"])
    print("    deviation_trace: %s  (integer counts)" % rA["deviation_trace"])
    print("    stop=%s  ask_spy=%d" % (rA["stop_reason"], len(spyA.calls)))
    wtA = rA["width_trace"]
    # inside tube: deviation stays low, width does not climb (narrows or holds at floor)
    a_all_int = all(isinstance(x, int) for x in wtA + rA["deviation_trace"])
    a_narrows = (len(wtA) >= 1 and wtA[-1] <= wtA[0])
    a_teacher_free = (len(spyA.calls) == 0)
    print("    -> width non-increasing (focus): %s ; teacher-free: %s ; all-int: %s"
          % (a_narrows, a_teacher_free, a_all_int))

    # (B) tube the trajectory is OUTSIDE: start 'poodle', tube = the BIRD branch
    #     region -> width WIDENS step by step and integer deviation FALLS.
    sB = _seed()
    spyB = AskSpy()
    bird_region = {"bird", "sparrow", "robin"} | set(tot.transitive_ancestors(sB, "bird"))
    rB = rtot.run_regulated_train_of_thought(
        sB, topic="poodle", tube_region=set(bird_region),
        width0=0, deviation_wide_quanta=1, deviation_converge_quanta=0,
        turns_per_segment=3, max_segments=8, on_unknown="return", ask_fn=spyB)
    print("\n(B) tube OUTSIDE the start (start=poodle, tube = bird branch):")
    print("    tube_region    : %s" % rB["tube_region"])
    print("    width_trace    : %s  (integer quanta)" % rB["width_trace"])
    print("    deviation_trace: %s  (integer counts)" % rB["deviation_trace"])
    print("    stop=%s  ask_spy=%d" % (rB["stop_reason"], len(spyB.calls)))
    wtB = rB["width_trace"]
    dtB = rB["deviation_trace"]
    b_all_int = all(isinstance(x, int) for x in wtB + dtB)
    b_widens = (len(wtB) >= 2 and wtB[-1] > wtB[0])          # width steps up
    b_dev_falls = (len(dtB) >= 2 and dtB[-1] < max(dtB))     # integer deviation falls
    b_teacher_free = (len(spyB.calls) == 0)
    print("    -> width widens step-by-step: %s ; deviation falls: %s ; "
          "teacher-free: %s ; all-int: %s"
          % (b_widens, b_dev_falls, b_teacher_free, b_all_int))

    ok = (a_narrows and a_teacher_free and a_all_int
          and b_widens and b_dev_falls and b_teacher_free and b_all_int)
    print("\nVERDICT: %s" % ("BLOCK 348 CONTROL LAW PASS (both halves, quantized)"
                             if ok else "FALSIFIED (see above)"))
    print("SUMMARY_JSON " + json.dumps({
        "A_width_trace": wtA, "A_deviation_trace": rA["deviation_trace"],
        "A_stop": rA["stop_reason"], "A_narrows": a_narrows,
        "B_width_trace": wtB, "B_deviation_trace": dtB,
        "B_stop": rB["stop_reason"], "B_widens": b_widens, "B_dev_falls": b_dev_falls,
        "all_integer_traces": bool(a_all_int and b_all_int),
        "teacher_calls": len(spyA.calls) + len(spyB.calls)}))
    print("=" * 74)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
