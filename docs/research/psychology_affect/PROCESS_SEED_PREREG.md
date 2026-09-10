# Process extraction as CAN graph dynamics — PRE-REG

**Block**: 329000. Build target: `domains/llm_process_seed.py`; measure:
`scripts/llm_process_seed_measure.py`. Substrate BP / grammar are PROTECTED
(`can_native_bp.py`, `seeds/can_native_reimplementation.json`), read-only —
built TO; NO new rewrite rules / Gamma productions are installed.

## Motivation

Tier 3 (hardest) of the extraction direction, after knowledge (327: relational
facts, held-out entailment) and concept (328: a relation as a reusable operator,
held-out transfer). A PROCESS is a PROCEDURE the LLM runs — a transformation of
an input configuration into an output configuration — extracted as graph
DYNAMICS (a transport operator, connecting to the transport arc 324–326) and
applied to inputs it never saw. The bar rises from held-out TRANSFER to held-out
APPLICATION. Process studied: `negate` ("X is Y" → "X is not Y").

## Claims (falsifiable)

**Claim 1 — the process extracts and applies in the LLM representation.** A
transport operator N (fit on context-A affirmation→negation vector pairs) maps a
held-out context-B affirmation to a representation that reads as NEGATED under a
valence probe fit on A. Prediction: N(B-affirmation) reads negated well above an
identity baseline (no transform → still affirmed) and a shuffled-N control.
FALSIFIED IF extracted-N ≈ identity/shuffle (no transferable procedure).

**Claim 2 — the process runs on the substrate as graph dynamics.** Expressed as
a TRANSPORT settle over Concept mode-nodes (block 324/325 mechanism, no new
grammar), the process transforms a held-out B input config to an output config
that reads negated, above the identity baseline. Prediction: substrate-settle
extracted-N beats identity. Reported honestly against the known block-326
discretisation ceiling.

**Claim 3 — application, not memorisation.** Both readings apply N to B inputs
DISJOINT from the A extraction, with NO LLM at query time; controls (identity,
shuffled-N) must fail.

## Method

- EXTRACT (model venv, offline): `statement_vectors` (contextual last-token at a
  mid layer), `fit_process_operator` (ridge N: input→output on A pairs),
  `fit_valence_probe` (affirm-vs-negate direction on A). Save N, probe, held-out
  B vectors; also a K-mode-space version (PCA over A) for the substrate settle.
- REPRESENTATION application (numpy, no LLM): apply N to B affirmations, read
  valence; vs identity and shuffled-N.
- SUBSTRATE application (substrate only): `run_process_substrate` — N as
  transport edges over mode-nodes, `run_loopy_bp` settle, read output config
  valence; vs identity. Continuous-K readout isolates K-compression from the
  Ising-settle loss.

## Anti-faking

- Context-B statements DISJOINT from the A extraction — the process never saw
  them.
- NO LLM at query time: N, the probe, and the coupling are frozen recovered
  structure; the transforms are numpy / substrate ops.
- Two controls: identity (a no-op process cannot transform) and shuffled-N (a
  scrambled operator cannot negate).
- The substrate execution is reported HONESTLY against the block-326
  discretisation constant + the K-mode compression — the reduced substrate
  fidelity is stated, not hidden behind the crisp representation result.
- NO new grammar: a process is a transport-operator + BP settle over existing
  Concept / causal_influence types (protected seed grammar untouched).
- **default == today**: `.so` md5 stays `7efe75eba05b006cafd15dbb4b7da246`;
  protected CAN internals + seed grammar untouched; models + venv under
  `/applications`, NOT committed.
