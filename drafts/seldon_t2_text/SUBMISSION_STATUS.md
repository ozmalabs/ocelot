# SUBMISSION STATUS — Agenthon 2026 Track 2 (forecasting), OCELOT/Seldon

Honest cross-phase status of the `drafts/seldon_t2_text/` submission effort.
Follows the repo's honesty norms: **proven vs assumed, and nulls are findings.**
**No score is fabricated** — a ranked/normalized leaderboard number is impossible
to produce locally (every local run is `RAW_UNRANKABLE`, PHASE0 §5.1), so none is
claimed anywhere. All local metrics use a clearly-labelled hand-made realized
proxy; the sealed outcomes are not available.

Provenance: **[RUN]** executed here · **[BUILD]** built/sealed here · **[MOCK]**
architecture exercised against a stub · **[UNVERIFIABLE-LOCALLY]** needs the
organizer endpoint / sealed data / registry / team id.

---

## 1. What is PROVEN and RUNNABLE (real repos, real scorer, in this workspace)

Phase 0 cloned the REAL public repos, so everything below is scored against the
**real** `qfbench2_track_forecasting` reference scorer + `qfbench2-smoke` + the
real `qfbench2-common 2.3.1` — not a mock.

1. **Output-contract adapter is admissible.** `t2_adapter.py` puts the PoC Seldon
   reachable-set + confidence mechanism on the exact Track 2 output contract
   (forecast.parquet `draw,asset,horizon,value`; `n_draws×cell_count` rows, every
   cell once, contiguous 0-based draws, finite; `forecast_meta.json` keyed on
   **`unit_id`**; non-blank rationale). **g0–g3 pass on 41 units** (exemplar + 18
   F1 + 22 F3) via the real scorer + smoke. [RUN] `FastSeldonForecaster` is
   numerically identical to the exact PoC propagate (max mass diff ~1e-16).

2. **The joint variogram gap (the 30% the PoC failed) is closed where the premise
   holds.** `JointDrawEngine` draws cross-asset-correlated shocks with marginals
   held identical to the independent arm. On **pure UST yield-curve F3 units** the
   joint variogram beats independent on **85% of cells** (mean −1.16, composite
   −0.35), marginals/tail held fixed. [RUN] On FX/mixed it does NOT win — reported
   honestly, with a proven diagnosis (the hand-made realized mis-signs
   anti-correlated EM crosses; the variogram is level-gap-dominated on mixed-scale
   FX). **Null reported as a finding**, not tuned away.

3. **Real claim-typing ceiling is measured.** [RUN] A rules-only typer on 52
   verbatim real snippets recovers direction on **71.1%** of directional snippets;
   the failure mode is **silence (85% of misses are abstains), not error** (4.4%
   wrong-direction). Sharp doc-type cut: FOMC statements **0.829**, everything
   else (ECB rhetoric, data releases, 8-K, COT) **0.0–0.43**. So on real prose the
   PoC's "~100% typing by construction" is a DGP artifact; **extraction, not
   linking, is the binding constraint**, and rules-only is a safe FOMC-only floor.

4. **Containerized, offline, admissible.** [BUILD]/[RUN] `docker build` succeeds
   (683 MB, `LABEL interface_version=2.0`, no ENTRYPOINT, `forecast` on PATH,
   `qfbench2-common@v2.3.1` installed from the git tag, `substrate_rs` abi3 wheel
   copied). `docker run --network=none … forecast …` on the exemplar writes
   admissible output confirmed by the real scorer AND smoke, **no GPU, no network**.
   Solve **0.037–0.112 s/unit** across all families + the BRL transfer unit.

5. **Calibration measured + tightened without over-tightening.** [RUN] The
   forecaster is over-dispersed (central randomised-PIT hump, KS 0.1884). A
   tail-guarded `disp_scale=0.90` improves KS **10.3%** (→0.1690) and marginal
   CRPS, while the scorer's tail metric stays within 5%. `argmin(KS)≈0.40` was
   rejected as over-tightening (tail +58%). Wired into the shipped engines +
   verb; output still admissible.

6. **Text ablation (in-harness H1).** [RUN] FULL vs empty-corpus BLANK, same
   draws. On a text-consistent realized the text arm helps **70%** of the time
   (mean composite −0.0255) at a retuned **0.1σ** shift; on the honest null it is
   **≈break-even** (safe floor, quantified). The Phase-4 0.5σ shift over-shot
   (hurt the null +0.064, helped only 46%) → lowered to 0.1σ.

7. **`submission.json` descriptor is valid + sealed.** [BUILD] Built against the
   real 12-key C5 schema and sealed with the real toolkit; the authoritative
   parser accepts it and rejects both a tampered copy and the `house_endpoint_only`
   trap field.

**Bottom line:** an admissible, calibrated, containerized, offline forecaster that
passes g0–g3 on every family and closes the joint-variogram gap on yield-curve
units — runnable end-to-end here.

---

## 2. What is BUILT-BUT-UNVERIFIED-LOCALLY (wiring proven, payoff needs organizer infra)

These are implemented and exercised, but the thing that would confirm the *payoff*
is not available in this workspace. None is claimed as measured.

- **Docker cold-pull time.** Image is 683 MB; the 90–187 s cold pull is the
  binding budget cost. The guide figure is used; the real pull depends on the
  organizer registry. [UNVERIFIABLE-LOCALLY]
- **The real toolkit at scoring time.** We install `qfbench2-common@v2.3.1` and
  score with the real reference scorer + smoke here, but the organizer's scoring
  harness (with `ref_scale` for normalization) is not reproducible → only gates +
  raw components + relative deltas, never a ranked number. [UNVERIFIABLE-LOCALLY]
- **The house `MODEL_ENDPOINT`.** The full call path (env-driven, OpenAI-compatible,
  proxy-only, no vendor key, `temperature:0.0`) is proven against a localhost mock
  [MOCK]/[RUN]; the container hit the mock, parsed responses, stayed admissible.
  **Live accuracy on real prose — especially the non-FOMC sources where rules
  typing collapses — is NOT measured.** This is the single biggest open lever on
  text uplift. [UNVERIFIABLE-LOCALLY]
- **Sealed realized outcomes / real calibration + uplift.** All local calibration
  and ablation numbers use a hand-made common-factor proxy, stated as such. The
  real PIT calibration and the real text uplift against the sealed truth are not
  obtainable locally. [UNVERIFIABLE-LOCALLY]
- **Final image digest + team id in the descriptor.** Placeholders; filled at
  build/submit time (see §3).

---

## 3. Remaining actions to get a SCORED submission on the Development board (ordered)

Precise, ordered, each with the exact command/where-from. Nothing here is optional
for a scored entry.

1. **Rebuild the image with the Phase-5 code.** The Phase-4 image predates the
   calibration + shift retune. Run `bash drafts/seldon_t2_text/docker/build.sh`
   (or `SKIP_WHEEL=1 …` to reuse the fresh substrate wheel). Confirm the
   `LABEL qfbench2.interface_version="2.0"` survives (`docker inspect`).
2. **Re-run the offline GATE on the rebuilt image.**
   `docker run --network=none -v <staged-unit>:/input:ro -v <out>:/output IMAGE
   forecast --panels /input/panels/ --text /input/text/ --asof <ASOF> --out
   /output/forecast.parquet`, then score with the reference scorer + `qfbench2-smoke`.
   Expect g0–g3 pass (as here). This guards against a build-vs-source drift.
3. **Push the image** to a pullable registry (`image_access: public`, or the
   organizer mirror). Record the `sha256:` digest from the push.
4. **Finalise `submission.json`.** Re-run
   `make_submission_descriptor.py --team-id <REAL> --category <byo-small|api>
   --image-digest sha256:<real> --registry <r> --repository <repo>`; it re-seals
   the JCS digest and round-trips through the real parser. Fill:
   - `team_id` — from your CodaBench profile.
   - `image.digest` — from step 3.
   - `category` — `byo-small`/`access:local` for the deterministic default arm, OR
     `api`/`access:api` if the house-endpoint arm is enabled.
   - if `api`: put the most honest `models[0].version`/`training_cutoff` and
     **raise the unpublished house-model pin with the organizers** (unknowable
     from the docs).
5. **Decide the text arm for the run.** Default rules-only is the safe,
   network-free floor (helps on FOMC, silent elsewhere). To chase non-FOMC uplift,
   enable `QFB2_TEXT_ARM=model` with the proxy env — but ONLY after step 6.
6. **(If pursuing the model arm) Measure live house-endpoint typing accuracy** on
   the real corpus and confirm it beats rules-only's 0.756 usable recall by enough
   to justify the token budget. This is the standing open item from Phase 3/4.
   Also add the OpenAI `seed` field to the request payload for full determinism.
7. **Submit** the one-file zip (`submission.json` at the archive root, nothing
   else) to the Development phase. Then **read the returned per-card scores** (not
   rank — the Dev board is a pipeline check and the practice data self-leaks by the
   organizers' own measurement). That is the first and only place a real,
   normalized score exists.

**Standing risk (unchanged):** text uplift on non-FOMC sources depends on the live
house endpoint; rules-only is the proven safe floor but leaves that signal on the
table. The numeric core (calibration + joint variogram) is the proven,
endpoint-independent value.
