# `AddNodeIfAbsent` adoption sweep — PREREG

**Status: PREREG. Registered before any code was edited.** Written in the worktree
`/home/matt/ocelot-dedup-adoption-sweep`, branch `dedup-adoption-sweep`, from `main` at
`abadbab` (`Merge meta-shape-arity-key-fixes: …`, verified with `git log --oneline -1 main`
immediately before `git worktree add`). Results go in
`DEDUP_ADOPTION_SWEEP_RESULTS.md`.

**Charter, verbatim, from the brief:** *"On dedup: the primitive already exists and is
structural (`AddNodeIfAbsent`, `rewrite.rs:1693-1740`), but it is reachable from the
rule-effect layer only — absent from all four sites where this month's four dedup defects
occurred, and adopted at 68/1,079 mint sites (6.3%)."*

**What this rung is NOT:** it is not "wire `AddNodeIfAbsent` into the other 1,011 sites."
Per `SHAPE_TYPE_VOCABULARY_SPIKE.md` §8.3 the discriminator is **scope** — dedup-on-mint is
correct exactly when the node is a *world-model fact* and wrong when it is an
*observation-scoped datum* — so most of the 1,011 are correctly bare. This rung re-derives
the population, filters it by real risk, fixes a small high-confidence batch with live
before/after evidence, and enumerates the rest.

**Pre-registration honesty note:** read-only investigation (grep, AST scans, JSON census,
and *read-only live probes that write no file*) was performed **before** this document, to
make the bars concrete rather than aspirational. Every number quoted below as
"already measured" is reproduced in the RESULTS doc with its script. **No source file,
seed, or test had been edited when this document was committed.**

---

## AR1 — `AddNodeIfAbsent` mechanics, verified precisely

Report, from source, with `file:line`:

1. The exact authoring form (what a seed rule must write to invoke it).
2. The dedup key semantics (which attrs participate, subset or exact).
3. Which layer it is reachable from, and — precisely — whether a raw Python
   `substrate.add_node(...)` call site can adopt it without being restructured as a Rule
   effect first.
4. The three second-order semantics a site must satisfy before adoption is safe:
   fixpoint `progressed` behaviour on the found branch, witness-var binding on the found
   branch, and the cost of the linear `nodes_of_type` scan.

**Bar:** all four answered from source, not from the spike's prose. A wrong answer here
invalidates every fix below, so this is reported first.

## AR2 — the 1,079-site population, re-derived and risk-categorised

**Bar 2.1 (reproduce):** an independent census script over `seeds/*.json` reproduces the
spike's split — 1,011 bare `add_node` + 68 `add_node_if_absent` = **1,079** rule-effect
mint sites — or reports a different number *with the reason*. (Already run: reproduced
exactly. The seed-file count differs by one from the spike's 893, base commit differs;
stated in RESULTS.)

**Bar 2.2 (categorise by fixability shape):** every site classified as
*Rule-effect-reachable* (i.e. `AddNodeIfAbsent` applies directly, a one-token seed edit) or
*raw-Python* (needs the `learn_word`/`learn_recursive_concept` find-or-create shape
instead). Report the counts.

**Bar 2.3 (categorise by scope):** report, with counts, how the population divides on the
spike §8.3 discriminator. This will NOT be a per-site verdict for all 1,079 — that is 1,079
judgement calls and is explicitly out of charter. It will be: the census by minted node
type (427 types), plus a per-type verdict for every type that clears AR3's evidence filter,
plus an explicit statement that the untriaged remainder is untriaged (not "assumed safe").

**Bar 2.4:** the seven node types minted **both** ways (spike §8.2's "interesting row",
left `[unverified]` there) each get a read-and-verdict: is the mixed treatment a real
inconsistency or two correctly-different scopes?

## AR3 — the highest-confidence next-candidate list, by the identity-lookup signature

The four already-found bugs share a signature: **a node type that is later looked up
BY IDENTITY** (a name, a key, a canonical form) where a duplicate causes stale data or
misrouting. Operationalised for this rung as two mechanical scans:

* **Python side:** an AST scan for first-match-wins lookup loops — a
  `for v in <x>.nodes("<Type>")` whose body compares an attr and `return`s/`break`s.
  (Already run: 499 such loops over 126 node types.)
* **Rust side:** codebook loaders that key by a name — `load_parts`' `by_name.insert`
  (`shape_decode.rs`), which is **last-write-wins on a name collision**.

**Bar 3:** the intersection of {bare-minted node types} × {types with such a reader} is
reported in full, and every candidate carried forward to AR4 has **live evidence** — a
probe that produces the duplicate (or the blocked mint) on a booted agent — not a
similarity argument. A candidate with no reproduction is reported as *named, not fixed*.

## AR4 — fixes applied, with live before/after per fix

Registered candidates, with the specific claim each fix must demonstrate. **Both were
reproduced live before this document was written; the before-numbers are therefore
committed here in advance and the RESULTS doc must reproduce them.**

**AR4.1 — `sd_recognize_dim`'s `LatentDimension` (`seeds/shape_decode_loop.json`).**
`SHAPE_AUDIT.md` §4.4 and `SHAPE_TYPE_VOCABULARY_SPIKE.md` §3.4(b) both name this as *the*
canonical scope error: the mint is guarded by the `has_transform` edge, which is a
per-observation fixpoint-termination guard, so *"a `LatentDimension` is a world-model fact:
`latent:rotation90` is the same dimension whichever observation revealed it"* but N frames
mint N of them. **Measured before this doc: three observations of the same rotated tromino
→ 3 `LatentDimension` nodes, 1 distinct attr-set (byte-identical).**
*Bar:* after the fix, same probe → **1** node, and the second and third observations still
reach `recognized_transformed` and still carry a `has_latent_dimension` edge (to the
shared node). `tests/test_dimension_inference_migrated.py`'s `baseline_latent + 1`
assertions must stay green.

**AR4.2 — `sd_mint_generator`'s `DimensionGenerator` (`seeds/shape_decode_loop.json`).**
The rule's own comment records the defect as a scope limit: *"Dedup: one linear generator
per boot (a fuller matrix-keyed dedup for multiple coexisting discovered generators is a
documented scope limit)."* The guard is `Not Exists` a `DimensionGenerator` with
`kind == "linear"` — a *type-coarse* guard standing in for a *content* key, i.e. exactly
the "a number where a shape belonged" shape one level up. **Measured before this doc, in
ONE booted graph, three orbits in sequence (shear A, shear B, unimodular):** the first
mints and reaches `recognized_transformed`; **the second and third reach neither a
generator nor a quantum — they terminate at `status = "decoded"` and are silently
dropped**, because `sd_mint_quantum` and `sd_dedup_existing` both require
`Not gen_explained == 1`. This is a growth failure strictly worse than a duplicate.
*Bar:* after the fix, the same three orbits in one graph mint **three distinct** linear
generators and all three observations reach `recognized_transformed`; a **repeat** of an
already-minted orbit mints **no** fourth generator (the dedup direction); and
`tests/test_gen_infer_migrated.py` stays green (its per-orbit fresh boots are unaffected
by construction, which the run must confirm rather than assume).

**AR4.3 — held open for at most one more candidate**, admitted only if it clears AR3's
live-evidence bar within this rung. Named up front so a null is legible: the two
`ShapeSignature` codebook mints (`vision_identity_seam.json::is_mint`,
`vision_sdloop.json::vq_grow_quantum`), which mint `ShapeSignature{name: obs.key[0], …}`
into the codebook `load_parts` reads last-write-wins. **Registered expectation: this one
may well come back a null** — if observation keys are unique per observation, the minted
names differ, `AddNodeIfAbsent` is a no-op there, and the real defect is
`SHAPE_AUDIT.md` §3.1b's *differently-named same-signature* case, which this primitive
cannot fix. Reporting that as a null is a result.

**Discipline for every fix:** the before/after is a live probe on a booted agent showing
the duplicate (or the stall) and its absence, following
`SHAPE_AUDIT_PATTERN_C_FIXES_RESULTS.md`'s format. "The code now calls a different effect"
is not evidence.

## AR5 — the `MetaShapeMint` name collision: GO / NO-GO

`META_SHAPE_ARITY_AND_KEY_SEPARATOR_FIXES_RESULTS.md` §4.3 measured **23 reachable
collision pairs** in the real attribute-key vocabulary at `shape_decode.rs:5749`'s
`format!("ms_{}", key.join("_"))`, and deliberately did not fix it: the escaping fix would
rename every `MetaShape` ever minted, and the structural fix (a `pred_key` attr guarded on
instead of the name) carries a checkpoint-resume hazard — resumed agents hold `MetaShape`
nodes with no `pred_key`, so a `pred_key`-only guard re-mints them.

**Bar:** a GO/NO-GO with reasoning, and — either way — the design recorded precisely
enough for a future rung to pick up, including any trap found while evaluating it.
Registered in advance so a NO-GO cannot be read as avoidance: **a NO-GO must ship the
design, not just the refusal.**

## AR6 — no regression, paired failing-node-id LISTS

Per `CLAUDE.md`'s standing rule (*"A BASELINE MUST BE A LIST OF NODE IDS, NEVER A COUNT OR
A CHARACTERISATION"*): a pristine baseline is run in the **same worktree** via `git stash`,
same interpreter, same `.so`, and the failing node-id lists are `diff`ed.

Registered suite (the seeds these fixes touch, plus their neighbours):

```
tests/test_dimension_inference_migrated.py
tests/test_gen_infer_migrated.py
tests/test_transform_decode_migrated.py
tests/test_continuous_pose_migrated.py
tests/test_stereo_infer_migrated.py
tests/test_galileo_migrated.py
tests/test_robust_witness_migrated.py
tests/test_axis_mint_novelty.py
tests/test_composer_driver_migrated.py
tests/test_meta_shape_growth_migrated.py   [if present]
tests/test_vision_sdloop*.py               [if present]
```

**Bar:** byte-identical failing-node-id lists before and after, or every difference
attributed to this rung's diff and explained.

---

## Explicitly out of scope

1. **Any blanket sweep of the 1,011 bare sites.** Charter says so; the scope discriminator
   says so.
2. **Any file another thread owns today:** `domains/analogical_thinking.py`,
   `domains/reflective_faculty.py`'s `CapabilityAxis`/rule-selection regions,
   `domains/rule_signature.py`, `runners/dsl/src/py.rs`, `substrate/world_adapter.py`'s
   checkpoint-load region, `seeds/meta_shape_growth.json`'s already-fixed guards. A dedup
   risk found in any of these is **named in the inventory, not fixed**.
3. **A Rust rebuild**, unless a fix genuinely cannot be expressed at the seed level. The
   registered fixes are both seed-JSON edits; if that changes it will be reported as a
   deviation from this PREREG.
4. **Retroactive cleanup of duplicates already in a persisted graph.** Same boundary
   `SHAPE_AUDIT_PATTERN_C_FIXES_RESULTS.md` §6 drew: this is a mint-path fix, not a graph
   migration.
5. **Any claim about production prevalence.** Per `CLAUDE.md`'s standing rule
   (*"synthetic-proven mechanism ≠ benchmark value, report both"*), every fix below is a
   mechanism claim demonstrated on a booted agent; how often it fires on the live daemon is
   not measured and will be stated as unmeasured.

## What would falsify each fix

* **AR4.1 is falsified** if a consumer somewhere needs one `LatentDimension` *node per
  observation* (rather than per dimension) — e.g. reads a per-observation attr off it. The
  RESULTS doc must enumerate every reader of `LatentDimension` and its attrs before
  claiming the fix is safe.
* **AR4.2 is falsified** if a second coexisting linear `DimensionGenerator` degrades
  `DimInfer`'s selection (Occam order, or a spurious explanation) — the
  `test_gen_infer_migrated.py` Occam and noise-floor gates are the check, and a fresh probe
  must confirm the held-rotation Occam case still selects rather than mints **with two
  minted linear generators already in the codebook**.
