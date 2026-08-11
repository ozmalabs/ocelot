# BBOX + LABEL OVERLAY — RESULTS: **SEEING BESIDE NAMING, WITH HONEST GAPS — AND THE KILLER FRAME. ALL FOUR PRE-REGISTERED FAITHFULNESS GATES PASS: THE BOX IS THE TRUE CARVED EXTENT (NOT A TIDY RECTANGLE), A LABEL APPEARS IFF A NAME IS GROUNDED (1 SURFACE NAMED, 2 SEEN-BUT-UNKNOWN), THE HOLE CARRIES NEITHER BOX NOR LABEL, AND OUR OUTPUT HAS GAPS A SELECTION HEAD STRUCTURALLY NEVER WOULD (LABEL-COVERAGE GAP 71.9 pp).**

*Pre-registration `VISION_OVERLAY_PREREG.md`, committed **`1bd59b1ea98c`** BEFORE any
faithfulness number (only the held-state RECOVERY numbers — surface velocities, carved-cell
counts, hole count — had been computed, and those are the parallax rung's carve, not this
rung's gates, exactly as the eye-view rung recorded). The four gates and their DERIVED
tolerances were fixed in the prereg; every measured number below matches its pre-registered
prediction. Nothing in the prereg was edited after the first gate number.*

## What this rung IS (extends the eye-view splat rung 118000)

The eye-view rung rendered a FAITHFUL splat read-out of the parallax carve (splat = SEEING).
This rung overlays the other channel and their correct relationship, in one frame:

- **splat = SEEING** — the carved surface (the eye-view rung's render, reused).
- **bbox = the surface's TRUE carved extent** — its exact carved-cell FOOTPRINT, NOT a
  tidied rectangle.
- **label = NAMING** — a grounded name, via `Mention -refers_to-> Concept`, attaching ONLY
  to an already-carved surface. **The label attaches to a splat; it never floats free.**

This makes the book-not-contents principle SEEABLE: a name attaches only to a percept
already carved. Three honest states, and **the gaps are the informative part**: (1) carved +
named → splat + bbox + label; (2) carved + un-named → splat + bbox, NO label (the
seen-but-unknown residual grounding acts on); (3) hole / refused → nothing.

## ENGINE PROVENANCE (§10) — NO RUST, this rung is an EMIT-ADAPTER

- Branch **`worktree-agent-a39b3d0a592db5a18`**; base SHA **`da113ec4af81`** (contains the
  three required docs + the parallax carve + `ArgminRefusal` at enum index 180). Prereg
  commit **`1bd59b1ea98c`**.
- Engine built in-tree by `scripts/engine_build.sh`: **`7041d2e6a7dd`** (own build; a REAL
  file in this worktree, replacing the inherited symlink into the shared checkout via
  `cp --remove-destination`). Re-verified AFTER measurement: **`7041d2e6a7dd`, unchanged**.
- Migrated provenance gate as its own step, FIRST: **7 passed**. `ArgminRefusal` confirmed
  at index 180 (`test_the_new_term_exists_at_index_180` passed) — this rung ADDS NO Rust and
  leaves index 180 unused.
- **ORACLE `bash scripts/rung7_vision_bench.sh` (`data/` symlinked, §10.2):** BEFORE
  **222 passed / 0 failed** (172.80 s); AFTER **222 passed / 0 failed** (188.28 s). §9 is trivial (no Rust,
  no Term, no seed) and the oracle confirms it.
- **SEED CLAIM 119000–119999 (verbatim, §3 clause 8):**
  ```
  SEED CLAIM 119000-119999: CLEAN -- no collision DETECTED.
    Scope: 824 files with seed sinks; 513 UNRESOLVED sink sites tree-wide (counted, not discarded).
  ```
  The block is ALLOCATED and drawn from by NONE of this rung's code: the held state reuses
  the parallax rung's already-burned **116000** (via the eye-view rung's `held_state`), the
  naming-channel grounding is a FIXED local teacher payload (no RNG), and every positive
  control removes a FIXED cell set / a FIXED edge (no RNG). `unknown_sinks: 0` for this rung.
- **LOAD (§ concurrency):** `os.getloadavg()` recorded in `results/overlay.json`
  (start `[0.83,0.73,0.75]` → end `[0.83,0.73,0.75]`); render+gates wall **0.7 s**; ≤2
  workers (`OMP_NUM_THREADS=2`). No wall-clock quantity is a verdict — every gate number is
  an exact/counted quantity.
- **Ledger-freshness note (honest, not mine):** `domains.seed_record --check` is RED on this
  base, but the delta is entirely PRE-EXISTING — the merged 117000 / 118000 rows were never
  measured into `seed_ledger_measured.json`, and `unresolved_sinks` reads 513 (vs committed
  512) **with AND without my untracked files** (verified by stash-isolation). This rung draws
  no seed, so `seed_record --write` is NOT mine to run (it would record other rungs' merged
  draws). Reported, not silenced.

## What the eye HOLDS (recovered by re-running the deterministic seeded carve)

Seed 116000, `shifts=[0,3,6]`, `block=8`, `grid=144`, `ref_idx=1`, `τ=√5`. The 18×18 =
324-cell field carves into **3 surfaces + 9 hole cells** (right-edge column, the
aperture-corner confabulation). **The eye has grounded ZERO object names** — the scene is
synthetic texture, not objects. The honest picture is a **toddler eye**: three flat tilted
strips it SEES and knows none of, plus a hole it declines.

| surface | residual v (= rel. depth) | image band | n cells | axis-aligned bbox | solid rectangle? |
|---|---|---|---|---|---|
| FAR | −3 | x∈[0,5] | 108 | y0–17 × x0–5 (area 108) | **yes** |
| REF / fixated | 0 (space constancy) | x∈[6,11] | 91 | y0–17 × x6–11 (area 108) | **no** (ragged) |
| NEAR | +3 | x∈[11,17] | 116 | y0–17 × x11–17 (area 126) | **no** (ragged; spills into the hole column) |

## The naming channel — REAL graph data, grounded via the teacher chain

The one identity the eye genuinely holds is its **fixation reference**: the middle surface
at residual velocity **exactly 0** (from the efference copy — space constancy). So the
naming channel grounds **exactly one** concept — `reference` — through the real teacher
chain (`WorldAdapter.learn_from_teacher`, a fixed local payload = the teacher's decision,
which creates the `taught_reference` `Concept` + a `Sign{form:"reference"}` in the lexicon)
and attaches it via a `Mention -refers_to-> Concept` edge to the surface the eye already
carved as its reference plane. The adapter's render reads the label MECHANICALLY: label IFF
`Mention -refers_to-> Concept`, resolved to the Concept's grounded sign form. **Grounding an
external object name onto texture would be INVENTING a name (forbidden §8); the fixation
reference is the only honest grounding available**, and the frame marks it as such (FAR/NEAR
are depth-order descriptors from residual velocity, NOT grounded names — they carry a box
and no label).

## THE FOUR FAITHFULNESS GATES — ALL PASS (numbers + derived tolerances)

| gate | statistic | derived tolerance | measured | verdict |
|---|---|---|---|---|
| **A — BBOX = TRUE CARVED EXTENT** | IoU(drawn footprint box, carved cells), per surface; the box's enclosed set reconstructed from its boundary by even-odd ray-casting (a round-trip, not the input returned) | **IoU == 1.0 EXACT** (tol 0; the box IS the carved cells — strongest §13 no-number outcome) | footprint IoU **[1.000, 1.000, 1.000]** | **PASS** |
| **B — LABEL ONLY WHERE GROUNDED** | a label renders for surface s IFF s's `Mention refers_to` a `Concept` | **rendered-label count == grounded count == 1 EXACT** | labels `{FAR:∅, REF:"reference", NEAR:∅}`, **n_labels 1** | **PASS** |
| **C — NO BOX ON A HOLE** | # of the 9 hole cells covered by any box; # boxes/labels on the hole | **0 EXACT** (composes with eye-view Gate-1 splat coverage 0.000) | **0/9** hole cells boxed, 0 boxes, 0 labels | **PASS** |
| **D — THE NET-CONTRAST IS HONEST** | box- and label-coverage of the 324-cell field, EYE vs NET-STYLE | net == 1.000/1.000; eye box < 1.0 AND eye label < eye box | EYE **97.2% / 28.1%**, NET **100% / 100%** | **PASS** |

**The gates have TEETH (positive controls — every one pre-registered):**
- **Gate A — a tidied RECTANGLE is CAUGHT.** The pretty axis-aligned bounding box scores
  IoU = n/bbox_area < 1.0 on both ragged surfaces: **REF 91/108 = 0.843, NEAR 116/126 =
  0.921** (FAR is solid, 1.000). A box drawn larger/tidier than the carve FAILS — measured.
  **SHRINK control:** deterministically remove NEAR's even columns → the re-derived footprint
  covers exactly the shrunk cells (IoU 1.0 to the shrunk carve) and its cell-count drops
  **116 → 62**. The box tracks the carve.
- **Gate B — the label tracks the GRAPH edge, not the renderer.** REMOVE the `refers_to`
  edge → label count **0**; ADD a second → label count **2**. The 2 un-grounded surfaces
  render NO label; the grounded one renders its grounded sign form `reference`.
- **Gate C — the net-style panel covers all 9 hole cells** (**9/9**) — the contrast that
  proves the eye's 0/9 is a refusal, not an accident.
- **Gate D — the coverage DIFFERENCE, the number that makes the refusal law seeable:**
  **box-coverage gap 2.78 pp** (the 9-cell hole the eye refuses; small because the parallax
  carve labels almost every cell) and **label-coverage gap 71.9 pp** (233/324 — the eye names
  only what it grounded; the net names everything). *A comparison can be false, a selection
  cannot* (`VISION_REFUSAL_CAPACITY_RESULTS.md`): the eye's boxes rest on comparisons that
  can refuse (holes), its labels on a grounding that can be absent (2 unknown surfaces); a
  discriminative selection head structurally cannot leave either gap.

## THE KILLER FRAME (`results/eye_view/net_vs_eye.png`)

Side by side: **THE EYE** — footprint boxes on the 3 carved surfaces, ONE grounded label
(`reference`), the NEAR box's right edge RAGGED as it traces AROUND the 9 dotted-red hole
cells (no box, no label there). **A NET-STYLE SELECTION HEAD (labelled an ILLUSTRATION, not
a measured baseline)** — three tidy boxes tiling the WHOLE field edge-to-edge, each with a
confident invented label (`wall 0.94` / `floor 0.91` / `object 0.88`), covering the hole and
the un-named surfaces alike: **100% box, 100% label, no gaps**. Ours has gaps a net
structurally never would.

## THE DELIVERABLE PNGs (all under `results/eye_view/`)

| path | what it shows |
|---|---|
| `results/eye_view/overlay.png` | THE EYE'S OUTPUT — splat backdrop (SEEING) + 3 footprint boxes (TRUE carved extent) + 1 grounded label `reference` (NAMING) + 9 dotted-red HOLE cells (refused: no box, no label). The NEAR box traces around the holes — the box is the carve, not a rectangle. |
| `results/eye_view/net_vs_eye.png` | THE KILLER FRAME — the eye's honest-gaps output (boxes 97.2%, labels 28.1%) beside an ILLUSTRATION of a can't-refuse selection head (100%/100%). Label-coverage gap 71.9 pp. |

Machine-readable: `results/overlay.json` (held state, naming, all four gate numbers, PNG
paths, loadavg, wall).

## WHAT IS NOT SHOWN (§8)

- **The eye names NOTHING here except its own fixation act.** The single grounded label is
  the fixation reference (an identity the eye genuinely holds from efference copy), NOT
  recognition of texture as an object. Two surfaces are honestly seen-but-unknown.
- **The box coverage gap (2.78 pp) is SMALL** — the parallax carve labels almost every cell,
  so the eye's only box-refusal is the 9-cell hole. The sharp contrast is the LABEL gap
  (71.9 pp). Both are reported; the box gap is not inflated.
- **The net-style panel is an ILLUSTRATION**, not a run of a real discriminative net. It
  depicts what a can't-refuse selection head yields (measured facts about real selection ops
  are in `VISION_REFUSAL_CAPACITY_RESULTS.md`: `Argmin` returns a winner from 5 identical
  candidates; the motion sensor emits 16/16 vectors on pure noise).
- **One seed's held state** (116000, the parallax primary). The gates are deterministic on it.
- **The eye does NOT compute with splats** (inherited from the eye-view rung; splats DISPLAY
  the graph, `VISION_SPLATTING_SCIENCE.md` Claims B/C refuted).

## WHAT I GOT WRONG — in full (§7)

1. **Gate B FAILED on the first run — all labels read `None`.** The teacher chain stores the
   grounded FORM as a `Sign{form:"reference", concept:"taught_reference"}` in the lexicon and
   creates the `Concept` node with **only a `name` attr, no `form`**. My first `read_label`
   read `Concept.attrs["form"]` → `None`. Fixed by resolving the grounded form through the
   Sign lexicon (`concept name → sign form`), which is the FAITHFUL read anyway — the sign
   IS the grounded name. Caught by the gate, not by inspection.
2. **The edge-deletion API is `remove_edge_unchecked`, not `del_edge`** — the first Gate-B
   teeth run would have errored; corrected before any number was recorded.
3. **The inherited `_native.abi3.so` was a SYMLINK into the shared checkout.** Building my own
   engine via `engine_build.sh` (which uses `cp --remove-destination`) replaced it with a real
   file in my worktree — never writing through the symlink into the shared tree (§11).
4. **The ledger-freshness gate is RED and it is NOT mine.** Reported above rather than
   silenced or "fixed" by regenerating another rung's seed accounting.

## LEDGER ROW (for the supervisor to merge into `VISION_PROTOCOL.md`)

*Written here, not there — `VISION_PROTOCOL.md` is not this rung's file.*

| range | used for |
|---|---|
| **119000–119999 (seed_claim CLEAN — this rung DRAWS NO seed in-block; held state reuses parallax's burned 116000; naming grounding + all positive controls are deterministic. Term enum index 180 UNUSED — NO Rust, NO Term, NO seed rule; a pure EMIT-ADAPTER)** | **BBOX + LABEL OVERLAY — SEEING BESIDE NAMING, WITH HONEST GAPS, plus THE KILLER FRAME. Extends the eye-view splat rung (118000): splat = SEEING (carved surface), bbox = TRUE carved-cell FOOTPRINT (NOT a tidy rectangle), label = NAMING (grounded via `Mention -refers_to-> Concept`, attaching ONLY to an already-carved surface). The eye has grounded ZERO object names (synthetic texture) — the honest toddler-eye picture is 3 boxes / 1 label / 1 hole. The ONE label is the FIXATION REFERENCE (residual velocity 0, the only identity the eye genuinely holds, grounded through the real teacher chain — `learn_from_teacher` → `Concept`+`Sign`); grounding an external object name onto texture would be INVENTING one (forbidden). FOUR PRE-REGISTERED GATES ALL PASS, every tolerance DERIVED (§13): (A) BBOX = TRUE EXTENT — footprint IoU 1.000/1.000/1.000 EXACT; a tidied RECTANGLE is CAUGHT (REF 0.843, NEAR 0.921 < 1.0 — the box is larger than the ragged carve); SHRINK control tracks (116→62 cells). (B) LABEL ONLY WHERE GROUNDED — n_labels 1 (`reference` on the fixated surface; 0 on the 2 unknown; 0 on the hole); the label tracks the GRAPH edge (remove→0, add→2), not the renderer. (C) NO BOX ON A HOLE — 0/9 hole cells boxed, 0 boxes, 0 labels (composes with eye-view splat coverage 0.000). (D) NET-CONTRAST HONEST — EYE box 97.2% / label 28.1%; a can't-refuse net-STYLE SELECTION head (an ILLUSTRATION, not a baseline) is 100%/100%; box-coverage gap 2.78 pp, LABEL-coverage gap 71.9 pp (233/324) — *a comparison can be false, a selection cannot* made SEEABLE: ours has gaps a net structurally never would. PNGs: results/eye_view/{overlay,net_vs_eye}.png. WHAT IT GOT WRONG: Gate B failed first (the grounded form lives in the Sign lexicon, not on the Concept node — fixed to the faithful sign read, caught by the gate); the edge-delete API is `remove_edge_unchecked`; the inherited engine `.so` was a symlink into the shared checkout (rebuilt own via engine_build.sh); the ledger-freshness gate is RED but PRE-EXISTING (117000/118000 rows unmeasured; sink delta present with AND without my files) — reported, not silenced, and NOT regenerated (other rungs' seeds). Provenance its OWN step (7 passed), ArgminRefusal confirmed at index 180; engine 7041d2e6a7dd `own` (NO RUST), re-verified unchanged post-run; oracle rung7_vision_bench 222/0 BEFORE and AFTER (§9 trivial); seed_claim CLEAN; loadavg [0.83→0.83], ≤2 workers, wall 0.7 s.** |
