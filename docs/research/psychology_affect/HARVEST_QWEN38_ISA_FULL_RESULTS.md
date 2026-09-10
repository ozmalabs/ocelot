# Harvest Qwen3.8 — Full is-a Reaping at Open-Vocabulary Scale (block 337000)

## What this run does

The real "full reaping" of the calibration-EARNED tier (is-a): a large,
open-vocabulary subject inventory instead of the 213 hand-curated subjects of
block 336. Subjects are sampled from WordNet's noun taxonomy, which also supplies
the true immediate hypernym of each subject — so fidelity is scored against an
independent gold, not hand-authored labels. WordNet lives ONLY in the
`/applications` venv (`nltk_data`), never committed.

- Inventory: **6,000 subjects, 8,160 candidate hypernyms** (WordNet nouns).
- Elicitation: **6,000 subjects in 1,787 s (~30 min) = 12,090 edges/hr** (batched
  bs=32) — the block-335 throughput held at scale.
- Extracted: **5,772 is-a edges** (228 self-loops dropped), 6,445 nodes.

## Results (measured)

| metric | value | reading |
|---|---|---|
| elicitation rate | 12,090 edges/hr | throughput held at open-vocab scale |
| held-out transitive accuracy | **1.000** (1998/2000 pos, 2000/2000 neg) | substrate derives the closure of the graph it holds |
| direct-edge-only baseline (pos recall) | **0.000** | traversal, not lookup, carries entailment |
| shuffled-graph control | **0.505** | collapses to chance — structure carries it |
| adjacent fidelity vs WordNet gold (exact parent) | **0.108** | |
| valid WordNet ancestor (ANY level, sampled 800) | **0.272** | true is-a rate |

## The headline honest finding: is-a fidelity does NOT hold at open-vocab scale

On the block-336 *curated* subjects, adjacent fidelity was **0.86**. On 6,000
*random WordNet nouns* it collapses:

- **0.108** exact-match to WordNet's immediate parent, and
- **only 27.2%** of reaped edges have the object anywhere in the subject's true
  WordNet ancestor cone (sampled 800) — so even crediting skip-level answers,
  roughly **three quarters of the edges are wrong**.

This is a real negative result, not a bug. The 0.86 was on common, well-known
subjects; the long tail of WordNet (e.g. *chromolithography*, *carbineer*,
*epicanthus*) is where the 4B model's knowledge thins out, and a constrained
argmax over an 8,160-word candidate set that mostly does not apply to a given
subject produces confident-but-wrong picks. **Raw edge count massively overstates
useful yield**: 5,772 reaped ≈ **~1,570 valid** is-a edges.

## Why the substrate metrics are still 1.00 — and why that is NOT a contradiction

The held-out transitive accuracy (1.00) measures whether the substrate correctly
derives the transitive closure of *whatever graph it was given*. It does —
perfectly. That is a property of the substrate's inference, entirely separate
from whether the *input edges* are true. The two controls (direct-edge 0.000,
shuffle 0.505) confirm the inference is genuine multi-hop structure, not lookup
or node-set artifact. So: the substrate's reasoning is sound; the *source's
content* is noisy at scale. Conflating the two would be the dishonest move — they
are reported separately here.

## Why this is safe to keep anyway

Every edge carries `source=qwen3`, `trust=0.5` — the calibrated self-published
band under corroborate-before-assert. The ~73% wrong edges **cannot assert
alone**: they need corroboration and are outgrown/demoted by the agent's own
witnesses (block-333 guard). The band is precisely what lets a noisy
open-vocabulary harvest be ingested without laundering the model's errors into
asserted fact. The seed records the fidelity honestly in its calibration block so
any consumer sees the true yield.

## Read-through for "extract everything"

Throughput is not the wall (12k edges/hr held). **Fidelity is the wall, and it is
subject-distribution-dependent**: high on common concepts, poor on the long tail.
"Extract everything the model knows" is really "extract the common-concept core
reliably"; the tail comes in as low-trust witnesses that only survive if
corroborated. Useful scaling is a *curation* problem (which subjects), not a
compute problem.

## Artifacts

- `scripts/llm_harvest_isa_full.py` (the run)
- `seeds/generated/qwen3_reaped_isa_full.json` (5,772 edges, source=qwen3,
  trust=0.5, full calibration block incl. the honest fidelity numbers)

## Guardrails

- `.so` md5 unchanged: `7efe75eba05b006cafd15dbb4b7da246` (python/JSON only).
- Protected READ-ONLY files untouched.
- Model/venv + WordNet under `/applications` not committed; run log under `var/`
  (ignored).
- Committed block-337 only, add-by-name.
