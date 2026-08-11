# ARC 6 — A14: THE IMPOTENCE CAMPAIGN — measuring (a) vs (b), before building either

**Date:** 2026-08-11
**Bars:** `PROGRAM_SYNTHESIS_ARC6_PREREG.md` **amendment A14** (`IC1`–`IC4`),
registered **before** this measurement.
**Base commit:** `e48e117` (detached worktree `/home/matt/arc6-impotence-campaign`).
**Engine:** `953b8e3fa6471a285f5e4d5fb731a721667ecf6e4fffba1f3feca52b96683a85` —
the SAME committed binary A13 measured on; `git status` never lists it as
modified in this worktree (only its mtime needed a `touch`, see §7.1 — sha256
unchanged before/after). Coherence probe passed before every measurement:
`add_node("T", {"lst":[1,2,3], "tup":(1,2,3)})` reads back `[1,2,3]` and
`(1,2,3)` **distinctly**.
**Seed:** `seeds/arc_executor.json` v1.2.0, sha256
`49aa286f4d76999ebcadc47d6065f05b879257a3a2aa4bc7f7aabceb14ee83b5` — **byte-
identical to A13's own**, and to `HEAD`. **This rung edits zero seeds and
zero adapters** — `git diff --stat HEAD -- seeds/ domains/ tools/ tests/
runners/` is empty throughout.
**Artifact:** `results/arc6_impotence_campaign.json` (engine + seed stamped;
every scene is a live boot, mutation and `run_rules()`, not a fixture
replay; two scenes are REAL live remeasurements, ~142s and ~144s).
**Gate:** unchanged from A13 — `tests/test_arc_executor_migrated.py` **50
collected, 49 green**, plus the other four ARC-6 suites, all measured fresh
in this worktree before touching anything (§4); no seed/adapter edit in this
rung, so those numbers stand as both the before- and after-arm.

**SCOPE: the measurement campaign only.** Per A14's own registered null
reading, **nothing was built**: the concentration/spread bar (`IC2`) reads
AMBIGUOUS / AMBIGUOUS-underpowered on every view measured, so `IC3`'s
compound GO/NO-GO test is not met for either candidate (a) or (b). This is a
complete, valuable result under this arc's own standing culture of clean
nulls (M0's four ceiling probes, the D-seam leave-one-out) — not a failure
to find something to build.

---

## 0. VERDICTS

| bar | verdict | what it rests on |
|---|---|---|
| **IC1 — the sweep's own methodology is sound and reproducible** | **PASS** | every scene is a REAL live execution (2, order-1 and order-N), the SAME `headroom_n → 0` pool-exit A13 §7.1 validated, or a real `attach_reply` — never a hand-faked `AgendaVerdict`, never `status → 'retired'`, never an edited `ArcGoalPolicy` weight, never an invented `ArcGoal.kind`. Hypothetical scenes (groups 3–4) are labelled as such and never merged into the real/natural-trajectory statistic without saying so. Twin-run determinism: **byte-identical**. §2 |
| **IC2 — concentration/spread threshold, applied as registered** | **AMBIGUOUS / AMBIGUOUS-underpowered on every view** | real-only: 2 distinct live states (1 `supply_blocker`, 1 `source_claim`) — `n=2 < 5`, **AMBIGUOUS-underpowered**. real+hypothetical: 10 distinct live states, modal `source_claim` at fraction **0.6** — inside `(0.50, 0.75)`, **AMBIGUOUS** (neither CONCENTRATED nor SPREAD by the registered thresholds). §3, §5 |
| **IC3 — GO/NO-GO for building (a) or (b)** | **NO-GO for both** | GO-for-(b) requires IC2 CONCENTRATED on the real-only subset — not met. GO-for-(a) requires IC2 SPREAD on the real-only subset — not met (real-only reads AMBIGUOUS-underpowered, not SPREAD, regardless of its raw 0.5 fraction, because `n<5` is checked first per the registered formula). **Neither compound condition holds. NO-GO for both, exactly the registered null-reading path.** §6 |
| **IC4 — no regression** | **PASS, trivially and by construction** | this rung edits **zero** seed and **zero** adapter file (`git diff --stat HEAD -- seeds/ domains/ tools/ tests/ runners/` empty throughout) — the five-suite baseline measured fresh in this worktree (§4) stands unchanged as both the before- and after-arm. Same two pre-existing, environment-conditional reds as every prior ARC-6 rung, same node ids. |

**The one thing worth reading if you read nothing else.** The campaign found
something A12/WH4's own priors did not anticipate: the "obvious" supply-side
dominance (`missing_structural_primitive`'s headroom of 42 makes
`supply_blocker` look like the concentrated answer) **does not survive
contact with the actual `VALUE` term.** `PENALTY` — not headroom — turns out
to dominate for two of the three `supply_blocker` goals (`budget`,
`missing_dimension` are penalised down near the `source_claim` goals' level
even with **zero** testimony in the scene), so once the one routable goal is
gone, "which kind is nearest-unroutable" is close to a coin flip between
`supply_blocker` and `source_claim` — and a **discovered, unregistered**
mechanism (§8) means the graph's own **stored** `AgendaVerdict` cannot even
see that coin flip once it has happened once.

---

## 1. WHAT WAS BUILT

**Two files: the measurement script and its artifact. Nothing else.**

```
scripts/arc6_impotence_campaign_measure.py   NEW -- the sweep runner, 4
                                              scene groups + aggregation
results/arc6_impotence_campaign.json         NEW -- the artifact, engine +
                                              seed stamped
PROGRAM_SYNTHESIS_ARC6_PREREG.md             amendment A14 appended (bars
                                              registered BEFORE the sweep
                                              ran)
PROGRAM_SYNTHESIS_ARC6_IMPOTENCE_CAMPAIGN.md this file
```

No `.rs`, no `seeds/*.json`, no `domains/*.py`, no `tools/*.py`. The
measurement runs entirely through mechanisms A13 and its predecessors
already shipped: `axe.agenda_verdicts` (the pure read-off), `headroom_n → 0`
(A13 §7.1's validated pool-exit), `agi.attach_reply` (the adapter's own
testimony translation), `axe.run_order` (the adapter's own dispatch).

---

## 2. IC1 — THE SWEEP METHODOLOGY

`results/arc6_impotence_campaign.json` — four scene groups, all live:

- **GROUP 1 (real, 2 scenes).** One live execution under order-1 (a
  conditioned reply, the `live_run` gate fixture's own recipe) and one under
  order-N (silent, the WH2 arm's own recipe) — **real ~142s / ~144s
  remeasurements**, not fixtures. Both retire the sole routable goal for
  real: pool 8 → 7, and `ax_impotent` fires afterward in both, naming
  `supply_blocker` (`missing_structural_primitive`) as
  `nearest_unroutable_kind` — reproducing A13's own IM1/IM4 findings on a
  fresh boot.
- **GROUP 1s (synthetic cross-check, 2 scenes).** The identical post-
  execution pool, reached via `headroom_n → 0` instead of a live
  measurement — confirms the synthetic technique reproduces what the real
  executions reach, so groups 2–4 do not need to re-run the ~140s
  measurement to explore further variation.
- **GROUP 2 (real, testimony chains, 2 × up to 6 replies).** Starting from
  the synthetic 7-goal pool, `attach_reply` (unconditioned) sent to whatever
  `ArcQuestion` is currently open, repeated. **This is a real mechanism** —
  the SAME `agi.attach_reply` / `gr_move_penalty` machinery AG-5 EX5 arm 2
  and WH2 already exercised — reweighting the pool WITHOUT changing its
  membership.
- **GROUP 3 (HYPOTHETICAL, 8 scenes).** A depletion ladder beyond the loop's
  own reach: `headroom_n → 0` applied to goals nothing in this tree can
  currently retire unaided (`supply_blocker` / `source_claim` goals), one at
  a time, down to an empty pool. Labelled hypothetical throughout — see §5.1.
- **GROUP 4 (HYPOTHETICAL, the 4th kind).** A `SelfConcern` node added
  directly and wired via `has_self_concern` — `ag_mint_self_concern` (a
  real, existing rule, not invented) mints an `ArcGoal{kind:'reported'}`
  from it. Confirms the kind-space's 4th member is real and mintable, and
  is not naturally present without the separate gap-awareness pipeline.

**Determinism.** `twin_run_determinism.byte_identical: true` — the group-1s
order-1 synthetic scene, run twice independently, produces byte-identical
`AgendaVerdict` content.

**Nothing hand-faked.** No `AgendaVerdict` node was ever constructed
directly; every one read back in the artifact was minted by `ax_impotent`
itself, live, in response to a real boot/mutation/`run_rules()` sequence.

---

## 3. THE RAW PER-SCENE TABLE — a list, never a bare count

Every distinct **live state** reached (pool signature × live winner kind,
the corrected view — §8), REAL scenes first, HYPOTHETICAL scenes after,
never merged silently:

| # | group | scene | pool_n | mechanism | live winner agid | kind |
|---|---|---|---|---|---|---|
| 1 | 1 (real) | order-1, conditioned reply, **real 142.47s execution** | 7 | live execution | `…missing_structural_primitive` | `supply_blocker` |
| 2 | 1 (real) | order-N, silent, **real 143.64s execution** | 7 | live execution | `…missing_structural_primitive` | `supply_blocker` |
| 3 | 1s (real) | order-1, synthetic cross-check | 7 | `headroom_n→0` | `…missing_structural_primitive` | `supply_blocker` |
| 4 | 1s (real) | order-N, synthetic cross-check | 7 | `headroom_n→0` | `…missing_structural_primitive` | `supply_blocker` |
| 5 | 2 (real) | order-1 chain, reply 0 | 7 | (same pool as 1/3) | `…missing_structural_primitive` | `supply_blocker` |
| 6 | 2 (real) | order-1 chain, reply 1 | 7 | 1 unconditioned reply | `…budget` | `supply_blocker` |
| 7 | 2 (real) | order-1 chain, reply 2–4 (fixed point, 0 open q. after reply 3) | 7 | 2 more unconditioned replies | `arc6.claim.seam_b…` | `source_claim` |
| 8 | 2 (real) | order-N chain, reply 0 | 7 | (same pool) | `…missing_structural_primitive` | `supply_blocker` |
| 9 | 2 (real) | order-N chain, reply 1 | 7 | 1 unconditioned reply | `…budget` | `supply_blocker` |
| 10 | 2 (real) | order-N chain, reply 2–4 (fixed point) | 7 | 2 more unconditioned replies | `arc6.claim.seam_b…` | `source_claim` |
| — | **dedup (pool-sig × kind)** | rows 1–10 collapse to **2 distinct live states**: `(7-pool, supply_blocker)`, `(7-pool, source_claim)` | | | | |
| 11 | 3 (HYPOTHETICAL) | remove `row_verdict_seed_only` | 7 | `headroom_n→0` | `…missing_structural_primitive` | `supply_blocker` |
| 12 | 3 (HYPOTHETICAL) | + remove `missing_structural_primitive` | 6 | `headroom_n→0` | `…budget` | `supply_blocker` |
| 13 | 3 (HYPOTHETICAL) | + remove `budget` | 5 | `headroom_n→0` | `arc6.claim.seam_b…` | `source_claim` |
| 14 | 3 (HYPOTHETICAL) | + remove `missing_dimension` | 4 | `headroom_n→0` | `arc6.claim.seam_b…` | `source_claim` |
| 15 | 3 (HYPOTHETICAL) | + remove `seam_b` | 3 | `headroom_n→0` | `arc6.claim.seam_d…` | `source_claim` |
| 16 | 3 (HYPOTHETICAL) | + remove `seam_d` | 2 | `headroom_n→0` | `arc6.claim.tier0…` | `source_claim` |
| 17 | 3 (HYPOTHETICAL) | + remove `tier0` | 1 | `headroom_n→0` | `arc6.claim.valuelayer…` | `source_claim` |
| — | 3 (HYPOTHETICAL) | + remove `valuelayer` → **empty pool** | 0 | `headroom_n→0` | (excluded — done, not impotent) | — |
| 18 | 4 (HYPOTHETICAL) | `SelfConcern` added, full 9-goal pool | 9 | real rule, injected node | `…missing_structural_primitive` | `supply_blocker` (unchanged — `reported` does not outrank it) |
| 19 | 4 (HYPOTHETICAL) | everything else depleted, `reported` sole survivor | 1 | `headroom_n→0` ×8 | `arc.concern.campaign_probe_concern` | `reported` |
| — | **dedup, all 19 rows** | **10 distinct live states**: `supply_blocker` ×3, `source_claim` ×6, `reported` ×1 | | | | |

`exec_classes_held` is **`["re_measure"]`** on every single verdict across
every scene — it is a property of the SEED (how many `ExecClass` nodes
exist), not of the pool, and therefore carries **zero** information about
concentration vs spread. `nearest_unroutable_kind` is the only field that
does the work, and only once read the corrected way (§8).

---

## 4. BASELINE — MEASURED FRESH, BEFORE TOUCHING ANYTHING

Per A14's process discipline, all five suites were run in this worktree
**before** the sweep script was written, on the engine above:

| suite | result | failing node ids |
|---|---|---|
| `test_arc_executor_migrated` | 49 passed, 1 failed (50 collected) | `test_ex1_the_frozen_artifacts_are_STILL_byte_identical` |
| `test_arc_goals_migrated` | 37 / 37 | — |
| `test_goal_residual_migrated` | 29 passed, 1 failed, 1 skipped | `test_gr4_the_live_mbpp_pass_ids_are_unchanged` |
| `test_arc6_valuelayer_migrated` | 35 / 35 | — |
| `test_arc_magnitude_migrated` | 43 / 43 | — |

**Identical to A13's own baseline table**, same two pre-existing,
environment-conditional reds, same node ids (`results/` untracked in this
checkout; the engine's short sha is not in `test_gr4`'s three-entry
allowlist — neither is this rung's to fix, per the task's own scope
constraints and A12/A13's prior identical findings). Because this rung
edits no seed and no adapter (§1), this table stands as **both** the before-
and after-arm of IC4 — re-running it a third time (after a fresh ~140s live
remeasurement) would measure nothing IC4 does not already have: `git diff
--stat HEAD -- seeds/ domains/ tools/ tests/ runners/` is empty.

---

## 5. IC2 — THE CONCENTRATION/SPREAD READ

Four views are reported, because the design investigation (§8) surfaced a
real defect in the most literal reading of the registered statistic:

| view | population | n | modal kind | fraction | read |
|---|---|---|---|---|---|
| by pool signature (as registered) | real-only | 1 | `supply_blocker` | 1.0 | AMBIGUOUS-underpowered (`n<5`) |
| by **stored** verdict kind (undercounts, §8) | real-only | 1 | `supply_blocker` | 1.0 | AMBIGUOUS-underpowered |
| by **live winner** state (corrected, §8) | real-only | **2** | `supply_blocker` | **0.5** | **AMBIGUOUS-underpowered** (`n<5`, checked before the fraction) |
| by pool signature (as registered) | real + hypothetical | 8 | `source_claim` | 0.625 | AMBIGUOUS |
| by **stored** verdict kind (undercounts) | real + hypothetical | 8 | `source_claim` | 0.625 | AMBIGUOUS |
| by **live winner** state (corrected) | real + hypothetical | **10** | `source_claim` | **0.6** | **AMBIGUOUS** |

**No view, under any reading registered in A14, crosses the 0.75
CONCENTRATED threshold.** The real-only subset — the one IC3's GO condition
for (b) actually keys off — is underpowered at `n=2`, and even at face value
its 1-vs-1 split is the least concentrated result two data points can show.
The extended (real+hypothetical) view leans toward `source_claim` (0.6) but
does not cross the 0.75 line either, and — because IC3's SPREAD condition
for (a) is keyed to the **real-only** subset specifically, not the
extended one — even a genuinely SPREAD extended reading would not by
itself satisfy GO-for-(a).

### 5.1 Real vs hypothetical, kept honestly separate

The REAL-only population (rows 1–10, table §3) is everything reachable
either by this loop's own current action or by a human answering a question
it already asks — no capability growth assumed. It collapses to exactly
**two** distinct live states because there is exactly **one** pool
composition this system can currently reach unaided (nothing here can
retire a `supply_blocker` or `source_claim` goal by itself), and testimony
only re-ranks within it. That collapse to `n=2` is not a sampling failure —
it is a structural fact about this system's CURRENT capability count,
registered in A14 §"design investigation" **before** the sweep ran. The
HYPOTHETICAL population (rows 11–19) exists to ask a different, forward-
looking question — "if this system could reach further pool compositions,
what would the kind-space look like" — and answers it: less concentrated
than a `headroom`-only reading of the shipped seed would have suggested
(§6), because `PENALTY` reshuffles two of the three `supply_blocker` goals
down near the `source_claim` goals' level (§8).

---

## 6. IC3 — THE GO/NO-GO CALL

**NO-GO for both (a) and (b).**

- **GO-for-(b)** required IC2 CONCENTRATED on the real-only subset. It read
  AMBIGUOUS-underpowered (`n=2`). **Not met** — condition (i) alone fails,
  so conditions (ii)/(iii) were not evaluated (there is nothing to weigh a
  registered risk against without a concentration finding to weigh it
  against).
- **GO-for-(a)** required IC2 SPREAD on the real-only subset. It read
  AMBIGUOUS-underpowered, not SPREAD — `n<5` is checked before the fraction
  in the registered formula, so the raw 0.5 split does not qualify as
  SPREAD any more than it qualifies as CONCENTRATED. **Not met.**

**Reported anyway, because it was measured and is informative even though
it does not change the call:** condition (ii) of GO-for-(a) — whether a
testimony chain about impotence reaches a fixed point rather than cycling —
**was measured favourably**. Both group-2 chains (order-1 and order-N)
stopped asking after 3 replies (`n_open_questions` reaches 0) rather than
cycling indefinitely between `supply_blocker` and `source_claim`
candidates. Had IC2 read SPREAD, this finding would have been relevant to
weighing (a)'s registered repricing-loop risk; since IC2 did not read
SPREAD, it is recorded as a side finding, not as a partial justification
for building (a) anyway.

**This is the registered null-reading path, stated in A14 before the sweep
ran: "If IC2 reads AMBIGUOUS, or if IC3's compound test is not met for
either candidate, this rung builds NOTHING beyond the measuring campaign
itself… and reports the concentration/spread read as the complete result."**
That is exactly what happened. Nothing beyond `scripts/
arc6_impotence_campaign_measure.py` and its artifact was built.

---

## 7. EVERYTHING THAT BROKE

Recorded because the process is the result — including two hazards this
rung tripped that A12/A13 had already named.

### 7.1 A false "STALE engine" refusal from git-worktree checkout mtimes

The first baseline run refused with `EngineProvenanceError: 84 .rs file(s)
are NEWER than the binary`. Not a real staleness — `git worktree add`
checks out every file (source and binary) at the same real time, and
ordering ties left some `.rs` mtimes a hair after the `.so`'s. Confirmed by
sha256: identical before and after a plain `touch` on the binary (no
rebuild, no content change), and `find … -newer` dropped from 84 hits to 0.
**Not the glibc/rustc mismatch A11 hit** — this binary already ran; only its
mtime needed correcting for the provenance check's own mtime heuristic.

### 7.2 I tripped A12.2's exact hazard a second time, on a **different**
worktree, and the recovery followed A12.2's own playbook exactly

A12.2 registered: *"never run a suite containing a tree-mutating fixture
under a timeout shorter than the fixture."* Despite having just read that
paragraph, the first attempt to run the five baseline suites used the Bash
tool's **default 2-minute timeout** — shorter than the `live_run` fixture's
~140s. The timeout `SIGKILL`ed the pytest process mid-way through the ONE
`re_measure` remeasurement, and the runner's `finally` never ran, leaving:

- `seeds/program_synthesis.json` **patched** in this worktree (the
  `row_verdict_seed_only` comparator swap left applied), and
- `results/arc6_verdict_before.json` **overwritten** — in the **canonical**
  `/home/matt/ozmadev/ocelot/results/`, via this worktree's symlinked
  `results/` (§7.4 of `PROGRAM_SYNTHESIS_ARC6_WIRE_HANDS.md` names exactly
  this exposure).

**Recovery, verified by sha256, no guessing:**

1. `seeds/program_synthesis.json` — restored via `git checkout --` in this
   worktree (it is tracked; git is authoritative). Confirmed
   `4e866340eb509ed…`, matching the pristine value A12.2 itself recorded.
2. `results/arc6_verdict_before.json` — the runner's own crash stash
   survived at `/tmp/arc6_remeasure_v2ug4sp3/` (created before the run
   started, per `arc6_remeasure_row_verdict.py`'s own `tempfile.mkdtemp`).
   Its `arc6_verdict_before.json` hashed `ed90bf281bd8dc812a…` — **identical**
   to an independent, older stash (`/tmp/arc6_remeasure_1oiko27u/`, dated
   00:54, left over from a prior rung's own A12.2 recovery) — two
   independent stashes from different times agreeing on the same sha is
   strong corroboration this is the true pristine value, not a guess. Copied
   back; the canonical tree's `results/arc6_verdict_before.json`,
   `arc6_verdict_after.json` and `arc6_verdict_pricing.json` all verified at
   their documented pristine shas (`ed90bf28…` / `db47ad2c…` / `1815d381…`,
   the exact values `PROGRAM_SYNTHESIS_ARC6_WIRE_HANDS.md` §9 quotes) after
   the fix.

**Both trees verified clean before any further measurement**: this
worktree's `git status --porcelain` shows only the intended amendment edit
and the two symlinks; the canonical tree's `git status --porcelain` was
re-checked and shows only pre-existing, unrelated `docs-reorg` files this
rung never touched. No measurement in this document's §2–§6 ran during the
damaged window — the baseline table (§4) is a clean, subsequent run.

**What this adds to A12.2's own registered rule, rather than just
repeating it**: the hazard fired on the **default tool timeout**, not a
deliberately-chosen short one — meaning any tooling layer that wraps a
tree-mutating measurement with an unreviewed default timeout is an attacker
by default, not only under a mistaken explicit `--timeout`. Every
subsequent invocation of `test_arc_executor_migrated.py` in this rung used
an explicit, generous timeout (480s) specifically because of this.

### 7.3 The registered statistic needed a mid-measurement correction — see §8

Not a process hazard, but a genuine defect in the first cut of the
aggregation, caught by inspecting the raw data rather than trusting the
summary number. Detailed in §8 because it is itself a finding about
`ax_impotent`, not just a script bug.

---

## 8. THE DISCOVERED, UNREGISTERED FINDING: THE STORED VERDICT FREEZES AT MINT

Not anticipated by A14 (the bars register the sweep's methodology and
thresholds, not this). Found by reading the group-2 chain's raw per-step
data rather than trusting the first aggregate number, which read `n=1` for
the real-only subset — implausibly small given the chain visibly moved the
winner from `missing_structural_primitive` to `budget` to `arc6.claim.seam_b`.

**The mechanism.** `ax_impotent` mints once per **pool signature**
(`pool_agids`, IM5's own registered mint-once unit). A `attach_reply` that
moves the **live winner** (via `gr_move_penalty`, the same mechanism AG-5
EX5 arm 2 measured) **without changing pool membership** does not produce a
new signature, so the mint guard correctly refuses to mint a second verdict
— and **nothing in this rule ever updates an existing node's attrs**. The
result: the **stored** `AgendaVerdict.nearest_unroutable_kind` freezes at
whatever `SEL_AGID` named at first mint, and does not track further ranking
drift under a constant signature.

**Measured directly, both collapses, reproduced twice:**

```
order-1 chain   live winner kind:    supply_blocker, supply_blocker, source_claim, source_claim, source_claim
                stored verdict kind: supply_blocker, supply_blocker, supply_blocker, supply_blocker, supply_blocker

order-N chain   live winner kind:    supply_blocker, supply_blocker, source_claim, source_claim, source_claim
                stored verdict kind: supply_blocker, supply_blocker, supply_blocker, supply_blocker, supply_blocker
```

**Why this is not a bug in IM5's bar.** Mint-once-by-pool-signature is
*exactly* what A13's IM5 registered and gated, and it is the right anti-
flooding guard for the case it was built for (an unchanged pool re-running
`run_rules()` should not double-mint). This is a **previously unmeasured
consequence** of that correct design, surfaced only because this campaign
needed to read `nearest_unroutable_kind` across a sequence of testimony
replies — a use IM5's own scenes never exercised, because IM5 never chained
replies through an already-impotent pool.

**Consequence for this campaign's own statistic, stated in the open.** The
"as registered" reading of IC2 (dedup by stored `pool_agids` +
`nearest_unroutable_kind`) systematically **undercounts** — it would have
read the group-2 chains as contributing exactly **one** state each
(`supply_blocker`, frozen), hiding the very ranking-drift dynamic the
testimony axis was built to probe. The corrected view (`_live_states`, §3)
recomputes the winner **live** at each step, the same way `SEL_AGID` itself
is defined, bypassing the frozen node. Both readings are reported in the
artifact and in §5's table; the corrected one is the one IC2/IC3's verdicts
above are read from, and the difference between them (real-only: `n=1` →
`n=2`) is itself part of this rung's result, not a footnote.

**Consequence beyond this campaign, named and not built against (out of
scope, per the task's own constraints — this rung measures, it does not
extend `ax_impotent`).** A human reading the agent's own held knowledge
after a testimony exchange would see a stale `nearest_unroutable_kind` that
no longer matches what the collapse currently believes, with `stale: 0.0`
still asserting it is current. This is a sibling of A13's own registered
uncertainty #1 ("a verdict's condition lapses on epoch advance only, not on
pool composition drift") — but sharper, because this drift needs **no**
composition change and **no** epoch advance at all, only a reply.

---

## 9. REMAINING UNCERTAINTIES

Ordered by how much damage being wrong would do.

1. **The `VALUE` term's `PENALTY` component was not reverse-engineered.**
   This campaign measured, empirically, that `budget` and
   `missing_dimension` are penalised far below their raw headroom
   (`7`/`4`) — down near `source_claim`'s `-25`-ish level — **even with
   zero testimony in the scene** (§3, rows 12–13's precursor probe). Why
   specifically those two supply_blocker goals and not
   `missing_structural_primitive` was not traced into `gr_move_penalty`'s
   own term tree; this campaign treats it as an honest empirical fact about
   the shipped `ArcGoalPolicy`, not a mechanism it explains. A wrong guess
   about the mechanism would not change any measured number above, but
   would change how confidently a future rung could predict a NEW goal's
   rank without measuring it.
2. **The real-only subset is small (`n=2`) because this system currently
   has exactly one internally-reachable pool composition.** This is
   reported as a structural fact (§5.1), not a sampling shortfall to be
   fixed by more scenes of the same kind — more testimony replies against
   the SAME 7-goal pool cannot add a third distinct composition; only new
   capability (an execution route for a second `ExecClass`) or further
   hypothetical depletion can. The hypothetical extension (§3, rows 11–19)
   is exactly that, clearly labelled, but a reader who wants the **real-
   only** GO/NO-GO answer more powered has no way to get it without this
   system actually gaining a second executable capability — which is
   candidate (b)'s whole proposal, so the campaign cannot power its own
   real-only bar without partially pre-empting the question it is asking.
3. **`ag_ask` and `ax_impotent` still read different collapses in general**
   (A13's own uncertainty #5, unchanged, not built against here) — not
   observed to matter in any scene this campaign constructed (every
   impotent scene here has both `arc_sel_*` and `mg_sel_*`, where present,
   agreeing after the tier ladder settles), but not proven impossible
   either.
4. **The `reported` kind (group 4) is real but requires an out-of-seed-set
   construction** (a directly-injected `SelfConcern`, not the full gap-
   awareness pipeline). Its one contribution to the extended statistic
   (`n=1` of 10) should be read as "this kind exists and is mintable," not
   as evidence about how often it would actually appear on a graph that
   also loads gap-awareness — that composition was not measured.
5. **The re-arm deadlock (AG-5 §5) and the silent order-N fallback
   (WIRE_HANDS §8.1) were not touched**, per the task's explicit scope
   boundary. Neither was exercised by any scene in this campaign in a way
   that would have required touching them.
6. **§8's finding is reported, not repaired.** Whether the right fix is a
   second `ResidualCondition` kind keyed on drift-of-winner (which A13's own
   uncertainty #1 already named as requiring a `gr_condition_lapse`
   vocabulary change, explicitly out of that rung's scope and this one's) or
   something else was not designed here — this campaign's job was to
   measure, and it surfaced a genuine gap in what gets measured by the
   existing mechanism rather than to close it.

---

## 10. FILES

| file | what |
|---|---|
| `scripts/arc6_impotence_campaign_measure.py` | the sweep runner — 4 scene groups (2 real live executions, 1 synthetic cross-check pair, 2 testimony chains, a hypothetical depletion ladder, the `reported`-kind probe), the corrected `_live_states` aggregation (§8), IC2's concentration statistic |
| `results/arc6_impotence_campaign.json` | the artifact, engine + seed stamped, every scene's full trace |
| `PROGRAM_SYNTHESIS_ARC6_PREREG.md` | **amendment A14** appended, registered before the sweep ran |
| `PROGRAM_SYNTHESIS_ARC6_IMPOTENCE_CAMPAIGN.md` | this file |

**Nothing else changed.** `git diff --stat HEAD -- seeds/ domains/ tools/
tests/ runners/` is empty. `runners/dsl/python/substrate_rs/_native.abi3.so`
does not appear as modified (only its mtime was touched, §7.1; sha256
unchanged). `data` and `results` appear as untracked **symlinks** into the
canonical tree (39G / 21G, gitignored) — must not be staged. The canonical
tree `/home/matt/ozmadev/ocelot`'s own `git status --porcelain` is
unaffected by anything in this document, and was independently re-verified
clean after the §7.2 recovery.

---

## 11. REPRODUCE

```bash
# --- the worktree ---------------------------------------------------------
git worktree add --detach /home/matt/arc6-impotence-campaign e48e117
cd /home/matt/arc6-impotence-campaign
ln -s /home/matt/ozmadev/ocelot/data    data        # 39G, gitignored
ln -s /home/matt/ozmadev/ocelot/results results     # 21G, gitignored

# --- the engine.  Reproduces byte-identically to HEAD's committed binary on
#     this box.  If a git-worktree checkout leaves .rs mtimes racing the
#     .so's (SS7.1 -- a false "STALE" refusal, content unaffected), touch it:
touch runners/dsl/python/substrate_rs/_native.abi3.so
sha256sum runners/dsl/python/substrate_rs/_native.abi3.so
#   953b8e3fa6471a285f5e4d5fb731a721667ecf6e4fffba1f3feca52b96683a85

# --- the coherence probe.  STOP if these read back the same. --------------
PYTHONPATH=runners/dsl/python:. python3 -c "
import substrate_rs as srs; s=srs.Substrate()
a=s.node(s.add_node('T',{'lst':[1,2,3],'tup':(1,2,3)}))['attrs']
print(a['lst'], a['tup'], a['lst']!=a['tup'])"

# --- the baseline, BEFORE touching anything -- ALWAYS an explicit generous
#     timeout: the live_run fixture takes ~140s and a killed run leaves the
#     tree dirty (SS7.2). --------------------------------------------------
for s in test_arc_executor_migrated test_arc_goals_migrated \
         test_goal_residual_migrated test_arc6_valuelayer_migrated \
         test_arc_magnitude_migrated; do
  COLUMNS=250 OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
    PYTHONPATH=runners/dsl/python:. timeout 480 \
    python3 -m pytest tests/$s.py --confcutdir=$PWD -q -p no:randomly -rf
done

# --- the sweep (two REAL ~140s remeasurements inside it; ~6 min total) ----
COLUMNS=250 OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  PYTHONPATH=runners/dsl/python:. \
  python3 scripts/arc6_impotence_campaign_measure.py
#   -> results/arc6_impotence_campaign.json
```

**Engine provenance.** Every number in this document was produced by
`953b8e3fa6471a285f5e4d5fb731a721667ecf6e4fffba1f3feca52b96683a85`, resolving
from inside `/home/matt/arc6-impotence-campaign`.

**Contamination.** The MBPP test-split `code` is read only by the two real
remeasurements' own battery/report scripts (unmodified, existing scripts,
the same ones every prior ARC-6 rung invoked) — their reads are the
measurement itself. Nothing entered a codebook, a cue table or a route
table: no seed changed.
