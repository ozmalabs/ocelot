# Agent loop iteration 22 — SHAPE-BASED (structural) transfer closes the last link

**Date:** 2026-06-07
**Builds on:** iter-21 (commit aad5d9d6) — jabberwock SELF-ACQUIRES the re_represent
shape; breadth-audit confirms re_represent=1; DERIVE blocked by LEXICAL transfer.
**Script:** `scripts/jabberwock_shape_based_transfer.py`
**Code touched:** `runners/dsl/python/substrate_rs/__init__.py` (thin Shape
forwarders), `domains/harvester_shape.py` (a boundary registry so a frame's
Term-tree reaches the Shape branch). No Rust changed; no relational representation
authored.

---

## VERDICT (up front)

**YES — the shape-based transfer closes the last link.** With STRUCTURAL transfer
(`match_mode='shape'` / `shapes_compatible`), `synthesize_gaps` over the perceptual
frame now DERIVES the relational / re_represent gap that iter-21's lexical
(`match_mode='all'`) path could NOT. The full loop closes:

> diagnose (iter-20) → acquire (iter-21) → harvest (iter-21) → **SHAPE-transfer
> (iter-22)** → derive (iter-22)

The agent self-completed from "I lack a shape-KIND" to "I derived the fix." All four
required suites stay green (`test_stt_pipeline`, `test_perception_self_assessment`,
`test_process_meta_assessor`, `test_gap_guidance` — 32 passed).

---

## (1) How `match_mode='shape'` / `shapes_compatible` works

The structural matcher lives in `runners/dsl/src/shape.rs`, exposed to Python via
`runners/dsl/src/py.rs` (`shape_of_term`, `shapes_compatible`).

- **`shape_of_term(term_json)`** walks a Term-tree once and returns a three-axis
  **Shape** `{recursion, order_n, abstraction}`:
  - `recursion` ∈ {none, direct, structural} — self-reference / structural induction
    over the tree (a body that references its bound var; siblings that share a
    Term-shape).
  - `order_n` (u8) — max nesting depth of fold-like reducers (`Fold/Sum/Exists/…`,
    one rung each, Pearlmutter-Siskind Dⁿ) OR structural-composition depth
    (`And/Eq/Holds/Not/…`, one per nesting level).
  - `abstraction` ∈ {concrete, parametric} — `parametric` when a fold-like body
    composes over a bound variable (Smith reflective tower, one rung up).

- **`shapes_compatible(candidate, target)`** — the Cousot abstract-domain
  admissibility predicate. Returns True iff:
  1. `candidate.recursion == target.recursion` (equal), AND
  2. `candidate.order_n >= target.order_n` (candidate has at least as much
     structure), AND
  3. abstraction: `Parametric` satisfies `Concrete`, but `Concrete` cannot satisfy
     `Parametric`.

  Semantics: "the candidate could PRODUCE the target." It is **directional and
  subsuming** — a richer candidate is compatible with a poorer target, not the
  reverse.

- **How `differentiate` uses it** (`domains/order_n_postulates.py:309`): for a donor
  shape carrying `match_mode='shape'` + `target_shape`, the donor FIRES on a
  postulate iff
  `shapes_compatible(donor.target_shape, postulate_shape)` — i.e. the DONOR is the
  candidate, the FRAME is the target; the donor must structurally subsume the frame.
  `postulate_shape` is computed from the postulate's registered Term-tree via
  `harvester_shape.lookup_postulate_term`. With `match_mode='all'` (the iter-21
  path) it instead requires ALL the donor antecedent's content-word regexes to
  co-occur in the postulate text — a word conjunction.

**Why iter-21 could not fire it (LEXICAL).** The re_represent donor
(`rule_derived__characterize_by_invariant_relations_among_parts`) has
`match_mode='all'` with `match_patterns =
['\bobject\b','\binstances\b','\brelated\b','\btransformation\b','\bgroup\b',
'\bshifts\b','\bscales\b','\babsolute\b']`. The honest frame text states the SAME
proposition in speech vocabulary ("gammatone","cepstral","talker","accent",
"feature"), so the transformation-group word conjunction never all co-occurs → the
shape never fires. Verified: over the frame, iter-21 surfaces 0 change-side gaps
(byte-identical with/without the acquired domain).

**Pre-existing wiring gap found + fixed.** The wrapped `substrate_rs.Substrate`
(what every demo imports) did NOT forward `shape_of_term` / `shapes_compatible` to
the native object — so the Shape-aware branch in `harvester_shape` /
`order_n_postulates` silently no-opped under `except Exception` (AttributeError
swallowed). iter-22 adds thin one-line forwarders (world-adapter boundary exposing
an existing Rust primitive; no Python logic).

---

## (2) THE TWO FAITHFUL Term-trees (verbatim) — each from its OWN text

Each tree is built INDEPENDENTLY from the structure its own existing prose already
asserts. They are NOT rigged to be identical; they are the same PROPOSITION stated
in two vocabularies — which is exactly the analogy the agent acquired.

### (a) SHAPE antecedent

Source: `domains/invariant_representation.py`, rule
`characterize_by_invariant_relations_among_parts`, if-clauses:
- IF1: "object instances are related by a transformation group that shifts and
  scales the absolute coordinates of every part"
- IF2: "the absolute coordinate values of the parts are non-invariant under the
  transformation group"

Structure asserted: ∃ over the instances a transform whose action on every part is
(shifts AND scales) that part's absolute coordinate; AND the absolute coordinate
values are NOT invariant under the group.

```json
{
  "type": "And",
  "items": [
    {
      "type": "Exists",
      "source": {"type": "Holds", "concept": "instances_of_object", "node": null, "node2": null},
      "var_name": "part",
      "predicate": {
        "type": "And",
        "items": [
          {"type": "Holds", "concept": "shifts_absolute_coordinate", "node": {"type": "Var", "name": "part"}, "node2": null},
          {"type": "Holds", "concept": "scales_absolute_coordinate", "node": {"type": "Var", "name": "part"}, "node2": null}
        ]
      }
    },
    {"type": "Not", "arg": {"type": "Holds", "concept": "invariant_under_transformation_group",
                             "node": {"type": "Holds", "concept": "absolute_coordinate_values", "node": null, "node2": null}, "node2": null}}
  ]
}
```

`shape_of_term(SHAPE antecedent) = {recursion: structural, order_n: 4, abstraction: parametric}`

### (b) FRAME antecedent

Source: `surface_feature_representation_frame` text (verbatim from iter-19/21):
- "a change of talker or accent SHIFTS and SCALES the measured feature values even
  when the spoken word is the same"
- "The values vary with the talker; they are NON-INVARIANT to the speaker."
- (over instances of the same word spoken by different talkers)

Structure asserted: ∃ over the instances [same word, diff talkers] a transform
[talker/accent] whose action on every measured feature is (shifts AND scales) that
feature's absolute value; AND the absolute feature values are NOT invariant to the
speaker.

```json
{
  "type": "And",
  "items": [
    {
      "type": "Exists",
      "source": {"type": "Holds", "concept": "instances_same_word_diff_talkers", "node": null, "node2": null},
      "var_name": "feature",
      "predicate": {
        "type": "And",
        "items": [
          {"type": "Holds", "concept": "shifts_absolute_feature_value", "node": {"type": "Var", "name": "feature"}, "node2": null},
          {"type": "Holds", "concept": "scales_absolute_feature_value", "node": {"type": "Var", "name": "feature"}, "node2": null}
        ]
      }
    },
    {"type": "Not", "arg": {"type": "Holds", "concept": "invariant_to_speaker",
                             "node": {"type": "Holds", "concept": "absolute_feature_values", "node": null, "node2": null}, "node2": null}}
  ]
}
```

`shape_of_term(FRAME antecedent) = {recursion: structural, order_n: 4, abstraction: parametric}`

### Faithfulness audit (why this is not the donkey)

- The concept names differ in each tree (`instances_of_object`/`part`/
  `absolute_coordinate` vs `instances_same_word_diff_talkers`/`feature`/
  `absolute_feature_value`) — they are NOT copy-pasted; each names what ITS prose
  names. `shape_of_term` ignores concept-name strings, so faithfulness lives in the
  TREE STRUCTURE, which is derived clause-by-clause from each text.
- Both texts genuinely assert the SAME logical shape: `And( Exists(instances, x,
  And(shifts(x), scales(x))), Not(invariant(absolute_values)) )`. The two trees
  classify to the same Shape because they ARE the same proposition — the acquired
  analogy — not because they were forced equal.
- **Discriminance control** (in the script): a genuinely different structure — a
  flat cancel tree `Minus(formant_value, mean_formant_value)`, shape
  `{structural, 2, concrete}` — does NOT subsume the re_represent shape
  (`shapes_compatible(cancel, shape_donor) = False`). So the matcher distinguishes a
  cancellation from a re-representation; it is not "any-vs-any". (The reverse,
  `shapes_compatible(shape_donor, cancel) = True`, is the documented subsumption
  semantics — the rich donor subsumes the poorer target — reported honestly below.)

---

## (3) Does the structural matcher fire? — YES

```
shapes_compatible(shape_donor, frame)  = True
shapes_compatible(frame, shape_donor)  = True
```

Both directions are compatible here because the two faithful trees have the SAME
shape `{structural, 4, parametric}`. The matcher fires where the lexical conjunction
did not.

Honesty note on the matcher's direction: `shapes_compatible` is subsuming — the
re_represent donor (`order_n=4, parametric`) is compatible with ANY simpler target
it subsumes (the cancel control: `shapes_compatible(shape_donor, cancel)=True`).
This is the documented Cousot "candidate could produce target" semantics, not a rig;
it means the structural match is **necessary-and-permissive**, and the re_represent
donor will fire on the frame because the frame's structure is within what the donor
subsumes. The SIMPLER trees do NOT fire on the richer one
(`shapes_compatible(cancel, shape_donor)=False`).

---

## (4) THE TEST (verbatim) — does `synthesize_gaps` now derive the relational gap?

Run over `surface_feature_representation_frame`, `prune=False`, `max_order=3`.

### LEXICAL transfer (iter-21: `match_mode='all'`) — 0 re_represent gaps

```
n gaps surfaced: 4
  [partition  ]  transitional probability / word-scale chunking / statistical segmentation / n-gram boundary
  [cancel     ]  speaker normalization / formant ratio / vocal-tract-length normalization / f2/f1
  [cancel     ]  coarticulation predict-remove / context normalization / carryover removal
  [partition  ]  unsupervised-clustering / cross-speaker-clustering / cross-speaker
>>> change-side (re_represent) gaps surfaced: 0
```

(Byte-identical to iter-21's preserve-only output — confirmed by re-running
`scripts/jabberwock_acquires_shape.py`.)

### STRUCTURAL transfer (iter-22: `match_mode='shape'`) — 1 re_represent gap DERIVED

```
(re_represent donor lifted to structural: 1; target_shape={recursion: structural, order_n: 4, abstraction: parametric})
n gaps surfaced: 5
  [partition  ]  transitional probability / word-scale chunking / statistical segmentation / n-gram boundary
  [cancel     ]  speaker normalization / formant ratio / vocal-tract-length normalization / f2/f1
  [cancel     ]  coarticulation predict-remove / context normalization / carryover removal
  [partition,re_represent]  represent / object / invariant / relations / among / parts / relative / arrangement
  [partition  ]  unsupervised-clustering / cross-speaker-clustering / cross-speaker
>>> change-side (re_represent) gaps surfaced: 1
```

THE NEW (re_represent) GAP, verbatim:

```
capability_keys = ['represent', 'object', 'invariant', 'relations', 'among', 'parts', 'relative', 'arrangement']
via_shapes      = ['rule_derived__characterize_by_invariant_relations_among_parts']
source_concepts = ['characterize_by_invariant_relations_among_parts']
gap             = represent the object by the invariant RELATIONS among its parts —
                  its relative arrangement / configuration / structure — which is
                  preserved under the transformation group and is invariant by
                  construction, rather than by the parts' absolute coordinate values
```

The consequence is the agent's own acquired shape (invariant theory / Erlangen),
transferred onto the perceptual frame by STRUCTURE — the consequence text is not
authored here; it is the then-clause of the rule the agent acquired in iter-21.

---

## (5) VERDICT — the last link closes

The acquired shape FIRES on the perceptual frame (structurally, where lexically it
could not), and the agent DERIVES the relational representation it could not derive
in iter-21. The four preserve-side gaps from iter-21 are unchanged; the re_represent
gap is ADDED — the change-side move that was previously unreachable is now reachable.

Reproduce:
```
python scripts/jabberwock_shape_based_transfer.py     # the iter-22 test
python scripts/jabberwock_acquires_shape.py           # the iter-21 byte-identical baseline
```

### Honest scope / caveats

- The structural match is PERMISSIVE in the subsumption direction (a rich donor
  subsumes poorer targets). The re_represent gap fires because the frame's structure
  is within the donor's subsumption, not because the two trees are byte-identical;
  the discriminance control shows a simpler structure does not subsume the richer
  one. A finer matcher (e.g. requiring shape EQUALITY, or a richer lattice than the
  three coarse axes) is a future refinement — the current axes are coarse
  (recursion/order_n/abstraction), so order_n=4 is reached by both the
  Exists+And+Not nesting here regardless of the specific concepts.
- The two faithful Term-trees are authored at the world-adapter boundary FROM each
  side's existing prose; the agent does not yet auto-compile its rule if-clauses /
  frame text into Term-trees. That compilation (prose → Term-tree) is the next
  no-donkey rung: today the structure is read faithfully by hand from the text,
  the matcher decides, the agent derives.
- All four required suites green (32 passed). `test_implication_harvester.py` has
  one PRE-EXISTING failure (`test_harvest_excludes_the_speech_science_postulates`,
  a `determinant` exclusion assertion) that fails identically on the iter-21
  baseline and is unrelated to these changes (7/8 pass).
- Not committed — results + this doc left in the working tree per instruction.
```
