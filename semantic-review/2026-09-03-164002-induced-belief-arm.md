# Induced-belief text-arm: prereg + CLAUDE.md adherence review

The decode-through-ToM text arm (`drafts/seldon_t2_text/induced_belief/`) types a central-bank utterance by decoding it against a forecast-frame codebook, applying the decoded stance as evidence to a target-scoped CAN belief, and reading the CAN marginal + transitive grounding back as a signed, confidence-weighted band shift. Built strictly as REUSE of the existing substrate (`mint_target_concept`, `concept_apply_evidence`, `reasoning_can_bridge`, `grounding_reach`, the reading/CAN engines). This review verifies the five specific claims the task named: no new parallel ToM mechanism, the H0 seam verdict backed by real evidence, no Python decision over graph state, honest/non-fabricated numbers, and g0-g3 pass. I re-ran H1, H3, the g0-g3 gate, and the bigville CAN/ToM test suite independently.

Watch for:
- **(confirmed)** The stance-selection readout in `arm.py:356-369` is a Python `argmax` over Concept `state` graph values, and direction in `arm.py:389-393` is a Python `if/elif` over the winning stance's sign. This is the house's flagged pattern (`homework_loop.py:600-603` explicitly says "never a Python argmax/sort"; readouts should be a held `Argmax` Term). It decides which stance wins and which way the band moves — a decision over graph state living in Python, not a rule or a held Term.
- **(confirmed, mitigating)** The per-utterance path does NOT call `reasoning_can_bridge.apply_derived_fact_as_can_evidence`; it calls `native.concept_apply_evidence` directly on a boot-cached Concept map (`arm.py:326`). Same primitive, but the "reuse the bridge" claim holds only for a one-time boot warm-up (`arm.py:186-187`), not the measured decode path. The prereg's REUSE target is the primitive, and the primitive is reused — but the bridge itself is bypassed at decode time.
- **(confirmed, expected)** H2 is a reported NULL/PARTIAL: KS "not worse than flat" fails by +0.0032 (`h2_results.json`). Correctly surfaced as a finding, not hidden. RAW_UNRANKABLE stated.

Everything else holds: no new belief node type, H0 file:line evidence is real and the substrate is byte-unchanged (git-confirmed), H1/H3/gate numbers reproduce exactly, and all g0-g3 gates pass under the organizer's own scorer.

**Verdict**: NEEDS_CHANGES

## High-level view

The arm is genuinely REUSE at the representation level. The stance belief is a `<stance>_stance_for:rates_market` Concept minted through `shared_arousal.mint_target_concept` / `bigville_theory_of_mind.mint_resident_tom_belief` — the identical `<aspect>_for:<target>` CAN pattern hate/trust/arousal already use. No bespoke ToM or belief node type was authored. Concern #1 is clean.

The H0 REUSE verdict is backed by real, verifiable file:line evidence: `read_clause` at `reading_collapse.py:1600`, the `(entity, attr)` extraction at `solver_dispatch.py:295-320`, and the source-agnostic bridge `apply_derived_fact_as_can_evidence(agent, entity: str, attr: str, ...)` at `reasoning_can_bridge.py:188` calling `concept_apply_evidence` at :234. Because the verdict is REUSE, the net-win gate is satisfied vacuously: `git status` shows zero edits under `domains/worlds/runners/seeds/substrate` and the entire arm is untracked under `drafts/`. The 57 bigville CAN/ToM/arousal/hate/trust/grounding tests I re-ran are green — trivially so, since nothing they cover was touched. This is the correct outcome for a REUSE verdict, not evidence of a generalization done right (there was no generalization).

The one real CLAUDE.md violation is the decision boundary. The *stance-typing* decision is correctly a graph rule (`ib_decode_stance`, an Eq-join in `induced_belief_codebook.json`). But two downstream decisions — which stance wins the marginal, and which direction that implies — are executed by Python `argmax`/`if` over graph state in `decode_utterance`, not by a rule or a held Term. The house has an explicit idiom for exactly this (held `Argmax`), and this arm does not use it.

The numbers are measured and honest. H1 reproduces at 0.846 overall / non-FOMC 0.727 vs cue-lexicon 0.273 against the frozen 52-snippet `study_set.json` gold labels, using the frozen Phase-3 metric functions. H3 reproduces (guard fires, shift ratio 0.0). H2 is a declared partial null. No ranked/normalized score is claimed anywhere — the gate reports `score: None` because realized outcomes are sealed, and the tom signal (0.3333) is a shift magnitude. All three arms (off/rules/tom) pass g0-g3 under the organizer's `build_verifier`.

<details>
<summary>Issues (4)</summary>

1. **Python argmax over graph state** — `arm.py:356-369` selects the winning stance by iterating Concepts and keeping the largest `state` in Python. Per CLAUDE.md and the `homework_loop.py:600-603` precedent this readout should be a held `Argmax` Term over the marginal, not a Python loop. Decides which belief wins.
2. **Python if/else deciding direction** — `arm.py:389-393` maps the winning stance's sign to up/down/none via `if stance_sign > 0 / elif < 0`. Direction is a decision over graph state; it belongs in a rule or a held sign Term (the sign already lives on the CBSpeechAct/StanceReading as graph data, so the branch is avoidable).
3. **Bridge bypassed at decode time** — the measured path calls `native.concept_apply_evidence` directly (`arm.py:326`) rather than `reasoning_can_bridge.apply_derived_fact_as_can_evidence`; the bridge is exercised only in a one-time boot warm-up (`arm.py:186-187`). The reused *primitive* is legitimate, but the RESULTS wording ("via the UNCHANGED reasoning_can_bridge") overstates the decode path. Align the claim with the code or route the decode through the bridge.
4. **H2 KS regression (reported)** — `h2_results.json` `NEUTRAL_OR_BETTER: false`, KS worse than flat by +0.0032. Already surfaced honestly as a finding; no action beyond keeping it labeled a null, not a pass.

</details>

<details>
<summary>Details</summary>

### Concern #1 — no new parallel ToM/belief mechanism (HOLDS)

The stance belief is `<stance>_stance_for:rates_market`, minted in `build_market` (`arm.py`) through `tom.mint_resident_tom_belief(native, mt, "%s_stance" % stance, market)`, which is `bigville_theory_of_mind.mint_resident_tom_belief` → `shared_arousal.mint_target_concept` — the same call `hate_attribution.py:84-88` uses for `regard_for` / `removal_desire_for` / `pity_for`. The `_attr()` helper in `frame.py` reconstructs exactly the `<aspect>_for:<target>` name the convention produces. The market is a bigville `Resident` built via `worlds.bigville_can_beliefs.build_resident_can_mt`. There is no new node type standing in for a belief: `FrameReading`, `CBSpeechAct`, and `StanceReading` are decode-intermediate nodes (frame token, codebook entry, decoded verdict), not a competing belief representation — the belief itself is the reused CAN Concept, graded by the CAN marginal. This is the CAN `<aspect>_for:<target>` pattern, reused. No flag.

### Concern #2 — H0 seam verdict is real, not asserted (HOLDS; REUSE)

The verdict is REUSE, and the chain is traceable:

```
read_clause (reading_collapse.py:1600)  ->  predications [[rel,arg0,arg1],...]
   -> _extract_property_fact (solver_dispatch.py:295-320) -> (entity, attr) as bare strings
      -> apply_derived_fact_as_can_evidence(agent, entity:str, attr:str, ...)   (reasoning_can_bridge.py:188)
           resolves SmEntity --denotes--> Mt --has_concept--> Concept(name==attr)  [UNCHANGED correspondence rules]
           -> native.concept_apply_evidence(concept, evidence, alpha)             (reasoning_can_bridge.py:234)
```

The bridge signature takes two plain strings — it is already source-agnostic, so there was no deduction/scenario coupling to break. Because the verdict is REUSE, the net-win gate reduces to "the substrate is untouched." I confirmed both halves:

- `git status --short domains/ worlds/ runners/ seeds/ substrate/` returns empty; the whole arm is `?? drafts/seldon_t2_text/induced_belief/`.
- Re-ran `test_bigville_theory_of_mind`, `test_can_native_reimplementation`, `test_shared_arousal_excitation_transfer`, `test_hate_attribution`, `test_resident_trust`, `test_grounding_reach`, `test_grounding_theory`: **57 passed**.

This green is the *baseline* — it proves nothing was broken, which is what a REUSE (no-edit) verdict should show. It is not evidence that a generalization was done correctly, because no generalization was made. The prereg's GENERALIZE branch (and its "make `reasoning_can_bridge`'s INPUT source-agnostic" requirement) is moot here; the input was already source-agnostic. There is no dedicated `reasoning_can_bridge` test file in `tests/`, but the bridge is unmodified so that is not a gap introduced by this arm.

### Concern #3 — Python decision over graph state (VIOLATION)

The *stance-typing* decision is correctly graph-native: `ib_decode_stance` in `induced_belief_codebook.json` is an Eq-join (`FrameReading.symbol == CBSpeechAct.symbol AND FrameReading.motion == CBSpeechAct.motion`), guarded by `Not(Exists decoded_to)`, minting a `StanceReading` with the codebook entry's stance/sign/attr. Python only mints the `FrameReading` nodes and ticks. Good.

But `decode_utterance` then makes two decisions in Python over graph state:

Step 7 — winning-stance selection (`arm.py:356-369`):
```python
best = None
for stance in _STANCES:
    ...
    st = float(sub.node(c)["attrs"].get("state"))
    if st <= 0: continue
    if best is None or st > best[1]:
        best = (stance, st, c)
```
This is a Python argmax over the Concept `state` marginals — a decision (which belief wins) read out of graph state by a Python loop. The house convention (`homework_loop.py:600-603`) is explicit that a winner-selection readout must be a held `Argmax` Term, "never a Python argmax/sort." The prereg itself says the winning signal "IS the CAN marginal" — but *selecting* the max marginal across three Concepts is still a decision, and it is done in Python.

Step 8 — direction (`arm.py:389-393`):
```python
if stance_sign > 0:   direction = "up"
elif stance_sign < 0: direction = "down"
else:                 direction = "none"
```
An `if/elif` over graph state (`StanceReading.sign`) that decides the band direction — the exact "if/else that reads graph state and decides what to do next" CLAUDE.md names as a Rule, not Python. The sign is already graph data on the CBSpeechAct/StanceReading, so a held sign Term or a rule that stamps a `direction` attr would keep the decision in the graph.

Steps 10-11 (grounding weight, base-shift dict lookup, shift multiply) are arithmetic marshalling of already-decided values and are legitimate adapter work. The violation is specifically the argmax (7) and the direction branch (8). The `forecast_cli._derive_text_signal_tom` sign→float mapping is a second copy of the same direction branch, but it consumes the arm's already-decided `direction` string, so it is downstream marshalling of the same underlying decision rather than a separate one.

This is a real, localized CLAUDE.md violation, not a whole-arm indictment: the *typing* decision is graph-native, and the fix is bounded (a held `Argmax` over the stance Concepts' marginals + a rule/Term that stamps direction from the winning StanceReading's sign).

### Concern #4 — numbers measured, nulls reported, no fabricated score (HOLDS)

I re-ran the harnesses:

- **H1** (`measure_h1.py`): overall 0.846; non-FOMC ToM 8/11 = 0.727 vs cue lexicon 3/11 = 0.273; by doc_type fomc 0.878, cb_speech 0.857, corporate_8k 1.0, positioning_report 1.0, macro_release 0.0. Reproduced byte-for-byte against `h1_results.json`. Gold labels come from the frozen `phase3_derisk/study_set.json` (52 snippets, `gold` field), and the lexicon comparison is read from the frozen `phase3_derisk/results.json`, using the Phase-3 `measure.py` metric functions verbatim. `macro_release` 0.0 is reported as an honest residual (CPI number-reading is out of frame scope), not smoothed.
- **H3** (`measure_h3.py`): grounded shift 0.3333 / ungrounded-confident shift 0.0, GroundingGap minted (1 node), ratio 0.0 < 0.10 → PROVEN. Reproduced exactly.
- **H2** (`h2_results.json`): grounding-weighted vs flat — tail criterion passes (0.2268 ≤ 0.2279), KS fails by +0.0032, `NEUTRAL_OR_BETTER: false`, `RAW_UNRANKABLE: true`. Uses the real `qfbench2_common.scoring.crps` plus the Phase-2 hand-made realized proxy. Reported as a partial null, correctly.

No ranked or normalized score is asserted anywhere. The gate reports `score: None` (realized sealed); the tom `text_signal` 0.3333 is a shift magnitude (sign × grounding_weight), not a score.

### Concern #5 — g0-g3 on the wired arm (HOLDS)

Re-ran `gate_g0g3.py` under t2venv (`PYTHONPATH=runners/dsl/python:.bigtmp/track2`) against the exemplar `t2-EXAMPLE-ust-curve-1m` using the organizer's own `scoring.scoring.build_verifier`. All three arms `admissible=True` with `g0_integrity/g1_schema/g2_cutoff_resource/g3_domain_semantics` all True. The tom arm applied text (`UST_2Y: 0.3333`), decoding the June-2024 FOMC statement to `down` with grounding_weight 0.3333. The wire-in is fully guarded: every failure path in `_derive_text_signal_tom` returns an empty (text-blind) signal, so the arm cannot break admissibility — the Phase-3 "silence is safe" floor.

</details>

<details>
<summary>File map</summary>

- `induced_belief/frame.py` — forecast-frame symbol vocabulary + surface→(symbol,motion) reader + the (symbol,motion)→(stance,sign) codebook as taught data. Thin I/O-boundary classifier; carries no up/down verdict.
- `induced_belief/arm.py` — the decode driver (world adapter). Reuses mint_target_concept / concept_apply_evidence / grounding_reach. **Contains the Python argmax (step 7, :356-369) and direction branch (step 8, :389-393) flagged under concern #3.**
- `induced_belief/induced_belief_codebook.json` — the `ib_decode_stance` seed rule (Eq-join) + sentinel Concept. The stance-typing decision, graph-native.
- `induced_belief/measure_h1.py` / `measure_h2.py` / `measure_h3.py` — the three hypothesis harnesses; reuse frozen Phase-3 metrics and the real crps scorer.
- `induced_belief/gate_g0g3.py` — wire-in verification via the organizer's build_verifier.
- `induced_belief/*_results.json` — measured outputs (all reproduced in this review).
- `forecast_cli.py` — `--text-arm tom` wire-in (`_derive_text_signal_tom`), fully guarded.
- `INDUCED_BELIEF_RESULTS.md` — deliverable write-up (H0 REUSE evidence, H1 table, H2 before/after, H3 guard, proven-vs-assumed ledger).

Full diff: n/a — the arm is untracked under `drafts/`; `git status` confirms zero edits to `domains/worlds/runners/seeds/substrate`.

</details>
