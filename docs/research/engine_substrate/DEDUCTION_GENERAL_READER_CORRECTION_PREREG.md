# DEDUCTION GENERALIZATION — GENERAL-READER CORRECTION — PREREG

**Status: PREREG for a CORRECTION, not new design.** This is a short note
(house style permits brevity for a correction, per the standing prereg
discipline) registering what I expect to find and change, before editing,
in an isolated worktree.

**What is being corrected.** `docs/research/engine_substrate/
DEDUCTION_GENERALIZATION_PREREG.md`/`_RESULTS.md` (commit `2f3e872`, merged
`a20e334`) built `domains/propositional_deduction.py` with its own
hand-rolled, 8-surface-form token-pattern mini-grammar (`_FORMS`,
`_tokenize`, `_match_pattern`) to parse conditional prose ("if X is a bird,
X can fly") into an antecedent/consequent pair. The creator's correction,
verbatim: *"This inference was already present in the understanding and
reading sections - check it"* and *"The whole point of this is to make
general machinery."*

**What I expect to confirm, before touching code:**

1. `seeds/reading_constructions.json` (`local_id: 48`) already declares a
   GENERAL `ShapeSignature{kind:"construction", name:"conditional"}`
   (`signature:[["IF"],["THEN"]]`, `predication:"implies"`,
   `ground_template:{"pred":"implies","mode":"pair"}`), decoded by
   `domains/reading_collapse.py` through the SAME `ShapeDecode` mechanism
   every other construction (definitional/attributive/event/...) uses.
2. `tests/test_reading_collapse.py:57` already exercises this construction
   live, today, unrelated to the deduction rung: `("if it rains then the
   ground is wet", "conditional", ["implies", "it_rains", "ground"])`.
3. `domains/propositional_deduction.py`'s own docstring never mentions
   `reading_collapse.py` at all — strong circumstantial evidence the general
   mechanism was never checked before the bespoke grammar was built.

**What I expect the correction to require, and the open question I am NOT
pre-deciding:** replace `parse_conditional`'s bespoke grammar with a call
into the general reading pipeline. The OPEN QUESTION, to be resolved by
actually running the code, not assumed: does the shared `conditional`
construction's own `implies(...)` predication (the one
`tests/test_reading_collapse.py:57` proves) directly supply what
`mint_logical_schema` needs (an `antecedent_attr` + `consequent_relation` +
`consequent_attr` triple), or does its `"pair"` ground_template (which reads
only `roles[0]`/`roles[1]`) turn out to be too coarse for the specific
capability/property-consequent shape this module mints from ("if X is a P,
X can/is Q") — in which case the smallest correct adapter is needed, and
must be reported precisely rather than silently building a second grammar
under a different name.

**What must NOT change, per the task:** `seeds/inference_knowledge.json`
(8 existing schemas), `domains/ground_reductions.py`,
`domains/comprehend_theorem.py`, the inert logic seed files,
`tests/test_reading_collapse.py` (consumed, not edited), the
`knowledge_logical` `ShapeSignature` schema shape itself, and the
gap-detect/collapse/mint wiring in `domains/inference_generation.py`
(pre-verified correct by the orchestrating session; this rung re-confirms
rather than re-derives that verdict).

**Base:** `main` @ `a20e334` (`Merge deduction-generalization: propositional
modus ponens through the general collapse pipeline, GO`), verified via
`git log --oneline -1 main` before creating the worktree.

**Success criteria (GO/NO-GO):** (a) `parse_conditional`'s bespoke
token-pattern grammar is fully removed, not kept as a fallback; (b) the
replacement demonstrably ingests through `reading_collapse.py`'s general
pipeline (a source fact, not an assertion); (c) the SAME four demo outcomes
(bird/fly hand-seeded, fish/swim prose-minted, dog discriminative null,
glass empirical-pipeline coexistence) reproduce byte-identically in OUTCOME;
(d) `tests/test_reading_collapse.py` diffs to zero against its pre-change
content; (e) `tests/test_deduction_generalization.py` passes (updated where
it tested the old parser's signature, not merely deleted); (f) whatever
adapter, if any, was needed is named and justified with a real measurement,
not assumed away.
