# PHASE 5 — Calibration, text ablation, submission-readiness — RESULTS

Written AFTER measuring, against the contract in `PHASE0_GROUND_TRUTH.md` and
building on PHASE 1–2 (`PHASE12_RESULTS.md`), PHASE 3 (`PHASE3_DERISK_RESULTS.md`)
and PHASE 4 (`PHASE4_RESULTS.md`). Provenance tags:

- **[RUN]** executed here, real number, reproducible in this workspace.
- **[BUILD]** produced by an actual build/seal in this environment.
- **[UNVERIFIABLE-LOCALLY]** the exact action is given but the thing it needs (the
  organizer's live endpoint, the sealed realized outcomes, a real registry pull,
  a team id) is not available here, so it is NOT claimed as measured.

**No score is fabricated.** Local runs are always `RAW_UNRANKABLE` (PHASE0 §5.1);
every local metric below uses a **hand-made realized proxy** (the transparent
common-factor instrument from PHASE 2, `run_variogram_eval.make_realized`) and is
reported as a RELATIVE before/after or full/blank number, never as a leaderboard
value. The sealed outcomes are not available.

Environment (unchanged from prior phases): `.bigtmp/t2venv` (py3.13 + the REAL
`qfbench2-common 2.3.1` + `qfbench2_track_forecasting` scorer + `qfbench2-smoke`),
`.bigtmp/track2` (104 units). Scoring uses the scorer's OWN
`qfbench2_common.scoring.crps.crps_composite` in-process (cross-checked to the
reference CLI to 6+ sig figs in PHASE 2).

---

## 1. Calibration — randomised PIT, before/after

### 1.1 What was measured, and against what

The PoC reported PIT KS **0.0926** (over-dispersion). We measure the **randomised
PIT** (Czado et al. 2009 — the ties-corrected transform for ensemble forecasts)
of the SHIPPED numeric core (`JointDrawEngine`, the phase12 arm) on the local
realized proxy:

```
u = ( #{draws < y} + V·#{draws == y} ) / m ,   V ~ U(0,1)
```

pooled over **22 multi-asset F3 units × 8 realized seeds × all cells**
(`n_pit ≈ 1300` points), and take the one-sample KS distance of the pooled PIT to
Uniform(0,1). We also report the scorer's OWN tail metric (`|coverage_a − a|`,
PHASE0 §5.4) so the story is told in the harness's currency. `n_draws=1000`,
model seed 0. [RUN] — `run_calibration_eval.py`.

The tightening knob is a **dispersion scale** `disp_scale` on the innovation
kernel width:  `x' = mean + disp_scale·(x − mean)`. `disp_scale < 1` tightens.
It is **contract-preserving** (a per-cell affine map on already-drawn values →
draws stay finite, cell occupancy and row count unchanged) and **variogram-
preserving** (it scales the marginal std only; cross-asset correlation is
scale-invariant, so the PHASE 2 joint structure is untouched).

### 1.2 The before picture — the forecaster IS over-dispersed [RUN]

At `disp_scale=1.0` (the phase1/2 behaviour) the pooled randomised-PIT histogram
(10 bins over [0,1]) is a pronounced **central hump**:

```
bins:  [71, 11, 62, 143, 311, 328, 167, 64, 45, 62]      KS = 0.1884
                        ^^^^^^^^  mass piles in the middle  = OVER-DISPERSED
```

A central PIT hump is the textbook over-dispersion signature (the forecast bands
are too wide, so the realized lands near the median too often). This reproduces
the PoC's over-dispersion finding qualitatively on the real contract. (The KS
0.1884 here is on the hand-made proxy and is not directly comparable to the PoC's
0.0926 on its own DGP — different realized — but the DIRECTION is the same.)

### 1.3 The scan — and the over-tightening trap the plan warned about [RUN]

Tightening `disp_scale` down flattens the hump, but the scorer's **tail penalty
blows up** because narrowing the body also narrows the extreme quantiles, so
coverage error at 0.01/0.05/0.95/0.99 grows:

| disp_scale | KS | marginal CRPS | tail penalty | note |
|---|---|---|---|---|
| 1.00 (baseline) | 0.1884 | 0.2578 | 0.2392 | over-dispersed body |
| 0.95 | 0.1806 | 0.2500 | 0.2462 | |
| 0.90 | **0.1690** | **0.2423** | 0.2509 | **chosen** |
| 0.85 | 0.1591 | 0.2347 | 0.2538 | KS lower, tail worse |
| 0.70 | 0.1347 | 0.2130 | 0.2706 | |
| 0.50 | 0.1027 | 0.1878 | 0.3197 | |
| 0.40 | **0.0753** (argmin KS) | 0.1779 | 0.3795 | **tail +0.14 = over-tightened** |
| 0.30 | 0.0987 | 0.1708 | 0.4824 | KS turns back up (now UNDER-dispersed) |
| 0.20 | 0.1826 | 0.1683 | 0.7046 | badly under-dispersed |

`argmin(KS)` is at `disp_scale ≈ 0.40`, but that is exactly the over-tightening
the plan cautioned against: **CRPS punishes both tails**, and the tail penalty
(0.239 → 0.379, +58%) says the extreme quantiles have become far too narrow. So
we do **NOT** pick `argmin(KS)`.

The result is **robust across realized modes**: the `signed` co-movement realized
(anti-correlated EM crosses included) gives the same shape — KS min at ~0.40, tail
monotonically worse as you tighten. [RUN]

### 1.4 The after picture — the tail-guarded choice [RUN]

We pick the scale that (a) reduces KS vs baseline AND (b) does not worsen the
scorer's tail metric beyond 5% AND (c) does not worsen marginal CRPS. That is
**`disp_scale = 0.90`** — a mild 10% tightening:

| metric | before (1.00) | after (0.90) | change |
|---|---|---|---|
| randomised-PIT KS | 0.1884 | **0.1690** | **−0.0194 (−10.3%, better)** |
| marginal CRPS | 0.2578 | **0.2423** | −0.0155 (better) |
| tail penalty | 0.2392 | 0.2509 | +0.0117 (within 5% tol) |
| PIT histogram | `[71,11,62,143,311,328,167,64,45,62]` | `[75,19,77,129,299,294,190,63,45,73]` | hump lower/flatter |

So the mild tightening flattens the central hump, improves marginal CRPS, and
costs the tail metric only a little — a genuine calibration gain that does **not**
over-tighten. A larger tightening buys a lower KS but at a tail cost the composite
would punish. **Honest caveat:** on THIS proxy the body-over-dispersion and the
tail-coverage are in tension (a uniform width scale cannot fix both at once); a
future refinement is a shape knob that reshapes the body without touching the
extreme quantiles. The mild 0.90 is the defensible, non-destructive choice now.

### 1.5 Applied, not just measured [RUN]

`disp_scale` is wired into the shipped engines (`JointDrawEngine.sample_matrix`,
`IndependentDrawEngine.sample_matrix`), threaded through `run_forecast` and the
`forecast` verb (`forecast_cli.run_verb`, `--disp-scale` flag), and defaulted to
**0.90** via `t2_adapter.DEFAULT_DISP_SCALE`. With the new default the exemplar
and `t2-F3-bear-flattener-2022` are **still admissible** (g0–g3 all pass) by BOTH
the reference scorer AND `qfbench2-smoke`.

Reproduce:
```
PYTHONPATH=.bigtmp/track2 .bigtmp/t2venv/bin/python \
  drafts/seldon_t2_text/run_calibration_eval.py \
  --units .bigtmp/track2/units --track2-repo .bigtmp/track2 \
  --select F3 --n-draws 1000 --realized-seeds 0,1,2,3,4,5,6,7 \
  --scales 0.85,0.88,0.9,0.92,0.94,0.96,0.98,1.0
```

---

## 2. Text ablation — empty corpus vs full pipeline (in-harness H1)

### 2.1 Design [RUN]

The SHIPPED forecaster is run two ways on each unit, sharing the SAME base draws
and SAME calibration so the ONLY difference is the text:

- **FULL** — numeric draws + the PHASE 3 rules text arm (type each corpus doc →
  link via the alias index → bounded confidence-mass shift, preserving the joint
  correlation).
- **BLANK** — the SAME draws with the corpus replaced by an **empty corpus** →
  text-blind.

Composite delta = `FULL − BLANK` (negative ⇒ text HELPS), scored with the
scorer's own `crps_composite`. **46 units** (EXAMPLE + F1 + F3, all of which
produced a usable rules signal) × 8 realized seeds. `run_text_ablation.py`.

Because the sealed outcomes are unavailable, we report against **two hand-made
realized flavours**, both stated plainly as proxies:

- **neutral** — the text-agnostic common-factor realized (the HONEST NULL: the
  truth carries no text component, so a directional band shift can only help by
  luck; expected uplift ≈ 0).
- **text-consistent** — the realized nudged in the SAME direction the corpus
  signals (a controlled DGP where the text IS informative). This is the
  **upper bound** — it isolates the apply-mechanism from typing accuracy (which
  PHASE 3 measured separately at 0.71 usable directional recall on real prose).

### 2.2 Result — and a retuned shift [RUN]

Sweeping the text shift fraction (the `apply_text_shift` knob):

| shift_frac | neutral mean Δ (want ≈0) | text-consistent mean Δ (want <0) | text-consistent helps % |
|---|---|---|---|
| **0.1** | **−0.0045 (≈break-even)** | **−0.0255** | **70.4%** |
| 0.2 | −0.0001 | −0.0417 | 67.1% |
| 0.3 | +0.0131 (hurts null) | −0.0492 | 62.2% |
| 0.5 (PHASE-4 default) | +0.0640 (hurts null a lot) | −0.0400 | 46.5% |

**The PHASE-4 0.5σ shift over-shoots the composite.** At 0.5σ it hurt the
text-agnostic null by +0.064 composite and helped only **46%** of the time even
when the text pointed the right way. At **0.1σ** the null downside is essentially
break-even (−0.0045 — the "silence/small-shift is safe" property PHASE 3 wanted)
while a directionally-correct signal helps **70%** of the time (mean −0.0255).

So we lowered the `apply_text_shift` default from **0.5σ → 0.1σ**. Smaller is
also the right call given typing recall is only 0.71 (PHASE 3): a mistyped 0.1σ
nudge barely moves the band.

### 2.3 What the ablation delta does and does NOT say (honest reading)

- The **headline in-harness H1 number** is the FULL−BLANK composite delta on the
  text-consistent realized: **mean −0.0255, helps 70%** at the shipped 0.1σ shift
  [RUN]. That is the apply-mechanism's upside WHEN the text is right.
- On the **honest null** (text-agnostic truth) the delta is **≈0** [RUN] — the
  text arm neither helps nor meaningfully hurts. This is the safe-floor property,
  quantified in the harness.
- **This is NOT a leaderboard uplift.** The real-board uplift is the product of
  (PHASE 3 typing recall, 0.71 and FOMC-style-only) × (this apply-mechanism
  upside) × (whether the realized actually moves with the text). The first factor
  is measured and modest; the third is sealed. On non-FOMC sources (ECB rhetoric,
  data releases, event filings) PHASE 3 showed rules typing collapses to 0.0–0.43,
  so the uplift there is gated on the live house endpoint — **[UNVERIFIABLE-
  LOCALLY]**.

Reproduce:
```
PYTHONPATH=.bigtmp/track2 .bigtmp/t2venv/bin/python \
  drafts/seldon_t2_text/run_text_ablation.py \
  --units .bigtmp/track2/units --track2-repo .bigtmp/track2 \
  --select EXAMPLE,F1,F3 --realized-seeds 0,1,2,3,4,5,6,7 \
  --n-draws 1000 --shift-fracs 0.1,0.2,0.3,0.5
```

---

## 3. Submission-readiness checklist — against the PHASE0 contract

Each item is **READY** / **NOT-READY** / **UNVERIFIABLE-LOCALLY**, with the exact
remaining action. Verified against the REAL 12-key C5 `submission.schema.json`
and `qfbench2_common.contracts` in `.bigtmp/t2venv`, and the real scorer.

| # | Item | Status | Evidence / remaining action |
|---|---|---|---|
| 1 | **Category choice** (`api`/`byo-small`/`byo-large`) with reasoning | **READY** | The shipped DEFAULT arm is a deterministic, network-free forecaster (rules text + numeric draws) → no model call. The track fixture (`SUBMISSION-DESCRIPTOR.md`) says for a no-model deterministic forecaster to use **`byo-small` with `access:"local"`** and say so. We do exactly that. If the MODEL_ENDPOINT arm is enabled, switch to **`api`** + model `access:"api"`. Both encoded in `make_submission_descriptor.py`. |
| 2 | **`submission.json` descriptor valid + sealed** | **READY** [BUILD] | Built `submission.dev.json`, validated against the real 12-key schema and sealed with `seal_descriptor_digest`; `SubmissionDescriptor.from_mapping` ACCEPTS it. Proven real: it REJECTS a tampered copy (digest `ContractError`) and REJECTS the `house_endpoint_only` trap field (unknown-field error). Avoids the legacy `image_digest`/`model_disclosure` shapes. |
| 3 | **Image digest** in the descriptor | **NOT-READY** | `image.digest` is a placeholder (`sha256:000…`). Remaining action: rebuild the Phase-4 image to include the Phase-5 code, take the real `sha256:` from `docker build`, substitute it, and re-run `make_submission_descriptor.py` to re-seal. |
| 4 | **Team id** in the descriptor | **UNVERIFIABLE-LOCALLY** | `team_id` is a placeholder. It comes from the CodaBench profile and cannot be derived here (the doc says so explicitly). Remaining action: paste the real team id and re-seal. |
| 5 | **Model version pinning + training-cutoff disclosure** | **READY (deterministic arm) / UNVERIFIABLE-LOCALLY (api arm)** | Deterministic arm: `models[0] = {name: ocelot-seldon-deterministic, version: t2-ocelot-phase5, training_cutoff: not-applicable, access: local, revision: <git sha>}` — all five keys present, honest. If `api`: the house model's `version`/`training_cutoff` are **not published** anywhere in the kit; per the doc, put the most honest value and raise with organizers — cannot be finalised locally. |
| 6 | **Seed pinning** | **READY** [RUN] | `--seed` default 0 → `np.random.default_rng(seed)` for all draws; deterministic. Same seed ⇒ byte-identical forecast. |
| 7 | **Temperature pinning** | **READY (rules) / PARTIAL (model)** | Rules arm is deterministic (no temperature). Model arm payload pins `temperature: 0.0`. Minor remaining action for full model determinism: also set the OpenAI `seed` field in the request payload (the house endpoint may honor it). |
| 8 | **Three output files correct (`unit_id` not `card_id`)** | **READY** [RUN] | `forecast.parquet` (cols exactly `draw,asset,horizon,value`), `forecast_meta.json` keyed on **`unit_id` == card `[task].id`** (t2_adapter `write_outputs`), `forecast_rationale.md` non-blank. g0 sees exactly these three files. Verified byte-level in phases 1/4 and re-verified admissible here. |
| 9 | **Passes g0–g3** | **READY** [RUN] | With BOTH Phase-5 changes live (disp 0.90 + shift 0.1): **9/9 admissible**, g0–g3 all pass, across EXAMPLE / F1 / F2 / F3 / F4 + the BRL transfer unit, via the real reference scorer; exemplar + F3 also cross-confirmed by `qfbench2-smoke`. No regression from calibration. |
| 10 | **Fits the phase budget** | **READY (compute) / UNVERIFIABLE-LOCALLY (cold pull)** | Phase-4 measured solve **0.037–0.112 s/unit** (mean 0.082 s) — ~4 orders under the ~400 s/unit Dev clock. Calibration/ablation add no runtime cost (same draw path). The binding cost is the **90–187 s cold image pull** (guide figure) on the 683 MB image; the real pull time depends on organizer infra. |
| 11 | **Interface version label** | **READY** [BUILD] | Phase-4 image carries `LABEL qfbench2.interface_version="2.0"`; descriptor `interface_version` matches. (A rebuild for item 3 must preserve the label — the Dockerfile already sets it.) |
| 12 | **Network contract** (offline default, house endpoint via proxy only) | **READY (wiring) / UNVERIFIABLE-LOCALLY (live)** | Default rules arm never touches the network (Phase-4 `--network=none` run admissible). Model arm routes ONLY via `HTTP_PROXY`/`HTTPS_PROXY` → `MODEL_ENDPOINT`, no vendor URL/key; proven against a localhost mock. Live house-endpoint behaviour is the standing open item. |
| 13 | **Ranked / normalized leaderboard score** | **UNVERIFIABLE-LOCALLY** | Always `RAW_UNRANKABLE` locally (PHASE0 §5.1); a normalized score needs the organizer `ref_scale`, which participants never have. Only gates + raw components + relative deltas are reproducible. Remaining action: submit the image + descriptor to the Dev board and read the returned per-card scores. |

Descriptor build (reproduce):
```
.bigtmp/t2venv/bin/python drafts/seldon_t2_text/make_submission_descriptor.py \
  --team-id <YOUR_TEAM_ID> --category byo-small \
  --image-digest sha256:<64hex-of-final-image> \
  --out drafts/seldon_t2_text/submission.dev.json
```

---

## 4. Proven vs assumed — ledger

**PROVEN [RUN]/[BUILD] (real, reproducible here):**
- The shipped numeric core is over-dispersed on the local proxy (central PIT
  hump, KS 0.1884); a tail-guarded `disp_scale=0.90` improves KS 10.3% and
  marginal CRPS without over-tightening the tail. Robust across realized modes.
- `argmin(KS)` (≈0.40) over-tightens (tail +58%) — the CRPS-both-tails trap,
  explicitly avoided.
- Calibration knob wired into the shipped engines + verb, default 0.90; output
  still admissible g0–g3 (real scorer + smoke).
- In-harness text ablation: FULL−BLANK on a text-consistent realized helps 70%
  (mean −0.0255) at the retuned 0.1σ shift; on the honest null it is ≈break-even.
  The old 0.5σ shift over-shot (hurt the null +0.064, helped only 46%); lowered
  to 0.1σ.
- `submission.json` built, schema-validated, sealed, and accepted by the real
  contracts parser; rejects tamper + the `house_endpoint_only` trap.
- 9/9 admissible across all families + BRL transfer with Phase-5 changes live.

**ASSUMED / NOT OBTAINED (stated, not fabricated):**
- All local metrics use a HAND-MADE realized proxy, not the sealed outcomes; they
  are RELATIVE before/after and full/blank numbers, never leaderboard values.
- Live MODEL_ENDPOINT accuracy on real (esp. non-FOMC) prose — needs the house
  endpoint; the text uplift on those sources is gated on it.
- Final image digest + team id — placeholders; filled at build/submit time.
- Ranked score — impossible locally.
- The body-vs-tail calibration tension means a uniform width scale is a partial
  fix; a body-only reshaping knob is a noted future refinement.

All scripts run clean and deterministic; no temp files left behind.

## Files (this phase)
- `run_calibration_eval.py` — randomised-PIT KS + tail scan, tail-guarded choice.
- `run_text_ablation.py` — full-vs-blank composite delta, shift-frac sweep.
- `make_submission_descriptor.py` + `submission.dev.json` — validated, sealed C5
  descriptor (with the two placeholders flagged).
- `phase5_calibration_records.json`, `phase5_calibration_records_wide.json`,
  `phase5_ablation_records.json` — raw records.
- Edits: `t2_adapter.py` (`disp_scale` knob + `DEFAULT_DISP_SCALE=0.90`),
  `forecast_cli.py` (`--disp-scale`; `apply_text_shift` default 0.5→0.1).
