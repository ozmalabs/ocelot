# Codebook partition consolidation — RESULTS

**PREREG:** `CODEBOOK_PARTITION_CONSOLIDATION_PREREG.md` (same folder), registered
before any file was touched.
**Worktree:** `/home/matt/ocelot-codebook-partition-consolidation`, branch
`codebook-partition-consolidation`, from `main`@`2b271bc`.
**Charter:** `SHAPE_TYPE_VOCABULARY_SPIKE.md` §3.4(a) — fifteen `ShapeSignature*` node
types plus a `kind` attr, called an instance of `SHAPE_AUDIT.md`'s sixth pattern.

---

## The one thing worth reading if you read nothing else

**`kind` does not partition a decode pool, and never has.** The spike's §3.4(a) says
the type split and the `kind` attr serve *"the same need"*. They do not. A **node type
is the only mechanism that partitions a `ShapeDecode` candidate pool**; `kind` is a
pass-through label that `load_parts` reads into `Part.kind_val` and
`eval_shape_decode` copies into the plan step, and that nothing filters on. A `kind`
key on the Term's wire form is silently dropped.

So the implied fix — collapse the types into `ShapeSignature{kind:…}` — is not a
simplification. It **deletes the only working isolation mechanism** and replaces it
with the emergent fact that the pools happen to use disjoint predicates today. That is
measurably unsafe:

| merge | held signatures re-decoded | verdict CHANGED |
|---|---|---|
| the four stroke grains → one pool | 502 | **261** |
| `ShapeSignatureCoarse` alone, effect on the PRIMARY fine pool | 237 | **147** |
| `ShapeSignatureMid` alone, same | 237 | **46** |
| the eight own-pool reading-faculty types → one pool | 51 | **1** (`condition_if` → `conditional`) |

**Verdict: NO-GO on all fifteen.** Three types were technically eligible under the
PREREG's own decision rule and were still declined — the reason is §6, recorded as a
deviation rather than buried.

**What shipped instead:** the reasons, which until now lived only in docstrings and one
seed `description`, are now **gated** (`tests/test_codebook_partition_migrated.py`,
8/8), the deciding measurement is reproducible
(`scripts/codebook_partition_probe.py`), and §3.4(a) is **corrected in place** in the
spike rather than silently left standing.

**And the sixth pattern IS here — it is the other copy.** Of the fourteen subtypes,
**ten** carry a `kind` attr that merely restates the type name
(`ShapeSignatureCoherence{kind:'coherence_relation'}`, `ShapeSignatureNarrative
{kind:'narrative_role'}`, `ShapeSignatureCoarse{kind:'stroke_coarse'}`, …) and that
nothing filters on; **two** carry a `kind` that is a genuine sub-classifier and not a
restatement (`ShapeSignatureMeter{kind:'foot'}`,
`ShapeSignatureThroughline{kind:'character'|'pattern'|'payoff'}`); **two** carry no
`kind` at all (`Register`, `Format`). The duplicated enumeration is those ten inert
`kind` values, not the types.

---

## 1. AR2 — the mechanical question, answered first because everything turns on it

Read: `runners/dsl/src/shape_decode.rs::load_parts` (`:239-325`) and every filter
parameter on `ShapeDecode` / `TransformDecode` / `DimInfer` (`term.rs:947-985`).

```rust
for nid in ctx.graph.nodes_of_type(codebook_type) {      // :248  — the ONLY partition
    ...
    "kind" => kind_val = Some(v.clone()),                 // :260  — read
    ...
let kind_val = kind_val.unwrap_or(Value::Str(Sym::default()));   // :313 — defaulted
by_name.insert(name.clone(), Part { name, name_val, kind_val, ... });  // :322 — stored
```

`kind_val` is then used at exactly one place — `shape_decode.rs:1380`, copying it into
the emitted `PlanStep`. **It is never a predicate on candidacy.** The two filters that
do exist are both keyed on the part's **name**:

* `exclude` — *"evaluates to part name(s) to skip"* (`term.rs:911`);
* `codebook_scope` — *"restrict the codebook to parts whose `name` is in this set —
  the inclusion twin of `exclude`"* (`term.rs:962-965`).

**Live, `scripts/codebook_partition_probe.py`:**

```
goal BBB, no filter                  -> [('p_beta', 'beta')]
goal BBB, term param kind='alpha'    -> [('p_beta', 'beta')]      <- silently dropped
goal BBB, term param codebook_kind   -> [('p_beta', 'beta')]      <- silently dropped
goal BBB, codebook_scope=['p_alpha'] -> []
goal BBB, exclude=['p_beta']         -> []
```

Two consequences worth stating separately:

1. **An unknown key on a Term's JSON wire form is silently ignored.** A rule author who
   writes `"kind": "stroke"` on a `ShapeDecode` gets no error and no filtering. This is
   the same silent-drop class `string_attr_or_panic` was built to end one layer down
   (`shape_decode.rs:191-233`); it is **not** fixed here (engine change, wide blast
   radius) but it is named.
2. **Is `kind`-scoping trivially buildable?** Yes — a `codebook_kind: Option<Sym>`
   threaded into `load_parts`' loop is roughly ten lines. **It was deliberately not
   built.** Nothing in the tree needs it: every pool that needs isolation already has a
   node type, and adding an unused engine parameter is exactly the *"scalar knob
   standing in for a shape"* failure `CLAUDE.md`'s SHAPES-NOT-NUMBERS section names.
   Registered as out-of-scope in the PREREG §4 before measuring, and the measurement
   did not change that.

**Where `kind` IS load-bearing, and it is not here.** The codebook-facing modules do
read `kind` — `stroke_codebook.py:275/291/553/849/870/1082`, `ink_decode.py:773`,
`arrangement_codebook.py:132`, `code_reading.py:455`, `reading_collapse.py:1478/2938`,
`format_channel.py:359`, `metrical_reading.py:481`, `prog_ir_signature.py:243/264`
(every `get("kind")` in those eight modules was read). Every one is a **mint-side name
lookup or a post-decode readback** — "is this name already held at this kind", "read
the winner's attrs back". Not one scopes a decode. That is the correct division, and
§5 shows the corner of the tree that already states it.

---

## 2. AR1 — per-type justification audit, all fifteen

Method: predicate vocabulary and relation arity of every `signature` attr, measured over
`seeds/*.json`; every `codebook_type` site (seed rule bodies **and** the Python module
constants — `domains/narrative_structure.py:84`, `discourse_coherence.py:96`,
`trope_theme.py:111/118`, `throughlines.py:53/54`, `story_tree.py:71`,
`nested_reading.py:55` — a seed-only grep under-counts by nine); and the type's own
stated reason where one exists.

| # | type | n | verdict | why |
|---|---|---|---|---|
| 1 | `ShapeSignature` | 399 | — | the default pool; 14 `kind` populations across 11 seeds |
| 2 | `ShapeSignatureCoarse` | 185 | **J** | same predicates+arities as fine; merging changes **147/237** fine verdicts |
| 3 | `ShapeSignatureMid` | 44 | **J** | same; merging changes **46/237** fine verdicts |
| 4 | `ShapeSignatureFineChild` | 10 | **J (prophylactic)** | same predicates; 0/237 today, 2/10 child-goal decodes change — see §2.2 |
| 5 | `ShapeSignatureCoherence` | 8 | **J** | the `IF` collision, §2.1 — the one stated reason, and measurement confirms it |
| 6 | `ShapeSignatureNarrative` | 6 | **J (own pool)** | own `codebook_type` site; disjoint today, but see §2.3 |
| 7 | `ShapeSignatureRegister` | 6 | **N (staging)** | not a codebook — projected into `ShapeSignature{kind:'register_sig'}`, §5 |
| 8 | `ShapeSignatureMeter` | 5 | **N (staging)** | **carries no `signature` attr at all** — `load_parts` skips every one |
| 9 | `ShapeSignatureFormat` | 4 | **N (staging)** | projected into `ShapeSignature{kind:'format_sig'}`, §5 |
| 10 | `ShapeSignatureTrope` | 3 | **J (own pool)** | own `codebook_type` site (`trope_theme.py:111`) |
| 11 | `ShapeSignatureSemanticTrope` | 3 | **J (own pool)** | own `codebook_type` site (`trope_theme.py:118`) |
| 12 | `ShapeSignatureStoryBoundary` | 3 | **J (own pool)** | own `codebook_type` site (`story_tree.py:71`) |
| 13 | `ShapeSignatureThroughline` | 3 | **J (own pool)** | own `codebook_type` site (`throughlines.py:53`) |
| 14 | `ShapeSignatureMetaTheme` | 2 | **J (own pool)** | own `codebook_type` site (`throughlines.py:54`) |
| 15 | `ShapeSignatureSpanningTheme` | 1 | **J (own pool)** | own `codebook_type` site (`nested_reading.py:55`) |

**Count: 0 of 15 redundant.** 11 justified, 3 not codebooks at all (and correctly
outside the pool for that reason), 1 is the default pool itself.

### 2.1 The one stated reason, and the collision that proves it

`seeds/coherence_relations.json` line 5, verbatim: coherence relations are *"kept in
their OWN codebook_type so they never compete with the clause-construction
`ShapeSignature` pool"*. That seed's manifest also declares
`"depends_on": ["reading_constructions"]` — **the two pools are always co-loaded**.

They collide, exactly once, and it is enough:

```
reading_constructions   ShapeSignature{name:'conditional'}          [["IF"],["THEN"]]
coherence_relations     ShapeSignatureCoherence{name:'condition_if'} [["IF"]]
```

Live before/after, real seed data, the reading faculty's own call shape
(`beam=1, max_steps=1, cand_k=4`):

```
coherence decode of a marked conditional   goal=[['IF']]
  BEFORE (pool=ShapeSignatureCoherence)  [('condition_if','coherence_relation',1,1)]
  AFTER  (merged into ShapeSignature)    [('conditional','construction',1,1)]
  IDENTICAL: False
```

The tree's single documented justification for a codebook type split is **correct, and
now measured** rather than asserted. It is also the ONLY predicate overlap between two
separately-pooled reading vocabularies (§2.3) — the one place emergent disjointness
already failed.

### 2.2 The stroke grain ladder — a structural guarantee, and the honest edge of it

`domains/stroke_codebook.py::grow_stroke_refinement_quantum` states the general
principle better than this document could:

> *"installing it into the SAME `"ShapeSignature"` node type would still make it a
> candidate `_score_span`'s default `ShapeDecode` scan iterates (Rust's `load_parts`
> filters by node TYPE, never by a `kind` attr) … A genuinely separate node TYPE makes
> that PROVABLY impossible rather than merely improbable."*

**That sentence is the answer to this rung's charter, and it was already in the tree.**
It was written by someone who hit the mechanism directly, and the spike's §3.4(a) was
written without it.

All four stroke grains carry identical predicate vocabularies
(`seg`/`pose_x`/`pose_y`/`pose_o`/`pose_s`) at overlapping arities, so this is the
family where a merge is unambiguously destructive — 261/502 held signatures re-decode
differently. Examples:

```
O_0                    before ('O_0','stroke',56,16)   after ('bulge_0','stroke_mid',52,12)
stroke_9cec1d207bb0    before (…,'stroke',56,16)       after (…,'stroke_coarse',51,11)
mid goal 'line'        before ('line','stroke_mid',…)  after ('I_0','stroke',…)
```

**The honest edge:** merging `ShapeSignatureFineChild` alone changes **0/237** fine
verdicts on today's seed. Its guarantee is prophylactic — which is precisely what its
own docstring claims ("PROVABLY impossible rather than merely improbable"), so the
verdict stays J, but the claim is recorded at its measured strength, not inflated.

### 2.3 The seven own-pool reading types — eligible on today's data, still declined

Merging all eight own-pool reading vocabularies plus their shared dependency
`reading_constructions` into one pool re-decoded 51 held signatures and changed **one**
(the `IF` collision). The other seven are predicate-disjoint today. **Four of them are static** (no mint path:
`Narrative`, `StoryBoundary`, `Throughline`, `MetaTheme`, `SpanningTheme`), but **three
do grow at runtime** — `trope_theme.py:474` mints `ShapeSignatureTrope`,
`trope_theme.py:957` mints `ShapeSignatureSemanticTrope`, and `register_source.py:756`
mints `ShapeSignatureRegister`. A first sweep missed all three because they mint through
the module constant, not a literal — the same under-count the `codebook_type` sites had,
and it is recorded because it changes the argument: for those three, "the predicates are
disjoint today" is a statement about a vocabulary that is still being written.

They were still not consolidated, and the PREREG's clause 2 is why: **each has a
`codebook_type` site pointing at it.** A decode that names a type IS using the type as
its pool. Consolidating means rewriting that decode to point at a shared pool it must
then *trust* to stay disjoint — trading a structural guarantee for an emergent property,
for zero mechanical gain, in a tree that has one live measured counterexample to that
trust sitting in the same family (§2.1).

### 2.4 The one isolation the tree gets WITHOUT a separate type — and its exact condition

`ShapeSignature{kind:'substroke'}` (26 parts) shares ONE pool with
`ShapeSignature{kind:'stroke'}` (237). `domains/ink_decode.py::decode_substrokes`
justifies it as *"arity-distinct from every stroke-grain entry … why this is safe
without a companion node type"*.

**Measured, and it holds** — but it is an emergent property with a precise failure
condition:

```
arity x kind in the one shared pool: {('stroke',16):83, ('stroke',12):146,
                                      ('stroke',7):8,  ('substroke',8):26}
cross-kind verdicts over all 263 parts: 0
```

A signature's relation count is `segments + 4` (four `pose_*` singletons), so a
stroke-grain quantum authored with `segments == SUBSTROKE_SEGMENTS (4)` lands at arity 8
and collides. `DEFAULT_SEGMENTS` is 12. This is now gated
(`test_substroke_arity_disjointness_is_the_only_thing_separating_it_from_stroke`) so the
collision would surface as a test failure rather than a silent misrecognition.

Two further within-pool `kind` overlaps were checked and are **intended**, not defects:
`ShapeSignature{kind:'math'}` × `{kind:'faculty'}` share 11 predicates inside
`math_capability_shapes.json`, and cross-signature comparison is that seed's entire
purpose (*"the bridge faculty runs the HELD AntiUnify over two named signatures"*).

---

## 3. Why predicate-disjointness is a sufficient safety condition — read, then confirmed

The PREREG registered as **risk 1** that a foreign part might win a zero-coverage
contest on `shape_fit` alone, since fit is an `AntiUnify` score not gated on predicate
match. **That risk is disproven** — `shape_decode.rs:1345-1347`:

```rust
let (fit, covered) = score_part_for_residual(&state.residual, sig, &wild_val, wild_objects);
if covered.is_empty() {
    continue;                 // a part covering nothing is never a candidate
}
```

So a part with no predicate overlap is never entered into the beam at all. Confirmed
live (`ar3_contam` probe: identical plans with and without disjoint foreign parts, for
fully-covered, partly-covered and uncovered goals). `TransformDecode`/`DimInfer` are
stricter still — `build_candidate` (`:1591`, `:1619`) requires equal relation counts and
per-pair predicate equality.

**This is the finding that makes the whole audit tractable:** predicate vocabulary is
the thing to measure, and merging only ever matters where predicates overlap. It is
also why the `IF` collision is decisive rather than incidental.

---

## 4. AR4 — the other `codebook_type` names, categorized

36 distinct values across seed rule bodies, Python literals and module constants. They
are **not** one phenomenon; they fall into four groups, and one of them is not this
mechanism at all.

**(a) Seed-declared `ShapeDecode` pools — genuinely different grains.** `F16AxisSample`
(36 sites, order-N viability samples), `EmbodiedMotorPlanHintStage` (113 nodes),
`EmbodiedMotorPlanHint` (19), `ChannelStreamSignature`, `ControlOrderSample`. Each
carries `name` + `signature` and is read by `load_parts` exactly like `ShapeSignature`.
Their parts are embodied-control samples with their own predicate vocabularies —
correctly their own pools, same reasoning as §2.3.

**(b) Runtime-minted pools with zero seed declarations** — `MetaShape`,
`ConceptSignature`, `HumanoidMotorProgram`, `HumanoidBodyShapeSignature`,
`EmbodiedMotorShapeMemory`, `EmbodiedMotorProposalShapeMemory`,
`EmbodiedMotorProposalBodyShapeMemory`, `EmbodiedDevelopmentalCapabilityMemory`,
`SomatomotorCouplingMemory`, `EmbodiedMotorProgramShape`, `XfSignature`, `VdSignature`,
`SeenQuantum`, `ShapeSignaturePrediction`. **Genuinely-different-grain**, and
`MetaShape` is the precedent the charter names: `META_SHAPE_FIRST_CLASS_RESULTS.md` §3(b)
records that its codebook holds **WILD-slotted lgg patterns, not literal parts**, so
rung 1 there is `Covers`, not `ShapeDecode`'s literal set cover — a content difference a
`kind` attr could not express even if `kind`-scoping existed. Consolidating any of these
is not on the table.

**(c) Staging types that are NOT pools** — `ShapeSignatureRegister`,
`ShapeSignatureFormat`, `ShapeSignatureMeter`. §5.

**(d) A different `codebook_type` key entirely — a name collision, reported not fixed.**
`domains/procedural_reader.py:387`, `method_synthesis.py:329-347`,
`binding_resolver.py:705` use `codebook_type` **paired with `codebook_key`** to name one
side of a rule JOIN parsed out of natural language ("a *view* holds the *count* of its
*source's mentions*"). Its values are things like `"tag"`, `"action intent"`,
`"trope signature"`, `"epistemic signal"`, `"disclaimer cue"` — and the corresponding
seed nodes (`DisclaimerCue`, `DistancingCue`, `OpposingActionPair`, `TropeSignature`,
`EpistemicSignal`) carry **no `signature` attr**, so `load_parts` would skip every one.
This has nothing to do with `ShapeDecode`. **Any future sweep that greps
`codebook_type` and treats the hits as one population will be wrong** — including this
document's own first pass, which is why it is recorded here.

---

## 5. The corner of the tree that already has the right rule: **type = pool, kind = label**

`register_source`, `format_channel` and `metrical_reading` do not decode against their
`ShapeSignature*` types at all. `ensure_*_codebook` **projects** each staging node into
a plain decode-part in the shared default pool, copying name and signature verbatim:

```python
# domains/format_channel.py:111
sub.add_node("ShapeSignature", {
    "name": nm, "kind": "format_sig", "signature": at.get("signature"),
    "format": at.get("format", nm), ...})
```

So for this family the division is already correct and complete:

* the **staging type** holds the definition — including attrs that must never reach the
  pool, e.g. `register_source`'s `shape_decode: 0.0` gate, which withholds a decode-part
  for the `conversational` register so it *"can never change an existing document's
  decode-by-shape verdict"*;
* the **derived `ShapeSignature{kind:'register_sig'|'format_sig'|'foot_tiled'}`** is the
  pool member, and `kind` is its label — read back by
  `format_channel.py:359` / `metrical_reading.py:481` after the decode, never before it.

`ShapeSignatureMeter` is the cleanest case: its nodes carry `base_pattern`, `syllables`,
`adjective` and **no `signature` attr at all**, so `load_parts`' `let (Some(nv),
Some(sv)) = (name_val, sig_val) else { continue }` skips every one. A type named
`ShapeSignature*` that is not a signature codebook is a naming wart, but it is
**mechanically inert** and renaming it would touch six modules, two seeds and four
scripts for no behavioural gain. Reported, not renamed.

---

## 6. AR3 — the GO/NO-GO, and a deviation recorded rather than buried

**Verdict: NO-GO on all fifteen.**

The PREREG's decision rule had three clauses, all required. Applying it:

* Clause 1 (verdict R or N) — excludes the 11 J types.
* Clause 2 (no `codebook_type` site) — excludes the 8 own-pool reading types and
  `Coarse`/`Mid`, independently.
* Clause 3 (identical live before/after) — excludes `Coherence`, and the whole stroke
  ladder, on measurement.

**The deviation.** Three types — `ShapeSignatureRegister`, `ShapeSignatureFormat`,
`ShapeSignatureMeter` — passed **all three clauses** (N verdict; zero `codebook_type`
sites; measured identical before/after: `register_source` and `format_channel` merges
returned the same plan and the same `kind`, and `Meter` has no `signature` so a merge is
inert). Under the rule as written they were eligible. **They were still declined**, and
the reason matters more than the rule:

> Merging a staging type into `ShapeSignature` puts the definition nodes **inside** the
> pool they feed, where they become **name-duplicates of their own derived parts**.
> `load_parts` dedups by name with *"a later duplicate name only overwrites its VALUE"*
> (`:236-238`). The measured before/after is identical **only because
> `ensure_*_codebook` happens to insert the derived part second**. Today's safety is an
> insertion-order accident where today's separation is structural. That is strictly
> worse, for zero benefit.

So AR3's clause 3 turned out to be **necessary but not sufficient**: "the results are
identical today" does not establish "the invariant is as strong". A future rung reusing
this decision rule should add a fourth clause — *does the merge preserve the strength of
the guarantee, not just its current output?* Recorded here rather than retro-fitted into
the PREREG.

---

## 7. AR5 — what shipped

No source file changed. Zero Rust changes (the `codebook_type` mechanism is
grain-agnostic and needed none — confirmed by reading `load_parts`, as
`META_SHAPE_FIRST_CLASS_RESULTS.md` §3 already established). Zero seed changes, so the
"seeds are emitted, never hand-edited" rule is not engaged: **there was nothing to
migrate.** Noted in passing, since a migration would have needed it: **no
`tools/build_*.py` emits any of the twelve seed files** holding these types (checked
by name against every `seeds/…json` path referenced from `tools/` and `scripts/gen_*`).
`stroke_shapes.json` and `character_shapes.json` are written by the agent's own
`teach()` facility (`stroke_codebook.grow_stroke_quantum`); the reading-faculty seeds
(`coherence_relations`, `narrative_structure`, `register_source`, `prosodic_meter`,
`format_channel`, `narrative_tropes`, `semantic_tropes`, `story_boundary`,
`throughline`, `throughline_meta`, `spanning_theme`) are hand-authored manifests
installed by `ensure_*_codebook`. Reported, not addressed.

1. **`tests/test_codebook_partition_migrated.py`** — 8/8. Turns four measured
   invariants into gates that previously existed only as prose:
   * `test_kind_is_a_label_not_a_pool_filter` — the central mechanism. Fails loudly if
     a `kind`-scoped decode is ever built, with a message telling the reader to
     re-measure this document's NO-GO.
   * `test_coherence_codebook_must_stay_its_own_node_type` — the `IF` collision.
   * `test_stroke_grain_ladder_must_stay_separate_node_types` (×3 grains).
   * `test_substroke_arity_disjointness_…` — the emergent invariant
     `decode_substrokes` relies on, with its exact failure condition asserted.
   * `test_staging_signature_types_are_not_decode_pools` (×2).
2. **`scripts/codebook_partition_probe.py`** — the deciding measurement, reproducible,
   over real seed data, no mocking.
3. **`SHAPE_TYPE_VOCABULARY_SPIKE.md` §3.4(a) corrected in place**, retraction-style
   (the counts stand; the *"same need"* sentence and its implied fix are marked wrong,
   with the measurement). The original text is left readable — a historical record is
   not converted, a standing claim is.

---

## 8. AR6 — regression, as LISTS

**Selection:** 70 test files — every `tests/test_*` whose name matches
shape / decode / ink / stroke / character / arrangement / narrative / trope /
coherence / register / format / metrical / reading / meaning / order_n / theme /
story / through / codebook / composer / dimension / transform. This is deliberately the
whole decode-and-codebook neighbourhood, not the four files this rung's own claims
touch.

**Conditions, stated because a red count without them is the exact defect CLAUDE.md
retracted a paragraph over:** `data/` present; `chess` not required by this selection;
`-p no:randomly`, `--continue-on-collection-errors`, `--timeout=900`, no `-n`;
**engine binary stale** (see below).

```
155 failed, 802 passed, 18 skipped, 34 errors in 2001.39s
```

**The list — 189 red node ids across 42 files —** is written to
`results/codebook_partition_red_nodeids.txt` (one id per line, sorted). It is a list,
not a count, and not a characterisation.

**Paired before/after.** The two lists are **identical**, and the argument is
structural rather than a second 33-minute run, so its premises are stated so a reviewer
can check them:

1. `git status` on the branch shows **one** tracked modification —
   `SHAPE_TYPE_VOCABULARY_SPIKE.md` — plus four new files
   (`…_PREREG.md`, `…_RESULTS.md`, `scripts/codebook_partition_probe.py`,
   `tests/test_codebook_partition_migrated.py`, `results/…red_nodeids.txt`).
   **No `.py`, `.rs`, or `.json` under `domains/`, `substrate/`, `runners/`, `seeds/`
   was touched.**
2. **Nothing reads the edited document at runtime.**
   `grep -rn "SHAPE_TYPE_VOCABULARY_SPIKE" tests/ domains/ scripts/ substrate/`
   returns docstring mentions only — no `open(`, `read_text`, or `Path(` reference. The
   one test file that names it (`test_meta_shape_arity_migrated.py`) mentions it in its
   module docstring and is **green** in this sweep.
3. **The new test file contributes zero reds** — `grep -c codebook_partition` over the
   red list is `0`, and it passes 8/8 standalone.

So no red id in the list can be caused by this branch. Any reviewer who disagrees can
falsify it by running the same selection at `2b271bc`; the selection command is in §10.

**Two conditions on the reds that are pre-existing and NOT this rung's:**

* **34 errors are `EngineProvenanceError`, not test failures.** `git worktree add`
  gives every checked-out `.rs` a fresh mtime, so `engine_provenance` reports the
  prebuilt `_native.abi3.so` as *"STALE — 85 .rs newer than the binary"* and refuses to
  measure. **The primary tree at `main` reports the same refusal** (*"STALE — 4 .rs
  newer"*), and `diff -rq` shows the two trees' `runners/dsl/src` are byte-identical, so
  the binary is correct for this source and only the mtimes lie. The guard was **not**
  worked around — touching a provenance binary to silence it is exactly the kind of
  quiet falsification it exists to prevent.
* The remaining reds are the tree's documented pre-existing condition for this
  neighbourhood. `results/failure_baseline.json` — the enumerated baseline CLAUDE.md
  names — **is not present in the tree at `2b271bc`** (only its generator,
  `scripts/failure_baseline_sweep.py`, and its gate,
  `tests/test_failure_baseline_migrated.py`), so this list could not be diffed against
  it. Reported, not worked around.

---

## 9. What this document does NOT establish

* **It does not prove the eleven J verdicts are optimal.** It proves each type's
  separation is currently load-bearing or currently harmless-and-structural. A
  different architecture (a `kind`-scoped `load_parts`, or a Γ production declaring
  pool membership) could make some of them unnecessary. That architecture does not
  exist and was deliberately not built here.
* **Predicate disjointness was measured on seed-declared parts only.** Pools that grow
  at runtime (the stroke grains, `ShapeSignatureTrope`/`SemanticTrope`/`Register`,
  `MetaShape`, the embodied-motor memories) can mint parts whose predicates are in no
  seed. The stroke case is exactly why those grains have separate types; the others
  were not swept for runtime vocabularies.
* **Two greps in this audit under-counted, and both were caught by reading rather than
  by a wider grep.** `codebook_type` sites (a seed-JSON grep misses the nine Python
  module constants) and runtime mint sites (a literal-`add_node("ShapeSignature<X>"`
  grep misses `add_node(_CODEBOOK_TYPE, …)`). Both corrections are folded in above;
  they are recorded because the same two shapes will defeat the next sweep too.
* **The silent-drop of unknown Term keys was named, not fixed.** It is a real defect
  class of the same family as `string_attr_or_panic`'s, and it is engine work with a
  wide blast radius.
* **`ShapeSignatureMeter`'s naming was not fixed.** A type named `ShapeSignature*` that
  carries no signature is misleading; renaming it is a six-module change for no
  behavioural gain and was declined on cost, not on principle.

---

## 10. Reproduce

```bash
cd /home/matt/ocelot-codebook-partition-consolidation
PYTHONPATH=runners/dsl/python:. python3 scripts/codebook_partition_probe.py
PYTHONPATH=runners/dsl/python:. python3 -m pytest tests/test_codebook_partition_migrated.py -q

# the AR6 selection, verbatim (33 min; run under a memory scope, never -n auto)
SEL=$(ls tests/ | grep -iE \
  "shape|decode|ink|stroke|character|arrangement|narrative|trope|coheren|register|\
format|metrical|reading|meaning|order_n|theme|story|through|generic_reading|codebook|\
composer|dimension|transform" | sed 's|^|tests/|' | tr '\n' ' ')
PYTHONPATH=runners/dsl/python:. systemd-run --scope --user \
  -p MemoryMax=8G -p MemoryHigh=7G -- \
  python3 -m pytest $SEL -q -p no:randomly --continue-on-collection-errors --timeout=900
```

Counts in §0 and §2 come from a read-only pass over `seeds/*.json` `nodes` arrays,
reproducing the spike's own figures exactly (399 / 185 / 44 / 10 / 8 / 6 / 6 / 5 / 4 /
3 / 3 / 3 / 3 / 2 / 1).

## 11. Files

| file | change |
|---|---|
| `docs/research/engine_substrate/CODEBOOK_PARTITION_CONSOLIDATION_PREREG.md` | new |
| `docs/research/engine_substrate/CODEBOOK_PARTITION_CONSOLIDATION_RESULTS.md` | new (this) |
| `docs/research/engine_substrate/SHAPE_TYPE_VOCABULARY_SPIKE.md` | §3.4(a) corrected in place |
| `scripts/codebook_partition_probe.py` | new |
| `tests/test_codebook_partition_migrated.py` | new, 8/8 |
| `results/codebook_partition_red_nodeids.txt` | new — the AR6 list, 189 ids |
