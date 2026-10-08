# Thoughtexperiment composed-proposal active query v1 — preregistration

## Question

Can the thoughtexperiment path use an active query to distinguish a substrate-composed repair proposal from a faulty target rule, and then retain the proposal on independent held-out cases?

This gate composes the existing non-action `classify_kind_family` target via the normal general structural proposal route. A known faulted target is the competing baseline. It then asks the native Term query selector to choose among supplied ControlKind names. The candidate predictions are produced by running each actual rule in an isolated native substrate branch; the selector receives no expected labels. This is a cross-interface integration test on one authored control-kind family, not an open-ended induction claim.

## Procedure

Four workers each generate a proposal via `ground_concern` and the registered general-structural cue. Each worker then evaluates two hypotheses: the faulted target rule and the generated proposal. Candidate pools contain 100 distinct names, with 0%, 50%, 90%, or 99% neutral names; informative names are built from the locked control-kind lexical signals and include novel suffix tokens. Neutral names contain no registered signal. The native rule closure predicts both hypotheses' outputs for each name. A native-Term selector chooses a maximum predictive-entropy name. Its query, predictions, and entropy are captured before the task oracle is consulted.

After all worker orders are written, the scoring stage applies an independently locked label table for the signal families and `null` for neutral names. It reports survivor identity, query validity, proposal-vs-fault discrimination, and random one-shot probe performance. The generated proposal and fault baseline are also scored in fresh held-out branches on the established two held-out names. Source, task, adapter, query selector, Term evaluator, and loaded native binary hashes are frozen before capture and checked at each stage.

## Measures and pass conditions

Report proposal target/operator/site, host candidate digest match, native closure predictions, selector entropy, correct proposal survival, random baseline discrimination, held-out proposal/fault utility, receipt validity, primary-state preservation, selector cost, and proposal/candidate-scoring phase costs where available. The gate passes if all 16 selected queries are valid and discriminating, all post-query survivors contain only the composed proposal, every composed proposal passes both held-outs, every fault baseline fails them, receipts and primary preservation hold, and all source hashes are stable. Random baseline outcomes are descriptive, not a gate.

## Scope boundary

Candidate task, fault construction, structural cue, lexical label table, candidate pool construction, and oracle remain authored by Python. The composer uses the native graph Term for target/operator selection after Python exposes rule provenance, and Python still materializes edits. The query selector uses supplied hypothesis Terms and candidate examples. This measures integration of prompted proposal composition with bounded active selection and native rule prediction. It does not demonstrate autonomous fault diagnosis, discovery of hypotheses, new task-family transfer, dimension induction, primitive invention, or self-improvement.

## Reproduction

Run `python3 evaluation/substrate_capability/thoughtexperiment_composed_proposal_active_query_v1.py --lock`, then `--orders`, then `--score`, and finally `python3 evaluation/substrate_capability/analyze_thoughtexperiment_composed_proposal_active_query_v1.py`.
