# THE FIXPOINT PREDICATE `run_rules` CAN SATISFY — cycle detection

*Continues the settling rung (`39f2ae29`) and the non-bipartite rung (`0d1978f2`).
Engineering, not the paradigm claim (§7): the sd rung's negative — "the loop
composes what it holds; it does not discover what it lacks" — stands untouched.*

**Engine:** `engine 8c55ce96c909 @ …/runners/dsl/python/substrate_rs/_native.abi3.so`
(own build of THIS tree's Rust source; provenance gate 7/7). Baseline engine
before the change: `5c2957b3b081`. Base commit `0d1978f2`. Bench condition:
`data/` symlinked from canonical → **200 passed / 0 skipped** (without `data/` it
is 190/10; §10.2).

**Seed block: 23000–23999 ALLOCATED, BURNED NONE.** Every measurement here is on
already-burned seed 0 and is DETERMINISTIC (byte-identity, application counts,
bit-identical state, the degree-ε refutation, the spectrum) — no RNG arm, so no
confirmatory seed is consumed. The exploratory pilot (§4 below) is likewise
burned-seed-0 only.

---

## 1. THE PROBLEM, REPRODUCED ON THIS TREE'S OWN ENGINE (§12.4)

The non-bipartite rung's ULP measurement is a sibling's claim, not a source. Re-ran
`scripts/settle8_terminate.py` on engine `8c55ce96c909`:

```
c=4, cap-burning step: act scale 1.8358, 1 ULP = 2.220e-16
  tick apps  d_act      d_act_next   |act-next|
   0    1    0.000e+00  8.882e-16    8.882e-16
   1    1    8.882e-16  0.000e+00    0.000e+00     ... forever
  => 4.0 ULP  -> ULP DITHER of a SETTLED sheet
c=8, cap-burning step: act scale 18.3001, 1 ULP = 3.553e-15
  => 1.0 ULP  -> ULP DITHER of a SETTLED sheet
```

Confirmed independently: every cap-burning step is a **period-2 ULP dither of an
already-settled sheet** (settled to ~1e-16). `st_settle` writes `act_next` one ULP
away; `st_commit` copies it back; `run_rules` terminates only on EXACT value
equality, which a float contraction's fixed point generically cannot reach, so it
dithers between the two nearest floats and burns the 200 000 cap forever. **This is
a fact about exact-equality fixpoints over floats — it afflicts any relaxation the
substrate runs, not a lattice/cortex/vision fact.**

---

## 2. THE FIX — CYCLE DETECTION, AND WHY IT OVER THE ALTERNATIVES

**A period-2 orbit IS a fixed point of the 2-step map**, and rule application is a
DETERMINISTIC map on graph state, so a **repeated state proves the trajectory is
periodic** — nothing new can be reached, and continuing to the cap discovers
nothing. The termination test becomes "have I been in this exact state before",
which needs **exact equality against history and NO TOLERANCE**.

`TypedGraph::state_fingerprint()` (Rust, `graph.rs`) hashes every live node
`(id, type, attrs)` and edge `(src, type, tgt, attrs)`, **order-independently**
(XOR/`wrapping_add` folds — load-bearing, because `Attrs` is a `Vec` whose `remove`
is a `swap_remove`, so equal states can be stored in different orders). `run_rules`
gains an opt-in `detect_cycles`: it stops when a state's fingerprint repeats,
placed AFTER the committed `!any_progress` exit so a true fixed point still returns
by the old path.

**Why this over the named ε-route and the other alternatives:**

| route | verdict |
|---|---|
| **cycle detection** (built) | commits **NO float**. No ε, no knob — there is no constant to name. Cost: state (a hash set), and a probabilistic 64-bit collision (~2.7e-10 over ~1e5 states). |
| ε = fixpoint up to `np.spacing` (the named route) | its ε-factor is OPEN — dithers span **1.0–4.0 ULP** — and **"tune it to 4" is `μ=0.024` again**. |
| degree-based ε (`d·ULP`) | **REFUTED BY THE DATA, re-measured here:** c=4 (degree 4) → 4.0 ULP, c=8 (degree 8) → 1.0 ULP. **More degree gave LESS dither**, because ρ<1 (0.668 at c=8) damps round-off while ρ=1.000 (c=4) is marginal. The dither is set by loop GAIN ~1/(1−ρ), and **ρ is not something a rule can know**, so a rule-side ε has nothing to fall out of. |
| tolerance predicate in `run_rules` | principled but needs an ε AND changes core-loop semantics for every seed. |
| don't-write-below-resolution | relocates the same unknown-ρ constant into the rule. |

**The ε falls out of nothing, because there is no ε.** That is the §13 pay-off:
the honest form of the mechanism is not a magic number falling out of a natural
process, it is *no number at all* — the same test GCAL's tolerance predicate
approximates, taken to the machine's exact resolution by asking about history
rather than about a threshold.

**SOUNDNESS CAVEAT (stated, not assumed):** determinism is the premise. The
engine's only randomness is a seeded xorshift (`apc.rs`). An effect reading
genuinely external mutable state between passes (a live framebuffer) could revisit
a graph state and still have somewhere new to go — so detection is **opt-in per
call, never global**.

---

## 3. §9 — WHAT MOVED (nothing) AND THE ORACLES, RECOMPUTED LIVE (§12.3)

**Detection ships OFF by default at every layer** (`run_rules_opts(…, false)`, the
pyo3 `detect_cycles=false`, both Python wrappers `= False`). A seed that does not
opt in computes no fingerprint, keeps no state, and cannot move.

**Byte-identity, proven across TWO DIFFERENT BINARIES.** `scripts/bulk_attr_digest.py`
on the pre-change engine `5c2957b3b081` and on the new engine `8c55ce96c909`:

| | track_prev_burst=False | =True |
|---|---|---|
| pre-change `5c2957b3b081` | `49d6ab06…099142` | `2df8181d…09b61f` |
| new `8c55ce96c909` | `49d6ab06…099142` | `2df8181d…09b61f` |

**Identical.** The oracle was **positive-controlled** (§12.3): `+1e-9` into one
`last_burst` write flipped BOTH digests (`98d114dc…`, `dd22e0c9…`); revert restored
both exactly. An oracle only ever seen pass is not an oracle tested.

Every other committed contract, recomputed live (never a frozen digest):

| contract | required | measured |
|---|---|---|
| vision bench (with `data/`) | 200 / 0 | **200 passed / 0 skipped** |
| `fm0_vacuity_audit` | VACUOUS, D==0.0 | **VACUOUS, D=0.0e+00** on lum/x/θ/resp |
| `fm0b` | 8.071079e-01 / 5.315726e-01 / 4.013261e-01 / 5.169134e-01 | **exact, all four** |
| Troxler | 7/7 | **7/7** |
| sd-loop / dimension inference | orbit law + 16 gates | **16/16 + 8/8** |
| engine provenance | 7/7 | **7/7** |

**Nothing moved.** A semantics change was permitted to move results; it did not,
because the new exit is unreachable except on a run that currently BURNS THE CAP,
and no committed contract does.

---

## 4. DOES THE DITHER TERMINATE, AND IS THE ANSWER THE SAME SHEET? (yes, exactly)

`tests/test_cycle_detect_migrated.py` (10/10). On the settling loop with detection
ON vs OFF, per developmental step:

```
c=4: apps OFF = 1 200 000   ON = 38    (31 579× fewer applications)
     max|act_off − act_on| = 0.000e+00  (0.0 ULP)  -> THE SAME SHEET, bit-identical
c=8: apps OFF =   600 000   ON = 12    (50 000×)
     max|act_off − act_on| = 0.000e+00  (0.0 ULP)  -> THE SAME SHEET, bit-identical
```

**This is what distinguishes cycle detection from a tolerance predicate: a
tolerance ACCEPTS a nearby state; detection PROVES there is no other state to
reach.** The answer is not within an ε of the cap's answer — it IS the cap's
answer, 30 000× cheaper.

The gate is positive-controlled two ways: (a) the default-off gate went RED when
the observable default was flipped to true and GREEN when reverted — and it caught
that the default lives in TWO places (the pyo3 signature AND the Python wrapper);
(b) the detector is shown to ABSTAIN on already-terminating steps (c=8 apps=0
under both), so it is discriminating a real cycle, not firing unconditionally.

---

## 5. §2 / 8D — THE QUESTION IS NOW ASKABLE. EXPLORATORY PILOT SAYS IT DOES NOT
### TRIVIALLY RESOLVE.

`scripts/cycle_settle_convergence_pilot.py`, **EXPLORATORY, burned seed 0 only.**
drift(t) = ‖w(t)−w(t−Δ)‖/‖w(t)‖ over developmental time, settling load-ordered so
it is load-bearing (`st_settle` relaxes `act` before `oo_sunit_rate` reads it):

| η | ‖w‖ (start → end) | drift (start → end) | regime |
|---|---|---|---|
| **5e-4** (committed default) | 29.702 → 29.715 | 0.0071 → 0.0060 | **near-vacuous** — flat, drift not falling |
| 2e-3 | 29.701 → 29.779 | 0.029 → 0.039 | active, ‖w‖ creeping |
| 5e-3 | 29.701 → 30.211 | 0.072 → 0.103 | drift RISING, ‖w‖ growing → runaway edge |

The pilot **discriminates** (drift monotone in η), so "5e-4 is near-vacuous" is a
real reading, not a dead instrument (§1 clause 4). **None of the three η's shows
drift → 0.** Making the loop TERMINABLE did not hand over CONVERGENCE — 8D's
tension survives: there is a near-vacuous end and a runaway end and this pilot
found **no η that is both convergent (drift→0) and load-bearing (‖w‖ moves)** on
this small sheet. That is the honest state: the question is now *askable*, and
answering it needs its own pre-registration, an η-sweep, fresh seeds, and the
`wave_world.step` opt-in (below).

---

## 6. WHAT THIS DOES NOT FIX — STATED PLAINLY

- **ρ(M) → 1 as the sheet grows** (0.45 → 0.87 over n_side 3→6; re-checked here,
  gated in `test_rho_ceiling_is_not_fixed_by_this`). A GCAL-scale sheet settles
  arbitrarily slowly **regardless of termination semantics**. Cycle detection ends
  the *dither*; it does not make the sheet *settle faster*. The small sheets above
  are small **for this reason** — a working small sheet is NOT the ceiling moving.
- **GCAL says "(data not shown)"** — it asserts convergence and never demonstrates
  it (non-bipartite rung, verified from the primary).
- The `wave_world.step()` internal `s.tick(200_000)` does **not** thread
  `detect_cycles`. It is shared infrastructure this rung does not edit (§11.4);
  **the one-line opt-in is REPORTED for the supervisor to sequence**, and is what
  the confirmatory §2/8D run needs. (The learning TRAJECTORY is unaffected by it —
  the guarded `oo_learn` fires once per step regardless — so the fix buys
  tractability at scale, not a different answer.)

---

## 7. WHAT I GOT WRONG EN ROUTE

- **The default-off gate's first draft could only ever pass** (`s.tick(10) ==
  s.tick(10, False)` on a fresh substrate — no cycle, so equal either way). §12's
  "a guard that runs the thing it guards is not a guard", in a new costume. Caught
  by the positive control, rewritten to gate the default where it is observable (a
  DITHERING sheet must still burn the cap with no flag).
- **I positive-controlled by flipping only the pyo3 default and it stayed GREEN** —
  because the Python wrapper passes the flag explicitly and shadows it. The
  observable default lives in TWO places; the gate now guards both.
