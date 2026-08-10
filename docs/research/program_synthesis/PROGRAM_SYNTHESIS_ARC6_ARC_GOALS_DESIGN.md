# ARC 6 — ARC-GRAIN GOAL MINTING: DESIGN (phase 1, nothing wired)

**Date:** 2026-08-03
**Status:** DESIGN ONLY. No existing file touched. No seed installed. Nothing measured.
**Precursor:** `PROGRAM_SYNTHESIS_ARC6_GOAL_RESIDUALS.md` §9 —
*"arc-planning goals are not yet minted as graph data, so there is no live
arc-grain collapse for these six to steer."*
**Corrected by:** `PROGRAM_SYNTHESIS_ARC6_COHERENCE.md` (the row-verdict residual
is stale as shipped — which turns out to be this design's best mint source).

**Scaffolding (new files only, deliberately NOT in a loaded directory):**

| file | what | why not in place |
|---|---|---|
| `drafts/arc_goals/arc_goals.draft.json` | the seed, drafted in full | `substrate/boot_all.py::_read_seeds` **globs `seeds/*.json`** and installs every match at boot. A file dropped in `seeds/` is live immediately — it would perturb the running sweep, and `test_arc6_tier0_migrated.py::test_no_python_decision_was_added` asserts `git status --porcelain domains seeds` is empty, so an untracked file there reds a gate that is not this rung's to move. |
| `drafts/arc_goals/test_arc_goals_draft.py` | the gate scaffold | `pytest tests/ -k migrated` is live; a new file under `tests/` risks collection mid-run. Not named `*_migrated.py` and not under `tests/`. |

Phase-2 activation is a file-move plus the four existing-file edits enumerated in
§11. **Every one of those is listed with its blast radius**, because two of them
change gates that currently pass.

---

## 1. The problem, and the boundary it sits on

Every arc-planning decision in arc 6 — kill S3, kill seam C at its ceiling, judge
seam B not worth building, price the verdict rung NO-GO, take the value layer —
was made by a human reading a markdown ceiling. `CLAUDE.md`'s self-repair boundary
is explicit: *"the agent can self-repair exactly where its cognition is
graph-native… it CANNOT edit the Python front end, because that is not graph it
can see or vary."* **Arc planning is currently prose. Prose is the blind spot.**

The goal-residual rung made the *refutations* graph-native and hooked them into
the move-grain collapse. It was honest that this left the mechanism inert: the six
residuals are at arc grain, every `MoveCandidate` `domains/prog_moves.py` mints is
unsignatured, and `gr_move_penalty` requires a non-null `sig_seam`, so the term is
arithmetically `0.0` on every live candidate. Measured, not assumed:
`results/arc6_goal_residuals.json` → `GR1_collapse_live.unsignatured_candidates`
= `{A: 0.0, B: 0.0}`.

**The negative exists; the positive does not.** There is no node in this tree that
says *"build the import oracle"*. Confirmed by enumeration: every `Goal.kind` in
`seeds/program_synthesis.json` v1.12.0 is task-grain or smaller (`synth_program`,
`fold_step`, `final_expr`, `branch_then`, `branch_other`); `prog_chunk_growth` and
`prog_construction_loop` are sub-task grain; no `domains/prog_*.py` mints anything
above one task.

---

## 2. This is more than one rung, and here is the decomposition

Stated up front because the brief invites it and because bundling these would
reproduce exactly the failure A5 registered (two semantics changes in one
measurement).

| rung | what it lands | can be measured alone? |
|---|---|---|
| **AG-1** | `ArcGoal` nodes minted by rule from measured sources; no collapse acts on them | yes — mint determinism, mint-once, provenance, and the six residuals now have something to steer |
| **AG-2** | `ag_select` — the arc-grain weighted collapse, with the proven `PENALTY` sub-term | yes — GR1's four-scene structure lifts verbatim to arc grain |
| **AG-3** | vocabulary extension: an unrecognised seam mints a `SignatureVocab` token | yes — the sd loop's own headline gate shape (mint exactly one, then recognise) |
| **AG-4** | the NL **question** when the collapse is underdetermined; the reply lands as a conditioned residual | yes — question rate is itself the measurement |
| **AG-5** | closing the loop: winner → run → artifact → re-ingest → residual → `measure_epoch` bump | **no.** This is the one that needs an executor, and it is where the honest uncertainty lives (§12) |

AG-1..AG-3 are one coherent build (three commits). AG-4 is separable and should be
built *after* AG-2, because the ask trigger is defined in terms of the collapse's
own margin. AG-5 is a different size of thing and should be scoped separately.

---

## 3. What an arc goal is

```
ArcGoal {
  agid,                                  # stable id, e.g. "arc6.remeasure.row_verdict"
  sig_seam, sig_lever, sig_target,       # the SAME three dimensions the residuals use
  kind,                                  # re_measure | supply_blocker | source_claim | reported
  source_kind,                           # residual_stale | residual_blocker | not_ingested | self_concern
  evidence_artifact, evidence_path,      # the dotted path this goal was minted FROM
  headroom_n, denominator_n,             # MEASURED value (see §6.2) — never authored
  reach_class, reach_class_factor,       # inherited from the source residual
  novelty_bits,                          # MDL price if it needs a new vocab token (§5.4)
  cost_bits,                             # declared measurement cost (§8.3 — the weak one)
  status,                                # minted | selected | pursued | settled | lapsed
  minted_epoch, measure_epoch_at_mint
}
  -mint_source->  GoalResidual | ResidualFact | SelfConcern     (provenance, always present)
  -holds_under->  ResidualCondition                             (so a GOAL can lapse too)
```

**Why a new node type and not `CapabilityGap`.** `CapabilityGap` is the tree's
existing arc-grain population, and `gap_priority` already ranks it with the
pool/value separation this design needs. It was seriously considered and rejected
on two measured grounds:

1. **No rule anywhere in `seeds/` matches or writes a `CapabilityGap`.** Every one
   of its attrs (`in_agenda`, `ordered`, `norm_salience`, `fixed`, `kind`,
   `salience`, `status`) is written by Python (`domains/self_capability_collapse.py`,
   `gap_prioritization.py`, `stopping_policy.py`, `research_agenda.py`,
   `substrate_extension.py`, `reading_review.py`). The graph only *reads* them
   inside two `Program` term-trees. Minting arc goals as `CapabilityGap`s would
   put the arc loop's state back into Python — the exact inversion of this rung's
   purpose.
2. **There is direct precedent that adding to that population perturbs live
   gates.** `seeds/code_authoring/concern_to_target_bridge.json`'s own
   `_non_resident_note` records that a resident copy *"perturbed the
   capability/self machinery's run_rules (shifted `test_gap_is_idempotent`'s
   CapabilityGap count 0→1)"*. That is not a hypothetical coupling risk; it has
   already bitten once, for a much smaller addition than this.

`ArcGoal.kind` is also deliberately a **third** namespace, not a reuse of
`CapabilityGap.kind` — which is already overloaded across two disjoint
vocabularies (`{performance, understanding, incoherence}` for the prioritiser,
`{knowledge, capability}` for the route dispatch). Adding a third meaning to that
attr is how a closed vocabulary silently stops being one.

---

## 4. Mint sources — evaluated, not assumed

Four candidates were considered. Two produce real goals on the shipped graph
today, from measured data, with no invention. One is cheap and honest. One is
admitted but deliberately weakened.

### 4.1 A STALE residual ⟹ a re-measurement goal — **the strongest source**

`codebook_epoch`'s shape, applied to ceilings. Named as not-built in the
goal-residual doc §9: *"The mechanism can tell you a ceiling no longer describes
the world; it cannot re-run the ceiling."*

**It fires today, unprompted.** `results/arc6_goal_residuals.json` →
`GR2_condition_lapse_live.as_shipped` records
`arc6.verdict.row_verdict_seed_only: 1.0` — stale, because restoring engine
`8311d4356082…` falsified `value_layer_list_eq_tuple == "1"`. So AG-1 mints
exactly one goal on a clean boot, and its content is *"the row-verdict ceiling was
measured under a value layer that no longer exists; re-measure it"* — which is a
true statement about this tree that presently lives only in a markdown correction.

**The annihilation check, and why this source passes it.** A goal minted from
residual *R* that carries *R*'s own signature would be charged *R*'s full weight by
`gr_move_penalty` the instant it entered the pool — mint and penalty would cancel,
and the mechanism would look inert while actually being self-defeating. A
re-measure goal **does** carry its source's signature (`row_verdict / verdict /
mbpp_test_257`). It survives because `gr_move_penalty`'s `Exists` predicate
requires `Not(Eq(Attr(grr,"stale"), 1.0))` — a stale residual charges nothing.
**The existing matcher is already correct for this case by construction**, which
is a real (and lucky) property, not a fix.

It is also *fragile in the right direction*: if the condition comes back (the
value layer regresses), `gr_condition_hold` un-stales the residual, the
re-measure goal is suddenly charged 51.33, and it drops down the collapse —
which is correct, because a ceiling whose world has returned does not need
re-measuring. **AG-1 must gate this explicitly** (`ag_remeasure_retire`: a
re-measure goal whose source residual is no longer stale retires), because relying
on the weight alone leaves a stale goal sitting in the pool forever.

### 4.2 A residual's MEASURED BLOCKER SPLIT ⟹ a supply-the-blocker goal

`reach_class` was the brief's suggested source. On its own it is nearly inert
here, and the reason is measured: **all six residuals are `operator_blocked`**, and
the structural ceiling measured `dimension_vs_operator.missing_dimension_ids: []`,
`n: 0`. So the `missing_dimension ⟹ mint the dimension` branch (the arc-5 π-geometry
move) would mint **nothing**, and the `operator_blocked ⟹ supply the operator`
branch would mint six goals that are all *"rebuild the seam we just killed"*.
Both outcomes are useless. **The class alone is too coarse to be a mint source.**

What *is* usable is one level finer and is already on the node: seam A carries a
blocker split over the live-unreached 53 —
**`budget 7 / missing_dimension 4 / missing_structural_primitive 42`**. Those are
measured counts against named blockers, and a goal minted from
`missing_structural_primitive × 42` is **not** "rebuild seam A"; it is "supply the
structural primitive that blocks 42 tasks". Different goal, different signature,
no annihilation.

And critically: `missing_structural_primitive` **is not a `sig_seam` token**. This
mint source therefore *forces* the vocabulary question rather than dodging it —
which is why §5 exists and why it is not speculative. The mint source and the
vocabulary-extension trigger are the same story.

### 4.3 `deliberately_not_ingested` ⟹ a source-claim goal — cheap, honest, small

Four claims were left out of the residual seed for having no measured source
(`domains/goal_residual_ingest.DELIBERATELY_NOT_INGESTED`): the 39/218 signature
count, the "35 of 36 atoms carried a verbatim prompt substring" claim, HS1's
0-of-10, and `arc6_valuelayer.json`'s non-refutation. Each is a *measurement that
does not exist yet* — i.e. exactly a goal. Minting them costs nothing and produces
goals whose success criterion is unambiguous (a dotted path resolves).

Value: these are the goals most likely to be **cheap and low-value**, so they are
also the natural probe for the cheap-goal-convergence failure mode (§8.3). If the
collapse converges on these, the value term is wrong. That makes them useful as a
control, not just as content.

### 4.4 `SelfConcern` ⟹ an unsignatured goal, admitted at a cost

The existing gap spine (`seeds/gap_awareness.json`, `residual_promote.json`,
`prog_read_gap.json`, `ps_gap_file`) already files `SelfConcern{status:'noted'}`
nodes with free-text `content`. Routing them in is right — it is the tree's
existing "the agent finds its own gaps" channel.

**What must NOT happen: parsing that free text into a signature.** That is Seam C's
failure exactly — the `relation_all` keyword variant "recognised" 245 of 257 tasks,
and the cherry-picked cue set matched `turn` inside `reTURNs` for 29 of 31 ids. A
string-derived `sig_seam` would reproduce it at arc grain, where the blast radius
is a whole build instead of one task.

So: **a `SelfConcern`-sourced `ArcGoal` is minted with no `sig_*` attrs at all.**
It can be pursued (unsignatured candidates are charged 0.0 — measured, GR1 row 4)
but it cannot be matched by any residual.

That is a loophole, and it must be priced rather than closed: **an unsignatured
goal carries an explicit `w_unsignatured` cost in the collapse.** Otherwise the
cheapest way for the loop to escape every refutation it holds is to mint
everything as an NL concern. Being illegible to the evidence layer is a cost, not
a free pass. This is a design decision I have not seen made anywhere else in the
tree and it is the one I would most want a second opinion on.

### 4.5 Rejected: the human's own past arc verdicts

"Kill S3", "seam B not worth building", "verdict rung NO-GO" are *refutations*.
They are already the residual layer, or they belong in it. Minting them as goals
would double-count evidence as intent.

---

## 5. Vocabulary extension — how an unrecognised seam extends a closed set

### 5.1 The ladder (the sd loop's, copied rung for rung)

The sd loop's Occam order is: exact recognise → transform in the existing basis →
infer the dimension → mint. It is enforced **purely by guard attrs on the node**,
each rung requiring the previous rung's `*_checked == 1` **and**
`Not(*_explained == 1)`. There is no rule-ordering mechanism in this engine; the
ladder *is* the guards. The arc-grain twin:

| rung | sd loop | arc goals |
|---|---|---|
| 1 exact | `sd_recognize` | `ag_vocab_recognize` — the proposed token IS a held `SignatureVocab{dim, token}` → `vocab_checked=1, vocab_explained=1` |
| 2 in-basis | `sd_transform_decode` | `ag_vocab_alias` — the token is a held **`SeamAlias{token, alias_of}`** node. **Authored graph data, never string similarity.** The alias table is the auditable dial |
| 3 infer dim | `sd_infer_dimension` | **deferred, named.** "This isn't a new seam, it's a new *dimension* of signature" (a fourth `sig_*`). Real, out of scope for AG-3, and it needs the `sd_dim_check_mark` treatment |
| 4 mint | `sd_mint_quantum` | `ag_vocab_mint` — add `SignatureVocab{dim, token, minted:1, provenance, evidence_artifact, evidence_path}`, bump `vocab_epoch` |
| re-arm | `sd_redecode` | `ag_revocab` — any `ArcGoal` whose `decoded_vocab_epoch < agent.vocab_epoch` re-arms and re-runs the ladder |

Rung 3 must ship with a **Term-free marker twin** (`ag_dim_check_mark`) even
though it is deferred. Reason, from the sd loop's own scars: *the seed loader
drops a rule WHOLESALE the moment any effect references an unknown Term*, so
`sd_infer_dimension` failed to install at all pre-`DimInfer`, `dim_checked` was
never set, and `sd_mint_quantum` deadlocked for every residual-having observation.
The marker rule (byte-identical guard, single literal effect) is what kept the
ladder satisfiable. Any rung we defer needs one.

### 5.2 What bounds the minting — three bounds, none of them a veto

**(a) Provenance. A token may only be minted if it is quoted from a measured
artifact.** `ag_vocab_mint`'s guard requires the proposing goal to carry a
non-null `evidence_artifact` **and** `evidence_path`, and the token string to be
the value at that path. No measurement ⇒ no token ⇒ no goal at that seam. **This
is the real bound: the vocabulary can only grow as fast as measurement grows.**
It is also the anti-Seam-D guard — a per-task token would need a per-task artifact
path, and the existing `verbatim_prompt_substring_of_len_ge_12` audit catches
that shape (§5.3).

**(b) Mint-once and dedup, copied exactly.**
- edge latch: `goal -vocab_minted-> SignatureVocab`, guarded
  `Count(Neighbours(goal,"vocab_minted")) == 0` (the `has_transform` / `minted`
  form — a monotone latch, because this engine has no `remove_edge`);
- token dedup: `Not(Exists(NodesOfType("SignatureVocab"), And(Eq(dim), Eq(token))))`
  — the `sd_mint_generator` `kind=="linear"` form, but **keyed on `(dim, token)`
  rather than one-per-boot**, which is the documented scope limit of the generator
  version and is not acceptable here;
- **one mint per pass**: the `pcon_mint` serializer — the goal must *be* the
  `Argmin` survivor over the mint-eligible snapshot. Without it two unrecognised
  tokens in one pass both mint before either sees the other, because this engine
  applies effects against pre-effect reads (snapshot-drain);
- a mirror `ag_vocab_dedup` rule (the `sd_dedup_existing` pattern) so a refused
  mint still reaches a terminal status and does not re-scan every tick.

**(c) Novelty is PRICED, not forbidden.** `ArcGoal.novelty_bits > 0` for a goal
that needs a new token, entering the collapse as `− w_mdl × novelty_bits` —
the `ps_move_w_mdl` term one grain up. A goal that needs a new word must out-earn
its novelty. This is the answer to "what stops unbounded minting" that does not
reintroduce a gate, and it is the only one of the three that scales.

### 5.3 The closure audit must be re-pointed, or minting silently escapes it

`tests/test_goal_residual_migrated.py::test_signature_vocabulary_is_CLOSED_and_graph_resident`
and `::test_no_signature_token_is_a_verbatim_prompt_substring` currently read the
**manifest's** `SignatureVocab` list. The moment a rule can mint one, those tests
must read `NodesOfType("SignatureVocab")` from the **live graph** instead —
otherwise a minted token is un-audited by construction, which is worse than having
no audit. **This is a required edit to an existing test file** and is listed in
§11 with that framing: it is not a re-pin, it is a scope extension in the
strengthening direction.

Related and easy to miss: `tools/build_goal_residual_seed.py` regeneration is gated
**byte-identical**. If minted tokens are ever captured back into the manifest, that
gate breaks. The design's answer is that minted tokens live only in the live graph
and in `seeds/generated/` if they are ever persisted — never re-captured into
`seeds/goal_residuals.json`.

### 5.4 Does this "solve" a closed vocabulary? Only partly — say so

Minting extends `sig_seam` **within** the existing dimension set. A genuinely
unanticipated *kind* of goal — one that isn't a (seam, lever, target) triple at all
— is rung 3, which is deferred. So the honest claim is: **AG-3 removes the ceiling
on tokens, not the ceiling on dimensions.** The dimension ceiling is real and is
named, not closed.

---

## 6. The collapse — what is hooked, and the honest finding

### 6.1 There is no arc-grain collapse over rule-minted nodes. Here is what exists.

| candidate | grain | pool/weight separated? | population written by | verdict |
|---|---|---|---|---|
| `ps_move_select` (`seeds/program_synthesis.json`) | move | **yes** — `refuted != 1`, `gap > 0` are `where`; the ranking is the Argmax value | rules | right form, wrong grain |
| `gap_priority` + `should_continue` (`gap_prioritization.json`, `stopping_policy.json`) | **arc** — the research agenda | **yes** — `in_agenda ∧ ¬ordered` is `Filter`; `norm_salience` is the Argmax value | **Python, entirely** — no rule anywhere matches a `CapabilityGap` | right grain, wrong residency |
| `cascade_pick` (`escalation_rungs.json`) | sequencing | n/a — `Argmin(level)` gated by `Lt(margin, threshold)` | seed | wrong shape for a weight; **right shape for the ask trigger** (§7.1) |
| `variation_pick` (`variation_ops.json`) | which *variation family* | — | seed | picks how, not what |
| `route_pick` (`research_agenda_dispatch.json`) | kind → filler | pool = matching cues, tie-break = priority | seed | the right shape for AG-5's executor dispatch, not for ranking |

**So: `ag_select` takes `ps_move_select`'s RULE FORM and `gap_priority`'s GRAIN,
and I am stating that as a new selector rather than pretending otherwise.** What
is genuinely reused, not re-invented:

- the **`PENALTY` sub-term, verbatim.** `gr_move_penalty`'s matcher is pure
  attr-equality over `sig_seam`/`sig_lever`/`sig_target` with residual-side
  wildcards — it never looks at `SignatureVocab` nodes and never looks at the
  edge type. It transfers to any node carrying `sig_*` **unchanged**. This is the
  proven, gated, four-scene-measured piece and it is copied character for
  character;
- the **policy-node pattern** from `gap_prioritization` — `SaliencePolicyWeight`
  for cross-kind normalisation, `SufficiencyPolicy` for the stop. `ag_select`
  ships `ArcSaliencePolicy` and reuses `SufficiencyPolicy` by adding one node,
  not by editing the Program;
- the **stop decision**, `should_continue`'s shape: sufficiency, not completion.
  *"The agent STOPS when what REMAINS is not salient enough to be worth fixing."*
  At arc grain this is the primary bound on the long tail (§8.1).

### 6.2 The weight, and a defect in reusing the residual formula as a value

```
value(ArcGoal g) =
      w_headroom  × headroom_n(g) × reach_class_factor(g)
    − w_residual  × PENALTY(g)              # verbatim from ps_move_select
    − w_mdl       × novelty_bits(g)
    − w_cost      × cost_bits(g)
    − w_unsig     × [g has no sig_seam]     # §4.4
```

`PENALTY` appears **only** here, inside the Argmax value — never in `match`, never
in `where`, never in the Argmax *source*. That is the structural difference
between a weight and a veto, and it is testable exactly as
`test_gr3_the_penalty_is_not_a_pool_filter` tests it today.

**The defect worth naming.** The residual weight formula is
`RESIDUAL_SCALE × reach_class_factor × (1 − honest_n / denominator_n)` — a
**dimensionless ratio**. That is right for a penalty (how completely did this
approach fail?) and **wrong as a value signal**, because it makes a 15-task target
look exactly as valuable as a 257-task one. `arc6.verdict.row_verdict_seed_only`
has `denominator_n = 15`; `arc6.seam_b.ir_retarget` has `257`. Ranking arc goals
by the ratio would treat them as near-equals.

So the value term uses **absolute headroom** — `headroom_n = denominator_n −
honest_n`, in tasks — not the ratio. Same measured numbers, different reading.
The ratio stays where it belongs, in the penalty. This is a small change and I
think it is the single most consequential line in the design.

### 6.3 A rule, not a Program

`ag_select` is a **Rule** (like `ps_move_select`), not a `Program` evaluated from
Python (like `gap_priority`). Reason: the whole population is rule-minted, so
keeping the selection inside the same `run_rules` fixpoint means no Python ever
holds arc-loop state. Adopting `gap_priority`'s invocation style would import its
Python driver along with its shape.

Consequence to design against: `ps_move_select` moves the goal's status off the
scan state, and GR2 recorded the ordering fact — *"a lapse settles in the fixpoint,
and a goal that has already passed the rung is not re-decided."* Same here, and it
is the anti-oscillation guard (§8.2).

---

## 7. The human interface is a QUESTION, not a gate

**The position, and the reason it is not a preference.** Arc 6's own plan already
records the theorem: *"excluding a candidate yields **zero bits** (Mitchell;
Angluin's L*)"* (`PROGRAM_SYNTHESIS_ARC6_PLAN.md`, Seam D). An approve/deny gate is
structurally a rejection with no counterexample — it returns ~1 bit and no reason.
**A question is the request for the counterexample.** This is the same theorem
applied to the human interface, and it explains why a gate is the wrong
*instrument* rather than merely a heavy one.

The mechanism therefore is: **the ask is a candidate in the same collapse.** Not a
side channel, not a status, not a privileged approval. `ArcQuestion` competes with
`ArcGoal`s on the same weight scale, and the agent asks only when asking outranks
acting. Everything below follows from that.

Nothing new is needed to carry it. The tree already has every piece:

| need | existing machinery |
|---|---|
| a rule that emits an NL question | `ask_clarification_self_improvement` (`seeds/conversation_self_concern.json` v2.1.0) — `add_node reply Message{from:'agent', text: StringConcat(...)}` + `agent -sent-> reply`. A rule, gated on the agent's own comprehension confidence |
| the reply comes back in | `agent -received-> m` → `comprehend_text` → Mentions → `refers_to` Concepts (the intent seed) |
| an NL instruction changing agent state, graph-natively | `steer_promote_concern` (`seeds/conversation_steering.json`) — a steering verb + a content-overlap `where`, effect is a single `set_attr` |
| surfacing what it doesn't know | `_run_self_gaps` + `seeds/question_targets.json` |
| persistence | `teach()` |

### 7.1 The ask trigger — measured, and it distinguishes ignorance from refutation

Three triggers, each a live graph read. **The second is the one that matters.**

**T1 — margin.** The top two `ArcGoal` values are within `ArcAskPolicy.margin`.
`Lt(margin, threshold)` is `cascade_pick`'s exact escalate-or-stay shape
(`seeds/escalation_rungs.json`), cited as the precedent for the form.

**T2 — ignorance, not refutation.** *No non-stale `GoalResidual` matches ANY of the
tied candidates.* These are different states and conflating them is the trap:

- tied **under refutation** — residuals cover the region, the evidence is already
  held, the weight decides. **Do not ask.** Asking here re-litigates a measurement,
  and a human answer would be *weaker* evidence than the ceiling already on the
  node.
- tied **under ignorance** — `Not(Exists(matching non-stale residual))`. Nothing is
  held either way. **Ask.** A reply is not redundant with anything.

Structurally this is one `Exists` term — the same one `gr_move_penalty` already
computes — negated. So the ignorance/refutation distinction costs nothing new and
is enforced by the same predicate that does the weighting.

**T3 — vocabulary extension.** A goal that would mint a new `SignatureVocab` token.
High consequence, and the Occam ladder already says minting is last resort.
**But the ask does not block the mint.** The mint proceeds on its own guards; the
question runs concurrently and its reply lands as evidence that can down-weight or
confirm the region afterwards. If asking blocked minting, it would be a gate with
extra steps.

**Rate bounds** — asking on everything is a gate; asking on nothing is §8's
degenerate risk:
- one open `ArcQuestion` per signature region: edge latch `region -asked_about->`,
  the `has_transform` form;
- re-ask only after `measure_epoch` bumps — the `codebook_epoch` form. Re-entry
  gated on **new measurement**, never on graph churn;
- and the real one: the ask is a candidate, so its own value falls as residual
  coverage grows.

### 7.2 The question must carry what makes it answerable

A yes/no question has reproduced the gate and its zero bits. The `StringConcat`
effect composes, from graph reads:

1. **what is underdetermined** — the two competing goals by `agid`, seam and target;
2. **what each is worth** — `headroom_n` out of `denominator_n`, the measured numbers;
3. **what is already held** — the matching residuals and their ceilings, or,
   explicitly, *"I hold no measurement covering either"* (the T2 branch, and this
   sentence is the most useful thing the agent can say);
4. **the request for a reason, shaped so the answer can become a condition** —
   *"what would have to change for this to be worth trying?"*

Point 4 is the load-bearing one and §7.3 says why.

### 7.3 The reply is a residual, with a condition — or it expires

The reply must be *evidence, not scripture*. The mechanism: a rule matching
`agent -received-> m` where `m -responds_to-> q` and `q` is an `ArcQuestion` mints
a **`GoalResidual`** — the same node type as the six measured ceilings — with
`evidence_kind: 'utterance'` and a `holds_under` edge to a `ResidualCondition`.
`gr_condition_lapse` / `gr_condition_hold` then apply **verbatim**. Zero new lapse
machinery. A human answer becomes literally the same kind of object as a measured
ceiling, weighted the same way, lapsing the same way.

**Two things must differ from a measured residual, and both are honest:**

- **weight.** Testimony is not measurement. `reach_class_factor` is replaced by
  `TestimonyPolicy.factor` (authored graph data, tunable, declared as authored in
  the write-up — the `RESIDUAL_SCALE` precedent).
- **default condition.** If the reply names a checkable condition, use it — the
  three existing `ckind`s (`shape_count`, `payload_count`, `fact_equals`) cover a
  lot, and §7.2's question is *shaped* to elicit one. If it names none, the
  default condition is `fact_equals(measure_epoch == <epoch at reply>)`, i.e.
  **an unconditioned answer expires at the next measurement epoch.**

That default is the Angluin point made mechanical: an answer with no
counterexample carries ~0 bits and lasts one epoch; an answer carrying a reason
persists until its reason is falsified. It is also the direct application of §4 of
the goal-residual doc — *"a residual that cannot lapse is a lie with a long
half-life"* — to the one source of residuals that has never been subject to it.

### 7.4 What this gives you for free

**Which questions the agent asks, and how many, is a direct read on what it does
not know.** Unsupervised operation becomes something you *observe* — the question
rate per measurement epoch falling as residual coverage grows — not something
anyone switches on. Record it as `ArcQuestionLedger{epoch, asked_n, answered_n,
region_ids}`; the falling curve is the result, and the *content* of the questions
is a second, richer read: questions clustering on one region name the frontier.

Unanswered questions must retire (the `note_experiments_exhausted` /
`elaboration_exhausted` pattern) so they neither block nor accumulate. An
unanswered question is itself data: it says the loop ran without input.

---

## 8. Degenerate goal selection — the risk this design is really about

The verification layer in this project is demonstrably strong (a builder caught
HV1/HV2 as jointly unsatisfiable before implementing; a rung tested its briefing
premise and found the engine wrong; tier 0 caught its own coincidental fit and
refused the flattering number). The untested thing is **goal selection with no
frame supplied.** Three failure modes.

### 8.1 Unbounded minting

**Do the sd loop's guards suffice? Partially — and the gap is structural.**

They do stop: re-minting the same goal (edge latch, monotone), minting without
evidence (provenance), minting more than one per pass (Argmin serializer), and
minting before cheaper explanations are tried (the Occam guard chain).

They do **not** stop a long tail of *distinct but worthless* goals. The reason is
not sloppiness in the sd loop; it is that **the sd loop's residual is bounded by
an observation.** There is always a finite thing being decoded, and the residual
shrinks as the codebook grows. An arc goal has no bounding observation — the space
of "things one could build" is open.

The bound that actually applies is therefore the *other* precedent:
`should_continue`'s **sufficiency, not completion** — stop when what remains is not
salient enough to be worth doing, deliberately leaving low-value goals undone.
Paired with §6.2's absolute-headroom value, a goal worth 3 tasks never clears the
threshold, however novel. **That is the answer, and it is an existing mechanism,
not a new one.**

### 8.2 Oscillation

Two guards, both existing shapes:

- a selected goal moves to a terminal status and **only re-enters the pool on a
  `measure_epoch` bump** — re-entry gated on new measurement, never on graph churn.
  This is `sd_redecode`'s epoch guard, and it is what makes the loop monotone in
  information rather than in time;
- **Argmax tie determinism.** Two goals with equal value must not alternate. The
  tree has already studied this (`ENGINE_ARGMAX_DETERMINISM_*`); AG-2 must pin the
  tie-break explicitly (`agid` lexical, or `minted_epoch`) rather than inherit
  whatever the engine happens to do — an inherited tie-break is a condition-free
  claim.

### 8.3 Convergence on cheap-to-measure goals — **the one with no clean answer**

This is the Goodhart of the whole design and I do not have a satisfying solution.

What helps: §6.2's absolute headroom means a cheap-to-measure goal covering 3 tasks
does not outrank an expensive one covering 200 — the value term is denominated in
the thing that matters, not in convenience. §4.3's source-claim goals are the
designed probe: they are the cheapest goals available, so **if the collapse
converges on them, the value term is wrong, and that is observable.**

What does not help: `cost_bits` is **authored**, not measured, and therefore
gameable by whoever authors it — including the agent, once AG-5 lets it author its
own goals. Naming a cost the collapse can see is better than a collapse that
cannot see cost at all (which converges on cheap *by accident*), but it is a real
hole. Two ideas, neither designed:

- **measure cost instead of authoring it** — wall time / task count of the last
  run at that seam, recorded as a `ResidualFact` by the executor. Only available
  after AG-5, and only for goals already attempted;
- **an explicit anti-Goodhart gate** — assert across a run that the selected goals'
  `headroom_n` distribution is not monotonically decreasing. Crude, but it fails
  loudly, and a crude gate that fires beats an elegant one that does not exist.

Registering this as the primary open risk of AG-2 is the honest handling.

---

## 9. Guard rails, and the concrete gate for each

| guard rail | how it is architecture, not discipline | gate |
|---|---|---|
| **weight, not veto** | every residual/testimony/novelty/cost term appears in the Argmax **value** only; pool membership is a separate `Filter` | the `test_gr3_the_penalty_is_not_a_pool_filter` form — assert `GoalResidual` appears in every Argmax value, in **no** Argmax source, in **no** `where`. Plus the four-scene GR1 lift, including *raise the headroom and the charged goal wins anyway* |
| **a residual must be able to lapse** | replies get `holds_under` → `ResidualCondition` and are handled by the **existing** `gr_condition_lapse`/`gr_condition_hold` pair, which is not latched in either direction; unconditioned testimony expires by default | assert an utterance-residual lapses on its condition **and un-lapses when restored** — both directions in one scene, per the coherence doc's strengthened form |
| **non-repetition is architecture** | signature dedup + monotone edge latches + epoch-gated re-entry. A refuted seam is *charged*, never blocked | the not-a-veto scene is the positive half; the mint-once scene is the negative half |
| **specificity is authored and auditable** | aliases are `SeamAlias` nodes, never string similarity; tokens require an artifact path; no free text is ever parsed into a signature (§4.4) | closure test re-pointed to the **live** node set (§5.3) + the `verbatim_prompt_substring_of_len_ge_12` audit run over minted tokens + a LOO-style discrimination gate over arc goals |
| **no Python decisions** | minting, matching, ranking, lapsing, asking are all Rules/Terms. The only Python is an ingest adapter resolving dotted paths and a reader | the standing source audit on the new adapter, plus the stronger module-specific form the ingest adapter already passes: it never imports `substrate_rs`, never calls `.evaluate(`, never calls `run_rules` |

---

## 10. Bars, stated as mechanisms

Per A4's standing rule — *state bars as mechanisms, not as id lists*, because an id
list inherits the blind spot of whatever instrument produced it.

- **AG1 (mint).** On a clean boot, the ladder mints at least one `ArcGoal` from a
  *measured* source, every minted goal resolves its `evidence_path` in its named
  artifact, and a second `run_rules` mints nothing further. Re-running from the
  same graph state is byte-identical.
- **AG2 (collapse).** A goal matching a held non-stale residual is measurably
  down-weighted; a look-alike differing in exactly one dimension is charged 0.0 in
  the same scene; raising headroom lets the charged goal win **while still
  charged**; an unsignatured goal is charged exactly 0.0, asserted as arithmetic on
  the Term.
- **AG3 (vocabulary).** An unrecognised token with a resolving artifact path mints
  **exactly one** `SignatureVocab`, the epoch bumps, re-decode **recognises** it,
  and a second pass mints nothing. Without a resolving path it mints **zero**. Two
  unrecognised tokens in one pass mint exactly one (the serializer).
- **AG4 (ask).** The ask fires under ignorance and does **not** fire under
  refutation with the same margin — the discriminating pair. The question text
  contains both candidates' measured numbers. An unconditioned reply is stale by
  the next `measure_epoch`; a conditioned one survives and lapses only when its
  condition is falsified.
- **AG-noreg (all rungs).** The live MBPP pass/accepted id lists are **unchanged**,
  paired against a freshly measured pre-patch baseline **on the same engine** — not
  against the patched run, and never as a count (`results/failure_baseline.json`'s
  standing rule). Per the coherence doc: the engine must be **asserted before
  measuring**, via a behavioural probe of the semantics the rung depends on, run
  under `conftest.py`.

---

## 11. Phase-2 activation: the four existing-file edits, with blast radius

| edit | why | blast radius |
|---|---|---|
| move `drafts/arc_goals/arc_goals.draft.json` → `seeds/arc_goals.json` | `boot_all._read_seeds` globs `seeds/*.json`; this is the install | **installs at every boot, for every agent in the tree.** Needs a paired tree-wide sweep per A5, not just a battery |
| `domains/seed_registry.py` +1 `REGISTRY.register` | the goal-residual precedent; the capture tool needs it | additive. *Alternative worth weighing:* the **adapter self-load** route (`domains/reading_collapse.py::_ensure_role_decode_loop`, `prog_ir_signature.ensure_prog_construction_loop`) — a `Seed{id}` marker guard, no registry edit, and the seed is inert until its adapter asks for it. **For a first landing this is the safer of the two** and it is precedented |
| `tests/test_goal_residual_migrated.py` — re-point the two closure tests from the manifest to `NodesOfType("SignatureVocab")` | §5.3 — otherwise minted tokens are un-audited | changes two currently-green gates **in the strengthening direction**. Must be dated and named, per the sanctioned reconciliation form |
| `tools/build_goal_residual_seed.py` — assert minted tokens are never captured back | the regeneration gate is byte-identical | additive assertion |

**Not to be edited:** `seeds/program_synthesis.json` (AG-2 adds a *new* rule; it
does not touch `ps_move_select`, so the confinement gate stays true),
`seeds/gap_prioritization.json`, `seeds/stopping_policy.json` (§3 — their
population is Python-written and adding to it has perturbed a gate before).

---

## 12. What I am NOT confident about

Ordered by how much damage being wrong would do.

1. **AG-5 — closing the loop — is the real rung, and it is not designed here.**
   Everything above makes goals *exist*, *rank*, *lapse*, and *ask*. None of it
   makes the loop **run**: winner → execute a measurement → produce an artifact →
   re-ingest → residual → epoch bump. The executor precedent is
   `research_agenda`'s `route_pick` + `_FILLER_REGISTRY`, and the seed-shipped
   `StandingConcern{status:'pending'}` (`seeds/standing_self_improvement_concern.json`,
   which states in its own description that it runs *"with no human in the loop"*)
   shows the entry exists. But an executor that runs arbitrary measurement code
   chosen by a graph collapse is a *materially different* proposition from
   everything else here, and I have not designed it. **Without AG-5 this is a
   planning layer with no hands, and I would rather say that than imply otherwise.**
2. **The cheap-goal convergence hole (§8.3).** `cost_bits` is authored and
   therefore gameable, most acutely once the agent authors its own goals. I have a
   probe and a crude gate, not a solution.
3. **`w_unsignatured` (§4.4) is my invention** and has no precedent in this tree.
   The reasoning is sound to me — an unsignatured goal escapes all residual
   evidence, so illegibility must cost something — but I have not measured it, and
   set too high it suppresses the `SelfConcern` channel that `CLAUDE.md` treats as
   the agent's primary self-discovery route. It needs a two-position test like the
   wildcard gate (`test_gr1_an_undeclared_dimension_is_a_wildcard`) before it is
   trusted.
4. **I have not run anything.** The sweep is live and phase 1 is new-files-only, so
   every claim about live behaviour above is read off committed source, committed
   seeds, and `results/*.json` — not observed. Specifically unverified: that
   `seeds/gap_prioritization.json` and `stopping_policy.json` are actually loaded
   on the program-synthesis path (they are in the `seeds/*.json` glob, so they
   should be, but "should be" is what §7 of the goal-residual doc said too); and
   that `ArcGoal` nodes carrying `sig_*` are picked up by `gr_move_penalty`
   unchanged — the matcher is attr-based and I have read it, but `gr_move_penalty`
   matches on the `has_move_candidate` **edge**, so AG-2 needs its own twin rule
   and the "grain-agnostic" claim in the goal-residual doc is true of the
   *predicate*, not of the *rule*. **That distinction is load-bearing and I only
   found it by reading the JSON.**
5. **Rung 3 of the vocabulary ladder (new dimensions) is deferred, so the
   closed-vocabulary ceiling is lowered, not removed** (§5.4). A goal that is not a
   (seam, lever, target) triple still has no way in.
6. **The question-rate-as-observable claim (§7.4) is untested.** It is a good
   argument; it is not a measurement. It could fail in a boring way — e.g. the rate
   is dominated by T3 (vocabulary mints) and says more about how novel the mint
   sources are than about what the agent doesn't know.
7. **Whether the ask should ever influence the mint.** I designed the ask never to
   block, which is right for a gate-free architecture. But it means a
   high-consequence vocabulary mint proceeds while the question is still in flight,
   and the reply can only down-weight it *afterwards*, never prevent it. I believe
   that is correct — a mint is cheap and reversible-by-weight, and blocking is what
   makes a gate — but it is the design decision here I would most like challenged.
