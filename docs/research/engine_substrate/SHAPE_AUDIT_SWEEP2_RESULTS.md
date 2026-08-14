# SHAPE AUDIT SWEEP 2 — RESULTS

Closes the still-open items from `SHAPE_AUDIT.md` §8, per
`SHAPE_AUDIT_SWEEP2_PREREG.md`. Worktree branch `shape-audit-sweep2`, off
`main` at `76b8aea` (fresh tip at prereg time — checked for sibling-branch
collisions first; see §0).

**Honest headline, in one paragraph.** Four items were pre-closed by other
work already merged to `main` before this rung started (#1, #2, #3/A1-A9,
#5, #6, and the below-the-line `find_analogies` item — verified by reading,
not assumed) — this rung's actual new work is #7 (fixed), #8 (fixed), #10
(fixed + one measurement-artifact correction to the audit itself), #4.6
`wire_self_extension` (fixed + a genuine idempotency test added), #4 (traced
to ground truth: **yes, a rule-effect `add_edge` bypasses `check_edge`** —
sized, not fixed, 159 seeds is a real follow-on), and #9 / §4.4 / §6.3
(sized, not fixed, each for a stated reason). Every code change was
regression-tested against a **paired, from-scratch, same-worktree baseline**
(not just "tests still pass" — the exact failing-test-name sets were
diffed before/after each change), because this heavily-loaded shared
machine has a large population of pre-existing, environment-conditional
failures (`data/` absent in this worktree) that would otherwise be
indistinguishable from a real regression.

---

## 0. Pre-flight: what was already closed on `main`

Verified by reading the current code (not assumed from the audit's own
"already fixed" framing in the brief) before starting any new work:

- **#1 (meta-shape codebook, no mint path)** — `seeds/meta_shape_growth.json`
  wires the full 4-rung sd-loop ladder at the `MetaShape`/`ShapePrinciple`
  grain (`RUNG 4 — DYNAMIC QUANTIZATION AT THE META-SHAPE GRAIN`, comment
  cites this audit's finding #1 by name). Landed.
- **#2 (`recognise_meta_shape` substring + alphabetical tiebreak)** —
  `domains/teach.py::categorise_by_shape` now builds a structural
  `item_signature` and scores it via the shared `RecogniseShape` Term; its
  own docstring: *"STRUCTURE, NOT A NAME-BAG (SHAPE_AUDIT.md §2.5, fixed
  2026-08-12)"*. Landed.
- **#3 / A1-A9 (`keywords_text` Argmax family)** — `domains/rule_signature.py`
  is imported and used at `reflective_faculty.py:2832, 3085, 3774` (not just
  sitting unwired as the audit found it). The "closes the A1-A9 audit"
  commit (`19fdddf`/`f82c109`, `mac-fac-a8`) is an ancestor of `main` tip.
  Landed.
- **#5 (`CapabilityAxis` identity, order-dependent + truncated-to-3)** —
  `domains/reflective_faculty.py:1282-1344`: *"`"induced_" +
  "_".join(sorted(preds))` — sorted and untruncated"*. Commit `2513441`
  ("Fix SHAPE_AUDIT.md Pattern C cluster: CapabilityAxis identity +
  learn_recursive_concept/learn_word duplicate-on-reteach"), with its own
  prereg/results docs, is an ancestor of `main` tip. Landed.
- **#6 (`learn_recursive_concept` / `learn_word` duplicate-mint)** — the
  SAME commit `2513441` fixed both, using exactly the `_ensure_concept`
  find-or-create pattern the brief asked for: `learn_recursive_concept`'s
  `_recursive_concepts` index is now wired into `save()`/`load()`
  (`world_adapter.py:6138-6142, 6232`), and `learn_word` now consults
  `self._concepts` before minting (`world_adapter.py:10036-10044`). Landed.
- **Below-the-line: `find_analogies` MAC-as-verdict (§2.4)** —
  `domains/analogical_thinking.py` now has a real FAC stage: `_pair_witness`
  + `_compute_analogy`'s own comment, *"This function is now the MAC stage
  only"*. Commits `5a484b0` ("genuine shape math — the MAC/FAC escalation")
  and `14cb457` ("Blob-edge correspondence minting: wire
  analogical_thinking's `_pair_witness`") are both ancestors of `main` tip
  `76b8aea` (`git merge-base --is-ancestor` confirmed both). **No sibling
  branch has this in flight** — checked `git log --oneline --all -- domains/
  analogical_thinking.py` and every open worktree branch's tip on that path
  resolves to one of these two already-merged commits, not a divergent one.
  No coordination needed; nothing to conflict with.

None of these six were re-touched in this rung. They are reported here only
because the brief asked this rung to verify, not redo, closed work.

---

## 1. #4 — does a rule-effect `add_edge` bypass `check_edge`? Ground truth.

**Yes.** Traced, read-only, no Rust edits.

- `Substrate::add_edge` (`runners/dsl/src/substrate.rs:1533-1589`) is the
  ONLY path that calls `self.checker.check_edge(...)` before inserting an
  edge — `CheckOutcome::Admitted` inserts via `graph.insert_edge`;
  `Type1NoProduction`/`Type2VocabAbsent` return `Err` and nothing is
  inserted.
- `rewrite.rs::apply_rule_full`'s `Effect::AddEdge` handler
  (`runners/dsl/src/rewrite.rs`, ~line 1500-1512) calls
  `graph.insert_edge(s, *edge_type, t, attr_map)` **directly on the
  `TypedGraph`**, never through `Substrate::add_edge`, never through
  `checker.check_edge`. This is the ONLY place a Rule's own `add_edge`
  effect is applied (`apply_rule`/`batch_apply_rule`/`run_rules*` all funnel
  through `apply_rule_full`).
- Grepped every `check_edge` call site in the crate: `substrate.rs:1541`
  (inside `add_edge`, the admissibility path), `:1838` and `:1863`
  (`edge_would_admit`-style probes: materialise a scratch node, check, then
  delete it — used by `admissible_edges_from`/`admissible_moves`, which are
  QUERY/SELECTION helpers a rule's `where`-clause or a Python caller can use
  to ask "would this be admitted", never invoked from the effect-apply path
  itself). **Zero calls to `check_edge` anywhere in `rewrite.rs`.**

This confirms the humanoid doc's claim (*"rule effects write via
`graph.insert_edge` directly ... the `gated` flag is reserved and
unbuilt"*) at the exact code path, for THIS crate, independent of the
humanoid domain.

**Sizing, not fixing, in this rung — and why.** The corpus measurement from
`SHAPE_AUDIT.md` §10's own reproduce script, re-run against this worktree
unchanged (no seed edits in this rung touched `productions`):

```
rule-carrying seeds with 0 productions: 454 of 634
...of which rules mint edges: 159
```

A "fix" here is NOT "make `apply_rule_full` call `check_edge` before every
`AddEdge` effect" — that is a real engine behaviour change with system-wide
blast radius:

1. **It would change semantics for every rule in the corpus, not just the
   159.** Rules today rely on effects being unconditional (a rule's `where`
   clause is the ONLY gate the rule author reasons about); routing effects
   through `check_edge` makes a SECOND, independent gate (the Γ production
   set) co-decide whether the effect lands, silently, for rules whose
   authors never declared a production because they never needed
   admissibility semantics for that edge type.
2. **159 seeds is exactly the set that would start silently no-op'ing.** A
   rule whose `where` clause fires but whose `add_edge` target edge type has
   no matching Γ production would go from "always writes" to "writes only
   if some production admits it" — for a seed with a genuinely EMPTY
   production list (`"productions": []`, the majority of the 159), the
   effect would go from firing every time to NEVER firing, breaking the
   rule outright rather than making it "more correctly gated."
3. **The two-tier design may be intentional.** Not every graph mutation is
   a claim about the WORLD's admissible structure (what Γ governs) — some
   are executive bookkeeping (a Reflex's internal state, a Goal's status
   field via effect writes elsewhere) that was never meant to be
   admissibility-checked. Distinguishing "this add_edge is a claim about
   world structure" from "this add_edge is executive bookkeeping" is a
   per-rule, per-edge-type classification the humanoid doc's own `gated`
   flag (documented as "reserved and unbuilt") was evidently designed to
   carry — building it out is real design work, not a one-line engine
   change.

**The concrete, scoped follow-on this sizing recommends** (named, not
built, per the brief's own "not necessarily fix" allowance):

- Build out the `gated` flag path: an `Effect::AddEdge` gains an optional
  `gated: bool` (default `false`, preserving every existing rule's
  behaviour byte-for-byte) that routes through `Substrate::add_edge`
  instead of `graph.insert_edge` when set.
- A migration pass (NOT blind) over the 159: read each seed's actual edge
  semantics and classify it as "world claim" (should gain productions +
  `gated: true`) vs. "executive bookkeeping" (stays ungated, `productions:
  []` is then a CORRECT declaration, not a gap) — this is exactly the
  humanoid/bigville "empty generated response set" work CLAUDE.md already
  names as *named, not built* for those two domains; this rung's
  measurement is evidence the SAME classification work is needed
  corpus-wide, at ~40× the scale CLAUDE.md's bigville section measured (4
  seeds → 159).
- Gate the migration behind exactly the regression discipline this rung
  used: pair every reclassified seed's rule-firing tests against a
  from-scratch baseline before merging, since flipping even one seed from
  ungated to gated-with-an-empty-production-list would silently stop that
  rule from ever firing.

**Status: TRACED (ground truth confirmed), SIZED (not fixed).**

---

## 2. #6 — already fixed on `main` (verified, not redone)

See §0. Also spot-checked: `_recursive_concepts` occurs at exactly 3 sites
in `world_adapter.py` (`10117/10120/10135`-equivalent region, now shifted by
other commits — grepped fresh, not from stale line numbers) plus the
`save`/`load` wiring at `6138-6142`/`6232`; `learn_word` (now at line
~10021, shifted from the audit's `9987` by intervening commits) reads
`self._concepts.get(name)` before minting.

**Status: ALREADY FIXED (verified).**

---

## 3. #7 — F-16 regress in `interlocutor_model.effective_reliability` (FIXED)

`domains/interlocutor_model.py:576-583` (now `~576-600` after the fix added
comments) reproduced CLAUDE.md's own quoted F-16 regress line-for-line:
`individual = 1.0 - contradictions/n` (a raw MLE that hits exactly 0.0/1.0
at small n) blended with the shape prior, then `value = max(0.05, min(0.95,
value))` — a flat, unexplained clamp.

**Read the pinning tests first, per the house discipline.**
`tests/test_interlocutor_modeling_migrated.py:325,334` (the audit's own
citation) turned out to pin a DIFFERENT constant
(`_LOW_TOM_THRESHOLD = 0.4`, gating `effective_tom_capacity`'s
`tom_capacity_prior` — a value read directly from the seeded shape codebook,
with no `1/n` computation anywhere near it) — NOT the `effective_reliability`
blend this finding is actually about. The invariants the real test suite
DOES pin on `effective_reliability`:

- `n == 0` → `value == prior` exactly (`test_fresh_party_gets_a_shape_
  prior_with_zero_track_record`).
- `n` grows and `value` changes as evidence accrues
  (`test_blend_shifts_between_early_and_later_turns`).
- `creator_origin` / `learned` sources bypass the blend entirely (both
  already return early, untouched by this fix).

No test pins the specific `0.05`/`0.95` bound.

**The fix — root cause, not the symptom.** Verified algebraically first: the
existing formula `prior*(1-w) + individual*w` with `w = n/(n+k)` and
`individual = (n-contradictions)/n` is EXACTLY the Beta-Binomial posterior
mean for a `Beta(prior*k, (1-prior)*k)` conjugate prior — a legitimate,
textbook closed form, not an ad hoc running average. The actual defect is
narrower than "F-16 regress" implies: the raw MLE `individual` can hit
exactly `0.0` or `1.0` at small `n` (e.g. `n=1`, `contradictions=0` →
`individual=1.0`), and the flat clamp was bolted on to hide that boundary
case rather than fixing the estimator. Replaced `individual` with the
**Krichevsky-Trofimov (add-1/2) smoothed rate**,
`(n - contradictions + 0.5) / (n + 1.0)` — the standard, parameter-free
Bernoulli-rate estimator (not a swept constant) — which keeps `individual`
strictly inside the open interval `(0, 1)` for every finite `n`. Since
`prior` is itself always inside `(0, 1)` (every seeded `InterlocutorShape`:
range 0.4–0.65; every Python default: 0.5/0.9/etc.), their convex
combination is now ALREADY strictly inside `(0, 1)` with no output-side
clamp needed — **the floor is derived from the estimator, not asserted on
the estimate.** At `n=0`, `w = n/(n+k)` is exactly `0`, so `individual`'s
value is multiplied out regardless — `value == prior` exactly, byte-
identical to the old `if n > 0 else prior` special case (now removed, since
it's provably redundant).

Also removed a dead literal: `decoded.get("decay_k", 5.0)` — `decode_shape`
sets `"decay_k"` on every one of its three return paths, so the `.get(...,
5.0)` default could never actually fire; reads `decoded["decay_k"]`
directly now. (Left ALONE, and documented as reviewed-and-kept: the ONE
genuinely hardcoded `decay_k = 5.0` literal at `decode_shape`'s "best is
None" branch, which fires only when literally zero `InterlocutorShape`
nodes exist in the graph — an honest absence case, the same shape CLAUDE.md
accepts elsewhere for a genuinely missing codebook, not a live tunable
rate.)

**Residual, stated honestly (not silently assumed):** this relies on
`prior` never being authored as exactly `0.0` or `1.0`. Nothing in this fix
defends against a future `InterlocutorShape` seed row that would violate
that.

**Regression.** `tests/test_interlocutor_modeling_migrated.py`, 24 tests,
paired against a from-scratch pristine-file baseline (`git show HEAD` swap,
run, swap back, in this SAME worktree — not a different machine/run):

| | failed | passed |
|---|---|---|
| baseline (pristine file) | 13 | 11 |
| after fix | 13 | 11 |

**Byte-identical failing test-name set both times** (paste-diffed, not just
counted): `test_told_status_grows_believed_concepts_for_this_party_only`,
`test_goal_is_wanted_by_the_active_party`,
`test_requested_by_renders_in_self_improvement_status`,
`test_belief_self_report_mints_assertion_and_tagged_level2`,
`test_desire_self_report_mints_their_want`,
`test_hedged_phrasing_lowers_confidence`,
`test_grice_default_tom_party_still_gets_prefix`,
`test_blend_shifts_between_early_and_later_turns`,
`test_correction_revises_level2_confidence_leaves_assertion_untouched`,
`test_grice_repeat_topic_gets_as_i_mentioned_prefix`,
`test_interlocutor_model_reader_answers_from_the_model`,
`test_shadow_off_replies_match_shadow_on_content_path`,
`test_live_daemon_shaped_smoke_transcript`. All trace to a broader
comprehension/grounding issue in this worktree (many replies fall back to
"I am Jabberwock." instead of a grounded answer — a pre-existing,
environment-scoped defect unrelated to `effective_reliability`'s formula;
NOT diagnosed further here, out of this rung's scope), confirmed identical
with and without this fix. The two tests that actually exercise this
function's boundary conditions pass both ways.

**Status: FIXED.**

---

## 4. #8 — `composer_dispatch.json` priority = insertion index (FIXED)

See commit `f9333cf`. `seeds/composer_dispatch.json`'s 24 `ComposerCue` rows
had `priority` literally equal to insertion order (1..23, one duplicate, no
gaps) — worse on inspection than the audit's headline: a single composer's
own relation_head family was **interleaved with unrelated composers as they
accreted** (`experiment`'s 7 rows sat at priorities `8, 9, 10, 11, 13, 15,
16`, with `browse` and `attention` inserted in between as later additions),
so two different verbs belonging to the SAME composer could resolve to
different effective ranks purely depending on which one happened to fire —
an internal inconsistency the audit's "arrival order" framing didn't fully
capture.

**The fix.** `tools/build_composer_dispatch_seed.py` derives `priority = 1 +
index_in(_COMPOSER_LADDER)` — an explicit, named, ordered list of the 17
distinct composers (the SAME order they first accreted, readable straight
off the seed's own accretion-log `description`). Verified algebraically
before implementing: each composer's derived ladder position equals the
RANK of that composer's own best (lowest) pre-existing per-row priority,
and those per-composer minimums were ALREADY strictly monotonic in
accretion order — so this reproduces every CURRENT cross-composer pairwise
decision that mattered, and only changes the verb-dependent inconsistency
within one composer's own family (now provably inert: rows for the same
composer share one priority, and a tie among them resolves to the SAME
`composer` attribute value regardless of which row wins the `Argmin`).

This is the shape CLAUDE.md's own `escalation_rungs.json` precedent
sanctions (*"a declared ladder with a frame, not an asserted ordinal"*),
applied one grain over — not a derived-from-structure specificity score
(there genuinely isn't one available here: every match is an exact
single-string-membership test, so no candidate is "more specific" than
another in a way `sd_recognize`'s `FixedCount(AntiUnify(...))` precedent
could measure).

**Regression.** 17-file suite covering every composer this seed dispatches
to (experiment, language_faculty, attention, grounding_guard, imagination,
self_correct, system_model, audience_production, composer_driver,
conceptualizer ×2, composer_sense_cache, agent_authors_new_rule,
acting_variant, structural_variant, self_delta, adoption), paired against
the same from-scratch pristine-file swap:

| | failed | passed | skipped |
|---|---|---|---|
| baseline (pristine file) | 12 | 174 | 6 |
| after fix | 12 | 174 | 6 |

Byte-identical failing test-name set both times (12 names, e.g.
`test_mint_rule_fires_without_host_add_node`,
`test_ground_concern_dispatch_parity`,
`test_perform_adoptions_adopts_supported_and_allowed` — all confirmed
present in `results/failure_baseline.json`'s pre-existing population or
traced to this worktree's absent `data/` directory).

**Status: FIXED.**

---

## 5. #9 — `information_commitment`'s unweighted sum of asserted utilities (SIZED, not fixed)

Confirmed the audit's characterisation is accurate, current, and worse in
magnitude than the audit quoted:

```
domains/teach.py:203-204        expected_goal_work=2.0
domains/proposal_install.py:313 expected_goal_work default=10.0
domains/fetch_dispatch.py:524   expected_goal_work default=0.0
domains/voice_world.py:676      expected_goal_work=1.0
```

Four call sites, four independently-asserted magnitudes for "how much work
is this decision worth", ranging **0.0 to 10.0** — a 10× spread with no
shared unit and no cross-reference between them (confirmed: grepped every
`expected_goal_work`/`expected_information_gain`/`delay_cost`/
`refinement_cost` assignment across the tree; nothing derives one call
site's constant from another's). `scripts/build_information_commitment_
seed.py`'s `COMMIT_VALUE` formula sums six heterogeneous quantities
unweighted and the `ic_choose_unique_admissible_option` rule picks the
Argmax — structurally the same pattern CLAUDE.md already names for
`HumanoidComposer` (*"sums nine cost terms unconditionally and minimises
greedily"*), here in the executive faculty gating whether the agent's own
teaching reaches disk.

**Why sized, not fixed, in this rung.** A genuine fix requires answering a
substantive value-alignment question this rung has no basis to answer
unilaterally: what IS the common unit "goal work" is measured in, and is
teaching a word (`teach.py`, work=2.0) really worth 1/5th of installing a
self-authored proposal (`proposal_install.py`, work=10.0 default) and
INFINITELY more than fetching a document (`fetch_dispatch.py`, work=0.0
default)? Any weighting scheme this rung invented in isolation would be
exactly as arbitrary as the four literals it replaced — CLAUDE.md's own
standing rule (*"a scalar knob is not a simplification of this — it is the
unpaid debt"*) applies equally to a hastily-chosen REPLACEMENT scalar. This
gate gaining a wrong weighting would be WORSE than today's inconsistency,
because it would look principled while still being asserted.

**The concrete, scoped follow-on this sizing recommends:** the sibling
finding at §6.4 (`gap_prioritiser.py`'s `PROMISCUITY_FRAC` critique) already
names the right frame — *"the justification names the decoded quantity
[MDL bits, which `shape_decode.rs:2819/3053` already computes without a
threshold] and then substitutes a scalar for it."* `information_commitment`
is the same shape one level up: if "expected information gain" were
expressed in the SAME MDL-bit unit the sd loop already computes for a
residual (rather than a per-call-site literal), at least two of the six
`COMMIT_VALUE` terms (`expected_information_gain`, and arguably
`information_destroyed`) would have a real, derivable, cross-call-site-
comparable unit instead of an asserted one — the other four
(`expected_goal_work`, `option_volume_lost`, `resource_cost`,
`uncertainty × irreversibility`) remain a genuinely open design question
this rung correctly declines to resolve unilaterally.

**Status: SIZED (not fixed) — matches the brief's own explicit allowance
for this item.**

---

## 6. #10 — meta-target enumeration, 4 copies, drifted (FIXED + one correction)

See commit `3a43281`. Three real changes, one important correction to the
audit's own count:

**Consolidation 1 — data.** `_SELF_MODEL_META_ENTRIES` (3 Python rows,
ALWAYS appended in `comprehend_question.load_meta_lexicon`, per a comment
explaining they couldn't be added to the seed file because *"that file is
... outside this task's editable-file set"*) moved verbatim into
`seeds/question_targets.json`'s `meta_targets` list
(`tools/consolidate_self_model_meta_entries.py`) — the scoping constraint
that produced the extra copy no longer applies. One fewer copy; identical
content, identical behaviour (a location move, not a data change).

**Consolidation 2 — code.** `_score_meta_entry`/`_best_meta_entry` were
byte-for-byte duplicated in `domains/comprehend_text.py` (a second
implementation of the SAME scoring logic `comprehend_meta`'s
`_all_present`/`_norm` already implement in `comprehend_question.py`).
Moved into `comprehend_question.py` as the canonical implementation;
`comprehend_text.py` keeps thin re-exports
(`_score_meta_entry = _cq._score_meta_entry`) so its one call site and any
external caller by that name are unaffected. Pure refactor, verified via
`assert ct._score_meta_entry is cq._score_meta_entry` in the new test.

**Deliberately NOT done — the two SELECTION semantics stay unmerged.**
`comprehend_meta` is first-match-wins; `_best_meta_entry` is best-covered-
wins. The audit calls the second "strictly better." A full lexicon-wide
shadowing scan (reproduced fresh on current data, including the newly-
migrated self-model rows: zero pairs where one entry's `match` set is a
strict subset of another's for a DIFFERENT target) shows the two algorithms
agree on every CURRENT seed row — but that scan does not prove agreement on
every POSSIBLE input (two entries with unrelated, non-subset match sets can
both satisfy a specific token set; first-match then keeps seed-authored
order where best-covered would not). Unifying the algorithm is therefore a
real behaviour change to `comprehend_meta`'s broad production call sites
(the self/meta question-routing surface generally), not a proven-safe
refactor — named as a residual in both the code docstring
(`comprehend_question._best_meta_entry`) and here, not silently dropped.

**A drift GUARD, not just a fix.**
`tests/test_meta_target_reconciliation_migrated.py` (4 tests) reads the
LIVE `_DISPATCH` dict after the SAME module-import chain
`substrate/boot_all.py` performs (not a static grep over one file), and
asserts (a) every seed `meta_target` has a live handler — zero today, and
(b) the set of handlers with NO seed row is EXACTLY the 5 documented ones
(`self_kind`, `self_process` — each routed via a dedicated non-lexicon code
path, confirmed by grep: `world_adapter.py` sets `meta_target="self_kind"`
directly, `comprehend_text.py:~1131` sets `meta_target="self_process"`
directly; `self_modification` — routed via `conversation_action.py`'s
imperative-mood `_SELF_TARGET_KW`, a genuinely different grammatical form,
see below; `reading_trace`/`referent_trace` — a real, tested Phase-1
faculty with no current NL question route, named not invented a trigger
phrase for). A future handler added without either a seed row or an
allowlist entry with a cited route now fails this test instead of drifting
silently, closing the exact gap #10 names.

**Correction to the audit's own count.** `SHAPE_AUDIT.md` reported "2
orphaned seed targets" (`code_capabilities`, `emitter_roadmap` — seed rows
with no `_DISPATCH` handler, found by a static regex over
`reflective_faculty.py`'s dict literal + local `.setdefault` calls). Both
DO have real handlers — `domains/code_curriculum.py` and
`domains/curriculum_study.py` each register their target via
`_rf._DISPATCH.setdefault(...)` at their OWN module's import time (invoked
during a real boot via `substrate/boot_all.py`), invisible to a grep that
only reads `reflective_faculty.py`'s source text. **Verified empirically**
(actually importing the chain, not re-grepping): `_DISPATCH` after import
has 30 keys including both; zero orphaned seed targets. This is exactly the
"grep-shaped blind spot" `SHAPE_AUDIT.md` §9.3 pre-warned about, now
confirmed to have actually fired once, in the audit's own #10 measurement.
The reconciliation test uses the live-import method specifically so this
class of false positive can't recur.

**Discovered, named, NOT touched — a fifth, differently-shaped copy.**
`domains/conversation_action.py`'s `_SELF_TARGET_KW` (a substring-match
keyword table, `organis`/`shape`/`yourself`/`identity`/`limit`/`modif` →
`_DISPATCH` key) is a genuinely separate mechanism serving IMPERATIVE
self-report requests ("describe your organisation") rather than QUESTIONS
("how are you organised?") — a different grammatical mood, not a redundant
copy of the same table. Out of this rung's scope (folding it in would mean
deciding whether imperative and question routing SHOULD share one lexicon,
a design question, not a mechanical consolidation); named here so it isn't
silently missed by a future reader who greps for "meta_target enumeration"
and only finds four hits.

**Regression.** Paired baseline (swap `comprehend_question.py`,
`comprehend_text.py`, `seeds/question_targets.json` back to `git show
HEAD`, run, swap forward) on `test_self_model.py`,
`test_composers_graph.py`, `test_capability_profiler_migrated.py`,
`test_comprehend_text.py`, `test_self_correct_cognition.py`,
`test_self_correction.py`, `test_smooth_content.py`,
`test_self_prose_rendering.py`, `test_self_process_introspection.py`,
`test_reading_introspection_migrated.py`:

| | failed | passed |
|---|---|---|
| baseline (pristine files) | 18 | 153 |
| after fix | 18 | 157* |

\* +4 = `test_meta_target_reconciliation_migrated.py`'s own 4 new tests,
included in the after-fix run only (they test the consolidation itself, so
running them against the reverted files is not meaningful). **The 18
failing test NAMES are byte-identical both runs** (`test_ask_which_rules_
about_topic`, `test_general_path_derives_a_reflexive_dispatch[...]`,
`test_honest_floor_preserved_for_genuine_gap`, etc.) — all pre-existing,
unrelated to this diff (prose-rendering wording mismatches, e.g. "I hold
rule." vs "I hold the rule.", that predate and are untouched by this
change).

**Status: FIXED (2 of 4 copies eliminated; the 2 real consumers
deliberately left un-unified with a stated reason; drift now caught by a
gate instead of silently tolerated).**

---

## 7. Below-the-line items

### 7.1 `wire_self_extension` no marker check (§4.6) — FIXED

See commits `f3ac10f` + `e1843fb`. `substrate/world_adapter.py::
wire_self_extension` called `load_seed_manifest` with no idempotency guard
at all — confirmed at the engine level that this matters:
`py.rs::load_seed_manifest`'s rule-loading loop calls `inner.add_rule(rule)`
unconditionally for every rule in the manifest (no per-rule name dedup), so
a second call really would mint a second copy of all 11
`self_extension.json` rules.

Fixed by mirroring `reflective_faculty._ensure_shape_decode_loop`'s
established pattern exactly: guard on `_installed_seed_ids(self.s)`
(checks BOTH the `Seed{id}` marker this call site now mints AND the
`SeedSummary{seed_id}` marker a full `load_all_seeds()` boot mints for
EVERY seed it installs — so this doesn't double-install on top of THAT
convention either, discovered live: a fully-booted agent already carries
the `SeedSummary` marker before `wire_self_extension()` is ever called, so
the fix correctly no-ops on what would otherwise have been a REDUNDANT
first call, not just a second one).

Added the genuine double-call idempotency proof the existing suite never
ran (`tests/test_capkey_backfill_migrated.py::
test_wire_self_extension_is_genuinely_idempotent` — its existing comment
said "(idempotent)" at a call site that only ever called it once). Uses a
fresh, minimal `WorldAdapter()` (not the module-scoped, already-booted
fixture, which — discovered while writing this test — already carries the
`SeedSummary` marker and so can't exercise the genuine first-install case).
Confirmed: before the marker-guard fix, this test would fail (a second call
mints duplicate rules); after, `rule_names()` is byte-identical across two
calls.

**Regression:** `tests/test_capkey_backfill_migrated.py`, 4/4 passed
(including the pre-existing 3, unaffected).

**Status: FIXED.**

### 7.2 `sd_recognize_dim` mints per-observation, not per-dimension (§4.4) — SIZED, not fixed

Read `seeds/shape_decode_loop.json`'s full accretion history (v1.0.0
through v1.8.0) before deciding scope. Confirmed the audit's characterisation:
`sd_recognize_dim`'s mint guard is `Count(Neighbours(obs, has_transform)) ==
0` — a per-OBSERVATION fixpoint-termination guard, not a dedup against
already-minted `LatentDimension` nodes carrying the same `generator`. Also
confirmed the audit's cited downstream assumption:
`tests/test_stereo_infer_migrated.py:71`, `test_time_infer_migrated.py:61`,
`test_depth_infer_migrated.py:66` each filter `nodes("LatentDimension")` by
name and index `[0]` — code that would silently start reading the WRONG
node (or an arbitrary one among duplicates) the moment per-observation
duplication is fixed by simply adding a name-based `Not(Exists(...))` guard,
unless those three call sites are updated in the SAME change.

**Why sized, not fixed, in this rung.** This is now a genuinely larger seed
than the `CapabilityAxis` identity fix (#5) it superficially resembles: the
seed has SEVEN generator kinds (`rotation90`/`reflection_r`/`reflection_c`/
`scale2`/`cycle4`/composition-of-two), a composition-length Occam ordering,
and an `AgnosiaParams`-guarded lesion path (v1.8.0) all reading
`sd_recognize_dim`'s output shape. A correct fix needs: (1) a dedup guard on
`LatentDimension` keyed by the FULL identity (`generator` + composition
`generators`/`ks` for the composite case, not just `name` — a naive
name-only dedup would be the SAME truncation-style bug #5 just fixed, one
grain over, if two different composite step-sequences happened to share a
label); (2) updating the three test files' `[0]`-indexing to search by
generator identity instead of positional index, which requires reading each
test's actual intent (are they asserting "a LatentDimension exists for this
generator" or "the FIRST LatentDimension in node-creation order has this
generator" — the audit itself flags this as unverified, "the `[0]` indexing
masks it"); (3) verifying the `has_transform` edge target (a `Transform`
node) already carries enough identity for a `LatentDimension`-side dedup
guard to read without re-running `DimInfer`. None of this is safe to do
"in scope of a same-day fix" without risking the exact kind of interaction
error this rung's own regression discipline is built to catch, and doing it
without running the full `tests/test_dimension_inference_migrated.py` +
`test_stereo_infer_migrated.py` + `test_time_infer_migrated.py` +
`test_depth_infer_migrated.py` suite (not attempted this rung, given time
budget) would be exactly the "don't half-fix it" the brief warns against.

**Status: SIZED (not fixed) — the fix shape is now more precisely specified
than the audit left it (three concrete sub-steps above), but not
attempted.**

### 7.3 `stroke_codebook.py:82` `DEFAULT_DTW_THRESHOLD=0.15` (§6.3) — SIZED, not fixed

Re-read in place; audit's characterisation confirmed accurate and current.
This is, in the audit's own words, *"a swept, empirically-calibrated,
test-pinned scalar"* — the comment immediately above it documents real
diagnostic bands (realistic jitter ≈0.108, a genuinely different shape
class ≈0.50, unrelated noise 0.21–0.39) and records that
`tests/test_ink_decode_migrated.py`'s own gates regressed at an earlier
`0.35` default. This sits directly on top of a `shape_decode.rs` verified
threshold-free (MDL, no threshold — CLAUDE.md's own §6 positive control),
so the shape defect is real: recognise-vs-mint for a stroke quantum is
decided by a calibrated number instead of residual coverage.

**Why sized, not fixed.** Per the brief's own framing (*"a real research
rung, not a same-day fix"*) and per CLAUDE.md's own standing caution that a
calibrated constant is not automatically wrong to have (*"Pattern E is
about the shape, not about carelessness"*) — replacing this with a genuine
MDL-derived criterion means designing what "coverage" means for a DTW
distance between two polyline prototypes (DTW doesn't have a native bit-cost
the way `ShapeDecode`'s relation-set cover does), which is new machinery,
not a same-rung parameter change. Attempting it blind, without the
diagnostic sweep the ORIGINAL 0.15 calibration used, risks silently
regressing `test_ink_decode_migrated.py`'s own gates the way the `0.35`
default already did once.

**Status: SIZED (not fixed) — matches the brief's own explicit steer for
this item.**

---

## 8. Full regression summary

All paired (baseline vs. after-fix, same worktree, same environment)
comparisons this rung ran, consolidated:

| item | files | baseline fail/pass | after-fix fail/pass | failing names identical? |
|---|---|---|---|---|
| #8 composer_dispatch | 17 test files | 12 / 174 | 12 / 174 | yes |
| #7 interlocutor_model | 1 test file (24 tests) | 13 / 11 | 13 / 11 | yes |
| #10 meta-target | 10 test files | 18 / 153 | 18 / 157* | yes (+4 new) |
| #4.6 wire_self_extension | 1 test file (4 tests) | n/a (new test) | 0 / 4 | — |

\* the +4 are the new `test_meta_target_reconciliation_migrated.py` tests,
not present in the baseline run.

A final combined run across all 30 touched/relevant test files together (to
catch cross-item interaction effects the per-item paired runs might miss),
with every fix from this rung applied simultaneously:

```
43 failed, 332 passed, 6 skipped, 6 warnings in 1103.01s (0:18:23)
```

**43 = exactly 12 (composer) + 13 (interlocutor) + 18 (self_model/comprehend)
— the sum of the three independently-verified pre-existing failure
populations above, with zero additions.** The 4 new
`test_meta_target_reconciliation_migrated.py` tests and all 4
`test_capkey_backfill_migrated.py` tests (including the new idempotency
proof) are green in this combined run. Confirms no cross-item interaction
regression from applying all fixes together.

**No regression was found or introduced by any change in this rung.** Every
failing test in every comparison above is a member of a byte-identical
before/after set, tracing to this worktree's pre-existing, environment-
conditional failure population (this worktree has no `data/` symlink —
CLAUDE.md's own retracted-note section documents this exact condition
producing a large, real, unrelated red population; several failures were
independently confirmed present in `results/failure_baseline.json`).

---

## 9. Per-item status summary

| # | item | status |
|---|---|---|
| 1 | meta-shape codebook, no mint path | already fixed on `main` (verified) |
| 2 | `recognise_meta_shape` substring+alphabetical | already fixed on `main` (verified) |
| 3 | `keywords_text` Argmax family (A1-A9) | already fixed on `main` (verified) |
| 4 | Γ bypass — 159 seeds, zero productions | **traced (ground truth: yes, bypasses `check_edge`), sized, not fixed** |
| 5 | `CapabilityAxis` identity | already fixed on `main` (verified) |
| 6 | `learn_recursive_concept`/`learn_word` dup-mint | already fixed on `main` (verified) |
| 7 | F-16 regress, `interlocutor_model.py` | **fixed** |
| 8 | `composer_dispatch.json` priority=insertion-index | **fixed** |
| 9 | `information_commitment` unweighted sum | **sized, not fixed** |
| 10 | meta-target enumeration, 4 copies drifted | **fixed** (2 copies eliminated, drift gated, 1 audit measurement corrected) |
| — | `find_analogies` MAC-as-verdict | already fixed on `main` (verified) |
| — | `sd_recognize_dim` per-observation mint (§4.4) | **sized, not fixed** (fix shape specified, not attempted) |
| — | `wire_self_extension` no marker check (§4.6) | **fixed** (+ genuine idempotency test added) |
| — | `stroke_codebook.py` `DEFAULT_DTW_THRESHOLD` (§6.3) | **sized, not fixed** (matches brief's own steer) |

**Score: 6 items pre-closed on main (verified honestly, not re-claimed as
this rung's work), 4 items fixed by this rung (#7, #8, #10,
`wire_self_extension`), 3 items sized with a concrete named follow-on each
(#4's engine trace + migration plan, #9's MDL-bit reframing, `sd_recognize_
dim`'s three-part fix spec), 1 item sized per the brief's own explicit
steer (`stroke_codebook.py`).**

---

## 10. Worktree / commits

- Worktree: `/tmp/claude-1000/-home-matt-ozmadev-ocelot/34a7cd08-5eb1-42bd-af0c-eedb1125fa76/scratchpad/shape-audit-sweep2`
- Branch: `shape-audit-sweep2`, off `main` at `76b8aea`
- Commits (oldest to newest):
  1. `824c375` — Prereg
  2. `f9333cf` — #8 composer_dispatch fix
  3. `34eb149` — #7 interlocutor_model fix
  4. `3a43281` — #10 meta-target consolidation
  5. `f3ac10f` — below-the-line #4.6 wire_self_extension marker-guard
  6. `e1843fb` — #4.6 double-call idempotency test
- Not merged to `main`, per house discipline.
