# RESULTS — macro-release numeric-surprise mechanism

Measured against `MACRO_SURPRISE_PREREG.md` (the contract; nothing above its
MEASUREMENT GATE line was edited once numbers existed). Closes the one coverage
gap the induced-belief arc left open: H1 scored **0.0 on `macro_release`
snippets** because the ToM decode types a SPEECH ACT and a CPI/NFP print is not
a speech act — it is a NUMBER whose forecast relevance is its SURPRISE vs
expectation.

Architecture discipline (CLAUDE.md): the agent is a graph in Rust; Python is
only the world adapter. The macro mechanism adds ZERO new belief machinery — it
reuses the ToM arm's stance Concepts, `concept_apply_evidence`, the winning-
stance `Argmax` readout, and `grounding_reach` verbatim. The DECISION (which
stance a surprise is) is the seed rule `ib_decode_macro_surprise`; which sign of
a surprise is hawkish is the `MacroSurpriseSign` codebook DATA, keyed on series,
NOT a Python branch.

Code: `induced_belief/macro_surprise.py`, `induced_belief/macro_surprise_codebook.json`
(the seed rule), `induced_belief/macro_study_set.json` (the frozen hand-labels +
`macro_study_set.sha256`), `induced_belief/measure_hm1.py` / `measure_hm3.py`,
`induced_belief/gate_macro.py`. Wired behind the SAME `forecast_cli --text-arm tom`
flag, gated to `macro_release` doc_types. Result JSON: `hm1_results.json`,
`hm3_results.json`, `gate_macro_results.json`.

---

## Corrections to the prereg's stated premises (found while grounding, recorded before measuring)

The prereg made three factual claims about the corpus/panel that the real repo
contradicts. None change the mechanism; all are recorded here for honesty:

1. **The macro panel is per-unit `macro_monthly.parquet`, not a global
   `macro/releases_quarterly`.** `releases_quarterly` is only a logical name in
   prose. The on-disk realization is `<unit>/macro_monthly.parquet`, columns
   `[date, asset, value, panel_id]` (matches the prereg's row shape). Loaded via
   `t2_adapter.load_panels(unit_dir, asof)` + `asset_series`.
2. **GDP is NOT in the panel.** The series present are `CPI_ALL, CPI_CORE, NFP,
   PCE_ALL, PCE_CORE, UNRATE` — no GDP. The `MacroSurpriseSign` codebook keeps a
   harmless GDP entry (unused on this corpus).
3. **The two study-set `macro_release` snippets already had `gold != None`.**
   `phase3_derisk/study_set.json` s03/s52 are both `gold="up"` (the labelers DID
   assign a released-vs-prior direction). The prereg said they were `None`; they
   were not. The frozen extension re-states them (identical gold) and adds 15
   more real prints.

---

## The frozen hand-labeled study set (committed BEFORE measuring)

`induced_belief/macro_study_set.json` — **17** real `macro_release` CPI prints
from the cloned Track-2 corpus, each hand-labeled with the released-vs-prior (or
released-vs-recent-trend) direction per the rubric in the file's `_meta`,
**before** the mechanism was built or measured. The labels are frozen by
`macro_study_set.sha256` (verified `OK` after all measurement). Gold
distribution: **up=6, down=9, none=2** — deliberately NOT 50/50, so the >0.5
confirmation bar is a genuine threshold, not a coin flip. 10 prints carry an
explicit prior in the text (the quantitative-text path); 7 do not (prior=None,
routed to the panel-trend / released-sign path).

---

## The mechanism (as built)

    macro print (corpus Message, doc_type=macro_release)
      -> read_surprise: the SURPRISE read, I/O only, no verdict:
           (a) QUANTITATIVE text  — released vs the print's OWN stated prior
               ("rose 0.6% ... after rising 0.2%") -> surprise_sign
           (b) QUANTITATIVE panel  — released vs the series' recent trend/MA
               (panel_trend_baseline off macro_monthly)  -> surprise_sign
           (b') released-sign fallback — a signed print with no baseline
           (c) QUALITATIVE lexicon — "stronger/weaker-than-expected" etc.
         -> a bare surprise_sign in {+1, -1, 0} (above / below / inline)
      -> band_sign = surprise_sign x hawkish_sign, held per (series,
         surprise_sign) as taught DATA on MacroSurpriseSign nodes    [codebook DATA]
      -> MacroSurpriseReading{series, surprise_sign, market, surprise_motion}
         minted — the BARE read, no stance/direction computed in Python  [graph in]
      -> ib_decode_macro_surprise RULE (Eq-join on series AND surprise_sign)
         pulls (stance, band_sign, direction, attr) OFF the joined codebook node
         into a StanceReading — the SAME shape ib_decode_stance mints    [DECISION = rule]
      -> concept_apply_evidence on the SAME <stance>_stance_for:rates_market
         CAN Concept the ToM decode uses                               [REUSE — composes]
      -> force_all_dirty(); run_rules(): CAN relaxation                 [gotcha honored]
      -> winning stance = the held Argmax over the confirmed stance Concepts    [REUSE]
      -> grounding_reach(StanceReading) IS the confidence; no anchor -> GroundingGap, shift~0  [REUSE]
      -> shift = direction(winning stance) x grounding_weight.

`MACRO_SURPRISE_SIGN` (taught DATA): `CPI/CPI_CORE/PCE/NFP/GDP -> hawkish_sign
= +1` (above expectation = hotter/stronger = hawkish = band up). This is
expanded at teach time into one `MacroSurpriseSign` node per
`(series, surprise_sign)` carrying the full `(stance, band_sign, direction,
attr)` triple — the exact ToM `(symbol, motion) -> (stance, sign)` codebook
pattern. The DECISION (which stance) is the rule's `(series, surprise_sign)`
join pulling the triple off that node; Python computes no stance or direction.

---

## H-M1 — the headline: **CONFIRMED** (recovers direction where the ToM arm scored 0.0)

`measure_hm1.py` over the 17 frozen macro prints, macro-snippet directional
accuracy vs the ToM arm's **0.0** baseline on `macro_release`.

| | correct / n | accuracy |
|---|---:|---:|
| ToM decode (H1 baseline on macro_release) | 0 / 2 | **0.0** |
| **macro-surprise mechanism** | **17 / 17** | **1.000** |

**CONFIRMED** per the pre-declared rule (macro-snippet accuracy > 0.5; a coin
flip on the up/down subset is 0.5, the ToM arm's score was 0.0). Directional-only
(gold ∈ {up,down}): **15/15 = 1.000**.

By read path (`hm1_results.json` `by_source`):

| path | correct / n |
|---|---:|
| `quantitative_text` (released vs stated prior) | 10 / 10 |
| `released_sign` (signed print, no baseline) | 6 / 6 |
| `none` (unchanged/equal print -> abstain, gold=none) | 1 / 1 |

Every prediction is a real decode; no fabricated numbers. The frame's
anti-lexical discipline carries through: the mechanism reads the NUMBER's
direction (2.7 vs 2.6 → up; 0.3 vs 1.2 → down), never a polarity word.

**Honest scope of the 100%.** The perfect score is on a small (n=17), single-
annotator, CPI-dominated set where the released-vs-prior sign is unambiguous in
the text. It establishes that the mechanism *recovers the labeled direction*
where the ToM arm was silent — it is NOT a claim of live forecast skill (see
RAW_UNRANKABLE below). Two structural caveats that the score hides and this
document surfaces:

- **The 6 `released_sign` prints did NOT exercise the panel-trend path.** Their
  units ship only `rates_daily`, no `macro_monthly` — so there was no CPI series
  to read a trend from, and they fell to the released-sign fallback
  (released vs an implicit 0). The panel-trend path (b) IS functional and was
  verified independently on a panel-carrying unit
  (`t2-F4-cpi-vintage-2022`: CPI 0.6% released vs a trend-implied 0.70% m/m →
  below → dovish, `source=quantitative_panel`) — but this frozen study set did
  not happen to route any label through it. Recorded, not hidden.
- **NFP is typed only qualitatively, not by count.** The percent parser is
  gated OFF for NFP (`PERCENT_SERIES` excludes it) because an employment report
  has no percent headline — applying the percent parser grabbed a spurious
  earnings/workweek percent. NFP-by-count parsing ("rose by 225,000") is NOT
  implemented; NFP falls to the qualitative cue lexicon (on the covid empsit it
  matched "eased", a weak/borderline cue) or abstains. Declared future work.

---

## H-M2 — composes, does not regress the ToM arm: **CONFIRMED**

The macro path fires ONLY on `macro_release` doc_types; every other doc_type
goes through the UNCHANGED ToM speech-act decode.

- **`measure_h1.py` re-run is BYTE-IDENTICAL** to the committed `h1_results.json`
  (overall accuracy 0.846, non-FOMC ToM 0.727 (8/11), and every one of the 52
  per-snippet rows unchanged). Diff is empty. The ToM decode path is not touched
  by the macro code.
- **The exemplar g0–g3 gate is BYTE-IDENTICAL** to the committed
  `gate_g0g3_results.json`: `--text-arm tom` still emits `UST_2Y: 0.3333` on the
  non-macro exemplar, with the macro mechanism installed. So the macro path,
  present in the wired arm, does not leak into non-macro reads.

**CONFIRMED** per the pre-declared rule (non-macro numbers unchanged; the macro
path is strictly gated). The composition is real: on `t2-F2-some-pain-2022` the
macro CPI print typed to `none` (an "unchanged in July" print, no surprise) and
the unit's `UST_10Y: 0.3333` signal came from the ToM decode of the FOMC docs —
macro and ToM coexisting on one belief, macro contributing only when it has a
surprise to contribute.

---

## H-M3 — surprise → composite via the shift: **LITERAL-CONFIRMED, but SHIFT-ARTIFACT CONFOUNDED (the pre-committed partial branch)**

**RAW_UNRANKABLE.** Every number is on `make_realized_text_aware` (H2_RESOLUTION's
direction-aware PROXY, reused verbatim) with the REAL scorer
`qfbench2_common.scoring.crps.crps_composite`. The proxy's gold direction is the
macro decode's OWN direction — it is *sympathetic to the decode by construction*
and is NOT the sealed organizer outcome.

`measure_hm3.py`, 46 macro-carrying units (24 carry a non-zero macro direction),
realized seeds 0–7, n_draws=1000, `no_shift` vs `macro_shift` (the macro decode's
graded `sign × grounding_weight` scaled into the flat 0.1σ band):

| p_signal | e | no_shift comp | macro_shift comp | Δcomp | ns tail | macro tail |
|---|---|---:|---:|---:|---:|---:|
| 0.0 | 0.5 | 14.71464 | 14.43595 | −0.27869 | 0.24270 | 0.24560 |
| 0.0 | 1.0 | 14.71464 | 14.43595 | −0.27869 | 0.24270 | 0.24560 |
| 0.3 | 0.5 | 15.20593 | 14.92447 | −0.28146 | 0.24249 | 0.24538 |
| 0.3 | 1.0 | 15.70520 | 15.42286 | −0.28234 | 0.24339 | 0.24629 |
| 0.5 | 0.5 | 16.70755 | 16.41955 | −0.28799 | 0.24169 | 0.24459 |
| 0.5 | 1.0 | 18.76828 | 18.47614 | −0.29214 | 0.24260 | 0.24549 |
| 0.7 | 0.5 | 17.22950 | 16.94110 | −0.28840 | 0.24214 | 0.24504 |
| 0.7 | 1.0 | 19.81142 | 19.51868 | −0.29273 | 0.24350 | 0.24640 |

**Literal criterion PASSES: `composite(macro_shift) < composite(no_shift)` in
6/6 signalled cells.** But this is NOT a clean win, and reporting it as one would
be dishonest:

- **The confound.** At `p_signal=0` (the proxy carries NO gold signal), the
  macro_shift already beats no_shift by **−0.2787** — the SAME magnitude as the
  signalled-cell gain (−0.29). The improvement is overwhelmingly a
  *direction-independent* shift-toward-proxy-center artifact on these large-
  level single-asset macro units (composites ~15–20, series like CPI_ALL≈260 /
  NFP≈150 000), not a reward for correct direction. This is the exact
  direction-agnostic-proxy trap the H2 resolution documented, appearing here
  because the units are single-asset levels.
- **The real, small direction effect.** Stripping the artifact
  (`signalled_delta − empty_signal_delta` at the same `e`) gives the
  DIRECTION-ATTRIBUTABLE gain:

  | p_signal | e=0.5 | e=1.0 |
  |---|---:|---:|
  | 0.3 | −0.00277 | −0.00365 |
  | 0.5 | −0.00931 | −0.01345 |
  | 0.7 | −0.00972 | −0.01405 |

  This is small (mean **−0.0088**) but **all negative** and **monotone in both
  `p_signal` and `e`** — the signature of a genuine direction effect (more
  correctly-signalled cells, and a stronger effect, buy a bigger correct-
  direction gain). So the surprise direction IS forecast-relevant, but at the
  raw composite level on level-scale macro units the shift-center artifact
  dominates it ~30×.

**Verdict: the pre-committed H-M3 partial branch** — "the direction is
recoverable but the shift does not [cleanly] convert it to composite; localises
to the shift, not the surprise read." The direction read (H-M1) is sound; the
band-shift magnitude/shape on single-asset level series is the remaining lever
(as H2b already found: `grounding_weight` attenuates by confidence, not by
effect size). We report the confound and do not tune it away.

---

## Wire-in — admissible g0–g3 behind the flag

`gate_macro.py` runs the organizer's own `scoring.scoring.build_verifier`
(the SAME gate `run_example.sh` runs) on two macro-carrying units, both arms:

| unit | asset | arm | admissible | g0 | g1 | g2 | g3 | macro path fired |
|---|---|---|---|---|---|---|---|---|
| `t2-F2-some-pain-2022` | UST_10Y | off | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| `t2-F2-some-pain-2022` | UST_10Y | tom | ✅ | ✅ | ✅ | ✅ | ✅ | cpi_2022-08-10 (none, no surprise) |
| `t2-F4-covid-nfp-2020` | NFP | off | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| `t2-F4-covid-nfp-2020` | NFP | tom | ✅ | ✅ | ✅ | ✅ | ✅ | empsit x2 (NFP, qualitative) |

Plus the exemplar `t2-EXAMPLE-ust-curve-1m` (non-macro) unchanged from the
committed gate. All admissible; the macro path fires exactly on `macro_release`
docs (`path=macro_surprise` in the per-doc debug) and nowhere else. (Scores are
`None` under the public smoke — realized outcomes sealed.)

Reproduce:

    PYTHONPATH=runners/dsl/python:.bigtmp/track2 OZMA_SEED_PERSIST_DISABLED=1 \
      .bigtmp/t2venv/bin/python drafts/seldon_t2_text/induced_belief/measure_hm1.py
    PYTHONPATH=runners/dsl/python:.bigtmp/track2 OZMA_SEED_PERSIST_DISABLED=1 \
      .bigtmp/t2venv/bin/python drafts/seldon_t2_text/induced_belief/measure_hm3.py \
      --units .bigtmp/track2/units --realized-seeds 0,1,2,3,4,5,6,7 --n-draws 1000 \
      --p-signals 0.0,0.3,0.5,0.7 --effects 0.5,1.0 \
      --json-out drafts/seldon_t2_text/induced_belief/hm3_results.json
    PYTHONPATH=runners/dsl/python:.bigtmp/track2 OZMA_SEED_PERSIST_DISABLED=1 \
      .bigtmp/t2venv/bin/python drafts/seldon_t2_text/induced_belief/gate_macro.py

---

## Proven-vs-assumed ledger

**PROVEN (measured, this run):**
- H-M1: macro-snippet directional accuracy **17/17 = 1.000** vs the ToM arm's
  0.0 on `macro_release`, on the frozen (sha256-checksummed) hand-labeled set
  committed before measuring. Real decode on every snippet.
- H-M2: `measure_h1.py` BYTE-IDENTICAL to committed `h1_results.json`; exemplar
  g0–g3 BYTE-IDENTICAL to committed `gate_g0g3_results.json`. The macro path is
  strictly gated to `macro_release` doc_types and does not touch non-macro reads.
- H-M3 direction-attributable gain is negative and monotone in `p_signal`/`e`
  (a real, small direction effect on the direction-aware proxy).
- g0–g3 admissible on the exemplar + `t2-F2-some-pain-2022` +
  `t2-F4-covid-nfp-2020`, both arms, under the real organizer verifier.
- The mechanism reuses the ToM stance Concepts, `concept_apply_evidence`, the
  `Argmax` readout, and `grounding_reach` verbatim; the DECISION is the seed
  rule `ib_decode_macro_surprise`; which sign is hawkish is `MacroSurpriseSign`
  DATA. No new belief mechanism, no Python decision over graph state, no
  substrate/`domains`/`worlds`/`seeds` edit (the whole arm lives under untracked
  `drafts/seldon_t2_text/`). The panel-trend path was verified functional on a
  panel-carrying unit.

**PARTIAL / HONEST-NULL:**
- H-M3: the LITERAL criterion passes 6/6 but is **confounded** — the empty-signal
  (`p_signal=0`) composite gain (−0.28) equals the signalled gain (−0.29), so the
  raw win is a direction-independent shift-center artifact on large-level single-
  asset units. The genuine direction effect is the small (−0.0088) monotone
  residual. Localises the remaining work to the shift magnitude on level series,
  not the surprise read. Not tuned away.
- NFP is typed only via the qualitative cue lexicon (a weak "eased" match on the
  covid empsit), not a real payroll-count surprise; NFP-count parsing is unbuilt
  future work.
- The 7 prior=null study snippets never exercised the panel-trend path (their
  units ship no `macro_monthly`); they used the released-sign fallback. The
  panel path is proven functional but under-exercised by this frozen set.

**ASSUMED (not independently verified this run):**
- All H-M3 scores are RAW_UNRANKABLE: no ranked/normalized organizer number is
  obtainable locally (sealed outcomes). The proxy's gold direction IS the macro
  decode's own direction, so the proxy is sympathetic to the decode by
  construction; it can show that IF the print-implied direction is the truth the
  shift helps, it cannot certify the print-implied direction IS the sealed truth.
- H-M1's 1.000 is on a small (n=17), single-annotator, CPI-dominated set; it is
  a directional-recovery result, not a live-skill claim.
- The macro reads (`parse_released_prior`, `panel_trend_baseline`,
  `qualitative_surprise`) are thin I/O-boundary tokenizers/parsers over surface
  forms and panel numbers; they carry no up/down verdict (the codebook rule +
  marginal do), but they ARE regex/arithmetic readers, honest about being
  boundary translators.

---

## Files

- `induced_belief/macro_surprise.py` — the surprise read (both quantitative
  paths + the qualitative lexicon), the `MacroSurpriseSign` codebook (taught
  DATA), and `decode_macro_surprise` (marshal-in / tick / read-out, reusing the
  ToM arm's helpers verbatim).
- `induced_belief/macro_surprise_codebook.json` — the seed: the
  `ib_decode_macro_surprise` rule (Eq-join MacroSurpriseReading × MacroSurpriseSign
  → StanceReading, the same shape ib_decode_stance produces).
- `induced_belief/macro_study_set.json` (+ `.sha256`) — the frozen hand-labeled
  17-print macro-direction study set, committed before measuring.
- `induced_belief/measure_hm1.py` / `measure_hm3.py` — the H-M1 / H-M3 harnesses.
- `induced_belief/gate_macro.py` — the g0–g3 wire-in gate on macro units.
- `induced_belief/hm1_results.json` / `hm3_results.json` /
  `gate_macro_results.json` — the raw measured outputs.
- `forecast_cli.py` — `--text-arm tom` now composes the macro path
  (`_derive_text_signal_tom`, gated to `macro_release`).
