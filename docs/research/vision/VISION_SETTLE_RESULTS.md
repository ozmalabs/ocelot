# THE CORTICAL SETTLING LOOP — RESULTS

**THE GRAPH ENGINE CAN EXPRESS THE SETTLING DYNAMICS AND CANNOT EXPRESS THE
SETTLING TERMINATION. The loop does NOT converge, the reason is a theorem rather
than a bug, and no seed was burned.**

Engine **`74fc035c8595`** @ `runners/dsl/python/substrate_rs/_native.abi3.so`,
**`shared` build — Rust source byte-identical to this tree** (this rung adds NO
Rust; legitimate under §10.1 rule 4). Base **`70cbbcb6`** (rebased, not merged —
my worktree was BEHIND main and lacked `scripts/waveiso_lib.py`). `data/`
symlinked from canonical (§10.2). Runner: `scripts/settle_lib.py`,
`domains/settle_world.py`, `seeds/vision_settle.json`.

**THIS IS ENGINEERING, NOT THE PARADIGM CLAIM.** A working V1 would be valuable
and NOT novel — GCAL already works. The paradigm question (can the substrate's
OWN dynamic-quantization loop grow vision?) is separately answered **NEGATIVE**
by the sd rung and **stays that way**; nothing here touches it.

**Seeds 21000–21999: ALLOCATED, BURNED NONE, still CLEAN.** The rung stopped at
the **§2 CONVERGENCE gate**, which is what rungs 5, 6, 8, 8B, 8C and 8D each
did. No arm was run, so no confirmatory seed was consumed.

---

## 1. THE HEADLINE

| question the brief posed | verdict |
|---|---|
| Can the rules **express** a settling loop? | **YES — and with NO new Rust.** `Fold`/`Neighbours`/`NodesOfType`/`Max`/`Div`/`Count` already exist. Three rules + one production. |
| Does the loop **converge** (§2)? | **NO. It burns the fixpoint's ENTIRE 200,000-application cap on EVERY step, under BOTH update schedules.** |
| Does orientation emerge? | **NOT ASKED. §2 forbids it** — an arm measured on a non-convergent scaffold is measured at an arbitrary point on a limit cycle, which is the exact defect that killed nine attempts. |
| Does settling give the learning rule an operating regime (8D's §2 prediction)? | **UNANSWERED, and honestly so.** It cannot be asked until the loop settles. |

**The reason it does not converge is not an implementation defect. It is a
spectral fact about the sheet**, and it is the same fact that explains why GCAL
needs the constants §13 forbids me to import.

---

## 2. WHAT WAS BUILT

`seeds/vision_settle.json` (ships **INERT**: `settle=0`, `bubble=0`):

| rule | what it does |
|---|---|
| `st_latch_aff` | latches the afferent drive into `aff` once per step (phase guard, `wv_propagate`'s idiom) — the relaxation's inhomogeneous term |
| `st_settle` | `act_next <- max(aff + mean_nb(act) − mean_sheet(act), 0)` — the sweep |
| `st_commit` | `act <- act_next` — the synchronous (Jacobi) half-step |
| `st_burst_bubble` | every settled survivor bursts, so `oo_learn_*` (gated on `bursting`) learns the SETTLED response — GCAL's *"we use the V1 response to update the weights"* |

`domains/settle_world.py` is an adapter: `wire_sheet` states lattice adjacency
as edges, `set_settle_params` writes the ablation as **graph data**. **No Python
conditional decides any lateral dynamics** — the settling, the survivor set and
the burst are all rules.

---

## 3. EVERY CONSTANT, AND WHAT IT FALLS OUT OF (§13)

| number | falls out of |
|---|---|
| **settling step count** | **NO CONSTANT EXISTS.** `run_rules` IS the fixpoint; a `SetAttr` landing the same value does not progress. GCAL's own words for its 16 are *"a fixed number sufficient to ensure that cortical activity is no longer changing significantly"* — we hold the **criterion**; GCAL holds a **count** that fell out of it. **(This is also exactly what breaks — see §5.)** |
| **excitatory radius** | **NO CONSTANT.** The `sunit_neighbour` adjacency is the retina's OWN 4-neighbourhood, read off the grid the units already sit on (`rf`/`window_steps`' precedent). GCAL's `σ_E=0.025` NOT imported. |
| **inhibitory extent** | **NO CONSTANT.** Global — *"everything that is not a local neighbour is a competitor"* is what the committed hard-WTA Argmax **already is** (the infinite-inhibition limit). This rule SOFTENS an existing competition; it imports none. GCAL's `σ_I=0.075` NOT imported. |
| **inhibitory strength** | **NO CONSTANT.** The sheet's OWN mean activity — a RELATIVE threshold (§13's corollary: *"an absolute constant IS a view from nowhere; ratios transfer, absolutes do not"*). GCAL's `γ_I=−1.4` NOT imported. |
| **excitatory strength** | **NO CONSTANT — and this is the one that bit.** The MEAN of the neighbours, i.e. normalised by **the degree the graph itself supplies**. See §4: the alternative that *looks* constant-free is not. |
| `Max(Count,1)` denominator | **TOTAL, not a guarded lookup** (§1.1): on a degree-0 unit the Fold is 0 and `0/1 = 0` is the correct "no excitation", not a fabricated floor. |

**GCAL's `γE=1.7`, `γI=−1.4`, `16`, `σ_E`, `σ_I`, `α_E`, `α_I`, `μ=0.024` appear
NOWHERE in this seed.** That was the requirement. **§5 records what it cost.**

---

## 4. THE FIRST FINDING — "COUNT EACH EDGE ONCE" IS NOT CONSTANT-FREE. IT IS A GAIN OF 4.

The first cut SUMMED the neighbours — the choice that *looks* like it introduces
no number at all, because it only counts edges that exist.

**Measured: `act` → 2.48e+224.** The loop diverged toward float overflow.

**A sum over a degree-4 adjacency IS a 4× amplifier**, and no positive-feedback
loop survives one. The degree-normalised MEAN is the version whose stability is
**derived** rather than tuned. **This is a genuine §13 sharpening, and it cuts
against the naive reading of the rule:** "introduce no constant" is not the same
as "introduce no gain". The adjacency's degree is a number whether or not you
type it. GCAL types it (`γE=1.7`); we inherited it silently and it detonated.

---

## 5. THE DECIDING FINDING — THE FIXPOINT CANNOT TERMINATE, AND IT IS A THEOREM

The sweep's linear part is exactly

```
M = D⁻¹A − (1/N)J
```

`D⁻¹A` (random-walk on the sheet), `J` (the global mean subtraction). I claimed
in the seed's own comment that `M` is a contraction *"for a connected
**non-bipartite** lattice"* — **and a square lattice is BIPARTITE.** I stated the
condition and then violated it.

**Measured (`n_side` 3/4/5, the exact wired operator):**

| n_side | N | ρ(M) | λ_min(M) |
|---|---|---|---|
| 3 | 9 | 1.000000 | **−1.000000** |
| 4 | 16 | 1.000000 | **−1.000000** |
| 5 | 25 | 1.000000 | **−1.000000** |

A bipartite graph's random-walk matrix has an eigenvalue of **exactly −1** — the
**checkerboard mode**, which **negates every sweep**. A period-2 orbit **is not a
fixed point**. `run_rules` terminates on *exact value equality*, so on this sheet
it **provably cannot terminate**, and it does not:

| schedule | applications / step | hit cap? |
|---|---|---|
| Gauss-Seidel (in-place) | **200000 / 200000** | **6/6 steps** |
| Jacobi (double-buffered, GCAL's own) | **200000 / 200000** | **6/6 steps** |

The synchronous fix — the mechanism fix, precedented by the setpoint rung's
EMA→cumulative-mean correction, **not** metric surgery — **did not rescue it**,
because the defect was never the schedule.

### 5.1 AND THIS IS WHY GCAL HAS A COUNT

**GCAL does not converge either. It STOPS.** Verified from the primary myself
(§12.4, PMC6618482, not taken from the peer): *"At t + 0.20 and every 0.05
iterations until t + 1.0, V1 continues to compute in a series of settling steps,
a fixed number sufficient to ensure that cortical activity is no longer changing
significantly"*, and then — decisively — *"Once all **16** settling steps are
complete, the settled V1 activation pattern is deemed to be the V1 response to
the presented pattern. **At this point** we use the V1 response to update ... the
afferent and lateral inhibitory weights via Hebbian learning."*

**GCAL's 16 is not an implementation detail of a fixed point. It IS the
termination rule.** GCAL never asks whether the sheet settled; it sweeps 16 times
and reads out. Its `γE=1.7 / γI=−1.4` — which its own paper says were *"set to
provide a balance between excitation and inhibition"* — are what keep 16 sweeps
in a useful regime.

**⇒ THE EXPRESSIBILITY ANSWER, PRECISELY:**

> **The engine expresses the settling DYNAMICS natively and cannot express the
> settling TERMINATION at all.** `run_rules` offers exactly one termination
> semantics — *run to an exact fixed point* — and GCAL's settling is
> *sweep a bounded number of times and stop short of one*. The engine's
> criterion is not a weaker version of GCAL's; **it is a different and strictly
> stronger one, and the stronger one does not exist on this sheet.**

The brief's hint — *"`run_rules` IS a fixpoint loop, and GCAL's settling is a
fixpoint"* — **is the half that is false, and it is the half that decides the
rung.** GCAL's settling is a **bounded iteration**, not a fixpoint. Tested, not
assumed; that is why it was worth testing.

---

## 6. WHAT I GOT WRONG

1. **I asserted a contraction whose own stated precondition my sheet violates**
   (non-bipartite). The proof named the hole and I did not look through it. A
   30-second `eigvals` — run only *after* the loop had already failed twice —
   settles it. **Check the spectrum before the sweep, not after.**
2. **I called the summed adjacency "constant-free."** It is a gain of 4 (§4).
3. **I assumed GCAL's 16 was an approximation to a fixed point.** The primary
   says the opposite in its own sentence, which I had already read and quoted
   before I built the wrong thing. **I had the disconfirming quote in hand and
   built past it.**
4. **The first cut was VACUOUS and I nearly missed it.** With `vision_settle`
   appended after `vision_onoff`, `rate == aff` **to the last digit** — the
   readout had already run on the UNSETTLED `act`. Only `D` on a downstream
   attribute (§1 clause 5) caught it.
5. **A silent anatomy bug of §12.3's exact shape:** `linspace(3,12,3).round()` =
   `[3, 8, 12]` — steps of **5 and 4**. My "lattice" wired **12** directed edges
   where **24** were due, with no error and no warning. An integer stride fixes
   it; a float `linspace` should never have been asked a lattice question.

---

## 7. THE ENGINE FINDING WORTH KEEPING — RULE PRIORITY IS SEED LOAD ORDER

`run_rules` tries rules in list order and restarts on the first that progresses,
so **a rule fires only once every EARLIER rule is exhausted.** `vision_onoff`'s
pipeline (`oo_sunit_activate` → `oo_sunit_rate` → `oo_sunit_burst_winner` →
`oo_learn_*`) is a phase sequence enforced *only* by that order, each rule
holding a once-per-step guard.

**⇒ A seed loaded AFTER another seed can never interpose a phase inside it.**
Measured: `rate == aff` exactly. Loading `vision_settle` BEFORE `vision_onoff`
gives `st_settle` priority and the settling then reaches the readout (`rate ≠
aff`, confirmed). **The phase structure IS the rule order, and the engine has no
other way to say it** — there is no priority, no phase, no barrier declaration.
That is why `scripts/settle_lib.py` re-implements `rung8_lib.build`'s boot rather
than calling it (§11 rule 4: `rung8_lib.py` is rung 8's file and is NOT edited).

---

## 8. §13.1 — COULD THIS HAVE PRODUCED THE OPPOSITE? AND THE CONTROL THAT COULD FAIL

**The control that could have failed, and DID: §2 itself.** The loop was free to
settle and did not. The measurement that killed the rung is the one the rung was
built to pass.

**The forced-architecture question, answered honestly for the arm I did NOT run:**
the settling rules force a **BUBBLE** (a locally-coherent active cluster) — that
much *is* architectural, and I claim no credit for it. They do **not** force an
**ORIENTED** bubble: on a thin travelling wavefront (`front_nb_raw` 1.9898,
`coh_local` 0.7809) a bubble is an oriented segment, while on GCAL's own isotropic
disks the same rules make an isotropic blob. **This is the sharp edge the brief
names: GCAL produces orientation FROM isotropic disks, so "orientation appeared"
would NOT have discriminated a working mechanism from a forced one.** The
pre-registered control would therefore have had to be the **disk arm** — same
rules, isotropic input — which can fail and which no rule here can rescue.
**It was not run, and nothing about orientation is claimed.**

---

## 9. §9 — DEFAULTS PRESERVE COMMITTED RESULTS

`scripts/rung7_vision_bench.sh`: **200 passed / 0 failed / 0 skipped** at engine
`74fc035c8595`.

**Quoted WITH ITS CONDITION (§10.2): this is the `200/0` WITH `data/` number, not
the `190/10` without it.** My worktree symlinks `data/` from canonical, so the 10
BSDS300 tests that *"have never run in any worktree"* **ran here and passed**.

`vision_settle` ships `settle=0`, `bubble=0`; no committed script loads it; the
only shared file touched is `domains/seed_registry.py` (an additive
registration). `PickUnique` is used for every config read (`param()`-equivalent);
`set_settle_params` refuses a non-singleton `SettleParams` rather than letting
`PickUnique` panic (§12.3).

---

## 10. WHAT A NEXT ATTEMPT MUST DECIDE (NOT DONE HERE)

The blocker is now **named and spectral**, not vague. Three routes, and each needs
its own pre-registration with a mechanism-level hypothesis (§3.6 — none of these
is a parameter search):

1. **Damping** (`act_next = (1−α)·act + α·f(act)`) moves λ from −1 to `1−2α`,
   killing the checkerboard mode. **`α` is a KNOB and must be NAMED as one** — an
   honest knob is acceptable; a knob dressed as a derivation is not. Whether α
   falls out of anything (a membrane time constant the sheet measures in itself,
   as `mu_endo` did) is the real question, and I did not answer it.
2. **A non-bipartite sheet** (8-connectivity adds the diagonals and destroys the
   2-colouring) removes λ=−1 **structurally, with no constant at all**.
   `wire_sheet(connectivity=8)` already exists and is untested. **This is the
   cheapest honest shot and I did not take it** — it is a mechanism change and
   deserves its own prereg, not a sweep appended to a failed run.
3. **A bounded-iteration Term in Rust** would give the engine GCAL's actual
   semantics (sweep k times, stop). Expressibility is NOT grounds to reject a
   biologically-plausible mechanism (the creator has ruled twice), and this is the
   one place a Rust Term is genuinely indicated — but it hands the count back as a
   constant, which is precisely what §13 forbids importing. **That tension is
   unresolved and I am not resolving it by fiat.**

**The honest summary: the missing layer is now BUILT and INERT, its dynamics are
expressible in pure graph rules with no Rust, and it does not run because the
sheet's spectrum says a fixed point does not exist. That is a diagnosed negative
(§7), and it is worth more than an un-diagnosed positive would have been.**
