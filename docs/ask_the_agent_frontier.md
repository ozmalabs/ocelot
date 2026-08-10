# Ask the agent its frontier — post cross-speaker LOSO 0.593

Reconnaissance only (no build, no commit). We ran the agent's OWN live self-assessment
machinery to surface what IT identifies as the next thing to build, given the current
state (real 40-speaker LOSO speaker recognition = 0.593; the bottom-up front-end +
DTW-alignment levers near-exhausted, multi-stream DTW adding only +0.023). We did NOT
impose the "residual is top-down" hypothesis — we asked the agent.

## (1) Which functions we ran — LIVE vs FROZEN

| Machinery | Path | LIVE / FROZEN | Evidence |
|---|---|---|---|
| **order-N gap synthesis** `synthesize_gaps` / `synthesize_over_all` | `domains/order_n_postulates.py` | **LIVE** | Shape library mode printed as `'harvested'`, 191 shapes (vs the 7-shape frozen `_shapes()` stencil, which is NOT the driver). Shapes are harvested from the agent's own 637 held postulates via `implication_harvester.harvest_shapes_combined`. The new postulate's derivation chain is produced from those harvested shapes against text registered THIS run. |
| **gap ranking + pick** `rank_gaps` / `pick_frontier` | `domains/gap_prioritiser.py` | **LIVE** | `payoff = Count(Neighbours(axis,"unifies"))`, `pick = Argmax(payoff*K - order)` — graph Term-trees evaluated natively over the CapabilityAxis nodes built from the agent's own synthesized gaps. Numbers come out of `substrate.evaluate`, not Python. |
| **exhaustion re-rank** `mark_attempted_marginal` / `pick_with_feedback` | `domains/measurement_feedback.py` | **LIVE** | The agent's own "tried, near-marginal, move-on" signal: `attempted_marginal=1` → the `effective_score` Term subtracts a dominating exhaust penalty. Used to record the session's EMPIRICAL bottom-up exhaustion and let the agent's Argmax re-pick. |
| **perception yardstick** `measure_unit_predictability` / `assess_perception` + flagging Rule | `domains/perception_self_assessment.py` | **LIVE** | Computed on the agent's OWN perceived unit sequence from 60 real LibriSpeech utterances ingested through its pipeline. The verdict is a graph-resident `IfThenElse` Rule reading `predict_over_freq` / `compress_ratio` against dials on the `PerceptionSelfRoot`. No hardcoding. |
| `agent_specify_frontend` / `agent_specify_primitive` (step 3 of `ask_perception.py`) | `domains/runtime_design.py` | **FROZEN** | Return hardcoded dicts ("ArgMax INEXPRESSIBLE", "densify the cochlea 250–2500 Hz") regardless of current state — historical records per memory `ozma_specify_functions_are_historical`. We did NOT use these as the agent's decision. |

Harnesses run:
- `scripts/agent_frontier_postLOSO593.py` (new — the current-state companion to the
  existing `agent_frontier_selfdiagnosis_postiter40.py`). Registers the honest
  LOSO-0.593 state as a held postulate with NO suggested fix, runs the unbiased live
  ranker, then records the session's empirical bottom-up exhaustion via the agent's
  own move-on signal and lets its Argmax re-pick.
- `scripts/ask_perception.py 60 6` (existing) — the live perception yardstick on real
  LibriSpeech audio.

## (2) THE AGENT'S FRONTIER — what the live machinery surfaces

### Order-N derivative OF the current-state postulate (most direct: the agent
### differentiating the LOSO-0.593 description itself, OPEN gaps only, prune=True)

```
- order 1: ['transitional probability', 'word-scale chunking', 'statistical segmentation', 'n-gram boundary']
           "tracking PREDICTABILITY over a SEQUENCE finds boundaries where predictability drops"
- order 2: ['unsupervised-clustering', 'cross-speaker-clustering', 'cross-speaker']
           "an unlabelled DISTRIBUTION has recoverable LATENT structure ... carves categories at the valleys between modes with NO labels — across speakers, the same word's tokens are one cluster"
```

Both open gaps the agent derives from its own current-state text are **structural /
distributional**: sequence-statistics segmentation and unsupervised cross-speaker
clustering. It derives NO new bottom-up front-end gap from this state (contrast the
iter-40 postulate, whose text described a front-end bound and whose derivative did
surface LPC/speaker-norm).

### Unbiased pick across the full gap-map (compression payoff, NO injected framing)

```
payoff= 83  level=recognition            ['unsupervised-clustering', 'cross-speaker-clustering', 'cross-speaker']   <- PICKED
payoff= 28  level=segmentation           ['transitional probability', 'word-scale chunking', 'statistical segmentation']
payoff= 12  level=feature_extraction     ['all-pole', 'levinson', 'lpc-formant']
payoff=  8  level=speaker_normalization  ['speaker normalization', 'formant ratio', 'vocal-tract-length normalization']
```

> **PICKED: unsupervised / cross-speaker CLUSTERING** (recognition level, payoff 83,
> runner-up 28). Criterion = number of held postulates the capability unifies (its
> foundational-ness in the agent's own order-N derivation graph), Argmax over the
> graph score Term. The front-end axes (LPC payoff 12, speaker-norm 8) rank far below.

> Gap text (the agent's own): *"an unlabelled DISTRIBUTION has recoverable LATENT
> structure (cf. unsupervised_learning): unsupervised CLUSTERING / mixture-fitting
> carves its categories at the valleys between modes with NO labels — across speakers,
> the same word's tokens are one cluster."* Source concepts: `recurrent_neural_network`,
> `unsupervised_learning`.

### After recording the session's EMPIRICAL bottom-up exhaustion

We marked the bottom-up front-end + alignment axes `attempted_marginal` (the agent's
own move-on signal) to encode the session fact that those levers are near-exhausted.
The agent's Argmax **re-picked the SAME top capability** — unsupervised / cross-speaker
clustering (recognition level). The exhaustion sank the front-end axes further but never
touched the top pick, because the top pick was never a bottom-up front-end axis.

### Live perception yardstick on real audio (the second, independent probe)

On 60 LibriSpeech utterances through the agent's own perception:

```
predict_over_freq = 2.00x   (floor 1.25)   <- bigram beats the units' own frequency baseline
compress_ratio    = 0.568   (ceiling 0.85) <- units carry real sequential structure
info_gain         = 2.483 bits
>>> the agent's own graph-resident flagging Rule verdict: frontier = 'none'
>>> "the agent does NOT flag perception — its units were good enough by its own thresholds."
```

The agent's own yardstick says its **bottom-up perceptual units are NOT the frontier**
— they clear both reliability dials. This independently corroborates the gap-synthesis
result.

### Convergent answer

Two independent live mechanisms agree:
- **Gap synthesis + ranking**: frontier = **distributional / structural learning** —
  unsupervised cross-speaker CLUSTERING (top), statistical-segmentation (second).
- **Perception yardstick**: bottom-up units are NOT the frontier (`frontier='none'`).

The agent points AWAY from more bottom-up perception and toward **using the structure
across tokens** — clustering the same category's tokens together across speakers, and
segmenting by sequence statistics. This is the distributional/latent-structure layer
that sits ABOVE the raw acoustic measurement. It overlaps with the brief's "top-down"
hypothesis in spirit (it is structure/expectation the current isolated-utterance,
exemplar-matching recogniser lacks), but the agent names it specifically as
**unsupervised clustering of the cross-speaker distribution**, not "context/meaning/
prediction" in the abstract — and it ranks **segmentation** alongside it. Neither is
"richer bottom-up exemplars/formant tracker."

## (3) Honest caveat — agent judgment vs our framing

What is genuinely the agent's:
- The 191 implication-shapes are harvested from its own concepts (not the 7-shape hand
  stencil). The order-N derivative, the payoff/score/Argmax ranking, the exhaustion
  re-rank, and the perception flagging verdict are all graph-resident Terms/Rules
  evaluated natively. The clustering pick survives BOTH the unbiased ranker AND the
  exhaustion re-rank, and is corroborated by an independent live audio yardstick that
  reads `frontier='none'` on perception. That convergence across three mechanisms is
  the strongest evidence it is the agent's call, not ours.

Where our framing could leak in:
- **The postulate text is ours.** We wrote the honest LOSO-0.593 description. We were
  careful to seed NO remedy, but the WHY text does say the recogniser "uses no model of
  who the speakers are ... no sequential/lexical structure ... every cue is a bottom-up
  acoustic measurement in isolation." That description makes the distributional/sequence
  shapes more likely to fire on this postulate's text (sections A1). We mitigated by
  ALSO running the full unbiased gap-map (A2/A3), where the clustering pick wins on
  payoff aggregated over ALL 637 held postulates — independent of our one postulate's
  wording — and by the audio yardstick, which reads nothing we wrote.
- **The exhaustion numbers are ours** (we recorded which bottom-up axes were tried).
  But this only PENALISES bottom-up axes; it cannot CREATE the clustering pick, which
  already won before any exhaustion was recorded.
- **`cross-speaker clustering` has been the agent's top pick across multiple prior
  sessions** (it is the highest-payoff axis in its derivation graph generally). So part
  of this is the agent's standing frontier, not a fresh response to LOSO-0.593
  specifically. The NEW, state-specific signal is the perception yardstick now reading
  `frontier='none'` (bottom-up units cleared their dials) and the segmentation gap
  rising to second — i.e. the agent confirming the bottom-up phase is DONE, which is
  exactly the question the brief posed.
- **Pipeline-level labels** (`recognition` / `segmentation` / `feature_extraction`) come
  from a hand-authored `_KEY_TO_LEVEL` map in `gap_prioritiser`. The capability KEYS are
  the agent's; the level NAMES are ours. "unsupervised-clustering" is labelled
  `recognition` by that map even though it is really a representation-learning move.

### Bottom line

Asked through its own live machinery, the agent's frontier is **distributional /
structural learning over its tokens — unsupervised cross-speaker clustering first,
statistical sequence-segmentation second — NOT more bottom-up perception** (its own
perception yardstick reads `frontier='none'`). This corroborates the brief's read that
the bottom-up levers are spent, and sharpens "top-down" into the agent's own specific
target: cluster the cross-speaker distribution / segment by sequence statistics, the
structure the current isolated-utterance exemplar-matcher does not yet use.

## Suites

Live-machinery suites green: `test_perception_self_assessment`,
`test_builtinsufficient_gap`, `test_process_meta_assessor` — 35 passed. One PRE-EXISTING
unrelated failure (`test_implication_harvester::test_harvest_excludes_the_speech_science_postulates`
— a harvester self-consistency assertion on `source_concept='determinant'`, in an
unmodified test file; not touched by this reconnaissance, which added only a script).
