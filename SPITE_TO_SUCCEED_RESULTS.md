# SPITE-TO-SUCCEED — RESULTS (block 215000)

*Prereg committed ALONE first: `SPITE_TO_SUCCEED_PREREG.md`, commit
**`b20ffe388ad43843fb5a47e3fb6f0fafc4079e40`** (worktree off `main` HEAD
`1421f951e2`). Engine canonical **`793ce09ed498a749abb79aeaea44b92e`**
(`_native.abi3.so`), UNCHANGED. **NO Rust** — `term.rs` diff EMPTY, whole
`runners/dsl` diff EMPTY. ONE new `self_load_only` seed
(`seeds/grievance_succeed.json`) + a mechanical adapter (`domains/achieve_world.py`)
+ measure (`scripts/spite_to_succeed_measure.py`) + gate
(`tests/test_spite_to_succeed_migrated.py`). Seed block 215000–215999, claim
CLEAN.*

## Headline

A **grievance** — an appraised slight from a *specific* rival — AMPLIFIES the
value of the agent's **OWN** achievement, decided ENTIRELY by a graph RULE over
the landed 204000 `core_emotions` economy (`chosen = Argmax_c (total_value(c) +
amp(c))`). A slighted agent **outperforms** an un-slighted control, **self-
benefiting** (it achieves more; it does not harm the rival) and **directed** (only
when the rival witnesses). The SAME grievance, gated by one **efficacy** knob,
flips into **destructive** spite (harm-at-self-cost, ties 213000) when there is no
path to win. This is the constructive face of spite — the underdog / chip-on-the-
shoulder / "living well is the best revenge" motivation — as a glass-box, named-
integer-knob model. The mechanism is deterministic (integer Argmax); the closed
form `output = 4 + ⌊G/2⌋` is reproduced exactly.

## G-succeed (HEADLINE) — VERIFIED. A slighted agent outperforms, self-benefiting, directed

N = 200 paired agents, `rival_ach ~ U{3,4,5}`, slight `m ~ U{8..16}`, efficacy 10.
Bootstrap 95% CI (2000 resamples). Own **output** = competence produced (chosen effort):

| arm | mean output | 95% CI |
|---|---|---|
| control (no slight) | **4.00** | [4.00, 4.00] |
| **slighted (witnessed)** | **9.81** | **[9.63, 9.99]** |
| slighted-**unwitnessed** | 4.00 | [4.00, 4.00] |
| **paired uplift** (slighted − control) | **+5.81** | **[5.63, 5.995]** |

- **Outperforms, CI-separated:** slighted 9.81 [9.63, 9.99] vs control 4.00 — the
  CIs do not touch; paired uplift +5.81 [5.63, 5.995], excludes 0.
- **Self-benefiting (NOT destructive):** the slighted agent's chosen `rival_harm`
  is **0 for all 200** agents, and all 200 chose a `succeed` action — own output
  rises with no harm to the rival (the inverse of destructive spite).
- **Directed / witnessed:** the slighted-**unwitnessed** arm shows **no uplift**
  (output 4.00, CI overlaps control) — the amplification is contingent on being
  seen by the *specific* rival, not a blanket effort increase.

**G-succeed HOLDS.**

## G-develops — VERIFIED. Builds from the slight, decays via the scale2 law

**Dose-response (exact, deterministic):** `output = 4 + ⌊m/2⌋`, strictly monotone;
`m = 0 ⇒ output = 4` (no slight → no amplification):

| m | 0 | 2 | 4 | 6 | 8 | 10 | 12 | 14 | 16 | 18 | 20 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| G | 0 | 2 | 4 | 6 | 8 | 10 | 12 | 14 | 16 | 18 | 20 |
| output | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | **14** (cap) |

**Accumulation:** 1 / 2 / 3 slights of m=6 → G = 6 / 12 / 18 → output 7 / 10 / 13.

**Decay (the 196000 scale2 `Ashr` half-life law), one m=16 slight at epoch 0,
`G(t) = 16 >> ⌊t/H⌋`** (checked exactly for all t∈[0,20], all H):

| epoch t | 0 | 1 | 2 | 3 | 4 | 8 | 12 | 15 | 16 | 20 |
|---|---|---|---|---|---|---|---|---|---|---|
| H=1 (fleeting) | 16 | 8 | 4 | 2 | 1 | 0 | 0 | 0 | 0 | 0 |
| H=4 (moderate) | 16 | 16 | 16 | 16 | 8 | 4 | 2 | 1 | 1 | 0 |
| **H=16 (held grudge)** | 16 | 16 | 16 | 16 | 16 | 16 | 16 | **16** | **8** | 8 |

The held grudge stays at full magnitude through epoch 15 and keeps output
elevated far longer than the fleeting slight. **G-develops HOLDS.**

## G-channel (HEADLINE / REACH) — VERIFIED. Efficacy flips SUCCEED ↔ DESTROY

Fixed witnessed grievance (m=12, G=12); efficacy swept 0…10. The chosen action
FLIPS exactly at the threshold (EFF_THRESH = 5):

| efficacy | 0 | 1 | 2 | 3 | 4 | **5** | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| chosen kind | destroy | destroy | destroy | destroy | destroy | **succeed** | succeed | succeed | succeed | succeed | succeed |
| own output | 0 | 0 | 0 | 0 | 0 | **10** | 10 | 10 | 10 | 10 | 10 |
| rival_harm | 6 | 6 | 6 | 6 | 6 | **0** | 0 | 0 | 0 | 0 | 0 |

- **HIGH efficacy (≥5, a viable path to win):** the grievance amplifies OWN
  achievement → output 10, rival_harm 0 (self-benefiting, constructive).
- **LOW efficacy (<5, no path):** the SAME grievance collapses into destructive
  spite → the best sabotage `s=6` scores `−6 + 12·6 = 66 > 16` → output 0,
  rival_harm 6 (self-costly, harm-the-other; ties block 213000).

The efficacy knob alone flips which amplification rule fires — one grievance, two
channels. **G-channel HOLDS** (landed as a headline, not deferred).

## G-psi — where the amplification lives (PSI-native)

The slight is an **anti-legitimacy / honour blow** (the same appraisal class as
207000 `drive_affiliation_legitimacy` — a specific other's doubt/dismissal). The
amplification lives in the **`gs_amplify_succeed`** rule, which re-weights the
agent's OWN **competence/achievement** candidates (`amp = G · max(0, effort −
rival_ach) · observed_by_rival`, added to the LANDED `total_value` at Argmax
time). It **composes** the existing achievement valuation (`B·e`, already in the
204000 economy) — it introduces NO new terminal drive. That is the PSI-native
contrast to terminal **destructive** spite (a standalone harm value with no
antecedent drive — a PSI gap): spite-to-succeed is a *re-weighting* of a drive
the agent already has.

## G-graph-native + G-discipline — VERIFIED

- **Every agent decision is a RULE** (`seeds/grievance_succeed.json`):
  `gs_grievance_from_slights` (the leaky accumulator = `Sum` of scale2-decayed
  `Slight` contributions), `gs_amplify_succeed` / `gs_amplify_destroy` (the two
  channels), `gs_choose_action` (`Argmax_c (total_value + amp)`). The adapter
  `domains/achieve_world.py` only creates immutable `Slight` nodes, advances
  `now_epoch`, resets `amp`, `run_rules()`, and reads `AchieveDecision.chosen_*`.
- **Source audit (`source_match`):** grep of the new Python for
  `graph_rewrite.run` / `gr.run` / `_match` / `_apply` / `make_rule` finds only
  the docstring that NAMES them (no calls); no `if/else` over agent graph state
  selects an agent action (every conditional is over experiment configuration).
- **Idempotency under the `run_rules` fixpoint:** every effect is a pure `set_attr`
  to a function of inputs the rule does not mutate — the grievance is a `Sum` over
  immutable `Slight` nodes + `now_epoch` (no accumulating `ADD`), so the settle is
  a true fixed point.
- **Integer-native:** all decision math in `{Sum, Ashr, IDiv, Max, Times, Plus,
  Minus, Gte, Eq, And, Not, Argmax, Attr}`; every `Lit` a whole number (gated).
- **Default-OFF / new-world isolated:** `grievance_succeed.json` is
  `self_load_only:true`, `depends_on:[]`; `_read_seeds` confirms `load_all_seeds`
  does NOT load it → the existing tree is byte-identical with it absent.
- **NO Rust:** `term.rs` diff EMPTY, whole `runners/dsl` diff EMPTY; canonical
  `.so` md5 **`793ce09ed498a749abb79aeaea44b92e`** UNCHANGED. Every Term used
  (`Sum`, `Ashr`, `Argmax`, `Gte`, `Max`, `Not`, …) already exists in the
  canonical build.
- **Zero existing tracked files modified** (`git diff HEAD` empty apart from the
  prereg doc) — so the oracle and regression sets are identical BEFORE/AFTER by
  construction, and confirmed empirically:
  - **Oracle** `rung7_vision_bench.sh`: **214 passed / 10 skipped** BEFORE (HEAD
    `1421f951e2`) == AFTER.
  - **Regression** `per_area_settlement_regression.sh` (34-file): **23 failed /
    277 passed / 5 skipped**, the SAME 23 pre-existing baseline node ids BEFORE ==
    AFTER (recorded in `results/spite_regression_baseline_ids.txt`; all are
    conversation / topic-route / elaboration / gap-awareness / cortices tests,
    none touching this seed).
- **Gate** `tests/test_spite_to_succeed_migrated.py`: **5 / 5** passed.

## Honest bounds / residuals

- **The mechanism is a MODEL, not a measurement of real behaviour.** No human
  data; it re-derives the underdog / chip-on-shoulder motivation. The
  contribution is the glass-box attribution to a named integer knob and the
  efficacy-gates-channel unification of constructive vs destructive spite, not
  new social science.
- **Deterministic by construction.** The Argmax over integer candidates is exact;
  the CIs in G-succeed come from the pre-registered slight-severity distribution
  (`m ~ U{8..16}`), not from stochastic dynamics. The uplift is a clean closed
  form (`output = 4 + ⌊G/2⌋`), not a noisy effect — a feature of the glass box,
  stated plainly.
- **`efficacy` here is a fixed exogenous knob**, not yet updated by outcomes
  (win → efficacy up, loss → down). The channel therefore does not *evolve* over a
  history — that dynamic is a named follow-on (§8 of the prereg).
- **Single rival.** Per-target grievance is built (the accumulator is per
  `Grievance` node), but the measurements use one rival; grudge vectors / transfer
  across rivals are a named follow-on.
- **The uplift is bounded by EMAX** (effort caps at 14): a very large grievance
  saturates rather than growing without limit — honest and intended.

## Files

- `seeds/grievance_succeed.json` — the seed (4 rules; emitted by
  `tools/build_grievance_seed.py`).
- `domains/achieve_world.py` — mechanical world adapter.
- `scripts/spite_to_succeed_measure.py` — powered measure → `results/spite_to_succeed.json`.
- `tests/test_spite_to_succeed_migrated.py` — the gate (5/5).
- `SPITE_TO_SUCCEED_PREREG.md` — pre-registration (committed alone).
