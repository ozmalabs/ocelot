# H2 RESOLUTION — RESULTS

Answers `H2_RESOLUTION_PREREG.md` (the contract). The prereg is committed above
the MEASUREMENT GATE; nothing in it was edited once numbers existed. This
document reports the swept grid, the H2a/H2b/H2c verdicts, and an honest
statement of what a direction-aware PROXY can and cannot establish about the
sealed board.

**RAW_UNRANKABLE.** Every number below is on `make_realized_text_aware`, a
direction-SENSITIVE PROXY — the symmetric common-factor co-movement of the
Phase-2 proxy with a gold-direction nudge layered on a `p_signal` fraction of
signalled cells. It is NOT the sealed organizer outcome. These are relative,
direction-aware calibration instruments, not a board score.

---

## What was fixed (the instrument, not the mechanism)

The original `induced_belief/measure_h2.py` returned NEUTRAL (KS worse by
+0.0032). The prereg's diagnosis — that this was an **instrument artifact**, not
a result — is borne out by the code and is now demonstrated:

1. **Random shift direction.** `measure_h2.py`'s `unit_dir(name, dir_seed)` is a
   coin flip on a hash, averaged over 8 random assignments. Both arms shift in an
   arbitrary direction; the test measured "random-direction shift of magnitude A
   vs B," never "correctly-directed shift." (The intact file still reproduces its
   original null: run on 2 F3 units it reports KS delta +0.0266, NEUTRAL-OR-BETTER
   = False — left byte-unchanged as the record.)
2. **Direction-agnostic realized proxy.** `run_variogram_eval.make_realized` is a
   symmetric common-factor draw with no relation to any text signal, so a
   correctly-directed shift earned nothing.

The fix, exactly as preregistered:

- **`run_variogram_eval.make_realized_text_aware`** — a *sibling* of
  `make_realized` (`make_realized` is byte-unchanged; `run_variogram_eval` and
  `measure_h2.py` still run, verified). For a `p_signal` fraction of signalled
  cells with a known gold direction, it nudges the realized outcome in that gold
  direction by effect size `e` (in cell-σ) **on top of** the same common-factor
  co-movement. Cells with no signal, and a `1 − p_signal` fraction of signalled
  cells (the typer's error/abstain rate), keep the UNCHANGED symmetric proxy.
  Deterministic given seed (the signalled-cell selection uses a seed-derived RNG
  distinct from the proxy draw RNG; `p_signal=0` is byte-identical to
  `make_realized`, verified).
- **Real per-cell direction + grounding_weight from the arm.**
  `measure_h2_directed.py` boots the induced-belief arm once and runs
  `arm.decode_utterance` on each unit's **real corpus text**. The per-cell shift
  direction is the arm's OWN decoded `direction`; the graded magnitude is the
  arm's OWN `shift` (= `direction × grounding_weight`). Python reads these values
  off the graph decode — it invents no direction and takes no decision over graph
  state (CLAUDE.md). The gold direction the proxy nudges toward is that SAME
  arm-decoded direction, so the proxy correlates with the text only where the
  corpus carries a real, correctly-typed signal.

### The scored path applies the graded per-cell shift (confirmed)

`cell_shift_grid` sets the per-cell shift (in cell-σ) for each arm from the
arm's decode:

| arm | per-cell shift | source |
|---|---|---|
| `no_shift` | `0` | — |
| `flat_0.1sigma` | `sign × 0.1σ` | `sign` = arm's decoded direction |
| `grounding_weighted` | `0.1σ × arm.shift` = `0.1σ × sign × grounding_weight` | arm's **graded** graph-produced `shift` |

Verified directly: for the bear-flattener unit (dir=up, grounding_weight=0.333),
`grounding_weighted[cell] = 0.0333` while `flat[cell] = 0.1` — i.e. the graded
arm shift, `flat × grounding_weight`, **not a flat constant**. Arms 2 and 3
differ ONLY in magnitude policy; direction is held correct for both, via the same
`apply_band_shift` contract-preserving per-cell additive discipline (generalized
to a per-cell vector in `apply_band_shift_percell`, byte-identical formula:
`samples + shift_sigma_cell × per-cell-std`).

---

## The arm's decode over the 22 F3 units (graph-native)

`arm.decode_utterance` on each unit's real corpus (FOMC statements/minutes,
Beige Book, CPI releases, in `corpus_index` order):

- **12 / 22 units carry a non-zero decoded direction** (10 up, 2 down); grounded
  chain reached a SensorAnchor at hops=3, grounding_weight=0.333.
- **10 / 22 decode `direction=none`** (no frame hit reached an anchor) → zero
  shift. This is real arm behaviour on those corpora, not a fabricated abstain;
  it is the "silence, not error" discipline in action and it is why the arm does
  not hurt the no-signal units (see H2c).

up: bear-flattener, conundrum-joint, cpi-shock-cross, dollar-vortex, dots-vs-oil,
funding-flip, hiking-year-curve, oil-fx-split, rates-into-factors,
term-premium-steepener. down: divergence, vaccine-rotation. none: boj-ust-channel,
brexit-joint, covid-curve, dollar-squeeze, election-2024-joint, fragile-five-joint,
inversion-persistence, safe-haven-paradox, scandies-stress, taper-steepener.

---

## The swept grid (RAW_UNRANKABLE)

22 F3 units × realized seeds 0–7 × `n_draws=1000`, `realized-mode=signed`,
`flat_shift=0.1σ`. Composite / marginal / tail / KS per arm. Lower is better for
composite, marginal, tail, and KS. Deterministic (re-run reproduces to 5 d.p.).

| p_signal | e | no_shift (comp/marg/tail/KS) | flat_0.1σ | grounding_weighted |
|---|---|---|---|---|
| 0.0 | 0.5 | 1.60513 / 0.2567 / 0.23692 / 0.1933 | 1.60621 / 0.2570 / 0.24024 / 0.1857 | 1.60521 / 0.2565 / 0.23813 / 0.1923 |
| 0.0 | 1.0 | 1.60513 / 0.2567 / 0.23692 / 0.1933 | 1.60621 / 0.2570 / 0.24024 / 0.1857 | 1.60521 / 0.2565 / 0.23813 / 0.1923 |
| 0.3 | 0.5 | 1.60195 / 0.2566 / 0.23482 / 0.2043 | 1.60209 / 0.2560 / 0.23643 / 0.1952 | 1.60163 / 0.2561 / 0.23503 / 0.1988 |
| 0.3 | 1.0 | 1.65298 / 0.2636 / 0.23987 / 0.2086 | 1.65244 / 0.2622 / 0.24065 / 0.2003 | 1.65261 / 0.2629 / 0.24070 / 0.2052 |
| 0.5 | 0.5 | 1.62538 / 0.2583 / 0.23205 / 0.2085 | 1.62507 / 0.2570 / 0.23380 / 0.1984 | 1.62490 / 0.2576 / 0.23225 / 0.2036 |
| 0.5 | 1.0 | 1.71312 / 0.2720 / 0.24064 / 0.2156 | 1.71132 / 0.2691 / 0.24015 / 0.2075 | 1.71242 / 0.2708 / 0.24148 / 0.2115 |
| 0.7 | 0.5 | 1.66915 / 0.2612 / 0.23166 / 0.2172 | 1.66848 / 0.2594 / 0.23281 / 0.2027 | 1.66858 / 0.2603 / 0.23187 / 0.2122 |
| 0.7 | 1.0 | 1.78062 / 0.2806 / 0.24430 / 0.2326 | 1.77816 / 0.2768 / 0.24321 / 0.2221 | 1.77974 / 0.2790 / 0.24513 / 0.2326 |

(The `p_signal=0` rows are identical across `e` by construction — with no gold
nudge the proxy is the symmetric base regardless of `e`.)

---

## Hypotheses (pre-declared, falsifiable)

### H2a — helps under signal: **CONFIRMED**

`grounding_weighted` composite < `no_shift` composite in **6 / 6** signalled grid
cells (`p_signal ∈ {0.3,0.5,0.7} × e ∈ {0.5,1.0}`), at the arm's REAL per-cell
directions. Mean `gw − no_shift` composite = **−0.00055**; worst (least negative)
= **−0.00032**. Every signalled cell improves.

This is the headline the original instrument could not produce. A
correctly-directed grounding-weighted shift now converts into a composite gain on
a direction-aware proxy. **The original H2 NEUTRAL was an instrument artifact:**
with a symmetric proxy and a coin-flip direction the gain was structurally
invisible; give the instrument the ability to see direction and the gain appears
and is stable across the whole sweep. The ToM decode's direction (H1) does
convert to composite value when the outcome is direction-sensitive.

### H2b — grounding-weighting vs flat (the reopened question): **MIXED — flat wins on composite at strong effects; gw wins on tail and at modest effects**

Both arms are correctly directed; the only difference is magnitude policy. Win
criterion (pre-declared): composite(gw) ≤ composite(flat) AND tail(gw) ≤
tail(flat) + 5% tol. `grounding_weighted` satisfies BOTH in **2 / 6** cells.

Per-cell, `gw − flat`:

| p_signal | e | Δcomposite | Δtail | gw wins (both) |
|---|---|---|---|---|
| 0.3 | 0.5 | −0.000457 | −0.001402 | **yes** |
| 0.3 | 1.0 | +0.000168 | +0.000047 | no |
| 0.5 | 0.5 | −0.000176 | −0.001544 | **yes** |
| 0.5 | 1.0 | +0.001101 | +0.001326 | no |
| 0.7 | 0.5 | +0.000101 | −0.000947 | no (tail better, composite +1e-4) |
| 0.7 | 1.0 | +0.001576 | +0.001922 | no |

The structure is clean and interpretable, and it is a **real finding, reported as
found — not tuned to reverse:**

- **At modest effect (`e=0.5`)** grounding-weighting is composite-neutral-to-better
  and consistently **better on tail** (Δtail = −0.0014, −0.0015, −0.0009 across
  p_signal). The attenuated (0.1σ × 0.333) shift is a gentler band translation
  that does not over-extend the extreme quantiles, so tail coverage error is
  lower. This is the "grounding-weighting buys calibration" reading the prereg
  named.
- **At strong effect (`e=1.0`)** flat wins on composite (Δcomposite up to
  +0.0016) and on tail. When the realized signal is genuinely strong, the FULL
  0.1σ flat shift moves further toward the gold outcome; the grounding-weighted
  shift **under-shoots** because `grounding_weight=0.333` attenuates the
  magnitude regardless of how strong the outcome effect is. Grounding_weight
  encodes *the typer's confidence*, not *the effect size* — so when the two
  diverge (strong effect, moderate grounding) a flat shift at the typer's
  precision extracts more.

**Verdict on H2b (per the prereg's flat-wins branch):** grounding-weighting is
**calibration-neutral-to-positive but not a composite lever over a flat
correctly-directed shift** — on average across the sweep flat is marginally
better on composite (mean Δcomposite = +0.00039) while gw is marginally better on
tail (mean Δtail = −0.00010). Neither dominates. The prereg's pre-committed
reading applies: *a flat shift at the typer's precision is as good as grading it
on composite; grounding-weighting buys tail calibration, not composite.* We
report it and do not tune to reverse it.

### H2c — graceful under no signal: **CONFIRMED**

At `p_signal=0` (text carries nothing into the outcome), `|gw − no_shift|`
composite = **0.000082**, an order of magnitude below the mean signalled-cell
`|gain|` of **0.00055**. The poorly-/un-grounded reads shift ≈0 — and the 10
`direction=none` units contribute exactly zero — so the arm does not actively
hurt on empty text. This is the composite-level version of H3's shift-ratio
guard, and it holds by *attenuation* (grounding_weight → 0 on no-anchor reads),
not by a hard gate.

---

## What a direction-aware PROXY can and cannot establish about the sealed board

**Can establish (relative, direction-sensitive):**

- That the arm's decoded *direction* is forecast-relevant — a correctly-directed
  shift lowers composite when the outcome is direction-sensitive (H2a). This
  answers the exact question the instrument-blind original was built not to
  answer, and answers it in the affirmative.
- The *relative* ranking of magnitude policies (flat vs grounding-weighted) under
  a stated `p_signal`/`e` structure, swept, never hand-fit — including the
  crossover where flat overtakes gw as the effect strengthens (H2b), and the
  no-signal safety (H2c).

**Cannot establish (RAW_UNRANKABLE):**

- Any *absolute* board score, or that these composite deltas would survive
  against the **sealed organizer outcome**. The proxy's gold direction is, by
  construction, the arm's own decode — so the proxy is *sympathetic to the arm's
  direction typing by design*. It can show that IF the corpus-implied direction
  is the true direction (to degree `p_signal`, at effect `e`), the shift helps;
  it cannot certify that the corpus-implied direction *is* the sealed truth. That
  is exactly what a proxy cannot do and the sealed board can.
- The true `p_signal` and `e` of the real board. The sweep brackets a plausible
  range and the H2a/H2c verdicts hold across all of it, but the *magnitude* of
  the composite gain (~5e-4) and the H2b crossover point are proxy artifacts of
  the chosen `e` grid, not board quantities.

The deltas here are small in absolute terms (composite ~1.6–1.8, gains ~5e-4).
Per the standing CLAUDE.md rule (POWER THE GATE; deltas within ~3× the
per-episode step are not results), the H2b per-cell differences (~1e-4 to 1.5e-3)
are near the noise floor of an 8-seed proxy and should be read as *directional
structure* (e=0.5 favours gw-on-tail; e=1.0 favours flat-on-composite), not as
CI-separated wins. H2a's sign (gw < no_shift) is consistent 6/6 and is the robust
claim; H2b is a MIXED/near-tie; H2c is a robust order-of-magnitude gap.

---

## Localised conclusion (what this moves)

- **The typer types direction well AND that direction converts to composite gain
  on a direction-aware proxy (H2a).** The original H2 null does not survive a
  competent instrument; it was the instrument, not the mechanism. This reopens
  and *resolves in the affirmative* the "direction is worthless for composite"
  reading the instrument-blind null implied.
- **Grounding-weighting is not a composite lever over a flat correctly-directed
  shift (H2b, flat-wins branch).** Its value is tail calibration at modest effect
  and graceful attenuation on no signal (H2c) — i.e. the **H3 guard** (attenuate
  to ~0 on ungrounded), now confirmed at the composite level. The pre-committed
  guidance applies: *one could ship a flat shift at the typer's precision for
  composite and keep grounding_weight for the guard.* The remaining composite
  headroom is in the **shift magnitude/shape** (grounding_weight attenuates by
  confidence, not by effect size, so it under-shoots strong signals), localising
  the next work to the shift transform, not the ToM decode.

## Reproduce

```
PYTHONPATH=runners/dsl/python:.bigtmp/track2 .bigtmp/t2venv/bin/python \
  drafts/seldon_t2_text/induced_belief/measure_h2_directed.py \
  --units .bigtmp/track2/units --select t2-F3 \
  --realized-seeds 0,1,2,3,4,5,6,7 --n-draws 1000 \
  --p-signals 0.0,0.3,0.5,0.7 --effects 0.5,1.0 \
  --json-out drafts/seldon_t2_text/induced_belief/h2_directed_results.json
```

Artifacts: `measure_h2_directed.py` (new), `make_realized_text_aware`
(sibling in `run_variogram_eval.py`; `make_realized` byte-unchanged),
`induced_belief/h2_directed_results.json` (full grid). The instrument-blind
`induced_belief/measure_h2.py` is left INTACT as the record of the original null.


---

## FOLLOW-UP — H2b powered to 64 seeds (`H2B_POWER_RESULTS.md`)

The H2b MIXED/near-tie above was flagged as underpowered at 8 seeds. It has now
been powered to **64 seeds** with paired per-seed CIs (`H2B_POWER_PREREG.md` /
`H2B_POWER_RESULTS.md`, `measure_h2b_power.py`). The resolution:

- **Composite: flat-wins, CI-separated in 6/6 signalled cells.** The two 8-seed
  cells where `grounding_weighted` appeared to win on composite (p0.3_e0.5,
  p0.5_e0.5, deltas −0.00046/−0.00018) **flip sign and CI-separate the other
  way** under power (+0.00031 [+0.00001,+0.00060] and +0.00054
  [+0.00026,+0.00083]) — they were sampling noise.
- **Tail: genuine tie.** Every tail-delta CI straddles 0; the 8-seed "gw better
  on tail at e=0.5" does not survive power, and the e-crossover dissolves.

**Verdict CONFIRMED under power:** grounding-weighting is neither a composite
lever nor a tail lever over a flat correctly-directed shift — ship flat for
composite, keep `grounding_weight` only for the H3/H2c guard. The remaining
composite headroom is the shift magnitude/shape (gw under-shoots because it
scales by confidence, not effect size), orthogonal to the grade-vs-flat question
now closed. The 8-seed MIXED was the instrument, not the mechanism.

**Item-2 extension (grounding-weight RANGE, in `H2B_POWER_RESULTS.md`):** the
64-seed run above used the arm's decoded `grounding_weight`, which is a CONSTANT
0.333 in this harness (all 12 signalled units, hops=3, saturated marginal). To
rule out that the near-tie was an artifact of that pin, `measure_h2b_gwrange.py`
swept the gw magnitude as `flat × w` over `w ∈ {0.2..1.0}` (global) and a
signal-TRACKING per-unit weight spanning [0.2,1.0]. Result: **flat-robust** —
`mean d_comp(w)` is monotone and asymptotes to 0 from above (flat's advantage
shrinks only because the graded arm converges to flat at w=1.0); no w or
tracking assignment CI-beats flat in a majority of cells (only 1/36 global cells
separate gw<flat). Within `flat×[0,1]`, **flat (w=1) is composite-optimal** and
any attenuation strictly costs composite on this proxy. The grade-vs-flat
question is closed in both the fixed-gw and full-range senses; the only remaining
lever is a shift that scales by ESTIMATED EFFECT (outside `flat×[0,1]`),
orthogonal to grading.
