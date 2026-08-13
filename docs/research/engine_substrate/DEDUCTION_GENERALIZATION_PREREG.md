# GENERAL PROPOSITIONAL DEDUCTION THROUGH THE INFERENCE-GENERATION COLLAPSE — PREREG

**Status: PREREG. Design only below §7; nothing has been built yet.** House style,
matching `CROSS_DOMAIN_SHAPE_SPIKE.md` and `SHAPE_TYPE_VOCABULARY_SPIKE.md`: a
first-person research journal that makes the design decision legible and
falsifiable *before* committing code, written in an isolated worktree.

**Charter, as handed down, paraphrased with the load-bearing correction kept
verbatim.** An earlier investigation this session concluded the agent has NO
executing deduction facility — only inert prose (`seeds/logic_foundation.json` /
`seeds/logic_propositional_predicate.json`, 10 rules, `match: null`). The creator
corrected this directly: **"the deduction does exist but likely needs expansion."**
A follow-up investigation (by the orchestrating session) found the correction is
right and located it: `domains/comprehend_theorem.py` +
`domains/ground_reductions.py` is a real, executing, propositional
modus-ponens engine — narrowly scoped to group-theory invariant theorems. The
task handed to this rung: connect that PROVEN deduction machinery to the
GENERAL, graph-native `domains/inference_generation.py` collapse pipeline
(gap-detect → `ShapeDecode` collapse against a knowledge codebook → mint →
re-run the fixpoint), so genuine propositional deduction becomes available for
ANY domain, sourced from held implication facts, not just group theory.

**Base:** `main` at `b124038` (`Merge seed-pick-structural-fallback (A3):
precomputed aggregate signature, GO with a found scope caveat`), verified with
`git log --oneline -1 main` before reading anything. `git worktree list` checked:
one detached baseline worktree (`d239b7c`, unrelated), one sibling worktree
`blob-edge-analogy-extension` at the same tip with a clean working tree (no
divergent changes, confirmed via `git status --short` and `git diff --stat main`
inside it — both empty). No collision.

**Confidence convention**, following the prior two spikes: claims verified by
reading source in this tree carry `file:line`. Claims I ran (not just read) are
marked **[RUN]** with the actual output pasted. Anything not independently
re-verified is `[unverified]`.

---

## 1. What I verified before designing anything

### 1.1 The "inert logic" claim, re-confirmed

**[RUN]**, both seed files, counting rules and their `match` field:

```
seeds/logic_foundation.json n_rules= 5
   modus_ponens match= None
   modus_tollens match= None
   valid_argument_preserves_truth match= None
   consistency_required_for_meaningful_inference match= None
   inductive_strength_depends_on_evidence match= None
seeds/logic_propositional_predicate.json n_rules= 5
   and_introduction_combines match= None
   and_elimination_decomposes match= None
   universal_instantiation_specializes match= None
   existential_generalization_abstracts match= None
   godel_limits_formal_systems match= None
```

Confirmed: 10 rules, all `match: null`, genuinely never executed by `run_rules`
(a rule with no `match` pattern cannot fire — there is nothing for the matcher
to bind against). This is prose knowledge *about* logic, for conversational
recitation. Out of scope per the task; not touched below.

### 1.2 The real, executing deduction engine

`domains/ground_reductions.py:299-348` (`ImplicationClause` / `GroundedReduction`):

```python
@dataclass
class ImplicationClause:
    antecedent: Callable[[dict], bool]
    antecedent_name: str
    value: Any
    chain: str

@dataclass
class GroundedReduction:
    ...
    def compute(self, obj: dict) -> Any:
        for cl in self.clauses:
            if cl.antecedent(obj):
                ...
                return cl.value
        return self.fallthrough
```

`compute` is real modus ponens: iterate clauses in order, the antecedent is a
held Python predicate composed over the object's held structure
(`ground_reductions.py:159-287`, e.g. `some_factor_finite_cyclic`), the FIRST
clause whose antecedent holds wins, its consequent is returned. Proven live —
`verify_grounded` (`:557-576`) runs every clause against `KNOWN_OBJECTS` /
`KNOWN_VALUES` and refuses a grounding that mismatches a known.

`domains/comprehend_theorem.py:1-773` PARSES the theorem PROSE
("a group with torsion has cohomological dimension infinite") into exactly this
`ImplicationClause` shape, via a seeded construction grammar
(`seeds/theorem_constructions.json`) — genuinely general within its domain: it
is demonstrated on paraphrases and held-out theorems it was not tuned for
(module docstring, `comprehend_theorem.py:48-59`), and it SELF-VERIFIES every
grounded clause against the same known-object bar before asserting it
(`comprehend_theorem.py:596-677`, `self_verify_clause`).

**The scope limit, confirmed by reading, not assumed:** every held predicate
`ground_modifier` can bind to (`_held_predicate`, `comprehend_theorem.py:105-111`)
resolves by name against `domains/ground_reductions` — i.e. against a FIXED,
hand-written table of ~8 functions that compose over ONE specific object shape:
`{"orders": [...]}` / `{"rank": n}`, the free-product-of-cyclics representation
(`ground_reductions.py:159-170`, `_factors`). There is no route from arbitrary
graph-resident facts (an `SmEntity`'s attrs, a `Concept`, a stated sentence) into
this antecedent evaluator. That is the wall this rung is asked to cross — not by
widening `ground_reductions` (explicitly out of scope, and it stays exactly
as-is per the task), but by building an INDEPENDENT, general path that reuses
its *semantics* (antecedent/consequent separation, ordered-clause resolution)
rather than its *implementation* (Python callables over a fixed object shape).

### 1.3 The general inference-generation pipeline, re-confirmed

`domains/inference_generation.py:1-72` (module docstring) states the operative
frame directly: gap-detect (mechanical graph read) → DECODE (the collapse —
`reflective_faculty.compose_design_for_goal`, the Rust `ShapeDecode` Term) →
MINT (the winning schema's own `supplies` attr names the fact; written via
`situation_model_reader.ingest_predication`, unchanged) → GATE
(`standard_of_coherence`). Two existing gap kinds (`detect_precondition_gaps`,
`:254-286`; `detect_bridging_gaps`, `:292-330`) plus goal-from-state
(`detect_goal_gaps`, `:345-369`), causal (`detect_causal_gaps`, `:777-798`) and
elaborative (`detect_elaborative_candidates`, `:880-885`) — five gap kinds, one
mechanism, all decoding against `seeds/inference_knowledge.json`'s
`ShapeSignature` codebook.

**[RUN]** `seeds/inference_knowledge.json`: exactly 8 `ShapeSignature` nodes
(`local_id` 3-10), `kind` values: `knowledge_enabling` (1), `knowledge_elaborative`
(1), `knowledge_partwhole` (1), `knowledge_goal` (3), `knowledge_causal` (2). Zero
`knowledge_logical`. Confirmed by direct read of the seed JSON — the gap this
rung closes is real and precisely as the task states it.

`decode_gap` (`inference_generation.py:898-909`) is the ONE decode entry point
every existing gap kind calls: build a goal relation-system, decode it via
`compose_design_for_goal`, read the winner via `rc._winner` (never re-picked in
Python — `reading_collapse.py:1233-1246`, "the construction the decode chose =
the plan part with the greatest `shape_fit`... read off ShapeDecode's own
ranking, never re-ranked here"). This is *already* the general mechanism the
task's directive names: "once you have a universal algorithm, you should use
it." My job is to feed it a sixth gap kind, not build a seventh pipeline.

### 1.4 The `Concept.definition` candidate, checked and rejected

The task asks me to check whether `Concept`'s existing `definition` Term-subgraph
(`SHAPE_TYPE_VOCABULARY_SPIKE.md` §3.1 row 7) is a plausible home for "P implies
Q" before inventing anything. I read that row and its cross-references closely:

> `Concept` | `name`, `category`, `definition` | scalars; `definition` is a
> `Term.*` subgraph | `name`, via an out-of-graph Python index | per-site Python
> find-or-create (today) | 10,775 nodes, **114 with any outgoing edge, 190
> Concept→Concept edges total**.

And §5.4 of the same document, read in full, states the negative directly and
gives the reason: *"`Concept` should not be made to conform, because §6 shows it
has no signature to declare — and manufacturing one for conformance's sake is
exactly the 'no-op wearing the costume of a fix' `ANALOGICAL_THINKING_
SHAPE_MATH_RESULTS.md` §3.1 warns about."* §6.1 (same doc) is the measurement
behind that verdict: 98.9% of the 10,775-node `Concept` population carries no
outgoing edge at all, and the rung that actually needed `Concept`-level
relational structure built a DERIVED signature elsewhere (`_concept_shape_vector`
in `analogical_thinking.py`) rather than editing `Concept` itself, because
"building relational alignment here would be a no-op wearing the costume of a
fix."

**Verdict: `Concept.definition` is REJECTED as the home for a held implication.**
Three independent reasons converge: (a) it is a free-text/Term-subgraph field
with no declared signature convention any decode operator reads today — using
it would mean inventing exactly the ad-hoc parsing this rung is supposed to
avoid; (b) the tree's own prior measurement (§5.4 above) already ruled out
making `Concept` conform to a shape-bearing interface, for a documented reason
that applies here without modification; (c) `Concept`'s identity/dedup
discipline is per-site Python find-or-create (no structural key), which is the
wrong discipline for a piece of decodable knowledge that should be findable by
the SAME `ShapeDecode` mechanism as the other 8 schemas — `ShapeSignature`
already has that discipline (name-keyed, read generically by `decode_gap`).

---

## 2. Design question 1 — what does a held implication look like as graph data?

### 2.1 The candidates

1. **A new node type**, e.g. `Implication{antecedent, consequent, chain}`,
   consumed by a NEW decode pool separate from `ShapeSignature`.
2. **`Concept.definition`** — rejected, §1.4.
3. **A new `ShapeSignature` `kind`** (`"knowledge_logical"`), reusing the
   EXISTING node type and EXISTING decode pool the other 8 schemas already
   share.

### 2.2 Why (3), decided by the tree's own corrected finding, not by taste

`SHAPE_TYPE_VOCABULARY_SPIKE.md` §3.4(a), the **in-place correction** dated
2026-08-12 (same day as this rung; I read the correction, not the retracted
original): *"`kind` does not partition a decode pool and never has... the only
two candidate filters `ShapeDecode` accepts — `codebook_scope` and `exclude` —
are both keyed on the part's **name**... So the **node type is the only
mechanism that partitions a pool**, and `kind` is a pass-through label... The
correct rule the tree already follows in its best-behaved corner... is **type =
pool, kind = label within a pool.**"*

The existing 8 `knowledge_*` schemas already demonstrate this rule working:
`knowledge_enabling`, `knowledge_elaborative`, `knowledge_partwhole`,
`knowledge_goal`, `knowledge_causal` are five different `kind` values on the
SAME `ShapeSignature` node type, decoded together by the SAME `decode_gap` scan
over `sub.nodes("ShapeSignature")` (`inference_generation.py:905`). A sixth
kind, `knowledge_logical`, is exactly this pattern one more time — not a new
node type, not a new pool, not a new decode call site. It also means **zero
new Rust** (per the task's constraint): `ShapeDecode`/`compose_design_for_goal`
already reads `ShapeSignature.signature`/`.supplies`/`.coherence` generically;
a new `kind` value is just new data flowing through the existing reader, the
same way `knowledge_goal` was added after `knowledge_enabling` without any
engine change.

### 2.3 What the new schema's fields hold, and how they mirror `ImplicationClause`

The existing 8 schemas already have the right SHAPE for this — `signature`
(what pattern the decode must see to consider this schema) and `supplies`
(what fact to mint when it wins) are, respectively, the antecedent and the
consequent of an implication that's already been living in this codebook
under a different name. `fragile_glassware`'s `signature` --
`[["needs","glass","fragile"],...]` -- and `supplies` --
`{"relation":"is_a","attr":"fragile"}` -- IS "glass ⇒ fragile" (a class
membership implies a property), just phrased for the *enabling-condition* gap
shape (§3 explains why that gap shape does not fit modus ponens directly).

For `knowledge_logical` the mapping to `ImplicationClause`'s fields is direct:

| `ImplicationClause` field | `knowledge_logical` `ShapeSignature` field |
|---|---|
| `antecedent` (a held Python predicate) | `signature`: `[["holds", <antecedent_attr>]]` — a held FACT PATTERN, decoded structurally (`Covers`) rather than executed as a callable |
| `antecedent_name` | the antecedent attr string itself, inline in `signature` |
| `value` (the consequent) | `supplies`: `{"relation": "is_a", "attr": <consequent_attr>}` — BYTE-IDENTICAL shape to the existing `knowledge_enabling` `supplies` |
| `chain` (inspectable provenance) | a new `chain` attr, same idiom, e.g. `"IF is_a(X,bird) THEN is_a(X,can_fly) [propositional, held]"` |

This is graph-resident (no `Callable`), decodable by the unmodified
`ShapeDecode` Term, and an ADDITION to the existing codebook file convention —
not a new mechanism.

**Named limitation, honestly, up front:** this represents a SINGLE-antecedent
implication (`P ⇒ Q` for one attribute `P`). `ground_reductions`'s clauses
compose MULTI-part antecedents (`some_factor_finite_cyclic`, itself a
disjunction/conjunction over a list of factors) — that generality is NOT
reproduced here. Scoped correctly per the task ("propositional modus-ponens-
shaped inference only... quantified logic... out of scope"); a conjunctive
antecedent (`P₁ ∧ P₂ ⇒ Q`) is a real, named residual (§6).

---

## 3. Design question 2 — how does gap-detection recognize a genuine logical gap?

### 3.1 Why `detect_precondition_gaps`'s shape does NOT transfer as-is

I read `detect_precondition_gaps` closely (`inference_generation.py:254-286`)
because the task asks me to mirror it "as closely as the logical case allows"
and to report honestly if it doesn't fit. It doesn't, and the reason is
structural, not incidental:

`detect_precondition_gaps` requires a rule with **≥ 2 conjuncts**
(`len(rule["conds"]) < 2` is explicitly excluded, `:280`) and reports only
entities **exactly one conjunct short** (`len(missing) == 1`, `:283-284`). Its
own docstring is explicit about why: *"A rule with only ONE conjunct... is
NEVER reported here: an unset single precondition on an entity that never
triggered the event at all is not 'one fact away from coherence'"* (`:262-267`).

Modus ponens for a single implication `P ⇒ Q` is a **one-conjunct** antecedent
by construction (the antecedent IS `P`, no partial-conjunct state exists — `P`
is either fully stated or not stated at all). Feeding a single-conjunct
implication through `detect_precondition_gaps`'s "one-away-from-N-conjuncts"
machinery would require inventing a fake second conjunct just to make the
"exactly one missing" test pass, which is not honest grounding — it is forcing
a different-shaped gap through a filter built for a different reason. The
`detect_precondition_gaps` shape answers *"is this entity partway toward
satisfying a multi-part precondition?"*; modus ponens answers *"has this
entity's antecedent ALREADY fully fired, with the consequent not yet drawn?"*
Those are different questions and conflating them would be the "shallow/fake
version" the task explicitly warns against.

### 3.2 The shape that DOES transfer: the breadth-offer pattern

Two of the FIVE existing gap kinds already use a different, and better-fitting,
shape: `detect_goal_gaps` (`:345-369`) and `detect_elaborative_candidates`
(`:880-885`) both OFFER every resident fact/entity as a raw candidate
(`at[k] == 1` for every non-excluded key) and let the DECODE discriminate which
ones the codebook actually covers — no gap-shape assumption about "how many
conjuncts are missing." `detect_goal_gaps`'s own docstring states the
discipline this rung needs verbatim: *"this scan never hardcodes which attr
NAME counts as a need-state (no `if attr == 'thirsty'`); the codebook... is
what actually recognises one, and an uncovered attr... decodes to no winner —
an honest null"* (`:350-355`).

This is EXACTLY the shape modus ponens needs: offer every stated fact
(`at[k]==1`) on every resident entity as a candidate antecedent; the decode (not
Python) decides whether any `knowledge_logical` schema's `signature` covers it;
a schema that wins names its consequent via `supplies`; mint only if the
consequent is not already held (idempotent, mirroring `resolve_elaborative_
candidate`'s own "already holds — idempotent, no re-mint" check, `:1032-1034`).

`detect_implication_gaps(agent, unit=None)` is therefore modeled on
`detect_goal_gaps`, not on `detect_precondition_gaps` — same breadth-offer
discipline, same exclusion set (`coref_` prefix, `goal`/`name` keys), different
candidate goal head (`"holds"` instead of `"needs_goal"`).

**Honest limitation:** because this is a breadth scan (every `attr==1` on every
entity is offered), an entity with N stated facts generates N candidates each
decode-cycle, of which the codebook covers however many it holds implications
for — this is the SAME cost/precision profile `detect_goal_gaps` already has in
production (its own docstring calls the discrimination "the codebook... is what
actually recognises one" — the breadth is intentional, not a shortcut).

---

## 4. Design question 3 — reusing `ground_reductions`'s proven semantics

The task asks specifically whether to reuse (a) the antecedent/consequent
SEPARATION and (b) the FIRST-clause-that-holds-wins ORDERING.

**(a) Separation — reused directly**, per §2.3's field mapping: `signature`
(antecedent pattern) and `supplies` (consequent fact) are evaluated as two
separate steps by the EXISTING `decode_gap` → mint pipeline, exactly as
`ImplicationClause.antecedent` and `.value` are evaluated as two separate steps
by `GroundedReduction.compute`. No new separation logic is written; the
existing pipeline already enforces the separation for all 8 current schemas.

**(b) Ordering — reused, but through a different, already-proven mechanism, not
re-implemented.** `GroundedReduction.compute`'s "first clause that holds wins"
loop (`ground_reductions.py:330-337`) is a bespoke Python `for` loop over an
ORDERED list, because `ImplicationClause`s are Python objects with no
independent notion of "how well does this antecedent match" — order is the only
tie-break available. The general pipeline already has a STRICTLY better
mechanism for the same job: `rc._winner` picks the covering schema with the
greatest `shape_fit` (`reading_collapse.py:1233-1246`) — a data-driven best-match
selection, not an author-supplied list order. Every existing gap kind
(`resolve_precondition_gap`, `resolve_goal_gap`, `resolve_causal_gap`, ...)
already relies on `rc._winner` to arbitrate when more than one schema could
apply; `knowledge_logical` gets this for free by being one more `kind` in the
same pool. **I am NOT porting `GroundedReduction`'s ordered-list-with-first-
match loop into the general pipeline** — that would be reimplementing a
mechanism the general pipeline already has a proven, more general analogue of,
which the task's own framing ("the whole point of expansion is reusing what's
proven, not rebuilding it") argues against once the better-fitting existing
mechanism is identified. If two `knowledge_logical` schemas ever genuinely tie
on `shape_fit` for the same gap, `rc._winner`'s existing tie-break (first
`>`, not `>=`, in plan order — `:1244`) governs, exactly as it already does for
every other schema kind; this rung does not add a second ordering mechanism on
top of it.

---

## 5. The mint path — reused unchanged

`resolve_implication_gap` mints the consequent via
`situation_model_reader.ingest_predication(agent, ["is_a", entity, consequent_
attr], ...)` — the IDENTICAL call `resolve_precondition_gap` already makes
(`inference_generation.py:969-970`). No new mint primitive. `ingest_predication`'s
own property-predication branch (`situation_model_reader.py:357-362`) sets the
attr and re-runs `run_rules`, so if the newly-derived fact itself completes
ANOTHER stalled rule (chained inference), the existing fixpoint machinery
already carries it forward with no new code — the same way `fragile` minted by
`resolve_precondition_gap` cascades to `broken`/`worthless` today.

---

## 6. What is explicitly NOT being built (named residuals, not silently dropped)

- **Conjunctive antecedents** (`P₁ ∧ P₂ ⇒ Q`). `ground_reductions`'s clauses can
  compose multi-part antecedents; `knowledge_logical` schemas here are
  single-antecedent only. A conjunctive case would need either (a) a
  `signature` with >1 `["holds", attr]` row treated as an AND (which
  `ShapeDecode`'s `Covers` semantics may or may not already give for free over
  a `List` container — untested, flagged rather than assumed) or (b) reusing
  `detect_precondition_gaps`'s multi-conjunct machinery after all, restricted
  to the all-conjuncts-already-true case (`missing == []` instead of `== 1`) —
  a real, buildable extension, not attempted this rung.
- **Quantified/universal instantiation** ("every bird can fly" as a general
  rule vs. "Tweety is a bird" as an instance) — explicitly out of scope per the
  task. This rung's implications are instance-level modus ponens only: a
  `knowledge_logical` schema names the antecedent/consequent ATTRIBUTES
  generically (any entity carrying `bird=1`), which already gets "universal"
  behavior across ENTITIES for free (it is not keyed to one entity's name, the
  same way `fragile_glassware` is not keyed to one glass) — but there is no
  representation here of nested quantifiers, variables binding across multiple
  implications, or existential consequents.
- **Negation / modus tollens.** The task scopes this to modus ponens; the inert
  `logic_foundation.json` already has a `modus_tollens` prose entry (untouched,
  out of scope) that would be the natural next rung if this one lands.
  Grounding it via this rung's `knowledge_logical` shape is a straightforward
  but unbuilt extension: `¬Q` stated + `P ⇒ Q` held ⇒ derive `¬P` — not
  attempted here.
- **The prose→implication mini-parser's generality.** §7 below builds a small
  construction-pattern parser for statements of the form "if X is a/an P, X
  can/is Q" — genuinely useful for the live demo (mints a schema from prose,
  not a hand-typed fact) but FAR narrower than `comprehend_theorem`'s grammar
  (which has ~8+ statement forms, biconditionals, symbolic values). I am
  building the smallest parser that lets the live demo mint from prose rather
  than a hand-authored JSON literal, matching the discipline `ground_reductions`
  itself uses (a finite, honestly-scoped codebook) rather than trying to
  reproduce `comprehend_theorem`'s full generality, which is explicitly out of
  scope to touch or to re-derive.

---

## 7. What will actually be built

1. **`domains/propositional_deduction.py`** (new, small): `parse_conditional
   (statement)` — a tiny construction-pattern parser (2-3 surface forms) that
   turns "if X is a bird, X can fly" / "a fish can swim" into
   `(antecedent_attr, consequent_relation, consequent_attr, chain)`, modeled
   on `comprehend_theorem`'s PARSE→GROUND→EMIT shape but not calling into it
   (independent, general-purpose, not group-theory-bound) — plus
   `mint_logical_schema(agent, statement)` which installs one
   `ShapeSignature{kind:"knowledge_logical"}` node (mechanical graph write,
   idempotent by `name`, mirroring the existing seed-install idiom).
   Unparseable prose is a named residual (returns `None`), never a hand-wired
   fallback.
2. **`seeds/inference_logical.json`** (new seed, `depends_on:
   ["inference_knowledge"]`) — a small, honestly-finite codebook of hand-authored
   `knowledge_logical` schemas (mirroring the other 8 schemas' own
   hand-authored-knowledge discipline, per `inference_knowledge.json`'s own
   description: *"The KNOWLEDGE is finite and seeded; the MECHANISM is
   general"*), loaded via a new idempotent `ensure_logical_seeds(agent)`
   depending on `inference_generation.ensure_seeds`. **`seeds/inference_
   knowledge.json` itself is not touched** — zero diff, trivially preserving
   the "8 existing schemas untouched" bar.
3. **`domains/inference_generation.py`** — additive only: `detect_implication_
   gaps`, `resolve_implication_gap` (both new top-level functions, following
   §3.2/§5), and one new pass appended inside `read_and_infer` writing
   `r["logical"]` (a new dict key; no existing key's shape changes).
4. **`tests/test_deduction_generalization.py`** (new) — the live demonstration:
   a fresh agent reads "Tweety is a bird." (plain text, general copular
   reading, unrelated to any hand-authored fact), a `knowledge_logical` schema
   for "a bird can fly" is minted BOTH by hand-authored seed data and via
   `mint_logical_schema` from prose (two independent paths to the same schema
   shape), `read_and_infer` derives `can_fly=1` on `tweety` with `can_fly`
   never stated in the text — genuine modus ponens through the general
   pipeline. Plus a discriminative null (an entity with no covering
   implication mints nothing) and a source/no-regression audit
   (`tests/test_inference_generation.py` re-run unchanged).
5. **`docs/research/engine_substrate/DEDUCTION_GENERALIZATION_RESULTS.md`** —
   the results doc with real output.

**Explicitly NOT touched:** `domains/comprehend_theorem.py`,
`domains/ground_reductions.py`, `seeds/logic_foundation.json`,
`seeds/logic_propositional_predicate.json`, `seeds/inference_knowledge.json`.
No Rust.

---

## 8. Pre-registered success/failure criteria

**GO** requires, measured not asserted: (a) `tests/test_inference_generation.py`
green, byte-identical pass/fail set to its pre-change baseline; (b) a new test
demonstrating `tweety.can_fly == 1` derived through `read_and_infer` with
`can_fly` never appearing in the input text, sourced from a `knowledge_logical`
schema decode (not a Python `if`); (c) the same derivation reachable when the
schema is minted from prose via `parse_conditional`/`mint_logical_schema`
rather than only from the hand-authored seed; (d) a discriminative null (no
covering schema ⇒ nothing minted); (e) a source audit confirming no new
`if entity ==` / `if attr ==` branch selects the mint (mirroring the existing
`test_source_audit_no_regex_and_decode_is_the_decision`).

**Partial-GO / NO-GO conditions to watch for and report honestly:** if
`ShapeDecode`'s `Covers` on a single-row `signature` does not discriminate
cleanly from the OTHER `knowledge_*` kinds sharing the pool (e.g. a `["holds",
"bird"]` goal accidentally covers a `knowledge_goal` schema) — would show up as
a wrong `_winner` in testing and must be reported, not silently worked around by
narrowing the goal predicate name ad hoc. If the prose parser cannot cleanly
separate from `comprehend_theorem`'s territory without duplicating logic, report
that precisely rather than force it.
