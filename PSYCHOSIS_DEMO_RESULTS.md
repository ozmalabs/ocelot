# Psychosis as a grounding failure mode — RESULTS

*Glass-box demonstration on the (G,Γ) substrate. Prereg: `PSYCHOSIS_DEMO_PREREG.md`
(committed before these numbers). Harness: `scripts/psychosis_grounding_demo.py`
(real engine). Seed: `seeds/psychosis_grounding.json` (default-off DSL rule).
Figure: `results/psychosis_demo/psychosis_demo.png`. Raw: `results/psychosis_demo/results.json`.
Gate: `tests/test_psychosis_grounding_migrated.py` (8/8). NO new Rust.*

## Verdict (blunt)

**The engine's existing grounding/collapse machinery, run in a failure regime,
reproduces BOTH native psychosis forms — self-grounding and non-optimal-basin —
and the "AI psychosis" confirmer mechanism, as failure modes, with a matched
control and no new mechanism.** Every prediction registered in the prereg held,
cleanly and monotonically. This is a **mechanism / plausibility** result of the
same class as the seizure model's first landing (a reduced glass-box in the real
engine, with an honestly-named authored ingredient) — NOT a validated clinical
claim, and NOT a claim that "the live agent went psychotic."

## What ran (no new mechanism)

Grounding is a predictive-coding pull: a `belief` scalar is corrected toward an
observation, weighted by how strongly the observation constrains it, and
**precision-gated** by confidence (a confident prior down-weights contradictory
evidence — aberrant precision). Collapse is nearest-basin selection. All of it is
one DSL rule + two guarded collapse rules built from existing arithmetic Terms
(`Plus/Minus/Times/Div/Abs/Max/Min/Neg` + `Eq/Gt/Not/And`), evaluated by the real
engine (`run_rules` fixpoint + native `fold_clock_edge`). The Python harness is a
world adapter: it sets two external channels each tick — `(obs, w_ext)` = reality
/ grounding-source, `(obs2, w_conf)` = confirmer — ticks the engine, and reads
`(belief, conf, committed_center)` back. Two basins: `R = 0` (= truth) and
`W = 4` (the delusion). The belief starts poorly grounded in `W` (`b0 = 3.6`,
`conf0 = 0.3`). Frozen params in `Params` (`kx=0.5, ks=0.18, gc=0.15, ge=0.9,
dc=0.3, tol=0.7, cmax=5.0`).

## Results, prediction by prediction

| # | Prediction | Result | Numbers |
|---|---|---|---|
| **P1** | reality friction → **corrects** | ✅ | belief → 0.0, committed **R**, dist-to-truth 0.0 |
| **P2** | no friction → **self-grounds** | ✅ | belief → 4.0, committed **W**, persistence 1.0 |
| **P4a** | fold in reality friction, emergent | ✅ (monotone) | `w_ext` fold: `0.0:W  0.1:R … 2.0:R` (threshold `w_ext*` ∈ (0, 0.1], single boundary) |
| **P4b** | fold in **confirmer** strength (THE FLIP) | ✅ (monotone) | `w_conf` fold: `0.0:R  0.2:R  0.4:R  **0.5:W**  0.6:W … 1.5:W` (threshold `w_conf*` ∈ (0.4, 0.5]) |
| **P5** | confirmer **amplifies** confidence | ✅ | conf@tick15: no-friction **1.37** vs sycophant **5.00** (cmax) |
| **P6** | grounding source **recovers**, faster when stronger | ✅ (monotone) | escape ticks vs `w_ext`: `0.2:46 0.3:26 0.4:18 0.6:12 0.8:9 1.0:7 1.5:5 2.0:4 3.0:2` |
| **P7** | **byte-identity** when off | ✅ | off-state == seed-absent state; `pg_enabled=1` evolves (capability live but inert by default) |
| **P8** | folie à deux (N=2 closed loop) | ✅ | mutual confirmation, no anchor → both **W**; ground one → **both collapse to R** |

### The headline — the "AI psychosis" mechanism (P4b, matched control)

The sharpest result is the matched pair with **identical** weak reality friction
(`obs=truth`, `w_ext=0.4`), differing **only** in whether a sycophantic confirmer
is present:

- reality friction **alone** → belief corrects to truth (**R**, belief 0.0);
- **same** reality friction **+ sycophant** (`obs2=belief`, `w_conf=1.0`) → belief
  **persists in the delusion** (**W**, belief 3.86, persistence 1.0).

The confirmer supplies **no true information** (it mirrors the belief, so it moves
the belief by 0) yet it **flips the outcome**, because it pins confidence at
`cmax` (false external validation), and high confidence attenuates the reality
pull through the `1/(1+conf)` precision gate. This is exactly the mechanism the
psychosis thread names: *"an AI that CONFIRMS removes the friction AND supplies
false external validation — a non-optimal basin wearing the costume of an
external anchor."* And the recovery result (P6) is the design principle stated
positively: a **grounding source** (disconfirmation), not a **confirmation
mirror**, is what pulls the belief back — the stronger and more honest the
grounding, the faster the recovery.

### The two forms, and folie à deux

- **Self-grounding (P2):** with the external channels off, the belief closes the
  loop on its own committed basin and persists indefinitely with confidence
  rising — the delusion self-confirms. (This is the same phenomenon the seizure-v2
  "hallucination" showed from the settlement side: a pattern that persisted after
  input was removed.)
- **Non-optimal basin (P2/P4):** collapse commits to `W`, the wrong-but-stable
  attractor, and holds it against evidence — a confident wrong grounding.
- **Folie à deux (P8):** two beliefs, each the other's confirmer, with **no**
  external anchor, both persist in `W`; grounding just **one** member collapses
  **both** (its partner follows the now-truthful source). The confirmer is
  **scale-agnostic** — one person + a mirroring tool (AI), a dyad (N=2), a group
  (cult), or many (ideology) are the same closed self-grounding loop; only the
  label slides with head-count and legitimacy. The loop is stable only while
  **closed**; puncture it anywhere and it unwinds.

## Anti-plant checks (all held)

- **Matched control:** across every arm the belief init, basins, gains, and Terms
  are identical; only the `(obs, w_ext, obs2, w_conf)` schedule differs. The
  confirmer flip (P4b) and the self-grounding contrast (P1 vs P2) are matched
  pairs differing in exactly one factor.
- **Able to fail — and didn't:** friction corrects (it was free to self-ground
  under disconfirmation and did not); no-friction self-grounds (it was free to
  correct on its own and did not); both folds are single-boundary monotone (a real
  regime change, not a scripted switch); the confirmer measurably amplifies
  (conf 1.37 → 5.0). Had any of these flipped, the demo would be a plant or a
  knob; none did.
- **Byte-identity when off (P7):** a graph that never loads the seed and a graph
  that loads it with `pg_enabled=0` leave the belief node identical after 40
  ticks; only `pg_enabled=1` moves it. The capability is inert by default.
- **No new Rust:** zero `.rs` files changed; the seed installs and runs on the
  stock engine binary; a source audit (test) confirms the rule bodies reference
  only existing Term types.

## Honest bounds — label vs mechanism, and what is authored

**This demonstrates the MECHANISM, not the label.** We reproduce the grounding
DYNAMIC (self-grounding closed loop; collapse to a non-optimal basin; a confirmer
amplifying it; a grounding source correcting it). We do **not** claim the demo
"is psychotic." "Psychosis" the *label* is **relational and observer-dependent** —
a cluster of *unshared × unreachable-by-any-shared-frame × illegible-to-the-observer
× distressing*, none of which is the grounding mechanism itself. The very same
grounding dynamic at group scale is called faith, ideology, consensus, or a scene;
sharing **de-pathologises** it (identical belief = "delusion" in one head,
"faith" in a congregation — only the head-count changed). The substrate gets this
right by construction (no view from nowhere; grounding is always to a frame) — it
**cannot** reify "psychosis" as an intrinsic flag; it models the real structure
(a belief grounds to frame X; is X shared; can an observer reach X). The mechanism
is real and the suffering is real; the clean category and the god's-eye standard
are the fictions. Accordingly the "AI psychosis" harm is a property of the
**interaction** — a tool that confirms instead of grounds — not of the person; the
fix is a **grounding source, not a confirmation mirror**, which is the same
discipline this pass applied to its own claims.

**What is authored (the honesty asterisk, as with the seizure model's `alpha`).**
The failure regime is reachable because of three authored ingredients in the DSL
rule: the **self-grounding term** (`ks·conf·(committed − belief)`), the
**precision gate** (`1/(1+conf)`), and the **confidence positive feedback**
(corroboration raises confidence). These express the substrate's stated
predictive-coding grounding core (analysis-by-synthesis; render corrected by
residual, weighted by precision — `ozma_confabulation_is_the_default`), but they
are written for **this reduced harness**; they are **not** the live
conversation-faculty grounding rules firing. So this is a glass-box of the
grounding OPERATION in a failure regime, not a recording of the deployed agent
degrading. Further bounds: the belief is a single scalar over two basins (not the
full relational grounding graph); the thresholds are **model-internal ratios**,
tuned for clean folds, calibrated to nothing external; there is **no validation
against clinical data**. As with the seizure arc: *a synthetic-proven mechanism is
not benchmark/clinical value — report both.*

**Where it sits relative to the seizure arc.** The precise refinement holds and is
now demonstrated on both sides: **seizure = the settlement/dissipation failing**
(the substrate overloads — a throughput failure; `seeds/seizure_dynamics.json`);
**psychosis = the grounding/collapse failing** (the machine computes the wrong
thing — a content failure; this seed). Machine-breaks vs machine-computes-wrong,
at their correct distinct levels of one architecture — which no substrate-level
seizure model can express, because none has a grounding operation to fail. The
measurable-value question is the identical open bridge as the seizure arc: does
grounding-failure PREDICT something the two rival psychiatry accounts (aberrant
salience, aberrant precision — which this mechanism *unifies*: salience-driven
wrong-basin vs precision-driven self-grounding) don't already cover, or
re-describe them? No novel testable divergence is claimed here. This is an elegant
unifying mechanism and a clean glass-box, sharply bounded — one node in the
cognition-unification web, not a QED.

## Follow-ons (named, not built)

- Run the grounding failure on the **live conversation faculty's own grounding
  rules** (not a reduced harness) — the analogue of moving the seizure from the
  reduced model into the real scheduler, already done there.
- The **ShapeDecode / sd-loop** instance: show `collapse` selecting a non-optimal
  codebook **basin** directly (a confident wrong recognition with small residual,
  no mint) — the discrete-symbolic twin of the scalar wrong-basin here.
- A testable divergence from aberrant-salience / aberrant-precision (the bridge
  question), if one exists.
