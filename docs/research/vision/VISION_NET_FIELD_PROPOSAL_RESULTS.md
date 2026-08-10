# A SMALL NET AS THE PER-CELL FIELD PROPOSAL, UNDER A REFUSABLE VERDICT — RESULTS

*Pre-registration: `VISION_NET_FIELD_PROPOSAL_PREREG.md`, committed `d0f26b8413`
BEFORE any number (§3). Block 133000–133999. Extends the scale arc (131000/132000)
and the refusal arc (129000/130000).*

> **COORDINATOR CORRECTION APPLIED:** the primary mechanism is the PROJECT's own
> graph-native self-learning net (`domains/cascade_net.py` — stacked ELM blocks,
> fixed random features + local delta-rule readout, driven by the Rust
> `cascade_collapse_step`, **NO backprop**), gated by the EXISTING external basin
> gate (`reflex_net_basin_gate_is_external`). The CONFIRM/DEGRADE/FALSIFY verdict
> RESTS ON THE PROJECT'S NET. A host-side torch conv net is kept ONLY as a labeled
> UPPER-BOUND predictability PROBE and to measure the spatial-batching gap the
> project's net lacks — it is **not** the design and **not** the verdict.

## VERDICT: **DEGRADE**, with a **first-class FALSIFY on the SCALE facet for the project's net.**

The RetinaCell state field (the "wave relaxation", 51% of the tick per 132000) **IS
cheaply predictable by the project's OWN self-training net** — the graph-native
cascade net, delta-rule, no backprop, reaches **cell-accuracy 0.9967** (primary
nb=6) / **0.9986** (nb=8), near the torch ceiling **0.99906**; the residual
CONCENTRATES on the wave front and the exogenous ignition. The external basin gate
(comparison to the substrate's OWN lawful reconstruction) beats net-confidence
CI-separated on the net's errors — the 129/130 wedge reproduced with the project's
mechanisms. **BUT the project's net does NOT attack scale — it makes it WORSE:** its
per-cell forward is a per-query PyO3 evaluation with **no spatial weight-sharing**,
so it costs **30.2 µs/cell** (nb=6) — **~23× SLOWER** than the engine's own
1.33 µs/cell relaxation — and the net-economy judge (`reflex_ms < slow_ms`,
`reflex_net_judge_is_faster_and_regression_free`) **REFUTES it**. And byte-identity
is not the net's to give: the substrate's **own exact rule, vectorized**
(numpy-exact, byte-identical) is **~500× FASTER** than the engine, so the scale
lever for a KNOWN local rule is exact vectorization, not a net.

**What the project's net would need (named, not built):** a **batched /
convolutional `net_forward`** (spatial weight-sharing) in Rust — the torch probe
shows this closes a **~380× per-cell gap** and would make an approximate net
~18× faster than the engine (still ~30× slower than the byte-identical
vectorized-exact rule). Absent that Rust extension, "small net as the dense per-cell
proposal" is a LOSS on this compute.

## 0. Provenance / engine / oracle

| item | value |
|---|---|
| branch | `worktree-agent-ab81112c9046769e5` (NOT main); base HEAD `cf6c95f360` |
| engine | `own` **`7c2aaa41748f`** @ this worktree's `runners/dsl/python/substrate_rs/_native.abi3.so` (built `scripts/engine_build.sh`) |
| Rust added | **NONE** — a measurement. `NUM_TERM_VARIANTS` unchanged, no seed, no Term. |
| re-verify after run | `source_match = own` asserted IN-PROCESS at the end of BOTH measuring scripts (`provenance_stamp()` in the committed JSON) |
| oracle BEFORE | **222 passed, 0 failed** (`rung7_vision_bench.sh`, `var/oracle_before_133000.log`), `data/` symlinked |
| oracle AFTER | **222 passed, 0 failed** (`var/oracle_after_133000.log`) |
| `check_claim` | `SEED CLAIM 133000-133999: CLEAN` — unresolved sinks **561**, verbatim in prereg §8 |
| block seeds | train worlds 133000–133003; CONFIRMATORY held-out worlds 133100–133104 (predictability/refusal) + 133100–133109 (torch probe); net init 133500; bootstrap 133600 |

## 1. Timing rigor & solitude — PROVEN by CI width (machine ALONE)

| item | value |
|---|---|
| machine | AMD Ryzen (12 logical), governor **powersave** (disclosed; depresses absolute ms — the RATIOS and exponents are governor-independent) |
| torch threads | 2 (pinned); numpy CA is pure boolean ops (single-thread); engine single-thread Rust; project-net PyO3 single-thread |
| torch-probe run loadavg | start `[1.24,1.13,1.02]` → end `[1.36,1.20,1.06]` |
| project-net run loadavg | start `[0.86,0.83,0.92]` → end `[1.04,1.06,1.03]` |
| **solitude proof (per-point CI width)** | engine ms/tick CI95 **±0.27 %–1.76 %** of median at every grid — one to two orders of magnitude below the 1.66× (66 %) contention swings prior rungs refused wall-clock over (`ENGINE_WINNER_VALUE`, `VIDEO_PROBE §0.1`). No competing job launched during either timed sweep. |
| net train cost (DATA, not a verdict) | project net train 83 s (nb=4) / 245 s (nb=6) / 486 s (nb=8) over 651 k patches, delta-rule online; torch probe train 7.6 s |

## 2. THE TARGET (measured, verified byte-identical)

The RetinaCell STATE field is a **radius-1 deterministic CA** (`wv_propagate` /
`wv_refract` / `wv_recover`) + exogenous random ignition (k=1 every 5 steps). The
`driven`/`lum`/`change` machinery does NOT enter the state transitions. A numpy
reimplementation of the CA is **byte-identical to `s.tick()`** across 9 configs ×
60 steps (`scripts/_scratch_ca_verify.py`, the positive control for the "exact"
arm). The net predicts `S_{t+1}` per-cell from `S_t` (target-B, "learns by
watching"). ~20 % of cells change per step (the wave front); the exogenous ignition
is ~0.5 % of cells and unpredictable from the field.

## 3. FACET 1 — PREDICTABILITY (the PROJECT's net is the spine; torch is the ceiling)

**PROJECT net** (cascade, delta-rule self-training, no backprop; 5 held-out
confirmatory worlds, 814 k test cells):

| config | cell acc | det acc (non-ignition) | ignition acc | class-2 **front** (recruited) acc | µs/forward |
|---|---|---|---|---|---|
| nb=4 hid=32 | 0.9901 | 0.9910 | 0.040 | 0.897 | 11.8 |
| **nb=6 hid=64 (primary)** | **0.9967** | **0.9976** | 0.040 | **0.951** | 31.6 |
| nb=8 hid=96 | 0.9986 | 0.9995 | 0.041 | 0.982 | 58.7 |
| **torch probe (ceiling)** | **0.99906** | **0.99995** | 0.047 | ~1.0 | — |

- **The project's OWN self-training net learns the per-cell field**: cell-accuracy
  0.997 (primary) → 0.999 (nb=8), approaching the torch ceiling 0.99906. DEPTH buys
  the front: class-2 (recruited = the wave front, the rare hard transition) climbs
  0.897 → 0.951 → 0.982 with blocks — the cascade's residual-refinement doing
  exactly what it is for.
- **The residual is the wave FRONT + the exogenous ignition** — CONCENTRATED, not
  diffuse (torch median error-fraction per step **0.000**; errors are the ~0.5 %
  ignition and the front's hard cells). **§13.1 named:** this concentration is
  FORCED by the CA's locality (a radius-1 deterministic rule is learnable by any
  local net) and by ignition being spatially sparse by construction — it is not a
  risky prediction, and I do not claim it as evidence for the design.
- **Ignition is unpredictable to every net** (acc ~0.04): a random rested→active
  draw is exogenous entropy with no antecedent in the field.

## 4. FACET 2 — COMPUTE-∝-SURPRISE / SCALE (the FALSIFY, on the project's net)

Three implementations of the SAME field update, timed ALONE (µs per cell):

| grid | ENGINE (`s.tick`, waves-only) | NUMPY-EXACT (byte-identical) | torch-conv probe (batched) | **PROJECT net (nb=6, per-cell PyO3)** |
|---|---|---|---|---|
| 16² | 1.44 | 0.049 | 0.252 | **30.5** |
| 64² | 1.33 | 0.0066 | 0.106 | **30.2** |
| 256² | 1.41 | 0.0026 | 0.079 | **30.2** (proj.) |
| **exponent (log-log)** | **0.999** (linear) | **0.48** (sublinear) | **0.776** (sublinear) | **1.00** (per-cell constant) |

- **The project's net LOSES to the engine it is meant to accelerate.** 30.2 µs/cell
  vs the engine's 1.33 µs/cell = **~23× SLOWER** (nb=6; nb=4 ~9×, nb=8 ~44×), at a
  CONSTANT per-cell cost with no batching (exponent 1.0). The net-economy judge
  (`reflex_ms < slow_ms`) **REFUTES** this reflex net — it is not faster, so by the
  project's own adoption rule it is never enabled.
- **Byte-identity is NOT the net's to give — the substrate's OWN exact rule
  dominates.** NUMPY-EXACT (the CA vectorized, byte-identical to the engine) is
  **~500× faster** than the engine at 256² and SUBLINEAR (exp 0.48 — vectorization
  amortizes). For a KNOWN local rule the scale lever is exact vectorization of the
  rule the substrate already holds, not an approximate net. The sound surprise-gate
  confirms this: a byte-identical "gate" fills the deterministic-change band with
  the exact reconstruction and the static bulk with the known-static value — i.e. it
  **is** the exact rule, using the net nowhere (the net-trusting variant is only
  99.7 % sound: the net occasionally errs on a "static" cell the band trusts).
- **The batching gap is the whole story, and it is NAMED.** The torch conv (batched,
  weight-shared) is **~18× faster than the engine** and **~380× faster per cell than
  the project's per-query net** (0.079 vs 30.2 µs/cell @256²). The project's
  `net_forward` evaluates ONE query at a time (a per-decision reflex, not a dense
  spatial map); to be the dense per-cell proposal it needs a **batched /
  convolutional `net_forward`** with spatial weight-sharing in
  `runners/dsl/src/net_forward.rs` — a real Rust extension, not a config. Even then
  it would be ~18× faster than the engine but still ~30× slower than the
  byte-identical vectorized-exact rule.

## 5. FACET 3 — REFUSAL (external basin gate vs net-confidence; the 129/130 wedge)

The external gate = the substrate's OWN lawful reconstruction (the held CA rule,
net-INDEPENDENT — `reflex_net_basin_gate_is_external`); confidence = the net's
softmax margin (a SELECTION). Paired bootstrap AUROC on "is this cell a net error",
PROJECT net (primary), 814 k cells:

| error subset | AUROC comparison (external gate) | AUROC confidence (net) | paired diff [95% CI] |
|---|---|---|---|
| all errors | 0.853 | 0.850 | **+0.0030 [+0.0027,+0.0034] SEP+** |
| deterministic errors | 0.999 | 0.995 | **+0.0041 [+0.0037,+0.0047] SEP+** |
| ignition errors (within) | 0.289 | 0.289 | 0.000 **ns** (both blind) |

- **The wedge reproduces with the project's mechanisms:** the external comparison
  gate beats net-confidence CI-separated on the net's own errors — on the
  deterministic errors it is near-perfect (0.999) because the substrate holds the
  exact generator. This is 129/130's "a comparison can refuse, a selection cannot",
  at the field level, with the project's external basin gate.
- **But the margin is NARROW** (+0.003…+0.004), because a well-trained net's
  confidence is already well-calibrated on this EASY deterministic task — the gap
  the wedge exploits shrinks as the net improves. (The torch probe, det-acc 0.99995,
  shows comparison AUROC **1.000** vs confidence 0.9991 on its handful of
  deterministic errors — the wedge is real but the errors are vanishing.)
- **The honest floor of refusability:** EXOGENOUS ignition is unrefusable by BOTH
  signals (AUROC 0.289, ns). A rested cell with no active neighbour that ignites is
  an IN-BASIN input with an EXOGENOUS outcome — it violates no rule, so a comparison
  has nothing to compare against and confidence has no reason for doubt. **You can
  refuse a rule-violation; you cannot refuse an unpredictable draw.** This sharpens
  the wedge: comparison beats selection where a reconstruction EXISTS; where the
  surprise is exogenous entropy, neither can help.

## 6. THE DISCRIMINATOR, RESOLVED

- **CONFIRM (not met):** would require the PROJECT's net to attack scale at a
  measured, growing speedup AND beat NUMPY-EXACT AND a sound gate reproduce the
  field. The project's net is ~23× SLOWER than the engine and ~11000× slower than
  NUMPY-EXACT; refuted by the net-economy judge.
- **DEGRADE (met):** predictable (0.997) with a concentrating residual and a
  CI-separated refusal wedge — the mechanism facets hold — but (a) predictability &
  concentration are FORCED by CA locality (§13.1), (b) the project's net is
  DOMINATED by the byte-identical exact vectorization, and (c) the refusal margin is
  narrow with an exogenous floor neither signal crosses.
- **FALSIFY on the SCALE facet (first-class, per the coordinator's mandate):** the
  project's net as it exists CANNOT be the dense per-cell proposal for scale — a
  per-query `net_forward` with no spatial batching is slower than the compute it
  proposes to replace. The named extension is a **batched/convolutional
  `net_forward`** (Rust). This is a real, valuable capability finding: the reflex
  net is a per-decision CACHE, not a dense spatial predictor.

## 7. SCOPE — what is NOT shown (§8)

- **The representation frontier is UNTESTED.** The wave state field has no rich
  learned representation (it is a 4-symbol CA), so this rung speaks to SCALE and to
  the net-as-proposal mechanism, NOT to the representation deficit 130000 named.
- **KNOWN vs UNKNOWN dynamics.** The verdict is specific to a KNOWN local rule the
  substrate can vectorize exactly. The net-proposal design's payoff needs an
  UNKNOWN/complex per-cell update where no exact vectorization exists — the wave CA
  is not one. This rung does NOT show the design fails for unknown dynamics; it shows
  it is dominated for THIS (known, cheap-to-vectorize, local) compute.
- **The CONSTRUCTED-net grade is not exercised.** The reflex_net microtheory names
  two grades — a CONSTRUCTED (write-not-train, EXACT) net and a TRAINED (fuzzy,
  basin-limited) net. The CA, being an exact local rule, maps to the CONSTRUCTED
  grade (weights could be authored to compute it exactly) — which is just the exact
  rule again, confirming §4's finding from the other side. I measured the TRAINED
  grade (the self-learning net the mandate specifies).
- Governor powersave; single CNN/cascade family; one grid family; CPU; waves-only
  boot (the pure state CA, cheaper per cell than 132000's assembled-eye tick).

## 8. WHAT I GOT WRONG

1. **I first built the WRONG net.** My initial instrument used a host-side torch
   conv net as the primary mechanism — which is NOT the project's design and
   violates the architecture rule. Corrected on the coordinator's instruction: the
   spine is now the project's graph-native self-learning net; torch is a labeled
   probe only. The torch results stand solely as the predictability ceiling and the
   batching-gap measurement.
2. **My prereg predicted the net would be "dominated by NUMPY-EXACT" but I
   under-weighted HOW dominated.** The project's net is not merely slower than a
   vectorized exact kernel — it is slower than the ENGINE itself (~23×), because I
   had not accounted for the per-query PyO3 round-trip cost with no spatial batching.
   The FALSIFY is sharper than my "DEGRADE — buys nothing" prediction.
3. **The refusal wedge is narrower than the raw 129/130 number suggested.** On a
   well-trained net over an easy deterministic task, net-confidence is already good,
   so comparison's edge is +0.003…+0.004 (still SEP+), not the wide margin the
   Omniglot regime showed. I report the narrow margin and the exogenous-ignition
   floor (AUROC 0.289, unrefusable) rather than the headline det-error 0.999.
4. **The engine's per-cell relaxation is cheaper than 132000's 7 µs/cell** — that
   figure was the ASSEMBLED EYE (with lateral); the pure waves-only state CA I
   predict is ~1.33 µs/cell. I compare the net against the right object (the pure
   relaxation), which makes the net's ~23× slowdown, not a smaller one, the honest
   number.

## 9. Bench state — no new instrument-seams red

`tests/test_instrument_seams_migrated.py`: the 3 pre-existing reds
(`codec_decision_probe.py` preamble floor; stale measured-ledger over other blocks;
other rungs' preregs missing check_claim) are unchanged; **my prereg records its
`check_claim` verbatim (§8), and my two measure scripts call `engine_preamble()`**
(not a bare import), so I add **no new preamble violation and no new
prereg-missing-claim red**. My scripts draw only in-block seeds and touch no ledger,
floor, or seed file. (Verified in §10 below.)

## 10. Ledger row (transcribe to VISION_PROTOCOL.md — do NOT edit it here)

| block | outcome |
|---|---|
| **133000–133999 (train worlds 133000–133003, confirmatory held-out 133100–133109, net-init 133500, bootstrap 133600 — literal in-block seeds, disclosed; `check_claim` CLEAN, unknown_sinks 561; NO Rust, NO seed, NO Term — a measurement over the committed wave CA + the project's cascade/reflex net)** | **SMALL NET AS THE PER-CELL FIELD PROPOSAL — DEGRADE, with a first-class FALSIFY on SCALE for the PROJECT'S net.** The RetinaCell state field (the 51% "wave relaxation", verified a radius-1 deterministic CA byte-identical to `s.tick()`) IS cheaply predictable by the PROJECT'S OWN graph-native self-training net (cascade, delta-rule, NO backprop): cell-accuracy 0.9967 (nb=6) → 0.9986 (nb=8), residual on the wave FRONT (class-2 recruited 0.951→0.982 with depth) + the exogenous ignition (unpredictable, ~0.04 acc); torch ceiling probe 0.99906. **§13.1: predictability + concentration are FORCED by the CA's locality/sparse-ignition, named not claimed.** REFUSAL: the external basin gate (comparison to the substrate's OWN lawful reconstruction, net-independent — `reflex_net_basin_gate_is_external`) beats net-confidence CI-separated (deterministic errors 0.999 vs 0.995 SEP+; all 0.853 vs 0.850 SEP+) — the 129/130 wedge reproduced with the project's mechanisms — but NARROW (well-trained confidence is already good) and with an honest floor: EXOGENOUS ignition is unrefusable by BOTH (0.289, ns) — a comparison refuses a rule-violation, never an unpredictable draw. **SCALE = FALSIFY:** the project's net (per-query `net_forward`, NO spatial weight-sharing) costs 30.2 µs/cell (nb=6) = ~23× SLOWER than the engine's own 1.33 µs/cell relaxation, per-cell CONSTANT (exp 1.0) — the net-economy judge `reflex_ms<slow_ms` REFUTES it. Byte-identity is the substrate's OWN rule vectorized (NUMPY-EXACT, byte-identical, exp 0.48, ~500× FASTER than the engine at 256²) — the scale lever for a KNOWN local rule is exact vectorization, not a net. NAMED extension (not built): a batched/convolutional `net_forward` in Rust closes the ~380× per-cell batching gap the torch probe measures (torch conv ~18× faster than engine) but still ~30× slower than vectorized-exact. Representation frontier UNTESTED (the field has no rich representation). WHAT I GOT WRONG: (1) first built a torch net as primary (wrong — corrected to the project's net; torch is a labeled probe); (2) under-predicted the slowdown (the net is slower than the ENGINE, not just than numpy-exact); (3) the refusal wedge is narrow, not wide, on a well-trained net; (4) the engine relaxation is 1.33 µs/cell (waves-only), not 132000's assembled-eye 7. Engine `own` `7c2aaa41748f` re-verified `own` in-process after the run; oracle `rung7_vision_bench` **222/0 BEFORE and AFTER**; `check_claim` verbatim in prereg §8; loadavg proven-alone by per-point CI ±0.27–1.76% (vs 1.66× contention swings); governor powersave. Raw: `results/net_field_project.json` (spine), `results/net_field_proposal.json` (torch probe); instruments `scripts/net_field_project_measure.py`, `scripts/net_field_proposal_measure.py`; CA control `scripts/_scratch_ca_verify.py`. |
