# DEDUCTION EXTENSION — modus tollens + conjunctive antecedents — PREREG

**Base:** `main` @ `8af4fde` (re-checked; current tip when this worktree was
cut). **Worktree:** `/home/matt/ozmadev/ocelot-worktrees/deduction-extension`.
**Branch:** `deduction-extension`.

This rung extends the WORKING facility landed today in
`DEDUCTION_GENERALIZATION_RESULTS.md` (hand-seeded + prose-minted single-
antecedent modus ponens through `inference_generation.py`'s gap-detect →
`ShapeDecode` → mint → re-run-fixpoint pipeline, sourced from `ShapeSignature
{kind:"knowledge_logical"}`) and `DEDUCTION_GENERAL_READER_CORRECTION_
RESULTS.md` (the parser is the GENERAL reading pipeline, not a bespoke
grammar). Read in full before this doc: `domains/propositional_deduction.py`,
`domains/inference_generation.py`, `seeds/inference_logical.json`.

Everything below was investigated by RUNNING the real engine in this
worktree before writing this prereg (not assumed) — findings and the file:line
citations that back them are recorded here, and the build plan follows from
them.

---

## 1. Negation representation — investigated, found, precise

**No first-class negation/polarity representation exists in the general
reading pipeline.** Grepped `domains/reading_collapse.py`, `domains/
situation_model_reader.py`, `seeds/reading_constructions.json` for
`negat`/`polarity`/`NEG` — zero hits of that shape. `"not"` is listed only as
a member of the `AUXILIARY` `ClosedClass` (`seeds/reading_constructions.json`,
the `note` field: *"AUXILIARY / modal / negator forms the argument-structure
parse skips before the finite main verb"*) — i.e. by design "not" is meant to
be a function word the parse passes over, not something that mints a scoped
`Not`/polarity relation.

**What actually happens, run live:**

```
'the ground is not wet'   -> definitional: [['is_a', 'ground', 'not_wet']]
'the ground is wet'       -> definitional: [['is_a', 'ground', 'wet']]
'x is not a bird'         -> definitional: [['is_a', 'x', 'not_bird']]
'tweety cannot fly'       -> event:        [['can', 'tweety', 'not_fly']]
'the mammal is not warm-blooded' -> definitional: [['is_a','mammal','not_warm-blooded']]
```

The literal token `not` SURVIVES as part of the complement's underscore-joined
span — the SAME multi-word-role-span joining mechanism that turns "warm
blooded" into "warm_blooded" (`propositional_deduction.py`'s own `_norm_attr`
docstring already documents this joining convention) also, incidentally,
joins "not wet" into "not_wet" because nothing in that join step special-cases
or strips `not`. **This is an ACCIDENTAL byproduct of complement-span joining,
not a designed negation construction** — there is no separate polarity field,
no `Not`/`deny` relation, and the SAME literal token behaves differently by
construction kind (`definitional` cleanly prefixes the single-word complement;
`event`, for a capability form like "cannot fly", produces `can(tweety,
not_fly)` — the verb's own object gets the prefix, not a `can_`-shaped
attr — see §3 below for why this asymmetry matters for the antecedent/
consequent-shape mapping this module's schemas already use).

**Verdict, precisely, as asked:** a `"not_" + <base>` NAME PREFIX is the only
usable regularity, reproducible and consistent for every COPULAR
(`is_a`-relation) form tested, and it is exactly the naming convention this
module's OWN existing code already half-uses (`consequent_attr = "can_" +
cons_tail` for a capability, plain `cons_tail` for a property —
`propositional_deduction.py:227`). Reusing this SAME prefix convention
SYMMETRICALLY (negate a held attr name by prefixing `not_`, and know how to
invert `mint_logical_schema`'s own `can_` transform when doing so) requires
NO new representational work in `reading_collapse.py`/`situation_model_
reader.py` — it is a plain, mechanical string transform of a value this
module's own code already produces, not a new construction. This is the
design adopted below (§3). It is NOT a general negation-scoping mechanism —
a negated clause with more than one word in its complement, or negation
scoped over anything other than a single-token copular complement, is out of
what this reuses (not attempted; would be new representational work, per the
task's own framing of the open question).

---

## 2. Modus tollens — PLAN: reuse the EXISTING gap-detect/resolve pair
UNCHANGED; the extension is graph DATA, not new decode/resolve code

Investigated directly (run live, see the worktree's throwaway probe output
folded into §1/§3 of the RESULTS doc): offering the SAME `knowledge_logical`
codebook pool a SECOND, MECHANICALLY-DERIVED companion `ShapeSignature` node
per held implication — its **contrapositive** (`P⇒Q` entails `¬Q⇒¬P`,
classical logic, not a new interpretive decision) — means
`detect_implication_gaps`/`resolve_implication_gap`/`decode_gap`
(`domains/inference_generation.py`, ALL THREE UNCHANGED) already run modus
tollens with ZERO new gap-detection code, because:

- `detect_implication_gaps` already offers EVERY resident `attr==1` fact as a
  candidate antecedent, breadth-first, with no attr-name allowlist — a
  `not_wet==1` fact is offered exactly like a `bird==1` fact, already, today.
- `decode_gap`'s `Covers`-based structural match is exact-literal on the
  `signature` field's string tokens (confirmed live: a schema whose
  `signature` is `[["holds","not_wet"]]` does not ambiguously also match a
  goal of `[["holds","rain"]]` — tested directly, zero false-positive
  crossover between the forward schema and its contrapositive).
- The mint (`situation_model_reader.ingest_predication`) is relation-agnostic
  about the attr name — `not_rain` mints exactly like `can_fly` does.

**So the task's own hypothesized "second gap-detection pattern" turns out,
on measurement, not to be needed at all** — the ONLY new code is a small,
MECHANICAL contrapositive-derivation helper in
`domains/propositional_deduction.py` (parse `signature`/`supplies`, negate
both sides using the SAME `not_`/`can_` prefix convention already used
inside this module, install a companion node), called (a) once per
freshly-minted forward schema inside `mint_logical_schema`, and (b) once
over the seed-installed schemas inside `ensure_logical_seeds`
(`inference_generation.py` — ONE new call at the end of that existing
function, mirroring the EXISTING `_ensure_warning_lexicon`/`_ensure_trust_
lexicon` "additive, idempotent, safe on an already-loaded graph" pattern
already used there).

**Predicted, before building:** GO — clean, minimal, zero regression risk to
`detect_implication_gaps`/`resolve_implication_gap`/`decode_gap` (all three
byte-unchanged). The one genuine subtlety, already investigated (§1): a
capability consequent (`can_fly`) needs its contrapositive's SIGNATURE side
computed as `not_` + the BARE verb (`not_fly`, matching what the general
reader's event-construction actually produces for "cannot fly"), not `not_`
+ the stored `can_`-prefixed attr name — handled by checking the `can_`
prefix (a plain, reversible read of this module's OWN naming convention, not
a new decision about text).

**Named, honestly, before building:** the live TEXTUAL round-trip (raw
prose → derived fact) will be demonstrated for the PROPERTY-consequent case
only (`is_a` relation — the rain/wet form, matching the task's own literal
example exactly). The CAPABILITY-consequent case (`can`) has a PRE-EXISTING
gap, unrelated to this rung: `situation_model_reader._is_property_pred`
(`situation_model_reader.py:324-336`) only treats `is_a`/`is`/`cop`/
`designate` as property-setting relations; a `can`-relation predication
routes through the eventive/COS branch instead, so "Tweety can fly" stated
as raw declarative text does not set `can_fly=1` via ordinary text
ingestion EITHER (confirmed by reading `ingest_predication`, not assumed) —
the ORIGINAL modus-ponens landing never round-tripped a capability
consequent through raw text for this reason (it only ever mints it via the
mechanical `ingest_predication` call, never states it as text and re-reads
it). The contrapositive mechanism will still be built to handle the
capability form CORRECTLY at the graph-data level (proven via direct
`ingest_predication`/`decode_gap` calls, not text parsing), and this
pre-existing text-ingestion gap will be reported, not silently worked
around or fixed (fixing it is `situation_model_reader.py` surgery, out of
this rung's scope).

---

## 3. Conjunctive antecedents — PLAN: real new machinery, small and scoped

Investigated directly (run live): `ShapeDecode`'s `Covers`-based matcher
ALREADY handles a MULTI-item goal against a multi-item `signature` correctly
when FULLY covered — minted a throwaway 2-conjunct `knowledge_logical` test
schema (`signature: [["holds","p"],["holds","q"]]`) and called `decode_gap`
with both facts offered: **`authored: True`, `covered_count: 2`, matching
the full signature** — the SAME joint-decode mechanism the constructions'
own multi-marker skeletons (`[["IF"],["THEN"]]`) already use for a different
purpose. This confirms the SCHEMA SHAPE itself needs zero change (a
`signature` list of length ≥ 2 is already fully expressible and already
decodes as ONE candidate) and confirms the task's hoped-for reuse is REAL for
the matching primitive.

**But a genuine gap was found, also by running it, not assumed:** offering
ONLY `p` (NOT `q`) to the SAME 2-conjunct schema still returns `authored:
True`, `fit: 2 > 0`, `residual: ()` — **`ShapeDecode` does NOT require full
signature coverage before "authoring"; `Covers` accepts PARTIAL coverage as a
valid (lower-fit) match.** `residual` in the result names goal items left
uncovered, not signature items left unsatisfied — so it is EMPTY even when
the schema needed 2 antecedents and only got 1. If `resolve_implication_gap`'s
existing `fit <= 0` guard were reused as-is against a conjunctive schema, it
would MISFIRE on partial evidence (exactly the false positive the task
requires guarding against).

**So: real new machinery IS needed, precisely two small pieces**, both in
`domains/inference_generation.py`:

1. A new gap-detect shape, `detect_conjunctive_gaps` — NOT one-candidate-
   per-attr like `detect_implication_gaps` (that discipline is proven to
   under-offer here: a conjunctive schema needs to see ALL of an entity's
   currently-true facts AT ONCE, not one at a time) — instead ONE joint
   candidate per entity: `[["holds", k] for every currently-true, admissible
   attr]`, reusing the SAME `_NON_CANDIDATE_KEYS`/`_NON_CANDIDATE_PREFIXES`
   exclusion `detect_implication_gaps`/`detect_goal_gaps` already use.
2. A new POST-decode gate in `resolve_conjunctive_gap` — read the WINNING
   schema's OWN `signature` length (a plain attribute read off the node
   `decode_gap` already named as winner — the SAME idiom `_coherence_of`/
   `_supplies_of` already use to read a POST-decode attribute off the
   winner, never a pre-decode filter) and require `covered_count ==
   len(schema_signature)` before minting — i.e. FULL antecedent coverage,
   no partial credit. This is a "gate that decides WHETHER a pass runs,
   never WHICH schema wins" — the SAME category of plain-attribute gate
   `coherence == "elaborative" and not deep` already is throughout this
   file (module docstring §4) — not a new decision mechanism, a new
   CONSISTENCY CHECK on a decision ShapeDecode already made.

Scoped to schemas with `len(signature) >= 2` only (a single-antecedent
schema is MP's job, left to the existing unchanged pipeline) to keep the two
mechanisms cleanly separated for testing/reporting, even though nothing
would technically break if a 1-antecedent schema won here too (idempotent
mint would just no-op).

**Predicted, before building:** GO on the STRUCTURAL machinery
(representation + detect + resolve + full-coverage gate), demonstrated with
ONE HAND-SEEDED conjunctive schema (`seeds/inference_logical.json`, matching
this seed file's own existing style of hand-authoring its one example
implication) — a genuine partial-match null (only P stated) and a genuine
joint-fact mint (P and Q both stated) both proven live.

**Predicted residual, before building — prose-parsing of conjunctive
antecedents:** investigated directly: `reading_collapse.decompose_sentence`
splits "if X is a mammal and X is aquatic, X is a dolphin" correctly at the
COMMA (`clauses[0] = ['x','is','a','mammal','x','is','aquatic']`,
`clauses[1] = ['x','is','a','dolphin']`) but its own `_segment_into_clauses`
DROPS the coordinator "and" during tokenisation (glue-word filtering) — so
there is no marker left in `decompose_sentence`'s OWN output to split the
antecedent clause on. Grounding `clauses[0]` as one fragment via
`read_clause` yields exactly ONE predication (`is_a(x, mammal)`) — "aquatic"
is silently dropped, not coordinated. Splitting the antecedent on the
coordinator would therefore require working on the RAW STATEMENT STRING
(recovering the antecedent substring before `decompose_sentence` ever
tokenises it, splitting IT on literal `" and "`, then grounding each half
independently) — a real, plausible, small adapter, but one that reads OUTSIDE
`decompose_sentence`'s own clause-boundary mechanism rather than reusing it,
which is exactly the shape of thing `DEDUCTION_GENERAL_READER_CORRECTION_
RESULTS.md` (the CORRECTION rung landed THIS SAME DAY, immediately prior to
this one) identified and fixed as "a second grammar duplicating a capability
the general reader doesn't actually have. **Predicted NOT to be attempted in
this rung** — building it would risk reintroducing the exact anti-pattern
the correction rung just corrected, for a piece this task explicitly framed
as optional generality ("investigate... or whether it needs real new
machinery. Report honestly which" — not "build the parser too"). Will be
named and sized precisely in the RESULTS doc as a follow-on, not silently
absorbed or force-fitted.

---

## 4. Quantifiers — investigated, predicted STRETCH-GOAL-NOT-ATTEMPTED, with
a precise finding either way

Investigated directly (grep + read, not assumed):

- `seeds/reading_constructions.json`'s own `ClosedClass{role:"determiner"}`
  list includes `every`/`some`/`any`/`each` alongside `a`/`the`/`this` — i.e.
  **quantifier words are currently classified as plain determiners, with NO
  distinct scope/force representation.** "every bird can fly" and "a bird
  can fly" ground IDENTICALLY today (the determiner is stripped during
  argument-structure parsing either way) — confirmed by the `_DETERMINERS`
  frozenset in `reading_collapse.py:2277-2278` including both.
- The Term algebra DOES already have real bound-variable machinery: `Exists
  { source, var_name, predicate }` (`runners/dsl/src/shape.rs:539`,
  `jsonio.rs:587/1416`, `reflect.rs:284/1119`) — a genuine existential
  quantifier over a graph-resident COLLECTION, already used elsewhere in the
  substrate (e.g. `fallback_trace.rs`'s `Not(Exists(...))` absence-guard
  idiom cited throughout CLAUDE.md's own rule-engine discussion). And the
  rule engine's own match phase produces `Binding = FxHashMap<Sym, NodeID>`
  (`rewrite.rs:904`) — variable-to-node binding over every node satisfying a
  pattern, which is structurally universal instantiation already: a Rule
  `[x, is_entity, x]` with a `where` clause fires for EVERY `x` satisfying
  it, i.e. "for all x, P(x) ⇒ Q(x)" restricted to the graph's current domain
  of discourse.
- In fact the DEDUCTION MODULE ITSELF, as it stands after §2/§3 above, is
  ALREADY implicitly universally quantified in exactly this sense:
  `detect_implication_gaps`/`detect_conjunctive_gaps` iterate `sub.nodes(
  "SmEntity")` — every resident entity gets the SAME implication applied
  when it qualifies. What is missing is not the INSTANTIATION mechanism (it
  already exists, twice over) but an EXPLICIT SYNTACTIC representation a
  human could state as a stand-alone premise ("all birds can fly", "some
  bird cannot fly") distinct from asserting N separate per-entity facts, plus
  nested-scope/sorted-domain handling for anything past one flat quantifier.

**Predicted finding (to confirm honestly in the RESULTS doc, not force a
build):** quantifiers are tractable ONLY in the weak sense already present
(iteration over resident entities = implicit ∀); a genuinely NEW capability
— parsing an EXPLICIT quantifier-scoped premise from prose into a
bound-variable graph representation, plus an existential WITNESS SEARCH
distinct from "scan all resident entities" — is real, additional work on
BOTH the reading-pipeline side (no quantifier-scope construction exists
today, confirmed above) and the deduction side (no existential-witness
resolver exists), matching the task's own prediction that this needs "real
variable binding over a domain of objects, a different kind of complexity."
Sized, not built, per the task's explicit stretch-goal framing.

---

## 5. Build order and files touched (predicted)

1. `domains/propositional_deduction.py` — ADD `_negate_signature_attr`/
   `_negate_supplies_attr` (or one combined helper) + `derive_contrapositive`
   + `ensure_contrapositives`; call the batch form at the end of
   `mint_logical_schema` (only for the freshly-minted node, guarded
   idempotent) — no change to `parse_conditional`/existing exports' outward
   behaviour.
2. `domains/inference_generation.py` — ONE new call at the end of
   `ensure_logical_seeds` (`pd.ensure_contrapositives(agent)`, mirroring the
   existing `_ensure_warning_lexicon`/`_ensure_trust_lexicon` idiom) for MT;
   `detect_conjunctive_gaps`/`resolve_conjunctive_gap` (new functions) +
   ONE new additive key in `read_and_infer`'s return dict
   (`"conjunctive": [...]`) for conjunction. `detect_implication_gaps`/
   `resolve_implication_gap`/`decode_gap`/every existing gap kind: UNCHANGED
   (git-diff-guarded in the new test file, same discipline as the existing
   `test_ground_reductions_and_comprehend_theorem_untouched` guard).
3. `seeds/inference_logical.json` — version bump; ADD one hand-seeded
   conjunctive schema (`if X is wet and X is cold, X is frozen` or similar);
   contrapositive companions for `logical_bird_can_fly` are MECHANICALLY
   DERIVED at load time (via `ensure_contrapositives`), not hand-authored —
   confirming the "one implication, both directions, one seed entry" design
   the task asked to investigate.
4. `tests/test_deduction_extension.py` — new file: MT live demo + null;
   conjunction live demo + partial-match null; source/scope-guard audits
   mirroring the existing `test_deduction_generalization.py` discipline
   (no regex; decode is the decision; existing files/functions untouched).
5. Regression: `tests/test_deduction_generalization.py`,
   `tests/test_reading_collapse.py` re-run byte-unchanged; full relevant
   bundle re-run.

**GO/NO-GO called per piece, honestly, in the RESULTS doc** — this prereg
predicts GO on MT (data-only extension, zero pipeline code change), GO on
conjunction's STRUCTURAL machinery (small, precisely-scoped new code, both
pieces already justified above by a measured gap in `ShapeDecode`'s own
behaviour), NO-GO-BY-DESIGN on conjunctive prose-parsing (named follow-on,
not attempted, to avoid reintroducing today's already-corrected
second-grammar anti-pattern), and STRETCH-GOAL-NOT-ATTEMPTED on quantifiers
(precisely sized, real existing machinery identified, real gap identified,
not built).
