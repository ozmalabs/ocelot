# The Thought-Manifold — a Train of Thought is a Trajectory Through a Manifold (block 348000)

## The closure (the arc's origin, landed)

The arc began with the utterance realized as a **deformation of a shape** — a spoken
clause is a controlled distortion of a held form, heard back and scored by its residual
(the block-345 self-dialogue base). Turned inward (block 346) that became an unspoken
conversation with yourself; given an adjustable breadth (block 347) it became a train
that can hug the is-a spine or wander associatively. This block closes the arc by naming
what all of that always was:

> **A train of thought IS a trajectory through a manifold.**

Every piece built in 341–347 is a facet of that one geometric fact:

- each **thought** is a point on the manifold (a concept, at an aperture);
- the **succession** of thoughts is the **trajectory** (the path traced);
- **attention_width** (block 347) is the **tangent breadth** — how wide a neighbourhood the
  trajectory may step into at each point;
- the **set-point** is the **required tube** the trajectory is steered to stay within;
- the **feedback loop** is **trajectory control**: the residual (deviation from the tube)
  drives the width to steer back;
- block-347's `novelty_stalled` is the trajectory reaching the manifold **boundary**.

This is the arc closure — "like it always was."

## The SIBLING verdict (honest naming)

The same discipline that made `attention_width` a *sibling* of aperture (a distinct axis in
a different space, not a reuse of `resolves`/`grain`) applies to the manifold itself. The
`ThoughtManifold` built here is a **SIBLING of `future_option_risk.FutureManifold`**, not an
instance of it:

- **Shared structure:** tube = admissible region; projection/deviation = departure from that
  region; boundary = termination. That tube/projection/deviation skeleton is the same.
- **Different space:** `ThoughtManifold` lives over **concept-signature space** (the concept
  graph), whereas `FutureManifold` lives over action / world-state `ShapeSlice` cells.
- **NOT reused:** it does **not** reuse `ShapeSlice`, `action_count`, `intervention_magnitude`,
  or the commit-wait-refine machinery — those are action-specific. Only the abstract
  tube/projection/deviation structure is shared.

## The DISCRETE-QUANTA correction (corrects block 347's float axis)

Block 347 expressed `attention_width` as a **float on a continuum** (`width ∈ [0,1]`,
`0.0/0.5/1.0`). The substrate's premise is **discrete quanta** — never a continuum, and also
**not** a coarse hardcoded int. This block re-expresses the breadth axis, the deviation, and
the segment steps as **`k * quantum` at a configurable grain**:

- **width** is `k` quanta of breadth at a configurable grain: `width = k * grain` (integer `k`).
  The grain is the resolution dial — make it finer for more breadth levels, never by reaching
  for a raw float. A caller-supplied `width` is **snapped** the substrate's native way,
  `k = round(width / grain)` (exactly `analogy_search._round_to_vocab` / `observer_aperture`
  grain: a value snapped onto `k * quantum`), then clamped to `[0, WIDTH_MAX_SHELL]`. Every
  float that ever appears is only an *input* snapped on entry — no continuum leaks in.
- **deviation** is an **integer count** of reached concepts outside the tube (the natural
  quantum of the concept graph — whole concepts), never a float fraction.
- **segment steps** widen/narrow by **±1 quantum**, compared against **quantum thresholds**
  (counts), not float thresholds.

**Resolution preserved via fine quantum, behavior preserved.** The default grain
(`WIDTH_QUANTUM = 0.5`) snaps 347's demonstrated widths `0.0 → k=0`, `0.5 → k=1`, `1.0 → k=2`,
reproducing the goal / children+siblings / associative train shapes exactly. This corrected
347's float axis **in place** (the `scripts/gen_rung3_attention_width.py` sweep now runs
`k = 0,1,2`) and the block-347 experiment still passes 4/4 — behavior preserved, ontology
corrected. Finer resolution is a finer grain, never a raw float.

## The mapping (what this block builds, what it defers)

| geometry | this block | note |
|---|---|---|
| **tube** = the required region | a **concept-region** set-point (topic + its is-a cone) | the aperture-grain tube is deferred to 349 |
| **deviation** = departure from the tube | integer count of reached concepts outside the region → **steers the width** | discrete quantum |
| **width** = tangent breadth | integer quanta (shells `k`) admitted at each point | block-347 quantized axis |
| **boundary** = termination | 347's `novelty_stalled` (segment's own train stalls) / tube exhausted (`converged`) | the manifold boundary |

The **aperture-grain tube** — a set-point `observer_aperture` whose grain sets tube width
(vague grain ⇒ wide tube/freeform, sharp ⇒ narrow tube/focus) — is the confirmed-literal
form, but its vague↔sharp dial only bites when concepts carry the dynamical/qualia dimensions
grain acts on, which the plain is-a seed lacks. It is **deferred to block 349** (seed the
qualia substrate). Both are valid tubes; this block names + builds the concept-region one and
leaves the aperture-grain hook ready.

## Result (measured, pure graph, teacher-free, no LLM)

Seed: the multi-hop is-a DAG (`poodle`/`beagle → dog`, `cat → mammal`, `dog → mammal`,
`sparrow → bird`, `mammal`/`bird → animal`). Run teacher-free via
`PYTHONPATH=runners/dsl/python:. python3 scripts/gen_rung3_regulated_manifold.py` (exit 0).
Everything reported in **discrete quanta** — integer widths, integer deviation counts. A
teacher-call spy counts external-answerer invocations. **All five claims PASS honestly.**

| claim | result (verbatim from the experiment) |
|---|---|
| **C1 NARROW TUBE → FOCUS** (tube = poodle is-a cone, start inside) | **PASS** — `width_trace [2,1]` (narrows/focus), `deviation_trace [0,2]`, `stop=converged`, `ask_spy=0` |
| **C2 TUBE-OUTSIDE → STEER** (start=poodle, tube=bird branch) | **PASS** — `width_trace [0,1,2,2,2,2,2,2]` (WIDENS +1/segment then clamps at `WIDTH_MAX_SHELL=2`), `deviation_trace [3,1,1,1,1,1,1,1]` (integer deviation FALLS 3→1 as widening steers toward the tube), `ask_spy=0` |
| **C3 MISMATCH DRIVES WIDTH** (same start/width, generous tube vs perturbed/moved-away bird tube) | **PASS** — perturbing raised `dev0` 0→3, which pushed the next-segment width up 1→2. Deviation genuinely drives width |
| **C4 TEACHER-FREE on the HELD path** | **PASS** — `on_unknown='return'` → `ask_spy=0` across all segments. Wired as `on_unknown='ask'` the floor fires exactly once, and ONLY on the genuinely-UNHELD boundary concept `animal` (topmost is-a ancestor, no out-edges to derive) — held concepts never trigger it |
| **C5 LIMITING CASE** (everything-tube → deviation always `[0,0,0,0,0,0]`, comparator off) | **PASS** — first segment reach `['poodle','mammal','animal']` is byte-identical to a single plain block-347 `run_inner_conversation`, every segment terminates the plain-train way (`seg_stop=converged`, matching the plain stop). Faithful superset |

## Honest record: two claim assertions were mis-stated first — the ASSERTIONS were corrected, not the substrate

Verified via the actual `ask_fn` call path in `domains/self_dialogue.self_answer`:

- **C4** first draft wrongly demanded `ask_spy=0` even under `on_unknown='ask'`. The ask floor
  legitimately fired on `animal` — the topmost is-a ancestor with no `causal_influence`
  out-edges, so `held_frames_for_topic` returns `[]` and the external floor correctly engages.
  That is correct floor behavior on a genuinely-unheld boundary concept, not a teacher call on
  the held path. The corrected claim proves (i) the held path is teacher-free under
  `on_unknown='return'`, and (ii) under `'ask'` the floor only ever fires on unheld concepts.
- **C5** first draft used `max_segments=1` and asserted the LOOP-level `stop_reason` be
  `converged`/`novelty_stalled`; the loop returns `max_segments` (an everything-tube always has
  more admissible region to visit — `bird/cat/dog/beagle/sparrow`). The corrected claim asserts
  on the PER-SEGMENT dynamic (each `seg_stop=converged`, first segment == plain train), which is
  the accurate meaning of "reduces to a single `run_inner_conversation`".

## Honest bounds

The trajectory hits the manifold **boundary** when a segment's own train stalls
(`novelty_stalled`) or the tube/frontier is exhausted (`converged`). Only the
**concept-region** tube is demonstrable on the plain is-a seed (proved here).

## Deferred (honest, not faked)

- **Aperture-grain tube** (vague/sharp qualia grain sets tube width) — **block 349**; needs
  `seeds/qualia_space.json` + the dynamical coords the plain is-a seed lacks.
- **Global workspace** (produce seriality via broadcast/competition) — **block 350**.
- **Gated dimension-minting** (on accumulated persistent residual) — **block 351**; needs the
  qualia substrate.

## Guardrails

- `.so` md5 unchanged: `7efe75eba05b006cafd15dbb4b7da246` (python/JSON only, Rust never rebuilt).
- Protected READ-ONLY files untouched (`runners/dsl/src/can_ops.rs`, `domains/can_junction_tree.py`,
  `domains/can_native_bp.py`, `domains/model_reader.py`); `domains/conceptualizer.py` untouched
  (no-Python-decision audit stays green); block 346/347 experiments still pass.
- Additive only; teacher-free at loop time (no LLM); no model/venv/`/applications`.
- Committed block-348 only, add-by-name.

## Artifacts

- `domains/regulated_train_of_thought.py` — the `ThoughtManifold` trajectory controller
  (`run_regulated_train_of_thought`, `_region_from_topic`, `_trajectory_deviation`); concept-region
  tube; discrete-quanta width + integer deviation.
- `domains/train_of_thought.py` — the quantized `attention_width` axis (`WIDTH_QUANTUM`,
  `WIDTH_MAX_SHELL`, `snap_width_to_quanta`, `breadth_stance` on integer shells `k`); corrects
  block-347's float axis (behavior preserved).
- `scripts/gen_rung3_regulated_manifold.py` — the experiment (C1–C5, teacher-call spy).
- `scripts/gen_rung3_attention_width.py` — the block-347 experiment, updated to sweep integer
  quanta `k = 0,1,2` (still 4/4).
