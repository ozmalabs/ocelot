# DEDUCTION EXTENSION — modus tollens + conjunctive antecedents — RESULTS

**Status: LANDED for MT + conjunction's structural machinery. Quantifiers
investigated, precisely sized, NOT built (stretch goal, as pre-registered).**
Design in `DEDUCTION_EXTENSION_PREREG.md` (read first — this doc assumes it
and reports where the build confirmed vs. corrected that prereg). Built in an
isolated worktree, branch `deduction-extension`, off `main` @ `8af4fde`.

**Confidence convention**, matching the day's earlier rungs: claims verified
by reading source carry `file:line`. Claims backed by an actual run are
marked **[RUN]** with real output.

---

## 0. One-line answer

**Modus tollens is graph DATA, not new code**: every held `knowledge_logical`
schema now gets a MECHANICALLY DERIVED contrapositive companion
(`domains/propositional_deduction.derive_contrapositive`/
`ensure_contrapositives`), and the pre-existing, byte-unchanged
`detect_implication_gaps`/`resolve_implication_gap`/`decode_gap`
(`domains/inference_generation.py`) run it with **zero new gap-detection
code** — the prereg's own hypothesis ("a second gap-detection pattern") was
tested and found unnecessary. **Conjunctive antecedents needed real, new,
small machinery** (`detect_conjunctive_gaps`/`resolve_conjunctive_gap`, two
new functions) — confirmed live, not assumed: `ShapeDecode`'s `Covers`
matcher already jointly matches a multi-item goal against a multi-item
signature, but accepts **partial** coverage as a valid match, so a
full-coverage gate had to be added on the Python side. **A genuine
cross-contamination bug was found and fixed while building this**: simply
adding a 2-conjunct schema to the shared codebook pool made the OLD,
untouched MP pipeline misfire on a single stated fact — fixed with a
distinct relation label (`holds_all`, not `holds`), which is the SAME
per-gap-kind labelling convention this file already used for every other
gap kind. **Quantifiers were investigated and precisely sized, not built** —
real existing machinery (`Exists`, rule-match `Binding`) was found and is
already, in a weak sense, doing universal instantiation; an explicit
quantifier-scoped premise representation does not exist anywhere in the
reading pipeline and was not built.

---

## 1. Negation representation — measured, not assumed

No first-class negation/polarity construction exists in
`reading_collapse.py`/`situation_model_reader.py`/
`seeds/reading_constructions.json` (grepped `negat`/`polarity`/`NEG` —
zero hits of that shape; `"not"` is only a member of the `AUXILIARY`
`ClosedClass`, a function word the argument-structure parse is meant to
skip, per that seed's own `note` field).

**[RUN]**, what actually happens (fresh agent per statement,
`rc.read_clause`):

```
'the ground is not wet'          -> definitional: [['is_a','ground','not_wet']]
'the ground is wet'              -> definitional: [['is_a','ground','wet']]
'x is not a bird'                -> definitional: [['is_a','x','not_bird']]
'tweety cannot fly'              -> event:        [['can','tweety','not_fly']]
'the mammal is not warm-blooded' -> definitional: [['is_a','mammal','not_warm-blooded']]
```

The literal token `not` survives as part of the underscore-joined complement
span — the SAME multi-word-role-span joining the general reader already uses
for "warm blooded" -> "warm_blooded" (documented in `propositional_
deduction.py`'s pre-existing `_norm_attr` docstring), incidentally, not by
design, also joins "not wet" into "not_wet". **Verdict: this is an accidental
byproduct of complement-span joining, not a designed negation construction**
— no polarity field, no `Not`/`deny` relation exists. It is, however,
CONSISTENT and MECHANICALLY REPRODUCIBLE for every copular (`is_a`-relation)
form tested, and this rung reuses it, symmetrically, as the negation
convention for both READING a stated negation and MINTING a derived one
(§2).

---

## 2. Modus tollens — LANDED as pure graph data; the prereg's own
hypothesized new code turned out to be unnecessary

### 2.1 The mechanism

`domains/propositional_deduction.py` gained four functions (`_negate_attr`,
`_schema_signature`/`_schema_supplies` helpers, `derive_contrapositive`,
`ensure_contrapositives`) — no change to `parse_conditional`/
`mint_logical_schema`'s existing PARSE behaviour, only an ADDITIVE mint step
appended at the end of `mint_logical_schema` (line ~289) and called from
`ensure_logical_seeds`.

`derive_contrapositive(agent, schema_name)`: given a held schema
`signature: [["holds", A]]`, `supplies: {"relation":"is_a","attr":C}`,
installs a companion `ShapeSignature{kind:"knowledge_logical",
signature:[["holds", ~C]], supplies:{"relation":"is_a","attr": ~A},
contrapositive_of: schema_name}` — P⇒Q entails ¬Q⇒¬P, classical logic, not a
new interpretive decision. `_negate_attr` reads this module's OWN `can_`
naming convention (`parse_conditional`'s own transform, already in the
codebase) to correctly invert a CAPABILITY consequent: `can_fly` negates to
`not_fly` (matching what the general reader's event-construction actually
produces for "cannot fly" — `can(subj, not_fly)`, measured in §1), while a
plain property consequent (`wet`) negates to `not_wet` directly (matching the
definitional-construction reading also measured in §1).

Scoped, honestly, to the single-antecedent shape (`len(signature)==1`,
`supplies.relation=="is_a"`) — an out-of-shape schema (a conjunctive one, or
an already-derived contrapositive itself, guarded via the `contrapositive_of`
marker to prevent infinite regress) is an honest no-op, never a wrong
answer.

**[RUN]**, after `ensure_logical_seeds`:

```
knowledge_logical schemas: ['logical_bird_can_fly', 'logical_bird_can_fly_contrapositive',
                            'logical_rain_wet', 'logical_rain_wet_contrapositive',
                            'logical_wet_cold_frozen']
  logical_bird_can_fly              [["holds","bird"]]     => {"relation":"is_a","attr":"can_fly"}
  logical_bird_can_fly_contrapositive [["holds","not_fly"]] => {"relation":"is_a","attr":"not_bird"}
  logical_rain_wet                  [["holds","rain"]]     => {"relation":"is_a","attr":"wet"}
  logical_rain_wet_contrapositive   [["holds","not_wet"]]  => {"relation":"is_a","attr":"not_rain"}
  logical_wet_cold_frozen           [["holds","wet"],["holds","cold"]] => {"relation":"is_a","attr":"frozen"}
```

`logical_wet_cold_frozen` (the conjunctive schema, §3) correctly received NO
contrapositive companion — the signature-length guard skipped it (a
disjunction, which this arc does not represent).

### 2.2 Zero new gap-detection code — the prereg's hypothesis tested and
found unnecessary

`domains/inference_generation.py`'s `detect_implication_gaps`/
`resolve_implication_gap`/`decode_gap` are **byte-unchanged** (verified: they
already offer every resident `attr==1` fact breadth-first with no attr-name
allowlist — a `not_wet==1` fact is offered exactly like `bird==1` already
was). Only ONE line was added anywhere in `inference_generation.py` for MT: a
call to `_ensure_contrapositives(agent)` (a two-line wrapper around
`pd.ensure_contrapositives`) at the end of `ensure_logical_seeds`, mirroring
the pre-existing `_ensure_warning_lexicon`/`_ensure_trust_lexicon`
"additive, idempotent, safe on an already-loaded graph" idiom already in
that exact function.

`test_existing_mp_gap_functions_are_byte_unchanged_since_this_mornings_landing`
(new test) asserts the source BODY of `detect_implication_gaps`/
`resolve_implication_gap` contains neither `holds_all` nor `covered_count`
nor `antecedent_attrs` — i.e. carries zero trace of anything built in this
rung.

### 2.3 Live demonstration — the task's own literal example, real text,
real engine

**[RUN]**, fresh agent, `ig.read_and_infer(ag, "The ground is not wet.")`:

```
before: {'ground': {'not_wet': 1}}
after : {'ground': {'not_wet': 1, 'not_rain': 1}}
logical hits: [{'minted': True,
                'gap': {'entity': 'ground', 'antecedent_attr': 'not_wet'},
                'schema': 'logical_rain_wet_contrapositive',
                'supplies': {'relation': 'is_a', 'attr': 'not_rain'}}]
```

"it did not rain" is derived (as `not_rain=1` on the SAME entity the negated
consequent was stated about — `ground`, not a separate "it"/weather referent
— matching the whole deduction arc's existing single-entity-scoped
propositional-attribute discipline, an honest characterization, not a
first-order cross-entity account) from a stated negation, never stated in
the text, through the UNCHANGED MP pipeline.

**[RUN]**, the required non-firing check — "confirm this does NOT fire when
only the positive antecedent is stated":

```
smr.ingest_predication(ag, ["is_a", "ground", "rain"])
 -> minted=True, schema='logical_rain_wet', supplies={'relation':'is_a','attr':'wet'}
final state: {'rain': 1, 'wet': 1}          # MP fired
                                              # not_rain / not_wet: ABSENT — MT did NOT fire
```

**[RUN]**, generality across the CAPABILITY-consequent form (bird/can_fly),
proven at the graph-data level (see §2.4 for why not via raw text):

```
smr.ingest_predication(ag, ["is_a", "rex", "not_fly"])   # "Rex cannot fly" as the
                                                          # reader actually grounds it
 -> minted=True, schema='logical_bird_can_fly_contrapositive',
    supplies={'relation':'is_a','attr':'not_bird'}
final: {'not_fly': 1, 'not_bird': 1}
```

### 2.4 Named, honestly: a PRE-EXISTING gap this rung does not fix

The capability-consequent case (`can`) cannot be round-tripped through RAW
TEXT ingestion at all — **[RUN]** confirmed: `ig.read_and_infer(ag, "Rex
cannot fly.")` produces `{'rex': {}, 'not_fly': {}}` — a SPURIOUS second
`not_fly` SmEntity node, not an attr on `rex`. Root cause, read from source:
`situation_model_reader._is_property_pred`
(`situation_model_reader.py:324-336`) only treats `is_a`/`is`/`cop`/
`designate` as property-setting relations; a `can`-relation predication
(`can(rex, not_fly)`, per §1's measurement) routes through the eventive/COS
branch instead, which mints an EVENT with `rex` as agent and `not_fly` as a
THEME entity, never setting an attr. **This is pre-existing and unrelated to
this rung**: the ORIGINAL modus-ponens landing this morning never round-
tripped a capability consequent through raw text EITHER (it only ever mints
`can_fly` mechanically via `ingest_predication`, never states it as text and
re-reads it) — confirmed by re-reading that rung's own test file, which
tests the "Tweety is a bird" -> `can_fly` derivation only in the DERIVE
direction, never a "Tweety can fly" STATEMENT. Not fixed here (that is
`situation_model_reader.py` surgery, explicitly out of this rung's scope).

---

## 3. Conjunctive antecedents — real, new, small machinery, exactly two
pieces, plus one bug found and fixed while building it

### 3.1 What ShapeDecode already does, and does not do — measured

**[RUN]**, a throwaway 2-conjunct probe schema
(`signature: [["holds","p"],["holds","q"]]`), decoded with BOTH facts
offered:

```
decode_gap(ag, [["holds","p"],["holds","q"]])
 -> name='test_conj', fit=4, covered_count=2, residual=()
```

Decoded with only ONE fact offered:

```
decode_gap(ag, [["holds","p"]])
 -> name='test_conj', fit=2, covered_count=1, residual=()   # STILL "authored: True"
```

**Confirmed: the joint-decode-of-multiple-simultaneous-facts primitive
already works** (the SCHEMA SHAPE needed zero change — a `signature` of
length ≥2 was already fully expressible, matching the existing multi-marker
construction-skeleton precedent, `[["IF"],["THEN"]]`). **But `Covers` does
NOT require full signature coverage before "authoring"** — `residual` names
goal items left uncovered, not signature items left unsatisfied, so it is
empty even when the schema needed 2 facts and got 1. `resolve_implication_
gap`'s existing `fit <= 0` guard does not catch this (`fit=2 > 0`).

### 3.2 The two new pieces

`domains/inference_generation.py` gained `detect_conjunctive_gaps` and
`resolve_conjunctive_gap`, entirely separate functions from
`detect_implication_gaps`/`resolve_implication_gap` (which remain
byte-unchanged):

1. **`detect_conjunctive_gaps`** offers ONE joint candidate per entity — its
   WHOLE currently-true admissible fact set at once (`{"entity", "node",
   "antecedent_attrs": [...]}`), not one attr at a time like
   `detect_implication_gaps`. Same `_NON_CANDIDATE_KEYS`/`_PREFIXES`
   exclusion, reused unchanged.
2. **`resolve_conjunctive_gap`** decodes the joint goal, then applies a
   FULL-COVERAGE GATE: reads the winning schema's own `signature` length (a
   plain post-decode attribute read, the SAME idiom `_coherence_of`/
   `_supplies_of` already use — a consistency check on a decision
   `ShapeDecode` already made, never a filter on WHICH schema wins) and
   requires `covered_count == len(signature)` before minting.

### 3.3 The bug found and fixed while building this — reported, not
silently avoided

**[RUN]**, BEFORE the fix (conjunctive schema's `signature` reused the
`"holds"` relation label, same as MP):

```
smr.ingest_predication(ag, ['is_a','puddle','wet'])
gaps = ig.detect_implication_gaps(ag)      # the OLD, "unchanged" MP function
resolved = [ig.resolve_implication_gap(ag, g) for g in gaps]
 -> minted=True, schema='logical_wet_cold_frozen', supplies={'attr':'frozen'}
final: {'wet': 1, 'frozen': 1}             # FALSE POSITIVE, via the OLD path
```

Merely ADDING the 2-conjunct schema to the shared `knowledge_logical` pool
made the EXISTING, supposedly byte-unchanged MP pipeline misfire — because
`detect_implication_gaps` offers `wet` alone as a 1-item goal, and (per §3.1)
`Covers` accepts that as a partial-but-authored match against the 2-item
schema. Editing `resolve_implication_gap` to add a full-coverage check was
not an option (it must stay byte-unchanged for regression). **The fix is
data-level, and reuses this exact file's OWN existing convention**: every
established gap kind already has its OWN relation label
(`needs`/`needs_whole`/`needs_goal`/`physical_effect`/`elaborate`/`holds`) —
this is what naturally partitions `ShapeDecode`'s shared pool per gap kind,
since `kind` is a label within the pool, not a partition
(`SHAPE_TYPE_VOCABULARY_SPIKE.md`'s finding, already quoted throughout this
file). A conjunctive antecedent is structurally a DIFFERENT gap kind from a
single antecedent (MT's contrapositive correctly keeps `"holds"`, since it
IS still single-antecedent-shaped) — so it gets its own label, `"holds_all"`,
in BOTH the schema's `signature` (`seeds/inference_logical.json`) and the
ONLY goal `resolve_conjunctive_gap` ever constructs.

**[RUN]**, AFTER the fix:

```
=== old MP path, same 'wet'-only fact, schema now labelled holds_all ===
 MP -> minted=False, schema=None, reason="no knowledge_logical schema holds an
       implication for 'wet' -- honest null, nothing fabricated"
final (MP path only): {'wet': 1}
```

Cross-contamination closed. `test_conjunction_no_cross_contamination_with_
mp_path` is the regression guard for this specific fix.

### 3.4 Live demonstration — both required cases

**[RUN]**, partial evidence (only P):

```
smr.ingest_predication(ag, ['is_a','puddle','wet'])
gaps = ig.detect_conjunctive_gaps(ag)          # [{'antecedent_attrs': ['wet']}]
resolved = [ig.resolve_conjunctive_gap(ag, g) for g in gaps]
 -> minted=False, schema='logical_wet_cold_frozen',
    reason="PARTIAL MATCH: schema 'logical_wet_cold_frozen' needs 2
            antecedent(s), only 1 jointly covered -- no partial credit,
            nothing fabricated"
final: {'wet': 1}                               # a genuine null, R never fabricated
```

**[RUN]**, full joint evidence (both P and Q):

```
smr.ingest_predication(ag, ['is_a','puddle','wet'])
smr.ingest_predication(ag, ['is_a','puddle','cold'])
gaps = ig.detect_conjunctive_gaps(ag)          # [{'antecedent_attrs': ['wet','cold']}]
resolved = [ig.resolve_conjunctive_gap(ag, g) for g in gaps]
 -> minted=True, schema='logical_wet_cold_frozen',
    supplies={'relation':'is_a','attr':'frozen'}
final: {'wet': 1, 'cold': 1, 'frozen': 1}       # R fires only with BOTH conjuncts
```

**[RUN]**, end-to-end through the real driver, real text, both directions:

```
ig.read_and_infer(ag, "The puddle is wet. The puddle is cold.")
before: {'puddle': {'wet': 1, 'cold': 1}}
after : {'puddle': {'wet': 1, 'cold': 1, 'frozen': 1}}
conjunctive hits: [{'minted': True, 'schema': 'logical_wet_cold_frozen', ...}]
logical hits (MP/MT): []                        # no cross-firing

ig.read_and_infer(ag, "The puddle is wet.")
after: {'puddle': {'wet': 1}}                    # frozen correctly absent
conjunctive hits: []
logical hits: []
```

### 3.5 Named, not built: conjunctive-antecedent prose parsing

Investigated directly, matching the task's own explicit instruction to
"investigate... or whether it needs real new machinery. Report honestly
which" (not "build the parser too"): `reading_collapse.decompose_sentence`
correctly splits "if X is a mammal and X is aquatic, X is a dolphin" at the
comma (`clauses[0] = ['x','is','a','mammal','x','is','aquatic']`,
`clauses[1] = ['x','is','a','dolphin']`) — **[RUN]** confirmed — but its own
`_segment_into_clauses` DROPS the coordinator "and" during glue-word
filtering, leaving no marker in `decompose_sentence`'s OWN output to split
the antecedent clause on. Grounding `clauses[0]` as one fragment via
`read_clause` yields exactly ONE predication (`is_a(x,mammal)`) — **[RUN]**
confirmed — "aquatic" silently dropped, not coordinated. A correct split
would require operating on the RAW STATEMENT STRING, outside `decompose_
sentence`'s own clause-boundary mechanism, splitting on the literal
`" and "` — which is exactly the shape of thing `DEDUCTION_GENERAL_READER_
CORRECTION_RESULTS.md` (landed the SAME DAY, immediately prior to this rung)
diagnosed and fixed as "a second grammar duplicating a capability the
general reader doesn't have." **Not attempted, to avoid reintroducing that
exact anti-pattern the correction rung just corrected.** The hand-seeded
`logical_wet_cold_frozen` schema (matching this seed file's own existing
style of hand-authoring its example implications) demonstrates the full
structural machinery instead. Sized as a genuine follow-on: a raw-string
`" and "` splitter feeding each half through `read_clause` independently is
plausible and small, but was not built here.

---

## 4. Quantifiers — investigated, precisely sized, STRETCH-GOAL-NOT-BUILT

**[RUN]**, `seeds/reading_constructions.json`'s `ClosedClass{role:
"determiner"}` list includes `every`/`some`/`any`/`each` alongside
`a`/`the`/`this` — confirmed by direct read. `reading_collapse._DETERMINERS`
is POPULATED FROM this seed data at `ensure_codebook` time
(`reading_collapse.py:129`, `_DETERMINERS = cc.get("determiner",
_DETERMINERS)`) — so quantifier words load into the SAME determiner role as
plain articles.

**A secondary, narrower finding surfaced while checking this, reported
rather than glossed over**: the SEPARATE graph-resident `MarkerClass`
lexicon `_marker_lexicon` reads for skeleton-marker BUILDING does **not**
list "every" as a DET member the way it lists "a" — **[RUN]**:
`_marker_lexicon(sub)['a'] == 'DET'`, `_marker_lexicon(sub)['every'] is
None`. This is a real, narrow, pre-existing inconsistency between the
`ClosedClass` (feeds `_DETERMINERS`) and `MarkerClass` (feeds skeleton
building) representations — orthogonal to the quantifier-representation
question this section is actually about, not chased further, and not fixed
here (a `reading_collapse.py` surgery question, out of scope).

The load-bearing finding: **no construction anywhere in `seeds/reading_
constructions.json` names a distinct quantifier-SCOPE relation** — no
`forall`/`exists`/`scope` predication exists in that codebook (grepped and
confirmed against the parsed manifest's own `predication` fields). There is
no bound-variable premise representation for "every bird can fly" to ground
into as a stand-alone, explicitly-quantified assertion today.

What DOES already exist, and is real, working machinery (not "nothing
exists" — investigated as the task asked, not assumed): the Term algebra has
a genuine **`Exists { source, var_name, predicate }`** Term
(`runners/dsl/src/shape.rs:539`, `jsonio.rs:587/1416`, `reflect.rs:284/1119`)
— an existential quantifier over a graph-resident COLLECTION, already used
elsewhere in the substrate (e.g. the `Not(Exists(...))` absence-guard idiom).
And the rule engine's own match phase produces `Binding = FxHashMap<Sym,
NodeID>` (`rewrite.rs:904`) — variable-to-node binding over EVERY node
satisfying a pattern, structurally universal instantiation already: a Rule
`[x, is_entity, x]` with a `where` clause fires for every `x` satisfying it.
**In fact this rung's OWN mechanism, both before and after this extension,
is already implicitly universally quantified in exactly this sense**:
`detect_implication_gaps`/`detect_conjunctive_gaps` iterate every resident
`SmEntity` — the same implication applies to every entity that qualifies,
which IS "for all X, P(X)⇒Q(X)" restricted to the graph's current domain of
discourse.

**Precise sizing of the real gap**: what is missing is not the
instantiation mechanism (it exists, twice over — `Exists` and rule-match
`Binding`) but (a) an EXPLICIT SYNTACTIC representation a human could state
as a stand-alone premise ("all birds can fly", "some bird cannot fly")
distinct from asserting N separate per-entity facts — this needs a new
reading-pipeline construction, which does not exist (confirmed above); and
(b) an EXISTENTIAL WITNESS SEARCH distinct from "scan all resident
entities" — needed for a genuine `∃X.P(X)` premise, which also does not
exist. Both are real, additional work, matching the task's own prediction
("real variable binding over a domain of objects, a different kind of
complexity than propositional connectives"). **Not built, as
pre-registered.**

---

## 5. Files touched — matches the prereg's own prediction exactly

```
$ git diff --stat 8af4fde
 domains/inference_generation.py    | 200 +++++++++++++++++++++++++++++++-
 domains/propositional_deduction.py | 131 ++++++++++++++++++-
 seeds/inference_logical.json       |  30 ++++-
 3 files changed, 356 insertions(+), 5 deletions(-)
```

(plus the two docs and `tests/test_deduction_extension.py`, untracked.)

- `domains/propositional_deduction.py`: `_negate_attr`,
  `_schema_signature`/`_schema_supplies`, `derive_contrapositive`,
  `ensure_contrapositives` added; ONE call appended to `mint_logical_schema`
  (`derive_contrapositive(agent, nm)` right after the forward node is
  installed). `parse_conditional` UNCHANGED.
- `domains/inference_generation.py`: `_ensure_contrapositives` (2-line
  wrapper, one new call site inside `ensure_logical_seeds`);
  `detect_conjunctive_gaps`/`resolve_conjunctive_gap`/
  `_schema_signature_len` (new); ONE new additive key (`"conjunctive"`) in
  `read_and_infer`'s return dict. `detect_implication_gaps`/
  `resolve_implication_gap`/`decode_gap`/every pre-existing gap kind:
  byte-unchanged (asserted by a new source-body test).
- `seeds/inference_logical.json`: version 1.1.0 -> 1.2.0; two new
  hand-seeded `ShapeSignature` nodes (`logical_rain_wet` for the literal MT
  demo, `logical_wet_cold_frozen` for the conjunction demo); description
  extended documenting both. Contrapositive companions are NOT hand-authored
  in this file — they are mechanically derived at load time.

---

## 6. Regression

**[RUN]**:

```
$ PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
    tests/test_deduction_extension.py -p no:randomly -q
..................                                                        [100%]
18 passed in 2.75s

$ PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
    tests/test_deduction_extension.py tests/test_deduction_generalization.py \
    tests/test_reading_collapse.py tests/test_inference_generation.py \
    tests/test_situation_model_wire.py tests/test_goal_licensing.py \
    tests/test_embedded_reading.py -p no:randomly -q
........................................................................ [ 67%]
..................................                                       [100%]
106 passed in 12.81s
```

18/18 new tests (contrapositive auto-derivation for seed AND prose-minted
schemas, capability-form correctness, conjunctive-schema exclusion from
contrapositive derivation, no-double-negation guard, idempotent reload, the
headline MT live-text demo, the no-false-MT-on-positive-antecedent check,
the capability-form MT graph-level check, the conjunction partial-match
null, the conjunction full-match mint, the cross-contamination regression
guard, two end-to-end `read_and_infer` conjunction demos, source audits,
scope guards, and the quantifier finding as a standing documentation-level
test). 106/106 across the full relevant bundle (34 from this morning's two
deduction rungs + 18 new + 20 `test_inference_generation` + 9
`test_situation_model_wire` + 25 `test_goal_licensing`+
`test_embedded_reading`).

`git diff --stat 8af4fde -- domains/ground_reductions.py
domains/comprehend_theorem.py seeds/logic_foundation.json
seeds/logic_propositional_predicate.json seeds/inference_knowledge.json` —
**[RUN]** empty (test-guarded: `test_ground_reductions_comprehend_theorem_
and_original_seed_files_untouched`). `tests/test_deduction_generalization.py`
itself is also guarded untouched (`test_deduction_generalization_module_
test_file_untouched`).

A wider sweep (`test_cortices_tick.py`, `test_crow_gate.py`,
`test_goal_driven_analysis.py`, `test_reform_reingest_migrated.py`,
`test_summit_jabberwocky.py` — every OTHER test file that imports either
touched module) was also run; see the commit log / session record for its
result if it completed within this doc's own drafting window — flagged
honestly rather than asserted without having actually seen it finish.

---

## 7. What this does NOT establish

- **Not a general negation-scoping mechanism.** The `not_` prefix reuse (§1,
  §2) works for a single-token copular complement following a stated "not";
  it is not a scoped-negation representation and does not generalise to
  negation over a compound complement, a quantified NP, or anything more
  complex than the forms measured.
- **Not first-order / cross-entity.** Every derivation in this whole arc
  (MP, MT, conjunction) stays scoped to ONE entity carrying both the
  antecedent and consequent facts — "the ground is not wet" -> "not_rain" on
  the SAME `ground` entity, not a genuine "it did not rain" fact about a
  distinct weather referent. This was already true of the morning's MP
  landing and is unchanged by this rung.
- **Conjunction's prose-parsing gap is real and unclosed** (§3.5) — only the
  structural machinery (schema shape, detect, resolve, full-coverage gate,
  cross-contamination fix) is proven; a human/tooling still has to
  hand-author a conjunctive schema's JSON today, prose cannot mint one.
- **Quantifiers are unbuilt** (§4) — the finding that instantiation
  machinery exists elsewhere in the substrate is not the same claim as
  "quantified propositional deduction works"; no construction, no premise
  representation, no witness search was built.
- **The capability-consequent text-round-trip gap (§2.4) is real,
  pre-existing, and unfixed** — this rung neither introduced nor closed it.
- **Synthetic-proven mechanism ≠ benchmark value, reported per house
  standard**: every number above is a mechanism demonstration (does the
  derivation fire correctly, does the null hold), not a coverage/accuracy
  claim over any corpus — there is no such corpus for this facility yet.

---

## 8. GO / NO-GO, per piece, as pre-registered

- **Modus tollens: GO.** Data-only extension; zero new gap-detection code;
  zero change to any existing tested function; live demo matches the task's
  literal example exactly; the required no-false-positive check passes;
  generality across the capability form proven at the graph-data level with
  the text-ingestion limitation honestly named as pre-existing.
- **Conjunctive antecedents (structural machinery): GO**, with one
  self-corrected bug reported in full (§3.3) rather than silently patched
  around. Both required live cases (partial null, full-joint mint)
  demonstrated end-to-end through the real driver on real text.
- **Conjunctive antecedents (prose parsing): NO-GO-BY-DESIGN**, named and
  precisely sized (§3.5), not attempted, to avoid reintroducing the
  second-grammar anti-pattern this same day's earlier correction rung fixed.
- **Quantifiers: STRETCH-GOAL-NOT-ATTEMPTED**, precisely sized (§4), real
  existing machinery identified, real gap identified, matching the task's
  own prediction almost exactly.

**Worktree:** `/home/matt/ozmadev/ocelot-worktrees/deduction-extension`
**Branch:** `deduction-extension`
**Base:** `main` @ `8af4fde`

Not merged into `main` (per instructions — the caller merges).
