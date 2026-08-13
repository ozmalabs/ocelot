# QUANTIFIED DEDUCTION — universal + existential instantiation — PREREG

**Base:** `main` @ `76b8aea` (re-checked fresh — `deduction-extension` and other
sibling rungs are already merged; this is the current tip). **Worktree:**
`/home/matt/ozmadev/ocelot-worktrees/quantified-deduction`. **Branch:**
`quantified-deduction`.

This rung picks up the STRETCH GOAL that `DEDUCTION_EXTENSION_RESULTS.md`
Sec4 investigated, precisely sized, and explicitly did NOT build: quantified
premises. Read in full before this doc (all four already read in full this
session): `docs/research/engine_substrate/DEDUCTION_EXTENSION_RESULTS.md`,
`domains/propositional_deduction.py`, `domains/inference_generation.py`,
`seeds/inference_logical.json`.

The prior rung's finding, quoted because everything below either confirms or
extends it: *"what is missing is not the instantiation mechanism (it exists,
twice over — `Exists` and rule-match `Binding`) but (a) an EXPLICIT SYNTACTIC
representation a human could state as a stand-alone premise... distinct from
asserting N separate per-entity facts; and (b) an EXISTENTIAL WITNESS SEARCH
distinct from 'scan all resident entities'... Both are real, additional
work."* This rung builds (a) and (b), reusing the SAME engine-level primitives
the prior rung named (`Exists`, rule-match `Binding` — realised on the Python
side, throughout this whole file family, as a plain `for n in
sub.nodes("SmEntity")` scan; see §4) rather than adding any new Rust Term.

Everything below was investigated by RUNNING the real engine in this worktree
before writing this prereg (not assumed) — findings and file:line citations
are recorded here, and the build plan follows from them.

---

## 1. Universal instantiation — what the reading pipeline actually does with
"All X are Y" today, measured live

**Live, fresh agent, `pd.parse_conditional` (unmodified) fed whole
quantified sentences directly:**

```
'All men are mortal'      -> 'multi_clause': False,
                              read_clause predications: [['is_a','all_men','mortal']]
'Every bird can fly'      -> predications: [['bird','every','can_fly']]   (garbled)
'Some birds are penguins' -> predications: [['is_a','some_birds','penguins']]
'A man is mortal'         -> predications: [['is_a','man','mortal']]      (correct — "a" IS stripped)
```

**Confirmed: the quantifier word is NOT stripped from the subject** by the
whole-clause `read_clause` path `parse_conditional`'s `bare_universal` branch
calls (`domains/propositional_deduction.py:215`) — "all"/"some" fuse onto the
head noun as one compound token (`all_men`, `some_birds`), and "every"
produces an outright garbled predication shape. This is despite `_DETERMINERS`
(`domains/reading_collapse.py:2277-2278`, populated from
`seeds/reading_constructions.json`'s `ClosedClass{role:"determiner"}` at
`ensure_codebook` time, `reading_collapse.py:129`) already listing
`any`/`each`/`every`/`some` alongside `a`/`an`/`the` — **so the classification
the prior rung found ("quantifier words load into the SAME determiner role as
plain articles") does not, on its own, make the WHOLE-CLAUSE subject
extraction path actually strip them**, confirmed live, not assumed.

**A second, separate finding, checked directly because the first one looked
suspicious:** the ROLE-SPAN cleaning primitives `_arg_head`
(`reading_collapse.py:2392`) / `_clean_head` (`reading_collapse.py:1816`) DO
correctly strip every one of these words when called on an isolated span:

```
_arg_head(ag, "a man")     -> "man"
_arg_head(ag, "some man")  -> "man"
_arg_head(ag, "some birds")-> "birds"
_arg_head(ag, "all men")   -> "men"
_arg_head(ag, "every bird")-> "bird"
```

So the determiner-stripping MACHINERY exists and works — the whole-sentence
`bare_universal` grounding path in `parse_conditional` simply never routes
the SUBJECT through it for a bare "Det N₁ V N₂" sentence with no clause
split (it does for the multi-item enumerated-list ground_template
elsewhere in `reading_collapse.py`, an unrelated code path). This is a real,
narrow inconsistency in the general reader (a sibling of the
`_marker_lexicon`/`ClosedClass` inconsistency the prior rung already
reported and declined to fix) — **not chased or fixed here**: changing
`read_clause`'s own subject-extraction for the shared `bare_universal`/
`definitional` path is `reading_collapse.py` surgery with its own
byte-parity-tested battery (`tests/test_reading_collapse.py`), exactly the
class of change `DEDUCTION_GENERAL_READER_CORRECTION_RESULTS.md` already
flagged as out of scope for this whole module family.

**The plan (which does NOT touch `reading_collapse.py` or `parse_conditional`
at all): strip the quantifier word from the RAW STATEMENT STRING, before
`decompose_sentence`/`read_clause` ever see it, then hand the REMAINDER to
`parse_conditional` UNCHANGED.** `"All philosophers are mortal"` →
strip `"All "` → `"philosophers are mortal"` → `parse_conditional` (reused,
byte-unchanged) already grounds this correctly at the level it always has:

```
pd.parse_conditional(ag, "philosophers are mortal")
 -> {'antecedent_attr': 'philosophers', 'consequent_relation': 'is',
     'consequent_attr': 'mortal', 'form': 'bare_universal', ...}
```

**A second, genuinely orthogonal residual, found and precisely sized while
confirming this:** the general reader has **no noun-plural lemmatiser** —
`'philosophers'`/`'birds'` survive as literal plural strings, so a fact
minted as `is_a(socrates, philosopher)` (singular, the natural way to state
an instance) would never match an antecedent stored as `'philosophers'`
(plural). Confirmed the SAME held reference every other lemma-normalisation
in this file family already depends on (`situation_model_reader._lemma`,
`reading_collapse._clean_head`, both WordNet `morphy`) fixes this too, on
the **noun** POS tag instead of the verb one already used elsewhere:

```
wn.morphy('philosophers', 'n') -> 'philosopher'
wn.morphy('penguins', 'n')     -> 'penguin'
wn.morphy('mortal', 'n')       -> 'mortal'   (already singular, no-op)
wn.morphy('can_fly', 'n')      -> None       (not a noun form, safe no-op fallback)
wn.morphy('men', 'n')          -> 'men'      (IRREGULAR PLURAL — morphy does not
                                                fix this; a KNOWN WordNet-morphy
                                                limitation, not something this
                                                rung's mechanism can paper over)
```

**Plan:** a small, mechanical `_singular_attr(attr)` helper in
`domains/propositional_deduction.py` — `wn.morphy(attr, "n")`, fallback to
`attr` unchanged on `None`/exception — applied to `antecedent_attr` always,
and to `consequent_attr` only when `consequent_relation == "is"` (a capability
consequent, `can_fly`, is already the bare verb form `_relation_and_attr`
produces, never plural-inflected — singularising it would be a no-op by the
morphy safety check above, but the scope is stated precisely rather than
applied blindly). This is the SAME class of mechanical morphological
normalisation `_lemma` already documents for verbs — applying the identical
held reference to a different POS tag is not a new decision.

**Honest, named limitation, before building:** irregular plurals (`men` →
`man`, `mice` → `mouse` via `noun.exc`, NOT reached by plain `wn.morphy`
lookups the way regular `-s` plurals are — confirmed above, `men` round-trips
to `men`) are NOT fixed by this mechanism. The live demo below is therefore
built on a REGULAR plural (`philosophers`), not the textbook `"All men are
mortal"` phrasing literally — same STYLE, same structure, WordNet-tractable
vocabulary. This is reported, not silently avoided.

---

## 2. The quantifier-word recognition itself — a thin I/O-boundary classifier,
CLAUDE.md's own named carve-out

No construction in `seeds/reading_constructions.json` names a distinct
quantifier-SCOPE relation (confirmed by the prior rung, re-confirmed by grep
here) — there is no Rust primitive and no reading-pipeline construction that
already converts "the first word of this statement is a universal/existential
quantifier" into a graph token. Recognising the leading quantifier word is
therefore exactly CLAUDE.md's own permitted carve-out: *"A thin I/O-boundary
classifier is permitted... when it is genuinely converting an opaque external
form into the smallest graph token, AND there's no Rust primitive that can do
the job."* Plan: a graph-resident `QuantifierLexicon` node (mirroring the
EXISTING `WarningLexicon`/`TrustLexicon` idiom in
`domains/inference_generation.py`'s `_warning_lexicon`/`_trust_lexicon` —
`{"universal": ["all","every","each"], "existential": ["some"]}`), read via a
new `_quantifier_lexicon(agent)` helper following that exact pattern, and a
plain `str.split(None, 1)` + lowercase + membership check to recognise and
strip the LEADING token — no regex, matching this whole file family's
existing discipline (`test_source_audit_no_regex_and_decode_is_the_decision`
already guards this for the sibling files).

**Scoping decision, to avoid a collision the conjunction rung's own history
warns about (§3):** `"a"/"an"` stay OWNED by the EXISTING `bare_universal`
generic reading (`"a bird can fly"` already grounds and fires today,
functionally universal per the prior rung's own finding) — the NEW
`QuantifierLexicon` only recognises `"all"/"every"/"each"` (universal) and
`"some"` (existential), never `"a"/"an"`, so there is no ambiguity about which
path a bare indefinite-article sentence takes (unchanged, byte-identical).

---

## 3. Universal instantiation — PLAN: new PARSE, reused MINT/DETECT/RESOLVE
(mirrors the MT precedent exactly)

Once the quantifier is stripped and the remainder is singularised, a
universal premise is STRUCTURALLY IDENTICAL to any other single-antecedent
`knowledge_logical` schema `mint_logical_schema` already installs (same
`signature`/`supplies` field shape, same node type, same codebook pool) — so
`detect_implication_gaps`/`resolve_implication_gap`/`decode_gap`
(`domains/inference_generation.py:943/966/1171`, ALL THREE UNCHANGED) already
run universal instantiation with **zero new gap-detection code**, exactly the
same finding the MT rung made for the contrapositive extension (*"the task's
own hypothesized 'second gap-detection pattern' turns out, on measurement,
not to be needed at all"* — `DEDUCTION_EXTENSION_RESULTS.md` §0). This is a
PREDICTION, to be confirmed live in the RESULTS doc exactly like that
precedent was.

**Plan:** `parse_universal(agent, statement)` (strip quantifier, must be
`"universal"`; delegate the remainder to `parse_conditional`, UNCHANGED;
singularise per §1) + `mint_universal_schema(agent, statement, *, name=None)`
(install the `ShapeSignature{kind:"knowledge_logical", quantifier:"universal",
...}` node, mirroring `mint_logical_schema`'s own attrs construction — a
small, self-contained sibling function, NOT a refactor of
`mint_logical_schema` itself, to keep that existing, tested function's body
byte-for-byte unchanged — then call `derive_contrapositive` at the end,
exactly like `mint_logical_schema` already does).

**Predicted, before building:** because the minted schema is
`kind:"knowledge_logical"` with a length-1 `signature`, `ensure_
contrapositives`'s batch scan (`propositional_deduction.py:398`) picks it up
FOR FREE — a universally-quantified premise should automatically get a
mechanically-derived contrapositive too, composing with the MT rung with zero
new code. To be confirmed live, not assumed.

**Live demo planned (regular-plural, WordNet-tractable, per §1's honest
limitation):** `mint_universal_schema(ag, "All philosophers are mortal")` +
`smr.ingest_predication(ag, ["is_a", "socrates", "philosopher"])` +
`detect_implication_gaps`/`resolve_implication_gap` (UNCHANGED) → `is_a
(socrates, mortal)`. A REAL syllogism (Socrates, philosopher, mortal — real
WordNet-grounded Concepts, not toy strings), PROSE-MINTED end to end with NO
hand-seeded schema fallback needed — stronger than the MT/conjunction demos,
which both needed at least one hand-seeded schema because their own examples
fell outside `parse_conditional`'s antecedent-shape grammar.

---

## 4. Existential instantiation — PLAN: real, new, small witness-search
machinery (mirrors the conjunction precedent, not the MT one)

**Why this is NOT the same shape as universal instantiation, precisely, per
the prior rung's own framing:** a universal premise licenses "apply the
consequent to EVERY resident entity that satisfies the antecedent" — exactly
what `detect_implication_gaps`'s breadth-first `for n in sub.nodes(
"SmEntity")` scan already does (this IS the graph-native realisation of the
rule-match `Binding` the prior rung cited, `rewrite.rs:904` — a Python
for-loop reproducing the SAME "every node satisfying a pattern" semantics the
Rust match phase already has, the SAME idiom every `detect_*` function in
`inference_generation.py` already uses, not a new engine primitive). An
existential premise ("some bird is a penguin") licenses NO SUCH THING — it
must not fire on every resident bird, only find (or, failing that,
construct) ONE witness. This is the prior rung's own "distinct from scan all
resident entities" phrase, given a precise operational meaning: same
underlying scan primitive (`for n in sub.nodes("SmEntity")` — reusing the
`Exists`-shaped existential-over-a-collection semantics the Rust `Exists`
Term already has, `runners/dsl/src/shape.rs:539`, `jsonio.rs:587/1416`,
without adding a Rust call for it, since every other `detect_*` function in
this file already reproduces `Exists`'s semantics as a Python loop rather
than an FFI call — the SAME choice, not a new one), but STOPPED at the first
match and, if none is found, followed by a MINT (introduce a fresh witness
constant — classical existential instantiation) rather than continuing the
scan or applying to everything.

**Ordering rule adopted, citing CLAUDE.md's own sd-loop precedent directly:**
search (recognise) BEFORE mint — "exact recognize... only after BOTH rungs
fail" (`CLAUDE.md`, "SHAPES, NOT NUMBERS"). A witness that already exists in
the graph is used; a fresh one is minted ONLY when the search comes back
empty. This is the SAME Occam ordering the sd loop's own ladder already
enforces elsewhere in the substrate, applied here without needing the sd loop
itself (no `ShapeDecode` call — see the cross-contamination note below for
why).

**Cross-contamination, predicted from the conjunction rung's own precedent,
to be confirmed live, not assumed:** the existential schema's `signature`
must use a relation label DISTINCT from `"holds"` (MP) and `"holds_all"`
(conjunction) — `"holds_some"` — for exactly the reason
`DEDUCTION_EXTENSION_RESULTS.md` §3.3 found and fixed for conjunction: any
shared label risks `detect_implication_gaps`'s own `holds`-keyed goal (or
`detect_conjunctive_gaps`'s `holds_all`-keyed one) becoming a candidate
decoder for a schema it was never meant to see. Plan: predicted GO on
`"holds_some"` cleanly separating the pools, verified live with the SAME
no-cross-contamination test shape `test_conjunction_no_cross_contamination_
with_mp_path` already establishes.

**Why NOT `decode_gap`/`ShapeDecode` for this schema, an honest architectural
choice, not an oversight:** `decode_gap` exists to pick WHICH of several
competing knowledge schemas covers a gap (a genuine collapse/ambiguity
problem). An existential premise, once parsed, is already a SINGLE, fully
specified `(antecedent_attr, consequent_attr)` pair — there is no competing
schema to choose among, so routing it through `ShapeDecode` would be
overhead with no discriminative work for the collapse to do. The schema node
still reuses the SAME `ShapeSignature` type + `signature`/`supplies` JSON
field shape as every other `knowledge_*` kind (consistency, not a new node
type — SHAPE_TYPE_VOCABULARY_SPIKE.md's finding, again), but is consumed by a
direct node-scan (`detect_existential_gaps`), not a decode.

**Plan, two new pieces in `domains/inference_generation.py`, mirroring the
conjunction rung's own "detect offers, resolve gates+acts" shape:**

1. `detect_existential_gaps(agent, unit=None)` — every resident
   `ShapeSignature{kind:"knowledge_existential"}` schema not yet marked
   `witnessed` — a gap about the SCHEMA (not an entity), returning
   `{schema, node, antecedent_attr, consequent_attr}`.
2. `resolve_existential_gap(agent, gap, *, t=0, unit=None)` — SEARCH: the
   first resident, non-nested `SmEntity` with `antecedent_attr == 1`
   (mirrors `detect_implication_gaps`'s own admissible-fact discipline). If
   found: mint the consequent fact on THAT entity via `situation_model_
   reader.ingest_predication` (UNCHANGED, reused, the identical call every
   other `resolve_*` in this file already makes) — `witness_kind: "found"`.
   If not found: mint a FRESH witness `SmEntity` (a name derived from the
   antecedent, collision-checked against resident names) via TWO
   `ingest_predication` calls (antecedent then consequent), tagged
   `existential_witness: 1` for honest provenance (mirrors the
   `blocked_gap`/`imperative_derived` provenance-marker convention already in
   this file) — `witness_kind: "minted"`. Either branch marks the schema
   `witnessed: 1` (idempotent guard, mirrors `contrapositive_of`).

**Wiring:** ONE new additive key in `read_and_infer`'s return dict
(`"existential": [...]`), mirroring exactly how `"conjunctive"` was added —
`detect_implication_gaps`/`resolve_implication_gap`/`decode_gap`/every
existing key: untouched.

**Live demos planned, both required by the task:**
- **Search-found:** ingest `"Tux is a bird"` (context), THEN
  `mint_existential_premise(ag, "Some bird is a penguin")` → resolve →
  Tux (the resident bird) gets `penguin=1` — NO new entity minted.
- **Search-mint:** a fresh agent with NO resident bird entities,
  `mint_existential_premise(ag, "Some bird is a penguin")` → resolve → a
  FRESH witness entity is minted carrying BOTH `bird=1` AND `penguin=1`,
  tagged `existential_witness=1`.

---

## 5. Out of scope, restated from the task, honoured by construction

- **Entity resolution** (SmEntity/Concept identity, coreference) — untouched;
  every mint here reuses `situation_model_reader._entity`/`ingest_predication`
  exactly as-is.
- **CAN bridges** — not touched, no relation to this rung's mechanism.
- **New Rust Terms** — none planned. Every "search"/"instantiate" operation
  reuses the SAME Python-side `for n in sub.nodes("SmEntity")` idiom already
  used by all six existing `detect_*` functions in `inference_generation.py`,
  which is itself the graph-native realisation of `Exists`/rule-match
  `Binding` the prior rung already identified in the Term algebra — reused,
  not reimplemented, no FFI call added.
- **Nested/multi-quantifier sentences** ("every bird has some friend that
  flies") — not attempted; only single, top-level, flat quantified premises
  are in scope, matching the prior rung's own explicit sizing of what a
  "genuinely new capability" would require and the task's own framing
  (single explicit premise + one witness/instantiation step).
- **Negative existentials** ("some bird cannot fly") — not attempted in this
  rung to avoid combining the quantifier-strip mechanism with the `not_`
  negation-prefix convention in one build; named as a natural, small
  follow-on (the two mechanisms are already independently proven — MT §2 of
  the prior rung, quantifier-strip §1 here — composing them is plausible but
  untested).

---

## 6. Build order and files touched (predicted)

1. `domains/propositional_deduction.py` — ADD `_singular_attr`,
   `_quantifier_lexicon`, `_split_leading_quantifier`, `parse_universal`,
   `mint_universal_schema`, `parse_existential`, `mint_existential_premise`.
   `parse_conditional`/`mint_logical_schema`/`derive_contrapositive`/
   `ensure_contrapositives`: UNCHANGED (called, never edited).
2. `domains/inference_generation.py` — ADD `detect_existential_gaps`,
   `resolve_existential_gap`; ONE new additive key in `read_and_infer`.
   `detect_implication_gaps`/`resolve_implication_gap`/`decode_gap`/
   `detect_conjunctive_gaps`/`resolve_conjunctive_gap`: UNCHANGED
   (git-diff-guarded in the new test file, matching the existing discipline).
3. `seeds/inference_logical.json` — version bump; ADD one `QuantifierLexicon`
   node. NO new hand-seeded example schema predicted to be needed (both demos
   are prose-minted live, unlike MT/conjunction which each needed one
   hand-seeded fallback) — to be confirmed, not assumed, in the RESULTS doc.
4. `tests/test_quantified_deduction.py` — new file: universal live syllogism
   demo, contrapositive-composes-for-free check, existential search-found
   demo, existential search-mint demo, cross-contamination guard
   (`holds_some` vs `holds`/`holds_all`), idempotency, source/scope-guard
   audits mirroring `test_deduction_extension.py`'s own discipline.
5. Regression: `tests/test_deduction_generalization.py`,
   `tests/test_deduction_extension.py` re-run byte-unchanged; full relevant
   bundle re-run.

**GO/NO-GO called per piece, honestly, in the RESULTS doc** — this prereg
predicts GO on universal instantiation (new parse + singularisation, zero
pipeline code change, reuses MT's own "second gap-detection code turns out
unnecessary" finding), GO on existential instantiation's structural machinery
(small, precisely-scoped new detect/resolve pair, justified above by the
"search-then-mint, not scan-all" distinction measured against `Exists`'s own
semantics), NO-GO-BY-DESIGN on nested/multi-quantifier premises and negative
existentials (named follow-ons, not attempted), and an honestly bounded GO on
the irregular-plural limitation (named, not fixed, demo built around it).
