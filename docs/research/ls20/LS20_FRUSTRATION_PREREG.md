# FRUSTRATION — futile repetition triggers an emotional STOP (PRE-REGISTRATION)

*Committed ALONE, BEFORE any implementation and BEFORE any measurement.
Isolated worktree off `main` HEAD **`80f1e12cb2`** (LEDGER 224000). Engine
canonical **`793ce09ed498a749abb79aeaea44b92e`** (`_native.abi3.so`, shared
build; Rust source identical to this worktree — `source_match` to be reported).
This rung adds **NO Rust** (`term.rs` diff EMPTY, whole `runners/dsl` diff
EMPTY) and **ONE new `self_load_only` seed** (`seeds/ls20_frustration.json`,
emitted by the builder `domains/ls20_frustration_seed.py`) plus a mechanical
world adapter + measure + tests. Seed block **226000–226999** (`default_rng` /
derived seeds at the block base).*

Seed-claim check (verbatim, run before any number):

```
$ python3 scripts/seed_claim.py 226000 226999
SEED CLAIM 226000-226999: CLEAN -- no collision DETECTED.
  Scope: 930 files with seed sinks; 633 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

This block was CLEAN at pre-registration; the verbatim `check_claim` above is
the record. It is **NOT installed as a permanent pytest** — a seed-claim check
INVERTS the moment this block's ledger row lands (the 223000 mistake). It is a
pre-registration artefact, quoted here, not a gate.

---

## 0. THE STEER (owner)

> *"The last playback shows the avatar just cycling. Doing the same thing over
> and over is not just wrong — it should also trigger an emotional reaction to
> stop."*

Build the frustration / anti-cycling emotional regulation: **repetition WITHOUT
understanding-gain → a frustration modulator rises → break the loop (switch
strategy / stop).** This is the PSI REGRESS-BREAKER (Dörner / Bach; the 207000
modulator framework) wired to the 221000 understanding signal — **frustration
is the emotional COMPLEMENT to the curiosity/understanding drive: understanding
rewards compression, frustration punishes futile repetition.**

---

## 1. FRAMING — a glass-box, gated instantiation; NOT new psychology

This re-derives, it does not discover, an established idea: Dörner's PSI /
Bach's MicroPsi hold that an **anti-regress / resolution-lowering** modulator
rises when a strategy stops paying off and forces the agent off it. The
contribution is the **graph-native, gated, ATTRIBUTABLE instantiation** wired to
this project's OWN understanding signal (221000 surprise / hypothesis growth):
every decision — *is this repeat futile?*, *how much frustration?*, *stop now?*
— is a **RULE** over graph data, fired by `run_rules()`. Because the knobs are
named we can attribute the STOP to *futility accumulated past a threshold*, and
DISTINGUISH it from mere repetition — a black box cannot.

**Synthetic-proven ≠ benchmark value.** The powered headline runs on a SYNTHETIC
cycling scenario (a controlled model). An ls20 DEMONSTRATION follows, honestly
framed: the live ls20 cycling the owner saw is partly the naive live-harness
action policy; the general deliverable is the CAPABILITY (emotional regulation
against futile repetition), which serves any domain (Doom, harvest, ls20).

---

## 2. THE DISCRIMINATOR IS THE WHOLE POINT (do NOT build a repeat-counter)

Frustration must track **FUTILITY**, not repetition. Repeating an action that is
STILL yielding understanding (surprise dropping, hypotheses minting / confirming,
new state reached) is FINE and must NOT raise frustration. Only repetition with
**NO understanding-gain** is the trigger. **A plain repeat-counter that fires on
any repetition is REFUTED by the productive-repetition control (§4).**

Operationally, a step carries three RAW per-step observables the adapter stamps
mechanically (exactly as the 208000 narration adapter stamps `ev_*`), never a
decision:

- `d_hyp` — # hypotheses newly minted/confirmed this step (a graph count delta);
- `d_state` — # new distinct states reached this step (a graph count delta);
- `s_drop` — 1 iff this step's surprise is a strict new running-minimum.

**Understanding-gain = `d_hyp>0 OR d_state>0 OR s_drop==1`.** A step is FUTILE
iff it RECURS with NO gain. Both the recurrence test and the conjunction live in
the RULES, never in Python.

---

## 3. THE MECHANISM (graph-native; reuse 207 + 221 + 215; NO Rust)

ONE new `self_load_only` seed `seeds/ls20_frustration.json`. Wired to an
`EmotionHub` exactly like the 215000 grievance:
`EmotionHub -has_frustration_params-> HeldFrustrationParams{enabled, frust_unit,
half_life, frustration_thresh}`, `EmotionHub -has_frustration->
FrustrationModulator{now_epoch, frustration, break_now, hit_frustration,
action_tendency, emotion_code}`, and the trajectory as GRAPH DATA:
`FrustrationModulator -has_step-> Step{sig, epoch, d_hyp, d_state, s_drop,
futile}` (one immutable Step per acted step, the adapter adds it; `sig` is the
`state|action` signature).

**Four rules (all guarded on `HeldFrustrationParams.enabled==1`; integer-native;
Terms all pre-existing — `Sum/Ashr/IDiv/Times/Plus/Minus/Max/Eq/Gt/Gte/Lt/And/
Not/Exists/Attr/Lit`, no new Term):**

1. **`fr_mark_futile`** (order 0) — THE DISCRIMINATOR. Matches a Step `st`; sets
   `st.futile = 1` iff `st.d_hyp==0 AND st.d_state==0 AND st.s_drop==0` AND
   `Exists st2` (another `has_step` Step) with `st2.sig==st.sig AND
   st2.epoch<st.epoch`. Recurrence is a graph MATCH over the step history (the
   gap_awareness dedup-`Exists` precedent); no-gain is the three raw observables.
   A productive repeat has a gain observable set → NOT marked futile. Idempotent
   (pure function of immutable Step facts).
2. **`fr_accumulate`** (order 1) — the leaky **scale2** accumulator, the 215000
   `gs_grievance_from_slights` pattern verbatim in shape:
   `frustration = Sum_{st in has_step} Times(st.futile,
   Ashr(frust_unit, IDiv(now_epoch − st.epoch, Max(1, half_life))))`.
   Only futile steps contribute (`Times(st.futile, …)`); older futile events
   decay (`Ashr`). **Productive repetition → every `st.futile==0` → Sum stays 0.**
   Idempotent (pure function of the futile flags + adapter-advanced `now_epoch`).
3. **`fr_break`** (order 2) — THE REGRESS-BREAK. Where `frustration >=
   frustration_thresh`: sets `break_now=1`, `hit_frustration=1`,
   `action_tendency="STOP"`, `emotion_code=1`. The emotion converts "futile" into
   "stop". The STOP is THIS RULE reading the modulator — never Python.
4. **`fr_narrate_code`** is subsumed into `fr_break` (it sets `emotion_code`); a
   `FrustrationNarration{code:1, template:"Same thing, no progress — this is
   frustrating. Stop."}` lexicon node is the 208000 template the adapter emits
   when `break_now==1` (mechanical format).

The adapter does EXACTLY: add the immutable `Step` with its raw observables,
advance `now_epoch`, `run_rules()`, read `frustration` / `break_now` /
`action_tendency` off the graph, and (ON) stop the loop when `break_now==1`.
**No `graph_rewrite.run` / `_match` / `_apply` / `make_rule`; no `if repeated:
stop`; no conditional over graph state that decides an agent action.**

---

## 4. THE GATES (pre-registered; measured on the SYNTHETIC scenario, powered)

Two arms, **N = 200 runs each** (seeds `226000 + i`), bootstrap **95% CI**
(2000 resamples). Both arms repeat the SAME `(state,action)` many times; the
ONLY difference is whether the repeats keep YIELDING understanding:

- **FUTILE arm** — after a short productive prefix the agent falls into a
  `(state,action)` cycle with `d_hyp=d_state=s_drop=0` on every repeat.
- **PRODUCTIVE arm** — the agent repeats the SAME `(state,action)` but each
  repeat still yields a gain (one of `d_hyp/d_state/s_drop` fires).

Randomised per run: the productive-prefix length and small jitter in which gain
signal fires (productive arm). World constants FROZEN by this prereg:
`frust_unit=8`, `half_life=4`, `frustration_thresh=20`, episode cap `CAP=40`.

**G-frustration-tracks-futility (HEADLINE + teeth).** Frustration measured after
`W=6` repeats. Registered prediction: FUTILE-arm frustration is HIGH; PRODUCTIVE-
arm frustration is **0** (flat); the two 95% CIs are **separated**. *The
PRODUCTIVE control is the gate that FAILS if frustration merely counts repeats.*
REFUTED if the two arms' CIs overlap, or the productive arm's frustration
upper-CI is not ≈0.

**G-breaks-the-loop.** On the FUTILE scenario, regulation **ON** vs **OFF**
(`enabled` 1 vs 0), paired on seeds. Metric: steps-until-the-cycle-is-broken
(ON = the step `break_now` fires; OFF = the episode cap `CAP`, the un-regulated
agent never stops itself — the "just cycling" the owner saw). Registered
prediction: **ON ≪ OFF**, CIs separated (the emotion is the regress-breaker,
measured). REFUTED if ON is not CI-below OFF.

**G-no-false-break (selectivity).** On the PRODUCTIVE scenario, regulation ON.
Metric: the FALSE-BREAK RATE = fraction of runs where `break_now` fires before
the productive episode ends. Registered prediction: **0** (Wilson 95% CI upper
bound reported); the regulation does NOT stop an agent that is still gaining.
REFUTED if the productive arm breaks at a rate whose CI excludes a low bar
(pre-set: upper CI must be < the FUTILE-arm break rate's lower CI).

**G-graph-native.** Source audit of the adapter: every decision (futile? how
much? stop?) is a rule; the adapter is mechanical I/O. No rule-engine calls, no
`if repeated: stop`. Reported with the location of each decision.

**G-narration (ties to 208000).** The agent narrates the reaction + the stop
from graph state: on `break_now==1` the adapter emits the `FrustrationNarration`
template keyed by `emotion_code`. A verbatim sample is reported.

**G-discipline.**
- Integer-native; every literal a whole number.
- **Default-OFF byte-identity:** `ls20_frustration.json` is `self_load_only:true`
  (skipped by `load_all_seeds`; nothing `depends_on` it), so the tree is
  byte-identical with it absent. Shown by the unchanged oracle + regression
  node-id SETS.
- **Canonical `.so` md5 stays `793ce09ed498a749abb79aeaea44b92e`**; **`term.rs`
  diff EMPTY, whole `runners/dsl` diff EMPTY** (NO Rust; if a primitive seemed
  needed I would STOP and report — it is not).
- **Oracle** `bash scripts/rung7_vision_bench.sh` BEFORE == AFTER.
- **Regression** `bash scripts/per_area_settlement_regression.sh` (34-file)
  BEFORE == AFTER (compared as the SET of failing node ids, never a count).
- **`source_match`** reported.

---

## 5. THE ls20 DEMONSTRATION (honest scope)

Using the 221000 understanding machinery OFFLINE (the `arc_ls20_scenario`
corpus + sd-loop recogniser — reproducible, no live API): an agent that keeps
probing a station whose transform the sd-loop CANNOT recognise ("unrecognised"
each time) gains NO hypothesis / no surprise-drop → the SAME `(probe,station)`
recurs with no gain → frustration RISES → `break_now` fires → it stops probing
that station. A station it CAN learn (confirms accrue) → productive → frustration
stays 0 → no break. The frustration modulator reads the ACTUAL 221000 signals
(confirmed-hypothesis delta, surprise running-min). **Honest:** this
demonstrates the CAPABILITY on the real understanding signal; the live-harness
cycling is a separate naive-policy issue. If the live ls20 API is exercised at
all, auth is verified first and `ARC_API_KEY` is never printed/committed; STOP +
report if unreachable, never fabricate.

---

## 6. FALSIFICATION BAR

Frustration tracks FUTILITY (repetition-WITHOUT-understanding-gain), NOT mere
repetition — the productive-repetition control is the teeth; the loop-break is
MEASURED (ON vs OFF) AND SELECTIVE (does not break productive loops). GENERAL —
the same modulator framework serves any domain, not an ls20 hack. Every gate
reports the straight null if it fails.

---

## 7. NAMED FOLLOW-ONS (explicitly NOT built here)

- wiring `frustration` into the 207000 `ModulatorState` region reader so it
  lowers global `resolution` (the true PSI resolution-drop), not only a local
  STOP flag;
- frustration → EXPLORATION-raise (switch strategy) as an alternative to STOP
  (the regress-break's other face);
- the live ls20 harness action-policy fix (the Python-layer cycling the owner
  saw is a blind spot the agent can only FIND, per the gap pipeline);
- graded frustration → graded resolution as a continuous PSI dial.
