# ARC 6 — A21: POOL-COMPOSITION DRIFT, CLOSED WITHOUT TOUCHING `gr_condition_lapse`

**Date:** 2026-08-11
**Bars:** `PROGRAM_SYNTHESIS_ARC6_PREREG.md` **amendment A21** (`AR21a`–`AR21d`),
registered **before** this investigation/build.
**Base commit:** `45eab90` (`main`, detached worktree
`/home/matt/ocelot-arc6-condition-lapse`, branch `arc6-condition-lapse`).
**Engine:** `c5e50801d48a170d3f16f2320f1e35eac355e0552a798faa9026d16bbbaaf567`
— copied from the canonical tree, **verified resolving from inside this
worktree**, `engine_provenance.source_match == "own"`, `stale_rust: []`.
**The same binary A19/A20 measured on**; the canonical tree's copy has not
moved. Coherence probe passed before every measurement:
`add_node("T", {"lst":[1,2,3], "tup":(1,2,3)})` reads back `[1,2,3]` and
`(1,2,3)` **distinctly**.
**Seed:** `seeds/arc_executor.json` **v1.7.0** (bumped from v1.6.0), sha256
`9ebf3742983671f56394acb3dd202660238c1abeade057ea6be555b2684689fc`, emitted
by `tools/build_arc_executor_seed.py` and gated byte-identical against it —
**12 rules** (the shipped 10 plus `ax_impotent_pool_lapse` /
`ax_impotent_pool_hold`). `seeds/goal_residuals.json` sha256
`199a90a48b645a739c452c55e04f3659ef43d936d3c431046b60b7a09f2b4148` —
**byte-identical to `HEAD`**, confirmed by direct comparison
(`git show HEAD:seeds/goal_residuals.json | sha256sum`), not merely by a
gate assertion.
**Gates:** `tests/test_arc_executor_migrated.py` — **101 collected, 100
passed, 1 failed (pre-existing)**; the other five arc-6 suites combined —
**173 collected, 172 passed, 1 failed (pre-existing), 1 skipped**.
**Artifact:** `results/arc6_condition_lapse.json` (engine + both seed shas
stamped; every scene is a live boot + mutation + `run_rules()` + read-off,
no fixture replay, no live subprocess).

**SCOPE: exactly AR21a–AR21d — characterize which verdicts carry a
pool-signature field, decide GO/NO-GO between extending
`gr_condition_lapse`'s closed vocabulary vs. applying the A19/A20
reversible-pair pattern directly, build the winning approach, and
demonstrate both directions live.** `results/arc6_import_impedance.json`/
`scripts/arc6_import_impedance.py`, and anything under `docs/research/
theory_convergence/`, `docs/research/adventure_mechanics/`, or
`docs/research/engine_substrate/decision_making_spike.md` are **untouched**.

---

## 0. VERDICTS

| bar | verdict | what it rests on |
|---|---|---|
| **AR21a — characterize which verdict kinds carry a pool-signature field, as a table** | **PASS** | reading every `AgendaVerdict` kind this seed mints: exactly ONE (`impotent`, A13) carries a set-valued `pool_agids` field; the other two (`order_n_fallback` — A19; `ask_dispatch_divergence` — A20) are each a single Term's truth value or a two-goal comparison, neither has a "which of several states" axis. §2 |
| **AR21b — GO/NO-GO between vocabulary extension and the reversible-pair pattern, registered before either was built** | **GO for the reversible pair, applied PER-NODE, entirely inside `seeds/arc_executor.json`; NO-GO for extending `gr_condition_lapse`** | the vocabulary extension fails its own registered no-Python-probe disqualifier (§3.1) — `_pool_sig()` is already a live, graph-native Term, so wiring it through `fact_equals` would mean inventing a Python probe for a quantity the graph can already compute itself, and a fourth native `ckind` would still couple the GENERIC `goal_residuals` seed to one domain's `POOL()` concept. The reversible pair clears BOTH its conditions: buildable per-node (preserving IM5's multi-verdict history) and strictly cheaper (two rules, zero cross-seed coupling, zero new node/edge type). §3 |
| **AR21c — demonstrate live, both directions, matching IM5's own discipline** | **PASS, plus the reverse-hold direction measured as a bonus** | (i) FIRES ON DRIFT: a second goal leaving the pool, with NO epoch bump, flips the superseded verdict's `pool_stale` to `1.0` in the SAME `run_rules()` fixpoint that mints the fresh verdict for the new composition — reproduced live, twin-run deterministic. (ii) DOES NOT FIRE WITHOUT DRIFT ACROSS A GENUINE EPOCH BUMP: reproducing IM5's own epoch-bump scene shows `pool_stale` stays `0.0` on BOTH the epoch-stale and the fresh verdict — orthogonal to `gr_condition_lapse`'s own axis, not a duplicate trigger for it. (iii), measured though not separately registered: the reverse direction (`ax_impotent_pool_hold`) restores `pool_stale` to `0.0` when the pool's composition returns to exactly what a verdict recorded. §4 |
| **AR21d — no regression, node-id lists not counts** | **PASS** | the six gate suites produce the **same** failing-node-id lists before and after, paired and named below. `ax_impotent`'s own `where`/`match`/mint-once guard are byte-identical to `HEAD`; its `effects` diff is EXACTLY the one additive `pool_stale:0.0` stamp, asserted structurally, not merely claimed. `seeds/goal_residuals.json` and every other sibling seed/adapter this rung does not touch are byte-identical to `HEAD`. §5 |

**The one thing worth reading if you read nothing else.** A13/A14 named a
gap and explicitly pre-committed its likely fix to a `gr_condition_lapse`
vocabulary extension ("a second, pool-signature-keyed condition kind would
need a change to `gr_condition_lapse`'s closed `MISMATCH` vocabulary").
Investigating it honestly finds the opposite: `gr_condition_lapse`'s
`fact_equals` branch is Python-probe-mediated by design (`ResidualFact`
nodes stamped by `probe_facts`/`install_facts`), and the pool's signature is
**already** a pure, existing, graph-native Term (`_pool_sig()`) evaluated
inside `ax_impotent` itself — extending the generic vocabulary to reach it
would be pushing a computation the graph can already do itself out into a
Python probe, backwards per `CLAUDE.md`. A19/A20's reversible-pair pattern,
applied **per-node** rather than as their own global singleton (so IM5's
multi-verdict history survives), closes the gap for less cost and zero
touch to shared infrastructure other threads (arc-4/5, `ps_move_select`)
depend on. `gr_condition_lapse`'s closed vocabulary is reported as
correctly staying closed.

---

## 1. WHAT CHANGED

Four files edited (one of them a regenerated artifact of another), two
added. **`seeds/goal_residuals.json` is byte-unchanged** — this rung's
whole point is that it did not need to be.

```
tools/build_arc_executor_seed.py     the emitter.  ax_impotent's mint effects
                                      gain one additive pool_stale:0.0 stamp;
                                      two new rules, ax_impotent_pool_lapse /
                                      ax_impotent_pool_hold; version
                                      1.6.0 -> 1.7.0
seeds/arc_executor.json              REGENERATED from that emitter (never
                                      hand-edited)
tests/test_arc_executor_migrated.py  +9 new AR21 gates; 3 existing
                                      confinement pins narrowed/converted
                                      (dated notes, see SS5.3)
scripts/arc6_condition_lapse_measure.py  NEW -- the measurement runner
results/arc6_condition_lapse.json    NEW -- the artifact
PROGRAM_SYNTHESIS_ARC6_PREREG.md     amendment A21 appended
PROGRAM_SYNTHESIS_ARC6_CONDITION_LAPSE.md  NEW -- this file
```

No `.rs` file, no edit to `domains/arc_executor.py` (confirmed byte-identical
to `HEAD`, gated), no edit to `seeds/goal_residuals.json`,
`seeds/arc_goals.json`, `seeds/arc_magnitude.json`, `seeds/arc_decompose.json`,
`seeds/program_synthesis.json`, or any of their ingest adapters.

---

## 2. AR21a — WHICH VERDICT KINDS CARRY A POOL-SIGNATURE FIELD

`grep -n '"pool_agids"' tools/build_arc_executor_seed.py` (on `HEAD`, before
this rung touched anything) returns hits **only** inside `_r_impotent`'s own
guard and effects.

| kind | rung | identity shape | pool-signature field | drift-of-composition even applicable? |
|---|---|---|---|---|
| `impotent` | A13 | a SET (the pool's ordered agid list) | `pool_agids` | **YES — this is the gap** |
| `order_n_fallback` | A19 | a single Term's truth value (`_order_n_is_not_live()`) | none | no — nothing set-shaped to drift |
| `ask_dispatch_divergence` | A20 | a two-goal comparison (`SEL_AGID()` vs `arc_sel_agid`) | none | no — two scalars, not a set |

Exactly one kind is in scope, confirming design item 1's prediction before
any code was written. No `AgendaVerdict` kind has landed since A20 under
this seed (`tools/build_arc_executor_seed.py::_rules()` — the two A19/A20
pairs plus `ax_dispatch`/`ax_retired_epoch`/`ax_rearm`/`ax_close`/
`ax_impotent`/`ax_world_probe_epoch` was the full list on `HEAD`); MG4
decomposition and supply-blocker retirement, named in the task brief as
already landed, mint no `AgendaVerdict` of their own (confirmed:
`grep -n AgendaVerdict tools/build_arc_decompose_seed.py` and the retire-
blocker tooling return nothing).

---

## 3. AR21b — THE GO/NO-GO CALL

### 3.1 Why the vocabulary extension is NO-GO

`gr_condition_lapse`'s three `ckind`s are not uniform in HOW they read the
world:

- `shape_count`/`payload_count` (`tools/build_goal_residual_seed.py::
  _shape_count`) read `ShapeSignature` nodes **directly, live, inside the
  rule** — no Python between the condition and the count.
- `fact_equals` is different in kind: it compares against a
  `ResidualFact{name,value}` node, and **every** existing `ResidualFact` is
  written by `domains/goal_residual_ingest.py::probe_facts`/`install_facts`
  — Python code that reads an external world (a file's presence/sha, a live
  value-layer probe) and stamps the answer as mechanical I/O, called
  explicitly, not continuously re-derived inside `run_rules()`.
  `arc_measure_epoch` (the ONE `fact_equals` condition `ax_impotent` itself
  already used, for the EPOCH axis) is the one exception that proves the
  rule: it has a producer already living in the executor's own rules, so
  comparing against it needed no new Python probe.

The pool's live signature (`_pool_sig()`, `tools/build_arc_executor_seed.py`)
is **already a pure, existing DSL Term**, evaluated inside `ax_impotent`
itself. A `pool_sig_equals` `ckind` computed through `fact_equals` would mean
inventing a Python step that probes the graph's own pool and writes it back
as a `ResidualFact` — precisely the "push a graph-native computation out
into Python" move `CLAUDE.md` forbids, for a quantity the graph can already
compute itself, live, in the same rule that would consume it. This is the
hard disqualifier AR21b registered in advance, and it is met exactly as
predicted: **confirmed, not assumed** —
`grep -n 'import.*substrate_rs\|\.evaluate(\|run_rules' domains/
goal_residual_ingest.py` returns nothing beyond `probe_facts`'s own
mechanical `add_node`/`node` calls (the module cannot compute `_pool_sig()`
without either duplicating the Term in Python — a decision — or importing
`arc_executor`'s own Term builder into a seed that has never depended on it).

Even setting the Python-probe problem aside, a **native** fourth `ckind`
hard-coding `_pool_sig()`'s Term shape into the GENERIC `MISMATCH` function
would be the first domain-specific concept `seeds/goal_residuals.json` has
ever carried — confirmed:
`grep -n 'import.*arc_goals\|import.*arc_executor' tools/
build_goal_residual_seed.py` returns no hits. `ps_move_select`
(`seeds/program_synthesis.json`) and every arc-4/5/6 `GoalResidual` ride the
same `MISMATCH`/`gr_condition_lapse`/`gr_condition_hold` pair; coupling it to
`ArcAgenda`'s `POOL()` is a real modularity cost future non-ARC-6 residuals
would have to route around, weighed against a mechanism (§3.2) that needs
none of it.

### 3.2 Why the reversible pair, applied per-node, is GO

A19's own design item 4 rejected the epoch-shaped `fact_equals` idiom for
the **same structural reason** pool drift has: the fact in question can
change with no epoch bump in the scene, so a description honest only until
the next measurement is the wrong shape. A19/A20 both instead added a
direct reversible pair keyed on a live Term comparison, entirely inside
`seeds/arc_executor.json`. The one respect in which pool drift is NOT
identical to either precedent, and the discriminator this rung's bars
required before reusing the shape verbatim: **A19/A20 are both SINGLETON
facts** (`EXISTS` an `active`-flagged node of that kind is the whole state).
`ax_impotent`, by IM5's own registered design (A13 §6), intentionally holds
**multiple** `AgendaVerdict{kind:'impotent'}` nodes simultaneously — one per
distinct pool signature, a deliberate historical record
(`test_im5_a_DIFFERENT_impotent_pool_mints_its_OWN_verdict`). A literal
A19-shaped global `active` flag would have collapsed that history the first
time the pool drifted while remaining impotent. The design built here
instead flips an `active`-style flag (named `pool_stale`, matching `stale`'s
own polarity rather than `active`'s, deliberately — see §4) **per verdict
node**, comparing that node's own `pool_agids` against the current
`_pool_sig()`, never a singleton guard. It costs two rules, zero new node
type, zero new edge type, zero new DSL Term, zero cross-seed coupling — the
comparison AR21b required, and it wins on every registered axis.

### 3.3 The mechanism, precisely

```python
def _r_impotent_pool_lapse():
    return {
        "name": "ax_impotent_pool_lapse",
        "match": HUB + [["agenda", "has_agenda_verdict", "av"]],
        "where": AND(
            EQ(A(V("av"), "kind"), L("impotent")),
            NOT(EQ(A(V("av"), "pool_agids"), _pool_sig())),
            NOT(EQ(A(V("av"), "pool_stale"), L(1.0))),
        ),
        "effects": [["set_attr", "av", "pool_stale", 1.0],
                    ["set_attr", "av", "pool_stale_epoch", T(MEASURE_EPOCH())]],
    }

def _r_impotent_pool_hold():
    return {
        "name": "ax_impotent_pool_hold",
        "match": HUB + [["agenda", "has_agenda_verdict", "av"]],
        "where": AND(
            EQ(A(V("av"), "kind"), L("impotent")),
            EQ(A(V("av"), "pool_agids"), _pool_sig()),
            EQ(A(V("av"), "pool_stale"), L(1.0)),
        ),
        "effects": [["set_attr", "av", "pool_stale", 0.0],
                    ["set_attr", "av", "pool_held_epoch", T(MEASURE_EPOCH())]],
    }
```

Mutually exclusive by construction (`Eq` vs `Not(Eq)` against the identical
comparison), the `gr_condition_lapse`/`gr_condition_hold` SHAPE and NAMING
convention, reused deliberately — the two-flag idiom transfers even though
the `ResidualCondition` indirection does not need to. `ax_impotent` itself
gains exactly one additive stamp at mint (`"pool_stale": 0.0` — true by
construction, since a freshly minted verdict's own `pool_agids` trivially
equals the pool signature at that instant); its `where`/`match`/mint-once
guard are untouched, asserted structurally (§5.2).

**Two orthogonal staleness axes, deliberately, not one widened axis.**
`stale` (unmodified `gr_condition_lapse`) answers "has a measurement
happened since this was minted" — an EPOCH question. `pool_stale` answers
"does this verdict's `pool_agids` still equal the pool's CURRENT signature"
— a COMPOSITION question, live, no epoch involved. A verdict can be
`stale:1.0, pool_stale:0.0` (superseded by a later measurement, but still
describing today's actual pool) or `stale:0.0, pool_stale:1.0` (current
epoch, but the pool has since moved under it without a re-measurement) —
both measured live below, both genuinely informative, neither redundant
with the other.

---

## 4. AR21c — LIVE, BOTH DIRECTIONS

`results/arc6_condition_lapse.json`.

### 4.1 Fires on drift, NO epoch bump

Boot → the sole routable goal (`AGID`) leaves the pool (7-goal impotent
pool, mint-once) → verdict `V1` mints, `pool_stale:0.0, stale:0.0`. A
**second** goal (`arc6.claim.tier0_hs1_0_of_10`) then leaves the pool, with
**no** epoch bump anywhere in the scene:

```
pool_n_seen                          [6, 7]
new_verdict_minted_for_6_pool        True    (IM5's own mint-once behaviour, unmodified)
first_verdict_pool_stale_flipped     True    (V1.pool_stale: 0.0 -> 1.0)
first_verdict_epoch_stale_UNCHANGED  True    (V1.stale stays 0.0 -- no measurement happened)
```

Within the SAME `run_rules()` fixpoint: a fresh verdict mints for the new
6-goal composition (`pool_stale:0.0`) and `V1`'s `pool_stale` flips to `1.0`
— the reader no longer has to compare `pool_agids` against the current pool
by hand; the graph says so. Gate:
`test_a21_AR21c_fires_on_pool_composition_drift_with_NO_epoch_bump`.

### 4.2 Does NOT fire across a genuine epoch bump WITHOUT drift

Reproducing IM5's own scene exactly (bump `arc_measure_epoch`, pool
composition **unchanged**):

```
count_after        2        (IM5's own behaviour: old verdict epoch-stales, a fresh one mints for the SAME signature)
all_pool_stale_zero  True   (pool_stale stays 0.0 on BOTH held verdicts)
epoch_stale_split   [0.0, 1.0]   (the SAME split IM5 measured, unmoved)
```

`pool_stale` is provably orthogonal to `gr_condition_lapse`'s own axis, not
a duplicate trigger for it — it does not fire merely because a measurement
happened. Gate:
`test_a21_AR21c_does_NOT_fire_across_a_genuine_epoch_bump_WITHOUT_drift`.

### 4.3 The reverse direction, measured though not separately registered

Drift the pool (`V1.pool_stale` 0.0 → 1.0), then restore the SECOND goal's
`headroom_n` to its original value — the composition returns to EXACTLY
what `V1` recorded:

```
first_pool_stale     0.0
drifted_pool_stale    1.0
restored_pool_stale   0.0
```

A one-way lapse would itself be an unrevisable claim, per the
`gr_condition_lapse`/`gr_condition_hold` precedent this reuses. Gate:
`test_a21_AR21c_the_reverse_direction_pool_hold_is_TWO_SIDED`.

### 4.4 Determinism

`twin_run_determinism.byte_identical: true` — the drift scene, run twice
independently, produces byte-identical `AgendaVerdict` content (sorted by
`(pool_n, pool_stale)` to remove read-order as a variable). Gate:
`test_a21_AR21c_twin_run_determinism`.

---

## 5. AR21d — NO REGRESSION. NODE-ID LISTS, NEVER A BARE COUNT.

Both arms below ran on the **same binary** (`c5e50801d48a…`), in this
worktree; the **before** arm is the unmodified tree at `45eab90`.

| suite | before | after | failing node ids — **identical before and after** |
|---|---|---|---|
| `test_arc_executor_migrated` | 91 passed, **1 failed** (92 collected) | **100 passed, 1 failed** (101 collected) | `test_ex1_the_frozen_artifacts_are_STILL_byte_identical` |
| `test_arc_goals_migrated` | **37 / 37** | **37 / 37** | — |
| `test_goal_residual_migrated` | 29 passed, **1 failed**, 1 skipped | 29 passed, **1 failed**, 1 skipped | `test_gr4_the_live_mbpp_pass_ids_are_unchanged` |
| `test_arc6_valuelayer_migrated` | **35 / 35** | **35 / 35** | — |
| `test_arc_magnitude_migrated` | **43 / 43** | **43 / 43** | — |
| `test_arc_decompose_migrated` | **28 / 28** | **28 / 28** | — |

The executor suite's collected count rises **92 → 101**: nine new AR21c/
AR21d gates, zero removed, zero renamed.

### 5.1 The two reds, unchanged, neither caused here

Both are the SAME two reds every prior ARC-6 rung has recorded, same node
ids:

- `test_ex1_the_frozen_artifacts_are_STILL_byte_identical` — `results/` is
  gitignored and untracked in this checkout, so its `git show HEAD:…`
  witness returns empty. The property the gate is *about* passes on every
  run here; the chosen witness is what fails.
- `test_gr4_the_live_mbpp_pass_ids_are_unchanged` — asserts the engine's
  short sha is in a three-entry allowlist that predates `c5e50801d48a`.
  **Not widened** — this rung did not touch that gate or its allowlist.

### 5.2 `ax_impotent`'s firing behaviour is byte-identical; its additive stamp is asserted structurally

`test_a21_AR21d_ax_impotents_where_and_match_and_mint_once_guard_are_
UNCHANGED` diffs `match`/`where`/`batch` against `HEAD` for byte equality,
then diffs `effects` element by element and asserts the ONLY difference on
the `AgendaVerdict`-minting effect is the addition of `pool_stale: 0.0` —
nothing removed, nothing else added, nothing else edited. Two OLDER
confinement pins (`test_a19_AR19d_ax_dispatch_and_every_prior_rule_body_is_
UNCHANGED`, `test_a20_AR20d_every_prior_rule_body_is_UNCHANGED`) previously
asserted `ax_impotent`'s FULL rule dict byte-identical to `HEAD`; both are
now false BY CONSTRUCTION once the additive stamp lands, so both were
**narrowed, with a dated note naming this rung**, to exclude `ax_impotent`
from their byte-identical set — the sanctioned "drifted pins are reconciled
in the improvement direction with dated notes" pattern this arc has used at
every version bump (WH1→A18→A19→A20, now A20→A21). No behavioural assertion
was removed: the property both pins were protecting (`ax_impotent`'s FIRING
behaviour is unchanged) is now covered, more precisely, by the new
`where`/`match`/mint-once-guard-specific gate.

### 5.3 The seeds below this rung are untouched, gated

`test_a21_AR21d_gr_condition_lapse_and_every_sibling_seed_are_still_
UNTOUCHED` diffs `seeds/arc_goals.json`, `seeds/goal_residuals.json`,
`seeds/program_synthesis.json`, `seeds/arc_magnitude.json`,
`seeds/arc_decompose.json`, `domains/arc_goal_ingest.py`,
`domains/goal_residual_ingest.py`, `domains/arc_magnitude_ingest.py` against
`HEAD` — all eight byte-identical — and regenerates
`seeds/goal_residuals.json` via its own emitter's `--check`, confirming no
drift. `gr_condition_lapse`'s closed `MISMATCH` vocabulary is untouched in
every particular.

### 5.4 The adapter is untouched

`test_a21_AR21d_the_adapter_is_BYTE_IDENTICAL_to_HEAD` — `domains/
arc_executor.py` needed no edit: `agenda_verdicts(sub, kind=...)` was
already generic (A19's own finding, reused verbatim a third time). No new
adapter function, no changed source-audit allow-list.

---

## 6. EVERYTHING THAT BROKE

Recorded because the process is the result — including a hazard this rung
tripped despite the brief's own explicit warning.

### 6.1 The timeout hazard, a SEVENTH time, on my own first command

The task brief named this hazard explicitly, quoting A20's own account, and
this rung still tripped it on its very first measurement command: a loop
running all six baseline suites was submitted with an internal `timeout
480` on each `pytest` invocation, but the **outer** tool-call timeout
defaulted to 2 minutes and `SIGKILL`ed the whole loop mid-way through
`test_arc_executor_migrated.py`'s `live_run` fixture (~140s). The runner's
`finally` never ran, leaving `seeds/program_synthesis.json` patched (the
`row_verdict_seed_only` comparator swap left applied) in this worktree.

**Recovery, verified by sha256, no guessing:** `git status --porcelain`
showed only `seeds/program_synthesis.json` modified; `git checkout --
seeds/program_synthesis.json` restored it, verified `4e866340eb50…`,
matching the pristine value every prior rung in this arc has recorded. The
canonical tree's own `git status --porcelain` was checked before and after
and never showed any change — the crash-stash directories under `/tmp`
(`arc6_remeasure_*`) confirmed the damage never reached past this worktree's
own tracked file. Every subsequent suite run in this rung used an explicit,
generous **Bash-tool-level** timeout (480000ms), not merely an internal
`timeout` inside the shell command — the distinction the prior six
incidents across this arc had already named but that this rung still had to
relearn firsthand.

### 6.2 The two pre-existing confinement pins needed narrowing, predicted in the bars, and it happened exactly as predicted

AR21d's own text pre-registered that `ax_impotent` "may gain an ADDITIVE
`active:1.0`-style stamp at mint time" and that this would need the older
byte-identical pins updated. It did — §5.2 above is that update, done with
a dated note rather than silently.

### 6.3 An effect-list indexing bug in the first draft of the additive-stamp gate

The first draft of `test_a21_AR21d_ax_impotents_where_and_match_and_mint_
once_guard_are_UNCHANGED` indexed the `add_node` effect list as
`[op, var, attrs]` (3 elements); the engine's actual shape is
`[op, var, type, attrs]` (4 elements, matching `["add_node", "av",
"AgendaVerdict", {...}]`) — an `AttributeError: 'str' object has no
attribute 'get'` on the first run caught it immediately, fixed by reading
`h[2]`/`h[3]` correctly rather than `h[2]` alone.

### 6.4 Nothing else broke

No engine rebuild was needed, no seed this rung does not own needed
touching, and the emitter's `--check` passed on the first regeneration
after the two new rules were written correctly the first time (the
`ar21c_*` measurement scenes were verified via the standalone script,
§4, before any gate was written against them).

---

## 7. REMAINING UNCERTAINTIES

Ordered by how much damage being wrong would do. Named, not built against —
out of this rung's scope where noted.

1. **`pool_stale` inherits `_pool_sig()`'s own exposure, unmodified.**
   `_pool_sig()` (`tools/build_arc_executor_seed.py`) is a same-run,
   same-graph signature — comparable by `Eq` with no sort, because two reads
   of the SAME graph state walk the SAME underlying `Filter` order — not a
   canonical cross-run signature (A13's own §1.2 note, unchanged). This
   rung's mechanism reads the identical Term `ax_impotent` itself mints
   against, so it can never disagree with `ax_impotent` about what the
   pool's signature is, by construction — but it also means neither rule
   would survive a hypothetical future change to `POOL()`'s own iteration
   order without both `ax_impotent` and this rung's two rules moving
   together, which they structurally must, since they share the Term.
2. **This closes the LAST originally-named remaining item in this executor
   sub-thread, and the arc's own culture is to say so plainly rather than
   leave it implicit.** The re-arm deadlock (A18), the silent order-N
   fallback (A19), `ag_ask`/`ax_dispatch` reading different collapses (A20),
   MG4 decomposition and supply-blocker retirement (landed under their own
   docs), and now pool-composition drift (A21) are all done. No new
   uncertainty of comparable scope was surfaced by this rung's own
   investigation — see §8 for what, if anything, is worth naming as a
   natural next step.
3. **The A19/A20 precedent is now used three times with a growing set of
   variations (singleton vs per-node; epoch-shaped vs Term-shaped), and no
   rung has yet written down the GENERAL shape all three share as its own
   reusable pattern**, separate from `gr_condition_lapse`/`gr_condition_
   hold`'s own generic (but Python-probe-coupled) one. This rung's own §3.2
   is the closest thing to that write-up that exists today; formalizing it
   into something a FOURTH consumer could cite directly (rather than reading
   three prior rungs' comments) was not done here and is a documentation
   task, not a code one.
4. **`ag_ask` and `ax_impotent` still read different collapses in general**
   (A13's own uncertainty #5, restated by A14, unchanged, not built against
   here) — not observed to matter in any scene this rung constructed, and
   orthogonal to pool-composition drift specifically.

---

## 8. STATUS OF THE ARC6 EXECUTOR SUB-THREAD

All six originally-named "remains to build" items from this thread are now
closed: the re-arm deadlock (A18), the silent order-N fallback (A19),
`ag_ask`/`ax_dispatch` collapse divergence (A20), MG4 decomposition and
supply-blocker retirement (landed separately), and pool-composition drift
(A21, this rung). `ax_dispatch`/`SEL_AGID`/`ARMED_AGID`/`ARMED_VALUE`/
`COLLAPSE_NAME`/`_armed`/`ROUTE`/`_routable` — the actual dispatch decision —
remain byte-unchanged across all six rungs; every one of them added
OBSERVABILITY (a standing, queryable `AgendaVerdict` fact) rather than
changing what gets dispatched or when. `gr_condition_lapse`'s closed
vocabulary is untouched across the entire arc, including this rung, which
was the rung most likely to have needed to touch it.

**What is genuinely open, named honestly rather than manufactured to have
something to point at:**

- §7 item 3 (write up the reversible-pair idiom as its own named pattern,
  independent of `gr_condition_lapse`, for a future fourth consumer) is a
  small documentation task, not a build.
- A13's uncertainty #3 (the (a)/(b) capability-acquisition candidates A14's
  campaign measured NO-GO for, on the evidence available then) was never
  revisited with fresh evidence; nothing in this rung's own measurements
  changes that NO-GO, and no scene here was built to re-test it.
- Nothing else in this sub-thread's own accumulated uncertainty lists (A13
  §8, A14 §9, A18, A19, A20) was found, on rereading them for this rung, to
  still be open AND in scope AND not already superseded by a later rung —
  each was checked against the current tree, not merely quoted.

**This rung's own honest read: the executor sub-thread is complete for
now.** Nothing was found that would justify continuing it as a numbered
amendment sequence; a future rung in this area would be starting a
genuinely new question (most plausibly the (a)/(b) capability-acquisition
question A14 left NO-GO, if new evidence ever arrives — e.g., a second
capability landing that changes the real-only subset's `n=2` power
constraint A14 §9 item 2 named), not continuing this one.

---

## 9. FILES

| file | what |
|---|---|
| `tools/build_arc_executor_seed.py` | the emitter — `ax_impotent`'s effects gain one additive `pool_stale:0.0` stamp; two new rules, `ax_impotent_pool_lapse`/`ax_impotent_pool_hold`; version 1.6.0 → 1.7.0 |
| `seeds/arc_executor.json` | **regenerated** from that emitter, never hand-edited; gated byte-identical by `test_a21_AR21d_the_new_rules_are_the_ONLY_addition_to_the_seed` |
| `tests/test_arc_executor_migrated.py` | nine new gates (`test_a21_AR21c_*` ×4, `test_a21_AR21d_*` ×5); three existing confinement pins narrowed with dated notes (§5.2) |
| `scripts/arc6_condition_lapse_measure.py` | the measurement runner — AR21c fires-on-drift / does-not-fire-across-epoch-bump / reverse-hold / twin-run scenes |
| `results/arc6_condition_lapse.json` | the artifact, engine + both seed shas stamped |
| `PROGRAM_SYNTHESIS_ARC6_CONDITION_LAPSE.md` | this file |
| `PROGRAM_SYNTHESIS_ARC6_PREREG.md` | **amendment A21** appended |

**In this worktree's `git status`, not part of the change:**

- **`data` and `results` appear as untracked.** They are **symlinks** into
  the canonical tree (gitignored — the `.gitignore` patterns match
  directories, not symlinks). They must not be staged.
- `runners/dsl/python/substrate_rs/_native.abi3.so` does **not** appear as
  modified — this rung's copied engine matches the canonical tree's
  committed one byte-for-byte, confirmed both before and after every
  measurement.

**Nothing in the canonical tree changed.** This worktree's changes are
isolated to itself; the canonical `/home/matt/ozmadev/ocelot` tree's
`git status --porcelain` is unaffected by anything in this document,
re-verified clean after the §6.1 recovery.

---

## 10. REPRODUCE

```bash
# --- verify main's tip, then the worktree ---------------------------------
git -C /home/matt/ozmadev/ocelot log --oneline -1 main   # 45eab90
git worktree add --detach /home/matt/ocelot-arc6-condition-lapse 45eab90
cd /home/matt/ocelot-arc6-condition-lapse
ln -s /home/matt/ozmadev/ocelot/data    data        # gitignored
ln -s /home/matt/ozmadev/ocelot/results results     # gitignored

# --- the engine.  Reproduces byte-identically to HEAD's committed binary. -
mkdir -p runners/dsl/python/substrate_rs
cp /home/matt/ozmadev/ocelot/runners/dsl/python/substrate_rs/_native.abi3.so \
   runners/dsl/python/substrate_rs/_native.abi3.so
touch runners/dsl/python/substrate_rs/_native.abi3.so   # git-worktree mtime race, A14 SS7.1
sha256sum runners/dsl/python/substrate_rs/_native.abi3.so
#   c5e50801d48a170d3f16f2320f1e35eac355e0552a798faa9026d16bbbaaf567

# --- the coherence probe.  STOP if these read back the same. --------------
PYTHONPATH=runners/dsl/python:. python3 -c "
import substrate_rs as srs; s=srs.Substrate()
a=s.node(s.add_node('T',{'lst':[1,2,3],'tup':(1,2,3)}))['attrs']
print(a['lst'], a['tup'], a['lst']!=a['tup'])"

# --- the seed is EMITTED, never hand-edited --------------------------------
PYTHONPATH=runners/dsl/python:. python3 tools/build_arc_executor_seed.py
PYTHONPATH=runners/dsl/python:. python3 tools/build_arc_executor_seed.py --check

# --- the measurement artifact ----------------------------------------------
COLUMNS=250 OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  PYTHONPATH=runners/dsl/python:. \
  python3 scripts/arc6_condition_lapse_measure.py   # -> results/arc6_condition_lapse.json

# --- the gate (fast -- no live subprocess in the A21-only slice) -----------
COLUMNS=250 OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  PYTHONPATH=runners/dsl/python:. \
  python3 -m pytest tests/test_arc_executor_migrated.py -k a21 \
    --confcutdir=$PWD -q -p no:randomly -rf     # 9 passed

# --- the full regression arms.  ALWAYS an explicit, generous Bash-tool-
#     level timeout, not merely an internal `timeout` inside the command --
#     the live_run fixture (~140s) has SIGKILLed a shorter one SEVEN times
#     across this arc now, most recently in this rung's own first attempt
#     (SS6.1). ------------------------------------------------------------
for s in test_arc_executor_migrated test_arc_goals_migrated \
         test_goal_residual_migrated test_arc6_valuelayer_migrated \
         test_arc_magnitude_migrated test_arc_decompose_migrated; do
  COLUMNS=250 OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
    PYTHONPATH=runners/dsl/python:. timeout 480 \
    python3 -m pytest tests/$s.py --confcutdir=$PWD -q -p no:randomly -rf
done
```

**Engine provenance.** Every number in this document was produced by
`c5e50801d48a170d3f16f2320f1e35eac355e0552a798faa9026d16bbbaaf567`,
resolving from inside `/home/matt/ocelot-arc6-condition-lapse`.

**Contamination.** No MBPP test-split `code` was read by anything in this
rung — the AR21c scenes are all boot + mutation + `run_rules()` + read-off,
with zero live remeasurement subprocess; the only battery invocation
anywhere in this rung's own measurement path is inside the pre-existing
`live_run` fixture the FULL regression suite (not the A21-only slice)
already ran before this rung touched anything, and its pass/accepted id
lists are unchanged (not independently re-quoted here; see
`PROGRAM_SYNTHESIS_ARC6_IMPOTENCE_TERM.md` §4.2 / `PROGRAM_SYNTHESIS_ARC6_
IMPOTENCE_CAMPAIGN.md` for the last rungs that re-derived and quoted them).
