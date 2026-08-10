# VISION — THE STREAM: a bounded budget spent by SALIENCE × SCALE (pre-registration)

*Written and COMMITTED before the confirmatory run (PROTOCOL §3). Seeds
**33000–33999** (declared below). 12000–32999 untouched.*

## 0. The claim, and the audit that precedes it

Creator's framing: *"vision is streamed in by salience and order N. A spear flying
at your head means you see very little else. Opening your eyes in a random place,
large shapes stream in first."* The percept is NOT delivered all-at-once and
uniform — it is **STREAMED**: (1) coarse-to-fine by **SCALE** (large low-frequency
structure resolves first; detail refines on the residual — order-N); (2) allocated
by **SALIENCE** (a bounded refinement budget is spent on the largest-residual
region first); (3) **PREEMPTIBLE** (a maximally-salient / looming / large-residual
"spear" captures the budget and the rest degrades to the top-down render — tunnel
vision, "you see very little else").

### AUDIT (in-code, §12.4) — what already exists, verified in the source

- **`space_quantize` (Rust, `runners/dsl/src/space_quantize.rs`) does NOT stream
  coarse-before-fine under a partial budget.** It decomposes the focus region into
  **maximal axis-aligned boxes** greedily (`grow_box` / `split_along_dim`,
  lines 434–721) — which is *structurally* coarse-biased (it makes the biggest box
  it can and only subdivides where the belief forces it) — but it resolves the
  **whole** focus in **one call**, foveated to `focus_lo/hi`, with **NO budget and
  NO salience ordering**. Its `min_extent` field is documented as *"a performance
  knob only … the RESULT is identical to a naive unit-stepped grower"*
  (`space_quantize.rs:101–106`). So the SCALE decomposition into coarse quanta is
  prior machinery; **the salience-ordered bounded STREAM over it is not built.**
- **The residual→refine step exists only as an INPUT contract and a DESIGN NOTE.**
  `space_quantize` reads `stale`/`stale_dim` as input and re-splits along the
  failing dimension (`space_quantize.rs:51–64`, `split_along_dim` 434–500), but the
  Rule that would SET `stale` in response to a residual (`qf_stale_on_block`) and
  the depth-refinement rule (`qf_refine_residual`) are **explicitly NOT built** —
  `runners/dsl/DYADIC_DEPTH_DESIGN.md` is **"DESIGN ONLY. NOT IMPLEMENTED"** (§0),
  and §5 warns that touching `space_quantize.rs` is *"the exact sprawl the task
  warns against."* **This rung does NOT touch `space_quantize.rs`.**
- **The quanta-navigation seeds (`seeds/quanta_navigation.json`, 14 `qf_*` rules)
  are a Bellman FLOOD for navigation, not a salience budget.** `qf_relax` is a
  `min`-relax over portals; `qf_frontier_goal` commits the **single** nearest
  frontier via **`Eq(F, Argmin(...))`** — the *"match the one Argmin winner"*
  idiom. `qf_stale_on_block_*` set `stale` from block observations. There is **no
  budget attr, no salience order, no queue** anywhere in the vision seeds.
- **The ordering + arithmetic primitives DO exist and are in-class.** `Argmax` /
  `Argmin` Terms (`term.rs:376–377`, used 37× / 13× across seeds), `Plus` / `Minus`
  (`term.rs:492–493`, used 2428× / 581×), the flag-gated-rule idiom
  (`GroundParams{ground:0.0}` + `Gt(Attr(PickUnique(NodesOfType …)),0.5)` in
  `seeds/vision_ground.json`), and the run-to-fixpoint `s.tick()` driver
  (`ground_world.present`). **The salience-ordered bounded budget is expressible in
  this class with NO new Rust and NO new engine primitive** — the contribution is a
  **seed rule set**, exactly the illusion-rung / stereo-rung pattern.

**The rung's contribution:** ONE seed (`seeds/vision_stream.json`, flag OFF by
default, §9) whose single rule `stream_resolve_salient` spends a `Scene.budget` by
resolving the **`Argmax`-residual** region per `run_rules` pass, decrementing the
budget as graph data. **Coarse-first, budget-allocation, and preemption/tunnel are
EMERGENT consequences of that ONE water-filling rule — there is no preemption
THRESHOLD (§13: preemption falls OUT of the argmax; it is not put IN).**

## 1. Mechanism — exact (all in graph data, no Python decision)

The runner (`scripts/stream_measure.py`, adapter `domains/stream_world.py`) builds a
scene **mechanically** and reads the stream back; it makes **no percept decision**
(§0 / CLAUDE.md). Graph:

- `StreamParams{stream: 0.0}` — the OFF-by-default flag (the `GroundParams` idiom).
- `Scene{budget: B (Int), spent: 0.0}` — the bounded resource, counted UP to B.
- `Region` nodes, `scene -has_region-> R`, attrs: `rrow`/`rcol` (Int position),
  `scale` (Int level: 0 coarse … k fine), `residual` (Int ≥ 0 = **salience** = the
  render-vs-input surprise MASS over the region, set MECHANICALLY by the runner —
  the residual the just-landed bidirectional loop computes), `resolved` (0.0
  default), `order` (−1.0 default = never streamed in).

**The ONE rule** `stream_resolve_salient` (`match [["scene","has_region","R"]]`):
- **where** `And`: (i) flag on `Gt(StreamParams.stream, 0.5)`; (ii) budget remaining
  `Lt(Scene.spent, Scene.budget)`; (iii) unresolved `Lt(R.resolved, 0.5)`; (iv)
  positive residual `Gt(R.residual, 0.0)`; (v) **winner**
  `Eq(R, Argmax(source = Filter(Neighbours(scene,has_region): unresolved ∧
  residual>0), value = Attr(cand,"residual")))`.
- **effects**: `set R.resolved = 1.0`; `set R.order = Scene.spent`;
  `set Scene.spent = Plus(Scene.spent, 1.0)`.

`s.tick()` runs this to a fixpoint. Each pass exactly **one** region satisfies (v)
(the unique Argmax winner; ties broken deterministically first-encountered, the
`qf_frontier_goal` precedent), so **one** region resolves and the budget advances by
one. The stream terminates when `spent == budget` **or** no unresolved
positive-residual region remains. **`order` is the stream sequence** (0 = streamed
in first); `order = −1` = never reached this budget. Zero floats are tuned: the
budget `B` and every `residual` are STRUCTURAL data (a budget the world states; a
residual the render-vs-input mass produces), the decrement is the integer unit
`+1`, and the ordering is a pure `Argmax` (§13).

## 2. Statistics — exact, per arm

All arms DETERMINISTIC except the floor (n fixed in advance, matching the
illusion/blind-spot precedent). The **spear-detector** used by the preemption arm
AND the floor is one readout: `tunnel(scene) := (spent == budget) ∧
(periphery_resolved == 0) ∧ (Σ residual over resolved ≥ Σ residual over
unresolved)` — the budget was consumed by regions holding the **majority** of the
field's residual mass while the periphery got **nothing** (majority = the
scale-free definition of dominance, a READOUT over the percept, NOT a rule
threshold — the rule has none).

### A — COARSE-FIRST (scale; a CONFIRMATION that the ordering realises order-N)

A multi-scale field: `n_coarse` scale-0 regions (large area ⇒ high `residual`) +
`n_fine` scale-≥1 regions (small area ⇒ low `residual`), all residuals distinct,
every coarse > every fine. Budget `B = n_coarse` (PARTIAL: `B < n_coarse+n_fine`).
**PASS iff** (a) the resolved set is **exactly** the coarse regions (`min residual
over resolved > max residual over unresolved`); (b) every fine region is unresolved
(`order = −1`); (c) the stream order is monotone non-increasing in residual (a
higher-residual region streams no later — 0 inversions). *"Large shapes stream in
first; detail refines on the residual."*

### B — BUDGET-ALLOCATION (salience; the budget goes where the surprise is)

One high-residual **salient** region (placed LAST in row-major order) + a
low-residual REST (each residual > 0, all < salient), budget `B` modest. **PASS
iff** (a) the salient region is resolved **first** (`order == 0`); (b) the resolved
set is the top-`B` by residual (water-filling); (c) **CONTRAST** — a residual-BLIND
**uniform-spend control** (row-major round-robin, same `B`, computed in the runner)
leaves the salient region **UNRESOLVED** (it is last in row-major, `B <
salient_index`), where the salience spend resolves it at `order 0`. PASS iff
salience-spend resolves the salient region AND uniform-spend (same budget) does not.

### C — PREEMPTION / TUNNEL (the spear; "you see very little else")

Inject a **spear**: a contiguous cluster of `K` regions with residual so large their
combined mass is a strict MAJORITY of the field, `K == B` (looming = large + high
contrast) + a low-residual PERIPHERY. **PASS iff** (a) `tunnel(scene)` fires — all
budget spent on spear regions, periphery resolved == 0, spear holds the residual
majority; (b) **CONTRAST** — the SAME periphery with the spear REMOVED (spear
residual set 0, same `B`) resolves periphery regions (`periphery_resolved > 0`), so
the peripheral resolution is measurably lower (0) WITH the spear than without (>0).
*The budget collapses onto the spear; the rest degrades to the render.*

### D — ANTI-OVERFIT FLOOR (not a universal salience-hallucinator)

- **F1 (deterministic):** a ZERO-residual field (render already matches input — no
  surprise) resolves **0** regions (`spent == 0`) — the stream does not spend budget
  inventing detail where there is none.
- **F2 (n = 100, seeds 33000–33099):** 100 random iid-noise residual fields (residual
  drawn iid per region, NO contiguous salient mass) invent **0** tunnels —
  `tunnel(scene)` fires **0/100** (scattered noise cannot form a majority-mass
  contiguous spear). PASS iff **0/100**, mirroring the illusion rung's 0/100 blank
  floor.
- **F3 (support, n = 100, same seeds):** the resolution order is residual-monotone
  in **100/100** (0 inversions) — the mechanism orders by TRUE salience and invents
  no different order. Reported, not separately gated.

### E — COMPUTE-BOUNDED (the whole point: bounded spend)

- **C1 (EXACT):** total refinements `spent == min(B, N_positive)` EXACTLY, across all
  arms — the spend is bounded by the budget, independent of `N`. This is the headline
  compute claim.
- **C2 (fixed-budget locality):** at FIXED `B`, the number of regions resolved does
  NOT grow with field size `N` (constant `= B`) — refinement is BUDGET-directed, not
  field-directed. PASS iff resolved-count is flat in `N` at fixed `B`.
- **C3 (descriptive, ungated):** the rule-application/selection cost vs `N` at fixed
  `B`, fitted log-log exponent, reported honestly. Predicted `≈ 2` because the
  `Eq(R, Argmax(…))` winner idiom re-evaluates the argmax per candidate binding (the
  `qf_frontier_goal` cost structure) — this is the `run_rules` SELECTION cost, NOT
  the O(N²) `apply_rule_once` GLOBAL-MATCH drive, and it is stated in advance so it
  cannot be a rescued surprise (§3.6). The bounded-SPEND claim (C1) is the compute
  result; C3 is the honest cost of the selection scan.

### §9 — OFF-day

`vision_stream` is loaded only by the runner/gate (not boot-loaded), and ships
`StreamParams{stream:0.0}` so the rule is inert by default. **NO new Rust** ⇒ engine
byte-identical by construction. PASS iff: bench **200/0** with `data/`; sd orbit law
`{2:1,3:2,4:2,6:2,12:4}` unmoved; sibling gates green — illusion 8 · blink 9 ·
vision-ground 11 · time 6 · depth 8 · stereo 9 · dim 8 · gen_infer/provenance 7 ·
sdloop · cycle-detect.

## 3. n, fixed in advance

Deterministic arms need no n. The floor: **n = 100** (seeds 33000–33099), matching
the illusion spatial floor and the blind-spot blank floor. No power analysis is
needed for a floor whose null is an EXACT 0 count (any single false tunnel fails it).
No sweeps, no re-runs (§3.6).

## 4. Burned-seed ledger for this rung

- **33000–33099** — anti-overfit floor (F2/F3), 100 seeds.
- **33100–33999** — CLEAN, reserved for any follow-up with its own prereg.

Confirmatory floor seeds consumed ONCE here, never reused. The deterministic arms
were designed on hand-constructed stimuli only (no 33xxx seed touched).

## 5. Decision rule — what each answer means (§7: either answer is a result)

- **Coarse-first orders by scale AND budget goes to the salient region AND the spear
  preempts to a tunnel AND the floor is 0 AND the spend is bounded** ⇒ perception
  streams by salience × scale on a bounded budget, with preemption/tunnel EMERGENT
  from one water-filling rule and zero magic numbers. Bounded to the discrete/integer,
  in-frame residual-mass class.
- **The order does NOT follow residual** (a lower-residual region streams before a
  higher one) ⇒ the substrate's `Argmax` under `run_rules` does not serialise the
  budget as claimed — a clean negative, reported, NOT rescued.
- **The spear does NOT preempt** (periphery still resolves under a majority-mass
  spear) ⇒ preemption does not fall out of salience ordering and needs a separate
  mechanism — reported as a negative, not patched with a threshold.
- **A floor field invents a tunnel** ⇒ the mechanism hallucinates salience from
  noise; overfitting; reported.

## 6. Prediction, stated in advance, with provisos (§3.7)

I predict **all four phenomenon arms hold, the floor is 0/100, and the spend is
bounded** — because the mechanism is a pure `Argmax`-over-residual under a
counted-down budget, and coarse-first / preemption are direct consequences of
ordering by residual mass (a large or looming structure simply HAS more residual
mass, so it wins the argmax first / drains the budget).

Provisos that could break (and what each would teach):
1. **run_rules serialisation** — I predict exactly one region resolves per pass (the
   unique argmax). If `run_rules` batches multiple bindings whose `Eq(R,Argmax)` all
   pass in one pass (e.g. an argmax tie resolving several at once), the budget could
   overshoot; C1's `spent == min(B, N_pos)` would then FAIL and reveal the batching
   semantics. *(Piloted on the `qf_frontier_goal` precedent, which serialises; stated
   as the risked mechanism.)*
2. **Compute exponent (C3)** — I predict ≈ 2 for the argmax-per-candidate scan. If it
   is worse than ~2.2 the selection is super-quadratic and the "cheap selection"
   framing is bounded; if ≈ 1 the winner idiom is cheaper than expected. Either way
   C1 (bounded spend) is the gated claim; C3 is descriptive.
3. **Floor F2** — I predict 0/100. If a scattered-noise field trips `tunnel`, the
   majority-mass + contiguity definition is too loose and the spear-detector needs
   tightening — a real (surprising) result, reported not tuned.

## 7. Scope — what is NOT shown (§8), the named frontier

- **BOUNDED to the discrete/integer, in-frame residual-mass class.** Integer
  residuals (surprise MASS), integer budget, integer positions. Nothing continuous is
  claimed (the frame/continuum invariant: the continuous lives in the cross-frame
  render/metric, not in a frame's coordinates; `coord_ints` refusing floats stays
  correct).
- **The COLOUR-SALIENCE channel (pop-out for equiluminant targets) is OUT OF SCOPE —
  the named frontier, NOT attempted.** Salience here is luminance/residual mass; a
  colour pop-out channel needs the separate categorical colour sign (MEMORY: colour
  is a sparse sign, a later faculty), not built.
- **The full 3D-heading dazzle / looming-bearing test is OUT OF SCOPE — the named
  frontier.** A true "spear flying at your head" needs objecthood + bearing/heading
  estimation (the diagnosed cortex layer). Here the spear is modelled as a
  high-residual-mass contiguous region (looming = large + high contrast), the
  tractable in-class core; the bearing-estimated looming object is the frontier.
- **This is NOT a re-implementation of `space_quantize`'s depth ladder.** The
  `SpaceQuantum.depth` + `refines`-edge route (`DYADIC_DEPTH_DESIGN.md` §5) remains
  deferred; this rung streams over a residual-mass region field, not over the
  navigation flood — they compose in principle (salience = a quantum's residual) but
  the coupling is not built here and is not claimed.

## 8. Engine / bench (filled at OUTCOME)

Engine hash + resolution path, bench condition, and the §9 byte-identity table are
recorded in `VISION_STREAM_RESULTS.md` at the confirmatory run. **This rung adds NO
Rust**; the shared canonical build is legitimate iff the Rust source is
byte-identical (§10.1 rule 4) — verified by `provenance_line()`. `data/` symlinked to
canonical (§10.2).
