# P22 candidate-specific request audit: D4 0955–0959

**Status: superseded. No action has been taken. Do not use this request.**

Candidate `#1908` has a standalone effect absent from the registered D4 root,
but the only recorded independent-goal witness is not useful improvement
evidence. Its verified transfer child has the same effect as active held
process `rot90`. The qualification rule has since been tightened to require
both the source candidate and its transfer-child effect to be absent from
active/adopted processes. Under that rule `#1908` has no qualification, and
this request cannot authorize an action.

The earlier source run and replay recorded candidate digest
`2d2cb9ecda29351e1d0f513498eb6089c0f48b2dc1f8ee8650ebb2bbf39cdc46`, source
qualification `#12011`, and witness keys 0955/0957. Their raw SHA-256 values
are `d28d5a1b28745eaebacf6c30944c56020cbd40061a2d527dec4c4fb342cf12b8` and
`bda9d81607bc0de632ac1c2214944cd729ef406c4845aa77a1175f8706d5d5dc`.
Reevaluation with the transfer-child novelty guard recorded zero
qualifications, approvals or receipts, and no validation or held-out access;
its raw SHA-256 is `12d014e3af958b889c1706cbf6d87853c6b8540ed5df9ca4856995492a7ba21a`.

The output path `evaluation/process_mastery/results/p22_approved_candidate_d4_0955_0957.json`
remains unused. The machine request has status `superseded`; the guarded CLI
rejects it. A separate request now selects qualification `#11843` and witnesses
0962/0972 for the same expression; only that current packet can authorize an
action.

Machine audit record: [`COGNITION_P22_CANDIDATE_AUDIT_D4_0955_0959.json`](COGNITION_P22_CANDIDATE_AUDIT_D4_0955_0959.json).
