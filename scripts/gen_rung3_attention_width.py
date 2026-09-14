"""Block 347000 — attention-width: the goal-directed<->associative axis + honest termination.

Two fidelity fixes the consciousness/inner-speech literature review flagged for the
train of thought (block 346):

  #1 ASSOCIATIVE transitions blended with goal-directed. Real trains of thought are not
     one regime: they blend deliberately-constrained goal-directed transitions with
     associative/spreading-activation flights (James's substantive vs transitive parts;
     Christoff et al.'s deliberate<->automatic continuum; Bar associative, Dolan/Dayan
     model-based). Implemented as a single continuous ATTENTION-WIDTH axis in [0,1] —
     the graph-walk analogue of aperture (a DISTINCT axis; aperture resolves a field,
     this sets neighbourhood breadth): 0 = goal-directed (is-a spine), 1 = associative
     (wander siblings / children / any-relation neighbours).

  #3 HONEST TERMINATION. A train that only stops when its agenda empties is a RUMINATION
     engine (Nolen-Hoeksema: pathological non-termination = failed disengagement).
     Implemented as a dynamic ON the axis: disengage when the last `novelty_window`
     turns recovered nothing NEW (novelty stalled) — the train circling without learning
     lets go. (Lightweight novelty proxy; the learning_progress_curiosity smoothed-
     progress signal is the noted richer upgrade.)

Falsifiable claims (a teacher-call spy counts external-answerer invocations):
  C1 WIDTH SHAPES THE TRAIN: width 0 vs mid vs 1 produce DISTINCT train shapes on the
     SAME seed — 0 climbs the is-a spine, wide wanders siblings/cross-branch. Distinct
     shapes ⇒ the axis genuinely governs transition breadth.
  C2 HONEST TERMINATION PREVENTS RUMINATION: a train that would churn to max_turns under
     agenda-only stopping (novelty_window=None) instead STOPS with 'novelty_stalled' when
     the window is on — for a real reason (no fresh recovery), not agenda-exhaustion.
  C3 TEACHER-FREE: the held path calls the external answerer ZERO times at every width.
  C4 BACKWARD-COMPAT: width 0 (and stance='residual') is byte-identical to the block-346
     default train shape.

Order-N (block 348 workspace, 349 minting) deferred. Pure graph, teacher-free (no LLM).
Run: PYTHONPATH=runners/dsl/python:. python3 scripts/gen_rung3_attention_width.py
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
    """A small is-a DAG with siblings + two branches, so width has room to differ:
    poodle/beagle is-a dog; tabby/cat -> mammal; sparrow -> bird; both -> animal."""
    s = _native.Substrate()
    ks.build_knowledge_mt(s, ["seeds/can_native_reimplementation.json"],
                          [("poodle", "dog"), ("beagle", "dog"), ("dog", "mammal"),
                           ("cat", "mammal"), ("mammal", "animal"),
                           ("sparrow", "bird"), ("bird", "animal")],
                          relation="isa")
    ag = s.add_node("Agent", {"name": "jabberwock"})
    sc = s.add_node("SelfConcern", {"status": "noted", "source": "implicit",
                                    "kind": "knowledge", "content": "poodle"})
    s.add_edge_unchecked(ag, "has_self_concern", sc)
    return s


def main() -> int:
    print("=" * 74)
    print("ATTENTION-WIDTH — goal<->associative axis + honest termination (block 347)")
    print("=" * 74)

    # C1 + C3 + C4: breadth sweep on the same seed, teacher-free. The breadth axis
    # is DISCRETE QUANTA (integer shells k); we sweep k = 0, 1, 2 (goal /
    # +children+siblings / +associative) — the same shapes 347 demonstrated at the
    # float widths 0.0/0.5/1.0, now expressed as the integer quanta they snap to.
    spies = {}
    shapes = {}
    for w in (0, 1, 2):
        spy = AskSpy(); spies[w] = spy
        r = tot.run_inner_conversation(_seed(), topic="poodle", max_turns=12,
                                       width=w, on_unknown="return", ask_fn=spy)
        shapes[w] = r["topics_thought"]
        print("\nwidth=%d quanta (k=%d)  train: %s"
              % (w, r["width_quanta"], r["topics_thought"]))
        print("   stop=%s  frontier=%s  ask_spy=%d"
              % (r["stop_reason"], r["frontier_growth"], len(spy.calls)))

    # C4 backward-compat: k=0 quanta == the block-346 default (stance='residual')
    r_res = tot.run_inner_conversation(_seed(), topic="poodle", max_turns=12,
                                       stance="residual")
    c4 = (shapes[0] == r_res["topics_thought"])
    print("\nC4 backward-compat: width0 %s == residual %s -> %s"
          % (shapes[0], r_res["topics_thought"], c4))

    # C1 distinct shapes: the widest quantum wanders wider than the goal core
    c1 = (shapes[0] != shapes[2] and len(shapes[2]) > len(shapes[0]))
    print("C1 width shapes the train (0 != 2, wide wanders wider): %s" % c1)

    # C3 teacher-free at every width
    c3 = all(len(spies[w].calls) == 0 for w in spies)
    print("C3 teacher-free at every width (all ask_spy=0): %s" % c3)

    # C2 honest termination prevents rumination. Construct a train that keeps getting
    # fed no-knowledge topics (would churn to max_turns): with novelty_window it STOPS
    # 'novelty_stalled'; with novelty_window=None it runs on (agenda-only = rumination).
    s2 = _native.Substrate()
    ks.build_knowledge_mt(s2, ["seeds/can_native_reimplementation.json"],
                          [("a", "b")], relation="isa")
    ag2 = s2.add_node("Agent", {"name": "jw"})
    for nm in ["x1", "x2", "x3", "x4", "x5", "x6"]:
        s2.add_node("Concept", {"name": nm, "state": 0.0,
                                "external_field": 0.0, "identity_field": 0.0})
    spyR = AskSpy()

    def churn_stance(wa, turn, seen):     # keeps feeding fresh no-knowledge topics
        return [nm for nm in ["x1", "x2", "x3", "x4", "x5", "x6"] if nm not in seen][:1]

    r_stall = tot.run_inner_conversation(s2, topic="x1", max_turns=20,
                                         stance_fn=churn_stance, novelty_window=3,
                                         on_unknown="return", ask_fn=spyR)
    r_churn = tot.run_inner_conversation(s2, topic="x1", max_turns=20,
                                         stance_fn=churn_stance, novelty_window=None,
                                         on_unknown="return")
    c2 = (r_stall["stop_reason"] == "novelty_stalled"
          and len(r_stall["turns"]) < len(r_churn["turns"])
          and len(spyR.calls) == 0)
    print("\nC2 honest termination vs rumination:")
    print("   with window:  stop=%s after %d turns"
          % (r_stall["stop_reason"], len(r_stall["turns"])))
    print("   no window:    stop=%s after %d turns (agenda-only = would ruminate)"
          % (r_churn["stop_reason"], len(r_churn["turns"])))
    print("   -> %s" % c2)

    allpass = c1 and c2 and c3 and c4
    print("\n--- claims ---")
    for name, ok in [("C1 width shapes the train", c1),
                     ("C2 honest termination (anti-rumination)", c2),
                     ("C3 teacher-free at every width", c3),
                     ("C4 backward-compat (width0==residual)", c4)]:
        print("  %-42s %s" % (name, "PASS" if ok else "FAIL"))
    verdict = ("BLOCK 347 PASS: goal-directed<->associative is one adjustable "
               "attention-width axis (distinct train shapes), termination is a "
               "dynamic on that axis (disengages when learning stalls, not just when "
               "the agenda empties), teacher-free, backward-compatible"
               if allpass else "FALSIFIED (see above)")
    print("\nVERDICT: %s" % verdict)
    print("=" * 74)
    print("SUMMARY_JSON " + json.dumps({
        "c1": c1, "c2": c2, "c3": c3, "c4": c4,
        "shape_w0": shapes[0], "shape_w05": shapes[1], "shape_w1": shapes[2],
        "stall_stop": r_stall["stop_reason"], "stall_turns": len(r_stall["turns"]),
        "churn_turns": len(r_churn["turns"]),
        "deferred": "global_workspace (348) + gated dimension-minting (349)"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
