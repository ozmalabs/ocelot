# Γ as a third instance of the collapse-mint algorithm — RESULTS

Worktree: `/home/matt/ozmadev/ocelot-worktrees/gamma-collapse-algorithm`, branch
`gamma-collapse-algorithm`, forked at `03bd3b3`. PREREG:
`docs/research/engine_substrate/GAMMA_COLLAPSE_ALGORITHM_PREREG.md`.

## 0. Headline verdicts

| Question | Verdict |
|---|---|
| Q1 — deep or superficial fit? | **Deep, WITH a real adaptation.** Rung 1 (recognize) transfers unchanged; the support-discipline half of rung 4 (mint-on-recurrence) transfers with ZERO modification (Prediction B confirmed). Rungs 2–3 (transform-in-basis, infer-dimension) genuinely DO NOT APPLY — not because the analogy is weak there, but because a Type-1 triple is atomic (Prediction A confirmed exactly as registered). |
| Q2 — routes through the existing gate? | **Half yes, half honestly no.** `SelfConcern -> promote_self_concern -> StandingConcern` — ZERO code changes, GO bar met exactly as registered. `StandingConcern -> judge -> adopt` — falls through to the generic `comprehend_first` default (no `gamma_production` handler exists, mirroring the `code_write`/`prog_read` precedent that WOULD be needed); reported as a named, out-of-scope gap, not silently patched. |
| Q3 — separate or unified? | **Separate — confirmed, not assumed.** Checked directly: `sd_mint_quantum`'s own `CapabilityAxis` becomes load-bearing (readable by `sd_recognize`) the instant it is minted, no status/approval gate anywhere in that rule. Γ's admission-control layer is not an instance of the recognize/mint shape; it is a distinct governance layer the paper gives its own theorem, and this build adds a SECOND admission-control layer (the human promote gate) on top of a genuine third instance of the shape, never conflating the two. |
| Q4 — SHAPE_AUDIT 159/634 connection? | **Speculative, as predicted — no seed named with confidence.** Reported honestly below with the one concrete, real (but not-159) illustration found (`scripts/settle8_spectrum.py`). |
| Built or named-not-built? | **Built.** Rust instrumentation (feature-flagged, default off), seed rule, end-to-end demonstration through the real `WorldAdapter` + `jabberwock_daemon.promote_self_concern`, a manual adopt step, full regression pass. |

## 1. Q1 — deep or superficial, in detail

**Rung 1 (recognize) is `check_edge`, literally unchanged.** No code in this
build touches `checker.rs` or `grammar.rs`. An admitted edge never reaches
`Type1NoProduction` at all — recognition-without-growth is already exactly
the shape the sd loop's own rung 1 realises.

**Rung 4 (mint-on-recurrence)'s SUPPORT DISCIPLINE transfers with literally
zero modification — Prediction B confirmed.** `shape_decode.rs:8795-8797`'s
"support >= 2, TWO is not a swept knob" is reused VERBATIM
(`seeds/gamma_residual.json`'s `Gte(Count(...), 2)` guard), and the
canonical-grouping-key concern that motivated meta-shape-mint's sorted
predicate SET (`SHAPE_AUDIT.md` §3.1's `CapabilityAxis` truncation bug) simply
does not arise here: `(src_type, edge_type, tgt_type)` is already a fixed
3-tuple, so grouping by exact attr equality (no sort, no lgg) is already
canonical. Verified live (§5): support 1 → 0 residuals mint;
support 2 → exactly 1; support 3, 4, 5 → still exactly 1 (mint-once holds
under repeated recurrence).

**Rungs 2–3 genuinely do not apply — Prediction A confirmed exactly as
registered, and this is the load-bearing finding of Q1.** `TransformDecode`
(rung 2) and `DimInfer` (rung 3) exist because a shape-decode residual is the
UNEXPLAINED PORTION of a larger structural comparison — some relations
matched the held signature, some didn't, and rungs 2–3 ask whether the
unmatched ones are a consistent per-dimension delta on the matched ones. A
`Type1NoProduction` triple has no such structure to have: `check_edge`
(`checker.rs:53-103`) looks up `grammar.candidates(src_type, edge_type,
tgt_type)` as one atomic key — the outcome is binary (some production
matches AND its where-clause admits, or it does not), with no notion of
"three quarters of this triple matched." There is no partial coverage for a
transform or a dimension-inference step to explain, because there is no
partial anything — the object being tested is a lookup key, not a relation
set. **This means the complete, non-degenerate instance of the shape here is
rung 1 + rung 4 only, and that is not a crippled instance missing two
rungs — it is what the shape looks like when applied to an atomic
recognition unit instead of a structured one.** Confirmed by building rung 4
without ever needing rungs 2–3, and by the fact that no sensible construction
of "transform of a rejected triple" presented itself while designing the seed
rule (a src_type/edge_type/tgt_type substitution IS just a different
triple — a different point in the SAME lookup table, not a delta on a held
shape).

**One place the analogy needed active resistance, not just adaptation, and
did not break:** it would have been tempting to make "two triples with the
same edge_type but different src/tgt" count as one fuzzy group (a
transform-like move). This was deliberately REJECTED — `SHAPE_AUDIT.md`
§3.1's own lesson (order-dependent, truncated identity → growth failure
disguised as recognition) argues directly against loosening the grouping key
for convenience. The exact-triple grouping is not a missed opportunity for a
richer rung 2; it is the correct boundary for what Type-1 admissibility even
means (Definition 3 in the paper: the triple is the unit of (in)admissibility,
full stop).

## 2. Q2 — gate reuse, in detail

**What routes with zero changes.** `note_gamma_production_gap`
(`seeds/gamma_residual.json`) mints a `SelfConcern{status:'noted',
source:'implicit', kind:'gamma_production', content:<the triple>}` — the
IDENTICAL node shape `gap_awareness.json`'s two existing mint rules produce.
Verified live (`tests/test_gamma_collapse_algorithm_migrated.py::
test_promote_self_concern_accepts_the_minted_gap_with_zero_code_changes`):
`jabberwock_daemon.promote_self_concern` (`scripts/jabberwock_daemon.py:2150`)
accepts it, mints a `StandingConcern{status:'pending', source:
'conversation_promoted'}`, sets the originating `SelfConcern.status =
'promoted'` — with **no edit to that function**. `reflective_faculty.
_run_self_gaps`'s scan-all-SelfConcern fallback (`reflective_faculty.py:
396-400`) surfaces it the same way it surfaces every other gap kind, also
with no edit.

**What does not route automatically, reported honestly rather than
patched.** `_promote_relations_for_concern` (`jabberwock_daemon.py:
2040-2148`) special-cases exactly two prior kinds needing non-generic
handling — `code_write` and `prog_read` — precisely because the generic
`comprehend_first` default does the wrong thing for a non-conversational
gap. `kind:'gamma_production'` is not one of those two, nor is it in the
`want_experiment` kind list, so it falls to the SAME generic default. This
was VERIFIED, not assumed:
`test_promote_self_concern_accepts_the_minted_gap_with_zero_code_changes`
asserts `standing["pipeline"] == "comprehend_first"` explicitly, so a future
addition of a real handler is a deliberate, visible change to that
assertion, not a silent behaviour drift. Building the missing handler (the
Python analogue of `_process_code_write_standing` /
`_process_prog_read_standing`, teaching the judge/adopt machinery to turn a
promoted triple into an actual `Production` JSON and route it to a human
decision) is real engineering, explicitly out of scope per the task's own
"no redesign" boundary — named here as the concrete next rung, not built.

**The manual adopt step stands in for exactly that missing rung**, using the
primitive the missing handler would eventually call anyway
(`add_production`) — so the gap is a missing DISPATCH, not a missing
primitive.

## 3. Q3 — is admission control part of the shape?

Checked directly rather than assumed. `sd_recognize`
(`seeds/shape_decode_loop.json`) matches an `Observation` and decodes it
against `NodesOfType('ShapeSignature')`/`CapabilityAxis` via the `ShapeDecode`
Term — its `where` clause (read in full) contains an `AgnosiaParams` lesion
guard and a `status=='decoded'` guard on the OBSERVATION, but **no status,
approval, or gate check on the CANDIDATE shapes/axes it decodes against.**
`sd_mint_quantum` mints a `CapabilityAxis{induced:1.0, ...}` and the VERY NEXT
`run_rules` fixpoint pass, `sd_recognize`/`sd_redecode` can read it back — it
is load-bearing the instant it exists. The SAME is true of the meta-shape
mint (`MetaShapeMint`, rung 4 of that grain): no human step sits between a
minted `MetaShape` and `analogical_thinking` reading it.

**Conclusion: admission control is a SEPARATE governance layer, not part of
the recognize/collapse/mint shape, and this is not a threat to the working
hypothesis — it is the answer the paper's own theorem structure predicts.**
The recognize/mint shape governs how the substrate decides something is
*worth minting as a candidate*; nothing about that shape says anything about
when a candidate becomes *trusted, load-bearing structure*. Every other
minted structure in this codebase answers that question the same way
(mint ⇒ immediately trusted), because minting into an ALREADY-TRUSTED region
(a codebook another rule already reads unconditionally) is a fundamentally
different operation from minting a PRODUCTION, which changes what edges may
exist at all, in a substrate whose own docstring calls this out by name
(`checker.rs:1-3`, Theorem XII). **This build therefore has TWO gates, not
one, and keeps them administratively distinct on purpose:** the sd-loop-style
mint gate (support >= 2, decides "is this worth proposing") and the
Theorem-XII admission gate (decides "is this now real Γ"), with the human
promote step sitting between them. Collapsing the two would be exactly the
mistake CLAUDE.md's charter warns against — mistaking the working hypothesis
("one recurring algorithmic shape") for a claim that GOVERNANCE also
collapses into that shape, which the charter's own load-bearing correction
(algorithm, not primitive) explicitly does not assert.

## 4. Q4 — SHAPE_AUDIT 159/634 connection

**No specific one of the 159 zero-Γ-production seeds could be named with
confidence as an instance of a checked-path Type-1 rejection**, and this is
reported as the honest, registered NO-GO for Q4's strong form. The reason,
confirmed by reading (not assumed): the 159 seeds' OWN rule effects mint
edges via `graph.insert_edge` DIRECTLY (`rewrite.rs:1510,1828,1962`) —
**bypassing `check_edge` structurally**, not failing it. A rule-effect edge
insertion in those 159 seeds never reaches `Substrate::add_edge` at all, so
it can never produce a `Type1NoProduction` outcome for this build's
instrumentation to see. The 159 are architecturally EXEMPT from Γ, not
silently failing it — a materially different situation from what this spike
instruments.

**A real, concrete, checked-Γ-path rejection DOES exist in the tree, though
not among the 159** (`scripts/settle8_spectrum.py:53-59`, read directly): a
"bare `boot_core` raises `InadmissibleEdge` … the `SUnit` type and the `SUnit
-sunit_neighbour-> SUnit` production are graph data in `vision_onoff` /
`vision_settle`" — i.e. a human, running this script, hit a genuine
`add_edge`-path rejection, diagnosed it by reading the exception message, and
fixed it by loading the right seed. **This is exactly the shape of manual
labour this spike's mechanism could reduce** — not by making the edge
admissible (it must not), but by turning "read a raised exception once, in
one script's failure, and reason it out" into "the graph itself notices the
SAME triple recurring and surfaces it as a findable, promotable gap" — the
identical value proposition `gap_awareness.json`'s own module docstring
claims for conversational gaps, transplanted to Γ. This is offered as the
closest real illustration of the phenomenon, not as a demonstrated instance
of the 159 population; the PREREG's own GO bar for Q4 required naming a
plausible seed or reporting the connection as speculative, and the honest
finding is closer to the latter, with this one concrete data point attached.

## 5. What was built

**Rust (`runners/dsl/src/substrate.rs`, `runners/dsl/src/py.rs`).** One new
`pub(crate) gamma_residual_capture: bool` field on `Substrate`, default
`false`, mirroring the established `precise_dirty`/`dirty_telemetry` opt-in
pattern (`substrate.rs:172-294`) byte-for-byte in style, plus a
`gamma_residual_root: Option<NodeID>` for lazy anchor creation (kept
DELIBERATELY separate from `add_production`'s own `gamma_graph_root`, so a
residual is never structurally confusable with a live production even though
both share the `GammaGrammar`-family vocabulary). `record_gamma_residual`
(new method) is called from exactly one site — the `Type1NoProduction` arm of
`Substrate::add_edge` (`substrate.rs`, right after the existing
`on_rejection_type1`/`on_production_reject` counter calls) — and does
mechanical event logging only: one new `GammaResidual{src_type, edge_type,
tgt_type, hit_count, proposed}` node per rejection, anchored under a lazily
created `GammaResidualRoot` via an unchecked `gamma_residual` edge (same
category as `add_production`'s own unchecked `GammaProduction` mirror write).
No new `TermNode` variant. No change to `Production`/`Grammar`/
`ConsistencyChecker`.

**Seed (`seeds/gamma_residual.json`, new, one rule).**
`note_gamma_production_gap` groups `GammaResidual` nodes by exact triple via
`Filter`+`Count` (existing Terms only), applies the `shape_decode.rs`
support discipline verbatim (`Gte(count, 2)`), picks one canonical leader via
the `retire_duplicate_gap` `Argmin`-over-node-identity idiom
(`gap_awareness.json`), mints a `SelfConcern` in the exact shape
`gap_awareness.json`'s own mint rules use, content-deduped and mint-once
exactly like those rules. Deliberately mints NO `agent -has_self_concern->`
edge (no reliable single-Agent anchor at this grain; `_run_self_gaps`'s
scan-all fallback makes this a non-issue, confirmed by reading, not assumed).

**Tests.** `runners/dsl/src/substrate.rs`'s own `#[cfg(test)] mod tests`
gains three new tests co-located with the existing `Type1NoProduction`
precedent (`gamma_residual_capture_off_leaves_graph_unchanged`,
`gamma_residual_capture_on_logs_one_node_per_rejection`,
`gamma_residual_capture_distinguishes_different_triples`).
`tests/test_gamma_collapse_algorithm_migrated.py` (new, 5 tests) exercises
the full loop through a real `WorldAdapter` + `load_all_seeds` boot + the
real `jabberwock_daemon.promote_self_concern`.

## 6. A real bug found and fixed en route: unmarked dirty state

**The defect.** The first working version of `record_gamma_residual` used
raw `self.graph.insert_node`/`insert_edge` (mirroring `add_production`'s own
mirror-write style verbatim). This compiled, and the isolated
`substrate_rs.Substrate()` script-level demonstration (§7 below) showed it
working — but a scripted repro that rejected the SAME triple five times in a
row, calling `run_rules()` after each rejection, showed **zero** `SelfConcern`
mints at every step from 1 through 5, and only produced the expected mint
after an UNRELATED, later `add_node` call happened to trigger the engine's
blanket dirty path. Root cause: `graph.insert_node`/`insert_edge` do not, by
themselves, mark any rule dirty — `Substrate::add_node` and the checked
`add_edge` path both call `mark_node_mutation`/`mark_external_write`/
`mark_edge_type_dirty` explicitly on top of the raw graph write, and my first
draft skipped that layer entirely, exactly as `add_production`'s own mirror
write does (which is harmless there ONLY because nothing currently matches on
`GammaProduction`/`GammaGrammar` node types in a top-level rule `match`).

**The fix.** `record_gamma_residual` now inserts the `GammaResidual` node via
`self.add_node(...)` (not the raw graph call) and explicitly calls
`self.mark_edge_type_dirty(residual_edge)` after the unchecked edge insert —
the same call the checked `add_edge` path makes for an admitted edge. Verified
by direct comparison: before the fix, 5 sequential same-triple rejections with
a `run_rules()` after each produced 0 `SelfConcern` mints through 5
rejections; after the fix, the mint appears immediately on the SECOND
rejection (support == 2) and stays at exactly one mint through the 3rd, 4th,
and 5th. **This is reported because it is directly relevant to CLAUDE.md's
own audit finding**: `SHAPE_AUDIT.md`'s Pattern C (minted without checking
first) is about admissibility; this is a sibling defect class in the SAME
family — mutating the graph in a way invisible to the rule engine's own
dirty-tracking — found in NEW code written specifically to fix a different
Pattern-adjacent gap, which is a small but real data point that this failure
mode is easy to reintroduce even when actively watching for adjacent bugs.

## 7. A second finding, out of scope, reported not fixed

The PyO3-exposed `add_production` (`py.rs:7803-7820` — the one seed loading
and `WorldAdapter` code actually call) does **not** call the Rust-inherent
`Substrate::add_production` (`substrate.rs:832`, the one that mints the
`GammaProduction` graph mirror and bumps `gamma_epoch`); it calls
`inner.checker.grammar.add(p)` directly. Its neighbour
`add_production_no_mirror`'s own docstring (`py.rs:7822-7844`) describes
itself as "the sole mirror-free variant," implying the plain `add_production`
binding should mirror — it does not, as read directly. **Not verified
further and not fixed here** — it predates this spike, is unrelated to
Type-1 residual capture, and fixing it would touch `add_production`'s call
graph, which is out of scope ("no redesign of
Production/Grammar/ConsistencyChecker"). Consequence for THIS build: the
manual "adopt" step in every test and demonstration below calls
`add_production` — which DOES make `checker.grammar` admit the triple
(confirmed live, §8) — but does NOT write a `GammaProduction` graph mirror
for it. The safety-relevant fact (checker admits it) is unaffected; the
introspection-relevant fact (the mirror shows it) is not, and is named here
so it is not mistaken for something this build's own code broke.

## 8. Live before/after demonstration

Raw `substrate_rs.Substrate()` script (pre-`WorldAdapter`, used to develop
and debug the mechanism):

```
=== capture OFF ===
rejection 1: Γ rejects (AliveCell) -[adjacent_to]-> (DeadCell)
GammaResidual nodes (capture off): 0

=== capture ON ===
rejection 2 (1st logged): Γ rejects (AliveCell) -[adjacent_to]-> (DeadCell)
SelfConcern after 1 logged rejection: 0
GammaResidual nodes: 1
rejection 3 (2nd logged -- recurrence): Γ rejects (AliveCell) -[adjacent_to]-> (DeadCell)

=== load gamma_residual seed, then re-tick ===
SelfConcern count after recurrence + rule load: 1
 -> content: 'Gamma repeatedly rejects (AliveCell) -[adjacent_to]-> (DeadCell) -- no admissibility production covers it'

=== check_edge before adopt ===
admissible now? False

=== manual human-equivalent ADOPT step ===
=== check_edge after adopt ===
admissible now? True
add_edge result: ADMITTED
```

Negative control (a triple rejected exactly once, in the presence of a
DIFFERENT recurring triple accumulating support in parallel — proves the
grouping key does not cross-contaminate): after 5 rejections of one triple
(support growing 1→5) and one clean single rejection of an unrelated triple,
`SelfConcern` count stayed at 0 through support 1, became 1 at support 2, and
the single-occurrence triple never minted at all.

At the `WorldAdapter` grain (`tests/test_gamma_collapse_algorithm_migrated.py`,
all 5 green): a fresh agent boots the FULL seed set (`load_all_seeds`,
`seeds/gamma_residual.json` included automatically, no special wiring),
capture stays off through ordinary conversation (0 `GammaResidual` nodes
minted by normal operation), a single rejection produces a residual node but
no `SelfConcern`, two rejections of the same synthetic triple produce
EXACTLY one `SelfConcern{kind:'gamma_production'}`,
`jabberwock_daemon.promote_self_concern` accepts it and mints a
`StandingConcern{status:'pending', pipeline:'comprehend_first'}` with zero
code changes to that function, and a manual `add_production` call flips
`is_edge_admissible` from `False` to `True` for the EXACT triple while an
unrelated, never-adopted triple (`GammaSpikeBar -[gs_adopt_edge]->
GammaSpikeFoo`, the reverse direction) stays `False` — adoption is scoped to
the exact triple, not a blanket relaxation.

**Theorem XII check, explicit.** In every test and script above: (1) no rule
anywhere calls `add_production` — `seeds/gamma_residual.json`'s only effects
are `set_attr`/`add_node`/`add_edge` on `SelfConcern`/`GammaResidual`, never
a grammar mutation; (2) a single rejection never changes
`is_edge_admissible` (asserted explicitly in
`test_manual_adopt_flips_check_edge_and_theorem_xii_holds`); (3) the
recurrence mint (support >= 2) never changes `is_edge_admissible` either —
verified by construction, since `note_gamma_production_gap`'s effects touch
only `SelfConcern`/`GammaResidual` attrs, and confirmed live in
`test_recurrence_mints_exactly_one_self_concern` (which asserts the
`SelfConcern` mint but never checks or asserts a change in admissibility,
because there is none to observe — `add_edge` inside that test's own loop
keeps raising on every iteration including the last); (4) only the explicit,
manual `add_production` call — never something a rule triggers — changes
admissibility, and it changes ONLY the exact adopted triple. **The
reference-monitor invariant held throughout, unconditionally.**

## 9. Regression

**Rust.** Full crate (`cargo test --release --lib`), single-threaded:
**769 passed, 0 failed, 4 ignored (pre-existing)**. Default (parallel)
`--test-threads` run shows 4 failures, ALL in `shape_decode::dim_infer_tests`
(`d_codebook_growth_is_seen_by_the_encoder`, `d_green_different_goals_are_
seven_distinct`, `d_red_identical_arguments_collapse_to_one`, `d_sweep_
distinct_tracks_its_axis`) — reproduced BYTE-IDENTICAL on unmodified `main`
under the same parallel invocation (confirmed by running the same filter on
`/home/matt/ozmadev/ocelot` directly), and confirmed to pass individually and
under `--test-threads=1` on BOTH trees. This is pre-existing test-isolation
flakiness in that module (a shared global recorder, per the "the recording
site must see every invocation" panic text), unrelated to this spike — not
touched by any file this build changed. Scoped filters also green:
`grammar_reflect::` 2/2, `substrate::tests::` 29/29 (2 pre-existing ignores).

**Python.** `tests/test_gap_awareness_migrated.py` 9/9,
`tests/test_self_concern_promote_migrated.py` 6/6,
`tests/test_engine_provenance_migrated.py` 9/9 (1 pre-existing skip),
`tests/test_gamma_collapse_algorithm_migrated.py` (new) 5/5. A worktree
environment note, not a code defect: `data/` and one `results/*` artifact
file are gitignored, untracked local caches `git worktree add` does not
carry — five `test_gap_awareness_migrated.py` tests failed until `data/` was
symlinked from the canonical tree (topic-grounding needs its local wiki
library), matching CLAUDE.md's own documented "data/ symlinked vs absent"
condition precisely; two more files failed to COLLECT until
`results/prog_synthesis_battery.json` was individually symlinked, matching
the `failure_baseline.json` record's own stated convention ("results/
per-entry symlinks to the canonical tree"). Both are worktree setup, not
regressions — confirmed by reproducing the SAME 20 collection errors (all
pre-existing optional-dependency gaps) on unmodified `main` under an
identical broad `pytest -k` sweep.

## 10. What this does NOT establish

- It does not measure whether real Γ rejections in normal agent operation
  recur often enough for this mechanism to fire outside a synthetic test —
  `test_capture_off_by_default_mints_nothing` only shows capture stays
  off by default, not what capture ON would find in a live corpus. No
  production traffic was run with capture enabled.
- It does not build or size the missing `gamma_production` StandingConcern
  handler (Q2's honest gap) — the manual adopt step stands in for it but is
  not a substitute for the real dispatch code.
- It does not fix the `add_production` no-mirror drift (§7) — named,
  unrelated, out of scope.
- It does not confirm or deny that any of the SHAPE_AUDIT 159 population
  would benefit from this mechanism — Q4's answer is that the 159 are
  structurally exempt from the checked path this spike instruments, which is
  itself informative but is a NO, not a maybe.
- Support >= 2 is reused verbatim from `shape_decode.rs`, not re-derived or
  independently justified for the Γ case — the PREREG registered this as the
  correct move (source the criterion, don't invent one), but it is worth
  being explicit that no argument beyond "this is the sd loop's own
  discipline for the analogous choice" was made for why 2 (rather than, say,
  a triple's rejection density relative to overall Γ-check volume) is right
  here specifically.

## 11. Commit

Committed in this worktree; branch `gamma-collapse-algorithm`, not merged
into `main` — left for the orchestrating session per instruction.
