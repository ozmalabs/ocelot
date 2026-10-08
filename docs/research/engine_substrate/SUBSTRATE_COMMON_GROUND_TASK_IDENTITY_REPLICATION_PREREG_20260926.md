# Common-ground stress task-identity replication

**Question:** does the same-addressee Goal identity failure reproduce on the separately authored `phase3_common_ground_stress.v1` fixture, and does an explicit event-to-Goal relation disambiguate its two intended task sequences?

The fixture has Goal origins at event indices 0 and 3. The frozen task oracle assigns selection/execution/action-result indices 4/5/6 to Goal 0 and 7/8/9 to Goal 1. Compare three benchmark arms: current temporal-only rules; benchmark-only addressee-guarded rules; and benchmark-only explicit `event for_goal goal` guards. In the explicit arm only, instantiate `for_goal` edges from fixture indices; record that these edges are fixture-supplied and not produced by current discourse event ingestion. Run three fresh processes per arm (nine total), applying full native closure after each event.

Require all event and closure records, unique PIDs, expected common-ground claims, exact full-run repeatability within each arm, and explicit arm exact task-oracle paths. The temporal and addressee controls are registered to fail the task oracle. Report per-arm transition paths, counter/timing distributions and full-graph digests. This is an independent authored fixture replication, not a natural-task frequency estimate, production repair, or general tractability result. No rules in shipped seeds are changed.
