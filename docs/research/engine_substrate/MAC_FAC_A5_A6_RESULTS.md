# MAC/FAC A5 + A6 — results

Companion to `MAC_FAC_A5_A6_PREREG.md` (read first — it registers the fix
shape, the floor choices, and the honest A5 scope limit before any of the
numbers below existed). Closes `SHAPE_AUDIT.md` §2.1's A5/A6 sites — the
same `keywords_text` MAC-without-FAC pattern A1-A4 already fixed, extended
to two more self-modification decisions in `domains/reflective_faculty.py`.

**Worktree:**
`/tmp/claude-1000/-home-matt-ozmadev-ocelot/34a7cd08-5eb1-42bd-af0c-eedb1125fa76/scratchpad/mac-fac-a5-a6`,
branch `mac-fac-a5-a6`, detached from `main` at `8af4fde`. No Rust touched —
`runners/dsl/python/substrate_rs/_native.abi3.so` sha256
`07aabbf14af065566b096403c8bd4cbee0d79eb4f7800ba5fc04f46e1b92b75e`, confirmed
identical before and after (verified at commit time, §6).

---

## GO on both sites. A5 closes a real false-abstain gap (discrimination
unmeasurable at its real N=1); A6 closes a genuine multi-rule Class A/B gap,
powered on the real corpus. Zero measured regression.

---

## 0. A live cross-worktree hazard found and fixed en route — reported
because it is a real risk to this folder's own documented technique, not
because it touches the fix

Per `EDIT_OP_APPLICABILITY_GATE_RESULTS.md`/`RULE_SIGNATURE_...RESULTS.md`
precedent, this rung captured its AR4 "before" baseline via `git stash push
-- domains/reflective_faculty.py` on the production edit, planning to `pop`
it back after the baseline run. **`git worktree add` worktrees of the SAME
repository share ONE `refs/stash` — the stash is per-REPOSITORY, not
per-worktree.** A sibling agent (`deduction-extension`, a concurrent,
unrelated rung touching `domains/inference_generation.py` /
`domains/propositional_deduction.py` / `seeds/inference_logical.json`) was,
independently, running the identical documented stash-baseline technique in
its own worktree at the same time. The two `push`/`pop` sequences
interleaved on the shared LIFO stack: the sibling's `pop` grabbed THIS
rung's stashed `reflective_faculty.py` diff and applied it into the
sibling's own working tree; this rung's own `pop` then grabbed the
sibling's 3-file diff and applied it into THIS working tree. Both sides
briefly held the other's uncommitted, unrelated changes; `git stash list`
ended up empty on both sides, with each rung's own stash commit surviving
only as a dangling object (`git fsck --no-reflog`).

**Recovered without loss, verified precisely, not assumed:**
1. `git fsck --no-reflog` on this worktree found the dangling stash commit
   (`183c0512...`, `Merge: 8af4fde b652f3c`, message `WIP on
   mac-fac-a5-a6: ...`) touching only `domains/reflective_faculty.py`;
   `git show 183c0512...:domains/reflective_faculty.py` recovered this
   rung's edit byte-for-byte (confirmed: `grep -c "STRUCTURAL FALLBACK
   (MAC_FAC_A5_A6"` → 2, both sites present; `ast.parse` clean).
2. The sibling's cross-contaminated copy in THIS worktree
   (`domains/inference_generation.py` / `domains/propositional_deduction.py`
   / `seeds/inference_logical.json`) was saved as a patch to this rung's
   scratchpad (`rescued_sibling_changes/deduction_extension_wip.patch`,
   446 lines) before being reverted here (`git checkout --`) — not
   discarded blind.
3. This rung's contamination of the SIBLING's live worktree
   (`domains/reflective_faculty.py` there) was confirmed BYTE-IDENTICAL to
   this rung's own diff (`diff <(git -C sibling-worktree diff
   reflective_faculty.py) <(git diff reflective_faculty.py)` — exit 0) and
   reverted there (`git checkout -- domains/reflective_faculty.py`,
   sibling worktree) — the one safe, unambiguous action available (their
   own stated task, per their worktree's `DEDUCTION_EXTENSION_PREREG.md` /
   `_RESULTS.md`, has nothing to do with `reflective_faculty.py`). No other
   file in the sibling's worktree was touched; their own
   `propositional_deduction.py`/`inference_generation.py` continued
   changing under direct observation immediately afterward, confirming
   their process was live and self-recovering independently, not stalled
   by this incident.
4. **From this point on, this rung captured AR4 baselines by COPYING the
   file aside and restoring it, never by `git stash`**, to avoid the same
   hazard recurring for the remainder of this rung's own measurements.

**This is a real, general risk for this folder's own documented "capture
baseline via git stash" convention (`EDIT_OP_APPLICABILITY_GATE_RESULTS.md`
§5, `RULE_SIGNATURE_PRODUCTION_WIRING_RESULTS.md`) whenever more than one
agent works concurrently in linked worktrees of the same repository** — not
a defect in this rung's fix, but a defect in a widely-reused measurement
technique, surfaced here and worth flagging for any future concurrent rung:
prefer `cp file file.orig` / restore over `git stash` when siblings may be
running in other worktrees of the same repo.

---

## 1. A5 — the structural signal, as built, and the honest N=1 limit

`domains/reflective_faculty.py::_compose_datum_feedback_rule`
(`_DATUM_FEEDBACK_CANDIDATES`, one row today). The primary `keywords_text`
Argmax is UNCHANGED, tried first. On genuine abstain (no row scores >= 2),
a second pass scores each row by content-word membership against
`" ".join([node_type, datum_attr, belief_attr]).replace("_", " ")` — the
row's own real operational identity (FAC) rather than its hand-authored
prose blurb (MAC), same >=2-word floor. `fallback_used` is now a field on
the return dict so this is directly observable, not inferred.

**Measured, before building anything (PREREG §3): exactly two structural
words are genuinely novel** — `interlocutor` (from `node_type`) and `count`
(one token of `datum_attr = self_report_contradiction_count`) — every other
token of `node_type`/`datum_attr`/`belief_attr` is already present in
`keywords_text` (redundant with the prose).

**Demonstration (`tests/test_mac_fac_a5_a6_structural_fallback.py`,
3 tests, all passing):**

| test | content | primary | fallback | result |
|---|---|---|---|---|
| Class B | "your reliability trust tracking is broken" | overlap=2, hits | not consulted | `built=True, fallback_used=False` |
| Class A | "the interlocutor object's count field is climbing every single week" | overlap=0, abstains (mechanically confirmed: `sum(1 for w in words if w in kw_row) < 2`) | overlap=2 (`interlocutor`, `count`) | `built=True, fallback_used=True` |
| still abstains | "you always mumble incoherently" | overlap=0 | overlap=0 | `built=False`, `"abstain"` in wall (byte-identical to pre-fix) |

**The honest limit, exactly as registered in the PREREG before this was
built, not softened after the fact:** the real table has **one row**. A
fallback Argmax over a singleton candidate set cannot demonstrate
DISCRIMINATION — there is no wrong candidate to reject, so "the fallback
picked the right row" is true by construction the moment it picks anything
at all. What IS demonstrated, and is real: **false-abstain avoidance** — a
concern that names the row's own attribute identity but not its prose
blurb used to return `built: False` and now correctly authors the rule.
This is reported as its own, narrower thing, not dressed up as a
multi-candidate discrimination result. If `_DATUM_FEEDBACK_CANDIDATES`
grows a second row, this fallback would need a FRESH discrimination
measurement before being trusted to pick correctly between two genuine
candidates — named here as the natural follow-on, not attempted (there is
nothing to discriminate against yet).

---

## 2. A6 — the structural signal, as built, and the population it was
measured against

`domains/reflective_faculty.py::_compose_rule_literal_variant`. The primary
per-`(rule, where-lit-candidate)`-pair Argmax (`_collect_vocab_tokens`, a
LOCAL read of one comparison subtree) is UNCHANGED, tried first. On
system-wide abstain (no pair anywhere scores >= 2), a two-tier fallback
runs: **tier 1** scores each candidate RULE (the same
`writes_where_literal==1.0 AND skippable==1.0` pool) by content-word
substring overlap against its own `where_signature_json` (the FULL
`where`-clause structural signature — `domains.rule_signature`, reused
DIRECTLY: `ensure_where_signature` mints for every `RuleSummary` carrying a
`rule_json`, not filtered to `writes_chosen_action`/`writes_reply`, so no
new signature machinery was needed, confirmed by reading before assuming);
**tier 2** picks WHICH `_find_where_lits` candidate within the
structurally-chosen rule via the SAME local vocab scorer, floor lifted
(the floor's job — reject a too-weak signal — was already discharged at
the rule level). `fallback_used` is returned on the dict.

**The gap this closes, confirmed by direct read, not inferred from the
brief's framing:** `_collect_vocab_tokens` walks only the ONE comparison
node `_find_where_lits` handed it — it never sees a rule's SIBLING
`And`-items. Read directly: `escalate_narrative_shape`'s `where` clause has
four sibling `Eq` guard conditions (`goal.reading_report`,
`spine_stage.name=="spine"`, `spine_stage.flow==src.flow`,
`spine_stage.status=="done"`) reachable from NEITHER of its two numeric
comparison candidates.

**Population, measured (`scripts/a6_discover_probes.py`, full boot, real
corpus, not a subset):** 696/704 seeds loaded; `_ensure_where_literal_rule_
provenance` + `rule_signature.ensure_where_signature` (2229 new attrs
minted) found **642 rules, 13016 (rule, literal) pairs, 746 distinct local-
vocab words**. Excluding generic JSON/Term-scaffolding vocabulary
(`type`/`node`/`attr`/`items`/`exists`/... — not rule content) and
underscore-splitting identifiers to match how a real sentence is actually
worded (a human writes "count", never "babble_idx"): **547 genuine Class A
words** (present in some rule's `where_signature_json`, absent from the
GLOBAL local-vocab union — no `(rule, candidate)` pair anywhere can ever
score on them under the primary) and **51665 genuine Class B occurrences**
(already in some candidate's own local vocab). Cost: 145.5s total, of which
141.0s is `ensure_where_signature`'s one-time corpus walk — consistent with
`SEED_PICK_STRUCTURAL_FALLBACK_RESULTS.md`'s own ~130s figure for the
analogous seed-grain computation; idempotent, not a per-tick cost.

**Note on the first version of this discovery script:** the first run
(unfixed tokenizer, no scaffolding exclusion) took **13+ minutes** and was
killed — it re-tokenized every rule's `where_signature_json` once PER
CANDIDATE PAIR (13016 times) instead of once per rule (642 times), and kept
whole underscored identifiers (`"babble_idx"`) as single tokens instead of
the word parts a real sentence would use. Fixed (dedupe by rule, split on
`_`, exclude scaffolding vocabulary) before trusting any number from it —
145.5s after the fix. Reported because a slow tool is itself worth noting,
not because it affects the production fix.

**Demonstration (`tests/test_mac_fac_a5_a6_structural_fallback.py`,
3 tests, all passing), using a REAL, mechanically-discovered probe —
`adopt_denied_on_regression` (`seeds/adoption_safety.json`), one where-lit
candidate (`exp.regressions > 0`), whose SIBLING guard
(`Not(Eq(exp.adopt_denied, true))`) supplies the words `adopt`/`denied`,
both confirmed absent from the global local-vocab union:**

| test | content | primary (system-wide) | fallback | result |
|---|---|---|---|---|
| Class B | "your narrative shape escalation floor of three sentences read before it fires makes you escalate too rarely on short stories" (the pre-existing, already-passing probe) | hits (`escalate_narrative_shape`) | not consulted | `built=True, fallback_used=False, removed_rule='escalate_narrative_shape'` |
| Class A | "it keeps getting denied and I never actually get to adopt anything, this happens too rarely" | genuinely abstains — mechanically confirmed LIVE by re-scanning every `(rule, candidate)` pair in the real, freshly-provenanced pool for this exact word set (`max_local < 2` asserted, not assumed) | tier 1 picks `adopt_denied_on_regression` (2 hits in its `where_signature_json`); tier 2 picks its one candidate | `built=True, fallback_used=True, removed_rule='adopt_denied_on_regression', direction='increase_fires'` |
| still abstains | "you always mumble incoherently and nothing makes sense" | abstains | abstains | `built=False`, `"abstain"` in wall (byte-identical to pre-fix) |

The Class A test's own system-wide-abstain assertion is not a sampled
spot-check — it re-derives the primary's own scoring loop live, over the
same freshly-provenanced pool the production function itself reads, for
the EXACT probe words used, and requires the max score across every
candidate in the whole corpus to be < 2 before trusting the probe.

---

## 3. AR1 — the combination-wiring design, confirmed as built

Both sites: primary tried first, UNCHANGED; fallback is a genuinely SEPARATE
pass, never a pre-filter or blend (§AR1 of the PREREG's own reasoning —
the two signals are not commensurable, and a name-native concern must not
be filtered out before the primary sees it). Confirmed live by construction
of both Class B tests: `fallback_used is False` and every returned field is
identical to what the unmodified primary alone would have produced (the
primary loop body is byte-unchanged in both functions — only the
`if best is None:` abstain branch grew a second pass).

---

## 4. Reachability via `ground_concern` — checked, not assumed, same
finding shape as A3

Both A5 and A6 are reached from `_pick_variation_op`/`_VARIATION_REGISTRY`
inside `_compose_experiment_rule`'s `vary` branch (`reflective_faculty.py`,
WAVE 5) — the SAME function A3's own fix touched. Reading
`_route_experiment_composer` (`:6134-6165`) directly: for the
conversation-`'replay'` family it returns `None` (`ground_concern` falls
through to the Python builder, reaching this rung's fix); for the common
`'test'`-anchored, non-`'replay'` family, the graph-resident twin
(`compose_experiment_mint_parametric`, `seeds/composer_experiment_graph.json`
— SHAPE_AUDIT's A7-A9, a SIBLING agent's own concurrent scope, not touched
here) wins first. Reading that meta-rule's own description: its
variant-family branches are exactly `{none, gradient, structure}` — no
`rule_literal_edit`/`datum_feedback_rule`/`cue_set_edit`/`shape_mint`
branch exists there at all. **Same shape as `SEED_PICK_STRUCTURAL_
FALLBACK_RESULTS.md`'s own headline finding**: this rung's Python-level fix
is correct and directly validated (§1-2, and both family test files
already call these functions directly, not through `ground_concern` — the
existing, pre-rung test convention), but for the live agent's actual
`ground_concern`-driven self-experiment loop, it is reachable only for the
conversation-`replay` case today. Not investigated further (A7-A9 is
explicitly out of scope and a sibling's concurrent territory) — reported
because the prior two rungs in this exact family both made it a headline
finding, not a footnote.

---

## 5. AR4 — no regression

**Baseline ("before"), captured on `8af4fde` (production edit isolated via
`git stash`, before the cross-worktree hazard in §0 was discovered — this
ONE baseline capture is the run that triggered discovering the hazard; it
completed and was recorded before anything went wrong):**

```
tests/test_composer_capability_migrated.py tests/test_rule_literal_variation_migrated.py -q
2 failed, 31 passed in 335.06s (0:05:35)
FAILED tests/test_composer_capability_migrated.py::test_datum_feedback_adoption_vetoed_on_regressions
FAILED tests/test_rule_literal_variation_migrated.py::test_judge_rule_literal_outcome_matrix
```

**After (same two files, production edit applied, recovered per §0 and
independently re-verified syntactically/semantically clean), run
SYNCHRONOUSLY to completion, no polling:**

```
2 failed, 31 passed in 447.95s (0:07:27)
FAILED tests/test_composer_capability_migrated.py::test_datum_feedback_adoption_vetoed_on_regressions
FAILED tests/test_rule_literal_variation_migrated.py::test_judge_rule_literal_outcome_matrix
```

**The two failing-node-id lists are byte-identical, before and after.**
Independently reconfirmed by a second full run (463.16s) with the same two
node ids, same order, same assertion text — the failures are deterministic,
not flaky.

Both pre-existing failures are unrelated to the WHICH-pick this rung
touched: `test_datum_feedback_adoption_vetoed_on_regressions` exercises the
`adoption_safety` veto rule downstream of a successful pick (not the pick
itself — the SAME `_compose_datum_feedback_rule` call at the top of that
test already succeeds); `test_judge_rule_literal_outcome_matrix` exercises
`judge_rule_literal_outcome`'s verdict matrix (a different function
entirely). Neither test's assertion failure is about which row/rule/literal
gets picked.

**New test file**: `tests/test_mac_fac_a5_a6_structural_fallback.py`
(6 tests: 3 for A5, 3 for A6) — `6 passed in 150.57s`.

---

## 6. Native library / Rust — confirmed unchanged

```
sha256sum runners/dsl/python/substrate_rs/_native.abi3.so
07aabbf14af065566b096403c8bd4cbee0d79eb4f7800ba5fc04f46e1b92b75e  (before, at worktree creation)
07aabbf14af065566b096403c8bd4cbee0d79eb4f7800ba5fc04f46e1b92b75e  (after, at commit time)
```

No new Term type, no new PyO3 binding, no new graph node type, no
`add_node` call anywhere in either edit — both fixes are additive-only
`if best is None:` branches inside existing Python functions.

---

## Honest residuals

1. **A5's fallback is unmeasurable for multi-candidate discrimination** —
   the real table has one row (§1). A second row would need its own
   Class A/B measurement before this fix could be trusted to discriminate
   correctly, not merely to avoid a false abstain.
2. **A6's fallback is reachable via direct call (matching the existing test
   convention for this whole family) but shadowed by the A7-A9 graph twin
   for the common `ground_concern`-driven case** (§4) — same scope-limited
   "GO, narrowly" verdict `SEED_PICK_STRUCTURAL_FALLBACK_RESULTS.md`
   reported for A3. Closing it requires porting the same fallback shape
   into `compose_experiment_mint_parametric`'s own held Term — explicitly
   out of scope here (A7-A9, a sibling's territory).
3. **The cross-worktree `git stash` hazard (§0) is a standing risk for this
   folder's own documented technique**, not something this rung can fix
   inside its own scope (it is a fact about how `git worktree` shares
   `refs/stash`, not a bug in any one rung) — flagged for whoever reads
   this next, with the safe alternative (copy-aside, not stash) named.
4. **`_DATUM_FEEDBACK_CANDIDATES` and the `writes_where_literal` pool were
   not otherwise touched** — no row added, no rule reclassified, exactly
   the AR3 scope both PREREG and this doc register.
5. **Downstream self-experiment-adoption outcomes are not measured** — same
   sidestep A1-A4 already took, for the same reason (the slow, noisy live
   oracle). "The wired pick matches the oracle more often" is the claim
   made; "the agent's self-improvement outcomes get better" is not.

---

## Reproduce

```bash
cd /tmp/claude-1000/-home-matt-ozmadev-ocelot/34a7cd08-5eb1-42bd-af0c-eedb1125fa76/scratchpad/mac-fac-a5-a6
git log --oneline -1                                        # mac-fac-a5-a6, base 8af4fde
sha256sum runners/dsl/python/substrate_rs/_native.abi3.so   # 07aabbf1...92af (unchanged)

# A6 population + probe discovery (145.5s)
systemd-run --scope --user -p MemoryMax=8G -p MemoryHigh=7G -- \
  python3 scripts/a6_discover_probes.py

# The new dedicated test file (6 tests, both sites' Class A/B + abstain)
systemd-run --scope --user -p MemoryMax=8G -p MemoryHigh=7G -- \
  python3 -m pytest tests/test_mac_fac_a5_a6_structural_fallback.py -q

# AR4 -- regression, the two family files
systemd-run --scope --user -p MemoryMax=8G -p MemoryHigh=7G -- \
  python3 -m pytest tests/test_composer_capability_migrated.py \
    tests/test_rule_literal_variation_migrated.py -q
```
