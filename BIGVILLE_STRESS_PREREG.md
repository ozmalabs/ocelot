# PREREG — block 328000: allostatic load + coping (C4)

`BIGVILLE_COGNITIVE_CAPABILITIES_PLAN.md` C4. Chronic stress **accumulates as wear-and-tear**
(McEwen & Stellar's allostatic load), and when the cumulative load crosses the agent's
**window of tolerance** it **breaks down**; **coping** (co-regulation / rest) reduces the
load and recovers. Grounded in allostatic load (McEwen), coping/appraisal (Lazarus), and the
window of tolerance (Siegel — bigville already holds this). Extends the existing affect.

## The mechanism (`bigville_stress.json`)

- **`al_accumulate`** — a stressor the agent perceives adds its magnitude to `load` (once).
  It is the *accumulation* that matters — many small stressors sum, exactly as one large one.
- **`al_break`** — when `load > window` the agent's `broken` flag is set (breakdown:
  withdraw / tantrum / collapse) — a *chronic-load* threshold, not a single acute trigger.
- **`al_cope`** — a coping act (co-regulation) reduces `load` by `coping_relief` (floored at 0).
- **`al_recover`** — a broken agent whose `load` falls back within the window recovers.
- **`al_rest`** — on a rest epoch, `load` decays geometrically (`load · recovery`) — passive
  recovery between stressors; with `recovery = 0` each rest wipes the load (the falsifier).

## Gates (pass/fail, pre-registered) — the qualitative signature, not tuned numbers

1. **G-chronic-load-breaks (HEADLINE):** several stressors each **below** the window
   individually accumulate and **cross** it — the agent breaks from *chronic* load, not any
   single acute event.
2. **G-window-is-load-bearing:** the same stressor sequence breaks a **narrow**-window agent
   but not a **wide**-window one — tolerance capacity is real.
3. **G-coping-restores (HEADLINE):** an over-loaded agent that **copes** (co-regulation)
   drops its load back within the window and **recovers** (un-breaks).
4. **G-chronic-vs-reset (falsifier):** the same small stressors applied with a **full-reset
   rest between each** never accumulate and never break — proving it is the *accumulation*
   (McEwen), not the individual events, that breaks the agent.
5. **G-no-python-decision (source audit):** accumulate/break/cope/recover/rest are the seed
   rules; the adapter presents stressors, arms coping, pulses rest, and reads.

## Scope / honesty
- `load` is the agent's own cumulative held state; the stressor magnitudes are (in the full
  system) C3's negative appraisals — the demonstrator supplies them directly. Breakdown as a
  single `broken` flag stands in for the graded tantrum/withdraw/collapse repertoire bigville
  already has (`affect_spiral`, `viol_act`), wired in the integration.
- Allostatic load is modelled as a linear sum with geometric rest-recovery; McEwen's
  physiological multi-system detail is out of scope — the rung gates the accumulate →
  cross-window → break → recover signature.
- Isolated demonstrator (`self_load_only`); extends the existing affect conceptually; no
  Rust; `.so` untouched (`a8a9012c`).
