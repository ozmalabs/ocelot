# Capability Suite — Tracks 1 & 3 Results (category recoverability + compression-meaning)

Tracks 1 and 3 of the capability suite (see `CAPABILITY_SUITE_PLAN.md`), scored on the
two remaining metrics of Rubric A (arXiv:2505.17117): RQ1 category recoverability and
RQ3 the ℒ compression-meaning objective. Both metrics are the paper's; neither invented.

## Track 1 — Category recoverability (Rubric A RQ1: AMI / NMI / ARI)

**Rubric:** chance-corrected clustering agreement (AMI/NMI/ARI) between a system's item
grouping and the human categories. Published reference: LLMs recover categories only
approximately from distributional geometry (human-aligned band ~0.55 AMI, encoder peak
~0.60).

**Result (`track1_category_recoverability.py`, exit 0, R1–R4 PASS):**

| condition | AMI | reading |
|-----------|-----|---------|
| **structural** (is-a graph) | **1.000** (NMI 1.0, ARI 1.0) | exact recovery |
| **geometry-only** (commitment axis) | **−0.143** | felt axis carries no category identity |
| **structural, is-a edge removed** | **0.000** | grouping rides the edge, not the attr |
| LLM reference (published) | ~0.55 | emergent, approximate |

**The finding is the asymmetry.** The substrate recovers human categories *exactly*
because it stores them as **explicit is-a structure** the train of thought navigates —
so it "clears" the LLM ~0.55 band, but this is **not the same achievement**: it is free
structural recovery, not emergent geometric induction. Two controls make this honest and
concrete rather than a caveat:

- **Geometry-only (R2):** grouping by the felt `dynamical:commitment` coordinate alone
  scores AMI ≈ 0 — the felt axis encodes *within-category typicality*, orthogonal to
  category identity. So the substrate would **not** match the LLM if forced to induce
  categories from raw geometry.
- **Non-circular (R3):** removing the is-a edges drops structural AMI from 1.0 to 0.0
  (the `category` attr alone does not carry the grouping) — the score rides the **edge
  structure**, not the label attr.

Symbolic explicit structure vs LLM distributional geometry: the two systems keep
category identity in fundamentally different places, and the suite reports the metric for
both with the asymmetry stated.

## Track 3 — Compression-meaning balance (Rubric A RQ3, the ℒ objective)

**Rubric:** `ℒ(X,C;β) = I(X;C) + β·(1/|X|)·Σ_c Σ_{i∈c} ‖e_i − ē_c‖²` (complexity in bits
+ within-cluster distortion). Lower ℒ = more "efficient." Published finding: LLMs
**over-compress** to a lower ℒ than humans by discarding within-category detail; humans
keep an "inefficient," higher-ℒ representation that preserves meaning.

**Result (`track3_compression_meaning.py`, exit 0, L1–L4 PASS):** embeddings = the
substrate's own signature coordinate on the graded axis, at each grain; clustering = the
human categories.

| representation | complexity | distortion | ℒ |
|----------------|-----------|-----------|---|
| **coarse** (pre-mint / over-compressed) | 2.572 | **0.000** | **2.572** |
| **fine** (post-mint / detail preserved) | 2.572 | 1.983 | **4.555** |

- **L1** minting **raises ℒ** by +1.98 — toward the human "rich" band, away from the
  over-compressed floor.
- **L2** the move is entirely the **distortion (meaning) term**; complexity (bits) is
  unchanged (same category clustering) — minting adds preserved detail, not bits.
- **L3** the coarse representation has **distortion = 0** — all items collapse to one
  coordinate, the LLM-style maximal compression that discards the fine distinction.
- **L4** integer coordinates; teacher-free (pure graph reads).

This is the direct RQ3 analogue of the human-vs-LLM contrast: where LLMs sit at the
low-ℒ over-compressed floor, minting moves the substrate up toward the human
detail-preserving band.

## Guardrails

Additive only. `.so` md5 `7efe75eba05b006cafd15dbb4b7da246` frozen; no protected-file
edit; `conceptualizer.py` untouched (audit green); nothing under `/applications`. Files:
`tests/capability/minting/{track1_category_recoverability.py, track3_compression_meaning.py}`,
the `build_multi_category`/`isa_parent` additions to `runners/substrate_runner.py`, and
this doc.

## Suite status

Prove/stretch/measure now covers all three Rubric-A metrics (RQ1 T1, RQ2 T2, RQ3 T3) and
the Rubric-B readiness gate (T4). Remaining: **Track 5** — Potemkin validity keystones,
the OFF-by-default teacher-free LLM harness, the human protocol, and the unified
side-by-side scorecard with FLEX CIs.
