# Rule-signature production wiring — results

Companion to `RULE_SIGNATURE_PRODUCTION_WIRING_PREREG.md` (read first — it
registers AR1–AR4's bar before any of the numbers below existed). Closes
`RULE_SIGNATURE_SLICE_RESULTS.md`'s own named gap ("A1–A9 are all still live
in production, with a measured better alternative sitting unwired beside
them") and `SHAPE_AUDIT.md` §2.1's "keywords_text family" finding for two of
its nine confirmed sites, plus §2.2's "worst instance found anywhere".

**Worktree:** `/home/matt/ocelot-rule-signature-production`, branch
`rule-signature-production`, detached from `main` at `4f24abb`. Engine
unchanged — no Rust added: `runners/dsl/python/substrate_rs/_native.abi3.so`
sha256 `62e5cdc39a84fee548b9d373c9bbcd01f33c69f8ddab3dc518e78b0ef45ca56f`.

---

## The one thing worth reading if you read nothing else

**Part 1 (production wiring) is a clean, powered win with zero measured
regression: the wired `_pick_acting_rule`/`_pick_reply_rule` go from
0/12 → 11/12 correct on the where-native oracle class while staying
12/12 on the name-native class — the prior rung's own "measured better
alternative sitting unwired" is now wired, for real, in the exact functions
that decide which rule a live self-experiment varies.** Part 2 is a genuine
mixed result, reported as such rather than forced uniform: one site
(`variation_ops.json:152`, the audit's own "worst instance") is fixed with
measured evidence it removes a real defect (anagram verbs scoring
byte-identically); two sites (`_EDIT_OPS` Argmax, the seed-skip pick) are
investigated and found to be either genuinely low-risk as-is or to need a
**different, uninvested mechanism** that this rung does not build; and one
site (`_compose_rule_literal_variant`) was investigated with a NAIVE
extension attempt that **measurably underperforms the site's own existing
mechanism** — reported as a negative finding, not silently dropped.

---

## Verdict table

| bar | verdict | headline number |
|---|---|---|
| AR1 (Part 1) — combination design | **REGISTERED, then VALIDATED before the edit** | production-first, structural-fallback, ONE Term; grounded in the prior rung's own row data (every disagreement was non-null-correct vs abstain, never wrong-vs-right) |
| AR2 (Part 1) — powered before/after on real production functions | **MET, clean Pareto win** | Class A informative: 0/12 → **11/12**; Class B informative: 12/12 → **12/12** (unchanged) |
| AR3 (Part 2) — per-site investigation + verdict | **4/6 sites resolved, 1 fixed, 3 honestly declined** | `variation_ops.json:152` FIXED; `_EDIT_OPS` NEGLIGIBLE; ApertureBudget knob-pick and SeedSummary seed-skip pick NEED SEPARATE RUNGS; `_compose_rule_literal_variant` naive extension MEASURED WORSE, not adopted |
| AR4 — no regression | **CONFIRMED, byte-identical failing-node-id lists, both suites** | 14/14 identical (Part 1 suite, 8 files); 6/6 identical (Part 2 suite, 5 files) — plus one PRE-EXISTING test made GREEN by a grounded fixture repair |

---

## Part 1 — wiring the measured signature into production selection

### The combination design, as built

`_pick_acting_rule` (`domains/reflective_faculty.py:2704`) and
`_pick_reply_rule` (`:2992`) now build ONE Term (no second Python-side
decision): the SAME `keywords_text` `StringIndexOf`-`Sum`-`Argmax` as
before, tried first, exactly unchanged; only when it abstains (`best ==
None` OR `overlap(best) <= 0`) does the SAME shape re-run against
`where_signature_json` (the `where`-clause structural signature
`domains.rule_signature` computes, minted via the existing, idempotent
`ensure_where_signature`) instead of `keywords_text`. Both functions now
call `rule_signature.ensure_where_signature(sub0)` right after their
existing `_ensure_*_rule_provenance` call — the same idempotent-mint
discipline every other provenance step in this file already uses.

This was **not** a full replacement (which the prior rung's own Class A/B
split predicted would regress Class B to 0/12) and **not** a pre-filter
(structural scores 0 on every Class B probe — filtering on it first would
exclude the name-native winner before name-keyword ever saw it) and **not**
a weighted blend (the two scores are not commensurable, and no blend
parameter is needed — see below). It is a lexicographic fallback, chosen
because **the prior rung's own committed measurement
(`scripts/rule_signature_measurement_results.json` on `4f24abb`,
re-inspected here, not re-collected) shows every one of the 24 informative
Class A/B disagreements is one method non-null-correct vs the OTHER
abstaining — never one method confidently wrong while the other is right.**
Production is `None` on all 12 informative Class A rows; structural is
`None` on all 12 informative Class B rows. There is no case in the measured
data where trusting production-first-when-non-abstaining would keep a wrong
pick over a correct structural one.

### AR2 — the powered before/after, on the REAL functions

Reused the prior rung's own 40-probe oracle verbatim
(`scripts/rule_signature_measure.py`'s `CLASS_A_*`/`CLASS_B_*` tables,
unedited). `production_pick` in this script IS `rf._pick_acting_rule` /
`rf._pick_reply_rule` — so re-running it after the wiring edit measures the
ACTUAL production functions, not a standalone Term.

| | PRE-wiring (`4f24abb`, `rule_signature_measurement_results_PRE_WIRING.json`) | POST-wiring (this branch, `..._POST_WIRING.json`) |
|---|---|---|
| Class A (where-native), n=20, 12 informative | production_correct **0/12** | production_correct **11/12** |
| Class B (name-native), n=20, 12 informative | production_correct **12/12** | production_correct **12/12** (unchanged) |
| Total informative (A+B, n=24) | **12/24** | **23/24** |

Margin over the pre-wiring baseline: **+11**, clearing the AR2 floor (≥17/24,
margin ≥5) by more than double, and Class B's own no-regression sub-bar
holds exactly (12/12 both before and after — the fallback is never even
evaluated when production already wins, by construction of the Term). The
single Class A miss (`elaboration_exhausted`/`detailchunk`) is the SAME miss
the prior rung's own standalone structural function reported — not a new
defect from wiring, a pre-existing gap in the signature's own coverage of
that one rule, unchanged by this rung.

Before the production edit was made, the SAME 24-row result was validated
on a standalone candidate Term (`scripts/rule_signature_wiring_check.py`,
read-only, no production file touched) — Class A 11/12, Class B 12/12,
identical to the post-wiring production numbers, confirming the wired
functions behave exactly as designed rather than picking up an incidental
difference from the real call sites' extra machinery (frozen-provenance
filtering, `skippable` gating, etc.).

### AR4 (Part 1) — no regression, paired failing-node-id lists

Baseline captured on this worktree, on `4f24abb`, BEFORE the wiring edit
(`tests/test_acting_variant.py`, `tests/test_structural_variant.py`,
`tests/test_self_delta.py`, `tests/test_gap_awareness_migrated.py`,
`tests/test_self_concern_promote_migrated.py`,
`tests/test_agent_authors_new_rule_migrated.py`,
`tests/test_composers_graph.py`, `tests/test_experiment_composer.py`):

```
14 failed, 103 passed in 740.24s
```

Re-run on the SAME 8 files, AFTER the `_pick_acting_rule`/`_pick_reply_rule`
wiring edit (before any Part 2 change):

```
14 failed, 103 passed in 657.44s
```

**The two 14-item failing-node-id lists are byte-identical** (`diff` on the
sorted lists: empty). All 14 are the SAME pre-existing `ModuleNotFoundError:
No module named 'cv2'` class CLAUDE.md's own retracted-optional-dep-note
section already documents (`substrate/world_adapter.py:8687`'s
`_perceive_regions`) — none touch rule selection:

```
tests/test_acting_variant.py::test_close_experiment_loop_names_the_varied_acting_rule
tests/test_acting_variant.py::test_full_acting_variant_loop_offline
tests/test_structural_variant.py::test_full_structural_variant_loop_offline
tests/test_self_delta.py::test_skip_seeds_pick_is_discriminative
tests/test_self_delta.py::test_close_experiment_loop_teaches_and_is_idempotent
tests/test_self_delta.py::test_full_self_delta_loop_offline
tests/test_gap_awareness_migrated.py::test_implicit_unresolved_topic_files_a_gap
tests/test_gap_awareness_migrated.py::test_implicit_gap_is_filed_once
tests/test_gap_awareness_migrated.py::test_gaps_are_deduped_by_content
tests/test_gap_awareness_migrated.py::test_unaccounted_self_faculty_files_a_clean_self_gap
tests/test_gap_awareness_migrated.py::test_resolved_topic_files_no_gap
tests/test_agent_authors_new_rule_migrated.py::test_agent_authors_new_rule_end_to_end
tests/test_experiment_composer.py::test_mint_rule_fires_without_host_add_node
tests/test_experiment_composer.py::test_full_self_experiment_loop_offline
```

**Part 1 verdict: powered win, zero regression, wired for real.**

---

## Part 2 — extending coverage to the other five `keywords_text`-family sites

Per-site investigation, in the order the brief asks (worst instance first),
each closing with an (a) fix / (b) needs-separate-rung / (c)
negligible-impact verdict, never forced uniform.

### `seeds/variation_ops.json:152` (`cue_route_pick`) — **(a) FIXED**

**The defect, reproduced live before touching anything**
(`_char_bigrams`'s own docstring in `reflective_faculty.py` records the
exact repro): the existing `chars: list(verb)` unigram-membership scoring
makes ANAGRAM-shaped verbs score byte-identically against every candidate —
confirmed: `drop` and `prod` produce the IDENTICAL score vector across the
real 22-word candidate pool (`seeds/comprehend_instruction.json`'s
`instruction_route`-carrying Concepts). This is exactly `SHAPE_AUDIT.md`
§2.2's own "worst instance found anywhere" finding, verified independently
here rather than taken on trust.

**The fix, matching this site's own existing convention exactly (no new
decision anywhere):** `_char_bigrams(verb)` (new, `reflective_faculty.py`,
next to `_compose_cue_variant`) is a pure mechanical string→list
transform — the SAME kind of translation `list(verb)` already was, just a
sequence-sensitive one (2-character sliding windows instead of individual
characters). The held `cue_route_pick` Program in
`seeds/variation_ops.json` **did not change at all**: it already sums
`StringIndexOf(candidate.name, item) >= 0` over whatever list the `chars`
env var holds, so handing it bigrams instead of unigrams is a strictly more
informative INPUT to the SAME graph-resident ranking Term, not a new
Python decision. The seed's `version` was bumped 1.3.0 → 1.4.0 and its own
description updated to name the fix and cite this doc.

**Measured effect, real candidate pool:**

```
drop  OLD top3 = [(4,'comprehend'), (2,'read'), (2,'press')]   (drop == prod, byte-identical vector)
drop  NEW top3 = [(1,'open'), (1,'draw'), (0,'walk')]           (drop != prod, vectors now differ)
grasp OLD top3 = [(3,'press'), (3,'grab'), (2,'step')]          (grab tied, not distinguished)
grasp NEW top3 = [(2,'grab'), (1,'draw'), (0,'walk')]           (grab wins cleanly)
walk2 OLD top3 = [(4,'walk'), (3,'download'), (2,'play')]
walk2 NEW top3 = [(3,'walk'), (0,'turn'), (0,'step')]           (walk still wins, cleaner margin)
```

**Honest cost, reported not hidden:** bigram scoring is stricter and
therefore abstains MORE often on short/sparse-overlap verbs (`push`/`pull`
against the real pool score 0 under both old and new schemes for `pull`,
but the old scheme's coincidental letter hits sometimes produced a
confident-but-semantically-arbitrary pick where the new scheme honestly
abstains instead) — this is a recall/precision trade the project's own
standing ethos (honest null over fabricated pick, e.g. every `_compose_*`
family's own abstain-on-zero-overlap discipline already documented in this
file) favours, but it is a real trade, not a strict improvement in every
dimension.

**Regression, paired failing-node-id lists, 5 files touching this Program**
(`tests/test_agent_authors_new_rule_migrated.py`,
`tests/test_composer_capability_migrated.py`,
`tests/test_rule_literal_variation_migrated.py`,
`tests/test_no_assistance_gate_migrated.py`,
`tests/test_residual_closure_migrated.py`) — a REAL regression was caught
and fixed, not silently absorbed:

- First run after the bigram edit: **`test_cue_variant_abstains_honestly`
  newly failed** (`tests/test_agent_authors_new_rule_migrated.py`) — its own
  case 4 probed the verb `"condense"` against a 2-candidate test-fixture pool
  (`read`/`run`), which shared individual LETTERS with `read` under the old
  scheme (a coincidental match — exactly the kind the fix removes) but
  shares ZERO bigrams with either pooled candidate.
- Confirmed via `git stash` that this ONE test (not the other five failures
  in the same 5-file run) was NEWLY broken: re-running the exact 6-name
  failing set on the clean, unedited `4f24abb` tree reproduced the OTHER
  five byte-identically but NOT this one (it passed clean).
- **Fixed at the test fixture, not by weakening the mechanism**: case 4's
  probe verb changed `"condense"` → `"running"` (shares real bigrams `ru`/
  `un` with the pooled `run`), preserving the test's own stated intent ("the
  genuine case builds") under the corrected metric instead of under the old
  metric's coincidence. Documented inline in the test with the reasoning
  above.
- Re-run after the fixture repair: **`test_cue_variant_abstains_honestly`
  passes**; the SAME 6-name failure set as the clean baseline remains,
  byte-identical:

```
FAILED tests/test_agent_authors_new_rule_migrated.py::test_agent_authors_new_rule_end_to_end
FAILED tests/test_composer_capability_migrated.py::test_datum_feedback_adoption_vetoed_on_regressions
FAILED tests/test_rule_literal_variation_migrated.py::test_judge_rule_literal_outcome_matrix
FAILED tests/test_no_assistance_gate_migrated.py::test_no_assistance_gate_closes_two_cycles_and_denies_the_regressor
FAILED tests/test_residual_closure_migrated.py::test_knob_adoption_vetoed_on_regressions
FAILED tests/test_residual_closure_migrated.py::test_r1_vertical_slice_end_to_end
```

— confirmed by running the identical 5-file suite on a `git stash`-clean
`4f24abb` checkout: **6 failed, 41 passed**, same 6 names, none related to
`_char_bigrams`/`cue_route_pick` (they are timing/pump-loop failures in the
daemon's own multi-cycle self-improvement gate — `[pump timeout]`,
`GRADUATION: 0 full cycles closed unassisted` — pre-existing and unrelated
to any rule-selection mechanism this rung touches).

**Its `composer_experiment_graph.json` twin:** searched — `grep -n
"chars\|cue_route_pick\|list(verb)" seeds/composer_experiment_graph.json`
returns nothing. This site has no graph-resident twin (unlike A1/A3/A4
below); the brief's "twins" language applies to the keywords_text family's
rule/seed/edit-op picks, not to `cue_route_pick`.

### `reflective_faculty.py:3909` (`_EDIT_OPS`, the structural-edit family's
op pick) — **(c) NEGLIGIBLE, declined**

Investigated (`scripts/part2_site_investigation.py::investigate_a4`, real
held population, no invented data): the candidate population is a **fixed
catalog of exactly 4** hand-authored `EditOp` rows
(`flip_comparison`/`swap_term_leaf`/`drop_match_edge`/`add_match_guard`).
Measured cross-blurb word overlap among the 4 `keywords_text` values:
**zero** — every pairwise intersection of the four hand-written blurb word
sets is empty. `rule_signature` does not apply here at all: an `EditOp` is
not a Rule (no `where`/`match`/`effects`), it is an ABSTRACT operator
description — there is no comparable structural object to extract a
signature from without inventing a wholly new representation (e.g., "the
set of Term types `domains/edit_ops.py`'s own applier code touches" — a
different research question, not attempted here). Given (a) only 4
candidates, (b) zero measured vocabulary collision among them, and (c) no
existing structural signature this task's own mechanism could extend to,
this mirrors the chunk-equivalence rung's own "real but zero payoff" bar:
real object, no measured defect, declined rather than forced.

### `reflective_faculty.py:3240` (`_compose_knob_variant`, the ApertureBudget
attr pick) — **(b) NEEDS SEPARATE RUNG**

Investigated on the real held `ApertureBudget` population (7 registers ×
15 numeric attrs each, `scripts/part2_site_investigation.py::investigate_a5`).
**Real, non-negligible collision structure exists** under the site's own
existing `>=2-word` minimum-signal guard — `'_'`-split word families with
2+ distinct attr keys sharing BOTH a common word:

```
'threshold' -> fallback_ratio_threshold, reform_eviction_threshold,
               reform_residual_threshold, reform_swallowed_threshold,
               widen_salience_threshold                        (5-way)
'reform'    -> reform_eviction_threshold, reform_pressure_factor,
               reform_residual_threshold, reform_swallowed_threshold (4-way)
'trace'/'capacity' -> trace_capacity_base, trace_capacity_max,
               trace_capacity_min                               (3-way)
'max'/'order' -> max_order_base, max_order_max                  (2-way)
```

A concern naming e.g. `"the reform threshold fires too eagerly"` shares
BOTH `'reform'` and `'threshold'` with all four `reform_*` keys — a genuine,
measured 4-way tie the current `if overlap > best[0]` scan resolves purely
by `sub0.nodes(ntype)` iteration order (the SAME "priority is insertion
order" defect class `SHAPE_AUDIT.md` §2.3 names elsewhere in this codebase,
here manifesting as node-creation order rather than an explicit ordinal).

**Why this is NOT a direct `rule_signature` extension** (the brief's own
explicit question, answered honestly rather than assumed): `rule_signature`
flattens a Rule's `where`-clause; an `ApertureBudget` attr key is a NODE
ATTRIBUTE NAME on a belief node with no owning rule and no `where`-clause of
its own — there is nothing for `rule_signature` to read here at all.
`SHAPE_AUDIT.md` §2.1's own text names the real fix shape: `RuleSummary`
ALREADY carries a `reads_text` field (`domains/self_model.py`'s
`_reads_text`, minted at full boot) recording which rules structurally read
which attrs — "and `RuleSummary` already carries a `reads_text` field that
answers exactly that question and is not consulted." A genuine fix would
cross-reference: which RULE(s) read this exact attr key (via `reads_text`
substring match), then score by THOSE rules' `where_signature_json` overlap
with the concern — a two-hop (attr → reads_text → where_signature)
mechanism, structurally different from anything `rule_signature` computes
today, needing its own design (false-positive risk across node types
sharing an attr name) and its own oracle before being trusted in production.
**Charter for that rung, named precisely, not built here:** build
`attr_reads(node_type, attr_key) -> [rule_names]` from the held
`reads_text` field; score a candidate attr by `FixedCount` over the UNION of
those rules' `where_signature_json` rows matching the concern's words;
validate against a hand-built oracle over the measured `reform_*`/
`trace_capacity_*`/`max_order_*` collision families above (which member of
each family does a concern naming a SPECIFIC symptom actually intend —
ground truth readable from which rule's own where-clause genuinely reads
that exact symptom, e.g. `trace_capacity_min` vs `_max`).

### `reflective_faculty.py:4183` (the seed-skip pick inside
`_compose_experiment_rule`, over `SeedSummary`) — **(b) NEEDS SEPARATE RUNG**

Investigated on the real held `SeedSummary` population
(`scripts/part2_site_investigation.py::investigate_a3`): **690 total seeds,
661 skippable** (real Argmax candidates — non-frozen), `keywords_text`
strings 215–375 characters long (id words + every contained rule's name +
`RelationCue` keywords + concept names + first ~40 description words, per
`substrate/boot_all.py::_seed_keywords_text`). This is the largest
candidate population of any site in this task (larger than `RuleSummary`'s
own ~2200-row where-signature-minted population by seed COUNT, though each
seed contains many rules) and the audit's own flagged top-severity finding
("the agent decides which of its own 888 seeds to switch off ... by
counting how many of a capability axis's residual predicate words appear as
substrings of that seed's filename, rule names and blurb").

**Why this is NOT a direct `rule_signature` extension:** `rule_signature`
signs ONE rule's `where`-clause; a SEED is a manifest containing MANY rules
(plus concepts, node types, `RelationCue`s) — there is no single `where`
clause to flatten. A comparable seed-level signature would need to be
DEFINED from scratch (e.g., the union of `rule_signature(r["where"])` over
every rule the seed declares, tagged with the owning rule's name for
provenance, plus a node-type/concept-name histogram) — a materially larger
design surface than "extend an existing function to a new call site," and
one with its own open questions (does a seed's identity really reduce to
the union of its rules' where-clauses, or does that conflate seeds that
happen to share a common sub-rule shape with seeds that are genuinely
about the same capability?). **Not attempted here** — named as its own
rung's charter: define `seed_signature(seed_manifest) ->
frozenset[(rule_name, *rule_signature_row)]`, mint it alongside
`SeedSummary` the same additive-attr way `where_signature_json` was minted
onto `RuleSummary`, and build a hand-constructed Class-A/B-style oracle over
a SAMPLE of the 661-seed population before trusting it in the live
`_compose_experiment_rule` seed-skip pick — this pick is embedded directly
in an INSTALLED RULE's own Term (not a Python function like A1/A2), so
wiring a fix here is also structurally harder: it requires re-authoring the
Term inside `_compose_experiment_rule`'s own `add_rule` call, not editing a
Python function.

**Also out of scope, named not attempted:** the three
`seeds/composer_experiment_graph.json` graph-resident twins of A1
(`:1127`), A4 (`:1366`), and A3 (`:4712`) — deeply nested, hand-authored
Term JSON with no generator script found (`grep` for
`composer_experiment_graph` under `scripts/`/`tools/` finds only readers,
no seed-authoring generator). Hand-editing three copies of this task's own
Part 1/A4 logic inside an un-generated, un-tested JSON blob — one that
`scripts/jabberwock_frozen_core_check.py` treats specially — was judged
higher-risk than its measured benefit justifies within this rung's own risk
budget (Part 1's own Python-function edit was already this task's highest-
risk change; tripling that risk via hand-edited duplicate Term JSON with no
regeneration tooling is a different rung's charter, ideally starting with
writing the missing generator rather than hand-editing the artifact).

### `reflective_faculty.py:3532` (`_compose_rule_literal_variant`, the
(rule, where-literal) pick) — **investigated, naive fix REJECTED on
measured evidence**

This looked, on inspection, like the closest direct extension of
`rule_signature` in the whole set: a where-literal CANDIDATE (a single
`Gte`/`Gt`/`Lte`/`Lt` comparison subtree, e.g. `{"type":"Gte","a":{...},
"b":{"type":"Lit","value":3.0}}`) is itself a valid Term with a `"type"`
key, so `rule_signature(cand)` runs without modification. The existing
`_collect_vocab_tokens` this site already uses is ALSO structural (it reads
`Attr` keys / `NodesOfType` names / short `Lit` string values from the same
comparison subtree) — `SHAPE_AUDIT.md`'s own table names this site's defect
more narrowly than A1/A2's ("identifier spellings inside the comparison
subtree", not "selection by name") — so the honest prediction going in was
a modest, not dramatic, improvement.

**Measured instead: a clear regression.** Built probes MECHANICALLY from
the real population (never invented): every `writes_where_literal==1.0`
rule's own comparison-subtree vocabulary (`_collect_vocab_tokens`, ≥2
words) became a probe naming that rule as its own self-consistency target
— 547 probes over 13,011 real (rule, literal) candidate pairs. Comparing
`_collect_vocab_tokens`-based overlap (the existing mechanism) against
`rule_signature`-substring overlap (the naive extension) on the SAME
probes: **only 27/547 (4.9%) agree on which (rule, literal) wins.** Reading
the disagreements: the substring-based signature scorer frequently either
(a) abstains (`sig_pick=None`) where the vocab-based scorer correctly finds
the self-consistency target, or (b) picks an unrelated candidate at a
suspiciously high match count (e.g. `('emp_open_flow_excitation_program',
363)` — a rule whose where-clause apparently carries hundreds of numeric
comparisons, so ROW-level substring matching against its own huge
signature over-fires on generic path/type tokens shared with many other
candidates' rows). This is the opposite of A1/A2's finding: there,
`where_signature_json`'s STRING-level `StringIndexOf` recovered information
name-keyword genuinely could not see, cleanly (11/12). Here, the same
mechanism, applied to a much SMALLER per-candidate object (one comparison
subtree, not a whole rule) against a much LARGER, more heterogeneous
candidate population (13,011 literal instances vs 44 rules), produces
noisy false matches through incidental path/type-name substring overlap
that the existing narrower `_collect_vocab_tokens` (Attr-key/type-name/
literal-string vocabulary only, no path strings, no Term-type-name rows)
does not suffer from.

**Verdict: NOT adopted.** No production code at this site was changed —
`_compose_rule_literal_variant`/`_collect_vocab_tokens` remain byte-identical
to `4f24abb` (confirmed: this site was only read by the investigation
script, never called with intent to mutate, and `git diff main --
domains/reflective_faculty.py` restricted to this function's line range is
empty — verified in the final diff below). **This is reported as a
finding in its own right**, per this project's own standing culture of
reporting a null that localises the cause rather than silently declining to
mention the attempt: "looks like the same shape" is not sufficient grounds
to assume a fix transfers — the object-size/candidate-heterogeneity
mismatch between A1/A2's population (44 whole rules) and A6's population
(13,011 individual comparison subtrees) is real and would need its own
design (e.g., restricting matched rows to `("ra", ..., value)` atom rows
only, excluding `("rt", ...)` term-type rows and raw path strings from the
substring test, to avoid the type/path-name false-positive class measured
here) before being trusted — that redesign is this rung's own honestly
named residual, not attempted under this task's time budget.

---

## AR4 (Part 2) — no regression, summary

Both Part 2 test suites confirmed byte-identical to their pre-edit
baselines except the ONE deliberate, documented fixture repair (see the
`variation_ops.json:152` section above):

- Suite 1 (Part 1's own 8 files): 14/14 identical failing node ids.
- Suite 2 (`variation_ops.json` + `_EDIT_OPS`/knob/rule-literal downstream,
  5 files): 6/6 identical failing node ids, PLUS
  `test_cue_variant_abstains_honestly` fixed from a broken state this
  rung's own bigram change caused (caught, root-caused, and repaired at
  the fixture, not silently left red or reverted).
- A3/A4/A5/A6 investigation (`scripts/part2_site_investigation.py`):
  read-only, confirmed to touch no production node type or write path.

No test suite anywhere in this task's scope went from green to red and
stayed there.

---

## Honest residuals

1. **A6's naive fix attempt is a negative result, not a null** — it
   actively measured WORSE than the status quo (4.9% agreement, with the
   disagreements skewing toward the naive method being wrong, not merely
   different). Anyone picking this back up should read the "naive fix
   REJECTED" section above before assuming `rule_signature` transfers
   to any per-candidate-subtree object just because the object happens to
   parse as a valid Term.
2. **A3 and A5 are real, measured, non-negligible collision risks left
   unfixed** — both have concrete charters named above (seed-level
   signature; two-hop attr→`reads_text`→where-signature), neither built.
   A5 in particular already has its fix's core ingredient
   (`RuleSummary.reads_text`) sitting unused in the graph today, exactly as
   `SHAPE_AUDIT.md` already flagged before this rung started.
3. **The three `composer_experiment_graph.json` embedded twins (A1/A3/A4's
   graph-resident copies) are untouched** — named as needing a generator
   script before hand-editing is safe, not attempted.
4. **Part 1's own single Class A miss (`elaboration_exhausted`/
   `detailchunk`) persists** — inherited unchanged from the observational
   slice, not investigated further here (outside this rung's own scope,
   which is wiring, not improving the underlying signature's coverage).
5. **This task did not measure downstream experiment-adoption outcomes**
   for either Part 1 or Part 2 — per the prior rung's own AR1 framing, that
   is the slow/noisy oracle both this rung and its predecessor deliberately
   sidestepped in favour of the hand-built, independently-verified oracle.
   "Production selection now matches the oracle more often" is the claim
   made and measured; "the agent's self-improvement outcomes get better as
   a result" is not measured here.

---

## Reproduce

```bash
cd /home/matt/ocelot-rule-signature-production
git log --oneline -1                                        # on rule-signature-production, base 4f24abb
sha256sum runners/dsl/python/substrate_rs/_native.abi3.so   # 62e5cdc3...ca56f (unchanged)

# Part 1 AR2 — the powered before/after on the real production functions
systemd-run --scope --user -p MemoryMax=8G -p MemoryHigh=7G -- \
  python3 scripts/rule_signature_measure.py
# compare against the committed PRE_WIRING/POST_WIRING json snapshots

# Part 1 AR4 — regression, suite 1 (~12 min)
systemd-run --scope --user -p MemoryMax=8G -p MemoryHigh=7G -- \
  python3 -m pytest tests/test_acting_variant.py tests/test_structural_variant.py \
    tests/test_self_delta.py tests/test_gap_awareness_migrated.py \
    tests/test_self_concern_promote_migrated.py tests/test_agent_authors_new_rule_migrated.py \
    tests/test_composers_graph.py tests/test_experiment_composer.py -q
# expect: 14 failed (pre-existing cv2 class), 103 passed

# Part 2 — variation_ops.json bigram fix, regression suite 2 (~25 min)
systemd-run --scope --user -p MemoryMax=8G -p MemoryHigh=7G -- \
  python3 -m pytest tests/test_agent_authors_new_rule_migrated.py \
    tests/test_composer_capability_migrated.py tests/test_rule_literal_variation_migrated.py \
    tests/test_no_assistance_gate_migrated.py tests/test_residual_closure_migrated.py -q
# expect: 6 failed (pre-existing, unrelated timing/pump-loop failures), 44 passed

# Part 2 — A3/A4/A5/A6 investigation (~10 min)
systemd-run --scope --user -p MemoryMax=8G -p MemoryHigh=7G -- \
  python3 scripts/part2_site_investigation.py
# committed output: scripts/part2_site_investigation_results.json
```
