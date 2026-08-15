# Program Synthesis — Rungs 1, 2, 4 reconciliation against the reassessment PREREG — RESULTS

**Status, headline, one line per rung:**

- **Rung 1 (§5.1, 10 Tier-1 stdlib Term ports): ALREADY BUILT, as this
  PREREG's own direct fulfilment.** GO, merged, MBPP 49→54, +5/0 regressed.
- **Rung 2 (§5.2, both named items): ALREADY BUILT AND STILL LIVE, both
  sub-items.** The `_wire`/`_unwire` symmetric input-side fix converted task
  106 (+ a bonus, 115) as designed, MBPP 54→56, and — checked directly
  against current `main`, not assumed — **survived the later
  wire-boundary-systemic-audit unchanged in effect**: task 106 is
  confirmed passing in the CURRENT `results/mbpp_endgame.json`
  (`measured_at: 2026-08-15T23:06:50+1000`). The `decode_value` bare-array
  question (§5.2's second item) was never left open — it was decided
  **before this PREREG was even drafted**, deliberately, in
  `VALUELAYER.md` §9.2 itself ("stays `Tuple`"), and has been re-affirmed,
  unchanged, by every later rung that touched the boundary.
- **Rung 4 (§5.5, `SynthesisOperatorShape` alignment): PARTIALLY built,
  correctly NOT fully built, and — by the PREREG's own stated
  precondition — NOT YET RIPE to build further.** The tiebreak half of
  item 1 ("delete the implicit tie behaviour") is fixed and merged
  (commit `9365017`, explicitly citing this PREREG by name). The
  structural-match half of item 1 and all of item 2 ("Grow": mint a new
  operator-shape from a residual) remain completely unbuilt — the seed
  file has had exactly 2 commits in its entire history (initial import,
  then the tiebreak fix) and the shape population is still exactly the 2
  hand-authored entries the PREREG itself measured. This document does
  **not** build the remainder: the PREREG's own §5.5 closing line says to
  build it "after Rung 1 has shipped a few more operator-shapes to season
  the classifier" — and nothing has added a third operator-shape since,
  so that precondition has not been met, and building growth machinery
  for a 2-entry population would repeat the exact mistake `SHAPE_AUDIT.md`
  named ("a shape matcher built before there is a shape to match").

**Investigation-only. No new code, seed JSON, or tests were written by
this task** (beyond this document itself, and the git/file reads used to
produce it). All three findings are established by reading current `main`
source and `git log` directly, per this task's own instruction, not by
trusting any prior document's self-report.

Base for every claim below: `main @ c4f630f` ("Merge progsyn-rung3-sort-pricing:
term:Sort pricing was already resolved, retroactively GO"), verified via
`git log --oneline -1 main` immediately before starting — the same tip
`PROGRAM_SYNTHESIS_RUNG3_SORT_PRICING_RESULTS.md` used, confirming this
document continues from exactly where that one left off rather than
re-deriving a stale base.

---

## 0. The chronology that explains all three findings at once

The reassessment PREREG (`PROGRAM_SYNTHESIS_STRUCTURAL_CEILING_
REASSESSMENT_PREREG.md`) was committed to `main` as `1d7d437` ("Add
orphaned PREREG…") at **2026-08-15 23:11:17**. But `git log --oneline
--ancestry-path fecd35e..c4f630f` shows the PREREG's own §5.1/§5.2 work
was already committed to `main`, as direct linear ancestors of `1d7d437`,
**a day earlier**:

| commit | what | date |
|---|---|---|
| `5b8c2c7` | Rung 1: 10 Tier-1 stdlib Term ports, MBPP 49→54 | 2026-08-14 14:33 |
| `aecfe8b` | Rung 2/3 PREREG (inputs_json fix design + Sort pricing) | 2026-08-14 15:15 |
| `5bca8b2` | Rung 2: inputs_json symmetric wire/unwire fix, MBPP 54→56 | 2026-08-14 16:05 |
| `9365017` | `SynthesisOperatorShape`: delete the Argmax tiebreak | 2026-08-14 20:34 |
| `0c119f1` | wire-boundary-systemic-audit: retire hand-rolled `_wire`/`_unwire` for the engine's own codec | (merge, before `1d7d437`) |
| `1d7d437` | **Add orphaned PREREG** (this document's brief) | 2026-08-15 23:11 |
| `c4f630f` | Merge progsyn-rung3-sort-pricing | (current tip) |

`git merge-base --is-ancestor <commit> 1d7d437` returns true for every row
above except the last two. **The document naming these four rungs was
committed to `main` roughly a day after three of the four rungs it names
were already built and merged**, and the fourth (Rung 4) had already
received a partial fix. This is the identical "orphaned document" pattern
`PROGRAM_SYNTHESIS_RUNG3_SORT_PRICING_RESULTS.md` diagnosed for Rung 3 —
here it turns out to apply, to different degrees, to all three remaining
rungs at once. `PROGRAM_SYNTHESIS_STRUCTURAL_CEILING_RUNG1_RESULTS.md` and
the Rung 2 results doc both **explicitly cite the reassessment PREREG by
name and section** as their own prereg (§1 below), which is how commits
that predate `1d7d437`'s own commit timestamp can nonetheless be its
direct, intentional fulfilment — the PREREG's content was evidently
drafted and acted on before its own file landed on `main`'s linear
history.

---

## 1. Rung 1 (§5.1) — 10 Tier-1 stdlib Term ports

### 1.1 Found built, cited, and verified

`git log --oneline -- docs/research/program_synthesis/PROGRAM_SYNTHESIS_STRUCTURAL_CEILING_RUNG1_RESULTS.md`
→ one commit, `5b8c2c7`. Reading that document's own opening lines
(`docs/research/program_synthesis/PROGRAM_SYNTHESIS_STRUCTURAL_CEILING_RUNG1_RESULTS.md:1-8`):

> Prereg: `PROGRAM_SYNTHESIS_STRUCTURAL_CEILING_REASSESSMENT_PREREG.md`
> §5.1 ("Rung 1 (primitive layer, do this first) — Tier 1 stdlib Term
> ports, exactly `STRUCTURAL_CEILING.md` §9's own prioritised order").
> Base `main @ 1480d48` … Worktree
> `/home/matt/ozmadev/ocelot-worktrees/progsyn-rung1-tier1`, branch
> `progsyn-rung1-tier1`.

`1480d48` is the exact base commit the reassessment PREREG itself declares
(`PROGRAM_SYNTHESIS_STRUCTURAL_CEILING_REASSESSMENT_PREREG.md:3-4`: "Base
`main @ 1480d48`"). This is not a coincidental match to an older,
differently-scoped rung (as happened with the old `PROGRAM_SYNTHESIS_
STRUCTURAL_CEILING_RUNG2_RUNG3_PREREG.md` naming, see §2) — it is the same
base commit, the same document, the same section number, cited by name.
**Verdict: (b), built AS this PREREG's own fulfilling commit.**

### 1.2 What was built and measured, confirmed against current `main`

All ten Terms (`Replace`, `Str`, `Split`, `StrCount`, `Round`, `Reverse`,
`IndexedMap`, `Capitalize`, `ParseInt`, `Slice`) landed exactly per
§5.1's table and ordering (`Slice` last, per its larger blast radius).
Rust suite 774/774 before and after (byte-identical);
`NUM_TERM_VARIANTS` 213→223. Live MBPP: **49→54, +5 net, zero
regressions** (exact set comparison, not aggregate counts, per the
document's own §3). Merged as `fecd35e`.

**GO, no further action.** Nothing about the current `main` state
contradicts or supersedes this rung; no later commit touches any of the
10 new `TermNode` variants' evaluators.

---

## 2. Rung 2 (§5.2) — `inputs_json` symmetric fix + the `decode_value` question

### 2.1 The first item: symmetric `_wire`/`_unwire` on the input side

**Built, and confirmed built specifically as a continuation of the
reassessment PREREG.** `PROGRAM_SYNTHESIS_STRUCTURAL_CEILING_RUNG2_RUNG3_
PREREG.md` (commit `aecfe8b`) opens (`:1-9`):

> Base `main @ fecd35e` ("Merge progsyn-rung1-tier1…"), verified via `git
> log --oneline -1 main` immediately before branching. Worktree
> `/home/matt/ozmadev/ocelot-worktrees/progsyn-rung2-rung3`, branch
> `progsyn-rung2-rung3`. Continues `PROGRAM_SYNTHESIS_STRUCTURAL_CEILING_
> REASSESSMENT_PREREG.md`'s own plan (§5.2 Rung 2, §5.3 Rung 3) and
> `PROGRAM_SYNTHESIS_STRUCTURAL_CEILING_RUNG1_RESULTS.md`'s already-shipped
> Rung 1.

The design matches §5.2's own citation exactly: wrap `inputs` in the
already-existing `_wire()` before `json.dumps` at the write site
(`_add_example_row`), add a new `_unwire()` inverse, apply it at all 13
`inputs_json` reader call sites named in the PREREG. Built (uncommitted
in the original agent's worktree, per an OOM-interruption note), then
independently completed, measured, and merged by the orchestrator as
`5bca8b2` / `2b1661c`
(`PROGRAM_SYNTHESIS_STRUCTURAL_CEILING_RUNG2_RUNG3_RESULTS.md:1-90`):
**exact set diff, before 54 → after 56, newly passing `{106, 115}`,
regressed `[]`** — task 106 is the PREREG's own named witness
(§5.2: "converting task 106 (live witness: 670 candidates/solved vs.
16,603/budget-exhausted, already measured)"), confirmed converted.

### 2.2 Checked directly, not assumed: did the later wire-boundary-systemic-audit undo this?

The orchestrator's own suspicion (stated in the brief) was correct to
raise but turns out **not** to hold. `git log --oneline --graph main`
shows `0c119f1` ("Merge wire-boundary-systemic-audit: retire hand-rolled
`_wire`/`_unwire` for the engine's own codec") lands after `5bca8b2` and
before `1d7d437`. Reading `WIRE_BOUNDARY_SYSTEMIC_AUDIT_RESULTS.md` in
full, its own stated scope (§1's ten-site table) is explicit that site #1
(`prog_synthesis.py::_wire`/`_unwire`) was **not deleted** but
**delegated**: *"Delegate to `substrate_rs.encode`/`decode`"* — the
function names, call sites, and tag vocabulary are kept byte-identical
(the doc's own words: *"The function NAME and call sites are kept
byte-unchanged … the tag vocabulary emitted is IDENTICAL to the
hand-rolled version's … so every already-stored `inputs_json` string
decodes unchanged"*).

Confirmed by reading current `main` source directly
(`domains/prog_synthesis.py`, current `main`):

- Line 592, the write site, is still `"inputs_json": json.dumps(_wire(inputs), sort_keys=True)` — unchanged.
- Every one of the 13+ read sites (lines 849, 1088, 1306, 1493, 1850,
  1999, 2064, 2139, 2293, 2323, 2354, 2489, 2565) is still
  `_unwire(json.loads(...))` — unchanged.
- `_wire`/`_unwire` themselves (lines 877-933) now read `return
  srs.encode(v)` / `return srs.decode(v)` respectively — the hand-rolled
  tag-matching body was replaced by a one-line delegation to
  `substrate_rs.encode`/`decode` (a **strict superset**: it additionally
  covers `Rational`/`Node`/`Surface`, which the hand-rolled version could
  never represent), but the INPUT-SIDE WIRING ITSELF — the thing Rung 2
  specifically built (calling `_wire` at the write site, `_unwire` at
  every read site) — is exactly as Rung 2 left it.

This matches the orchestrator's own hypothesis about the audit's
scope: its stated target was the *implementation gaps* (frozenset /
Fraction / non-string-dict-key coverage across `_wire`'s own hand-rolled
tag matcher and its `_plain`/`prog_moves.py` siblings), found and fixed
across three separate PRIOR rungs before this audit — **not** the
task-106 input-side flattening bug, which was already closed by Rung 2's
own separate fix. The audit's own regression battery
(`WIRE_BOUNDARY_SYSTEMIC_AUDIT_RESULTS.md` §5) shows the MBPP full arm
held at **69/257 exactly**, `det_identical=True`, before and after —
i.e. whatever set of passes existed going into the audit (which by then
already included 106 and 115 from Rung 2, plus everything from the
SetLit/DictItems/GroupCount/DictMerge rungs in between) survived it
unchanged.

**Re-confirmed live against the CURRENT `results/mbpp_endgame.json`**
(working-tree artifact, `measured_at: 2026-08-15T23:06:50+1000` — i.e.
essentially current, one hour before the PREREG's own commit timestamp):
task 106 is present in `runnable_rows` for all three arms
(`full`/`content_stripped`/`official`) with `status: accepted`,
`outcome: pass`, in every arm. **Task 106 is solved, currently, on
`main`, and has been continuously since Rung 2's own merge.**

**Verdict on §5.2's first item: (b), built as this PREREG's own
fulfilling commit, and confirmed NOT superseded by the later
wire-boundary audit — the audit's fix and Rung 2's fix operate on two
different halves of the same function (internal tag-matching
implementation vs. call-site wiring) and are complementary, not
conflicting.** No further action needed.

### 2.3 The second, deliberately-unbundled item: `persist::decode_value`'s bare-array question

**Already decided — before this PREREG existed — and unchanged since.**
The PREREG's own §5.2 text says `VALUELAYER.md` "itself declines to make
[this decision] unilaterally, and this document does not resolve it
either." Reading `PROGRAM_SYNTHESIS_ARC6_VALUELAYER.md` §9.2 directly
(`:587-598`) shows this undersells what that document actually did: it
did not leave the question fully open, it made a **deliberate, reasoned,
default choice** and named the alternative as a possible *future* rung,
not a currently-blocking decision:

> `persist::decode_value(J::Array)` was deliberately left meaning
> `Tuple`, so that every seed-resident `Lit` array literal (68 of them,
> all feeding `In`/`Append`/`Let`/`IfThenElse`, none compared with `Eq`)
> is byte-unchanged. … A later rung may decide a bare array should mean
> `list` … that is a seed-semantics change and belongs in its own
> measurement.

Checked directly against current `main` source
(`runners/dsl/src/persist.rs:159-168`) — the exact comment and behaviour
VALUELAYER.md describes is still present, verbatim:

```rust
J::Array(items) => {
    // A bare JSON array decodes as a Tuple — matches the Python
    // `decode` fallthrough for plain lists. Tagged tuples /
    // sets come through Object below.
    ...
    Value::Tuple(Arc::new(out))
}
```

`git log --oneline -L 158,168:runners/dsl/src/persist.rs` returns exactly
**one** commit for these lines: `26ca9ff`, "Initial import of ocelot
project." **This convention has never been touched in this codebase's
recorded history** — it was the pre-existing behaviour VALUELAYER.md
found, reasoned about, and explicitly chose to keep, not something any
rung introduced or is obligated to revisit.

The wire-boundary-systemic-audit (§2.2 above) independently re-confirms
and *relies on* this same unchanged convention — its own §2 calls it
"`persist.rs`'s own documented, deliberate convention," and its §4 uses
the bare-array-means-Tuple behaviour to correctly diagnose a *different*,
unrelated test-fixture bug (a test helper that skipped `_wire` entirely).
No document since VALUELAYER.md proposes changing it; none argues the
current choice is wrong for any of the 42 named MBPP ceiling tasks.

**Verdict on §5.2's second item: already resolved.** The "decision" the
PREREG frames as outstanding is, on direct reading, a decision already
made (keep `Tuple`, for a stated and still-valid reason — 68 seed
literals would otherwise need auditing) and reaffirmed, unchanged, by
every later rung that touched this boundary. **There is no dangling
action item here** — a future rung MAY still choose to revisit it if a
specific MBPP task is found to need `list` semantics from a bare-array
`Lit`, but no such task has been named anywhere in this codebase's
research history, and this document did not find one either.

---

## 3. Rung 4 (§5.5) — align `SynthesisOperatorShape` to the sd-loop discipline

### 3.1 What has and hasn't grown, verified directly against the seed file

`git log --oneline -- seeds/program_synthesis_grounding.json` → exactly
**two** commits in this file's entire history: `26ca9ff` (initial import,
created the file with its original 2 `SynthesisOperatorShape` nodes and 2
rules) and `9365017` (the tiebreak fix, below). Reading the file on
current `main` directly: still exactly **2** `SynthesisOperatorShape`
nodes (`thresholded_greater_branch`, `thresholded_lower_branch`, byte-
identical `trigger_tokens`/`minimum_trigger_matches`/`ops` structure to
what the PREREG measured), and still exactly **2** rules
(`ps_ground_held_quantity_lexeme`, `ps_select_synthesis_operator_shape`)
— no third shape, no mint/grow rule, anywhere. This directly answers the
task's framing question: **the population has NOT grown past the 2
hand-authored shapes the PREREG measured.**

### 3.2 What DID happen: the tiebreak half of item 1, fixed, and explicitly scoped against this PREREG

Commit `9365017` ("SynthesisOperatorShape: delete the Argmax tiebreak
(Pattern-D bug)", part of `BUGFIX_SWEEP2_RESULTS.md`, merged to `main` as
`2e954b6`) fixes exactly the defect §1.3/§4.2 of the reassessment PREREG
names: two shapes sharing 6 of their trigger tokens
(`THAN`/`TIMES`/`THRESHOLD`/`WHEN`/`OTHERWISE`/`ELSE`) could both clear
`minimum_trigger_matches: 5` on a message with **zero** directional
evidence, and the old `Argmax` silently resolved the tie by graph
iteration order (deterministically `thresholded_greater_branch`/`Gt`,
every time). `BUGFIX_SWEEP2_RESULTS.md` (`:52-56`) cites the reassessment
PREREG **by name and section**:

> the same class of defect `META_SHAPE_FIRST_CLASS_RESULTS.md` fixed for
> `recognise_meta_shape` … independently confirmed as a real, if
> secondary, alignment target by `PROGRAM_SYNTHESIS_STRUCTURAL_CEILING_
> REASSESSMENT_PREREG.md §1.3/§5.5` ("Rung 4 … optional").

The fix: swap `Argmax` for the existing `ArgminUnique` Term over the
negated match count — a genuine tie now returns `null` instead of an
arbitrary pick, and the existing `if graph_ops:` fallback in
`prog_synthesis.py` treats a `null` `ps_enum_ops` as "no shape selected,
use `DEFAULT_OPS`" — exactly the safety net the reassessment PREREG names
as already in place (§5.5 item 3's own "explicitly out of scope" framing,
and §4.2's fallback description). Verified live before/after in that
document: the two unambiguous cases (real greater/less cues) are
byte-identical; only the genuinely ambiguous case changes, from a silent
wrong pick to an honest refusal. Regression: named 9-file suite 3
failed/241 passed, identical to the historical baseline; no MBPP task's
live outcome changed (none was expected to — the PREREG's own §4.3 says
no MBPP task fails for this reason today).

**This is real, and it is a partial but honest fulfilment of §5.5 item
1's "delete the implicit tie behaviour" clause** — the exact clause
`META_SHAPE_FIRST_CLASS_RESULTS.md` established as the load-bearing move
for meta-shape ("a recognizer that always answers can never produce a
residual"). `BUGFIX_SWEEP2_RESULTS.md` §6 item 4 (`:361-368`) says this
explicitly, in its own words, rather than overclaiming completeness:

> Whether `ArgminUnique`'s tie-refusal behavior (item 1) is the RIGHT
> long-term shape for operator-shape selection generally, versus a fuller
> `Covers`/`AntiUnifyWitness`-based structural match — this fix deletes
> the specific unprincipled tiebreak, exactly the brief's narrow mandate;
> it does not redesign the two-shape selector into a growable codebook
> (`PROGRAM_SYNTHESIS_STRUCTURAL_CEILING_REASSESSMENT_PREREG.md §5.5`'s
> own "Rung 4" full recognize/mint proposal remains unbuilt).

### 3.3 What remains genuinely unbuilt, and why this document does not build it

Two pieces of §5.5 are confirmed, by direct source read (§3.1 above), to
be completely untouched:

1. **The structural-match half of item 1** — `ps_select_synthesis_
   operator_shape`'s scoring is still a raw trigger-token `Count`
   (now negated and passed through `ArgminUnique` instead of `Argmax`,
   but the SCORING FUNCTION ITSELF is unchanged in kind — still "count
   how many of this shape's tokens appear in the message," not a
   `Covers`/`AntiUnifyWitness`-shaped structural match over parsed shape
   facts). The tiebreak was deleted; the underlying Pattern-A/D scoring
   shape §1.3 of the PREREG names was not replaced.
2. **Item 2, "Grow," entirely** — there is no rule anywhere in
   `seeds/program_synthesis_grounding.json` (confirmed: exactly 2 rules,
   neither named anything like mint/grow/residual) that mints a new
   `SynthesisOperatorShape` when no existing shape scores above
   threshold. A task whose search finds something despite no shape
   match still just falls through to `DEFAULT_OPS`/typed defaults
   (`prog_synthesis.py`'s `if graph_ops:` guard) — safe, per the
   PREREG's own §4.3 finding, but not growth.

**This document does not build either.** The reassessment PREREG's own
§5.5 closing paragraph states the precondition for taking this rung at
all:

> This rung is explicitly separable from and not a prerequisite for
> Rungs 1-3. It should be built, if at all, **after Rung 1 has shipped a
> few more operator-shapes to season the classifier's real drift, not
> before** — sizing a fix from a 2-entry table would repeat
> `SHAPE_AUDIT.md`'s own named mistake ("a shape matcher built before
> there is a shape to match").

Rung 1 shipped (10 new Term variants), and substantial further Term work
has landed since (`Sort`, `DictItems`, `SortBy`, `GroupCount`,
`DictMerge`, `Call`, and more, per the git log walked for the Rung 3
reconciliation) — but **none of it added a new `SynthesisOperatorShape`
to the seed**. The population is still 2, exactly as it was when the
PREREG measured it. The PREREG's own stated precondition for building the
structural-match/mint machinery — "season the classifier" with more
shapes first — has therefore **not been met**, by the PREREG's own
criterion, not by this document's independent judgment. Building a
`Covers`/`AntiUnifyWitness`-based recognizer or an `sd_mint_quantum`-style
grow rule against a 2-entry population now would be sizing a fix the same
way `SHAPE_AUDIT.md` warned against — before there is a second data point
to generalize from.

**Verdict on Rung 4: (b) for the tiebreak half of item 1 (built, as a
scoped, explicitly-cited partial fulfilment of this PREREG, under the
`BUGFIX_SWEEP2` banner rather than a dedicated Rung-4 worktree, but
citing the PREREG by name and section) — and (d), genuinely unbuilt, for
the structural-match half of item 1 and all of item 2, with the added
finding that the PREREG's own stated precondition for building either has
not yet been satisfied.** This is named precisely, for the orchestrator
to act on or defer, rather than built speculatively against a population
too small to size confidently — the same judgment call §4.3 of the
PREREG itself already made once.

---

## 4. What this document does NOT establish

1. **No code, seed JSON, or tests were written.** This is investigation
   and reconciliation only, following the Rung 3 document's own template
   and method (`git log` for provenance, direct source reads for current
   state, no trust in any prior document's self-report without
   cross-checking it against code).
2. **No battery was re-run by this task.** Every MBPP number cited (49,
   54, 56, 69/68/98) is read from already-committed RESULTS documents or
   the current working-tree `results/mbpp_endgame.json` artifact, cross-
   checked for internal consistency (e.g. task 106's presence was
   independently re-verified against the live artifact, not just quoted
   from a prior doc) but not independently re-measured from a fresh
   battery run.
3. **Task 115's individual attribution** (the "bonus" gain Rung 2's own
   RESULTS doc names but does not isolate) is not re-investigated here —
   it was already named as unattributed in `PROGRAM_SYNTHESIS_
   STRUCTURAL_CEILING_RUNG2_RUNG3_RESULTS.md`'s own "what this does not
   establish," and this document adds nothing new about it.
4. **Whether any MBPP task specifically needs `decode_value`'s bare-array
   convention to mean `list`** was not exhaustively re-checked against
   all 257 test-split tasks or the 68 seed `Lit` array literals
   individually — this document confirms the convention is *unchanged
   and was a deliberate choice*, not that it is *provably optimal* for
   every current or future task.
5. **Whether `BUGFIX_SWEEP2`'s other two items** (task 242 retrieval-
   ceiling re-pin; the three `SHAPE_AUDIT_SWEEP2` deferred items) bear on
   program synthesis further is out of this document's scope — only the
   one item overlapping Rung 4 (`SynthesisOperatorShape`) was read in
   full; the rest of that document was read only enough to establish
   provenance and scope for item 1.
6. **A structural-match/mint design for Rung 4's remainder is not
   sketched here** — this document establishes that the precondition for
   building it has not been met and names precisely what is missing
   (§3.3), but does not attempt the design itself; that is future work,
   correctly gated on more operator-shapes existing to season it against,
   per the PREREG's own reasoning.

---

## 5. Summary table

| rung | PREREG ask | current state | verdict | action needed |
|---|---|---|---|---|
| 1 (§5.1) | 10 Tier-1 `TermNode` ports | built, merged (`5b8c2c7`/`fecd35e`), MBPP 49→54, +5/0 regressed, 774/774 Rust | (b) built as this PREREG's fulfilment | none |
| 2a (§5.2, `_wire` on `inputs_json`) | symmetric input-side wire fix, convert task 106 | built (`5bca8b2`/`2b1661c`), MBPP 54→56, {106,115}; internals later delegated to `substrate_rs.encode`/`decode` (`0c119f1`) but call-site wiring unchanged; task 106 confirmed passing in current `results/mbpp_endgame.json` | (b) built as this PREREG's fulfilment, unaffected by the later audit | none |
| 2b (§5.2, `decode_value` bare-array) | named as an open seed-semantics decision | decided in `VALUELAYER.md` §9.2 itself (keep `Tuple`, deliberately, for 68 seed literals), unchanged since initial import (`26ca9ff`), reaffirmed by the wire-boundary audit | already resolved before the PREREG was drafted | none (revisit only if a specific task is found needing `list` semantics — none named anywhere) |
| 4a (§5.5 item 1, tiebreak) | delete the implicit tie behaviour | built, merged (`9365017`/`2e954b6`), explicitly cites this PREREG, regression-clean | (b), partial fulfilment | none |
| 4b (§5.5 item 1, structural match) | replace raw trigger-token count with `Covers`/`AntiUnifyWitness` match | untouched — scoring is still `Count` (now via `ArgminUnique`/`Neg`, same shape) | (d) unbuilt | defer — precondition (seasoned population) unmet |
| 4c (§5.5 item 2, Grow) | mint a new operator-shape from an unmatched residual | untouched — 2 rules total in the seed, neither a mint rule | (d) unbuilt | defer — precondition (seasoned population) unmet |

**Net effect on the reassessment PREREG as a planning document**: three of
its four rungs (1, 2a, 2b) are fully resolved and require no further
action; the fourth (4) is honestly half-done, with the unbuilt half
correctly gated by the PREREG's own stated precondition rather than
either abandoned or force-built. No code follow-up is required for Rungs
1 or 2. Rung 4's remainder should stay named-not-built until a
subsequent rung adds at least one more hand-authored `SynthesisOperatorShape`
to season the classifier — exactly as the PREREG itself specified.
