# Live self-report lifecycle identity v1.7 amendment

**Amendment before capture.** V1.6 establishes semantic lifecycle identity and five controls for the live self-report route, but it does not attribute native work performed inside the production `_record_live_goal_event` helper, and its source lock does not cover every seed manifest read by `load_all_seeds()`.

V1.7 repeats the two sequential live self-report turns and existing semantic controls. It scopes native scale and per-rule counters around each helper call, records helper elapsed time, and preserves all reply, Goal identity, event ownership, closure, and failure-control oracles. The source lock covers every top-level and generated seed JSON manifest plus Python sources under `domains/`, `substrate/`, and `runners/dsl/python/`, as well as the direct runner/analyzer/protocol/native/build inputs. Worker start/end and parent post-run source maps must match.

This remains two repeated requests of one held task family. Helper costs include event preparation and native closure and cover the full loaded rule set. No route prevalence, natural-task distribution, or scaling claim will be made.
