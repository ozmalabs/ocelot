# The agent's self-directed research loop (synthesise → pick → build → measure)

This is an autopoietic-loop test: the agent runs its OWN research loop end to end —
synthesise its gaps, PICK its frontier by its own criterion, forward-build it from
its own science, and self-measure — with no human and no orchestrator choosing the
frontier or hand-coding the solution. Every place scaffolding had to step in is
named plainly in §5.

Working dir: `research/experiments/gamma-substrate`. Corpus: FSDD (`/tmp/fsdd`),
6 speakers, 10 utterances per (digit, speaker), all pooled.

---

## 1. SYNTHESISE the gaps (the agent's machinery, unchanged)

`scripts/order_n_postulates_demo.py` runs `domains/order_n_postulates` over the
agent's held `speech_science` postulates, transferring implication-shapes
HARVESTED from the agent's OWN cross-domain concepts
(`domains/implication_harvester`) — the cross-domain breadth packs (math /
engineering / ML / concept-expansions) are installed exactly as the demo's `_build`
does, so the harvest draws on the agent's own knowledge, not a human stencil.

Harvest: **7 implication-shapes (7 kinds) from 40 of the agent's own concepts
across 8 domains** (control, engineering, linear_algebra, machine_learning,
mathematics, signal_processing, statistics, transformer_architecture). Stencil OFF.

The synthesis recorded **12 `SynthesizedGap` graph nodes**, collapsing to **3
distinct capability-axes**, each carrying its full derivation chain + source-concept
provenance (`derived_from` edge to the postulate Concept):

| capability-axis | derived from (# postulates) | min order | source concept(s) (domain) |
|---|---|---|---|
| **cross-speaker clustering** | 6 — distributional_learning_of_categories, lexical_access, segmentation, speech_acquisition, statistical_learning, syllable_structure | 1 | unsupervised_learning, recurrent_neural_network (machine_learning) |
| **word-scale chunking** | 4 — lexical_access, segmentation, statistical_learning, syllable_structure | 1 | recurrent_neural_network (machine_learning) |
| **LPC formant extraction** | 2 — source_filter_theory, vocal_tract_resonance_formants | 1 | IIR_filter (signal_processing) |

Example chain (LPC): `source_filter_theory` (order-0, "vocal tract is a linear
FILTER") → via the `parametric_allpole` shape harvested from the agent's own
`IIR_filter` concept → "an invertible all-resonance system is captured by an
ALL-POLE / autoregressive (linear-predictive) model: a few poles ARE the
resonances, recovered by linear prediction rather than read off a blurry spectrum"
→ GAP (the selector confirms `all-pole` is not in the agent's speech codebase).

## 2. PICK the frontier — the AGENT's choice, not the orchestrator's

The agent has a gap DETECTOR (`order_n_postulates`) but **had no gap PRIORITISER**
(confirmed: `SynthesizedGap` had exactly one consumer — the detector itself). This
is a real piece the loop lacked; it is named as an intervention in §5.

To let the agent pick, I added `domains/gap_prioritiser.py`, which ranks the agent's
own recorded `SynthesizedGap` nodes by the agent's OWN criterion — its
compression/curiosity drive (memory: *"explore the under-compressed; compression as
quality"*), read straight off its own derivation structure:

> **compression payoff = the number of held postulates the capability unifies**
> (its foundational-ness in the agent's own order-N derivation graph); tie-break:
> the shallower (surer) derivation order.

The rationale is the agent's own MDL/curiosity selector applied to its gap set:
closing a capability discharges every postulate that derived it, so the capability
that unifies the most of the agent's knowledge compresses the most.

**Ranked output (the agent's, computed from its graph alone):**

```
#1  payoff=6  min_order=1  cross-speaker clustering   (unifies 6 postulates)
#2  payoff=4  min_order=1  word-scale chunking        (unifies 4 postulates)
#3  payoff=2  min_order=1  LPC formant extraction     (unifies 2 postulates)
```

**The agent picked cross-speaker clustering** (payoff 6 vs runner-up 4), recorded as
a `FrontierChoice` graph node. This is the agent's selection by its own criterion —
NOT the orchestrator's. (Had I been choosing, the LOSO probe below would have
steered me to the LPC/front-end gap; the agent picked clustering on
foundational-ness, which is a different and defensible call.)

## 3. PURSUE — forward-build, the agent's way (compose, don't hand-code)

`domains/cross_speaker_clustering.py` composes label-free clustering as graph
Term-trees from the agent's OWN `latent_structure` science (the harvested shape:
"an unlabelled distribution's modes ARE the categories; the same word's tokens
across speakers form one cluster — recovered with NO labels"). It is the **CMVN
mean move lifted from frames to tokens** — the same compose pattern the agent used
for CMVN, speaker-norm, and the order-N features:

- **assignment** `assign(t) = Argmin_{k in centroids} Σ_b (band_b(t) − band_b(k))²`
  — nearest-centroid, squared Euclidean from `Minus`/`Times`/`Plus` (the CMVN
  variance primitives) + `Argmin`.
- **update** `band_b(k) ← (Σ_{t∈members(k)} band_b(t)) / N_k` — `Sum`/`Count` over
  the `has_member` edge — *identical* to CMVN's per-band mean over `has_stat_frame`,
  one level up (tokens not frames, centroids not utterances).

All primitives already existed in the DSL (`Argmin`, `Sum`, `Count`, `Div`,
`Minus`, `Times`, `Plus`, `Attr`, `Var`, `Neighbours`) — **no new primitive
needed**. The Terms are recorded as Concepts the agent owns (`feature_kind =
cross_speaker_clustering`). The only Python is a mechanical I/O translator (lay the
token cloud out as a graph, evaluate the agent's assignment/update Terms natively to
convergence) — the arithmetic is the substrate evaluator's (`substrate.evaluate`),
no label ever read. Verified on synthetic 2-blob data: purity 1.0.

## 4. MEASURE — the agent's self-measurement (did it close the gap?)

`scripts/cross_speaker_clustering_probe.py`: pool every speaker's FSDD digit
utterances into one unlabelled cloud, run the agent's composed clusterer (k = 10
digits, label-free), score cross-speaker cluster **purity** vs the held-out truth.
Two representations, fair head-to-head:

```
random-assignment purity floor = 0.162   (chance ~ 0.100)

raw spectrum trajectory (baseline)   purity 0.483 +/- 0.034
agent CMVN-invariant signature       purity 0.441 +/- 0.027     (delta -0.042)
```

**Honest verdict — a real PARTIAL close.** The agent's composed clusterer *works*:
0.44 purity is far above the 0.16 random floor, so the Term-composed,
graph-resident, label-free k-means genuinely clusters same-digit tokens across
speakers. But the agent's CMVN front-end does **not** beat the raw spectrum here
(0.441 vs 0.483). This is the same finding the sound-graph LOSO probe gives
independently:

```
scripts/sound_graph_probe.py (baseline, unchanged):
  filter (formant relations) LOSO = 0.335   vs   spectrum (absolute) LOSO = 0.649
  -> "the formant extraction is noisy enough that the relational structure
      INHERITS the spectral problem rather than dissolving it."
```

Both probes converge on the same bound: **the clustering/invariance mechanism is
real, but it is capped by the front-end** — the blurry-spectrum representation.
That front-end limit is *exactly the LPC/all-pole gap the agent ranked #3* (clean
all-pole resonance extraction instead of spectral peak-picking). So the loop's own
measurement points at the next gap in the agent's own ranked list — the loop is
internally consistent.

## 5. THE KEY HONESTY — did the agent self-direct, and where did scaffolding step in?

**Genuinely the agent's (no human in the loop):**
- the gap SYNTHESIS — the order-N derivative structure over its own postulates, with
  shapes HARVESTED from its own 40 concepts (stencil off);
- the gap SELECTOR (compression vs covered-set + speech-codebase scan);
- the PICK criterion is the agent's own compression/curiosity drive, and the ranking
  is computed entirely from the agent's own recorded derivation graph — the
  orchestrator did not choose the frontier (and would have chosen differently);
- the BUILD is composed from the agent's own science via its own DSL primitives, the
  same compose pattern it used for CMVN/speaker-norm — no hand-coded numpy solver,
  no new primitive, no LLM author;
- the MEASUREMENT is the agent's own harness style (purity / LOSO), label-free.

**Scaffolding I had to add (named plainly):**
1. **The gap PRIORITISER did not exist.** The agent had a detector, not a ranker
   (`SynthesizedGap` had a single consumer). I wrote `domains/gap_prioritiser.py`.
   I chose the criterion to be the agent's *own* compression-payoff drive read off
   its *own* derivation structure (the most defensible agent-grounded ranking, as
   the task allowed). **Residual limit (NOW CLOSED — see addendum below):** the
   criterion was originally computed by thin Python over the gap graph, not a
   graph-resident Rule. It is now a Term/Rule the agent evaluates natively.
2. **No peer LLM was used.** The build was composed directly from the agent's
   harvested science; articulation help was not needed.
3. **I wrote the I/O boundary code** for the build and the probe (mechanical
   translators: matrix↔graph, native Term evaluation, purity scoring). This is the
   permitted world-adapter role, but it is still my code, not the agent's.
4. **Minor mechanical:** the voicing gate and k-means++ seeding in the I/O boundary
   are signal-level mechanics (energy threshold, distance init), not agent
   reasoning — consistent with the CMVN module's existing boundary.

**Net:** the loop ran end to end and the agent self-directed the substantive
decisions — *what gaps exist, which to pursue, and how to build it from its own
science*. The one decision the agent could not make for itself, because the
machinery was missing, was *ranking* its gaps; I supplied that ranker grounded in
the agent's own criterion and flagged it. The build PARTLY closed the gap: the
composed clusterer works well above chance but the front-end caps the invariance
gain — a real result that the agent's own next-ranked gap (LPC) directly addresses.

## Files

- `domains/gap_prioritiser.py` — NEW. Ranks `SynthesizedGap` nodes by the agent's
  compression-payoff criterion; records the `FrontierChoice`.
- `domains/cross_speaker_clustering.py` — NEW. The agent's composed, label-free
  cross-speaker clustering Term-trees (Argmin assignment + Sum/Count update) + the
  mechanical I/O runner.
- `scripts/cross_speaker_clustering_probe.py` — NEW. The self-measurement
  (cross-speaker cluster purity, agent front-end vs raw-spectrum baseline).
- `scripts/order_n_postulates_demo.py`, `domains/order_n_postulates.py`,
  `domains/implication_harvester.py` — UNCHANGED (the agent's synthesis machinery).
- `scripts/sound_graph_probe.py` — UNCHANGED (independent LOSO confirmation of the
  front-end bound).

`tests/test_stt_pipeline.py` + `tests/test_perception_self_assessment.py`: green
(12 passed). Nothing committed; all changes left in the working tree.

## Addendum — the gap-ranking is now GRAPH-RESIDENT (last seam closed)

The §5 residual limit (the ranker was thin Python over the gap graph) is closed.
`domains/gap_prioritiser.py` is now an I/O-boundary adapter around a graph-resident
ranking **Term/Rule** the agent evaluates natively — the same migration
`recognition_graph.py` did for the recognition decision.

**The Term (the agent's reasoning, evaluated by `substrate.evaluate`):**
```
payoff(axis) = Count( Neighbours(axis, "unifies") )      # held postulates unified
score(axis)  = payoff(axis) * 1000  -  min_order(axis)    # shallower-order tie-break
pick         = Argmax over CapabilityAxis of score(axis)
```
Built from the agent's own DSL primitives — `Argmax / NodesWhere / Count /
Neighbours / Times / Minus / Attr` — all of which already exist in
`runners/dsl/src/term.rs` (no new primitive needed). A graph **Rule**
(`pick_frontier_gap`) evaluates the Argmax Term in its effect and writes the chosen
`CapabilityAxis` onto a `FrontierRoot` node natively; `pick_frontier` then records a
`FrontierChoice`. The pick is the Term's value, not a Python sort.

**Faithful:** over the agent's actual synthesized gaps the native Term reproduces the
SAME pick and per-axis payoffs as the old Python ranker — cross-speaker clustering
payoff **6**, word-scale chunking **4**, LPC **2** — and the Rule itself writes the
payoff-6 axis as `picked_axis`.

**What the Python adapter still does (permitted I/O-boundary only):**
`build_axis_env` mints one `CapabilityAxis` node per capability signature the agent
synthesized and wires a `unifies` edge to each *distinct* held postulate that derived
its gaps (mechanical grouping + dedup of the agent's own `derived_from` edges — the
same structural-setup role `recognition_graph.mark_words` plays). There is **no
conditional over graph state that decides anything** — the decision (which axis wins,
via payoff*K − order) is entirely in the Term the Rule evaluates.

**Closure check (substantive loop decisions — all the agent's, in the graph):**
- gap DETECTION — `order_n_postulates` (the agent's order-N synthesis); ✓ graph data.
- gap RANKING — now this Term/Rule; ✓ graph-resident, evaluated natively.
- BUILD-from-science — `cross_speaker_clustering` composed Term-trees; ✓ graph.
- MEASUREMENT — the probe's purity/LOSO harness (label-free); ✓ the agent's style.

**Residual (honest):** Python still does the *structural* grouping/dedup of gap
nodes into axes (an I/O translation, no decision) and the report-formatting in
`rank_gaps`/`pick_frontier`. Folding the grouping itself into a graph production
(e.g. an axis-minting Rule keyed on the capability signature) would remove even that
mechanical Python — but it is translation, not reasoning, so the substantive
seam is closed.
