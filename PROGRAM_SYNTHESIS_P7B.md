# PROGRAM SYNTHESIS P7 — track B: TRACE-GUIDED LOCAL REPAIR (results)

**Date:** 2026-07-31. Prereg: `PROGRAM_SYNTHESIS_P7_PREREG.md` (H7b; written
first). Deliverables: `seeds/program_synthesis.json` **v1.3.0** (38 → 43
rules), `domains/prog_synthesis.py` (2 new mechanical repair verbs + 3
one-line extensions of existing verbs), `tests/test_prog_repair_migrated.py`
(11 gates, green, ~1 s), `tests/test_program_synthesis_migrated.py` (+1
additive guard; the rule-count pin follows the version bump, the P6.5
precedent).

**The governing insight, applied to DIAGNOSIS:** *"ShapeDecode tells you what
is going on."* A failing row's TRACE — prefix evaluations at each statement
boundary, compared against expectations DERIVED by descent's own
row-derivation machinery — localizes the fault to a statement/hole. Repair
re-opens ONLY that hole; the counterexample propagates INTO the hole's
derived row set (this is what kills first-fit overfitting — P7-A residual 1);
the skeleton is never re-proposed.

## 1. The repair lane as landed (rules decide; the adapter is mechanical)

```
accepted ──(external verification fails a row)──────────────────────────────
  │   ingest_counterexample (adapter, mechanical): the failing row becomes
  │   an ExampleRow{ce_pending:1.0} on the goal's spec Message — a recorded
  │   datum, the ps_write_request precedent. The CEGIS oracle protocol:
  │   whoever verifies (a held-out check, the environment, a human) reports
  │   the row; the loop never peeks at unrevealed rows.
  ▼
ps_repair_mark     REFUTE: the Program keeps its provenance but is marked
  │                refuted; the accepted_program edge is RETRACTED (del_edge,
  │                the retire_duplicate_gap precedent) so ps_accept's
  │                mint-once guard re-arms. ps_repair_seq += 1 (integer round
  │                counter). → trace_pending
  ▼
record_trace       (adapter, mechanical): boundary FACTS for the ce rows —
  │                per-boundary {derivable, expect, got, agree} + the goal
  │                summary facts ps_trace_skel_agree / ps_trace_diverge_hole
  │                / ps_trace_derivable / ps_trace_json. Expectations are
  │                DERIVED, never guessed (§2). Fixed formulas — the ink
  │                ps_spine_ok class.
  ▼
  ├─ ps_localize_hole        the trace pinned the FOLDED hole (skeleton
  │     │                    boundaries agree, the divergence is at the
  │     │                    hole's grain) AND integer repair budget remains:
  │     │                    the refuted candidate → ExcludedSub at hole
  │     │                    scope; a NEW Hole{repair:1, same kind, same
  │     │                    construction} on the collision-free plan_seq
  │     │                    counter; ps_repair_attempts += 1 (OWN lane,
  │     │                    never ps_attempts — P6.5 discipline).
  │     ▼
  │   THE UNCHANGED DESCENT MACHINERY runs the re-opened hole:
  │   derive_hole_rows (now over outer rows INCLUDING the ce row — the
  │   propagation) → spawn_subgoal (carries the exclusion facts §3) →
  │   sub-goal ladder → fold_up re-verifies the FULL rows (ce included)
  │   → ps_foldup_accept → verified → ps_accept mints the REPAIRED Program
  │   (sub-solve fails → ps_hole_failed → descend_exhausted → the global
  │   enumerate-then-gap fall-through, honest)
  │
  ├─ ps_localize_refuse_fresh / _descended    localization HONESTLY REFUSES
  │     (no folded hole — e.g. a rung-1 accept has no skeleton/hole split;
  │     or no derivable expectation — e.g. a multi-item row against a fold
  │     body; or a skeleton boundary itself diverged): the UNTOUCHED global
  │     CEGIS path proceeds — ps_attempts += 1, all rows re-evaluated,
  │     ps_row_fail → ps_counterexample → Excluded → re-proposal /
  │     enumerate / gap, exactly the pre-P7B rules. (The _descended variant
  │     also sets ps_descend_done so a spent descent rung cannot park the
  │     goal on pending — the P6.5 zero-parks discipline.)
  │
  └─ ps_repair_exhausted     localizable but ps_repair_attempts ≥
        ps_repair_budget (integer, 2): no repair round N+1 — the same
        global fall-back, then the honest terminal.
```

New rules (5): `ps_repair_mark`, `ps_localize_hole`,
`ps_localize_refuse_fresh`, `ps_localize_refuse_descended`,
`ps_repair_exhausted`. Edited (1): `ps_goal` (the Goal mints the repair
counter lane: `ps_repair_attempts`/`ps_repair_budget` (integer 2) +
`ps_repair_seq`/`ps_trace_seq` (freshness pair, −1 sentinel)). New
production: `Goal -ps_sub_excluded→ ExcludedSub`. Adapter verbs (2, facts
in/facts out): `ingest_counterexample`, `record_trace`; existing verbs
extended mechanically: `fold_up` records `solved_term_json` on the hole it
judges, `spawn_subgoal` transcribes hole-scope exclusions onto the sub-spec,
`run_enumerate` passes a consts list when drop facts are present.

## 2. Localization: derivability scopes (the same table as descent, at trace grain)

| accepted shape | derivable boundary expectation | divergence verdict | refusal boundary |
|---|---|---|---|
| **final_expr skeleton** (v_i := covered template_i; return hole) | each covered construction's template re-evaluated on the ce row's own inputs (the `_derive_final_expr` walk) — the v_i boundaries | skeleton boundaries agree ⇒ the fault is the return (the hole) | a trapping / non-scalar template evaluation makes the row non-derivable — refuse |
| **fold_step skeleton** (return Fold{literal init, holed body}) | a SINGLETON ce row pins the one-iteration unroll: acc_before = init, item = the element, acc_after = the row's expected (the `_derive_fold_step` scope) — compared against the HELD body evaluated at that point | held body value ≠ pinned acc_after ⇒ the fault is the fold body (the hole) | multi-item ce rows pin nothing — counted, refused, global path |
| **rung-1 codebook accept** (no skeleton/hole split) | none — the return IS the covered template | — | always refused: there is no hole to blame; the global CEGIS path is the correct repair |

The refusal is honest by construction: `ps_trace_diverge_hole` /
`ps_trace_skel_agree` are recorded facts (prefix evaluation — pure, fueled),
and the refuse rules fall to a path that is byte-identical to pre-P7B
machinery (gated: the decoy scenario repairs itself via fresh attempt →
CounterExample → exclusion → re-proposal → correct accept).

## 3. Multi-candidate holes (P7-A residual 1, closed as far as the contract allows)

`SynthEnumerate` is deterministic first-fit with observational-equivalence
pruning — excluding a candidate WITHOUT changing the Term's input is a no-op
by construction. The honest input shifts, in force:

1. **The grown row set (the load-bearing one).** Every successful
   localization propagates the ce row's contribution into the re-opened
   hole's derived rows. By construction the refuted candidate cannot fit the
   grown set (it was refuted by exactly the row that joined), so the
   re-solve can never return it — exclusion-by-rows, sound and free. This is
   what "la-class holes get a second row and stop accepting Lit constants"
   is, verbatim, in the fold gate: rows `(acc=0,x=5)→10` + propagated
   `(acc=0,x=3)→6` retire `Lit 10`; the re-solve finds `(x + x)`.
2. **ExcludedSub at hole scope (provenance + drops).** `ps_localize_hole`
   mints `ExcludedSub{term, kind, repair_seq}` (bounded by the integer
   repair budget); `spawn_subgoal` transcribes them onto the sub-spec
   (`ps_enum_excluded`), and an excluded BARE-LIT value becomes a droppable
   const (`ps_enum_drop_consts`) that `run_enumerate` subtracts from the
   Term's documented default const set.
3. **Honest contract boundary (measured, `synth_enumerate.rs`):** the Term
   RE-APPENDS integer-valued spec outputs to any caller-passed consts, so an
   excluded Lit whose value is a spec output cannot be dropped this way —
   for the dominant Lit-overfit class the row growth is the killer and the
   drop is provenance. **Op-restriction shifts were considered and
   REJECTED:** dropping the refuted term's root op can exclude the TRUE term
   (e.g. dropping `Plus` after `(x+x)` fails would also kill
   `acc + (x + x)`) — an unsound restriction. A Rust-side `exclude`
   parameter is the named lever if within-round iteration is ever needed
   (none of the corpus mass needs it — §4).

## 4. The 4-id before/after (the P7-A holdout_fail set — this track's primary targets)

Protocol (declared, part of the claim): the CEGIS oracle protocol — after an
accept, held-out rows are checked in order and the FIRST failing row is fed
back via `ingest_counterexample`; repeat. "holdout_ok" = the final accept
passes ALL held-out rows including those never revealed. **The frozen battery
artifact is untouched and battery rows do NOT move on this track's account:
the battery protocol (track D) feeds no verification rows, and without a
`ce_pending` row the repair lane is provably inert (gated twice).**

| task (P7-A: accepted_holdout_fail) | ce rounds | localized | after | attempts accounting (post-failure work) |
|---|---|---|---|---|
| `la_10_count_positives` | 1 | final_expr | **accepted_holdout_ok** — row `(v1=5)→3` enters the hole rows; re-solve `min(3, (-1 + max(v1, 1)))` fits all four AND the never-revealed held-out row (`v1=3→2`, pinned by an example row) | **repair: 0 outer attempts + 1 hole re-solve** vs global re-proposal (counterfactual, same knowledge from scratch): 1 codebook attempt + 2 hole solves — **1 < 3**, gated |
| `la_11_count_evens` | 2 | final_expr ×2 | **gapped:enumerate_failed (honest terminal)** — round 1 re-fits (`v1/(v1 − min(v1,2))`), round 2's ce makes the hole rows CONTRADICTORY (both held-out rows have v1=3 with outputs 3 vs 1) → sub-solve honestly fails → global fall-through | 2 repair attempts = the integer budget, exactly |
| `la_21_count_zeros` | 1 | final_expr | **gapped:enumerate_failed (honest terminal)** — the ce `[0,0,0]→3` contradicts the example `(v1=3)→2` immediately | 1 repair attempt |
| `la_29_count_above_ten` | 1 | final_expr | **gapped:enumerate_failed (honest terminal)** — the ce `(v1=3)→1` contradicts the example `(v1=3)→2` | 1 repair attempt |

**Why the three non-conversions are genuinely unreachable (gate what IS,
proven in-gate):** (a) at live-var grain, held-out rows share `v1 = len`
with rows of different expected output — NO function of the live vars
exists (`test_headline_unreachable_ids_reach_honest_terminals` measures the
collision from the fixture rows); (b) at fold grain, the ce rows are
multi-item — the unroll pins nothing (the prereg'd non-determinable class,
never guessed) — and even with rows, the needed bodies are outside the
enumerator's reach: parity has no op in the kernel table (`Div` is real
division; no `Mod`/floor), and `count_above_ten` needs the constant 10,
which is neither a default const nor a spec output. The honest terminal
(`gapped:enumerate_failed`, one SelfConcern, zero parks) replaces a
standing WRONG accept once the verifier reveals the failure — the refuted
Program is retracted and kept as provenance (`refuted: 1`).

**H7b readings:** attempts-per-accept falls on the converted task
(mechanism-gated: 1 unit of post-failure work vs 3 — and the outer
`ps_attempts` counter is UNCHANGED through a successful repair, which is the
"no global re-proposal" claim in one integer). Parks stay 0 in every
scenario (each gate sweeps every synth_program goal for a terminal status).
The registered-null half of H7b holds for 3 of the 4 ids: local repair
converts nothing the row-level information cannot determine — reported above
as the attempted-repair taxonomy, per prereg.

## 5. Locality (gate 2, the proof shape)

On the converted task the old (refuted) and new Program IRs are compared
statement-by-statement as canonical JSON: every covered-span statement
byte-identical; ONLY the final `ProgReturn` (the localized hole's sub-IR)
differs. Alongside: `ps_attempts` 1.0 → 1.0, the exclusion set unchanged,
`ps_cover_json` byte-identical, `ps_descent_decoded` still the single
original pass (ShapeDecode ran ONCE, at descent time), `rungs.enumerate is
None`. The fold gate proves the same at fold grain: `source` / `init` /
`acc_name` / `var_name` unchanged, only `body` differs.

## 6. Gates (all green at this commit)

`tests/test_prog_repair_migrated.py` — **11 passed, ~1.0 s**: headline
conversion (la_10 → holdout_ok with the unrevealed row passing; frozen-row
cross-checked) + 3 honest terminals (with the in-gate unreachability
measurement); locality (canonical statement compare + provenance counters);
counterexample-into-hole (pinned `(v1=5)→3` as the 4th derived row; the
ExcludedSub equals the refuted return expr); refusal → the untouched global
CEGIS path (decoy accept repaired to `max_of_two` at attempt 3 with the
standard CounterExample/Excluded artifacts; refuted Program retracted+kept);
fold_step repair (singleton-ce unroll localization, Lit death by second row,
input-shift facts `ps_enum_drop_consts=[10]` / `ps_enum_excluded` on the
sub-spec, fold locality); budget honesty (budget forced 0 → `gaveup`, no
repair hole, global path → honest gap); attempts accounting (both arms
measured); repair-lane inertness (idle fixpoint: zeros, no ExcludedSub, one
Program).

Neighbors, unchanged behaviour: `test_program_synthesis_migrated.py` **17
passed** (16 P4/P6.5/P7-A gates untouched — the only edit is the rule-count
pin 38 → 43 per the version bump — plus 1 additive repair-inertness guard);
descent **15**, battery gate **11 over the UNMODIFIED artifact**, selfimprove
**5**, chunks **11**, code-synthesis baseline **11**, prog_ir **54**,
prog_constructions **10**. The no-Python-decision source audit re-ran green
over the modified adapter (the new verbs are prefix evaluation + record and
mechanical transcription of rule-minted facts; no argmin/argmax, no
sort-on-score).

## 7. Honest residuals

1. **Repair sees only what a verifier reveals.** The lane converts a wrong
   accept exactly when a failing row is INGESTED (held-out check, live
   environment, human). The battery number does not move on this track's
   account; whether track D's protocol includes a verification-feedback arm
   is track D's registered decision, not this one's.
2. **Within-round candidate iteration is contract-blocked for output-valued
   Lits** (§3): the Term re-appends integer spec outputs to caller consts,
   and op-drops are unsound. Corpus mass needing it: none found (row growth
   covered every reachable case). Named lever: a Rust `exclude` parameter on
   `SynthEnumerate` (out of scope here — no Rust).
3. **Fold-grain localization requires a SINGLETON ce row** (the prereg'd
   derivability scope). A multi-item ce against a fold-step accept refuses
   to the global path — correct but coarse; pinning interior fold boundaries
   would need either inversion (rejected) or a trace-emitting `ProgEval`
   (a possible Rust lever, same family as residual 2).
4. **acc-dependence is invisible to singleton-derived fold rows** (all have
   acc = init): a body whose acc-usage matters on multi rows can be
   observationally equivalent to an acc-free term on every derivable row —
   first-fit then fails fold-up and no input shift can surface the acc
   variant (it is PRUNED as equivalent, not merely ranked lower). The
   final_expr plan rescues the corpus cases (it did for la_20's family);
   the principled fix is a non-init derivable row source, none of which
   exists under the current scopes — documented blocker, unchanged from
   P7-A's scope table.
5. **The three unreachable ids stay unreachable by design honesty**, not by
   budget: count_evens needs parity (no op), count_zeros/above_ten need
   predicates over the ELEMENTS at fold grain with only final_expr-grain
   information derivable from their specs. These are P7-C-shaped gaps
   (codebook/chunk content: a `count-matching` fold shape with a predicate
   hole), not repair-shaped ones.
6. **`ps_repair_budget` (2) is a minted constant** on `ps_goal`, not
   adaptive; the exhaustion path is gated, the constant is not tuned.
