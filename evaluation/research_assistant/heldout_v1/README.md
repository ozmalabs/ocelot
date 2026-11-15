# Held-out research assistant tasks, v1

This set contains four new held-out prompts, separate from the burned pilot in
`../pilot_20261114/`. It has not been run against any model. The set covers a
finite check versus universal proof, missing and dead controls, an unavailable
stale source, and qualitative analysis of non-GE OCELOT work.

## Files and interface

- `tasks.json` is the answer-generation input. Give the system one task object
  at a time, including its prompt and evidence blocks. Do not expose
  `answer_keys.json`.
- `answer_keys.json` is for blinded human grading after answers are frozen.
- `source_manifest.json` pins real repository source files by SHA-256 and
  identifies their locators. The synthetic `case_record` facts are explicitly
  embedded in task evidence; they are fixture premises, not original records.
  Frozen `tasks.json` SHA-256: `b3856619df851db6d417a904391bfe97d96773f466218bfdc416c635e3790620`.
- Record one answer per `task_id`, preserve citations/locators, and blind grader
  arm identity. Keep the original input and answer file unchanged during runs.

Before evaluation, recompute SHA-256 for each repository file listed in the
manifest and record the result. A changed hash requires a new frozen source
snapshot or a new task-set version. The fixture is data only: it contains no
runner, model calls, or results.
