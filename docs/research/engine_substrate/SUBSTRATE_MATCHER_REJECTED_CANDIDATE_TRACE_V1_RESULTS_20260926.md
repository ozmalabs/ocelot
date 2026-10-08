# Rejected matcher candidate trace probe v1 results (2026-09-26)

All eight preregistered checks pass on the current-source native engine.

- Candidate count 1: `cand_tested=1`, one successful `pattern_edge` event, one candidate predicate attribute read.
- Candidate count 9: `cand_tested=9`, still one successful `pattern_edge` event, and nine candidate predicate attribute reads.
- Traced and untraced closures settle with the same fixed-point status and progress; untraced arms emit no events; trace overflow is zero.

The predicate reads are represented, but the access trace omits the concrete edge identities for the eight rejected candidates. The native scale audit establishes that candidate matching work increased 9× while successful binding-edge events remained constant. This narrows the gap: traces show the accessed predicate attribute resources, but do not faithfully encode all candidate edge dependencies or matcher work. It is one controlled one-edge rule family, not a general matcher recall rate.

Reproduce with:

```sh
PYTHONPATH=runners/dsl/python:. python3 scripts/substrate_matcher_rejected_candidate_trace_v1.py
```

See the [preregistration](SUBSTRATE_MATCHER_REJECTED_CANDIDATE_TRACE_V1_PREREG_20260926.md), [runner](../../../scripts/substrate_matcher_rejected_candidate_trace_v1.py), and [raw report](../../../evaluation/reports/substrate_matcher_rejected_candidate_trace_v1_20260926.json), which embeds the shared run manifest and a hashed parent-process log at `evaluation/run_logs/substrate-matcher-rejected-candidate-trace-v1-20260926.stdout_stderr.log`.
