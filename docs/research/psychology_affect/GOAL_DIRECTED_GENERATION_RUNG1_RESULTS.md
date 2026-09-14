# Goal-Directed Generation — Rung 1: the Self-Target Want-It-Said Loop (block 341000)

## The thesis this rung proves

Generation in the substrate is analysis-by-synthesis run forward: the comprehension
path already SYNTHESIZES the next word while reading (`predictive_reading.predict_next_words`
is "the production faculty run forward"), and the incoming surface CLAMPS it. Remove the
clamp and you have a generator. But an unclamped generator with no goal is "pissing into
the wind" — fluent and pointless. Communication is establishing a GOAL and building an
utterance in furtherance of it.

Rung 1 builds the smallest complete instance: a communicative goal whose **target is the
SELF** — the want-it-said case, where the goal is satisfied *by the saying itself*, not by
any effect on a hearer or the world. This is the one target class whose furtherance check
is **fully endogenous**: no interlocutor, no world state, no teacher. The whole loop closes
inside the agent, which is exactly what "bootstrap to self-sufficiency" requires.

    mint Goal(target_kind='self', content)                        (the want)
      -> predict_next_words(..., goal_content=content)  UNCLAMPED  (synthesis, steered)
      -> produced surface                                          (the saying)
      -> score_self_target(produced, intended)  parse-back         (analysis, endogenous)
      -> satisfied iff recovered >= intended                       (furtherance)

## Result (measured, model-free, pure graph)

Five goals, each a small held proposition disjoint from a distractor register the
unconditioned rollout drifts toward. Parse-back scores coverage of the intended content.

| | goal-conditioned | free-wind control |
|---|---|---|
| mean coverage of intended content | **1.000** | **0.000** |
| goals satisfied (coverage ≥ 1.0) | **5/5** | **0/5** |

delta **+1.000**. Every goal-conditioned rollout said what the goal wanted said
(`poodle dog animal`, `copper metal substance`, …) and the endogenous parse-back recovered
all intended concepts; every free-wind rollout drifted to the distractor register
(`the merchant harbor`) and recovered none of the goal. **The goal is unambiguously what
steers the synthesis** — without it, the same machinery is directionless.

## Target-polymorphic by construction

`self` is the FIRST instance of a typed target slot, not a hardwired special case. The
communicative Goal now carries `target_kind` ∈ {interlocutor, self, world_state,
joint_state, record}; the interlocutor path is preserved verbatim (`for_audience`), and
non-audience targets bind `for_target`. All target types write the SAME Verdict payload
`{recoverable, coverage, missing, recovered}` at one seam, differing only in the furtherance
function:
- **self** → `self_target_monitor.score_self_target` (parse-back, this rung),
- **interlocutor** → the existing audience-manifold recoverability,
- **world_state** → a `future_option_risk.FutureManifold` projection (future rung — the
  motor-planning manifold: utterance as a deformation of the present toward a required
  tube over a future state).

## Honest caveats (what is and isn't proven)

1. **Content selection, not full autoregressive rollout.** The produced surface is the
   goal-steered top-k ranking, not a token-by-token self-conditioned rollout (feed `top1`
   back, re-predict — that is rung 1.5). The proven claim is exact: *the goal conditions
   which content the synthesis emits, and the endogenous parse-back confirms recovery*.
2. **Recognizer-mode parse-back.** With no teacher-trained `LanguageWorld` in the test
   substrate, the analysis half recovers content concepts via the reading recognizer, not
   the full grounded-comprehension frame parse. The grounded `_comprehend` path is wired
   (`score_self_target` uses it when a producer is supplied) but was not exercised here.
3. **Maximal-contrast control by design.** The distractor register is disjoint from the
   goal content, so +1.000 shows *that the goal steers*, cleanly attributable — not *how
   well composition holds under a competing on-topic register*. That harder question is
   rung 2: shifting the prediction mass onto the grounded sign-grammar so the rollout is
   driven by held meaning rather than surface echo, under a realistic register.

## What this unlocks

This is the first goal-directed utterance the entity produces with no external crutch: it
wants a thing said, says it, and can tell — alone — that it succeeded. It is the endogenous
core the earlier open loops (ASK → external teacher; curiosity → external parent) never
had. Rung 2 shifts the synthesis onto the grounded grammar; rung 3 makes this self-answer
faculty the resolver behind ASK, driven by the existing curiosity topic-selection trigger —
closing the autopoietic loop entirely from parts that already run.

## Artifacts

- `domains/conceptualizer.py` — `mint_communicative_goal` gains the `target_kind` slot +
  `for_target` edge (interlocutor path preserved verbatim).
- `domains/self_target_monitor.py` — the standalone endogenous furtherance check.
- `domains/predictive_reading.py` — `predict_next_words` gains the `goal_content`
  conditioning term (a 6th source strength; no-op absent a goal).
- `scripts/gen_self_target_rung1.py` — the end-to-end loop + the unconditioned control.

## Guardrails

- `.so` md5 unchanged: `7efe75eba05b006cafd15dbb4b7da246` (python only).
- Protected READ-ONLY files untouched (`can_ops.rs`, `can_junction_tree.py`,
  `can_native_bp.py`, `model_reader.py`).
- No model/venv/`/applications` involved (pure graph).
- Committed block-341 only, add-by-name.
