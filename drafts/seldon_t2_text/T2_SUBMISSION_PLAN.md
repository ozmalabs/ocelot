# PLAN — draft → Agenthon 2026 Track 2 submission

Target: `github.com/Agenthon-2026/track2-forecasting-public`. Moves the
`drafts/seldon_t2_text/` PoC (arxiv-importer ingestion + graph-native referent
linking + TimeInfer projection + Seldon confidence overlay, time-as-`coord:t`)
onto the REAL Track 2 submission contract.

## Contract facts (from the participant guide, 2026-08-27 state)

- **Verb**: `forecast --panels /input/panels --text /input/text --asof YYYY-MM-DD --out /output/forecast.parquet`. Unit dir mounted at `/input` (`panels/`, `text/` are subdirs).
- **Output**: `forecast.parquet` cols `[draw:int32, asset:string, horizon:int32, value:float64]`, MONTE CARLO DRAWS (n≥200; 500+ rec; 1000+ for F4 tails). Joint cards (F3/F4): every draw index must have rows for ALL target assets+horizons (co-movement is scored).
- **Sidecars**: `forecast_meta.json` (key is `unit_id`, must match `card.toml [task].id`; NOT `card_id`), `forecast_rationale.md` (required, non-blank, never scored).
- **Score**: `S = 0.5·marginal CRPS + 0.3·joint variogram + 0.2·tail penalty`, lower better. Single-asset cards: variogram=0, reweighted to 0.714·CRPS + 0.286·tail. Text-blind baseline normalized to 1.0; missing/inadmissible card = 4.0.
- **Baselines to beat (text-blind)**: theta_arima, chronos, timesfm, lag_llama, moirai.
- **Data**: 4 real Parquet panels (rates/ust-daily, fx/g10-daily, macro/releases-quarterly, factors/jkp-daily), 2000-01-03..2024-12-31, cols `[date, asset, value, panel_id]`. Real dated text corpus (FOMC/ECB/macro headlines/COT).
- **Families**: F1 (23), F2 (27, text-cued regime shift + TRANSFER to EM FX absent from inputs), F3 (22, cross-asset), F4 (31, tail/shock-from-text). 103 practice units, NO answers shipped.
- **Network**: restricted. Only egress = organizer proxy to `MODEL_ENDPOINT` (OpenAI-compatible house model; free, per-run budget). Vendor APIs refused. Vendor tools (web/retrieval) disabled. Local smoke = `--network=none`.
- **Resources**: 16 vCPU / 128G / gpu=true / 1800s per-unit ceiling BUT phase budget binds: Dev 43200s (~400s/unit over ~100), Final/Verif 86400s. Clock starts at `docker create` (cold image pull billed 90-187s).
- **Toolkit**: `pip install "qfbench2-common @ git+https://github.com/Agenthon-2026/Agenthon2026-public.git@v2.3.1#subdirectory=common"` — pin v2.3.1 (first tag with `qfbench2_common.contracts`). Dockerfile MUST add it (else `ModuleNotFoundError: qfbench2_common`).
- **Scorer**: `scoring/scoring.py` is reference; gates g0-g3. `qfbench2-smoke <unit>/ output/ --track forecasting` runs gates offline. Realized outcomes SEALED (no local score; supply own `--realized` for local metric).
- **Categories**: api / byo-small (≤~8B) / byo-large (80G). One ranking, equal-weight mean of normalized scores.

## Contract mismatches vs the draft (load-bearing)

1. Output = MC draws, not stepped (value,mass). Need `.sample(n_draws)`.
2. Score = 3-term composite. Draft scores marginal CRPS only. **Joint variogram (30%) is the biggest gap** — draft propagates entities INDEPENDENTLY, so joint term is systematically bad on F3/F4.
3. Real panels + real corpus. Draft is semi-synthetic. Real claim-typing over FOMC prose replaces the "leg-iii 100% by construction" caveat — becomes the live problem.
4. Docker + restricted net + house `MODEL_ENDPOINT`. OCELOT `substrate_rs` must run in-image; any LLM call via proxy, not vendor API.
5. Entity linking targets real financial entities (tenors/crosses/series), not tickers. F2 transfer: EM FX absent from inputs → claim→band must fire from text alone.
6. Score against THEIR `scoring.py`, pass g0-g3. Draft reimplemented CRPS.

## Phases

### Phase 0 — Ground truth (no agent code yet)
- Clone track2 repo + toolkit v2.3.1. Run exemplar `run_example.sh` end-to-end; run `scoring/scoring.py` + `qfbench2-smoke` on it.
- READ `scoring/scoring.py` line by line — variogram + tail definitions as-CODED are the spec (not the prose paraphrase).
- Read `docs/CONCEPTS.md`, `docs/CATEGORIES.md` (F1-F4), `SUBMISSION_CLI.md`, `forecast.schema.json`.
- Run ≥1 text-blind baseline on a few practice units to see panel shapes + the bar.
- DELIVERABLE: a note pinning exact output contract, composite formula as-coded, per-family input/target shapes.

### Phase 1 — Output-contract adapter (reuse mechanism, change emit)
- `.sample(n_draws)` on the Seldon stepped dist → MC draws. Keep reachable-set + confidence mechanism.
- Write forecast.parquet / forecast_meta.json (`unit_id`!) / forecast_rationale.md per schema.
- Real panel loader (`[date,asset,value,panel_id]` Parquet) replacing synthetic Panel; as-of truncation.
- Card.toml reader (targets asset_ids, horizons, unit id).
- GATE: pass g0-g3 on exemplar + ≥10 practice units via their scorer + smoke.

### Phase 2 — Joint variogram (the 30% currently failing)
- Replace independent per-entity propagation with JOINT draws: estimate cross-asset innovation covariance from panel history, draw correlated residuals; co-movement preserved. OCELOT framing = reachable-set over the joint manifold.
- Validate variogram term drops on F3-shaped units vs independent-draw baseline (hand-made realized file for local metric).
- GATE: joint variogram materially better than independent draws on multi-asset units.

### Phase 3 — Real text pipeline (the science)
- Re-point ingest at real corpus (FOMC/ECB/headlines) — arxiv `_load()` structural pass still applies; claim-typing (tightening/easing/surprise → rate/FX direction) now REAL + measurable.
- Re-point linking at real entities (tenor/cross/series names + alias/synonym seed). F2 transfer: claim→band fires from text alone, no panel history for the asset.
- LLM boundary decision: claim-typing via `MODEL_ENDPOINT` (allowed) vs rules-only (OCELOT-native, network-independent). Prototype BOTH, measure. Rules-only more robust to budget/latency.
- DE-RISK FIRST (week 1): hand-label tightening/easing tone on ~50 real FOMC/ECB snippets; measure rules-only vs MODEL_ENDPOINT typer recall. If typing weak on real text, ceiling moved from linking to extraction — know it early.

### Phase 4 — Containerize (net + resource contract)
- Dockerfile: base + numpy/pandas/pyarrow/jsonschema + `qfbench2-common@v2.3.1` + OCELOT `substrate_rs` wheel built in-image. `forecast` on PATH, no ENTRYPOINT.
- Start with NO GPU present and NO network (offline smoke). Route model calls via `HTTP_PROXY`/`MODEL_ENDPOINT`. Pin model version + disclose training cutoff.
- Budget: keep image small (favors byo-small/api). Per-unit solve fast — the linker boots agent + runs rules per surface; MUST cache/batch or precompute an alias index to fit ~400s/unit incl cold pull.
- GATE: `docker run --network=none` writes admissible outputs on exemplar; restricted-net dry run hits house endpoint only.

### Phase 5 — Calibration, ablation, submit
- Tighten calibration (PoC KS 0.0926 = over-dispersion; CRPS punishes both tails).
- Run text-ablated variant (empty corpus) — the H1 uplift measurement, now in their harness.
- Pick category, pin versions/seed/temp, write rationale, submit image digest to Dev board. Read per-card scores not rank (board is pipeline check; practice data self-leaks by their own measurement — 75/103 units' targets appear in sibling panels).

## Sequencing
Phases 1-2 = critical path to admissible+rankable. Phase 3 = where uplift is won/lost.
STRATEGY: get a dumb-but-admissible full-composite submission on the board FIRST (Phase 0-2 + trivial climatology text-blind arm), THEN layer text pipeline — always have a scored baseline to measure uplift against; don't debug format + science simultaneously.

## Highest risk
Real claim-typing over central-bank prose. PoC's clean H1 leaned on leg-iii ~100% by construction; gone on real text. Prior ceiling was entity linking; against this spec it may move to claim extraction. De-risk in Phase 3 week 1 before committing architecture.
