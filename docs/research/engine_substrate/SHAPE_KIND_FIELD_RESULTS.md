# SHAPE-BEARING NODE `kind` FIELD — DESIGN SPIKE, RESULTS

Prereg: `SHAPE_KIND_FIELD_PREREG.md`, same commit series, base `main` at `4bb1794`.
Worktree `/home/matt/ozmadev/ocelot-worktrees/shape-kind-field-spike`, branch
`shape-kind-field-spike`.

**Verdict, up front: NO-GO on building a `kind` field or a kind-guard on
`AntiUnifyWitness`/`Covers`/`AntiUnify`, in the specific form the charter registered.**
Both predictions in the prereg (§2, P2a and P2b) confirmed exactly as registered, and
together they refute H2 in the form it was posed: the one live site that genuinely
crosses H1's kind categories already produces a clean accidental refusal, and the one
live, measured nonsense match is same-kind — a `kind` tag could not have prevented it.
This is a complete, valuable null, not an unmeasured shrug: it localises the cause
(row-arity mismatch already gates the cross-kind case; positional/axis-anchoring is the
real defect in the same-kind case) and names the correct next lever, which is not this
one.

---

## 1. H1 — the five-way kind inventory: CONFIRMED, with one real complication found

### 1.1 The five categories hold up under direct source reading

| kind | node type(s) | evidence |
|---|---|---|
| MAP | `DimensionGenerator` | `struct Generator { name, kind, coord_dims, params, ... }`, `shape_decode.rs:389-431`; consumed by `apply_generator_once`/`DimInfer`, never by `Covers` |
| MAP | `Transform{dim,delta}` | per-observation delta along one dimension (`CLAUDE.md` "Transformation = quantum change..." section); consumed by `Substitute`-style application, not recognised upward |
| MAP | `GammaProduction` | `SHAPE_TYPE_VOCABULARY_SPIKE.md` §5.4: *"a constructor, consumed downward via `Substitute`... the interface above is written for recognisers consumed upward via `Covers`"* |
| OBJECT / IDENTITY | `Concept` | `name`, `category`, `definition` only; `ANALOGICAL_THINKING_SHAPE_MATH_RESULTS.md` §3.1 (cited in the spike, §5.4): *"98.9% of the population has no edge to consult... a no-op wearing the costume of a fix"* — no native relational signature of its own |
| RELATION-PATTERN | `ShapeSignature`, `MetaShape`, `ShapePrinciple` | `signature` = a list of `[predicate, value]`/relation tuples, read upward by `Covers`/`AntiUnify` (`META_SHAPE_FIRST_CLASS_RESULTS.md`, `meta_shape.py:60-79`) |
| CODEBOOK | `CapabilityAxis` | grows via `sd_mint_quantum`; identity is a derived key over the covered predicate SET (`SHAPE_AUDIT_PATTERN_C_FIXES_RESULTS.md` §1), not a static signature — this is the property that makes it structurally different from a RELATION-PATTERN entry even though both carry a `signature`-ish attr |
| PROCEDURE | `Mechanism` | `steps` = an ordered TOKEN LIST (`["quantize","FIELD","into","UNIT"]`), transferred via `TransferDecode`, never compared via `Covers` — `CROSS_DOMAIN_SHAPE_SPIKE.md` §8 item 3: *"A `Mechanism`'s `steps` are token lists... not signatures. This is a procedure-transfer mechanism wearing a shape-transfer name"* |

I found no shape-bearing node type (grep across `runners/dsl/src/*.rs` for
`Covers`/`AntiUnify`/`StructSim`/`FixedCount` call sites, plus a read of every type
`SHAPE_TYPE_VOCABULARY_SPIKE.md` §3.1's table names) that straddles two of the five in
a way that breaks the split. **The hypothesis holds as stated.** `Concept`'s zero-
signature status (an OBJECT with no shape at all) is the sharpest evidence it is a real
category and not just a label: it is the one type §5.4 of the vocabulary spike already
refused to give a shared interface to, for exactly the reason H1 predicts.

### 1.2 The complication: `"kind"` is ALREADY three different, incompatible things in this tree

This was not part of the charter's five-way hypothesis and is the most concrete new
fact this rung adds. Read directly from source and seed data:

1. **`ShapeSignature.kind`** — per `SHAPE_TYPE_VOCABULARY_SPIKE.md` §3.4(a)'s corrected
   addendum (citing `CODEBOOK_PARTITION_CONSOLIDATION_RESULTS.md`): *"`kind` does not
   partition a decode pool and never has... 10 of 14 subtypes carry a `kind` attr that
   merely RESTATES the type name... and that nothing filters on."* Mostly inert.
2. **`ShapeSignature.kind` in `seeds/math_capability_shapes.json`** (a DIFFERENT
   population of `ShapeSignature` nodes than (1), same attr name) — here `kind` DOES do
   real, consequential work: `"math"` / `"faculty"` / `"authored"` are read by
   `_load_shape_signatures` (`reflective_faculty.py:7045-7064`) and used as a live
   filter in `_run_math_bridge` (`:7426-7427`, `v[0] == "math"` / `"faculty"`) and in
   `learn_term_for_concern` (`:1126`, `v[0] == "faculty"`). **This is a working
   precedent that a `kind`-shaped filter changes a real decision** — just not the
   category-of-shape-bearing-thing meaning the charter is asking about; it is a
   DOMAIN label (which body of knowledge a signature belongs to), read by exactly the
   code that needs it.
3. **`DimensionGenerator.kind`** (`shape_decode.rs:389-396`) — an ALGORITHM DISPATCH
   key (`"linear"`/`"rotation90"`/`"reflection"`/`"scale2"`/`"modular"`), selecting
   which built-in coordinate-map primitive `apply_generator_once` runs. A MAP-kind
   node's OWN internal variant selector — nothing to do with H1's MAP/OBJECT/...
   categorisation at all.

**Consequence for any future build:** a new field carrying H1's five-way semantics
must NOT be named `kind` on `ShapeSignature` or `DimensionGenerator` — that name is
already claimed, twice, for two different real purposes on exactly the node types H1
would want to tag. `SHAPE_TYPE_VOCABULARY_SPIKE.md` §5.3's proposed field name for the
adjacent `scope` axis (`observation` vs `world_fact`) sets the right precedent: a
new axis gets a new name (`category`, or reusing the spike's own unclaimed
`ShapeRole.role` slot) rather than overloading `kind` a third time. This alone is a
sufficient reason the "obvious" field name in the charter's own phrasing ("the kind
field") needs renaming before any build, independent of the GO/NO-GO below.

---

## 2. H2 — the load-bearing question: does a `kind` field change any decision?

### 2.1 P2a — the one live cross-kind site: CONFIRMED, and it is a clean accidental refusal

`learn_term_for_concern` (`domains/reflective_faculty.py:1074-1158`) is the one place
in the tree I found where a genuinely CODEBOOK-kind operand (a `CapabilityAxis`'s
`residual_predicates`, reshaped `[[p] for p in preds]` at `:1110`) can reach the shape
matcher against a genuinely RELATION-PATTERN-kind operand (a seeded
`ShapeSignature{kind:'faculty'}`, `:1126`, `:1131`), via `_shared_shape`
(`:7137-7154`), with **no kind check anywhere on the path**.

Measured (`scripts/shape_kind_probe.py`, run in this worktree, native evaluator, no
agent boot):

```
cap_axis_sig=[['scan'], ['gate'], ['focus'], ['route']]
faculty='residual_recurrence' sig=[['build', 'NEW', 'from', 'PRIOR'], ['refers', 'NEW', 'to', 'SELF'], ['bound', 'SELF', 'by', 'UNIT'], ['base', 'STOP']]
-> AntiUnify result=(('·?·',), ('·?·',), ('·?·',), ('·?·',))
-> fixed (shared leaves) = 0
```

Row-arity census over every seeded `kind:'faculty'` `ShapeSignature`
(`seeds/math_capability_shapes.json`, 11 nodes): **row lengths are 2, 3, or 4, never
1.** A `CapabilityAxis`-residual row (`[[p]]`) is always length 1. `term.rs`'s
`Tuple`/`List` anti-unify arm requires equal length per pair or collapses that pair to
WILD (`term.rs:3367-3375`, per `SHAPE_TYPE_VOCABULARY_SPIKE.md` §3.3's table) — so
**every row pair here collapses to WILD, and `fixed == 0` for every real pairing on
current seed data.** P2a confirmed exactly as predicted.

**This is not a designed guard.** It is a side effect of each kind's own row schema
(CapabilityAxis residuals happen to be bare predicate names; faculty `ShapeSignature`
rows happen to be RelationCue-vocabulary tuples of length ≥2) — an accident that
currently produces the right behaviour, not a rule anyone wrote down. A `kind` field
would formalise this refusal but would not CHANGE it, because the refusal already
happens. This matches the charter's own permitted NO-GO condition: *"today's
`where`-guards already implicitly prevent it... via ... predicate matching."*

### 2.2 P2b — a real, live, MEASURED nonsense match — but it is SAME-kind

Searching for where H2 might still hold turned up a genuine defect, just not the one
predicted. `author_signature` (`reflective_faculty.py:7112-7134`) builds a `Concept`'s
signature by scanning `seeds/relation_vocabulary.json`'s `RelationCue` list in its
SEED-DECLARATION order and appending each cue's relation tuple whose keyword fires in
the concept's definition text — unlike `analogical_thinking._concept_shape_vector`,
which deliberately sorts onto a FIXED vocabulary axis with an `_ABSENT` filler
specifically so position is meaningful (`analogical_thinking.py:362-368`).
`author_signature`'s output has no such anchor: two unrelated concepts' fired-cue
relations can land at the same list index purely by which keywords happened to match,
and the `RelationCue` vocabulary reuses placeholder tokens (`"NEW"`, `"SELF"`,
`"PART"`, `"to"`, `"by"`, ...) across otherwise-unrelated relations.

Measured (same probe, `scripts/shape_kind_probe.py`):

```
concept_a (self-reference/recursion cues) = [['refers', 'NEW', 'to', 'SELF'], ['build', 'NEW', 'from', 'PRIOR'], ['base', 'STOP']]
concept_b (symmetry, unrelated)            = [['map', 'PART', 'to', 'PART'], ['invariant', 'PART', 'under', 'TRANSFORM'], ['repeat', 'PART']]
-> AntiUnify result=((('·?·',), ('·?·',), 'to', ('·?·',)), (('·?·',), ('·?·',), ('·?·',), ('·?·',)), (('·?·',), ('·?·',)))
-> fixed (shared leaves) = 1
```

Two `Concept`s with NO genuine shared structure — one is about self-referential
recursion (`refers NEW to SELF`), the other about geometric symmetry (`map PART to
PART`) — register a `fixed=1` "shared leaf" purely because both happen to place the
placeholder word `"to"` at row-index 0, column-index 2. This is a real, reproducible
nonsense match, and it is CONSEQUENTIAL: it feeds `learn_term_for_concern`'s and
`_run_math_bridge`'s `Argmax` picks of which term-family/faculty to connect a concept
to (`reflective_faculty.py:1134-1157`, `:7454-7473`) — a decision the agent actually
acts on.

**But both operands here are RELATION-PATTERN-kind under H1.** `author_signature`'s
output and a seeded `ShapeSignature`'s `signature` are the exact same category of
thing — a relation-tuple list. **A `kind` tag on each node would read `RELATION-
PATTERN` on both sides, pass any conceivable kind guard unchanged, and the spurious
match would still occur.** P2b confirms the prediction that the live defect found is
orthogonal to kind, not caused by it.

### 2.3 The decision rule, applied

The prereg's registered rule: *if P2a confirms and P2b confirms, H2 is refuted in the
form registered, and that is NO-GO on the kind-guard slice.* Both confirmed exactly as
predicted. **NO-GO**, per the prereg's own bar, not a post-hoc rationalisation.

### 2.4 Corroborating precedent at the sd-loop/Γ layer (not re-measured, cited)

The same question at a different grain was already answered, in this arc, by
`CODEBOOK_PARTITION_CONSOLIDATION_RESULTS.md` (quoted in
`SHAPE_TYPE_VOCABULARY_SPIKE.md` §3.4(a)'s addendum): *"the node type is the only
mechanism that partitions a pool"* — `ShapeDecode`'s `codebook_scope`/`exclude`
filters are keyed on node NAME within a `codebook_type`-selected node TYPE, and every
`msg_recognize`-style rule (`seeds/meta_shape_growth.json:56`,
`:177`) restricts its `match_type` to one graph node type before any `Covers`/
`AntiUnify` runs. **At the Rust/rule layer, node type already IS the kind guard** —
consistent with §2.1's finding that the one place a guard is genuinely missing
(Python-orchestrated `_shared_shape` call sites) happens to be accidentally safe on
today's data rather than because anyone designed it to be.

---

## 3. The DOOR_SWITCH precedent — thematic resonance confirmed, mechanism transfer NOT confirmed

`ozmalabs/internal/research/experiments/gamma-substrate/DOOR_SWITCH_RECOGNITION_RESULTS.md`
is a real, built, gated precedent (`tests/test_pattern_recognition_migrated.py`, 10/10,
in that repo) for a two-tier recognizer: COARSE family match (integer L1 distance of a
region's `[geometry_level, texture_level]` descriptor from a held prototype, cleared
against a threshold) before FINE label match (nearest-prototype by the same integer L1
distance, tighter threshold). The owner steer that shaped it, verbatim: *"spotting a
different type of thing is easy; naming it a switch needs a closer look."*

**The STRATEGY transfers; the MECHANISM does not, and the two should not be
conflated.** What would transfer to graph-node kinds is the STRATEGY — a cheap check
before an expensive one, "is this even the same category of thing" gating "does it
match this specific pattern." A `kind` field guarding `AntiUnifyWitness`/`Covers`
would realise exactly that strategy: symbolic equality on `kind` (MAP vs OBJECT vs...)
as the coarse gate, the existing `Covers`/`AntiUnify` structural comparison as the fine
match. **But DOOR_SWITCH's actual mechanism is a continuous, quantized DISTANCE metric
over a descriptor space** (integer L1 norm, a threshold, a tier ladder) — there is no
analogous distance space over graph-node KINDS (MAP is not "closer to" or "further
from" OBJECT in any metric sense the tree defines); a kind check is a flat symbolic
equality test, structurally closer to Γ's `knows_node_type` check
(`checker.rs:66-85`, already built, already the working "different type of thing"
gate for EDGES) than to DOOR_SWITCH's tiered descriptor classifier. **Verdict: same
SHAPE one level up in the loose sense of "coarse-before-fine is a good strategy,"
confirmed; NOT the same mechanism, and this document does not claim it is** — forcing
the connection past the strategy level, as the task explicitly warned against, would
overclaim.

---

## 4. What was built

**Nothing landed.** Per the registered GO/NO-GO bar (§4 of the prereg) and the
confirmed result above, no `kind` field, no guard, and no new Rust or seed data were
added to the substrate. The only artefacts in this worktree are:

- `docs/research/engine_substrate/SHAPE_KIND_FIELD_PREREG.md` (this rung's prereg)
- `docs/research/engine_substrate/SHAPE_KIND_FIELD_RESULTS.md` (this file)
- `scripts/shape_kind_probe.py` — the read-only measurement script for §2's decisive
  test. It touches no graph, boots no agent, and is not imported by anything. Kept
  (not reverted) because it is the reproduction artefact for a result this document
  reports, matching the standing convention of every other spike in this arc
  (`scripts/dimgen_program_ir_gate.py`, `scripts/build_pattern_recognition_seed.py`,
  etc. are all kept alongside their RESULTS docs).

No shared file was touched (`git status --short` shows only the three new files
below), so no regression suite is owed beyond the light sanity check actually run:
`tests/test_analogical_shape_math_migrated.py` + `tests/test_meta_shape_arity_migrated.py`,
**21 passed, 0 failed**, unchanged before/after because nothing shared changed.

```
$ git status --short
?? docs/research/engine_substrate/SHAPE_KIND_FIELD_PREREG.md
?? docs/research/engine_substrate/SHAPE_KIND_FIELD_RESULTS.md
?? scripts/shape_kind_probe.py
```

---

## 5. What this document does NOT establish

1. **It does not establish that a `kind` field would never be useful anywhere in this
   tree.** It establishes that the ONE call-site family the charter's own suggested
   test pointed at (`AntiUnifyWitness`/`Covers`/`AntiUnify` cross-kind comparison in
   `reflective_faculty.py`/`analogical_thinking.py`) does not currently produce a
   wrong result a kind tag would fix. A different call site, not audited here, might.
2. **The P2b defect (positional/axis-anchoring in `author_signature`) is reported, not
   fixed.** It is real, measured, and consequential (§2.2), but fixing it is a
   different rung with a different fix shape (give `author_signature` a fixed axis
   layout, the way `_concept_shape_vector` already has one) — explicitly out of scope
   here, and not to be confused with the `kind`-field question this rung was chartered
   to answer.
3. **§2.1's "clean refusal" is a property of TODAY's seed data, not a proof.** The
   row-arity census (§2.1) is over 11 seeded `kind:'faculty'` `ShapeSignature` nodes;
   a future faculty signature with a 1-element row would not be caught by the same
   accidental guard. This is named, not fixed — and is itself a small piece of
   evidence FOR eventually declaring something like a `kind`/`category` field, just not
   evidence that it is worth building on the strength of today's live behaviour.
4. **The five-way H1 split (§1.1) is confirmed by reading, not by an exhaustive
   machine-checked sweep of every node type in the seed corpus.** `SHAPE_TYPE_VOCABULARY_SPIKE.md`
   §2.3 already measured 354-427 distinct node types across the seed corpus; this rung
   did not re-run that census filtered for "shape-bearing," so a rarer sixth category
   is not ruled out by exhaustive search, only by not being found in the types this
   arc's own prior rungs already flagged as shape-bearing.
5. **No benchmark claim.** Per `CLAUDE.md`'s standing rule, this entire rung is a
   mechanism-level null; no number changed on any task.
6. **The DOOR_SWITCH connection is confirmed at the strategy level only (§3)** — citing
   it as evidence for "coarse-before-fine is a sound design pattern in general" is fair;
   citing it as evidence that the SAME mechanism (a distance metric) is what a
   graph-kind guard would use is not, and this document declines to make that claim.

---

## 6. Named follow-on, explicitly not built here

The creator's own live sharpening, folded in per instruction rather than driving a
rebuild: *"this would also allow a far far better document describing how ocelot works.
because it has a shape schema."* `CLAUDE.md` already documents two reflective
faculties the agent can run today — `self_organisation` (reads its own microtheories:
"how are you organised?") and `self_shape` (reads its own eleven meta-shapes: "what
shape are you?"), both surfaced via `drive()`. If a `kind`/`category` field (under a
non-colliding name — see §1.2) is ever built on top of a future, better-targeted
guard site than the one this rung tested, the natural next capability is a
**GENERATED "how Ocelot works" account read directly off the graph's own kind-tagged
self-description** — not hand-authored, so it cannot drift from what the substrate
actually holds, the same way `self_shape`'s answer today is a live read of the meta-
shape codebook rather than a written paragraph. **Not measured, not built, not sized
here** — recorded so it is not rediscovered from scratch when a `kind` field does
eventually land on a site where §2's bar is met.

---

## 7. Reproduce

```bash
cd /home/matt/ozmadev/ocelot-worktrees/shape-kind-field-spike
git log --oneline -1 main   # 4bb1794, verified before branching

# §1.2 — the three existing meanings of "kind"
sed -n '389,396p' runners/dsl/src/shape_decode.rs   # DimensionGenerator.kind (dispatch)
grep -n '"kind"' seeds/math_capability_shapes.json  # math/faculty/authored domain label
sed -n '7045,7064p' domains/reflective_faculty.py   # _load_shape_signatures reads it

# §2 — the decisive measurement (P2a, P2b)
PYTHONPATH=. python3 scripts/shape_kind_probe.py

# §4 — regression (no shared file touched)
python3 -m pytest tests/test_analogical_shape_math_migrated.py \
                   tests/test_meta_shape_arity_migrated.py -q   # 21 passed
```
