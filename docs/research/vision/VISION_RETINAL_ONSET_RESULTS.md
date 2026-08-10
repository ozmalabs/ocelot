# ASYNC VISUAL ONSET EVENTS — RESULTS

Prereg: `VISION_RETINAL_ONSET_PREREG.md` (committed at `359085212f`, BEFORE any
confirmatory number). Seeds 135000–135999. Engine `01b3ebda0c50` (`own` build,
this worktree). Provenance its own step: `tests/test_engine_provenance_migrated.py`
**7 passed**.

## The build

- **Rust (DECISION primitive):** `runners/dsl/src/cognitive_tasks.rs` — new task
  kind `photon_transduce_onset`, a byte-identical peer of `photon_transduce` in
  its first three outputs, appending
  `output[3] = 20·log10((caught+1e-10)/(adaptation+1e-10))` — the visual analog
  of `cochlear_nucleus.rs::detect_onsets`' "dB above the local floor" line, the
  floor being the receptor's OWN held `adaptation`. Two Rust `#[cfg(test)]` unit
  tests pin the peer-identity and the fresh-floor-fires / adapted-floor-silent
  behaviour.
- **Graph (mint):** `seeds/retinal_onset.json` — rule `retinal_mint_onset`
  (retina, order 2) thresholds `output[3]` against `RetinaOnsetParams.threshold_db`,
  enforces the refractory (`rod.input_epoch − column.last_onset_epoch >
  refractory_epochs`), and MINTS `RetinalOnsetEvent{column_index, magnitude_db,
  epoch, logical_time}` carrying the receptor's OWN `input_epoch`. A per-task
  `onset_seen` guard makes one transient → one event.
- **Adapter (I/O only):** `domains/photon_eye.py` — `context["visual_onset"]`
  loads the seed, emits the onset task kind, mints one `RetinaOnsetParams` node,
  and seeds `last_onset_epoch`. `context["synchronous"]` lets a test drive
  `submit → run_cognitive_tasks → run_rules` deterministically. OFF by default.

## Confirmatory measurement (`tests/test_retinal_onset_migrated.py`)

`n_az=16`, threshold 6.0 dB, refractory 0, Poisson(2000)-photon bright columns,
`default_rng(135000)`, 8 dark warm-up frames before each scene.

| quantity | measured | prereg |
|---|---|---|
| `moving_count` (bar sweep, 16 frames) | **16** | ≥ 12, localised |
| `static_adapted_count` (held bright, last 8 frames, adapt ON) | **0** | ≤ 2 |
| `off_count` (SAME scene, last 8 frames, adapt_rate=0) | **128** | ≥ 16 |
| **R = moving/(static_adapted+1)** | **16.0** | **[6, 40]** ✅ |

- **Compute-∝-surprise gate: PASS.** The moving bar fired **16** onsets, one per
  column, each `column_index` localised EXACTLY to the bright column at its
  epoch. The held, adapted scene fell **silent (0)**. The adaptation-OFF control
  — identical scene, only `adapt_rate=0` — stayed **noisy (128 = 16 columns ×
  8 frames)**: the frozen floor never rises, so a sustained bright drive departs
  it every frame. The silence is therefore the floor's doing, not an artefact.
- **Headline R = 16.0**, dead-centre of the design prediction and inside the
  pre-registered `[6, 40]`.
- **Default OFF / byte-identity:** with the flag off, no `RetinalOnsetEvent` is
  minted, no `RetinaOnsetParams` node exists, and the plain `photon_transduce`
  kind is used. The Rust unit test pins the two kernels' first three outputs as
  byte-identical.

Gate: `tests/test_retinal_onset_migrated.py` **4 passed**.

## Oracle (`bash scripts/rung7_vision_bench.sh`, `data/` symlinked, §10.2)

- **BEFORE** (pristine main — onset source stashed, engine `b896651472d9`
  rebuilt): **224 passed, 0 failed** (175 s).
- **AFTER** (change present, flag off, engine `01b3ebda0c50`): **224 passed,
  0 failed** (172 s).

BEFORE == AFTER == **224/0** ⇒ the additive onset path is byte-identical with
the flag off (§9). NOTE the count is **224**, not the 222 quoted in older
prereg examples: with `data/` symlinked at this base the bench turns two
otherwise-skipped tests into passes, and the file list has grown since; the
load-bearing facts are **0 failed** and **BEFORE == AFTER**, quoted WITH their
condition (§9's "quote the baseline with its condition").

## Honest residuals

- `detect_onsets` uses an ASYMMETRIC windowed floor (latch-down / decay-up);
  this rung reuses the receptor's existing SYMMETRIC `adapt_rate` low-pass as the
  floor (the atom the project already ships). An asymmetric visual floor is a
  named successor, not built here.
- The floor used in the dB departure is the receptor's `adaptation` as passed
  into the task (the value BEFORE this observation updated it), so a fresh
  `adaptation=0` fires on the very first observation by construction — handled by
  the 8-frame dark warm-up, mirroring how `detect_onsets` initialises its floor
  to `envelope[0]`.
- In this synchronous harness the receptor `input_epoch` advances once per
  submit, so "the receptor's own clock" coincides with the frame index here; the
  event carries the per-receptor `input_epoch` (not a shared counter), which is
  the architecturally-correct source once ticks decouple per area.
- This rung mints the onset substrate only; motion / carve / depth are the
  downstream rungs that READ these events.
