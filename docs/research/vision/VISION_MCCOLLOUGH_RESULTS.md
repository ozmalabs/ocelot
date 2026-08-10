# VISION — the McCOLLOUGH CONTINGENT AFTEREFFECT (RESULTS)

*Confirmatory run of `VISION_MCCOLLOUGH_PREREG.md` (committed BEFORE the run at
`de452643`, §3). Runner `scripts/mccollough_measure.py`; gate
`tests/test_mccollough_migrated.py`; seed `seeds/vision_mccollough.json` (builder
`tools/build_vision_mccollough.py`); adapter `domains/mccollough_world.py`; raw
`results/mccollough_measure.json`.*

## Engine / bench / provenance (§10)

- **Engine `7d5f50c18673`** @ `runners/dsl/python/substrate_rs/_native.abi3.so`
  — **shared build, Rust source byte-identical** to canonical (`provenance_line()`
  reads *"shared build … Rust source identical"*; this rung adds **NO Rust**, so the
  shared build is legitimate, §10.1 rule 4). No `data/` dir in this worktree
  (§10.2).
- **Named vision bench: 190 passed / 10 skipped** (`scripts/rung7_vision_bench.sh`,
  127.5s) — **exactly the documented no-`data/` baseline** ("200 passed with `data/`,
  190/10 without", VISION_COLOUR_RESULTS.md §10.2). The 10 skipped are the
  `data/`-dependent BSDS corpus tests; nothing failed.
- **The sd orbit law `{2:1,3:2,4:2,6:2,12:4}` is UNMOVED** (`test_sdloop_vision_migrated.py`
  orbit/arithmetic/mint tests = 4 passed).
- **Sibling gates green** (see §9 below).
- **NO new Rust, ONE new seed** (`vision_mccollough`, NOT boot-loaded; ships
  `MccoughParams{mcc_enabled:0, mcc_mode:0, mcc_phase:0, frame:0}` — the seed is
  INERT with `mcc_enabled=0` by default), so §9 byte-identity holds by construction
  and is verified by the bench + siblings above.

## Verdict — ALL 8 gated arms PASS; every headline prediction held; NO proviso broke; the gate DISCRIMINATES

| arm | result |
|---|---|
| **H_contingency** (headline) | **PASS** — after red-vertical / green-horizontal adaptation, an ACHROMATIC vertical test yields `percept_rg = −10.0` (GREEN-biased) and a horizontal test `+10.0` (PINK-biased); contingency `C = −20.0`. The prior learned `mean_rg = +10` (vertical) / `−10` (horizontal) — E[colour\|orientation]. `percept_by = 0.0` both (proviso 1 held: pure rg-axis contingency). |
| **swap_flip** (the JOINT claim) | **PASS** — the SAME achromatic patch read under `theta=vertical` → `−10.0`, under `theta=horizontal` → `+10.0`: the aftereffect colour FLIPS with orientation. The effect lives in the colour⊗orientation JOINT. |
| **crux — THE decisive test (§1.1)** | **PASS** — PREDICTIVE arm `(−10, +10)` PRODUCES the aftereffect; the FEEDFORWARD control `(0.0, 0.0)` produces NONE (achromatic in → achromatic out), for BOTH orientations. `D_crux = 10.0` (the arms genuinely differ). The FF arm is **ALIVE** — a coloured (red) test reports the real colour `+10.0`, so its achromatic null is a real null, not a dead arm scoring a perfect floor. **A feedforward classifier cannot fake McCollough.** |
| **H_persist** (error-driven, not fatigue) | **PASS** — the prior `(sum_rg=+80, n=8)` is BIT-IDENTICAL across a 50-tick intervening no-adaptation block; the percept is unchanged `−10.0` (not fatigue, which recovers). Error-driven: `n` grows `1 → 8` with exposure. |
| **H_floor (no adaptation)** | **PASS** — no adaptation ⇒ prior `n=0` ⇒ `percept_rg = 0.0`. No aftereffect. |
| **H_floor (colour alone)** | **PASS** — RED adapted on BOTH orientations ⇒ `percept_rg(vert) = percept_rg(horiz) = −10.0`, contingency `C = 0.0`: an aftereffect exists but is NOT orientation-contingent. |
| **H_noise** (anti-overfit, n=100) | **PASS** — **0/100** iid colour-noise adaptation sequences (seeds 41000–41099) reach a contingency `\|C\| ≥ 20` (the structured magnitude); `mean C_noise = −0.35 ≈ 0`, `max\|C_noise\| = 11.25`. Zero-mean adaptation averages to no pairing. |
| **H_offday** (§9) | **PASS** — `mcc_enabled=0` (default) ⇒ every percept `0.0`, prior `n=0`: inert. |

## The headline — the contingent aftereffect IS the negative residual of an over-fit contingency prior, and a feedforward control cannot produce it

**Three seed rules realise the grounding's mechanism (VISION_VENTRAL_GROUNDING.md
§FAILURE-MODE GATES §2) with ZERO new Rust and ZERO magic numbers:**

- **`mcc_learn`** accumulates the joint statistic `E[colour | orientation]` — the
  running MEAN colour given orientation (`Div(sum, Max(n,1))`), a stored prior with
  NO learning rate. This is the "over-fit contingency prior."
- **`mcc_percept_pred`** is vision_lateral's *predict-then-transmit-the-residual*
  shape with the ORIENTATION prior as the predictor: `percept = observed −
  render-from-prior`. On an ACHROMATIC test (observed = 0) the percept is `−prior`:
  opposite the adapted colour, in OPPONENT space (negative rg = green), CONTINGENT on
  orientation. **This is render-from-prior + opponent-residual, exactly.**
- **`mcc_percept_ff`** is the FEEDFORWARD control: `percept = observed colour`, read
  directly. The prior is MATCHED (identical information available) but NOT rendered
  or subtracted — no predictive loop. Achromatic in ⇒ achromatic out ⇒ NO aftereffect.

**The crux is the whole test, and it discriminates exactly.** The predictive and
feedforward arms are the SAME seed, the SAME inputs, the SAME prior available; they
differ ONLY in whether the render-from-prior is subtracted. The predictive arm
produces the full contingent aftereffect `(−10, +10)`; the feedforward arm produces
`(0, 0)`. `D_crux = 10.0`. **This is the §1.1 discrimination the grounding named as
"highest discriminative value": a genuine predictive/opponent code produces the
contingent aftereffect; a feedforward classifier control does not.** And the control
is provably ALIVE (a coloured test → `+10`), so its null is a real null.

## §13 — every number falls out; NO magic number

- **The prior is a running MEAN (`sum/Max(n,1)`)** — no learning rate, no time
  constant. The aftereffect MAGNITUDE equals the adapting-colour magnitude by
  construction; the aftereffect SIGN is fixed by the sign of the adapting colour and
  is invariant to any scale or frame count. No number was tuned to make an output
  look right.
- **`Max(n,1)`'s `1`** is the div-by-zero floor idiom (cc_contrast's
  `Max(Fold(+1),1)`), so an un-adapted orientation reads `0/1 = 0` — the floor arm
  falls out, not put in.
- **The `0.5` thresholds** are flag/boolean discriminators (every seed's idiom), not
  magnitudes.
- **Orientation labels (90/0) and stimulus cone values** are stimulus identity, not
  model constants; the result depends only on the labels being DISTINCT.
- **FRAMES=8** is an arbitrary exposure; no arm's truth depends on it (persistence
  reads `n=8`, but the SIGN/contingency/crux/floor claims are frame-count-invariant).

## §9 — defaults preserve committed results (byte-identity)

The seed ships OFF (`mcc_enabled=0`) and is NOT boot-loaded, so §9 holds by
construction. Verified:

- **Named vision bench 190 passed / 10 skipped** — the documented no-`data/`
  baseline, unchanged.
- **sd orbit law `{2:1,3:2,4:2,6:2,12:4}` unmoved** (sdloop orbit/arithmetic/mint
  = 4 passed).
- **Sibling gates green** — colour-salience, colour-identity, dimension-inference,
  time, depth, stereo, gen-infer, illusion, vision-ground, cycle-detect,
  engine-provenance, and the new McCollough gate (8/8) — all pass (see the run log).
- The `mcc_learn` / percept rules fire ONLY when `mcc_enabled>0.5`, which no other
  seed sets, and on `Scene`/`Region`/`Contingency` nodes only this adapter builds.

## Audit — what was already built vs the contribution (§12.4, in-code)

Verified in the source before designing (cited in the prereg §0):

- **Cone-opponent colour is expressible by composition — no new Rust.**
  `seeds/vision_colour.json` `cc_contrast` (VISION_COLOUR_RESULTS.md) computes the
  opponent coordinates `rg = L−M`, `by = S−(L+M)` inline from raw cone attrs;
  reused verbatim as the colour representation (`build_vision_mccollough.py:RG/BY`).
- **The render/residual shape is already a seed rule.**
  `seeds/vision_lateral.json` `lat_residual` (388–583) is *"predict the centre from
  the surround; transmit the residual."* The McCollough percept is the SAME shape
  with the predictor swapped to the ORIENTATION prior.
- **The EMA/accumulate + per-frame guard idiom exists.**
  `seeds/vision_theta.json` `th_track_rbar` accumulates a running average behind a
  `rbar_step<step` per-frame guard; `mcc_learn` uses the same guard (`astep<frame`).
- **The incoming-edge join exists.** `seeds/vision_onoff.json` `oo_bipolar_burst`
  matches `[[a,edge,b],[c,edge2,b]]` (a bound node found via an incoming edge);
  `mcc_learn`/percept use `[["scene","has_region","R"],["K","tunes","R"]]`.
- **A learnable JOINT colour⊗orientation prior did NOT exist** — this rung builds the
  first, as pure graph data.

**The contribution:** ONE seed (`vision_mccollough.json`, flag OFF by default) whose
three rules learn the joint E[colour\|orientation] and read the predictive
render-from-prior + opponent-residual (`mcc_percept_pred`) vs the feedforward direct
read (`mcc_percept_ff`), plus a ~120-line mechanical adapter
(`domains/mccollough_world.py`). NO new Rust; the whole mechanism is the existing DSL
(`Attr/Minus/Plus/Times/Div/Max/Gt/Lt/And/NodesWhere/PickUnique/set_attr`).

## Scope — what is NOT shown (§8), and the named frontier

- **A VALIDATION gate for predictive/opponent JOINT colour⊗orientation coding — NOT
  a recognition capability.** It shows the substrate's render-from-prior +
  opponent-residual reproduces the decisive contingent aftereffect a feedforward
  classifier cannot, and nothing about object/scene recognition.
- **Orientation is supplied as a stimulus FEATURE (`theta`), not grown.** Grown
  orientation-selective maps are the diagnosed Hebbian dead-end (`vision_theta.json`
  / MEMORY); a validation gate legitimately takes orientation as input, as it takes
  cone values as input. The claim is about the JOINT PRIOR and the PREDICTIVE
  READOUT — which ARE the graph's.
- **The prior is a running mean over a small oriented colour patch**, not a full
  grating field with spatial phase. The colour⊗orientation contingency, not the bar
  structure, is what the effect requires.
- **NOT claimed biological in magnitude or time-constant** — only that the SIGN,
  contingency, OPPONENT character, persistence-vs-fatigue, and the
  feedforward/predictive DISSOCIATION reproduce. No decay dynamics, no persistence
  duration in real units.
- **NAMED FRONTIER (not this rung):** the other FAILURE-MODE GATES —
  apperceptive/associative dissociation, face-inversion + Thatcher, crowding,
  cerebral achromatopsia (VISION_VENTRAL_GROUNDING.md §FAILURE-MODE GATES).

## Is the "what"/opponent layer genuinely PREDICTIVE-CODING? — the plain answer

**Yes, on this decisive test.** The substrate learns the joint colour⊗orientation
statistic and, at test on an achromatic grating, RENDERS the expected colour from
that prior and perceives the OPPONENT RESIDUAL (observed − predicted): vertical →
green, horizontal → pink, flipping with orientation — the McCollough contingent
aftereffect. A FEEDFORWARD control with the same prior available but no
render-from-prior produces NO aftereffect, while remaining alive to real colour.
**The predictive loop is load-bearing (§13.2): toggle the readout mode and the
aftereffect appears/vanishes (`D_crux=10`), a change nothing else drives.** With
ZERO new Rust and ZERO magic numbers. **Bounded to** the validation-gate scope:
orientation supplied as a stimulus feature, a colour⊗orientation contingency on the
rg axis, no biological magnitude/time-constant claim; the other failure-mode gates
are the named, unreached frontier.
