# QUANTIFIED DEDUCTION — universal + existential instantiation — RESULTS

**Status: LANDED for both pieces.** Design in `QUANTIFIED_DEDUCTION_PREREG.md`
(read first — this doc assumes it and reports where the build confirmed vs.
corrected that prereg). Built in an isolated worktree, branch
`quantified-deduction`, off `main` @ `76b8aea`.

**Confidence convention**, matching this arc's own house style: claims
verified by reading source carry `file:line`. Claims backed by an actual run
are marked **[RUN]** with real output.

---

## 0. One-line answer

**Universal instantiation is a NEW PARSE reusing OLD MACHINERY, exactly
mirroring the modus-tollens precedent**: `propositional_deduction.
parse_universal`/`mint_universal_schema` strip the leading quantifier word
from the RAW STATEMENT STRING (measured live: the whole-clause reading path
does not itself strip "all"/"some"/"every", despite the isolated-span
primitives `_arg_head`/`_clean_head` handling it correctly — a narrow,
pre-existing reader inconsistency, NOT fixed), delegate the remainder to the
EXISTING, byte-unchanged `parse_conditional`, then singularise via a NEW
WordNet-morphy noun-lemma helper — and the resulting schema is picked up by
`detect_implication_gaps`/`resolve_implication_gap`/`decode_gap` (**all three
byte-unchanged**) with **zero new gap-detection code**, the SAME finding the
modus-tollens rung already made for its own extension. A REAL syllogism
("All philosophers are mortal" + "Socrates is a philosopher" → "Socrates is
mortal") was proven **[RUN]**, prose-minted end to end, with **no hand-seeded
fallback needed at all** — stronger than the MT/conjunction demos, which each
needed one. It also composes with modus tollens **for free** (confirmed
**[RUN]**: the universally-quantified schema auto-derives its contrapositive
via the unchanged `ensure_contrapositives` batch scan). **Existential
instantiation is real, new, small WITNESS-SEARCH machinery**
(`inference_generation.detect_existential_gaps`/`resolve_existential_gap`),
materially different in kind from universal instantiation's breadth-apply —
search for ONE qualifying entity first, MINT a fresh witness constant only
if none exists (the sd loop's own search-before-mint ordering, applied
without needing the sd loop itself), using a distinct relation label
(`holds_some`) to avoid the SAME class of cross-contamination the
conjunction rung already found and fixed for `holds_all`. Both live demos
(**search-found**, **search-mint**) proven **[RUN]**, including the
capability form of universal instantiation. **A build-environment defect
was found, misdiagnosed once, then correctly re-diagnosed and fixed under
coordinator re-verification (§5)**: this worktree's `data/` (gitignored,
~600MB, holding the Wiktionary POS dump the general reader's verb-detection
fallback reads) was absent — `git worktree add` never copies gitignored
files — silently degrading `is_verb_headed` to `False` for every word, not
a quantifier- or capability-specific defect. Fixed by symlinking `data/` to
the canonical tree, the project's own documented convention. Zero new Rust
Terms; zero regressions — the full required regression bundle plus this
rung's own suite is 56/56 green in one invocation, and the wider bundle is
129/129 green (§6).

---

## 1. Universal instantiation — quantifier grounding, measured live

**Confirmed exactly as the PREREG predicted**, `pd.parse_conditional`
(unmodified) fed whole quantified sentences directly:

```
'All men are mortal'      -> read_clause predications: [['is_a','all_men','mortal']]
'Every bird can fly'      -> predications: [['bird','every','can_fly']]   (garbled)
'Some birds are penguins' -> predications: [['is_a','some_birds','penguins']]
'A man is mortal'         -> predications: [['is_a','man','mortal']]      (correct)
```

The quantifier word is NOT stripped from the subject by the whole-clause
path `parse_conditional`'s `bare_universal` branch calls
(`domains/propositional_deduction.py:215`), despite `_DETERMINERS`
(`domains/reading_collapse.py:2277-2278`) already listing
`any`/`each`/`every`/`some` — **[RUN]** confirmed the isolated-span
primitives DO strip them correctly:

```
_arg_head(ag, "a man")     -> "man"
_arg_head(ag, "some man")  -> "man"
_arg_head(ag, "all men")   -> "men"
_arg_head(ag, "every bird")-> "bird"
```

So the machinery exists; the whole-sentence subject-extraction path simply
never routes through it for this shape. NOT fixed (`reading_collapse.py`
surgery, out of scope, same discipline `DEDUCTION_GENERAL_READER_
CORRECTION_RESULTS.md` already established for a sibling gap).

**The build**: strip the quantifier word from the RAW STATEMENT STRING
BEFORE `decompose_sentence`/`read_clause` ever see it, then hand the
remainder to `parse_conditional`, UNCHANGED. **[RUN]**:

```
pd.parse_conditional(ag, "philosophers are mortal")
 -> {'antecedent_attr': 'philosophers', 'consequent_relation': 'is',
     'consequent_attr': 'mortal', 'form': 'bare_universal', ...}
```

**A second, orthogonal residual, found and closed while confirming this**:
no noun-plural lemmatiser exists anywhere in the general reader —
`'philosophers'` survives as a literal plural. The SAME held WordNet
reference `situation_model_reader._lemma`/`reading_collapse._clean_head`
already depend on fixes this too, applied to the NOUN pos tag instead of the
verb one already used elsewhere (`domains/propositional_deduction.py`'s new
`_singular_attr`). **[RUN]**:

```
wn.morphy('philosophers', 'n') -> 'philosopher'
wn.morphy('penguins', 'n')     -> 'penguin'
wn.morphy('mortal', 'n')       -> 'mortal'   (already singular, safe no-op)
wn.morphy('can_fly', 'n')      -> None       (not a noun form, safe fallback)
wn.morphy('men', 'n')          -> 'men'      (IRREGULAR PLURAL, NOT fixed —
                                                named, not papered over)
```

**Honest, named limitation**: irregular plurals (`men` → `man`) are not
reached by plain `wn.morphy` lookups the way regular `-s` plurals are — the
live demo below is therefore built on a regular plural (`philosophers`), not
the textbook `"All men are mortal"` phrasing literally. Same STYLE, same
structure, real WordNet-grounded Concepts, per the task's own "all-men-mortal
STYLE" framing.

---

## 2. The quantifier-word recognition — a thin I/O-boundary classifier,
graph-resident, mirroring `WarningLexicon`/`TrustLexicon`

No construction in `seeds/reading_constructions.json` names a distinct
quantifier-SCOPE relation (grepped, zero hits of that shape — confirmed,
not assumed) — recognising the leading quantifier word is CLAUDE.md's own
named carve-out: *"converting an opaque external form into the smallest
graph token, AND there's no Rust primitive that can do the job."*

**Built**: a graph-resident `QuantifierLexicon` node
(`seeds/inference_logical.json` local_id 5,
`{"universal": ["all","every","each"], "existential": ["some"]}`), read via
`propositional_deduction._quantifier_lexicon` (mirrors
`inference_generation._warning_lexicon`/`_trust_lexicon`'s exact idiom), and
`_split_leading_quantifier` — plain `str.split(None, 1)` + lowercase +
membership check. No regex (source-audited, §7).

**Scoping decision, deliberately avoiding a collision the conjunction rung's
own history warns about**: `"a"/"an"` are NOT members — they stay owned by
the EXISTING `bare_universal` generic reading, unchanged. **[RUN]**
confirmed:

```
pd.parse_universal(ag, "A philosopher is mortal") -> None   # not claimed by the new lexicon
```

---

## 3. Universal instantiation — LANDED exactly as predicted: new PARSE,
reused MINT/DETECT/RESOLVE

`domains/propositional_deduction.py` gained `_singular_attr`,
`_quantifier_lexicon`, `_split_leading_quantifier`, `parse_universal`,
`mint_universal_schema` — all NEW, SELF-CONTAINED (not a refactor of
`parse_conditional`/`mint_logical_schema`, which stay byte-unchanged,
source-audit-guarded, §7). `mint_universal_schema` installs a
`ShapeSignature{kind:"knowledge_logical", quantifier:"universal"}` node —
structurally identical to any other single-antecedent MP schema — so
`domains/inference_generation.py`'s `detect_implication_gaps`/
`resolve_implication_gap`/`decode_gap` (`inference_generation.py:943/966/
1171`, **all three untouched**, source-audit-guarded §7) run universal
instantiation with **zero new gap-detection code**.

### 3.1 The headline live demo — the task's own literal requirement, real
Concepts, real engine, prose-minted end to end

**[RUN]**:

```
minted = pd.mint_universal_schema(ag, "All philosophers are mortal")
 -> minted=True, name='logical_universal_philosopher_mortal',
    parsed={'antecedent_attr': 'philosopher', 'consequent_attr': 'mortal', ...}

smr.ingest_predication(ag, ["is_a", "socrates", "philosopher"])
 -> socrates: {'philosopher': 1}

gaps = ig.detect_implication_gaps(ag)   # UNCHANGED
 -> [{'entity': 'socrates', 'antecedent_attr': 'philosopher', ...}]

resolved = [ig.resolve_implication_gap(ag, g) for g in gaps]   # UNCHANGED
 -> minted=True, schema='logical_universal_philosopher_mortal',
    supplies={'relation': 'is_a', 'attr': 'mortal'}

socrates: {'philosopher': 1, 'mortal': 1}
```

**A real syllogism — Socrates, philosopher, mortal, all real WordNet-grounded
Concepts — proven through the graph engine, no hand-seeded schema, no toy
strings.** Unlike MT's `logical_rain_wet` (hand-seeded because its
antecedent is an event predication outside `parse_conditional`'s grammar)
and conjunction's `logical_wet_cold_frozen` (hand-seeded because prose
conjunction-splitting was out of scope), **this rung needed zero hand-seeding
for its headline demo** — both `parse_universal` and `parse_existential`
reach real prose cleanly.

**[RUN]**, the required no-firing check:

```
pd.mint_universal_schema(ag2, "All philosophers are mortal")   # no resident philosopher entity
[g for g in ig.detect_implication_gaps(ag2) if g["antecedent_attr"] == "philosopher"] -> []
```

**[RUN]**, end to end via the real driver, real text:

```
r = ig.read_and_infer(ag, "Socrates is a philosopher.")
before_situation_model: {'socrates': {'philosopher': 1}}
logical hits: [{'minted': True, 'schema': 'logical_universal_philosopher_mortal', ...}]
after: {'socrates': {'philosopher': 1, 'mortal': 1}}
```

### 3.2 Composes with modus tollens for free — a predicted finding,
confirmed, not assumed

Because the minted schema is `kind:"knowledge_logical"` with a length-1
signature, `ensure_contrapositives`'s existing batch scan
(`propositional_deduction.py:398`) picks it up automatically. **[RUN]**:

```
names -> {..., 'logical_universal_philosopher_mortal',
              'logical_universal_philosopher_mortal_contrapositive', ...}

smr.ingest_predication(ag, ["is_a", "plato", "not_mortal"])
resolve_implication_gap(...) for plato -> minted=True,
  supplies={'relation': 'is_a', 'attr': 'not_philosopher'}
```

Zero new code for this — the SAME composition MT itself already
demonstrated, now shown to extend one level further.

### 3.3 Idempotency, capability form, residuals

**[RUN]**: `mint_universal_schema` called twice with the identical statement
→ `minted=True` then `minted=False, already=True`, same schema name both
times. **[RUN]**: `parse_universal(ag, "philosophers are mortal")` (no
leading quantifier) → `None`, the honest residual.

---

## 4. Existential instantiation — LANDED: real, new, small witness-search
machinery, materially different from universal's breadth-apply

**Why this is NOT the same shape as universal, precisely, per the PREREG's
own framing, confirmed live**: universal instantiation licenses "apply the
consequent to EVERY resident entity that satisfies the antecedent" — exactly
what `detect_implication_gaps`'s breadth-first scan already does (the
graph-native realisation of the rule-match `Binding` the prior rung cited,
`rewrite.rs:904`). An existential premise licenses no such thing — it is
satisfied by finding (or, failing that, constructing) exactly ONE witness.

**Built**, `domains/inference_generation.py` gained `detect_existential_gaps`
+ `resolve_existential_gap` (entirely new, separate from
`detect_implication_gaps`/`resolve_implication_gap`/`detect_conjunctive_gaps`/
`resolve_conjunctive_gap`, all of which remain byte-unchanged,
source-audit-guarded §7); `domains/propositional_deduction.py` gained
`parse_existential`/`mint_existential_premise` (installs a
`ShapeSignature{kind:"knowledge_existential"}` premise, `signature`
labelled `"holds_some"` — NOT `"holds"`/`"holds_all"` — witnessed:0`).

**Ordering rule adopted, citing CLAUDE.md's own sd-loop precedent directly**:
search (recognise) BEFORE mint — the same Occam ordering the sd loop's own
ladder already enforces elsewhere in the substrate, applied here without
needing the sd loop itself (no `ShapeDecode` call — an honest architectural
choice: a single, fully-specified existential premise has no competing
schema to choose among, so a collapse would be overhead with no
discriminative work to do).

### 4.1 Live demo A — witness search FOUND (context supplies a real witness)

**[RUN]**:

```
smr.ingest_predication(ag, ["is_a", "tux", "bird"])
pd.mint_existential_premise(ag, "Some bird is a penguin")
gaps = ig.detect_existential_gaps(ag)
 -> [{'schema': 'existential_bird_penguin', 'antecedent_attr': 'bird', 'consequent_attr': 'penguin'}]
resolved = ig.resolve_existential_gap(ag, gaps[0])
 -> minted=True, witness_kind='found', entity='tux'
tux: {'bird': 1, 'penguin': 1}      # NO new entity minted
```

### 4.2 Live demo B — witness search MINTS a fresh constant (no context)

**[RUN]**:

```
pd.mint_existential_premise(ag2, "Some bird is a penguin")   # no resident bird entity at all
resolved = ig.resolve_existential_gap(ag2, gaps[0])
 -> minted=True, witness_kind='minted', entity='bird_witness'
bird_witness: {'bird': 1, 'penguin': 1, 'existential_witness': 1}   # classical existential
                                                                      # instantiation: a fresh
                                                                      # constant introduced,
                                                                      # honestly tagged
```

**[RUN]**, idempotency: a second `detect_existential_gaps` call after
resolution returns `[]` (schema marked `witnessed`) — no duplicate witness
minted.

### 4.3 Cross-contamination — the SAME class of bug the conjunction rung
found and fixed, checked here BEFORE it could ship, not after

**[RUN]**, the required test: an unrelated bird entity, offered to the
UNCHANGED MP pipeline, must never pick up `penguin` from the existential
schema:

```
pd.mint_existential_premise(ag3, "Some bird is a penguin")
smr.ingest_predication(ag3, ["is_a", "robin", "bird"])
resolve_implication_gap(...) for robin
 -> minted=True, schema='logical_bird_can_fly', supplies={'attr': 'can_fly'}   # the
    PRE-EXISTING seed schema, unrelated to the existential one
robin: {'bird': 1, 'can_fly': 1}      # NO 'penguin' -- holds_some never visible to holds
```

Also checked against the conjunction pipeline (`detect_conjunctive_gaps`/
`resolve_conjunctive_gap`) — same result, no cross-contamination either
direction. `holds_some` cleanly isolates the pool by construction, matching
the `holds`/`holds_all` precedent.

### 4.4 End to end via the real driver

**[RUN]**:

```
pd.mint_existential_premise(ag, "Some bird is a penguin")
r = ig.read_and_infer(ag, "Tux is a bird.")
before: {'tux': {'bird': 1}}
existential hits: [{'minted': True, 'witness_kind': 'found', 'entity': 'tux'}]
after: {'tux': {'bird': 1, 'can_fly': 1, 'penguin': 1}}
```

**A genuine, unplanned compositional finding**: `tux` also picked up
`can_fly` from the PRE-EXISTING `logical_bird_can_fly` seed schema via the
UNCHANGED MP pipeline in the SAME `read_and_infer` pass — universal (MP),
and existential (witness search) both fired on the same entity, correctly,
with no interference. Not designed for, discovered by running it.

### 4.5 Existential does not get a contrapositive

**[RUN]**: `derive_contrapositive`'s own `kind == "knowledge_logical"` scan
(unchanged) never sees a `knowledge_existential` schema — confirmed no
`existential_bird_penguin_contrapositive` node exists. Correct by
construction, not a special case added for this rung.

---

## 5. RETRACTED AND CORRECTED (post-coordinator re-verification) — the
"environment-dependent Rust binary" claim below was WRONG; the real cause
was a missing gitignored dataset, fixed by symlinking `data/`

**What happened.** The first version of this doc reported, as a genuine
environment finding: *"this worktree's committed native Rust binary cannot
ground a bare capability ('can') consequent via `parse_conditional` at all
— traced to an uncommitted rebuild of `_native.abi3.so` on main."* The
coordinator independently re-ran this rung's own required regression files
(`test_deduction_generalization.py` + `test_deduction_extension.py`) against
a freshly checked-out, unmodified worktree at the same base commit and got
**33/33 PASS**, then ran them in this worktree and got **6 FAILED** — directly
contradicting the "pre-existing, unrelated to this rung" claim above, since
a truly pre-existing/environment-only gap should have failed identically in
BOTH.

**Re-diagnosed from scratch, this time to ground truth, not to a
convenient-looking correlation.** The earlier ".so mismatch" theory was
falsified by a controlled experiment: copying main's EXACT `_native.abi3.so`
bytes (md5-verified identical) plus its `_native.build.json` into a
plain `git worktree add` checkout at `76b8aea` did **NOT** fix the
`None` result — proving the compiled engine was never the cause. Tracing
`pd.parse_conditional(ag, "bird can fly")` step by step
(`decompose_sentence` → `_skeleton_from_words` → `instruction_reading.
is_verb_headed` → `language_faculty_ops.measure_span_features` →
`consumption_quality._pos` → `domains/wiktionary_reference.py:
wiktionary_pos`) found the actual fork: `measure_span_features('bird',
'en')` returns real POS tags (`hp0: 'noun', lp_has_verb: 1.0`) in the
canonical tree and **empty** ones (`hp0: '', lp_has_verb: 0.0`) in every
freshly checked-out worktree — because `wiktionary_reference.py`'s POS
lookup reads a **622MB, gitignored** Wiktionary extract
(`data/wiktionary/en.jsonl.gz`) that a plain `git worktree add` never
copies (gitignored files are not part of the git object graph a worktree
checks out). With that dataset absent, `is_verb_headed` silently degrades
to `False` for every token — not just "can", **every word**, including
"bird" and "fly" — collapsing the whole `_skeleton_from_words` fallback
path, not a quantifier-specific or capability-specific defect at all.

**This is the project's own already-documented gotcha, not a new one.**
CLAUDE.md's "optional-dep note" section states exactly this shape of
problem for a DIFFERENT dataset dependency (`data/` symlinked vs. absent
changes the measured baseline substantially) and treats "`data/`
symlinked" as the correct reference condition. The fix is exactly that
convention, applied here: `ln -s <canonical-tree>/data data` in this
worktree. **[RUN]**, after symlinking:

```
ir.is_verb_headed('bird')  -> True   (was False)
pd.parse_conditional(ag, "bird can fly")
 -> {'antecedent_attr': 'bird', 'consequent_relation': 'can', 'consequent_attr': 'can_fly', ...}
pd.mint_universal_schema(ag, "Every penguin can swim")
 -> minted=True, antecedent_attr='penguin', consequent_attr='can_swim'
```

The capability (`"can"`) form of universal instantiation, wrongly reported
as undemonstrable in this environment, works correctly and is now
demonstrated live (`test_capability_form_universal_instantiation`,
replacing the retracted `test_capability_consequent_parse_is_environment_
dependent_pre_existing_gap`, which asserted a fictional finding and has
been deleted).

**What this means for every earlier "pre-existing failure" claim in §6
(original)**: they were true in the narrow sense that an UNMODIFIED,
identically-`data/`-less baseline worktree reproduced the same failing node
ids (a real, honest paired comparison) — but the comparison itself was
measuring a broken environment on BOTH sides, so "matches baseline" was not
evidence of "no regression" in any useful sense; it was evidence that this
rung's `data/`-less worktree and an unrelated `data/`-less worktree fail
the same way, which is a much weaker and, as the coordinator correctly
judged, insufficient claim. §6 is fully rewritten below with `data/`
symlinked in this worktree, verified together with the coordinator's own
exact two-file command.

**Standing lesson for this arc**: `parse_conditional`'s capability-consequent
form was never broken, in this rung or the prior one — `DEDUCTION_EXTENSION_
RESULTS.md` §2.4's ORIGINAL "capability-consequent text-round-trip gap"
finding should itself be re-examined under a `data/`-symlinked worktree
before being trusted as a real, permanent gap rather than another instance
of this same missing-dataset artifact. Not re-verified here (out of this
rung's scope — flagged for whoever next touches that doc).

---

## 6. Regression (re-verified, `data/` symlinked — the corrected numbers)

**[RUN]**, the coordinator's own exact command, the two REQUIRED regression
files, in this worktree, with `data/` now symlinked to the canonical tree
(`ln -s /home/matt/ozmadev/ocelot/data data`):

```
$ PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
    tests/test_deduction_generalization.py tests/test_deduction_extension.py -q
33 passed in ...s
```

**[RUN]**, all three files together, matching the coordinator's explicit
instruction to verify in ONE invocation:

```
$ PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
    tests/test_deduction_generalization.py tests/test_deduction_extension.py \
    tests/test_quantified_deduction.py -q
56 passed in 4.77s
```

33 pre-existing + 23 new = 56/56, all green, in the same worktree, one
invocation — the coordinator's exact bar.

**[RUN]**, the wider relevant bundle (matching `DEDUCTION_EXTENSION_
RESULTS.md`'s own §6 file list, plus this rung's own new file), now WITH
`data/` symlinked:

```
$ PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
    tests/test_quantified_deduction.py tests/test_deduction_extension.py \
    tests/test_deduction_generalization.py tests/test_reading_collapse.py \
    tests/test_inference_generation.py tests/test_situation_model_wire.py \
    tests/test_goal_licensing.py tests/test_embedded_reading.py -q
129 passed in 13.54s
```

**All 129, zero failures** — up from 87 passed/42 failed before the `data/`
fix (§5): every one of those 42 "pre-existing" failures was the SAME missing-
Wiktionary-dataset artifact, not a genuine pre-existing defect, and disappears
once `data/` is correctly symlinked per the project's own documented
convention.

**[RUN]**, a WIDER sweep still (every other test file in the repo that
imports either touched module — `test_cortices_tick.py`,
`test_crow_gate.py`, `test_goal_driven_analysis.py`,
`test_reasoning_facility_bridge.py`, `test_reform_reingest_migrated.py`,
`test_summit_jabberwocky.py`), also with `data/` symlinked:

```
8 failed, 61 passed in 157.23s
```

(down from 22 failed before the fix). **[RUN]**, all 8 checked against an
independently checked-out, unmodified worktree at the SAME base commit
(`76b8aea`), ALSO with `data/` symlinked (an honest, apples-to-apples
baseline this time, not a `data/`-less one): **7 of the 8 reproduce
identically** —

```
FAILED tests/test_cortices_tick.py::test_crow_report_byte_identical_via_tick
FAILED tests/test_cortices_tick.py::test_ticked_reading_matches_run_reading_flow_report
FAILED tests/test_goal_driven_analysis.py::test_crow_report_is_graph_driven_and_matches_quality
FAILED tests/test_goal_driven_analysis.py::test_mouse_report_is_graph_driven_general
FAILED tests/test_goal_driven_analysis.py::test_reports_are_byte_identical_after_dissolution
FAILED tests/test_goal_driven_analysis.py::test_blackboard_holds_nothing_load_bearing
FAILED tests/test_reform_reingest_migrated.py::test_document_qa_mentions_reform_components
```

— genuinely pre-existing, unrelated to `propositional_deduction.py`/
`inference_generation.py` (none of these test bodies touch the quantifier
extension; they fail on unrelated report-formatting/summarisation
assertions). **The 8th** —
`test_reasoning_facility_bridge.py::test_source_audit_no_facility_internals_edited`
— is explained, not a regression: it runs `git diff --stat main --
domains/propositional_deduction.py domains/inference_generation.py ...` and
asserts it is EMPTY. That test is a scope guard belonging to the
`reasoning-facility-bridge` sibling rung, verifying THAT rung's own work did
not touch these exact files — it will trivially "fail" from ANY worktree
whose deliberate job is to edit `propositional_deduction.py`/
`inference_generation.py` (this rung's entire point), because `main` has
since advanced past `76b8aea` (confirmed: `main` is now several unrelated
sibling merges ahead) and the diff correctly shows THIS rung's own
intentional changes. Confirmed not a real regression: the independently
checked-out, unmodified baseline worktree shows an EMPTY diff against
current `main` for those same files (the intervening sibling merges did not
touch them either) — the test is doing exactly its job, correctly, on a
worktree it was never designed to gate.

`git diff --stat 76b8aea -- domains/ground_reductions.py
domains/comprehend_theorem.py seeds/logic_foundation.json
seeds/logic_propositional_predicate.json seeds/inference_knowledge.json` —
**[RUN]** empty (test-guarded:
`test_ground_reductions_comprehend_theorem_and_original_seed_files_untouched`).
`tests/test_deduction_generalization.py`/`tests/test_deduction_extension.py`
themselves are also guarded untouched
(`test_prior_deduction_test_files_untouched`).

**Note on `data/` and this worktree going forward**: `data/` is now a
symlink (`data -> /home/matt/ozmadev/ocelot/data`) inside this worktree,
committed as a plain symlink file (git tracks the symlink itself, ~30
bytes, not the gitignored contents it points to) — the same convention
CLAUDE.md's optional-dep note already documents as the correct baseline
condition for this repository.

---

## 7. Files touched — matches the prereg's own prediction exactly

```
$ git diff --stat 76b8aea
 domains/inference_generation.py    | 135 +++++++++++++
 domains/propositional_deduction.py | 260 +++++++++++++++++++++++-
 seeds/inference_logical.json       |  13 +-
 3 files changed, 405 insertions(+), 3 deletions(-)
```

(plus this doc, the PREREG doc, and `tests/test_quantified_deduction.py`,
untracked.)

- `domains/propositional_deduction.py`: `_singular_attr`,
  `_quantifier_lexicon`, `_split_leading_quantifier`, `parse_universal`,
  `mint_universal_schema`, `parse_existential`, `mint_existential_premise`
  added. `parse_conditional`/`mint_logical_schema`/`derive_contrapositive`/
  `ensure_contrapositives`: byte-unchanged (source-audit test asserts the
  body of `parse_conditional` through `_negate_attr` carries no
  `quantifier`/`_split_leading_quantifier`/`_singular_attr` trace).
- `domains/inference_generation.py`: `detect_existential_gaps`,
  `resolve_existential_gap`, `_fresh_witness_name` (new); ONE new additive
  key (`"existential"`) in `read_and_infer`'s return dict.
  `detect_implication_gaps`/`resolve_implication_gap`/`decode_gap`/
  `detect_conjunctive_gaps`/`resolve_conjunctive_gap`: byte-unchanged
  (source-audit test asserts none of their bodies contain `holds_some`,
  `existential`, or `witness`).
- `seeds/inference_logical.json`: version 1.2.0 -> 1.3.0; one new
  `QuantifierLexicon` node (local_id 5); description extended documenting
  the v1.3.0 build. No new hand-seeded EXAMPLE schema — both universal and
  existential demos are prose-minted live (a genuine improvement over
  MT/conjunction, which each needed one hand-seeded fallback because their
  own examples fell outside `parse_conditional`'s grammar).

---

## 8. What this does NOT establish

- **Not nested or multi-quantifier.** "Every bird has some friend that
  flies" — nested scope, or more than one quantifier per premise — is not
  attempted; only single, flat, top-level quantified premises are in scope,
  matching the prereg's own explicit sizing.
- **Not negative existentials.** "Some bird cannot fly" (the classic
  textbook counterpart to "All birds can fly") was not attempted, to avoid
  combining the quantifier-strip mechanism with the `not_` negation-prefix
  convention in one build. Both mechanisms are independently proven
  elsewhere in this arc; composing them is plausible but untested.
- **The irregular-plural limitation is real and unfixed** (§1) — `wn.
  morphy('men', 'n')` does not reach `'man'`. The live demo is built on a
  regular plural for this reason, reported rather than silently avoided.
- **A missing-`data/`-symlink build-environment defect was found in this
  worktree, misdiagnosed once as a Rust-binary issue, then correctly
  re-diagnosed and FIXED after coordinator re-verification** (§5) — not an
  open item; recorded here as a standing lesson (re-verify any
  "environment-dependent" claim by isolating the ACTUAL differing artifact
  before reporting it, not by the first plausible-looking correlation) and
  as a flag that `DEDUCTION_EXTENSION_RESULTS.md` §2.4's own
  capability-consequent gap finding should be re-checked under a
  `data/`-symlinked worktree before being trusted as permanent.
- **Existential witness search picks the FIRST qualifying resident entity**,
  not the "best" one by any further criterion — a plain, order-dependent
  scan, matching every other `detect_*` function's own discipline in this
  file, not a ranked selection.
- **The `test_reasoning_facility_bridge.py` scope-guard "failure" is not a
  regression** (§6) — explained precisely, not silently dismissed: that test
  gates a DIFFERENT sibling rung's own promise not to touch these files, and
  necessarily reads as "changed" from any worktree, including this one,
  whose actual job is to change them.
- **Synthetic-proven mechanism ≠ benchmark value, reported per house
  standard**: every number above is a mechanism demonstration (does the
  instantiation fire correctly, does the null/cross-contamination guard
  hold), not a coverage/accuracy claim over any corpus.

---

## 9. GO / NO-GO, per piece, as pre-registered

- **Universal instantiation: GO.** New parse (quantifier-strip + noun
  singularisation), zero pipeline code change (reuses MP/MT unchanged),
  live syllogism demo matches the task's own literal requirement (real
  syllogism, real Concepts, no hand-seeding needed), composes with modus
  tollens for free (confirmed, not assumed), idempotent, both the property
  and capability consequent forms demonstrated live, honest residual named
  (irregular plurals).
- **Existential instantiation: GO.** Real, new, small witness-search
  machinery (materially distinct from universal's breadth-apply, per the
  prereg's own framing, confirmed live), both required live cases
  demonstrated (search-found, search-mint), cross-contamination checked
  and closed BEFORE shipping (not found-then-fixed after, unlike the
  conjunction rung's own history — this time verified clean from the
  start), idempotent, no contrapositive (correct by construction).
- **Nested/multi-quantifier premises, negative existentials:
  NOT-ATTEMPTED-BY-DESIGN**, named follow-ons, matching the prereg's own
  scoping.
- **The `data/`-symlink build-environment defect: FOUND, MISDIAGNOSED
  ONCE, THEN CORRECTLY FIXED** (§5) — not a residual; recorded as a standing
  lesson for the arc.

**Worktree:** `/home/matt/ozmadev/ocelot-worktrees/quantified-deduction`
**Branch:** `quantified-deduction`
**Base:** `main` @ `76b8aea`
**`data/`**: symlinked to the canonical tree (`data -> /home/matt/ozmadev/ocelot/data`),
the project's documented convention — required for an accurate baseline in
this worktree, per §5.

Not merged into `main` (per instructions — the caller merges).
