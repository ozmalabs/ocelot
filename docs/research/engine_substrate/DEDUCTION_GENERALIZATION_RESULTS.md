# GENERAL PROPOSITIONAL DEDUCTION THROUGH THE INFERENCE-GENERATION COLLAPSE — RESULTS

**Status: LANDED.** Design in `DEDUCTION_GENERALIZATION_PREREG.md` (read first —
this doc assumes it). Built in an isolated worktree, branch
`deduction-generalization`, off `main` at `b124038`. **GO.**

**Confidence convention**, matching the prereg: claims verified by reading
source carry `file:line`. Claims backed by an actual run are marked **[RUN]**
with real output. Nothing below is asserted without either.

---

## 0. One-line answer

**Genuine propositional modus ponens now runs through the general
`inference_generation.py` gap-detect → `ShapeDecode` collapse → mint →
re-run-fixpoint pipeline, sourced from a new `ShapeSignature{kind:
"knowledge_logical"}` codebook kind — reusing `ground_reductions.py`'s proven
antecedent/consequent SEPARATION as the design model (not its implementation)
and reusing the pipeline's own best-fit selection (`reading_collapse._winner`)
in place of `GroundedReduction.compute`'s bespoke ordered-clause loop.** Live
end-to-end: "Tweety is a bird." derives `can_fly=1` — never stated in the
text — both from a hand-seeded implication and from one parsed live off
ordinary conditional prose ("if X is a fish, X can swim"). The 8 existing
empirical schemas, `ground_reductions.py`, and `comprehend_theorem.py` are
byte-unchanged (git-diff-verified, §5). 34/34 relevant tests pass; a
pre-existing, environment-conditional worktree defect (missing `data/`,
unrelated to this rung) was found and is reported honestly in §6, not
silently worked around.

---

## 1. What was verified before building (full detail in the prereg; headline
here)

- **[RUN]** `seeds/logic_foundation.json` / `seeds/logic_propositional_
  predicate.json`: 10 rules, all `match: None` — confirmed genuinely inert,
  untouched, out of scope (prereg §1.1).
- **`domains/ground_reductions.py:299-348`** (`ImplicationClause`/
  `GroundedReduction.compute`) is real, executing, self-verified modus ponens
  — confirmed by reading, not assumed (prereg §1.2). Entirely bound to
  Python-callable antecedents over ONE object shape
  (`ground_reductions.py:159-170`, `_factors`) — the wall this rung crosses
  without rewriting it.
- **`seeds/inference_knowledge.json`**: exactly 8 `ShapeSignature` nodes, zero
  `knowledge_logical` — confirmed by direct read (prereg §1.3), matching the
  task's own claim precisely.
- **`Concept.definition` rejected as the implication's home**, on the tree's
  own prior measurement (`SHAPE_TYPE_VOCABULARY_SPIKE.md` §5.4/§6.1: 98.9% of
  `Concept` nodes carry no outgoing edge; manufacturing a signature for
  `Concept` "for conformance's sake" is the same "no-op wearing the costume of
  a fix" a prior rung already named and rejected) — prereg §1.4.

---

## 2. The graph representation chosen, and why

A held implication `P ⇒ Q` is a **`ShapeSignature` node, `kind:
"knowledge_logical"`** — the SAME node type and decode pool the existing 8
schemas already share, not a new node type. This follows directly from
`SHAPE_TYPE_VOCABULARY_SPIKE.md` §3.4(a)'s **in-place-corrected** finding (same
day as this rung): *"the node TYPE is the only mechanism that partitions a
[decode] pool, and `kind` is a pass-through label... type = pool, kind = label
within a pool."* A sixth `kind` value is an addition within the existing pool,
exactly as `knowledge_goal` was added after `knowledge_enabling` with no engine
change.

**Field mapping to `ImplicationClause` (the reused MODEL, not the reused
code):**

| `ImplicationClause` | `knowledge_logical` `ShapeSignature` |
|---|---|
| `antecedent` (Python callable) | `signature`: `[["holds", <antecedent_attr>]]` — a STRUCTURAL pattern, decoded via the unmodified `ShapeDecode`/`Covers`, never executed as code |
| `value` (the consequent) | `supplies`: `{"relation": "is_a", "attr": <consequent_attr>}` — byte-identical shape to `knowledge_enabling`'s `supplies` |
| `chain` (inspectable provenance) | a new `chain` attr, same idiom |

**[RUN]**, `seeds/inference_logical.json` (`local_id` 2, the ONE hand-seeded
schema, `logical_bird_can_fly`):

```json
{
  "name": "logical_bird_can_fly", "kind": "knowledge_logical",
  "coherence": "blocking",
  "signature": "[[\"holds\", \"bird\"]]",
  "supplies": "{\"relation\": \"is_a\", \"attr\": \"can_fly\"}",
  "statement": "if X is a bird, X can fly",
  "chain": "PARSE 'if X is a bird, X can fly' -> ANTECEDENT is_a(X,bird) => CONSEQUENT is_a(X,can_fly) [propositional, held, hand-seeded]"
}
```

New seed file `seeds/inference_logical.json`, `depends_on:
["inference_knowledge"]` — **`seeds/inference_knowledge.json` itself has ZERO
diff** (verified, §5). Loaded by a new `ensure_logical_seeds(agent)`
(`domains/inference_generation.py`), the same sentinel-`Concept`
idempotent-install idiom as every other `ensure_seeds` in this codebase.

**Named limitation, honestly:** single-antecedent-attribute implications only.
`ground_reductions`'s clauses compose multi-part antecedents
(`some_factor_finite_cyclic` is itself a structural disjunction over a factor
list); that generality is not reproduced. See §7 for the precise residual.

---

## 3. The gap-detection mechanism, and why it does NOT mirror
`detect_precondition_gaps`

`detect_precondition_gaps` (`inference_generation.py:254-286`) requires a rule
with **≥ 2 conjuncts** and reports only entities **exactly one conjunct
short**. Its own docstring states why: a single-conjunct rule is "not
inapplicable" reported here at all — there is no *partial* state for a
one-conjunct antecedent to be caught in. Modus ponens for `P ⇒ Q` is exactly a
one-conjunct antecedent by construction: `P` is either fully stated or not —
there is no "one fact away" state to detect. Forcing the single-antecedent
case through the two-conjunct machinery would mean fabricating a second,
fictitious conjunct purely to make the "exactly one missing" test pass — the
"shallow/fake version" the task explicitly warned against. **Reported
honestly, as asked: this shape genuinely does not transfer, for a structural
reason, not a laziness one.**

What DOES transfer is the **breadth-offer discipline** two of the five
existing gap kinds already use — `detect_goal_gaps` and `detect_elaborative_
candidates` offer every resident `attr==1` fact as a raw candidate and let the
DECODE (not the scan) discriminate coverage. `detect_goal_gaps`'s own
docstring states the exact discipline this rung needed: *"this scan never
hardcodes which attr NAME counts as a need-state... the codebook... is what
actually recognises one."* `detect_implication_gaps`
(`inference_generation.py`, new) is modeled on `detect_goal_gaps` — same
exclusion set (`_NON_CANDIDATE_KEYS`/`_NON_CANDIDATE_PREFIXES`, reused
unchanged), different candidate goal head (`"holds"` vs `"needs_goal"`).

---

## 4. Reuse of `ground_reductions.py`'s proven semantics

- **Antecedent/consequent SEPARATION — reused directly.** `signature` and
  `supplies` are evaluated as two independent steps by the existing
  `decode_gap`/mint pipeline, mirroring `ImplicationClause.antecedent`/`.value`
  exactly.
- **"First clause that holds wins" ordering — reused as a MODEL, deliberately
  NOT re-implemented as code.** `GroundedReduction.compute`'s ordered Python
  loop (`ground_reductions.py:330-337`) exists because `ImplicationClause`s
  have no independent match-quality signal — author order is the only
  tie-break available. The general pipeline already has a strictly more
  general mechanism for the identical job: `reading_collapse._winner`
  (`reading_collapse.py:1233-1246`) selects the covering schema with the
  greatest `shape_fit`, and every one of the 5 existing gap kinds already
  relies on it. `knowledge_logical` gets ordering/arbitration for free by
  joining the same pool — porting `GroundedReduction`'s bespoke loop into the
  general pipeline would have been reimplementing a mechanism the pipeline
  already has a proven, more general analogue of. This was a real design
  decision, not an oversight, and is recorded as such (prereg §4).
- **The mint primitive — reused unchanged, verbatim.**
  `resolve_implication_gap` calls `situation_model_reader.ingest_predication
  (agent, ["is_a", entity, consequent_attr], ...)` — the IDENTICAL call
  `resolve_precondition_gap` already makes
  (`inference_generation.py:969-970`). **[RUN]** confirmed live: a derived
  `can_fly` fact and the pre-existing `fragile→broken→worthless` empirical
  cascade coexist correctly on facts about the same session (test
  `test_logical_and_empirical_gaps_coexist_on_one_entity`, passing).

---

## 5. Untouched files — verified, not asserted

**[RUN]**, `git diff --stat b124038` restricted to the files that must stay
byte-identical:

```
$ git diff --stat b124038 -- domains/ground_reductions.py domains/comprehend_theorem.py \
    seeds/logic_foundation.json seeds/logic_propositional_predicate.json \
    seeds/inference_knowledge.json
(empty output)
```

Zero diff on all five. Full worktree diff, for completeness:

```
$ git diff --stat b124038
 domains/inference_generation.py | 119 ++++++++++++++++++++++++++++++++++++++--
 1 file changed, 114 insertions(+), 5 deletions(-)
```

(plus three new, untracked files: `domains/propositional_deduction.py`,
`seeds/inference_logical.json`, `tests/test_deduction_generalization.py`, and
this pair of docs — `git status --short` confirms nothing else moved.)

---

## 6. The live demonstration

**[RUN]**, fresh agent per case, `boot_core()`:

```
=== bird/fly (hand-seeded implication) ===
before: {'bird': 1}
after : {'bird': 1, 'can_fly': 1}

=== fish/swim (implication PARSED from prose at runtime) ===
mint: True logical_fish_can_swim
before: {'fish': 1}
after : {'fish': 1, 'can_swim': 1}

=== dog (discriminative null — no covering implication) ===
after : {'dog': 1}
any minted: False

=== regression spot-check: glass (empirical pipeline, unmodified) ===
{'fell': 1, 'location': 'the floor', 'holder': '(nobody)', 'on_floor': 1,
 'on_floor_inferred': 1, 'fragile': 1, 'broken': 1, 'broken_inferred': 1,
 'worthless': 1, 'worthless_inferred': 1, 'blocked_gap': 1}
```

`can_fly` and `can_swim` are DERIVED, never stated in "Tweety is a bird." /
"Nemo is a fish." — genuine modus ponens (`P` stated, held `P ⇒ Q`, `Q` not
yet drawn ⇒ `Q` derived) through the SAME collapse pipeline `inference_
generation.py` already runs for the five empirical gap kinds. The fish/swim
case is the sharper proof: the implication itself did not exist as seed data
at agent-boot time — `propositional_deduction.mint_logical_schema` parsed it
from ordinary conditional prose and installed it live, and the SAME unmodified
`decode_gap`/mint path picked it up with zero code change.

**Test file** `tests/test_deduction_generalization.py`, 14 tests, all real
(not smoke tests): parser generality (explicit "if X...X..." form, a held-out
bare-universal paraphrase, a property-consequent form, an honest residual on
unparseable prose), the headline hand-seeded derivation, the prose-minted
derivation, mint idempotency, coexistence with the empirical pipeline on one
entity, two discriminative nulls (uncovered antecedent; consequent already
held), mint-reuse confirmation, a source audit (no regex, no hardcoded
attr-literal branch, decode is the decision), an explicit git-diff scope guard
on the five must-stay-untouched files, and a direct-`situation_model_reader`
non-interference check.

**[RUN]**:

```
$ PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
    tests/test_deduction_generalization.py -p no:randomly -q
..............
14 passed in 2.53s
```

---

## 7. Regression — the 8 existing empirical schemas

**[RUN]**, `tests/test_inference_generation.py` (the existing 20-test suite
covering all 5 empirical gap kinds and the 8 `knowledge_*` schemas), run
AFTER all changes in this rung:

```
$ PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
    tests/test_inference_generation.py -p no:randomly -q
....................
20 passed in 5.92s
```

20/20, matching main's own baseline exactly (see §7.1 for the environment
caveat this number is conditioned on). Combined with the new suite:

```
$ python3 -m pytest tests/test_inference_generation.py \
    tests/test_deduction_generalization.py -p no:randomly -q
..................................
34 passed in 6.67s
```

Additional non-interference spot-checks, both green, both untouched by this
rung's code (they call `read_and_infer`/`situation_model_reader` from a
different angle):

```
tests/test_situation_model_wire.py .........  9 passed
tests/test_goal_licensing.py + test_embedded_reading.py  .........................  25 passed
```

### 7.1 An honest environment finding along the way, reported not hidden

**[RUN]**: the FIRST run of `tests/test_inference_generation.py` in the fresh
worktree (before any of this rung's code changes — confirmed via `git stash`)
returned **14 failed, 6 passed**, including `test_spine_unwired_still_bare`,
which calls `situation_model_reader` directly and touches none of this rung's
code. This is a **pre-existing, environment-conditional defect, not a
regression**: `git worktree add` does not populate `data/` (gitignored,
untracked, ~117MB of local corpus — `git check-ignore -v data` confirms the
pattern, `git ls-files data | wc -l` returns 0) — exactly the "`data/` absent"
condition CLAUDE.md's own retracted-note section already documents
elsewhere in this tree, encountered here independently. Fix: `ln -s
<main-repo>/data data` inside the worktree (the documented workaround; NOT
committed — `data` is untracked/ignored and stays a local convenience symlink,
confirmed absent from `git status --short`'s tracked output and never
`git add`ed). **[RUN]** confirmed on the pristine (pre-change) code with the
symlink in place: `20 passed` — i.e. this rung's numbers above are the true
baseline, and the defect was a worktree-provisioning artifact unrelated to any
code in this rung, caught and fixed rather than silently worked around or
left unexplained.

---

## 8. GO / NO-GO

**GO**, with the scope precisely as pre-registered:

**Built:**
- A graph-resident held-implication representation (`ShapeSignature{kind:
  "knowledge_logical"}`), an ADDITION to the existing codebook pool, zero new
  node types, zero Rust.
- A general propositional-conditional mini-parser
  (`domains/propositional_deduction.py`, `parse_conditional`/
  `mint_logical_schema`) — independent of `comprehend_theorem.py`, 8 surface
  forms across 2 conditional shapes ("if X is a/an P, X can/is Q" and the bare
  universal "a/an P can/is Q"), each honestly residual (`None`) outside its
  seeded forms.
- A sixth gap kind in the general pipeline (`detect_implication_gaps`/
  `resolve_implication_gap`, `domains/inference_generation.py`), modeled on
  the breadth-offer discipline (`detect_goal_gaps`) rather than the
  missing-one-conjunct discipline (`detect_precondition_gaps`), for the
  structural reason given in §3.
- Reuse, not reinvention, of `ground_reductions.py`'s proven
  antecedent/consequent separation (as a design model) and of the general
  pipeline's own `reading_collapse._winner` (in place of `GroundedReduction.
  compute`'s bespoke ordering) and `ingest_predication` (mint, verbatim).
- Live, passing, non-trivial demonstration of genuine modus ponens through the
  unmodified general collapse pipeline, both from a hand-seeded fact and from
  runtime-parsed prose.
- Zero regression: 8 existing schemas / 5 existing gap kinds / 20 existing
  tests byte-identical; `ground_reductions.py`, `comprehend_theorem.py`, both
  inert logic seed files, and `seeds/inference_knowledge.json` itself all
  git-diff-confirmed untouched.

**Named, NOT built (real residuals, not silently dropped — see prereg §6 for
the full list):**
- Conjunctive antecedents (`P₁ ∧ P₂ ⇒ Q`) — single-antecedent only in this
  landing.
- Quantified logic / universal instantiation — explicitly out of scope per the
  task; this rung's implications are attribute-generic across entities (any
  `bird=1` entity, not one named entity) but carry no variable-binding or
  nested-quantifier representation.
- Negation / modus tollens — the natural next rung if this one is picked up
  again; the inert `modus_tollens` prose entry in `logic_foundation.json`
  remains untouched and unconnected.
- The prose parser's generality is deliberately much narrower than
  `comprehend_theorem`'s (8 forms across 2 conditional shapes vs.
  `comprehend_theorem`'s larger construction grammar including
  biconditionals and symbolic values) — sized to what this rung's live demo
  needed, not to full theorem-grammar parity.

**Worktree:** `/home/matt/ozmadev/ocelot-worktrees/deduction-generalization`
**Branch:** `deduction-generalization`
**Base:** `main` @ `b124038`

Not merged into `main` (per instructions — the caller merges).
