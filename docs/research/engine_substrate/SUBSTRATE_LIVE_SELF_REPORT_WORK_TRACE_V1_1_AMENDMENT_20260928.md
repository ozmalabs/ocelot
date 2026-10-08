# Live self-report all-scope work trace v1.1 amendment

Date: 2026-09-28  
Status: source-lock and custody repair; task and criteria unchanged.

## Reason

V1 attempt 1 was censored after `domains/comprehend_text.py` changed during its first worker. The v1 recursive seed lock also hashed 307,510 JSON files beneath `seeds/`, while `substrate/boot_all.py::_seed_manifest_paths` enumerates only top-level `seeds/*.json` and direct `seeds/generated/*.json` manifests.

## Amendment

- Preserve attempt 1 raw and lock artifacts unchanged; exclude them from confirmatory results.
- Change source closure to hash every Python file under `domains/`, `substrate/`, and `runners/dsl/python`, plus the manifest paths actually enumerated by `_seed_manifest_paths`.
- Before a worker runs, require its start fingerprint to equal the frozen lock. After a worker, compare start/end and parent fingerprints. On drift, preserve raw worker data and stop before launching another worker.
- Refuse to overwrite lock/raw outputs so each attempt has distinct custody.
- Keep both prompts, full-seed boot, counters, all-scope work rows, task gates, and analyzer equations from the v1 preregistration unchanged.

## Claim boundary

The corrected lock represents source files available to the exercised full-seed loader by inspection; it does not include arbitrary runtime-loaded resources outside that closure. The recapture is accepted only if all three workers start and finish on the exact locked source state.
