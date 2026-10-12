# EQUILIBRIUM BEHAVIOURAL QUANTA — SLICE 2 RESULTS (stream T3b, space climate)

Pack **0.4.0 / eq-tax-0.4.0**. Branch `t3b/climate-traits` (based on `t3b/behavioural-quanta`).
Design: `EQUILIBRIUM_BEHAVIOURAL_QUANTA_DESIGN_20261002.md`. Slice 1: `..._SLICE1_RESULTS_20261002.md`.
Pre-registration: `..._PREREG_20261002.md`. That document is unchanged. Slice 2 was not pre-registered, so
nothing below is a confirmatory test.

## 1. What changed

Equilibrium's space-climate metrics needed seven window-level traits. All seven are new and all are
`shadow`. Every one of them is seed data plus seeded rules, built through `teach` by
`scripts/build_equilibrium_seed_pack.py`. They reuse the scope, speech-act, contrast, competence and
stratum machinery from slice 1.

| trait | owner / target | shape (all relational or presence/absence; no numeric literal) |
|---|---|---|
| `voice.dissent` + | author → actor disagreed with | A claim-type turn (assertion or directive) that replies to another actor's claim and has one of: (a) a disagreement formula that is not negated (new scoped cue set `disagreement`); (b) a contrast connective as its first word; (c) a **negated echo**, meaning a negator followed directly by a content token whose lemma also appears un-negated in the replied-to claim. A hedge in the turn sends it to `eq_hedged`, which caps the match at partial. A negated formula ("I don't disagree") is counter-evidence. |
| `voice.error_admission` + | author, no target | New scoped cue set `error_admission` ("I was wrong", "my mistake", "I stand corrected", ...). Negated forms go to `msg.error_admission_negated`, either through negation scope or through the direct `error_denial` constructions that a contiguous cue cannot reach ("I was not wrong", "I wasn't mistaken"). Those negated forms are counter-evidence. |
| `inquiry.challenge` + | author → actor challenged | A reply to another actor that is either a question opening with a contrast connective, or an evidence request that is not negated (new scoped cue set `evidence_request`: "what's the evidence", "how do you know", "any source", ...). A negated request is counter-evidence. |
| `inquiry.answered` + | **answerer** → asker | A later reply to another actor's question that is not a question, withdrawal or dismissive reply. Evidence = [question, answer]. |
| `inquiry.unanswered` + | **asker**, no target | A question with no `inquiry.answered` over the completed window (S2 reads the absence of S1). It only fires if another actor posted later in the window, so absence is always relative. The asker's answered questions are counter-evidence. |
| `response.dismissal` + | replier → dismissed actor | A reply to a question, dissent or challenge that carries a dismissal or hostility cue, or a status claim without grounding. Evidence = [stimulus, reply]. |
| `response.engagement` + | replier → engaged actor | A reply to a question, dissent or challenge that carries grounding (code, link, citation or technical vocabulary), a concession or a follow-up question, and is not dismissive. Evidence = [stimulus, reply]. |

Mechanics:
- **Seeds.** There is a new seed, `equilibrium_climate`: the `EqClimateCue{role, lab_key}` reply codebook
  (roles stimulus / dismiss / status / ground / engage / nonanswer) plus five rules. The S1 rules are
  dismissal, engagement and answered. The S2 rules are unanswered and its counter.
- **Message-layer rules.** `equilibrium_msg` gains seven S0 rules (`eq.msg.dissent.*`, `eq.msg.challenge.*`,
  `*_hedged.hedge_op`) and one structural rule, `eq.msg.negated_token.neg_op`. That rule marks the content
  token right after a negator in a reply, so the echo join is linear, not token × token.
- **Lexicon and scope.** `equilibrium_lexicon` gains 4 cue sets (now 217 cues). `equilibrium_scope` gains a
  closed-class function-word codebook, `EqClosedClass`, which is lexical by design §5.4. It is used only to
  stop an echo from matching on "the", "it" and similar words.
- **The `eq_context` edge.** This new edge is `EqQuantum → Message`. It holds the turn a relational
  quantum replies to, for example the question of `inquiry.answered`. The adapter reads it out as
  `evidence` (a mechanical union). The match shapes do **not** count it, so one reply is one act and the
  match is at most partial (design §6.2).
- **Label statuses.** 13 new msg labels and 7 traits. `/v1/info` `trait_status` lists them as `shadow`
  through the existing LabelStatus read. Their `since_pack` is `0.4.0`.
- **Unchanged.** The `/v1/discourse` wire contract, the server code and every slice-1 rule's JSON, apart
  from the version stamp and one edge production.

## 2. Decisions

1. **Dissent and challenge do not overlap.** Dissent requires the dissenting turn to be an assertion or
   directive. A question that opens with a contrast is a challenge. This is a positive condition, so it is
   safe in S0 while the speech-act labels are still being derived.
2. **Dissent always has a target.** Every dissent shape requires `eq_responds_to` another actor's claim.
   A top-level "I disagree with the plan" mints nothing.
3. **"Substantive" is defined negatively, as the brief specified.** An answer is any later reply that is
   not a counter-question, not a withdrawal and not dismissive. Engagement additionally excludes dismissive
   replies, so a hostile reply that carries a link is a dismissal and not an engagement. A reply never
   carries both.
4. **Status-over-evidence is `msg.status_claim` without grounding in the same turn.** `msg.credential` was
   left out on purpose, because answering with relevant experience is not treated as dismissal.
5. **Golden tests.** The sealed slice-1 golden windows still compare their 0.3.0 trait set exactly
   (`_slice1`). The 0.4.0 quanta those windows now also produce are asserted separately, and listed in the
   tests. Three `/v1/classify` goldens gained new labels: "I misread" and "my bad" are error admissions,
   and "That is wrong" is a disagreement. Those goldens were extended, not rewritten.
6. **Rule ordering.** The conjuncts in the climate rules are ordered by cost only. The `enabled()` gate,
   which scans the LabelStatus rows, comes last.

## 3. Tests (synthetic, pseudonyms only)

`tests/test_equilibrium_climate.py` (12 tests) covers:
- a golden thread carrying all seven traits;
- negation near-misses ("I was not wrong", "I wasn't wrong", "It was not my mistake", "I don't disagree",
  "I don't need a source", "Open source is fine");
- a negated admission alone minting nothing;
- answered vs unanswered questions: a substantive answer, a counter-question, a hostile reply, and the
  asker's answered question as counter-evidence;
- a trailing question not being marked unanswered;
- a meeting answer by adjacency;
- dismissal vs engagement of dissent: status without grounding → dismissal; concession plus technical
  vocabulary → engagement; hostility plus a link → dismissal only;
- a status claim with grounding → not a dismissal;
- dissent near-misses: an agreeing restatement, negator plus function word, a negated formula, and a
  contesting question (challenge, not dissent);
- dissent counter-evidence;
- statuses and versioning;
- disabling a trait by data only.

The service tests add `test_discourse_contract_climate_window` (the client-parse mirror accepts all seven
codes) and the `trait_status` checks. The P7 replay now mixes climate cue lines into all 120 windows.

Final run, from the worktree, with `OZMA_NO_LLM=1 PYTHONPATH=.:runners/dsl/python python3 -m pytest
tests/test_equilibrium_{climate,discourse,discourse_service,classify,classifier_service}.py -q -s`:
```
P7 discourse turns=20000 windows=120 source_revision=[2273, 304, 164] digest=804f3ff850e884d1 strace=yes
111 passed in 352.18s (0:05:52)
```

## 4. Measurements (actual output, concurrency 1, loopback HTTP)

The machine was heavily shared during this slice: load average 21–35 on 24 cores. Absolute numbers are
therefore inflated compared with slice 1, which recorded 500-turn p95 658 ms. For a fair comparison, the
0.3.0 pack (a `git archive HEAD` snapshot in /tmp, using the same Rust build) and 0.4.0 were run
back-to-back with the same harness. The last interleaved pair:
```
BASE03 MEASURE discourse c=1 window=200 turns x10: p50 450 ms p95 590 ms max 655 ms, 447 turns/s
BASE03 MEASURE discourse c=1 window=500 turns x10: p50 1050 ms p95 1224 ms max 1238 ms, 484 turns/s
BASE03 MEASURE c=1 batch=100 n=10000: 923 msgs/s ... peak RSS (VmHWM) boot 238.6 MiB -> after 238.6 MiB
NEW04  MEASURE discourse c=1 window=200 turns x10: p50 547 ms p95 672 ms max 870 ms, 350 turns/s
NEW04  MEASURE discourse c=1 window=500 turns x10: p50 1511 ms p95 1520 ms max 1767 ms, 347 turns/s
NEW04  MEASURE discourse c=1 window=200 climate-mix turns x10: p50 559 ms p95 634 ms max 696 ms, 377 turns/s
NEW04  MEASURE discourse c=1 window=500 climate-mix turns x10: p50 1327 ms p95 1607 ms max 1640 ms, 376 turns/s
NEW04  MEASURE boot-to-healthy 3.14s, peak RSS (VmHWM) boot 238.8 MiB -> after 245.8 MiB
NEW04  MEASURE c=1 batch=100 n=10000: 794 msgs/s ... peak RSS (VmHWM) boot 238.2 MiB -> after 241.4 MiB
```
In-process medians over 6 synthetic 500-turn windows, same load:

| | 0.3.0 | 0.4.0 |
|---|---|---|
| discourse | 919–990 ms | 1145–1151 ms |
| classify, 1,000 msgs | 995–1051 ms | 1137–1227 ms |

Time per stratum, 0.4.0 vs 0.3.0 (ms): ingest 239/242, S0 312/212, S1 54/47, S2 313/258, S3 102/78,
S4 72/42.

Worst-case body (500 turns × 4,000 chars, in-process): **39.3 s** on 0.4.0 vs **33.0 s** on 0.3.0. That is
under the Equilibrium client's 60 s `DISCOURSE_TIMEOUT_S`.

Taken together, 0.4.0 costs about +20–25% wall time for discourse and +15–20% for classify. Most of it is
in S0 (4 cue sets and the negated-token rule) and in S2/S3 (more quanta for the generic rules to read).
Peak RSS is unchanged at about 246 MiB, under 384 MB. The rule fuel use is still small (S0 ≤ 29 steps in
the goldens).

## 5. Nulls, limitations, open questions

- **Not validated.** No corpus or human-coded data was used. Every trait is a behavioural indicator in
  shadow, with no validity claim.
- **Meetings answer by adjacency only.** A meeting answer counts only if it is the next turn by another
  actor. A later answer after an interjection is missed, which over-states `inquiry.unanswered` in
  meetings. Any non-question reply also counts as an answer by adjacency ("Let's pause" answers the
  question before it).
- **Window boundaries.** A question near the end of a window is unanswered only if another actor posted
  later. A window cut can still split a question from its answer.
- **Conditionals and idioms.** "If I was wrong", "correct me if I'm wrong" (the second was dropped from the
  lexicon) and "I couldn't disagree more" (read as negated) are not resolved. Double negation is still
  unresolved, as in slice 1.
- **Negated echo is a narrow shape.** It needs the negator to be directly followed by the echoed content
  token. "The cache is not really cold" is missed because "really" is closed-class. A shared content word
  that is not the disputed claim can produce a false echo.
- **Rhetorical questions.** These count as questions for answered/unanswered ("Are you serious?" is a
  question plus hostility).
- **Engagement is broad.** Technical vocabulary alone counts as grounding.
- **Open: should dissent root or extend dispute episodes?** It does not yet, so the episode goldens are
  unchanged.
- **Open: should `msg.credential` count as status-over-evidence?** It does not yet.
- **Open: targeted unanswered.** `interaction.responsiveness` already covers the case of a question to a
  named actor who posted later and did not reply.
