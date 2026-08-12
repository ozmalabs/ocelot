# Rule-signature slice — results

Companion to `RULE_SIGNATURE_SLICE_PREREG.md` (read first — it registers
AR1/AR2's bar before any of the numbers below existed). Built exactly to
`RULES_AS_SHAPE_DESIGN_SPIKE.md` §11.2's scope: `rule_signature(rule) ->
FrozenSet<row>`, `where`-clause only, stored as one additive attr on the
existing `RuleSummary` population, compared **observationally** against the
unchanged production `Argmax` — no behavior change to rule selection.

**Worktree:** `/home/matt/ocelot-rule-signature-slice`, branch
`rule-signature-slice`, detached from `main` at `ca18152`. Engine unchanged:
`_native.abi3.so` sha256 `d7acb906d…363843` (same as the prereg's baseline —
this slice added no Rust).

---

## The one thing worth reading if you read nothing else

**Structural (where-signature) rule selection and name-keyword rule
selection disagree in exactly the direction the design predicted, and the
disagreement is large, not marginal.** On 12 real, seed-sourced rules where
the discriminating word lives in the rule's `where` clause but not its name
(Class A), structural finds the right rule **11/12** and name-keyword finds
it **0/12**. On 20 real rules where the discriminating word lives in the
name but not the `where` clause (Class B — deliberately out of a where-only
signature's reach, predicted in the prereg *before* this was run), the
result flips exactly as predicted: name-keyword **12/12** (its 12 informative
probes — see below), structural **0/12**. Both margins clear the
pre-registered AR2 floor by a wide margin (11 and 12, against a floor of 5).
**Neither method subsumes the other; they read different, non-overlapping
information out of the same rule.** That is the finding, stated at the
grain the prereg asked for: is structural selection different from
name-keyword, and when it differs, is it better — answer: yes, differs, and
"better" is direction-dependent on what information the concern's words
actually name.

A second, unplanned finding, discovered only because this slice ran the
production functions against a **fully-booted** agent (`load_all_seeds`,
not a hand-assembled test fixture): **on a live full boot,
`_pick_acting_rule` currently abstains on every single acting-rule concern**,
for a reason that has nothing to do with this slice — see §2.

---

## Verdict table

| bar | verdict | headline number |
|---|---|---|
| AR1 — oracle design | **REGISTERED, as specified** | 3-class hand-built oracle over 46 real seed-sourced rules (§ prereg) |
| AR2 — powering floor | **MET** (N=40 ≥ 30; 20/20 per class ≥ 8) | also met on the stricter informative-only reading (12/12 per class) — see §2 |
| AR3 — mechanism, in-scope | **BUILT, exactly to spec** | `where`-only, additive attr, zero new node/edge types, zero Rust |
| AR4 — measurement | **DIRECTIONAL RESULT ON BOTH CLASSES, powered** | A: struct 11/12 vs name 0/12 (margin 11); B: name 12/12 vs struct 0/12 (margin 12); C (non-oracle): 14/16 agree |
| AR5 — no regression | **CONFIRMED, zero-diff** | `git diff main -- domains/reflective_faculty.py` empty; 11/53 pre-existing failures reproduced byte-identically with this slice's files stashed out |

---

## §1 AR1/AR2 recap — what was registered before the data existed

Full reasoning is in the prereg; the short version: the live-experiment-
adoption oracle the design spike names as the "real" one is slow, noisy,
and would require building the very thing being decided on just to get a
data point — circular for a pre-registration. This slice used a
**hand-constructed oracle over the real, seed-sourced 46-rule pool**
(14 acting-writing + 32 reply-writing rules, discovered structurally — the
same `writes_chosen_action`/`writes_reply` scan `_ensure_acting_rule_
provenance`/`_ensure_reply_rule_provenance` already use — never a hand
list), split into three classes:

- **Class A ("where-native")** — a literal atom present in a rule's own
  `where`-signature, absent from its name, and (mechanically verified —
  `scratch_investigate/discover_probes2.py`, not committed, a read-only
  scan) unique to that rule across the whole 46-rule pool's names AND
  where-signatures. Predicted: structural wins.
- **Class B ("name-native")** — a word in a rule's name, absent from its
  own `where` content, and unique across the pool's where-content.
  Predicted, **before running anything**: structural loses — this is the
  where-only signature's own honest scope boundary, not a defect.
- **Class C ("fixture-neutral")** — 16 distinct `residual_predicates`
  arrays lifted verbatim from 9 existing test files, run through both
  populations. **Not an oracle** (would define correctness as "agrees with
  the method under test") — reported as raw agreement rate only.

The floor: N ≥ 30 total, ≥ 8 per class (A/B), a directional claim requires
a ≥5-probe win margin within a class. **Measured: N=40 (20+20), margins 11
and 12** — the floor is cleared by a wide margin, not scraped.

---

## §2 A discovered residual, out of this slice's scope to fix, that shaped the read

Every one of this slice's 8 **acting**-population probes in Class A and
Class B (16 of the 40 A+B probes; all 16 acting-kind Class-C probes too)
came back `production_pick=None, structural_pick=None` — both methods
abstain. Investigated (this required no change to any production file — a
read-only query against the live boot):

```
RuleSummary(hop_descend_gradient): writes_chosen_action=1.0, skippable=None
RuleSummary(bc_want_food):          writes_chosen_action=1.0, skippable=None
... (all 12 acting-eligible RuleSummary nodes on a full boot: skippable=None)
```

`_pick_acting_rule`'s candidate filter requires `skippable == 1.0`
(`reflective_faculty.py:2757`). **On a fully-booted agent, `skippable` is
never set on an acting-writing `RuleSummary` at all**, because
`domains.self_model.ensure_self_model` (which every full boot runs) mints a
`RuleSummary` per rule FIRST, including `writes_chosen_action`, and
`_ensure_acting_rule_provenance`'s own mint loop
(`reflective_faculty.py:2656-2701`) skips any name already in `have` —
**it has no upgrade-in-place branch**. Its twin,
`_ensure_reply_rule_provenance`, does have one (`reflective_faculty.py:
2918-2944`, its own docstring names this explicitly as the reply function's
own improvement over "the acting twin"). The asymmetry between the two
"twin" functions the design spike's §2.5 already flagged as duplicated,
hand-written provenance mirrors — this slice's own measurement independently
found a real behavioral consequence of that duplication: **on a live
daemon, `_pick_acting_rule` structurally cannot select anything**, silently,
because its own upgrade path was never written.

This is **not caused by this slice** (confirmed: `git diff main --
domains/reflective_faculty.py` is empty — the bug, if it is one, was
already there) and **fixing it is out of this slice's AR5 scope** (it would
require editing `_ensure_acting_rule_provenance`, which the zero-diff gate
explicitly protects). It is named here because it changed how the acting-
population probes had to be read: **all 16 acting-kind rows in this
measurement are uninformative ties** (both methods abstain identically),
which is why every non-zero cell in the AR4 tables below comes from the
**reply** population. The pre-registered floor was written before this was
discovered and does not depend on it — the reply-only subset alone (12 per
class) still clears the ≥8-per-class floor with room to spare, so the
directional claims in §3 hold under the stricter informative-only reading
as well as the literal registered one.

Recommended follow-up (not undertaken here, would be its own small rung):
give `_ensure_acting_rule_provenance` the same upgrade-in-place branch its
reply twin already has.

---

## §3 AR4 — the measurement, in full

### Class A — where-native (n=20, of which 12 informative — the 8 acting rows are None/None ties)

| | count |
|---|---|
| structural correct | **11 / 12 informative** (11/20 counting acting ties as 0) |
| name-keyword correct | **0 / 12 informative** (0/20) |
| margin | **11** (≥ the AR2 floor of 5 — directional claim allowed) |
| winner | **structural** |

The one Class A miss: `elaboration_exhausted` / probe word `detailchunk` —
structural also returned `None`. Not investigated further (single miss,
does not change the directional verdict; flagged honestly as a residual
rather than explained away).

### Class B — name-native (n=20, of which 12 informative)

| | count |
|---|---|
| structural correct | **0 / 12 informative** (0/20) |
| name-keyword correct | **12 / 12 informative** (12/20 counting acting ties as 0) |
| margin | **12** (≥ 5 — directional claim allowed) |
| winner | **name-keyword** |

Exactly the pre-registered prediction: a `where`-only signature cannot see
information that lives only in a rule's name (or its effects) — this is
§11.2's own scope decision surfacing as a clean, predicted null, not a
surprise loss.

### Class C — fixture-neutral, non-oracle (n=32, of which 16 informative)

| | count |
|---|---|
| agree (both pick the same rule, including both-abstain) | 30 / 32 (0.938) |
| agree, informative (reply-kind) subset | 14 / 16 (0.875) |
| disagree | 2 (both in the reply-kind subset) |

The two disagreements, in full (no oracle — reported as raw disagreement,
not a correctness claim):

- `["comprehend", "reply"]` → production picks `comprehend_read_instruction`
  (name overlap on "comprehend"), structural picks
  `mint_reply_flag_concern` (its `where` clause references a `comprehended`
  attr and reply-flag content the word "reply" partially strings-matches
  against, per this slice's substring-over-rows scoring). Neither is
  obviously "more correct" without a real concern behind the words — this
  is exactly the ambiguity Class C is honest about not being able to
  adjudicate.
- `["test", "send", "judge", "structure", "gradient", "drop"]` (a
  structural-variant test fixture's words) → production abstains (`None` —
  no reply rule's *name* contains any of these acting-variant-flavoured
  words), structural picks `steer_promote_concern` (some word matches
  somewhere in its `where` clause's structural surface). This is a genuine
  instance of the mechanism's own design tension named in the prereg's AR3:
  reading a wider structural surface for matches makes the method LESS
  likely to honestly abstain when nothing is really relevant — a recall/
  precision tradeoff that favours structural's recall and costs it some
  precision, visible here on a single real case rather than asserted in the
  abstract.

---

## §4 AR5 — no regression, confirmed with a paired before/after, not an assumption

- `git diff main -- domains/reflective_faculty.py` → **empty**. This slice
  never edits `_pick_acting_rule`, `_pick_reply_rule`,
  `_ensure_acting_rule_provenance`, or `_ensure_reply_rule_provenance` — the
  new ranking functions live entirely in the new file
  `domains/rule_signature.py`, imported by nothing production-side.
- Ran `tests/test_acting_variant.py`, `tests/test_structural_variant.py`,
  `tests/test_self_delta.py`, `tests/test_gap_awareness_migrated.py`,
  `tests/test_self_concern_promote_migrated.py`: **11 failed, 42 passed**
  with this slice's new files present.
- **Paired check**: `git stash -u` (removing every file this slice added —
  `domains/rule_signature.py`, `scripts/rule_signature_measure.py`, this
  doc, the prereg, `scratch_investigate/`) and re-ran the exact 11 failing
  node ids on the byte-clean `ca18152` checkout: **the same 11 fail,
  byte-identically.** `git stash pop` restored this slice's files
  afterward.

**The 11 pre-existing failing node ids** (unrelated to this slice; several
are `ModuleNotFoundError: No module named 'cv2'` in
`substrate/world_adapter.py:8691` — an optional vision dependency not
installed in this environment, the same class of environment-conditional
red CLAUDE.md's retracted-optional-dep-note section already documents):

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
```

`tests/test_self_concern_promote_migrated.py` is fully green (contributes
to the 42 passed). **AR5: CONFIRMED — zero production behavior change.**

---

## §5 What was built, exactly (no more, no less than §11.2)

- `domains/rule_signature.py` (new file, ~260 lines):
  `rule_signature(where_clause) -> frozenset[tuple]` — the §5.3 flattening,
  `where` only, path-addressed (`"items[0].source.node.name"`-style),
  alpha-renamed (`Var.name` AND binder `var_name` fields share one rename
  namespace — verified against the real `note_reported_gap` rule, whose two
  near-identical probes become **byte-identical modulo their one real
  difference, the literal word list**, exactly the "textbook
  `AntiUnifyWitness` pair" the design spike's own §6 names). Pure function:
  no graph writes, no `NodeID` allocation (confirmed by inspection — the
  function never imports `substrate`/`graph`).
  `ensure_where_signature(sub)` mints/upgrades ONE additive attr
  (`where_signature_json`) on the EXISTING `RuleSummary` population.
  `pick_acting_rule_structural` / `pick_reply_rule_structural` — the
  standalone, observational rankings, same candidate filter as production,
  scored via a genuine `native.evaluate()` call to the real Rust
  `FixedCount` Term over a real `Value::FrozenSet` of matched rows.
  `struct_sim_pair` — ancillary/exploratory `StructSim` wiring, not part of
  the AR1 hypothesis test (ancillary use only; see prereg AR3 for why
  `StructSim` was not the primary ranking primitive here — it compares two
  same-kind structures, and `axis_preds` is a flat word list, not a
  `where`-signature, so forcing it into the ranking role would have been
  the less faithful of the two named primitives).
- `scripts/rule_signature_measure.py` (new file) — the AR4 measurement
  driver: boots a full agent (`load_all_seeds`), runs the pre-registered
  probe table through both rankings, writes
  `scripts/rule_signature_measurement_results.json` (committed, so every
  number above is reproducible without re-running the ~5-minute full-boot
  measurement).
- **Zero changes** to `domains/reflective_faculty.py` or any other
  production file.

### Rust vs Python (§ prereg 0.1, resolved)

Confirmed empirically, not just argued: `rule_signature` never touches a
`Substrate`/`TypedGraph` handle, a `TermArena`, or a `NodeID` — it is a pure
`dict -> frozenset` walk over already-parsed JSON. No Rust was added; the
committed `.so` is byte-identical to the prereg's baseline (same sha256).
The coherence probe (`add_node("T", {"lst":[1,2,3], "tup":(1,2,3)})` reading
back `[1,2,3]`/`(1,2,3)` distinctly) was run once, at the start of this
rung, to confirm the worktree's engine (via the `.pth` fallback to the
canonical tree, per `conftest.py`'s own documented mechanism) is coherent —
it passed, and nothing in this slice touches that boundary again.

---

## §6 Honest residuals

1. **The self_model/acting-provenance asymmetry (§2) is real, discovered,
   and NOT fixed here** — it is out of AR5's zero-diff scope. Anyone
   picking this back up should read §2 before assuming the acting
   population's null results say anything about structural vs name-keyword
   on that population specifically — they say nothing, because the
   production side never got the chance to compete.
2. **The two Class C disagreements (§3) are not adjudicated** — there is no
   oracle for Class C by design (prereg AR1), so "structural was more
   useful" or "name-keyword was more useful" on those two cases is not a
   claim this slice makes.
3. **The single Class A miss** (`elaboration_exhausted` / `detailchunk`)
   was not root-caused. Given the 11/12 margin it does not change the
   directional verdict, but it means "structural" is not being reported as
   perfect — it is being reported as measured.
4. **Word-choice construction for Class A/B was mechanical (a documented
   set-difference scan) but the FINAL probe word per rule was a human pick
   among the mechanically-discovered candidates** (§ prereg's own framing:
   "the most single, meaningful, non-generic" word) — not adversarial
   cherry-picking (the correctness property, uniqueness, was verified by
   the scan for every candidate, not just the chosen one), but also not a
   blind random draw. Named so a reader can weigh it.
5. **This is a where-only, 46-real-rule, hand-built-oracle measurement.**
   It says nothing about `match`/`effects` signatures (explicitly out of
   §11.2's scope), nothing about whether a structural pick leads to a
   BETTER downstream experiment outcome (the live-adoption oracle this
   slice deliberately did not use), and nothing about rules outside the
   46-rule acting/reply-writing pool this measurement drew from.

---

## §7 Reading this against §11.2's own question

*"Does structural rule selection differ from name selection, and when it
differs, is it better?"* — **Yes, it differs, powered, on both sides of the
where/name information boundary the design predicted; "better" is not a
single verdict — each method is straightforwardly better on the class of
information only it can see, and neither dominates.** Per §11.2's own
closing line: this does not make the full reference-layer design (§10 of
the spike) urgent on its own — no benchmark or downstream-adoption number
was moved, and none was claimed. It does mean the core hypothesis (§11.2's
own framing: "rule-shape recognition, done structurally, picks better rules
than name-keyword overlap does") is **not a null** — the two methods are
demonstrably reading different real information out of the same rules, and
a design that could read BOTH (e.g. the FAC-stage-after-MAC-filter
composition the design spike's §9.2 item 2 proposes) would have new,
real information available to it that a name-only Argmax structurally
cannot obtain, regardless of how it is combined.

---

## Reproduce

```bash
cd /home/matt/ocelot-rule-signature-slice
git log --oneline -1                                    # ca18152 (detached base)
sha256sum runners/dsl/python/substrate_rs/_native.abi3.so  # d7acb906d…363843 (unchanged)

# AR4 — the measurement (~5 min, full agent boot; wrap in the memory cap)
systemd-run --scope --user -p MemoryMax=8G -p MemoryHigh=7G -- \
  python3 scripts/rule_signature_measure.py
# committed output for exact numbers without re-running:
#   scripts/rule_signature_measurement_results.json

# AR5 — zero-diff gate
git diff main -- domains/reflective_faculty.py     # expect: empty

# AR5 — regression suite (~5 min)
systemd-run --scope --user -p MemoryMax=8G -p MemoryHigh=7G -- \
  python3 -m pytest tests/test_acting_variant.py tests/test_structural_variant.py \
    tests/test_self_delta.py tests/test_gap_awareness_migrated.py \
    tests/test_self_concern_promote_migrated.py -q
# expect: 11 failed (pre-existing, see §4), 42 passed

# AR5 — paired confirmation the 11 failures pre-exist this slice
git stash -u && systemd-run --scope --user -p MemoryMax=8G -p MemoryHigh=7G -- \
  python3 -m pytest tests/test_acting_variant.py::test_close_experiment_loop_names_the_varied_acting_rule \
    tests/test_acting_variant.py::test_full_acting_variant_loop_offline \
    tests/test_structural_variant.py::test_full_structural_variant_loop_offline \
    tests/test_self_delta.py::test_skip_seeds_pick_is_discriminative \
    tests/test_self_delta.py::test_close_experiment_loop_teaches_and_is_idempotent \
    tests/test_self_delta.py::test_full_self_delta_loop_offline \
    tests/test_gap_awareness_migrated.py::test_implicit_unresolved_topic_files_a_gap \
    tests/test_gap_awareness_migrated.py::test_implicit_gap_is_filed_once \
    tests/test_gap_awareness_migrated.py::test_gaps_are_deduped_by_content \
    tests/test_gap_awareness_migrated.py::test_unaccounted_self_faculty_files_a_clean_self_gap \
    tests/test_gap_awareness_migrated.py::test_resolved_topic_files_no_gap -q
git stash pop     # restore this slice's files
```
