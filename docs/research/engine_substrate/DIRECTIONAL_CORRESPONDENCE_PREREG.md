# DIRECTIONAL CORRESPONDENCE — PREREG

Base `main @ 76b8aea` (re-verified before branching; `git log --oneline -1
main`). Worktree
`/tmp/claude-1000/-home-matt-ozmadev-ocelot/34a7cd08-5eb1-42bd-af0c-eedb1125fa76/scratchpad/directional-correspondence`,
branch `directional-correspondence`.

Collision check: `git status --short -- domains/analogical_thinking.py` is
empty and `git diff --stat main -- domains/analogical_thinking.py` is empty
at branch time — no uncommitted sibling-rung edits to this file are sitting
in the working tree at the moment this worktree was cut. Several sibling
worktrees exist (`shape-audit-sweep2`, `mac-fac-a5-a6` …), all on `main` tips
at or before `76b8aea`; none has merged since. This rung is additive-only to
`domains/analogical_thinking.py` (new functions after the existing ones) and
adds two new files (`domains/directional_correspondence.py` is NOT planned —
new functions land in `analogical_thinking.py` and `propositional_deduction.py`,
both additive), so a later merge of a sibling's *own* additive changes to the
same files should not conflict at the line level; if it does, the fix is a
textual merge, not a redesign.

---

## 0. What is already established, read before writing any code

- `REASONING_FACILITY_BRIDGE_RESULTS.md` §3 (candidate 2a) checked, live, and
  found: `find_analogies` output and `_pair_witness`'s own
  `{shared, name_shared, fixed_count, transform}` carry **no directional
  signal** — `source_concept`/`target_concept` in a returned record reflect
  SEARCH ORDER (which Concept the outer loop visited first), not a causal or
  logical direction. `_pair_witness`'s `shared`/`transform` are SYMMETRIC in
  their two operands by construction (`AntiUnifyWitness` generalises over an
  unordered pair). Declared NO-GO-BY-DESIGN, precisely sized, not forced.
- `SHAPE_AUDIT.md` §2.4: `find_analogies`/`emit_analogy_as_graph` used to
  write an `implements` edge on `order_n >= 2` alone — a hand-set ordinal
  asserting structural correspondence nothing had computed (the June
  "MAC stage treated as the verdict" diagnosis, re-found at its own original
  site).
- `BLOB_EDGE_ANALOGY_EXTENSION_RESULTS.md`: `_pair_witness`'s real call site
  (`_compute_analogy`, inside `find_analogies`'s PASS 1) is wired into
  `seeds/blob_edge_correspondence.json`'s `blob_mint`/`blob_recognize`/
  `blob_no_collapse` rules via a Gamma-only companion seed
  (`seeds/blob_edge_concept_correspondence.json`) admitting `Concept`-typed
  `about_a`/`about_b`/`links_a`/`links_b` edges. `record_pair_correspondence`
  calls `run_rules()` **per write** (a batched, once-per-pass version was
  tried and measured to produce a real duplicate-`BlobEdge` race — the
  engine's matcher is semi-naive, matches found against a snapshot before
  effects apply).

## 1. Pre-registered reading of the current state — verify BEFORE assuming stale

Read directly (not from memory of the task brief, which quotes SHAPE_AUDIT.md
as if the §2.4 defect were still open):

- `domains/analogical_thinking.py::emit_analogy_as_graph` (current line
  numbers, to be confirmed by `grep -n`) — does the `implements` edge still
  fire on `order_n >= 2` alone, or has it already been gated on a real
  computed quantity?
- `git log --oneline -3 -- domains/analogical_thinking.py` and
  `git merge-base --is-ancestor ae38fe7 HEAD` (`ae38fe7` = the SHAPE_AUDIT.md
  landing commit) to establish whether any fix postdates the audit.

**Prediction, to be confirmed or refuted by the read above, not assumed
either way**: given this file has had multiple recent rungs land on it
(`14cb457`/`080bc88`, the blob-edge wiring), it is plausible the audit's
own diagnosis has already been acted on by a rung that isn't this one — in
which case task item 3 becomes "confirm and report", not "fix." If the read
shows it is still exactly as SHAPE_AUDIT.md describes, task item 3 becomes
"size a follow-on", per the task's own explicit sanction not to
opportunistically fix an unrelated defect.

## 2. The directionality-signal investigation — expected finding, registered before computing anything

Three candidate signals will be checked against real code, in this order,
because each is progressively more expensive to justify:

1. **Search-order asymmetry from the calling context itself**
   (`find_analogies(source_mt_name, target_mt_names, ...)`,
   `_compute_analogy`'s `sc`/`tc` argument order). **Expected: this is NOT a
   real signal** — confirmed by `REASONING_FACILITY_BRIDGE_RESULTS.md` §3
   already, and expected to be reconfirmed by reading real call sites: the
   only LIVE standing caller (`reframing_proposer.py::scan_for_recurring_
   structure`) calls `find_analogies(sub, mt_name, [mt_name], ...)` —
   comparing a microtheory **to itself**, where "source" and "target" are
   definitionally the same domain and the label is pure loop-visitation
   order. Other scripts that use genuinely different source/target Mt names
   are, per the same results doc, confirmed NOT LIVE (stale Mt names /
   import paths). **If this prediction holds, search order is rejected as
   the signal**, exactly as the prior rung already found — this rung does
   not re-litigate that finding, it starts from it.
2. **Temporal order of learning / "established longer"** (a `Concept`
   creation timestamp, or node-id order as a proxy). **Expected: no
   meaningful signal exists for the standing seeded corpus** — `Concept`
   nodes across `domains/*.py` are not observed to carry a consistent
   creation-timestamp attribute, and essentially all `Concept` nodes in the
   domains this rung can realistically demonstrate on (`mathematics`,
   `computer_architecture`, …) are loaded in one seed-boot pass; node-id
   order there reflects JSON/seed-file iteration order, not the agent's own
   epistemic history, and using it would be fabricating a signal dressed as
   data. To be confirmed by grep before ruling it out — this is a real
   empirical check, not a foregone conclusion.
3. **Structural-elaboration asymmetry** — how many axes of the SAME
   `_vocabulary_keys` vocabulary each concept in the pair is independently
   evidenced on (`_concept_shape_vector`'s own non-absent count per side).
   **Expected: this is a real, already-computed-adjacent, genuinely
   asymmetric quantity** — `_pair_witness`'s `shared`/`transform` outputs
   are symmetric by construction, but the two INPUT vectors it is handed
   (`vec_a`, `vec_b`) are not symmetric with each other in their own right:
   one concept may be evidenced on more axes (more functional roles /
   abstract principles / meta-shapes / name-slot hits) than the other. This
   mirrors the standard analogy-theory convention (a richer, better-known
   "base" domain supplies structure to a sparser "target" domain being
   explained) without inventing new machinery: the count can be read via
   the SAME `FixedCount` Rust Term `_pair_witness` already calls
   (`native.evaluate({"type": "FixedCount", "pattern": <one vector>, "wild":
   _ABSENT}, {})`), applied to one side's vector instead of the merged
   AntiUnify template — expected, and to be confirmed by reading
   `fixed_count_value` (`term.rs`), to return `len(vector) + count(non-absent
   entries)`, which is a monotonic function of "axes evidenced" given
   `_concept_shape_vector` produces a FIXED-ARITY vector of identical length
   for every concept (confirmed by that function's own docstring) — so
   comparing `FixedCount` on `vec_a` vs `vec_b` is expected to be
   arithmetically equivalent to comparing raw evidenced-axis counts, with
   ZERO new Rust.

**Registered decision rule**: if (3) is confirmed real and asymmetric on a
genuine pair with `fixed_count > 0` (structural correspondence exists at
all), it becomes the grounding signal, with an honest **tie → no direction
assigned** outcome when both sides are equally rich (never forced). If (3)
also turns out degenerate (e.g. every real concept pair in the seeded
vocabulary happens to tie), that is itself reported as a clean null and the
rung reports directionality as genuinely underdetermined without new
external signal, per the task's own explicit sanction for that outcome.

## 3. The directional record — planned design (subject to what §2 actually finds)

A NEW node type, `DirectionalCorrespondence` — explicitly NOT a `BlobEdge`
edit (`BlobEdge`'s own shape stays byte-unchanged) and explicitly NOT a
`ShapeSignature` — for a safety reason established by reading
`runners/dsl/src/shape_decode.rs::load_parts` before writing any code: the
`ShapeDecode` codebook pool is loaded by scanning **every** node of type
`ShapeSignature` with a `name` + `signature` attr present; `kind` is read
but **not used to filter** which nodes are eligible candidates. This means
tagging an unverified hypothesis `ShapeSignature{kind:"knowledge_logical_
hypothesis"}` would NOT keep it out of `resolve_implication_gap`'s live
decode pool — the moment its `signature` shape matches a real gap's goal, it
competes for a real modus-ponens mint on a real `SmEntity`, regardless of
`kind`. **The only genuinely safe gate is a node-TYPE boundary**, not an
attribute flag. `DirectionalCorrespondence` therefore stays outside
`ShapeSignature` entirely until an explicit promotion step.

Planned shape (subject to revision once §2's numbers are in hand):
`{status: pending|a_source|b_source|symmetric|no_correspondence,
shared_count, richness_a, richness_b, transform_key}` +
`about_a`/`about_b` edges (mirrors `Correspondence`'s own shape) +
`source_concept`/`target_concept` edges written ONLY when a rule resolves a
real direction. Mint/read pattern mirrors `record_pair_correspondence`
(mechanical ingest, `run_rules()` per write) exactly. The direction JUDGEMENT
(which side is richer) is a graph RULE reading `Gt`/`Lt` over the two
already-written `richness_a`/`richness_b` attrs — not a Python `if`/`else` —
matching this file's own `blob_mint`/`blob_recognize`/`blob_no_collapse`
status-ladder idiom and CLAUDE.md's rule that a decision over graph state is
a Rule, not Python.

## 4. Feeding the deduction facility — planned design

An explicit, NEVER-automatic promotion function
(`propositional_deduction.py`, additive — no edit to any existing function)
turns a RESOLVED (`a_source`/`b_source`, never `symmetric`/`no_correspondence`
— an honest gate, not forced) `DirectionalCorrespondence` into a real
`ShapeSignature{kind:"knowledge_logical", provenance:"analogical", …}` node,
in the SAME `signature`/`supplies` shape `mint_logical_schema` already
writes (`signature: [["holds", source_concept_name]]`, `supplies:
{"relation":"is_a","attr":target_concept_name}`), so it composes with
`inference_generation.py`'s UNCHANGED `decode_gap`/`resolve_implication_gap`
pipeline with zero new gap-detection code — the same reuse
`REASONING_FACILITY_BRIDGE_RESULTS.md`'s own candidates 1/3 already
demonstrated for a different pair of facilities.

**Trust-tier decision to be justified, not asserted, once built**: expected
answer is `coherence:"elaborative"` (the ALREADY-EXISTING, already-documented
weaker-evidence tier `inference_generation.py`'s own docstring names —
"fires ONLY when `standard_of_coherence.depth` reads `deep`"), not
`"blocking"` (the tier `mint_logical_schema`'s directly-taught/proven
schemas use, and which fires unconditionally). This is investigated, not
assumed: `derive_contrapositive` already propagates whatever `coherence`
value the parent schema carries (`at.get("coherence") or "blocking"`), so no
new code is needed there either way — only the promotion function's own
`attrs["coherence"]` choice is a real decision, to be justified in RESULTS
against the alternative (`SelfConcern`/`StandingConcern`/promote/adopt).
**Distinguishability requirement**: the promoted schema must carry
`provenance:"analogical"`, a `chain` string naming its derivation, and a
`derived_from` edge back to the `DirectionalCorrespondence` node (a NEW
Gamma production, `ShapeSignature -derived_from-> DirectionalCorrespondence`)
— none of which a directly-taught (`mint_logical_schema` from NL text) schema
carries, so the two are inspectable-distinct in the graph, not merely
distinct in an external log.

## 5. `find_analogies`'s MAC-as-verdict defect (task item 3) — investigated, not fixed opportunistically, unless genuinely entangled

Per §1 above: read the CURRENT state of `emit_analogy_as_graph` first. If it
already gates the `implements` edge on a real computed quantity (not
`order_n >= 2` alone), report as CONFIRMED FIXED (by which commit, when,
citing the fix's own comment if it names SHAPE_AUDIT.md), and separately
assess whether the BROADER complaint in the same section — "not one of the
five [abstraction] orders consults a concept's edges" — is also addressed by
that fix or remains a narrower, distinct residual (the FAC witness this rung
extends operates over a vocabulary-hit-derived vector, not literal
Concept-to-Concept graph edges — these are not obviously the same claim, and
conflating them would overstate what any single fix established). Report
honestly whichever way this comes out; this rung will NOT edit
`_compute_analogy`'s per-order surface computation regardless of what is
found, per the task's own explicit scope boundary.

## 6. Live-demonstration scenario — registered before running anything

Construct (or select from the real seeded corpus) two `Concept` nodes with:

1. `_pair_witness(..).fixed_count > 0` (a real structural correspondence
   exists — otherwise there is nothing to direct);
2. an ASYMMETRIC richness count (§2 candidate 3) — otherwise the honest
   `symmetric` outcome is the correct and expected result, and the
   demonstration will show THAT instead, reported as equally valid
   (the task explicitly sanctions this as a complete outcome), with a
   SEPARATE constructed pair used to show the resolved-direction path if the
   first real pair found ties.

Then:

- Run the correspondence through `record_directional_correspondence` +
  `run_rules()`, read back `status`, confirm it names a real source/target
  Concept pair (by NAME, not by which was visited first in the search loop —
  the whole point being tested).
- Promote the resolved hypothesis via the new `propositional_deduction.py`
  function; confirm the minted `ShapeSignature` carries `provenance:
  "analogical"`, `coherence:"elaborative"`, and a `derived_from` edge.
- Mint a real `SmEntity` holding the SOURCE concept's name as a fact; run
  `resolve_implication_gap` at `standard_of_coherence.depth=="shallow"`
  (expected: does NOT fire — the elaborative gate holds) and again at
  `"deep"` (expected: DOES fire, minting `is_a(entity, target_concept_name)`
  via the unmodified `situation_model_reader.ingest_predication` path) —
  showing the two-tier trust gate operating on a REAL derived fact, not a
  type-check.
- Confirm the derived fact is inspectably distinguishable from one minted by
  `mint_logical_schema` from NL text (no `provenance` attr, `coherence:
  "blocking"`, no `derived_from` edge on the taught schema).

**Honest-null branch, registered as an equally acceptable outcome**: if no
real pair in the standing corpus resolves a direction (every candidate
ties), the live demonstration will construct two synthetic `Concept` nodes
with a hand-built vocabulary-hit asymmetry (mirroring how the existing
`test_blob_edge_analogy_extension.py` constructs its own pairs) rather than
force an artificial "win" out of the real corpus — reported as such, not
hidden.

## 7. Out of scope, restated

`_pair_witness`'s own symmetric structural computation (extend around it,
never edit its return shape); the general `SmEntity`/`Concept`
entity-resolution work (sibling rung's scope); quantified deduction (sibling
rung's scope); any new Rust Term (none identified as necessary above — if
one turns out to be genuinely required, STOP and report why rather than
build it).

## 8. Regression gate

`tests/test_blob_edge_analogy_extension.py`,
`tests/test_deduction_generalization.py`, `tests/test_deduction_extension.py`
must stay green (paired failing-node-id list if not), plus new tests for the
directional mechanism and the promotion path.
