# Stacks Project code-reading panel v1 preregistration

Date: 2026-09-27  
Status: freeze before confirmatory execution.  
Question: how does the production code-reading path process independently authored functions from a software repository outside the Think Python teaching corpus?

## Corpus and selection

The corpus is the six Python files under `data/stacks/repo/scripts/` from the locally vendored Stacks Project repository at commit `9b335a632509b7b16cc9eb7bf771ec2cf82ac640`. The scripts directory contains its Apache-2.0 license. The source tree is used locally for research; raw records retain paths and hashes, not source text. Select every top-level `FunctionDef` in lexical file/line order (37 functions across six files). This is a census of that bounded local slice, not a random sample of software projects. For a repeated function name, the file path disambiguates the task. Each task passes the complete source module and selected function name to `domains.code_reading.read_function`.

No behavior examples, expected answers, or task outcomes are used for selection. This is a route-entry and coverage measurement, not a semantic correctness test. The source modules are parsed, never imported or executed by the harness.

## Execution and outcomes

Two fresh worker processes boot the full seed runtime, then process the frozen schedule in independent adapters. Record source and module hashes, exceptions, recognized construction, minted-route flag, Term presence, new receipt/observation/axis/signature/transform counts, wall and CPU time, graph deltas, boot failures, and peak RSS. Do not persist source text, comment text, or rendered output. Count post-cold-start (tasks 2–37) receipt/mint incidence separately from the first task. Report function-level and aggregate coverage; these outcomes do not establish semantic understanding, behavior prediction, or general repository performance.

## Integrity gates and limits

Lock this protocol, selector, frame, runner, analyzer, all six source modules, scripts license, repository README, relevant runtime sources, and the complete boot-selected seed set (`seeds/*.json` and `seeds/generated/*.json`, matching `substrate.boot_all._seed_manifest_paths`), plus native extension. Do not hash unrelated nested seed archives as though the runtime loads them. Require two distinct worker PIDs, stable locks before/after each worker and parent run, all 37 tasks in exact order, no task errors for the clean-run claim, and independent reconstruction of the selector/frame, hashes, and outcome totals. The shared `substrate-run-manifest-v1` capture records explicit inputs and a hashed parent stdout/stderr log; child return codes and stderr remain in the raw report. A source mutation invalidates confirmation. The source is one repository and a locally vendored snapshot; conclusions are limited to this corpus and route. A semantic follow-up needs a separate safe behavioral subset, declared input contracts, an independent oracle, and held-out composition/family tests.
