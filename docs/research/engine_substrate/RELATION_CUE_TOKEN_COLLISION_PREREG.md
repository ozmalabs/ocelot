# RELATION_CUE TOKEN COLLISION — PREREG

Base `main` at `e3bb0b6` ("Merge author-signature-axis-anchor: fix axis-anchor
false-positive, GO"), re-verified with `git log --oneline -1 main` immediately before
branching. Worktree `/home/matt/ozmadev/ocelot-worktrees/relation-cue-token-collision`,
branch `relation-cue-token-collision`.

Continues the same-day arc under `docs/research/engine_substrate/`. The just-merged
`AUTHOR_SIGNATURE_AXIS_ANCHOR_RESULTS.md` fixed `_shared_shape`'s positional-pairing bug
by anchoring on `RelationCue` IDENTITY instead of list position, and explicitly named
the vocabulary's own token reuse ("the 52 cues reusing tokens like `"to"`/`"NEW"`/
`"PART"` across unrelated relations") as a SEPARATE, orthogonal question, out of scope
for that rung. The creator's charter for this rung, verbatim: *"spike the relation cue
token collisions next — does this mean that existing data needs reconciliation? getting
a better process is far more important than avoiding work."*

---

## 1. The question, restated precisely

`seeds/relation_vocabulary.json` holds 52 `RelationCue` nodes, each
`{name, keywords, relation}`, where `relation` is a 2-to-4-element tuple mixing
lowercase literal words (predicates/prepositions: `to`/`by`/`of`/`from`/`as`/`into`/
`is`/`over`/`select`/`when`/`with`) and UPPERCASE argument/slot-role placeholders
(`NEW`/`SELF`/`PART`/`PRIOR`/`GOAL`/...). Many of these tokens are reused across
UNRELATED cues. Four questions, each gating the next:

1. Is the collision LIVE anywhere beyond the already-fixed `_shared_shape` site?
2. Is each colliding token's reuse semantically ACCIDENTAL or INTENTIONAL (a genuinely
   shared abstract role)?
3. Does reconciliation, if warranted, touch data beyond `relation_vocabulary.json`
   itself (other seeds, already-installed graph state)?
4. What is the right fix shape, per finding: (a) rename accidental collisions in the
   seed file, (b) leave intentional collisions alone, (c) fix a live comparison site
   that is broken by the collision (mirroring `_shared_shape`'s own fix)?

---

## 2. The full census (registered before classification)

Total `RelationCue` nodes: 52. Total distinct tokens across all `relation` tuples: 134
(63 uppercase, 71 lowercase). Colliding tokens (appearing in >=2 DIFFERENT cues'
`relation` tuples): 22 uppercase, 11 lowercase (33 total); 41 uppercase tokens are
unique to one cue.

**Uppercase (role placeholder) tokens, by cue-count descending:**

```
PART: 6 cues -> grow_library, invariant_under, map_part_to_part, position_buffer, repeat, sequence_order
SELF: 5 cues -> adopt_winner, bounded, control_agency, self_reference, vary_self
VARIANT: 4 cues -> dispatch_variant, embed_variant, structural_edit_variant, vary_acting_gradient
COLLAPSE: 3 cues -> collapse_watch, grounding_escalate, imagine_counterfactual
GOAL: 3 cues -> comprehend_directive, decompose_subgoal, relevance_match
NEW: 3 cues -> attention_watch, build_from_prior, self_reference
PARTS: 3 cues -> compose_whole_object, detect_contact, pairwise
ACTING: 2 cues -> structural_edit_variant, vary_acting_gradient
AUDIENCE: 2 cues -> audience_produce, communicate_action
CANDIDATE: 2 cues -> expected_utility_decision, self_correct_action
CONTACT: 2 cues -> detect_contact, type_invariant
CONTENT: 2 cues -> find_target_directive, source_recognition
DIVERGENCE: 2 cues -> collapse_watch, self_correct_action
IDENTITY: 2 cues -> allograph_select, identity_to_form
ITEM: 2 cues -> bind_to_slot, iterate_each
POSITION: 2 cues -> position_buffer, spatial_gradient
PRIOR: 2 cues -> build_from_prior, reduce_uncertainty
TARGET: 2 cues -> constrain_target_directive, find_target_directive
TRIAL: 2 cues -> hypothesis_test, judge_outcome
TURN: 2 cues -> accumulate, move_toward
UTTERANCE: 2 cues -> audience_produce, communicate_action
WHOLE: 2 cues -> compose_whole_object, control_agency
```

**Lowercase (literal predicate/preposition) tokens, by cue-count descending:**

```
to: 8, by: 7, from: 4, of: 4, as: 3, into: 3, is: 2, over: 2, select: 2, when: 2, with: 2
```

Reproduce: `python3 -c "import json,collections; d=json.load(open('seeds/relation_vocabulary.json')); ..."`
(full reproduction in `RELATION_CUE_TOKEN_COLLISION_RESULTS.md` §1).

**Verified separately, load-bearing for Q1/Q4:** zero FULL relation TUPLES are
duplicated across cues (every cue's complete 4-tuple is unique). This means any
comparison keyed on the WHOLE tuple (not sub-tuple/token slices) is *already*
cue-identity-anchored by construction — the risk is specifically in comparisons that
slice/zip PART of a relation row against another row, the same failure shape
`_shared_shape` had before its fix.

**Already checked and ruled OUT** (by the orchestrating session, before this rung):
`FunctionalRole` nodes (`seeds/shape_vocabulary.json`) are a different axis
(system-function labels: `scheduler`/`memory_store`/...), not a pre-existing home for
these argument-role placeholders.

---

## 3. Falsifiable predictions, registered before fixing/renaming

- **P1 (Q1 — a second live site exists).** `_shared_shape` was the only Python-side
  consumer found in the prior rung, but `ShapeDecode`'s Rust composer
  (`runners/dsl/src/shape_decode.rs`) implements the identical `AntiUnify`-over-
  relation-lists comparison independently (`shape_fit`), for the SAME class of
  operand (a `ShapeSignature.signature` — the pool `author_signature`/
  `math_capability_shapes.json` share). Prediction: `shape_fit` will be found to use
  RAW POSITIONAL truncate-and-zip (not axis-anchored), and a constructed repro (two
  candidate parts with IDENTICAL real `Covers`-verified coverage of a goal, one
  carrying an extra row that ACCIDENTALLY token-collides with an uncovered residual
  relation) will show DIFFERENT `shape_fit` scores for the two parts despite
  identical real structure — the same false-positive SHAPE as `_shared_shape`'s
  pre-fix P1, one layer down.
- **P2 (Q2 — a real split between accidental and intentional).** Reading each
  colliding token's cues' own `keywords` will NOT put every token in one bucket.
  Prediction: most uppercase tokens (SELF, VARIANT, COLLAPSE, GOAL, PARTS, PART, ...)
  denote a genuinely shared abstract role across their cues (correct sharing, per the
  same caution `rel2`'s pool-merge null already taught this session: de-merging a
  real shared structure is as wrong as merging an unrelated one) — but at least one
  token will show a clear SEMANTIC split (two truly different notions using the same
  English word by coincidence), falsifiable per-token against the cues' own
  `keywords`.
- **P3 (Q3 — reconciliation is not seed-file-local).** `relation_vocabulary.json`'s
  `relation` tuples are copied VERBATIM into `seeds/math_capability_shapes.json`'s
  `ShapeSignature.signature` rows (already established for 3/53 near-miss rows in
  `AUTHOR_SIGNATURE_AXIS_ANCHOR_RESULTS.md` §5). Prediction: for any token classified
  ACCIDENTAL in P2, at least one of its two colliding cues' relation tuple will be
  found embedded verbatim in `math_capability_shapes.json`, so a rename in
  `relation_vocabulary.json` ALONE would silently orphan that embedded row (make it
  stop matching its own cue) unless the embedded row is updated in the same motion.
- **P4 (fix-shape decision, registered before measuring).** GO/NO-GO bar, per option:
  - **(a) Scoped rename** of a token in `relation_vocabulary.json` (+ every seed row
    that embeds that exact tuple verbatim) is warranted IFF P2 finds the token
    ACCIDENTAL (not merely "could be read either way") AND the blast radius found
    under P3 is small enough to enumerate and migrate completely in this rung (a
    handful of rows, not dozens) — the charter's "don't shrink a real finding"
    applies to (a) only if the blast radius turns out large; a SMALL, fully-migrated
    blast radius is not an excuse to skip it either.
  - **(b) Leave alone** is the verdict for every token P2 classifies SHARED-
    INTENTIONAL, by construction — no code or data change for those tokens.
  - **(c) Fix a live comparison site** is warranted IFF P1 confirms a second live,
    exploitable site — the fix mirrors `_shared_shape`'s own cue-identity-anchoring,
    applied at whatever layer (Python or Rust) the site lives in, WITHOUT breaking
    any codebook/domain that never uses the `RelationCue` vocabulary at all (a
    regression risk unique to a SHARED scoring primitive like `shape_fit`, which
    other domains — e.g. ink stroke/substroke signatures — also route through via
    the same default `codebook_type='ShapeSignature'` pool; any fix must be checked
    against that risk explicitly, not just against the cognitive-shape domain it
    was found in).
- **A clean NO-GO on (a)/(c)** — "the census looks alarming but nothing live is
  broken and every apparent collision is correct semantic sharing" — is registered
  here as a fully acceptable outcome if that is what P1/P2 measure. This document
  does not presuppose a large reconciliation is warranted.

---

## 4. GO/NO-GO bar

**GO on (c)** iff P1 confirms live exploitability with a real repro, AND the fix
(i) eliminates the demonstrated false-positive-style inflation, (ii) is verified via
the SAME regression discipline `AUTHOR_SIGNATURE_AXIS_ANCHOR_RESULTS.md` used
(paired before/after, no new failing node id versus a baseline captured on the
UNMODIFIED engine in this same worktree), and (iii) is checked against every
non-`RelationCue` domain that shares the same scoring primitive/pool (the ink
stroke/substroke risk named in P4c above) before being called safe.

**GO on (a)** iff P2 classifies at least one token ACCIDENTAL with the cues'
own keywords as evidence, AND P3's blast radius for that token is fully enumerated
and migrated (every verbatim-embedded row updated, not just the vocabulary source),
AND a live before/after demonstration shows a concrete case that was
ambiguous/wrong before the rename and correct after.

**NO-GO on (a)/(c)** for any token/site where the evidence does not clear its own
bar above — reported as a named, accepted residual, not silently dropped.

## 5. Explicitly out of scope (restated from the charter)

- `TransferDecode`'s mechanism-transfer slot vocabulary (`Mechanism.slots[].role`/
  `cue`, `seeds/mechanism_index.json`) — a SEPARATE, independently-authored
  vocabulary, not sourced from `relation_vocabulary.json`. If Q1's audit surfaces it
  as textually adjacent (e.g. reusing a string like `"UNIT"`), that is reported as a
  named, unrelated observation, not investigated as part of this collision question.
- `analogical_thinking.py`'s own meta-shape vocabulary (`MetaShape`/`ShapePrinciple`)
  — a third, separate system; not a `RelationCue` consumer (grep-verified before this
  document was written).
- Inventing a new graph node type or vocabulary layer — only in scope if P1/P3 show
  a rename/comparison-fix is provably insufficient (not expected; would be named as a
  follow-on, per the charter, not built speculatively here).
