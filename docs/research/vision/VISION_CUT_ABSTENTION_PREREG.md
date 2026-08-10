# GRAPH-RESIDENT ABSTENTION ON A DISCONTINUED PRIOR — PRE-REGISTRATION

*Written and committed BEFORE any headline number, per protocol §3.*

**Branch:** `worktree-agent-a93c4d00f89b45c4c` (the worktree was provisioned under
an auto-generated name; the intended name was `gamma-substrate/cut-abstention`).
**Branch base:** `212212e30b767466eca100f80e023f22365bd8d9`.

**Engine (§10):** `25fa11652e83` @
`runners/dsl/python/substrate_rs/_native.abi3.so` — a **shared build from the
canonical tree, Rust source verified byte-identical** (`shared` verdict).
**This rung adds NO Rust, NO Term and NO constant to the engine.**
`scripts/engine_build.sh` is therefore not run;
`tests/test_engine_provenance_migrated.py` was run **as its own step before any
number**: **7 passed, exit 0**. The oracle
`bash scripts/rung7_vision_bench.sh` was run at the branch base with `data/`
symlinked: **222 passed, exit 0** (147.8 s).

**Seed block: 73000–73999.** A concurrent rung holds 72000–72999; no seed
outside 73000–73999 will be drawn by this rung.

**Corpora reproduce exactly.** The committed motion statistic of
`results/verdict_comparator_video.json` was regenerated from Jellyfin with the
committed constants (n=150, every=2, start_s=300, size=24, episode_index C1=0 /
C2=3) before anything else was done: C1 max `52.34345685659597`, C2 max
`57.8950993584262` — **identical to the last digit on both corpora**.

---

## 1. THE DEFECT THIS AIMS AT, AND WHY IT IS A CLIFF

Three landed results converge on one mechanism.

`VISION_SALIENCE_RESCORE_RESULTS.md` §4: at Δ=1 misidentification is **not a
region property, it is a FRAME event**. All 31 of C1/Q0's Δ=1 errors fall in
**2 base frames of 50**, in which **every one of 16 regions failed at once**;
per-frame error count tracks per-frame motion at **r = +0.987**; **100%** of
those errors sit in the top-10% motion frames.

`VISION_VERDICT_RESULTS.md` §3.1: an **Otsu** split of per-step motion — a
threshold with **no free parameter** — names C1 cut bases **[34, 47]**, exactly
the two frames the salience rung found by error concentration. Two unrelated
methods, one answer.

`VISION_VERDICT_RESULTS.md` §5.1: across a cut the winning arm V2 is
**confidently wrong on 99.4% of C2 cut trials and abstains on NONE of them**.
V3 refuses **12× more often on cut trials than non-cut** — but that is
**0.1000 on C2 and 0.1363 on C1**, so ~87% of cut trials still get a confident
answer.

`VISION_REDUNDANCY_RESULTS.md` ARM 4: **observability 0/2, marker inventory
EMPTY in all 26 runs including baseline** — there is no vocabulary in this
system for recording that a fallback occurred.

**Abstention is what converts a cliff into a degradation.** The claim under test
is that the system can decide, from graph state it holds, that its
frame-to-frame prior has been discontinued, and decline — leaving a trace.

## 2. HYPOTHESIS (two-sided)

**H1.** A rule reading graph state can detect that the frame-to-frame prior has
been invalidated, and abstain, with a threshold that FALLS OUT of the
observation's own distribution rather than being set.

**H0 / the null that would be a complete result:** V3's existing measured-floor
refusal (`vd_refuse`) already covers the cut stratum, and an explicit rule adds
nothing measurable. **This would be reported as loudly as a success.** The
published V3 cut-refusal rates (0.1000 / 0.1363) make this unlikely but they are
rates over a stratum, not a per-probe increment, and the per-probe increment has
never been measured.

**H2 (the arm that matters, and where I predict FAILURE).** A magnitude-based
statistic cannot distinguish *discontinuity* from *large continuous change*. A
fast rigid pan has no discontinuity and an arbitrarily large frame difference.
If the rule abstains there, it has bought safety by refusing to work.

**H3 (the sharpest thing I expect to find, and it is an indictment of the
method I am using).** **Otsu has no free parameter, but it also has no null
hypothesis.** It returns a split on *any* distribution, including one with no
cut in it at all. A parameter-free threshold is not the same as a *calibrated*
one, and this has never been tested in this arc even though Otsu has now been
used twice.

## 3. THE MECHANISM — every decision is a rule

New seed `seeds/vision_cut_abstention.json`, loaded explicitly by this rung's
runner, **shipping OFF** (`CutParams.armed` is the empty string, matching no
arm) and **not in the default boot set**, per §9. Depends on
`vision_verdict_comparator`.

The adapter's only new work is **mechanical ingest**: one `VidFrame` node per
decoded frame carrying `vals` (flat row-major grey), `rows` (24 lists of 24) and
`cols` (its transpose); one `FrameStep` node per consecutive pair with
`from_frame` / `to_frame` edges; and one `spans` edge from each probe's
`ObsGroup` to each `FrameStep` in its own `[t, t+Δ)` interval — an interval the
runner already knows because it constructed the probe. **No conditional over
graph state, no motion computed in Python, no threshold in Python.**

**Rule 1 — `ca_step_mag` (PRIMARY statistic).** Per `FrameStep`,

```
mag = Sum(TemporalDiff(from.vals, to.vals), d -> Abs(d)) / Count(TemporalDiff(...))
```

i.e. **mean |Δ| per pixel, computed by the graph** with the existing
`TemporalDiff` Term. This is by construction the identical statistic the
verdict rung computed in numpy (`np.mean(np.abs(frames[t+1]-frames[t]))`), so
the graph's value is checkable against it.

**Rule 1S — `ca_step_res` (SECONDARY statistic S1).** Per `FrameStep`,

```
mag = 1 - Max( XCorrPeak(from.rows, to.rows), XCorrPeak(from.cols, to.cols) )
```

the unexplained fraction after the best axis-aligned shift, using the existing
`XCorrPeak` Term (a ±8-lag peak-NCC sweep over the row index; applied to the
transpose it sweeps columns). **This is the statistic that could in principle
separate a pan from a cut**, because a pan IS a shift and a cut is not.
Declared now, unconditionally, and reported either way — it is not a rescue
held in reserve for a failed primary.

**Rule 2 — `ca_otsu` (THE THRESHOLD, AND IT FALLS OUT).**

```
cut_threshold = mag of Argmax over FrameStep of  (s0*n1 - s1*n0)^2 / (n0*n1)
```

where `n0/s0` are the count and sum of `mag` over steps with `mag <= c.mag` and
`n1/s1` over `mag > c.mag`. That expression is Otsu's between-class variance
`w0*w1*(m0-m1)^2` rescaled by `N^2` — **the same argmax, in one division**. The
threshold is not a number in the seed; it is **the `mag` of a step the graph
picked**, i.e. a value the data supplied. Guarded to `n1 > 0`. **No numeric
threshold appears anywhere in the seed, and a gate asserts that.**

**Rule 3 — `ca_mark_cut`.** A `FrameStep` with `mag > cut_threshold` gets
`is_cut = 1`.

**Rule 4 — `ca_abstain` (THE DECISION).** An `ObsGroup` that has reached
`vd_final` (so `vd_refuse` has already had its say) and `Exists` a `spans`
neighbour with `is_cut = 1` gets `vd_answer = "refused"`.

**THE ABSTENTION IS RECORDED (the observability defect).** Rule 4 also mints a
node via `add_node_if_absent`:

```
Refusal { reason: "prior_invalidated", statistic: <mag|xcorr>, group: <key> }
```

with an edge `grp -refused_by-> Refusal`, and sets `grp.abstain_reason`.
`add_node_if_absent` dedups on the attrs, so exactly one `Refusal` is minted per
group and the fixpoint terminates.

**What reads it, stated in advance so this is not a marker nobody consumes:**
(a) the adapter's `read()`, which emits `abstain_reason` and `n_refusal_nodes`
per row; (b) `scripts/redundancy_observability.py`'s marker inventory
**unchanged** — its `MARKER_RE` is
`unresolved|gap|refus|ambig|residual|stale|fallback|missing|degrad|absent|unknown`,
which matches the node type `Refusal`, the edge type `refused_by` and the
attribute value `refused`. **This rung will run that scanner's inventory logic
over its own final graph and report the count.** The redundancy rung's finding
was "there are none to fire"; the test here is whether this rung's graph makes
that scanner non-empty. A marker no existing reader consumes would be a
different kind of nothing, so the existing reader is the one used.

## 4. THE GATE IS A CONJUNCTION

Unit = **base frame**, n = 50, paired 95% t-CI with `t(0.975,49) = 2.0096` (the
incumbent's table, unchanged). **Per corpus. Never pooled** — cartoon and
live-action have now disagreed in SIGN four times in this arc.

The protected arm is **V3 (ncc)**, the only arm that passed the verdict rung's
gate. **V2 (ssdg)** is run as the contrast whose refusal is a proven dead
instrument.

**Ground truth is the OUTCOME, not the label.** Arm 1 and arm 2 are scored
against whether the protected comparator was **actually right or wrong on that
probe** (`true_is_max`), not against the motion label — otherwise the rule would
be graded against its own statistic. **The statistic is input-side (a property
of the frame pair, available before any comparison); the ground truth is the
comparator's realised error.** Stated as a bound rather than a boast: the
statistic and the comparator read the same grey pixels, so this is *not* the
strong independence the salience rung had with chroma. It is the weaker and
honest claim that the cut statistic is **not computed by the component whose
failure it predicts** — no codebook, no orbit, no Argmax over regions enters it.

| arm | population | statistic | passes iff |
|---|---|---|---|
| **1 ABSTAINS ON CUTS** | A1 probes where V3 is WRONG (`true_is_max == False`) | fraction refused | **CI-separated increase** over the V3 baseline, and ≥0.80 restricted to the catastrophic frames |
| **2a DOES NOT ABSTAIN ON HARD-BUT-CONTINUOUS** | A1 probes where V3 is RIGHT, restricted to the **top motion decile among non-cut steps** | fraction refused | **not CI-separated from the V3 baseline** |
| **2b DOES NOT ABSTAIN ON A FAST PAN** | synthetic rigid-translation sequence, v ∈ {1,2,4,8} px/step, **no discontinuity anywhere** | fraction of steps marked `is_cut` | **0.000 at every v** |
| **3 BYTE-IDENTITY OFF CUTS** | every probe whose span contains no cut step | full read-back row | **identical, field by field**, to the inert-seed baseline |
| **4 CUT-FREE CONTROL** | a sequence containing no discontinuity | fraction of steps marked `is_cut` | **0.000** |

Arms 2b and 4 are the ones I expect to fail. They are in the gate anyway,
because a rule that passes 1 and 3 and fails 2b and 4 is a rule that has learned
"large change" and not "broken prior", and that distinction is the whole claim.

**The velocity set {1,2,4,8} and the top-decile cut for arm 2a are named as
HAND-SET (§13).** They do not fall out of anything; they are a stress sweep and
a stratification, not fitted parameters, and no verdict is chosen from them
after the fact.

## 5. THE INCREMENT OVER V3's EXISTING REFUSAL

Three configurations, identical in every other respect, same seeds, same
substrate construction:

| cfg | seed loaded | armed |
|---|---|---|
| **B** | yes | `""` — inert |
| **P** | yes | `"mag"` — primary |
| **S1** | yes | `"xcorr"` — secondary |

**B is the V3 baseline including `vd_refuse`.** The reported increment is
`P − B` and `S1 − B`, paired per base frame, on each arm. B is additionally
checked against the published V3 rates (0.0083 / 0.1000 non-cut / cut on C2;
0.0056 / 0.1363 on C1) as a consistency check — **not** an identity check, since
this rung draws from a different seed block and therefore a different insertion
permutation and different noise draws.

## 6. n, AND WHY NO NEW POWER PILOT IS RUN

n = 50 base frames per corpus, **fixed in advance**, inherited unchanged from
the verdict rung so every number is directly comparable to
`VISION_VERDICT_RESULTS.md`. The relevant power was already established there:
paired per-frame differences on this design resolved effects of ±0.08 with
CI separation (V3−V2 cut refusal, +0.0838 [+0.0300, +0.1375]). **The standing
rule from the Omniglot arc — POWER THE GATE BEFORE THE ENDGAME — is respected
by inheriting a powered design, not by asserting that this one is powered.**

The bound this leaves, declared now: **the cut stratum is SMALL** (C1 50 of 150
probe cells, C2 30 of 150; at Δ=1, 16 of 800 C2 trials). Arm 1 at Δ=1 rests on
few frames, and any Δ=1 number will be reported with its n beside it.

## 7. MY PREDICTIONS, IN ADVANCE (§3.7)

1. **The in-graph Otsu reproduces the numpy Otsu's PARTITION exactly** on both
   corpora — the same 3 high steps, same set. The threshold *value* will differ
   (the seed's threshold is the lower endpoint; numpy's is the midpoint between
   consecutive distinct values), and the classification is unchanged by that.
2. **Arm 1 is largely FORCED and I say so before measuring.** The rule refuses
   every probe spanning a step it marked; the risked part is not "does it
   refuse" but **how much of V3's actual error it covers**. Predicted:
   restricted to the catastrophic frames, ≥0.80 (pass); pooled over all V3
   errors at Δ=1, **under 0.30**, because the salience rung established most
   Δ=1 errors at wide orbits are region-level distractor inflation and no
   frame-level statistic can see them.
3. **Arm 2a passes, and the pass is WEAK EVIDENCE, declared now.** Measured
   from the committed motion arrays before writing this: the largest non-cut
   step is **11.06 (C1)** and **4.46 (C2)**; the smallest cut step is **43.52
   (C1)** and **44.75 (C2)**. The corpora are separated by **4×–10×**, so a
   wide range of thresholds gives the same answer and arm 2a **cannot
   discriminate a good rule from a lucky one on this corpus**. That is why arm
   2b exists.
4. **Arm 2b FAILS for the primary statistic**, at v ≥ 4 px/step and possibly at
   v = 2. A rigid pan of 4 px on a 24-px frame produces a mean |Δ| comparable to
   a cut, and the primary statistic cannot tell them apart by construction.
5. **Arm 4 FAILS for the primary statistic.** Otsu will split a cut-free
   sequence anyway, marking its top steps as cuts. I predict a non-zero
   `is_cut` fraction on a sequence with no discontinuity in it.
6. **S1 (XCorrPeak) is two-sided and I am genuinely unsure.** The argument for:
   a pan is a shift and a cut is not, so the statistic is aimed at the right
   distinction. The argument against: `xcorr_peak` does **not** mean-centre, so
   it is cosine similarity on all-positive luminance, which saturates near 1 for
   any pair of natural frames and may have no usable dynamic range. If S1 passes
   arm 2b while passing arm 1, that is the finding of this rung. If it saturates,
   that is a measured property of an existing Term and is reported as such.
7. **Arm 3 is exact.** The rule writes only on groups spanning a marked step, so
   every other row must be identical field by field. I expect exact identity and
   will treat any difference as an instrument defect that blocks every number,
   not as a result.
8. **The marker inventory becomes non-empty** — at least `type:Refusal` and
   `val:vd_answer=refused` — under the redundancy rung's UNCHANGED scanner.
9. **The increment over V3 on cut trials is large** (V3 alone refuses ~10–14%;
   with the rule, ~100%), and **the increment on non-cut trials is exactly
   zero**. If instead B already refuses most cut trials, H0 holds and this rung
   reports the null.

## 8. WHAT THIS RUNG DOES NOT DO (§8, declared in advance)

- **Toy resolution.** 24×24 frames, 6×6 regions. Nothing here is a claim about
  video at any real resolution. The measured scale wall is untouched.
- **Nothing is learned.** No codebook growth, no training, no accumulation.
- **Two episodes.** Not a survey, and the two corpora are never pooled.
- **The statistic and the comparator share the same grey pixels** (§4). This is
  weaker independence than the salience rung's chroma argument, and it is stated
  as a bound, not defended as equivalent.
- **`is_cut` is a per-STEP mark and abstention is per-PROBE via `spans`.** A
  probe that straddles a cut is refused wholesale; there is no partial credit,
  no per-region abstention, and no attempt to answer the regions a cut did not
  affect.
- **No default moves.** The new seed ships inert and is not boot-loaded; no
  committed seed is edited; no Rust is touched. The oracle bench must still
  report 222 passed, exit 0 at the end.
- **The Δ=1 cut stratum is small** (§6) and every number from it carries its n.
