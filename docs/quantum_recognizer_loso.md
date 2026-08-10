# Quantum-probability recognizer vs the classical combines (cross-speaker LOSO)

Applies the **"a postulate is a quantum state"** framework
([[ozma_postulate_is_a_quantum_state]] / [[ozma_collapse_is_gamma_application]]) to
the EAR. The classical combines all hit the cross-speaker LOSO wall — FLAT product
0.323, EXCLUSION 0.228, VECTOR 0.305 (full 10-digit, commit 54fd606b) — and they are
all **commutative** (order-blind) and **interference-free** (a sum/product of paths,
no cross-terms). The quantum framing asks whether recognition instead carries
quantum-probability structure the classical combine cannot hold.

## What was built (donkey-clean — composable linear algebra, owned ops, no fit/net)

`domains/many_settings_recognizer.py` — `cue_amplitude`, `cue_operator`,
`quantum_recognize`; driven by `scripts/quantum_recognizer_loso.py`.

- **WORD-STATE** `psi` = a COMPLEX amplitude vector over the candidate words — a
  superposition of held word-hypotheses, init uniform (the flat prior).
- **CUE = MEASUREMENT OPERATOR.** From the cue's per-word 1-NN distances `D_c(w)`
  (the SAME evidence the classical recognizer uses) build the complex evidence
  amplitude `e_c`:
  - `|e_c(w)| = exp(-D_c(w) / (2 T_c))`, `T_c` = the cue's own median candidate
    distance (read from data, not searched). This is the **square-root of the
    classical Gaussian likelihood**, so `|e_c(w)|^2` reduces EXACTLY to the classical
    softmax factor (Born: `|amp|^2 = prob`).
  - `arg(e_c(w)) = PHI · (med_c − D_c(w)) / spread_c` — `PHI · (the cue's SIGNED
    MARGIN in robust-spread/MAD units)`. Positive phase where the cue prefers `w`,
    negative where it disprefers it. **The phase is DERIVED from the cue's own signed
    margin, not fitted.** `PHI = π/2` is a fixed structural quarter-turn per
    spread-unit (a unit choice); zeroing `PHI` removes the phase → no interference.
  - Operator `M_c = (1−β)·diag(e_c) + β·(ê_c ê_c†)`. The diagonal term reduces to the
    classical product; the **rank-1 complex outer-product** is the non-diagonal
    measurement back-action that makes operators **non-commuting** and seeds
    interference. `β = 1/2` is the maximally-balanced weak measurement (structural,
    not searched). **β = 0 ⇒ purely diagonal ⇒ commutes ⇒ Born = classical product
    exactly** (verified in a smoke test).
- **SEQUENTIAL, NON-COMMUTING:** `psi_final = M_K … M_1 psi` (renormalize after each).
- **BORN:** `P(w) = |psi_final(w)|^2`; recognize = argmax.

**Donkey audit:** amplitudes/projectors/Born = the agent's owned linear algebra; the
phase is derived from each cue's signed margin; β a fixed structural constant. No fit,
no net, no searched parameter. Cues = the SAME COCHLEA / SHARP-HF / MANNER-VOICE /
FRIC-VOICE channels the classical pool uses. Held-out speakers never banked; LOSO
ungameable. Config: 120 train / 40 held-out speakers, 20/word, seed 20240609.

## Results (captured, /tmp/quantum_run.txt, marker QUANTUM_RECOGNIZER_LOSO_COMPLETE)

### Test 1 — ACCURACY

| set | FLAT | EXCLUSION | VECTOR | **QUANTUM** |
|---|---|---|---|---|
| Full 10-digit | 0.323 | 0.228 | 0.305 | **0.142** |
| Fricative set | 0.492 | 0.329 | 0.412 | **0.221** |

The quantum combine is **far WORSE** than every classical combine — 10-digit
−0.180 vs FLAT, −0.163 vs VECTOR; fricative −0.271 vs FLAT, −0.192 vs VECTOR. It does
not beat the wall; it falls below it.

### Test 2 — ORDER EFFECTS (non-commutativity)

| set | order spread (max−min acc) | per-query argmax changes with order |
|---|---|---|
| Full 10-digit | 0.062 (0.142 → 0.205) | **99.0%** of probes |
| Fricative set | 0.067 (0.196 → 0.263) | **97.1%** of probes |

Order effects are **strongly present** (classical = exactly 0). The cue operators
genuinely do not commute: nearly every probe's argmax flips depending on cue order.

### Test 3 — INTERFERENCE (phase-ON vs phase-OFF, φ=0)

| set | acc phase-ON | acc phase-OFF | Δ | Born L1 shift | argmax flips |
|---|---|---|---|---|---|
| Full 10-digit | 0.142 | 0.203 | **−0.060** | 0.581 | 76.5% |
| Fricative set | 0.221 | 0.308 | **−0.088** | 0.570 | 74.2% |

Interference is **strongly present** — the complex cross-terms move the Born
distribution by ~0.57 L1 per query and flip ~75% of argmaxes. But the interference is
**destructive/harmful**: turning the phase ON *lowers* accuracy (phase-OFF beats
phase-ON on both sets). The cross-terms do a lot of work, and the work hurts.

## VERDICT

**QUANTUM FRAMING BUYS NOTHING HERE — reported plainly, NOT rescued.**

The kill criterion required quantum to **beat** classical AND show order-effects +
interference. The machinery shows order-effects and interference **emphatically**
(spread 0.062, 99% order-sensitive argmaxes, L1 0.581, 76% phase-flips on the
10-digit set) — the non-commutation and complex cross-terms are real and large. But
quantum **does not beat classical**; it is dramatically worse (0.142 vs FLAT 0.323).
The interference is destructive, and the rank-1 back-action scrambles the readout that
the classical diagonal product gets right.

This is consistent with — and re-confirms — the 54fd606b finding: **the residual is a
PERCEPTION limit (the cross-speaker feature wall), not a combine problem.** The
classical FLAT product was already the right (simple) combine for this number. The
quantum structure is genuinely *there* (order-effects + interference are not zero —
the operators are non-commuting by construction), but on THIS recognition task that
structure is a liability, not a lever: it injects sensitivity to a feature wall that
the order-blind, interference-free product simply averages over.

Honest reading against the theory: the prediction was "if quantum beats classical AND
shows order/interference, recognition is quantum-structured." The conjunction FAILS at
the first clause. The framework correctly *predicts the existence* of order-effects and
interference once you build complex amplitudes with derived phase — but their
*presence does not imply a capability gain*, and here it is a loss. The quantum-cognition
signatures are reproducible in the substrate; they are simply **not the lever for this
cross-speaker recognition number**. The next lever remains the FEATURE (make the cues
separate cross-speaker / measure cue reliability held-out), exactly as 54fd606b
concluded — not the combine, classical OR quantum.

## Suites

Required suites green: `test_stt_pipeline`, `test_perception_self_assessment`,
`test_process_meta_assessor`, `test_gap_guidance`, `test_frontend_effect_gate`
(36 passed). Not committed.
