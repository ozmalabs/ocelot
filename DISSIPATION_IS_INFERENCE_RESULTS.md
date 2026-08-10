# VISION — DISSIPATION *IS* INFERENCE: results (block 197000)

*Prereg (committed ALONE, before any number): `DISSIPATION_IS_INFERENCE_PREREG.md`
@ commit `dcd212bbdc`. Worktree off `main` HEAD `6342f643bb`. Engine canonical
`793ce09ed498a749abb79aeaea44b92e` — **UNTOUCHED before and after** (NO Rust,
`term.rs` diff EMPTY). Seed block 197000–197999, seed-claim CLEAN (verbatim in the
prereg). All numbers are deterministic (`default_rng(197000)`); no wall-clock claim.*

Raw: `results/dissipation_inference.json`, curves
`results/dissipation_inference/dissipation_inference.png`. Gate:
`tests/test_dissipation_inference_migrated.py` (5/5). Measure:
`scripts/dissipation_inference_measure.py`. Seed: `seeds/dissipation_inference.json`
(authored by `tools/author_dissipation_inference_seed.py`).

## The result in one line

**ONE integer relaxation dynamics settles a field. Read as physics it is a
second-law dissipative relaxation whose free energy falls monotonically to
equilibrium; read — under a pure relabel that touches no arithmetic — as
cognition it is MAP inference over a Gaussian MRF that denoises a noisy input to
the percept. The two readings are the SAME byte-identical integer trajectory, and
forcing the physics uphill (anti-dissipative) destroys the perception: they are
one process, not two that coincide.** All five pre-registered gates pass.

## The shared dynamics (as implemented)

A 24×24 grid of `FieldCell{val, obs, par}` nodes on 4-connected `adj` edges, with a
single `RelaxField{enabled, lam=2, phase, sign}` hub. ONE `batch` rule `df_relax`
(seed `dissipation_inference.json`) updates only cells with `par == phase` to their
conditional integer argmin:

```
num  = lam*obs_i + Σ_{j∈adj(i)} val_j          # Sum over Neighbours(i,"adj")
den  = lam + deg_i                             # lam + Count(Neighbours(i,"adj"))
cand = IDiv(2*num + den, 2*den)                # round-to-nearest INTEGER argmin
val_i ← IfThenElse(sign>0, cand, 2*val_i - cand)   # descent : reflected ascent
```

Red-black colouring (`par=(row+col)&1`, the adapter flips `phase` between
`run_rules(1)` half-sweeps — a mechanical clock) makes every simultaneously-updated
cell mutually non-adjacent, so one half-sweep is **exact integer block coordinate
descent**. The energy `E` is a sum of integer squares → the descent is exactly
monotone with no rounding limit cycle, terminating at a fixed point in finitely
many sweeps. Operators used — `Sum`, `Neighbours`, `Count`, `Attr`, `IDiv`, `Plus`,
`Times`, `Minus`, `IfThenElse`, `Gt`/`Eq`, `And`, `Var`, `Lit` — **all exist;
`term.rs` diff EMPTY; NO Rust.**

## The relabel table — the ENTIRE difference between the frames (pure, zero dynamics)

| neutral object | PHYSICS frame | COGNITION frame |
|---|---|---|
| `val_i` (integer state) | microstate configuration | posterior MAP estimate `x_i` |
| `obs_i` (fixed integer) | external field / boundary source | noisy observation `y_i` |
| `lam` (=2) | coupling / inverse-temperature weight | likelihood precision |
| `adj` edge | nearest-neighbour interaction | MRF smoothness clique |
| `E = λΣ(x−obs)² + Σ_edges(x−x_j)²` | Gibbs free energy (Hamiltonian) | negative log-posterior |
| a settling half-sweep | dissipative relaxation step | one coordinate step of MAP inference |
| the fixed point | thermodynamic equilibrium | the MAP percept |
| `E` decreasing | free energy dissipated → 2nd law | evidence maximised → inference converges |
| `sign<0` | anti-dissipative (energy pumped in) | inference de-maximised |

## Gate results (all PASS)

### G1 — THE IDENTITY (one computation, two readings)
- The physics-labelled and cognition-labelled runs (same builder, differing only
  in the relabel dict) produce a **BYTE-IDENTICAL integer `val`-trajectory**, 17
  ticks to the fixed point.
- The Gibbs-energy functional and the negative-log-posterior functional, computed
  on that ONE trajectory by **independent code paths**, are the **element-wise
  identical integer sequence**: head `[1794634, 1221797, 758346, 725363, …]` for
  BOTH — because they are the same formula, renamed.
- Source audit: the relabel is a pure `str→str` dict; it appears in no `set_attr`
  and no arithmetic. **PASS.**

### G2 — PHYSICS HOLDS (the 2nd law)
- Free energy **monotonically non-increasing every half-sweep**, `1794634 →
  716683` over 16 sweeps, then constant (fixed point reached):
  `[1794634, 1221797, 758346, 725363, 719044, 717455, 716956, 716784, …]` — never
  rises. `E` is an EXACT integer throughout.
- Entropy produced `S(t) = E(0) − E(t)` rises monotonically to its max `1077951`.
- **PASS** (monotone-down ∧ reached fixed point ∧ entropy-up).

### G3 — COGNITION WORKS (percept recovery = MAP)
- `obs = clean + integer noise (±40)`. Recovery error
  `‖val(t) − clean‖₁`: **11452 (noisy input) → 6292** (denoise ratio **0.55**).
- The fixed point `val*` is **byte-identical to an independent numpy red-black
  integer denoiser** (same fixed point — it IS the same ICM/MAP algorithm), and
  **within 1** (`max|val* − round(x*_real)| = 1`) of the exact real linear-solve MAP
  `x* = (L+λI)⁻¹λy`. "It matches because it IS it." **PASS.**

### G4 — BREAK-ONE-BREAKS-BOTH (the key falsifier, non-vacuity)
- Flip the SAME rule to anti-dissipative (`sign=−1`, reflected ascent), same grid,
  same init. Free energy is forced **monotonically UP and diverges**:
  `1794634 → 782,559,357,815` (`[1794634, 3514457, 6049318, 15190983, 31914738,
  87383386, …]`).
- The perceptual recovery **breaks with it**: recovery error rises monotonically
  `11452 → 5,572,550`.
- Breaking the dissipation breaks the inference → **one process. PASS.**

### G5 — INTEGER-NATIVE + DEFAULT-OFF byte-identity
- **Zero** non-integer writes to any in-frame cell/control attr across the
  trajectory (`val`, `obs`, `par`, `lam`, `phase`, `sign`, `enabled` all integer).
  The only floats are the cross-frame map: the real linear-solve MAP and the
  normalised ratios; even the Gibbs energy `E` is computed as an exact Python int.
- The seed is opt-in and **referenced by no default loader** (its node types
  `FieldCell`/`RelaxField` appear in no other graph); with it absent every existing
  path is byte-identical. **PASS.**

## Discipline ledger

- **Prereg committed ALONE** before any implementation/number (`dcd212bbdc`);
  seed-claim 197000–197999 CLEAN (verbatim in prereg).
- **Engine canonical `793ce09e…` UNTOUCHED** before and after (verified md5); NO
  Rust added; `term.rs` diff EMPTY; source_match — worktree Rust source byte-
  identical to the shared canonical build (`git diff … -- '*.rs'` empty).
- **Oracle `bash scripts/rung7_vision_bench.sh` BEFORE == AFTER: 214 passed / 10
  skipped / 0 failed** (data-less worktree baseline), unchanged by this rung.
- Measure module is **IMPORT-INERT** (all work inside `main()`/scoped functions; no
  module-level shared-state mutation).
- Gate `tests/test_dissipation_inference_migrated.py` 5/5; staleness_decay 7/7 +
  held_surface 3/3 green alongside (15/15) — no regression on the neighbouring seeds.

## Honest scope

This proves the identity on ONE dynamics, rigorously — the settlement/dissipation
⇔ MAP-inference identity, integer-native, with a working break-one-breaks-both
falsifier. It does **not** prove all cognition is physics; that is the program, and
this is its anchor. The falsifier is real: had the anti-dissipative run left the
recovery intact, the two frames would have been two processes and the identity
would have failed as stated. It did not — forcing the free energy uphill destroyed
the percept, byte-for-byte on the same rule.
