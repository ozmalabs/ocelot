# Four-case exploratory comparison — 2026-11-14

**Result: no measured advantage for the helper in this run.** Two Luna
reviewers scored 12 answers from fresh Luna agents: four cases in each of the
source-only, generic-ledger, and research-helper arms. Each score below is the
mean of both reviewers' seven 0–2 rubric dimensions, then averaged across the
four cases. Higher is better.

| Arm | Completed | Mean score / 2 |
| --- | ---: | ---: |
| Source-only | 4/4 | 1.911 |
| Generic ledger | 4/4 | 1.964 |
| Research helper | 4/4 | 1.893 |

The paired helper-minus-source differences were −0.071, +0.143, −0.143 and
0.000 across the four cases (mean −0.018). Helper-minus-generic differences
were −0.071, +0.071, −0.214 and −0.071 (mean −0.071). These are descriptive
scores for these particular answers, not estimates of a population effect.
The ceiling-heavy rubric, four cases and grader judgement make the decimals
more precise-looking than the evidence warrants.

The largest negative helper comparison was on the qualitative document case:
the graders judged that the helper answer did not mention a reported flat-to-
declining training-size sweep, which the key treated as counterevidence. The
case's short supplied excerpt did not mention that sweep, although the full
source was available to all arms. This makes the criterion a test of source
inspection as well as the supplied excerpt and limits interpretation of that
score. Other answers mentioned the sweep. The helper ledger and a passing graph
check did not guarantee that the answer captured this limitation.

Grader exact agreement was 12/12 for source accuracy, contradiction recall
11/12, limitation recall 11/12, unsupported assertions 11/12, completion 11/12,
citation-hash match 12/12, and citation reopenability **5/12**. Inspection of
the rationales shows a systematic difference: one grader generally wanted a
precise linked locator, while the other accepted document-and-section
references. Those citation scores should not be treated as a reliable
measurement until the rubric is tightened. For the other dimensions, raw
agreement on 12 cases is not a reliable inter-rater reliability estimate.
Hash scoring checked the currently available cited files against the fixture
manifest; it did not require an answer to state the hash except where its task
required it. Thus this score does not establish historical source provenance.

All scheduled answers were returned. The four helper runs recorded graphs
containing frame, claim, evidence, and alternative nodes; their saved ledgers
are alongside the answers. Tokens, provider cost, and reliable per-run latency
were unavailable, so cost or efficiency was not compared. Agent model was
requested as `gpt-6-luna`; exact model snapshot and sampling controls were not
available. The key, assignment, and output files shared a filesystem with the
answering agents: access was prohibited by instruction, not enforced. Grader
blinding was likewise by instruction and answer content could reveal the arm.
The task author and two graders were LLM agents, and no independent human
validation of the key was performed.

These four new cases are close variants of burned pilot topics, and the local
protocol was not committed or independently timestamped. They are not a clean
held-out sample. The result cannot establish that the helper helps, harms, or
has no effect in broader research tasks. The 40-task confirmatory protocol's
isolation, key review, model-budget, sample-size and preregistration gates remain
unmet; do not present this run as that study.

## Reproduction and audit

- [Protocol](PROTOCOL.md), [randomized assignments](assignments.json), [blind answers](blind_answers.json),
  [first grader](grader1.json), [second grader](grader2.json), and
  [machine-readable results](results.json).
- Task bundle SHA-256 `b3856619df851db6d417a904391bfe97d96773f466218bfdc416c635e3790620`;
  answer key `24477fe88acce42dd936791ccc82b7e900f2851c5dc8f2496e2644d4b4c426a7`;
  blind answer bundle `d7aef6ac34b65161e413715131029329f02b8ce1d43b93fa3437fead9f0d5286`;
  grader 1 `52e1ad93fc538125cb1190f56aa4e6dc72cf62f20f2359a6d2c07b5114aa8c73`;
  grader 2 `1d1cb880e0350e5ebf67217766f159344fe812a92a5fb80390edad2c107fd955`.
  Hashes identify these local artifacts; they are not external timestamping.
- Run `python -m evaluation.research_assistant.analyze_exploratory` from the
  repository root. It validates labels, task IDs, answer hashes and score
  ranges before producing the descriptive results.
- Focused evaluation tests: `python -m pytest
  evaluation/research_assistant/tests/test_heldout_runner.py
  tests/test_research_evaluation_migrated.py -q` — 9 passed.
