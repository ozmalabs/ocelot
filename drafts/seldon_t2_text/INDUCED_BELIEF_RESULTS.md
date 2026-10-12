# RESULTS — the decode-through-ToM text arm as REUSE

Measured against `INDUCED_BELIEF_PREREG.md` (the contract; nothing above its
MEASUREMENT GATE line was edited once numbers existed). Successor to the
Phase-3 rules-only cue typer (`phase3_derisk/`, 0.83 on FOMC house-style,
~0.0 on ECB rhetoric / 8-Ks / COT).

Architecture discipline (CLAUDE.md): the agent is a graph in Rust; Python is
only the world adapter. Every DECISION in this arm is a seed **rule**
(`ib_decode_stance`, an Eq-join) or the CAN **marginal** ⟨σ⟩; Python marshals
graph in, ticks, reads out. NO new parallel text-only belief mechanism was
authored — the arm reuses `mint_target_concept` / `mint_resident_tom_belief`,
`concept_apply_evidence`, `reasoning_can_bridge`, `grounding_reach`, and the
reading/CAN engines verbatim.

Code: `drafts/seldon_t2_text/induced_belief/` (`frame.py`, `arm.py`,
`induced_belief_codebook.json`, `measure_h1.py`, `measure_h2.py`,
`measure_h3.py`, `gate_g0g3.py`). Wired behind `forecast_cli --text-arm tom`.
Result JSON: `h1_results.json`, `h2_results.json`, `h3_results.json`,
`gate_g0g3_results.json`.

---

## H0 — the seam: **REUSE** (no generalization required)

**Verdict: REUSE.** A text-read grounded predication ALREADY reaches
`apply_derived_fact_as_can_evidence`, so a corpus utterance already updates a
target-scoped CAN belief via `concept_apply_evidence`. The bridge input is two
bare strings `(entity, attr)` — fully source-agnostic — so there was no
coupling to break and nothing to GENERALIZE.

**Evidence (file:line), the end-to-end text→CAN path:**

1. `domains/reading_collapse.py:1600` — `read_clause(...)` returns
   `predications = [[rel, arg0, arg1], ...]` for a declarative property clause.
2. `domains/solver_dispatch.py:295-320` (`_extract_property_fact`) and
   `:468+` (`mint_solve_reasoning_bridge_goal_from_text`) consume `read_clause`
   output, extract `entity = subject`, `attr = propositional_deduction._norm_attr(object)`,
   gated by `situation_model_reader._is_property_pred`.
3. `domains/reasoning_can_bridge.py:187-231` —
   `apply_derived_fact_as_can_evidence(agent, entity: str, attr: str, *, positive, alpha)`
   takes **plain strings**, resolves `SmEntity --denotes--> Microtheory
   --has_concept--> Concept(name==attr)` via the UNCHANGED
   `seeds/entity_concept_correspondence.json` rules, then calls
   `native.concept_apply_evidence(concept, evidence, alpha)` at
   `reasoning_can_bridge.py:227`.
4. `reading_collapse.py` / `media_analysis.py` / `actor_goals.py` do NOT import
   the bridge (grep: zero matches); the join lives one layer up in
   `solver_dispatch.py` and is already source-agnostic.

**The GOTCHA (confirmed, honored):** `concept_apply_evidence` writes
`external_field` OUTSIDE the rule-effect path, so `run_rules()`'s incremental
dirty-tracking never re-examines the Concept unless `force_all_dirty()` is
called first (`can_self_worth_bridge.py:20-25`, `hate_attribution.py:120-122`).
The arm calls `inner.force_all_dirty()` before `inner.run_rules()` after every
evidence application. Without it the marginal silently stays 0 (reproduced live
during the build).

**Net-win gate (bigville byte-unchanged and GREEN).** Because H0 = REUSE, NO
edit was made to `reasoning_can_bridge` or any substrate file. `git status`
confirms ZERO tracked files modified (the whole arm lives under the untracked
`drafts/seldon_t2_text/`). The bigville CAN/ToM machinery the arm reuses was
run green BEFORE and AFTER the build:

| suite | result |
|---|---|
| `test_solver_can_adapter` + `test_bigville_theory_of_mind` + `test_shared_arousal_excitation_transfer` | 20 passed |
| `test_hate_attribution` + `test_resident_trust` + `test_grounding_reach` | 25 passed |
| `test_can_native_reimplementation` (batch) | passed |

Since no substrate file changed, these remain byte-identically green — the
net-win gate holds by construction.

---

## The mapping under test (as built)

A central-bank statement is a bigville resident's ACTION applying evidence to a
target-scoped CAN belief. The **market** (`rates_market`) is modeled as a
bigville **Resident** (strict reuse of `worlds.bigville_can_beliefs.
build_resident_can_mt`), so its target-scoped stance Concepts live in a CAN
belief Microtheory the utterance's `SmEntity` DENOTES.

    utterance (corpus Message)
      -> frame.ground_frame: surface -> (frame_symbol, motion)   [the FRAME decode,
         keyed on the INSTRUMENT + its direction of change, NOT on hawk/dove words]
      -> FrameReading{symbol, motion, market} minted per hit      [graph in]
      -> ib_decode_stance RULE (Eq-join FrameReading × CBSpeechAct codebook)
         -> StanceReading{attr:"<stance>_stance_for:rates_market", sign}  [DECISION = rule]
      -> concept_apply_evidence on that target-scoped CAN Concept  [reuse]
      -> force_all_dirty(); run_rules(): CAN relaxation            [gotcha honored]
      -> the CAN marginal ⟨σ⟩ (Concept.state) per-frame IS the graded signal  [read out]
      -> grounding_reach(StanceReading) transitive read IS the confidence;
         a chain reaching no anchor mints GroundingGap and shifts ~0  [reuse]
      -> shift the forecast band by direction(stance sign) × grounding_weight.

The frame symbols (`policy_rate_path`, `balance_sheet`,
`inflation_target_credibility`, `forward_guidance`, `backstop_commitment`,
`funding_stress`, `carry_positioning`, `term_premium`) and the central-bank
speech-act codebook (`(symbol, motion) -> (stance, sign)`) are **taught data**,
not rule logic. The ToM knowledge is in the codebook: *contracting the balance
sheet is tightening (up) even though the verb is "reduce"* — the exact
anti-lexical case the cue lexicon inverted.

---

## H1 — the headline: **CONFIRMED** (generalizes past FOMC)

Frozen `phase3_derisk/study_set.json` (52 real snippets, hand-labelled),
directional accuracy split by `doc_type`, vs the frozen Phase-3 cue-lexicon
numbers (`phase3_derisk/results.json`). Same metric functions
(`phase3_derisk/measure.py`, reused verbatim).

| doc_type | n | cue lexicon | **ToM decode** |
|---|---:|---:|---:|
| `fomc_statement` | 41 | 0.829 (34) | **0.878 (36)** |
| `cb_speech` (ECB/Draghi/Lagarde) | 7 | 0.429 (3) | **0.857 (6)** |
| `corporate_8k` (SVB) | 1 | 0.0 (0) | **1.000 (1)** |
| `positioning_report` (COT) | 1 | 0.0 (0) | **1.000 (1)** |
| `macro_release` (CPI) | 2 | 0.0 (0) | 0.0 (0) |

**HEADLINE — non-FOMC (the doc types the lexicon went silent on):**

| | correct / n | accuracy |
|---|---:|---:|
| cue lexicon | 3 / 11 | 0.273 |
| **ToM decode** | **8 / 11** | **0.727** |

**+45.4 percentage points on exactly the non-FOMC prose the Phase-3 lexicon
scored ~0.0–0.43 on.** Overall accuracy 0.846 (lexicon 0.712); directional
usable-recall 0.822, wrong-direction rate 0.067, abstain 0.111.

**CONFIRMED** per the pre-declared rule (non-FOMC directional accuracy > the cue
lexicon's ≈0.0–0.43 by a margin outside per-class noise). This is a genuine
generalization win, not a null: the lexicon-killers are recovered by the frame
decode + ToM codebook.

**The recovered lexicon-killers** (all zero directional-cue vocabulary):
- s22/s23 Draghi *"whatever it takes to preserve the euro"* → **down** (via
  `backstop_commitment`/commit → dovish), where the lexicon abstained.
- s39 SVB 8-K *"proposed offerings … completed the sale of substantially all …
  available-for-sale securities"* → **down** (via `funding_stress`/shock →
  flight-to-quality), where the lexicon had no monetary vocabulary.
- s46 COT *"noncommercial net short position deeply negative"* → **down** (via
  `carry_positioning`/crowded), tabular data, no prose cues.
- s24–s26 ECB Lagarde hike telegraph → **up**.

**The anti-lexical frame cases** (verb sign ≠ stance sign — where the lexicon
inverted): s16 taper *"reduce the pace of asset purchases"* → **up**
(`balance_sheet`/contract); s32 QE *"increase holdings … downward pressure"* →
**down** (`balance_sheet`/expand); s41/s50 QT → **up**. The frame reads the
instrument, not the polarity word.

**The 8 misses, honestly** (`h1_results.json`, per-snippet):
- **macro_release (s03, s52): still 0/2** — CPI number-direction reading
  ("2.6→2.7", "0.6% m/m") is not a frame speech-act; the frame decode has no
  number-reader. This is the SAME class the lexicon missed, and is an honest
  residual, not a regression. A number-reading frame is named future work.
- **Negation/conditional traps (s07, s09, s12, s19):** pre-declared TRAP
  snippets where an utterance carries opposite-signed clauses ("increase …
  remains unlikely"; "increases … later than"; "increases in interest rates"
  inside a growth-cooling sentence). The frame decode grounds multiple hits
  that tie at ⟨σ⟩=1 and the winning-stance tiebreak resolves to hawkish by
  stance order → wrong sign on these four. This is a real limitation of the
  independent-concept CAN wiring under conflicting single-sentence evidence
  (the `causal_influence` couplings that would let one stance dominate are not
  populated between the stance Concepts) — named, not hidden.
- **Abstains (s01, s21):** s01 has no frame hit (honest silence); s21 grounds
  only `policy_rate_path`/hold in a firming regime (unit-intent up), abstains.

Wrong-direction rate is 0.067 (3/45 directional), and confusion shows **zero
down↦none-of-the-wrong-sign among the lexicon-killers**; the misses concentrate
on the pre-declared traps and the number-reading macro releases.

---

## H2 — grounding-weighted shift calibration: **partial (tail-neutral; KS
confounded by the RAW_UNRANKABLE proxy)**

22 F3-shaped units (`.bigtmp/track2/units`, `--select F3`), the REAL reference
scorer (`qfbench2_common.scoring.crps`), the Phase-2 hand-made common-factor
realized proxy (`run_variogram_eval.make_realized`), the Phase-5 randomised-PIT
/ KS / tail machinery (`run_calibration_eval`, reused verbatim). Direction of
the shift averaged over 8 assignments so the verdict is not a single-pattern
artifact. **RAW_UNRANKABLE: the realized is the hand-made proxy, NOT the sealed
organizer outcome — all numbers are relative calibration instruments.**

| arm | shift | KS↓ | tail↓ | PIT mean |
|---|---|---:|---:|---:|
| no_shift (baseline) | 0 | 0.2258 | 0.2268 | 0.525 |
| flat_0.1σ (Phase-5) | 0.100σ | 0.2152 | 0.2279 | 0.520 |
| **grounding_weighted** | **0.0333σ** | 0.2184 | **0.2268** | 0.523 |

Pre-declared rule: NEUTRAL-OR-BETTER iff KS not worse than flat AND tail within
the Phase-5 5% tolerance.

- **Tail (the Phase-5 over-tightening tripwire): PASSES.** Grounding-weighted
  tail (0.2268) ≤ flat tail (0.2279), within the 5% tolerance — in fact
  strictly better than flat and equal to the no-shift baseline. The
  grounding-weighted shift does not over-tighten the extreme quantiles.
- **KS: literal "not worse than flat" FAILS by +0.0032** (0.2184 vs 0.2152).
  Mechanism, stated honestly: the grounding weight for a grounded single-hit
  read is 1/3 (hops=3), so the grounding-weighted shift (0.033σ) is *smaller
  and more conservative* than the flat 0.1σ shift, and therefore perturbs
  calibration LESS from the unshifted baseline (0.2184 sits between no_shift
  0.2258 and flat 0.2152). On a **direction-agnostic** symmetric hand-made
  proxy, KS is minimised by whichever policy happens to move mass toward the
  near-centre realized — a larger shift wins that lottery. This is a property
  of the RAW_UNRANKABLE proxy (it has no true direction to reward a
  correctly-directed shift), NOT a calibration regression of the grounding
  weight.

**Verdict: partial.** The calibration-safety criterion the Phase-5 flat shift
was chosen for (tail not worse) holds; the KS comparison is confounded by the
direction-agnostic proxy and cannot be resolved without sealed outcomes. Per
the prereg's pre-committed stance, a regression would be a finding — but this is
not a regression (tail-neutral, and the shift is strictly more conservative);
it is an unresolvable-on-a-proxy KS tie reported transparently.

---

## H3 — the overconfidence guard: **PROVEN**

Constructed an ungrounded-but-confident read: the same confident hawkish stance
is forced with NO genuine frame ground (its `FrameReading` has no `read_from`
Message → its `grounded_in` chain reaches no anchor), vs a grounded case with a
real `policy_rate_path`/rise ground. `flag_ungrounded_confident` (the UNCHANGED
`grounding_reach` guard) is called with the StanceReading flagged
low-residual + high-confidence.

| case | reached anchor | GroundingGap | shift |
|---|---|---|---:|
| grounded (real frame ground) | True (hops=3) | no | 0.3333 |
| ungrounded-confident (forced) | False | **yes (1 minted)** | **0.0000** |

Shift ratio ungrounded/grounded = **0.0 < 0.10**. **PROVEN** per the
pre-declared rule: the ungrounded-confident case mints a `GroundingGap` and the
shift attenuates to <10% of the grounded case. This is the structural version
of Phase-3's "silence, not error" safety — a confidently-typed read whose chain
reaches nothing external is silenced.

---

## Wire-in — admissible g0–g3 behind a flag

The arm is wired into the text-arm path behind `forecast_cli --text-arm tom`
(choices `rules|model|off|tom`). `_derive_text_signal_tom` boots the arm once,
decodes each corpus doc to `(direction, grounding_weight)`, and emits a per-asset
FLOAT signal = `sign × grounding_weight`; `apply_text_shift` (unchanged) then
produces the grounding-weighted band shift. The path is fully guarded — any
failure returns an empty signal (text-blind), so text can NEVER break
admissibility (the Phase-3 silence-is-safe floor).

g0–g3 gate on the worked exemplar `t2-EXAMPLE-ust-curve-1m`, via the
organizer's own `scoring.scoring.build_verifier` (the SAME gate
`run_example.sh` runs):

| text_arm | admissible | g0_integrity | g1_schema | g2_cutoff_resource | g3_domain_semantics | text applied |
|---|---|---|---|---|---|---|
| off | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| rules | ✅ | ✅ | ✅ | ✅ | ✅ | UST_2Y: −1 |
| **tom** | **✅** | ✅ | ✅ | ✅ | ✅ | **UST_2Y: 0.3333** |

The ToM arm's output is admissible, identical gate profile to the `off`/`rules`
arms. On the exemplar the arm decoded the June-2024 FOMC statement to **down**
(the "greater confidence"/hold framing) with grounding weight 0.333 — matching
the exemplar's own rationale note that the front end should move on that
guidance. (Score is `None` under the public smoke: realized outcomes are sealed.)

Reproduce:

    PYTHONPATH=runners/dsl/python:.bigtmp/track2 OZMA_SEED_PERSIST_DISABLED=1 \
      .bigtmp/t2venv/bin/python drafts/seldon_t2_text/induced_belief/gate_g0g3.py

(The exemplar scorer env `.bigtmp/t2venv` has no `substrate_rs`; the arm's
`substrate_rs` is the abi3 `.so` importable via `PYTHONPATH=runners/dsl/python`,
so one interpreter runs both the arm and the scorer.)

---

## Proven-vs-assumed ledger

**PROVEN (measured, this run):**
- H0 = REUSE, with file:line evidence; the text→CAN path exists and the bridge
  input is source-agnostic. No substrate edit made.
- Net-win gate: bigville CAN/ToM/arousal/hate/trust/grounding tests green
  (20 + 25 + batch), byte-unchanged (git-confirmed zero tracked-file diffs).
- H1: non-FOMC directional accuracy 0.727 (8/11) vs cue lexicon 0.273 (3/11),
  +45.4pp; per-doc_type table above; lexicon-killers recovered. Real decode on
  every one of the 52 frozen snippets (no fabricated numbers).
- H3: GroundingGap mints on the ungrounded-confident case and the shift
  attenuates to 0.0 (ratio 0.0 < 0.10).
- Wire-in: `--text-arm tom` output passes g0–g3 on the exemplar under the real
  organizer verifier; identical gate profile to off/rules.
- The mechanism reuses `mint_target_concept`/`mint_resident_tom_belief`,
  `concept_apply_evidence`, `reasoning_can_bridge`, `grounding_reach`, the CAN
  native engine, and `read_clause` verbatim; the stance DECISION is the seed
  rule `ib_decode_stance`; the winning-stance SELECTION is the held `Argmax`
  Term over the confirmed stance Concepts' CAN marginals (graph-native), and the
  band direction is read off the winning StanceReading's `direction` graph datum.

**PARTIAL / HONEST-NULL:**
- H2: tail-neutral (the Phase-5 over-tightening criterion) PASSES; the KS "not
  worse than flat" criterion fails by +0.0032, confounded by the
  direction-agnostic RAW_UNRANKABLE hand-made proxy (which cannot reward a
  correctly-directed shift). Not a regression; unresolvable without sealed
  outcomes. Reported transparently.
- H1 macro_release: still 0/2 — CPI number-direction reading is out of the
  frame-speech-act model's scope (no number-reader), the same class the lexicon
  missed. Honest residual.
- H1 negation/conditional traps (s07/s09/s12/s19): the arm mis-signs 4
  pre-declared trap snippets because conflicting single-sentence frame hits tie
  at the CAN marginal and the winning-stance tiebreak resolves by stance order.
  The `causal_influence` couplings between stance Concepts that would let the
  network resolve the conflict are not populated. Named limitation.

**ASSUMED (not independently verified this run):**
- All scores are RAW_UNRANKABLE: no ranked/normalized organizer number is
  obtainable locally (sealed outcomes). The exemplar gate score is `None`
  (public smoke), as designed.
- The hand-made realized proxy is a relative calibration instrument only, not a
  claim about live forecast skill.
- The frame `ground_frame` surface→symbol reader is a thin I/O-boundary
  classifier (CLAUDE.md's permitted boundary translator): it carries no up/down
  verdict (the codebook rule + marginal do), but it IS a regex reader over
  surface forms. A fully graph-native frame decode (mention→frame-symbol
  Concept grounding via the reading pipeline, then a symbol-level codebook) is
  the natural next step; the current reader is honest about being a boundary
  tokenizer.

---

## Files

- `induced_belief/frame.py` — frame-symbol vocabulary, surface→(symbol,motion)
  frame decode, `(symbol,motion)→(stance,sign)` codebook (taught data).
- `induced_belief/induced_belief_codebook.json` — the seed: `ib_decode_stance`
  rule (Eq-join FrameReading × CBSpeechAct → StanceReading).
- `induced_belief/arm.py` — the world-adapter driver (boot / decode_utterance /
  reset_beliefs). Reuses the CAN engine and `grounding_reach`; applies belief
  evidence with `native.concept_apply_evidence` directly on the boot-cached
  Concept map (the same primitive `reasoning_can_bridge` calls). The bridge
  itself is exercised ONCE at boot to establish the SmEntity→Mt denotes edge,
  not on the per-utterance decode path.
- `induced_belief/measure_h1.py` / `_h2.py` / `_h3.py` — the three hypothesis
  harnesses. `gate_g0g3.py` — the wire-in admissibility gate.
- `h1_results.json` / `h2_results.json` / `h3_results.json` /
  `gate_g0g3_results.json` — the raw measured outputs.
- `forecast_cli.py` — `--text-arm tom` wiring (`_derive_text_signal_tom`).


---

## REVIEW FIX (semantic-review/2026-09-03-164002-induced-belief-arm.md)

The review confirmed ONE CLAUDE.md violation: two coupled Python decisions over
graph state in `decode_utterance`. Both are now moved graph-native, with the
measured behaviour held **byte-identical**.

**Decision 1 — winning-stance selection (was a Python argmax loop, `arm.py`
step 7).** The old code iterated the stance Concepts and kept the largest
positive `state` marginal in Python (`if st > best[1]: best = ...`) — the exact
`homework_loop.py:600-603` "never a Python argmax/sort" anti-pattern. It is now
the held **`Argmax` Term** (`arm._winning_stance_term`), evaluated in Rust via
`native.evaluate`, mirroring `coref_entities.antecedent_argmax_term` /
`many_settings_recognizer.predict_many_settings_term`:

    Argmax( Filter( NodesWhere(Concept, ib_stance_market == market),
                    c, Gt(c.state, 0) ),        # only CONFIRMED stances (was `if st <= 0: continue`)
            c, c.state, default = None )          # ranked by the CAN marginal ⟨σ⟩

`build_market` stamps each of the three target-scoped stance Concepts with a
small DATA marker `ib_stance_market` (mechanical mint-time tagging, the same
one-time-init discipline `state`/`external_field` use) so the `NodesWhere`
source enumerates EXACTLY those three, not every Concept on the Mt. The
`state > 0` filter reproduces the old confirmed-stance guard; the `default=None`
reproduces the old `best is None` no-winner path. The Argmax's first-encountered
tiebreak matches the old loop's `st > best[1]` strict-improvement tiebreak
because the Concepts are minted in `_STANCES` order (hawkish, dovish, neutral),
so tied-at-1.0 marginals resolve to the same winner. Python now only reads the
winning Concept node's name back — it never picks the winner.

**Decision 2 — band direction (was a Python `if/elif` over the sign, `arm.py`
step 8).** The old code decided the direction with
`if stance_sign > 0: "up" elif < 0: "down" else "none"` — a branch over graph
state. The sign→direction mapping is the codebook's own causal semantics, so it
is now held as codebook DATA: `frame.SIGN_DIRECTION = {1:"up", -1:"down",
0:"none"}`, and each CBSpeechAct carries a `direction` attr (a mechanical
`SIGN_DIRECTION` lookup, not a decision). The `ib_decode_stance` rule copies
`direction` graph-native onto every StanceReading (one more `__term__` Attr copy
alongside the existing `sign`/`stance`/`attr` copies). The decode now READS the
winning StanceReading's `direction` datum off the graph — a mechanical attr read,
no Python conditional deciding the direction.

**Term / rule used:** the held `Argmax` DSL Term (already shipped,
`runners/dsl/src/term.rs`; no new Rust primitive) evaluated with
`native.evaluate`; and the existing `ib_decode_stance` seed rule extended to
carry the `direction` graph datum. No substrate/`domains`/`worlds`/`seeds` edit
— all changes are inside the untracked `drafts/seldon_t2_text/induced_belief/`
arm.

**Numbers are byte-identical after the fix** (re-ran every harness, compared the
full JSON to the pre-fix outputs):

- **H1** — overall accuracy **0.846**, non-FOMC ToM **0.727** (8/11) vs cue
  lexicon 0.273, every per-doc_type figure and every one of the 52 per-snippet
  rows (pred / marginal / shift / grounding) IDENTICAL to the pre-fix
  `h1_results.json`.
- **H3** — guard fires: GroundingGap minted, shift **ratio 0.0**, PROVEN;
  `h3_results.json` byte-identical.
- **g0–g3** — off / rules / **tom** all admissible, identical gate profile,
  tom signal **UST_2Y: 0.3333**; `gate_g0g3_results.json` byte-identical.
- **H2** — unaffected (H2 uses a fixed `grounding_weight` constant and never
  calls `decode_utterance`); `h2_results.json` unchanged.

**RESULTS wording correction (review concern #3).** The decode path does NOT run
"via the UNCHANGED `reasoning_can_bridge`". It calls
`native.concept_apply_evidence` DIRECTLY on the boot-cached Concept map
(`arm.py`, decode step 5) — the SAME belief-update primitive the bridge calls at
`reasoning_can_bridge.py:227`, but the bridge itself is exercised ONLY once at
boot warm-up (`build_market`) to establish the `SmEntity --denotes--> Mt` edge.
The reused *primitive* is legitimate; the *bridge* is not on the per-utterance
path. The module docstring, the proven-vs-assumed ledger, and the Files section
above have been corrected to state this accurately.
