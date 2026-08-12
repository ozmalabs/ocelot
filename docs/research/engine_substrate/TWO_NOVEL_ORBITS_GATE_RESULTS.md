# Two-novel-orbits gate — RESULTS

**Prereg:** `TWO_NOVEL_ORBITS_GATE_PREREG.md`, committed (`89a002f`) before the test
file was written. Worktree `/home/matt/ocelot-two-novel-orbits-gate`, branch
`two-novel-orbits-gate`, from `main` at `c415a56`. Engine `8963fb4dccaa`,
coherence-probed, `test_engine_provenance_migrated.py` green (10/10). No Rust rebuild —
this is a pure test-addition rung, confirmed below.

**Verdict: all 6 PREREG bars GO.** New file `tests/test_two_novel_orbits_gate_migrated.py`
(4 tests), green against the current engine; **3 of the 4 tests independently reproduce
a failure against the pre-fix seed** (the fourth, the second-grain generalisation, is
correctly unaffected — it targets a grain the fix never touched); AR5's second-grain
generalisation is a GO (`ShapeSignature`/`vq_grow_quantum`), with `MetaShape` ruled out
up front per the PREREG's own reasoning; regression on the neighbouring suites is clean.

---

## The one thing worth reading if you read nothing else

**The gate is a real regression-catcher, not a green check that merely restates the
fix.** Running the exact same committed test file against the fix's own pre-fix parent
commit (`3638c60`, same engine binary, only the seed JSON reverted) reproduces the
named defect precisely: the second novel orbit (`SHEAR_B`) in a graph that already
holds a discovery from a first orbit (`SHEAR_A`) terminates at `status == "decoded"`
instead of `"recognized_transformed"` — the exact silent-drop
`DEDUP_ADOPTION_SWEEP_RESULTS.md` §4.2.1 described and this gate's own AR2 assertion
exists to catch. **Three of the four tests fail on the pre-fix tree, for exactly the
reason each one's docstring says it should; the fourth (the second-grain
generalisation) correctly passes on BOTH trees**, because it targets a codebook grain
(`vq_grow_quantum`) the fix never touched — its own AR4.3 probe in the DEDUP rung had
already found that grain self-limiting for the repeat case, and this rung's own probe
(§3 below) confirms it was never at risk for the *multiple-distinct-novel* case either.

---

## AR1 — the primary scenario, as built

Exactly the PREREG's registered fixture (`BASE` asymmetric L-tetromino, `_lin(M)`,
`gen_infer_enabled=1`, one booted graph, one held `ShapeSignature`), four orbits
presented **in sequence to the same graph**: `SHEAR_A=[1,0,1,1]`, `SHEAR_B=[1,1,0,1]`,
`UNIMOD=[2,1,1,1]` (= their composition), repeat `SHEAR_A`. Live, current engine
(`test_four_orbits_one_graph_no_stall_bounded_growth_correct_dedup`):

```
A  [1,0,1,1]  status=recognized_transformed  ep 0.0->1.0  dt~7ms
B  [1,1,0,1]  status=recognized_transformed  ep 1.0->2.0  dt~7ms
U  [2,1,1,1]  status=recognized_transformed  ep 2.0->2.0  dt~3ms
A2 [1,0,1,1]  status=recognized_transformed  ep 2.0->2.0  dt<1ms
total wall: ~18ms

generators: genlin_[1,0,1,1] -> (1,0,1,1)
            genlin_[1,1,0,1] -> (1,1,0,1)
LatentDimension names: latent:genlin_[1,0,1,1]
                       latent:genlin_[1,1,0,1]
                       latent:genlin_[1,0,1,1]+genlin_[1,1,0,1]
```

Byte-identical to the PREREG's committed-in-advance probe output. Two isolation
variants were also built, each targeting one specific claim narrowly enough that a
partial or accidental fix cannot pass by coincidence:

* `test_second_novel_orbit_does_not_stall_even_isolated` — presents ONLY `SHEAR_A`
  then `SHEAR_B` (no composition, no repeat) and asserts both resolve. This is the
  minimal reproduction of §4.2.1's "orbit 2 mints nothing" finding.
* `test_repeat_orbit_after_two_mints_does_not_triple_mint` — after two distinct
  generators are minted, re-presents each and asserts the generator count stays at 2
  (dedup direction, isolated from the composition step).

## AR2 — the stall assertion: GO, checked after every orbit

Implemented as an assertion **inside the loop**, run once per orbit, not deferred to
end-of-scenario — a stall on orbit 2 or 3 cannot hide behind orbit 4's success. Live,
current engine: all four orbits assert `status == "recognized_transformed"`
individually; all pass. **Falsified on the pre-fix tree** — see AR6.2.

## AR3 — the loop assertion: GO, real checked bounds

* Per-`run_rules()`-call bound: `< 3.0s`. Measured: all four calls `< 8ms` (current
  engine). The bound is **29× smaller** than the pre-fix-attempt's measured 87.4s, so a
  regression to that exact state cannot pass.
* Whole-scenario bound: `< 10.0s`. Measured: `~18ms`.
* `codebook_epoch` growth bound: `<= baseline + 4`. Measured: `+2` (one bump per
  genuine generator mint — `SHEAR_A`, `SHEAR_B`; zero for the composed orbit and the
  repeat). The bound is set at 2× the measured value (headroom for a legitimate future
  rung adding one more epoch-bearing effect) and remains **four orders of magnitude**
  below the pre-fix-attempt's measured 20,000-per-call blowup — a regression to that
  state fails this bound by construction, not by luck.

No wall-clock/epoch blowup was reproduced against `3638c60` either (see AR6.2) — that
specific defect existed only in a since-abandoned intermediate fix attempt that was
never committed to `main` at any point (`DEDUP_ADOPTION_SWEEP_RESULTS.md` §4.2.2's "first
attempt", corrected before the commit that landed). The bound is registered anyway,
per the PREREG's own framing: it exists to catch a *future* regression to that
mechanism (deleting the per-observation termination guard again), which is a real risk
the code comment at `sd_mint_generator` explicitly documents as the thing that must not
regress.

## AR4 — dedup-direction assertions: GO

* Exactly 2 `DimensionGenerator{kind:"linear"}` nodes after all four orbits — not 3
  (no spurious mint for `UNIMOD`, correctly explained as composition) and not 1 (the
  pre-fix cap). Matrices `(1,0,1,1)` and `(1,1,0,1)`, each present exactly once.
* Generator names distinct (`genlin_[1,0,1,1]` / `genlin_[1,1,0,1]`) — the direct
  regression check for the `load_generators` name-shadowing bug (§4.2.3): under the
  pre-correction-2 (base-shape-derived-name) state both would collide on
  `genlin_base_L`, and the final repeat-of-`SHEAR_A` step is specifically where that
  would surface as a failure to re-explain (not on orbit 1 itself). Passes on current
  engine; this specific sub-defect was already fixed before `3638c60` diverges from it
  (§4.2.3's correction 2 was folded into the same commit as correction 1, so it is not
  separately reproducible pre-`dcea7ad` without hand-reverting only half the diff — not
  attempted, since the whole seed file is what AR6.2 correctly reverts as a unit).
* Exactly 3 distinct `LatentDimension` names (2 individual generators + 1
  composition) — the repeat mints no 4th (AR4.1's fix, confirmed still working
  correctly in combination with AR4.2's fix in the same scenario, which the DEDUP
  rung's own probes never ran together against multiple novel orbits).

## AR5 — generalisation to a second grain: GO, `ShapeSignature`/`vq_grow_quantum`

**`MetaShape` ruled out, as pre-registered**, without re-investigation: its fix needs a
new Rust field (`pred_key`) per `DEDUP_ADOPTION_SWEEP_RESULTS.md` AR5, which is both a
Rust change and touches `shape_decode.rs` return-shape work adjacent to files this
task's own charter excludes — not cheap.

**Grain built: `seeds/vision_sdloop.json`'s `vq_grow_quantum` rule**, the OTHER
growable codebook the DEDUP rung's AR4.3 had already probed — but only for the
*repeat-same-signature* case (self-limiting, correctly a NULL there). This rung's own
probe presents **three structurally distinct novel shapes** (tromino / square /
3-line — different cell counts, not orientations of one shape, so no orbit-law folding
applies) to ONE graph in one session:

```
tromino  status=recognized  mints 0->1  ep 0.0->1.0  dt~1ms
square   status=recognized  mints 1->2  ep 1.0->2.0  dt~1ms
line3    status=recognized  mints 2->3  ep 2.0->3.0  dt~1ms
repeat tromino (new key): status=recognized, covered_by=tromino, mints STAYS 3
total wall: ~3ms
```

**All three mint distinctly, no drop, bounded growth — GO, and it stays a GO on the
pre-fix tree too** (see AR6.2 — this grain was correctly unaffected by the
`shape_decode_loop.json` v1.8.0→v1.9.0 diff, since `vq_grow_quantum` lives in a
different seed file entirely and was never touched by that fix). This is the honest
shape of a "checked and confirmed not at risk" result, not a "this test caught a bug"
result — recorded as such rather than dressed up as a second regression-catcher. The
one substantive finding: the terminal `status` field reads `"recognized"` even for a
brand-new shape (because `vq_grow_quantum` installs the codebook entry and bumps the
epoch in the SAME rule firing that mints it, so the observation immediately
re-recognizes itself against the entry it just caused to exist) — the correct novelty
signal at this grain is `codebook_state(s)["mints"]` (the `CapabilityAxis` count), which
the test uses; this was flagged in the PREREG in advance so it is not misread as a loose
assertion.

**Third grain considered and set aside, per the PREREG:** `prog_chunk_growth`'s
`code_write_construction` codebook (`ckg_mint`). Its naming law is a strictly-increasing
count discriminator (`ckt_<snake(head)>_q<count>`), not content-derived, so it is not
exposed to the SAME collision mechanism either — but confirming that (or finding
otherwise) would require constructing a second genuinely-distinct
`synthesize_from_request` fixture whose extracted `chunk_rels` differ in KIND, which
means reading the chunk-extraction walk (`domains/prog_chunk_growth.py`'s
`chunk_candidates`) closely enough to build a second spine template — real fixture work,
not a cheap reuse of `_boot_selfteach`'s existing one-shape gate. **Named as a follow-on,
not attempted**, per this task's own scoping instruction.

## AR6 — no regression, both directions

### 6.1 — current engine: GO

```
tests/test_two_novel_orbits_gate_migrated.py ....   [100%]
4 passed in 0.52s
```

### 6.2 — pre-fix reproduction: GO, real regression-catcher confirmed

Per the PREREG's plan (no Rust rebuild needed — `git show dcea7ad --stat` confirms zero
`.rs` files in the fix diff, only `seeds/shape_decode_loop.json` and the stale
`scripts/genmint_build_seeds.py` builder): `git worktree add --detach` at `3638c60`
(the fix commit `dcea7ad`'s sole parent — the exact pre-fix state), same engine binary
copied in (`sha256` verified byte-identical to this worktree's, `8963fb4dccaa`), the
committed test file copied in unmodified, run:

```
tests/test_two_novel_orbits_gate_migrated.py FFF.   [100%]
3 failed, 1 passed in 0.67s
```

**Exactly the predicted shape.** All three tests targeting the `DimensionGenerator`/
`LatentDimension` grain fail; the one targeting the `ShapeSignature`/`vq_grow_quantum`
grain (untouched by this fix) passes on both trees.

```
FAILED test_four_orbits_one_graph_no_stall_bounded_growth_correct_dedup
  -> orbit 'B' must resolve to recognized_transformed ... got 'decoded'
FAILED test_second_novel_orbit_does_not_stall_even_isolated
  -> the SECOND novel orbit in one graph must resolve ... got 'decoded'
FAILED test_repeat_orbit_after_two_mints_does_not_triple_mint
  -> a repeat must not mint a third generator: [(1, 0, 1, 1)]  (only 1 generator total,
     because SHEAR_B never minted one in the first place — the SAME root stall)
PASSED test_three_novel_shapes_one_graph_mint_distinctly_bounded_growth
```

Note on the third failure: it fails for the SAME underlying reason as the first two
(the coarse `kind == "linear"` guard capped the graph at one generator for life, so
`SHEAR_B` never got a chance to mint at all) — the AR4 dedup-direction assertion and
the AR2 stall assertion are, on THIS specific pre-fix defect, two views of one root
cause. That is expected and consistent with `DEDUP_ADOPTION_SWEEP_RESULTS.md`'s own
account: the stall and the "one generator for life" cap are the same guard.

**What was NOT reproduced, and why that is correct, not a gap:** the LOOP defect
(§4.2.2's 87.4s / 20,001-epoch blowup) did not reproduce, because that intermediate
state (naive `add_node_if_absent` swap with the coarse guard deleted and no
termination guard added) was a since-corrected first attempt that was **never
committed to `main` at any point** — `3638c60` is the PREREG commit (no code changes
yet), and `dcea7ad` is the finished, corrected fix; the broken intermediate state
between them exists only in the DEDUP rung's own measurement log, not in git history.
The PREREG registered this as best-effort and explicitly anticipated this exact
outcome ("if the coarse guard's exact pre-correction-1 state is reproduced by
accident...") — it was not, and the AR3 bound is retained anyway as a
regression-catcher against a FUTURE reintroduction of that mechanism (e.g. someone
deleting the `Count(Neighbours(obs, "gen_minted")) == 0` termination guard while
"simplifying" the rule), which is exactly the kind of edit the rule's own seed comment
warns against.

### 6.3 — broader neighbouring suites: GO, unaffected

```
tests/test_gen_infer_migrated.py
tests/test_dimension_inference_migrated.py
tests/test_sdloop_vision_migrated.py
tests/test_two_novel_orbits_gate_migrated.py
  -> 35 passed in 4.05s
```

No existing test edited; only the new file added.

---

## What this gate does NOT establish (CLAUDE.md: "synthetic-proven mechanism ≠
benchmark value, report both")

1. **No claim about production prevalence.** This is a mechanism-level gate on a
   booted synthetic agent, same boundary every DEDUP-rung fix drew. How often a real
   session presents multiple genuinely novel linear-generator orbits (or multiple
   novel percepts under the vq grain) in one sitting is unmeasured.
2. **The LOOP bound (AR3) is a forward-looking regression guard, not a reproduction.**
   Recorded precisely in §6.2 so this is not overstated: the specific 87.4s/20,001-epoch
   state was never in git history to reproduce.
3. **AR4's name-collision sub-check (load_generators shadowing, §4.2.3) is validated
   in its FIXED form, not independently isolated from AR4.1's LatentDimension fix** —
   both landed in one commit, and reverting only one half was not attempted (out of
   scope; the PREREG registered reverting the whole file as the regression mechanism).
4. **The second-grain result (AR5) is a "checked, not at risk" confirmation, not a
   second regression-catcher** — stated plainly in AR5/AR6.2 rather than implied.
5. **The third-grain candidate (`prog_chunk_growth`) is named, not built** — a
   follow-on, with the specific reason it wasn't cheap.

## What a reviewer should look at first

1. **AR6.2**, the pre-fix reproduction — the strongest evidence this gate is a real
   regression-catcher: 3/4 tests fail on the pre-fix tree, each for the documented
   reason, and the 4th correctly stays green because it targets an untouched grain.
2. **AR1's primary scenario**, `test_four_orbits_one_graph_no_stall_bounded_growth_correct_dedup`
   — the single test that most directly encodes the DEDUP rung's own worked example
   (4 orbits, 2 generators, 1 composition, 1 repeat) with per-orbit stall checks,
   bounded-growth checks, and both dedup directions in one scenario.
3. **AR5**, the second-grain generalisation and the honest `MetaShape` NO-GO /
   `prog_chunk_growth` follow-on naming — the methodology-gap closure applied one
   level more generally than the letter of the original finding required.

---

## Reproduce

```bash
cd /home/matt/ocelot-two-novel-orbits-gate
git log --oneline -1                     # two-novel-orbits-gate, on top of c415a56
sha256sum runners/dsl/python/substrate_rs/_native.abi3.so   # 8963fb4dcc…
PYTHONPATH=runners/dsl/python:. python3 -c "
import substrate_rs as srs; s=srs.Substrate()
a=s.node(s.add_node('T',{'lst':[1,2,3],'tup':(1,2,3)}))['attrs']
print(a['lst'], a['tup'], a['lst']!=a['tup'])"          # coherence probe

# AR1-AR4 — current engine
PYTHONPATH=runners/dsl/python:. python3 -m pytest -q -p no:randomly \
  tests/test_two_novel_orbits_gate_migrated.py -v

# AR6.3 — neighbouring suites
PYTHONPATH=runners/dsl/python:. python3 -m pytest -q -p no:randomly \
  tests/test_gen_infer_migrated.py tests/test_dimension_inference_migrated.py \
  tests/test_sdloop_vision_migrated.py tests/test_two_novel_orbits_gate_migrated.py

# AR6.2 — pre-fix reproduction (scratch worktree, same engine binary)
git worktree add --detach /tmp/prefix-check 3638c60
cd /tmp/prefix-check
sha256sum runners/dsl/python/substrate_rs/_native.abi3.so   # must match 8963fb4dcc…
touch runners/dsl/python/substrate_rs/_native.abi3.so        # mtime-staleness workaround,
                                                               # see DEDUP_ADOPTION_SWEEP_RESULTS.md's
                                                               # own "Environment note"
cp /home/matt/ocelot-two-novel-orbits-gate/tests/test_two_novel_orbits_gate_migrated.py tests/
PYTHONPATH=runners/dsl/python:. python3 -m pytest -q -p no:randomly \
  tests/test_two_novel_orbits_gate_migrated.py -v   # expect 3 failed, 1 passed
cd /home/matt/ocelot-two-novel-orbits-gate
git worktree remove /tmp/prefix-check --force
```
