# Bounded planner native unit audit v1.3 amendment

## Reason

V1.2 passed all five exact test filters, but post-run manifest review found that the shared manifest did not capture `LD_LIBRARY_PATH` because that variable is not in its standard environment allowlist. The v1.2 runner derives and sets the path from the active Python interpreter's `sysconfig`, and successful dynamic loading implies that the test child received it; however, that is indirect evidence.

## Amendment

V1.3 repeats the same five exact test commands and records the child environment overrides (`RUSTFLAGS` and `LD_LIBRARY_PATH`) directly in each child-process manifest entry. It writes separate logs/report and leaves the v1.2 pass intact as a successful but environment-incomplete capture.
