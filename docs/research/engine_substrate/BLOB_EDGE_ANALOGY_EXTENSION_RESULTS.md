# BLOB-EDGE ANALOGY EXTENSION — RESULTS

Prereg: `BLOB_EDGE_ANALOGY_EXTENSION_PREREG.md`, same worktree/branch, base
`main` at `b124038`. Worktree
`/home/matt/ozmadev/ocelot-worktrees/blob-edge-analogy-extension`, branch
`blob-edge-analogy-extension`.

**Verdict: GO, with one design correction made mid-build and reported
honestly rather than silently absorbed.** `_pair_witness`'s real call site
(`domains/analogical_thinking.py::_compute_analogy:751`, inside
`find_analogies`'s PASS-1 analogy search) is now wired into the SAME
`seeds/blob_edge_correspondence.json` recognize/mint rules the predecessor
rung built — reused verbatim, unedited. The Γ-schema gap this site's
different operand type opened (`Correspondence`/`BlobEdge` endpoints are
`Concept` nodes here, not `ShapeSignature` nodes) was closed by a new,
strictly additive, productions-only seed. **A genuine batching optimisation
was attempted, measured to produce a real duplicate-BlobEdge race at this
site's much larger call volume, and reverted in favour of the merged site's
own proven-safe per-write shape** — the risk the PREREG named in advance
(§5) as the thing to check, not assume, and it was real.

---

## 1. The operand-type mapping — what changed and why

`_pair_witness(substrate, vec_a, vec_b)` (`analogical_thinking.py:414`,
**byte-unchanged** — pinned by
`test_pair_witness_return_value_is_unchanged`) already returns
`{shared, name_shared, fixed_count, transform}`, where `shared` is the
FILTERED, non-wild, non-absent readout of the `AntiUnifyWitness` template —
the axes both concepts were independently evidenced on, over
`_vocabulary_keys`'s held `FunctionalRole`/`ShapePrinciple`/`MetaShape`
vocabulary. This is the direct analogue of `_shared_shape`'s `res` output
one call removed, but **not interchangeable with it**: `_shared_shape`
expects raw relation tuples anchored onto `RelationCue` nodes by content
identity; `_pair_witness`'s vectors are `[axis:name, value]` pairs over a
different, `analogical_thinking`-owned vocabulary. Feeding one comparator's
operands through the other finds nothing (checked directly against both
functions' code before writing any new code — PREREG §1.2).

**Mapping built** (`domains/analogical_thinking.py`, additive, all local to
this file — no cross-import from `reflective_faculty.py`, following the
existing house convention that file's own `_relation_cue_index` docstring
already states: *"same pattern, own cache — no cross-import"*):

- `_agent_node_id` / `_resolve_blob_edge` — local copies of
  `reflective_faculty`'s helpers, same bodies.
- `_canon_pair_shared(shared)` — canonicalises `_pair_witness`'s own
  `out["shared"]` (`json.dumps(sorted(...))`) into the `transform_key` —
  NOT a reuse of `reflective_faculty._canon_shared_shape`, which serialises
  a differently-shaped input (the raw AntiUnify template including wild
  rows; `_pair_witness` has already filtered those out).
- `record_pair_correspondence(substrate, node_a, node_b, witness)` —
  mechanical ingest: writes the `Correspondence` node
  (`status=pending`, `shared_count=witness["fixed_count"]`,
  `transform_key=_canon_pair_shared(witness["shared"])`) plus
  `about_a`/`about_b`/`observed_correspondence` edges to the two REAL
  `Concept` nodes, then runs the engine (see §4 for why per-write, not
  batched).

Wired at `_compute_analogy:751`, one line after `witness =
_pair_witness(substrate, vec_s, vec_t)`:
`record_pair_correspondence(substrate, sc, tc, witness)`.

## 2. The Γ extension — additive, the merged seed untouched

`seeds/blob_edge_concept_correspondence.json` (`depends_on:
["blob_edge_correspondence"]`) declares exactly 4 new unconditional Γ
productions — `Correspondence-about_a->Concept`,
`Correspondence-about_b->Concept`, `BlobEdge-links_a->Concept`,
`BlobEdge-links_b->Concept` — and **zero new rules**.
`blob_mint`/`blob_recognize`/`blob_no_collapse` are reused verbatim: their
`where` guards read only `status`/`shared_count`/`transform_key` off
`Correspondence`/`BlobEdge` attrs and never inspect the endpoint node's
type, so no rule edit was needed to make them fire correctly for `Concept`
endpoints — only the Γ schema needed extending, confirmed empirically:

```
$ git diff --stat seeds/blob_edge_correspondence.json
(zero output — the merged seed is byte-unchanged)
```

## 3. Real scale at this call site, measured before wiring anything

Instrumented `_pair_witness` on the real booted corpus (`WorldAdapter` +
`load_all_seeds`, 483 Microtheories, 204 with ≥1 Concept, 6302 concepts
total across the nonzero Mts):

```
find_analogies('computer_architecture' x itself, order_n=4):
  concepts=142  pairs_total=20164  pair_witness_calls=7970  results=7346  time=2.48s (baseline)
find_analogies('mathematics' x itself, order_n=4):
  concepts=137  pairs_total=18769  pair_witness_calls=112   results=1406  time=1.25s (baseline)
find_analogies('communication' x itself, order_n=4):
  concepts=136  pairs_total=18496  pair_witness_calls=76    results=374   time=1.02s (baseline)
```

Call volume at this site varies **two orders of magnitude** across real Mts
of near-identical size, driven entirely by how many pairs clear the
pre-existing `order >= 2` surface gate before `_pair_witness` is even
called — this is genuinely `O(n·m)`-shaped at the high end, unlike the
merged site's four call sites (all ≤66 calls/invocation). `jabberwock_reads_
looos.py`/`jabberwock_cross_references_everything.py` were checked and are
**not live**: their Mt names (`looos_claims`, `held_writing_primitives`) do
not exist in the standing seeded corpus, and the latter script hardcodes a
stale absolute import path from an earlier project layout. The only live
standing caller of this exact call shape today is
`domains/reframing_proposer.py::scan_for_recurring_structure`, which today
only ever compares its own small 4-faculty `agent_faculties_scan` Mt — the
large-corpus numbers above are real and reachable (any caller CAN pass
`computer_architecture`), but not exercised by any standing caller yet.

**Real pooling, measured on `computer_architecture` (the largest real Mt)**:
7970 `_pair_witness` calls collapse onto only **139 distinct transform_key
patterns** — 98.3% of calls (7831/7970) reuse an already-seen pattern.
This is a MUCH more dramatic pooling ratio than the merged site's own
measured 23% (`_run_math_bridge`: 66 pairs → 8 minted, 15 recognized) —
directly confirming the PREREG's predicted larger payoff at this site's
scale.

## 4. The batching race — found, not hypothesised

**First design attempt** (as pre-registered, PREREG §5): `record_pair_
correspondence` wrote every pending `Correspondence` node with NO
`run_rules()` call; `find_analogies` called `run_rules()` **once**, after
PASS 1's whole loop completed. Measured directly on `computer_architecture`
x itself:

```
CALL 1 (naive batch, one run_rules() for all 7970 pending writes):
  Correspondence = 7970   BlobEdge = 7970
  distinct transform_keys among BlobEdges = 139
  duplicate-transform_key BlobEdges = 7831
```

**Every one of the 7970 pending Correspondences minted its own BlobEdge** —
`blob_mint`'s guard (`Not(Exists(BlobEdge with matching transform_key))`)
never saw a same-pass sibling's mint. The engine's rule matcher is
semi-naive (`runners/dsl/src/rewrite.rs`'s own comment; matches are found
against a graph snapshot before effects are applied), so within one
`run_rules()` fixpoint pass, many pending nodes sharing one `transform_key`
can all see "no existing BlobEdge" simultaneously. **This is precisely the
risk the PREREG named in advance and registered a GO bar against** (§5:
*"GO bar for the batching design: the number of distinct BlobEdge nodes
created must equal the number of distinct transform_keys... If it does not,
the fallback is per-write run_rules()"*) — the bar was not met, and the
fallback was taken exactly as pre-registered.

**Fix**: `record_pair_correspondence` calls `native.run_rules()` per write —
identical in shape to `record_correspondence`'s own proven-correct pattern
at the merged site. Re-measured on the same corpus:

```
CALL 1 (per-write run_rules(), the merged site's own shape):
  Correspondence = 7970   BlobEdge = 139
  distinct transform_keys among BlobEdges = 139
  duplicates = 0
```

Exactly matches the pre-wiring instrumentation count (139). **This is the
built, shipped behaviour** — `find_analogies` retains one additional
`run_rules()` call after PASS 1 as a harmless idempotent safety net (nothing
is left pending by then), but the correctness-critical run happens per
write, per the merged site's own precedent, not a batched shortcut.

**The real, honest cost of correctness at this site's scale**:

```
computer_architecture x itself:  ~40.0s (per-write)  vs  ~2.5s (unmodified)  — ~16x
mathematics x itself:            ~1.6s  (per-write)  vs  ~1.25s (unmodified) — ~1.3x
communication x itself:          ~1.3s  (per-write)  vs  ~1.0s  (unmodified) — ~1.24x
```

The overhead is ~4-5ms per `record_pair_correspondence` write regardless of
corpus (dominated by per-call `run_rules()` fixed cost, not graph size —
consistent across all three measured scales), so it scales roughly linearly
with call volume. At the small/medium real Mts this is a modest, easily
acceptable overhead (~25-30%); at the largest real Mt it is a genuine ~16x
slowdown for a single self-comparison call. **No standing caller pays this
cost today** (§3) — it becomes real only if/when a future caller requests a
self-comparison over one of the tree's large domain Mts, and is reported
here so that decision is made with real numbers, not assumed away.

## 5. Live before/after demonstration

**Baseline (unmodified `main` @ `b124038`, `git stash`, same worktree, same
moment)**: `find_analogies(sub, 'mathematics', ['mathematics'], order_n=4)`
returns 1406 analogies; zero `Correspondence`/`BlobEdge` nodes exist or are
created (the node types are not referenced by unmodified
`analogical_thinking.py` at all).

**Fixed engine, same call**:

```
CALL 1: find_analogies('mathematics' x itself, order_n=4)
  results=1406   Correspondence=112   BlobEdge=12
CALL 2: same call, same agent session
  results=1406   Correspondence=224   BlobEdge=12
  BlobEdge growth on call 2: 0
```

`Correspondence` count exactly doubles (224 = 2×112) — `_pair_witness`
genuinely recomputes every call, honestly, no shortcut taken there (matching
the merged rung's own finding at its site). `BlobEdge` count is flat
(12 → 12): every one of the 112 correspondences on the second call
RECOGNIZES an already-minted pattern.

**Decision unaffected by persistence — confirmed byte-identical three ways**:

```
res1 == res2                                (this branch, call 1 vs call 2):  True
baseline_result == this_branch_call_1_result (unmodified vs fixed, JSON-dumped): True
```

The second comparison used a full JSON round-trip dump of `find_analogies`'s
returned list (`sort_keys=True`) captured independently from the unmodified
engine (`git stash`) and from the fixed engine, on the identical
`mathematics` corpus — 1406 records, byte-identical in both length and
content. Persistence adds a side channel; it does not touch the verdict.

## 6. What was built

- `seeds/blob_edge_concept_correspondence.json` — 4 Γ productions
  (schema-only), 0 new rules. `blob_edge_correspondence.json` (the merged
  seed) has zero diff.
- `domains/analogical_thinking.py` (additive; `_pair_witness` itself
  byte-unchanged): `_agent_node_id`, `_canon_pair_shared`,
  `record_pair_correspondence`, `_resolve_blob_edge`; one call at
  `_compute_analogy:751` (now `:876` post-edit); one (non-load-bearing)
  `run_rules()` call after `find_analogies`'s PASS 1 loop.
- `tests/test_blob_edge_analogy_extension.py` — 6 new tests: `_pair_witness`
  unchanged; mint fires once for a novel pair found via the real
  `find_analogies` call site, linked to both real `Concept` endpoints;
  recognize fires with zero `BlobEdge` growth for a repeated pattern;
  real-corpus (`mathematics`) no-duplicate-transform_key GO bar; the
  two-call repeat demonstration with byte-identical returned analogies;
  graceful degradation on a missing node id.

## 7. Regression

**`tests/test_blob_edge_correspondence.py` (the merged site's own tests) —
6/6 passed, unchanged.** Confirms `_run_math_bridge`/`_shared_shape` and
their mechanism are completely untouched by this rung.

**Real analogy-search regression surface** —
`tests/test_analogical_relative_ranking.py` +
`tests/test_analogical_shape_math_migrated.py`: 24/24 passed. The returned-
analogy-list assertions in both files (order_n, rationale strings,
corroboration counts, `struct_shared`) are unaffected — persistence is
additive-only, confirmed by these tests still passing verbatim.

**Broader sweep** (`test_author_signature_axis_anchor.py`,
`test_frame_manifold.py`, `test_reframing_proposer.py` — the one live real
caller of this exact `find_analogies` shape —, `test_composer_driver_
migrated.py`, `test_reflex_net_migrated.py`, `test_codebook_axis_
migrated.py`, 68 collected):

```
AFTER (this branch): 3 failed, 65 passed
FAILED tests/test_composer_driver_migrated.py::test_ground_concern_dispatch_parity
FAILED tests/test_composer_driver_migrated.py::test_question_driver_parity
FAILED tests/test_codebook_axis_migrated.py::test_the_short_circuit_ACTUALLY_FIRES_on_the_explained_path
```

All 3 re-run individually against the UNMODIFIED engine (`git stash`, same
worktree, same moment): **identical 3/3 failures**. `test_question_driver_
parity` and `test_the_short_circuit...` are byte-identical to the values
`BLOB_EDGE_SD_LOOP_RESULTS.md` §6 already documented for this exact
pre-existing baseline (`FileNotFoundError: data/hle_math.json`;
`0.020808323329331732 != 0.08843537414965986`). `test_ground_concern_
dispatch_parity` fails identically before and after (a dict-content mismatch
in `relation_head_cases`, unrelated to `analogical_thinking.py` — confirmed
present on the unmodified baseline in this same worktree/moment).
**Paired failing-node-id list: identical before and after, zero new
failures, zero newly-passing.**

New test file: `tests/test_blob_edge_analogy_extension.py`, 6/6 passed
(~70s).

## 8. What this does NOT establish

1. **No compute-time win at small/medium scale, and a real compute-time
   COST at large scale — measured, not assumed.** Unlike the merged site
   (Q4: no measurable win, none claimed), this site's real call volume is
   large enough that persisting correspondences costs real wall-clock time
   (~16x at `computer_architecture`'s 7970-call scale) when the mechanism
   must stay correct (per-write `run_rules()`). The batching optimisation
   that would have amortised this cost was tried and found unsafe (§4); no
   cheaper-but-safe alternative was found or attempted within this rung's
   scope (e.g. a Python-side pre-write dedup against already-resolved
   `transform_key`s, which would touch on deciding recognize-vs-mint in
   Python and was judged out of bounds for this rung — named as a possible
   follow-on, not built).
2. **No standing caller pays this cost today.** The only live caller of this
   exact `find_analogies` shape (`reframing_proposer.py`) compares a
   4-faculty Mt, not a large domain Mt — the 40s number is real and
   reachable but not currently exercised in the standing pipeline.
3. **Rungs 2/3 of the sd ladder still have no correspondence-grain
   analogue**, unchanged from the merged rung's own scoping — not
   re-litigated here.
4. **Two of the four real call sites the merged rung named remain
   unwired**: `connect_concern_to_term` (`reflective_faculty.py:1131` —
   harder, the concern side frequently has no real Concept node) and
   `_run_math_bridge`'s own redundant "find weakest" pass. Both still named
   follow-on, not built, in either rung.
5. **The semi-naive-matcher batching hazard found here (§4) is a genuine,
   reusable finding about the engine, not specific to this seed** — any
   future rung that writes many same-tick nodes competing for one novelty
   guard (the `blob_mint`/`sd_mint_quantum` shape generally) should
   pre-check this exact risk rather than assume batching is safe by
   default. Not filed as a Rust engine bug (the per-pass-snapshot semantics
   may well be intentional/documented elsewhere) — reported here as an
   operational fact discovered by building against it, for the next rung
   that reaches for the same shortcut.

## 9. Reproduce

```bash
cd /home/matt/ozmadev/ocelot-worktrees/blob-edge-analogy-extension
git log --oneline -1 main   # b124038, verified before branching

PYTHONPATH=".:runners/dsl/python" python3 -c "
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains import analogical_thinking as at
a = WorldAdapter(seeds=()); load_all_seeds(a)
sub = a.s
res1 = at.find_analogies(sub, 'mathematics', ['mathematics'], order_n=4)
print('call 1:', len(res1), 'Correspondence:', len(sub.nodes('Correspondence')), 'BlobEdge:', len(sub.nodes('BlobEdge')))
res2 = at.find_analogies(sub, 'mathematics', ['mathematics'], order_n=4)
print('call 2:', len(res2), 'Correspondence:', len(sub.nodes('Correspondence')), 'BlobEdge:', len(sub.nodes('BlobEdge')))
print('identical:', res1 == res2)
"

# New mechanism tests
python3 -m pytest tests/test_blob_edge_analogy_extension.py -q

# Regression (the merged site's own tests + the real analogy-search surface)
python3 -m pytest tests/test_blob_edge_correspondence.py \
  tests/test_analogical_relative_ranking.py tests/test_analogical_shape_math_migrated.py \
  tests/test_author_signature_axis_anchor.py tests/test_frame_manifold.py \
  tests/test_reframing_proposer.py tests/test_composer_driver_migrated.py \
  tests/test_reflex_net_migrated.py tests/test_codebook_axis_migrated.py -q
```
