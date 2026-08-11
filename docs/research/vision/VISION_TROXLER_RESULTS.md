# TROXLER — RESULTS

*Pre-registration: `VISION_TROXLER_PREREG.md`, committed **`4e707ff6`,
2026-07-17T16:01:06+10:00**. The confirmatory run started **16:01:14+10:00**, eight
seconds later, and its log is timestamped against that commit. No confirmatory seed was
touched before the pre-registration existed.*

**Engine `366ce5f14eff`**, resolved to
`<worktree>/runners/dsl/python/substrate_rs/_native.abi3.so`;
`tests/test_engine_provenance_migrated.py` **7/7** — the loaded engine is a build of THIS
tree's Rust source (§10.1's invariant is CONTENT, not location).
**Base `80e706f5`** (rebased onto the rewritten main tip; the worktree was 5 behind, 0
ahead — a fast-forward, never a merge).
**This rung adds NO Rust, edits NO seed, and changes NO default.**

---

## THE HEADLINE

**The stabilised image FADES. The drifting one does NOT.** Seeds 15000–15007, n=8 fixed
in advance. `results/troxler_confirm.json`.

| seed | drift (A) | stabilised (B) | diff | alive_min A | alive_min B | stab_err | `mu_endo` |
|---|---|---|---|---|---|---|---|
| 15000 | 0.130935 | 0.000282 | +0.130653 | 0.625 | 1.000 | 0.0 | 0.147227 |
| 15001 | 0.138415 | 0.000212 | +0.138204 | 0.625 | 1.000 | 0.0 | 0.146276 |
| 15002 | 0.129485 | 0.000317 | +0.129168 | 0.625 | 1.000 | 0.0 | 0.145562 |
| 15003 | 0.146949 | 0.000289 | +0.146660 | 0.625 | 1.000 | 0.0 | 0.150174 |
| 15004 | 0.133262 | 0.000179 | +0.133083 | 0.625 | 1.000 | 0.0 | 0.149393 |
| 15005 | 0.135867 | 0.000019 | +0.135848 | 0.625 | 1.000 | 0.0 | 0.145581 |
| 15006 | 0.130777 | 0.000196 | +0.130581 | 0.625 | 1.000 | 0.0 | 0.142486 |
| 15007 | 0.126713 | 0.000326 | +0.126387 | 0.625 | 1.000 | 0.0 | 0.141803 |

- **drift** mean **0.134050** (sd 0.006375); **stabilised** mean **0.000227** (sd 0.000101)
- **paired diff** mean **0.133823**, 95% bootstrap CI **[0.130106, 0.138323]**
- **8/8 positive; exact two-sided sign test p = 0.007812**
- the stabilised arm retains **0.17%** of its own t=0 contrast; the drifting arm **80%**

**DECISION RULE (CONJUNCTIVE — §4; a mechanism must not pass by making itself inert):**

| criterion | result |
|---|---|
| p < 0.01 | **True** (0.007812) |
| arm B `alive_min` > 0.99 | **True** (1.0000) |
| arm B `max_stab_err` == 0 | **True** (0.000000e+00) |
| arm A `alive_min` > 0 | **True** (0.6250) |

⇒ **H1.** *(The sign test was declared in advance because the pilot showed the separation
is deterministic in sign; my implementation is checked against `scipy.binomtest` on
k=8,7,4,0 — exact agreement, including the two-sided 0/8 case.)*

**THE FADE IS TO THE SETPOINT, NOT TO ZERO — and that is the mechanism's own signature:**
`mean_resp(final) = 0.146063` vs `mu_endo = 0.146063`. **Equal to six decimals.** The
stabilised sheet ends **firing at exactly the setpoint each cell measured in itself**, and
uniform. The image is gone; the cells are not.

**DITCHBURN, NOT PARALYSIS:** arm B's eye is still walking (**253 distinct gaze cells**)
while its retinal image is frozen to `stab_err = 0.000000e+00`. Arm A's image moves
(`max_err = 8.074797e-01`).

### Is the drift arm's contrast STRUCTURE, or the ReLU floor? (descriptive, not pre-registered)

The pre-registration named this as **my least confident prediction**: arm A settles at
`alive ≈ 0.625`, so ~37% of cells sit at exactly 0, and an SD over a 37%-hard-zero sheet
could be measuring the **rectification boundary** rather than the image — the mirror image
of FM-1's dead-arm error. **Checked** (`scripts/troxler_structure_check.py`, burned seed
0, `corr(resp, lum)` across the 256 cells over the last 50 settled steps):

| arm | `corr(resp, lum)` | alive | contrast |
|---|---|---|---|
| **drift** | **+0.9890 ± 0.0006** | 0.632 | 0.130885 |
| **stabilised** | **+0.1247 ± 0.0002** | 1.000 | 0.000075 |

**The drift arm's response tracks the image on the retina at r = 0.989.** The hard-zero
floor is NOT what the SD is reading: "does not fade" is a claim about **structure**. The
stabilised arm has almost nothing left to correlate with — and its residual r=0.125 sits
on a contrast of 7.5e-5, i.e. the homeostat's convergence residue, which is image-shaped
because that is what it is cancelling.

**This check can only make the claim stricter and it is not a substitute for the
pre-registered primary** (§5: metric surgery is changing a measure to RESCUE a failure;
making one stricter against yourself is what §1 and §7 demand).

---

## §13.1 — COULD THIS MODEL HAVE PRODUCED THE OPPOSITE RESULT?

**The two arms have completely different epistemic status, and I said so before the run.**

**Arm B's fade is ARCHITECTURALLY FORCED — I claim NO credit for it.** A per-cell
homeostat on a static input MUST equalise every cell to μ. This is derivable from the
rule equations without running anything: `resp = max(x−θ,0)`, `θ += λ(xbar−μ)` ⇒ for
static `x_i`, `θ_i → x_i − μ` ⇒ `resp_i → μ` **for every i** ⇒ SD → 0. **No rule could
have failed to yield it.** Reporting "the stabilised image faded" as a discovery would be
**a tautology with error bars** — §13.1's disease, the same shape as the Engbert
crossover (one rule *solely responsible* for each half of the signature ⇒ assembled, not
derived).

**The confirmation that it is forced, not fitted:** the stabilised arm's fixed point is
`mean_resp = 0.144319` and `mu_endo = 0.144319` — **equal to six decimals**. The sheet
did not fade to *zero*; it faded to **exactly the setpoint each cell measured in itself**.
That is the equations' own answer, arrived at from the run.

**The falsifiable content is ENTIRELY in arm A, and it is the reason this test was worth
running.** *Does the drift's own timescale outrun adaptation?* No rule fixes this:

| timescale | measured | falls out of |
|---|---|---|
| **τ_drift** = retinal-image decorrelation to 1/e (adaptation FROZEN ⇒ pure image motion) | **3 steps** | **Engbert's self-avoiding walk** (α measured, never imported: 1.1553 / 0.7590) |
| **τ_adapt** = stabilised-arm contrast e-folding | **160 steps** | **λ, β** and the cell's **own measured `mu_endo`** |
| **separation** | **53.3×** | — |

**Neither number was chosen with the other in mind**, and they could have landed on the
same side of the boundary — in which case both arms fade and the wired drift is
quantitatively wrong (pre-reg §7 proviso 1, declared in advance as a reportable
negative). They did not. **Arm A could have failed. Arm B could not.**

The decorrelation measurement carries its own corroboration: `corr(resp(t), resp(0))` in
the drift arm **oscillates** — +0.707 at lag 1, **+0.004 at lag 3**, +0.998 at lag 5,
**−0.980 at lag 16**. That is a period-8 grating sliding under the retina, which is
exactly what a moving image on this scene must do, and it is not something a static or
decorative drift could produce.

**So: does the drift's timescale outrun adaptation?** **Yes, by 53×** — and that is the
honest answer to the question the brief posed, including its uncomfortable half:
**53× is a wide margin, not a delicate one.** The drift in this model moves ~1 receptor
per step. The biological question — whether a drift of *one-tenth* a receptor still
outruns adaptation — is **NOT tested here**, and the margin is reported precisely so that
nobody reads this as if it were.

**Is arm A the "one rule per half" disease?** No, and the distinction is the point. The
Engbert crossover had one rule *solely responsible* for each half of a QUALITATIVE
signature, so the model could not not produce it. Here the homeostat forces a fade on ANY
static input; whether drift makes the input non-static ENOUGH is a **quantitative race
between two independently-derived timescales**. Both outcomes were expressible, and one
of them would have been a negative.

---

## §6 — WHAT EACH ARM IS IN THE ANIMAL, AND WHETHER THE TWO MANIPULATIONS COINCIDE

**"Freeze the drift" is NOT "stabilise the image."** Ditchburn & Ginsborg 1952 / Riggs &
Ratliff 1952 / Yarbus stabilised the image *against* eye movement with a mirror on a
contact lens: **the eye keeps moving; the image follows it.** Freezing the gaze is
**paralysis** — a different manipulation.

| arm | `saw` | world | retina sees | in the animal |
|---|---|---|---|---|
| **A — DRIFT** | 1 | stationary | a MOVING image | a normal eye at fixation |
| **B — STABILISED** | **1 — the eye still moves** | re-painted at the eye's position each step | a STATIC image | **Ditchburn's mirror** |
| **C — FROZEN** | 0 | stationary | a STATIC image | **paralysis** |

**MEASURED, NOT ASSUMED** (`troxler_calibrate.py` PART A, burned seed 0, 400 steps,
FM-0's own statistic):

| attribute | `D(B,C) = max\|stabilised − frozen\|` |
|---|---|
| `lum` | **0.000000e+00** |
| `x` | **0.000000e+00** |
| `theta` | **0.000000e+00** |
| `resp` | **0.000000e+00** |

**They coincide EXACTLY** — the drift's only wired consumer is the sampling, so in THIS
model the two manipulations are the same experiment. The task asked me to verify this
rather than assume it, and the verification is a measurement with FM-0's statistic, not a
grep (§12.1: the ninth inert instrument was the supervisor's and it WAS a grep).

**⚠️ THIS IS A SCOPE LIMIT, NOT A CONVENIENCE (§8).** In the **animal** the two are NOT
the same: paralysis removes the eye's motion, stabilisation removes only the image's. The
animal's drift has consumers this model does not have. **This model cannot distinguish
paralysis from stabilisation**, and any future claim that it reproduces the *difference*
between them is unsupported. Arm B is what is reported, because it is the arm that
corresponds to Ditchburn.

**Where the stabilisation lives, and why it is not a rule.** Ditchburn's mirror is
**apparatus, not physiology**, so it lives in the WORLD. `add_world`'s docstring already
says the adapter "does NOT say which receptor sees which photon — that is
`ey_sample_at_gaze`'s decision", and `present_world` exists verbatim *"for a moving-scene
control"*. Arm B **is** that control: a scene whose motion equals the gaze's. The EYE is
byte-identical across all three arms but for `saw`, which is graph DATA on `EyeParams`
(§0). A RULE would put the mirror inside the eye and make the retina cancel its own gaze
— **efference copy / VOR, a different mechanism** that no stabilisation experiment
contains.

---

## §1 — ALL FIVE CLAUSES ON THE FADE MEASURE, FLOORS MEASURED IN-RUN

`contrast = SD over the 256 cells of resp`. Floors measured **in-run**, never inherited
(OSI's floor is init-dependent 0.0044 vs 0.3899 — **89×**).

| clause | check | result |
|---|---|---|
| **1. floor on structureless input** | a FLAT world — no contrast exists to represent | **contrast = 0.000000, alive = 1.0000** |
| **2. high on an ideal exemplar** | a binary maximal-contrast world | **contrast = 0.309482** (the experiment's own grating: 0.167349) |
| **3. stable against duration** | with the MECHANISM OFF (`frozen=1`, a REAL freeze) | **0.167349 → 0.167349 over 3200 steps (0.0000% drift)** |
| **4. ARMS ALIVE** | per arm, per timepoint | see the aliveness table below |
| **5. mechanism moves something downstream** | FM-0b, re-run by me | `D_lum` **0.807**, `D_x` **0.532**, `D_theta` **0.401**, `D_resp` **0.517** |

**Clause 3 needed care and I state the reasoning.** Troxler *is* a duration effect, so
"the score must not change with duration" cannot apply naively — it would forbid the
phenomenon. The honest form: **the READER must not fade on its own; the fade must be the
MECHANISM's.** With every adaptation rule gated (`frozen=1`) the measure is flat to
**0.0000%** across the full 3200 steps. Any fade seen with the mechanism ON is the
mechanism's.

**THE FLOOR IS REACHED BY UNIFORMITY, NOT BY DEATH** — the flat-world sheet scores 0.000000
while **100% alive**. That is exactly the distinction §1.1 says `SD(resp)` cannot make on
its own, and it is why aliveness is printed beside contrast at every timepoint.

**Reader positive control (a fade is an ABSENCE CLAIM):** with the mechanism off, the
reader **sees** the non-faded response that is there (contrast 0.167 > 0.1). The measure
can tell "not faded" from "faded".

**`peak/base` was NOT read** (unbounded; blown up in two independent rungs at 1.6×10⁶ and
7.1×10⁷).

---

## §1.1 — ALIVENESS, PER ARM, PER TIMEPOINT

**"Faded" and "was never alive" are the same reading**, and this arc has caught ten inert
instruments. FM-1 retracted its own headline fade window (t≈300–800) as dead-arm readings
once aliveness came back **10.5%**. Rung 8B passed all four pre-registered criteria on an
arm that fired at **0 of 12** orientations.

`alive(t) = frac(resp > 0)`, over all 256 cells, at EVERY one of the 3200 steps, for
EVERY seed:

| arm | alive at t=0 | **alive_min over ALL 3200 steps × 8 seeds** | alive at t=3200 |
|---|---|---|---|
| **A — DRIFT** | 1.0000 | **0.6250** | 0.6250 |
| **B — STABILISED** | 1.0000 | **1.0000** | **1.0000** |

**The stabilised arm is 100% alive at every timepoint of every seed — its aliveness never
drops at all.** Its fade is a sheet that is **firing and uniform**, not one that is
silent. **This is the single fact that makes the result a fade rather than a death**, and
it is why `mu_mode=1` was used: with GCAL's imported `μ=0.024` the sheet goes to **0%
aliveness for a window** (the setpoint rung's finding), and §1's fourth clause would have
failed on the arm before any fade could be read.

**The drift arm never falls below 62.5% alive**, and its response tracks the image at
r=0.989 (above) — so it is alive throughout, and alive *with structure*.

**Neither arm is ever silent. No arm scores its floor by death.**

---

## WHAT I GOT WRONG

**1. My worktree was based 5 commits behind, and two of the four files I was told to
verify DID NOT EXIST in it.** `scripts/fm0b_drift_wired_audit.py` and
`scripts/eye_setpoint_lib.py` were both absent. **A missing file in a wrongly-based tree
is indistinguishable from a file that never existed** — had I not checked the base first,
the honest-looking conclusion available to me was "the drift was never wired; FM-0 stands;
Troxler is untestable", which is FALSE and would have been reported with a straight face.
The tree was a strict ancestor (5 behind, **0 ahead**), so the fix was a fast-forward
rebase, never a merge — *"a merged branch off a rewritten base is not inert; it is a
loaded revert."*

**2. My first instinct on the engine was the fix §10.1 explicitly says was TRIED AND
REJECTED.** `substrate_rs._native` resolves to the **canonical tree's** `.so`, not my
worktree's, and I began to treat that as a stop-the-run defect. It is not: §10.1's
invariant is **CONTENT, not location** — *"a right-path binary can still be built from
wrong source; a shared binary from identical source is CORRECT"*, and asserting the
artifact lives in the current tree makes the gate unconditionally red in every worktree,
"which is a gate agents route around". The correct check is the one the provenance suite
already makes (7/7), plus verifying my tracked `runners/dsl/src` is byte-identical to
canonical's — it is; the only difference is an **untracked `py.rs.selfmod.bak`** in the
canonical tree, which cargo never compiles.

**3. I printed arm A's number under an arm B label — in the headline artifact.** The first
confirmatory run printed `arm B gaze still moving: 253 distinct cells` while reading the
`drift_gaze_distinct` field. **The claim it makes is the one that separates Ditchburn from
paralysis**, i.e. the entire §6 point of the rung, and I read it off the wrong arm. The
claim turned out TRUE — verified two ways afterwards: the arms' gaze trajectories are
identical (82 distinct / path 199.0 on both), and **no `ey_saw_*` rule reads
`lum`/`resp`/`x`/`theta`, so the walk is blind to the image** — but *"it happened to be
true"* is not a defence. The script now records `stab_gaze_distinct` off arm B and the run
was repeated; the primary statistics are byte-identical (see the reproduction check).
**This is exactly the disease this protocol keeps catching — a number read off a nearby
convenience rather than off the thing the claim is about** (the setpoint rung's `frame()`
vs `bursting` error, 6× in the flattering direction, is the same shape).

**4. §1's third clause cannot be applied naively here, and my first reading of it would
have forbidden the phenomenon.** "If the score changes with how long you trained on the
same input, the measure is duration-confounded" — but **Troxler IS a duration effect**, so
read literally the clause outlaws the experiment. The honest translation is: **the READER
must not fade on its own; the fade must be the MECHANISM's.** With every adaptation rule
gated (`frozen=1`) the measure is flat to 0.0000% over the full 3200 steps. I record the
reasoning rather than silently dropping the clause.

**5. I pinned my own §12.3 gate to a base sha, and it rotted within the hour.** See the
gates section: `80e706f5..HEAD` silently widened to include another rung's commit the
moment I rebased onto the advanced tip. I wrote that gate *while quoting the rule it
violates* — §12.3 says pin to the DIFF, and I pinned to a base, which is only the same
thing until someone else commits. Now pinned by commit identity and positive-controlled.
**The rule caught me one costume later than I expected**, which is what the protocol says
happens.

**6. I nearly used `frame=` in the arms, which would have raced the graph's own sampling.**
With `world_sample=1` the GRAPH decides which receptor sees which photon
(`ey_sample_at_gaze`); the adapter's legacy `present()` writes `lum` directly. Passing
both would have had the adapter and the rule writing the same attribute in one tick — the
adapter quietly overwriting the graph's decision. All arms pass `frame=None`.

---

## GATES, AND EVERY ONE POSITIVE-CONTROLLED (§12.3)

*"A gate you have only ever seen pass is not a gate you have tested."* Each gate had a
violation injected, was observed **RED**, the violation was reverted, and it was observed
**GREEN** again.

```
python -m pytest tests/test_troxler_migrated.py -q          ->  7 passed
python -m pytest tests/test_engine_provenance_migrated.py -q ->  7 passed
python scripts/fm0_vacuity_audit.py       -> VACUOUS      (§9: defaults reproduce)
python scripts/fm0b_drift_wired_audit.py  -> LOAD-BEARING (§1 clause 5)
```

| gate | injected violation | RED? | reverted → GREEN? |
|---|---|---|---|
| `test_the_mirror_stabilises_EXACTLY_...` | paint the world +0.01 off the stabilised image | ✔ *"the mirror did not stabilise the image"* | ✔ |
| `test_the_fade_measures_FLOOR_is_reached_by_UNIFORMITY_not_by_DEATH` | make the "flat" world structured | ✔ *"does not floor on a flat world"* | ✔ |
| `test_frozen_gaze_does_not_move_and_stabilised_gaze_does` | force `saw=1` in the frozen arm | ✔ *"saw=0 did not freeze the gaze"* | ✔ |
| `test_the_reader_can_SEE_a_non_faded_response` | make the "real freeze" fake (`frozen=0`) | ✔ *"the measure fades on its own with the mechanism OFF (0.0616)"* | ✔ |
| `test_defaults_preserve_committed_results` | flip `world_sample` default ON in the seed | ✔ *"world_sample must default OFF"* | ✔ (seed restored) |
| `test_this_rung_adds_NO_rust_and_edits_NO_seed` | re-point the range at `3fc83ec9` (the rung that added `PickUnique`) | ✔ *"this rung added Rust"* | ✔ |

### §12.3 — MY FIRST PIN WAS ROT-PRONE, AND IT ROTTED WITHIN THE HOUR

I pinned the no-Rust gate to `80e706f5..HEAD` — a **base sha**, which is what §12.3 warns
about in a different costume. **A base sha is not a pin: a rebase moves what sits above
it.** Main advanced by one commit (`f7c1e104`, the scale rung) while this rung's runs were
in flight, and the mandatory rebase onto the new tip meant `80e706f5..HEAD` **spanned that
other rung's commit**. The gate still passed — the scale rung added no Rust — so **it
would have gone on passing while silently testing the wrong diff**, and would have
**falsely accused this rung** the first time any neighbour touched `runners/`. That is
precisely how rung 8B's two self-restraint gates rotted the same day they were written.

**Fixed by pinning to IDENTITY, not to a base:** the gate resolves the Troxler rung's own
commits by subject (`^vision TROXLER`) and diffs **each against its own parent**.
Invariant under rebase and under any amount of concurrent work by other agents. Verified
to see **exactly this rung's 10 files** and nothing else.

**And the FIXED gate was positive-controlled**: aimed at the two-eyes rung — which
genuinely added `PickUnique` — it fires (*"this rung added Rust"*); reverted, it is green.
**A gate you have only ever seen pass is not a gate you have tested**, and that applies to
the fix as much as to the original.

**§12 — explicit test file lists, never `-k vision`** (it matches "pro**vision**al").
Nothing was staged with `git add -A`; no file over 10 MB; nothing under
`results/*_checkpoints/`. **The runners are COMMITTED** — rung 2's headline was permanently
lost because its runner never was.

---

## §9 — DEFAULTS PRESERVE COMMITTED RESULTS

**This rung changes NO default, NO seed, and NO Rust. It adds runners, gates and prose
only.** `world_sample` and `mu_mode` remain `0.0`, so `fm0_vacuity_audit.py` still reports
**VACUOUS** (`D = 0.000000e+00` exactly on lum/x/theta/resp at all 400 steps) — re-run and
verified on this engine. Every committed result reproduces.

The arms are **graph DATA** on the `EyeParams` singleton (`saw`, `world_sample`,
`mu_mode`, `calib`, `frozen`), never a Python code path (§0). `set_params` writes to the
singleton and `PickUnique` guards ambiguous reads — no second params node was introduced.

---

## REPRODUCTION CHECK

The confirmatory script was run **twice** on the same seeds — once as pre-registered, and
once after fixing the mislabelled arm-B diagnostic (item 3 above). The pipeline is
deterministic, so the primary statistics must be **byte-identical**. **Verified, not
assumed:**

| statistic | run 1 | run 2 | identical |
|---|---|---|---|
| `p` | 0.0078125 | 0.0078125 | ✔ |
| `sign_k` / `sign_n` | 8 / 8 | 8 / 8 | ✔ |
| `diff_mean` | 0.13382288511824758 | 0.13382288511824758 | ✔ |
| `verdict` | True | True | ✔ |
| **all per-seed primary fields** (contrast, diff, `mu_endo`, `stab_err`, aliveness) | — | — | **✔** |

**This is NOT a second test and no seed was re-burned** (§3.6 forbids re-running to get a
different answer; this re-ran identical deterministic code on the identical block and
got the identical numbers, which is a *reproduction*, not a *retry*). Run 2 additionally
records **`stab_gaze_distinct = 253`, path length 3199.0 over 3200 steps — read off ARM
B**, so the claim "arm B's eye is still moving" is now measured on arm B rather than
inferred from arm A. Arm A's value is also 253: **identical, because the walk is blind to
the image.**

---

## §8 — SCOPE: WHAT IS **NOT** SHOWN

- **This licences nothing about which biological mechanism is correct.** A homeostatic
  threshold is ONE candidate for Troxler; receptor adaptation, bipolar adaptation and
  synaptic depression are others. This result does not discriminate them.
- **The drift here moves ~1 receptor/step** — LARGE relative to the receptor lattice.
  Real fixational drift is a small fraction of it. The 53.3× margin is a win in a
  **COARSE-drift regime**, NOT in the delicate biological one where the margin is thin.
  **The margin, not just the sign, is the reportable quantity**, which is why it is
  measured rather than asserted.
- **The model cannot distinguish paralysis from stabilisation** (`D(B,C) == 0`).
- **`mu_endo` inherits rung 1's wave protocol** — free of a *constant*, not free of the
  ladder beneath it.
- **The commensurability wound is unhealed** (the setpoint rung's own): `mu_endo` averages
  a `{0,1}` burst alphabet while `resp` is graded. Nothing here tests that they are the
  same quantity. FM-2's binarisation finding is the same wound.
- **No claim about the TIME COURSE matching the animal's.** Troxler fading in humans takes
  seconds; "160 steps" is not calibrated to seconds, and no such mapping is attempted.
