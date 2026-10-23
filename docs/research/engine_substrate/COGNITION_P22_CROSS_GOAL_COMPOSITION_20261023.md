# P22 distinct-goal composition development result

This is a development-only mechanism result for P22.02. It does not replace a
preregistration, held-out evaluation, checkpoint lineage, or four-arm learner
comparison. The training pairs were selected as mechanism fixtures so a
verified source candidate composed with a held process can reach the second
goal. The Loopover pair was selected by inspecting generated training-process
relations. No efficacy inference follows from these selected fixtures.

## Mechanism and boundary

P19 search now tests a digest-attested candidate as an algebraic operand in
both composition orders on a distinct training goal before broad recursive
search expansion. A native `AddNodeWithinCounters` effect checks and increments
the shared policy reservation and that request's reservation before creating
an attempt. If either counter is invalid or at its limit, the effect creates
nothing and binds no attempt variable. The verified composition attempt keeps
an `extends_candidate` edge; minting its child candidate produces an expression
digest that includes the parent candidate digest and source epochs. P22
qualification requires the verified child receipt and the second training
task. Neither the proposal nor child candidate is actionable without the
existing exact approval path.

The two evidence runs produced one qualified source candidate per family:

| Family and training goals | Source candidate | Verified second-goal attempt and child | Qualification |
|---|---|---|---|
| D4 v2, train `0200` → `0202` | `#752`, digest `8a737c4d9d27d7e97233ddbc57921fb661e088a65fecce23eea884b7a8753788`, params `[0,2,1,3]` | Attempt `#3194` on `0202`; child `#3198`, digest `a9978b63744fce75244b7d39352746701d0890ee0df00ce85032cd1e4d1f0e3b` | `independent_goal_composition`; witnesses are source attempt `#751` and trial `#3194` |
| Loopover v2, train `0015` → `0026` | `#5761`, digest `f8277f0f8d7df4de63aed09cfc4f265ed2f6d9293034ae73ec18fdb9babfe75d`, params `[0,3,2,5,1,7,6,4,8]` | Attempt `#5770` on `0026`; child `#5791`, digest `6d8cf36cb8672db82f7083624a700295557a860b0af034d3bef8369225a70215` | `independent_goal_composition`; witnesses are source attempt `#1483` and trial `#5770` |

Node IDs are local to each ephemeral graph. Digests and bindings identify the
expressions. Request attempt counts equaled native reservation counts in both
runs: D4 2,441 and 3,939; Loopover 5,000 per request. The bounded development
probe overrides the per-request limit to 5,000 and the shared total to 30,000;
these limits are diagnostics, not a frozen evaluation budget.

No approval, world receipt, or checkpoint was created. The eight-world
validation scorer is descriptive only: D4 source/child scores were 3/8 and
1/8; Loopover source/child scores were 0/8 and 0/8. The fixture selection,
small sample, lack of matched arms, and absence of approved checkpoint lineages
preclude any efficacy or generalization claim.

The earlier distinct-goal probes remain valid historical evidence: D4
`0200/0201` and Loopover `0206/0207` produced no cross-goal qualification. They
tested pairs without a verified candidate-plus-held composition to the second
goal. Do not overwrite those records. All validation draws `0201–0208` used
here overlap the earlier development panel and are unavailable to later
preregistered evaluation. Training pairs `0200/0202` and `0015/0026` are also
consumed development allocations.

Raw outputs:

- [`p22_cross_goal_composition_probe_d4.json`](../../../evaluation/process_mastery/results/p22_cross_goal_composition_probe_d4.json), SHA-256 `c465b13af262db2c7662969961004acde7e13f0fcf6d0f43797a64d33a3700bb`.
- [`p22_cross_goal_composition_probe_loopover.json`](../../../evaluation/process_mastery/results/p22_cross_goal_composition_probe_loopover.json), SHA-256 `e4e610f6ed49d60c24bed394a32009c730c2bcc61a3f843689a6e614f24d486f`.

Verification: `tests/test_open_process_search.py`,
`tests/test_independent_improvement.py`, and `tests/test_p22_development.py` —
26 passed. Native Rust suite — 869 passed, 4 ignored. Engine provenance — 9
passed, 1 skipped. The source candidate `#752` retains the digest in the
earlier candidate-approval packet. The Loopover source candidate here has a
different digest from that packet's Loopover candidate and carries no approval.
These new results do not grant simulated-adoption authorization.
