# Thoughtexperiment recurrence budget calibration v1.1 — preregistration

## Question

Does staged early rejection preserve useful recurrence repairs as graph arity and per-stage work budgets vary, while reducing closure work spent on poor proposals? This is a calibration study for the thoughtexperiment harness. It does not claim general termination or move candidate generation into the substrate.

## Workload and paired design

Build each episode from a new deterministic graph generator in the study runner; do not call the earlier candidate-admission or early-rejection episode builders. The generator creates one `MintingRecurrenceEpisode` and a sequence of 2, 4, or 8 due candidates. Each candidate receives a unique worker/split/sample/ordinal recurrence key, structural signature, and supporting segment. Training and held-out use disjoint keys, and the runner records the full input specification and its digest. This changes both graph construction and task arity while retaining the same seeded recurrence rule family and exact offer-count oracle.

Use four source-locked workers, the eight existing host-generated variants of `mrl_offer_due_once`, two training samples and two held-out samples per worker/arity, and paired evaluation at stage budgets 200, 400, and 800 rule calls. A stage is one due candidate: install the proposal, run rule batches of at most 100 until a batch uses fewer than its limit or the budget is exhausted, then admit the next due candidate only after fixed point. The reference arm uses the same incremental admission order and a 1,000-call per-stage ceiling; a stage still unresolved at that ceiling is recorded as right-censored, not as nonterminating. All arms begin from fresh equivalent graphs. Run each configuration on exactly the same task input; freeze training outcomes and candidate decisions before scoring held-out inputs.

The graph Term selects from the supplied candidates using training outcomes only. The ranker receives only training-split prediction-versus-oracle evidence; it receives no held-out values or explicit identity of the useful variant. Use opaque candidate IDs at decision time, with label decoding held for analysis. Retain an all-wrong/tie control to verify abstention. Candidate definitions and ordering are generated before held-out execution and hashed into the training-order artifact.

## Measures and gates

For each arity and budget, report exact episode-level outcome parity against the reference, selected-candidate oracle success, false-rejection count for any candidate that reaches the reference oracle and fixed point, budget rejection by stage and candidate, rule work, elapsed time, graph construction, Term scoring, and candidate-generation time. Report the winner's result separately from aggregate candidate work. A budget rejection is censored work, never evidence of nontermination.

The confirmatory gate passes only if: (1) source/native/input hashes remain stable; (2) candidate identities and task inputs match across paired arms; (3) the same unique useful candidate is selected in all workers from training evidence; (4) the selected candidate has exact oracle parity and reaches fixed point on all held-out episodes at every arity and budget; (5) tie/all-wrong controls abstain; (6) each evaluation starts from a fresh graph and leaves the installed candidate rule definition unchanged during closure; and (7) all captured work/time fields are finite and recomputable from raw records. This is an evaluation-only calibration: it does not measure adoption into a shared primary graph. Alternative proposals may be rejected by the budget; their exact rejection rates and work savings are reported. If any budget rejects an oracle-correct candidate that the reference resolves, that budget fails the useful-candidate preservation gate, even if the winning proposal happens to survive.

Do not pool budgets or arities to hide a failed cell. Do not infer an asymptotic complexity law from this finite matrix. This is an independent replication of budget behavior under a new graph generator, not an independent semantic rule family or natural-task sample.

## Provenance and reproduction

Before capture, freeze this protocol, runner, analyzer, all active Python/Rust/native sources, seed files, and the loaded native binary. Capture training orders first; held-out outcomes are generated only after the order artifact is frozen. The analyzer must be separate from the runner and consume only the lock, orders, scores, and raw capture. Publish all raw rows and any deviations, including failed/censored cells.
