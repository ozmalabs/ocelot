# REPLACING `G_figadj` — competitive border ownership. RESULTS

Pre-registration `VISION_FIGADJ_REPLACEMENT_PREREG.md`, committed **03e78a79**
before any real-frame number. Runner committed **19cb08b9**. Seeds
**83000–83999**. Engine **d6097900e8b5** (no Rust change), provenance gate run as
its own step **before** any number: **638 passed**.

Oracle `scripts/rung7_vision_bench.sh`: **212 passed, 10 skipped, exit 0** — this
tree has no `data/`, the documented no-corpus case (222 is the *collected* count;
the 10 skips are `BSDS300 corpus absent`). Reported with its condition.

Corpora pinned and asserted at run time: **C1** cartoon `08630d4b…`, **C2**
live-action `119eca43…`. Configuration **G72**: one 72×72 decode tiled into a
4×4 grid of 18×18 tiles, as the resolution rung recommended.

---

## THE HEADLINE, IN THREE LINES

**The replacement works: it triples-to-quintuples proto-object yield, the protos
persist far above an arbitrary partition, and they survive a tiling shift — so
they are scene structure, not window artifact.**

**But the finding that matters more is that `G_figadj` was NOT the whole blocker.
The four-times-reproduced zero is CONFIGURATION-CONDITIONAL: at G72 the
INCUMBENT already yields 3.3–14.1 multi-cell protos per frame.** The prior rung
attributed to a gate what was substantially owed to the whole-frame lattice.

**And a registered negative control FAILED**: the replacement mints on **26%** of
iid speckle fields where the incumbent mints on 0%. Every one of those false
mints is a **single cell**.

---

## 0 — CONTROLS: THE DEAD-INSTRUMENT ARM ACTUALLY FIRED, AND SO DID A NEW ONE

| control | incumbent | replacement | |
|---|---|---|---|
| **D1** committed 12×12 figure | 1 proto / 24 members | 1 proto / 24 members | reproduces, both |
| **D2b** uniform field, frame stripped | **1 proto, 144 "members"**, `n_frame=0`, `reach=0` | **same** | **the trap, fired, both arms** |
| **D2a** *figure* field, frame stripped | 0 protos (`G_figadj` refused both) | **1 proto, 24 members**, `n_frame=0`, `reach=0` | **REGISTERED PREDICTION CONFIRMED** |
| **NOISE** iid speckle, 18×18, k=16 | 0/100 | **26/100** | **REGISTERED CONTROL FAILED** |

**D2a is a dead-instrument trap that this rung registered IN ADVANCE as one it
expected to fire, and it fired.** The value-flood rung recorded a *wrong*
prediction here: it predicted a vacuous mint under the incumbent and got none,
because `G_figadj` refused both mutually-adjacent components. The replacement is
weaker, so §4 predicted it *would* mint — the smaller-perimeter side wins the
competition and mints on an unseeded flood. It does. A control that fires is a
control that works; it is separated from every live run by `n_frame = 0` and
`reach = 0`.

### The registered negative control that FAILED

§4 registered: *"iid noise at 18×18, k=16, must mint nothing under the
replacement."* It does not. **26/100 fields mint** (the registered n=10 pilot
caught 1/10, so the control had already failed at its registered n; n was raised
to 100 only to put a rate on a verdict that was already fixed, and both numbers
are reported so the enlargement cannot launder it).

**The mitigating fact, stated without it being an excuse: `max_false_proto_size`
is 1.** Every speckle false-mint is a **single cell**. The headline quantity —
*multi-cell* protos — is untouched by this failure mode. But the raw proto count
under the replacement carries a single-cell speckle tax that the incumbent did
not, and that is a real cost of the weakening.

The 12×12 / 100-field `arm_floor_noise` in the synthetic gate stays **0/100**
under both predicates, so this is specific to the 18×18 / k=16 regime, not a
general collapse of speckle refusal.

---

## 1 — ARM 1: MULTI-CELL PROTOS APPEAR — AND SO THEY DO UNDER THE INCUMBENT

Mean per frame over 7 sampled frames × 16 tiles.

| corpus | arm | k | comps | refused | pass | protos | **MULTI** |
|---|---|---|---|---|---|---|---|
| C1 | incumbent | 16 | 721.0 | 693.0 (**96.1%**) | 7.7 | 7.7 | **3.3** |
| C1 | replacement | 16 | 721.0 | 622.4 (**86.3%**) | 49.0 | 49.0 | **10.0** |
| C1 | incumbent | 8 | 365.7 | 320.9 (87.7%) | 13.6 | 13.6 | 7.6 |
| C1 | replacement | 8 | 365.7 | 263.1 (72.0%) | 48.4 | 48.4 | **12.9** |
| C2 | incumbent | 16 | 568.3 | 523.3 (**92.1%**) | 24.6 | 24.6 | **10.7** |
| C2 | replacement | 16 | 568.3 | 454.4 (**80.0%**) | 69.6 | 69.6 | **17.1** |
| C2 | incumbent | 8 | 230.9 | 176.9 (76.6%) | 25.0 | 25.0 | 12.7 |
| C2 | replacement | 8 | 230.9 | 135.6 (58.7%) | 49.6 | 49.6 | **18.4** |

**The replacement does exactly what it was derived to do.** Component structure
is byte-identical (the flood was not touched — `comps` matches to the decimal),
and the refusal share falls **96.1% → 86.3%** (C1) and **92.1% → 80.0%** (C2).
Proto yield rises **6.4×** (C1 k16) and **2.8×** (C2 k16); multi-cell protos rise
**3.0×** and **1.6×**.

**`G_figadj` at G72 still reproduces the prior rung's headline share** — 96.1% /
92.1% at k=16, against its 93.4%. The gate is exactly as strict as it was
measured to be. What changed is what that strictness costs.

### The finding the registered arms did not anticipate

**The incumbent yields 3.3–14.1 multi-cell protos per frame at G72.** The
quantity that was **exactly zero on four independent measurements** is not zero
here, under the *unmodified* mechanism.

The cause is the configuration, and it is mechanical: `add_field` sets `frame=1`
on every field's border, so **each 18×18 tile independently asserts that its own
window edge is ground.** A tile is a small window with a guaranteed ground seed
all the way round, and components per field drop from 294.9 (whole frame, L=32,
k=16) to ~45. Enclosure becomes common; `G_figadj` has far less to veto.

**So the value-flood rung's attribution was configuration-conditional.** Its
measurement of `G_figadj` was correct and reproduces here; its implied claim that
`G_figadj` was *the* thing standing between the mechanism and real-frame protos
was not. This is the same shape as this tree's run-16 reconciliation: two true
measurements, a conclusion that belonged to the configuration rather than to the
mechanism.

**Both facts stand together.** Windowing unblocks the mechanism; the replacement
then roughly triples what the unblocked mechanism yields. Neither subsumes the
other.

---

## 2 — ARM 2: THE PROTOS CORRESPOND TO SOMETHING

Unit of analysis: the frame pair (39 consecutive pairs), aggregated over 16
tiles, k=16. Paired 95% CI.

| corpus \| arm | persist | FLOOR-A shuffle | FLOOR-B arbitrary partition | vs A (lo) | vs B (lo) | |
|---|---|---|---|---|---|---|
| C1 \| incumbent | 0.792 | 0.594 | 0.103 | **+0.128** | **+0.612** | PASS |
| C1 \| replacement | **0.813** | 0.630 | **0.069** | **+0.119** | **+0.671** | PASS |
| C2 \| incumbent | 0.289 | 0.014 | 0.032 | **+0.204** | **+0.188** | PASS |
| C2 \| replacement | **0.221** | 0.024 | 0.038 | **+0.142** | **+0.133** | PASS |

**All four pass both floors with the CI lower bound clear of zero.** The
replacement's protos persist at **0.813** against an arbitrary partition of the
identical field at **0.069** — a separation of 0.67 with the field, the proto
count and the size multiset all held fixed. **The mechanism is not minting an
arbitrary partition.**

C2 (live-action) persists far less than C1 (cartoon) — 0.22 vs 0.81 — which is
what a moving camera over textured footage should do, and its floors fall with
it, so the *separation* survives.

**Honest reading of the arm-versus-arm comparison: it is not resolved.** The
replacement is numerically higher on C1 (0.813 vs 0.792) and lower on C2 (0.221
vs 0.289); the CIs overlap. **ARM 2's registered claim is that the replacement's
protos correspond to something, and that is established. A claim that they
correspond BETTER than the incumbent's is NOT established and is not made.**
Per the standing rule, deltas of this size are not results.

### The confound ARM 2 could not see — and the post-hoc control that closed it

**NOT PRE-REGISTERED. Reported because it can only weaken this rung's claim.**

Cross-frame persistence is measured per tile position and the tile grid is fixed
across frames. **A proto that is an artifact of the window geometry is therefore
perfectly stable across frames and would beat both registered floors** —
including FLOOR-B, which randomises the grouping but not the geometry. The
registered arm cannot separate scene structure from window artifact.

The discriminator: shift the tile grid by **half a tile** (9 px, so *every*
boundary moves onto what was tile interior) and re-decode the same frame. Scene
structure is indifferent to where windows fall; a window artifact is defined by
the window.

| corpus \| arm | shifted agreement | arbitrary floor | paired lo | |
|---|---|---|---|---|
| C1 \| incumbent | 1.000 | 0.000 | +1.000 | (n=6, small) |
| C1 \| replacement | **0.384** | 0.014 | **+0.321** | PASS |
| C2 \| incumbent | 1.000 | 0.024 | +0.954 | (n=10) |
| C2 \| replacement | **0.803** | 0.049 | **+0.694** | PASS |

**The protos survive a shift that moves every window boundary.** The confound is
real but it is not what is driving the result. The incumbent's 1.000 is on a
small, heavily-selected sample — it produces few protos, and the ones surviving
the coverage restriction are small isolated regions that trivially reappear; the
replacement's 0.38/0.80 is over several times as many protos and is the more
informative number.

---

## 3 — ARM 3: THE SYNTHETIC GATE STAYS 9/9, SUBSTANTIVELY

**18 passed** — the nine arms under the incumbent
(`tests/test_border_ownership_migrated.py`) *and* the same nine re-run with
`bo_mint_owned` armed (`tests/test_border_ownership_owned_migrated.py`).

This is constraint 1 tested rather than trivially satisfied by the flag's `0.0`
default. It holds for a structural reason: on a figure-on-blank stimulus the
figure has no abutting enclosed component, so the competitive conjunct is never
reached and the two term trees evaluate identically. **The replacement is a
strict weakening** — it agrees with the incumbent on every component that touches
nothing, and differs only where a component abuts another, which is the case a
photograph is full of and a synthetic raster has none of.

The Zhou contextual-flip headline, the figure-ground mint, the recurrence
fixpoint, the gestalt size-tracking, the open-contour floor, the ambiguous-split
hold-open, and the 100-field iid noise floor (seeds **36000–36099**, the
incumbent arm's own range, reused so both predicates see byte-identical fields)
all return identical verdicts.

---

## 4 — ARM 4: NO NEW THRESHOLD ENTERED (§13)

`tests/test_figadj_replacement_ast_migrated.py` — **7 passed**. A **term-tree AST
walk**, never a substring selector.

Asserted both ways round, so a hole in one cannot satisfy the other:

- every `Lit` appearing in a comparison is compared against a **0/1 flag**
  (`bown`, `bown_own`, `bg`, `frame`, `owns`), or is the pre-existing `2` against
  `Count(roots)` that *defines* a bipartition;
- **no** literal is compared against `val`, `rim`, `glabel`, `cid`, `members` or
  `root`;
- the literal **inventory is unchanged in KIND** from the incumbent — no third
  kind was added;
- the ownership comparison, located **structurally**, is `Attr(rim)` vs
  `Attr(rim)` under exactly one `Not`, **with no literal on either side**;
- `bo_rim` computes a `Count` and does not bound it by any constant;
- the incumbent predicate does not read `rim` and carries exactly one
  mutual-exclusion guard.

**The tie is equality.** §13 is satisfied by construction, not by deriving a
constant.

---

## 5 — M4: THE BACKGROUND DID NOT SWALLOW THE FIELD

`max_members / 324`, worst case over all rows: **0.327 under BOTH arms** —
identical, so it is not caused by the replacement. It occurs only at `k=2`, where
a two-level quantization legitimately produces a component covering a third of a
tile. At the headline `k=16` the worst case is **0.028–0.046**.

The named failure mode of the prior rung — *"loose admissibility lets the
background swallow the figures"* — **does not occur**, which is what the
prediction that this rung does not touch the flood requires.

---

## 6 — INSTRUMENT VALIDATION

The prior rung's counterfactual simulation was validated `168/168` **under the
incumbent predicate only**, so it cannot score a different predicate. **Both
predicates were therefore run through the substrate itself**, and the read-out
was re-validated under each.

- **`G_pass == n_protos`: 48/56 rows per arm.** The **8 mismatches are all at
  `k=2`, and are identical in both arms** — so the cause is shared, not the
  replacement.
- **Cause identified, exactly.** `bo_mint_gestalt` mints protos the read-out does
  not replicate (§7 registered that the rule would not be touched). Verified on
  C1/k2/f0: `G_pass(12) + gestalt-minted(2) = n_protos(14)`, exact.
- **This overturns another of the prior rung's residuals.** It recorded
  `bo_mint_gestalt` as *"unreachable on real frames — it has never been exercised
  outside synthetic stimuli."* **At 18×18 tile grain with k=2 it is reachable and
  it fires.** Configuration-conditional, like the headline.
- **Every `k=4/8/16` row reconciles exactly**, including all headline rows.
- **`rim_mismatch = 0` on all 56 replacement rows** — the `rim` the rule
  materialised agrees cell-for-cell with an independent recomputation from the
  settled graph. (On the incumbent arm `rim_mismatch` is large and *meaningless*:
  `bo_rim` is gated on `bown_own`, so `rim` is never written there. That is the
  flag working, and it is not a reconciliation claim.)

---

## 7 — SEED ACCOUNTING: MEASURED, NOT ASSERTED

Declared **83000–83999**. Measured with `scripts/seed_audit.py`:

```
{"declared": [83000, 83999], "ok": true, "outside": []}
```

Full report over all three of this rung's scripts: **5 resolved seeds —
83100, 83101, 83200, 83201, 83900 — and 83300/83301/83310/83311 in the
post-hoc control. ZERO unknown sinks.**

**The first draft passed `--check` while leaving 2 sinks UNKNOWN**, because the
RNGs were seeded off `spec["episode_index"]` (a dict subscript the analyser
cannot resolve). **A `--check` that passes with unknown sinks has verified
nothing.** The loop was restructured to an explicit `((0, "C1"), (1, "C2"))`
tuple sequence so every seed is statically resolvable — and the RNG ordinal was
decoupled from the catalogue index, which should never have been coupled.

**Disclosed draw outside the block:** `tests/test_border_ownership_owned_migrated.py`
drives `arm_floor_noise`, which draws **36000–36099**. That is the *incumbent*
arm's own range, reused deliberately so both predicates see byte-identical
fields; it is a re-run of an existing control, not an allocation.

---

## 8 — WHICH REGISTERED OUTCOME OCCURRED

§6 registered three. **The answer is outcome 1 with a large piece of outcome 3.**

1. **The replacement works** — multi-cell protos appear (3.0× / 1.6× the
   incumbent at k=16) and persist far above an arbitrary partition, surviving a
   tiling shift. ✅
3. **`G_figadj` was not the whole blocker** — the four-times-reproduced zero is a
   property of the whole-frame configuration, and the value-flood rung's
   attribution needs the revision recorded in §1. ✅

Outcome 2 (an arbitrary partition) is **refuted** by FLOOR-B with the lower bound
at +0.671 / +0.133.

---

## 9 — WHAT I GOT WRONG

- **I did not anticipate that the configuration change alone would dissolve most
  of the blockade.** The rung was framed as replacing a gate that produces
  nothing on real frames; at the configuration the brief itself recommended, the
  unmodified gate produces plenty. Both arms had to be re-measured at G72 to see
  it, which the "re-earn every floor across a configuration change" instruction
  is exactly what forced — had I inherited the floor, I would have reported a 3×
  improvement over a zero that was not there.
- **A registered negative control failed and I am reporting it as a failure**,
  not reframing it. The replacement has a 26% single-cell false-mint rate on iid
  speckle. The `max_false_proto_size = 1` finding softens the consequence but
  does not rescue the control.
- **ARM 2 as registered could not distinguish scene structure from window
  artifact**, because a fixed tile grid makes a geometric artifact perfectly
  persistent. I did not see this when registering it. The post-hoc tiling-shift
  control closed it, and it closed favourably — but a control added after seeing
  results is weaker evidence than one registered before, and it is marked as such
  wherever it appears.
- **I wrote a watcher whose `pgrep -f` guard matched its own shell's command
  line** — the exact failure the brief named. The run was covered by an
  independent completion notification, so nothing was lost, but the guard was
  useless and I would not have known from its silence.
- **A cosmetic log-format bug**: the noise-control log line prints `26/10`
  because the denominator was left at the registered n after the count moved to
  100. The JSON carries both numbers correctly.

## 10 — RESIDUALS (not fixed here)

- **The tiling injects a "window edge is ground" prior per tile.** The shift
  control shows it is not driving the result, but the prior is real and
  unmodelled. A whole-frame decode at 72×72 with true image-border framing is the
  clean comparison and was not run.
- **`k` remains a hand-set adapter magic number** (§13), inherited and unfixed.
- **The single-cell speckle tax is unmitigated.** The obvious lever — requiring
  a proto to exceed one cell — would be a hand-set size threshold and is
  therefore refused under §13.
- **`bo_mint_gestalt` is now known to be reachable** at tile grain and is not
  replicated by the read-out; the 8 unreconciled `k=2` rows are its footprint.
  It was not modified, as registered.
- **Arm-versus-arm persistence is not resolved** (C1 favours the replacement, C2
  the incumbent, CIs overlap). Separating them needs more frame pairs than 39.
- **7 sampled frames per corpus for M1**, inherited from the incumbent. No CI is
  claimed on any per-frame mean; the load-bearing M1 numbers are aggregate shares
  over ~12,000 components per arm.
