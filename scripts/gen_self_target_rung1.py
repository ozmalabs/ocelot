"""Block 341000 — RUNG 1 of goal-directed generation: the SELF-TARGET want-it-said loop.

The claim, made falsifiable: a communicative GOAL whose target is the SELF can
CONDITION the unclamped analysis-by-synthesis rollout so the produced utterance says
what the goal wants said, and the endogenous self-monitor parse-back CONFIRMS it — with
NO interlocutor, NO world, NO teacher in the loop. The whole loop is inside the agent:

    mint Goal(target_kind='self', content)                       (the want)
      -> predict_next_words(..., goal_content=content)  UNCLAMPED  (synthesis, steered)
      -> produced surface                                          (the saying)
      -> score_self_target(produced, intended)  parse-back         (analysis, endogenous)
      -> satisfied iff recovered >= intended                       (furtherance)

CONTROL (the 'pissing into the wind' baseline): the SAME rollout with NO goal_content.
A goal-less rollout drifts toward the writer/register prior (here a distractor corpus),
so it should recover the intended content FAR LESS than the goal-conditioned rollout.
If goal-conditioning does NOT beat the free baseline, the design is FALSIFIED — the goal
would not actually be steering the synthesis.

No model, no network, no substrate .so write path — pure graph + faculty. Run:
  PYTHONPATH=runners/dsl/python:. python3 scripts/gen_self_target_rung1.py
"""
from __future__ import annotations

import json

from substrate_rs import _native

from domains import conceptualizer as cz
from domains import predictive_reading as pr
from domains import self_target_monitor as stm


# A DISTRACTOR class corpus — the free-wind register the goal must overcome. These
# texts share NO content with the goal's intended concepts, so an unconditioned
# rollout drifts toward THESE words, not the goal's.
DISTRACTOR_CORPUS = [
    "the merchant sailed across the wide sea to trade silk and spice",
    "the merchant counted coins by candlelight in the harbor town",
    "sailors mend the sail and haul the heavy rope at dawn",
    "the harbor market sells salt fish rope and barrels of oil",
]

# The GOALS the agent wants said — each a small held proposition (concept set). These
# are DISJOINT from the distractor register, so recovery is attributable to the goal.
GOALS = [
    ["poodle", "dog", "animal"],
    ["copper", "metal", "substance"],
    ["sparrow", "bird", "creature"],
    ["oak", "tree", "plant"],
    ["hammer", "tool", "artifact"],
]


def _rollout_surface(ranked, k):
    """Greedy top-k rollout surface: the k highest-ranked predicted words, in rank
    order. (A minimal self-conditioned rollout: we take the goal-steered ranking as
    the produced content; a fuller rollout would feed top1 back and re-predict, but
    the recovery claim is already testable on the top-k content selection.)"""
    return " ".join(w for w, _ in ranked[:k])


def run_one(agent, ws_node, intended):
    """Run the goal-conditioned rollout and the unconditioned control for one goal;
    return the parse-back verdicts for both."""
    k = max(3, len(intended))

    # GOAL-CONDITIONED: mint the self-target goal, condition the rollout on its content.
    g = cz.mint_communicative_goal(agent, "inform", intended, target_kind="self")
    goal_content = list(agent.node(g)["attrs"]["content"])
    pred_goal = pr.predict_next_words(agent, ws_node, context="",
                                      goal_content=goal_content)
    said_goal = _rollout_surface(pred_goal["ranked"], k)
    verdict_goal = stm.score_self_target(agent, said_goal, intended)

    # CONTROL: same rollout, NO goal_content (free wind).
    pred_free = pr.predict_next_words(agent, ws_node, context="")
    said_free = _rollout_surface(pred_free["ranked"], k)
    verdict_free = stm.score_self_target(agent, said_free, intended)

    return {"intended": intended, "goal_node": pr._v(g),
            "said_goal": said_goal, "verdict_goal": verdict_goal,
            "said_free": said_free, "verdict_free": verdict_free}


def main() -> int:
    print("=" * 74)
    print("RUNG 1 — SELF-TARGET want-it-said goal-directed generation (block 341)")
    print("=" * 74)
    s = _native.Substrate()

    # Build the writer model / register from the DISTRACTOR corpus — the free-wind
    # prior the unconditioned rollout drifts toward.
    model = pr.build_writer_model(s, DISTRACTOR_CORPUS,
                                  class_corpus=DISTRACTOR_CORPUS)
    ws = model["writer_style"]
    print("writer model built (distractor register, %d recurring-surface words)"
          % len(model.get("recurring_surface", [])))

    rows = [run_one(s, ws, g) for g in GOALS]

    print("\nper-goal furtherance (coverage of intended content by the parse-back):")
    print("  %-26s | goal-cond | free-wind" % "intended")
    goal_cov = []
    free_cov = []
    goal_sat = 0
    free_sat = 0
    for r in rows:
        gc = r["verdict_goal"]["coverage"]
        fc = r["verdict_free"]["coverage"]
        goal_cov.append(gc); free_cov.append(fc)
        goal_sat += int(r["verdict_goal"]["recoverable"])
        free_sat += int(r["verdict_free"]["recoverable"])
        print("  %-26s |   %.2f    |   %.2f" % (",".join(r["intended"]), gc, fc))
        print("      said(goal): %r -> recovered %s"
              % (r["said_goal"], r["verdict_goal"]["recovered"]))
        print("      said(free): %r -> recovered %s"
              % (r["said_free"], r["verdict_free"]["recovered"]))

    n = len(rows)
    mg = sum(goal_cov) / n
    mf = sum(free_cov) / n
    print("\nMEAN coverage:  goal-conditioned %.3f   vs   free-wind %.3f  (delta %+.3f)"
          % (mg, mf, mg - mf))
    print("SATISFIED (recoverable, coverage>=1.0): goal %d/%d  vs  free %d/%d"
          % (goal_sat, n, free_sat, n))
    verdict = ("GOAL STEERS THE SYNTHESIS (conditioning beats free-wind)"
               if mg > mf + 0.2 else
               "FALSIFIED: goal-conditioning does NOT beat the free baseline")
    print("\nVERDICT: %s" % verdict)
    print("=" * 74)

    summary = {"mean_coverage_goal": round(mg, 4),
               "mean_coverage_free": round(mf, 4),
               "delta": round(mg - mf, 4),
               "satisfied_goal": goal_sat, "satisfied_free": free_sat,
               "n_goals": n,
               "parse_back_mode": rows[0]["verdict_goal"]["mode"] if rows else None,
               "verdict": verdict}
    print("SUMMARY_JSON " + json.dumps(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
