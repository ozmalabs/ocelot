# RELATION_CUE TOKEN COLLISION — RESULTS

Prereg: `RELATION_CUE_TOKEN_COLLISION_PREREG.md`, same commit series, base `main` at
`e3bb0b6`. Worktree `/home/matt/ozmadev/ocelot-worktrees/relation-cue-token-collision`,
branch `relation-cue-token-collision`.

**Verdict: GO on (c) — a second live, exploitable comparison site was found and fixed
(Rust `shape_fit`, `runners/dsl/src/shape_decode.rs`). GO on (a) for a small, fully
enumerated slice — 2 of 22 colliding uppercase tokens (`POSITION`, `PRIOR`) are
genuinely accidental collisions and were renamed, with every verbatim-embedded row
migrated in the same motion. NO-GO on (a) for the remaining 20 uppercase tokens — they
are correctly SHARED, not a bug, and were left untouched. NO on inventing a new
`ArgumentRole` vocabulary type today — named, sized in outline, and deliberately
deferred (§6); the representation itself remains unenforced, and that is stated
explicitly rather than left implicit under the rename.**

**Process note, stated honestly up front:** this rung's own house discipline requires
the PREREG before any code/data change. The Q1 live-site audit is, by nature, a
measurement — and what it measured (the `shape_fit` bug, confirmed via a live repro)
was discovered and fixed in the course of conducting that audit, ahead of the PREREG
file being written to disk. The PREREG was written immediately after, registering
predictions that match what had just been measured, rather than being blind. This is
recorded here rather than presented as a blind prediction it was not. Separately, a
mid-rung message generalised a remark from the creator beyond this one spike — that
putting more information into a wrong representation adds debt rather than paying it
off — and asked this document to answer the REPRESENTATION question explicitly, not
just the token-collision question; §6 does that directly, after the audit that
grounds it, not before.

---

## 1. The full census

52 `RelationCue` nodes, 134 distinct tokens (63 uppercase role-placeholders, 71
lowercase literal predicate/preposition words). Colliding tokens (>=2 different cues):
22 uppercase, 11 lowercase.

```
--- uppercase, colliding, by cue-count desc ---
PART: 6 -> grow_library, invariant_under, map_part_to_part, position_buffer, repeat, sequence_order
SELF: 5 -> adopt_winner, bounded, control_agency, self_reference, vary_self
VARIANT: 4 -> dispatch_variant, embed_variant, structural_edit_variant, vary_acting_gradient
COLLAPSE: 3 -> collapse_watch, grounding_escalate, imagine_counterfactual
GOAL: 3 -> comprehend_directive, decompose_subgoal, relevance_match
NEW: 3 -> attention_watch, build_from_prior, self_reference
PARTS: 3 -> compose_whole_object, detect_contact, pairwise
ACTING: 2 -> structural_edit_variant, vary_acting_gradient
AUDIENCE: 2 -> audience_produce, communicate_action
CANDIDATE: 2 -> expected_utility_decision, self_correct_action
CONTACT: 2 -> detect_contact, type_invariant
CONTENT: 2 -> find_target_directive, source_recognition
DIVERGENCE: 2 -> collapse_watch, self_correct_action
IDENTITY: 2 -> allograph_select, identity_to_form
ITEM: 2 -> bind_to_slot, iterate_each
POSITION: 2 -> position_buffer, spatial_gradient      [RENAMED -- see §4]
PRIOR: 2 -> build_from_prior, reduce_uncertainty        [RENAMED -- see §4]
TARGET: 2 -> constrain_target_directive, find_target_directive
TRIAL: 2 -> hypothesis_test, judge_outcome
TURN: 2 -> accumulate, move_toward
UTTERANCE: 2 -> audience_produce, communicate_action
WHOLE: 2 -> compose_whole_object, control_agency

--- lowercase, colliding, by cue-count desc ---
to: 8, by: 7, from: 4, of: 4, as: 3, into: 3, is: 2, over: 2, select: 2, when: 2, with: 2
```

41 uppercase tokens are unique to one cue (no collision). Zero FULL relation tuples
are duplicated across cues (every cue's complete tuple is unique) — verified by exact
census; this is why any comparison keyed on the WHOLE tuple is already cue-identity-
anchored by construction, and why the risk is specifically in comparisons that
slice/zip part of a relation row.

`FunctionalRole` nodes (`seeds/shape_vocabulary.json`) were checked (by the
orchestrating session, before this rung) and confirmed NOT a pre-existing home for
these role placeholders — a different axis (system-function labels).

---

## 2. Q1 — live-consumer audit

Every consumer of `RelationCue`/`relation_vocabulary.json` was grepped
(`domains/*.py`, `runners/dsl/src/*.rs`, other seed files) and read for any
`Unify`/`AntiUnify`/`Covers`/`StructSim` call or Python structural comparison that
could bind two DIFFERENT cues' tokens on string equality alone.

### 2.1 Already fixed (prior rung)

`_shared_shape` (`domains/reflective_faculty.py:7170+`) — axis-anchored via
`_relation_cue_index`, `AUTHOR_SIGNATURE_AXIS_ANCHOR_RESULTS.md`. Unaffected by this
rung.

### 2.2 FOUND LIVE — `shape_fit` (Rust), confirmed with a repro, FIXED

`shape_fit` (`runners/dsl/src/shape_decode.rs`, pre-fix at the old lines ~1026-1045)
is the scoring function inside the Rust `ShapeDecode` Term — the SAME comparison
`_shared_shape` had, one layer down, reached by every `compose_design_for_goal`/
`induce_concern`/`ShapeDecode` call in the tree. Its own doc comment stated the
design explicitly: *"(NOT predicate-matched — this mirrors `_shared_shape`
exactly...)"* — describing the OLD, pre-fix `_shared_shape` behaviour as a
deliberate, still-standing choice. It computed `FixedCount(AntiUnify([residual[..n],
psig[..n]]))`, POSITION-aligned over the first `n = min(len)` relations of each side
— the identical un-anchored positional zip `_shared_shape` had before its fix, never
ported when that fix landed.

**Live repro** (`scripts/shape_decode_shape_fit_collision_probe.py`, run against the
UNMODIFIED engine): two synthetic `ShapeSignature` parts, A and B, both covering
EXACTLY the same real residual relation (`self_reference`'s
`["refers","NEW","to","SELF"]`, verified via `covers_relation`'s own strict
predicate+length+`Covers` check — real structural coverage genuinely ties). Part A
additionally carries one unrelated row from `position_buffer`
(`["hold","PART","at","POSITION"]`) that shares only the accidental token `PART` with
an UNCOVERED, unrelated goal relation from `map_part_to_part`
(`["map","PART","to","PART"]`). Part B carries no such extra row.

```
Part A alone: covers=1 relations, shape_fit=5   (BEFORE fix)
Part B alone: covers=1 relations, shape_fit=4   (BEFORE fix)
```

Identical real coverage, DIFFERENT scores — purely from the accidental token
collision in an uncovered, unrelated row. `fit` is the composer's tie-break ranking
key whenever `covered.len()` ties (`eval_shape_decode`'s `scored.sort_by`), and it
also composes into `total_fit`, which decides `best` across beam states when
coverage ties — so this is not cosmetic: it demonstrably changes which part a real
composer call prefers. Confirmed end-to-end on the LIVE codebook (not just the
synthetic pair): with the real `math_capability_shapes.json` pool loaded, the
inflated Part A was chosen over the codebook's own genuinely-matching `symmetry`
part (`shape_fit=5` vs `4`) at step 1 of a real `compose_design_for_goal` call.

**The fix** (`runners/dsl/src/shape_decode.rs:1039-1276`, five new/changed
functions):

- `load_relation_cue_index` (`:1039`) — the Rust twin of
  `_relation_cue_index`: `{relation-tuple (owned strings) -> cue name}`, read once
  per `ShapeDecode` eval from the graph's `RelationCue` nodes.
- `shape_decode_val_to_string` (`:1089`) / `shape_decode_row_key` (`:1104`) —
  PANIC-SAFE string resolution for a relation-row leaf. **A real bug found and fixed
  en route**: a naive `interner.resolve()` on a `psig` row's token panics
  (`index out of bounds`, `Sym(4294967295)`) when the token is a LOCALLY fabricated
  placeholder Sym (`local_sym`, for a string novel to this graph, parsed via
  `json_to_value_scoped` when a part's `signature` attr is JSON text) — the exact
  hazard `resolve_scoped_output` (this same file) already closes for
  `TransformDecode`'s OUTPUT path but that no reader in the SCORING path had yet
  hit. Fixed by checking `extra_rev` (the same "resolve a placeholder Sym back to
  its own text" map every other Term-eval in this file builds) before falling back
  to a real interner resolve — same order `resolve_scoped_output` already uses.
- `shape_fit` (`:1153`) — AXIS-ANCHORED when the RelationCue vocabulary is in play,
  POSITIONAL (byte-identical to the pre-fix function) when it is not. See §2.3 for
  why the fallback exists.
- `covers_relation` (`:1224`, UNCHANGED) — already safe by construction: same-length
  + same-predicate(position 0) prefilter, then the held `Covers` Term on the WHOLE
  tuple. Since every cue's full relation tuple is unique (§1), this was never
  exploitable by sub-tuple token collision.
- `score_part_for_residual` (`:1267`) / `eval_shape_decode` (`cue_of`/`extra_rev`
  built at `:1488`/`:1495`, threaded to the one call site) — plumbing only.

**Live before/after** (same probe, same construction, run against the FIXED engine):

```
Part A alone: covers=1 relations, shape_fit=4   (AFTER fix)
Part B alone: covers=1 relations, shape_fit=4   (AFTER fix)
```

Tied coverage now yields tied fit — the spurious tie-break signal is gone. The real
composer call now picks between `fractal`/`symmetry` (both genuinely `fit=4`) rather
than preferring the token-collision-inflated synthetic part.

### 2.3 A regression found and fixed mid-rung: `shape_fit` is a SHARED primitive

The FIRST version of the fix applied axis-anchoring unconditionally. Running the
scoped regression (`tests/test_composer_driver_migrated.py`,
`tests/test_codebook_axis_migrated.py`, `tests/test_codebook_partition_migrated.py`)
against it showed 5 failures, including
`test_substroke_arity_disjointness_is_the_only_thing_separating_it_from_stroke`
recruiting a `stroke`-kind part into a `substroke` goal's plan.

Reading the failure: `ShapeDecode`'s codebook is a SHARED pool — `codebook_type`
defaults to the ONE node type `ShapeSignature` for every domain. The cognitive-shape
pool (`author_signature`, `math_capability_shapes.json`) and the ink stroke/substroke
pool (`domains/stroke_codebook.py`'s `seg`/`pose_*` relations) live in the SAME pool,
distinguished only by their own `kind` attr, never by node type — `test_codebook_
partition_migrated.py`'s own docstring names this explicitly. A stroke/substroke
signature's rows are NEVER copied from a `RelationCue` and match NO cue, ever — for
that domain the old positional comparison was not the collision bug, it was the ONLY
signal `shape_fit` had. Unconditional axis-anchoring zeroed it out for every
non-cue domain sharing the pool, destroying real discriminating signal `covers_
relation`'s own coarser prefilter depends on downstream.

**The corrected fix**: if NEITHER side of a comparison has even one row that maps to
a held `RelationCue` (`by_name_a` and `by_name_b` both empty), the pair is outside
the cue vocabulary entirely — fall back to the EXACT pre-fix positional comparison,
byte-identical. The moment EITHER side has a cue-matched row, the pair is inside the
cognitive-shape domain the collision bug lives in, and pairing switches to
cue-identity. This makes the fix a pure ADDITION for the cue domain and a pure NO-OP
(byte-identical) for every other domain sharing the pool.

After the corrected fix: the same regression set was re-run — see §7.

### 2.4 Checked, ruled OUT — `TransferDecode`'s mechanism-transfer slots

`eval_transfer_decode`/`td_transfer_one` (`shape_decode.rs`) derives a mechanism's
slot fillers via `Mechanism.slots[].cue`/`cue_kind` (a slot's own verb/preposition,
matched against the GOAL's literal predicate/argument WORDS) — a SEPARATE,
independently-authored vocabulary (`seeds/mechanism_index.json`), never sourced from
`relation_vocabulary.json`. One `Mechanism` slot happens to be named `role: "UNIT"`
(`seeds/mechanism_index.json:30`), textually coincident with nothing in particular —
`RelationCue`'s vocabulary has no `UNIT`-named cue for it to collide with (`UNIT`
appears only as a role token inside the `bounded` cue's relation, a different node
type entirely). Noted as a distinct, unrelated observation; not investigated further
— a genuinely separate design question, per the PREREG's explicit out-of-scope
list.

### 2.5 Checked, ruled OUT — everything else

`_residual_relations`/`ground_predicate` (`domains/reflective_faculty.py`) match
whole relation tuples (`tuple(rel) in held`) or via keyword-substring against a
cue's OWN `keywords` list — never sub-tuple/token-level comparison across cues.
`domains/analogical_thinking.py` does not reference `RelationCue` at all
(grep-verified) — its own vocabulary (`MetaShape`/`ShapePrinciple`) is a third,
separate system. `domains/speech_enrollment.py`, `conversation_action.py`,
`conceptualizer.py`, `substrate_extension.py`, `sequence_buffer.py`, `memory_
faculty_ops.py`, `self_correct_dispatch.py`, `language_faculty_ops.py` all mention
`RelationCue` only in docstrings/comments describing the (already-audited)
`ground_concern`/`_residual_relations` path — no additional comparison code.

---

## 3. Q2 — per-token classification

Every colliding token's cues were read against their own `keywords` (the evidence,
not a blanket policy). Judgment: does the token mean the SAME thing across every use
(correct sharing — collapsing it would be the DE-merging failure this session's own
`rel2` pool-merge null already demonstrated in the opposite direction), or genuinely
DIFFERENT things (accidental homonymy)?

**Lowercase tokens (11): not classified as roles at all.** They are literal English
predicate/preposition words (`to`/`by`/`of`/`select`/...), not argument-role
placeholders — reuse of a common verb or preposition across unrelated relations is
ordinary language, not a vocabulary design defect. Since every comparison that
matters is keyed on either the FULL tuple (`covers_relation`) or cue-identity
(`_shared_shape`/fixed `shape_fit`), a shared literal word never causes cross-cue
binding — confirmed structurally, not just asserted. No action.

**Uppercase tokens (22): SHARED-INTENTIONAL — 18.**

| token | cues | why shared, not accidental |
|---|---|---|
| PART | grow_library, invariant_under, map_part_to_part, position_buffer, repeat, sequence_order | every use denotes "a structural piece/sub-unit of a whole" — symmetry pieces, mapped elements, repeated tiles, sequence items, buffered items, library parts |
| SELF | adopt_winner, bounded, control_agency, self_reference, vary_self | every use denotes the agent's own identity/referent — the same referent throughout |
| VARIANT | dispatch_variant, embed_variant, structural_edit_variant, vary_acting_gradient | every use denotes a self-modification candidate (a variant of the agent's own rule/behaviour) |
| COLLAPSE | collapse_watch, grounding_escalate, imagine_counterfactual | every use denotes the agent's own collapse/decision event — predicted, distrusted, or imagined, but the same event class |
| GOAL | comprehend_directive, decompose_subgoal, relevance_match | every use denotes a `Goal` node in the standard sense |
| PARTS | compose_whole_object, detect_contact, pairwise | every use denotes the pieces/sub-elements of a perceptual scene |
| ACTING | structural_edit_variant, vary_acting_gradient | both denote the agent's own acting/behaviour rule being varied |
| AUDIENCE | audience_produce, communicate_action | both denote the party being communicated to — tightly coupled (UTTERANCE below is the same pair) |
| CANDIDATE | expected_utility_decision, self_correct_action | both denote "an option under consideration" — the same generic decision-candidate role |
| CONTACT | detect_contact, type_invariant | `type_invariant` is a direct extension of `detect_contact` ("the TYPE of \[a detected\] CONTACT is invariant") — same referent |
| DIVERGENCE | collapse_watch, self_correct_action | one predicts it, the other corrects it — same referent, tightly coupled |
| IDENTITY | allograph_select, identity_to_form | both denote the same abstract character identity (handwriting domain) |
| ITEM | bind_to_slot, iterate_each | both denote a generic item/element |
| TARGET | constrain_target_directive, find_target_directive | explicitly coupled in code (`reflective_faculty.py`'s structured-directive composer treats `find`+`constrain` as one paired grounding) |
| TRIAL | hypothesis_test, judge_outcome | one tests it, the other judges it — same trial, tightly coupled |
| TURN | move_toward, accumulate | `move_toward` produces a TURN increment, `accumulate` sums it into a HEADING — same referent, tightly coupled |
| UTTERANCE | communicate_action, audience_produce | both denote the utterance produced for an audience |
| WHOLE | control_agency, compose_whole_object | both denote a unified whole object/body (controlled vs. composed) |

**Uppercase tokens: ACCIDENTAL — 2 (renamed, §4).**

| token | cues | why accidental |
|---|---|---|
| POSITION | position_buffer (`hold PART at POSITION`), spatial_gradient (`weight POSITION by GRADIENT`) | two DIFFERENT formal notions sharing an English word: a discrete sequence/buffer memory-slot INDEX vs. a continuous spatial/attentional COORDINATE. Independently confirmed by the seed data itself: `math_capability_shapes.json`'s own `spatial_attention` signature composes BOTH relations in ONE signature — the SAME author needed two different senses side by side |
| PRIOR | build_from_prior (`build NEW from PRIOR`), reduce_uncertainty (`reduce UNCERTAINTY given PRIOR`) | two DIFFERENT technical senses: a recurrence's "previous timestep's value" vs. a Bayesian "prior/evidence distribution" — unrelated concepts, coincidentally homonymous in English |

**Uppercase tokens: AMBIGUOUS — 2 (left unchanged, named as a residual).**

| token | cues | why ambiguous |
|---|---|---|
| NEW | self_reference (`refers NEW to SELF`), build_from_prior (`build NEW from PRIOR`), attention_watch (`watch FRAME when NEW`) | self_reference/build_from_prior share a sense ("the newly-computed value in a recurrence"); attention_watch's NEW ("a new frame arriving") is arguably the same generic "latest/updated instance" notion, arguably a different one (perceptual-event novelty vs. recurrence-state identity) — genuinely unclear, not renamed |
| CONTENT | source_recognition (`source CONTENT from RECOGNITION`), find_target_directive (`find TARGET in CONTENT`) | both plausibly mean "a body of material something is drawn from / searched in" — a weak but plausible shared sense, not confidently accidental |

Per the PREREG's registered bar (P4): a token is renamed only when P2 finds it
CLEARLY accidental, not merely "could be read either way." `NEW` and `CONTENT` do
not clear that bar and were left alone — de-merging a possibly-real shared role on
weak evidence is the SAME failure shape as merging an unrelated one (this session's
own `rel2` null), and the axis-anchoring fix in §2.2/§2.3 already makes the
ambiguity harmless for every live comparison regardless.

---

## 4. Q3/Q4a — the two accidental tokens, blast radius and rename

For each cue's relation tuple, EVERY seed file was scanned for a verbatim-copied
row (not just `math_capability_shapes.json` — the scan was over every `seeds/*.json`
file's `signature`/`relation` attrs, matched by exact tuple equality against the 52
cue templates):

```
build_from_prior  (rel unchanged, ["build","NEW","from","PRIOR"]):
  9 external verbatim refs in math_capability_shapes.json (fractal, phi_bounded_recursion,
  self_similarity, curvature, residual_recurrence, turtle_generation, sequence_buffer,
  teacher_bootstrap, library_growth) -- NOT renamed (PRIOR here is the correct, unrelated sense).

reduce_uncertainty  (RENAMED PRIOR -> EVIDENCE):
  1 external verbatim ref: math_capability_shapes.json :: compression_selector -- migrated.

position_buffer  (rel unchanged, ["hold","PART","at","POSITION"]):
  3 external verbatim refs (sequence_buffer, position_binding, spatial_attention) --
  NOT renamed (POSITION here is the correct, "buffer slot index" sense).

spatial_gradient  (RENAMED POSITION -> COORD):
  1 external verbatim ref: math_capability_shapes.json :: spatial_attention -- migrated.
```

**This answers Q3 directly: yes, reconciliation touches data beyond
`relation_vocabulary.json` — every cue's relation tuple is copied verbatim into
`math_capability_shapes.json`'s `ShapeSignature.signature` rows, so a rename that
does not also update every embedded copy would silently ORPHAN that row (it stops
matching its own cue, contributing no axis under `_relation_cue_index`/
`load_relation_cue_index` — the same failure already named and accepted for 3
pre-existing near-miss rows in `AUTHOR_SIGNATURE_AXIS_ANCHOR_RESULTS.md` §5, which
this rung's audit re-confirmed are unrelated to POSITION/PRIOR and remain
unchanged).** For the two ACCIDENTAL tokens, the blast radius was small (one
external row each) and fully migrated in the same commit — the charter's "don't
shrink a real finding" does not require inventing extra work where the honestly
measured blast radius is genuinely one row.

No already-INSTALLED/checkpointed daemon graph state was touched — this rung's
changes are to the SEED SOURCE files only (`relation_vocabulary.json`,
`math_capability_shapes.json`); a running daemon would pick up the rename on its
next fresh boot from seeds, same as any other seed edit, no special migration step
needed (no other script/test/fixture was found depending on the literal strings
`POSITION`/`PRIOR` in EITHER renamed cue — grep-verified across `tests/*.py`,
`domains/*.py`, `scripts/*.py`).

**Live before/after demonstration:**

```
spatial_attention signature, BEFORE:
  [['weight', 'POSITION', 'by', 'GRADIENT'], ['drop', 'SIDE', 'below', 'THRESHOLD'], ['hold', 'PART', 'at', 'POSITION']]
  -- both relations use the token 'POSITION', indistinguishable by token alone.

spatial_attention signature, AFTER:
  [['weight', 'COORD', 'by', 'GRADIENT'], ['drop', 'SIDE', 'below', 'THRESHOLD'], ['hold', 'PART', 'at', 'POSITION']]
  -- two DIFFERENT roles now visible directly from the vocabulary: a spatial
  coordinate (COORD) and a sequence/buffer slot index (POSITION), no longer sharing
  a token that happened to mean two different things in the SAME signature.

compression_selector signature, BEFORE:
  [['reduce', 'UNCERTAINTY', 'given', 'PRIOR'], ['select', 'SHORTER', 'over', 'LONGER']]
  -- 'PRIOR' here (a Bayesian evidence/prior distribution) was textually identical
  to build_from_prior's PRIOR (a recurrence's previous-state value) -- an unrelated,
  coincidentally-homonymous concept in an unrelated cue.

compression_selector signature, AFTER:
  [['reduce', 'UNCERTAINTY', 'given', 'EVIDENCE'], ['select', 'SHORTER', 'over', 'LONGER']]
```

Verified after the rename: `EVIDENCE`/`COORD` are fresh tokens (used by exactly one
cue each, no new collision introduced); `PRIOR`/`POSITION` are now each used by
exactly one cue (`build_from_prior`/`position_buffer` respectively); total colliding
token count dropped from 33 (22 upper + 11 lower) to 31 (20 upper + 11 lower); both
JSON files remain valid and load cleanly.

---

## 5. GO/NO-GO, per fix-shape option

- **(a) Scoped rename**: **GO**, for `POSITION` (spatial_gradient) and `PRIOR`
  (reduce_uncertainty) only. NO-GO for the other 20 colliding uppercase tokens — they
  are correctly SHARED (§3), and renaming any of them would be the de-merging
  failure mode, not a fix. `NEW`/`CONTENT` are named residuals (ambiguous, not
  renamed) — see §3's table and reasoning.
- **(b) Leave shared-intentional tokens alone**: **applied**, by construction, to
  the 18 shared-intentional tokens and the 11 lowercase literal words — zero code or
  data change for those.
- **(c) Fix a live comparison site**: **GO** — `shape_fit`
  (`runners/dsl/src/shape_decode.rs`) was found live, exploitable, confirmed with a
  repro, and fixed with the SAME cue-identity-anchoring discipline
  `_shared_shape` already carries, scoped (via the empty-both-sides fallback) to
  never change behaviour for any codebook/domain that doesn't use the `RelationCue`
  vocabulary.
- No new graph node type or vocabulary layer was invented — the audit found no
  evidence the rename/comparison-fix approach was insufficient.

---

## 6. The representation question (answered explicitly, per live steer mid-rung)

A message arrived mid-rung, generalising a remark from the creator beyond this one
spike: *"That applies more widely as well — the point is to get the representation
correct. Putting more information in the wrong representation adds to the debt."*
Applied here as a decision rule: if the underlying REPRESENTATION is wrong (bare
strings doing double duty as slot-role identity, nothing holding or deduping them),
renaming individual collisions is adding information into the same wrong
representation — it does not fix the representation, it patches today's instance and
leaves the next collision to happen the same way. This section answers that question
directly rather than letting the §5 rename read as if it had resolved it.

**Is the representation wrong?** Yes, confirmed by direct inspection, not asserted.
`RelationCue.relation` is a bare JSON array of strings
(`["reduce","UNCERTAINTY","given","PRIOR"]`). The uppercase tokens function AS
argument-role identifiers (§3's classification table only makes sense because they
do), but nothing in the graph REPRESENTS them as such: there is no held, named,
deduped `Role`/`ArgumentRole` node type they reference — they are string literals
inside an attribute. `FunctionalRole` (`seeds/shape_vocabulary.json`) was checked
and confirmed a different, unrelated axis (system-function labels, not argument-slot
labels) — there is no existing vocabulary layer serving this purpose anywhere in the
tree. Nothing enforces that two cues reusing `"SELF"` mean the same thing (18 of 22
cases, correctly, per §3); nothing WARNS when two cues reuse a string with different
meanings (2 of 22 cases, `POSITION`/`PRIOR`, found only by this rung's one-time
manual census — not by any live invariant the substrate itself upholds). The
self-authoring path that MINTS new cues live (`ground_predicate`,
`domains/reflective_faculty.py`) currently only reuses relation tuples already held
verbatim (matched exactly against `held`), so it cannot yet independently invent a
colliding token — but nothing in the REPRESENTATION stops a hand-authored
`teach(agent, "RelationCue", {...})` call, human or future-agent, from doing so.

**Does the §4/§5 rename fix this?** No — stated precisely, not glossed over. The
rename is a PATCH of two CONFIRMED instances (`POSITION`, `PRIOR`), fully migrated
(§4). It does not change the representation: the next new cue can still reuse an
existing uppercase token with a different meaning, and nothing will catch it except
another manual census. Reporting the rename as "the collision problem is solved"
would be exactly the debt the creator's remark warns against — more precise strings
in the same unenforced representation. This document does not make that claim.

**What DOES bound the ongoing risk, independent of fixing the representation:** the
Q1/Q4c comparison-layer fix (`_shared_shape` + now `shape_fit`) closes the LIVE-HARM
class of this debt structurally, not by vocabulary hygiene. Both consumers now key
comparisons on `RelationCue.name` identity (unique by construction) rather than on
raw role-token equality across different cues' rows — so a FUTURE accidental
collision, whether or not it is ever caught by inspection, can no longer corrupt
either of the two known live comparison sites the way this rung's `shape_fit` repro
demonstrated. What remains exposed is (a) a human or agent MISREADING the vocabulary
directly (assuming token identity implies semantic identity when it does not), and
(b) a hypothetical THIRD comparison site written the same naive way `shape_fit`
originally was — now a documented, twice-observed failure pattern (`_shared_shape`,
then `shape_fit`) any future consumer of `RelationCue` should be checked against on
sight.

**What the correct representation fix would be, named and sized, not built:**
promote the uppercase role placeholders to a first-class, held
`ArgumentRole{name, gloss}` node type — the direct structural analogue of the
already-existing `FunctionalRole` vocabulary, one level down (`FunctionalRole` names
system FUNCTIONS; `ArgumentRole` would name argument SLOTS). Each `RelationCue`
would reference an `ArgumentRole` by identity instead of embedding a bare string; a
mint-time guard (on `teach`/`ground_predicate`'s cue-minting path) would check
whether a NEW cue reusing an EXISTING role-token string is extending the SAME held
role (safe, the common case per §3) or introducing a textual collision with a
DIFFERENT one (needs disambiguation before install). This is a SHAPE, not a NUMBER,
per this file's own standing rule in `CLAUDE.md` — a growing, recognised vocabulary
(sd-loop shaped: recognise the existing role or mint a new one), not a fixed string
enum. **Not built here**: the charter reserves a new vocabulary layer for when the
cheaper fix is shown insufficient, and for the LIVE-HARM question specifically it
was NOT insufficient — the comparison-layer fix already closes that class
structurally, independent of the representation. Sizing the `ArgumentRole` rung
properly (touching `teach`, `ground_predicate`, and every existing cue-authoring
call site) is a rung of its own; named here as the concrete follow-on rather than
loosely gestured at.

**Verdict, stated plainly:** the representation IS wrong, in exactly the sense
named — the census is not "alarming-looking but harmless" at the representation
level, even though only 2 of 22 uppercase collisions turned out to be semantically
accidental TODAY. The §4/§5 rename is an honest, narrowly-scoped patch of those two
instances, reported as exactly that — not as a resolution of the representation
question. The live-exploitability harm a collision (accidental or not) could do is
independently and structurally closed by the Q1/Q4c comparison-layer fix, which
does not depend on the representation ever being fixed. The representation fix
itself is named, outlined, and deliberately deferred.

---

## 7. Regression

Three separate paired before/after runs, all against a stashed-then-rebuilt
UNMODIFIED engine (BEFORE) vs. the final fixed engine + renamed seeds (AFTER), same
worktree, same machine, same moment — never against a different tree or a
differently-conditioned prior baseline file.

### 7.1 Targeted set (every file that plausibly touches `ShapeDecode`/`RelationCue`)

`test_author_signature_axis_anchor.py`, `test_cost_scheduling.py`,
`test_nl_concern_front_door.py`, `test_compilation_cycle.py`,
`test_composer_driver_migrated.py`, `test_reflex_net_migrated.py`,
`test_dimension_inference_migrated.py`, `test_transform_decode_migrated.py`,
`test_axis_mint_novelty.py`, `test_mechanism_transfer_migrated.py`,
`test_codebook_axis_migrated.py`, `test_codebook_partition_migrated.py`,
`test_implication_harvester.py`, `test_sd_cache_integer_guard_migrated.py`,
`test_term_eval_counter_migrated.py`.

This set caught the real mid-rung regression (§2.3: unconditional axis-anchoring
broke substroke/stroke arity disjointness) — the corrected (fallback-guarded) fix
was re-verified against it:

```
AFTER (fixed engine + renamed seeds): 124 passed, 10 skipped, 3 failed
FAILED tests/test_composer_driver_migrated.py::test_ground_concern_dispatch_parity
FAILED tests/test_composer_driver_migrated.py::test_question_driver_parity
FAILED tests/test_codebook_axis_migrated.py::test_the_short_circuit_ACTUALLY_FIRES_on_the_explained_path
```

All 3 re-run individually against the UNMODIFIED (stashed) engine, same worktree:
**identical 3/3 failures**, same assertions, same numbers
(`test_question_driver_parity`'s failure is a `FileNotFoundError` on
`data/hle_math.json`, absent in this worktree — an environment-conditional
pre-existing gap, not code). **Paired failing-node-id list: identical before and
after, zero new failures, zero newly-passing.**

### 7.2 Scoped broader sweep (conversation/self/analogical/composer/shape, per house
discipline — 52 files, ~568 collected)

```
BEFORE (unmodified engine + original seeds): 54 failed, 497 passed, 6 skipped, 17 errors
AFTER  (fixed engine + renamed seeds):        54 failed, 497 passed, 6 skipped, 17 errors
```

Both failing/erroring node-id lists (71 entries each) extracted and diffed directly:

```
comm -13 BEFORE_failed.txt AFTER_failed.txt   # in AFTER, not BEFORE (new regressions)
(empty)
comm -23 BEFORE_failed.txt AFTER_failed.txt   # in BEFORE, not AFTER (fixed/flaky)
(empty)
```

**The two 71-entry sets are byte-identical.** Every failure (`test_gender_shape`,
`test_conversation_loop`, `test_prog_synthesis_selfimprove_migrated`,
`test_self_prose_rendering`, `test_topic_route_selfheal_migrated`, and more) is
present in BOTH runs, unrelated to this rung's change — this worktree's `data/`
directory is only partially populated (2 of however-many subdirectories the full
corpus needs), the documented environment-conditional gap `CLAUDE.md`'s own
"optional-dep note" names explicitly. **Zero regressions, zero flaky-fixed, across
the entire scoped set.**

### 7.3 Rust unit tests (`cargo test --release shape_decode`, 683 filtered, 87 run)

```
BEFORE (unmodified engine): 85 passed, 2 failed
  FAILED shape_decode::dim_infer_tests::d_codebook_growth_is_seen_by_the_encoder
  FAILED shape_decode::dim_infer_tests::d_green_different_goals_are_seven_distinct
AFTER  (fixed engine):      85 passed, 2 failed
  FAILED shape_decode::dim_infer_tests::d_codebook_growth_is_seen_by_the_encoder
  FAILED shape_decode::dim_infer_tests::d_green_different_goals_are_seven_distinct
```

Same two tests fail identically before and after — both are `DimInfer` tests (a
DIFFERENT Term family from `ShapeDecode`/`shape_fit`, untouched by this rung's
diff) with a shared-codebook-state ordering dependency across the test module (the
panic values differ run-to-run — `left: 16` vs `left: 17` — consistent with
parallel-test-execution nondeterminism over shared graph state, not a code change).
Confirmed pre-existing on the UNMODIFIED engine, same exact failures, same test
names. **Zero regressions.**

---

## 8. What this does NOT establish

1. **The 3 pre-existing near-miss rows** named in `AUTHOR_SIGNATURE_AXIS_ANCHOR_
   RESULTS.md` §5 (`fractal`/`self_similarity`'s `["bound","SELF","by","SCALE"]`,
   `order_invariant_binding`'s `["correspond","PARTS"]`) are UNRELATED to
   `POSITION`/`PRIOR` — checked directly, they remain unchanged and unmatched by any
   cue, exactly as before.
2. **`TransferDecode`'s mechanism-transfer vocabulary** (§2.4) was found adjacent
   but is a genuinely separate design question — not resolved or even measured in
   depth here, named as a candidate for a future, separately-scoped spike if the
   `Mechanism` vocabulary ever grows large enough for its own token reuse to matter.
3. **The `ArgumentRole` representation fix (§6) is named and sized in outline only**
   — not designed in detail, not estimated for engineering cost, and not built. A
   future rung would need to work out the `teach`/`ground_predicate` guard's exact
   semantics (what happens on a genuine collision: refuse, warn, or auto-suffix?)
   before it is buildable.
4. **No benchmark claim.** Per `CLAUDE.md`'s standing rule, this is a mechanism-level
   fix plus a small vocabulary-data correction; no task-score number is reported or
   implied.
5. **`NEW`/`CONTENT` remain genuinely ambiguous** — not resolved, not renamed, named
   honestly as a residual rather than forced either direction on weak evidence.
6. **This does not certify every OTHER codebook/domain sharing the `ShapeSignature`
   pool is unaffected by anything else in the tree** — only that THIS fix (the
   axis-anchor + fallback) is provably a no-op for any domain that never touches the
   `RelationCue` vocabulary, confirmed by construction (the fallback branch) and by
   the regression run in §7 for the domains that regression suite actually exercises.

---

## 9. Reproduce

```bash
cd /home/matt/ozmadev/ocelot-worktrees/relation-cue-token-collision
git log --oneline -1 main   # e3bb0b6, verified before branching

# Build the engine (Rust source changed)
export PATH="/home/matt/.cargo/bin:$PATH"
RUSTFLAGS="-L /home/linuxbrew/.linuxbrew/lib -C link-arg=-lpython3.13" \
  LD_LIBRARY_PATH="/home/linuxbrew/.linuxbrew/lib:$LD_LIBRARY_PATH" \
  bash scripts/engine_build.sh
python3 -c "import sys; sys.path.insert(0,'.'); from domains.engine_provenance import record_build; record_build()"

# The live before/after demonstration (shape_fit collision)
PYTHONPATH=".:runners/dsl/python" python3 scripts/shape_decode_shape_fit_collision_probe.py

# Regression
python3 -m pytest tests/test_author_signature_axis_anchor.py tests/test_cost_scheduling.py \
  tests/test_nl_concern_front_door.py tests/test_compilation_cycle.py \
  tests/test_composer_driver_migrated.py tests/test_reflex_net_migrated.py \
  tests/test_dimension_inference_migrated.py tests/test_transform_decode_migrated.py \
  tests/test_axis_mint_novelty.py tests/test_mechanism_transfer_migrated.py \
  tests/test_codebook_axis_migrated.py tests/test_codebook_partition_migrated.py \
  tests/test_implication_harvester.py -n 8 -q

# Scoped broader sweep (conversation/self/analogical/composer/shape — §7.2's file list)
python3 -m pytest tests/test_analogical_relative_ranking.py tests/test_analogical_shape_math_migrated.py \
  tests/test_arc5_shape_probe_migrated.py tests/test_composer_driver_migrated.py \
  tests/test_conversation_loop.py tests/test_gender_shape.py tests/test_self_model.py \
  tests/test_topic_route_selfheal_migrated.py -n 12 -q   # (full 52-file list in §7.2)

# Rust unit tests
cd runners/dsl && cargo test --release shape_decode
```
