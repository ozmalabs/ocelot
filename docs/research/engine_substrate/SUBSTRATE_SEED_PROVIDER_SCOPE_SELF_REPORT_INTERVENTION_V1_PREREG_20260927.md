# Seed provider-scope / self-report intervention v1

Date: 2026-09-27

## Question and contrast

The locked route-contrast snapshot uses `substrate/boot_all.py` SHA-256 `9b9c2ac025f0fea54a9b463e818737e7d765bcce351d69a0572b9ede746bf494` and reproducibly sends `report your organisation` to wordplay. The later worktree version (`6662935bceb89af91cb86a402273045e579a20120e134cf74b7919f2c0fc7b22`) changes one provider-closure block: when following typed seed references it prefers the source provider, filters to same-group providers, and admits a global provider only when unique. No other file differed in the source-lock comparison.

Test whether this one-file boot change alters the loaded seed set and self-report outcome. Compare the archived old `boot_all.py` against the current `substrate.boot_all` in six fresh processes (three each), interleaved by replicate. Hold prompt fixed at `report your organisation`; boot from the same source tree, seeds, native extension, and other Python modules. The archived module is dynamically loaded as `substrate.boot_all`; no workspace source is overwritten.

## Captures and gates

Capture source locks before/after each worker and at driver boundaries, old/current `boot_all.py` digests, loaded seed IDs, failed seed manifests, semantic graph digest, comprehension kind/dispatch, route, reply, Goal lifecycle, boot time, and PID.

Pass gates: six unique PIDs; three runs per condition; exact stable source locks throughout; identical route/reply/graph and loaded-seed set within each condition; complete records; and no source changes besides the designated boot module between the treatment definitions. Report the symmetric difference in loaded manifests. Causality is supported only for this prompt and this exact one-file implementation contrast; do not generalize to all boot profiles or language routes.

## Interpretation

If route changes with only the boot module version, provider-scope selection is a causal boot-path dependency for this prompt. If loaded manifests also change, that set difference is a candidate mediator, not proof which individual manifest is necessary. Seed-specific attribution requires a further deletion/add-back intervention. If routes remain identical, the route contrast is not explained by this hunk.

## Reproduction

```sh
python3 scripts/probe_seed_provider_scope_self_report_intervention_v1.py --lock
python3 scripts/probe_seed_provider_scope_self_report_intervention_v1.py
python3 scripts/analyze_seed_provider_scope_self_report_intervention_v1.py
```
