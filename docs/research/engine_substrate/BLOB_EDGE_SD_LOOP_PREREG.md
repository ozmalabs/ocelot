# BLOB-EDGE SD LOOP — PREREG

Worktree `/home/matt/ozmadev/ocelot-worktrees/blob-edge-sd-loop`, branch
`blob-edge-sd-loop`, base `main` at `03bd3b3` (verified via `git log --oneline -1
main` immediately before branching — matches the orchestrating session's stated
tip). Immediate predecessor: `RELATION_CUE_TOKEN_COLLISION_RESULTS.md` (same
day's arc, merged as `03bd3b3`) — its `_shared_shape` axis-anchor fix
(`domains/reflective_faculty.py:7170`) is read here and built ON, never
touched.

**Process note, stated up front, same discipline the predecessor rung used:**
a load-bearing correction arrived from the creator (via the coordinating
session) mid-investigation, AFTER the four charter questions were read but
BEFORE any code was written. §3 (Q3, the mint criterion) is written to reflect
the corrected design directly — the superseded first draft of that section is
not presented as if it were the original prediction; the correction itself and
why it changes the design are recorded in §3.1 rather than silently absorbed.

---

## 0. The charter, restated precisely

Three creator messages, one idea, building in sequence (verbatim in the task
brief this rung was given):

1. Match salience should SUM across independently-corroborating structural
   edges, not come from one axis's verdict.
2. When many small correspondences accumulate in one neighbourhood, the
   substrate should POOL them into one aggregate ("blobby," the retinal
   ganglion-cell analogy) rather than carry N crisp edges forever.
3. The pooling/minting operation in (2) should be the EXISTING sd loop
   (recognize → transform → infer → mint) reapplied to edge/correspondence
   data, not a new bespoke mechanism — "once you have a universal algorithm,
   you should use it."

This spike is scoped to the MINT/PERSISTENCE half of the idea only (per the
brief's explicit out-of-scope list): does a recurring structural correspondence
between two held things deserve to become a first-class, persisted graph fact,
and if so, via which of the two generative primitives CLAUDE.md names (sd loop
vs Γ)? The multi-axis SALIENCE system (message 1, summing across shape + kind +
provenance + scope) is a related, separate follow-on, not built here.

## 1. The concrete gap, verified directly against the real code

`domains/analogical_thinking.py::_pair_witness` (line 414) and
`domains/reflective_faculty.py::_shared_shape` (line 7170) are both pure,
ephemeral, RECOMPUTED-EVERY-CALL functions — verified by reading both in full.
Neither writes anything to the graph; both return a plain Python
tuple/dict built from a `native.evaluate(...)` call (`AntiUnifyWitness`/
`AntiUnify` + `FixedCount`) and forget it the instant the caller reads it.

Grep confirms: no `Analogy`/`SharedShape`/`Correspondence`-named NODE type
exists anywhere in `seeds/*.json` that persists "these two things are
structurally linked, this strongly." `CorrespondenceRow`
(`seeds/lua_correspondence.json`) was checked and is a different,
unrelated hand-authored Lua/Rust API table — not a mined/grown structural-match
record.

Real call sites, read in full:

- `analogical_thinking.py:751` — inside `find_analogies`'s per-pair scoring
  loop (source-Mt concept × target-Mt concept).
- `reflective_faculty.py:1131` — inside `connect_concern_to_term`, scoring a
  concern's authored signature against every held `faculty`-kind
  `ShapeSignature`. Both operands here are frequently NOT graph nodes on both
  sides (the concern side can be a bare induced-residual list with no held
  Concept, `concept = "(induced from observation)"`, `reflective_faculty.py:1111`)
  — a real, honestly-reportable limitation for persistence (§4).
- `reflective_faculty.py:7523` and `:7533` — inside `_run_math_bridge`, scoring
  every held `math`-kind `ShapeSignature` against every held `faculty`-kind
  `ShapeSignature`. **Both operands here are, by construction, real
  `ShapeSignature` graph nodes** (both drawn from the same
  `_load_shape_signatures(substrate)` dict, `reflective_faculty.py:7045`,
  keyed by each node's own `name` attr) — the cleanest of the four sites for a
  first persistence demonstration, and the one this spike uses (§5).

## 2. Q1 — is "blob edge = sd loop applied to edge residuals" well-typed?

**Read closely, not assumed:** `runners/dsl/src/shape_decode.rs`'s
`sd_decode`/`sd_recognize`/`sd_mint_quantum` (via
`seeds/shape_decode_loop.json`, rule bodies read in full) decode ONE
`Observation` against a CODEBOOK of many `ShapeSignature` parts — the
`ShapeDecode` Term does beam search over the codebook, `covers_relation`
checks whole-tuple coverage, a non-empty residual either explains as a
transform/dimension-shift on an EXISTING held shape (rungs 2–3) or, failing
both, mints a brand-new `CapabilityAxis` quantum (rung 4), gated by a NOVELTY
guard so a recurring identical residual (`capability_keys` match) never
re-mints (`sd_dedup_existing` handles the terminal status for that case).

A "blob edge" is structurally different in one respect and identical in
another:

- **Different**: it is a fact about a PAIR of already-existing nodes (a
  correspondence), not a decode of ONE observation's structure against a
  codebook of many candidate PARTS. `_shared_shape(sig_a, sig_b)` never
  searches a codebook of many candidates for sig_a/sig_b themselves — it
  compares exactly two given signatures.
- **Identical, and this is the load-bearing part**: `_shared_shape` is
  ALREADY, in its current (predecessor-rung-fixed) form, doing a collapse onto
  EXISTING HELD STRUCTURE — the `RelationCue` vocabulary (52 held nodes,
  `_relation_cue_index`, `reflective_faculty.py:7140`). `by_name_a`/`by_name_b`
  are built by anchoring each side's rows onto the SAME held `RelationCue`
  nodes by content identity; `shared_names = sorted(set(by_name_a) &
  set(by_name_b))` is precisely the set of held structures BOTH sides
  independently collapsed onto. This is exactly the shape the creator's
  mid-flight correction (§3.1) names: `I_A -> S + r_A`, `I_B -> S + r_B`,
  where `S` is the shared `RelationCue` axis set. The AntiUnify template
  computed over `[by_name_a[nm] ...], [by_name_b[nm] ...]` is the residual
  READOUT of that collapse (which leaves are IDENTICAL — `fixed_count` — vs
  which vary — the wildcarded slots), not a fresh decode against a codebook of
  parts.

**Verdict: well-typed, but a NARROWER re-instance than the full four-rung sd
loop, and this narrowing is reported honestly rather than glossed over.** What
transfers cleanly: the recognize/mint DUALITY (a correspondence that matches
already-held structure is RECOGNIZED; a correspondence that names a
genuinely new structural pattern is MINTED once, guarded against duplicate
re-minting) and the concrete Rust-engine constraint sd_mint_quantum's own
family already lives with (`add_edge` targets must be match-bound vars — see
§3.2). What does NOT transfer: there is no beam search, no multi-part
composition, no transform-in-basis / infer-dimension rung here — a pairwise
`_shared_shape` call has no notion of "explain this residual as a shift of an
existing shape," because there is no larger codebook of correspondence-parts
being decoded against; there are exactly two operands. **This spike targets
only the recognize/mint duality (rungs analogous to 1 and 4 of the sd
ladder), explicitly not rungs 2–3 (transform/infer) — there is no
correspondence-shape "transform" concept defined, and inventing one would be
forcing an analogy past where the mechanics actually match.**

### 2.1 Deep vs superficial, per the Cangiotti/Nappo criteria

The paper's full PDF criteria were not extractable via automated fetch (the
arXiv abstract page returns metadata only); the assessment below is therefore
made directly against the STRUCTURAL test the charter itself asks for
("apply those criteria honestly"), cross-checked against the paper's stated
aim (generalizing Hesse 1963's account of when an analogy carries genuine
INDUCTIVE — not merely decorative — support) and against this project's own
prior, closely-related finding
(`RULES_AS_SHAPE_DESIGN_SPIKE.md`'s MAC-without-FAC diagnosis: an analogy is
superficial when only the surface match (predicate skeleton, name overlap)
is checked and the underlying correspondence structure is never retained or
re-used).

Applying the retained-structure test directly: a blob edge minted from a
`_shared_shape` collapse is deep, not superficial, because **the correspondence
IS the same representation being reused, not a post-hoc similarity score
computed after the fact over two independently-arrived-at answers.**
`shared_names` names the EXACT held `RelationCue` nodes both operands
independently anchored onto — the mechanism doing the recognizing (axis
anchoring) is the SAME mechanism that would explain, causally, why the two
signatures resemble each other (they share provenance in a common vocabulary
item), not a coincidence of surface tokens. This is precisely the corrected
framing in §3.1: minting at collapse time, not after an independent
similarity-score threshold, is what keeps this deep rather than superficial —
a blob edge minted on a bare `fixed_count > 0` threshold with no reference to
WHICH held structure produced the match would have been the superficial
version (a decorative similarity score persisted as if it were structure).

## 3. Q2 — Γ concern, sd-loop concern, or both?

Read directly: `runners/dsl/src/grammar.rs`'s `Production{src, edge_type, tgt,
where_, weight, provenance}` and `checker.rs`'s `check_edge` (Type-1 vs Type-2
inadmissibility) decide **whether an edge KIND is legal to exist at all** —
confirmed load-bearing, not advisory: `Substrate::add_edge`
(`runners/dsl/src/substrate.rs:1437`) returns `Err(InadmissibleEdge)` on
`CheckOutcome::Type1NoProduction`/`Type2VocabAbsent`, and the PyO3 binding
(`runners/dsl/src/py.rs:1715`) turns that into a raised Python exception. This
is not a soft convention — an edge type absent from Γ's `(src_type,
edge_type, tgt_type)` index cannot be written, by either a rule effect or
Python ingest, full stop. Verified empirically: `math_capability_shapes.json`
(the seed that actually creates the `ShapeSignature` nodes this spike
operates on) declares **zero** productions of its own — `ShapeSignature`
becomes a known Γ node type only because OTHER seeds
(`prog_construction_loop.json`, `code_write_gap.json`, `vision_margin.json`)
happen to reference it as a production endpoint. A brand-new edge kind (e.g.
`Correspondence -[about_a]-> ShapeSignature`) is admitted by NONE of the
existing productions (checked: none of the three above declare `about_a`,
`about_b`, `minted` from `Correspondence`, `links_a`, or `links_b`) and would
be rejected outright without new Γ productions.

**Verdict: both, and they are the SAME two-part split CLAUDE.md's own
standing rule names, cleanly separable, not conflated:**

- **Γ's job**: declare that `Agent -[observed_correspondence]-> Correspondence`,
  `Correspondence -[about_a/about_b]-> ShapeSignature`,
  `Correspondence -[minted]-> BlobEdge`, and
  `BlobEdge -[links_a/links_b]-> ShapeSignature` are ADMISSIBLE edge kinds at
  all — a static, unconditional (no `where`) declaration, exactly the shape
  `shape_decode_loop.json`'s own 2-entry `productions` list already uses for
  `Agent -[observed]-> Observation` / `Observation -[minted]-> CapabilityAxis`.
  This never varies per-instance; it is a schema fact.
- **sd-loop's job**: given a SPECIFIC computed correspondence (a specific pair,
  a specific `fixed_count`, a specific residual template), decide whether THIS
  instance recognizes an already-held pattern or mints a new one — an
  instance-level, data-dependent decision, never a schema fact. This is
  exactly the `RULE_SIGNATURE_PRODUCTION_WIRING_RESULTS.md`/humanoid/bigville
  finding CLAUDE.md's SHAPES-not-numbers section already names: conflating
  "what's legal" with "what's decided now" was the measured failure mode
  elsewhere. This spike keeps them in the two separate files/sections the
  precedent seed (`shape_decode_loop.json`) already keeps them in — one
  `"productions"` list, separate `"rules"` list, same seed file.

## 3.1 The mid-flight correction — mint criterion supersedes the original brief

**Original brief (superseded):** "mint when the SAME correspondence recurs (is
independently recomputed and found again) rather than on a magic fixed-count
threshold."

**Correction received mid-investigation, from the creator via the
coordinating session, formalised as an online MDL update:**
`L(G_{t+1}) ≈ L(G_t) + L(r_t) + L(E_t)` — storing a new observation costs only
its residual plus new edges, because it PREFERENTIALLY COLLAPSES onto existing
reusable structure. The correction's precise claim: **edge formation
activates AT COLLAPSE TIME, not after a recurrence threshold** — any
observation that successfully recognizes/transforms/infers against EXISTING
structure (i.e. does NOT fall through to mint-as-novel) mints the
correspondence edge immediately, no waiting for a second occurrence.
Recurrence instead gates a DIFFERENT thing — whether the part that did NOT
collapse (the genuine residual) eventually graduates into new minted
structure — which is a separate question this spike's narrow scope does not
need to re-decide, because it is already `sd_mint_quantum`'s own existing,
unmodified concern for genuinely novel residuals elsewhere in the tree.

**Checked against the real code, not taken on the correction's word alone —
and it holds:** re-reading `sd_mint_quantum`'s own guard
(`seeds/shape_decode_loop.json`, quoted in full in this rung's investigation)
confirms the ORIGINAL brief's "wait for recurrence" framing was never actually
how the existing sd loop works, even for genuine novelty-quantum minting. The
NOVELTY guard (`Not(Exists(NodesOfType('CapabilityAxis'), induced==1 AND
capability_keys==obs.key))`) fires on the FIRST occurrence of a residual that
doesn't already have a matching axis — it does not wait for a second sighting.
What recurrence gates, in the ALREADY-SHIPPED code, is DE-DUPLICATION (a
SECOND identical residual is recognized as a duplicate via
`sd_dedup_existing`, not re-minted) — never the INITIAL mint. The original
brief's "mint on recurrence" was therefore a mis-reading of the very mechanism
it asked this rung to reuse; the correction fixes that mis-reading against the
real code, not against a new invented rule.

**Consequence for this design:** a `_shared_shape` call whose `shared_names`
is non-empty (the two signatures collapsed onto ≥1 real held `RelationCue`
axis — the "successful partial collapse" the correction names) mints or
recognizes a `BlobEdge` on THAT SAME call, immediately — never deferred. A
call whose `shared_names` is EMPTY (total residual, no shared axis at all —
the two signatures share no held structure whatsoever) mints NOTHING at the
correspondence-edge grain; this is honestly out of this spike's scope (there
is no larger "residual accumulates toward a future mint" concept for a
pairwise comparison the way there is for a single `Observation`'s unexplained
predicates — a `Correspondence` node with zero shared axes is not a
"residual" in the sd loop's sense, it is simply "no correspondence found,"
and is recorded as a terminal `no_collapse` status for fixpoint hygiene, not
silently dropped).

## 3.2 A concrete engine constraint this design must (and does) respect

`sd_dedup_existing`'s own comment (`seeds/shape_decode_loop.json`) states
directly: *"add_edge targets must be match-bound vars in this engine"* — a
rule CANNOT `add_edge` to a node discovered via a `Term` search (`Exists`,
`Argmax`, `PickUnique`) within the SAME rule; only nodes bound by an actual
match TRIPLE (or minted earlier in the SAME rule's own effects list, as
`sd_mint_quantum` does for its freshly-`add_node`-ed `axis` var) are legal
`add_edge` endpoints. Confirmed independently by reading
`vg_mint_kernel_from_patch` (`seeds/vision_growth.json`), which uses a
THREE-triple match (`sense-considers->fac`, `sense-has_field->f`,
`f-has_patch->p`) precisely so `add_edge fac has_kernel k` can target a var
bound two hops back in the match chain, not a Term-found one.

This spike's `blob_mint`/`blob_recognize` rules are designed around this
constraint exactly as `sd_mint_quantum`/`sd_dedup_existing` already are:
`blob_mint` needs `add_edge` to the two correspondence endpoints
(`links_a`/`links_b`), so its match is a 3-triple chain (`ag
-observed_correspondence-> c`, `c -about_a-> na`, `c -about_b-> nb`) binding
`na`/`nb` as real match vars; `blob_recognize` needs to check "does an
existing `BlobEdge` already carry this `transform_key`" via a Term search
(`Exists`/`NodesOfType`) and therefore — like `sd_dedup_existing` — CANNOT add
an edge to that found `BlobEdge` within the rule. It sets a terminal
`status="recognized"` only; Python resolves the actual matching `BlobEdge`
node afterward by the SAME mechanical re-query pattern `induce_concern`
already uses for `CapabilityAxis` (equality scan on the shared identity key —
here `transform_key`, there `capability_keys`) — a read-back, not a decision,
exactly mirroring the existing precedent rather than inventing a new one.

## 4. Q3 (superseded framing folded into §3.1) / Q4 — does this pay for itself?

Call volume at the four real sites (§1) is small — none is a hot loop; the
prior rung's own audit (`RELATION_CUE_TOKEN_COLLISION_RESULTS.md`) found
these call sites during a manual, deliberate structural audit, not a
per-tick or per-frame path. **Prediction, registered before measuring:**
persisting correspondences will NOT show a measurable compute-time win at
today's call volume — the honest cost/benefit case is dedup (bounded,
recognizable structure instead of unbounded implicit re-derivation) and
DEMONSTRATING the mechanism works on real data, not a production
optimisation. This mirrors the charter's own framing of this as a live
possibility, not a forced conclusion either way.

**GO bar for Q4 (registered before measuring):** build the SMALLEST
demonstration that shows (a) `blob_mint` firing exactly once for a genuinely
novel correspondence pattern found in the REAL `math_capability_shapes.json`
codebook (not synthetic data — real data is available and was explicitly
preferred per the predecessor rung's own probe-script precedent), and (b)
`blob_recognize` firing — with ZERO new `BlobEdge` node created — the moment a
SECOND real pair (any two of `_run_math_bridge`'s math×faculty pairs) shares
the identical `transform_key`. If no such second pair exists in the real
seeded data, a small controlled synthetic pair (mirroring the predecessor
rung's `shape_decode_shape_fit_collision_probe.py` construction) is an
acceptable, honestly-labelled fallback — but the real-data case is checked
FIRST and reported either way.

## 5. The slice, concretely, if the above cohere (GO)

All four questions above assess GO — Q1 well-typed (narrower than the full
four-rung ladder, honestly scoped to rungs 1/4 only), Q2 both (Γ declares the
edge kinds, sd-loop-shaped rules decide instances), Q3/mint-criterion
corrected and re-verified against the real `sd_mint_quantum` code, Q4 real
cost-benefit registered above rather than assumed.

**Site**: `reflective_faculty.py:7523` inside `_run_math_bridge` — the
math↔faculty bridge loop, BOTH operands real `ShapeSignature` nodes by
construction (§1). This is also the most narratively apt site: it is
literally the codebase's own cross-domain analogy-finding call (`math_sig`
compared against every `faculty_sig`), which is exactly the "cross-domain
path I_A↔S↔I_B" scenario the creator's correction describes.

**New graph vocabulary** (`seeds/blob_edge_correspondence.json`,
`depends_on: ["math_capability_shapes"]`):

- `Correspondence` node — one computed witness attempt: `status`
  (pending/recognized/minted/no_collapse), `shared_count` (int, `fixed_count`
  read-out), `transform_key` (string, canonicalised `AntiUnify` template).
- `BlobEdge` node — a PERSISTED, held correspondence PATTERN: `transform_key`,
  `fixed_count`, `source`.
- Γ productions (unconditional, mirroring `shape_decode_loop.json`'s own
  2-entry list): `Agent-observed_correspondence->Correspondence`,
  `Correspondence-about_a/about_b->ShapeSignature`,
  `Correspondence-minted->BlobEdge`, `BlobEdge-links_a/links_b->ShapeSignature`.
- Rules (mirroring `sd_mint_quantum`/`sd_dedup_existing`'s exact shape):
  `blob_mint` (guard: `status==pending AND shared_count>0 AND NOT
  Exists(BlobEdge with matching transform_key)` → `add_node` BlobEdge +
  `add_edge minted` + `add_edge links_a/links_b` to the match-bound `na`/`nb`
  + `status=minted`), `blob_recognize` (mirror guard, existing match found →
  `status=recognized`, no new edge — §3.2), `blob_no_collapse`
  (`shared_count<=0` → `status=no_collapse`, fixpoint termination hygiene).

**Python** (`domains/reflective_faculty.py`, additive, `_shared_shape` itself
untouched): `record_correspondence(substrate, node_a, sig_a, node_b, sig_b)` —
mechanical ingest mirroring `domains/meta_shape.py::observe`'s exact pattern
(write node + edges, `run_rules()`, read back `status`); two small lookup
helpers (`_agent_node_id`, `_shape_signature_node_id`) for resolving real node
ids by name, since `_load_shape_signatures` is name-keyed only. Wired at
`_run_math_bridge`'s primary loop (:7523) only — the redundant "find weakest"
pass (:7533) and the other two real sites (`analogical_thinking.py:751`,
`connect_concern_to_term`) are named as follow-on, not built, per the
charter's explicit "pick ONE."

**Live before/after demonstration**: run `_run_math_bridge` (or the
underlying loop directly) against the UNMODIFIED engine first, showing every
pair's `_shared_shape` computed from scratch with nothing persisted (grep the
graph for `Correspondence`/`BlobEdge` node counts: zero, both before and
after, on the unmodified engine — there is no persistence to demonstrate
there). Then, on the FIXED engine: first pass over the real codebook shows
`blob_mint` firing (a new `BlobEdge` appears) for however many DISTINCT
`transform_key`s the real math×faculty pairs actually produce; **the
headline number to report is how many of the real pairs' correspondences
collapse onto a transform_key some OTHER pair already produced** (recognize
firing with zero incremental `BlobEdge` growth) versus how many are novel
(mint firing) — measured, not predicted, in §RESULTS.

**Explicitly out of scope, restated**: no new Rust Term (only
`AntiUnify`/`FixedCount`/`Exists`/`NodesOfType`/`add_node`/`add_edge`, all
pre-existing); no change to `_shared_shape` itself; no retrofit of the other
three real call sites (named as follow-on); no multi-axis salience system
(message 1's full idea).

## 6. Regression plan

Scoped test files: `tests/test_composer_driver_migrated.py`,
`tests/test_reflex_net_migrated.py` (both exercise `reflective_faculty.py`'s
composer paths), plus any existing test file that calls `_run_math_bridge`/
`_shared_shape` directly (to be located during the build). A NEW test file,
`tests/test_blob_edge_correspondence.py`, covering: mint fires once for a
novel pattern; recognize fires with zero `BlobEdge` growth for a repeat
pattern; no_collapse fires and terminates for a genuinely disjoint pair;
`_shared_shape`'s own return value is byte-unchanged (this spike is additive
only). PAIRED failing-node-id lists (never bare counts) reported in RESULTS
if anything shared regresses, per CLAUDE.md's standing rule from the
`results/failure_baseline.json` retraction.

## 7. GO/NO-GO bar, stated before building

- Q1: GO if the collapse-onto-`RelationCue` reading holds up under direct
  code reading (it does, §2) — narrower-than-full-ladder is an acceptable,
  honestly-reported GO, not a NO-GO; a NO-GO would require finding that
  `shared_names`/`fixed_count` do NOT actually anchor on held structure
  (falsified — the predecessor rung's own axis-anchor fix is exactly this
  anchoring, read directly).
- Q2: GO on "both, cleanly separable" if Γ's admit/deny gate is confirmed
  load-bearing (it is, §3 — `add_edge` raises on rejection, not a soft
  warning) and the existing seed precedent keeps schema (Γ) and instance
  decision (rules) in the same file's two separate top-level keys (it does).
- Q3: superseded framing corrected in §3.1; GO on "collapse-time mint, no
  recurrence gate for the edge itself" if `sd_mint_quantum`'s own guard,
  re-read, confirms first-occurrence minting (it does — quoted in full in
  §3.1). NO-GO would require finding the real `sd_mint_quantum` gates on a
  SECOND sighting, which the direct quote refutes.
- Q4: GO on "build the minimal demonstration, not a production optimisation"
  bar stated in §4; NO-GO on any compute-time-savings claim (not measured,
  not predicted to be measurable at today's call volume, and not required for
  a GO under the charter's own "smallest demonstration" framing).

All four assess GO. Proceeding to build per §5.
