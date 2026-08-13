# SmEntity ↔ Concept general resolution — RESULTS

Prereg: `ENTITY_RESOLUTION_PREREG.md`, same worktree/branch, base
`main @ 6871cab`. Worktree
`/tmp/claude-1000/-home-matt-ozmadev-ocelot/34a7cd08-5eb1-42bd-af0c-eedb1125fa76/scratchpad/entity-concept-resolution`,
branch `entity-concept-resolution`. (`main` has since advanced further, to
`4dbf7a5` — a sibling rung, `can-loopy-bp`, merged while this one was in
flight; `6871cab` remains a real, verified ancestor and this rung's own
regression scope never touches loopy-BP's files.)

**Verdict, up front. GO.** `SmEntity` and CAN `Concept` are confirmed
genuinely different KINDS of thing (§1) — not the same thing under two type
tags — and the real gap was never "compare two node shapes," it was "resolve
WHOSE beliefs a discourse referent is about," a question CAN's own
population-uniform topic vocabulary (§1) makes impossible to answer from
Concept-name overlap alone. The general mechanism built is a two-rung,
Occam-ordered Rule pair (`seeds/entity_concept_correspondence.json`) that
mints an explicit `denotes` edge `SmEntity -> Microtheory`: exact name
equality first, then a native `Covers` (Set/FrozenSet subset) structural
test over precomputed name-token sets — the SAME token-containment relation
`domains/name_variant_merge.py` already uses for `SmEntity<->SmEntity` alias
merging, applied here cross-type — with an explicit ambiguity guard that
REFUSES to mint rather than guess. `domains/reasoning_can_bridge.py` is
rewired to use it. **Live-demonstrated on real `seeds/bigville_cast100.json`
data, both directions, with a surface form (surname only) the OLD
naming-convention bridge is provably unable to resolve, plus a genuine
ambiguous-surname null.** Zero new Rust Terms (checked, not assumed — the
required set-intersection/subset primitives already exist). Regression:
123/123 (112 pre-existing + 11 new), zero facility-internals diff.

---

## 0. Confidence convention

Matching this arc's own standing discipline: a claim verified by reading
source carries `file:line`. A claim backed by an actual run carries **[RUN]**
with real output.

---

## 1. What `SmEntity` and `Concept` actually are — investigation, confirmed

**[RUN]** Grepped every `SmEntity`-minting site (`domains/
situation_model_reader.py:280` `_entity`; `domains/character_tom.py:385,431`;
`domains/inference_generation.py:774`; `domains/
cognitive_disambiguation.py:368,480`; ~15 `scripts/*.py` demo sites) against
every `Concept`-minting site (287 files — confirming `REASONING_FACILITY_
BRIDGE_RESULTS.md` §1.1's own independent finding that `Concept` the node
TYPE is heavily overloaded across the whole tree).

**`SmEntity`** is an open-vocabulary, name-keyed, persistent-across-a-read
DISCOURSE REFERENT pool (`situation_model_reader.py:264-282`). Attrs are a
free-form bag — `name`, `coref_category`, arbitrary derived STATE attrs
written per predication (`is_a(glass, fragile)` → `sub.set_attr(ent,
"fragile", 1)`, `:357-359`).

**`Concept`** (the CAN sense, `worlds/bigville_can_beliefs.py:159-163`) is a
pre-authored belief-network PROPOSITION, scoped inside one believer's
`Microtheory`, carrying CAN dynamics attrs (`state`, `external_field`,
`identity_field`, `causal_influence`).

**The load-bearing fact, confirmed live, that shaped the whole design:**
`TOPIC_NAMES` (`bigville_can_beliefs.py:44-47`) is a FIXED 5-topic template —
`trust_mayor`/`claim_credible`/`world_safe`/`self_worth`/`debtor_trustworthy`
— shared by EVERY resident. **[RUN]**:

```python
>>> {r["name"] for r in cast100["residents"][:5]}  # any 5 residents
>>> [sorted(build_resident_can_mt(s, r)["concepts"].keys()) for r in ...]
# every result: ['claim_credible','debtor_trustworthy','self_worth','trust_mayor','world_safe']
```

**Every CAN Microtheory's Concept-NAME set is identical across all 100
residents.** This one fact rules out the naive "structural resolution"
design (score candidate Mts by Concept-name overlap with an entity's derived
attrs) — every Mt would score identically on name-set overlap alone. The
identity question ("whose beliefs are these") and the topic question ("which
topic is this") are answered by two STRUCTURALLY DIFFERENT kinds of
evidence, and the old naming-convention bridge's single string format
conflated them by construction. The correct correspondence is therefore
`SmEntity <-> Microtheory` (identity), composed with the ALREADY-correct
literal `attr-string <-> Concept.name` match
(`propositional_deduction._norm_attr:151-158`, unmodified — this half stays
symbolic on both sides, confirmed to have no non-degenerate structural
alternative, §1.6 of `REASONING_FACILITY_BRIDGE_RESULTS.md` already named
this exact split without separating it out explicitly).

**No comparable non-name structural attribute overlap exists between
`SmEntity` and `Resident`/`Concept`.** `Resident` carries only
`name`/`index`/`resolution_bins`/`arousal`/`effective_bins`
(`bigville_can_beliefs.py:152-157`); `Concept` carries CAN dynamics attrs;
`SmEntity` carries discourse attrs. The one piece of real, richer structure
that exists but is not on the graph is `resident["role"]` (occupation, e.g.
`"baker"`, `seeds/bigville_cast100.json`) — named here as a real future
lever, deliberately NOT used (using it would require inventing a fresh
Bigville-specific descriptor-noun convention to replace the old
naming-convention coincidence with a different one).

## 2. `domains/reasoning_can_bridge.py`'s exact naming-convention dependency — read in full

**[file:line]** `_find_mt_by_name(sub, "%s%s" % (entity, "_beliefs"))`
(pre-rewire `reasoning_can_bridge.py:69-73,110`) and `_mt_entity_name`
(`:155-167`, reverse read) are literal STRING-FORMAT lookups assuming the
deduction-side entity name is byte-identical to `resident["name"]`.

**[RUN]** Confirmed narrower than even the prior rung's own test fixtures
suggested: `worlds/bigville_can_beliefs.build_resident_can_mt` names its Mt
`f"{resident['name']}_beliefs"` using the RAW resident name. For the
synthetic fixtures (`"avery"`, `"blair"`) this is a single lowercase token
that happens to equal what a reading pipeline would produce. For REAL
`seeds/bigville_cast100.json` residents (`"Ida Ditchwater"`, `"Verity
Peaseblossom"` — two tokens, title case) the literal format needs
`entity == "Ida Ditchwater"` EXACTLY; a reading pipeline's own `SmEntity`
naming (a single lowercased token from the parsed argument, confirmed live
in §4 below: `"Ditchwater is calm."` → `SmEntity{name:"ditchwater"}`) would
never produce that string. **The old bridge was narrower than "works when
names coincide" — for any real multi-token resident name it could not have
worked AT ALL, regardless of any naming coincidence.**

## 3. Design decision — what structural signal is genuinely available

Checked against `runners/dsl/src/term.rs`, not assumed:

- **`AntiUnify`/`FixedCount` on `Set`/`FrozenSet` compute intersection and
  its cardinality** (`term.rs:3402-3416`, `:3930`) — the `shape_fit =
  FixedCount(AntiUnify(...))` idiom `ShapeDecode` already uses
  (`term.rs:900-904`). **Confirms no new Rust Term is needed for a
  set-overlap score**, though (per §1) it turned out NOT to be the right
  signal for the identity question in this corpus.
- **`Covers`/`CoversOpen` on `Set`/`FrozenSet` test SUBSET**
  (`term.rs:814-822`) — exactly the relation `domains/name_variant_merge.py`
  already uses (in Python) for its OWN `SmEntity<->SmEntity` alias-merging
  ("a surname/first-name is a TOKEN of a full name",
  `name_variant_merge.py:21-22`). This IS the right signal for the identity
  question, expressed graph-natively for the NEW cross-type
  `SmEntity<->Resident` case.
- **A frozenset-valued node attr, read via `Attr` inside a Rule's `where`
  clause, is an already-shipped, LIVE pattern** — `substrate/
  world_adapter.py:9436` (`believed_concepts`) read back inside a real rule
  (`seeds/conversation_grice.json:26`). **[RUN]** confirms this round-trips
  through the engine, not merely a Python convenience.
- **Rule effects (`Effect::AddEdge`, `runners/dsl/src/rewrite.rs:1499-1517`)
  call `graph.insert_edge` directly, with no `check_edge` call** — the SAME
  corpus-wide property `SHAPE_AUDIT.md` already found ("159/634
  rule-carrying seeds mint edges through zero Γ productions"). A Γ
  production for `SmEntity -denotes-> Microtheory` is registered in the
  seed anyway (`entity_concept_correspondence.json`'s `productions` array,
  matching the task's alternative phrasing), but this is confirmed
  **declarative only** — consistent with, not a fix to, the standing corpus
  property.

**Decision, per CLAUDE.md's own shape/rule axis:** this is Rule EXECUTION
over held name structure, not `sd_recognize` ACQUISITION — no codebook is
grown; a resident's own name is already fully known, held data. Two Rules,
Occam-ordered (`seeds/entity_concept_correspondence.json`):

1. `sm_entity_denotes_believer_exact` — `Eq(Attr(e,"name"), Attr(r,"name"))`,
   guarded `Not(Exists(...denotes...))`. The OLD naming convention, now an
   explicit graph fact via a Rule instead of a Python string format.
2. `sm_entity_denotes_believer_by_name_tokens` — fires only when (1) does
   not apply. `Covers(pattern=Attr(e,"name_tokens"),
   instance=Attr(r,"name_tokens"))` OR the symmetric direction (either name's
   token set is a subset of the other's), non-degenerate
   (`FixedCount(Attr(e,"name_tokens")) > 0`), plus an explicit AMBIGUITY
   GUARD — `Not(Exists another Resident r2 whose name_tokens also
   token-subset-match e)` — the `name_variant_merge` "no-over-merge
   discipline," applied cross-type: refuses to mint when more than one
   candidate matches.

`name_tokens` is precomputed by `reasoning_can_bridge._name_tokens_frozenset`
— **reuses `name_variant_merge._name_tokens` verbatim, no new tokenizer**,
with ONE mechanical normalization found necessary during a live smoke test
(§5): a real resident's SPACE-joined name (`"Verity Peaseblossom"`) is
normalized to the underscore convention `_name_tokens` already expects
(`"verity_peaseblossom"`) before tokenizing — `_name_tokens` itself splits
only on `_`, confirmed by reading it
(`name_variant_merge.py:83-94`) and by the exact live failure this produced
before the fix (§5).

## 4. Live demonstration — real data, real generalization, real null

`tests/test_entity_concept_resolution.py`, 11/11 passing.

**[RUN]** Grounding facts checked, not assumed
(`test_ditchwater_surname_is_unique_in_the_real_cast`,
`test_peaseblossom_surname_is_genuinely_ambiguous_in_the_real_cast`): of 100
real residents, `"ditchwater"` (Ida Ditchwater) is a unique surname;
`"peaseblossom"` is shared by 4 residents (Verity, Radella, Elowen,
Henrietta Peaseblossom).

**[RUN]** `test_old_literal_naming_convention_fails_on_a_real_multi_token_resident`:
`_find_mt_by_name(sub, "ditchwater_beliefs")` on a real, unmodified
`build_resident_can_mt(Ida Ditchwater)` returns `None` — the real Mt is
named `"Ida Ditchwater_beliefs"`. The old bridge could not have resolved
this by ANY naming coincidence.

**[RUN]** `test_live_direction1_resolves_real_resident_by_surname_only_not_full_name`:
`ig.read_and_infer(a, "Ditchwater is calm.")` mints `SmEntity{name:
"ditchwater"}` (confirmed live — the reading pipeline lowercases the parsed
argument verbatim, never the resident's own two-token record name) and
derives `is_a(ditchwater, world_safe)` via modus ponens. The NEW bridge
resolves it: `apply_inference_hits_as_can_evidence` applies real evidence to
the real `world_safe` Concept (`external_field: None -> 1.0`), and the
`denotes` edge is confirmed to have been minted by the TOKEN-SUBSET rung
specifically (`"ditchwater" != "Ida Ditchwater"`, the exact rule cannot have
fired), pointing at the real `"Ida Ditchwater_beliefs"` Microtheory.

**[RUN]** `test_live_direction1_end_to_end_moves_real_can_settled_state_by_surname`
— the headline demonstration, mirroring `REASONING_FACILITY_BRIDGE_
RESULTS.md` §1.4's own shape but on real cast data and a surface form the
old bridge could never reach: two identical pipelines differing only in
whether the bridge is applied,

```
baseline (no bridge):   world_safe settles to state = 0
with bridge (surname):  world_safe settles to state = 1
```

genuinely different settled states, confirmed direction.

**[RUN]** `test_live_direction2_writes_predications_on_the_denoting_surface_form`
— the reverse direction, on the SAME established surname correspondence: once
`"ditchwater"` denotes Ida's Mt, a settled CAN network's `can_state_as_
predications` writes `is_a(ditchwater, ...)` — the surface form the
discourse actually used — never a freshly-normalized `"ida_ditchwater"` the
reading pipeline never introduced. A held implication re-fires off that
predication, deriving a new fact keyed to the SAME surface form.

**[RUN]** `test_ambiguous_surname_refuses_to_resolve_honest_null` — with BOTH
"Verity Peaseblossom" and "Radella Peaseblossom" real, unmodified CAN
networks built, `apply_derived_fact_as_can_evidence(a, "peaseblossom",
"world_safe")` returns `{"applied": False, ...}` — the ambiguity guard
refuses to mint a `denotes` edge rather than guess which Peaseblossom is
meant. **This is the mechanism's own no-over-merge discipline functioning,
not a missing case** — it is exactly the honest behaviour
`domains/name_variant_merge.py`'s own docstring calls "no-over-merge" for
its intra-type analogue, now confirmed to hold for the cross-type case too.

## 5. An operational finding along the way, reported not smoothed over

**[RUN]** The first version of the token-subset rule was tested against a
real two-token resident name (`"Verity Peaseblossom"`) and silently produced
**zero** correspondence — `Covers(e_tokens, r_tokens)` evaluated `False` even
though the surname token was genuinely present. Root cause, found by direct
`native.evaluate` inspection (not guessed): `name_variant_merge._name_tokens`
splits ONLY on `_` (`name_variant_merge.py:83-94`); a real, space-joined
Bigville resident name (`"Verity Peaseblossom"`) survived tokenization as
ONE token, `"verity peaseblossom"` (lowercased, space intact), never
`{"verity","peaseblossom"}`. Fixed by normalizing whitespace to underscore
BEFORE calling the reused tokenizer
(`reasoning_can_bridge._name_tokens_frozenset`) — a one-line mechanical
convention bridge between two facilities' different raw name formats (an
`SmEntity`-style name is already underscore-joined; a raw
`bigville_cast100.json` record name is space-joined), not a change to
`name_variant_merge.py` itself. **Reported here as a reusable operational
fact**: any future cross-facility reuse of `_name_tokens` against a
NON-`SmEntity`-sourced name string needs the same normalization.

**[RUN]** Separately, the worktree's own environment needed two of this
project's own documented mechanisms to produce a trustworthy baseline before
any of the above could be trusted: the `data/` symlink convenience
workaround (`DEDUCTION_GENERALIZATION_RESULTS.md` §7.1, undocumented in a
fresh `git worktree add` since it is gitignored-by-convention but not
actually excluded — confirmed live: `git check-ignore` returns no match, so
it is a MANUAL step, not automatic) and `domains.engine_provenance.
ensure_tree_engine()`/`build_is_stale()` (`engine_provenance.py:124-165,
432+`, the project's own sanctioned "PROTOCOL §10/§11" mechanism for giving a
fresh worktree a source-consistent compiled engine). Without both, 20 tests
across `test_deduction_generalization.py`/`test_inference_generation.py`
failed for reasons entirely UNRELATED to this rung's code (missing WordNet/
corpus data, and — before `ensure_tree_engine()` was called —an
unconfirmed engine/source pairing). **Reported as a reusable operational
fact for the next rung that opens a fresh worktree**, exactly the shape
`REASONING_FACILITY_BRIDGE_RESULTS.md` §1.5 already reported for its own
engine-level finding.

## 6. Regression — facility internals untouched, confirmed by diff

**[RUN]**:

```
$ git status --short
 M domains/reasoning_can_bridge.py
?? docs/research/engine_substrate/ENTITY_RESOLUTION_PREREG.md
?? docs/research/engine_substrate/ENTITY_RESOLUTION_RESULTS.md
?? scripts/_entity_resolution_smoke.py
?? seeds/entity_concept_correspondence.json
?? tests/test_entity_concept_resolution.py
?? tools/build_entity_concept_correspondence_seed.py
```

(`data` is the local, gitignored-by-convention-but-not-by-pattern `data/`
symlink workaround, §5 — not committed.)

```
$ git diff --stat main -- domains/propositional_deduction.py \
    domains/inference_generation.py domains/situation_model_reader.py \
    domains/name_variant_merge.py seeds/inference_logical.json \
    seeds/can_native_reimplementation.json seeds/can_decay_identity.json \
    worlds/bigville_can_beliefs.py runners/dsl/src/can_ops.rs runners/dsl/src/term.rs
(empty output)
```

Also asserted as a standing regression guard:
`test_source_audit_no_facility_internals_edited`
(`tests/test_entity_concept_resolution.py`), and
`test_name_tokens_reused_not_reimplemented` (confirms the tokenizer really is
`name_variant_merge`'s own, not a parallel implementation).

**Pre-registered regression suite (the prior rung's own set), before and
after this rung's changes — identical, 112/112 passed both times, PLUS the
11 new tests, 123/123 total ([RUN], no paired failures to report):**

```
$ PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
    tests/test_deduction_generalization.py tests/test_deduction_extension.py \
    tests/test_inference_generation.py tests/test_blob_edge_analogy_extension.py \
    tests/test_analogical_relative_ranking.py tests/test_can_native_reimplementation.py \
    tests/test_bigville_can_integration.py tests/test_can_identity_nudge_final.py \
    tests/test_reasoning_facility_bridge.py tests/test_entity_concept_resolution.py \
    -q -p no:randomly
123 passed in 89.31s
```

New test file alone:

```
$ PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
    tests/test_entity_concept_resolution.py -q -p no:randomly
11 passed in 2.65s
```

`tests/test_reasoning_facility_bridge.py` (the ORIGINAL bridge test file,
unmodified) alone, confirming the rewire is byte-behavior-compatible with
every pre-existing assertion including the two honest-miss message-substring
checks:

```
$ PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
    tests/test_reasoning_facility_bridge.py -q -p no:randomly
10 passed in 2.44s
```

---

## 7. What this rung does NOT establish

1. **Not general cross-domain coreference.** Only NAME-STRUCTURE-based
   identity resolution (exact match, then token containment). A definite
   description with zero lexical overlap with the resident's own name (`"the
   shopkeeper"`, no name token in common) is NOT resolved by this mechanism —
   it needs a different signal (e.g. `resident["role"]`, named in §1 as a
   real future lever, deliberately not built here to avoid trading one
   Bigville-specific coincidence for another).
2. **The attr-string <-> Concept.name correspondence stays a literal
   match**, unchanged from the old bridge — confirmed in §1 to be the
   CORRECT design (both facilities' topic vocabulary is inherently symbolic
   on both sides; there is no non-degenerate structural alternative at that
   grain), not an oversight.
3. **Not a fix to the corpus-wide "rule effects bypass `check_edge`"
   property** (§3) — the Γ production registered here is declarative,
   consistent with the standing (imperfect) corpus convention, not a new
   enforcement mechanism. `SHAPE_AUDIT.md`'s finding stands unchanged.
4. **The ambiguity guard is a REFUSAL, not a disambiguation.** A genuinely
   ambiguous surname (§4's Peaseblossom case) is correctly left unresolved,
   not resolved to "the most likely" candidate — no ranking/salience
   mechanism was built to break such ties (a real, deliberately unbuilt
   extension; CAN's population-uniform Concept-name vocabulary, §1, could
   not supply a tie-break signal anyway).
5. **`run_rules(2000)`'s starvation risk on a FULL WorldAdapter boot is
   named, not tested** — `_run_correspondence` is exercised here only on the
   SAME minimal harness the prior rung's own tests use (a handful of
   explicitly-loaded seeds, not a 600+-seed boot). `REASONING_FACILITY_
   BRIDGE_RESULTS.md` §1.5's own cross-seed starvation finding is a real risk
   for this mechanism too on a full boot, not yet measured here.
6. **No standing caller exercises either bridge direction on a full
   WorldAdapter today** — same honest shape the prior rung's own §1.6/§2.4
   already reported for itself, unchanged by this rung.
7. **Synthetic-proven mechanism ≠ benchmark value, per house standard**:
   every number above is a mechanism demonstration (does the general
   resolution correctly resolve/refuse on real data), not a coverage/accuracy
   claim over the full 100-resident corpus or any external benchmark.

---

## 8. Reproduce

```bash
cd /tmp/claude-1000/-home-matt-ozmadev-ocelot/34a7cd08-5eb1-42bd-af0c-eedb1125fa76/scratchpad/entity-concept-resolution

# fresh-worktree setup this rung needed (sec5) -- not part of the mechanism,
# but needed to trust any number below
ln -s /home/matt/ozmadev/ocelot/data data
PYTHONPATH=".:runners/dsl/python" python3 -c \
  "from domains import engine_provenance as ep; ep.ensure_tree_engine()"

# regenerate the seed from its builder (deterministic, one-off tool script)
python3 tools/build_entity_concept_correspondence_seed.py

# the new mechanism's own tests (all 5 live demonstrations + 2 grounding
# facts + regression guards)
PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_entity_concept_resolution.py -q -p no:randomly

# the prior rung's own bridge tests, unmodified, still green
PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_reasoning_facility_bridge.py -q -p no:randomly

# full pre-registered regression set
PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_deduction_generalization.py tests/test_deduction_extension.py \
  tests/test_inference_generation.py tests/test_blob_edge_analogy_extension.py \
  tests/test_analogical_relative_ranking.py tests/test_can_native_reimplementation.py \
  tests/test_bigville_can_integration.py tests/test_can_identity_nudge_final.py \
  tests/test_reasoning_facility_bridge.py tests/test_entity_concept_resolution.py \
  -q -p no:randomly

# throwaway smoke script used during development (kept for citability, not
# part of the shipped test suite -- mirrors REASONING_FACILITY_BRIDGE_
# RESULTS.md's own scripts/_reasoning_bridge_lowrank_probe.py precedent)
PYTHONPATH=".:runners/dsl/python" python3 scripts/_entity_resolution_smoke.py
```
