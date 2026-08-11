# DOES `run_rules` RETURN OVER UNSETTLED STATE? — PRE-REGISTRATION

*Written and committed BEFORE any measurement (PROTOCOL §3).*

**Branch actually in use: `worktree-agent-ad325918cc2ff96ac`** — NOT the
intended `gamma-substrate/fixpoint-settle`. The worktree was created with an
auto-generated name, as the last ten rungs were. Recorded here rather than
silently renamed.

**Base SHA:** `e8bf398747c4b14f54a8519d234b0667f246438a`.

**Seed block allocated: 85000–85999.** This rung is expected to draw **ZERO**
seeds — its instrument is a deterministic engine reproduction, not a sampled
corpus. I will run `scripts/seed_audit.py` and report the measured draw and
the `unknown_sinks` count regardless; a zero I did not measure is not a zero.

**Engine:** this rung ADDS RUST (a `#[cfg(test)]` regression test at minimum),
so the shared canonical build is NOT legitimate. I will build this worktree's
own engine with `scripts/engine_build.sh` (never a bare `cargo build`, never
rebuilding the canonical tree, §11) and run the provenance gate as its own
step, pinning BOTH endpoints of every range (`tests/test_provenance_endpoint_guard_migrated.py`
fails any range ending at `HEAD`).

---

## 0. WHY THIS RUNG EXISTS

Two landed rungs independently reported the same-looking scheduling
behaviour, neither of them looking for it:

1. **`VISION_MOTION_OBJECTS_RESULTS.md` §8.1** — `run_rules` returned **0
   further sweeps** over a flood in which **6 cells still had an admissible
   neighbour carrying a smaller label**, and the guard evaluated `True` on
   exactly those cells when applied by hand. The stated trigger: *"a guard
   reads an attribute written mid-fixpoint on a node outside its own match
   neighbourhood (`field.mtol`)."* Broadcasting the attribute onto the cells
   did NOT fix it; only having it present before the first flood binding was
   evaluated did.
2. **`VISION_CUT_MINT_POLICY_RESULTS.md` §2** — `Substrate::run_rules`
   schedules every dirty rule **in one pass, in index order, with no break**,
   so `is_decide` (writing `status`) and `is_mint` (reading it) fire in the
   same pass; the policy rule only works installed *between* them.

The supervisor unified these **from two report summaries, not from the
code**, and has explicitly flagged that they may have different causes. That
possibility is a registered outcome here, not a fallback.

## 0.1 WHAT I READ IN THE CODE BEFORE MEASURING

Recorded before measuring, per the locality-index precedent.

`Substrate::run_rules_opts` (`runners/dsl/src/substrate.rs` ~1884) is **not**
a single pass. It is a `while steps < max_steps` loop with two exits:

- a fast exit at pass top when **no active rule is dirty**;
- `if !any_progress { return steps; }` at pass bottom.

So the cut-mint rung's "one pass, no break" is accurate **per pass** but the
outer loop does iterate. A rule that misses its cue in pass *n* should fire in
pass *n+1* — **unless it is never re-enumerated**. That is the crux, and it
means the cut-mint observation is NOT self-evidently a fixpoint defect; it
needs the same second mechanism the motion rung hit.

The candidate second mechanism is already **named in the engine's own trace
string** (`try_incremental_match`, ~line 1605):

> `*** ALL ZERO: no new driving edges -> nothing scanned -> rule CANNOT fire this pass even if its where is now true (the stable-edge attr-gated bug) ***`

`try_incremental_match` is semi-naive: it enumerates bindings driven **only by
edges new since the rule's cursor**. A rule whose match-edges are stable
enumerates **zero** — while `rule_cost_count` still increments (the locality
rung's "an enumeration count is not a scan count").

There IS a mitigation, and it must be accounted for before claiming a bug:
`dirty_by_writeset` (~527) clears a consumer's cursor — forcing full re-match
— when the firing rule's `write_set` meets the consumer's `read_set` on an
`Attr` key AND the consumer has a where-clause. **So the defect cannot be the
bare stable-edge story; it requires that mitigation to MISS.** Registered
candidate misses, to be discriminated: (a) `read_set` under-approximates
(a where-clause reaching an attr through a Term-tree / Concept indirection
the read_set never recorded); (b) `write_set` under-approximates; (c) the
mutation does not come from a rule effect at all (adapter write between
`run_rules` calls, or a queued/deferred effect drained between passes);
(d) `rule_has_where[j]` false for a rule that nonetheless gates on an attr.

**I am registering that the supervisor's offered lead — "stale-but-valid
cursor" — is NOT what I found in the code.** The cursor in the motion story
is *valid*; the enumeration is empty because the driving edges are *stable*.
Those are different conditions and I will not report the lead's wording as
confirmed if the mechanism is the one I actually find.

---

## 1. THE VERDICT QUESTION, DECIDED FIRST

**Is `run_rules` specified as a FIXPOINT or as ONE PASS?** Registered
sources, to be read and quoted before any fix is proposed: the doc comment on
`run_rules` / `run_rules_opts`; the existing `#[cfg(test)]` tests around it;
`CLAUDE.md`'s claim that *"the `run_rules` fixpoint IS the decode → grow →
re-decode loop"*; `SPEC.md`.

- If **specified as one pass** → the seeds assuming multi-pass convergence
  are wrong; the deliverable is documentation plus explicit phase flags, and
  the two rungs' workarounds were correct all along.
- If **specified as a fixpoint** → the engine is wrong, and the deliverable
  is the precise condition under which it returns early.

I will state this verdict **before** proposing anything. I will not conclude
"bug" merely because the behaviour surprised two competent authors.

## 2. THE REPRODUCTION — the deliverable's spine

A minimal graph + rules where `run_rules(max)` returns while an admissible
binding remains. Registered acceptance criteria, fixed now:

- **R1** `run_rules` returns a step count; a subsequent independent check
  finds at least one rule whose where-clause is TRUE on a binding that was
  never applied.
- **R2** the same graph, with the enabling attribute present **before** the
  first pass, settles completely — matching the motion rung's fix.
- **R3** it is committed as a regression test that **fails on the current
  engine** if the condition is real. A test that passes today proves nothing.

If I cannot build R1, that is a **publishable negative**: the two observations
would then have causes not reducible to a minimal engine-level case, and I
will report the reproduction as FAILED rather than weakening the criteria
(§5 — no metric surgery, and no acceptance-criterion surgery either).

## 3. DISCRIMINATING THE CONDITION

For whichever mechanism reproduces, I will discriminate among:
(i) match set created by another rule in the same pass; (ii) batch
application showing a rule pre-pass state; (iii) stale cursors;
(iv) dirty-bit propagation missing an edge type; (v) the stable-edge
attr-gated path with a `dirty_by_writeset` miss.

Discrimination is by **direct instrumentation of the engine path taken**
(which branch of `try_incremental_match` / whether the cursor was cleared),
not by inference from the outcome. An outcome consistent with two mechanisms
discriminates neither.

## 4. BLAST RADIUS — enumerated, not estimated

The exposure set is statically findable from rule bodies: ordered pairs
(A, B) where A writes an attribute key K and B's where-clause reads K, split
into STABLE-EDGE (exposed) vs EDGE-DRIVEN (order-robust by construction), with
an explicit **UNDETERMINED** bucket. Parsed by **AST/JSON walk, never
substring selectors** (§12). The enumeration's blind spots (dynamic attr keys,
Term-tree indirection, rules installed from Python) will be stated as limits
on coverage — an enumeration with unstated blind spots is worthless, and the
instrument-discipline lesson that "a detector built from observed instances
covers observed instances" applies directly.

I will **name the exposure**, not re-litigate the landed rungs.

## 5. THE INSTRUMENT'S POSITIVE CONTROL

`assert_settled` fired once, then discarded **0 of 160**. That is the shape of
a check that has stopped being able to fire (the standing lesson: *a gate that
has never been ABLE to fail has not been tested*; three provenance gates sat
green 51 commits then all fired at once as false accusations).

Registered control: construct a field that **IS** unsettled and demonstrate
`assert_settled` goes **RED** on it. Pass criteria:

- **P1** an unsettled field → the check raises/returns failure.
- **P2** a settled field → the check passes (no false positive).

If P1 fails, `assert_settled` is a DEAD INSTRUMENT and the motion rung's
"0/160 discarded" means nothing — I will report that plainly, as the
term-eval rung reported its dead instrument.

## 6. REGISTERED OUTCOMES — all publishable

1. **Genuine engine bug** with a named, reproduced condition.
2. **Correct as specified**; the seeds are wrong; fix is docs + phase flags.
3. **The two observations have DIFFERENT causes** and were wrongly unified.
4. **No minimal reproduction** — the condition does not reduce to an
   engine-level case, and the unification is unsupported either way.

## 7. STOP CONDITIONS

- I will not propose an engine change without a reproduction that fails first.
- I will not report the supervisor's "stale cursor" wording as the mechanism
  unless the instrumented path shows a stale cursor.
- I will not report "0 seeds drawn" without running the audit.
- Bounds (§8): a single-condition reproduction bounds the condition, not its
  frequency in the wild; the blast radius bounds candidate exposure, not
  demonstrated breakage. I will keep those two claims apart.
