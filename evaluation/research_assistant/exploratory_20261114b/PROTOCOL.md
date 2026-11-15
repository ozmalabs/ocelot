# Four-case exploratory evaluation protocol

Written before answer generation. This is an exploratory comparison, not the
40-task confirmatory design in `HELDOUT_PREREG.md`: the agent runtime does not
provide filesystem isolation, a pinned model snapshot, fixed token limits or
usage, independent key verification, or enough distinct tasks. The four new
cases contain close parallels to burned pilot topics and are not a clean
held-out sample. Do not claim they are independent of prior tasks or use them
for confirmation. Inputs and keys are separately stored but share a filesystem;
agents are instructed not to read keys, an unenforced boundary.

Use 12 fresh Luna agents, one per task/arm, each given the same task JSON and
listed source paths. Arms: ordinary source reading; generic claim/evidence notes;
and the helper's frame, claims, evidence, counterevidence and export. Model
settings and token usage are unavailable; wall time is only recorded if the
orchestrator can capture it. Randomize execution and arm labels using seed
20261114 with `heldout_runner.freeze_assignments`; assignments are fixed in
`assignments.json`. Agents return one answer each under their blind label.
Store all outputs, failures and visible protocol deviations. All arms have the
same source access. No agent may read keys, assignment mapping, other answers,
or prior pilot; these are instructions rather than enforced restrictions.

After all answers are collected, request two fresh graders to independently
score every answer against keys using the seven-dimension pilot rubric and
record rationales. Grader labels hide arm identity but answers may expose their
method. Preserve scores and report exact agreement, per-arm descriptive mean
scores, task-wise paired differences and all missing/failing runs. No confidence
interval or inferential claim is warranted by four related tasks and shared
filesystem; report token and timing values as unavailable where not captured.
No change to tasks, arm instructions, scores or acceptance rules after output
collection starts. This freezes the procedure locally; it has not been
committed or independently timestamped and is not a confirmatory preregistration.
