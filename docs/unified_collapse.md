# Unified collapse — the two arcs as ONE loop (discrete + continuous voice)

## (1) Verdict — ARE THE TWO ARCS NOW ONE LOOP?

**YES, for the recognition itself — with one honestly-named residual on the
*shuffle gate* (not on the collapse).** Voice-identity recognition runs through
the **identical core bytecode** (`run_collapse + manifold + evaluate`,
`sha256[:16] = 962c466b194bd3e1`) that drives the three discrete domains — **only
the DomainPlug is swapped**, with a **soft-agree kernel** supplied in place of the
hard symbol-equality the core falls back to. The speaker manifold **collapses
honestly onto the right speaker** as cues accumulate:

```
        domain |      agree |   H0.1->H0.9 |   ECE | rec-frac | gates
     sentences |     hard== |  3.91->0.00  | 0.018 |    0.19  | YYYY
       letters |     hard== |  7.73->0.19  | 0.021 |    0.59  | YYYY
   llvm_passes |     hard== |  2.14->0.11  | 0.022 |    0.31  | YYYY
         voice |  soft-kern |  2.01->0.36  | 0.142 |    0.49  | YYY.   <- continuous
```

- **Full-reveal speaker recognition: 28/31 = 0.903** (chance 1/8 = 0.125), through
  the same core.
- The voice manifold **collapses** (H 2.01 → 0.36 bits), is **calibrated**
  (ECE 0.142 < 0.15), and shows **cohort structure** (mean recognition-fraction
  0.49; 3/31 never become unique — the genuine colliders).
- The **one gate that does NOT pass for voice is `seq_driven`** — the cue-ORDER
  shuffle (next-cue top-1 1.07×, below the 1.3× bar). This is **not the collapse
  leaking** — it is the *prefix-order* assumption of the core's shuffle gate
  meeting an **unordered feature bundle**: a speaker's cues are not a sequential
  grammar, so destroying their *reveal order* barely changes next-cue
  anticipation. My own `collapse_core.md` predicted exactly this leak
  ("prefix→non-prefix boundary"). The **structure-appropriate control** —
  destroying the **cue↔speaker binding** — collapses recognition from **0.903 →
  0.000**, proving the collapse IS driven by real cue structure, not bookkeeping.

So: **arcs unified on the collapse/recognition/calibration/cohort/honesty axes;
the abstraction leaks only where it was predicted to — the sequential-ORDER gate
is the wrong control for a continuous unordered-cue domain, and the right control
(binding-destroyed) is decisive.**

Run: `python -m scripts.unified_collapse_run` → `/tmp/unified_full.log` (end
marker `===UNIFIED_END_MARKER rc=0===`; process pgrep-verified gone;
`UNIFIED_COLLAPSE_RUN_COMPLETED`).

---

## (2) The soft-agree extension I designed — and why backward-compat holds

The core's one load-bearing assumption (named in `collapse_core.md §5.1`):
*admissibility = symbol EQUALITY revealed left-to-right* — `c[i] == prefix[i]`,
broken at first mismatch. A continuous domain accumulates evidence that never
`==`-matches. So I **generalised the agree term to a metric kernel**, with hard
equality as the **exact special case**.

**The change (`scripts/collapse_engine.py`, +50/-11):**

1. A generic plug field `agree(cand_sym, prefix_sym) -> float in [0,1]` — *how
   well the partial evidence at this position agrees with the hypothesis.*
2. `manifold()` now sums `agree_fn(c[i], prefix[i])` over revealed positions
   instead of counting `==`. The break rule is preserved: `s <= 0.0` breaks the
   prefix.
   - **Discrete (`plug.agree = None`)**: the core uses `_hard_agree(a,b) = 1.0 if
     a==b else 0.0`. A `0.0` is a mismatch → **prefix break** → byte-identical to
     the old `c[i]==prefix[i]` loop. The 3 discrete domains pass `agree=None`.
   - **Continuous (voice)**: a Gaussian `exp(-½((cv-pv)/σ_d)²)` ∈ (0,1], **never
     0**, so it never breaks — it **accumulates soft evidence across every
     revealed cue**, which is precisely what a continuous domain needs.
   **One code path, the kernel swapped.** Symbol-equality is literally the hard
   special case of the metric kernel.
3. A second generic field `truth_of(target) -> pool_member` (default **identity**)
   so a held-out **probe** (the revealed continuous evidence) can have its ground
   truth be the matching **reference hypothesis** in the pool — probe ≠ its truth.
   For discrete domains identity holds (`truth = tgt`), unchanged.

**Why backward-compat holds — measured, not asserted.** With `agree=None`, the
new `manifold` reduces to the old one exactly (`_hard_agree` + break-on-0 ≡
`c[i]==prefix[i]` + break), and `truth_of=identity` ≡ the old `c == tgt`. The 3
discrete domains reproduce the **prior committed numbers byte-for-byte**:

```
                 prior (collapse_core.md)   now (unified run)
  sentences  H 3.91->0.00 ECE 0.018 rec 0.19 t1 2.0x   ==   3.91->0.00 0.018 0.19 2.00x  YYYY
  letters    H 7.73->0.19 ECE 0.021 rec 0.59 t1 1.8x   ==   7.73->0.19 0.021 0.59 1.80x  YYYY
  llvm       H 2.14->0.11 ECE 0.022 rec 0.31 t1 5.2x   ==   2.14->0.11 0.022 0.31 5.17x  YYYY
```

All three still pass all four gates (collapse, ECE, cohort, shuffle), unchanged.
The factoring stays domain-agnostic: the runner asserts the core's executable code
references **zero** domain terms — now including `voice`/`formant`/`f0`/`cue` — and
the assertion passes (the soft-agree lives entirely as a generic plug field).

---

## (3) Voice-identity through the same core — the numbers

**The mapping.** SPEAKERS = hypotheses (pool, 8 VCTK speakers, each a recovered
reference code). PROGRESSIVE EVIDENCE = a held-out probe utterance's recovered
cues `[logf0, oq, tilt, level, logF1, logF2, logF3, logB1, logB2, logB3]`, revealed
cue-by-cue in my chosen order (`logf0, level, F1, F2, F3, oq, tilt, B1, B2, B3` —
separating cues first). SOFT-AGREE = the Gaussian kernel on the per-dim
standardised cue distance. Codes recovered **read-only** via
`domain_gap.signal_full_vector` (no synthesis re-run, no voice/synth file touched).

**Collapse** (H over revealed fraction): 3.00 → 0.36 bits; truth-confidence
0.125 → 0.785; admissible set 8.0 → 1.8. The manifold concentrates as cues arrive.

**Calibration**: ECE = 0.142 (< 0.15, honest). Looser than the discrete domains
(0.018–0.022) — the high-confidence bin `[0.9,1.0)` over-predicts (mean 0.980,
hit 0.829) precisely because of the genuine colliders below. Calibrated, not
sharp — the honest signature of a domain with real data-collisions.

**Cohort / recognition-point**: mean rec-frac 0.49, median 0.40; **3/31 probes
never become unique** — the colliders that legitimately stay in a cohort.

**Shuffle (cue-ORDER) control**: next-cue top-1 REAL 0.561 / SHUF 0.523 = **1.07×**
(top-5 1.01×) — below the 1.3× gate. *This is the honest leak* (§5): cue order is
not a sequential grammar, so the order-shuffle is the wrong control here.

**Structure control (the right one)**: destroying the **cue↔speaker binding**
(shuffle each cue dim's values across speakers) collapses recognition **0.903 →
0.000**. The collapse is driven by **real cue structure**.

**Full-reveal recognition: 28/31 = 0.903** (chance 0.125). Confusions:
`p227→p226`, `p231→p233`, `p228→p225` — all **within-register neighbours** (the
real-formant overlap `domain_gap.md` documented).

---

## The p228-collision honesty payoff (4) — calibrated-LOW-confidence, NOT confident-wrong

The voice work's overlap reality is that the high-f0 speakers (p225/p228 and
neighbours) genuinely collide in cue-space. **Does the collapse core stay honestly
wide there, or does it spike to confident-wrong?** Per-speaker confidence:

```
  p232 conf 1.000   p227 0.999   p226 0.989   p231 0.993   p230 0.999   p233 0.994
  p225 conf 0.860  <- COLLIDER (lowest two)
  p228 conf 0.849  <- COLLIDER
```

The two genuine colliders carry the **lowest confidence**; cleanly-separated
speakers sit at ~1.0. Full-reveal manifold mass on the colliders:

```
  truth=p225 pred=p225 conf 0.685 H=1.38b  mass: p225 0.685, p228 0.137, p230 0.132  [honest-wide]
  truth=p228 pred=p225 conf 0.647 H=1.10b  mass: p225 0.647, p230 0.323             [honest-wide]
  truth=p228 pred=p228 conf 0.772 H=0.84b  mass: p228 0.772, p225 0.218             [honest-wide]
  ...vs cleanly-separated p232/p230: conf 1.000, H=0.00b
```

The single confident-wrong-direction case (`p228→p225` at 0.647) is the genuine
data-collision — and **even there the manifold keeps H ≈ 1.1 bits and spreads mass
over the two colliders** rather than spiking. Where the cues genuinely separate
(p232, p230) the manifold collapses to H = 0.00 b, conf 1.000. **The collapse is
honest on the data-collisions: it stays wide exactly where the cues genuinely
overlap, and razor-sharp where they separate.** This is the calibrated-low-
confidence behaviour the mandate asked for — the manifold spends no false
certainty on the colliders.

---

## (5) Donkey audit

**ALL PASS.** The voice score is **owned math**: a Gaussian kernel on standardised
cue distances; the per-dim σ are the population cue spread (a `std`, not a fit);
`seq_logprob` is a **flat prior** (uniform over speakers) so the **AGREE kernel
carries the entire manifold**. The audit recomputes one kernel value by hand
(`agree(self,self)=1.000`). The recovered cue codes come **read-only** from the
existing owned-DSP extractor (`signal_full_vector`: YIN f0, IAIF glottal inverse,
LPC formants/bandwidths, median over voiced frames). **NO LM, NO net, NO `.fit`,
NO gradient, NO loss, NO sweep, NO embedding.** The structure control destroys
cue↔speaker binding only (marginals preserved), so its collapse is structural.

`CortexLoop/solve_for_n.py` **untouched**. The voice/synth files
(`domain_gap.py`, `synth_formant_fix.py`, `voice_impression_48k.py`,
`domains/voice_impressionist.py`) **untouched** (git diff empty). Audio synthesis
**not re-run**. The discrete plugs and prior runner **unchanged**.

---

## Honest verdict — arcs unified, and where the abstraction leaked

**Unified.** The recognition that the voice arc ground on all night — *which
speaker is this?* — runs through the **same core bytecode** (sha256
`962c466b194bd3e1`) as sentences/letters/llvm-passes, with **only the plug
swapped** and a **soft-agree kernel** in place of hard symbol-equality. The
speaker manifold collapses (H 2.01→0.36), is calibrated (ECE 0.142), shows cohort
structure, recognises 28/31 = 90.3%, is driven by real cue structure (0.903 vs
0.000 binding-destroyed control), and is **honest on the collisions** (colliders
carry the lowest confidence, mass stays spread). Voice identity **IS the same
collapse loop.**

**Where it leaked — named, not hidden.** Exactly one of the four gates fails for
voice: `seq_driven` (cue-ORDER shuffle 1.07×). This is **the prefix→non-prefix
boundary** my own `collapse_core.md §5.2` flagged: a speaker's cues are an
**unordered feature bundle**, not a sequential grammar, so destroying their reveal
*order* barely affects next-cue anticipation — the cohort signal here is
prefix-anchored but the evidence is order-free. The collapse, calibration, cohort,
recognition, and structure-dependence are all genuine; what does not transfer is
the *order-sensitivity gate*, because there is no order to be sensitive to. The
structure-appropriate control (binding-destroyed, 0.903→0.000) is the right test
for this domain and is decisive. The remaining frontier is therefore the gate
design, not the loop: a continuous unordered-cue domain wants a binding/structure
shuffle in place of (or alongside) the sequential-order shuffle — the core's loop
itself already unifies the two arcs.

---

### Files

- `scripts/collapse_engine.py` — **MODIFIED** (+50/-11): the soft-agree kernel
  (`agree` plug field + `_hard_agree` default) and `truth_of` (probe→reference).
  Hard equality + identity are the special cases; discrete domains reproduce prior
  numbers byte-for-byte.
- `scripts/collapse_voice.py` — **NEW**: the voice-identity plug. Speakers =
  hypotheses; recovered cues = progressive evidence; Gaussian soft-agree; cue-order
  shuffle twin; read-only reuse of `domain_gap.signal_full_vector`.
- `scripts/unified_collapse_run.py` — **NEW**: runs all 4 domains through the one
  core, the same-bytecode proof, per-speaker recognition, the structure control,
  and the collision-honesty analysis.
- `docs/unified_collapse.md` — this report.
- `/tmp/unified_full.log` — full captured run (end marker present).

n flagged: voice n = 8 speakers / 31 held-out probes (small, as in the voice work);
the 0.903-vs-0.000 contrast and the collider-confidence ordering are the
load-bearing results; individual confusions wobble at this n.
