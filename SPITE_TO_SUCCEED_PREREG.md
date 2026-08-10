# SPITE-TO-SUCCEED — grievance as a driver of the agent's OWN achievement (PRE-REGISTRATION)

*Committed ALONE, BEFORE any implementation and BEFORE any measurement.
Isolated worktree reset to `main` HEAD **`1421f951e2`** (LEDGER 212000 — has
204000 `core_emotions`, 207000 `drives`/`modulators`, 212000 `harvest`). Engine
canonical **`793ce09ed498a749abb79aeaea44b92e`** (`_native.abi3.so`, shared
build; Rust source identical to this worktree — `source_match` to be reported).
This rung adds **NO Rust** (`term.rs` diff EMPTY, whole `runners/dsl` diff EMPTY)
and **ONE new `self_load_only` seed** (`seeds/grievance_succeed.json`) plus a
mechanical world adapter + measure. Seed block **215000–215999**
(`default_rng`/derived seeds at the block base).*

Seed-claim check (verbatim, run before any number):

```
$ python3 scripts/seed_claim.py 215000 215999
SEED CLAIM 215000-215999: CLEAN -- no collision DETECTED.
  Scope: 914 files with seed sinks; 617 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

---

## 0. FRAMING — the CONSTRUCTIVE face of spite; a glass-box named-knob model, NOT new psychology

Destructive spite (Hamilton; block 213000's `w_spite`) is **harm-the-other-at-
self-cost**: you pay to lower a rival, your own achievement falls. **Spite-to-
succeed is nearly its INVERSE.** A **grievance** — an appraised slight / doubt /
dismissal / being-bested by a *specific* other — AMPLIFIES the value of the
agent's **OWN** competence and achievement, especially achievement measured
against / witnessed by the doubter. The reward is **VINDICATION** ("I showed
them"). It is:

- **self-BENEFITING** — you achieve MORE (own output rises); you do not pay to
  destroy (distinct from destructive spite, whose own output falls);
- **directed** — aimed at surpassing the *specific* rival's benchmark, witnessed
  by them; not a blanket effort increase against everyone;
- **developing** — an integer accumulator built from the slight that DECAYS via
  the 196000 scale2 (`Ashr`, ×2⁻ᵏ) half-life law; a held grudge = slow decay.

This re-derives the **underdog / chip-on-the-shoulder / "living well is the best
revenge"** achievement motivation (behavioural-econ underdog effect; social
comparison; the spite literature's constructive pole). **The contribution is NOT
the phenomenon** (it is well known). It is the **glass-box, gated, named-knob
instantiation on the substrate's OWN landed value economy** (204000
`core_emotions`: `total_value = happiness + fulfilment`), so the achievement
uplift can be **ATTRIBUTED to a named integer knob** (grievance magnitude), and
— the unifying claim — the SAME grievance is shown to channel into SUCCEED vs
DESTROY gated by **EFFICACY** (competence-belief / whether a viable path to win
exists). No human data; every gate reports the straight null if it fails.

---

## 1. THE ARCHITECTURE INVARIANT — every agent decision is a RULE (load-bearing)

`CLAUDE.md` is the hard constraint. The world is a mechanical Python adapter
(I/O only). **Every agent decision is graph-native, integer, idempotent** (the
engine settles `run_rules` to a fixed point, so every effect is a pure SET, never
an accumulating ADD; statefulness across ticks lives in immutable `Slight` nodes
+ the adapter-advanced `now_epoch`):

| decision | WHERE it lives | mechanism |
|---|---|---|
| how big is the grievance | rule `gs_grievance_from_slights` | `magnitude = Σ_{slight} Ashr(slight.magnitude, (now_epoch − slight.epoch)/half_life)` — a leaky accumulator = sum of scale2-decayed slight contributions; idempotent (pure fn of immutable slights + epoch) |
| how much to amplify OWN success | rule `gs_amplify_succeed` | per succeed candidate `c`: `amp(c) = G · max(0, effort − rival_ach) · observed_by_rival`, gated on `efficacy ≥ 5` — the vindication of surpassing the specific rival, witnessed, scaled by grievance |
| the destructive alternative | rule `gs_amplify_destroy` | per destroy candidate `c`: `amp(c) = G · rival_harm`, gated on `efficacy < 5` — the spite value of harming the rival (self-costly) |
| which action | rule `gs_choose_action` | `chosen = Argmax_c ( total_value(c) + amp(c) )` over the agent's candidates — the LANDED `total_value` (204000) plus the grievance amplification; the decision is the existing Argmax, unchanged in kind |

`total_value` is computed by the **unchanged** 204000 `core_emotions` rules
(`happiness = individual_benefit − individual_cost + mood_bias`;
`fulfilment_value = [w>0]·supergraph_contribution + mood_bias`;
`total_value = happiness + fulfilment`). This seed does **not edit** the 204000 /
207000 / 212000 seeds; it composes a NEW seed on top. The adapter publishes the
task mechanics (per-effort benefit/cost, rival standing, witness bit) as
full-information observations, `run_rules()`, and reads `chosen_action` off the
graph. **Source-audit to be reported** (G-graph-native): no `graph_rewrite.run` /
`gr.run` / `_match` / `_apply` / `make_rule`; no Python `if/else` over agent state
that selects an agent action.

---

## 2. THE TASK (mechanical adapter, integer-native, FROZEN constants)

A single-agent **achievement** task; a specific **rival** has a fixed standing and
delivers the slight. The agent chooses among candidate Appraisals:

- **Succeed candidates** — effort `e ∈ {0 … EMAX=14}`:
  `individual_benefit = B·e` (`B = 8`, linear output utility),
  `individual_cost = e²` (convex effort cost, published),
  `output = e` (competence produced), `rival_harm = 0`,
  `observed_by_rival ∈ {0,1}`, `rival_ach` (the rival's standing).
- **Destroy candidates** — sabotage `s ∈ {1 … SMAX=6}`:
  `individual_benefit = −s` (pure self-cost), `individual_cost = 0`,
  `output = 0`, `rival_harm = s`.

The base economy (no grievance, `w_supergraph = 0`) gives
`total_value(succeed e) = 8e − e²`, maximised at **e = 4** (the un-slighted
baseline), and `total_value(destroy s) = −s < 0` (never chosen). **`rival_ach`
is FROZEN at 4** = the baseline optimum: the un-slighted agent exactly TIES the
rival and never sabotages.

**Grievance knobs (FROZEN):** `EFF_THRESH = 5`; `efficacy ∈ {0 … 10}` (HIGH ⇔ ≥5,
a viable path to win; LOW ⇔ <5, no path). Half-life `H ∈ {1 (fleeting), 4
(moderate, default), 16 (held grudge)}` epochs. A `Slight{magnitude m, epoch}`
is the dose. All constants above are fixed by this prereg (piloted, then frozen).

**Closed-form the mechanism predicts** (high efficacy, witnessed, grievance `G`):
the vindicated optimum is `e* = 4 + ⌊G/2⌋` (capped at EMAX): `d/de[8e − e² +
G·(e − 4)] = 0 ⇒ e = 4 + G/2`. So **one extra unit of effort per +2 grievance** —
a clean linear dose-response — and own output rises 4 → e* > 4 (self-benefiting,
surpassing the rival's 4). This closed form is a REGISTERED prediction, checked
exactly against the graph's Argmax.

---

## 3. G-succeed (HEADLINE) — a slighted agent OUTPERFORMS an un-slighted control

**Design.** Paired arms over **N = 200** seeded rivals; run `r` seeded
`215000 + r` (max 215199, in-block). Per pair draw `rival_ach ~ U{3,4,5}` and, for
the slighted arm, slight magnitude `m ~ U{8 … 16}` (severity varies — realistic),
`efficacy = 10`, `observed_by_rival = 1`, measured at the slight's own epoch
(no decay). Arms (paired on the rival draw):

- **control** — no slight (`m = 0`);
- **slighted** — one slight of magnitude `m`, witnessed;
- **slighted-unwitnessed** (directedness control) — same slight, `observed_by_rival = 0`.

Metrics per agent, read off the graph: **own output** (chosen `output`),
**rival_harm** (chosen), **chosen kind** (succeed/destroy). Report mean + **95% CI**
(bootstrap, 2000 resamples); paired uplift = `output_slighted − output_control`.

**Registered predictions.** (i) slighted mean output **> control** (= 4),
CI-separated; mean paired uplift ≈ `⌊m/2⌋` ≈ **+6**, CI excludes 0. (ii)
**self-benefiting:** the slighted agent's chosen `rival_harm = 0` and its own
output RISES — it does not harm the rival (distinct from destructive spite).
(iii) **directed:** the slighted-**unwitnessed** arm shows **no uplift** (output ≈ 4,
CI overlaps control) — the amplification is contingent on being witnessed by the
specific rival, not a blanket effort increase. (iv) attributable to the grievance
knob (the only varied input). **G-succeed is REFUTED if** slighted and control are
not CI-separated on output, OR the slighted agent's uplift comes with `rival_harm > 0`
(that would be destruction, not constructive success).

---

## 4. G-develops — the grievance BUILDS from the slight and DECAYS via the scale2 law

**Dose-response (deterministic, exact).** High efficacy, witnessed, single fresh
slight at its epoch: sweep `m ∈ {0,2,4,…,20}`; record `G` and chosen output.
**Registered:** `G = m` (fresh, undecayed) and `output = min(EMAX, 4 + ⌊m/2⌋)` —
strictly monotone; `m = 0 ⇒ output = 4` (no slight → no amplification). **Repeated
slights accumulate:** 1 / 2 / 3 slights of `m = 6` at the same epoch → `G = 6/12/18`
→ output `7/10/13`.

**Decay (the 196000 scale2 half-life law).** Fix one slight `m = 16` at epoch 0;
advance `now_epoch = 0 … 20`; for each `H ∈ {1, 4, 16}` record `G(epoch)` and
output. **Registered:** `G(t) = 16 >> ⌊t/H⌋` — an integer halving every `H`
epochs (`H=1` fleeting: `16→8→4→…→0`; `H=16` held grudge: stays 16 through epoch
15, then 8). The held grudge keeps output elevated far longer than the fleeting
one. **G-develops is REFUTED if** output does not increase monotonically with `m`,
OR `G` does not halve on the `H`-epoch schedule, OR a zero slight yields any uplift.

---

## 5. G-channel (HEADLINE / REACH — the unifying structure) — EFFICACY gates SUCCEED vs DESTROY

**The same grievance, two channels, one knob.** Fix a witnessed grievance
(`m = 12`, `observed_by_rival = 1`, epoch 0, `G = 12`) and sweep
`efficacy ∈ {0 … 10}`, reading the graph's chosen action:

- **HIGH efficacy (≥ 5, a viable path to win):** `gs_amplify_succeed` fires,
  `gs_amplify_destroy` does not → the grievance amplifies OWN achievement →
  chosen kind = **succeed**, output = `4 + ⌊12/2⌋ = 10`, `rival_harm = 0`
  (self-benefiting).
- **LOW efficacy (< 5, no path):** `gs_amplify_succeed` is gated OFF,
  `gs_amplify_destroy` fires (`amp = G·rival_harm = 12·s`) → the best destroy
  candidate `s = 6` scores `−6 + 12·6 = 66 > 16` (best succeed) → chosen kind =
  **destroy**, output = 0, `rival_harm = 6` (self-costly; ties 213000's harm-
  the-other-at-self-cost).

**Registered prediction.** The chosen kind FLIPS from succeed to destroy as
efficacy crosses the threshold (succeed for efficacy ≥ 5, destroy for < 5, at this
`G`); own output and rival_harm move in opposite directions across the flip.
**This is the reach:** if the flip does not land cleanly (e.g. the destroy channel
does not win at low efficacy for realistic `G`), we **land G-succeed + G-develops
and NAME the channel structure** as the follow-on, reporting the straight result.

---

## 6. G-psi — it amplifies the COMPETENCE valuation, triggered by an honour/legitimacy blow (PSI-native)

The slight is an **anti-legitimacy / honour blow** (a specific other's doubt /
dismissal — the same appraisal class as 207000 `drive_affiliation_legitimacy`).
Spite-to-succeed **COMPOSES existing machinery**: `gs_amplify_succeed` re-weights
the agent's OWN **competence/achievement** candidates (the `B·e` output valuation
already in the 204000 economy) — it adds NO new terminal drive. This is the
PSI-native contrast to terminal **destructive** spite (a standalone harm-the-other
value with no antecedent drive — a PSI gap). **Where the amplification lives:**
stated exactly (the `gs_amplify_succeed` term raising the value of high-competence
candidates in proportion to the grievance), so the reweighting is a named,
inspectable graph term, not a hidden parameter.

---

## 7. G-graph-native + G-discipline (gates, load-bearing)

- **G-graph-native:** source audit of the adapter proving every agent decision is
  a rule and the adapter is mechanical I/O only. Reported with the exact location
  of each decision (table §1) and a grep for the forbidden calls.
- **Integer-native:** all agent-decision math uses the integer subset
  (`Plus/Minus/Times/IDiv/Ashr/Max/Min/IfThenElse/Eq/Gt/Gte/And/Or/Not/Sum/Argmax`);
  every literal a whole number (checked by the gate test).
- **Default-OFF / new-world-isolated byte-identity:** `grievance_succeed.json` is
  `self_load_only:true` (skipped by `load_all_seeds`; nothing `depends_on` it), so
  the existing tree is **byte-identical with it absent** — demonstrated by the
  unchanged oracle + regression node-id sets and a `_read_seeds` absence check.
- **Canonical `.so` md5 stays `793ce09ed498a749abb79aeaea44b92e`**; **`term.rs`
  diff EMPTY**, **whole `runners/dsl` diff EMPTY** (NO Rust; if a primitive seemed
  needed I STOP and report — it is not: `Sum`, `Ashr`, `Argmax`, `Gte`, `Max`,
  `Not` all already exist in the canonical build).
- **Oracle** `bash scripts/rung7_vision_bench.sh` BEFORE == AFTER
  (BEFORE = 214 passed / 10 skipped, captured at HEAD `1421f951e2`).
- **Regression** `bash scripts/per_area_settlement_regression.sh` (34-file)
  BEFORE == AFTER (compared as the SET of failing node ids, never a count).
- **`source_match`** (Rust source vs the canonical build) reported.

---

## 8. NAMED FOLLOW-ONS (explicitly NOT built here)

- **per-target grievance vectors** — many rivals, distinct grudges, and grudge
  transfer / generalisation across rivals;
- **the efficacy DYNAMICS** — efficacy itself updated by outcomes (a win raises it,
  a loss lowers it), so the succeed↔destroy channel shifts over a history;
- **grievance → sub-goal planning** (instrumental "train to beat them", not just a
  one-shot effort bump);
- **the social version** — a slighted agent inside the 212000 HARVEST commons
  out-competing the peer who doubted it (grievance meets the shared-pool economy);
- **recovering the grievance knob from behaviour** (206000-style inverse inference
  on an achievement transcript).

A solid G-succeed + G-develops landing, an honest G-channel result, and these
named is the target — better than a sprawling half-verified everything.
