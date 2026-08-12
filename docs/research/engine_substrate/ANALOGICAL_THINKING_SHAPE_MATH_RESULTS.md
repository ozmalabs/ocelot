# ANALOGICAL THINKING — GENUINE SHAPE MATH — RESULTS

**Prereg:** `ANALOGICAL_THINKING_SHAPE_MATH_PREREG.md`, registered before any
code was written (commit `c6c2505`). **Charter:** `SHAPE_AUDIT.md` §2.4 — the
June 2026 MAC/FAC diagnosis at its original site, re-confirmed live by
`META_SHAPE_FIRST_CLASS_RESULTS.md` §9.1 and left untouched there.

## Provenance

| | |
|---|---|
| base commit | `d239b7c` (`Merge shape-audit-pattern-c-fixes: three live corruption bugs closed`) |
| worktree | `/home/matt/ocelot-analogical-thinking-shape-math`, branch `analogical-thinking-shape-math` |
| baseline worktree | `/home/matt/ocelot-atsm-baseline`, detached at `d239b7c` |
| **engine** | **UNCHANGED, never rebuilt.** `_native.abi3.so` sha256 **`62e5cdc39a84fee548b9d373c9bbcd01f33c69f8ddab3dc518e78b0ef45ca56f`** — byte-identical in both worktrees, verified by `sha256sum`. `git diff d239b7c -- runners/` is **empty**. **Zero Rust was written**, as registered in prereg §3.5. |
| files changed | `domains/analogical_thinking.py` (+516/−75), one new probe, one new gate file, two docs |

---

## The one thing worth reading if you read nothing else

**On the largest real bridge in the agent's own graph — 142 computer-architecture
concepts × 137 mathematics concepts — the faculty reported 8,575 analogies. 8,253
of them were a keyword matching inside a longer word.**

The single worst offender is `io` (the `input_output` role) matching
`operat`**`io`**`n`, `satisfact`**`io`**`n`, `relat`**`io`**`n`: **39.6% of every
vocabulary hit in the booted graph**. This is not a newly-discovered bug — it is
documented *inside this tree*, by a caller that had to hand-patch around it
(`scripts/jabberwock_reads_looos.py`: *"the substring 'io' spuriously matches
every '-tion' word"*). The faculty's own consumers knew. Nothing upstream did.

Anchoring the match at a token start is a one-argument change to an existing
Term. Requiring an abstract-order claim to be *structurally supported* is the
MAC/FAC escalation the June diagnosis prescribed. Together they take that bridge
from 8,575 claims to **321**, and the 321 are ranked by evidence the old key
could not see at all: the top result is `branch_predictor → expectation_variance`
at order 4 with **all three shared axes evidenced in the concepts' own name
slots**.

**And the second thing:** the brief's own suggested mechanism —
`AntiUnifyWitness` per pair, transplanted from
`RULE_REFERENCE_LAYER_SIZING_RESULTS.md` §4 — **does not transfer, and that was
registered as a NO-GO before building** (§3). It earns its place only where §4
actually used it: **across** pairs. 78 pairs on that bridge are corroborated by
another pair realising the same held witness — the parallelogram, at the concept
grain, on real data.

---

## 1. Verdicts

| bar | verdict | evidence |
|---|---|---|
| **AR1** — investigation | **GO** | five orders read from the code (§2); nine callers enumerated (prereg §1.1); population compatibility **verified and partly NEGATIVE** — 114/10,775 concepts have any edge, and the per-pair `AntiUnifyWitness` transplant is a reasoned NO-GO (§3) |
| **AR2** — design registered first | **GO** | prereg §3, built as written. Two deviations, both reported in §7 |
| **AR3** — live demonstration | **GO** | curated bridge 22 → 9 pairs, the `io` case withdrawn by name (§4.1); exhaustive sweep 17,241 → 9,911 readings, **0 added** (§4.2); real 142×137 bridge 8,575 → 321 with 78 corroborated (§4.3) |
| **AR4** — no regression | **GO** | 7 test files, both trees, **identical failing node-id LISTS** — 10 pre-existing reds, zero new (§6). 12 new gates ship green. Consumers `shape_hits` byte-identical; `metashape_realisation_counts` rank order identical 11/11 |

---

## 2. AR1 — what `_compute_analogy` actually does, verified

All five orders are a **set overlap of strings**, and the two lower ones and the
three upper ones fail differently:

| order | compared | mechanism | verified defect |
|---|---|---|---|
| 0 | concept names | `_tokens` intersection | none — honest surface similarity |
| 1 | `category` + definitions | equality, then token intersection with a hard floor `>= 3` | the `>= 3` floor is an unregistered scalar knob; **not touched**, reported in §8 |
| 2 | `FunctionalRole` | `StringIndexOf(name + " " + definition, kw) >= 0` | unanchored substring; slots concatenated away |
| 3 | `ShapePrinciple` | same | same |
| 4 | `MetaShape` | order-3 hits, then **any one** shared `has_principle` neighbour | 1-of-N disjunction, then outranks every lower order outright |

The verdict is `(top_order, feature_count)`. Two consequences are part of the
same defect and both are fixed here:

* `emit_analogy_as_graph` wrote a real `implements` **edge** on `order_n >= 2`
  with the comment *"n >= 2 indicates genuine structural correspondence"* — an
  ordinal asserting a structure never computed. Measured: that ordinal was
  reachable by `io` inside `operation`.
* **There was no path by which this faculty could say "no clear analogy here."**
  One shared vocabulary hit was an analogy, with a rationale asserting a shared
  functional role.

**Found in passing, pre-existing, not repaired** (out of charter, prereg §6):
`scripts/jabberwock_reads_looos.py:145` and
`scripts/jabberwock_designs_runner_brain.py:136` both still read `a["score"]`, a
key deleted when ranking was made relative. Both raise `KeyError`. This matters
for §5: **the script that produced the frozen seven-subsystem decomposition
cannot be re-run in either tree.**

---

## 3. AR1's negative half — what the population can and cannot support

This is the part of the rung that changed the design, and it was measured before
the design was registered.

### 3.1 The concept population has no relational structure

| measured on a full `load_all_seeds` boot | |
|---|---|
| `Concept` nodes | **10,775** |
| …with ≥1 outgoing edge of any type | **114 (1.06%)** |
| `Concept -*-> Concept` edges, whole graph | **190** |
| incoming | 6,312 × `has_concept` + 179 everything else |

`SHAPE_AUDIT.md` §2.4's charge — *"never consults a concept's edges"* — is a
**correct diagnosis of the code and a dead end as a prescription.** 98.9% of the
population has no edge to consult. Building relational alignment here would be a
no-op wearing the costume of a fix. **Saying so is the result.**

### 3.2 The per-pair `AntiUnifyWitness` transplant is a NO-GO — registered, with its reason

The brief proposed `RULE_REFERENCE_LAYER_SIZING_RESULTS.md` §4's operation
(extract **T** from two known corners with `AntiUnifyWitness`, apply it with
`Substitute`) as *"very likely the CORRECT operation"*. Verified against the real
data shape, it is not — **for a single pair**:

* `AntiUnifyWitness` generalises element-wise over **equal-length** tuples, so
  two concept signatures must first be aligned by predicate;
* aligning by predicate makes the predicate correspondence the **identity map**;
* the template's fixed leaves are then exactly *"the attributes that are equal"*
  — which is `category == category`, i.e. **order 1, already there**;
* the values are opaque prose, so no reusable transform exists *inside* one pair
  to hand to `Substitute`.

**Where it does earn its place is exactly where §4 used it: ACROSS pairs.** §4's
parallelogram is two corner-pairs sharing one transform. At this grain, a
candidate pair `(A,B)` induces a witness σ; a different pair `(C,D)` in the same
bridge induces its own; **when the witnesses are equal, the two pairs are the two
corner-pairs of one parallelogram and each corroborates the other.** That is
Gentner's systematicity computed rather than asserted, and it needs no concept
edges. It fires on real data (§4.3).

**This distinction — the operator is right, the arity was wrong — is the finding
this rung would flag second.**

---

## 4. AR3 — live, before and after, same graph, same process

`scripts/analogical_shape_math_probe.py` reimplements the `d239b7c` scorer in
Python as a read-only mirror, so both verdicts are computed **side by side
against the same graph**. Full output: `results/analogical_shape_math_probe.txt`.

### 4.1 Curated — the real `looos_claims` × `held_writing_primitives` bridge

Concepts taken **verbatim** from `scripts/jabberwock_reads_looos.py` (5 paper
claims × 6 held primitives = 30 candidate pairs). At every one of n=2, 3, 4:

| | BEFORE | AFTER |
|---|---|---|
| pairs reported | **22** | **9** |
| withdrawn | — | **13** |
| demoted to a lower order | — | 2–3 (n-dependent) |
| newly invented | — | **0** |

Every grounding the reading script actually wants **survives at its correct
order**:

| pair | AFTER |
|---|---|
| `nearest_neighbour_classifier → nearest_neighbour_one_shot` | order 4 |
| `nearest_neighbour_classifier → order_invariant_shape_distance` | order 4 |
| `innate_prior_modelling → nuisance_folding_invariance` | order 4 |
| `distortion_at_first_sight → deformation_match` | order 2 |

And the withdrawn set is the spurious set — `innate_prior_modelling →
canonical_parse`, `nearest_neighbour_classifier → deformation_match`,
`distortion_at_first_sight → nuisance_folding_invariance`, …

**The named case, by name.** `white_box_model → learned_nuisance_whitening`,
BEFORE: `{order_n: 2, rationale: "shared functional role: input_output"}`.
Nothing about a white-box model is an input/output role; `io` sits inside
`distortion` and `segmentation`. AFTER: **withdrawn.** This is the exact pair the
tree's own reader script had to hand-patch out with a
`if v.strip() != "input_output"` filter.

### 4.2 Exhaustive — every `Concept` in a full seed boot

| | |
|---|---|
| concepts | **10,775** |
| vocabulary readings BEFORE | **17,241** |
| vocabulary readings AFTER | **9,911** |
| **withdrawn** | **7,330 — 42.5%** |
| **added** | **0 — the change is strictly a withdrawal** |
| concepts whose reading changed at all | **5,924 — 55.0%** |

`added = 0` is the important cell: anchoring is a **strict refinement** of the
substring test, so it can only ever remove. Measured across the whole
population, not argued.

| withdrawn reading | count | why |
|---|---|---|
| role `input_output` | **5,649** | `io` in `operat`**`io`**`n` |
| principle `spatial_motion` / shape `spatial_dynamics` | 386 each | `posit` in `com`**`posit`**`ion` |
| role `synchronize` | 165 | `sync` in `a`**`sync`**`hronous`, `lock` in `c`**`lock`**`wise` |
| role `integrate` | 88 | `synthesi` in `photo`**`synthesi`**`s` |
| role `learn` | 86 | `train` in `cons`**`train`**`t` |
| role `gating` | 65 | `gate` in `ag`**`gregate`**`s` |
| principle `hierarchical_abstraction` + both shapes it feeds | 65 each | `layer` in `p`**`layer`** (`nash_equilibrium`, `zero_sum_game`) |

### 4.3 The broadest real bridge, and the parallelogram firing

`computer_architecture` (142 concepts) × `mathematics` (137) — 19,454 candidate
pairs, the two largest concept-bearing microtheories the agent holds.

| | n=2 | n=4 |
|---|---|---|
| BEFORE | **8,575** | **8,664** |
| AFTER | **321** | **375** |
| withdrawn | 8,253 | 8,278 |
| demoted | 13 | 18 |
| **corroborated (≥1 other pair realising the same held witness)** | **78** | **78** |

Corroboration distribution at n=4: 297 pairs at 0, **62 at 1, 12 at 2, 4 at 3**.
**Registered risk 2 does not bite at real scale** — it bit on the 30-pair
curated bridge, where corroboration was 0 everywhere, exactly as the prereg said
it might.

The corr=3 group is the one to look at, because it is a textbook parallelogram:

```
register_file -> markov_chain    |  l2_cache -> markov_chain
l1_cache      -> markov_chain    |  l3_cache -> markov_chain
      ... four memory-hierarchy levels, ONE held witness ...
```

Four source concepts differing from the same target in *exactly the same places
by exactly the same amounts*. No per-pair scorer of any sharpness can produce
that number; it is a property of the bridge, not of a pair.

Top of the new ranking, and why it is top:

```
n=4  corr=0  name_shared=3  struct=3   branch_predictor -> expectation_variance
n=4  corr=0  name_shared=3  struct=3   forwarding       -> expectation_variance
```

Three shared axes (`predict` / `prediction` / `prediction_minus_observation`),
**all three evidenced in the concepts' own NAME slots**, not in prose. That is
`META_SHAPE_FIRST_CLASS_RESULTS.md` §2's `pred_principles` tier landing one
grain over: *an item whose slot IS the shape beats an item that merely talks
about it.* The old key had no term for it.

---

## 5. AR3's uncomfortable half — the frozen decomposition moves

Registered risk 3 asked whether withdrawing spurious analogies changes the
seven-meta-shape decomposition frozen in
`seeds/seven_meta_shape_subsystems.json`. **Measured. It does, in the tail.**

Reproducing `jabberwock_designs_runner_brain.py`'s aggregation (6 source Mts ×
8 target Mts, n=4, `min_score=5`), with `features_total` standing in for the
deleted `score` key:

| rank | BEFORE | AFTER |
|---|---|---|
| 1 | prediction_minus_observation (1349) | prediction_minus_observation (705) |
| 2 | spatial_dynamics (1150) | spatial_dynamics (422) |
| 3= | hierarchical_invariance_buildup (675) | hierarchical_invariance_buildup (206) |
| 3= | relational_structure_match (675) | relational_structure_match (206) |
| 5 | competitive_inhibition (310) | **associative_recall (177)** |
| 6 | associative_recall (302) | **competitive_inhibition (129)** |
| 7 | selective_gating (163) | **delayed_persistence (17)** |
| 8 | feedback_control (67) | **selective_gating (11)** |
| 9 | delayed_persistence (51) | feedback_control (10) |
| 10 | global_message_passing (5) | **absent** |

Top four stable; three swaps in the tail; `global_message_passing`, which BEFORE
rested on **exactly one** analogy worth 5, is gone entirely.

**Three honest statements about this, none of which is "so the seed is wrong":**

1. **The seed was not edited by this rung**, per prereg §6.
2. **Neither tree reproduces the seed's own numbers** (3078 / 1194 / 843 / 556 /
   452 / 449 / 81) or its own ordering. It was produced under a third code
   state, before the relative-ranking rung deleted `score`.
3. **The producing script cannot run in either tree** — it reads `a["score"]`
   (§2). So the decomposition is currently un-reproducible independently of
   anything this rung did. That is a pre-existing gap this rung found, not one
   it created, and it is the honest reason the seed is left alone: a rung that
   cannot re-derive a frozen artefact should not edit it.

---

## 6. AR4 — regression, as LISTS

Per CLAUDE.md's retracted-baseline rule (*"a baseline must be a list of node ids,
never a count or a characterisation"*). Both trees, same day, same engine binary.

### 6.1 Direct consumers

| file | BEFORE (`d239b7c`) | AFTER |
|---|---|---|
| `tests/test_analogical_relative_ranking.py` | 6 passed | 6 passed |
| `tests/test_frame_manifold.py` | 13 passed | 13 passed |
| `tests/test_reframing_proposer.py` | 9 passed | 9 passed |
| `tests/test_reading_introspection_migrated.py` | 8 passed | 8 passed |

**Registered risk 1 did not bite.** `test_reframing_proposer.py:188`, the named
at-risk gate (it asserts specific meta-shapes are read off specific prose), is
green in both trees.

### 6.2 Indirect consumers (`metashape_realisation_counts` / `shape_hits` readers)

| file | BEFORE | AFTER |
|---|---|---|
| `tests/test_self_model.py` | 2 failed / 10 passed | 2 failed / 10 passed |
| `tests/test_self_prose_rendering.py` | 4 failed / 5 passed | 4 failed / 5 passed |
| `tests/test_self_process_introspection.py` | 1 failed / 13 passed | 1 failed / 13 passed |
| `tests/test_smooth_content.py` | 3 failed / 5 passed | 3 failed / 5 passed |

**The failing node ids, enumerated — identical sets, both trees, no
substitutions:**

* `test_self_model.py` — `test_ask_which_rules_about_topic`,
  `test_ask_which_parts_touch_attr`
* `test_self_prose_rendering.py` — `test_battery_never_dumps_raw_dict`,
  `test_self_model_touches_reply_is_fluent_and_preserves_facts`,
  `test_self_model_topic_reply_is_fluent_and_preserves_facts`,
  `test_rule_description_uses_the_production_faculty`
* `test_self_process_introspection.py` — `test_honest_floor_preserved_for_genuine_gap`
* `test_smooth_content.py` — `test_describe_scene_is_connected_prose_not_fragments`,
  `test_register_shapes_the_content_voice_formal_vs_casual`,
  `test_smoothing_preserves_rule_facts`

**AR4 verdict: GO — zero node ids red in AFTER that are green in BEFORE.** All
10 reds are pre-existing at `d239b7c`, node id for node id.

### 6.3 Consumer values, before and after

| consumer | BEFORE | AFTER |
|---|---|---|
| `shape_hits("gate the layer by policy")` | `{hierarchical_invariance_buildup, relational_structure_match, selective_gating}` | **identical** |
| `shape_hits("you should predict things and observe them")` | `{prediction_minus_observation}` | **identical** |
| `shape_hits("a global hormone broadcast")` | `{global_message_passing}` | **identical** |
| `shape_hits("replay during sleep to consolidate")` | `{delayed_persistence}` | **identical** |
| `shape_hits("an operation on a satisfaction fold")` | *(not previously probed)* | `{}` — the `io` reading is gone |
| `metashape_realisation_counts` **rank order** | 11 shapes | **identical, 11/11** |
| `metashape_realisation_counts` **magnitudes** | spatial_dynamics 1143, selective_gating 185, … | 757, 124, … — **shrink, by design** |

The magnitudes shrink because ~42% of the readings feeding them were substring
accidents. The **rank order is unchanged**, which is what
`reflective_faculty._run_self_shape` actually reports.

### 6.4 New gates

`tests/test_analogical_shape_math_migrated.py` — **12 passed**: anchoring
(3 gates, incl. the strict-refinement property and `_` as a boundary), the
honest non-answer (2), the name-slot tier and recorded structure (2),
corroboration and its rank position (2), the `implements` edge both ways (1),
the public contract (1), and a source audit that the meet / fixed-leaf count /
cover are all Rust Terms (1).

---

## 7. Deviations from the PREREG

| registered | built | why |
|---|---|---|
| `_vocab_hits` becomes "slot-addressed **and** token-anchored" | the **public** `_vocab_hits(substrate, voc_type, text)` keeps its flat-set signature; slot-addressing lives in a new `_vocab_hits_by_slot` that `_concept_reading` uses | `shape_hits` and `metashape_realisation_counts` take arbitrary text, not a concept. Splitting kept their contract byte-stable (§6.3) at no cost to the analogy path |
| the honest non-answer is a pair returning `None` | a pair **falls back to the surface orders it genuinely has**, and returns `None` only when nothing survives | strictly better: an unsupported *order-2 claim* is withheld without deleting a real order-0 name match. The rationale says so (`WITHHELD at order(s) 2: …`) |

Nothing registered was weakened. The registered NO-GO (§3.2) was reported as
registered, not quietly dropped.

---

## 8. Everything that broke on the way

1. **The first boundary test treated `_` as a word character** — and it was
   wrong in the direction that *manufactures* a result: it "killed"
   `typographic_hierarchy → hierarch`, `pre_echo_control → control`,
   `uv_mapping → map`, all of which are genuine hits at a snake_case boundary.
   Caught by reading the examples rather than the total, corrected, and the
   headline moved 49.9% → 47.1% (and 42.5% on the final per-axis count). **A
   spurious-hit rate is only as good as its boundary definition**, and the wrong
   one flattered the result.
2. **`Covers` requires the wild marker WRAPPED** — `["y", "·?·"]` returns
   `False`, `["y", ["·?·"]]` returns `True`. Verified live against the engine
   before wiring anything, because a silent `False` here would have made the
   order-4 structural path look "dormant" for the wrong reason.
3. **`_covered_shapes` was written and never called.** Caught by measuring
   dormancy rather than assuming it: the function existed, the order-4 branch
   did not call it, and the "0 of 11 signatures" figure would have been true and
   meaningless. Wired, re-measured, re-gated.
4. **`AntiUnifyWitness` returns TUPLES, and mixed ones** — a fully-fixed relation
   comes back as a `list`, a wild-bearing one as a nested `tuple`. Exactly
   CLAUDE.md's own warning (*"`native.evaluate()` returns TUPLES not lists — an
   `isinstance(list)` filter silently disabled child-minting"*). `_is_wild` is a
   form test over both shapes for this reason.
5. **`emit_analogy_as_graph` writes through the CHECKED `add_edge`**, so a test
   substrate with no Γ production for `implements` silently swallows the edge in
   a bare `except: pass`. The first `implements` gate failed for that reason,
   not for the reason under test.
6. **The seed manifest's `local_id` is not the node array index.** The probe's
   vocabulary loader raised `KeyError: 41` until it read `local_id` off the node.

---

## 9. Remaining uncertainties, honestly

* **The vocabulary CONTENT is still wrong in places, and anchoring cannot fix
  it.** `spatial_motion` carries the keywords `fixed` and `station`, so
  `reservation_station → fixed_point_stability` still comes back as a shared
  `spatial_dynamics` meta-shape at order 4 — both keywords match at genuine
  token starts. This is a `seeds/shape_vocabulary.json` content defect, explicitly
  out of scope (prereg §6), and it is the largest surviving false-positive class.
* **Order 4's structural `Covers` path is DORMANT**, exactly as registered: 0 of
  11 seeded `MetaShape`s carry a `signature` (`META_SHAPE_FIRST_CLASS_RESULTS.md`
  §3a). It is wired and it costs nothing; it lights up for free the first time
  `seeds/meta_shape_growth.json` mints a shape into a graph this faculty reads.
  **No claim is made that it does anything today.**
* **Order 4's 1-of-N `has_principle` disjunction is UNCHANGED.** Seven of the
  eleven shapes have one principle, so for those, order 4 is a rename of order 3;
  for the other four, half the evidence claims the whole shape — and order 4 then
  outranks everything below it. Documented in prereg §2.3, not registered as a
  change, not made.
* **Order 1's `len(common) >= 3` floor is an unregistered scalar knob** and is
  untouched. It is exactly the Pattern-E defect CLAUDE.md's SHAPES-NOT-NUMBERS
  section describes, sitting inside the faculty this rung just repaired.
* **`order_n` remains PRIMARY over corroboration.** That is a deliberate
  non-decision: it is the previous rung's registered, gated result
  (`test_analogical_relative_ranking.py`) and relitigating it was out of charter.
  Whether structural corroboration is *better* evidence than axis position is a
  real open question this rung did not test.
* **Alignment is strict.** Two concepts sharing a role but evidenced for it in
  different slots (one in its name, one in prose) are not aligned on that axis.
  Defensible under the typed-slot principle and gated as intended behaviour, but
  no experiment here shows strict beats lenient on real data.
* **The 321 survivors on the big bridge were not hand-verified.** The withdrawn
  8,253 are demonstrably withdrawn *for a stated mechanical reason*; nobody has
  read the 321 and confirmed each is a good analogy. "8,253 spurious claims
  removed" is claimed; "321 correct analogies" is **not**.
* **No benchmark moved and none is claimed** (*"synthetic-proven mechanism ≠
  benchmark value, report both"*).

---

## 10. Reproduce

```bash
git worktree add --detach /tmp/atsm-baseline d239b7c
git worktree add --detach /tmp/atsm          analogical-thinking-shape-math
# the engine is UNCHANGED — do not rebuild; verify instead:
sha256sum /tmp/atsm{,-baseline}/runners/dsl/python/substrate_rs/_native.abi3.so

# AR3 — curated + consumers + exhaustive (the last section boots all 690 seeds)
cd /tmp/atsm && PYTHONPATH=.:runners/dsl/python \
  python3 scripts/analogical_shape_math_probe.py

# the new gates
cd /tmp/atsm && PYTHONPATH=.:runners/dsl/python \
  python3 -m pytest tests/test_analogical_shape_math_migrated.py -q

# AR4 — paired, in BOTH trees, with -rf to get node ids not counts
for T in /tmp/atsm-baseline /tmp/atsm; do (cd $T && PYTHONPATH=.:runners/dsl/python \
  python3 -m pytest tests/test_analogical_relative_ranking.py tests/test_frame_manifold.py \
    tests/test_reframing_proposer.py tests/test_self_model.py \
    tests/test_self_prose_rendering.py tests/test_self_process_introspection.py \
    tests/test_smooth_content.py -q -p no:randomly -rf); done
```

## 11. Files

| file | |
|---|---|
| `domains/analogical_thinking.py` | the whole change: `_token_starts` / `_kw_hit_term` (anchoring), `_vocab_hits_by_slot` / `_concept_reading` (slot-addressing), `_concept_shape_vector` / `_pair_witness` / `_canon_transform` / `_covered_shapes` (the held FAC stage), `_finalise_analogy` (MAC→FAC promotion + the honest `None`), `RANK_KEY`, and the `implements` gate |
| `scripts/analogical_shape_math_probe.py` | the AR3 harness — BEFORE mirror + AFTER, one process, one graph |
| `tests/test_analogical_shape_math_migrated.py` | 12 gates |
| `results/analogical_shape_math_probe.txt` | the full measured output |

**Not touched:** `domains/reflective_faculty.py`, `domains/rule_signature.py`,
`runners/dsl/src/py.rs`, `substrate/world_adapter.py`,
`seeds/shape_vocabulary.json`, `seeds/seven_meta_shape_subsystems.json`, and
every `.rs` file in the tree.
