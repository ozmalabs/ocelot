# `AddNodeIfAbsent` adoption sweep — RESULTS

**Prereg:** `DEDUP_ADOPTION_SWEEP_PREREG.md`, committed (`3638c60`) before any code was
edited. Worktree `/home/matt/ocelot-dedup-adoption-sweep`, branch `dedup-adoption-sweep`,
from `main` at `abadbab`. Engine `8963fb4dccaa`, byte-identical (`sha256`) to the primary
tree's `.so`; no Rust rebuild — both fixes are seed JSON.

**Verdict: 2 fixes GO (AR4.1, AR4.2), 1 registered candidate NULL (AR4.3), AR5 NO-GO with
the design and a newly-found trap recorded. AR6 clean: 62-file paired sweep, failing
node-id lists byte-identical in 3 of 4 chunks and the single difference traced to a flake
the test's own docstring characterises at ~10% per fresh process.**

---

## The one thing worth reading if you read nothing else

**The `AddNodeIfAbsent` adoption number is the wrong frame, and following it literally
would have made the tree worse.** Adopting it at `sd_mint_generator` *as a drop-in* —
swapping the effect and deleting the coarse guard it was standing in for — produced a
**live non-terminating loop**: `codebook_epoch` ran from 1 to 20,001 in a single
`run_rules` call (measured, §4.2.2), because `AddNodeIfAbsent`'s found-branch sets no
`progressed` flag but *the rule's other effects do*, and nothing else in that rule was a
per-observation termination guard. The coarse guard was load-bearing for two things at
once — identity **and** termination — and only one of them is `AddNodeIfAbsent`'s job.

Pulling that thread found the real defect, which is not a duplicate at all: the guard
`Not Exists a DimensionGenerator with kind == "linear"` capped the whole graph at **one
discovered linear generator for its entire life**, and because `sd_mint_quantum` and
`sd_dedup_existing` both require `Not gen_explained == 1`, a second novel orbit reached
**neither a generator nor a quantum** — it terminated at `status = "decoded"` and was
silently dropped. Three orbits in one graph, only the first resolved (§4.2.1). And the
*third* layer down: once more than one linear generator was allowed to exist, they all
minted under the **same name** (`genlin_<base_shape>`), and `load_generators`
(`shape_decode.rs:457`) is `by_name`-keyed **last-write-wins**, so only the last one
loaded and previously-explained orbits stopped being explainable (§4.2.3).

**One "6.3% adoption" line hid a three-deep stack: a termination guard doing identity
work, an identity guard capping growth, and a name-keyed codebook index silently dropping
entries.** The fix is all three together, and no part of it is "call the dedup primitive
more often."

---

## AR1 — `AddNodeIfAbsent` mechanics, verified from source

Implementation `runners/dsl/src/rewrite.rs:1693-1740` (line range in the spike confirmed
exact), parser `runners/dsl/src/graph_rules.rs:261-277`.

**1. Authoring form.** A rule-effect list entry:
`["add_node_if_absent", "<witness_var>", "<NodeType>", {<attrs>}]` — positionally
identical to `add_node`; the parser requires `parts.len() >= 4` and takes the same three
arguments. **The seed edit is one token.**

**2. Dedup key.** The author's attrs, resolved to concrete `Value`s first, then a linear
scan of `graph.nodes_of_type(type_)` for the first node whose attrs include **every**
`(k, v)` pair. **Subset semantics** — an existing node may carry attrs the author did not
mention (`rewrite.rs:1701-1706`, verbatim in the source comment). The consequence that
matters in practice: **every attr you write participates in the key**, so a site that
writes one per-occasion attr (a `k`, a timestamp, an observation id) dedups on nothing.
This is exactly why AR4.1's fix is partial and AR4.2's needed a name change first.

**3. Reachable layer — precisely.** It is a variant of `enum Effect`, constructed only by
`graph_rules.rs`'s effect parser. **It is not a graph operation and not a `Substrate`
method**: there is no `add_node_if_absent` on `Substrate` (`substrate.rs:1419-1435` is the
unconditional `add_node`), none on the PyO3 surface, none in `term_to_subgraph`,
`production_to_subgraph`, `add_rule`, or `load_seed_manifest`. **A raw Python
`substrate.add_node(...)` call site therefore CANNOT adopt it at all without first being
re-expressed as a Rule effect.** The spike's "reachable from the rule-effect layer only"
is exactly right and is a hard constraint, not a stylistic one — it is why all three
`SHAPE_AUDIT_PATTERN_C_FIXES` fixes were Python find-or-create rather than this primitive.

**4. Three second-order semantics a site must satisfy before adopting.**

| | behaviour | why it matters |
|---|---|---|
| fixpoint `progressed` | **found ⇒ not set** (no `UndoStep` either); **minted ⇒ set** | good in isolation, but it means the primitive *cannot* terminate a rule on its own — see the loop in §4.2.2 |
| witness binding | found ⇒ `b.insert(new_var, existing)` | downstream `add_edge` still works and attaches to the **shared** node (this is what makes AR4.1 correct); a downstream `set_attr` would **mutate the shared world fact**, which is a real hazard for any site that does one |
| cost | linear scan of `nodes_of_type` per firing | fine at codebook scale (tens of nodes); would not be fine on `Message`/`Goal` populations |

---

## AR2 — the population, re-derived and categorised

### 2.1 Reproduced exactly

Census over `seeds/*.json` (script in §8):

| | count |
|---|---|
| seed files parsed as dicts | 892 (spike: 893 — different base commit) |
| rule-carrying seeds | 635 |
| rule-effect mint sites, `add_node` | **1,011** |
| rule-effect mint sites, `add_node_if_absent` | **68 (6.3%)** |
| **total** | **1,079** |
| distinct node types minted by rule effects | 427 |
| types minted bare only | 389 |
| types minted with dedup | 38 |
| types minted **both** ways | **7** |

The spike's numbers reproduce exactly. **The 1,079 is real.**

### 2.2 Fixability shape — the population is 100% Rule-effect-reachable, and that is the smaller half of the problem

All 1,079 are rule effects by construction of the census, so `AddNodeIfAbsent` is a
one-token edit at every one of them. The *other* population — the one where the four
known bugs actually lived — is not in the 1,079 at all:

| layer | mint call sites | can adopt `AddNodeIfAbsent`? |
|---|---|---|
| seed rule effects | **1,079** | yes, one-token |
| Python `.add_node(` in `domains/` | 1,287 | **no** — needs the `learn_word` find-or-create shape |
| Python `.add_node(` in `substrate/` | 104 | **no** |
| Python `.add_node(` in `scripts/` | 1,849 | no (measurement code, mostly out of scope) |
| Python `.add_node(` in `tests/` | 2,704 | no (fixtures) |
| Rust `insert_node(` in `runners/dsl/src/` | 163 | no |

**Three of this month's four dedup defects were in the 1,391 `domains/`+`substrate/`
Python sites, and one was in the Rust mirror. Zero were in the 1,079.** Reporting the
adoption rate over the 1,079 measures the layer where the bugs *weren't*. That is not a
criticism of the spike — it flagged the layering itself — but it is the correction a
reader of the "6.3%" number needs.

### 2.3 Scope categorisation — 79% of the bare sites have no identity reader at all

Per spike §8.3, dedup-on-mint is right only for world-model facts. Operationalised as
"does anything anywhere look this type up by identity" (AR3's scan):

| | types | bare sites |
|---|---|---|
| bare-minted types with **no** first-match-wins reader anywhere | 373 | **799 (79%)** |
| bare-minted types with a reader in `tests/` or `scripts/` only | 4 | 33 |
| bare-minted types with a reader in `domains/` or `substrate/` | **19** | **179** |

**The 799 are not "assumed safe" — they are *unread by identity*, which is the operational
form of observation-scoped.** A node nothing ever looks up by name/key cannot cause the
stale-data or misrouting failure all four known bugs caused. That is a weaker claim than
"correctly scoped" and it is the claim the evidence supports; the untriaged remainder is
untriaged, not cleared.

Of the 179 at-risk-shaped sites: 36 already carry a self-type `NodesOfType` guard, 122
carry some `Not` in the `where`, 21 carry no `Not` guard at all. (This classifier is
coarse — a `Not Exists` over an *edge* is the tree's more common mint-once idiom and does
not mention the node type, so "self-type guard" undercounts. Stated so the number is not
reused as a defect count.)

### 2.4 The seven both-way types — read, and verdicts (spike §8.2 left this `[unverified]`)

| type | mixed how | verdict |
|---|---|---|
| `Axis` | `projection.json` dedups on `proj_role`; `bigville_degradation_learn.json` mints `{minted}` bare | **not an inconsistency** — different seeds, different objects sharing a bare type name |
| `Hypothesis` | 3 seeds dedup on a content key; `learning_core.json::rule_hypothesis_mint` bare | **correct as-is** — a per-trial hypothesis (`formed_tick`, `trials`) is observation-scoped |
| `Law` | `physics_derivation.json` dedups (`quantity`/`regime` — a discovered world fact); `bigville_legislature.json::leg_enact` bare | **correct as-is** — an enacted law is an authored artefact with mutable `status` |
| `ParetoCandidate` | 2 dedup, 17 bare | **correct as-is** — a frontier candidate is per-episode by definition; the two dedup'd ones key on `source_affordance_ref`/`morphology_epoch`, i.e. a per-morphology prior |
| `EmbodiedMotorProgram` / `EmbodiedMotorBootstrapSelection` / `EmbodiedMotorSelectionEpochRequest` | mint-from-morphology dedups, per-episode selection/revision bare | **correct as-is** — the same prior/episode split |

**Seven for seven, the mixed treatment is two correctly-different scopes, not a drift.**
This is the strongest single piece of evidence in this document that the scope
discriminator is real and that seed authors have been applying it, undeclared, correctly.

---

## AR3 — the identity-lookup candidate list

Two mechanical scans (both in §8):

* **Python:** AST scan for `for v in <x>.nodes("<Type>")` loops whose body compares an attr
  and `return`s/`break`s — **499 first-match-wins lookups over 126 node types**.
* **Rust:** name-keyed codebook loaders. Two found, both `by_name.insert` **last-write-wins
  on a name collision**: `load_parts` (`shape_decode.rs:239-326`, every `ShapeSignature`/
  `MetaShape`/codebook grain) and `load_generators` (`shape_decode.rs:457`, every
  `DimensionGenerator`). The second is not named in any prior document and is what §4.2.3
  turned on.

Intersection with the bare-mint census, `domains/`+`substrate/` readers only, top rows:

| bare sites | type | core reader | live evidence found? |
|---|---|---|---|
| 4 | `ShapeSignature` | 9 files + `load_parts` (Rust) | **null** — §4.3 |
| 4 | `LatentDimension`* | `falling_world.py` + 3 test suites | **YES — 3 byte-identical nodes**, §4.1 |
| 1 | `DimensionGenerator`* | `load_generators` (Rust) | **YES — stall + name shadowing**, §4.2 |
| 47 | `Goal` | `reading_norms.py`, `world_adapter.py` | not probed — observation-scoped by construction (a Goal is per-episode) |
| 35 | `Message` | `world_adapter.py` | not probed — observation-scoped |
| 30 | `CognitiveTask` | `photon_eye.py` | not probed |
| 22 | `SelfConcern` | `reflective_faculty.py` | **already fixed** (gap_awareness content-dedup guard, CLAUDE.md 2026-07-09) |
| 7 | `CapabilityAxis` | `reflective_faculty.py` | **already fixed today** (Pattern C AR1 + separator escape) |
| 12 | `AnalysisStage`, 5 `Impasse`, 3 `Observation`, 3 `Operator`, 2 `GoalResidual`, 2 `Intent`, 1 each `Experiment`/`PlanAct`/`MetaShape`/`Program`/`ReflexNet`/`UploadTextReadStage`/`Sign` | 1 core reader each | not probed — inventory §6 |

*`LatentDimension` and `DimensionGenerator` were reached from `SHAPE_AUDIT.md` §4.4 and
the `sd_mint_generator` rule comment respectively, then confirmed by this scan — reported
that way rather than claiming the scan found them cold.

---

## AR4 — the fixes, live before/after

Both are in `seeds/shape_decode_loop.json` (v1.8.0 → **v1.9.0**). Diff: **+44/−44 across
2 files** (the seed, and `scripts/genmint_build_seeds.py`, the stale one-off builder that
emits three of these rules — kept in sync so the divergence does not grow, with a
stale-builder warning added because it has not tracked the seed since v1.7.0 and
re-running it would delete v1.8.0's agnosia guards).

### 4.1 — `sd_recognize_dim`'s `LatentDimension`: GO

**The defect, as named:** `SHAPE_AUDIT.md` §4.4 — *"A `Transform` genuinely is
per-observation data. A `LatentDimension` is a world-model fact: `latent:rotation90` is the
same dimension whichever observation revealed it."* Both are minted by the same rule, under
the same `has_transform`-edge guard, which is a **per-observation fixpoint-termination
guard**, not a dedup.

**Live BEFORE** (three Observations of the same k=1-rotated tromino, one held
`ShapeSignature` codebook entry):

```
obs0 status=recognized_transformed covered_by=part_tromino
obs1 status=recognized_transformed covered_by=part_tromino
obs2 status=recognized_transformed covered_by=part_tromino
LatentDimension nodes: 3   (baseline 0)
  x3 {"generator":"rotation90","generators":["rotation90"],"k":1,"ks":[1],
      "name":"latent:rotation90","source":"dim_infer"}  -> [#770, #773, #776]
DISTINCT attr-sets: 1   TOTAL nodes: 3
```

**Live AFTER** (same probe, same seed set, one-token change):

```
obs0 status=recognized_transformed covered_by=part_tromino
obs1 status=recognized_transformed covered_by=part_tromino
obs2 status=recognized_transformed covered_by=part_tromino
LatentDimension nodes: 1   (baseline 0)
  x1 {...same attrs...} -> [#770]
DISTINCT attr-sets: 1   TOTAL nodes: 1
```

All three observations still reach `recognized_transformed`; observations 2 and 3 bind
`ld` to the **existing** node and still get their own `has_latent_dimension` edge (the
witness-binding semantics of AR1 item 3 are what make this work).

**The `Transform` mint one effect above was deliberately left as `add_node`.** It is the
observation-scoped half of the same pair, and deduping it would be the exact opposite
error. The two effects sitting adjacent in one rule, one now dedup'd and one not, is the
scope distinction made visible in the seed.

**Known residual, stated:** `k` and `ks` are part of the dedup key, so the same generator
observed at a **different k** still mints a second `LatentDimension`. The correct home for
`k` is the `Transform` (where it already is), but three test suites assert `ld_at.get("k")`
(`test_dimension_inference_migrated.py:271, 477, 558, 678`), so removing it is its own
rung. **This fix collapses byte-identical duplicates — exactly what §4.4 named — and no
more.**

### 4.2 — `sd_mint_generator`'s `DimensionGenerator`: GO, after two corrections found by measurement

The rule's own comment recorded the defect as a scope limit: *"Dedup: one linear generator
per boot (a fuller matrix-keyed dedup for multiple coexisting discovered generators is a
documented scope limit)."*

#### 4.2.1 What the scope limit actually costs — measured

Three orbits (shear A, shear B, unimodular) of one base shape, presented **in sequence to
ONE booted graph** (every existing gate boots fresh per orbit, so this had never been run):

```
BEFORE
orbit [1,0,1,1] status=recognized_transformed  new_axes=0  lingens=[(1,0,1,1)]
orbit [1,1,0,1] status=decoded                 new_axes=0  lingens=[(1,0,1,1)]
orbit [2,1,1,1] status=decoded                 new_axes=0  lingens=[(1,0,1,1)]
```

Orbits 2 and 3 mint **nothing** — not a generator, not a quantum — and terminate at
`status = "decoded"`. `sd_mint_quantum` and `sd_dedup_existing` both carry
`Not gen_explained == 1` (verified in the seed), so once GenInfer has explained an orbit
the *only* rule that can consume it is `sd_mint_generator`, and the coarse guard had
already fired. **A growth failure strictly worse than a duplicate: the observation is
silently dropped.**

#### 4.2.2 The drop-in adoption is WRONG — a live non-terminating loop

First attempt: swap `add_node` → `add_node_if_absent`, delete the coarse guard. Measured:

```
orbit [1,1,0,1] iter 0: status=decoded  87.4s  epoch=20001.0
orbit [1,1,0,1] iter 1: status=decoded  87.2s  epoch=40001.0
orbit [1,1,0,1] iter 2: status=decoded  84.6s  epoch=60001.0
```

`codebook_epoch` +20,000 per `run_rules` — the fixpoint iteration cap, hit every call.
`AddNodeIfAbsent`'s found-branch sets no `progressed`, but the rule's other three effects
(`add_edge`, the epoch bump, the status write) do; `sd_redecode` then re-arms the
observation on the bumped epoch; `sd_redecode` **does not clear `gen_checked`/
`gen_explained`** (verified — it clears only the transform and dim flags), so the mint
guard is satisfied again immediately. The coarse guard had been carrying **termination**,
not just identity.

**Correction 1:** add the per-observation termination guard the rule always needed and
never had — `Count(Neighbours(obs, "gen_minted")) == 0`, the same edge the rule's own
effects already write, and the same idiom `sd_recognize_dim` uses with `has_transform` and
`sd_mint_quantum` uses with `minted`.

#### 4.2.3 The name shadowing underneath it

With termination fixed, three generators minted — and a **repeat** of orbit 1 then failed
to be explained (`dim_explained=False`), which it had been explained before the change.
Cause: all three minted generators were named `genlin_base_L` — the name was
`"genlin_" + GenInfer(field:"base")`, i.e. **derived from the base shape, not from the
map** — and `load_generators` (`shape_decode.rs:457`) is `by_name`-keyed last-write-wins,
so only the last of the three ever loaded. The `kind == "linear"` cap had been hiding a
name-collision defect one layer down.

**Correction 2:** derive the name from the content —
`StringConcat(["genlin_", ToJsonString(GenInfer(field:"matrix"))])` → `genlin_[1,0,1,1]`.
(Noted in passing, an unrelated silent-drop worth someone's attention: `StringConcat`
**silently drops a non-string part** — `StringConcat("genlin_", Lit([1,0,1,1]))` evaluates
to `"genlin_"`, no error. `ToJsonString` is the working form.)

#### 4.2.4 Live AFTER

```
orbit [1,0,1,1] status=recognized_transformed  new_axes=0  lingens=[(1,0,1,1)]
orbit [1,1,0,1] status=recognized_transformed  new_axes=0  lingens=[(1,0,1,1),(1,1,0,1)]
orbit [2,1,1,1] status=recognized_transformed  new_axes=0  lingens=[(1,0,1,1),(1,1,0,1)]
orbit [1,0,1,1] status=recognized_transformed  new_axes=0  lingens=[(1,0,1,1),(1,1,0,1)]

generators: genlin_[1,0,1,1] -> (1,0,1,1)
            genlin_[1,1,0,1] -> (1,1,0,1)
LatentDimension names: latent:genlin_[1,0,1,1]
                       latent:genlin_[1,1,0,1]
                       latent:genlin_[1,0,1,1]+genlin_[1,1,0,1]
```

**All four observations resolve. `codebook_epoch` bumps once per real mint (1 → 2), and
the fixpoint settles inside a single `run_rules`** (0.0s, versus 87s at the cap).

**A registered prediction was wrong and the outcome is better than it.** The PREREG's
AR4.2 bar said "mint three distinct linear generators." Only **two** minted: the third
orbit `[2,1,1,1]` was explained as a **composition** of the two already held
(`latent:genlin_[1,0,1,1]+genlin_[1,1,0,1]`, and its `gen_checked` was never set — the
generator rung was never reached). That is v1.6.0's Occam ladder working exactly as
designed: compose what you hold before minting anything new. The *capability* bar — every
novel orbit resolves, a repeat mints nothing — is met; the *number* in the bar was mine
and it was wrong. Recording it rather than restating the bar to match the result.

**Known residual, stated:** the dedup key includes `name`, and the name is
matrix-derived, so a byte-identical matrix now dedups regardless of which base shape
discovered it — the residual noted in the seed comment while the name was base-derived is
**closed by correction 2**. What remains open is `params`, which is a hardcoded
`[1,2,3,4,5,6]` literal in the mint (a scalar knob, in CLAUDE.md's sense, that nobody has
looked at); it is constant today so it does not affect the key.

### 4.3 — `ShapeSignature` codebook mints: NULL, as the PREREG predicted it might be

`vision_sdloop.json::vq_grow_quantum` and `vision_identity_seam.json::is_mint` mint
`ShapeSignature{name: obs.key[0], signature: obs.signature, …}` into the codebook
`load_parts` reads last-write-wins.

**Probe (seed actually installed — a first attempt under bare `boot_core` did not install
`vision_sdloop` and was discarded rather than reported):** three observations, same key,
same signature.

```
obs0 status=recognized
obs1 status=recognized
obs2 status=recognized
vq_grown ShapeSignature nodes: 1  [(#769, 'vq_same_key')]
codebook_epoch: 1.0
```

**No duplicate. The site is self-limiting**: the growth obs0 performs makes obs1
recognisable before it can reach the mint. `AddNodeIfAbsent` here would be a no-op.
**Reported as checked-and-not-at-risk for the repeat case, and NOT fixed.**

**But the probe found something else, and it is a real finding, filed not fixed.** Same
key, **different** signature (the shape a re-used identity tag actually produces):

```
obs0 (signature A) status=recognized
obs1 (signature B) status=recognized_duplicate   <- genuinely novel, recorded as a duplicate
vq_grown entries: 1
```

`sd_dedup_existing`'s guard is `capability_keys == obs.key`, and `obs.key` is a
**caller-supplied tag** (`domains/sdloop_vision.py:80`, `domains/identity_seam_world.py:129`
both write `"key": [tag]`), not a structural key. A second, structurally novel percept
sharing a tag is silently marked `recognized_duplicate` and never grows the codebook —
the audit's "failure direction 2" at a site nobody has looked at. **Not fixed here**: it
changes the sd loop's core novelty gate, `induce_concern` depends on the key convention,
and whether the identity-seam experiment *intends* tag-scoped dedup is unverified. §6.

---

## AR5 — `MetaShapeMint`'s name collision: **NO-GO**, with the design and a new trap

`META_SHAPE_ARITY_AND_KEY_SEPARATOR_FIXES_RESULTS.md` §4.3 measured 23 reachable collision
pairs at `shape_decode.rs:5749`'s `format!("ms_{}", key.join("_"))` and estimated the
structural fix (a `pred_key` attr, guarded on instead of the name) at *"a ~20-line change"*
carrying one hazard. **Three findings, two of them new, make it NO-GO for this rung:**

1. **NEW — the seed cannot read the key today, so this is not a seed-level fix at all.**
   `MetaShapeMint`'s returned Dict exposes `name`, `keys`, `signature`, `support`, `fixed`,
   `leader`, `mintable` (`shape_decode.rs:5749-5762`). The obvious candidate, `keys`, is
   **not** the identity — it is `discriminative`, the predicates filtered to those *not*
   universal across the observed population (`:5744-5747`), computed specifically to narrow
   what the keyword prior can see. **The full sorted predicate set `key` is never
   exposed.** So `pred_key` requires adding a field to the Term in Rust and a rebuild —
   outside this PREREG's registered scope, which admitted Rust only if a fix could not be
   expressed at the seed level and required reporting it as a deviation.
2. **NEW — the obvious resume-safe mitigation is provably wrong.** The natural way to
   protect checkpoint-resumed agents holding pre-`pred_key` `MetaShape` nodes is to guard
   on `pred_key matches OR name matches`. **That reintroduces the exact bug**: a collision
   is by definition two distinct predicate sets producing the *same* name, so the legacy
   name arm still blocks the second, legitimate mint. Any correct fix therefore **must**
   ship a backfill, not a disjunctive guard. Sketch, for whoever picks it up: a
   `msg_backfill_pred_key` rule matching `MetaShape{minted:1}` with no `pred_key`, deriving
   it as `MapList(Attr(ms,"signature"), rel, IndexAt(rel, 0))` — and that derivation needs
   its own gate proving it equals the Term's `key` (the signature is the lgg, so whether it
   preserves every predicate of the group key is an assumption, not a fact).
3. **File scope.** `seeds/meta_shape_growth.json`'s guards are explicitly outside this
   rung's file scope (another thread landed them today).

**NO-GO. The design above is the deliverable, per the PREREG's own condition that a NO-GO
must ship the design rather than the refusal.**

---

## AR6 — regression, paired failing-node-id LISTS

Pristine baseline via `git stash` in the same worktree, same interpreter, same `.so`.

**Registered 12-file suite** (the seeds these fixes touch):

| run | result |
|---|---|
| pristine baseline | `1 failed, 91 passed, 1 skipped` (165.05s) |
| this rung's fix | `1 failed, 91 passed, 1 skipped` (111.95s) |

Failing node-id list, both runs, identical:

```
FAILED tests/test_composer_driver_migrated.py::test_ground_concern_dispatch_parity
```

Pre-existing (a captured-fixture parity drift, unrelated to this diff — identical on the
untouched baseline).

**Broader 62-file sweep** — every `tests/*.py` mentioning `shape_decode_loop`, `DimInfer`,
`GenInfer`, `LatentDimension` or `DimensionGenerator` — run in 4 chunks, paired:

| chunk | baseline | fixed | failing-node-id diff |
|---|---|---|---|
| 1 (16 files) | 13 failed, 282 passed, 10 skipped | 13 failed, 282 passed, 10 skipped | **empty** |
| 2 (16 files) | 9 failed, 145 passed | 9 failed, 145 passed | **empty** |
| 3 (15 files) | 5 failed, 191 passed, 9 skipped | 6 failed, 190 passed, 9 skipped | **+1, investigated below** |
| 4 (15 files) | 1 failed, 153 passed, 4 skipped | 1 failed, 153 passed, 4 skipped | **empty** |

**The one difference — `tests/test_motion_compensated_search_migrated.py::
test_h1_mc_recovers_nonzero_proportional_accel` — is a documented flake, not this diff.**
Three independent lines of evidence: (a) the test's own docstring characterises it —
*"the carve's ±1 CROSS-PROCESS track jitter injects an occasional glitch frame
(characterized: 2/20 fresh processes give d2=[3,3,39]…)"* — i.e. ~10% per fresh process;
(b) it passes in isolation on the **fixed** tree; (c) a full re-run of chunk 3 on the
fixed tree is **byte-identical to the baseline list** (`diff` empty). Reported rather than
re-run-until-green.

---

## 5. Everything that broke, and what didn't

* **Broke nothing that a paired list shows.** 3 of 4 chunks byte-identical; the fourth's
  single difference attributed above with three lines of evidence.
* **The first attempt at AR4.2 broke the fixpoint** (§4.2.2) and was caught by measurement,
  not by tests — no test in the tree presents two novel orbits to one graph. **The gate
  that would have caught it does not exist**; it is named in §6.
* **`codebook_epoch` semantics changed at one site, deliberately:** `sd_mint_generator`
  now bumps it once per *real* mint rather than once per *first* mint ever. Under the old
  guard the rule fired at most once per graph; it can now fire once per novel orbit. Every
  bump re-arms every decoded observation via `sd_redecode`, so a graph discovering many
  generators does more re-decode work than before — **this is the intended cost of the
  growth the cap was preventing**, but it is a cost and it is not measured at scale.
* **Every auto-derived linear-generator NAME changed** (`genlin_base_L` →
  `genlin_[1,0,1,1]`) — intended, §4.2.3. Checked: no test or seed reads the literal.
  `docs/research/vision/VISION_TIME_RESULTS.md:30` records `latent:genlin_base_L` as a
  measured result; per CLAUDE.md's rule a historical record is not converted, so it stands
  as the reading it was.
* **`scripts/genmint_build_seeds.py` was already stale** (it emits v1.7.0 and would delete
  v1.8.0's `AgnosiaParams` guards if re-run). Not caused here; kept in sync for the three
  gen rules and given an explicit stale-builder warning so the next person does not run it
  blind.

## 6. Remaining uncertainties, and the honest inventory

### 6.1 At real risk, NOT fixed here — named precisely enough to pick up

| # | site | why at risk | why not fixed here |
|---|---|---|---|
| I1 | `sd_dedup_existing` / `sd_mint_quantum`'s `capability_keys == obs.key` guard (`seeds/shape_decode_loop.json`) | `obs.key` is a **caller-supplied tag** in both vision adapters; a structurally novel percept under a re-used tag is silently `recognized_duplicate` (§4.3, live) | changes the sd loop's core novelty gate; `induce_concern`'s key convention depends on it; whether identity-seam *intends* tag-scoped dedup is unverified |
| I2 | `MetaShapeMint` name collision (`shape_decode.rs:5749` + `seeds/meta_shape_growth.json::msg_mint_shape`) | 23 measured reachable collision pairs; blocks a legitimate mint | AR5 — needs a Rust field, a backfill rule, and a file this rung may not touch |
| I3 | `load_parts` `by_name.insert` last-write-wins (`shape_decode.rs:239-326`) | two codebook entries with the same name ⇒ **the first is silently dropped**, whatever their signatures; `SHAPE_AUDIT.md` §3.1b's twin, from the other side | a structural (signature-keyed) codebook identity is the spike §5.2 `ShapeRole` design, not a one-token edit. `AddNodeIfAbsent` cannot reach it — `load_parts` is a reader |
| I4 | `load_generators` `by_name.insert` last-write-wins (`shape_decode.rs:457`) | same mechanism as I3, **newly found here** (§4.2.3), currently masked by the fact that only matrix-derived names are minted | same reason as I3; this rung avoided it rather than fixed it |
| I5 | `time_axis.json::time_infer_mint` / `depth_axis.json::depth_infer_mint` `LatentDimension` mints | same scope error as AR4.1, no per-observation guard at all | **`tests/test_galileo_migrated.py:126-128` asserts exactly three non-deduped `latent:time` nodes**, with a rationale (*"the raw loop has no cross-object recognition; that is exactly what seeds/galileo.json supplies"*). Deduping would break a documented arc. Needs that arc's owner |
| I6 | the 179 bare sites whose type has a `domains/`/`substrate/` identity reader, minus the 4 triaged above | AR3's signature | not probed. Each needs a live reproduction; 175 sites is its own rung |
| I7 | the missing gate: no test presents **two novel orbits to one graph** | the §4.2.2 loop and the §4.2.1 stall both survived every existing gate because every gate boots fresh per orbit | writing it is cheap and it belongs with I4 |

### 6.2 Out of this rung's file scope, named not fixed

Nothing at genuine dedup risk was found in the excluded files
(`domains/analogical_thinking.py`, `domains/reflective_faculty.py`'s `CapabilityAxis`/
rule-selection regions, `domains/rule_signature.py`, `runners/dsl/src/py.rs`,
`substrate/world_adapter.py`'s checkpoint-load region,
`seeds/meta_shape_growth.json`'s guards) beyond I2, which is named above. This is a
"looked and found nothing new," not a "did not look" — the AST scan covered all of them.

### 6.3 Checked and not at risk

* The **799 bare sites (79%)** whose minted type has no identity reader anywhere
  (§2.3) — with the stated caveat that "no identity reader" is weaker than "correctly
  observation-scoped."
* All **seven** both-way types (§2.4) — two correct scopes each, not drift.
* `vq_grow_quantum` / `is_mint` for the **repeat** case (§4.3) — self-limiting, measured.
* The `Transform` mint in `sd_recognize_dim` — correctly bare, deliberately left so.

### 6.4 Claims this document does NOT make

1. **No production-prevalence claim.** Both fixes are mechanism proofs on a booted agent.
   How often the `LatentDimension` duplicate or the generator stall fires on the live
   daemon is **unmeasured** (CLAUDE.md: *"synthetic-proven mechanism ≠ benchmark value,
   report both"*).
2. **No claim that the 1,079 are now triaged.** 179 have the risk *shape*; 4 were probed.
3. **No retroactive cleanup.** A graph that already holds duplicate `LatentDimension` nodes
   still holds them; this is a mint-path fix, the same boundary
   `SHAPE_AUDIT_PATTERN_C_FIXES_RESULTS.md` §6 drew.
4. **The `codebook_epoch` cost of allowing multiple generators is not measured at scale**
   (§5).
5. **The AST scan is a heuristic.** It finds `for … in .nodes("T")` + attr-compare +
   early-exit; it misses comprehension-based lookups and dict-index caches. 499 is a floor.

---

## 7. What a reviewer should look at first

1. **§4.2.2**, the non-terminating loop — the reason "adopt the primitive more widely" is
   not a safe instruction, and the strongest argument in this document.
2. **§4.2.3**, `load_generators`' name shadowing — a new instance of the month's recurring
   defect (a name-keyed index with last-write-wins), found by removing a guard that was
   hiding it.
3. **§2.4**, the seven both-way types — seven for seven correct, which is the evidence that
   the scope discriminator is real rather than invented.
4. **§6.1 I5**, the `test_galileo_migrated` assertion that three identical
   `LatentDimension` nodes must exist — a place where the duplicate is currently
   load-bearing for another arc, and therefore not this rung's to remove.

---

## 8. Reproduce

```bash
cd /home/matt/ocelot-dedup-adoption-sweep
git log --oneline -1                     # dedup-adoption-sweep, on top of abadbab
sha256sum runners/dsl/python/substrate_rs/_native.abi3.so   # 8963fb4dcc…
PYTHONPATH=runners/dsl/python:. python3 -c "
import substrate_rs as srs; s=srs.Substrate()
a=s.node(s.add_node('T',{'lst':[1,2,3],'tup':(1,2,3)}))['attrs']
print(a['lst'], a['tup'], a['lst']!=a['tup'])"          # coherence probe

# AR1 — the primitive, from source
sed -n '1693,1740p' runners/dsl/src/rewrite.rs
sed -n '261,277p'   runners/dsl/src/graph_rules.rs
sed -n '457,470p'   runners/dsl/src/shape_decode.rs     # load_generators by_name
sed -n '239,326p'   runners/dsl/src/shape_decode.rs     # load_parts by_name
sed -n '5744,5762p' runners/dsl/src/shape_decode.rs     # MetaShapeMint: `keys` != `key`

# AR2 — the 1,079 census
python3 - <<'PY'
import json, glob, collections
ops=collections.Counter(); per_type=collections.defaultdict(collections.Counter)
for f in sorted(glob.glob('seeds/*.json')):
    try: d=json.load(open(f))
    except Exception: continue
    if not isinstance(d, dict): continue
    for r in (d.get('rules') or []):
        for e in (r.get('effect') or r.get('effects') or []):
            if isinstance(e,list) and e and str(e[0]).startswith('add_node'):
                ops[e[0]]+=1
                per_type[e[2] if len(e)>2 and isinstance(e[2],str) else None][e[0]]+=1
bare={t for t,c in per_type.items() if c.get('add_node')}
ifab={t for t,c in per_type.items() if c.get('add_node_if_absent')}
print(dict(ops), 'TOTAL', sum(ops.values()))
print('types', len(per_type), 'bare-only', len(bare-ifab), 'ifabsent', len(ifab),
      'both', sorted(bare&ifab))
PY

# AR3 — the first-match-wins reader scan (499 loops / 126 types)
python3 - <<'PY'
import ast, glob, collections
hits=[]
for path in glob.glob('**/*.py', recursive=True):
    if path.startswith('build/'): continue
    try: src=open(path, encoding='utf-8', errors='replace').read()
    except Exception: continue
    if '.nodes(' not in src: continue
    try: tree=ast.parse(src)
    except Exception: continue
    for fn in ast.walk(tree):
        if not isinstance(fn,(ast.FunctionDef, ast.AsyncFunctionDef)): continue
        for node in ast.walk(fn):
            if not isinstance(node, ast.For): continue
            t=None
            for sub in ast.walk(node.iter):
                if (isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute)
                        and sub.func.attr=='nodes' and sub.args
                        and isinstance(sub.args[0], ast.Constant)):
                    t=sub.args[0].value
            if not t: continue
            d=ast.dump(node)
            if any(isinstance(s,(ast.Return, ast.Break)) for s in ast.walk(node)) \
               and 'Compare' in d and ("'get'" in d or 'attrs' in d):
                hits.append((path, t))
by=collections.Counter(t for _,t in hits)
print('loops', len(hits), 'types', len(by)); print(by.most_common(12))
PY

# AR4.1 — LatentDimension, before/after  (BEFORE: git stash first)
PYTHONPATH=runners/dsl/python:. python3 - <<'PY'
import json
from substrate.boot_core import boot_core
from domains import reflective_faculty as rf
TROMINO=[["cell",0,0,"red"],["cell",0,1,"red"],["cell",1,0,"red"]]
ROT1   =[["cell",0,0,"red"],["cell",0,1,"red"],["cell",1,1,"red"]]
DT=["pred","coord:r","coord:c","val"]
s,ag=boot_core(); native=rf._native_eval2(s); rf._ensure_shape_decode_loop(s,native,ag)
s.add_node("ShapeSignature",{"name":"part_tromino","signature":json.dumps(TROMINO),
                             "kind":"faculty","faculty":"part_tromino","dim_types":DT})
ep=s.node(ag)["attrs"].get("codebook_epoch") or 0.0
for i in range(3):
    o=s.add_node("Observation",{"signature":ROT1,"key":["probe_rot_%d"%i],"status":"decoded",
                                "residual":ROT1,"decoded_epoch":ep,"dim_types":DT})
    s.add_edge(ag,"observed",o); native.run_rules()
    print(i, s.node(o)["attrs"].get("status"))
print("LatentDimension nodes:", len(list(s.nodes("LatentDimension"))))   # BEFORE 3 / AFTER 1
PY

# AR4.2 — the generator orbits, before/after
PYTHONPATH=runners/dsl/python:. python3 - <<'PY'
import json
from substrate.boot_core import boot_core
from domains import reflective_faculty as rf
DT=["pred","coord:r","coord:c","val"]
BASE=[["cell",0,0,"red"],["cell",1,0,"red"],["cell",2,0,"red"],["cell",2,1,"red"]]
def lin(M):
    rs=[c[1] for c in BASE]; cs=[c[2] for c in BASE]; mr,mc=min(rs),min(cs)
    return [["cell",M[0]*(r-mr)+M[1]*(c-mc),M[2]*(r-mr)+M[3]*(c-mc),v] for _,r,c,v in BASE]
s,ag=boot_core(); native=rf._native_eval2(s); rf._ensure_shape_decode_loop(s,native,ag)
s.set_attr(ag,"gen_infer_enabled",1.0)
s.add_node("ShapeSignature",{"name":"base_L","signature":json.dumps(BASE),
                             "kind":"faculty","faculty":"base_L","dim_types":DT})
for i,M in enumerate(([1,0,1,1],[1,1,0,1],[2,1,1,1],[1,0,1,1])):
    ep=s.node(ag)["attrs"].get("codebook_epoch") or 0.0
    o=s.add_node("Observation",{"signature":lin(M),"key":["p%d"%i],"status":"decoded",
                                "residual":lin(M),"decoded_epoch":ep,"dim_types":DT})
    s.add_edge(ag,"observed",o); native.run_rules()
    lg=[tuple(s.node(n)["attrs"].get("matrix")) for n in s.nodes("DimensionGenerator")
        if s.node(n)["attrs"].get("kind")=="linear"]
    print(M, s.node(o)["attrs"].get("status"), lg)
# BEFORE: orbits 2,3 -> "decoded", 1 generator.  AFTER: all four resolve, 2 generators.
PY

# AR4.3 — the vq null (NOTE: vision_sdloop must be installed explicitly)
PYTHONPATH=runners/dsl/python:. python3 - <<'PY'
from substrate.boot_core import boot_core
from substrate.seed_loader import manifest_for
from domains import reflective_faculty as rf
from domains import sdloop_vision as sv
s,ag=boot_core(); native=rf._native_eval2(s); rf._ensure_shape_decode_loop(s,native,ag)
native.load_seed_manifest(manifest_for("vision_sdloop"), ag)
SIG=[["on",0,0],["on",0,1],["on",1,0],["off",2,2]]
for i in range(3):
    o=sv.ingest(s,ag,SIG,"vq_same_key"); native.run_rules()
    print(i, s.node(o)["attrs"].get("status"))
print("grown:", [s.node(n)["attrs"].get("name") for n in s.nodes("ShapeSignature")
                 if s.node(n)["attrs"].get("vq_grown")])          # exactly one
PY

# AR6 — paired regression (baseline via `git stash` in this worktree)
PYTHONPATH=runners/dsl/python:. python3 -m pytest -q -p no:randomly \
  tests/test_dimension_inference_migrated.py tests/test_gen_infer_migrated.py \
  tests/test_transform_decode_migrated.py tests/test_continuous_pose_migrated.py \
  tests/test_stereo_infer_migrated.py tests/test_galileo_migrated.py \
  tests/test_robust_witness_migrated.py tests/test_axis_mint_novelty.py \
  tests/test_composer_driver_migrated.py tests/test_meta_shape_arity_migrated.py \
  tests/test_sdloop_vision_migrated.py tests/test_identity_seam_migrated.py
# broad sweep file list:
grep -rl "shape_decode_loop\|DimInfer\|GenInfer\|LatentDimension\|DimensionGenerator" tests/*.py
```

**Environment note, stated because it changes what a reader sees:** this worktree has
`data/` symlinked to the primary tree's, and `_native.abi3.so` was `touch`ed after
checkout (the checkout gave 85 `.rs` files an mtime 3µs newer than the binary, which
`domains/engine_provenance.py` correctly refuses; the `.so` is `sha256`-identical to the
primary tree's, verified before touching). Both conditions apply to the baseline and the
fixed run equally, so the paired lists are unaffected — but an absolute red count from
this worktree is not comparable to one taken without them.
