# Stage 2 — Self-Run Developmental Vision Curriculum (plan)

*2026-07-16. Branch: `gamma-substrate/developmental-vision`. Stage 1 floor is done + verified (see `VISION_DEVELOPMENT_ARC.md`). This is the actionable plan for Stage 2.*

> ## STATUS (2026-07-16, end of the first execution pass)
>
> **The premise changed under the plan.** Executing it surfaced that Stage 1's floor
> does NOT grow anything — `sensory_convolution` ships six hand-designed
> `designed:1.0` kernels (incl. `centre_surround`/`edge_axis1`), **no rule anywhere
> mints a Kernel**, and the emergence measure passes random noise ~50–75% of the time
> while failing an ideal Gabor. So L0-as-written would have inherited that
> circularity. See "The T9/T11 retraction" in `VISION_DEVELOPMENT_ARC.md`.
>
> **Done:** the retraction + corrections; real kernel GROWTH (`seeds/vision_growth.json`
> — mint-on-residual + Oja's rule as graph data, no new Rust); the self-run curriculum
> (`domains/vision_curriculum.py` + `study_tick` branch + the 4th reopen arm), verified
> live (0→24 kernels, donkey=0, no per-lesson call); the real corpus (BSDS300 +
> live Jellyfin children's TV + Omniglot with *verified* ground-truth transforms).
> Gates: growth 7/7, curriculum 5/5, floor 7/7 (re-scoped), vision suites 60/60.
>
> **The measured L0 verdict is a NEGATIVE result, reported as such:** kernels genuinely
> grow, but Oja's rule adds no oriented structure over the raw image patch each kernel
> was minted from (+0.015, p=0.37, n=128/arm). Orientation is inherited from the data,
> not produced by learning. Likely cause: **no whitening** + the wrong objective
> (sparsity, not PCA, is what drives Gabor emergence). Details + the full table in the
> arc report.
>
> **NOT built:** L1–L6 (tracking / permanence / transform-invariance / objecthood /
> naming / escalation). `VISION_KINDS == ("babble",)`; an unbuilt level reports
> attempted=0 rather than faking a pass (gated by
> `test_unbuilt_levels_are_not_faked`).
>
> **Corrections to this plan's own assumptions**, found while executing it:
> - The corpus section's SAYCam-style video is **not obtainable** (Databrary
>   application). Superseded by the live Jellyfin library the repo already has an
>   adapter for — real children's TV, but broadcast, **not egocentric**.
> - "no new Rust expected" held, but **`net_collapse` is the wrong tool for kernel
>   learning** (needs a `ReflexNet→NetworkAssemblage→WeightTensor` subgraph only
>   Python mints; trains only the last layer over a fixed random one).
> - The verification block's CLI is wrong: the daemon's `--seeds` accepts only
>   `full|chat`, and `--study-every` is **int ticks**, not `2s`.
> - `scattering_feature.render_trace` cannot stage transforms (it min/max-normalises
>   per axis, erasing translation+scale and turning rotation into rotation+stretch).

## Goal

The agent **self-runs** a staged curriculum that develops vision from the Stage-1 floor upward, growing its own codebook via the `sd_*` loop, persisting via `teach()`, and acquiring learned recognisers through the net spine. Mirror `VOICE_CURRICULUM.md`: donkey=0, data-driven modules with growth measures, `curriculum_study` + existing seed-rule lifecycle. Endpoint = developmental capability itself (no external benchmark).

**The unification:** vision prediction-error and net surprise are the **same currency**. `net_collapse` (surprise/NLMS descent, drained inside the `run_rules` fixpoint) learns the readout; the `sd_*` loop grows the symbolic codebook that proposes; "bins propose, continuous decides."

## Prerequisites (all done)

- PR #16 net spine merged into the active branch ✓ (NetForward, `net_collapse`, cascade nets, net economy, external basin-gating, `codebook_scope`).
- Rust Term floor ✓ (`ChangeDetect`/`TemporalDiff`/`Foveate` + `vision_primitives.rs`).
- `vision_floor` seed + `vision_world` adapter + teach hook ✓.
- Region-as-belief (`interior_inherited` + `grounding_label` + contradiction-split) ✓.

## The curriculum (merged from the literature steer + the stage0-2 ladder)

`contrast → motion → foveation → tracking → permanence → transform-invariance → objecthood → naming`

- **L0 Active-gaze babble.** Curiosity-driven dwell + foveation selects the training signal (dwell where prediction error is high — the curiosity drive). Kernels **grow**: `vg_mint_kernel_from_patch` mints a `Kernel` from a real unexplained image patch and `vg_learn_kernel_oja` learns it by Oja's rule (`seeds/vision_growth.json`).
  > **CORRECTED 2026-07-16.** As originally written this level said kernels "grow (`keep_discriminative_kernel`)" and measured "which biological kernel-classes emerged". Both were unsound and would have inherited the Stage-1 circularity: `keep_discriminative_kernel` only SELECTS from six hand-designed `designed:1.0` kernels (no rule mints a Kernel anywhere), and the emergence measure — the `_is_center_surround`/`_is_oriented` sign classifiers — is passed by **random noise** ~50–75% of the time while an **ideal Gabor fails it**. See "The T9/T11 retraction" in `VISION_DEVELOPMENT_ARC.md`.
  >
  > *Growth measure (replacement):* count of **grown** (`designed:0.0`) kernels; and structure measured **spectrally** (anisotropy of the 2D power spectrum: ideal Gabor ≈ 0.87, ideal DoG ≈ 0.00, random 7×7 ≈ 0.15) — **always reported against a random-kernel control and a raw-image-patch control**. The raw-patch control is the load-bearing one: a minted kernel is *initialised as an image patch*, so orientation inherited from the data is not orientation produced by learning. The claim is only ever the *delta over that control*, with a permutation test.
- **L1 Tracking / temporal slowness.** Regions persist across frames; slot identity; adjacent views of the same object stay related (Földiák slowness). *Growth:* distinct recognized shapes rise; a re-decoded shape after `codebook_epoch` bump is `recognized`.
- **L2 Permanence / occlusion (elevated).** visibility→0 → held belief persists (latent imagination — the persistent-observation-BELIEF precedent from `quanta_navigation`); impossible reappearance → surprise residual → gap. *Growth:* a moving object keeps one identity across frames through occlusion.
- **L3 Transform invariance.** Rung-1 `TransformDecode` — rotation/translation/scale of a recognized shape = a pose quantum, not a new shape (the ink precedent). *Growth:* zero-mint transform reads on held shapes.
- **L4 Objecthood / composition.** Figure-ground + multi-part objects via the `sd_*` composition rung (Omniglot-stroke-proven). Region-as-belief interior-inheritance + summary-stat `CapabilityAxis` carry the object's interior + texture. *Growth:* multi-part shapes recognized from parts.
- **L5 Naming (net spine).** `teach()` a grounded Concept/term for a recognized object-class into the lexicon (language-bootstrap coupling); basin-gated net readout as the verdict layer. The net spine admits learned readout nets (`NetForward` + `net_collapse`) grounded by the ventral codebook, basin-gated by `ShapeDecode` residual (`reflex_ground_residual`). Cascade nets for depth-by-residual. Net economy admits/retires by `worth = residual − cost`. *Growth:* a net is `adopted` (not `retired`); ablate the net → recognition regresses.
- **L6 Autonomous curriculum escalation.** `standing_self_improvement` concern + `curriculum_study` reopen-on-growth. When the ventral codebook can't explain a region (residual), file a gap (`gap_awareness`) → mint a quantum (`sd_mint_quantum`) → `teach()` persists → re-decode on `codebook_epoch`. donkey=0.

(Dorsal/ventral coupling is a thread throughout: motion/tracking = dorsal; contrast/objecthood = ventral; permanence binds them.)

## Self-run mechanism (mirror `domains/voice_curriculum.py` + `VOICE_CURRICULUM.md`)

- `curriculum_study.install_curriculum("Vision Development", lessons, source=real-image/video corpus under data/vision_curriculum/)` mints one `Curriculum` + one `StudyLesson{status:'queued', text_path, kind}` per corpus chunk, `kind in {babble, constancy, invariance, composition, recognition, binding}`.
- A **vision-lesson processor** `learn_vision_from_lesson(agent, text, kind)` routed by the lesson's `kind` attr (a graph attr the pick reads, NOT a Python content sniff). Each lesson feeds the `sd_*` loop + `teach()`; recognition lessons additionally drive a `TrainingJob` (wire the deferred live-trace harvest here). The lesson SEQUENCE + reopen-on-growth are the existing `study_lesson_*` seed rules, unchanged.
- The daemon `--study-every` cadence advances one lesson per tick, autonomously. Reopen: as the vision codebook grows (`vision_codebook_epoch` bumped on new `CapabilityAxis`/`LatentDimension`), a lesson blocked on a missing prerequisite re-arms via `study_lesson_reopen_on_growth`.

## File-level changes (representative)

**Seeds (new):**
- `seeds/vision_curriculum.json` (new) — the staged lessons L0–L6, `study_lesson_*` reopen-on-growth, `vision_codebook_epoch`. `depends_on`: `vision_floor`, `curriculum_study`, `gap_awareness`, `reflex_net`, `net_economy`, `standing_self_improvement_concern`.

**Python (thin adapters / seed-builders only — no decisions):**
- `domains/vision_curriculum.py` (new) — `learn_vision_from_lesson` processor + `install_curriculum` grounder, mirroring `voice_curriculum.py`.
- Corpus under `data/vision_curriculum/` — child-perspective egocentric video / natural-image chunks (per steer #1: child-perspective video, not ImageNet).

**Tests:**
- `tests/test_vision_curriculum_migrated.py` (new) — staged L0–L6 growth, donkey=0, the ablations.

## Gates (donkey=0, the voice-curriculum verification shape)

1. **BEFORE:** enumerate the agent's grown kernel codebook / minted `CapabilityAxis` / `LatentDimension` counts and 3 concrete failures (a shape it can't recognize; a transform it mints-as-novelty instead of reading as a pose; a motion it can't bind to identity).
2. Run the study loop autonomously for the queued lessons (no human input, no per-lesson hand call — `study_tick` in a loop / the daemon cadence).
3. **AFTER:** the counts rose materially; the 3 failures now succeed (the shape `recognized`; the transform read as pose via `TransformDecode`; the motion bound to identity); a re-perception of a held-out scene shows richer codebook coverage.
4. **donkey=0 throughout;** the lesson SEQUENCING + growth decisions are seed rules. Ablations: removing the reopen rule stops re-arming; removing `net_collapse` regresses L5; removing `keep_discriminative_kernel` regresses L0; removing the region-as-belief `vf_contradiction_split` regresses L2/L4.

## Verification (end-to-end)

```bash
cd research/experiments/gamma-substrate
cd runners/dsl && maturin develop --release && cd ..          # no new Rust expected
# REGRESSION GATE. NOT `-k migrated` and NOT a failure COUNT — both are substring
# selectors, and `-k` matches "pro-VISION-al" (§12). The oracle is the NAMED file list:
bash scripts/rung7_vision_bench.sh          # 212 passed/10 skipped without data/; 222/0 with
# "no NEW failures" is checked against the LIST, never against a number:
python3 scripts/failure_baseline.py verify --only-fast 20
PYTHONPATH=runners/dsl/python:. python -m pytest tests/test_vision_curriculum_migrated.py -q
# live developmental run — daemon self-advances the vision curriculum
PYTHONPATH=runners/dsl/python:. python3 scripts/jabberwock_daemon.py --seeds vision_floor,vision_curriculum --study-every 2s
python3 scripts/jbw_talk.py "what did your vision curriculum grow?"   # grounded self-model
```

## Execution approach (learned from Stage 1)

- **Pre-ground each agent** (exact file:line sites + precedent code + the T7/T8 contract) so it implements rather than explores — the first Stage-1 workflow churned on an open-ended T7; concrete-prompt agents succeeded first-try.
- **Agents on GLM 5.2** (omit the `model` override → inherit the session model). Sonnet was a Claude-subscription hangover, not an API choice.
- **Sequential workflow with verify gates per stage**, stop-on-fail; **don't git commit** mid-flow — review/commit at the end.
- **The linchpin stage gets a self-test bar** (like T7's byte-parity); later stages get the existing-test green bar.

## Honest notes

- L5 (naming via the net spine) is where the `codebook_scope` human-built boundary bites hardest (per-pathway basins). Budget for it.
- The live-trace harvest into `TrainingJob` (mocked in PR-16) must be wired for L5 — flagged as deferred work.
- The POS-cold-slab migrated-gate failures are NOT this work's concern (recount-line frontier; the stashed WIP addresses them). Do not "fix" them by metric surgery — they're vision-unrelated. **They are identified by NODE ID in `results/failure_baseline.json`, not by the count "5"** — the count was written when it was 5, and a count cannot tell you whether the entries you are stepping over are still the same entries (2026-07-21; a declared 19-failure baseline in this tree became 144 nodes with nobody negligent). Check membership, never arithmetic.
