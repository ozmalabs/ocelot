# VISION — THE STREAM: a bounded budget spent by SALIENCE × SCALE (RESULTS)

*Confirmatory run of `VISION_STREAM_PREREG.md` (committed BEFORE the run at
`19f28448`, §3). Runner `scripts/stream_measure.py`; gate
`tests/test_stream_salience_migrated.py`; seed `seeds/vision_stream.json` (builder
`tools/build_vision_stream.py`); adapter `domains/stream_world.py`; raw
`results/stream_measure.json`.*

## Engine / bench / provenance (§10)

- **Engine `7d5f50c18673`** @ `runners/dsl/python/substrate_rs/_native.abi3.so`
  — **shared build, Rust source byte-identical** to canonical (`provenance_line()`
  reads *"shared build from … — Rust source identical"*; this rung adds **NO Rust**,
  so the shared build is legitimate, §10.1 rule 4). `data/` symlinked to canonical
  (§10.2).
- **Bench 200 passed / 0 failed with `data/`** (`scripts/rung7_vision_bench.sh`,
  157.3s); the no-Python-thresholds scan is clean (*"every knob is graph data"*).
- **Sibling gates green: 105 passed / 0 failed** run together — illusion · blink ·
  vision-ground · time · depth · stereo · dim · gen_infer · provenance · sdloop ·
  cycle-detect + the new `test_stream_salience_migrated.py` (**6/6**, also verified
  in isolation). The **sd orbit law `{2:1,3:2,4:2,6:2,12:4}` is unmoved** (the
  sdloop gate, which pins it, passed).
- **NO new Rust, ONE new seed** (`vision_stream`, NOT boot-loaded; ships
  `StreamParams{stream:0.0}` OFF by default), so §9 byte-identity holds by
  construction and is verified above.

## Verdict — ALL 6 gated arms PASS (every prediction held; the one proviso landed inside its stated window)

| arm | result |
|---|---|
| **A_coarse_first** (scale) | **PASS** — coarse residuals [30,25,20] stream in as `order=[0,1,2]`; the 6 fine regions [6,5,4,3,2,1] stay at render grain (`order=−1`); 0 inversions (order monotone in residual). *Large shapes stream in first.* |
| **B_budget_allocation** (salience) | **PASS** — the salient region (residual 50, placed LAST row-major) resolves **first** (`order 0`); the salience spend resolves the top-3 `{0,1,7}`; the residual-BLIND uniform spend (`{0,1,2}`) leaves the salient region UNSEEN. *The budget goes where the surprise is.* |
| **C_preemption** (the spear) | **PASS** — a majority-mass spear (4×100 vs periphery 10×1) fires the tunnel detector; periphery resolved **0** WITH the spear vs **4** WITHOUT it; no tunnel without. *"You see very little else."* |
| **E_compute** (bounded spend) | **PASS** — refinements `spent == min(budget, N_positive)` EXACTLY (3/3/4); at fixed budget 4, resolved-count is FLAT across N∈{16,64,256,1024} (all 4). C3 selection-cost exponent **1.590** (reported, ungated). |
| **X_offday** (§9) | **PASS** — flag OFF (default) ⇒ inert: `spent=0`, `order` all −1. |
| **D_floor** (anti-overfit) | **PASS** — F1: a zero-residual field spends **0**; F2: **0/100** iid-noise fields (seeds 33000–33099) invent a tunnel; F3: **100/100** residual-monotone, **0** total inversions. |

## The headline — perception STREAMS by salience × scale on a bounded budget, and preemption FALLS OUT

**One water-filling rule (`stream_resolve_salient`: resolve the `Argmax`-residual
region per `run_rules` pass, count the budget up as graph data) produces all three
phenomena the creator named, with ZERO magic numbers:**

- **Coarse-to-fine by SCALE (order-N):** under a partial budget, the large/coarse
  structure (which carries more residual MASS) streams in first and the fine detail
  is left at the render grain — `order=[0,1,2,−1,−1,−1,−1,−1,−1]`, coarse resolved,
  fine unseen. *"Opening your eyes in a random place, large shapes stream in first."*
- **Allocation by SALIENCE (water-filling):** the budget flows to the largest
  residual first, so a single salient region is resolved even when it is last in the
  raw scan order — where a residual-blind uniform spend of the SAME budget misses it
  entirely. *The budget goes where the surprise is.*
- **PREEMPTION / TUNNEL (the spear):** a maximally-salient looming region (a
  contiguous cluster holding the majority of the residual mass) DRAINS the whole
  budget onto itself; the periphery gets **nothing** (0 resolved, vs 4 when the spear
  is absent) and degrades to the top-down render. *"A spear flying at your head means
  you see very little else."* **There is NO preemption threshold** — the tunnel is
  the SAME `Argmax` ordering under the SAME budget; the spear wins because it HAS the
  residual mass (§13: preemption falls OUT, it is not put IN).

**The anti-overfit crux holds:** the stream is NOT a universal salience-hallucinator.
A structureless (zero-residual) field is left entirely at the render grain (`spent=0`
— no surprise, no spend); **0/100** scattered iid-noise fields invent a tunnel (a real
spear needs a contiguous majority-mass, which scattered noise cannot form); and the
resolution order is residual-monotone in **100/100** (0 inversions) — the mechanism
orders by TRUE salience and invents no different order. A mechanism that "streamed"
structure from noise would fail all three; none fail.

**The spend is BOUNDED — the whole point.** The number of refinements is
`min(budget, N_positive)` EXACTLY (never more than the budget), and it does NOT grow
with the field: at a fixed budget of 4, exactly 4 regions are resolved whether the
field has 16 or 1024 regions. The bounded budget is the claim, and it is exact.

## What I predicted, and where the one proviso landed (§3.7)

I predicted **all four phenomenon arms hold, the floor is 0/100, and the spend is
bounded** — confirmed on every arm. The three provisos:

1. **run_rules serialisation (proviso 1)** — I predicted exactly one region resolves
   per pass (the unique `Argmax` winner), so the budget cannot overshoot. **HELD:**
   `spent == min(budget, N_positive)` to the unit across every arm (the
   `qf_frontier_goal` `Eq(·, Argmax)` idiom serialises the fixpoint as expected).
2. **Compute exponent (proviso 2)** — I predicted the argmax-per-candidate selection
   scan would be **≈ 2**. **Measured 1.590** — sub-quadratic, INSIDE the "not the
   O(N²) global-match drive" window, and stated in advance so it is not a rescued
   surprise (§3.6). The `run_rules` matcher prunes the candidate set below the naive
   O(N²); C3 is the honest cost of the selection scan and is **ungated** — the gated
   compute claim is the EXACT bounded spend (C1/C2), which is the real
   "compute-bounded" result. The selection cost is the `run_rules` overhead, NOT the
   `apply_rule_once` drive, and 1.59 < 2 regardless.
3. **Floor F2 (proviso 3)** — I predicted 0/100. **HELD 0/100** — the majority-mass
   definition of a tunnel (resolved mass ≥ unresolved mass, with the field not fully
   covered) is not tripped by scattered noise where the budget-many top cells hold a
   small fraction of a large field's mass. No tightening was needed.

**No proviso broke; nothing was rescued or re-run (§5/§3.6).**

## Audit — what was already built vs the contribution (§12.4, in-code)

Verified in the source before designing (cited in the prereg §0):
- `space_quantize` (`runners/dsl/src/space_quantize.rs`) decomposes a focus into
  **maximal boxes** greedily (coarse-BIASED, `space_quantize.rs:434–721`) but has
  **NO budget and NO salience order** — it resolves the whole focus in one call
  (`min_extent` is *"a performance knob only … the RESULT is identical"*, `:101–106`).
  Its residual→refine step exists only as an INPUT contract (`stale`/`split_along_dim`,
  `:51–64`), and the refinement rule (`qf_refine_residual`) is **DESIGN ONLY, NOT
  IMPLEMENTED** (`DYADIC_DEPTH_DESIGN.md` §0/§5). **This rung does NOT touch
  `space_quantize.rs`.**
- `seeds/quanta_navigation.json` is a Bellman FLOOD for navigation, not a salience
  budget: `qf_relax` (`min`-relax over portals), `qf_frontier_goal` (`Eq(F,Argmin(…))`
  single-winner). No budget attr, no salience order, no queue anywhere in vision.
- The primitives DO exist and are in-class: `Argmax`/`Argmin` (`term.rs:376–377`),
  `Plus`/`Minus` (`term.rs:492–493`), the flag-gated-rule idiom
  (`GroundParams`/`PickUnique(NodesOfType …)`), the `s.tick()` fixpoint driver.

**The contribution:** ONE seed (`vision_stream.json`, flag OFF by default) whose
single rule spends a `Scene.budget` by resolving the `Argmax`-residual region per
`run_rules` pass — coarse-first, budget-allocation and preemption/tunnel as EMERGENT
consequences with no threshold. NO new Rust; the salience-ordered bounded budget is
expressed entirely in the existing DSL, the illusion/stereo-rung pattern.

## Scope — what is NOT shown (§8), and the named frontier

- **BOUNDED to the discrete/integer, in-frame residual-mass class.** Integer
  residuals (surprise MASS), integer budget, integer positions. Nothing continuous is
  claimed (the frame/continuum invariant: the continuous lives in the cross-frame
  render/metric, not a frame's coordinates; `coord_ints` refusing floats stays
  correct).
- **The COLOUR-SALIENCE channel (pop-out for equiluminant targets) is the named
  frontier — NOT attempted.** Salience here is luminance/residual mass; a colour
  pop-out channel needs the separate categorical colour sign, not built.
- **The full 3D-heading dazzle / looming-bearing test is the named frontier — NOT
  attempted.** A true "spear flying at your head" needs objecthood + bearing/heading
  estimation (the diagnosed cortex layer). Here the spear is a high-residual-mass
  contiguous region (looming = large + high contrast), the tractable in-class core.
- **This is NOT a re-implementation of `space_quantize`'s depth ladder.** The
  `SpaceQuantum.depth` + `refines`-edge route (`DYADIC_DEPTH_DESIGN.md` §5) remains
  deferred; the stream runs over a residual-mass region field, not the navigation
  flood — they compose in principle (salience = a quantum's residual) but the coupling
  is not built here and is not claimed.
- **Salience is supplied as measured residual mass** (the runner computes the
  render-vs-input surprise MASS mechanically, exactly as the illusion runner computed
  `gbel` vs `raw_sensor` / `frames_symdiff`). This rung tests the salience-ORDERED
  bounded budget (the decision), not the residual computation (the just-landed
  bidirectional loop already proved residual = surprise).

## Is perception a salience-ordered bounded stream? — the plain answer

**Yes, bounded.** A single water-filling rule over a residual-mass field spends a
bounded budget in descending-salience order: large/coarse structure streams in first
(order-N), the budget flows to the salient region (water-filling), and a
majority-mass spear preempts the whole budget onto itself, leaving the periphery at
the render grain — tunnel vision, with NO preemption threshold (it falls out of the
`Argmax`). It does not spend where there is no surprise and invents no tunnel from
noise (`spent=0` on a flat field; 0/100 on scattered noise; 100/100 residual-monotone).
The spend is exactly `min(budget, N_positive)`, flat in field size. **Bounded to** the
discrete/integer, in-frame residual-mass class; the colour-salience channel and the
3D-heading looming test are the named, unreached frontier. Zero magic numbers were
committed (the budget and every residual are structural data; the decrement is the
integer unit +1; the ordering is a pure `Argmax`; the only proviso that could have
surprised — the selection-cost exponent — was predicted ≈2 and measured 1.590, inside
its window and not gated).
