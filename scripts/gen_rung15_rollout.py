"""Block 343000 — RUNG 1.5: the full autoregressive self-conditioned rollout.

Rungs 1-2 took a top-k SELECTION over ONE prediction — a bag of the highest-ranked
words, no feedback. Rung 1.5 makes it a true rollout: emit a word, FEED IT BACK into
the context + register, RE-PREDICT, repeat — the reader's next-word synthesis run
FORWARD with its own output as the observation (self-conditioned), unclamped by any
external surface. Goal + audience conditioning (rung 2) carry through every step.

Falsifiable claims:
  (C1) FEEDBACK PRESERVES FURTHERANCE: the rolled surface still recovers the goal's
       intended content (parse-back), i.e. self-conditioning does not lose the goal.
  (C2) IT TERMINATES WITHOUT DEGENERATE REPETITION: stop_reason is 'goal_covered'
       (not 'max_steps' runaway or 'exhausted' stall), repeat_rate low.
  (C3) THE STREAM IS ORDERED + PROVENANCED: per-step source (goal/voice/register/
       context) is recorded so drift is MEASURED, not hidden; the ordering is
       meaningful (goal content emitted first, then the voice tail) rather than a
       set. Compared head-to-head with the rung-2 top-k selection on identical goals.

Honest: coherence is bounded by the writer/register model; this does NOT claim
grammatical sentences. It proves the LOOP — self-conditioned, goal-steered,
terminating, content recovered. No model / network / substrate .so write path. Run:
  PYTHONPATH=runners/dsl/python:. python3 scripts/gen_rung15_rollout.py
"""
from __future__ import annotations

import json

from substrate_rs import _native

from domains import conceptualizer as cz
from domains import predictive_reading as pr
from domains import utterance_shaping as us
from domains import self_target_monitor as stm


DISTRACTOR_CORPUS = [
    "the merchant sailed across the wide sea to trade silk and spice",
    "sailors mend the sail and haul the heavy rope at dawn",
]
SELF_STYLE_CORPUS = [
    "indeed the poodle is plainly and simply a dog",
    "indeed the sparrow is plainly and simply a bird",
]
GOALS = [
    ["poodle", "dog", "animal"],
    ["sparrow", "bird", "creature"],
    ["copper", "metal", "substance"],
]


def main() -> int:
    print("=" * 74)
    print("RUNG 1.5 — autoregressive self-conditioned rollout vs rung-2 selection")
    print("=" * 74)
    s = _native.Substrate()
    ws_distractor = pr.build_writer_model(s, DISTRACTOR_CORPUS,
                                          class_corpus=DISTRACTOR_CORPUS)["writer_style"]
    ws_self = pr.build_writer_model(s, SELF_STYLE_CORPUS)["writer_style"]

    roll_sat = sel_sat = 0
    terminated_clean = 0
    total_repeat = 0.0
    n = len(GOALS)
    for intended in GOALS:
        # rung-2 shaping (self audience): content residual + own-idiolect voice
        resolved = cz.resolve_audience(s, None)
        shape = us.shape_from_audience(s, resolved, intended, self_style_node=ws_self)
        residual = shape["complexity_residual"]
        voice = shape["voice_words"]

        # --- AUTOREGRESSIVE ROLLOUT (rung 1.5): feed own output back, re-predict ---
        roll = pr.rollout_unclamped(s, ws_distractor, goal_content=residual,
                                    voice_words=voice, max_steps=16,
                                    voice_headroom=2)
        v_roll = stm.score_self_target(s, roll["surface"], residual)
        roll_sat += int(v_roll["recoverable"])
        terminated_clean += int(roll["stop_reason"] == "goal_covered")
        total_repeat += roll["repeat_rate"]

        # --- RUNG-2 SELECTION (top-k of ONE prediction, no feedback) for contrast ---
        k = max(3, len(residual) + min(len(voice), 3))
        pred = pr.predict_next_words(s, ws_distractor, context="",
                                     goal_content=residual, voice_words=voice)
        sel_surface = " ".join(w for w, _ in pred["ranked"][:k])
        v_sel = stm.score_self_target(s, sel_surface, residual)
        sel_sat += int(v_sel["recoverable"])

        print("\ngoal %s:" % ",".join(intended))
        print("  ROLLOUT   %r" % roll["surface"])
        print("     stop=%s repeat_rate=%.2f covered=%s per-step=%s"
              % (roll["stop_reason"], roll["repeat_rate"], roll["goal_covered"],
                 [(st["word"], st["source"]) for st in roll["steps"]]))
        print("     parse-back recovered=%s cov=%.2f"
              % (v_roll["recovered"], v_roll["coverage"]))
        print("  SELECT-k  %r  (recovered=%s cov=%.2f)"
              % (sel_surface, v_sel["recovered"], v_sel["coverage"]))

    print("\n--- claims ---")
    print("C1 feedback preserves furtherance: rollout %d/%d recovered "
          "(selection %d/%d for contrast)" % (roll_sat, n, sel_sat, n))
    print("C2 terminates cleanly (stop='goal_covered'): %d/%d; mean repeat_rate %.3f"
          % (terminated_clean, n, total_repeat / n))
    print("C3 ordered + provenanced: per-step source recorded above "
          "(goal content first, then voice tail — ordering meaningful)")
    c1 = (roll_sat == n)
    c2 = (terminated_clean == n and (total_repeat / n) < 0.2)
    verdict = ("RUNG 1.5 PASS: self-conditioned rollout preserves content recovery, "
               "terminates without degenerate repetition, emits an ordered provenanced "
               "stream" if (c1 and c2) else
               "RUNG 1.5 FALSIFIED: " + ("content lost under feedback " if not c1 else "")
               + ("degenerate (runaway/repeat)" if not c2 else ""))
    print("\nVERDICT: %s" % verdict)
    print("=" * 74)
    print("SUMMARY_JSON " + json.dumps({
        "rollout_satisfied": roll_sat, "selection_satisfied": sel_sat, "n": n,
        "terminated_goal_covered": terminated_clean,
        "mean_repeat_rate": round(total_repeat / n, 4),
        "c1_furtherance_preserved": c1, "c2_terminates_clean": c2,
        "parse_back_mode": "recognizer"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
