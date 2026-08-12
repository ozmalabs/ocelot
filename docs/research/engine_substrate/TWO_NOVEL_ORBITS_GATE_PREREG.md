# Two-novel-orbits gate — PREREG

**Status: PREREG. Registered before the test file was written.** Worktree
`/home/matt/ocelot-two-novel-orbits-gate`, branch to be created
`two-novel-orbits-gate`, from `main` at `c415a56` (`Merge red-test-triage: 458 -> 216
red node ids, …`, verified with `git log --oneline -1 main` immediately before
`git worktree add`). Engine `8963fb4dccaa`, coherence-probed (list/tuple identity
preserved and distinguishable) and `test_engine_provenance_migrated.py` green (10/10)
in this worktree before any file was touched. Results go in
`TWO_NOVEL_ORBITS_GATE_RESULTS.md`.

**Charter, quoted precisely, from `DEDUP_ADOPTION_SWEEP_RESULTS.md`:** *"the real
methodology gap this rung found — no existing test in the tree presents two novel
orbits to one graph, which is exactly why both the stall and the loop survived every
prior gate."* This rung closes that gap with a test file, not a fix — the engine is
already fixed (`seeds/shape_decode_loop.json` v1.9.0, commit `dcea7ad`, merged
`2b271bc`, both ancestors of `c415a56`). No Rust and no seed edits are expected;
deviation will be reported if either turns out to be necessary.

**Pre-registration honesty note:** the exact scenario numbers below were obtained by
running the DEDUP rung's own AR4.2.4 live-probe script (reproduced verbatim from
`DEDUP_ADOPTION_SWEEP_RESULTS.md` §8) against this worktree's engine *before* writing
this document, to make the bars concrete rather than aspirational — exactly the
discipline `DEDUP_ADOPTION_SWEEP_PREREG.md` itself used. The probe output is quoted in
AR1 below and the RESULTS doc must reproduce it via the committed test file, not via a
fresh ad hoc script.

---

## The two failure modes this gate exists to catch, restated precisely

From `DEDUP_ADOPTION_SWEEP_RESULTS.md` §4.2.1–4.2.3, both found only because that rung
happened to run three orbits in sequence against one booted graph — something no
committed test had done before:

1. **THE STALL (pre-fix, coarse-guard defect).** With the original
   `Not Exists a DimensionGenerator with kind == "linear"` guard, a second and third
   novel orbit reached **neither a generator nor a quantum** — `sd_mint_quantum` and
   `sd_dedup_existing` both require `Not gen_explained == 1`, which a `GenInfer`-explained
   observation already satisfies, so the observation terminated at `status == "decoded"`
   with nothing minted. Silently dropped, no error.
2. **THE LOOP (first fix attempt, before the termination-guard correction).** Swapping
   `add_node` for `add_node_if_absent` and deleting the coarse guard, with no per-observation
   termination guard added, caused `codebook_epoch` to run **1 → 20,001 in a single
   `run_rules` call** (87.4s wall-clock), because `AddNodeIfAbsent`'s found-branch sets no
   `progressed` flag but the rule's other effects (edge, epoch bump, status write) do, and
   `sd_redecode` re-arms the observation on the bumped epoch without clearing
   `gen_checked`/`gen_explained`, so the mint guard is satisfied again immediately.

Both defects are specifically about **what happens to the SECOND and THIRD novel
observation in one graph**, and both are invisible to any test that boots fresh per
orbit (which is every gate in `tests/test_gen_infer_migrated.py` today — its
`test_multi_held_out_mints_the_correct_DIFFERENT_generator_and_collapses` calls `_run`,
which calls `_boot`, fresh, per orbit).

---

## AR1 — the primary scenario, registered exactly

**Grain:** `DimensionGenerator` (linear generators) + `LatentDimension`, the two types
`DEDUP_ADOPTION_SWEEP_RESULTS.md` AR4.1/AR4.2 fixed, in `seeds/shape_decode_loop.json`.

**Fixture:** the DEDUP rung's own worked example, reproduced verbatim — asymmetric
L-tetromino `BASE`, `_lin(M)` applies a 2×2 integer matrix to it, `gen_infer_enabled=1`,
ONE booted graph, ONE `ShapeSignature("base_L")` held. Four orbits presented **in
sequence to the same graph**, each via its own `Observation` + `run_rules()` call
(mirroring how a real session accumulates observations one at a time, not one big
batch):

```
SHEAR_A  = [1, 0, 1, 1]   (genuinely novel — no held generator explains it)
SHEAR_B  = [1, 1, 0, 1]   (genuinely novel — different from SHEAR_A)
UNIMOD   = [2, 1, 1, 1]   (= SHEAR_A ∘ SHEAR_B — must be explained as COMPOSITION,
                            not minted as a third generator — Occam ladder)
SHEAR_A  (repeat)          (must recognize via the ALREADY-minted generator — this is
                            precisely what the load_generators name-shadowing bug broke:
                            §4.2.3 found a REPEAT of orbit 1 stopped being explainable
                            once a second same-named generator was minted)
```

**Already measured (this document's own probe, before it was written), reproduced
below verbatim — the RESULTS doc must match this exactly via the committed test:**

```
A  [1,0,1,1]  status=recognized_transformed  ep 0.0->1.0  dt=0.0069s  generators=[(1,0,1,1)]
B  [1,1,0,1]  status=recognized_transformed  ep 1.0->2.0  dt=0.0075s  generators=[(1,0,1,1),(1,1,0,1)]
U  [2,1,1,1]  status=recognized_transformed  ep 2.0->2.0  dt=0.0027s  generators=[(1,0,1,1),(1,1,0,1)]
A2 [1,0,1,1]  status=recognized_transformed  ep 2.0->2.0  dt=0.0006s  generators=[(1,0,1,1),(1,1,0,1)]
total wall: 0.018s

LatentDimension names: latent:genlin_[1,0,1,1]
                       latent:genlin_[1,0,1,1]+genlin_[1,1,0,1]
                       latent:genlin_[1,1,0,1]
generators: {'genlin_[1,0,1,1]': (1,0,1,1), 'genlin_[1,1,0,1]': (1,1,0,1)}
```

**This is the CORRECT, measured behaviour — 2 generators, not 3 — not the DEDUP
PREREG's original registered bar (which predicted 3 and was wrong, per its own RESULTS
§4.2.4 "A registered prediction was wrong and the outcome is better than it"). This
rung's bars are set to the measured shape, not the earlier wrong prediction, per this
task's own charter.**

## AR2 — the stall assertion, registered exactly

**Bar:** for every one of the four orbits above, the Observation's terminal `status` is
`"recognized_transformed"` — **never** `"decoded"` (the silent-drop terminus the
pre-fix coarse guard produced) and never any status with `residual` non-empty and no
`gen_minted`/`minted`/`has_transform` edge. Concretely, the test asserts
`status == "recognized_transformed"` after each `run_rules()` call, individually, not
just at the end — so a stall on orbit 2 or 3 (which would still let orbit 4 pass, since
by then the graph is in a different state) cannot hide behind a single end-of-scenario
check.

## AR3 — the loop assertion, registered exactly

**Bar:** a **real, checked upper bound**, not "it eventually returns":

* `codebook_epoch` after the full 4-orbit sequence is `<= baseline + 4` (measured: `+2`,
  one bump per genuine generator mint, zero for the composition and the repeat — the
  bound is set at 2× the measured value, not at the measured value itself, so the test
  is not brittle to a legitimate future rung adding one more epoch-bearing effect, while
  remaining **four orders of magnitude** below the pre-fix-attempt's measured 20,000-per-call
  blowup).
* Each individual `run_rules()` call completes in **under 3 seconds** wall-clock
  (measured: all four calls under 8ms; the bound is generous relative to CI jitter but
  is **29× smaller** than the measured 87.4s pre-fix-attempt blowup, so it cannot be
  satisfied by a regression to that state and still pass).
* The whole 4-orbit scenario completes in **under 10 seconds** total (measured: 18ms).

## AR4 — dedup-direction assertions (the fix's OTHER half, so this gate does not
just check growth)

**Bar:**
* Exactly **2** `DimensionGenerator{kind:"linear"}` nodes exist after all four orbits —
  not 3 (no spurious mint for the composed orbit) and not 1 (the pre-fix cap).
* The two generators' `matrix` attrs are `(1,0,1,1)` and `(1,1,0,1)` — the two
  genuinely-distinct maps, each present exactly once (content-keyed dedup working in
  both directions: novel mints, repeat doesn't re-mint).
* The two generators' `name` attrs are **distinct** (`genlin_[1,0,1,1]` /
  `genlin_[1,1,0,1]`) — this is the direct regression check for the
  `load_generators` name-shadowing bug (§4.2.3): under the pre-correction-2 state
  (base-shape-derived names), both would have collided on `genlin_base_L` and
  `load_generators`' last-write-wins would drop the first, which the orbit-4 REPEAT
  step is specifically placed to catch (it fails to re-explain SHEAR_A exactly when the
  first-minted generator has been shadowed).
* Exactly **3** distinct `LatentDimension` names exist (`latent:genlin_[1,0,1,1]`,
  `latent:genlin_[1,1,0,1]`, `latent:genlin_[1,0,1,1]+genlin_[1,1,0,1]`) — not 4 (the
  repeat must not mint a duplicate, AR4.1's fix) and not fewer (each real dimension must
  still be represented).

## AR5 — generalisation to a second grain: GO, registered scenario

**Candidates considered, and why `MetaShape` is ruled out up front:** the task names
`MetaShape` as a candidate "given how much work landed on that grain today."
`DEDUP_ADOPTION_SWEEP_RESULTS.md` AR5 already evaluated exactly this grain's dedup
defect (`MetaShapeMint`'s name collision, `shape_decode.rs:5749`) and returned
**NO-GO for that rung** because the fix needs a new Rust field (`pred_key`) the seed
layer cannot read today (`keys` on the Term's returned Dict is the *discriminative*
subset, not the full identity) — i.e. it is not a seed-level fix and is out of this
task's file scope (`runners/dsl/src/py.rs`/`term.rs` are explicitly excluded, and
`shape_decode.rs`'s `MetaShapeMint` return shape would need the same kind of change).
**Ruled out here for the same reason, without re-investigating**: a second grain that
needs a Rust field is not "cheap."

**Grain selected instead: `ShapeSignature` growth via `vq_grow_quantum`**
(`seeds/vision_sdloop.json`, `domains/sdloop_vision.py`). This is the OTHER growable
codebook grain `DEDUP_ADOPTION_SWEEP_RESULTS.md` AR4.3 already probed (and returned a
NULL — "self-limiting," not at risk for the *repeat-same-key* case) — but that probe
used **one repeated signature**, never multiple genuinely different novel signatures in
one session, so it is itself an instance of the exact gap this task closes, one grain
over. It is reachable with existing fixtures/helpers (`domains/sdloop_vision.ingest`,
`.read_outcome`, `.codebook_state`, already used by
`tests/test_sdloop_vision_migrated.py`) and **structurally different from the
generator grain in the one way that matters**: `vq_grow_quantum`'s `ShapeSignature`
name is read straight off the observation's own (adapter-supplied, deliberately unique)
key via `IndexAt` — **not derived from content** the way `genlin_<matrix>` is — so this
grain is not exposed to the *same* name-collision mechanism AR4's repeat step targets.
The value of testing it anyway is the **positive** half of the methodology gap: does
presenting N genuinely novel percepts (not orientations of one shape — three
*structurally* distinct shapes, so no orbit-law folding applies) to one graph in one
session correctly mint N times, with no stall and bounded growth, at this grain too.

**Already measured (this document's own probe), reproduced below verbatim:**

```
tromino  recognized  ep 0.0->1.0  dt=0.0008s
square   recognized  ep 1.0->2.0  dt=0.0008s
line3    recognized  ep 2.0->3.0  dt=0.0011s
codebook_state: {'mints': 3, 'latent_dims': 0, 'latent_names': [], 'shape_signatures': 20}
repeat tromino (new key): status=recognized, covered_by=tromino
codebook_state after repeat: {'mints': 3, ...}  <- UNCHANGED, no re-mint
total wall: 0.0033s
```

Note the terminal `status` on the FIRST-ever novel shape reads `"recognized"`, not
`"minted"` — this is **expected**, not a stall: `vq_grow_quantum` installs the
newly-minted axis as a codebook entry and bumps `codebook_epoch` in the SAME rule
firing, which re-arms `sd_redecode` and the observation immediately recognizes itself
against the codebook entry it just caused to exist, within the same `run_rules` call.
The correct novelty signal at this grain is `codebook_state(s)["mints"]` (the
`CapabilityAxis` count), the same ground truth `test_scrambled_support_mints_every_time`
already uses — not the observation's own terminal status string. Stated up front so the
RESULTS doc's assertions are not misread as loose.

**Bar:**
* All 3 structurally-distinct novel shapes cause `codebook_state(s)["mints"]` to
  increase by exactly 1 each (3 total, running total after each) — no stall (a mint
  silently dropped would show as a smaller-than-expected total, exactly the AR2 shape
  one level up).
* `codebook_state(s)["shape_signatures"]` increases monotonically and by a bounded
  amount per orbit (not unbounded growth from a redecode storm).
* A repeat of the first shape under a **new, unique key** (the adapter's own
  discipline — every stimulus gets a unique key, per the module's own docstring)
  is `recognized` with `covered_by` equal to the first shape's key, and does **not**
  increase `mints`.
* `codebook_epoch` growth and wall-clock time are bounded by the same style of
  generous-but-real bars as AR3 (`<= baseline + 6` epoch, `< 3s` per `run_rules` call,
  `< 10s` total) — set to catch a 20,000-epoch-class regression, not to be a tight
  performance gate.

**This is scoped as a confirmatory generalisation, not a defect hunt**: per this
task's own constraint, if this probe (or the committed test) surfaces a genuinely new
defect at this grain, it will be named precisely in RESULTS, not fixed in this rung.

## AR6 — no regression, both directions

**Bar 6.1 (current engine, GO required):** the new test file, run against this
worktree's current (already-fixed) engine and seed set, is **100% green**.

**Bar 6.2 (pre-fix reproduction, best-effort per the task's own instruction not to
force a large detour):** the DEDUP rung's fix is a single commit, `dcea7ad`
(`Dedup adoption sweep: two real fixes, …`), with a single parent `3638c60`
(`PREREG: AddNodeIfAbsent adoption sweep — bars registered before any code edit`) —
i.e. `3638c60` is the exact pre-fix state, and `git show dcea7ad --stat` confirms
**zero Rust files changed** (only `seeds/shape_decode_loop.json` and the stale
`scripts/genmint_build_seeds.py` builder), so the SAME engine binary (`8963fb4dccaa`,
already coherence-probed in this worktree) is valid to run against the pre-fix seed
JSON — no rebuild needed for the regression check. Plan: check out `3638c60` in a
throwaway scratch worktree (outside both this task's worktree and the primary tree,
per the task's own "scratch location" allowance), copy the committed test file in
un-modified, run it, and report which assertions fail and how (expected: the AR2 stall
assertion fails on orbit 2/3, OR — if the coarse guard's exact pre-correction-1 state
is reproduced by accident — the AR3 loop bound fails). This is reported as best-effort;
if constructing the scratch worktree turns out to be awkward it will be replaced by a
close reading of `dcea7ad`'s diff against the registered AR2/AR3 assertions, per this
task's own explicit fallback.

**Bar 6.3 (broader regression):** the existing `tests/test_gen_infer_migrated.py`,
`tests/test_dimension_inference_migrated.py`, and `tests/test_sdloop_vision_migrated.py`
stay green (unchanged pass/fail) with the new file present — this rung adds a file, it
does not edit any existing test or seed.

---

## Explicitly out of scope

1. **Any fix.** This is a test-addition task. A newly-discovered defect (beyond the two
   already named in `DEDUP_ADOPTION_SWEEP_RESULTS.md`) is named in RESULTS, not fixed.
2. **`MetaShape` as the second grain** — ruled out above (AR5), needs a Rust field.
3. **Files owned by concurrent threads today**: `domains/analogical_thinking.py`,
   `runners/dsl/src/py.rs`, `substrate/world_adapter.py`'s checkpoint-load region,
   `domains/rule_signature.py`, `runners/dsl/src/term.rs`. Nothing in this task's plan
   touches any of them.
4. **A third grain** (e.g. `prog_chunk_growth`'s `code_write_construction` codebook,
   considered and set aside): its `ckg_mint` naming law is a strictly-increasing
   count discriminator, not a content-derived name, and constructing a SECOND
   genuinely-distinct novel chunk fixture (a different accepted-request template
   whose extracted `chunk_rels` differ in kind, not just content) requires reading
   `psy.synthesize_from_request` and the chunk-extraction walk closely enough that
   it is real fixture-construction work, not a cheap reuse of an existing helper —
   named as a follow-on, not attempted here.

## What would falsify this gate as a real regression-catcher (not just a green check)

* If Bar 6.2's pre-fix run does NOT reproduce a failure on AR2 or AR3, the gate's claim
  to be a regression-catcher (as opposed to a mechanism-confirming smoke test) is
  weakened and RESULTS must say so plainly rather than asserting it caught anything.
* If AR5's second-grain probe turns out, on the committed test, to disagree with the
  numbers already measured above (mints, epoch, status), that is itself worth reporting
  precisely (a flake or a probe-vs-test discrepancy), not silently adjusted to match.
