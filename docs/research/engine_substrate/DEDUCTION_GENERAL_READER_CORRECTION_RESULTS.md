# DEDUCTION GENERALIZATION — GENERAL-READER CORRECTION — RESULTS

**Status: LANDED. GO.** Corrects `docs/research/engine_substrate/
DEDUCTION_GENERALIZATION_PREREG.md`/`_RESULTS.md` (commit `2f3e872`, merged
`a20e334`). Design in `DEDUCTION_GENERAL_READER_CORRECTION_PREREG.md` (read
first). Built in an isolated worktree, branch
`deduction-general-reader-correction`, off `main` @ `a20e334`.

**Confidence convention**, matching the original rung: claims verified by
reading source carry `file:line`. Claims backed by an actual run are marked
**[RUN]** with real output.

---

## 0. One-line answer

**The duplication the creator flagged was real, and the fix is landed:**
`domains/propositional_deduction.py`'s hand-rolled 8-form token-pattern
mini-grammar (`_FORMS`/`_tokenize`/`_match_pattern`) is DELETED. `parse_
conditional` now ingests every conditional statement through the GENERAL
reading pipeline (`reading_collapse.decompose_sentence` + `.read_clause`) and
reads off the antecedent/consequent shape from the predications grounding
already produces. **A genuine adapter WAS required** (pre-registered as an
open question, not assumed): the shared `conditional` construction's own
`implies(...)` predication — the one `tests/test_reading_collapse.py:57`
proves live — turns out to be too coarse for this module's specific need,
measured directly (§2). The adapter that closes that gap reuses TWO existing
general mechanisms (`decompose_sentence`'s clause-splitter, `read_clause`'s
per-clause grounding) and adds no grammar of its own. All four original demo
outcomes reproduce byte-identically; `test_reading_collapse.py` is
git-diff-confirmed untouched; 54/54 relevant tests pass.

---

## 1. The duplication, confirmed exactly as charged

**[RUN]**, `seeds/reading_constructions.json`, `local_id: 48`:

```json
{
  "name": "conditional", "kind": "construction", "predication": "implies",
  "signature": "[[\"IF\"],[\"THEN\"]]",
  "ground_template": "{\"pred\": \"implies\", \"mode\": \"pair\"}"
}
```

**[RUN]**, the exact scenario in `tests/test_reading_collapse.py:57`, run
standalone, unrelated to this rung's own code:

```
r = rc.read_clause(agent, "if it rains then the ground is wet")
r["construction"]   -> "conditional"
r["predications"]   -> [["implies", "it_rains", "ground"]]
```

This construction is decoded by `domains/reading_collapse.py` through the
exact same `ShapeDecode`/`_winner` mechanism as every other construction
(`definitional`, `attributive`, `event`, `comparative_*`, ...) —
`reading_collapse.py:1233-1246` (`_winner`), `:1334-1395` (`_ground`, the ONE
mode-dispatched grounding routine every construction shares). It existed
and passed before this session's deduction-generalization rung ever touched
the tree.

`domains/propositional_deduction.py`'s original docstring (read in full
before this correction) discusses `comprehend_theorem.py` at length — why
its group-theory-bound `ImplicationClause` semantics don't reach an
arbitrary graph fact — and **never once mentions `reading_collapse.py`**.
The verdict stands: the duplication was real, not a false alarm.

---

## 2. The open question, resolved by running the code — a genuine adapter was needed

The correction directive explicitly left open whether the shared
`conditional` construction's own `implies(...)` predication could feed
`mint_logical_schema` directly, or whether a "nontrivial adapter" was
required. **Measured, not assumed:**

**[RUN]**, the shared `conditional` construction on every surface form this
module actually needs to mint from:

| statement | `conditional` construction's own `implies(...)` |
|---|---|
| `"if it rains then the ground is wet"` (the tested case) | `implies(it_rains, ground)` — drops the consequent's own predicate ("wet") entirely |
| `"if X is a fish, X can swim"` | `implies(x, fish_x_can_swim)` — antecedent is just the bare subject "x"; consequent is a GARBLED BLOB fusing "fish X can swim" into one concept |
| `"if X is a mammal, X is warm blooded"` | decode doesn't even pick `conditional` — it picks `attributive`: `has_property(x, mammal_x)`, and drops "warm blooded" entirely |
| `"if it is a fish then it can swim"` | `implies(it, fish)` — drops the ENTIRE consequent clause |

Root cause, read from source: the construction's `ground_template` mode is
`"pair"` (`reading_collapse.py:1382-1384`), which unconditionally reads only
`roles[0]`/`roles[1]` regardless of how many marker-delimited roles the
clause actually produced. For "if it rains then the ground is wet" the
marker skeleton is `[IF, THEN, COP]` with 3 roles (`['it rains', 'ground',
'wet']`); `"pair"` mode happens to grab `(antecedent-clause, consequent-
subject)` and silently drops `roles[2]` (the consequent's own predicate).
For "if X is a fish, X can swim" there is no `THEN` marker at all (only
`[IF, COP]`), so the clause-final complement role absorbs BOTH the
antecedent's complement AND the entire consequent clause into one blob
(`"fish x can swim"`), because nothing bounds the copula's role capture
before the sentence ends.

**Verdict:** this is a real, load-bearing gap in the SHARED `conditional`
construction — not a defect introduced by this rung, and NOT something this
rung fixes (that `ground_template` is shared by the byte-parity-tested
battery in `tests/test_reading_collapse.py`; touching it risks that test and
is out of this correction's scope). A genuine adapter was required, exactly
as the correction directive's point 4 anticipated as a live possibility.

---

## 3. The adapter that was built — reusing two EXISTING general mechanisms, adding no grammar

**[RUN]**, the mechanism that DOES cleanly reach this module's need, with
zero bespoke grammar:

```
rc.decompose_sentence(agent, "if X is a bird, X can fly")["clauses"]
  -> [['x', 'is', 'a', 'bird'], ['x', 'can', 'fly']]
```

`decompose_sentence` (`reading_collapse.py:3499-3577`) is the EXISTING
general multi-clause splitter used for every other multi-clause sentence in
the corpus (relative clauses, coordination, reported speech). Its own
`_segment_into_clauses` (`reading_collapse.py:3333-3465`) already treats
`IF` as a `_CLAUSE_OPENERS` marker and a comma as a clause boundary —
untouched, pre-existing, general-purpose. It correctly splits the antecedent
clause from the consequent clause at the comma.

Each half is then re-grounded independently via the plain `rc.read_clause`
(fragment mode, `write=False`) — **not** `decompose_sentence`'s own
`_read_clause_clean`, which was tried first and found to DROP the
consequent clause: `_read_clause_clean` (`reading_collapse.py:3059-3084`)
routes a non-copular clause through `_event_predication_graph` with
`intransitive_ok=False` (the default), and "X can fly" is bare-intransitive
(no object) — **[RUN]** confirmed directly: `_event_predication_graph(agent,
['x','can','fly'], lex)` returns `[]`. Plain `read_clause`, by contrast,
grounds "X can fly" fine via its own event-construction path (`skeleton:
[['VERB']]`, `predications: [['can', 'x', 'fly']]`) — **[RUN]** confirmed —
because its role-splitting (`_skeleton_from_words`) is looser than
`_event_predication_graph`'s transitivity requirement. This substitution
(plain `read_clause` in place of `_read_clause_clean`) is the one place this
correction chose a DIFFERENT existing call than the first one tried, and it
is recorded here as a real design decision, not a silent swap.

For the bare-universal form ("a fish can swim", no `if`), `decompose_
sentence` reports a single, unsplit clause (`multi_clause: False`) — no
split needed at all: a SINGLE `read_clause` call on the whole statement
already grounds subject + relation + consequent as one predication
(`event`: `[can, fish, swim]`; `definitional`: `[is_a, mammal,
warm_blooded]`). **[RUN]** confirmed for both consequent shapes.

**The resulting adapter** (`domains/propositional_deduction.py`,
`parse_conditional` + two small helpers, `_norm_attr`/`_relation_and_attr`):
try `decompose_sentence`; if it splits into exactly 2 clauses, ground each
independently via `read_clause` and require the antecedent clause's own
predication to be `is_a` and the consequent clause's own predication to be
`is_a`/`can`; else ground the whole statement in one `read_clause` call and
apply the same `is_a`/`can` requirement to its single predication. Neither
branch tokenises, pattern-matches, or classifies raw text — both branches
call ONLY the general reading pipeline's own top-level functions and read
off the predicate NAME (`is_a` vs `can`) their decode already chose. The
only string operation left in the module is `_norm_attr`: a single
`str.replace("-", "_")` mechanical normalisation (a hyphenated token like
"warm-blooded" survives the reader's own tokenizer unsplit, so it needed one
character substitution to match the underscore-joining convention every
other multi-word role span already gets from `reading_collapse._norm`) —
not a grammar, not a decision.

**[RUN]**, all four battery cases through the corrected `parse_conditional`:

```
'if X is a bird, X can fly'
  -> {'antecedent_attr': 'bird', 'consequent_relation': 'can',
      'consequent_attr': 'can_fly', 'form': 'conditional_split'}
'a fish can swim'
  -> {'antecedent_attr': 'fish', 'consequent_relation': 'can',
      'consequent_attr': 'can_swim', 'form': 'bare_universal'}
'a mammal is warm-blooded'
  -> {'antecedent_attr': 'mammal', 'consequent_relation': 'is',
      'consequent_attr': 'warm_blooded', 'form': 'bare_universal'}
'gibberish that matches nothing at all'  -> None
''                                        -> None
```

All five match the pre-registered/original scope exactly (2 conditional
shapes, `can`/`is` consequent relations, honest residual on unparseable
prose and empty input).

---

## 4. Named residual, honestly: the "if X is a P **then** X can/is Q" form

The ORIGINAL bespoke `_FORMS` list never actually supported this form either
(all 8 patterns required a literal comma, not "then") — so this is not a
scope regression. Recorded because it was investigated directly:
`decompose_sentence`'s `_segment_into_clauses` deliberately leaves a
GOVERNED `then` (one following an `IF`) in place as part of the SAME clause
(`reading_collapse.py:3340-3352`, "a governed 'then' is left in place... it
stays in the clause's marker skeleton for the held conditional construction
to decode") rather than splitting on it — so `decompose_sentence` reports
`multi_clause: False` for "if it is a fish then it can swim", and the
single-clause fallback then hits the SAME lossy shared `conditional`
construction §2 measured (dropping the consequent). **[RUN]** confirmed:
`pd.parse_conditional(agent, "if it is a fish then it can swim")` returns
`None` — an honest residual, not a silent wrong answer. Extending coverage
to the "then" form would require either widening `_segment_into_clauses`'s
own governed-`then` handling (a shared function, out of this correction's
scope) or a dedicated adapter branch reading the `implies` predication's
raw `roles` list instead of its post-grounding predication — not attempted
here, matching the original rung's own scope discipline of naming, not
silently absorbing, adjacent forms.

---

## 5. Live demonstration through the corrected path

**[RUN]**, fresh agent per case, `boot_core()`:

```
=== STEP 0: confirm the general reader ALREADY produces implies() ===
construction: conditional
predications: [['implies', 'it_rains', 'ground']]
matches tests/test_reading_collapse.py:57 exactly: True

=== STEP 1: parse_conditional now ingests via the GENERAL reading path ===
parsed: {'antecedent_attr': 'bird', 'consequent_relation': 'can',
         'consequent_attr': 'can_fly', 'form': 'conditional_split', ...}

=== bird/fly (hand-seeded implication) ===
before: {'bird': 1}
after : {'bird': 1, 'can_fly': 1}

=== fish/swim (implication PARSED from prose, corrected GENERAL-READER path) ===
mint: True logical_fish_can_swim   form= conditional_split
before: {'fish': 1}
after : {'fish': 1, 'can_swim': 1}

=== dog (discriminative null -- no covering implication) ===
after : {'dog': 1}
any minted: False

=== regression spot-check: glass (empirical pipeline, unmodified) ===
{'bird': 1, 'fell': 1, 'location': 'the floor', 'holder': '(nobody)',
 'on_floor': 1, 'on_floor_inferred': 1, 'fragile': 1, 'broken': 1,
 'broken_inferred': 1, 'worthless': 1, 'worthless_inferred': 1,
 'blocked_gap': 1, 'can_fly': 1}
```

Every outcome is byte-identical to the original (uncorrected) landing's own
`§6` transcript. What changed is entirely UNDER `mint_logical_schema` — the
KNOWLEDGE now flows through the general reading path instead of a bespoke
grammar; the derivation mechanism (`inference_generation.py`'s gap-detect ->
`ShapeDecode` collapse -> mint -> re-run-fixpoint) is completely unmodified.

---

## 6. What stayed, unchanged, as pre-registered

- The `ShapeSignature{kind:"knowledge_logical"}` schema shape (antecedent
  `signature`/consequent `supplies`, mirroring `ImplicationClause`) —
  untouched.
- Reuse of `situation_model_reader.ingest_predication` for the mint —
  untouched (still the identical call `resolve_precondition_gap` makes).
- Reuse of `reading_collapse._winner`'s best-fit selection for which
  `knowledge_logical` schema wins a gap — untouched.
- `domains/inference_generation.py`'s `detect_implication_gaps`/
  `resolve_implication_gap`/gap-detection wiring — **[RUN]** git-diff-
  confirmed zero change from `a20e334` (it never imported
  `propositional_deduction` at all — only a comment references the module
  name, `inference_generation.py:923`).
- `domains/ground_reductions.py`, `domains/comprehend_theorem.py`, the
  inert `logic_foundation.json`/`logic_propositional_predicate.json`,
  `seeds/inference_knowledge.json` — **[RUN]** git-diff-confirmed zero
  change from `b124038` (the same guard test the original rung shipped,
  re-run here unmodified).
- `tests/test_reading_collapse.py` — **[RUN]**:

```
$ git diff --stat b124038 -- tests/test_reading_collapse.py
(empty output)
```

Zero diff — consumed via `rc.read_clause`/`rc.decompose_sentence`, never
edited.

---

## 7. What changed

```
$ git diff --stat a20e334
 domains/propositional_deduction.py                                  | 332 +++++++++++++++++----------------
 seeds/inference_logical.json                                        |   2 +-
 tests/test_deduction_generalization.py                              |  47 ++++-
 3 files changed, 217 insertions(+), 164 deletions(-)
```

(plus these two docs, untracked.)

- **`domains/propositional_deduction.py`**: `parse_conditional` rewritten to
  take `agent` (it now needs graph access — the general reading pipeline is
  graph-native) and ingest via `reading_collapse.decompose_sentence`/
  `.read_clause` instead of the deleted `_FORMS`/`_tokenize`/`_match_pattern`
  mini-grammar. `mint_logical_schema` unchanged except passing `agent` through
  to `parse_conditional`.
- **`seeds/inference_logical.json`**: one description-text sentence updated
  to state the corrected mechanism (no schema/data change — `git diff` on
  the `nodes`/`edges`/`rules` arrays is empty; only the `description` prose
  field changed).
- **`tests/test_deduction_generalization.py`**: the 4 standalone PARSE tests
  updated to call `pd.parse_conditional(_fresh(), statement)` (the new
  required `agent` argument) instead of `pd.parse_conditional(statement)`;
  one new test added
  (`test_general_reader_conditional_construction_already_produces_implies`)
  that independently proves, inside this rung's own test file, that the
  general `conditional` construction already produces `implies(...)`,
  byte-matching `tests/test_reading_collapse.py:57`. Every other test
  (headline/mint/chaining/discriminative/source-audit/scope-guard/
  non-interference) is UNCHANGED — the correction only touched the
  parse-layer plumbing, not the derivation outcomes those tests check.

---

## 8. Regression

**[RUN]**:

```
$ PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
    tests/test_deduction_generalization.py -p no:randomly -q
...............                                                          [100%]
15 passed in 2.93s

$ PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
    tests/test_reading_collapse.py -p no:randomly -q
...................                                                       [100%]
19 passed in 3.87s

$ PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
    tests/test_inference_generation.py tests/test_deduction_generalization.py \
    tests/test_reading_collapse.py tests/test_situation_model_wire.py \
    tests/test_goal_licensing.py tests/test_embedded_reading.py -p no:randomly -q
........................................................................ [ 81%]
................                                                          [100%]
88 passed in 11.67s
```

15/15 (14 original + 1 new proof test), 19/19 `test_reading_collapse.py`
(byte-identical, zero diff), 88/88 across the full relevant bundle
(`test_inference_generation` 20 + `test_deduction_generalization` 15 +
`test_reading_collapse` 19 + `test_situation_model_wire` 9 +
`test_goal_licensing`+`test_embedded_reading` 25).

No other file in the tree referenced the deleted `_FORMS`/`_tokenize`/
`_match_pattern` internals — **[RUN]** grep-confirmed; the only other
`parse_conditional` symbol in the codebase lives in
`domains/concept_promotion_rules.py`, an unrelated function in a different
module (different signature, different purpose — theorem-definition
`when`/`if` clause extraction for concept promotion, not this module's
implication mining), never calling into or called by
`domains/propositional_deduction.py`.

---

## 9. GO / NO-GO

**GO.**

**Confirmed:** the duplication was real (§1); the general `conditional`
construction demonstrably already produces `implies(...)`, proven both by
re-running `tests/test_reading_collapse.py:57`'s own scenario and by a new
test inside this rung's own suite (§1, §5).

**Confirmed, and reported precisely as the task required:** the shared
`conditional` construction's own `implies(...)` predication does NOT
directly supply this module's needed shape — its `"pair"` ground_template
drops the consequent's own predicate on every phrasing this module mints
from (§2, measured not assumed). The smallest correct adapter reuses TWO
existing general mechanisms (`decompose_sentence`'s clause-splitter,
`read_clause`'s per-clause grounding) and adds zero grammar of its own (§3).

**Replaced:** `parse_conditional`'s 8-form hand-rolled token-pattern
mini-grammar — fully deleted, not kept as a fallback.

**Unchanged in outcome:** all four original demo scenarios (§5), the
`knowledge_logical` schema shape, the mint primitive, the gap-detection
wiring, `ground_reductions.py`, `comprehend_theorem.py`, the inert logic
seeds, `seeds/inference_knowledge.json`, and `tests/test_reading_collapse.py`
(§6 — all git-diff-confirmed zero change).

**Named, not built:** the "if X is a P then X can/is Q" (no comma) form
remains an honest residual, same as in the original (uncorrected) rung —
not a regression, and precisely why (§4).

**Worktree:** `/home/matt/ozmadev/ocelot-worktrees/deduction-general-reader-correction`
**Branch:** `deduction-general-reader-correction`
**Base:** `main` @ `a20e334`

Not merged into `main` (per instructions — the caller merges).
