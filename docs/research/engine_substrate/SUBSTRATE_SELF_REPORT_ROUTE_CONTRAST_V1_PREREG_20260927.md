# Self-report route contrast panel v1

Date: 2026-09-27

## Question

How does current full-boot conversation routing vary across request syntax, self-reference, known versus out-of-vocabulary (OOV) content, and genuine coinage prompts? This panel follows the one-worker exploration; all utterances and gates are fixed before its confirmatory workers run.

## Fixed utterance matrix

| ID | Text | Intended contrast |
|---|---|---|
| A | `report your organisation` | Regression target: instruction + OOV noun |
| B | `describe your organisation` | Alternate verb, same OOV noun |
| C | `tell me about your organisation` | Declarative request form, same OOV noun |
| D | `report your purpose` | Same action head, familiar noun |
| E | `describe yourself` | Familiar self-reference, alternate action head |
| F | `tell me about yourself` | Familiar self-reference, alternate request form |
| G | `what do you do?` | Self-directed question control |
| H | `what does florpification mean?` | Positive coinage/definition control |
| I | `florpification is a new word` | Coinage in a statement, syntax control |
| J | `what is organisation?` | OOV morphology without a request verb |

These are route stimuli, not a natural-language coverage sample. “Intended contrast” does not assert the intended output is presently supported.

## Method and gates

Run three fresh processes for each of the ten utterances (30 independent full boots), with deterministic shuffled schedule seed `20260927`. Each worker captures the exact reply, comprehension `kind`/`intent`/`dispatch`, communication route, instruction outcome, loaded/failed seed manifests, and semantic graph digest. No monkeypatch, seed repair, or synthetic graph intervention is used. Instrumentation is a read-only comprehension observer.

Gates: (1) 30 unique PIDs; (2) exact same source closure, runner and preregistration hashes at driver and worker boundaries; (3) three replicates per stimulus; (4) per-stimulus comprehension, route, reply, boot profile and graph digest repeat; (5) all worker records are complete and source-linked. If behavior varies within a stimulus, report the variance and do not collapse it to a single route.

## Measures and interpretation

Primary: proportions of stimulus classes routed to wordplay, instruction, another comprehension path, or no route; for instructions, proportions ending in a held faculty route, ask-back, or gap. Secondary: which tokens trigger coinage, whether definition-request context changes coinage classification, and boot-integrity consistency.

This panel characterizes ten authored stimuli on one locked implementation. It cannot estimate real-world prevalence, prove a route fix, establish natural frame locality, or support tractability claims. A successful positive control means only that the current wordplay route fires for that control. Seed failures are recorded but not presumed causal.

## Reproduction

```sh
python3 scripts/probe_self_report_route_contrast_v1.py --lock
python3 scripts/probe_self_report_route_contrast_v1.py
python3 scripts/analyze_self_report_route_contrast_v1.py
```
