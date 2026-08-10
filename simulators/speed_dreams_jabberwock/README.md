# Speed Dreams Jabberwock bridge

This is a policy-free Speed Dreams 2.4.2 robot module. It serializes raw
simulator state to localhost UDP and applies a fixed binary actuator packet.
All target-speed, path, traffic, recovery, learning, and damage decisions stay
in the `racing_cognition` graph.

Protocol v2 carries four drive and four brake commands. Speed Dreams 2.4.2
exposes the four brake channels directly, so the bridge scales them only by
the car's configured front/rear brake repartition. Its robot ABI has a single
engine accelerator; individual drive commands are retained in the protocol
but the official backend can apply only their graph-authored aggregate.

Default ports are `31001` for commands and `31002` for telemetry. They can be
changed with `JABBERWOCK_SD_COMMAND_PORT` and
`JABBERWOCK_SD_TELEMETRY_PORT`.

The official matching source tag is installed outside the repository at
`/home/matt/ozma/internal/simulators/speed-dreams-code-2.4.2`; the matching
official 2.4.2 AppImage is installed at
`/home/matt/ozma/internal/simulators/speed-dreams-2.4.2`.

The module intentionally fails closed: until a valid command arrives it holds
zero steering/throttle and full brake. This is transport safety, not a driving
policy.

Speed Dreams 2.4.2 regenerates each non-human robot's module descriptor from
the per-interface identity under `drivers/<module>/<index>/driver.xml`.
Install `driver.xml` and `skill.xml` under `drivers/jabberwock/0/` as well as
the top-level module descriptor, otherwise startup replaces the Jabberwock
identity with a generated one and removes it from the configured race.
