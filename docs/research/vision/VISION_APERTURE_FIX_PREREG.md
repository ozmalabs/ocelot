# THE TRUNCATED APERTURE — pre-registration

**Committed BEFORE any measurement (§3).** Seed block **71000–71999**.
Engine `5b7eb7ff9ecd`, built with `scripts/engine_build.sh` in this worktree;
provenance gate run as its own step BEFORE this file was written (627 passed,
exit 0).

Branch `gamma-substrate/aperture-fix`, base `64a9641bcda7a7e8a00f7c9686e317054e4a69e4`.

---

## 0. The defect, stated precisely

`domains/invariant_comparator_world.py`:

```python
def pad_edge(frame, rho):        # pads by rho
def orbit_windows(qsrc_padded, origin, rho, region=REGION):
    rr, cc = r0 + rho + dr, c0 + rho + dc
    out.append((j, qsrc_padded[rr:rr + region, cc:cc + region]))
```

The slice is unchecked. numpy clips an out-of-range slice **silently**, so a
window that runs off the padded array returns FEWER than `region × region`
cells. `pad_edge(src, rho)` is only sufficient when the window origin is the
UNDISPLACED region origin; a probe presented at displacement `d` takes its
window at `origin + d`, and then the correct pad is `rho + |d|`, not `rho`.

The verdict rung (`domains/verdict_comparator_world.py`, merged `64a9641b`)
found this in its own confirmatory data because its verdict is a NORM and a
short window changes the number of terms. It fixed its own copy with (a) an
explicit `pad` parameter and (b) a loud `ValueError` on any non-`(region,
region)` window, and correctly did NOT touch the incumbent's copy.

**Why it hid:** `covered_count` is a SET OVERLAP. A short window simply
contributes fewer tuples; the graph and the outside reference both compute the
same wrong number over the same short window, so **score agreement stays
1.0000 while both are wrong.** The incumbent's central cross-check is blind to
this defect by construction.

## 1. What this rung does

1. Correct `orbit_windows` / `pad_edge` in `invariant_comparator_world.py` so
   every window is full-sized at every displacement, and a configuration that
   cannot be full-sized FAILS LOUDLY instead of returning a short array.
2. Gate it **array-by-array** (element-wise `np.array_equal` on the returned
   tiles), never by a summary statistic — a shape bug that produces a plausible
   scalar is exactly what got missed the first time.
3. Re-establish the "no-op at zero displacement" claim **independently**. It is
   inherited from the verdict rung and this arc has repeatedly found inherited
   correctness claims to be conditional.
4. Measure the **positional selection bias** the truncation induces.
5. Enumerate the blast radius explicitly.

**No Rust. No new Term. No seed change.** The change is confined to two
world-adapter functions (mechanical array slicing — no conditional over graph
state) and their call sites.

---

## 2. Hypotheses, two-sided, with predictions stated in advance

### H1 — THE FIX IS COMPLETE AND LOUD

*Statistic:* over an exhaustive enumeration of `(rho ∈ {0,1,2,3}) ×
(pad ∈ {rho, rho+d}) × (d ∈ {0,1,2,3,4,6}) × (all 16 region origins) ×
(all (2ρ+1)² shifts)` on a 24×24 source, the count of returned windows whose
shape is not exactly `(6, 6)`.

*Decision:* post-fix this count must be **0 for every configuration that is
padded sufficiently**, and every INSUFFICIENTLY padded configuration must
**raise `ValueError`** rather than return anything. Pre-fix the same
enumeration is expected to return short windows silently; that count is
reported as the defect's reachable surface.

*Prediction:* pre-fix, short windows appear for every `(d > 0, pad = rho)`
configuration at the trailing-edge origins (`r0` or `c0` = 18) once
`d + dr > rho`. Post-fix, zero silent truncations anywhere.

### H2 — THE d=0 NO-OP, RE-ESTABLISHED RATHER THAN CITED

*Statistic:* for every `(rho ∈ {0,1,2,3}) × (16 origins) × ((2ρ+1)² shifts)` on
24 declared sources at `d = 0, pad = rho`, `np.array_equal(post_fix_tile,
pre_fix_tile)` — the PRE-FIX function is retained verbatim in the test file as
a frozen reference implementation, so the comparison is against actual old
code, not a re-description of it.

*Decision:* **all** comparisons identical ⇒ the no-op holds and every landed
zero-displacement result stands unchanged. **Any** comparison differing ⇒ the
no-op is FALSE, the verdict rung's inherited claim is retracted, and every
landed d=0 number in both rungs enters the blast radius.

*Prediction:* identical. `pad` defaults to `rho`, and at `d = 0` the arithmetic
`r0 + pad + dr` is character-for-character the old expression. **Proviso that
would break it:** if the fix changed `pad_edge`'s padding amount rather than
only `orbit_windows`' index arithmetic, d=0 would move. The fix is therefore
constrained to leave `pad_edge` semantically unchanged.

### H3 — BLAST RADIUS: WHICH LANDED CALL SITES ACTUALLY TRIGGERED

*Statistic:* instrument the UNMODIFIED landed call paths
(`scripts/invariant_comparator_measure.py::run_cell` for C3, video and replay;
`tests/test_invariant_comparator_migrated.py::_present_shifted`) and count
every window they produce whose shape is not `(6, 6)`.

*Decision:* a call site with count 0 is **UNAFFECTED, by measurement** — and
the entry must name WHICH argument makes it unreachable, not merely report the
zero. A call site with count > 0 needs its result re-run; where the re-run is
cheap it is run here and reported before/after.

*Prediction, stated in advance:* **I predict the incumbent rung's landed
numbers are UNAFFECTED, and NOT for the "no-op at d=0" reason.** Reading the
call sites:

- **C3** displaces (`d ∈ {0,1,2,3,4,6}`, diagonal `(d,d)`) but its source is
  the FULL BSDS photo (321×481), with the 24×24 grid taken at the photo
  CENTRE (`ar = (h − 24)//2`). The window indices are ~150 from either border,
  so `pad_edge`'s padding is never the binding constraint — the photo's own
  margin is.
- **The video path** uses genuine 24×24 frames, where the padding IS the
  binding constraint — but every probe there is presented at offset `(0, 0)`.
- **replay** is a C3 subset.
- **The tests** use a 42×42 random source with the 24×24 grid centred
  (margin 9).

So the defect is **LATENT but never triggered** in the incumbent: C3 escapes on
source size, video escapes on zero displacement, tests escape on source size.
**Two-sided:** if the instrumentation finds any truncation, this prediction is
wrong, the affected C3 cells are re-run, and the horizon result is re-measured.

### H4 — THE POSITIONAL SELECTION BIAS (the question this rung exists to answer)

A truncated window compares FEWER cells, so under `covered_count` it has a
**lower ceiling and can never win** an argmax against a full-sized competitor.
That is not merely a wrong score — it is a **systematic bias in WHICH orbit
member and which codebook region is selected**, and it is **invisible to a
score-agreement check**, because the outside reference is computed over the
same truncated windows.

Measured in the configuration where truncation IS reachable — 24×24 source,
`pad = rho`, `d > 0`, i.e. the incumbent's latent case and the verdict rung's
actual one.

*Arms:* TRUNC (pre-fix arithmetic, `pad = rho`) vs FULL (post-fix, `pad =
rho + d`), on identical sources, identical codebooks, identical displacements.

*Statistics, all three reported SEPARATELY (§ the task's explicit instruction
to separate selection bias from score change):*

- **S1 — score change.** Mean `covered_count` at the winning member, TRUNC vs
  FULL, and the mean cell-count of the compared window (36 under FULL by
  construction).
- **S2 — SELECTION disagreement.** Fraction of trials where
  `argmax_region(TRUNC) ≠ argmax_region(FULL)`.
- **S3 — DIRECTIONAL selection bias.** Partition the 16 regions into
  **trailing-edge** (`r0 = 18` or `c0 = 18`; 7 of 16) and **interior** (9 of
  16). Statistic: `P(TRUNC selects an interior region | FULL selects a
  trailing-edge region)` minus `P(TRUNC selects a trailing-edge region | FULL
  selects an interior region)`. A positive value is bias TOWARD the interior.
  Also reported: per-region accuracy (`said == truth`) for trailing-edge vs
  interior regions under each arm, as a paired per-source difference with a
  95% t-CI.
- **S4 — the blindness demonstration.** Score agreement between the graph's
  `icg_max` and the outside reference `reference_choice`, computed under TRUNC.
  Predicted **1.0000** — i.e. the incumbent's own cross-check passes perfectly
  on data the fix proves wrong. This is the evidence for the claim that the
  defect is invisible to a set-overlap verdict.

*Unit of analysis:* the SOURCE (§4), never the trial. n = 40 independent 24×24
random fields, seeds **71100–71139**, plus the 24 BSDS centre crops as a
second, non-synthetic corpus. `rho = 2` (the measured knee), `d ∈ {1,2,3,4,6}`.
n fixed in advance; no sweep over rho.

*Prediction:* S2 > 0 and S3 > 0 — truncation biases selection toward interior
regions, because a trailing-edge probe's own window is the truncated one and
its ceiling drops below its interior competitors'. S4 = 1.0000 exactly.
**Two-sided:** S3 ≤ 0 (bias toward the edge, or none) is a real and reportable
outcome and would mean the ceiling argument is wrong — most plausibly because
a truncated window also has fewer tuples to MISS, so its overlap FRACTION can
rise even as its count falls.

### H5 — THE HORIZON RESULT

`VISION_INVARIANT_COMPARATOR_RESULTS.md`'s headline is that the translation
horizon moved **1 → 2 → 3** as ρ grew. If edge windows had been truncated, the
orbit's effective coverage at the boundary was smaller than declared and the
horizon measurement is in scope.

*Decision:* conditional on H3. If H3's count is 0 for the C3 path, the horizon
stands untouched **by measurement, not by argument**, and this rung says so
explicitly. If H3's count is > 0, the C3 arms at every `d > 0` are re-run
post-fix and the horizon is re-derived.

---

## 3. The two-sided gate

`tests/test_aperture_fix_migrated.py`. Both sides must be DEMONSTRATED:

- **IDENTICAL** — the d=0 path, array-by-array, against a frozen verbatim copy
  of the pre-fix function (H2). Plus: every landed call-site configuration
  produces byte-identical tiles pre- and post-fix (H3).
- **CHANGED** — the `d > 0, pad = rho` edge windows, where the fix must
  produce a `(6,6)` window where the old code produced a short one, and the new
  window must be shown to be the CORRECT one (element-wise equal to the window
  cut directly from a sufficiently-padded source) — not merely different.
- **LOUD** — an insufficiently-padded call must raise, and the gate must be
  positive-controlled: reverting the guard turns it RED.

A fix that changes nothing anywhere has not been applied; a fix that changes
everything has broken something.

## 4. Seeds

| Range | Use |
|---|---|
| 71000–71039 | H1/H2 declared sources (24 used) |
| 71040–71099 | H3 instrumentation sources |
| 71100–71139 | H4 synthetic corpus (40 sources) |
| 71140–71199 | H4 codebook insertion-order permutations |

Confirmatory seeds are used once. Nothing outside 71000–71999 is consumed.

## 5. What a null means

If H3 finds zero truncation in every landed call site AND H2 confirms the
d=0 no-op, then **this rung lands a latent-defect fix that corrects no landed
number** — and that is the full result, reported plainly as such. The
positional-bias measurement (H4) is then a characterisation of a defect that
was reachable but not reached, which is exactly the information needed to say
whether the verdict rung's own fix was necessary and whether any FUTURE caller
is at risk.

If H3 finds truncation in a landed call site, this rung issues a **correction
to the record**, which this arc has done before and which is better than a
quiet re-run.
