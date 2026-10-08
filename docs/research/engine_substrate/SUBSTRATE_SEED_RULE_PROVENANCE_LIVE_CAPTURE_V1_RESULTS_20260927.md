# Seed-to-rule provenance on live describe-scene v1 (2026-09-27)

## Capture integrity

The fresh current-source capture passes all ten independent gates. Its `world_adapter.py` hash is `517cec9914d600ca…`; source inputs match at start/end. Full seed loading reports 731 loaded seeds and 11 manifest failures. Two simultaneous scene requests both return the expected description and resolve request-bound Goals through selection, execution, and action result. The native trace has 2,138,740 selected access events and zero drops; every traced UID joins the final native rule table. Per-seed native rule index intervals are contiguous and reconcile exactly.

## Where the observed rules came from

| Rule source | Rules added | Selected access events | Share |
|---|---:|---:|---:|
| Loaded seed manifests | 2,325 total native rules after boot | 872,784 | 40.8% |
| Lazy describe faculty, first request | 18 | 1,265,388 | 59.2% |
| Scene conceptualizer, first request | 6 | 568 | <0.1% |
| Further rules on second request | 0 | — | — |

The lazy faculty's top rules recognize a thing that moves itself (417,582 events), a thing that stays put (417,516), and a counter (417,516). The largest seed-installed contributors are `causal_attitude_networks` (379,200), `shape_decode_loop` (281,885), and `goal_residuals` (80,111) selected access events. These are operation counts for this two-request fixture, not runtime or causal ablation effects.

The per-thread hook shows that one request creates all 18 lazy-faculty rules and the six conceptualizer rules; the other creates none. Which caller gets that work is a scheduling label, not a semantic distinction. In source, [`_act_describe_scene`](../../../domains/conversation_action.py) calls `_ensure_describe` before it creates the request scene view and runs the new request through rules. Therefore this route mints the faculty on first use without first measuring a held-structure failure. That is a concrete path-specific departure from a strict “transform/infer first, mint only on residual” ordering. It may be an intentional lazy capability bootstrap, but its prevalence and cost amortization must be measured rather than assumed rare.

## Capability and tractability limits

This capture traces a successful single scene-description task on one locked source version. It maps rule provenance and operation counts; it does not show which seeds or rules are necessary, which rules dominate wall time, or how often lazy faculty construction occurs across natural prompts. The eleven boot failures and the graph/public-output alignment issue documented in v2.4 remain separate evidence boundaries. The low-RSS four/eight-seed profiles failed the task Goal gate, so this provenance map does not yet justify a reduced seed profile.

The next experiment should separate first-use faculty construction from cached reuse over independent prompts. Capture request wall/CPU and RSS with no trace or rule audit, count new rules per turn, and compare the built-in lazy route with a frozen prebuilt-faculty profile. Keep held-out prompts and full lifecycle/output gates so prebuilding cannot conceal capability loss.

## Artifacts

- [preregistration](SUBSTRATE_SEED_RULE_PROVENANCE_LIVE_CAPTURE_V1_PREREG_20260927.md)
- [source-locked runner](../../../scripts/substrate_seed_rule_provenance_live_capture_v1.py)
- [independent analyzer](../../../scripts/analyze_substrate_seed_rule_provenance_live_capture_v1.py)
- [lock](../../../evaluation/substrate_capability/seed_rule_provenance_live_capture_v1_lock_20260927.json)
- [raw capture](../../../evaluation/reports/seed_rule_provenance_live_capture_v1_20260927.json)
- [analysis](../../../evaluation/reports/seed_rule_provenance_live_capture_v1_analysis_20260927.json)
- [describe faculty builder](../../../scripts/arc_self_report.py)
