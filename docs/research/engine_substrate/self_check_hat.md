# The self-check hat — the agent's weighted, bounded skeptic

## VERDICT (lead)

The agent now has its OWN weighted self-check reflex — the disposition the assistant
used to supply by hand. Built from the agent's own pieces (native surprise +
meta-monitor + do-contrast), composed as native Term-trees. The killer replay
(`scripts/self_check_hat_replay.py`, full log `/tmp/selfcheck_full.log`,
EXIT=0, `===MARKER_SELF_CHECK_HAT_REPLAY_COMPLETE===`) shows:

| case | conf | surprise | uncertainty | stakes | **weight** | fire | decision |
|---|---|---|---|---|---|---|---|
| **W5 regression** | 0.320 | 1.139 | 0.533 | 1.00 | **0.533** | **FIRE** | **REOPEN** |
| Stage-5 clean win | 0.978 | 0.022 | 0.022 | 0.55 | 0.012 | glance | COMMIT |
| Stage-6 clean fire | 1.000 | 0.000 | 0.000 | 0.60 | 0.000 | glance | COMMIT |
| weighting: high-stakes + clean | 1.000 | 0.000 | 0.000 | 1.00 | 0.000 | glance | — |
| weighting: low-stakes + W5-surprise | 0.320 | 1.139 | 0.533 | 0.10 | 0.053 | glance | — |

- **(1) Catches W5**: weight 0.533 > threshold 0.30 → FIRE → targeted do-contrast at the
  weak link (the OLD anchor baseline) → meta-monitor measures payoff WITH the real anchor
  prior (0.625) vs WITHOUT it (the degraded 0.20), Δ+0.425 → resolves **REOPEN**: the
  "matches/beats OLD = True" verdict compared the fused 20% to a **degraded** OLD baseline
  (62.5% → 20%). Rejected — exactly the way the assistant caught it by hand.
- **(2) Does NOT over-fire**: the clean Stage-5 (real-but-modest gain, anchor held) and
  clean Stage-6 (boundary-F1 lift, baseline intact) get a glance (weight 0.012 / 0.000)
  and COMMIT. One bounded check on the suspicious; a glance on the clean. No OCD.
- **(3) The weighting is real, not a binary**: high-stakes-but-clean (weight 0.000) does
  NOT fire — stakes alone can't trip it. The SAME surprise as W5 at low stakes (weight
  0.053) does NOT fire either. Only uncertainty × stakes BOTH high fires (W5, 0.533).

## What was built

A gateable module on the loop — **just a hat**, not a core change.

- **`domains/self_check_hat.py`** — the hat. Native Term-trees + world-adapter glue only.
  - `T_CONF` (line ~94): confidence the verdict deserves = realised_support / claimed_support,
    clamped — native `Div/Max/Min`. When OLD claims 0.625 but realises 0.20, conf ≈ 0.32.
  - `T_UNCERTAINTY` (line ~102): `surprise/(surprise+1)`, where `surprise = Neg(Log(T_CONF))`
    is the agent's OWN error signal (imported `scripts.native_collapse.T_SURPRISE`).
  - `T_WEIGHT` (line ~106): `Times(T_UNCERTAINTY, Attr(C,"stakes"))` = **uncertainty × stakes**.
  - `T_FIRE` (line ~109): `IfThenElse(Gt(T_WEIGHT, fire_threshold), 1, 0)` — the fire/glance
    decision is a native Term, evaluated by `substrate.evaluate`. No Python `if` decides it.
  - `gate_verdict` (line ~118): marshals a verdict's numbers onto a `Check` node, evaluates
    the four native Terms. `run_do_contrast` (line ~178): hands the weak-link do-contrast to
    the agent's OWN investigator (`domains.meta_monitor.investigate` /
    `install_investigation_rule` / `agent_conclude_investigation` — the 3-way
    lever_helps/lever_harms/disconnected_lever graph Rule). `resolve` (line ~219): bounded
    REOPEN/COMMIT. `self_check` (line ~258): the whole reflex in one call.
- **`seeds/self_check_hat.json`** — the one dial (`fire_threshold: 0.30`), seeded not hard-coded.
- **`scripts/self_check_hat_replay.py`** — the killer replay (world-adapter glue: feeds the
  REAL staged-run numbers into the hat, runs the do-contrast callables, reads the verdict).

### How the weight = uncertainty × stakes is computed from the agent's own pieces

- **uncertainty** ← the agent's native SURPRISE Term (`-log(conf)`, the same one
  `native_collapse` uses for its manifold), squashed to [0,1). conf is the realised-vs-claimed
  support ratio — a verdict whose support crashed below its claim has low conf, high surprise.
- **stakes** ← the verdict's own declared cost-of-being-wrong in [0,1] (a gate-fire/commit ≈ 1.0).
- **weight** ← native `Times` of the two. FIRE ⇔ native `Gt(weight, threshold)`.
- the targeted check ← the agent's own do-contrast (meta-monitor `investigate`), at the weak
  link only — not a global re-doubt.

### Donkey / architecture audit

- **Hat, not core.** Three NEW files only (`git status`: `?? domains/self_check_hat.py`,
  `?? scripts/self_check_hat_replay.py`, `?? seeds/self_check_hat.json`). CortexLoop /
  `scripts/solve_for_n.py` / `domains/cortex_loop.py` **untouched** (git clean). The
  quarantined core is not modified. `domains/order_n_postulates.py` and
  `domains/speech_science.py` were dirty before this task (another task owns them) and contain
  no `self_check` refs — not touched here.
- **No new Python cognition.** Every decision is a Term (`T_FIRE`, `T_WEIGHT`) or the
  meta-monitor's existing `investigate_connection` Rule. Python only marshals numbers into
  graph attrs and runs the caller's measurement callables (world-I/O), exactly as
  `meta_monitor.investigate` already does.
- **No net, no .fit, no gradient, no sweep.** The weight is composed surprise arithmetic; the
  do-contrast verdict is a graph Rule deciding from MEASUREMENT.
- The surprise + meta-monitor are graph-resident already; the hat only COMPOSES them.

## Honest assessment

The agent's own skeptic is **seated**: it catches the W5 miss (weighted, via a targeted
do-contrast at the weak link, then re-opens) and it does NOT OCD the clean wins (glance +
commit). The weighting genuinely discriminates — proven by the two control cases where
stakes-alone and surprise-alone both stay below threshold; only their product fires.

Honest scope notes (not gaps in the reflex, but its boundaries):

- The hat reads the verdict's **claimed vs realised support** and **stakes** as inputs from the
  caller (world-adapter glue, the way every probe feeds the substrate). The numbers replayed
  here are the REAL staged-run values; wiring the hat to read them automatically off a stage's
  printed verdict line is a thin follow-on (a parser, still glue), not new cognition.
- The W5 miss is detected via the realised-support-crash signal AND confirmed by the
  meta-monitor do-contrast (Δ+0.425). The do-contrast here measures the anchor-vs-degraded
  payoff; for a stage that does not expose a clean with/without toggle, the hat still fires on
  the surprise but the do-contrast would need that stage to declare its intervention (the
  meta-monitor's seed-declared intervention pattern). The reflex is correct; its do-contrast is
  as good as the weak-link toggle the stage exposes.
