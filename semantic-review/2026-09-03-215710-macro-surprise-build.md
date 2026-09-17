# Macro-release numeric-surprise mechanism — prereg + CLAUDE.md audit

The build closes the H1 `macro_release` 0.0 residual by treating a CPI/NFP print as a NUMBER whose forecast relevance is its SURPRISE vs an expectation, rather than a speech act. The surprise sign is read mechanically (released-vs-prior text, panel trend, or a taught cue lexicon), a `MacroSurpriseReading` carrying only `(series, surprise_sign, market)` is minted, and a seed rule Eq-joins that against a taught `MacroSurpriseSign` codebook to mint the SAME `StanceReading` the ToM arm mints — feeding `concept_apply_evidence` on the SAME `<stance>_stance_for:<market>` CAN Concept. I re-ran H-M1, H-M2 (`measure_h1` diff), the g0–g3 gate, and the H-M3 sweep; all reproduce the numbers in `MACRO_SURPRISE_RESULTS.md`.

Watch for: nothing blocking. Two informational notes — the H-M3 harness leaves its own `direction_only_monotone_in_p_and_e` summary flag as `null` (unset, not false; I confirmed monotonicity by hand from the reproduced grid) (confirmed); and H-M1's 1.0 is an honest but narrow directional-recovery result on n=17 CPI-dominated single-annotator labels, already flagged RAW_UNRANKABLE in the doc (confirmed).

**Verdict**: APPROVED

## High-level view

No fork. The macro path mints exactly two node kinds — a taught `MacroSurpriseSign` codebook node and a bare `MacroSurpriseReading` — and reuses the ToM arm's stance Concepts, `concept_apply_evidence`, the `_winning_stance_term` Argmax readout, and `grounding_reach` verbatim. There is no new Concept, no second CAN engine, no parallel belief.

No Python decision over direction. Which sign of a surprise is hawkish is codebook DATA (`MACRO_SURPRISE_SIGN`, keyed on series), expanded at teach time into `(stance, band_sign, direction, attr)` triples; the decision — which stance a `(series, surprise_sign)` is — is the seed rule `ib_decode_macro_surprise`, an Eq-join that pulls the triple off the codebook node. The Python only computes a bare surprise sign by arithmetic on parsed numbers (above/below/inline the expectation), which is I/O, and dispatches on `doc_type` at the CLI boundary, which is routing.

Non-regression holds. `measure_h1` re-runs byte-identical to the committed `h1_results.json`; the per-doc_type ToM numbers (fomc 36/41, cb_speech 6/7, corporate_8k 1/1, positioning_report 1/1) are unchanged, and the macro path fires only on `macro_release` docs in the wired CLI.

H-M1 confirmed and honest: 17/17 = 1.0 against a sha256-frozen hand-labeled set (checksum verifies OK), gold distribution up=6/down=9/none=2 (not 50/50), tom baseline 0.0. H-M3 is literal-confirmed but the doc correctly reports it as shift-artifact confounded — the raw −0.28 win is direction-independent, the genuine direction effect is the −0.0088 residual — and every H-M3 number is stated RAW_UNRANKABLE.

<details>
<summary>Issues (2)</summary>

1. **H-M3 monotone flag unset** — `measure_hm3.py` emits `direction_only_monotone_in_p_and_e: null`; the results prose claims monotonicity in both p and e. The claim is TRUE (I verified from the reproduced grid), but the harness's own flag doesn't compute it. Non-blocking; either wire the flag or note it's hand-verified.
2. **H-M1 breadth caveat (informational)** — 1.0 on n=17, single annotator, CPI-dominated, panel-trend path under-exercised (7 prior-null snippets fell to `released_sign`, not the panel path). Already disclosed in the doc; no action required, listed for completeness.

</details>

<details>
<summary>Details</summary>

### 1 — No parallel belief mechanism (verified)

`macro_surprise.py` mints only two node types: `MacroSurpriseSign` (a taught codebook DATA node, `add_node` at line 445) and `MacroSurpriseReading` (line 504), which carries only `series`, `surprise_sign`, `market`, `surprise_motion`. There is no `mint_target_concept`, no `create_concept`, no new CAN construction anywhere in the module (grep for `add_node\(|mint_target|new_can|create_concept` returns only those two mints). The `StanceReading` is produced by the seed rule, the same type `ib_decode_stance` produces. Belief update at `macro_surprise.py:534` is `native.concept_apply_evidence(concept, 1.0, alpha)` where `concept = mk["concepts"].get(s_attr)` — the ToM arm's already-booted stance Concepts handed in via `mk`, not a fresh belief. `_winning_stance_term` Argmax and `gr.grounding_reach` are called through `_arm` (lines 486, 550). No fork; strict reuse per the prereg's REUSE clause. (confirmed)

### 2 — No Python decision over direction (verified)

The prereg's line is: number parsing from text/panel is mechanical I/O and fine; a branch DECIDING hawkish/dovish is not. The build holds this line:

- The only `hawkish`/`dovish` string literals in the module are in comments and the `_SIGN_STANCE` / `MACRO_SURPRISE_SIGN` data tables (`macro_surprise.py:59–63, 89–96, 106`). No `if`/`elif` reads a series and returns a stance.
- The branches in `read_surprise` (`macro_surprise.py:322–380`) compute a *bare surprise sign* by arithmetic: `diff = released - prior; sign = 1 if diff > 1e-9 else (-1 if diff < -1e-9 else 0)`. This is above/below/inline the expectation — an I/O arithmetic result, not a direction verdict.
- The hawkish mapping (`band_sign = surprise_sign * hawkish_sign`) is done in `macro_codebook_entries()` (`macro_surprise.py:118–139`) at teach time as data expansion, and `direction`/`stance` are table lookups (`frame.SIGN_DIRECTION`, `_SIGN_STANCE`) baked onto the codebook node.
- The DECISION lives in `macro_surprise_codebook.json`'s `ib_decode_macro_surprise` rule: an Eq-join on BOTH `series` and `surprise_sign` that pulls `stance`/`band_sign`/`direction`/`attr` OFF the joined `MacroSurpriseSign` node (the rule's `effects` read `Attr(ms, ...)`, never `Attr(mr, ...)` for the stance fields). Python computes no stance/direction.
- At the CLI, `forecast_cli.py:275` dispatches `is_macro = (d.get("doc_type") in _MACRO_DOC_TYPES)` — a `doc_type` routing decision at the I/O boundary (permitted adapter classification), not a decision over graph state. The final `sgn = {"up": +1.0, "down": -1.0, "none": 0.0}.get(direction, 0.0)` (line 297) is a mechanical relabel of a direction *read off the graph* (`r["direction"]`), identical in kind to the ToM arm's own relabel.

No violation found. (confirmed)

### 3 — H-M2 non-regression (reproduced)

`measure_h1.py` re-run diffs byte-identical (raw and json-normalized) against the committed `h1_results.json`. The ToM arm's per-doc_type table is unchanged:

```
fomc_statement       36/41  0.878
cb_speech             6/7   0.857
corporate_8k          1/1   1.0
positioning_report    1/1   1.0
macro_release         0/2   0.0   (ToM baseline; the residual this build targets)
```

The g0–g3 gate (`gate_macro.py`, re-run) shows the macro path firing exclusively on `[macro_release]` docs (`path=macro_surprise` in the per-doc debug) and the ToM path on everything else. One scoping nuance worth stating: `measure_h1.py` does not itself install the macro seed, so its byte-identity proves the ToM *decode code* is untouched; the stronger assertion — that with the macro path installed and active, non-macro reads still route through the untouched ToM decode — rests on the CLI `is_macro` gate plus the exemplar gate, both of which I reproduced (the exemplar still emits `UST_2Y: 0.3333` / the F2 unit `UST_10Y: 0.3333` with the macro mechanism booted). The macro path fires only on macro reads, as required. (confirmed)

### 4 — H-M1 frozen labels + accuracy (reproduced)

`sha256sum -c macro_study_set.sha256` returns `OK` — the hand-labeled set is unchanged since freezing. The file's `_meta` declares `committed_before_measure: true` with a rubric anchored on the released-vs-prior number direction (not policy verbs), and gold distribution up=6/down=9/none=2, so the >0.5 bar is a genuine threshold rather than a coin flip. `measure_hm1.py` reproduces:

```
macro_surprise_acc   1.0   (17/17)
tom_baseline_acc     0.0
directional_only     15/15 = 1.0
H_M1_confirmed       true
by_source: quantitative_text 10/10, released_sign 6/6, none 1/1
```

The 1.0 is above 0.5 and against the 0.0 ToM baseline — H-M1 CONFIRMED. The doc does not oversell it: it flags the small n, single annotator, CPI-dominance, and that the panel-trend path was under-exercised (7 prior-null snippets fell to the `released_sign` fallback because their units ship no `macro_monthly`). Labels were frozen before measurement, not fitted. (confirmed)

### 5 — RAW_UNRANKABLE discipline + honest nulls (verified)

Every H-M3 number is stated RAW_UNRANKABLE: the proxy's gold direction IS the macro decode's own direction (sympathetic by construction), and sealed organizer outcomes are unavailable (gate scores are `None` under the public smoke, which I reproduced). The proven-vs-assumed ledger separates PROVEN (H-M1 accuracy, H-M2 byte-identity, gate admissibility) from ASSUMED (all H-M3 as proxy, H-M1 as directional-recovery not live skill). No sealed score is claimed anywhere. Nulls are reported as headline: H-M1 near-chance would have been a null (it wasn't), and H-M3 is honestly downgraded to the pre-committed partial branch rather than dressed as a clean win. (confirmed)

### 6 — H-M3 confound, reproduced and correctly characterized

The sweep reproduces the doc's table exactly: `no_shift` composite 14.71464, `macro_shift` 14.43595, Δ −0.27869 at p=0; literal criterion passes 6/6 signalled cells. The summary reproduces `shift_artifact_confound: true`, `empty_signal_abs_delta_composite: 0.27869`, `mean_direction_only_gain: -0.008825`. Stripping the artifact, the direction-attributable residuals I recomputed from the grid match the doc's table to 5 decimals:

```
p_signal  e=0.5      e=1.0
0.3      -0.00277   -0.00365
0.5      -0.00931   -0.01345
0.7      -0.00972   -0.01405
```

All negative, monotone-decreasing in p_signal for both e, and more negative at e=1.0 — supporting the doc's "small but genuine, monotone in both p and e" reading. The empty-signal delta (−0.28) equalling the signalled delta (−0.29) is the honest confound: the raw win is a direction-independent shift-center artifact on large-level single-asset macro units, exactly as the doc states. The only gap is cosmetic: the harness leaves its own `direction_only_monotone_in_p_and_e` flag `null` rather than computing it, so the monotonicity claim is hand-verified, not machine-asserted. (confirmed)

### Net-win / no-tracked-files (verified)

`git status --short drafts/seldon_t2_text/induced_belief/` reports the whole directory as untracked (`??`) — no substrate/domains/worlds/seeds edit, consistent with the reuse-not-fork discipline and the net-win gate. (confirmed)

</details>

<details>
<summary>File map</summary>

- `induced_belief/macro_surprise.py` — the surprise read (quantitative text/panel + qualitative lexicon), the `MacroSurpriseSign` codebook (taught DATA), `decode_macro_surprise` (reuses ToM helpers). Mints only `MacroSurpriseSign` + `MacroSurpriseReading`.
- `induced_belief/macro_surprise_codebook.json` — the seed rule `ib_decode_macro_surprise` (Eq-join on `(series, surprise_sign)` → `StanceReading`; DECISION lives here).
- `induced_belief/macro_study_set.json` (+ `.sha256`) — frozen 17-print hand-labeled set; checksum verifies OK.
- `induced_belief/measure_hm1.py` / `measure_hm3.py` / `gate_macro.py` — the harnesses (all re-run, numbers reproduced).
- `forecast_cli.py:211–305` — `_derive_text_signal_tom` composes the macro path behind `--text-arm tom`, gated by `doc_type ∈ {macro_release}` at line 275.
- `MACRO_SURPRISE_RESULTS.md` — the results doc under review; verdicts H-M1 CONFIRMED / H-M2 CONFIRMED / H-M3 literal-confirmed-but-confounded all supported by reproduced numbers.

Reproduce: the three commands in `MACRO_SURPRISE_RESULTS.md` under "Reproduce" (measure_hm1, measure_hm3 with the stated sweep, gate_macro), plus `measure_h1.py` diffed against `h1_results.json`.

</details>
