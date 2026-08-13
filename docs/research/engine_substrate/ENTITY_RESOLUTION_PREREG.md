# SmEntity ↔ Concept general resolution — registered before any code change

**Status: PREREG.** Follows `REASONING_FACILITY_BRIDGE_PREREG.md`/`_RESULTS.md`'s
own methodology: mapping claims registered here, verified against real code
before being relied on, the mechanism built in a follow-on RESULTS doc.

**Charter, precisely.** `REASONING_FACILITY_BRIDGE_RESULTS.md` §1.6/§2.4 both
named the SAME open gap, twice, independently: *"This is a NAMING-CONVENTION
bridge, not general entity resolution... at minimum, an explicit
`corresponds_to`-style edge (or a coreference step) linking an `SmEntity` to
the CAN-network-bearing Microtheory it denotes... sized at roughly one new Γ
production + one new rule + a resolution convention."* This rung builds
exactly that, and rewires `domains/reasoning_can_bridge.py`'s two directions
to use it instead of the naming-convention coincidence.

**Worktree:**
`/tmp/claude-1000/-home-matt-ozmadev-ocelot/34a7cd08-5eb1-42bd-af0c-eedb1125fa76/scratchpad/entity-concept-resolution`,
branch `entity-concept-resolution`, base `main @ 6871cab` (verified via
`git log --oneline -1 main` immediately before branching — NOT the
`76b8aea`/`19fdddf` hashes named in earlier docs; a sibling rung had merged in
the meantime, confirming the task's own warning not to assume a prior hash).

**Confidence convention:** a claim verified by reading source in THIS tree
carries `file:line`. A claim backed by an actual run carries **[RUN]** with
real output.

---

## 1. Investigation, done before this doc — what `SmEntity` and `Concept` actually are

**[RUN + file:line]** Grepped every `SmEntity`-minting site (`domains/
situation_model_reader.py:280`, `domains/character_tom.py:385,431`,
`domains/inference_generation.py:774`, `domains/cognitive_disambiguation.py:
368,480`, plus ~15 `scripts/*.py` demo/authoring sites) against every
`Concept`-minting site (287 files — `Concept` the node TYPE is heavily
overloaded across acoustic/vision/CAN/meta-shape/lexicon/reading uses,
confirmed independently of `REASONING_FACILITY_BRIDGE_RESULTS.md` §1.1's own
same finding).

**`SmEntity`** (`situation_model_reader.py:264-282`, `_entity`): an
open-vocabulary, name-keyed, persistent-across-a-read entity pool. Attrs are a
free-form bag written by whichever predication touched the entity —
`name`, `coref_category`, `kind`, `salience`, plus arbitrary derived
STATE attrs (`is_a(glass, fragile)` → `sub.set_attr(ent, "fragile", 1)`,
`situation_model_reader.py:357-359`). It represents a TEXTUAL/DISCOURSE
referent — what a reading pipeline currently believes a name in the text
denotes.

**`Concept`** (in the CAN sense, `worlds/bigville_can_beliefs.py:159-163`): a
pre-authored belief-network PROPOSITION, scoped inside one believer's
`Microtheory`, carrying CAN dynamics attrs (`state`, `external_field`,
`identity_field`, `causal_influence` edges to sibling Concepts in the SAME
Mt). It represents a TOPIC a believer holds an attitude about, not a
referent.

**Finding, confirmed not assumed: these are genuinely different KINDS of
thing, not the same thing under two type tags.** `SmEntity` is
entity-grained (one node per referent); CAN `Concept` is
topic-grained-within-a-believer (one node per (believer, topic) pair, and
`worlds/bigville_can_beliefs.TOPIC_NAMES:44-47` is a FIXED 5-topic template
shared by every resident — `trust_mayor`/`claim_credible`/`world_safe`/
`self_worth`/`debtor_trustworthy` — so **every CAN Microtheory's Concept-name
SET is identical across all 100 residents**, `worlds/bigville_can_beliefs.py:
159-163`, `[RUN]` confirmed against `seeds/bigville_cast100.json`). This one
fact governs the whole design below: Concept-name overlap can never
distinguish WHICH resident's Mt an entity belongs to (every Mt has the same
five names) — the identity question ("whose beliefs are these") and the topic
question ("which topic is this") are answered by two structurally different
kinds of evidence, and conflating them was a hidden trap the naming-
convention bridge's single string format papered over.

The CORRECT correspondence is therefore not `SmEntity <-> Concept` directly —
it is `SmEntity <-> Microtheory` (the "whose beliefs" identity link) composed
with the ALREADY-established `attr-string <-> Concept.name` literal
normalization (`propositional_deduction._norm_attr:151-158`, unchanged, both
facilities already independently converge on the same lowercase-underscore
topic vocabulary — this half is inherently symbolic/nominal on both sides and
has no non-degenerate "structural" alternative; it stays a literal match, now
reached via a resolved Mt rather than a formatted string).

## 2. `domains/reasoning_can_bridge.py`'s exact naming-convention dependency

**[file:line]** `_find_mt_by_name(sub, "%s%s" % (entity, "_beliefs"))`
(`reasoning_can_bridge.py:69-73,110`) and `_mt_entity_name`
(`:155-167`, the reverse read) are STRING-FORMAT lookups: they assume the
deduction-side entity name string is EXACTLY `resident["name"]`
(case-sensitive, no tokenisation). **[RUN]** this is narrower than even the
existing test fixtures suggest: `worlds/bigville_can_beliefs.build_resident_
can_mt` names its Mt `f"{resident['name']}_beliefs"` using the RAW resident
name — for the synthetic test fixtures (`"avery"`, `"blair"`) this is a
single lowercase token and happens to equal what a reading pipeline would
produce; for REAL `seeds/bigville_cast100.json` residents (`"Verity
Peaseblossom"`, two tokens, title case) the literal format `f"{entity}_
beliefs"` would need `entity == "Verity Peaseblossom"` EXACTLY — a
reading pipeline's own `SmEntity` naming (typically a single lowercased
token from the parsed lemma) would almost never produce that string. **The
coincidence is narrower than “names happen to match” — it only worked at
all because every existing test used single-token synthetic names built to
match.**

## 3. What structural signal is genuinely available (design decision)

Checked, not assumed, against `runners/dsl/src/term.rs`:

- **`AntiUnify`/`FixedCount` on `Set`/`FrozenSet` values compute set
  INTERSECTION and its CARDINALITY** (`term.rs:3402-3416` intersection;
  `term.rs:3930` `Value::Set(s)|Value::FrozenSet(s) => s.len()`) — this is
  literally the `shape_fit = FixedCount(AntiUnify(...))` idiom `ShapeDecode`
  already uses (`term.rs:900-904`), reusable verbatim for a set-overlap
  score. **Already established as computable WITHOUT a new Rust Term** — the
  task's own out-of-scope condition is satisfied by inspection.
- **`Covers`/`CoversOpen` on `Set`/`FrozenSet` test SUBSET** (docstring
  `term.rs:814-822`: "a Set/FrozenSet requires the pattern be a SUBSET of the
  instance") — the exact relation `domains/name_variant_merge.py`'s own
  ALREADY-SHIPPED, ALREADY-GENERIC name-token containment check needs
  (`"a surname/first-name is a TOKEN of a full name"`, `name_variant_merge.py:
  21-22`), just expressed natively instead of as a Python `set <=` (that
  module still does the subset test in Python — `_cluster`, `:227-333` — this
  rung is a chance to do the ANALOGOUS cross-type check graph-natively, per
  CLAUDE.md's own rule that a decision ranging over graph state belongs in a
  Rule).
- **A frozenset-valued node ATTR, read via `Attr` inside a Rule's `where`
  clause, is an already-shipped, already-live pattern** — `substrate/
  world_adapter.py:9436` (`set_attr(ad, "believed_concepts",
  frozenset(believed))`) is read back inside a real seed rule's `where`
  (`seeds/conversation_grice.json:26`, `"container": {"type": "Attr", ...,
  "key": "believed_concepts"}`). **[RUN]** confirms this round-trips through
  the engine today, not merely a Python-side convenience.
- **No comparable non-name structural attribute overlap exists between
  `SmEntity` and `Resident`/`Concept`** — `Resident` (`bigville_can_beliefs.py:
  152-157`) carries only `name`/`index`/`resolution_bins`/`arousal`/
  `effective_bins`; `Concept` carries CAN dynamics attrs; `SmEntity` carries
  discourse attrs. The one piece of REAL, richer world structure that exists
  but is NOT currently written onto the graph is `resident["role"]`
  (occupation, `seeds/bigville_cast100.json`, e.g. `"baker"`) — using it would
  require inventing a new SmEntity-side descriptor-noun convention not
  supplied by any existing facility, so it is named here as a possible FUTURE
  lever and NOT used in this rung's mechanism (avoids inventing a fresh
  Bigville-specific coincidence to replace the old one).

**Decision:** the correspondence is `SmEntity <-> Microtheory` identity
resolution, decided by NAME-TOKEN structure (a `Rule`, not a Python `if`),
mirroring `rule_mention_resolves_to_concept`'s (`seeds/intent.json:854-914`)
existing exact-match precedent for the base case and generalising it with a
`Covers`-based token-subset rung for the case the base case cannot reach —
**this is Γ/Rule EXECUTION over held name structure, not `sd_recognize`
acquisition** (no codebook is being grown; a resident's own name is already
fully known, held data — CLAUDE.md's "shape is acquisition, rule is
execution" axis places this on the RULE side). A Γ production for the
resulting `denotes` edge is registered too (`SmEntity -denotes->
Microtheory`), matching the task's alternative phrasing — **checked [RUN]
that this is DECLARATIVE only**: `runners/dsl/src/rewrite.rs:1499-1517`
(`Effect::AddEdge`) calls `graph.insert_edge` directly, with NO `check_edge`
call — the SAME corpus-wide property `SHAPE_AUDIT.md` already found
("159/634 rule-carrying seeds mint edges through zero Γ productions"), not
introduced or fixed by this rung.

## 4. The mechanism, precisely

New seed `seeds/entity_concept_correspondence.json`, two rules mining a
`denotes` edge `SmEntity -> Microtheory`:

1. `sm_entity_denotes_believer_exact` — `Eq(Attr(e,"name"), Attr(r,"name"))`,
   guarded by `Not(Exists(...denotes...))`. This is the OLD naming-convention
   case, now an explicit graph fact instead of a Python string format.
2. `sm_entity_denotes_believer_by_name_tokens` — fires only when rule 1 does
   not apply. `Covers(pattern=Attr(e,"name_tokens"), instance=Attr(r,
   "name_tokens"))` OR the symmetric direction (token SUBSET either way,
   the `name_variant_merge` containment relation, natively), non-degenerate
   (`FixedCount(Attr(e,"name_tokens")) > 0`), and an EXPLICIT ambiguity guard
   — `Not(Exists another Resident r2 whose name_tokens also satisfy the
   subset test)` — refusing to mint when more than one candidate matches
   (the `name_variant_merge` "no-over-merge discipline" precedent, applied
   cross-type). `name_tokens` is a frozenset attr mechanically precomputed
   (reusing `domains.name_variant_merge._name_tokens` — no new tokenizer) on
   `SmEntity`/`Resident` nodes before the rules run — mechanical I/O per
   CLAUDE.md, the decision itself stays in the `Covers`/`Not(Exists)` Term
   tree the Rule evaluates.

`domains/reasoning_can_bridge.py` is rewired: `apply_derived_fact_as_can_
evidence`/`can_state_as_predications` resolve the Mt (forward) / entity name
(reverse) by walking the `denotes` edge FIRST, falling back to the legacy
naming-convention read only when no correspondence (of either rung) is found
— preserving the two existing honest-miss tests' message shape (`git blame`
shows both assert a substring of the legacy `f"{entity}_beliefs"` format,
which the miss message still mentions diagnostically).

## 5. GO bar

**[RUN required]** Two real Bigville residents (`seeds/bigville_cast100.json`,
real data, not synthetic), each with a DIFFERENT-from-`SmEntity`-name
surface form:
- a UNIQUE-surname resident (checked `[RUN]` against the 100 real records
  before picking one) referred to by SURNAME ONLY in the simulated read — the
  OLD literal-format bridge provably CANNOT resolve this (`f"{surname}_
  beliefs"` names no real Mt), the NEW mechanism must resolve it correctly
  via the token-subset rung, feeding a real derived fact into a real CAN
  network's settled state (direction 1) — end to end, mirroring
  `REASONING_FACILITY_BRIDGE_RESULTS.md` §1.4's live-demo shape.
- the SAME correspondence read BACKWARD (direction 2): a settled CAN network
  whose owning entity is denoted by the non-canonical surface form produces a
  predication ON THAT SURFACE FORM (not a silently-substituted canonical
  name), which then fires a held implication — a genuinely new derived fact
  that did not exist before the round trip.
- a DUPLICATE-surname resident (checked `[RUN]`, `"peaseblossom"` is shared
  by 4 of the 100 residents) is used as a NEGATIVE control: the ambiguity
  guard must REFUSE to mint a correspondence rather than guess — reported
  as a genuine null, not smoothed over.

**GO** iff all three run for real, on the real engine, with the stated
outcomes. **NO-GO** iff the token-subset rung cannot be expressed without a
new Rust Term (checked already, §3 — not expected) or the ambiguity guard
cannot be expressed as a Rule `where`-clause (not expected — `Not(Exists(...))`
is a standing idiom, `seeds/gap_awareness.json` uses it repeatedly).

## 6. Regression scope

Files this rung may ADD to (new seed, rewired bridge module, new/extended
test file, this doc + RESULTS) but will NOT edit the internals of:
`domains/propositional_deduction.py`, `domains/inference_generation.py`,
`domains/situation_model_reader.py`, `domains/name_variant_merge.py` (reused,
not modified — only its `_name_tokens` helper is imported),
`seeds/inference_logical.json`, `seeds/can_native_reimplementation.json`,
`seeds/can_decay_identity.json`, `worlds/bigville_can_beliefs.py`,
`runners/dsl/src/can_ops.rs`, `runners/dsl/src/term.rs`. A `git diff --stat`
restricted to this list must be empty at RESULTS time.
`domains/reasoning_can_bridge.py` IS expected to change (that is the rewire)
— its existing tests (`tests/test_reasoning_facility_bridge.py`) must stay
green, run before and after, paired failing-node-id lists if anything
regresses.

## 7. What this will NOT establish, registered in advance

- Not general cross-domain coreference (pronoun binding, definite
  descriptions like "the shopkeeper" with no name-token overlap at all) —
  only NAME-STRUCTURE-based identity resolution. A description with zero
  lexical overlap with the resident's own name needs a different signal
  (e.g. `resident["role"]`, named in §3 as future work, not built here).
- Not a fix to the corpus-wide "rule effects bypass `check_edge`" property
  (§3) — the Γ production registered here is declarative, consistent with
  the standing (imperfect) corpus convention, not a new enforcement
  mechanism.
- Not a claim that `Concept`-name-set overlap is USELESS as a signal in
  general — only that it cannot discriminate BETWEEN residents in THIS
  corpus because `TOPIC_NAMES` is population-uniform (§1); a corpus with
  resident-specific topic vocabularies would make it a real disambiguator.
