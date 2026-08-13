# Automatic recognition of the evidence-accumulation generator — RESULTS

Prereg: `LOGODDS_DIMINFER_PREREG.md`, same worktree/branch, base
`main @ 5ccbe3b` ("Merge logodds-generator: causal-strength dimension + item
4 graded Hebbian reweighting, GO"). Worktree
`/home/matt/ozmadev/ocelot-worktrees/logodds-diminfer`, branch
`logodds-diminfer`.

**Verdict, up front.** Both decision claims registered in the PREREG held.
**`TimeInfer`, not `DimInfer`**, is the correct existing mechanism —
confirmed live, not merely by source-reading. `LOGODDS_GENERATOR_RESULTS.md`
§7.1's named gap is closed for the case it actually names (a PER-DIRECTION
axis, exactly the shape that seed's own PER-DIRECTION convention already
uses): a pure confirm-only reinforcement run is now automatically recognized
and minted, with **zero pre-declared generator anywhere in the graph**
(`seeds/inference_knowledge.json` is never loaded by any test in this rung).
**Zero new Rust** — `git diff --stat main -- '*.rs'` is empty. One new seed
(`seeds/evidence_axis_infer.json`, two rules + one codebook part) does the
whole job, mirroring two already-landed idioms (`f16_sample_axis_margins`'s
window accumulator and `sd_recognize_dim`'s `add_node_if_absent` mint)
exactly. **The registered null also held**: the genuinely coupled 2-D
`(confirm, disconfirm)` trajectory is not recognized as one dimension by
either mechanism, and this is confirmed live as a real, honest scope
boundary — not a defect, and not patched around.

---

## 1. The DimInfer-vs-TimeInfer decision — confirmed live, both claims

### Claim A: `DimInfer`'s rung-2 loop is architecturally unreached for a
single-relation delta

`tests/test_evidence_axis_infer.py::test_dim_infer_rung1_already_explains_a_
single_relation_delta_no_generator_needed` probes `TransformDecode` (rung 1,
**no generator applied at all** — `build_candidate` called directly on the
part's raw signature) on a single-relation goal `("m", 3, 1)` against a held
base `("m", 0, 0)`:

```
TransformDecode (rung 1, NO generator) on a single-relation 2-slot delta:
explained=True transforms=({'dim': 1, 'kind': 'shift', 'delta': 3},
                            {'dim': 2, 'kind': 'shift', 'delta': 1})
```

`explained=True` with a plain per-dimension `transforms` list and **no
`DimensionGenerator` ever consulted** — confirming, live, that
`build_candidate`'s tier-1 "uniform delta" check (`shape_decode.rs:1833
-1930`) is vacuously satisfied for a signature made of exactly one relation
(there is only one aligned pair, so "uniform across all pairs" is trivially
true for any delta on any slot). Per the sd loop's own Occam ordering
(`sd_recognize` → `sd_transform_decode` → `sd_infer_dimension` →
`sd_mint_quantum`), rung 2 (`DimInfer`) is never reached for this
representation — not a defect in `DimInfer`, but a structural consequence
of the single-relation shape a Coactivation ledger's current
`(confirm, disconfirm)` state naturally has.

### Claim B: `TimeInfer` explains the pure-axis case; correctly refuses the
coupled case

`tests/test_evidence_axis_infer.py::test_coupled_2d_trajectory_is_not_
explained_by_time_infer` feeds `TimeInfer` the EXACT trajectory
`test_can_native_reimplementation.py::test_evidence_counters_are_real_
integers_stepping_across_ticks` measures live — `(0,0)→(1,0)→(2,0)→(3,0)→
(3,1)` — as a raw 2-D sequence:

```
coupled 2-D trajectory [(0,0),(1,0),(2,0),(3,0),(3,1)]: TimeInfer(explained)=False
```

`explained=False`, exactly as predicted: the per-tick offset changes
direction (`(1,0)` for three steps, then `(0,1)`), which is neither a single
constant generator (`eval_time_infer`'s order-1 exact-equality path,
`shape_decode.rs:3645-3665`) nor a regular finite-difference stream (the
order-N fallback, `order_n_translate_verdict` — checked directly in §3
below, not merely asserted).

---

## 2. The live demonstration — all four registered scenarios, real numbers

`tests/test_evidence_axis_infer.py`, run via `PYTHONPATH=".:runners/dsl/
python" python3 -m pytest tests/test_evidence_axis_infer.py -q -s`. **None
of these tests load `seeds/inference_knowledge.json`** — the pre-declared
`logodds_evidence` `DimensionGenerator`/`latent:causal_strength`
`LatentDimension` from that seed are simply absent from every graph here.

### (a) Zero-mint-once-recognized / correct-mint-on-recurrence

```
tick 1: evidence_confirm=1 window=(1,)             inferred_gens=0 inferred_lds=0
tick 2: evidence_confirm=2 window=(1, 2)            inferred_gens=0 inferred_lds=0
tick 3: evidence_confirm=3 window=(1, 2, 3)         inferred_gens=1 inferred_lds=1
tick 4: evidence_confirm=4 window=(1, 2, 3, 4)      inferred_gens=1 inferred_lds=1
tick 5: evidence_confirm=5 window=(1, 2, 3, 4, 5)   inferred_gens=1 inferred_lds=1

MINT: tick=3 window_at_mint=(1, 2, 3)
  generator={'offset': (1,), 'kind': 'translate', 'name': 'logodds_evidence_inferred',
             'source': 'time_infer', 'params': (1,), 'coord_dims': (1,)}
  latent_dim={'generator': 'logodds_evidence_inferred', 'name': 'latent:causal_strength_inferred',
              'source': 'time_infer', 'k': 3}

zero-mint-once-recognized confirmed: 1 generator(s), 1 dimension(s) after 3 further confirming ticks
```

Recognition fires the instant the window reaches its 3-sample minimum
(`Gte(Count(window), 3)`), mints `DimensionGenerator{kind:"translate",
coord_dims:(1,), offset:(1,)}` — **auto-discovered from raw data**, matching
the already-declared `logodds_evidence` generator's own semantics
(`LOGODDS_GENERATOR_RESULTS.md` §1) byte-for-byte on `kind`/`offset`, though
this graph never held that declaration — plus `LatentDimension{name:
"latent:causal_strength_inferred"}`, and a `has_inferred_axis` edge. Three
further confirming ticks (the window keeps satisfying `TimeInfer`'s orbit
test every time) do **not** re-mint: the `has_inferred_axis`-edge guard
(mirroring `sd_recognize_dim`'s `has_transform`-edge guard exactly) holds
node/edge counts flat at 1/1.

### (b) No-spurious-mint on a genuinely irregular trajectory

```
interleaved window: (1, 1, 2, 3, 4) (a genuine early disconfirming observation must show as a flat step)
no-spurious-mint confirmed: interleaved trajectory recognized by nothing, minted nothing
```

A genuine disconfirming observation lands immediately after the mint tick
(`b`'s sign flips — the same idiom `test_evidence_counters_are_real_
integers_stepping_across_ticks` uses), deliberately early so no clean
3-sample confirming prefix exists before the irregularity — test (a) already
shows recognition fires the instant 3 samples accumulate, so a later
irregularity would be moot; a genuine negative case has to poison the window
from the start. The window sampler is gated on a REAL co-activation
observation (`Not(Eq(a.state,0))`/`Not(Eq(b.state,0))`, the exact guard
`can_native_hebbian_reweight` itself uses), so it never samples a silent
tick — only genuine evidence events. The resulting window `(1,1,2,3,4)` has
first-pair delta `0` (the disconfirming tick leaves `confirm` flat):
`infer_translate_offset`'s zero-offset result is excluded as "no motion" by
`eval_time_infer`'s own construction (`shape_decode.rs:3606-3607`), and the
order-N finite-difference fallback never reaches a witnessed `>=2`-element
constant from this stream (traced by hand against `diff_pyramid`,
`shape_decode.rs:2832-2848`: offset stream `[0,1,1]` → level 1 `[1,0]` (not
equal) → level 2 `[-1]` (single element, `<2` — the loop breaks without ever
witnessing a constant) → `pyramid_order` returns `None`). Zero mints across
the full 5-observation run.

### (c) The registered null, demonstrated directly

Both halves of §1 above (Claims A and B), run as their own tests, are this
demonstration.

### (d) Composition with the existing Hebbian mechanism (item 4)

```
log_odds render: plain=1.6094 with_axis_infer=1.6094
inferred generator present alongside the render:
  {'offset': (1,), 'kind': 'translate', 'name': 'logodds_evidence_inferred', ...}
```

The EXISTING, byte-unchanged `_log_odds_term()`
(`Log(Div(Plus(confirm,1),Plus(disconfirm,1)))`) renders the **identical**
value (`1.6094`) whether `seeds/evidence_axis_infer.json` is loaded or not,
on the same 4-confirm/0-disconfirm scenario — confirmed by evaluating on two
independently-built substrates (`CAN_SEED` alone vs. `CAN_SEED +
AXIS_SEED`), not merely by inspection. `evidence_confirm`/
`evidence_disconfirm` land at `(4, 0)` in both, and no `log_odds`/`render`
key is ever written onto the node in either. On the `AXIS_SEED` graph
specifically, the inferred `DimensionGenerator` is confirmed present
alongside the unchanged render — additive graph data, not a parallel or
disconnected mechanism.

---

## 3. Where the design landed

### `seeds/evidence_axis_infer.json` (new, v1.0.0)

- One codebook `Part`: `EvidenceAxisSample{name, signature:"[[\"m\",0]]",
  dim_types:["pred","coord:v"]}` — the exact shape
  `seeds/f16_flight_path_control.json`'s `F16AxisSample` already uses (index
  0 = predicate, index 1 = the coordinate slot `TimeInfer` reads).
- `evidence_axis_sample_window`: mirrors `f16_sample_axis_margins` exactly
  — `Append`/`Count`/`IfThenElse`/`ListDrop` maintains a rolling
  `evidence_confirm_window` Tuple attr on the `Coactivation` node, capped at
  6 samples (an ENGINEERING buffer bound, not a borrowed human perceptual
  number — `CAN_SOLVER_THEORETICAL_LIMITS_RESEARCH.md` §5.3/§7's own
  caution, honored: 6 is sized only to hold a recognizable run plus enough
  of a poisoned run to demonstrate the null, the same sizing logic `f16`'s
  own cap uses). Gated on the SAME genuine-observation guard
  `can_native_hebbian_reweight` uses (`Not(Eq(a.state,0))`/
  `Not(Eq(b.state,0))`) — a sample is taken only on a real co-activation
  event, never a silent tick.
- `evidence_axis_infer`: mirrors `sd_recognize_dim` exactly —
  `TimeInfer(explained)==1` (checked directly on the `MapList`'d window,
  `codebook_type:"EvidenceAxisSample"`) plus a `Not(Exists has_inferred_axis
  edge)` guard mints `DimensionGenerator{name:"logodds_evidence_inferred",
  kind, coord_dims, params:[1], offset}` (all of `kind`/`coord_dims`/
  `offset` read directly off `TimeInfer`'s own field-selected output — no
  hand-picked values) + `LatentDimension{name:
  "latent:causal_strength_inferred", generator, k}` via `add_node_if_absent`
  (content-keyed dedup, `DEDUP_ADOPTION_SWEEP_RESULTS.md` v1.9.0 idiom) +
  the guarding edge.

Zero new Rust Terms: `TimeInfer` (existing) is the only Term this seed calls
beyond the ordinary `Attr`/`Plus`/`Gt`/`Gte`/`Eq`/`Not`/`And`/`Count`/
`Append`/`ListDrop`/`MapList`/`Vec`/`IfThenElse` arithmetic every other
CAN-native rule already uses.

### `tests/test_evidence_axis_infer.py` (new)

Five tests: the two positive/negative live demonstrations (§2a, §2b), the
two null-confirming direct probes (§1, Claims A and B), and the composition
check (§2d).

---

## 4. Regression

**Scoped CAN regression, one run, 75/75 passed** (the six pre-existing CAN
files + `can_native_reimplementation.py`'s 11 tests + this rung's 5 new
tests):

```
$ PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_can_belief_quantization.py tests/test_bigville_can_integration.py \
  tests/test_causal_attitude_networks.py tests/test_can_ops.py \
  tests/test_can_migration.py tests/test_can_crossover_point.py \
  tests/test_can_native_reimplementation.py tests/test_evidence_axis_infer.py -q
75 passed in 10.64s
```

**`DimInfer`/`TimeInfer` existing-generator suites — matched pre-existing
baseline exactly, measured both ways (worktree vs. the original checkout's
own dirty working tree, not assumed):**

```
$ PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_dimension_inference_migrated.py tests/test_dim_infer_args_migrated.py \
  tests/test_time_infer_migrated.py tests/test_generic_order_n_migrated.py -q
6 failed, 35 passed in 14.82s
```

The 6 failures are all in `tests/test_dim_infer_args_migrated.py`
(`test_calls_equals_the_invocation_counter`,
`test_the_headline_reproduces`, `test_the_novel_path_has_no_redundancy`,
`test_distinct_is_invariant_in_N_and_K`,
`test_I_is_the_seed_s_own_DimInfer_SITE_COUNT`,
`test_only_the_field_selector_varies_across_the_invocations`) — **confirmed
identical**, same failing-test-name list, running the SAME file directly on
the original repo checkout (which carries pre-existing uncommitted local
state unrelated to this branch: a modified `_native.abi3.so`/
`_native.build.json` and two unrelated Bigville files, present before this
worktree was ever created). This branch touches neither the Rust engine nor
any file `test_dim_infer_args_migrated.py` exercises — the 6 failures are a
pre-existing environment-conditional baseline, not introduced here.
`rotation90`/`scale2`/`modular` generator recognition
(`test_dimension_inference_migrated.py`, `test_time_infer_migrated.py`,
`test_generic_order_n_migrated.py`) — 35/35 passed, unaffected.

**No Rust build or `cargo test` was needed or run** — `git diff --stat main
-- '*.rs'` is empty; zero `.rs` files touched anywhere in this branch,
exactly as the PREREG's Claim A/B decision predicted.

---

## 5. What this build does NOT establish

1. **The coupled 2-D `(confirm, disconfirm)` trajectory is NOT automatically
   recognized as one dimension by anything built in this rung, and this is
   a deliberate, confirmed scope boundary, not a partial result.** Per §1,
   `DimInfer` cannot reach it (no residual survives rung 1 for a
   single-relation representation) and `TimeInfer` correctly refuses it (an
   event-conditional per-tick offset is neither a constant generator nor a
   regular finite-difference stream). This directly validates
   `LOGODDS_GENERATOR_RESULTS.md`'s own PER-DIRECTION tracking convention
   from a new angle: per-direction decomposition isn't just a modeling
   convenience, it is REQUIRED for either existing sd-loop mechanism to
   automatically infer anything at all.
2. **Only the `evidence_confirm` axis is wired.** `evidence_disconfirm`
   would need its own symmetric sampler/infer rule pair (the same shape,
   the SAME per-direction convention) — not built here, since no live
   scenario in this rung needed it to demonstrate the four registered
   behaviors, and building an unexercised symmetric pair would be padding,
   not rigor.
3. **The minted `DimensionGenerator{name:"logodds_evidence_inferred"}` is a
   SEPARATE node from `seeds/inference_knowledge.json`'s hand-declared
   `logodds_evidence`** (different `name`, so `add_node_if_absent`'s
   content-key never unifies them) — this rung does not attempt to
   reconcile an auto-inferred generator with a hand-declared one when both
   are present in the same graph (no test here loads both). They are
   structurally identical in `kind`/`coord_dims`/`offset` semantics but
   remain two distinct graph objects if co-present; unifying them (or
   deciding whether they should be) is unbuilt, unnamed-as-a-problem until
   now.
4. **The window-sampler's 6-sample cap and 3-sample minimum are engineering
   buffer choices, not derived from any formal bound** (per
   `CAN_SOLVER_THEORETICAL_LIMITS_RESEARCH.md` §5.3's own method-not-number
   distinction) — sized only to make the four registered demonstrations
   possible on the smallest graphs that exercise them, not optimized or
   claimed optimal for any real deployment scale.
5. **No test in this rung exercises `evidence_axis_infer.json` loaded
   ALONGSIDE `seeds/inference_knowledge.json`** — the "without the generator
   pre-declared" condition is achieved by never loading that seed at all in
   any test here, which is the cleanest test of automatic inference but
   leaves the CO-PRESENT case (residual #3 above) genuinely unexercised.
6. **This rung says nothing new about `can_ops.rs`, the old continuous CAN
   mechanism, or its real consumers** (`domains/insight_detection.py` et
   al.) — untouched, as scoped.

---

## 6. Reproduce

```bash
cd /home/matt/ozmadev/ocelot-worktrees/logodds-diminfer
git log --oneline -1 main   # 5ccbe3b, verified before branching

# The five new live demonstrations
PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_evidence_axis_infer.py -q -s

# Scoped CAN regression
PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_can_belief_quantization.py tests/test_bigville_can_integration.py \
  tests/test_causal_attitude_networks.py tests/test_can_ops.py \
  tests/test_can_migration.py tests/test_can_crossover_point.py \
  tests/test_can_native_reimplementation.py tests/test_evidence_axis_infer.py -q

# DimInfer/TimeInfer existing-generator suites (baseline-matched)
PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_dimension_inference_migrated.py tests/test_dim_infer_args_migrated.py \
  tests/test_time_infer_migrated.py tests/test_generic_order_n_migrated.py -q
```
