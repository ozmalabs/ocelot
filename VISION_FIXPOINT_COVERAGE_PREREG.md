# FINISHING THE FIXPOINT RE-RUN — COVERAGE, EXECUTED BY CODE — PRE-REGISTRATION

*Written and committed BEFORE any measurement number exists. Seeds **98000–98999**.
Continues `VISION_FIXPOINT_RERUN_PREREG.md` / `..._RESULTS.md`, which answered
"does the fixpoint fix move any landed number?" with **YES** at **7.5% coverage**
(11 of 147 documents) and named its own unmeasured remainder.*

---

## 0. SEED CLAIM (§3 clause 8) — verbatim

```
SEED CLAIM 98000-98999: CLEAN -- no collision DETECTED.
  Scope: 805 files with seed sinks; 497 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

**Unresolved sink count: 497.**

**Like the predecessor, I DELIBERATELY RE-USE ALREADY-BURNED SEEDS and this is not
a §3 violation — it is the point.** Every arm re-runs each landed script on the
seeds that script already declares, because the comparison is fix-vs-revert on
IDENTICAL inputs; a replication that redraws is not a replication. Block
98000–98999 is reserved for material I draw myself (controls only), and I expect
to return it substantially unused.

## 1. THE QUESTION

The predecessor established that the fix moves at least one landed number, and
that **exposure is a property of the WORKLOAD, not the seed** — within one seed,
four of five workloads had zero exposure, making four of its five pre-registered
nulls VACUOUS. It stopped at 11 of 147 documents.

**My question: over the WHOLE population of landed result documents, which
others move, and what fraction of the tree's ACTUAL defect exposure have I
compared?**

## 2. THE DENOMINATOR CHANGES — and this is the methodological point

The predecessor reported coverage as **documents** (11/147) and ranked candidates
by **static race-constructible pairs** (316 across 95 consumers). Its own result
refutes that ranking: `time`/`depth`/`stereo`/`blink` all load the 34-pair
`shape_decode_loop` seed and all triggered **ZERO**.

So I pre-register a second, primary denominator:

> **EXPOSURE COVERAGE = (harmful-skip triggers observed in the documents I
> compared) / (harmful-skip triggers observed across every script I ran).**

A document with zero exposure contributes zero to both numerator and denominator:
its null is free and licenses nothing, which is exactly the accounting the
predecessor had to add retrospectively. I report BOTH denominators.

## 3. SELECTION RULE — STATED, AND EXECUTED BY CODE

The predecessor's stated error was writing a correct selection rule and then
hand-listing 5 of the 18 members it selects, with the mover among the missing 13.
**My rule is executed by a committed script, and I print the full selected set.**

> **RULE: a script S is selected iff an AST walk of S finds a string literal
> naming a `results/*.json` that exists in the tree, AND S contains a write call
> (`open(...,'w')` / `write_text` / `json.dump` / `write_bytes`).**

AST only — never a substring selector (§12). Executed by
`scripts/fixpoint_coverage_select.py`. **Its output as of this pre-registration:
160 result documents, 97 mapped to a producing script, 63 unmapped, 95 distinct
producing scripts.** The full list is printed into the results document.

**DECLARED BLIND SPOT OF THE SELECTOR (stated before measuring):** the 63
unmapped documents are unmapped because their output path is CONSTRUCTED
(f-strings, `argv`-driven, loop-generated) rather than a literal. My selector
resolves literals only. Those 63 are reported **NOT RUN**, never as unchanged.

## 4. THE FOUR NAMED SEEDS — a static finding, recorded BEFORE the run

The brief names `impasse_escalation` (41 race-constructible pairs, the largest),
`goal_derivation` (23), `nav_intent` (20), `grid_navigation` (16) as entirely
unmeasured. Executing my selection rule and searching the 95 producing scripts
for those seed names gives, **before any measurement**:

> **ZERO of the 95 result-producing scripts boot ANY of the four.**

They are booted only by agent/demo scripts (`arc_run.py`, `maze_run.py`,
`autonomous_speech.py`, …) that produce no `results/*.json`. **So the four
largest static consumers have NO LANDED NUMBER that could move.** That does not
make them uninteresting — it makes them a different question, which I
pre-register separately:

- **Q-A (landed numbers):** the 95-script sweep above.
- **Q-B (live runtime exposure):** boot each of the four seeds through a script
  that actually loads it and record HARMFUL_SKIPS. This measures whether the
  defect fires in the agent's live nav/escalation path. **A Q-B result is
  explicitly NOT a landed-number result** and will never be reported as one.

## 5. HYPOTHESIS AND PREDICTION (two-sided, §3.1/§3.7)

**H0:** no further landed document moves under the fix.
**H1:** at least one further landed document moves.

**MY PREDICTION: H1, but WEAKLY, and I expect the movers to be FEW and
CONCENTRATED in documents that (a) have nonzero exposure and (b) record a
STATUS or a COUNT produced by a post-mint ladder step.** Reasoning: the
predecessor's single mover was not a headline claim but an *aliveness positive
control* — a field whose whole job is to read nonzero. The defect ate the
ladder's LAST step, so the fields at risk are terminal-state readouts, not the
counts that precede them.

**My provisos, so a broken one is informative:**
- (a) I assume most of the 95 scripts have LOW or ZERO exposure, following the
  predecessor's 5519-vs-0 spread. If exposure turns out broad, my "few and
  concentrated" prediction is wrong and the fix's blast radius is larger than
  this arc has assumed.
- (b) I assume scripts are deterministic on their declared seeds. Where they are
  not, a difference is NOT attributable; I derive the noise floor empirically
  (§6) rather than asserting a timing-key list — the predecessor's hand-written
  filter fired zero times.
- (c) I assume the four named seeds have nonzero live exposure (Q-B). If they
  read zero, the "largest static exposure" ranking is refuted a second time and
  more strongly.

## 6. STATISTIC AND DECISION RULE

**The statistic is EXACT JSON EQUALITY of each result document, field by field,
against an EMPIRICALLY DERIVED same-engine noise set.** I do NOT hand-write a
list of timing keys to ignore — that instrument was measured inert by the
predecessor. The noise set is obtained by running the FIX arm **TWICE** and
taking the field paths that differ between two runs of the SAME engine.

- **A field differing fix-vs-revert AND NOT in the same-engine noise set ⇒ H1,
  THE NUMBER MOVED.** That outranks everything else; I report magnitude and
  direction and will NOT attempt to rescue any original claim (§5, §7).
- **All non-noise fields equal ⇒ a NULL, BOUNDED BY ITS EXPOSURE.** A null on a
  document whose HARMFUL_SKIPS is 0 is reported as **VACUOUS — NO POWER**, never
  as evidence.
- **"Unmoved" is earned PER NUMBER.** Any document not executed, or executed
  with a non-zero exit code, or timed out, is reported **NOT RUN**.

## 7. THE INHERITED HARNESS DEFECT — explicitly not inherited

The predecessor's runner **copied `results/*.json` even on FAILED runs**, so a
failed script would have compared identical-to-committed and counted as
coverage. My runner:

1. records the exit code FIRST;
2. copies an artifact **only** on `rc == 0`;
3. records the file's mtime and **refuses** an artifact the script did not
   actually rewrite during the run (a stale committed file is not evidence);
4. emits an explicit `NOT_RUN` record with a reason for every other case.

Rule 3 is a check the predecessor did not have at all, and it also catches the
subtler case of a script that exits 0 without writing.

## 8. METHOD — ENGINES, NOT HISTORY

Both engines are built **in my own worktree from this tree's source** via
`scripts/engine_build.sh` (§11.2 — never symlinked, never a global install):

- **ARM FIX** — tree as committed. Engine **`a1d350bbd23b`** (built; hash
  **identical to the predecessor's independently-built fix engine**, an
  unplanned reproducibility check that passed).
- **ARM REVERT+COUNTER** — the early-out `if self.rule_dirty[j] { continue; }`
  restored in `dirty_by_writeset`, plus the trigger counter of §9. Engine
  **`85f1f24567b4`**.

The arms MUST report different engine hashes; if they report the same hash the
revert did not take and the comparison is void.

**PROVENANCE (§10 rule 1b, landed this week):** `engine_preamble()` now RAISES
in-process on a wrong or stale engine. **I am deliberately loading a REVERTED
engine, which is a legitimate `strict=False` case, and per the rule's own text I
state so here and will state it again in the results.** Note that the revert is a
change to the TREE's Rust source and the engine is rebuilt from it, so source and
engine AGREE in both arms — provenance is honest in both, and the gate passes
strictly in both. `tests/test_engine_provenance_migrated.py` is run as its own
step on every engine before any number.

## 9. POSITIVE CONTROLS — every instrument shown ABLE to fail, BEFORE it is trusted

1. **The engine arms.** `tests/test_fixpoint_settle_migrated.py` must go RED on
   the reverted engine and GREEN on the fix engine.
2. **The trigger counter.** A `HARMFUL_SKIPS` counter compiled into the reverted
   engine, incrementing exactly when the early-out skips a consumer for which the
   fixed code would have cleared a NON-EMPTY cursor. It must fire on the
   reproduction arm that yields the WRONG answer.
3. **The counter's own contribution.** Read via two atomics through a PyO3
   function that does **not** boot a `Substrate` — so, unlike the predecessor's
   fallback, the instrument cannot contribute to its own reading. Verified to
   read `(0, 0)` at bare import.
4. **The comparator.** Before trusting any "identical", the comparator must be
   shown to REPORT a difference on a known-different pair — I diff the
   predecessor's committed `ARM_fix_codebook_axis.json` against
   `ARM_revert_codebook_axis.json` and require it to find the `n_exact` movement.
   **A comparator that has never reported a difference is not a comparator.**

**If any control is QUIET, I find out why before logging a pass.** The
predecessor's first power probe read a clean 0/2307 on a known-defective engine
because the defect satisfied its predicate; that is the failure mode this section
exists to prevent.

## 10. WHAT THIS DESIGN CANNOT SEE (§8)

1. **The 63 documents my selector cannot map** (constructed output paths). NOT RUN.
2. **Scripts that need absent `data/`** will fail and be reported NOT RUN, not
   unchanged. The tree's oracle is 212/10 without `data/`.
3. **Python-installed rules.** The predecessor's enumeration never scanned them.
   For me this does not bite the MEASUREMENT — differential execution is agnostic
   to how a rule was installed — but it does bite any static claim about which
   seeds are at risk, and I make no such claim.
4. **Non-vision landed results** outside `results/` are untouched.
5. **Wall-clock noise on a loaded machine.** Handled by the derived noise set,
   not by assertion; concurrent load is recorded.
6. **A script whose randomness is not seed-controlled** will show as a spurious
   mover; the same-engine replicate is what distinguishes that, and any mover
   that also differs same-engine is reported as NOT ATTRIBUTABLE.

## 11. WHAT A NULL WILL AND WILL NOT LICENSE

A null over this coverage licenses: *"the documents I ran, with the exposure I
measured, are byte-identical under fix and revert."* It does NOT license *"the
fix changed nothing else"* — the 63 unmapped documents, every failed or
timed-out script, and all non-`results/` landed numbers remain unmeasured. **A
document I did not execute is NOT REPORTED AS UNCHANGED — it is reported as NOT
RUN.** I will write that sentence in the results document whatever the outcome,
and I will report the exposure-weighted coverage fraction alongside the document
fraction so that a wide-but-powerless sweep cannot masquerade as thorough.
