# ARC SUMMARY — Agenthon 2026 Track 2 (Forecasting), OCELOT/Seldon

One-page consolidation of the whole arc: PoC → real-contract adapter → reuse
text arm → macro surprise → powered nulls. Follows the repo honesty norms:
**proven vs assumed, nulls are findings, no fabricated score.** Every local
metric uses a hand-made / direction-aware proxy and is **RAW_UNRANKABLE** — the
sealed organizer outcomes are unavailable, so no ranked/normalized number is
claimed anywhere.

## The question

Track 2 asks: can an agent reason over a timestamped text corpus + time-series
panels to forecast better than text-blind baselines (CRPS composite; as-of +
calibration gate)? The scientific crux is INFORMATION UPLIFT from text.

## The through-line

1. **PoC (drafts/seldon_t2_poc/).** A Seldon manifold-with-confidence forecaster
   (reachable set + stepped credence) is CRPS-scorable and calibratable;
   conditioning the confidence mass on a CLEAN synthetic regime signal cut CRPS
   ~6%. It STUBBED real text (`TextToken{t,entity,incoming_regime}` handed for
   free) — the hard steps (link, type, date) were skipped.

2. **Reuse assessment (the reframe that paid off).** Investigation established
   the substrate ALREADY contains the machinery an honest text arm needs, and
   the user's reframes were each verified against code:
   - "utterances are manifold deformations with purpose" → the ToM/intent stack
     (bigville `<aspect>_for:<target>` CAN Concepts, `actor_goals` abduction).
   - "time is a coordinate to mint, not special" → `TimeInfer` (embodiment-proven
     forward projection); as-of = a bound on `coord:t`.
   - "grounding is the confidence" → grounding is a VECTOR (CAN marginal ⟨σ⟩),
     transitively closed via `ReachableFrom('grounded_in')`, with a
     `GroundingGap` overconfidence guard — all pre-existing.

3. **The text arm = STRICT REUSE, zero substrate edits.** A central-bank
   utterance is a bigville resident's action applying evidence to a target-scoped
   CAN belief: read_clause → `concept_apply_evidence` on
   `<stance>_stance_for:market` → CAN marginal is the graded signal →
   `grounding_reach` is the confidence → shift the band by direction × grounding.
   H0 verdict REUSE (the corpus→CAN-evidence bridge `reasoning_can_bridge` is
   already source-agnostic); no fork, no new belief node type.

4. **Macro surprise (F4 gap).** A CPI/NFP print is not a speech act — its signal
   is SURPRISE vs expectation. Built as MORE evidence on the SAME belief (taught
   `MacroSurpriseSign` codebook + `ib_decode_macro_surprise` rule), composing
   with the ToM decode. Still reuse, still zero substrate edits.

## Hypotheses — all measured, every null localized

| ID | claim | verdict |
|----|-------|---------|
| H0 | corpus→CAN-evidence is reuse (or generalize) | **REUSE** — bridge already source-agnostic; bigville tests green (net-win gate vacuous, no edit) |
| H1 | decode-through-ToM generalizes past FOMC house-style | **CONFIRMED** — non-FOMC direction 0.727 vs cue-lexicon 0.273 (+45pp); overall 0.846 vs 0.712 |
| H2a | correctly-directed shift lifts composite (direction-aware proxy) | **CONFIRMED** 6/6 — the original NEUTRAL was a blind-instrument artifact |
| H2b | grounding-weighted beats flat shift on composite | **NULL (flat-robust), powered 64 seeds + CI + full gw-range sweep** — grounding-weighting never CI-separates above flat; it's a tie only in the flat limit |
| H2c | graceful under no signal | **CONFIRMED** — |Δ| 8e-5, order below the signal gain |
| H3 | ungrounded-confident read shifts ~0 | **PROVEN** — GroundingGap mints, shift ratio 0.0 |
| H-M1 | macro surprise recovers direction (the 0.0 residual) | **CONFIRMED** 17/17 vs ToM 0.0, labels frozen (sha256) pre-measure |
| H-M2 | macro path does not regress ToM | **CONFIRMED** — non-macro H1 byte-identical |
| H-M3 | macro surprise → composite via shift | **partial/confounded** — raw win is a shift-center artifact; true direction effect small (−0.0088) but monotone |

## What this establishes (proven)

- An admissible, calibrated, containerized, OFFLINE forecaster passing g0–g3 on
  the exemplar + F1/F2/F3/F4 practice units via the REAL reference scorer.
- The text arm is strict reuse of the substrate's own ToM/grounding/CAN machinery
  — which is WHY it generalizes past FOMC where a surface cue-lexicon collapsed.
- Two design questions CLOSED with powered/CI evidence: (a) direction is
  forecast-relevant (H2a); (b) grounding-weighting is a calibration + safety
  feature (H3/H2c), NOT a composite lever (H2b powered). So the shipped arm can
  be as simple as a flat correctly-directed shift + the GroundingGap guard.
- The joint-variogram gap (the 30% the PoC failed) is closed on yield-curve F3
  units (JointDrawEngine, cross-asset-correlated draws).

## What is NOT established (assumed / unavailable)

- Any RANKED/normalized/board number — impossible locally (always
  RAW_UNRANKABLE); needs the sealed organizer outcomes.
- Live house-endpoint (MODEL_ENDPOINT) typing accuracy on non-FOMC prose — the
  biggest open uplift lever; wiring proven against a mock, live number unmeasured.
- Real calibration/uplift vs sealed truth; all proxies are direction-sensitive
  relative instruments, sympathetic to the arm's own decode by construction.
- H-M1's 1.0 is narrow (n=17, single annotator, CPI-dominated).

## Submission status (staged, organizer-gated)

- Image `ghcr.io/ozmalabs/qfb2-t2-ocelot@sha256:c71c12c3a355…` built, pushed,
  runs `--network=none`, admissible g0–g3, writes exactly the 3 deliverables.
- `submission.dev.json`: team_id 255, real digest, sealed against the real
  toolkit, no placeholders.
- **Remaining organizer-gated actions (not build):**
  1. Make the GHCR package PUBLIC (UI: github.com/orgs/ozmalabs/packages → visibility).
  2. Get the CodaBench competition link for `agenthon2026-forecasting` (from the
     team-255 registration email / agenthon.net starter package / codabench.org
     "My Competitions" once invited / ask admin@agenthon.net or T2 lead Ruolan Sun).
     NOT public — gated behind team registration; NOT findable on the open web.
  3. Upload `submission.dev.json`; read per-CARD scores (not rank — dev board is a
     practice board and the practice data self-leaks by the organizers' own
     measurement). Budget: 5/day, 20 total — submit text-blind FIRST as the
     "is-this-on" smoke, then layer the ToM arm on a known baseline.

## Files (all under drafts/seldon_t2_text/, untracked)

PoC: ../seldon_t2_poc/. Adapter+joint: t2_adapter.py, PHASE12_*. Arm:
induced_belief/ (arm.py, frame.py, macro_surprise.py, measure_h1/h2/h3,
measure_h2_directed, measure_h2b_power, measure_h2b_gwrange). Preregs+results:
INDUCED_BELIEF_*, H2_RESOLUTION_*, H2B_POWER_*, MACRO_SURPRISE_*. Container:
docker/. Submission: submission.dev.json, make_submission_descriptor.py.
Plan/status: T2_SUBMISSION_PLAN.md, SUBMISSION_STATUS.md, this file.
