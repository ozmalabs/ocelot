# Goal-Directed Generation — Plan-Then-Realize (block 344000)

## Why this block changed course mid-build

Block 344 began as a "mass shift": raise the weight of a grounded-grammar term inside
the next-word ranker so grounded clauses would dominate the surface-statistical terms.
Before wiring it further, two parallel literature reviews were commissioned (the
psychology/science of human utterance production; the methods computational systems
use). Both converged on the same verdict: **making the grammar one heavily-weighted
term in a word-ranker is a known failure mode** — a soft feature that never guarantees
clause order or content coverage, and that trades fluency against faithfulness on a
single weight dial. The reviews prescribed **plan-then-realize**: the grammar OWNS
clause order and admissible words as HARD CONSTRAINTS; statistics are demoted to filling
genuine gaps within the grammar-admissible frontier.

The flawed weighted-mass-shift edits were **reverted** (recorded here so the dead end is
not silently forgotten). The one endorsed piece — grounding a copular clause shape so
is-a realizes as an ordered clause — was **kept**. What the reviews also validated and
this block preserves: the self-monitor parse-back (a safety net; Levelt's perceptual
loop / Pickering–Garrod forward model), and the goal + typed-target design including the
SELF/inner-speech target (Vygotsky).

## Architecture (implemented)

`predictive_reading.realize_goal_clause(agent, producer, goal_frame, *, ws_node=None,
language='en', allow_fallback=True, intended_concepts=None, fallback_kwargs=None)`:

1. **Plan.** The grounded sign-grammar producer (`literary_analysis._build_producer`,
   teacher-free, NO LLM) runs `produce(language, goal_frame)`. Its output exposes the
   grammar's clause ORDER (`surface_structure.ordered_slots`) and per-slot admissibility
   (`phonological_word.words`, each `{role, concept, surface, realized}`).
2. **Realize in grammar order.** Walk the slots:
   - `realized==True` → GRAMMAR-FIXED: emit the grammar's surface verbatim
     (`source='grammar'`); the ranker is never consulted.
   - `realized==False` → OPEN slot (the grammar left the bare concept as a placeholder):
     try the statistical ranker (`predict_next_words`, `goal_content=[concept]`) for THAT
     slot only. A result is used ONLY if it genuinely differs from the placeholder
     (`source='gapfill'`); otherwise the grammar lemma stands (`source='grammar_lemma'`).
     The ranker can neither reorder nor touch a fixed slot — it is structurally confined.
3. **Fallback (honest).** If the grammar yields no clause (coverage gap), degrade to the
   rung-1.5 `rollout_unclamped` and return `mode='fallback'` with the full rollout
   sub-result — never a silent empty.
4. **Check.** `self_target_monitor.score_self_target(..., producer=producer)` runs the
   grounded-comprehension parse-back on the realized clause (production closing on
   comprehension) and reports content recovery.

## Result (measured, pure graph, teacher-free)

Four is-a goals, each realized as an ordered grammatical clause:
`isa(poodle,dog)` → `"The poodle is the dog."`, `isa(wolf,mammal)` →
`"The wolf is the mammal."`, `isa(dog,mammal)`, `isa(sparrow,bird)`.

| claim | result |
|---|---|
| C1 grammar owns order (surface == grammar's `overt_speech`, ordered clause) | **4/4** |
| C2 ranker structurally confined (fixed slots byte-identical, order == `ordered_slots`, sources correct) | **4/4** |
| C3 honest fallback (ungrounded goal → reported `mode='fallback'`, not silent empty) | **PASS** |
| C4 content recovered (grounded-comprehension parse-back, coverage 1.0) | **4/4** |

The output is now a **real ordered grammatical clause owned by the grammar**, not a
ranked bag of words — the correction the reviews prescribed, verified.

## Honest sub-finding: gap-fill is a proven-SAFE no-op at this lexicon

C2 is proven structurally (the ranker is confined to open slots and cannot override or
reorder), but with an important caveat that is NOT hidden: at this rung's lexicon the
ranker never actually SUBSTITUTES. Because gap-fill conditions on `goal_content=[concept]`
with a high goal weight, the ranker's top-1 is that very concept — so the "fill" always
equals the grammar's placeholder and the grammar lemma stands. Net: **the grammar owns
the entire clause and the ranker adds nothing.** That is the correct and safe behavior
here (no spurious substitution), but it means the *value* of gap-fill is not yet
demonstrated. Genuine gap-fill requires a register offering lexical ALTERNATIVES
(synonymy / inflection the grammar did not ground) for the ranker to prefer over the bare
concept — which this lexicon does not model.

Also fixed during this block (defects the experiment surfaced): `gaps_filled` now counts
only genuine substitutions; and when nothing substitutes, the grammar's clause stands
verbatim (casing + terminator preserved) rather than being space-rejoined.

## Deferrals (explicit)

- **Genuine lexical-alternative gap-fill** — needs grounded synonymy/inflection so the
  ranker has a real alternative to the concept placeholder.
- **Self-conditioned-rollout gap-fill** — per the block's amendment, gap-fill stays a
  single top-1 per slot this rung; a rollout for gap-fill is its own later rung.
- **Fidelity refinements the reviews flagged, framed as future rungs, not blockers:**
  lemma/lexeme + functional/positional level structure with human-like error signatures;
  incremental VARIABLE planning scope; a forward-model early-drift monitor
  (Pickering–Garrod) in addition to the after-the-fact parse-back.
- Determiner note: the copula grounds "X is **the** Y" not "X is **a** Y" (determiner
  grounding); acceptable for the ordered-clause claim, recorded honestly.

## Guardrails

- `.so` md5 unchanged: `7efe75eba05b006cafd15dbb4b7da246` (python only).
- Protected READ-ONLY files untouched; `conceptualizer.py` untouched (its
  no-Python-decision audit unaffected).
- Grounding is teacher-free (`teacher_stub`, no LLM); no model/venv/`/applications`.
- Committed block-344 only, add-by-name.

## Artifacts

- `domains/predictive_reading.py` — `realize_goal_clause` + `_gapfill_slot` (additive).
- `domains/literary_analysis.py` — copula exemplar in `_GRAMMAR_BANK` (is-a → ordered clause).
- `scripts/gen_rung2_plan_then_realize.py` — the experiment (C1–C4).
