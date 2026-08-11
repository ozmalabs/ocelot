# ARC 6 — THE `Lit` WIRE FIX

**Date:** 2026-08-03
**Worktree:** `/home/matt/arc6-lit-wire/research/experiments/gamma-substrate` (detached at `b29ac875ec`)
**Bars:** `PROGRAM_SYNTHESIS_ARC6_PREREG.md` amendment **A8**, LW1–LW6.
**Artifacts:** `results/arc6_lit_wire.json`, `results/arc6_verdict_litwire_arm{A,A_rebuild,B,C}.json`,
`results/arc6_full_sweep_litwire_arm{A,C}.json`.

**Engines** (A1.1 — all three archived out of tree in `~/ozma-engine-archive/`):

| arm | engine sha256 | what it is |
|---|---|---|
| A | `8311d4356082acf4f70fab61a6e943d3dcecbd404d6e90c4f72ccc9486936df0` | the shipped baseline |
| A′ | `8941a4d3da1fe92058a8ff1afccd2f599ff184ed803ed29c0a554dbb7ab9df89` | UNMODIFIED HEAD Rust source, rebuilt in this worktree — the rebuild-alone control |
| B, C | `4a9a492936bbbff21e7b25f8f31ec85b128c9b7ed74301365067f3fbaac22532` | the fix |

---

## 0. Two premise corrections, both load-bearing, both the author's to own

### 0.1 A8 says "seed files never pass through `pyobj_to_json`". They do.

A8 bounds the blast radius with this sentence:

> A bare JSON array must keep meaning `Value::Tuple` — every seed-resident
> `Lit` array literal depends on it, and **seed files never pass through
> `pyobj_to_json`**, so they must be byte-unaffected.

The premise is false. `domains/doom_operate.py:34` is
`wa.inner.load_seed_manifest(json.load(open(SEED_PATH)), None)`, and
`load_seed_manifest` is `pyobj_to_json` (`py.rs:1296`). `substrate/boot_all.py`
does the same for every booted seed. Measured: **68 array-valued `Lit`s across
21 files in `seeds/*.json`**.

So the design as literally worded — "preserve the Python object's actual type at
encode" applied to `pyobj_to_json` — would have retyped all 68 from `Tuple` to
`List`, which is exactly what **LW2 forbids**. The two clauses of A8's design
paragraph are in direct contradiction the moment the false premise is removed.

**The requirement is honoured by CHANNEL, not by file**, which is the same
constraint stated in terms that survive the correction:

* a Term handed over for **evaluation** is Python-originated → type-faithful;
* a Term installed as **graph data** (seed manifest, rule, production, concept
  definition, checkpoint) is the persisted wire form, where a bare array means
  `Tuple` → untouched, byte for byte.

Six entry points move to the faithful encoder — `evaluate`, `relax_to_fixpoint`,
`search`, `shape_of_term`, `add_shape_node_for_term`, `add_term_subgraph`.
Eight keep the legacy encoder verbatim — `load_seed_manifest`, `add_rule`,
`import_rules`, `add_production`, `define_concept`, `graph_from_dict`,
`graph_diff`, and the `decode` free function (which is *by definition* the
reader of the persisted wire form, where a bare array means `Tuple`).

### 0.2 "Rebuilding HEAD's Rust source reproduces `8311d435…` byte-for-byte" — not here.

Measured: in this worktree, a release build of pristine HEAD source produces
**`8941a4d3…`**, differing from the archived baseline in **259,213 bytes**, with

* `git status runners/` empty (the source really is pristine),
* an **identical** `Cargo.lock` (byte-for-byte `diff`),
* the same `rustc 1.95.0 (59807616e)`, `LLD 22.1.2`, `GCC 16.1.1`,
* the same size (8,513,392 bytes) and **no worktree path embedded in either
  binary** (only cargo-registry paths, 68 in each).

The pruning-fix rung's byte-for-byte reproduction was real *in its own worktree*
— `/home/matt/arc6-pruning-fix/.../target/release/libsubstrate_rs.so` still
hashes `8311d435…` today. **Byte-reproducibility of this crate is therefore
worktree-dependent and is not a usable identity check.** Recorded because a
future rung told "the build is deterministic, so a sha mismatch means you
changed something" would misread a clean tree as a dirty one.

The consequence for A1.2 is handled by measurement rather than by assumption:
arm **A′** runs baseline code on `8941a4d3` and is compared to arm A on
`8311d435`. Any move there is rebuild noise; it bounds what `B − A` can be
attributed to.

---

## 1. The defect, read before it was fixed

`Lit`'s value is decoded by `persist::decode_value` (`jsonio.rs:1141,1208`), and
that function's bare-array case is `Value::Tuple`. `pyobj_to_json`
(`py.rs:983`) round-trips the whole Term dict through Python's `json.dumps`.
**JSON has one array type.** So a Python `list` and a Python `tuple` in a `Lit`
arrive identically.

Confirmed live on the baseline binary before any change:

| `Lit` value written in Python | arrives as |
|---|---|
| `[1, 2]` | `(1, 2)` — **tuple** |
| `(1, 2)` | `(1, 2)` — tuple |
| `{"__list__": [1, 2]}` | `[1, 2]` — list |
| `{"__tuple__": [1, 2]}` | `(1, 2)` — tuple |

The encode path **is** where the loss happens, and the shipped tagged form
already survives it. The design's mechanism is therefore correct; only its
blast-radius justification needed replacing (§0.1).

---

## 2. The fix

`runners/dsl/src/py.rs`, +186/−8, one new function and six one-line call-site
changes. Zero `domains/`, zero `seeds/`, zero changes to any existing test.

`pyobj_to_json_term(py, obj, mode)` walks the Python object in three modes:

* **`Structural`** — Term structure. Arrays stay arrays (they are children
  lists), and a dict whose `type` is `"Lit"` descends into its `value` in
  `Value` mode. This is what keeps `{"type":"And","clauses":[…]}` parsing.
* **`Value`** — a `Lit`'s value. `list` → `{"__list__": …}`, `tuple` →
  `{"__tuple__": …}`, `set` → `{"__set__": …}`, `frozenset` → `{"__fset__": …}`.
* **`Verbatim`** — a dict already carrying a wire tag is emitted as-is and not
  re-tagged. This is what makes `_wire_rows`' output and the plain path
  *identical* rather than merely *equivalent*.

**Every leaf the walker does not handle natively is delegated to the untouched
`pyobj_to_json`**, so pre-existing behaviour is preserved exactly rather than
widened: `bytes` still raises `TypeError`, `NaN`/`Infinity` still raise
`ValueError`, `2**70` still degrades to a float, and an int-keyed dict is still
stringified by `json.dumps`' own rules. Pinned in
`test_lw1_unwireable_values_fail_exactly_as_before`.

**A bare JSON array still decodes as `Value::Tuple`.** Nothing in `persist.rs`
was touched. What changed is that a Python `list` on the evaluation wire is no
longer *written* as a bare array.

---

## 3. LW1 — types survive the wire · **PASS**

Both directions, live, on every entry point that **has** a readout. Each block
carries its own **capability control** — the engine's shipped tagged form, which
resolves the list/tuple distinction on the *pre-fix* binary too. A7's standing
rule is why: a gate that only asserted "a list arrives as a list" would pass
just as happily on a channel that had silently turned everything into a list.

| path | probe | arm A `8311d435` | arm B/C `4a9a4929` |
|---|---|---|---|
| `evaluate` | Python `list` | `tuple` | **`list`** |
| `evaluate` | Python `tuple` | `tuple` | `tuple` |
| `evaluate` | *capability* `{"__list__":…}` | `list` | `list` |
| `evaluate` | *capability* `{"__tuple__":…}` | `tuple` | `tuple` |
| `add_term_subgraph` | Python `list` | `tuple` | **`list`** |
| `add_term_subgraph` | Python `tuple` | `tuple` | `tuple` |
| `add_term_subgraph` | *capability* tagged | `list` / `tuple` | `list` / `tuple` |
| `search` | Python `list` | `Value::Tuple` | **NOT `Value::Tuple`** |
| `search` | Python `tuple` | `Value::Tuple` | `Value::Tuple` |
| `search` | *capability* tagged | NOT-Tuple / Tuple | NOT-Tuple / Tuple |

The capability rows resolve the distinction on **both** binaries, so the arm-A
column is a reading of the wire and not of a blind channel. That is the exact
control A6 lacked.

Two paths are reported as **NO READOUT** rather than as passes:

* **`relax_to_fixpoint`** commits only `Value::Float`/`Value::Int` into its
  register (`_ => None` discards everything else, `py.rs`), so a `Lit` list can
  never reach a graph attr through it. Its capability row (a numeric `Lit`)
  *does* pass, which is how we know the probe is not simply broken. The four
  container rows return `KeyError: 'reg'` on **both** arms — a property of the
  path, not of the wire.
* **`shape_of_term`** and **`add_shape_node_for_term`** return a *shape*, which
  cannot express a `Lit`'s value type. What is observable is **which encoder the
  path uses**: a Python `set` in a `Lit` raises `TypeError: Object of type set is
  not JSON serializable` on arm A and encodes cleanly on arm B/C, on all four
  wired paths. That differential is the evidence they are wired; the list/tuple
  behaviour of the encoder itself is established on the paths that do have a
  readout.

## 4. LW2 — file-resident arrays are unchanged · **PASS**

Measured end to end against **real seeds**, not reasoned: `json.load(seed)` →
`load_seed_manifest` → `export_rules`, which re-emits every installed rule
through `persist::encode_value`, so a `Value::Tuple` returns tagged `__tuple__`
and a `Value::List` returns tagged `__list__`. That readout distinguishes the
two **by construction** — it is the capability control for this bar.

| | arm A `8311d435` | arm B/C `4a9a4929` |
|---|---|---|
| seeds carrying array-valued `Lit`s | 21 | 21 |
| file-resident array `Lit`s | 68 | 68 |
| exported `__tuple__` | **38** | **38** |
| exported `__list__` | **0** | **0** |
| exported bare arrays | 0 | 0 |

**Byte-identical between arms.** Seeds are untouched.

The seed loader is not the only data-channel caller, so the separation is pinned
directly as well: `test_lw2_the_data_channel_is_still_the_legacy_encoder`
installs the *same* bare array through `load_seed_manifest` (→ `__tuple__`) and
evaluates it through `evaluate` (→ `list`) in one gate. A later change that
makes the data channel faithful goes red instead of silently retyping 68 seed
literals.

## 5. LW3 — `_wire_rows` is now redundant · **PASS** (and it is NOT deleted)

Proved, not assumed, over the whole MBPP corpus: every spec's rows were sent
through **both** `_wire_rows(rows)` and plain `rows`, and the engine's readback
compared.

| | specs | rows | mismatches | equivalent |
|---|---|---|---|---|
| arm A `8311d435` | 420 | 1,299 | **196** | **no** |
| arm B/C `4a9a4929` | 420 | 1,299 | **0** | **yes** |

**The 196 is the capability control.** The comparison demonstrably separates the
two paths — on the pre-fix engine it found 196 specs where `_wire_rows` was doing
real work (e.g. task 2, whose `frozenset` output the plain path could not put on
the wire at all: `TypeError: Object of type frozenset is not JSON serializable`).
On the fixed engine the same comparison finds zero. That is a measured null, not
a dead instrument.

Five specs (**124, 237, 590, 758, 779**) raise the *same* exception on both
paths — `complex` values and tuple dict keys, which neither encoder can carry.
They are equivalent, listed rather than hidden, and are a pre-existing wire
limit this rung did not introduce.

`_wire_rows` and `_wire` are left in place, per A8, and
`test_lw3_wire_rows_is_not_deleted_in_this_rung` pins that.

## 6. LW4 — no regression · **PASS**

| | arm A `8311d435` | arm A′ `8941a4d3` | arm B `4a9a4929` | arm C `4a9a4929` |
|---|---|---|---|---|
| code | baseline | baseline | baseline | this rung |
| pass ids | **48** | **48** | **48** | **48** |
| accepted ids | 95 | 95 | 95 | 95 |
| outcome hash | `aa8896089d…` | `aa8896089d…` | `aa8896089d…` | `aa8896089d…` |
| determinism (2 runs) | identical | identical | identical | identical |

`lost_pass = []`, `lost_accepted = []`. `per_task` is **byte-identical** between
arms A and B.

**On A1.2, and this is the part that needed a real control.** The intervention
here **is** the engine, so `C − B` is empty *by construction* — arm C adds one
test file and no `domains/`/`seeds/` change, and this battery does not read
`tests/`. The claimable comparison is therefore `B − A`, which A1.2 would
normally discount as "what the rebuild did". Arm **A′** is what separates them:
baseline code on a binary rebuilt from **unmodified HEAD source**, differing from
arm A's binary in **259,213 bytes**, moves **nothing** — `A′ − A = ∅` on pass
ids, accepted ids, and outcome hash. So `B − A = ∅` is a **measured null across a
changed binary**, not an artefact of a dead instrument.

**`accept_requires_list_tuple_collapse` stays `[]` and the 12 named
collapse-accepts stay rejected**, by the strongest available argument: arm C's
`per_task` is byte-identical to arm A's, so *every* id keeps exactly the
acceptance it had at the baseline the pruning-fix rung measured
(`results/arc6_pruning_fix_collapse_check.json`). This rung moved acceptance by
zero. On the literal reading, all 12 remain in `accepted_ids` — the state
recorded and explained in A4, unchanged here.

The four named suites are green together, **129 passed**:
`test_arc6_valuelayer_migrated` (35), `test_goal_residual_migrated` (31),
`test_arc6_tier0_migrated`, `test_synth_enumerate_migrated`, plus the 12 new
`test_arc6_lit_wire_migrated` gates.

**Two gates were repointed, and both pin the exact behaviour A8 asked to change.**

1. `test_arc6_tier0_migrated::test_the_bare_lit_wire_is_the_thing_that_was_lossy`
   **pinned the defect** (`assert ev(Lit [1,2]) == (1,2)`). Repointed to
   `..._is_no_longer_lossy`, keeping both directions: the **bare** wire now
   SOLVES the map spec at `tested = 25, distinct = 17` — arm A's own figures,
   with no `_wire_rows` at all — while the tuple-declared spec is **still
   REFUSED**. That pairing is the whole rung in one gate.
2. `test_goal_residual_migrated::test_gr4_…` asserted the engine short sha
   *equals* `8311d4356082`. Widened to an **allowlist** with `4a9a492936bb`
   **added, not substituted**, after measuring the pass ids identical on both
   binaries. Prereg §6 keeps it an allowlist and never a wildcard.

A third failure, `test_no_python_decision_was_added`, was **environmental and is
a standing instrument property**: the tree-wide sweep itself writes
`seeds/metonymy_patterns.json` and creates `seeds/acquired/`, so this gate's
colour depends on run ordering. Restored with `git checkout --`; no seed or
domain file is changed by this rung.

## 7. LW5 — the paired sweep · **PASS**

Both arms run in **this** worktree, same instrument
(`scripts/arc6_valuelayer_sweep.py`, the `--confcutdir` one — **never**
`failure_baseline_sweep.py`), same 6 workers, same 420 s timeout, same symlinked
`data/` and `results/run*_checkpoints`.

| | arm A `8311d435` | arm C `4a9a4929` | Δ |
|---|---|---|---|
| files | 947 | 948 (+ the new gate file) | +1 |
| red nodes | **151** | **157** | **+6** |
| RED files | 85 | 88 | +3 |
| GREEN | 850 | 850 | 0 |
| NOT_ESTABLISHED | 10 | 8 | −2 |

For reference, the frozen `results/arc6_full_sweep_armC.json` is **162 nodes / 88
RED files**; HEAD already contains the pruning-fix's five fixed nodes, which is
why arm A measures 151 here. The diff below is on **node ids**, unambiguous
under either counting.

**8 new red nodes, 2 fixed. Every new red classified. Unexplained bucket EMPTY.**

| # | node | class |
|---|---|---|
| 1–3 | `test_editop_dialect_terms::test_list_drop_{removes_the_element_at_index, negative_index_counts_from_end, out_of_range_is_a_mechanical_noop}` | **type-blind test now correctly stricter** |
| 4 | `test_bigville_world_migrated::test_scope_gating_cost_is_flat_in_the_out_of_scope_world` | **pre-existing** (non-deterministic on both binaries) |
| 5 | `test_lowercase_primer::test_each_construction_reads_as_itself` | **pre-existing** (PYTHONHASHSEED) |
| 6 | `test_run79_migrated::test_stage_prep_leaves_seed_md5_unchanged` | **environmental** (concurrent write, shared tree) |
| 7–8 | `test_bigville_speech_migrated::test_runners_dsl_untouched_zero_new_rust`, `test_doom_emotion_narration_migrated::test_term_rs_and_runners_dsl_diff_empty` | **scope guard from another rung** |

**1–3, type-blind.** Each passed a Python list in a `Lit` and asserted a *tuple*
back; the first justified it in its own message as *"Tuple-valued
(Value::Tuple), nested lists decode as nested tuples too"* — documenting the
collapse as if it were semantics. That was the wire, not `ListDrop`: measured
live with a capability control, `ListDrop` returns list→list and tuple→tuple,
and the tagged forms resolve identically on both binaries. **Repointed, 3 gates,
one file, one mechanism** — and each is now paired with its refuting direction,
so they are *stricter* than before. All 3 fail on `8311d435` and pass on
`4a9a4929`.

**4, pre-existing.** On the **baseline** engine, five reps of `_scope_cost` gave
`c_big` 72…113 — ratio **1.487** against the test's own **1.5** bar. The test is
unstable against its own threshold with no code change; the sweep's 1.615 is
inside that envelope under load.

**5, pre-existing.** `_perturb(…, seed=hash(c) % 1000)`, and `hash(str)` is
**PYTHONHASHSEED-randomised per process** — measured `hash('c') % 1000` =
437 / 871 / 649 / 699 / 756 across five processes. Non-deterministic by
construction, engine-independent; 25/25 passed on re-run.

**6, environmental.** `build_prep()` reads
`results/run78_checkpoints/prep.json` — **7,473,475 bytes**, symlinked into the
shared canonical tree, **mtime 2026-08-04 00:51**, inside the arm C sweep window
(which ended 00:57). A partial read of a file the other live session was
rewriting. Green 3/3 on re-run.

**7–8, and these fit none of A8's four buckets, so they are not force-fitted.**
Both assert `git diff runners/dsl` is **empty** — they guard the *zero-Rust cost
claim* of two other rungs. They fire on any engine-touching change, and A8 itself
registers "Engine rebuild expected". No behaviour changed. **Deliberately not
touched:** widening another rung's cost guard is the orchestrator's call, not
this rung's.

**The 2 fixed nodes are not credited to the fix.**
`test_engine_provenance_migrated::test_loaded_engine_is_a_build_of_THIS_TREES_rust_source`
was red in arm A only because `target/release/` held the patched build while the
installed `.so` was the baseline — my own artifact, the same trap the pruning-fix
rung hit. `test_rust_engine_ext_7b::test_attr_index_perf_beats_linear` is a
timing assertion (`≥3×` speedup) that failed under 6-worker load. Recorded so
`−2` is not read as `−2` of mine.

## 8. LW6 — the stop condition · **NOT TRIGGERED**

**8 new red nodes against a ~40-node bar, and none resisted classification.**
Re-pins total **five**, across three files, each with a named and separately
measured mechanism, and each paired with a refuting direction: three type-blind
`ListDrop` assertions, one gate that pinned the defect itself, one engine-sha
allowlist widened by addition. That is not a wave, and it is enumerated here
rather than summarised as a count.

## 9. What remains unfixed, named

- **The data channel is still lossy by design, and that is now a pinned
  decision rather than an accident.** A bare array in a seed, rule, production,
  concept or checkpoint still means `Value::Tuple`.
  `test_lw2_the_data_channel_is_still_the_legacy_encoder` fixes that in place, so
  a future "global" change goes red rather than retyping 68 seed literals.
- **`_wire_rows` is redundant but NOT deleted** (A8's instruction). Removing it
  is a separate, now-cheap rung.
- **A `Lit` value that is a NON-STRING-KEYED dict is still lossy.** The walker
  delegates such dicts wholesale to `json.dumps` rather than reimplementing its
  key-stringification rules, so containers nested inside them still collapse.
  Narrow, deliberate, and recorded.
- **`Substrate.search` has no termination guard.** A `search` whose `open` term
  does not shrink recurses until the process dies of stack overflow. **Pre-existing**
  — the baseline binary dumps core on the identical call with no `Lit` container
  in the term. Found while probing; not touched.
- **`relax_to_fixpoint` discards every non-numeric Value** (`_ => None`), so no
  container can reach a register through it. Not a wire defect; recorded because
  it is why LW1 has no readout there.
- **Byte-reproducibility of the engine is worktree-dependent** (§0.2). Within one
  worktree the build is deterministic (verified twice); across worktrees it is
  not. A sha mismatch is therefore not evidence of a dirty tree.
- **The tree-wide sweep mutates `seeds/`** — it rewrites `metonymy_patterns.json`
  and creates `acquired/`, which reds `test_no_python_decision_was_added`
  depending on ordering.
- Known-unfixed and untouched, as instructed: `sorted`-on-strings,
  `Eq(0.0, False)`, `inputs_json`.

## 10. What made me want to exceed scope, and did not

1. **Making the data channel faithful too.** It would delete the last asymmetry —
   and retype 68 seed-resident array literals. LW2 forbids it, and the seed
   loader is exactly the path A8 wrongly believed was not involved.
2. **Deleting `_wire_rows`.** Proven redundant; A8 says prove first, delete later.
3. **Widening the two other rungs' `runners/dsl`-untouched guards.** Their reds
   are correct. Not mine to widen.
4. **Fixing `search`'s unbounded recursion.** A real engine defect, found here,
   unrelated to the wire. Named, not bundled.
