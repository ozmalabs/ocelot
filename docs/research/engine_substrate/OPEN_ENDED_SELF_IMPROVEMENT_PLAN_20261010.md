# Open-ended self-improvement: assessment and plan (2026-10-10)

## The question

Tranche 24 showed compounding self-improvement inside a space of changes that humans defined, judged by a criterion that humans defined. This plan asks whether the agent can extend both:

1. the space: author new kinds of change (variation families);
2. the criterion: judge whether a reply is appropriate, not merely error-free;

while noticing subtler failures, and without the loop gaining the ability to weaken its own standards.

## 1. Assessment

### 1.1 Operators: what kinds of change the agent can make

**Choosing a family is graph data. Executing one is Python.**

The `VariationOp` nodes and the `variation_pick` Program (`seeds/variation_ops.json`) choose a family by name. Each family then exists only because four Python sites know that name:
- a builder in `_VARIATION_REGISTRY` (`domains/reflective_faculty.py`, about lines 4862–4872, 5270);
- a per-family `if/elif` that wires the builder's report onto `SeedDelta` keys (5596–5745);
- per-family probe flags in the child replay (`scripts/convo_child_run.py` 599–608), plus family judges in `seeds/self_optimisation.json`;
- a per-family branch in `perform_adoptions`.

A `VariationOp` node the agent minted with a new name would build nothing.

**The ten builders reduce to about nine rule-JSON primitives:**
- copy and rename;
- remove;
- edit a literal at a path, either shifting it or setting it to an observed value;
- add a `where` conjunct (a guard, or `Not(…)`);
- drop a match edge or a conjunct;
- rewrite a field across the tree (flip a comparison, swap an `Attr` key);
- edit or append an effect;
- add a node or set a node attribute;
- instantiate a rule template.

The intelligence of each family lies in *site selection*: which rule, which guard, which literal. All of that is Python: `_pick_acting_rule`, `_guards_on`, the one-failing-guard search, `_find_where_lits`, and the `_DATUM_FEEDBACK_CANDIDATES` table.

**The pieces for a graph-native edit grammar exist but are not assembled:**
- The Rust Term dialect already has `FromJsonString`/`ToJsonString`, `RewriteTreeNodes`, `ListDrop`, attribute-key ranking and `MkDict`.
- `seeds/composer_experiment_graph.json` already authors rules from graph meta-rules, applying flip, swap and drop entirely in-graph. It is validated by parity with the Python oracle (`tests/test_experiment_composer_graph.py`).
- `domains/edit_ops.py` has Python appliers and a bounded one-edit enumerator (`enumerate_single_edit_candidates`), which is not used live.
- `SynthEnumerate` (Rust) synthesises value Terms from input/output examples. It has no rule-edit operations.

**Adoption is per-family.** The generic path only accepts "replace one rule with `<orig>_*`" or an ablation. Add-only rule sets, multiple replacements and node edits each needed a dedicated branch. A generic whole-delta adopt/revert does not exist.

### 1.2 Judge: what counts as an improvement

The child replay's only quality predicate is `_is_broken_reply` (empty, the error surface, or an exception), combined with string inequality against the control (`convo_child_run.py` 687–740):
- A flagged turn is "fixed" if its reply changed and is not broken. **"Got it" in answer to a question scores +1.**
- The `repaired` path (unflagged, in scope or previously erroring) waves through any non-error change.
- The parent's judge sees only the sign of score/frames.

Nothing checks speech-act fit, whether a question was answered, topic continuity or informativeness.

**Unused material for a better judge:**
- adjacency-pair data: `expects_response` edges in `seeds/conversation.json` and `adjacency_replied_act`;
- the probe's own inbound speech act, which the replay already reads;
- `data/corpus/persona_chat_20.json`, which holds each speaker's real next turn;
- human `reply_fix` flag notes, which state how the reply *should* work but are used only as "must change".

**No positive human signal exists.** Flags are negative only, so there is nothing to calibrate a judge against.

**Judges are protected, correctly.** They name `Experiment`/`SeedDelta`, so `improvement_integrity` excludes them from variation and adoption.

### 1.3 Concern supply: what the agent notices

Every automatic filer reads a mechanical datum:
- `explicit_error` or unhandled outcomes;
- shallow/deep reader divergence;
- latency;
- explicit-deficiency keywords.

A turn that released *any* reply files nothing. **No rule reads the interlocutor's next turn as feedback** on the agent's previous reply. That rules out: other-initiated repair ("what?", "huh?"), rejection ("that's not what I asked"), re-asking, topic abandonment and conversation ending.

Repair and correction dispositions are detected, but only replied to. `reported` concerns, the clearest human-voiced failures, are excluded from replay and are not self-promotable.

### 1.4 Safety: what stops the loop changing itself

- `improvement_integrity` blocks any *rule* that names a loop node type. It is a string match on rule JSON. `VariationOp` is protected, so a rule that authors families can never be adopted through the loop. That is the right default, and it is exactly the boundary this plan has to cross deliberately.
- **Integrity gap (verified):** the node-attribute delta path (`apply_node_attr_delta`, and the knob adoption branch) applies to any node type with **no protected-type filter**. A knob delta could set attributes on a `VariationOp`, `VariationPolicy` or `InstructionRetryPolicy` node. The current knob builder does not pick those types, but nothing prevents it. Concept/typed-node additions (`add_concepts`) also need checking.
- The adoption veto stack is sound and generic: `adopt_denied_on_regression` and `adopt_denied_on_overridden_verdict`.

## 2. Principles

1. **Three levels, each judged from outside itself.**
   - **L0, behaviour:** the current loop changes conversation rules.
   - **L1, operators:** the agent authors variation families.
   - **L2, criteria:** judges and concern filers.

   Each level is judged by a criterion it cannot modify. L0 is judged by the L2 judge. L1 is judged by a meta-evaluation on held-out concerns, using the same frozen L2 judge. L2 changes are only *proposed* by the agent and adopted by a human, validated against human-labelled data.
2. **Measure before trusting.** Every new judge and signal is first run report-only and calibrated against human labels before it gates anything.
3. **Parity before replacement.** Each step that moves machinery from Python to graph data must reproduce the existing behaviour byte-for-byte on recorded inputs before anything new is built on it.
4. **Every self-change stays a readable, revertible diff.** This includes agent-authored families.
5. **The graph decides, Python executes.** The edit grammar's primitives are mechanical. Which edit, on which rule, at which site is a graph Program.

## 3. Plan

The phases are ordered by dependency. Each has a preregistered gate. P0–P2 make the judge and the supply honest. P3–P4 make operators data. P5 is operator authorship. P6 is criterion proposals.

### P0. A quality measurement, report-only (1–2 tranches)

**Build:**
- **`ReplyQuality` v1, computed in the child replay and reported, not scored:**
  - **act fit:** the reply's act satisfies `expects_response(inbound act)`; a question answered by a receipt fails;
  - **question addressed:** an interrogative inbound gets an answer, an honest self-account, an ask-back or an explicit not-knowing, never a bare receipt;
  - **topic continuity:** content-word overlap with the inbound;
  - **error/none.**
- **A held-out labelled set:** about 300 turns from persona_chat dialogues *not* in the 120-turn stream. Each has the agent's reply plus a 3-way human label (appropriate / acceptable-minimal / inappropriate). The real next speaker's reply is kept as a reference.

**Gate Q0:** `ReplyQuality` agrees with the human labels at Cohen's κ ≥ 0.6, and `act fit` alone at precision ≥ 0.8 for "inappropriate".

**Also report:** the tranche 22–24 adoptions scored by `ReplyQuality`. This tells us honestly how many of the "fixes" are minimal receipts.

### P1. Judge v2 (human-authored, frozen; 1 tranche)

**Build:**
- The child result carries `quality_delta`, the variant's mean `ReplyQuality` minus the control's on the probes, and `quality_drops`, the number of turns whose quality decreased. Experiment ingest copies them, as it does `regressions`.
- `adoption_safety` v1.2 adds `adopt_denied_on_quality_drop`: deny when `quality_drops > 0` or `quality_delta < 0`.
- A flagged fix counts +1 only if its quality is at least acceptable-minimal. The `repaired` path requires quality not to decrease. A receipt for an interrogative inbound becomes a broken fix.
- The seed is frozen, and the rules name protected types, so they are outside the loop.

**Gate J1:** re-run the tranche-24 arms. Then:
- a constructed "receipt to questions" variant is denied;
- the statement-receipt adoptions are still adopted;
- error/none is still below the noreopen arm;
- 0 regressions.

### P2. Concern supply v2: the interlocutor's next turn (1–2 tranches)

**Build:** `seeds/reply_feedback_gap.json`, which files `SelfConcern{kind:'reply_quality'}` about the *previous* agent turn when the next interlocutor turn shows:
- other-initiated repair ("what?", "huh?", "I don't understand", a bare repeat);
- rejection or correction aimed at the agent's reply ("that's not what I asked", "no, I meant…");
- the same question asked again within k turns;
- an act mismatch recorded by `ReplyQuality` in production (P0).

Concerns are keyed by evidence class with a recurrence threshold, as `unanswered_gap` is. `reported` turns become concern *sources*, not just excluded probes.

**Self-promotion** of `reply_quality` is enabled only after P1, because a kind needs a judge that can tell success from receipt-ification.

**Gate S2:**
- On the held-out labelled set, filed concerns point at turns labelled inappropriate with precision ≥ 0.7.
- On a production run, concerns are filed for failures that were *not* errors.

**Also: post-adoption audit.** The same signals, measured on turns handled by an adopted rule, can trigger `revert_adoption` automatically. Production evidence, rather than replay, then closes the loop on mistakes.

### P3. One generic delta path, plus the integrity gap (1–2 tranches)

**Build:**
- `perform_adoptions` / `revert_adoption` gain a single **generic whole-delta** branch: any set of `add_rules`, `remove_rules`, `add_concepts`, `remove_concepts` and `set_node_attrs`, with the full original state captured on the `Adoption` record. The per-family branches become thin wrappers or are retired.
- The per-family child probes and judges become **declared witnesses** on the delta: `{witness_kind, direction}` data read by one generic judge. This replaces the per-family Python flags.
- **Fix the integrity gap:** `set_node_attrs` and `add_concepts` are filtered by `protected_node_types`, both in the child and at adoption.

**Gate G3:**
- every existing family test passes;
- the tranche 22–24 production runs reproduce their adoptions exactly;
- a constructed knob delta targeting `VariationPolicy` is denied.

### P4. The edit grammar and family programs as graph data (2–3 tranches)

**Build:**
- **Rule-edit Terms in Rust:**
  - `RuleView`: `FromJsonString` on `RuleSummary.rule_json`, plus path helpers;
  - `EditAt(rule, path, op, arg)`, with ops `set_lit`, `shift_lit`, `add_conjunct`, `drop_conjunct`, `relax_guard_to(observed)`, `append_effect`, `rename`;
  - `InstantiateTemplate(template, bindings)`.

  All are pure and deterministic, return `None` when inert, and never fabricate.
- **`FamilyProgram`:** a `VariationOp.builder_program` Term that takes the concern context (the concern's turn, its interpretation, held rules) and returns a delta value. A generic `_compose_from_program` interprets it. `_VARIATION_REGISTRY` remains as the fallback for families not yet ported.
- **Port `disposition_generalise` and `deep_reader_correct` first.** They are the two families that have produced production adoptions, and both are pure combinations of these primitives.

**Gate F4 (parity):** on every recorded concern from the tranche 22–24 runs, the ported programs produce deltas byte-identical to the Python builders, including abstaining on the same concerns. The tranche-24 production run then reproduces with the Python builders disabled for those two families.

### P5. Agent-authored families: operator authorship (3–4 tranches)

**Mechanism:**
- When a concern class is exhausted (`note_experiments_exhausted`), or a family abstains on recurring classes, the agent proposes **new FamilyPrograms**. It does this by bounded, MDL-ordered mutation and composition of held programs over the P4 grammar. Examples:
  - relax two guards instead of one;
  - choose the source rule by a different criterion;
  - route an interrogative class to a held faculty's reply rule instead of a receipt;
  - compose `deep_reader_correct`'s guard with `disposition_generalise`'s copy.

  `SynthEnumerate`'s enumeration discipline (bottom-up, MDL, observational-equivalence pruning) is the model, applied to programs over rule-edit ops.
- **Meta-evaluation, not the L0 judge alone:** a candidate family is run over a **held-out bank of concerns**, meaning recorded failing turns from *other* streams. Each resulting delta is judged by judge v2 in its own replay. The family qualifies only if all of these hold:
  - it fixes at least k concerns in the bank;
  - it has 0 regressions and 0 quality drops on all of them;
  - it fixes at least one class that no held family fixes.
- **Adoption of a family is a separate, frozen path.** A new seed, `operator_authorship`, contains the meta-evaluation and `FamilyAdoption` rules. It is listed in `_FROZEN_SEED_IDS` and names protected types, so the loop cannot vary it. An adopted family enters as `VariationOp{provenance:'agent_authored', probation:1}` with a priority penalty, and keeps its own `VariationCredit`. A family whose L0 trials then fail is retired by its credit.
- **Required human decision:** `improvement_integrity` currently forbids any loop-authored `VariationOp`. This phase needs a human to add a *narrow* exception: `VariationOp` nodes may be created by the frozen `operator_authorship` rules only, never edited by L0, and judges, concern filers and integrity rules stay forbidden. Per that seed's own description, editing this list is a human decision. Until then, P5 runs in **propose-only mode**: candidate families are evaluated and reported, never installed.

**Gates:**
- **A5a (propose-only):** on the remaining tranche-24 failure classes (interrogatives, short agreements), at least one agent-composed family qualifies on the held-out bank.
- **A5b (after the human decision):**
  - on a held-out stream, an agent-authored family is adopted and fixes concerns that a counterfactual arm with authorship off cannot fix;
  - judge v2 passes, with 0 harm and 0 machinery adoptions;
  - the family's program is readable as a diff.

### P6. Criteria: the agent proposes, humans adopt (2 tranches, open-ended)

**Build:** the agent proposes changes to `ReplyQuality` or concern filers as `CriterionProposal` nodes. Examples: a new act-fit pairing, a repair cue it observed preceding labelled failures. Each proposal carries its measured agreement with the human-labelled set, and with interlocutor-feedback signals, on held-out data.

**Adoption is human-only** (approve/deny), like the existing `ExtensionProposal` rung. The plan does not include autonomous criterion adoption. Whether it could ever be safe is an open research question, and the evidence this phase produces (proposal accuracy over time) is what would inform it.

**Gate C6:** at least one proposal improves agreement with held-out human labels and is approved. A proposal that would raise the loop's own success rate without raising human agreement is shown to be rejected by the measurement.

## 4. Invariants (checked at every gate)

- **I1.** No level is judged by a criterion it can modify.
- **I2.** No adoption, at any level, when regressions > 0, quality drops > 0, or the verdict was overridden. *Revised 2026-10-10 by human decision (P5b/P5c): harm is weighed, not vetoed. A regression is a change that is worse in the frame it is measured in. Adoption needs a weighed net of fixes against harm (`AdoptionWeighing`), and the overridden-verdict check stays. An authored family qualifies by beating its parent's net.*
- **I3.** No rule or delta that reads or writes protected types is adopted through L0 or L1. Node-attribute and typed-node deltas are covered too (from P3).
- **I4.** Every adoption records its full prior state and can be reverted. Post-adoption audit (P2) can revert automatically.
- **I5.** `improvement_integrity`, `adoption_safety`, the judges and `operator_authorship` are frozen. Their contents change only by human edit.
- **I6.** Every claim is preregistered, has an "off" arm, and is measured on held-out data the loop did not train on.

## 5. Risks

- **Goodhart on `ReplyQuality`.** The loop optimises whatever the judge measures. Mitigations: human-label calibration (P0), held-out evaluation, keeping the judge frozen (P1), and criterion changes only through humans (P6). Residual: act fit is a proxy, so the plan reports agreement, never "quality" as such.
- **Search cost.** Family enumeration grows combinatorially. Bounded MDL search plus held-out banks keeps it measurable. A meta-evaluation is many child replays, so the budget must be graph data with a cap.
- **The labelling dependency.** P0 and P6 need human labels: about 300 turns at first. This is the plan's main external cost.
- **The receipt ceiling.** Without faculties that can actually answer persona questions (self-account, preferences, ask-back), no operator can produce good answers. P5's interrogative target may reveal that the missing piece is a faculty, not an operator. That would itself be a useful, reportable finding.

## 6. Human decisions needed

1. **P0:** produce or approve the labelled held-out set, about 300 turns with a 3-way label.
2. **P1:** approve judge v2's quality veto as a frozen seed.
3. **P5:** whether to add the narrow `operator_authorship` exception to `improvement_integrity`. P5 runs propose-only until then.
4. **P6:** every criterion proposal.

## 7. First step

P0. Build `ReplyQuality` v1 report-only in the child replay and production, plus the labelling harness. Score the existing tranche 22–24 adoptions with it. This costs little, changes no behaviour, and answers the question every later phase depends on: how much of the current improvement is real.
