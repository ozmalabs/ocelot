# Meta-shape arity + `CapabilityAxis` key separator — two fixes — RESULTS

**Prereg:** `META_SHAPE_ARITY_AND_KEY_SEPARATOR_FIXES_PREREG.md`, committed
(`fd7bbec`) before any code was edited. Worktree
`/home/matt/ocelot-meta-shape-arity-key-fixes`, branch
`meta-shape-arity-key-fixes`, from `main` at `cf774d3`. Baseline runs used a
second, untouched worktree at the same commit
(`/home/matt/ocelot-msak-baseline`) so the primary tree was never written to.

**Both fixes landed. Both bars met. The measurement inverted one of the two
claims it was checking**, which is the most important line in this document and
is expanded in §4.3: the collision the spike reported at the `induced_` grain is
**unreachable in the measured vocabulary (0 of 61 predicates could produce
one)**, while the *same lossy join* in `shape_decode.rs`'s minted `MetaShape`
name — which the spike listed as "canonical after today's fixes" — has **23
reachable collision pairs in the real attribute-key vocabulary**. The second is
named, measured, and **not fixed here**, with the exact fix and the exact
hazard that puts it in its own rung.

---

## 1. The two fixes, in one line each

| | Bug 1 (spike §3.3.1) | Bug 2 (spike §7.2) |
|---|---|---|
| defect | meta-shape recognition was **arity-exact** | the `CapabilityAxis` key join is **lossy** |
| fix | a NEW Rust Term `CoversOpen` (+ the six `msg_*` guards moved to it) | percent-escape the separator and the escape introducer |
| shared primitive touched | **none** — `covers_value` and `Covers` are byte-unchanged | none |
| existing values changed | none (a new Term; nothing else uses it) | **none** — measured, §4.4 |
| measured live prevalence | 1/1 — reproduced on the first probe | **0** — §4.3 |

---

## 2. AR0 — before, live, on the committed engine

Reproduced before the prereg was written, on `cf774d3`'s own engine.

**Bug 1.** `shape_vocabulary` + `meta_shape_growth`, three `TradeRecord`
observations, the third carrying one extra attribute:

```
recognized  ms_buyer_is_a_lot_seller  [[buyer,alice],[is_a,traderecord],[lot,7],[seller,bob]]
recognized  ms_buyer_is_a_lot_seller  [[buyer,carol],[is_a,traderecord],[lot,9],[seller,dave]]
residual    None                      [[buyer,gary],[is_a,traderecord],[lot,13],[note,anything],[seller,hank]]

minted MetaShape ms_buyer_is_a_lot_seller
  signature (('buyer',WILD), ['is_a','traderecord'], ('lot',WILD), ('seller',WILD))
```

The spike's §3.3.1 prediction held exactly, and its own stated refutation
condition ("If it does, I am wrong and I would want to know why") did not fire.

**Bug 2.** `sorted(["a_b","c"])` and `sorted(["a","b_c"])` both join to
`induced_a_b_c`.

---

## 3. Bug 1 — investigation (AR1), and the arm selected

### 3.1 The three arms, and how the pre-registered tests decided

**Arm A — fixed-arity discipline (spike §5): REJECTED, but not for the reason
I expected, and it is fairer than it looks.** The prereg's test 1 asked whether
Arm A's growth path actually terminates in a minted *k+1* shape rather than
stranding the observation. **It does.** Measured on the unmodified engine, with
a *second* extra-attribute observation (recurrence ≥ 2 is `MetaShapeMint`'s own
condition):

```
recognized  ms_buyer_is_a_lot_seller       (4 relations)
recognized  ms_buyer_is_a_lot_seller       (4 relations)
recognized  ms_buyer_is_a_lot_note_seller  (5 relations)
recognized  ms_buyer_is_a_lot_note_seller  (5 relations)
SHAPES: ['ms_buyer_is_a_lot_seller', 'ms_buyer_is_a_lot_note_seller']
```

So Arm A is self-consistent and the ladder does grow. **What kills it is what
that growth COSTS**: one codebook entry per attribute-SET, and a *singleton*
variant — one item that happens to carry an extra field — is never recognised
and never mints (support 1 < 2), so it sits at `residual` permanently. For a
`teach`-driven grain whose items are heterogeneous dicts, that is combinatorial
fragmentation of exactly the vocabulary the codebook exists to generalise, and
it is the failure the meta-shape rung was built to remove.

**Arm C — change `covers_value`'s `Tuple | List` arm for everyone: REJECTED on
blast radius, enumerated not characterised.** Every caller, by file:line:

| caller | what it is |
|---|---|
| `runners/dsl/src/term.rs:6521` | the `Covers` Term's evaluator |
| `runners/dsl/src/shape_decode.rs:1086`, `:1088` | `covers_relation` — the sd loop's per-relation compare, both `wild_objects` role orders |
| `runners/dsl/src/shape_decode.rs:8653` | a Rust unit test |
| `seeds/prog_chunk_growth.json` | 4 `Covers` guards (chunk grain) |
| `seeds/prog_construction_loop.json` | 4 `Covers` guards (construction grain) |
| `domains/analogical_thinking.py:499` | the analogical faculty's own coverage check |
| `scripts/structural_residual_gate.py:47` | a gate script |
| `scratch_rr/rr1_covers_witness_probe.py:50`, `scratch_rr/rr1_corpus_sweep.py:84`, `:103` | scratch probes |

`shape_decode.rs:1086/1088` alone disqualifies Arm C: `covers_relation`
prefilters on `step_t.len() != goal_t.len()` and then calls `covers_value` on
two RELATIONS. Making the list arm open-arity globally would change what the
sd loop counts as a covered relation at every grain in the tree — a semantics
change to the decode core, sitting under the F-16, humanoid, ink, speech and
chunk faculties, for a defect that lives in one seed's six guards.

**Arm B — a meta-shape-grain-LOCAL Term: SELECTED**, on the prereg's test 2.

### 3.2 Test 2, the deciding evidence: the engine already reads relation sets this way

`shape_decode.rs::covers_relation` (`:1047-1100`) asks *"does SOME relation in
the part's signature cover this goal relation?"* and leaves the uncovered goal
relations as the residual. It never requires the two signatures to be the same
length. **Open arity at relation-set grain is the sd loop's existing, settled
semantics**; the meta-shape rung's whole-signature `Covers` guard was the
outlier. Arm B restores consistency rather than inventing semantics, which was
the pre-registered condition for preferring it — and I record that this is the
arm I said in advance I expected, so the agreement is not over-credited.

### 3.3 What `CoversOpen` is, and the general finding it carries

`covers_open_value` (`runners/dsl/src/term.rs`, next to `covers_value`):

* pattern WILD ⇒ true (as `covers_value`);
* both sides list-like ⇒ true iff there is an **injective** map from pattern
  elements to instance elements under which each pattern element
  `covers_value`s its image (maximum bipartite matching, Kuhn's). Superset-
  tolerant, **never** subset-tolerant;
* anything else ⇒ delegate to `covers_value` verbatim — Dict, Set and scalar
  arms are untouched.

The matching is injective rather than a per-element existential so two pattern
relations can never be satisfied by one instance relation. At this grain a
signature's predicates are distinct by construction, so the two readings agree
on real data; the matching is there so the semantics is honest independently of
that contingent fact, not because a failing case was observed
(`covers_open_matching_is_injective` constructs one deliberately).

**The finding worth reusing, stated narrowly.** The prereg forbade claiming
that spike §3.3's three-way container trade is dissolved, and it is not. The
honest statement is one level down:

> The trade — *no single container gives WILD slots AND residual capture AND
> open arity* — is a statement about **one container serving one level**. A
> shape signature in this tree is **not one container**: it is a SET of
> POSITIONAL relations. Asking for set semantics outside and tuple semantics
> inside gets all three properties, and costs exactly one function that
> delegates to the existing one at every level but the outermost.

That is why the fix is 60 lines and not a re-encoding. It does **not**
generalise for free to grains whose outer container is genuinely one object
(§7).

### 3.4 The behaviour change this buys, stated plainly

Under `CoversOpen`, a recurring strict SUPERSET no longer mints its own entry —
the same four-observation probe as §3.1 now ends with **one** shape:

```
shapes now: ['ms_buyer_is_a_lot_seller']
  4 recognized ms_buyer_is_a_lot_seller
  4 recognized ms_buyer_is_a_lot_seller
  5 recognized ms_buyer_is_a_lot_seller
  5 recognized ms_buyer_is_a_lot_seller
```

This is the Occam ladder working as designed (rung 1 hit ⇒ no graph growth) and
it is the trade Arm B buys: **the codebook stops fragmenting per attribute-set,
and in exchange a genuine SUBTYPE — a richer idiom that strictly contains a
held one — is recognised as the general shape instead of earning its own
entry.** Whether the ladder should be able to mint a refinement UNDER a
recognised shape is a real design question this rung does not answer and does
not touch; it is `named-not-built` in §7.

---

## 4. Bug 2 — investigation (AR3), and the fix

### 4.1 Prevalence at the reported site: measured **zero**

Every `induce_concern` call site in the tree, by AST scan (not grep):

| | count |
|---|---|
| total call sites | **192** |
| `name_hint` supplied (the join never runs) | **186** |
| derived key (the join runs) | **6** |

The six derived sites, with their actual keys:

| site | predicates | key |
|---|---|---|
| `scripts/magnitude_fit_gate.py:82` | damp, oscillate, overshoot | `induced_damp_oscillate_overshoot` |
| `scripts/predicate_grounding_gate.py:108` | damp, oscillate, overshoot | `induced_damp_oscillate_overshoot` |
| `scripts/concern_grounding_gate.py:119` | damp, oscillate, overshoot | `induced_damp_oscillate_overshoot` |
| `scripts/concern_induction_gate.py:57` | detect, pairwise, type | `induced_detect_pairwise_type` |
| `scripts/concern_induction_gate.py:62` | damp, oscillate, overshoot | `induced_damp_oscillate_overshoot` |
| `tests/fixtures/composer_driver_parity/capture.py:202` | move, stop | `induced_move_stop` |

* **Real collisions among live derived keys: 0.**
* **Derived-site predicates containing `_` (the necessary condition): 0.**
* Widening to *every* site with a source-literal observation — 92 sites, i.e.
  what would happen if every call dropped its `name_hint` — the vocabulary is
  **61 distinct predicates, of which exactly ONE (`for_each`) contains `_`**,
  producing 40 distinct keys and **0 collisions**.

The mechanism is arithmetic and certain. The prevalence at this site is nil,
and the prereg required saying so rather than folding it into a justification.

### 4.2 AR3.2 — the convention question

Spike §7.1 lists four identity schemes in use. None fits as-is:

* **bare `name`** — this key exists precisely because a name was not enough;
* **content hash** (`Substrate::rule_content_hash`) — closes the collision but
  changes **every** key value, which AR3.3 forbids without an enumeration;
* **structural equality** (`AddNodeIfAbsent`'s attr-subset scan) — the right
  answer in principle (spike §7.3: a world-model fact should be keyed
  structurally) but **unavailable here**: the consumer is a rule guard
  comparing an `Eq`-able scalar, which is spike §7.2's own stated constraint;
* **derived string join** — the defective one.

So the fix is the minimal **injective refinement of the existing scheme**:
percent-escape the separator (`_` → `%5f`) and the escape introducer
(`%` → `%25`). Escaped components contain no bare `_`, so the split is
unambiguous, and no component can forge an escape sequence. A **doubling**
scheme (`_` → `__`) was considered and rejected as NOT injective: `["a_","b"]`
and `["a","_b"]` both produce a run of three underscores.

### 4.3 THE MEASUREMENT THAT INVERTED THE CLAIM

The same lossy join exists a second time, in Rust:
`shape_decode.rs:5749`, `let name = format!("ms_{}", key.join("_"))` —
`MetaShapeMint`'s minted shape NAME, which `msg_mint_shape` uses as its
mint-once guard (`Not Exists` a `MetaShape` with this name). Spike §7.1 lists
this site as *"canonical after today's fixes"*.

Measured over the real vocabularies, with the same test in both cases — does
there exist `x, y` in the vocabulary with `x < y` and `x_y` also in the
vocabulary (the smallest reachable collision: `{x_y}` and `{x, y}` join
identically once sorted):

| grain | vocabulary | contains `_` | reachable collision pairs |
|---|---|---|---|
| `induced_` (`reflective_faculty.py`) | 61 `induce_concern` predicates | 1 | **0** |
| `ms_` (`shape_decode.rs`) | 1235 seed-declared attribute keys + `is_a` | 920 | **23** |

Examples from the 23: `{goal, kind}` vs `{goal_kind}`; `{claim, id}` vs
`{claim_id}`; `{base, weight}` vs `{base_weight}`; `{keywords, text}` vs
`{keywords_text}` — all pairs of attribute keys that genuinely co-occur on
taught items in this tree.

**Consequence at that site**, read from the rule: `MetaShapeMint` groups
observations by predicate SET (structural — that part is not lossy), but the
mint guard compares the joined NAME. A collision therefore **blocks a
legitimately distinct shape from ever minting** — the same "failure direction
2" the audit called the dangerous one, at the site where it is actually
reachable.

**It is NOT fixed here, deliberately.** The brief scoped Bug 2 to
`reflective_faculty.py`, and the honest fix at the `ms_` site is not the
escaping one: **every** meta-shape signature carries an `is_a` relation by
construction, so escaping would rename **every** `MetaShape` ever minted
(`ms_buyer_is_a_lot_seller` → `ms_buyer_is%5fa_lot_seller`), churning persisted
graphs and every gate that names one. The correct fix is the structural one
spike §7.3 already argues for: emit the sorted predicate list as a `pred_key`
attr on the minted node and guard on **that** instead of on the name, leaving
the name purely cosmetic. That is a ~20-line change and it carries one real
hazard that needs its own rung: a checkpoint-resumed agent holds `MetaShape`
nodes minted *without* `pred_key`, so a `pred_key`-only guard would re-mint
them — exactly the class of defect `_reconcile_seed_*` exists for, and exactly
the kind of thing that must not be bolted onto a rung whose bars were
registered for something else.

### 4.4 AR3.3 / AR4.3 — literal-string readers, and no key churn

`capability_keys` has 498 references across `.py` + `.json`; the overwhelming
majority are seed manifests declaring what a seed *provides* (authored strings,
never derived). The derived keys reach: `Observation.key` →
`sd_mint_quantum`/`sd_dedup_existing`'s `Eq` guard →
`CapabilityAxis.capability_keys` → the five `reflective_faculty` read sites →
the captured parity fixture `tests/fixtures/composer_driver_parity/` (which
records `induced_move_stop` from `capture.py:202`).

**The fix changes no current key value**, by construction: a predicate
containing neither `_` nor `%` is returned unchanged. Verified live over every
measured derived key:

```
['damp','oscillate','overshoot'] old='induced_damp_oscillate_overshoot' new=... identical=True
['move','stop']                  old='induced_move_stop'                new=... identical=True
['detect','pairwise','type']     old='induced_detect_pairwise_type'     new=... identical=True
```

---

## 5. AR2 / AR4 — the bars, live, after the fix

All run in the worktree, against the engine built from this branch's own source
(`sha256 8963fb4d…`, `_native.abi3.so` == `target/release/libsubstrate_rs.so`,
verified by `sha256sum`; `domains/engine_provenance.py` reports
`engine 8963fb4dccaa`; the list/tuple coherence probe prints
`[1, 2, 3] (1, 2, 3) True`).

| bar | before | after |
|---|---|---|
| **AR2.1** headline: k-shape covers k+1 observation | `residual` / `covered_by=None` | **`recognized` / `ms_buyer_is_a_lot_seller`** |
| **AR2.2** negative control: disjoint `Concept{name,definition}` | `residual` | `residual` (unchanged — not spuriously recognised) |
| **AR2.3** subset control: `TradeRecord{buyer,lot}`, `seller` absent | `residual` | `residual` (superset-tolerant only) |
| **AR2.4** shared `Covers` unchanged | `False` on the length-mismatched pair | `False` — and `CoversOpen` `True` on the same pair, `False` with the roles reversed |
| **AR2.5** rung 4 still grows | mints on a novel predicate set | mints `ms_is_a_sensor_value` alongside `ms_buyer_is_a_lot_seller` |
| **AR4.1** key collision | `induced_a_b_c` == `induced_a_b_c` | `induced_a%5fb_c` ≠ `induced_a_b%5fc` |
| **AR4.3** no key churn | — | every measured derived key byte-identical (§4.4) |

---

## 6. AR5 — regression, paired lists not counts

### 6.1 Rust (`cargo test --release --lib`, this worktree, same engine env)

**This crate's test binary is not deterministic under parallelism at
`cf774d3`, before any change** — reported rather than dismissed, because a
count would have hidden it:

| run | mode | result | failing node ids |
|---|---|---|---|
| BEFORE (stashed to `cf774d3` source) | default (parallel) | 749 passed / 1 failed | `shape_decode::dim_infer_tests::d_red_identical_arguments_collapse_to_one` |
| BEFORE | `--test-threads=1` | 749 passed / 1 failed | `framebuffer::tests::seqlock_read_races_writer_and_stays_honest` |
| BEFORE | module alone, parallel | 19 passed / 3 failed | `d_codebook_growth_is_seen_by_the_encoder`, `d_green_different_goals_are_seven_distinct`, `d_sweep_distinct_tracks_its_axis` |
| AFTER | default (parallel), run 1 | 755 passed / 3 failed | `d_green_different_goals_are_seven_distinct`, `d_red_identical_arguments_collapse_to_one`, `d_sweep_distinct_tracks_its_axis` |
| AFTER | default (parallel), run 2 | 756 passed / 2 failed | `d_codebook_growth_is_seen_by_the_encoder`, `d_sweep_distinct_tracks_its_axis` |
| **AFTER** | **`--test-threads=1`** | **758 passed / 0 failed** | — |

Reading, stated honestly: `shape_decode::dim_infer_tests` shares a global
recording site and fails a varying 2-3 of its 22 tests under parallelism **at
the unchanged baseline, with the module run alone** — so the parallel-mode reds
are not this rung's. `framebuffer::tests::seqlock_read_races_writer_and_stays_honest`
is a self-documented racy test. **In the deterministic mode the suite is green
before and after**, and `d_red_identical_arguments_collapse_to_one` passes when
run `--exact` at baseline, confirming it is schedule-dependent, not a real red.

`758 = 750 + 8`: the eight new `CoversOpen` unit tests, all green
(`covers_open_accepts_a_superset_instance`,
`covers_open_still_accepts_an_exact_arity_instance`,
`covers_open_refuses_a_subset_instance`,
`covers_open_refuses_a_disjoint_instance`,
`covers_open_keeps_relations_positional`,
`covers_open_matching_is_injective`,
`covers_open_delegates_non_list_containers_verbatim`,
`covers_open_term_round_trips_through_json`).

### 6.2 Python — 16 files, both trees, same day, same command

Files: every suite the meta-shape rung's own RESULTS names as its gate set that
is not a 39-minute outlier, plus the `induce_concern`/`CapabilityAxis`/shape-
decode suites and the `Covers`-Term source audit —
`test_analogical_shape_math_migrated`, `test_axis_mint_novelty`,
`test_composer_driver_migrated`, `test_transform_decode_migrated`,
`test_dimension_inference_migrated`, `test_character_composition_migrated`,
`test_mechanism_transfer_migrated`, `test_analogical_relative_ranking`,
`test_reframing_proposer`, `test_seed_guard_migrated`,
`test_self_process_introspection`, `test_teacher_dispatch`,
`test_teacher_dispatch_native_migrated`, `test_compilation_cycle`,
`test_structured_find`, `test_grounding_guard`.

|  | BEFORE (`/home/matt/ocelot-msak-baseline`, `cf774d3`) | AFTER (this branch) |
|---|---|---|
| result | 6 failed / 215 passed (303.67s) | 6 failed / 215 passed (311.52s) |

**The failing node ids — identical sets, no substitutions:**

* `tests/test_composer_driver_migrated.py::test_ground_concern_dispatch_parity`
* `tests/test_composer_driver_migrated.py::test_question_driver_parity`
* `tests/test_self_process_introspection.py::test_honest_floor_preserved_for_genuine_gap`
* `tests/test_structured_find.py::test_pos_and_governance_stamped_on_directive`
* `tests/test_structured_find.py::test_structured_comprehension_separates_target_and_constraint`
* `tests/test_structured_find.py::test_structured_find_gate_end_to_end`

`tests/test_engine_provenance_migrated.py` was dropped from the PAIRED set and
run in this worktree only: a freshly-created baseline worktree checks out 85
`.rs` files with mtimes newer than the committed `.so`, so the provenance guard
correctly refuses to measure there. It passes here (the engine was actually
built): `test_engine_provenance_migrated.py` + the new gate file = **16
passed**.

### 6.3 New gates added by this rung

`tests/test_meta_shape_arity_migrated.py` — **9 passed**. Six for Bug 1
(headline superset; disjoint negative control; strict-subset refusal; rung 4
still mints; `Covers` unchanged while `CoversOpen` accepts; and a source audit
asserting the seed carries zero `Covers` and exactly six `CoversOpen`, so no
rung is left arity-exact while its neighbours are not) and three for Bug 2
(injectivity including the pair a doubling scheme would collide on; value
preservation over every measured derived key; and the key read back through
`induce_concern` itself rather than a re-implementation of the join).

---

## 7. What this rung did NOT do, and what a follow-on would need

1. **The `ms_` name collision (§4.3) is measured and unfixed** — 23 reachable
   pairs, the fix named (`pred_key` attr + a structural mint guard), the hazard
   named (legacy `MetaShape` nodes without `pred_key` would re-mint on a
   checkpoint resume). This is the single highest-value follow-on in the
   document.
2. **`CoversOpen` is not applied to the other two `Covers` seeds.**
   `seeds/prog_chunk_growth.json` (4 guards) is
   `PROGRAM_SYNTHESIS_CHUNK_EQUIVALENCE_RESULTS.md`'s residual #8 — the same
   `covers_value` equal-length root cause, one grain over — and the Term it
   needs now exists. **But it is NOT obviously the right semantics there**, and
   this document declines to claim it is: at the chunk grain the arity
   difference is a different STATEMENT COUNT, and a program with an extra
   statement may genuinely mean something else, unlike an item with an extra
   annotation. That is an unmeasured question, not a queued patch.
3. **Refinement under a recognised shape** (§3.4): the ladder cannot mint a
   subtype of a shape that already covers an observation. Named, not built.
4. **Nothing in spike §5/§8** — the `ShapeRole` declaration, the `scope` field,
   a uniform find-or-create on mint — was started.

---

## 8. Reproduce

```bash
# AR0 / AR2.1-2.3 (the headline, one script; before the fix the third line
# reads `residual None`)
PYTHONPATH=runners/dsl/python:. OZMA_SEED_PERSIST_DISABLED=1 python3 -c "
from substrate.world_adapter import WorldAdapter
from substrate.seed_loader import manifest_for
from domains.meta_shape import observe
wa = WorldAdapter()
for seed in ('shape_vocabulary','meta_shape_growth'):
    wa.inner.load_seed_manifest(manifest_for(seed), wa.agent)
observe(wa,'TradeRecord',{'buyer':'alice','seller':'bob','lot':'7'})
observe(wa,'TradeRecord',{'buyer':'carol','seller':'dave','lot':'9'})
observe(wa,'TradeRecord',{'buyer':'gary','seller':'hank','lot':'13','note':'anything'})
r=[wa.s.node(n)['attrs'] for n in wa.s.nodes('ShapeObservation')][-1]
print(r.get('status'), r.get('covered_by'))"

# AR3.1 / §4.3 — the two prevalence measurements
#   (the AST scan and the x_y-in-vocabulary test are in this doc's §4.1/§4.3;
#    both are pure read-only scans over *.py and seeds/*.json)

# the gates
PYTHONPATH=runners/dsl/python:. OZMA_SEED_PERSIST_DISABLED=1 \
  python3 -m pytest tests/test_meta_shape_arity_migrated.py -q

# the engine (this rung changes Rust — the ONLY sanctioned build)
PATH=/home/matt/.cargo/bin:$PATH \
RUSTFLAGS="-L /home/linuxbrew/.linuxbrew/lib -C link-arg=-lpython3.13" \
LD_LIBRARY_PATH=/home/linuxbrew/.linuxbrew/lib:$LD_LIBRARY_PATH \
  bash scripts/engine_build.sh
```

---

## 9. The four sentences a reviewer should take away

1. **The container trade is per-LEVEL, not per-container** — a signature is a
   SET of POSITIONAL relations, and asking each level for its own semantics
   gets WILD *and* residual *and* open arity for the price of one delegating
   function.
2. **The engine already agreed**: `shape_decode::covers_relation` has always
   read relation sets with open arity; the meta-shape whole-signature guard was
   the outlier, so this is a consistency repair, not a new semantics.
3. **The fix costs a real thing and the doc says which**: strict-superset
   subtypes are now recognised rather than minted, which is the Occam ladder's
   own rule applied honestly.
4. **The measurement moved the target**: the reported key collision is
   unreachable (0/61) and the unreported twin is reachable 23 ways — which is
   the argument for measuring prevalence before sizing a fix, and for saying so
   when the measurement disagrees with the report that prompted the rung.
