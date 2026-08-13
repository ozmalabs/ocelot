# BLOB-EDGE ANALOGY EXTENSION — PREREG

Worktree `/home/matt/ozmadev/ocelot-worktrees/blob-edge-analogy-extension`,
branch `blob-edge-analogy-extension`, base `main` at `b124038` (verified via
`git log --oneline -1 main` immediately before branching; `git worktree list`
checked first — no sibling worktree currently touching
`domains/reflective_faculty.py` or `domains/analogical_thinking.py`).
Immediate predecessor: `BLOB_EDGE_SD_LOOP_PREREG.md` / `_RESULTS.md` (merged
earlier today as `a0bbd38`) — read in full before this rung started; this
rung's methodology, terminology and Γ/rule split are inherited from those
documents wholesale, not re-derived.

## 0. The charter, restated precisely

The merged rung built persisted "blob edge" correspondence minting — the sd
loop's recognize/mint duality reapplied one level up, to a pairwise
structural CORRESPONDENCE between two held things, rather than to a single
`Observation` decoded against a codebook of many parts. It wired exactly ONE
of four real call sites it identified
(`domains/reflective_faculty.py::_run_math_bridge`, both operands real
`ShapeSignature` graph nodes) and explicitly named the other three as
follow-on: `connect_concern_to_term`, `_run_math_bridge`'s own redundant
"find weakest" pass, and — the one this rung targets —
`domains/analogical_thinking.py::_pair_witness` (line 414), called from
`_compute_analogy` (line 751), which is itself called from `find_analogies`'s
PASS 1 loop (line ~558) — the agent's actual cross-domain analogy-search
primitive.

This rung's scope: wire `_pair_witness`'s real call site into the SAME
blob-edge mechanism (`seeds/blob_edge_correspondence.json`'s
`blob_mint`/`blob_recognize`/`blob_no_collapse` rules), adapting the
Python-side mapping and the Γ schema where the shapes genuinely differ,
without touching `_shared_shape`/`_run_math_bridge` or the already-merged
seed's rules.

## 1. The concrete gap, and where it genuinely differs from the merged site

`_pair_witness(substrate, vec_a, vec_b)` (`analogical_thinking.py:414`) is,
like `_shared_shape`, a pure, ephemeral, recomputed-every-call function: it
runs `AntiUnifyWitness` + `FixedCount` over two operand vectors and returns
`{shared, name_shared, fixed_count, transform}`, writing nothing to the
graph. Its real call site (`_compute_analogy:751`) is reached only when
`any(k >= 2 for k in per_order)` — i.e. only for a candidate pair that has
ALREADY passed a cheaper surface filter (shared functional role / abstract
principle / meta-shape at order ≥ 2); orders 0/1 never reach it. This is a
real, pre-existing guard, not something this rung adds.

**Read closely — three respects in which this site is NOT a byte-identical
copy of the merged site:**

1. **Operand type.** `_run_math_bridge` compares two `ShapeSignature` graph
   nodes; `_compute_analogy` compares two `Concept` graph nodes (`sc`, `tc` —
   real nodes from `_list_concepts(substrate, mt)`, confirmed by reading
   `_list_concepts` and the `find_analogies` PASS 1 loop). The Γ productions
   the merged seed declared (`Correspondence-about_a/about_b->ShapeSignature`,
   `BlobEdge-links_a/links_b->ShapeSignature`) are typed to `ShapeSignature`
   specifically. Confirmed directly from `runners/dsl/src/checker.rs::check_edge`
   (read in full): `Substrate::add_edge` looks up Γ productions by the
   **actual runtime type** of both endpoints
   (`graph.node(src).type_`/`graph.node(tgt).type_`), not by the edge type
   alone — an `about_a` edge from `Correspondence` to a `Concept` node would
   be rejected (`Type1NoProduction`) by the existing productions as they
   stand. **This is a genuine, load-bearing typing gap, not a cosmetic one.**
2. **Operand vector shape.** `_shared_shape` (the merged site's comparator)
   expects its two operand lists to be raw relation TUPLES that are
   byte-identical to a held `RelationCue.relation` template — it anchors
   each row onto a NAMED axis via `_relation_cue_index`
   (`{tuple(relation): cue_name}`) before comparing. `_pair_witness`'s
   operands (`_concept_shape_vector`'s output) are a **different**
   vocabulary and a **different** row shape: `[["role:scheduler", "value-or-
   absent"], ..., ["category", cat-or-absent]]` — already-paired
   `[axis:name, value]` rows over the `analogical_thinking`-owned
   `_vocabulary_keys` vocabulary, not `RelationCue`-anchored relation tuples.
   Feeding `_pair_witness`'s vectors through `_shared_shape` would find zero
   matches in `_relation_cue_index` for every row (checked directly against
   the two functions' code, not assumed) — the two comparators are
   **structurally parallel, not interchangeable**. `_pair_witness` already
   does its OWN axis-fixed-vs-wild extraction internally (`out["shared"]`,
   built by filtering `AntiUnifyWitness`'s template for non-wild,
   non-absent rows) — this is the correct "recognized structure" readout to
   persist, not a call to `_shared_shape`.
3. **Call volume.** Measured directly on the real seeded corpus (WorldAdapter
   + `load_all_seeds`, `Substrate.nodes("Microtheory")` — 483 Mts, 204 with
   ≥1 concept, 6302 concepts total across nonzero Mts; largest:
   `computer_architecture` 142, `mathematics` 137, `communication` 136):

   ```
   find_analogies('computer_architecture' x itself, order_n=4):
     concepts=142  pairs_total=20164  pair_witness_calls=7970  results=7346  time=2.48s
   find_analogies('mathematics' x itself, order_n=4):
     concepts=137  pairs_total=18769  pair_witness_calls=112   results=1406  time=1.25s
   find_analogies('communication' x itself, order_n=4):
     concepts=136  pairs_total=18496  pair_witness_calls=76    results=374   time=1.02s
   ```

   `_pair_witness` call volume varies **two orders of magnitude** across real
   Mts depending on how many concept pairs clear the order≥2 surface gate
   (7970 vs 76 for near-identical total pair counts) — this is genuinely
   `O(n·m)`-shaped at the high end, not a small fixed handful like the merged
   site's four real call sites (§4 of the merged PREREG: "none is a hot
   loop"). **This changes the cost/benefit case materially: the merged site's
   own Q4 predicted (and confirmed) no measurable compute-time win at ~66
   calls/invocation; at 7970 calls/invocation the question is open and is
   measured, not assumed, in §3 below.**

   `jabberwock_reads_looos.py`/`jabberwock_cross_references_everything.py`
   (scripts referencing Mt names `looos_claims`/`held_writing_primitives` or
   walking all-Mts-×-all-Mts) were checked and are **not part of the
   standing seeded corpus** — those Mt names do not exist in
   `load_all_seeds`'s output, and `jabberwock_cross_references_everything.py`
   hardcodes a stale absolute import path (`/home/matt/ozma/internal/...`)
   from an earlier project layout — both are historical one-off artifacts,
   not live call sites, and are not used for the scale measurement above.
   The `computer_architecture`/`mathematics`/`communication` self-comparisons
   above ARE live, real, standing seed data reachable by any caller of
   `find_analogies(sub, mt_name, [mt_name], order_n=4)` today (e.g.
   `domains/reframing_proposer.py::scan_for_recurring_structure`, which calls
   exactly this shape, albeit today only over its own small
   `agent_faculties_scan` Mt).

## 2. Q1 — is the mapping onto `BlobEdge`'s schema well-typed for THIS site?

**Verdict: yes, with the operand-type extension named in §1.1 handled as a
genuinely-justified adjacent Γ addition (not a rewrite of the merged
productions), and the transform_key readout adapted to `_pair_witness`'s own
already-filtered `shared` output (not routed back through `_shared_shape`).**

The recognize/mint DUALITY still transfers cleanly for the identical reason
the merged rung found it transfers for `_shared_shape`: `_pair_witness`'s
`out["shared"]` is not a post-hoc similarity score — it is the readout of
which axes of the SAME held vocabulary (`_vocabulary_keys`) both concepts
were independently evidenced on, i.e. the same "collapse onto existing held
structure" event the merged rung's §2 names, one grain over (the held
vocabulary here is `_vocabulary_keys`'s `FunctionalRole`/`ShapePrinciple`/
`MetaShape` axis set instead of `RelationCue`, but the shape of the claim —
"I_A and I_B both anchor onto the same named S, that anchoring IS the
recognized structure" — is unchanged).

**What does NOT transfer, same as the merged rung's honest scoping**: no
beam search, no correspondence-grain transform/infer rung (rungs 2–3) — this
build implements rungs 1/4 (recognize/mint) only, exactly as scoped there.

## 3. Q2 — the Γ extension, and why it is additive, not a rewrite

Per §1.1, the existing 6 productions in `seeds/blob_edge_correspondence.json`
do not admit a `Concept`-typed `about_a`/`about_b`/`links_a`/`links_b` edge.
**This rung does NOT edit that seed's productions or rules** (explicitly out
of scope, per the charter). Instead: a new, small, ADJACENT seed —
`seeds/blob_edge_concept_correspondence.json`, `depends_on:
["blob_edge_correspondence"]` — declares exactly 4 new unconditional Γ
productions (`Correspondence-about_a->Concept`, `Correspondence-about_b->
Concept`, `BlobEdge-links_a->Concept`, `BlobEdge-links_b->Concept`) and
**zero new rules**.

This is well-typed because `blob_mint`/`blob_recognize`/`blob_no_collapse`'s
rule bodies (read in full, `seeds/blob_edge_correspondence.json`) never
inspect `na`/`nb`'s node TYPE — the match triples (`c-about_a->na`,
`c-about_b->nb`) bind whatever node the edge actually points at, and the
`where` guards only read `status`/`shared_count`/`transform_key` attrs off
`c` and `existing_blob`. The rules are, by construction, type-agnostic over
the correspondence ENDPOINTS — only Γ (which is per-instance-type, checked
at `add_edge` time) needed extending. **The three rules are reused verbatim,
unedited, exactly as the charter requires**; only the schema (what edge
KINDS are admissible) grows, in a separate seed file, which is the same
Γ/rules separation the merged rung's own §3 already establishes as the
correct place to put a schema fact.

## 4. Q3 — the mint criterion (inherited, not re-derived)

The merged rung's corrected mint criterion (collapse-time minting, first
occurrence, no recurrence gate for the edge itself — verified there against
`sd_mint_quantum`'s own NOVELTY guard) is inherited unchanged: a
`Correspondence` whose `shared_count > 0` mints or recognizes on the SAME
call/pass it is created, never deferred; a `Correspondence` with
`shared_count <= 0` (no held axis shared at all) terminates via
`blob_no_collapse`, honestly out of the sd ladder's residual-accumulation
scope, exactly as before.

## 5. Q4 — the batching adaptation, the genuinely load-bearing design decision

**This is the one place this rung's design differs materially from the
merged site's wiring, and it is justified directly by the §1.3 scale
measurement, not by convenience.**

The merged site's `record_correspondence` calls `native.run_rules()` once
PER CALL (once per math×faculty pair, ≤66 times per `_run_math_bridge`
invocation) because its caller (`_run_math_bridge`) reads the persisted
`status` back synchronously for its own bookkeeping. At this site,
`_compute_analogy`'s caller (`find_analogies`) does **not** consume the
Correspondence/BlobEdge persistence status for anything — the analogy
verdict (`_finalise_analogy`) is computed entirely from `_pair_witness`'s
in-memory return value (`witness["shared"]`/`witness["transform"]`), never
from a graph read-back of the persisted `Correspondence` node. Persistence
here is a pure side channel, exactly as it is at the merged site — but
unlike the merged site, nothing downstream needs it synchronously per pair.

Given the measured call volume (§1.3: up to 7970 `_pair_witness` calls in one
`find_analogies` invocation), calling `run_rules()` 7970 times per
invocation is the wrong default to assume safe — it must be measured, not
copied uncritically from a site that only ever saw ≤66 calls. **Design
decision, stated before measuring**: `_compute_analogy` performs the
mechanical INGEST (write the `Correspondence` node + `about_a`/`about_b`/
`observed_correspondence` edges) but does **not** call `run_rules()` itself;
`find_analogies` calls `native.run_rules()` **once**, after PASS 1's full
loop completes and before PASS 2/3 (which do not depend on Correspondence
status either). This is the identical shape CLAUDE.md's own canonical
world-adapter example already sanctions ("ingest loop... no decision...
Hand off to the Rust agent" — one `tick()`/`run_rules()` call after a batch
of mechanical writes, not one per write) — it is not a new pattern invented
for this rung, it is the standing documented shape applied where the
merged site's per-call shape was itself just the degenerate N=1 case of it.

**This changes nothing about WHAT is decided** — Python still makes zero
recognize-vs-mint decisions; it only changes WHEN the pre-existing
`run_rules()` primitive is invoked (once per batch of N writes instead of
once per write), which is scheduling, not agent logic.

**Risk this must rule out empirically, stated before measuring**: with many
pending `Correspondence` nodes sharing an IDENTICAL `transform_key` present
simultaneously before a single `run_rules()` fixpoint pass, does
`blob_mint`'s guard (`Not(Exists(BlobEdge with matching transform_key))`)
correctly mint EXACTLY ONE `BlobEdge` per distinct key and route every other
same-key `Correspondence` to `blob_recognize` within that ONE pass — or can
two pending Correspondences with the same key both see "no existing
BlobEdge" and both mint (a duplicate-BlobEdge race)? This has never been
exercised at this multiplicity by the merged rung (its own real call site
never had more than 66 pending Correspondences, and never more than a
handful sharing a key in one pass). **GO bar for the batching design**: on
the real `computer_architecture` corpus, the number of distinct `BlobEdge`
nodes created must equal the number of distinct `transform_key`s measured in
§1.3's pre-wiring instrumentation probe (139), with zero duplicates. If it
does not, the fallback is per-write `run_rules()` (the merged site's own
proven-safe shape) — slower but correct — reported honestly as a NO-GO on
the batching optimisation specifically (not on the whole extension).

## 6. The Python mapping, concretely

`domains/analogical_thinking.py` (additive; `_pair_witness` itself
byte-unchanged):

- `_agent_node_id(substrate)` — a local copy of the merged site's helper
  (same body), NOT a cross-import from `reflective_faculty.py`. Verified: the
  only cross-reference between these two files today is `reflective_faculty
  .py` lazily importing FROM `analogical_thinking.py` (never the reverse),
  and `_relation_cue_index`'s own docstring states the house convention
  directly — "same pattern, own cache — no cross-import." This rung follows
  that existing convention rather than introducing the first
  `analogical_thinking → reflective_faculty` edge.
- `_canon_pair_shared(shared)` — canonicalises `_pair_witness`'s own
  `out["shared"]` (already a filtered, deterministically-ordered list of
  `(pred, val)` pairs — order follows `_vocabulary_keys`'s global sort) via
  `json.dumps(sorted(shared))`, mirroring `_canon_shared_shape`'s role
  without reusing its body (different input shape — see §1.2).
- `record_pair_correspondence(substrate, node_a, node_b, witness)` —
  mechanical ingest ONLY (no `run_rules()` call — see §5): writes the
  `Correspondence` node (`status=pending`, `shared_count=witness
  ["fixed_count"]`, `transform_key=_canon_pair_shared(witness["shared"])`)
  and the `about_a`/`about_b`/`observed_correspondence` edges, mirroring
  `record_correspondence`'s write shape exactly, minus the inline
  `run_rules()`/status-read-back (moved to the batch caller). Returns the
  same honest non-match shape (a no-op, no exception) when either node id is
  `None` or the substrate has no `add_node`.
- `_resolve_blob_edge(substrate, transform_key)` — local copy of the merged
  site's helper, same equality-scan pattern, no cross-import (same rationale
  as `_agent_node_id`).

Wired at `_compute_analogy:751`, immediately after `witness =
_pair_witness(substrate, vec_s, vec_t)`:
`record_pair_correspondence(substrate, sc, tc, witness)`. `find_analogies`
gains one `native.run_rules()` call after PASS 1's loop.

## 7. Live demonstration plan

1. **Baseline**: confirm the unmodified engine has zero `Correspondence`/
   `BlobEdge` node growth from any `find_analogies` call (grep the merged
   commit's own baseline check for precedent; repeat directly on this
   branch's pre-wiring state).
2. **Real-corpus single call**: `find_analogies(sub, 'computer_architecture',
   ['computer_architecture'], order_n=4)` on the FIXED engine — report
   distinct `BlobEdge` count (predicted 139, per §1.3's pre-wiring probe) and
   `Correspondence` count (predicted 7970), confirming §5's GO bar (no
   duplicate-key BlobEdges).
3. **Repeat-call demonstration** (mirrors the merged rung's §4.2 exactly):
   call the SAME `find_analogies` a second time in the same agent session —
   `BlobEdge` count must stay flat (0 growth); `Correspondence` count must
   exactly double; the RETURNED analogy list must be byte-identical between
   call 1 and call 2 (and byte-identical to the unmodified baseline's
   returned list — persistence must never change the verdict).

## 8. Regression plan

- `tests/test_blob_edge_correspondence.py` — must stay green, UNCHANGED (the
  merged site's own mechanism and tests untouched by this rung).
- `tests/test_analogical_relative_ranking.py`,
  `tests/test_analogical_shape_math_migrated.py` — the real regression
  surface for `find_analogies`/`_compute_analogy`; must stay green, and any
  returned-analogy-list assertions must be byte-identical (persistence is
  additive-only).
- New file: `tests/test_blob_edge_analogy_extension.py` — mint fires once for
  a novel pair pattern; recognize fires with zero `BlobEdge` growth for a
  repeat pattern (both real `Concept` nodes, not synthetic sig lists);
  `_pair_witness`'s own return value byte-unchanged; the real-corpus
  no-duplicate-key GO bar from §5; the two-call repeat demonstration
  (§7.3) with byte-identical returned analogies.
- PAIRED failing-node-id lists (never bare counts) if anything shared
  regresses, per CLAUDE.md's standing rule.

## 9. GO/NO-GO bar, stated before building

- **GO** on the extension overall if: (a) the Γ addition is genuinely
  additive (no edit to the merged seed's productions/rules — confirmed by
  diffing that file after the build, expect zero diff); (b) the real-corpus
  batched run produces exactly as many `BlobEdge`s as distinct
  `transform_key`s with zero duplicates (§5's GO bar); (c) the returned
  analogy list is byte-identical before/after and across repeat calls; (d)
  regression suite green or identically-paired-failing to the pre-existing
  baseline.
- **NO-GO** (fully acceptable, per the charter) if: the duplicate-BlobEdge
  race in §5 is found and the per-write-`run_rules()` fallback is also
  measured to be intractable at 7970 calls/invocation (i.e. neither the fast
  nor the safe form of this mechanism is usable at the site's real scale);
  or if the Γ typing gap in §1.1 turns out to require touching the merged
  seed's own productions to close cleanly (it should not, per §3, but this
  is checked, not assumed).
