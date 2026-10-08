# Conversation-profile runtime import observation v1

Date: 2026-09-28  
Status: preregistered before capture.

## Question

Does `load_conversation_seed_profile()` actually issue the 65 module-preload calls declared by `CONVERSATION_RUNTIME_MODULES`, which modules are newly imported versus already present, and what is the selected seed/profile startup cost on this source snapshot?

## Frozen inputs and procedure

- Use the v1.1 Python source coverage inventory as the expected file and loader-manifest hash set. Verify all listed Python files, all top-level plus `seeds/generated/*.json` manifests, the native extension/build record, runner, analyzer, and this protocol before and after each worker.
- Run three fresh Python worker processes. Each constructs `WorldAdapter(seeds=())`, records `domains.*` modules already loaded, invokes `load_conversation_seed_profile()` once, and wraps `importlib.import_module` to record every exact call, result module, and duration from that invocation.
- Record declared-versus-observed import-call order, modules newly present afterward, selected seed IDs and status, graph node/edge counts, total profile wall time, and process peak RSS.
- No conversation prompt, task score, or rule-closure benchmark is part of this probe. Do not interpret module imports as executed capability.

## Gates

1. Three distinct worker PIDs, each with stable locked inputs at worker start and finish and stable top-level inputs after the run.
2. All profiles report selection complete and no seed load failures; selected seed IDs and graph counts repeat across workers.
3. The observed importlib call sequence exactly matches the declared 65-item tuple in order, and each target resolves to the corresponding in-repository module file.
4. Report modules that were already loaded before the profile separately from modules newly imported by the profile; do not call the latter a complete per-task dependency closure.
5. Preserve raw data and report the analyzer result even if any capability/boot gate fails. Do not rerun into the same output paths.

## Claim boundary

The result measures one explicit boot profile on one current source snapshot. It does not establish which preloaded modules a particular conversation uses, whether each domain module is operational, the cost of full seed boot, or natural task prevalence. The 838 manifest hash set covers loader path inputs; manifests marked `self_load_only` are recorded but not selected by this profile's ordinary load.
