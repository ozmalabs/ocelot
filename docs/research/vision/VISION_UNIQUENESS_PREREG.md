# RUNG L1b — THE UNIQUENESS GATE for the SILENT-ARGMIN HAZARD — PRE-REGISTRATION

*Written and COMMITTED BEFORE the confirmatory run (§3). Base `main` HEAD **dedd71ca**
(`git merge-base --is-ancestor dedd71ca HEAD` verified). Branch
`gamma-substrate/vision-uniqueness-l1b`. Engine **`7d5f50c18673`** (shared build, Rust
source byte-identical — this rung adds NO Rust). Baseline vision bench measured on this
worktree BEFORE any file was added: **200 passed / 0 failed** with `data/` symlinked
(§10.2).*

This rung acts on the negative L1 found in its own mechanism
(`VISION_LIGHTING_L1_RESULTS.md`, §"THE NEGATIVE"): below `g≈0.06` recognition returns a
**confident wrong identity** (`refused=0` in every failing row) while **≥2 candidates lie
INSIDE the verdict bound** — the ambiguity is visible in the graph and `Argmin` resolves
it silently. It has **two parts**, and part A is reported even if part B fails.

---

## PART A — THE AUDIT (measurement, no build)

**Question, per already-merged codebook rung: does a regime exist where ≥2 candidates
fall inside the verdict bound and the `Argmin` picks silently?** For each rung the
stimulus that would expose it is CONSTRUCTED (small / degenerate / low-contrast).

Audited rungs: **T1 continuous-pose** (`cp_recognize`), **T2 category**
(`cat_recognize`), the **similarity / identity-untangling** path (`shape_decode_loop`),
**L1 lighting** (`l1_recognize`), plus two rungs the structural audit surfaced that were
not in the brief — **colour identity** (`ci_assign`) and **deformation**
(`df_recognize`).

The audit's per-rung verdict is EXPOSED / NOT EXPOSED / NOT APPLICABLE with the measured
numbers. **A rung found affected is a CORRECTION TO THE RECORD, not a failure of this
rung** (§7).

## PART B — THE GATE

**A UNIQUENESS GATE: recognition REFUSES when ≥2 candidates lie within the verdict
bound, instead of silently returning the `Argmin`.** Flag-gated **OFF by default** (§9),
in a **NEW additive seed** — **no committed seed file is edited** (§11.4), so §9 holds by
construction on the seed files as well as at the flag.

### Where the gate is built, and WHY NOT everywhere — decided from PART A, in advance

The gate is built on **L1** only. **This is a pre-registered scope decision forced by the
audit, not a retreat after a failure:** the count-within-bound predicate is only
meaningful where the admission bound is DISCRIMINATIVE. The audit measures that it is on
L1 (0 multi-candidate rows in the clean regime, 12/12 at the floor) and that it is
**near-vacuous on T1** (≥2 candidates in bound in 63/63 trials at BOTH the aliasing
resolution and the clean one), where the same gate would refuse T1's landed 63/63. T1 is
therefore reported EXPOSED-but-not-gateable-by-this-mechanism, and the margin instrument
it would need is **NAMED, NOT BUILT** (§5) — exactly as L1 named L1b rather than bolting
it on.

### The predicate — composition only, NO new Rust

```
ambiguous(R)  :=  Gte( Count( Filter( Neighbours(ref,'has_identity'), cand,
                                      Lte( resid(R,cand), 1.0 ) ) ), 2 )
```

`resid` is **`l1_recognize`'s own residual expression, term-for-term** (the per-channel
`Max` of `Abs(Minus(c_ch, Times([p_ch, Div(a_ch, pa_ch)])))`), and `1.0` is **L1's own
falls-out bound** — ONE lattice step (§13). **No new constant is introduced by this
rung**: the count `2` is not a threshold but the definition of "more than one", and the
bound is inherited unchanged. `Count`/`Filter`/`Lte`/`Gte`/`Neighbours` all pre-exist
(`runners/dsl/src/jsonio.rs:1148`, `:1149`, `:1094`, `:1102`; `term.rs:70`, `:71`).

**KNOWN TRAP, positive-controlled (process rule 4):** `Times` takes an `items` **LIST**;
an `a`/`b` form parses to an **EMPTY PRODUCT = 1**. The predicate uses `Times` three
times. The gate will be run with that defect INJECTED and must go RED.

---

## THE ARMS, with §13.1 ENTAILED vs RISKED declared IN ADVANCE

For every RISKED arm: **what input would make it fail, and is that input in range?**
(L1's arm D was declared risked while its stimulus range sat entirely above the failure
region and it passed 12/12 without being able to fail. That is not repeated here.)

| arm | statistic | prediction | ENTAILED / RISKED | **what input would make it FAIL — and is it in range?** |
|---|---|---|---|---|
| **A HAZARD REPRODUCED** *(the premise)* | flag OFF, `g ∈ {0.06,0.05,0.04}`: false identities and `refused` | **2 / 2 / 4 false, 0 refused** | **RISKED** | A build that refused, or was correct, at those gains kills the premise. **In range:** these are the three gains L1 measured as the floor; a fresh boot could disagree. |
| **B GATE REFUSES** | flag ON, same gains: false identities; `l1_status` on the failing rows | **0 false; `l1_ambiguous`** | **RISKED** | If the count expression does not reproduce `l1_recognize`'s admission set, the count reads `<2` on a failing row and the false identity SURVIVES. **In range:** `g=0.04` material `e` has **6 of 6** candidates in bound and `g=0.06` material `b` has exactly **2** — the 2-candidate row is the tightest possible test of the `Gte(...,2)` boundary and it is in the set. |
| **C NO REGRESSION** *(the §1.1 conjunction)* | flag ON, the 5 REAL gains L1 scored 60/60: correct identities, refusals | **60/60 correct, 0 refused** | **RISKED** | **A build that REFUSES EVERYTHING FAILS THIS ARM** — which is the point (process rule 5). The `Times` empty-product defect makes every residual `\|c−1\|`, moving the in-bound count off its true value and refusing the clean regime; so would `Gte(...,1)` instead of `2`. **In range:** the 60 rows are exactly L1's committed headline. |
| **D DISCRIMINATION exact-0** | flag ON, cross-material false identities at the real gains | **0** | **RISKED** | A gate that widened admission (wrong comparison sense in the `Filter`) would admit a cross-material identity. **In range** — but note §1.1: a refuse-everything build ALSO scores 0 here, which is why **C is the arm that bites** and D alone is not a gate. |
| **E NOISE floor** *(n=100, seeds **45340–45439**)* | flag ON: random fields minting or claiming | **0/100** | **RISKED** | A gate that mutated `l1_recognized` upward, or a seed that fired outside its guard, would claim on noise. **In range** — 100 fresh confirmatory seeds. |
| **F NOVEL-material floor** | flag ON: never-minted material force-matched | **0**, all refused | **RISKED** | A gate that cleared `l1_status` and left `l1_recognized` set would show a claim. **In range.** |
| **G AMBIGUITY COST** *(reported; PREDICTED IN ADVANCE, not a failure)* | flag ON, at the floor: correct identities retained | **0/12 at each of `g=0.06/0.05/0.04`** — ALL 12 rows refuse | **ENTAILED** (measured in the pilot: all 12 rows have ≥2 in bound) | — |
| **X OFF-DAY** (§9) | flag at default 0 | L1 **19/19**, T3 **27/27**, T1 continuous-pose, T2 category, sd orbit law **{2:1,3:2,4:2,6:2,12:4}** unmoved, bench **200/0** | **ENTAILED** | The seed is not boot-loaded and every rule is gated at `uniqueness>0.5` with the flag shipped at `0.0`; inertness is entailed by construction. Reported as consistency, **not banked** (a broken build fails it). |

**The declared cost, stated before the run (G):** at the resolution floor the gate refuses
**every** row, not only the wrong ones — because at `g≤0.06` all 12 rows have ≥2
candidates in bound. It trades **12 confident answers (10 right, 2 wrong) for 12 honest
refusals.** That is the price of the gate and it is predicted here, in advance, so that
finding it in the results is not a discovery and reporting it is not a rescue.

**What is RISKED, in one sentence:** that a count-within-bound predicate composed from
held Terms reproduces the recognizer's own admission set exactly enough to convert the
floor's confident wrong identities into refusals **WITHOUT** disturbing the clean
regime — the conjunction, not either half.

---

## SEEDS (ledger)

**TAKEN BY THIS RUNG: `45340–45439`** (arm E, the noise floor, n=100). Allocated but
**NOT** consumed: `45440–45999`, `45100–45199`. Every other arm is DETERMINISTIC (fixed
gains, fixed materials) and consumes no seed. The PART A audit was piloted entirely on
deterministic stimuli and already-burned territory — **no confirmatory seed was spent on
the pilot** (§3.3).

## BOUNDS (§8) — what this rung does NOT do

A uniqueness / refusal gate. **NOT a widening of any invariance class** — no gain, angle,
deformation or category that was refused before is recognized now; the gate can only ever
turn a claim into a refusal. Still the named frontier and NOT this rung: **L2**
spatially-varying illuminant, **L3** global illuminant inference, **L4** shadow-vs-
reflectance, multi-illuminant scenes. NEWLY NAMED and NOT BUILT: the **MARGIN**
instrument T1 would need (the count-within-bound predicate does not transfer where the
bound is near-vacuous), and a uniqueness gate for `ci_assign`, which has **no bound at
all** to count within. Inherited: the abstract cone-triple grain, the white-patch anchor
assumption, the intrinsic global-scale ambiguity.

## Decision rule

Part A stands on its own and is reported regardless. For part B the gate is claimed only
if **A reproduces AND B converts AND C does not regress AND D is exact-0 AND E/F hold at
the floor** — the conjunction. Any single failure is reported as a failure of the rung,
in place, with the measurement that forced it (§7). A null on B (the gate does not
convert) would mean the count-within-bound predicate does not reproduce the recognizer's
admission set, and would be reported as such rather than retuned (§5).
