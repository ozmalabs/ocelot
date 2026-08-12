# META-SHAPE AS A FIRST-CLASS GRAIN — PREREG

**Status: REGISTERED BEFORE CODE.** Written against `main` at `ae38fe7`
(`Shape audit: 40 confirmed sites across the codebase, verified not just
grepped`), in the isolated worktree
`/home/matt/ocelot-meta-shape-first-class` on branch
`meta-shape-first-class`. The only measurements taken before this document was
written were **read-only** (a probe that boots `seeds/shape_vocabulary.json` and
calls the *existing* `categorise_by_shape`); those numbers are quoted in §2 as
the registered BEFORE, and nothing in the tree was modified to produce them.

**Charter.** `docs/research/engine_substrate/SHAPE_AUDIT.md` findings **#1 and
#2 only** (its §5.1 and §2.5). The creator's directive: *"Shape needs to be a
first class item, do it."*

---

## 0. The claim being tested, in one paragraph

Every other grain in this tree that decodes against a codebook has the **whole**
sd loop: `decode → residual → mint → codebook grows → re-decode → recognize`.
Vision/`CapabilityAxis`, ink strokes, program-synthesis chunks, spatial quanta
and latent dimensions all do. **The grain literally named "shape" — the agent's
`MetaShape` vocabulary — has only the recognize half, and that half is a
substring count over a lossy string with an alphabetical tiebreak.** This rung
asks whether meta-shape can be made first-class on the *same* shape as the other
five: (a) recognition by the item's **structure** rather than by a name-bag, and
(b) a **mint path** so a residual that recurs grows the codebook. It is
deliberately NOT asking whether twelve shapes are better than eleven — the
audit's own §5.1 caution stands: *"the absence is the finding, not the count."*

---

## 1. What is defective, precisely (the two findings, restated as mechanisms)

### 1.1 Finding #2 — `recognise_meta_shape` (`runners/dsl/src/shape_decode.rs:5339-5395`)

Three stacked defects, in the order they destroy information:

1. **The item's typed structure is destroyed before scoring.**
   `domains/teach.py:93` builds the scored text as
   `" ".join(str(v) for v in attrs.values() if isinstance(v, str)).lower()`.
   This discards (i) every attribute **KEY**, (ii) every **non-string** value,
   and (iii) the node **TYPE** (`type_`) entirely. An item
   `Concept{name:"quintuple", definition:"multiply a number by five",
   multiplier_factor:5.0}` is scored as the string
   `"quintuple multiply a number by five"`.
2. **The score is a raw `text.contains(kw)` count at PRINCIPLE granularity** — a
   principle counts once no matter how many of its keywords hit, so *two*
   independent pieces of evidence for one shape score identically to *one*.
3. **Ties break alphabetically by the shape's own name**
   (`.then_with(|| a.1.cmp(&b.1))`). This is not a stability tiebreak on an
   otherwise-decided contest; on this vocabulary it is *the deciding step* in a
   measured majority of ambiguous cases (§2).

### 1.2 Finding #1 — no mint path anywhere

`seeds/shape_vocabulary.json` holds 11 `MetaShape` + 13 `ShapePrinciple` + 17
`FunctionalRole` nodes and **nothing in the tree mints one at runtime.** The
residual currently dies in `teach.py:148-150`: when `categorise_by_shape`
returns `None`, the item is filed under its own `category`/`domain`/`topic`
string, else the literal `"taught"`. That fallback is exactly where a
**mint candidate** should be, and is not.

---

## 2. THE REGISTERED BEFORE (read-only, measured on `ae38fe7`, engine
`81d75c0a84dc221839cb1d4aa9668d2064061613a225bf754cbc768c9f9b5b2e`)

Booting `seeds/shape_vocabulary.json` alone, the held codebook is:

| MetaShape | principles |
|---|---|
| associative_recall | pattern_completion |
| competitive_inhibition | pattern_separation, winner_take_all |
| delayed_persistence | buffering, consolidation |
| feedback_control | homeostasis, regulate |
| global_message_passing | broadcast |
| hierarchical_invariance_buildup | hierarchical_abstraction |
| modular_isolation | modular_specialization |
| prediction_minus_observation | prediction |
| relational_structure_match | hierarchical_abstraction, structure_mapping |
| selective_gating | gated_access |
| spatial_dynamics | spatial_motion |

*(`regulate` is a `has_principle` target with no `ShapePrinciple` node of that
name in the manifest — recorded, not fixed here: out of charter.)*

Two verdicts that the current recognizer gets **wrong, live**, both decided by
the alphabetical tiebreak:

| observation text | principle-scores | current verdict | why it is wrong |
|---|---|---|---|
| `"gate the layer by policy"` | selective_gating 1, hierarchical_invariance_buildup 1, relational_structure_match 1 | **hierarchical_invariance_buildup** | `gated_access` matched **two** keywords (`gate`, `policy`); `hierarchical_abstraction` matched **one** (`layer`). The stronger evidence lost to the letter `h`. |
| `"the selection is a winner-take-all recall from an attractor"` | associative_recall 1, competitive_inhibition 1 | **associative_recall** | genuinely 2-vs-2 keywords. Not a wrong pick so much as a **fabricated** one: the contest is tied and the answer is asserted anyway. |

These are the audit's own cited failure mode reproduced live, including its
literal example (*"`associative_recall` beats `feedback_control` on a tie for no
reason but the letter `a`"*).

---

## 3. THE DESIGN, registered before building

### 3.1 Part 1 — recognition by structure (an Occam ladder, matching the sd loop's own)

**The item's signature.** An item `(type_, attrs)` is translated — *mechanically,
in Python, no conditionals over graph state* — into the sd loop's own relation-set
format, the same one `induce_concern` builds at `reflective_faculty.py:1286` and
`ShapeDecode` / `AntiUnify` / `Covers` consume:

```
[["is_a", <type_>],
 [<attr_key_1>, <tok>, <tok>, ...],
 [<attr_key_2>, ...], ...]
```

Nothing is discarded: keys become **predicates**, values become **arguments**,
the node type becomes an explicit `is_a` relation.

**The ladder**, run in `recognise_meta_shape_struct` (Rust), Occam-ordered
exactly like `sd_recognize → sd_transform_decode → sd_infer_dimension →
sd_mint_quantum`:

* **Rung 1 — STRUCTURAL COVER.** For every `MetaShape` holding a `signature`
  (an lgg pattern with WILD slots), test `covers_value(shape.signature,
  item.signature)` — the existing `Covers` primitive, a **boolean subsumption
  test, no threshold**. Among covering shapes, pick the **most specific** by
  `fixed_count_value(shape.signature)` — the identical specificity metric
  `sd_recognize` already uses (`FixedCount(AntiUnify(...))`). No scalar, no
  weight.
* **Rung 2 — SLOT-AWARE KEYWORD PRIOR (the honest bootstrap).** Only reached
  when rung 1 finds nothing. The 11 seeded shapes hold no signature and never
  will until something files under them, so keywords remain the bootstrap — but
  now scored over the **structure**, ranked **lexicographically** with no
  weights:
  1. `predicate_hits` — distinct (principle, relation-**predicate**) matches.
     A keyword matching the item's own typed slot name (or its `is_a` type) is
     *structural* evidence and outranks any amount of prose evidence.
  2. `principles_hit` — distinct principles matched (the CURRENT score,
     preserved as a key so this is a strict refinement, never a reversal).
  3. `keyword_hits` — distinct keywords matched (the finer evidence count that
     fixes the `"gate the layer by policy"` case).
* **Rung 3 — RESIDUAL.** Nothing scored, **or the top two candidates share the
  full ranking tuple** ⇒ return `None`. **The alphabetical tiebreak is deleted
  outright.** A genuine tie is a residual, not an answer. This is the sd loop's
  own honest-uncertainty discipline (`sd_mint_quantum` fires *"only after BOTH
  rungs fail"*; it does not guess).

**Term surface.** `RecogniseShape` becomes **input-polymorphic on the evaluated
value**: a `Str` takes the legacy text path (with the tiebreak fixed — finding
#2 applies to `TransferDecode` too, which shares the scorer); a `Tuple`/`List`
takes the structural ladder. Additive; no existing Term signature changes.

### 3.2 Part 2 — the mint path (AR2's registered answer)

**Where.** Graph rules in a new seed `seeds/meta_shape_growth.json`, mirroring
`seeds/shape_decode_loop.json` rule-for-rule. Minted entries are **live graph
nodes**, not seed-file edits — the same target every other grain mints into
(`sd_mint_quantum` adds a `CapabilityAxis` node; `sd_mint_generator` adds a
`DimensionGenerator` node). `seeds/shape_vocabulary.json` is **not** hand-edited
by this rung.

| rule | does |
|---|---|
| `ms_decode` | a `ShapeObservation{status:"pending"}` → `RecogniseShape(sig)`; stores `shape` + `decoded_epoch`; status → `decoded` |
| `ms_recognize` | `decoded` **with** a shape → status `recognized`, `recognised_as` edge to the winning MetaShape |
| `ms_residual` | `decoded` **without** a shape → status `residual` |
| `ms_mint_shape` | two `residual` observations with a **non-trivial** `AntiUnify` lgg → mint `MetaShape{name, signature, minted:1}` + `ShapePrinciple{name, keywords}` + `has_principle`; bump `codebook_epoch` |
| `ms_redecode` | any observation whose `decoded_epoch < agent.codebook_epoch` re-arms to `pending` |

**The support/threshold discipline, and why — AR2.**

* **Support = 2, and it is not a tuned scalar.** *Recurrence is the definition of
  idiom* (the discipline P7-C's chunk-mining registered, and the same one
  `sd_dedup_existing` encodes negatively). Two is the **smallest cardinality at
  which "recurs" is defined at all** — it is a definitional boundary, not a
  swept knob. The alternative precedents were considered and rejected in
  writing: P7-C's **distribution-derived quantile** needs a distribution, and
  this codebook has 24 entries total; a **similarity threshold** (the
  `stroke_codebook.py:82 DEFAULT_DTW_THRESHOLD = 0.15` shape) is exactly the
  Pattern E defect the audit reports at §6.3 and is refused here.
* **Non-triviality is structural, not numeric.** The lgg must retain **at least
  one relation whose predicate is not WILD** — i.e. the two residuals must share
  an actual named slot. Two unrelated items anti-unify to all-WILD and mint
  nothing. Again a boolean structural test, not a coverage fraction.
* **Mint-once by signature**, the `sd_mint_quantum` guard shape:
  `Not Exists` a `MetaShape` whose `signature` equals this lgg. And — learning
  from the audit's own §3.1 — the minted **name is derived from the SORTED set**
  of the lgg's fixed predicates (`ms_<p1>_<p2>_…`), never from their positional
  order, so the order-dependent-truncated-key defect §3.1 documents is not
  reproduced here.
* **Bootstrap compatibility.** The minted `ShapePrinciple` carries the shared
  fixed predicates as its `keywords`, so `analogical_thinking._vocab_hits` /
  `shape_hits` / `metashape_realisation_counts` / `_run_self_shape` — every
  existing reader — see the new entry through the interface they already use.

---

## 4. BARS — registered, with their NO-GO conditions

| bar | claim | passes iff | NO-GO iff |
|---|---|---|---|
| **AR1** | the recognizer fix is a real improvement, not a reshuffle | On an **exhaustive** sweep of a constructed adversarial set against **all 11** MetaShapes: every case the BEFORE decided by the alphabetical tiebreak is either decided correctly by evidence or honestly returned as a residual; and **≥1 case where structure (a typed slot) decides and text cannot** flips from a wrong/absent verdict to the right one. Every flip enumerated case-by-case. | the structural path changes no verdict, or changes one to a *worse* verdict, on the available cases |
| **AR2** | the mint design is registered before building | §3.2 above, unchanged, is what gets built; any deviation is reported as a deviation | — (this bar is discharged by this document) |
| **AR3** | the growth loop closes | A constructed observation that decodes to **no** shape under the fixed recognizer: (a) is marked `residual`, not forced into a wrong existing shape; (b) on recurrence mints **exactly one** new `MetaShape` + `ShapePrinciple`; (c) a **near-variant** observation, re-decoded after the epoch bump, is `recognized` **against the minted entry** via rung 1. **NEGATIVE CONTROL:** an observation that already has a home (e.g. the `gate the layer by policy` case) still recognises and mints **nothing** | the loop needs a Python `while`, or the mint fires for an item that already had a home, or re-decode does not recognise the near-variant |
| **AR4** | the existing consumers still work | `analogical_thinking` (`shape_hits`, `metashape_realisation_counts`, order-4), `TransferDecode`, and the reflective `_run_self_shape` all run against the fixed recognizer AND against a codebook containing a minted entry, live-checked | any consumer raises, or silently returns empty where it previously returned content |
| **AR5** | no regression | `cargo test --lib` (debug) green in the worktree; the Python suites covering `teach`/shape/analogy/transfer/reflective green. **Reported as paired failing-node-id LISTS, never counts** (CLAUDE.md's retracted-baseline rule), diffed against the same lists measured on `ae38fe7` **in this worktree, same engine-source condition** | any node id red in AFTER that is green in BEFORE |

**A NO-GO on any sub-part is a complete result.** If rung 1 cannot be shown to
decide anything the keyword prior does not already decide (a real possibility:
the seeded shapes hold no signatures, so rung 1 is dormant until a mint
happens), that is reported as measured, and the rung's value reduces to
"finding #2 fixed + the mint path built and demonstrated on minted entries
only" — which is stated here, in advance, as an acceptable landing.

---

## 5. Provenance and protocol

* Worktree `/home/matt/ocelot-meta-shape-first-class`, branch
  `meta-shape-first-class`, base `ae38fe7`. Nothing is pushed; `main` is not
  touched.
* Engine: this rung edits `runners/dsl/src/shape_decode.rs`, so the worktree
  **must build its own** `_native.abi3.so` (per
  `domains/engine_provenance.py` — a worktree otherwise silently measures the
  canonical tree's binary and its `.rs` edit evaporates). BEFORE and AFTER
  sha256 are stamped in the RESULTS doc.
* Coherence probe after every rebuild: `add_node("T", {"lst":[1,2,3],
  "tup":(1,2,3)})` reads back `[1,2,3]` and `(1,2,3)` **distinctly**.
* Files this rung is forbidden to touch (concurrent threads):
  `runners/dsl/src/rule_reflect.rs`, `add_rule`'s installation path in
  `substrate.rs` / `graph_rules.rs`, `domains/rule_signature.py`,
  `runners/dsl/src/py.rs`, `substrate/world_adapter.py`.
* The other 38 SHAPE_AUDIT findings are **out of charter**. Any noticed in
  passing are named in the RESULTS doc and not fixed.

---

## 6. Named risks, registered

1. **Rung 1 is dormant on a fresh boot.** No seeded MetaShape holds a
   `signature`, so structural cover cannot fire until a mint happens. Registered
   as expected, not as a defect — it is the honest bootstrap, and it is exactly
   why rung 2 keeps the keyword prior instead of deleting it.
2. **Deleting the alphabetical tiebreak changes `TransferDecode`'s verdicts on
   ties.** `tests/test_mechanism_transfer_migrated.py` is the exposed gate. If a
   committed transfer result depended on an alphabetically-decided tie, that is
   a *finding*, reported, not papered over.
3. **`categorise_by_shape` returning `None` more often** (honest residual)
   re-routes those items to `teach()`'s `domain`/`topic` fallback — the same
   place they went when they scored zero. Behaviour change is confined to
   previously-tied cases.
4. **A minted `ShapePrinciple`'s keywords are predicate names**, which the
   existing substring matchers will happily match inside unrelated prose. The
   mint therefore widens the keyword prior. Watched under AR4.
