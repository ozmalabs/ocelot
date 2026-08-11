# ARC 6 — A22: THE IMPOTENCE RE-SWEEP — real-only n GROWS to 5, and IC3 now reads GO for candidate (a)

**Date:** 2026-08-11/12
**Bars:** `PROGRAM_SYNTHESIS_ARC6_PREREG.md` **amendment A22** (`IR1`–`IR4`),
registered **before** this measurement.
**Base commit:** `0351084` (`main` at brief time), rebased cleanly onto
`02a71e3` (`main`'s tip by the time this rung finished — two unrelated
merges landed mid-rung, `arc6-condition-lapse`/A21 and
`risk-ladder-implementation`; neither touches `seeds/`, `domains/`,
`tools/`, `tests/`, or `docs/research/program_synthesis/`, confirmed by
`git diff --stat` before rebasing). Detached worktree
`/home/matt/ocelot-arc6-impotence-resweep`, branch
`arc6-impotence-resweep`.
**Engine:** `c5e50801d48a170d3f16f2320f1e35eac355e0552a798faa9026d16bbbaaf567`
— copied from the canonical tree's committed binary, **verified resolving
from inside this worktree** (`substrate_rs._native.__file__` is inside
`/home/matt/ocelot-arc6-impotence-resweep`). **The same binary A17/A18/A19/
A20/A21 all measured on.** Coherence probe passed before every
measurement: `add_node("T", {"lst":[1,2,3], "tup":(1,2,3)})` reads back
`[1,2,3]` and `(1,2,3)` **distinctly**.
**Seeds:** `seeds/arc_executor.json` (v1.7.0) and `seeds/arc_decompose.json`
(v1.1.0) — **byte-identical to `HEAD`** (`git diff --stat HEAD -- seeds/
domains/ tools/ tests/ runners/` is empty throughout this rung — no seed,
adapter, or rule was touched; this is a pure measurement rung).
**Artifacts:** `results/arc6_impotence_resweep.json` (the primary sweep —
engine + both seed shas stamped, every scene a live boot + mutation +
`run_rules()`/live subprocess, two REAL live remeasurements ~0.13s and
~140s), `results/arc6_impotence_resweep_testimony_chain.json` (the cheap
testimony-chain extension), `results/arc6_impotence_resweep_IC2.json` (the
IC2 aggregation, computed with A14's own unmodified
`concentration_stat` function, imported not reimplemented).
**Gate:** the six existing ARC-6 suites, measured fresh in this worktree
both before and after this rung's own measurement script ran — **identical
node-id lists both times** (§5); since this rung builds nothing, this is
the complete IR4 result.

**SCOPE: the measurement only.** Per this rung's own registered
constraint, **candidate (a) or (b) is not built here even though IC3 now
reads GO for (a)** — §6 names the sharpened next charter instead of
building it.

---

## 0. VERDICTS

| bar | verdict | what it rests on |
|---|---|---|
| **IR1 — re-derive the current real-only distinct impotent-state count** | **GREW: n=2 → n=5** | Driving the tree's current full capability (order-N magnitude + MG4 decomposition via a REAL constraint reply + BOTH `ExecClass`es to real completion + a genuine live attempt at `mg_tier_retire`'s natural firing condition) in one boot reaches a pool composition **structurally distinct** from either of A14's own two states (10 goals, not 7; a `decomposition_tier` goal present for the first time in this sweep's real population) AND a **different live `nearest_unroutable_kind`** (`decomposition_tier`, not `supply_blocker`/`source_claim`). A cheap follow-on testimony chain (A14 group-2's own already-real mechanism, applied to this NEW pool) surfaces **two further** distinct real states on the SAME new pool signature (`supply_blocker`, then `source_claim` at a fixed point) — five real-only states total, deduplicated by A14's own `(pool signature, live winner kind)` unit. §2–§4 |
| **IR2 — IF n≥5: run IC2/IC3, quoting A14's own formulas** | **RUN. IC2 = SPREAD (f=0.4 ≤ 0.50). IC3 = GO for (a), NO-GO for (b)** | `n=5`, modal-kind fraction `0.4` — below the `0.50` SPREAD threshold, i.e. SPREAD on BOTH the letter (`f ≤ 0.50`) and the substance (no kind holds even half). GO-for-(a)'s two conditions are BOTH met on the scenes this rung measured: (i) SPREAD on real-only [met]; (ii) the testimony chain reaches a fixed point rather than cycling [met, twin-run deterministic]. GO-for-(b) requires CONCENTRATED, which SPREAD is definitionally not — NO-GO for (b), condition (i) alone disqualifies it. **§6 sharpens what "GO for (a)" should actually mean as a next charter — read it before treating this as "go build (a)."** §5–§6 |
| **IR3 — if n<5, report a null and characterize the next-needed capability** | **DOES NOT APPLY** — `n=5`, not `<5`. (Remaining-uncertainties §8 still records what A17's own two named, still-unbuilt candidates look like after this rung's own investigation, for completeness.) | §8 |
| **IR4 — no regression** | **PASS** | The six gate suites produce the **same** failing-node-id lists before and after this rung's own measurement script ran (this rung edits zero seed/adapter/test/rule file). Same two standing, environment-conditional reds every prior rung since A12 has recorded. §7 |

**The one thing worth reading if you read nothing else.** Three prior rungs
(A14, A15, A17) each independently declined to build candidate (a) or (b),
citing an underpowered `n=2`. This rung finds that underpowering was not a
permanent structural fact about the system — it was a fact about a sweep
that had never combined two ALREADY-LANDED, ALREADY-REAL capabilities in
one boot: A16's decomposition (`mg_decompose`, real via a genuine
constraint reply, landed **before** A17) and the executor's own two
`ExecClass`es (A15). Doing so for the first time — not building anything
new, purely exercising what the graph could already do — jumps real-only
`n` from 2 to 5 and flips IC2's read from AMBIGUOUS-underpowered to SPREAD.
**The growth did NOT come from A17's own `mg_tier_retire` mechanism**: this
rung reproduced A17's exact finding live, on a fresh engine, months later —
tier 1's witness coverage is *still* two ids short (`18`, `310`, identical
to A17's own gap) — `mg_tier_retire` still correctly, honestly declines to
fire. **The growth came from decomposition itself, before any retirement
happens at all**: splitting one `supply_blocker` goal into four
`decomposition_tier` children changes the pool's shape and its nearest-
unroutable kind regardless of whether any child ever resolves. A15 §6's own
prediction — "a capability whose retirement changes which
`nearest_unroutable_kind` the pool settles into" — turns out to have named
the wrong verb: it is not *retirement* that grows real-only `n` here, it is
*decomposition*, a capability that had already shipped and had simply never
been exercised inside an impotence sweep before this rung.

---

## 1. THE DESIGN INVESTIGATION (recap — full text registered in `PROGRAM_SYNTHESIS_ARC6_PREREG.md` amendment A22, before this measurement ran)

Summarised here so this document is self-contained; the full text is in the
prereg.

1. Since A14's own base commit, five more amendments landed: A15 (second
   `ExecClass`, already checked null for this exact question), A16 (MG4
   decomposition, minting the `decomposition_tier` kind), A17
   (`mg_tier_retire`, a real-but-not-yet-naturally-firing retirement path),
   A18 (re-arm deadlock closed), A19 (silent order-N fallback made
   observable), A20 (`ag_ask`/`ax_dispatch` divergence made observable),
   A21 (per-node `pool_stale` marker on `impotent` verdicts).
2. A19/A20/A21 are ruled OUT as relevant to the pool-composition question by
   A21's OWN already-registered, already-gated `AR21a` survey: neither
   `order_n_fallback` nor `ask_dispatch_divergence` carries a `pool_agids`-
   shaped field, and `pool_stale` is a currentness marker on an EXISTING
   verdict, not a new pool exit — none of the three can, by construction,
   create a pool composition A14's own methodology did not already reach.
   This rung does not re-measure that; it is quoted, not re-derived.
3. A17's own mechanism was therefore the one candidate worth a genuine,
   live re-attempt: has the `18`/`310` gap in tier 1's witness coverage
   closed since A17's own live remeasurement? The committed
   `results/arc6_structural_ceiling.json` on this tree, checked before
   registering A22's bars, still read the PRE-A17 6-id witness set (an
   OLDER engine's evidence, `5c1b472fe674…`) — nobody had re-run and
   recommitted it since A17's own 8-id live finding, so this rung's own
   live re-run would be the first fresh look since A17.

---

## 2. THE MEASUREMENT — driving the current tree's full capability in one boot

`scripts/arc6_impotence_resweep_measure.py` (new, 320 lines) — every scene
is real per A14's own IC1 rules: a REAL live execution, a real
`attach_constraint_reply` (the SAME class of mechanism as `attach_reply`,
applied to the ONE constraint channel `mg_ask_constraints` already asks
over), or the SAME already-validated `headroom_n → 0` synthetic pool-exit
(used only to isolate one goal's dispatch, A15's own `run_one` precedent —
never to fabricate a pool composition this system cannot reach on its own).

**Step 1 — decomposition, via a REAL horizon reply, never a poke.** A16/A17's
own test suite documents this as "THE ONLY WORKING CONSTRUCTION" for
reaching decomposition at all — a raw `decompose_required` attribute poke
does not survive a `run_rules()` pass (a cross-cutting seed-load-order race
A16 diagnosed and left in place, not this rung's to fix). `horizon=5.0` is
the SAME value every existing MG4/A17 gate scene uses, for direct
comparability, not cherry-picked for this rung.

```
boot (order-N + decompose + 2-ExecClass executor, in ONE graph — never
      exercised together before this rung: every prior A15/A17 gate
      exercised the executor OR decompose, not both at once)
  pool_n = 8   (row-verdict re_measure + 3 supply_blocker + 4 source_claim;
                the structural re_measure goal is not yet minted — its
                residual is not yet stale)

step 1: attach_constraint_reply(horizon=5.0)   -- REAL reply
  missing_structural_primitive -> status='decomposed', 4 children minted
  pool_n = 11   (+4 children, -1 decomposed parent)
```

**Step 2 — BOTH `ExecClass`es to REAL completion**, mirroring A15 §6's own
extension-probe shape (cheap one first): the structural residual is forced
stale via the SAME narrow `_put_fact` poke A13/A15 validated (never a raw
`decompose_required`-style poke on a Rust-Term-computed field — this one
targets a Python-mediated `ResidualFact`, exactly the shape A21's own
investigation confirmed is the ONLY kind of condition a poke can
legitimately target); row-verdict is organically stale already (confirmed:
`value_layer_list_eq_tuple` reads `"0"` live vs the seed's `"1"`, the SAME
finding every prior rung since A14 recorded, still true on this engine).

```
step 2a: structural ExecClass -- REAL subprocess, 0.13s
  retires; pool_n = 11 -> back to 11 after the +1/-1 (mint then retire)

step 2b: row-verdict ExecClass -- REAL subprocess, 139.86s
  MBPP battery re-run: pass n=48, accepted n=95->96 (baseline);
  GO/NO-GO: NO-GO (unchanged from every prior rung's own finding --
  the value-layer fix converts nothing new on this population)
  retires; pool_n = 10

  -> FIRST moment any AgendaVerdict{kind:'impotent'} mints in this scene
     (both re_measure goals now gone -- nothing routable):
     pool_n=10, nearest_unroutable_kind = decomposition_tier,
     nearest_unroutable_agid = ...missing_structural_primitive.tier1.0
```

**Step 3 — a GENUINE attempt at `mg_tier_retire`'s natural firing
condition**, reproducing A17 §4.1's own methodology exactly: a real,
stash-protected, sha-verified live re-run of the UNMODIFIED
`scripts/arc6_structural_ceiling.py` (A15's own second-`ExecClass` runner
script), reading the fresh witness set **before** restoring the protected
artifact (the SAME "read before restore" shape A17's own live test used).

```
protected artifact before: sha256 5af750cd4dcc7572a2164f5f360ff75b22e2bff…
live run: 0.06s, exit 0
tier 1 all_ids_covered (REAL, LIVE) = 0.0
tier 1 missing_ids = [18, 310]      <-- IDENTICAL to A17's own finding
protected artifact restored: byte-identical (verified)
```

**The gap has NOT closed.** Installing the REAL (declining) probe result
(not a constructed override) leaves the pool unchanged — `mg_tier_retire`
correctly, honestly declines to fire, exactly reproducing A17's own §4.1
result on a different day, a different engine build of the same source, and
a rebased tree. The FINAL state after this step is unchanged from the end
of step 2b: `pool_n=10`, `nearest_unroutable_kind=decomposition_tier`.

**This one state is already structurally distinct from both of A14's own
states** — different `pool_agids` signature (10 goals, not 7; four
`decomposition_tier` children present, `missing_structural_primitive`
itself absent) AND a different live `nearest_unroutable_kind`
(`decomposition_tier`, appearing in this sweep's real population for the
first time — A14's own group 4 only reached the `reported` kind via a
HYPOTHETICAL, out-of-seed-set construction; this kind is reached for real,
using capability already shipped).

---

## 3. THE CHEAP EXTENSION — a testimony chain on the NEW pool, A14 group-2's own mechanism, applied to a pool state A14 itself could never reach

Because A14's own `_leave_pool` (`headroom_n → 0`) technique for the two
`re_measure` goals is now cross-validated TWICE over on this exact new pool
— by A14's own original group-1s cross-check for row-verdict, and by
**this rung's own §2 real live executions** for BOTH goals — a second,
much cheaper measurement re-reaches the SAME 10-goal impotent pool without
repeating the 140-second subprocess, then chains real `attach_reply`
testimony against it, exactly mirroring A14 group 2's own already-real
mechanism:

```
boot -> decompose (real reply) -> synthetic exit, BOTH re_measure goals
  (the SAME already-validated A13 SS7.1 technique, re-validated for BOTH
  goals by this rung's own S2 live executions above)
  pool_n = 10, live winner = decomposition_tier   (matches S2's real result)

reply 1 (real attach_reply, unconditioned) -> live winner = supply_blocker
                                               (arc...budget)
reply 2 (real attach_reply, unconditioned) -> live winner = source_claim
                                               (arc6.claim.seam_b...)
reply 3 (real attach_reply, unconditioned) -> live winner = source_claim
                                               (UNCHANGED -- fixed point)
reply 4: 0 open questions left -- chain terminates naturally
```

Pool signature is **constant across the whole chain** (confirmed
programmatically) — exactly A14's own "testimony reweights without
changing membership" finding, one level up on the new pool. **Twin-run
determinism confirmed**: the entire boot → decompose → synthetic-exit →
reply-chain sequence, run twice independently, produces a byte-identical
`kind_sequence`
(`['decomposition_tier','supply_blocker','source_claim','source_claim','source_claim']`
both times).

---

## 4. IR1 — THE FIVE REAL-ONLY STATES, A TABLE NOT A BARE COUNT

Deduplicated by A14's own registered unit — `(pool_agids signature, LIVE
winner kind)`, the corrected view A14 §8 established (the STORED verdict
field freezes at first mint; the live winner does not) — quoting A14's own
two states rather than re-deriving them (their own mechanism is untouched
by this rung and re-verified unchanged by this rung's own regression gate,
§7):

| # | pool signature | kind | how reached | rung |
|---|---|---|---|---|
| 1 | 7-goal (`missing_structural_primitive` present) | `supply_blocker` | REAL live execution, row-verdict retires alone | A14 (quoted) |
| 2 | 7-goal (SAME signature as #1) | `source_claim` | REAL testimony chain (2-3 replies) on the SAME 7-goal pool | A14 (quoted) |
| 3 | 10-goal (4 `decomposition_tier` children, `missing_structural_primitive` absent) | `decomposition_tier` | REAL: decompose reply + BOTH `ExecClass`es to real completion, §2 | **A22 (new)** |
| 4 | 10-goal (SAME signature as #3) | `supply_blocker` | REAL: decompose reply + validated synthetic exit + 1 real testimony reply, §3 | **A22 (new)** |
| 5 | 10-goal (SAME signature as #3) | `source_claim` | REAL: decompose reply + validated synthetic exit + 2-3 real testimony replies, fixed point, §3 | **A22 (new)** |

`n=5`. This is the first time in this arc's history the real-only subset
has crossed A14's own registered `n≥5` power threshold.

---

## 5. IC2 / IC3 — RUN, QUOTING A14'S OWN FORMULAS VERBATIM

**IC2, exactly as A14 registered it**: *"CONCENTRATED if f ≥ 0.75. SPREAD if
f ≤ 0.50 … AMBIGUOUS in between, or if |S| < 5."* Computed with A14's own
`concentration_stat` function (`scripts/arc6_impotence_campaign_measure.py`,
imported, not reimplemented) over the five-row table above:

```
n = 5
kind_counts = {supply_blocker: 2, source_claim: 2, decomposition_tier: 1}
modal fraction f = 2/5 = 0.4
read: SPREAD          (0.4 <= 0.50; also true on substance -- no kind
                        reaches even half of the real-only population)
```

**IC3, exactly as A14 registered it.**

- **GO for (b)** requires (i) IC2 CONCENTRATED on real-only. **Not met** —
  SPREAD is definitionally not CONCENTRATED. Conditions (ii)/(iii) not
  evaluated (nothing to weigh a concentration finding against). **NO-GO for
  (b).**
- **GO for (a)** requires (i) IC2 SPREAD on real-only [**met**, above], AND
  (ii) A12/WH4's registered repricing-loop objection measured NOT to apply
  in this campaign's own group-2-style testimony-chain scenes (chain
  reaches a fixed point, does not cycle). **Met**: the §3 chain terminates
  after 3 replies (0 open questions remain), the winner kind stabilizes at
  `source_claim` for the last two replies before termination, and the whole
  scene (boot → decompose → exit → chain) is twin-run byte-identical.
  **GO for (a).**

**IC3 verdict: GO for (a), NO-GO for (b).** This is the FIRST time in this
arc's history either compound condition has read GO. A14 and A15 (which
never re-ran IC2/IC3, only checked the n-growth precondition and found it
null) both stood at NO-GO for both.

---

## 6. SHARPENING THE NEXT CHARTER — GO for (a) is NOT "go build (a) as A14 described it"

**This rung does not build (a).** Per this rung's own registered scope
boundary, a GO read names the next rung's charter; it does not license
building it here. What follows sharpens that charter, because a naive
reading of "GO for (a)" would understate what the next rung actually needs
to do.

**Why the naive reading is wrong.** A14 §"design investigation" finding 3
already identified the *mechanism* behind (a)'s own registered
repricing-loop risk: `REGION(g)` falls back to `g.agid` whenever `sig_seam`
is unset — true of every `supply_blocker`/`source_claim`/`decomposition_tier`
goal this tree has ever minted. This means `ag_ask`'s existing testimony
question **smuggles a presupposition**: "region ≈ single goal." A reply
penalises the ONE asked-about goal specifically, not a class of goals — not
an incidental property of (a)'s design, but the root cause of exactly the
risk IC3's GO-for-(a) condition (ii) has to check.

**This rung's own GO reading does not discharge that risk — it only fails
to trip it on the scenes measured.** The §3 chain that satisfied condition
(ii) was itself built on the SAME naive `ag_ask`/`REGION`-fallback
mechanism (per A14's own IC1 methodology, which this rung reused verbatim
— that mechanism IS what "a real `attach_reply`" means in this arc). A
chain that reaches a fixed point on ONE scene (here: a 10-goal pool with
two `supply_blocker` siblings, four near-identical `decomposition_tier`
children, and four `source_claim` goals, asked about in whatever order the
loop itself chose) is evidence the naive mechanism did not cycle on THAT
scene — not a proof the naive mechanism cannot cycle in general. A wider
scene (e.g. deliberately asking about each of the four `decomposition_tier`
children in turn, or forcing a return to an already-answered region) was
not attempted here, and might still expose cycling the measured chain
happened not to hit.

**The charter, stated precisely.** The next rung should build the
impotence-specific question **through `question_driver.py` /
`seeds/question_driving.json`'s existing gap-guard/contrast machinery
(`qd_bind_resolver`, decompose/fold-up/gap-guard/contrast rules)** —
machinery ALREADY BUILT in this tree for exactly the class of problem
`REGION`'s fallback creates (surfacing what a question presupposes before
asking it) and currently unused by `ag_ask` — **not as a naive reuse of
`ag_ask`'s `REGION` fallback with different wording.** A naive reuse would
inherit the same smuggled region≈agid presupposition this section just
named, and the repricing-loop risk would stay live even though THIS rung's
own IC3 condition (ii) read pass on the specific scenes it measured.

---

## 7. REGRESSION — A LIST OF NODE IDS, NEVER A COUNT

Both arms below ran on the SAME binary (`c5e50801d48a…`), in this
worktree, on the rebased tip (`02a71e3`); the BEFORE arm was measured
first, before the sweep script existed; the AFTER arm was measured after
the sweep script (and its two extension measurements) had already run and
written to the shared, symlinked `results/` directory.

| suite | before | after | failing node ids — **identical before and after** |
|---|---|---|---|
| `test_arc_executor_migrated` | 100 passed, 1 failed (101 collected) | 100 passed, 1 failed (101 collected) | `test_ex1_the_frozen_artifacts_are_STILL_byte_identical` |
| `test_arc_goals_migrated` | 37 / 37 | 37 / 37 | — |
| `test_goal_residual_migrated` | 29 passed, 1 failed, 1 skipped | 29 passed, 1 failed, 1 skipped | `test_gr4_the_live_mbpp_pass_ids_are_unchanged` |
| `test_arc6_valuelayer_migrated` | 35 / 35 | 35 / 35 | — |
| `test_arc_magnitude_migrated` | 43 / 43 | 43 / 43 | — |
| `test_arc_decompose_migrated` | 28 / 28 | 28 / 28 | — |

Both pre-existing reds are the **same two node ids every prior rung since
A12 has recorded** — `results/` is untracked in this checkout (`git show
HEAD:results/…` returns empty; this rung's own live measurements legitimately
overwrite `results/arc6_verdict_before.json`/`_after.json`/`_pricing.json`
as part of driving the row-verdict `ExecClass` to REAL completion — this is
the file's designed behaviour on every real remeasurement across every
worktree that shares this symlinked directory, not a hazard; A17's own
"protected, restored" language refers to a TEST's own stash around an
isolated canary run, not to production dispatch of a real order) and this
engine's short sha is not in `test_gr4`'s three-entry allowlist. Neither is
this rung's to fix, and neither was touched.

**Confinement, asserted not promised.** `git diff --stat HEAD -- seeds/
domains/ tools/ tests/ runners/` is empty throughout this rung — no seed,
adapter, or Rust file was edited. `results/arc6_structural_ceiling.json`
(the ONE protected artifact this rung's own §2 tier-witness probe
temporarily disturbed) was restored byte-identical, verified by sha256
before and after
(`5af750cd4dcc7572a2164f5f360ff75b22e2bff411f8f094fd944b023ebfa322`, MATCHES
A17's own documented pristine value). `results/arc6_a_ceiling.json`
(read-only upstream, never written by anything in this rung) is unchanged
(`c65bfc0e2b68012bcc4b11bc90174e96da22c5332a14779f437498b1a32b2c84`, MATCHES
A15's own documented value).

**Both trees verified clean.** This worktree's `git status --porcelain`
shows only the intended new files (the sweep script, this document, the
prereg amendment) and the two gitignored `data`/`results` symlinks. The
canonical tree's `git status --porcelain` was re-checked clean after the
process incident in §8.1.

---

## 8. EVERYTHING THAT BROKE

Recorded because the process is the result (A11–A21's own standing
practice).

### 8.1 A22's own amendment text was first written into the PRIMARY tree, not the worktree — caught by an outside reviewer, recovered without loss

Mid-rung, the `Edit` call that registered amendment A22 in
`PROGRAM_SYNTHESIS_ARC6_PREREG.md` was issued against
`/home/matt/ozmadev/ocelot` (the canonical, primary tree) instead of
`/home/matt/ocelot-arc6-impotence-resweep` (this rung's own isolated
worktree) — a path-discipline slip, not a content error (the amendment text
itself, once relocated, applied and read correctly). This was caught
**before** any further primary-tree pollution, the diff was saved to a
patch file, the primary tree was restored to a clean `git checkout --`, and
the patch was re-applied cleanly (`patch -p1 --dry-run` succeeded with zero
fuzz) inside this worktree. **Added to this arc's own standing process
discipline**: every subsequent file operation in this rung explicitly
qualified its target path against `/home/matt/ocelot-arc6-impotence-resweep`,
and `git -C /home/matt/ozmadev/ocelot status --porcelain` was re-checked
clean after the recovery and again at the end of this rung. No content was
lost; the only cost was the extra verification pass.

### 8.2 A rebase was needed mid-rung because `main` moved twice while this rung was running

Two unrelated merges landed on `main` during this rung
(`arc6-condition-lapse`/A21 — already reflected in this rung's own base
commit choice — and `risk-ladder-implementation`, an F-16 flight-control
thread this brief explicitly named as a concurrent, do-not-touch worktree).
`git diff --stat 0351084 02a71e3 -- docs/research/program_synthesis/ seeds/
domains/ tools/ tests/ scripts/ runners/` confirmed **zero** file overlap
(the risk-ladder merge touches only `f16_flight_path_control.json`/
`control_regime_escalation.json` and their own scripts/tests) before
`git rebase main --autostash` was run — clean, zero conflicts, engine sha
unchanged (the tracked `.so` content was untouched by either merge).

### 8.3 A small script bug, caught before any tree mutation

The first draft of the §3 cheap-extension script tried to
`headroom_n → 0`-exit the structural `re_measure` goal BEFORE forcing its
residual stale — but that goal's `ArcGoal` node does not exist until the
residual actually goes stale (a real mint-on-condition rule, not a bug),
so the helper's own `raise AssertionError("no such goal: …")` fired
immediately, before any `run_rules()` pass or tree mutation. Fixed by
forcing staleness first (mirroring the primary sweep script's own already-
correct step 2a ordering) and re-run.

---

## 9. REMAINING UNCERTAINTIES

Ordered by how much damage being wrong would do.

1. **IC3's GO-for-(a) reading rests on ONE testimony-chain scene.** §6
   already names the sharpest form of this: the naive `ag_ask`/`REGION`
   fallback mechanism did not cycle on the specific 10-goal pool this rung
   built, but a wider exploration (asking about each `decomposition_tier`
   child individually, forcing a return to an already-answered region, or
   running the chain under a DIFFERENT random reply order) was not
   attempted. This is exactly the gap §6's charter closes — build through
   `question_driver.py`'s gap-guard/contrast machinery, not a naive reuse.
2. **Only one chain variant (effectively order-N) was measured for this new
   pool** — decomposition is structurally order-N-scoped (it depends on
   `arc_magnitude`'s own ladder/`mg_rung` machinery), so unlike A14's own
   paired order-1/order-N chains on the 7-goal pool, this rung's new states
   have no order-1 analogue to cross-check against. Whether an order-1-only
   variant of this new pool state exists at all is an open, structural
   question this rung did not need to answer (decomposition requires
   magnitude by construction), not a gap in this rung's own methodology.
3. **`mg_tier_retire`'s own gap is UNCHANGED from A17** — ids `18`/`310`
   still missing from tier 1's witness coverage, reproduced live, on a
   different engine build, months later. This rung's own finding is that
   closing this gap is NOT what is needed to grow real-only `n` further (it
   already grew without it) — but closing it would still change the FINAL
   state once more (pool_n 10→9, and tier 1 would stop being the nearest-
   unroutable candidate), a further, not-yet-measured shift this rung did
   not need to chase to answer its own charter.
4. **A17's other two named, still-unbuilt candidates are unchanged by this
   rung's own investigation** (recorded for completeness, since IR3 itself
   does not fire — `n≥5`): (a) the `source_claim` condition-and-lapse gap
   (`ArcSourceClaim` carries no `stale`/`holds_under` apparatus at all —
   still a from-scratch invention, still a materially bigger, different
   build than anything measured here); (b) `budget`/`missing_dimension`
   (no bounded sub-claim analogous to tier 1's "these ids, already built" —
   `budget` has no natural termination by definition). Neither is better-
   scoped by anything this rung measured; both remain named, not costed.
5. **The `decomposition_tier` children's own internal diversity was not
   stress-tested.** All four tier children share the same `parent_agid`,
   the same source shape, and (per MG4b's own already-gated finding)
   DIFFERENT `magnitude_ratio`s but the SAME `push_back` rung at this
   horizon — whether asking about each one individually produces four
   genuinely distinct sub-states or collapses to the same few kinds (as the
   §3 chain's own experience suggests — only `budget` and `seam_b` were
   ever reached, never a tier child by name) is unmeasured.
6. **`REGION(g)`'s fallback-to-`g.agid` mechanism itself was READ, not
   re-derived or re-verified from the Rust source, in this rung** — it is
   quoted from A14's own already-registered, already-cited finding (§6).
   This rung's own contribution is connecting it to the specific GO
   reading measured here, not re-establishing it from scratch.

---

## 10. FILES

| file | what |
|---|---|
| `scripts/arc6_impotence_resweep_measure.py` | NEW — the primary sweep: boot, real decompose reply, both `ExecClass`es to real completion, a genuine live attempt at `mg_tier_retire`'s natural firing condition |
| `results/arc6_impotence_resweep.json` | NEW — its artifact, engine + both seed shas stamped |
| `results/arc6_impotence_resweep_testimony_chain.json` | NEW — the cheap §3 extension's artifact |
| `results/arc6_impotence_resweep_IC2.json` | NEW — the IC2 aggregation, computed with A14's own unmodified `concentration_stat` |
| `PROGRAM_SYNTHESIS_ARC6_PREREG.md` | amendment A22 appended, registered before this measurement |
| `PROGRAM_SYNTHESIS_ARC6_IMPOTENCE_RESWEEP.md` | this file |

**Nothing else changed.** `git diff --stat HEAD -- seeds/ domains/ tools/
tests/ runners/` is empty. `runners/dsl/python/substrate_rs/_native.abi3.so`
does not appear as modified (content byte-identical to the canonical
tree's committed binary; only its mtime was touched to clear the
git-worktree false-staleness refusal). `data` and `results` appear as
untracked **symlinks** into the canonical tree (gitignored) — not staged.

---

## 11. REPRODUCE

```bash
# --- the worktree ---------------------------------------------------------
git worktree add --detach /home/matt/ocelot-arc6-impotence-resweep <main-tip>
cd /home/matt/ocelot-arc6-impotence-resweep
git checkout -b arc6-impotence-resweep
ln -s /home/matt/ozmadev/ocelot/data    data
ln -s /home/matt/ozmadev/ocelot/results results

# --- the engine -------------------------------------------------------------
cp /home/matt/ozmadev/ocelot/runners/dsl/python/substrate_rs/_native.abi3.so \
   runners/dsl/python/substrate_rs/_native.abi3.so
touch runners/dsl/python/substrate_rs/_native.abi3.so   # clear worktree mtime false-staleness
sha256sum runners/dsl/python/substrate_rs/_native.abi3.so
#   c5e50801d48a170d3f16f2320f1e35eac355e0552a798faa9026d16bbbaaf567

# --- the coherence probe.  STOP if these read back the same. ---------------
PYTHONPATH=runners/dsl/python:. python3 -c "
import substrate_rs as srs; s=srs.Substrate()
a=s.node(s.add_node('T',{'lst':[1,2,3],'tup':(1,2,3)}))['attrs']
print(a['lst'], a['tup'], a['lst']!=a['tup'])"

# --- the baseline, BEFORE touching anything -- ALWAYS an explicit generous
#     tool-level timeout: this suite contains a REAL ~140-200s remeasurement.
for s in test_arc_goals_migrated test_goal_residual_migrated \
         test_arc6_valuelayer_migrated test_arc_magnitude_migrated \
         test_arc_decompose_migrated; do
  COLUMNS=250 OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
    PYTHONPATH=runners/dsl/python:. timeout 480 \
    python3 -m pytest tests/$s.py --confcutdir=$PWD -q -p no:randomly -rf
done
COLUMNS=250 OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  PYTHONPATH=runners/dsl/python:. timeout 480 \
  python3 -m pytest tests/test_arc_executor_migrated.py --confcutdir=$PWD -q -p no:randomly -rf

# --- the primary sweep (2 REAL remeasurements, ~0.13s + ~140s; ~2.5 min total)
COLUMNS=250 OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  PYTHONPATH=runners/dsl/python:. timeout 460 \
  python3 scripts/arc6_impotence_resweep_measure.py
#   -> results/arc6_impotence_resweep.json

# --- the regression arms, run identically before and after ----------------
#     (repeat the six-suite block above)
```

**Engine provenance.** Every number in this document was produced by
`c5e50801d48a170d3f16f2320f1e35eac355e0552a798faa9026d16bbbaaf567`, resolving
from inside `/home/matt/ocelot-arc6-impotence-resweep`.

**Contamination.** The MBPP test-split `code` is read only by the row-
verdict remeasurement's own, pre-existing, unmodified battery/report
scripts (the same ones every prior ARC-6 rung invoked) — their reads are
the measurement itself. Nothing entered a codebook, a cue table, or a route
table: no seed changed.
