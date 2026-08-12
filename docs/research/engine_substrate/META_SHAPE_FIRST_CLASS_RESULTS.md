# META-SHAPE AS A FIRST-CLASS GRAIN — RESULTS

**Prereg:** `META_SHAPE_FIRST_CLASS_PREREG.md`, registered before any code was
written. **Charter:** `SHAPE_AUDIT.md` findings **#1 and #2 only**. **Creator's
directive:** *"Shape needs to be a first class item, do it."*

## Provenance

| | |
|---|---|
| base commit | `ae38fe7` (`Shape audit: 40 confirmed sites …`) |
| worktree | `/home/matt/ocelot-meta-shape-first-class`, branch `meta-shape-first-class` |
| baseline worktree | `/home/matt/ocelot-msfc-baseline`, detached at `ae38fe7` (created because `main` advanced to `d88a519` mid-rung, so the canonical tree was no longer a valid BEFORE) |
| BEFORE engine | `runners/dsl/python/substrate_rs/_native.abi3.so` sha256 **`5c572ca114040090fe343ea1246e4998277afb745f354b40465ad21c69e1c6da`** (debug, built in the baseline worktree from `ae38fe7`'s `.rs`) |
| AFTER engine | sha256 **`f0b496bcaa55954a1557eb2eff6c15c3c984e5f1b648b5ae410fbbbcf49601cb`** (debug, built in this worktree) |
| toolchain | rustup `stable` = rustc 1.97.1. **The Homebrew rustc 1.87 first on `PATH` cannot build this tree** (29 × E0658); every build here is `PATH=/home/matt/.cargo/bin:$PATH`. |
| coherence probe | both engines: `add_node("T", {"lst":[1,2,3], "tup":(1,2,3)})` reads back `[1,2,3]` (`list`) and `(1,2,3)` (`tuple`) **distinctly** ✓ |

---

## The one thing worth reading if you read nothing else

**On an exhaustive sweep of every pair of the agent's eleven meta-shapes, 44 of
55 pairs are ties — and the old recognizer decided every single one of those 44
by the alphabet.** Not "sometimes tie-broken alphabetically": 44/44, always the
alphabetically-first of the tied shapes. That was the deciding step in **80% of
the codebook's pairwise contests**, in the faculty that files the agent's own
knowledge and feeds `analogical_thinking` order-4 and `TransferDecode`.

The fix does not replace the alphabet with a better sort. It **deletes the
tiebreak** — a genuinely tied contest now returns `None`, which is the honest
residual, which is a **mint candidate**. That is the whole point of the rung:
finding #2's defect and finding #1's absence are the *same* hole seen from two
sides. A recognizer that always answers can never produce a residual, and a
grain with no residual can never grow. Fixing the scorer is what makes the mint
path reachable at all.

---

## 1. Verdicts

| bar | verdict | evidence |
|---|---|---|
| **AR1** — the recognizer fix | **GO** | curated set 6/10 → **10/10**, four flips, zero regressions (§2.1). Exhaustive 55-pair sweep: 44 alphabet-decided ties → 44 honest residuals; the 11 genuinely-decided pairs agree exactly (§2.2) |
| **AR2** — mint design registered first | **GO** | §3.2 of the PREREG, built as written, with two deviations both reported in §6 |
| **AR3** — the growth loop closes | **GO** | residual → recurrence → **exactly one** mint → epoch bump → re-decode → **both** recognised against the minted entry; near-variant recognised via rung 1; negative control recognised as `selective_gating` and minted nothing (§4) |
| **AR4** — consumers still work | **GO** | `shape_hits`, `metashape_realisation_counts`, `TransferDecode`, `_run_self_shape` byte-identical before and after a runtime mint grew the codebook 11 → 12 (§5) |
| **AR5** — no regression | **GO** | `cargo test --lib` single-threaded: **740 passed / 0 failed / 4 ignored in BOTH trees**, identical. The default parallel run fails 3 in both trees with *different, non-overlapping* node-id sets — a pre-existing shared-global-counter race, enumerated in §7. Python: 14 files, both trees, **identical failing node-id lists** — 30 pre-existing reds, **zero new** (§7.2) |

**Rung-2/3 refinement (mid-flight, from the creator):** the mint is **not**
rung-4-only. `shape_decode.rs::load_parts` turned out to be genuinely
grain-agnostic, so the full ladder was wired. See §3 — this is the finding I
would flag second.

---

## 2. AR1 — what the recognizer actually does differently

### 2.0 The three defects, and what replaced each

| `SHAPE_AUDIT.md` §2.5 defect | before | after |
|---|---|---|
| the item's typed structure is destroyed (`teach.py:93` discards every attribute **KEY**, every non-string **VALUE**, and the node **TYPE**) | scored `"quintuple multiply a number by five"` | scored the item's **signature**: `[["definition","multiply a number by five"], ["is_a","concept"], ["multiplier_factor","5.0"], ["name","quintuple"]]` — keys are relation **predicates** |
| raw `contains` count at **principle** granularity (two keyword hits scored the same as one) | `score = #principles hit` | lexicographic `(pred_principles, principles, keywords)` — **no weights, no sum**; the legacy score is preserved as the *middle* key so the new order is a strict refinement |
| `then_with(\|\| a.1.cmp(&b.1))` — **ties break alphabetically by the shape's own name** | `associative_recall` wins on the letter `a` | **deleted.** Top two share the full key ⇒ `None` (residual) |

The first key, `pred_principles`, encodes the design claim in one line: **a
keyword matching the item's own typed slot name outranks any amount of prose
evidence.** An item whose slots *are* the shape beats an item that merely talks
about the shape.

### 2.1 The curated set (one process, one codebook, both scorers)

`scripts/meta_shape_first_class_probe.py` reimplements the BEFORE scorer in
Python as a read-only mirror of `shape_decode.rs @ ae38fe7`, so both verdicts are
computed side by side against the *same* graph — no cross-engine comparison, no
drift.

| case | expected | BEFORE | AFTER | |
|---|---|---|---|---|
| `gate the layer by policy` | selective_gating | **hierarchical_invariance_buildup** | selective_gating | ✅ fixed |
| `the selection is a winner-take-all recall from an attractor` | *(residual)* | **associative_recall** | `None` | ✅ fixed |
| `Belief{predict:…, observe:…}` | prediction_minus_observation | **`None`** | prediction_minus_observation | ✅ fixed |
| `Policy{gate:…, target:…}` | selective_gating | **`None`** | selective_gating | ✅ fixed |
| `Note{text:"you should predict things and observe them"}` | prediction_minus_observation | ✔ | ✔ | unchanged |
| `Note{text:"replay during sleep to consolidate"}` | delayed_persistence | ✔ | ✔ | unchanged |
| `Note{text:"a global hormone broadcast"}` | global_message_passing | ✔ | ✔ | unchanged |
| `MarkerClass{marker:"however", role:"contrast"}` | *(residual)* | ✔ | ✔ | unchanged |
| `Concept{name:"quintuple", …, multiplier_factor:5.0}` | *(residual)* | ✔ | ✔ | unchanged |
| `SelectionalClassPair{verb:"slide", …}` | spatial_dynamics | ✔ | ✔ | unchanged |

**6/10 → 10/10. Four flips, all in the right direction, zero regressions.**

The pair worth staring at is rows 3 and 5. `Belief{predict:"the next frame",
observe:"the actual frame"}` — whose *typed slots literally are* the shape —
scored **nothing** before, because the keys were thrown away and the values
("the next frame") contain no keyword. `Note{text:"you should predict things and
observe them"}` — the same idea as *prose* — was classified correctly. **The old
recognizer could see the shape only when it was talked about, never when it was
instantiated.**

### 2.2 The exhaustive sweep (all 55 pairs of the held codebook)

For every unordered pair of distinct MetaShapes, an observation carrying exactly
one keyword from each (chosen so neither keyword is a substring of the other) —
a tie by construction.

| | count |
|---|---|
| pairs swept (11 shapes) | **55** |
| **BEFORE decided by the alphabet** (≥2 shapes tied at the top) | **44** |
| …of those, BEFORE returned the alphabetically-first tied shape | **44 / 44 (100%)** |
| **AFTER on those 44** | **44 × `None`** — the honest residual, no fabricated winner |
| pairs BEFORE genuinely decided on evidence | 11 |
| …AFTER agrees with BEFORE on all 11 | **11 / 11** |

This is the powered claim the PREREG asked for at whatever power the 24-entry
codebook allows: **exhaustive over the entire pairwise space**, not a sample.
And it is a clean separation — the change is confined *exactly* to the cases the
old scorer could not decide, and touches nothing it could.

---

## 3. The ladder — and the mid-flight refinement that made it four rungs, not two

The rung was underway with a `recognize → mint` design when the creator asked
whether the mint went straight from "no match" to "mint", or first checked
whether the residual was itself a *recognisable kind of gap* — rungs 2 and 3 of
the sd loop's own ladder.

**Investigated, and the answer changed the build.** `shape_decode.rs::load_parts`
(`:239`) reads *any* `codebook_type`-typed node carrying `name` + `signature`.
It is genuinely grain-agnostic — CLAUDE.md's claim holds here. So `ShapeDecode`,
`TransformDecode` and `DimInfer` all point at `codebook_type: "MetaShape"` **with
zero new Rust**, and `seeds/meta_shape_growth.json` wires the same four-rung
Occam ladder every other grain has:

| rung | rule | what it decides |
|---|---|---|
| 1 | `msg_decode` / `msg_recognize` | structural cover by a held meta-shape pattern |
| 2 | `msg_transform_decode` / `msg_recognize_transformed` | the residual is a held shape stepping by one uniform per-dimension delta |
| 3 | `msg_infer_dimension` / `msg_recognize_dim` | a generator-composed residual |
| prior | `msg_recognize_prior` | the **keyword bootstrap** — the fixed §2 scorer |
| 4 | `msg_mint_shape` | novelty: mint a new `MetaShape` + `ShapePrinciple` |
| — | `msg_redecode` | codebook growth re-arms every observation |

Two things about this are worth recording precisely, because both were
*measured* rather than assumed.

**(a) The keyword prior sits BELOW rungs 1-3 and ABOVE the mint.** The eleven
seeded MetaShapes carry no `signature` at all, so `load_parts` skips them
entirely and rungs 1-3 are structurally dormant on them. Keywords are the honest
bootstrap — the weakest evidence in the ladder, run last before minting. This is
the PREREG's registered risk 1, confirmed exactly as registered.

**(b) Rung 1 is `Covers`, NOT `ShapeDecode`'s literal set cover — a real grain
difference.** Every other grain's codebook holds *literal* parts, so
`sd_decode`'s `wild_objects: false` literal decode is right there. **This
codebook holds anti-unified lgg PATTERNS**: a minted entry's signature is
`[["buyer", WILD], ["is_a","traderecord"], ["lot", WILD], ["seller", WILD]]`, and
a literal set cover can never match `["buyer","erin"]` against `["buyer", WILD]`.
`Covers` (`term.rs::covers_value`, "WILD matches anything") is the dual primitive
that does — and it is what `AntiUnify` is paired with everywhere else in this
tree. Verified live before rewiring: `Covers(minted_core, near_variant) == True`
while `ShapeDecode(near_variant, codebook_type="MetaShape")` returned no
coverage at all. `msg_decode` still runs `ShapeDecode` for its `residual` /
`covered_count` diagnostics; the rung-1 *verdict* is the `Covers` test, and
`covered_by` is the **most specific** covering pattern (`Argmax` by
`FixedCount`) — a derived specificity, never an asserted ordinal.

**Rung 3 is an honest no-op at this grain today**, and the seed says so in its
own comment: a meta-shape signature's slots are strings, not integer
coordinates, so `DimInfer`'s generators (rotation90 / reflections / scale2 /
modular — all coordinate maps) have nothing to act on. It is wired anyway
because the ladder's shape is the point and because a future meta-shape
signature carrying ordered slots lights it up for free.

---

## 4. AR3 — the growth loop, live

`scripts/meta_shape_growth_probe.py`, booting only `shape_vocabulary` +
`meta_shape_growth`. Every transition below is a `run_rules` fixpoint; there is
no Python iteration anywhere in the loop.

| step | observations (status, covered_by) | codebook |
|---|---|---|
| observe `TradeRecord{buyer:alice, seller:bob, lot:7}` | `residual`, — | 11 |
| observe `TradeRecord{buyer:carol, seller:dave, lot:9}` | `recognized` ×2, both `ms_buyer_is_a_lot_seller` | **12** |
| observe `TradeRecord{buyer:erin, seller:frank, lot:11}` *(near-variant)* | `recognized` ×3 | 12 |
| observe `Note{text:"gate the layer by policy"}` *(negative control)* | `recognized_prior`, **`selective_gating`** | **12 — no new mint** |

The minted entry:

```
MetaShape{ name: "ms_buyer_is_a_lot_seller", support: 2, minted: 1,
           signature: [["buyer", WILD], ["is_a", "traderecord"],
                       ["lot", WILD], ["seller", WILD]] }
  -has_principle-> ShapePrinciple{ name: "ms_buyer_is_a_lot_seller",
                                   keywords: ("buyer", "lot", "seller") }
```

Every clause of the PREREG's AR3 is discharged: the single occurrence is
**correctly a residual and not forced into a wrong existing shape**; recurrence
mints **exactly one** entry; the epoch bump re-arms *both* group members and
they re-decode to `recognized` **against the newly minted entry**; a
never-before-seen near-variant is recognised by rung 1 with no further mint; and
the negative control — an observation that already had a home — recognises
correctly and mints nothing.

### 4.1 The mint's support discipline, as built

* **Grouping is by PREDICATE SET** — the sorted, de-duplicated set of a
  signature's relation predicates. Sorted and set-valued deliberately:
  `SHAPE_AUDIT.md` §3.1 documents the `CapabilityAxis` key as *"order-dependent
  and truncated at three"* with two distinct failure directions; this key is
  neither.
* **Support = 2.** Not a swept knob — the smallest cardinality at which "recurs"
  is *defined*. The alternatives were considered in the PREREG and declined in
  writing: P7-C's distribution-derived quantile needs a distribution a 24-entry
  codebook does not have, and a similarity threshold is exactly the
  `stroke_codebook.py:82 DEFAULT_DTW_THRESHOLD = 0.15` Pattern E defect
  `SHAPE_AUDIT.md` §6.3 reports.
* **Non-triviality is structural**: the lgg must fix ≥1 leaf
  (`fixed_count > 0`). Two unrelated items anti-unify to all-WILD and mint
  nothing. Symmetrically, rung 1 refuses an all-WILD pattern as a cover — a
  degenerate entry would otherwise swallow the whole grain.
* **One minter per group per pass**: the lowest node id. A canonical-representative
  pick, the same shape `retire_duplicate_gap`'s `Argmin` uses and which
  `SHAPE_AUDIT.md` §2.7 explicitly rejects as Pattern A — not a similarity rank.
* **Mint-once across passes**: `Not Exists` a MetaShape with this name, the
  `sd_mint_quantum` guard shape.

### 4.2 The bug the negative control caught (and the derived fix)

The first working mint emitted `is_a` among the minted principle's `keywords`.
Because **every** observation carries an `is_a` relation by construction, the
minted shape then scored a predicate hit on literally everything and won the
keyword prior against the correct answer — live, the `"gate the layer by policy"`
control came back as `ms_buyer_is_a_lot_seller` instead of `selective_gating`.
This is the PREREG's registered risk 4, biting exactly where it was registered.

The fix is **derived, not a name-list**: a predicate present in *every* held
observation carries zero discriminative information and is dropped from the
keywords. A boolean information test over the observed population — not a tuned
frequency threshold, and emphatically not a hardcoded stop-list of predicate
names, which would have been the very Pattern A defect this rung exists to
remove. The group **key** (the shape's identity and name) still uses the full
predicate set; only what the weak keyword rung can see is narrowed.

Measured consequence, both ways:

| population at mint time | minted keywords |
|---|---|
| only the two group members (everything universal) | `()` — the shape is rung-1-only, which is the honest outcome: unreachable by the weak keyword rung, perfectly reachable by structural `Covers` |
| a mixed population (2 unrelated `Note`s already observed) | `("buyer", "lot", "seller")` — `is_a` correctly dropped, and all four verdicts correct |

---

## 5. AR4 — the consumers finding #1 named

Run against the fixed recognizer **and** against a codebook that a runtime mint
had grown from 11 → 12 entries:

| consumer | before mint | after mint |
|---|---|---|
| `analogical_thinking.shape_hits("gate the layer by policy")` | `{hierarchical_invariance_buildup, relational_structure_match, selective_gating}` | **identical** |
| `analogical_thinking.metashape_realisation_counts` | 9 shapes, `relational_structure_match:12 … feedback_control:1` | **identical** |
| `TransferDecode` (regulation goal) | `meta_shape="feedback_control"`, 1 mechanism retrieved | **identical** |
| `reflective_faculty._run_self_shape` | seven meta-shapes, primary `hierarchical_invariance_buildup_subsystem` (12 vs 6) | **identical** |

Nothing broke, and nothing silently emptied. The minted shape correctly does
*not* appear in the realisation counts — no `Concept` realises it yet, which is
what that reader measures.

`shape_hits` returning three shapes where the fixed recognizer returns one is
**not** an inconsistency: `shape_hits` is deliberately a *set* of every shape
with a principle hit (a MAC-stage recall set), while `RecogniseShape` is a
*verdict*. That distinction is exactly the MAC/FAC framing
`RULES_AS_SHAPE_DESIGN_SPIKE.md` §4.2 imports — and it is worth naming that
`analogical_thinking`'s own `_compute_analogy` still treats its cheap
content-match as the verdict at all five orders. **That is `SHAPE_AUDIT.md` §2.4,
out of charter here, and untouched.**

---

## 6. Deviations from the PREREG

| registered | built | why |
|---|---|---|
| `recognize → mint`, a two-step | the **full four-rung ladder** (§3) | the creator's mid-flight refinement, plus the measured finding that `load_parts` is grain-agnostic so rungs 2-3 cost zero new Rust |
| rung 1 as `ShapeDecode` set cover | rung 1 as **`Covers`** | measured: a literal set cover cannot match a WILD-bearing lgg pattern, which is what this codebook holds (§3b) |
| minted keywords = the core's fixed predicates | = the **discriminative** fixed predicates | the universal-predicate bug the negative control caught (§4.2) |

Nothing in the PREREG's bars was weakened; two were built stronger than
registered.

---

## 7. AR5 — regression, as LISTS

Per CLAUDE.md's retracted-baseline rule (*"a baseline must be a list of node ids,
never a count or a characterisation"*).

### 7.1 Rust

`cargo test --lib`, **single-threaded** (`--test-threads=1`), the deterministic
run:

| tree | result | failing node ids |
|---|---|---|
| baseline `ae38fe7` | 740 passed / 0 failed / 4 ignored | **[]** |
| this branch | 740 passed / 0 failed / 4 ignored | **[]** |

**Ten new gates** ship with the change, in
`shape_decode::meta_shape_first_class_tests` — five for the recognizer (tie ⇒
residual; untied still resolves; keyword evidence beats an equal principle
count; a predicate hit outranks a prose hit; the legacy flat-text path still
scores) and five for the mint (one occurrence is not recurrence; recurrence
mints a WILD-bearing core that covers a never-seen variant; only the group
leader mints; unrelated residuals do not group; a universal predicate is
dropped from the minted keywords). All 10 pass.

The **default parallel** run fails 3 in *both* trees, with **different,
partially non-overlapping** sets:

| tree | failing node ids (parallel) |
|---|---|
| baseline `ae38fe7` | `scale_audit::tests::totals_are_always_emitted_even_when_every_cell_is_zero`, `shape_decode::dim_infer_tests::d_codebook_growth_is_seen_by_the_encoder`, `shape_decode::dim_infer_tests::d_green_different_goals_are_seven_distinct` |
| this branch | `scale_audit::tests::known_counts_are_exact`, `scale_audit::tests::units_outside_any_evaluation_are_reported_not_hidden`, `shape_decode::dim_infer_tests::d_codebook_growth_is_seen_by_the_encoder` |

Every one of these passes in isolation and all 740 pass single-threaded in both
trees. **This is a pre-existing shared-global-counter race in the
`scale_audit` instrumentation, not attributable to this branch** — the fact that
the *baseline* fails a set this branch does not, and vice versa, is the proof.
It is also **already documented in the tree**, at `shape_decode.rs`'s own
`AUDIT_TESTS` mutex comment: *"THE SCALE AUDIT IS PROCESS-GLOBAL, AND `cargo
test` IS PARALLEL BY DEFAULT … Run these with `--test-threads=1` as well."* The
lock covers the audit tests it guards; the `dim_infer` counter tests reached by
the same globals are not all inside it.
Reported rather than dismissed, because a count would have hidden it: both runs
read "737 passed / 3 failed", identical numbers over different failures.

**A build note that is not optional.** `runners/dsl/Cargo.toml:12` pins
`pyo3 = { features = ["extension-module", …] }` **unconditionally**, so
`cargo test --lib` cannot link a test binary at all on Linux (undefined
`PyErr_*`, `PyBytes_*`, `PyObject_Call`, …). Every `cargo test` figure above
required:

```
RUSTFLAGS="-C link-arg=-L$(python3 -c 'import sysconfig;print(sysconfig.get_config_var("LIBDIR"))') -C link-arg=-lpython3.13" \
LD_LIBRARY_PATH=/home/linuxbrew/.linuxbrew/lib cargo test --lib
```

README's *"`cargo test` (debug) is the memory-safe default"* is, as written,
not runnable in this environment.

### 7.2 Python

Fourteen files — every file in `tests/` that references `categorise_by_shape`,
`RecogniseShape`, `MetaShape`, `shape_hits`, `analogical_thinking`,
`_run_self_shape`, `TransferDecode` or `domains.teach` — run **per file**, in
both trees, on the same day, each tree against its own engine.

| file | BEFORE (`ae38fe7`) | AFTER (this branch) |
|---|---|---|
| `test_mechanism_transfer_migrated.py` | 5 passed | 5 passed |
| `test_analogical_relative_ranking.py` | 6 passed | 6 passed |
| `test_reframing_proposer.py` | 9 passed | 9 passed |
| `test_code_curriculum_migrated.py` | TIMEOUT @900s (unmeasured) | **15 passed** in 2358s (39m18s) |
| `test_adaptive_bins_migrated.py` | 24 passed | 24 passed |
| `test_render_geometry_migrated.py` | 18 passed | 18 passed |
| `test_actor_goals_migrated.py` | 5 failed / 6 passed | 5 failed / 6 passed |
| `test_seed_guard_migrated.py` | 4 passed | 4 passed |
| `test_self_process_introspection.py` | 1 failed / 13 passed | 1 failed / 13 passed |
| `test_experiment_composer_graph.py` | 4 failed / 54 passed | 4 failed / 54 passed |
| `test_teacher_dispatch_native_migrated.py` | 1 passed | 1 passed |
| `test_teacher_dispatch.py` | 9 passed | 9 passed |
| `test_compilation_cycle.py` | 15 passed | 15 passed |
| `test_meaning_inference_migrated.py` | 20 failed / 38 passed | 20 failed / 38 passed |

**The failing node ids, enumerated — identical sets, both trees, no
substitutions:**

* `test_actor_goals_migrated.py` — `test_no_cover_control_charity_funds_renewables`,
  `test_headline_active_voice_oil_company_funds`,
  `test_no_cover_control_active_voice_charity_funds`,
  `test_agency_recipient_company_received_a_grant`,
  `test_null_unrelated_verb_mints_no_layered_goal`
* `test_self_process_introspection.py` — `test_honest_floor_preserved_for_genuine_gap`
* `test_experiment_composer_graph.py` — `test_full_combo_gradient_embed_matches_shift_rule_thresholds_oracle`,
  `test_test_alone_graph_rule_mints_experiment_without_host_add_node`,
  `test_vary_bare_graph_rule_fires_and_picks_skip_seeds`,
  `test_embed_graph_rule_fires_and_embeds_a_real_variant`
* `test_meaning_inference_migrated.py` — `test_headline_infers_provisional_sense_from_selectional_restriction`,
  `test_combine_raises_confidence_not_duplicates`,
  `test_revisable_belief_is_held_and_superseded_on_grounding`,
  `test_definition_sense_outranks_selectional_sense_for_same_term`,
  `test_agent_teaches_new_selectional_coverage`,
  `test_headline_infers_provisional_sense_from_derivational_suffix`,
  `test_headline_infers_from_surgical_act_suffix`,
  `test_headline_infers_from_enzyme_suffix`,
  `test_morphology_sense_is_revisable_and_superseded_on_grounding`,
  `test_morphology_confidence_ranks_below_selectional`,
  `test_agent_teaches_new_morphological_coverage`,
  `test_analogy_confidence_ranks_below_definition_and_above_selectional`,
  `test_headline_structural_analogy_transfers_class_with_no_comparison_cue`,
  `test_structural_analogy_sense_is_revisable_and_superseded_on_grounding`,
  `test_insitu_appositive_definition_grounds_is_a_from_clean_boot`,
  `test_insitu_parenthetical_definition_grounds_is_a_from_clean_boot`,
  `test_pipeline_selectional_sense_reaches_read_and_comprehend`,
  `test_pipeline_appositive_definition_sense_reaches_read_and_comprehend`,
  `test_pipeline_morphology_sense_reaches_read_and_comprehend`,
  `test_report_is_id_normalised_identical_with_and_without_meaning_inference`

**AR5 Python verdict: GO — zero node ids red in AFTER that are green in
BEFORE.** All 30 reds are pre-existing at `ae38fe7`, node id for node id.

Two things worth stating rather than glossing:

* `test_meaning_inference_migrated.py`'s 20 reds include
  `test_agent_teaches_new_selectional_coverage` and
  `test_agent_teaches_new_morphological_coverage` — the two `teach()`-exercising
  tests in the file, i.e. exactly where a `teach()` change would show. They are
  red **identically in both trees**, so the change is not implicated; but their
  being pre-red means **this suite could not have caught a `teach()` regression
  either way**, and that is a gap in the evidence, not a clean bill of health.
* `test_code_curriculum_migrated.py` needs **~40 minutes** and timed out at the
  900s per-file budget both suites originally ran under. Re-run standalone with
  a 2400s budget it is **15 passed / 0 failed in 2358s (39m18s)** on this branch.
  BEFORE was left unmeasured at that budget, and deliberately so: **AFTER being
  fully green makes the BEFORE comparison unnecessary for AR5's claim** — a
  regression can only appear as a red, and there are none. What the BEFORE gap
  does cost is the ability to say whether the branch made it *slower*; it does
  not weaken "zero new reds".

The wider suite (`pytest tests/ -k migrated`) was **not** run — out of budget
for this rung, and named here as the honest limit of AR5's coverage.

---

## 8. Everything that broke on the way

1. **The Homebrew rustc 1.87 first on `PATH` cannot build this tree** — 29 ×
   E0658. Silent until you read the errors; `cargo build` exits non-zero with a
   generic message. Always `PATH=/home/matt/.cargo/bin:$PATH`.
2. **`NUM_TERM_VARIANTS` is a hard array length.** Adding a `TermNode` variant
   requires bumping `term_variants.rs:15` *and* using the next free dense index
   (211, not a gap). The compiler catches it, but the error names the array, not
   the variant.
3. **Γ rejected the new edge type outright** (`Γ rejects: type 'observed_shape'
   not in vocabulary (Type-2)`) until the seed declared productions. This is a
   *good* failure — it is the admissibility grammar working — and it is why this
   seed ships three real productions instead of `"productions": []` (the exact
   omission CLAUDE.md's SHAPES-NOT-NUMBERS section reports in 454 of 634
   rule-carrying manifests).
4. **`Plus` takes `items`, not `a`/`b`.** A `{"type":"Plus","a":…,"b":…}` effect
   parsed without error and silently did nothing — the epoch never bumped and
   `msg_redecode` never fired, so the loop looked like it did not close when in
   fact one effect was inert. Found by comparing against
   `sd_mint_generator`'s own JSON.
5. **`Count(None) == 0` read a codebook that could not be consulted as full
   coverage.** With no MetaShape carrying a signature, `ShapeDecode` returns
   `{authored: false, reason: "no held parts …"}` — *no `residual` key at all*.
   A bare "residual is empty" rung-1 guard therefore recognised every
   observation against nothing (measured: all four probe observations came back
   `recognized` with a meaningless `covered_by`). This is precisely the hazard
   `shape_decode.rs` warns about in its own panic text — *"an absence produced
   by a LOOKUP is not evidence of a measurement"* — and the fix is to require
   positive evidence, which is what pushed rung 1 onto `Covers`.
6. **The universal-predicate keyword pollution** (§4.2), caught only by the
   negative control. Worth noting that the positive cases all passed while this
   bug was live.

---

## 9. Remaining uncertainties, honestly

* **Rung 2 is built but unexercised at this grain.** No probe here produced a
  residual that `TransferDecode` explained as a consistent substitution on a
  held meta-shape — partly because rung 1's WILD-bearing patterns already absorb
  that case. Whether rung 2 ever fires on real taught data is **unmeasured**.
* **Rung 3 is a graceful no-op at this grain today** (§3), by construction, not
  by accident.
* **The minted principle's keywords can still substring-match unrelated prose**
  (`"lot"` inside `"a lot of"`). Inherent to the keyword rung; mitigated by the
  prior sitting last in the ladder, unmeasured at scale.
* **`teach()` now mints a `ShapeObservation` per taught item.** Inert when the
  seed is not loaded, but it is a real node-count change; the Python regression
  in §7.2 is the only evidence about its blast radius.
* **`categorise_by_shape` returns `None` more often** (honest residuals), which
  routes those items to `teach()`'s existing `domain`/`topic` fallback — the same
  place they went when they scored zero. Confined to previously-tied cases, but
  the *set* of previously-tied cases is large (§2.2).
* **Support = 2 is defensible, not validated.** No experiment here shows that 2
  is better than 3 on real taught data, and the PREREG deliberately did not
  claim one.
* **`recognise_meta_shape`'s text path still exists** for `TransferDecode`,
  which flattens a structured goal (a Tuple-of-Tuples — already relation-shaped!)
  into a single string before scoring. Pointing `TransferDecode` at the
  structural path is a named, unbuilt follow-on: it would give the mechanism-
  transfer faculty the same predicate-aware scoring for free.

## 9.1 Audit findings noticed in passing, NOT fixed (out of charter)

* **§2.4** — `analogical_thinking._compute_analogy` still treats a string-token
  overlap as the verdict at all five orders and never consults a concept's
  edges. Confirmed still true; untouched.
* **`seeds/shape_vocabulary.json` wires `feedback_control -has_principle-> regulate`,
  and there is no `ShapePrinciple{name:"regulate"}` in the manifest** — the
  target is a `FunctionalRole`. It works (the scorer walks `has_principle`
  without type-checking the target) and it is why `feedback_control` is one of
  the few shapes that can score 2 and break out of a tie. Recorded as an
  inconsistency, not repaired.

---

## 10. Reproduce

**SUPERSEDED (2026-08-12, commit `ddf39ec`):** at the time this rung's own
branch was written, the committed `.so` was stale — `ae38fe7`'s pre-fix
8.6 MB release build, while a 140 MB debug build was deliberately left
uncommitted, so a fresh checkout of `meta-shape-first-class` carried Rust
source its own binary did not implement. This was caught and fixed before
merge: a proper `--release` engine was rebuilt from this exact source and
committed (`ddf39ec`), verified against the coherence probe and this rung's
own gate suite, before `meta-shape-first-class` was merged to `main`.
**On `main` today, the committed `.so` IS the engine this source describes.**
The original warning is left below, historical, for anyone reproducing this
exact branch state rather than `main`.

```bash
git worktree add --detach /tmp/msfc-baseline ae38fe7
git worktree add --detach /tmp/msfc          meta-shape-first-class

for T in /tmp/msfc-baseline /tmp/msfc; do
  (cd $T/runners/dsl && PATH=/home/matt/.cargo/bin:$PATH CARGO_BUILD_JOBS=2 cargo build --lib)
  cp $T/runners/dsl/target/debug/libsubstrate_rs.so \
     $T/runners/dsl/python/substrate_rs/_native.abi3.so
done

# AR1 (curated + exhaustive) and AR4
cd /tmp/msfc && python3 scripts/meta_shape_first_class_probe.py
# AR3 — the growth loop
cd /tmp/msfc && python3 scripts/meta_shape_growth_probe.py
# AR5 Rust (note the link flags — see §7.1)
cd /tmp/msfc/runners/dsl && PATH=/home/matt/.cargo/bin:$PATH \
  LD_LIBRARY_PATH=/home/linuxbrew/.linuxbrew/lib \
  RUSTFLAGS="-C link-arg=-L/home/linuxbrew/.linuxbrew/lib -C link-arg=-lpython3.13" \
  cargo test --lib -- --test-threads=1

# regenerate the seed (never hand-edit seeds/meta_shape_growth.json)
python3 tools/build_meta_shape_growth_seed.py
```

## 11. Files

| file | |
|---|---|
| `runners/dsl/src/shape_decode.rs` | the fixed scorer (`ms_relations` / `ms_score_shapes` / `ms_pick` / `recognise_meta_shape` / `eval_recognise_shape`) + `eval_meta_shape_mint` |
| `runners/dsl/src/term.rs`, `jsonio.rs`, `reflect.rs`, `term_variants.rs` | `MetaShapeMint` Term plumbing (additive) |
| `tools/build_meta_shape_growth_seed.py` | the seed EMITTER — the seed is generated, never hand-edited |
| `seeds/meta_shape_growth.json` | 10 rules + 3 Γ productions |
| `domains/meta_shape.py` | mechanical glue only: `item_signature` + `observe` |
| `domains/teach.py` | `categorise_by_shape` now passes a signature; `teach()` observes |
| `scripts/meta_shape_first_class_probe.py`, `scripts/meta_shape_growth_probe.py` | the AR1/AR3/AR4 harnesses |

**Not touched:** `runners/dsl/src/rule_reflect.rs`, `add_rule`'s installation
path in `substrate.rs`/`graph_rules.rs`, `domains/rule_signature.py`,
`runners/dsl/src/py.rs`, `substrate/world_adapter.py`, `seeds/shape_vocabulary.json`.
