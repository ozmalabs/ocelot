# Concept extraction as a reusable CAN operator — PRE-REG

**Block**: 328000. Build target: `domains/llm_concept_seed.py`; measure:
`scripts/llm_concept_seed_measure.py`. Substrate BP / grammar are PROTECTED
(`can_native_bp.py`, `seeds/can_native_reimplementation.json`), read-only —
built TO.

## Motivation

Tier 2 of the extraction direction (after knowledge, block 327). Knowledge was
relational FACTS the substrate could store and traverse. A CONCEPT is harder: it
is a RELATION AS A REUSABLE OPERATOR — an identity that applies to entities it
never co-occurred with. The bar rises from held-out ENTAILMENT (327) to held-out
TRANSFER: extract the concept from context A, apply it in context B it never saw,
and check the substrate produces the right answer BY THE CONCEPT'S STRUCTURE,
not by stored B-instances. Concept studied: `opposite-of` (antonymy) — symmetric,
composable, and with a natural substrate form (antonyms want opposite states =
negative Ising coupling).

## Claims (falsifiable)

**Claim 1 — the concept has an extractable GEOMETRIC signature that transfers.**
A linear operator W fit on context-A antonym pairs (in the LLM's own
representation) recognises held-out context-B antonym pairs above chance and
above a random-W control — measured as the separation (AUC) between true-B
antonym alignment and random-B-pair alignment. Prediction: extracted-W AUC >
0.5 and > random-W. FALSIFIED IF extracted-W ≈ random-W (no transferable
concept, only memorised A instances).

**Claim 2 — the concept has a SUBSTRATE signature that executes on held-out B.**
Two opposite Concept nodes couple with a NEGATIVE Ising weight; clamping one
settles the other to the OPPOSITE state on the substrate's own BP. For held-out
B pairs the concept never saw, the extracted (negative) coupling settles the
partner opposite; a shuffled (positive) coupling settles it to the SAME state
(the wrong answer). Prediction: negative-coupling → opposite for B pairs;
positive-coupling control → same. FALSIFIED IF the coupling sign does not
determine the settle (the substrate signature is not the concept's dynamics).

**Claim 3 — transfer, not memorisation.** Both signatures are applied to B
families DISJOINT from the A extraction, with NO LLM at query time. The concept
is a reusable operator, not stored instances.

## Method

- EXTRACT (model venv, offline): `word_vectors` (per-word representation),
  `fit_opposite_operator` (ridge W: vec → opposite-vec on A pairs, both
  directions since opposite is symmetric). Save W + vectors + A/B split.
- GEOMETRIC transfer (substrate-free numpy, no LLM): alignment
  `Ŵ·vec(a) · vec(b)`; AUC of true-B pairs vs random-B pairs; vs random-W.
- SUBSTRATE transfer (substrate only): `opposite_settle` — Concept nodes with a
  negative coupling, clamp one, `run_loopy_bp` settle the other; vs a positive
  (shuffled-sign) control.

## Anti-faking

- Context-B families are DISJOINT from the A extraction — the concept never
  co-occurred with them.
- Query time is representation + substrate only; the LLM only provided the
  vectors offline (no LLM in the transfer loop).
- Two controls: random-W (geometric) and positive-coupling (substrate) — a
  scrambled concept must fail.
- Honest readout: the geometric transfer is reported as RELATION RECOGNITION
  (AUC), not a 1-of-N retrieval (which is too brittle for a 0.6B model — the
  brittle retrieval framing is reported as a negative, not hidden).
- **default == today**: `.so` md5 stays `7efe75eba05b006cafd15dbb4b7da246`;
  protected CAN internals + seed grammar untouched (read-only, built-to);
  models + venv under `/applications`, NOT committed.
