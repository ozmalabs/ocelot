# PHASE 0 — GROUND TRUTH: Agenthon 2026 Track 2 contract

This file pins the REAL Track 2 contract as-coded. Every downstream stage builds against
this, not against the prose paraphrase in `T2_SUBMISSION_PLAN.md`. Each fact is tagged
with provenance:

- **[CODE]** verified from source read line-by-line (file:line cited).
- **[RUN]** verified by executing the exemplar / scorer / smoke in this workspace.
- **[DATA]** verified by inspecting real parquet/text bytes.
- **[PROSE]** from a participant-guide / docs `.md` only; NOT confirmed against code (and
  where it conflicts with code, **code wins** — conflicts are called out explicitly).

## Provenance path used

**CLONE SUCCEEDED — the repos are public.** Both cloned into `.bigtmp/` with no network
restriction:

- Repo: `github.com/Agenthon-2026/track2-forecasting-public` → `.bigtmp/track2/`
  (default branch; the scorer package `qfbench2_track_forecasting/` v2.1.0 lives here).
- Toolkit: `github.com/Agenthon-2026/Agenthon2026-public` @ tag **v2.3.1** →
  `.bigtmp/toolkit/` (detached HEAD at commit `9c5541a`; `common/` = `qfbench2-common` 2.3.1).

A local venv `.bigtmp/t2venv` (Python 3.13) was built with `numpy pandas pyarrow jsonschema`
+ `pip install ./toolkit/common`. The exemplar ran end-to-end and the scorer + `qfbench2-smoke`
both executed against it. So essentially everything below is [CODE]/[RUN]/[DATA]; almost nothing
is [PROSE]-only.

---

## 1. Submission / mount / verb contract

**[CODE/PROSE — SUBMISSION_CLI.md]** A submission is a Docker image. The harness runs:

```
docker run --rm \
  --network=none|qfb2-eval \
  --cpus=<card.cpus> --memory=<card.memory> [--gpus all] \
  -v <unit-dir>:/input:ro \
  -v <run>/output:/output \
  <IMAGE> <verb> [args]
```

- The **verb is the container command** (first arg after the image). Build with **no
  ENTRYPOINT** and put `forecast` on `PATH`, OR consume the verb as a leading positional.
  A verb that is missing/non-exec scores **zero on that unit** (127/126), recorded as YOUR failure.
- Image LABEL `qfbench2.interface_version="2.0"` is **required**.

**T2 verb (exact):**
```
forecast --panels /input/panels/ --text /input/text/ --asof <YYYY-MM-DD> --out /output/forecast.parquet
```
- `--panels` points at the STAGED unit's `panels/` subdir. **[PROSE, SUBMISSION_CLI.md T2
  status note]** `stage_bundle.py` relocates root-level panels into `panels/`; `--panels /input/`
  (no subdir) dies "no .parquet found". NOTE: in the **public repo units as shipped**, panels sit
  at unit root (e.g. `rates_daily.parquet`), not in `panels/` — the `panels/` layout is what the
  container sees at scoring time after staging. **[DATA — confirmed: `.bigtmp/track2/units/*/`
  hold panels at unit root, no `panels/` subdir.]**
- `--out` names `forecast.parquet`. Sidecars `forecast_meta.json` and `forecast_rationale.md`
  are written next to it (all three in `/output`).

**Network** **[PROSE — SUBMISSION_CLI.md]**: exactly two modes; T2 = `restricted`. NO open
internet ever. Egress ONLY via audited proxy (`HTTP_PROXY`/`HTTPS_PROXY` env, never hardcode)
to `MODEL_ENDPOINT` (organizer-hosted OpenAI-compatible, model id `MODEL_NAME`, free, per-run
token budget — provisional 1,000,000 in / 100,000 out per unit). Vendor APIs
(api.openai.com etc.) **refused by the proxy**; vendor-side tools (web/retrieval/code-exec)
MUST be off. No participant API keys exist. Local smoke = `--network=none`.

**Categories** **[PROSE]**: `api` (CPU, house endpoint only) / `byo-small` (≤~8B, CPU or small
GPU) / `byo-large` (GPU 80GB-class). One leaderboard, every entry tagged. Pin model versions,
disclose `models[].training_cutoff` in `submission.json`. Optional `house_endpoint_only: true`
→ "Open Division" display filter (not a separate ranking).

---

## 2. Output contract — forecast.parquet (the draws)

**[CODE — grid.py `FORECAST_COLUMNS`, ~line 62]** The exact, EXACT (not minimal) column set:

```
forecast.parquet columns == ("draw", "asset", "horizon", "value")   # order not required in parquet, set must be exact
```
- **An extra column is REFUSED, not ignored** (`limits.read_parquet_columns`; grid.py
  `build_sample_matrix`). A missing column is refused. Duplicate column name refused.
- **[CODE — grid.py `build_sample_matrix` / `_place_exactly_once`]** Draw semantics, enforced:
  - `draw` ids MUST be **contiguous, zero-based integers `0..n_draws-1`** (bool is not int).
  - Row count MUST equal **exactly `n_draws × cell_count`** where `cell_count = |assets|×|horizons|`
    (checked on the parquet FOOTER before materialization — `expect_exact_rows`, limits.py).
  - **Every `(draw, asset, horizon)` cell occupied EXACTLY ONCE.** Duplicate cell → refused
    (`INCOMPLETE_OUTPUT`), never averaged. Missing cell → refused. This is the JOINT-draw
    requirement: for a 4-asset F3 card every draw index has one row per (asset,horizon).
  - `value` must be **finite** (no NaN/Inf) — a non-finite value is a PARTICIPANT failure
    (`SCHEMA_INVALID`, grid.py `_finite_values`).
  - Any asset/horizon label outside the committed grid → refused (grid.py `_codes_for`).
- **dtypes**: `draw:int`, `asset:str`, `horizon:int`, `value:float`. The scorer coerces via
  `to_pylist()` and type-checks each element; int-typed draw/horizon and float value are the
  safe emit. **[CODE]** The exemplar emits `draw:int64, asset:str, horizon:int64, value:float64`
  **[DATA — RUN]** and passed g3.
- **Flattening / ordering [CODE — grid.py `GridSpec.cells`]**: canonical order is
  **asset-major, horizon-minor, in the plan's DECLARED order**. The realized vector is flattened
  the same way, so **grid order is part of the contract**: `forecast_meta.asset_ids`/`horizons`
  must match the committed grid **exactly, in order, with no repeats** (grid.py
  `check_declared_grid`) or g3 refuses (`SCHEMA_INVALID`).
- **`representation` accepted = `("samples",)` ONLY** **[CODE — scoring.py line 98, 315]**.
  `parametric` is advertised by the shared schema but has **no loader** and is REFUSED by the
  scorer. Do not emit parametric.

**Column-count ceiling** **[CODE — limits.py line 78]**: `max_columns=8`; row groups ≤ 64;
file ≤ 64 MiB on disk; ≤ 5,000,000 rows generic backstop; but the binding bound is the exact
`n_draws×cell_count` footer check.

### Baseline result shape (for the adapter)
**[CODE — baselines/base.py]** `ForecastResult.samples.shape == (n_draws, n_assets, n_horizons)`,
axis order strict (draws, assets, horizons), assets in `request.asset_ids` order, horizons in
`request.horizons` order. The long forecast.parquet is produced by unrolling this 3-D array
(see run_example.sh). `ForecastRequest` = `{panels: dict[str,DataFrame], asof: str, asset_ids,
horizons, n_draws=500}`.

---

## 3. forecast_meta.json — required keys

**[CODE — forecast.schema.json in qfbench2_common/schemas/ + scoring.py g1/g2]**

Required by JSON Schema (`required`): **`unit_id`, `asof`, `representation`, `asset_ids`,
`horizons`**. Conditionally required: **`n_draws`** when `representation=="samples"` (always, for us).

```json
{
  "unit_id": "<must EQUAL card.toml [task].id>",   // NOT card_id — bind_metadata checks == card [task].id
  "asof": "YYYY-MM-DD",                              // must EQUAL card as-of (regex ^\d{4}-\d{2}-\d{2}$)
  "representation": "samples",                       // only 'samples' accepted by scorer
  "asset_ids": ["...", "..."],                       // == committed grid, in order, no repeats
  "horizons": [21],                                  // integers >= 1, == grid order
  "n_draws": 500,                                    // int, 200 <= n <= 20000 (see limits)
  "target": "level"                                  // optional; if present MUST match card [targets].target_type
}
```

- **`unit_id` NOT `card_id`** [CODE — scoring.py `_g0`/`bind_metadata`, cutoff.py]. `unit_id`
  must equal the card's `[task].id`. (The scorer's CLI *stdout* prints a `card_id` field, and the
  corpus_index.json uses a `card_id` key — but the OUTPUT sidecar key is `unit_id`.)
- **`asof` binding** [CODE — cutoff.py `bind_metadata`]: `meta.asof` must EQUAL the card as-of
  (`[forecast].asof` or `[provenance].data_cutoff`); mismatch → `CUTOFF_VIOLATION`.
- **`target` binding** [CODE — cutoff.py]: if present and ≠ card `[targets].target_type` →
  `SCHEMA_INVALID` ("a level forecast scored as a log return is a different quantity"). Schema
  `target` enum = `level | log_return | yield`.
- **`n_draws` floor is enforced in CODE, not just schema** [CODE — limits.py line 86
  `min_draws=200`, line 81 `max_draws=20000`; scoring.py g1 + grid.py `build_sample_matrix`].
  Three historical bypasses of the schema `minimum:200` are all closed. `n_draws` must be a real
  `int` (bool rejected).
- **`rationale` key** in schema is OPTIONAL and declaration-only; the FILE is what matters.

---

## 4. forecast_rationale.md

**[CODE — scoring.py g1 + limits.py `rationale_has_content`]** REQUIRED, checked by g1 for
**existence + at least one non-whitespace char ONLY**. **NEVER scored**; no scoring code reads
its content. Max 1 MiB. It is a human-review screen over the leaderboard (a flag opens review;
cannot by itself DNF or move a score). **[PROSE — SUBMISSION_CLI.md / RATIONALE-REVIEW.md]**
current false-positive measurement 0/4.

---

## 5. Composite score — AS CODED

**[CODE — qfbench2_common/scoring/crps.py + scoring.py `_score`]** `LEADERBOARD_SORT="asc"`
(lower composite wins; scoring.py line 86).

### 5.1 The composite (crps.py `crps_composite`, line 130-160)
```
S = w_m·(marg / ref.marginal) + w_j·(jnt / ref.joint) + w_t·(tail[/ref.tail if present])
default weights (w_m,w_j,w_t) = (0.5, 0.3, 0.2)     # from card [scoring.params.weights]
```
- Skill-normalized by an official text-blind baseline's per-component values via `ref_scale`.
  **[CODE — normalization.py + scoring.py `hydrate_ctx`]** Without a `ref_scale` the raw
  components are used and the run is `RAW_UNRANKABLE` (the local CLI/smoke path is ALWAYS
  raw/unranked — `NormalizationMode.RAW_UNRANKABLE`; a ranked score requires a C1 signed plan +
  `ref_scale`, which participants never have locally). **Consequence: you cannot reproduce your
  leaderboard number locally**; you can only reproduce raw components + gates.
- `tail` is normalized only if `ref_scale` carries a `"tail"` key; otherwise left raw.

### 5.2 Marginal CRPS (crps.py `crps_ensemble` L52, `crps_marginal` L65)
```
CRPS_ens(samples[m], y) = mean_i |x_i - y|  -  0.5 · E|X-X'|
  where E|X-X'| uses the FAIR (almost-unbiased) estimator with denom m·(m-1) (fair=True default),
  computed via the sorted identity sum_{i,j}|x_i-x_j| = 2·sum_i (2i-m-1)·x_(i).
marginal = MEAN over the d = assets×horizons flattened cells of the univariate CRPS.
```
Weight 50%. NOTE: crps.py `fair=True` (denom m(m-1)); CONCEPTS.md prose shows the biased 1/(2m²)
form — **[CONFLICT: code uses fair estimator; prose formula is the simplified biased one]**.

### 5.3 Joint variogram (crps.py `variogram_score` L90, DEFAULT joint)
```
VS_p(samples[m,d], y) = sum_{i,j} w_ij · ( |y_i - y_j|^p  -  mean_m |X_mi - X_mj|^p )^2
  p = 0.5 (default vs_p), w_ij = 1 (unweighted d×d).
```
Weight 30%. **Independent per-asset draws are systematically penalized** (base.py docstring
confirms per-asset baselines "carry no cross-asset dependence structure" → variogram penalty).
`joint` can also be `"energy"` (energy_score, L79) but cards default `joint="variogram"`
(exemplar card `[scoring.params].joint="variogram"`). **This is the 30% the current draft fails.**

### 5.4 Tail penalty (crps.py `tail_penalty` L110)  ⚠ CONFLICT WITH PROSE
```
P_tail = sum over levels a in (0.01,0.05,0.95,0.99) of | coverage_a - a |
  coverage_a = mean over d cells of 1{ y_d <= quantile_a(samples) }
```
Weight 20%. **[CONFLICT — LOAD-BEARING]** `CONCEPTS.md §10` and `CATEGORIES.md` F4 prose
describe the tail penalty as **pinball / check loss** at those quantiles. **The CODE does NOT
use pinball — it uses `|empirical PIT coverage − level|`.** Downstream MUST optimize the
as-coded coverage metric (a coverage-calibration objective), NOT pinball loss. This is the
single most important prose-vs-code discrepancy in the scoring.

### 5.5 Single-asset reweighting (scoring.py `_score`, lines 461-468)
On a **single-cell grid** (`cell_count == 1`), the variogram is 0 by construction, so its weight
is redistributed over the components that exist:
```
if cell_count == 1:
    live = w_m + w_t
    weight_tuple = (w_m/live, 0.0, w_t/live)   # (0.5,0.3,0.2) -> (0.714286, 0.0, 0.285714)
```
Every multi-cell unit is byte-identical (no renorm). **[CODE + PROSE consistent]** This keeps the
text-blind baseline at 1.0 on both card shapes. `_score` output includes `rank_group`
("single"/"multi"), `weights_effective`, `cell_count`, `n_draws`, and the three components.

### 5.6 Aggregation / clip [PROSE — CONCEPTS.md §13, SCORING-AGGREGATION.md not shipped]
One board = equal-weight mean of normalized composites (1.0 = text-blind baseline). Inadmissible/
errored/unattempted card = **4.0** (worst of declared metric domain `[0.0,4.0]`); real scores
clipped at 4.0. **[PROSE caveat in the doc itself]**: the CURRENTLY DEPLOYED dev scorer still
*drops* failed cards instead of charging 4.0 — the 4.0 rule is what the signed plan commits to
for Final. Treat 4.0 as the design intent.

---

## 6. Admissibility gates g0–g3 — AS CODED

**[CODE — scoring.py `GATES` line 508; helpers in limits.py / cutoff.py / grid.py]** Hierarchical:
stop at first failure. Order is fixed (dev == final):

- **g0_integrity** (`_g0_integrity`): output dir exists; contains EXACTLY the three files
  `{forecast.parquet, forecast_meta.json, forecast_rationale.md}` — any UNEXPECTED entry →
  `SCHEMA_INVALID`. forecast.parquet is a regular file within size ceiling (no symlink, no FIFO,
  no hard link, ≤64 MiB — limits.py `stat_regular_file`). `forecast_meta.json` parses as a JSON
  object (bounded ≤256 KiB). FAILS on: missing output dir (`NO_OUTPUT`), extra files, non-regular
  node, unparseable meta.
- **g1_schema** (`_g1_schema`): `jsonschema.validate(meta, forecast.schema.json)` — validator is
  MANDATORY (missing jsonschema = OrganizerFault, never fail-open). Then: `representation` ∈
  `{"samples"}` (parametric refused); `n_draws` is a real int in `[200, 20000]`;
  `forecast_rationale.md` present + non-empty. FAILS → `SCHEMA_INVALID`.
- **g2_cutoff_resource** (`_g2_cutoff_resource`): binds meta to the TRUSTED card —
  `meta.asof == card asof`, `meta.unit_id == card [task].id`, `meta.target == card target_type`
  (if present); and checks every card target date strictly post-dates the as-of. FAILS →
  `CUTOFF_VIOLATION` / `SCHEMA_INVALID`. **NOTE [CODE — cutoff.py docstring]**: the actual
  panel-row scan and text-corpus-cutoff scan do **NOT** run inside g2 at scoring time (the scoring
  process only receives ref/res, not the participant mount); they run at PUBLICATION/staging via
  `scan_panel_cutoff` / `scan_text_corpus_cutoff` (organizer-side, fail-closed, abort on any
  post-asof row/doc, require corpus_index.json to match the dir both ways).
- **g3_domain_semantics** (`_g3_domain_semantics`): `check_declared_grid` (meta grid == committed
  grid, exact/ordered/no-repeats) THEN `build_sample_matrix` (footer row count == n_draws×cells,
  exact column set, contiguous 0-based draws, all labels in-grid, finite values, every cell once).
  FAILS → `SCHEMA_INVALID` / `INCOMPLETE_OUTPUT`.

**[PROSE — CONCEPTS glossary]** documents named flags `T2_UNCALIBRATED_MARGINAL`,
`T2_BAD_DEPENDENCE`, `T2_TAIL_MISCALIBRATION` as g3 sub-checks. **[CODE — NOT FOUND]**: the
shipped g3 implements grid/coverage/finiteness checks only; no std≈0 or coverage-tolerance flag
appears in the v2.3.1/v2.1.0 code. Treat those flag names as prose-only / unverified.

---

## 7. Per-family (F1–F4) input & target shapes  [PROSE — docs/CATEGORIES.md + DATA]

Composite is the same for all; families differ by which term dominates and text's role.

| Family | Test | Text role | Dominant term | As-of lead |
|---|---|---|---|---|
| F1 Continuation-with-context | incremental text on a well-seen series | refines | marginal CRPS (50%) | ≥6 mo before 1st target |
| F2 Text-cued regime shift | regime change signalled in text first; some cards TRANSFER to an asset ABSENT from panel | pivotal leading indicator | CRPS + tail (50%+20%) | ≥3 mo |
| F3 Cross-asset reasoning | text about one asset ⇒ joint move of correlated assets | cross-market inference | joint variogram (30%) | ≥1 mo |
| F4 Tail/shock-from-text | text foreshadows a shock ⇒ extreme outcomes | shock foreshadowing | tail penalty (20%) | ≥ horizon before shock |

- Targets always come from `card.toml [targets]`: `asset_ids` (ordered), `horizons` (business
  days, integers ≥1), `target_type` (`level`/`log_return`/`yield`), `target_dates` (sealed on
  participant cards), `value_unit`.
- **[DATA] Exemplar (F3-shaped)**: 4 assets × 1 horizon = **4-cell / multi-cell** → full 3-term
  composite. `n_draws` rec ≥500 for F3.
- **[DATA] F4 real (t2-F4-hike-cycle-2021Q4b)**: `asset_ids=["UST_2Y"]`, `horizons=[126]` =
  **1-cell / single-cell** → variogram=0, reweighted to (0.714·CRPS + 0.286·tail). rec ≥1000 draws.
- **[DATA] F2 transfer (t2-F2-fragile-five-brl-2013)**: target `["BRL"] @ horizon 64`,
  `value_unit="brl_per_usd"`, **single-cell**. BRL appears ONLY in `em_transfer_early.parquet`
  (early history 1995..2000-ish + a row at the as-of) and is ABSENT from the main `g10_fx_daily`
  panel — this is the "claim→band must fire from text alone" transfer configuration.
- **[PROSE]** joint draws: for multi-cell F3/F4, every draw MUST contain rows for ALL target
  (asset,horizon) cells (enforced by g3 exact-occupancy).

Practice counts **[PROSE — plan]**: F1=23, F2=27, F3=22, F4=31 (103 units); no answers shipped
(`reference/realized.parquet` absent → smoke score = None). **[DATA — confirmed: `units/` holds
103 dirs (1 EXAMPLE + F1/F2/F3/F4).]**

---

## 8. Real panel schema  ⚠ VARIES ACROSS UNITS  [DATA]

**There is NO single panel schema.** Confirmed by reading real bytes:

- **Exemplar `rates_daily.parquet`**: columns `[date, asset_id, value]` — dtypes
  `timestamp[ms]`, `large_string`, `double`. **NO `panel_id` column.** 516 rows,
  2024-01-02..2024-06-28, assets `{UST_2Y,UST_5Y,UST_10Y,UST_30Y}`.
- **F2 `g10_fx_daily.parquet`**: columns `[date, asset, value, panel_id]` — dtypes
  `date32[day]`, `string`, `double`, `string`. 33,700 rows, 2000..2013, 10 G10 crosses.
- **F2 `em_transfer_early.parquet`**: `[date, asset, value, panel_id]` — `date32[day]`,
  `large_string`, `double`, `large_string`.

**Implications for the loader (LOAD-BEARING):**
- Accept BOTH asset-column spellings **`asset` and `asset_id`** (base.py `_extract_series`
  confirms: requiring `asset_id` only returned empty for all 238 authored panels).
- `panel_id` is present in some panels, absent in others — do not require it.
- `date` may be `date32[day]` OR `timestamp[ms]` — normalize to a date.
- The plan's assumed `[date, asset, value, panel_id]` is TRUE for most authored panels but NOT
  for the exemplar. Loader must be tolerant on columns/dtypes and select `value` for the target
  asset with `date <= asof`.
- Multiple panel files per unit (e.g. F2 has `g10_fx_daily` + `em_transfer_early`). Read all
  `*.parquet` under the panels dir.

---

## 9. Real text corpus — layout & document shape  [DATA]

- Each unit has a `text/` dir with `corpus_index.json` + one `.txt` per document.
- **`corpus_index.json`** shape: `{card_id, asof, note, documents: [{doc_id, timestamp
  (YYYY-MM-DD), source, doc_type, file, note?}]}`. The staging cutoff scan requires the index to
  match the dir bidirectionally and every doc `timestamp <= asof`.
- **Document `.txt` format**: plain text. The EXEMPLAR docs carry a small header block
  (`SOURCE:`, `DATE:`, `DOC_TYPE:`, `DOC_ID:`, then `---`, then prose, then an `[EXEMPLAR STUB]`
  trailer). REAL docs (e.g. `bernanke_jec_testimony_2013.txt`) are full source prose with a
  free-form date/title header and NO structured key:value block — so parse dates from
  `corpus_index.json`, not the file header. `doc_type` values seen: `fomc_statement`,
  `fomc_minutes`, `beige_book`, `landmark`.
- **[PROSE + DATA]** minutes/COT/testimony timestamps in the index are PUBLIC RELEASE dates, not
  meeting/report dates (matters for cutoff). Docs are real central-bank prose (FOMC statements
  verbatim; some exemplar snippets are organizer paraphrase per manifest.json `source` notes).
- Claim-typing target: tightening/easing/restrictive/"greater confidence" tone → rate/FX
  direction, over genuinely messy real prose (paragraphs, not clean sentences).

---

## 10. Toolkit install / import requirements  [CODE — pyproject.toml x2, RUN]

- Track scorer package `qfbench2-track-forecasting` (v2.1.0) depends on **numpy>=2.1,
  pandas>=2.2, pyarrow>=18, jsonschema>=4.21** and:
  ```
  qfbench2-common @ git+https://github.com/Agenthon-2026/Agenthon2026-public.git@v2.3.1#subdirectory=common
  ```
  `jsonschema` is a PRODUCTION dep (g1 raises OrganizerFault if absent, never fail-open). The
  Dockerfile MUST install qfbench2-common or `ModuleNotFoundError: qfbench2_common`.
- `qfbench2-common` (2.3.1) requires **Python >=3.13**, deps `numpy>=1.26, scipy>=1.11,
  jsonschema>=4.21`; optional extras: `data`=[pandas>=2.2,pyarrow>=15], `nli`=[transformers,torch]
  (T4 only, not needed for T2). License CC-BY-NC-4.0.
- Key imports the scorer uses: `qfbench2_common.contracts` (FailureCode, OrganizerFault,
  RosterEntry — this is why v2.3.1 is the required pin), `qfbench2_common.scoring.crps`,
  `qfbench2_common.taskcard.schema_path`, `qfbench2_common.verifier` (HierarchicalVerifier,
  GateResult).
- **Console scripts**: from track repo → `forecast` (the submission verb,
  `qfbench2_track_forecasting.cli:main`) and `qfbench2-t2-score` (unranked local scorer). From
  toolkit → `qfbench2` and **`qfbench2-smoke`** (`qfbench2_common.smoke:_cli`).
- **`qfbench2-smoke` DOES exist** (toolkit, not deprecated). Invocation:
  `qfbench2-smoke <unit_dir> <output_dir> --track forecasting [--profile smoke|production]`.
  It validates card+manifest, then runs `build_verifier(ctx)` (forecasting has no separate
  `build_smoke_verifier`, so smoke and production use the same factory here). It imports
  `qfbench2_track_forecasting.scoring` — so the track package must be importable (on PYTHONPATH
  or installed).

---

## 11. RUN EVIDENCE — actual outputs captured

**[RUN] Exemplar end-to-end** (`bash run_example.sh`, gaussian-rw fallback, 500 draws):
```
baseline impl: gaussian-rw-placeholder
admissible: True
gate_results: {'g0_integrity': True, 'g1_schema': True, 'g2_cutoff_resource': True, 'g3_domain_semantics': True}
score: None   (None => public smoke: realized outcomes are sealed)
```

**[RUN] `qfbench2-smoke units/t2-EXAMPLE-ust-curve-1m <out> --track forecasting`:**
```
[t2-EXAMPLE-ust-curve-1m] factory=build_verifier admissible=True score=None labels=[]
```

**[RUN] Reference scorer CLI, gates-only** (`python -m qfbench2_track_forecasting.scoring score
--card .../card.toml --forecast .../output/forecast.parquet`):
```json
{ "card_id": "t2-EXAMPLE-ust-curve-1m", "admissible": true,
  "gates": {"g0_integrity":"pass","g1_schema":"pass","g2_cutoff_resource":"pass","g3_domain_semantics":"pass"},
  "scored": false, "note": "no --realized supplied: gates only, no score" }
```

**[RUN] Reference scorer CLI with a SYNTHETIC realized file** ([asset,horizon,value], the
`REALIZED_COLUMNS` set) — proves the full composite path and the raw component keys:
```json
{ "card_id": "t2-EXAMPLE-ust-curve-1m", "admissible": true,
  "gates": {"g0_integrity":"pass","g1_schema":"pass","g2_cutoff_resource":"pass","g3_domain_semantics":"pass"},
  "failure_labels": [], "normalization_mode": "raw_unrankable", "rankable": false,
  "marginal_crps": 0.0512..., "joint_variogram": 0.1411..., "tail_penalty": 0.2700...,
  "composite_score": 0.1219..., "n_draws": 500, "cell_count": 4 }
```
(Values depend on the invented realized numbers; the point is the KEYS + that
`0.5·0.0512 + 0.3·0.1411 + 0.2·0.2700 = 0.1219` reproduces the as-coded formula. The multi-cell
weights (0.5,0.3,0.2) are used — NOT reweighted, since cell_count=4.) Reference realized file
columns are exactly `(asset, horizon, value)` — flattened in plan order.

---

## 12. Downstream deltas this pins (vs the draft plan)

1. **Tail metric is COVERAGE-error `|cov−a|`, not pinball.** Optimize coverage calibration.
2. **Panel columns vary (`asset`/`asset_id`, ±`panel_id`, date32 vs timestamp).** Loader must be
   tolerant; do not hardcode `[date,asset,value,panel_id]`.
3. **Output = exact `n_draws×cell_count` long draws, every cell once, contiguous 0-based draws,
   `representation:"samples"` only.** No parametric, no duplicated/averaged cells.
4. **Sidecar key is `unit_id` == card `[task].id`; `asof`/`target` must bind to the card.**
5. **Joint variogram (30%) penalizes independent draws** — the F3/F4 gap is real and measured.
6. **Local runs are always RAW_UNRANKABLE** — you can reproduce gates + raw components, never the
   normalized leaderboard number; bring your own `--realized` for a local metric.
7. **Weights come from `card [scoring.params.weights]`** (default 0.5/0.3/0.2); single-cell auto-
   reweights to 0.714/0/0.286 in the scorer.

## Cited source locations (in .bigtmp, this workspace)

- Metric: `toolkit/common/qfbench2_common/scoring/crps.py` — crps_ensemble L52, crps_marginal L65,
  variogram_score L90, tail_penalty L110 (`err += abs(cov - a)` L123), crps_composite L130
  (composite L159).
- Gate stack / weights / reweight: `track2/qfbench2_track_forecasting/scoring.py` — LEADERBOARD_SORT
  L86, ACCEPTED_REPRESENTATIONS L98, reps check L315, single-cell reweight L461-468, crps_composite
  call L477, GATES L508.
- Grid / draws / columns: `track2/qfbench2_track_forecasting/grid.py` — FORECAST_COLUMNS ~L62,
  REALIZED_COLUMNS ~L70, check_declared_grid, build_sample_matrix, _place_exactly_once, flatten_realized.
- Limits / floors: `track2/qfbench2_track_forecasting/limits.py` — min_draws L86, max_draws L81,
  max_columns L78, inspect_parquet, expect_exact_rows, rationale_has_content.
- Cutoff binding: `track2/qfbench2_track_forecasting/cutoff.py` — bind_metadata, scan_panel_cutoff,
  scan_text_corpus_cutoff.
- Schema: `toolkit/common/qfbench2_common/schemas/forecast.schema.json`.
- CLI/mount: `track2/SUBMISSION_CLI.md`. Families: `track2/docs/CATEGORIES.md`,
  `track2/docs/CONCEPTS.md`. Smoke: `toolkit/common/qfbench2_common/smoke.py`.
- Exemplar: `track2/units/t2-EXAMPLE-ust-curve-1m/` (card.toml, manifest.json, run_example.sh,
  rates_daily.parquet, text/). Baseline shape: `track2/baselines/base.py`.
