# PHASE 3 DE-RISK — PREREGISTRATION

**Written BEFORE measuring.** This file fixes the hypotheses, the study set, the two
typers, the metrics, and the decision rule. `PHASE3_DERISK_RESULTS.md` reports the outcome
against exactly this spec. No metric or lexicon entry is added after seeing the numbers;
any deviation is logged in the results file as a deviation.

Provenance discipline follows PHASE0: **[RUN]** = executed here, real number; **[MOCK]** =
architecture exercised against a stubbed response, live number NOT obtained; **[ASSUMED]** =
stated expectation, not measured.

---

## 1. The question this de-risks

The Track 2 submission plan names the **highest-risk unknown**: the PoC's clean text-uplift
(~6%) leaned on **leg-iii claim-typing being ~100% by fixed-template construction**. In
`corpus_gen.py` every regime-1 item is rendered from a template that literally contains a
directional cue word ("raise / surge / expand"); `ingest.py::_type_claim` then recovers it by
a 7-word lexicon overlap. On that corpus, typing recall is ~100% *by design*.

On REAL FOMC/ECB/headline prose that guarantee is gone. The direction that matters for the
forecast is the **forward-guidance / regime tone**, which:

- is frequently **opposite in sign to the surface action verb** (a 25bp *cut* delivered with a
  shallower dot-plot is *hawkish* for the 2Y → `t2-F1-hawkish-cut-2024`);
- is carried by verbs whose lexical polarity is inverted in context (*taper* = "**reduce** the
  pace of asset purchases" is **hawkish**; QE = "**increase** ... holdings" is **dovish**);
- is sometimes carried by sentences with **zero directional-cue vocabulary** ("ready to do
  whatever it takes to preserve the euro"; an SVB emergency-capital 8-K; a CFTC positioning
  extreme).

**PHASE0 §9** already flagged this: "Claim-typing target: ... tone → rate/FX direction, over
genuinely messy real prose (paragraphs, not clean sentences)." **PHASE0 §12 / plan mismatch
#3**: "Real claim-typing over FOMC prose replaces the 'leg-iii 100% by construction' caveat —
becomes the live problem."

**This stage tests whether the ceiling actually moves from entity LINKING to claim
EXTRACTION.** Prior stages established entity linking as the ceiling; the PoC's near-perfect
typing hid extraction. If a rules-only typer collapses on real prose, extraction is the new
ceiling and the uplift story from the PoC does not transfer.

---

## 2. Study set (frozen before measurement)

- **File**: `phase3_derisk/study_set.json`. **52 snippets** (target was ~50).
- **Real** central-bank / macro prose, **VERBATIM** from the cloned Track 2 corpus
  (`.bigtmp/track2/units/<unit>/text/<file>`). Extraction aid: `extract_snippets.py`
  (mechanical sentence surfacing + hand selection of the load-bearing sentence). Two entries
  (`s39` SVB 8-K, `s46` CFTC COT) are marked `trim=true`: they are labelled descriptions of a
  filing / tabular positioning report, not clean prose — deliberately included as the extreme
  "no policy vocabulary at all" cases. Everything else is a verbatim sentence.
- **Coverage**: F1/F2/F4 units; doc types `fomc_statement` (41), `cb_speech` (7),
  `macro_release` (2), `corporate_8k` (1), `positioning_report` (1). (F3 units share the same
  FOMC/CB prose surface; F3's distinctive difficulty is *joint* cross-asset structure, out of
  scope for a per-snippet typing test — noted, not a gap for this question.)
- **Label space**: `{up, down, none}`.
  - `up`  = hawkish / tightening / restrictive / less-easing-than-priced → rates band UP.
  - `down`= dovish / easing / accommodative / backstop / less-tightening-than-priced → rates band DOWN.
  - `none`= neutral, on-hold with balanced risks, or pure descriptive data with no directional
    policy implication.
- **Labelling rule**: direction is the **forecast-relevant** move implied by the text's tone,
  anchored on the organizer's unit intent (unit name + card `[text].notes` + `[targets]`),
  **NOT** the surface action verb. Single annotator.
- **Label distribution (frozen)**: `up=26, down=19, none=7`.
- **Deliberate trap subset** (the cases that separate a lexicon from real understanding):
  `s01` hawkish-cut guidance, `s02` cut-action-in-hawkish-unit, `s07/s09` negated/conditional
  increases that are dovish, `s12` "increases in interest rates" inside a dovish cooling
  narrative, `s16/s34/s41/s50` taper/QT (reduce = hawkish), `s19` "premature tightening"
  warning (dovish), `s21` hawkish hold, `s22/s23` whatever-it-takes (dovish, no cue words),
  `s29`/`s31` identical sentence in two different units, `s32` QE (increase = dovish),
  `s39` SVB 8-K shock, `s46` COT positioning extreme.

The study set is committed as-is. No snippet is added, removed, or relabelled after any typer
is run.

---

## 3. Typer A — RULES-ONLY (OCELOT-native, no network) — [will be RUN]

Extends the PoC `ingest.py` cue-lexicon approach into a **real macro/monetary lexicon**,
staying inside OCELOT world-adapter discipline (mechanical, no reasoning, no network, no model
weights). Committed design (frozen before measurement):

1. **Hawkish (→ up) lexicon**: tighten*, restrictive, firming, raise/hike/higher rates,
   liftoff, taper / reduce (asset) purchases, balance-sheet reduction / runoff / QT, remove
   accommodation, "measured" removal, inflation upside / elevated / firm, ongoing increases,
   sufficiently restrictive, hot/beat CPI (number rising).
2. **Dovish (→ down) lexicon**: ease/easing, cut/lower rates, accommodat*, QE / asset purchase
   expansion / increase holdings, downward pressure on rates, patient, considerable period /
   time, lower-for-longer, backstop / whatever it takes / preserve, downside risk, inflation
   easing / softening, greater confidence (pre-cut framing), rate relief.
3. **Neutral / balanced (→ none) lexicon**: roughly balanced/equal risks, little changed,
   maintain/keep unchanged (absent a directional modifier), on hold, monitor.
4. **Polarity-flip / negation handling** (the load-bearing addition vs the PoC): a small set of
   context rules so the lexicon does not fire on surface polarity —
   - "reduce/reducing the pace of asset purchases", "reduce ... balance sheet", "runoff" → **up**
     (taper/QT), overriding the generic dovishness of "reduce".
   - "increase ... holdings / asset purchases", "expand ... purchases" → **down** (QE),
     overriding the generic hawkishness of "increase".
   - a negation window ("unlikely", "not ... appropriate to raise", "premature tightening ...
     risk of", "increases ... later") flips or suppresses the matched cue.
5. **Scoring within the typer**: weighted cue tally; hawkish − dovish sign → up/down; if both
   ~0 or a neutral cue dominates → none. Ties → none (honest abstain), as in the PoC.

The lexicon + rules are **committed in `rules_typer.py` before the confusion matrix is read**.
The flip rules are motivated by the *linguistic phenomenon* (documented in PHASE0 §9 and the
snippet notes), not tuned to individual snippet outcomes. Any post-hoc edit is logged as a
deviation in the results.

## 4. Typer B — MODEL_ENDPOINT (LLM via organizer proxy) — [will be MOCK only]

Implements the **call path** a submission would use at run time:

- Read `MODEL_ENDPOINT`, `MODEL_NAME`, `HTTP_PROXY`/`HTTPS_PROXY` from env (never hardcoded),
  POST an **OpenAI-compatible** `/v1/chat/completions` request through the audited proxy, with
  a fixed system+user prompt that asks for a strict-JSON `{direction, confidence}` typing.
- Parse the JSON out of the completion; map to `{up, down, none}`.
- **No network is available locally** (PHASE0 §1: T2 net is restricted; local smoke is
  `--network=none`; vendor APIs refused; no participant keys). So Typer B is exercised against a
  **stubbed/mock transport** that returns a canned OpenAI-shaped response. This proves the
  request-build → send → parse → map ARCHITECTURE end-to-end. **It does NOT produce a live
  accuracy number.** The live number requires the house endpoint and is explicitly out of reach
  here.

I will **not** fabricate a live LLM accuracy. The results file states plainly: architecture
proven [MOCK]; live number pending house endpoint [not obtained].

---

## 5. Metrics (frozen)

Computed by `measure.py` over the 52-snippet study set:

1. **Overall accuracy** = correct / 52.
2. **Per-class precision / recall / F1** for `up`, `down`, `none`.
3. **3×3 confusion matrix** (rows = gold, cols = predicted).
4. **"Forecast-usable direction" recall** = of the 45 directional (up/down) snippets, the
   fraction typed with the CORRECT direction. This is the number that matters for uplift: a
   directional claim typed the WRONG way is worse than an abstain (it pushes the forecast the
   wrong way). Reported alongside a **wrong-direction rate** (up gold typed down, or vice
   versa) — the actively-harmful error.
5. **Trap-subset accuracy** on the ~18 flagged trap snippets, reported separately, because the
   trap subset is where a lexicon is expected to fail and where the extraction ceiling lives.

For Typer B: report only that the mock request/parse path returns a well-formed typing for all
52 snippets ([MOCK] architecture check), plus one printed example request+response.

---

## 6. Hypotheses (stated before measurement)

- **H1 [ASSUMED]**: Rules-only overall accuracy on real prose is **materially below** the PoC's
  ~100% typing — predicted **0.45–0.70** overall, driven down by the trap subset.
- **H2 [ASSUMED]**: Rules-only **wrong-direction rate is non-trivial (≥15%)** on the directional
  snippets, concentrated in the polarity-flip cases (taper/QE) and zero-cue cases
  (whatever-it-takes, SVB, COT) — even WITH the flip rules, because zero-cue signals have
  nothing to match.
- **H3 [ASSUMED]**: The flip/negation rules recover *some* trap cases (taper/QT, QE, negated
  increases) but **cannot** recover the zero-vocabulary signals; those remain the residual
  ceiling.
- **H4 [MOCK]**: The MODEL_ENDPOINT architecture (build→proxy→parse→map) works against the
  mock for all 52 snippets. Whether the live model clears the extraction ceiling is **untested
  here** and is the explicit open item for the house-endpoint run.

## 7. Decision rule — "did the ceiling move to extraction?"

Fixed before measurement. Read off the rules-only [RUN] numbers:

- **Ceiling MOVED to extraction** if EITHER: forecast-usable directional recall **< 0.80**,
  OR wrong-direction rate **≥ 0.15**, OR trap-subset accuracy **< 0.50**. In that case the
  PoC's uplift story does **not** transfer on rules-only typing: extraction, not linking, is
  the binding constraint, and the architecture decision (rules-only vs MODEL_ENDPOINT) becomes
  load-bearing for uplift.
- **Ceiling did NOT move** (rules-only is good enough) if forecast-usable directional recall
  **≥ 0.80** AND wrong-direction rate **< 0.15** AND trap-subset accuracy **≥ 0.50**. Then
  rules-only typing transfers and the MODEL_ENDPOINT path is an optional robustness upgrade,
  not a necessity.

The verdict in the results file is whichever branch the real numbers select — reported even if
it contradicts H1–H3.

## 8. What stays PROVEN vs ASSUMED in the results

- **PROVEN [RUN]**: rules-only precision/recall/confusion/wrong-direction/trap numbers on 52
  real snippets; the study set is real verbatim prose.
- **PROVEN [MOCK]**: MODEL_ENDPOINT request/parse/map architecture.
- **ASSUMED / NOT OBTAINED**: the live MODEL_ENDPOINT accuracy number. It needs the house
  endpoint. It will be labelled as such and NOT fabricated.
- **Scope caveat**: single annotator; 52 snippets is a de-risk probe, not a calibrated
  benchmark; F3 joint-structure difficulty is out of scope for a per-snippet typing test.
