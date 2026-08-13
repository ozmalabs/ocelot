# BLOB-EDGE SD LOOP — RESULTS

Prereg: `BLOB_EDGE_SD_LOOP_PREREG.md`, same worktree/branch, base `main` at
`03bd3b3`. Worktree `/home/matt/ozmadev/ocelot-worktrees/blob-edge-sd-loop`,
branch `blob-edge-sd-loop`.

**Verdict: GO on all four questions, and BUILT (not just designed).** The
mechanism is a genuine, narrower re-instance of the sd loop's recognize/mint
duality (rungs 1 and 4 only — see §1), correctly split across Γ (schema) and
sd-loop-shaped rules (instance decision) per §2, using the CORRECTED
collapse-time mint criterion (§3, superseding this rung's own original brief
after a mid-flight correction verified against the real `sd_mint_quantum`
code), and it pays for itself as a dedup/persistence mechanism on real data —
not as a compute-time win (§4). Wired at ONE real call site
(`reflective_faculty.py::_run_math_bridge`, line ~7639 post-edit), live
before/after measured on the real `math_capability_shapes.json` corpus, zero
regressions.

---

## 1. Q1 — deep vs superficial, well-typed but narrower than the full ladder

Confirmed by direct reading (not assumed) of `runners/dsl/src/shape_decode.rs`
and `seeds/shape_decode_loop.json`'s rule bodies in full: the sd loop's four
rungs (recognize / transform-in-basis / infer-dimension / mint) decode ONE
`Observation` against a CODEBOOK of many `ShapeSignature` PARTS via beam
search. A "blob edge" is a fact about a PAIR of already-existing nodes, not a
decode of one observation against many candidates — structurally different in
that respect.

**What transfers, and why it is DEEP rather than decorative**:
`domains/reflective_faculty.py::_shared_shape` (line 7170, UNCHANGED by this
rung — the predecessor rung's own axis-anchor fix, `RELATION_CUE_TOKEN_
COLLISION_RESULTS.md`) already anchors both operand signatures onto the SAME
held `RelationCue` nodes (`_relation_cue_index`, 52 held nodes) before
comparing them. `shared_names = sorted(set(by_name_a) & set(by_name_b))` IS
the collapse-onto-existing-structure event the creator's mid-flight
correction names precisely: `I_A -> S + r_A`, `I_B -> S + r_B`, where `S` is
the shared `RelationCue` axis set both operands independently anchor onto.
This is not a post-hoc similarity score computed over two independently
arrived-at answers (which would be the superficial reading, per this
project's own prior MAC-without-FAC diagnosis in `RULES_AS_SHAPE_DESIGN_
SPIKE.md`) — it is the SAME representation (the held `RelationCue` vocabulary)
being reused by construction. Cangiotti/Nappo's full PDF criteria were not
extractable (the arXiv fetch returned only abstract metadata, recorded
honestly in the PREREG rather than fabricated); the assessment above is made
directly against the structural retained-representation test instead,
cross-checked against the paper's stated aim (Hesse-1963-generalising
criteria for genuine inductive, not merely decorative, analogical support).

**What does NOT transfer, named explicitly**: there is no beam search, no
multi-part composition, and no correspondence-grain analogue of
transform-in-basis / infer-dimension (rungs 2–3) — a pairwise `_shared_shape`
comparison has exactly two operands, never a codebook of many correspondence
PARTS to decode against, so there is nothing for a "transform" or "infer a
dimension" rung to operate over. **This build implements rungs 1 (recognize)
and 4 (mint) only, and reports this as the honest scope rather than forcing
an unneeded rung-2/3 analogue into existence.**

## 2. Q2 — Γ and sd-loop, both, cleanly separable (not conflated)

Confirmed empirically, not merely read: `Substrate::add_edge`
(`runners/dsl/src/substrate.rs:1437`) returns `Err(InadmissibleEdge)` on
`CheckOutcome::Type1NoProduction`/`Type2VocabAbsent`, and the PyO3 binding
(`runners/dsl/src/py.rs:1715`) raises a Python exception on rejection — Γ's
admit/deny gate is load-bearing, not advisory. `math_capability_shapes.json`
(the seed that creates the `ShapeSignature` nodes this build operates on)
declares **zero** productions of its own — `ShapeSignature` is a known Γ node
type only because three OTHER seeds happen to reference it as a production
endpoint. None of the existing productions in the tree admit
`Correspondence-about_a/about_b->ShapeSignature`,
`Correspondence-minted->BlobEdge`, or `BlobEdge-links_a/links_b->ShapeSignature`
— confirmed by grep across all `seeds/*.json` before writing this seed's own
productions.

**Built accordingly, split exactly as designed**: `seeds/blob_edge_
correspondence.json` declares 6 unconditional Γ productions (schema: these
edge kinds are LEGAL) and 3 rules (`blob_mint`/`blob_recognize`/
`blob_no_collapse`: which SPECIFIC instance decision applies to a given
computed `Correspondence`) — the same two-part split `shape_decode_loop.json`
itself already keeps in one seed file's `"productions"` vs `"rules"` keys, not
a new pattern invented for this rung.

## 3. Q3 — the corrected mint criterion, verified against the real code

**Original brief (superseded, recorded honestly rather than silently
dropped)**: "mint when the SAME correspondence recurs (recomputed and found
twice)." **Correction received mid-flight** (relayed by the coordinating
session, formalised as an MDL update — storing a new observation costs only
its residual because it preferentially collapses onto existing structure):
edge formation activates AT COLLAPSE TIME, on the FIRST occurrence a
correspondence successfully collapses onto held structure — never deferred to
a second sighting.

**Checked against the real code before accepting the correction, not taken on
its word alone**: `sd_mint_quantum`'s own NOVELTY guard
(`seeds/shape_decode_loop.json`, quoted in full in the PREREG) —
`Not(Exists(NodesOfType('CapabilityAxis'), induced==1 AND
capability_keys==obs.key))` — fires on the FIRST residual with no matching
existing axis; it never waits for a repeat. What recurrence actually gates in
the shipped code is de-duplication of a SECOND identical residual
(`sd_dedup_existing`'s terminal `recognized_duplicate` status), never the
INITIAL mint. **The correction fixed a real mis-reading of the mechanism the
original brief asked this rung to reuse — verified against the primary source,
not accepted on authority.**

**Built exactly this way**: `blob_mint` fires the FIRST time a
`Correspondence`'s `transform_key` has no existing matching `BlobEdge`
(mirrors `sd_mint_quantum`'s guard shape, substituting `transform_key`
identity for `capability_keys` identity); `blob_recognize` fires whenever a
matching `BlobEdge` already exists (mirrors `sd_dedup_existing`, including its
documented engine constraint — see next paragraph); `blob_no_collapse`
terminates a `Correspondence` with `shared_count<=0` honestly (no larger
residual-accumulation concept exists at the pairwise-correspondence grain, so
this is reported as out of the sd ladder's normal scope rather than forced
into one).

**A real engine constraint, reused rather than reinvented**: `sd_dedup_
existing`'s own comment states *"add_edge targets must be match-bound vars in
this engine"* — a rule cannot `add_edge` to a node found via a `Term` search
(`Exists`) within the same rule. Confirmed independently by reading
`vg_mint_kernel_from_patch` (`seeds/vision_growth.json`), whose 3-triple match
exists precisely so its `add_edge` target is match-bound rather than
Term-found. `blob_mint`/`blob_recognize`/`blob_no_collapse` all use a
3-triple match (`ag-observed_correspondence->c`, `c-about_a->na`,
`c-about_b->nb`) so `blob_mint`'s `add_edge blob links_a na` /
`links_b nb` targets real match-bound vars; `blob_recognize` — like
`sd_dedup_existing` — sets `status="recognized"` only, with NO new edge to
the found `BlobEdge` (Python resolves it afterward via
`_resolve_blob_edge`'s equality scan on `transform_key`, the exact
`induce_concern`/`capability_keys` read-back pattern already used elsewhere in
this file).

## 4. Q4 — cost/benefit, measured, not assumed

**Prediction registered in the PREREG**: no measurable compute-time win at
today's call volume (four real call sites, none a hot loop); the honest case
is dedup + a working demonstration, not a production optimisation. **This
held.** The `_shared_shape`/`AntiUnifyWitness` computation itself is NOT
skipped by this design — `blob_mint`/`blob_recognize` decide what happens to
the RESULT, exactly as `sd_recognize`/`sd_mint_quantum` never skip
`ShapeDecode`'s own decode either. The measured win is graph-growth control
(dedup), demonstrated live below.

### 4.1 Real-corpus measurement (`_run_math_bridge`, no synthetic data needed)

Real `math_capability_shapes.json` × real `RelationCue`-anchored
`_shared_shape` comparisons, wired at `_run_math_bridge`'s primary math↔faculty
loop (`reflective_faculty.py`, `for mn in math_names: for fn in facs.items():`):

```
one full _run_math_bridge(agent, None) call:
  total Correspondence nodes created:  66   (every math x faculty pair)
  status breakdown:  minted=8   recognized=15   no_collapse=43
  distinct minted transform_keys:      8
  BlobEdge nodes created:              8   (== distinct minted transform_keys, exactly)
  recognized correspondences' transform_keys: 1 distinct key, and it is a
    SUBSET of the minted keys (verified: recognized_keys <= minted_keys)
```

66 real pairs collapse to 8 distinct held structural patterns; 15 of the 66
pairs (23%) reuse an ALREADY-minted pattern rather than manufacturing a new
node — real, measured pooling (message 2's "blobby" idea), not asserted.

### 4.2 Live before/after — the load-bearing demonstration

**BEFORE (unmodified `main` @ `03bd3b3`, verified directly, not assumed)**:
`git show 03bd3b3:domains/reflective_faculty.py | grep -c
"Correspondence\|BlobEdge"` → **0** — the node types do not exist in the
baseline at all. Every call to `_shared_shape`/`_run_math_bridge` recomputes
from scratch with categorically no possibility of memory, on the first call
and every call after it.

**AFTER (this branch), calling `_run_math_bridge` TWICE in the SAME agent
session**:

```
=== CALL 1 ===
Correspondence nodes: 66   BlobEdge nodes: 8
=== CALL 2 (same agent, same graph) ===
Correspondence nodes: 132  BlobEdge nodes: 8
BlobEdge growth on call 2: 0
connection identical across both calls: True
```

`Correspondence` count exactly doubles (132 = 2×66) — the witness computation
genuinely reruns every call, honestly, no shortcut taken there. `BlobEdge`
count is FLAT (8 → 8) — every one of the 66 correspondences on the second call
is RECOGNIZED against an already-minted pattern; zero new nodes. **This is
`sd_recognize` firing instead of `sd_mint_quantum` on the second occurrence,
demonstrated as graph growth stopping, not as compute time dropping** — the
correct, honestly-scoped form of "recognized/reused from the minted blob-edge"
per §4's registered prediction (the SLICE's requested demonstration, delivered
in the form the corrected mechanics actually support).

**The decision itself is unaffected by persistence** — `_run_math_bridge`'s
returned `connection` (`{'math': 'phi_bounded_recursion', 'faculty':
'residual_recurrence', 'shared_leaves': 14, ...}`) is BYTE-IDENTICAL between
the unmodified baseline and this branch's first call, and identical again
between this branch's first and second calls — confirmed by direct comparison,
not assumed. This build is additive: it persists a fact about a computation
that already happened; it does not change what the computation decides.

## 5. What was built

- `seeds/blob_edge_correspondence.json` (`depends_on:
  ["math_capability_shapes"]`) — 6 Γ productions (schema) + 3 rules
  (`blob_mint`/`blob_recognize`/`blob_no_collapse`, instance decision),
  mirroring `sd_mint_quantum`/`sd_dedup_existing`'s exact rule shape. No new
  Rust Term — every Term used (`AntiUnify`, `FixedCount`, `Exists`,
  `NodesOfType`, plus rule-effect `add_node`/`add_edge`/`set_attr`) already
  existed; no engine rebuild was required (verified: the pre-existing
  compiled `substrate_rs` binary ran this seed and its rules with zero
  changes to Rust source).
- `domains/reflective_faculty.py` (additive; `_shared_shape` itself
  byte-unchanged — pinned by `test_shared_shape_return_value_is_unchanged`):
  `_agent_node_id`, `_shape_signature_node_id`, `_canon_shared_shape`,
  `record_correspondence` (mechanical ingest, mirrors
  `domains/meta_shape.py::observe`'s exact pattern — write node + edges,
  `run_rules()`, read back `status`, no Python decision), `_resolve_blob_edge`
  (mechanical read-back, mirrors the `induce_concern`/`capability_keys`
  pattern). Wired at `_run_math_bridge`'s primary loop only (line ~7639
  post-edit); the redundant "find weakest" pass
  (`_run_math_bridge`'s `worst` computation) and the other two real
  `_shared_shape`/`_pair_witness` call sites (`connect_concern_to_term`,
  `analogical_thinking.find_analogies:751`) are named follow-on, not built —
  per the charter's explicit "pick ONE."
- `tests/test_blob_edge_correspondence.py` — 6 new tests: `_shared_shape`
  unchanged; mint fires once + links both real endpoints; recognize fires on
  a repeat with zero `BlobEdge` growth; `no_collapse` for a genuinely disjoint
  pair; the real-corpus two-call demonstration (§4.2); graceful degradation
  when a real node id is missing on either side.

## 6. Regression

Scoped set (`tests/test_author_signature_axis_anchor.py`,
`tests/test_composer_driver_migrated.py`, `tests/test_reflex_net_migrated.py`,
`tests/test_codebook_axis_migrated.py`, `tests/test_codebook_partition_
migrated.py`, `tests/test_cost_scheduling.py`,
`tests/test_nl_concern_front_door.py`, 83 collected):

```
AFTER (this branch):  70 passed, 10 skipped, 3 failed (564.21s)
FAILED tests/test_composer_driver_migrated.py::test_ground_concern_dispatch_parity
FAILED tests/test_composer_driver_migrated.py::test_question_driver_parity
FAILED tests/test_codebook_axis_migrated.py::test_the_short_circuit_ACTUALLY_FIRES_on_the_explained_path
```

All 3 re-run individually against the UNMODIFIED engine (`git stash`, same
worktree, same moment): **identical 3/3 failures**, same assertion values
(`test_the_short_circuit...`: `0.020808323329331732 != 0.08843537414965986`,
byte-identical on both sides), `test_question_driver_parity`'s failure is the
same `FileNotFoundError: data/hle_math.json` (absent in this worktree, an
environment-conditional pre-existing gap, not code — this is the SAME
paired-failure set the immediate predecessor rung
(`RELATION_CUE_TOKEN_COLLISION_RESULTS.md` §7.1) already found and reported
identically). **Paired failing-node-id list: identical before and after, zero
new failures, zero newly-passing.**

New test file: `tests/test_blob_edge_correspondence.py`, 6/6 passed (62.05s).

## 7. What this does NOT establish

1. **No compute-time win, and none was claimed.** The AntiUnify/FixedCount
   computation itself is not skipped by recognize — only redundant `BlobEdge`
   node creation is avoided. A future rung could explore short-circuiting the
   witness computation itself for an EXACT repeat pair (not just a
   repeat transform_key across different pairs), which this build does not
   attempt.
2. **Rungs 2/3 of the sd ladder (transform-in-basis, infer-dimension) have no
   correspondence-grain analogue here**, and none was built — §1 explains why
   forcing one would not be a faithful re-instance.
3. **Only ONE of four real call sites is wired.** `connect_concern_to_term`
   (`reflective_faculty.py:1131`, harder — the concern side frequently has no
   real Concept node, `concept = "(induced from observation)"`),
   `_run_math_bridge`'s own `worst`-finding pass, and
   `analogical_thinking.py::find_analogies:751` (a different file, different
   operand shape — `AntiUnifyWitness` over concept vectors, not
   `AntiUnify`/`FixedCount` over `RelationCue`-anchored signatures) are all
   named, not touched.
4. **Message 1's multi-axis salience system (summing shape + kind +
   provenance + scope) is not built** — this spike is the mint/persistence
   half only, as scoped.
5. **The Cangiotti/Nappo paper's actual formal criteria were not read** — the
   arXiv fetch returned abstract metadata only; §1's deep/superficial
   judgment is made against a structural proxy test (retained representation
   vs. post-hoc score) cross-checked against the paper's stated aim, not
   against its worked formal apparatus.
6. **No claim about the other ~40 shape-comparison sites `SHAPE_AUDIT.md`
   found across the tree** — only this one call site is measured.

## 8. Reproduce

```bash
cd /home/matt/ozmadev/ocelot-worktrees/blob-edge-sd-loop
git log --oneline -1 main   # 03bd3b3, verified before branching

# No Rust changed -- the existing compiled substrate_rs runs this unmodified.
PYTHONPATH=".:runners/dsl/python" python3 -c "
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains import reflective_faculty as rf
a = WorldAdapter(seeds=()); load_all_seeds(a)
print('call 1:', rf._run_math_bridge(a, None)['connection'])
print('correspondences:', len(a.s.nodes('Correspondence')), 'blobs:', len(a.s.nodes('BlobEdge')))
print('call 2:', rf._run_math_bridge(a, None)['connection'])
print('correspondences:', len(a.s.nodes('Correspondence')), 'blobs:', len(a.s.nodes('BlobEdge')))
"

# New mechanism tests
python3 -m pytest tests/test_blob_edge_correspondence.py -q

# Regression
python3 -m pytest tests/test_author_signature_axis_anchor.py tests/test_composer_driver_migrated.py \
  tests/test_reflex_net_migrated.py tests/test_codebook_axis_migrated.py \
  tests/test_codebook_partition_migrated.py tests/test_cost_scheduling.py \
  tests/test_nl_concern_front_door.py -q
```
