# Thoughtexperiment deferred NetCollapse attribution v1 preregistration

## Question

Can a queued `Effect::NetCollapse` retain its producer-rule identity through the between-pass drain, and do its reported targets cover the exact graph delta?

## Change under evaluation

The transient queue payload carries the originating rule symbol. The drain opens a `deferred=true` write event for that rule around the existing collapse and surprise update. Matching, queue order, arithmetic, and settlement semantics are intended to remain unchanged.

## Protocol and gates

Run three source-locked workers, each on fresh equivalent substrates. A single pending `ReflexObservation` triggers `reflex_net_self_train_step`, which queues one collapse and marks the observation consumed. Compare ordinary settlement, attributed mutation reporting, and exact snapshot delta. Require status/progress/pass parity; exact changed node and edge targets covered by events; event targets included in aggregate targets; the observation write present; exactly one deferred origin event named `reflex_net_self_train_step`; no dropped events; distinct worker PIDs; and stable source/native fingerprints.

The independent analyzer evaluates the capture. This is a narrow attribution/observer check, not a learning-quality result and not a performance claim. It does not establish origin binding identity when several match bindings collapse into the same queue, field-level provenance, or the other deferred queue families.

## Reproduction

Build the release extension with `PYTHON=python3 scripts/engine_build.sh`. Then run the runner with `--lock`, `--run`, and the analyzer. The source lock includes the runner, analyzer, this preregistration, Rust implementation sources, and loaded native binary.
