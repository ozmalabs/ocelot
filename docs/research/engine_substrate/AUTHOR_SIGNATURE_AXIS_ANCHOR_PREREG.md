# `author_signature` AXIS-ANCHORING — PREREG

Base `main` at `6805175` ("Merge shape-kind-field-spike: kind field for shape-bearing
nodes, NO-GO"), re-verified with `git log --oneline -1 main` immediately before
branching. Worktree `/home/matt/ozmadev/ocelot-worktrees/author-signature-axis-anchor`,
branch `author-signature-axis-anchor`.

Continues the same-day arc under `docs/research/engine_substrate/`. This rung is a
**direct bug fix**, not a research spike: `SHAPE_KIND_FIELD_RESULTS.md` §2.2 (P2b)
already measured the defect live. This document registers what "fixed" means precisely
and what the two before/after demonstrations must show, so the fix isn't graded by its
own after-the-fact narrative.

---

## 1. The bug, restated precisely

`author_signature` (`domains/reflective_faculty.py:7112-7134`) builds a `Concept`'s
structural signature by scanning the held `RelationCue` vocabulary
(`seeds/relation_vocabulary.json`, 52 nodes) **in seed-declaration order** and appending
each cue's `relation` tuple whose `keywords` fire in the concept's definition text. The
output list's **position** is an accident of scan order intersected with which cues
happened to fire for *this* concept — it carries no cross-concept meaning.

`_shared_shape` (`:7137-7154`) then compares two such signatures by **raw list
position**: `n = min(len(sig_a), len(sig_b))`, then `AntiUnifyWitness` over
`sig_a[:n]` vs `sig_b[:n]` row-by-row. Two concepts whose *different* fired cues happen
to land at the same index are compared as if they were the same axis.

Measured repro (`SHAPE_KIND_FIELD_RESULTS.md` §2.2, `scripts/shape_kind_probe.py`):
self-reference/recursion concept vs symmetry concept (no genuine shared structure) →
`fixed (shared leaves) = 1`, because both concepts' row-0 relation tuple happens to
place the placeholder token `"to"` at column-index 2.

This is consequential: `learn_term_for_concern` (`:1074-1158`) and `_run_math_bridge`
(`:7416-7489`) both call `_shared_shape` and `Argmax` over its `fixed` score to decide
which term-family / faculty a concern or a math connects to — a real agent decision.

---

## 2. What "fixed" means for this rung (registered before code changes)

**`fixed > 0` in `_shared_shape(sig_a, sig_b)` must be true if and only if `sig_a` and
`sig_b` share at least one row that was authored from the SAME NAMED `RelationCue`** —
never merely because two *different* cues' rows happened to land at the same list
index. This is the entire correctness bar. It is the same discipline
`analogical_thinking._concept_shape_vector` already applies over its own vocabulary
(`FunctionalRole`/`ShapePrinciple`/`MetaShape`, `analogical_thinking.py:362-411`):
*"position is always the SAME axis across every concept."*

### 2.1 The wide-blast-radius finding that shapes the fix locus (read before assuming
the obvious fix)

`author_signature`'s return value is consumed FAR beyond the two named call sites.
Grepped, then read, every call site:

- `learn_term_for_concern` (`:1094`) and `_run_math_bridge` (`:7436`) — the two named
  sites, both route straight into `_shared_shape`.
- `induce_concern` (via `_act_author_concern`, `domains/conversation_action.py:454`,
  and directly in ~8 `scripts/jabberwock_*.py` self-authoring scripts) — the SD-LOOP
  dequantize/mint path (`ShapeDecode`/`sd_recognize`/`sd_mint_quantum`).
- `grow_part_library` (`:7354-7396`) — installs the raw signature verbatim as a NEW
  `ShapeSignature{kind:'authored'}.signature`, which is then loaded by
  `_load_shape_signatures` and re-enters the SAME pool `_run_math_bridge`/the composer
  read from — a compact, variable-length, unwrapped relation-tuple list is the format
  every other `ShapeSignature` in that pool already uses.
- `goal_signature_from_held_concept` (`:7312-7333`) → `compose_design_for_goal`'s beam
  composer.

`_shared_shape`, by contrast, has **exactly two callers in the whole tree**
(`grep -n "_shared_shape(" domains/*.py scripts/*.py` — both inside
`reflective_faculty.py`, both already read above).

**Consequence for the fix locus:** changing `author_signature`'s *return type* (e.g. to
a fixed 52-row `["cue:<name>", tuple-or-ABSENT]` vector mirroring
`_concept_shape_vector` exactly) would change what `induce_concern`'s SD-loop
dequantizes against, what `grow_part_library` installs as a `ShapeSignature.signature`
for every OTHER consumer of that pool to read, and what the beam composer treats as a
goal shape — none of which are the two named call sites, none of which this rung's
charter puts in scope, and all of which are format-sensitive (`SHAPE_TYPE_VOCABULARY_SPIKE.md`
§3.3's `Tuple`/`List` equal-arity rule applies to every one of them). A 52-row,
mostly-`_ABSENT` vector handed to `induce_concern`'s dequantize or installed as a
`grow_part_library` part would silently corrupt those paths' existing behaviour — the
exact "signature format zoo" `SHAPE_TYPE_VOCABULARY_SPIKE.md` §3.2 already diagnosed as
a cross-cutting risk, one rung earlier today.

**Registered decision:** `author_signature`'s return type and internal row order are
left **byte-identical** — every one of the ~10 callers outside the two named sites is
therefore untouched by construction, not by later testing. The fix lands entirely
inside `_shared_shape`, the sole, exclusive consumer for both named call sites, which
is upgraded from **positional** pairing to **cue-identity-keyed** pairing: a row from
`sig_a` and a row from `sig_b` are compared only when they are byte-identical to the
same `RelationCue.relation` tuple (i.e. they were authored from the same NAMED cue).
This satisfies the correctness bar in §2 exactly, for both operand types the two named
sites ever pass in (an `author_signature` output, a `CapabilityAxis`-residual
`[[p], ...]` list, or a seeded `math_capability_shapes.json` `ShapeSignature.signature`
— all three are, by construction, lists of raw relation tuples, so cue-identity lookup
applies uniformly to all three without a format change on any side).

This is registered as a real judgment call under the charter's own item 1 latitude
("or whether `author_signature`'s existing callers can tolerate a different but
equally axis-anchored shape") — resolved here in the strongest form: EVERY existing
caller of `author_signature` tolerates the fix trivially, because `author_signature`
itself does not change at all.

### 2.2 Known accepted residual: three seed rows with no exact cue match

Census (`seeds/math_capability_shapes.json`, all `kind in {math, faculty}` rows,
matched against `seeds/relation_vocabulary.json`'s 52 `RelationCue.relation` tuples by
exact equality): 53 total rows, **3 have no exact cue match** —
`fractal: ["bound","SELF","by","SCALE"]`, `self_similarity`: the same row, and
`order_invariant_binding: ["correspond","PARTS"]` (near-variants of the `bounded` /
`correspond_parts`-family cue templates, hand-authored directly into the seed JSON
rather than produced by `author_signature`, so they never went through the cue scan at
all). Under cue-identity-keyed pairing these 3 rows contribute no matched axis on
either side they appear — they are **excluded from the anchored comparison**, not
silently miscounted. This is the SAME "RelationCue placeholder-token reuse" family the
charter marks **explicitly out of scope** (seed-data precision, not this rung's
matching logic) — named here, not fixed, and checked in §4 to confirm it does not flip
any live decision this rung is required to preserve.

---

## 3. Falsifiable predictions, registered before touching code

- **P1 (false positive drops).** Re-running the EXACT `SHAPE_KIND_FIELD_RESULTS.md`
  §2.2 repro (self-reference/recursion concept vs symmetry concept) through the fixed
  `_shared_shape` yields `fixed == 0` (no shared cue between the two — confirmed by
  reading the cue sets: `{self_reference, build_from_prior, base_case}` vs
  `{map_part_to_part, invariant_under, repeat}`, disjoint).
- **P2 (true positive preserved).** Two concepts whose definitions both fire the SAME
  named cue (e.g. both fire `self_reference`, via a `refers to itself` / `recursion`-
  flavoured definition) still yield `fixed > 0` after the fix, and the AntiUnify
  witness includes that cue's relation tuple as shared structure.
- **P3 (the two named call sites still connect on real data).** `learn_term_for_concern`
  and `_run_math_bridge`, exercised on the SAME scenarios the existing regression
  suite (`tests/test_cost_scheduling.py`,
  `test_authored_donkey_zero_and_matches_residual_recurrence_keystone`) already pins,
  still resolve to `term_family == "residual_recurrence"` — i.e. the fix does not flip
  an existing, tested agent decision.

## 4. GO/NO-GO bar

**GO** iff P1, P2, and P3 all hold, AND the scoped regression run
(`tests/test_cost_scheduling.py`, `tests/test_nl_concern_front_door.py`,
`tests/test_compilation_cycle.py` — the three files that reference
`author_signature`/`_shared_shape`/`learn_term_for_concern` — plus a new test file for
this fix) shows no new failing node id versus a baseline run captured on this same
worktree BEFORE the code change.

**NO-GO** on any part that fails its predicate; that part is reverted, and only the
verified-safe remainder is committed. Given the bug and the fix locus are both already
measured/read (not hypothesised), a full NO-GO is not expected, but a partial one
(e.g. P3 holding with a different `shared_leaves` count than before, which is
acceptable since no test pins an exact leaf count — only the `term_family` string) is
explicitly anticipated and would not by itself be NO-GO.

## 5. Explicitly out of scope (restated from the charter)

- `RelationCue` seed data itself (the 52 cues, their placeholder-token collisions, and
  the 3 near-miss seed rows named in §2.2) — orthogonal, separate rung.
- `analogical_thinking._concept_shape_vector` / `_vocabulary_keys` — mirrored, not
  touched.
- The `kind`-field question — already NO-GO'd (`SHAPE_KIND_FIELD_RESULTS.md`),
  orthogonal to this bug per that document's own §2.2 conclusion.
- Any new Rust `Term` — this is a Python-side pairing fix over the existing
  `AntiUnifyWitness`/`FixedCount` algebra.
- Changing `author_signature`'s return contract for its ~10 non-`_shared_shape`
  callers (§2.1) — deliberately left untouched, for the reasons given there.
