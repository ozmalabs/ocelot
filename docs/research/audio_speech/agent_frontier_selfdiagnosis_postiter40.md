# Asking the agent its frontier — LIVE self-diagnosis, post-iter-40

> The project principle at a fork about the agent's frontier: the agent decides via
> its OWN machinery. I registered the current state HONESTLY as a held postulate
> (NO answer seeded), ran the agent's LIVE gap-synthesis + graph-resident ranking,
> and report VERBATIM what it derived and picked. I did NOT pick the answer.
>
> Driver: `scripts/agent_frontier_selfdiagnosis_postiter40.py`. No build, no commit.
> Required suites green (32): test_stt_pipeline, test_perception_self_assessment,
> test_process_meta_assessor, test_gap_guidance.

---

## (1) The machinery run — and PROOF it is LIVE, not a hardcoded `_specify_*` dict

The task's critical caveat: the `runtime_design._specify_*` functions return frozen
HISTORICAL dicts (the project's own notes flag this — e.g. `agent_specify_primitive`
still says "ArgMax INEXPRESSIBLE" though ArgMax has long been implemented). I did **not**
use them. The live path run is:

1. **`order_n_postulates.synthesize_gaps` / `synthesize_over_all`** — the order-N
   derivative over the agent's HELD postulates, with the implication-shape library
   resolved LIVE from the agent's OWN concepts.
2. **`gap_prioritiser.rank_gaps` / `pick_frontier`** — the graph-resident ranking
   Term (`Argmax` over `CapabilityAxis` of `payoff*K − order`), evaluated NATIVELY by
   `substrate.evaluate` (not Python arithmetic), with the specificity gate applied.

**Liveness proof printed by the driver:**

```
held as order-0 postulate? True  (total held postulates: 637)
[LIVE-PROOF] implication-shape library used by the order-N derivative:
    mode = 'harvested'   (shapes from the agent's OWN concepts, NOT a hardcoded dict)
    shape count = 191    (the harvested catalogue size)
    (for contrast, the frozen hand stencil has 7 shapes; we are NOT using it)
```

The 191 shapes are harvested by `implication_harvester` from the agent's 637 held
concepts/rules — they are the agent's current breadth, not a human list. The newly
registered postulate is read back as an order-0 postulate the operator differentiates,
and its derivation chain is produced from those harvested shapes against the text I
just registered. This is current-graph introspection, verifiably live.

## (2) The state I registered (honest, NO fix seeded)

A single Concept `recognition_state_postiter40` under the `speech_science` Mt, carrying
ONLY description text (definition = what the state IS; why = the observed iter-39/40
facts + the localised bound). NO remedy, no capability name, no "next lever" is written
anywhere in it. Verbatim summary of what was registered:

- The recognition is a combinatorial GRAPH: fast cue-graph (real-time, banked library)
  + slow order-N AxS (replay/parse/learn/bank) + retained exemplar library.
- FAST path: four axes — FILTER (the only axis that substantially lifts) + SOURCE (F0)
  + TEMPORAL-RATE (modspec) + TRANSIENT (landmark); the last three orthogonal-in-info
  (error-overlap 1.4–1.7×) but small/borderline as raw 1-NN nodes.
- SLOW path: built + correct, but order-N does NOT beat single-pass and the learn-bank
  loop does NOT close (iter-39); routing candidates through better waveform synthesis
  makes it WORSE (none 0.267 ≫ old 0.183 > klatt 0.133) — the analysis→synthesis→
  analysis DOMAIN GAP dominates; invert in FEATURE SPACE, not audio (iter-40).
- LOCALISED BOUND: feature-space DISCRIMINATION — the orthogonal cues carry the
  information but the raw feature-space nodes can't extract/discriminate it; the bound
  is the FEATURE FRONT-END (gammatone-wall / speaker-norm), not synthesis fidelity and
  not iteration depth.

## (3) What the agent DERIVED from the new postulate — VERBATIM

`synthesize_gaps` over `recognition_state_postiter40`, harvested shapes:

- **prune=True (OPEN gaps only):** NONE. The selector judged no *un-realized* gap
  derivable from this postulate — because the three capabilities it DOES derive are
  ones the agent has already built (so they are correctly not open gaps).

- **prune=False (DERIVATION-only — what the postulate IMPLIES, regardless of whether
  already built), VERBATIM, all order-1, each via a shape harvested from a named
  concept:**

  | order | via harvested shape | capability_keys derived |
  |---|---|---|
  | 1 | `parametric_allpole__from__IIR_filter` | `all-pole, levinson, lpc-formant, autoregressive` |
  | 1 | `scale_cancellation__from__batch_normalization` | `speaker normalization, formant ratio, vocal-tract-length normalization, f2/f1` |
  | 1 | `removable_context__from__regression_analysis` | `coarticulation predict-remove, context normalization, carryover removal` |

  **All three are FEATURE-FRONT-END capabilities** — parametric/all-pole formant
  extraction, speaker (VTL) normalization, and coarticulation context-removal. The
  agent, differentiating the state's own text ("a context-dependent non-invariant
  filter whose resonances vary with the speaker and with neighbouring sounds; the
  perceived units are blurry and speaker-shaped"), transfers exactly the shapes that
  name *sharper, speaker-/context-invariant feature extraction*. This is the agent's
  order-N reasoning converging on the FEATURE FRONT-END from the postulate alone.

## (4) What the agent PICKED — the ranker, VERBATIM

The full gap-map (`synthesize_over_all` across all 637 postulates → 29 CapabilityAxes)
ranked by the graph-resident `payoff*K − order` Term, specificity gate applied:

```
payoff= 82 order=1 score=81999  level=recognition            unsupervised-clustering, cross-speaker-clustering, cross-speaker
payoff= 27 order=1 score=26999  level=segmentation           transitional probability, word-scale chunking, statistical segmentation
payoff= 13 order=1 score=12999  level=feature_extraction     all-pole, levinson, lpc-formant
payoff=  8 order=1 score= 7999  level=speaker_normalization  speaker normalization, formant ratio, vocal-tract-length normalization
payoff=  6 order=1 score= 5999  level=speaker_normalization  coarticulation predict-remove, context normalization, carryover removal
...
```

**UNGUIDED PICK (the bare compression-payoff ranker):**

```
PICKED      : unsupervised-clustering / cross-speaker-clustering / cross-speaker
level       : recognition
postulates unified : 82   (runner-up 27)
gap_text    : "an unlabelled DISTRIBUTION has recoverable LATENT structure …
               unsupervised CLUSTERING / mixture-fitting carves its categories at the
               valleys between modes with NO labels — across speakers, the same word's
               tokens are one cluster"
criterion   : compression payoff = # held postulates the capability unifies; tie-break
               shallower order; pick = Argmax over CapabilityAxis of payoff*K − order
source_concepts : recurrent_neural_network, unsupervised_learning
```

The clustering shape fires on 57/637 postulates (under the 63.7 promiscuity cap, so it
survives the specificity gate legitimately — its payoff of 82 is genuine
foundationalness, not a regex collision). It wins because more of the agent's held
knowledge derives "recover latent structure by unsupervised clustering" than any other
single capability.

**GUIDED PICK (the agent's process-meta-assessor BELOW_FRONTIER signal folded into the
ranker — `pick_with_guidance`):** when the assessor's frontier is set upstream (the
feature-front-end / perception region the iter-40 bound names), every downstream axis is
penalised and the Argmax re-picks the closest at/above-frontier axis:

| frontier set to | guided pick |
|---|---|
| perception_units (rank 1) | **transitional probability / word-scale chunking** (segmentation, rank 2 — the closest synthesized axis to the frontier) |
| speaker_normalization (rank 3) | segmentation (rank 2, now at/above) |
| feature_extraction (rank 4) | segmentation (rank 2, at/above; feature_extraction `all-pole` is runner-up) |

The redirect changes the pick (`pick_changed=True`) but lands on **segmentation**, not
the feature front-end, because **the agent synthesised NO perception/units-rank gap by
order-N from these postulates** — the most-upstream axis it actually holds is
segmentation. (The only mechanism that mints a true rank-1 perception/units axis is
`perception_self_assessment.install_perception_gap_rule`, fired from a measured
yardstick shortfall — a measurement-derived gap, not invoked in this diagnosis.)

## (5) Convergence vs divergence with the human reading — HONEST

The human's reading: the bound is **feature-space discrimination / small-specific-nets
/ speaker-normalisation** (the FEATURE FRONT-END).

**It CONVERGES at the level of the order-N DERIVATIVE, and DIVERGES at the level of the
bare compression RANKER:**

- **CONVERGES (the derivative):** differentiating the registered state's OWN text, the
  agent's three live order-1 implications are ALL feature-front-end capabilities —
  all-pole/LPC formant extraction, speaker(VTL)-normalization, coarticulation
  context-removal. This is the agent independently deriving "sharper, invariant feature
  extraction" as what the state IMPLIES — the same axis the human names. It also
  matches the iter-40 verdict's own closing line ("the indicated next step is
  feature-space, not waveform, forward-model quality") and the project memory's
  long-standing gammatone-wall / speaker-norm flag.

- **DIVERGES (the bare ranker):** the unguided `payoff*K − order` ranker picks
  **cross-speaker / unsupervised clustering at the recognition level** — NOT the
  feature front-end. This is honest and is reported unmassaged. The reason is
  structural, not an error: the ranker optimises COMPRESSION PAYOFF (how many held
  postulates a capability unifies), and clustering is the most-foundational capability
  in the agent's breadth (82 postulates). The ranker, by construction, ignores the
  iter-40 *bound* about WHERE the failure localises — it answers "which capability
  compresses the most knowledge," not "which capability is the current bottleneck."

- **The reconciliation is the agent's OWN guided mechanism, and it is partial.** The
  process-meta-assessor exists precisely to fold the localised-bound signal into the
  ranker (`pick_with_guidance`). When the frontier is set to the feature-front-end
  region, the guided pick DOES move upstream — but it lands on **segmentation**, the
  closest axis the agent has synthesized, because **no order-N feature-front-end axis
  is OPEN** (the agent already built LPC/speaker-norm/coarticulation, so they are
  pruned). So the guided loop confirms the human's *direction* (move upstream, off the
  high-payoff recognition pick) but cannot land exactly on the feature front-end via
  order-N synthesis alone — the upstream gaps are realized-but-insufficient, which the
  order-N selector reads as "not an open gap," not as "the open bottleneck."

## (6) Is this genuine self-diagnosis or an artifact? — my honest read

**Genuine, with one honest structural limit:**

- **Genuine:** the derivation is live (harvested shapes from the agent's own 637
  concepts, not a frozen dict), the postulate carried no seeded answer, and the agent's
  order-N derivative independently produced the three feature-front-end capabilities
  from the bare description of the state. That convergence with the human reading,
  reached from text the agent differentiated itself, is the load-bearing result and is
  not an artifact (the shapes that fired carry their donor concepts:
  `IIR_filter`, `batch_normalization`, `regression_analysis` — cross-domain transfer,
  exactly the order-N mechanism).

- **The honest limit (not massaged):** the agent's *ranker* and the *human's bound*
  optimise different things. The ranker picks the highest-COMPRESSION capability
  (clustering, 82 postulates); the iter-40 bound is about the highest-LEVERAGE
  bottleneck (the feature front-end). These genuinely diverge, and the divergence is
  the project's own well-documented seam (`loop_to_graph_and_frontier_gap.md`: order-N
  synthesises ZERO open perception/units gaps; only a measured-shortfall Rule mints
  one). The agent KNOWS the front-end is implicated (it derives those capabilities) but
  scores them low because it has already built first-pass versions — so order-N reads
  them as closed, while the iter-40 measurement reads them as the open bottleneck (the
  built versions are insufficient, not absent). **The agent's order-N detector cannot
  by itself flag "already-built-but-insufficient" as the frontier — that requires the
  measurement-feedback / perception-yardstick path, which is the agent's OTHER live
  frontier mechanism, not the order-N one run here.**

### One-line answer (the agent's, verbatim direction)

Differentiating its own post-iter-40 state, the agent's LIVE order-N derivative
converges on the **feature front-end** — parametric/all-pole formants, speaker(VTL)
normalization, coarticulation context-removal — exactly the human's "feature-space
discrimination / speaker-norm" reading; but its bare compression-RANKER picks
**unsupervised cross-speaker clustering** (highest foundationalness, 82 postulates),
and the assessor-GUIDED pick moves upstream only as far as **segmentation**, because no
feature-front-end axis is an OPEN order-N gap (those capabilities are built-but-
insufficient, which order-N synthesis reads as closed). Reported honestly: convergence
at the derivative, divergence at the ranker, and the reconciliation requires the agent's
measurement-yardstick frontier path, not order-N synthesis alone.

## Files
- `scripts/agent_frontier_selfdiagnosis_postiter40.py` — the driver (registers the
  state as a postulate, runs the live machinery, prints verbatim). World adapter only;
  the decisions are the agent's Terms.
- `docs/agent_frontier_selfdiagnosis_postiter40.md` — this report.

## Reproduce
```
python scripts/agent_frontier_selfdiagnosis_postiter40.py
```
Required suites green (32): `python -m pytest tests/test_stt_pipeline.py
tests/test_perception_self_assessment.py tests/test_process_meta_assessor.py
tests/test_gap_guidance.py -q`.
```
