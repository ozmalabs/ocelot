# Cross-family idempotence transfer v2 — task staging amendment

**Date:** 2026-10-01  
**Status:** Applied before the three-worker confirmatory replay.

## Reason

The first development fixture inserted both recurrence candidates before rule closure. The native matcher evaluates both bindings from the same pre-effect state, so an episode-wide negative-existence guard allowed both offers in the first pass. That fixture did not distinguish episode-level from candidate-level idempotence and failed the intended utility contrast.

## Amendment

The recurrence graph now begins with one due candidate. Each branch applies one candidate repair and settles native closure. Only after that first offer has settled does the fixture add a second due candidate to the same episode and settle again. The oracle requires exactly one candidate-linked offer for each candidate and zero progress at the final closure. Under this staged arrival, an episode-wide guard must suppress the second valid offer, while a candidate-scoped guard should permit it.

The original preregistration remains unchanged. The single-worker staging probe is exploratory; the confirmatory result uses three fresh workers and captures the amended staging protocol.
