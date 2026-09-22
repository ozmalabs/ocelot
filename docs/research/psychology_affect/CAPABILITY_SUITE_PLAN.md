# Capability Suite Plan — Gated-Minting Train of Thought vs Humans and LLMs

## Purpose

Prove, stretch, and measure the capability introduced by the train-of-thought arc
(blocks 341→351), with the sharpest focus on **block 351: gated dimension-minting** —
an agent that, mid-reasoning, detects a *recurring* conceptual gap (a residual that
fits no held axis) and **coins a new dimension** for it, teacher-free, in discrete
quanta. The suite benchmarks the substrate against **humans** and **LLMs** on
**published rubrics**, not invented scales.

## The capability under test (measurable form)

1. **Accommodation vs gap-fill** — mint on a *persistent* residual; refuse a
   *transient* one. (The core novel claim.)
2. **Over-minting resistance** — refuse a duplicate gap (the sd-loop dedup guard).
3. **Fine-grained fidelity** — the minted axis preserves distinctions coarser
   representations compress away.
4. **Category recoverability** — the minted structure still recovers human category
   boundaries.
5. **Compression–meaning balance** — where the system sits on the efficiency /
   richness frontier.
6. **Teacher-free + discrete-quanta discipline** — no LLM at loop time; integer
   resolution.

## Anchor rubrics (found by literature search, not invented)

### Rubric A — Compression-vs-Meaning (IB / RDT)
Soffer, Jurafsky, LeCun, Shwartz-Ziv, *From Tokens to Thoughts*, **arXiv:2505.17117**.
Releases a human baseline (1,049 items / 34 categories from Rosch 1973/1975 +
McCloskey & Glucksberg 1978; membership + typicality) and defines three metrics:

- **RQ1 categorical alignment** — Adjusted / Normalized Mutual Information (AMI/NMI)
  and Adjusted Rand Index (ARI) between a system's clusters and human categories.
  Reference points: human-aligned ≈ 0.55 AMI; encoder LLMs peak ~0.60; many decoder
  LLMs much lower on static embeddings.
- **RQ2 internal structure** — Spearman ρ between item-to-centroid similarity and
  human typicality. Reference points: most decoder LLMs ρ < 0.2; BERT ρ ≈ 0.38.
- **RQ3 the trade-off** — the objective
  `ℒ(X,C;β) = I(X;C) + β · (1/|X|) Σ_c Σ_{i∈c} ‖e_i − ē_c‖²`
  (complexity = bits, distortion = within-cluster spread). Lower ℒ = more
  "efficient." Finding: LLMs over-compress (lower ℒ) and lose nuance; humans keep
  richer, "inefficient" structure.

*(Rubric content rephrased for licensing compliance; see the paper for exact wording.)*

### Rubric B — Conceptual-change with a readiness gate
Carey, *The Origin of Concepts* (precis, PMC3489495); the false-belief acquisition
study, PMC4001252. A scored **pre-test → exposure → post-test** protocol that credits
representational change **only when a genuinely new representation is constructed and
used**, and **only for learners "conceptually close" beforehand** (a readiness gate).
This is the human-science analogue of our **persistence gate**: mint only when the gap
*recurs* (the learner is "ready"), never on a single miss. *(Rephrased for compliance.)*

### Statistical spine — FLEX
**arXiv:2107.07170.** Sample-size design, confidence intervals, controlled episode
counts — so substrate / human / LLM numbers are comparable, not point estimates.

### Validity keystones — Potemkin
**arXiv:2506.21521.** A shared human/LLM benchmark is only valid if failures are
human-like; include adversarial *keystone* items that pass a surface mint test without
real representational change. If the suite can't catch them, its validity is void.
*(Rephrased for compliance.)*

## Vendored data

`tests/capability/minting/fixtures/rosch1975_typicality.json` (+ `PROVENANCE.md`) — a
faithful reconstruction of the Rosch (1975) typicality **rank** norms, 6 categories.
The ρ metric consumes only the order, which the reconstruction gets right. Honest
about not being the raw rating table / the arXiv supplement (both unfetchable at build
time). Replaceable when exact values surface.

## The five tracks

| Track | Question | Rubric / metric | Status |
|-------|----------|-----------------|--------|
| **T1** | Does the minted-axis clustering recover human category boundaries? | A · RQ1 AMI/NMI/ARI | **complete; see [CAPABILITY_T1_T3_RESULTS.md](CAPABILITY_T1_T3_RESULTS.md)** |
| **T2** | After minting, does item-to-set-point distance correlate with human typicality? | A · RQ2 Spearman ρ | **complete; see [CAPABILITY_T2_T4_RESULTS.md](CAPABILITY_T2_T4_RESULTS.md)** |
| **T3** | Does minting move ℒ toward the human rich band rather than the LLM over-compressed band? | A · RQ3 ℒ objective | **complete; see [CAPABILITY_T1_T3_RESULTS.md](CAPABILITY_T1_T3_RESULTS.md)** |
| **T4** | Persistent → mint; transient → no mint; duplicate → refused at the right time? | B readiness gate · precision/recall + latency | **complete; see [CAPABILITY_T2_T4_RESULTS.md](CAPABILITY_T2_T4_RESULTS.md)** |
| **T5** | Are surface-pass-without-change keystones caught, with a cross-population scorecard? | Potemkin + FLEX CIs | **complete; see [CAPABILITY_T5_RESULTS.md](CAPABILITY_T5_RESULTS.md)** |

### Current interpretation

All five tracks have result documents and executable local evidence. They demonstrate bounded mechanism behavior under the stated fixtures and rubrics; they do **not** demonstrate general agency, P5 transfer, independent custody, production deployment, or a general-intelligence claim. The results retain their stated caveats: T1’s AMI reflects explicit is-a structure rather than emergent geometric induction; the LLM comparison uses published reference values; the human data is an order-faithful reconstruction; and all conclusions are bounded to the tested local substrate.

## Prove / stretch / measure

- **Prove (completed local tracks)** — T1 category recoverability and T4 readiness-gated accommodation have result documents and falsifiable local verdicts.
- **Stretch (completed local tracks)** — T2 fidelity and T3 compression/meaning were measured at the tested grain and protocol settings; broader scaling remains future work.
- **Measure (completed local track)** — T5 tests Potemkin keystones and records the cross-population scorecard with the available published/reference baselines and declared uncertainty.

The suite is a capability-evidence layer. Any promotion into the general-agency roadmap or P5 evaluator requires a separate preregistration, evaluator custody, held-out data, containment evidence, and an explicit gate; these results do not supply those conditions.

## Architecture — three runners, one scorer

- **substrate runner** — plays each scenario through
  `domains.minting_train_of_thought.run_minting_train_of_thought` (and the block-349
  aperture-grain tube it rides on), emitting the minted axes, the induced item
  ordering, and clusters. Teacher-free (ask-spy must be 0).
- **LLM harness** — the SAME items + questions as a prompt bundle. **OFF by default /
  teacher-free**: it emits a prompt file you point at a model; it does **not** call any
  network unprompted. Results are pasted back into a results file the scorer reads. Any
  actual model call is an explicit, user-initiated step.
- **human protocol** — the same battery as a written protocol (present the item
  sequence, ask the readiness/typicality questions) + a results-entry JSON the scorer
  reads. Lets a human subject be scored on the identical rubric.
- **common scorer** — computes AMI/NMI/ARI (T1), Spearman ρ (T2), ℒ (T3), gate
  precision/recall + latency (T4), keystone-catch rate (T5), each with FLEX-style CIs,
  and prints a **side-by-side scorecard**: substrate / human / LLM.

## Layout

```
tests/capability/minting/
  fixtures/
    rosch1975_typicality.json      # vendored human baseline (rank norms)
    PROVENANCE.md
  runners/
    substrate_runner.py            # run_minting_train_of_thought over a scenario
    llm_harness.py                 # OFF-by-default prompt bundle + results reader
    human_protocol.md              # written protocol + results-entry format
  scoring/
    metrics.py                     # AMI/NMI/ARI, Spearman rho, L objective, gate P/R
    scorecard.py                   # side-by-side substrate/human/LLM + CIs
  track2_fine_grained_fidelity.py  # T2 experiment (result documented)
  track4_accommodation_gate.py     # T4 experiment (result documented)
  track1_category_recoverability.py # T1 experiment (result documented)
  track3_compression_meaning.py     # T3 experiment (result documented)
  track5_keystones_and_scorecard.py # T5 experiment (result documented)
```

## Guardrails (every commit)

Additive only. `.so` md5 `7efe75eba05b006cafd15dbb4b7da246` frozen (Python/JSON only —
never rebuild Rust). No edit to any protected READ-ONLY file
(`runners/dsl/src/can_ops.rs`, `domains/can_junction_tree.py`,
`domains/can_native_bp.py`, `domains/model_reader.py`); no touch to
`domains/conceptualizer.py` (its no-Python-decision audit stays green). Nothing under
`/applications`. Commit track-by-track: `git diff --cached --stat` FIRST, `reset`, then
add-by-name (never `git add -A` — the working tree carries unrelated dirty
papers/drafts/tools). On `main` atop `ede0c796`.

## Honesty commitments

- Metrics are the published ones; where reconstruction was necessary (the human data),
  it is documented and order-preserving.
- The LLM comparison uses the paper's already-published LLM numbers as reference; any
  fresh LLM run is user-initiated and teacher-free with respect to the substrate loop.
- Every track prints a falsifiable PASS/FAIL verdict and an HONEST NEGATIVE path if the
  claim does not hold on the substrate as built.
