# PREREG — PER-AREA RESIDUAL SALIENCE ON THE EVENT STREAM (Rung 4 of the photon-eye migration)

**Seed block: 164000–164999** (`check_claim(164000, 164999)` CLEAN — no
collision detected; not declared in any ledger block; not in
`VISION_PROTOCOL.md` (which ends at 163999); drawn once at
`default_rng(164000)`). Committed as its OWN commit BEFORE any confirmatory
number (corrective to Rung 3, which bundled its prereg into the impl commit).

Verbatim `python3 scripts/seed_claim.py 164000 164999`:

```
SEED CLAIM 164000-164999: CLEAN -- no collision DETECTED.
  Scope: 864 files with seed sinks; 583 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

## The claim

Salience is computed event-natively as the RESIDUAL of the async onset-event
stream after the coherent structure is explained. The salient region is the
SURPRISING one — the onset activity NOT accounted for by the dominant
common-fate motion. This is compute-∝-surprise made into an attention signal:
**salience = the residual (the under-compressed).**

It re-expresses the RGB-pipeline residual-salience result (block 157000: on a
forward walk, the RESIDUAL after egomotion cancellation ranks the independent
mover ABOVE the egomotion-swung background, where RAW salience fails) onto the
EVENT STREAM. The carve (Rung 3, `retinal_common_fate_carve` /
`VisionPolygon`) gives the coherent/predicted structure — the dominant
common-fate group is the "explained" background, the event-native analogue of
157000's dominant-mode egomotion. The residual against that dominant motion is
the salience.

**Egomotion (157000) ⟷ dominant common-fate velocity (here).** In 157000 the
dominant-MODE flow vector is the egomotion; a track's salience is its residual
after cancelling that egomotion. Event-natively the dominant common-fate group's
velocity `v_dom` (columns-per-epoch, `Δc/Δe`) is the coherent background flow; a
firing column's salience is its residual after cancelling `v_dom`.

**HONEST SCOPE (stated, not hidden):** the photon eye is a 1-D AZIMUTH STRIP, so
this salience is per-column over that strip (a per-AREA salience field, the area
being the retina). A true 2-D salience map needs the retina extended to
elevation columns first — a NAMED follow-on, NOT this rung.

## The mechanism (fixed before the confirmatory run)

- **Rust kernel `retinal_residual_salience`** (a new pure CognitiveTask kind,
  peer of `retinal_common_fate_carve` / `retinal_event_motion` — NO new DSL Term
  enum variant): payload `[n_az, max_gap, vel_tol, k, c_0, e_0, …, c_{k-1},
  e_{k-1}]` — identical header to the carve (retina width, the two common-fate
  segmentation params, the `k` onset events as column index + own epoch). It:
  1. reduces the events to one mean epoch per firing column, sorted by column;
  2. SEGMENTS the sorted firing columns into maximal COMMON-FATE runs (the SAME
     segmentation the carve uses — spatial contiguity `≤ max_gap`, shared sign,
     magnitude within `vel_tol`); each run's velocity `v_run = Δc/Δe` is its
     least-squares slope (columns-per-epoch, the Rung-2 regression);
  3. picks the DOMINANT run = the run spanning the MOST firing columns (ties →
     most total events) — the coherent background; `v_dom` is its velocity (0
     when no run reaches ≥2 columns, i.e. no coherent motion to cancel);
  4. per firing column, emits `raw_salience = |v_run|` (the column's own
     common-fate SPEED — the "swung background" reads HIGH, the failing signal)
     and `residual_salience = |v_run − v_dom|` (its departure from the dominant
     motion — the background is the dominant motion so its residual is ~0; an
     independent mover with a DIFFERENT velocity has a large residual).
  Output is a FIXED per-column layout of stride 3:
  `[fired, raw_salience, residual_salience]` for each column `0..n_az`; a
  non-firing column is all-zero. `v_dom = 0` ⇒ `residual_salience == raw_salience`
  (nothing to cancel — the event-native analogue of 157000's no-egomotion
  identity control).
- **Seed `seeds/retinal_salience.json`** rule `retinal_mint_salience`: matches
  every `RetinalColumn` against the done salience task and mints a
  `RetinalSalience{column_index, raw_salience, residual_salience, epoch}` node
  (edged `retina -has_salience-> sal`, the graph data the fovea reads) iff
  `output[index*3+0] == 1.0` (this column fired), once per column-epoch via a
  `salience_epoch` guard. No threshold on the salience value — every firing
  column gets a candidate carrying both scores (the fovea's `ArgminUnique` over
  `Log(salience)` decides, 160000). Gate held as DATA on a `RetinaSalienceParams`
  node (`enabled`, `max_gap`, `vel_tol`).
- **OFF by default (§9):** engages only under `context["visual_salience"]`, which
  creates the `RetinaSalienceParams` node (and implies the onset path); absent it
  the rule cannot match and no salience task is ever created. Onset / motion /
  carve / coarse paths are byte-identical.
- **Python is mechanical only:** the adapter (`GraphEye.settle_salience`) reads
  `RetinalOnsetEvent` attrs (`column_index`, `epoch`) — the EVENT STREAM, nothing
  from the raster — packs them into the salience task payload (with the two
  segmentation params read as DATA off `RetinaSalienceParams`), and reads the
  `RetinalSalience` nodes back (`GraphEye.salience_percepts`). No decision in
  Python; the salience DECISION is the Rust kernel + the graph rule, and the
  attention SELECTION is the existing fovea grammar (160000).

## Headline QUANTITY + pre-registered interval

On a controlled scene with a coherent background common-fate motion spanning
many contiguous columns PLUS an independent surprising element (a disjoint span
of columns whose onset events carry a DIFFERENT common-fate velocity), driven
through the REAL mint rule:

> **RESIDUAL salience ranks the surprising element ABOVE the coherent
> background — the mover is TOP-1 by residual salience and the mover-vs-background
> residual AUC ∈ [0.95, 1.0] (exactly 1.0 on the noiseless synthetic) — where
> RAW salience does NOT: the raw (own-speed) mover-vs-background AUC ≤ 0.6 (in
> the crisp kernel scene, where the background sweeps FASTER than the mover, raw
> AUC = 0.0 — raw ranks the fast background ABOVE the slow mover).**

Because the synthetic sweeps are noiseless the per-run velocities are exact, so
the residual ranking is exact (AUC = 1.0), not a distribution; the interval
`[0.95, 1.0]` records the pre-registered pass band.

## Able-to-fail controls (read MEASURED values; no constant re-derived in Python)

1. **HEADLINE — mover isolated by residual, missed by raw:** mover TOP-1 by
   residual, residual fg-vs-bg AUC ∈ [0.95, 1.0], raw fg-vs-bg AUC ≤ 0.6.
2. **SILENCE — fully coherent field → no high salience anywhere:** every column
   on ONE common-fate diagonal (one dominant run covering all) → every
   `residual_salience ≈ 0` (max residual salience below the mover scene's mover
   residual, and below a small floor) — the compute-∝-surprise silence. RAW is
   NOT silent there (it reports the coherent sweep's speed everywhere), so the
   control also shows residual ≠ raw when there IS a dominant motion.
3. **STATIC / DARK → no events → no salience:** a dark field fires no onset
   events → the kernel returns all-zero → NO `RetinalSalience` node is minted.
4. **NO-DOMINANT-MOTION identity → residual == raw:** a field with no coherent
   run (`v_dom = 0`) → `residual_salience == raw_salience` for every firing
   column (nothing to cancel; 157000's no-egomotion control, event-native).
5. **DEFAULT OFF:** flag off ⇒ no `RetinaSalienceParams`, no salience task, no
   `RetinalSalience` node, plain `photon_transduce` kind; existing paths
   byte-identical.

## Merge-block criterion (supervisor checks)

Salience is computed from the async EVENT STREAM (`RetinalOnsetEvent` column +
own epoch + the motion/carve residual), NOT from the coarse `retinal_field`
raster and NOT from the existing raster `shape_salience` /
`order_n_shape_salience` on the pixel field. The gate source-audits
`GraphEye.settle_salience` for `RetinalOnsetEvent` / `column_index` / `epoch` and
asserts the forbidden raster / frame-diff / raster-salience symbols
(`retinal_field`, `PhotonExposure`, `retinal_flow_depth`, `_previous_field`,
`vector_field`, `native.segment`, `shape_salience`, `order_n_shape_salience`) are
absent.

## Provenance (§10)

`engine_provenance()["source_match"] ∈ {"own", "shared"}` — never a pinned hash,
never `== "shared"`.

## Oracle (§9)

`bash scripts/rung7_vision_bench.sh` = 0 failed, and BEFORE == AFTER with the
salience flag OFF (both sides).

## NO TIMING CLAIM

Other rungs run in parallel; this claim is CORRECTNESS (residual salience ranks
the surprising element above the coherent background), never milliseconds.

## Named follow-ons / residuals

- **2-D salience map** (azimuth×elevation) needs the retina extended to elevation
  columns first — named, not this rung.
- **Wiring into the fovea end-to-end** (feed `RetinalSalience` nodes to the
  160000 `FoveaCandidate` / `fovea_resolve` `ArgminUnique`) is left to a follow-on;
  this rung EMITS the salience as graph data the fovea CAN read (the
  `RetinalSalience` node with `residual_salience`), and proves the ranking, but
  does not itself re-run the fovea selection.
- A mover whose velocity happens to equal `v_dom` (moving exactly WITH the
  background) is invisible to residual salience — correct by construction (it is
  not surprising), the 1-D analogue of the aperture limit, named not solved.
