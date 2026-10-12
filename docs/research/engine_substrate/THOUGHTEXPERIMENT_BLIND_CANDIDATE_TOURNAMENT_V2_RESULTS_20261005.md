# Blind candidate tournament v2 results

## Outcome

The source-locked panel passed independent analysis across three fresh
workers and six opaque authored cases. The boolean-effect and numeric-
threshold repair cases each selected one candidate, passed three canary
rehearsals and the disjoint final examples, and committed exactly once by
revision-checked RulePatch (revision 0 to 1). The boolean and threshold
no-repair cases, an ambiguous-threshold training case, and an irrelevant
relation proposal all abstained with `no_causally_supported_patch`; each kept
revision 0. The ambiguous case is underdetermined by its training split, and
the relation case generated one distractor candidate whose measured outcome
did not clear the control margin.

The threshold case initially admitted both a threshold-shift candidate and an
equality guard under two training examples. Before source lock, the fixture
was amended with a third training value that distinguishes those hypotheses.
The frozen evaluation therefore measures unique selection on the amended
split; it does not count the exploratory ambiguity as a frozen failure.

## Measured phase costs

Median wall-clock timings from the three-worker capture (tiny in-process
fixtures; nanoseconds):

| Phase | Median | Observations |
|---|---:|---:|
| Candidate generation | 0.496 ms | 6 |
| No-op rehearsal, 3 reps | 1.943 ms | 6 |
| Placebo rehearsal, 3 reps | 2.124 ms | 6 |
| Candidate-pool rehearsal | 30.209 ms | 6 |
| Graph selection | 0.206 ms | 6 |
| Canary rehearsal, 3 reps | 9.330 ms | 2 |
| Canary/commit tick | 0.136 ms | 2 |
| Final verification | 1.505 ms | 2 |
| No-repair abort close tick | 0.065 ms | 4 |

The median summed measured lifecycle across the two committed repair cases is
89.989 ms. It covers the runner's measured rehearsal/control, selection,
canary, commit, and final-verification phases; it excludes process boot,
fixture/task construction, and external oracle work. Candidate-pool rehearsal
is the largest measured phase. Six authored cases are too few for workload-
level latency claims.

## Interpretation and limits

This extends the v1 boolean demonstration to a second local edit family and
adds explicit no-repair, ambiguity, and relation-distractor behavior. Candidate
generation sees the live rule and observed relation signatures; graph
selection sees opaque candidate IDs and measured branch evidence, while the
harness retains task labels and the oracle. It is evidence for a bounded
generation → rehearsal → selection/abstention → canary → CAS integration, not
open-ended induction, natural-task prevalence, or substrate self-improvement.
The cases are authored and tiny, with only two repair families and three
workers. Scaling, broader candidate grammars, independently authored task
families, and a task-side oracle not supplied by the harness remain open.

## Reproduction artifacts

- [Preregistration](THOUGHTEXPERIMENT_BLIND_CANDIDATE_TOURNAMENT_V2_PREREG_20261005.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_blind_candidate_tournament_v2.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_thoughtexperiment_blind_candidate_tournament_v2.py)
- [Fixture](../../../evaluation/substrate_capability/thoughtexperiment_blind_candidate_tournament_v2_fixture_20261005.json)
- [Source lock](../../../evaluation/substrate_capability/thoughtexperiment_blind_candidate_tournament_v2_lock_20261005.json)
- [Capture](../../../evaluation/reports/thoughtexperiment_blind_candidate_tournament_v2_20261005.json)
- [Independent analysis](../../../evaluation/reports/thoughtexperiment_blind_candidate_tournament_v2_analysis_20261005.json)
